"""WP-1a shared scorer - one scorer for the future three arms.

Arms: repository_agent, SIP, RM-CSS.
Inputs: frozen predictions (task_id -> set of file paths); labels loaded ONLY
after prediction freeze; identical task-ID sets.

Metrics: TP, FP, FN, Precision, Recall, FNR, F1, mean predicted-set size,
empty-set rate.

Statistical plan: paired task bootstrap, N_RESAMPLES=10000, seed=20260920,
DeltaF1 = F1(RM-CSS) - F1(repository_agent), 95% percentile CI
[Q2.5, Q97.5]. CI crossing zero => NO_DIFFERENCE_DETECTED_AT_THIS_N (not
equivalence). No non-inferiority margin is silently chosen.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

import numpy as np

ARMS: tuple[str, ...] = ("repository_agent", "SIP", "RM-CSS")

N_RESAMPLES: int = 10_000
BOOTSTRAP_SEED: int = 20260920
CI_QUANTILES: tuple[float, float] = (0.025, 0.975)

METRIC_NAMES: tuple[str, ...] = (
    "tp", "fp", "fn", "precision", "recall", "fnr", "f1",
    "mean_predicted_set_size", "empty_set_rate",
)


@dataclass(frozen=True)
class ArmConfusion:
    tp: int
    fp: int
    fn: int

    @property
    def precision(self) -> float:
        return self.tp / (self.tp + self.fp) if (self.tp + self.fp) else 0.0

    @property
    def recall(self) -> float:
        return self.tp / (self.tp + self.fn) if (self.tp + self.fn) else 0.0

    @property
    def fnr(self) -> float:
        return self.fn / (self.tp + self.fn) if (self.tp + self.fn) else 0.0

    @property
    def f1(self) -> float:
        denom = 2 * self.tp + self.fp + self.fn
        return 2.0 * self.tp / denom if denom else 0.0


def per_task_confusion(
    predicted: set[str], label: set[str]
) -> ArmConfusion:
    tp = len(predicted & label)
    fp = len(predicted - label)
    fn = len(label - predicted)
    return ArmConfusion(tp=tp, fp=fp, fn=fn)


def confusion_from_components(components: list[ArmConfusion]) -> ArmConfusion:
    tp = sum(c.tp for c in components)
    fp = sum(c.fp for c in components)
    fn = sum(c.fn for c in components)
    return ArmConfusion(tp=tp, fp=fp, fn=fn)


def score_arm(
    predictions: dict[str, set[str]],
    labels: dict[str, set[str]],
    task_ids: list[str],
) -> dict[str, float | int]:
    """Pooled micro metrics for one arm over the identical task-ID set."""
    components = [per_task_confusion(predictions.get(cid, set()), labels[cid]) for cid in task_ids]
    pooled = confusion_from_components(components)
    sizes = [len(predictions.get(cid, set())) for cid in task_ids]
    empty_rate = sum(1 for s in sizes if s == 0) / len(task_ids) if task_ids else 0.0
    return {
        "tp": pooled.tp,
        "fp": pooled.fp,
        "fn": pooled.fn,
        "precision": pooled.precision,
        "recall": pooled.recall,
        "fnr": pooled.fnr,
        "f1": pooled.f1,
        "mean_predicted_set_size": float(np.mean(sizes)) if sizes else 0.0,
        "empty_set_rate": float(empty_rate),
    }


def paired_bootstrap_delta_f1(
    arm_a_components: list[ArmConfusion],
    arm_b_components: list[ArmConfusion],
    *,
    n_resamples: int = N_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, object]:
    """Paired task bootstrap of DeltaF1 = F1(arm_a) - F1(arm_b).

    The task is the resampling unit: each bootstrap sample draws n task indices
    with replacement and pools the confusion components of BOTH arms over those
    SAME tasks (paired). Returns point delta + 95% percentile CI.
    """
    n = len(arm_a_components)
    if n != len(arm_b_components) or n == 0:
        raise ValueError("paired bootstrap requires equal non-empty component lists")
    rng = random.Random(seed)

    def _f1(components: list[ArmConfusion], idx: list[int]) -> float:
        pooled = confusion_from_components([components[i] for i in idx])
        return pooled.f1

    deltas = np.empty(n_resamples, dtype=np.float64)
    for b in range(n_resamples):
        idx = [rng.randrange(n) for _ in range(n)]
        deltas[b] = _f1(arm_a_components, idx) - _f1(arm_b_components, idx)
    lo, hi = np.quantile(deltas, CI_QUANTILES)
    point = _f1(arm_a_components, list(range(n))) - _f1(arm_b_components, list(range(n)))
    return {
        "delta_f1_point": float(point),
        "ci95_lower": float(lo),
        "ci95_upper": float(hi),
        "n_resamples": n_resamples,
        "seed": seed,
        "ci_quantiles": list(CI_QUANTILES),
        "ci_crosses_zero": bool(lo < 0 < hi),
        "interpretation_if_crosses_zero": (
            "NO_DIFFERENCE_DETECTED_AT_THIS_N (not equivalence)"
            if bool(lo < 0 < hi) else "CI excludes zero"
        ),
    }


def assert_identical_task_ids(*task_id_sets: set[str]) -> list[str]:
    """Assert all arms share the exact identical task-ID set; return sorted."""
    if not task_id_sets:
        raise ValueError("no task-ID sets provided")
    first = task_id_sets[0]
    for s in task_id_sets[1:]:
        if s != first:
            raise ValueError("task-ID sets differ across arms")
    return sorted(first)
