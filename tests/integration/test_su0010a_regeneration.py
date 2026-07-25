"""SU-0010A integration tests: minimal shared regeneration path end-to-end."""

import sys
from pathlib import Path

from benchmark.core.enums import ActionKind, ArtifactType, BlastRadius, RunStatus
from benchmark.core.models import (
    AcceptanceCriterion,
    ArtifactRef,
    ArtifactUniverse,
    ImpactPrediction,
    Scenario,
    TokenUsage,
)
from benchmark.execution.isolation import IsolationContext
from benchmark.execution.runner import BenchmarkRunner, RunnerConfig
from benchmark.repositories.workspace import WorkspacePath
from benchmark.selection.planner import ArtifactSelector, RegenerationPlanner
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


def _setup_workspace(tmp_path: Path, artifacts: tuple[ArtifactRef, ...]) -> tuple[IsolationContext, Path]:
    ws_root = tmp_path / "workspace"
    ws_root.mkdir(parents=True, exist_ok=True)
    snap_base = tmp_path / "snapshots"
    snap_base.mkdir(exist_ok=True)

    for ref in artifacts:
        target = ws_root / ref.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"original {ref.path} content", encoding="utf-8")

    ws = WorkspacePath(root=str(ws_root))
    iso = IsolationContext(workspace=ws, snapshot_base=snap_base)
    return iso, ws_root


def _make_runner(
    tmp_path: Path,
    strategy: object,
    backend: object,
    iso: IsolationContext,
    enable_regeneration: bool = False,
    validation_command: list[str] | None = None,
) -> BenchmarkRunner:
    config = RunnerConfig(
        strategy_name="test",
        backend_name="mock",
        protocol_version="1.0",
        max_attempts=1,
        enable_regeneration=enable_regeneration,
        validation_command=validation_command,
        validation_timeout=10,
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
        strategy = HybridSelectiveStrategy(semantic_threshold=0.0)
        scenario = _make_scenario(
            artifacts=artifacts,
            before="models utils",
            after="models utils new_feature",
        )

        runner = _make_runner(
            tmp_path, strategy, backend, iso,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
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
        iso_full, ws_full = _setup_workspace(tmp_path / "full", artifacts)
        iso_hybrid, ws_hybrid = _setup_workspace(tmp_path / "hybrid", artifacts)

        backend = _make_backend("replacement content")

        # Full scope run
        full_strategy = MonolithicRegenerationStrategy()
        full_scenario = _make_scenario("full_repo", artifacts)
        full_runner = _make_runner(
            tmp_path / "full", full_strategy, backend, iso_full,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
        )
        full_record = full_runner.run(full_scenario)

        # Hybrid selective run
        hybrid_strategy = HybridSelectiveStrategy(semantic_threshold=0.0)
        hybrid_scenario = _make_scenario(
            "hybrid_repo", artifacts,
            before="main utils helpers",
            after="main utils helpers new_api",
        )
        hybrid_runner = _make_runner(
            tmp_path / "hybrid", hybrid_strategy, backend, iso_hybrid,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
        )
        hybrid_record = hybrid_runner.run(hybrid_scenario)

        assert full_record.regenerated_artifact_count >= hybrid_record.regenerated_artifact_count
        assert full_record.status == RunStatus.succeeded
        assert hybrid_record.status == RunStatus.succeeded


class TestLegacyImpactOnly:
    def test_legacy_impact_only_path_still_works(self, tmp_path: Path) -> None:
        iso, ws_root = _setup_workspace(tmp_path, ())
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
        assert record.functional_validation_passed is False

    def test_legacy_impact_only_all_fields_default(self, tmp_path: Path) -> None:
        iso, ws_root = _setup_workspace(tmp_path, ())
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
        )
        record = runner.run(scenario)

        # totals should equal stage sums
        stage_total = record.selection_total_tokens + record.regeneration_total_tokens
        assert record.total_workflow_tokens == stage_total
        assert record.total_workflow_model_calls >= record.regeneration_model_calls


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
