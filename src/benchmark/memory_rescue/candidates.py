"""PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2 — memory candidates + V2 features.

Frozen configuration (docs/PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_IMPACT_
DECLARATION_2026-09-20.md):

Memory candidate generation (mission §15):
  - structural: top COCHANGE_TOP_FILES = 10 NON-SPARSE files by
    cochange_memory_score > 0 (tie-break higher score / higher support /
    path ascending);
  - episodic: top EPISODIC_TOP_FILES = 10 NON-SPARSE files by
    episode_similarity > 0;
  - memory candidate set = union(structural, episodic).

V2 candidate universe (mission §16): Sparse ∪ dense top-20 NON-SPARSE ∪
memory candidates.

V2 features (mission §19) — EXACTLY 11:
  the 7 V1 features (identical definitions to benchmark.calibrated.features)
  + cochange_sparse + cochange_top1 + log_history_change_count
  + episode_similarity.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from benchmark.calibrated.features import no_units_score  # type: ignore[no-untyped-call]

COCHANGE_TOP_FILES = 10
EPISODIC_TOP_FILES = 10
TOP_ADD_UNIVERSE = 20

FEATURE_NAMES = (
    "dense_file_score",
    "log_rank",
    "gap_to_top1",
    "in_sparse",
    "log_sparse_set_size",
    "sparse_empty",
    "sparse_rank_interaction",
    "cochange_sparse",
    "cochange_top1",
    "log_history_change_count",
    "episode_similarity",
)

CONTINUOUS_FEATURES = (
    "dense_file_score",
    "log_rank",
    "gap_to_top1",
    "log_sparse_set_size",
    "sparse_rank_interaction",
    "cochange_sparse",
    "cochange_top1",
    "log_history_change_count",
    "episode_similarity",
)

BOOLEAN_FEATURES = ("in_sparse", "sparse_empty")


@dataclass(frozen=True)
class MemoryBundle:
    """Per-task memory data for ONE realization.

    Realization-independent fields (cached on D:):
      history_change_count: path -> C(path)
      cochange_sparse:      path -> max Jaccard(f, Sparse seed)
      episode_similarity:   path -> max normalized BM25 among retrieved episodes
      episode_hit_count:    path -> descriptive hit count (NOT a feature)
      n_production_changing_commits: int

    Realization-dependent fields (selected at run time for the realization):
      cochange_top1:        path -> Jaccard(f, dense-rank-1-file)
      structural:           list of structural candidate paths (top-10)
      episodic:             list of episodic candidate paths (top-10)
    """

    history_change_count: dict[str, int]
    cochange_sparse: dict[str, float]
    episode_similarity: dict[str, float]
    episode_hit_count: dict[str, int]
    n_production_changing_commits: int
    cochange_top1: dict[str, float] | None = None
    structural: list[str] | None = None
    episodic: list[str] | None = None


def assert_finite_dense_score_bounds(parquet_df: pd.DataFrame,
                                     bound: float = 10.0) -> None:
    """HARD PIPELINE GUARD (P86): fail if any FINITE candidate dense score has
    |score| > bound.

    The frozen DEV dense-file-score distribution is ~[0.07, 0.82]. A finite
    value outside [-bound, +bound] indicates a pipeline defect (e.g. the
    pre-P86 finite -1e9 sentinel), NOT a legitimate score. NO silent fallback.
    """
    finite = parquet_df.loc[
        np.isfinite(parquet_df["dense_file_score"].to_numpy(dtype=np.float64)),
        "dense_file_score",
    ]
    if finite.empty:
        return
    bad = finite.loc[finite.abs() > bound]
    if len(bad):
        raise ValueError(
            f"dense_file_score out of scientific bounds: {len(bad)} finite "
            f"value(s) with |score| > {bound} (min {float(bad.min())}, "
            f"max {float(bad.max())}); possible finite missing-sentinel "
            f"contamination. FAIL.")


@dataclass(frozen=True)
class CandidateRow:
    """One V2 candidate-file row (11 features + evaluation label)."""

    case_id: str
    repository: str
    file_path: str
    dense_rank: int
    dense_file_score: float
    log_rank: float
    gap_to_top1: float
    in_sparse: int
    log_sparse_set_size: float
    sparse_empty: int
    sparse_rank_interaction: float
    cochange_sparse: float
    cochange_top1: float
    log_history_change_count: float
    episode_similarity: float
    label: int


def build_rows(
    parquet_df: pd.DataFrame,
    tasks_by_id: dict,
    memory: dict[str, MemoryBundle],
    top_add_universe: int = TOP_ADD_UNIVERSE,
) -> list[CandidateRow]:
    """Build the frozen V2 candidate-universe feature rows (one realization)."""
    rows, _ = build_rows_with_provenance(
        parquet_df, tasks_by_id, memory, top_add_universe=top_add_universe)
    return rows


def build_rows_with_provenance(
    parquet_df: pd.DataFrame,
    tasks_by_id: dict,
    memory: dict[str, MemoryBundle],
    top_add_universe: int = TOP_ADD_UNIVERSE,
) -> tuple[list[CandidateRow], dict[str, dict[str, frozenset]]]:
    """Build V2 rows + per-file channel provenance.

    provenance[case_id][file_path] = frozenset of channels among
    {"sparse", "dense", "structural", "episodic"} that generated the file
    (used ONLY for the descriptive error decomposition, mission §25).
    """
    floor = no_units_score(parquet_df)
    assert_finite_dense_score_bounds(parquet_df)
    log1p_cache: dict[int, float] = {}
    rows: list[CandidateRow] = []
    provenance: dict[str, dict[str, frozenset]] = {}
    for case_id, g in parquet_df.groupby("case_id", sort=True):
        task = tasks_by_id[case_id]
        bundle = memory[case_id]
        g = g.sort_values(["file_path"]).copy()
        scores = np.where(np.isfinite(g["dense_file_score"].to_numpy(dtype=np.float64)),
                          g["dense_file_score"].to_numpy(dtype=np.float64), floor)
        rank = g["dense_rank"].to_numpy(dtype=np.int64)
        in_sparse = g["in_sparse"].astype(bool).to_numpy()
        paths = g["file_path"].tolist()
        score_max = float(scores.max())
        sparse_size = len(task.write_set)
        log_sparse_size = float(math.log1p(sparse_size))
        sparse_empty = 1 if sparse_size == 0 else 0
        proxy = set(task.proxy)

        # ---- memory candidate generation (frozen §12, §15) ----
        structural = set(bundle.structural or [])
        episodic = set(bundle.episodic or [])

        # ---- V2 candidate universe (frozen §16) ----
        sparse_mask = in_sparse
        non_sparse_order = np.argsort(rank[~sparse_mask], kind="stable")
        non_sparse_positions = np.where(~sparse_mask)[0][non_sparse_order][:top_add_universe]
        dense_paths = {paths[i] for i in non_sparse_positions}
        sparse_paths = {paths[i] for i in np.where(sparse_mask)[0]}

        task_prov: dict[str, frozenset] = {}
        candidate_positions: set[int] = set()
        for pos, f in enumerate(paths):
            channels: set[str] = set()
            if f in sparse_paths:
                channels.add("sparse")
            if f in dense_paths:
                channels.add("dense")
            if f in structural:
                channels.add("structural")
            if f in episodic:
                channels.add("episodic")
            if not channels:
                continue
            task_prov[f] = frozenset(channels)
            candidate_positions.add(pos)
        provenance[case_id] = task_prov

        for pos in sorted(candidate_positions):
            f = paths[pos]
            score = float(scores[pos])
            r = int(rank[pos])
            log_rank = float(math.log1p(r))
            is_sparse = 1 if in_sparse[pos] else 0
            hcc = bundle.history_change_count.get(f, 0)
            if hcc not in log1p_cache:
                log1p_cache[hcc] = float(math.log1p(hcc))
            rows.append(CandidateRow(
                case_id=case_id,
                repository=str(g["repository"].iloc[0]),
                file_path=f,
                dense_rank=r,
                dense_file_score=score,
                log_rank=log_rank,
                gap_to_top1=float(score_max - score),
                in_sparse=is_sparse,
                log_sparse_set_size=log_sparse_size,
                sparse_empty=sparse_empty,
                sparse_rank_interaction=float(is_sparse * log_rank),
                cochange_sparse=float(bundle.cochange_sparse.get(f, 0.0)),
                cochange_top1=float((bundle.cochange_top1 or {}).get(f, 0.0)),
                log_history_change_count=log1p_cache[hcc],
                episode_similarity=float(bundle.episode_similarity.get(f, 0.0)),
                label=1 if f in proxy else 0,
            ))
    rows.sort(key=lambda r: (r.case_id, r.file_path))
    return rows, provenance


def rows_to_frame(rows: list[CandidateRow]) -> pd.DataFrame:
    """Convert CandidateRow objects to a DataFrame (11 features + label)."""
    return pd.DataFrame(
        [
            {
                "case_id": r.case_id,
                "repository": r.repository,
                "file_path": r.file_path,
                "dense_rank": r.dense_rank,
                "dense_file_score": r.dense_file_score,
                "log_rank": r.log_rank,
                "gap_to_top1": r.gap_to_top1,
                "in_sparse": r.in_sparse,
                "log_sparse_set_size": r.log_sparse_set_size,
                "sparse_empty": r.sparse_empty,
                "sparse_rank_interaction": r.sparse_rank_interaction,
                "cochange_sparse": r.cochange_sparse,
                "cochange_top1": r.cochange_top1,
                "log_history_change_count": r.log_history_change_count,
                "episode_similarity": r.episode_similarity,
                "label": r.label,
            }
            for r in rows
        ]
    )


def feature_matrix(frame: pd.DataFrame, names: tuple = FEATURE_NAMES) -> np.ndarray:
    return frame[list(names)].to_numpy(dtype=np.float64)


def label_vector(frame: pd.DataFrame) -> np.ndarray:
    return frame["label"].to_numpy(dtype=np.int64)
