from __future__ import annotations

import ast
import builtins
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

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

# ---- FULL9-EXEC-01: corrected Full-9 executable notebook contract -----------
FULL9_SOURCE_COMMIT = "7f2a4509482dc7e62c2b243374592e9a88e2ff48"
FULL9_BUILD_ID = "7f2a450"
FULL9_EXPECTED_MODEL_IDENTITY = "qwen:14b-instruct-v1:bnb-nf4:cfg-cc9474140d25"
FULL9_OUTPUT_DIR_NAME = "qwen14b_bnb_nf4_full9_scientific_smoke_wsfix_7f2a450"
FULL9_OUTPUT_DIR = f"/kaggle/working/runs/{FULL9_OUTPUT_DIR_NAME}"
FULL9_PREFLIGHT_DIR = "/kaggle/working/runs/preflight_full9_wsfix_7f2a450"
FULL9_SCENARIOS = ("todo-smoke-001", "todo-smoke-002", "todo-smoke-003")
FULL9_STRATEGIES = ("monolithic", "selective", "iterative_repository_agent")
FULL9_EXPECTED_MATRIX = frozenset(
    (s, st) for s in FULL9_SCENARIOS for st in FULL9_STRATEGIES
)
ACTIVE_FULL9_CELL_ORDER = (
    "setup-cell",
    "install-lock-cell",
    "preflight-cell",
    "secrets-cell",
    "full9-execution-cell",
    "full9-verification-cell",
    "export-evidence-cell",
)
REMOVED_LEGACY_CELL_IDS = (
    "exec-cell",
    "progress-cell",
    "selective-calibration-canary-md",
    "selective-calibration-canary-cell",
    "continuous-smoke-md",
    "continuous-smoke-cell",
)


def _src(cell: dict[str, Any]) -> str:
    src = cell["source"]
    return src if isinstance(src, str) else "".join(src)


def _canonical_notebook() -> dict[str, Any]:
    nb_path = PROJECT_ROOT / "notebooks" / "seven_arm_benchmark.ipynb"
    assert nb_path.is_file(), f"canonical notebook missing: {nb_path}"
    return json.loads(nb_path.read_text(encoding="utf-8"))


def _cell_sources(nb: dict[str, Any]) -> dict[str, str]:
    return {c.get("id", ""): _src(c) for c in nb["cells"]}


def _code_cells_text(nb: dict[str, Any]) -> str:
    return "\n".join(
        _src(c) for c in nb["cells"] if c.get("cell_type") == "code"
    )


def _code_cell_sources(nb: dict[str, Any]) -> dict[str, str]:
    return {
        c.get("id", ""): _src(c)
        for c in nb["cells"]
        if c.get("cell_type") == "code"
    }


FULL9_SETUP_HELPER_FUNCS = frozenset({
    "_load_smoke_evidence",
    "_terminal_record_outcome",
    "_verify_full9_evidence",
    "_export_full9_evidence",
    "_label_bar_containers",
})
FULL9_SETUP_HELPER_CONSTS = frozenset({
    "SOURCE_COMMIT",
    "DEPLOYED_BUILD_ID",
    "EXPECTED_MODEL_IDENTITY",
    "EXPECTED_PROFILE",
    "EXPECTED_PROTOCOL_VERSION",
    "FULL9_EXPECTED_MATRIX",
    "SCIENTIFIC_FAILURE_KINDS",
    "ENGINEERING_FAILURE_KINDS",
    "EVIDENCE_FILES",
    "KAGGLE_DEPLOYMENT_PATHS",
    "FULL9_OUTPUT_DIR",
})


def _full9_verify_namespace() -> dict[str, Any]:
    """Extract the setup-cell Full-9 verification helpers into a clean namespace."""
    nb = _canonical_notebook()
    setup_src = _cell_sources(nb)["setup-cell"]
    tree = ast.parse(setup_src)
    segments: list[str] = []
    for node in tree.body:
        if (
            isinstance(node, ast.FunctionDef) and node.name in FULL9_SETUP_HELPER_FUNCS
        ) or (
            isinstance(node, ast.ClassDef)
            and node.name == "ScientificSmokeExecutionError"
        ):
            segments.append(ast.get_source_segment(setup_src, node))
        elif isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if any(t in FULL9_SETUP_HELPER_CONSTS for t in targets):
                segments.append(ast.get_source_segment(setup_src, node))
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id in FULL9_SETUP_HELPER_CONSTS
        ):
            segments.append(ast.get_source_segment(setup_src, node))
    ns: dict[str, Any] = {
        "Path": Path,
        "_json": json,
        "zipfile": zipfile,
        "datetime": datetime,
    }
    exec(compile("\n\n".join(segments), "setup-cell-full9-helpers", "exec"), ns)
    return ns


def _exact_full9_records(source_commit: str = FULL9_SOURCE_COMMIT) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    index = 0
    for scenario in FULL9_SCENARIOS:
        for strategy in FULL9_STRATEGIES:
            records.append({
                "run_id": f"full9-run-{index}",
                "scenario_id": scenario,
                "strategy_id": strategy,
                "strategy_name": strategy,
                "status": "succeeded",
                "source_commit": source_commit,
                "repetition": 1,
                "profile": "scientific-smoke-v2",
                "failure_classification": "",
                "failure_details": [],
                "total_workflow_model_calls": 3,
                "total_workflow_tokens": 200,
            })
            index += 1
    return records


def _write_full9_evidence(
    output_dir: Path,
    records: list[dict[str, Any]] | None = None,
    total_planned: int = 9,
    total_completed: int | None = None,
    pending_run_ids: list[str] | None = None,
    source_commit: str = FULL9_SOURCE_COMMIT,
    build_id: str = FULL9_BUILD_ID,
    model_identity: str = FULL9_EXPECTED_MODEL_IDENTITY,
    profile: str = "scientific-smoke-v2",
    protocol_version: str = "1.0",
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "experiment_id.txt").write_text("exp-full9-test\n", encoding="utf-8")
    (output_dir / "source_identity.json").write_text(
        json.dumps({
            "source_commit": source_commit,
            "source_tag": "",
            "deployed_build_id": build_id,
            "config_hash": "cfg-cc9474140d25",
            "model_identity": model_identity,
            "profile": profile,
            "protocol_version": protocol_version,
            "experiment_id": "exp-full9-test",
            "hf_repo_id": "NabilDo/selective-regeneration-experiment-results",
            "dry_run": False,
        }),
        encoding="utf-8",
    )
    records = records or _exact_full9_records(source_commit=source_commit)
    completed = total_completed if total_completed is not None else len(records)
    (output_dir / "run_records.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in records),
        encoding="utf-8",
    )
    planned_ids = [f"rid-{i}" for i in range(total_planned)]
    (output_dir / "checkpoint.json").write_text(
        json.dumps({
            "profile": profile,
            "execution_plan_hash": "hash",
            "planned_run_ids": planned_ids,
            "completed_run_ids": planned_ids[:completed],
            "failed_run_ids": [],
            "succeeded_run_ids": planned_ids[:completed],
            "retryable_run_ids": [],
            "pending_run_ids": pending_run_ids or planned_ids[completed:],
            "current_run_id": "",
            "total_planned": total_planned,
            "total_completed": completed,
            "protocol_version": protocol_version,
            "model_identity": model_identity,
            "config_hash": "cfg-cc9474140d25",
            "source_commit": source_commit,
            "completion_status": "completed" if completed == total_planned else "incomplete",
            "scenario_ids": list(FULL9_SCENARIOS),
            "strategy_names": list(FULL9_STRATEGIES),
            "declared_source_tag": "",
            "deployed_build_id": build_id,
            "attempted_run_ids": planned_ids[:completed],
        }),
        encoding="utf-8",
    )
    return output_dir


def _assert_full9_command_contract(
    cmd: list[str],
    data_dir: Path,
    model_path: str,
    output_dir: Path,
) -> None:
    pairs = {
        "--backend": "kaggle-qwen",
        "--profile": "scientific-smoke-v2",
        "--qwen-quantization": "bnb-nf4",
        "--max-attempts": "3",
        "--protocol-version": "1.0",
        "--max-completion-tokens-per-call": "1024",
        "--max-total-workflow-tokens": "0",
        "--timeout": "300",
        "--hf-repo-id": "NabilDo/selective-regeneration-experiment-results",
        "--source-commit": FULL9_SOURCE_COMMIT,
        "--deployed-build-id": FULL9_BUILD_ID,
        "--data-dir": str(data_dir),
        "--model-path": model_path,
        "--output-dir": str(output_dir),
    }
    assert cmd[0] == sys.executable, cmd[0]
    for flag, value in pairs.items():
        assert flag in cmd, f"missing {flag}"
        assert cmd[cmd.index(flag) + 1] == value, f"{flag} value mismatch"
    for flag in ("--hf-sync", "--new-experiment"):
        assert flag in cmd, f"missing {flag}"
    for forbidden in ("--strategy", "--max-runs", "--auto-resume-hf"):
        assert forbidden not in cmd, f"forbidden flag {forbidden}"


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


def _bundled_notebook_sources() -> str:
    nb_path = BUNDLE_ROOT / "notebooks" / "seven_arm_benchmark.ipynb"
    assert nb_path.is_file(), f"bundled notebook missing: {nb_path}"
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    chunks = []
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        src = cell["source"]
        chunks.append("".join(src) if isinstance(src, list) else src)
    return "\n".join(chunks)


def _pinned_identity() -> dict[str, str]:
    """Extract the notebook's pinned SOURCE_COMMIT / DEPLOYED_BUILD_ID."""
    text = _bundled_notebook_sources()
    source = re.search(r'SOURCE_COMMIT = "([0-9a-f]{40})"', text)
    build = re.search(r'DEPLOYED_BUILD_ID = "([0-9a-f]{7})"', text)
    assert source, "SOURCE_COMMIT pin missing in bundled notebook"
    assert build, "DEPLOYED_BUILD_ID pin missing in bundled notebook"
    return {"source_commit": source.group(1), "build_id": build.group(1)}


def _name_closure_sets(src: str) -> tuple[set[str], set[str]]:
    """Return (defined, loaded) top-level-ish names for a cell's source."""
    tree = ast.parse(src)
    defined: set[str] = set()
    loaded: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            if isinstance(node.ctx, (ast.Store, ast.Del)):
                defined.add(node.id)
            else:
                loaded.add(node.id)
        elif isinstance(node, ast.arg):
            defined.add(node.arg)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(node.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                defined.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                defined.add(alias.asname or alias.name.split(".")[-1])
    return defined, loaded


def _bootstrap_undefined_names(src: str) -> set[str]:
    """Return top-level names loaded before they are defined in ``src``.

    Mirrors real setup-cell execution order: module-level statements run
    sequentially, function/lambda bodies are ignored until called, class bodies
    are checked because they execute at class-definition time, and
    comprehension-local target variables are excluded. This catches bootstrap
    ``NameError`` regressions (e.g. the deleted ``MODEL_DIR``) that cell
    compilation alone cannot detect.
    """
    tree = ast.parse(src)
    defined_so_far: set[str] = set()
    undefined: set[str] = set()
    loaded_stack: list[set[str]] = []
    local_scopes: list[set[str]] = []

    def is_local(name: str) -> bool:
        return any(name in scope for scope in local_scopes)

    def visit(node: ast.AST) -> None:
        if isinstance(node, ast.Name):
            if isinstance(node.ctx, (ast.Store, ast.Del)):
                if local_scopes:
                    local_scopes[-1].add(node.id)
                else:
                    defined_so_far.add(node.id)
            elif isinstance(node.ctx, ast.Load):
                if not is_local(node.id):
                    loaded_stack[-1].add(node.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defined_so_far.add(node.name)
            for decorator in node.decorator_list:
                visit(decorator)
        elif isinstance(node, ast.ClassDef):
            defined_so_far.add(node.name)
            for decorator in node.decorator_list:
                visit(decorator)
            for base in node.bases:
                visit(base)
            local_scopes.append(set())
            for stmt in node.body:
                visit(stmt)
            local_scopes.pop()
        elif isinstance(node, ast.Import):
            for alias in node.names:
                defined_so_far.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                defined_so_far.add(alias.asname or alias.name.split(".")[-1])
        elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            local_scopes.append({
                n.id for n in ast.walk(node)
                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)
            })
            for child in ast.iter_child_nodes(node):
                visit(child)
            local_scopes.pop()
        else:
            for child in ast.iter_child_nodes(node):
                visit(child)

    builtins_names = set(dir(builtins))
    for stmt in tree.body:
        defined_before = set(defined_so_far)
        loaded_stack.append(set())
        visit(stmt)
        statement_loaded = loaded_stack.pop()
        for name in statement_loaded:
            if name not in defined_before and name not in builtins_names:
                undefined.add(name)
    return undefined


def _setup_top_level_assign(tree: ast.Module, name: str) -> ast.Assign:
    """Return the top-level setup-cell ``ast.Assign`` that binds ``name``."""
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign):
            targets = [t.id for t in stmt.targets if isinstance(t, ast.Name)]
            if name in targets:
                return stmt
    raise AssertionError(f"setup-cell must assign {name} at top level")


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


class TestKaggleBundleCliDryRun:
    def test_bundled_cli_dry_run_executes_exact_nine_cell_plan(self, tmp_path: Path) -> None:
        script = BUNDLE_CODE / "seven_arm_benchmark.py"
        assert script.is_file(), f"generated entrypoint not found: {script}"
        src_dir = BUNDLE_CODE / "src"
        data_dir = BUNDLE_ROOT / "data"
        assert data_dir.is_dir(), f"bundled data dir missing: {data_dir}"

        runs_dir = tmp_path / "runs"

        env = os.environ.copy()
        env["PYTHONPATH"] = str(src_dir)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env.pop("HF_TOKEN", None)
        env.pop("OPENROUTER_API_KEY", None)

        before = subprocess.run(
            ["git", "status", "--short"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )
        before_status = before.stdout

        pinned = _pinned_identity()

        result = subprocess.run(
            [
                sys.executable, str(script),
                "--dry-run",
                "--profile", "scientific-smoke-v2",
                "--data-dir", str(data_dir),
                "--output-dir", str(runs_dir),
                "--source-commit", pinned["source_commit"],
                "--deployed-build-id", pinned["build_id"],
                "--max-attempts", "3",
                "--max-completion-tokens-per-call", "4096",
                "--max-total-workflow-tokens", "0",
                "--timeout", "300",
            ],
            cwd=str(tmp_path),
            timeout=120,
            capture_output=True,
            text=True,
            env=env,
        )
        combined = result.stdout + result.stderr

        assert result.returncode == 0, (
            f"bundled CLI dry-run failed rc={result.returncode}\n{combined}"
        )
        assert "Selected 3 scenario(s) for profile=scientific-smoke-v2" in combined, (
            f"missing selection line\n{combined}"
        )
        assert "Execution plan: 9 pending" in combined, (
            f"missing execution-plan line\n{combined}"
        )
        assert "Benchmark complete: 9/9 runs" in combined, (
            f"missing completion line\n{combined}"
        )

        after = subprocess.run(
            ["git", "status", "--short"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )
        after_status = after.stdout
        assert before_status == after_status, (
            f"bundled CLI dry-run changed the working tree\nbefore:\n{before_status}\nafter:\n{after_status}"
        )

        records = [
            json.loads(line)
            for line in (runs_dir / "run_records.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert len(records) == 9, f"expected 9 records, got {len(records)}"
        assert all(r["status"] == "succeeded" for r in records), "not all statuses succeeded"
        assert all(r["profile"] == "scientific-smoke-v2" for r in records), "profile mismatch"
        assert all(r["repetition"] == 1 for r in records), "repetition != 1"
        assert all(r["model_metadata"]["dry_run"] == "True" for r in records), "dry_run flag mismatch"
        assert all(r["model_calls"] == 0 for r in records), "model_calls != 0"
        assert all(r["total_workflow_tokens"] == 0 for r in records), "total_workflow_tokens != 0"

        scenario_set = {r["scenario_id"] for r in records}
        strategy_set = {r["strategy_id"] for r in records}
        assert scenario_set == {
            "todo-smoke-001",
            "todo-smoke-002",
            "todo-smoke-003",
        }, f"scenario set mismatch: {scenario_set}"
        assert strategy_set == {
            "monolithic",
            "selective",
            "iterative_repository_agent",
        }, f"strategy set mismatch: {strategy_set}"

        pairs = {(r["scenario_id"], r["strategy_id"]) for r in records}
        expected_pairs = {
            (s, st)
            for s in ("todo-smoke-001", "todo-smoke-002", "todo-smoke-003")
            for st in ("monolithic", "selective", "iterative_repository_agent")
        }
        assert len(records) == len(pairs) == len(expected_pairs) == 9, "not 9 unique pairs"
        assert pairs == expected_pairs, f"pair set mismatch: {pairs ^ expected_pairs}"

        checkpoint = json.loads(
            (runs_dir / "checkpoint.json").read_text(encoding="utf-8")
        )
        assert checkpoint["total_planned"] == 9, checkpoint["total_planned"]
        assert checkpoint["total_completed"] == 9, checkpoint["total_completed"]
        assert checkpoint["completion_status"] == "completed", checkpoint["completion_status"]
        assert set(checkpoint["scenario_ids"]) == scenario_set, "checkpoint scenario_ids mismatch"
        assert set(checkpoint["strategy_names"]) == strategy_set, "checkpoint strategy_names mismatch"
        assert checkpoint["source_commit"] == pinned["source_commit"], (
            checkpoint["source_commit"]
        )
        assert checkpoint["deployed_build_id"] == pinned["build_id"], checkpoint["deployed_build_id"]

        identity = json.loads(
            (runs_dir / "source_identity.json").read_text(encoding="utf-8")
        )
        assert identity["source_commit"] == pinned["source_commit"], (
            identity["source_commit"]
        )
        assert identity["deployed_build_id"] == pinned["build_id"], identity["deployed_build_id"]
        assert identity["profile"] == "scientific-smoke-v2", identity["profile"]
        assert identity["dry_run"] is True, identity["dry_run"]

        summary = json.loads(
            (runs_dir / "benchmark_summary.json").read_text(encoding="utf-8")
        )
        assert set(summary) == strategy_set, f"summary strategy keys mismatch: {set(summary)}"
        for sname in strategy_set:
            agg = summary[sname]["aggregate"]
            assert agg["run_count"] == 3, f"{sname} run_count != 3"
            assert agg["success_count"] == 3, f"{sname} success_count != 3"
            assert agg["failed_count"] == 0, f"{sname} failed_count != 0"
        total_records = sum(len(entry["records"]) for entry in summary.values())
        assert total_records == 9, f"summary records total != 9: {total_records}"


class TestKaggleBundleRuntimeGuardrails:
    """KAGGLE-SMOKE-V2: fail-closed runtime guardrails on the generated bundle."""

    def _bundle_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(BUNDLE_CODE / "src")
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env.pop("HF_TOKEN", None)
        env.pop("OPENROUTER_API_KEY", None)
        return env

    def test_missing_model_fails_before_experiment_creation(self, tmp_path: Path) -> None:
        script = BUNDLE_CODE / "seven_arm_benchmark.py"
        assert script.is_file()
        data_dir = BUNDLE_ROOT / "data"
        runs_dir = tmp_path / "runs"
        pinned = _pinned_identity()

        result = subprocess.run(
            [
                sys.executable, str(script),
                "--backend", "kaggle-qwen",
                "--profile", "scientific-smoke-v2",
                "--data-dir", str(data_dir),
                "--output-dir", str(runs_dir),
                "--model-path", str(tmp_path / "no-such-model"),
                "--source-commit", pinned["source_commit"],
                "--deployed-build-id", pinned["build_id"],
                "--max-runs", "1",
                "--max-attempts", "3",
                "--protocol-version", "1.0",
                "--max-completion-tokens-per-call", "4096",
                "--max-total-workflow-tokens", "0",
                "--timeout", "300",
            ],
            cwd=str(tmp_path),
            timeout=120,
            capture_output=True,
            text=True,
            env=self._bundle_env(),
        )
        combined = result.stdout + result.stderr
        assert result.returncode != 0, f"expected non-zero, got {result.returncode}\n{combined}"
        assert "--model-path" in combined, f"missing --model-path error\n{combined}"
        assert not (runs_dir / "experiment_id.txt").exists(), (
            "experiment was created despite a missing model"
        )

    def test_shared_snapshot_non_dry_wiring_in_bundle(self) -> None:
        source = (BUNDLE_CODE / "seven_arm_benchmark.py").read_text(encoding="utf-8")
        assert "snapshot_storage_root" in source, "snapshot_storage_root wiring missing"
        assert "snapshot_base" in source, "snapshot_base wiring missing"
        assert 'workspace_dir / "snapshots"' in source, "shared storage root call missing"

    def test_one_run_fail_closed_exit_logic_in_bundle(self) -> None:
        source = (BUNDLE_CODE / "seven_arm_benchmark.py").read_text(encoding="utf-8")
        assert "_decide_session_exit_code" in source, "exit-code helper missing"
        assert "session_created_run_ids" in source, "session run tracking missing"
        assert "last_run_status" in source, "last-run status tracking missing"
        assert "last_run_outcome" in source, "terminal outcome tracking missing"
        assert "_terminal_record_outcome" in source, "scientific/engineering classifier missing"
        assert "engineering_blocker_count" in source, "engineering blocker gate missing"
        assert "completed_with_failures" in source, "truthful completion marker missing"

    def test_notebook_pins_exact_source_and_build_identity(self) -> None:
        pinned = _pinned_identity()
        assert re.fullmatch(r"[0-9a-f]{40}", pinned["source_commit"]), pinned["source_commit"]
        assert pinned["build_id"] == pinned["source_commit"][:7], (
            f"build id {pinned['build_id']} != short source {pinned['source_commit'][:7]}"
        )

    def test_notebook_hf_repo_id_is_correct(self) -> None:
        text = _bundled_notebook_sources()
        assert 'HF_RESULTS_REPO_ID = "NabilDo/selective-regeneration-experiment-results"' in text, (
            "bundled notebook HF repo ID is not NabilDo/selective-regeneration-experiment-results"
        )

    def test_full9_exec_01_verification_cell_uses_full9_guardrail(self) -> None:
        nb = _canonical_notebook()
        sources = _cell_sources(nb)
        verify_src = sources["full9-verification-cell"]
        assert "_verify_full9_evidence(FULL9_OUTPUT_DIR)" in verify_src, (
            "full9-verification-cell must call the Full-9 evidence verifier"
        )
        text = _bundled_notebook_sources()
        assert "Full-9 verification FAILED" in text
        assert "engineering blocker record" in text
        assert "scientific_failed" in text
        assert "exact 3x3 scenario x strategy matrix" in text

    def test_notebook_pins_14b_base_checkpoint_and_nf4(self) -> None:
        text = _bundled_notebook_sources()
        assert "/transformers/14b-instruct/1" in text, (
            "bundled notebook does not pin the 14b-instruct base checkpoint"
        )
        assert "gptq" not in text.lower(), (
            "bundled notebook must not reference a GPTQ checkpoint"
        )
        assert 'QWEN_QUANTIZATION = "bnb-nf4"' in text
        assert "--qwen-quantization" in text


class TestKaggleBundleR7CRuntimeClosure:
    """R7C-REAL-RUN-ROOT-CLOSURE: pinned runtime + preflight gate + repairability."""

    def test_requirements_smoke_kaggle_lock_bundled_with_exact_pins(self) -> None:
        lock = BUNDLE_CODE / "requirements-smoke-kaggle.lock"
        assert lock.is_file(), f"requirements-smoke-kaggle.lock not bundled: {lock}"
        text = lock.read_text(encoding="utf-8")
        assert "Django==5.2.16" in text
        assert "djangorestframework==3.17.1" in text
        assert "pytest==8.4.2" in text
        assert "pytest-django==4.12.0" in text
        assert "accelerate==1.14.0" in text
        assert "bitsandbytes==0.49.2" in text
        assert "transformers==4.57.6" in text
        pin_lines = {line.split("==")[0] for line in text.splitlines() if "==" in line}
        assert "torch" not in pin_lines, "lock must not pin torch (Kaggle image provides it)"
        assert "transformers" in pin_lines, "lock must pin transformers==4.57.6"

    def test_bundled_pyproject_pins_django_runtime(self) -> None:
        pyproject = BUNDLE_CODE / "pyproject.toml"
        assert pyproject.is_file(), "pyproject.toml not bundled"
        text = pyproject.read_text(encoding="utf-8")
        assert "Django==5.2.16" in text
        assert "djangorestframework==3.17.1" in text
        assert "pytest-django==4.12.0" in text

    def test_bundled_cli_has_kaggle_preflight_only_gate(self) -> None:
        source = (BUNDLE_CODE / "seven_arm_benchmark.py").read_text(encoding="utf-8")
        assert "--kaggle-preflight-only" in source
        assert "run_kaggle_smoke_preflight" in source
        assert "render_preflight_table" in source
        assert "kaggle_smoke_preflight.v1" in source

    def test_bundled_cli_bootstraps_src_without_ambient_pythonpath(
        self, tmp_path: Path
    ) -> None:
        """The deployed script must reach its preflight gate in a clean subprocess."""
        model_dir = tmp_path / "fake-model"
        model_dir.mkdir()
        (model_dir / "config.json").write_text("{}\n", encoding="utf-8")
        (model_dir / "model.safetensors").write_bytes(b"not-real-weights")
        output_dir = tmp_path / "preflight"
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        env["PYTHONDONTWRITEBYTECODE"] = "1"

        result = subprocess.run(
            [
                sys.executable,
                str(BUNDLE_CODE / "seven_arm_benchmark.py"),
                "--kaggle-preflight-only",
                "--backend",
                "kaggle-qwen",
                "--profile",
                "scientific-smoke-v2",
                "--data-dir",
                str(BUNDLE_ROOT / "data"),
                "--model-path",
                str(model_dir),
                "--output-dir",
                str(output_dir),
            ],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        combined = result.stdout + result.stderr
        assert result.returncode == 1, combined
        assert "No module named 'benchmark'" not in combined
        assert "KAGGLE SMOKE PREFLIGHT" in combined
        assert (output_dir / "kaggle_smoke_preflight.v1.json").is_file()
        assert not (output_dir / "checkpoint.json").exists()
        assert not (output_dir / "workspace").exists()

    def test_bundled_preflight_module_present(self) -> None:
        module = BUNDLE_CODE / "src" / "benchmark" / "execution" / "preflight.py"
        assert module.is_file(), "preflight module not bundled"
        text = module.read_text(encoding="utf-8")
        assert "kaggle_smoke_preflight.v1" in text
        assert "MIN_FREE_VRAM_GIB" in text
        assert "PROBE_MAX_TOKENS" in text
        assert "BitsAndBytesConfig" in text or "bitsandbytes" in text

    def test_bundled_cli_uses_model_aware_quantization_identity(self) -> None:
        source = (BUNDLE_CODE / "seven_arm_benchmark.py").read_text(encoding="utf-8")
        backend_source = (BUNDLE_CODE / "src" / "benchmark" / "llm" / "kaggle_qwen_backend.py").read_text(
            encoding="utf-8"
        )
        assert "compute_model_identity" in source
        assert 'return "qwen:1:int8"' not in source
        assert "qwen-quantization" in source
        assert "CANONICAL_QUANTIZATION_MODES" in backend_source
        assert 'choices=["bnb-int8", "bnb-nf4", "fp16"]' in source

    def test_bundled_runner_has_infrastructure_nonrepairable_classification(self) -> None:
        source = (BUNDLE_CODE / "src" / "benchmark" / "execution" / "runner.py").read_text(
            encoding="utf-8"
        )
        assert "classify_validation_repairability" in source
        assert "infrastructure_nonrepairable" in source
        assert "_reclassify_infrastructure_failure" in source

    def test_bundled_regeneration_threads_scenario_context_and_preserve_guard(self) -> None:
        source = (BUNDLE_CODE / "src" / "benchmark" / "execution" / "regeneration.py").read_text(
            encoding="utf-8"
        )
        assert "SCENARIO_CONTEXT_PROMPT_TEMPLATE" in source
        assert "expected_action_for" in source
        assert "out_of_scope_change" in source
        assert "build_generation_prompt" in source

    def test_bundled_models_include_frozen_scenario_context(self) -> None:
        source = (BUNDLE_CODE / "src" / "benchmark" / "core" / "models.py").read_text(
            encoding="utf-8"
        )
        assert "class RegenerationScenarioContext" in source
        assert "expected_action_for" in source

    def test_bundled_enums_include_infrastructure_nonrepairable(self) -> None:
        source = (BUNDLE_CODE / "src" / "benchmark" / "core" / "enums.py").read_text(
            encoding="utf-8"
        )
        assert "infrastructure_nonrepairable" in source


class TestKaggleFull9OutputDefinitionOrder:
    """FULL9-EXEC-01: FULL9_OUTPUT_DIR is defined in setup-cell before use."""

    @staticmethod
    def _notebook_cells() -> tuple[dict[str, Any], dict[str, Any], int, int]:
        nb_path = PROJECT_ROOT / "notebooks" / "seven_arm_benchmark.ipynb"
        assert nb_path.is_file(), f"canonical notebook missing: {nb_path}"
        nb = json.loads(nb_path.read_text(encoding="utf-8"))
        cells = nb["cells"]
        setup_idx = next(i for i, c in enumerate(cells) if c.get("id") == "setup-cell")
        exec_idx = next(
            i for i, c in enumerate(cells) if c.get("id") == "full9-execution-cell"
        )
        by_id = {c.get("id"): c for c in cells}
        return by_id["setup-cell"], by_id["full9-execution-cell"], setup_idx, exec_idx

    def test_full9_output_dir_defined_before_full9_cell(self) -> None:
        setup, exec_cell, setup_idx, exec_idx = self._notebook_cells()
        setup_src = _src(setup)
        exec_src = _src(exec_cell)
        assert setup_src.count('KAGGLE_DEPLOYMENT_PATHS["full9_output_dir"]') == 1, (
            "setup-cell must define FULL9_OUTPUT_DIR via KAGGLE_DEPLOYMENT_PATHS exactly once"
        )
        assert FULL9_OUTPUT_DIR in setup_src, (
            "setup-cell must define the exact Full-9 output dir literal"
        )
        assert "FULL9_OUTPUT_DIR = Path(" not in setup_src, (
            "setup-cell must not hard-code FULL9_OUTPUT_DIR outside KAGGLE_DEPLOYMENT_PATHS"
        )
        assert "FULL9_OUTPUT_DIR = Path(" not in exec_src, (
            "full9-execution-cell must not re-assign FULL9_OUTPUT_DIR"
        )
        assert "FULL9_OUTPUT_DIR" in exec_src, (
            "full9-execution-cell must use FULL9_OUTPUT_DIR"
        )
        assert setup_idx < exec_idx, (
            "setup-cell must appear before full9-execution-cell"
        )


class TestKaggleFull9ExecutionClosure:
    """FULL9-EXEC-01: the Full-9 pipeline cells form a name-closed 3x3 contract."""

    PIPELINE_CELL_IDS = (
        "setup-cell",
        "full9-execution-cell",
        "full9-verification-cell",
        "export-evidence-cell",
    )

    def test_full9_pipeline_cells_present_and_legacy_cells_removed(self) -> None:
        nb = _canonical_notebook()
        ids = [c.get("id") for c in nb["cells"]]
        present = [cid for cid in ACTIVE_FULL9_CELL_ORDER if cid in ids]
        assert present == list(ACTIVE_FULL9_CELL_ORDER), (
            f"Full-9 cell order broken: {present}"
        )
        leftover = [cid for cid in REMOVED_LEGACY_CELL_IDS if cid in ids]
        assert leftover == [], f"legacy cells still present: {leftover}"

    def test_full9_execution_and_verification_cells_are_name_closed(self) -> None:
        nb = _canonical_notebook()
        sources = _cell_sources(nb)
        defined: set[str] = set()
        for cid in self.PIPELINE_CELL_IDS:
            d, _ = _name_closure_sets(sources[cid])
            defined |= d
        undefined: set[str] = set()
        for cid in ("full9-execution-cell", "full9-verification-cell", "export-evidence-cell"):
            _, loads = _name_closure_sets(sources[cid])
            undefined |= loads
        undefined -= defined
        undefined -= set(dir(builtins))
        undefined -= {"_", "__name__"}
        assert not undefined, f"undefined names in Full-9 pipeline: {sorted(undefined)}"

    def test_full9_verification_helpers_available_in_setup_cell(self) -> None:
        ns = _full9_verify_namespace()
        for fn in ("_load_smoke_evidence", "_terminal_record_outcome", "_verify_full9_evidence"):
            assert callable(ns.get(fn)), f"setup-cell must define {fn}()"
        assert ns.get("FULL9_EXPECTED_MATRIX") == FULL9_EXPECTED_MATRIX, (
            "setup-cell must define the exact 3x3 scenario x strategy matrix"
        )

    def test_full9_exec_01_setup_bootstrap_symbols_defined_before_use(self) -> None:
        """F9: every top-level setup-cell symbol must be defined before use.

        A deleted bootstrap binding (e.g. the undefined ``MODEL_DIR``) compiles
        fine but raises ``NameError`` at Kaggle setup time. This check mirrors
        real setup execution order, ignoring function/lambda bodies until
        called and comprehension-local target variables.
        """
        src = _cell_sources(_canonical_notebook())["setup-cell"]
        undefined = _bootstrap_undefined_names(src)
        assert undefined == set(), (
            "setup-cell loads top-level names before definition: "
            f"{sorted(undefined)}"
        )

    def test_full9_exec_01_setup_bootstrap_contract_preserved(self) -> None:
        """F9: the setup-cell must keep its fail-closed bootstrap contract.

        Source directory must be validated and put on ``sys.path``; model
        candidates must be initialized from ``KNOWN_MODEL`` with ``MODEL_PATH``
        derived from them; ``SCRIPT_PATH`` existence must be validated; the
        operational path source of truth must exist; and no old
        canary/continuous state may be present.
        """
        src = _cell_sources(_canonical_notebook())["setup-cell"]
        tree = ast.parse(src)

        src_dir_stmt = _setup_top_level_assign(tree, "src_dir")
        src_dir_guard = tree.body[tree.body.index(src_dir_stmt) + 1]
        assert isinstance(src_dir_guard, ast.If), (
            "src/ validation must immediately follow the src_dir assignment"
        )
        assert "src_dir" in ast.unparse(src_dir_guard.test)
        assert "sys.path.insert(0, str(src_dir))" in ast.unparse(src_dir_guard.body), (
            "source directory must be inserted into sys.path"
        )
        assert "FileNotFoundError" in ast.unparse(src_dir_guard.orelse), (
            "missing src/ must fail closed with FileNotFoundError"
        )

        candidates_stmt = _setup_top_level_assign(tree, "MODEL_CANDIDATES")
        candidates_loaded = {
            n.id for n in ast.walk(candidates_stmt.value)
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
        }
        assert "KNOWN_MODEL" in candidates_loaded, (
            "model candidates must be initialized from KNOWN_MODEL"
        )

        model_path_stmt = _setup_top_level_assign(tree, "MODEL_PATH")
        model_path_loaded = {
            n.id for n in ast.walk(model_path_stmt.value)
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
        }
        assert "MODEL_CANDIDATES" in model_path_loaded, (
            "MODEL_PATH must be derived from the initialized MODEL_CANDIDATES"
        )
        assert "MODEL_DIR" not in model_path_loaded, (
            "undefined MODEL_DIR must not be loaded"
        )

        script_stmt = _setup_top_level_assign(tree, "SCRIPT_PATH")
        script_guard = tree.body[tree.body.index(script_stmt) + 1]
        assert isinstance(script_guard, ast.If), (
            "SCRIPT_PATH existence must be validated immediately after assignment"
        )
        assert "SCRIPT_PATH" in ast.unparse(script_guard.test)
        assert "is_file" in ast.unparse(script_guard.test)
        assert "FileNotFoundError" in ast.unparse(script_guard.body), (
            "missing benchmark script must fail closed with FileNotFoundError"
        )

        assert "KAGGLE_DEPLOYMENT_PATHS" in src, (
            "deployment path source of truth must be available in setup-cell"
        )
        for stale in (
            "SELECTIVE_CANARY_OUTPUT_DIR",
            "OUTPUT_DIR = Path(",
            "RUN_GENERIC_ONE_RUN",
            "AUTHORIZE_CONTINUOUS_AFTER_CALIBRATION_REVIEW",
            "--auto-resume-hf",
        ):
            assert stale not in src, (
                f"stale canary/continuous state in setup-cell: {stale}"
            )

    def test_full9_exec_01_verification_accepts_exact_terminal_matrix(
        self, tmp_path: Path
    ) -> None:
        ns = _full9_verify_namespace()
        verifier = ns["_verify_full9_evidence"]
        evidence_dir = tmp_path / "runs" / FULL9_OUTPUT_DIR_NAME
        _write_full9_evidence(evidence_dir)
        verifier(str(evidence_dir))

    def test_full9_exec_01_verification_rejects_incomplete_matrix(
        self, tmp_path: Path
    ) -> None:
        ns = _full9_verify_namespace()
        verifier = ns["_verify_full9_evidence"]
        evidence_dir = tmp_path / "runs" / FULL9_OUTPUT_DIR_NAME
        records = _exact_full9_records()[:8]
        _write_full9_evidence(
            evidence_dir,
            records=records,
            total_planned=9,
            total_completed=8,
        )
        with pytest.raises((ns["ScientificSmokeExecutionError"], AssertionError, ValueError)):
            verifier(str(evidence_dir))

    def test_full9_exec_01_all_canonical_notebook_code_cells_compile(self) -> None:
        """Every canonical notebook code cell must compile as Python."""
        nb = _canonical_notebook()
        for idx, cell in enumerate(nb["cells"]):
            if cell.get("cell_type") != "code":
                continue
            cell_id = cell.get("id", "<no-id>")
            try:
                compile(_src(cell), f"canonical-cell-{idx}-{cell_id}", "exec")
            except SyntaxError as exc:
                raise AssertionError(
                    f"canonical notebook code cell index {idx} id '{cell_id}' "
                    f"failed to compile: {exc}"
                ) from exc

    def test_full9_exec_01_active_execution_cell_order_is_exact(self) -> None:
        """The active execution cells must appear in the exact documented order."""
        nb = _canonical_notebook()
        ids = [c.get("id") for c in nb["cells"]]
        present = [cid for cid in ACTIVE_FULL9_CELL_ORDER if cid in ids]
        assert present == list(ACTIVE_FULL9_CELL_ORDER), (
            f"active execution cell order broken: {present}"
        )

    def test_full9_exec_01_legacy_execution_state_is_absent(self) -> None:
        """F2: no stale generic/canary/continuous state may remain active."""
        text = _code_cells_text(_canonical_notebook())
        stale_fragments = (
            'OUTPUT_DIR = Path("/kaggle/working/runs/scientific_smoke_v2")',
            "SELECTIVE_CANARY_OUTPUT_DIR",
            "RUN_GENERIC_ONE_RUN",
            "AUTHORIZE_CONTINUOUS_AFTER_CALIBRATION_REVIEW",
            "_validate_continuous_precondition",
            "_verify_scientific_run",
            "_expected_model_identity",
        )
        for stale in stale_fragments:
            assert stale not in text, (
                f"stale Full-9 legacy execution state still present: {stale}"
            )

    def test_full9_exec_01_bundled_notebook_matches_canonical(self) -> None:
        """The bundled notebook code cells must be identical to the canonical ones."""
        canonical = _canonical_notebook()
        bundled_path = BUNDLE_ROOT / "notebooks" / "seven_arm_benchmark.ipynb"
        assert bundled_path.is_file(), f"bundled notebook missing: {bundled_path}"
        bundled = json.loads(bundled_path.read_text(encoding="utf-8"))
        c_code = [_src(c) for c in canonical["cells"] if c.get("cell_type") == "code"]
        b_code = [_src(c) for c in bundled["cells"] if c.get("cell_type") == "code"]
        assert c_code == b_code, (
            "bundled notebook code cells differ from canonical; rebuild the bundle"
        )


def _full9_fail_record(
    scenario: str,
    strategy: str,
    *,
    kind: str,
    status: str = "failed",
    classification: str = "",
) -> dict[str, Any]:
    """A FAILED Full-9 record carrying one terminal failure kind."""
    return {
        "run_id": f"full9-fail-{scenario}-{strategy}",
        "scenario_id": scenario,
        "strategy_id": strategy,
        "strategy_name": strategy,
        "status": status,
        "source_commit": FULL9_SOURCE_COMMIT,
        "repetition": 1,
        "profile": "scientific-smoke-v2",
        "failure_classification": classification,
        "failure_details": [
            {"kind": kind, "stage": "checkpoint", "message": f"terminal {kind}"}
        ],
        "total_workflow_model_calls": 1,
        "total_workflow_tokens": 10,
    }


def _full9_script_runner(
    ns: dict[str, Any],
    *,
    scripts_touched: list[str],
    fail_fast: bool = False,
    records: list[dict[str, Any]] | None = None,
    block_after_write: bool = False,
) -> Callable[..., Any]:
    """A controllable stand-in for the setup-cell _run_benchmark_live authority.

    Mirrors the real contract: create the runs dir, persist the console log and
    smoke evidence, and raise (fail fast) before persisting anything when the
    underlying run is blocked at its first script.
    """
    def _run_benchmark_live(exec_cmd, output_dir, tail_limit=200):
        output_dir = Path(output_dir)
        scripts_touched.append(str(exec_cmd[0]))
        output_dir.mkdir(parents=True, exist_ok=True)
        if fail_fast:
            raise ns["ScientificSmokeExecutionError"](
                "Full-9 blocked at first script (fail-fast short-circuit)"
            )
        (output_dir / "kaggle_console.log").write_text(
            "FAKE RUNNER console\n", encoding="utf-8"
        )
        if records is not None:
            _write_full9_evidence(
                output_dir,
                records=records,
                total_completed=len(records),
            )
        if block_after_write:
            raise ns["ScientificSmokeExecutionError"](
                "Full-9 blocked after the last matrix arm"
            )
        return []
    return _run_benchmark_live


def _full9_recording_runner(calls: list[list[str]]) -> Callable[..., Any]:
    """A launcher stand-in that records the exact subprocess command."""
    def _run_benchmark_live(exec_cmd, output_dir, tail_limit=200):
        calls.append(list(exec_cmd))
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "kaggle_console.log").write_text(
            "RECORDED RUNNER console\n", encoding="utf-8"
        )
        return []
    return _run_benchmark_live


def _full9_exec_cell_namespace(
    runner: Callable[..., Any],
    tmp_path: Path,
) -> dict[str, Any]:
    """Exec the real full9-execution-cell source with a controllable runner."""
    ns = _full9_verify_namespace()
    output_dir = tmp_path / "runs" / FULL9_OUTPUT_DIR_NAME
    ns.update({
        "sys": sys,
        "SCRIPT_PATH": str(tmp_path / "seven_arm_benchmark.py"),
        "QWEN_QUANTIZATION": "bnb-nf4",
        "HF_RESULTS_REPO_ID": "NabilDo/selective-regeneration-experiment-results",
        "SOURCE_COMMIT": FULL9_SOURCE_COMMIT,
        "DEPLOYED_BUILD_ID": FULL9_BUILD_ID,
        "DATA_DIR": tmp_path / "data",
        "MODEL_PATH": str(tmp_path / "models" / "qwen"),
        "FULL9_OUTPUT_DIR": output_dir,
        "_run_benchmark_live": runner,
    })
    nb = _canonical_notebook()
    exec_src = _cell_sources(nb)["full9-execution-cell"]
    exec(compile(exec_src, "full9-execution-cell", "exec"), ns)
    return ns


class TestFull9Exec01Boundary:
    """FULL9-EXEC-01: fail-closed boundary behavior of the real Full-9 cells."""

    DOCUMENTED_OUTCOMES = frozenset({
        "scientific_success",
        "scientific_failure",
        "engineering_blocker",
    })

    def test_full9_exec_01_runs_dir_creation_is_authoritative(
        self, tmp_path: Path
    ) -> None:
        setup_src = _cell_sources(_canonical_notebook())["setup-cell"]
        assert "output_dir.mkdir(parents=True, exist_ok=True)" in setup_src, (
            "_run_benchmark_live must authoritatively create the runs dir"
        )

        def _no_dir_runner(exec_cmd, output_dir, tail_limit=200):
            raise ImportError("os.makedirs unavailable - runs dir never created")

        with pytest.raises(ImportError):
            _full9_exec_cell_namespace(_no_dir_runner, tmp_path)
        evidence = tmp_path / "runs" / FULL9_OUTPUT_DIR_NAME
        assert not (evidence / "checkpoint.json").is_file(), (
            "no smoke evidence may be claimed when the runs dir was never created"
        )

    def test_full9_exec_01_runs_dir_created_but_no_smoke_record_rejected(
        self, tmp_path: Path
    ) -> None:
        ns = _full9_verify_namespace()
        scripts_touched: list[str] = []
        runner = _full9_script_runner(ns, scripts_touched=scripts_touched)
        executed = _full9_exec_cell_namespace(runner, tmp_path)
        evidence = tmp_path / "runs" / FULL9_OUTPUT_DIR_NAME
        assert evidence.is_dir(), (
            "runs dir must be created by the execution authority"
        )
        assert not (evidence / "run_records.jsonl").is_file(), (
            "boundary precondition: no smoke record may exist"
        )
        with pytest.raises(executed["ScientificSmokeExecutionError"]) as excinfo:
            executed["_verify_full9_evidence"](executed["FULL9_OUTPUT_DIR"])
        assert "missing or invalid" in str(excinfo.value)

    def test_full9_exec_01_fail_at_first_script_short_circuits(
        self, tmp_path: Path
    ) -> None:
        ns = _full9_verify_namespace()
        scripts_touched: list[str] = []
        runner = _full9_script_runner(
            ns,
            scripts_touched=scripts_touched,
            fail_fast=True,
            records=_exact_full9_records(),
        )
        with pytest.raises(ns["ScientificSmokeExecutionError"]):
            _full9_exec_cell_namespace(runner, tmp_path)
        assert len(scripts_touched) == 1, (
            "fail-fast must short-circuit: only the first script may be touched"
        )
        evidence = tmp_path / "runs" / FULL9_OUTPUT_DIR_NAME
        assert not (evidence / "run_records.jsonl").is_file(), (
            "fail-fast must not persist any smoke record"
        )

    def test_full9_exec_01_fail_after_full_matrix_persists_all_arms(
        self, tmp_path: Path
    ) -> None:
        ns = _full9_verify_namespace()
        records = _exact_full9_records()
        records[-1] = _full9_fail_record(
            records[-1]["scenario_id"],
            records[-1]["strategy_id"],
            kind="engineering_failure",
        )
        scripts_touched: list[str] = []
        runner = _full9_script_runner(
            ns,
            scripts_touched=scripts_touched,
            records=records,
            block_after_write=True,
        )
        with pytest.raises(ns["ScientificSmokeExecutionError"]):
            _full9_exec_cell_namespace(runner, tmp_path)
        evidence = tmp_path / "runs" / FULL9_OUTPUT_DIR_NAME
        persisted = [
            json.loads(line)
            for line in (evidence / "run_records.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        assert len(persisted) == 9, (
            "fail at the last arm must still persist all 9 matrix arms"
        )
        assert persisted[-1]["status"] == "failed"

    def test_full9_exec_01_engineering_blocker_blocks_full9(
        self, tmp_path: Path
    ) -> None:
        ns = _full9_verify_namespace()
        outcome = ns["_terminal_record_outcome"](
            _full9_fail_record(
                "todo-smoke-001", "monolithic", kind="engineering_failure"
            )
        )
        assert outcome == "engineering_blocker"
        records = _exact_full9_records()
        records[0] = _full9_fail_record(
            records[0]["scenario_id"],
            records[0]["strategy_id"],
            kind="engineering_failure",
        )
        evidence_dir = tmp_path / "runs" / FULL9_OUTPUT_DIR_NAME
        _write_full9_evidence(evidence_dir, records=records, total_completed=9)
        with pytest.raises(ns["ScientificSmokeExecutionError"]) as excinfo:
            ns["_verify_full9_evidence"](str(evidence_dir))
        assert "engineering blocker record: True" in str(excinfo.value)

    def test_full9_exec_01_terminal_outcome_enum_is_documented(self) -> None:
        ns = _full9_verify_namespace()
        terminal = ns["_terminal_record_outcome"]
        cases = [
            ("succeeded", None, "scientific_success"),
            ("failed", "engineering_failure", "engineering_blocker"),
            ("failed", "model_output", "scientific_failure"),
            ("failed", "infrastructure", "engineering_blocker"),
            ("timed_out", None, "engineering_blocker"),
            ("cancelled", None, "engineering_blocker"),
            ("unknown_status", None, "engineering_blocker"),
        ]
        for status, kind, expected in cases:
            record = _full9_fail_record(
                "todo-smoke-001", "monolithic", kind=kind or "x", status=status
            )
            got = terminal(record)
            assert got == expected, (
                f"status={status} kind={kind}: expected {expected}, got {got}"
            )
            assert got in self.DOCUMENTED_OUTCOMES

    def test_full9_exec_01_checkpoint_stop_policy_invariants(
        self, tmp_path: Path
    ) -> None:
        ns = _full9_verify_namespace()
        verifier = ns["_verify_full9_evidence"]
        for planned, completed in ((1, 0), (1, 1), (9, 2), (9, 9)):
            records = _exact_full9_records()[:completed]
            evidence_dir = tmp_path / "runs" / f"stop-{planned}-{completed}"
            _write_full9_evidence(
                evidence_dir,
                records=records,
                total_planned=planned,
                total_completed=completed,
            )
            cp = json.loads(
                (evidence_dir / "checkpoint.json").read_text(encoding="utf-8")
            )
            assert cp["total_planned"] == planned
            assert cp["total_completed"] == completed
            expected_status = "completed" if completed == planned else "incomplete"
            assert cp["completion_status"] == expected_status, (
                f"stop policy {planned}/{completed}: completion_status must be "
                f"{expected_status}"
            )
            if planned == completed == 9:
                verifier(str(evidence_dir))
            else:
                with pytest.raises(ns["ScientificSmokeExecutionError"]):
                    verifier(str(evidence_dir))

    def test_full9_exec_01_nonempty_output_fails_before_subprocess(
        self, tmp_path: Path
    ) -> None:
        """F1: an already-populated Full-9 output dir must fail closed before launch."""
        calls: list[list[str]] = []
        runner = _full9_recording_runner(calls)
        output_dir = tmp_path / "runs" / FULL9_OUTPUT_DIR_NAME
        output_dir.mkdir(parents=True, exist_ok=True)
        sentinel = output_dir / "sentinel.txt"
        sentinel.write_text("do-not-delete\n", encoding="utf-8")
        with pytest.raises(RuntimeError):
            _full9_exec_cell_namespace(runner, tmp_path)
        assert calls == [], (
            "subprocess launcher must not be called for a non-empty Full-9 output dir"
        )
        assert sentinel.is_file(), "pre-existing Full-9 output must never be cleaned"

    def test_full9_exec_01_empty_output_builds_one_exact_full9_launch(
        self, tmp_path: Path
    ) -> None:
        """F1: an empty/nonexistent output dir builds exactly one exact Full-9 launch."""
        calls: list[list[str]] = []
        runner = _full9_recording_runner(calls)
        _full9_exec_cell_namespace(runner, tmp_path)
        output_dir = tmp_path / "runs" / FULL9_OUTPUT_DIR_NAME
        assert len(calls) == 1, f"Full-9 launcher called {len(calls)} times, expected 1"
        _assert_full9_command_contract(
            calls[0],
            data_dir=tmp_path / "data",
            model_path=str(tmp_path / "models" / "qwen"),
            output_dir=output_dir,
        )

    def test_full9_exec_01_verification_accepts_success_and_scientific_failure_matrix(
        self, tmp_path: Path
    ) -> None:
        """F4: ACCEPT an exact 9-cell matrix that includes a scientific failure."""
        ns = _full9_verify_namespace()
        records = _exact_full9_records()
        records[4] = _full9_fail_record(
            "todo-smoke-002", "selective", kind="build", status="failed"
        )
        assert ns["_terminal_record_outcome"](records[4]) == "scientific_failure"
        evidence_dir = tmp_path / "runs" / FULL9_OUTPUT_DIR_NAME
        _write_full9_evidence(evidence_dir, records=records, total_completed=9)
        ns["_verify_full9_evidence"](str(evidence_dir))

    def test_full9_exec_01_verification_rejects_duplicate_or_missing_matrix_cell(
        self, tmp_path: Path
    ) -> None:
        """F4: REJECT nine records containing one duplicate and one missing pair."""
        ns = _full9_verify_namespace()
        records = _exact_full9_records()
        records[-1] = dict(records[0])
        records[-1]["run_id"] = "duplicate-cell"
        evidence_dir = tmp_path / "runs" / FULL9_OUTPUT_DIR_NAME
        _write_full9_evidence(evidence_dir, records=records, total_completed=9)
        with pytest.raises(ns["ScientificSmokeExecutionError"]) as excinfo:
            ns["_verify_full9_evidence"](str(evidence_dir))
        assert "exact 3x3 scenario x strategy matrix" in str(excinfo.value)

    def test_full9_exec_01_export_archives_only_corrected_full9_directory(
        self, tmp_path: Path
    ) -> None:
        """F5: the export archives ONLY the corrected Full-9 output tree."""
        ns = _full9_verify_namespace()
        runs = tmp_path / "runs"
        full9_dir = runs / FULL9_OUTPUT_DIR_NAME
        full9_dir.mkdir(parents=True)
        (full9_dir / "checkpoint.json").write_text("{}\n", encoding="utf-8")
        (full9_dir / "run_records.jsonl").write_text("", encoding="utf-8")
        dashboard = full9_dir / "dashboard"
        dashboard.mkdir()
        (dashboard / "dashboard_summary.json").write_text("{}\n", encoding="utf-8")

        canary = runs / "qwen14b_bnb_nf4_selective_canary"
        canary.mkdir()
        (canary / "canary_marker.txt").write_text("canary\n", encoding="utf-8")

        preflight = runs / "preflight"
        preflight.mkdir()
        (preflight / "kaggle_smoke_preflight.v1.json").write_text("{}\n", encoding="utf-8")

        archive_root = tmp_path / "working"
        bundle_path = ns["_export_full9_evidence"](
            str(full9_dir),
            archive_root=str(archive_root),
            timestamp="2026-08-08-000000",
        )
        assert bundle_path.name == "corrected-full9-wsfix-7f2a450-2026-08-08-000000.zip"
        assert bundle_path.is_file()
        with zipfile.ZipFile(bundle_path) as zf:
            names = zf.namelist()
        top_levels = {name.split("/")[0] for name in names}
        assert top_levels == {FULL9_OUTPUT_DIR_NAME}, top_levels
        assert f"{FULL9_OUTPUT_DIR_NAME}/checkpoint.json" in names
        assert f"{FULL9_OUTPUT_DIR_NAME}/dashboard/dashboard_summary.json" in names
        assert not any("canary" in name for name in names), names
        assert not any("preflight" in name for name in names), names

    def test_full9_exec_01_dashboard_bar_labels_present(self) -> None:
        """F8: every dashboard bar/barh container receives numeric data labels."""
        ns = _full9_verify_namespace()
        label_fn = ns["_label_bar_containers"]

        class _FakeContainer:
            def __init__(self, values: list[float]) -> None:
                self.datavalues = values

        class _FakeAxes:
            def __init__(self, containers: list[_FakeContainer]) -> None:
                self.containers = containers
                self.label_calls: list[tuple[_FakeContainer, dict[str, Any]]] = []

            def bar_label(self, container: _FakeContainer, **kwargs: Any) -> None:
                self.label_calls.append((container, kwargs))

        containers = [_FakeContainer([12000, 3]), _FakeContainer([600.5, 0])]
        ax = _FakeAxes(containers)
        label_fn(ax)
        assert len(ax.label_calls) == len(containers), ax.label_calls
        for container, kwargs in ax.label_calls:
            assert "labels" in kwargs, kwargs
            assert kwargs["labels"] == [f"{float(v):,.0f}" for v in container.datavalues]
        setup_src = _cell_sources(_canonical_notebook())["setup-cell"]
        for chart_file in (
            "status_by_strategy.png",
            "tokens_by_strategy.png",
            "model_calls_by_strategy.png",
            "duration_by_strategy.png",
            "failure_causes.png",
        ):
            assert chart_file in setup_src, f"dashboard chart missing: {chart_file}"
        assert setup_src.count("_label_bar_containers(ax)") >= 5, (
            "every dashboard bar/barh chart must call _label_bar_containers(ax)"
        )
