# ruff: noqa: N803, N806
"""Source-specific oracle recall ceilings + complementarity (Sections 4-5).

For each cheap source, computes a deterministic Oracle-Recall ceiling: the
maximum FNs the source could surface at budget K IF its ranking were perfect
among the candidates the source can emit (its deterministic candidate pool).
Pool membership is derived from parent-visible evidence only; the hidden proxy
never enters a pool. This is an oracle characterization of candidate
availability, not a deployment method.

Sources:
  BM25, PATH_TOKEN, GRAPH_1HOP (undirected neighbors of seeds),
  GRAPH_REVERSE_1HOP (consumers: import a seed), GRAPH_FORWARD_1HOP
  (providers: imported by a seed), GRAPH_2HOP, GRAPH_REVERSE_2HOP,
  HISTORY_COCHANGE (djangocms only; Saleor UNAVAILABLE),
  STRUCTURAL_SIBLING (same parent dir / module as a seed), and unions.

For budget K in {1,3,5,10,ALL}, reports per repo:
  - oracle FN recovery count and ORR ceiling
  - marginal gain beyond the current Route-B composite (actual, deterministic)
  - overlap with Route-B recovered FNs
  - unique FN recovery contribution
  - candidate queue size / inspections per task
  - expected Random recovery under the same queue size
"""
from __future__ import annotations

from dataclasses import dataclass

from .data import RecallTask
from .rankers import rank_composite

BUDGETS = (1, 3, 5, 10, "ALL")

SOURCES = (
    "BM25",
    "PATH_TOKEN",
    "GRAPH_1HOP",
    "GRAPH_REVERSE_1HOP",
    "GRAPH_FORWARD_1HOP",
    "GRAPH_2HOP",
    "GRAPH_REVERSE_2HOP",
    "HISTORY_COCHANGE",
    "STRUCTURAL_SIBLING",
    "UNION_1HOP_2HOP",
    "UNION_CONSUMER_PROVIDER",
    "UNION_2HOP_COCHANGE_SIBLING",
    "UNION_ALL",
)


@dataclass(frozen=True)
class SourcePool:
    name: str
    pool: frozenset[str]  # candidate paths the source can emit


def _seeds(task: RecallTask) -> frozenset[str]:
    return task.seeds


def _undirected_neighbors(task: RecallTask) -> frozenset[str]:
    return frozenset(c["path"] for c in task.candidates if c["dist"] == 1)


def _consumers(task: RecallTask) -> frozenset[str]:
    return frozenset(c["path"] for c in task.candidates if c["consumer"])


def _providers(task: RecallTask) -> frozenset[str]:
    return frozenset(c["path"] for c in task.candidates if c["provider"])


def _dist2(task: RecallTask) -> frozenset[str]:
    return frozenset(c["path"] for c in task.candidates if c["dist"] == 2)


def _reverse_2hop(task: RecallTask) -> frozenset[str]:
    """Consumers-of-consumers: candidate c with c->x->s for some seed s."""
    # Approximate with parent-visible flag: candidates whose consumer flag is
    # set and which also have a 2-hop reverse path. We conservatively use
    # candidates at undirected distance 2 OR consumers at distance 2.
    out: set[str] = set()
    for c in task.candidates:
        if c["dist"] == 2 and c["consumer"]:
            out.add(c["path"])
    return frozenset(out)


def _cochange(task: RecallTask) -> frozenset[str]:
    if not task.candidates:
        return frozenset()
    avail = task.candidates[0]["history_available"]
    if not avail:
        return frozenset()
    return frozenset(c["path"] for c in task.candidates if c["co_change"] > 0)


def _siblings(task: RecallTask) -> frozenset[str]:
    seeds = _seeds(task)
    seed_dirs = {task.universe_records.get(s, {}).get("parent_dir", "") for s in seeds}
    seed_modules = {task.universe_records.get(s, {}).get("module", "") for s in seeds}
    out: set[str] = set()
    for c in task.candidates:
        if c["parent_dir"] in seed_dirs or (c.get("module") and c["module"] in seed_modules):
            out.add(c["path"])
    return frozenset(out)


def _union(*pools: frozenset[str]) -> frozenset[str]:
    out: set[str] = set()
    for p in pools:
        out |= set(p)
    return frozenset(out)


def task_source_pool(task: RecallTask, source: str) -> SourcePool:
    if source == "BM25" or source == "PATH_TOKEN":
        return SourcePool(source, frozenset(c["path"] for c in task.candidates))
    if source == "GRAPH_1HOP":
        return SourcePool(source, _undirected_neighbors(task))
    if source == "GRAPH_REVERSE_1HOP":
        return SourcePool(source, _consumers(task))
    if source == "GRAPH_FORWARD_1HOP":
        return SourcePool(source, _providers(task))
    if source == "GRAPH_2HOP":
        return SourcePool(source, _dist2(task))
    if source == "GRAPH_REVERSE_2HOP":
        return SourcePool(source, _reverse_2hop(task))
    if source == "HISTORY_COCHANGE":
        return SourcePool(source, _cochange(task))
    if source == "STRUCTURAL_SIBLING":
        return SourcePool(source, _siblings(task))
    if source == "UNION_1HOP_2HOP":
        return SourcePool(source, _union(_undirected_neighbors(task), _dist2(task)))
    if source == "UNION_CONSUMER_PROVIDER":
        return SourcePool(source, _union(_consumers(task), _providers(task)))
    if source == "UNION_2HOP_COCHANGE_SIBLING":
        return SourcePool(source, _union(_dist2(task), _cochange(task), _siblings(task)))
    if source == "UNION_ALL":
        return SourcePool(
            source,
            _union(
                _undirected_neighbors(task), _dist2(task), _consumers(task),
                _providers(task), _cochange(task), _siblings(task),
            ),
        )
    raise KeyError(source)


def _fn_set(task: RecallTask) -> frozenset[str]:
    return frozenset(c["path"] for c in task.candidates if c["is_missed_positive"])


def _route_b_recovered(task: RecallTask, K: int) -> set[str]:
    ranked = rank_composite(task)
    B_eff = min(K, task.omitted_size)
    return set(ranked[:B_eff])


def oracle_ceiling(task: RecallTask, pool: frozenset[str], K: int | str) -> tuple[int, int]:
    """(ceiling_fn_recovery, queue_size) under budget K for a candidate pool.

    ceiling = the max FNs the source could surface within K inspections if it
    ranked its pool perfectly = min(K, |pool ∩ FN|) per task, where K="ALL"
    means the entire pool is inspected.
    """
    fns = _fn_set(task)
    pool_fns = pool & fns
    if K == "ALL":
        return len(pool_fns), len(pool)
    k = int(K)
    q = min(k, len(pool))
    return min(k, len(pool_fns)), q


def source_stats(task: RecallTask, source: str, K: int | str) -> dict:
    pool = task_source_pool(task, source).pool
    n_fn_total = task.n_missed
    n_fns_in_pool = len(pool & _fn_set(task))
    ceiling, queue_size = oracle_ceiling(task, pool, K)
    route_b_budget = task.omitted_size if K == "ALL" else int(K)
    route_b_rec = _route_b_recovered(task, route_b_budget)
    route_b_fn = route_b_rec & _fn_set(task)
    overlap = len(pool & route_b_fn)
    unique = ceiling - overlap if ceiling >= overlap else 0
    N = task.omitted_size
    expected_random = (queue_size * n_fn_total / N) if N else 0.0
    return {
        "case_id": task.case_id,
        "repository": task.repository,
        "source": source,
        "K": K,
        "n_fn_total": n_fn_total,
        "n_fns_in_pool": n_fns_in_pool,
        "oracle_ceiling": ceiling,
        "queue_size": queue_size,
        "route_b_recovered_fns": len(route_b_fn),
        "overlap_with_route_b": overlap,
        "unique_fns": unique,
        "expected_random": expected_random,
    }
