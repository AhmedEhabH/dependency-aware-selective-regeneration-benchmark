from pathlib import Path

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
        iso = IsolationContext(workspace=ws)
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
