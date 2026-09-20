#!/usr/bin/env python3
"""STAGE5_V2_FINAL - final deployment V2 refit on ALL 323 DEVELOPMENT tasks (T3).

Frozen procedure (docs/STAGE5_V2_FINAL_IMPACT_DECLARATION_2026-09-20.md §9):
  1. build the frozen V2 candidate universe rows (Sparse ∪ dense-top20-non-
     Sparse ∪ structural-top10 ∪ episodic-top10) for ALL 323 DEV tasks
     (realization A);
  2. threshold selection: SAME deterministic 5-fold task-grouped
     repository-stratified OOF over all 323 DEV; inner threshold =
     argmax pooled micro-F1 over 0.01..0.99, tie-break HIGHER;
  3. final deployment model: L2-LR C=1.0 liblinear max_iter=1000 random_state=0,
     StandardScaler on continuous features fit on ALL 323 rows;
  4. persist deployment artifacts (coefficients, intercept, scaler, threshold,
     fold map, feature schema, candidate constants, hashes).

ZERO Stage-5 outcome access. ZERO sealed data. Deterministic.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))
sys.path.insert(0, str(_PROJECT_DIR / "scripts"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from benchmark.calibrated.folds import grouped_stratified_folds  # noqa: E402
from benchmark.calibrated.policy import (  # noqa: E402
    fit_policy,
    predict_proba,
    select_threshold,
)
from benchmark.memory_rescue import candidates as C  # noqa: E402, N812
from benchmark.memory_rescue.history import CACHE_ROOT  # noqa: E402
from benchmark.recall.data import load_dev_tasks  # noqa: E402

OUT_DIR = _PROJECT_DIR / "research" / "stage5-v2-final"
REPORTS_DIR = _PROJECT_DIR / "reports"
QWEN_DIR = _PROJECT_DIR / "research" / "contamination-bridge" / "qwen_embed"
MEMORY_CACHE = CACHE_ROOT / "memory_bundles.json"

N_FOLDS = 5
FOLD_SEED = 20260920
REALIZATION = "A"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_memory_bundles(realization: str) -> dict[str, C.MemoryBundle]:
    raw = json.loads(MEMORY_CACHE.read_text(encoding="utf-8"))
    out: dict[str, C.MemoryBundle] = {}
    for cid, t in raw["tasks"].items():
        v = t["variants"][realization]
        out[cid] = C.MemoryBundle(
            history_change_count={k: int(x) for k, x in t["history_change_count"].items()},
            cochange_sparse={k: float(x) for k, x in t["cochange_sparse"].items()},
            episode_similarity={k: float(x) for k, x in t["episode_similarity"].items()},
            episode_hit_count={k: int(x) for k, x in t["episode_hit_count"].items()},
            n_production_changing_commits=int(t["n_production_changing_commits"]),
            cochange_top1={k: float(x) for k, x in v["cochange_top1"].items()},
            structural=list(v["structural"]),
            episodic=list(t["episodic"]),
        )
    return out


def main() -> int:
    tasks = load_dev_tasks()
    if len(tasks) != 323:
        raise RuntimeError(f"expected 323 DEV tasks, got {len(tasks)}")
    tasks_by_id = {t.case_id: t for t in tasks}

    df = pd.read_parquet(QWEN_DIR / f"realization_{REALIZATION}" / "full_file_scores.parquet")
    memory = load_memory_bundles(REALIZATION)
    rows, _ = C.build_rows_with_provenance(df, tasks_by_id, memory)
    frame = C.rows_to_frame(rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(OUT_DIR / "deployment_candidate_rows.parquet", index=False, compression="zstd")

    repo_of = {cid: str(frame.loc[frame["case_id"] == cid, "repository"].iloc[0])
               for cid in sorted(set(frame["case_id"]))}
    case_ids = sorted(set(frame["case_id"]))
    if len(case_ids) != len(tasks_by_id):
        raise RuntimeError("frame case set must equal the DEV task set")

    # ---- 5-fold task-grouped OOF over ALL 323 DEV (threshold selection) ----
    fold_map = grouped_stratified_folds(case_ids, lambda c: repo_of[c], k=N_FOLDS, seed=FOLD_SEED)
    oof_probs: list[np.ndarray] = []
    oof_labels: list[np.ndarray] = []
    for fold in range(N_FOLDS):
        train_ids = [c for c in case_ids if fold_map[c] != fold]
        held_ids = [c for c in case_ids if fold_map[c] == fold]
        train_frame = frame[frame["case_id"].isin(train_ids)]
        held_frame = frame[frame["case_id"].isin(held_ids)]
        scaler, model = fit_policy(
            C.feature_matrix(train_frame), C.label_vector(train_frame),
            continuous_cols=C.CONTINUOUS_FEATURES, boolean_cols=C.BOOLEAN_FEATURES,
            feature_names=C.FEATURE_NAMES)
        probs = predict_proba(
            scaler, model, C.feature_matrix(held_frame),
            continuous_cols=C.CONTINUOUS_FEATURES, boolean_cols=C.BOOLEAN_FEATURES,
            feature_names=C.FEATURE_NAMES)
        oof_probs.append(probs)
        oof_labels.append(C.label_vector(held_frame))

    oof_all = np.concatenate(oof_probs)
    labels_all = np.concatenate(oof_labels)
    threshold = select_threshold(oof_all, labels_all)

    # ---- final deployment model on ALL 323 DEV rows ----
    scaler, model = fit_policy(
        C.feature_matrix(frame), C.label_vector(frame),
        continuous_cols=C.CONTINUOUS_FEATURES, boolean_cols=C.BOOLEAN_FEATURES,
        feature_names=C.FEATURE_NAMES)

    # ---- determinism check (identical rerun) ----
    # (computed once here; the validation step runs the reproducibility test)

    artifact = {
        "mission": "STAGE5_V2_FINAL",
        "realization": REALIZATION,
        "n_dev_tasks": len(case_ids),
        "n_candidate_rows": len(frame),
        "n_features": len(C.FEATURE_NAMES),
        "feature_names": list(C.FEATURE_NAMES),
        "continuous_features": list(C.CONTINUOUS_FEATURES),
        "boolean_features": list(C.BOOLEAN_FEATURES),
        "model": "L2 LogisticRegression",
        "C": 1.0,
        "solver": "liblinear",
        "max_iter": 1000,
        "random_state": 0,
        "scaler_mean": [float(x) for x in scaler.mean_.tolist()],
        "scaler_scale": [float(x) for x in scaler.scale_.tolist()],
        "lr_coef": [float(x) for x in model.coef_.ravel().tolist()],
        "lr_intercept": float(model.intercept_[0]),
        "threshold": float(threshold),
        "threshold_method": "5-fold task-grouped OOF argmax pooled micro-F1, tie-break HIGHER",
        "fold_seed": FOLD_SEED,
        "n_folds": N_FOLDS,
        "fold_map": fold_map,
        "oof_micro_f1_at_threshold": _micro_f1(oof_all, labels_all, threshold),
        "candidate_constants": {
            "TOP_ADD_UNIVERSE": C.TOP_ADD_UNIVERSE,
            "COCHANGE_TOP_FILES": C.COCHANGE_TOP_FILES,
            "EPISODIC_TOP_FILES": C.EPISODIC_TOP_FILES,
            "EPISODIC_TOP_CHANGES": None,
            "qwen_model": "qwen/qwen3-embedding-8b",
            "provider": "DeepInfra",
        },
    }
    artifact_json = json.dumps(artifact, sort_keys=True, indent=1)
    artifact_sha = _sha256_text(artifact_json)
    artifact["config_sha256"] = artifact_sha
    OUT_DIR.joinpath("deployment_artifact.json").write_text(
        json.dumps(artifact, sort_keys=True, indent=1), encoding="utf-8")
    REPORTS_DIR.joinpath("stage5_dev_refit_artifact.json").write_text(
        json.dumps(artifact, sort_keys=True, indent=1), encoding="utf-8")

    print(json.dumps({
        "n_tasks": len(case_ids),
        "n_rows": len(frame),
        "threshold": float(threshold),
        "lr_coef": [round(x, 6) for x in model.coef_.ravel().tolist()],
        "lr_intercept": round(float(model.intercept_[0]), 6),
        "config_sha256": artifact_sha,
    }, indent=1))
    print("[deployment refit] DONE")
    return 0


def _micro_f1(probs: np.ndarray, labels: np.ndarray, threshold: float) -> float:
    sel = probs >= threshold
    tp = int(np.sum(sel & (labels == 1)))
    fp = int(np.sum(sel & (labels == 0)))
    fn = int(np.sum((~sel) & (labels == 1)))
    denom = 2 * tp + fp + fn
    return 2.0 * tp / denom if denom else 0.0


if __name__ == "__main__":
    raise SystemExit(main())
