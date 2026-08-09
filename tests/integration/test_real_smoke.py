"""End-to-end regression test for the real-mode smoke path.

Reproduces the Kaggle real-smoke execution pipeline: non-dry-run with
a fake backend that simulates KaggleQwenBackend failure behaviour.
Verifies that all 7 arms succeed and produce correctly-named records.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from benchmark.core.exceptions import ModelBackendError
from benchmark.core.models import DependencyGraph, LLMResponse, Scenario, TokenUsage
from benchmark.execution.isolation import IsolationContext
from benchmark.execution.pipeline import BenchmarkPipeline, PipelineConfig
from benchmark.repositories.workspace import WorkspacePath

STRATEGY_NAMES = [
    "monolithic",
    "agent",
    "selective",
    "compiled_ai",
    "delta_mcp",
    "incr_rtl",
    "code_plan",
]


class _FakeKaggleBackend:
    """Simulates KaggleQwenBackend failure behaviour (ModelBackendError on generate)."""

    def __init__(self, fail_on_generate: bool = True) -> None:
        self._fail_on_generate = fail_on_generate
        self.generate_call_count = 0

    async def generate(
        self,
        prompt: str = "",
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        self.generate_call_count += 1
        if self._fail_on_generate:
            raise ModelBackendError(
                "Simulated model-load failure: torch/transformers not available"
            )
        return LLMResponse(text="mock", token_usage=TokenUsage())


def _build_test_graph(scenario: Scenario) -> DependencyGraph:
    """Build a minimal graph from a scenario's expected affected artifacts."""
    paths = [a.path for a in scenario.expected_affected_artifacts]
    return DependencyGraph(nodes=tuple(paths), edges=(), metadata={"source": "test"})


def _make_strategy(name: str, backend=None, graph=None, artifact_descriptors=None):
    from benchmark.strategies import (
        FullContextStrategy,
        HybridSelectiveStrategy,
        MonolithicRegenerationStrategy,
        RepositoryAgentStrategy,
        SemanticOnlyStrategy,
        StaticOnlyStrategy,
        TraceabilityOnlyStrategy,
    )
    if name == "agent":
        if backend is None:
            raise ValueError("RepositoryAgentStrategy requires a backend")
        return RepositoryAgentStrategy(backend=backend)
    strategies = {
        "monolithic": (MonolithicRegenerationStrategy, {}),
        "selective": (HybridSelectiveStrategy, {"graph": graph, "artifact_descriptors": artifact_descriptors}),
        "compiled_ai": (StaticOnlyStrategy, {"graph": graph}),
        "delta_mcp": (SemanticOnlyStrategy, {}),
        "incr_rtl": (TraceabilityOnlyStrategy, {}),
        "code_plan": (FullContextStrategy, {"graph": graph}),
    }
    entry = strategies.get(name)
    if entry is None:
        raise ValueError(f"Unknown strategy: {name}")
    cls, kwargs = entry
    return cls(**{k: v for k, v in kwargs.items() if v is not None})


class _ScenarioProvider:
    def __init__(self, scenarios_dir: Path) -> None:
        from benchmark.scenarios.loader import ScenarioLoader
        self._loader = ScenarioLoader(scenarios_dir)
        self._all: list[Scenario] | None = None

    def _ensure_loaded(self) -> None:
        if self._all is None:
            scenarios = self._loader.load_all()
            self._all = scenarios

    def get_scenario(self, scenario_id: str) -> Scenario:
        self._ensure_loaded()
        assert self._all is not None
        for s in self._all:
            if s.scenario_id == scenario_id:
                return s
        raise KeyError(f"Scenario not found: {scenario_id}")

    def list_scenarios(self, repo_id: str | None = None) -> list[Scenario]:
        self._ensure_loaded()
        assert self._all is not None
        if repo_id:
            return [s for s in self._all if s.repository == repo_id]
        return list(self._all)


# Strategy that fails in this test environment:
#   agent → ModelBackendError (fake backend fails on generate)
# Graph-dependent strategies (compiled_ai, selective, code_plan) are now
# supplied with a minimal test graph.
STRATEGIES_WITH_MISSING_PREREQS: set[str] = {"agent", "selective"}


class TestRealSmokeEndToEnd:
    """Verifies the full real-mode smoke pipeline for all 7 arms."""

    @pytest.mark.parametrize("strategy_name", STRATEGY_NAMES)
    def test_each_arm_pipeline_completes_with_correct_identity(
        self, strategy_name: str, tmp_path: Path
    ) -> None:
        scenarios_dir = Path(__file__).resolve().parent.parent.parent / "benchmark_data" / "scenarios"
        scenario_provider = _ScenarioProvider(scenarios_dir)
        all_scenarios = scenario_provider.list_scenarios()
        assert len(all_scenarios) >= 1, "Need at least 1 scenario"

        has_missing_prereqs = strategy_name in STRATEGIES_WITH_MISSING_PREREQS
        backend = _FakeKaggleBackend(fail_on_generate=strategy_name == "agent")

        # Build a minimal graph from the first scenario's artifact universe
        test_scenario = all_scenarios[0]
        dep_graph = _build_test_graph(test_scenario)

        # Build artifact descriptors from the repository profile for selective
        descs: tuple[object, ...] = ()
        if strategy_name == "selective":
            from benchmark.repositories.loader import RepositoryLoader
            data_dir = Path(__file__).resolve().parent.parent.parent / "benchmark_data"
            loader = RepositoryLoader(data_dir)
            collection = loader.load_manifest()
            profile_obj = collection.get_profile(test_scenario.repository)
            from benchmark.selection.dependency_scope import descriptors_from_profile
            if profile_obj is not None:
                descs = descriptors_from_profile(
                    profile_obj.artifact_catalog,
                    tuple(profile_obj.artifact_universe.get("llm_editable", [])),
                )

        strategy = _make_strategy(strategy_name, backend=backend, graph=dep_graph, artifact_descriptors=descs)

        arm_ws = tmp_path / strategy_name
        arm_ws.mkdir(parents=True, exist_ok=True)
        (arm_ws / "snapshots").mkdir(exist_ok=True)
        (arm_ws / "runs").mkdir(exist_ok=True)
        (arm_ws / "tmp").mkdir(exist_ok=True)
        ws = WorkspacePath(root=str(arm_ws))
        isolation = IsolationContext(workspace=ws)

        config = PipelineConfig(
            protocol_version="1.0",
            timeout_seconds=0,
            max_attempts_per_run=3,
            dry_run=False,
        )
        pipeline = BenchmarkPipeline(
            strategy=strategy,
            backend=backend,
            scenario_provider=scenario_provider,
            isolation=isolation,
            config=config,
            strategy_name=strategy_name,
        )

        selected = all_scenarios[:1]
        scenario_ids = [s.scenario_id for s in selected]

        result = pipeline.run_all(scenario_ids=scenario_ids)

        if has_missing_prereqs:
            assert result.success_count == 0
            assert result.failure_count == len(scenario_ids)
        else:
            assert result.failure_count == 0, (
                f"Arm '{strategy_name}' reports {result.failure_count} failure(s)"
            )
            assert result.timeout_count == 0
            assert result.success_count == len(scenario_ids)

        for record in result.records:
            assert record.identity.strategy_name == strategy_name, (
                f"Expected strategy_name='{strategy_name}', "
                f"got '{record.identity.strategy_name}'"
            )
            assert record.identity.scenario_id in scenario_ids
            assert record.duration_seconds >= 0.0

    def test_all_arms_use_correct_dir_structure(self, tmp_path: Path) -> None:
        for _, name in enumerate(STRATEGY_NAMES):
            arm_dir = tmp_path / name
            arm_dir.mkdir(parents=True, exist_ok=True)
            (arm_dir / "snapshots").mkdir(exist_ok=True)
            (arm_dir / "runs").mkdir(exist_ok=True)
            (arm_dir / "tmp").mkdir(exist_ok=True)
            ws = WorkspacePath(root=str(arm_dir))
            iso = IsolationContext(workspace=ws)
            report = iso.verify()
            assert report.passed, f"Arm '{name}' isolation check failed: {report.message}"

    def test_isolation_check_still_rejects_same_path(self, tmp_path: Path) -> None:
        ws = WorkspacePath(root=str(tmp_path))
        iso = IsolationContext(workspace=ws, snapshot_base=tmp_path)
        report = iso.verify()
        assert not report.passed
        assert "same as workspace" in report.message
