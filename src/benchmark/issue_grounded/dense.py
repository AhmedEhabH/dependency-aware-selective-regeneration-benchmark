"""Issue-grounded intent headroom - dense ranking arm (T3).

ARM M: reuse the existing frozen Qwen full-file dense ranks
(research/contamination-bridge/qwen_embed/realization_{A,B}/full_file_scores.parquet).

ARM I: compute ONLY the new issue-query embedding (title + body) for each
PRIMARY paired (temporally-clean) task, then score every file in the SAME
frozen candidate universe with the SAME frozen file-MAX cosine aggregation,
SAME tie-break (ascending path), SAME full-universe dense rank. The code-unit
embeddings are reused from the persisted E: realization cache - the code
corpus is NOT re-embedded.

This module is pure given (query vectors, cache matrix, task files); the API
call is made by the caller after a live-price + budget guard.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from benchmark.issue_grounded.corpus import load_corpus
from benchmark.signal.code_units import extract_code_units, sha256_text
from benchmark.signal.swrank_adapter import aggregate_file_score

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent.parent


def arm_i_query_for_task(record: dict[str, Any]) -> str | None:
    """ARM I query = concatenation of CLEAN issue title/body (ascending number).

    Returns None when the task has no temporally-clean candidate issue.
    """
    pairs: list[tuple[int, str, str]] = []
    for num, t, b, flag in zip(
        record["issue_numbers"], record["title"], record["body"], record["temporal_flag"],
        strict=True,
    ):
        if flag == "TEMPORALLY_CLEAN":
            pairs.append((int(num), str(t), str(b)))
    if not pairs:
        return None
    pairs.sort(key=lambda x: x[0])
    return "\n".join(f"{t}\n{b}".strip() for _, t, b in pairs)


def arm_i_queries(clean_case_ids: list[str], corpus_path: Path) -> dict[str, str]:
    """case_id -> ARM I query text for the given clean tasks."""
    corpus = load_corpus(corpus_path)
    by_id: dict[str, dict[str, Any]] = {r["case_id"]: r for r in corpus["records"]}
    out: dict[str, str] = {}
    for cid in clean_case_ids:
        q = arm_i_query_for_task(by_id[cid])
        if q:
            out[cid] = q
    return out


def load_cache_matrix(rid: str, cache_root: Path) -> tuple[np.ndarray, dict[str, int], int]:
    """Load the persisted chunk cache (matrix, index) for a realization."""
    idx = json.loads((cache_root / f"realization_{rid}" / "index.json").read_text(encoding="utf-8"))
    parts = sorted((cache_root / f"realization_{rid}" / "parts").glob("part_*.npy"))
    rows = [np.load(p, mmap_mode="r") for p in parts]
    dim = rows[0].shape[1]
    full = np.concatenate([np.asarray(r) for r in rows], axis=0).astype(np.float32)
    return full, idx, dim


def build_plan(blob_texts: dict[str, str]) -> dict[str, list[str]]:
    """blob sha -> list of unit shas (frozen extraction; whitespace-only excluded)."""
    plan: dict[str, list[str]] = {}
    for sha, text in blob_texts.items():
        if text is None:
            plan[sha] = []
            continue
        plan[sha] = [sha256_text(u) for u in extract_code_units(text) if u.strip()]
    return plan


def _l2(v: np.ndarray) -> np.ndarray:
    arr = np.asarray(v, dtype=np.float64)
    n = float(np.linalg.norm(arr))
    return (arr / n if n > 0 else arr).astype(np.float32)


def rank_files_full_universe(
    query_emb: np.ndarray,
    unit_mat: np.ndarray,
    cache_idx: dict[str, int],
    file_blobs: dict[str, str],
    plan: dict[str, list[str]],
    universe: list[str],
) -> dict[str, int]:
    """Full-universe dense rank (1=best) with frozen MAX-cosine aggregation."""
    q = _l2(query_emb)
    scores: dict[str, float] = {}
    for path in universe:
        blob_sha = file_blobs.get(path)
        keys = plan.get(blob_sha, []) if blob_sha else []
        if not keys:
            scores[path] = -1e9
            continue
        rows = [cache_idx[k] for k in keys if k in cache_idx]
        if not rows:
            scores[path] = -1e9
            continue
        unit_cos = unit_mat[rows] @ q
        scores[path] = aggregate_file_score(
            [(k, float(c)) for k, c in zip(keys, unit_cos, strict=True)])  # type: ignore[arg-type]
    ranked = sorted(universe, key=lambda p: (-scores.get(p, -1e9), p))
    return {p: i + 1 for i, p in enumerate(ranked)}


def full_file_scores_arm_m(parquet: Any, case_id: str) -> tuple[dict[str, float], dict[str, int]]:
    """ARM M frozen dense scores/ranks for one task from the frozen parquet."""
    g = parquet[parquet["case_id"] == case_id]
    scores: dict[str, float] = {}
    ranks: dict[str, int] = {}
    for r in g.itertuples(index=False):
        scores[str(r.file_path)] = float(r.dense_file_score)
        ranks[str(r.file_path)] = int(r.dense_rank)
    return scores, ranks
