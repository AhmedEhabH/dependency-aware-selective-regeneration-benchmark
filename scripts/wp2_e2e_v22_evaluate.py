#!/usr/bin/env python3
"""WP-2 E2E Smoke v2.2 evaluation wrapper (brain-authored kit; hash-verified).

Reuses the frozen v2.1 evaluator (materialize / evaluate_state / score / unique-diff
plan) unchanged, pointed at the v2.2 root, and fixes two latent v2.1 defects:

- D7: ``benchmark.wp2.e2e.evaluate.E2E_ROOT`` defaults to the IMMUTABLE v1 root, and the
  v2.1 script never re-pointed it, so JUnit evidence would have been written into v1.
  Here it is pointed at the v2.2 root before any evaluation.
- D8: v2.1 by-construction records were written to evaluations/<subdir>/<label>/ with no
  task id, so records of different tasks collided. Here the path is
  evaluations/<subdir>/<task_id>/<label>/evaluation.json (the v2.1 summary rglob reads it).

Usage:
  python scripts/wp2_e2e_v22_evaluate.py --plan
  python scripts/wp2_e2e_v22_evaluate.py --resume --max-evals 4
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

from benchmark.wp2.e2e_v22.common import V22_ROOT, json_sha256  # noqa: E402


def load_v21_evaluate() -> ModuleType:
    path = PROJECT / "scripts" / "wp2_e2e_smoke_v21_evaluate.py"
    spec = importlib.util.spec_from_file_location("wp2_e2e_smoke_v21_evaluate_for_v22", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.V21_ROOT = V22_ROOT  # every function in the module reads this global at call time
    return mod


def point_evaluator_at_v22() -> None:
    from benchmark.wp2.e2e import evaluate as ev
    ev.E2E_ROOT = V22_ROOT


def by_construction_path(root: Path, subdir: str, task_id: str, label: str) -> Path:
    return root / "evaluations" / subdir / task_id / label / "evaluation.json"


def label_collisions(plan: dict) -> list[str]:
    """The reused v2.1 evaluator stores unique evaluations at unique_<sha8> (not task-scoped).
    Two distinct (task_id, diff) items sharing a label would silently share one record, so
    the v2.2 wrapper refuses such a plan (fail closed) instead of scoring the wrong task."""
    seen: dict[str, tuple[str, str]] = {}
    bad: list[str] = []
    for it in plan["items"]:
        label = f"unique_{it['diff_sha256'][:8]}"
        key = (it["task_id"], it["diff_sha256"])
        if label in seen and seen[label] != key:
            bad.append(f"{label}: {seen[label][0]} vs {key[0]}")
        seen.setdefault(label, key)
    return bad


def by_construction_records(mod: ModuleType, sets: dict) -> int:
    n = 0
    for it in mod._collect_by_construction():
        task = it["task_id"]
        rec_path = by_construction_path(V22_ROOT, it["subdir"], task, it["label"])
        if rec_path.exists():
            continue
        t = sets["tasks"].get(task)
        if t is None:
            raise RuntimeError(f"task missing from evaluator sets: {task}")
        f2p = "FAIL" if t["behavioral_f2p_node_ids"] else "UNDEFINED"
        p2ps = "PASS_BY_CONSTRUCTION" if t["p2p_s_defined"] else "UNDEFINED"
        p2pu = "PASS_BY_CONSTRUCTION" if t["p2p_u_cap200_defined"] else "UNDEFINED"
        rec = {"task_id": task, "label": it["label"], "arm": it["arm"],
               "diff_sha256": it["diff_sha256"], "status": "BY_CONSTRUCTION", "groups": {},
               "f2p_task": f2p, "p2p_s_task": p2ps, "p2p_u200_task": p2pu,
               "resolved": False, "flaky_under_patch": [], "source": it["source"],
               "evaluation_sha256": ""}
        rec["evaluation_sha256"] = json_sha256(rec)
        rec_path.parent.mkdir(parents=True, exist_ok=True)
        rec_path.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
        n += 1
    return n


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--max-evals", type=int, default=4)
    args = ap.parse_args(argv)
    if not (V22_ROOT / "generation_freeze_v22.json").exists():
        print("EVAL_REFUSED generation freeze missing (outcome-blind order)")
        return 1
    mod = load_v21_evaluate()
    point_evaluator_at_v22()
    if args.plan:
        fresh = mod.build_plan()
        collisions = label_collisions(fresh)
        if collisions:
            print("EVAL_PLAN_REFUSED label collision: " + "; ".join(collisions))
            return 1
        existing_path = V22_ROOT / "evaluations" / "plan.json"
        if existing_path.exists():  # idempotent re-run: same items -> keep the frozen plan
            existing = json.loads(existing_path.read_text(encoding="utf-8"))
            if existing["items"] != fresh["items"]:
                print("EVAL_PLAN_REFUSED existing plan differs from the frozen generation")
                return 1
            print(f"EVAL_PLAN existing n_unique_diffs={existing['n_unique_diffs']}")
            return 0
        plan = mod.persist_plan()
        print(f"EVAL_PLAN n_unique_diffs={plan['n_unique_diffs']} sha={plan['plan_sha256']}")
        return 0
    plan_path = V22_ROOT / "evaluations" / "plan.json"
    if plan_path.exists():
        collisions = label_collisions(json.loads(plan_path.read_text(encoding="utf-8")))
        if collisions:
            print("EVAL_REFUSED label collision: " + "; ".join(collisions))
            return 1
    evaluated = mod.run_eval(args.max_evals, telemetry=True)
    from benchmark.wp2.e2e.evaluator_sets import load_evaluator_sets
    n_bc = by_construction_records(mod, load_evaluator_sets())
    print(f"EVAL_CHUNK evaluated={evaluated} by_construction_written={n_bc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
