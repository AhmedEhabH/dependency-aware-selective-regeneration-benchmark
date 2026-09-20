# ruff: noqa: N812
"""SALEOR_RESERVE_300_RMCSS - targeted validation tests (T3).

Covers: sampling determinism; label-free exclusion counts; cache coverage;
NaN behavior / no finite sentinel; sentinel hard guard; feature schema;
primary + transfer model hashes; bootstrap unchanged; metric consistency;
independent audits pass.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))
if str(PROJECT_DIR / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR / "src"))
if str(PROJECT_DIR / "scripts") not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR / "scripts"))

from benchmark.calibrated.policy import BOOTSTRAP_SEED, N_BOOTSTRAP  # noqa: E402
from benchmark.memory_rescue import candidates as C  # noqa: E402

OUT = PROJECT_DIR / "research" / "saleor-reserve-300-rmcss"
REPORTS = PROJECT_DIR / "reports"
FROZEN_SHA = "8925d29a8e065bc864cd16e755ac0e896c7675b4a12f68fb66c35e5bd644ea95"
TRANSFER_SHA = "efb38c079a6ea15e6ada4ecdb65810f4afd1f5614ad28274f9516d2112740a67"
SAMPLE_SHA = "445b5e9d0aeeab9551e8feeb3e59e6b5bcfee793f029810a6efe0cbc8f126447"


class TestSamplingDeterminism:
    def test_sample_manifest_recompute(self) -> None:
        m = json.loads((OUT / "saleor_reserve_300_sample.json").read_text(encoding="utf-8"))
        ids = m["selected_ids"]
        ids_text = "\n".join(ids) + "\n"
        sha = hashlib.sha256(ids_text.encode("utf-8")).hexdigest()
        assert sha == SAMPLE_SHA
        assert len(ids) == 300 and len(set(ids)) == 300
        assert m["sampling_seed"] == 20260920

    def test_selected_are_reserve(self) -> None:
        split = json.loads((PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor"
                            / "split_freeze_saleor.json").read_text(encoding="utf-8"))
        m = json.loads((OUT / "saleor_reserve_300_sample.json").read_text(encoding="utf-8"))
        assert all(split["assignment"][c] == "RESERVE" for c in m["selected_ids"])


class TestLabelFreeExclusion:
    def test_preflight_300_ok(self) -> None:
        pre = json.loads((OUT / "saleor_reserve_300_preflight.json").read_text(encoding="utf-8"))
        assert pre["preflighted_ok"] == 300 and pre["excluded"] == 0

    def test_public_bundles_label_free(self) -> None:
        sample = json.loads((OUT / "saleor_reserve_300_sample.json").read_text(encoding="utf-8"))["selected_ids"]
        sc = PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor" / "scientific"
        for cid in sample[:10]:
            assert not (sc / cid / "hidden").exists()
            mani = json.loads((sc / cid / "case_manifest.json").read_text(encoding="utf-8"))
            assert "change_statuses" not in mani.get("record", {})


class TestEmbeddingCoverageAndNaN:
    def test_no_finite_sentinels(self) -> None:
        ffs = pd.read_parquet(OUT / "full_file_scores_saleor300.parquet")
        assert int((ffs["dense_file_score"] == -1e9).sum()) == 0
        assert int((ffs["dense_file_score"] == -1e6).sum()) == 0

    def test_nan_rate_within_tolerance(self) -> None:
        ffs = pd.read_parquet(OUT / "full_file_scores_saleor300.parquet")
        rate = float(ffs["dense_file_score"].isna().mean())
        assert abs(rate - 0.0835) <= 0.03

    def test_finite_range(self) -> None:
        ffs = pd.read_parquet(OUT / "full_file_scores_saleor300.parquet")
        fin = ffs.loc[np.isfinite(ffs["dense_file_score"].to_numpy(dtype=np.float64)), "dense_file_score"]
        assert float(fin.min()) >= -1.5 and float(fin.max()) <= 1.5

    def test_sentinel_guard(self) -> None:
        with pytest.raises(ValueError):
            C.assert_finite_dense_score_bounds(pd.DataFrame({"dense_file_score": [0.5, -1e9]}))


class TestFeatureSchemaAndHashes:
    def test_feature_schema(self) -> None:
        cand = pd.read_parquet(OUT / "candidate_rows_saleor300.parquet")
        art = json.loads((PROJECT_DIR / "research" / "stage5-v2-final"
                          / "deployment_artifact.json").read_text(encoding="utf-8"))
        assert list(C.FEATURE_NAMES) == art["feature_names"]
        assert len(art["feature_names"]) == 11
        assert set(cand.columns) >= set(art["feature_names"])

    def test_primary_model_hash(self) -> None:
        art = json.loads((PROJECT_DIR / "research" / "stage5-v2-final"
                          / "deployment_artifact.json").read_text(encoding="utf-8"))
        assert art["config_sha256"] == FROZEN_SHA
        assert abs(float(art["threshold"]) - 0.20) < 1e-12
        assert art["realization"] == "A"

    def test_transfer_model_hash(self) -> None:
        t = json.loads((OUT / "django_only_rmcss_transfer_model.json").read_text(encoding="utf-8"))
        assert t["artifact_sha256"] == TRANSFER_SHA
        assert abs(float(t["threshold"]) - 0.20) < 1e-12
        assert t["model_id"] == "DJANGO_ONLY_RMCSS_TRANSFER_MODEL"
        assert t["n_train_tasks"] == 174


class TestBootstrapAndMetrics:
    def test_bootstrap_unchanged(self) -> None:
        assert N_BOOTSTRAP == 10_000 and BOOTSTRAP_SEED == 20260920

    def test_result_consistency(self) -> None:
        r = json.loads((REPORTS / "saleor_reserve_300_rmcss_result.json").read_text(encoding="utf-8"))
        assert r["n_tasks"] == 300
        assert r["primary"]["verdict"] == "SALEOR_RESERVE_300_RMCSS_PASS"
        assert r["secondary_transfer"]["verdict"] == "SECONDARY_CROSS_REPO_TRANSFER_PASS"
        assert r["primary"]["ci"]["f1"]["ci95_lower"] > 0
        assert r["secondary_transfer"]["ci"]["f1"]["ci95_lower"] > 0

    def test_sip_categories(self) -> None:
        recs = [json.loads(ln) for ln in (OUT / "sip_300_run_records.jsonl")
                    .read_text(encoding="utf-8").splitlines() if ln.strip()]
        from collections import Counter
        cats = Counter(r["terminal_status"] for r in recs)
        assert len(recs) == 300
        assert cats["succeeded"] == 228 and cats["succeeded_empty"] == 70 and cats["transport_failed"] == 2


class TestAudits:
    def test_parity_gate_pass(self) -> None:
        g = json.loads((REPORTS / "saleor_reserve_300_parity_gate.json").read_text(encoding="utf-8"))
        assert g["pass"] == g["total"] == 10

    def test_parity_audit_pass(self) -> None:
        a = json.loads((REPORTS / "saleor_reserve_300_parity_gate_audit.json").read_text(encoding="utf-8"))
        assert a["pass"] == a["total"]

    def test_result_audit_pass(self) -> None:
        a = json.loads((REPORTS / "saleor_reserve_300_rmcss_result_audit.json").read_text(encoding="utf-8"))
        assert a["pass"] == a["total"]
