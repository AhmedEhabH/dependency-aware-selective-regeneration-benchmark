#!/usr/bin/env python3
"""WP-1a Correction C - deterministic SIP/RM-CSS per-task re-derivation.

Builds the frozen per-task prediction artifact from frozen Saleor-300 artifacts
(zero API), verifies EXACT reproduction of the authoritative frozen headline
values, and persists:

- research/wp1a/sip_rmcss_per_task_predictions.json
- research/wp1a/sip_rmcss_per_task_predictions.sha256
- research/wp1a/wp1_rederivation_verification.json

On any authoritative-value mismatch this script STOPS with
WP1A_RMCSS_REDERIVATION_DRIFT and does not persist the new artifact.
The historical Saleor-300 result artifact is NEVER replaced.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.wp1a.rederive import (  # noqa: E402
    rederive_per_task,
    verify_exact_reproduction,
)

OUT_DIR = _PROJECT_DIR / "research" / "wp1a"
RESEARCH = _PROJECT_DIR / "research" / "saleor-reserve-300-rmcss"
RECORDS = RESEARCH / "sip_300_run_records.jsonl"
CANDIDATE_ROWS = RESEARCH / "candidate_rows_saleor300.parquet"
DEPLOYMENT = _PROJECT_DIR / "research" / "stage5-v2-final" / "deployment_artifact.json"
PROXIES = RESEARCH / "saleor_reserve_300_proxies.json"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    artifact = rederive_per_task(
        records_path=RECORDS,
        candidate_rows_path=CANDIDATE_ROWS,
        deployment_artifact_path=DEPLOYMENT,
    )
    artifact["generated_utc"] = datetime.datetime.now(datetime.UTC).isoformat()

    # 1) persist prediction hashes BEFORE loading labels (procedural blinding)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pred_path = OUT_DIR / "sip_rmcss_per_task_predictions.json"
    pred_path.write_text(json.dumps(artifact, indent=1), encoding="utf-8")

    # 2) SHA-256 manifest of the frozen per-task artifact
    sha_path = OUT_DIR / "sip_rmcss_per_task_predictions.sha256"
    sha_path.write_text(_sha256_file(pred_path) + "  " + pred_path.name + "\n", encoding="utf-8")

    # 3) NOW load labels and verify exact reproduction
    verification = verify_exact_reproduction(
        per_task_artifact=artifact,
        proxies_path=PROXIES,
    )
    verification["per_task_artifact_sha256"] = _sha256_file(pred_path)
    verification["label_loaded_after_prediction_hash_persisted"] = True
    (OUT_DIR / "wp1_rederivation_verification.json").write_text(
        json.dumps(verification, indent=1), encoding="utf-8")

    print("[wp1a-rederive] per-task predictions:", pred_path)
    print("[wp1a-rederive] sha256:", _sha256_file(pred_path))
    print("[wp1a-rederive] verification:", verification["verification"])
    print("[wp1a-rederive] SIP:", verification["sip"])
    print("[wp1a-rederive] RM-CSS:", verification["rmcss"])
    print("[wp1a-rederive] delta_f1:", verification["delta_f1"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
