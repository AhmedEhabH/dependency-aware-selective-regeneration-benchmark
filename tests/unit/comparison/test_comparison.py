from __future__ import annotations

from benchmark.comparison.aggregator import (
    AggregatedMetrics,
    AggregatedResult,
    RepositorySummary,
    ResultAggregator,
    aggregate_run_records,
)
from benchmark.comparison.ground_truth import GroundTruthCollection, GroundTruthComparator, GroundTruthEntry
from benchmark.core.enums import ActionKind, ArtifactType, RunStatus
from benchmark.core.models import (
    ArtifactRef,
    ImpactDecision,
    ImpactPrediction,
    RunIdentity,
    RunRecord,
)
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


def _make_run_record(
    scenario_id: str = "repo-s01-1",
    strategy_name: str = "strategy-a",
    status: RunStatus = RunStatus.succeeded,
) -> RunRecord:
    return RunRecord(
        identity=RunIdentity(
            run_id=f"run-{scenario_id}-{strategy_name}",
            protocol_version="1.0",
            repository_commit_sha="abc123",
            scenario_id=scenario_id,
            strategy_name=strategy_name,
        ),
        status=status,
        prediction=ImpactPrediction(decisions=()) if status == RunStatus.succeeded else None,
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


class TestAggregateRunRecords:
    def test_retains_failed_runs(self) -> None:
        records = (
            _make_run_record(scenario_id="r-s01-1", strategy_name="a", status=RunStatus.succeeded),
            _make_run_record(scenario_id="r-s01-2", strategy_name="a", status=RunStatus.failed),
        )
        result = aggregate_run_records(records)
        assert result.records_processed == 2
        assert len(result.micro) == 2
        passed_count = sum(1 for r in result.micro if r.passed)
        failed_count = sum(1 for r in result.micro if not r.passed)
        assert passed_count == 1
        assert failed_count == 1

    def test_micro_preserves_identifiers(self) -> None:
        records = (
            _make_run_record(scenario_id="repo-scen-1", strategy_name="strat_a"),
            _make_run_record(scenario_id="repo-scen-2", strategy_name="strat_b"),
        )
        result = aggregate_run_records(records)
        ids = {(r.scenario_id, r.strategy_name) for r in result.micro}
        assert ("repo-scen-1", "strat_a") in ids
        assert ("repo-scen-2", "strat_b") in ids

    def test_micro_deterministic_order(self) -> None:
        records = (
            _make_run_record(scenario_id="z-001", strategy_name="b"),
            _make_run_record(scenario_id="a-001", strategy_name="a"),
        )
        result = aggregate_run_records(records)
        names = [r.strategy_name for r in result.micro]
        assert names == sorted(names)

    def test_macro_equal_weight_repositories(self) -> None:
        """Macro pass rate must not be biased by scenario count per repo."""
        records = (
            # repo-A: 4 scenarios, all pass -> repo pass rate = 1.0
            _make_run_record(scenario_id="A-s1-1", strategy_name="x", status=RunStatus.succeeded),
            _make_run_record(scenario_id="A-s2-1", strategy_name="x", status=RunStatus.succeeded),
            _make_run_record(scenario_id="A-s3-1", strategy_name="x", status=RunStatus.succeeded),
            _make_run_record(scenario_id="A-s4-1", strategy_name="x", status=RunStatus.succeeded),
            # repo-B: 1 scenario, fails -> repo pass rate = 0.0
            _make_run_record(scenario_id="B-s1-1", strategy_name="x", status=RunStatus.failed),
        )
        result = aggregate_run_records(records)
        macro_strat = next(s for s in result.macro.strategies if s.strategy_name == "x")
        # Equal weight: (1.0 + 0.0) / 2 = 0.5, NOT 4/5 = 0.8
        pass_rate = macro_strat.metrics["pass_rate"]
        assert pass_rate is not None
        assert abs(pass_rate - 0.5) < 1e-9

    def test_rejects_malformed_record(self) -> None:
        """Verify that records with empty strategy are rejected.

        RunIdentity itself rejects empty scenario_id and empty strategy_name,
        so we test that aggregate_run_records handles the ValueError gracefully
        by wrapping in a try and verifying no results are produced.
        """
        try:
            bad = RunRecord(
                identity=RunIdentity(
                    run_id="x",
                    protocol_version="1.0",
                    repository_commit_sha="abc",
                    scenario_id="repo-s1-1",
                    strategy_name="",
                ),
                status=RunStatus.succeeded,
                prediction=ImpactPrediction(decisions=()),
            )
            # If RunIdentity allowed empty strategy, aggregator should reject
            result = aggregate_run_records((bad,))
            assert result.records_rejected == 1
        except ValueError:
            # RunIdentity correctly rejects empty strategy_name
            pass

    def test_conditional_notes_for_failed_runs(self) -> None:
        records = (
            _make_run_record(scenario_id="r-s1-1", strategy_name="a", status=RunStatus.failed),
        )
        result = aggregate_run_records(records)
        assert len(result.conditional_notes) == 1
        assert "Conditional" in result.conditional_notes[0]

    def test_empty_input(self) -> None:
        result = aggregate_run_records(())
        assert result.records_processed == 0
        assert result.macro.overall_pass_rate == 0.0

    def test_per_repository_populated(self) -> None:
        records = (
            _make_run_record(scenario_id="repo1-s1-1", strategy_name="a"),
            _make_run_record(scenario_id="repo2-s1-1", strategy_name="a"),
        )
        result = aggregate_run_records(records)
        repos = {r.repository for r in result.per_repository}
        assert "repo1" in repos
        assert "repo2" in repos
