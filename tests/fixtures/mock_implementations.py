"""Shared mock implementations for protocol conformance testing.

These are simple fakes that satisfy the protocol interfaces defined in
benchmark.core.protocols. They do not perform real operations.
"""

from benchmark.core.enums import BlastRadius, RunStatus
from benchmark.core.models import (
    AnalysisReport,
    ArtifactUniverse,
    DependencyGraph,
    ImpactPrediction,
    LLMResponse,
    MetricValue,
    ProvenanceEvent,
    RepositoryIdentity,
    RepositorySnapshot,
    RequirementChange,
    RunIdentity,
    RunRecord,
    Scenario,
    TokenUsage,
    ValidationCheck,
    ValidationReport,
)


class FakeStrategy:
    def analyze_impact(
        self,
        repository: RepositorySnapshot,
        requirement_change: RequirementChange,
        artifact_universe: ArtifactUniverse,
    ) -> ImpactPrediction:
        return ImpactPrediction()


class FakeLLMBackend:
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        return LLMResponse(
            text="mock",
            token_usage=TokenUsage(prompt_tokens=5, completion_tokens=5, total_tokens=10),
        )


class FakeRepositoryAdapter:
    def clone(self, url: str, ref: str) -> RepositorySnapshot:
        return RepositorySnapshot(
            identity=RepositoryIdentity(name="fake", url=url),
            commit_sha="abc123",
            path="/tmp/fake",
        )

    def checkout(self, sha: str) -> None:
        pass

    def run_tests(self, paths: list[str]) -> dict[str, bool]:
        return {}


class FakeScenarioProvider:
    def get_scenario(self, scenario_id: str) -> Scenario:
        return Scenario(
            scenario_id=scenario_id,
            repository="r",
            change_type="t",
            blast_radius=BlastRadius.localized,
            requirement_before="before",
            requirement_after="after",
            rationale="test",
        )

    def list_scenarios(self, repo_id: str | None = None) -> list[Scenario]:
        return [self.get_scenario("s1")]


class FakeDependencyExtractor:
    def build_graph(self, snapshot: RepositorySnapshot) -> DependencyGraph:
        return DependencyGraph()


class FakeExecutionRunner:
    def run_strategy(self, strategy: object, scenario: Scenario) -> RunRecord:
        identity = RunIdentity(
            run_id="r1",
            protocol_version="1.0",
            repository_commit_sha="a",
            scenario_id=scenario.scenario_id,
            strategy_name="fake",
        )
        return RunRecord(identity=identity, status=RunStatus.succeeded)


class FakeValidator:
    def validate(self, snapshot: RepositorySnapshot, result: RunRecord) -> ValidationReport:
        return ValidationReport(
            run_identity=result.identity,
            checks=(ValidationCheck(name="c1", passed=True),),
            passed=True,
        )


class FakeMetric:
    name: str = "fake_metric"

    def compute(self, prediction: ImpactPrediction, ground_truth: ImpactPrediction) -> float:
        return 1.0


class FakeStatisticsAnalyzer:
    def analyze(self, results: list[RunRecord]) -> AnalysisReport:
        return AnalysisReport(
            title="fake",
            metrics=(MetricValue(name="m1", value=0.5),),
        )


class FakeResultWriter:
    def write_run(self, record: RunRecord) -> None:
        pass


class FakeProvenanceRecorder:
    def record(self, event: ProvenanceEvent) -> None:
        pass
