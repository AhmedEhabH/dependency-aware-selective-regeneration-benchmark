from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from benchmark.execution.scenario_evaluator import run_scenario_evaluator
from tests.support.evaluator_fixture_workspaces import (
    _BASELINE_REPO,
    build_todo_smoke_001_workspace,
    build_todo_smoke_002_workspace,
    build_todo_smoke_003_workspace,
)

_SMOKE_001_CHECKS = (
    "task_priority_enum",
    "task_priority_field",
    "task_priority_default",
    "task_priority_valid_values",
    "task_serializer_priority",
    "task_priority_invalid_rejected",
    "task_priority_filter",
    "task_unfiltered_list",
    "baseline_task_fields",
    "project_and_tag_regression",
)

_SMOKE_002_CHECKS = (
    "soft_delete_retains_row",
    "soft_delete_sets_timestamp",
    "default_manager_excludes_deleted",
    "normal_list_excludes_deleted",
    "deleted_detail_is_404",
    "deleted_action_lists_deleted",
    "restore_action_restores",
    "soft_deleted_data_preserved",
    "project_and_tag_regression",
)

_SMOKE_003_CHECKS = (
    "project_owner_field",
    "project_creator_becomes_owner",
    "project_owner_read_only",
    "project_owner_can_write",
    "project_non_owner_forbidden",
    "task_create_uses_project_owner",
    "task_update_uses_project_owner",
    "task_delete_uses_project_owner",
    "authenticated_reads_unrestricted",
    "tag_permissions_unchanged",
)

_NEGATIVE_EXPECTED_CHECKS = {
    "todo-smoke-001": {
        "wrong_default": "task_priority_default",
        "missing_filter": "task_priority_filter",
        "invalid_serializer_choice": "task_serializer_priority",
    },
    "todo-smoke-002": {
        "hard_delete": "soft_delete_retains_row",
        "deleted_visible_in_normal_list": "default_manager_excludes_deleted",
        "restore_keeps_timestamp": "restore_action_restores",
    },
    "todo-smoke-003": {
        "task_owner_authority": "task_update_uses_project_owner",
        "project_non_owner_write_allowed": "project_non_owner_forbidden",
        "project_owner_writable": "project_owner_read_only",
    },
}


def _baseline_hashes():
    hashes = {}
    for p in _BASELINE_REPO.rglob("*"):
        if p.is_file():
            rel = str(p.relative_to(_BASELINE_REPO).as_posix())
            import hashlib
            hashes[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return hashes


class _EvaluatorHelper:
    def __init__(self, scenario_id, asset_path, expected_checks, tmp_path):
        self.scenario_id = scenario_id
        self.asset_path = asset_path
        self.expected_checks = expected_checks
        self.tmp_path = tmp_path
        self.build_fn = {
            "todo-smoke-001": build_todo_smoke_001_workspace,
            "todo-smoke-002": build_todo_smoke_002_workspace,
            "todo-smoke-003": build_todo_smoke_003_workspace,
        }[scenario_id]

    def run(self, variant="correct"):
        workspace = self.build_fn(self.tmp_path / f"ws_{variant}", variant=variant)
        cpr = self.tmp_path / f"project_{variant}"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        asset_src = Path(__file__).resolve().parent.parent / "evaluator_assets" / self.asset_path
        dest = cpr / "tests" / "evaluator_assets" / self.asset_path
        dest.write_bytes(asset_src.read_bytes())
        return run_scenario_evaluator(
            str(cpr),
            f"tests/evaluator_assets/{self.asset_path}",
            str(workspace),
            python_executable=sys.executable,
            timeout=120,
        )


class TestTodoSmoke001Evaluator:
    HELPER_CLS = _EvaluatorHelper
    SCENARIO_ID = "todo-smoke-001"
    ASSET = "todo_smoke_001_checks.py"
    EXPECTED_CHECKS = _SMOKE_001_CHECKS

    @pytest.fixture
    def helper(self, tmp_path):
        return _EvaluatorHelper(self.SCENARIO_ID, self.ASSET, self.EXPECTED_CHECKS, tmp_path)

    def test_correct_passes(self, helper):
        result = helper.run("correct")
        assert result.passed, f"correct variant failed: {result.error}"
        assert result.exit_code == 0
        assert result.checks == self.EXPECTED_CHECKS, f"check mismatch: {result.checks}"

    def test_wrong_default_fails_expected_check(self, helper):
        result = helper.run("wrong_default")
        assert not result.passed, "wrong_default should fail"
        assert _NEGATIVE_EXPECTED_CHECKS["todo-smoke-001"]["wrong_default"] in result.error

    def test_missing_filter_fails_expected_check(self, helper):
        result = helper.run("missing_filter")
        assert not result.passed, "missing_filter should fail"
        assert _NEGATIVE_EXPECTED_CHECKS["todo-smoke-001"]["missing_filter"] in result.error

    def test_invalid_serializer_choice_fails_expected_check(self, helper):
        result = helper.run("invalid_serializer_choice")
        assert not result.passed, "invalid_serializer_choice should fail"
        assert _NEGATIVE_EXPECTED_CHECKS["todo-smoke-001"]["invalid_serializer_choice"] in result.error


class TestTodoSmoke002Evaluator:
    SCENARIO_ID = "todo-smoke-002"
    ASSET = "todo_smoke_002_checks.py"
    EXPECTED_CHECKS = _SMOKE_002_CHECKS

    @pytest.fixture
    def helper(self, tmp_path):
        return _EvaluatorHelper(self.SCENARIO_ID, self.ASSET, self.EXPECTED_CHECKS, tmp_path)

    def test_correct_passes(self, helper):
        result = helper.run("correct")
        assert result.passed, f"correct variant failed: {result.error}"
        assert result.exit_code == 0
        assert result.checks == self.EXPECTED_CHECKS, f"check mismatch: {result.checks}"

    def test_hard_delete_fails_expected_check(self, helper):
        result = helper.run("hard_delete")
        assert not result.passed, "hard_delete should fail"
        assert _NEGATIVE_EXPECTED_CHECKS["todo-smoke-002"]["hard_delete"] in result.error

    def test_deleted_visible_in_normal_list_fails_expected_check(self, helper):
        result = helper.run("deleted_visible_in_normal_list")
        assert not result.passed, "deleted_visible should fail"
        assert _NEGATIVE_EXPECTED_CHECKS["todo-smoke-002"]["deleted_visible_in_normal_list"] in result.error

    def test_restore_keeps_timestamp_fails_expected_check(self, helper):
        result = helper.run("restore_keeps_timestamp")
        assert not result.passed, "restore_keeps_timestamp should fail"
        assert _NEGATIVE_EXPECTED_CHECKS["todo-smoke-002"]["restore_keeps_timestamp"] in result.error


class TestTodoSmoke003Evaluator:
    SCENARIO_ID = "todo-smoke-003"
    ASSET = "todo_smoke_003_checks.py"
    EXPECTED_CHECKS = _SMOKE_003_CHECKS

    @pytest.fixture
    def helper(self, tmp_path):
        return _EvaluatorHelper(self.SCENARIO_ID, self.ASSET, self.EXPECTED_CHECKS, tmp_path)

    def test_correct_passes(self, helper):
        result = helper.run("correct")
        assert result.passed, f"correct variant failed: {result.error}"
        assert result.exit_code == 0
        assert result.checks == self.EXPECTED_CHECKS, f"check mismatch: {result.checks}"

    def test_task_owner_authority_fails_expected_check(self, helper):
        result = helper.run("task_owner_authority")
        assert not result.passed, "task_owner_authority should fail"
        assert _NEGATIVE_EXPECTED_CHECKS["todo-smoke-003"]["task_owner_authority"] in result.error

    def test_project_non_owner_write_allowed_fails_expected_check(self, helper):
        result = helper.run("project_non_owner_write_allowed")
        assert not result.passed, "non_owner_write should fail"
        assert _NEGATIVE_EXPECTED_CHECKS["todo-smoke-003"]["project_non_owner_write_allowed"] in result.error

    def test_project_owner_writable_fails_expected_check(self, helper):
        result = helper.run("project_owner_writable")
        assert not result.passed, "project_owner_writable should fail"
        assert _NEGATIVE_EXPECTED_CHECKS["todo-smoke-003"]["project_owner_writable"] in result.error


class TestEvaluatorIntegrity:
    def test_pytest_not_collect_evaluator_scripts(self):
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/evaluator_assets", "--collect-only", "-q"],
            cwd=Path(__file__).resolve().parent.parent.parent,
            capture_output=True, text=True, timeout=30,
        )
        assert "no tests collected" in result.stderr.lower() or "no tests collected" in result.stdout.lower()

    def test_baseline_hashes_preserved(self, tmp_path):
        before = _baseline_hashes()
        ws = build_todo_smoke_001_workspace(tmp_path / "ws_hash", variant="correct")
        cpr = tmp_path / "project_hash"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        asset_src = Path(__file__).resolve().parent.parent / "evaluator_assets" / "todo_smoke_001_checks.py"
        dest = cpr / "tests" / "evaluator_assets" / "todo_smoke_001_checks.py"
        dest.write_bytes(asset_src.read_bytes())
        run_scenario_evaluator(
            str(cpr),
            "tests/evaluator_assets/todo_smoke_001_checks.py",
            str(ws),
            python_executable=sys.executable,
            timeout=120,
        )
        after = _baseline_hashes()
        assert before == after, "Baseline hashes changed after fixture/evaluator run"

    def test_workspace_migration_integrity(self, tmp_path):
        import hashlib
        ws = build_todo_smoke_001_workspace(tmp_path / "ws_mig", variant="correct")
        mig_dir = ws / "todo" / "migrations"
        h = "61273ccb29c97b095120155ab8a74e63448b3d54bffd2e4e191c3e148f57aa88"
        h2 = "7b9a7dcb12867ca57d844da77b1ea948eacdf65ba2c34794ef33b3c2844ea73d"
        h3 = "6d22650fefe167af42bf3b7e6473073d159eecfb0583e5c899ddd40df5b8b6fa"
        for name, expected_hash in [
            ("0001_initial.py", h),
            ("0002_task_owner.py", h2),
            ("0003_alter_project_options_alter_tag_options_and_more.py", h3),
        ]:
            mig_file = mig_dir / name
            assert mig_file.exists(), f"Baseline migration {name} missing from workspace"
            actual_hash = hashlib.sha256(mig_file.read_bytes()).hexdigest()
            assert actual_hash == expected_hash, f"Hash mismatch for {name}"
        numbered = [p for p in mig_dir.iterdir() if p.suffix == ".py" and p.name != "__init__.py"]
        assert len(numbered) == 4, f"Expected 4 migrations (3 baseline + 1 new), got {len(numbered)}"

    def test_workspace_migration_integrity_002(self, tmp_path):
        import hashlib
        ws = build_todo_smoke_002_workspace(tmp_path / "ws_mig2", variant="correct")
        mig_dir = ws / "todo" / "migrations"
        h = "61273ccb29c97b095120155ab8a74e63448b3d54bffd2e4e191c3e148f57aa88"
        h2 = "7b9a7dcb12867ca57d844da77b1ea948eacdf65ba2c34794ef33b3c2844ea73d"
        h3 = "6d22650fefe167af42bf3b7e6473073d159eecfb0583e5c899ddd40df5b8b6fa"
        for name, expected_hash in [
            ("0001_initial.py", h),
            ("0002_task_owner.py", h2),
            ("0003_alter_project_options_alter_tag_options_and_more.py", h3),
        ]:
            mig_file = mig_dir / name
            assert mig_file.exists(), f"Baseline migration {name} missing from workspace"
            actual_hash = hashlib.sha256(mig_file.read_bytes()).hexdigest()
            assert actual_hash == expected_hash, f"Hash mismatch for {name}"
        numbered = [p for p in mig_dir.iterdir() if p.suffix == ".py" and p.name != "__init__.py"]
        assert len(numbered) == 4, f"Expected 4 migrations (3 baseline + 1 new), got {len(numbered)}"

    def test_workspace_migration_integrity_003(self, tmp_path):
        import hashlib
        ws = build_todo_smoke_003_workspace(tmp_path / "ws_mig3", variant="correct")
        mig_dir = ws / "todo" / "migrations"
        h = "61273ccb29c97b095120155ab8a74e63448b3d54bffd2e4e191c3e148f57aa88"
        h2 = "7b9a7dcb12867ca57d844da77b1ea948eacdf65ba2c34794ef33b3c2844ea73d"
        h3 = "6d22650fefe167af42bf3b7e6473073d159eecfb0583e5c899ddd40df5b8b6fa"
        for name, expected_hash in [
            ("0001_initial.py", h),
            ("0002_task_owner.py", h2),
            ("0003_alter_project_options_alter_tag_options_and_more.py", h3),
        ]:
            mig_file = mig_dir / name
            assert mig_file.exists(), f"Baseline migration {name} missing from workspace"
            actual_hash = hashlib.sha256(mig_file.read_bytes()).hexdigest()
            assert actual_hash == expected_hash, f"Hash mismatch for {name}"
        numbered = [p for p in mig_dir.iterdir() if p.suffix == ".py" and p.name != "__init__.py"]
        assert len(numbered) == 4, f"Expected 4 migrations (3 baseline + 1 new), got {len(numbered)}"

    def test_source_isolation(self, tmp_path):
        import hashlib
        evaluator_path = Path(__file__).resolve().parent.parent / "evaluator_assets" / "todo_smoke_001_checks.py"
        before_hash = hashlib.sha256(evaluator_path.read_bytes()).hexdigest()
        ws = build_todo_smoke_001_workspace(tmp_path / "ws_src", variant="correct")
        cpr = tmp_path / "project_src"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        dest = cpr / "tests" / "evaluator_assets" / "todo_smoke_001_checks.py"
        dest.write_bytes(evaluator_path.read_bytes())
        run_scenario_evaluator(
            str(cpr),
            "tests/evaluator_assets/todo_smoke_001_checks.py",
            str(ws),
            python_executable=sys.executable,
            timeout=120,
        )
        assert not (ws / "tests" / "evaluator_assets").exists(), "evaluator assets leaked into workspace"
        after_hash = hashlib.sha256(evaluator_path.read_bytes()).hexdigest()
        assert before_hash == after_hash, "canonical evaluator hash changed"

    def test_evaluator_stdout_is_exactly_one_json_object(self, tmp_path):
        ws = build_todo_smoke_001_workspace(tmp_path / "ws_json", variant="correct")
        cpr = tmp_path / "project_json"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        asset_src = Path(__file__).resolve().parent.parent / "evaluator_assets" / "todo_smoke_001_checks.py"
        dest = cpr / "tests" / "evaluator_assets" / "todo_smoke_001_checks.py"
        dest.write_bytes(asset_src.read_bytes())
        result = run_scenario_evaluator(
            str(cpr),
            "tests/evaluator_assets/todo_smoke_001_checks.py",
            str(ws),
            python_executable=sys.executable,
            timeout=120,
        )
        parsed = json.loads(result.stdout.strip())
        assert isinstance(parsed, dict)
        assert "passed" in parsed
        assert "checks" in parsed
        assert "error" in parsed

    def test_source_not_copied_into_workspace(self, tmp_path):
        ws = build_todo_smoke_001_workspace(tmp_path / "ws_source", variant="correct")
        cpr = tmp_path / "project_source"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        asset_src = Path(__file__).resolve().parent.parent / "evaluator_assets" / "todo_smoke_001_checks.py"
        dest = cpr / "tests" / "evaluator_assets" / "todo_smoke_001_checks.py"
        dest.write_bytes(asset_src.read_bytes())
        run_scenario_evaluator(
            str(cpr),
            "tests/evaluator_assets/todo_smoke_001_checks.py",
            str(ws),
            python_executable=sys.executable,
            timeout=120,
        )
        assert not (ws / "scenario_evaluator.py").exists()
