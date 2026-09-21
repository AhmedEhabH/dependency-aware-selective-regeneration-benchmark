"""WP-1b first-class truncation / cap / failure telemetry schema.

Mission section 10 requires that a method cannot be declared scientifically
stronger without exposing whether the competing arm was harmed by
instrumentation limits. These metrics are emitted per task, aggregated per
method, and included in the final report and machine-readable output.

Definitions:
- control call: one repository-agent LLM call (agent control plane, bounded by
  the frozen agent-control completion cap).
- cap hit / truncation: a control call whose finish_reason is "length" (the
  response was cut at the completion cap). Because the control plane is bounded
  separately from the source-edit cap, a "length" here always means the
  control cap was reached.
- EMPTY prediction: a task completed by the strategy without any selected path
  (fail-closed). The EMPTY reason classifies WHY:
    truncation      -> a control call was truncated (finish_reason=length)
    round_cap       -> the 8 agent calls were exhausted without a valid final
    parser_failure  -> malformed JSON or schema-invalid final answer on the
                       last allowed call
    infrastructure  -> cooperative workflow deadline / token allowance
                       exhaustion (no model call performed)
    none            -> a valid final answer was accepted (not an EMPTY)

Aggregation returns both per-call and per-task tallies so an instrument finding
(many EMPTY due to truncation/cap/parser) can be separated from a method
finding.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from benchmark.strategies.iterative_agent import IterativeRepositoryAgentStrategy

EMPTY_REASONS: tuple[str, ...] = (
    "truncation",
    "round_cap",
    "parser_failure",
    "infrastructure",
    "none",
)

PER_TASK_FIELDS: tuple[str, ...] = (
    "task_id",
    "model_calls",
    "control_truncation_count",
    "cap_hit_count",
    "malformed_count",
    "schema_invalid_count",
    "valid_final_count",
    "finish_reason_distribution",
    "empty_reason",
    "prediction_empty",
    "final_answer_truncated",
    "observation_truncation_rate",
    "paths_read",
    "paths_surfaced",
    "tool_output_chars_raw_total",
    "tool_output_chars_shown_total",
    # A4: per-task tool telemetry (report-only, behavior-preserving).
    "successful_reads",
    "search_calls_with_hits",
    "rejected_repeat_count",
    "tool_error_counts",
    # A4/G11: report-only search telemetry.
    "search_files_scanned",
    "search_results_returned",
    "search_result_cap_hits",
    "unique_paths_surfaced",
    "tool_duration_seconds_total",
)

CALL_SIDECAR_FIELDS: tuple[str, ...] = (
    "task_id",
    "call_index",
    "force_final",
    "action",
    "path",
    "query",
    # A4: per-call tool outcome.
    "tool_ok",
    "tool_error",
    "tool_duration_seconds",
    "tool_output_chars_raw",
    "tool_output_chars_shown",
    "observation_truncated",
    # A4/G11: per-call search telemetry (search_text only; 0 defaults otherwise).
    "search_files_scanned",
    "search_results_returned",
    "search_result_cap_hit",
    "finish_reason",
    "prompt_tokens",
    "completion_tokens",
    "usd",
    "latency_s",
    "raw_response_text",
    "raw_response_sha256",
)


def strategy_telemetry(
    strategy: IterativeRepositoryAgentStrategy, *, task_id: str = ""
) -> dict[str, Any]:
    """Build the per-task telemetry record from strategy counters."""
    empty_reason = strategy.selection_empty_reason
    return {
        "task_id": task_id,
        "model_calls": strategy.model_call_count,
        "control_truncation_count": strategy.selection_truncation_count,
        "cap_hit_count": strategy.selection_truncation_count,
        "malformed_count": strategy.selection_malformed_count,
        "schema_invalid_count": strategy.selection_schema_invalid_count,
        "valid_final_count": strategy.selection_valid_final_count,
        "finish_reason_distribution": dict(strategy.selection_finish_reason_distribution),
        "empty_reason": empty_reason,
        "prediction_empty": empty_reason != "none",
        "final_answer_truncated": empty_reason == "truncation",
        "observation_truncation_rate": strategy.observation_truncation_rate(),
        "paths_read": list(strategy.paths_read),
        "paths_surfaced": list(strategy.paths_surfaced),
        "tool_output_chars_raw_total": strategy.tool_output_chars_raw_total,
        "tool_output_chars_shown_total": strategy.tool_output_chars_shown_total,
        "successful_reads": strategy.successful_reads,
        "search_calls_with_hits": strategy.search_calls_with_hits,
        "rejected_repeat_count": strategy.rejected_repeat_count,
        "tool_error_counts": dict(strategy.tool_error_counts),
        "search_files_scanned": strategy.search_files_scanned,
        "search_results_returned": strategy.search_results_returned,
        "search_result_cap_hits": strategy.search_result_cap_hits,
        "unique_paths_surfaced": len(set(strategy.paths_surfaced)),
        "tool_duration_seconds_total": strategy.tool_duration_seconds,
    }


def call_sidecar_records(
    strategy: IterativeRepositoryAgentStrategy, *, task_id: str = ""
) -> list[dict[str, Any]]:
    """Build the per-call sidecar JSONL records (additive WP-1b telemetry)."""
    return [
        {"task_id": task_id, **dict(rec)}
        for rec in strategy.call_sidecar
    ]


def aggregate(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate per-task telemetry into the first-class WP-1b metrics."""
    n = len(records)
    if n == 0:
        raise ValueError("cannot aggregate an empty telemetry list")
    reason_counts: dict[str, int] = {r: 0 for r in EMPTY_REASONS}
    for rec in records:
        reason = rec["empty_reason"]
        reason_counts[reason] = reason_counts.get(reason, 0) + 1

    finish_reasons: dict[str, int] = {}
    for rec in records:
        for reason, count in rec["finish_reason_distribution"].items():
            finish_reasons[reason] = finish_reasons.get(reason, 0) + count

    return {
        "final_answer_truncation_count": reason_counts["truncation"],
        "final_answer_truncation_rate": reason_counts["truncation"] / n,
        "cap_hit_count": sum(rec["cap_hit_count"] for rec in records),
        "cap_hit_rate": sum(rec["cap_hit_count"] for rec in records) / n,
        "finish_reason_distribution": finish_reasons,
        "valid_final_schema_count": sum(rec["valid_final_count"] for rec in records),
        "valid_final_schema_rate": sum(1 for rec in records if rec["valid_final_count"] > 0) / n,
        "EMPTY_due_to_truncation_count": reason_counts["truncation"],
        "EMPTY_due_to_round_cap_count": reason_counts["round_cap"],
        "EMPTY_due_to_parser_failure_count": reason_counts["parser_failure"],
        "EMPTY_due_to_infrastructure_count": reason_counts["infrastructure"],
        "unclassified_EMPTY_count": n - sum(reason_counts[r] for r in EMPTY_REASONS),
    }


def validate(record: dict[str, Any]) -> None:
    """Validate a per-task telemetry record against the frozen schema."""
    for field in PER_TASK_FIELDS:
        if field not in record:
            raise ValueError(f"telemetry record missing field {field!r}")
    if record["empty_reason"] not in EMPTY_REASONS:
        raise ValueError(
            f"invalid empty_reason {record['empty_reason']!r}; "
            f"allowed: {EMPTY_REASONS}"
        )
    if record["prediction_empty"] != (record["empty_reason"] != "none"):
        raise ValueError("prediction_empty inconsistent with empty_reason")
