from __future__ import annotations

from benchmark.core.enums import ActionKind, ArtifactType, RunStatus
from benchmark.core.models import (
    ArtifactRef,
    ImpactDecision,
    ImpactPrediction,
    RunIdentity,
    RunRecord,
)
from benchmark.evaluation.engine import EvaluationConfig, EvaluationEngine, EvaluationResult


def _make_prediction() -> ImpactPrediction:
    return ImpactPrediction(
        decisions=(
            ImpactDecision(
                artifact=ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source),
                action=ActionKind.regenerate,
                rationale="test",
            ),
            ImpactDecision(
                artifact=ArtifactRef(path="src/views.py", artifact_type=ArtifactType.source),
                action=ActionKind.preserve,
                rationale="test",
            ),
        )
    )


def _make_ground_truth() -> ImpactPrediction:
    return ImpactPrediction(
        decisions=(
            ImpactDecision(
                artifact=ArtifactRef(path="src/models.py", artifact_type=ArtifactType.source),
                action=ActionKind.regenerate,
                rationale="expected",
            ),
            ImpactDecision(
                artifact=ArtifactRef(path="src/views.py", artifact_type=ArtifactType.source),
                action=ActionKind.regenerate,
                rationale="expected",
            ),
        )
    )


def _make_run_record(status: RunStatus = RunStatus.succeeded) -> RunRecord:
    return RunRecord(
        identity=RunIdentity(
            run_id="test-run-1",
            protocol_version="1.0",
            repository_commit_sha="abc123",
            scenario_id="test-scenario-001",
            strategy_name="test-strategy",
        ),
        status=status,
        prediction=_make_prediction(),
        duration_seconds=1.0,
    )


class TestEvaluationEngine:
    def test_evaluate_successful_run(self) -> None:
        engine = EvaluationEngine()
        run_record = _make_run_record()
        ground_truth = _make_ground_truth()

        result = engine.evaluate(run_record, ground_truth)

        assert result.scenario_id == "test-scenario-001"
        assert result.strategy_name == "test-strategy"
        assert len(result.metrics) > 0

    def test_evaluate_failed_run(self) -> None:
        engine = EvaluationEngine()
        from benchmark.core.enums import FailureKind
        from benchmark.core.models import FailureRecord

        failed_record = RunRecord(
            identity=RunIdentity(
                run_id="test-run-2",
                protocol_version="1.0",
                repository_commit_sha="abc123",
                scenario_id="test-scenario-002",
                strategy_name="test-strategy",
            ),
            status=RunStatus.failed,
            failures=(FailureRecord(failure_kind=FailureKind.infrastructure, message="Test failure"),),
        )

        result = engine.evaluate(failed_record, _make_ground_truth())

        assert result.passed is False
        assert "failed" in result.message.lower()

    def test_evaluate_succeeded_no_prediction(self) -> None:
        engine = EvaluationEngine()
        run_record = RunRecord(
            identity=RunIdentity(
                run_id="test-run-3",
                protocol_version="1.0",
                repository_commit_sha="abc123",
                scenario_id="test-scenario-003",
                strategy_name="test-strategy",
            ),
            status=RunStatus.succeeded,
        )

        result = engine.evaluate(run_record, _make_ground_truth())

        assert result.passed is False
        assert "no prediction" in result.message.lower()

    def test_evaluate_non_succeeded_status(self) -> None:
        engine = EvaluationEngine()

        for status in [RunStatus.timed_out, RunStatus.cancelled, RunStatus.failed]:
            run_record = RunRecord(
                identity=RunIdentity(
                    run_id="test-run-4",
                    protocol_version="1.0",
                    repository_commit_sha="abc123",
                    scenario_id="test-scenario-004",
                    strategy_name="test-strategy",
                ),
                status=status,
            )

            result = engine.evaluate(run_record, _make_ground_truth())
            assert result.passed is False


class TestEvaluationResult:
    def test_validation(self) -> None:
        try:
            EvaluationResult(scenario_id="", strategy_name="test")
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert "scenario_id" in str(e)

        try:
            EvaluationResult(scenario_id="test", strategy_name="")
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert "strategy_name" in str(e)


class TestEvaluationConfig:
    def test_defaults(self) -> None:
        config = EvaluationConfig()
        assert config.protocol_version == "1.2"
        assert config.include_secondary is True
        assert config.strict_mode is False

    def test_custom_values(self) -> None:
        config = EvaluationConfig(protocol_version="2.0", include_secondary=False, strict_mode=True)
        assert config.protocol_version == "2.0"
        assert config.include_secondary is False
        assert config.strict_mode is True
