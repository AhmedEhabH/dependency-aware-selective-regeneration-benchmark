"""Shared metrics for the strong-localization-signal studies (T3, ZERO API).

Canonical definitions used in EVERY relevant report from 2026-09-19 onward:

    Precision            P  = TP / (TP + FP)
    Recall               R  = TP / (TP + FN)
    False Negative Rate  FNR = FN / (TP + FN) = 1 - R
    F1                   F1 = 2TP / (2TP + FP + FN)
    Candidate precision  = correct recovered omitted positives / all accepted
                           recovery candidates
    ORR per task i       ORR_i = recovered omitted positives_i / omitted
                           positives_i (0 when the task has no omitted positives)
    Macro ORR            mean_i(ORR_i)

Paired task bootstrap (the TASK is the resampling unit, never individual
files): for bootstrap replicate b, Delta_b = Metric_B_b - Metric_A_b, and
CI95 = [quantile_2.5%(Delta), quantile_97.5%(Delta)] using a fixed seed and
>= 10,000 resamples. Pooled metrics (final file-level P/R/F1/FNR, candidate
precision, micro ORR) are recomputed within each resample by pooling the
resampled tasks' per-task contributions (TP/FP/FN, recovered/selected).

ZERO model/API calls. Deterministic. All functions are pure.
"""
from __future__ import annotations

import random
from collections.abc import Iterable, Sequence

import numpy as np

TPF = tuple[int, int, int]  # (tp, fp, fn)


def confusion(pred: Iterable[str], pos: Iterable[str]) -> tuple[int, int, int]:
    """Per-task confusion (tp, fp, fn) from a predicted set and the positives.

    pred = final predicted file set; pos = proxy positive file set.
    """
    p = set(pos)
    pr = set(pred)
    tp = len(pr & p)
    fp = len(pr - p)
    fn = len(p - pr)
    return tp, fp, fn


def p_r_f1_fnr(tp: int, fp: int, fn: int) -> dict:
    """Pooled Precision/Recall/F1/FNR from pooled TP/FP/FN (all four always present)."""
    denom_p = tp + fp
    denom_r = tp + fn
    p = tp / denom_p if denom_p else 0.0
    r = tp / denom_r if denom_r else 0.0
    f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
    fnr = fn / denom_r if denom_r else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r,
            "f1": f1, "fnr": fnr}


def candidate_precision(correct_recovered: int, selected: int) -> float:
    """correct recovered omitted positives / all accepted recovery candidates."""
    return correct_recovered / selected if selected else 0.0


def orr(recovered: int, missed: int) -> float:
    """ORR_i for one task; 0 when the task has no omitted positives (frozen macro convention)."""
    return recovered / missed if missed else 0.0


def macro_orr(values: Sequence[float]) -> float:
    """Mean over tasks of per-task ORR (includes the frozen zero-denominator tasks as 0)."""
    return float(np.mean(values)) if values else 0.0


# ---------------------------------------------------------------------------
# Paired task bootstrap
# ---------------------------------------------------------------------------

METRIC_NAMES = ("macro_orr", "final_precision", "final_recall", "final_f1",
                "final_fnr", "candidate_precision")


def _pool_metric(metric: str, contribs: Sequence[tuple]) -> float:
    """Compute a pooled metric from a list of per-task contribution tuples.

    Each contribution tuple carries exactly the fields required by `metric`:
      - macro_orr:        (orr_i,)                                            -> mean
      - final_precision / final_recall / final_f1 / final_fnr: (tp, fp, fn)   -> pooled P/R/F1/FNR
      - candidate_precision: (cand_fn, cand_sel)                              -> pooled cand precision
    """
    if metric == "macro_orr":
        return float(np.mean([c[0] for c in contribs])) if contribs else 0.0
    if metric in ("final_precision", "final_recall", "final_f1", "final_fnr"):
        tp = sum(c[0] for c in contribs)
        fp = sum(c[1] for c in contribs)
        fn = sum(c[2] for c in contribs)
        return p_r_f1_fnr(tp, fp, fn)[metric.replace("final_", "")]
    if metric == "candidate_precision":
        cand_fn = sum(c[0] for c in contribs)
        cand_sel = sum(c[1] for c in contribs)
        return candidate_precision(cand_fn, cand_sel)
    raise ValueError(f"unknown metric {metric}")


def paired_bootstrap(
    arm_a: Sequence[tuple],
    arm_b: Sequence[tuple],
    metric: str,
    n_resamples: int = 10_000,
    seed: int = 20260919,
) -> dict:
    """Paired task bootstrap for `metric` (Arm B - Arm A deltas).

    arm_a / arm_b are aligned per-task contribution tuples (task i in arm_a
    pairs with task i in arm_b). The TASK is the bootstrap unit: each resample
    draws n task indices with replacement and pools the sampled per-task
    contributions inside each arm, then records Delta_b = metric_B - metric_A.
    CI95 = [q2.5, q97.5] of the delta distribution.

    Returns point estimate (full-sample delta), CI, and the raw delta array.
    """
    if len(arm_a) != len(arm_b):
        raise ValueError("arm_a and arm_b must be aligned per task")
    n = len(arm_a)
    if n == 0:
        raise ValueError("no tasks to bootstrap")
    point_a = _pool_metric(metric, arm_a)
    point_b = _pool_metric(metric, arm_b)
    point = point_b - point_a

    rng = random.Random(seed)
    deltas = np.empty(n_resamples, dtype=np.float64)
    for b in range(n_resamples):
        idx = [rng.randrange(n) for _ in range(n)]
        va = _pool_metric(metric, [arm_a[i] for i in idx])
        vb = _pool_metric(metric, [arm_b[i] for i in idx])
        deltas[b] = vb - va
    lo, hi = np.quantile(deltas, [0.025, 0.975])
    return {
        "metric": metric,
        "n_tasks": n,
        "n_resamples": n_resamples,
        "seed": seed,
        "point_arm_a": float(point_a),
        "point_arm_b": float(point_b),
        "point_delta": float(point),
        "ci95_lower": float(lo),
        "ci95_upper": float(hi),
        "ci95_excludes_zero": bool((lo > 0) or (hi < 0)),
    }
