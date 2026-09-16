#!/usr/bin/env python3
"""Omission-Risk Development Inference — 90-cell TRAIN/VALIDATION manifest.

Shared manifest builder for the frozen DEVELOPMENT-INFERENCE protocol
(docs/OMISSION_RISK_DEVELOPMENT_INFERENCE_PROTOCOL.md):

- splits: TRAIN (24) + VALIDATION (6) ONLY; HELD_OUT_TEST NEVER in this run
- arm: sparse_v2 ONLY
- repetitions: 3 (nested observations; task = statistical unit, N=30)
- total: 90 cells
- model: qwen/qwen3-coder (Qwen3-Coder-480B-A35B-Instruct)
- provider: deepinfra/turbo pinned through OpenRouter (fallback OFF)
- temperature 0, completion cap 16384, graph OFF
- protocol version: real-commit-p1-v1.0.0 (serialization policy = SPARSE)

Budget ceilings (frozen, HARD STOP): 600,000 total tokens AND $0.30.
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

DATASET_DIR = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_v1"
STUDY_DIR = _PROJECT_DIR / "research" / "omission-risk-feature-study-v1"

STUDY_ID = "omission-risk-development-inference-v1"
MANIFEST_NAME = "sparse_v2_trainval_manifest.json"
RUN_RECORDS_NAME = "sparse_v2_trainval_run_records.jsonl"
ARM = "sparse_v2"

MODEL = p1.P1_MODEL
MODEL_HUMAN = p1.P1_MODEL_HUMAN
PROVIDER_PINNED = "DeepInfra"
PROVIDER_TAG = p1.P1_PROVIDER_TAG
TEMPERATURE = p1.P1_TEMPERATURE
CAP = p1.P1_MAX_COMPLETION_TOKENS
REPETITIONS = p1.P1_REPETITIONS
PROTOCOL_VERSION = p1.P1_PROTOCOL_VERSION

# Frozen HARD STOP budget ceilings (docs/OMISSION_RISK_DEVELOPMENT_INFERENCE_PROTOCOL.md §4).
TOKEN_CEILING: int = 600_000
COST_CEILING_USD: float = 0.30
COST_MARGIN: float = 0.10

# P1 frozen pricing snapshot (research/real-commit-p1-01/endpoint_freeze.json).
P1_ENDPOINT_FREEZE = _PROJECT_DIR / "research" / "real-commit-p1-01" / "endpoint_freeze.json"
FALLBACK_PROMPT_PER_TOKEN_USD = 0.30 / 1_000_000
FALLBACK_COMPLETION_PER_TOKEN_USD = 1.00 / 1_000_000


def trainval_case_ids(dataset_dir: Path = DATASET_DIR) -> list[str]:
    """Sorted TRAIN + VALIDATION case ids (HELD_OUT_TEST NEVER included)."""
    split_freeze = json.loads(
        (Path(dataset_dir) / "split_freeze.json").read_text(encoding="utf-8")
    )
    ids: list[str] = []
    for split in ("TRAIN", "VALIDATION"):
        ids.extend(split_freeze["per_split"][split]["case_ids"])
    return sorted(ids)


def build_omission_risk_manifest(
    dataset_dir: Path = DATASET_DIR,
    *,
    repetitions: int = REPETITIONS,
) -> list[dict[str, Any]]:
    """Build the 90-cell manifest (30 tasks x 1 arm x 3 repetitions)."""
    rows: list[dict[str, Any]] = []
    for case_id in trainval_case_ids(dataset_dir):
        bundle = p1.load_case_public_bundle(dataset_dir, case_id)
        mapping = p1.build_p1_candidate_map(bundle.candidate_paths)
        for rep in range(1, repetitions + 1):
            rows.append(
                {
                    "run_id": f"omission-{case_id}-sparse_v2-r{rep}",
                    "case_id": case_id,
                    "repetition": rep,
                    "arm": ARM,
                    "serialization_policy": ARM,
                    "expected_model": MODEL,
                    "provider_tag": PROVIDER_TAG,
                    "temperature": TEMPERATURE,
                    "max_completion_tokens": CAP,
                    "candidate_count": len(mapping.id_to_path),
                    "candidate_map_sha256": mapping.sha256,
                    "public_bundle_sha256": bundle.public_bundle_sha256,
                    "protocol_version": PROTOCOL_VERSION,
                }
            )
    return rows


def run_records_path(study_dir: Path = STUDY_DIR) -> Path:
    return study_dir / RUN_RECORDS_NAME


def manifest_path(study_dir: Path = STUDY_DIR) -> Path:
    return study_dir / MANIFEST_NAME


def load_pricing() -> dict[str, Any]:
    """Frozen P1 pricing snapshot (DeepInfra $0.30/$1.00 per 1M through OpenRouter)."""
    if P1_ENDPOINT_FREEZE.is_file():
        data = json.loads(P1_ENDPOINT_FREEZE.read_text(encoding="utf-8"))
        prompt = float(data.get("input_price_per_1M_usd", 0.30)) / 1_000_000
        completion = float(data.get("output_price_per_1M_usd", 1.00)) / 1_000_000
        return {
            "prompt_per_token_usd": prompt,
            "completion_per_token_usd": completion,
            "source": str(P1_ENDPOINT_FREEZE),
            "input_price_per_1M_usd": float(data.get("input_price_per_1M_usd", 0.30)),
            "output_price_per_1M_usd": float(data.get("output_price_per_1M_usd", 1.00)),
        }
    return {
        "prompt_per_token_usd": FALLBACK_PROMPT_PER_TOKEN_USD,
        "completion_per_token_usd": FALLBACK_COMPLETION_PER_TOKEN_USD,
        "source": "frozen P1 live endpoint pricing (DeepInfra $0.30/$1.00 per 1M)",
        "input_price_per_1M_usd": 0.30,
        "output_price_per_1M_usd": 1.00,
    }


def render_sparse_prompt(case_id: str, dataset_dir: Path = DATASET_DIR) -> str:
    """Render the frozen P1 SPARSE prompt for one TRAIN/VALIDATION case."""
    bundle = p1.load_case_public_bundle(dataset_dir, case_id)
    mapping = p1.build_p1_candidate_map(bundle.candidate_paths)
    return str(p1.render_p1_sparse_prompt(case=bundle, mapping=mapping))


if __name__ == "__main__":
    cells = build_omission_risk_manifest()
    assert len(cells) == 90, f"expected 90 cells, got {len(cells)}"
    print(f"MANIFEST_CELLS={len(cells)}")
    print(f"RUN_IDS_UNIQUE={len({c['run_id'] for c in cells}) == 90}")
    print(f"ARMS={sorted({c['arm'] for c in cells})}")
    print(f"CASES={len({c['case_id'] for c in cells})}")
    print(f"REPS={sorted({c['repetition'] for c in cells})}")
    print(f"TOKEN_CEILING={TOKEN_CEILING}")
    print(f"COST_CEILING_USD={COST_CEILING_USD}")
