#!/usr/bin/env python3
"""POST-ICCI — Four-action FN breakdown on the existing P1 Full/Sparse raw outputs.

For each gold-positive file (proxy path) that is NOT in the binary REGENERATE
selection (i.e. every FN at the cell level), classify what action the model
produced for that candidate: PRESERVE / VALIDATE / HUMAN_REVIEW. REGENERATE
cannot appear here by construction (an FN is a missed gold-positive).

Source: the frozen P1 run records + persisted raw provider responses
(research/real-commit-p1-01/run_records.jsonl + runs/raw/*.txt). ZERO API.

Discipline:
- This is a SECONDARY DIAGNOSTIC ANALYSIS of existing frozen evidence, NOT a
  new confirmatory experiment and NOT a tuning step on the exposed
  HELD_OUT_TEST tasks.
- The full policy (id -> action) is re-decoded from the persisted raw response
  payload (decisions list) exactly as the P1 harness decoded it
  (decode_p1_full / decode_p1_sparse); omitted ids in Sparse-v2 decode to
  PRESERVE by the frozen representation-equivalence contract.
- Metrics are aggregated at the correct level: task-level micro over the 3
  nested repetitions (never treating repetitions as independent tasks).

Outputs:
- research/post-icci-zero-api-closure/four_action_fn_breakdown.json
- research/post-icci-zero-api-closure/four_action_fn_breakdown.csv
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PACKAGE_ROOT))
sys.path.insert(0, str(_PACKAGE_ROOT / "src"))

from benchmark.real_commits import p1_evaluation as p1  # noqa: E402

DATASET_DIR = _PACKAGE_ROOT / "benchmark_data" / "real_commit_impact_v1"
STUDY_DIR = _PACKAGE_ROOT / "research" / "real-commit-p1-01"
OUT_DIR = _PACKAGE_ROOT / "research" / "post-icci-zero-api-closure"
RECORDS = STUDY_DIR / "run_records.jsonl"
MANIFEST = STUDY_DIR / "manifest_60.json"
RAW_DIR = STUDY_DIR / "runs" / "raw"

ARMS = ("full_v2", "sparse_v2")
FN_ACTIONS = ("PRESERVE", "VALIDATE", "HUMAN_REVIEW")


def _candidate_count_by_run() -> dict[str, int]:
    manifest = _load_json(MANIFEST)
    return {cell["run_id"]: int(cell["candidate_count"]) for cell in manifest["cells"]}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _records() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line in RECORDS.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def _proxy(case_id: str) -> set[str]:
    p = DATASET_DIR / "scientific" / case_id / "hidden" / "observed_change_set_proxy.json"
    return set(_load_json(p)["paths"])


def _candidate_map(case_id: str) -> p1.P1CandidateMap:
    bundle = p1.load_case_public_bundle(DATASET_DIR, case_id)
    return p1.build_p1_candidate_map(bundle.candidate_paths)


def _raw_content(cell: dict[str, Any]) -> dict[str, Any] | None:
    raw_path = RAW_DIR / f"{cell['run_id']}.txt"
    if not raw_path.exists():
        return None
    raw = raw_path.read_text(encoding="utf-8")
    parsed = json.loads(raw)
    choices = parsed.get("choices") or []
    choice = choices[0] if choices else {}
    message = choice.get("message") or {}
    content = message.get("content") or ""
    if not content.strip():
        return None
    payload = json.loads(content)
    if not isinstance(payload, dict):
        return None
    return payload


def _decode_policy(cell: dict[str, Any], payload: dict[str, Any], cand_count: int) -> dict[int, str] | None:
    try:
        if cell["arm"] == "full_v2":
            policy = p1.decode_p1_full(payload, candidate_count=cand_count)
        else:
            policy = p1.decode_p1_sparse(payload, candidate_count=cand_count)
    except p1.P1DecodeError:
        return None
    return dict(policy)


def _path_actions(mapping: p1.P1CandidateMap, policy: dict[int, str]) -> dict[str, str]:
    return {mapping.path_for(i): action for i, action in policy.items()}


def cell_fn_breakdown(
    cell: dict[str, Any],
    mapping: p1.P1CandidateMap,
    proxy: set[str],
    payload: dict[str, Any],
    cand_count: int,
) -> dict[str, Any]:
    policy = _decode_policy(cell, payload, cand_count)
    if policy is None:
        return {
            "run_id": cell["run_id"],
            "case_id": cell["case_id"],
            "arm": cell["arm"],
            "repetition": cell["repetition"],
            "decoded": False,
            "fn_count": 0,
        }
    path_actions = _path_actions(mapping, policy)
    regenerate = {p for p, a in path_actions.items() if a == "REGENERATE"}
    fns = sorted(proxy - regenerate)
    breakdown = {action: 0 for action in FN_ACTIONS}
    fn_files: list[dict[str, str]] = []
    for path in fns:
        action = path_actions.get(path, "PRESERVE")
        breakdown[action] = breakdown.get(action, 0) + 1
        fn_files.append({"path": path, "action": action})
    return {
        "run_id": cell["run_id"],
        "case_id": cell["case_id"],
        "arm": cell["arm"],
        "repetition": cell["repetition"],
        "decoded": True,
        "fn_count": len(fns),
        "breakdown": breakdown,
        "fn_files": fn_files,
    }


def _merge_breakdown(cells: list[dict[str, Any]]) -> dict[str, int]:
    out = {action: 0 for action in FN_ACTIONS}
    for c in cells:
        if c.get("decoded"):
            for a in FN_ACTIONS:
                out[a] += c["breakdown"].get(a, 0)
    return out


def main() -> int:
    records = _records()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    by_task: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for cid in {r["case_id"] for r in records}:
        by_task.setdefault(cid, {}).update({arm: [] for arm in ARMS})

    cell_results: list[dict[str, Any]] = []
    decode_failures: list[str] = []
    cand_count_by_run = _candidate_count_by_run()
    for rec in records:
        if rec["arm"] not in ARMS:
            continue
        payload = _raw_content(rec)
        if payload is None:
            decode_failures.append(rec["run_id"])
            continue
        mapping = _candidate_map(rec["case_id"])
        proxy = _proxy(rec["case_id"])
        cand_count = cand_count_by_run.get(rec["run_id"])
        if cand_count is None:
            decode_failures.append(rec["run_id"])
            continue
        row = cell_fn_breakdown(rec, mapping, proxy, payload, cand_count)
        cell_results.append(row)
        by_task[rec["case_id"]][rec["arm"]].append(row)

    aggregate: dict[str, dict[str, int]] = {}
    for arm in ARMS:
        cells = [c for c in cell_results if c["arm"] == arm]
        aggregate[arm] = _merge_breakdown(cells)
    aggregate["both_arms"] = {
        a: aggregate["full_v2"].get(a, 0) + aggregate["sparse_v2"].get(a, 0)
        for a in FN_ACTIONS
    }

    task_level: dict[str, Any] = {}
    for cid in sorted(by_task):
        task_level[cid] = {}
        for arm in ARMS:
            task_level[cid][arm] = _merge_breakdown(by_task[cid][arm])

    # CSV: per task, per arm.
    csv_rows: list[dict[str, Any]] = []
    for cid in sorted(by_task):
        for arm in ARMS:
            row = {"case_id": cid, "arm": arm}
            row.update(task_level[cid][arm])
            csv_rows.append(row)

    result = {
        "classification": "SECONDARY DIAGNOSTIC ANALYSIS of existing frozen P1 evidence (ZERO API)",
        "note": "For each proxy path missed by binary REGENERATE selection, the action the model "
                "assigned (PRESERVE/VALIDATE/HUMAN_REVIEW). NOT a new confirmatory experiment; "
                "no tuning on the exposed HELD_OUT_TEST tasks.",
        "denominator": "30 cells per arm (10 tasks x 3 nested repetitions); task-level micro over "
                       "the 3 repetitions (repetitions are nested observations, not independent tasks).",
        "decoded_cells": sum(1 for c in cell_results if c.get("decoded")),
        "total_cells": len(records),
        "decode_failures": decode_failures,
        "aggregate": aggregate,
        "per_task": task_level,
    }
    json_path = OUT_DIR / "four_action_fn_breakdown.json"
    csv_path = OUT_DIR / "four_action_fn_breakdown.csv"
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["case_id", "arm", *FN_ACTIONS])
        writer.writeheader()
        writer.writerows(csv_rows)

    print("=== FOUR-ACTION FN BREAKDOWN (P1 Full/Sparse raw outputs; ZERO API) ===")
    print(f"decoded {result['decoded_cells']}/{result['total_cells']} cells; "
          f"decode_failures={decode_failures}")
    print("aggregate (proxy files missed by REGENERATE, by assigned action):")
    for k, v in aggregate.items():
        print(f"  {k:<10} {v}")
    print("per task (arm rows):")
    for cid in sorted(by_task):
        print(f"  {cid}")
        for arm in ARMS:
            print(f"    {arm:<9} {task_level[cid][arm]}")
    print(f"Wrote: {json_path}")
    print(f"Wrote: {csv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
