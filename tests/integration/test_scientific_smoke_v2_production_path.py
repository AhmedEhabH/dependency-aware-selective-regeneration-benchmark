"""R5 nine-record production-path integration tests.

Build order:
  Step 1 — support API + scripted backend + sources
  Step 2 — one Monolithic cell
  Step 3 — one Selective cell
  Step 4 — one Agent cell
  Step 5 — full 9-cell matrix
  Step 6 — persistence + negative controls
  leakage — source-inspection boundary rules
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime
from pathlib import Path

import pytest

from benchmark.checkpoint.persistence import RunRecordData, RunRecordIntegrityError, RunRecordStore
from benchmark.core.enums import FailureKind, RunStatus
from benchmark.core.models import FailureRecord, RunIdentity, RunRecord, TokenUsage
from benchmark.execution.regeneration import BUILT_IN_PROMPT_TEMPLATE
from benchmark.scenarios.loader import ScenarioLoader
from benchmark.strategies.iterative_agent import INITIAL_SYSTEM_PROMPT
from tests.support.evaluator_fixture_workspaces import get_correct_sources_for_scenario
from tests.support.scripted_llm_backend import (
    ScriptedSmokeV2Backend,
    ScriptedSmokeV2Mode,
    classify_scenario_id,
    deterministic_token_count,
    extract_artifact_path_from_generation_prompt,
)
from tests.support.scripted_smoke_v2 import (
    SMOKE_V2_SCENARIO_IDS,
    SMOKE_V2_STRATEGY_NAMES,
    assert_scripted_smoke_v2_cell,
    assert_scripted_smoke_v2_record,
    build_scripted_smoke_v2_cell,
    format_scripted_smoke_v2_evidence_table,
    run_scripted_smoke_v2_matrix,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCENARIOS_DIR = PROJECT_ROOT / "benchmark_data" / "scenarios"
BASELINE_TODO = PROJECT_ROOT / "benchmark_data" / "repositories" / "todo"
EDITABLE_PATHS = (
    "todo/models.py",
    "todo/serializers.py",
    "todo/views.py",
    "todo/permissions.py",
    "todo/urls.py",
)

_EXPECTED_AGENT_SELECTION = {
    "todo-smoke-001": ("todo/models.py", "todo/serializers.py", "todo/views.py"),
    "todo-smoke-002": ("todo/models.py", "todo/views.py"),
    "todo-smoke-003": (
        "todo/models.py",
        "todo/serializers.py",
        "todo/permissions.py",
        "todo/views.py",
    ),
}


def _requirement_delta(scenario_id: str) -> str:
    scenario = ScenarioLoader(SCENARIOS_DIR).load_scenario(SCENARIOS_DIR / f"{scenario_id}.yaml")
    return f"{scenario.requirement_before} -> {scenario.requirement_after}"


def _generation_prompt(scenario_id: str, artifact_path: str) -> str:
    return BUILT_IN_PROMPT_TEMPLATE.format(
        requirement_delta=_requirement_delta(scenario_id),
        artifact_path=artifact_path,
        language_hint="python",
        current_content="# baseline placeholder",
    )


def _agent_initial_prompt(scenario_id: str) -> str:
    scenario = ScenarioLoader(SCENARIOS_DIR).load_scenario(SCENARIOS_DIR / f"{scenario_id}.yaml")
    criteria = "\n".join(f"  - {c.description}" for c in scenario.acceptance_criteria)
    return INITIAL_SYSTEM_PROMPT.format(
        before=scenario.requirement_before,
        after=scenario.requirement_after,
        acceptance_criteria=criteria,
        editable_paths="\n".join(f"  - {p}" for p in EDITABLE_PATHS),
        TOOL_SCHEMA="",
    )


# ---------------------------------------------------------------------------
# Step 1 — support API and scripted backend
# ---------------------------------------------------------------------------


def test_r5_correct_sources_api_returns_fresh_copies():
    for scenario_id in ("todo-smoke-001", "todo-smoke-002", "todo-smoke-003"):
        first = get_correct_sources_for_scenario(scenario_id)
        second = get_correct_sources_for_scenario(scenario_id)
        assert isinstance(first, dict)
        assert first == second
        assert first is not second
        assert all(isinstance(v, str) and v.strip() for v in first.values())

    with pytest.raises(ValueError):
        get_correct_sources_for_scenario("todo-smoke-999")
    with pytest.raises(ValueError):
        get_correct_sources_for_scenario("")


def test_r5_correct_sources_api_does_not_expose_negative_variants():
    for scenario_id in ("todo-smoke-001", "todo-smoke-002", "todo-smoke-003"):
        sources = get_correct_sources_for_scenario(scenario_id)
        for _path, content in sources.items():
            assert "default=Priority.HIGH," not in content
            assert "instance.delete()" not in content
            assert "permission_classes = []" not in content


def test_r5_smoke_002_correct_sources_exactly_models_and_views():
    sources = get_correct_sources_for_scenario("todo-smoke-002")
    assert set(sources) == {"todo/models.py", "todo/views.py"}


def test_r5_scenario_classification_from_public_requirement():
    assert classify_scenario_id(_requirement_delta("todo-smoke-001")) == "todo-smoke-001"
    assert classify_scenario_id(_requirement_delta("todo-smoke-002")) == "todo-smoke-002"
    assert classify_scenario_id(_requirement_delta("todo-smoke-003")) == "todo-smoke-003"
    assert classify_scenario_id("no marker text here") == ""


def test_r5_artifact_path_extraction_from_generation_prompt():
    prompt = _generation_prompt("todo-smoke-001", "todo/models.py")
    assert extract_artifact_path_from_generation_prompt(prompt) == "todo/models.py"
    assert extract_artifact_path_from_generation_prompt("no artifact marker") == ""


def test_r5_deterministic_token_counting():
    assert deterministic_token_count("") == 1
    assert deterministic_token_count("a") == 1
    first = deterministic_token_count("hello world" * 50)
    second = deterministic_token_count("hello world" * 50)
    assert first == second
    assert first > 0


def test_r5_scripted_backend_generation_contract():
    backend = ScriptedSmokeV2Backend(ScriptedSmokeV2Mode.MONOLITHIC, baseline_repo=BASELINE_TODO)
    for scenario_id in ("todo-smoke-001", "todo-smoke-002", "todo-smoke-003"):
        correct = get_correct_sources_for_scenario(scenario_id)
        for artifact_path in EDITABLE_PATHS:
            prompt = _generation_prompt(scenario_id, artifact_path)
            expected_prompt_tokens = backend.count_prompt_tokens(prompt)
            response = asyncio.run(backend.generate(prompt=prompt, max_tokens=4096))
            usage = response.token_usage
            assert usage.prompt_tokens == expected_prompt_tokens > 0
            assert usage.completion_tokens > 0
            assert usage.completion_tokens <= 4096
            assert usage.total_tokens == usage.prompt_tokens + usage.completion_tokens
            if artifact_path in correct:
                assert response.text == correct[artifact_path]
            else:
                expected_baseline = (BASELINE_TODO / artifact_path).read_text(encoding="utf-8")
                assert response.text == expected_baseline
            assert response.text.startswith("```") is False


def test_r5_scripted_backend_diagnostics_and_reset():
    backend = ScriptedSmokeV2Backend(ScriptedSmokeV2Mode.MONOLITHIC, baseline_repo=BASELINE_TODO)
    assert backend.generate_call_count == 0
    assert backend.generation_call_count == 0
    assert backend.captured_max_tokens == []
    assert backend.generation_paths_requested == []

    for artifact_path in ("todo/models.py", "todo/views.py"):
        asyncio.run(backend.generate(prompt=_generation_prompt("todo-smoke-001", artifact_path), max_tokens=2048))

    assert backend.generate_call_count == 2
    assert backend.generation_call_count == 2
    assert backend.captured_max_tokens == [2048, 2048]
    assert backend.generation_paths_requested == ["todo/models.py", "todo/views.py"]

    backend.reset()
    assert backend.generate_call_count == 0
    assert backend.generation_call_count == 0
    assert backend.captured_max_tokens == []
    assert backend.generation_paths_requested == []


def test_r5_scripted_backend_agent_contract():
    backend = ScriptedSmokeV2Backend(ScriptedSmokeV2Mode.AGENT, baseline_repo=BASELINE_TODO)
    prompt = _agent_initial_prompt("todo-smoke-001")
    actions = []
    for _ in range(4):
        response = asyncio.run(backend.generate(prompt=prompt, max_tokens=4096))
        import json

        action = json.loads(response.text)
        actions.append(action["action"])
        assert response.token_usage.total_tokens > 0
        assert response.token_usage.completion_tokens <= 4096
        assert (
            response.token_usage.total_tokens
            == response.token_usage.prompt_tokens + response.token_usage.completion_tokens
        )
    assert actions == ["list_files", "search_text", "read_file", "final"]
    assert backend.agent_actions_returned[-1]["action"] == "final"
    assert set(backend.agent_actions_returned[-1]["selected_paths"]) == set(
        _EXPECTED_AGENT_SELECTION["todo-smoke-001"]
    )
    assert backend.generate_call_count == 4
    assert backend.generation_call_count == 0


def test_r5_scripted_backend_bounded_agent_selection_per_scenario():
    for scenario_id in ("todo-smoke-001", "todo-smoke-002", "todo-smoke-003"):
        backend = ScriptedSmokeV2Backend(ScriptedSmokeV2Mode.AGENT, baseline_repo=BASELINE_TODO)
        prompt = _agent_initial_prompt(scenario_id)
        final_paths = ()
        for _ in range(8):
            response = asyncio.run(backend.generate(prompt=prompt, max_tokens=4096))
            import json

            action = json.loads(response.text)
            if action["action"] == "final":
                final_paths = tuple(action["selected_paths"])
                break
        assert set(final_paths) == set(_EXPECTED_AGENT_SELECTION[scenario_id])
        assert backend.generate_call_count <= 8


# ---------------------------------------------------------------------------
# Steps 2-4 — one representative cell per arm through the real production path
# ---------------------------------------------------------------------------


def test_r5_representative_monolithic_cell_todo_smoke_001(tmp_path):
    cell = build_scripted_smoke_v2_cell(
        "todo-smoke-001",
        "monolithic",
        base_dir=tmp_path,
    )
    assert_scripted_smoke_v2_cell(cell)


def test_r5_representative_selective_cell_todo_smoke_001(tmp_path):
    cell = build_scripted_smoke_v2_cell(
        "todo-smoke-001",
        "selective",
        base_dir=tmp_path,
    )
    assert_scripted_smoke_v2_cell(cell)


def test_r5_representative_agent_cell_todo_smoke_001(tmp_path):
    cell = build_scripted_smoke_v2_cell(
        "todo-smoke-001",
        "iterative_repository_agent",
        base_dir=tmp_path,
    )
    assert_scripted_smoke_v2_cell(cell)


def test_r5_shared_snapshot_root_arm_child_topology_succeeds(tmp_path):
    """KAGGLE-SMOKE-V2: shared snapshot storage is accepted for every arm child.

    Reproduces the real failing topology:
      shared storage  = <root>/workspace/snapshots
      active snapshot = <root>/workspace/snapshots/todo/<revision>
      arm workspace   = <root>/workspace/<strategy>
    The isolation base must be the explicit shared storage root, never the
    arm-local `<arm>/snapshots` directory. Execution must reach successful
    generation and validation instead of an isolation failure.
    """
    from benchmark.repositories.snapshot import stage_repository_snapshot
    from seven_arm_benchmark import (
        ExecutionProfile,
        ScenarioProvider,
        _run_single_scenario_strategy,
        make_isolation,
    )
    from tests.support.scripted_llm_backend import ScriptedSmokeV2Backend, ScriptedSmokeV2Mode
    from tests.support.scripted_smoke_v2 import SMOKE_V2_EDITABLE_PATHS, VALIDATION_COMMAND

    root = tmp_path / "shared-topology"
    shared_workspace = root / "workspace"
    storage = shared_workspace / "snapshots"

    staged = stage_repository_snapshot(
        source_root=BASELINE_TODO,
        snapshot_storage_root=storage,
        repository_id="todo",
        revision_id="todo-smoke-001",
    )

    provider = ScenarioProvider(SCENARIOS_DIR)
    provider.get_scenario("todo-smoke-001")

    # 1. every child arm workspace accepts the shared storage root and gets the
    #    immutable active snapshot copied into its workspace.
    for strategy in SMOKE_V2_STRATEGY_NAMES:
        arm_ws = shared_workspace / strategy
        isolation = make_isolation(
            arm_ws,
            active_snapshot_root=staged,
            snapshot_storage_root=storage,
        )
        report = isolation.verify()
        assert report.passed, f"{strategy}: {report.message}"
        assert isolation.snapshot_base == storage.resolve()
        assert (arm_ws / "manage.py").is_file(), f"{strategy}: workspace source not populated"

    # 2. one full run through the shared-root topology succeeds end to end.
    arm_ws = shared_workspace / "monolithic"
    profile = ExecutionProfile(
        name="smoke-test",
        label="scientific-smoke-v2-shared-root",
        scenario_count=1,
        strategies=["monolithic"],
        repetitions=1,
        is_publication=False,
    )
    backend = ScriptedSmokeV2Backend(ScriptedSmokeV2Mode.MONOLITHIC, baseline_repo=BASELINE_TODO)
    record_dict, success = _run_single_scenario_strategy(
        scenario_id="todo-smoke-001",
        strategy_name="monolithic",
        scenario_provider=provider,
        dry_run=False,
        profile=profile,
        model_path=None,
        protocol_version="1.0",
        max_attempts=3,
        timeout_seconds=300,
        dep_graph=None,
        workspace_dir=arm_ws,
        backend_name="mock",
        validation_command=VALIDATION_COMMAND,
        max_tokens=0,
        active_snapshot_root=str(staged),
        snapshot_storage_root=storage,
        editable_artifact_paths=SMOKE_V2_EDITABLE_PATHS,
        _backend=backend,
    )
    assert success == 1, (
        f"expected success, got status={record_dict.get('status')} "
        f"failures={record_dict.get('failures')}"
    )
    assert record_dict.get("status") == "succeeded"
    assert record_dict.get("baseline_validation_passed") is True
    assert record_dict.get("migration_generation_passed") is True
    assert record_dict.get("scenario_evaluator_passed") is True
    assert record_dict.get("total_workflow_model_calls", 0) > 0


# ---------------------------------------------------------------------------
# Step 5 — full 3 scenarios x 3 arms x 1 repetition matrix
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def scripted_matrix(tmp_path_factory):
    base = tmp_path_factory.mktemp("r5_matrix")
    store = RunRecordStore(base / "records")
    result = run_scripted_smoke_v2_matrix(base / "matrix", store=store)
    assert len(result.cells) == 9
    assert result.git_status_before == result.git_status_after
    return result, store


def test_r5_nine_record_matrix(scripted_matrix, capsys):
    result, _store = scripted_matrix
    for cell in result.cells:
        assert_scripted_smoke_v2_cell(cell)

    run_ids = [cell.record_data.run_id for cell in result.cells]
    assert len(run_ids) == 9
    assert len(set(run_ids)) == 9

    # Deterministic evidence table printed only under -s; otherwise the run
    # ids and per-cell contracts above carry the evidence.
    print("scripted token magnitudes are engineering metrics and do not predict Qwen cost")
    print(format_scripted_smoke_v2_evidence_table(list(result.cells)))


# ---------------------------------------------------------------------------
# Step 6a — persistence round-trip and fail-closed integrity
# ---------------------------------------------------------------------------


def test_r5_persistence_round_trip(scripted_matrix):
    result, store = scripted_matrix
    loaded = store.load_all()
    assert len(loaded) == 9
    assert len({r.run_id for r in loaded}) == 9
    assert {r.scenario_id for r in loaded} == set(SMOKE_V2_SCENARIO_IDS)
    assert {r.strategy_id for r in loaded} == set(SMOKE_V2_STRATEGY_NAMES)
    assert {r.repetition for r in loaded} == {1}

    in_memory = {c.record_data.run_id: c.record_data for c in result.cells}
    for data in loaded:
        cell = next(c for c in result.cells if c.record_data.run_id == data.run_id)
        assert data == in_memory[data.run_id]
        assert data.status == cell.record.status.value
        assert data.scenario_id == cell.scenario_id
        assert data.strategy_id == cell.strategy_name
        assert data.selection_model_calls == cell.record.selection_model_calls
        assert data.selection_tool_calls == cell.record.selection_tool_calls
        assert data.selection_inspected_file_count == cell.record.selection_inspected_file_count
        assert data.regeneration_model_calls == cell.record.regeneration_model_calls
        assert data.repair_model_calls == cell.record.repair_model_calls
        assert data.total_workflow_model_calls == cell.record.total_workflow_model_calls
        assert data.selection_total_tokens == cell.record.selection_total_tokens
        assert data.regeneration_total_tokens == cell.record.regeneration_total_tokens
        assert data.repair_total_tokens == cell.record.repair_total_tokens
        assert data.total_workflow_tokens == cell.record.total_workflow_tokens
        assert data.generated_migration_paths == list(cell.record.generated_migration_paths)
        assert data.scenario_evaluator_checks == list(cell.record.scenario_evaluator_checks)
        assert data.migration_generation_passed == cell.record.migration_generation_passed
        assert data.baseline_validation_passed == cell.record.baseline_validation_passed
        assert data.scenario_evaluator_passed == cell.record.scenario_evaluator_passed


def test_r5_persistence_failure_fields_round_trip(tmp_path):
    store = RunRecordStore(tmp_path / "records")
    cell = build_scripted_smoke_v2_cell(
        "todo-smoke-001",
        "monolithic",
        base_dir=tmp_path / "cells",
        store=store,
        fail_mode="zero_calls",
        config_kwargs={"max_attempts_per_run": 1},
    )
    assert cell.record.status == RunStatus.failed
    assert cell.record_data.failure_details

    loaded = store.load_all()
    assert len(loaded) == 1
    assert loaded[0].run_id == cell.record_data.run_id
    assert loaded[0].status == "failed"
    assert loaded[0].failure_details == cell.record_data.failure_details
    assert loaded[0].failure_details[0]["stage"] == "regeneration"


def test_r5_persistence_append_idempotent(scripted_matrix):
    result, store = scripted_matrix
    for cell in result.cells:
        store.append(cell.record_data)
    assert store.count() == 9


def test_r5_persistence_conflict_raises_integrity_error(scripted_matrix):
    result, store = scripted_matrix
    first = result.cells[0].record_data
    conflicting = RunRecordData(**{**first.__dict__, "total_workflow_tokens": first.total_workflow_tokens + 1})
    with pytest.raises(RunRecordIntegrityError):
        store.append(conflicting)


def _reconstruct_run_record(data: RunRecordData) -> RunRecord:
    """Reconstruct a RunRecord from persisted RunRecordData.

    The RunRecord constructor validates metric identities, so this is the
    production validation that detects corrupted persisted totals.
    """
    metric_fields = (
        "selection_prompt_tokens", "selection_completion_tokens", "selection_total_tokens",
        "selection_model_calls", "selection_duration_seconds",
        "selection_tool_calls", "selection_tool_duration_seconds",
        "selection_inspected_file_count", "selection_tool_transcript",
        "regeneration_prompt_tokens", "regeneration_completion_tokens",
        "regeneration_total_tokens", "regeneration_model_calls", "regeneration_duration_seconds",
        "functional_validation_duration_seconds", "functional_validation_passed",
        "migration_generation_passed", "migration_duration_seconds", "generated_migration_paths",
        "baseline_validation_passed", "baseline_validation_duration_seconds",
        "scenario_evaluator_passed", "scenario_evaluator_duration_seconds", "scenario_evaluator_checks",
        "repair_prompt_tokens", "repair_completion_tokens", "repair_total_tokens",
        "repair_model_calls", "repair_duration_seconds", "repair_attempts", "token_accounting_mode",
        "total_workflow_tokens", "total_workflow_model_calls", "total_workflow_duration_seconds",
        "selected_artifact_count", "regenerated_artifact_count",
        "preserved_artifact_count", "unresolved_human_review_count",
    )
    kwargs = {name: getattr(data, name) for name in metric_fields}
    return RunRecord(
        identity=RunIdentity(
            run_id=data.run_id,
            protocol_version=data.protocol_version,
            repository_commit_sha=data.source_commit or "00000000000000000000000000000000",
            scenario_id=data.scenario_id,
            strategy_name=data.strategy_id,
        ),
        status=RunStatus(data.status),
        duration_seconds=data.duration_seconds,
        token_usage=TokenUsage(
            prompt_tokens=data.token_usage["prompt"],
            completion_tokens=data.token_usage["completion"],
            total_tokens=data.token_usage["total"],
        ),
        failures=tuple(
            FailureRecord(
                failure_kind=FailureKind(f["kind"]),
                message=f["message"],
                details=f.get("details", ""),
                stage=f.get("stage", ""),
            )
            for f in data.failure_details
        ),
        **kwargs,
    )


def test_r5_persistence_zeroed_metrics_detected(scripted_matrix):
    result, store = scripted_matrix
    loaded = store.load_all()
    assert loaded
    _reconstruct_run_record(loaded[0])

    zeroed = RunRecordData(**{**loaded[0].__dict__, "total_workflow_tokens": 0, "total_workflow_model_calls": 0})
    with pytest.raises(ValueError, match="total_workflow"):
        _reconstruct_run_record(zeroed)


# ---------------------------------------------------------------------------
# Step 6b — negative controls (one focused fail-closed cell per condition)
# ---------------------------------------------------------------------------


def _failure(record: RunRecord) -> FailureRecord:
    assert record.failures, f"expected a failure, got status={record.status} failures={record.failures}"
    return record.failures[0]


def test_r5_negative_dry_run(tmp_path):
    cell = build_scripted_smoke_v2_cell(
        "todo-smoke-001",
        "monolithic",
        base_dir=tmp_path,
        config_kwargs={"dry_run": True},
    )
    assert cell.record.status == RunStatus.succeeded
    assert cell.record_data.model_metadata["dry_run"] == "True"
    assert cell.record.total_workflow_model_calls == 0
    assert cell.record.regenerated_artifact_count == 0
    assert cell.record.baseline_validation_passed is None
    assert not cell.workspace_diff_paths


def test_r5_negative_no_regeneration(tmp_path):
    cell = build_scripted_smoke_v2_cell(
        "todo-smoke-001",
        "monolithic",
        base_dir=tmp_path,
        config_kwargs={"enable_regeneration": False},
    )
    assert cell.record.status == RunStatus.succeeded
    assert cell.record_data.model_metadata["dry_run"] == "False"
    assert cell.record.regeneration_model_calls == 0
    assert cell.record.regenerated_artifact_count == 0
    assert cell.record.baseline_validation_passed is None


def test_r5_negative_zero_generation_calls(tmp_path):
    cell = build_scripted_smoke_v2_cell(
        "todo-smoke-001",
        "monolithic",
        base_dir=tmp_path,
        fail_mode="zero_calls",
    )
    assert cell.record.status == RunStatus.failed
    failure = _failure(cell.record)
    assert failure.stage == "regeneration"
    assert failure.failure_kind == FailureKind.model_output
    assert "zero generation calls" in failure.message
    assert any(f.stage == "generation_guard" for f in cell.record.failures)
    assert cell.backend.generation_call_count == 0


def test_r5_negative_empty_source(tmp_path):
    cell = build_scripted_smoke_v2_cell(
        "todo-smoke-001",
        "monolithic",
        base_dir=tmp_path,
        fail_mode="empty_source",
        config_kwargs={"max_attempts_per_run": 1},
    )
    assert cell.record.status == RunStatus.failed
    failure = _failure(cell.record)
    assert failure.stage == "regeneration"
    assert "Empty generation" in failure.message
    assert any(f.stage == "generation_guard" for f in cell.record.failures)


def test_r5_negative_no_selected_artifacts(tmp_path):
    cell = build_scripted_smoke_v2_cell(
        "todo-smoke-001",
        "selective",
        base_dir=tmp_path,
        config_kwargs={"editable_artifact_paths": ()},
    )
    assert cell.record.status == RunStatus.failed
    failure = _failure(cell.record)
    assert failure.stage == "runner"
    assert failure.failure_kind == FailureKind.infrastructure
    assert "non-empty" in failure.message


def test_r5_negative_no_new_migration(tmp_path):
    cell = build_scripted_smoke_v2_cell(
        "todo-smoke-001",
        "monolithic",
        base_dir=tmp_path,
        pre_apply_migration=True,
        config_kwargs={"max_attempts_per_run": 1},
    )
    assert cell.record.status == RunStatus.failed
    failure = _failure(cell.record)
    assert failure.stage == "migration_generation"
    assert cell.record.migration_generation_passed is False


def test_r5_negative_vacuous_baseline_absent_evaluator(tmp_path):
    empty_cpr = tmp_path / "empty_cpr"
    empty_cpr.mkdir()
    cell = build_scripted_smoke_v2_cell(
        "todo-smoke-001",
        "monolithic",
        base_dir=tmp_path,
        config_kwargs={
            "validation_command": [sys.executable, "-c", "pass"],
            "canonical_project_root": empty_cpr,
            "max_attempts_per_run": 1,
        },
    )
    assert cell.record.status == RunStatus.failed
    failure = _failure(cell.record)
    assert failure.stage == "scenario_evaluator"
    assert cell.record.baseline_validation_passed is True
    assert cell.record.scenario_evaluator_passed is False


def test_r5_negative_evaluator_execution_skipped(tmp_path):
    cell = build_scripted_smoke_v2_cell(
        "todo-smoke-001",
        "monolithic",
        base_dir=tmp_path,
        config_kwargs={
            "python_executable": str(tmp_path / "nonexistent_python"),
            "max_attempts_per_run": 1,
        },
    )
    assert cell.record.status == RunStatus.failed
    failure = _failure(cell.record)
    assert failure.stage == "scenario_evaluator"
    assert "evaluator" in failure.message.lower()
    assert cell.record.scenario_evaluator_passed is False


def test_r5_negative_mutated_snapshot(tmp_path):
    cell = build_scripted_smoke_v2_cell(
        "todo-smoke-001",
        "monolithic",
        base_dir=tmp_path,
        mutate_snapshot=True,
    )
    assert cell.record.status == RunStatus.failed
    failure = _failure(cell.record)
    assert failure.stage == "runner"
    assert "views.py" in failure.message
    assert cell.snapshot_hash_before != cell.snapshot_hash_after


def test_r5_persisted_timestamps_truthful_timezone_aware(scripted_matrix):
    _result, store = scripted_matrix
    loaded = store.load_all()
    assert len(loaded) == 9
    for data in loaded:
        assert data.started_at and data.ended_at
        started = datetime.fromisoformat(data.started_at)
        ended = datetime.fromisoformat(data.ended_at)
        assert started.tzinfo is not None
        assert ended.tzinfo is not None
        assert started <= ended


def test_r5_negative_zeroed_persisted_metrics(tmp_path):
    store = RunRecordStore(tmp_path / "records")
    cell = build_scripted_smoke_v2_cell(
        "todo-smoke-001",
        "monolithic",
        base_dir=tmp_path / "cells",
        store=store,
    )
    assert_scripted_smoke_v2_record(cell)

    zeroed = RunRecordData(
        **{**cell.record_data.__dict__, "total_workflow_tokens": 0, "total_workflow_model_calls": 0}
    )
    with pytest.raises(ValueError, match="total_workflow"):
        _reconstruct_run_record(zeroed)


# ---------------------------------------------------------------------------
# Leakage controls — source-inspection boundary rules only
# ---------------------------------------------------------------------------

_BACKEND_SOURCE = Path(__file__).resolve().parent.parent / "support" / "scripted_llm_backend.py"
_HARNESS_SOURCE = Path(__file__).resolve().parent.parent / "support" / "scripted_smoke_v2.py"
_PRODUCTION_SRC = Path(__file__).resolve().parent.parent.parent / "src" / "benchmark"
_KAGGLE_BENCHMARK = (
    Path(__file__).resolve().parent.parent.parent / "kaggle_upload" / "code" / "seven_arm_benchmark.py"
)


def _source_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _ast_names(path: Path) -> set[str]:
    """All Name/Attribute identifiers in executable code (docstrings excluded)."""
    import ast

    tree = ast.parse(_source_text(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
    return names


def _imported_module_names(path: Path) -> set[str]:
    """Module names from import statements only."""
    import ast

    tree = ast.parse(_source_text(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_r5_leakage_scripted_backend_source_omits_ground_truth():
    names = _ast_names(_BACKEND_SOURCE)
    assert "expected_affected_artifacts" not in names
    assert "GroundTruth" not in names
    assert "ground_truth" not in names


def test_r5_leakage_scripted_backend_source_no_evaluator_imports():
    modules = _imported_module_names(_BACKEND_SOURCE)
    assert not any(m.startswith("tests.evaluator_assets") for m in modules)
    assert "benchmark.execution.scenario_evaluator" not in modules
    assert "benchmark.evaluation" not in modules


def test_r5_leakage_scripted_backend_source_no_strategy_imports():
    modules = _imported_module_names(_BACKEND_SOURCE)
    assert not any(m.startswith("benchmark.strategies") for m in modules)
    assert not any(m.startswith("benchmark.execution") for m in modules)
    assert not any(m.startswith("seven_arm_benchmark") for m in modules)


def test_r5_leakage_production_source_no_tests_support():
    for path in sorted(_PRODUCTION_SRC.rglob("*.py")):
        source = _source_text(path)
        assert "tests.support" not in source, path
        assert "scripted_smoke_v2" not in source, path
        assert "scripted_llm_backend" not in source, path


def test_r5_leakage_production_backend_registry_excludes_scripted():
    llm_dir = _PRODUCTION_SRC / "llm"
    for path in sorted(llm_dir.rglob("*.py")):
        source = _source_text(path)
        assert "scripted" not in source, path
    source = _source_text(Path(__file__).resolve().parent.parent.parent / "seven_arm_benchmark.py")
    assert "scripted_smoke_v2" not in source
    assert "scripted_llm_backend" not in source


def test_r5_leakage_kaggle_provider_choices_exclude_scripted():
    source = _source_text(_KAGGLE_BENCHMARK)
    assert "scripted" not in source
    assert "scripted_smoke_v2" not in source
    assert "scripted_llm_backend" not in source


def test_r5_leakage_agent_tools_reject_evaluator_paths(tmp_path):
    from benchmark.strategies.repository_tools import RepositoryTools

    cell = build_scripted_smoke_v2_cell(
        "todo-smoke-001",
        "monolithic",
        base_dir=tmp_path,
    )
    tools = RepositoryTools(cell.workspace)
    read = tools.read_file("tests/evaluator_assets/todo_smoke_001_checks.py")
    assert read.ok is False
    listing = tools.list_files(".")
    assert "evaluator_assets" not in listing.output
    assert not any("evaluator" in line for line in tools.read_file("todo/views.py").output.lower().splitlines())


# ---------------------------------------------------------------------------
# Step 7 — R7B shared-backend factory-count regression
# ---------------------------------------------------------------------------


def test_r7b_nine_cell_plan_creates_one_backend_object(tmp_path, monkeypatch):
    """A nine-cell dry-run plan must create exactly one backend instance.

    The V2 Smoke failures included repeated model loads per run causing T4
    OOM. The runtime must create one shared backend before the execution loop
    and reuse it across all runs.
    """
    import seven_arm_benchmark as cli

    original_make_backend = cli.make_backend
    calls: list[int] = []

    def counting_backend(*args, **kwargs):  # type: ignore[no-untyped-def]
        calls.append(1)
        return original_make_backend(*args, **kwargs)

    monkeypatch.setattr(cli, "make_backend", counting_backend)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "seven_arm_benchmark.py",
            "--dry-run",
            "--profile", "scientific-smoke-v2",
            "--data-dir", str(PROJECT_ROOT / "benchmark_data"),
            "--output-dir", str(tmp_path / "runs"),
            "--source-commit", "b6a203183572e6ebd5531c83eb0c81ecd7419ec8",
            "--deployed-build-id", "b6a2031",
            "--max-attempts", "3",
            "--max-completion-tokens-per-call", "1024",
            "--max-total-workflow-tokens", "0",
            "--timeout", "300",
        ],
    )

    result = cli.main()
    assert result == 0
    assert len(calls) == 1, f"expected exactly one backend factory call, got {len(calls)}"


def test_r7c_missing_module_is_infrastructure_nonrepairable_with_no_repair(tmp_path):
    """Replays the observed real-run root cause: missing Django dependency.

    The V2 real run treated ``ModuleNotFoundError`` as repairable code and
    looped the repair budget pointlessly. R7C must classify it as
    infrastructure_nonrepairable, stop immediately, and issue zero repair
    model calls.
    """
    from tests.support.scripted_smoke_v2 import build_scripted_smoke_v2_cell

    cell = build_scripted_smoke_v2_cell(
        "todo-smoke-001",
        "monolithic",
        base_dir=tmp_path,
        config_kwargs={
            "validation_command": [
                sys.executable,
                "-c",
                "raise ModuleNotFoundError(\"No module named 'django'\")",
            ],
            "max_attempts_per_run": 3,
        },
    )
    record = cell.record
    assert record.status == RunStatus.failed
    assert record.failures, "expected at least one FailureRecord"
    first = record.failures[0]
    assert first.failure_kind == FailureKind.infrastructure_nonrepairable
    assert first.stage in ("scenario_evaluator", "baseline_validation", "migration_generation")
    assert sum(
        1
        for failure in record.failures
        if failure.failure_kind == FailureKind.infrastructure_nonrepairable
    ) == 1
    assert "No module named 'django'" in first.message or "No module named 'django'" in first.details
    assert "exit_code=" in first.details
    assert record.repair_model_calls == 0
    assert record.repair_attempts == 0
    assert record.repair_total_tokens == 0
    # Initial monolithic generation touches all editable paths; zero repair calls.
    assert record.regeneration_model_calls == 5
    assert record.total_workflow_model_calls == 5


def test_r7c_preserve_only_artifact_change_is_rejected(tmp_path):
    """The frozen scope contract rejects out-of-scope edits to preserve files.

    The executor receives a RegenerationScenarioContext whose expected_actions
    mark only the declared files as modify/create. A plan that tries to
    regenerate a preserve-only file must be rejected (byte-identity enforced)
    instead of silently overwriting it.
    """
    from benchmark.core.enums import ActionKind, ArtifactType
    from benchmark.core.models import ArtifactRef, RegenerationScenarioContext
    from benchmark.execution.isolation import IsolationContext
    from benchmark.execution.regeneration import SharedRegenerationExecutor
    from benchmark.repositories.workspace import WorkspacePath
    from benchmark.selection.planner import RegenerationPlan
    from tests.support.scripted_llm_backend import ScriptedSmokeV2Backend, ScriptedSmokeV2Mode

    ws_root = tmp_path / "ws"
    (ws_root / "todo").mkdir(parents=True)
    (ws_root / "todo" / "views.py").write_text("ORIGINAL_VIEWS", encoding="utf-8")
    workspace = WorkspacePath(root=str(ws_root))
    iso = IsolationContext(
        workspace=workspace,
        snapshot_base=tmp_path / "snap",
        active_snapshot_root=tmp_path / "active",
    )

    plan = RegenerationPlan(
        ordered_artifacts=(ArtifactRef(path="todo/views.py", artifact_type=ArtifactType.source),),
        actions={"todo/views.py": ActionKind.regenerate},
    )
    ctx = RegenerationScenarioContext(
        scenario_id="todo-smoke-001",
        requirement_before="before",
        requirement_after="after",
        expected_actions=(("todo/models.py", "modify"),),
    )
    backend = ScriptedSmokeV2Backend(ScriptedSmokeV2Mode.MONOLITHIC, baseline_repo=BASELINE_TODO)
    executor = SharedRegenerationExecutor(backend)
    result = executor.execute(
        plan, iso, requirement_delta="before -> after", scenario_context=ctx,
    )
    assert result.artifacts
    artifact = result.artifacts[0]
    assert artifact.status == "rejected"
    assert any("preserve" in f for f in result.failures)
    assert (ws_root / "todo" / "views.py").read_text("utf-8") == "ORIGINAL_VIEWS"
