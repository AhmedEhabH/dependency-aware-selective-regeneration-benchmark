from pathlib import Path

from benchmark.core.enums import BlastRadius, RunStatus
from benchmark.core.models import (
    ArtifactUniverse,
    ImpactPrediction,
    LLMResponse,
    RepositorySnapshot,
    RequirementChange,
    Scenario,
)
from benchmark.execution.isolation import IsolationContext
from benchmark.execution.pipeline import BenchmarkPipeline, PipelineConfig
from benchmark.repositories.workspace import WorkspacePath


class _FakeStrategy:
    def analyze_impact(
        self,
        repository: RepositorySnapshot,
        requirement_change: RequirementChange,
        artifact_universe: ArtifactUniverse,
    ) -> ImpactPrediction:
        return ImpactPrediction()


class _FakeBackend:
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        return LLMResponse(text="mock")


class _FakeScenarioProvider:
    def __init__(self) -> None:
        self._scenarios = {
            "s1": Scenario(
                scenario_id="s1", repository="r", change_type="t",
                blast_radius=BlastRadius.localized,
                requirement_before="b", requirement_after="a", rationale="x",
            ),
            "s2": Scenario(
                scenario_id="s2", repository="r", change_type="t",
                blast_radius=BlastRadius.localized,
                requirement_before="b", requirement_after="a", rationale="x",
            ),
        }

    def get_scenario(self, scenario_id: str) -> Scenario:
        return self._scenarios[scenario_id]

    def list_scenarios(self, repo_id: str | None = None) -> list[Scenario]:
        return list(self._scenarios.values())


def _make_pipeline(tmp_path: Path, dry_run: bool = False) -> BenchmarkPipeline:
    ws_root = tmp_path / "workspace"
    ws_root.mkdir()
    snap_base = tmp_path / "snapshots"
    snap_base.mkdir()
    ws = WorkspacePath(root=str(ws_root))
    iso = IsolationContext(workspace=ws, snapshot_base=snap_base)

    config = PipelineConfig(
        protocol_version="1.0",
        dry_run=dry_run,
    )
    return BenchmarkPipeline(
        strategy=_FakeStrategy(),
        backend=_FakeBackend(),
        scenario_provider=_FakeScenarioProvider(),
        isolation=iso,
        config=config,
    )


class TestBenchmarkPipeline:
    def test_run_scenario_dry_run(self, tmp_path: Path) -> None:
        pipeline = _make_pipeline(tmp_path, dry_run=True)
        record = pipeline.run_scenario_by_id("s1")
        assert record.status == RunStatus.succeeded

    def test_run_scenario_by_id(self, tmp_path: Path) -> None:
        pipeline = _make_pipeline(tmp_path, dry_run=True)
        record = pipeline.run_scenario_by_id("s1")
        assert record.identity.scenario_id == "s1"

    def test_run_all_dry_run(self, tmp_path: Path) -> None:
        pipeline = _make_pipeline(tmp_path, dry_run=True)
        result = pipeline.run_all()
        assert result.success_count == 2
        assert result.total_duration == 0.0

    def test_run_all_with_ids(self, tmp_path: Path) -> None:
        pipeline = _make_pipeline(tmp_path, dry_run=True)
        result = pipeline.run_all(scenario_ids=["s1"])
        assert result.success_count == 1

    def test_pipeline_result_tracks_failures(self, tmp_path: Path) -> None:
        ws = WorkspacePath(root=str(tmp_path))
        iso = IsolationContext(workspace=ws)
        config = PipelineConfig(protocol_version="1.0")
        pipeline = BenchmarkPipeline(
            strategy=_FakeStrategy(),
            backend=_FakeBackend(),
            scenario_provider=_FakeScenarioProvider(),
            isolation=iso,
            config=config,
        )
        result = pipeline.run_all(scenario_ids=["s1"])
        assert result.failure_count > 0

    def test_run_scenario_non_dry(self, tmp_path: Path) -> None:
        pipeline = _make_pipeline(tmp_path)
        record = pipeline.run_scenario_by_id("s2")
        assert isinstance(record.status, RunStatus)
