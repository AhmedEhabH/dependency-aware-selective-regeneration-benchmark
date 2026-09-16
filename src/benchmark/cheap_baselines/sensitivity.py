"""Path-mention sensitivity diagnostic for cheap-baselines-v1 (ZERO API).

Deterministic recomputation over PERSISTED evidence only
(``research/cheap-baselines-v1/per_task_metrics_v1.json``). No dataset is
modified, no ranking is rerun, no API is called.

The 3 TRAIN cases whose full visible commit-message intent mentions a changed
path are excluded as a task-level localization-shortcut sensitivity check.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import evaluation

PATH_MENTION_TRAIN_CASES: tuple[str, ...] = (
    "djangocms-rc-2efae8e43bd6",
    "djangocms-rc-ada585d3f358",
    "djangocms-rc-5ff38b521274",
)

BASELINES: tuple[str, ...] = ("random", "bm25", "path_token", "graph", "hybrid")
K_VALUES: tuple[int, ...] = (1, 3, 5, 10)


def load_rows(per_task_path: Path, split_freeze_path: Path) -> list[dict[str, Any]]:
    """Flatten persisted per-task metrics into row records with split labels."""
    per = json.loads(per_task_path.read_text(encoding="utf-8"))
    sf = json.loads(split_freeze_path.read_text(encoding="utf-8"))
    assignment: dict[str, str] = sf["assignment"]
    rows: list[dict[str, Any]] = []
    for cid, baseline_map in per.items():
        split = assignment[cid]
        if split == "HELD_OUT_TEST":
            continue
        for baseline, k_map in baseline_map.items():
            for k, metrics in k_map.items():
                row = dict(metrics)
                row["case_id"] = cid
                row["split"] = split
                row["baseline"] = baseline
                row["k"] = int(k)
                rows.append(row)
    return rows


def select_rows(
    rows: list[dict[str, Any]],
    *,
    include_validation: bool,
    exclude: frozenset[str],
) -> list[dict[str, Any]]:
    return [
        r
        for r in rows
        if (include_validation or r["split"] != "VALIDATION") and r["case_id"] not in exclude
    ]


def micro_table(rows: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    """Baseline x K -> pooled micro metrics."""
    table: dict[str, dict[str, dict[str, Any]]] = {}
    for baseline in BASELINES:
        table[baseline] = {}
        for k in K_VALUES:
            group = [r for r in rows if r["baseline"] == baseline and r["k"] == k]
            table[baseline][str(k)] = evaluation.aggregate_micro_metrics(group)
    return table


def best_f1(table: dict[str, dict[str, dict[str, Any]]], baseline: str) -> float:
    return float(max(table[baseline][str(k)]["f1"] for k in K_VALUES))


def material_ordering_unchanged(
    pooled_clean: dict[str, dict[str, dict[str, Any]]],
    pooled_orig: dict[str, dict[str, dict[str, Any]]],
) -> bool:
    """Material qualitative ordering is preserved under the exclusion.

    Asserted claims (pooled micro, best-F1 across K):
    1. BM25 > Hybrid > max(Graph, path_token) > Random.
    2. Graph and path_token remain a tied pair (|ΔF1| < 0.01 at every K).
    """
    for tbl in (pooled_orig, pooled_clean):
        bm = best_f1(tbl, "bm25")
        hy = best_f1(tbl, "hybrid")
        gr = best_f1(tbl, "graph")
        pt = best_f1(tbl, "path_token")
        rn = best_f1(tbl, "random")
        if not (bm > hy > max(gr, pt) > rn):
            return False
        for k in K_VALUES:
            if abs(tbl["graph"][str(k)]["f1"] - tbl["path_token"][str(k)]["f1"]) >= 0.01:
                return False
    return True


def compute_sensitivity(
    per_task_path: Path,
    split_freeze_path: Path,
) -> dict[str, Any]:
    """Compute original vs path-clean TRAIN and pooled tables (deterministic)."""
    rows = load_rows(per_task_path, split_freeze_path)
    exclude = frozenset(PATH_MENTION_TRAIN_CASES)

    sf = json.loads(split_freeze_path.read_text(encoding="utf-8"))
    assignment: dict[str, str] = sf["assignment"]
    train_ids = {cid for cid, s in assignment.items() if s == "TRAIN"}
    assert set(PATH_MENTION_TRAIN_CASES) <= train_ids
    assert len(set(PATH_MENTION_TRAIN_CASES)) == 3

    original_train = select_rows(rows, include_validation=False, exclude=frozenset())
    clean_train = select_rows(rows, include_validation=False, exclude=exclude)
    original_pooled = select_rows(rows, include_validation=True, exclude=frozenset())
    clean_pooled = select_rows(rows, include_validation=True, exclude=exclude)

    t_orig_train = micro_table(original_train)
    t_clean_train = micro_table(clean_train)
    t_orig_pooled = micro_table(original_pooled)
    t_clean_pooled = micro_table(clean_pooled)

    return {
        "excluded_cases": list(PATH_MENTION_TRAIN_CASES),
        "tables": {
            "original_train": t_orig_train,
            "path_clean_train": t_clean_train,
            "original_pooled": t_orig_pooled,
            "path_clean_pooled": t_clean_pooled,
        },
        "ordering": {
            "material_ordering_unchanged": material_ordering_unchanged(
                t_clean_pooled, t_orig_pooled
            ),
            "original_pooled_best_f1": {
                b: best_f1(t_orig_pooled, b) for b in BASELINES
            },
            "path_clean_pooled_best_f1": {
                b: best_f1(t_clean_pooled, b) for b in BASELINES
            },
        },
    }
