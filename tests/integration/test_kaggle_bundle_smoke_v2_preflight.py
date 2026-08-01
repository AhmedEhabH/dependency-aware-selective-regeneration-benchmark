from __future__ import annotations

import ast
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from benchmark.execution.scenario_evaluator import run_scenario_evaluator
from tests.support.evaluator_fixture_workspaces import (
    _assert_workspace_has_no_evaluator_assets,
    get_correct_sources_for_scenario,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BUNDLE_ROOT = PROJECT_ROOT / "kaggle_upload"
BUNDLE_CODE = BUNDLE_ROOT / "code"
BUNDLE_DATA_TODO = BUNDLE_ROOT / "data" / "repositories" / "todo"
BUNDLE_EVALUATOR_DIR = BUNDLE_CODE / "tests" / "evaluator_assets"

EXPECTED_TODO_TEST_FILES = (
    "__init__.py",
    "test_models.py",
    "test_permissions.py",
    "test_serializers.py",
    "test_views.py",
)

EXPECTED_EVALUATOR_ASSETS = (
    "todo_smoke_001_checks.py",
    "todo_smoke_001_checks.py.sha256",
    "todo_smoke_002_checks.py",
    "todo_smoke_002_checks.py.sha256",
    "todo_smoke_003_checks.py",
    "todo_smoke_003_checks.py.sha256",
)

SMOKE_SCENARIOS = ("todo-smoke-001", "todo-smoke-002", "todo-smoke-003")


def _count_test_methods(test_dir: Path) -> int:
    count = 0
    for p in sorted(test_dir.glob("*.py")):
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                count += 1
    return count


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _numbered_migrations(ws: Path) -> list[Path]:
    mig_dir = ws / "todo" / "migrations"
    return sorted(
        p for p in mig_dir.iterdir() if p.suffix == ".py" and p.name != "__init__.py"
    )


def _migration_hashes(ws: Path) -> dict[str, str]:
    return {p.name: _sha256(p) for p in _numbered_migrations(ws)}


def _scenario_evaluator_asset(scenario_id: str) -> str:
    scenario_path = BUNDLE_ROOT / "data" / "scenarios" / f"{scenario_id}.yaml"
    assert scenario_path.is_file(), f"bundled scenario not found: {scenario_path}"
    data = yaml.safe_load(scenario_path.read_text(encoding="utf-8"))
    asset = data["evaluator_asset"]
    assert asset, f"evaluator_asset missing for {scenario_id}"
    return asset


class TestKaggleBundleSmokeV2Preflight:
    @pytest.mark.parametrize("scenario_id", SMOKE_SCENARIOS)
    def test_bundle_baseline_47_tests_and_evaluator_pass(self, tmp_path: Path, scenario_id: str) -> None:
        assert BUNDLE_DATA_TODO.is_dir(), "bundle data todo repo missing"

        # 1. copy baseline from the generated bundle
        workspace = tmp_path / f"ws_{scenario_id}"
        shutil.copytree(str(BUNDLE_DATA_TODO), str(workspace), symlinks=False)

        # 2. prove the five baseline test files exist
        test_dir = workspace / "todo" / "tests"
        assert test_dir.is_dir()
        files = sorted(p.name for p in test_dir.glob("*.py"))
        assert files == list(EXPECTED_TODO_TEST_FILES), f"test files mismatch: {files}"

        # 3. prove 47 test methods are present
        assert _count_test_methods(test_dir) == 47, "baseline test method count != 47"

        # 4. apply the correct source mapping for the scenario
        for rel, content in get_correct_sources_for_scenario(scenario_id).items():
            target = workspace / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)

        # 5. run makemigrations todo --noinput
        pre_hashes = _migration_hashes(workspace)
        make = subprocess.run(
            [sys.executable, "manage.py", "makemigrations", "todo", "--noinput"],
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=180,
        )
        assert make.returncode == 0, f"makemigrations failed\n{make.stdout}\n{make.stderr}"

        # 6. exactly one new migration and old migration hashes unchanged
        post_migrations = _numbered_migrations(workspace)
        assert len(post_migrations) == len(pre_hashes) + 1, (
            f"expected exactly one new migration, got {len(post_migrations)} vs {len(pre_hashes)}"
        )
        for name, expected_hash in pre_hashes.items():
            assert _sha256(workspace / "todo" / "migrations" / name) == expected_hash, (
                f"baseline migration changed: {name}"
            )

        # 7. run manage.py test todo --verbosity 1
        test_run = subprocess.run(
            [sys.executable, "manage.py", "test", "todo", "--verbosity", "1"],
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=300,
        )

        # 8. assert return code zero and output reports exactly Ran 47 tests
        combined = test_run.stdout + test_run.stderr
        assert test_run.returncode == 0, (
            f"todo test suite failed for {scenario_id}\n{combined}"
        )
        assert "Ran 47 tests" in combined, (
            f"expected 'Ran 47 tests' for {scenario_id}\n{combined}"
        )

        # 9. call the real scenario evaluator from the generated code bundle
        evaluator_asset = _scenario_evaluator_asset(scenario_id)
        evaluator_result = run_scenario_evaluator(
            BUNDLE_CODE,
            evaluator_asset,
            workspace,
            python_executable=sys.executable,
            timeout=120,
        )

        # 10. assert evaluator pass and expected check list is non-empty
        assert evaluator_result.passed, (
            f"evaluator failed for {scenario_id}: {evaluator_result.error}"
        )
        assert evaluator_result.checks, f"evaluator returned no checks for {scenario_id}"
        assert evaluator_result.exit_code == 0

        # 11. assert generated workspace contains no tests/evaluator_assets
        _assert_workspace_has_no_evaluator_assets(workspace)


class TestKaggleBundleGlobalContract:
    def test_exact_six_evaluator_files(self) -> None:
        assets = sorted(BUNDLE_EVALUATOR_DIR.iterdir())
        assert [p.name for p in assets] == list(EXPECTED_EVALUATOR_ASSETS)

    def test_each_py_hash_equals_its_sha256(self) -> None:
        for name in EXPECTED_EVALUATOR_ASSETS:
            if not name.endswith(".py"):
                continue
            asset = BUNDLE_EVALUATOR_DIR / name
            fingerprint = BUNDLE_EVALUATOR_DIR / f"{name}.sha256"
            assert fingerprint.is_file(), f"missing fingerprint for {name}"
            recorded = fingerprint.read_text(encoding="utf-8").strip().split()[0]
            assert _sha256(asset) == recorded, f"fingerprint mismatch for {name}"

    def test_no_tests_support_in_code_bundle(self) -> None:
        assert not (BUNDLE_CODE / "tests" / "support").exists()

    def test_no_scripted_backend_or_harness(self) -> None:
        hits = [
            p for p in BUNDLE_ROOT.rglob("*")
            if "scripted" in p.name.lower() or "harness" in p.name.lower()
        ]
        assert hits == [], f"scripted/harness files in bundle: {hits}"

    def test_no_caches_dbs_absolute_paths_or_secrets(self) -> None:
        forbidden_names = ("__pycache__", ".pyc", "db.sqlite3", ".env", ".sqlite3")
        hits = [
            p for p in BUNDLE_ROOT.rglob("*")
            if any(n in p.name for n in forbidden_names)
        ]
        assert hits == [], f"forbidden artifacts in bundle: {hits}"

        for manifest in ("code_manifest.json", "data_manifest.json", "notebook_manifest.json"):
            text = (BUNDLE_ROOT / manifest).read_text(encoding="utf-8")
            assert "\\" not in text, f"backslash path separator in {manifest}"

        secret_hits = [
            p for p in BUNDLE_ROOT.rglob("*")
            if p.is_file() and (p.read_bytes().find(b"sk-or-v1-") != -1)
        ]
        assert secret_hits == [], f"embedded API key material in bundle: {secret_hits}"
