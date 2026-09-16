"""Omission-Risk Feature Study V1 — feature extraction (deterministic, ZERO LLM).

Feature extraction consumes ONLY parent-visible public inputs (the public case
bundle: intent, candidate universe, parent-only dependency graph) plus the
frozen cheap-baseline machinery (BM25, metadata corpus, path_token / graph /
hybrid rankers). The hidden observed-change proxy is NEVER an input here; it is
used only by :mod:`benchmark.omission_risk.labels` at evaluation time.

First-pass operationalization (pre-registered BEFORE any feature performance):
the first-pass "impact plan" is the deterministic BM25@K selection over the
metadata corpus (module + classes + functions per candidate from the public
candidate universe). Sparse-LLM plan action features (VALIDATE/HUMAN_REVIEW
counts, action entropy, model confidence/completion metadata) are DEFERRED:
they require Sparse-v2 LLM plan outputs on TRAIN/VALIDATION, which do not exist
and cannot be produced without new scientific LLM calls (spec: prefer ZERO new
LLM calls; document DEFERRED rather than call).
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from benchmark.cheap_baselines.bm25 import BM25Index
from benchmark.cheap_baselines.corpus import MetadataCorpus
from benchmark.cheap_baselines.rankers import (
    compute_seed_paths,
    rank_graph,
    rank_hybrid,
    rank_path_token,
)
from benchmark.cheap_baselines.tokenize import token_set, tokenize, tokenize_path
from benchmark.harness.interfaces import PublicCase

K_GRID: tuple[int, ...] = (3, 5, 10)
BIG_DIST: float = 1e6

# Pre-registered monotone direction of risk for each scale-like feature:
# +1 = larger value -> more omission risk; -1 = smaller value -> more risk;
# 0 = sign must be interpreted from AUROC (direction recorded analytically).
RISK_DIRECTION: dict[str, int] = {}


@dataclass(frozen=True)
class FeatureSpec:
    """One feature: name, family, description, risk direction, K-dependence."""

    name: str
    family: str
    description: str
    k_dependent: bool = False

    @property
    def direction(self) -> int:
        return RISK_DIRECTION.get(self.name, 1)


# ---------------------------------------------------------------------------
# Deterministic helpers
# ---------------------------------------------------------------------------


def _module_of(path: str) -> str:
    return path.split("/")[0] if "/" in path else path


def _adjacency(edges: tuple[tuple[str, str], ...]) -> dict[str, set[str]]:
    adj: dict[str, set[str]] = {}
    for src, dst in edges:
        adj.setdefault(src, set()).add(dst)
        adj.setdefault(dst, set()).add(src)
    return adj


def _bfs(seeds: set[str], adj: dict[str, set[str]], max_hops: int) -> dict[str, int]:
    dist: dict[str, int] = {s: 0 for s in seeds}
    frontier = list(seeds)
    for hop in range(1, max_hops + 1):
        nxt: list[str] = []
        for node in frontier:
            for nb in adj.get(node, set()):
                if nb not in dist:
                    dist[nb] = hop
                    nxt.append(nb)
        frontier = nxt
        if not frontier:
            break
    return dist


def _components(
    nodes: set[str], edges: Sequence[tuple[str, str]]
) -> int:
    adj: dict[str, set[str]] = {}
    active = set(nodes)
    for src, dst in edges:
        if src in active and dst in active:
            adj.setdefault(src, set()).add(dst)
            adj.setdefault(dst, set()).add(src)
    seen: set[str] = set()
    n_comp = 0
    for node in sorted(active):
        if node in seen:
            continue
        n_comp += 1
        stack = [node]
        seen.add(node)
        while stack:
            cur = stack.pop()
            for nb in adj.get(cur, set()):
                if nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
    return n_comp


def _norm_entropy(scores: list[float]) -> float:
    """Normalized entropy (0..1) over a score distribution."""
    total = sum(max(0.0, s) for s in scores)
    if total <= 0:
        return 0.0
    probs = [max(0.0, s) / total for s in scores]
    probs = [p for p in probs if p > 0]
    if len(probs) <= 1:
        return 0.0
    h = -sum(p * math.log(p) for p in probs)
    return h / math.log(len(probs))


def _elbow_k(scores_desc: list[float], n: int) -> int:
    """Knee of the descending score curve (max perpendicular distance to chord)."""
    if len(scores_desc) <= 2:
        return len(scores_desc)
    xs = range(len(scores_desc) - 1)
    y0 = scores_desc[0]
    y1 = scores_desc[-1]
    d0 = y0 - y1
    if d0 <= 0:
        return 1
    best_i, best_d = 0, -1.0
    for i in xs:
        y = scores_desc[i]
        dist = abs((y1 - y0) * i - (len(scores_desc) - 2) * (y0 - y)) / math.sqrt(
            (y1 - y0) ** 2 + (len(scores_desc) - 2) ** 2
        )
        if dist > best_d:
            best_d, best_i = dist, i
    return max(1, min(best_i + 1, n))


def _string_list(rec: dict[str, Any], key: str) -> list[str]:
    value = rec.get(key)
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value if isinstance(x, str)]
    if isinstance(value, str):
        return [value]
    return []


# ---------------------------------------------------------------------------
# Main extraction
# ---------------------------------------------------------------------------


def compute_scores(case: PublicCase) -> tuple[BM25Index, dict[str, float]]:
    """Build the metadata corpus + BM25 index and per-candidate scores."""
    corpus = MetadataCorpus(
        parent_commit=case.parent_commit,
        candidate_records=tuple(case.candidate_records),
    )
    index = BM25Index(corpus.texts)
    query_terms = tokenize(case.intent_text)
    scores = {doc: index.score(doc, query_terms) for doc in index.doc_ids}
    return index, scores


def _candidate_vocab(case: PublicCase) -> frozenset[str]:
    vocab: set[str] = set()
    records_by_path = {str(r.get("path", "")): r for r in case.candidate_records}
    path_set = set(case.candidate_paths)
    for path in path_set:
        rec = records_by_path.get(path, {})
        tokens = set(tokenize_path(path))
        tokens.update(t for t in token_set(str(rec.get("module", ""))) if t)
        for key in ("classes", "functions"):
            for name in _string_list(rec, key):
                tokens.update(t for t in token_set(name) if t)
        vocab.update(tokens)
    return frozenset(vocab)


def extract_features(case: PublicCase) -> dict[str, float]:
    """Compute all registered features deterministically from public inputs.

    Returns a flat dict {feature_name: value}. Deterministic given the same
    public case (frozen seed semantics not needed: everything is score/token
    based).
    """
    out: dict[str, float] = {}
    n = len(case.candidate_paths)
    out["n_candidates"] = float(n)

    # --- Family A: retrieval uncertainty (full BM25 score distribution) ------
    index, scores = compute_scores(case)
    sorted_docs = sorted(scores, key=lambda p: (-scores[p], p))
    desc_scores = [scores[d] for d in sorted_docs]
    nonneg = [max(0.0, s) for s in desc_scores]
    out["bm25_top1_score"] = desc_scores[0] if desc_scores else 0.0
    out["bm25_top1_top2_margin"] = (
        desc_scores[0] - desc_scores[1] if len(desc_scores) > 1 else 0.0
    )
    out["bm25_top3_min"] = (min(desc_scores[:3]) if desc_scores else 0.0)
    out["bm25_top10_min"] = (min(desc_scores[:10]) if desc_scores else 0.0)
    out["bm25_top3_mean"] = (
        sum(desc_scores[:3]) / min(3, len(desc_scores)) if desc_scores else 0.0
    )
    out["bm25_top10_mean"] = (
        sum(desc_scores[:10]) / min(10, len(desc_scores)) if desc_scores else 0.0
    )
    top_n = min(10, len(nonneg))
    out["bm25_top10_norm_entropy"] = (
        _norm_entropy(nonneg[:top_n]) if nonneg else 0.0
    )
    top10_sum = sum(nonneg[:10])
    out["bm25_concentration_top1"] = (
        (desc_scores[0] / top10_sum) if top10_sum > 0 else 0.0
    )
    total_all = sum(nonneg)
    if total_all > 0:
        out["bm25_concentration_herfindahl"] = sum(
            (s / total_all) ** 2 for s in nonneg
        )
    else:
        out["bm25_concentration_herfindahl"] = 0.0
    top1 = desc_scores[0] if desc_scores else 0.0
    thresh = 0.1 * top1 if top1 > 0 else 0.0
    out["bm25_relthresh_count"] = float(
        sum(1 for s in desc_scores if s >= thresh and s > 0)
    )
    out["bm25_elbow_k"] = float(_elbow_k(desc_scores, n))
    out["bm25_zero_count"] = float(sum(1 for s in desc_scores if s <= 0))
    out["bm25_positive_count"] = float(sum(1 for s in desc_scores if s > 0))
    out["bm25_nonzero_frac"] = (
        out["bm25_positive_count"] / n if n else 0.0
    )
    out["bm25_score_range"] = desc_scores[0] - desc_scores[-1] if desc_scores else 0.0
    top_heavy = (desc_scores[0] - desc_scores[min(9, len(desc_scores) - 1)])
    out["bm25_top10_skew"] = top_heavy / max(desc_scores[0], 1e-9)

    # --- Alternative rankers (needed for the disagreement family) ------------
    k_alt = 10
    graph_ranked, graph_seeds, graph_reason = rank_graph(
        intent_text=case.intent_text,
        candidate_paths=case.candidate_paths,
        candidate_records=case.candidate_records,
        graph_edges=case.graph_edges,
        k=k_alt,
    )
    pt_ranked = rank_path_token(
        intent_text=case.intent_text,
        candidate_paths=case.candidate_paths,
        candidate_records=case.candidate_records,
        k=k_alt,
    )
    corpus = MetadataCorpus(
        parent_commit=case.parent_commit,
        candidate_records=tuple(case.candidate_records),
    )
    hybrid_ranked, _hybrid_reason = rank_hybrid(
        intent_text=case.intent_text,
        corpus=corpus,
        candidate_paths=case.candidate_paths,
        candidate_records=case.candidate_records,
        graph_edges=case.graph_edges,
        k=k_alt,
    )
    bm25_rank_all = {d: i + 1 for i, d in enumerate(sorted_docs)}

    # --- Family B: first-pass vs alternative ranking disagreement ------------
    for k in K_GRID:
        p1 = set(desc_sorted_k(index, case.intent_text, k))
        gk = set(graph_ranked[: min(k, len(graph_ranked))])
        ptk = set(pt_ranked[: min(k, len(pt_ranked))])
        hyk = set(hybrid_ranked[: min(k, len(hybrid_ranked))])
        jg = _jaccard(p1, gk)
        jpt = _jaccard(p1, ptk)
        jhy = _jaccard(p1, hyk)
        out[f"disagree_jaccard_graph_k{k}"] = jg
        out[f"disagree_jaccard_pt_k{k}"] = jpt
        out[f"disagree_jaccard_hy_k{k}"] = jhy
        out[f"disagree_graph_omitted_k{k}"] = float(len(gk - p1))
        out[f"disagree_pt_omitted_k{k}"] = float(len(ptk - p1))
        out[f"disagree_hy_omitted_k{k}"] = float(len(hyk - p1))
        out[f"disagree_overlap_graph_k{k}"] = float(len(p1 & gk))
        out[f"disagree_alt_share_of_p1_k{k}"] = (
            len(p1 & gk) / len(p1) if p1 else 0.0
        )
        out[f"disagree_max_bm25_omitted_graph_k{k}"] = _max_score(
            scores, gk - p1
        )
        out[f"disagree_max_bm25_omitted_pt_k{k}"] = _max_score(scores, ptk - p1)
        out[f"disagree_graph_max_bm25_rank_k{k}"] = _max_bm25_rank(
            bm25_rank_all, gk
        )
        out[f"disagree_pt_max_bm25_rank_k{k}"] = _max_bm25_rank(
            bm25_rank_all, ptk
        )

    # --- Family C: graph structure --------------------------------------------
    adj = _adjacency(case.graph_edges)
    eligible = compute_seed_paths(
        intent_text=case.intent_text,
        candidate_paths=case.candidate_paths,
        candidate_records=case.candidate_records,
    )
    seeds = set(eligible.seed_paths)
    out["graph_seed_count"] = float(len(seeds))
    out["graph_seed_eligible"] = 1.0 if eligible.eligible else 0.0
    dist_all = _bfs(seeds, adj, max_hops=3)
    out["graph_1hop_frontier_size"] = float(
        sum(1 for s in dist_all.values() if s == 1)
    )
    out["graph_2hop_frontier_size"] = float(
        sum(1 for s in dist_all.values() if s == 2)
    )
    active = set(case.candidate_paths)
    in_edges = [
        (s, d) for s, d in case.graph_edges if s in active and d in active
    ]
    out["graph_edge_count"] = float(len(in_edges))
    out["graph_cross_module_edges"] = float(
        sum(1 for s, d in in_edges if _module_of(s) != _module_of(d))
    )
    denom_density = n * (n - 1) / 2
    out["graph_density"] = len(in_edges) / denom_density if denom_density > 0 else 0.0
    out["graph_conn_components"] = float(_components(active, in_edges))
    degrees: Counter[str] = Counter()
    for s, d in in_edges:
        degrees[s] += 1
        degrees[d] += 1
    out["graph_avg_degree"] = (2 * len(in_edges) / n) if n else 0.0
    out["graph_isolated_count"] = float(sum(1 for c in active if degrees[c] == 0))
    reachable = sum(1 for s in dist_all.values() if 0 < s <= 1)
    out["graph_candidate_expansion_ratio"] = (len(seeds) + reachable) / n if n else 0.0
    p1k = set(desc_sorted_k(index, case.intent_text, 10))
    dist_p1 = [dist_all.get(p, BIG_DIST) for p in p1k]
    finite = [d for d in dist_p1 if d < BIG_DIST]
    out["graph_p1_min_dist_seeds"] = min(finite) if finite else BIG_DIST
    out["graph_p1_mean_dist_seeds"] = (
        sum(finite) / len(finite) if finite else BIG_DIST
    )
    out["graph_p1_reachable_frac"] = len(finite) / len(p1k) if p1k else 0.0

    # --- Family E: task complexity --------------------------------------------
    intent_tokens = tokenize(case.intent_text)
    intent_set = set(intent_tokens)
    out["intent_char_len"] = float(len(case.intent_text))
    out["intent_token_count"] = float(len(intent_tokens))
    out["intent_set_size"] = float(len(intent_set))
    vocab = _candidate_vocab(case)
    hit = [t for t in intent_set if t in vocab]
    out["intent_hit_frac"] = len(hit) / len(intent_set) if intent_set else 0.0
    out["intent_identifier_like_count"] = float(len(hit))
    path_tokens: set[str] = set()
    for p in case.candidate_paths:
        path_tokens.update(tokenize_path(p))
    out["candidate_path_token_count"] = float(len(path_tokens))
    out["candidate_token_vocab_size"] = float(len(vocab))
    modules = {_module_of(p) for p in case.candidate_paths}
    out["n_modules"] = float(len(modules))
    out["module_breadth"] = len(modules) / n if n else 0.0
    locs: list[float] = []
    imps: list[float] = []
    classes_n = 0
    funcs_n = 0
    for p in case.candidate_paths:
        rec = {str(r.get("path", "")): r for r in case.candidate_records}.get(p, {})
        locs.append(float(rec.get("loc", 0) or 0))
        imps.append(float(rec.get("import_count", 0) or 0))
        classes_n += len(_string_list(rec, "classes"))
        funcs_n += len(_string_list(rec, "functions"))
    out["median_candidate_loc"] = float(sorted(locs)[len(locs) // 2]) if locs else 0.0
    out["median_candidate_import_count"] = (
        float(sorted(imps)[len(imps) // 2]) if imps else 0.0
    )
    out["candidate_class_count_total"] = float(classes_n)
    out["candidate_function_count_total"] = float(funcs_n)

    # --- Family F: first-pass plan signals (deterministic first pass) ---------
    for k in K_GRID:
        out[f"fp_density_k{k}"] = k / n if n else 0.0
    # fp_validate_count / fp_human_review_count / action entropy are constant
    # zero for a deterministic ranker first pass and are DEFERRED for the
    # Sparse-LLM plan (see module docstring).

    return out


# ---------------------------------------------------------------------------
# Small helpers used above
# ---------------------------------------------------------------------------


def desc_sorted_k(
    index: BM25Index, intent_text: str, k: int
) -> tuple[str, ...]:
    return tuple(index.rank(intent_text, k=k))


def _jaccard(a: set[str], b: set[str]) -> float:
    union = a | b
    if not union:
        return 1.0
    return len(a & b) / len(union)


def _max_score(scores: dict[str, float], paths: set[str]) -> float:
    if not paths:
        return 0.0
    return max(scores.get(p, 0.0) for p in paths)


def _max_bm25_rank(rank_all: dict[str, int], paths: set[str]) -> float:
    if not paths:
        return 0.0
    return float(max(rank_all.get(p, len(rank_all) + 1) for p in paths))


FEATURE_FAMILIES: dict[str, str] = {}


def feature_specs() -> list[FeatureSpec]:
    """Return the registered feature schema (name -> family/description)."""
    return [
        FeatureSpec("bm25_top1_score", "A_retrieval_uncertainty", "top BM25 score"),
        FeatureSpec("bm25_top1_top2_margin", "A_retrieval_uncertainty", "top1-top2 score margin"),
        FeatureSpec("bm25_top3_min", "A_retrieval_uncertainty", "min of top-3 scores"),
        FeatureSpec("bm25_top10_min", "A_retrieval_uncertainty", "min of top-10 scores"),
        FeatureSpec("bm25_top3_mean", "A_retrieval_uncertainty", "mean of top-3 scores"),
        FeatureSpec("bm25_top10_mean", "A_retrieval_uncertainty", "mean of top-10 scores"),
        FeatureSpec(
            "bm25_top10_norm_entropy",
            "A_retrieval_uncertainty",
            "normalized entropy of top-10 score distribution",
        ),
        FeatureSpec("bm25_concentration_top1", "A_retrieval_uncertainty", "top-1 share of top-10 score mass"),
        FeatureSpec(
            "bm25_concentration_herfindahl",
            "A_retrieval_uncertainty",
            "Herfindahl concentration over all scores",
        ),
        FeatureSpec("bm25_relthresh_count", "A_retrieval_uncertainty", "candidates above 10% of top-1 score"),
        FeatureSpec("bm25_elbow_k", "A_retrieval_uncertainty", "knee/adaptive-K estimate of score curve"),
        FeatureSpec("bm25_zero_count", "A_retrieval_uncertainty", "candidates with zero BM25 score"),
        FeatureSpec("bm25_positive_count", "A_retrieval_uncertainty", "candidates with positive BM25 score"),
        FeatureSpec("bm25_nonzero_frac", "A_retrieval_uncertainty", "fraction of candidates with positive score"),
        FeatureSpec("bm25_score_range", "A_retrieval_uncertainty", "range of the score distribution"),
        FeatureSpec("bm25_top10_skew", "A_retrieval_uncertainty", "top-heaviness (top1 - top10)/top1"),
        *[
            FeatureSpec(
                f"disagree_jaccard_graph_k{k}",
                "B_sparse_disagreement",
                f"Jaccard(BM25@{k}, Graph@{k})",
                True,
            )
            for k in K_GRID
        ],
        *[
            FeatureSpec(
                f"disagree_jaccard_pt_k{k}",
                "B_sparse_disagreement",
                f"Jaccard(BM25@{k}, path_token@{k})",
                True,
            )
            for k in K_GRID
        ],
        *[
            FeatureSpec(
                f"disagree_jaccard_hy_k{k}",
                "B_sparse_disagreement",
                f"Jaccard(BM25@{k}, Hybrid@{k})",
                True,
            )
            for k in K_GRID
        ],
        *[
            FeatureSpec(
                f"disagree_graph_omitted_k{k}",
                "B_sparse_disagreement",
                f"graph@{k}-selected files omitted by the first pass",
                True,
            )
            for k in K_GRID
        ],
        *[
            FeatureSpec(
                f"disagree_pt_omitted_k{k}",
                "B_sparse_disagreement",
                f"path_token@{k}-selected files omitted by the first pass",
                True,
            )
            for k in K_GRID
        ],
        *[
            FeatureSpec(
                f"disagree_hy_omitted_k{k}",
                "B_sparse_disagreement",
                f"hybrid@{k}-selected files omitted by the first pass",
                True,
            )
            for k in K_GRID
        ],
        *[
            FeatureSpec(
                f"disagree_overlap_graph_k{k}",
                "B_sparse_disagreement",
                f"|BM25@{k} and Graph@{k}|",
                True,
            )
            for k in K_GRID
        ],
        *[
            FeatureSpec(
                f"disagree_alt_share_of_p1_k{k}",
                "B_sparse_disagreement",
                f"share of first pass also selected by Graph@{k}",
                True,
            )
            for k in K_GRID
        ],
        *[
            FeatureSpec(
                f"disagree_max_bm25_omitted_graph_k{k}",
                "B_sparse_disagreement",
                f"max BM25 score among graph-selected, first-pass-omitted files @{k}",
                True,
            )
            for k in K_GRID
        ],
        *[
            FeatureSpec(
                f"disagree_max_bm25_omitted_pt_k{k}",
                "B_sparse_disagreement",
                f"max BM25 score among path_token-selected, first-pass-omitted files @{k}",
                True,
            )
            for k in K_GRID
        ],
        *[
            FeatureSpec(
                f"disagree_graph_max_bm25_rank_k{k}",
                "B_sparse_disagreement",
                f"max BM25 rank among graph-selected files @{k}",
                True,
            )
            for k in K_GRID
        ],
        *[
            FeatureSpec(
                f"disagree_pt_max_bm25_rank_k{k}",
                "B_sparse_disagreement",
                f"max BM25 rank among path_token-selected files @{k}",
                True,
            )
            for k in K_GRID
        ],
        FeatureSpec("graph_seed_count", "C_graph", "number of lexical graph seeds"),
        FeatureSpec("graph_seed_eligible", "C_graph", "1 if a defensible seed set exists"),
        FeatureSpec("graph_1hop_frontier_size", "C_graph", "nodes at graph distance 1 from seeds"),
        FeatureSpec("graph_2hop_frontier_size", "C_graph", "nodes at graph distance 2 from seeds"),
        FeatureSpec("graph_edge_count", "C_graph", "edges within the candidate set"),
        FeatureSpec("graph_cross_module_edges", "C_graph", "edges crossing module boundaries"),
        FeatureSpec("graph_density", "C_graph", "edge density over candidate pairs"),
        FeatureSpec("graph_conn_components", "C_graph", "weakly connected components"),
        FeatureSpec("graph_avg_degree", "C_graph", "mean graph degree of candidates"),
        FeatureSpec("graph_isolated_count", "C_graph", "candidates with no graph edges"),
        FeatureSpec("graph_candidate_expansion_ratio", "C_graph", "(seeds + 1-hop)/N"),
        FeatureSpec("graph_p1_min_dist_seeds", "C_graph", "min graph distance of first-pass files to seeds"),
        FeatureSpec("graph_p1_mean_dist_seeds", "C_graph", "mean graph distance of first-pass files to seeds"),
        FeatureSpec("graph_p1_reachable_frac", "C_graph", "fraction of first-pass files reachable from seeds"),
        FeatureSpec("intent_char_len", "E_task_complexity", "intent length in characters"),
        FeatureSpec("intent_token_count", "E_task_complexity", "intent token count"),
        FeatureSpec("intent_set_size", "E_task_complexity", "unique intent tokens"),
        FeatureSpec("intent_hit_frac", "E_task_complexity", "fraction of intent tokens hitting candidate vocabulary"),
        FeatureSpec(
            "intent_identifier_like_count",
            "E_task_complexity",
            "intent tokens that are candidate identifiers",
        ),
        FeatureSpec("candidate_path_token_count", "E_task_complexity", "distinct path-segment tokens over candidates"),
        FeatureSpec("candidate_token_vocab_size", "E_task_complexity", "distinct candidate vocabulary size"),
        FeatureSpec("n_modules", "E_task_complexity", "distinct modules"),
        FeatureSpec("module_breadth", "E_task_complexity", "modules / candidates"),
        FeatureSpec("median_candidate_loc", "E_task_complexity", "median candidate LOC"),
        FeatureSpec("median_candidate_import_count", "E_task_complexity", "median candidate import count"),
        FeatureSpec("candidate_class_count_total", "E_task_complexity", "total classes across candidates"),
        FeatureSpec("candidate_function_count_total", "E_task_complexity", "total functions across candidates"),
        FeatureSpec("n_candidates", "E_task_complexity", "candidate universe size"),
        *[
            FeatureSpec(
                f"fp_density_k{k}",
                "F_sparse_plan",
                f"first-pass density K/N at K={k}",
                True,
            )
            for k in K_GRID
        ],
    ]


def feature_names() -> list[str]:
    return [s.name for s in feature_specs()]
