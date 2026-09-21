"""WP-1a Correction B - label isolation tests (AC-1A.2).

Prediction-side loaders must NOT expose label/outcome columns. Tests fail if
prediction-side code receives forbidden columns.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))
if str(PROJECT_DIR / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR / "src"))

from benchmark.wp1a.schema import (  # noqa: E402
    ForbiddenColumnError,
    load_prediction_view,
    validate_prediction_view,
)

RESEARCH = PROJECT_DIR / "research" / "saleor-reserve-300-rmcss"
WP1A = PROJECT_DIR / "research" / "wp1a"


def _frame_with_label() -> pd.DataFrame:
    return pd.DataFrame({
        "case_id": ["t1", "t1"],
        "file_path": ["a.py", "b.py"],
        "label": [1, 0],
        "dense_file_score": [0.5, 0.4],
    })


def test_validate_rejects_label_column() -> None:
    with pytest.raises(ForbiddenColumnError):
        validate_prediction_view(_frame_with_label())


def test_validate_rejects_hidden_proxy_columns() -> None:
    df = pd.DataFrame({"hidden_proxy": [1], "file_path": ["a.py"]})
    with pytest.raises(ForbiddenColumnError):
        validate_prediction_view(df)


def test_validate_accepts_clean_frame() -> None:
    df = pd.DataFrame({"case_id": ["t1"], "file_path": ["a.py"], "dense_file_score": [0.5]})
    assert validate_prediction_view(df) is df


def test_candidate_rows_parquet_contains_label_column() -> None:
    """Confirms the concern: the frozen artifact contains a label column."""
    raw = pd.read_parquet(RESEARCH / "candidate_rows_saleor300.parquet")
    assert "label" in raw.columns


def test_prediction_view_drops_label_at_boundary() -> None:
    view = load_prediction_view(RESEARCH / "candidate_rows_saleor300.parquet")
    assert "label" not in view.columns
    assert set(("case_id", "file_path", "dense_file_score", "dense_rank")).issubset(view.columns)
    # frozen 11-feature schema preserved
    assert set(
        ("dense_file_score", "log_rank", "gap_to_top1", "in_sparse",
         "log_sparse_set_size", "sparse_empty", "sparse_rank_interaction",
         "cochange_sparse", "cochange_top1", "log_history_change_count",
         "episode_similarity")
    ).issubset(view.columns)


def test_per_task_prediction_artifact_has_no_label() -> None:
    import json
    pred = json.loads((WP1A / "sip_rmcss_per_task_predictions.json").read_text(encoding="utf-8"))
    for entry in pred["per_task"].values():
        assert "label" not in entry
        assert "proxy" not in entry


def test_frozen_per_task_hashes_are_plain_sets() -> None:
    import json
    pred = json.loads((WP1A / "sip_rmcss_per_task_predictions.json").read_text(encoding="utf-8"))
    for entry in pred["per_task"].values():
        assert isinstance(entry["sip_predicted_set"], list)
        assert isinstance(entry["rmcss_predicted_set"], list)
        assert entry["sip_prediction_hash"]
        assert entry["rmcss_prediction_hash"]
