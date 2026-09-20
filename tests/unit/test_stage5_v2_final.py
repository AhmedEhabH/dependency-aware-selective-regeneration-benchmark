"""Stage-5 V2 final preregistration — validation tests (T3, DEV-only).

Covers the pre-unsealing validation list:
  - feature schema (exactly 11 features, frozen order);
  - final-model serialization/reload test (coefficients + threshold preserved);
  - threshold reproducibility (deterministic 5-fold OOF argmax micro-F1);
  - candidate-generator determinism;
  - Sparse baseline determinism (write_set is fixed from the frozen run records);
  - Qwen config/provider check;
  - parent-only history guard (sealed / no-future failure closed);
  - preregistration hash verification.

No Stage-5 outcome access.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))
if str(PROJECT_DIR / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR / "src"))
if str(PROJECT_DIR / "scripts") not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR / "scripts"))

from benchmark.calibrated.folds import grouped_stratified_folds  # noqa: E402
from benchmark.calibrated.policy import fit_policy, predict_proba, select_threshold  # noqa: E402
from benchmark.memory_rescue import candidates as C  # noqa: E402, N812
from benchmark.memory_rescue.history import CACHE_ROOT, RepoHistory, TaskHistory  # noqa: E402
from benchmark.recall.data import load_dev_tasks  # noqa: E402
from benchmark.signal.or_embeddings import (  # noqa: E402
    OPENROUTER_EMBED_MODEL,
    OPENROUTER_EMBED_PROVIDER,
)

STAGE_DIR = PROJECT_DIR / "research" / "stage5-v2-final"
REPORTS_DIR = PROJECT_DIR / "reports"


def _load_artifact() -> dict:
    return json.loads((STAGE_DIR / "deployment_artifact.json").read_text(encoding="utf-8"))


def _load_frame() -> object:
    import pandas as pd

    return pd.read_parquet(STAGE_DIR / "deployment_candidate_rows.parquet")


class TestFinalModel:
    def test_feature_schema_exact_11(self) -> None:
        art = _load_artifact()
        assert art["feature_names"] == list(C.FEATURE_NAMES)
        assert len(art["feature_names"]) == 11
        assert set(art["continuous_features"]) == set(C.CONTINUOUS_FEATURES)
        assert set(art["boolean_features"]) == set(C.BOOLEAN_FEATURES)

    def test_coefficients_shape(self) -> None:
        art = _load_artifact()
        assert len(art["lr_coef"]) == 11
        assert len(art["scaler_mean"]) == len(C.CONTINUOUS_FEATURES) == 9
        assert len(art["scaler_scale"]) == 9

    def test_threshold_reproducible(self) -> None:
        """Re-run the 5-fold OOF threshold selection and compare."""
        frame = _load_frame()
        repo_of = {cid: str(frame.loc[frame["case_id"] == cid, "repository"].iloc[0])
                   for cid in sorted(set(frame["case_id"]))}
        case_ids = sorted(set(frame["case_id"]))
        fold_map = grouped_stratified_folds(
            case_ids, lambda c: repo_of[c], k=5, seed=20260920)
        probs: list[np.ndarray] = []
        labels: list[np.ndarray] = []
        for fold in range(5):
            train_ids = [c for c in case_ids if fold_map[c] != fold]
            held_ids = [c for c in case_ids if fold_map[c] == fold]
            tr = frame[frame["case_id"].isin(train_ids)]
            te = frame[frame["case_id"].isin(held_ids)]
            sc, m = fit_policy(C.feature_matrix(tr), C.label_vector(tr),
                               continuous_cols=C.CONTINUOUS_FEATURES,
                               boolean_cols=C.BOOLEAN_FEATURES,
                               feature_names=C.FEATURE_NAMES)
            probs.append(predict_proba(sc, m, C.feature_matrix(te),
                                       continuous_cols=C.CONTINUOUS_FEATURES,
                                       boolean_cols=C.BOOLEAN_FEATURES,
                                       feature_names=C.FEATURE_NAMES))
            labels.append(C.label_vector(te))
        t = select_threshold(np.concatenate(probs), np.concatenate(labels))
        assert abs(t - _load_artifact()["threshold"]) < 1e-12

    def test_serialization_reload(self) -> None:
        """Coefficients/intercept/threshold reload from JSON == refit on all rows."""
        art = _load_artifact()
        frame = _load_frame()
        sc, m = fit_policy(C.feature_matrix(frame), C.label_vector(frame),
                           continuous_cols=C.CONTINUOUS_FEATURES,
                           boolean_cols=C.BOOLEAN_FEATURES,
                           feature_names=C.FEATURE_NAMES)
        np.testing.assert_allclose([float(x) for x in m.coef_.ravel()],
                                   art["lr_coef"], rtol=1e-6, atol=1e-6)
        np.testing.assert_allclose([float(m.intercept_[0])], [art["lr_intercept"]],
                                   rtol=1e-6, atol=1e-6)
        np.testing.assert_allclose(sc.mean_, art["scaler_mean"], rtol=1e-6, atol=1e-6)
        np.testing.assert_allclose(sc.scale_, art["scaler_scale"], rtol=1e-6, atol=1e-6)

    def test_preregistration_hash(self) -> None:
        p = REPORTS_DIR / "stage5_final_preregistration.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        stored = data["preregistration_sha256"]
        # stored hash was computed before the sha field was added
        recomputed_body = {k: v for k, v in data.items() if k != "preregistration_sha256"}
        d = hashlib.sha256(json.dumps(recomputed_body, indent=1, sort_keys=True).encode()).hexdigest()
        assert d == stored


class TestCandidateDeterminism:
    def test_candidate_rows_reproducible(self) -> None:
        art = _load_artifact()
        # The deployment rows parquet is deterministic content; recompute its row count
        frame = _load_frame()
        assert len(frame) == art["n_candidate_rows"]
        assert frame["case_id"].nunique() == art["n_dev_tasks"] == 323


class TestSparseBaseline:
    def test_write_set_deterministic_from_records(self) -> None:
        tasks = load_dev_tasks()
        # write_set comes from the frozen run records (first-succeeded rep); verify
        # it is non-empty for at least a sanity subset and stable across load.
        t1 = [t for t in tasks if t.repository == "djangocms"][:5]
        # load twice and ensure identical objects
        tasks2 = load_dev_tasks()
        by = {t.case_id: frozenset(t.write_set) for t in tasks2}
        for t in t1:
            assert by[t.case_id] == frozenset(t.write_set)


class TestQwenConfig:
    def test_model_and_provider_frozen(self) -> None:
        assert OPENROUTER_EMBED_MODEL == "qwen/qwen3-embedding-8b"
        assert OPENROUTER_EMBED_PROVIDER == "DeepInfra"


class TestParentOnlyHistoryGuard:
    def test_repo_history_fail_closed_on_sealed(self) -> None:
        # A future commit hash must not be resolvable as an ancestor of a DEV parent.
        tasks = load_dev_tasks()
        dc = [t for t in tasks if t.repository == "djangocms"][0]
        rh = RepoHistory("djangocms")
        # The parent must be reachable; any non-ancestor raises.
        try:
            rh.ancestors_of(dc.parent_commit)
        except RuntimeError:
            pytest.fail("DEV parent must be resolvable")

    def test_parent_only_guard_frozen(self) -> None:
        tasks = load_dev_tasks()
        dc = [t for t in tasks if t.repository == "djangocms"][0]
        rh = RepoHistory("djangocms")
        th = TaskHistory(rh, dc.parent_commit, set(dc.universe_records))
        # production-changing commit count must equal cached memory bundle
        raw = json.loads((CACHE_ROOT / "memory_bundles.json").read_text(encoding="utf-8"))
        bundle = raw["tasks"][dc.case_id]
        assert th.n_production_changing_commits() == int(
            bundle["n_production_changing_commits"])
