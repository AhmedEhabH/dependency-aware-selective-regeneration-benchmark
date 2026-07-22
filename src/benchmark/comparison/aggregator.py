from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from benchmark.core.models import RunRecord
from benchmark.evaluation.engine import EvaluationResult


@dataclass(frozen=True)
class AggregatedMetrics:
    strategy_name: str
    scenario_id: str
    metrics: dict[str, float | None] = field(default_factory=dict)
    total_runs: int = 0
    passed_runs: int = 0
    failed_runs: int = 0


@dataclass(frozen=True)
class RepositorySummary:
    repository: str
    strategy_results: tuple[EvaluationResult, ...] = ()
    total_runs: int = 0
    passed_runs: int = 0
    failed_runs: int = 0


@dataclass(frozen=True)
class AggregatedResult:
    strategies: tuple[AggregatedMetrics, ...] = ()
    repositories: tuple[RepositorySummary, ...] = ()
    overall_pass_rate: float = 0.0
    overall_fail_rate: float = 0.0


class ResultAggregator:
    def __init__(self) -> None:
        self._results: list[EvaluationResult] = []

    def add_result(self, result: EvaluationResult) -> None:
        self._results.append(result)

    def add_results(self, results: tuple[EvaluationResult, ...]) -> None:
        self._results.extend(results)

    def aggregate_by_strategy(self) -> tuple[AggregatedMetrics, ...]:
        strategy_data: dict[str, list[EvaluationResult]] = defaultdict(list)

        for result in self._results:
            strategy_data[result.strategy_name].append(result)

        aggregated: list[AggregatedMetrics] = []
        for strategy_name, results in strategy_data.items():
            passed = sum(1 for r in results if r.passed)
            failed = sum(1 for r in results if not r.passed)

            metric_values: dict[str, list[float]] = defaultdict(list)
            for r in results:
                for m in r.metrics:
                    if m.value is not None:
                        metric_values[m.name].append(m.value)

            avg_metrics: dict[str, float | None] = {}
            for name, values in metric_values.items():
                if values:
                    avg_metrics[name] = sum(values) / len(values)
                else:
                    avg_metrics[name] = None

            aggregated.append(
                AggregatedMetrics(
                    strategy_name=strategy_name,
                    scenario_id="",
                    metrics=avg_metrics,
                    total_runs=len(results),
                    passed_runs=passed,
                    failed_runs=failed,
                )
            )

        return tuple(aggregated)

    def aggregate_by_repository(self, repository: str) -> RepositorySummary:
        repo_results = [r for r in self._results if repository in r.scenario_id]
        passed = sum(1 for r in repo_results if r.passed)
        failed = sum(1 for r in repo_results if not r.passed)

        return RepositorySummary(
            repository=repository,
            strategy_results=tuple(repo_results),
            total_runs=len(repo_results),
            passed_runs=passed,
            failed_runs=failed,
        )

    def aggregate_all(self) -> AggregatedResult:
        all_results = self._results
        total = len(all_results)
        passed = sum(1 for r in all_results if r.passed)
        failed = sum(1 for r in all_results if not r.passed)

        by_strategy = self.aggregate_by_strategy()
        repositories = self._aggregate_repositories()

        return AggregatedResult(
            strategies=by_strategy,
            repositories=repositories,
            overall_pass_rate=passed / total if total > 0 else 0.0,
            overall_fail_rate=failed / total if total > 0 else 0.0,
        )

    def _aggregate_repositories(self) -> tuple[RepositorySummary, ...]:
        repo_data: dict[str, list[EvaluationResult]] = defaultdict(list)

        for result in self._results:
            repo = result.scenario_id.rsplit("-", 2)[0] if "-" in result.scenario_id else result.scenario_id
            repo_data[repo].append(result)

        summaries: list[RepositorySummary] = []
        for repo, results in repo_data.items():
            passed = sum(1 for r in results if r.passed)
            failed = sum(1 for r in results if not r.passed)

            summaries.append(
                RepositorySummary(
                    repository=repo,
                    strategy_results=tuple(results),
                    total_runs=len(results),
                    passed_runs=passed,
                    failed_runs=failed,
                )
            )

        return tuple(summaries)

    def clear(self) -> None:
        self._results.clear()

    @property
    def results(self) -> tuple[EvaluationResult, ...]:
        return tuple(self._results)


def aggregate_run_records(
    records: tuple[RunRecord, ...],
) -> AggregatedResult:
    from benchmark.core.enums import RunStatus

    aggregator = ResultAggregator()
    for record in records:
        if record.status == RunStatus.succeeded and record.prediction:
            result = EvaluationResult(
                scenario_id=record.identity.scenario_id,
                strategy_name=record.identity.strategy_name,
                metrics=(),
                passed=True,
                message="",
            )
            aggregator.add_result(result)
    return aggregator.aggregate_all()
