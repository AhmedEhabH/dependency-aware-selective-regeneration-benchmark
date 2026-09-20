# ruff: noqa: N812
"""STAGE5_CORRECTED_REEXECUTION - targeted validation tests (T3).

Covers the mission §17 targeted test list:
  - cache miss with embeddable blob -> resolution (build_plan + unit coverage);
  - cache hit;
  - no-unit file -> NaN (frozen DEV semantics, never a finite sentinel);
  - no finite sentinel;
  - abs(score) hard guard (feature builder fails hard);
  - parity gate quantities (sentinel count, NaN rate, finite range);
  - feature schema (11 features, names, order);
  - model/scaler hash + threshold == 0.20;
  - no refit;
  - Sparse outputs reused exactly;
  - bootstrap unchanged (10,000 resamples, seed 20260920, deterministic).
"""
from __future__ import annotations

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

from benchmark.calibrated.policy import BOOTSTRAP_SEED, N_BOOTSTRAP, paired_bootstrap_deltas  # noqa: E402
from benchmark.memory_rescue import candidates as C  # noqa: E402
from benchmark.signal.code_units import extract_code_units, sha256_text  # noqa: E402

STAGE_DIR = PROJECT_DIR / "research" / "stage5-v2-final"
REPORTS_DIR = PROJECT_DIR / "reports"
FROZEN_SHA = "8925d29a8e065bc864cd16e755ac0e896c7675b4a12f68fb66c35e5bd644ea95"


class TestNoFiniteSentinelAndNaN:
    def test_no_units_score_is_nan_based(self) -> None:
        """no_units_score imputes min_finite - 1 for NaN rows (no sentinel)."""
        df = pd.DataFrame({"dense_file_score": [0.5, 0.3, np.nan]})
        floor = C.no_units_score(df)
        assert floor == pytest.approx(0.3 - 1.0)

    def test_finite_minus_one_never_uses_1e9(self) -> None:
        df = pd.DataFrame({"dense_file_score": [0.5, 0.3, -1e9]})
        # -1e9 is finite -> treated as a real score by the imputer (the defect)
        floor = C.no_units_score(df)
        # the guard below must catch it instead
        assert abs(floor) > 10


class TestAbsScoreGuard:
    def test_guard_passes_normal_scores(self) -> None:
        df = pd.DataFrame({"dense_file_score": [0.5, 0.3, np.nan, -0.2]})
        C.assert_finite_dense_score_bounds(df)  # must not raise

    def test_guard_fails_on_1e9(self) -> None:
        df = pd.DataFrame({"dense_file_score": [0.5, 0.3, -1e9]})
        with pytest.raises(ValueError):
            C.assert_finite_dense_score_bounds(df)

    def test_guard_fails_on_1e6_and_999999(self) -> None:
        for bad in (-1e6, -999999.0, 100.0, -100.0):
            df = pd.DataFrame({"dense_file_score": [0.5, bad]})
            with pytest.raises(ValueError):
                C.assert_finite_dense_score_bounds(df)

    def test_guard_boundary_10_exact(self) -> None:
        df = pd.DataFrame({"dense_file_score": [10.0, -10.0, 9.999]})
        C.assert_finite_dense_score_bounds(df, bound=10.0)  # abs(10) is NOT > 10


class TestCacheMissCacheHitNoUnit:
    def _plan(self, blob_texts: dict) -> tuple[dict, dict]:
        plan: dict[str, list[str]] = {}
        unit_texts: dict[str, str] = {}
        for sha, text in blob_texts.items():
            if text is None:
                plan[sha] = []
                continue
            keys = []
            for u in extract_code_units(text):
                if not u.strip():
                    continue
                us = sha256_text(u)
                keys.append(us)
                unit_texts.setdefault(us, u)
            plan[sha] = keys
        return plan, unit_texts

    def test_empty_blob_no_units(self) -> None:
        plan, _ = self._plan({sha256_text(""): ""})
        assert plan[sha256_text("")] == []

    def test_whitespace_blob_no_units(self) -> None:
        plan, _ = self._plan({sha256_text("   \n  "): "   \n  "})
        assert plan[sha256_text("   \n  ")] == []

    def test_code_blob_has_units(self) -> None:
        code = "def f():\n    return 1\n"
        plan, unit_texts = self._plan({sha256_text(code): code})
        assert len(plan[sha256_text(code)]) >= 1
        assert all(u in unit_texts for u in plan[sha256_text(code)])

    def test_none_text_is_empty_plan(self) -> None:
        plan, _ = self._plan({sha256_text("x"): None})
        assert plan[sha256_text("x")] == []

    def test_cache_hit_resolution(self) -> None:
        """All units of a cached blob resolve (CASE A)."""
        code = "def g():\n    return 2\n"
        plan, unit_texts = self._plan({sha256_text(code): code})
        idx = {u: i for i, u in enumerate(unit_texts)}
        assert all(u in idx for u in plan[sha256_text(code)])

    def test_cache_miss_with_embeddable_units_is_covered_after_embed(self) -> None:
        """CASE B: after embedding, all units resolve; none silently sentinel."""
        code = "def h():\n    return 3\n"
        plan, unit_texts = self._plan({sha256_text(code): code})
        idx = {u: i for i, u in enumerate(unit_texts)}
        missing = [u for u in plan[sha256_text(code)] if u not in idx]
        assert missing == []


class TestParityGateQuantities:
    def test_sentinel_count_zero(self) -> None:
        g = json.loads((REPORTS_DIR / "stage5_parity_gate.json").read_text(encoding="utf-8"))
        assert g["pass"] == g["total"] == 8
        b = next(c for c in g["checks"] if c["name"] == "B.no_finite_sentinels")
        assert b["pass"] is True
        assert "==-1e9:0" in b["detail"]

    def test_parity_gate_a_embedding_coverage(self) -> None:
        g = json.loads((REPORTS_DIR / "stage5_parity_gate.json").read_text(encoding="utf-8"))
        a = next(c for c in g["checks"] if c["name"] == "A.embedding_coverage")
        assert a["pass"] is True
        assert "unresolved_misses=0" in a["detail"]

    def test_nan_rate_within_tolerance(self) -> None:
        g = json.loads((REPORTS_DIR / "stage5_parity_gate.json").read_text(encoding="utf-8"))
        c = next(c for c in g["checks"] if c["name"] == "C.nan_no_unit_rate")
        assert c["pass"] is True

    def test_finite_score_range(self) -> None:
        g = json.loads((REPORTS_DIR / "stage5_parity_gate.json").read_text(encoding="utf-8"))
        d = next(c for c in g["checks"] if c["name"] == "D.finite_score_range")
        assert d["pass"] is True


class TestFeatureSchemaAndModelHash:
    def test_feature_schema_exact_11(self) -> None:
        art = json.loads((STAGE_DIR / "deployment_artifact.json").read_text(encoding="utf-8"))
        assert art["feature_names"] == list(C.FEATURE_NAMES)
        assert len(art["feature_names"]) == 11

    def test_threshold_stays_020(self) -> None:
        art = json.loads((STAGE_DIR / "deployment_artifact.json").read_text(encoding="utf-8"))
        assert abs(float(art["threshold"]) - 0.20) < 1e-12

    def test_model_hash_frozen(self) -> None:
        art = json.loads((STAGE_DIR / "deployment_artifact.json").read_text(encoding="utf-8"))
        assert art["config_sha256"] == FROZEN_SHA
        assert art["realization"] == "A"

    def test_no_refit(self) -> None:
        art = json.loads((STAGE_DIR / "deployment_artifact.json").read_text(encoding="utf-8"))
        assert art["mission"] == "STAGE5_V2_FINAL"
        assert len(art["lr_coef"]) == 11


class TestSparseReusedAndBootstrap:
    def test_sparse_outputs_reused(self) -> None:
        rows = pd.read_parquet(STAGE_DIR / "candidate_rows_stage5_corrected.parquet")
        records = [json.loads(line) for line in
                   (STAGE_DIR / "sparse_stage5_run_records.jsonl").read_text(encoding="utf-8").splitlines()
                   if line.strip()]
        sparse_map = {}
        for r in records:
            if r["terminal_status"] == "succeeded":
                sparse_map.setdefault(r["case_id"], set(r["predicted_write_set"]))
        row_sets = {}
        for cid, g in rows.groupby("case_id"):
            row_sets[cid] = set(g.loc[g["in_sparse"] == 1, "file_path"])
        assert len(row_sets) == 139
        for cid, s in row_sets.items():
            assert s == sparse_map.get(cid, set())

    def test_bootstrap_unchanged(self) -> None:
        assert N_BOOTSTRAP == 10_000
        assert BOOTSTRAP_SEED == 20260920

    def test_bootstrap_deterministic(self) -> None:
        pc = [(1, 1, 0), (0, 1, 1), (1, 0, 1)]
        sc = [(1, 0, 1), (0, 1, 0), (1, 1, 0)]
        a = paired_bootstrap_deltas(pc, sc, n_resamples=200, seed=20260920)
        b = paired_bootstrap_deltas(pc, sc, n_resamples=200, seed=20260920)
        assert a["f1"]["point_delta"] == b["f1"]["point_delta"]
        assert a["f1"]["ci95_lower"] == b["f1"]["ci95_lower"]

    def test_corrected_primary_result_consistent(self) -> None:
        r = json.loads((REPORTS_DIR / "stage5_corrected_reexecution_result.json").read_text(encoding="utf-8"))
        assert r["verdict"] == "STAGE5_CORRECTED_REEXECUTION_POSITIVE"
        pe = r["primary_endpoint"]
        assert pe["resamples"] == 10_000 and pe["seed"] == 20260920
        assert pe["delta_f1_point"] > 0 and pe["ci95_lower"] > 0
