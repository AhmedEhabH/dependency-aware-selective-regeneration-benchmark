from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from benchmark.checkpoint.checkpoint import CheckpointData, CheckpointManager, ProgressData, ProgressManager
from benchmark.checkpoint.persistence import RunRecordData, RunRecordStore
from benchmark.checkpoint.resume import ResumeManager, ResumeValidationError
from benchmark.checkpoint.package import ResultsPackager


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
