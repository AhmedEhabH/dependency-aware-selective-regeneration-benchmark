from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pytest

from benchmark.config.models import ExecutionConfig
from benchmark.core.enums import ActionKind, ArtifactType, RunStatus
from benchmark.core.models import (
    ArtifactRef,
    ArtifactUniverse,
    ImpactDecision,
    ImpactPrediction,
    LLMResponse,
    RepositoryIdentity,
    RepositorySnapshot,
    RequirementChange,
    RunIdentity,
    RunRecord,
    TokenUsage,
)
from benchmark.execution.budgets import BudgetManager, resolve_completion_allowance
from benchmark.execution.isolation import IsolationContext
from benchmark.execution.pipeline import PipelineConfig
from benchmark.execution.regeneration import SharedRegenerationExecutor
from benchmark.execution.runner import RunnerConfig, _WorkflowMetricAccumulator
from benchmark.repositories.workspace import WorkspacePath
from benchmark.selection.planner import RegenerationPlan
from benchmark.strategies.iterative_agent import IterativeRepositoryAgentStrategy

# ---------------------------------------------------------------------------
# A. TokenUsage
# ---------------------------------------------------------------------------


def test_token_usage_requires_integer_values() -> None:
    TokenUsage(prompt_tokens=1, completion_tokens=2, total_tokens=3)
    with pytest.raises(ValueError):
        TokenUsage(prompt_tokens="1", completion_tokens=2, total_tokens=3)
    with pytest.raises(ValueError):
        TokenUsage(prompt_tokens=1, completion_tokens="2", total_tokens=3)
    with pytest.raises(ValueError):
        TokenUsage(prompt_tokens=1, completion_tokens=2, total_tokens="3")


def test_token_usage_rejects_boolean_values() -> None:
    with pytest.raises(ValueError, match="integer, not bool"):
        TokenUsage(prompt_tokens=True, completion_tokens=2, total_tokens=3)
    with pytest.raises(ValueError, match="integer, not bool"):
        TokenUsage(prompt_tokens=1, completion_tokens=False, total_tokens=3)
    with pytest.raises(ValueError, match="integer, not bool"):
        TokenUsage(prompt_tokens=1, completion_tokens=2, total_tokens=False)


def test_token_usage_rejects_negative_values() -> None:
    with pytest.raises(ValueError):
        TokenUsage(prompt_tokens=-1, completion_tokens=2, total_tokens=1)
    with pytest.raises(ValueError):
        TokenUsage(prompt_tokens=1, completion_tokens=-2, total_tokens=-1)
    with pytest.raises(ValueError):
        TokenUsage(prompt_tokens=1, completion_tokens=2, total_tokens=-3)


def test_token_usage_rejects_inconsistent_total() -> None:
    with pytest.raises(ValueError, match="total_tokens"):
        TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=20)


def test_token_usage_accepts_exact_identity() -> None:
    tu = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
    assert tu.prompt_tokens == 10
    assert tu.completion_tokens == 5
    assert tu.total_tokens == 15


# ---------------------------------------------------------------------------
# B. Configuration resolution
# ---------------------------------------------------------------------------


def _dummy_identity() -> RunIdentity:
    return RunIdentity(run_id="test", protocol_version="1.0", repository_commit_sha="abc", scenario_id="s1", strategy_name="s")


def _make_sci(pm: float = 0.0, pb: float = 0.0, pe: float = 0.0) -> Any:
    from benchmark.execution.post_generation import PostGenerationResult
    from benchmark.execution.runner import _ScientificValidationResult
    from benchmark.execution.scenario_evaluator import ScenarioEvaluatorResult
    from benchmark.execution.validation import FunctionalValidationResult
    return _ScientificValidationResult(
        migration=PostGenerationResult(passed=True, exit_code=0, stdout="", stderr="", created_paths=(), duration_seconds=pm),
        baseline=FunctionalValidationResult(passed=True, exit_code=0, stdout="", stderr="", duration_seconds=pb),
        evaluator=ScenarioEvaluatorResult(passed=True, exit_code=0, stdout="", stderr="", error="", checks=(), duration_seconds=pe),
        passed=True, failed_stage=None, failure_kind=None, feedback="",
        duration_seconds=pm + pb + pe,
    )


def test_runner_config_defaults_to_4096_per_call_and_unlimited_total() -> None:
    cfg = RunnerConfig(strategy_name="test", backend_name="mock", protocol_version="1.0")
    assert cfg.max_completion_tokens_per_call == 4096
    assert cfg.max_total_workflow_tokens == 0
    assert cfg.resolved_max_total_workflow_tokens == 0


def test_pipeline_config_defaults_to_4096_per_call_and_unlimited_total() -> None:
    cfg = PipelineConfig(protocol_version="1.0")
    assert cfg.max_completion_tokens_per_call == 4096
    assert cfg.max_total_workflow_tokens == 0
    assert cfg.resolved_max_total_workflow_tokens == 0


def test_execution_config_defaults_to_4096_per_call_and_unlimited_total() -> None:
    cfg = ExecutionConfig()
    assert cfg.max_completion_tokens_per_call == 4096
    assert cfg.max_total_workflow_tokens == 0
    assert cfg.resolved_max_total_workflow_tokens == 0


def test_explicit_total_workflow_ceiling_resolves() -> None:
    cfg = ExecutionConfig(max_total_workflow_tokens=8192)
    assert cfg.resolved_max_total_workflow_tokens == 8192
    assert cfg.max_total_workflow_tokens == 8192
    assert cfg.max_tokens == 0


def test_legacy_runner_total_alias_resolves() -> None:
    cfg = RunnerConfig(strategy_name="t", backend_name="m", protocol_version="1.0", max_tokens=4096)
    assert cfg.resolved_max_total_workflow_tokens == 4096


def test_legacy_pipeline_total_alias_resolves() -> None:
    cfg = PipelineConfig(protocol_version="1.0", max_tokens_per_run=4096)
    assert cfg.resolved_max_total_workflow_tokens == 4096


def test_equal_explicit_and_legacy_totals_are_allowed() -> None:
    cfg = RunnerConfig(
        strategy_name="t", backend_name="m", protocol_version="1.0",
        max_tokens=4096, max_total_workflow_tokens=4096,
    )
    assert cfg.resolved_max_total_workflow_tokens == 4096


def test_conflicting_explicit_and_legacy_totals_fail() -> None:
    with pytest.raises(ValueError):
        RunnerConfig(
            strategy_name="t", backend_name="m", protocol_version="1.0",
            max_tokens=4096, max_total_workflow_tokens=8192,
        )
    with pytest.raises(ValueError):
        PipelineConfig(protocol_version="1.0", max_tokens_per_run=1000, max_total_workflow_tokens=2000)
    with pytest.raises(ValueError):
        ExecutionConfig(max_tokens=1000, max_total_workflow_tokens=2000)


def test_zero_or_negative_per_call_limit_fails() -> None:
    with pytest.raises(ValueError):
        ExecutionConfig(max_completion_tokens_per_call=0)
    with pytest.raises(ValueError):
        ExecutionConfig(max_completion_tokens_per_call=-5)


def test_negative_total_workflow_limit_fails() -> None:
    with pytest.raises(ValueError):
        ExecutionConfig(max_total_workflow_tokens=-1)


def test_boolean_token_limits_fail() -> None:
    with pytest.raises(ValueError):
        TokenUsage(prompt_tokens=True, completion_tokens=2, total_tokens=3)


# ---------------------------------------------------------------------------
# C. Budget and allowance
# ---------------------------------------------------------------------------


def test_unlimited_total_returns_full_per_call_allowance() -> None:
    result = resolve_completion_allowance(
        max_completion_tokens_per_call=4096,
        remaining_total_workflow_tokens=0,
        prompt_tokens=100,
    )
    assert result == 4096


def test_previous_calls_do_not_reduce_unlimited_allowance() -> None:
    for prompt in [0, 10, 100, 1000, 5000]:
        result = resolve_completion_allowance(
            max_completion_tokens_per_call=4096,
            remaining_total_workflow_tokens=0,
            prompt_tokens=prompt,
        )
        assert result == 4096


def test_positive_total_reduces_allowance_only_when_needed() -> None:
    result = resolve_completion_allowance(
        max_completion_tokens_per_call=4096,
        remaining_total_workflow_tokens=5000,
        prompt_tokens=10,
    )
    assert result == min(4096, 5000 - 10)


def test_prompt_tokens_are_subtracted_only_under_positive_total() -> None:
    result = resolve_completion_allowance(
        max_completion_tokens_per_call=4096,
        remaining_total_workflow_tokens=100,
        prompt_tokens=30,
    )
    assert result == min(4096, 100 - 30)


def test_prompt_equal_to_remaining_total_returns_zero() -> None:
    result = resolve_completion_allowance(
        max_completion_tokens_per_call=4096,
        remaining_total_workflow_tokens=50,
        prompt_tokens=50,
    )
    assert result == 0


def test_allowance_rejects_invalid_inputs() -> None:
    with pytest.raises(ValueError):
        resolve_completion_allowance(max_completion_tokens_per_call=0, remaining_total_workflow_tokens=0, prompt_tokens=0)
    with pytest.raises(ValueError):
        resolve_completion_allowance(max_completion_tokens_per_call=4096, remaining_total_workflow_tokens=-1, prompt_tokens=0)
    with pytest.raises(ValueError):
        resolve_completion_allowance(max_completion_tokens_per_call=4096, remaining_total_workflow_tokens=0, prompt_tokens=-1)


def test_budget_manager_exposes_total_limit_without_private_access() -> None:
    bm = BudgetManager(max_tokens=4096)
    assert bm.has_total_token_limit is True
    assert bm.remaining_total_tokens == 4096
    assert bm.remaining_total_tokens == bm.remaining_tokens


def test_budget_manager_unlimited_remaining_is_zero_with_explicit_flag() -> None:
    bm = BudgetManager(max_tokens=0)
    assert bm.has_total_token_limit is False
    assert bm.remaining_total_tokens == 0


def test_budget_records_measured_tokens_on_failed_run() -> None:
    bm = BudgetManager(max_tokens=100)
    bm.record_attempt()
    bm.record_tokens(30)
    assert bm.remaining_tokens == 70
    assert not bm.state.exhausted
    bm.record_tokens(80)
    assert bm.state.exhausted


def test_completion_allowance_exact_arithmetic() -> None:
    result = resolve_completion_allowance(
        max_completion_tokens_per_call=20,
        remaining_total_workflow_tokens=30,
        prompt_tokens=5,
    )
    assert result == 20
    result = resolve_completion_allowance(
        max_completion_tokens_per_call=20,
        remaining_total_workflow_tokens=15,
        prompt_tokens=10,
    )
    assert result == 5


# ---------------------------------------------------------------------------
# D. Dummy result for SharedRegenerationExecutor tests
# ---------------------------------------------------------------------------


def _dummy_exec_result(
    prompt: int = 0,
    completion: int = 0,
    calls: int = 0,
    duration: float = 0.0,
) -> Any:
    from benchmark.execution.regeneration import RegenerationExecutionResult
    return RegenerationExecutionResult(
        artifacts=(),
        prompt_tokens=prompt,
        completion_tokens=completion,
        total_tokens=prompt + completion,
        model_calls=calls,
        duration_seconds=duration,
    )


class _ExecutorCaptureBackend:
    token_accounting_mode: str = "fixture_or_approximate"

    def __init__(
        self,
        responses: list[tuple[str, TokenUsage]],
        prompt_estimate: int = 10,
    ) -> None:
        self._responses = responses
        self._idx = 0
        self.prompt_estimate = prompt_estimate
        self.last_counted_prompt = ""
        self.captured_max_tokens: list[int] = []
        self.captured_prompts: list[str] = []
        self.captured_temperatures: list[float] = []
        self.call_count = 0

    def count_prompt_tokens(self, prompt: str) -> int:
        self.last_counted_prompt = prompt
        return self.prompt_estimate

    async def generate(
        self,
        prompt: str = "",
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        self.captured_prompts.append(prompt)
        self.captured_temperatures.append(temperature)
        self.captured_max_tokens.append(max_tokens)
        self.call_count += 1
        text, usage = self._responses[min(self._idx, len(self._responses) - 1)]
        self._idx += 1
        return LLMResponse(text=text, token_usage=usage, finish_reason="stop")


class _AgentCaptureBackend:
    token_accounting_mode: str = "fixture_or_approximate"

    def __init__(
        self,
        responses: list[tuple[dict[str, Any], TokenUsage]],
        prompt_estimate: int = 50,
    ) -> None:
        self._responses = responses
        self._idx = 0
        self.prompt_estimate = prompt_estimate
        self.last_counted_prompt = ""
        self.captured_max_tokens: list[int] = []
        self.captured_prompts: list[str] = []
        self.captured_temperatures: list[float] = []
        self.call_count = 0

    def count_prompt_tokens(self, prompt: str) -> int:
        self.last_counted_prompt = prompt
        return self.prompt_estimate

    async def generate(
        self,
        prompt: str = "",
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        self.captured_prompts.append(prompt)
        self.captured_temperatures.append(temperature)
        self.captured_max_tokens.append(max_tokens)
        self.call_count += 1
        action, usage = self._responses[min(self._idx, len(self._responses) - 1)]
        self._idx += 1
        return LLMResponse(text=json.dumps(action), token_usage=usage, finish_reason="stop")


def _make_executor_context(
    tmp_path: Path,
    paths: list[str],
) -> tuple[IsolationContext, RegenerationPlan]:
    ws_root = tmp_path / "executor_workspace"
    ws_root.mkdir(parents=True, exist_ok=True)
    for path in paths:
        target = ws_root / path.lstrip("/")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("original content", encoding="utf-8")
    snap_base = tmp_path / "executor_snapshot"
    snap_base.mkdir(exist_ok=True)
    isolation = IsolationContext(
        workspace=WorkspacePath(root=str(ws_root)),
        snapshot_base=snap_base,
    )
    plan = RegenerationPlan(
        ordered_artifacts=tuple(
            ArtifactRef(path=path, artifact_type=ArtifactType.source) for path in paths
        ),
        actions={path: ActionKind.regenerate for path in paths},
    )
    return isolation, plan


def _final_action(path: str, usage: TokenUsage) -> tuple[dict[str, Any], TokenUsage]:
    return ({"action": "final", "selected_paths": [path], "rationale": "ok"}, usage)


def _tool_action(name: str, path: str, usage: TokenUsage) -> tuple[dict[str, Any], TokenUsage]:
    return ({"action": name, "path": path}, usage)


def _make_agent_context(
    tmp_path: Path,
    backend: _AgentCaptureBackend,
) -> tuple[
    IterativeRepositoryAgentStrategy,
    ArtifactUniverse,
    RepositorySnapshot,
    RequirementChange,
]:
    ws_root = tmp_path / "agent_workspace"
    (ws_root / "src").mkdir(parents=True, exist_ok=True)
    (ws_root / "src" / "a.py").write_text("def a():\n    ...\n", encoding="utf-8")
    strategy = IterativeRepositoryAgentStrategy(backend=backend)
    strategy.begin_run(ws_root)
    universe = ArtifactUniverse(
        artifacts=(ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
    )
    repo = RepositorySnapshot(
        identity=RepositoryIdentity(name="repo", url="https://example.com/repo"),
        commit_sha="abc123",
        path=str(ws_root),
    )
    change = RequirementChange(
        before="legacy behavior",
        after="new behavior",
        acceptance_criteria=("passes new tests",),
    )
    return strategy, universe, repo, change


def test_executor_reports_exact_prompt_completion_total_and_calls() -> None:
    result = _dummy_exec_result(prompt=30, completion=11, calls=2, duration=2.0)
    assert result.prompt_tokens == 30
    assert result.completion_tokens == 11
    assert result.total_tokens == 41
    assert result.model_calls == 2
    assert result.duration_seconds == 2.0


def test_executor_rejects_zero_per_call_limit() -> None:
    with pytest.raises(ValueError):
        resolve_completion_allowance(max_completion_tokens_per_call=0, remaining_total_workflow_tokens=0, prompt_tokens=0)


def test_executor_rejects_negative_remaining_total() -> None:
    with pytest.raises(ValueError):
        resolve_completion_allowance(max_completion_tokens_per_call=4096, remaining_total_workflow_tokens=-1, prompt_tokens=0)


def test_zero_allowance_skips_backend_call(tmp_path: Path) -> None:
    isolation, plan = _make_executor_context(tmp_path, ["src/a.py"])
    backend = _ExecutorCaptureBackend(
        responses=[("content-a", TokenUsage(0, 8, 8))],
        prompt_estimate=15,
    )
    executor = SharedRegenerationExecutor(backend=backend)
    result = executor.execute(
        plan,
        isolation,
        max_completion_tokens_per_call=4096,
        remaining_total_workflow_tokens=10,
    )
    assert backend.call_count == 0
    assert result.model_calls == 0
    assert any("Token budget exhausted" in f for f in result.failures)


def test_backend_token_overrun_fails_closed_and_preserves_usage(tmp_path: Path) -> None:
    isolation, plan = _make_executor_context(tmp_path, ["src/a.py", "src/b.py"])
    backend = _ExecutorCaptureBackend(
        responses=[("content-a", TokenUsage(0, 25, 25))],
        prompt_estimate=10,
    )
    executor = SharedRegenerationExecutor(backend=backend)
    result = executor.execute(
        plan,
        isolation,
        max_completion_tokens_per_call=20,
        remaining_total_workflow_tokens=30,
    )
    assert backend.call_count == 1
    assert result.model_calls == 1
    assert any("Backend overrun" in f for f in result.failures)
    assert result.completion_tokens == 25
    assert result.total_tokens == 25
    assert all(g.status == "rejected" for g in result.artifacts)
    target = Path(isolation.workspace.root) / "src/b.py"
    assert target.read_text(encoding="utf-8") == "original content"


def test_three_files_each_receive_4096_when_total_unlimited(tmp_path: Path) -> None:
    isolation, plan = _make_executor_context(
        tmp_path, ["src/a.py", "src/b.py", "src/c.py"]
    )
    backend = _ExecutorCaptureBackend(
        responses=[
            ("content-a", TokenUsage(0, 8, 8)),
            ("content-b", TokenUsage(0, 8, 8)),
            ("content-c", TokenUsage(0, 8, 8)),
        ],
        prompt_estimate=100,
    )
    executor = SharedRegenerationExecutor(backend=backend)
    result = executor.execute(
        plan,
        isolation,
        max_completion_tokens_per_call=4096,
        remaining_total_workflow_tokens=0,
    )
    assert backend.captured_max_tokens == [4096, 4096, 4096]
    assert backend.call_count == 3
    assert result.model_calls == 3
    assert result.failures == ()
    assert result.total_tokens == 24


def test_unlimited_call_does_not_subtract_prompt_estimate() -> None:
    result = resolve_completion_allowance(
        max_completion_tokens_per_call=4096,
        remaining_total_workflow_tokens=0,
        prompt_tokens=999999,
    )
    assert result == 4096


def test_positive_total_ceiling_reduces_later_call(tmp_path: Path) -> None:
    isolation, plan = _make_executor_context(
        tmp_path, ["src/a.py", "src/b.py", "src/c.py"]
    )
    backend = _ExecutorCaptureBackend(
        responses=[
            ("content-a", TokenUsage(0, 18, 18)),
            ("content-b", TokenUsage(0, 18, 18)),
        ],
        prompt_estimate=10,
    )
    executor = SharedRegenerationExecutor(backend=backend)
    result = executor.execute(
        plan,
        isolation,
        max_completion_tokens_per_call=20,
        remaining_total_workflow_tokens=30,
    )
    assert backend.captured_max_tokens == [20, 2]
    assert backend.call_count == 2
    assert result.model_calls == 2
    assert any("Backend overrun" in f for f in result.failures)
    assert result.prompt_tokens == 0
    assert result.completion_tokens == 36
    assert result.total_tokens == 36


def test_agent_initial_call_receives_per_call_limit(tmp_path: Path) -> None:
    backend = _AgentCaptureBackend(
        responses=[_final_action("src/a.py", TokenUsage(50, 10, 60))],
        prompt_estimate=50,
    )
    strategy, universe, repo, change = _make_agent_context(tmp_path, backend)
    prediction = strategy.analyze_impact(
        repo,
        change,
        universe,
        max_completion_tokens_per_call=4096,
        remaining_total_workflow_tokens=0,
    )
    assert backend.captured_max_tokens == [4096]
    assert backend.call_count == 1
    assert prediction.token_usage is not None
    assert prediction.token_usage.prompt_tokens == 50
    assert prediction.token_usage.completion_tokens == 10
    assert prediction.token_usage.total_tokens == 60
    assert [d.action for d in prediction.decisions] == [ActionKind.regenerate]


def test_agent_revision_call_receives_per_call_limit(tmp_path: Path) -> None:
    backend = _AgentCaptureBackend(
        responses=[_final_action("src/a.py", TokenUsage(50, 10, 60))],
        prompt_estimate=50,
    )
    strategy, universe, repo, change = _make_agent_context(tmp_path, backend)
    previous = ImpactPrediction(
        decisions=(
            ImpactDecision(
                artifact=universe.artifacts[0],
                action=ActionKind.regenerate,
                rationale="previous",
            ),
        ),
        token_usage=TokenUsage(50, 10, 60),
    )
    prediction = strategy.revise_plan(
        change,
        universe,
        previous,
        exit_code=1,
        val_stdout="",
        val_stderr="",
        workspace_summary="",
        remaining_attempts=1,
        remaining_tokens=0,
        max_completion_tokens_per_call=4096,
        remaining_total_workflow_tokens=0,
    )
    assert backend.captured_max_tokens == [4096]
    assert backend.call_count == 1
    assert prediction.token_usage is not None
    assert prediction.token_usage.total_tokens == 60
    assert [d.action for d in prediction.decisions] == [ActionKind.regenerate]


def test_agent_unlimited_total_does_not_shrink_later_calls(tmp_path: Path) -> None:
    backend = _AgentCaptureBackend(
        responses=[
            _tool_action("list_files", ".", TokenUsage(0, 0, 0)),
            _tool_action("list_files", ".", TokenUsage(0, 0, 0)),
            _final_action("src/a.py", TokenUsage(0, 0, 0)),
        ],
        prompt_estimate=50,
    )
    strategy, universe, repo, change = _make_agent_context(tmp_path, backend)
    prediction = strategy.analyze_impact(
        repo,
        change,
        universe,
        max_completion_tokens_per_call=4096,
        remaining_total_workflow_tokens=0,
    )
    assert backend.captured_max_tokens == [4096, 4096, 4096]
    assert backend.call_count == 3
    assert prediction.token_usage is not None
    assert prediction.token_usage.total_tokens == 0


def test_agent_positive_total_can_reduce_later_call(tmp_path: Path) -> None:
    backend = _AgentCaptureBackend(
        responses=[
            _tool_action("list_files", ".", TokenUsage(0, 60, 60)),
            _tool_action("list_files", ".", TokenUsage(0, 60, 60)),
            _final_action("src/a.py", TokenUsage(0, 60, 60)),
        ],
        prompt_estimate=50,
    )
    strategy, universe, repo, change = _make_agent_context(tmp_path, backend)
    prediction = strategy.analyze_impact(
        repo,
        change,
        universe,
        max_completion_tokens_per_call=4096,
        remaining_total_workflow_tokens=500,
    )
    assert backend.captured_max_tokens == [450, 390, 330]
    assert backend.call_count == 3
    assert all(t < 4096 for t in backend.captured_max_tokens)
    assert prediction.token_usage is not None
    assert prediction.token_usage.total_tokens == 180


def test_agent_zero_allowance_does_not_call_backend(tmp_path: Path) -> None:
    backend = _AgentCaptureBackend(
        responses=[_final_action("src/a.py", TokenUsage(0, 0, 0))],
        prompt_estimate=50,
    )
    strategy, universe, repo, change = _make_agent_context(tmp_path, backend)
    prediction = strategy.analyze_impact(
        repo,
        change,
        universe,
        max_completion_tokens_per_call=4096,
        remaining_total_workflow_tokens=5,
    )
    assert backend.call_count == 0
    assert prediction.token_usage is not None
    assert prediction.token_usage.total_tokens == 0
    assert any("no paths selected" in e for e in prediction.errors)


def test_agent_prediction_usage_is_incremental_not_cumulative(tmp_path: Path) -> None:
    backend = _AgentCaptureBackend(
        responses=[_final_action("src/a.py", TokenUsage(50, 10, 60))],
        prompt_estimate=50,
    )
    strategy, universe, repo, change = _make_agent_context(tmp_path, backend)
    first = strategy.analyze_impact(
        repo,
        change,
        universe,
        max_completion_tokens_per_call=4096,
        remaining_total_workflow_tokens=0,
    )
    second = strategy.analyze_impact(
        repo,
        change,
        universe,
        max_completion_tokens_per_call=4096,
        remaining_total_workflow_tokens=0,
    )
    assert first.token_usage is not None
    assert second.token_usage is not None
    assert first.token_usage.total_tokens == 60
    assert second.token_usage.total_tokens == 60
    assert second.token_usage.total_tokens < first.token_usage.total_tokens + 60


def test_agent_eight_call_cap_is_independent_from_token_limit(tmp_path: Path) -> None:
    backend = _AgentCaptureBackend(
        responses=[_tool_action("list_files", ".", TokenUsage(0, 0, 0))],
        prompt_estimate=50,
    )
    strategy, universe, repo, change = _make_agent_context(tmp_path, backend)
    prediction = strategy.analyze_impact(
        repo,
        change,
        universe,
        max_completion_tokens_per_call=4096,
        remaining_total_workflow_tokens=0,
    )
    assert backend.call_count == 8
    assert backend.captured_max_tokens == [4096] * 8
    assert any("no remaining agent calls" in e for e in prediction.errors)
    assert all(d.action == ActionKind.preserve for d in prediction.decisions)


# ---------------------------------------------------------------------------
# E. Accumulator identities
# ---------------------------------------------------------------------------


def test_accumulator_selection_identity() -> None:
    acc = _WorkflowMetricAccumulator()
    acc.add_selection(TokenUsage(prompt_tokens=11, completion_tokens=7, total_tokens=18), model_calls=1, duration_seconds=1.0)
    fields = acc.as_record_fields(final_scientific_result=None, token_accounting_mode="exact_tokenizer")
    assert fields["selection_prompt_tokens"] == 11
    assert fields["selection_completion_tokens"] == 7
    assert fields["selection_total_tokens"] == 18
    assert fields["selection_model_calls"] == 1
    assert fields["selection_duration_seconds"] == 1.0


def test_accumulator_initial_regeneration_identity() -> None:
    acc = _WorkflowMetricAccumulator()
    acc.add_code_generation(_dummy_exec_result(prompt=30, completion=11, calls=2, duration=2.0), is_repair=False)
    fields = acc.as_record_fields(final_scientific_result=None, token_accounting_mode="exact_tokenizer")
    assert fields["regeneration_prompt_tokens"] == 30
    assert fields["regeneration_completion_tokens"] == 11
    assert fields["regeneration_total_tokens"] == 41
    assert fields["regeneration_model_calls"] == 2
    assert fields["regeneration_duration_seconds"] == 2.0


def test_accumulator_repair_identity() -> None:
    acc = _WorkflowMetricAccumulator()
    acc.add_code_generation(_dummy_exec_result(prompt=19, completion=8, calls=1, duration=3.0), is_repair=True)
    fields = acc.as_record_fields(final_scientific_result=None, token_accounting_mode="exact_tokenizer")
    assert fields["repair_prompt_tokens"] == 19
    assert fields["repair_completion_tokens"] == 8
    assert fields["repair_total_tokens"] == 27
    assert fields["repair_model_calls"] == 1
    assert fields["repair_duration_seconds"] == 3.0
    assert fields["repair_attempts"] == 1


def test_accumulator_cumulative_scientific_durations() -> None:
    from benchmark.execution.post_generation import PostGenerationResult
    from benchmark.execution.runner import _ScientificValidationResult
    from benchmark.execution.scenario_evaluator import ScenarioEvaluatorResult
    from benchmark.execution.validation import FunctionalValidationResult

    acc = _WorkflowMetricAccumulator()
    sci = _ScientificValidationResult(
        migration=PostGenerationResult(passed=True, exit_code=0, stdout="", stderr="", created_paths=(), duration_seconds=0.4),
        baseline=FunctionalValidationResult(passed=True, exit_code=0, stdout="", stderr="", duration_seconds=0.5),
        evaluator=ScenarioEvaluatorResult(passed=True, exit_code=0, stdout="", stderr="", error="", checks=(), duration_seconds=0.8),
        passed=True, failed_stage=None, failure_kind=None, feedback="", duration_seconds=1.7,
    )
    acc.add_scientific(sci)
    sci2 = _ScientificValidationResult(
        migration=PostGenerationResult(passed=True, exit_code=0, stdout="", stderr="", created_paths=(), duration_seconds=0.6),
        baseline=FunctionalValidationResult(passed=True, exit_code=0, stdout="", stderr="", duration_seconds=0.7),
        evaluator=ScenarioEvaluatorResult(passed=True, exit_code=0, stdout="", stderr="", error="", checks=(), duration_seconds=0.9),
        passed=True, failed_stage=None, failure_kind=None, feedback="", duration_seconds=2.2,
    )
    acc.add_scientific(sci2)
    fields = acc.as_record_fields(final_scientific_result=sci2, token_accounting_mode="exact_tokenizer")
    assert math.isclose(fields["migration_duration_seconds"], 1.0, rel_tol=1e-9, abs_tol=1e-9)
    assert math.isclose(fields["baseline_validation_duration_seconds"], 1.2, rel_tol=1e-9, abs_tol=1e-9)
    assert math.isclose(fields["scenario_evaluator_duration_seconds"], 1.7, rel_tol=1e-9, abs_tol=1e-9)


def test_accumulator_tool_duration_is_not_double_counted() -> None:
    acc = _WorkflowMetricAccumulator()
    acc.add_selection(TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15), model_calls=1, duration_seconds=1.0, tool_calls=2, tool_duration_seconds=0.25)
    acc.add_code_generation(_dummy_exec_result(prompt=10, completion=5, calls=1, duration=2.0), is_repair=False)
    acc.add_code_generation(_dummy_exec_result(prompt=10, completion=5, calls=1, duration=3.0), is_repair=True)
    acc.add_scientific(_make_sci(pm=1.0, pb=1.2, pe=1.7))
    fields = acc.as_record_fields(final_scientific_result=None, token_accounting_mode="exact_tokenizer")
    total_dur = fields["total_workflow_duration_seconds"]
    stage_sum = (
        fields["selection_duration_seconds"]
        + fields["regeneration_duration_seconds"]
        + fields["repair_duration_seconds"]
        + fields["migration_duration_seconds"]
        + fields["baseline_validation_duration_seconds"]
        + fields["scenario_evaluator_duration_seconds"]
    )
    assert math.isclose(total_dur, stage_sum, rel_tol=1e-9, abs_tol=1e-9)
    assert math.isclose(fields["selection_tool_duration_seconds"], 0.25, rel_tol=1e-9, abs_tol=1e-9)


def test_accumulator_total_token_identity() -> None:
    acc = _WorkflowMetricAccumulator()
    acc.add_selection(TokenUsage(prompt_tokens=11, completion_tokens=7, total_tokens=18), model_calls=1, duration_seconds=1.0)
    acc.add_code_generation(_dummy_exec_result(prompt=30, completion=11, calls=2, duration=2.0), is_repair=False)
    acc.add_code_generation(_dummy_exec_result(prompt=19, completion=8, calls=1, duration=3.0), is_repair=True)
    fields = acc.as_record_fields(final_scientific_result=None, token_accounting_mode="exact_tokenizer")
    assert fields["total_workflow_tokens"] == 18 + 41 + 27


def test_accumulator_total_call_identity() -> None:
    acc = _WorkflowMetricAccumulator()
    acc.add_selection(TokenUsage(prompt_tokens=11, completion_tokens=7, total_tokens=18), model_calls=1, duration_seconds=1.0)
    acc.add_code_generation(_dummy_exec_result(prompt=30, completion=11, calls=2, duration=2.0), is_repair=False)
    acc.add_code_generation(_dummy_exec_result(prompt=19, completion=8, calls=1, duration=3.0), is_repair=True)
    fields = acc.as_record_fields(final_scientific_result=None, token_accounting_mode="exact_tokenizer")
    assert fields["total_workflow_model_calls"] == 1 + 2 + 1


def test_accumulator_total_duration_identity() -> None:
    acc = _WorkflowMetricAccumulator()
    acc.add_selection(TokenUsage(prompt_tokens=11, completion_tokens=7, total_tokens=18), model_calls=1, duration_seconds=1.0)
    acc.add_code_generation(_dummy_exec_result(prompt=30, completion=11, calls=2, duration=2.0), is_repair=False)
    acc.add_code_generation(_dummy_exec_result(prompt=19, completion=8, calls=1, duration=3.0), is_repair=True)
    acc.add_scientific(_make_sci(pm=1.0, pb=1.2, pe=1.7))
    fields = acc.as_record_fields(final_scientific_result=None, token_accounting_mode="exact_tokenizer")
    expected = 1.0 + 2.0 + 3.0 + 1.0 + 1.2 + 1.7
    assert math.isclose(fields["total_workflow_duration_seconds"], expected, rel_tol=1e-9, abs_tol=1e-9)


def test_accumulator_from_record_preserves_all_metrics() -> None:
    record = RunRecord(
        identity=_dummy_identity(),
        status=RunStatus.succeeded,
        token_usage=TokenUsage(prompt_tokens=60, completion_tokens=26, total_tokens=86),
        selection_prompt_tokens=11, selection_completion_tokens=7, selection_total_tokens=18,
        selection_model_calls=1, selection_duration_seconds=1.0,
        regeneration_prompt_tokens=30, regeneration_completion_tokens=11, regeneration_total_tokens=41,
        regeneration_model_calls=2, regeneration_duration_seconds=2.0,
        repair_prompt_tokens=19, repair_completion_tokens=8, repair_total_tokens=27,
        repair_model_calls=1, repair_duration_seconds=3.0, repair_attempts=1,
        migration_duration_seconds=1.0, baseline_validation_duration_seconds=1.2,
        scenario_evaluator_duration_seconds=1.7,
        total_workflow_tokens=86, total_workflow_model_calls=4,
        total_workflow_duration_seconds=9.9,
    )
    acc = _WorkflowMetricAccumulator.from_record(record)
    fields = acc.as_record_fields(final_scientific_result=None, token_accounting_mode="exact_tokenizer")
    assert fields["selection_prompt_tokens"] == 11
    assert fields["selection_completion_tokens"] == 7
    assert fields["regeneration_prompt_tokens"] == 30
    assert fields["repair_prompt_tokens"] == 19
    assert fields["total_workflow_tokens"] == 86


def test_accumulator_failed_record_preserves_consumed_metrics() -> None:
    acc = _WorkflowMetricAccumulator()
    acc.add_selection(TokenUsage(prompt_tokens=11, completion_tokens=7, total_tokens=18), model_calls=1, duration_seconds=1.0)
    acc.add_code_generation(_dummy_exec_result(prompt=30, completion=11, calls=2, duration=2.0), is_repair=False)
    acc.add_code_generation(_dummy_exec_result(prompt=19, completion=8, calls=1, duration=3.0), is_repair=True)
    fields = acc.as_record_fields(final_scientific_result=None, token_accounting_mode="exact_tokenizer")
    assert fields["selection_total_tokens"] == 18
    assert fields["regeneration_total_tokens"] == 41
    assert fields["repair_total_tokens"] == 27


# ---------------------------------------------------------------------------
# F. RunRecord semantics
# ---------------------------------------------------------------------------


def test_new_record_legacy_token_usage_mirrors_workflow_total() -> None:
    record = RunRecord(
        identity=_dummy_identity(),
        status=RunStatus.succeeded,
        token_usage=TokenUsage(prompt_tokens=60, completion_tokens=26, total_tokens=86),
        selection_prompt_tokens=11, selection_completion_tokens=7, selection_total_tokens=18,
        regeneration_prompt_tokens=30, regeneration_completion_tokens=11, regeneration_total_tokens=41,
        repair_prompt_tokens=19, repair_completion_tokens=8, repair_total_tokens=27,
        total_workflow_tokens=86, total_workflow_model_calls=0,
    )
    assert record.token_usage.total_tokens == record.total_workflow_tokens


def test_new_record_model_calls_equal_workflow_calls() -> None:
    record = RunRecord(
        identity=_dummy_identity(),
        status=RunStatus.succeeded,
        selection_model_calls=1,
        regeneration_model_calls=2,
        repair_model_calls=1,
        total_workflow_model_calls=4,
    )
    assert record.total_workflow_model_calls == 4


def test_repair_attempts_count_executor_attempts_not_files() -> None:
    record = RunRecord(
        identity=_dummy_identity(),
        status=RunStatus.succeeded,
        repair_attempts=2,
        repair_model_calls=4,
        repair_total_tokens=0, repair_prompt_tokens=0, repair_completion_tokens=0,
        total_workflow_model_calls=4,
    )
    assert record.repair_attempts == 2
    assert record.repair_model_calls == 4


def test_record_rejects_negative_repair_metrics() -> None:
    with pytest.raises(ValueError):
        RunRecord(identity=_dummy_identity(), status=RunStatus.succeeded, repair_prompt_tokens=-1)
    with pytest.raises(ValueError):
        RunRecord(identity=_dummy_identity(), status=RunStatus.succeeded, repair_attempts=-1)


def test_record_rejects_invalid_selection_count_types() -> None:
    for field_name in ("selection_tool_calls", "selection_inspected_file_count"):
        with pytest.raises(ValueError, match=f"RunRecord.{field_name}"):
            RunRecord(identity=_dummy_identity(), status=RunStatus.succeeded, **{field_name: True})
        with pytest.raises(ValueError, match=f"RunRecord.{field_name}"):
            RunRecord(identity=_dummy_identity(), status=RunStatus.succeeded, **{field_name: "3"})
        with pytest.raises(ValueError, match=f"RunRecord.{field_name}"):
            RunRecord(identity=_dummy_identity(), status=RunStatus.succeeded, **{field_name: -1})


def test_record_accepts_valid_selection_count_values() -> None:
    record = RunRecord(
        identity=_dummy_identity(),
        status=RunStatus.succeeded,
        selection_tool_calls=4,
        selection_inspected_file_count=7,
    )
    assert record.selection_tool_calls == 4
    assert record.selection_inspected_file_count == 7


def test_record_rejects_invalid_accounting_mode() -> None:
    with pytest.raises(ValueError, match="token_accounting_mode"):
        RunRecord(identity=_dummy_identity(), status=RunStatus.succeeded, token_accounting_mode="invalid_mode")


def test_duration_identity_uses_float_tolerance() -> None:
    record = RunRecord(
        identity=_dummy_identity(),
        status=RunStatus.succeeded,
        selection_duration_seconds=1.0,
        regeneration_duration_seconds=2.0,
        repair_duration_seconds=3.0,
        migration_duration_seconds=1.0,
        baseline_validation_duration_seconds=1.2,
        scenario_evaluator_duration_seconds=1.7,
        total_workflow_duration_seconds=9.9,
    )
    stage_sum = (
        record.selection_duration_seconds
        + record.regeneration_duration_seconds
        + record.repair_duration_seconds
        + record.migration_duration_seconds
        + record.baseline_validation_duration_seconds
        + record.scenario_evaluator_duration_seconds
    )
    assert math.isclose(record.total_workflow_duration_seconds, stage_sum, rel_tol=1e-9, abs_tol=1e-9)


# ---------------------------------------------------------------------------
# G. Qwen and accounting mode
# ---------------------------------------------------------------------------


def test_builtin_backends_expose_frozen_accounting_modes() -> None:
    from benchmark.llm.dry_run_backend import DryRunLLMBackend
    from benchmark.llm.kaggle_qwen_backend import KaggleQwenBackend
    from benchmark.llm.mock_backend import MockLLMBackend, NullLLMBackend
    from benchmark.llm.openrouter_backend import OpenRouterBackend

    assert KaggleQwenBackend.token_accounting_mode == "exact_tokenizer"
    assert MockLLMBackend.token_accounting_mode == "approximate_character"
    assert NullLLMBackend.token_accounting_mode == "none"
    assert DryRunLLMBackend.token_accounting_mode == "fixture_or_approximate"
    assert OpenRouterBackend.token_accounting_mode == "provider_reported"


def test_qwen_prompt_count_uses_tokenizer() -> None:
    from benchmark.llm.kaggle_qwen_backend import KaggleQwenBackend
    backend = KaggleQwenBackend()
    assert backend.token_accounting_mode == "exact_tokenizer"


def test_qwen_prompt_count_failure_raises_model_backend_error() -> None:
    from benchmark.core.exceptions import ModelBackendError
    from benchmark.llm.kaggle_qwen_backend import KaggleQwenBackend
    backend = KaggleQwenBackend()
    with pytest.raises(ModelBackendError):
        backend.count_prompt_tokens("test")


def test_qwen_response_token_identity() -> None:
    tu = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
    assert tu.prompt_tokens + tu.completion_tokens == tu.total_tokens


# ---------------------------------------------------------------------------
# H. Addendum-mandated contract tests (R4 single-pass requirement)
# ---------------------------------------------------------------------------


def test_executor_local_budget_contract(tmp_path: Path) -> None:
    isolation, plan = _make_executor_context(
        tmp_path, ["src/a.py", "src/b.py", "src/c.py"]
    )
    backend = _ExecutorCaptureBackend(
        responses=[
            ("content-a", TokenUsage(10, 80, 90)),
            ("content-b", TokenUsage(10, 80, 90)),
            ("content-c", TokenUsage(12, 10, 22)),
        ],
        prompt_estimate=10,
    )
    executor = SharedRegenerationExecutor(backend=backend)
    result = executor.execute(
        plan,
        isolation,
        max_completion_tokens_per_call=100,
        remaining_total_workflow_tokens=200,
    )
    assert backend.captured_max_tokens == [100, 100, 10]
    assert backend.call_count == 3
    assert result.model_calls == 3
    assert any("Backend total overrun" in f for f in result.failures)
    assert result.prompt_tokens == 32
    assert result.completion_tokens == 170
    assert result.total_tokens == 202
    assert [g.status for g in result.artifacts] == ["generated", "generated", "rejected"]


def test_agent_allowance_below_per_call_limit(tmp_path: Path) -> None:
    backend = _AgentCaptureBackend(
        responses=[_final_action("src/a.py", TokenUsage(50, 10, 60))],
        prompt_estimate=50,
    )
    strategy, universe, repo, change = _make_agent_context(tmp_path, backend)
    prediction = strategy.analyze_impact(
        repo,
        change,
        universe,
        max_completion_tokens_per_call=4096,
        remaining_total_workflow_tokens=500,
    )
    assert backend.captured_max_tokens == [450]
    assert backend.captured_max_tokens[0] < 4096
    assert prediction.token_usage is not None
    assert prediction.token_usage.total_tokens == 60


def test_accumulator_as_record_fields_includes_rollup() -> None:
    from benchmark.execution.runner import _WorkflowMetricAccumulator
    acc = _WorkflowMetricAccumulator()
    acc.add_selection(TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15), model_calls=1, duration_seconds=0.5)
    fields = acc.as_record_fields(final_scientific_result=None, token_accounting_mode="mock")
    assert "selection_prompt_tokens" in fields
    assert "selection_total_tokens" in fields
    assert "selection_model_calls" in fields
    assert "selection_duration_seconds" in fields
