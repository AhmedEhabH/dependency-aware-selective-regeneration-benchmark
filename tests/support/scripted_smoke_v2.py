"""R5 scripted production-path harness.

Builds and runs nine real production-path cells (3 frozen Smoke V2 scenarios x 3
scientific arms x 1 repetition) using real production components: ScenarioLoader,
RepositoryLoader, ProfileGraphBuilder, descriptors_from_profile, make_strategy,
BenchmarkPipeline, BenchmarkRunner, SharedRegenerationExecutor, the real
migration generator, the real baseline validation command, the real isolated
scenario evaluator, real RunRecordData conversion, and the real RunRecordStore.

Engineering-only scripted orchestration proof; not Qwen-quality evidence.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from benchmark.checkpoint.persistence import (
    RunRecordData,
    RunRecordStore,
    compute_config_hash,
    make_run_id,
)
from benchmark.core.enums import RunStatus
from benchmark.core.models import RunRecord
from benchmark.execution.isolation import IsolationContext
from benchmark.execution.pipeline import BenchmarkPipeline, PipelineConfig
from benchmark.graph.builder import ProfileGraphBuilder
from benchmark.repositories.loader import RepositoryLoader
from benchmark.repositories.snapshot import stage_repository_snapshot
from benchmark.scenarios.loader import ScenarioLoader
from benchmark.selection.dependency_scope import descriptors_from_profile
from seven_arm_benchmark import _to_run_record_data, make_isolation, make_strategy
from tests.support.scripted_llm_backend import ScriptedSmokeV2Backend, ScriptedSmokeV2Mode

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "benchmark_data"
SCENARIOS_DIR = DATA_DIR / "scenarios"
BASELINE_TODO_SOURCE = DATA_DIR / "repositories" / "todo"

PROTOCOL_VERSION = "1.0"

VALIDATION_COMMAND: list[str] = [sys.executable, "manage.py", "test", "todo", "--verbosity", "0"]

SMOKE_V2_SCENARIO_IDS: tuple[str, ...] = (
    "todo-smoke-001",
    "todo-smoke-002",
    "todo-smoke-003",
)

SMOKE_V2_STRATEGY_NAMES: tuple[str, ...] = (
    "monolithic",
    "selective",
    "iterative_repository_agent",
)

SMOKE_V2_EDITABLE_PATHS: tuple[str, ...] = (
    "todo/models.py",
    "todo/serializers.py",
    "todo/views.py",
    "todo/permissions.py",
    "todo/urls.py",
)

SMOKE_V2_EXPECTED_SELECTION: dict[str, tuple[str, ...]] = {
    "todo-smoke-001": ("todo/models.py", "todo/serializers.py", "todo/views.py"),
    "todo-smoke-002": ("todo/models.py", "todo/views.py"),
    "todo-smoke-003": (
        "todo/models.py",
        "todo/serializers.py",
        "todo/permissions.py",
        "todo/views.py",
    ),
}

_MODE_FOR_STRATEGY: dict[str, ScriptedSmokeV2Mode] = {
    "monolithic": ScriptedSmokeV2Mode.MONOLITHIC,
    "selective": ScriptedSmokeV2Mode.SELECTIVE,
    "iterative_repository_agent": ScriptedSmokeV2Mode.AGENT,
}

_MIGRATION_DIR = "todo/migrations"

_CACHE_MARKERS: tuple[str, ...] = (
    "__pycache__",
    ".pytest_cache",
    "db.sqlite3",
    ".coverage",
    ".git",
)

_WORKSPACE_INTERNAL_PREFIXES: tuple[str, ...] = ("snapshots/", "runs/", "tmp/")

_EVIDENCE_COLUMNS: tuple[str, ...] = (
    "scenario",
    "strategy",
    "status",
    "selection_model_calls",
    "selection_tool_calls",
    "selection_inspected_file_count",
    "regeneration_model_calls",
    "repair_model_calls",
    "total_workflow_model_calls",
    "selection_total_tokens",
    "regeneration_total_tokens",
    "repair_total_tokens",
    "total_workflow_tokens",
    "selected_count",
    "generated_count",
    "migration_path",
    "baseline_pass",
    "evaluator_pass",
    "functional_pass",
    "snapshot_unchanged",
    "workspace_diff_count",
)


def _utc_now_str() -> str:
    return datetime.now(UTC).isoformat()


def _git_status_short() -> str:
    proc = subprocess.run(
        ["git", "status", "--short"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    return proc.stdout.strip()


def _git_head() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    return proc.stdout.strip() if proc.returncode == 0 else ""


def _is_excluded_path(rel: str) -> bool:
    if rel.endswith(".pyc"):
        return True
    for marker in _CACHE_MARKERS:
        if marker in rel:
            return True
    return any(rel.startswith(prefix) for prefix in _WORKSPACE_INTERNAL_PREFIXES)


def _rel_files(root: Path) -> list[str]:
    return sorted(
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file() and not _is_excluded_path(p.relative_to(root).as_posix())
    )


def snapshot_hash_of(root: str | Path) -> str:
    """Deterministic content hash of every meaningful file under *root*."""
    root_path = Path(root)
    hasher = hashlib.sha256()
    for rel in _rel_files(root_path):
        hasher.update(rel.encode("utf-8"))
        hasher.update((root_path / rel).read_bytes())
    return hasher.hexdigest()


def workspace_differences(workspace: Path, snapshot: Path) -> tuple[str, ...]:
    """Rel paths differing between the workspace and the immutable snapshot."""
    ws_root = workspace.resolve()
    snap_root = snapshot.resolve()
    ws_files = {
        p.relative_to(ws_root).as_posix()
        for p in ws_root.rglob("*")
        if p.is_file()
    }
    snap_files = {
        p.relative_to(snap_root).as_posix()
        for p in snap_root.rglob("*")
        if p.is_file()
    }
    diffs: list[str] = []
    for rel in sorted(ws_files | snap_files):
        if _is_excluded_path(rel):
            continue
        ws_path = ws_root / rel
        snap_path = snap_root / rel
        if ws_path.is_file() and snap_path.is_file():
            if ws_path.read_bytes() != snap_path.read_bytes():
                diffs.append(rel)
        elif ws_path.is_file() or snap_path.is_file():
            diffs.append(rel)
    return tuple(diffs)


class _ScenarioDirectoryProvider:
    """ScenarioProvider backed by the real ScenarioLoader."""

    def __init__(self, scenarios_dir: Path) -> None:
        self._loader = ScenarioLoader(scenarios_dir)
        self._all = self._loader.load_all()

    def get_scenario(self, scenario_id: str):
        for scenario in self._all:
            if scenario.scenario_id == scenario_id:
                return scenario
        raise KeyError(f"Scenario not found: {scenario_id}")

    def list_scenarios(self, repo_id: str | None = None):
        if repo_id is None:
            return list(self._all)
        return [s for s in self._all if s.repository == repo_id]


@dataclass
class ScriptedSmokeV2Cell:
    scenario_id: str
    strategy_name: str
    workspace: Path
    snapshot_root: Path
    snapshot_hash_before: str
    snapshot_hash_after: str
    workspace_diff_paths: tuple[str, ...]
    selected_paths: tuple[str, ...]
    migration_paths: tuple[str, ...]
    backend: ScriptedSmokeV2Backend
    isolation: IsolationContext
    config: PipelineConfig
    record: RunRecord
    record_data: RunRecordData


@dataclass
class ScriptedSmokeV2RunResult:
    cells: tuple[ScriptedSmokeV2Cell, ...]
    store: RunRecordStore
    git_status_before: str
    git_status_after: str


def _record_to_dict(record: RunRecord) -> dict[str, Any]:
    return {
        "run_id": record.identity.run_id,
        "scenario_id": record.identity.scenario_id,
        "strategy_name": record.identity.strategy_name,
        "status": record.status.value if hasattr(record.status, "value") else str(record.status),
        "duration_seconds": record.duration_seconds,
        "token_usage": {
            "prompt": record.token_usage.prompt_tokens,
            "completion": record.token_usage.completion_tokens,
            "total": record.token_usage.total_tokens,
        }
        if record.token_usage
        else {"prompt": 0, "completion": 0, "total": 0},
        "selection_prompt_tokens": record.selection_prompt_tokens,
        "selection_completion_tokens": record.selection_completion_tokens,
        "selection_total_tokens": record.selection_total_tokens,
        "selection_model_calls": record.selection_model_calls,
        "selection_duration_seconds": record.selection_duration_seconds,
        "selection_tool_calls": record.selection_tool_calls,
        "selection_tool_duration_seconds": record.selection_tool_duration_seconds,
        "selection_inspected_file_count": record.selection_inspected_file_count,
        "selection_tool_transcript": list(record.selection_tool_transcript),
        "regeneration_prompt_tokens": record.regeneration_prompt_tokens,
        "regeneration_completion_tokens": record.regeneration_completion_tokens,
        "regeneration_total_tokens": record.regeneration_total_tokens,
        "regeneration_model_calls": record.regeneration_model_calls,
        "regeneration_duration_seconds": record.regeneration_duration_seconds,
        "functional_validation_duration_seconds": record.functional_validation_duration_seconds,
        "functional_validation_passed": record.functional_validation_passed,
        "migration_generation_passed": record.migration_generation_passed,
        "migration_duration_seconds": record.migration_duration_seconds,
        "generated_migration_paths": list(record.generated_migration_paths),
        "baseline_validation_passed": record.baseline_validation_passed,
        "baseline_validation_duration_seconds": record.baseline_validation_duration_seconds,
        "scenario_evaluator_passed": record.scenario_evaluator_passed,
        "scenario_evaluator_duration_seconds": record.scenario_evaluator_duration_seconds,
        "scenario_evaluator_checks": list(record.scenario_evaluator_checks),
        "repair_prompt_tokens": record.repair_prompt_tokens,
        "repair_completion_tokens": record.repair_completion_tokens,
        "repair_total_tokens": record.repair_total_tokens,
        "repair_model_calls": record.repair_model_calls,
        "repair_duration_seconds": record.repair_duration_seconds,
        "repair_attempts": record.repair_attempts,
        "token_accounting_mode": record.token_accounting_mode,
        "total_workflow_tokens": record.total_workflow_tokens,
        "total_workflow_model_calls": record.total_workflow_model_calls,
        "total_workflow_duration_seconds": record.total_workflow_duration_seconds,
        "selected_artifact_count": record.selected_artifact_count,
        "regenerated_artifact_count": record.regenerated_artifact_count,
        "preserved_artifact_count": record.preserved_artifact_count,
        "unresolved_human_review_count": record.unresolved_human_review_count,
    }


def _build_record_data(
    record: RunRecord,
    *,
    scenario_id: str,
    strategy_name: str,
    config: PipelineConfig,
    max_attempts: int,
    started_at: str,
    ended_at: str,
) -> RunRecordData:
    config_hash = compute_config_hash(
        {
            "protocol_version": config.protocol_version,
            "validation_command": config.validation_command,
            "editable_artifact_paths": list(config.editable_artifact_paths),
        }
    )
    failure_details = [
        {
            "kind": f.failure_kind.value if hasattr(f.failure_kind, "value") else str(f.failure_kind),
            "message": f.message,
            "details": f.details,
            "stage": f.stage,
        }
        for f in record.failures
    ]
    return _to_run_record_data(
        _record_to_dict(record),
        run_id=make_run_id(scenario_id, strategy_name, 1, config.protocol_version, config_hash),
        profile="scientific-smoke-v2",
        repository_id="todo",
        scenario_id=scenario_id,
        strategy_id=strategy_name,
        repetition=1,
        model_identity="scripted-smoke-v2",
        dry_run=config.dry_run,
        protocol_version=config.protocol_version,
        source_commit=_git_head(),
        config_hash=config_hash,
        started_at=started_at,
        ended_at=ended_at,
        hw_id="cpu",
        sw_id=f"python={sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}|scripted",
        max_attempts=max_attempts,
        failure_details=failure_details,
    )


def _build_pipeline_config(
    staged_snapshot: Path,
    overrides: dict[str, Any] | None = None,
) -> PipelineConfig:
    kwargs = overrides or {}
    editable = tuple(kwargs.get("editable_artifact_paths", SMOKE_V2_EDITABLE_PATHS))
    return PipelineConfig(
        protocol_version=kwargs.get("protocol_version", PROTOCOL_VERSION),
        timeout_seconds=kwargs.get("timeout_seconds", 0),
        max_attempts_per_run=kwargs.get("max_attempts_per_run", 3),
        max_tokens_per_run=0,
        dry_run=kwargs.get("dry_run", False),
        enable_regeneration=kwargs.get("enable_regeneration", True),
        validation_command=kwargs.get("validation_command", VALIDATION_COMMAND),
        validation_timeout=kwargs.get("validation_timeout", 300),
        active_snapshot_root=str(staged_snapshot) if kwargs.get("active_snapshot_root", True) else None,
        editable_artifact_paths=editable,
        canonical_project_root=kwargs.get("canonical_project_root", PROJECT_ROOT),
        python_executable=kwargs.get("python_executable", sys.executable),
        max_completion_tokens_per_call=4096,
        max_total_workflow_tokens=0,
    )


def _pre_apply_migration(workspace: Path, scenario_id: str) -> None:
    from benchmark.execution.post_generation import run_post_generation_command
    from tests.support.evaluator_fixture_workspaces import get_correct_sources_for_scenario

    sources = get_correct_sources_for_scenario(scenario_id)
    for rel, content in sources.items():
        target = workspace / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
    result = run_post_generation_command(
        workspace,
        (sys.executable, "manage.py", "makemigrations", "todo", "--noinput"),
        require_new_migration=True,
        timeout=180,
    )
    if not result.passed:
        raise RuntimeError(f"pre-apply migration failed: {result.stderr or result.stdout}")


def build_scripted_smoke_v2_cell(
    scenario_id: str,
    strategy_name: str,
    *,
    base_dir: Path,
    store: RunRecordStore | None = None,
    data_dir: Path | None = None,
    fail_mode: str = "none",
    backend_kwargs: dict[str, Any] | None = None,
    config_kwargs: dict[str, Any] | None = None,
    mutate_snapshot: bool = False,
    pre_apply_migration: bool = False,
) -> ScriptedSmokeV2Cell:
    """Build, execute, and persist one non-dry production-path cell."""
    if scenario_id not in SMOKE_V2_SCENARIO_IDS:
        raise ValueError(f"Unsupported scenario_id: {scenario_id!r}")
    if strategy_name not in SMOKE_V2_STRATEGY_NAMES:
        raise ValueError(f"Unsupported strategy_name: {strategy_name!r}")

    data = data_dir or DATA_DIR
    provider = _ScenarioDirectoryProvider(data / "scenarios")

    profile = RepositoryLoader(data).load_manifest().get_profile("todo")
    if profile is None:
        raise RuntimeError("todo repository profile not found")
    graph = ProfileGraphBuilder().build_from_profile(profile)
    descriptors = descriptors_from_profile(tuple(profile.artifact_catalog), SMOKE_V2_EDITABLE_PATHS)

    cell_dir = Path(base_dir) / f"{scenario_id}__{strategy_name}"
    workspace = cell_dir / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    staged_snapshot = stage_repository_snapshot(
        source_root=BASELINE_TODO_SOURCE,
        snapshot_storage_root=workspace / "snapshots",
        repository_id="todo",
        revision_id=scenario_id,
    )

    snapshot_hash_before = snapshot_hash_of(staged_snapshot)

    if mutate_snapshot:
        (staged_snapshot / "todo" / "views.py").unlink()

    mode = _MODE_FOR_STRATEGY[strategy_name]
    backend = ScriptedSmokeV2Backend(mode, fail_mode=fail_mode, **(backend_kwargs or {}))

    isolation = make_isolation(workspace, active_snapshot_root=staged_snapshot)

    if pre_apply_migration:
        _pre_apply_migration(workspace, scenario_id)

    strategy = make_strategy(
        strategy_name,
        backend=backend,
        graph=graph,
        artifact_descriptors=descriptors,
    )

    config = _build_pipeline_config(staged_snapshot, config_kwargs)

    pipeline = BenchmarkPipeline(
        strategy=strategy,
        backend=backend,
        scenario_provider=provider,
        isolation=isolation,
        config=config,
        strategy_name=strategy_name,
    )

    started_at = _utc_now_str()
    record = pipeline.run_scenario_by_id(scenario_id)
    ended_at = _utc_now_str()

    snapshot_hash_after = snapshot_hash_of(staged_snapshot)

    diff = workspace_differences(workspace, staged_snapshot)
    editable_set = set(SMOKE_V2_EDITABLE_PATHS)
    selected_paths = tuple(sorted(p for p in diff if p in editable_set))
    migration_paths = tuple(sorted(p for p in diff if p.startswith(_MIGRATION_DIR + "/")))

    record_data = _build_record_data(
        record,
        scenario_id=scenario_id,
        strategy_name=strategy_name,
        config=config,
        max_attempts=config.max_attempts_per_run,
        started_at=started_at,
        ended_at=ended_at,
    )

    if store is not None:
        store.append(record_data)

    return ScriptedSmokeV2Cell(
        scenario_id=scenario_id,
        strategy_name=strategy_name,
        workspace=workspace,
        snapshot_root=staged_snapshot,
        snapshot_hash_before=snapshot_hash_before,
        snapshot_hash_after=snapshot_hash_after,
        workspace_diff_paths=diff,
        selected_paths=selected_paths,
        migration_paths=migration_paths,
        backend=backend,
        isolation=isolation,
        config=config,
        record=record,
        record_data=record_data,
    )


def run_scripted_smoke_v2_matrix(
    base_dir: Path,
    *,
    store: RunRecordStore | None = None,
    data_dir: Path | None = None,
) -> ScriptedSmokeV2RunResult:
    """Run the complete 3 scenarios x 3 arms x 1 repetition matrix."""
    base = Path(base_dir)
    base.mkdir(parents=True, exist_ok=True)
    if store is None:
        store = RunRecordStore(base / "records")
    git_before = _git_status_short()
    cells: list[ScriptedSmokeV2Cell] = []
    for scenario_id in SMOKE_V2_SCENARIO_IDS:
        for strategy_name in SMOKE_V2_STRATEGY_NAMES:
            cell = build_scripted_smoke_v2_cell(
                scenario_id,
                strategy_name,
                base_dir=base,
                store=store,
                data_dir=data_dir,
            )
            cells.append(cell)
    git_after = _git_status_short()
    return ScriptedSmokeV2RunResult(
        cells=tuple(cells),
        store=store,
        git_status_before=git_before,
        git_status_after=git_after,
    )


def assert_scripted_smoke_v2_record(cell: ScriptedSmokeV2Cell) -> None:
    """Assert the full positive-record contract for one cell."""
    record = cell.record
    data = cell.record_data

    assert record.status == RunStatus.succeeded
    assert data.model_metadata["dry_run"] == "False"
    assert record.total_workflow_model_calls > 0
    assert record.regeneration_model_calls > 0
    assert record.total_workflow_tokens > 0
    assert record.regenerated_artifact_count > 0
    assert record.migration_generation_passed is True
    assert len(record.generated_migration_paths) == 1
    assert record.baseline_validation_passed is True
    assert record.scenario_evaluator_passed is True
    assert record.functional_validation_passed is True
    assert record.failures == ()
    assert record.token_accounting_mode == "fixture_or_approximate"

    assert record.token_usage.total_tokens == record.total_workflow_tokens
    assert record.total_workflow_tokens == (
        record.selection_total_tokens + record.regeneration_total_tokens + record.repair_total_tokens
    )
    assert record.total_workflow_model_calls == (
        record.selection_model_calls + record.regeneration_model_calls + record.repair_model_calls
    )
    assert record.token_usage.prompt_tokens == (
        record.selection_prompt_tokens + record.regeneration_prompt_tokens + record.repair_prompt_tokens
    )
    assert record.token_usage.completion_tokens == (
        record.selection_completion_tokens
        + record.regeneration_completion_tokens
        + record.repair_completion_tokens
    )

    for name in (
        "selection",
        "regeneration",
        "repair",
        "functional_validation",
        "migration",
        "baseline_validation",
        "scenario_evaluator",
        "total_workflow",
    ):
        assert getattr(record, f"{name}_duration_seconds", -1) >= 0

    if cell.strategy_name == "monolithic":
        expected_generated = tuple(sorted(SMOKE_V2_EDITABLE_PATHS))
        expected_preserved = 0
        assert record.selection_model_calls == 0
        assert set(cell.selected_paths) == set(SMOKE_V2_EXPECTED_SELECTION[cell.scenario_id])
    elif cell.strategy_name == "selective":
        expected_generated = tuple(sorted(SMOKE_V2_EXPECTED_SELECTION[cell.scenario_id]))
        expected_preserved = len(SMOKE_V2_EDITABLE_PATHS) - len(expected_generated)
        assert set(cell.selected_paths) == set(expected_generated)
        assert len(cell.selected_paths) == len(expected_generated)
        assert set(cell.selected_paths) < set(SMOKE_V2_EDITABLE_PATHS)
    else:
        expected_generated = tuple(sorted(SMOKE_V2_EXPECTED_SELECTION[cell.scenario_id]))
        expected_preserved = len(SMOKE_V2_EDITABLE_PATHS) - len(expected_generated)
        assert 1 <= record.selection_model_calls <= 8
        assert record.selection_tool_calls > 0
        assert record.selection_inspected_file_count > 0
        assert record.selection_inspected_file_count <= 30
        assert cell.selected_paths
        assert set(cell.selected_paths) <= set(SMOKE_V2_EDITABLE_PATHS)
        assert record.selection_tool_transcript
        assert record.selection_model_calls <= 8

    assert tuple(cell.backend.generation_paths_requested) == expected_generated
    assert record.selected_artifact_count == len(expected_generated)
    assert record.regeneration_model_calls == len(expected_generated)
    assert record.regenerated_artifact_count == len(expected_generated)
    assert record.preserved_artifact_count == expected_preserved


def assert_scripted_smoke_v2_isolation(cell: ScriptedSmokeV2Cell) -> None:
    """Assert the full isolation contract for one cell."""
    workspace = cell.workspace.resolve()
    snapshot = cell.snapshot_root.resolve()

    assert workspace != snapshot
    assert cell.snapshot_hash_before == cell.snapshot_hash_after

    baseline_migrations = [
        rel
        for rel in _rel_files(snapshot)
        if rel.startswith(_MIGRATION_DIR + "/") and not rel.endswith("/__init__.py")
    ]
    assert len(baseline_migrations) == 3
    for rel in baseline_migrations:
        assert (workspace / rel).read_bytes() == (snapshot / rel).read_bytes()

    assert len(cell.migration_paths) == 1

    test_files = [rel for rel in _rel_files(snapshot) if rel.startswith("todo/tests/")]
    for rel in test_files:
        assert (workspace / rel).read_bytes() == (snapshot / rel).read_bytes()

    assert not (workspace / "tests" / "evaluator_assets").exists()
    assert not (workspace / "scenario_evaluator.py").exists()

    for rel in (
        "config/settings.py",
        "config/urls.py",
        "manage.py",
        "pytest.ini",
        "requirements.txt",
        "todo/urls.py",
    ):
        assert (workspace / rel).read_bytes() == (snapshot / rel).read_bytes()

    for rel in cell.selected_paths:
        assert rel in SMOKE_V2_EDITABLE_PATHS
        assert "db.sqlite3" not in rel
        assert "__pycache__" not in rel

    meaningful = set(cell.workspace_diff_paths)
    expected = set(cell.selected_paths) | set(cell.migration_paths)
    assert meaningful == expected, f"unexpected workspace diffs: {sorted(meaningful ^ expected)}"


def assert_scripted_smoke_v2_cell(cell: ScriptedSmokeV2Cell) -> None:
    assert_scripted_smoke_v2_record(cell)
    assert_scripted_smoke_v2_isolation(cell)


def format_scripted_smoke_v2_evidence_table(cells: list[ScriptedSmokeV2Cell]) -> str:
    """Deterministic evidence table with stable column order."""
    rows = ["\t".join(_EVIDENCE_COLUMNS)]
    for cell in cells:
        record = cell.record
        rows.append(
            "\t".join(
                [
                    cell.scenario_id,
                    cell.strategy_name,
                    record.status.value,
                    str(record.selection_model_calls),
                    str(record.selection_tool_calls),
                    str(record.selection_inspected_file_count),
                    str(record.regeneration_model_calls),
                    str(record.repair_model_calls),
                    str(record.total_workflow_model_calls),
                    str(record.selection_total_tokens),
                    str(record.regeneration_total_tokens),
                    str(record.repair_total_tokens),
                    str(record.total_workflow_tokens),
                    str(record.selected_artifact_count),
                    str(record.regenerated_artifact_count),
                    ",".join(cell.migration_paths) or "-",
                    str(record.baseline_validation_passed),
                    str(record.scenario_evaluator_passed),
                    str(record.functional_validation_passed),
                    str(cell.snapshot_hash_before == cell.snapshot_hash_after),
                    str(len(cell.workspace_diff_paths)),
                ]
            )
        )
    return "\n".join(rows)
