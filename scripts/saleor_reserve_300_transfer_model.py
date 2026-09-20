#!/usr/bin/env python3
# ruff: noqa: E501, N806, N812
"""SALEOR_RESERVE_300_RMCSS - fit DJANGO_ONLY_RMCSS_TRANSFER_MODEL (§7).

Fitted BEFORE any Saleor RESERVE target outcome is opened, using djangoCMS
DEVELOPMENT tasks ONLY, with the EXACT RM-CSS recipe:

  - 11 frozen RM-CSS features, same order;
  - StandardScaler on the 9 continuous features (fit on django rows);
  - L2 LogisticRegression C=1.0 solver=liblinear max_iter=1000 random_state=0;
  - threshold: 5-fold task-grouped OOF on djangoCMS DEV ONLY, grid 0.01..0.99
    step 0.01, argmax pooled micro-F1, tie-break higher.

Persisted (research/saleor-reserve-300-rmcss/django_only_rmcss_transfer_model.json):
coefficients, intercept, scaler mean/scale, threshold, feature schema,
training-task IDs, folds, configuration, SHA256 hashes.

No Saleor labels are used. Deterministic.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

from benchmark.calibrated.folds import grouped_stratified_folds, split_by_fold  # noqa: E402
from benchmark.calibrated.policy import select_threshold  # noqa: E402
from benchmark.memory_rescue import candidates as C  # noqa: E402

OUT = _PROJECT_DIR / "research" / "stage5-v2-final"
OUT_DIR = _PROJECT_DIR / "research" / "saleor-reserve-300-rmcss"
DEV_CAND = OUT / "deployment_candidate_rows.parquet"
SEED = 20260920


def main() -> int:
    dev = pd.read_parquet(DEV_CAND)
    dc = dev[dev["repository"] == "djangocms"]
    dc_ids = sorted(set(dc["case_id"]))
    repo_of = {cid: "djangocms" for cid in dc_ids}
    fold_map = grouped_stratified_folds(dc_ids, lambda c: repo_of[c], k=5, seed=SEED)

    idx_cont = [C.FEATURE_NAMES.index(c) for c in C.CONTINUOUS_FEATURES]
    idx_bool = [C.FEATURE_NAMES.index(c) for c in C.BOOLEAN_FEATURES]

    # threshold: 5-fold task-grouped OOF on djangoCMS DEV only
    probs: list[np.ndarray] = []
    labels: list[np.ndarray] = []
    for fold in range(5):
        tr, te = split_by_fold(fold_map, fold)
        trf = dc[dc["case_id"].isin(tr)]
        tef = dc[dc["case_id"].isin(te)]
        sc = StandardScaler()
        Xtr = C.feature_matrix(trf)
        Xtr_cont = sc.fit_transform(Xtr[:, idx_cont])
        Xtr_bool = Xtr[:, idx_bool].astype(np.float64)
        m = LogisticRegression(penalty="l2", C=1.0, solver="liblinear", max_iter=1000, random_state=0)
        m.fit(np.concatenate([Xtr_cont, Xtr_bool], axis=1), C.label_vector(trf))
        Xte = C.feature_matrix(tef)
        Xte_cont = sc.transform(Xte[:, idx_cont])
        Xte_bool = Xte[:, idx_bool].astype(np.float64)
        probs.append(m.predict_proba(np.concatenate([Xte_cont, Xte_bool], axis=1))[:, 1])
        labels.append(C.label_vector(tef))
    threshold = float(select_threshold(np.concatenate(probs), np.concatenate(labels)))

    # final model on ALL djangoCMS DEV rows
    scaler = StandardScaler()
    X = C.feature_matrix(dc)
    X_cont = scaler.fit_transform(X[:, idx_cont])
    X_bool = X[:, idx_bool].astype(np.float64)
    model = LogisticRegression(penalty="l2", C=1.0, solver="liblinear", max_iter=1000, random_state=0)
    model.fit(np.concatenate([X_cont, X_bool], axis=1), C.label_vector(dc))

    artifact = {
        "model_id": "DJANGO_ONLY_RMCSS_TRANSFER_MODEL",
        "mission": "SALEOR_RESERVE_300_RMCSS",
        "training": "djangoCMS DEVELOPMENT tasks ONLY (no Saleor labels)",
        "n_train_tasks": len(dc_ids),
        "threshold": threshold,
        "threshold_method": "5-fold task-grouped OOF on djangoCMS DEV ONLY; grid 0.01..0.99 step 0.01; argmax pooled micro-F1; tie-break HIGHER",
        "fold_seed": SEED,
        "feature_names": list(C.FEATURE_NAMES),
        "continuous_features": list(C.CONTINUOUS_FEATURES),
        "boolean_features": list(C.BOOLEAN_FEATURES),
        "model": "L2 LogisticRegression",
        "C": 1.0,
        "solver": "liblinear",
        "max_iter": 1000,
        "random_state": 0,
        "lr_coef": [float(x) for x in model.coef_.ravel()],
        "lr_intercept": float(model.intercept_[0]),
        "scaler_mean": [float(x) for x in scaler.mean_],
        "scaler_scale": [float(x) for x in scaler.scale_],
        "n_features": len(C.FEATURE_NAMES),
        "training_task_ids": dc_ids,
        "fold_map": fold_map,
    }
    # SHA256 of the canonical serialization (exclude training ids/fold map for the identity hash)
    body = {k: v for k, v in artifact.items() if k not in ("training_task_ids", "fold_map")}
    artifact["artifact_sha256"] = hashlib.sha256(
        json.dumps(body, indent=1, sort_keys=True).encode("utf-8")).hexdigest()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "django_only_rmcss_transfer_model.json").write_text(
        json.dumps(artifact, indent=1), encoding="utf-8")
    print(f"threshold={threshold} artifact_sha256={artifact['artifact_sha256']}")
    print(f"n_train_tasks={len(dc_ids)} coef_n={len(artifact['lr_coef'])}")
    print(f"wrote {OUT_DIR / 'django_only_rmcss_transfer_model.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
