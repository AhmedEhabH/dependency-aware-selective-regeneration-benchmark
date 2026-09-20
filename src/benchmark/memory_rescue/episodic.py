"""PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2 — Channel B episodic change memory.

Deterministic non-parametric memory of prior repository changes (frozen,
mission §11-§13):

- Corpus = parent-visible production-changing commit documents; each document
  is the commit subject + body (NO web/API enrichment, NO issue text unless
  already local + parent-visible + leakage-free; none is available, so commit
  text only).
- Retrieval = deterministic BM25 over HISTORICAL CHANGE TEXT (NOT source-code
  BM25). Query = the exact frozen parent-visible task intent already used by
  the benchmark. Retrieved top `EPISODIC_TOP_CHANGES = 10` episodes (frozen,
  NO K sweep).
- episode_similarity(f) = maximum normalized BM25 score among retrieved
  episodes that modified f; 0 if no retrieved episode touched f.
  Normalization = raw score / max raw score within the retrieved top-10.
- episode_hit_count(f)   = number of retrieved top-10 episodes touching f
  (DESCRIPTIVE ONLY; NOT a V2 model feature).

Reuses the deterministic BM25 implementation from benchmark.cheap_baselines
(identical tokenizer and Okapi BM25 — determinism by construction).
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))
if str(PROJECT_DIR / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR / "src"))

from benchmark.cheap_baselines.bm25 import BM25Index  # noqa: E402
from benchmark.cheap_baselines.tokenize import tokenize  # noqa: E402

EPISODIC_TOP_CHANGES = 10


def retrieve_top(documents: dict[str, str], query: str,
                 k: int = EPISODIC_TOP_CHANGES) -> list[str]:
    """Deterministic BM25 top-k episode SHAs for the query (frozen §12)."""
    index = BM25Index(documents)
    return index.rank(query, k=k)


def episode_signals(
    episode_records: list[dict],
    query: str,
    k: int = EPISODIC_TOP_CHANGES,
) -> dict[str, dict]:
    """Per-file episodic signals from the top-k retrieved episodes.

    episode_records: parent-visible production-changing commit records, each
    {"sha", "subject", "body", "paths": (path, ...)}. The top-k retrieved
    episodes are selected by deterministic BM25 over the change text. For
    every file modified by a retrieved episode:

      episode_similarity(f) = max normalized BM25 score among retrieved
                              episodes touching f (0 if none);
      episode_hit_count(f)  = number of retrieved episodes touching f.

    Deterministic; pure.
    """
    docs = {e["sha"]: f"{e['subject']}\n{e['body']}" for e in episode_records}
    index = BM25Index(docs)
    qterms = tokenize(query)
    top_shas = retrieve_top(docs, query, k=k)
    top_set = set(top_shas)
    raw = {e["sha"]: index.score(e["sha"], qterms) for e in episode_records
           if e["sha"] in top_set}
    max_raw = max(raw.values()) if raw else 0.0
    sim: dict[str, float] = {}
    hits: dict[str, int] = {}
    for e in episode_records:
        if e["sha"] not in top_set:
            continue
        norm = (raw[e["sha"]] / max_raw) if max_raw > 0.0 else 0.0
        for p in e["paths"]:
            sim[p] = max(sim.get(p, 0.0), norm)
            hits[p] = hits.get(p, 0) + 1
    return {p: {"episode_similarity": round(sim[p], 12),
                "episode_hit_count": hits[p]}
            for p in sim}
