from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from benchmark.core.enums import RunStatus
from benchmark.core.models import RunRecord, Scenario
from benchmark.core.protocols import ImpactStrategy, LLMBackend, ScenarioProvider
from benchmark.execution.isolation import IsolationContext
from benchmark.execution.runner import BenchmarkRunner, RunnerConfig


@dataclass
class PipelineConfig:
    protocol_version: str
    timeout_seconds: int = 0
    max_attempts_per_run: int = 3
    max_tokens_per_run: int = 0
    dry_run: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineResult:
    records: tuple[RunRecord, ...] = ()
    total_duration: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    timeout_count: int = 0


class BenchmarkPipeline:
    def __init__(
        self,
        strategy: ImpactStrategy,
        backend: LLMBackend,
        scenario_provider: ScenarioProvider,
        isolation: IsolationContext,
        config: PipelineConfig,
    ) -> None:
        self._strategy = strategy
        self._backend = backend
        self._scenario_provider = scenario_provider
        self._isolation = isolation
        self._config = config

    def run_scenario(self, scenario: Scenario) -> RunRecord:
        if self._config.dry_run:
            return self._dry_run_scenario(scenario)

        runner = self._make_runner(scenario)
        return runner.run(scenario)

    def run_scenario_by_id(self, scenario_id: str) -> RunRecord:
        scenario = self._scenario_provider.get_scenario(scenario_id)
        return self.run_scenario(scenario)

    def run_all(self, scenario_ids: list[str] | None = None) -> PipelineResult:
        if scenario_ids:
            scenarios = [self._scenario_provider.get_scenario(sid) for sid in scenario_ids]
        else:
            scenarios = self._scenario_provider.list_scenarios()

        if self._config.dry_run:
            return self._dry_run_all(scenarios)

        import time
        start = time.monotonic()
        records: list[RunRecord] = []

        for scenario in scenarios:
            record = self.run_scenario(scenario)
            records.append(record)

        duration = time.monotonic() - start

        success_count = sum(1 for r in records if r.status == RunStatus.succeeded)
        failure_count = sum(1 for r in records if r.status in (RunStatus.failed,))
        timeout_count = sum(1 for r in records if r.status == RunStatus.timed_out)

        return PipelineResult(
            records=tuple(records),
            total_duration=duration,
            success_count=success_count,
            failure_count=failure_count,
            timeout_count=timeout_count,
        )

    def _make_runner(self, _scenario: Scenario) -> BenchmarkRunner:
        runner_config = RunnerConfig(
            strategy_name="strategy",
            backend_name="backend",
            protocol_version=self._config.protocol_version,
            timeout_seconds=self._config.timeout_seconds,
            max_attempts=self._config.max_attempts_per_run,
            max_tokens=self._config.max_tokens_per_run,
        )
        return BenchmarkRunner(
            strategy=self._strategy,
            backend=self._backend,
            isolation=self._isolation,
            config=runner_config,
        )

    def _dry_run_scenario(self, scenario: Scenario) -> RunRecord:
        runner = self._make_runner(scenario)
        return runner.dry_run(scenario)

    def _dry_run_all(self, scenarios: list[Scenario]) -> PipelineResult:
        records = [self._dry_run_scenario(s) for s in scenarios]
        return PipelineResult(
            records=tuple(records),
            total_duration=0.0,
            success_count=len(scenarios),
        )
