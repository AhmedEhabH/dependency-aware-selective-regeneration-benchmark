"""Protocol-A output-equivalence regression (ZERO API, git cache required).

Reproduces the frozen Protocol-A cheap-baseline outputs THROUGH the harness
compatibility layer and asserts byte-for-byte scientific equivalence against
the frozen persisted evidence (``research/cheap-baselines-v1/*.json``).

The test is skipped when the frozen git cache is unavailable (same policy as
gate 5 of the cheap-baselines block). Wall-clock timing fields are excluded
(non-deterministic by nature).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from benchmark.harness import protocol_a

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
DATASET_DIR = PROJECT_DIR / "benchmark_data" / "real_commit_impact_v1"
CACHE_DIR = PROJECT_DIR / "dist" / "real-commit-cache" / "djangocms"
FROZEN_DIR = PROJECT_DIR / "research" / "cheap-baselines-v1"


def _require_git_cache() -> None:
    if not CACHE_DIR.is_dir():
        pytest.skip(f"git cache not present: {CACHE_DIR}")


@pytest.fixture(scope="module")
def harness_output() -> dict:
    _require_git_cache()
    return protocol_a.run_protocol_a_via_harness(
        dataset_dir=DATASET_DIR, cache_dir=CACHE_DIR, case_slice=(0, 2)
    )


def test_scientific_equivalence_with_frozen_raw(harness_output: dict) -> None:
    errors = protocol_a.compare_to_frozen(
        harness_output, FROZEN_DIR / "raw_predictions_v1.json"
    )
    assert errors == [], "harness output diverged from frozen evidence:\n" + "\n".join(
        errors[:20]
    )


def test_per_task_matches_frozen(harness_output: dict) -> None:
    frozen_per = json.loads(
        (FROZEN_DIR / "per_task_metrics_v1.json").read_text(encoding="utf-8")
    )
    per_task = harness_output["per_task"]
    for cid, methods in per_task.items():
        frozen_cid = frozen_per[cid]
        for baseline, k_map in methods.items():
            for k, row in k_map.items():
                frozen_row = frozen_cid[baseline][k]
                for field in (
                    "tp", "fp", "fn", "precision", "recall", "f1", "fnr",
                    "selected_count", "proxy_count",
                ):
                    assert row[field] == frozen_row[field], (
                        f"{cid} {baseline} k={k} {field}: "
                        f"frozen={frozen_row[field]!r} harness={row[field]!r}"
                    )


def test_harness_output_shape(harness_output: dict) -> None:
    assert harness_output["corpus_mode"] == "parent_commit"
    assert len(harness_output["cases"]) == 2
    for case in harness_output["cases"]:
        assert len(case["results"]) == 5 * 4  # 5 methods x 4 K
        for row in case["results"]:
            assert row["baseline"] in (
                "random", "bm25", "path_token", "graph", "hybrid",
            )
            assert row["k"] in (1, 3, 5, 10)
            assert set(row["selected_paths"]) <= set(case["candidate_paths"])


def test_aggregate_view_matches_frozen_micro_for_compared_cases(
    harness_output: dict,
) -> None:
    """Aggregate micro for the compared cases must match a recomputation
    from the frozen per-task rows (same split-bucketing and denominator)."""
    frozen_per = json.loads(
        (FROZEN_DIR / "per_task_metrics_v1.json").read_text(encoding="utf-8")
    )
    split_by_case = {c["case_id"]: c["split"] for c in harness_output["cases"]}
    rows: list[dict] = []
    for cid, split in split_by_case.items():
        for baseline, k_map in frozen_per[cid].items():
            for k, m in k_map.items():
                rows.append(
                    {
                        "case_id": cid,
                        "split": split,
                        "baseline": baseline,
                        "k": int(k),
                        "tp": m["tp"],
                        "fp": m["fp"],
                        "fn": m["fn"],
                        "precision": m["precision"],
                        "recall": m["recall"],
                        "f1": m["f1"],
                        "fnr": m["fnr"],
                        "selected_count": m["selected_count"],
                        "proxy_count": m["proxy_count"],
                    }
                )
    from benchmark.harness import evaluator as h_eval

    for group_name in ("TRAIN", "VALIDATION"):
        harness_agg = harness_output["aggregate"][group_name]
        group = [r for r in rows if r["split"] == group_name]
        if not group:
            continue
        for baseline in ("random", "bm25", "path_token", "graph", "hybrid"):
            for k in (1, 3, 5, 10):
                krows = [r for r in group if r["baseline"] == baseline and r["k"] == k]
                micro = h_eval.aggregate_micro(krows)
                assert micro["f1"] == harness_agg[baseline][str(k)]["micro"]["f1"]
                assert micro["tp"] == harness_agg[baseline][str(k)]["micro"]["tp"]
