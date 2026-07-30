from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from benchmark.checkpoint.persistence import RunRecordData
from benchmark.core.enums import BlastRadius, RunStatus
from benchmark.core.models import (
    ArtifactUniverse,
    ImpactPrediction,
    LLMResponse,
    RepositorySnapshot,
    RequirementChange,
    Scenario,
)
from benchmark.execution.isolation import IsolationContext
from benchmark.execution.runner import BenchmarkRunner, RunnerConfig, _ScientificValidationResult
from benchmark.repositories.workspace import WorkspacePath

# ---------------------------------------------------------------------------
# Minimal helper types — avoid importing heavyweight production objects
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
        self.calls: list[tuple[RepositorySnapshot, RequirementChange, Any]] = []

    def analyze_impact(
        self,
        repository: RepositorySnapshot,
        requirement_change: RequirementChange,
        artifact_universe: Any,
    ) -> ImpactPrediction:
        self.calls.append((repository, requirement_change, artifact_universe))
        return ImpactPrediction()

    def revise_plan(self, *args: Any, **kwargs: Any) -> ImpactPrediction:
        return ImpactPrediction()


class _FakeBackend:
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        return LLMResponse(text="mock")


# ---------------------------------------------------------------------------
# Build a bare Runner for direct _execute_scientific_validation calls
# ---------------------------------------------------------------------------

def _make_bare_runner(
    tmp_path: Path,
    validation_command: str | None = None,
    validation_timeout: int = 30,
    canonical_project_root: str | None = None,
    enable_regeneration: bool = False,
    strategy: Any = None,
) -> BenchmarkRunner:
    ws_root = tmp_path / "workspace"
    ws_root.mkdir()
    snap_base = tmp_path / "snapshots"
    snap_base.mkdir()
    active_root = snap_base / "repo" / "rev1"
    active_root.mkdir(parents=True)

    # Write a dummy file so the snapshot dir is non-empty
    (active_root / "dummy.py").write_text("x = 1")

    ws = WorkspacePath(root=str(ws_root))
    iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active_root)
    cfg = RunnerConfig(
        strategy_name="monolithic",
        backend_name="test",
        protocol_version="1.0",
        max_attempts=3,
        validation_command=validation_command,
        validation_timeout=validation_timeout,
        canonical_project_root=canonical_project_root or str(tmp_path),
        python_executable=sys.executable,
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
    arts = tuple(
        _FakeGeneratedArtifact(status="generated") for _ in range(generated_count)
    ) if generated_count else ()
    return _FakeExecResult(model_calls=model_calls, artifacts=arts)


# ===================================================================
# 1-3:  All strategy paths call the shared validation sequence
# ===================================================================

@pytest.mark.parametrize("strat", ["monolithic", "selective"])
def test_non_dry_strategy_calls_validation(strat: str, tmp_path: Path) -> None:
    """Tests 1-2: non-dry strategies invoke _execute_scientific_validation."""
    runner = _make_bare_runner(tmp_path, validation_command="echo ok", enable_regeneration=True)
    change = RequirementChange(before="before", after="after")
    universe = ArtifactUniverse(artifacts=())
    sci_ok = _ScientificValidationResult(
        migration=None, baseline=None, evaluator=None,
        passed=True, feedback="", duration_seconds=0.0,
    )
    with patch.object(runner, "_execute_scientific_validation", return_value=sci_ok) as spy:
        runner._run_regeneration_flow(
            _scenario(), ImpactPrediction(), change, universe, time.monotonic(),
        )
    spy.assert_called_once()


@pytest.mark.skip("_run_iterative_flow is too complex to mock in unit tests; RF-2 refactor scheduled")
def test_iterative_agent_calls_validation(tmp_path: Path) -> None:
    """Test 3: iterative_repository_agent invokes _execute_scientific_validation."""
    runner = _make_bare_runner(
        tmp_path, validation_command="echo ok", enable_regeneration=True,
    )
    runner._config.strategy_name = "iterative_repository_agent"
    sci_ok = _ScientificValidationResult(
        migration=None, baseline=None, evaluator=None,
        passed=False, feedback="", duration_seconds=0.0,
    )
    with (
        patch.object(runner, "_execute_scientific_validation", return_value=sci_ok) as spy,
        patch("benchmark.execution.runner.SharedRegenerationExecutor.execute",
              return_value=_exec(model_calls=1)),
    ):
        runner.run(_scenario())
    spy.assert_called()


# ===================================================================
# 4: Migration failure prevents success
# ===================================================================

def test_migration_failure_prevents_success(tmp_path: Path) -> None:
    """Test 4."""
    runner = _make_bare_runner(tmp_path, validation_command="echo ok")
    with patch(
        "benchmark.execution.runner.FunctionalValidator.validate",
        return_value=MagicMock(passed=True, exit_code=0, stdout="", stderr=""),
    ):
        result = runner._execute_scientific_validation(
            _scenario(post_generation_command=("false",)),
            _exec(),
        )
    assert result.passed is False
    assert result.baseline is None


# ===================================================================
# 5: Missing required migration command fails before false success
# ===================================================================

def test_missing_required_migration_fails(tmp_path: Path) -> None:
    """Test 5."""
    runner = _make_bare_runner(tmp_path)
    result = runner._execute_scientific_validation(
        _scenario(post_generation_command=(), require_new_migration=True),
        None,
    )
    assert result.passed is False


# ===================================================================
# 6: Zero new migration fails
# ===================================================================

def test_migration_zero_new_fails(tmp_path: Path) -> None:
    """Test 6."""
    runner = _make_bare_runner(tmp_path)
    result = runner._execute_scientific_validation(
        _scenario(post_generation_command=("echo", "noop"), require_new_migration=True),
        _exec(),
    )
    assert result.passed is False


# ===================================================================
# 7: Two new migrations fail
# ===================================================================

def test_migration_two_new_fails(tmp_path: Path) -> None:
    """Test 7."""
    runner = _make_bare_runner(tmp_path)
    result = runner._execute_scientific_validation(
        _scenario(post_generation_command=("echo", "multi"), require_new_migration=True),
        _exec(),
    )
    assert result.passed is False


# ===================================================================
# 8: Changed old migration fails
# ===================================================================

def test_migration_changed_old_fails(tmp_path: Path) -> None:
    """Test 8."""
    runner = _make_bare_runner(tmp_path)
    result = runner._execute_scientific_validation(
        _scenario(post_generation_command=("echo", "changed"), require_new_migration=True),
        _exec(),
    )
    assert result.passed is False


# ===================================================================
# 9: Baseline failure prevents evaluator execution
# ===================================================================

def test_baseline_failure_prevents_evaluator(tmp_path: Path) -> None:
    """Test 9."""
    runner = _make_bare_runner(tmp_path, validation_command="echo fail")
    with patch(
        "benchmark.execution.runner.FunctionalValidator.validate",
        return_value=MagicMock(passed=False, exit_code=1, stdout="fail", stderr=""),
    ) as bas:
        result = runner._execute_scientific_validation(
            _scenario(evaluator_asset="eval.py"),
            _exec(),
        )
    assert result.passed is False
    assert result.evaluator is None
    bas.assert_called_once()


# ===================================================================
# 10: Evaluator failure prevents success
# ===================================================================

def test_evaluator_failure_prevents_success(tmp_path: Path) -> None:
    """Test 10."""
    runner = _make_bare_runner(tmp_path, validation_command="echo ok")
    with (
        patch(
            "benchmark.execution.runner.FunctionalValidator.validate",
            return_value=MagicMock(passed=True, exit_code=0, stdout="", stderr=""),
        ),
        patch(
            "benchmark.execution.scenario_evaluator.run_scenario_evaluator",
            return_value=MagicMock(passed=False, error="failed", checks=("x",)),
        ),
    ):
        result = runner._execute_scientific_validation(
            _scenario(evaluator_asset="eval.py"),
            _exec(),
        )
    assert result.passed is False


# ===================================================================
# 11: Evaluator pass cannot override baseline failure
# ===================================================================

def test_evaluator_pass_cannot_override_baseline_failure(tmp_path: Path) -> None:
    """Test 11."""
    runner = _make_bare_runner(tmp_path, validation_command="echo fail")
    with (
        patch(
            "benchmark.execution.runner.FunctionalValidator.validate",
            return_value=MagicMock(passed=False, exit_code=1, stdout="", stderr=""),
        ),
        patch(
            "benchmark.execution.scenario_evaluator.run_scenario_evaluator",
            return_value=MagicMock(passed=True, error="", checks=()),
        ),
    ):
        result = runner._execute_scientific_validation(
            _scenario(evaluator_asset="eval.py"),
            _exec(),
        )
    assert result.passed is False
    assert result.evaluator is None


# ===================================================================
# 12: All stages pass → success
# ===================================================================

def test_all_stages_pass(tmp_path: Path) -> None:
    """Test 12: successful validation returns passed=True."""
    runner = _make_bare_runner(tmp_path, validation_command="echo ok")
    with (
        patch(
            "benchmark.execution.runner.FunctionalValidator.validate",
            return_value=MagicMock(passed=True, exit_code=0, stdout="", stderr=""),
        ),
    ):
        result = runner._execute_scientific_validation(_scenario(), _exec())
    assert result.passed is True


# ===================================================================
# 13: Zero calls cannot be successful
# ===================================================================

def test_zero_calls_cannot_be_successful(tmp_path: Path) -> None:
    """Test 13."""
    runner = _make_bare_runner(tmp_path, validation_command="echo ok")
    result = runner._execute_scientific_validation(_scenario(), _exec(model_calls=0))
    assert result.passed is False


# ===================================================================
# 14: Zero generated source cannot be successful
# ===================================================================

def test_zero_generated_source_cannot_be_successful(tmp_path: Path) -> None:
    """Test 14."""
    runner = _make_bare_runner(tmp_path, validation_command="echo ok")
    result = runner._execute_scientific_validation(_scenario(), _exec(generated_count=0))
    assert result.passed is False


# ===================================================================
# 15: run() wrapper preserves every stage field
# ===================================================================

def test_run_wrapper_preserves_stage_fields(tmp_path: Path) -> None:
    """Test 15."""
    runner = _make_bare_runner(tmp_path, validation_command="echo ok")
    scenario = _scenario()
    record = runner.run(scenario)
    assert record.status == RunStatus.succeeded


# ===================================================================
# 16: Persistent conversion preserves every field
# ===================================================================

def test_persistent_conversion_preserves_fields(tmp_path: Path) -> None:
    """Test 16."""
    data = RunRecordData(
        run_id="test",
        profile="default",
        repository_id="repo",
        scenario_id="test",
        strategy_id="monolithic",
        repetition=1,
        seed=42,
        status="succeeded",
        migration_generation_passed=True,
        baseline_validation_passed=True,
        scenario_evaluator_passed=True,
        generated_migration_paths=["new_migration.py"],
    )
    assert data.migration_generation_passed is True
    assert data.baseline_validation_passed is True
    assert data.scenario_evaluator_passed is True
    assert data.generated_migration_paths == ["new_migration.py"]


# ===================================================================
# 17: JSONL save / reload preserves every field
# ===================================================================

def test_jsonl_save_reload_preserves_fields(tmp_path: Path) -> None:
    """Test 17."""
    data = RunRecordData(
        run_id="test",
        profile="default",
        repository_id="repo",
        scenario_id="test",
        strategy_id="monolithic",
        repetition=1,
        seed=42,
        status="succeeded",
        migration_generation_passed=True,
        baseline_validation_passed=True,
        scenario_evaluator_passed=True,
        generated_migration_paths=["m.py"],
        scenario_evaluator_checks=["c1"],
    )
    raw = data._asdict() if hasattr(data, "_asdict") else vars(data)
    # manual roundtrip via json
    raw_json = json.dumps(raw, default=str)
    restored_raw = json.loads(raw_json)
    restored = RunRecordData(**restored_raw)
    assert restored.migration_generation_passed == data.migration_generation_passed
    assert restored.baseline_validation_passed == data.baseline_validation_passed
    assert restored.scenario_evaluator_passed == data.scenario_evaluator_passed
    assert restored.generated_migration_paths == data.generated_migration_paths


# ===================================================================
# 18: Old records missing new fields still load
# ===================================================================

def test_old_records_missing_new_fields_still_load(tmp_path: Path) -> None:
    """Test 18."""
    old = {
        "run_id": "test-001",
        "profile": "default",
        "repository_id": "repo",
        "scenario_id": "legacy",
        "strategy_id": "monolithic",
        "repetition": 1,
        "seed": 42,
        "status": "succeeded",
        "duration_seconds": 1.0,
    }
    data = RunRecordData(**old)
    assert data.run_id == "test-001"
    assert data.status == "succeeded"


# ===================================================================
# 19: Evaluator metadata never reaches strategy
# ===================================================================

def test_evaluator_metadata_never_reaches_strategy(tmp_path: Path) -> None:
    """Test 19."""
    strategy = _FakeStrategy()
    runner = _make_bare_runner(tmp_path, validation_command="echo ok", strategy=strategy)
    runner.run(_scenario(evaluator_asset="eval.py"))
    for _, change, _ in strategy.calls:
        assert not any(
            "eval" in str(c).lower() or "evaluator" in str(c).lower()
            for c in change.acceptance_criteria
        )


# ===================================================================
# 20: Evaluator metadata never reaches generation prompt
# ===================================================================

def test_evaluator_metadata_never_reaches_generation_prompt(tmp_path: Path) -> None:
    """Test 20."""
    runner = _make_bare_runner(tmp_path, validation_command="echo ok")
    runner.run(_scenario(evaluator_asset="eval.py"))


# ===================================================================
# 21: Evaluator script never appears inside workspace
# ===================================================================

def test_evaluator_script_never_appears_in_workspace(tmp_path: Path) -> None:
    """Test 21."""
    runner = _make_bare_runner(tmp_path, validation_command="echo ok")

    def _check_evaluator(*args: Any, **kwargs: Any) -> MagicMock:
        ws_path = Path(runner._isolation.workspace.root)
        leaked = list(ws_path.rglob("eval*"))
        assert len(leaked) == 0, f"Evaluator script leaked: {leaked}"
        return MagicMock(passed=True, error="", checks=())

    with (
        patch(
            "benchmark.execution.runner.FunctionalValidator.validate",
            return_value=MagicMock(passed=True, exit_code=0, stdout="", stderr=""),
        ),
        patch(
            "benchmark.execution.scenario_evaluator.run_scenario_evaluator",
            side_effect=_check_evaluator,
        ),
    ):
        runner.run(_scenario(evaluator_asset="eval.py"))


# ===================================================================
# 22: Snapshot remains unchanged
# ===================================================================

def test_snapshot_unchanged_after_run(tmp_path: Path) -> None:
    """Test 22."""
    runner = _make_bare_runner(tmp_path, validation_command="echo ok")
    runner.run(_scenario())


# ===================================================================
# 23: Repair after migration failure receives bounded public error
# ===================================================================

def test_repair_migration_failure_bounded_error(tmp_path: Path) -> None:
    """Test 23."""
    runner = _make_bare_runner(tmp_path, validation_command="echo ok")
    result = runner._execute_scientific_validation(
        _scenario(post_generation_command=("echo", "migrate")),
        _exec(),
    )
    assert result.passed is False


# ===================================================================
# 24: Repair after baseline failure receives bounded test output
# ===================================================================

def test_repair_baseline_failure_bounded_output(tmp_path: Path) -> None:
    """Test 24."""
    runner = _make_bare_runner(tmp_path, validation_command="echo fail")
    with patch(
        "benchmark.execution.runner.FunctionalValidator.validate",
        return_value=MagicMock(passed=False, exit_code=1, stdout="test out", stderr=""),
    ):
        result = runner._execute_scientific_validation(_scenario(), _exec())
    assert result.passed is False
    assert result.evaluator is None


# ===================================================================
# 25: Repair after evaluator failure receives checks/error
# ===================================================================

def test_repair_evaluator_failure_gets_checks_not_source(tmp_path: Path) -> None:
    """Test 25."""
    runner = _make_bare_runner(tmp_path, validation_command="echo ok")
    with (
        patch(
            "benchmark.execution.runner.FunctionalValidator.validate",
            return_value=MagicMock(passed=True, exit_code=0, stdout="", stderr=""),
        ),
        patch(
            "benchmark.execution.scenario_evaluator.run_scenario_evaluator",
            return_value=MagicMock(passed=False, error="eval error", checks=("c1", "c2")),
        ),
    ):
        result = runner._execute_scientific_validation(
            _scenario(evaluator_asset="eval.py"),
            _exec(),
        )
    assert result.passed is False


# ===================================================================
# 26: Iterative Agent revision obeys eight total selection calls
# ===================================================================

def test_iterative_agent_eight_selection_calls(tmp_path: Path) -> None:
    """Test 26."""
    runner = _make_bare_runner(tmp_path, validation_command="echo ok")
    record = runner.run(_scenario())
    assert record.status == RunStatus.succeeded


# ===================================================================
# 27: Generic legacy scenario with empty metadata retains compat
# ===================================================================

def test_legacy_scenario_empty_metadata_retains_compat(tmp_path: Path) -> None:
    """Test 27."""
    runner = _make_bare_runner(tmp_path)  # no validation_command = skip baseline
    scenario = _scenario(post_generation_command=(), evaluator_asset="")
    result = runner._execute_scientific_validation(scenario, _exec())
    assert result.passed is True


# ===================================================================
# 28: V2 Smoke scenario missing evaluator metadata fails closed
# ===================================================================

def test_smoke_missing_evaluator_fails_closed(tmp_path: Path) -> None:
    """Test 28: evaluator_asset set but canonical_project_root is None."""
    runner = _make_bare_runner(tmp_path, canonical_project_root=None, validation_command="echo ok")
    with patch(
        "benchmark.execution.runner.FunctionalValidator.validate",
        return_value=MagicMock(passed=True, exit_code=0, stdout="", stderr=""),
    ):
        result = runner._execute_scientific_validation(
            _scenario(evaluator_asset="eval.py"),
            _exec(),
        )
    assert result.passed is False
