#!/usr/bin/env python3
"""WP-2 Mission-11 D2 - E2E Smoke evaluation (zero API, workers=1, resumable)."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

E2E_ROOT = PROJECT / "research/wp2/e2e_smoke_eng_v1"

from benchmark.wp2.e2e.evaluate import evaluate_state, materialize, score  # noqa: E402
from benchmark.wp2.e2e.evaluator_sets import load_evaluator_sets  # noqa: E402


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--max-evals", type=int, default=4)
    args = ap.parse_args()

    gen = json.loads((E2E_ROOT / "generation_freeze.json").read_text(encoding="utf-8"))
    # evaluation plan: unique (task, diff_sha) over APPLIED episodes (D39)
    applied = {k: v for k, v in gen["per_episode"].items() if v["status"] == "APPLIED"}
    plan: list[tuple[str, str, str]] = []  # (task, arm, diff_sha)
    seen_diffs: set[str] = set()
    for k, v in applied.items():
        task, arm = k.split("|", 1)
        if v["diff_sha256"] and v["diff_sha256"] not in seen_diffs:
            seen_diffs.add(v["diff_sha256"])
            plan.append((task, arm, v["diff_sha256"]))

    # by-construction scoring for non-APPLIED episodes (D46)
    by_construction = {k: v for k, v in gen["per_episode"].items()
                       if v["status"] in ("NO_SCOPE", "INVALID_AFTER_REPAIR", "GENERATION_FAIL", "SCOPE_MISSING")}
    sets = load_evaluator_sets()
    for k, v in by_construction.items():
        task, arm = k.split("|", 1)
        rec_path = E2E_ROOT / "evaluations" / task / arm / "evaluation.json"
        if rec_path.exists():
            continue
        t = sets["tasks"][task]
        f2p = "FAIL" if t["behavioral_f2p_node_ids"] else "UNDEFINED"
        p2ps = "PASS_BY_CONSTRUCTION" if t["p2p_s_defined"] else "UNDEFINED"
        p2pu = "PASS_BY_CONSTRUCTION" if t["p2p_u_cap200_defined"] else "UNDEFINED"
        rec = {"task_id": task, "label": arm, "diff_sha256": v["diff_sha256"],
               "status": "BY_CONSTRUCTION", "groups": {},
               "f2p_task": f2p, "p2p_s_task": p2ps, "p2p_u200_task": p2pu,
               "resolved": f2p == "PASS" and p2ps in ("PASS", "PASS_BY_CONSTRUCTION", "UNDEFINED")
                           and p2pu in ("PASS", "PASS_BY_CONSTRUCTION", "UNDEFINED"),
               "flaky_under_patch": [],
               "evaluation_sha256": ""}
        rec["evaluation_sha256"] = _sha(rec)
        rec_path.parent.mkdir(parents=True, exist_ok=True)
        rec_path.write_text(json.dumps(rec, indent=1), encoding="utf-8")

    done = 0
    for task, arm, diff_sha in plan:
        if args.max_evals and done >= args.max_evals:
            break
        rec_path = E2E_ROOT / "evaluations" / task / arm / "evaluation.json"
        if rec_path.exists():
            print(f"  {task} {arm} already evaluated; skip")
            done += 1
            continue
        diff_text = (E2E_ROOT / "episodes" / task / arm / "final_diff.patch").read_text(encoding="utf-8")
        wt, tree_sha = materialize(task, f"smoke_{arm[:4]}", diff_text)
        eval_rec = evaluate_state(task, f"smoke_{arm[:4]}", wt)
        scd = score(task, f"smoke_{arm[:4]}", eval_rec["groups"])
        rec = {"task_id": task, "label": arm, "diff_sha256": diff_sha, "tree_sha": tree_sha,
               "status": "DONE", "groups": eval_rec["groups"],
               **{k: scd[k] for k in ("f2p_task", "p2p_s_task", "p2p_u200_task", "resolved", "flaky_under_patch")},
               "evaluation_sha256": ""}
        rec["evaluation_sha256"] = _sha(rec)
        rec_path.parent.mkdir(parents=True, exist_ok=True)
        rec_path.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  {task} {arm} -> f2p={rec['f2p_task']} p2ps={rec['p2p_s_task']} "
              f"p2pu={rec['p2p_u200_task']} resolved={rec['resolved']}")
        done += 1
    print(f"[eval] done this invocation: {done}")
    return 0


def _sha(payload) -> str:
    return hashlib.sha256(
        json.dumps({k: v for k, v in payload.items() if k != "evaluation_sha256"},
                   sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())