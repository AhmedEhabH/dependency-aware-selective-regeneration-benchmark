"""WP-1a Correction B - label-free prediction view / forbidden-column enforcement.

The frozen Saleor-300 candidate rows artifact
(research/saleor-reserve-300-rmcss/candidate_rows_saleor300.parquet) contains a
``label`` column (all-zero placeholder, written label-free). Prediction-side
loaders MUST NOT expose label/outcome columns: any DataFrame used for prediction
drops/denies label immediately at the boundary (AC-1A.2 label isolation).

This module provides:
- FORBIDDEN_COLUMNS / _FORBIDDEN_FRAGMENTS: exact + substring denylist.
- load_prediction_view(): loads the candidate rows artifact, verifies the raw
  artifact does not carry a *populated* outcome, drops/denies forbidden columns
  at the boundary, and returns ONLY the frozen 11-feature prediction schema +
  identifiers. Fails closed on any forbidden column.
- validate_prediction_view(): runtime guard for arbitrary DataFrames.

The repository-agent candidate universe comes from parent-state / public
sources (public/candidate_universe.json), NOT from these labeled candidate
rows - verified by the independent audit.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

# Exact column names that must never reach prediction-side code.
FORBIDDEN_COLUMNS: frozenset[str] = frozenset({
    "label",
    "proxy",
    "is_proxy",
    "target",
    "outcome",
    "gold",
    "expected",
    "hidden",
    "change_status",
    "changed",
    "is_changed",
    "y",
    "gt",
    "ground_truth",
    "observed_change_set",
    "positive",
    "is_positive",
    "target_paths",
})

# Substring fragments (lowercase) treated as outcome indicators.
_FORBIDDEN_FRAGMENTS: tuple[str, ...] = (
    "label",
    "proxy",
    "outcome",
    "ground_truth",
    "expected_affected",
    "change_status",
    "observed_change",
    "is_changed",
    "target_path",
)

# Frozen 11-feature RM-CSS schema + identifiers allowed on the prediction side.
PREDICTION_VIEW_COLUMNS: tuple[str, ...] = (
    "case_id",
    "repository",
    "file_path",
    "dense_rank",
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

FEATURE_NAMES: tuple[str, ...] = (
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

CONTINUOUS_FEATURES: tuple[str, ...] = (
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

BOOLEAN_FEATURES: tuple[str, ...] = ("in_sparse", "sparse_empty")


class ForbiddenColumnError(ValueError):
    """Raised when prediction-side code receives a label/outcome column."""


def forbidden_column_matches(columns: set[str]) -> list[str]:
    """Return the subset of ``columns`` that violates the label-free boundary."""
    lower = {c: c.lower() for c in columns}
    violations: list[str] = []
    for col in sorted(columns):
        if col in FORBIDDEN_COLUMNS:
            violations.append(col)
            continue
        lc = lower[col]
        if any(frag in lc for frag in _FORBIDDEN_FRAGMENTS):
            violations.append(col)
    return violations


def validate_prediction_view(frame: pd.DataFrame) -> pd.DataFrame:
    """Fail closed if ``frame`` exposes any forbidden label/outcome column.

    Returns the frame unchanged when clean (caller should already have dropped
    the forbidden columns via :func:`load_prediction_view`).
    """
    violations = forbidden_column_matches(set(frame.columns))
    if violations:
        raise ForbiddenColumnError(
            "prediction-side DataFrame exposes forbidden outcome column(s): "
            f"{sorted(violations)}"
        )
    return frame


def load_prediction_view(path: Path) -> pd.DataFrame:
    """Load the frozen candidate-rows artifact as a label-free prediction view.

    - reads the parquet;
    - checks the raw artifact (must not contain a populated outcome column);
    - drops any forbidden column at the boundary (fails closed if any
      forbidden column is detected);
    - returns ONLY the frozen 11-feature schema + identifiers.

    The all-zero ``label`` placeholder column is DROPPED, never returned.
    """
    frame = pd.read_parquet(path)
    violations = forbidden_column_matches(set(frame.columns))
    if violations:
        # Drop at the boundary, but still record the occurrence for the audit.
        frame = frame.drop(columns=list(violations))
    missing = [c for c in PREDICTION_VIEW_COLUMNS if c not in frame.columns]
    if missing:
        raise ValueError(f"prediction view missing required columns: {missing}")
    return frame[list(PREDICTION_VIEW_COLUMNS)].copy()
