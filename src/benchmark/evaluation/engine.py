from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from benchmark.core.models import ImpactPrediction, RunRecord
from benchmark.evaluation.metrics import MetricComputer, MetricResult

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class EvaluationResult:
    scenario_id: str
    strategy_name: str
    metrics: tuple[MetricResult, ...] = ()
    passed: bool = False
    message: str = ""

    def __post_init__(self) -> None:
        if not self.scenario_id:
            raise ValueError("EvaluationResult.scenario_id must not be empty")
        if not self.strategy_name:
            raise ValueError("EvaluationResult.strategy_name must not be empty")


@dataclass
class EvaluationConfig:
    protocol_version: str = "1.1"
    include_secondary: bool = True
    strict_mode: bool = False


class EvaluationEngine:
    def __init__(self, config: EvaluationConfig | None = None) -> None:
        self._config = config or EvaluationConfig()
        self._metric_computer = MetricComputer(include_secondary=self._config.include_secondary)

    def evaluate(
        self,
        run_record: RunRecord,
        ground_truth: ImpactPrediction,
    ) -> EvaluationResult:
        from benchmark.core.enums import RunStatus

        if run_record.status == RunStatus.succeeded:
            prediction = run_record.prediction
            if prediction is None:
                return EvaluationResult(
                    scenario_id=run_record.identity.scenario_id,
                    strategy_name=run_record.identity.strategy_name,
                    passed=False,
                    message="Run succeeded but no prediction available",
                )
        elif run_record.status == RunStatus.failed:
            return EvaluationResult(
                scenario_id=run_record.identity.scenario_id,
                strategy_name=run_record.identity.strategy_name,
                passed=False,
                message=f"Run failed: {run_record.failures}",
            )
        else:
            return EvaluationResult(
                scenario_id=run_record.identity.scenario_id,
                strategy_name=run_record.identity.strategy_name,
                passed=False,
                message=f"Run did not succeed (status: {run_record.status})",
            )

        metrics = self._metric_computer.compute_all(prediction, ground_truth)

        passed = self._determine_passed(metrics)
        message = self._build_message(metrics, passed)

        return EvaluationResult(
            scenario_id=run_record.identity.scenario_id,
            strategy_name=run_record.identity.strategy_name,
            metrics=metrics,
            passed=passed,
            message=message,
        )

    def _determine_passed(self, metrics: tuple[MetricResult, ...]) -> bool:
        thresholds = {"recall": 0.8, "precision": 0.8, "action_accuracy": 0.9}
        for metric in metrics:
            if metric.name in thresholds and metric.value is not None and metric.value < thresholds[metric.name]:
                return False
        return True

    def _build_message(self, metrics: tuple[MetricResult, ...], passed: bool) -> str:
        metric_strs = [f"{m.name}={m.value:.4f}" if m.value is not None else f"{m.name}=N/A" for m in metrics]
        status = "PASSED" if passed else "FAILED"
        return f"Evaluation {status}: {', '.join(metric_strs)}"
