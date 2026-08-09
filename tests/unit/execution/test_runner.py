import sys
import time
from pathlib import Path

import pytest

from benchmark.core.enums import ActionKind, ArtifactType, BlastRadius, FailureKind, RunStatus
from benchmark.core.models import (
    AcceptanceCriterion,
    ArchitectureConstraint,
    ArtifactRef,
    ArtifactUniverse,
    FailureRecord,
    ImpactDecision,
    ImpactPrediction,
    LLMResponse,
    RepositorySnapshot,
    RequirementChange,
    RunIdentity,
    RunRecord,
    Scenario,
    TokenUsage,
)
from benchmark.execution.isolation import IsolationContext
from benchmark.execution.post_generation import PostGenerationResult
from benchmark.execution.runner import (
    BenchmarkRunner,
    RunnerConfig,
    _compact_head_tail,
    _extract_root_cause,
    _ScientificValidationResult,
)
from benchmark.repositories.snapshot import resolve_allowed_artifacts
from benchmark.repositories.workspace import WorkspacePath


class _FakeStrategy:
    def __init__(self) -> None:
        self.calls: list[tuple[RepositorySnapshot, RequirementChange, ArtifactUniverse]] = []

    def analyze_impact(
        self,
        repository: RepositorySnapshot,
        requirement_change: RequirementChange,
        artifact_universe: ArtifactUniverse,
    ) -> ImpactPrediction:
        self.calls.append((repository, requirement_change, artifact_universe))
        return ImpactPrediction()


class _FakeBackend:
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        return LLMResponse(text="mock")


def _make_scenario(scenario_id: str = "test") -> Scenario:
    return Scenario(
        scenario_id=scenario_id,
        repository="repo",
        change_type="modify",
        blast_radius=BlastRadius.localized,
        requirement_before="before",
        requirement_after="after",
        rationale="test",
    )


def _make_runner(tmp_path: Path, max_attempts: int = 3) -> BenchmarkRunner:
    ws_root = tmp_path / "workspace"
    ws_root.mkdir()
    snap_base = tmp_path / "snapshots"
    snap_base.mkdir()
    active_root = snap_base / "repo" / "rev1"
    active_root.mkdir(parents=True)
    ws = WorkspacePath(root=str(ws_root))
    iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active_root)

    config = RunnerConfig(
        strategy_name="test_strategy",
        backend_name="test_backend",
        protocol_version="1.0",
        max_attempts=max_attempts,
    )
    return BenchmarkRunner(
        strategy=_FakeStrategy(),
        backend=_FakeBackend(),
        isolation=iso,
        config=config,
    )


class TestBenchmarkRunner:
    def test_dry_run_returns_succeeded(self, tmp_path: Path) -> None:
        runner = _make_runner(tmp_path)
        record = runner.dry_run(_make_scenario())
        assert record.status == RunStatus.succeeded
        assert record.duration_seconds == 0.0

    def test_run_returns_record(self, tmp_path: Path) -> None:
        runner = _make_runner(tmp_path)
        record = runner.run(_make_scenario())
        assert isinstance(record, RunRecord)
        assert record.identity.strategy_name == "test_strategy"
        assert record.identity.scenario_id == "test"

    def test_state_machine_tracks_lifecycle(self, tmp_path: Path) -> None:
        runner = _make_runner(tmp_path)
        assert runner.state.is_prepared is True
        runner.dry_run(_make_scenario())
        assert runner.state.succeeded is True

    def test_isolation_failure_returns_failure_record(self, tmp_path: Path) -> None:
        ws = WorkspacePath(root=str(tmp_path))
        iso = IsolationContext(workspace=ws, snapshot_base=tmp_path)
        config = RunnerConfig(
            strategy_name="s", backend_name="b", protocol_version="1.0",
        )
        runner = BenchmarkRunner(
            strategy=_FakeStrategy(),
            backend=_FakeBackend(),
            isolation=iso,
            config=config,
        )
        record = runner.run(_make_scenario())
        assert record.status == RunStatus.failed
        assert any("Isolation" in f.message for f in record.failures)

    def test_budget_property(self, tmp_path: Path) -> None:
        runner = _make_runner(tmp_path, max_attempts=5)
        assert runner.budget.max_attempts == 5

    def test_deadline_before_selection_stops_next_model_call(self, tmp_path: Path) -> None:
        strategy = _FakeStrategy()
        ws_root = tmp_path / "workspace"
        ws_root.mkdir()
        snap_base = tmp_path / "snapshots"
        snap_base.mkdir()
        active_root = snap_base / "repo" / "rev1"
        active_root.mkdir(parents=True)
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active_root)
        config = RunnerConfig(
            strategy_name="monolithic",
            backend_name="test_backend",
            protocol_version="1.0",
            max_attempts=3,
            timeout_seconds=1,
            enable_regeneration=True,
            validation_command=["pytest"],
        )
        runner = BenchmarkRunner(
            strategy=strategy,
            backend=_FakeBackend(),
            isolation=iso,
            config=config,
        )
        object.__setattr__(runner.budget._state, "start_time", time.time() - 1000)

        record = runner.run(_make_scenario())

        assert record.status == RunStatus.failed
        assert record.failures[0].failure_kind == FailureKind.scientific_budget_exhausted
        assert strategy.calls == []
        assert "configured_budget" in record.failures[0].message
        assert "actual_elapsed_seconds" in record.failures[0].message

    def test_budget_exhaustion_before_generation_is_scientific(self, tmp_path: Path) -> None:
        strategy = _FakeStrategy()
        ws_root = tmp_path / "workspace"
        ws_root.mkdir()
        snap_base = tmp_path / "snapshots"
        snap_base.mkdir()
        active_root = snap_base / "repo" / "rev1"
        active_root.mkdir(parents=True)
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active_root)
        config = RunnerConfig(
            strategy_name="monolithic",
            backend_name="test_backend",
            protocol_version="1.0",
            max_attempts=1,
            timeout_seconds=1,
            enable_regeneration=True,
            validation_command=["pytest"],
        )
        runner = BenchmarkRunner(
            strategy=strategy,
            backend=_FakeBackend(),
            isolation=iso,
            config=config,
        )
        object.__setattr__(runner.budget._state, "start_time", time.time() - 1000)

        record = runner.run(_make_scenario())

        assert record.status == RunStatus.failed
        assert record.failures[0].failure_kind == FailureKind.scientific_budget_exhausted
        assert strategy.calls == []

    def test_generation_deadline_stops_after_first_model_call(self, tmp_path: Path) -> None:
        """Closure A generation deadline at the runner level.

        Three artifacts are selected; call 1 advances the fake clock beyond
        the deadline. Exactly one model call happens, no further call is made,
        nothing is written, and the run is a scientific budget-exhausted
        terminal with the consumed call/tokens retained.
        """
        class _ThreeArtifactStrategy:
            def analyze_impact(
                self,
                repository: RepositorySnapshot,
                requirement_change: RequirementChange,
                artifact_universe: ArtifactUniverse,
            ) -> ImpactPrediction:
                return ImpactPrediction(
                    decisions=tuple(
                        ImpactDecision(
                            artifact=a,
                            action=ActionKind.regenerate,
                            rationale="test",
                        )
                        for a in artifact_universe.artifacts
                    )
                )

        holder: dict[str, object] = {}

        class _DeadlineRewindingBackend:
            def __init__(self) -> None:
                self.call_count = 0
                self._tok = TokenUsage(
                    prompt_tokens=10, completion_tokens=5, total_tokens=15
                )

            async def generate(
                self,
                prompt: str,
                temperature: float = 0.0,
                max_tokens: int = 4096,
            ) -> LLMResponse:
                self.call_count += 1
                object.__setattr__(
                    holder["runner"].budget._state, "start_time", time.time() - 1000
                )
                return LLMResponse(
                    text="replacement content",
                    token_usage=self._tok,
                    finish_reason="stop",
                )

        ws_root = tmp_path / "workspace"
        ws_root.mkdir()
        snap_base = tmp_path / "snapshots"
        snap_base.mkdir()
        active_root = snap_base / "repo" / "rev1"
        active_root.mkdir(parents=True)
        for rel in ("src/a.py", "src/b.py", "src/c.py"):
            for root in (ws_root, active_root):
                target = root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(f"original {rel}\n", encoding="utf-8")
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active_root)
        config = RunnerConfig(
            strategy_name="monolithic",
            backend_name="test_backend",
            protocol_version="1.0",
            max_attempts=3,
            timeout_seconds=1,
            enable_regeneration=True,
            validation_command=["pytest"],
            editable_artifact_paths=("src/a.py", "src/b.py", "src/c.py"),
        )
        backend = _DeadlineRewindingBackend()
        runner = BenchmarkRunner(
            strategy=_ThreeArtifactStrategy(),
            backend=backend,
            isolation=iso,
            config=config,
        )
        holder["runner"] = runner

        record = runner.run(_make_scenario())

        assert backend.call_count == 1
        assert record.status == RunStatus.failed
        assert record.failures[0].failure_kind == FailureKind.scientific_budget_exhausted
        assert record.regenerated_artifact_count == 0
        assert record.regeneration_model_calls == 1
        assert record.total_workflow_tokens == 15
        for rel in ("src/a.py", "src/b.py", "src/c.py"):
            assert (ws_root / rel).read_text(encoding="utf-8") == f"original {rel}\n"

    def test_run_id_includes_scenario_and_strategy(self, tmp_path: Path) -> None:
        runner = _make_runner(tmp_path)
        record = runner.dry_run(_make_scenario("scenario-x"))
        assert "scenario-x" in record.identity.run_id
        assert "test_strategy" in record.identity.run_id

    def test_run_extracts_correct_domain_objects(self, tmp_path: Path) -> None:
        strategy = _FakeStrategy()
        ws_root = tmp_path / "workspace"
        ws_root.mkdir()
        snap_base = tmp_path / "snapshots"
        snap_base.mkdir()
        active_root = snap_base / "repo" / "rev1"
        active_root.mkdir(parents=True)
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active_root)
        config = RunnerConfig(
            strategy_name="test_strategy",
            backend_name="test_backend",
            protocol_version="1.0",
            max_attempts=3,
        )
        runner = BenchmarkRunner(
            strategy=strategy,
            backend=_FakeBackend(),
            isolation=iso,
            config=config,
        )
        scenario = _make_scenario("sc-001")
        record = runner.run(scenario)
        assert record.status == RunStatus.succeeded
        assert len(strategy.calls) == 1
        repo, change, universe = strategy.calls[0]
        assert isinstance(repo, RepositorySnapshot)
        assert isinstance(change, RequirementChange)
        assert isinstance(universe, ArtifactUniverse)
        assert repo.identity.name == "repo"
        assert repo.commit_sha == "sc-001"
        assert change.before == "before"
        assert change.after == "after"
        assert len(change.acceptance_criteria) == 0
        assert len(universe.artifacts) == 0


    def test_evaluator_metadata_never_reaches_strategy(self, tmp_path: Path) -> None:
        strategy = _FakeStrategy()
        ws_root = tmp_path / "workspace"
        ws_root.mkdir()
        snap_base = tmp_path / "snapshots"
        snap_base.mkdir()
        active_root = snap_base / "repo" / "rev1"
        active_root.mkdir(parents=True)
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active_root)
        config = RunnerConfig(
            strategy_name="test_strategy",
            backend_name="test_backend",
            protocol_version="1.0",
            max_attempts=3,
        )
        runner = BenchmarkRunner(
            strategy=strategy,
            backend=_FakeBackend(),
            isolation=iso,
            config=config,
        )
        scenario = Scenario(
            scenario_id="sc-smoke",
            repository="repo",
            change_type="modify",
            blast_radius=BlastRadius.localized,
            requirement_before="before text",
            requirement_after="after text",
            rationale="test",
            acceptance_criteria=(
                AcceptanceCriterion(description="public criterion 1"),
                AcceptanceCriterion(description="public criterion 2"),
            ),
            expected_affected_artifacts=(
                ArtifactRef(path="todo/models.py", artifact_type=ArtifactType.source),
            ),
            architecture_constraints=(
                ArchitectureConstraint(description="some constraint"),
            ),
            hidden_tests=("hidden test",),
            evaluator_asset="tests/evaluator_assets/todo_smoke_001_checks.py",
            post_generation_command=("python", "manage.py", "makemigrations", "todo", "--noinput"),
            require_new_migration=True,
        )
        record = runner.run(scenario)
        assert record.status == RunStatus.succeeded
        assert len(strategy.calls) == 1
        _repo, change, _universe = strategy.calls[0]
        assert change.before == "before text"
        assert change.after == "after text"
        assert change.acceptance_criteria == ("public criterion 1", "public criterion 2")
        assert not hasattr(change, "evaluator_asset")
        assert not hasattr(change, "post_generation_command")
        assert not hasattr(change, "require_new_migration")
        assert not hasattr(change, "hidden_tests")
        assert not hasattr(change, "expected_affected_artifacts")

    def test_runner_passes_acceptance_criteria_only(self, tmp_path: Path) -> None:
        strategy = _FakeStrategy()
        ws_root = tmp_path / "workspace"
        ws_root.mkdir()
        snap_base = tmp_path / "snapshots"
        snap_base.mkdir()
        active_root = snap_base / "repo" / "rev1"
        active_root.mkdir(parents=True)
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active_root)
        config = RunnerConfig(
            strategy_name="test_strategy",
            backend_name="test_backend",
            protocol_version="1.0",
            max_attempts=3,
        )
        runner = BenchmarkRunner(
            strategy=strategy,
            backend=_FakeBackend(),
            isolation=iso,
            config=config,
        )
        scenario = Scenario(
            scenario_id="sc-accept",
            repository="repo",
            change_type="modify",
            blast_radius=BlastRadius.localized,
            requirement_before="before",
            requirement_after="after",
            rationale="test",
            acceptance_criteria=(
                AcceptanceCriterion(description="criterion_a"),
            ),
        )
        runner.run(scenario)
        _repo, change, _universe = strategy.calls[0]
        assert change.acceptance_criteria == ("criterion_a",)

class TestArtifactUniverseConstruction:
    def test_regeneration_uses_actual_snapshot_files(self, tmp_path: Path) -> None:
        strategy = _FakeStrategy()
        ws_root = tmp_path / "workspace"
        ws_root.mkdir(parents=True)
        snap_base = tmp_path / "snapshots"
        snap_base.mkdir()
        active_root = snap_base / "repo" / "v1"
        active_root.mkdir(parents=True)
        (active_root / "src").mkdir()
        (active_root / "src" / "main.py").write_text("")
        (active_root / "src" / "utils.py").write_text("")
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active_root)
        config = RunnerConfig(
            strategy_name="monolithic",
            backend_name="test_backend",
            protocol_version="1.0",
            max_attempts=1,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            editable_artifact_paths=("src/main.py", "src/utils.py"),
        )
        runner = BenchmarkRunner(
            strategy=strategy,
            backend=_FakeBackend(),
            isolation=iso,
            config=config,
        )
        scenario = _make_scenario("sc-001")
        runner.run(scenario)
        assert len(strategy.calls) == 1
        _repo, _change, universe = strategy.calls[0]
        paths = {a.path for a in universe.artifacts}
        assert "src/main.py" in paths
        assert "src/utils.py" in paths

    def test_regeneration_does_not_use_expected_affected_artifacts(self, tmp_path: Path) -> None:
        strategy = _FakeStrategy()
        ws_root = tmp_path / "workspace"
        ws_root.mkdir(parents=True)
        snap_base = tmp_path / "snapshots"
        snap_base.mkdir()
        active_root = snap_base / "repo" / "v1"
        active_root.mkdir(parents=True)
        (active_root / "src").mkdir()
        (active_root / "src" / "actual_a.py").write_text("")
        (active_root / "src" / "actual_b.py").write_text("")
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active_root)
        config = RunnerConfig(
            strategy_name="monolithic",
            backend_name="test_backend",
            protocol_version="1.0",
            max_attempts=1,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            editable_artifact_paths=("src/actual_a.py", "src/actual_b.py"),
        )
        runner = BenchmarkRunner(
            strategy=strategy,
            backend=_FakeBackend(),
            isolation=iso,
            config=config,
        )
        from benchmark.core.enums import ArtifactType
        from benchmark.core.models import ArtifactRef
        gt_artifact = ArtifactRef(path="src/ground_truth_only.py", artifact_type=ArtifactType.source)
        scenario = Scenario(
            scenario_id="sc-001",
            repository="repo",
            change_type="modify",
            blast_radius=BlastRadius.localized,
            requirement_before="before",
            requirement_after="after",
            rationale="test",
            expected_affected_artifacts=(gt_artifact,),
        )
        runner.run(scenario)
        assert len(strategy.calls) == 1
        _repo, _change, universe = strategy.calls[0]
        paths = {a.path for a in universe.artifacts}
        assert "src/actual_a.py" in paths
        assert "src/actual_b.py" in paths
        assert "src/ground_truth_only.py" not in paths

    def test_unrelated_file_appears_in_candidate_universe(self, tmp_path: Path) -> None:
        strategy = _FakeStrategy()
        ws_root = tmp_path / "workspace"
        ws_root.mkdir(parents=True)
        snap_base = tmp_path / "snapshots"
        snap_base.mkdir()
        active_root = snap_base / "repo" / "v1"
        active_root.mkdir(parents=True)
        (active_root / "src").mkdir()
        (active_root / "src" / "actual_a.py").write_text("")
        (active_root / "src" / "actual_b.py").write_text("")
        (active_root / "src" / "unrelated.py").write_text("")
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active_root)
        config = RunnerConfig(
            strategy_name="monolithic",
            backend_name="test_backend",
            protocol_version="1.0",
            max_attempts=1,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            editable_artifact_paths=("src/actual_a.py", "src/actual_b.py", "src/unrelated.py"),
        )
        runner = BenchmarkRunner(
            strategy=strategy,
            backend=_FakeBackend(),
            isolation=iso,
            config=config,
        )
        from benchmark.core.enums import ArtifactType
        from benchmark.core.models import ArtifactRef
        gt_artifact = ArtifactRef(path="src/ground_truth_only.py", artifact_type=ArtifactType.source)
        scenario = Scenario(
            scenario_id="sc-001",
            repository="repo",
            change_type="modify",
            blast_radius=BlastRadius.localized,
            requirement_before="before",
            requirement_after="after",
            rationale="test",
            expected_affected_artifacts=(gt_artifact,),
        )
        runner.run(scenario)
        _repo, _change, universe = strategy.calls[0]
        paths = {a.path for a in universe.artifacts}
        assert "src/actual_a.py" in paths
        assert "src/actual_b.py" in paths
        assert "src/unrelated.py" in paths
        assert "src/ground_truth_only.py" not in paths

    def test_ground_truth_file_absent_from_snapshot_not_in_universe(self, tmp_path: Path) -> None:
        strategy = _FakeStrategy()
        ws_root = tmp_path / "workspace"
        ws_root.mkdir(parents=True)
        snap_base = tmp_path / "snapshots"
        snap_base.mkdir()
        active_root = snap_base / "repo" / "v1"
        active_root.mkdir(parents=True)
        (active_root / "src").mkdir()
        (active_root / "src" / "actual.py").write_text("")
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active_root)
        config = RunnerConfig(
            strategy_name="monolithic",
            backend_name="test_backend",
            protocol_version="1.0",
            max_attempts=1,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            editable_artifact_paths=("src/actual.py",),
        )
        runner = BenchmarkRunner(
            strategy=strategy,
            backend=_FakeBackend(),
            isolation=iso,
            config=config,
        )
        from benchmark.core.enums import ArtifactType
        from benchmark.core.models import ArtifactRef
        gt = ArtifactRef(path="src/only_in_ground_truth.py", artifact_type=ArtifactType.source)
        scenario = Scenario(
            scenario_id="sc-001",
            repository="repo",
            change_type="modify",
            blast_radius=BlastRadius.localized,
            requirement_before="before",
            requirement_after="after",
            rationale="test",
            expected_affected_artifacts=(gt,),
        )
        runner.run(scenario)
        _repo, _change, universe = strategy.calls[0]
        paths = {a.path for a in universe.artifacts}
        assert "src/only_in_ground_truth.py" not in paths
        assert "src/actual.py" in paths

    def test_missing_snapshot_path_fails_closed_when_regeneration_enabled(self, tmp_path: Path) -> None:
        from benchmark.core.exceptions import RepositoryError
        ws_root = tmp_path / "nonexistent_workspace"
        snap_base = tmp_path / "snapshots"
        snap_base.mkdir()
        active_root = snap_base / "repo" / "v1"
        active_root.mkdir(parents=True)
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active_root)
        config = RunnerConfig(
            strategy_name="monolithic",
            backend_name="test_backend",
            protocol_version="1.0",
            max_attempts=1,
            enable_regeneration=True,
        )
        runner = BenchmarkRunner(
            strategy=_FakeStrategy(),
            backend=_FakeBackend(),
            isolation=iso,
            config=config,
        )
        scenario = _make_scenario()
        with pytest.raises(RepositoryError, match="Workspace path does not exist"):
            runner.run(scenario)

    def test_empty_real_snapshot_produces_empty_universe(self, tmp_path: Path) -> None:
        strategy = _FakeStrategy()
        ws_root = tmp_path / "empty_workspace"
        ws_root.mkdir(parents=True)
        snap_base = tmp_path / "snapshots"
        snap_base.mkdir()
        active_root = snap_base / "repo" / "v1"
        active_root.mkdir(parents=True)
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active_root)
        config = RunnerConfig(
            strategy_name="monolithic",
            backend_name="test_backend",
            protocol_version="1.0",
            max_attempts=1,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            editable_artifact_paths=("src/missing.py",),
        )
        runner = BenchmarkRunner(
            strategy=strategy,
            backend=_FakeBackend(),
            isolation=iso,
            config=config,
        )
        scenario = _make_scenario("sc-empty")
        record = runner.run(scenario)
        assert record.status == RunStatus.failed
        messages = " ".join(f.message for f in record.failures)
        assert "does not exist" in messages

    def test_legacy_impact_only_fixture_path_remains_compatible(self, tmp_path: Path) -> None:
        strategy = _FakeStrategy()
        ws_root = tmp_path / "workspace"
        ws_root.mkdir(parents=True)
        snap_base = tmp_path / "snapshots"
        snap_base.mkdir()
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base)
        config = RunnerConfig(
            strategy_name="test_strategy",
            backend_name="test_backend",
            protocol_version="1.0",
            max_attempts=1,
            enable_regeneration=False,
        )
        runner = BenchmarkRunner(
            strategy=strategy,
            backend=_FakeBackend(),
            isolation=iso,
            config=config,
        )
        from benchmark.core.enums import ArtifactType
        from benchmark.core.models import ArtifactRef
        legacy_artifact = ArtifactRef(path="legacy/fixture.py", artifact_type=ArtifactType.source)
        scenario = Scenario(
            scenario_id="sc-legacy",
            repository="repo",
            change_type="modify",
            blast_radius=BlastRadius.localized,
            requirement_before="before",
            requirement_after="after",
            rationale="test",
            expected_affected_artifacts=(legacy_artifact,),
        )
        runner.run(scenario)
        assert len(strategy.calls) == 1
        _repo, _change, universe = strategy.calls[0]
        paths = {a.path for a in universe.artifacts}
        assert "legacy/fixture.py" in paths


class TestSnapshotSourceWorkspaceSeparation:
    def test_source_output_separation(self, tmp_path: Path) -> None:
        strategy = _FakeStrategy()
        ws_root = tmp_path / "workspace"
        ws_root.mkdir(parents=True)
        snap_base = tmp_path / "snapshots"
        snap_base.mkdir()
        active_root = snap_base / "repo" / "v1"
        active_root.mkdir(parents=True)

        (active_root / "src").mkdir(parents=True)
        (active_root / "src" / "source_a.py").write_text("")
        (active_root / "src" / "source_b.py").write_text("")

        (ws_root / "runs").mkdir(parents=True)
        (ws_root / "runs" / "generated.py").write_text("")
        (ws_root / "tmp").mkdir(parents=True)
        (ws_root / "tmp" / "temp.py").write_text("")
        (ws_root / "unrelated_workspace.py").write_text("")

        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active_root)
        config = RunnerConfig(
            strategy_name="monolithic",
            backend_name="test_backend",
            protocol_version="1.0",
            max_attempts=1,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            editable_artifact_paths=("src/source_a.py", "src/source_b.py"),
        )
        runner = BenchmarkRunner(
            strategy=strategy,
            backend=_FakeBackend(),
            isolation=iso,
            config=config,
        )
        from benchmark.core.enums import ArtifactType
        from benchmark.core.models import ArtifactRef
        gt_artifact = ArtifactRef(path="src/ground_truth_only.py", artifact_type=ArtifactType.source)
        scenario = Scenario(
            scenario_id="sc-sep",
            repository="repo",
            change_type="modify",
            blast_radius=BlastRadius.localized,
            requirement_before="before",
            requirement_after="after",
            rationale="test",
            expected_affected_artifacts=(gt_artifact,),
        )
        runner.run(scenario)
        assert len(strategy.calls) == 1
        _repo, _change, universe = strategy.calls[0]
        paths = {a.path for a in universe.artifacts}
        assert "src/source_a.py" in paths
        assert "src/source_b.py" in paths
        assert "runs/generated.py" not in paths
        assert "tmp/temp.py" not in paths
        assert "unrelated_workspace.py" not in paths
        assert "src/ground_truth_only.py" not in paths

    def test_empty_snapshot_produces_empty_universe(self, tmp_path: Path) -> None:
        strategy = _FakeStrategy()
        ws_root = tmp_path / "empty_ws"
        ws_root.mkdir(parents=True)
        snap_base = tmp_path / "empty_snap"
        snap_base.mkdir()
        active_root = snap_base / "repo" / "v1"
        active_root.mkdir(parents=True)
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active_root)
        config = RunnerConfig(
            strategy_name="monolithic",
            backend_name="test_backend",
            protocol_version="1.0",
            max_attempts=1,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            editable_artifact_paths=("src/nonexistent.py",),
        )
        runner = BenchmarkRunner(
            strategy=strategy,
            backend=_FakeBackend(),
            isolation=iso,
            config=config,
        )
        scenario = _make_scenario("sc-empty-snap")
        record = runner.run(scenario)
        assert record.status == RunStatus.failed
        messages = " ".join(f.message for f in record.failures)
        assert "does not exist" in messages

    def test_missing_snapshot_base_fails_closed(self, tmp_path: Path) -> None:
        ws_root = tmp_path / "ws"
        ws_root.mkdir(parents=True)
        snap_base = tmp_path / "nonexistent_snap"
        active_root = snap_base / "repo" / "v1"
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active_root)
        config = RunnerConfig(
            strategy_name="monolithic",
            backend_name="test_backend",
            protocol_version="1.0",
            max_attempts=1,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
        )
        runner = BenchmarkRunner(
            strategy=_FakeStrategy(),
            backend=_FakeBackend(),
            isolation=iso,
            config=config,
        )
        scenario = _make_scenario()
        record = runner.run(scenario)
        assert record.status == RunStatus.failed
        messages = " ".join(f.message for f in record.failures)
        assert "does not exist" in messages or "not a directory" in messages


class TestRepositorySnapshotPathConsistency:
    def test_regeneration_enabled_uses_active_snapshot_path(self, tmp_path: Path) -> None:
        strategy = _FakeStrategy()
        ws_root = tmp_path / "work"
        ws_root.mkdir(parents=True)
        snap_base = tmp_path / "snap"
        snap_base.mkdir()
        active_root = snap_base / "repo" / "v1"
        active_root.mkdir(parents=True)
        (active_root / "src").mkdir()
        (active_root / "src" / "a.py").write_text("")
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active_root)
        config = RunnerConfig(
            strategy_name="monolithic",
            backend_name="test_backend",
            protocol_version="1.0",
            max_attempts=1,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            editable_artifact_paths=("src/a.py",),
        )
        runner = BenchmarkRunner(
            strategy=strategy,
            backend=_FakeBackend(),
            isolation=iso,
            config=config,
        )
        scenario = _make_scenario("sc-path")
        runner.run(scenario)
        assert len(strategy.calls) == 1
        repo, _change, _universe = strategy.calls[0]
        expected = str(active_root.resolve())
        assert Path(repo.path).resolve() == Path(expected).resolve()
        assert repo.path != scenario.repository

    def test_legacy_impact_only_uses_scenario_repository(self, tmp_path: Path) -> None:
        strategy = _FakeStrategy()
        ws_root = tmp_path / "work"
        ws_root.mkdir(parents=True)
        snap_base = tmp_path / "snap"
        snap_base.mkdir()
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base)
        config = RunnerConfig(
            strategy_name="test_strategy",
            backend_name="test_backend",
            protocol_version="1.0",
            max_attempts=1,
            enable_regeneration=False,
        )
        runner = BenchmarkRunner(
            strategy=strategy,
            backend=_FakeBackend(),
            isolation=iso,
            config=config,
        )
        scenario = _make_scenario("sc-legacy-path")
        runner.run(scenario)
        assert len(strategy.calls) == 1
        repo, _change, _universe = strategy.calls[0]
        assert repo.path == scenario.repository


class TestActiveSnapshotFailClosed:
    def test_no_active_snapshot_with_regeneration_fails_closed(self, tmp_path: Path) -> None:
        ws_root = tmp_path / "ws"
        ws_root.mkdir(parents=True)
        snap_base = tmp_path / "snap"
        snap_base.mkdir()
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base)
        config = RunnerConfig(
            strategy_name="monolithic",
            backend_name="test_backend",
            protocol_version="1.0",
            max_attempts=1,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
        )
        runner = BenchmarkRunner(
            strategy=_FakeStrategy(),
            backend=_FakeBackend(),
            isolation=iso,
            config=config,
        )
        scenario = _make_scenario("sc-no-active")
        record = runner.run(scenario)
        assert record.status == RunStatus.failed
        messages = " ".join(f.message for f in record.failures)
        assert "active_snapshot_root" in messages or "active snapshot" in messages.lower()

    def test_active_snapshot_missing_fails_closed(self, tmp_path: Path) -> None:
        ws_root = tmp_path / "ws"
        ws_root.mkdir(parents=True)
        snap_base = tmp_path / "snap"
        snap_base.mkdir()
        missing_active = snap_base / "repo" / "v1"
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=missing_active)
        config = RunnerConfig(
            strategy_name="monolithic",
            backend_name="test_backend",
            protocol_version="1.0",
            max_attempts=1,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
        )
        runner = BenchmarkRunner(
            strategy=_FakeStrategy(),
            backend=_FakeBackend(),
            isolation=iso,
            config=config,
        )
        scenario = _make_scenario("sc-missing-active")
        record = runner.run(scenario)
        assert record.status == RunStatus.failed
        messages = " ".join(f.message for f in record.failures)
        assert "does not exist" in messages or "not a directory" in messages

    def test_empty_active_snapshot_produces_empty_universe(self, tmp_path: Path) -> None:
        strategy = _FakeStrategy()
        ws_root = tmp_path / "ws"
        ws_root.mkdir(parents=True)
        snap_base = tmp_path / "snap"
        snap_base.mkdir()
        active = snap_base / "repo" / "v1"
        active.mkdir(parents=True)
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active)
        config = RunnerConfig(
            strategy_name="monolithic",
            backend_name="test_backend",
            protocol_version="1.0",
            max_attempts=1,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            editable_artifact_paths=("src/nonexistent.py",),
        )
        runner = BenchmarkRunner(
            strategy=strategy,
            backend=_FakeBackend(),
            isolation=iso,
            config=config,
        )
        scenario = _make_scenario("sc-empty-active")
        record = runner.run(scenario)
        assert record.status == RunStatus.failed
        messages = " ".join(f.message for f in record.failures)
        assert "does not exist" in messages

    def test_legacy_impact_only_no_active_snapshot_required(self, tmp_path: Path) -> None:
        strategy = _FakeStrategy()
        ws_root = tmp_path / "ws"
        ws_root.mkdir(parents=True)
        snap_base = tmp_path / "snap"
        snap_base.mkdir()
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base)
        config = RunnerConfig(
            strategy_name="test_strategy",
            backend_name="test_backend",
            protocol_version="1.0",
            max_attempts=1,
            enable_regeneration=False,
        )
        runner = BenchmarkRunner(
            strategy=strategy,
            backend=_FakeBackend(),
            isolation=iso,
            config=config,
        )
        scenario = _make_scenario("sc-legacy-no-active")
        runner.run(scenario)
        assert len(strategy.calls) == 1
        assert len(strategy.calls[0][2].artifacts) == 0


class TestSourceSnapshotImmutability:
    def test_source_and_snapshot_unchanged_after_regeneration(self, tmp_path: Path) -> None:
        from benchmark.core.enums import ArtifactType
        from benchmark.core.models import ArtifactRef, LLMResponse, TokenUsage
        from benchmark.strategies.monolithic import MonolithicRegenerationStrategy

        class _DeterministicBackend:
            async def generate(
                self, prompt: str, temperature: float = 0.0, max_tokens: int = 4096
            ) -> LLMResponse:
                pt = max(1, len(prompt) // 4)
                ct = max(1, len("replacement content") // 4)
                return LLMResponse(
                    text="replacement content",
                    token_usage=TokenUsage(prompt_tokens=pt, completion_tokens=ct, total_tokens=pt + ct),
                    finish_reason="stop",
                )

        artifact = ArtifactRef(path="src/main.py", artifact_type=ArtifactType.source)

        source_repo = tmp_path / "source_repo"
        source_repo.mkdir()
        (source_repo / "src").mkdir()
        (source_repo / "src" / "main.py").write_text("original source", encoding="utf-8")

        storage = tmp_path / "storage"
        storage.mkdir()
        from benchmark.repositories.snapshot import stage_repository_snapshot
        active = stage_repository_snapshot(source_repo, storage, "myrepo", "rev1")

        ws_root = tmp_path / "workspace"
        ws_root.mkdir(parents=True)
        wstarget = ws_root / "src" / "main.py"
        wstarget.parent.mkdir(parents=True)
        wstarget.write_text("original source", encoding="utf-8")

        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=storage, active_snapshot_root=active)
        config = RunnerConfig(
            strategy_name="monolithic",
            backend_name="test_backend",
            protocol_version="1.0",
            max_attempts=1,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            editable_artifact_paths=("src/main.py",),
        )
        runner = BenchmarkRunner(
            strategy=MonolithicRegenerationStrategy(),
            backend=_DeterministicBackend(),
            isolation=iso,
            config=config,
        )
        scenario = Scenario(
            scenario_id="sc-immutable",
            repository="myrepo",
            change_type="modify",
            blast_radius=BlastRadius.localized,
            requirement_before="before",
            requirement_after="after",
            rationale="test",
            expected_affected_artifacts=(artifact,),
        )
        record = runner.run(scenario)

        assert (source_repo / "src/main.py").read_text() == "original source"
        assert (active / "src/main.py").read_text("utf-8") == "original source"
        assert (ws_root / "src/main.py").read_text("utf-8") == "replacement content"
        assert record.regenerated_artifact_count == 1
        assert record.functional_validation_passed is True


class TestMultipleSnapshotIsolation:
    def test_artifact_universe_bound_to_one_active_snapshot(self, tmp_path: Path) -> None:
        strategy = _FakeStrategy()
        ws_root = tmp_path / "ws"
        ws_root.mkdir(parents=True)

        storage = tmp_path / "storage"
        storage.mkdir()
        (storage / "repo_a" / "rev_1" / "src").mkdir(parents=True)
        (storage / "repo_a" / "rev_1" / "src" / "a.py").write_text("")
        (storage / "repo_a" / "rev_1" / "src" / "b.py").write_text("")
        (storage / "repo_b" / "rev_1" / "src").mkdir(parents=True)
        (storage / "repo_b" / "rev_1" / "src" / "c.py").write_text("")

        active = storage / "repo_a" / "rev_1"

        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=storage, active_snapshot_root=active)
        config = RunnerConfig(
            strategy_name="monolithic",
            backend_name="test_backend",
            protocol_version="1.0",
            max_attempts=1,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            editable_artifact_paths=("src/a.py", "src/b.py"),
        )
        runner = BenchmarkRunner(
            strategy=strategy,
            backend=_FakeBackend(),
            isolation=iso,
            config=config,
        )
        scenario = Scenario(
            scenario_id="sc-multi-snap",
            repository="repo_a",
            change_type="modify",
            blast_radius=BlastRadius.localized,
            requirement_before="before",
            requirement_after="after",
            rationale="test",
        )
        runner.run(scenario)
        assert len(strategy.calls) == 1
        _repo, _change, universe = strategy.calls[0]
        paths = {a.path for a in universe.artifacts}
        assert "src/a.py" in paths
        assert "src/b.py" in paths
        assert "src/c.py" not in paths


class TestEditableArtifactUniverse:
    def test_editable_paths_used_when_configured(self, tmp_path: Path) -> None:
        strategy = _FakeStrategy()
        ws_root = tmp_path / "workspace"
        ws_root.mkdir(parents=True)
        snap_base = tmp_path / "snapshots"
        snap_base.mkdir()
        active_root = snap_base / "repo" / "v1"
        active_root.mkdir(parents=True)
        (active_root / "todo").mkdir()
        (active_root / "todo" / "models.py").write_text("")
        (active_root / "todo" / "views.py").write_text("")
        (active_root / "todo" / "tests.py").write_text("")
        (active_root / "manage.py").write_text("")
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active_root)
        config = RunnerConfig(
            strategy_name="selective",
            backend_name="test_backend",
            protocol_version="1.0",
            max_attempts=1,
            enable_regeneration=True,
            validation_command=["python", "-c", "exit(0)"],
            editable_artifact_paths=("todo/models.py", "todo/views.py"),
        )
        runner = BenchmarkRunner(
            strategy=strategy,
            backend=_FakeBackend(),
            isolation=iso,
            config=config,
        )
        scenario = Scenario(
            scenario_id="sc-editable-001",
            repository="repo",
            change_type="modify",
            blast_radius=BlastRadius.localized,
            requirement_before="before",
            requirement_after="after",
            rationale="test",
        )
        runner.run(scenario)
        assert len(strategy.calls) == 1
        _repo, _change, universe = strategy.calls[0]
        paths = {a.path for a in universe.artifacts}
        assert paths == {"todo/models.py", "todo/views.py"}

    def test_editable_excludes_tests_migrations_config(self, tmp_path: Path) -> None:
        strategy = _FakeStrategy()
        ws_root = tmp_path / "workspace"
        ws_root.mkdir(parents=True)
        snap_base = tmp_path / "snapshots"
        snap_base.mkdir()
        active_root = snap_base / "repo" / "v2"
        active_root.mkdir(parents=True)
        (active_root / "todo").mkdir()
        (active_root / "todo" / "models.py").write_text("")
        (active_root / "todo" / "tests.py").write_text("")
        (active_root / "todo" / "migrations").mkdir()
        (active_root / "todo" / "migrations" / "0001.py").write_text("")
        (active_root / "config").mkdir()
        (active_root / "config" / "settings.py").write_text("")
        (active_root / "manage.py").write_text("")
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active_root)
        config = RunnerConfig(
            strategy_name="selective",
            backend_name="test_backend",
            protocol_version="1.0",
            max_attempts=1,
            enable_regeneration=True,
            validation_command=["python", "-c", "exit(0)"],
            editable_artifact_paths=("todo/models.py",),
        )
        runner = BenchmarkRunner(
            strategy=strategy,
            backend=_FakeBackend(),
            isolation=iso,
            config=config,
        )
        scenario = Scenario(
            scenario_id="sc-editable-002",
            repository="repo",
            change_type="modify",
            blast_radius=BlastRadius.localized,
            requirement_before="before",
            requirement_after="after",
            rationale="test",
        )
        runner.run(scenario)
        assert len(strategy.calls) == 1
        _repo, _change, universe = strategy.calls[0]
        paths = {a.path for a in universe.artifacts}
        assert paths == {"todo/models.py"}
        assert "todo/tests.py" not in paths
        assert "todo/migrations/0001.py" not in paths
        assert "config/settings.py" not in paths
        assert "manage.py" not in paths

    def test_editable_paths_skip_gt(self, tmp_path: Path) -> None:
        """Changing scenario.expected_affected_artifacts does not change the universe."""
        strategy = _FakeStrategy()
        ws_root = tmp_path / "workspace"
        ws_root.mkdir(parents=True)
        snap_base = tmp_path / "snapshots"
        snap_base.mkdir()
        active_root = snap_base / "repo" / "v3"
        active_root.mkdir(parents=True)
        (active_root / "todo").mkdir()
        (active_root / "todo" / "models.py").write_text("")
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active_root)
        config = RunnerConfig(
            strategy_name="selective",
            backend_name="test_backend",
            protocol_version="1.0",
            max_attempts=1,
            enable_regeneration=True,
            validation_command=["python", "-c", "exit(0)"],
            editable_artifact_paths=("todo/models.py",),
        )
        runner = BenchmarkRunner(
            strategy=strategy,
            backend=_FakeBackend(),
            isolation=iso,
            config=config,
        )
        from benchmark.core.enums import ArtifactType
        from benchmark.core.models import ArtifactRef
        gt = ArtifactRef(path="todo/gt_only.py", artifact_type=ArtifactType.source)
        scenario = Scenario(
            scenario_id="sc-editable-003",
            repository="repo",
            change_type="modify",
            blast_radius=BlastRadius.localized,
            requirement_before="before",
            requirement_after="after",
            rationale="test",
            expected_affected_artifacts=(gt,),
        )
        runner.run(scenario)
        assert len(strategy.calls) == 1
        _repo, _change, universe = strategy.calls[0]
        paths = {a.path for a in universe.artifacts}
        assert paths == {"todo/models.py"}

    def test_runner_uses_same_resolver_as_production(self, tmp_path: Path) -> None:
        """Runner uses resolve_allowed_artifacts directly (same as CLI)."""
        snap_base = tmp_path / "snap_base"
        snap_base.mkdir(parents=True)
        snap = snap_base / "repo" / "v1"
        snap.mkdir(parents=True)
        todo = snap / "todo"
        todo.mkdir()
        for f in ("models.py", "views.py", "urls.py"):
            (todo / f).write_text("")
        allowed = ("todo/models.py", "todo/views.py", "todo/urls.py")
        direct = resolve_allowed_artifacts(snap, allowed)
        direct_paths = {a.path for a in direct}
        ws_root = tmp_path / "workspace"
        ws_root.mkdir(parents=True)
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=snap)
        config = RunnerConfig(
            strategy_name="selective",
            backend_name="test_backend",
            protocol_version="1.0",
            max_attempts=1,
            enable_regeneration=True,
            validation_command=["python", "-c", "exit(0)"],
            editable_artifact_paths=allowed,
        )
        strategy = _FakeStrategy()
        runner = BenchmarkRunner(
            strategy=strategy,
            backend=_FakeBackend(),
            isolation=iso,
            config=config,
        )
        scenario = Scenario(
            scenario_id="sc-editable-004",
            repository="repo",
            change_type="modify",
            blast_radius=BlastRadius.localized,
            requirement_before="before",
            requirement_after="after",
            rationale="test",
        )
        runner.run(scenario)
        assert len(strategy.calls) == 1
        _repo, _change, universe = strategy.calls[0]
        runner_paths = {a.path for a in universe.artifacts}
        assert runner_paths == direct_paths


class TestClassifyValidationRepairability:
    """R7C-REAL-RUN-ROOT-CLOSURE: infrastructure failures never enter repair."""

    @staticmethod
    def _classify(
        *,
        exit_code: int = 1,
        stdout: str = "",
        stderr: str = "",
        stage: str = "scenario_evaluator",
    ) -> str:
        return BenchmarkRunner.classify_validation_repairability(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            stage=stage,
        )

    def test_missing_module_is_infrastructure_nonrepairable(self) -> None:
        assert (
            self._classify(
                stderr="ModuleNotFoundError: No module named 'django'",
            )
            == "infrastructure_nonrepairable"
        )

    def test_generated_import_error_remains_repairable(self) -> None:
        assert (
            self._classify(stderr="ImportError: cannot import name 'settings'")
            == "repairable_code"
        )

    def test_missing_project_module_remains_repairable(self) -> None:
        assert (
            self._classify(stderr="ModuleNotFoundError: No module named 'todo.missing'")
            == "repairable_code"
        )

    def test_invalid_submodule_of_installed_dependency_is_repairable(self) -> None:
        assert (
            self._classify(
                stderr="ModuleNotFoundError: No module named 'django.nonexistent'"
            )
            == "repairable_code"
        )
        assert (
            self._classify(
                stderr=(
                    "ModuleNotFoundError: No module named "
                    "'rest_framework_simplejwt'"
                )
            )
            == "repairable_code"
        )

    def test_cuda_oom_is_infrastructure_nonrepairable(self) -> None:
        assert (
            self._classify(stderr="CUDA out of memory. Tried to allocate 512.00 MiB")
            == "infrastructure_nonrepairable"
        )

    def test_exit_127_command_not_found_is_infrastructure_nonrepairable(self) -> None:
        assert self._classify(exit_code=127) == "infrastructure_nonrepairable"
        assert (
            self._classify(stderr="command not found: python") == "infrastructure_nonrepairable"
        )

    def test_baseline_validation_assertion_is_repairable_code(self) -> None:
        assert (
            self._classify(stderr="AssertionError: baseline mismatch", stage="baseline_validation")
            == "repairable_code"
        )

    def test_normal_test_failure_is_repairable_code(self) -> None:
        assert (
            self._classify(
                stdout="FAILED tests/test_models.py::test_x",
                stderr="AssertionError: expected 3, got 2",
                stage="scenario_evaluator",
            )
            == "repairable_code"
        )

    def test_empty_feedback_is_repairable_code(self) -> None:
        assert self._classify() == "repairable_code"


class TestRepairEvidencePreservesRootCause:
    """Replay the exact long-traceback failure shape observed on Kaggle."""

    def test_head_tail_compaction_retains_final_exception(self) -> None:
        traceback = (
            "Traceback (most recent call last):\n"
            + "  File \"django/core/management/__init__.py\", line 1\n" * 200
            + "ModuleNotFoundError: No module named 'rest_framework_simplejwt'\n"
        )

        compact = _compact_head_tail(traceback)

        assert "chars omitted" in compact
        assert compact.startswith("Traceback")
        assert compact.rstrip().endswith(
            "ModuleNotFoundError: No module named 'rest_framework_simplejwt'"
        )
        assert _extract_root_cause(compact) == (
            "ModuleNotFoundError: No module named 'rest_framework_simplejwt'"
        )

    def test_repair_context_contains_root_exception_and_scope_failures(
        self, tmp_path: Path
    ) -> None:
        runner = _make_runner(tmp_path)
        traceback = (
            "Traceback (most recent call last):\n"
            + "  File \"django/core/management/__init__.py\", line 1\n" * 200
            + "ModuleNotFoundError: No module named 'rest_framework_simplejwt'\n"
        )
        scientific = _ScientificValidationResult(
            migration=PostGenerationResult(
                passed=False,
                exit_code=1,
                stdout="",
                stderr=traceback,
                duration_seconds=0.5,
            ),
            baseline=None,
            evaluator=None,
            passed=False,
            failed_stage="migration_generation",
            failure_kind=FailureKind.build,
            feedback="migration failed",
            duration_seconds=0.5,
        )
        failures = (
            FailureRecord(
                failure_kind=FailureKind.model_output,
                message=(
                    "out_of_scope_change: todo/permissions.py expected action "
                    "'preserve' but generated output differs"
                ),
                stage="regeneration",
            ),
            FailureRecord(
                failure_kind=FailureKind.model_output,
                message=(
                    "out_of_scope_change: todo/urls.py expected action 'preserve' "
                    "but generated output differs"
                ),
                stage="regeneration",
            ),
        )

        prompt = runner._build_repair_context(scientific, failures)

        assert prompt is not None
        assert "Failed stage: migration_generation" in prompt
        assert (
            "Root cause: ModuleNotFoundError: No module named "
            "'rest_framework_simplejwt'"
        ) in prompt
        assert "todo/permissions.py" in prompt
        assert "todo/urls.py" in prompt
        assert "root exception retained" in prompt


class TestRepairEligibilityUsesCanonicalClassifier:
    """The final repair decision must agree with the canonical classifier."""

    @staticmethod
    def _record(message: str, *, stage: str = "baseline_validation") -> RunRecord:
        return RunRecord(
            identity=RunIdentity(
                run_id="repair-eligibility",
                protocol_version="1.0",
                repository_commit_sha="snapshot",
                scenario_id="scenario",
                strategy_name="monolithic",
            ),
            status=RunStatus.failed,
            failures=(
                FailureRecord(
                    failure_kind=FailureKind.build,
                    message=message,
                    details=message,
                    stage=stage,
                ),
            ),
        )

    @staticmethod
    def _eligible(record: RunRecord) -> bool:
        runner = object.__new__(BenchmarkRunner)
        return runner._is_repairable_failure(record)

    def test_project_local_missing_module_remains_repairable(self) -> None:
        record = self._record("ModuleNotFoundError: No module named 'todo.missing'")
        assert self._eligible(record) is True

    def test_generated_cannot_import_name_remains_repairable(self) -> None:
        record = self._record(
            "ImportError: cannot import name 'Task' from 'todo.models'"
        )
        assert self._eligible(record) is True

    def test_declared_runtime_module_is_not_repairable(self) -> None:
        record = self._record("ModuleNotFoundError: No module named 'django'")
        assert self._eligible(record) is False

    def test_generation_oom_is_not_repairable(self) -> None:
        record = self._record(
            "Qwen generation failed: CUDA out of memory",
            stage="regeneration",
        )
        assert self._eligible(record) is False


class TestBuildScenarioContext:
    """R7C-REAL-RUN-ROOT-CLOSURE: scenario context maps ground-truth actions."""

    def _runner(self, tmp_path: Path) -> BenchmarkRunner:
        ws_root = tmp_path / "ws"
        ws_root.mkdir(parents=True)
        iso = IsolationContext(
            workspace=WorkspacePath(root=str(ws_root)),
            snapshot_base=tmp_path / "snap",
            active_snapshot_root=tmp_path / "active",
        )
        return BenchmarkRunner(
            strategy=_FakeStrategy(),
            backend=_FakeBackend(),
            isolation=iso,
            config=RunnerConfig(
                strategy_name="monolithic",
                backend_name="test_backend",
                protocol_version="1.0",
                max_attempts=1,
                enable_regeneration=True,
                validation_command=[sys.executable, "-c", "exit(0)"],
                editable_artifact_paths=("todo/models.py",),
            ),
        )

    def test_maps_expected_actions(self, tmp_path: Path) -> None:
        runner = self._runner(tmp_path)
        scenario = Scenario(
            scenario_id="todo-smoke-001",
            repository="todo",
            change_type="modify",
            blast_radius=BlastRadius.localized,
            requirement_before="old",
            requirement_after="new",
            rationale="test",
            acceptance_criteria=(AcceptanceCriterion(description="app runs"),),
            architecture_constraints=(ArchitectureConstraint(description="single app"),),
            expected_actions=(
                (ArtifactRef(path="todo/models.py", artifact_type=ArtifactType.source), ActionKind.regenerate),
                (ArtifactRef(path="todo/views.py", artifact_type=ArtifactType.source), ActionKind.preserve),
            ),
            expected_artifact_instructions=(
                ("todo/models.py", "add Task.Priority and priority field"),
            ),
        )
        ctx = runner._build_scenario_context(scenario)
        assert ctx.scenario_id == "todo-smoke-001"
        assert ctx.expected_action_for("todo/models.py") == "modify"
        assert ctx.expected_action_for("todo/views.py") == "preserve"
        assert ctx.acceptance_criteria == ("app runs",)
        assert ctx.architecture_constraints == ("single app",)
        assert ctx.instruction_for("todo/models.py") == (
            "add Task.Priority and priority field"
        )

    def test_empty_expected_actions_yields_empty_contract(self, tmp_path: Path) -> None:
        runner = self._runner(tmp_path)
        scenario = Scenario(
            scenario_id="s",
            repository="repo",
            change_type="modify",
            blast_radius=BlastRadius.localized,
            requirement_before="old",
            requirement_after="new",
            rationale="test",
        )
        ctx = runner._build_scenario_context(scenario)
        assert ctx.expected_actions == ()
        assert ctx.expected_action_for("anything.py") == "preserve"
