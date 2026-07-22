from __future__ import annotations

from benchmark.comparison.aggregator import AggregatedMetrics, AggregatedResult, RepositorySummary, ResultAggregator
from benchmark.comparison.ground_truth import GroundTruthCollection, GroundTruthComparator, GroundTruthEntry
from benchmark.core.enums import ActionKind, ArtifactType
from benchmark.core.models import ArtifactRef, ImpactDecision, ImpactPrediction
from benchmark.evaluation.engine import EvaluationResult


def _make_evaluation_result(
    scenario_id: str = "test-001",
    strategy_name: str = "strategy-a",
    passed: bool = True,
) -> EvaluationResult:
    return EvaluationResult(
        scenario_id=scenario_id,
        strategy_name=strategy_name,
        passed=passed,
        message="Test message",
        metrics=(),
    )


class TestGroundTruthComparator:
    def test_compare_matches_expected(self) -> None:
        comparator = GroundTruthComparator()
        prediction = ImpactPrediction(
            decisions=(
                ImpactDecision(
                    artifact=ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source),
                    action=ActionKind.regenerate,
                    rationale="test",
                ),
            )
        )

        from benchmark.core.models import BlastRadius, Scenario
        scenario = Scenario(
            scenario_id="test-scenario",
            repository="test-repo",
            change_type="test",
            blast_radius=BlastRadius.localized,
            requirement_before="before",
            requirement_after="after",
            rationale="test",
            expected_actions=(
                (ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source), ActionKind.regenerate),
            ),
        )

        result = comparator.compare(prediction, scenario)

        assert len(result.decisions) == 1
        assert result.decisions[0].action == ActionKind.regenerate

    def test_build_from_scenario(self) -> None:
        comparator = GroundTruthComparator()

        from benchmark.core.models import BlastRadius, Scenario
        scenario = Scenario(
            scenario_id="test-scenario",
            repository="test-repo",
            change_type="test",
            blast_radius=BlastRadius.localized,
            requirement_before="before",
            requirement_after="after",
            rationale="test",
            expected_actions=(
                (ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source), ActionKind.regenerate),
                (ArtifactRef(path="src/views.py", artifact_type=ArtifactType.source), ActionKind.preserve),
            ),
        )

        ground_truth = comparator.build_from_scenario(scenario)

        assert len(ground_truth.decisions) == 2

    def test_compute_match_rate(self) -> None:
        comparator = GroundTruthComparator()
        prediction = ImpactPrediction(
            decisions=(
                ImpactDecision(
                    artifact=ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source),
                    action=ActionKind.regenerate,
                    rationale="test",
                ),
            )
        )

        from benchmark.core.models import BlastRadius, Scenario
        scenario = Scenario(
            scenario_id="test-scenario",
            repository="test-repo",
            change_type="test",
            blast_radius=BlastRadius.localized,
            requirement_before="before",
            requirement_after="after",
            rationale="test",
            expected_actions=(
                (ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source), ActionKind.regenerate),
            ),
        )

        rate = comparator.compute_match_rate(prediction, scenario)
        assert rate == 1.0


class TestGroundTruthCollection:
    def test_empty_collection(self) -> None:
        collection = GroundTruthCollection()
        assert collection.entries == ()

    def test_get_for_scenario(self) -> None:
        entry = GroundTruthEntry(
            scenario_id="test-001",
            artifact=ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source),
            expected_action=ActionKind.regenerate,
        )
        collection = GroundTruthCollection(entries=(entry,))

        result = collection.get_for_scenario("test-001")
        assert len(result) == 1
        assert result[0].scenario_id == "test-001"

    def test_duplicate_detection(self) -> None:
        entry1 = GroundTruthEntry(
            scenario_id="test-001",
            artifact=ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source),
            expected_action=ActionKind.regenerate,
        )
        entry2 = GroundTruthEntry(
            scenario_id="test-001",
            artifact=ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source),
            expected_action=ActionKind.preserve,
        )

        try:
            GroundTruthCollection(entries=(entry1, entry2))
            raise AssertionError("Should have raised ValueError for duplicate")
        except ValueError as e:
            assert "Duplicate" in str(e)


class TestResultAggregator:
    def test_add_result(self) -> None:
        aggregator = ResultAggregator()
        result = _make_evaluation_result()

        aggregator.add_result(result)

        assert len(aggregator.results) == 1

    def test_add_results(self) -> None:
        aggregator = ResultAggregator()
        results = [_make_evaluation_result(scenario_id=f"test-{i}") for i in range(3)]

        aggregator.add_results(tuple(results))

        assert len(aggregator.results) == 3

    def test_aggregate_by_strategy(self) -> None:
        aggregator = ResultAggregator()
        aggregator.add_result(_make_evaluation_result(scenario_id="test-001", strategy_name="strategy-a", passed=True))
        aggregator.add_result(_make_evaluation_result(scenario_id="test-002", strategy_name="strategy-a", passed=False))
        aggregator.add_result(_make_evaluation_result(scenario_id="test-003", strategy_name="strategy-b", passed=True))

        aggregated = aggregator.aggregate_by_strategy()

        assert len(aggregated) == 2
        strategy_names = {a.strategy_name for a in aggregated}
        assert "strategy-a" in strategy_names
        assert "strategy-b" in strategy_names

    def test_aggregate_by_repository(self) -> None:
        aggregator = ResultAggregator()
        aggregator.add_result(_make_evaluation_result(scenario_id="repo1-001", strategy_name="strategy-a", passed=True))
        aggregator.add_result(
            _make_evaluation_result(scenario_id="repo1-002", strategy_name="strategy-a", passed=False)
        )

        summary = aggregator.aggregate_by_repository("repo1")

        assert summary.repository == "repo1"
        assert summary.total_runs == 2

    def test_aggregate_all(self) -> None:
        aggregator = ResultAggregator()
        aggregator.add_result(_make_evaluation_result(scenario_id="test-001", strategy_name="strategy-a", passed=True))
        aggregator.add_result(_make_evaluation_result(scenario_id="test-002", strategy_name="strategy-b", passed=False))

        result = aggregator.aggregate_all()

        assert isinstance(result, AggregatedResult)
        assert result.overall_pass_rate == 0.5

    def test_clear(self) -> None:
        aggregator = ResultAggregator()
        aggregator.add_result(_make_evaluation_result())

        aggregator.clear()

        assert len(aggregator.results) == 0


class TestAggregatedMetrics:
    def test_validation(self) -> None:
        metrics = AggregatedMetrics(
            strategy_name="test",
            scenario_id="",
            total_runs=0,
        )
        assert metrics.strategy_name == "test"


class TestRepositorySummary:
    def test_validation(self) -> None:
        summary = RepositorySummary(
            repository="test-repo",
            total_runs=5,
        )
        assert summary.repository == "test-repo"
