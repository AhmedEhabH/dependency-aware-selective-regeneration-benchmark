

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
    TokenUsage,
    ValidationReport,
)
from benchmark.core.protocols import (
    DependencyExtractor,
    ExecutionRunner,
    ImpactStrategy,
    LLMBackend,
    Metric,
    ProvenanceRecorder,
    RepositoryAdapter,
    ResultWriter,
    ScenarioProvider,
    StatisticsAnalyzer,
    Validator,
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
    async def generate(self, prompt: str, temperature: float = 0.0, max_tokens: int = 4096) -> LLMResponse:
        usage = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        return LLMResponse(text="mock response", token_usage=usage)


class FakeRepositoryAdapter:
    def clone(self, url: str, ref: str) -> RepositorySnapshot:
        from benchmark.core.models import RepositoryIdentity
        ri = RepositoryIdentity(name="fake", url=url)
        return RepositorySnapshot(identity=ri, commit_sha="abc123", path="/tmp/fake")
    def checkout(self, sha: str) -> None:
        pass
    def run_tests(self, paths: list[str]) -> dict[str, bool]:
        return {}


class FakeScenarioProvider:
    def get_scenario(self, scenario_id: str) -> Scenario:
        from benchmark.core.enums import BlastRadius
        return Scenario(scenario_id=scenario_id, repository="r", change_type="t",
                        blast_radius=BlastRadius.localized, requirement_before="b",
                        requirement_after="a", rationale="x")
    def list_scenarios(self, repo_id: str | None = None) -> list[Scenario]:
        return [self.get_scenario("s1")]


class FakeDependencyExtractor:
    def build_graph(self, snapshot: RepositorySnapshot) -> DependencyGraph:
        return DependencyGraph()


class FakeExecutionRunner:
    def run_strategy(self, strategy: ImpactStrategy, scenario: Scenario) -> RunRecord:
        from benchmark.core.enums import RunStatus
        from benchmark.core.models import RunIdentity
        identity = RunIdentity(run_id="r1", protocol_version="1.0", repository_commit_sha="a",
                                scenario_id=scenario.scenario_id, strategy_name="fake")
        return RunRecord(identity=identity, status=RunStatus.succeeded)


class FakeValidator:
    def validate(self, snapshot: RepositorySnapshot, result: RunRecord) -> ValidationReport:
        from benchmark.core.models import ValidationCheck
        return ValidationReport(
            run_identity=result.identity,
            checks=(ValidationCheck(name="check1", passed=True),),
            passed=True,
        )


class FakeMetric:
    name: str = "fake_metric"
    def compute(self, prediction: ImpactPrediction, ground_truth: ImpactPrediction) -> float:
        return 1.0


class FakeStatisticsAnalyzer:
    def analyze(self, results: list[RunRecord]) -> AnalysisReport:
        from benchmark.core.models import MetricValue
        return AnalysisReport(title="fake", metrics=(MetricValue(name="m1", value=0.5),))


class FakeResultWriter:
    def write_run(self, record: RunRecord) -> None:
        pass


class FakeProvenanceRecorder:
    def record(self, event: ProvenanceEvent) -> None:
        pass


class TestProtocolStructuralConformance:
    def test_impact_strategy(self) -> None:
        impl: ImpactStrategy = FakeStrategy()
        assert isinstance(impl, ImpactStrategy)
        pred = impl.analyze_impact(
            repository=FakeRepositoryAdapter().clone("url", "ref"),
            requirement_change=RequirementChange(before="old", after="new"),
            artifact_universe=ArtifactUniverse(),
        )
        assert isinstance(pred, ImpactPrediction)

    def test_llm_backend(self) -> None:
        impl: LLMBackend = FakeLLMBackend()
        assert isinstance(impl, LLMBackend)

    def test_repository_adapter(self) -> None:
        impl: RepositoryAdapter = FakeRepositoryAdapter()
        assert isinstance(impl, RepositoryAdapter)
        snapshot = impl.clone("url", "ref")
        assert isinstance(snapshot, RepositorySnapshot)

    def test_scenario_provider(self) -> None:
        impl: ScenarioProvider = FakeScenarioProvider()
        assert isinstance(impl, ScenarioProvider)
        scenario = impl.get_scenario("s1")
        assert isinstance(scenario, Scenario)

    def test_dependency_extractor(self) -> None:
        impl: DependencyExtractor = FakeDependencyExtractor()
        assert isinstance(impl, DependencyExtractor)

    def test_execution_runner(self) -> None:
        impl: ExecutionRunner = FakeExecutionRunner()
        assert isinstance(impl, ExecutionRunner)

    def test_validator(self) -> None:
        impl: Validator = FakeValidator()
        assert isinstance(impl, Validator)

    def test_metric(self) -> None:
        impl: Metric = FakeMetric()
        assert isinstance(impl, Metric)
        assert impl.name == "fake_metric"

    def test_statistics_analyzer(self) -> None:
        impl: StatisticsAnalyzer = FakeStatisticsAnalyzer()
        assert isinstance(impl, StatisticsAnalyzer)

    def test_result_writer(self) -> None:
        impl: ResultWriter = FakeResultWriter()
        assert isinstance(impl, ResultWriter)

    def test_provenance_recorder(self) -> None:
        impl: ProvenanceRecorder = FakeProvenanceRecorder()
        assert isinstance(impl, ProvenanceRecorder)
