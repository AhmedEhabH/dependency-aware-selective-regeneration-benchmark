#!/usr/bin/env python3
"""Cheap non-LLM baseline runner (Protocol A) — CLI entry.

Usage:
    python scripts/run_cheap_baselines.py                # real run (git corpus)
    python scripts/run_cheap_baselines.py --metadata-only
    python scripts/run_cheap_baselines.py --output research/cheap-baselines-v1
    python scripts/run_cheap_baselines.py --dry-run      # 2 cases, metadata only

ZERO LLM calls. TRAIN + VALIDATION only. HELD_OUT_TEST refused fail-closed.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PACKAGE_ROOT))
sys.path.insert(0, str(_PACKAGE_ROOT / "src"))

from benchmark.cheap_baselines import evaluation  # noqa: E402
from benchmark.cheap_baselines.runner import (  # noqa: E402
    SPLITS_ALLOWED,
    build_config_files,
    run_baselines,
)

DATASET_DIR = _PACKAGE_ROOT / "benchmark_data" / "real_commit_impact_v1"
CACHE_DIR = _PACKAGE_ROOT / "dist" / "real-commit-cache" / "djangocms"
DEFAULT_OUTPUT = _PACKAGE_ROOT / "research" / "cheap-baselines-v1"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _persist(payload: dict, out_dir: Path, name: str) -> Path:
    path = out_dir / name
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DATASET_DIR)
    parser.add_argument("--cache-dir", type=Path, default=CACHE_DIR)
    parser.add_argument("--metadata-only", action="store_true", default=False)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dry-run", action="store_true", default=False)
    args = parser.parse_args()

    dataset_dir = args.dataset_dir.resolve()
    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        # Deterministic 2-case smoke: use metadata-only corpus (no git).
        cache_dir = None
    elif args.metadata_only:
        cache_dir = None
    else:
        cache_dir = args.cache_dir
        if not cache_dir.is_dir():
            print(f"ERROR: cache_dir not found: {cache_dir}")
            print("Run with --metadata-only to skip parent-content corpus.")
            return 2

    config = build_config_files(cache_dir)
    _persist(config, output_dir, "config_v1.json")

    print(f"PROTOCOL_VERSION={config['protocol_version']}")
    print(f"SPLITS={SPLITS_ALLOWED}")
    print(f"CORPUS_MODE={config['corpus_mode']}")
    print(f"OUTPUT={output_dir}")

    case_evals, manifest = run_baselines(dataset_dir=dataset_dir, cache_dir=cache_dir)
    manifest["ran_at_utc"] = _now_iso()
    _persist(manifest, output_dir, "manifest_v1.json")

    raw_payload = {
        "protocol_version": manifest["protocol_version"],
        "dataset_authority": "benchmark_data/real_commit_impact_v1",
        "reference": manifest["reference"],
        "predicted_positive": manifest["predicted_positive"],
        "cases": [c.to_json() for c in case_evals],
    }
    _persist(raw_payload, output_dir, "raw_predictions_v1.json")

    per_task: dict[str, dict[str, dict[str, dict]]] = {}
    for c in case_evals:
        per_task[c.case_id] = {}
        for row in c.to_json()["results"]:
            per_task[c.case_id].setdefault(row["baseline"], {})[row["k"]] = {
                k: row[k]
                for k in (
                    "tp", "fp", "fn", "precision", "recall", "f1", "fnr",
                    "selected_count", "proxy_count", "build_seconds", "query_seconds",
                    "seed_reason",
                )
            }
    _persist(per_task, output_dir, "per_task_metrics_v1.json")

    # Aggregate metric tables (aggregate_v1.json): per baseline x k, split by
    # TRAIN, VALIDATION, and TRAIN+VALIDATION (development evidence).
    task_rows: list[dict] = []
    for c in case_evals:
        for row in c.to_json()["results"]:
            row["case_id"] = c.case_id
            row["split"] = c.split
            task_rows.append(row)

    aggregate: dict[str, dict[str, dict[str, dict]]] = {}
    split_groups = {"TRAIN": [], "VALIDATION": [], "TRAIN_VALIDATION": []}
    for row in task_rows:
        if row["split"] == "TRAIN":
            split_groups["TRAIN"].append(row)
            split_groups["TRAIN_VALIDATION"].append(row)
        elif row["split"] == "VALIDATION":
            split_groups["VALIDATION"].append(row)
            split_groups["TRAIN_VALIDATION"].append(row)

    for group_name, rows in split_groups.items():
        aggregate[group_name] = {}
        for baseline in ("random", "bm25", "path_token", "graph", "hybrid"):
            aggregate[group_name][baseline] = {}
            for k in (1, 3, 5, 10):
                krows = [r for r in rows if r["baseline"] == baseline and r["k"] == k]
                aggregate[group_name][baseline][str(k)] = {
                    "micro": evaluation.aggregate_micro_metrics(krows),
                    "macro": evaluation.aggregate_macro_metrics(krows),
                }
    aggregate_payload = {
        "protocol_version": manifest["protocol_version"],
        "confidence_label": "DEVELOPMENT EVIDENCE (TRAIN+VALIDATION); not confirmatory",
        "aggregates": aggregate,
    }
    _persist(aggregate_payload, output_dir, "aggregate_v1.json")

    # Efficiency summary.
    eff: dict[str, dict] = {}
    for baseline in ("random", "bm25", "path_token", "graph", "hybrid"):
        rows = [r for r in task_rows if r["baseline"] == baseline]
        build = [float(r["build_seconds"]) for r in rows]
        query = [float(r["query_seconds"]) for r in rows]
        corpus_build = [float(r.get("corpus_build_seconds", 0.0)) for r in rows]
        eff[baseline] = {
            "cases": len(rows),
            "total_wallclock_seconds": round(
                sum(build) + sum(query) + sum(corpus_build), 6
            ),
            "index_build_total_seconds": round(sum(build), 6),
            "corpus_build_total_seconds": round(sum(corpus_build), 6),
            "query_total_seconds": round(sum(query), 6),
            "llm_calls": 0,
            "llm_tokens": 0,
        }
    _persist({"efficiency_v1": eff}, output_dir, "efficiency_v1.json")

    print("\nDONE: raw_predictions_v1.json / per_task_metrics_v1.json / aggregate_v1.json / efficiency_v1.json")
    print(f"CASES={len(case_evals)} ZERO_LLM=TRUE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
