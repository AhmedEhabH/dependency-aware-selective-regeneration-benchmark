"""Common evaluator (V1).

One scoring function for every method: predicted selected file set vs the
hidden observed-change proxy, using the SAME frozen binary evaluator semantics
as P1/P5 (``p1_selection_metrics``). Micro/macro aggregation is shared so every
method is compared on identical denominators.
"""

from __future__ import annotations

from typing import Any

from benchmark.real_commits import p1_evaluation as p1

from .interfaces import PlanPrediction, RankedPrediction

COMMON_EVALUATOR_VERSION: str = "harness-common-evaluator-v1"

_METRIC_FIELDS = (
    "tp",
    "fp",
    "fn",
    "precision",
    "recall",
    "f1",
    "fnr",
    "full_recall",
    "proxy_size",
    "predicted_size",
)


def evaluate_prediction(
    *,
    prediction: RankedPrediction | PlanPrediction,
    proxy_paths: tuple[str, ...],
) -> dict[str, Any]:
    """Score one prediction against the hidden proxy (evaluation-only)."""
    selected = set(prediction.selected_paths)
    proxy = set(proxy_paths)
    metrics = p1.p1_selection_metrics(selected, proxy)
    return {
        "case_id": prediction.case_id,
        "method": prediction.method,
        "k": prediction.k if isinstance(prediction, RankedPrediction) else None,
        "selected_count": int(metrics["predicted_size"]),
        "proxy_count": int(metrics["proxy_size"]),
        "tp": int(metrics["tp"]),
        "fp": int(metrics["fp"]),
        "fn": int(metrics["fn"]),
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1": metrics["f1"],
        "fnr": metrics["fnr"],
        "full_recall": bool(metrics["full_recall"]),
        "evaluator_version": COMMON_EVALUATOR_VERSION,
    }


def aggregate_micro(task_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Pooled micro P/R/F1/FNR over tasks (TP/FP/FN summed)."""
    tp = sum(int(r["tp"]) for r in task_results)
    fp = sum(int(r["fp"]) for r in task_results)
    fn = sum(int(r["fn"]) for r in task_results)
    selected = sum(int(r["selected_count"]) for r in task_results)
    precision = tp / selected if selected else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    fnr = fn / (tp + fn) if (tp + fn) else 0.0
    return {
        "tasks": len(task_results),
        "selected": selected,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "fnr": fnr,
    }


def aggregate_macro(task_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Macro (task-level average) P/R/F1/FNR."""
    if not task_results:
        return {
            "tasks": 0,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "fnr": 0.0,
        }
    n = len(task_results)
    return {
        "tasks": n,
        "precision": sum(float(r["precision"]) for r in task_results) / n,
        "recall": sum(float(r["recall"]) for r in task_results) / n,
        "f1": sum(float(r["f1"]) for r in task_results) / n,
        "fnr": sum(float(r["fnr"]) for r in task_results) / n,
    }
