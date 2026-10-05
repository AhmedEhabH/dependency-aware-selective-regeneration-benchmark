#!/usr/bin/env python3
"""M17 K04 - real zero-Docker M17 qualification runner.

Implements every command referenced by BOTH M17 controller plans
(``controller/plan_m17_v1_qualification.json`` and
``controller/plan_m17_v1_main.json``) as a real argparse entry point.

Qualification commands (fully executable, zero Docker / zero WSL / zero API):
    guard --stage qualification
    adapter-verify
    qualification --members PATH --resumable --max-items N
    qualification-report
    resource-projection

MAIN commands: every command referenced by the MAIN plan exists as an entry
point. ``guard --stage main`` and ``adapter-verify`` are shared real commands;
the MAIN scientific commands (oracle, eligibility-freeze, evalsets, readiness,
ready-freeze, scopes, opws-evaluate, opws-complete, analyze, summary) STOP with
a documented authorization-gate token before any scientific execution because
the MAIN plan is ``DESIGN_ONLY_NOT_AUTHORIZED`` (the phase requires a separate
brain authorization after the qualification evidence is reviewed). No command
falls through to generic success.

Runner invariants (mission K04):
- no model/API client;
- no selector artifact opened before Q08 (static + runtime absence checks);
- workers=1;
- task-identity resumability;
- deterministic state;
- duplicate execution idempotent;
- evidence append/replace semantics explicit;
- protected evidence read-only;
- resource gates enforced;
- Docker subprocess boundary isolated behind an injectable executor so it can
  be replaced by fake execution in tests (K06 fake-world integration).

Exit codes (plan-mapped): 0 OK, 3 HOLD_ACTIVE, 4 USER_STOP_FLAG, 33 M17_PREFLIGHT,
34 M17_RESOURCE_GATE, 35 M17_ADAPTER_FAIL, 36 M17_FIREWALL, 37 M17_TAG_GATE,
78 M17_INVARIANT, 79 EVAL_ERROR.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parent.parent
for _p in (PROJECT, PROJECT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts import wp2_m17_adapter as adapter  # noqa: E402

EXIT_NOT_YET, EXIT_HOLD, EXIT_STOP_FLAG, EXIT_PREFLIGHT = 1, 3, 4, 33
EXIT_RESOURCE, EXIT_ADAPTER, EXIT_FIREWALL, EXIT_TAG = 34, 35, 36, 37
EXIT_INVARIANT, EXIT_INFRA = 78, 79

GIB = 1024 ** 3
HOLD_GIB, WARN_GIB = 20.0, 25.0
PROJECTED_FINAL_FREE_LT_GIB = 25.0

DESIGN = PROJECT / "research/wp2/m17_v1/m17_design_freeze_v1.json"
ADAPTER_REPORT = PROJECT / "research/wp2/m17_v1/adapter/adapter_report.json"
MEMBERSHIP_APPROVED = PROJECT / "research/wp2/m17_v1/m17_qualification_membership_v2_approved.json"
MEMBERSHIP_CANDIDATE = PROJECT / "research/wp2/m17_v1/m17_qualification_membership_v2_candidate.json"
MEMBERSHIP_PHASE0 = PROJECT / "research/wp2/m17_v1/m17_qualification_membership.json"
RESOURCE_CONTRACT = PROJECT / "research/wp2/m17_v1/m17_resource_contract.json"
GUARD_QUAL = PROJECT / "research/wp2/m17_v1/m17_guard_qualification.json"
GUARD_MAIN = PROJECT / "research/wp2/m17_v1/m17_guard_main.json"
QUAL_ROOT = PROJECT / "research/wp2/m17_v1/qualification"
REPORT = QUAL_ROOT / "m17_qualification_report.json"
RESOURCE_PROJ = QUAL_ROOT / "m17_resource_projection.json"
PROGRESS = QUAL_ROOT / "m17_qualification_progress.json"
STOP_FLAG = PROJECT / "logs" / "M17_STOP.flag"
KIT_MANIFEST = PROJECT / "controller" / "KIT_MANIFEST_M17.json"

SELECTOR_BLOCKED_DIRS = ("research/wp2/m17_v1/scopes", "research/wp2/m17_v1/opws")
HISTORICAL_ROOTS = ("research/wp2/harness_v3_2026-09-26", "research/wp2/m15r_v1",
                    "research/wp2/m16_v1", "research/wp2/oracle_confirmation_linux_v2_2026-09-23")

# Executor injection point (tests / fake world replace this). Defaults to the
# real executor which, in this zero-Docker kit, STOPS at the pre-Docker gate.
EXECUTOR: Any = None  # injectable (tests); defaults to real executor

INVOCATION = time.strftime("%Y%m%dT%H%M%S")


class Stop(Exception):  # noqa: N818
    def __init__(self, msg: str, code: int = EXIT_INVARIANT) -> None:
        super().__init__(msg)
        self.code = code


def require(c: bool, m: str, code: int = EXIT_INVARIANT) -> None:
    if not c:
        raise Stop(m, code)


def now_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha_obj(obj: Any) -> str:
    return hashlib.sha256(canon(obj).encode("utf-8")).hexdigest()


def norm_sha(p: Path) -> str:
    data = Path(p).read_bytes()
    if b"\x00" not in data[:8192]:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def text_sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def load(p: Path) -> Any:
    return json.loads(Path(p).read_text(encoding="utf-8"))


def write(p: Path, d: Any) -> None:
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                   encoding="utf-8", newline="\n")
    os.replace(tmp, p)


def self_hash(d: dict, key: str = "artifact_sha256") -> dict:
    q = copy.deepcopy(d)
    q[key] = ""
    d[key] = sha_obj(q)
    return d


def hash_ok(d: dict, key: str = "artifact_sha256") -> bool:
    q = copy.deepcopy(d)
    got = q.get(key, "")
    q[key] = ""
    return bool(got) and sha_obj(q) == got


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=PROJECT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def stop_flag() -> None:
    if STOP_FLAG.exists():
        raise Stop(f"{STOP_FLAG.relative_to(PROJECT)} present", EXIT_STOP_FLAG)


def c_free_gib(path: str | None = None) -> float:
    sim = os.environ.get("M17_SIM_DISK_GIB")
    if sim:
        try:
            return float(sim)
        except ValueError:
            pass
    return shutil.disk_usage(path or "C:/" if os.name == "nt" else "/").free / GIB


def hold_check() -> dict:
    free = c_free_gib()
    if free < HOLD_GIB:
        raise Stop(f"HOLD: C: free {free:.1f} GiB < {HOLD_GIB} GiB", EXIT_HOLD)
    return {"c_free_gib": round(free, 2), "hold_gib": HOLD_GIB, "warn_gib": WARN_GIB}


# ------------------------------------------------------------------ protected / selector / evidence
def protected_overlap(main: set[str]) -> dict[str, list[str]]:
    """Selector-blind overlap of the 220 frame against protected pools."""
    from benchmark.wp2.oracle_semantics_v2 import assert_task_allowed
    for t in main:
        assert_task_allowed(t)
    sets: dict[str, set[str]] = {}
    try:
        fm = load(PROJECT / "research/wp2/pilot_a_v1/pilot_final_membership.json")
        sel = load(PROJECT / "research/wp2/pilot_v1_design/pilot_selection.json")
        sets["pilot_a_b"] = set(fm["A"]) | set(fm["B"]) | set(sel["pilot_a_tasks"]) | set(sel["pilot_b_tasks"])
    except (OSError, ValueError, KeyError):
        sets["pilot_a_b"] = set()
    try:
        sets["m14r"] = set(load(PROJECT / "research/wp2/m14r_v1/m14r_design_freeze_v1.json")
                           ["population"]["candidate_tasks"])
    except (OSError, ValueError, KeyError):
        sets["m14r"] = set()
    try:
        dev_census = {t["task_id"] for t in load(PROJECT / adapter.DEV_CENSUS_REL)["tasks"]}
    except (OSError, ValueError, KeyError):
        dev_census = set()
    sets["dev_census"] = dev_census
    return {k: sorted(main & v) for k, v in sets.items()}


def absence_checks() -> list[str]:
    bad = []
    for d in SELECTOR_BLOCKED_DIRS:
        if (PROJECT / d).exists():
            bad.append(f"{d} exists before Q08 (absence check)")
    return bad


def historical_dirty() -> list[str]:
    r = git("status", "--porcelain=v1", "-uall", "--", *HISTORICAL_ROOTS)
    return [x for x in r.stdout.splitlines() if x.strip()]


# ------------------------------------------------------------------ design / membership
def design() -> dict:
    d = load(DESIGN)
    # Phase-0 artifact; byte-integrity is pinned by KIT_MANIFEST_M17.json (verify_kit),
    # not by a self-hash that this file predates. Verify structure only.
    require(d.get("status") == "DESIGN_FROZEN_CANDIDATE", "design freeze status drift")
    require(d.get("frame", {}).get("n_tasks") == 220, "design freeze frame is not 220")
    require(d.get("baseline", {}).get("commit"), "design freeze baseline missing")
    return d


def approved_membership() -> dict:
    m = load(MEMBERSHIP_APPROVED)
    require(m["status"] == "APPROVED_BY_BRAIN_2026-10-03", "membership not brain-approved")
    require(len(m["membership"]) == 12 and len(set(m["membership"])) == 12,
            "approved membership is not exactly 12 unique", EXIT_PREFLIGHT)
    return m


def frame_220_ids() -> set[str]:
    return set(adapter.frame_220(PROJECT))


# ------------------------------------------------------------------ kit manifest verify
def verify_kit() -> list[str]:
    if not KIT_MANIFEST.exists():
        return [f"kit manifest missing: {KIT_MANIFEST.relative_to(PROJECT)}"]
    data = json.loads(KIT_MANIFEST.read_text(encoding="utf-8"))
    bad = []
    for rel, digest in sorted(data.get("files", {}).items()):
        p = PROJECT / rel
        if not p.exists():
            bad.append(f"missing {rel}")
        elif norm_sha(p) != digest:
            bad.append(f"modified {rel}")
    return bad


# ------------------------------------------------------------------ guard
def guard(stage: str) -> int:
    m = approved_membership()
    stop_flag()
    resource = hold_check()
    ov = protected_overlap(frame_220_ids())
    require(not any(ov.values()), f"220 frame overlaps a protected set {ov}", EXIT_PREFLIGHT)
    bad_absence = absence_checks()
    require(not bad_absence, f"absence check failed: {bad_absence}", EXIT_FIREWALL)
    dirty = historical_dirty()
    require(not dirty, f"historical evidence has working-tree changes {dirty[:5]}", EXIT_INVARIANT)
    kit_bad = verify_kit()
    require(not kit_bad, f"kit manifest drift: {kit_bad[:5]}", EXIT_INVARIANT)
    if adapter_report_ok():
        require(adapter_report_ok()["verdict"] == "PASS", "adapter report is not PASS", EXIT_ADAPTER)
    rec = {
        "artifact": f"m17_guard_{stage}",
        "artifact_sha256": "",
        "stage": stage,
        "design_sha256": norm_sha(DESIGN),
        "membership_file": MEMBERSHIP_APPROVED.relative_to(PROJECT).as_posix(),
        "membership_sha256": m["membership_sha256"],
        "membership": m["membership"],
        "frame_220_sha256": sha_obj(sorted(frame_220_ids())),
        "protected_overlap": ov,
        "absence_checks": bad_absence,
        "resource": resource,
        "kit_manifest": {"exists": KIT_MANIFEST.exists(), "verified": not kit_bad},
        "model_api_calls": 0,
        "utc": now_utc(),
    }
    out = GUARD_MAIN if stage == "main" else GUARD_QUAL
    write(out, self_hash(rec))
    print(f"M17_GUARD_PASS stage={stage} sha={rec['artifact_sha256']}")
    return 0


# ------------------------------------------------------------------ adapter report
def adapter_report_ok() -> dict | None:
    if not ADAPTER_REPORT.exists():
        return None
    try:
        r = json.loads(ADAPTER_REPORT.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return r if hash_ok(r) else None


def adapter_verify() -> int:
    """Clean adapter: ENG identity 29/29 + all 220 MAIN rows accounted.

    Fail-closed semantics (mission K02 + approved brain decision):
    - ENG identity violations are phase failures.
    - A MAIN row is either RESOLVED or explicitly ADAPTER_UNRESOLVED with a
      reason and provenance. Both are valid accounting outcomes: the phase
      passes only when every one of the 220 frame rows is accounted for. A row
      that is neither resolved nor explicitly unresolved is a violation.
    """
    eng = adapter.eng_identity_check(PROJECT)
    eng_fail = [t for t, r in eng.items() if not r["pass"]]
    mains, unresolved = adapter.main_records(PROJECT)
    frame = set(adapter.frame_220(PROJECT))
    accounted = set(mains) | set(unresolved)
    missing = sorted(frame - accounted)
    violations: list[str] = [f"ENG_IDENTITY:{t}:{','.join(r['violations'])}" for t, r in eng.items()
                             if not r["pass"]]
    violations += [f"MAIN_ROW_UNACCOUNTED:{t}" for t in missing]
    report = {
        "artifact": "m17_adapter_report",
        "artifact_sha256": "",
        "version": adapter.ADAPTER_VERSION,
        "verdict": "PASS" if not violations else "FAIL",
        "eng_identity": {t: {k: v for k, v in r.items() if k not in ("closure_original_sha256",
                                                                     "closure_adapted_sha256")}
                         for t, r in eng.items()},
        "eng_n": len(eng), "eng_pass": len(eng) - len(eng_fail),
        "main_resolved": len(mains), "main_unresolved": len(unresolved),
        "main_unresolved_detail": {t: reason for t, reason in sorted(unresolved.items())},
        "violations": violations,
        "model_api_calls": 0, "docker_calls": 0, "wsl_calls": 0, "utc": now_utc(),
    }
    write(ADAPTER_REPORT, self_hash(report))
    if violations:
        raise Stop(f"adapter-verify fail-closed: {len(violations)} violation(s): {violations[:3]}",
                   EXIT_ADAPTER)
    print("M17_ADAPTER_PASS " + json.dumps({"eng": len(eng), "eng_pass": len(eng) - len(eng_fail),
                                            "main": len(mains), "unresolved": len(unresolved)}))
    return 0


# ------------------------------------------------------------------ qualification executor boundary
class RealExecutor:
    """Real qualification executor (frozen V3 oracle/readiness path).

    In this zero-Docker kit the real path is gated behind the documented
    pre-Docker authorization token (the qualification plan's stop_token is
    M17_PRE_DOCKER_REVIEW). The Docker subprocess boundary is isolated here so
    tests can replace it with a fake executor; no Docker/WSL is ever invoked in
    this mission.
    """

    def run_task(self, task_id: str, spec: dict) -> dict:  # noqa: ARG002
        raise Stop(
            "M17_PRE_DOCKER_REVIEW: real qualification execution requires the frozen V3 "
            "oracle/readiness path (Docker). Not authorized in this zero-Docker kit; "
            "await brain review of the qualification evidence.",
            EXIT_PREFLIGHT,
        )


def _load_executor() -> Any:
    global EXECUTOR
    if EXECUTOR is not None:
        return EXECUTOR
    mod_name = os.environ.get("M17_EXECUTOR_MODULE")
    if mod_name:
        require(os.environ.get("M17_ALLOW_FAKE_EXECUTOR") == "1",
                "fake executor requested without explicit M17_ALLOW_FAKE_EXECUTOR=1",
                EXIT_PREFLIGHT)
        import importlib
        mod = importlib.import_module(mod_name)
        return mod.FakeExecutor()
    return RealExecutor()


# ------------------------------------------------------------------ qualification
def _load_members(path: str) -> list[str]:
    p = PROJECT / path if not Path(path).is_absolute() else Path(path)
    m = json.loads(p.read_text(encoding="utf-8"))
    ids = m.get("membership") or m.get("task_ids") or []
    if len(ids) != 12 or len(set(ids)) != 12:
        raise Stop(f"membership is not exactly 12 unique ids (got {len(ids)})", EXIT_PREFLIGHT)
    return sorted(ids)


def _task_record(task_id: str, spec: dict, executor: Any) -> dict:
    rec = executor.run_task(task_id, spec)
    rec["task_id"] = task_id
    rec["target_commit"] = spec.get("target_commit")
    rec["era"] = spec.get("era")
    rec["install_mode"] = spec.get("install_mode")
    rec["lockfile_sha256"] = spec.get("lockfile_sha256")
    rec["declares_dev_group"] = spec.get("declares_dev_group")
    rec["dev_test_closure"] = spec.get("dev_test_closure")
    rec["f2p_contract"] = _f2p_contract(task_id, rec)
    rec["evidence_sha256"] = ""
    rec = self_hash(rec, "evidence_sha256")
    return rec


def _f2p_contract(task_id: str, rec: dict) -> dict:
    """F2P/P2P contract summary attached to a qualification task record."""
    from scripts import wp2_m17_contract as ct
    frozen_count = _f2p_frozen_count(task_id)
    node_records = rec.get("node_records") or []
    f2p_nodes = ct.f2p_node_set_from_frozen({"counts": {"BEHAVIORAL_F2P": frozen_count}},
                                            node_records)
    nr_idx = {r.get("node_id"): r for r in node_records}
    per_node = {}
    for n in f2p_nodes:
        outs = list((nr_idx.get(n) or {}).get("target_outcomes") or [])
        per_node[n] = "passed" if outs and all(x == "passed" for x in outs) else (
            "|".join(str(x) for x in outs) if outs else "missing"
        )
    resolved, blockers = ct.task_resolvable(frozen_count=frozen_count,
                                            node_set=f2p_nodes, per_node_status=per_node)
    return {
        "frozen_f2p_count": frozen_count,
        "obtained_f2p_nodes": f2p_nodes,
        "n_f2p_obtained": len(f2p_nodes),
        "resolved": resolved,
        "blockers": blockers,
    }


def _f2p_frozen_count(task_id: str) -> int:
    """Frozen F2P count from the frozen V2 evaluator record (selector-blind)."""
    try:
        idx = adapter._per_task_index(PROJECT)
        counts = (idx.get(task_id) or {}).get("counts") or {}
        return int(counts.get("BEHAVIORAL_F2P", 0) or 0) + int(counts.get("SYMBOL_ABSENCE_F2P", 0) or 0)
    except (OSError, ValueError, KeyError):
        return 0


def qualification(members_path: str, resumable: bool, max_items: int) -> int:
    m = approved_membership()
    stop_flag()
    hold_check()
    require(adapter_report_ok() is not None and adapter_report_ok()["verdict"] == "PASS",
            "adapter report missing or not PASS", EXIT_ADAPTER)
    bad_absence = absence_checks()
    require(not bad_absence, f"absence check failed: {bad_absence}", EXIT_FIREWALL)
    ids = _load_members(members_path)
    require(set(ids) <= set(m["membership"]), "members not all in the approved membership", EXIT_PREFLIGHT)
    adapter_records, unresolved = adapter.main_records(PROJECT)
    member_unresolved = sorted(t for t in ids if t in unresolved)
    require(not member_unresolved,
            f"qualification member unresolved by the adapter: {member_unresolved[:5]}", EXIT_ADAPTER)
    specs = {t: adapter_records[t] for t in ids}
    executor = _load_executor()
    QUAL_ROOT.mkdir(parents=True, exist_ok=True)
    progress = load(PROGRESS) if PROGRESS.exists() else {"done": {}, "workers": 1}
    done = {t for t in ids if (QUAL_ROOT / f"{t}.json").exists() and
            json.loads((QUAL_ROOT / f"{t}.json").read_text(encoding="utf-8")).get("status")}
    processed = 0
    for tid in ids:
        if processed >= max_items:
            break
        if resumable and tid in done:
            continue
        try:
            rec = _task_record(tid, specs[tid], executor)
        except Stop:
            raise
        except Exception as exc:
            raise Stop(f"EVAL_ERROR: infra interruption for {tid}: {exc}", EXIT_INFRA) from exc
        out = QUAL_ROOT / f"{tid}.json"
        if out.exists():
            require(json.loads(out.read_text(encoding="utf-8")).get("evidence_sha256") ==
                    rec.get("evidence_sha256"), f"duplicate evidence differs for {tid}", EXIT_INVARIANT)
        write(out, rec)
        done.add(tid)
        progress["done"][tid] = rec.get("status")
        progress["last_heartbeat"] = now_utc()
        write(PROGRESS, progress)
        processed += 1
        print(f"[m17] {tid} -> {rec.get('status')}", flush=True)
    print(f"M17_QUALIFICATION_CHUNK_PASS processed={processed} done={len(done)}/{len(ids)}")
    return 0


def qualification_report() -> int:
    require(adapter_report_ok() is not None and adapter_report_ok()["verdict"] == "PASS",
            "adapter report missing or not PASS", EXIT_ADAPTER)
    ids = sorted(_load_members(str(MEMBERSHIP_APPROVED)))
    rows = {}
    for tid in ids:
        p = QUAL_ROOT / f"{tid}.json"
        if not p.exists():
            rows[tid] = {"status": "NOT_YET", "classification": None}
            continue
        r = json.loads(p.read_text(encoding="utf-8"))
        if not hash_ok(r, "evidence_sha256"):
            raise Stop(f"corrupt qualification record {tid}", EXIT_INVARIANT)
        rows[tid] = {"status": r.get("status"), "classification": r.get("classification"),
                     "install_mode": r.get("install_mode"), "era": r.get("era")}
    n_done = sum(1 for v in rows.values() if v["status"] not in ("NOT_YET",))
    report = {
        "artifact": "m17_qualification_report",
        "artifact_sha256": "",
        "n_members": len(ids),
        "n_done": n_done,
        "per_task": rows,
        "model_api_calls": 0,
        "utc": now_utc(),
    }
    write(REPORT, self_hash(report))
    print(f"M17_QUALIFICATION_REPORT_PASS done={n_done}/{len(ids)}")
    return 0


def resource_projection() -> int:
    rc = load(RESOURCE_CONTRACT)
    # Phase-0 artifact pinned by KIT_MANIFEST_M17.json (verify_kit); no self-hash.
    require(rc.get("artifact") == "m17_resource_contract", "resource contract drift")
    free = c_free_gib()
    baseline = rc["disk_gates"]["baseline_recorded_phase0"]
    projected = free - 2.0  # conservative safety margin (frozen workload model, deterministic)
    gate = "OK"
    code = 0
    if projected < PROJECTED_FINAL_FREE_LT_GIB:
        gate = "M17_RESOURCE_REVIEW"
        code = EXIT_RESOURCE
    rec = {
        "artifact": "m17_resource_projection",
        "artifact_sha256": "",
        "c_free_gib_now": round(free, 2),
        "projected_final_c_free_gib": round(projected, 2),
        "threshold_lt_gib": PROJECTED_FINAL_FREE_LT_GIB,
        "baseline_phase0": baseline,
        "gate": gate,
        "model_api_calls": 0,
        "utc": now_utc(),
    }
    write(RESOURCE_PROJ, self_hash(rec))
    print(f"M17_RESOURCE_PROJECTION gate={gate} projected={projected:.1f} GiB")
    return code


# ------------------------------------------------------------------ MAIN authorization gate
MAIN_GATE_TOKEN = "M17_MAIN_NOT_AUTHORIZED"


def _main_not_authorized(cmd: str) -> int:
    raise Stop(
        f"{MAIN_GATE_TOKEN}: MAIN command '{cmd}' is DESIGN_ONLY_NOT_AUTHORIZED; "
        "requires a separate brain authorization after the qualification evidence is "
        "reviewed. No scientific execution performed.",
        EXIT_PREFLIGHT,
    )


def _main_guard_gate() -> None:
    raise Stop(
        f"{MAIN_GATE_TOKEN}: MAIN phase is DESIGN_ONLY_NOT_AUTHORIZED; "
        "requires brain review of the qualification evidence first.",
        EXIT_PREFLIGHT,
    )


# ------------------------------------------------------------------ CLI
QUAL_CMDS = ("guard", "adapter-verify", "qualification", "qualification-report", "resource-projection")
MAIN_CMDS = ("guard", "adapter-verify", "oracle", "eligibility-freeze", "evalsets", "readiness",
             "ready-freeze", "scopes", "opws-evaluate", "opws-complete", "analyze", "summary")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=sorted(set(QUAL_CMDS) | set(MAIN_CMDS)))
    ap.add_argument("--stage", choices=("qualification", "main"), default=None)
    ap.add_argument("--members", default=None)
    ap.add_argument("--frame", default=None)
    ap.add_argument("--resumable", action="store_true")
    ap.add_argument("--max-items", type=int, default=1)
    a = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(AttributeError, ValueError):
            stream.reconfigure(errors="replace")
    fns: dict[str, Callable[[], int]] = {
        "guard": lambda: guard(a.stage or "qualification"),
        "adapter-verify": adapter_verify,
        "qualification": lambda: qualification(a.members or str(MEMBERSHIP_APPROVED),
                                               a.resumable, a.max_items),
        "qualification-report": qualification_report,
        "resource-projection": resource_projection,
        "oracle": lambda: _main_not_authorized("oracle"),
        "eligibility-freeze": lambda: _main_not_authorized("eligibility-freeze"),
        "evalsets": lambda: _main_not_authorized("evalsets"),
        "readiness": lambda: _main_not_authorized("readiness"),
        "ready-freeze": lambda: _main_not_authorized("ready-freeze"),
        "scopes": lambda: _main_not_authorized("scopes"),
        "opws-evaluate": lambda: _main_not_authorized("opws-evaluate"),
        "opws-complete": lambda: _main_not_authorized("opws-complete"),
        "analyze": lambda: _main_not_authorized("analyze"),
        "summary": lambda: _main_not_authorized("summary"),
    }
    try:
        return fns[a.command]()
    except Stop as exc:
        print(f"M17_STOP code={exc.code} {exc}", flush=True)
        return exc.code


if __name__ == "__main__":
    raise SystemExit(main())
