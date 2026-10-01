#!/usr/bin/env python3
"""WP2 M15-R evaluator amendment E1A1 (brain-authored). ZERO model API.

Discovery (2026-10-01, Q16_S2_EVALUATE, STOP EVAL_ERROR, resumable)
------------------------------------------------------------------
Identity saleor-rc-0a39d039049d / u_2d7cf6d90275 (frozen S2 GOLD G0 r3 patch) made all six
active runs (C_0..C_2, U_0..U_2) exit rc=1 before pytest wrote JUnit, every run with the
identical log (sha 454cde87...) ending in Graphene's schema builder:

    AssertionError: Found different types with the same name in the schema: Date, Date.

The patch declares `graphene.Date(...)`; the repository already registers its own scalar
named `Date`, so building the GraphQL schema at import time fails. The parent tree starts
(readiness), so the failure is caused by the patch. The frozen E1 rule
(M14A_E1_PATCH_STARTUP_FAILURE_V1) requires the traceback to NAME an edited file (R3); this
schema-level failure is raised from Graphene's own frames, so E1 answered INFRA_UNCLASSIFIED
and the engine stopped. The patch must be scored as a failure, never edited.

Rule M15R_E1A1_GRAPHQL_DUPLICATE_TYPE_STARTUP_V1 (applies ONLY when frozen E1 says
INFRA_UNCLASSIFIED; every condition required)
  A1 the frozen E1 diagnostics of THIS call exist, are self-hash valid, have the frozen E1
     rule id and decision INFRA_UNCLASSIFIED;
  A2 EVERY active run is missing JUnit (missing_runs == active_runs, non-empty);
  A3 parent_starts_ok is true and the patch edits >= 1 file;
  A4 for every run: rc 1..127, log present, traceback marker and exception line present
     (frozen E1 R3 minus the edited-file-name clause);
  A5 for every run: the last non-empty log line is the generic Graphene schema assertion
     `AssertionError: Found different types with the same name in the schema: ...` and the
     log tail contains a Graphene type-map frame (`graphene/types/`). No type name, task id
     or scalar is special-cased.
If A1-A5 hold: every node of every active group gets ["missing"] * REPS (exactly the frozen
E1 PATCH_STARTUP_FAILURE outcome) and e1_decision = "PATCH_STARTUP_FAILURE_E1A1". Otherwise
the original EvalInfraError is re-raised unchanged (resumable EVAL_ERROR, brain review).

Scope: S2 and S3 evaluation of the M15-R continuation only. When frozen E1 returns normally
(JUnit present, or E1's own PATCH_STARTUP_FAILURE) the result is returned unchanged, so
records already written under frozen E1 (S0, S1, the two S2 records) are exactly what E1A1
would write: nothing is re-evaluated. The frozen E1 module, the M15-R engine, the design,
scopes, episodes and patches are not modified.

Subcommands: verify | evaluate --stage s2|s3 --max-evals N
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import traceback
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
for _p in (PROJECT, PROJECT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import scripts.wp2_m15r_run as m15r  # noqa: E402  (frozen engine, imported unchanged)

RULE_ID = "M15R_E1A1_GRAPHQL_DUPLICATE_TYPE_STARTUP_V1"
DECISION = "PATCH_STARTUP_FAILURE_E1A1"
FROZEN_E1_RULE_ID = "M14A_E1_PATCH_STARTUP_FAILURE_V1"
SIGNATURE_RE = re.compile(r"^(?:E\s+)?AssertionError: Found different types with the same name in the "
                          r"schema: \S")
FRAME_RE = re.compile(r"graphene/types/")
RULE_CONSTANTS = {"rule_id": RULE_ID, "applies_to_e1_decision": "INFRA_UNCLASSIFIED",
                  "signature_re": SIGNATURE_RE.pattern, "frame_re": FRAME_RE.pattern,
                  "signature_position": "last non-empty line of every run's log tail",
                  "rc_range": [1, 127], "require_all_runs_missing": True,
                  "require_parent_starts_ok": True, "require_edited_paths": True,
                  "missing_outcome": "missing", "decision": DECISION}
AMENDMENT = m15r.ROOT / "m15r_e1a1_amendment.json"
DIAG_DIR = m15r.ROOT / "evaluations/diagnostics_e1a1"


def rule_constants_sha() -> str:
    return hashlib.sha256(json.dumps(RULE_CONSTANTS, sort_keys=True).encode("utf-8")).hexdigest()


def _sha_obj(x: Any) -> str:
    return hashlib.sha256(json.dumps(x, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def diag_hash_ok(d: dict) -> bool:
    q = copy.deepcopy(d)
    got = q.get("artifact_sha256", "")
    q["artifact_sha256"] = ""
    return bool(got) and _sha_obj(q) == got


def last_line(tail: list[str]) -> str:
    return next((x for x in reversed(tail or []) if x.strip()), "")


def decide_e1a1(d: dict) -> tuple[str, list[str]]:
    """A1-A5 on a frozen E1 diagnostics record. Pure function (unit-tested).
    Returns (decision, failed_conditions); decision is DECISION or 'NOT_APPLICABLE'."""
    bad: list[str] = []
    if not (diag_hash_ok(d) and d.get("rule_id") == FROZEN_E1_RULE_ID
            and d.get("decision") == "INFRA_UNCLASSIFIED"):
        bad.append("A1")
    active, missing = sorted(d.get("active_runs") or []), sorted(d.get("missing_runs") or [])
    if not active or active != missing:
        bad.append("A2")
    if d.get("parent_starts_ok") is not True or not d.get("edited_paths"):
        bad.append("A3")
    per = d.get("per_run") or {}
    for k in missing or ["<none>"]:
        r = per.get(k)
        if not r or not (r.get("log_present") and r.get("rc_in_range") and r.get("traceback")
                         and r.get("exception_line")):
            bad.append(f"A4:{k}")
            continue
        tail = r.get("log_tail_redacted") or []
        if not SIGNATURE_RE.search(last_line(tail).strip()) or not any(FRAME_RE.search(x) for x in tail):
            bad.append(f"A5:{k}")
    return (DECISION if not bad else "NOT_APPLICABLE"), bad


def diag_path_for(task_id: str, label: str) -> Path:
    return DIAG_DIR / task_id / label / "e1_diagnostics.json"


def evaluate_state_e1a1(ev: Any, task_id: str, label: str, worktree: str, *, diff_text: str,
                        diag_path: Path, parent_starts_ok: bool, e1_fn: Any = None) -> dict:
    """Frozen evaluate_state_e1, plus E1A1 on its INFRA_UNCLASSIFIED outcome only."""
    from scripts.wp2_m14a_evalcore import EvalInfraError
    if e1_fn is None:
        from scripts.wp2_m14a_evalcore_e1 import evaluate_state_e1 as e1_fn
    if diag_path.exists():
        diag_path.unlink()                                   # never decide on a stale record
    try:
        return e1_fn(ev, task_id, label, worktree, diff_text=diff_text, diag_path=diag_path,
                     parent_starts_ok=parent_starts_ok)
    except EvalInfraError:
        if not diag_path.exists():
            raise
        d = json.loads(diag_path.read_text(encoding="utf-8"))
        decision, failed = decide_e1a1(d)
        rec = {"artifact": "m15r_e1a1_decision", "rule_id": RULE_ID,
               "rule_constants_sha256": rule_constants_sha(), "task_id": task_id, "label": label,
               "frozen_e1_decision": d.get("decision"), "frozen_e1_diagnostics_sha256":
               d.get("artifact_sha256"), "decision": decision, "failed_conditions": failed,
               "model_api_calls": 0, "artifact_sha256": ""}
        rec["artifact_sha256"] = _sha_obj(rec)
        (diag_path.parent / "e1a1_decision.json").write_text(
            json.dumps(rec, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        if decision != DECISION:
            raise
    t = ev.load_evaluator_sets()["tasks"][task_id]
    groups = {"C": sorted(set(t["behavioral_f2p_node_ids"]) | set(t["p2p_s_node_ids"])),
              "U": list(t["p2p_u_cap200_stable_ids"])}
    return {"task_id": task_id, "label": label, "status": "DONE",
            "groups": {g: {n: ["missing"] * ev.REPS for n in groups[g]} for g in ("C", "U")},
            "junit_files": {}, "skipped_empty_groups": [g for g in ("C", "U") if not groups[g]],
            "e1_decision": DECISION}


def amended_fns() -> Any:
    """m15r.EvalFns whose evaluate step is frozen E1 + E1A1 (materialize is unchanged)."""
    fns = m15r.EvalFns()

    def efn(tk: str, lb: str, wt: str, d: str) -> dict:
        return evaluate_state_e1a1(fns.ev, tk, lb, wt, diff_text=d, diag_path=diag_path_for(tk, lb),
                                   parent_starts_ok=m15r.readiness_ok(tk))
    fns.evaluate_fn = efn
    return fns


def verify() -> int:
    """Zero-API continuation checks before any amended evaluation."""
    a = json.loads(AMENDMENT.read_text(encoding="utf-8"))
    m15r.require(diag_hash_ok(a) and a["rule_id"] == RULE_ID
                 and a["rule_constants_sha256"] == rule_constants_sha(), "amendment record drift")
    for r, h in a["frozen_files_unchanged"].items():
        m15r.require(m15r.norm_sha(PROJECT / r) == h, f"frozen file changed {r}")
    bad = m15r.verify_freeze()
    m15r.require(not bad, f"M15-R freeze drift {bad[:3]}")
    bad = m15r.verify_generation_freeze("s2")
    m15r.require(not bad, f"S2 generation freeze drift {bad[:3]}")
    for r, h in a["pre_amendment_records"].items():
        p = PROJECT / r
        m15r.require(p.exists() and m15r.norm_sha(p) == h, f"pre-amendment record changed {r}")
    st = json.loads((m15r.ROOT / "controller_state.json").read_text(encoding="utf-8"))
    stop = st.get("stop") or {}
    m15r.require(stop.get("token") == "EVAL_ERROR" and stop.get("phase") == "Q16_S2_EVALUATE",
                 "original controller is not stopped at Q16 EVAL_ERROR (do not run the old plan)")
    for pid in a["original_plan_phases_pass"]:
        m15r.require(st["phases"].get(pid, {}).get("status") == "PASS", f"{pid} not PASS")
    print("M15R_E1A1_VERIFY_PASS " + json.dumps({"rule": RULE_ID, "model_api_calls": 0}))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("verify")
    q = sp.add_parser("evaluate")
    q.add_argument("--stage", choices=("s2", "s3"), required=True)
    q.add_argument("--max-evals", type=int, default=4)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "verify":
            return verify()
        return m15r.evaluate(a.stage, a.max_evals, fns=amended_fns())
    except m15r.Stop as exc:
        print(f"M15R_E1A1_STOP {a.cmd} code={exc.code}: {exc}")
        return exc.code
    except Exception as exc:
        if type(exc).__name__ == "EvalInfraError":
            print(f"M15R_E1A1_EVAL_INFRA {a.cmd}: {exc}")
            return m15r.EXIT_EVAL_INFRA
        print(f"M15R_E1A1_STEP_ERROR {a.cmd} {type(exc).__name__}: {exc}")
        traceback.print_exc()
        return m15r.EXIT_INVARIANT


if __name__ == "__main__":
    raise SystemExit(main())
