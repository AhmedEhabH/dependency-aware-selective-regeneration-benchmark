#!/usr/bin/env python3
"""WP2 M15-R engine: Pilot-B scope sufficiency (OPWS) + gated G0 generation (brain-authored).

Frozen design: research/wp2/m15r_v1/m15r_design_freeze_v1.json (sha pinned below), which
implements docs/WP2_RESHAPE_INDEPENDENT_REVIEW_2026-10-01.md section 11.

  S0  readiness (zero API, Docker): empty-diff negative + scoped-gold positive per Pilot-B task
  --  human authorization (cap <= $3.00 for Agent localization + S2 + S3)
  --  Agent localization (PAID): frozen protocol-v3 Agent, 3 fresh runs per member task
  S1  OPWS (zero API, Docker, PRIMARY): gold non-test diff restricted to the selector's
      editable files, evaluated with the frozen evaluator + E1 semantics
  S2  G0 GOLD viability (PAID): GOLD_HARD x r1-r3 with the M14R G0 episode function
  S3  only if the S2 gate passes (PAID): RMCSS_HARD and AGENT_HARD x r1-r3 with G0

Only `agent` (Agent localization) and `generate` call a model API; `doctor-paid` reads
provider metadata only. Every other subcommand makes zero model/API calls. G0 is the
M14R function `run_base_episode` (context C0) executed UNCHANGED; this engine only
redirects its evidence root and supplies the frozen raw scope of the item it runs.

Exit codes: 0 PASS/progress, 1 check-not-yet, 3 HOLD, 4 stop flag, 31 pool insufficient,
32 not authorized, 33 environment/preflight fail (resumable), 75 provider outage,
76 request rejected, 77 budget, 78 invariant, 79 evaluation infrastructure error.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import traceback
from collections import Counter
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
for _p in (PROJECT, PROJECT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts import wp2_m14r_core as core  # noqa: E402

ROOT = PROJECT / "research/wp2/m15r_v1"
DESIGN = ROOT / "m15r_design_freeze_v1.json"
DESIGN_SHA = "e350bb5be3f456fc74897f833df772c8df1bf288bb0cd1ce962dfac1335db0a7"
PILOT_A = PROJECT / "research/wp2/pilot_a_v1"
PILOT_SETS = PILOT_A / "evaluator_only/pilot_a_evaluator_sets_v1.json"
FINAL_MEMBERSHIP = PILOT_A / "pilot_final_membership.json"
M14R_ROOT = PROJECT / "research/wp2/m14r_v1"
GUARD = ROOT / "m15r_guard.json"
READY = ROOT / "readiness"
MEMBERSHIP = ROOT / "m15r_membership.json"
AUTH = ROOT / "human_authorization.json"
AGENT_PRE = ROOT / "agent_prefreeze.json"
AGENT_DIR = ROOT / "agent"
AGENT_ITEMS = AGENT_DIR / "items"
FREEZE = ROOT / "m15r_freeze.json"
SCOPES = ROOT / "frozen_scopes.json"
PROMPT_META = ROOT / "g0_prompt_meta.json"
OPWS_DIR = ROOT / "opws"
OPWS_PLAN = OPWS_DIR / "plan.json"
OPWS_SUMMARY = ROOT / "opws_summary.json"
PLANS = {"s2": ROOT / "s2_generation_plan.json", "s3": ROOT / "s3_generation_plan.json"}
GEN_FREEZE = {"s2": ROOT / "generation_freeze_s2.json", "s3": ROOT / "generation_freeze_s3.json"}
EVAL_PLAN = {"s2": ROOT / "evaluations/plan_s2.json", "s3": ROOT / "evaluations/plan_s3.json"}
S2_GATE = ROOT / "s2_gate.json"
SUMMARY = ROOT / "m15r_summary.json"
OPWS_REPORT = PROJECT / "docs/WP2_M15R_V1_OPWS_RESULT.md"
REPORT = PROJECT / "docs/WP2_M15R_V1_RESULT.md"
LEDGER = ROOT / "ledger/m15r_generation_spend.jsonl"
STOP_FLAG = PROJECT / "logs/M15R_STOP.flag"
OOF_A = PROJECT / "research/memory-rescue-v2/final_oof_predictions_A.json"
PROTOCOL_V3 = PROJECT / "research/wp1b/wp1b_frozen_agent_protocol_v3.json"
SALEOR_SCIENTIFIC = PROJECT / "benchmark_data/real_commit_impact_saleor/scientific"
SALEOR_CACHE = PROJECT / "dist/pilot-repo-cache/saleor"

APPROVAL_TOKEN = "I_AUTHORIZE_WP2_M15R_V1=YES"
MODEL, PROVIDER = "qwen/qwen3-coder", "deepinfra/turbo"
MAX_USD, MIN_USD, AGENT_CEILING_USD = 3.0, 2.0, 1.25
GENERATION_HEADROOM_USD = 0.75          # S2 + S3 expected ~$0.5 + the $0.12 per-episode reserve
MIN_MEMBERS = 6
REPS = ("r1", "r2", "r3")
SELECTORS = ("RMCSS_HARD", "AGENT_HARD:r1", "AGENT_HARD:r2", "AGENT_HARD:r3")
EMPTY_DIFF_SHA = "16ec795185b645d8d57bd90786f83612f045ee5efe642dd1520f3496ef3b03d3"
TERMINAL = {"NO_SCOPE", "INVALID_AFTER_REPAIR", "APPLIED"}
EXIT_HOLD, EXIT_STOP, EXIT_POOL, EXIT_AUTH, EXIT_PREFLIGHT = 3, 4, 31, 32, 33
EXIT_OUTAGE, EXIT_REJECTED, EXIT_BUDGET, EXIT_INVARIANT, EXIT_EVAL_INFRA = 75, 76, 77, 78, 79
INFRA_EXC = ("EvalInfraError", "RuntimeError", "TimeoutExpired", "CalledProcessError")
AGENT_TAG_PATTERN = "wp2-m15r-v1-agent-freeze-*"
AGENT_CODE_FILES = ("src/benchmark/strategies/iterative_agent.py",
                    "src/benchmark/strategies/repository_tools.py",
                    "src/benchmark/wp1b/telemetry.py", "src/benchmark/wp1b/main_runner.py",
                    "src/benchmark/wp1b/resilient_backend.py", "src/benchmark/wp1b/label_guard.py",
                    "scripts/wp1b_main_run.py", "scripts/saleor_portability_fix.py",
                    "scripts/wp1b_budget_model_v2.py", "scripts/wp2_m15r_run.py")
AGENT_PATHSPECS = ("src/benchmark", "scripts/wp1b_main_run.py", "scripts/saleor_portability_fix.py",
                   "scripts/wp1b_budget_model_v2.py", "scripts/wp2_m15r_run.py",
                   "research/wp1b/wp1b_frozen_agent_protocol_v3.json",
                   "research/wp1b/wp1b_budget_model_v2.json",
                   "research/wp1b/wp1b_decision_rules_v2.json",
                   "research/wp2/m15r_v1/agent_prefreeze.json",
                   "research/wp2/m15r_v1/m15r_design_freeze_v1.json",
                   "research/wp2/pilot_a_v1/evaluator_only/",
                   "research/wp2/harness_v3_2026-09-26/evaluator_only/")
AGENT_FORBIDDEN = ("research/wp2/pilot_a_v1/evaluator_only/",
                   "research/wp2/harness_v3_2026-09-26/evaluator_only/",
                   "research/wp2/pilot_a_v1/readiness/", "research/wp2/pilot_a_v1/evaluations/",
                   "research/wp2/m15r_v1/readiness/", "research/wp2/m15r_v1/evaluations/",
                   "research/wp2/m15r_v1/opws/", "research/wp2/m14r_v1/evaluations/")
M14R_G0 = ["scripts/wp2_m14r_run.py", "scripts/wp2_m14r_core.py"]
KIT = ["scripts/wp2_ctl_v224.py", "scripts/wp2_m15r_run.py", "scripts/wp2_m15r_authorize.py",
       "controller/plan_m15r_v1.json", "controller/light_profile_m15r.json",
       "controller/KIT_MANIFEST_M15R.json"]


class Stop(Exception):  # noqa: N818 - same name as the frozen M14R engine
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


sha_obj = core.sha_obj


def write(p: Path, d: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                 encoding="utf-8", newline="\n")


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


def require(c: bool, m: str, code: int = EXIT_INVARIANT) -> None:
    if not c:
        raise Stop(m, code)


def rel(p: Path) -> str:
    return Path(p).relative_to(PROJECT).as_posix()


def git(*a: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *a], cwd=PROJECT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def record_state(p: Path, key: str = "artifact_sha256") -> str:
    if not p.exists():
        return "ABSENT"
    try:
        return "VALID" if hash_ok(load(p), key) else "CORRUPT"
    except (ValueError, OSError):
        return "CORRUPT"


def m14r():
    """The frozen M14R engine module (imported, never modified)."""
    import scripts.wp2_m14r_run as m
    return m


def design() -> dict:
    d = load(DESIGN)
    require(hash_ok(d) and d["artifact_sha256"] == DESIGN_SHA, "design freeze drift")
    require(d["core_constants_sha256"] == sha_obj(core.design_constants()),
            "M14R core constants differ from the frozen design")
    return d


def population() -> list[str]:
    return list(design()["population"]["pilot_b_tasks"])


def pilot_sets() -> dict:
    d = load(PILOT_SETS)
    c = copy.deepcopy(d)
    c.setdefault("hashes", {})["artifact_sha256"] = ""
    got = hashlib.sha256(json.dumps(c, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    require(got == d.get("hashes", {}).get("artifact_sha256") ==
            design()["pins"]["pilot_sets_artifact_sha256"], "Pilot evaluator sets drift")
    return d["tasks"]


def members() -> list[str]:
    m = load(MEMBERSHIP)
    require(hash_ok(m) and m["verdict"] == "OK", "membership missing or not OK")
    return list(m["members"])


def skey_arm(skey: str) -> str:
    return skey.split(":", 1)[0]


def safe(skey: str) -> str:
    return skey.replace(":", "__")


# ------------------------------------------------------------------ guard
def protected_ids() -> dict[str, set[str]]:
    sel = load(PROJECT / "research/wp2/pilot_v1_design/pilot_selection.json")
    fm = load(FINAL_MEMBERSHIP)
    m14d = load(M14R_ROOT / "m14r_design_freeze_v1.json")
    evaluated = set()
    for sub in ("episodes", "evaluations/unique", "evaluations/episodes"):
        d = PILOT_A / sub
        if d.exists():
            evaluated |= {p.name for p in d.iterdir() if p.is_dir()}
    return {"pilot_a": set(fm["A"]) | set(sel["pilot_a_tasks"]),
            "m14r_eng": set(m14d["population"]["candidate_tasks"]),
            "pilot_a_e1_evaluated": evaluated}


def prior_outputs(tasks: list[str]) -> list[str]:
    """Any generation/evaluation output for a Pilot-B task outside the M15-R root."""
    hits = []
    for base in sorted((PROJECT / "research/wp2").iterdir()):
        if not base.is_dir() or base.name == "m15r_v1":
            continue
        for sub in ("episodes", "evaluations", "opws", "cache_namespaces"):
            d = base / sub
            if d.exists():
                hits += [rel(p) for p in d.rglob("*") if p.is_dir() and p.name in tasks]
    return sorted(hits)


def guard() -> int:
    d = design()
    pins = d["pins"]
    tasks = population()
    import scripts.wp2_m14a_run as m14a
    bad = m14a.verify_generation_freeze()
    require(not bad, f"Pilot-A frozen evidence drift {bad[:3]}")
    bad = m14r().verify_generation_freeze()
    require(not bad, f"M14R frozen evidence drift {bad[:3]}")
    s = load(M14R_ROOT / "m14r_summary.json")
    require(s["artifact_sha256"] == pins["m14r_summary_artifact_sha256"]
            and s["token"] == "M14R_FLOOR_NOT_MET", "M14R summary differs from the reviewed LIGHT")
    pa = load(PILOT_A / "pilot_a_summary.json")
    require(pa["artifact_sha256"] == pins["pilot_a_summary_artifact_sha256"]
            and pa["token"] == "PILOT_A_GENERATOR_FLOOR_HOLD", "Pilot-A summary differs")
    require(load(PILOT_A / "m14a_e1_amendment.json")["artifact_sha256"]
            == pins["m14a_e1_amendment_artifact_sha256"], "E1 amendment differs")
    fm = load(FINAL_MEMBERSHIP)
    require(fm["artifact_sha256"] == pins["pilot_final_membership_artifact_sha256"]
            and fm["B"] == tasks, "Pilot-B list differs from the frozen membership")
    prot = protected_ids()
    for name, ids in prot.items():
        require(not set(tasks) & ids, f"Pilot-B overlaps {name}: {sorted(set(tasks) & ids)}")
    for t in tasks:
        r = load(PILOT_A / "readiness" / t / "record.json")
        require(r.get("artifact_sha256") == fm["readiness_record_sha256"][t]
                and r.get("gold_empty_ok") is True, f"Pilot-A readiness gold_empty_ok fails for {t}")
    hits = prior_outputs(tasks)
    require(not hits, f"Pilot-B generation/evaluation output exists before the freeze {hits[:3]}")
    allowed = {"m15r_design_freeze_v1.json", "reshape_decision_ledger_entry.json",
               "m15r_guard.json", "controller_state.json", "controller_reports"}
    extra = sorted(p.name for p in ROOT.iterdir() if p.name not in allowed)
    require(not extra, f"M15-R root holds outputs before S0 {extra[:5]}")
    sets = pilot_sets()
    for t in tasks:
        require(t in sets and sets[t]["behavioral_f2p_node_ids"], f"no Pilot evaluator set for {t}")
    for r, h in pins["file_norm_sha256"].items():
        require((PROJECT / r).exists() and norm_sha(PROJECT / r) == h, f"pinned file drift {r}")
    for r in d["required_files"]:
        require((PROJECT / r).exists(), f"required file missing {r}")
    write(GUARD, self_hash({"artifact": "m15r_guard", "artifact_sha256": "", "design": DESIGN_SHA,
                            "pilot_b_tasks": tasks, "protected_overlap": [], "prior_outputs": [],
                            "model_api_calls": 0, "utc": now()}))
    print("M15R_GUARD_PASS " + json.dumps({"pilot_b_tasks": len(tasks)}))
    return 0


# ------------------------------------------------------------------ S0 readiness (zero API)
def _ev():
    from scripts.wp2_m14a_evalcore import point_evaluator
    return point_evaluator(PILOT_SETS, ROOT)


def readiness_task(task_id: str, ev: Any = None) -> dict:
    """M14R readiness semantics on the Pilot evaluator sets (negative + scoped-gold positive)."""
    from benchmark.wp2.e2e.scopes import build_arm_scopes
    from scripts.wp2_m14a_evalcore import evaluate_state_safe
    from scripts.wp2_m14a_evalcore_e1 import evaluate_state_e1
    ev = ev or _ev()
    t = pilot_sets()[task_id]
    wt, tree = ev.materialize(task_id, "rneg", "")
    neg = evaluate_state_safe(ev, task_id, "rneg", wt)
    nst, nrb = core.score_strict(t, neg["groups"]), core.score_robust(t, neg["groups"])
    rec: dict[str, Any] = {"task_id": task_id, "negative": {
        "tree_sha": tree, "strict": nst, "robust": nrb, "nodes": core.node_report(t, neg["groups"])}}
    write(READY / task_id / "negative_groups.json",
          self_hash({"task_id": task_id, "groups": neg["groups"], "tree_sha": tree,
                     "junit_files": neg["junit_files"], "artifact_sha256": ""}))
    gold = build_arm_scopes(task_id, "GOLD_HARD")
    diff = m14r().scoped_gold_diff(task_id, gold["editable"])
    rec["positive"] = {"editable": gold["editable"], "excluded_large": gold["excluded_large"],
                       "excluded_budget": gold["excluded_budget"],
                       "scoped_diff_sha256": text_sha(diff),
                       "scoped_diff_identity": core_diff_sha(diff)}
    reason = ""
    if nst["f2p_task"] != "FAIL" or nrb["p2p_s_task"] not in core.PASSISH or \
            nrb["p2p_u200_task"] not in core.PASSISH:
        reason = "NEGATIVE_CONTROL_INVALID"
    elif not diff.strip():
        reason = "EMPTY_SCOPED_GOLD"
    else:
        try:
            wt2, tree2 = ev.materialize(task_id, "rpos", diff)
        except ValueError as exc:
            reason = "SCOPED_GOLD_DOES_NOT_APPLY"
            rec["positive"]["error"] = str(exc)[:300]
        else:
            pos = evaluate_state_e1(ev, task_id, "rpos", wt2, diff_text=diff,
                                    diag_path=READY / task_id / "positive_e1_diagnostics.json",
                                    parent_starts_ok=True)
            pst, prb = core.score_strict(t, pos["groups"]), core.score_robust(t, pos["groups"])
            rec["positive"].update({"tree_sha": tree2, "strict": pst, "robust": prb,
                                    "e1_decision": pos["e1_decision"],
                                    "nodes": core.node_report(t, pos["groups"])})
            write(READY / task_id / "positive_groups.json",
                  self_hash({"task_id": task_id, "groups": pos["groups"], "tree_sha": tree2,
                             "e1_decision": pos["e1_decision"], "scoped_diff_sha256": text_sha(diff),
                             "artifact_sha256": ""}))
            if not prb["resolved"]:
                reason = "SCOPED_GOLD_NOT_RESOLVED"
    rec["decision"] = "READY" if not reason else "NOT_READY_" + reason
    return rec


def readiness(max_new: int, task_fn: Callable[[str], dict] | None = None) -> int:
    design()
    require(GUARD.exists() and hash_ok(load(GUARD)), "guard missing")
    task_fn = task_fn or readiness_task
    done = 0
    for t in population():
        p = READY / t / "record.json"
        st = record_state(p)
        require(st != "CORRUPT", f"corrupt readiness record {t}")
        if st == "VALID":
            continue
        if done >= max_new:
            break
        try:
            rec = task_fn(t)
        except Exception as exc:
            if type(exc).__name__ in INFRA_EXC or isinstance(exc, OSError):
                raise Stop(f"readiness environment failure {t}: {exc}", EXIT_PREFLIGHT) from exc
            raise
        write(p, self_hash(dict(rec, artifact="m15r_readiness_task", artifact_sha256="",
                                model_api_calls=0, utc=now())))
        done += 1
        print(f"[m15r-readiness] {t} -> {rec['decision']}", flush=True)
    print(f"READINESS_CHUNK new={done}")
    return 0


def readiness_check() -> int:
    c = population()
    n = sum(record_state(READY / t / "record.json") == "VALID" for t in c)
    print(f"READINESS_{'COMPLETE' if n == len(c) else 'INCOMPLETE'} {n}/{len(c)}")
    return 0 if n == len(c) else 1


def readiness_ok(task_id: str) -> bool:
    p = READY / task_id / "record.json"
    return record_state(p) == "VALID" and load(p)["decision"] == "READY"


def membership() -> int:
    require(readiness_check() == 0, "readiness incomplete")
    c = population()
    recs = {t: load(READY / t / "record.json") for t in c}
    mem = sorted(t for t in c if recs[t]["decision"] == "READY")
    verdict = "OK" if len(mem) >= MIN_MEMBERS else "POOL_INSUFFICIENT"
    write(MEMBERSHIP, self_hash({
        "artifact": "m15r_membership", "artifact_sha256": "", "verdict": verdict, "members": mem,
        "min_members": MIN_MEMBERS, "excluded": {t: recs[t]["decision"] for t in c if t not in mem},
        "terminal_token": "" if verdict == "OK" else "M15R_POOL_INSUFFICIENT",
        "readiness_record_sha256": {t: recs[t]["artifact_sha256"] for t in c}}))
    print("M15R_MEMBERSHIP " + json.dumps({"verdict": verdict, "n": len(mem)}))
    if verdict != "OK":
        print("M15R_POOL_INSUFFICIENT (frozen fallback: WP2 Option B; human review)")
    return 0 if verdict == "OK" else EXIT_POOL


# ------------------------------------------------------------------ authorization / doctor
def validate_auth() -> dict:
    require(AUTH.exists(), "human_authorization.json missing", EXIT_AUTH)
    a = load(AUTH)
    require(hash_ok(a), "authorization self-hash mismatch", EXIT_AUTH)
    require(a.get("authorized") is True and a.get("approval_token") == APPROVAL_TOKEN,
            "authorization token", EXIT_AUTH)
    require(a.get("design_artifact_sha256") == DESIGN_SHA, "design hash mismatch", EXIT_AUTH)
    require(a.get("membership_artifact_sha256") == load(MEMBERSHIP)["artifact_sha256"],
            "membership hash mismatch", EXIT_AUTH)
    require(a.get("model") == MODEL and a.get("provider") == PROVIDER
            and a.get("allow_fallbacks") is False, "route mismatch", EXIT_AUTH)
    require(a.get("agent_protocol") == "wp1b_frozen_agent_protocol_v3", "agent protocol", EXIT_AUTH)
    cap = a.get("max_total_spend_usd")
    require(isinstance(cap, (int, float)) and MIN_USD <= float(cap) <= MAX_USD,
            f"max spend must be >= {MIN_USD} and <= {MAX_USD}", EXIT_AUTH)
    r = rel(AUTH)
    require(git("ls-files", "--error-unmatch", r).returncode == 0, "authorization not tracked",
            EXIT_AUTH)
    require(not git("status", "--porcelain", "--", r).stdout.strip(),
            "authorization has uncommitted changes", EXIT_AUTH)
    return a


def auth_check() -> int:
    a = validate_auth()
    write(ROOT / "auth_check.json", self_hash({
        "artifact": "m15r_auth_check", "artifact_sha256": "", "auth_artifact_sha256":
        a["artifact_sha256"], "authorized_by": a.get("authorized_by"),
        "max_total_spend_usd": a["max_total_spend_usd"]}))
    print("AUTH_CHECK_PASS " + json.dumps({"by": a.get("authorized_by"),
                                           "max_usd": a["max_total_spend_usd"]}))
    return 0


def agent_pricing_preflight() -> tuple[bool, dict]:
    """Same check as the frozen WP-1b/DEV Agent wrappers (provider metadata only)."""
    sys.path.insert(0, str(PROJECT / "scripts"))
    from wp1b_provider_pricing_preflight import (  # type: ignore[import-not-found]
        FROZEN_COMPLETION_PER_1M_USD,
        FROZEN_PROMPT_PER_1M_USD,
        _fetch_model_metadata,
    )
    payload, error = _fetch_model_metadata()
    rec: dict[str, Any] = {"artifact": "m15r_agent_pricing_preflight", "utc": now()}
    if payload is None:
        rec.update({"live_metadata_available": False, "error": error, "no_drift": False})
        return False, rec
    di = payload.get("deepinfra") or {}
    pr = di.get("pricing", {}) if isinstance(di, dict) else {}
    prompt, completion = float(pr.get("prompt", 0)) * 1e6, float(pr.get("completion", 0)) * 1e6
    ok = bool(di) and abs(prompt - FROZEN_PROMPT_PER_1M_USD) < 1e-9 and \
        abs(completion - FROZEN_COMPLETION_PER_1M_USD) < 1e-9
    rec.update({"live_metadata_available": True, "prompt_per_1m_usd": prompt,
                "completion_per_1m_usd": completion, "no_drift": ok})
    return ok, rec


def doctor(mode: str) -> int:
    checks: dict[str, dict] = {}
    free = shutil.disk_usage(PROJECT).free / 2 ** 30
    checks["disk_free_gib"] = {"ok": free >= 20, "value": round(free, 1)}
    try:
        from benchmark.wp2.harness_v3 import clock_preflight, ensure_postgres_running
        ensure_postgres_running()
        clk = clock_preflight()
        checks["postgres_clock"] = {"ok": clk.get("verdict") != "CLOCK_BLOCKED",
                                    "value": clk.get("verdict")}
    except Exception as exc:
        checks["postgres_clock"] = {"ok": False, "value": str(exc)[:300]}
    try:
        from benchmark.wp2.e2e_v22.common import env_identity
        env = env_identity()
        checks["images"] = {"ok": not env.get("errors"), "value": env}
    except Exception as exc:
        checks["images"] = {"ok": False, "value": str(exc)[:300]}
    checks["saleor_cache"] = {"ok": SALEOR_CACHE.exists(), "value": rel(SALEOR_CACHE)}
    if mode == "paid":
        checks["api_key"] = {"ok": bool(os.environ.get("OPENROUTER_API_KEY", "").strip())}
        out = ROOT / "doctor/key_usage.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            r = subprocess.run([sys.executable, "scripts/wp1b_openrouter_key_usage.py", "--out",
                                str(out)], cwd=PROJECT, capture_output=True, text=True,
                               timeout=180)
            u = load(out) if out.exists() else {}
            credit = u.get("remaining_usd_min_of_sources") or u.get("limit_remaining_usd")
            checks["credit_ge_5"] = {"ok": r.returncode == 0 and credit is not None
                                     and float(credit) >= 5, "value": credit}
        except Exception as exc:
            checks["credit_ge_5"] = {"ok": False, "value": str(exc)[:200]}
        try:
            from scripts.wp2_e2e_v22_doctor import live_pricing
            checks["generation_pricing"] = live_pricing()
        except Exception as exc:
            checks["generation_pricing"] = {"ok": False, "value": str(exc)[:200]}
        try:
            ok, rec = agent_pricing_preflight()
            checks["agent_pricing"] = {"ok": ok, "value": rec}
        except Exception as exc:
            checks["agent_pricing"] = {"ok": False, "value": str(exc)[:200]}
    ok = all(v.get("ok") for v in checks.values())
    write(ROOT / f"doctor/doctor_{mode}.json", self_hash({
        "artifact": "m15r_doctor", "artifact_sha256": "", "mode": mode, "checks": checks,
        "pass": ok, "model_api_calls": 0, "utc": now()}))
    for k, v in checks.items():
        print(f"DOCTOR {'PASS' if v.get('ok') else 'FAIL'} {k} {str(v.get('value', ''))[:160]}")
    return 0 if ok else EXIT_PREFLIGHT


# ------------------------------------------------------------------ Agent localization (paid)
def agent_items(tasks: list[str]) -> list[dict]:
    return [{"key": f"{t}#{rep}", "task_id": t, "replicate": int(rep[1:]), "rep": rep}
            for rep in REPS for t in tasks]


def worst_case(task_id: str) -> dict:
    sys.path.insert(0, str(PROJECT / "scripts"))
    import wp1b_budget_model_v2 as bm  # type: ignore[import-not-found]
    return bm._worst_case(task_id)


def bundle_meta(task_id: str) -> dict:
    base = SALEOR_SCIENTIFIC / task_id
    man = load(base / "case_manifest.json")
    cu = load(base / "public/candidate_universe.json")
    return {"intent_norm_sha256": norm_sha(base / "public/intent.json"),
            "candidate_universe_norm_sha256": norm_sha(base / "public/candidate_universe.json"),
            "parent_commit": str(man.get("record", {}).get("parent_commit", "")),
            "universe_size": len(cu.get("records", []))}


def build_agent_prefreeze() -> dict:
    a = validate_auth()
    tasks = members()
    items = agent_items(tasks)
    wc = {t: worst_case(t) for t in tasks}
    ceiling = min(float(a["max_total_spend_usd"]), AGENT_CEILING_USD)
    total_worst = sum(wc[t]["worst_case_usd"] for t in tasks) * len(REPS)
    require(total_worst <= ceiling, f"Agent worst case ${total_worst:.4f} exceeds the Agent ceiling "
            f"${ceiling:.2f}", EXIT_AUTH)
    require(float(a["max_total_spend_usd"]) - total_worst >= GENERATION_HEADROOM_USD,
            "authorized cap leaves less than the S2/S3 generation headroom", EXIT_AUTH)
    return self_hash({
        "artifact": "m15r_agent_prefreeze", "artifact_sha256": "", "design_artifact_sha256":
        DESIGN_SHA, "membership_artifact_sha256": load(MEMBERSHIP)["artifact_sha256"],
        "auth_artifact_sha256": a["artifact_sha256"], "protocol": "wp1b_frozen_agent_protocol_v3",
        "protocol_norm_sha256": norm_sha(PROTOCOL_V3), "items": items,
        "items_sha256": sha_obj(items), "replicate_rule":
        "replicate r uses Agent run r (fresh run per task per replicate)",
        "worst_case_per_task": wc, "worst_case_total_usd": round(total_worst, 6),
        "agent_ceiling_usd": ceiling, "bundles": {t: bundle_meta(t) for t in tasks},
        "code_norm_sha256": {r: norm_sha(PROJECT / r) for r in AGENT_CODE_FILES},
        "rmcss_predictions_norm_sha256": norm_sha(OOF_A), "model_api_calls": 0})


def agent_prefreeze() -> int:
    pre = build_agent_prefreeze()
    if AGENT_PRE.exists():
        old = load(AGENT_PRE)
        require(old.get("artifact_sha256") == pre["artifact_sha256"],
                "agent prefreeze exists and differs (never rewritten)")
    else:
        require(not AGENT_DIR.exists(), "Agent evidence exists without a prefreeze")
        write(AGENT_PRE, pre)
    print("M15R_AGENT_PREFREEZE " + json.dumps({"items": len(pre["items"]),
                                                "ceiling_usd": pre["agent_ceiling_usd"],
                                                "worst_total_usd": pre["worst_case_total_usd"]}))
    return 0


def agent_prefreeze_record() -> dict:
    require(AGENT_PRE.exists(), "agent prefreeze missing")
    pre = load(AGENT_PRE)
    require(hash_ok(pre) and pre["design_artifact_sha256"] == DESIGN_SHA, "agent prefreeze hash")
    require(pre["membership_artifact_sha256"] == load(MEMBERSHIP)["artifact_sha256"],
            "agent prefreeze membership")
    for r, h in pre["code_norm_sha256"].items():
        require(norm_sha(PROJECT / r) == h, f"Agent code drift since the prefreeze: {r}")
    require(norm_sha(PROTOCOL_V3) == pre["protocol_norm_sha256"], "protocol v3 drift")
    require(norm_sha(OOF_A) == pre["rmcss_predictions_norm_sha256"]
            == design()["pins"]["file_norm_sha256"][rel(OOF_A)], "RM-CSS predictions drift")
    require(pre["auth_artifact_sha256"] == validate_auth()["artifact_sha256"],
            "authorization changed after the Agent prefreeze", EXIT_AUTH)
    return pre


def agent_tag_gate() -> str:
    from benchmark.wp1b import git_gate as gg
    tags = sorted(x for x in git("tag", "--list", AGENT_TAG_PATTERN).stdout.split() if x)
    try:
        # Only tags that reached origin count (a resumed Q07 can leave an unpushed local tag
        # of a failed day); every pushed one must equal origin and the frozen tree.
        pushed = [t for t in tags if gg.remote_tag_objects(PROJECT, t)["object"]]
        require(bool(pushed), f"no agent-freeze tag on origin (local: {tags})", EXIT_PREFLIGHT)
        for tag in pushed:
            gg.verify_tag_on_origin(PROJECT, tag)
            gg.verify_tree_matches_tag(PROJECT, tag, AGENT_PATHSPECS)
    except gg.GitRemoteUnavailableError as exc:
        raise Stop(f"origin unreachable for the tag gate: {exc}", EXIT_PREFLIGHT) from exc
    except gg.GitGateError as exc:
        raise Stop(f"agent tag gate failed (no paid call made): {exc}") from exc
    return pushed[0]


def records_by_key() -> dict[str, dict]:
    from benchmark.wp1b import main_runner as mr
    rows, _bad = mr.read_jsonl_tolerant(AGENT_DIR / mr.RECORDS_FILE)
    out: dict[str, dict] = {}
    for r in rows:
        require(str(r["work_key"]) not in out, f"duplicate Agent record {r['work_key']}")
        out[str(r["work_key"])] = r
    return out


def mirror_agent_items() -> int:
    """One small file per finished Agent item (controller progress + audit view)."""
    n = 0
    for k, r in records_by_key().items():
        t, rep = k.split("#")
        p = AGENT_ITEMS / f"{t}__{rep}.json"
        if not p.exists():
            write(p, self_hash({"work_key": k, "task_id": t, "replicate": rep,
                                "selected_paths": r["selected_paths"],
                                "prediction_empty": r["prediction_empty"],
                                "empty_reason": r["empty_reason"],
                                "infra_failure": r["infra_failure"],
                                "token_usage": r["token_usage"], "model_calls": r["model_calls"],
                                "artifact_sha256": ""}))
            n += 1
    return n


def translate_agent_exit(code: int, status: str) -> int:
    from benchmark.wp1b import main_runner as mr
    if code == mr.EXIT_OK:
        return 0
    if status == "OPERATOR_STOP":
        return EXIT_STOP
    if status == "MATERIALIZATION_HALT":
        return EXIT_PREFLIGHT
    return {mr.EXIT_BUDGET_ABORT: EXIT_BUDGET, mr.EXIT_CONFIG_ERROR: EXIT_PREFLIGHT,
            mr.EXIT_INFRA_HALT: EXIT_OUTAGE, mr.EXIT_INSTRUMENT_HALT: EXIT_INVARIANT,
            mr.EXIT_CRASH_HALT: EXIT_INVARIANT, mr.EXIT_LOCKED: EXIT_PREFLIGHT}.get(code,
                                                                                    EXIT_INVARIANT)


def agent(max_items: int, runner_factory: Callable[..., Any] | None = None) -> int:
    """Frozen protocol-v3 Agent localization (PAID). Thin wrapper over the WP-1b MainRunner,
    as scripts/wp2_dev_agent_scope_run.py: only the manifest, bundles and ceiling differ."""
    from benchmark.wp1b import main_runner as mr
    pre = agent_prefreeze_record()
    validate_auth()
    tag = agent_tag_gate() if runner_factory is None else "TEST"
    try:
        knobs = mr.verify_frozen_knobs(PROTOCOL_V3)
    except mr.KnobDriftError as exc:
        raise Stop(f"agent knob drift: {exc}") from exc
    items = [mr.WorkItem(key=i["key"], task_id=i["task_id"], replicate=i["replicate"], index=n)
             for n, i in enumerate(pre["items"])]
    extra: dict[str, Any] = {"knob_check.json": knobs}
    resume = (AGENT_DIR / mr.STATE_FILE).exists()
    if runner_factory is None:
        ok, prec = agent_pricing_preflight()
        prec["mode"] = "resume" if resume else "fresh"
        extra["pricing_preflight.json"] = prec
        if not ok and not resume:
            raise Stop("agent pricing metadata unreachable or drifted before a fresh paid run",
                       EXIT_PREFLIGHT)
    code_sha = {r: mr.file_sha256(PROJECT / r) for r in AGENT_CODE_FILES}
    code_sha["protocol_v3"] = str(knobs.get("protocol_sha256", ""))
    worst = {t: float(v["worst_case_usd"]) for t, v in pre["worst_case_per_task"].items()}
    config = mr.RunnerConfig(
        run_label="M15R_AGENT_SCOPE", kind="m15r_agent_scope", out_dir=AGENT_DIR,
        ceiling_usd=float(pre["agent_ceiling_usd"]), worst_case_usd=worst, items=items,
        manifest_sha256=pre["items_sha256"], code_sha256=code_sha, resume=resume,
        limit=max_items, stop_file=STOP_FLAG, extra_files=extra)
    runner = (runner_factory or _real_agent_runner)(config)
    outcome = runner.run()
    n = mirror_agent_items()
    print(f"M15R_AGENT {outcome.status}: {outcome.detail} | {outcome.completed}/{outcome.total} "
          f"| ledger ${outcome.ledger_usd:.6f} / ceiling ${pre['agent_ceiling_usd']:.2f} "
          f"| tag {tag} | mirrored {n}")
    return translate_agent_exit(outcome.exit_code, outcome.status)


def _real_agent_runner(config: Any) -> Any:  # pragma: no cover - paid path, never in tests
    from benchmark.llm.openrouter_backend import OpenRouterBackend
    from benchmark.strategies.iterative_agent import IterativeRepositoryAgentStrategy
    from benchmark.wp1b import label_guard as lg
    from benchmark.wp1b import main_runner as mr
    from benchmark.wp1b.resilient_backend import ResilientAccountingBackend, SpendLedger
    from scripts.saleor_portability_fix import materialize_production_parent
    lg._FORBIDDEN_PREFIXES = lg._FORBIDDEN_PREFIXES + AGENT_FORBIDDEN
    lg.install_label_access_guard(PROJECT)
    config.out_dir.mkdir(parents=True, exist_ok=True)
    ledger = SpendLedger.open(config.out_dir / mr.LEDGER_FILE)
    inner = OpenRouterBackend(model=mr.FROZEN_MODEL, provider=mr.FROZEN_PROVIDER,
                              api_key_env="OPENROUTER_API_KEY", timeout_seconds=120.0,
                              max_transient_retries=0)
    backend = ResilientAccountingBackend(inner, ledger=ledger, ceiling_usd=config.ceiling_usd)

    def _materialize(bundle: Any, workspace: Path) -> None:
        materialize_production_parent(SALEOR_CACHE, bundle.parent_commit, workspace,
                                      roots=("saleor",))

    def _load(task_id: str) -> Any:
        return mr.load_saleor_bundle(SALEOR_SCIENTIFIC, task_id)

    def _make(b: Any) -> Any:
        return IterativeRepositoryAgentStrategy(
            backend=b, agent_control_max_completion_tokens=mr.FROZEN_AGENT_CAP)
    return mr.MainRunner(config, backend=backend, load_bundle=_load, materialize=_materialize,
                         make_strategy=_make)


def agent_complete() -> int:
    if not AGENT_PRE.exists():
        return 1
    want = {i["key"] for i in load(AGENT_PRE)["items"]}
    got = set(records_by_key()) if AGENT_DIR.exists() else set()
    require(got <= want, f"unexpected Agent work keys {sorted(got - want)[:3]}")
    print(f"AGENT_{'COMPLETE' if got == want else 'INCOMPLETE'} {len(got)}/{len(want)}")
    return 0 if got == want else 1


def agent_usage() -> dict:
    """Tokens and model calls of the Agent localization runs (from the frozen records)."""
    recs = records_by_key() if AGENT_DIR.exists() else {}
    tok = [r.get("token_usage", {}) for r in recs.values()]
    return {"runs": len(recs), "model_calls": sum(int(r.get("model_calls", 0) or 0) for r in recs.values()),
            "prompt_tokens": sum(int(x.get("prompt_tokens", 0) or 0) for x in tok),
            "completion_tokens": sum(int(x.get("completion_tokens", 0) or 0) for x in tok),
            "empty_predictions": sum(bool(r.get("prediction_empty")) for r in recs.values())}


def agent_spend_usd() -> float:
    from benchmark.wp1b import main_runner as mr
    from benchmark.wp1b.resilient_backend import SpendLedger
    p = AGENT_DIR / mr.LEDGER_FILE
    return float(SpendLedger.open(p).total_usd) if p.exists() else 0.0


# ------------------------------------------------------------------ freeze (zero API)
def build_scopes(tasks: list[str], agent_raw: dict[tuple[str, str], list[str]]) -> dict:
    from benchmark.wp2.e2e.scopes import editable_filter, gold_raw_scope, rmcss_raw_scope
    out: dict[str, dict] = {}
    for t in tasks:
        raws = {"GOLD_HARD": gold_raw_scope(t), "RMCSS_HARD": rmcss_raw_scope(t)}
        for rep in REPS:
            raws[f"AGENT_HARD:{rep}"] = sorted(agent_raw[(t, rep)])
        out[t] = {k: editable_filter(t, v) for k, v in raws.items()}
    return out


def g0_prompt_meta(task_id: str, skey: str, scope: dict, sets_t: dict) -> dict:
    """Deterministic G0 prompt (no call): characters + evaluator-side leakage scan."""
    from benchmark.wp2.e2e.generate import _parent_texts
    from benchmark.wp2.e2e.task_inputs import load_task_input
    if not scope["editable"]:
        return {"no_scope": True, "prompt_chars": 0, "scope_chars": 0, "leakage_hits": 0}
    m = m14r()
    arm = skey_arm(skey)
    item = {"task_id": task_id, "arm": arm, "context": "C0", "replicate": "r1",
            "label": f"{arm}__C0__r1"}
    pt = _parent_texts(task_id, scope["editable"])
    msgs, psha = m.messages_for(item, load_task_input(task_id), scope["editable"], pt, scope)
    hits = m.leakage_scan(task_id, msgs[1]["content"], sets_t)
    require(not hits, f"LEAKAGE_BLOCK {task_id}/{skey}: {hits[:3]}")
    return {"no_scope": False, "prompt_sha256": psha,
            "prompt_chars": len(msgs[0]["content"]) + len(msgs[1]["content"]),
            "scope_chars": sum(len(pt.get(p, "")) for p in scope["editable"]), "leakage_hits": 0}


def gen_items(stage: str, tasks: list[str]) -> list[dict]:
    arms = ("GOLD_HARD",) if stage == "s2" else ("RMCSS_HARD", "AGENT_HARD")
    out = []
    for rep in REPS:
        for t in tasks:
            for arm in arms:
                out.append({"task_id": t, "arm": arm, "context": "C0", "replicate": rep,
                            "label": f"{arm}__C0__{rep}", "stage": stage,
                            "scope_key": f"AGENT_HARD:{rep}" if arm == "AGENT_HARD" else arm})
    return out


def build_freeze() -> dict:
    d = design()
    a = validate_auth()
    pre = agent_prefreeze_record()
    require(agent_complete() == 0, "Agent localization incomplete")
    tasks = members()
    recs = records_by_key()
    agent_raw = {(t, rep): list(recs[f"{t}#{rep}"]["selected_paths"]) for t in tasks for rep in REPS}
    scopes = build_scopes(tasks, agent_raw)
    for t in tasks:
        require(load(READY / t / "record.json")["positive"]["editable"]
                == scopes[t]["GOLD_HARD"]["editable"],
                f"GOLD scope differs from the readiness positive control {t}")
    write(SCOPES, {"artifact": "m15r_frozen_scopes", "tasks": scopes, "sha256": sha_obj(scopes)})
    sets = pilot_sets()
    meta = {t: {k: g0_prompt_meta(t, k, scopes[t][k], sets[t]) for k in scopes[t]} for t in tasks}
    write(PROMPT_META, {"artifact": "m15r_g0_prompt_meta", "tasks": meta, "sha256": sha_obj(meta)})
    for st in ("s2", "s3"):
        it = gen_items(st, tasks)
        write(PLANS[st], {"artifact": f"m15r_{st}_generation_plan", "items": it,
                          "sha256": sha_obj(it)})
    intents = {}
    for t in tasks:
        p = SALEOR_SCIENTIFIC / t / "public/intent.json"
        require(p.exists(), f"public intent missing {t}")
        intents[rel(p)] = norm_sha(p)
    from benchmark.wp1b import main_runner as mr
    arts = [DESIGN, GUARD, MEMBERSHIP, AUTH, AGENT_PRE, OOF_A, ROOT / "doctor/doctor_offline.json",
            ROOT / "doctor/doctor_paid.json", SCOPES, PROMPT_META, PLANS["s2"], PLANS["s3"],
            AGENT_DIR / mr.RECORDS_FILE]
    arts += [READY / t / n for t in population() for n in ("record.json", "negative_groups.json")]
    arts += [READY / t / "positive_groups.json" for t in tasks]
    return self_hash({
        "artifact": "m15r_freeze", "artifact_sha256": "", "design_artifact_sha256": DESIGN_SHA,
        "membership_artifact_sha256": load(MEMBERSHIP)["artifact_sha256"],
        "human_auth_artifact_sha256": a["artifact_sha256"],
        "agent_prefreeze_artifact_sha256": pre["artifact_sha256"],
        "max_total_spend_usd": float(a["max_total_spend_usd"]),
        "agent_spend_usd_frozen_list_price": round(agent_spend_usd(), 7),
        "model": MODEL, "provider": PROVIDER, "allow_fallbacks": False, "temperature": 0.0,
        "generator": "M14R run_base_episode, context C0 (G0), executed unchanged",
        "selectors_opws": list(SELECTORS), "frozen_scopes_sha256": sha_obj(scopes),
        "g0_prompt_meta_sha256": sha_obj(meta),
        "plan_sha256": {st: sha_obj(load(PLANS[st])["items"]) for st in ("s2", "s3")},
        "agent_empty": {f"{t}#{rep}": not scopes[t][f"AGENT_HARD:{rep}"]["editable"]
                        for t in tasks for rep in REPS},
        "artifact_hashes": {rel(p): norm_sha(p) for p in arts},
        "source_hashes": {r: norm_sha(PROJECT / r) for r in
                          d["pins"]["m14r_g0_source_norm_sha256"]} | {
            r: norm_sha(PROJECT / r) for r in KIT},
        "public_intent_hashes": intents})


def verify_freeze() -> list[str]:
    if not (FREEZE.exists() and SCOPES.exists() and PLANS["s2"].exists() and PLANS["s3"].exists()):
        return ["freeze artifacts missing"]
    fr = load(FREEZE)
    bad = [] if hash_ok(fr) else ["freeze self-hash"]
    for key in ("artifact_hashes", "source_hashes", "public_intent_hashes"):
        for r, h in fr.get(key, {}).items():
            p = PROJECT / r
            if not p.exists() or norm_sha(p) != h:
                bad.append(f"drift {r}")
    pins = design()["pins"]["m14r_g0_source_norm_sha256"]
    for r, h in pins.items():
        if fr["source_hashes"].get(r) != h:
            bad.append(f"M14R G0 source differs from the design pin {r}")
    if sha_obj(load(SCOPES)["tasks"]) != fr["frozen_scopes_sha256"] or any(
            sha_obj(load(PLANS[st])["items"]) != fr["plan_sha256"][st] for st in ("s2", "s3")):
        bad.append("plan/scope drift")
    return bad


def freeze() -> int:
    require(not (ROOT / "episodes").exists() and not OPWS_PLAN.exists(),
            "S1/S2 evidence exists; the freeze is never rebuilt")
    if FREEZE.exists():
        require(not verify_freeze(), "freeze exists and does not verify")
    else:
        write(FREEZE, build_freeze())
    bad = verify_freeze()
    require(not bad, f"freeze verify failed {bad[:5]}")
    fr = load(FREEZE)
    print("M15R_FREEZE_PASS " + json.dumps({"sha": fr["artifact_sha256"][:16],
                                            "agent_empty": sum(fr["agent_empty"].values())}))
    return 0


def freeze_verify() -> int:
    bad = verify_freeze()
    print("M15R_FREEZE_VERIFY_PASS" if not bad else "M15R_FREEZE_VERIFY_FAIL " + str(bad[:5]))
    return 0 if not bad else 1


# ------------------------------------------------------------------ shared evaluation (zero API)
def core_diff_sha(diff: str) -> str:
    """Frozen v21 identity: sha256(json.dumps([diff]))."""
    return hashlib.sha256(json.dumps([diff], sort_keys=True, ensure_ascii=False)
                          .encode("utf-8")).hexdigest()


def unique_path(task_id: str, identity: str) -> Path:
    require(len(identity) == 64, f"full identity sha required: {identity!r}")
    return ROOT / "evaluations/unique" / task_id / identity / "evaluation.json"


def evaluation_record(task_id: str, identity: str, groups: dict, t: dict, tree: str,
                      e1_decision: str, source: str, labels: list[str],
                      sources: list[str]) -> dict:
    st, rb = core.score_strict(t, groups), core.score_robust(t, groups)
    return self_hash({"task_id": task_id, "diff_sha256": identity,
                      "eval_identity": f"{task_id}/{identity}", "label": "u_" + identity[:12],
                      "tree_sha": tree, "status": "DONE", "groups": groups, "strict": st,
                      "robust": rb, "nodes": core.node_report(t, groups),
                      "e1_decision": e1_decision, "evaluation_source": source, "labels": labels,
                      "sources": sources, "evaluation_sha256": ""}, "evaluation_sha256")


class EvalFns:
    """Frozen evaluator access (materialize + E1 evaluation); injectable for tests."""

    def __init__(self, evaluate_fn: Callable[..., dict] | None = None,
                 materialize_fn: Callable[..., tuple[str, str]] | None = None) -> None:
        self.evaluate_fn, self.materialize_fn, self.ev = evaluate_fn, materialize_fn, None

    def run(self, task_id: str, identity: str, diff: str) -> tuple[dict, str, str]:
        from scripts.wp2_m14a_evalcore import EvalInfraError
        from scripts.wp2_m14a_evalcore_e1 import evaluate_state_e1
        if self.ev is None and (self.evaluate_fn is None or self.materialize_fn is None):
            self.ev = _ev()
        lab = "u_" + identity[:12]
        mat = self.materialize_fn or self.ev.materialize
        efn = self.evaluate_fn or (lambda tk, lb, wt, d, _ev=self.ev: evaluate_state_e1(
            _ev, tk, lb, wt, diff_text=d,
            diag_path=ROOT / "evaluations/diagnostics" / tk / lb / "e1_diagnostics.json",
            parent_starts_ok=readiness_ok(tk)))
        try:
            wt, tree = mat(task_id, lab, diff)
        except ValueError as exc:
            raise Stop(f"frozen diff does not apply at evaluation: {exc}") from exc
        except (RuntimeError, OSError, subprocess.SubprocessError) as exc:
            raise Stop(f"evaluation infrastructure error: {exc}", EXIT_EVAL_INFRA) from exc
        try:
            er = efn(task_id, lab, wt, diff)
        except (EvalInfraError, RuntimeError, OSError, subprocess.SubprocessError) as exc:
            raise Stop(f"evaluation infrastructure error: {exc}", EXIT_EVAL_INFRA) from exc
        return er["groups"], tree, er.get("e1_decision", "")


def negative_record(task_id: str, identity: str, t: dict, labels: list[str],
                    sources: list[str]) -> dict:
    ng = load(READY / task_id / "negative_groups.json")
    require(hash_ok(ng), "negative control record hash")
    return evaluation_record(task_id, identity, ng["groups"], t, ng["tree_sha"],
                             "ALL_JUNIT_PRESENT", "READINESS_NEGATIVE_CONTROL", labels, sources)


def positive_record(task_id: str, identity: str, t: dict, labels: list[str],
                    sources: list[str]) -> dict:
    pg = load(READY / task_id / "positive_groups.json")
    require(hash_ok(pg), "positive control record hash")
    return evaluation_record(task_id, identity, pg["groups"], t, pg["tree_sha"],
                             pg["e1_decision"], "READINESS_POSITIVE_CONTROL", labels, sources)


# ------------------------------------------------------------------ S1 OPWS (zero API)
def opws_paths(scopes_t: dict, skey: str) -> list[str]:
    """P_S files = selector editable set INTERSECT gold-changed non-test files."""
    return sorted(set(scopes_t[skey]["editable"]) & set(scopes_t["GOLD_HARD"]["raw"]))


def prf(editable: list[str], gold: list[str]) -> dict:
    e, g = set(editable), set(gold)
    tp = len(e & g)
    p = tp / len(e) if e else 0.0
    r = tp / len(g) if g else 0.0
    return {"precision": round(p, 6), "recall": round(r, 6),
            "f1": round(2 * p * r / (p + r), 6) if p + r else 0.0, "tp": tp,
            "n_editable": len(e), "n_gold": len(g)}


def opws_record_path(task_id: str, skey: str) -> Path:
    return OPWS_DIR / task_id / safe(skey) / "opws.json"


def freeze_pushed() -> str:
    """S1 may start only after the scope freeze is committed, tagged and on origin."""
    from benchmark.wp1b import git_gate as gg
    tags = sorted(x for x in git("tag", "--list", "wp2-m15r-v1-freeze-*").stdout.split() if x)
    try:
        for tag in tags:
            if gg.remote_tag_objects(PROJECT, tag)["object"]:
                gg.verify_tag_on_origin(PROJECT, tag)
                for p in (FREEZE, SCOPES, PLANS["s2"], PLANS["s3"]):
                    gg.verify_file_in_tag(PROJECT, tag, p)
                return tag
    except gg.GitRemoteUnavailableError as exc:
        raise Stop(f"origin unreachable: {exc}", EXIT_EVAL_INFRA) from exc
    except gg.GitGateError as exc:
        raise Stop(f"scope freeze not pushed as tagged: {exc}") from exc
    raise Stop("no pushed wp2-m15r-v1-freeze-* tag holds the scope freeze")


def opws_plan(diff_fn: Callable[[str, list[str]], str] | None = None,
              pushed_fn: Callable[[], str] | None = None) -> int:
    bad = verify_freeze()
    require(not bad, f"freeze drift {bad[:3]}")
    (pushed_fn or freeze_pushed)()
    diff_fn = diff_fn or (lambda t, ps: m14r().scoped_gold_diff(t, ps))
    scopes = load(SCOPES)["tasks"]
    items = []
    for t in members():
        pos = load(READY / t / "record.json")["positive"]
        for skey in ("GOLD_HARD",) + SELECTORS:
            ps = opws_paths(scopes[t], skey)
            it = {"task_id": t, "selector": skey, "opws_files": ps,
                  "file_prf": prf(scopes[t][skey]["editable"], scopes[t]["GOLD_HARD"]["raw"])}
            if not ps:
                it.update({"kind": "EMPTY_BY_CONSTRUCTION", "diff_sha256_raw": "", "identity": ""})
            else:
                try:
                    diff = diff_fn(t, ps)
                except Exception as exc:
                    if type(exc).__name__ in INFRA_EXC or isinstance(exc, OSError):
                        raise Stop(f"OPWS diff infrastructure error {t}: {exc}",
                                   EXIT_EVAL_INFRA) from exc
                    raise
                require(bool(diff.strip()), f"restricted gold diff empty for non-empty P_S {t}/{skey}")
                p = OPWS_DIR / t / safe(skey) / "opws_diff.patch"
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(diff, encoding="utf-8", newline="")
                raw = text_sha(diff)
                it.update({"kind": "REUSE_SCOPED_GOLD" if raw == pos["scoped_diff_sha256"]
                           else "EVALUATE", "diff_sha256_raw": raw, "identity": core_diff_sha(diff),
                           "diff_path": rel(p)})
            items.append(it)
    gold_ok = all(i["kind"] == "REUSE_SCOPED_GOLD" for i in items if i["selector"] == "GOLD_HARD")
    require(gold_ok, "GOLD OPWS diff differs from the readiness scoped-gold diff")
    plan = {"artifact": "m15r_opws_plan", "items": items, "sha256": sha_obj(items),
            "rule": "P_S = gold non-test diff restricted to (selector editable INTERSECT "
                    "gold-changed files); empty P_S = FAIL by construction; P_S identical to the "
                    "scoped gold = S0 positive evaluation reused; otherwise frozen evaluator + E1"}
    if OPWS_PLAN.exists():
        require(load(OPWS_PLAN)["items"] == items, "existing OPWS plan differs")
    else:
        write(OPWS_PLAN, plan)
    print("M15R_OPWS_PLAN " + json.dumps(dict(Counter(i["kind"] for i in items))))
    return 0


def opws_evaluate(max_evals: int, fns: EvalFns | None = None) -> int:
    bad = verify_freeze()
    require(not bad, f"freeze drift {bad[:3]}")
    require(OPWS_PLAN.exists(), "OPWS plan missing")
    fns = fns or EvalFns()
    sets = pilot_sets()
    done = written = 0
    for i in load(OPWS_PLAN)["items"]:
        p = opws_record_path(i["task_id"], i["selector"])
        st = record_state(p)
        require(st != "CORRUPT", f"corrupt OPWS record {p}")
        if st == "VALID":
            continue
        t = sets[i["task_id"]]
        require(readiness_ok(i["task_id"]), f"task not ready {i['task_id']}")
        lab = f"OPWS:{i['selector']}"
        if i["kind"] == "EMPTY_BY_CONSTRUCTION":
            ev = None
            strict = {"f2p_task": "FAIL", "p2p_s_task": "PASS_BY_CONSTRUCTION",
                      "p2p_u200_task": "PASS_BY_CONSTRUCTION", "resolved": False}
            robust, source = dict(strict), "EMPTY_BY_CONSTRUCTION"
        else:
            up = unique_path(i["task_id"], i["identity"])
            ust = record_state(up, "evaluation_sha256")
            require(ust != "CORRUPT", f"corrupt evaluation record {up}")
            if ust == "ABSENT":
                if i["kind"] == "REUSE_SCOPED_GOLD":
                    ev = positive_record(i["task_id"], i["identity"], t, [lab], [i["diff_path"]])
                else:
                    if done >= max_evals:
                        break
                    diff = (PROJECT / i["diff_path"]).read_text(encoding="utf-8")
                    require(text_sha(diff) == i["diff_sha256_raw"], f"OPWS diff drift {p}")
                    groups, tree, e1 = fns.run(i["task_id"], i["identity"], diff)
                    ev = evaluation_record(i["task_id"], i["identity"], groups, t, tree, e1,
                                           "OPWS_EVALUATED", [lab], [i["diff_path"]])
                    done += 1
                write(up, ev)
            ev = load(up)
            strict, robust, source = ev["strict"], ev["robust"], ev["evaluation_source"]
        rec = self_hash({"artifact": "m15r_opws_result", "task_id": i["task_id"],
                         "selector": i["selector"], "kind": i["kind"], "identity": i["identity"],
                         "opws_files": i["opws_files"], "file_prf": i["file_prf"],
                         "strict": strict, "robust": robust,
                         "opws_strict": bool(strict["resolved"]),
                         "opws_robust": bool(robust["resolved"]),
                         "nodes": (ev or {}).get("nodes"), "evaluation_source": source,
                         "artifact_sha256": ""})
        write(p, rec)
        written += 1
        print(f"[m15r-opws] {i['task_id']} {i['selector']} -> robust={rec['opws_robust']} "
              f"strict={rec['opws_strict']} ({source})", flush=True)
    print(f"OPWS_CHUNK evaluated={done} written={written}")
    return 0


def opws_complete() -> int:
    if not OPWS_PLAN.exists():
        return 1
    items = load(OPWS_PLAN)["items"]
    st = [record_state(opws_record_path(i["task_id"], i["selector"])) for i in items]
    if "CORRUPT" in st:
        print("OPWS_CORRUPT")
        return 1
    n = st.count("VALID")
    print(f"OPWS_{'COMPLETE' if n == len(items) else 'INCOMPLETE'} {n}/{len(items)}")
    return 0 if n == len(items) else 1


def _jaccard(a: list[str], b: list[str]) -> float:
    sa, sb = set(a), set(b)
    return 1.0 if not sa and not sb else len(sa & sb) / len(sa | sb)


def compute_opws_summary() -> dict:
    tasks = members()
    scopes = load(SCOPES)["tasks"]
    meta = load(PROMPT_META)["tasks"]
    res = {(i["task_id"], i["selector"]): load(opws_record_path(i["task_id"], i["selector"]))
           for i in load(OPWS_PLAN)["items"]}
    per_sel: dict[str, dict] = {}
    for skey in ("GOLD_HARD",) + SELECTORS:
        rows = [res[(t, skey)] for t in tasks]
        mm = [meta[t][skey] for t in tasks]
        per_sel[skey] = {
            "n_tasks": len(tasks), "opws_robust": sum(r["opws_robust"] for r in rows),
            "opws_strict": sum(r["opws_strict"] for r in rows),
            "empty_by_construction": sum(r["kind"] == "EMPTY_BY_CONSTRUCTION" for r in rows),
            "no_scope": sum(not scopes[t][skey]["editable"] for t in tasks),
            "mean_precision": round(sum(r["file_prf"]["precision"] for r in rows) / len(rows), 6),
            "mean_recall": round(sum(r["file_prf"]["recall"] for r in rows) / len(rows), 6),
            "mean_f1": round(sum(r["file_prf"]["f1"] for r in rows) / len(rows), 6),
            "mean_editable_files": round(sum(len(scopes[t][skey]["editable"]) for t in tasks)
                                         / len(tasks), 3),
            "mean_scope_chars": round(sum(x["scope_chars"] for x in mm) / len(mm), 1),
            "mean_g0_prompt_chars": round(sum(x["prompt_chars"] for x in mm) / len(mm), 1)}
    per_task = {t: {skey: {"opws_robust": res[(t, skey)]["opws_robust"],
                           "opws_strict": res[(t, skey)]["opws_strict"],
                           "kind": res[(t, skey)]["kind"], "f1": res[(t, skey)]["file_prf"]["f1"]}
                    for skey in ("GOLD_HARD",) + SELECTORS} for t in tasks}
    agents = [s for s in SELECTORS if s.startswith("AGENT")]
    agree = sum(len({res[(t, s)]["opws_robust"] for s in agents}) == 1 for t in tasks)
    jac = [sum(_jaccard(scopes[t][a]["editable"], scopes[t][b]["editable"])
               for a, b in (("AGENT_HARD:r1", "AGENT_HARD:r2"), ("AGENT_HARD:r1", "AGENT_HARD:r3"),
                            ("AGENT_HARD:r2", "AGENT_HARD:r3"))) / 3 for t in tasks]
    paired = {}
    for a in agents + ["AGENT_MAJORITY"]:
        w = lo = ti = 0
        for t in tasks:
            rv = res[(t, "RMCSS_HARD")]["opws_robust"]
            av = (sum(res[(t, s)]["opws_robust"] for s in agents) >= 2 if a == "AGENT_MAJORITY"
                  else res[(t, a)]["opws_robust"])
            w += rv and not av
            lo += av and not rv
            ti += rv == av
        paired[f"RMCSS_vs_{a}"] = {"rmcss_only": w, "agent_only": lo, "ties": ti}
    evaluated = [r for r in res.values() if r["kind"] != "EMPTY_BY_CONSTRUCTION"]
    discord = sum(r["opws_strict"] != r["opws_robust"] for r in evaluated)
    instrument_ok = (opws_complete() == 0 and not verify_freeze()
                     and all(res[(t, "GOLD_HARD")]["opws_robust"] for t in tasks))
    return {"artifact": "m15r_opws_summary", "design_artifact_sha256": DESIGN_SHA,
            "token": "M15R_OPWS_COMPLETE" if instrument_ok else "M15R_INSTRUMENT_REVIEW",
            "primary_endpoint": "OPWS_ROBUST", "n_tasks": len(tasks), "members": tasks,
            "per_selector": per_sel, "per_task": per_task,
            "agent_replicate_agreement_tasks": agree,
            "agent_mean_pairwise_jaccard": round(sum(jac) / len(jac), 6),
            "paired_rmcss_vs_agent": paired, "strict_robust_discordance": discord,
            "n_evaluated_or_reused": len(evaluated), "instrument_valid": instrument_ok,
            "descriptive_only": True,
            "mandatory_wording": ("OPWS asks whether the developer's own patch, restricted to the "
                                  "files a selector allowed, still passes the hidden tests. It is "
                                  "independent of any generator, does not penalise over-selection "
                                  "(cost is reported separately), and credits no alternative fix. "
                                  "Gold-changed files follow the frozen GOLD_HARD definition "
                                  "(modified/deleted non-test files; added and renamed files are "
                                  "excluded, as in Smoke, Pilot-A and M14R). "
                                  "n <= 10 Pilot-B tasks: descriptive only, no superiority claim.")}


def opws_summary() -> int:
    require(opws_complete() == 0, "OPWS incomplete")
    s = self_hash(dict(compute_opws_summary(), artifact_sha256=""))
    require(s["instrument_valid"], "OPWS instrument invalid (GOLD reference or completeness)")
    write(OPWS_SUMMARY, s)
    lines = ["# WP2 M15-R V1 - S1 OPWS result (Pilot-B, descriptive)", "",
             f"Token: **{s['token']}**. Members: {s['n_tasks']}. Primary endpoint: OPWS_ROBUST "
             "(strict co-reported).", "",
             "| Selector | OPWS robust | OPWS strict | empty P_S | NO_SCOPE | mean P | mean R | "
             "mean F1 | mean files | mean scope chars | mean G0 prompt chars |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for k, v in s["per_selector"].items():
        lines.append(f"| {k} | {v['opws_robust']}/{v['n_tasks']} | {v['opws_strict']}/{v['n_tasks']}"
                     f" | {v['empty_by_construction']} | {v['no_scope']} | {v['mean_precision']} | "
                     f"{v['mean_recall']} | {v['mean_f1']} | {v['mean_editable_files']} | "
                     f"{v['mean_scope_chars']} | {v['mean_g0_prompt_chars']} |")
    lines += ["", f"Agent replicate agreement on OPWS_ROBUST: {s['agent_replicate_agreement_tasks']}"
              f"/{s['n_tasks']} tasks; mean pairwise Jaccard of Agent editable sets: "
              f"{s['agent_mean_pairwise_jaccard']}.",
              f"Paired RM-CSS vs Agent (per task): {json.dumps(s['paired_rmcss_vs_agent'])}.",
              f"Strict/robust discordance among evaluated OPWS states: "
              f"{s['strict_robust_discordance']}/{s['n_evaluated_or_reused']}.", "",
              s["mandatory_wording"], ""]
    OPWS_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OPWS_REPORT.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print("M15R_OPWS_COMPLETE " + json.dumps({k: v["opws_robust"]
                                              for k, v in s["per_selector"].items()}))
    return 0


# ------------------------------------------------------------------ S2 / S3 G0 generation (paid)
class Ledger:
    """Durable generation spend ledger (fsync per record). The offset is the Agent
    localization spend, so the human cap binds Agent + S2 + S3 together."""

    def __init__(self, path: Path, ceiling: float, offset: float = 0.0) -> None:
        self.path, self.ceiling, self.offset, self.t, self.context = path, ceiling, offset, 0.0, {}
        if path.exists():
            for x in path.read_text(encoding="utf-8").splitlines():
                if x.strip():
                    self.t += float(json.loads(x).get("cost_usd", 0) or 0)

    def total(self) -> float:
        return self.offset + self.t

    def generation_total(self) -> float:
        return self.t

    def can_spend(self, worst: float) -> bool:
        return self.total() + worst <= self.ceiling + 1e-12

    def record(self, r: dict) -> None:
        r = dict(r, stage="M15R", **self.context)
        self.t += float(r.get("cost_usd", 0) or 0)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(r, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())


def ep_dir(item: dict) -> Path:
    return ROOT / "episodes" / item["task_id"] / item["label"]


def ep_status(item: dict) -> str | None:
    p = ep_dir(item) / "episode.json"
    if not p.exists():
        return None
    try:
        return load(p).get("status")
    except (ValueError, OSError):
        return "UNREADABLE"


def cache_for(item: dict):
    from benchmark.wp2.e2e.response_cache import ResponseCache
    return ResponseCache(ROOT / "cache_namespaces" / item["task_id"] / item["label"])


@contextlib.contextmanager
def g0_redirect(scopes: dict) -> Iterator[dict]:
    """Run the frozen M14R G0 code with the M15-R evidence root and the frozen raw scope of
    the current item. Nothing in the M14R modules is edited; both attributes are restored."""
    import benchmark.wp2.e2e.generate as gen
    m = m14r()
    state: dict[str, Any] = {"item": None}

    def raw_scope(task_id: str, arm: str) -> list[str]:
        it = state["item"]
        require(it is not None and it["task_id"] == task_id and it["arm"] == arm,
                f"raw-scope resolver called outside its item {task_id}/{arm}")
        return list(scopes[task_id][it["scope_key"]]["raw"])
    saved = (m.ROOT, gen._raw_scope)
    m.ROOT, gen._raw_scope = ROOT, raw_scope
    try:
        yield state
    finally:
        m.ROOT, gen._raw_scope = saved


def g0_episode(item: dict, client: Any, ledger: Any, cache: Any, state: dict) -> dict:
    state["item"] = item
    try:
        return m14r().run_base_episode(
            {k: item[k] for k in ("task_id", "arm", "context", "replicate", "label")},
            client, ledger, cache)
    finally:
        state["item"] = None


def gate_record() -> dict:
    require(S2_GATE.exists() and hash_ok(load(S2_GATE)), "S2 gate record missing")
    return load(S2_GATE)


def s3_skipped() -> bool:
    return S2_GATE.exists() and gate_record()["verdict"] != "PASS"


def _paid_setup():
    from benchmark.wp2.e2e_v22.circuit import CircuitBreaker
    from benchmark.wp2.e2e_v22.transport import AttemptLog, V22HttpClient
    a = validate_auth()
    ledger = Ledger(LEDGER, min(float(a["max_total_spend_usd"]), MAX_USD), agent_spend_usd())
    client = V22HttpClient([ROOT / "HOLD"], AttemptLog(ROOT / "transport/attempts.jsonl"))
    breaker = CircuitBreaker(ROOT / "transport/circuit.json")
    return ledger, client, breaker


def generate(stage: str, max_new: int, max_seconds: float, setup: Callable[[], tuple] | None = None,
             cache_fn: Callable[[dict], Any] | None = None) -> int:
    bad = verify_freeze()
    require(not bad, f"freeze drift before generation {bad[:3]}")
    require(OPWS_SUMMARY.exists() and hash_ok(load(OPWS_SUMMARY)), "S1 OPWS must close before S2")
    if stage == "s3":
        g = gate_record()
        if g["verdict"] != "PASS":
            print(f"S3_SKIPPED {g['token']}")
            return 0
        bad = verify_generation_freeze("s2")
        require(not bad, f"S2 generation freeze drift {bad[:3]}")
    if setup is None:
        from scripts.wp2_e2e_v22_doctor import live_pricing
        pr = live_pricing()
        require(bool(pr.get("ok")), f"generation pricing preflight failed: {str(pr)[:300]}",
                EXIT_PREFLIGHT)
    ledger, client, breaker = (setup or _paid_setup)()
    scopes = load(SCOPES)["tasks"]
    m = m14r()
    cache_fn = cache_fn or cache_for
    with g0_redirect(scopes) as state:
        code, info = m.drive(load(PLANS[stage])["items"],
                             lambda i: g0_episode(i, client, ledger, cache_fn(i), state),
                             client, ledger, breaker,
                             lambda i: scopes[i["task_id"]][i["scope_key"]]["editable"],
                             max_new, max_seconds, stop_flag=STOP_FLAG)
    info.update({"exit": code, "stage": stage, "spend_total_usd": round(ledger.total(), 7),
                 "generation_spend_usd": round(ledger.generation_total(), 7),
                 "network_attempts": getattr(client, "network_attempts", None)})
    print("M15R_DRIVER_RESULT " + json.dumps(info, sort_keys=True, default=str))
    return code


def generation_complete(stage: str) -> int:
    if stage == "s3" and s3_skipped():
        print("GENERATION_S3_SKIPPED")
        return 0
    if not PLANS[stage].exists():
        return 1
    items = load(PLANS[stage])["items"]
    n = sum(ep_status(i) in TERMINAL for i in items)
    print(f"GENERATION_{stage.upper()}_{'COMPLETE' if n == len(items) else 'INCOMPLETE'} "
          f"{n}/{len(items)}")
    return 0 if n == len(items) else 1


def _prefix_record(p: Path) -> dict:
    lines = p.read_text(encoding="utf-8").replace("\r\n", "\n").splitlines(keepends=True)
    return {"lines": len(lines), "prefix_sha256": text_sha("".join(lines))}


def _prefix_ok(p: Path, rec: dict) -> bool:
    if not p.exists():
        return rec["lines"] == 0
    lines = p.read_text(encoding="utf-8").replace("\r\n", "\n").splitlines(keepends=True)
    return len(lines) >= rec["lines"] and text_sha("".join(lines[:rec["lines"]])) == \
        rec["prefix_sha256"]


def generation_freeze(stage: str) -> int:
    require(generation_complete(stage) == 0, f"{stage} generation incomplete")
    require(not verify_freeze(), "freeze drift")
    if stage == "s3" and s3_skipped():
        gf = self_hash({"artifact": "m15r_generation_freeze_s3", "artifact_sha256": "",
                        "skipped": True, "reason": gate_record()["token"], "files": {},
                        "append_only": {}, "n_episodes": 0})
    else:
        items = load(PLANS[stage])["items"]
        files = {}
        for i in items:
            e = load(ep_dir(i) / "episode.json")
            require(e.get("status") in TERMINAL, "non-terminal episode")
            require(e["episode_sha256"] == sha_obj(dict(e, episode_sha256="")), f"episode hash {i}")
            for c in e.get("calls", []):
                require(c.get("route") != "replay", "replay route in paid evidence")
            for p in sorted(ep_dir(i).rglob("*")):
                if p.is_file():
                    files[p.relative_to(ROOT).as_posix()] = norm_sha(p)
        app = {r: _prefix_record(ROOT / r) for r in ("ledger/m15r_generation_spend.jsonl",
                                                      "transport/attempts.jsonl")
               if (ROOT / r).exists()}
        gf = self_hash({"artifact": f"m15r_generation_freeze_{stage}", "artifact_sha256": "",
                        "skipped": False, "m15r_freeze_sha256": load(FREEZE)["artifact_sha256"],
                        "n_episodes": len(items), "files": files, "append_only": app,
                        "generation_spend_usd": round(Ledger(LEDGER, MAX_USD).generation_total(), 7)})
    if GEN_FREEZE[stage].exists():
        require(load(GEN_FREEZE[stage])["artifact_sha256"] == gf["artifact_sha256"],
                "generation freeze exists and differs")
    write(GEN_FREEZE[stage], gf)
    print(f"M15R_GENERATION_FROZEN_{stage.upper()} " + json.dumps({"n": gf["n_episodes"]}))
    return 0


def verify_generation_freeze(stage: str) -> list[str]:
    if not GEN_FREEZE[stage].exists():
        return [f"generation freeze {stage} missing"]
    bad = verify_freeze()
    gf = load(GEN_FREEZE[stage])
    if not hash_ok(gf):
        bad.append("generation freeze self-hash")
    for r, h in gf.get("files", {}).items():
        p = ROOT / r
        if not p.exists() or norm_sha(p) != h:
            bad.append(f"generation evidence drift {r}")
    for r, rec in gf.get("append_only", {}).items():
        if not _prefix_ok(ROOT / r, rec):
            bad.append(f"append-only file rewritten {r}")
    return bad


def generation_freeze_verify(stage: str) -> int:
    bad = verify_generation_freeze(stage)
    print(f"M15R_GENERATION_FREEZE_{stage.upper()}_VERIFY_" + ("PASS" if not bad else
                                                              "FAIL " + str(bad[:5])))
    return 0 if not bad else 1


def build_eval_plan(stage: str) -> list[dict]:
    if stage == "s3" and s3_skipped():
        return []
    uniq: dict[tuple[str, str], dict] = {}
    for i in load(PLANS[stage])["items"]:
        e = load(ep_dir(i) / "episode.json")
        if e.get("status") != "APPLIED" or not e.get("diff_sha256"):
            continue
        k = (i["task_id"], e["diff_sha256"])
        src = (ep_dir(i) / "episode.json").relative_to(ROOT).as_posix()
        if k not in uniq:
            uniq[k] = {"task_id": i["task_id"], "diff_sha256": e["diff_sha256"], "source": src,
                       "labels": [i["label"]], "sources": [src]}
        else:
            uniq[k]["labels"].append(i["label"])
            uniq[k]["sources"].append(src)
    return sorted(uniq.values(), key=lambda x: (x["task_id"], x["diff_sha256"]))


def eval_plan(stage: str) -> int:
    bad = verify_generation_freeze(stage)
    require(not bad, f"generation freeze drift {bad[:3]}")
    items = build_eval_plan(stage)
    p = {"artifact": f"m15r_evaluation_plan_{stage}", "items": items,
         "n_unique_identities": len(items), "sha256": sha_obj(items)}
    if EVAL_PLAN[stage].exists():
        require(load(EVAL_PLAN[stage])["items"] == items, "existing evaluation plan differs")
    else:
        write(EVAL_PLAN[stage], p)
    print(f"M15R_EVAL_PLAN_{stage.upper()} " + json.dumps({"n_unique_identities": len(items)}))
    return 0


def evaluate(stage: str, max_evals: int, fns: EvalFns | None = None) -> int:
    bad = verify_generation_freeze(stage)
    require(not bad, f"generation freeze drift {bad[:3]}")
    require(EVAL_PLAN[stage].exists(), "evaluation plan missing")
    fns = fns or EvalFns()
    sets = pilot_sets()
    done = 0
    for i in load(EVAL_PLAN[stage])["items"]:
        p = unique_path(i["task_id"], i["diff_sha256"])
        stt = record_state(p, "evaluation_sha256")
        require(stt != "CORRUPT", f"corrupt evaluation record {p}")
        if stt == "VALID":
            continue
        if done >= max_evals:
            break
        t = sets[i["task_id"]]
        require(readiness_ok(i["task_id"]), f"task not ready {i['task_id']}")
        if i["diff_sha256"] == EMPTY_DIFF_SHA:
            rec = negative_record(i["task_id"], i["diff_sha256"], t, i["labels"], i["sources"])
        else:
            txt = (ROOT / i["source"]).parent.joinpath("final_diff.patch").read_text(
                encoding="utf-8")
            require(core_diff_sha(txt) == i["diff_sha256"], f"frozen diff drift {i['source']}")
            groups, tree, e1 = fns.run(i["task_id"], i["diff_sha256"], txt)
            rec = evaluation_record(i["task_id"], i["diff_sha256"], groups, t, tree, e1,
                                    "EVALUATED", i["labels"], i["sources"])
        write(p, rec)
        done += 1
        print(f"[m15r-eval-{stage}] {i['task_id']} {i['diff_sha256'][:12]} -> strict="
              f"{rec['strict']['resolved']} robust={rec['robust']['resolved']} "
              f"f2p={rec['strict']['f2p_task']}", flush=True)
    print(f"EVAL_CHUNK stage={stage} evaluated={done}")
    return 0


def eval_complete(stage: str) -> int:
    if not EVAL_PLAN[stage].exists():
        return 1
    miss, corrupt = [], []
    for i in load(EVAL_PLAN[stage])["items"]:
        s = record_state(unique_path(i["task_id"], i["diff_sha256"]), "evaluation_sha256")
        (corrupt if s == "CORRUPT" else miss if s == "ABSENT" else []).append(
            f"{i['task_id']}/{i['diff_sha256'][:12]}")
    if corrupt or miss:
        print(("EVAL_CORRUPT " if corrupt else "EVAL_INCOMPLETE ") + json.dumps((corrupt or miss)[:20]))
        return 1
    print(f"EVAL_COMPLETE stage={stage} n_unique={load(EVAL_PLAN[stage])['n_unique_identities']}")
    return 0


def episode_rows(stage: str) -> list[dict]:
    sets = pilot_sets()
    rows = []
    for i in load(PLANS[stage])["items"]:
        e = load(ep_dir(i) / "episode.json")
        t = sets[i["task_id"]]
        v = None
        if e["status"] == "APPLIED":
            p = unique_path(i["task_id"], e["diff_sha256"])
            v = load(p) if record_state(p, "evaluation_sha256") == "VALID" else None
        if e["status"] == "APPLIED" and v is None:
            lab = {"label": "UNEVALUATED", "detail": ""}
        else:
            lab = core.classify_episode(e["status"], e.get("diff_sha256") == EMPTY_DIFF_SHA,
                                        (v or {}).get("e1_decision"), t,
                                        (v or {}).get("groups"), (v or {}).get("strict"))
        rows.append({"task_id": i["task_id"], "arm": i["arm"], "replicate": i["replicate"],
                     "label": i["label"], "stage": stage, "status": e["status"],
                     "taxonomy": lab, "strict_resolved": bool(v and v["strict"]["resolved"]),
                     "robust_resolved": bool(v and v["robust"]["resolved"]),
                     "f2p_pass": bool(v and v["strict"]["f2p_task"] == "PASS"),
                     "scope_violation": e["status"] == "APPLIED" and not set(
                         e.get("edited_files", [])) <= set(e.get("editable_set", [])),
                     "unevaluated": e["status"] == "APPLIED" and v is None,
                     "tokens": m14r().episode_tokens(e),
                     "calls": len(e.get("calls", [])), "repair_used": bool(e.get("repair_used")),
                     "f2p_nodes_pass3": (v or {}).get("nodes", {}).get("f2p_pass3", 0) if v else 0,
                     "f2p_nodes_total": len(t["behavioral_f2p_node_ids"]),
                     "cost_usd": round(sum(float(c.get("cost_usd_actual", 0) or 0)
                                           for c in e.get("calls", [])), 7)})
    return rows


def gate_thresholds(n: int) -> dict:
    """ceil(0.4 n) and ceil(0.2 * 3n) in exact integer arithmetic (no float rounding)."""
    return {"min_solvable_tasks": -(-4 * n // 10), "min_robust_episodes": -(-6 * n // 10),
            "n_tasks": n, "n_episodes": 3 * n}


def s2_gate() -> int:
    require(eval_complete("s2") == 0, "S2 evaluation incomplete")
    require(not verify_generation_freeze("s2"), "S2 generation freeze drift")
    rows = episode_rows("s2")
    require(not any(r["unevaluated"] or r["scope_violation"] for r in rows),
            "S2 instrument invariant (unevaluated APPLIED or scope violation)")
    tasks = members()
    per_task = {t: sum(r["robust_resolved"] for r in rows if r["task_id"] == t) for t in tasks}
    per_task_strict = {t: sum(r["strict_resolved"] for r in rows if r["task_id"] == t)
                       for t in tasks}
    th = gate_thresholds(len(tasks))
    solvable = sorted(t for t in tasks if per_task[t] > 0)
    eps = sum(per_task.values())
    ok = len(solvable) >= th["min_solvable_tasks"] and eps >= th["min_robust_episodes"]
    rec = self_hash({"artifact": "m15r_s2_gate", "artifact_sha256": "",
                     "verdict": "PASS" if ok else "FAIL",
                     "token": "M15R_S2_GATE_PASS" if ok else
                     "M15R_GOLD_FLOOR_FAIL_NO_GENERATION_CLAIM",
                     "thresholds": th, "gold_solvable_tasks": solvable,
                     "gold_robust_episodes": eps, "per_task_robust": per_task,
                     "per_task_strict": per_task_strict,
                     "strict_view": {"solvable": sum(v > 0 for v in per_task_strict.values()),
                                     "episodes": sum(per_task_strict.values())},
                     "analysis_set_for_s3": solvable if ok else []})
    if S2_GATE.exists():
        require(load(S2_GATE)["artifact_sha256"] == rec["artifact_sha256"], "S2 gate exists and differs")
    write(S2_GATE, rec)
    print(f"{rec['token']} " + json.dumps({"solvable": len(solvable), "episodes": eps, **th}))
    return 0


def compute_summary() -> dict:
    tasks = members()
    g = gate_record()
    rows = episode_rows("s2") + ([] if s3_skipped() else episode_rows("s3"))
    analysis = list(g["analysis_set_for_s3"])
    per_arm: dict[str, dict] = {}
    for arm in ("GOLD_HARD", "RMCSS_HARD", "AGENT_HARD"):
        for rep in REPS:
            rr = [r for r in rows if r["arm"] == arm and r["replicate"] == rep]
            if not rr:
                continue
            per_arm[f"{arm}:{rep}"] = {
                "n": len(rr), "applied": sum(r["status"] == "APPLIED" for r in rr),
                "no_scope": sum(r["status"] == "NO_SCOPE" for r in rr),
                "invalid": sum(r["status"] == "INVALID_AFTER_REPAIR" for r in rr),
                "robust_all": sum(r["robust_resolved"] for r in rr),
                "strict_all": sum(r["strict_resolved"] for r in rr),
                "robust_analysis_set": sum(r["robust_resolved"] for r in rr
                                           if r["task_id"] in analysis),
                "strict_analysis_set": sum(r["strict_resolved"] for r in rr
                                           if r["task_id"] in analysis),
                "f2p_pass": sum(r["f2p_pass"] for r in rr),
                "f2p_node_progress": f"{sum(r['f2p_nodes_pass3'] for r in rr)}/"
                                     f"{sum(r['f2p_nodes_total'] for r in rr)}",
                "calls": sum(r["calls"] for r in rr), "repair_used": sum(r["repair_used"] for r in rr),
                "taxonomy": dict(Counter(r["taxonomy"]["label"] for r in rr)),
                "tokens": sum(r["tokens"] for r in rr),
                "cost_usd": round(sum(r["cost_usd"] for r in rr), 7)}
    paired = {}
    if not s3_skipped():
        for rep in REPS:
            w = lo = ti = 0
            for t in analysis:
                def res(arm: str, t: str = t, rep: str = rep) -> bool:
                    return any(r["robust_resolved"] for r in rows
                               if r["arm"] == arm and r["replicate"] == rep and r["task_id"] == t)
                rv, av = res("RMCSS_HARD"), res("AGENT_HARD")
                w += rv and not av
                lo += av and not rv
                ti += rv == av
            paired[rep] = {"rmcss_only": w, "agent_only": lo, "ties": ti}
    led = [json.loads(x) for x in LEDGER.read_text(encoding="utf-8").splitlines()
           if x.strip()] if LEDGER.exists() else []
    instrument_ok = (not any(r["unevaluated"] or r["scope_violation"] for r in rows)
                     and not verify_generation_freeze("s2")
                     and (s3_skipped() or not verify_generation_freeze("s3")))
    require(instrument_ok, "summary instrument invariant")
    tokens = [load(OPWS_SUMMARY)["token"],
              g["token"] if g["verdict"] != "PASS" else "M15R_COMPLETE_DESCRIPTIVE"]
    return {"artifact": "m15r_summary", "design_artifact_sha256": DESIGN_SHA, "tokens": tokens,
            "s2_gate": {k: g[k] for k in ("verdict", "token", "thresholds", "gold_solvable_tasks",
                                          "gold_robust_episodes")},
            "s3_executed": not s3_skipped(), "analysis_set": analysis, "n_tasks": len(tasks),
            "members": tasks, "per_arm_replicate": per_arm, "paired_s3_analysis_set": paired,
            "rows": rows, "opws_summary_artifact_sha256": load(OPWS_SUMMARY)["artifact_sha256"],
            "cost": {"agent_localization_usd_frozen_list_price": round(agent_spend_usd(), 7),
                     "agent_localization": agent_usage(),
                     "generation_provider_reported_usd": round(sum(float(r.get("cost_usd", 0) or 0)
                                                                   for r in led), 7),
                     "generation_provider_reported_tokens": sum(
                         int(r.get("prompt_tokens", 0) or 0) + int(r.get("completion_tokens", 0) or 0)
                         for r in led),
                     "rmcss_selector": "frozen out-of-fold predictions; no M15-R model call"},
            "winner_tokens": [], "auto_execution_of_M16": False,
            "mandatory_wording": ("M15-R is descriptive (n <= 10 Pilot-B tasks). OPWS (S1) is "
                                  "the primary, generator-independent selector endpoint. Generation "
                                  "results (S3) are interpreted only on GOLD-solvable tasks and "
                                  "only if the S2 gate passed. No superiority claim.")}


def summary() -> int:
    require(OPWS_SUMMARY.exists(), "OPWS summary missing")
    require(eval_complete("s2") == 0 and (s3_skipped() or eval_complete("s3") == 0),
            "evaluation incomplete")
    s = self_hash(dict(compute_summary(), artifact_sha256=""))
    write(SUMMARY, s)
    lines = ["# WP2 M15-R V1 result (Pilot-B, descriptive)", "",
             f"Tokens: **{' + '.join(s['tokens'])}**. S3 executed: **{s['s3_executed']}**.",
             f"S2 gate: {json.dumps(s['s2_gate'], sort_keys=True)}.", "",
             "| Arm:rep | n | APPLIED | NO_SCOPE | INVALID | robust (all) | strict (all) | "
             "robust (analysis set) | F2P | tokens | cost $ |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for k, v in s["per_arm_replicate"].items():
        lines.append(f"| {k} | {v['n']} | {v['applied']} | {v['no_scope']} | {v['invalid']} | "
                     f"{v['robust_all']} | {v['strict_all']} | {v['robust_analysis_set']} | "
                     f"{v['f2p_pass']} | {v['tokens']} | {v['cost_usd']} |")
    lines += ["", f"Paired S3 (analysis set): {json.dumps(s['paired_s3_analysis_set'])}.",
              f"Cost: {json.dumps(s['cost'], sort_keys=True)}.", "", s["mandatory_wording"], ""]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print("M15R_SUMMARY " + json.dumps({"tokens": s["tokens"]}))
    return 0


# ------------------------------------------------------------------ CLI
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    for x in ("guard", "readiness-check", "membership", "auth-check", "doctor-offline",
              "doctor-paid", "agent-prefreeze", "agent-complete", "freeze", "freeze-verify",
              "opws-plan", "opws-complete", "opws-summary", "s2-gate", "summary"):
        sp.add_parser(x)
    q = sp.add_parser("readiness")
    q.add_argument("--max-new", type=int, default=1)
    q = sp.add_parser("agent")
    q.add_argument("--max-items", type=int, default=10)
    q = sp.add_parser("opws-evaluate")
    q.add_argument("--max-evals", type=int, default=2)
    for x in ("generate", "generation-complete", "generation-freeze", "generation-freeze-verify",
              "eval-plan", "evaluate", "eval-complete"):
        q = sp.add_parser(x)
        q.add_argument("--stage", choices=("s2", "s3"), required=True)
        if x == "generate":
            q.add_argument("--max-new", type=int, default=10)
            q.add_argument("--max-seconds", type=float, default=5400)
        if x == "evaluate":
            q.add_argument("--max-evals", type=int, default=4)
    a = ap.parse_args(argv)
    fns: dict[str, Callable[[], int]] = {
        "guard": guard, "readiness": lambda: readiness(a.max_new),
        "readiness-check": readiness_check, "membership": membership, "auth-check": auth_check,
        "doctor-offline": lambda: doctor("offline"), "doctor-paid": lambda: doctor("paid"),
        "agent-prefreeze": agent_prefreeze, "agent": lambda: agent(a.max_items),
        "agent-complete": agent_complete, "freeze": freeze, "freeze-verify": freeze_verify,
        "opws-plan": opws_plan, "opws-evaluate": lambda: opws_evaluate(a.max_evals),
        "opws-complete": opws_complete, "opws-summary": opws_summary,
        "generate": lambda: generate(a.stage, a.max_new, a.max_seconds),
        "generation-complete": lambda: generation_complete(a.stage),
        "generation-freeze": lambda: generation_freeze(a.stage),
        "generation-freeze-verify": lambda: generation_freeze_verify(a.stage),
        "eval-plan": lambda: eval_plan(a.stage),
        "evaluate": lambda: evaluate(a.stage, a.max_evals),
        "eval-complete": lambda: eval_complete(a.stage), "s2-gate": s2_gate, "summary": summary}
    try:
        return fns[a.cmd]()
    except Stop as exc:
        print(f"M15R_STOP {a.cmd} code={exc.code}: {exc}")
        return exc.code
    except Exception as exc:
        if type(exc).__name__ == "EvalInfraError":
            print(f"M15R_EVAL_INFRA {a.cmd}: {exc}")
            return EXIT_EVAL_INFRA
        print(f"M15R_STEP_ERROR {a.cmd} {type(exc).__name__}: {exc}")
        traceback.print_exc()
        return EXIT_INVARIANT


if __name__ == "__main__":
    raise SystemExit(main())
