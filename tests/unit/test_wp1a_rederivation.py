"""WP-1a Correction C - exact 300-task re-derivation tests (AC-1A.3)."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))
if str(PROJECT_DIR / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR / "src"))

from benchmark.wp1a.rederive import (  # noqa: E402
    AUTHORITATIVE,
    derive_rmcss_sets,
    load_sip_sets,
    rederive_per_task,
    verify_exact_reproduction,
)

RESEARCH = PROJECT_DIR / "research" / "saleor-reserve-300-rmcss"
WP1A = PROJECT_DIR / "research" / "wp1a"
DEPLOYMENT = PROJECT_DIR / "research" / "stage5-v2-final" / "deployment_artifact.json"


def test_sip_sets_loaded_from_records() -> None:
    sets = load_sip_sets(RESEARCH / "sip_300_run_records.jsonl")
    assert len(sets) == 300
    # transport-failed -> fail-closed EMPTY
    assert sets["saleor-rc-cff241afc8d7"] == set()
    assert sets["saleor-rc-d24336188b88"] == set()


def test_rmcss_sets_label_free_derivation() -> None:
    artifact = json.loads(DEPLOYMENT.read_text(encoding="utf-8"))
    predicted, hashes = derive_rmcss_sets(
        RESEARCH / "candidate_rows_saleor300.parquet", artifact)
    assert len(predicted) == 300
    assert len(hashes) == 300


def test_rederive_per_task_300() -> None:
    artifact = rederive_per_task(
        records_path=RESEARCH / "sip_300_run_records.jsonl",
        candidate_rows_path=RESEARCH / "candidate_rows_saleor300.parquet",
        deployment_artifact_path=DEPLOYMENT,
    )
    assert artifact["n_tasks"] == 300
    assert len(artifact["per_task"]) == 300


def test_exact_reproduction() -> None:
    artifact = rederive_per_task(
        records_path=RESEARCH / "sip_300_run_records.jsonl",
        candidate_rows_path=RESEARCH / "candidate_rows_saleor300.parquet",
        deployment_artifact_path=DEPLOYMENT,
    )
    v = verify_exact_reproduction(
        per_task_artifact=artifact,
        proxies_path=RESEARCH / "saleor_reserve_300_proxies.json",
    )
    assert v["verification"] == "EXACT_REPRODUCTION"
    assert v["sip"]["tp"] == AUTHORITATIVE["sip"]["tp"]
    assert v["sip"]["fp"] == AUTHORITATIVE["sip"]["fp"]
    assert v["sip"]["fn"] == AUTHORITATIVE["sip"]["fn"]
    assert abs(v["sip"]["f1"] - AUTHORITATIVE["sip"]["f1"]) < 1e-9
    assert v["rmcss"]["tp"] == AUTHORITATIVE["rmcss"]["tp"]
    assert v["rmcss"]["fp"] == AUTHORITATIVE["rmcss"]["fp"]
    assert v["rmcss"]["fn"] == AUTHORITATIVE["rmcss"]["fn"]
    assert abs(v["rmcss"]["f1"] - AUTHORITATIVE["rmcss"]["f1"]) < 1e-9
    assert abs(v["delta_f1"] - AUTHORITATIVE["delta_f1"]) < 1e-9


def test_persisted_verification_matches() -> None:
    v = json.loads((WP1A / "wp1_rederivation_verification.json").read_text(encoding="utf-8"))
    assert v["verification"] == "EXACT_REPRODUCTION"
    assert abs(v["sip"]["f1"] - 0.26474622770919065) < 1e-12
    assert abs(v["rmcss"]["f1"] - 0.35687263556116017) < 1e-12
    assert abs(v["delta_f1"] - 0.09212640785196952) < 1e-12


def test_sha256_manifest_matches_artifact() -> None:
    artifact_path = WP1A / "sip_rmcss_per_task_predictions.json"
    manifest = (WP1A / "sip_rmcss_per_task_predictions.sha256").read_text(encoding="utf-8")
    digest = manifest.split()[0]
    assert digest == hashlib.sha256(artifact_path.read_bytes()).hexdigest()
