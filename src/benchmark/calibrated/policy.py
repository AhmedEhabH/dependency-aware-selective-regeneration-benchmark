"""CALIBRATED_SET_SELECTION_V1 — L2-LR policy + threshold + metrics (T3, ZERO API).

Frozen configuration (docs/CALIBRATED_SET_SELECTION_V1_IMPACT_DECLARATION_2026-09-20.md):

- Model: L2-regularized LogisticRegression (C=1.0, solver=liblinear,
  max_iter=1000, random_state=0) — deterministic, no hyperparameter search.
- Preprocessing: StandardScaler on the 5 continuous features
  (CONTINUOUS_FEATURES in features.py); boolean features are NOT scaled.
  The scaler is fit ONLY on training rows.
- Threshold: `t = argmax pooled micro-F1` over the grid 0.01..0.99 (step 0.01)
  on INNER task-grouped OOF predictions; tie-break = HIGHER threshold.
- Final set: {candidate file : predicted_probability >= t}.
- Metrics: pooled TP/FP/FN -> Precision/Recall/F1/FNR; task-paired bootstrap
  CIs (>= 10,000 resamples, fixed seed; the TASK is the unit).

All functions are pure and deterministic.
"""
# ruff: noqa: N803, N806

from __future__ import annotations

import random

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from .features import BOOLEAN_FEATURES, CONTINUOUS_FEATURES, FEATURE_NAMES

THRESHOLD_GRID = tuple(round(0.01 * i, 2) for i in range(1, 100))
N_BOOTSTRAP = 10_000
BOOTSTRAP_SEED = 20260920


def fit_policy(X_train: np.ndarray, y_train: np.ndarray,
               continuous_cols: tuple = CONTINUOUS_FEATURES,
               boolean_cols: tuple = BOOLEAN_FEATURES,
               feature_names: tuple = FEATURE_NAMES) -> tuple[StandardScaler, LogisticRegression]:
    """Fit StandardScaler (continuous features only) + L2-LR on training rows.

    The feature matrix X is assumed to have columns in `feature_names` order
    (defaults to the frozen V1 FEATURE_NAMES). The scaler is fit ONLY on the
    continuous columns; boolean columns pass through unscaled.
    """
    idx_cont = [feature_names.index(c) for c in continuous_cols]
    idx_bool = [feature_names.index(c) for c in boolean_cols]
    if not idx_cont or not idx_bool:
        raise ValueError("feature index split is empty; frozen feature order changed")
    scaler = StandardScaler()
    X_cont = scaler.fit_transform(X_train[:, idx_cont])
    X_bool = X_train[:, idx_bool].astype(np.float64)
    X_scaled = np.concatenate([X_cont, X_bool], axis=1)
    model = LogisticRegression(
        penalty="l2", C=1.0, solver="liblinear", max_iter=1000, random_state=0
    )
    model.fit(X_scaled, y_train)
    return scaler, model


def predict_proba(scaler: StandardScaler, model: LogisticRegression,
                  X: np.ndarray,
                  continuous_cols: tuple = CONTINUOUS_FEATURES,
                  boolean_cols: tuple = BOOLEAN_FEATURES,
                  feature_names: tuple = FEATURE_NAMES) -> np.ndarray:
    """Positive-class probability for rows X (columns in `feature_names` order)."""
    idx_cont = [feature_names.index(c) for c in continuous_cols]
    idx_bool = [feature_names.index(c) for c in boolean_cols]
    X_cont = scaler.transform(X[:, idx_cont])
    X_bool = X[:, idx_bool].astype(np.float64)
    X_scaled = np.concatenate([X_cont, X_bool], axis=1)
    return model.predict_proba(X_scaled)[:, 1]


def pooled_micro_f1(probs: np.ndarray, labels: np.ndarray, threshold: float) -> float:
    """Pooled micro-F1 at a threshold over OOF predictions."""
    sel = probs >= threshold
    tp = int(np.sum(sel & (labels == 1)))
    fp = int(np.sum(sel & (labels == 0)))
    fn = int(np.sum((~sel) & (labels == 1)))
    denom = 2 * tp + fp + fn
    return 2.0 * tp / denom if denom else 0.0


def max_f1_on_grid(probs: np.ndarray, labels: np.ndarray,
                   grid: tuple = THRESHOLD_GRID) -> float:
    """Maximum pooled micro-F1 achievable on the grid (descriptive F1*)."""
    return max(pooled_micro_f1(probs, labels, t) for t in grid)


def select_threshold(probs: np.ndarray, labels: np.ndarray,
                     grid: tuple = THRESHOLD_GRID) -> float:
    """t = argmax pooled micro-F1 on inner-OOF predictions; tie-break HIGHER t.

    The grid is iterated ascending; on an F1 tie (within floating tolerance)
    the HIGHER threshold replaces the current best (conservative tie-break).
    """
    best_t = grid[0]
    best_f1 = -1.0
    for t in grid:
        f1 = pooled_micro_f1(probs, labels, t)
        if f1 >= best_f1 - 1e-12:
            best_f1 = f1
            best_t = t
    return float(best_t)


def confusion(tp: int, fp: int, fn: int) -> dict:
    """Pooled Precision/Recall/F1/FNR from pooled TP/FP/FN."""
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
    fnr = fn / (tp + fn) if (tp + fn) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r,
            "f1": f1, "fnr": fnr}


def per_task_confusion(selected: set, proxy: set) -> tuple[int, int, int]:
    """Per-task (tp, fp, fn) of a final selected set against the proxy."""
    tp = len(selected & set(proxy))
    fp = len(selected - set(proxy))
    fn = len(set(proxy) - selected)
    return tp, fp, fn


def paired_bootstrap_deltas(
    policy_contribs: list[tuple[int, int, int]],
    sparse_contribs: list[tuple[int, int, int]],
    n_resamples: int = N_BOOTSTRAP,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, dict]:
    """Task-paired bootstrap CI95 for P/R/F1/FNR deltas (policy - sparse).

    policy_contribs[i] / sparse_contribs[i] are aligned per-task (tp, fp, fn).
    The TASK is the resampling unit; within each resample the per-task
    contributions are pooled and the metric recomputed, then
    Delta_b = Metric_policy_b - Metric_sparse_b. CI95 = [Q2.5, Q97.5].
    """
    if len(policy_contribs) != len(sparse_contribs):
        raise ValueError("aligned per-task contributions required")
    n = len(policy_contribs)
    if n == 0:
        raise ValueError("no tasks to bootstrap")
    rng = random.Random(seed)
    metrics = ("precision", "recall", "f1", "fnr")

    def _pool(contribs, idx):
        tp = sum(contribs[i][0] for i in idx)
        fp = sum(contribs[i][1] for i in idx)
        fn = sum(contribs[i][2] for i in idx)
        return tp, fp, fn

    out: dict[str, dict] = {}
    for m in metrics:
        point_p = confusion(*_pool(policy_contribs, range(n)))[m]
        point_s = confusion(*_pool(sparse_contribs, range(n)))[m]
        deltas = np.empty(n_resamples, dtype=np.float64)
        for b in range(n_resamples):
            idx = [rng.randrange(n) for _ in range(n)]
            dp = confusion(*_pool(policy_contribs, idx))[m]
            ds = confusion(*_pool(sparse_contribs, idx))[m]
            deltas[b] = dp - ds
        lo, hi = np.quantile(deltas, [0.025, 0.975])
        out[m] = {
            "metric": m,
            "n_tasks": n,
            "n_resamples": n_resamples,
            "seed": seed,
            "point_policy": float(point_p),
            "point_sparse": float(point_s),
            "point_delta": float(point_p - point_s),
            "ci95_lower": float(lo),
            "ci95_upper": float(hi),
            "ci95_excludes_zero": bool((lo > 0) or (hi < 0)),
        }
    return out
