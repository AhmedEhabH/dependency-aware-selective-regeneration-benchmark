#!/usr/bin/env python3
"""M17 real qualification + MAIN-oracle executor.

Brain-authored bridge that reuses the frozen M16 R1 oracle procedure and the
frozen V3 harness semantics read-only. It contains no selector access and no
model/API path.

Authorized scientific scope:
- real 12-task M17 qualification;
- selector-blind MAIN oracle over the frozen 220 frame;
- eligibility freeze.
Nothing after eligibility is implemented/authorized here.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
for _p in (PROJECT, PROJECT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts import wp2_m16_r1 as r1  # noqa: E402  # frozen reviewed R1 logic
from scripts import wp2_m17_adapter as adapter  # noqa: E402
from scripts import wp2_m17_contract as contract  # noqa: E402

EXIT_NOT_YET, EXIT_HOLD, EXIT_STOP, EXIT_PREFLIGHT = 1, 3, 4, 33
EXIT_RESOURCE, EXIT_ADAPTER, EXIT_FIREWALL, EXIT_INVARIANT, EXIT_INFRA = 34, 35, 36, 78, 79

ROOT = PROJECT / "research/wp2/m17_v1"
QUAL_ROOT = ROOT / "qualification"
ORACLE_ROOT = ROOT / "oracle"
ELIG_ROOT = ROOT / "eligibility"
APPROVED = ROOT / "m17_qualification_membership_v2_approved.json"
FRAME_AUDIT = ROOT / "m17_main_frame_audit.json"
ADAPTER_REPORT = ROOT / "adapter/adapter_report.json"
QG = ROOT / "m17_qualification_gate.json"
STOP_FLAG = PROJECT / "logs/M17_STOP.flag"

REAL_EXECUTOR_ID = "scripts.wp2_m17_exec.RealExecutor"
TEST_FAKE_EXECUTOR_ID = "tests.unit.wp2.m17.sim.fake_executor.FakeExecutor"
PROVIDER_ENV = (
    "OPENROUTER_API_KEY","OPENAI_API_KEY","ANTHROPIC_API_KEY","TOGETHER_API_KEY",
    "GROQ_API_KEY","FIREWORKS_API_KEY","DEEPINFRA_API_KEY","DEEPINFRA_TOKEN",
    "WP1B_API_KEY","LLM_API_KEY",
)
INVOCATION = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())

class M17StopError(RuntimeError):
    def __init__(self, msg: str, code: int = EXIT_INVARIANT) -> None:
        super().__init__(msg)
        self.code = code

def require(cond: bool, msg: str, code: int = EXIT_INVARIANT) -> None:
    if not cond:
        raise M17StopError(msg, code)

def canon(x: Any) -> str:
    return json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

def sha_obj(x: Any) -> str:
    return hashlib.sha256(canon(x).encode()).hexdigest()

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

def load(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))

def write(p: Path, d: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                   encoding="utf-8", newline="\n")
    os.replace(tmp, p)

def append_jsonl(p: Path, d: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(d, sort_keys=True, ensure_ascii=False) + "\n")

def scrub_provider_env() -> None:
    for k in PROVIDER_ENV:
        os.environ.pop(k, None)

def stop_flag() -> None:
    if STOP_FLAG.exists():
        raise M17StopError("USER_STOP_FLAG", EXIT_STOP)

def c_free_gib() -> float:
    return shutil.disk_usage("C:/" if os.name == "nt" else "/").free / (1024**3)

def disk_gate() -> None:
    free = c_free_gib()
    if free < 20.0:
        raise M17StopError(f"HOLD_ACTIVE: C free {free:.2f} GiB < 20 GiB", EXIT_HOLD)

def frame_rows() -> dict[str, dict]:
    a = load(FRAME_AUDIT)
    rows = {r["task_id"]: r for r in a["tasks"]}
    require(len(rows) == 220, f"frame audit not 220: {len(rows)}", EXIT_PREFLIGHT)
    return rows

def approved_members() -> list[str]:
    m = load(APPROVED)
    require(m.get("status") == "APPROVED_BY_BRAIN_2026-10-03", "membership not brain-approved", EXIT_PREFLIGHT)
    ids = sorted(m["membership"])
    require(len(ids) == 12 and len(set(ids)) == 12, "membership not 12 unique", EXIT_PREFLIGHT)
    return ids

def adapter_state() -> tuple[dict[str, dict], dict[str, str]]:
    resolved, unresolved = adapter.main_records(PROJECT)
    require(len(resolved) + len(unresolved) == 220, "adapter does not account for 220", EXIT_ADAPTER)
    return resolved, unresolved

def install_firewall() -> None:
    # Frozen selector firewall from M16, read-only reuse.
    from scripts import wp2_m16_firewall as firewall
    firewall.install(PROJECT, "full")

def firewall_violations() -> list:
    from scripts import wp2_m16_firewall as firewall
    return firewall.violations()

def runtime_full_closure(manifests: dict[str, str], era: str) -> dict:
    from benchmark.wp2.dep_compiler import PYTHON_VERSION_BY_ERA, derive_dev_test_closure
    c = dict(derive_dev_test_closure(manifests, python_version=PYTHON_VERSION_BY_ERA.get(era, "3.11")))
    if "poetry.lock" in manifests:
        c["lock_text"] = manifests["poetry.lock"]
    c["pins_sha256"] = sha_obj(c.get("pins", []))
    c["era_key"] = era
    c["python_version"] = PYTHON_VERSION_BY_ERA.get(era, "3.11")
    return c

def closure_brief(c: dict) -> dict:
    return {
        "mechanism": c.get("mechanism"),
        "n_pins": len(c.get("pins", [])),
        "pins_sha256": c.get("pins_sha256"),
        "n_unsupported": len(c.get("unsupported", [])),
        "era_key": c.get("era_key"),
        "python_version": c.get("python_version"),
        "note": c.get("note", ""),
    }

def locked_dev_fragment(closure: dict) -> str:
    """Frozen V3.1 locked-dev logic parameterized by M17's runtime closure."""
    if closure.get("mechanism") in ("uv", "none", "requirements"):
        return "echo NO_LOCKED_DEV_GROUP"
    from benchmark.wp2 import harness_v3 as hv3
    from benchmark.wp2.dep_compiler import exclude_tooling_pins
    lock_text = closure.get("lock_text") or ""
    pins = (closure.get("all_locked_pins") or {}).get("pins", [])
    pins = exclude_tooling_pins(pins, lock_text, hv3.HARNESS_TOOLING_NAMES)
    if not pins:
        return "echo NO_LOCKED_DEV_GROUP"
    pins_str = " ".join(pins)
    # Byte-for-byte shell algorithm from frozen harness_v3.locked_dev_install,
    # with the closure supplied explicitly instead of task-id DEV-census lookup.
    return (
        "( set +e; "
        "uv pip freeze --python /opt/venv/bin/python | sort > /tmp/v31_main_freeze.txt; "
        f"printf '%s\\n' {pins_str} | sort -u > /tmp/v31_all_pins.txt; "
        "comm -23 /tmp/v31_all_pins.txt /tmp/v31_main_freeze.txt > /tmp/v31_dev_pins.txt; "
        "if [ -s /tmp/v31_dev_pins.txt ]; then "
        "DEVLIST=$(tr '\\n' ' ' < /tmp/v31_dev_pins.txt); "
        "for round in 1 2 3 4 5 6 7 8 9 10; do "
        "if [ -z \"$DEVLIST\" ]; then echo DEV_NO_PINS_REMAINING; break; fi; "
        "if uv pip install --python /opt/venv/bin/python $DEVLIST >>/tmp/install.log 2>&1; then "
        "echo DEV_INSTALL_OK; break; "
        "else "
        "grep -oE 'no version of [A-Za-z0-9_.-]+==[^ ]+' /tmp/install.log "
        "| awk '{print $NF}' | sort -u > /tmp/v31_unavail.txt; "
        "grep -oE '[A-Za-z0-9_.-]+==[^ ]+ has no wheels' /tmp/install.log "
        "| awk '{print $1}' | sort -u >> /tmp/v31_unavail.txt; "
        "if [ ! -s /tmp/v31_unavail.txt ]; then echo DEV_INSTALL_UNRESOLVED_FAIL; "
        "tail -60 /tmp/install.log; break; "
        "else DEVLIST=$(grep -vxF -f /tmp/v31_unavail.txt /tmp/v31_dev_pins.txt "
        "| tr '\\n' ' '); "
        "echo DEV_RETRY_R$round dropped=$(wc -l < /tmp/v31_unavail.txt) >>/tmp/install.log; "
        "fi; fi; done; "
        "else echo DEV_NO_PINS; fi; )"
    )

def _actual_node_status(nr: dict) -> str:
    outs = list(nr.get("target_outcomes") or [])
    if outs and all(x == "passed" for x in outs):
        return "passed"
    if not outs:
        return "missing"
    return "|".join(str(x) for x in outs)

def f2p_contract(task_id: str, rec: dict) -> dict:
    idx = adapter._per_task_index(PROJECT)
    counts = (idx.get(task_id) or {}).get("counts") or {}
    frozen_count = int(counts.get("BEHAVIORAL_F2P", 0) or 0) + int(counts.get("SYMBOL_ABSENCE_F2P", 0) or 0)
    node_records = rec.get("node_records") or []
    nodes = contract.f2p_node_set_from_frozen({"counts": {"BEHAVIORAL_F2P": frozen_count}}, node_records)
    nr_idx = {n.get("node_id"): n for n in node_records}
    statuses = {n: _actual_node_status(nr_idx[n]) for n in nodes if n in nr_idx}
    resolved, blockers = contract.task_resolvable(
        frozen_count=frozen_count, node_set=nodes, per_node_status=statuses
    )
    return {
        "frozen_v2_f2p_count": frozen_count,
        "obtained_f2p_nodes": nodes,
        "per_node_status": statuses,
        "resolved_against_frozen_v2_count": resolved,
        "blockers": blockers,
    }

class RealExecutor:
    executor_id = REAL_EXECUTOR_ID

    def __init__(self, evidence_root: Path):
        self.evidence_root = evidence_root

    def run_task(self, task_id: str, spec: dict) -> dict:
        install_firewall()
        stop_flag()
        disk_gate()
        rows = frame_rows()
        require(task_id in rows, f"task not in frozen frame: {task_id}", EXIT_PREFLIGHT)
        row = rows[task_id]
        require(row["target_commit"] == spec["target_commit"], f"target mismatch {task_id}", EXIT_ADAPTER)
        require(row["era_key"] == spec["era"], f"era mismatch {task_id}", EXIT_ADAPTER)

        from benchmark.wp2 import harness_v3 as hv3
        from benchmark.wp2 import oracle_confirmation as oc
        from benchmark.wp2 import oracle_semantics_v2 as osem
        from scripts import wp2_m10b_phase5_c4_v3 as ph5

        manifests = hv3.target_manifests(spec["target_commit"])
        closure = runtime_full_closure(manifests, spec["era"])
        runtime_mode = hv3.lock_install_script("/opt/wp2_v2/worktrees/m17_probe_t", manifests)[1]
        runtime_lock = hv3.lockfile_sha256(manifests)

        require(runtime_mode == spec["install_mode"],
                f"runtime install_mode != adapter for {task_id}: {runtime_mode} != {spec['install_mode']}",
                EXIT_ADAPTER)
        require(runtime_lock == spec["lockfile_sha256"],
                f"runtime lockfile != adapter for {task_id}", EXIT_ADAPTER)
        expected_brief = spec["dev_test_closure"]
        got_brief = closure_brief(closure)
        for k in ("mechanism","n_pins","pins_sha256","n_unsupported","era_key","python_version"):
            require(got_brief.get(k) == expected_brief.get(k),
                    f"runtime closure {k} != adapter for {task_id}: {got_brief.get(k)!r} != {expected_brief.get(k)!r}",
                    EXIT_ADAPTER)

        raw = self.evidence_root / "raw" / task_id / "raw_tmp"
        shutil.rmtree(raw, ignore_errors=True)
        dev_fragment = locked_dev_fragment(closure)
        deps = {
            "changed_test_files": ph5.changed_test_files,
            "clock_preflight": hv3.clock_preflight,
            "target_manifests": hv3.target_manifests,
            "ensure_worktrees_v3": hv3.ensure_worktrees_v3,
            "lock_install_script": hv3.lock_install_script,
            "locked_dev_install": lambda _tid: dev_fragment,
            "base_image_id": hv3.base_image_id,
            "run_state_v3": hv3.run_state_v3,
            "parse_junit_with_failures": oc.parse_junit_with_failures,
            "classify_node_v2": osem.classify_node_v2,
            "task_eligibility_v2": osem.task_eligibility_v2,
            "remove_worktrees_v3": hv3.remove_worktrees_v3,
            "v31_dev_closure": lambda _tid: closure,
            "lockfile_sha256": hv3.lockfile_sha256,
        }
        before = c_free_gib()
        rec = r1.oracle_task(
            task_id,
            parent=row["parent_commit"],
            target=row["target_commit"],
            era_key=row["era_key"],
            raw_root=raw,
            deps=deps,
        )
        after = c_free_gib()
        if rec.get("status") == "DONE":
            archive = self.evidence_root / "raw" / task_id / "junit_raw.tar.gz"
            rec["junit_raw_sha256"] = r1.pack_raw(raw, archive)
        else:
            shutil.rmtree(raw, ignore_errors=True)
        rec["executor"] = self.executor_id
        rec["adapter_record_sha256"] = spec.get("adapter_record_sha256")
        rec["disk_free_before_gib"] = round(before, 3)
        rec["disk_free_after_gib"] = round(after, 3)
        rec["disk_growth_gib"] = round(max(0.0, before - after), 4)
        rec["f2p_contract"] = f2p_contract(task_id, rec)
        require(not firewall_violations(), f"selector firewall violation: {firewall_violations()[:3]}", EXIT_FIREWALL)
        return rec

def is_infra(exc: BaseException) -> bool:
    return type(exc).__name__ in {
        "EvalInfraError","OracleInfraError","RuntimeError","TimeoutExpired","CalledProcessError",
        "P2PUIntegrityError"
    } or isinstance(exc, (OSError,))

def run_with_attempts(stage: str, ledger: Path, key: str, fn) -> dict:
    prior = []
    if ledger.exists():
        prior = [
            json.loads(line)
            for line in ledger.read_text(encoding="utf-8").splitlines()
            if line.strip() and json.loads(line).get("key") == key
        ]
    tries_here = 0
    while True:
        n_infra = sum(r.get("outcome") == "INFRA" for r in prior)
        invocations = {r.get("invocation") for r in prior if r.get("outcome") == "INFRA"}
        tries_here += 1
        try:
            rec = fn()
            outcome = ("INFRA" if rec.get("status") in ("INFRA","ERROR") else
                       "CLOCK_BLOCKED" if rec.get("status") == "CLOCK_BLOCKED" else
                       "INSTALL_FAIL" if rec.get("status") == "ENV_INSTALL_BLOCKED" else "OK")
            reason = "; ".join(rec.get("infra_reasons", []))
        except M17StopError:
            raise
        except Exception as exc:  # infrastructure classification only
            if not is_infra(exc):
                raise
            rec, outcome, reason = None, "INFRA", f"{type(exc).__name__}: {exc}"[:500]
        row = {"stage": stage, "key": key, "attempt": len(prior) + 1, "invocation": INVOCATION,
               "outcome": outcome, "reason": reason, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        append_jsonl(ledger,row)
        prior.append(row)
        if outcome == "OK":
            return rec
        if outcome == "CLOCK_BLOCKED":
            raise M17StopError(f"{stage} {key}: CLOCK_BLOCKED", EXIT_PREFLIGHT)
        if outcome == "INSTALL_FAIL":
            if len(prior) >= 2 and prior[-2].get("outcome") == "INSTALL_FAIL":
                assert rec is not None
                rec["status"] = "ENV_INSTALL_BLOCKED"
                rec["install_blocked_rule"] = "2 consecutive INSTALL_FAIL attempts"
                return rec
            continue
        if n_infra + 1 >= 3 and len(invocations | {INVOCATION}) >= 2:
            return {"task_id": key, "status": "INFRA_UNRESOLVED", "attempts": n_infra + 1,
                    "last_reason": reason, "executor": REAL_EXECUTOR_ID}
        if tries_here >= 2:
            raise M17StopError(f"EVAL_ERROR: {stage} {key}: {reason}", EXIT_INFRA)

def final_record(rec: dict, *, artifact: str, spec: dict | None = None) -> dict:
    rec = dict(rec)
    rec["artifact"] = artifact
    rec["artifact_sha256"] = ""
    rec["model_api_calls"] = 0
    if spec:
        rec["adapter_record_sha256"] = spec.get("adapter_record_sha256")
    return self_hash(rec)

def record_valid(p: Path) -> bool:
    if not p.exists():
        return False
    try:
        return hash_ok(load(p))
    except Exception:
        return False

def make_executor(evidence_root: Path) -> Any:
    """Return the real executor unless an explicit test-only fake is authorized."""
    mod_name = os.environ.get("M17_EXECUTOR_MODULE")
    if mod_name:
        require(
            os.environ.get("M17_ALLOW_FAKE_EXECUTOR") == "1",
            "fake executor requested without M17_ALLOW_FAKE_EXECUTOR=1",
            EXIT_PREFLIGHT,
        )
        import importlib

        mod = importlib.import_module(mod_name)
        return mod.FakeExecutor()
    return RealExecutor(evidence_root)


def executor_allowed_for_current_mode(executor_id: str | None) -> bool:
    if os.environ.get("M17_ALLOW_FAKE_EXECUTOR") == "1":
        return executor_id in {REAL_EXECUTOR_ID, TEST_FAKE_EXECUTOR_ID}
    return executor_id == REAL_EXECUTOR_ID


def qualification(max_items: int) -> int:
    scrub_provider_env()
    install_firewall()
    ids = approved_members()
    resolved, unresolved = adapter_state()
    require(not (set(ids) & set(unresolved)), "approved qualification contains unresolved task", EXIT_ADAPTER)
    ex = make_executor(QUAL_ROOT)
    done = 0
    for tid in ids:
        p = QUAL_ROOT / f"{tid}.json"
        if record_valid(p):
            continue
        if done >= max_items:
            break
        rec = run_with_attempts("qualification", QUAL_ROOT/"attempts.jsonl", tid,
                                lambda _t=tid: ex.run_task(_t, resolved[_t]))
        rec = final_record(rec, artifact="m17_qualification_task", spec=resolved[tid])
        write(p, rec)
        done += 1
        print(f"[m17-qual] {tid} -> {rec.get('status')}", flush=True)
    return 0 if qualification_complete(silent=True) else EXIT_NOT_YET

def qualification_complete(silent: bool = False) -> bool:
    ids = approved_members()
    n = sum(record_valid(QUAL_ROOT/f"{t}.json") for t in ids)
    if not silent:
        print(f"M17_QUALIFICATION_COMPLETE {n}/{len(ids)}")
    return n == len(ids)

def qualification_report() -> int:
    require(qualification_complete(silent=True), "qualification incomplete", EXIT_NOT_YET)
    rows = {}
    for tid in approved_members():
        r = load(QUAL_ROOT/f"{tid}.json")
        require(
            executor_allowed_for_current_mode(r.get("executor")),
            f"non-authorized executor record in qualification: {tid}",
            EXIT_INVARIANT,
        )
        rows[tid] = {
            "status": r.get("status"), "classification":r.get("classification"),
            "era": r.get("era_key"), "executor":r.get("executor"),
            "counts":r.get("counts"), "f2p_contract":r.get("f2p_contract"),
            "disk_growth_gib":r.get("disk_growth_gib",0),
        }
    rep = self_hash({"artifact":"m17_qualification_report","artifact_sha256":"",
                     "n_members":12,"n_done":12,"per_task":rows,"model_api_calls":0,
                     "utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())})
    write(QUAL_ROOT/"m17_qualification_report.json",rep)
    print("M17_QUALIFICATION_REPORT_PASS")
    return 0

def qualification_gate() -> int:
    require(qualification_complete(silent=True), "qualification incomplete", EXIT_NOT_YET)
    rows = {t:load(QUAL_ROOT/f"{t}.json") for t in approved_members()}
    infra = [t for t,r in rows.items() if r.get("status")=="INFRA_UNRESOLVED"]
    done = [t for t,r in rows.items() if r.get("status")=="DONE"]
    eras = sorted({frame_rows()[t]["era_key"] for t in rows})
    done_eras = {frame_rows()[t]["era_key"] for t in done}
    bad_executor = [t for t, r in rows.items() if not executor_allowed_for_current_mode(r.get("executor"))]
    bad_r1 = []
    bad_marker = []
    for t,r in rows.items():
        for nr in r.get("node_records") or []:
            if len(nr.get("target_outcomes") or []) != 3 or len(nr.get("parent_outcomes") or []) != 3:
                bad_r1.append(t)
                break
        txt = canon(r)
        if "MISSING_FIXTURE" in txt or "SOCKET_BLOCKED" in txt:
            bad_marker.append(t)
    v2_primary = [
        t for t in rows
        if bool(
            (adapter._per_task_index(PROJECT).get(t) or {})
            .get("eligibility", {})
            .get("PRIMARY_BEHAVIORAL_F2P_ELIGIBLE")
        )
    ]
    retained = [
        t for t in v2_primary
        if int((rows[t].get("counts") or {}).get("BEHAVIORAL_F2P",0) or 0) > 0
    ]
    growth = sum(float(r.get("disk_growth_gib",0) or 0) for r in rows.values()) / max(1,len(rows))
    projected = c_free_gib() - max(0.0,growth) * 219
    checks = {
        "records_12_of_12": len(rows)==12,
        "real_executor_only": not bad_executor,
        "infra_unresolved_le_1": len(infra)<=1,
        "done_at_least_10": len(done)>=10,
        "done_each_represented_era": set(eras)<=done_eras,
        "r1_triplets_complete": not bad_r1,
        "no_missing_fixture_or_socket_blocked": not bad_marker,
        # preregistered selector-blind sanity floor: at least half of the four
        # V2-primary qualification tasks retain >=1 behavioral F2P under V3+R1.
        "v2_primary_f2p_retention_at_least_half": len(retained) >= max(1,(len(v2_primary)+1)//2),
        "projected_c_free_ge_25_gib": projected >= 25.0,
        "firewall_clean": not firewall_violations(),
    }
    gate = {
        "artifact":"m17_qualification_gate","artifact_sha256":"","rule_id":"M17_QG_V1_2026-10-03",
        "checks":checks,"pass":all(checks.values()),"n_done":len(done),"n_infra_unresolved":len(infra),
        "represented_eras":eras,"done_eras":sorted(done_eras),"v2_primary_tasks":v2_primary,
        "v3_retained_behavioral_f2p":retained,"mean_disk_growth_gib":round(growth,4),
        "projected_c_free_after_219_gib":round(projected,2),"model_api_calls":0,
        "utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
    }
    write(QG,self_hash(gate))
    print("M17_QG_" + ("PASS" if gate["pass"] else "FAIL") + " " + canon(checks))
    return 0 if gate["pass"] else EXIT_INVARIANT

def oracle(max_items: int) -> int:
    scrub_provider_env()
    install_firewall()
    qg = load(QG) if QG.exists() else {}
    require(hash_ok(qg) and qg.get("pass") is True, "qualification gate missing/not PASS", EXIT_PREFLIGHT)
    resolved, unresolved = adapter_state()
    ex = RealExecutor(ORACLE_ROOT)
    done = 0
    for tid,row in sorted(frame_rows().items()):
        p = ORACLE_ROOT/tid/"record.json"
        if record_valid(p):
            continue
        if done >= max_items:
            break
        if tid in unresolved:
            rec = final_record({
                "task_id":tid,"target_commit":row["target_commit"],"parent_commit":row["parent_commit"],
                "era_key":row["era_key"],"status":"ADAPTER_UNRESOLVED",
                "reason":unresolved[tid],"executor":"NO_EXECUTOR_ADAPTER_UNRESOLVED",
            }, artifact="m17_oracle_task")
        else:
            rec = run_with_attempts("oracle",ORACLE_ROOT/"attempts.jsonl",tid,
                                    lambda _t=tid: ex.run_task(_t,resolved[_t]))
            rec = final_record(rec,artifact="m17_oracle_task",spec=resolved[tid])
        write(p,rec)
        done += 1
        print(f"[m17-oracle] {tid} -> {rec.get('status')}",flush=True)
    return 0 if oracle_complete(silent=True) else EXIT_NOT_YET

def oracle_complete(silent: bool=False) -> bool:
    rows=frame_rows()
    n=sum(record_valid(ORACLE_ROOT/t/"record.json") for t in rows)
    if not silent:
        print(f"M17_ORACLE_COMPLETE {n}/220")
    return n==220

def eligibility_freeze() -> int:
    require(oracle_complete(silent=True),"oracle incomplete",EXIT_NOT_YET)
    tasks = {}
    eligible = []
    status_counts = {}
    for tid in sorted(frame_rows()):
        r=load(ORACLE_ROOT/tid/"record.json")
        st=r.get("status")
        status_counts[st] = status_counts.get(st, 0) + 1
        is_elig = st == "DONE" and bool((r.get("eligibility") or {}).get("PRIMARY_BEHAVIORAL_F2P_ELIGIBLE"))
        if is_elig:
            eligible.append(tid)
        tasks[tid]={
            "status":st,"classification":r.get("classification"),"counts":r.get("counts"),
            "era_key":r.get("era_key"),"record_sha256":r.get("artifact_sha256"),"eligible":is_elig,
        }
    rec=self_hash({
        "artifact":"m17_v3_eligibility","artifact_sha256":"",
        "rule": (
            "status DONE and PRIMARY_BEHAVIORAL_F2P_ELIGIBLE under frozen V3+R1; "
            "ADAPTER_UNRESOLVED remains explicit in 220 ledger"
        ),
        "frame_n":220,"eligible":eligible,"n_eligible":len(eligible),"status_counts":status_counts,
        "tasks":tasks,"qualification_gate_sha256":load(QG)["artifact_sha256"],
        "model_api_calls":0,"utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
    })
    write(ELIG_ROOT/"m17_v3_eligibility.json",rec)
    print(f"M17_ELIGIBILITY_FROZEN n_eligible={len(eligible)} status={status_counts}")
    return 0

def main(argv: list[str] | None = None) -> int:
    ap=argparse.ArgumentParser()
    sp=ap.add_subparsers(dest="cmd",required=True)
    q = sp.add_parser("qualification")
    q.add_argument("--max-items", type=int, default=1)
    sp.add_parser("qualification-complete")
    sp.add_parser("qualification-report")
    sp.add_parser("qualification-gate")
    o = sp.add_parser("oracle")
    o.add_argument("--max-items", type=int, default=4)
    sp.add_parser("oracle-complete")
    sp.add_parser("eligibility-freeze")
    a = ap.parse_args(argv)
    scrub_provider_env()
    try:
        if a.cmd == "qualification":
            return qualification(a.max_items)
        if a.cmd == "qualification-complete":
            return 0 if qualification_complete() else EXIT_NOT_YET
        if a.cmd == "qualification-report":
            return qualification_report()
        if a.cmd == "qualification-gate":
            return qualification_gate()
        if a.cmd == "oracle":
            return oracle(a.max_items)
        if a.cmd == "oracle-complete":
            return 0 if oracle_complete() else EXIT_NOT_YET
        if a.cmd == "eligibility-freeze":
            return eligibility_freeze()
        raise M17StopError("unknown command",EXIT_PREFLIGHT)
    except M17StopError as exc:
        print(f"M17_EXEC_STOP code={exc.code} {exc}",flush=True)
        return exc.code

if __name__=="__main__":
    raise SystemExit(main())
