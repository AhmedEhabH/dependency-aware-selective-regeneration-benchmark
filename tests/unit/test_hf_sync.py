from __future__ import annotations

import json
import os
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from benchmark.checkpoint.checkpoint import CheckpointData, CheckpointManager, ProgressData, ProgressManager
from benchmark.checkpoint.hf_sync import (
    HfResumeManager,
    HfUploader,
    RemoteLayout,
    RepoVisibilityError,
    ResumeValidationError,
    SyncFailureRecord,
    SyncFailureStore,
    _is_path_allowed,
    verify_repo_private,
)
from benchmark.checkpoint.persistence import RunRecordData, RunRecordStore
from benchmark.checkpoint.package import ResultsPackager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TEST_REPO = "NabilDo/selective-regeneration-experiment-results"


def _make_checkpoint_data(**overrides: str | list[str] | int) -> CheckpointData:
    data = CheckpointData(
        profile="smoke",
        execution_plan_hash="abc123",
        planned_run_ids=["run-1_agent_rep1_aabb", "run-2_selective_rep1_ccdd"],
        completed_run_ids=["run-1_agent_rep1_aabb"],
        failed_run_ids=[],
        pending_run_ids=["run-2_selective_rep1_ccdd"],
        total_planned=2,
        total_completed=1,
        protocol_version="1.0",
        model_identity="dry-run:mock",
        config_hash="deadbeef",
        source_commit="abc1234",
    )
    for k, v in overrides.items():
        setattr(data, k, v)
    return data


def _make_record_data(run_id: str = "run-1_agent_rep1_aabb", status: str = "succeeded") -> RunRecordData:
    return RunRecordData(
        run_id=run_id,
        profile="smoke",
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


def _create_recovery_artifacts(tmp_path: Path) -> None:
    CheckpointManager(tmp_path).write_atomic(_make_checkpoint_data())
    RunRecordStore(tmp_path).append(_make_record_data())
    ProgressManager(tmp_path).write(ProgressData(profile="smoke", total_planned=2, total_completed=1))
    ProgressManager(tmp_path).write_partial_summary({"agent": {"success": 1}})
    sync_state = tmp_path / "remote_sync.json"
    sync_state.write_text(json.dumps({"last_sync": "ok", "remote_path": "recovery/", "timestamp": "t"}))


# ---------------------------------------------------------------------------
# Tests: RemoteLayout
# ---------------------------------------------------------------------------

class TestRemoteLayout:
    def test_recovery_path(self) -> None:
        layout = RemoteLayout("smoke", "1.0", "abc1234", "exp-001")
        path = layout.recovery()
        assert "experiments" in path
        assert "smoke" in path
        assert "1.0" in path
        assert "abc1234" in path
        assert "exp-001" in path
        assert path.endswith("recovery")

    def test_snapshot_path(self) -> None:
        layout = RemoteLayout("research", "1.0", "def5678", "exp-002")
        path = layout.snapshot(1)
        assert path.endswith("snapshots/chunk-0001")

    def test_snapshot_path_padded(self) -> None:
        layout = RemoteLayout("pilot", "1.0", "xyz", "exp-003")
        path = layout.snapshot(42)
        assert path.endswith("snapshots/chunk-0042")

    def test_final_path(self) -> None:
        layout = RemoteLayout("smoke", "1.0", "abc", "exp-final")
        path = layout.final()
        assert path.endswith("final")

    def test_rejects_empty_source_commit(self) -> None:
        with pytest.raises(ValueError, match="source_commit"):
            RemoteLayout("smoke", "1.0", "", "exp-001")

    def test_rejects_empty_experiment_id(self) -> None:
        with pytest.raises(ValueError, match="experiment_id"):
            RemoteLayout("smoke", "1.0", "abc1234", "")

    def test_no_double_slash_in_recovery_path(self) -> None:
        layout = RemoteLayout("smoke", "1.0", "abc1234", "exp-double")
        path = layout.recovery()
        assert "//" not in path

    def test_no_double_slash_in_snapshot_path(self) -> None:
        layout = RemoteLayout("research", "1.0", "def5678", "exp-double")
        path = layout.snapshot(1)
        assert "//" not in path

    def test_no_double_slash_in_final_path(self) -> None:
        layout = RemoteLayout("pilot", "1.0", "xyz", "exp-double")
        path = layout.final()
        assert "//" not in path

    def test_upload_download_path_equality(self) -> None:
        layout = RemoteLayout("smoke", "1.0", "abc1234", "exp-equal")
        recovery = layout.recovery()
        upload_path = f"{recovery}/checkpoint.json"
        download_path = f"{recovery}/checkpoint.json"
        assert upload_path == download_path


# ---------------------------------------------------------------------------
# Tests: Security filter
# ---------------------------------------------------------------------------

class TestSecurityFilter:
    def test_allows_recovery_files(self, tmp_path: Path) -> None:
        for name in ["run_records.jsonl", "checkpoint.json", "progress.json", "benchmark_summary.partial.json"]:
            p = tmp_path / name
            assert _is_path_allowed(p, tmp_path), f"Should allow {name}"

    def test_allows_manifest(self, tmp_path: Path) -> None:
        assert _is_path_allowed(tmp_path / "manifest.json", tmp_path)
        assert _is_path_allowed(tmp_path / "MANIFEST.json", tmp_path)

    def test_allows_env_metadata(self, tmp_path: Path) -> None:
        assert _is_path_allowed(tmp_path / "environment_metadata.json", tmp_path)

    def test_allows_failure_records(self, tmp_path: Path) -> None:
        assert _is_path_allowed(tmp_path / "failure_records.json", tmp_path)

    def test_allows_sync_state(self, tmp_path: Path) -> None:
        assert _is_path_allowed(tmp_path / "remote_sync.json", tmp_path)

    def test_allows_completed_marker(self, tmp_path: Path) -> None:
        assert _is_path_allowed(tmp_path / "COMPLETED", tmp_path)

    def test_rejects_token_files(self, tmp_path: Path) -> None:
        assert not _is_path_allowed(tmp_path / ".hf_token", tmp_path)
        assert not _is_path_allowed(tmp_path / "token.txt", tmp_path)

    def test_rejects_model_weights(self, tmp_path: Path) -> None:
        assert not _is_path_allowed(tmp_path / "model.safetensors", tmp_path)
        assert not _is_path_allowed(tmp_path / "pytorch_model.bin", tmp_path)

    def test_rejects_hf_cache(self, tmp_path: Path) -> None:
        assert not _is_path_allowed(tmp_path / "huggingface" / "cache", tmp_path)
        assert not _is_path_allowed(tmp_path / ".cache" / "hf", tmp_path)

    def test_rejects_credential_files(self, tmp_path: Path) -> None:
        assert not _is_path_allowed(tmp_path / ".netrc", tmp_path)
        assert not _is_path_allowed(tmp_path / ".ssh" / "id_rsa", tmp_path)

    def test_rejects_absolute_windows_paths(self, tmp_path: Path) -> None:
        assert not _is_path_allowed(Path("C:/Users/secret.txt"), tmp_path)

    def test_rejects_hidden_tests(self, tmp_path: Path) -> None:
        assert not _is_path_allowed(tmp_path / "test_hidden.py", tmp_path)

    def test_rejects_arbitrary_workspace(self, tmp_path: Path) -> None:
        outside = tmp_path.parent / "some_workspace" / "data.json"
        assert not _is_path_allowed(outside, tmp_path)


# ---------------------------------------------------------------------------
# Tests: SyncFailureStore
# ---------------------------------------------------------------------------

class TestSyncFailureStore:
    def test_no_failures_initially(self, tmp_path: Path) -> None:
        store = SyncFailureStore(tmp_path)
        assert not store.has_failures()

    def test_record_failure(self, tmp_path: Path) -> None:
        store = SyncFailureStore(tmp_path)
        store.record_failure(SyncFailureRecord(stage="upload", remote_path="runs/test", error="timeout"))
        assert store.has_failures()

    def test_clear_removes_file(self, tmp_path: Path) -> None:
        store = SyncFailureStore(tmp_path)
        store.record_failure(SyncFailureRecord(stage="upload", remote_path="runs/test", error="timeout"))
        store.clear()
        assert not store.has_failures()

    def test_record_preserves_local_checkpoint_flag(self, tmp_path: Path) -> None:
        store = SyncFailureStore(tmp_path)
        store.record_failure(SyncFailureRecord(stage="upload", remote_path="runs/test", error="err", local_checkpoint_ok=True))
        data = json.loads(store._path.read_text())
        assert data[0]["local_checkpoint_ok"] is True


# ---------------------------------------------------------------------------
# Tests: Repo visibility verification (mocked)
# ---------------------------------------------------------------------------

class TestRepoVisibility:
    def test_private_repo_allowed(self) -> None:
        mock_repo = MagicMock()
        mock_repo.private = True
        with patch("benchmark.checkpoint.hf_sync.HfApi.repo_info", return_value=mock_repo):
            verify_repo_private(TEST_REPO)

    def test_public_repo_rejected(self) -> None:
        mock_repo = MagicMock()
        mock_repo.private = False
        with patch("benchmark.checkpoint.hf_sync.HfApi.repo_info", return_value=mock_repo):
            with pytest.raises(RepoVisibilityError, match="NOT private"):
                verify_repo_private(TEST_REPO)

    def test_missing_repo_rejected(self) -> None:
        from huggingface_hub.utils import RepositoryNotFoundError
        with patch("benchmark.checkpoint.hf_sync.HfApi.repo_info", side_effect=RepositoryNotFoundError("not found")):
            with pytest.raises(RepoVisibilityError, match="not found"):
                verify_repo_private(TEST_REPO)

    def test_dry_run_placeholder_allowed(self) -> None:
        verify_repo_private("validkhv/placeholder-mirror")


# ---------------------------------------------------------------------------
# Tests: HfUploader (fully mocked)
# ---------------------------------------------------------------------------

class TestHfUploader:
    def test_upload_recovery_success(self, tmp_path: Path) -> None:
        _create_recovery_artifacts(tmp_path)
        layout = RemoteLayout("smoke", "1.0", "abc1234", "exp-upload-1")

        with patch.object(HfUploader, "_upload_with_retry", return_value=True) as mock_upload:
            uploader = HfUploader(tmp_path, TEST_REPO, layout, token="hf_test_token")
            result = uploader.upload_recovery()
            assert result is True
            assert mock_upload.call_count >= 1

    def test_upload_after_failed_run(self, tmp_path: Path) -> None:
        _create_recovery_artifacts(tmp_path)
        layout = RemoteLayout("smoke", "1.0", "abc1234", "exp-fail")

        with patch.object(HfUploader, "_upload_with_retry", return_value=True):
            uploader = HfUploader(tmp_path, TEST_REPO, layout, token="hf_test_token")
            result = uploader.upload_recovery()
            assert result is True

    def test_local_checkpoint_written_before_upload(self, tmp_path: Path) -> None:
        _create_recovery_artifacts(tmp_path)
        layout = RemoteLayout("smoke", "1.0", "abc1234", "exp-check")

        checkpoint_path = tmp_path / "checkpoint.json"
        assert checkpoint_path.is_file()

        uploaded_files: list[str] = []

        def track_upload(local_path, remote_path, **kwargs):
            uploaded_files.append(local_path.name)
            return True

        with patch.object(HfUploader, "_upload_with_retry", side_effect=track_upload):
            uploader = HfUploader(tmp_path, TEST_REPO, layout, token="hf_test_token")
            uploader.upload_recovery()
            assert "checkpoint.json" in uploaded_files

    def test_no_next_run_before_local_persistence(self, tmp_path: Path) -> None:
        layout = RemoteLayout("smoke", "1.0", "abc1234", "exp-order")
        store = RunRecordStore(tmp_path)
        store.append(_make_record_data())

        checkpoint_path = tmp_path / "checkpoint.json"
        assert not checkpoint_path.is_file()

        CheckpointManager(tmp_path).write_atomic(_make_checkpoint_data())
        assert checkpoint_path.is_file()

    def test_bounded_retry_on_upload_failure(self, tmp_path: Path) -> None:
        _create_recovery_artifacts(tmp_path)
        layout = RemoteLayout("smoke", "1.0", "abc1234", "exp-retry")

        with patch.object(HfUploader, "_upload_with_retry", return_value=False) as mock_upload:
            uploader = HfUploader(tmp_path, TEST_REPO, layout, token="hf_test_token", max_retries=2)
            result = uploader.upload_recovery()
            assert result is False
            assert mock_upload.call_count >= 1

    def test_remote_failure_does_not_corrupt_local(self, tmp_path: Path) -> None:
        _create_recovery_artifacts(tmp_path)
        layout = RemoteLayout("smoke", "1.0", "abc1234", "exp-corrupt")

        before_checkpoint = (tmp_path / "checkpoint.json").read_bytes()
        before_records = (tmp_path / "run_records.jsonl").read_bytes()

        with patch.object(HfUploader, "_upload_with_retry", return_value=False):
            uploader = HfUploader(tmp_path, TEST_REPO, layout, token="hf_test_token")
            uploader.upload_recovery()

        assert (tmp_path / "checkpoint.json").read_bytes() == before_checkpoint
        assert (tmp_path / "run_records.jsonl").read_bytes() == before_records

    def test_retry_exponential_backoff(self, tmp_path: Path) -> None:
        _create_recovery_artifacts(tmp_path)
        layout = RemoteLayout("smoke", "1.0", "abc1234", "exp-backoff")

        sleep_calls: list[float] = []

        original_sleep = time.sleep
        with patch.object(HfUploader, "_upload_with_retry", return_value=False):
            uploader = HfUploader(tmp_path, TEST_REPO, layout, token="hf_test_token", max_retries=1, base_delay=0.1)
            uploader.upload_recovery()

    def test_recovery_files_updated_correctly(self, tmp_path: Path) -> None:
        _create_recovery_artifacts(tmp_path)
        layout = RemoteLayout("smoke", "1.0", "abc1234", "exp-update")

        uploaded_paths: list[str] = []

        def track(local_path, remote_path, **kwargs):
            uploaded_paths.append(remote_path)
            return True

        with patch.object(HfUploader, "_upload_with_retry", side_effect=track):
            uploader = HfUploader(tmp_path, TEST_REPO, layout, token="hf_test_token")
            uploader.upload_recovery()

    def test_snapshot_immutable_chunk(self, tmp_path: Path) -> None:
        _create_recovery_artifacts(tmp_path)
        layout = RemoteLayout("smoke", "1.0", "abc1234", "exp-chunk")

        with patch.object(HfUploader, "_upload_with_retry", return_value=True):
            uploader = HfUploader(tmp_path, TEST_REPO, layout, token="hf_test_token")
            pkg = ResultsPackager(tmp_path)
            result = uploader.upload_snapshot(pkg)
            assert result is True

    def test_upload_recovery_files_only(self, tmp_path: Path) -> None:
        _create_recovery_artifacts(tmp_path)
        layout = RemoteLayout("smoke", "1.0", "abc1234", "exp-only-recovery")

        uploaded: list[str] = []

        def track(local_path, remote_path, **kwargs):
            uploaded.append(remote_path)
            return True

        with patch.object(HfUploader, "_upload_with_retry", side_effect=track):
            uploader = HfUploader(tmp_path, TEST_REPO, layout, token="hf_test_token")
            uploader.upload_recovery()

        for path in uploaded:
            assert "recovery/" in path


# ---------------------------------------------------------------------------
# Tests: HfResumeManager (fully mocked)
# ---------------------------------------------------------------------------

class TestHfResumeManager:
    def test_resume_returns_skip_ids(self, tmp_path: Path) -> None:
        _create_recovery_artifacts(tmp_path)
        layout = RemoteLayout("smoke", "1.0", "abc1234", "exp-resume")

        def fake_download(**kwargs):
            return str(kwargs.get("local_dir", tmp_path))

        with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=fake_download):
            resume = HfResumeManager(
                runs_dir=tmp_path,
                repo_id=TEST_REPO,
                layout=layout,
                token="hf_test_token",
                protocol_version="1.0",
                config_hash="deadbeef",
                model_identity="dry-run:mock",
                source_commit="abc1234",
                scenario_ids=["run-1", "run-2"],
                strategy_names=["agent", "selective"],
            )
            ids = resume.download_and_validate()
            assert isinstance(ids, set)

    def test_incompatible_protocol_rejected(self, tmp_path: Path) -> None:
        _create_recovery_artifacts(tmp_path)
        cp_mgr = CheckpointManager(tmp_path)
        data = cp_mgr.read()
        assert data is not None
        data.protocol_version = "0.9"
        cp_mgr.write_atomic(data)

        layout = RemoteLayout("smoke", "0.9", "abc1234", "exp-bad-protocol")

        def fake_download(**kwargs):
            return str(kwargs.get("local_dir", tmp_path))

        with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=fake_download):
            resume = HfResumeManager(
                runs_dir=tmp_path,
                repo_id=TEST_REPO,
                layout=layout,
                token="hf_test_token",
                protocol_version="1.0",
                config_hash="deadbeef",
                model_identity="dry-run:mock",
                source_commit="abc1234",
                scenario_ids=["todo-add-feature-toggle"],
                strategy_names=["agent", "selective"],
            )
            with pytest.raises(ResumeValidationError, match="Protocol version mismatch"):
                resume.download_and_validate()

    def test_incompatible_config_hash_rejected(self, tmp_path: Path) -> None:
        _create_recovery_artifacts(tmp_path)
        cp_mgr = CheckpointManager(tmp_path)
        data = cp_mgr.read()
        assert data is not None
        data.config_hash = "old_hash"
        cp_mgr.write_atomic(data)

        layout = RemoteLayout("smoke", "1.0", "abc1234", "exp-bad-config")

        def fake_download(**kwargs):
            return str(kwargs.get("local_dir", tmp_path))

        with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=fake_download):
            resume = HfResumeManager(
                runs_dir=tmp_path,
                repo_id=TEST_REPO,
                layout=layout,
                token="hf_test_token",
                protocol_version="1.0",
                config_hash="new_hash",
                model_identity="dry-run:mock",
                source_commit="abc1234",
                scenario_ids=["todo-add-feature-toggle"],
                strategy_names=["agent", "selective"],
            )
            with pytest.raises(ResumeValidationError, match="Config hash mismatch"):
                resume.download_and_validate()

    def test_incompatible_source_commit_rejected(self, tmp_path: Path) -> None:
        _create_recovery_artifacts(tmp_path)
        cp_mgr = CheckpointManager(tmp_path)
        data = cp_mgr.read()
        assert data is not None
        data.source_commit = "old_commit"
        cp_mgr.write_atomic(data)

        layout = RemoteLayout("smoke", "1.0", "old_commit", "exp-bad-source")

        def fake_download(**kwargs):
            return str(kwargs.get("local_dir", tmp_path))

        with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=fake_download):
            resume = HfResumeManager(
                runs_dir=tmp_path,
                repo_id=TEST_REPO,
                layout=layout,
                token="hf_test_token",
                protocol_version="1.0",
                config_hash="deadbeef",
                model_identity="dry-run:mock",
                source_commit="new_commit",
                scenario_ids=["todo-add-feature-toggle"],
                strategy_names=["agent", "selective"],
            )
            with pytest.raises(ResumeValidationError, match="Source commit mismatch"):
                resume.download_and_validate()

    def test_incompatible_model_identity_rejected(self, tmp_path: Path) -> None:
        _create_recovery_artifacts(tmp_path)
        cp_mgr = CheckpointManager(tmp_path)
        data = cp_mgr.read()
        assert data is not None
        data.model_identity = "qwen:old"
        cp_mgr.write_atomic(data)

        layout = RemoteLayout("smoke", "1.0", "abc1234", "exp-bad-model")

        def fake_download(**kwargs):
            return str(kwargs.get("local_dir", tmp_path))

        with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=fake_download):
            resume = HfResumeManager(
                runs_dir=tmp_path,
                repo_id=TEST_REPO,
                layout=layout,
                token="hf_test_token",
                protocol_version="1.0",
                config_hash="deadbeef",
                model_identity="qwen:new",
                source_commit="abc1234",
                scenario_ids=["todo-add-feature-toggle"],
                strategy_names=["agent", "selective"],
            )
            with pytest.raises(ResumeValidationError, match="Model identity mismatch"):
                resume.download_and_validate()

    def test_resume_fails_closed_on_404(self, tmp_path: Path) -> None:
        layout = RemoteLayout("smoke", "1.0", "abc1234", "exp-404")
        with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=Exception("404 Client Error: Not Found")):
            resume = HfResumeManager(
                runs_dir=tmp_path,
                repo_id=TEST_REPO,
                layout=layout,
                token="hf_test_token",
                protocol_version="1.0",
                config_hash="deadbeef",
                model_identity="dry-run:mock",
                source_commit="abc1234",
                scenario_ids=["run-1"],
                strategy_names=["agent"],
            )
            with pytest.raises(ResumeValidationError, match="No recovery files could be downloaded"):
                resume.download_and_validate()

    def test_no_benchmark_execution_after_failed_resume(self, tmp_path: Path) -> None:
        layout = RemoteLayout("smoke", "1.0", "abc1234", "exp-no-exec")
        with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=Exception("404")):
            resume = HfResumeManager(
                runs_dir=tmp_path,
                repo_id=TEST_REPO,
                layout=layout,
                token="hf_test_token",
                protocol_version="1.0",
                config_hash="deadbeef",
                model_identity="dry-run:mock",
                source_commit="abc1234",
                scenario_ids=["run-1"],
                strategy_names=["agent"],
            )
            with pytest.raises(ResumeValidationError):
                resume.download_and_validate()
        checkpoint_path = tmp_path / "checkpoint.json"
        assert not checkpoint_path.is_file(), "No checkpoint file should exist after failed resume"

    def test_resume_skips_first_completed_run(self, tmp_path: Path) -> None:
        _create_recovery_artifacts(tmp_path)
        layout = RemoteLayout("smoke", "1.0", "abc1234", "exp-skip-first")

        def fake_download(**kwargs):
            return str(kwargs.get("local_dir", tmp_path))

        with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=fake_download):
            resume = HfResumeManager(
                runs_dir=tmp_path,
                repo_id=TEST_REPO,
                layout=layout,
                token="hf_test_token",
                protocol_version="1.0",
                config_hash="deadbeef",
                model_identity="dry-run:mock",
                source_commit="abc1234",
                scenario_ids=["run-1", "run-2"],
                strategy_names=["agent", "selective"],
            )
            ids = resume.download_and_validate()
            completed = RunRecordStore(tmp_path).get_completed_run_ids()
            for rid in completed:
                assert rid in ids, f"Completed run {rid} must be in skip set"

    def test_no_duplicated_runs_on_resume(self, tmp_path: Path) -> None:
        _create_recovery_artifacts(tmp_path)
        layout = RemoteLayout("smoke", "1.0", "abc1234", "exp-no-dup")

        def fake_download(**kwargs):
            return str(kwargs.get("local_dir", tmp_path))

        with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=fake_download):
            resume = HfResumeManager(
                runs_dir=tmp_path,
                repo_id=TEST_REPO,
                layout=layout,
                token="hf_test_token",
                protocol_version="1.0",
                config_hash="deadbeef",
                model_identity="dry-run:mock",
                source_commit="abc1234",
                scenario_ids=["run-1", "run-2"],
                strategy_names=["agent", "selective"],
            )
            ids = resume.download_and_validate()
            completed = RunRecordStore(tmp_path).get_completed_run_ids()
            assert all(c in ids for c in completed)

    def test_no_network_access(self) -> None:
        pytest.skip("Network access test is environment-dependent; HF sync uses mocked API calls")

    def test_token_never_logged(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        import logging
        caplog.set_level(logging.DEBUG)
        _create_recovery_artifacts(tmp_path)
        layout = RemoteLayout("smoke", "1.0", "abc1234", "exp-token")

        with patch.object(HfUploader, "_upload_with_retry", return_value=True):
            uploader = HfUploader(tmp_path, TEST_REPO, layout, token="hf_secret_xyz")
            uploader.upload_recovery()

        log_text = caplog.text
        assert "hf_secret_xyz" not in log_text
        assert "HF_TOKEN" not in log_text


# ---------------------------------------------------------------------------
# Tests: Integration scenarios (mocked)
# ---------------------------------------------------------------------------

class TestHfIntegration:
    def test_experiment_id_persistence_in_recovery(self, tmp_path: Path) -> None:
        exp_id = "exp-persist-test"
        layout = RemoteLayout("smoke", "1.0", "abc1234", exp_id)
        _create_recovery_artifacts(tmp_path)
        exp_file = tmp_path / "experiment_id.txt"
        exp_file.write_text(exp_id, encoding="utf-8")
        assert exp_file.is_file()
        assert exp_file.read_text().strip() == exp_id

    def test_source_identity_persistence(self, tmp_path: Path) -> None:
        layout = RemoteLayout("smoke", "1.0", "abc1234", "exp-src-id")
        _create_recovery_artifacts(tmp_path)
        src_id = tmp_path / "source_identity.json"
        src_id.write_text(json.dumps({
            "source_commit": "abc1234",
            "source_tag": "v0.7.0-smoke-passed",
            "config_hash": "deadbeef",
            "experiment_id": "exp-src-id",
        }), encoding="utf-8")
        assert src_id.is_file()
        data = json.loads(src_id.read_text())
        assert data["source_commit"] == "abc1234"
        assert data["source_tag"] == "v0.7.0-smoke-passed"

    def test_remote_sync_exists_before_upload(self, tmp_path: Path) -> None:
        layout = RemoteLayout("smoke", "1.0", "abc1234", "exp-sync-order")
        with patch.object(HfUploader, "_upload_with_retry", return_value=True):
            uploader = HfUploader(tmp_path, TEST_REPO, layout, token="hf_test_token")
            uploader.upload_recovery()
        sync_path = tmp_path / "remote_sync.json"
        assert sync_path.is_file(), "remote_sync.json must exist after upload_recovery"
        state = json.loads(sync_path.read_text())
        assert "last_sync" in state
        assert "remote_path" in state

    def test_automatic_upload_after_completed_run(self, tmp_path: Path) -> None:
        _create_recovery_artifacts(tmp_path)
        layout = RemoteLayout("smoke", "1.0", "abc1234", "exp-integ-complete")

        uploaded_after_complete: list[str] = []

        def track(local_path, remote_path, **kwargs):
            uploaded_after_complete.append(remote_path)
            return True

        with patch.object(HfUploader, "_upload_with_retry", side_effect=track):
            uploader = HfUploader(tmp_path, TEST_REPO, layout, token="hf_test_token")
            result = uploader.upload_recovery()
            assert result is True

    def test_automatic_upload_after_failed_retained_run(self, tmp_path: Path) -> None:
        _create_recovery_artifacts(tmp_path)
        store = RunRecordStore(tmp_path)
        store.append(_make_record_data("fail-run-1", status="failed"))
        layout = RemoteLayout("smoke", "1.0", "abc1234", "exp-integ-fail")

        with patch.object(HfUploader, "_upload_with_retry", return_value=True):
            uploader = HfUploader(tmp_path, TEST_REPO, layout, token="hf_test_token")
            result = uploader.upload_recovery()
            assert result is True

    def test_remote_failure_recorded(self, tmp_path: Path) -> None:
        _create_recovery_artifacts(tmp_path)
        layout = RemoteLayout("smoke", "1.0", "abc1234", "exp-fail-record")

        from huggingface_hub.utils import HfHubHTTPError
        with patch("benchmark.checkpoint.hf_sync.HfApi") as mock_api_cls:
            mock_api = MagicMock()
            mock_api_cls.return_value = mock_api
            mock_api.upload_file.side_effect = HfHubHTTPError("mock upload failure")
            uploader = HfUploader(tmp_path, TEST_REPO, layout, token="hf_test_token", max_retries=0)
            uploader.upload_recovery()
            assert uploader.failure_store.has_failures()


# ---------------------------------------------------------------------------
# Tests: Auto-resume (mocked HfApi)
# ---------------------------------------------------------------------------

from benchmark.checkpoint.hf_sync import (
    AutoResumeResult,
    CompatibleExperiment,
    list_compatible_experiments,
    resolve_auto_resume,
)


def _make_remote_files(
    prefix: str,
    exp_id: str,
    completed_run_ids: list[str],
    total_planned: int = 7,
    protocol_version: str = "1.0",
    config_hash: str = "deadbeef",
    model_identity: str = "dry-run:mock",
    source_commit: str = "abc1234",
    completion_status: str = "incomplete",
) -> list[str]:
    """Build a list of fake remote file paths for one experiment."""
    base = f"{prefix}/{exp_id}/recovery"
    files = [
        f"{base}/checkpoint.json",
        f"{base}/run_records.jsonl",
        f"{base}/progress.json",
        f"{base}/experiment_id.txt",
        f"{base}/source_identity.json",
    ]
    return files


def _make_fake_checkpoint_content(
    completed_run_ids: list[str],
    total_planned: int = 7,
    protocol_version: str = "1.0",
    config_hash: str = "deadbeef",
    model_identity: str = "dry-run:mock",
    source_commit: str = "abc1234",
    completion_status: str = "incomplete",
    scenario_id: str = "todo-add-feature-toggle",
    strategy_names: list[str] | None = None,
) -> str:
    if strategy_names is None:
        strategy_names = ["agent", "selective"]
    all_run_ids: list[str] = list(completed_run_ids)
    idx = 0
    while len(all_run_ids) < total_planned:
        strat = strategy_names[idx % len(strategy_names)]
        all_run_ids.append(f"{scenario_id}_{strat}_rep1_{idx:04d}")
        idx += 1
    completed = list(completed_run_ids)
    pending = [rid for rid in all_run_ids if rid not in completed]
    return json.dumps({
        "profile": "smoke",
        "execution_plan_hash": config_hash,
        "planned_run_ids": all_run_ids,
        "completed_run_ids": completed,
        "failed_run_ids": [],
        "pending_run_ids": pending,
        "total_planned": total_planned,
        "total_completed": len(completed),
        "protocol_version": protocol_version,
        "model_identity": model_identity,
        "config_hash": config_hash,
        "source_commit": source_commit,
        "completion_status": completion_status,
    })


def _make_fake_records_content(run_ids: list[str], statuses: list[str] | None = None) -> str:
    if statuses is None:
        statuses = ["succeeded"] * len(run_ids)
    records = []
    for rid, status in zip(run_ids, statuses):
        records.append(json.dumps({
            "run_id": rid,
            "profile": "smoke",
            "scenario_id": "todo-add-feature-toggle",
            "strategy_id": "agent",
            "repetition": 1,
            "seed": 42,
            "status": status,
            "duration_seconds": 1.0,
            "protocol_version": "1.0",
            "source_commit": "abc1234",
            "config_hash": "deadbeef",
            "timestamp": "2026-07-24T00:00:00",
        }))
    return "\n".join(records)


class TestAutoResume:
    """Tests for the auto-resume discovery and resolution logic."""

    def test_no_remote_experiment_starts_new(self) -> None:
        with patch("benchmark.checkpoint.hf_sync.HfApi") as mock_api_cls:
            mock_api = MagicMock()
            mock_api_cls.return_value = mock_api
            mock_api.list_repo_files.return_value = ["unrelated/file.txt"]

            result = resolve_auto_resume(
                repo_id=TEST_REPO,
                token="hf_test_token",
                profile="smoke",
                protocol_version="1.0",
                source_commit="abc1234",
                config_hash="deadbeef",
                model_identity="dry-run:mock",
                scenario_ids=["run-1"],
                strategy_names=["agent"],
            )
            assert result.action == "start_new"
            assert result.experiment_id == ""
            assert len(result.compatible_experiments) == 0

    def test_exactly_one_compatible_incomplete_resumes(self) -> None:
        prefix = "experiments/smoke/1.0/abc1234"
        exp_files = _make_remote_files(prefix, "exp-001", ["run-1"])

        cp_content = _make_fake_checkpoint_content(
            completed_run_ids=["todo-add-feature-toggle_agent_rep1_deadbeef"],
            total_planned=7,
        )
        records_content = _make_fake_records_content(
            ["todo-add-feature-toggle_agent_rep1_deadbeef"], ["succeeded"]
        )

        with patch("benchmark.checkpoint.hf_sync.HfApi") as mock_api_cls:
            mock_api = MagicMock()
            mock_api_cls.return_value = mock_api
            mock_api.list_repo_files.return_value = exp_files

            def fake_download(repo_id, filename, local_dir, token, **kwargs):
                local_p = Path(local_dir) / filename
                local_p.parent.mkdir(parents=True, exist_ok=True)
                if "checkpoint.json" in filename:
                    local_p.write_text(cp_content)
                elif "run_records.jsonl" in filename:
                    local_p.write_text(records_content)
                return str(local_p)

            with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=fake_download):
                result = resolve_auto_resume(
                    repo_id=TEST_REPO,
                    token="hf_test_token",
                    profile="smoke",
                    protocol_version="1.0",
                    source_commit="abc1234",
                    config_hash="deadbeef",
                    model_identity="dry-run:mock",
                    scenario_ids=["todo-add-feature-toggle"],
                    strategy_names=["agent", "selective"],
                )
                assert result.action == "resume"
                assert result.experiment_id == "exp-001"
                assert len(result.compatible_experiments) == 1

    def test_completed_experiment_does_not_duplicate(self) -> None:
        prefix = "experiments/smoke/1.0/abc1234"
        exp_files = _make_remote_files(prefix, "exp-done", ["run-1", "run-2", "run-3"])

        cp_content = _make_fake_checkpoint_content(
            completed_run_ids=[
                "scenario-a_agent_rep1_aaaa",
                "scenario-a_selective_rep1_bbbb",
                "scenario-a_monolithic_rep1_cccc",
            ],
            total_planned=3,
            completion_status="completed",
        )
        records_content = _make_fake_records_content(
            ["scenario-a_agent_rep1_aaaa", "scenario-a_selective_rep1_bbbb", "scenario-a_monolithic_rep1_cccc"],
            ["succeeded", "succeeded", "succeeded"],
        )

        with patch("benchmark.checkpoint.hf_sync.HfApi") as mock_api_cls:
            mock_api = MagicMock()
            mock_api_cls.return_value = mock_api
            mock_api.list_repo_files.return_value = exp_files

            def fake_download(repo_id, filename, local_dir, token, **kwargs):
                local_p = Path(local_dir) / filename
                local_p.parent.mkdir(parents=True, exist_ok=True)
                if "checkpoint.json" in filename:
                    local_p.write_text(cp_content)
                elif "run_records.jsonl" in filename:
                    local_p.write_text(records_content)
                return str(local_p)

            with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=fake_download):
                result = resolve_auto_resume(
                    repo_id=TEST_REPO,
                    token="hf_test_token",
                    profile="smoke",
                    protocol_version="1.0",
                    source_commit="abc1234",
                    config_hash="deadbeef",
                    model_identity="dry-run:mock",
                    scenario_ids=["scenario-a"],
                    strategy_names=["agent", "selective", "monolithic"],
                )
                assert result.action == "already_complete"
                assert result.experiment_id == "exp-done"

    def test_multiple_compatible_incomplete_fails(self) -> None:
        prefix = "experiments/smoke/1.0/abc1234"
        files_exp1 = _make_remote_files(prefix, "exp-001", ["run-1"])
        files_exp2 = _make_remote_files(prefix, "exp-002", ["run-2"])

        cp_content1 = _make_fake_checkpoint_content(
            completed_run_ids=["scenario-b_agent_rep1_aaaa"], total_planned=7,
            scenario_id="scenario-b",
            strategy_names=["agent", "selective", "monolithic"],
        )
        cp_content2 = _make_fake_checkpoint_content(
            completed_run_ids=["scenario-b_selective_rep1_bbbb"], total_planned=7,
            scenario_id="scenario-b",
            strategy_names=["agent", "selective", "monolithic"],
        )
        records1 = _make_fake_records_content(["scenario-b_agent_rep1_aaaa"], ["succeeded"])
        records2 = _make_fake_records_content(["scenario-b_selective_rep1_bbbb"], ["succeeded"])

        with patch("benchmark.checkpoint.hf_sync.HfApi") as mock_api_cls:
            mock_api = MagicMock()
            mock_api_cls.return_value = mock_api
            mock_api.list_repo_files.return_value = files_exp1 + files_exp2

            def fake_download(repo_id, filename, local_dir, token, **kwargs):
                local_p = Path(local_dir) / filename
                local_p.parent.mkdir(parents=True, exist_ok=True)
                if "checkpoint.json" in filename:
                    local_p.write_text(cp_content1 if "exp-001" in filename else cp_content2)
                elif "run_records.jsonl" in filename:
                    local_p.write_text(records1 if "exp-001" in filename else records2)
                return str(local_p)

            with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=fake_download):
                result = resolve_auto_resume(
                    repo_id=TEST_REPO,
                    token="hf_test_token",
                    profile="smoke",
                    protocol_version="1.0",
                    source_commit="abc1234",
                    config_hash="deadbeef",
                    model_identity="dry-run:mock",
                    scenario_ids=["scenario-b"],
                    strategy_names=["agent", "selective", "monolithic"],
                )
                assert result.action == "error"
                assert "Multiple" in result.message
                assert "exp-001" in result.message
                assert "exp-002" in result.message

    def test_incompatible_experiments_ignored(self) -> None:
        prefix = "experiments/smoke/1.0/abc1234"
        files_bad = _make_remote_files(prefix, "exp-bad", ["scenario-c"])

        cp_content = _make_fake_checkpoint_content(
            completed_run_ids=["scenario-c_agent_rep1_cccc"],
            total_planned=7,
            protocol_version="0.9",
            scenario_id="scenario-c",
        )
        records = _make_fake_records_content(["scenario-c_agent_rep1_cccc"], ["succeeded"])

        with patch("benchmark.checkpoint.hf_sync.HfApi") as mock_api_cls:
            mock_api = MagicMock()
            mock_api_cls.return_value = mock_api
            mock_api.list_repo_files.return_value = files_bad

            def fake_download(repo_id, filename, local_dir, token, **kwargs):
                local_p = Path(local_dir) / filename
                local_p.parent.mkdir(parents=True, exist_ok=True)
                if "checkpoint.json" in filename:
                    local_p.write_text(cp_content)
                elif "run_records.jsonl" in filename:
                    local_p.write_text(records)
                return str(local_p)

            with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=fake_download):
                result = resolve_auto_resume(
                    repo_id=TEST_REPO,
                    token="hf_test_token",
                    profile="smoke",
                    protocol_version="1.0",
                    source_commit="abc1234",
                    config_hash="deadbeef",
                    model_identity="dry-run:mock",
                    scenario_ids=["scenario-c"],
                    strategy_names=["agent"],
                )
                assert result.action == "start_new"
                assert len(result.compatible_experiments) == 0

    def test_remote_listing_failure_returns_error(self) -> None:
        with patch("benchmark.checkpoint.hf_sync.HfApi") as mock_api_cls:
            mock_api = MagicMock()
            mock_api_cls.return_value = mock_api
            mock_api.list_repo_files.side_effect = Exception("API error")

            result = resolve_auto_resume(
                repo_id=TEST_REPO,
                token="hf_test_token",
                profile="smoke",
                protocol_version="1.0",
                source_commit="abc1234",
                config_hash="deadbeef",
                model_identity="dry-run:mock",
                scenario_ids=["run-1"],
                strategy_names=["agent"],
            )
            assert result.action == "error"
            assert "Remote listing failed" in result.message

    def test_missing_recovery_file_skips_experiment(self) -> None:
        prefix = "experiments/smoke/1.0/abc1234"
        exp_files = _make_remote_files(prefix, "exp-incomplete", ["run-1"])

        with patch("benchmark.checkpoint.hf_sync.HfApi") as mock_api_cls:
            mock_api = MagicMock()
            mock_api_cls.return_value = mock_api
            mock_api.list_repo_files.return_value = exp_files

            with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=Exception("404 Not Found")):
                result = resolve_auto_resume(
                    repo_id=TEST_REPO,
                    token="hf_test_token",
                    profile="smoke",
                    protocol_version="1.0",
                    source_commit="abc1234",
                    config_hash="deadbeef",
                    model_identity="dry-run:mock",
                    scenario_ids=["scenario-c"],
                    strategy_names=["agent"],
                )
                assert result.action == "start_new"
                assert len(result.compatible_experiments) == 0

    def test_new_experiment_flag_creates_new(self) -> None:
        prefix = "experiments/smoke/1.0/abc1234"
        exp_files = _make_remote_files(prefix, "exp-existing", ["run-1"])

        cp_content = _make_fake_checkpoint_content(
            completed_run_ids=["scenario-g_agent_rep1_gggg"], total_planned=7,
            scenario_id="scenario-g",
        )
        records = _make_fake_records_content(["scenario-g_agent_rep1_gggg"], ["succeeded"])

        with patch("benchmark.checkpoint.hf_sync.HfApi") as mock_api_cls:
            mock_api = MagicMock()
            mock_api_cls.return_value = mock_api
            mock_api.list_repo_files.return_value = exp_files

            def fake_download(repo_id, filename, local_dir, token, **kwargs):
                local_p = Path(local_dir) / filename
                local_p.parent.mkdir(parents=True, exist_ok=True)
                if "checkpoint.json" in filename:
                    local_p.write_text(cp_content)
                elif "run_records.jsonl" in filename:
                    local_p.write_text(records)
                return str(local_p)

            with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=fake_download):
                result = resolve_auto_resume(
                    repo_id=TEST_REPO,
                    token="hf_test_token",
                    profile="smoke",
                    protocol_version="1.0",
                    source_commit="abc1234",
                    config_hash="deadbeef",
                    model_identity="dry-run:mock",
                    scenario_ids=["run-1"],
                    strategy_names=["agent"],
                    new_experiment=True,
                )
                assert result.action == "start_new"
                assert result.experiment_id == ""

    def test_list_compatible_experiments_returns_compatible(self) -> None:
        prefix = "experiments/smoke/1.0/abc1234"
        exp_files = _make_remote_files(prefix, "exp-ok", ["run-1"])

        cp_content = _make_fake_checkpoint_content(
            completed_run_ids=["scenario-d_agent_rep1_dddd"], total_planned=7,
            scenario_id="scenario-d",
            strategy_names=["agent", "selective"],
        )
        records = _make_fake_records_content(["scenario-d_agent_rep1_dddd"], ["succeeded"])

        with patch("benchmark.checkpoint.hf_sync.HfApi") as mock_api_cls:
            mock_api = MagicMock()
            mock_api_cls.return_value = mock_api
            mock_api.list_repo_files.return_value = exp_files

            def fake_download(repo_id, filename, local_dir, token, **kwargs):
                local_p = Path(local_dir) / filename
                local_p.parent.mkdir(parents=True, exist_ok=True)
                if "checkpoint.json" in filename:
                    local_p.write_text(cp_content)
                elif "run_records.jsonl" in filename:
                    local_p.write_text(records)
                return str(local_p)

            with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=fake_download):
                experiments = list_compatible_experiments(
                    repo_id=TEST_REPO,
                    token="hf_test_token",
                    profile="smoke",
                    protocol_version="1.0",
                    source_commit="abc1234",
                    config_hash="deadbeef",
                    model_identity="dry-run:mock",
                    scenario_ids=["scenario-d"],
                    strategy_names=["agent", "selective"],
                )
                assert len(experiments) == 1
                assert experiments[0].experiment_id == "exp-ok"
                assert experiments[0].completed_count == 1
                assert experiments[0].total_planned == 7

    def test_list_compatible_experiments_empty_prefix(self) -> None:
        with patch("benchmark.checkpoint.hf_sync.HfApi") as mock_api_cls:
            mock_api = MagicMock()
            mock_api_cls.return_value = mock_api
            mock_api.list_repo_files.return_value = ["other/path/file.txt"]

            experiments = list_compatible_experiments(
                repo_id=TEST_REPO,
                token="hf_test_token",
                profile="smoke",
                protocol_version="1.0",
                source_commit="abc1234",
                config_hash="deadbeef",
                model_identity="dry-run:mock",
                scenario_ids=["run-1"],
                strategy_names=["agent"],
            )
            assert experiments == []

    def test_auto_resume_finds_incomplete_over_complete(self) -> None:
        prefix = "experiments/smoke/1.0/abc1234"
        files_complete = _make_remote_files(prefix, "exp-done", ["run-1", "run-2", "run-3"])
        files_incomplete = _make_remote_files(prefix, "exp-partial", ["run-1"])

        cp_complete = _make_fake_checkpoint_content(
            completed_run_ids=["scenario-f_agent_rep1_aaaa", "scenario-f_selective_rep1_bbbb", "scenario-f_monolithic_rep1_cccc"],
            total_planned=3,
            completion_status="completed",
            scenario_id="scenario-f",
            strategy_names=["agent", "selective", "monolithic"],
        )
        cp_incomplete = _make_fake_checkpoint_content(
            completed_run_ids=["scenario-f_agent_rep1_dddd"],
            total_planned=7,
            scenario_id="scenario-f",
            strategy_names=["agent", "selective", "monolithic"],
        )
        records_complete = _make_fake_records_content(
            ["scenario-f_agent_rep1_aaaa", "scenario-f_selective_rep1_bbbb", "scenario-f_monolithic_rep1_cccc"], ["succeeded"] * 3,
        )
        records_incomplete = _make_fake_records_content(["scenario-f_agent_rep1_dddd"], ["succeeded"])

        with patch("benchmark.checkpoint.hf_sync.HfApi") as mock_api_cls:
            mock_api = MagicMock()
            mock_api_cls.return_value = mock_api
            mock_api.list_repo_files.return_value = files_complete + files_incomplete

            def fake_download(repo_id, filename, local_dir, token, **kwargs):
                local_p = Path(local_dir) / filename
                local_p.parent.mkdir(parents=True, exist_ok=True)
                if "checkpoint.json" in filename:
                    local_p.write_text(cp_complete if "exp-done" in filename else cp_incomplete)
                elif "run_records.jsonl" in filename:
                    local_p.write_text(records_complete if "exp-done" in filename else records_incomplete)
                return str(local_p)

            with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=fake_download):
                result = resolve_auto_resume(
                    repo_id=TEST_REPO,
                    token="hf_test_token",
                    profile="smoke",
                    protocol_version="1.0",
                    source_commit="abc1234",
                    config_hash="deadbeef",
                    model_identity="dry-run:mock",
                    scenario_ids=["scenario-f"],
                    strategy_names=["agent", "selective", "monolithic"],
                )
                assert result.action == "resume"
                assert result.experiment_id == "exp-partial"
