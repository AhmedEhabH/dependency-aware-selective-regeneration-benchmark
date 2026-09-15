"""Baseline rankers B0–B4 (deterministic, zero-LLM).

All rankers are pure functions of parent-visible inputs (intent text, candidate
metadata, parent-only corpus text, frozen per-case dependency graph) plus a
frozen combination rule. The hidden proxy never appears in a ranking input.

Frozen rules (defined BEFORE any validation result is observed):

- seed(case) = candidates whose path/identifier/class/function token set
  intersects the intent token set (the B2 lexical-overlap basis). If empty,
  Graph@K / Hybrid@K have **no defensible non-leaking seed signal** and return
  an empty ranking for that case (documented, never invented).
- Hybrid@K score = 0.5*Nm(BM25) + 0.5*Ng(graph), with Nm = min-max normalised
  BM25 score over candidates and Ng = (1+maxd-d)/(1+maxd) for reachable, 0 for
  unreachable/seedless. alpha = 0.5 frozen.
- Tie-breaks are deterministic: descending score, then ascending repr(path).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from .bm25 import BM25Index
from .corpus import CandidateCorpus
from .tokenize import token_set, tokenize, tokenize_path

BASELINES: tuple[str, ...] = (
    "random",
    "bm25",
    "path_token",
    "graph",
    "hybrid",
)

K_VALUES: tuple[int, ...] = (1, 3, 5, 10)

HYBRID_ALPHA = 0.5

# A candidate-universe record: {path, module, classes, functions, ...}.
CandidateRecord = dict[str, object]


def _string_list(rec: CandidateRecord, key: str) -> list[str]:
    """Safely extract a list of strings (e.g. classes/functions) from a record."""
    value = rec.get(key)
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value if isinstance(x, str)]
    if isinstance(value, str):
        return [value]
    return []


def _record_tokens(rec: CandidateRecord, path: str) -> set[str]:
    """Deterministic candidate token set from path + module + classes/functions."""
    tokens = set(tokenize_path(path))
    tokens.update(t for t in token_set(str(rec.get("module", ""))) if t)
    for key in ("classes", "functions"):
        for name in _string_list(rec, key):
            tokens.update(t for t in token_set(name) if t)
    return tokens


@dataclass(frozen=True)
class SeedEligibility:
    """Deterministic seed eligibility (B3 graph seed rule)."""

    seed_paths: tuple[str, ...]
    eligible: bool

    @property
    def reason(self) -> str:
        return (
            "no_defensible_seed_signal_stop_and_document" if not self.eligible else "seeds_ok"
        )


def compute_seed_paths(
    *,
    intent_text: str,
    candidate_paths: tuple[str, ...],
    candidate_records: tuple[CandidateRecord, ...],
) -> SeedEligibility:
    """Frozen non-leaking seed rule: intent-token ∩ candidate-token != ∅.

    Candidate token set = path segments + module segments + classes +
    functions (all parent-visible metadata). An empty intersection means there
    is NO defensible seed signal for the graph/hybrid baselines on this case;
    Graph@K/Hybrid@K then return an empty ranking (documented).
    """
    intent_tokens = token_set(intent_text)
    records_by_path = {str(r.get("path", "")): r for r in candidate_records}
    seeds: list[str] = []
    for path in sorted(set(candidate_paths)):
        rec = records_by_path.get(path, {})
        candidate_tokens = _record_tokens(rec, path)
        if candidate_tokens & intent_tokens:
            seeds.append(path)
    return SeedEligibility(
        seed_paths=tuple(sorted(set(seeds))),
        eligible=bool(seeds),
    )


def _adjacency(graph_edges: tuple[tuple[str, str], ...]) -> dict[str, set[str]]:
    adj: dict[str, set[str]] = {}
    for src, dst in graph_edges:
        adj.setdefault(src, set()).add(dst)
        adj.setdefault(dst, set()).add(src)
    return adj


def _bfs_distances(seeds: set[str], graph_edges: tuple[tuple[str, str], ...]) -> dict[str, int]:
    adj = _adjacency(graph_edges)
    dist: dict[str, int] = {}
    frontier: list[str] = list(seeds)
    for node in frontier:
        dist[node] = 0
    hops = 0
    while frontier:
        hops += 1
        nxt: list[str] = []
        for node in frontier:
            for neighbor in adj.get(node, set()):
                if neighbor not in dist:
                    dist[neighbor] = hops
                    nxt.append(neighbor)
        frontier = nxt
    return dist


def rank_random(
    *,
    case_id: str,
    candidate_paths: tuple[str, ...],
    seed: int,
    k: int,
) -> tuple[str, ...]:
    """B0 — deterministic seeded random ranking (matched K)."""
    rng = random.Random(f"{seed}:{case_id}")
    perm = sorted(candidate_paths)
    rng.shuffle(perm)
    return tuple(perm[:k])


def rank_bm25_from_index(
    index: BM25Index,
    *,
    intent_text: str,
    k: int,
) -> tuple[str, ...]:
    """B1 — BM25 ranking from a prebuilt index (build separated from query)."""
    return tuple(index.rank(intent_text, k=k))


def rank_bm25(
    *,
    intent_text: str,
    corpus: CandidateCorpus,
    k: int,
) -> tuple[str, ...]:
    """B1 — BM25 over the parent-commit candidate corpus vs the intent query."""
    index = BM25Index(corpus.texts)
    return rank_bm25_from_index(index, intent_text=intent_text, k=k)


def bm25_scores(corpus: CandidateCorpus, intent_text: str) -> dict[str, float]:
    """Deterministic BM25 score per candidate doc (shared by B1 and B4)."""
    index = BM25Index(corpus.texts)
    query_terms = tokenize(intent_text)
    return {doc: index.score(doc, query_terms) for doc in corpus.doc_id_set()}


def rank_path_token(
    *,
    intent_text: str,
    candidate_paths: tuple[str, ...],
    candidate_records: tuple[CandidateRecord, ...],
    k: int,
) -> tuple[str, ...]:
    """B2 — path/identifier token overlap similarity (BM25-independent).

    Score = size of (candidate token set ∩ intent token set); candidate token
    set = path segments + module + classes + functions. Ties broken by path.
    """
    intent_tokens = token_set(intent_text)
    records_by_path = {str(r.get("path", "")): r for r in candidate_records}
    scored: list[tuple[int, str]] = []
    for path in sorted(set(candidate_paths)):
        rec = records_by_path.get(path, {})
        tokens = _record_tokens(rec, path)
        scored.append((len(tokens & intent_tokens), path))
    scored.sort(key=lambda pair: (-pair[0], pair[1]))
    return tuple(path for _, path in scored[:k])


def rank_graph(
    *,
    intent_text: str,
    candidate_paths: tuple[str, ...],
    candidate_records: tuple[CandidateRecord, ...],
    graph_edges: tuple[tuple[str, str], ...],
    k: int,
) -> tuple[tuple[str, ...], tuple[str, ...], str]:
    """B3 — Graph@K from the frozen parent-only graph, seeded by intent hits.

    Returns (ranked, seeds, no_seed_reason). If the seed rule yields no seed,
    the ranking is empty and the caller documents the reason (stop rather than
    invent a signal).
    """
    eligibility = compute_seed_paths(
        intent_text=intent_text,
        candidate_paths=candidate_paths,
        candidate_records=candidate_records,
    )
    if not eligibility.eligible:
        return (), eligibility.seed_paths, eligibility.reason
    seeds = set(eligibility.seed_paths)
    dist = _bfs_distances(seeds, graph_edges)
    records_by_path = {str(r.get("path", "")): r for r in candidate_records}
    intent_tokens = token_set(intent_text)

    def lexical_overlap(path: str) -> int:
        rec = records_by_path.get(path, {})
        return len(_record_tokens(rec, path) & intent_tokens)

    ranked_candidates = sorted(
        set(candidate_paths),
        key=lambda p: (dist.get(p, -1) < 0, dist.get(p, 10**9), -lexical_overlap(p), p),
    )
    return tuple(ranked_candidates[:k]), tuple(sorted(seeds)), eligibility.reason


def rank_hybrid(
    *,
    intent_text: str,
    corpus: CandidateCorpus,
    candidate_paths: tuple[str, ...],
    candidate_records: tuple[CandidateRecord, ...],
    graph_edges: tuple[tuple[str, str], ...],
    k: int,
    alpha: float = HYBRID_ALPHA,
    bm25_scores_by_doc: dict[str, float] | None = None,
) -> tuple[tuple[str, ...], str]:
    """B4 — Hybrid@K: frozen alpha-weighted BM25 + graph signal.

    score = alpha*Nm(BM25) + (1-alpha)*Ng(graph). Ng = (1+maxd-d)/(1+maxd)
    for candidates reachable from the seed set, 0 otherwise. Seedless cases
    reduce to pure BM25 (documented). Frozen before validation.
    """
    if bm25_scores_by_doc is None:
        bm25_scores_by_doc = bm25_scores(corpus, intent_text)
    eligibility = compute_seed_paths(
        intent_text=intent_text,
        candidate_paths=candidate_paths,
        candidate_records=candidate_records,
    )
    if not eligibility.eligible:
        return rank_bm25_from_index(
            BM25Index(corpus.texts), intent_text=intent_text, k=k
        ), ("graph_seed_empty_hybrid_is_pure_bm25")

    scores: dict[str, float] = {}
    lo = min(bm25_scores_by_doc.values()) if bm25_scores_by_doc else 0.0
    hi = max(bm25_scores_by_doc.values()) if bm25_scores_by_doc else 0.0
    span = (hi - lo) or 1.0

    seeds = set(eligibility.seed_paths)
    dist = _bfs_distances(seeds, graph_edges)
    maxd = max(dist.values()) if dist else 0

    for path in set(candidate_paths):
        norm_bm25 = (bm25_scores_by_doc.get(path, 0.0) - lo) / span
        d = dist.get(path)
        norm_graph = ((1 + maxd - d) / (1 + maxd)) if d is not None else 0.0
        scores[path] = alpha * norm_bm25 + (1 - alpha) * norm_graph

    ranked = sorted(set(candidate_paths), key=lambda p: (-scores[p], p))
    return tuple(ranked[:k]), "hybrid_alpha_0.5"


@dataclass
class BaselineResult:
    baseline: str
    case_id: str
    k: int
    ranked_paths: tuple[str, ...]
    selected: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
