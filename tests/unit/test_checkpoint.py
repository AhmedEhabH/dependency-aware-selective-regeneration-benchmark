from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from benchmark.checkpoint.checkpoint import CheckpointData, CheckpointManager, ProgressData, ProgressManager
from benchmark.checkpoint.package import ResultsPackager
from benchmark.checkpoint.persistence import RunRecordData, RunRecordStore
from benchmark.checkpoint.resume import ResumeManager, ResumeValidationError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_record_data(run_id: str = "test-run-001", status: str = "succeeded") -> RunRecordData:
    return RunRecordData(
        run_id=run_id,
        profile="test",
        repository_id="todo",
        scenario_id="todo-add-feature-toggle",
        strategy_id="agent",
        repetition=1,
        seed=42,
        status=status,
        duration_seconds=1.0,
        protocol_version="1.0",
        source_commit="abc1234",
        config_hash="deadbeef",
        timestamp="2026-07-24T00:00:00",
    )


def _make_checkpoint_data(**overrides: str | list[str] | int) -> CheckpointData:
    data = CheckpointData(
        profile="test",
        execution_plan_hash="abc123",
        planned_run_ids=["run-1", "run-2", "run-3"],
        completed_run_ids=["run-1"],
        failed_run_ids=[],
        pending_run_ids=["run-2", "run-3"],
        total_planned=3,
        total_completed=1,
        protocol_version="1.0",
        model_identity="dry-run:mock",
        config_hash="deadbeef",
        source_commit="abc1234",
        scenario_ids=["test-scenario"],
        strategy_names=["agent"],
    )
    for k, v in overrides.items():
        setattr(data, k, v)
    return data


# ---------------------------------------------------------------------------
# Tests: RunRecordStore
# ---------------------------------------------------------------------------

class TestRunRecordStore:
    def test_append_and_load(self, tmp_path: Path) -> None:
        store = RunRecordStore(tmp_path)
        store.append(_make_record_data("r1"))
        store.append(_make_record_data("r2"))
        records = store.load_all()
        assert len(records) == 2
        assert records[0].run_id == "r1"
        assert records[1].run_id == "r2"

    def test_get_completed_run_ids(self, tmp_path: Path) -> None:
        store = RunRecordStore(tmp_path)
        store.append(_make_record_data("r1", status="succeeded"))
        store.append(_make_record_data("r2", status="failed"))
        store.append(_make_record_data("r3", status="running"))
        completed = store.get_completed_run_ids()
        assert completed == {"r1", "r2"}
        assert "r3" not in completed

    def test_load_from_existing_file(self, tmp_path: Path) -> None:
        store = RunRecordStore(tmp_path)
        store.append(_make_record_data("r1"))
        store2 = RunRecordStore(tmp_path)
        records = store2.load_all()
        assert len(records) == 1
        assert records[0].run_id == "r1"

    def test_empty_store(self, tmp_path: Path) -> None:
        store = RunRecordStore(tmp_path)
        records = store.load_all()
        assert records == []
        assert store.count() == 0

    def test_flush_after_each_record(self, tmp_path: Path) -> None:
        store = RunRecordStore(tmp_path)
        store.append(_make_record_data("r1"))
        content = store.path.read_text(encoding="utf-8")
        assert content.strip() != ""
        assert "\n" not in content.strip()  # exactly one line

    def test_corrupted_record_raises(self, tmp_path: Path) -> None:
        store = RunRecordStore(tmp_path)
        store.path.write_text("not-json\n", encoding="utf-8")
        with pytest.raises(ValueError, match="Corrupted"):
            store.load_all()

    def test_count(self, tmp_path: Path) -> None:
        store = RunRecordStore(tmp_path)
        assert store.count() == 0
        store.append(_make_record_data("r1"))
        store.append(_make_record_data("r2"))
        assert store.count() == 2


# ---------------------------------------------------------------------------
# Tests: CheckpointManager (atomic checkpoint)
# ---------------------------------------------------------------------------

class TestCheckpointManager:
    def test_write_and_read(self, tmp_path: Path) -> None:
        mgr = CheckpointManager(tmp_path)
        data = _make_checkpoint_data()
        mgr.write_atomic(data)
        assert mgr.path.is_file()
        loaded = mgr.read()
        assert loaded is not None
        assert loaded.profile == "test"
        assert loaded.total_planned == 3
        assert loaded.total_completed == 1

    def test_atomic_replacement(self, tmp_path: Path) -> None:
        mgr = CheckpointManager(tmp_path)
        mgr.write_atomic(_make_checkpoint_data(total_completed=1))
        mgr.write_atomic(_make_checkpoint_data(total_completed=2))
        loaded = mgr.read()
        assert loaded is not None
        assert loaded.total_completed == 2

    def test_no_tmp_file_left_behind(self, tmp_path: Path) -> None:
        mgr = CheckpointManager(tmp_path)
        mgr.write_atomic(_make_checkpoint_data())
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert len(tmp_files) == 0

    def test_read_nonexistent(self, tmp_path: Path) -> None:
        mgr = CheckpointManager(tmp_path)
        assert mgr.read() is None
        assert not mgr.exists()

    def test_corrupted_checkpoint_raises(self, tmp_path: Path) -> None:
        mgr = CheckpointManager(tmp_path)
        mgr.path.write_text("{invalid json", encoding="utf-8")
        with pytest.raises(ValueError, match="Corrupted"):
            mgr.read()

    def test_protocol_and_config_fields(self, tmp_path: Path) -> None:
        mgr = CheckpointManager(tmp_path)
        data = _make_checkpoint_data(
            protocol_version="1.0",
            config_hash="cfg_hash",
            source_commit="abc123",
        )
        mgr.write_atomic(data)
        loaded = mgr.read()
        assert loaded is not None
        assert loaded.protocol_version == "1.0"
        assert loaded.config_hash == "cfg_hash"
        assert loaded.source_commit == "abc123"

    def test_completion_status_transition(self, tmp_path: Path) -> None:
        mgr = CheckpointManager(tmp_path)
        data = _make_checkpoint_data(completion_status="incomplete")
        mgr.write_atomic(data)
        loaded = mgr.read()
        assert loaded is not None
        assert loaded.completion_status == "incomplete"
        data.completion_status = "completed"
        mgr.write_atomic(data)
        loaded = mgr.read()
        assert loaded is not None
        assert loaded.completion_status == "completed"


# ---------------------------------------------------------------------------
# Tests: ProgressManager
# ---------------------------------------------------------------------------

class TestProgressManager:
    def test_write_and_read(self, tmp_path: Path) -> None:
        mgr = ProgressManager(tmp_path)
        p = ProgressData(profile="test", total_planned=10, total_completed=5)
        mgr.write(p)
        assert mgr.path.is_file()
        loaded = mgr.read_progress()
        assert loaded is not None
        assert loaded.total_completed == 5

    def test_partial_summary(self, tmp_path: Path) -> None:
        mgr = ProgressManager(tmp_path)
        mgr.write_partial_summary({"agent": {"success": 1}})
        partial = tmp_path / "benchmark_summary.partial.json"
        assert partial.is_file()
        data = json.loads(partial.read_text())
        assert data["agent"]["success"] == 1

    def test_final_summary_created(self, tmp_path: Path) -> None:
        mgr = ProgressManager(tmp_path)
        mgr.write_final_summary({"agent": {"success": 2}})
        final = tmp_path / "benchmark_summary.json"
        assert final.is_file()

    def test_completed_marker(self, tmp_path: Path) -> None:
        mgr = ProgressManager(tmp_path)
        assert not mgr.is_completed()
        mgr.mark_completed()
        assert mgr.is_completed()
        marker = tmp_path / "COMPLETED"
        assert marker.is_file()
        data = json.loads(marker.read_text())
        assert data["status"] == "completed"

    def test_progress_elapsed_and_ratio(self, tmp_path: Path) -> None:
        mgr = ProgressManager(tmp_path)
        p = ProgressData(profile="test", total_planned=100, total_completed=25, completion_ratio=0.25)
        mgr.write(p)
        loaded = mgr.read_progress()
        assert loaded is not None
        assert loaded.completion_ratio == 0.25


# ---------------------------------------------------------------------------
# Tests: ResumeManager
# ---------------------------------------------------------------------------

class TestResumeManager:
    def test_resume_skip_completed_ids(self, tmp_path: Path) -> None:
        store = RunRecordStore(tmp_path)
        store.append(_make_record_data("run-1", status="succeeded"))
        store.append(_make_record_data("run-2", status="failed"))
        mgr = CheckpointManager(tmp_path)
        mgr.write_atomic(_make_checkpoint_data(
            planned_run_ids=["run-1", "run-2", "run-3"],
            completed_run_ids=["run-1", "run-2"],
            protocol_version="1.0",
            config_hash="deadbeef",
            source_commit="abc1234",
        ))
        resume = ResumeManager(
            runs_dir=tmp_path,
            protocol_version="1.0",
            config_hash="deadbeef",
            model_identity="dry-run:mock",
            source_commit="abc1234",
        )
        skip_ids = resume.validate_and_get_skip_ids()
        assert "run-1" in skip_ids
        assert "run-2" in skip_ids

    def test_protocol_mismatch_rejected(self, tmp_path: Path) -> None:
        mgr = CheckpointManager(tmp_path)
        mgr.write_atomic(_make_checkpoint_data(protocol_version="0.9"))
        resume = ResumeManager(
            runs_dir=tmp_path,
            protocol_version="1.0",
            config_hash="deadbeef",
            model_identity="dry-run:mock",
            source_commit="abc1234",
        )
        with pytest.raises(ResumeValidationError, match="Protocol version mismatch"):
            resume.validate_and_get_skip_ids()

    def test_config_hash_mismatch_rejected(self, tmp_path: Path) -> None:
        mgr = CheckpointManager(tmp_path)
        mgr.write_atomic(_make_checkpoint_data(config_hash="old_hash"))
        resume = ResumeManager(
            runs_dir=tmp_path,
            protocol_version="1.0",
            config_hash="new_hash",
            model_identity="dry-run:mock",
            source_commit="abc1234",
        )
        with pytest.raises(ResumeValidationError, match="Config hash mismatch"):
            resume.validate_and_get_skip_ids()

    def test_model_identity_mismatch_rejected(self, tmp_path: Path) -> None:
        mgr = CheckpointManager(tmp_path)
        mgr.write_atomic(_make_checkpoint_data(model_identity="qwen:old"))
        resume = ResumeManager(
            runs_dir=tmp_path,
            protocol_version="1.0",
            config_hash="deadbeef",
            model_identity="qwen:new",
            source_commit="abc1234",
        )
        with pytest.raises(ResumeValidationError, match="Model identity mismatch"):
            resume.validate_and_get_skip_ids()

    def test_source_commit_mismatch_rejected(self, tmp_path: Path) -> None:
        mgr = CheckpointManager(tmp_path)
        mgr.write_atomic(_make_checkpoint_data(source_commit="old_commit"))
        resume = ResumeManager(
            runs_dir=tmp_path,
            protocol_version="1.0",
            config_hash="deadbeef",
            model_identity="dry-run:mock",
            source_commit="new_commit",
        )
        with pytest.raises(ResumeValidationError, match="Source commit mismatch"):
            resume.validate_and_get_skip_ids()

    def test_resume_from_copies_files(self, tmp_path: Path) -> None:
        src = tmp_path / "previous"
        src.mkdir()
        src_checkpoint = src / "checkpoint.json"
        src_checkpoint.write_text(json.dumps({
            "profile": "test",
            "execution_plan_hash": "abc",
            "planned_run_ids": ["r1"],
            "completed_run_ids": [],
            "failed_run_ids": [],
            "pending_run_ids": ["r1"],
            "total_planned": 1,
            "total_completed": 0,
            "protocol_version": "1.0",
            "model_identity": "",
            "config_hash": "",
            "source_commit": "",
            "last_update": "",
            "completion_status": "incomplete",
        }))

        dst = tmp_path / "current"
        dst.mkdir()
        resume = ResumeManager(
            runs_dir=dst,
            protocol_version="1.0",
            config_hash="",
            model_identity="",
            source_commit="",
        )
        resume.resume_from(src)
        assert (dst / "checkpoint.json").is_file()

    def test_resume_from_missing_dir_raises(self, tmp_path: Path) -> None:
        resume = ResumeManager(
            runs_dir=tmp_path,
            protocol_version="1.0",
            config_hash="",
            model_identity="",
            source_commit="",
        )
        with pytest.raises(ResumeValidationError, match="not found"):
            resume.resume_from(tmp_path / "nonexistent")

    def test_resume_from_no_checkpoint_raises(self, tmp_path: Path) -> None:
        src = tmp_path / "previous"
        src.mkdir()
        resume = ResumeManager(
            runs_dir=tmp_path,
            protocol_version="1.0",
            config_hash="",
            model_identity="",
            source_commit="",
        )
        with pytest.raises(ResumeValidationError, match="No checkpoint"):
            resume.resume_from(src)

    def test_resume_idempotent(self, tmp_path: Path) -> None:
        store = RunRecordStore(tmp_path)
        store.append(_make_record_data("r1", status="succeeded"))
        mgr = CheckpointManager(tmp_path)
        mgr.write_atomic(_make_checkpoint_data(
            planned_run_ids=["r1", "r2"],
            completed_run_ids=["r1"],
            protocol_version="1.0",
            config_hash="deadbeef",
            source_commit="abc1234",
        ))
        resume = ResumeManager(
            runs_dir=tmp_path,
            protocol_version="1.0",
            config_hash="deadbeef",
            model_identity="dry-run:mock",
            source_commit="abc1234",
        )
        skip1 = resume.validate_and_get_skip_ids()
        skip2 = resume.validate_and_get_skip_ids()
        assert skip1 == skip2

    def test_failed_runs_retained(self, tmp_path: Path) -> None:
        store = RunRecordStore(tmp_path)
        store.append(_make_record_data("failed-1", status="failed"))
        store.append(_make_record_data("failed-2", status="failed"))
        completed = store.get_completed_run_ids()
        assert "failed-1" in completed
        assert "failed-2" in completed


# ---------------------------------------------------------------------------
# Tests: ResultsPackager
# ---------------------------------------------------------------------------

class TestResultsPackager:
    def test_create_zip(self, tmp_path: Path) -> None:
        store = RunRecordStore(tmp_path)
        store.append(_make_record_data("r1"))
        mgr = CheckpointManager(tmp_path)
        mgr.write_atomic(_make_checkpoint_data())
        pkg = ResultsPackager(tmp_path)
        zip_path = tmp_path / "results.zip"
        pkg.create_zip(zip_path)
        assert zip_path.is_file()
        assert zip_path.stat().st_size > 0

    def test_zip_contains_manifest(self, tmp_path: Path) -> None:
        store = RunRecordStore(tmp_path)
        store.append(_make_record_data("r1"))
        mgr = CheckpointManager(tmp_path)
        mgr.write_atomic(_make_checkpoint_data())
        pkg = ResultsPackager(tmp_path)
        zip_path = tmp_path / "results.zip"
        pkg.create_zip(zip_path)
        import zipfile
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            assert "manifest.json" in names
            assert "run_records.jsonl" in names or "run_records.jsonl" in names

    def test_zip_includes_env_metadata(self, tmp_path: Path) -> None:
        store = RunRecordStore(tmp_path)
        store.append(_make_record_data("r1"))
        pkg = ResultsPackager(tmp_path)
        zip_path = tmp_path / "results.zip"
        pkg.create_zip(zip_path)
        import zipfile
        with zipfile.ZipFile(zip_path, "r") as zf:
            assert "environment_metadata.json" in zf.namelist()


# ---------------------------------------------------------------------------
# Tests: SU-0010B2 End-to-End Metrics Persistence
# ---------------------------------------------------------------------------

def _make_e2e_record_data(**overrides: Any) -> RunRecordData:
    """Create RunRecordData with all end-to-end fields populated."""
    kwargs: dict[str, Any] = {
        "run_id": "e2e-test-001",
        "profile": "test",
        "repository_id": "test-repo",
        "scenario_id": "test-scenario-001",
        "strategy_id": "selective",
        "repetition": 1,
        "seed": 42,
        "status": "succeeded",
        "token_usage": {"prompt": 100, "completion": 50, "total": 150},
        "duration_seconds": 12.5,
        "protocol_version": "1.0",
        "source_commit": "abc123",
        "config_hash": "deadbeef",
        "timestamp": "2026-07-26T00:00:00",
        "model_calls": 2,
        "selection_prompt_tokens": 11,
        "selection_completion_tokens": 12,
        "selection_total_tokens": 23,
        "selection_model_calls": 1,
        "selection_duration_seconds": 3.25,
        "regeneration_prompt_tokens": 31,
        "regeneration_completion_tokens": 32,
        "regeneration_total_tokens": 63,
        "regeneration_model_calls": 3,
        "regeneration_duration_seconds": 2.0,
        "functional_validation_duration_seconds": 4.5,
        "functional_validation_passed": False,
        "total_workflow_tokens": 86,
        "total_workflow_model_calls": 4,
        "total_workflow_duration_seconds": 9.75,
        "selected_artifact_count": 5,
        "regenerated_artifact_count": 3,
        "preserved_artifact_count": 1,
        "unresolved_human_review_count": 1,
    }
    kwargs.update(overrides)
    return RunRecordData(**kwargs)


class TestEndToEndMetricsRoundTrip:
    """Verify that all RunRecordData end-to-end fields survive serialization."""

    def test_round_trip_all_fields(self, tmp_path: Path) -> None:
        """All end-to-end fields survive JSONL write+read cycle."""
        store = RunRecordStore(tmp_path)
        rec = _make_e2e_record_data()
        store.append(rec)

        loaded = store.load_all()
        assert len(loaded) == 1
        loaded_rec = loaded[0]

        assert loaded_rec.selection_prompt_tokens == 11
        assert loaded_rec.selection_completion_tokens == 12
        assert loaded_rec.selection_total_tokens == 23
        assert loaded_rec.selection_model_calls == 1
        assert loaded_rec.selection_duration_seconds == 3.25
        assert loaded_rec.regeneration_prompt_tokens == 31
        assert loaded_rec.regeneration_completion_tokens == 32
        assert loaded_rec.regeneration_total_tokens == 63
        assert loaded_rec.regeneration_model_calls == 3
        assert loaded_rec.regeneration_duration_seconds == 2.0
        assert loaded_rec.functional_validation_duration_seconds == 4.5
        assert loaded_rec.functional_validation_passed is False
        assert loaded_rec.total_workflow_tokens == 86
        assert loaded_rec.total_workflow_model_calls == 4
        assert loaded_rec.total_workflow_duration_seconds == 9.75
        assert loaded_rec.selected_artifact_count == 5
        assert loaded_rec.regenerated_artifact_count == 3
        assert loaded_rec.preserved_artifact_count == 1
        assert loaded_rec.unresolved_human_review_count == 1
        assert loaded_rec.duration_seconds == 12.5

    def test_validation_passed_true(self, tmp_path: Path) -> None:
        """functional_validation_passed=True survives round-trip."""
        store = RunRecordStore(tmp_path)
        rec = _make_e2e_record_data(functional_validation_passed=True)
        store.append(rec)
        loaded = store.load_all()[0]
        assert loaded.functional_validation_passed is True

    def test_validation_passed_none(self, tmp_path: Path) -> None:
        """functional_validation_passed=None survives round-trip."""
        store = RunRecordStore(tmp_path)
        rec = _make_e2e_record_data(functional_validation_passed=None)
        store.append(rec)
        loaded = store.load_all()[0]
        assert loaded.functional_validation_passed is None

    def test_validation_passed_false(self, tmp_path: Path) -> None:
        """functional_validation_passed=False survives round-trip."""
        store = RunRecordStore(tmp_path)
        rec = _make_e2e_record_data(functional_validation_passed=False)
        store.append(rec)
        loaded = store.load_all()[0]
        assert loaded.functional_validation_passed is False

    def test_durations_remain_numeric(self, tmp_path: Path) -> None:
        """Duration fields remain float, not strings."""
        store = RunRecordStore(tmp_path)
        rec = _make_e2e_record_data()
        store.append(rec)
        loaded = store.load_all()[0]
        assert isinstance(loaded.selection_duration_seconds, float)
        assert isinstance(loaded.regeneration_duration_seconds, float)
        assert isinstance(loaded.functional_validation_duration_seconds, float)
        assert isinstance(loaded.total_workflow_duration_seconds, float)
        assert isinstance(loaded.duration_seconds, float)

    def test_counts_remain_integers(self, tmp_path: Path) -> None:
        """Count/token fields remain int."""
        store = RunRecordStore(tmp_path)
        rec = _make_e2e_record_data()
        store.append(rec)
        loaded = store.load_all()[0]
        assert isinstance(loaded.selection_prompt_tokens, int)
        assert isinstance(loaded.selection_total_tokens, int)
        assert isinstance(loaded.regeneration_total_tokens, int)
        assert isinstance(loaded.total_workflow_tokens, int)
        assert isinstance(loaded.total_workflow_model_calls, int)
        assert isinstance(loaded.selected_artifact_count, int)
        assert isinstance(loaded.regenerated_artifact_count, int)
        assert isinstance(loaded.preserved_artifact_count, int)
        assert isinstance(loaded.unresolved_human_review_count, int)

    def test_historical_record_missing_fields(self, tmp_path: Path) -> None:
        """Historical record without new fields loads with defaults."""
        from dataclasses import asdict

        rec = _make_e2e_record_data()
        # Manually write JSON without the new fields by removing them from asdict
        raw_dict = asdict(rec)
        for field in [
            "selection_prompt_tokens", "selection_completion_tokens",
            "selection_total_tokens", "selection_model_calls",
            "selection_duration_seconds", "regeneration_prompt_tokens",
            "regeneration_completion_tokens", "regeneration_total_tokens",
            "regeneration_model_calls", "regeneration_duration_seconds",
            "functional_validation_duration_seconds",
            "functional_validation_passed", "total_workflow_tokens",
            "total_workflow_model_calls", "total_workflow_duration_seconds",
            "selected_artifact_count", "regenerated_artifact_count",
            "preserved_artifact_count", "unresolved_human_review_count",
        ]:
            raw_dict.pop(field, None)
        raw = json.dumps(raw_dict, sort_keys=True)
        (tmp_path / "run_records.jsonl").write_text(raw + "\n", encoding="utf-8")

        store = RunRecordStore(tmp_path)
        loaded = store.load_all()[0]
        # Check defaults
        assert loaded.selection_prompt_tokens == 0
        assert loaded.selection_total_tokens == 0
        assert loaded.regeneration_total_tokens == 0
        assert loaded.functional_validation_passed is None
        assert loaded.total_workflow_tokens == 0
        assert loaded.total_workflow_model_calls == 0
        assert loaded.selected_artifact_count == 0
        assert loaded.regenerated_artifact_count == 0

    def test_round_trip_checkpoint_resume_context(self, tmp_path: Path) -> None:
        """Checkpoint/resume context: record survives full write+read cycle."""
        store = RunRecordStore(tmp_path)
        rec = _make_e2e_record_data()
        store.append(rec)

        from benchmark.checkpoint.resume import ResumeManager
        CheckpointManager(tmp_path).write_atomic(CheckpointData(
            profile="test",
            execution_plan_hash="deadbeef",
            planned_run_ids=["e2e-test-001"],
            completed_run_ids=["e2e-test-001"],
            total_planned=1,
            total_completed=1,
            protocol_version="1.0",
            model_identity="test-model",
            config_hash="deadbeef",
            source_commit="abc123",
            completion_status="completed",
            scenario_ids=["test-scenario-001"],
            strategy_names=["selective"],
        ))

        resume = ResumeManager(
            runs_dir=tmp_path,
            protocol_version="1.0",
            config_hash="deadbeef",
            model_identity="test-model",
            source_commit="abc123",
        )
        skip_ids = resume.validate_and_get_skip_ids()
        assert "e2e-test-001" in skip_ids

        # Load from store and verify all fields preserved
        reloaded = RunRecordStore(tmp_path).load_all()
        assert len(reloaded) == 1
        loaded_rec = reloaded[0]
        assert loaded_rec.total_workflow_tokens == 86
        assert loaded_rec.total_workflow_model_calls == 4
        assert loaded_rec.total_workflow_duration_seconds == 9.75
        assert loaded_rec.functional_validation_passed is False

    def test_idempotent_append_with_new_fields(self, tmp_path: Path) -> None:
        """Appending identical end-to-end record is idempotent."""
        store = RunRecordStore(tmp_path)
        rec = _make_e2e_record_data()
        store.append(rec)
        store.append(rec)  # second append should be idempotent skip
        assert store.count() == 1

    def test_conflicting_append_with_new_fields_raises(self, tmp_path: Path) -> None:
        """Appending different end-to-end record with same run_id raises."""
        from benchmark.checkpoint.persistence import RunRecordIntegrityError
        store = RunRecordStore(tmp_path)
        rec1 = _make_e2e_record_data()
        store.append(rec1)
        rec2 = _make_e2e_record_data(total_workflow_tokens=999)
        with pytest.raises(RunRecordIntegrityError):
            store.append(rec2)
