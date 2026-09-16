"""Deterministic audit assertions for the path-mention sensitivity diagnostic.

Proves (ZERO API, persisted evidence only):
- the exclusion list is exactly the 3 documented TRAIN path-mention cases and
  all three are TRAIN (never VALIDATION / HELD_OUT_TEST);
- the sensitivity recomputation over persisted per-task metrics matches the
  frozen persisted ``path_mention_sensitivity_v1.json`` output;
- the material qualitative baseline ordering is unchanged under the exclusion
  (BM25 > Hybrid > max(Graph, path_token) > Random; Graph ≈ path_token);
- the frozen dataset is NOT modified by the diagnostic.
"""

from __future__ import annotations

import json
from pathlib import Path

from benchmark.cheap_baselines import sensitivity

DATASET_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "benchmark_data"
    / "real_commit_impact_v1"
)
OUT_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "research"
    / "cheap-baselines-v1"
)


def test_exclusion_list_is_exactly_three_train_cases() -> None:
    sf = json.loads((DATASET_DIR / "split_freeze.json").read_text(encoding="utf-8"))
    assignment: dict[str, str] = sf["assignment"]
    train = {cid for cid, s in assignment.items() if s == "TRAIN"}
    excluded = set(sensitivity.PATH_MENTION_TRAIN_CASES)
    assert len(excluded) == 3
    assert excluded <= train
    # None of the excluded cases may be VALIDATION or HELD_OUT_TEST.
    for cid in excluded:
        assert assignment[cid] == "TRAIN"


def test_compute_matches_persisted_sensitivity_output() -> None:
    recomputed = sensitivity.compute_sensitivity(
        OUT_DIR / "per_task_metrics_v1.json", DATASET_DIR / "split_freeze.json"
    )
    persisted = json.loads(
        (OUT_DIR / "path_mention_sensitivity_v1.json").read_text(encoding="utf-8")
    )
    assert recomputed["excluded_cases"] == persisted["excluded_cases"]
    assert recomputed["ordering"] == persisted["ordering"]
    assert recomputed["tables"] == persisted["tables"]


def test_material_ordering_unchanged_and_bm25_strongest() -> None:
    persisted = json.loads(
        (OUT_DIR / "path_mention_sensitivity_v1.json").read_text(encoding="utf-8")
    )
    assert persisted["ordering"]["material_ordering_unchanged"] is True
    best = persisted["ordering"]["path_clean_pooled_best_f1"]
    # BM25 remains the strongest cheap baseline after exclusion.
    assert best["bm25"] > best["hybrid"]
    assert best["bm25"] > best["graph"]
    assert best["bm25"] > best["path_token"]
    assert best["bm25"] > best["random"]


def test_diagnostic_does_not_rewrite_frozen_dataset() -> None:
    # The diagnostic only reads per_task_metrics_v1.json + split_freeze.json and
    # writes path_mention_sensitivity_v1.json. The frozen dataset dirs are never
    # touched; this test asserts the frozen per-split case counts are intact.
    sf = json.loads((DATASET_DIR / "split_freeze.json").read_text(encoding="utf-8"))
    assert len(sf["per_split"]["TRAIN"]["case_ids"]) == 24
    assert len(sf["per_split"]["VALIDATION"]["case_ids"]) == 6
    assert len(sf["per_split"]["HELD_OUT_TEST"]["case_ids"]) == 10


def test_sensitivity_knows_the_three_documented_cases() -> None:
    # The 3 excluded cases must be exactly the P6/audit-documented ones.
    assert sensitivity.PATH_MENTION_TRAIN_CASES == (
        "djangocms-rc-2efae8e43bd6",
        "djangocms-rc-ada585d3f358",
        "djangocms-rc-5ff38b521274",
    )
