from __future__ import annotations

import json
import sys
from pathlib import Path

from benchmark.execution.scenario_evaluator import run_scenario_evaluator
from tests.support.evaluator_fixture_workspaces import (
    build_todo_smoke_001_workspace,
    build_todo_smoke_002_workspace,
    build_todo_smoke_003_workspace,
)


class TestTodoSmoke001Evaluator:
    SCENARIO_ID = "todo-smoke-001"
    ASSET = "tests/evaluator_assets/todo_smoke_001_checks.py"

    def _run(self, tmp_path, variant="correct"):
        workspace = build_todo_smoke_001_workspace(tmp_path / f"ws_{variant}", variant=variant)
        cpr = tmp_path / f"project_{variant}"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        asset_src = Path(__file__).resolve().parent.parent / "evaluator_assets" / "todo_smoke_001_checks.py"
        dest = cpr / "tests" / "evaluator_assets" / "todo_smoke_001_checks.py"
        dest.write_bytes(asset_src.read_bytes())
        return run_scenario_evaluator(
            str(cpr),
            self.ASSET,
            str(workspace),
            python_executable=sys.executable,
            timeout=120,
        )

    def test_correct_passes(self, tmp_path):
        result = self._run(tmp_path, "correct")
        assert result.passed, f"correct variant failed: {result.error}"
        assert result.exit_code == 0
        assert len(result.checks) > 0

    def test_wrong_default_fails(self, tmp_path):
        result = self._run(tmp_path, "wrong_default")
        assert not result.passed, "wrong_default should fail"

    def test_missing_filter_fails(self, tmp_path):
        result = self._run(tmp_path, "missing_filter")
        assert not result.passed, "missing_filter should fail"

    def test_invalid_serializer_choice_fails(self, tmp_path):
        result = self._run(tmp_path, "invalid_serializer_choice")
        assert not result.passed, "invalid_serializer_choice should fail"


class TestTodoSmoke002Evaluator:
    SCENARIO_ID = "todo-smoke-002"
    ASSET = "tests/evaluator_assets/todo_smoke_002_checks.py"

    def _run(self, tmp_path, variant="correct"):
        workspace = build_todo_smoke_002_workspace(tmp_path / f"ws_{variant}", variant=variant)
        cpr = tmp_path / f"project_{variant}"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        asset_src = Path(__file__).resolve().parent.parent / "evaluator_assets" / "todo_smoke_002_checks.py"
        dest = cpr / "tests" / "evaluator_assets" / "todo_smoke_002_checks.py"
        dest.write_bytes(asset_src.read_bytes())
        return run_scenario_evaluator(
            str(cpr),
            self.ASSET,
            str(workspace),
            python_executable=sys.executable,
            timeout=120,
        )

    def test_correct_passes(self, tmp_path):
        result = self._run(tmp_path, "correct")
        assert result.passed, f"correct variant failed: {result.error}"
        assert result.exit_code == 0
        assert len(result.checks) > 0

    def test_hard_delete_fails(self, tmp_path):
        result = self._run(tmp_path, "hard_delete")
        assert not result.passed, "hard_delete should fail"

    def test_deleted_visible_in_normal_list_fails(self, tmp_path):
        result = self._run(tmp_path, "deleted_visible_in_normal_list")
        assert not result.passed, "deleted_visible should fail"

    def test_restore_keeps_timestamp_fails(self, tmp_path):
        result = self._run(tmp_path, "restore_keeps_timestamp")
        assert not result.passed, "restore_keeps_timestamp should fail"


class TestTodoSmoke003Evaluator:
    SCENARIO_ID = "todo-smoke-003"
    ASSET = "tests/evaluator_assets/todo_smoke_003_checks.py"

    def _run(self, tmp_path, variant="correct"):
        workspace = build_todo_smoke_003_workspace(tmp_path / f"ws_{variant}", variant=variant)
        cpr = tmp_path / f"project_{variant}"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        asset_src = Path(__file__).resolve().parent.parent / "evaluator_assets" / "todo_smoke_003_checks.py"
        dest = cpr / "tests" / "evaluator_assets" / "todo_smoke_003_checks.py"
        dest.write_bytes(asset_src.read_bytes())
        return run_scenario_evaluator(
            str(cpr),
            self.ASSET,
            str(workspace),
            python_executable=sys.executable,
            timeout=120,
        )

    def test_correct_passes(self, tmp_path):
        result = self._run(tmp_path, "correct")
        assert result.passed, f"correct variant failed: {result.error}"
        assert result.exit_code == 0
        assert len(result.checks) > 0

    def test_task_owner_authority_fails(self, tmp_path):
        result = self._run(tmp_path, "task_owner_authority")
        assert not result.passed, "task_owner_authority should fail"

    def test_project_non_owner_write_allowed_fails(self, tmp_path):
        result = self._run(tmp_path, "project_non_owner_write_allowed")
        assert not result.passed, "non_owner_write should fail"

    def test_project_owner_writable_fails(self, tmp_path):
        result = self._run(tmp_path, "project_owner_writable")
        assert not result.passed, "project_owner_writable should fail"


class TestEvaluatorIntegrity:
    def test_pytest_not_collect_evaluator_scripts(self):
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/evaluator_assets", "--collect-only", "-q"],
            cwd=Path(__file__).resolve().parent.parent.parent,
            capture_output=True, text=True, timeout=30,
        )
        assert "no tests collected" in result.stderr.lower() or "no tests collected" in result.stdout.lower()

    def test_evaluator_stdout_is_exactly_json(self, tmp_path):
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

    def test_baseline_unchanged(self, tmp_path):
        from tests.support.evaluator_fixture_workspaces import _BASELINE_REPO
        original_files = sorted([str(p.relative_to(_BASELINE_REPO)) for p in _BASELINE_REPO.rglob("*") if p.is_file()])
        ws = build_todo_smoke_001_workspace(tmp_path / "ws_baseline", variant="correct")
        ws_files = sorted([str(p.relative_to(ws)) for p in ws.rglob("*") if p.is_file()])
        for f in original_files:
            if f.startswith("todo" + "\\") or f.startswith("todo/"):
                continue
            assert f in ws_files, f"Baseline file missing from workspace: {f}"

    def test_exactly_one_migration(self, tmp_path):
        ws = build_todo_smoke_001_workspace(tmp_path / "ws_mig", variant="correct")
        mig_dir = ws / "todo" / "migrations"
        migs = [p for p in mig_dir.iterdir() if p.suffix == ".py" and p.name != "__init__.py"]
        assert len(migs) == 1, f"Expected 1 migration, got {len(migs)}"
