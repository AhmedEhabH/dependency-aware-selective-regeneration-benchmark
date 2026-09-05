from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from benchmark.core.enums import RunStatus
from benchmark.core.models import RunRecord, Scenario
from benchmark.core.protocols import ImpactStrategy, LLMBackend, ScenarioProvider
from benchmark.execution.isolation import IsolationContext
from benchmark.execution.runner import BenchmarkRunner, RunnerConfig
from benchmark.llm.mock_backend import NullLLMBackend


@dataclass
class PipelineConfig:
    protocol_version: str
    timeout_seconds: int = 0
    max_attempts_per_run: int = 3
    max_tokens_per_run: int = 0
    dry_run: bool = False
    enable_regeneration: bool = False
    validation_command: list[str] | None = None
    validation_timeout: int = 180
    validation_env: dict[str, str] = field(default_factory=dict)
    active_snapshot_root: str | Path | None = None
    editable_artifact_paths: tuple[str, ...] = ()
    max_completion_tokens_per_call: int = 4096
    max_total_workflow_tokens: int = 0
    agent_control_max_completion_tokens: int = 512
    canonical_project_root: str | Path | None = None
    python_executable: str = ""
    exact_patch: bool = False
    validation_python: str | None = None
    scientific_gold_isolation: bool = False
    extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.max_completion_tokens_per_call, bool):
            raise ValueError("PipelineConfig.max_completion_tokens_per_call must be integer, not bool")
        if isinstance(self.validation_timeout, bool) or self.validation_timeout <= 0:
            n = self.validation_timeout
            raise ValueError(f"PipelineConfig.validation_timeout must be a positive integer, got {n}")
        if isinstance(self.max_total_workflow_tokens, bool):
            raise ValueError("PipelineConfig.max_total_workflow_tokens must be integer, not bool")
        if isinstance(self.max_tokens_per_run, bool):
            raise ValueError("PipelineConfig.max_tokens_per_run must be integer, not bool")
        if self.max_completion_tokens_per_call <= 0:
            n = self.max_completion_tokens_per_call
            raise ValueError(f"PipelineConfig.max_completion_tokens_per_call must be > 0, got {n}")
        if self.max_total_workflow_tokens < 0:
            n = self.max_total_workflow_tokens
            raise ValueError(f"PipelineConfig.max_total_workflow_tokens must be >= 0, got {n}")
        if self.max_tokens_per_run < 0:
            n = self.max_tokens_per_run
            raise ValueError(f"PipelineConfig.max_tokens_per_run must be >= 0, got {n}")
        if isinstance(self.agent_control_max_completion_tokens, bool):
            raise ValueError(
                "PipelineConfig.agent_control_max_completion_tokens must be integer, not bool"
            )
        if self.agent_control_max_completion_tokens <= 0:
            n = self.agent_control_max_completion_tokens
            raise ValueError(
                "PipelineConfig.agent_control_max_completion_tokens must be > 0, got {n}"
            )
        _ = self.resolved_max_total_workflow_tokens

    @property
    def resolved_max_total_workflow_tokens(self) -> int:
        explicit_total = self.max_total_workflow_tokens
        legacy_total = self.max_tokens_per_run
        if explicit_total > 0 and legacy_total > 0 and explicit_total != legacy_total:
            raise ValueError(
                f"Explicit max_total_workflow_tokens ({explicit_total}) and "
                f"legacy max_tokens_per_run ({legacy_total}) are both positive but differ"
            )
        if explicit_total > 0:
            return explicit_total
        if legacy_total > 0:
            return legacy_total
        return 0


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
        backend: LLMBackend | None,
        scenario_provider: ScenarioProvider,
        isolation: IsolationContext,
        config: PipelineConfig,
        strategy_name: str = "strategy",
    ) -> None:
        self._strategy = strategy
        self._strategy_name = strategy_name
        self._backend = backend or NullLLMBackend()
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
            strategy_name=self._strategy_name,
            backend_name="backend",
            protocol_version=self._config.protocol_version,
            timeout_seconds=self._config.timeout_seconds,
            max_attempts=self._config.max_attempts_per_run,
            max_tokens=self._config.resolved_max_total_workflow_tokens,
            enable_regeneration=self._config.enable_regeneration,
            validation_command=self._config.validation_command,
            validation_timeout=self._config.validation_timeout,
            validation_env=dict(self._config.validation_env),
            editable_artifact_paths=self._config.editable_artifact_paths,
            max_completion_tokens_per_call=self._config.max_completion_tokens_per_call,
            max_total_workflow_tokens=self._config.resolved_max_total_workflow_tokens,
            agent_control_max_completion_tokens=self._config.agent_control_max_completion_tokens,
            canonical_project_root=self._config.canonical_project_root,
            python_executable=self._config.python_executable,
            exact_patch=self._config.exact_patch,
            validation_python=self._config.validation_python,
            scientific_gold_isolation=self._config.scientific_gold_isolation,
        )
        return BenchmarkRunner(
            strategy=self._strategy,
            backend=self._backend,  # type: ignore[arg-type]
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
