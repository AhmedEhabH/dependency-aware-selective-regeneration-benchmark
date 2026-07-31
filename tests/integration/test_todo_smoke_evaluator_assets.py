from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from benchmark.execution.scenario_evaluator import run_scenario_evaluator
from tests.support.evaluator_fixture_workspaces import (
    _BASELINE_REPO,
    _assert_workspace_has_no_evaluator_assets,
    _get_sources_for_variant,
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

_ALL_SCENARIO_VARIANTS = [
    ("todo-smoke-001", "correct"),
    ("todo-smoke-001", "wrong_default"),
    ("todo-smoke-001", "missing_filter"),
    ("todo-smoke-001", "invalid_serializer_choice"),
    ("todo-smoke-002", "correct"),
    ("todo-smoke-002", "hard_delete"),
    ("todo-smoke-002", "deleted_visible_in_normal_list"),
    ("todo-smoke-002", "restore_keeps_timestamp"),
    ("todo-smoke-003", "correct"),
    ("todo-smoke-003", "task_owner_authority"),
    ("todo-smoke-003", "project_non_owner_write_allowed"),
    ("todo-smoke-003", "project_owner_writable"),
]


def _baseline_hashes():
    hashes = {}
    for p in _BASELINE_REPO.rglob("*"):
        if p.is_file():
            rel = str(p.relative_to(_BASELINE_REPO).as_posix())
            hashes[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return hashes


def _baseline_migration_hashes():
    mig_dir = _BASELINE_REPO / "todo" / "migrations"
    hashes = {}
    for p in mig_dir.iterdir():
        if p.suffix == ".py" and p.name != "__init__.py":
            hashes[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    return hashes


def _assert_migration_integrity(workspace: Path) -> None:
    mig_dir = workspace / "todo" / "migrations"
    assert mig_dir.exists(), "migrations directory missing from workspace"
    baseline_hashes = _baseline_migration_hashes()
    for name, expected_hash in baseline_hashes.items():
        mig_file = mig_dir / name
        assert mig_file.exists(), f"Baseline migration {name} missing from workspace"
        actual_hash = hashlib.sha256(mig_file.read_bytes()).hexdigest()
        assert actual_hash == expected_hash, f"Hash mismatch for baseline migration {name}"
    numbered = [p for p in mig_dir.iterdir() if p.suffix == ".py" and p.name != "__init__.py"]
    assert len(numbered) == len(baseline_hashes) + 1, (
        f"Expected {len(baseline_hashes) + 1} migrations, got {len(numbered)}"
    )


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
        _assert_migration_integrity(workspace)
        _assert_workspace_has_no_evaluator_assets(workspace)
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
        assert not result.error.startswith("ModuleNotFoundError")
        assert not result.error.startswith("RuntimeError")

    def test_missing_filter_fails_expected_check(self, helper):
        result = helper.run("missing_filter")
        assert not result.passed, "missing_filter should fail"
        assert _NEGATIVE_EXPECTED_CHECKS["todo-smoke-001"]["missing_filter"] in result.error
        assert not result.error.startswith("ModuleNotFoundError")
        assert not result.error.startswith("RuntimeError")

    def test_invalid_serializer_choice_fails_expected_check(self, helper):
        result = helper.run("invalid_serializer_choice")
        assert not result.passed, "invalid_serializer_choice should fail"
        assert _NEGATIVE_EXPECTED_CHECKS["todo-smoke-001"]["invalid_serializer_choice"] in result.error
        assert not result.error.startswith("ModuleNotFoundError")
        assert not result.error.startswith("RuntimeError")


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
        assert not result.error.startswith("ModuleNotFoundError")
        assert not result.error.startswith("RuntimeError")

    def test_deleted_visible_in_normal_list_fails_expected_check(self, helper):
        result = helper.run("deleted_visible_in_normal_list")
        assert not result.passed, "deleted_visible should fail"
        assert _NEGATIVE_EXPECTED_CHECKS["todo-smoke-002"]["deleted_visible_in_normal_list"] in result.error
        assert not result.error.startswith("ModuleNotFoundError")
        assert not result.error.startswith("RuntimeError")

    def test_restore_keeps_timestamp_fails_expected_check(self, helper):
        result = helper.run("restore_keeps_timestamp")
        assert not result.passed, "restore_keeps_timestamp should fail"
        assert _NEGATIVE_EXPECTED_CHECKS["todo-smoke-002"]["restore_keeps_timestamp"] in result.error
        assert not result.error.startswith("ModuleNotFoundError")
        assert not result.error.startswith("RuntimeError")


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
        assert not result.error.startswith("ModuleNotFoundError")
        assert not result.error.startswith("RuntimeError")

    def test_project_non_owner_write_allowed_fails_expected_check(self, helper):
        result = helper.run("project_non_owner_write_allowed")
        assert not result.passed, "non_owner_write should fail"
        assert _NEGATIVE_EXPECTED_CHECKS["todo-smoke-003"]["project_non_owner_write_allowed"] in result.error
        assert not result.error.startswith("ModuleNotFoundError")
        assert not result.error.startswith("RuntimeError")

    def test_project_owner_writable_fails_expected_check(self, helper):
        result = helper.run("project_owner_writable")
        assert not result.passed, "project_owner_writable should fail"
        assert _NEGATIVE_EXPECTED_CHECKS["todo-smoke-003"]["project_owner_writable"] in result.error
        assert not result.error.startswith("ModuleNotFoundError")
        assert not result.error.startswith("RuntimeError")


class TestCorrectFixtureBaselineCompatibility:
    """R5-BASELINE-CONTRACT-001 gate: correct fixtures must keep the baseline
    suite green while producing only the frozen expected source changes."""

    EXPECTED_CHANGED_SOURCES = {
        "todo-smoke-001": {"todo/models.py", "todo/serializers.py", "todo/views.py"},
        "todo-smoke-002": {"todo/models.py", "todo/views.py"},
        "todo-smoke-003": {"todo/models.py", "todo/serializers.py", "todo/permissions.py", "todo/views.py"},
    }

    EDITABLE_PATHS = (
        "todo/models.py",
        "todo/serializers.py",
        "todo/views.py",
        "todo/permissions.py",
        "todo/urls.py",
    )

    @pytest.mark.parametrize(
        "scenario_id,build_fn,asset_name",
        [
            ("todo-smoke-001", build_todo_smoke_001_workspace, "todo_smoke_001_checks.py"),
            ("todo-smoke-002", build_todo_smoke_002_workspace, "todo_smoke_002_checks.py"),
            ("todo-smoke-003", build_todo_smoke_003_workspace, "todo_smoke_003_checks.py"),
        ],
    )
    def test_correct_fixture_passes_baseline_and_evaluator(self, tmp_path, scenario_id, build_fn, asset_name):
        workspace = build_fn(tmp_path / f"ws_{scenario_id}", variant="correct")
        _assert_migration_integrity(workspace)
        _assert_workspace_has_no_evaluator_assets(workspace)

        baseline_cmd = subprocess.run(
            [sys.executable, "manage.py", "test", "todo", "--verbosity", "0"],
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=300,
        )
        assert baseline_cmd.returncode == 0, (
            f"baseline suite failed for {scenario_id}\n"
            f"stdout:\n{baseline_cmd.stdout}\nstderr:\n{baseline_cmd.stderr}"
        )

        cpr = tmp_path / f"project_{scenario_id}"
        cpr.mkdir()
        (cpr / "tests").mkdir()
        (cpr / "tests" / "evaluator_assets").mkdir()
        asset_src = Path(__file__).resolve().parent.parent / "evaluator_assets" / asset_name
        dest = cpr / "tests" / "evaluator_assets" / asset_name
        dest.write_bytes(asset_src.read_bytes())
        evaluator_result = run_scenario_evaluator(
            str(cpr),
            f"tests/evaluator_assets/{asset_name}",
            str(workspace),
            python_executable=sys.executable,
            timeout=120,
        )
        assert evaluator_result.passed, f"evaluator failed for {scenario_id}: {evaluator_result.error}"

        changed = {
            rel
            for rel in self.EDITABLE_PATHS
            if (workspace / rel).read_bytes() != (_BASELINE_REPO / rel).read_bytes()
        }
        assert changed == self.EXPECTED_CHANGED_SOURCES[scenario_id], (
            f"changed source paths mismatch for {scenario_id}: {sorted(changed)}"
        )

        for rel in _baseline_hashes():
            if rel.startswith("todo/tests/"):
                assert (workspace / rel).read_bytes() == (_BASELINE_REPO / rel).read_bytes(), (
                    f"baseline test file changed in {scenario_id} workspace: {rel}"
                )

        assert not (workspace / "tests" / "evaluator_assets").exists()


class TestNegativeSourceDiff:
    @pytest.mark.parametrize("scenario_id,variant", [
        (s, v) for s, v in _ALL_SCENARIO_VARIANTS if v != "correct"
    ])
    def test_negative_changes_exactly_one_source_file(self, scenario_id, variant):
        correct_sources = _get_sources_for_variant(scenario_id, "correct")
        variant_sources = _get_sources_for_variant(scenario_id, variant)
        differing = set()
        all_keys = set(correct_sources) | set(variant_sources)
        for key in all_keys:
            if correct_sources.get(key) != variant_sources.get(key):
                differing.add(key)
        assert len(differing) == 1, (
            f"Expected exactly 1 source file to differ for {scenario_id}/{variant}, "
            f"got {len(differing)}: {differing}"
        )


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

    @pytest.mark.parametrize("scenario_id,variant", _ALL_SCENARIO_VARIANTS)
    def test_all_fixtures_migration_integrity(self, tmp_path, scenario_id, variant):
        build_fn = {
            "todo-smoke-001": build_todo_smoke_001_workspace,
            "todo-smoke-002": build_todo_smoke_002_workspace,
            "todo-smoke-003": build_todo_smoke_003_workspace,
        }[scenario_id]
        ws = build_fn(tmp_path / f"ws_{scenario_id}_{variant}", variant=variant)
        _assert_migration_integrity(ws)
        _assert_workspace_has_no_evaluator_assets(ws)

    def test_source_isolation_helper_ordinary_directory(self, tmp_path):
        ws = tmp_path / "ws_helper_dir"
        ws.mkdir(parents=True)
        (ws / "tests").mkdir()
        (ws / "tests" / "evaluator_assets").mkdir()
        with pytest.raises(AssertionError):
            _assert_workspace_has_no_evaluator_assets(ws)

    def test_source_isolation_helper_ordinary_file(self, tmp_path):
        ws = tmp_path / "ws_helper_file"
        ws.mkdir(parents=True)
        (ws / "tests").mkdir()
        (ws / "tests" / "evaluator_assets").write_text("leak")
        with pytest.raises(AssertionError):
            _assert_workspace_has_no_evaluator_assets(ws)

    def test_source_isolation_helper_broken_symlink(self, tmp_path):
        ws = tmp_path / "ws_helper_broken"
        ws.mkdir(parents=True)
        (ws / "tests").mkdir()
        leaker = ws / "tests" / "evaluator_assets"
        try:
            leaker.symlink_to(tmp_path / "nonexistent_target")
        except (OSError, NotImplementedError):
            pytest.skip("symlink creation not supported")
        with pytest.raises(AssertionError):
            _assert_workspace_has_no_evaluator_assets(ws)

    def test_source_isolation_clean_workspace_passes(self, tmp_path):
        ws = tmp_path / "ws_helper_clean"
        ws.mkdir(parents=True)
        _assert_workspace_has_no_evaluator_assets(ws)

    def test_source_isolation(self, tmp_path):
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

    @pytest.mark.parametrize("asset_name", [
        "todo_smoke_001_checks.py",
        "todo_smoke_002_checks.py",
        "todo_smoke_003_checks.py",
    ])
    def test_canonical_evaluator_integrity(self, asset_name):
        evaluator_path = Path(__file__).resolve().parent.parent / "evaluator_assets" / asset_name
        metadata_path = evaluator_path.with_suffix(evaluator_path.suffix + ".sha256")
        assert metadata_path.exists(), f"Hash metadata missing for {asset_name}"
        previous = metadata_path.read_text().strip()
        assert len(previous) == 64, f"Hash metadata for {asset_name} is not a valid 64-char SHA-256"
        current_hash = hashlib.sha256(evaluator_path.read_bytes()).hexdigest()
        assert current_hash == previous, f"Canonical evaluator {asset_name} hash changed"

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


def _build_fake_django_workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "fake_django"
    ws.mkdir(parents=True)
    (ws / "manage.py").write_text("")
    (ws / "config").mkdir()
    (ws / "config" / "__init__.py").write_text("")
    (ws / "config" / "settings.py").write_text('''
INSTALLED_APPS = ["todo"]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
AUTH_USER_MODEL = "auth.User"
USE_TZ = False
''')
    (ws / "todo").mkdir()
    (ws / "todo" / "__init__.py").write_text("")
    (ws / "django").mkdir()
    (ws / "django" / "__init__.py").write_text("def setup(): pass")
    (ws / "django" / "test").mkdir()
    (ws / "django" / "test" / "__init__.py").write_text("")
    return ws


def _write_runner_py(ws: Path, setup_db_raises: bool, teardown_raises: bool) -> None:
    lines = [
        '"""Fake Django test runner for lifecycle tests."""',
        'import sys',
        '',
        '',
        'class DiscoverRunner:',
        '    def __init__(self, verbosity=0, interactive=False):',
        '        self.verbosity = verbosity',
        '        self.interactive = interactive',
        '',
        '    def setup_test_environment(self):',
        '        pass',
        '',
        '    def setup_databases(self, **kwargs):',
    ]
    if setup_db_raises:
        lines.append("        raise RuntimeError('setup db boom')")
    else:
        lines.append("        return {'default': None}")
    lines += [
        '',
        '    def teardown_databases(self, old_config, **kwargs):',
    ]
    if teardown_raises:
        lines.append("        raise RuntimeError('teardown boom')")
    else:
        lines.append("        pass")
    lines += [
        '',
        '    def teardown_test_environment(self):',
    ]
    if teardown_raises:
        lines.append("        raise RuntimeError('teardown boom')")
    else:
        lines.append("        pass")
    lines += [
        '',
        '    def run_tests(self, test_labels, **kwargs):',
        '        return 0',
        '',
    ]
    runner_path = ws / "django" / "test" / "runner.py"
    runner_path.write_text("\n".join(lines))


_LIFECYCLE_ASSETS = [
    "todo_smoke_001_checks.py",
    "todo_smoke_002_checks.py",
    "todo_smoke_003_checks.py",
]


class TestEvaluatorLifecycle:
    @pytest.mark.parametrize("asset_name", _LIFECYCLE_ASSETS)
    def test_setup_db_failure_json_output(self, tmp_path, asset_name):
        ws = _build_fake_django_workspace(tmp_path)
        _write_runner_py(ws, setup_db_raises=True, teardown_raises=False)
        asset_src = Path(__file__).resolve().parent.parent / "evaluator_assets" / asset_name
        env = {**__import__("os").environ, "PYTHONPATH": str(ws), "PYTHONDONTWRITEBYTECODE": "1"}
        proc = __import__("subprocess").run(
            [sys.executable, str(asset_src), str(ws)],
            capture_output=True, text=True, timeout=60, env=env,
        )
        assert proc.returncode == 1, f"Expected exit code 1, got {proc.returncode}"
        stdout = proc.stdout.strip()
        data = json.loads(stdout)
        assert isinstance(data, dict)
        assert data["passed"] is False
        assert isinstance(data["checks"], list)
        assert "setup db boom" in data.get("error", "")

    @pytest.mark.parametrize("asset_name", _LIFECYCLE_ASSETS)
    def test_setup_and_teardown_failure_json_output(self, tmp_path, asset_name):
        ws = _build_fake_django_workspace(tmp_path)
        _write_runner_py(ws, setup_db_raises=True, teardown_raises=True)
        asset_src = Path(__file__).resolve().parent.parent / "evaluator_assets" / asset_name
        env = {**__import__("os").environ, "PYTHONPATH": str(ws), "PYTHONDONTWRITEBYTECODE": "1"}
        proc = __import__("subprocess").run(
            [sys.executable, str(asset_src), str(ws)],
            capture_output=True, text=True, timeout=60, env=env,
        )
        assert proc.returncode == 1, f"Expected exit code 1, got {proc.returncode}"
        stdout = proc.stdout.strip()
        data = json.loads(stdout)
        assert isinstance(data, dict)
        assert data["passed"] is False
        assert "setup db boom" in data.get("error", "")
        assert "teardown_test_environment" in data.get("error", "")
        assert "teardown boom" in data.get("error", "")
