# ruff: noqa: N803, N806
"""Recall ADD-queue candidates + evaluation (T3, ZERO API).

Defines at most three simple deterministic ADD queues (Section 6) and the
matched-budget evaluation helpers (Sections 7-8). The queue rankers are pure
functions of parent-visible features; the hidden proxy is only used to score
recovery after the fact.

Candidates (frozen, DEVELOPMENT; no hidden-proxy features; fixed tie-break
desc score then asc path; budgets K in {1,3,5,10}):
  Q1 BM25 + ReverseDependency        : score = bm25 + consumer (downstream)
  Q2 BM25 + ProviderConsumerSupport  : score = bm25 + consumer + provider
  Q3 BM25 + ComplementaryUnion       : score = bm25 + 2hop + co-change + sibling
"""
from __future__ import annotations

from .data import RecallTask
from .rankers import recovery

BUDGETS = (1, 3, 5, 10)


def _rank(task: RecallTask, key_fn: object) -> list[str]:
    cands = list(task.candidates)
    key = key_fn if callable(key_fn) else (lambda _c: 0.0)
    cands.sort(key=lambda c: (-float(key(c)), c["path"]))
    return [c["path"] for c in cands]


def rank_bm25_reverse_dependency(task: RecallTask) -> list[str]:
    """Q1 BM25 + ReverseDependency: bm25 + binary downstream-consumer flag."""
    return _rank(task, lambda c: c["bm25"] + float(c["consumer"]))


def rank_bm25_provider_consumer(task: RecallTask) -> list[str]:
    """Q2 BM25 + ProviderConsumerSupport: bm25 + consumer + provider."""
    return _rank(task, lambda c: c["bm25"] + float(c["consumer"]) + float(c["provider"]))


def rank_bm25_complementary_union(task: RecallTask) -> list[str]:
    """Q3 BM25 + ComplementaryUnion: bm25 + 2hop + co-change + sibling."""
    return _rank(
        task,
        lambda c: c["bm25"]
        + float(c["dist"] == 2)
        + float(c["co_change"] > 0 and c["history_available"])
        + float(c["sibling"]),
    )


QUEUE_RANKERS = {
    "BM25+ReverseDependency": rank_bm25_reverse_dependency,
    "BM25+ProviderConsumerSupport": rank_bm25_provider_consumer,
    "BM25+ComplementaryUnion": rank_bm25_complementary_union,
}


def queue_recovery(task: RecallTask, queue_name: str, B: int) -> dict:
    ranked = QUEUE_RANKERS[queue_name](task)
    r = recovery(task, ranked, B)
    r["queue"] = queue_name
    return r


def _top_added(task: RecallTask, queue_name: str, B: int) -> list[str]:
    ranked = QUEUE_RANKERS[queue_name](task)
    B_eff = min(B, task.omitted_size)
    return ranked[:B_eff]


def naive_union_metrics(task: RecallTask, queue_name: str, B: int) -> dict:
    """Final P/R/F1 if the top-B queue files are simply unioned into Sparse."""
    added = set(_top_added(task, queue_name, B))
    final = set(task.write_set) | added
    pos = set(task.proxy)
    tp = len(final & pos)
    fp = len(final - pos)
    fn = len(pos - final)
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": round(p, 4),
            "recall": round(r, 4), "f1": round(f1, 4)}


def oracle_reviewer_metrics(task: RecallTask, queue_name: str, B: int) -> dict:
    """Perfect-reviewer simulation: only the true FNs among top-B are accepted."""
    top = _top_added(task, queue_name, B)
    fn_set = set(task.proxy) - set(task.write_set)
    accepted = {p for p in top if p in fn_set}
    final = set(task.write_set) | accepted
    pos = set(task.proxy)
    tp = len(final & pos)
    fp = len(final - pos)
    fn = len(pos - final)
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": round(p, 4),
            "recall": round(r, 4), "f1": round(f1, 4),
            "n_accepted": len(accepted), "n_fns_in_top": sum(1 for p in top if p in fn_set)}
