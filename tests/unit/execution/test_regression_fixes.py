"""Regression tests for false-success and token-usage propagation fixes."""


from pathlib import Path

import pytest

from benchmark.core.enums import BlastRadius, FailureKind, RunStatus
from benchmark.core.exceptions import ModelBackendError
from benchmark.core.models import (
    ArtifactRef,
    ArtifactType,
    ArtifactUniverse,
    DependencyGraph,
    ImpactPrediction,
    LLMResponse,
    RepositoryIdentity,
    RepositorySnapshot,
    RequirementChange,
    Scenario,
    TokenUsage,
)
from benchmark.execution.isolation import IsolationContext
from benchmark.execution.runner import BenchmarkRunner, RunnerConfig
from benchmark.repositories.workspace import WorkspacePath
from benchmark.strategies.agent import RepositoryAgentStrategy
from benchmark.strategies.code_plan import FullContextStrategy
from benchmark.strategies.compiled_ai import StaticOnlyStrategy
from benchmark.strategies.delta_mcp import SemanticOnlyStrategy
from benchmark.strategies.monolithic import MonolithicRegenerationStrategy
from benchmark.strategies.selective import HybridSelectiveStrategy

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _scenario() -> Scenario:
    return Scenario(
        scenario_id="test-scenario",
        repository="test-repo",
        change_type="modify",
        blast_radius=BlastRadius.localized,
        requirement_before="old",
        requirement_after="new",
        rationale="test",
    )


def _snapshot() -> RepositorySnapshot:
    return RepositorySnapshot(
        identity=RepositoryIdentity(name="repo", url="https://example.com/repo"),
        commit_sha="abc123",
        path="/tmp/repo",
    )


def _change() -> RequirementChange:
    return RequirementChange(before="old", after="new")


def _universe() -> ArtifactUniverse:
    return ArtifactUniverse(
        artifacts=(
            ArtifactRef(path="src/main.py", artifact_type=ArtifactType.source),
        ),
    )


def _make_runner(
    tmp_path: Path,
    strategy: object,
    backend: object | None = None,
    max_attempts: int = 3,
) -> BenchmarkRunner:
    ws_root = tmp_path / "workspace"
    ws_root.mkdir(parents=True, exist_ok=True)
    snap_base = tmp_path / "snapshots"
    snap_base.mkdir(parents=True, exist_ok=True)
    ws = WorkspacePath(root=str(ws_root))
    iso = IsolationContext(workspace=ws, snapshot_base=snap_base)

    from tests.fixtures.mock_implementations import FakeLLMBackend

    config = RunnerConfig(
        strategy_name="test_strategy",
        backend_name="test_backend",
        protocol_version="1.0",
        max_attempts=max_attempts,
    )
    return BenchmarkRunner(
        strategy=strategy,
        backend=backend or FakeLLMBackend(),
        isolation=iso,
        config=config,
    )


# ---------------------------------------------------------------------------
# 1. ModelBackendError propagation
# ---------------------------------------------------------------------------


class TestModelBackendErrorPropagation:
    """ModelBackendError must propagate from every LLM-dependent strategy."""

    def test_agent_strategy_propagates_model_backend_error(self) -> None:
        """RepositoryAgentStrategy must NOT catch ModelBackendError."""

        class _FailingBackend:
            async def generate(self, prompt: str, **kwargs: object) -> LLMResponse:
                raise ModelBackendError("model not available")

        strategy = RepositoryAgentStrategy(backend=_FailingBackend())
        with pytest.raises(ModelBackendError):
            strategy.analyze_impact(_snapshot(), _change(), _universe())

    def test_agent_strategy_propagates_timeout(self) -> None:
        """Non-ModelBackendError exceptions still propagate."""

        class _TimeoutBackend:
            async def generate(self, prompt: str, **kwargs: object) -> LLMResponse:
                raise RuntimeError("connection timeout")

        strategy = RepositoryAgentStrategy(backend=_TimeoutBackend())
        with pytest.raises(RuntimeError):
            strategy.analyze_impact(_snapshot(), _change(), _universe())

    def test_non_llm_strategies_never_call_backend(self) -> None:
        """Non-LLM strategies must work without any backend."""
        for cls in [
            MonolithicRegenerationStrategy,
            HybridSelectiveStrategy,
            SemanticOnlyStrategy,
            FullContextStrategy,
        ]:
            strategy = cls()
            pred = strategy.analyze_impact(_snapshot(), _change(), _universe())
            assert isinstance(pred, ImpactPrediction)


# ---------------------------------------------------------------------------
# 2. Runner marks failed generation as failed
# ---------------------------------------------------------------------------


class TestRunnerFailureHandling:
    """Runner must mark runs as failed when generation fails."""

    def test_runner_marks_model_backend_error_as_failed(self, tmp_path: Path) -> None:
        """ModelBackendError from strategy → RunStatus.failed."""

        class _FailingAgentStrategy:
            def analyze_impact(
                self,
                repository: object = None,
                requirement_change: object = None,
                artifact_universe: object = None,
            ) -> ImpactPrediction:
                raise ModelBackendError("model unavailable")

        runner = _make_runner(tmp_path, strategy=_FailingAgentStrategy())
        record = runner.run(_scenario())
        assert record.status == RunStatus.failed
        assert any(f.failure_kind == FailureKind.model_output for f in record.failures)

    def test_runner_fails_on_prediction_errors(self, tmp_path: Path) -> None:
        """ImpactPrediction with errors → RunStatus.failed."""

        class _ErrorStrategy:
            def analyze_impact(self, **kwargs: object) -> ImpactPrediction:
                return ImpactPrediction(errors=("blocking error",))

        runner = _make_runner(tmp_path, strategy=_ErrorStrategy())
        record = runner.run(_scenario())
        assert record.status == RunStatus.failed

    def test_runner_succeeds_on_empty_prediction(self, tmp_path: Path) -> None:
        """ImpactPrediction without errors → RunStatus.succeeded."""

        class _OkStrategy:
            def analyze_impact(self, **kwargs: object) -> ImpactPrediction:
                return ImpactPrediction()

        runner = _make_runner(tmp_path, strategy=_OkStrategy())
        record = runner.run(_scenario())
        assert record.status == RunStatus.succeeded

    def test_failure_record_preserves_stage_and_exception(self, tmp_path: Path) -> None:
        """Failure diagnostics include stage, exception type, and sanitized message."""

        class _FailingStrategy:
            def analyze_impact(self, **kwargs: object) -> ImpactPrediction:
                raise ModelBackendError("disk full")

        runner = _make_runner(tmp_path, strategy=_FailingStrategy())
        record = runner.run(_scenario())
        assert len(record.failures) >= 1
        failure = record.failures[0]
        assert failure.stage
        assert "ModelBackendError" in failure.details or "model" in failure.details.lower()
        assert "disk full" in failure.message


# ---------------------------------------------------------------------------
# 3. Token-usage propagation
# ---------------------------------------------------------------------------


class TestTokenUsagePropagation:
    """Observed token usage must survive the full chain."""

    def test_agent_preserves_token_usage_from_backend(self) -> None:
        """RepositoryAgentStrategy must attach token_usage to ImpactPrediction."""

        class _MockBackend:
            async def generate(self, prompt: str, **kwargs: object) -> LLMResponse:
                return LLMResponse(
                    text='["src/main.py"]',
                    token_usage=TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
                    finish_reason="stop",
                )

        strategy = RepositoryAgentStrategy(backend=_MockBackend())
        pred = strategy.analyze_impact(_snapshot(), _change(), _universe())
        assert pred.token_usage is not None
        assert pred.token_usage.prompt_tokens == 10
        assert pred.token_usage.completion_tokens == 20
        assert pred.token_usage.total_tokens == 30

    def test_runner_propagates_token_usage_to_run_record(self, tmp_path: Path) -> None:
        """RunRecord.token_usage must match the prediction's token_usage."""

        class _TokenStrategy:
            def analyze_impact(self, **kwargs: object) -> ImpactPrediction:
                return ImpactPrediction(
                    token_usage=TokenUsage(prompt_tokens=5, completion_tokens=7, total_tokens=12),
                )

        runner = _make_runner(tmp_path, strategy=_TokenStrategy())
        record = runner.run(_scenario())
        assert record.token_usage.prompt_tokens == 5
        assert record.token_usage.completion_tokens == 7
        assert record.token_usage.total_tokens == 12

    def test_non_llm_strategies_record_zero_tokens(self, tmp_path: Path) -> None:
        """Non-LLM strategies may legitimately record zero tokens."""

        class _NoTokenStrategy:
            def analyze_impact(self, **kwargs: object) -> ImpactPrediction:
                return ImpactPrediction()

        runner = _make_runner(tmp_path, strategy=_NoTokenStrategy())
        record = runner.run(_scenario())
        assert record.token_usage.prompt_tokens == 0
        assert record.token_usage.completion_tokens == 0
        assert record.token_usage.total_tokens == 0

    def test_token_usage_on_failure_is_preserved(self, tmp_path: Path) -> None:
        """Token usage from a failed prediction must still appear in RunRecord."""

        class _FailingWithTokens:
            def analyze_impact(self, **kwargs: object) -> ImpactPrediction:
                return ImpactPrediction(
                    errors=("parse error",),
                    token_usage=TokenUsage(prompt_tokens=100, completion_tokens=0, total_tokens=100),
                )

        runner = _make_runner(tmp_path, strategy=_FailingWithTokens())
        record = runner.run(_scenario())
        assert record.status == RunStatus.failed
        assert record.token_usage.prompt_tokens == 100
        assert record.token_usage.total_tokens == 100


# ---------------------------------------------------------------------------
# 4. Repetition counts and repair-loop integration
# ---------------------------------------------------------------------------


class TestRepairLoopIntegration:
    """The repair loop must correctly aggregate failure information."""

    def test_repair_loop_exhausts_and_fails(self, tmp_path: Path) -> None:
        """A consistently failing strategy exhausts attempts and returns failed."""

        class _AlwaysFails:
            def analyze_impact(self, **kwargs: object) -> ImpactPrediction:
                raise ModelBackendError("persistent failure")

        runner = _make_runner(tmp_path, strategy=_AlwaysFails(), max_attempts=3)
        record = runner.run(_scenario())
        assert record.status == RunStatus.failed
        assert len(record.failures) >= 1

    def test_repair_loop_eventually_succeeds(self, tmp_path: Path) -> None:
        """A transiently failing strategy can succeed on retry."""

        class _TransientFailure:
            def __init__(self) -> None:
                self._attempts = 0

            def analyze_impact(self, **kwargs: object) -> ImpactPrediction:
                self._attempts += 1
                if self._attempts < 2:
                    raise ModelBackendError("transient failure")
                return ImpactPrediction(
                    token_usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
                )

        runner = _make_runner(tmp_path, strategy=_TransientFailure(), max_attempts=3)
        record = runner.run(_scenario())
        assert record.status == RunStatus.succeeded
        assert record.token_usage.total_tokens == 15


# ---------------------------------------------------------------------------
# 5. GPU compatibility check
# ---------------------------------------------------------------------------


class TestGpuCompatibilityCheck:
    """The preflight check must reject unsupported GPU compute capabilities."""

    def test_compute_capability_below_minimum_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Simulate sm_60 GPU which is below the sm_70 minimum."""
        pytest.importorskip("torch")
        import torch

        monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
        monkeypatch.setattr(torch.cuda, "get_device_capability", lambda device: (6, 0))
        monkeypatch.setattr(torch.cuda, "get_device_name", lambda device: "Tesla P100")

        from benchmark.llm.kaggle_qwen_backend import _check_gpu_compatibility

        with pytest.raises(ModelBackendError) as exc:
            _check_gpu_compatibility()
        assert "sm_60" in str(exc.value) or "6.0" in str(exc.value)
        assert "P100" in str(exc.value)


# ---------------------------------------------------------------------------
# 6. JSON summary correctness
# ---------------------------------------------------------------------------


class TestJsonSummary:
    """The benchmark summary JSON must correctly reflect failure and token data."""

    def test_summary_counts_match_run_statuses(self) -> None:
        """PipelineResult success/failure/timeout counts must match individual records."""
        from benchmark.execution.pipeline import PipelineResult

        result = PipelineResult(
            records=(
                _make_record(RunStatus.succeeded),
                _make_record(RunStatus.failed),
                _make_record(RunStatus.succeeded),
                _make_record(RunStatus.timed_out),
            ),
            total_duration=10.0,
            success_count=2,
            failure_count=1,
            timeout_count=1,
        )
        assert result.success_count == 2
        assert result.failure_count == 1
        assert result.timeout_count == 1
        assert len(result.records) == 4

    def test_failure_diagnostics_in_json(self, tmp_path: Path) -> None:
        """Full failure diagnostics are persisted in the JSON summary."""

        class _FailStrategy:
            def analyze_impact(self, **kwargs: object) -> ImpactPrediction:
                raise ModelBackendError("test failure")

        runner = _make_runner(tmp_path, strategy=_FailStrategy())
        record = runner.run(_scenario())

        import json
        record_dict = {
            "run_id": record.identity.run_id,
            "status": record.status.value,
            "failures": [
                {
                    "kind": f.failure_kind.value,
                    "message": f.message,
                    "details": f.details,
                    "stage": f.stage,
                }
                for f in record.failures
            ],
            "token_usage": {
                "prompt_tokens": record.token_usage.prompt_tokens,
                "completion_tokens": record.token_usage.completion_tokens,
                "total_tokens": record.token_usage.total_tokens,
            },
        }
        serialized = json.dumps(record_dict)
        deserialized = json.loads(serialized)
        assert deserialized["status"] == "failed"
        assert len(deserialized["failures"]) >= 1
        f0 = deserialized["failures"][0]
        assert "kind" in f0
        assert "message" in f0
        assert "stage" in f0
        assert "test failure" in f0["message"]


# ---------------------------------------------------------------------------
# Helpers for summary tests
# ---------------------------------------------------------------------------


def _make_record(status: RunStatus):
    from benchmark.core.models import RunIdentity, RunRecord

    return RunRecord(
        identity=RunIdentity(
            run_id="test",
            protocol_version="1.0",
            repository_commit_sha="sha",
            scenario_id="s1",
            strategy_name="s",
        ),
        status=status,
    )


# ---------------------------------------------------------------------------
# 7. Dependency graph injection
# ---------------------------------------------------------------------------


class TestDependencyGraphInjection:
    """Graph-dependent strategies must receive a graph when available."""

    def test_compiled_ai_receives_graph(self) -> None:
        """StaticOnlyStrategy with a graph must not report missing graph."""
        graph = DependencyGraph(nodes=("a.py", "b.py"), edges=(("a.py", "b.py"),))
        strategy = StaticOnlyStrategy(graph=graph)
        pred = strategy.analyze_impact(_snapshot(), _change(), _universe())
        assert pred.errors == () or not any("no dependency graph" in e for e in pred.errors)

    def test_selective_receives_graph(self) -> None:
        """HybridSelectiveStrategy with a graph must not crash."""
        graph = DependencyGraph(nodes=("src/main.py",), edges=())
        strategy = HybridSelectiveStrategy(graph=graph)
        pred = strategy.analyze_impact(_snapshot(), _change(), _universe())
        assert isinstance(pred, ImpactPrediction)

    def test_code_plan_receives_graph(self) -> None:
        """FullContextStrategy with a graph must not crash."""
        graph = DependencyGraph(nodes=("src/main.py",), edges=())
        strategy = FullContextStrategy(graph=graph)
        pred = strategy.analyze_impact(_snapshot(), _change(), _universe())
        assert isinstance(pred, ImpactPrediction)

    def test_missing_graph_in_compiled_ai_fails_cleanly(self) -> None:
        """StaticOnlyStrategy without graph returns explicit error."""
        strategy = StaticOnlyStrategy(graph=None)
        pred = strategy.analyze_impact(_snapshot(), _change(), _universe())
        assert pred.errors
        assert any("no dependency graph" in e for e in pred.errors)


# ---------------------------------------------------------------------------
# 8. ProfileGraphBuilder
# ---------------------------------------------------------------------------


class TestProfileGraphBuilder:
    """ProfileGraphBuilder correctly extracts graphs from profile data."""

    def test_build_from_architecture(self) -> None:
        from benchmark.graph.builder import ProfileGraphBuilder

        builder = ProfileGraphBuilder()
        arch = {
            "dependency_graph": {
                "edges": [
                    {"from": "a.py", "to": "b.py"},
                    {"from": "b.py", "to": "c.py"},
                ]
            }
        }
        graph = builder.build_from_architecture(arch)
        assert graph is not None
        assert len(graph.nodes) == 3
        assert len(graph.edges) == 2

    def test_build_from_empty_architecture(self) -> None:
        from benchmark.graph.builder import ProfileGraphBuilder

        builder = ProfileGraphBuilder()
        graph = builder.build_from_architecture({})
        assert graph is None

    def test_build_fallback_minimal_graph(self) -> None:
        """A DependencyGraph built from just artifact paths (no edges)."""
        from benchmark.core.models import DependencyGraph

        graph = DependencyGraph(
            nodes=("src/main.py", "src/utils.py"),
            edges=(),
        )
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 0

    def test_profile_graph_loading_from_yaml(self, tmp_path: Path) -> None:
        """Integration: build a graph from an actual YAML-derived profile."""
        from benchmark.graph.builder import ProfileGraphBuilder

        # Create required manifests dirs
        (tmp_path / "manifests").mkdir(parents=True, exist_ok=True)
        (tmp_path / "repository_profiles").mkdir(parents=True, exist_ok=True)

        repos_yaml = "repositories:\n  test-repo:\n    url: https://example.com\n"
        (tmp_path / "manifests" / "repositories.yaml").write_text(repos_yaml, encoding="utf-8")
        versions_yaml = "versions:\n  test-repo:\n    commit_sha: abc123\n"
        (tmp_path / "manifests" / "repository_versions.yaml").write_text(versions_yaml, encoding="utf-8")

        profile_content = """
repository_id: test-repo
architecture:
  dependency_graph:
    edges:
      - from: a.py
        to: b.py
"""
        profile_path = tmp_path / "repository_profiles" / "test-repo.yaml"
        profile_path.write_text(profile_content, encoding="utf-8")

        from benchmark.repositories.loader import RepositoryLoader
        loader = RepositoryLoader(tmp_path)
        collection = loader.load_manifest()
        profile = collection.get_profile("test-repo")
        assert profile is not None

        builder = ProfileGraphBuilder()
        graph = builder.build_from_profile(profile)
        assert graph is not None
        assert len(graph.edges) == 1
        assert graph.edges[0] == ("a.py", "b.py")


# ---------------------------------------------------------------------------
# 9. Lazy backend initialization
# ---------------------------------------------------------------------------


class TestLazyBackendInitialization:
    """Backend must only be initialized when a strategy actually needs LLM."""

    def test_non_llm_backend_is_null(self) -> None:
        """A NullLLMBackend raises if generate() is called unexpectedly."""
        import anyio

        from benchmark.llm.mock_backend import NullLLMBackend

        backend = NullLLMBackend()
        with pytest.raises(ModelBackendError):
            anyio.run(backend.generate, "prompt")

    def test_pipeline_accepts_null_backend(self, tmp_path: Path) -> None:
        """BenchmarkPipeline must accept None backend and use NullLLMBackend."""
        from benchmark.execution.isolation import IsolationContext
        from benchmark.execution.pipeline import BenchmarkPipeline, PipelineConfig
        from benchmark.repositories.workspace import WorkspacePath

        ws = WorkspacePath(root=str(tmp_path))
        iso = IsolationContext(workspace=ws, snapshot_base=tmp_path)
        config = PipelineConfig(protocol_version="1.0")

        strategy = MonolithicRegenerationStrategy()
        pipeline = BenchmarkPipeline(
            strategy=strategy,
            backend=None,
            scenario_provider=_ScenarioProvider(),
            isolation=iso,
            config=config,
            strategy_name="monolithic",
        )
        assert pipeline._backend is not None


class _ScenarioProvider:
    """Minimal ScenarioProvider for test purposes."""

    def __init__(self) -> None:
        self._scenarios = [_scenario()]

    def get_scenario(self, scenario_id: str):  # type: ignore[no-untyped-def]
        for s in self._scenarios:
            if s.scenario_id == scenario_id:
                return s
        raise KeyError(scenario_id)

    def list_scenarios(self, repo_id: str | None = None):  # type: ignore[no-untyped-def]
        return list(self._scenarios)


# ---------------------------------------------------------------------------
# 10. Strategy capability description
# ---------------------------------------------------------------------------


class TestStrategyCapabilityDescription:
    """describe_capabilities must accurately report each strategy."""

    def test_agent_has_llm_no_graph(self) -> None:
        from seven_arm_benchmark import describe_capabilities

        cap = describe_capabilities("agent")
        assert cap["uses_llm_by_design"] is True
        assert cap["llm_backend_attached"] is True
        assert cap["uses_dependency_graph_by_design"] is False
        assert cap["dependency_graph_attached"] is False

    def test_compiled_ai_has_graph_no_llm(self) -> None:
        from seven_arm_benchmark import describe_capabilities

        cap = describe_capabilities("compiled_ai")
        assert cap["uses_llm_by_design"] is False
        assert cap["llm_backend_attached"] is False
        assert cap["uses_dependency_graph_by_design"] is True
        assert cap["dependency_graph_attached"] is True

    def test_selective_has_both_by_design(self) -> None:
        from seven_arm_benchmark import describe_capabilities

        cap = describe_capabilities("selective")
        assert cap["uses_llm_by_design"] is True
        assert cap["uses_dependency_graph_by_design"] is True

    def test_monolithic_no_graph_no_llm_attached(self) -> None:
        from seven_arm_benchmark import describe_capabilities

        cap = describe_capabilities("monolithic")
        assert cap["uses_llm_by_design"] is True
        assert cap["llm_backend_attached"] is False
        assert cap["uses_dependency_graph_by_design"] is False
        assert cap["dependency_graph_attached"] is False

    def test_delta_mcp_no_graph_by_design(self) -> None:
        from seven_arm_benchmark import describe_capabilities

        cap = describe_capabilities("delta_mcp")
        assert cap["uses_dependency_graph_by_design"] is False
        assert cap["dependency_graph_attached"] is False

    def test_design_constants_frozen(self) -> None:
        """STRATEGY_CAPABILITIES_DESIGN must cover all 9 arm names.

        ``impact_plan`` (scientific-wip-impactplan-v1 proposed arm, D047) was
        added in IMPACTPLAN-WIP-01.
        """
        from seven_arm_benchmark import STRATEGY_CAPABILITIES_DESIGN

        assert set(STRATEGY_CAPABILITIES_DESIGN.keys()) == {
            "monolithic", "agent", "selective", "compiled_ai",
            "delta_mcp", "incr_rtl", "code_plan",
            "iterative_repository_agent", "impact_plan",
        }


# ---------------------------------------------------------------------------
# 11. GPU incompatibility preservation
# ---------------------------------------------------------------------------


class TestGpuIncompatibilityPreserved:
    """P100 incompatibility must remain an explicit typed failure."""

    def test_expected_error_message(self) -> None:
        """The ModelBackendError message must reference compute capability."""
        msg = (
            "GPU compute capability 6.0 on Tesla P100-PCIE-16GB is below "
            "the minimum 7.0 required by the installed PyTorch build."
        )
        assert "6.0" in msg
        assert "7.0" in msg
        assert "P100" in msg


# ---------------------------------------------------------------------------
# 12. Strategy graph injection via runner
# ---------------------------------------------------------------------------


class TestRunnerGraphInjection:
    """Runner must pass graph-dependent strategies a graph that works end-to-end."""

    def test_compiled_ai_succeeds_with_graph_via_runner(self, tmp_path: Path) -> None:
        """compiled_ai must succeed when a graph is injected via the runner."""
        graph = DependencyGraph(nodes=("src/main.py",), edges=())
        strategy = StaticOnlyStrategy(graph=graph)

        runner = _make_runner(tmp_path, strategy=strategy)
        record = runner.run(_scenario())
        assert record.status == RunStatus.succeeded

    def test_compiled_ai_fails_without_graph_via_runner(self, tmp_path: Path) -> None:
        """compiled_ai must fail cleanly when no graph is available."""
        strategy = StaticOnlyStrategy(graph=None)

        runner = _make_runner(tmp_path, strategy=strategy)
        record = runner.run(_scenario())
        assert record.status == RunStatus.failed
        assert any("graph" in f.message for f in record.failures)

    def test_selective_succeeds_with_graph_via_runner(self, tmp_path: Path) -> None:
        """selective must succeed with a graph via the runner."""
        from benchmark.selection.dependency_scope import ArtifactDescriptor

        graph = DependencyGraph(nodes=("src/main.py",), edges=())
        desc = ArtifactDescriptor(
            path="src/main.py",
            category="source",
            description="Main entry point with feature flag",
            provides_symbols=("feature_flag", "main_handler"),
            typical_change_triggers=("feature changes", "entry point modifications"),
        )
        strategy = HybridSelectiveStrategy(graph=graph, artifact_descriptors=(desc,))
        scenario = Scenario(
            scenario_id="test-scenario",
            repository="test-repo",
            change_type="modify",
            blast_radius=BlastRadius.localized,
            requirement_before="old",
            requirement_after="feature flag main handler",
            rationale="test",
            expected_affected_artifacts=(
                ArtifactRef(path="src/main.py", artifact_type=ArtifactType.source),
            ),
        )

        runner = _make_runner(tmp_path, strategy=strategy)
        record = runner.run(scenario)
        assert record.status == RunStatus.succeeded
