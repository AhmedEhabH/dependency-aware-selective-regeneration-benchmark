"""Minimal deterministic BM25 (Okapi BM25) implementation.

Pure-Python, zero external dependencies, deterministic. Used only for the
cheap lexical baseline B1. Documents are the parent-commit file contents
rendered by :mod:`benchmark.cheap_baselines.corpus`; the query is the visible
change intent.
"""

from __future__ import annotations

import math
from collections import Counter

from .tokenize import tokenize

K1 = 1.5
B = 0.75
EPS = 1e-9


def _idf(doc_freq: int, n_docs: int) -> float:
    return math.log((n_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1.0)


class BM25Index:
    """Deterministic BM25 index over a fixed set of documents."""

    def __init__(self, corpus: dict[str, str]) -> None:
        self.doc_ids = tuple(sorted(corpus))
        self._df: Counter[str] = Counter()
        self._term_lists: dict[str, tuple[str, ...]] = {}
        self._lengths: dict[str, int] = {}
        self.avgdl = 0.0

        if not self.doc_ids:
            return
        total_len = 0
        for doc_id, text in corpus.items():
            terms = tokenize(text)
            self._term_lists[doc_id] = terms
            self._lengths[doc_id] = len(terms)
            total_len += len(terms)
            self._df.update(set(terms))
        self.avgdl = total_len / max(1, len(self.doc_ids))

    @property
    def n_docs(self) -> int:
        return len(self.doc_ids)

    def score(self, doc_id: str, query_terms: tuple[str, ...]) -> float:
        if self.n_docs == 0:
            return 0.0
        terms = self._term_lists.get(doc_id, ())
        doc_len = self._lengths.get(doc_id, 0)
        freq = Counter(t for t in terms)
        score = 0.0
        for term in set(query_terms):
            tf = freq.get(term, 0)
            if tf == 0:
                continue
            idf = _idf(self._df.get(term, 0), self.n_docs)
            denom = tf + K1 * (1 - B + B * (doc_len / max(1.0, self.avgdl)))
            score += idf * (tf * (K1 + 1)) / (denom + EPS)
        return score

    def rank(self, query: str, *, k: int | None = None) -> list[str]:
        query_terms = tokenize(query)
        scored: list[tuple[float, str]] = []
        for doc_id in self.doc_ids:
            scored.append((self.score(doc_id, query_terms), doc_id))
        scored.sort(key=lambda pair: (-pair[0], pair[1]))
        ranked = [doc_id for _, doc_id in scored]
        return ranked[:k] if k is not None else ranked
