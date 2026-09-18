# ruff: noqa: N803, N806
"""Deterministic rankers/recovery helpers for the recall study (T3, ZERO API).

These reproduce the frozen Route-B V2 protocol metrics (macro ORR) and provide
the source-specific rankers used by the recall-ceiling analysis and the ADD
queues. All ranking keys are parent-visible (BM25, path-token, graph flags);
the hidden proxy is never a ranking input.
"""
from __future__ import annotations

from .data import RecallTask


def _ranked_omitted(task: RecallTask, key_fn: object) -> list[str]:
    cands = list(task.candidates)
    # Match frozen Route-B tie-break: descending score, then ascending path.
    key = key_fn if callable(key_fn) else (lambda _c: 0.0)
    cands.sort(key=lambda c: (-float(key(c)), c["path"]))
    return [c["path"] for c in cands]


def rank_bm25(task: RecallTask) -> list[str]:
    return _ranked_omitted(task, lambda c: c["bm25"])


def rank_path_token(task: RecallTask) -> list[str]:
    # pt_rank_pct smaller = better; invert.
    return _ranked_omitted(task, lambda c: -c["pt_rank_pct"])


def rank_composite(task: RecallTask) -> list[str]:
    """Route-B composite = normalized BM25 + binary graph-neighbor."""
    return _ranked_omitted(task, lambda c: c["bm25"] + c["graph_neighbor"])


def recovery(task: RecallTask, ranked: list[str], B: int, max_budget: int = 10) -> dict:
    """ORR/quantities for a fixed ranking at budget B (B clipped to omitted)."""
    M = task.n_missed
    N = task.omitted_size
    if M == 0:
        return {"recovered": 0, "total_missed": 0, "orr": 0.0, "expected_random": 0.0,
                "N": N, "B": B, "queue_size": 0}
    B_eff = min(B, max_budget, N)
    top = set(ranked[:B_eff])
    rec = sum(1 for c in task.candidates if c["path"] in top and c["is_missed_positive"])
    exp_random = B_eff * M / N if N else 0.0
    return {"recovered": rec, "total_missed": M, "orr": rec / M,
            "expected_random": exp_random / M, "N": N, "B": B,
            "queue_size": B_eff}


def composite_recovery(tasks: list[RecallTask], B: int) -> dict:
    """Frozen Route-B composite fixed-B macro ORR over a task list."""
    rows = [recovery(t, rank_composite(t), B) for t in tasks]
    macro = sum(r["orr"] for r in rows) / len(rows) if rows else 0.0
    total_rec = sum(r["recovered"] for r in rows)
    total_missed = sum(r["total_missed"] for r in rows)
    micro = total_rec / total_missed if total_missed else 0.0
    return {
        "macro_orr": round(macro, 4),
        "micro_orr": round(micro, 4),
        "recovered": int(total_rec),
        "total_missed": int(total_missed),
        "expected_random_macro": round(sum(r["expected_random"] for r in rows) / len(rows), 4) if rows else 0.0,
    }
