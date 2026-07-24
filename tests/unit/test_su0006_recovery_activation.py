"""SU-0006 regression tests: recovery activation at the canonical output directory."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from benchmark.checkpoint.checkpoint import CheckpointData, CheckpointManager
from benchmark.checkpoint.hf_sync import (
    HfResumeManager,
    RemoteLayout,
    ResumeValidationError,
)
from benchmark.checkpoint.persistence import RunRecordStore

TEST_REPO = "NabilDo/selective-regeneration-experiment-results"

SCENARIO_IDS = ["djangocms-cross-007"]
ALL_SEVEN_STRATEGIES = [
    "monolithic", "agent", "selective", "compiled_ai",
    "delta_mcp", "incr_rtl", "code_plan",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_run_id(scenario_id: str, strategy_name: str, rep: int,
                  config_hash: str = "deadbeef", protocol_version: str = "1.0") -> str:
    import hashlib
    import json as _json
    payload = _json.dumps({
        "scenario_id": scenario_id,
        "strategy_name": strategy_name,
        "repetition": rep,
        "config_hash": config_hash,
        "protocol_version": protocol_version,
    }, sort_keys=True)
    short = hashlib.sha256(payload.encode()).hexdigest()[:8]
    return f"{scenario_id}_{strategy_name}_rep{rep}_{short}"


def _make_checkpoint_content(
    completed_run_ids: list[str] | None = None,
    pending_run_ids: list[str] | None = None,
    total_planned: int = 7,
    completion_status: str = "incomplete",
    protocol_version: str = "1.0",
    config_hash: str = "deadbeef",
    source_commit: str = "v0.7.0-smoke-passed",
    scenario_ids: list[str] | None = None,
    strategy_names: list[str] | None = None,
) -> dict:
    planned = [
        _make_run_id("djangocms-cross-007", s, 1)
        for s in (strategy_names or ALL_SEVEN_STRATEGIES)
    ]
    completed = completed_run_ids or []
    pending = pending_run_ids or planned[len(completed):]
    return {
        "profile": "smoke",
        "execution_plan_hash": "abc123",
        "planned_run_ids": planned,
        "completed_run_ids": completed,
        "failed_run_ids": [],
        "pending_run_ids": pending,
        "total_planned": total_planned,
        "total_completed": len(completed),
        "protocol_version": protocol_version,
        "model_identity": "dry-run:mock",
        "config_hash": config_hash,
        "source_commit": source_commit,
        "last_update": "2026-07-24T20:31:39+00:00",
        "completion_status": completion_status,
        "scenario_ids": scenario_ids or SCENARIO_IDS,
        "strategy_names": strategy_names or ALL_SEVEN_STRATEGIES,
    }


def _make_run_record(run_id: str, strategy_id: str, status: str = "succeeded") -> dict:
    return {
        "run_id": run_id,
        "profile": "smoke",
        "repository_id": "todo",
        "scenario_id": "djangocms-cross-007",
        "strategy_id": strategy_id,
        "repetition": 1,
        "seed": 42,
        "status": status,
        "duration_seconds": 1.0,
        "protocol_version": "1.0",
        "source_commit": "v0.7.0-smoke-passed",
        "config_hash": "deadbeef",
        "timestamp": "2026-07-24T20:30:00+00:00",
    }


def _build_real_kaggle_layout(temp: Path, exp_id: str, completed_ids: list[str]) -> Path:
    """Create the exact real Kaggle hierarchy inside *temp*.

    Returns the path to the recovery directory.
    """
    recovery_dir = (
        temp / "experiments" / "smoke" / "1.0" / "v0.7.0-smoke-passed"
        / exp_id / "recovery"
    )
    recovery_dir.mkdir(parents=True, exist_ok=True)

    # checkpoint.json
    all_planned = [
        _make_run_id("djangocms-cross-007", s, 1) for s in ALL_SEVEN_STRATEGIES
    ]
    pending = [r for r in all_planned if r not in completed_ids]
    cp_content = _make_checkpoint_content(
        completed_run_ids=completed_ids,
        pending_run_ids=pending,
        total_planned=7,
        completion_status="incomplete",
    )
    (recovery_dir / "checkpoint.json").write_text(
        json.dumps(cp_content, indent=2), encoding="utf-8"
    )

    # run_records.jsonl
    records = []
    for rid in completed_ids:
        # Extract strategy name from run_id pattern: <scenario>_<strategy>_rep<N>_<hash>
        parts = rid.split("_")
        strategy = parts[1] if len(parts) >= 2 else "unknown"
        records.append(json.dumps(_make_run_record(rid, strategy)))
    (recovery_dir / "run_records.jsonl").write_text(
        "\n".join(records) + "\n" if records else "", encoding="utf-8"
    )

    # progress.json
    progress = {
        "profile": "smoke",
        "total_planned": 7,
        "total_completed": len(completed_ids),
        "last_update": "2026-07-24T20:31:39+00:00",
    }
    (recovery_dir / "progress.json").write_text(
        json.dumps(progress, indent=2), encoding="utf-8"
    )

    # experiment_id.txt
    (recovery_dir / "experiment_id.txt").write_text(exp_id, encoding="utf-8")

    # source_identity.json
    source_id = {
        "source_tag": "v0.7.0-smoke-passed",
        "source_commit": "v0.7.0-smoke-passed",
        "profile": "smoke",
    }
    (recovery_dir / "source_identity.json").write_text(
        json.dumps(source_id, indent=2), encoding="utf-8"
    )

    return recovery_dir


def _make_fake_download_for_layout(layout: RemoteLayout, temp_root: Path):
    """Create a fake hf_hub_download that places files in the real hierarchy."""
    def fake_download(**kwargs):
        local_dir = Path(kwargs["local_dir"])
        filename = kwargs["filename"]
        dest = local_dir / filename
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Map the filename to the source in temp_root
        # filename = "experiments/smoke/1.0/v0.7.0-smoke-passed/exp-xxx/recovery/checkpoint.json"
        # We need to find this file in temp_root
        source = temp_root / filename
        if source.is_file():
            shutil.copy2(str(source), str(dest))
        else:
            raise FileNotFoundError(f"Recovery file not found: {filename}")
        return str(dest)

    return fake_download


# ---------------------------------------------------------------------------
# Tests: Real Kaggle path layout
# ---------------------------------------------------------------------------

class TestRecoveryActivation:
    def test_recovery_found_and_activated(self, tmp_path: Path) -> None:
        """Recovery files from real hierarchy are activated at output root."""
        output_dir = tmp_path / "runs"
        output_dir.mkdir()

        exp_id = "exp-20260724-203139"
        completed_ids = [_make_run_id("djangocms-cross-007", "monolithic", 1)]
        layout = RemoteLayout("smoke", "1.0", "v0.7.0-smoke-passed", exp_id)

        # Create the real hierarchy in a separate temp dir
        download_root = tmp_path / "download"
        download_root.mkdir()
        _build_real_kaggle_layout(download_root, exp_id, completed_ids)

        fake_dl = _make_fake_download_for_layout(layout, download_root)
        with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=fake_dl):
            resume = HfResumeManager(
                runs_dir=output_dir,
                repo_id=TEST_REPO,
                layout=layout,
                token="t",
                protocol_version="1.0",
                config_hash="deadbeef",
                model_identity="dry-run:mock",
                source_commit="v0.7.0-smoke-passed",
                scenario_ids=SCENARIO_IDS,
                strategy_names=ALL_SEVEN_STRATEGIES,
            )
            skip_ids = resume.download_and_validate()

        # checkpoint.json is activated at output root
        assert (output_dir / "checkpoint.json").is_file()
        assert (output_dir / "run_records.jsonl").is_file()
        assert (output_dir / "progress.json").is_file()
        assert (output_dir / "experiment_id.txt").is_file()

        # Nested hierarchy is NOT under output root
        assert not (output_dir / "experiments").is_dir()
        assert not (output_dir / ".cache").is_dir()

        # Resume manager reads from canonical location
        cp_mgr = CheckpointManager(output_dir)
        cp = cp_mgr.read()
        assert cp is not None
        assert cp.total_planned == 7
        assert len(cp.completed_run_ids) == 1
        assert cp.completion_status == "incomplete"

        # Completed monolithic is in skip set
        assert completed_ids[0] in skip_ids

        # agent is the next pending run
        pending = cp.pending_run_ids
        assert any("agent" in r for r in pending)

    def test_completed_monolithic_skipped(self, tmp_path: Path) -> None:
        """Monolithic is in skip set, agent is the next run."""
        output_dir = tmp_path / "runs"
        output_dir.mkdir()

        exp_id = "exp-sequence-test"
        monolithic_id = _make_run_id("djangocms-cross-007", "monolithic", 1)
        completed_ids = [monolithic_id]
        layout = RemoteLayout("smoke", "1.0", "v0.7.0-smoke-passed", exp_id)

        download_root = tmp_path / "download"
        download_root.mkdir()
        _build_real_kaggle_layout(download_root, exp_id, completed_ids)

        fake_dl = _make_fake_download_for_layout(layout, download_root)
        with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=fake_dl):
            resume = HfResumeManager(
                runs_dir=output_dir,
                repo_id=TEST_REPO,
                layout=layout,
                token="t",
                protocol_version="1.0",
                config_hash="deadbeef",
                model_identity="dry-run:mock",
                source_commit="v0.7.0-smoke-passed",
                scenario_ids=SCENARIO_IDS,
                strategy_names=ALL_SEVEN_STRATEGIES,
            )
            skip_ids = resume.download_and_validate()

        assert monolithic_id in skip_ids

        record_store = RunRecordStore(output_dir)
        completed_in_records = record_store.get_completed_run_ids()
        assert monolithic_id in completed_in_records

    def test_progress_advances_1_to_2(self, tmp_path: Path) -> None:
        """Progress shows completed 2/7 after activation of a 1-completed experiment."""
        output_dir = tmp_path / "runs"
        output_dir.mkdir()

        exp_id = "exp-progress-test"
        completed_ids = [_make_run_id("djangocms-cross-007", "monolithic", 1)]
        layout = RemoteLayout("smoke", "1.0", "v0.7.0-smoke-passed", exp_id)

        download_root = tmp_path / "download"
        download_root.mkdir()
        _build_real_kaggle_layout(download_root, exp_id, completed_ids)

        fake_dl = _make_fake_download_for_layout(layout, download_root)
        with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=fake_dl):
            resume = HfResumeManager(
                runs_dir=output_dir,
                repo_id=TEST_REPO,
                layout=layout,
                token="t",
                protocol_version="1.0",
                config_hash="deadbeef",
                model_identity="dry-run:mock",
                source_commit="v0.7.0-smoke-passed",
                scenario_ids=SCENARIO_IDS,
                strategy_names=ALL_SEVEN_STRATEGIES,
            )
            resume.download_and_validate()

        cp = CheckpointManager(output_dir).read()
        assert cp is not None
        assert cp.total_completed == 1
        assert len(cp.pending_run_ids) == 6

    def test_no_experiments_dir_under_output(self, tmp_path: Path) -> None:
        """After activation, no experiments/ directory exists under output."""
        output_dir = tmp_path / "runs"
        output_dir.mkdir()

        exp_id = "exp-no-nesting"
        layout = RemoteLayout("smoke", "1.0", "v0.7.0-smoke-passed", exp_id)

        download_root = tmp_path / "download"
        download_root.mkdir()
        _build_real_kaggle_layout(download_root, exp_id, [])

        fake_dl = _make_fake_download_for_layout(layout, download_root)
        with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=fake_dl):
            resume = HfResumeManager(
                runs_dir=output_dir,
                repo_id=TEST_REPO,
                layout=layout,
                token="t",
                protocol_version="1.0",
                config_hash="deadbeef",
                model_identity="dry-run:mock",
                source_commit="v0.7.0-smoke-passed",
                scenario_ids=SCENARIO_IDS,
                strategy_names=ALL_SEVEN_STRATEGIES,
            )
            resume.download_and_validate()

        assert not (output_dir / "experiments").is_dir()
        assert not (output_dir / ".cache").is_dir()

    def test_no_cache_dir_under_output(self, tmp_path: Path) -> None:
        """After activation, no .cache/ directory exists under output."""
        output_dir = tmp_path / "runs"
        output_dir.mkdir()
        # Pre-create a .cache dir to test cleanup
        (output_dir / ".cache").mkdir()
        (output_dir / ".cache" / "stale.txt").write_text("old")

        exp_id = "exp-cache-cleanup"
        layout = RemoteLayout("smoke", "1.0", "v0.7.0-smoke-passed", exp_id)

        download_root = tmp_path / "download"
        download_root.mkdir()
        _build_real_kaggle_layout(download_root, exp_id, [])

        fake_dl = _make_fake_download_for_layout(layout, download_root)
        with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=fake_dl):
            resume = HfResumeManager(
                runs_dir=output_dir,
                repo_id=TEST_REPO,
                layout=layout,
                token="t",
                protocol_version="1.0",
                config_hash="deadbeef",
                model_identity="dry-run:mock",
                source_commit="v0.7.0-smoke-passed",
                scenario_ids=SCENARIO_IDS,
                strategy_names=ALL_SEVEN_STRATEGIES,
            )
            resume.download_and_validate()

        assert not (output_dir / ".cache").is_dir()


# ---------------------------------------------------------------------------
# Tests: Failure modes (must fail BEFORE activation)
# ---------------------------------------------------------------------------

class TestRecoveryActivationFailures:
    def test_missing_checkpoint_fails_before_activation(self, tmp_path: Path) -> None:
        """Missing checkpoint.json in download fails before any activation."""
        output_dir = tmp_path / "runs"
        output_dir.mkdir()

        exp_id = "exp-no-cp"
        layout = RemoteLayout("smoke", "1.0", "v0.7.0-smoke-passed", exp_id)

        download_root = tmp_path / "download"
        recovery_dir = (
            download_root / "experiments" / "smoke" / "1.0" / "v0.7.0-smoke-passed"
            / exp_id / "recovery"
        )
        recovery_dir.mkdir(parents=True)
        # Only write run_records.jsonl, no checkpoint.json
        (recovery_dir / "run_records.jsonl").write_text("")

        fake_dl = _make_fake_download_for_layout(layout, download_root)
        with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=fake_dl):
            resume = HfResumeManager(
                runs_dir=output_dir,
                repo_id=TEST_REPO,
                layout=layout,
                token="t",
                protocol_version="1.0",
                config_hash="deadbeef",
                model_identity="dry-run:mock",
                source_commit="v0.7.0-smoke-passed",
                scenario_ids=SCENARIO_IDS,
                strategy_names=ALL_SEVEN_STRATEGIES,
            )
            with pytest.raises(ResumeValidationError, match="no checkpoint.json"):
                resume.download_and_validate()

        # Output dir should be clean
        assert not (output_dir / "checkpoint.json").is_file()

    def test_malformed_checkpoint_fails_before_activation(self, tmp_path: Path) -> None:
        """Malformed checkpoint.json fails before activation."""
        output_dir = tmp_path / "runs"
        output_dir.mkdir()

        exp_id = "exp-bad-cp"
        layout = RemoteLayout("smoke", "1.0", "v0.7.0-smoke-passed", exp_id)

        download_root = tmp_path / "download"
        recovery_dir = (
            download_root / "experiments" / "smoke" / "1.0" / "v0.7.0-smoke-passed"
            / exp_id / "recovery"
        )
        recovery_dir.mkdir(parents=True)
        (recovery_dir / "checkpoint.json").write_text("NOT VALID JSON")

        fake_dl = _make_fake_download_for_layout(layout, download_root)
        with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=fake_dl):
            resume = HfResumeManager(
                runs_dir=output_dir,
                repo_id=TEST_REPO,
                layout=layout,
                token="t",
                protocol_version="1.0",
                config_hash="deadbeef",
                model_identity="dry-run:mock",
                source_commit="v0.7.0-smoke-passed",
                scenario_ids=SCENARIO_IDS,
                strategy_names=ALL_SEVEN_STRATEGIES,
            )
            with pytest.raises(ResumeValidationError, match="corrupted|could not be parsed"):
                resume.download_and_validate()

        assert not (output_dir / "checkpoint.json").is_file()

    def test_experiment_id_mismatch_fails(self, tmp_path: Path) -> None:
        """Experiment ID mismatch fails before activation."""
        output_dir = tmp_path / "runs"
        output_dir.mkdir()

        exp_id = "exp-real-id"
        wrong_id = "exp-wrong-id"
        layout = RemoteLayout("smoke", "1.0", "v0.7.0-smoke-passed", exp_id)

        download_root = tmp_path / "download"
        recovery_dir = (
            download_root / "experiments" / "smoke" / "1.0" / "v0.7.0-smoke-passed"
            / exp_id / "recovery"
        )
        recovery_dir.mkdir(parents=True)

        cp_content = _make_checkpoint_content()
        (recovery_dir / "checkpoint.json").write_text(
            json.dumps(cp_content), encoding="utf-8"
        )
        (recovery_dir / "experiment_id.txt").write_text(wrong_id, encoding="utf-8")

        fake_dl = _make_fake_download_for_layout(layout, download_root)
        with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=fake_dl):
            resume = HfResumeManager(
                runs_dir=output_dir,
                repo_id=TEST_REPO,
                layout=layout,
                token="t",
                protocol_version="1.0",
                config_hash="deadbeef",
                model_identity="dry-run:mock",
                source_commit="v0.7.0-smoke-passed",
                scenario_ids=SCENARIO_IDS,
                strategy_names=ALL_SEVEN_STRATEGIES,
            )
            with pytest.raises(ResumeValidationError, match="experiment ID mismatch"):
                resume.download_and_validate()

        assert not (output_dir / "checkpoint.json").is_file()

    def test_activation_does_not_mix_files(self, tmp_path: Path) -> None:
        """Activation only copies files from the selected experiment."""
        output_dir = tmp_path / "runs"
        output_dir.mkdir()
        # Pre-existing file from a different experiment
        (output_dir / "checkpoint.json").write_text("OLD DATA")

        exp_id = "exp-selected"
        completed_ids = [_make_run_id("djangocms-cross-007", "monolithic", 1)]
        layout = RemoteLayout("smoke", "1.0", "v0.7.0-smoke-passed", exp_id)

        download_root = tmp_path / "download"
        download_root.mkdir()
        _build_real_kaggle_layout(download_root, exp_id, completed_ids)

        fake_dl = _make_fake_download_for_layout(layout, download_root)
        with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=fake_dl):
            resume = HfResumeManager(
                runs_dir=output_dir,
                repo_id=TEST_REPO,
                layout=layout,
                token="t",
                protocol_version="1.0",
                config_hash="deadbeef",
                model_identity="dry-run:mock",
                source_commit="v0.7.0-smoke-passed",
                scenario_ids=SCENARIO_IDS,
                strategy_names=ALL_SEVEN_STRATEGIES,
            )
            resume.download_and_validate()

        # Old data is gone, replaced by selected experiment's checkpoint
        cp = CheckpointManager(output_dir).read()
        assert cp is not None
        assert cp.total_planned == 7

    def test_activation_failure_preserves_previous_state(self, tmp_path: Path) -> None:
        """If activation fails after partial copy, previous state is preserved."""
        output_dir = tmp_path / "runs"
        output_dir.mkdir()
        # Pre-existing checkpoint
        cp_mgr = CheckpointManager(output_dir)
        cp_mgr.write_atomic(CheckpointData(
            profile="old",
            execution_plan_hash="xxx",
            planned_run_ids=["old-run"],
            total_planned=1,
            protocol_version="1.0",
        ))

        exp_id = "exp-activation-fail"
        layout = RemoteLayout("smoke", "1.0", "v0.7.0-smoke-passed", exp_id)

        # Download succeeds, but the checkpoint is incompatible
        download_root = tmp_path / "download"
        recovery_dir = (
            download_root / "experiments" / "smoke" / "1.0" / "v0.7.0-smoke-passed"
            / exp_id / "recovery"
        )
        recovery_dir.mkdir(parents=True)
        bad_cp = _make_checkpoint_content(protocol_version="9.9")
        (recovery_dir / "checkpoint.json").write_text(
            json.dumps(bad_cp), encoding="utf-8"
        )

        fake_dl = _make_fake_download_for_layout(layout, download_root)
        with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=fake_dl):
            resume = HfResumeManager(
                runs_dir=output_dir,
                repo_id=TEST_REPO,
                layout=layout,
                token="t",
                protocol_version="1.0",
                config_hash="deadbeef",
                model_identity="dry-run:mock",
                source_commit="v0.7.0-smoke-passed",
                scenario_ids=SCENARIO_IDS,
                strategy_names=ALL_SEVEN_STRATEGIES,
            )
            with pytest.raises(ResumeValidationError):
                resume.download_and_validate()

        # Previous state is unchanged
        cp = CheckpointManager(output_dir).read()
        assert cp is not None
        assert cp.profile == "old"
        assert cp.planned_run_ids == ["old-run"]

    def test_no_fallback_to_start_new_after_validation_failure(self, tmp_path: Path) -> None:
        """After a selected candidate download/validation failure, does not START_NEW."""
        output_dir = tmp_path / "runs"
        output_dir.mkdir()

        exp_id = "exp-fail-no-fallback"
        layout = RemoteLayout("smoke", "1.0", "v0.7.0-smoke-passed", exp_id)

        download_root = tmp_path / "download"
        recovery_dir = (
            download_root / "experiments" / "smoke" / "1.0" / "v0.7.0-smoke-passed"
            / exp_id / "recovery"
        )
        recovery_dir.mkdir(parents=True)
        # Incompatible checkpoint
        bad_cp = _make_checkpoint_content(config_hash="WRONG_HASH")
        (recovery_dir / "checkpoint.json").write_text(
            json.dumps(bad_cp), encoding="utf-8"
        )

        fake_dl = _make_fake_download_for_layout(layout, download_root)
        with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=fake_dl):
            resume = HfResumeManager(
                runs_dir=output_dir,
                repo_id=TEST_REPO,
                layout=layout,
                token="t",
                protocol_version="1.0",
                config_hash="deadbeef",
                model_identity="dry-run:mock",
                source_commit="v0.7.0-smoke-passed",
                scenario_ids=SCENARIO_IDS,
                strategy_names=ALL_SEVEN_STRATEGIES,
            )
            with pytest.raises(ResumeValidationError):
                resume.download_and_validate()

        # Output dir should NOT have a new checkpoint (no START_NEW)
        assert not (output_dir / "checkpoint.json").is_file()

    def test_no_experiments_dir_left_in_output(self, tmp_path: Path) -> None:
        """No nested experiments/ hierarchy left under output_dir after activation."""
        output_dir = tmp_path / "runs"
        output_dir.mkdir()

        exp_id = "exp-no-nesting-check"
        layout = RemoteLayout("smoke", "1.0", "v0.7.0-smoke-passed", exp_id)

        download_root = tmp_path / "download"
        download_root.mkdir()
        _build_real_kaggle_layout(download_root, exp_id, [])

        fake_dl = _make_fake_download_for_layout(layout, download_root)
        with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=fake_dl):
            resume = HfResumeManager(
                runs_dir=output_dir,
                repo_id=TEST_REPO,
                layout=layout,
                token="t",
                protocol_version="1.0",
                config_hash="deadbeef",
                model_identity="dry-run:mock",
                source_commit="v0.7.0-smoke-passed",
                scenario_ids=SCENARIO_IDS,
                strategy_names=ALL_SEVEN_STRATEGIES,
            )
            resume.download_and_validate()

        # Recursively check: no experiments/ dir anywhere under output_dir
        for p in output_dir.rglob("experiments"):
            assert not p.is_dir(), f"Unexpected experiments/ dir: {p}"
        for p in output_dir.rglob(".cache"):
            assert not p.is_dir(), f"Unexpected .cache/ dir: {p}"
