from __future__ import annotations

import csv
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from benchmark.checkpoint.checkpoint import (
    CheckpointData,
    CheckpointManager,
    ProgressData,
    ProgressManager,
)
from benchmark.checkpoint.persistence import RunRecordData, RunRecordStore

logger = logging.getLogger("benchmark.reports")


# ---------------------------------------------------------------------------
# Report rebuild: pure, offline, idempotent
# ---------------------------------------------------------------------------

class ReportRebuildError(Exception):
    """Raised when raw evidence is inconsistent with the checkpoint."""


def _load_all_records(runs_dir: Path) -> list[RunRecordData]:
    """Load all persisted run records from run_records.jsonl."""
    return RunRecordStore(runs_dir).load_all()


def _load_checkpoint(runs_dir: Path) -> CheckpointData:
    """Load the authoritative checkpoint."""
    cp = CheckpointManager(runs_dir).read()
    if cp is None:
        raise ReportRebuildError(f"No checkpoint.json found in {runs_dir}")
    return cp


def _build_results_agg_from_records(
    records: list[RunRecordData],
    planned_run_ids: list[str],
) -> dict[str, dict[str, Any]]:
    """Build results_agg from persisted records, keyed by strategy_name.

    Only includes records whose run_id is in the planned set.
    Returns one entry per strategy that has at least one record.
    """
    planned_set = set(planned_run_ids)
    agg: dict[str, dict[str, Any]] = {}

    for rec in records:
        if rec.run_id not in planned_set:
            continue
        sname = rec.strategy_id
        if sname not in agg:
            agg[sname] = {
                "success_count": 0,
                "failure_count": 0,
                "timeout_count": 0,
                "records": [],
            }
        record_dict = {
            "run_id": rec.run_id,
            "scenario_id": rec.scenario_id,
            "strategy_name": rec.strategy_id,
            "status": rec.status,
            "duration_seconds": rec.duration_seconds,
            "token_usage": rec.token_usage,
            "model_calls": rec.model_calls,
            "failure_classification": rec.failure_classification,
            "hardware_identity": rec.hardware_identity,
            "software_environment_identity": rec.software_environment_identity,
            "repair_attempts": rec.repair_attempts,
            # End-to-end workflow metrics (SU-0010A)
            "selection_prompt_tokens": rec.selection_prompt_tokens,
            "selection_completion_tokens": rec.selection_completion_tokens,
            "selection_total_tokens": rec.selection_total_tokens,
            "selection_model_calls": rec.selection_model_calls,
            "selection_duration_seconds": rec.selection_duration_seconds,
            "regeneration_prompt_tokens": rec.regeneration_prompt_tokens,
            "regeneration_completion_tokens": rec.regeneration_completion_tokens,
            "regeneration_total_tokens": rec.regeneration_total_tokens,
            "regeneration_model_calls": rec.regeneration_model_calls,
            "regeneration_duration_seconds": rec.regeneration_duration_seconds,
            "functional_validation_duration_seconds": rec.functional_validation_duration_seconds,
            "functional_validation_passed": rec.functional_validation_passed,
            "total_workflow_tokens": rec.total_workflow_tokens,
            "total_workflow_model_calls": rec.total_workflow_model_calls,
            "total_workflow_duration_seconds": rec.total_workflow_duration_seconds,
            "selected_artifact_count": rec.selected_artifact_count,
            "regenerated_artifact_count": rec.regenerated_artifact_count,
            "preserved_artifact_count": rec.preserved_artifact_count,
            "unresolved_human_review_count": rec.unresolved_human_review_count,
        }
        agg[sname]["records"].append(record_dict)
        if rec.status == "succeeded":
            agg[sname]["success_count"] += 1
        elif rec.status == "failed":
            agg[sname]["failure_count"] += 1
        elif rec.status == "timed_out":
            agg[sname]["timeout_count"] += 1

    # Per-strategy aggregate metrics
    for _sname, entry in agg.items():
        records_list = entry.get("records", [])
        n = len(records_list)
        total_workflow_tokens = sum(r.get("total_workflow_tokens", 0) for r in records_list)
        total_workflow_model_calls = sum(r.get("total_workflow_model_calls", 0) for r in records_list)
        total_workflow_duration = sum(r.get("total_workflow_duration_seconds", 0.0) for r in records_list)
        selection_total = sum(r.get("selection_total_tokens", 0) for r in records_list)
        regeneration_total = sum(r.get("regeneration_total_tokens", 0) for r in records_list)
        selected_count = sum(r.get("selected_artifact_count", 0) for r in records_list)
        regenerated_count = sum(r.get("regenerated_artifact_count", 0) for r in records_list)
        preserved_count = sum(r.get("preserved_artifact_count", 0) for r in records_list)
        unresolved_count = sum(r.get("unresolved_human_review_count", 0) for r in records_list)
        # Validation tri-state: True=passed, False=failed, None=not executed
        validation_executed = [r.get("functional_validation_passed") for r in records_list
                               if r.get("functional_validation_passed") is not None]
        validation_passed = sum(1 for v in validation_executed if v is True)
        validation_failed = sum(1 for v in validation_executed if v is False)
        validation_executed_count = len(validation_executed)
        validation_pass_rate = (validation_passed / validation_executed_count
                                if validation_executed_count > 0 else None)

        entry["aggregate"] = {
            "run_count": n,
            "success_count": entry.get("success_count", 0),
            "failed_count": entry.get("failure_count", 0),
            "sum_total_workflow_tokens": total_workflow_tokens,
            "mean_total_workflow_tokens": round(total_workflow_tokens / n, 4) if n > 0 else 0,
            "sum_total_workflow_model_calls": total_workflow_model_calls,
            "mean_total_workflow_model_calls": round(total_workflow_model_calls / n, 4) if n > 0 else 0,
            "sum_total_workflow_duration_seconds": round(total_workflow_duration, 6),
            "mean_total_workflow_duration_seconds": round(total_workflow_duration / n, 6) if n > 0 else 0,
            "sum_selection_total_tokens": selection_total,
            "mean_selection_total_tokens": round(selection_total / n, 4) if n > 0 else 0,
            "sum_regeneration_total_tokens": regeneration_total,
            "mean_regeneration_total_tokens": round(regeneration_total / n, 4) if n > 0 else 0,
            "sum_selected_artifact_count": selected_count,
            "sum_regenerated_artifact_count": regenerated_count,
            "sum_preserved_artifact_count": preserved_count,
            "sum_unresolved_human_review_count": unresolved_count,
            "validation_executed_count": validation_executed_count,
            "validation_passed_count": validation_passed,
            "validation_failed_count": validation_failed,
            "validation_pass_rate": validation_pass_rate,
        }

    return agg


def _validate_evidence(
    cp: CheckpointData,
    records: list[RunRecordData],
) -> None:
    """Validate raw evidence consistency. Raises on mismatch."""
    planned_set = set(cp.planned_run_ids)
    record_ids = {r.run_id for r in records}
    unexpected = record_ids - planned_set
    if unexpected:
        raise ReportRebuildError(
            f"Unexpected Run IDs in records: {sorted(unexpected)}"
        )

    # Check for duplicate records
    seen: dict[str, int] = {}
    for rec in records:
        seen[rec.run_id] = seen.get(rec.run_id, 0) + 1
    dupes = {rid: cnt for rid, cnt in seen.items() if cnt > 1}
    if dupes:
        raise ReportRebuildError(
            f"Duplicate Run IDs in records: {dupes}"
        )

    # Check that succeeded checkpoint IDs have records
    for rid in cp.succeeded_run_ids:
        if rid not in record_ids:
            raise ReportRebuildError(
                f"Checkpoint claims succeeded but no record exists for Run ID: {rid}"
            )

    # Check overlap
    overlap = set(cp.pending_run_ids) & set(cp.completed_run_ids)
    if overlap:
        raise ReportRebuildError(
            f"Pending and completed overlap: {sorted(overlap)}"
        )


def _build_smoke_summary_from_agg(
    all_strategy_names: list[str],
    results_agg: dict[str, dict[str, Any]],
    planned_run_ids: list[str],
    checkpoint_completed: list[str],
    checkpoint_failed: list[str],
    pending_run_ids: list[str],
) -> list[dict[str, Any]]:
    """Build smoke progress summary from persisted records (via results_agg).

    Uses checkpoint-level data for planned/completed/pending counts,
    and results_agg (from ALL records) for succeeded/failed/timed_out.
    """
    summary_rows: list[dict[str, Any]] = []
    for sname in all_strategy_names:
        plan_ids = [rid for rid in planned_run_ids if f"_{sname}_" in rid]
        completed_ids = [rid for rid in checkpoint_completed if f"_{sname}_" in rid]
        pending_ids = [rid for rid in pending_run_ids if f"_{sname}_" in rid]

        agg = results_agg.get(sname, {})
        records = agg.get("records", [])
        succeeded = sum(1 for r in records if r.get("status") == "succeeded")
        failed = sum(1 for r in records if r.get("status") == "failed")
        timed_out = sum(1 for r in records if r.get("status") == "timed_out")
        env_failed = sum(
            1 for r in records
            if r.get("failure_classification") == "environment_preflight"
        )

        row: dict[str, Any] = {
            "strategy_name": sname,
            "total_planned": len(plan_ids),
            "total_completed": len(completed_ids),
            "succeeded": succeeded,
            "failed": failed,
            "timed_out": timed_out,
            "environment_failed": env_failed,
            "not_yet_run": len(pending_ids),
        }
        summary_rows.append(row)
    return summary_rows


def _build_per_strategy_detail_rows(
    results_agg: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build one row per run with full detail fields."""
    rows: list[dict[str, Any]] = []
    for sname, agg in sorted(results_agg.items()):
        for rec in agg.get("records", []):
            tok = rec.get("token_usage", {})
            rows.append({
                "strategy_name": rec.get("strategy_name", sname),
                "run_id": rec.get("run_id", ""),
                "execution_status": rec.get("status", ""),
                "failure_classification": rec.get("failure_classification", ""),
                "duration_seconds": rec.get("duration_seconds", 0.0),
                "model_calls": rec.get("model_calls", 0),
                "prompt_tokens": tok.get("prompt", 0),
                "completion_tokens": tok.get("completion", 0),
                "total_tokens": tok.get("total", 0),
                "repair_attempts": rec.get("repair_attempts", 0),
                "hardware_identity": rec.get("hardware_identity", ""),
                "software_environment_identity": rec.get("software_environment_identity", ""),
                # End-to-end workflow metrics (SU-0010B2)
                "selection_prompt_tokens": rec.get("selection_prompt_tokens", 0),
                "selection_completion_tokens": rec.get("selection_completion_tokens", 0),
                "selection_total_tokens": rec.get("selection_total_tokens", 0),
                "selection_model_calls": rec.get("selection_model_calls", 0),
                "selection_duration_seconds": rec.get("selection_duration_seconds", 0.0),
                "regeneration_prompt_tokens": rec.get("regeneration_prompt_tokens", 0),
                "regeneration_completion_tokens": rec.get("regeneration_completion_tokens", 0),
                "regeneration_total_tokens": rec.get("regeneration_total_tokens", 0),
                "regeneration_model_calls": rec.get("regeneration_model_calls", 0),
                "regeneration_duration_seconds": rec.get("regeneration_duration_seconds", 0.0),
                "functional_validation_duration_seconds": rec.get("functional_validation_duration_seconds", 0.0),
                "functional_validation_passed": rec.get("functional_validation_passed", None),
                "total_workflow_tokens": rec.get("total_workflow_tokens", 0),
                "total_workflow_model_calls": rec.get("total_workflow_model_calls", 0),
                "total_workflow_duration_seconds": rec.get("total_workflow_duration_seconds", 0.0),
                "selected_artifact_count": rec.get("selected_artifact_count", 0),
                "regenerated_artifact_count": rec.get("regenerated_artifact_count", 0),
                "preserved_artifact_count": rec.get("preserved_artifact_count", 0),
                "unresolved_human_review_count": rec.get("unresolved_human_review_count", 0),
            })
    return rows


def _compute_token_totals(
    records: list[RunRecordData],
    planned_set: set[str],
) -> dict[str, Any]:
    """Aggregate token counts from authoritative RunRecords."""
    total_prompt = 0
    total_completion = 0
    total_tokens = 0
    total_model_calls = 0
    included = 0

    for rec in records:
        if rec.run_id not in planned_set:
            continue
        included += 1
        total_model_calls += rec.model_calls
        tok = rec.token_usage
        total_prompt += tok.get("prompt", 0)
        total_completion += tok.get("completion", 0)
        total_tokens += tok.get("total", 0)

    return {
        "total_model_calls": total_model_calls,
        "total_prompt_tokens": total_prompt,
        "total_completion_tokens": total_completion,
        "total_tokens": total_tokens,
        "records_included": included,
    }


def _compute_workflow_totals(
    records: list[RunRecordData],
    planned_set: set[str],
) -> dict[str, Any]:
    """Aggregate end-to-end workflow metrics from authoritative RunRecords.

    For each record, the effective workflow token value is:
      - total_workflow_tokens for end-to-end records
      - token_usage.total for historical impact-only records (no new fields)

    An end-to-end record is identified by having evidence such as:
      functional_validation_passed is not None
      or regeneration_model_calls > 0
      or total_workflow_duration_seconds > 0
      etc.
    """
    total_workflow_tokens = 0
    total_workflow_model_calls = 0
    total_workflow_duration_seconds = 0.0
    effective_workflow_tokens = 0
    included = 0
    e2e_count = 0
    historical_count = 0

    for rec in records:
        if rec.run_id not in planned_set:
            continue
        included += 1
        total_workflow_tokens += rec.total_workflow_tokens
        total_workflow_model_calls += rec.total_workflow_model_calls
        total_workflow_duration_seconds += rec.total_workflow_duration_seconds

        if _is_end_to_end_record(rec):
            e2e_count += 1
            effective_workflow_tokens += rec.total_workflow_tokens
        else:
            historical_count += 1
            effective_workflow_tokens += rec.token_usage.get("total", 0)

    return {
        "total_workflow_tokens": total_workflow_tokens,
        "total_workflow_model_calls": total_workflow_model_calls,
        "total_workflow_duration_seconds": round(total_workflow_duration_seconds, 6),
        "effective_workflow_tokens": effective_workflow_tokens,
        "records_included": included,
        "end_to_end_record_count": e2e_count,
        "historical_record_count": historical_count,
    }


def _is_end_to_end_record(rec: RunRecordData) -> bool:
    """Determine whether a RunRecordData is an end-to-end regeneration record.

    Uses a deterministic compatibility rule based on evidence fields.
    Returns True for end-to-end records (including valid empty-scope runs).
    """
    if rec.functional_validation_passed is not None:
        return True
    if rec.regeneration_model_calls > 0:
        return True
    if rec.regeneration_total_tokens > 0:
        return True
    if rec.selected_artifact_count > 0:
        return True
    if rec.regenerated_artifact_count > 0:
        return True
    if rec.total_workflow_duration_seconds > 0:
        return True
    if rec.total_workflow_tokens > 0:
        return True
    return rec.total_workflow_model_calls > 0


def _compute_duration_totals(
    records: list[RunRecordData],
    planned_set: set[str],
) -> dict[str, Any]:
    """Sum duration_seconds from authoritative RunRecords."""
    total_seconds = 0.0
    included = 0
    for rec in records:
        if rec.run_id not in planned_set:
            continue
        included += 1
        total_seconds += rec.duration_seconds

    return {
        "experiment_run_duration_seconds": round(total_seconds, 6),
        "records_included": included,
    }


# ---------------------------------------------------------------------------
# Deterministic dashboard artifacts (R7B-SMOKE-FINISH)
#
# Four files written after each terminal Run and at final rebuild:
#   dashboard/dashboard_summary.json
#   dashboard/run_matrix.csv
#   dashboard/strategy_summary.csv
#   dashboard/failure_summary.csv
#
# All row ordering is deterministic and no timestamp appears in the
# deterministic comparison fields.
# ---------------------------------------------------------------------------

DASHBOARD_DIR_NAME = "dashboard"

RUN_MATRIX_COLUMNS = (
    "run_id",
    "scenario_id",
    "strategy_name",
    "repetition",
    "status",
    "failure_classification",
    "model_calls",
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "total_workflow_tokens",
    "total_workflow_model_calls",
    "duration_seconds",
    "selected_artifact_count",
    "regenerated_artifact_count",
    "preserved_artifact_count",
    "migration_generation_passed",
    "baseline_validation_passed",
    "scenario_evaluator_passed",
)

STRATEGY_SUMMARY_COLUMNS = (
    "strategy_name",
    "planned",
    "succeeded",
    "failed",
    "model_calls",
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "duration_seconds",
    "selected_artifact_count",
    "regenerated_artifact_count",
    "preserved_artifact_count",
    "migration_passed",
    "baseline_passed",
    "evaluator_passed",
)

FAILURE_SUMMARY_COLUMNS = (
    "failure_classification",
    "count",
    "run_ids",
    "top_messages",
)


def _parse_plan_run_id(run_id: str, strategy_names: list[str]) -> tuple[str, str, int] | None:
    """Recover scenario/strategy/repetition from a canonical planned run id."""
    for sname in strategy_names:
        marker = f"_{sname}_rep"
        if marker in run_id:
            scenario = run_id.split(marker)[0]
            tail = run_id.split(marker, 1)[1]
            rep_str = tail.split("_", 1)[0]
            try:
                rep = int(rep_str)
            except ValueError:
                rep = 0
            return scenario, sname, rep
    return None


def _bool_to_str(value: bool | None) -> str:
    if value is None:
        return ""
    return "true" if value else "false"


def _build_run_matrix_rows(cp: CheckpointData, records: list[RunRecordData]) -> list[dict[str, Any]]:
    """Exact one-row-per-planned-run matrix (3x3 for Smoke), deterministic order."""
    by_run_id = {r.run_id: r for r in records}
    rows: list[dict[str, Any]] = []
    for run_id in sorted(cp.planned_run_ids):
        parsed = _parse_plan_run_id(run_id, cp.strategy_names)
        base = {
            "run_id": run_id,
            "scenario_id": parsed[0] if parsed else "",
            "strategy_name": parsed[1] if parsed else "",
            "repetition": parsed[2] if parsed else 0,
        }
        rec = by_run_id.get(run_id)
        if rec is None:
            rows.append({
                **base,
                "status": "pending",
                "failure_classification": "",
                "model_calls": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "total_workflow_tokens": 0,
                "total_workflow_model_calls": 0,
                "duration_seconds": 0.0,
                "selected_artifact_count": 0,
                "regenerated_artifact_count": 0,
                "preserved_artifact_count": 0,
                "migration_generation_passed": "",
                "baseline_validation_passed": "",
                "scenario_evaluator_passed": "",
            })
            continue
        token_usage = rec.token_usage
        rows.append({
            **base,
            "status": rec.status,
            "failure_classification": rec.failure_classification,
            "model_calls": rec.model_calls,
            "prompt_tokens": token_usage.get("prompt", 0),
            "completion_tokens": token_usage.get("completion", 0),
            "total_tokens": token_usage.get("total", 0),
            "total_workflow_tokens": rec.total_workflow_tokens,
            "total_workflow_model_calls": rec.total_workflow_model_calls,
            "duration_seconds": rec.duration_seconds,
            "selected_artifact_count": rec.selected_artifact_count,
            "regenerated_artifact_count": rec.regenerated_artifact_count,
            "preserved_artifact_count": rec.preserved_artifact_count,
            "migration_generation_passed": _bool_to_str(rec.migration_generation_passed),
            "baseline_validation_passed": _bool_to_str(rec.baseline_validation_passed),
            "scenario_evaluator_passed": _bool_to_str(rec.scenario_evaluator_passed),
        })
    return rows


def _build_strategy_summary_rows(
    cp: CheckpointData, records: list[RunRecordData]
) -> list[dict[str, Any]]:
    """Per-strategy aggregate summary, deterministic order by strategy name."""
    planned_counts: dict[str, int] = {}
    for run_id in cp.planned_run_ids:
        parsed = _parse_plan_run_id(run_id, cp.strategy_names)
        if parsed is not None:
            planned_counts[parsed[1]] = planned_counts.get(parsed[1], 0) + 1

    planned_set = set(cp.planned_run_ids)
    rows: list[dict[str, Any]] = []
    for sname in sorted(cp.strategy_names):
        recs = [r for r in records if r.strategy_id == sname and r.run_id in planned_set]
        rows.append({
            "strategy_name": sname,
            "planned": planned_counts.get(sname, 0),
            "succeeded": sum(1 for r in recs if r.status == "succeeded"),
            "failed": sum(1 for r in recs if r.status in ("failed", "timed_out", "cancelled")),
            "model_calls": sum(r.model_calls for r in recs),
            "prompt_tokens": sum(r.token_usage.get("prompt", 0) for r in recs),
            "completion_tokens": sum(r.token_usage.get("completion", 0) for r in recs),
            "total_tokens": sum(r.token_usage.get("total", 0) for r in recs),
            "duration_seconds": round(sum(r.duration_seconds for r in recs), 6),
            "selected_artifact_count": sum(r.selected_artifact_count for r in recs),
            "regenerated_artifact_count": sum(r.regenerated_artifact_count for r in recs),
            "preserved_artifact_count": sum(r.preserved_artifact_count for r in recs),
            "migration_passed": sum(1 for r in recs if r.migration_generation_passed is True),
            "baseline_passed": sum(1 for r in recs if r.baseline_validation_passed is True),
            "evaluator_passed": sum(1 for r in recs if r.scenario_evaluator_passed is True),
        })
    return rows


def _build_failure_summary_rows(
    records: list[RunRecordData], planned_set: set[str]
) -> list[dict[str, Any]]:
    """Failure summary grouped by primary classification, deterministic order."""
    by_class: dict[str, dict[str, Any]] = {}
    for rec in records:
        if rec.run_id not in planned_set:
            continue
        if rec.status not in ("failed", "timed_out", "cancelled"):
            continue
        classification = rec.failure_classification or "unknown"
        entry = by_class.setdefault(classification, {"count": 0, "run_ids": [], "messages": {}})
        entry["count"] += 1
        entry["run_ids"].append(rec.run_id)
        for fd in rec.failure_details:
            message = str(fd.get("message", "")).strip()
            if message:
                entry["messages"][message] = entry["messages"].get(message, 0) + 1

    rows: list[dict[str, Any]] = []
    for classification in sorted(by_class):
        entry = by_class[classification]
        top_messages = sorted(entry["messages"].items(), key=lambda kv: (-kv[1], kv[0]))[:3]
        rows.append({
            "failure_classification": classification,
            "count": entry["count"],
            "run_ids": ",".join(sorted(entry["run_ids"])),
            "top_messages": " | ".join(f"{m} (x{c})" for m, c in top_messages),
        })
    return rows


def _build_dashboard_summary(
    cp: CheckpointData,
    records: list[RunRecordData],
    matrix_rows: list[dict[str, Any]],
    strategy_rows: list[dict[str, Any]],
    failure_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """KPI summary with no timestamp in deterministic fields."""
    planned_set = set(cp.planned_run_ids)
    completed = [r for r in records if r.run_id in planned_set]
    return {
        "total_planned": len(cp.planned_run_ids),
        "total_completed": len(cp.completed_run_ids),
        "total_succeeded": sum(1 for r in completed if r.status == "succeeded"),
        "total_failed": sum(1 for r in completed if r.status in ("failed", "timed_out", "cancelled")),
        "total_pending": len(cp.pending_run_ids),
        "total_model_calls": sum(r.model_calls for r in completed),
        "total_prompt_tokens": sum(r.token_usage.get("prompt", 0) for r in completed),
        "total_completion_tokens": sum(r.token_usage.get("completion", 0) for r in completed),
        "total_tokens": sum(r.token_usage.get("total", 0) for r in completed),
        "total_duration_seconds": round(sum(r.duration_seconds for r in completed), 6),
        "matrix_row_count": len(matrix_rows),
        "strategy_row_count": len(strategy_rows),
        "failure_row_count": len(failure_rows),
    }


def _write_dashboard_files(
    runs_dir: Path,
    cp: CheckpointData,
    records: list[RunRecordData],
) -> dict[str, Any]:
    """Write the four deterministic dashboard artifacts under runs_dir/dashboard."""
    matrix_rows = _build_run_matrix_rows(cp, records)
    strategy_rows = _build_strategy_summary_rows(cp, records)
    planned_set = set(cp.planned_run_ids)
    failure_rows = _build_failure_summary_rows(records, planned_set)
    summary = _build_dashboard_summary(cp, records, matrix_rows, strategy_rows, failure_rows)

    dashboard_dir = runs_dir / DASHBOARD_DIR_NAME
    dashboard_dir.mkdir(parents=True, exist_ok=True)

    (dashboard_dir / "dashboard_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    with (dashboard_dir / "run_matrix.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RUN_MATRIX_COLUMNS)
        writer.writeheader()
        for row in matrix_rows:
            writer.writerow(row)
    with (dashboard_dir / "strategy_summary.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=STRATEGY_SUMMARY_COLUMNS)
        writer.writeheader()
        for row in strategy_rows:
            writer.writerow(row)
    with (dashboard_dir / "failure_summary.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FAILURE_SUMMARY_COLUMNS)
        writer.writeheader()
        for row in failure_rows:
            writer.writerow(row)

    return summary


def write_dashboard_artifacts(runs_dir: Path) -> dict[str, Any]:
    """Rebuild the deterministic dashboard artifacts from persisted evidence."""
    cp = _load_checkpoint(runs_dir)
    records = _load_all_records(runs_dir)
    return _write_dashboard_files(runs_dir, cp, records)


def rebuild_experiment_reports(
    runs_dir: Path,
    *,
    session_elapsed_seconds: float = 0.0,
) -> dict[str, Any]:
    """Rebuild all derived reporting artifacts from checkpoint + persisted records.

    This function is:
    - Pure / offline: no model inference, no GPU, no HF token
    - Idempotent: same checkpoint + same records → same reports
    - Deterministic: timestamps excluded from comparison

    Args:
        runs_dir: Directory containing checkpoint.json and run_records.jsonl
        session_elapsed_seconds: Wall-clock time of the current invocation (optional)

    Returns:
        Audit report dict with validation results.

    Raises:
        ReportRebuildError: If raw evidence is inconsistent.
    """
    cp = _load_checkpoint(runs_dir)
    records = _load_all_records(runs_dir)

    # Validate raw evidence
    _validate_evidence(cp, records)

    planned_set = set(cp.planned_run_ids)

    # Build results_agg from ALL persisted records
    results_agg = _build_results_agg_from_records(records, cp.planned_run_ids)

    # --- Ensure every planned strategy has an entry ---
    for sname in cp.strategy_names:
        if sname not in results_agg:
            results_agg[sname] = {
                "success_count": 0,
                "failure_count": 0,
                "timeout_count": 0,
                "records": [],
            }

    # --- Aggregate metrics ---
    token_totals = _compute_token_totals(records, planned_set)
    workflow_totals = _compute_workflow_totals(records, planned_set)
    duration_totals = _compute_duration_totals(records, planned_set)

    # --- Write benchmark_summary.json ---
    progress_mgr = ProgressManager(runs_dir)
    progress_mgr.write_final_summary(results_agg)

    # --- Write benchmark_summary.partial.json ---
    progress_mgr.write_partial_summary(results_agg)

    # --- Write smoke_progress_summary.json ---
    smoke_summary = _build_smoke_summary_from_agg(
        all_strategy_names=cp.strategy_names,
        results_agg=results_agg,
        planned_run_ids=cp.planned_run_ids,
        checkpoint_completed=cp.completed_run_ids,
        checkpoint_failed=cp.failed_run_ids,
        pending_run_ids=cp.pending_run_ids,
    )
    smoke_path = runs_dir / "smoke_progress_summary.json"
    smoke_path.write_text(json.dumps(smoke_summary, indent=2), encoding="utf-8")

    # --- Write deterministic dashboard artifacts (R7B-SMOKE-FINISH) ---------
    _write_dashboard_files(runs_dir, cp, records)

    # --- Write progress.json ---
    is_completed = cp.completion_status == "completed"
    stage = "completed" if is_completed else "running"
    total_succeeded = len(cp.succeeded_run_ids)
    total_failed = len(cp.failed_run_ids)
    total_retryable = len(cp.retryable_run_ids)
    total_pending = len(cp.pending_run_ids)
    total_completed = len(cp.completed_run_ids)

    progress_data = ProgressData(
        profile=cp.profile,
        total_planned=cp.total_planned,
        total_completed=total_completed,
        total_failed=total_failed,
        total_pending=total_pending,
        elapsed_seconds=session_elapsed_seconds,
        completion_ratio=total_completed / max(cp.total_planned, 1),
        stage=stage,
        total_attempted=len(cp.attempted_run_ids),
        total_succeeded=total_succeeded,
        total_retryable=total_retryable,
        completion_status=cp.completion_status,
        experiment_run_duration_seconds=duration_totals["experiment_run_duration_seconds"],
        session_elapsed_seconds=session_elapsed_seconds,
        report_generated_at=datetime.now(UTC).isoformat(),
        experiment_wall_clock_seconds=None,
        experiment_wall_clock_unavailable_reason="cross-session idle intervals are not measured" if not is_completed else "",
    )
    progress_mgr.write(progress_data)

    # --- Audit report ---
    matched_ids = planned_set & {r.run_id for r in records}
    missing_ids = planned_set - {r.run_id for r in records}
    seen_ids: dict[str, int] = {}
    for r in records:
        if r.run_id in planned_set:
            seen_ids[r.run_id] = seen_ids.get(r.run_id, 0) + 1
    duplicate_ids = [rid for rid, cnt in seen_ids.items() if cnt > 1]

    audit = {
        "raw_run_record_count": len(records),
        "planned_run_id_count": len(cp.planned_run_ids),
        "matched_run_ids": sorted(matched_ids),
        "missing_run_ids": sorted(missing_ids),
        "duplicate_run_ids": sorted(duplicate_ids),
        "unexpected_run_ids": sorted({r.run_id for r in records} - planned_set),
        "token_totals": token_totals,
        "workflow_totals": workflow_totals,
        "duration_totals": duration_totals,
        "final_status": cp.completion_status,
        "total_succeeded": sum(1 for r in records if r.run_id in planned_set and r.status == "succeeded"),
        "total_failed": sum(1 for r in records if r.run_id in planned_set and r.status in ("failed", "timed_out", "cancelled")),
        "total_retryable": sum(1 for r in records if r.run_id in planned_set and r.status in ("failed", "timed_out", "cancelled") and r.failure_classification in ("environment_preflight", "environment", "gpu_incompatible", "cuda_error")),
        "total_pending": total_pending,
    }

    return audit
