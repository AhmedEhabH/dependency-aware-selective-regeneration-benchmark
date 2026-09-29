#!/usr/bin/env python3
"""WP-2 E2E Smoke v2.2 evaluation wrapper (brain-authored kit v2.2.1; hash-verified).

Reuses the frozen v2.1 evaluator primitives (materialize / evaluate_state / score) and the
v2.1 unique-diff plan builder (dedup by (task_id, diff_sha256)) unchanged, pointed at the
v2.2 root. It fixes these latent v2.1 defects:

- D7: ``benchmark.wp2.e2e.evaluate.E2E_ROOT`` defaults to the IMMUTABLE v1 root. It is
  pointed at the v2.2 root before any evaluation.
- D8: by-construction records are task-scoped:
  evaluations/<subdir>/<task_id>/<label>/evaluation.json
- D9 (amendment v2.2.1): v2.1 stored unique evaluations at unique_<diff_sha[:8]>, with no
  task id. Identical diffs on different tasks (for example the no-op diff that 7 tasks
  produced) would silently share one record. The scientific evaluation identity is now
  (task_id, full diff_sha256):
      evaluations/unique/<task_id>/<full_diff_sha256>/evaluation.json
  Deduplication happens ONLY when task_id AND the full diff hash are both identical.

Usage:
  python scripts/wp2_e2e_v22_evaluate.py --plan
  python scripts/wp2_e2e_v22_evaluate.py --plan-check      (no writes)
  python scripts/wp2_e2e_v22_evaluate.py --resume --max-evals 4
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from wp2_e2e_v22_freeze import eval_identity_label, unique_eval_path  # noqa: E402

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


def identity_problems(plan: dict[str, Any]) -> list[str]:
    """Plan invariants: every item has a task id and a FULL 64-hex diff hash, and
    (task_id, diff_sha256) is unique. Identical diffs on different tasks are allowed;
    they are distinct identities."""
    bad: list[str] = []
    seen: set[tuple[str, str]] = set()
    for it in plan["items"]:
        task, sha = it.get("task_id", ""), it.get("diff_sha256", "")
        if not task or len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
            bad.append(f"bad identity {task!r}/{sha!r}")
            continue
        if (task, sha) in seen:
            bad.append(f"duplicate identity {task}/{sha[:12]}")
        seen.add((task, sha))
    return bad


def cross_task_groups(plan: dict[str, Any]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for it in plan["items"]:
        groups.setdefault(it["diff_sha256"], []).append(it["task_id"])
    return {sha: sorted(ts) for sha, ts in groups.items() if len(set(ts)) > 1}


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


def diff_text(item: dict[str, Any]) -> str:
    src = V22_ROOT / item["source"]
    patch = src.parent / "final_diff.patch"
    if not patch.exists():
        raise FileNotFoundError(f"final_diff.patch missing for {item['source']}")
    return patch.read_text(encoding="utf-8")


def run_eval(plan: dict[str, Any], max_evals: int,
             materialize: Callable[..., Any] | None = None,
             evaluate_state: Callable[..., Any] | None = None,
             score: Callable[..., Any] | None = None) -> int:
    """Evaluate plan items in frozen order; one record per (task_id, full diff_sha256)."""
    if materialize is None or evaluate_state is None or score is None:
        from benchmark.wp2.e2e import evaluate as ev
        materialize, evaluate_state, score = ev.materialize, ev.evaluate_state, ev.score
    evaluated = 0
    for item in plan["items"]:
        if max_evals and evaluated >= max_evals:
            break
        task, sha = item["task_id"], item["diff_sha256"]
        rec_path = unique_eval_path(V22_ROOT, task, sha)
        if rec_path.exists():
            continue
        label = eval_identity_label(sha)
        print(f"[eval] {time.strftime('%H:%M:%S')} task={task} identity={sha[:16]} "
              f"label={label}", flush=True)
        text = diff_text(item)
        wt, tree_sha = materialize(task, label, text)
        eval_rec = evaluate_state(task, label, wt)
        scd = score(task, label, eval_rec["groups"])
        rec = {"task_id": task, "diff_sha256": sha, "eval_identity": f"{task}/{sha}",
               "label": label, "tree_sha": tree_sha, "status": "DONE",
               "diff_file_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
               "groups": eval_rec["groups"],
               **{k: scd[k] for k in ("f2p_task", "p2p_s_task", "p2p_u200_task",
                                      "resolved", "flaky_under_patch")},
               "sources": [item["source"]] + item.get("also_sources", []),
               "labels": [item["label"]] + item.get("also_labels", []),
               "evaluation_sha256": ""}
        rec["evaluation_sha256"] = json_sha256(rec)
        rec_path.parent.mkdir(parents=True, exist_ok=True)
        rec_path.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"[eval] {task} {sha[:12]} -> f2p={rec['f2p_task']} p2ps={rec['p2p_s_task']} "
              f"p2pu={rec['p2p_u200_task']} resolved={rec['resolved']}", flush=True)
        evaluated += 1
    return evaluated


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--plan-check", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--max-evals", type=int, default=4)
    args = ap.parse_args(argv)
    if not (V22_ROOT / "generation_freeze_v22.json").exists():
        print("EVAL_REFUSED generation freeze missing (outcome-blind order)")
        return 1
    mod = load_v21_evaluate()
    point_evaluator_at_v22()
    plan_path = V22_ROOT / "evaluations" / "plan.json"
    if args.plan or args.plan_check:
        fresh = mod.build_plan()
        problems = identity_problems(fresh)
        if problems:
            print("EVAL_PLAN_REFUSED " + "; ".join(problems[:20]))
            return 1
        groups = cross_task_groups(fresh)
        info = {"n_unique_identities": fresh["n_unique_diffs"],
                "cross_task_identical_diff_groups": {k[:16]: v for k, v in groups.items()}}
        if args.plan_check:
            print("EVAL_PLAN_CHECK " + json.dumps(info, sort_keys=True))
            return 0
        if plan_path.exists():  # idempotent re-run: same items -> keep the frozen plan
            existing = json.loads(plan_path.read_text(encoding="utf-8"))
            if existing["items"] != fresh["items"]:
                print("EVAL_PLAN_REFUSED existing plan differs from the frozen generation")
                return 1
            print(f"EVAL_PLAN existing n_unique_identities={existing['n_unique_diffs']}")
            return 0
        plan = mod.persist_plan()
        print(f"EVAL_PLAN n_unique_identities={plan['n_unique_diffs']} "
              f"sha={plan['plan_sha256']} " + json.dumps(info, sort_keys=True))
        return 0
    if not plan_path.exists():
        print("EVAL_REFUSED evaluation plan missing")
        return 1
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    problems = identity_problems(plan)
    if problems:
        print("EVAL_REFUSED " + "; ".join(problems[:20]))
        return 1
    evaluated = run_eval(plan, args.max_evals)
    from benchmark.wp2.e2e.evaluator_sets import load_evaluator_sets
    n_bc = by_construction_records(mod, load_evaluator_sets())
    print(f"EVAL_CHUNK evaluated={evaluated} by_construction_written={n_bc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
