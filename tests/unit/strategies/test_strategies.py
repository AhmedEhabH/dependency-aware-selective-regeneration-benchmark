from benchmark.core.enums import ActionKind, ArtifactType
from benchmark.core.models import (
    ArtifactRef,
    ArtifactUniverse,
    DependencyGraph,
    RepositoryIdentity,
    RepositorySnapshot,
    RequirementChange,
)
from benchmark.strategies.code_plan import FullContextStrategy
from benchmark.strategies.compiled_ai import StaticOnlyStrategy
from benchmark.strategies.delta_mcp import SemanticOnlyStrategy
from benchmark.strategies.incr_rtl import TraceabilityOnlyStrategy
from benchmark.strategies.monolithic import MonolithicRegenerationStrategy
from benchmark.strategies.registry import StrategyRegistry
from benchmark.strategies.selective import HybridSelectiveStrategy


def _make_snapshot() -> RepositorySnapshot:
    return RepositorySnapshot(
        identity=RepositoryIdentity(name="test-repo", url="https://example.com/test"),
        commit_sha="abc123",
        path="/tmp/test",
    )


def _make_change() -> RequirementChange:
    return RequirementChange(before="old behavior", after="new behavior")


def _make_universe() -> ArtifactUniverse:
    return ArtifactUniverse(
        artifacts=(
            ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source),
            ArtifactRef(path="src/views.py", artifact_type=ArtifactType.source),
            ArtifactRef(path="tests/test_models.py", artifact_type=ArtifactType.test),
        )
    )


class TestMonolithicStrategy:
    def test_regenerates_all_artifacts(self) -> None:
        strategy = MonolithicRegenerationStrategy()
        pred = strategy.analyze_impact(_make_snapshot(), _make_change(), _make_universe())
        assert len(pred.decisions) == 3
        assert all(d.action == ActionKind.regenerate for d in pred.decisions)

    def test_empty_universe(self) -> None:
        strategy = MonolithicRegenerationStrategy()
        pred = strategy.analyze_impact(_make_snapshot(), _make_change(), ArtifactUniverse())
        assert len(pred.decisions) == 0
        assert pred.errors == ()

    def test_protocol_conformance(self) -> None:
        from benchmark.core.protocols import ImpactStrategy
        strategy = MonolithicRegenerationStrategy()
        assert isinstance(strategy, ImpactStrategy)


class TestStaticOnlyStrategy:
    def test_returns_error_without_graph(self) -> None:
        strategy = StaticOnlyStrategy()
        pred = strategy.analyze_impact(_make_snapshot(), _make_change(), _make_universe())
        assert len(pred.errors) == 1
        assert "no dependency graph" in pred.errors[0]

    def test_regenerates_all_when_fully_connected(self) -> None:
        from benchmark.core.models import DependencyGraph
        graph = DependencyGraph(
            nodes=("src/models.py", "src/views.py", "tests/test_models.py"),
            edges=(("src/models.py", "src/views.py"), ("src/views.py", "tests/test_models.py")),
        )
        strategy = StaticOnlyStrategy(graph=graph)
        pred = strategy.analyze_impact(_make_snapshot(), _make_change(), _make_universe())
        assert len(pred.decisions) == 3
        regenerate_count = sum(1 for d in pred.decisions if d.action == ActionKind.regenerate)
        assert regenerate_count == 3


class TestSemanticOnlyStrategy:
    def test_selective_based_on_path_similarity(self) -> None:
        strategy = SemanticOnlyStrategy(threshold=0.01)
        pred = strategy.analyze_impact(_make_snapshot(), _make_change(), _make_universe())
        assert len(pred.decisions) == 3

    def test_high_threshold_preserves_all(self) -> None:
        strategy = SemanticOnlyStrategy(threshold=0.99)
        pred = strategy.analyze_impact(_make_snapshot(), _make_change(), _make_universe())
        assert all(d.action == ActionKind.preserve for d in pred.decisions)


class TestTraceabilityOnlyStrategy:
    def test_covers_mapped_artifacts(self) -> None:
        coverage = {"test_models": ["src/models.py"]}
        strategy = TraceabilityOnlyStrategy(coverage_map=coverage)
        pred = strategy.analyze_impact(_make_snapshot(), _make_change(), _make_universe())
        models_decision = next(d for d in pred.decisions if d.artifact.path == "src/models.py")
        assert models_decision.action == ActionKind.regenerate

    def test_preserves_uncovered_artifacts(self) -> None:
        strategy = TraceabilityOnlyStrategy(coverage_map={})
        pred = strategy.analyze_impact(_make_snapshot(), _make_change(), _make_universe())
        assert all(d.action == ActionKind.preserve for d in pred.decisions)


class TestHybridSelectiveStrategy:
    def test_symbol_match_regenerates(self) -> None:
        from benchmark.selection.dependency_scope import ArtifactDescriptor
        desc = ArtifactDescriptor(
            path="src/models.py",
            category="model",
            description="User and product models",
            provides_symbols=("User", "Product", "model_flag"),
            typical_change_triggers=("schema changes", "field modifications"),
        )
        strategy = HybridSelectiveStrategy(
            graph=DependencyGraph(nodes=("src/models.py",), edges=()),
            artifact_descriptors=(desc,),
        )
        change = RequirementChange(before="old", after="new behavior with Product model")
        pred = strategy.analyze_impact(_make_snapshot(), change, _make_universe())
        assert len(pred.decisions) == 3
        model_decision = [d for d in pred.decisions if d.artifact.path == "src/models.py"][0]
        assert model_decision.action == ActionKind.regenerate

    def test_no_descriptor_match_preserves_all(self) -> None:
        strategy = HybridSelectiveStrategy(
            graph=DependencyGraph(nodes=("src/models.py",), edges=()),
            artifact_descriptors=(),
        )
        pred = strategy.analyze_impact(_make_snapshot(), _make_change(), _make_universe())
        assert len(pred.decisions) == 3
        assert all(d.action == ActionKind.preserve for d in pred.decisions)
        assert pred.errors

    def test_no_seed_returns_error(self) -> None:
        strategy = HybridSelectiveStrategy(
            graph=DependencyGraph(nodes=(), edges=()),
            artifact_descriptors=(),
        )
        pred = strategy.analyze_impact(_make_snapshot(), _make_change(), _make_universe())
        assert pred.errors
        assert all(d.action == ActionKind.preserve for d in pred.decisions)


class TestFullContextStrategy:
    def test_returns_predictions(self) -> None:
        strategy = FullContextStrategy()
        pred = strategy.analyze_impact(_make_snapshot(), _make_change(), _make_universe())
        assert len(pred.decisions) == 3

    def test_with_graph_and_coverage(self) -> None:
        from benchmark.core.models import DependencyGraph
        graph = DependencyGraph(
            nodes=("src/models.py",),
            edges=(("src/models.py", "src/views.py"),),
        )
        coverage = {"t1": ["src/models.py"]}
        strategy = FullContextStrategy(graph=graph, coverage_map=coverage, semantic_threshold=0.01)
        pred = strategy.analyze_impact(_make_snapshot(), _make_change(), _make_universe())
        assert len(pred.decisions) == 3


class TestStrategyRegistry:
    def test_register_and_create(self) -> None:
        registry = StrategyRegistry()
        registry.register("monolithic", MonolithicRegenerationStrategy)
        strategy = registry.create("monolithic")
        assert isinstance(strategy, MonolithicRegenerationStrategy)

    def test_duplicate_registration_raises(self) -> None:
        from benchmark.core.exceptions import DuplicateRegistrationError
        registry = StrategyRegistry()
        registry.register("m", MonolithicRegenerationStrategy)
        try:
            registry.register("m", MonolithicRegenerationStrategy)
            raise AssertionError("Should have raised")
        except DuplicateRegistrationError:
            pass

    def test_unknown_lookup_raises(self) -> None:
        from benchmark.core.exceptions import UnknownRegistrationError
        registry = StrategyRegistry()
        try:
            registry.create("nonexistent")
            raise AssertionError("Should have raised")
        except UnknownRegistrationError:
            pass

    def test_freeze_prevents_registration(self) -> None:
        from benchmark.core.exceptions import BenchmarkError
        registry = StrategyRegistry()
        registry.register("m", MonolithicRegenerationStrategy)
        registry.freeze()
        try:
            registry.register("m2", MonolithicRegenerationStrategy)
            raise AssertionError("Should have raised")
        except BenchmarkError:
            pass

    def test_list_names(self) -> None:
        registry = StrategyRegistry()
        registry.register("b", MonolithicRegenerationStrategy)
        registry.register("a", MonolithicRegenerationStrategy)
        assert registry.list_names() == ["a", "b"]

    def test_contains_and_len(self) -> None:
        registry = StrategyRegistry()
        assert len(registry) == 0
        registry.register("m", MonolithicRegenerationStrategy)
        assert len(registry) == 1
        assert registry.contains("m")
        assert not registry.contains("x")

    def test_get_returns_class(self) -> None:
        registry = StrategyRegistry()
        registry.register("m", MonolithicRegenerationStrategy)
        cls = registry.get("m")
        assert cls is MonolithicRegenerationStrategy

    def test_is_frozen_property(self) -> None:
        registry = StrategyRegistry()
        assert not registry.is_frozen
        registry.freeze()
        assert registry.is_frozen


class TestIterativeAgentDeadline:
    def test_agent_selection_deadline_stops_after_first_call(self, tmp_path) -> None:
        import asyncio

        from benchmark.core.models import LLMResponse, TokenUsage
        from benchmark.strategies.iterative_agent import IterativeRepositoryAgentStrategy

        call_count = 0
        guard_state: list[int] = [0]

        class _ExpiryBackend:
            async def generate(self, prompt, temperature=0.0, max_tokens=4096):
                nonlocal call_count
                call_count += 1
                return LLMResponse(
                    text=(
                        '{"action": "final", "selected_paths": ["src/models.py"],'
                        ' "requires_iteration": false}'
                    ),
                    token_usage=TokenUsage(prompt_tokens=40, completion_tokens=10, total_tokens=50),
                    finish_reason="stop",
                )

            def count_prompt_tokens(self, prompt) -> int:
                return 40

        def guard() -> bool:
            guard_state[0] += 1
            return guard_state[0] <= 1

        strategy = IterativeRepositoryAgentStrategy(_ExpiryBackend())
        strategy.begin_run(tmp_path)
        strategy.set_model_call_guard(guard)
        try:
            existing_loop = asyncio.get_event_loop()
        except RuntimeError:
            existing_loop = None
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            pred = strategy.analyze_impact(_make_snapshot(), _make_change(), _make_universe())
        finally:
            loop.close()
            if existing_loop is not None:
                asyncio.set_event_loop(existing_loop)
            else:
                asyncio.set_event_loop(None)

        assert call_count == 1
        assert strategy.model_call_budget_exhausted is True
        assert strategy.model_call_count == 1
        assert strategy.total_tokens == 50
        assert pred.token_usage.total_tokens == 50
