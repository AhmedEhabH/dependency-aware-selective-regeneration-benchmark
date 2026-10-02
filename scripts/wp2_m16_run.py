#!/usr/bin/env python3
"""WP2 M16 OPWS-MAIN engine (brain-authored). ZERO model API in every subcommand.

Frozen design: research/wp2/m16_v1/m16_design_freeze_v1.json (sha pinned below), which
implements the approved Review Package v2 plus the four settled items (R1, R2, S1, S3).

Selector-blind subcommands (selector-input firewall installed, section 7 of the design):
  guard  adapter-verify  dryrun-select  dryrun-execute  dryrun-complete  resource-gate
  oracle  oracle-complete  eligibility-freeze  eligibility-verify  mirror(pre-Q08 tags)
  evalsets  evalsets-complete  evalsets-freeze  readiness  readiness-complete
  ready-freeze  ready-verify  historical-verify
Selector-aware subcommands (only after the READY tag is unique, pushed and verified):
  scopes  scopes-verify  opws-evaluate  opws-complete  analyze  summary  mirror(post-Q08)

Exit codes: 0 PASS/progress, 1 check-not-yet, 3 HOLD (resumable: C: free < 20 GiB or cold
mirror unreachable), 4 stop flag, 33 preflight (resumable), 34 resource gate / S3 required
(resumable), 35 R2 adapter fail-closed (non-resumable), 36 firewall violation
(non-resumable), 37 tag gate (resumable), 78 invariant (non-resumable), 79 evaluation /
execution infrastructure (resumable).

Amendment R2A (2026-10-02, tag wp2-m16-v1-r2a-2026-10-02; scripts/wp2_m16_r2a.py and
research/wp2/m16_v1/m16_r2a_adapter_verifier_amendment.json): adapter_verify applies the historical-schema
rule M16_R2A_ENG_IDENTITY_HIST_SCHEMA_V1; the guard verifies the amended files against the R2A tag and every
other kit file against the kit tag; READY ancestry is kit -> R2A -> dryrun -> ... when the record exists.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import datetime as dt
import hashlib
import inspect
import json
import os
import shutil
import subprocess
import sys
import uuid
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
for _p in (PROJECT, PROJECT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts import wp2_m16_adapter as adapter  # noqa: E402
from scripts import wp2_m16_firewall as firewall  # noqa: E402
from scripts import wp2_m16_r1 as r1  # noqa: E402
from scripts import wp2_m16_r2a as r2a  # noqa: E402
from scripts import wp2_m16_resource as resource  # noqa: E402
from scripts import wp2_m16_stats as stats  # noqa: E402

ROOT = PROJECT / "research/wp2/m16_v1"
DESIGN = ROOT / "m16_design_freeze_v1.json"
DESIGN_SHA = "959a23f1b9caff5a342439e8ea6c7243f8f6c5a0e53eed64b0d5c9ecb5856982"
QUARANTINE = ROOT / "m16_l_opws_quarantine_amendment.json"
R1_AMENDMENT = ROOT / "m16_r1_repetition_amendment.json"
GUARD = {"main": ROOT / "m16_guard.json", "dryrun": ROOT / "m16_guard_dryrun.json"}
ADAPTER_DIR = ROOT / "adapter"
SHADOW = PROJECT / "_workspace/tmp/m16_shadow_root"   # regenerable, hash-pinned in the report
ADAPTER_REPORT = ADAPTER_DIR / "adapter_report.json"
R2A_RECORD = ROOT / "m16_r2a_adapter_verifier_amendment.json"
DRY = ROOT / "dryrun"
DRY_SEL = DRY / "selection.json"
DRY_GATE = DRY / "resource_gate.json"
ORACLE = ROOT / "oracle"
ELIG = ROOT / "m16_v3_eligibility.json"
EVALSETS = ROOT / "evalsets"
P2PU_OUT = EVALSETS / "p2pu"
SETS = ROOT / "evaluator_only/m16_main_evaluator_sets_v3.json"
SETS_FREEZE = ROOT / "m16_evalsets_freeze.json"
READY = ROOT / "readiness"
READY_MEMBERSHIP = ROOT / "m16_ready_membership.json"
SCOPES = ROOT / "scopes/frozen_scopes.json"
OPWS_DIR = ROOT / "opws"
OPWS_PLAN = OPWS_DIR / "plan.json"
COMPLETE = ROOT / "m16_opws_complete.json"
ANALYSIS = ROOT / "analysis/m16_analysis.json"
SUMMARY = ROOT / "m16_summary.json"
REPORT = PROJECT / "docs/WP2_M16_V1_RESULT.md"
MIRROR_DIR = ROOT / "mirror"
STOP_FLAG = PROJECT / "logs/M16_STOP.flag"
SALEOR_CACHE = PROJECT / "dist/pilot-repo-cache/saleor"
WP1A_PRED = "research/wp1a/sip_rmcss_per_task_predictions.json"
WP1B_MAIN = "research/wp1b/main-297-2026-09-22/agent_run_records.jsonl"
WP1B_VAR = "research/wp1b/variance-15x3-2026-09-22/agent_run_records.jsonl"
MAIN_MANIFEST = "research/wp1b/wp1b_main_297_manifest.json"
OOF_A = "research/memory-rescue-v2/final_oof_predictions_A.json"

TAGS = {"kit": "wp2-m16-v1-kit-2026-10-02", "dryrun": "wp2-m16-v1-dryrun",
        "eligibility": "wp2-m16-v1-eligibility", "evalsets": "wp2-m16-v1-evalsets",
        "ready": "wp2-m16-v1-ready", "scopes": "wp2-m16-v1-scopes", "result": "wp2-m16-v1-result"}
SELECTORS = ("RMCSS_HARD", "AGENT_MAIN")
REPLICATES = ("AGENT_r1", "AGENT_r2", "AGENT_r3")
PASSISH = ("PASS", "UNDEFINED")
MAX_INFRA_ATTEMPTS = 3
PROVIDER_ENV = ("OPENROUTER_API_KEY", "DEEPINFRA_API_KEY", "DEEPINFRA_TOKEN", "OPENAI_API_KEY",
                "ANTHROPIC_API_KEY", "TOGETHER_API_KEY", "GROQ_API_KEY", "FIREWORKS_API_KEY",
                "WP1B_API_KEY", "LLM_API_KEY")
EXIT_NOT_YET, EXIT_HOLD, EXIT_STOP_FLAG, EXIT_PREFLIGHT = 1, 3, 4, 33
EXIT_RESOURCE, EXIT_ADAPTER, EXIT_FIREWALL, EXIT_TAG = 34, 35, 36, 37
EXIT_INVARIANT, EXIT_INFRA = 78, 79
INFRA_EXC = ("EvalInfraError", "OracleInfraError", "RuntimeError", "TimeoutExpired",
             "CalledProcessError", "P2PUIntegrityError")
INVOCATION = uuid.uuid4().hex[:12]
WORLD: Any = None   # injectable (tests); defaults to RealWorld()


class Stop(Exception):  # noqa: N818
    def __init__(self, msg: str, code: int = EXIT_INVARIANT) -> None:
        super().__init__(msg)
        self.code = code


# ------------------------------------------------------------------ helpers
def now() -> str:
    return dt.datetime.now(dt.UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def load(p: Path) -> Any:
    return json.loads(Path(p).read_text(encoding="utf-8"))


def norm_sha(p: Path) -> str:
    d = Path(p).read_bytes()
    if b"\x00" not in d[:8192]:
        d = d.replace(b"\r\n", b"\n")
    return hashlib.sha256(d).hexdigest()


def text_sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha_obj(x: Any) -> str:
    return hashlib.sha256(json.dumps(x, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def core_diff_sha(diff: str) -> str:
    """Frozen v21 identity: sha256(json.dumps([diff])) (as M15-R)."""
    return hashlib.sha256(json.dumps([diff], sort_keys=True, ensure_ascii=False)
                          .encode("utf-8")).hexdigest()


def write(p: Path, d: Any) -> None:
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                   encoding="utf-8", newline="\n")
    os.replace(tmp, p)


VOLATILE = ("utc", "artifact_sha256")


def _stable(d: dict) -> dict:
    return {k: v for k, v in d.items() if k not in VOLATILE}


def write_frozen(p: Path, d: dict, *, overwrite_if_different: bool = False) -> bool:
    """Idempotent write of a self-hashed artifact. If p already holds a valid artifact whose content
    (ignoring utc/artifact_sha256) equals d, nothing is written (bytes stay identical, so a resume
    after a failed tag push re-tags the same commit). A differing frozen artifact is STOP 78 unless
    overwrite_if_different (non-frozen derived outputs). Returns True when a write happened."""
    p = Path(p)
    if p.exists():
        try:
            old = load(p)
        except (OSError, ValueError):
            old = None
        if isinstance(old, dict) and hash_ok(old) and _stable(old) == _stable(d):
            return False
        require(overwrite_if_different, f"frozen artifact {p.as_posix()} exists with different content",
                EXIT_INVARIANT)
    write(p, d)
    return True


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


def record_state(p: Path, key: str = "artifact_sha256") -> str:
    if not Path(p).exists():
        return "ABSENT"
    try:
        return "VALID" if hash_ok(load(p), key) else "CORRUPT"
    except (ValueError, OSError):
        return "CORRUPT"


def require(c: bool, m: str, code: int = EXIT_INVARIANT) -> None:
    if not c:
        raise Stop(m, code)


def rel(p: Path) -> str:
    return Path(p).resolve().relative_to(PROJECT.resolve()).as_posix()


def git(*a: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *a], cwd=PROJECT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def append_jsonl(p: Path, row: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def read_jsonl(p: Path) -> list[dict]:
    if not Path(p).exists():
        return []
    return [json.loads(x) for x in Path(p).read_text(encoding="utf-8").splitlines() if x.strip()]


def safe(skey: str) -> str:
    return skey.replace(":", "__")


def scrub_provider_env() -> list[str]:
    """Remove provider credentials from this process (children inherit nothing)."""
    present = [k for k in PROVIDER_ENV if k in os.environ]
    for k in present:
        os.environ.pop(k, None)
    return present


def stop_flag() -> None:
    if STOP_FLAG.exists():
        raise Stop(f"{rel(STOP_FLAG)} present", EXIT_STOP_FLAG)


def hold_check() -> dict:
    h = resource.hold_status()
    if h["warn"]:
        print(f"[m16] WARN C: free {h['c_free_gib']} GiB < {h['warn_gib']}", flush=True)
    if h["hold"]:
        raise Stop(f"HOLD: C: free {h['c_free_gib']} GiB < {h['hold_gib']} GiB", EXIT_HOLD)
    return h


# ------------------------------------------------------------------ design
def design() -> dict:
    d = load(DESIGN)
    require(hash_ok(d) and d["artifact_sha256"] == DESIGN_SHA, "design freeze drift")
    c = d["constants"]
    require(c["r1_rule_constants_sha256"] == r1.rule_constants_sha(), "R1 rule constants drift")
    require(c["stats_version"] == stats.VERSION and c["band"] == stats.BAND, "stats constants drift")
    require(c["adapter_version"] == adapter.ADAPTER_VERSION, "adapter version drift")
    require(c["resource"] == {"hold_gib": resource.HOLD_GIB, "warn_gib": resource.WARN_GIB,
                              "plan_floor_gib": resource.PLAN_FLOOR_GIB,
                              "safety_gib": resource.SAFETY_GIB, "workload": resource.WORKLOAD},
            "resource constants drift")
    require(c["firewall"] == {k: v for k, v in firewall.config().items() if k not in ("installed", "mode")},
            "firewall constants drift")
    require(c["tags"] == TAGS, "tag names drift")
    rs = inspect.signature(stats.run_status).parameters
    require(rs["pool_min"].default == c["pool_min"] and rs["drop_max"].default == c["listwise_drop_max"]
            and rs["amended_max"].default == c["amended_max"], "run_status thresholds drift from the design")
    return d


def frame() -> list[str]:
    return adapter.frame_220(PROJECT)


def rows220() -> dict[str, dict]:
    return adapter.main_rows(PROJECT)


# ------------------------------------------------------------------ git / tag gates
def gg():
    from benchmark.wp1b import git_gate
    return git_gate


def remote_tags(pattern: str) -> list[str]:
    r = git("ls-remote", "--tags", "origin", f"refs/tags/{pattern}")
    if r.returncode:
        raise Stop(f"origin unreachable: {r.stderr[-300:]}", EXIT_TAG)
    names = set()
    for line in r.stdout.splitlines():
        parts = line.split()
        if len(parts) == 2:
            names.add(parts[1].removeprefix("refs/tags/").removesuffix("^{}"))
    return sorted(names)


def local_tags(pattern: str) -> list[str]:
    return sorted(x for x in git("tag", "--list", pattern).stdout.split() if x)


def tag_commit(tag: str) -> str:
    return git("rev-parse", f"refs/tags/{tag}^{{commit}}").stdout.strip()


def is_ancestor(a: str, b: str) -> bool:
    return bool(a) and bool(b) and git("merge-base", "--is-ancestor", a, b).returncode == 0


def pushed_tag(tag: str, files: list[Path]) -> dict:
    """Exactly one local + one remote tag of this name, same object, files in it, ancestor of HEAD."""
    loc, rem = local_tags(tag + "*"), remote_tags(tag + "*")
    require(loc == [tag] and rem == [tag], f"tag {tag}: local {loc} / origin {rem} must both be "
            f"exactly [{tag}]", EXIT_TAG)
    try:
        objs = gg().verify_tag_on_origin(PROJECT, tag)
        for f in files:
            gg().verify_file_in_tag(PROJECT, tag, f)
    except Exception as exc:  # noqa: BLE001 - git_gate raises its own error classes
        raise Stop(f"tag {tag} not verified on origin: {exc}", EXIT_TAG) from exc
    commit = tag_commit(tag)
    require(is_ancestor(commit, git("rev-parse", "HEAD").stdout.strip()),
            f"tag {tag} commit is not an ancestor of HEAD", EXIT_TAG)
    lsr = git("ls-remote", "origin", f"refs/tags/{tag}", f"refs/tags/{tag}^{{}}").stdout.strip()
    return {"tag": tag, "commit": commit, "objects": objs, "ls_remote": lsr}


def ready_pushed() -> dict:
    """P1: READY membership committed, uniquely tagged, on origin, with ordered ancestry."""
    info = pushed_tag(TAGS["ready"], [READY_MEMBERSHIP, SETS, ELIG])
    e, s = pushed_tag(TAGS["eligibility"], [ELIG]), pushed_tag(TAGS["evalsets"], [SETS, SETS_FREEZE])
    k, dr = pushed_tag(TAGS["kit"], [DESIGN]), pushed_tag(TAGS["dryrun"], [DESIGN])
    if R2A_RECORD.exists():                                     # R2A: kit -> r2a -> dryrun
        a = pushed_tag(r2a.TAG, [R2A_RECORD])
        require(is_ancestor(k["commit"], a["commit"]) and is_ancestor(a["commit"], dr["commit"]),
                "kit -> R2A -> dryrun tag ancestry violated", EXIT_TAG)
    require(is_ancestor(k["commit"], dr["commit"]) and is_ancestor(dr["commit"], e["commit"]) and
            is_ancestor(e["commit"], s["commit"]) and is_ancestor(s["commit"], info["commit"]),
            "kit -> dryrun -> eligibility -> evalsets -> READY tag ancestry violated", EXIT_TAG)
    return {**info, "eligibility_commit": e["commit"], "evalsets_commit": s["commit"]}


# ------------------------------------------------------------------ historical evidence
HISTORICAL_ROOTS = ("research/wp2/harness_v3_2026-09-26", "research/wp2/m15r_v1",
                    "research/wp2/m14r_v1", "research/wp2/pilot_a_v1",
                    "research/wp2/oracle_confirmation_linux_v2_2026-09-23", "research/wp1a",
                    "research/wp1b", "research/stage5-v2-final", "research/memory-rescue-v2")


def historical_trees(ref: str = "HEAD") -> dict[str, str]:
    out = {}
    for r in HISTORICAL_ROOTS:
        out[r] = git("rev-parse", f"{ref}:{r}").stdout.strip()
    return out


def historical_dirty() -> list[str]:
    r = git("status", "--porcelain=v1", "-uall", "--", *HISTORICAL_ROOTS)
    return [x for x in r.stdout.splitlines() if x.strip()]


def historical_verify() -> int:
    g = load(GUARD["main"]) if GUARD["main"].exists() else load(GUARD["dryrun"])
    require(hash_ok(g), "guard record hash")
    cur = historical_trees()
    require(cur == g["historical_trees"], f"historical evidence tree changed: "
            f"{[k for k in cur if cur[k] != g['historical_trees'].get(k)]}")
    dirty = historical_dirty()
    require(not dirty, f"historical evidence has working-tree changes {dirty[:5]}")
    print("M16_HISTORICAL_UNCHANGED " + json.dumps({"roots": len(cur)}))
    return 0


# ------------------------------------------------------------------ amendment R2A gate
def r2a_gate(d: dict) -> dict:
    """Without the R2A record every kit code file must equal the kit tag (original behaviour). With it:
    record self-hash + rule id + kit commit + design; the R2A tag is unique, on origin, an ancestor of HEAD,
    a descendant of the kit tag and holds the record and every amended/added code file byte-identically."""
    if not R2A_RECORD.exists():
        return {}
    rec = load(R2A_RECORD)
    require(hash_ok(rec), "R2A amendment record hash")
    kit_commit = tag_commit(TAGS["kit"])
    files = sorted(set(rec.get("amended_files", {})) | set(rec.get("added_files", {})))
    shas = {f: norm_sha(PROJECT / f) for f in files if (PROJECT / f).exists()}
    bad = r2a.record_problems(rec, kit_commit=kit_commit, design_sha=DESIGN_SHA, files_lf_sha=shas)
    require(not bad, f"R2A amendment record: {bad[:5]}")
    require(set(rec["amended_files"]) <= set(d["kit_code_files"]) | {"tests/unit/wp2/m16/sim/simulate.py"},
            "R2A amends a file outside the M16 kit")
    code = [PROJECT / f for f in files if f.startswith("scripts/")]
    info = pushed_tag(r2a.TAG, [R2A_RECORD] + code)
    require(is_ancestor(kit_commit, info["commit"]), "R2A tag is not a descendant of the kit tag", EXIT_TAG)
    return {**info, "rule_id": rec["rule_id"], "record_sha256": rec["artifact_sha256"],
            "amended_files": rec["amended_files"], "added_files": rec["added_files"]}


# ------------------------------------------------------------------ guard
def protected_overlap(main: set[str]) -> dict[str, list[str]]:
    from benchmark.wp2.oracle_semantics_v2 import assert_task_allowed
    for t in main:
        assert_task_allowed(t)
    sets: dict[str, set[str]] = {}
    fm = load(PROJECT / "research/wp2/pilot_a_v1/pilot_final_membership.json")
    sel = load(PROJECT / "research/wp2/pilot_v1_design/pilot_selection.json")
    sets["pilot_a_b"] = set(fm["A"]) | set(fm["B"]) | set(sel["pilot_a_tasks"]) | set(sel["pilot_b_tasks"])
    sets["m14r"] = set(load(PROJECT / "research/wp2/m14r_v1/m14r_design_freeze_v1.json")
                       ["population"]["candidate_tasks"])
    sets["dev_census"] = {t["task_id"] for t in load(PROJECT / adapter.DEV_CENSUS)["tasks"]}
    sets["oof_a"] = set(load(PROJECT / OOF_A))
    return {k: sorted(main & v) for k, v in sets.items()}


def guard(stage: str) -> int:
    d = design()
    q, a = load(QUARANTINE), load(R1_AMENDMENT)
    require(hash_ok(q) and q["artifact_sha256"] == d["pins"]["quarantine_amendment_artifact_sha256"],
            "quarantine amendment drift")
    require(text_sha(q["text"]) == d["pins"]["quarantine_text_sha256"], "quarantine text drift")
    require(hash_ok(a) and a["artifact_sha256"] == d["pins"]["r1_amendment_artifact_sha256"]
            and a["rule_constants_sha256"] == r1.rule_constants_sha(), "R1 amendment drift")
    amended = r2a_gate(d)                                       # {} when no R2A record exists
    kit = pushed_tag(TAGS["kit"], [DESIGN, QUARANTINE, R1_AMENDMENT] +
                     [PROJECT / f for f in d["kit_code_files"] if f not in amended.get("amended_files", {})])
    for f, h in d["pins"]["file_norm_sha256"].items():
        if firewall.path_blocked(PROJECT / f, str(PROJECT)):
            continue                                  # selector inputs are verified at Q08
        require((PROJECT / f).exists() and norm_sha(PROJECT / f) == h, f"pinned file drift {f}")
    trees_head, trees_kit = historical_trees("HEAD"), historical_trees(kit["commit"])
    require(trees_head == trees_kit, "historical evidence changed since the kit commit")
    require(not historical_dirty(), "historical evidence has working-tree changes")
    main = set(load(PROJECT / MAIN_MANIFEST)["task_ids"])
    require(len(main) == 297 and set(frame()) <= main, "MAIN manifest / 220 frame mismatch")
    ov = protected_overlap(main)
    require(not any(ov.values()), f"MAIN overlaps a protected or DEV set {ov}")
    for sub in ("scopes", "opws"):
        require(not (ROOT / sub).exists(), f"{sub}/ exists before Q08 (absence check)")
    h = hold_check()
    rec = {"artifact": f"m16_guard_{stage}", "artifact_sha256": "", "design": DESIGN_SHA,
           "stage": stage, "kit_tag": kit, "r2a": amended, "historical_trees": trees_head,
           "frame_220_sha256": sha_obj(frame()), "protected_overlap": ov,
           "provider_env_removed": scrub_provider_env(), "firewall": firewall.config(),
           "resources": h, "model_api_calls": 0, "utc": now()}
    if stage == "main":
        rec["resource_gate"] = gate_recheck()
    write(GUARD[stage], self_hash(rec))
    print(f"M16_GUARD_PASS stage={stage}")
    return 0


# ------------------------------------------------------------------ world (frozen code access)
class RealWorld:
    """All Docker/WSL/git effects go through frozen code under the R2 adapter."""

    def __init__(self) -> None:
        import benchmark.wp2.e2e.scopes as scopes
        import benchmark.wp2.harness_v3 as hv3
        import benchmark.wp2.oracle_confirmation as oc
        import benchmark.wp2.oracle_semantics_v2 as osem
        import scripts.wp2_m10b_phase5_c4_v3 as ph5
        self.scopes, self.hv3, self.oc, self.osem, self.ph5 = scopes, hv3, oc, osem, ph5

    # R2 checks -------------------------------------------------------------
    def target_manifests(self, target: str) -> dict:
        return self.hv3.target_manifests(target)

    def closure(self, task_id: str, adapted: bool) -> dict:
        adapter.clear_closure_cache([task_id])
        if adapted:
            with adapter.main_inputs(SHADOW):
                return copy.deepcopy(self.hv3.v31_dev_closure(task_id))
        return copy.deepcopy(self.hv3.v31_dev_closure(task_id))

    def adapted_lookup(self, task_id: str) -> dict:
        with adapter.main_inputs(SHADOW):
            parent, target = self.scopes.commits_of(task_id)
            return {"parent": parent, "target": target, "era": self.hv3._era_for(task_id)}

    def frozen_lookup(self, task_id: str) -> dict:
        parent, target = self.scopes.commits_of(task_id)
        return {"parent": parent, "target": target, "era": self.hv3._era_for(task_id)}

    def install_mode(self, manifests: dict) -> str:
        return self.hv3.lock_install_script("/opt/wp2_v2/worktrees/m16_probe_t", manifests)[1]

    def lock_signature(self, manifests: dict) -> str:
        return self.hv3.lockfile_sha256(manifests)

    def commits_exist(self, shas: list[str]) -> dict:
        def batch(cmd: list[str]) -> set[str]:
            r = subprocess.run(cmd, input="\n".join(shas) + "\n", capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=600)
            return {ln.split()[0] for ln in r.stdout.splitlines() if ln.endswith(" commit")
                    or " commit " in ln}
        win = batch(["git", "-C", str(SALEOR_CACHE), "cat-file", "--batch-check"])
        lin = batch(["wsl", "-d", resource.DISTRO, "--", "git", "-C", resource.WSL_CACHE,
                     "cat-file", "--batch-check"])
        return {"windows_missing": sorted(set(shas) - win), "wsl_missing": sorted(set(shas) - lin)}

    # oracle ------------------------------------------------------------------
    def oracle_task(self, task_id: str, row: dict, raw_root: Path, between=None) -> dict:
        hv3 = self.hv3
        with adapter.main_inputs(SHADOW):
            deps = {"changed_test_files": self.ph5.changed_test_files,
                    "clock_preflight": hv3.clock_preflight, "target_manifests": hv3.target_manifests,
                    "ensure_worktrees_v3": hv3.ensure_worktrees_v3,
                    "lock_install_script": hv3.lock_install_script,
                    "locked_dev_install": hv3.locked_dev_install, "base_image_id": hv3.base_image_id,
                    "run_state_v3": hv3.run_state_v3,
                    "parse_junit_with_failures": self.oc.parse_junit_with_failures,
                    "classify_node_v2": self.osem.classify_node_v2,
                    "task_eligibility_v2": self.osem.task_eligibility_v2,
                    "remove_worktrees_v3": hv3.remove_worktrees_v3,
                    "v31_dev_closure": hv3.v31_dev_closure, "lockfile_sha256": hv3.lockfile_sha256}
            return r1.oracle_task(task_id, parent=row["parent_commit"], target=row["target_commit"],
                                  era_key=row["era_key"], raw_root=raw_root, deps=deps,
                                  between_states=between)

    def snapshot(self, label: str, heavy: bool = True) -> dict:
        return resource.snapshot(label, heavy=heavy)

    def leftovers(self, tid: str) -> dict:
        return resource.transient_leftovers(tid)

    # evaluator sets -----------------------------------------------------------
    def p2pu_unit(self, task_id: str) -> tuple[dict, dict]:
        with adapter.main_inputs(SHADOW, P2PU_OUT) as m:
            p = m["p2pu"]
            dfile = P2PU_OUT / f"p2pu_v3_rediscovery_{task_id}.json"
            discovery = p.ensure_discovery(task_id)
            if discovery.get("collect_rc") not in (0,):
                dfile.unlink(missing_ok=True)
                raise r1.OracleInfraError(f"P2P-U rediscovery container rc={discovery.get('collect_rc')}")
            nodes = p.selection_nodes_from_discovery(discovery, 200)
            if not nodes:
                res = p.build_undefined_result(task_id, 200, discovery)
                p._write_unit_result(res)
                return discovery, res
            ok, _why = p.verify_unit(task_id, 200)
            if ok:
                return discovery, load(P2PU_OUT / f"p2pu_v3_eng_{task_id}_cap200.json")
            p._delete_unit_evidence(task_id, 200)
            return discovery, p.execute_cap(task_id, 200, nodes, discovery)

    def p2pu_discard(self, task_id: str) -> None:
        with adapter.main_inputs(SHADOW, P2PU_OUT) as m:
            m["p2pu"]._delete_unit_evidence(task_id, 200)

    # evaluation ---------------------------------------------------------------
    def _ev(self):
        from scripts.wp2_m14a_evalcore import point_evaluator
        return adapter.EvProxy(point_evaluator(SETS, ROOT), SHADOW)

    def gold_scope(self, task_id: str) -> tuple[list[str], dict]:
        with adapter.main_inputs(SHADOW):
            graw = self.scopes.gold_raw_scope(task_id)
            return graw, self.scopes.editable_filter(task_id, graw)

    def gold_raw(self, task_id: str) -> list[str]:
        with adapter.main_inputs(SHADOW):
            return self.scopes.gold_raw_scope(task_id)

    def editable(self, task_id: str, raw: list[str]) -> dict:
        with adapter.main_inputs(SHADOW):
            return self.scopes.editable_filter(task_id, raw)

    def scoped_gold_diff(self, task_id: str, files: list[str]) -> str:
        import scripts.wp2_m14r_run as m14r
        with adapter.main_inputs(SHADOW):
            return m14r.scoped_gold_diff(task_id, files)

    def evaluate(self, task_id: str, label: str, diff: str, *, e1: bool, diag: Path | None,
                 parent_starts_ok: bool) -> tuple[dict, str, str]:
        """materialize + frozen evaluate_state_safe (e1=False) or E1+E1A1 (e1=True)."""
        from scripts.wp2_m14a_evalcore import evaluate_state_safe
        import scripts.wp2_m15r_e1a1 as e1a1
        with adapter.main_inputs(SHADOW):
            ev = self._ev()
            wt, tree = ev.materialize(task_id, label, diff)      # ValueError: does not apply
            if not e1:
                er = evaluate_state_safe(ev, task_id, label, wt)
                return er["groups"], tree, "ALL_JUNIT_PRESENT"
            er = e1a1.evaluate_state_e1a1(ev, task_id, label, wt, diff_text=diff, diag_path=diag,
                                          parent_starts_ok=parent_starts_ok)
            return er["groups"], tree, er.get("e1_decision", "")


def world() -> Any:
    global WORLD
    if WORLD is None:
        WORLD = RealWorld()
    return WORLD


def is_infra(exc: BaseException) -> bool:
    return type(exc).__name__ in INFRA_EXC or isinstance(exc, (OSError, subprocess.SubprocessError))


# ------------------------------------------------------------------ Q02 adapter verify (R2)
def adapter_verify() -> int:
    design()
    w = world()
    readme = adapter.build_shadow(PROJECT, SHADOW)
    # R2A: historical-schema-aware ENG identity (scripts/wp2_m16_r2a.py); history is read, never written
    hist, census = r2a.parse_history((PROJECT / r2a.HIST_REL).read_text(encoding="utf-8"))
    violations: list[str] = [f"HIST_SCHEMA:{x}" for x in census["fatal"]]
    eng = {}
    for t in sorted(hist):
        rec = hist[t]
        mf = w.target_manifests(rec["target_commit"]) if rec.get("target_commit") else {}
        eng[t] = r2a.eng_check(
            rec, frozen_closure=w.closure(t, adapted=False), adapted_closure=w.closure(t, adapted=True),
            frozen_lookup=w.frozen_lookup(t), adapted_lookup=w.adapted_lookup(t),
            install_mode=w.install_mode(mf) if mf else None, lock_signature=w.lock_signature(mf) if mf else None,
            sha_obj=adapter.sha_obj, brief=adapter.closure_brief)
        violations += [f"ENG_IDENTITY:{t}:{x}" for x in eng[t]["violations"]]
    rows = rows220()
    main = {}
    for t, row in sorted(rows.items()):
        lk = w.adapted_lookup(t)
        mf = w.target_manifests(row["target_commit"])
        c = w.closure(t, adapted=True)
        bad = adapter.check_main_closure(t, row["era_key"], mf, c)
        if lk != {"parent": row["parent_commit"], "target": row["target_commit"], "era": row["era_key"]}:
            bad.append(f"LOOKUP_MISMATCH:{lk}")
        main[t] = {**adapter.closure_brief(c), "declares_dev_group": adapter.declares_dev_group(mf),
                   "install_mode": w.install_mode(mf) if mf else None,
                   "lock_signature": w.lock_signature(mf) if mf else None, "violations": bad}
        violations += [f"MAIN:{t}:{b}" for b in bad]
    shas = sorted({r["parent_commit"] for r in rows.values()} | {r["target_commit"] for r in rows.values()})
    ex = w.commits_exist(shas)
    if ex["windows_missing"] or ex["wsl_missing"]:
        violations.append(f"COMMITS_MISSING:{ex}")
    verdict = "PASS" if not violations else "FAIL"
    write(ADAPTER_REPORT, self_hash({
        "artifact": "m16_adapter_report", "artifact_sha256": "", "version": adapter.ADAPTER_VERSION,
        "verdict": verdict, "shadow": readme, "eng_identity": eng, "main": main,
        "r2a": {"rule_id": r2a.RULE_ID, "historical_schema": census,
                "provenance_coverage": r2a.provenance_coverage(eng)},
        "mechanism_counts": dict(Counter(v["mechanism"] for v in main.values())),
        "install_mode_counts": dict(Counter(v["install_mode"] for v in main.values())),
        "n_distinct_lock_signatures": len({v["lock_signature"] for v in main.values()}),
        "commits": {"n": len(shas), **ex}, "violations": violations, "model_api_calls": 0,
        "docker_calls": 0, "utc": now()}))
    if violations:
        raise adapter.AdapterError(f"R2 fail-closed: {len(violations)} violation(s): {violations[:3]}")
    print("M16_ADAPTER_PASS " + json.dumps({"eng": len(eng), "main": len(main)}))
    return 0


def adapter_ok() -> dict:
    r = load(ADAPTER_REPORT)
    require(hash_ok(r) and r["verdict"] == "PASS", "adapter report missing or not PASS", EXIT_ADAPTER)
    if not all((SHADOW / f).exists() for f in r["shadow"]["files"]):
        adapter.build_shadow(PROJECT, SHADOW)               # deterministic regeneration
    require(r["shadow"]["files"] == load(SHADOW / "M16_SHADOW_README.json")["files"],
            "shadow root differs from the verified adapter report", EXIT_ADAPTER)
    for f, h in r["shadow"]["files"].items():
        require(text_sha((SHADOW / f).read_text(encoding="utf-8")) == h, f"shadow file drift {f}",
                EXIT_ADAPTER)
    return r


# ------------------------------------------------------------------ dry-run (resource preflight)
def dryrun_select() -> int:
    d = design()
    rows = rows220()
    salt = d["constants"]["dryrun_salt"]
    pick = {}
    for era in adapter.ERAS:
        cands = sorted((hashlib.sha256(f"{salt}|{t}".encode()).hexdigest(), t)
                       for t, r in rows.items() if r["era_key"] == era)
        require(bool(cands), f"no frame task for era {era}")
        pick[era] = cands[0][1]
    rec = {"artifact": "m16_dryrun_selection", "artifact_sha256": "", "salt": salt,
           "rule": "per era: min sha256(salt|task_id) over the frozen 220 frame; inputs = frame + "
                   "per_task_v2 era only (selector-blind)", "tasks": pick, "utc": now()}
    if DRY_SEL.exists():
        old = load(DRY_SEL)
        require(hash_ok(old) and old["tasks"] == pick, "existing dry-run selection differs")
        return 0
    write(DRY_SEL, self_hash(rec))
    print("M16_DRYRUN_SELECTED " + json.dumps(pick))
    return 0


def dryrun_execute(max_tasks: int) -> int:
    design()
    adapter_ok()
    sel = load(DRY_SEL)
    require(hash_ok(sel), "dry-run selection hash")
    rows = rows220()
    done = 0
    for era, t in sel["tasks"].items():
        p = DRY / t / "record.json"
        st = record_state(p)
        require(st != "CORRUPT", f"corrupt dry-run record {t}")
        if st == "VALID" or done >= max_tasks:
            continue
        stop_flag()
        hold_check()
        snaps: dict[str, dict] = {}
        w = world()

        def between(label: str, _s=snaps, _w=w) -> None:
            _s[label] = _w.snapshot(label, heavy=label in ("before_t", "after_p"))
        rec = run_with_attempts("dryrun", DRY / "attempts.jsonl", t,
                                lambda: w.oracle_task(t, rows[t], DRY / t / "raw_tmp", between))
        require(rec["status"] in ("DONE", "ENV_INSTALL_BLOCKED") and
                all(k in snaps for k in ("before_t", "after_t", "after_p")),
                f"dry-run task {t} did not produce a measurable run ({rec['status']}); brain review",
                EXIT_INFRA)
        tid = t.split("-")[-1][:12]
        evidence = 0
        if rec["status"] == "DONE":
            rec["junit_raw_sha256"] = r1.pack_raw(DRY / t / "raw_tmp", DRY / t / "junit_raw.tar.gz")
            evidence += (DRY / t / "junit_raw.tar.gz").stat().st_size
        else:
            shutil.rmtree(DRY / t / "raw_tmp", ignore_errors=True)
        use_t, src_t = resource.state_use(snaps["before_t"], snaps["after_t"])
        use_p, src_p = resource.state_use(snaps["after_t"], snaps["after_p"])
        rec_body = json.dumps(rec, sort_keys=True).encode("utf-8")
        out = {"artifact": "m16_dryrun_task", "artifact_sha256": "", "era": era, "task_id": t,
               "oracle": rec, "snapshots": snaps, "use_t_gib": use_t, "use_p_gib": use_p,
               "source": src_t if src_t == src_p else f"{src_t}/{src_p}",
               "uv_cache_growth_bytes": ((snaps["after_p"].get("uv_cache_bytes") or 0)
                                         - (snaps["before_t"].get("uv_cache_bytes") or 0)),
               "evidence_bytes": evidence + len(rec_body), "leftovers": w.leftovers(tid),
               "selector_performance_measured": False, "utc": now()}
        lo = out["leftovers"]
        require(all(v == 0 for v in lo.values()), f"transient leftovers after {t} (None = unmeasurable): {lo}",
                EXIT_INFRA)
        write(p, self_hash(out))
        done += 1
        print(f"[m16-dryrun] {era} {t} -> {rec['status']} use_t={use_t:.3f} use_p={use_p:.3f} GiB")
    return 0


def dryrun_complete() -> int:
    sel = load(DRY_SEL) if DRY_SEL.exists() else {"tasks": {}}
    n = sum(record_state(DRY / t / "record.json") == "VALID" for t in sel["tasks"].values())
    print(f"M16_DRYRUN {n}/{len(sel['tasks'])}")
    return 0 if sel["tasks"] and n == len(sel["tasks"]) else EXIT_NOT_YET


def gate_inputs() -> dict:
    sel = load(DRY_SEL)
    recs = [load(DRY / t / "record.json") for t in sel["tasks"].values()]
    rep = adapter_ok()
    dry_sigs = {rep["main"][t]["lock_signature"] for t in sel["tasks"].values()}
    sigs = {v["lock_signature"] for v in rep["main"].values()}
    return {"rows": [{"use_t_gib": r["use_t_gib"], "use_p_gib": r["use_p_gib"], "source": r["source"]}
                     for r in recs],
            "n_new_lock_sets": len(sigs - dry_sigs),
            "evidence_bytes_per_task": max(r["evidence_bytes"] for r in recs),
            "install_status": {r["task_id"]: r["oracle"]["status"] for r in recs},
            "closure_mechanisms": {r["task_id"]: r["oracle"].get("dev_test_closure", {}).get("mechanism")
                                   for r in recs}}


def resource_gate() -> int:
    design()
    require(dryrun_complete() == 0, "dry-run incomplete")
    gi = gate_inputs()
    proj = resource.project(gi["rows"], c_free_now_gib=resource.c_free_gib(),
                            n_new_lock_sets=gi["n_new_lock_sets"],
                            evidence_bytes_per_task=gi["evidence_bytes_per_task"])
    hist = load(DRY_GATE).get("evaluations", []) if DRY_GATE.exists() else []
    hist.append({"utc": now(), "verdict": proj["verdict"],
                 "projected_c_free_at_q09_end_gib": proj["projected_c_free_at_q09_end_gib"],
                 "c_free_now_gib": proj["c_free_now_gib"]})
    write(DRY_GATE, self_hash({"artifact": "m16_resource_gate", "artifact_sha256": "",
                               "inputs": gi, "projection": proj, "verdict": proj["verdict"],
                               "evaluations": hist, "utc": now()}))
    print(f"M16_RESOURCE_GATE {proj['verdict']} projected_end={proj['projected_c_free_at_q09_end_gib']} GiB")
    if proj["verdict"] != "PASS":
        raise Stop("projected C: free at Q09 end below 25 GiB: S3 maintenance required", EXIT_RESOURCE)
    return 0


def gate_recheck() -> dict:
    """Q01: the dry-run gate passed and still passes with today's free space."""
    g = load(DRY_GATE) if DRY_GATE.exists() else None
    require(g is not None and hash_ok(g) and g["verdict"] == "PASS",
            "resource gate record missing or not PASS (run the dry-run plan / S3 first)", EXIT_RESOURCE)
    proj = resource.project(g["inputs"]["rows"], c_free_now_gib=resource.c_free_gib(),
                            n_new_lock_sets=g["inputs"]["n_new_lock_sets"],
                            evidence_bytes_per_task=g["inputs"]["evidence_bytes_per_task"])
    require(proj["verdict"] == "PASS", f"resource gate no longer passes today: {proj}", EXIT_RESOURCE)
    return proj


# ------------------------------------------------------------------ attempts / infra policy
def attempts_for(ledger: Path, task: str) -> list[dict]:
    return [r for r in read_jsonl(ledger) if r["key"] == task]


def run_with_attempts(stage: str, ledger: Path, key: str, fn) -> dict | None:
    """Run fn() under the frozen infra policy. Returns a record, or None when the key just
    became INFRA_UNRESOLVED (caller writes nothing more). Raises Stop(79) to yield to a human."""
    tries_here = 0
    while True:
        prior = attempts_for(ledger, key)
        n_infra = sum(r["outcome"] == "INFRA" for r in prior)
        invocations = {r["invocation"] for r in prior if r["outcome"] == "INFRA"}
        tries_here += 1
        try:
            rec = fn()
            outcome = ("INFRA" if rec.get("status") in ("INFRA", "ERROR") else
                       "CLOCK_BLOCKED" if rec.get("status") == "CLOCK_BLOCKED" else
                       "INSTALL_FAIL" if rec.get("status") == "ENV_INSTALL_BLOCKED" else "OK")
            reason = "; ".join(rec.get("infra_reasons", []))
        except Stop:
            raise
        except Exception as exc:  # noqa: BLE001
            if not is_infra(exc):
                raise
            rec, outcome, reason = None, "INFRA", f"{type(exc).__name__}: {exc}"[:500]
        append_jsonl(ledger, {"stage": stage, "key": key, "attempt": len(prior) + 1,
                              "invocation": INVOCATION, "outcome": outcome, "reason": reason,
                              "utc": now()})
        if outcome == "OK":
            return rec
        if outcome == "CLOCK_BLOCKED":
            raise Stop(f"{stage} {key}: host/WSL clock blocked (no attempt consumed)", EXIT_PREFLIGHT)
        if outcome == "INSTALL_FAIL":
            last = prior[-1]["outcome"] if prior else None
            if last == "INSTALL_FAIL":
                rec["status"] = "ENV_INSTALL_BLOCKED"
                rec["install_blocked_rule"] = "frozen INSTALL_FAIL on 2 consecutive attempts"
                return rec
            continue                                          # one immediate re-attempt
        if n_infra + 1 >= MAX_INFRA_ATTEMPTS and len(invocations | {INVOCATION}) >= 2:
            return {"task_id": key, "status": "INFRA_UNRESOLVED", "attempts": n_infra + 1,
                    "last_reason": reason}
        if tries_here >= 2:
            raise Stop(f"{stage} {key}: infrastructure failure ({reason})", EXIT_INFRA)


# ------------------------------------------------------------------ Q03 oracle (R1)
def oracle(max_tasks: int) -> int:
    design()
    adapter_ok()
    rows = rows220()
    done = 0
    for t in frame():
        p = ORACLE / t / "record.json"
        st = record_state(p)
        require(st != "CORRUPT", f"corrupt oracle record {t}")
        if st == "VALID":
            continue
        if done >= max_tasks:
            break
        stop_flag()
        hold_check()
        raw = ORACLE / t / "raw_tmp"
        shutil.rmtree(raw, ignore_errors=True)
        rec = run_with_attempts("oracle", ORACLE / "attempts.jsonl", t,
                                lambda: world().oracle_task(t, rows[t], raw))
        if rec["status"] == "DONE":
            rec["junit_raw_sha256"] = r1.pack_raw(raw, ORACLE / t / "junit_raw.tar.gz")
        else:
            shutil.rmtree(raw, ignore_errors=True)
            if rec["status"] == "INFRA_UNRESOLVED":
                rec["status"] = "ORACLE_INFRA_UNRESOLVED"
        rec.setdefault("task_id", t)
        rec.setdefault("era_key", rows[t]["era_key"])
        rec.setdefault("parent_commit", rows[t]["parent_commit"])
        rec.setdefault("target_commit", rows[t]["target_commit"])
        rec.update({"artifact": "m16_oracle_task", "artifact_sha256": "", "utc": now()})
        write(p, self_hash(rec))
        done += 1
        print(f"[m16-oracle] {t} -> {rec['status']} {rec.get('classification', '')}", flush=True)
    return 0


FINAL_ORACLE = ("DONE", "ENV_INSTALL_BLOCKED", "ORACLE_INFRA_UNRESOLVED")


def oracle_complete() -> int:
    n = 0
    for t in frame():
        p = ORACLE / t / "record.json"
        st = record_state(p)
        if st == "CORRUPT":
            print(f"M16_ORACLE_CORRUPT {t}")
            return EXIT_NOT_YET
        n += st == "VALID" and load(p)["status"] in FINAL_ORACLE
    print(f"M16_ORACLE {n}/220")
    return 0 if n == 220 else EXIT_NOT_YET


def eligibility_rows() -> dict[str, dict]:
    out = {}
    for t in frame():
        r = load(ORACLE / t / "record.json")
        out[t] = {"status": r["status"], "classification": r.get("classification"),
                  "counts": r.get("counts"), "era_key": r.get("era_key"),
                  "record_sha256": r["artifact_sha256"],
                  "eligible": r["status"] == "DONE" and bool(
                      r.get("eligibility", {}).get("PRIMARY_BEHAVIORAL_F2P_ELIGIBLE"))}
    return out


def eligibility_freeze() -> int:
    design()
    require(oracle_complete() == 0, "oracle construction incomplete")
    require(eligibility_verify() == 0, "eligibility recomputation failed")
    rows = eligibility_rows()
    eligible = sorted(t for t, r in rows.items() if r["eligible"])
    rec = {"artifact": "m16_v3_eligibility", "artifact_sha256": "", "design": DESIGN_SHA,
           "rule": "status DONE and PRIMARY_BEHAVIORAL_F2P_ELIGIBLE (oracle-semantics-v2 under "
                   "harness V3 + R1 repetition retention + R2 MAIN inputs)",
           "eligible": eligible, "n_eligible": len(eligible),
           "status_counts": dict(Counter(r["status"] for r in rows.values())),
           "era_counts_eligible": dict(Counter(rows[t]["era_key"] for t in eligible)),
           "tasks": rows, "attempts_ledger_sha256": norm_sha(ORACLE / "attempts.jsonl")
           if (ORACLE / "attempts.jsonl").exists() else "", "utc": now()}
    if ELIG.exists():
        old = load(ELIG)
        require(hash_ok(old) and old["eligible"] == eligible and old["tasks"] == rows,
                "existing eligibility freeze differs")
        return 0
    write(ELIG, self_hash(rec))
    print(f"M16_ELIGIBILITY_FROZEN n_eligible={len(eligible)} {rec['status_counts']}")
    return 0


def recompute_task(rec: dict) -> tuple[dict, dict]:
    """V4: re-derive classes/eligibility from stored per-repetition evidence (pure)."""
    from benchmark.wp2.oracle_semantics_v2 import classify_node_v2, task_eligibility_v2
    texts = rec.get("parent_failure_text", {})
    counts = {k: 0 for k in r1.COUNT_KEYS}
    for nr in rec["node_records"]:
        p = nr["parent_outcomes"]
        collected = any(o != "missing" for o in p)
        cls = classify_node_v2(target_outcomes=list(nr["target_outcomes"]), parent_outcomes=list(p),
                               parent_failure_text=texts.get(nr["node_id"], ""),
                               parent_collects_node=collected, shared_test_support_failed=not collected)
        require(cls == nr["v3_class"], f"V4 class mismatch {rec['task_id']} {nr['node_id']}")
        counts[cls] += 1
    flags = task_eligibility_v2(n_behavioral_f2p=counts["BEHAVIORAL_F2P"],
                                n_symbol_absence_f2p=counts["SYMBOL_ABSENCE_F2P"],
                                n_parent_collection_error=counts["PARENT_COLLECTION_ERROR"],
                                environment_valid=True, task_collection_failure=False)
    return counts, flags


def eligibility_verify() -> int:
    for t in frame():
        rec = load(ORACLE / t / "record.json")
        require(hash_ok(rec), f"oracle record hash {t}")
        if rec["status"] != "DONE":
            continue
        counts, flags = recompute_task(rec)
        require(counts == rec["counts"] and flags == rec["eligibility"], f"V4 recomputation differs {t}")
        if (ORACLE / t / "junit_raw.tar.gz").exists():
            require(hashlib.sha256((ORACLE / t / "junit_raw.tar.gz").read_bytes()).hexdigest()
                    == rec["junit_raw_sha256"], f"raw JUnit archive drift {t}")
    if ELIG.exists():
        e = load(ELIG)
        require(hash_ok(e) and e["tasks"] == eligibility_rows(), "eligibility freeze differs from records")
    print("M16_ELIGIBILITY_VERIFIED")
    return 0


def eligible() -> list[str]:
    e = load(ELIG)
    require(hash_ok(e), "eligibility freeze hash")
    return list(e["eligible"])


# ------------------------------------------------------------------ cold mirror (S1)
MIRROR_SETS = {
    "eligibility": [ELIG, ORACLE, ADAPTER_REPORT, GUARD["main"]],
    "evalsets": [SETS, SETS_FREEZE, EVALSETS],
    "ready": [READY_MEMBERSHIP, READY],
    "scopes": [SCOPES, OPWS_PLAN],
    "result": [ANALYSIS, SUMMARY, REPORT, OPWS_DIR, COMPLETE],
    "dryrun": [DRY, ADAPTER_REPORT],
}


def cold_root() -> Path:
    return Path(os.environ.get("M16_COLD_ROOT", "D:/wp2_cold")) / "m16_v1"


def mirror(stage: str) -> int:
    require(stage in MIRROR_SETS, f"unknown mirror stage {stage}")
    tag = TAGS[stage]
    pushed_tag(tag, [])
    base = cold_root()
    try:
        base.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise Stop(f"cold mirror unreachable {base}: {exc}", EXIT_HOLD) from exc
    files = []
    for src in MIRROR_SETS[stage]:
        if src.is_dir():
            files += sorted(x for x in src.rglob("*") if x.is_file())
        elif src.exists():
            files.append(src)
    copied = {}
    for f in files:
        r = rel(f)
        dst = base / tag / r
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(f, dst)
        h_src, h_dst = hashlib.sha256(f.read_bytes()).hexdigest(), hashlib.sha256(dst.read_bytes()).hexdigest()
        require(h_src == h_dst, f"mirror copy mismatch {r}", EXIT_HOLD)
        copied[r] = h_src
    write(MIRROR_DIR / f"{tag}.json", self_hash({"artifact": "m16_cold_mirror", "artifact_sha256": "",
                                                 "tag": tag, "destination": str(base / tag),
                                                 "n_files": len(copied), "files_sha256": copied,
                                                 "utc": now()}))
    print(f"M16_MIRROR {tag} files={len(copied)} -> {base / tag}")
    return 0


# ------------------------------------------------------------------ Q05 evaluator sets
def oracle_nodes(t: str, cls: str) -> list[str]:
    return sorted(nr["node_id"] for nr in load(ORACLE / t / "record.json")["node_records"]
                  if nr["v3_class"] == cls)


def evalsets(max_tasks: int) -> int:
    design()
    adapter_ok()
    pushed_tag(TAGS["eligibility"], [ELIG])
    done = 0
    for t in eligible():
        p = EVALSETS / t / "evalset.json"
        st = record_state(p)
        require(st != "CORRUPT", f"corrupt evalset record {t}")
        if st == "VALID" or done >= max_tasks:
            continue
        stop_flag()
        hold_check()

        def unit(_t=t) -> dict:
            discovery, res = world().p2pu_unit(_t)
            if res.get("status") in ("ENV_FAIL_P2PU", "INTEGRITY_FAIL"):
                world().p2pu_discard(_t)
                return {"status": "INFRA", "infra_reasons": [f"P2PU:{res.get('status')}"]}
            if res.get("status") == "CLOCK_BLOCKED":
                return {"status": "CLOCK_BLOCKED"}
            require(res.get("status") in ("DONE", "UNDEFINED"), f"P2P-U status {res.get('status')}")
            stable = sorted(n for n, c in res.get("node_classes", {}).items() if c == "STABLE_P2P")
            return {"status": "OK_SET", "p2pu_status": res["status"], "stable": stable,
                    "rediscovery_sha256": discovery.get("rediscovery_sha256", ""),
                    "unit_evidence_sha256": res.get("evidence_sha256", ""),
                    "class_counts": res.get("class_counts", {}),
                    "n_selected": res.get("n_selected", 0),
                    "composition": discovery.get("v3_selection", {}).get("composition_cap200")}
        r = run_with_attempts("evalsets", EVALSETS / "attempts.jsonl", t, unit)
        if r["status"] == "INFRA_UNRESOLVED":
            rec = {"task_id": t, "status": "NOT_READY_EVALUATOR_SET_INFRA_UNRESOLVED",
                   "attempts": r["attempts"]}
        else:
            rec = {"task_id": t, "status": "DEFINED", "behavioral_f2p_node_ids": oracle_nodes(t, "BEHAVIORAL_F2P"),
                   "p2p_s_node_ids": oracle_nodes(t, "P2P_ONLY"), "p2p_u_cap200_stable_ids": r["stable"],
                   "p2pu": {k: r[k] for k in ("p2pu_status", "rediscovery_sha256", "unit_evidence_sha256",
                                               "class_counts", "n_selected", "composition")}}
        rec.update({"artifact": "m16_evalset", "artifact_sha256": "", "utc": now(),
                    "oracle_record_sha256": load(ORACLE / t / "record.json")["artifact_sha256"]})
        write(p, self_hash(rec))
        done += 1
        print(f"[m16-evalsets] {t} -> {rec['status']}", flush=True)
    return 0


def evalsets_complete() -> int:
    el = eligible()
    n = sum(record_state(EVALSETS / t / "evalset.json") == "VALID" for t in el)
    print(f"M16_EVALSETS {n}/{len(el)}")
    return 0 if n == len(el) else EXIT_NOT_YET


def sets_artifact(tasks: dict[str, dict]) -> dict:
    """Same hashed schema that the frozen load_evaluator_sets verifies (m14a sets_artifact)."""
    d = {"artifact": "m16_main_evaluator_sets", "version": "m16-main-evaluator-sets-v3-r1-2026-10-02",
         "tasks": tasks, "hashes": {"artifact_sha256": ""},
         "leakage_note": "EVALUATOR-ONLY. Never readable by generator/prompt modules or selectors."}
    c = copy.deepcopy(d)
    d["hashes"]["artifact_sha256"] = hashlib.sha256(
        json.dumps(c, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    return d


def evalsets_freeze() -> int:
    design()
    require(evalsets_complete() == 0, "evaluator sets incomplete")
    tasks, excluded = {}, {}
    for t in eligible():
        r = load(EVALSETS / t / "evalset.json")
        if r["status"] != "DEFINED":
            excluded[t] = r["status"]
            continue
        tasks[t] = {"behavioral_f2p_node_ids": r["behavioral_f2p_node_ids"],
                    "p2p_s_node_ids": r["p2p_s_node_ids"],
                    "p2p_u_cap200_stable_ids": r["p2p_u_cap200_stable_ids"],
                    "p2p_s_defined": bool(r["p2p_s_node_ids"]),
                    "p2p_u_defined": bool(r["p2p_u_cap200_stable_ids"])}
    art = sets_artifact(tasks)
    if SETS.exists():
        require(load(SETS) == art, "existing evaluator sets differ")
    else:
        write(SETS, art)
    write_frozen(SETS_FREEZE, self_hash({"artifact": "m16_evalsets_freeze", "artifact_sha256": "",
                                  "sets_artifact_sha256": art["hashes"]["artifact_sha256"],
                                  "n_tasks": len(tasks), "excluded": excluded,
                                  "undefined_p2p_s": sorted(t for t, v in tasks.items() if not v["p2p_s_defined"]),
                                  "undefined_p2p_u": sorted(t for t, v in tasks.items() if not v["p2p_u_defined"]),
                                  "eligibility_sha256": load(ELIG)["artifact_sha256"], "utc": now()}))
    print(f"M16_EVALSETS_FROZEN n={len(tasks)} excluded={len(excluded)}")
    return 0


def sets() -> dict:
    f = load(SETS_FREEZE)
    require(hash_ok(f), "evalsets freeze hash")
    d = load(SETS)
    c = copy.deepcopy(d)
    c["hashes"]["artifact_sha256"] = ""
    got = hashlib.sha256(json.dumps(c, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    require(got == d["hashes"]["artifact_sha256"] == f["sets_artifact_sha256"], "evaluator sets drift")
    return d["tasks"]


# ------------------------------------------------------------------ Q06 readiness
def decide_ready(rec: dict) -> str:
    """Pure (unit-tested): the readiness decision from a stored record."""
    if rec.get("infra_unresolved"):
        return "NOT_READY_INFRA_UNRESOLVED"
    neg = rec.get("negative") or {}
    if (neg.get("strict", {}).get("f2p_task") != "FAIL"
            or neg.get("robust", {}).get("p2p_s_task") not in PASSISH
            or neg.get("robust", {}).get("p2p_u200_task") not in PASSISH):
        return "NOT_READY_NEGATIVE_CONTROL_INVALID"
    pos = rec.get("positive") or {}
    if not pos.get("scoped_diff_nonempty"):
        return "NOT_READY_EMPTY_SCOPED_GOLD"
    if pos.get("apply_error"):
        return "NOT_READY_SCOPED_GOLD_DOES_NOT_APPLY"
    if not (pos.get("robust") or {}).get("resolved"):
        return "NOT_READY_SCOPED_GOLD_NOT_RESOLVED"
    return "READY"


def readiness_one(t: str, tset: dict) -> dict:
    from scripts import wp2_m14r_core as core
    w = world()
    groups, tree, _ = w.evaluate(t, "rneg", "", e1=False, diag=None, parent_starts_ok=True)
    write(READY / t / "negative_groups.json", self_hash({"task_id": t, "groups": groups, "tree_sha": tree,
                                                         "artifact_sha256": ""}))
    rec: dict[str, Any] = {"task_id": t, "negative": {"tree_sha": tree,
                           "strict": core.score_strict(tset, groups), "robust": core.score_robust(tset, groups),
                           "nodes": core.node_report(tset, groups)}}
    graw, gold = w.gold_scope(t)
    diff = w.scoped_gold_diff(t, gold["editable"])
    rec["positive"] = {"gold_raw": graw, "editable": gold["editable"], "excluded_large": gold["excluded_large"],
                       "excluded_budget": gold["excluded_budget"], "scoped_diff_sha256": text_sha(diff),
                       "scoped_diff_identity": core_diff_sha(diff), "scoped_diff_nonempty": bool(diff.strip())}
    if decide_ready(rec) == "NOT_READY_NEGATIVE_CONTROL_INVALID" or not diff.strip():
        return rec
    try:
        pg, ptree, e1d = w.evaluate(t, "rpos", diff, e1=True,
                                    diag=READY / t / "positive_e1_diagnostics.json", parent_starts_ok=True)
    except ValueError as exc:
        rec["positive"]["apply_error"] = str(exc)[:300]
        return rec
    write(READY / t / "positive_groups.json", self_hash({"task_id": t, "groups": pg, "tree_sha": ptree,
                                                         "e1_decision": e1d, "scoped_diff_sha256": text_sha(diff),
                                                         "artifact_sha256": ""}))
    rec["positive"].update({"tree_sha": ptree, "strict": core.score_strict(tset, pg),
                            "robust": core.score_robust(tset, pg), "e1_decision": e1d,
                            "nodes": core.node_report(tset, pg)})
    return rec


def readiness(max_tasks: int) -> int:
    design()
    adapter_ok()
    pushed_tag(TAGS["evalsets"], [SETS, SETS_FREEZE])
    s = sets()
    done = 0
    for t in sorted(s):
        p = READY / t / "record.json"
        st = record_state(p)
        require(st != "CORRUPT", f"corrupt readiness record {t}")
        if st == "VALID" or done >= max_tasks:
            continue
        stop_flag()
        hold_check()
        rec = run_with_attempts("readiness", READY / "attempts.jsonl", t, lambda _t=t: readiness_one(_t, s[_t]))
        if rec.get("status") == "INFRA_UNRESOLVED":
            rec = {"task_id": t, "infra_unresolved": True, "attempts": rec["attempts"]}
        rec["decision"] = decide_ready(rec)
        rec.update({"artifact": "m16_readiness_task", "artifact_sha256": "", "utc": now()})
        write(p, self_hash(rec))
        done += 1
        print(f"[m16-readiness] {t} -> {rec['decision']}", flush=True)
    return 0


def readiness_complete() -> int:
    s = sets()
    n = sum(record_state(READY / t / "record.json") == "VALID" for t in s)
    print(f"M16_READINESS {n}/{len(s)}")
    return 0 if n == len(s) else EXIT_NOT_YET


def ready_verify() -> int:
    """V3: every decision is recomputed from the stored groups with the frozen scoring."""
    from scripts import wp2_m14r_core as core
    s = sets()
    member = []
    for t in sorted(s):
        rec = load(READY / t / "record.json")
        require(hash_ok(rec), f"readiness record hash {t}")
        if not rec.get("infra_unresolved"):
            ng = load(READY / t / "negative_groups.json")
            require(hash_ok(ng), f"negative groups hash {t}")
            require(rec["negative"]["strict"] == core.score_strict(s[t], ng["groups"]) and
                    rec["negative"]["robust"] == core.score_robust(s[t], ng["groups"]), f"V3 negative {t}")
            if (READY / t / "positive_groups.json").exists():
                pg = load(READY / t / "positive_groups.json")
                require(hash_ok(pg), f"positive groups hash {t}")
                require(rec["positive"]["robust"] == core.score_robust(s[t], pg["groups"]), f"V3 positive {t}")
        require(decide_ready(rec) == rec["decision"], f"V3 decision {t}")
        if rec["decision"] == "READY":
            member.append(t)
    if READY_MEMBERSHIP.exists():
        m = load(READY_MEMBERSHIP)
        require(hash_ok(m) and m["members"] == member, "READY membership differs from recomputation")
    print(f"M16_READY_VERIFIED n_ready={len(member)}")
    return 0


def ready_freeze() -> int:
    d = design()
    require(readiness_complete() == 0, "readiness incomplete")
    require(ready_verify() == 0, "readiness verification failed")
    s = sets()
    recs = {t: load(READY / t / "record.json") for t in sorted(s)}
    members = sorted(t for t, r in recs.items() if r["decision"] == "READY")
    pool_min = d["constants"]["pool_min"]
    rec = {"artifact": "m16_ready_membership", "artifact_sha256": "", "design": DESIGN_SHA,
           "members": members, "n_ready": len(members), "ready_membership_sha256": sha_obj(members),
           "not_ready": {t: r["decision"] for t, r in recs.items() if r["decision"] != "READY"},
           "pool_gate": {"pool_min": pool_min, "descriptive_only": len(members) < pool_min},
           "readiness_records_sha256": {t: r["artifact_sha256"] for t, r in recs.items()},
           "attempts_ledger_sha256": norm_sha(READY / "attempts.jsonl") if (READY / "attempts.jsonl").exists() else "",
           "evalsets_freeze_sha256": load(SETS_FREEZE)["artifact_sha256"], "utc": now()}
    if READY_MEMBERSHIP.exists():
        old = load(READY_MEMBERSHIP)
        require(hash_ok(old) and old["members"] == members, "existing READY membership differs")
        return 0
    write(READY_MEMBERSHIP, self_hash(rec))
    print(f"M16_READY_FROZEN n_ready={len(members)} descriptive_only={rec['pool_gate']['descriptive_only']}")
    return 0


def members() -> list[str]:
    m = load(READY_MEMBERSHIP)
    require(hash_ok(m), "READY membership hash")
    return list(m["members"])


# ------------------------------------------------------------------ Q08 scopes (selector-aware)
def selector_raw() -> dict[str, dict[str, list[str]]]:
    d = design()
    for f in (WP1A_PRED, WP1B_MAIN, WP1B_VAR):
        require(norm_sha(PROJECT / f) == d["pins"]["file_norm_sha256"][f], f"selector input drift {f}")
    pred = load(PROJECT / WP1A_PRED)["per_task"]
    main = {r["task_id"]: r for r in read_jsonl(PROJECT / WP1B_MAIN)}
    var: dict[str, dict[int, list[str]]] = {}
    for r in read_jsonl(PROJECT / WP1B_VAR):
        var.setdefault(r["task_id"], {})[int(r["replicate"])] = sorted(r.get("selected_paths") or [])
    out = {}
    for t in pred:
        row = {"RMCSS_HARD": sorted(pred[t].get("rmcss_predicted_set") or [])}
        if t in main:
            require(main[t].get("replicate") == 0, f"main agent record not replicate 0 {t}")
            row["AGENT_MAIN"] = sorted(main[t].get("selected_paths") or [])
        for k in (1, 2, 3):
            if k in var.get(t, {}):
                row[f"AGENT_r{k}"] = var[t][k]
        out[t] = row
    return out


def file_prf(editable: list[str], gold: list[str]) -> dict:
    e, g = set(editable), set(gold)
    tp = len(e & g)
    p = tp / len(e) if e else 0.0
    r = tp / len(g) if g else 0.0
    return {"precision": round(p, 6), "recall": round(r, 6),
            "f1": round(2 * p * r / (p + r), 6) if p + r else 0.0, "tp": tp,
            "n_editable": len(e), "n_gold": len(g)}


def scopes() -> int:
    design()
    adapter_ok()
    binding = ready_pushed()                                   # P1 (raises 37)
    require(not OPWS_PLAN.exists() or load(OPWS_PLAN)["binding"]["ready_commit"] == binding["commit"],
            "existing OPWS plan bound to another READY commit")
    w = world()
    raw = selector_raw()
    mem = members()
    frozen, items = {}, []
    for t in mem:
        rr = load(READY / t / "record.json")
        graw = rr["positive"]["gold_raw"]
        tscope = {"GOLD_HARD": {"raw": graw, "editable": rr["positive"]["editable"]}}
        for skey in ("GOLD_HARD",) + SELECTORS + REPLICATES:
            if skey != "GOLD_HARD":
                if skey not in raw.get(t, {}):
                    continue
                f = w.editable(t, raw[t][skey])
                tscope[skey] = {"raw": raw[t][skey], "editable": f["editable"],
                                "excluded_large": f["excluded_large"], "excluded_budget": f["excluded_budget"]}
            ps = sorted(set(tscope[skey]["editable"]) & set(graw))
            it = {"task_id": t, "selector": skey, "opws_files": ps,
                  "file_prf": file_prf(tscope[skey]["editable"], graw)}
            if not ps:
                it.update({"kind": "EMPTY_BY_CONSTRUCTION", "coverage": "NONE", "diff_sha256_raw": "",
                           "identity": ""})
            else:
                diff = w.scoped_gold_diff(t, ps)
                require(bool(diff.strip()), f"restricted gold diff empty for non-empty P_S {t}/{skey}")
                dp = OPWS_DIR / t / safe(skey) / "opws_diff.patch"
                dp.parent.mkdir(parents=True, exist_ok=True)
                dp.write_text(diff, encoding="utf-8", newline="")
                rawsha = text_sha(diff)
                reuse = rawsha == rr["positive"]["scoped_diff_sha256"]
                it.update({"kind": "REUSE_SCOPED_GOLD" if reuse else "EVALUATE",
                           "coverage": "FULL" if reuse else "PARTIAL", "diff_sha256_raw": rawsha,
                           "identity": core_diff_sha(diff), "diff_path": rel(dp)})
            items.append(it)
        frozen[t] = tscope
    gold_ok = all(i["kind"] == "REUSE_SCOPED_GOLD" for i in items if i["selector"] == "GOLD_HARD")
    require(gold_ok, "GOLD P_S differs from the readiness scoped gold", EXIT_INVARIANT)
    write_frozen(SCOPES, self_hash({"artifact": "m16_frozen_scopes", "artifact_sha256": "", "tasks": frozen,
                             "selector_inputs_norm_sha256": {f: norm_sha(PROJECT / f)
                                                             for f in (WP1A_PRED, WP1B_MAIN, WP1B_VAR)},
                             "editable_filter": "frozen D35 (benchmark.wp2.e2e.scopes.editable_filter)",
                             "utc": now()}))
    plan = {"artifact": "m16_opws_plan", "artifact_sha256": "", "items": items,
            "binding": {"ready_tag": binding["tag"], "ready_commit": binding["commit"],
                        "ready_tag_objects": binding["objects"], "ls_remote_at_q08": binding["ls_remote"],
                        "eligibility_commit": binding["eligibility_commit"],
                        "evalsets_commit": binding["evalsets_commit"],
                        "ready_membership_sha256": load(READY_MEMBERSHIP)["ready_membership_sha256"]},
            "items_sha256": sha_obj(items),
            "rule": "P_S = gold non-test diff restricted to (selector editable INTERSECT GOLD_HARD raw); "
                    "empty -> FAIL by construction; identical to the readiness scoped gold -> readiness "
                    "positive reused; otherwise frozen evaluator + E1 + E1A1", "utc": now()}
    if OPWS_PLAN.exists():
        require(load(OPWS_PLAN)["items"] == items, "existing OPWS plan differs")
    else:
        write(OPWS_PLAN, self_hash(plan))
    print("M16_SCOPES_FROZEN " + json.dumps(dict(Counter(i["kind"] for i in items))))
    return 0


def scopes_verify() -> int:
    plan = load(OPWS_PLAN)
    require(hash_ok(plan) and sha_obj(plan["items"]) == plan["items_sha256"], "OPWS plan hash")
    b = ready_pushed()
    require(b["commit"] == plan["binding"]["ready_commit"] and
            b["objects"] == plan["binding"]["ready_tag_objects"], "P2 binding differs from origin")
    require(sha_obj(members()) == plan["binding"]["ready_membership_sha256"], "membership binding")
    first = git("log", "--format=%H", plan["binding"]["ready_commit"], "--",
                "research/wp2/m16_v1/scopes", "research/wp2/m16_v1/opws").stdout.strip()
    require(not first, "V1: a commit reachable from READY touches scopes/ or opws/")
    touching = [c for c in git("log", "--format=%H", "HEAD", "--", "research/wp2/m16_v1/scopes",
                               "research/wp2/m16_v1/opws").stdout.split() if c]
    for c in touching:
        require(is_ancestor(plan["binding"]["ready_commit"], c), f"V1: {c} is not a descendant of READY")
    for i in plan["items"]:
        if i.get("diff_path"):
            require(text_sha((PROJECT / i["diff_path"]).read_text(encoding="utf-8")) == i["diff_sha256_raw"],
                    f"OPWS diff drift {i['diff_path']}")
    print(f"M16_SCOPES_VERIFIED items={len(plan['items'])} commits_touching={len(touching)}")
    return 0


# ------------------------------------------------------------------ Q09 OPWS evaluation
def unique_path(t: str, identity: str) -> Path:
    require(len(identity) == 64, "full identity required")
    return OPWS_DIR / "unique" / t / identity / "evaluation.json"


def opws_record_path(t: str, skey: str) -> Path:
    return OPWS_DIR / t / safe(skey) / "opws.json"


def evaluation_record(t: str, identity: str, groups: dict, tset: dict, tree: str, e1: str,
                      source: str) -> dict:
    from scripts import wp2_m14r_core as core
    return self_hash({"task_id": t, "identity": identity, "tree_sha": tree, "status": "DONE",
                      "groups": groups, "strict": core.score_strict(tset, groups),
                      "robust": core.score_robust(tset, groups), "nodes": core.node_report(tset, groups),
                      "e1_decision": e1, "evaluation_source": source, "evaluation_sha256": ""},
                     "evaluation_sha256")


def opws_evaluate(max_evals: int) -> int:
    design()
    adapter_ok()
    plan = load(OPWS_PLAN)
    require(hash_ok(plan), "OPWS plan hash")
    b = pushed_tag(TAGS["ready"], [READY_MEMBERSHIP])
    require(b["commit"] == plan["binding"]["ready_commit"] and
            b["objects"] == plan["binding"]["ready_tag_objects"], "P2: READY binding differs from origin")
    pushed_tag(TAGS["scopes"], [OPWS_PLAN, SCOPES])
    s = sets()
    done = 0
    for i in plan["items"]:
        p = opws_record_path(i["task_id"], i["selector"])
        st = record_state(p)
        require(st != "CORRUPT", f"corrupt OPWS record {p}")
        if st == "VALID":
            continue
        t, tset = i["task_id"], s[i["task_id"]]
        rr = load(READY / t / "record.json")
        require(rr["decision"] == "READY", f"task not READY {t}")
        ev = None
        if i["kind"] == "EMPTY_BY_CONSTRUCTION":
            strict = {"f2p_task": "FAIL", "p2p_s_task": "PASS_BY_CONSTRUCTION",
                      "p2p_u200_task": "PASS_BY_CONSTRUCTION", "resolved": False}
            robust, source, e1d = dict(strict), "EMPTY_BY_CONSTRUCTION", ""
        else:
            up = unique_path(t, i["identity"])
            ust = record_state(up, "evaluation_sha256")
            require(ust != "CORRUPT", f"corrupt evaluation record {up}")
            if ust == "ABSENT":
                if i["kind"] == "REUSE_SCOPED_GOLD":
                    pg = load(READY / t / "positive_groups.json")
                    require(hash_ok(pg), "positive groups hash")
                    ev = evaluation_record(t, i["identity"], pg["groups"], tset, pg["tree_sha"],
                                           pg["e1_decision"], "READINESS_POSITIVE_CONTROL")
                else:
                    if done >= max_evals:
                        break
                    stop_flag()
                    hold_check()
                    diff = (PROJECT / i["diff_path"]).read_text(encoding="utf-8")
                    require(text_sha(diff) == i["diff_sha256_raw"], f"OPWS diff drift {p}")
                    lab = "u_" + i["identity"][:12]
                    diag = OPWS_DIR / "diagnostics" / t / lab / "e1_diagnostics.json"

                    def run_one(_t=t, _lab=lab, _diff=diff, _diag=diag, _id=i["identity"], _ts=tset) -> dict:
                        try:
                            g, tree, e1 = world().evaluate(_t, _lab, _diff, e1=True, diag=_diag,
                                                           parent_starts_ok=True)
                        except ValueError as exc:
                            raise Stop(f"frozen restricted diff does not apply: {exc}") from exc
                        return evaluation_record(_t, _id, g, _ts, tree, e1, "OPWS_EVALUATED")
                    ev = run_with_attempts("opws", OPWS_DIR / "attempts.jsonl", f"{t}/{i['identity']}", run_one)
                    if ev.get("status") == "INFRA_UNRESOLVED":
                        ev = self_hash({"task_id": t, "identity": i["identity"], "status": "INFRA_UNRESOLVED",
                                        "attempts": ev["attempts"], "evaluation_sha256": ""},
                                       "evaluation_sha256")
                    done += 1
                write(up, ev)
            ev = load(up)
            if ev["status"] == "INFRA_UNRESOLVED":
                strict = robust = {"resolved": None}
                source, e1d = "INFRA_UNRESOLVED", ""
            else:
                strict, robust, source, e1d = ev["strict"], ev["robust"], ev["evaluation_source"], ev["e1_decision"]
        rec = self_hash({"artifact": "m16_opws_result", "task_id": t, "selector": i["selector"],
                         "kind": i["kind"], "coverage": i["coverage"], "identity": i["identity"],
                         "opws_files": i["opws_files"], "file_prf": i["file_prf"], "strict": strict,
                         "robust": robust, "opws_strict": strict.get("resolved"),
                         "opws_robust": robust.get("resolved"), "e1_decision": e1d,
                         "nodes": (ev or {}).get("nodes"), "evaluation_source": source,
                         "artifact_sha256": ""})
        write(p, rec)
        print(f"[m16-opws] {t} {i['selector']} -> robust={rec['opws_robust']} ({source})", flush=True)
    print(f"M16_OPWS_CHUNK evaluated={done}")
    return 0


def opws_complete() -> int:
    if not OPWS_PLAN.exists():
        return EXIT_NOT_YET
    items = load(OPWS_PLAN)["items"]
    st = [record_state(opws_record_path(i["task_id"], i["selector"])) for i in items]
    n = st.count("VALID")
    print(f"M16_OPWS {n}/{len(items)} corrupt={st.count('CORRUPT')}")
    if n != len(items) or "CORRUPT" in st:
        return EXIT_NOT_YET
    res = [load(opws_record_path(i["task_id"], i["selector"])) for i in items]
    body = {"artifact": "m16_opws_complete", "artifact_sha256": "", "n_items": len(items),
            "infra_unresolved_items": sum(r["evaluation_source"] == "INFRA_UNRESOLVED" for r in res),
            "plan_sha256": load(OPWS_PLAN)["artifact_sha256"]}
    if COMPLETE.exists():
        require(load(COMPLETE) == self_hash(dict(body)), "OPWS completeness record differs")
    else:
        write(COMPLETE, self_hash(body))
    return 0


# ------------------------------------------------------------------ Q11 analysis
def results() -> dict[tuple[str, str], dict]:
    return {(i["task_id"], i["selector"]): load(opws_record_path(i["task_id"], i["selector"]))
            for i in load(OPWS_PLAN)["items"]}


def failing_side(r: dict) -> str:
    rb = r.get("robust") or {}
    if r["kind"] == "EMPTY_BY_CONSTRUCTION":
        return "EMPTY_SCOPE"
    if rb.get("resolved"):
        return "PASS"
    nodes = r.get("nodes") or {}
    if r.get("e1_decision", "").startswith("PATCH_STARTUP_FAILURE"):
        return "PATCH_STARTUP"
    if rb.get("f2p_task") != "PASS":
        return "ZERO_F2P" if nodes.get("f2p_pass3", 0) == 0 else "PARTIAL_F2P"
    return "PRESERVATION"


def analyze() -> int:
    d = design()
    adapter_ok()                                               # regenerates the shadow root if absent
    require(opws_complete() == 0, "OPWS incomplete")
    scopes_verify()
    res = results()
    mem = members()
    s = sets()
    sc = load(SCOPES)["tasks"]
    rows220_ = rows220()
    drop = sorted({t for (t, k), r in res.items() if r["evaluation_source"] == "INFRA_UNRESOLVED"})
    T = [t for t in mem if t not in drop]
    evaluated = [(t, k) for (t, k), r in res.items() if t in T and r["evaluation_source"] == "OPWS_EVALUATED"]
    amended_items = sorted((t, k) for (t, k) in evaluated
                           if res[(t, k)].get("e1_decision") == "PATCH_STARTUP_FAILURE_E1A1")
    amended = sorted({t for t, _ in amended_items})
    n_eval = len(evaluated)
    gold_ok = all(res[(t, "GOLD_HARD")]["opws_robust"] for t in T)
    pair = [(bool(res[(t, "RMCSS_HARD")]["opws_robust"]), bool(res[(t, "AGENT_MAIN")]["opws_robust"])) for t in T]
    pair_strict = [(bool(res[(t, "RMCSS_HARD")]["opws_strict"]), bool(res[(t, "AGENT_MAIN")]["opws_strict"]))
                   for t in T]
    primary = stats.paired_analysis(pair)
    complete = opws_complete() == 0
    status = stats.run_status(stop_reason=None if gold_ok else "GOLD_IDENTITY", n_ready=len(mem),
                              listwise_drop_frac=(len(drop) / len(mem)) if mem else 1.0,
                              amended_frac=(len(amended_items) / n_eval) if n_eval else 0.0, complete=complete,
                              pool_min=d["constants"]["pool_min"])
    per_sel = {}
    for k in ("GOLD_HARD",) + SELECTORS:
        rs = [res[(t, k)] for t in T]
        cov = Counter(r["coverage"] for r in rs)
        part = [r for r in rs if r["coverage"] == "PARTIAL"]
        per_sel[k] = {"theta_robust": stats.proportion(sum(bool(r["opws_robust"]) for r in rs), len(rs)),
                      "theta_strict": stats.proportion(sum(bool(r["opws_strict"]) for r in rs), len(rs)),
                      "coverage_counts": dict(cov),
                      "p_full": stats.proportion(cov.get("FULL", 0), len(rs)),
                      "p_partial_and_pass": stats.proportion(sum(bool(r["opws_robust"]) for r in part), len(rs)),
                      "pi_partial_rescue": stats.proportion(sum(bool(r["opws_robust"]) for r in part), len(part)),
                      "mean_precision": _mean([r["file_prf"]["precision"] for r in rs]),
                      "mean_recall": _mean([r["file_prf"]["recall"] for r in rs]),
                      "mean_f1": _mean([r["file_prf"]["f1"] for r in rs]),
                      "mean_editable_files": _mean([len(sc[t][k]["editable"]) for t in T]),
                      "sufficient_per_editable_file": _ratio(sum(bool(r["opws_robust"]) for r in rs),
                                                             sum(len(sc[t][k]["editable"]) for t in T))}
    cross = Counter((res[(t, "RMCSS_HARD")]["coverage"], res[(t, "AGENT_MAIN")]["coverage"]) for t in T)
    cross_pass = Counter((res[(t, "RMCSS_HARD")]["coverage"], res[(t, "AGENT_MAIN")]["coverage"],
                          bool(res[(t, "RMCSS_HARD")]["opws_robust"]), bool(res[(t, "AGENT_MAIN")]["opws_robust"]))
                         for t in T)
    disagree = []
    for t in T:
        a, g = res[(t, "RMCSS_HARD")], res[(t, "AGENT_MAIN")]
        if bool(a["opws_robust"]) != bool(g["opws_robust"]):
            disagree.append({"task_id": t, "cell": "b_rmcss_only" if a["opws_robust"] else "c_agent_only",
                             "era": rows220_[t]["era_key"], "n_f2p": len(s[t]["behavioral_f2p_node_ids"]),
                             "n_gold_raw": len(sc[t]["GOLD_HARD"]["raw"]),
                             "rmcss": {"coverage": a["coverage"], "n_editable": len(sc[t]["RMCSS_HARD"]["editable"]),
                                       "failing_side": failing_side(a)},
                             "agent": {"coverage": g["coverage"], "n_editable": len(sc[t]["AGENT_MAIN"]["editable"]),
                                       "failing_side": failing_side(g)}})
    by_era = {}
    for era in adapter.ERAS:
        sub = [pair[i] for i, t in enumerate(T) if rows220_[t]["era_key"] == era]
        by_era[era] = stats.paired_table(sub) | {"delta_hat": ((sum(1 for r, g in sub if r and not g)
                                                               - sum(1 for r, g in sub if g and not r)) / len(sub))
                                                 if sub else None}
    sizes = sorted(len(sc[t]["GOLD_HARD"]["raw"]) for t in T)
    cut = (sizes[len(sizes) // 3], sizes[2 * len(sizes) // 3]) if sizes else (0, 0)
    def tercile(n: int) -> str:
        return "T1" if n <= cut[0] else "T2" if n <= cut[1] else "T3"
    by_size = {}
    for tc in ("T1", "T2", "T3"):
        sub = [pair[i] for i, t in enumerate(T) if tercile(len(sc[t]["GOLD_HARD"]["raw"])) == tc]
        by_size[tc] = stats.paired_table(sub)
    reps = replicate_analysis(T, res, sc)
    sens_amended = stats.paired_analysis([pair[i] for i, t in enumerate(T) if t not in amended])
    out = {"artifact": "m16_analysis", "artifact_sha256": "", "design": DESIGN_SHA,
           "run_status": status, "n_ready": len(mem), "n_analysed": len(T), "listwise_dropped": drop,
           "amended_e1a1_tasks": amended, "amended_e1a1_items": [list(x) for x in amended_items],
           "amended_item_rate": (len(amended_items) / n_eval) if n_eval else 0.0,
           "n_evaluated_items": n_eval, "gold_invariant_ok": gold_ok,
           "primary_robust": primary, "secondary_strict": stats.paired_analysis(pair_strict),
           "strict_robust_discordance": sum(1 for (t, k), r in res.items() if t in T and k != "GOLD_HARD"
                                            and bool(r["opws_strict"]) != bool(r["opws_robust"])),
           "per_selector": per_sel,
           "coverage_cross_table": {f"{a}|{b}": n for (a, b), n in sorted(cross.items())},
           "coverage_cross_table_with_passes": {f"{a}|{b}|R={int(c)}|A={int(e)}": n
                                                for (a, b, c, e), n in sorted(cross_pass.items())},
           "disagreement_listing": disagree, "by_era": by_era, "gold_size_tercile_cuts": list(cut),
           "by_gold_size_tercile": by_size,
           "listwise_bounds": stats.adversarial_bounds(pair, len(drop)),
           "sensitivity_excluding_e1a1_amended": sens_amended,
           "replicates_descriptive": reps,
           "transportability_descriptive": transportability(T),
           "tokens": tokens_for(status, primary), "utc": now()}
    write_frozen(ANALYSIS, self_hash(out), overwrite_if_different=True)
    print("M16_ANALYSIS " + json.dumps(out["tokens"]))
    return 0


def _mean(xs: list[float]) -> float | None:
    return round(sum(xs) / len(xs), 6) if xs else None


def _ratio(a: int, b: int) -> float | None:
    return round(a / b, 6) if b else None


def tokens_for(status: str, primary: dict) -> dict:
    issued = status == "M16_OPWS_COMPLETE" and primary.get("n")
    return {"run_status": status,
            "ci_position": primary["ci_position"] if issued else "NOT_ISSUED",
            "band_position": primary["band_position"] if issued else "NOT_ISSUED",
            "method_agreement": primary.get("method_agreement", "NOT_ISSUED") if issued else "NOT_ISSUED"}


def replicate_analysis(T: list[str], res: dict, sc: dict) -> dict:
    ov = [t for t in T if all((t, r) in res for r in REPLICATES)]
    if not ov:
        return {"n_overlap": 0}
    def jac(a: list[str], b: list[str]) -> float:
        sa, sb = set(a), set(b)
        return 1.0 if not sa and not sb else len(sa & sb) / len(sa | sb)
    per = {r: sum(bool(res[(t, r)]["opws_robust"]) for t in ov) for r in REPLICATES}
    maj = sum(sum(bool(res[(t, r)]["opws_robust"]) for r in REPLICATES) >= 2 for t in ov)
    agree = sum(len({bool(res[(t, r)]["opws_robust"]) for r in REPLICATES}) == 1 for t in ov)
    jj = [sum(jac(sc[t][a]["editable"], sc[t][b]["editable"]) for a, b in
              (("AGENT_r1", "AGENT_r2"), ("AGENT_r1", "AGENT_r3"), ("AGENT_r2", "AGENT_r3"))) / 3 for t in ov]
    return {"n_overlap": len(ov), "tasks": ov, "per_replicate_robust": per, "outcome_majority_robust": maj,
            "mean_sufficiency": round(sum(per.values()) / (3 * len(ov)), 6), "all_three_agree": agree,
            "mean_pairwise_jaccard": round(sum(jj) / len(jj), 6),
            "agent_main_robust_on_overlap": sum(bool(res[(t, "AGENT_MAIN")]["opws_robust"]) for t in ov),
            "note": "descriptive only; the main run is not pooled with r1-r3 (WP1b prereg)"}


def transportability(T: list[str]) -> dict:
    """E-D1 (descriptive): file-level F1 vs GOLD_HARD raw, RMCSS - AGENT_MAIN, on T*, its complement
    in MAIN_297 and all 297 (both selectors re-scored against the same gold definition)."""
    w = world()
    raw = selector_raw()
    main_ids = load(PROJECT / MAIN_MANIFEST)["task_ids"]
    diffs: dict[str, float] = {}
    for t in main_ids:
        if t not in raw or "AGENT_MAIN" not in raw[t]:
            continue
        graw = w.gold_raw(t)
        fr = file_prf(w.editable(t, raw[t]["RMCSS_HARD"])["editable"], graw)["f1"]
        fa = file_prf(w.editable(t, raw[t]["AGENT_MAIN"])["editable"], graw)["f1"]
        diffs[t] = fr - fa
    Ts = set(T)
    return {"t_star": stats.bootstrap_mean_diff([diffs[t] for t in T if t in diffs], seed=16001),
            "complement": stats.bootstrap_mean_diff([v for t, v in diffs.items() if t not in Ts], seed=16002),
            "all_297": stats.bootstrap_mean_diff(list(diffs.values()), seed=16003),
            "gold_definition": "GOLD_HARD raw (M/D non-test); differs from WP1's observed change-set proxy",
            "label": "DESCRIPTIVE ONLY (different constructs; no hypothesis)"}


# ------------------------------------------------------------------ Q12 summary + report
FORBIDDEN = ("non-inferior", "noninferior", "non-inferiority", "equivalent", "equivalence",
             "as good as", "better than")
PERMITTED_NEGATIONS = (
    "M16 does not show that either selection is more sufficient, and it does not show that they are equivalent.",
    "The band is an interpretive yardstick, not a non-inferiority or equivalence margin.")
SCOPE_SENTENCE = ("Saleor only; tasks with changed-test evidence, a V3-installable environment, >= 1 V3 "
                  "behavioral F2P node and a passing selector-blind readiness check; gold restricted to "
                  "modified/deleted non-test files (added and renamed files excluded); one Agent run per task.")


SCOPE_CLAUSE = SCOPE_SENTENCE.rstrip(".")


def claim_text(a: dict) -> list[str]:
    tk, pr = a["tokens"], a["primary_robust"]
    n = a["n_analysed"]
    if tk["ci_position"] == "NOT_ISSUED":
        return [f"Run status {tk['run_status']}: estimates are reported descriptively; no CI-position "
                f"or band token is issued. Scope: {SCOPE_SENTENCE}"]
    lo, hi = pr["tango_95"]
    dh = pr["delta_hat"]
    out = []
    if tk["ci_position"] == "DIFFERENCE_CI_INCLUDES_ZERO":
        out.append(f"On {n} MAIN tasks ({SCOPE_CLAUSE}), the difference in robust OPWS sufficiency "
                   f"(RM-CSS minus Agent single run) was {100 * dh:.1f} points (Tango 95% CI "
                   f"{100 * lo:.1f} to {100 * hi:.1f}). The data are compatible with no difference and with "
                   "differences anywhere in that interval.")
        out.append(PERMITTED_NEGATIONS[0])
    else:
        more = "more often" if tk["ci_position"].endswith("POSITIVE") else "less often"
        out.append(f"On {n} MAIN tasks ({SCOPE_CLAUSE}), RM-CSS selections were sufficient {more} than the "
                   f"Agent's single-run selections: {100 * dh:.1f} points (Tango 95% CI {100 * lo:.1f} to "
                   f"{100 * hi:.1f}; exact McNemar p = {pr['mcnemar_exact_p']:.4g}). This is a statement about "
                   "this census and these frozen selections, not about selector quality in general.")
    where = {"CI_INSIDE_DESCRIPTIVE_BAND": "inside", "CI_CROSSES_BAND_EDGE": "across one edge of",
             "CI_WIDER_THAN_BAND": "wider than", "CI_OUTSIDE_BAND": "outside"}[tk["band_position"]]
    out.append(f"Relative to the pre-declared +/-10-point descriptive band, the interval lies {where} the band. "
               + PERMITTED_NEGATIONS[1])
    if tk["method_agreement"] == "DISCORDANT":
        out.append("Inference about whether the difference is zero is method-sensitive.")
    return out


def forbidden_hits(lines: list[str]) -> list[str]:
    hits = []
    for ln in lines:
        txt = ln
        for ok in PERMITTED_NEGATIONS:
            txt = txt.replace(ok, "")
        low = txt.lower()
        hits += [f for f in FORBIDDEN if f in low]
    return hits


def summary() -> int:
    a = load(ANALYSIS)
    require(hash_ok(a), "analysis hash")
    claims = claim_text(a)
    hits = forbidden_hits(claims)
    require(not hits, f"forbidden wording in generated claims {hits}")
    s = {"artifact": "m16_summary", "artifact_sha256": "", "design": DESIGN_SHA, "tokens": a["tokens"],
         "n_ready": a["n_ready"], "n_analysed": a["n_analysed"], "primary_robust": a["primary_robust"],
         "claims": claims, "scope_sentence": SCOPE_SENTENCE, "model_api_calls": 0,
         "analysis_sha256": a["artifact_sha256"], "utc": now()}
    write(SUMMARY, self_hash(s))
    pr = a["primary_robust"]
    lines = ["# WP2 M16 OPWS-MAIN V1 - result", "", f"- run_status: `{a['tokens']['run_status']}`",
             f"- ci_position: `{a['tokens']['ci_position']}`", f"- band_position: `{a['tokens']['band_position']}`",
             f"- method_agreement: `{a['tokens']['method_agreement']}`",
             f"- READY census: {a['n_ready']}; analysed (after listwise drops): {a['n_analysed']}", "",
             "## Claims (generated from the frozen templates)", ""] + [f"- {c}" for c in claims] + [
             "", "## Primary paired table (OPWS_ROBUST)", "", "```", json.dumps(pr.get("table"), indent=1), "```",
             "", "Descriptive analyses (decomposition, replicates, transportability, strata) are in "
             "`research/wp2/m16_v1/analysis/m16_analysis.json`.", ""]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print("M16_SUMMARY " + json.dumps(a["tokens"]))
    return 0


# ------------------------------------------------------------------ CLI
SELECTOR_BLIND = {"guard", "adapter-verify", "dryrun-select", "dryrun-execute", "dryrun-complete",
                  "resource-gate", "oracle", "oracle-complete", "eligibility-freeze", "eligibility-verify",
                  "evalsets", "evalsets-complete", "evalsets-freeze", "readiness", "readiness-complete",
                  "ready-freeze", "ready-verify", "historical-verify"}
PRE_Q08_MIRRORS = {"eligibility", "evalsets", "ready", "dryrun"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    for c in sorted(SELECTOR_BLIND | {"scopes", "scopes-verify", "opws-complete", "analyze", "summary"}):
        q = sp.add_parser(c)
        if c == "guard":
            q.add_argument("--stage", choices=("dryrun", "main"), required=True)
        if c in ("dryrun-execute", "oracle", "evalsets", "readiness"):
            q.add_argument("--max-tasks", type=int, default=1)
    sp.add_parser("opws-evaluate").add_argument("--max-evals", type=int, default=4)
    sp.add_parser("mirror").add_argument("--stage", required=True, choices=sorted(MIRROR_SETS))
    a = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(AttributeError, ValueError):
            stream.reconfigure(errors="replace")
    scrub_provider_env()
    if a.cmd in SELECTOR_BLIND or (a.cmd == "mirror" and a.stage in PRE_Q08_MIRRORS):
        firewall.install(PROJECT, "full")
    else:
        firewall.install(PROJECT, "network")                  # Q08-Q12: no-network, selector reads allowed
    fns = {"guard": lambda: guard(a.stage), "adapter-verify": adapter_verify,
           "dryrun-select": dryrun_select, "dryrun-execute": lambda: dryrun_execute(a.max_tasks),
           "dryrun-complete": dryrun_complete, "resource-gate": resource_gate,
           "oracle": lambda: oracle(a.max_tasks), "oracle-complete": oracle_complete,
           "eligibility-freeze": eligibility_freeze, "eligibility-verify": eligibility_verify,
           "evalsets": lambda: evalsets(a.max_tasks), "evalsets-complete": evalsets_complete,
           "evalsets-freeze": evalsets_freeze, "readiness": lambda: readiness(a.max_tasks),
           "readiness-complete": readiness_complete, "ready-freeze": ready_freeze, "ready-verify": ready_verify,
           "historical-verify": historical_verify, "scopes": scopes, "scopes-verify": scopes_verify,
           "opws-evaluate": lambda: opws_evaluate(a.max_evals), "opws-complete": opws_complete,
           "analyze": analyze, "summary": summary, "mirror": lambda: mirror(a.stage)}
    try:
        rc = fns[a.cmd]()
    except Stop as exc:
        print(f"M16_STOP code={exc.code} {exc}", flush=True)
        rc = exc.code
    except firewall.FirewallViolation as exc:
        print(f"M16_FIREWALL_VIOLATION {exc}", flush=True)
        return EXIT_FIREWALL
    except adapter.AdapterError as exc:
        print(f"M16_ADAPTER_FAIL {exc}", flush=True)
        rc = EXIT_ADAPTER
    if firewall.violations():            # a violation swallowed by frozen code wins over ANY other exit code
        print(f"M16_FIREWALL_VIOLATION (recorded) {firewall.violations()[:3]}", flush=True)
        return EXIT_FIREWALL
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
