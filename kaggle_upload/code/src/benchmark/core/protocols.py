from __future__ import annotations

from typing import Protocol, runtime_checkable

from benchmark.core.models import (
    AnalysisReport,
    ArtifactUniverse,
    DependencyGraph,
    ImpactPrediction,
    LLMResponse,
    ProvenanceEvent,
    RepositorySnapshot,
    RequirementChange,
    RunRecord,
    Scenario,
    ValidationReport,
)


@runtime_checkable
class ImpactStrategy(Protocol):
    def analyze_impact(
        self,
        repository: RepositorySnapshot,
        requirement_change: RequirementChange,
        artifact_universe: ArtifactUniverse,
    ) -> ImpactPrediction:
        ...


@runtime_checkable
class LLMBackend(Protocol):
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        ...


@runtime_checkable
class RepositoryAdapter(Protocol):
    def clone(self, url: str, ref: str) -> RepositorySnapshot:
        ...

    def checkout(self, sha: str) -> None:
        ...

    def run_tests(self, paths: list[str]) -> dict[str, bool]:
        ...


@runtime_checkable
class ScenarioProvider(Protocol):
    def get_scenario(self, scenario_id: str) -> Scenario:
        ...

    def list_scenarios(self, repo_id: str | None = None) -> list[Scenario]:
        ...


@runtime_checkable
class DependencyExtractor(Protocol):
    def build_graph(self, snapshot: RepositorySnapshot) -> DependencyGraph:
        ...


@runtime_checkable
class ExecutionRunner(Protocol):
    def run_strategy(
        self,
        strategy: ImpactStrategy,
        scenario: Scenario,
    ) -> RunRecord:
        ...


@runtime_checkable
class Validator(Protocol):
    def validate(self, snapshot: RepositorySnapshot, result: RunRecord) -> ValidationReport:
        ...


@runtime_checkable
class Metric(Protocol):
    name: str

    def compute(
        self,
        prediction: ImpactPrediction,
        ground_truth: ImpactPrediction,
    ) -> float:
        ...


@runtime_checkable
class StatisticsAnalyzer(Protocol):
    def analyze(self, results: list[RunRecord]) -> AnalysisReport:
        ...


@runtime_checkable
class ResultWriter(Protocol):
    def write_run(self, record: RunRecord) -> None:
        ...


@runtime_checkable
class ProvenanceRecorder(Protocol):
    def record(self, event: ProvenanceEvent) -> None:
        ...
