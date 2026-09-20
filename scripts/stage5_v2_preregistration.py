#!/usr/bin/env python3
"""STAGE5_V2_FINAL - build machine-readable preregistration (T3, ZERO API).

Assembles the frozen preregistration JSON: task counts, frozen V2 policy, final
DEV-refit model + threshold, artifact hashes, endpoint + success rule, budget,
sealed-guard statements. Deterministic; no Stage-5 outcome access.
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

OUT = _PROJECT_DIR / "research" / "stage5-v2-final"
REPORTS = _PROJECT_DIR / "reports"


def _file_sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _git(cmd: list[str]) -> str:
    r = subprocess.run(["git", *cmd], capture_output=True, text=True)
    return r.stdout.strip()


def _artifact_hashes() -> dict:
    files = [
        "research/contamination-bridge/qwen_embed/realization_A/full_file_scores.parquet",
        "research/memory-rescue-v2/fold_assignments_A.json",
        "research/memory-rescue-v2/deployment_candidate_rows.parquet" if Path(
            "research/memory-rescue-v2/deployment_candidate_rows.parquet").exists() else None,
        "research/stage5-v2-final/deployment_candidate_rows.parquet",
        "research/stage5-v2-final/deployment_artifact.json",
    ]
    out = {}
    for rel in files:
        if not rel:
            continue
        p = _PROJECT_DIR / rel
        out[rel] = _file_sha(p) if p.exists() else None
    return out


def main() -> int:
    artifact = json.loads((OUT / "deployment_artifact.json").read_text(encoding="utf-8"))
    header = _git(["rev-parse", "HEAD"])

    prereg = {
        "mission": "STAGE5_V2_FINAL",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "source_commit_at_build": header,
        "python_version": platform.python_version(),
        "sealed_population": {
            "djangocms_reserve_n": 59,
            "saleor_internal_test_n": 80,
            "total_n": 139,
            "saleor_reserve_extension": "NO",
            "note": "populations defined by the frozen split manifests "
                    "(research/transparency/v2_split_proposal.json RESERVE=59; "
                    "benchmark_data/real_commit_impact_saleor/split_freeze_saleor.json INTERNAL_TEST=80)",
        },
        "qwen_realization": "A",
        "v2_policy_frozen": {
            "candidate_universe": [
                "Sparse files",
                "Qwen dense top-20 NON-SPARSE",
                "parent-only structural memory top-10",
                "parent-only episodic memory top-10",
            ],
            "features": artifact["feature_names"],
            "forbidden": ["new features", "feature deletion", "graph features",
                          "class weighting", "issue text", "adaptive K", "repository ID"],
        },
        "final_dev_model": {
            "model": artifact["model"],
            "C": artifact["C"],
            "solver": artifact["solver"],
            "max_iter": artifact["max_iter"],
            "random_state": artifact["random_state"],
            "threshold": artifact["threshold"],
            "threshold_method": artifact["threshold_method"],
            "fold_seed": artifact["fold_seed"],
            "n_folds": artifact["n_folds"],
            "scaler_mean": artifact["scaler_mean"],
            "scaler_scale": artifact["scaler_scale"],
            "lr_coef": artifact["lr_coef"],
            "lr_intercept": artifact["lr_intercept"],
            "n_dev_rows": artifact["n_candidate_rows"],
            "n_dev_tasks": artifact["n_dev_tasks"],
            "config_sha256": artifact["config_sha256"],
        },
        "primary_endpoint": {
            "name": "repo-stratified pooled micro-F1 difference (V2 minus Sparse)",
            "resamples": 10000,
            "seed": 20260920,
            "ci": "95% [Q2.5, Q97.5]",
            "population": "djangocms RESERVE 59 + saleor INTERNAL_TEST 80",
        },
        "success_rule": {
            "A": "pooled stratified Delta F1 point > 0 AND 95% CI lower > 0",
            "B": "djangoCMS Stage-5 point Delta F1 > 0 AND Saleor Stage-5 point Delta F1 > 0",
            "per_repo_ci_gating": False,
        },
        "budget": {
            "hard_incremental_ceiling_usd": 1.00,
            "qwen_model_required": "qwen/qwen3-embedding-8b",
            "qwen_provider": "DeepInfra",
            "verify_live_price_before_paid_call": True,
            "stop_before_paid_calls_if_projected_over_ceiling": True,
            "no_fallback": True,
            "no_model_substitution": True,
            "no_extra_realization": True,
        },
        "sealed_data_guard": {
            "unseal_only_after_preregistration_tag": True,
            "tag": "stage5-v2-final-preregistered-2026-09-20",
            "one_shot_only": True,
            "no_second_chance": True,
        },
        "artifact_hashes": _artifact_hashes(),
        "labels": {
            "PASS": "STAGE5_V2_FINAL_CONFIRMATION_PASS + IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED",
            "FAIL": "STAGE5_V2_FINAL_CONFIRMATION_FAIL + IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED",
            "MIXED": "STAGE5_V2_FINAL_CONFIRMATION_MIXED + IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED",
        },
    }
    blob = json.dumps(prereg, indent=1, sort_keys=True)
    d = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    prereg["preregistration_sha256"] = d
    (REPORTS / "stage5_final_preregistration.json").write_text(
        json.dumps(prereg, indent=1, sort_keys=True), encoding="utf-8")
    print("stage5_final_preregistration.json written")
    print("preregistration_sha256:", d)
    print("threshold:", artifact["threshold"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
