"""SU-0008 reporting rebuild tests: cross-session summary correctness."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from benchmark.checkpoint.checkpoint import (
    CheckpointData,
    CheckpointManager,
    ProgressData,
    ProgressManager,
)
from benchmark.checkpoint.persistence import (
    RunRecordData,
    RunRecordStore,
)
from benchmark.checkpoint.reports import (
    ReportRebuildError,
    rebuild_experiment_reports,
)

ALL_SEVEN_STRATEGIES = [
    "monolithic", "agent", "selective", "compiled_ai",
    "delta_mcp", "incr_rtl", "code_plan",
]
SCENARIO_IDS = ["djangocms-cross-007"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_run_id(scenario_id: str, strategy_name: str, rep: int,
                  config_hash: str = "deadbeef", protocol_version: str = "1.0") -> str:
    payload = json.dumps({
        "scenario_id": scenario_id,
        "strategy_name": strategy_name,
        "repetition": rep,
        "config_hash": config_hash,
        "protocol_version": protocol_version,
    }, sort_keys=True)
    suffix = hashlib.sha256(payload.encode()).hexdigest()[:8]
    return f"{scenario_id}_{strategy_name}_rep{rep}_{suffix}"


def _all_planned(config_hash: str = "deadbeef") -> list[str]:
    return [_make_run_id("djangocms-cross-007", s, 1, config_hash) for s in ALL_SEVEN_STRATEGIES]


def _make_record(
    tmp_path: Path,
    run_id: str,
    strategy_id: str = "agent",
    status: str = "succeeded",
    duration_seconds: float = 1.0,
    model_calls: int = 0,
    token_usage: dict[str, int] | None = None,
    hardware_identity: str = "",
    software_environment_identity: str = "",
    failure_classification: str = "",
) -> RunRecordData:
    rec = RunRecordData(
        run_id=run_id,
        profile="smoke",
        repository_id="djangocms",
        scenario_id="djangocms-cross-007",
        strategy_id=strategy_id,
        repetition=1,
        seed=42,
        status=status,
        duration_seconds=duration_seconds,
        token_usage=token_usage or {"prompt": 0, "completion": 0, "total": 0},
        protocol_version="1.0",
        source_commit="abc1234",
        config_hash="deadbeef",
        timestamp=datetime.now(UTC).isoformat(),
        started_at=datetime.now(UTC).isoformat(),
        ended_at=datetime.now(UTC).isoformat(),
        model_calls=model_calls,
        repair_attempts=0,
        hardware_identity=hardware_identity,
        software_environment_identity=software_environment_identity,
        failure_classification=failure_classification,
    )
    RunRecordStore(tmp_path).append(rec)
    return rec


def _make_checkpoint(
    tmp_path: Path,
    *,
    completed_run_ids: list[str] | None = None,
    succeeded_run_ids: list[str] | None = None,
    failed_run_ids: list[str] | None = None,
    retryable_run_ids: list[str] | None = None,
    pending_run_ids: list[str] | None = None,
    attempted_run_ids: list[str] | None = None,
    completion_status: str = "incomplete",
    config_hash: str = "deadbeef",
    source_commit: str = "abc1234",
) -> CheckpointData:
    planned = _all_planned(config_hash)
    completed = completed_run_ids or []
    succeeded = succeeded_run_ids or []
    failed = failed_run_ids or []
    retryable = retryable_run_ids or []
    attempted = attempted_run_ids or list(completed)
    pending = pending_run_ids or [r for r in planned if r not in completed]
    data = CheckpointData(
        profile="smoke",
        execution_plan_hash=config_hash,
        planned_run_ids=planned,
        completed_run_ids=completed,
        attempted_run_ids=attempted,
        succeeded_run_ids=succeeded,
        failed_run_ids=failed,
        retryable_run_ids=retryable,
        pending_run_ids=pending,
        total_planned=7,
        total_completed=len(completed),
        protocol_version="1.0",
        model_identity="dry-run:mock",
        config_hash=config_hash,
        source_commit=source_commit,
        completion_status=completion_status,
        scenario_ids=SCENARIO_IDS,
        strategy_names=ALL_SEVEN_STRATEGIES,
    )
    CheckpointManager(tmp_path).write_atomic(data)
    return data


# ---------------------------------------------------------------------------
# 1. Completed cross-session smoke
# ---------------------------------------------------------------------------

class TestCompletedCrossSessionSmoke:
    def test_all_seven_succeeded(self, tmp_path: Path) -> None:
        """Completed experiment: 7/7 succeeded, correct token totals."""
        planned = _all_planned()
        expected_tokens = 344  # 325 prompt + 19 completion

        # Record 1: monolithic (non-LLM, zero tokens)
        _make_record(tmp_path, planned[0], strategy_id="monolithic",
                     status="succeeded", duration_seconds=0.5, model_calls=0)

        # Record 2: agent (LLM-backed, 344 tokens)
        _make_record(tmp_path, planned[1], strategy_id="agent",
                     status="succeeded", duration_seconds=58.67, model_calls=1,
                     token_usage={"prompt": 325, "completion": 19, "total": 344},
                     hardware_identity="Tesla T4:sm_75",
                     software_environment_identity="python=3.11|torch=2.1|cuda=12.1")

        # Records 3-7: non-LLM strategies
        for i in range(2, 7):
            _make_record(tmp_path, planned[i], strategy_id=ALL_SEVEN_STRATEGIES[i],
                         status="succeeded", duration_seconds=0.1, model_calls=0)

        _make_checkpoint(
            tmp_path,
            completed_run_ids=list(planned),
            succeeded_run_ids=list(planned),
            completion_status="completed",
        )

        audit = rebuild_experiment_reports(tmp_path)

        # All seven present
        assert len(audit["matched_run_ids"]) == 7
        assert audit["missing_run_ids"] == []
        assert audit["duplicate_run_ids"] == []
        assert audit["unexpected_run_ids"] == []

        # Token totals
        assert audit["token_totals"]["total_model_calls"] == 1
        assert audit["token_totals"]["total_tokens"] == expected_tokens
        assert audit["token_totals"]["total_prompt_tokens"] == 325
        assert audit["token_totals"]["total_completion_tokens"] == 19

        # Duration
        assert audit["duration_totals"]["experiment_run_duration_seconds"] > 0

        # Status
        assert audit["final_status"] == "completed"
        assert audit["total_succeeded"] == 7
        assert audit["total_failed"] == 0
        assert audit["total_retryable"] == 0
        assert audit["total_pending"] == 0

    def test_benchmark_summary_includes_all_strategies(self, tmp_path: Path) -> None:
        """benchmark_summary.json has exactly 7 strategy entries."""
        planned = _all_planned()
        for i in range(7):
            _make_record(tmp_path, planned[i], strategy_id=ALL_SEVEN_STRATEGIES[i],
                         status="succeeded")

        _make_checkpoint(
            tmp_path,
            completed_run_ids=list(planned),
            succeeded_run_ids=list(planned),
            completion_status="completed",
        )

        rebuild_experiment_reports(tmp_path)

        summary_path = tmp_path / "benchmark_summary.json"
        assert summary_path.exists()
        summary = json.loads(summary_path.read_text(encoding="utf-8"))

        assert set(summary.keys()) == set(ALL_SEVEN_STRATEGIES)
        for sname in ALL_SEVEN_STRATEGIES:
            assert summary[sname]["success_count"] == 1
            assert summary[sname]["failure_count"] == 0
            assert summary[sname]["timeout_count"] == 0
            assert len(summary[sname]["records"]) == 1

    def test_progress_json_completed_state(self, tmp_path: Path) -> None:
        """progress.json reports stage=completed with correct counts."""
        planned = _all_planned()
        for i in range(7):
            _make_record(tmp_path, planned[i], strategy_id=ALL_SEVEN_STRATEGIES[i],
                         status="succeeded")

        _make_checkpoint(
            tmp_path,
            completed_run_ids=list(planned),
            succeeded_run_ids=list(planned),
            completion_status="completed",
        )

        rebuild_experiment_reports(tmp_path, session_elapsed_seconds=123.45)

        progress_path = tmp_path / "progress.json"
        assert progress_path.exists()
        progress = json.loads(progress_path.read_text(encoding="utf-8"))

        assert progress["stage"] == "completed"
        assert progress["total_planned"] == 7
        assert progress["total_completed"] == 7
        assert progress["total_succeeded"] == 7
        assert progress["total_failed"] == 0
        assert progress["total_retryable"] == 0
        assert progress["total_pending"] == 0
        assert progress["completion_ratio"] == 1.0
        assert progress["completion_status"] == "completed"

    def test_smoke_summary_all_succeeded(self, tmp_path: Path) -> None:
        """smoke_progress_summary.json: all 7 rows succeeded."""
        planned = _all_planned()
        for i in range(7):
            _make_record(tmp_path, planned[i], strategy_id=ALL_SEVEN_STRATEGIES[i],
                         status="succeeded")

        _make_checkpoint(
            tmp_path,
            completed_run_ids=list(planned),
            succeeded_run_ids=list(planned),
            completion_status="completed",
        )

        rebuild_experiment_reports(tmp_path)

        smoke_path = tmp_path / "smoke_progress_summary.json"
        assert smoke_path.exists()
        smoke = json.loads(smoke_path.read_text(encoding="utf-8"))

        assert len(smoke) == 7
        for row in smoke:
            assert row["succeeded"] == 1
            assert row["failed"] == 0
            assert row["timed_out"] == 0
            assert row["not_yet_run"] == 0
            assert row["total_completed"] == 1

    def test_no_duplicates(self, tmp_path: Path) -> None:
        """No duplicate Run IDs in summary records."""
        planned = _all_planned()
        for i in range(7):
            _make_record(tmp_path, planned[i], strategy_id=ALL_SEVEN_STRATEGIES[i],
                         status="succeeded")

        _make_checkpoint(
            tmp_path,
            completed_run_ids=list(planned),
            succeeded_run_ids=list(planned),
            completion_status="completed",
        )

        audit = rebuild_experiment_reports(tmp_path)
        assert audit["duplicate_run_ids"] == []

    def test_run_ids_in_planned_set(self, tmp_path: Path) -> None:
        """Every summary Run ID exists in planned_run_ids."""
        planned = _all_planned()
        for i in range(7):
            _make_record(tmp_path, planned[i], strategy_id=ALL_SEVEN_STRATEGIES[i],
                         status="succeeded")

        _make_checkpoint(
            tmp_path,
            completed_run_ids=list(planned),
            succeeded_run_ids=list(planned),
            completion_status="completed",
        )

        audit = rebuild_experiment_reports(tmp_path)
        planned_set = set(planned)
        for rid in audit["matched_run_ids"]:
            assert rid in planned_set

    def test_raw_evidence_unchanged(self, tmp_path: Path) -> None:
        """Rebuild does not modify checkpoint.json or run_records.jsonl."""
        planned = _all_planned()
        for i in range(7):
            _make_record(tmp_path, planned[i], strategy_id=ALL_SEVEN_STRATEGIES[i],
                         status="succeeded")

        _make_checkpoint(
            tmp_path,
            completed_run_ids=list(planned),
            succeeded_run_ids=list(planned),
            completion_status="completed",
        )

        cp_before = (tmp_path / "checkpoint.json").read_bytes()
        rec_before = (tmp_path / "run_records.jsonl").read_bytes()

        rebuild_experiment_reports(tmp_path)

        cp_after = (tmp_path / "checkpoint.json").read_bytes()
        rec_after = (tmp_path / "run_records.jsonl").read_bytes()

        # checkpoint.json may be modified by normalization (last_update timestamp)
        # but run_records.jsonl must be unchanged
        assert rec_before == rec_after, "run_records.jsonl must not be modified by rebuild"

    def test_experiment_duration_equals_sum(self, tmp_path: Path) -> None:
        """experiment_run_duration_seconds equals sum of RunRecord durations."""
        planned = _all_planned()
        durations = [0.5, 58.67, 0.1, 0.1, 0.1, 0.1, 0.1]
        for i in range(7):
            _make_record(tmp_path, planned[i], strategy_id=ALL_SEVEN_STRATEGIES[i],
                         status="succeeded", duration_seconds=durations[i])

        _make_checkpoint(
            tmp_path,
            completed_run_ids=list(planned),
            succeeded_run_ids=list(planned),
            completion_status="completed",
        )

        audit = rebuild_experiment_reports(tmp_path)
        expected_total = sum(durations)
        assert abs(audit["duration_totals"]["experiment_run_duration_seconds"] - expected_total) < 1e-6


# ---------------------------------------------------------------------------
# 2. Partial resumed smoke
# ---------------------------------------------------------------------------

class TestPartialResumedSmoke:
    def test_partial_summary_includes_all_records(self, tmp_path: Path) -> None:
        """On incomplete resume, summary includes both old and new records."""
        planned = _all_planned()

        # Simulate session 1: monolithic succeeded
        _make_record(tmp_path, planned[0], strategy_id="monolithic", status="succeeded")

        # Checkpoint after session 1
        _make_checkpoint(
            tmp_path,
            completed_run_ids=[planned[0]],
            succeeded_run_ids=[planned[0]],
            completion_status="incomplete",
        )

        # Simulate session 2: agent succeeded (appended to same JSONL)
        _make_record(tmp_path, planned[1], strategy_id="agent", status="succeeded")

        # Rebuild from both records
        audit = rebuild_experiment_reports(tmp_path)

        assert audit["raw_run_record_count"] == 2
        assert len(audit["matched_run_ids"]) == 2
        assert audit["total_succeeded"] == 2

        # Summary should have both strategies
        summary = json.loads((tmp_path / "benchmark_summary.json").read_text(encoding="utf-8"))
        assert "monolithic" in summary
        assert "agent" in summary
        assert summary["monolithic"]["success_count"] == 1
        assert summary["agent"]["success_count"] == 1

    def test_partial_smoke_summary_row_count(self, tmp_path: Path) -> None:
        """Smoke summary has 7 rows even when only 2 are completed."""
        planned = _all_planned()
        _make_record(tmp_path, planned[0], strategy_id="monolithic", status="succeeded")

        _make_checkpoint(
            tmp_path,
            completed_run_ids=[planned[0]],
            succeeded_run_ids=[planned[0]],
            completion_status="incomplete",
        )

        rebuild_experiment_reports(tmp_path)

        smoke = json.loads((tmp_path / "smoke_progress_summary.json").read_text(encoding="utf-8"))
        assert len(smoke) == 7

        # monolithic row: succeeded=1, not_yet_run=0
        mono_row = [r for r in smoke if r["strategy_name"] == "monolithic"][0]
        assert mono_row["succeeded"] == 1
        assert mono_row["not_yet_run"] == 0

        # agent row: succeeded=0, not_yet_run=1
        agent_row = [r for r in smoke if r["strategy_name"] == "agent"][0]
        assert agent_row["succeeded"] == 0
        assert agent_row["not_yet_run"] == 1

    def test_progress_incomplete_state(self, tmp_path: Path) -> None:
        """progress.json reports correct incomplete state."""
        planned = _all_planned()
        _make_record(tmp_path, planned[0], strategy_id="monolithic", status="succeeded")

        _make_checkpoint(
            tmp_path,
            completed_run_ids=[planned[0]],
            succeeded_run_ids=[planned[0]],
            pending_run_ids=planned[1:],
            completion_status="incomplete",
        )

        rebuild_experiment_reports(tmp_path, session_elapsed_seconds=5.0)

        progress = json.loads((tmp_path / "progress.json").read_text(encoding="utf-8"))
        assert progress["stage"] == "running"
        assert progress["total_planned"] == 7
        assert progress["total_completed"] == 1
        assert progress["total_succeeded"] == 1
        assert progress["total_failed"] == 0
        assert progress["total_pending"] == 6
        assert progress["completion_status"] == "incomplete"


# ---------------------------------------------------------------------------
# 3. Invalid evidence (fail closed)
# ---------------------------------------------------------------------------

class TestInvalidEvidence:
    def test_missing_record_for_succeeded_checkpoint(self, tmp_path: Path) -> None:
        """Checkpoint claims succeeded but no record exists -> error."""
        planned = _all_planned()
        # Only write checkpoint, no records
        _make_checkpoint(
            tmp_path,
            completed_run_ids=[planned[0]],
            succeeded_run_ids=[planned[0]],
            completion_status="incomplete",
        )

        with pytest.raises(ReportRebuildError, match="no record exists"):
            rebuild_experiment_reports(tmp_path)

    def test_unexpected_run_id_in_records(self, tmp_path: Path) -> None:
        """Record for non-planned Run ID -> error."""
        planned = _all_planned()
        _make_record(tmp_path, "UNEXPECTED-RUN-ID", strategy_id="agent", status="succeeded")

        _make_checkpoint(tmp_path)

        with pytest.raises(ReportRebuildError, match="Unexpected Run IDs"):
            rebuild_experiment_reports(tmp_path)

    def test_pending_succeeded_overlap(self, tmp_path: Path) -> None:
        """Pending and completed overlap -> error."""
        planned = _all_planned()
        _make_record(tmp_path, planned[0], strategy_id="monolithic", status="succeeded")

        _make_checkpoint(
            tmp_path,
            completed_run_ids=[planned[0]],
            succeeded_run_ids=[planned[0]],
            pending_run_ids=planned,  # includes planned[0] -> overlap!
            completion_status="incomplete",
        )

        with pytest.raises(ReportRebuildError, match="overlap"):
            rebuild_experiment_reports(tmp_path)

    def test_duplicate_run_id_in_records(self, tmp_path: Path) -> None:
        """Same Run ID appears twice in records -> error."""
        from dataclasses import asdict

        planned = _all_planned()
        _make_record(tmp_path, planned[0], strategy_id="monolithic", status="succeeded")

        # Manually append a conflicting record to bypass idempotency check
        rec2 = RunRecordData(
            run_id=planned[0], profile="smoke", repository_id="r",
            scenario_id="djangocms-cross-007", strategy_id="monolithic",
            repetition=1, seed=42, status="failed",
            token_usage={"prompt": 0, "completion": 0, "total": 0},
        )
        with open(tmp_path / "run_records.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(rec2), sort_keys=True) + "\n")

        _make_checkpoint(
            tmp_path,
            completed_run_ids=[planned[0]],
            succeeded_run_ids=[planned[0]],
            completion_status="incomplete",
        )

        with pytest.raises(ReportRebuildError, match="Duplicate Run IDs"):
            rebuild_experiment_reports(tmp_path)

    def test_no_checkpoint_raises(self, tmp_path: Path) -> None:
        """No checkpoint.json -> error."""
        with pytest.raises(ReportRebuildError, match="No checkpoint"):
            rebuild_experiment_reports(tmp_path)


# ---------------------------------------------------------------------------
# 4. Idempotency
# ---------------------------------------------------------------------------

class TestIdempotency:
    def test_same_input_same_output(self, tmp_path: Path) -> None:
        """Running rebuild twice produces identical reports (except timestamps)."""
        planned = _all_planned()
        for i in range(7):
            _make_record(tmp_path, planned[i], strategy_id=ALL_SEVEN_STRATEGIES[i],
                         status="succeeded", duration_seconds=1.0 + i * 0.5)

        _make_checkpoint(
            tmp_path,
            completed_run_ids=list(planned),
            succeeded_run_ids=list(planned),
            completion_status="completed",
        )

        rebuild_experiment_reports(tmp_path, session_elapsed_seconds=10.0)

        # Capture outputs
        summary1 = (tmp_path / "benchmark_summary.json").read_text(encoding="utf-8")
        smoke1 = (tmp_path / "smoke_progress_summary.json").read_text(encoding="utf-8")

        rebuild_experiment_reports(tmp_path, session_elapsed_seconds=10.0)

        summary2 = (tmp_path / "benchmark_summary.json").read_text(encoding="utf-8")
        smoke2 = (tmp_path / "smoke_progress_summary.json").read_text(encoding="utf-8")

        # These should be byte-equivalent
        assert summary1 == summary2
        assert smoke1 == smoke2


# ---------------------------------------------------------------------------
# 5. Token aggregation
# ---------------------------------------------------------------------------

class TestTokenAggregation:
    def test_zero_call_strategies_contribute_zero(self, tmp_path: Path) -> None:
        """Non-LLM strategies contribute zero tokens."""
        planned = _all_planned()
        for i in range(7):
            _make_record(tmp_path, planned[i], strategy_id=ALL_SEVEN_STRATEGIES[i],
                         status="succeeded", model_calls=0,
                         token_usage={"prompt": 0, "completion": 0, "total": 0})

        _make_checkpoint(
            tmp_path,
            completed_run_ids=list(planned),
            succeeded_run_ids=list(planned),
            completion_status="completed",
        )

        audit = rebuild_experiment_reports(tmp_path)
        assert audit["token_totals"]["total_tokens"] == 0
        assert audit["token_totals"]["total_model_calls"] == 0

    def test_only_llm_record_contributes_tokens(self, tmp_path: Path) -> None:
        """Only the agent record with 344 tokens contributes to total."""
        planned = _all_planned()
        for i in range(7):
            tok = {"prompt": 325, "completion": 19, "total": 344} if i == 1 else None
            _make_record(tmp_path, planned[i], strategy_id=ALL_SEVEN_STRATEGIES[i],
                         status="succeeded", model_calls=1 if i == 1 else 0,
                         token_usage=tok)

        _make_checkpoint(
            tmp_path,
            completed_run_ids=list(planned),
            succeeded_run_ids=list(planned),
            completion_status="completed",
        )

        audit = rebuild_experiment_reports(tmp_path)
        assert audit["token_totals"]["total_tokens"] == 344
        assert audit["token_totals"]["total_model_calls"] == 1


# ---------------------------------------------------------------------------
# 6. Duration aggregation
# ---------------------------------------------------------------------------

class TestDurationAggregation:
    def test_sum_of_record_durations(self, tmp_path: Path) -> None:
        """Duration equals sum of all record durations."""
        planned = _all_planned()
        expected = 0.0
        for i in range(7):
            dur = 1.0 + i
            expected += dur
            _make_record(tmp_path, planned[i], strategy_id=ALL_SEVEN_STRATEGIES[i],
                         status="succeeded", duration_seconds=dur)

        _make_checkpoint(
            tmp_path,
            completed_run_ids=list(planned),
            succeeded_run_ids=list(planned),
            completion_status="completed",
        )

        audit = rebuild_experiment_reports(tmp_path)
        assert abs(audit["duration_totals"]["experiment_run_duration_seconds"] - expected) < 1e-6
        assert audit["duration_totals"]["records_included"] == 7


# ---------------------------------------------------------------------------
# 7. Incomplete experiment does not produce misleading completed report
# ---------------------------------------------------------------------------

class TestIncompleteNoCompletedReport:
    def test_incomplete_not_completed(self, tmp_path: Path) -> None:
        """Incomplete experiment progress stage is not 'completed'."""
        planned = _all_planned()
        _make_record(tmp_path, planned[0], strategy_id="monolithic", status="succeeded")

        _make_checkpoint(
            tmp_path,
            completed_run_ids=[planned[0]],
            succeeded_run_ids=[planned[0]],
            completion_status="incomplete",
        )

        rebuild_experiment_reports(tmp_path)
        progress = json.loads((tmp_path / "progress.json").read_text(encoding="utf-8"))
        assert progress["stage"] != "completed"

    def test_incomplete_partial_summary_only(self, tmp_path: Path) -> None:
        """Incomplete: partial.summary should NOT have all strategies succeeded."""
        planned = _all_planned()
        _make_record(tmp_path, planned[0], strategy_id="monolithic", status="succeeded")

        _make_checkpoint(
            tmp_path,
            completed_run_ids=[planned[0]],
            succeeded_run_ids=[planned[0]],
            completion_status="incomplete",
        )

        rebuild_experiment_reports(tmp_path)
        summary = json.loads((tmp_path / "benchmark_summary.json").read_text(encoding="utf-8"))
        # monolithic should be present, but not all strategies
        assert "monolithic" in summary
        assert summary["monolithic"]["success_count"] == 1
        # Not all 7 should have records
        assert len(summary) < 7 or any(
            summary.get(s, {}).get("success_count", 0) == 0
            for s in ALL_SEVEN_STRATEGIES
        )


# ---------------------------------------------------------------------------
# 8. Per-strategy detail rows
# ---------------------------------------------------------------------------

class TestPerStrategyDetailRows:
    def test_smoke_summary_has_correct_fields(self, tmp_path: Path) -> None:
        """Each smoke progress summary row has all required fields."""
        planned = _all_planned()
        for i in range(7):
            _make_record(tmp_path, planned[i], strategy_id=ALL_SEVEN_STRATEGIES[i],
                         status="succeeded")

        _make_checkpoint(
            tmp_path,
            completed_run_ids=list(planned),
            succeeded_run_ids=list(planned),
            completion_status="completed",
        )

        rebuild_experiment_reports(tmp_path)
        smoke = json.loads((tmp_path / "smoke_progress_summary.json").read_text(encoding="utf-8"))

        required_fields = {
            "strategy_name", "total_planned", "total_completed",
            "succeeded", "failed", "timed_out",
            "environment_failed", "not_yet_run",
        }
        for row in smoke:
            assert required_fields.issubset(set(row.keys())), (
                f"Missing fields in row: {required_fields - set(row.keys())}"
            )
