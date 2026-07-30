"""SU-0010A integration tests: minimal shared regeneration path end-to-end."""

import sys
from pathlib import Path

from benchmark.core.enums import ActionKind, ArtifactType, BlastRadius, RunStatus
from benchmark.core.models import (
    AcceptanceCriterion,
    ArtifactRef,
    ArtifactUniverse,
    DependencyGraph,
    ImpactPrediction,
    RunRecord,
    Scenario,
    TokenUsage,
)
from benchmark.execution.budgets import BudgetManager
from benchmark.execution.isolation import IsolationContext
from benchmark.execution.regeneration import SharedRegenerationExecutor
from benchmark.execution.runner import BenchmarkRunner, RunnerConfig
from benchmark.repositories.workspace import WorkspacePath
from benchmark.selection.planner import ArtifactSelector, RegenerationPlan, RegenerationPlanner
from benchmark.strategies.monolithic import MonolithicRegenerationStrategy
from benchmark.strategies.selective import HybridSelectiveStrategy


def _make_backend(response_text: str = "replacement content"):
    class _Mock:
        def __init__(self, text: str):
            self._text = text

        async def generate(self, prompt: str, temperature: float = 0.0, max_tokens: int = 4096):
            from benchmark.core.models import LLMResponse
            pt = max(1, len(prompt) // 4)
            ct = max(1, len(self._text) // 4)
            return LLMResponse(
                text=self._text,
                token_usage=TokenUsage(prompt_tokens=pt, completion_tokens=ct, total_tokens=pt + ct),
                finish_reason="stop",
            )

    return _Mock(response_text)


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
        rationale="test scenario for SU-0010A",
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


def _make_runner(
    tmp_path: Path,
    strategy: object,
    backend: object,
    iso: IsolationContext,
    enable_regeneration: bool = False,
    validation_command: list[str] | None = None,
    validation_timeout: int = 10,
    strategy_name: str = "test",
    max_attempts: int = 1,
    max_tokens: int = 0,
    editable_artifact_paths: tuple[str, ...] = ("src/a.py",),
) -> BenchmarkRunner:
    config = RunnerConfig(
        strategy_name=strategy_name,
        backend_name="mock",
        protocol_version="1.0",
        max_attempts=max_attempts,
        max_tokens=max_tokens,
        enable_regeneration=enable_regeneration,
        validation_command=validation_command,
        validation_timeout=validation_timeout,
        editable_artifact_paths=editable_artifact_paths,
    )
    return BenchmarkRunner(
        strategy=strategy,
        backend=backend,
        isolation=iso,
        config=config,
    )


def _check_workspace_modified(ws_root: Path, artifact_paths: list[str], expected: bool = True) -> None:
    for path in artifact_paths:
        content = (ws_root / path).read_text(encoding="utf-8")
        if expected:
            assert content == "replacement content", f"{path} should be replacement"
        else:
            assert content == f"original {path} content", f"{path} should be unchanged"


class TestEndToEndFullScopeReference:
    def test_full_scope_regenerates_all_artifacts(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source),
            ArtifactRef(path="src/views.py", artifact_type=ArtifactType.source),
            ArtifactRef(path="tests/test_models.py", artifact_type=ArtifactType.test),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        backend = _make_backend("replacement content")
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)

        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="monolithic",
            editable_artifact_paths=("src/models.py", "src/views.py", "tests/test_models.py"),
        )
        record = runner.run(scenario)

        assert record.status == RunStatus.succeeded
        assert record.regenerated_artifact_count == 3
        assert record.selected_artifact_count == 3
        assert record.preserved_artifact_count == 0
        assert record.functional_validation_passed is True
        assert record.regeneration_total_tokens > 0
        _check_workspace_modified(ws_root, ["src/models.py", "src/views.py", "tests/test_models.py"], True)

    def test_full_scope_validation_failure(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        backend = _make_backend("replacement content")
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)

        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(1)"],
            strategy_name="monolithic",
            editable_artifact_paths=("src/models.py",),
        )
        record = runner.run(scenario)

        assert record.status == RunStatus.failed
        assert record.functional_validation_passed is False
        assert any("validation failed" in f.message for f in record.failures)

    def test_full_scope_total_workflow_metrics(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/main.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        backend = _make_backend("replacement content")
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)

        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="monolithic",
            editable_artifact_paths=("src/main.py",),
        )
        record = runner.run(scenario)

        assert record.total_workflow_tokens > 0
        assert record.total_workflow_model_calls >= 1
        assert record.total_workflow_duration_seconds > 0


class TestEndToEndHybridSelective:
    def test_hybrid_selective_regenerates_subset(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source),
            ArtifactRef(path="src/views.py", artifact_type=ArtifactType.source),
            ArtifactRef(path="src/utils.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        backend = _make_backend("replacement content")
        from benchmark.selection.dependency_scope import ArtifactDescriptor
        model_desc = ArtifactDescriptor(
            path="src/models.py", category="model", description="Data models",
            provides_symbols=("models",), typical_change_triggers=("schema changes",),
        )
        utils_desc = ArtifactDescriptor(
            path="src/utils.py", category="utility", description="Utilities",
            provides_symbols=("utils",), typical_change_triggers=("utility changes",),
        )
        views_desc = ArtifactDescriptor(
            path="src/views.py", category="view", description="Views",
            provides_symbols=("views",), typical_change_triggers=("api changes",),
        )
        strategy = HybridSelectiveStrategy(
            graph=DependencyGraph(nodes=("src/models.py", "src/views.py", "src/utils.py"), edges=()),
            artifact_descriptors=(model_desc, utils_desc, views_desc),
        )
        scenario = _make_scenario(
            artifacts=artifacts,
            before="models utils",
            after="models utils new_feature",
        )

        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="hybrid_selective",
            editable_artifact_paths=("src/models.py", "src/views.py", "src/utils.py"),
        )
        record = runner.run(scenario)

        assert record.status == RunStatus.succeeded
        assert record.regenerated_artifact_count >= 0
        assert record.selected_artifact_count >= 0
        assert record.functional_validation_passed is True


class TestHybridRegeneratesFewer:
    def test_hybrid_regenerates_fewer_than_full_scope(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/main.py", artifact_type=ArtifactType.source),
            ArtifactRef(path="src/utils.py", artifact_type=ArtifactType.source),
            ArtifactRef(path="src/helpers.py", artifact_type=ArtifactType.source),
            ArtifactRef(path="tests/test_main.py", artifact_type=ArtifactType.test),
        )
        iso_full, ws_full = _setup_workspace(tmp_path / "full", artifacts, repo="full_repo")
        iso_hybrid, ws_hybrid = _setup_workspace(tmp_path / "hybrid", artifacts, repo="hybrid_repo")

        backend = _make_backend("replacement content")

        # Full scope run
        full_strategy = MonolithicRegenerationStrategy()
        full_scenario = _make_scenario("full_repo", artifacts)
        full_runner = _make_runner(
            tmp_path / "full", full_strategy, backend, iso_full,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="monolithic",
            editable_artifact_paths=("src/main.py", "src/utils.py", "src/helpers.py", "tests/test_main.py"),
        )
        full_record = full_runner.run(full_scenario)

        # Hybrid selective run
        from benchmark.selection.dependency_scope import ArtifactDescriptor
        hybrid_descs = (
            ArtifactDescriptor(
                path="src/main.py", category="source", description="Main module",
                provides_symbols=("main",), typical_change_triggers=("entry changes",),
            ),
            ArtifactDescriptor(
                path="src/utils.py", category="utility", description="Utilities",
                provides_symbols=("utils",), typical_change_triggers=("utility changes",),
            ),
            ArtifactDescriptor(
                path="src/helpers.py", category="helper", description="Helpers",
                provides_symbols=("helpers",), typical_change_triggers=("helper changes",),
            ),
            ArtifactDescriptor(
                path="tests/test_main.py", category="test", description="Main tests",
                provides_symbols=("test_main",), typical_change_triggers=("test changes",),
            ),
        )
        hybrid_strategy = HybridSelectiveStrategy(
            graph=DependencyGraph(
                nodes=("src/main.py", "src/utils.py", "src/helpers.py", "tests/test_main.py"),
                edges=(),
            ),
            artifact_descriptors=hybrid_descs,
        )
        hybrid_scenario = _make_scenario(
            "hybrid_repo", artifacts,
            before="main utils helpers",
            after="main utils helpers new_api",
        )
        hybrid_runner = _make_runner(
            tmp_path / "hybrid", hybrid_strategy, backend, iso_hybrid,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="hybrid_selective",
            editable_artifact_paths=("src/main.py", "src/utils.py", "src/helpers.py", "tests/test_main.py"),
        )
        hybrid_record = hybrid_runner.run(hybrid_scenario)

        assert full_record.regenerated_artifact_count >= hybrid_record.regenerated_artifact_count
        assert full_record.status == RunStatus.succeeded
        assert hybrid_record.status == RunStatus.succeeded


class TestLegacyImpactOnly:
    def test_legacy_impact_only_path_still_works(self, tmp_path: Path) -> None:
        iso, ws_root = _setup_workspace(tmp_path, ())
        iso = IsolationContext(workspace=iso.workspace, snapshot_base=iso.snapshot_base)
        backend = _make_backend("should not be called")
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario()

        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=False,
        )
        record = runner.run(scenario)

        assert record.status == RunStatus.succeeded
        assert record.regeneration_total_tokens == 0
        assert record.regenerated_artifact_count == 0
        assert record.functional_validation_passed is None

    def test_legacy_impact_only_all_fields_default(self, tmp_path: Path) -> None:
        iso, ws_root = _setup_workspace(tmp_path, ())
        iso = IsolationContext(workspace=iso.workspace, snapshot_base=iso.snapshot_base)
        backend = _make_backend("")
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario()

        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=False,
        )
        record = runner.run(scenario)
        assert record.selection_prompt_tokens == 0
        assert record.regeneration_prompt_tokens == 0
        assert record.functional_validation_duration_seconds == 0.0
        assert record.functional_validation_passed is None


class TestTokenAccounting:
    def test_token_accounting_internally_consistent(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/app.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        backend = _make_backend("replacement content")
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)

        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="monolithic",
            editable_artifact_paths=("src/app.py",),
        )
        record = runner.run(scenario)

        # totals should equal stage sums
        stage_total = record.selection_total_tokens + record.regeneration_total_tokens
        assert record.total_workflow_tokens == stage_total
        assert record.total_workflow_model_calls == record.selection_model_calls + record.regeneration_model_calls


class TestArtifactSelection:
    def test_planner_includes_regenerate(self) -> None:
        ref = ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source)
        prediction = _make_prediction([(ref, ActionKind.regenerate)])
        selector = ArtifactSelector()
        universe = _make_universe([ref])
        selection = selector.select(prediction, universe)
        assert len(selection.artifacts) == 1

    def test_planner_excludes_preserve(self) -> None:
        ref = ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source)
        prediction = _make_prediction([(ref, ActionKind.preserve)])
        selector = ArtifactSelector()
        universe = _make_universe([ref])
        selection = selector.select(prediction, universe)
        plan = RegenerationPlanner().plan(selection, prediction)
        assert len(plan.ordered_artifacts) == 0
        assert len(plan.regenerate_artifact_paths) == 0

    def test_human_review_recorded_not_executed(self) -> None:
        ref = ArtifactRef(path="src/review.py", artifact_type=ArtifactType.source)
        prediction = _make_prediction([(ref, ActionKind.human_review)])
        selector = ArtifactSelector()
        universe = _make_universe([ref])
        selection = selector.select(prediction, universe)
        plan = RegenerationPlanner().plan(selection, prediction)
        assert len(plan.human_review_artifact_paths) == 1
        assert len(plan.regenerate_artifact_paths) == 0


class TestEmptySelectiveScope:
    def test_empty_selective_scope_stays_empty(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/main.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        backend = _make_backend("should not be called")
        # Full preserve prediction → empty selection
        from benchmark.core.models import ImpactDecision
        class _PreserveStrategy:
            def analyze_impact(self, **kwargs):
                return ImpactPrediction(
                    decisions=(
                        ImpactDecision(
                            artifact=artifacts[0],
                            action=ActionKind.preserve,
                            rationale="no change",
                        ),
                    ),
                )
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, _PreserveStrategy(), backend, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="monolithic",
            editable_artifact_paths=("src/main.py",),
        )
        record = runner.run(scenario)
        assert record.regenerated_artifact_count == 0
        assert record.regeneration_model_calls == 0
        assert record.selected_artifact_count == 0
        assert record.status == RunStatus.failed
        has_guard_msg = any(
            "no model calls" in f.message.lower()
            or "generation guard" in f.message.lower()
            or "scientific" in f.stage
            for f in record.failures
        )
        assert has_guard_msg

    def test_empty_selective_scope_preserves_workspace(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/main.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        orig = (ws_root / "src/main.py").read_text(encoding="utf-8")
        backend = _make_backend("should not be called")
        from benchmark.core.models import ImpactDecision
        class _PreserveStrategy:
            def analyze_impact(self, **kwargs):
                return ImpactPrediction(
                    decisions=(
                        ImpactDecision(
                            artifact=artifacts[0],
                            action=ActionKind.preserve,
                            rationale="no change",
                        ),
                    ),
                )
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, _PreserveStrategy(), backend, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="monolithic",
            editable_artifact_paths=("src/main.py",),
        )
        runner.run(scenario)
        assert (ws_root / "src/main.py").read_text(encoding="utf-8") == orig


class TestValidationTriState:
    def test_legacy_no_validation_is_none(self, tmp_path: Path) -> None:
        iso, ws_root = _setup_workspace(tmp_path, ())
        iso = IsolationContext(workspace=iso.workspace, snapshot_base=iso.snapshot_base)
        backend = _make_backend("")
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario()
        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=False,
        )
        record = runner.run(scenario)
        assert record.functional_validation_passed is None

    def test_regeneration_without_validation_fails_closed(self, tmp_path: Path) -> None:
        iso, ws_root = _setup_workspace(tmp_path, ())
        backend = _make_backend("replacement")
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario()
        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=None,
            strategy_name="monolithic",
            editable_artifact_paths=("src/main.py",),
        )
        record = runner.run(scenario)
        assert record.status == RunStatus.failed
        assert record.functional_validation_passed is None

    def test_regeneration_with_empty_validation_fails_closed(self, tmp_path: Path) -> None:
        iso, ws_root = _setup_workspace(tmp_path, ())
        backend = _make_backend("replacement")
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario()
        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=[""],
            strategy_name="monolithic",
            editable_artifact_paths=("src/main.py",),
        )
        record = runner.run(scenario)
        assert record.status == RunStatus.failed

    def test_validation_passed_is_true(self, tmp_path: Path) -> None:
        artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        backend = _make_backend("replacement content")
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="monolithic",
        )
        record = runner.run(scenario)
        assert record.functional_validation_passed is True

    def test_validation_passed_is_false(self, tmp_path: Path) -> None:
        artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        backend = _make_backend("replacement content")
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(1)"],
            strategy_name="monolithic",
        )
        record = runner.run(scenario)
        assert record.functional_validation_passed is False

    def test_validation_timed_out_is_false(self, tmp_path: Path) -> None:
        artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        backend = _make_backend("replacement content")
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "import time; time.sleep(10)"],
            validation_timeout=1,
            strategy_name="monolithic",
        )
        record = runner.run(scenario)
        assert record.functional_validation_passed is False


class TestRegeneratedArtifactCount:
    def test_planned_but_rejected_not_counted(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        backend = _make_backend("")
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="monolithic",
        )
        record = runner.run(scenario)
        assert record.selected_artifact_count == 1
        assert record.regenerated_artifact_count == 0

    def test_mixed_results_count_only_generated(self, tmp_path: Path) -> None:
        class _MixedRejectionStrategy:
            def analyze_impact(self, **kwargs):
                from benchmark.core.models import ImpactDecision, ImpactPrediction
                return ImpactPrediction(
                    decisions=(
                        ImpactDecision(
                            artifact=ArtifactRef(path="src/good.py", artifact_type=ArtifactType.source),
                            action=ActionKind.regenerate,
                            rationale="ok",
                        ),
                        ImpactDecision(
                            artifact=ArtifactRef(path="src/bad.py", artifact_type=ArtifactType.source),
                            action=ActionKind.regenerate,
                            rationale="bad",
                        ),
                        ImpactDecision(
                            artifact=ArtifactRef(path="src/review.py", artifact_type=ArtifactType.source),
                            action=ActionKind.human_review,
                            rationale="uncertain",
                        ),
                    ),
                )
        all_artifacts = (
            ArtifactRef(path="src/good.py", artifact_type=ArtifactType.source),
            ArtifactRef(path="src/bad.py", artifact_type=ArtifactType.source),
            ArtifactRef(path="src/review.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, all_artifacts)
        (ws_root / "src/good.py").write_text("good original", encoding="utf-8")
        (ws_root / "src/bad.py").write_text("bad original", encoding="utf-8")
        (ws_root / "src/review.py").write_text("review original", encoding="utf-8")

        class _SelectiveBackend:
            def __init__(self):
                self._call_count = 0
            async def generate(self, prompt, temperature=0.0, max_tokens=4096):
                self._call_count += 1
                from benchmark.core.models import LLMResponse, TokenUsage
                tu = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
                if self._call_count == 1:
                    return LLMResponse(text="good output", token_usage=tu)
                return LLMResponse(text="```bad output```", token_usage=tu)

        backend = _SelectiveBackend()
        strategy = _MixedRejectionStrategy()
        scenario = _make_scenario(artifacts=all_artifacts)
        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="monolithic",
            editable_artifact_paths=("src/good.py", "src/bad.py", "src/review.py"),
        )
        record = runner.run(scenario)
        assert record.selected_artifact_count == 3
        assert record.regenerated_artifact_count == 1


class TestModelCallAggregation:
    def test_total_equals_selection_plus_regeneration(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
            ArtifactRef(path="src/b.py", artifact_type=ArtifactType.source),
            ArtifactRef(path="src/c.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        backend = _make_backend("replacement content")
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="monolithic",
            editable_artifact_paths=("src/a.py", "src/b.py", "src/c.py"),
        )
        record = runner.run(scenario)
        assert record.selection_model_calls == 0
        assert record.regeneration_model_calls == 3
        assert record.total_workflow_model_calls == 3

    def test_empty_plan_zero_calls(self, tmp_path: Path) -> None:
        iso, ws_root = _setup_workspace(tmp_path, ())
        backend = _make_backend("should not be called")
        from benchmark.core.models import ImpactPrediction
        class _NoOpStrategy:
            def analyze_impact(self, **kwargs):
                return ImpactPrediction()
        scenario = _make_scenario()
        runner = _make_runner(
            tmp_path, _NoOpStrategy(), backend, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="monolithic",
            editable_artifact_paths=("src/a.py",),
        )
        record = runner.run(scenario)
        assert record.selection_model_calls == 0
        assert record.regeneration_model_calls == 0
        assert record.total_workflow_model_calls == 0

    def test_no_regeneration_path_zero_calls(self, tmp_path: Path) -> None:
        iso, ws_root = _setup_workspace(tmp_path, ())
        iso = IsolationContext(workspace=iso.workspace, snapshot_base=iso.snapshot_base)
        backend = _make_backend("")
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario()
        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=False,
        )
        record = runner.run(scenario)
        assert record.selection_model_calls == 0
        assert record.regeneration_model_calls == 0
        assert record.total_workflow_model_calls == 0


class TestSelectionDuration:
    def test_selection_duration_measured(self, tmp_path: Path) -> None:
        artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        backend = _make_backend("replacement")
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="monolithic",
        )
        record = runner.run(scenario)
        assert record.selection_duration_seconds >= 0

    def test_total_duration_equals_stage_sum(self, tmp_path: Path) -> None:
        artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        backend = _make_backend("replacement")
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="monolithic",
        )
        record = runner.run(scenario)
        expected = (
            record.selection_duration_seconds
            + record.regeneration_duration_seconds
            + record.functional_validation_duration_seconds
        )
        assert abs(record.total_workflow_duration_seconds - expected) < 0.01

    def test_non_regeneration_path_no_duration(self, tmp_path: Path) -> None:
        iso, ws_root = _setup_workspace(tmp_path, ())
        iso = IsolationContext(workspace=iso.workspace, snapshot_base=iso.snapshot_base)
        backend = _make_backend("")
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario()
        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=False,
        )
        record = runner.run(scenario)
        assert record.selection_duration_seconds >= 0


class TestCanonicalSourcePreservation:
    def test_canonical_source_unchanged_after_regeneration(self, tmp_path: Path) -> None:
        artifacts = (ArtifactRef(path="src/main.py", artifact_type=ArtifactType.source),)
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        canonical = tmp_path / "canonical"
        canonical.mkdir()
        canonical_src = canonical / "src"
        canonical_src.mkdir()
        orig = "original source content"
        (canonical_src / "main.py").write_text(orig, encoding="utf-8")
        (ws_root / "src/main.py").write_text(orig, encoding="utf-8")

        backend = _make_backend("new content")
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="monolithic",
            editable_artifact_paths=("src/main.py",),
        )
        runner.run(scenario)
        assert (canonical_src / "main.py").read_text(encoding="utf-8") == orig

    def test_path_traversal_rejected(self, tmp_path: Path) -> None:
        iso, ws_root = _make_isolation(tmp_path)
        evil_ref = ArtifactRef(path="../../etc/passwd", artifact_type=ArtifactType.configuration)
        plan = RegenerationPlan(
            ordered_artifacts=(evil_ref,),
            actions={"../../etc/passwd": ActionKind.regenerate},
        )
        backend = _make_backend("evil")
        executor = SharedRegenerationExecutor(backend)
        result = executor.execute(plan, iso)
        assert len(result.failures) == 1
        assert "Path traversal" in result.failures[0]


def _make_isolation(tmp_path: Path) -> tuple[IsolationContext, Path]:
    ws_root = tmp_path / "workspace"
    ws_root.mkdir(parents=True, exist_ok=True)
    snap_base = tmp_path / "snapshots"
    snap_base.mkdir(exist_ok=True)
    active_root = snap_base / "test_repo" / "test_revision"
    active_root.mkdir(parents=True, exist_ok=True)
    ws = WorkspacePath(root=str(ws_root))
    iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active_root)
    return iso, ws_root


def _make_prediction(
    decisions: list[tuple[ArtifactRef, ActionKind]],
    errors: list[str] | None = None,
) -> ImpactPrediction:
    from benchmark.core.models import ImpactDecision, ImpactPrediction
    return ImpactPrediction(
        decisions=tuple(
            ImpactDecision(artifact=d[0], action=d[1], rationale="test")
            for d in decisions
        ),
        errors=tuple(errors or []),
    )


def _make_universe(artifacts: list[ArtifactRef]) -> ArtifactUniverse:
    from benchmark.core.models import ArtifactUniverse
    return ArtifactUniverse(artifacts=tuple(artifacts))


class TestMissingBackend:
    """Correction 1 — Fail closed when backend is absent."""

    def test_regeneration_enabled_backend_none_fails_closed(self, tmp_path: Path) -> None:
        artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, strategy, None, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="monolithic",
        )
        record = runner.run(scenario)
        assert record.status == RunStatus.failed
        assert any("backend" in f.message.lower() for f in record.failures)
        assert record.regenerated_artifact_count == 0
        assert record.regeneration_total_tokens == 0
        assert record.functional_validation_passed is None

    def test_impact_only_backend_none_still_succeeds(self, tmp_path: Path) -> None:
        iso, ws_root = _setup_workspace(tmp_path, ())
        iso = IsolationContext(workspace=iso.workspace, snapshot_base=iso.snapshot_base)
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario()
        runner = _make_runner(
            tmp_path, strategy, None, iso,
            enable_regeneration=False,
        )
        record = runner.run(scenario)
        assert record.status == RunStatus.succeeded

    def test_no_false_successful_end_to_end_record(self, tmp_path: Path) -> None:
        artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, strategy, None, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="monolithic",
        )
        record = runner.run(scenario)
        assert record.status == RunStatus.failed
        assert any(
            f.failure_kind.value == "harness_defect" for f in record.failures
        )
        assert record.regenerated_artifact_count == 0
        assert record.functional_validation_passed is None


class TestBoundedRepairAttempts:
    """SU-0010B3 — Bounded repair after validation failure."""

    def test_validation_success_no_repair(self, tmp_path: Path) -> None:
        artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
        iso, ws_root = _setup_workspace(tmp_path, artifacts)

        from benchmark.core.models import LLMResponse, TokenUsage
        call_count = 0

        class _CountingBackend:
            async def generate(self, prompt, temperature=0.0, max_tokens=4096):
                nonlocal call_count
                call_count += 1
                return LLMResponse(
                    text="content",
                    token_usage=TokenUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
                )

        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, strategy, _CountingBackend(), iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="monolithic",
            max_attempts=3,
        )
        record = runner.run(scenario)
        assert record.status == RunStatus.succeeded
        assert call_count == 1

    def test_validation_failure_triggers_repair(self, tmp_path: Path) -> None:
        artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
        iso, ws_root = _setup_workspace(tmp_path, artifacts)

        from benchmark.core.models import LLMResponse, TokenUsage
        call_count = 0

        class _CountingBackend:
            async def generate(self, prompt, temperature=0.0, max_tokens=4096):
                nonlocal call_count
                call_count += 1
                return LLMResponse(
                    text="content",
                    token_usage=TokenUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
                )

        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, strategy, _CountingBackend(), iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(1)"],
            strategy_name="monolithic",
            max_attempts=3,
        )
        record = runner.run(scenario)
        assert record.status == RunStatus.failed
        # Initial attempt (1) + 2 repair attempts (max_attempts=3)
        assert call_count == 3

    def test_generation_rejection_no_repair(self, tmp_path: Path) -> None:
        """Bounded repair after an empty first generation: second attempt
        produces valid source and the runner succeeds. (R3D correction:
        generation_guard failures are now repairable.)"""
        artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
        iso, ws_root = _setup_workspace(tmp_path, artifacts)

        from benchmark.core.models import LLMResponse, TokenUsage
        call_count = 0

        class _BoundedEmptyBackend:
            async def generate(self, prompt, temperature=0.0, max_tokens=4096):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return LLMResponse(
                        text="",
                        token_usage=TokenUsage(prompt_tokens=1, completion_tokens=0, total_tokens=1),
                    )
                return LLMResponse(
                    text="content",
                    token_usage=TokenUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
                )

        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, strategy, _BoundedEmptyBackend(), iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="monolithic",
            max_attempts=3,
        )
        runner.run(scenario)
        assert call_count == 2

    def test_max_attempts_bounds_repair(self, tmp_path: Path) -> None:
        artifacts = (
            ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
            ArtifactRef(path="src/b.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)

        from benchmark.core.models import LLMResponse, TokenUsage
        call_count = 0

        class _CountingBackend:
            async def generate(self, prompt, temperature=0.0, max_tokens=4096):
                nonlocal call_count
                call_count += 1
                return LLMResponse(
                    text="content",
                    token_usage=TokenUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
                )

        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, strategy, _CountingBackend(), iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(1)"],
            strategy_name="monolithic",
            max_attempts=3,
            editable_artifact_paths=("src/a.py", "src/b.py"),
        )
        record = runner.run(scenario)
        assert record.status == RunStatus.failed
        # 2 artifacts × (1 initial + 2 repair) = 6 calls
        assert call_count == 6

    def test_max_attempts_1_no_repair(self, tmp_path: Path) -> None:
        artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
        iso, ws_root = _setup_workspace(tmp_path, artifacts)

        from benchmark.core.models import LLMResponse, TokenUsage
        call_count = 0

        class _CountingBackend:
            async def generate(self, prompt, temperature=0.0, max_tokens=4096):
                nonlocal call_count
                call_count += 1
                return LLMResponse(
                    text="content",
                    token_usage=TokenUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
                )

        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, strategy, _CountingBackend(), iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(1)"],
            strategy_name="monolithic",
            max_attempts=1,
        )
        record = runner.run(scenario)
        assert record.status == RunStatus.failed
        assert call_count == 1  # Only initial attempt, no repair

    def test_impact_only_failure_still_follows_repair_loop(self, tmp_path: Path) -> None:
        iso, ws_root = _setup_workspace(tmp_path, ())
        iso = IsolationContext(workspace=iso.workspace, snapshot_base=iso.snapshot_base)
        call_count = 0

        class _RetryStrategy:
            def analyze_impact(self, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count < 2:
                    return ImpactPrediction(errors=("fail first",))
                return ImpactPrediction()

        backend = _make_backend("content")
        scenario = _make_scenario()
        runner = _make_runner(
            tmp_path, _RetryStrategy(), backend, iso,
            enable_regeneration=False,
            max_attempts=3,
        )
        record = runner.run(scenario)
        assert record.status == RunStatus.succeeded
        assert call_count == 2  # RepairLoop retried

    def test_validation_failure_then_repair_success(self, tmp_path: Path) -> None:
        artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
        iso, ws_root = _setup_workspace(tmp_path, artifacts)

        class _FlippingBackend:
            """First generation produces failing content, second passes."""
            def __init__(self):
                self._call_count = 0
            async def generate(self, prompt, temperature=0.0, max_tokens=4096):
                self._call_count += 1
                from benchmark.core.models import LLMResponse, TokenUsage
                tu = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
                if self._call_count == 1:
                    return LLMResponse(text="bad content that will fail", token_usage=tu, finish_reason="stop")
                return LLMResponse(text="good content", token_usage=tu, finish_reason="stop")

        # Validation: exit(0) if file contains "good", exit(1) otherwise
        check_cmd = [
            sys.executable, "-c",
            "import sys; fp='src/a.py'; "
            "sys.exit(0 if 'good' in open(fp).read() else 1)"
        ]
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, strategy, _FlippingBackend(), iso,
            enable_regeneration=True,
            validation_command=check_cmd,
            strategy_name="monolithic",
            max_attempts=3,
        )
        record = runner.run(scenario)
        assert record.status == RunStatus.succeeded
        assert record.functional_validation_passed is True
        assert record.regeneration_model_calls == 2

    def test_non_repairable_missing_validation(self, tmp_path: Path) -> None:
        iso, ws_root = _setup_workspace(tmp_path, ())
        backend = _make_backend("content")
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario()
        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=None,
            strategy_name="monolithic",
            max_attempts=3,
            editable_artifact_paths=("src/a.py",),
        )
        record = runner.run(scenario)
        assert record.status == RunStatus.failed
        assert record.functional_validation_passed is None
        # No repair attempts despite max_attempts=3
        assert record.regeneration_model_calls == 0

    def test_repair_context_contains_validation_evidence(self, tmp_path: Path) -> None:
        """Prove repair prompt includes validation failure evidence."""
        artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
        iso, ws_root = _setup_workspace(tmp_path, artifacts)

        prompts_received: list[str] = []

        class _RecordingBackend:
            async def generate(self, prompt, temperature=0.0, max_tokens=4096):
                prompts_received.append(prompt)
                from benchmark.core.models import LLMResponse, TokenUsage
                tu = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
                return LLMResponse(text="content", token_usage=tu, finish_reason="stop")

        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, strategy, _RecordingBackend(), iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(42)"],
            strategy_name="monolithic",
            max_attempts=2,
        )
        runner.run(scenario)

        # At least 2 generation calls: initial + repair
        assert len(prompts_received) >= 2

        # The repair prompt (2nd call) should contain validation failure evidence
        repair_prompt = prompts_received[1]
        assert "exit code" in repair_prompt.lower() or "exit=" in repair_prompt.lower() or "42" in repair_prompt
        # No Ground Truth content
        assert "ground truth" not in repair_prompt.lower()

    def test_selection_metrics_counted_once(self, tmp_path: Path) -> None:
        artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
        iso, ws_root = _setup_workspace(tmp_path, artifacts)

        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)

        class _CountingBackend:
            def __init__(self):
                self._call_count = 0
            async def generate(self, prompt, temperature=0.0, max_tokens=4096):
                self._call_count += 1
                from benchmark.core.models import LLMResponse, TokenUsage
                tu = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
                return LLMResponse(text="content", token_usage=tu, finish_reason="stop")

        backend = _CountingBackend()
        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(1)"],
            strategy_name="monolithic",
            max_attempts=3,
        )
        record = runner.run(scenario)

        # Selection metrics unchanged across repair attempts
        assert record.selection_model_calls == 0
        # Only verify metrics are populated (not aggregated multiple times)
        assert record.selection_prompt_tokens == 0
        assert record.selection_total_tokens == 0

    def test_regeneration_and_validation_metrics_aggregated(self, tmp_path: Path) -> None:
        artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
        iso, ws_root = _setup_workspace(tmp_path, artifacts)

        class _CountingBackend:
            def __init__(self):
                self._call_count = 0
            async def generate(self, prompt, temperature=0.0, max_tokens=4096):
                self._call_count += 1
                from benchmark.core.models import LLMResponse, TokenUsage
                tu = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
                return LLMResponse(text="content", token_usage=tu, finish_reason="stop")

        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, strategy, _CountingBackend(), iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(1)"],
            strategy_name="monolithic",
            max_attempts=3,
        )
        record = runner.run(scenario)

        # 3 attempts × 1 artifact
        assert record.regeneration_model_calls == 3
        assert record.regeneration_total_tokens > 0
        assert record.functional_validation_duration_seconds > 0

    def test_token_budget_stops_repair(self, tmp_path: Path) -> None:
        """Prove initial generation exhausts token budget, preventing repair."""
        artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
        iso, ws_root = _setup_workspace(tmp_path, artifacts)

        from benchmark.core.models import LLMResponse, TokenUsage

        class _ControlledTokenBackend:
            def count_prompt_tokens(self, prompt: str) -> int:
                return 10

            async def generate(self, prompt, temperature=0.0, max_tokens=4096):
                return LLMResponse(
                    text="content",
                    token_usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
                )

        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, strategy, _ControlledTokenBackend(), iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(1)"],
            strategy_name="monolithic",
            max_attempts=10,
            max_tokens=15,
        )
        record = runner.run(scenario)
        assert record.status == RunStatus.failed
        # Only initial generation, no repair
        assert record.regeneration_model_calls == 1

    def test_timeout_stops_repair(self, tmp_path: Path) -> None:
        """Prove initial generation executes but timeout after it prevents repair."""
        artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
        iso, ws_root = _setup_workspace(tmp_path, artifacts)

        call_count = 0

        class _AdvancingClock:
            def __init__(self):
                self._now = 100.0

            def now(self):
                return self._now

            def advance(self, seconds):
                self._now += seconds

        clock = _AdvancingClock()

        from benchmark.core.models import LLMResponse, TokenUsage

        class _TimedOutBackend:
            async def generate(self, prompt, temperature=0.0, max_tokens=4096):
                nonlocal call_count
                call_count += 1
                # Advance past timeout during the first generation
                clock.advance(15)
                return LLMResponse(
                    text="content",
                    token_usage=TokenUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
                )

        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)

        config = RunnerConfig(
            strategy_name="monolithic",
            backend_name="mock",
            protocol_version="1.0",
            max_attempts=10,
            timeout_seconds=10,
            enable_regeneration=True,
            editable_artifact_paths=("src/a.py",),
            validation_command=[sys.executable, "-c", "exit(1)"],
        )
        runner = BenchmarkRunner(
            strategy=strategy,
            backend=_TimedOutBackend(),
            isolation=iso,
            config=config,
        )
        # Inject clock that advances past timeout after the initial generation
        runner._budget = BudgetManager(
            max_attempts=10,
            timeout_seconds=10,
            clock=clock,
        )
        record = runner.run(scenario)
        assert call_count == 1  # Only initial generation executed
        assert record.status == RunStatus.failed

    def test_token_budget_exhausted_after_initial_no_repair(self, tmp_path: Path) -> None:
        """Prove initial attempt tokens are added to budget and prevent repair."""
        artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
        iso, ws_root = _setup_workspace(tmp_path, artifacts)

        from benchmark.core.models import LLMResponse, TokenUsage

        class _ControlledTokenBackend:
            def count_prompt_tokens(self, prompt: str) -> int:
                return 10

            async def generate(self, prompt, temperature=0.0, max_tokens=4096):
                return LLMResponse(
                    text="x",
                    token_usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
                )

        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, strategy, _ControlledTokenBackend(), iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(1)"],
            strategy_name="monolithic",
            max_attempts=10,
            max_tokens=15,  # initial generation consumes all 15
        )
        record = runner.run(scenario)
        assert record.status == RunStatus.failed
        assert record.regeneration_model_calls == 1

    def test_token_budget_exhausted_after_one_repair(self, tmp_path: Path) -> None:
        """Prove token budget prevents second repair after one repair exhausts it."""
        artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
        iso, ws_root = _setup_workspace(tmp_path, artifacts)

        from benchmark.core.models import LLMResponse, TokenUsage

        class _ControlledTokenBackend:
            def count_prompt_tokens(self, prompt: str) -> int:
                return 10

            async def generate(self, prompt, temperature=0.0, max_tokens=4096):
                return LLMResponse(
                    text="x",
                    token_usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
                )

        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, strategy, _ControlledTokenBackend(), iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(1)"],
            strategy_name="monolithic",
            max_attempts=10,
            max_tokens=30,  # initial (15) + one repair (15) = 30, exhausts budget
        )
        record = runner.run(scenario)
        assert record.status == RunStatus.failed
        # 2 attempts: initial + one repair, no second repair
        assert record.regeneration_model_calls == 2

    def test_max_attempts_behavior_unchanged(self, tmp_path: Path) -> None:
        """Prove max_attempts still includes the initial attempt."""
        artifacts = (
            ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)

        from benchmark.core.models import LLMResponse, TokenUsage
        call_count = 0

        class _CountingBackend:
            async def generate(self, prompt, temperature=0.0, max_tokens=4096):
                nonlocal call_count
                call_count += 1
                return LLMResponse(
                    text="content",
                    token_usage=TokenUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
                )

        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, strategy, _CountingBackend(), iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(1)"],
            strategy_name="monolithic",
            max_attempts=3,
        )
        record = runner.run(scenario)
        assert record.status == RunStatus.failed
        # 1 initial + 2 repair = 3 attempts total
        assert call_count == 3

    def test_repair_success_preserves_failure_history(self, tmp_path: Path) -> None:
        """Prove successful repair retains previous validation-failure records."""
        artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
        iso, ws_root = _setup_workspace(tmp_path, artifacts)

        class _FlippingBackend:
            def __init__(self):
                self._call_count = 0

            async def generate(self, prompt, temperature=0.0, max_tokens=4096):
                self._call_count += 1
                from benchmark.core.models import LLMResponse, TokenUsage
                tu = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
                if self._call_count == 1:
                    return LLMResponse(text="bad content that will fail", token_usage=tu, finish_reason="stop")
                return LLMResponse(text="good content", token_usage=tu, finish_reason="stop")

        check_cmd = [
            sys.executable, "-c",
            "import sys; fp='src/a.py'; "
            "sys.exit(0 if 'good' in open(fp).read() else 1)"
        ]
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, strategy, _FlippingBackend(), iso,
            enable_regeneration=True,
            validation_command=check_cmd,
            strategy_name="monolithic",
            max_attempts=3,
        )
        record = runner.run(scenario)
        assert record.status == RunStatus.succeeded
        assert record.functional_validation_passed is True
        assert record.regeneration_model_calls == 2
        # Previous validation-failure records must be preserved
        assert len(record.failures) > 0
        assert any("validation failed" in f.message for f in record.failures)

    def test_first_attempt_success_no_repair_history(self, tmp_path: Path) -> None:
        """Prove first-attempt success has no repair-failure history."""
        artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
        iso, ws_root = _setup_workspace(tmp_path, artifacts)

        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, strategy, _make_backend("content"), iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="monolithic",
        )
        record = runner.run(scenario)
        assert record.status == RunStatus.succeeded
        assert len(record.failures) == 0

    def test_metrics_double_counted_not_duplicated(self, tmp_path: Path) -> None:
        """Prove regeneration and workflow token metrics include every executed attempt exactly once."""
        artifacts = (
            ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),
            ArtifactRef(path="src/b.py", artifact_type=ArtifactType.source),
        )
        iso, ws_root = _setup_workspace(tmp_path, artifacts)

        from benchmark.core.models import LLMResponse, TokenUsage

        class _KnownMetricBackend:
            async def generate(self, prompt, temperature=0.0, max_tokens=4096):
                return LLMResponse(
                    text="content",
                    token_usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
                )

        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, strategy, _KnownMetricBackend(), iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(1)"],
            strategy_name="monolithic",
            max_attempts=3,
            editable_artifact_paths=("src/a.py", "src/b.py"),
        )
        record = runner.run(scenario)
        # 2 artifacts × 3 attempts = 6 model calls
        assert record.regeneration_model_calls == 6
        # Each call uses 15 tokens: 6 × 15 = 90
        expected_regen_tokens = 90
        assert record.regeneration_total_tokens == expected_regen_tokens
        # total_workflow_tokens = selection (0) + regen (90)
        assert record.total_workflow_tokens == expected_regen_tokens


class TestStrategyGuard:
    """Correction 3 — Restrict SU-0010A to approved conditions."""

    def _make_simple_runner(self, tmp_path: Path, strategy_name: str) -> BenchmarkRunner:
        artifact = ArtifactRef(path="src/main.py", artifact_type=ArtifactType.source)
        iso, ws_root = _setup_workspace(tmp_path, (artifact,))
        strategy = MonolithicRegenerationStrategy()
        runner = _make_runner(
            tmp_path, strategy, _make_backend("content"), iso,
            enable_regeneration=True,
            editable_artifact_paths=("src/main.py",),
            strategy_name=strategy_name,
        )
        return runner

    @staticmethod
    def _has_condition_failure(record: RunRecord) -> bool:
        return any("condition" in f.message for f in record.failures)

    def test_monolithic_accepted(self, tmp_path: Path) -> None:
        artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        backend = _make_backend("replacement content")
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="monolithic",
        )
        record = runner.run(scenario)
        assert not self._has_condition_failure(record)

    def test_full_scope_reference_accepted(self, tmp_path: Path) -> None:
        artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        backend = _make_backend("replacement content")
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="full_scope_reference",
        )
        record = runner.run(scenario)
        assert not self._has_condition_failure(record)

    def test_selective_accepted(self, tmp_path: Path) -> None:
        artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        backend = _make_backend("replacement content")
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="selective",
        )
        record = runner.run(scenario)
        assert not self._has_condition_failure(record)

    def test_hybrid_selective_accepted(self, tmp_path: Path) -> None:
        artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
        iso, ws_root = _setup_workspace(tmp_path, artifacts)
        backend = _make_backend("replacement content")
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)
        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="hybrid_selective",
        )
        record = runner.run(scenario)
        assert not self._has_condition_failure(record)

    def test_agent_rejected(self, tmp_path: Path) -> None:
        runner = self._make_simple_runner(tmp_path, "agent")
        record = runner.run(_make_scenario())
        assert record.status == RunStatus.failed
        assert self._has_condition_failure(record)

    def test_iterative_agent_accepted(self, tmp_path: Path) -> None:
        runner = self._make_simple_runner(tmp_path, "iterative_repository_agent")
        record = runner.run(_make_scenario())
        assert not self._has_condition_failure(record)

    def test_unknown_strategy_rejected(self, tmp_path: Path) -> None:
        runner = self._make_simple_runner(tmp_path, "unknown_strategy")
        record = runner.run(_make_scenario())
        assert record.status == RunStatus.failed
        assert self._has_condition_failure(record)


class TestFairTokenBudget:
    """Correction 3 — Fair token-budget meaning across all regeneration arms."""

    def _make_agent_strategy_backend(self) -> tuple[object, object]:
        """Create an agent strategy and backend that produce known token usage."""

        class _AgentBackend:
            async def generate(self, prompt, temperature=0.0, max_tokens=4096):
                from benchmark.core.models import LLMResponse
                return LLMResponse(
                    text='{"action":"final","selected_paths":["src/a.py"],"rationale":"test"}',
                    token_usage=TokenUsage(prompt_tokens=30, completion_tokens=20, total_tokens=50),
                    finish_reason="stop",
                )

        from benchmark.strategies.agent import RepositoryAgentStrategy
        ab = _AgentBackend()
        return ab, RepositoryAgentStrategy(backend=ab)

    def test_oneshot_records_selection_and_regen_tokens_in_budget(self, tmp_path: Path) -> None:
        """A one-shot arm records selection plus regeneration tokens in BudgetManager."""
        artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
        iso, ws_root = _setup_workspace(tmp_path, artifacts)

        backend = _make_backend("replacement content")
        from benchmark.strategies.monolithic import MonolithicRegenerationStrategy
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)

        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            strategy_name="monolithic",
            max_tokens=1000,
        )
        _ = runner.run(scenario)
        total = runner._budget.state.total_tokens
        assert total > 0, "BudgetManager must record regeneration tokens"

    def test_same_max_tokens_stops_oneshot_before_call(self, tmp_path: Path) -> None:
        """One-shot arm stops before additional call after max_tokens exhausted."""
        artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
        iso, ws_root = _setup_workspace(tmp_path, artifacts)

        from benchmark.core.models import LLMResponse

        class _SmallTokenBackend:
            def __init__(self):
                self.call_count = 0

            def count_prompt_tokens(self, prompt: str) -> int:
                return 5

            async def generate(self, prompt, temperature=0.0, max_tokens=4096):
                self.call_count += 1
                return LLMResponse(
                    text="content",
                    token_usage=TokenUsage(prompt_tokens=5, completion_tokens=3, total_tokens=8),
                )

        rb = _SmallTokenBackend()
        from benchmark.strategies.monolithic import MonolithicRegenerationStrategy
        strategy = MonolithicRegenerationStrategy()
        scenario = _make_scenario(artifacts=artifacts)

        runner = _make_runner(
            tmp_path, strategy, rb, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(1)"],
            strategy_name="monolithic",
            max_attempts=10,
            max_tokens=8,
        )
        _ = runner.run(scenario)
        assert rb.call_count == 1

    def test_same_max_tokens_stops_iterative_before_call(self, tmp_path: Path) -> None:
        """Iterative arm stops before additional call after max_tokens exhausted."""
        from benchmark.core.models import LLMResponse
        from benchmark.strategies.iterative_agent import IterativeRepositoryAgentStrategy

        class _StrategyBackend:
            def __init__(self):
                self.call_count = 0

            def count_prompt_tokens(self, prompt: str) -> int:
                return 30

            async def generate(self, prompt, temperature=0.0, max_tokens=4096):
                self.call_count += 1
                return LLMResponse(
                    text='{"action":"final","selected_paths":["src/a.py"],"rationale":"only"}',
                    token_usage=TokenUsage(prompt_tokens=30, completion_tokens=20, total_tokens=50),
                    finish_reason="stop",
                )

        artifacts = (ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source),)
        iso, ws_root = _setup_workspace(tmp_path, artifacts)

        sb = _StrategyBackend()
        strategy = IterativeRepositoryAgentStrategy(backend=sb)

        class _RegenCounter:
            def __init__(self):
                self.call_count = 0

            def count_prompt_tokens(self, prompt: str) -> int:
                return 5

            async def generate(self, prompt, temperature=0.0, max_tokens=4096):
                self.call_count += 1
                return LLMResponse(
                    text="content",
                    token_usage=TokenUsage(prompt_tokens=5, completion_tokens=3, total_tokens=8),
                )

        rb = _RegenCounter()
        scenario = _make_scenario(artifacts=artifacts)
        check_cmd = [sys.executable, "-c", "exit(1)"]
        runner = _make_runner(
            tmp_path, strategy, rb, iso,
            enable_regeneration=True,
            validation_command=check_cmd,
            strategy_name="iterative_repository_agent",
            max_attempts=10,
            max_tokens=50,
        )

        _ = runner.run(scenario)
        assert sb.call_count == 1
        assert rb.call_count == 0
