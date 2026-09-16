#!/usr/bin/env python3
"""Path-mention sensitivity diagnostic for cheap-baselines-v1 (ZERO API).

A deterministic, zero-API recomputation over the PERSISTED evidence in
``research/cheap-baselines-v1/per_task_metrics_v1.json``.

Context: 3 TRAIN cases carry a full visible commit-message intent that
mentions a changed path (``djangocms-rc-2efae8e43bd6``,
``djangocms-rc-ada585d3f358``, ``djangocms-rc-5ff38b521274``). This is a
frozen-corpus property shared identically by the P1 LLM planner and the cheap
baselines (same public query), NOT hidden-gold pipeline leakage. It is,
however, a task-level localization shortcut for those 3 cases, so we report a
sensitivity diagnostic that excludes them.

Outputs:
- prints original vs path-clean TRAIN and pooled TRAIN+VALIDATION micro tables
- asserts the material qualitative baseline ordering is unchanged under the
  exclusion
- persists ``research/cheap-baselines-v1/path_mention_sensitivity_v1.json``

The frozen dataset is NOT modified.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PACKAGE_ROOT))
sys.path.insert(0, str(_PACKAGE_ROOT / "src"))

from benchmark.cheap_baselines import sensitivity  # noqa: E402

OUT_DIR = _PACKAGE_ROOT / "research" / "cheap-baselines-v1"
DATASET_DIR = _PACKAGE_ROOT / "benchmark_data" / "real_commit_impact_v1"


def _fmt(m: dict) -> str:
    return (
        f"P={m['precision']:.4f} R={m['recall']:.4f} F1={m['f1']:.4f} "
        f"FNR={m['fnr']:.4f} TP={m['tp']} FP={m['fp']} FN={m['fn']}"
    )


def _print_table(title: str, rows: list[dict], table: dict) -> None:
    print(f"\n{title}  (n_cases={len({r['case_id'] for r in rows})})")
    for baseline in sensitivity.BASELINES:
        for k in sensitivity.K_VALUES:
            print(f"  {baseline:<10} K={k:<2} {_fmt(table[baseline][str(k)])}")


def main() -> int:
    result = sensitivity.compute_sensitivity(
        OUT_DIR / "per_task_metrics_v1.json",
        DATASET_DIR / "split_freeze.json",
    )
    print("PATH-MENTION SENSITIVITY DIAGNOSTIC (Protocol A, ZERO API)")
    print(f"excluded TRAIN cases: {result['excluded_cases']}")

    rows = sensitivity.load_rows(
        OUT_DIR / "per_task_metrics_v1.json", DATASET_DIR / "split_freeze.json"
    )
    excl = frozenset(sensitivity.PATH_MENTION_TRAIN_CASES)
    original_train = sensitivity.select_rows(
        rows, include_validation=False, exclude=frozenset()
    )
    clean_train = sensitivity.select_rows(rows, include_validation=False, exclude=excl)
    original_pooled = sensitivity.select_rows(
        rows, include_validation=True, exclude=frozenset()
    )
    clean_pooled = sensitivity.select_rows(rows, include_validation=True, exclude=excl)

    _print_table("ORIGINAL TRAIN (n=24)", original_train, result["tables"]["original_train"])
    _print_table("PATH-CLEAN TRAIN (n=21)", clean_train, result["tables"]["path_clean_train"])
    _print_table(
        "ORIGINAL POOLED TRAIN+VALIDATION (n=30)",
        original_pooled,
        result["tables"]["original_pooled"],
    )
    _print_table(
        "PATH-CLEAN POOLED (n=27)",
        clean_pooled,
        result["tables"]["path_clean_pooled"],
    )

    unchanged = result["ordering"]["material_ordering_unchanged"]
    print(f"\nMATERIAL QUALITATIVE BASELINE ORDERING UNCHANGED: {unchanged}")

    payload = {
        "protocol_version": "cheap-nonllm-baselines-v1",
        "kind": "SENSITIVITY DIAGNOSTIC (not a new experiment; persisted evidence only)",
        "excluded_cases": result["excluded_cases"],
        "exclusion_reason": (
            "3 TRAIN cases whose full visible commit-message intent mentions a changed path; "
            "frozen-corpus property shared with the P1 planner (same public query); "
            "not hidden-gold pipeline leakage; excluded here only as a task-level "
            "localization-shortcut sensitivity check"
        ),
        "tables": result["tables"],
        "ordering": result["ordering"],
    }
    out_path = OUT_DIR / "path_mention_sensitivity_v1.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\npersisted={out_path}")
    return 0 if unchanged else 1


if __name__ == "__main__":
    raise SystemExit(main())
