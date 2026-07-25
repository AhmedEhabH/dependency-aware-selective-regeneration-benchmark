from __future__ import annotations

import hashlib
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
        }
        agg[sname]["records"].append(record_dict)
        if rec.status == "succeeded":
            agg[sname]["success_count"] += 1
        elif rec.status == "failed":
            agg[sname]["failure_count"] += 1
        elif rec.status == "timed_out":
            agg[sname]["timeout_count"] += 1

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
        "duration_totals": duration_totals,
        "final_status": cp.completion_status,
        "total_succeeded": sum(1 for r in records if r.run_id in planned_set and r.status == "succeeded"),
        "total_failed": sum(1 for r in records if r.run_id in planned_set and r.status in ("failed", "timed_out", "cancelled")),
        "total_retryable": sum(1 for r in records if r.run_id in planned_set and r.status in ("failed", "timed_out", "cancelled") and r.failure_classification in ("environment_preflight", "environment", "gpu_incompatible", "cuda_error")),
        "total_pending": total_pending,
    }

    return audit
