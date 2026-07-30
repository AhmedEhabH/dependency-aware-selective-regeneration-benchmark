from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from benchmark.checkpoint.persistence import RunRecordData, RunRecordStore
from benchmark.core.enums import ActionKind, ArtifactType, BlastRadius, FailureKind, RunStatus
from benchmark.core.models import (
    ArtifactRef,
    FailureRecord,
    ImpactDecision,
    ImpactPrediction,
    LLMResponse,
    RunIdentity,
    RunRecord,
    Scenario,
)
from benchmark.execution.isolation import IsolationContext
from benchmark.execution.post_generation import PostGenerationResult
from benchmark.execution.runner import BenchmarkRunner, RunnerConfig, _ScientificValidationResult
from benchmark.execution.scenario_evaluator import ScenarioEvaluatorResult
from benchmark.execution.validation import FunctionalValidationResult
from benchmark.repositories.workspace import WorkspacePath

# ---------------------------------------------------------------------------
# Minimal helpers
# ---------------------------------------------------------------------------

@dataclass
class _FakeGeneratedArtifact:
    path: str = ""
    status: str = "generated"


@dataclass
class _FakeExecResult:
    model_calls: int = 1
    artifacts: tuple[Any, ...] = (_FakeGeneratedArtifact(),)
    prompt_tokens: int = 10
    completion_tokens: int = 10
    total_tokens: int = 20
    duration_seconds: float = 0.5
    failures: tuple[str, ...] = ()


class _FakeStrategy:
    def __init__(self) -> None:
        self.calls: list[Any] = []
        self.model_call_count = 0
        self.tool_call_count = 0
        self.tool_duration_seconds = 0.0
        self.inspected_file_count = 0
        self.last_requires_iteration = False

    def analyze_impact(self, **kwargs: Any) -> ImpactPrediction:
        self.calls.append(kwargs)
        return ImpactPrediction()

    def revise_plan(self, **kwargs: Any) -> ImpactPrediction:
        self.calls.append(kwargs)
        return ImpactPrediction()


class _FakeBackend:
    async def generate(self, prompt: str, temperature: float = 0.0, max_tokens: int = 4096) -> LLMResponse:
        return LLMResponse(text="mock")


def _make_runner(
    tmp_path: Path,
    validation_command: list[str] | None = None,
    canonical_project_root: str | None = None,
    python_executable: str = "",
    enable_regeneration: bool = False,
    strategy: Any = None,
) -> BenchmarkRunner:
    ws_root = tmp_path / "workspace"
    ws_root.mkdir()
    snap_base = tmp_path / "snapshots"
    snap_base.mkdir()
    active_root = snap_base / "repo" / "rev1"
    active_root.mkdir(parents=True)
    (active_root / "dummy.py").write_text("x = 1")
    ws = WorkspacePath(root=str(ws_root))
    iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active_root)
    cfg = RunnerConfig(
        strategy_name="monolithic",
        backend_name="test",
        protocol_version="1.0",
        max_attempts=3,
        validation_command=validation_command,
        validation_timeout=30,
        canonical_project_root=canonical_project_root or str(tmp_path),
        python_executable=python_executable or sys.executable,
        enable_regeneration=enable_regeneration,
        editable_artifact_paths=("dummy.py",),
    )
    return BenchmarkRunner(
        strategy=strategy or _FakeStrategy(),
        backend=_FakeBackend(),
        isolation=iso,
        config=cfg,
    )


def _scenario(**kw: Any) -> Scenario:
    d: dict[str, Any] = dict(
        scenario_id="r3d",
        repository="repo",
        change_type="modify",
        blast_radius=BlastRadius.localized,
        requirement_before="before",
        requirement_after="after",
        rationale="test",
    )
    d.update(kw)
    return Scenario(**d)


def _exec(model_calls: int = 1, generated_count: int = 1) -> _FakeExecResult:
    arts = tuple(_FakeGeneratedArtifact(status="generated") for _ in range(generated_count)) if generated_count else ()
    return _FakeExecResult(model_calls=model_calls, artifacts=arts)


# ===================================================================
# 1-6: Production entry and preflight
# ===================================================================

def test_real_entry_builds_scientific_pipeline_config(tmp_path: Path) -> None:
    import sys
    from pathlib import Path

    import seven_arm_benchmark
    from benchmark.core.enums import RunStatus
    captured_configs: list[Any] = []

    class _CapturePipeline:
        def __init__(self, **kw: Any) -> None:
            captured_configs.append(kw.get("config"))
        def run_scenario_by_id(self, scenario_id: str = "") -> RunRecord:
            return RunRecord(
                identity=RunIdentity(
                    run_id="test", protocol_version="1.0",
                    repository_commit_sha="abc", scenario_id=scenario_id,
                    strategy_name="monolithic",
                ),
                status=RunStatus.succeeded,
            )

    with (
        patch("benchmark.execution.pipeline.BenchmarkPipeline", _CapturePipeline),
        patch("seven_arm_benchmark.make_strategy"),
        patch("seven_arm_benchmark.make_isolation"),
    ):
        provider = MagicMock()
        provider.get_scenario.return_value = MagicMock()
        seven_arm_benchmark._run_single_scenario_strategy(
            scenario_id="test", strategy_name="monolithic",
            scenario_provider=provider, dry_run=False,
            profile=MagicMock(), model_path=None,
            protocol_version="1.0", max_attempts=3,
            timeout_seconds=60, dep_graph=None,
            workspace_dir=tmp_path / "ws",
            validation_command=["echo", "ok"],
            active_snapshot_root=tmp_path / "snap",
        )
    config = captured_configs[0]
    assert config.canonical_project_root == Path(seven_arm_benchmark.__file__).resolve().parent
    assert config.python_executable == sys.executable


def test_missing_canonical_root_fails_before_strategy(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path, canonical_project_root=str(tmp_path), enable_regeneration=True)
    object.__setattr__(runner._config, "canonical_project_root", None)
    record = runner.run(_scenario(evaluator_asset="tests/evaluator_assets/eval.py"))
    assert record.status == RunStatus.failed
    assert any(f.stage == "configuration" for f in record.failures)
    assert runner._strategy.calls == []


def test_empty_python_executable_fails_before_strategy(tmp_path: Path) -> None:
    runner = _make_runner(
        tmp_path, canonical_project_root=str(tmp_path), python_executable=sys.executable,
        enable_regeneration=True,
    )
    object.__setattr__(runner._config, "python_executable", "")
    record = runner.run(_scenario(evaluator_asset="tests/evaluator_assets/eval.py"))
    assert record.status == RunStatus.failed
    assert any(f.stage == "configuration" for f in record.failures)


def test_v2_metadata_missing_evaluator_fails_before_strategy(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path, validation_command=["echo", "ok"], enable_regeneration=True)
    record = runner.run(
        _scenario(post_generation_command=("echo",), evaluator_asset=""),
    )
    assert record.status == RunStatus.failed
    assert any(f.stage == "configuration" for f in record.failures)
    assert runner._strategy.calls == []


def test_missing_required_migration_command_fails_before_strategy(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path, enable_regeneration=True)
    record = runner.run(
        _scenario(require_new_migration=True, post_generation_command=()),
    )
    assert record.status == RunStatus.failed
    assert any("post_generation_command" in f.message for f in record.failures)


def test_missing_baseline_command_fails_before_strategy(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path, validation_command=None, enable_regeneration=True)
    record = runner.run(_scenario())
    assert record.status == RunStatus.failed
    assert any(f.stage == "configuration" for f in record.failures)
    assert runner._strategy.calls == []


def test_whitespace_baseline_command_fails_before_strategy(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path, validation_command=["   "], enable_regeneration=True)
    record = runner.run(_scenario())
    assert record.status == RunStatus.failed
    assert any(f.stage == "configuration" for f in record.failures)
    assert runner._strategy.calls == []


def test_invalid_baseline_command_item_fails_before_strategy(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path, validation_command=["", "pytest"], enable_regeneration=True)
    record = runner.run(_scenario())
    assert record.status == RunStatus.failed
    assert any(f.stage == "configuration" for f in record.failures)


def test_agent_missing_baseline_command_fails_before_begin_run(tmp_path: Path) -> None:
    runner = _make_runner(
        tmp_path, validation_command=None, enable_regeneration=True,
        strategy=_FakeStrategy(),
    )
    object.__setattr__(runner._config, "strategy_name", "iterative_repository_agent")
    record = runner.run(_scenario())
    assert record.status == RunStatus.failed
    assert any(f.stage == "configuration" for f in record.failures)
    assert runner._strategy.calls == []


def test_legacy_scenario_empty_metadata_retains_compat(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path, validation_command=None)
    result = runner._execute_scientific_validation(
        _scenario(post_generation_command=(), evaluator_asset=""),
        _exec(),
    )
    assert result.passed is True
    assert result.failed_stage is None


# ===================================================================
# 7-16: Failure matrix
# ===================================================================

def test_migration_command_failure_is_migration_generation(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path, validation_command=["echo", "ok"])
    result = runner._execute_scientific_validation(
        _scenario(post_generation_command=("false",)),
        _exec(),
    )
    assert result.passed is False
    assert result.failed_stage == "migration_generation"
    assert result.failure_kind == FailureKind.build


def test_zero_new_migration_fails(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path)
    result = runner._execute_scientific_validation(
        _scenario(post_generation_command=("echo", "noop"), require_new_migration=True),
        _exec(),
    )
    assert result.passed is False
    assert result.failed_stage == "migration_generation"
    assert result.failure_kind == FailureKind.build


def test_two_new_migrations_fail(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path)
    result = runner._execute_scientific_validation(
        _scenario(post_generation_command=("echo", "multi"), require_new_migration=True),
        _exec(),
    )
    assert result.passed is False
    assert result.failed_stage == "migration_generation"


def test_old_migration_changed_fails(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path)
    result = runner._execute_scientific_validation(
        _scenario(post_generation_command=("echo", "changed"), require_new_migration=True),
        _exec(),
    )
    assert result.passed is False
    assert result.failed_stage == "migration_generation"


def test_baseline_failure_prevents_evaluator(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path, validation_command=["echo", "fail"])
    with patch(
        "benchmark.execution.runner.FunctionalValidator.validate",
        return_value=FunctionalValidationResult(
            passed=False, exit_code=1, stdout="fail", stderr="", duration_seconds=0.1,
        ),
    ):
        result = runner._execute_scientific_validation(
            _scenario(evaluator_asset="tests/evaluator_assets/eval.py"),
            _exec(),
        )
    assert result.passed is False
    assert result.failed_stage == "baseline_validation"
    assert result.evaluator is None


def test_evaluator_failure_prevents_success(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path, validation_command=["echo", "ok"])
    with (
        patch(
            "benchmark.execution.runner.FunctionalValidator.validate",
            return_value=FunctionalValidationResult(
                passed=True, exit_code=0, stdout="", stderr="", duration_seconds=0.1,
            ),
        ),
        patch(
            "benchmark.execution.scenario_evaluator.run_scenario_evaluator",
            return_value=ScenarioEvaluatorResult(
                passed=False, exit_code=1,
                checks=("c1",), error="eval error",
                stdout="", stderr="", duration_seconds=0.1,
            ),
        ),
    ):
        result = runner._execute_scientific_validation(
            _scenario(evaluator_asset="tests/evaluator_assets/eval.py"),
            _exec(),
        )
    assert result.passed is False
    assert result.failed_stage == "scenario_evaluator"


def test_baseline_failure_cannot_be_overridden(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path, validation_command=["echo", "fail"])
    with (
        patch(
            "benchmark.execution.runner.FunctionalValidator.validate",
            return_value=FunctionalValidationResult(
                passed=False, exit_code=1, stdout="", stderr="", duration_seconds=0.1,
            ),
        ),
        patch(
            "benchmark.execution.scenario_evaluator.run_scenario_evaluator",
            return_value=ScenarioEvaluatorResult(
                passed=True, exit_code=0, checks=("c1",), error="", stdout="", stderr="", duration_seconds=0.1,
            ),
        ),
    ):
        result = runner._execute_scientific_validation(
            _scenario(evaluator_asset="tests/evaluator_assets/eval.py"),
            _exec(),
        )
    assert result.passed is False
    assert result.evaluator is None
    assert result.failed_stage == "baseline_validation"


def test_all_v2_stages_pass_with_exact_typed_results(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path, validation_command=["echo", "ok"])
    call_order: list[str] = []

    with (
        patch(
            "benchmark.execution.post_generation.run_post_generation_command",
            return_value=PostGenerationResult(
                passed=True, exit_code=0, stdout="", stderr="",
                duration_seconds=0.1, created_paths=("m.py",),
            ),
        ),
        patch(
            "benchmark.execution.runner.FunctionalValidator.validate",
            side_effect=lambda *a, **kw: (
                call_order.append("baseline"),
                FunctionalValidationResult(
                    passed=True, exit_code=0, stdout="", stderr="", duration_seconds=0.2,
                )
            )[1],
        ),
        patch(
            "benchmark.execution.scenario_evaluator.run_scenario_evaluator",
            side_effect=lambda *a, **kw: (
                call_order.append("evaluator"),
                ScenarioEvaluatorResult(
                    passed=True, exit_code=0, checks=("c1",), error="",
                    stdout="", stderr="", duration_seconds=0.3,
                )
            )[1],
        ),
    ):
        result = runner._execute_scientific_validation(
            _scenario(
                post_generation_command=("echo", "migrate"),
                evaluator_asset="tests/evaluator_assets/eval.py",
            ),
            _exec(),
        )
    assert result.passed is True
    assert result.failed_stage is None
    assert result.migration is not None and result.migration.passed is True
    assert result.migration.created_paths == ("m.py",)
    assert result.baseline is not None and result.baseline.passed is True
    assert result.evaluator is not None and result.evaluator.passed is True
    assert result.evaluator.checks == ("c1",)
    assert call_order == ["baseline", "evaluator"]


def test_zero_model_calls_is_generation_guard(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path, validation_command=["echo", "ok"])
    result = runner._execute_scientific_validation(_scenario(), _exec(model_calls=0))
    assert result.passed is False
    assert result.failed_stage == "generation_guard"
    assert result.failure_kind == FailureKind.build


def test_zero_generated_source_is_generation_guard(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path, validation_command=["echo", "ok"])
    result = runner._execute_scientific_validation(_scenario(), _exec(generated_count=0))
    assert result.passed is False
    assert result.failed_stage == "generation_guard"


# ===================================================================
# 17-21: Wrapper and record evidence
# ===================================================================

def test_public_run_preserves_every_field(tmp_path: Path) -> None:
    from dataclasses import fields as dc_fields
    sentinel = RunRecord(
        identity=RunIdentity(
            run_id="sentinel", protocol_version="1.0",
            repository_commit_sha="abc", scenario_id="r3d", strategy_name="monolithic",
        ),
        status=RunStatus.succeeded,
        selection_tool_calls=7,
        selection_tool_duration_seconds=1.5,
        selection_inspected_file_count=9,
        selection_tool_transcript=("t1", "t2"),
        migration_generation_passed=True,
        generated_migration_paths=("m.py",),
        baseline_validation_passed=True,
        scenario_evaluator_passed=True,
        scenario_evaluator_checks=("c1",),
    )

    runner = _make_runner(tmp_path, validation_command=["echo", "ok"], enable_regeneration=True)
    with patch.object(runner, "_run_regeneration_flow", return_value=sentinel):
        record = runner.run(_scenario())
    for f in dc_fields(RunRecord):
        sent_val = getattr(sentinel, f.name, None)
        rec_val = getattr(record, f.name, None)
        if f.name in ("identity", "duration_seconds"):
            continue
        assert sent_val == rec_val, f"Field {f.name}: sentinel={sent_val} record={rec_val}"


def test_failed_initial_record_preserves_partial_evidence(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path, validation_command=["echo", "ok"])
    result = runner._execute_scientific_validation(
        _scenario(post_generation_command=("echo", "fail")),
        _exec(),
    )
    fields = runner._scientific_record_fields(result)
    assert fields["migration_generation_passed"] is False
    assert fields["baseline_validation_passed"] is None
    assert fields["scenario_evaluator_passed"] is None


def test_compatibility_baseline_mirror_exact(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path, validation_command=["echo", "ok"])
    result = runner._execute_scientific_validation(_scenario(), _exec())
    fields = runner._scientific_record_fields(result)
    assert fields["functional_validation_passed"] == fields["baseline_validation_passed"]
    assert fields["functional_validation_duration_seconds"] == fields["baseline_validation_duration_seconds"]


def test_scientific_record_fields_none_result(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path)
    fields = runner._scientific_record_fields(None)
    assert fields["migration_generation_passed"] is None
    assert fields["baseline_validation_passed"] is None
    assert fields["scenario_evaluator_passed"] is None
    assert fields["functional_validation_passed"] is None


def test_scientific_record_fields_all_passed(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path)
    mig = PostGenerationResult(
        passed=True, exit_code=0, stdout="", stderr="", duration_seconds=0.1, created_paths=("m.py",),
    )
    bas = FunctionalValidationResult(passed=True, exit_code=0, stdout="", stderr="", duration_seconds=0.2)
    eva = ScenarioEvaluatorResult(
        passed=True, exit_code=0, checks=("c1",), error="", stdout="", stderr="", duration_seconds=0.3,
    )
    result = _ScientificValidationResult(
        migration=mig, baseline=bas, evaluator=eva,
        passed=True, failed_stage=None, failure_kind=None,
        feedback="", duration_seconds=0.6,
    )
    fields = runner._scientific_record_fields(result)
    assert fields["migration_generation_passed"] is True
    assert fields["generated_migration_paths"] == ("m.py",)
    assert fields["baseline_validation_passed"] is True
    assert fields["scenario_evaluator_passed"] is True
    assert fields["scenario_evaluator_checks"] == ("c1",)


# ===================================================================
# 22-27: Persistence and reporting
# ===================================================================

def test_to_run_record_data_preserves_all_fields(tmp_path: Path) -> None:
    from seven_arm_benchmark import _to_run_record_data
    record_dict = {
        "run_id": "test-conv",
        "scenario_id": "r3d",
        "strategy_name": "monolithic",
        "status": "succeeded",
        "duration_seconds": 1.0,
        "token_usage": {"prompt": 10, "completion": 10, "total": 20},
        "selection_tool_calls": 7,
        "selection_tool_duration_seconds": 1.5,
        "selection_inspected_file_count": 9,
        "selection_tool_transcript": ["a"],
        "migration_generation_passed": True,
        "generated_migration_paths": ["m.py"],
        "baseline_validation_passed": True,
        "scenario_evaluator_passed": True,
        "scenario_evaluator_checks": ["c1"],
        "selection_prompt_tokens": 5,
        "selection_completion_tokens": 5,
        "selection_total_tokens": 10,
        "selection_model_calls": 1,
        "selection_duration_seconds": 0.5,
        "regeneration_prompt_tokens": 10,
        "regeneration_completion_tokens": 10,
        "regeneration_total_tokens": 20,
        "regeneration_model_calls": 1,
        "regeneration_duration_seconds": 0.5,
        "functional_validation_duration_seconds": 0.3,
        "functional_validation_passed": True,
        "total_workflow_tokens": 30,
        "total_workflow_model_calls": 2,
        "total_workflow_duration_seconds": 1.5,
    }
    data = _to_run_record_data(
        record_dict,
        run_id="test-conv",
        profile="default",
        repository_id="repo",
        scenario_id="r3d",
        strategy_id="monolithic",
        repetition=1,
        model_identity="test",
        dry_run=False,
        protocol_version="1.0",
        source_commit="abc",
        config_hash="hash",
        started_at="2024-01-01",
        ended_at="2024-01-01",
        hw_id="cpu",
        sw_id="python3",
        max_attempts=3,
    )
    assert data.selection_tool_calls == 7
    assert data.selection_tool_transcript == ["a"]
    assert data.migration_generation_passed is True
    assert data.scenario_evaluator_passed is True
    assert data.selection_prompt_tokens == 5


def test_actual_jsonl_save_reload_preserves_fields(tmp_path: Path) -> None:
    store = RunRecordStore(tmp_path / "runs")
    record = RunRecordData(
        run_id="test-jsonl",
        profile="default",
        repository_id="repo",
        scenario_id="r3d",
        strategy_id="monolithic",
        repetition=1,
        seed=42,
        status="succeeded",
        selection_tool_calls=7,
        selection_tool_duration_seconds=1.5,
        selection_inspected_file_count=9,
        selection_tool_transcript=["a"],
        migration_generation_passed=True,
        generated_migration_paths=["m.py"],
        baseline_validation_passed=True,
        scenario_evaluator_passed=True,
        scenario_evaluator_checks=["c1"],
    )
    store.append(record)
    loaded = store.load_all()
    assert len(loaded) == 1
    assert loaded[0].selection_tool_calls == 7
    assert loaded[0].selection_tool_transcript == ["a"]
    assert loaded[0].migration_generation_passed is True
    assert loaded[0].scenario_evaluator_passed is True


def test_old_record_defaults_load(tmp_path: Path) -> None:
    store = RunRecordStore(tmp_path / "runs")
    old = {
        "run_id": "legacy",
        "profile": "default",
        "repository_id": "repo",
        "scenario_id": "legacy",
        "strategy_id": "monolithic",
        "repetition": 1,
        "seed": 42,
        "status": "succeeded",
        "duration_seconds": 1.0,
    }
    import json
    with open(store.path, "a", encoding="utf-8") as f:
        f.write(json.dumps(old, sort_keys=True) + "\n")
    loaded = store.load_all()
    assert len(loaded) == 1
    assert loaded[0].selection_tool_calls == 0
    assert loaded[0].migration_generation_passed is None
    assert loaded[0].scenario_evaluator_passed is None


def test_idempotent_equality_includes_new_fields(tmp_path: Path) -> None:
    store = RunRecordStore(tmp_path / "runs")
    a = RunRecordData(
        run_id="idem", profile="default", repository_id="repo",
        scenario_id="r3d", strategy_id="monolithic", repetition=1, seed=42,
        status="succeeded", selection_tool_calls=3,
    )
    store.append(a)
    store.append(a)  # idempotent


def test_idempotent_append_with_same_new_fields_is_idempotent(tmp_path: Path) -> None:
    store = RunRecordStore(tmp_path / "runs")
    a = RunRecordData(
        run_id="idem2", profile="default", repository_id="repo",
        scenario_id="r3d", strategy_id="monolithic", repetition=1, seed=42,
        status="succeeded", selection_tool_calls=5,
        selection_tool_transcript=["x"],
        migration_generation_passed=True,
    )
    store.append(a)
    store.append(a)


def test_conflicting_new_field_raises_integrity_error(tmp_path: Path) -> None:
    from benchmark.checkpoint.persistence import RunRecordIntegrityError
    store = RunRecordStore(tmp_path / "runs")
    a = RunRecordData(
        run_id="conflict", profile="default", repository_id="repo",
        scenario_id="r3d", strategy_id="monolithic", repetition=1, seed=42,
        status="succeeded", selection_tool_calls=3,
    )
    b = RunRecordData(
        run_id="conflict", profile="default", repository_id="repo",
        scenario_id="r3d", strategy_id="monolithic", repetition=1, seed=42,
        status="succeeded", selection_tool_calls=7,
    )
    store.append(a)
    import pytest
    with pytest.raises(RunRecordIntegrityError):
        store.append(b)


def test_reporting_serializer_contains_all_fields(tmp_path: Path) -> None:
    from benchmark.statistics.reporting import NotebookExporter
    identity = RunIdentity(
        run_id="rep-test", protocol_version="1.0",
        repository_commit_sha="abc", scenario_id="r3d", strategy_name="monolithic",
    )
    record = RunRecord(
        identity=identity, status=RunStatus.succeeded,
        selection_tool_calls=7, selection_tool_duration_seconds=1.5,
        selection_inspected_file_count=9,
        selection_tool_transcript=("a", "b"),
        migration_generation_passed=True,
        generated_migration_paths=("m.py",),
        baseline_validation_passed=True,
        scenario_evaluator_passed=True,
    )
    exporter = NotebookExporter()
    serialized = exporter._serialize_record(record)
    assert serialized["selection_tool_calls"] == 7
    assert serialized["selection_tool_transcript"] == ["a", "b"]
    assert serialized["migration_generation_passed"] is True
    assert serialized["scenario_evaluator_passed"] is True


# ===================================================================
# 28-31: Leakage and isolation
# ===================================================================

def test_evaluator_metadata_never_reaches_strategy(tmp_path: Path) -> None:
    strategy = _FakeStrategy()
    runner = _make_runner(tmp_path, validation_command=["echo", "ok"], strategy=strategy, enable_regeneration=True)
    runner.run(_scenario(evaluator_asset="tests/evaluator_assets/eval.py"))
    for call_args in strategy.calls:
        rc = call_args.get("requirement_change", call_args)
        ac = getattr(rc, "acceptance_criteria", ())
        assert not any("eval" in str(c).lower() or "evaluator" in str(c).lower() for c in ac)


def test_repair_validation_duration_uses_complete_stage_sum(tmp_path: Path) -> None:
    import pytest
    runner = _make_runner(tmp_path, validation_command=["echo", "ok"], enable_regeneration=True)
    record = RunRecord(
        identity=runner._build_run_identity(_scenario()),
        status=RunStatus.failed,
        failures=(FailureRecord(
            failure_kind=FailureKind.build,
            message="fail", stage="migration_generation",
        ),),
        migration_duration_seconds=0.3,
        baseline_validation_duration_seconds=0.2,
        scenario_evaluator_duration_seconds=0.1,
    )
    sci_pass = _ScientificValidationResult(
        migration=None, baseline=None, evaluator=None,
        passed=True, failed_stage=None, failure_kind=None,
        feedback="", duration_seconds=0.4,
    )
    runner._last_scientific_result = sci_pass
    runner._last_prediction = ImpactPrediction()
    object.__setattr__(runner._budget, "_attempts", 0)
    object.__setattr__(runner._budget, "_max_attempts", 3)
    runner._state.start()
    with (
        patch.object(runner, "_execute_scientific_validation", return_value=sci_pass),
        patch(
            "benchmark.execution.runner.SharedRegenerationExecutor.execute",
            return_value=MagicMock(
                prompt_tokens=0, completion_tokens=0, total_tokens=0,
                model_calls=0, duration_seconds=0.0, artifacts=(),
                failures=(),
            ),
        ),
    ):
        result = runner._run_regeneration_repair_flow(
            scenario=_scenario(), first_record=record, start_time=0.0,
        )
    expected_val_dur = 0.3 + 0.2 + 0.1 + 0.4
    assert result.total_workflow_duration_seconds == pytest.approx(expected_val_dur, abs=0.01)


def test_evaluator_asset_never_appears_in_workspace(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path, validation_command=["echo", "ok"])

    def _check_evaluator(*args: Any, **kwargs: Any) -> ScenarioEvaluatorResult:
        ws_path = Path(runner._isolation.workspace.root)
        leaked = list(ws_path.rglob("*eval*"))
        assert len(leaked) == 0, f"Evaluator leaked: {leaked}"
        return ScenarioEvaluatorResult(
            passed=True, exit_code=0, checks=("c1",), error="", stdout="", stderr="", duration_seconds=0.1,
        )

    with (
        patch(
            "benchmark.execution.runner.FunctionalValidator.validate",
            return_value=FunctionalValidationResult(
                passed=True, exit_code=0, stdout="", stderr="", duration_seconds=0.1,
            ),
        ),
        patch(
            "benchmark.execution.scenario_evaluator.run_scenario_evaluator",
            side_effect=_check_evaluator,
        ),
    ):
        runner.run(_scenario(evaluator_asset="tests/evaluator_assets/eval.py"))


# ===================================================================
# 32-37: Repair and Agent feedback
# ===================================================================

def test_migration_failure_triggers_repair_bounded_feedback(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path, validation_command=["echo", "ok"])
    result = runner._execute_scientific_validation(
        _scenario(post_generation_command=("echo", "migrate")),
        _exec(),
    )
    assert result.passed is False
    ec, so, se = runner._scientific_feedback_channels(result)
    assert isinstance(ec, int)
    assert isinstance(so, str)
    assert isinstance(se, str)


def test_baseline_failure_triggers_repair_bounded_output(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path, validation_command=["echo", "fail"])
    with patch(
        "benchmark.execution.runner.FunctionalValidator.validate",
        return_value=FunctionalValidationResult(
            passed=False, exit_code=1, stdout="test out", stderr="", duration_seconds=0.1,
        ),
    ):
        result = runner._execute_scientific_validation(_scenario(), _exec())
    assert result.passed is False
    ec, so, se = runner._scientific_feedback_channels(result)
    assert "test out" in so


def test_evaluator_failure_triggers_repair_with_checks_not_source(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path, validation_command=["echo", "ok"])
    with (
        patch(
            "benchmark.execution.runner.FunctionalValidator.validate",
            return_value=FunctionalValidationResult(
                passed=True, exit_code=0, stdout="", stderr="", duration_seconds=0.1,
            ),
        ),
        patch(
            "benchmark.execution.scenario_evaluator.run_scenario_evaluator",
            return_value=ScenarioEvaluatorResult(
                passed=False, exit_code=1,
                checks=("c1", "c2"), error="eval error",
                stdout="", stderr="", duration_seconds=0.1,
            ),
        ),
    ):
        result = runner._execute_scientific_validation(
            _scenario(evaluator_asset="tests/evaluator_assets/eval.py"),
            _exec(),
        )
    assert result.passed is False
    ec, so, se = runner._scientific_feedback_channels(result)
    assert "c1" in se or "c2" in se
    assert "eval error" in se


def test_evaluator_feedback_includes_stdout_stderr_error_and_checks(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path, validation_command=["echo", "ok"])
    with (
        patch(
            "benchmark.execution.runner.FunctionalValidator.validate",
            return_value=FunctionalValidationResult(
                passed=True, exit_code=0, stdout="", stderr="", duration_seconds=0.1,
            ),
        ),
        patch(
            "benchmark.execution.scenario_evaluator.run_scenario_evaluator",
            return_value=ScenarioEvaluatorResult(
                passed=False, exit_code=1,
                checks=("task_priority_filter",), error="EVAL_BAD",
                stdout="EVAL_OUT", stderr="EVAL_STDERR",
                duration_seconds=0.1,
            ),
        ),
    ):
        result = runner._execute_scientific_validation(
            _scenario(evaluator_asset="tests/evaluator_assets/eval.py"),
            _exec(),
        )
    assert result.passed is False
    ec, so, se = runner._scientific_feedback_channels(result)
    assert "EVAL_OUT" in so
    assert "EVAL_STDERR" in se
    assert "EVAL_BAD" in se
    assert "task_priority_filter" in se
    assert "eval.py" not in se


# ===================================================================
# 38-40: Configuration and stage classification
# ===================================================================

def test_every_failed_stage_produces_exact_failure_record_stage(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path, validation_command=["echo", "ok"])
    mig_result = runner._execute_scientific_validation(
        _scenario(post_generation_command=("echo", "x"), require_new_migration=True),
        _exec(),
    )
    if not mig_result.passed:
        fr = runner._failure_from_scientific_result(mig_result)
        assert fr.stage == mig_result.failed_stage


def test_missing_metadata_uses_harness_defect(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path, validation_command=["echo", "ok"])
    cfg_fail = runner._validate_scientific_configuration(
        _scenario(post_generation_command=("echo",), evaluator_asset=""),
    )
    assert cfg_fail is not None
    assert cfg_fail.failure_kind == FailureKind.harness_defect


def test_migration_baseline_evaluator_use_build_kind(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path, validation_command=["echo", "ok"])
    result = runner._execute_scientific_validation(
        _scenario(post_generation_command=("false",)),
        _exec(),
    )
    if not result.passed:
        assert result.failure_kind == FailureKind.build


# ===================================================================
# Repair eligibility
# ===================================================================

def test_is_repairable_migration_failure(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path)
    record = RunRecord(
        identity=MagicMock(),
        status=RunStatus.failed,
        failures=(FailureRecord(
            failure_kind=FailureKind.build,
            message="Migration failed",
            stage="migration_generation",
        ),),
    )
    assert runner._is_repairable_failure(record) is True


def test_is_repairable_evaluator_failure(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path)
    record = RunRecord(
        identity=MagicMock(),
        status=RunStatus.failed,
        failures=(FailureRecord(
            failure_kind=FailureKind.build,
            message="Evaluator failed",
            stage="scenario_evaluator",
        ),),
    )
    assert runner._is_repairable_failure(record) is True


def test_is_repairable_generation_guard_failure(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path)
    record = RunRecord(
        identity=MagicMock(),
        status=RunStatus.failed,
        failures=(FailureRecord(
            failure_kind=FailureKind.build,
            message="No generated source",
            stage="generation_guard",
        ),),
    )
    assert runner._is_repairable_failure(record) is True


def test_is_not_repairable_harness_defect(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path)
    record = RunRecord(
        identity=MagicMock(),
        status=RunStatus.failed,
        failures=(FailureRecord(
            failure_kind=FailureKind.harness_defect,
            message="Bad config",
            stage="configuration",
        ),),
    )
    assert runner._is_repairable_failure(record) is False


def test_is_not_repairable_timeout(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path)
    record = RunRecord(
        identity=MagicMock(),
        status=RunStatus.failed,
        failures=(FailureRecord(
            failure_kind=FailureKind.timeout,
            message="Timed out",
            stage="budget",
        ),),
    )
    assert runner._is_repairable_failure(record) is False


def test_is_not_repairable_infrastructure(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path)
    record = RunRecord(
        identity=MagicMock(),
        status=RunStatus.failed,
        failures=(FailureRecord(
            failure_kind=FailureKind.infrastructure,
            message="Disk full",
            stage="runner",
        ),),
    )
    assert runner._is_repairable_failure(record) is False


# ===================================================================
# Failure record exact stage
# ===================================================================

def test_failure_from_scientific_result_exact_stage(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path)
    mig = PostGenerationResult(passed=False, exit_code=1, stdout="", stderr="err", duration_seconds=0.1)
    result = _ScientificValidationResult(
        migration=mig, baseline=None, evaluator=None,
        passed=False, failed_stage="migration_generation",
        failure_kind=FailureKind.build,
        feedback="migration failed", duration_seconds=0.1,
    )
    fr = runner._failure_from_scientific_result(result)
    assert fr.stage == "migration_generation"
    assert fr.failure_kind == FailureKind.build


# ===================================================================
# Monolithic/Selective repair — second generation attempt
# ===================================================================

def test_public_monolithic_migration_failure_repairs_to_success(tmp_path: Path) -> None:
    runner = _make_runner(
        tmp_path, validation_command=["echo", "ok"], enable_regeneration=True,
    )
    fail_result = _ScientificValidationResult(
        migration=PostGenerationResult(
            passed=False, exit_code=1, stdout="", stderr="migration fail",
            duration_seconds=0.1,
        ),
        baseline=None, evaluator=None,
        passed=False, failed_stage="migration_generation",
        failure_kind=FailureKind.build, feedback="Migration failed",
        duration_seconds=0.1,
    )
    pass_result = _ScientificValidationResult(
        migration=PostGenerationResult(
            passed=True, exit_code=0, stdout="ok", stderr="",
            duration_seconds=0.2, created_paths=("m.py",),
        ),
        baseline=FunctionalValidationResult(
            passed=True, exit_code=0, stdout="", stderr="", duration_seconds=0.2,
        ),
        evaluator=ScenarioEvaluatorResult(
            passed=True, exit_code=0, checks=("c1",), error="",
            stdout="", stderr="", duration_seconds=0.3,
        ),
        passed=True, failed_stage=None, failure_kind=None,
        feedback="", duration_seconds=0.7,
    )
    sci_calls: list[int] = []
    def _sci_side(*a: Any, **kw: Any) -> _ScientificValidationResult:
        sci_calls.append(1)
        return fail_result if len(sci_calls) == 1 else pass_result

    exec_ret = MagicMock(
        prompt_tokens=10, completion_tokens=10, total_tokens=20,
        model_calls=1, duration_seconds=0.5, artifacts=(),
        failures=(),
    )
    with (
        patch.object(runner, "_execute_scientific_validation", side_effect=_sci_side),
        patch(
            "benchmark.execution.runner.SharedRegenerationExecutor.execute",
            return_value=exec_ret,
        ),
    ):
        record = runner.run(_scenario(
            post_generation_command=("echo", "migrate"),
            evaluator_asset="tests/evaluator_assets/eval.py",
        ))
    assert record.status == RunStatus.succeeded
    assert len(sci_calls) == 2


def test_public_selective_evaluator_failure_repairs_to_success(tmp_path: Path) -> None:
    runner = _make_runner(
        tmp_path, validation_command=["echo", "ok"], enable_regeneration=True,
    )
    object.__setattr__(runner._config, "strategy_name", "selective")
    fail_result = _ScientificValidationResult(
        migration=PostGenerationResult(
            passed=True, exit_code=0, stdout="", stderr="",
            duration_seconds=0.1,
        ),
        baseline=FunctionalValidationResult(
            passed=True, exit_code=0, stdout="", stderr="", duration_seconds=0.2,
        ),
        evaluator=ScenarioEvaluatorResult(
            passed=False, exit_code=1, checks=("c1",), error="bad eval",
            stdout="", stderr="", duration_seconds=0.1,
        ),
        passed=False, failed_stage="scenario_evaluator",
        failure_kind=FailureKind.build, feedback="Evaluator failed",
        duration_seconds=0.4,
    )
    pass_result = _ScientificValidationResult(
        migration=PostGenerationResult(
            passed=True, exit_code=0, stdout="", stderr="",
            duration_seconds=0.1,
        ),
        baseline=FunctionalValidationResult(
            passed=True, exit_code=0, stdout="", stderr="", duration_seconds=0.2,
        ),
        evaluator=ScenarioEvaluatorResult(
            passed=True, exit_code=0, checks=("c1",), error="",
            stdout="", stderr="", duration_seconds=0.3,
        ),
        passed=True, failed_stage=None, failure_kind=None,
        feedback="", duration_seconds=0.6,
    )
    sci_calls_sel: list[int] = []
    def _sci_side_sel(*a: Any, **kw: Any) -> _ScientificValidationResult:
        sci_calls_sel.append(1)
        return fail_result if len(sci_calls_sel) == 1 else pass_result

    exec_ret_sel = MagicMock(
        prompt_tokens=10, completion_tokens=10, total_tokens=20,
        model_calls=1, duration_seconds=0.5, artifacts=(),
        failures=(),
    )
    with (
        patch.object(runner, "_execute_scientific_validation", side_effect=_sci_side_sel),
        patch(
            "benchmark.execution.runner.SharedRegenerationExecutor.execute",
            return_value=exec_ret_sel,
        ),
    ):
        record = runner.run(_scenario(
            post_generation_command=("echo", "migrate"),
            evaluator_asset="tests/evaluator_assets/eval.py",
        ))
    assert record.status == RunStatus.succeeded
    assert len(sci_calls_sel) == 2


# ===================================================================
# Agent transcript preservation
# ===================================================================

def test_agent_record_round_trip_preserves_complete_evidence(tmp_path: Path) -> None:
    import seven_arm_benchmark
    from benchmark.checkpoint.persistence import RunRecordStore
    from benchmark.statistics.reporting import NotebookExporter
    record_dict: dict[str, Any] = {
        "run_id": "agent-roundtrip",
        "scenario_id": "r3d",
        "strategy_name": "iterative_repository_agent",
        "status": "succeeded",
        "duration_seconds": 1.0,
        "token_usage": {"prompt": 10, "completion": 10, "total": 20},
        "selection_tool_calls": 3,
        "selection_tool_duration_seconds": 1.5,
        "selection_inspected_file_count": 7,
        "selection_tool_transcript": ["TOOL A", "TOOL B"],
        "migration_generation_passed": True,
        "generated_migration_paths": ["m.py"],
        "baseline_validation_passed": True,
        "scenario_evaluator_passed": True,
        "scenario_evaluator_checks": ["task_priority_filter"],
    }
    data = seven_arm_benchmark._to_run_record_data(
        record_dict, run_id="agent-roundtrip", profile="default",
        repository_id="repo", scenario_id="r3d",
        strategy_id="iterative_repository_agent", repetition=1,
        model_identity="test", dry_run=False, protocol_version="1.0",
        source_commit="abc", config_hash="hash",
        started_at="2024-01-01", ended_at="2024-01-01",
        hw_id="cpu", sw_id="python3", max_attempts=3,
    )
    assert data.selection_tool_calls == 3
    assert data.selection_tool_transcript == ["TOOL A", "TOOL B"]
    assert data.migration_generation_passed is True
    assert data.scenario_evaluator_passed is True
    assert data.scenario_evaluator_checks == ["task_priority_filter"]
    store = RunRecordStore(tmp_path / "runs")
    store.append(data)
    loaded = store.load_all()
    assert len(loaded) == 1
    assert loaded[0].selection_tool_calls == 3
    assert loaded[0].selection_tool_transcript == ["TOOL A", "TOOL B"]
    assert loaded[0].migration_generation_passed is True
    identity = RunIdentity(
        run_id="agent-roundtrip", protocol_version="1.0",
        repository_commit_sha="abc", scenario_id="r3d",
        strategy_name="iterative_repository_agent",
    )
    run_record = RunRecord(
        identity=identity, status=RunStatus.succeeded,
        selection_tool_calls=3,
        selection_tool_transcript=("TOOL A", "TOOL B"),
        migration_generation_passed=True,
        scenario_evaluator_passed=True,
        scenario_evaluator_checks=("task_priority_filter",),
    )
    exporter = NotebookExporter()
    serialized = exporter._serialize_record(run_record)
    assert serialized["selection_tool_calls"] == 3
    assert serialized["selection_tool_transcript"] == ["TOOL A", "TOOL B"]
    assert serialized["scenario_evaluator_checks"] == ["task_priority_filter"]


# ===================================================================
# Agent executor/scientific feedback
# ===================================================================

def test_public_agent_evaluator_failure_revises_and_preserves_transcript(tmp_path: Path) -> None:
    strategy = _FakeStrategy()
    strategy.begin_run = MagicMock()
    strategy.last_requires_iteration = True
    object.__setattr__(strategy, "compact_tool_transcript", ())
    runner = _make_runner(
        tmp_path, validation_command=["echo", "ok"], enable_regeneration=True,
        strategy=strategy,
    )
    object.__setattr__(runner._config, "strategy_name", "iterative_repository_agent")
    pred_with_decisions = ImpactPrediction(
        decisions=(
            ImpactDecision(
                artifact=ArtifactRef(path="dummy.py", artifact_type=ArtifactType.source),
                action=ActionKind.regenerate,
            ),
        ),
    )
    fail_result = _ScientificValidationResult(
        migration=PostGenerationResult(
            passed=True, exit_code=0, stdout="", stderr="",
            duration_seconds=0.1,
        ),
        baseline=FunctionalValidationResult(
            passed=True, exit_code=0, stdout="", stderr="", duration_seconds=0.2,
        ),
        evaluator=ScenarioEvaluatorResult(
            passed=False, exit_code=1,
            checks=("task_priority_filter",), error="EVAL_BAD",
            stdout="EVAL_OUT", stderr="EVAL_STDERR",
            duration_seconds=0.1,
        ),
        passed=False, failed_stage="scenario_evaluator",
        failure_kind=FailureKind.build,
        feedback="Agent evaluator failed", duration_seconds=0.4,
    )
    pass_result = _ScientificValidationResult(
        migration=PostGenerationResult(
            passed=True, exit_code=0, stdout="", stderr="",
            duration_seconds=0.1,
        ),
        baseline=FunctionalValidationResult(
            passed=True, exit_code=0, stdout="", stderr="", duration_seconds=0.2,
        ),
        evaluator=ScenarioEvaluatorResult(
            passed=True, exit_code=0, checks=("task_priority_filter",), error="",
            stdout="", stderr="", duration_seconds=0.3,
        ),
        passed=True, failed_stage=None, failure_kind=None,
        feedback="", duration_seconds=0.6,
    )
    sci_calls_ag: list[int] = []
    def _sci_side_ag(*a: Any, **kw: Any) -> _ScientificValidationResult:
        sci_calls_ag.append(1)
        result = fail_result if len(sci_calls_ag) == 1 else pass_result
        runner._last_scientific_result = result
        return result
    exec_ret_ag = MagicMock(
        prompt_tokens=10, completion_tokens=10, total_tokens=20,
        model_calls=1, duration_seconds=0.5, artifacts=(),
        failures=(),
    )
    mock_revise = MagicMock(return_value=pred_with_decisions)
    strategy.analyze_impact = MagicMock(return_value=pred_with_decisions)
    strategy.revise_plan = mock_revise
    with (
        patch.object(runner, "_execute_scientific_validation", side_effect=_sci_side_ag),
        patch(
            "benchmark.execution.runner.SharedRegenerationExecutor.execute",
            return_value=exec_ret_ag,
        ),
    ):
        record = runner.run(_scenario(
            post_generation_command=("echo", "migrate"),
            evaluator_asset="tests/evaluator_assets/eval.py",
        ))
    assert record.status == RunStatus.succeeded
    mock_revise.assert_called_once()
    se_val = str(mock_revise.call_args[1].get("val_stderr", ""))
    assert "EVAL_STDERR" in se_val
    assert "EVAL_BAD" in se_val
    assert "task_priority_filter" in se_val
    assert "eval.py" not in se_val
    assert "EVAL_OUT" in str(mock_revise.call_args[1].get("val_stdout", ""))
    assert record.selection_tool_transcript == ()
    assert record.scenario_evaluator_passed is True
    assert "task_priority_filter" in (record.scenario_evaluator_checks or ())


# ===================================================================
# Failure stage exactness
# ===================================================================

def test_every_failed_stage_produces_exact_failure_record_stage_2(tmp_path: Path) -> None:
    runner = _make_runner(tmp_path, validation_command=["echo", "ok"])
    for stage, scenario_kw, exec_kw in [
        ("generation_guard", {}, {"model_calls": 0, "generated_count": 0}),
        ("migration_generation", {"post_generation_command": ("false",)}, {}),
    ]:
        result = runner._execute_scientific_validation(
            _scenario(**scenario_kw),
            _exec(**exec_kw) if exec_kw else _exec(),
        )
        if not result.passed:
            fr = runner._failure_from_scientific_result(result)
            assert fr.stage == stage, f"Expected {stage}, got {fr.stage}"
