import sys
from pathlib import Path

import pytest

from benchmark.core.enums import BlastRadius, RunStatus
from benchmark.core.models import (
    ArtifactUniverse,
    ImpactPrediction,
    LLMResponse,
    RepositorySnapshot,
    RequirementChange,
    RunRecord,
    Scenario,
)
from benchmark.execution.isolation import IsolationContext
from benchmark.execution.runner import BenchmarkRunner, RunnerConfig
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
    ws = WorkspacePath(root=str(ws_root))
    iso = IsolationContext(workspace=ws, snapshot_base=snap_base)

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
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base)
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


class TestArtifactUniverseConstruction:
    def test_regeneration_uses_actual_snapshot_files(self, tmp_path: Path) -> None:
        strategy = _FakeStrategy()
        ws_root = tmp_path / "workspace"
        ws_root.mkdir(parents=True)
        (ws_root / "src").mkdir()
        (ws_root / "src" / "main.py").write_text("")
        (ws_root / "src" / "utils.py").write_text("")
        snap_base = tmp_path / "snapshots"
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
        (ws_root / "src").mkdir()
        (ws_root / "src" / "actual_a.py").write_text("")
        (ws_root / "src" / "actual_b.py").write_text("")
        snap_base = tmp_path / "snapshots"
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
        (ws_root / "src").mkdir()
        (ws_root / "src" / "actual_a.py").write_text("")
        (ws_root / "src" / "actual_b.py").write_text("")
        (ws_root / "src" / "unrelated.py").write_text("")
        snap_base = tmp_path / "snapshots"
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
        (ws_root / "src").mkdir()
        (ws_root / "src" / "actual.py").write_text("")
        snap_base = tmp_path / "snapshots"
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
        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(workspace=ws, snapshot_base=snap_base)
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
            strategy=strategy,
            backend=_FakeBackend(),
            isolation=iso,
            config=config,
        )
        scenario = _make_scenario("sc-empty")
        runner.run(scenario)
        assert len(strategy.calls) == 1
        _repo, _change, universe = strategy.calls[0]
        assert len(universe.artifacts) == 0

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
