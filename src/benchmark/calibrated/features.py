"""CALIBRATED_SET_SELECTION_V1 — candidate universe + frozen features (T3, ZERO API).

Frozen configuration (docs/CALIBRATED_SET_SELECTION_V1_IMPACT_DECLARATION_2026-09-20.md):

Candidate universe per task:
  - KEEP/DROP: every file with in_sparse == True (the Sparse write set);
  - ADD: the top `TOP_ADD_UNIVERSE = 20` NON-SPARSE legal production files by
    the frozen Qwen dense rank (ascending dense_rank among in_sparse == False);
  - files outside the candidate universe remain unselected in V1.

Features (exactly 7, no feature shopping):
  1. dense_file_score   (imputed deterministically when NaN — see no_units_score)
  2. log_rank           = log1p(dense_rank)  [ABSOLUTE rank; NOT normalized by N]
  3. gap_to_top1        = max_score(task) - dense_file_score
  4. in_sparse          (boolean)
  5. log_sparse_set_size = log1p(sparse_set_size)
  6. sparse_empty       (1 if sparse_set_size == 0)
  7. sparse_rank_interaction = in_sparse * log_rank

The label (1 if the file is in the historical changed-file proxy) is an
EVALUATION-ONLY target joined here for the scoring/audit steps. It is never an
input to scaling, model fitting, or threshold selection. Training functions in
this package receive X (feature matrix) and y (labels) separately so the nested
CV driver can structurally guarantee the label is used only where the frozen
protocol allows it.

All functions are pure and deterministic.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

TOP_ADD_UNIVERSE = 20

FEATURE_NAMES = (
    "dense_file_score",
    "log_rank",
    "gap_to_top1",
    "in_sparse",
    "log_sparse_set_size",
    "sparse_empty",
    "sparse_rank_interaction",
)

CONTINUOUS_FEATURES = (
    "dense_file_score",
    "log_rank",
    "gap_to_top1",
    "log_sparse_set_size",
    "sparse_rank_interaction",
)

BOOLEAN_FEATURES = ("in_sparse", "sparse_empty")


@dataclass(frozen=True)
class CandidateRow:
    """One candidate-file row with the frozen 7 features + evaluation label."""

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
    label: int


def no_units_score(parquet_df: pd.DataFrame) -> float:
    """Frozen deterministic imputation constant for files with NO embeddable units.

    `dense_file_score` is NaN for files with no embeddable code units. The
    imputed value is `min_finite_dense_score - 1.0`, computed once from the
    frozen label-free score artifact (parent-visible, label-free, identical
    across all folds). This keeps the value below every observed score while
    remaining numerically well-behaved under StandardScaler.
    """
    finite = parquet_df.loc[np.isfinite(parquet_df["dense_file_score"]), "dense_file_score"]
    if finite.empty:
        return -1.0
    return float(finite.min()) - 1.0


def _impute_scores(scores: pd.Series, floor: float) -> np.ndarray:
    arr = scores.to_numpy(dtype=np.float64)
    arr = np.where(np.isfinite(arr), arr, floor)
    return arr


def build_rows(
    parquet_df: pd.DataFrame,
    tasks_by_id: dict,
    top_add_universe: int = TOP_ADD_UNIVERSE,
) -> list[CandidateRow]:
    """Build the frozen candidate-universe feature rows for every DEV task.

    parquet_df: label-free Qwen full-file-score table for ONE realization
                (columns case_id/repository/file_path/dense_file_score/
                dense_rank/in_sparse).
    tasks_by_id: case_id -> RecallTask (provides write_set and proxy).
    """
    floor = no_units_score(parquet_df)
    rows: list[CandidateRow] = []
    for case_id, g in parquet_df.groupby("case_id", sort=True):
        task = tasks_by_id[case_id]
        g = g.sort_values(["file_path"]).copy()
        scores = _impute_scores(g["dense_file_score"], floor)
        rank = g["dense_rank"].to_numpy(dtype=np.int64)
        in_sparse = g["in_sparse"].astype(bool).to_numpy()
        paths = g["file_path"].tolist()
        score_max = float(scores.max())
        sparse_size = len(task.write_set)
        log_sparse_size = float(math.log1p(sparse_size))
        sparse_empty = 1 if sparse_size == 0 else 0
        proxy = set(task.proxy)

        # Candidate universe: Sparse files UNION top-K non-sparse by dense rank.
        sparse_mask = in_sparse
        non_sparse_order = np.argsort(rank[~sparse_mask], kind="stable")
        non_sparse_positions = np.where(~sparse_mask)[0][non_sparse_order][:top_add_universe]
        candidate_positions = set(np.where(sparse_mask)[0].tolist()) | set(non_sparse_positions.tolist())

        for pos in sorted(candidate_positions):
            score = float(scores[pos])
            r = int(rank[pos])
            log_rank = float(math.log1p(r))
            is_sparse = 1 if sparse_mask[pos] else 0
            rows.append(
                CandidateRow(
                    case_id=case_id,
                    repository=str(g["repository"].iloc[0]),
                    file_path=paths[pos],
                    dense_rank=r,
                    dense_file_score=score,
                    log_rank=log_rank,
                    gap_to_top1=float(score_max - score),
                    in_sparse=is_sparse,
                    log_sparse_set_size=log_sparse_size,
                    sparse_empty=sparse_empty,
                    sparse_rank_interaction=float(is_sparse * log_rank),
                    label=1 if paths[pos] in proxy else 0,
                )
            )
    rows.sort(key=lambda r: (r.case_id, r.file_path))
    return rows


def rows_to_frame(rows: list[CandidateRow]) -> pd.DataFrame:
    """Convert CandidateRow objects to a DataFrame (case_id, repository,
    file_path, features..., label)."""
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
                "label": r.label,
            }
            for r in rows
        ]
    )


def feature_matrix(frame: pd.DataFrame, names: tuple = FEATURE_NAMES) -> np.ndarray:
    """Feature matrix (no labels)."""
    return frame[list(names)].to_numpy(dtype=np.float64)


def label_vector(frame: pd.DataFrame) -> np.ndarray:
    """Evaluation-only label vector (1 if file in historical changed-file proxy)."""
    return frame["label"].to_numpy(dtype=np.int64)
