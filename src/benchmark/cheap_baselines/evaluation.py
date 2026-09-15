"""Evaluation for cheap baselines (frozen P1 binary evaluator semantics).

Reuses ``p1_evaluation.p1_selection_metrics`` — the SAME evaluator used by
P1 (Full-v2/Sparse-v2) and P5 LocAgent common evaluator. Predicted positive
file = selected file (the top-K ranked file set); reference = the case's
observed changed-production-Python proxy within U_t. Metrics: TP/FP/FN,
P/R/F1/FNR, micro and macro (task-level) aggregations.
"""

from __future__ import annotations

from typing import Any

from benchmark.real_commits import p1_evaluation as p1

EVALUATOR_VERSION: str = p1.P1_PROTOCOL_VERSION


def per_task_eval(
    *,
    case_id: str,
    selected_paths: tuple[str, ...],
    proxy_paths: tuple[str, ...],
) -> dict[str, Any]:
    """Evaluate one task using the frozen binary evaluator semantics."""
    predicted = set(selected_paths)
    proxy = set(proxy_paths)
    metrics = p1.p1_selection_metrics(predicted, proxy)
    return {
        "case_id": case_id,
        "selected_count": len(predicted),
        "proxy_count": len(proxy),
        "tp": int(metrics["tp"]),
        "fp": int(metrics["fp"]),
        "fn": int(metrics["fn"]),
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1": metrics["f1"],
        "fnr": metrics["fnr"],
        "full_recall": bool(metrics["full_recall"]),
    }


def aggregate_micro_metrics(task_results: list[dict[str, Any]]) -> dict[str, Any]:
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


def aggregate_macro_metrics(task_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Macro (task-level average) P/R/F1/FNR. Only tasks with a non-empty
    reference contribute per-metric averages (division by count)."""
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
