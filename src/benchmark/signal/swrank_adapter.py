"""Frozen file-level adapter for the SweRankEmbed-Small signal (T3, ZERO API).

FREEZED BEFORE outcomes (2026-09-19). ONE aggregation rule only:

  For every production code unit f in a file:
      score(f) = cosine(issue_embedding, code_embedding_f)
  For file F:
      score(F) = MAX over score(f), f in F

Rationale (frozen): one strongly relevant symbol should be enough to make the
file suspicious. No mean/top3/weighted alternatives are evaluated.

Ranking (Route-B matched, frozen):
  - candidate pool = omitted files (universe minus Sparse write set)
  - sort descending by file score, tie-break by normalized repository path
    ascending (matches the frozen Route-B tie-break convention)
  - the hidden proxy never enters parsing, embedding, scoring, ranking, or
    top-K selection.

The aggregation and ranking are pure functions over an injected
(unit -> embedding) map so tests can exercise them without the model.
"""
from __future__ import annotations

import math

import numpy as np


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity of two 1-D float arrays (L2-normalized)."""
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(float(np.dot(a, b)) / (na * nb))


def aggregate_file_score(unit_scores: list[tuple[str, float]]) -> float:
    """Frozen file aggregation: MAX over code units.

    unit_scores = list of (unit_key, cosine_score). Empty list -> -inf so an
    un-representable file can never win a tie (deterministic boundary).
    """
    if not unit_scores:
        return -math.inf
    return max(s for _, s in unit_scores)


def score_units(unit_embeddings: dict[str, np.ndarray], query_embedding: np.ndarray) -> dict[str, float]:
    """Per-unit cosine scores given a unit_key -> embedding map and a query embedding."""
    return {key: cosine(query_embedding, emb) for key, emb in unit_embeddings.items()}


def rank_files(file_scores: dict[str, float], universe: list[str],
               write_set: frozenset[str]) -> list[str]:
    """Rank the OMITTED candidate files (universe minus write_set).

    Sorting key: descending score, then ascending normalized path
    (string comparison on the slash-normalized path — identical to the frozen
    Route-B tie-break convention in src/benchmark/recall/rankers.py).
    """
    pool = [p for p in universe if p not in write_set]
    pool.sort(key=lambda p: (-file_scores.get(p, -math.inf), p))
    return pool


def top_k_from_rank(ranked: list[str], k: int) -> list[str]:
    return ranked[: max(0, min(k, len(ranked)))]
