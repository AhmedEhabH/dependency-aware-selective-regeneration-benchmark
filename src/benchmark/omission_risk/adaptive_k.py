"""Omission-Risk Feature Study V1 — adaptive retrieval depth (simple rules).

Do NOT freeze K=3 or K=10. Test whether cheap query-specific signals (visible
score distributions only) can choose a retrieval depth. Rules depend ONLY on
the BM25 score distribution of the task (public). No test-set tuning.

Pre-registered rules:
- fixed K=3
- fixed K=10
- adaptive_margin:  K* = #{scores >= 0.3 * top1}, clipped to [3, 10]
- adaptive_elbow:   K* = knee of the descending score curve, clipped to [3, 10]
- adaptive_entropy: K* = round(3 + 7 * top10_norm_entropy), clipped to [3, 10]

Evaluation (TRAIN / VALIDATION separately, evaluation-time proxy only):
- impact correctness (F1, recall, precision), average K, FNR, query cost (= K).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def adaptive_margin(desc_scores: list[float]) -> int:
    """K* = #{scores >= 0.3*top1} clipped to [3,10]."""
    top1 = desc_scores[0] if desc_scores else 0.0
    thresh = 0.3 * top1 if top1 > 0 else 0.0
    k = sum(1 for s in desc_scores if s >= thresh and s > 0)
    return max(3, min(10, k))


def adaptive_elbow(desc_scores: list[float]) -> int:
    """K* = knee point of the descending score curve clipped to [3,10]."""
    from benchmark.omission_risk.features import _elbow_k

    return max(3, min(10, _elbow_k(desc_scores, len(desc_scores))))


def adaptive_entropy(desc_scores: list[float]) -> int:
    """K* = round(3 + 7 * normalized entropy of top-10 scores) clipped to [3,10]."""
    from benchmark.omission_risk.features import _norm_entropy

    top_n = min(10, len(desc_scores))
    ent = _norm_entropy([max(0.0, s) for s in desc_scores[:top_n]])
    return max(3, min(10, int(round(3 + 7 * ent))))


ADAPTIVE_RULES: dict[str, Callable[[list[float]], int]] = {
    "fixed_3": lambda _scores: 3,
    "fixed_10": lambda _scores: 10,
    "adaptive_margin": adaptive_margin,
    "adaptive_elbow": adaptive_elbow,
    "adaptive_entropy": adaptive_entropy,
}


def choose_k(rule: str, desc_scores: list[float]) -> int:
    if rule not in ADAPTIVE_RULES:
        raise KeyError(f"unknown adaptive rule {rule!r}")
    return ADAPTIVE_RULES[rule](desc_scores)


def evaluate_rule(
    rule: str,
    *,
    sorted_scores_by_case: dict[str, list[float]],
    ranked_by_case_k: dict[tuple[str, int], list[str]],
    case_ids: list[str],
    proxy_by_case: dict[str, set[str]],
) -> dict[str, Any]:
    """Evaluate one rule over cases with the proxy (evaluation time only)."""
    k_stats: list[int] = []
    total_tp = 0
    total_fp = 0
    total_fn = 0
    for cid in case_ids:
        scores = sorted_scores_by_case[cid]
        k = choose_k(rule, scores)
        k_stats.append(k)
        ranked = ranked_by_case_k.get((cid, k), [])[:k]
        selected = set(ranked)
        proxy = proxy_by_case[cid]
        tp = len(selected & proxy)
        fp = len(selected - proxy)
        fn = len(proxy - selected)
        total_tp += tp
        total_fp += fp
        total_fn += fn
    prec = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0.0
    rec = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0.0
    f1 = (
        2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    )
    fnr = total_fn / (total_tp + total_fn) if (total_tp + total_fn) else 0.0
    return {
        "rule": rule,
        "n_tasks": len(case_ids),
        "avg_k": sum(k_stats) / len(k_stats) if k_stats else 0.0,
        "sum_k": sum(k_stats),
        "tp": total_tp,
        "fp": total_fp,
        "fn": total_fn,
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "fnr": fnr,
        "query_cost_sum_k": sum(k_stats),
    }
