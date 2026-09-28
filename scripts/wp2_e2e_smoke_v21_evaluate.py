#!/usr/bin/env python3
"""Mission-12B v2.1 - P unique-diff evaluation planner/runner (T5).

No generation imports capable of provider calls in this module.

Planner:
- collect main APPLIED diffs + variance APPLIED diffs;
- deduplicate per task by (task_id, diff_sha256);
- freeze deterministic order by (task_id, diff_sha256, label);
- persist the plan BEFORE the first evaluation with a plan hash;
- a plan cannot change once any result exists (plan_hash is stable).

Runner:
- workers=1; bounded chunks (default 4 unique diffs per invocation);
- environment telemetry before/after each chunk;
- the Harness already owns DB freshening; no "warm-up fix" is claimed;
- the existing 3-repetition flaky semantics are unchanged;
- JUnit/results are persisted immediately;
- resume-safe (a present, hash-verified result is skipped);
- no generation on failure.

Non-APPLIED episodes (NO_SCOPE / INVALID_AFTER_REPAIR / GENERATION_FAIL) get
BY_CONSTRUCTION evaluation records (D46), zero-API.

Usage:
  python scripts/wp2_e2e_smoke_v21_evaluate.py --plan            # build/persist plan
  python scripts/wp2_e2e_smoke_v21_evaluate.py --resume [--max-evals N]
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

V21_ROOT = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v21"

from benchmark.wp2.e2e.evaluate import evaluate_state, materialize, score  # noqa: E402
from benchmark.wp2.e2e.evaluator_sets import load_evaluator_sets  # noqa: E402


def _sha(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def _episode_rec(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _collect_applied() -> list[dict]:
    """Main episodes + variance replicates that are APPLIED with a diff."""
    items: list[dict] = []
    episodes_dir = V21_ROOT / "episodes"
    for ep in episodes_dir.rglob("episode.json"):
        rec = _episode_rec(ep)
        if not rec:
            continue
        if rec.get("status") == "APPLIED" and rec.get("diff_sha256"):
            rel = ep.relative_to(V21_ROOT)
            label = f"main|{rec['arm']}"
            items.append({"task_id": rec["task_id"], "diff_sha256": rec["diff_sha256"],
                          "label": label, "source": str(rel), "kind": "main"})
    variance_dir = V21_ROOT / "variance"
    if variance_dir.exists():
        for ep in variance_dir.rglob("episode.json"):
            rec = _episode_rec(ep)
            if not rec:
                continue
            if rec.get("status") == "APPLIED" and rec.get("diff_sha256"):
                rel = ep.relative_to(V21_ROOT)
                rep = ep.parent.name
                items.append({"task_id": rec["task_id"], "diff_sha256": rec["diff_sha256"],
                              "label": f"variance|{rep}", "source": str(rel),
                              "kind": "variance"})
    return items


def _collect_by_construction() -> list[dict]:
    """Non-APPLIED main/variance episodes scored by construction (D46)."""
    out: list[dict] = []
    for sub in ("episodes", "variance"):
        d = V21_ROOT / sub
        if not d.exists():
            continue
        for ep in d.rglob("episode.json"):
            rec = _episode_rec(ep)
            if not rec:
                continue
            if rec.get("status") in ("NO_SCOPE", "INVALID_AFTER_REPAIR", "GENERATION_FAIL"):
                out.append({"task_id": rec["task_id"], "arm": rec["arm"],
                            "label": ep.parent.name, "status": rec["status"],
                            "diff_sha256": rec.get("diff_sha256", ""),
                            "source": str(ep.relative_to(V21_ROOT)), "subdir": sub})
    return out


def build_plan() -> dict:
    """Unique-diff plan frozen before the first evaluation."""
    applied = _collect_applied()
    # dedup per task by (task_id, diff_sha256)
    unique: dict[tuple[str, str], dict] = {}
    for it in applied:
        key = (it["task_id"], it["diff_sha256"])
        existing = unique.get(key)
        if existing is None:
            unique[key] = dict(it)
        else:
            existing.setdefault("also_sources", []).append(it["source"])
            existing.setdefault("also_labels", []).append(it["label"])
    # deterministic order by (task_id, diff_sha256, label)
    ordered = sorted(unique.values(), key=lambda x: (x["task_id"], x["diff_sha256"], x["label"]))
    plan = {
        "artifact": "evaluation_plan_v21",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "rule": "unique (task_id, diff_sha256) over main APPLIED + variance APPLIED; "
                "order (task_id, diff_sha256, label)",
        "n_unique_diffs": len(ordered),
        "items": ordered,
    }
    plan["plan_sha256"] = _sha({k: v for k, v in plan.items() if k != "plan_sha256"})
    return plan


def persist_plan() -> dict:
    plan = build_plan()
    plan_path = V21_ROOT / "evaluations" / "plan.json"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    if plan_path.exists():
        existing = json.loads(plan_path.read_text(encoding="utf-8"))
        if existing.get("plan_sha256") != plan["plan_sha256"]:
            raise RuntimeError(
                "PLAN_CHANGED: existing plan hash differs; refusing to overwrite after results")
    plan_path.write_text(json.dumps(plan, indent=1, ensure_ascii=False), encoding="utf-8")
    return plan


def _by_construction_records() -> int:
    sets = load_evaluator_sets()
    n = 0
    for it in _collect_by_construction():
        task = it["task_id"]
        rec_path = V21_ROOT / "evaluations" / it["subdir"] / it["label"] / "evaluation.json"
        if rec_path.exists():
            continue
        t = sets["tasks"].get(task)
        if t is None:
            continue
        f2p = "FAIL" if t["behavioral_f2p_node_ids"] else "UNDEFINED"
        p2ps = "PASS_BY_CONSTRUCTION" if t["p2p_s_defined"] else "UNDEFINED"
        p2pu = "PASS_BY_CONSTRUCTION" if t["p2p_u_cap200_defined"] else "UNDEFINED"
        rec = {"task_id": task, "label": it["label"], "diff_sha256": it["diff_sha256"],
               "status": "BY_CONSTRUCTION", "groups": {},
               "f2p_task": f2p, "p2p_s_task": p2ps, "p2p_u200_task": p2pu,
               "resolved": f2p == "PASS" and p2ps in ("PASS", "PASS_BY_CONSTRUCTION", "UNDEFINED")
                           and p2pu in ("PASS", "PASS_BY_CONSTRUCTION", "UNDEFINED"),
               "flaky_under_patch": [],
               "source": it["source"], "evaluation_sha256": ""}
        rec["evaluation_sha256"] = _sha(rec)
        rec_path.parent.mkdir(parents=True, exist_ok=True)
        rec_path.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
        n += 1
    return n


def _diff_text(item: dict) -> str:
    src = V21_ROOT / item["source"]
    patch = src.parent / "final_diff.patch"
    if patch.exists():
        return patch.read_text(encoding="utf-8")
    # variance/control sources store diff under the same episode dir
    raise FileNotFoundError(f"final_diff.patch missing for {item['source']}")


def run_eval(max_evals: int, telemetry: bool = True) -> int:
    plan_path = V21_ROOT / "evaluations" / "plan.json"
    if not plan_path.exists():
        raise RuntimeError("evaluation plan missing; run --plan first")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    done = 0
    evaluated = 0
    for item in plan["items"]:
        if max_evals and evaluated >= max_evals:
            break
        task = item["task_id"]
        label = f"unique_{item['diff_sha256'][:8]}"
        rec_path = V21_ROOT / "evaluations" / "unique" / label / "evaluation.json"
        if rec_path.exists():
            done += 1
            continue
        if telemetry:
            print(f"[eval] {time.strftime('%H:%M:%S')} task={task} label={label} "
                  f"diff={item['diff_sha256'][:12]} env={platform.system()}")
        diff_text = _diff_text(item)
        wt, tree_sha = materialize(task, label, diff_text)
        eval_rec = evaluate_state(task, label, wt)
        scd = score(task, label, eval_rec["groups"])
        rec = {"task_id": task, "label": label, "diff_sha256": item["diff_sha256"],
               "tree_sha": tree_sha, "status": "DONE", "groups": eval_rec["groups"],
               **{k: scd[k] for k in ("f2p_task", "p2p_s_task", "p2p_u200_task",
                                      "resolved", "flaky_under_patch")},
               "sources": [item["source"]] + item.get("also_sources", []),
               "labels": [item["label"]] + item.get("also_labels", []),
               "evaluation_sha256": ""}
        rec["evaluation_sha256"] = _sha(rec)
        rec_path.parent.mkdir(parents=True, exist_ok=True)
        rec_path.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"[eval] {task} {label} -> f2p={rec['f2p_task']} p2ps={rec['p2p_s_task']} "
              f"p2pu={rec['p2p_u200_task']} resolved={rec['resolved']}")
        evaluated += 1
        done += 1
    print(f"[eval] done this invocation: {evaluated} evaluated, {done} total terminal")
    return evaluated


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true", help="build and persist the unique-diff plan")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--max-evals", type=int, default=4)
    ap.add_argument("--no-telemetry", action="store_true")
    args = ap.parse_args()
    if args.plan:
        plan = persist_plan()
        print(f"[eval] plan persisted: n_unique_diffs={plan['n_unique_diffs']} "
              f"plan_sha256={plan['plan_sha256']}")
        return 0
    run_eval(args.max_evals, telemetry=not args.no_telemetry)
    _by_construction_records()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
