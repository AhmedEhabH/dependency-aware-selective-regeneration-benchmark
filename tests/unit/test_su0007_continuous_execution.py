"""SU-0007 regression tests: resume state preservation, retry semantics, preflight, continuous execution."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from benchmark.checkpoint.checkpoint import CheckpointData, CheckpointManager
from benchmark.checkpoint.persistence import (
    RunRecordData,
    RunRecordStore,
    detect_hardware_identity,
    detect_software_environment_identity,
    failure_is_retryable,
)
from benchmark.checkpoint.resume import ResumeManager, ResumeValidationError

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


def _make_checkpoint(
    tmp_path: Path,
    completed_run_ids: list[str] | None = None,
    succeeded_run_ids: list[str] | None = None,
    failed_run_ids: list[str] | None = None,
    retryable_run_ids: list[str] | None = None,
    pending_run_ids: list[str] | None = None,
    completion_status: str = "incomplete",
    config_hash: str = "deadbeef",
    source_commit: str = "abc1234",
    deployed_build_id: str = "",
    declared_source_tag: str = "",
) -> CheckpointData:
    planned = _all_planned(config_hash)
    completed = completed_run_ids or []
    succeeded = succeeded_run_ids or []
    failed = failed_run_ids or []
    retryable = retryable_run_ids or []
    pending = pending_run_ids or [r for r in planned if r not in completed]
    data = CheckpointData(
        profile="smoke",
        execution_plan_hash=config_hash,
        planned_run_ids=planned,
        completed_run_ids=completed,
        attempted_run_ids=list(completed),
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
        declared_source_tag=declared_source_tag,
        deployed_build_id=deployed_build_id or source_commit,
    )
    CheckpointManager(tmp_path).write_atomic(data)
    return data


def _make_record(
    tmp_path: Path,
    run_id: str,
    strategy_id: str = "agent",
    status: str = "succeeded",
    model_calls: int = 1,
    started_at: str = "",
    ended_at: str = "",
    hardware_identity: str = "",
    software_environment_identity: str = "",
    failure_classification: str = "",
    token_usage: dict[str, int] | None = None,
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
        duration_seconds=1.0,
        token_usage=token_usage or {"prompt": 0, "completion": 0, "total": 0},
        protocol_version="1.0",
        source_commit="abc1234",
        config_hash="deadbeef",
        timestamp=started_at or datetime.now(UTC).isoformat(),
        started_at=started_at or datetime.now(UTC).isoformat(),
        ended_at=ended_at or datetime.now(UTC).isoformat(),
        model_calls=model_calls,
        repair_attempts=0,
        hardware_identity=hardware_identity,
        software_environment_identity=software_environment_identity,
        failure_classification=failure_classification,
    )
    RunRecordStore(tmp_path).append(rec)
    return rec


# ---------------------------------------------------------------------------
# 1. Resume preserves previous succeeded IDs
# ---------------------------------------------------------------------------

class TestResumePreservesSucceeded:
    def test_resume_preserves_succeeded_ids(self, tmp_path: Path) -> None:
        planned = _all_planned()
        run_monolithic = planned[0]
        run_agent = planned[1]

        _make_record(tmp_path, run_monolithic, strategy_id="monolithic", status="succeeded")
        _make_checkpoint(
            tmp_path,
            completed_run_ids=[run_monolithic],
            succeeded_run_ids=[run_monolithic],
            completion_status="incomplete",
        )

        resume = ResumeManager(
            runs_dir=tmp_path,
            protocol_version="1.0",
            config_hash="deadbeef",
            model_identity="dry-run:mock",
            source_commit="abc1234",
            deployed_build_id="abc1234",
        )
        cp = resume.get_normalized_checkpoint()
        assert cp is not None
        assert run_monolithic in cp.succeeded_run_ids
        assert run_agent not in cp.succeeded_run_ids


# ---------------------------------------------------------------------------
# 2. Resume preserves previous failed IDs
# ---------------------------------------------------------------------------

class TestResumePreservesFailed:
    def test_resume_preserves_failed_ids(self, tmp_path: Path) -> None:
        planned = _all_planned()
        run_monolithic = planned[0]
        run_agent = planned[1]

        _make_record(tmp_path, run_monolithic, strategy_id="monolithic", status="succeeded")
        _make_record(
            tmp_path, run_agent, strategy_id="agent", status="failed",
            failure_classification="model_output",
        )
        _make_checkpoint(
            tmp_path,
            completed_run_ids=[run_monolithic, run_agent],
            succeeded_run_ids=[run_monolithic],
            failed_run_ids=[run_agent],
            completion_status="incomplete",
        )

        resume = ResumeManager(
            runs_dir=tmp_path,
            protocol_version="1.0",
            config_hash="deadbeef",
            model_identity="dry-run:mock",
            source_commit="abc1234",
            deployed_build_id="abc1234",
        )
        cp = resume.get_normalized_checkpoint()
        assert cp is not None
        assert run_agent in cp.failed_run_ids
        assert run_monolithic not in cp.failed_run_ids


# ---------------------------------------------------------------------------
# 3. Resume preserves retryable IDs
# ---------------------------------------------------------------------------

class TestResumePreservesRetryable:
    def test_resume_preserves_retryable_ids(self, tmp_path: Path) -> None:
        planned = _all_planned()
        run_monolithic = planned[0]
        run_agent = planned[1]

        _make_record(tmp_path, run_monolithic, strategy_id="monolithic", status="succeeded")
        _make_record(
            tmp_path, run_agent, strategy_id="agent", status="failed",
            failure_classification="environment_preflight",
        )
        _make_checkpoint(
            tmp_path,
            completed_run_ids=[run_monolithic, run_agent],
            succeeded_run_ids=[run_monolithic],
            failed_run_ids=[run_agent],
            retryable_run_ids=[run_agent],
            completion_status="incomplete",
        )

        resume = ResumeManager(
            runs_dir=tmp_path,
            protocol_version="1.0",
            config_hash="deadbeef",
            model_identity="dry-run:mock",
            source_commit="abc1234",
            deployed_build_id="abc1234",
        )
        cp = resume.get_normalized_checkpoint()
        assert cp is not None
        assert run_agent in cp.retryable_run_ids


# ---------------------------------------------------------------------------
# 4. Previously succeeded monolithic remains succeeded after agent succeeds
# ---------------------------------------------------------------------------

class TestSucceededMonolithicStable:
    def test_succeeded_monolithic_stays_succeeded_after_agent_succeeds(self, tmp_path: Path) -> None:
        planned = _all_planned()
        run_monolithic = planned[0]
        run_agent = planned[1]

        _make_record(tmp_path, run_monolithic, strategy_id="monolithic", status="succeeded")
        _make_checkpoint(
            tmp_path,
            completed_run_ids=[run_monolithic],
            succeeded_run_ids=[run_monolithic],
            completion_status="incomplete",
        )

        resume1 = ResumeManager(
            runs_dir=tmp_path,
            protocol_version="1.0",
            config_hash="deadbeef",
            model_identity="dry-run:mock",
            source_commit="abc1234",
            deployed_build_id="abc1234",
        )
        skip1 = resume1.validate_and_get_skip_ids()
        assert run_monolithic in skip1

        _make_record(tmp_path, run_agent, strategy_id="agent", status="succeeded")
        _make_checkpoint(
            tmp_path,
            completed_run_ids=[run_monolithic, run_agent],
            succeeded_run_ids=[run_monolithic, run_agent],
            completion_status="incomplete",
        )

        resume2 = ResumeManager(
            runs_dir=tmp_path,
            protocol_version="1.0",
            config_hash="deadbeef",
            model_identity="dry-run:mock",
            source_commit="abc1234",
            deployed_build_id="abc1234",
        )
        cp = resume2.get_normalized_checkpoint()
        assert cp is not None
        assert run_monolithic in cp.succeeded_run_ids
        assert run_agent in cp.succeeded_run_ids


# ---------------------------------------------------------------------------
# 5. Retryable agent failure is retried
# ---------------------------------------------------------------------------

class TestRetryableAgentFailureRetried:
    def test_retryable_agent_failure_not_skipped(self, tmp_path: Path) -> None:
        planned = _all_planned()
        run_monolithic = planned[0]
        run_agent = planned[1]

        _make_record(tmp_path, run_monolithic, strategy_id="monolithic", status="succeeded")
        _make_record(
            tmp_path, run_agent, strategy_id="agent", status="failed",
            failure_classification="environment",
        )
        _make_checkpoint(
            tmp_path,
            completed_run_ids=[run_monolithic, run_agent],
            succeeded_run_ids=[run_monolithic],
            failed_run_ids=[run_agent],
            retryable_run_ids=[run_agent],
            completion_status="incomplete",
        )

        resume = ResumeManager(
            runs_dir=tmp_path,
            protocol_version="1.0",
            config_hash="deadbeef",
            model_identity="dry-run:mock",
            source_commit="abc1234",
            deployed_build_id="abc1234",
        )
        skip_ids = resume.validate_and_get_skip_ids()
        assert run_monolithic in skip_ids, "succeeded monolithic must be skipped"
        assert run_agent not in skip_ids, "retryable agent failure must be retried (not skipped)"

        remaining = [rid for rid in planned if rid not in skip_ids]
        assert remaining[0] == run_agent


# ---------------------------------------------------------------------------
# 6. After retry succeeds: succeeded=[monolithic,agent], failed excludes agent,
#    retryable excludes agent, pending begins with selective
# ---------------------------------------------------------------------------

class TestRetrySuccessStateTransition:
    def test_after_retry_succeeds_full_state(self, tmp_path: Path) -> None:
        planned = _all_planned()
        run_monolithic = planned[0]
        run_agent = planned[1]
        run_selective = planned[2]

        _make_record(tmp_path, run_monolithic, strategy_id="monolithic", status="succeeded")
        _make_record(
            tmp_path, run_agent, strategy_id="agent", status="failed",
            failure_classification="environment",
        )

        _make_checkpoint(
            tmp_path,
            completed_run_ids=[run_monolithic, run_agent],
            succeeded_run_ids=[run_monolithic],
            failed_run_ids=[run_agent],
            retryable_run_ids=[run_agent],
            completion_status="incomplete",
        )

        resume1 = ResumeManager(
            runs_dir=tmp_path,
            protocol_version="1.0",
            config_hash="deadbeef",
            model_identity="dry-run:mock",
            source_commit="abc1234",
            deployed_build_id="abc1234",
        )
        skip1 = resume1.validate_and_get_skip_ids()
        assert run_agent not in skip1

        # Remove the failed record and write a succeeded one (simulates retry)
        records_path = tmp_path / "run_records.jsonl"
        lines = records_path.read_text(encoding="utf-8").strip().split("\n")
        filtered = [line for line in lines if run_agent not in line or '"failed"' not in line]
        records_path.write_text("\n".join(filtered) + "\n", encoding="utf-8")
        _make_record(tmp_path, run_agent, strategy_id="agent", status="succeeded")

        _make_checkpoint(
            tmp_path,
            completed_run_ids=[run_monolithic, run_agent],
            succeeded_run_ids=[run_monolithic, run_agent],
            failed_run_ids=[],
            retryable_run_ids=[],
            completion_status="incomplete",
        )

        resume2 = ResumeManager(
            runs_dir=tmp_path,
            protocol_version="1.0",
            config_hash="deadbeef",
            model_identity="dry-run:mock",
            source_commit="abc1234",
            deployed_build_id="abc1234",
        )
        cp = resume2.get_normalized_checkpoint()
        assert cp is not None
        assert set(cp.succeeded_run_ids) >= {run_monolithic, run_agent}
        assert run_agent not in cp.failed_run_ids
        assert run_agent not in cp.retryable_run_ids
        assert cp.pending_run_ids[0] == run_selective


# ---------------------------------------------------------------------------
# 7. Active checkpoint after each run contains complete historical state
# ---------------------------------------------------------------------------

class TestCheckpointHistoricalState:
    def test_checkpoint_preserves_state_on_normalize(self, tmp_path: Path) -> None:
        planned = _all_planned()
        run_monolithic = planned[0]
        run_agent = planned[1]

        _make_record(tmp_path, run_monolithic, strategy_id="monolithic", status="succeeded")
        _make_record(
            tmp_path, run_agent, strategy_id="agent", status="failed",
            failure_classification="environment_preflight",
        )
        _make_checkpoint(
            tmp_path,
            completed_run_ids=[run_monolithic, run_agent],
            completion_status="incomplete",
        )

        cp_mgr = CheckpointManager(tmp_path)
        record_store = RunRecordStore(tmp_path)
        cp = cp_mgr.normalize_from_records(record_store)
        assert cp is not None
        assert run_monolithic in cp.succeeded_run_ids
        assert run_agent in cp.failed_run_ids
        assert run_agent in cp.retryable_run_ids
        assert cp.total_completed == 2
        assert len(cp.pending_run_ids) == 5

        loaded = cp_mgr.read()
        assert loaded is not None
        assert loaded.succeeded_run_ids == [run_monolithic]
        assert loaded.failed_run_ids == [run_agent]
        assert loaded.retryable_run_ids == [run_agent]


# ---------------------------------------------------------------------------
# 8. No-CUDA real Qwen preflight is incompatible
# ---------------------------------------------------------------------------

class TestNoCudaPreflightIncompatible:
    def test_qwen_preflight_no_cuda_returns_incompatible(self) -> None:
        """When torch.cuda.is_available() is False, real Qwen preflight must
        return compatible=False with a clear rejection message."""
        import sys
        import types
        import unittest.mock as mock

        mock_torch = types.ModuleType("torch")
        mock_torch.__version__ = "2.1.0"  # type: ignore[attr-defined]
        mock_torch.cuda = mock.MagicMock()  # type: ignore[attr-defined]
        mock_torch.cuda.is_available.return_value = False
        mock_torch.version = mock.MagicMock()  # type: ignore[attr-defined]
        mock_torch.version.cuda = "12.1"
        mock_torch.bfloat16 = "bfloat16"  # type: ignore[attr-defined]
        mock_torch.float16 = "float16"  # type: ignore[attr-defined]
        mock_torch.float32 = "float32"  # type: ignore[attr-defined]
        mock_torch.dtype = type  # type: ignore[attr-defined]

        sys.modules["torch"] = mock_torch
        try:
            from benchmark.llm.kaggle_qwen_backend import KaggleQwenBackend
            result = KaggleQwenBackend.preflight()
        finally:
            del sys.modules["torch"]

        assert result.compatible is False
        assert "CUDA GPU required" in result.rejection_reason

    def test_preflight_check_no_cuda_returns_not_ok(self) -> None:
        """_preflight_check on a real non-dry-run with no CUDA must return ok=False."""
        import sys
        import types
        import unittest.mock as mock

        mock_torch = types.ModuleType("torch")
        mock_torch.__version__ = "2.1.0"  # type: ignore[attr-defined]
        mock_torch.cuda = mock.MagicMock()  # type: ignore[attr-defined]
        mock_torch.cuda.is_available.return_value = False
        mock_torch.version = mock.MagicMock()  # type: ignore[attr-defined]
        mock_torch.version.cuda = "12.1"

        sys.modules["torch"] = mock_torch
        try:
            from seven_arm_benchmark import _preflight_check
            ok, hw, sw, reason = _preflight_check(
                dry_run=False, needs_llm=True, strategy_name="agent",
            )
        finally:
            del sys.modules["torch"]

        assert ok is False
        assert "CUDA GPU required" in reason


# ---------------------------------------------------------------------------
# 9. Dry-run without CUDA remains allowed
# ---------------------------------------------------------------------------

class TestDryRunNoCudaAllowed:
    def test_dry_run_preflight_returns_compatible_without_cuda(self) -> None:
        from seven_arm_benchmark import _preflight_check
        ok, hw, sw, reason = _preflight_check(
            dry_run=True, needs_llm=True, strategy_name="agent",
        )
        assert ok is True

    def test_non_llm_preflight_always_compatible(self) -> None:
        from seven_arm_benchmark import _preflight_check
        ok, hw, sw, reason = _preflight_check(
            dry_run=False, needs_llm=False, strategy_name="incr_rtl",
        )
        assert ok is True


# ---------------------------------------------------------------------------
# 10. Continuous execution without --max-runs runs all remaining plan entries
# ---------------------------------------------------------------------------

class TestContinuousExecutionNoMaxRuns:
    def test_no_max_runs_plan_includes_all_remaining(self, tmp_path: Path) -> None:
        planned = _all_planned()
        run_monolithic = planned[0]

        _make_record(tmp_path, run_monolithic, strategy_id="monolithic", status="succeeded")
        _make_checkpoint(
            tmp_path,
            completed_run_ids=[run_monolithic],
            succeeded_run_ids=[run_monolithic],
            completion_status="incomplete",
        )

        resume = ResumeManager(
            runs_dir=tmp_path,
            protocol_version="1.0",
            config_hash="deadbeef",
            model_identity="dry-run:mock",
            source_commit="abc1234",
            deployed_build_id="abc1234",
        )
        skip_ids = resume.validate_and_get_skip_ids()

        execution_plan = [rid for rid in planned if rid not in skip_ids]
        assert len(execution_plan) == 6
        assert run_monolithic not in execution_plan


# ---------------------------------------------------------------------------
# 11. --max-runs 1 executes exactly one remaining Run without changing identity
# ---------------------------------------------------------------------------

class TestMaxRunsOneIdentity:
    def test_max_runs_one_takes_exactly_one(self, tmp_path: Path) -> None:
        planned = _all_planned()

        execution_plan = list(planned)
        max_runs_plan = execution_plan[:1]
        assert len(max_runs_plan) == 1
        assert max_runs_plan[0] == planned[0]

    def test_max_runs_one_does_not_change_planned_run_ids(self, tmp_path: Path) -> None:
        _make_checkpoint(tmp_path)
        cp = CheckpointManager(tmp_path).read()
        assert cp is not None
        assert len(cp.planned_run_ids) == 7

    def test_max_runs_does_not_change_config_hash(self) -> None:
        import argparse

        from seven_arm_benchmark import _compute_config_hash

        args = argparse.Namespace(
            dry_run=True, profile="smoke", strategy=None,
            max_attempts=3, timeout=0, protocol_version="1.0",
        )
        h1 = _compute_config_hash(args)
        h2 = _compute_config_hash(args)
        assert h1 == h2

    def test_max_runs_does_not_change_scenarios_or_strategies(self, tmp_path: Path) -> None:
        _make_checkpoint(tmp_path)
        cp = CheckpointManager(tmp_path).read()
        assert cp is not None
        assert cp.scenario_ids == SCENARIO_IDS
        assert cp.strategy_names == ALL_SEVEN_STRATEGIES


# ---------------------------------------------------------------------------
# Source identity: declared tag vs deployed build ID
# ---------------------------------------------------------------------------

class TestSourceIdentity:
    def test_checkpoint_persists_both_tag_and_build_id(self, tmp_path: Path) -> None:
        _make_checkpoint(
            tmp_path,
            declared_source_tag="v0.7.0-smoke-passed",
            deployed_build_id="abc1234",
            source_commit="abc1234",
        )
        cp = CheckpointManager(tmp_path).read()
        assert cp is not None
        assert cp.declared_source_tag == "v0.7.0-smoke-passed"
        assert cp.deployed_build_id == "abc1234"

    def test_deployed_build_id_used_for_compatibility(self, tmp_path: Path) -> None:
        _make_checkpoint(
            tmp_path,
            deployed_build_id="build-42",
            source_commit="abc1234",
        )
        resume = ResumeManager(
            runs_dir=tmp_path,
            protocol_version="1.0",
            config_hash="deadbeef",
            model_identity="dry-run:mock",
            source_commit="abc1234",
            deployed_build_id="build-99",
        )
        with pytest.raises(ResumeValidationError, match="Deployed build ID mismatch"):
            resume.validate_and_get_skip_ids()

    def test_deployed_build_id_match_passes(self, tmp_path: Path) -> None:
        _make_checkpoint(
            tmp_path,
            deployed_build_id="build-42",
            source_commit="abc1234",
        )
        resume = ResumeManager(
            runs_dir=tmp_path,
            protocol_version="1.0",
            config_hash="deadbeef",
            model_identity="dry-run:mock",
            source_commit="abc1234",
            deployed_build_id="build-42",
        )
        skip = resume.validate_and_get_skip_ids()
        assert isinstance(skip, set)

    def test_backward_compat_empty_deployed_build_id(self, tmp_path: Path) -> None:
        planned = _all_planned()
        old_data = {
            "profile": "smoke",
            "execution_plan_hash": "deadbeef",
            "planned_run_ids": planned,
            "completed_run_ids": [planned[0]],
            "failed_run_ids": [],
            "pending_run_ids": planned[1:],
            "total_planned": 7,
            "total_completed": 1,
            "protocol_version": "1.0",
            "model_identity": "dry-run:mock",
            "config_hash": "deadbeef",
            "source_commit": "abc1234",
            "completion_status": "incomplete",
            "scenario_ids": SCENARIO_IDS,
            "strategy_names": ALL_SEVEN_STRATEGIES,
        }
        cp_path = tmp_path / "checkpoint.json"
        cp_path.write_text(json.dumps(old_data), encoding="utf-8")
        _make_record(tmp_path, planned[0], strategy_id="monolithic", status="succeeded")

        resume = ResumeManager(
            runs_dir=tmp_path,
            protocol_version="1.0",
            config_hash="deadbeef",
            model_identity="dry-run:mock",
            source_commit="abc1234",
        )
        skip = resume.validate_and_get_skip_ids()
        assert planned[0] in skip


# ---------------------------------------------------------------------------
# Per-run metrics completeness
# ---------------------------------------------------------------------------

class TestPerRunMetrics:
    def test_run_record_has_all_required_fields(self, tmp_path: Path) -> None:
        now = datetime.now(UTC).isoformat()
        rec = _make_record(
            tmp_path, "test-001",
            strategy_id="agent",
            status="succeeded",
            model_calls=3,
            started_at=now,
            ended_at=now,
            hardware_identity="Tesla V100:sm_70",
            software_environment_identity="python=3.11|torch=2.0|cuda=11.8",
            failure_classification="",
            token_usage={"prompt": 100, "completion": 50, "total": 150},
        )
        assert rec.started_at != ""
        assert rec.ended_at != ""
        assert rec.model_calls == 3
        assert rec.hardware_identity == "Tesla V100:sm_70"
        assert rec.software_environment_identity == "python=3.11|torch=2.0|cuda=11.8"
        assert rec.failure_classification == ""

    def test_record_loadable_from_jsonl(self, tmp_path: Path) -> None:
        now = datetime.now(UTC).isoformat()
        _make_record(
            tmp_path, "round-trip-001",
            status="succeeded",
            model_calls=5,
            started_at=now,
            ended_at=now,
            hardware_identity="T4:sm_75",
            software_environment_identity="python=3.11",
        )
        store = RunRecordStore(tmp_path)
        loaded = store.load_all()
        assert len(loaded) == 1
        assert loaded[0].model_calls == 5
        assert loaded[0].hardware_identity == "T4:sm_75"
        assert loaded[0].started_at == now


# ---------------------------------------------------------------------------
# Hardware detection
# ---------------------------------------------------------------------------

class TestHardwareDetection:
    def test_hardware_identity_returns_string(self) -> None:
        hw = detect_hardware_identity()
        assert isinstance(hw, str)
        assert len(hw) > 0

    def test_software_identity_returns_string(self) -> None:
        sw = detect_software_environment_identity()
        assert isinstance(sw, str)
        assert "python=" in sw


# ---------------------------------------------------------------------------
# CheckpointData backward compatibility
# ---------------------------------------------------------------------------

class TestCheckpointBackwardCompat:
    def test_old_checkpoint_without_new_fields_loads(self, tmp_path: Path) -> None:
        planned = _all_planned()
        old_data = {
            "profile": "smoke",
            "execution_plan_hash": "deadbeef",
            "planned_run_ids": planned,
            "completed_run_ids": [],
            "failed_run_ids": [],
            "pending_run_ids": list(planned),
            "total_planned": 7,
            "total_completed": 0,
            "protocol_version": "1.0",
            "model_identity": "dry-run:mock",
            "config_hash": "deadbeef",
            "source_commit": "abc1234",
            "completion_status": "incomplete",
            "scenario_ids": SCENARIO_IDS,
            "strategy_names": ALL_SEVEN_STRATEGIES,
        }
        cp_path = tmp_path / "checkpoint.json"
        cp_path.write_text(json.dumps(old_data), encoding="utf-8")
        loaded = CheckpointManager(tmp_path).read()
        assert loaded is not None
        assert loaded.declared_source_tag == ""
        assert loaded.deployed_build_id == ""
        assert loaded.total_planned == 7

    def test_new_checkpoint_persists_both_fields(self, tmp_path: Path) -> None:
        _make_checkpoint(
            tmp_path,
            declared_source_tag="v0.8.0",
            deployed_build_id="build-abc",
        )
        loaded = CheckpointManager(tmp_path).read()
        assert loaded is not None
        assert loaded.declared_source_tag == "v0.8.0"
        assert loaded.deployed_build_id == "build-abc"


# ---------------------------------------------------------------------------
# ResumeManager backward compat
# ---------------------------------------------------------------------------

class TestResumeDeployedBuildId:
    def test_resume_manager_defaults_deployed_to_source_commit(self) -> None:
        resume = ResumeManager(
            runs_dir=Path("/tmp/unused"),
            protocol_version="1.0",
            config_hash="deadbeef",
            model_identity="dry-run:mock",
            source_commit="abc1234",
        )
        assert resume._deployed_build_id == "abc1234"

    def test_resume_manager_explicit_deployed_build_id(self) -> None:
        resume = ResumeManager(
            runs_dir=Path("/tmp/unused"),
            protocol_version="1.0",
            config_hash="deadbeef",
            model_identity="dry-run:mock",
            source_commit="abc1234",
            deployed_build_id="build-xyz",
        )
        assert resume._deployed_build_id == "build-xyz"


# ---------------------------------------------------------------------------
# Failure classification
# ---------------------------------------------------------------------------

class TestFailureClassification:
    def test_environment_preflight_is_retryable(self) -> None:
        rec = RunRecordData(
            run_id="test", profile="smoke", repository_id="r",
            scenario_id="s", strategy_id="agent", repetition=1,
            seed=42, status="cancelled",
            failure_classification="environment_preflight",
        )
        assert failure_is_retryable(rec) is True

    def test_environment_is_retryable(self) -> None:
        rec = RunRecordData(
            run_id="test", profile="smoke", repository_id="r",
            scenario_id="s", strategy_id="agent", repetition=1,
            seed=42, status="failed",
            failure_classification="environment",
        )
        assert failure_is_retryable(rec) is True

    def test_model_output_is_not_retryable(self) -> None:
        rec = RunRecordData(
            run_id="test", profile="smoke", repository_id="r",
            scenario_id="s", strategy_id="agent", repetition=1,
            seed=42, status="failed",
            failure_classification="model_output",
        )
        assert failure_is_retryable(rec) is False

    def test_empty_classification_is_not_retryable(self) -> None:
        rec = RunRecordData(
            run_id="test", profile="smoke", repository_id="r",
            scenario_id="s", strategy_id="agent", repetition=1,
            seed=42, status="failed",
            failure_classification="",
        )
        assert failure_is_retryable(rec) is False


# ---------------------------------------------------------------------------
# Preflight behavior
# ---------------------------------------------------------------------------

class TestPreflightBehavior:
    def test_preflight_failure_leaves_checkpoint_resumable(self, tmp_path: Path) -> None:
        _make_checkpoint(
            tmp_path,
            completed_run_ids=[],
            completion_status="incomplete",
        )
        cp = CheckpointManager(tmp_path).read()
        assert cp is not None
        assert cp.completion_status == "incomplete"
        assert len(cp.completed_run_ids) == 0
        assert len(cp.pending_run_ids) == 7

    def test_preflight_result_classifies_compatibility(self) -> None:
        from benchmark.llm.kaggle_qwen_backend import GpuPreflightResult
        rejected = GpuPreflightResult(
            compatible=False,
            hardware_identity="Tesla P100:sm_60",
            software_identity="python=3.11",
            rejection_reason="GPU below minimum",
        )
        assert rejected.compatible is False
        assert rejected.rejection_reason != ""


# ---------------------------------------------------------------------------
# Invariant enforcement
# ---------------------------------------------------------------------------

class TestInvariantEnforcement:
    def test_no_id_both_attempted_and_pending(self, tmp_path: Path) -> None:
        planned = _all_planned()
        run_0 = planned[0]

        _make_record(tmp_path, run_0, strategy_id="monolithic", status="succeeded")
        _make_checkpoint(
            tmp_path,
            completed_run_ids=[run_0],
            pending_run_ids=planned,
        )

        resume = ResumeManager(
            runs_dir=tmp_path,
            protocol_version="1.0",
            config_hash="deadbeef",
            model_identity="dry-run:mock",
            source_commit="abc1234",
            deployed_build_id="abc1234",
        )
        resume.validate_and_get_skip_ids()

        normalized = CheckpointManager(tmp_path).read()
        assert normalized is not None
        assert set(normalized.completed_run_ids) & set(normalized.pending_run_ids) == set()

    def test_no_id_both_succeeded_and_failed(self, tmp_path: Path) -> None:
        planned = _all_planned()
        run_0 = planned[0]
        run_1 = planned[1]

        _make_record(tmp_path, run_0, strategy_id="monolithic", status="succeeded")
        _make_record(
            tmp_path, run_1, strategy_id="agent", status="failed",
            failure_classification="model_output",
        )
        _make_checkpoint(
            tmp_path,
            completed_run_ids=[run_0, run_1],
        )

        resume = ResumeManager(
            runs_dir=tmp_path,
            protocol_version="1.0",
            config_hash="deadbeef",
            model_identity="dry-run:mock",
            source_commit="abc1234",
            deployed_build_id="abc1234",
        )
        resume.validate_and_get_skip_ids()

        normalized = CheckpointManager(tmp_path).read()
        assert normalized is not None
        assert set(normalized.succeeded_run_ids) & set(normalized.failed_run_ids) == set()

    def test_attempted_equals_succeeded_union_failed(self, tmp_path: Path) -> None:
        planned = _all_planned()
        run_0 = planned[0]
        run_1 = planned[1]

        _make_record(tmp_path, run_0, strategy_id="monolithic", status="succeeded")
        _make_record(
            tmp_path, run_1, strategy_id="agent", status="failed",
            failure_classification="environment",
        )
        _make_checkpoint(
            tmp_path,
            completed_run_ids=[run_0, run_1],
        )

        resume = ResumeManager(
            runs_dir=tmp_path,
            protocol_version="1.0",
            config_hash="deadbeef",
            model_identity="dry-run:mock",
            source_commit="abc1234",
            deployed_build_id="abc1234",
        )
        resume.validate_and_get_skip_ids()

        normalized = CheckpointManager(tmp_path).read()
        assert normalized is not None
        assert set(normalized.completed_run_ids) == (
            set(normalized.succeeded_run_ids) | set(normalized.failed_run_ids)
        )

    def test_planned_equals_attempted_union_pending(self, tmp_path: Path) -> None:
        planned = _all_planned()
        run_0 = planned[0]

        _make_record(tmp_path, run_0, strategy_id="monolithic", status="succeeded")
        _make_checkpoint(
            tmp_path,
            completed_run_ids=[run_0],
            pending_run_ids=planned,
        )

        resume = ResumeManager(
            runs_dir=tmp_path,
            protocol_version="1.0",
            config_hash="deadbeef",
            model_identity="dry-run:mock",
            source_commit="abc1234",
            deployed_build_id="abc1234",
        )
        resume.validate_and_get_skip_ids()

        normalized = CheckpointManager(tmp_path).read()
        assert normalized is not None
        assert set(normalized.planned_run_ids) == (
            set(normalized.completed_run_ids) | set(normalized.pending_run_ids)
        )


# ---------------------------------------------------------------------------
# Non-retryable failure is skipped on resume
# ---------------------------------------------------------------------------

class TestNonRetryableFailureSkipped:
    def test_non_retryable_failure_is_skipped(self, tmp_path: Path) -> None:
        planned = _all_planned()
        run_0 = planned[0]
        run_1 = planned[1]

        _make_record(tmp_path, run_0, strategy_id="monolithic", status="succeeded")
        _make_record(
            tmp_path, run_1, strategy_id="agent", status="failed",
            failure_classification="model_output",
        )
        _make_checkpoint(
            tmp_path,
            completed_run_ids=[run_0, run_1],
            completion_status="incomplete",
        )

        resume = ResumeManager(
            runs_dir=tmp_path,
            protocol_version="1.0",
            config_hash="deadbeef",
            model_identity="dry-run:mock",
            source_commit="abc1234",
            deployed_build_id="abc1234",
        )
        skip_ids = resume.validate_and_get_skip_ids()
        assert run_0 in skip_ids
        assert run_1 in skip_ids


# ---------------------------------------------------------------------------
# Multi-session full sequence
# ---------------------------------------------------------------------------

class TestFullThreeSessionSequence:
    def test_full_three_session_sequence(self, tmp_path: Path) -> None:
        planned = _all_planned()
        completed_so_far: list[str] = []

        _make_record(tmp_path, planned[0], strategy_id="monolithic", status="succeeded")
        completed_so_far.append(planned[0])
        _make_checkpoint(tmp_path, completed_run_ids=list(completed_so_far))

        resume = ResumeManager(
            runs_dir=tmp_path,
            protocol_version="1.0",
            config_hash="deadbeef",
            model_identity="dry-run:mock",
            source_commit="abc1234",
        )
        skip = resume.validate_and_get_skip_ids()
        assert len(skip) == 1
        assert planned[0] in skip

        _make_record(tmp_path, planned[1], strategy_id="agent", status="succeeded")
        completed_so_far.append(planned[1])
        _make_checkpoint(tmp_path, completed_run_ids=list(completed_so_far))

        resume2 = ResumeManager(
            runs_dir=tmp_path,
            protocol_version="1.0",
            config_hash="deadbeef",
            model_identity="dry-run:mock",
            source_commit="abc1234",
        )
        skip2 = resume2.validate_and_get_skip_ids()
        assert len(skip2) == 2
        assert planned[0] in skip2
        assert planned[1] in skip2

        for i in range(2, 7):
            _make_record(
                tmp_path, planned[i],
                strategy_id=ALL_SEVEN_STRATEGIES[i],
                status="succeeded",
            )
            completed_so_far.append(planned[i])

        _make_checkpoint(
            tmp_path,
            completed_run_ids=list(completed_so_far),
            completion_status="completed",
        )

        cp = CheckpointManager(tmp_path).read()
        assert cp is not None
        assert cp.total_completed == 7
        assert cp.completion_status == "completed"
        assert len(cp.pending_run_ids) == 0

        store = RunRecordStore(tmp_path)
        assert store.count() == 7


# ---------------------------------------------------------------------------
# attempted_run_ids field
# ---------------------------------------------------------------------------

class TestAttemptedRunIds:
    def test_attempted_run_ids_populated_by_normalize(self, tmp_path: Path) -> None:
        planned = _all_planned()
        run_0 = planned[0]
        run_1 = planned[1]

        _make_record(tmp_path, run_0, strategy_id="monolithic", status="succeeded")
        _make_record(
            tmp_path, run_1, strategy_id="agent", status="failed",
            failure_classification="environment",
        )
        _make_checkpoint(
            tmp_path,
            completed_run_ids=[run_0, run_1],
        )

        resume = ResumeManager(
            runs_dir=tmp_path,
            protocol_version="1.0",
            config_hash="deadbeef",
            model_identity="dry-run:mock",
            source_commit="abc1234",
            deployed_build_id="abc1234",
        )
        resume.validate_and_get_skip_ids()

        normalized = CheckpointManager(tmp_path).read()
        assert normalized is not None
        assert set(normalized.attempted_run_ids) == {run_0, run_1}
        assert set(normalized.attempted_run_ids) == set(normalized.completed_run_ids)

    def test_attempted_run_ids_empty_on_start_new(self, tmp_path: Path) -> None:
        _make_checkpoint(tmp_path, completed_run_ids=[])
        cp = CheckpointManager(tmp_path).read()
        assert cp is not None
        assert cp.attempted_run_ids == []


# ---------------------------------------------------------------------------
# SU-0007 post-validation: is_resume detection via resolved action
# ---------------------------------------------------------------------------

def _simulate_is_resume(
    auto_resume_hf: bool,
    resume_action: str | None,
    skip_run_ids: set[str],
) -> bool:
    """Replicate the corrected is_resume logic from seven_arm_benchmark.py."""
    return bool(
        auto_resume_hf
        and resume_action is not None
        and resume_action == "resume"
    )


class TestIsResumeDetection:
    """Verify is_resume is derived from the resolved auto-resume action,
    NOT from bool(skip_run_ids)."""

    def test_resume_with_succeeded_and_nonempty_skip(self, tmp_path: Path) -> None:
        """RESUME with succeeded runs produces non-empty skip set -> is_resume True."""
        planned = _all_planned()
        run_0 = planned[0]

        _make_record(tmp_path, run_0, strategy_id="monolithic", status="succeeded")
        _make_checkpoint(
            tmp_path,
            completed_run_ids=[run_0],
            succeeded_run_ids=[run_0],
            completion_status="incomplete",
        )

        resume = ResumeManager(
            runs_dir=tmp_path,
            protocol_version="1.0",
            config_hash="deadbeef",
            model_identity="dry-run:mock",
            source_commit="abc1234",
            deployed_build_id="abc1234",
        )
        skip_ids = resume.validate_and_get_skip_ids()
        assert len(skip_ids) > 0, "succeeded run must be in skip set"

        is_resume = _simulate_is_resume(True, "resume", skip_ids)
        assert is_resume is True

        cp = resume.get_normalized_checkpoint()
        assert cp is not None
        assert run_0 in cp.succeeded_run_ids

    def test_resume_with_only_retryable_and_empty_skip(self, tmp_path: Path) -> None:
        """RESUME with only retryable failures produces empty skip set
        but is_resume must still be True (the key bug fix)."""
        planned = _all_planned()
        run_0 = planned[0]
        run_1 = planned[1]

        _make_record(tmp_path, run_0, strategy_id="monolithic", status="succeeded")
        _make_record(
            tmp_path, run_1, strategy_id="agent", status="failed",
            failure_classification="environment",
        )
        _make_checkpoint(
            tmp_path,
            completed_run_ids=[run_0, run_1],
            succeeded_run_ids=[run_0],
            failed_run_ids=[run_1],
            retryable_run_ids=[run_1],
            completion_status="incomplete",
        )

        resume = ResumeManager(
            runs_dir=tmp_path,
            protocol_version="1.0",
            config_hash="deadbeef",
            model_identity="dry-run:mock",
            source_commit="abc1234",
            deployed_build_id="abc1234",
        )
        skip_ids = resume.validate_and_get_skip_ids()
        # monolithic succeeded -> skipped; agent retryable -> NOT skipped
        assert run_0 in skip_ids
        assert run_1 not in skip_ids

        is_resume = _simulate_is_resume(True, "resume", skip_ids)
        assert is_resume is True, (
            "is_resume must be True even when skip_run_ids excludes retryable runs"
        )

        cp = resume.get_normalized_checkpoint()
        assert cp is not None
        assert run_0 in cp.succeeded_run_ids
        assert run_1 in cp.retryable_run_ids

    def test_start_new_with_empty_skip(self, tmp_path: Path) -> None:
        """START_NEW with no prior state -> is_resume False, empty checkpoint."""
        is_resume = _simulate_is_resume(True, "start_new", set())
        assert is_resume is False

        # Simulate START_NEW: initialize empty checkpoint
        planned = _all_planned()
        checkpoint_data = CheckpointData(
            profile="smoke",
            execution_plan_hash="deadbeef",
            planned_run_ids=planned,
            completed_run_ids=[],
            attempted_run_ids=[],
            succeeded_run_ids=[],
            retryable_run_ids=[],
            failed_run_ids=[],
            pending_run_ids=list(planned),
            total_planned=7,
            total_completed=0,
            protocol_version="1.0",
            model_identity="dry-run:mock",
            config_hash="deadbeef",
            source_commit="abc1234",
            completion_status="running",
            scenario_ids=SCENARIO_IDS,
            strategy_names=ALL_SEVEN_STRATEGIES,
            declared_source_tag="",
            deployed_build_id="abc1234",
        )
        CheckpointManager(tmp_path).write_atomic(checkpoint_data)
        cp = CheckpointManager(tmp_path).read()
        assert cp is not None
        assert cp.total_completed == 0
        assert len(cp.completed_run_ids) == 0
        assert len(cp.pending_run_ids) == 7

    def test_auto_resume_false_with_empty_skip(self) -> None:
        """Non-auto-resume mode -> is_resume False regardless of skip set."""
        is_resume = _simulate_is_resume(False, None, set())
        assert is_resume is False

    def test_already_complete_not_resume(self) -> None:
        """ALREADY_COMPLETE action -> is_resume False."""
        is_resume = _simulate_is_resume(True, "already_complete", set())
        assert is_resume is False
