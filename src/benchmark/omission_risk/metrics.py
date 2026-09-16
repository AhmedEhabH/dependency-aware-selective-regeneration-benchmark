"""Omission-Risk Feature Study V1 — routing metrics (deterministic, ZERO LLM).

Metrics are task-level (n independent tasks). Nested repetitions are NOT
treated as independent observations (there are none on TRAIN/VALIDATION for the
deterministic first pass; P1-style LLM repetitions are deferred).

All estimators are deterministic given a frozen bootstrap seed.

Metric set (pre-registered in reports/OMISSION_RISK_DETECTION_PROTOCOL_DRAFT.md
and idea_ledger I6):
- AUROC (rank-based, sign-free; direction reported separately)
- AUPRC (sklearn average_precision_score) vs base prevalence
- Brier score / ECE after a DEVELOPMENT-ONLY logistic calibration
- risky-task recall at escalation budgets 20%/40%/60% (and the full
  risk-coverage curve)
- task-level bootstrap CIs (95%) where sensible
"""

from __future__ import annotations

import random
from collections.abc import Callable, Sequence
from typing import Any

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score


def auroc(risk: Sequence[float], y: Sequence[int]) -> float:
    """Raw rank-based AUROC (no folding).

    Values below 0.5 indicate the label is anti-correlated with the score
    direction used; the signed AUROC (:func:`auroc_direction`) carries the
    same number and is used for direction interpretation.
    """
    r = np.asarray(risk, dtype=float)
    yt = np.asarray(y, dtype=int)
    if len(np.unique(yt)) < 2 or np.std(r) == 0:
        return 0.5
    return float(roc_auc_score(yt, r))


def auroc_direction(risk: Sequence[float], y: Sequence[int]) -> float:
    """Raw AUROC on [0,1]; >=0.5 means larger risk -> more omissions."""
    return auroc(risk, y)


def auprc(risk: Sequence[float], y: Sequence[int]) -> float:
    """Average precision (AUPRC) of the risk score vs the label."""
    r = np.asarray(risk, dtype=float)
    yt = np.asarray(y, dtype=int)
    if len(np.unique(yt)) < 2:
        return float(np.mean(yt))
    return float(average_precision_score(yt, r))


def _platt_calibration(
    risk_train: Sequence[float],
    y_train: Sequence[int],
    risk_eval: Sequence[float],
) -> np.ndarray:
    """Development-only logistic calibration fitted on TRAIN, applied to eval."""
    rt = np.asarray(risk_train, dtype=float).reshape(-1, 1)
    yt = np.asarray(y_train, dtype=int)
    clf = LogisticRegression(max_iter=1000)
    clf.fit(rt, yt)
    re = np.asarray(risk_eval, dtype=float).reshape(-1, 1)
    return np.asarray(clf.predict_proba(re)[:, 1], dtype=float)


def _isotonic_calibration(
    risk_train: Sequence[float],
    y_train: Sequence[int],
    risk_eval: Sequence[float],
) -> np.ndarray:
    """Development-only isotonic calibration (monotone) fitted on TRAIN."""
    rt = np.asarray(risk_train, dtype=float)
    yt = np.asarray(y_train, dtype=int)
    iso = IsotonicRegression(out_of_bounds="clip", increasing=True)
    iso.fit(rt, yt)
    return np.asarray(iso.predict(np.asarray(risk_eval, dtype=float)))


def brier(prob: Sequence[float], y: Sequence[int]) -> float:
    """Mean squared error of calibrated probability vs binary label."""
    p = np.asarray(prob, dtype=float)
    yt = np.asarray(y, dtype=int)
    return float(np.mean((p - yt) ** 2))


def ece(prob: Sequence[float], y: Sequence[int], n_bins: int = 5) -> float:
    """Expected calibration error over equal-bin calibration groups."""
    p = np.asarray(prob, dtype=float)
    yt = np.asarray(y, dtype=int)
    if len(p) == 0:
        return 0.0
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    total = 0.0
    for lo, hi in zip(edges[:-1], edges[1:], strict=False):
        mask = (p >= lo) & (p <= hi)
        if mask.sum() == 0:
            continue
        conf = float(np.mean(p[mask]))
        freq = float(np.mean(yt[mask]))
        total += (mask.sum() / len(p)) * abs(conf - freq)
    return float(total)


def recall_at_budget(
    risk: Sequence[float],
    y: Sequence[int],
    budgets: Sequence[float] = (0.2, 0.4, 0.6),
) -> dict[str, float]:
    """Risky-task recall when escalating the top-q fraction of tasks by risk.

    recall(q) = (# has_fn tasks among the top-q) / (# has_fn tasks).
    Ties broken deterministically by the task's (risk, index).
    """
    n = len(risk)
    if n == 0:
        return {f"recall_{q:.2f}": 0.0 for q in budgets}
    order = list(range(n))
    order.sort(key=lambda i: (-float(risk[i]), i))
    yt = np.asarray(y, dtype=int)
    n_pos = int(yt.sum())
    out: dict[str, float] = {}
    for q in budgets:
        take = min(n, max(1, int(round(q * n))))
        top = order[:take]
        captured = int(yt[top].sum())
        out[f"recall_{q:.2f}"] = captured / n_pos if n_pos else 0.0
    return out


def risk_coverage(risk: Sequence[float], y: Sequence[int]) -> dict[str, float]:
    """Risk-coverage curve: risky-task recall at every escalation rate t/20."""
    qs = [i / 20.0 for i in range(0, 21)]
    out: dict[str, float] = {}
    for q in qs:
        if q == 0.0:
            out[f"cov_{q:.2f}"] = 0.0
            continue
        out[f"cov_{q:.2f}"] = recall_at_budget(risk, y, (q,))[f"recall_{q:.2f}"]
    return out


def bootstrap_ci(
    risk: Sequence[float],
    y: Sequence[int],
    metric_fn: Callable[[Sequence[float], Sequence[int]], float],
    *,
    n_resamples: int = 1000,
    seed: int = 20260916,
) -> dict[str, float]:
    """Task-level bootstrap (resample tasks with replacement) 95% CI.

    Tasks are the independent units; the estimator is recomputed per resample.
    """
    rng = random.Random(seed)
    r = list(risk)
    yt = list(y)
    n = len(r)
    values: list[float] = []
    for _ in range(n_resamples):
        idx = [rng.randrange(n) for _ in range(n)]
        values.append(metric_fn([r[i] for i in idx], [yt[i] for i in idx]))
    arr = np.asarray(values, dtype=float)
    return {
        "estimate": float(metric_fn(risk, y)),
        "ci95_low": float(np.percentile(arr, 2.5)),
        "ci95_high": float(np.percentile(arr, 97.5)),
        "n_resamples": n_resamples,
        "seed": seed,
    }


def calibration_report(
    *,
    y_train: Sequence[int],
    risk_train: Sequence[float],
    y_eval: Sequence[int],
    risk_eval: Sequence[float],
    method: str = "platt",
) -> dict[str, Any]:
    """Development-only calibration: fit on TRAIN, evaluate Brier/ECE on EVAL."""
    if method == "isotonic":
        p = _isotonic_calibration(risk_train, y_train, risk_eval)
    else:
        p = _platt_calibration(risk_train, y_train, risk_eval)
    return {
        "method": method,
        "brier": brier(list(p), y_eval),
        "ece": ece(list(p), y_eval),
        "mean_predicted": float(np.mean(p)),
    }
