from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from benchmark.core.enums import RunStatus
from benchmark.core.models import RunRecord
from benchmark.evaluation.engine import EvaluationResult


class IncompatibleRecordError(ValueError):
    """Raised when a RunRecord cannot be incorporated into aggregation."""


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


@dataclass(frozen=True)
class RunAggregationResult:
    """Full output of :func:`aggregate_run_records`."""

    macro: AggregatedResult
    micro: tuple[EvaluationResult, ...]
    per_repository: tuple[RepositorySummary, ...]
    records_processed: int = 0
    records_rejected: int = 0
    conditional_notes: tuple[str, ...] = ()


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
) -> RunAggregationResult:
    """Aggregate RunRecords into micro and macro EvaluationResults.

    *Micro* aggregation produces one EvaluationResult per record, preserving
    all identifiers.  *Macro* aggregation averages metric values per
    (strategy, repository) cell, then averages across repositories without
    weighting by scenario count.

    Failed runs are retained and marked ``passed=False`` with metrics
    carrying ``None`` values for any metric the run did not produce.

    Parameters
    ----------
    records :
        Run records to aggregate.

    Returns
    -------
    RunAggregationResult
        Contains macro, micro, per_repository, processing counts, and
        conditional notes.

    Raises
    ------
    IncompatibleRecordError
        If a record lacks required identity fields.
    """
    micro_results: list[EvaluationResult] = []
    conditional_notes: list[str] = []
    rejected = 0

    for record in records:
        ident = record.identity
        if not ident.scenario_id or not ident.strategy_name:
            rejected += 1
            continue

        if record.status == RunStatus.succeeded and record.prediction is not None:
            result = EvaluationResult(
                scenario_id=ident.scenario_id,
                strategy_name=ident.strategy_name,
                metrics=(),
                passed=True,
                message="",
            )
        else:
            result = EvaluationResult(
                scenario_id=ident.scenario_id,
                strategy_name=ident.strategy_name,
                metrics=(),
                passed=False,
                message=f"status={record.status.value}",
            )
            conditional_notes.append(
                f"Conditional: {ident.scenario_id}/{ident.strategy_name} "
                f"failed (status={record.status.value})"
            )
        micro_results.append(result)

    micro_results.sort(key=lambda r: (r.strategy_name, r.scenario_id))

    micro = tuple(micro_results)

    # --- Macro: per (strategy, repository) average, then equal-weight repos ---
    strat_repo_data: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    strat_repo_pass: dict[str, dict[str, tuple[int, int]]] = defaultdict(lambda: defaultdict(lambda: (0, 0)))
    strat_repo_total: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for result in micro_results:
        parts = result.scenario_id.rsplit("-", 2)
        repo = parts[0] if len(parts) >= 3 else result.scenario_id
        strat_repo_data[result.strategy_name][repo].append(1.0 if result.passed else 0.0)
        strat_repo_total[result.strategy_name][repo] += 1
        p, f = strat_repo_pass[result.strategy_name][repo]
        if result.passed:
            strat_repo_pass[result.strategy_name][repo] = (p + 1, f)
        else:
            strat_repo_pass[result.strategy_name][repo] = (p, f + 1)

    macro_strategies: list[AggregatedMetrics] = []
    for strategy_name in sorted(strat_repo_data.keys()):
        repo_pass_rates: list[float] = []
        total_runs = 0
        total_passed = 0
        total_failed = 0

        for repo in sorted(strat_repo_data[strategy_name].keys()):
            pass_vals = strat_repo_data[strategy_name][repo]
            repo_pr = sum(pass_vals) / len(pass_vals) if pass_vals else 0.0
            repo_pass_rates.append(repo_pr)
            p, f = strat_repo_pass[strategy_name][repo]
            total_runs += strat_repo_total[strategy_name][repo]
            total_passed += p
            total_failed += f

        macro_pr = sum(repo_pass_rates) / len(repo_pass_rates) if repo_pass_rates else 0.0
        macro_strategies.append(
            AggregatedMetrics(
                strategy_name=strategy_name,
                scenario_id="",
                metrics={"pass_rate": macro_pr},
                total_runs=total_runs,
                passed_runs=total_passed,
                failed_runs=total_failed,
            )
        )

    # --- Per-repository summaries ---
    repo_results_map: dict[str, list[EvaluationResult]] = defaultdict(list)
    for result in micro_results:
        parts = result.scenario_id.rsplit("-", 2)
        repo = parts[0] if len(parts) >= 3 else result.scenario_id
        repo_results_map[repo].append(result)

    per_repo: list[RepositorySummary] = []
    for repo in sorted(repo_results_map.keys()):
        repo_res = repo_results_map[repo]
        passed = sum(1 for r in repo_res if r.passed)
        failed = sum(1 for r in repo_res if not r.passed)
        per_repo.append(
            RepositorySummary(
                repository=repo,
                strategy_results=tuple(repo_res),
                total_runs=len(repo_res),
                passed_runs=passed,
                failed_runs=failed,
            )
        )

    # --- Overall ---
    total = len(micro_results)
    passed_all = sum(1 for r in micro_results if r.passed)
    overall = AggregatedResult(
        strategies=tuple(macro_strategies),
        repositories=tuple(per_repo),
        overall_pass_rate=passed_all / total if total > 0 else 0.0,
        overall_fail_rate=(total - passed_all) / total if total > 0 else 0.0,
    )

    return RunAggregationResult(
        macro=overall,
        micro=micro,
        per_repository=tuple(per_repo),
        records_processed=total,
        records_rejected=rejected,
        conditional_notes=tuple(conditional_notes),
    )
