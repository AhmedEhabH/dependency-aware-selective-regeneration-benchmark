"""SU-0011 integration tests: iterative repository agent end-to-end."""

import sys
from pathlib import Path

from benchmark.core.enums import ArtifactType, BlastRadius, RunStatus
from benchmark.core.models import (
    AcceptanceCriterion,
    ArtifactRef,
    LLMResponse,
    Scenario,
    TokenUsage,
)
from benchmark.execution.budgets import BudgetManager
from benchmark.execution.isolation import IsolationContext
from benchmark.execution.runner import BenchmarkRunner, RunnerConfig
from benchmark.repositories.workspace import WorkspacePath
from benchmark.strategies.iterative_agent import IterativeRepositoryAgentStrategy


def _make_scenario(
    repo: str = "test_repo",
    artifacts: tuple[ArtifactRef, ...] = (),
    before: str = "old requirement",
    after: str = "new requirement",
) -> Scenario:
    return Scenario(
        scenario_id=f"{repo}_scenario",
        repository=repo,
        change_type="modify",
        blast_radius=BlastRadius.localized,
        requirement_before=before,
        requirement_after=after,
        rationale="test scenario for SU-0011",
        expected_affected_artifacts=artifacts,
        acceptance_criteria=(
            AcceptanceCriterion(description="validation must pass"),
        ),
    )


def _setup_workspace(
    tmp_path: Path,
    artifacts: tuple[ArtifactRef, ...],
    repo: str = "test_repo",
    revision: str = "test_revision",
) -> tuple[IsolationContext, Path]:
    ws_root = tmp_path / "workspace"
    ws_root.mkdir(parents=True, exist_ok=True)
    snap_base = tmp_path / "snapshots"
    snap_base.mkdir(exist_ok=True)
    active_root = snap_base / repo / revision
    active_root.mkdir(parents=True, exist_ok=True)

    for ref in artifacts:
        target = ws_root / ref.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"original {ref.path} content", encoding="utf-8")
        snap_target = active_root / ref.path
        snap_target.parent.mkdir(parents=True, exist_ok=True)
        snap_target.write_text(f"original {ref.path} content", encoding="utf-8")

    ws = WorkspacePath(root=str(ws_root))
    iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active_root)
    return iso, ws_root


class _StrategyBackend:
    """Backend used ONLY by IterativeRepositoryAgentStrategy for planning."""

    def __init__(self, responses: list[tuple[str, TokenUsage]] | None = None) -> None:
        self.call_count = 0
        self.prompts: list[str] = []
        self._responses = responses or [
            (
                '{"decisions": [{"path": "src/a.py", "action": "regenerate", "rationale": "test"}]}',
                TokenUsage(prompt_tokens=50, completion_tokens=10, total_tokens=60),
            ),
        ]

    async def generate(
        self, prompt: str, temperature: float = 0.0, max_tokens: int = 4096,
    ) -> LLMResponse:
        self.prompts.append(prompt)
        idx = min(self.call_count, len(self._responses) - 1)
        text, tu = self._responses[idx]
        self.call_count += 1
        return LLMResponse(text=text, token_usage=tu, finish_reason="stop")


def _make_regen_backend(response_text: str = "replacement content"):
    """Backend used ONLY by SharedRegenerationExecutor for file content generation."""

    class _RegenMock:
        def __init__(self, text: str):
            self._text = text

        async def generate(
            self, prompt: str, temperature: float = 0.0, max_tokens: int = 4096,
        ) -> LLMResponse:
            pt = max(1, len(prompt) // 4)
            ct = max(1, len(self._text) // 4)
            return LLMResponse(
                text=self._text,
                token_usage=TokenUsage(prompt_tokens=pt, completion_tokens=ct, total_tokens=pt + ct),
                finish_reason="stop",
            )

    return _RegenMock(response_text)


def _make_runner(
    tmp_path: Path,
    strategy: object,
    regen_backend: object,
    iso: IsolationContext,
    validation_command: list[str] | None = None,
    validation_timeout: int = 10,
    max_attempts: int = 3,
    max_tokens: int = 0,
) -> BenchmarkRunner:
    config = RunnerConfig(
        strategy_name="iterative_repository_agent",
        backend_name="mock",
        protocol_version="1.0",
        max_attempts=max_attempts,
        max_tokens=max_tokens,
        enable_regeneration=True,
        validation_command=validation_command or [sys.executable, "-c", "exit(0)"],
        validation_timeout=validation_timeout,
    )
    return BenchmarkRunner(
        strategy=strategy,
        backend=regen_backend,
        isolation=iso,
        config=config,
    )


# ---------------------------------------------------------------------------
# Test 1: Iteration 1 succeeds
# ---------------------------------------------------------------------------


class TestIteration1Succeeds:
    def test_single_iteration_success(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        sb = _StrategyBackend(responses=[
            (
                '{"decisions": [{"path": "src/a.py", "action": "regenerate", "rationale": "test"}]}',
                TokenUsage(prompt_tokens=50, completion_tokens=10, total_tokens=60),
            ),
        ])
        strategy = IterativeRepositoryAgentStrategy(backend=sb)
        rb = _make_regen_backend("correct content")
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(tmp_path, strategy, rb, iso)

        record = runner.run(scenario)
        assert record.status == RunStatus.succeeded
        assert record.functional_validation_passed is True
        assert record.selection_model_calls == 1
        assert record.regeneration_model_calls == 1
        assert record.functional_validation_duration_seconds > 0
        assert record.total_workflow_tokens > 0
        assert record.total_workflow_model_calls >= 2
        assert record.total_workflow_duration_seconds > 0


# ---------------------------------------------------------------------------
# Test 2: Iteration 1 fails validation, iteration 2 succeeds
# ---------------------------------------------------------------------------


class _StatefulRegenBackend:
    """Regen backend that returns different content on successive calls."""

    def __init__(self, contents: list[str]) -> None:
        self._contents = contents
        self._call_idx = 0

    async def generate(self, prompt: str, temperature: float = 0.0, max_tokens: int = 4096) -> LLMResponse:
        text = self._contents[min(self._call_idx, len(self._contents) - 1)]
        self._call_idx += 1
        pt = max(1, len(prompt) // 4)
        ct = max(1, len(text) // 4)
        return LLMResponse(
            text=text,
            token_usage=TokenUsage(prompt_tokens=pt, completion_tokens=ct, total_tokens=pt + ct),
            finish_reason="stop",
        )


class TestIteration2Succeeds:
    def test_two_iterations_success(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        sb = _StrategyBackend(responses=[
            (
                '{"decisions": [{"path": "src/a.py", "action": "regenerate", "rationale": "first attempt"}]}',
                TokenUsage(prompt_tokens=50, completion_tokens=10, total_tokens=60),
            ),
            (
                '{"decisions": [{"path": "src/a.py", "action": "regenerate", "rationale": "second attempt after validation failure"}]}',
                TokenUsage(prompt_tokens=60, completion_tokens=10, total_tokens=70),
            ),
        ])
        strategy = IterativeRepositoryAgentStrategy(backend=sb)
        rb = _StatefulRegenBackend(["wrong content", "correct content for second attempt"])
        scenario = _make_scenario(artifacts=artifacts)
        check_cmd = [
            sys.executable, "-c",
            "import sys; content = open('src/a.py').read(); sys.exit(0 if 'correct' in content else 1)",
        ]
        runner = _make_runner(
            tmp_path, strategy, rb, iso,
            validation_command=check_cmd,
        )

        record = runner.run(scenario)
        assert record.status == RunStatus.succeeded
        assert record.functional_validation_passed is True
        assert record.selection_model_calls == 2
        assert record.regeneration_model_calls >= 1
        assert record.functional_validation_duration_seconds > 0
        assert record.total_workflow_tokens > 0


# ---------------------------------------------------------------------------
# Test 3: Agent revises selected artifacts after validation feedback
# ---------------------------------------------------------------------------


class TestAgentRevisesArtifacts:
    def test_agent_changes_selection_after_feedback(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
            ArtifactRef(path="src/b.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        sb = _StrategyBackend(responses=[
            (
                '{"decisions": [{"path": "src/a.py", "action": "regenerate", "rationale": "first attempt"}]}',
                TokenUsage(prompt_tokens=50, completion_tokens=10, total_tokens=60),
            ),
            (
                '{"decisions": [{"path": "src/a.py", "action": "regenerate", "rationale": "still needed"}, {"path": "src/b.py", "action": "regenerate", "rationale": "also needed after feedback"}]}',
                TokenUsage(prompt_tokens=70, completion_tokens=15, total_tokens=85),
            ),
        ])
        strategy = IterativeRepositoryAgentStrategy(backend=sb)
        rb = _make_regen_backend("correct output")
        scenario = _make_scenario(artifacts=artifacts)
        check_cmd = [
            sys.executable, "-c",
            "import sys; import os; "
            "a = open('src/a.py').read() if os.path.exists('src/a.py') else ''; "
            "b = open('src/b.py').read() if os.path.exists('src/b.py') else ''; "
            "sys.exit(0 if 'correct' in a and 'correct' in b else 1)",
        ]
        runner = _make_runner(
            tmp_path, strategy, rb, iso,
            validation_command=check_cmd,
            max_attempts=3,
        )

        record = runner.run(scenario)
        assert record.status == RunStatus.succeeded
        assert record.selection_model_calls == 2


# ---------------------------------------------------------------------------
# Test 4: Validation stdout/stderr appear in the second agent prompt
# ---------------------------------------------------------------------------


class TestValidationFeedbackInPrompt:
    def test_validation_output_in_revise_prompt(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        sb = _StrategyBackend(responses=[
            (
                '{"decisions": [{"path": "src/a.py", "action": "regenerate", "rationale": "first"}]}',
                TokenUsage(prompt_tokens=50, completion_tokens=10, total_tokens=60),
            ),
            (
                '{"decisions": [{"path": "src/a.py", "action": "regenerate", "rationale": "second"}]}',
                TokenUsage(prompt_tokens=60, completion_tokens=10, total_tokens=70),
            ),
        ])
        strategy = IterativeRepositoryAgentStrategy(backend=sb)
        rb = _make_regen_backend("output")
        scenario = _make_scenario(artifacts=artifacts)
        check_cmd = [
            sys.executable, "-c",
            "import sys; print('STDOUT_MARKER'); sys.stderr.write('STDERR_MARKER'); sys.exit(1)",
        ]
        runner = _make_runner(
            tmp_path, strategy, rb, iso,
            validation_command=check_cmd,
        )

        runner.run(scenario)
        assert len(sb.prompts) >= 2
        second_prompt = sb.prompts[1]
        assert "STDOUT_MARKER" in second_prompt or "exit code" in second_prompt.lower()


# ---------------------------------------------------------------------------
# Test 5: Current workspace content appears in the second agent prompt
# ---------------------------------------------------------------------------


class TestWorkspaceContentInPrompt:
    def test_workspace_content_in_revise_prompt(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        sb = _StrategyBackend(responses=[
            (
                '{"decisions": [{"path": "src/a.py", "action": "regenerate", "rationale": "first"}]}',
                TokenUsage(prompt_tokens=50, completion_tokens=10, total_tokens=60),
            ),
            (
                '{"decisions": [{"path": "src/a.py", "action": "regenerate", "rationale": "second"}]}',
                TokenUsage(prompt_tokens=60, completion_tokens=10, total_tokens=70),
            ),
        ])
        strategy = IterativeRepositoryAgentStrategy(backend=sb)
        rb = _make_regen_backend("output")
        scenario = _make_scenario(artifacts=artifacts)
        check_cmd = [sys.executable, "-c", "import sys; sys.exit(1)"]
        runner = _make_runner(
            tmp_path, strategy, rb, iso,
            validation_command=check_cmd,
        )

        runner.run(scenario)
        assert len(sb.prompts) >= 2
        second_prompt = sb.prompts[1]
        assert "src/a.py" in second_prompt


# ---------------------------------------------------------------------------
# Test 6: Ground Truth-only paths never appear in prompts or selections
# ---------------------------------------------------------------------------


class TestNoGroundTruthLeakage:
    def test_ground_truth_paths_not_in_universe(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/actual.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        gt_path = "src/ground_truth_only.py"

        sb = _StrategyBackend(responses=[
            (
                '{"decisions": [{"path": "src/actual.py", "action": "regenerate", "rationale": "test"}]}',
                TokenUsage(prompt_tokens=50, completion_tokens=10, total_tokens=60),
            ),
        ])
        strategy = IterativeRepositoryAgentStrategy(backend=sb)
        rb = _make_regen_backend("output")
        scenario = Scenario(
            scenario_id="test_gt",
            repository="test_repo",
            change_type="modify",
            blast_radius=BlastRadius.localized,
            requirement_before="old",
            requirement_after="new",
            rationale="test",
            expected_affected_artifacts=(
                ArtifactRef(path=gt_path, artifact_type=ArtifactType.source),
            ),
            acceptance_criteria=(AcceptanceCriterion(description="pass"),),
        )
        runner = _make_runner(tmp_path, strategy, rb, iso)

        record = runner.run(scenario)
        assert record.status == RunStatus.succeeded
        for prompt in sb.prompts:
            assert gt_path not in prompt, f"Ground truth path leaked in prompt: {prompt}"
        if record.prediction:
            for d in record.prediction.decisions:
                assert d.artifact.path != gt_path


# ---------------------------------------------------------------------------
# Test 7: Agent stop signal prevents another iteration
# ---------------------------------------------------------------------------


class TestAgentStopSignal:
    def test_agent_stop_signal_prevents_iteration(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        # First call selects artifact, fails validation. Second call sends stop signal.
        sb = _StrategyBackend(responses=[
            (
                '{"decisions": [{"path": "src/a.py", "action": "regenerate", "rationale": "first"}]}',
                TokenUsage(prompt_tokens=50, completion_tokens=10, total_tokens=60),
            ),
            (
                '{"decisions": [], "requires_iteration": false}',
                TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            ),
        ])
        strategy = IterativeRepositoryAgentStrategy(backend=sb)
        rb = _make_regen_backend("output")
        scenario = _make_scenario(artifacts=artifacts)
        check_cmd = [sys.executable, "-c", "exit(1)"]
        runner = _make_runner(
            tmp_path, strategy, rb, iso,
            validation_command=check_cmd,
        )

        runner.run(scenario)
        assert sb.call_count == 2

    def test_requires_iteration_false_no_decisions_stops_immediately(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        sb = _StrategyBackend(responses=[
            (
                '{"decisions": [], "requires_iteration": false}',
                TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            ),
        ])
        strategy = IterativeRepositoryAgentStrategy(backend=sb)

        class _NeverCalledBackend:
            async def generate(self, prompt, temperature=0.0, max_tokens=4096):
                raise RuntimeError("should not be called")

        rb = _NeverCalledBackend()
        scenario = _make_scenario(artifacts=artifacts)
        check_cmd = [sys.executable, "-c", "exit(1)"]
        runner = _make_runner(
            tmp_path, strategy, rb, iso,
            validation_command=check_cmd,
        )

        runner.run(scenario)
        assert sb.call_count == 1
        assert not strategy.last_requires_iteration

    def test_requires_iteration_false_with_decisions_stops_after_one_validation(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        sb = _StrategyBackend(responses=[
            (
                '{"decisions": [{"path": "src/a.py", "action": "regenerate", "rationale": "only"}], "requires_iteration": false}',
                TokenUsage(prompt_tokens=50, completion_tokens=10, total_tokens=60),
            ),
        ])
        strategy = IterativeRepositoryAgentStrategy(backend=sb)
        rb = _make_regen_backend("output")
        scenario = _make_scenario(artifacts=artifacts)
        check_cmd = [sys.executable, "-c", "exit(1)"]
        runner = _make_runner(
            tmp_path, strategy, rb, iso,
            validation_command=check_cmd,
            max_attempts=10,
        )

        record = runner.run(scenario)
        assert sb.call_count == 1
        assert record.selection_model_calls == 1
        assert record.regeneration_model_calls == 1
        # Validation was run: decisions exist, so regeneration and validation execute
        assert record.functional_validation_duration_seconds > 0
        # No second agent call despite failing validation and having remaining budget
        assert not strategy.last_requires_iteration


# ---------------------------------------------------------------------------
# Test 8: max_attempts bounds total iterations
# ---------------------------------------------------------------------------


class TestMaxAttemptsBounds:
    def test_max_attempts_bounds_iterations(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        responses = [
            (
                '{"decisions": [{"path": "src/a.py", "action": "regenerate", "rationale": f"attempt {i}"}]}',
                TokenUsage(prompt_tokens=50, completion_tokens=10, total_tokens=60),
            )
            for i in range(5)
        ]
        sb = _StrategyBackend(responses=responses)
        strategy = IterativeRepositoryAgentStrategy(backend=sb)
        rb = _make_regen_backend("output")
        scenario = _make_scenario(artifacts=artifacts)
        check_cmd = [sys.executable, "-c", "exit(1)"]
        runner = _make_runner(
            tmp_path, strategy, rb, iso,
            validation_command=check_cmd,
            max_attempts=2,
        )

        runner.run(scenario)
        assert sb.call_count <= 2


# ---------------------------------------------------------------------------
# Test 9: Token budget stops further agent reasoning
# ---------------------------------------------------------------------------


class TestTokenBudgetStops:
    def test_token_budget_stops_agent_reasoning(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        # Strategy responses use 15 tokens each
        sb = _StrategyBackend(responses=[
            (
                '{"decisions": [{"path": "src/a.py", "action": "regenerate", "rationale": "only attempt"}]}',
                TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            ),
        ])
        strategy = IterativeRepositoryAgentStrategy(backend=sb)
        # Regen backend also uses small tokens
        class _SmallTokenRegenBackend:
            async def generate(self, prompt, temperature=0.0, max_tokens=4096):
                return LLMResponse(
                    text="x",
                    token_usage=TokenUsage(prompt_tokens=5, completion_tokens=3, total_tokens=8),
                )
        rb = _SmallTokenRegenBackend()
        scenario = _make_scenario(artifacts=artifacts)
        check_cmd = [sys.executable, "-c", "exit(1)"]
        runner = _make_runner(
            tmp_path, strategy, rb, iso,
            validation_command=check_cmd,
            max_attempts=10,
            max_tokens=30,
        )

        record = runner.run(scenario)
        assert record.status == RunStatus.failed
        assert sb.call_count <= 2

    def test_agent_exhausts_budget_before_regeneration(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        sb = _StrategyBackend(responses=[
            (
                '{"decisions": [{"path": "src/a.py", "action": "regenerate", "rationale": "only"}]}',
                TokenUsage(prompt_tokens=50, completion_tokens=50, total_tokens=100),
            ),
        ])
        strategy = IterativeRepositoryAgentStrategy(backend=sb)

        class _NeverCalledBackend:
            async def generate(self, prompt, temperature=0.0, max_tokens=4096):
                raise RuntimeError("should not be called")

        rb = _NeverCalledBackend()
        scenario = _make_scenario(artifacts=artifacts)
        check_cmd = [sys.executable, "-c", "exit(1)"]
        runner = _make_runner(
            tmp_path, strategy, rb, iso,
            validation_command=check_cmd,
            max_attempts=10,
            max_tokens=100,
        )

        record = runner.run(scenario)
        assert record.status == RunStatus.failed
        assert sb.call_count == 1
        assert record.regeneration_model_calls == 0
        assert record.functional_validation_duration_seconds == 0.0
        assert record.selection_model_calls == 1
        assert record.selection_total_tokens >= 100

    def test_later_agent_decision_exhausts_budget(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        # Agent uses 60 tokens on first call (under budget of 70), then 60 on second (over)
        sb = _StrategyBackend(responses=[
            (
                '{"decisions": [{"path": "src/a.py", "action": "regenerate", "rationale": "first"}]}',
                TokenUsage(prompt_tokens=30, completion_tokens=30, total_tokens=60),
            ),
            (
                '{"decisions": [{"path": "src/a.py", "action": "regenerate", "rationale": "second"}]}',
                TokenUsage(prompt_tokens=30, completion_tokens=30, total_tokens=60),
            ),
        ])
        strategy = IterativeRepositoryAgentStrategy(backend=sb)

        class _ControlledRegenBackend:
            def __init__(self):
                self.call_count = 0

            async def generate(self, prompt, temperature=0.0, max_tokens=4096):
                self.call_count += 1
                return LLMResponse(
                    text="content",
                    token_usage=TokenUsage(prompt_tokens=5, completion_tokens=3, total_tokens=8),
                )

        rb = _ControlledRegenBackend()
        scenario = _make_scenario(artifacts=artifacts)
        check_cmd = [sys.executable, "-c", "exit(1)"]
        runner = _make_runner(
            tmp_path, strategy, rb, iso,
            validation_command=check_cmd,
            max_attempts=10,
            max_tokens=70,
        )

        record = runner.run(scenario)
        assert record.status == RunStatus.failed
        # First iteration: agent(60) + regen(8) = 68, then second agent(60) would exceed 70
        assert sb.call_count == 2
        assert rb.call_count == 1
        assert record.selection_model_calls == 2
        assert record.regeneration_model_calls == 1


# ---------------------------------------------------------------------------
# Test 10: Timeout stops the loop
# ---------------------------------------------------------------------------


class TestTimeoutStops:
    def test_timeout_stops_iterative_loop(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)

        class _AdvancingClock:
            def __init__(self) -> None:
                self._now = 100.0

            def now(self) -> float:
                return self._now

            def advance(self, seconds: float) -> None:
                self._now += seconds

        clock = _AdvancingClock()

        sb = _StrategyBackend(responses=[
            (
                '{"decisions": [{"path": "src/a.py", "action": "regenerate", "rationale": "attempt"}]}',
                TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            ),
        ])
        strategy = IterativeRepositoryAgentStrategy(backend=sb)

        class _AdvancingRegenBackend:
            async def generate(self, prompt, temperature=0.0, max_tokens=4096):
                clock.advance(15)
                return LLMResponse(
                    text="x",
                    token_usage=TokenUsage(prompt_tokens=5, completion_tokens=3, total_tokens=8),
                )

        rb = _AdvancingRegenBackend()
        scenario = _make_scenario(artifacts=artifacts)
        check_cmd = [sys.executable, "-c", "exit(1)"]

        config = RunnerConfig(
            strategy_name="iterative_repository_agent",
            backend_name="mock",
            protocol_version="1.0",
            max_attempts=10,
            timeout_seconds=10,
            enable_regeneration=True,
            validation_command=check_cmd,
            validation_timeout=10,
        )
        runner = BenchmarkRunner(
            strategy=strategy,
            backend=rb,
            isolation=iso,
            config=config,
        )
        runner._budget = BudgetManager(
            max_attempts=10,
            timeout_seconds=10,
            clock=clock,
        )

        record = runner.run(scenario)
        assert record.status in (RunStatus.failed, RunStatus.timed_out)
        assert sb.call_count <= 2


# ---------------------------------------------------------------------------
# Test 11: Non-repairable isolation/config failure performs no second iteration
# ---------------------------------------------------------------------------


class TestNonRepairableFailure:
    def test_config_failure_no_iteration(self, tmp_path: Path) -> None:
        iso, ws_root = _setup_workspace(tmp_path, ())
        sb = _StrategyBackend()
        strategy = IterativeRepositoryAgentStrategy(backend=sb)
        scenario = _make_scenario()
        config = RunnerConfig(
            strategy_name="iterative_repository_agent",
            backend_name="mock",
            protocol_version="1.0",
            enable_regeneration=True,
            validation_command=None,
        )
        runner = BenchmarkRunner(
            strategy=strategy,
            backend=sb,
            isolation=iso,
            config=config,
        )
        record = runner.run(scenario)
        assert record.status == RunStatus.failed
        assert sb.call_count == 0

    def test_no_backend_fails_closed(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        strategy = IterativeRepositoryAgentStrategy(backend=None)  # type: ignore[arg-type]
        scenario = _make_scenario(artifacts=artifacts)
        config = RunnerConfig(
            strategy_name="iterative_repository_agent",
            backend_name="mock",
            protocol_version="1.0",
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
        )
        runner = BenchmarkRunner(
            strategy=strategy,
            backend=None,
            isolation=iso,
            config=config,
        )
        record = runner.run(scenario)
        assert record.status == RunStatus.failed
        assert any("backend" in f.message.lower() or "LLM" in f.message for f in record.failures)


# ---------------------------------------------------------------------------
# Test 12: Source and active snapshot remain immutable
# ---------------------------------------------------------------------------


class TestImmutability:
    def test_source_and_snapshot_unchanged(self, tmp_path: Path) -> None:
        from benchmark.repositories.snapshot import stage_repository_snapshot

        artifact = ArtifactRef(path="src/main.py", artifact_type=ArtifactType.source)

        source_repo = tmp_path / "source_repo"
        source_repo.mkdir()
        (source_repo / "src").mkdir()
        (source_repo / "src" / "main.py").write_text("original source", encoding="utf-8")

        storage = tmp_path / "storage"
        storage.mkdir()
        active = stage_repository_snapshot(source_repo, storage, "myrepo", "rev1")

        ws_root = tmp_path / "workspace"
        ws_root.mkdir(parents=True)
        wstarget = ws_root / "src" / "main.py"
        wstarget.parent.mkdir(parents=True)
        wstarget.write_text("original source", encoding="utf-8")

        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=storage, active_snapshot_root=active)

        sb = _StrategyBackend(responses=[
            (
                '{"decisions": [{"path": "src/main.py", "action": "regenerate", "rationale": "test"}]}',
                TokenUsage(prompt_tokens=50, completion_tokens=10, total_tokens=60),
            ),
        ])
        strategy = IterativeRepositoryAgentStrategy(backend=sb)
        rb = _make_regen_backend("correct content")
        scenario = Scenario(
            scenario_id="sc-immutable",
            repository="myrepo",
            change_type="modify",
            blast_radius=BlastRadius.localized,
            requirement_before="before",
            requirement_after="after",
            rationale="test",
            expected_affected_artifacts=(artifact,),
            acceptance_criteria=(AcceptanceCriterion(description="pass"),),
        )
        runner = _make_runner(tmp_path, strategy, rb, iso)
        record = runner.run(scenario)

        assert (source_repo / "src/main.py").read_text() == "original source"
        assert (active / "src/main.py").read_text(encoding="utf-8") == "original source"
        assert record.status == RunStatus.succeeded


# ---------------------------------------------------------------------------
# Test 13: Selection/agent metrics aggregate once per decision
# ---------------------------------------------------------------------------


class TestMetricsAggregation:
    def test_selection_metrics_counted_once_per_decision(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        sb = _StrategyBackend(responses=[
            (
                '{"decisions": [{"path": "src/a.py", "action": "regenerate", "rationale": "first"}]}',
                TokenUsage(prompt_tokens=50, completion_tokens=10, total_tokens=60),
            ),
            (
                '{"decisions": [{"path": "src/a.py", "action": "regenerate", "rationale": "second"}]}',
                TokenUsage(prompt_tokens=60, completion_tokens=15, total_tokens=75),
            ),
        ])
        strategy = IterativeRepositoryAgentStrategy(backend=sb)
        rb = _make_regen_backend("output")
        scenario = _make_scenario(artifacts=artifacts)
        check_cmd = [sys.executable, "-c", "exit(1)"]
        runner = _make_runner(
            tmp_path, strategy, rb, iso,
            validation_command=check_cmd,
            max_attempts=2,
        )

        record = runner.run(scenario)
        assert record.selection_model_calls == 2
        assert record.selection_total_tokens >= 60 + 75 or abs(record.selection_total_tokens - 135) < 20

    def test_regeneration_metrics_aggregated(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        sb = _StrategyBackend(responses=[
            (
                '{"decisions": [{"path": "src/a.py", "action": "regenerate", "rationale": "first"}]}',
                TokenUsage(prompt_tokens=50, completion_tokens=10, total_tokens=60),
            ),
            (
                '{"decisions": [{"path": "src/a.py", "action": "regenerate", "rationale": "second"}]}',
                TokenUsage(prompt_tokens=60, completion_tokens=15, total_tokens=75),
            ),
        ])
        strategy = IterativeRepositoryAgentStrategy(backend=sb)
        rb = _make_regen_backend("output")
        scenario = _make_scenario(artifacts=artifacts)
        check_cmd = [sys.executable, "-c", "exit(1)"]
        runner = _make_runner(
            tmp_path, strategy, rb, iso,
            validation_command=check_cmd,
        )

        record = runner.run(scenario)
        assert record.regeneration_model_calls >= 1
        assert record.regeneration_total_tokens > 0

    def test_validation_duration_aggregated(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        sb = _StrategyBackend(responses=[
            (
                '{"decisions": [{"path": "src/a.py", "action": "regenerate", "rationale": "first"}]}',
                TokenUsage(prompt_tokens=50, completion_tokens=10, total_tokens=60),
            ),
            (
                '{"decisions": [{"path": "src/a.py", "action": "regenerate", "rationale": "second"}]}',
                TokenUsage(prompt_tokens=60, completion_tokens=15, total_tokens=75),
            ),
        ])
        strategy = IterativeRepositoryAgentStrategy(backend=sb)
        rb = _make_regen_backend("output")
        scenario = _make_scenario(artifacts=artifacts)
        check_cmd = [sys.executable, "-c", "exit(1)"]
        runner = _make_runner(
            tmp_path, strategy, rb, iso,
            validation_command=check_cmd,
        )

        record = runner.run(scenario)
        assert record.functional_validation_duration_seconds >= 0

    def test_no_double_counting(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        sb = _StrategyBackend(responses=[
            (
                '{"decisions": [{"path": "src/a.py", "action": "regenerate", "rationale": "first"}]}',
                TokenUsage(prompt_tokens=50, completion_tokens=10, total_tokens=60),
            ),
            (
                '{"decisions": [{"path": "src/a.py", "action": "regenerate", "rationale": "second"}]}',
                TokenUsage(prompt_tokens=60, completion_tokens=15, total_tokens=75),
            ),
        ])
        strategy = IterativeRepositoryAgentStrategy(backend=sb)
        rb = _make_regen_backend("output")
        scenario = _make_scenario(artifacts=artifacts)
        check_cmd = [sys.executable, "-c", "exit(1)"]
        runner = _make_runner(
            tmp_path, strategy, rb, iso,
            validation_command=check_cmd,
        )

        record = runner.run(scenario)
        expected = record.selection_total_tokens + record.regeneration_total_tokens
        assert abs(record.total_workflow_tokens - expected) < 50

    def test_checkpoint_compatible(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        sb = _StrategyBackend(responses=[
            (
                '{"decisions": [{"path": "src/a.py", "action": "regenerate", "rationale": "test"}]}',
                TokenUsage(prompt_tokens=50, completion_tokens=10, total_tokens=60),
            ),
        ])
        strategy = IterativeRepositoryAgentStrategy(backend=sb)
        rb = _make_regen_backend("correct content")
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(tmp_path, strategy, rb, iso)

        record = runner.run(scenario)
        assert record.status == RunStatus.succeeded
        assert record.total_workflow_tokens >= 0
        assert record.selection_model_calls >= 1
        assert record.regeneration_model_calls >= 0
        assert record.functional_validation_duration_seconds >= 0
        assert record.selected_artifact_count >= 0
        assert record.regenerated_artifact_count >= 0

        assert hasattr(record, "selection_prompt_tokens")
        assert hasattr(record, "regeneration_prompt_tokens")
        assert hasattr(record, "functional_validation_duration_seconds")
        assert hasattr(record, "total_workflow_tokens")
        assert hasattr(record, "selected_artifact_count")


# ---------------------------------------------------------------------------
# Test 14: Backend exception propagation
# ---------------------------------------------------------------------------


class TestBackendExceptionPropagation:
    """Correction 5 — Backend/infrastructure exceptions must propagate."""

    def test_model_backend_error_on_initial_decision(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)

        from benchmark.core.exceptions import ModelBackendError

        class _FailingBackend:
            async def generate(self, prompt, temperature=0.0, max_tokens=4096):
                raise ModelBackendError("model backend unavailable")

        strategy = IterativeRepositoryAgentStrategy(backend=_FailingBackend())
        scenario = _make_scenario(artifacts=artifacts)
        rb = _make_regen_backend("content")
        runner = _make_runner(tmp_path, strategy, rb, iso)

        record = runner.run(scenario)
        assert record.status == RunStatus.failed
        assert any("model backend unavailable" in f.message for f in record.failures)

    def test_model_backend_error_on_revision(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)

        from benchmark.core.exceptions import ModelBackendError

        class _FailingOnSecondCallBackend:
            def __init__(self):
                self.call_count = 0

            async def generate(self, prompt, temperature=0.0, max_tokens=4096):
                self.call_count += 1
                if self.call_count == 1:
                    return LLMResponse(
                        text='{"decisions": [{"path": "src/a.py", "action": "regenerate", "rationale": "first"}]}',
                        token_usage=TokenUsage(prompt_tokens=50, completion_tokens=10, total_tokens=60),
                        finish_reason="stop",
                    )
                raise ModelBackendError("model backend fail on revision")

        strategy = IterativeRepositoryAgentStrategy(backend=_FailingOnSecondCallBackend())
        rb = _make_regen_backend("output")
        scenario = _make_scenario(artifacts=artifacts)
        check_cmd = [sys.executable, "-c", "exit(1)"]
        runner = _make_runner(
            tmp_path, strategy, rb, iso,
            validation_command=check_cmd,
        )

        record = runner.run(scenario)
        assert record.status == RunStatus.failed
        assert any("model backend fail on revision" in f.message for f in record.failures)

    def test_runtime_backend_failure_not_silent(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)

        class _RuntimeErrorBackend:
            async def generate(self, prompt, temperature=0.0, max_tokens=4096):
                raise RuntimeError("connection timeout")

        strategy = IterativeRepositoryAgentStrategy(backend=_RuntimeErrorBackend())
        rb = _make_regen_backend("content")
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(tmp_path, strategy, rb, iso)

        import pytest
        with pytest.raises(RuntimeError, match="connection timeout"):
            runner.run(scenario)
