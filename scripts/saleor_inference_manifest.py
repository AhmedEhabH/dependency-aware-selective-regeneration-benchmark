#!/usr/bin/env python3
"""RealCommitImpactDataset-Saleor — Sparse development-inference manifest.

Authorized ceilings (continuation mission, Block C): NEW cells <= 450,
tokens <= 2.7M, cost <= $1.00. Runs Saleor DEV_TRAIN + DEV_VALIDATION
(150 cases x 3 reps = 450 cells) with the frozen Sparse-v2 config
(qwen/qwen3-coder @ deepinfra/turbo, temp 0, cap 16384, Graph OFF).
INTERNAL_TEST + RESERVE are NEVER called.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.real_commits import p1_evaluation as p1  # noqa: E402

DATASET_DIR = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor"
STUDY_DIR = _PROJECT_DIR / "research" / "saleor-sparse-inference"
DEV_MANIFEST = DATASET_DIR / "saleor_development_manifest.json"

TOKEN_CEILING = 2_700_000
COST_CEILING_USD = 1.00
CELL_CEILING = 450
REPS = 3


def saleor_development_case_ids() -> list[str]:
    dev = json.loads(DEV_MANIFEST.read_text(encoding="utf-8"))
    return sorted(r["case_id"] for r in dev["cases"])


def build_saleor_manifest(repetitions: int = REPS) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case_id in saleor_development_case_ids():
        bundle = p1.load_case_public_bundle(DATASET_DIR, case_id)
        mapping = p1.build_p1_candidate_map(bundle.candidate_paths)
        for rep in range(1, repetitions + 1):
            rows.append(
                {
                    "run_id": f"saleor-{case_id}-sparse_v2-r{rep}",
                    "case_id": case_id,
                    "repetition": rep,
                    "arm": "sparse_v2",
                    "serialization_policy": "sparse_v2",
                    "expected_model": p1.P1_MODEL,
                    "provider_tag": p1.P1_PROVIDER_TAG,
                    "temperature": p1.P1_TEMPERATURE,
                    "max_completion_tokens": p1.P1_MAX_COMPLETION_TOKENS,
                    "candidate_count": len(mapping.id_to_path),
                    "candidate_map_sha256": mapping.sha256,
                    "public_bundle_sha256": bundle.public_bundle_sha256,
                    "protocol_version": p1.P1_PROTOCOL_VERSION,
                }
            )
    return rows


if __name__ == "__main__":
    cells = build_saleor_manifest()
    print("saleor_cells", len(cells))
    print("saleor_cases", len(saleor_development_case_ids()))
    print("within_cell_ceiling", len(cells) <= CELL_CEILING)
    print("arms", sorted({c["arm"] for c in cells}))
    # also verify manifest hashes for the freeze
    print("dev_manifest_sha", json.loads(DEV_MANIFEST.read_text(encoding="utf-8")).get("canonical_manifest_sha256", "")[:16])
