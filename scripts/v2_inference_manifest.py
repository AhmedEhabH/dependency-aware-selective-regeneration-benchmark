#!/usr/bin/env python3
"""RealCommitImpactDataset-v2 — Sparse development-inference manifest + gates.

Tier T3. LIVE API only after: V2 dev case IDs frozen (built bundles),
split frozen, six gates PASS, leakage audit PASS, budget documented.

Authorized ceilings (mission C3): NEW cells <= 450, tokens <= 2.5M, cost <= $1.00.
This runs DEV_TRAIN + DEV_VALIDATION (150 cases x 3 reps = 450 cells).
INTERNAL_TEST + RESERVE are NEVER called. LEGACY_EXPOSED_V1 never called.
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

DATASET_DIR = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_v2"
STUDY_DIR = _PROJECT_DIR / "research" / "omission-risk-feature-study-v1" / "v2_trainval"
SPLIT = _PROJECT_DIR / "research" / "transparency" / "v2_split_proposal.json"
DEV_MANIFEST = DATASET_DIR / "v2_development_manifest.json"

TOKEN_CEILING = 2_500_000
COST_CEILING_USD = 1.00
CELL_CEILING = 450
REPS = 3


def v2_development_case_ids() -> list[str]:
    dev = json.loads(DEV_MANIFEST.read_text(encoding="utf-8"))
    return sorted(r["case_id"] for r in dev["cases"])


def build_v2_manifest(repetitions: int = REPS) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case_id in v2_development_case_ids():
        bundle = p1.load_case_public_bundle(DATASET_DIR, case_id)
        mapping = p1.build_p1_candidate_map(bundle.candidate_paths)
        for rep in range(1, repetitions + 1):
            rows.append(
                {
                    "run_id": f"v2-{case_id}-sparse_v2-r{rep}",
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
    cells = build_v2_manifest()
    print("v2_cells", len(cells))
    print("v2_cases", len(v2_development_case_ids()))
    print("within_cell_ceiling", len(cells) <= CELL_CEILING)
    print("arms", sorted({c["arm"] for c in cells}))
