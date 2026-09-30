#!/usr/bin/env python3
"""WP2 M14A-E1 driver (brain-authored). ZERO model API.

Completes Pilot-A P12/P13 after the P12 STOP:EVAL_ERROR of 2026-09-30 under the
preregistered evaluator amendment E1 (see scripts/wp2_m14a_evalcore_e1.py and
research/wp2/pilot_a_v1/m14a_e1_amendment.json). No frozen file is modified:
`wp2_m14a_run.py` is imported and reused unchanged; only the per-diff evaluation
function is replaced (the `evaluate_fn` injection point of `run.evaluate`).

Subcommands
  verify              read-only: original freezes, amendment artifact, original STOP state,
                      pre-amendment evaluation records unchanged
  evaluate --max-evals N   one P12-equivalent chunk with the E1 evaluation function
  addendum            mechanical E1 addendum (json + md) after evaluation is complete
Exit codes: 0 PASS/progress, 1 check-not-yet, 78 invariant, 79 evaluation infrastructure
error (resumable).
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
for _p in (PROJECT, PROJECT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import scripts.wp2_m14a_run as run  # noqa: E402  (frozen engine, reused unchanged)
from scripts import wp2_m14a_evalcore_e1 as e1  # noqa: E402

AMEND = run.ROOT / "m14a_e1_amendment.json"
ORIG_STATE = run.ROOT / "controller_state.json"
DIAG_ROOT = run.ROOT / "evaluations/diagnostics"
ADDENDUM = run.ROOT / "m14a_e1_addendum.json"
ADDENDUM_MD = run.PROJECT / "docs/WP2_M14A_E1_RESULT_ADDENDUM.md"
ORIG_PHASES_PASS = ["P00_KIT_SELFTEST", "P01_GUARD", "P02_READINESS", "P03_MEMBERSHIP",
                    "P04_AUTH", "P05_DOCTOR_OFFLINE", "P06_DOCTOR_PAID", "P07_CANARY",
                    "P08_FREEZE", "P09_GENERATE", "P10_GENERATION_FREEZE", "P11_EVAL_PLAN"]


def diag_path(task_id: str, label: str) -> Path:
    return DIAG_ROOT / task_id / label / "e1_diagnostics.json"


def readiness_ok(task_id: str) -> bool:
    """R4: the frozen readiness record (self-hashed) shows gold/empty trees started pytest."""
    p = run.ROOT / "readiness" / task_id / "record.json"
    if not p.exists():
        return False
    d = run.load(p)
    return run.hash_ok(d) and d.get("gold_empty_ok") is True


def verify_problems() -> list[str]:
    bad = [f"original: {x}" for x in run.verify_generation_freeze()]
    if not AMEND.exists():
        return bad + ["amendment artifact missing"]
    a = run.load(AMEND)
    if not run.hash_ok(a):
        bad.append("amendment self-hash")
    for r, h in a.get("e1_file_hashes", {}).items():
        p = run.PROJECT / r
        if not p.exists() or run.norm_sha(p) != h:
            bad.append(f"e1 file drift {r}")
    for r, h in a.get("frozen_files_unchanged", {}).items():
        p = run.PROJECT / r
        if not p.exists() or run.norm_sha(p) != h:
            bad.append(f"frozen file drift {r}")
    if a.get("rule_constants_sha256") != e1.rule_constants_sha():
        bad.append("rule constants differ from amendment")
    st = run.load(ORIG_STATE) if ORIG_STATE.exists() else {}
    stop = st.get("stop") or {}
    if not (stop.get("token") == "EVAL_ERROR" and stop.get("phase") == "P12_EVALUATE"):
        bad.append("original controller state is not STOP:EVAL_ERROR at P12")
    ph = st.get("phases", {})
    if any(ph.get(x, {}).get("status") != "PASS" for x in ORIG_PHASES_PASS):
        bad.append("original P00-P11 not all PASS")
    for rel_path, sha in a.get("pre_amendment_evaluations", {}).items():
        p = run.PROJECT / rel_path
        if run.record_state(p) != "VALID" or run.load(p).get("evaluation_sha256") != sha:
            bad.append(f"pre-amendment evaluation changed {rel_path}")
    return bad


def verify() -> int:
    bad = verify_problems()
    print("M14A_E1_VERIFY_PASS" if not bad else "M14A_E1_VERIFY_FAIL " + str(bad[:6]))
    return 0 if not bad else run.EXIT_INVARIANT


def diff_map() -> dict[tuple[str, str], str]:
    out: dict[tuple[str, str], str] = {}
    for i in run.load(run.EVAL_PLAN)["items"]:
        txt = (run.ROOT / i["source"]).parent.joinpath("final_diff.patch").read_text(
            encoding="utf-8")
        out[(i["task_id"], "u_" + i["diff_sha256"][:12])] = txt
    return out


def evaluate(max_evals: int, evaluate_fn=None) -> int:
    bad = verify_problems()
    run.require(not bad, f"E1 verify failed {bad[:3]}")
    if evaluate_fn is None:
        from scripts.wp2_m14a_evalcore import point_evaluator
        ev = point_evaluator(run.EVAL_SETS, run.ROOT)
        dm = diff_map()

        def evaluate_fn(t: str, lab: str, wt: str) -> dict:
            return e1.evaluate_state_e1(ev, t, lab, wt, diff_text=dm[(t, lab)],
                                        diag_path=diag_path(t, lab),
                                        parent_starts_ok=readiness_ok(t))
    return run.evaluate(max_evals, evaluate_fn=evaluate_fn)


def addendum() -> int:
    run.require(run.eval_complete() == 0, "evaluation incomplete")
    plan = {(i["task_id"], "u_" + i["diff_sha256"][:12]): i for i in run.load(run.EVAL_PLAN)["items"]}
    rows = []
    for p in sorted(DIAG_ROOT.glob("*/*/e1_diagnostics.json")):
        d = run.load(p)
        i = plan.get((d["task_id"], d["label"]), {})
        rec = run.load(run.unique_path(i["task_id"], i["diff_sha256"])) if i else {}
        rows.append({"task_id": d["task_id"], "label": d["label"], "decision": d["decision"],
                     "diff_sha256": i.get("diff_sha256", ""),
                     "arm_labels": [i.get("label", "")] + i.get("also_labels", []),
                     "arm": i.get("arm", ""), "missing_runs": d["missing_runs"],
                     "rcs": d["rcs"], "edited_files_in_log": sorted(
                         {f for r in d["per_run"].values() for f in r["edited_files_in_log"]}),
                     "scored": {k: rec.get(k) for k in ("f2p_task", "p2p_s_task",
                                                          "p2p_u200_task", "resolved")},
                     "diagnostics": run.rel(p)})
    applied = [r for r in rows if r["decision"] == e1.PATCH_STARTUP_FAILURE]
    out = {"artifact": "m14a_e1_addendum", "rule_id": e1.RULE_ID,
           "amendment_sha256": run.load(AMEND)["artifact_sha256"],
           "n_unique_evaluations": run.load(run.EVAL_PLAN)["n_unique_identities"],
           "n_patch_startup_failure": len(applied), "rows": rows, "artifact_sha256": ""}
    run.write(ADDENDUM, run.self_hash(out))
    lines = ["# WP2 Pilot-A V1: M14A-E1 evaluator amendment addendum", "",
             f"Rule: `{e1.RULE_ID}`. Unique evaluations: {out['n_unique_evaluations']}. "
             f"Scored under E1 as PATCH_STARTUP_FAILURE: {len(applied)}.", "",
             "A patch whose tree cannot start pytest (all runs without JUnit, a Python traceback "
             "naming an edited file, parent/gold trees verified to start in readiness) is scored "
             "with every node `missing` (not passed), the frozen Smoke v2.2 semantics. Every other "
             "missing JUnit remained an infrastructure STOP.", "",
             "| Task | Arm | Diff | Decision | Edited file(s) in traceback | F2P | P2P-S | P2P-U200 |",
             "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        s = r["scored"]
        lines.append(f"| {r['task_id']} | {r['arm']} ({', '.join(r['arm_labels'])}) | "
                     f"{r['diff_sha256'][:12]} | {r['decision']} | "
                     f"{', '.join(r['edited_files_in_log'])} | {s.get('f2p_task')} | "
                     f"{s.get('p2p_s_task')} | {s.get('p2p_u200_task')} |")
    lines += ["", "Descriptive addendum. It changes no gate, threshold or endpoint.", ""]
    ADDENDUM_MD.parent.mkdir(parents=True, exist_ok=True)
    ADDENDUM_MD.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print("M14A_E1_ADDENDUM " + json.dumps({"n_patch_startup_failure": len(applied)}))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("verify")
    sp.add_parser("addendum")
    q = sp.add_parser("evaluate")
    q.add_argument("--max-evals", type=int, default=4)
    a = ap.parse_args(argv)
    fns = {"verify": verify, "addendum": addendum, "evaluate": lambda: evaluate(a.max_evals)}
    try:
        return fns[a.cmd]()
    except run.Stop as exc:
        print(f"M14A_STOP {a.cmd} code={exc.code}: {exc}")
        return exc.code
    except Exception as exc:
        if type(exc).__name__ == "EvalInfraError":
            print(f"M14A_EVAL_INFRA {a.cmd}: {exc}")
            return run.EXIT_EVAL_INFRA
        print(f"M14A_STEP_ERROR {a.cmd} {type(exc).__name__}: {exc}")
        traceback.print_exc()
        return run.EXIT_INVARIANT


if __name__ == "__main__":
    raise SystemExit(main())
