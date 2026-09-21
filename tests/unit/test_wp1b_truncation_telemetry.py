"""WP-1b G3/G2 - truncation and cap telemetry schema tests.

Mission section 10 requires first-class truncation/cap/failure metrics. These
tests protect the Impact Correctness validity dimension (instrument findings
must be separable from method findings) and Architecture Compliance (frozen
telemetry schema).
"""

from __future__ import annotations

import pytest

from benchmark.wp1b.telemetry import (
    EMPTY_REASONS,
    aggregate,
    strategy_telemetry,
    validate,
)


def _record(
    empty_reason: str = "none",
    trunc=0,
    malformed=0,
    schema_invalid=0,
    valid_final=0,
    finish_reasons=None,
) -> dict:
    return {
        "task_id": "t",
        "model_calls": 3,
        "control_truncation_count": trunc,
        "cap_hit_count": trunc,
        "malformed_count": malformed,
        "schema_invalid_count": schema_invalid,
        "valid_final_count": valid_final,
        "finish_reason_distribution": finish_reasons or {"stop": 3},
        "empty_reason": empty_reason,
        "prediction_empty": empty_reason != "none",
        "final_answer_truncated": empty_reason == "truncation",
        "observation_truncation_rate": 0.0,
        "paths_read": [],
        "paths_surfaced": [],
        "tool_output_chars_raw_total": 0,
        "tool_output_chars_shown_total": 0,
        "successful_reads": 0,
        "search_calls_with_hits": 0,
        "rejected_repeat_count": 0,
        "tool_error_counts": {},
        "search_files_scanned": 0,
        "search_results_returned": 0,
        "search_result_cap_hits": 0,
        "unique_paths_surfaced": 0,
        "tool_duration_seconds_total": 0.0,
    }


def test_valid_record_passes_validation() -> None:
    validate(_record(empty_reason="round_cap"))
    validate(_record(empty_reason="none"))


def test_invalid_empty_reason_rejected() -> None:
    with pytest.raises(ValueError):
        validate(_record(empty_reason="mystery"))


def test_prediction_empty_inconsistent_rejected() -> None:
    rec = _record(empty_reason="none")
    rec["prediction_empty"] = True
    with pytest.raises(ValueError):
        validate(rec)


def test_empty_reasons_enum_complete() -> None:
    assert set(EMPTY_REASONS) == {
        "truncation", "round_cap", "parser_failure", "infrastructure", "none",
    }


def test_aggregate_counts_each_empty_class() -> None:
    records = [
        _record("truncation", trunc=1, finish_reasons={"length": 1}),
        _record("round_cap"),
        _record("parser_failure", malformed=1),
        _record("infrastructure"),
        _record("none", valid_final=1),
    ]
    agg = aggregate(records)
    assert agg["EMPTY_due_to_truncation_count"] == 1
    assert agg["EMPTY_due_to_round_cap_count"] == 1
    assert agg["EMPTY_due_to_parser_failure_count"] == 1
    assert agg["EMPTY_due_to_infrastructure_count"] == 1
    assert agg["unclassified_EMPTY_count"] == 0
    assert agg["final_answer_truncation_count"] == 1
    assert agg["final_answer_truncation_rate"] == pytest.approx(0.2)
    assert agg["valid_final_schema_count"] == 1
    assert agg["valid_final_schema_rate"] == pytest.approx(0.2)
    assert agg["cap_hit_count"] == 1
    assert agg["cap_hit_rate"] == pytest.approx(0.2)
    assert agg["finish_reason_distribution"] == {"length": 1, "stop": 12}


def test_aggregate_empty_input_rejected() -> None:
    with pytest.raises(ValueError):
        aggregate([])


def test_strategy_telemetry_requires_strategy_with_selection_telemetry() -> None:
    """A stub strategy exposing the selection telemetry properties."""
    class _StubStrategy:
        model_call_count = 8
        selection_truncation_count = 0
        selection_malformed_count = 1
        selection_schema_invalid_count = 0
        selection_valid_final_count = 0
        selection_finish_reason_distribution = {"stop": 8}
        selection_empty_reason = "round_cap"
        tool_output_chars_raw_total = 0
        tool_output_chars_shown_total = 0

        def observation_truncation_rate(self) -> float:
            return 0.0

        @property
        def paths_read(self) -> list[str]:
            return []

        @property
        def paths_surfaced(self) -> list[str]:
            return []

        @property
        def successful_reads(self) -> int:
            return 0

        @property
        def search_calls_with_hits(self) -> int:
            return 0

        @property
        def rejected_repeat_count(self) -> int:
            return 0

        @property
        def tool_error_counts(self) -> dict[str, int]:
            return {}

        @property
        def search_files_scanned(self) -> int:
            return 0

        @property
        def search_results_returned(self) -> int:
            return 0

        @property
        def search_result_cap_hits(self) -> int:
            return 0

        @property
        def tool_duration_seconds(self) -> float:
            return 0.0

    rec = strategy_telemetry(_StubStrategy(), task_id="x")  # type: ignore[arg-type]
    validate(rec)
    assert rec["empty_reason"] == "round_cap"
    assert rec["model_calls"] == 8
