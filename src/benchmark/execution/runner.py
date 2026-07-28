from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from benchmark.core.enums import ActionKind, FailureKind, RunStatus
from benchmark.core.exceptions import BenchmarkError, ModelBackendError, ProtocolViolationError

if TYPE_CHECKING:
    from benchmark.execution.regeneration import RegenerationExecutionResult
from benchmark.core.models import (
    ArtifactUniverse,
    FailureRecord,
    ImpactPrediction,
    RepositoryIdentity,
    RepositorySnapshot,
    RequirementChange,
    RunIdentity,
    RunRecord,
    Scenario,
    TokenUsage,
)
from benchmark.core.protocols import ImpactStrategy, LLMBackend
from benchmark.execution.budgets import BudgetExhaustedError, BudgetManager
from benchmark.execution.isolation import IsolationContext
from benchmark.execution.regeneration import REPAIR_CONTEXT_PROMPT_TEMPLATE, SharedRegenerationExecutor
from benchmark.execution.repair import RepairLoop
from benchmark.execution.state_machine import RunStateMachine
from benchmark.execution.validation import FunctionalValidationResult, FunctionalValidator
from benchmark.repositories.snapshot import discover_eligible_artifacts, resolve_allowed_artifacts
from benchmark.selection.planner import ArtifactSelector, RegenerationPlanner, compute_artifact_counts


@dataclass
class RunnerConfig:
    strategy_name: str
    backend_name: str
    protocol_version: str
    timeout_seconds: int = 0
    max_attempts: int = 3
    max_tokens: int = 0
    enable_regeneration: bool = False
    validation_command: list[str] | None = None
    validation_timeout: int = 30
    editable_artifact_paths: tuple[str, ...] = ()
    max_completion_tokens_per_call: int = 4096
    max_total_workflow_tokens: int = 0
    extra: dict[str, Any] = field(default_factory=dict)


class BenchmarkRunner:
    def __init__(
        self,
        strategy: ImpactStrategy,
        backend: LLMBackend | None,
        isolation: IsolationContext,
        config: RunnerConfig,
    ) -> None:
        self._strategy = strategy
        self._backend = backend
        self._isolation = isolation
        self._config = config
        self._state = RunStateMachine()
        self._budget = BudgetManager(
            max_attempts=config.max_attempts,
            max_tokens=config.max_tokens,
            timeout_seconds=config.timeout_seconds,
        )
        self._last_prediction: ImpactPrediction | None = None
        self._last_val_result: FunctionalValidationResult | None = None

    @property
    def state(self) -> RunStateMachine:
        return self._state

    @property
    def budget(self) -> BudgetManager:
        return self._budget

    def run(self, scenario: Scenario) -> RunRecord:
        isolation_report = self._isolation.verify()
        if not isolation_report.passed:
            return self._build_failure_record(
                scenario=scenario,
                failures=(
                    FailureRecord(
                        failure_kind=FailureKind.infrastructure,
                        message="Isolation check failed",
                        details=isolation_report.message,
                        stage="isolation",
                    ),
                ),
            )

        if self._config.enable_regeneration:
            _approved_strategies = frozenset({
                "monolithic",
                "full_scope_reference",
                "selective",
                "hybrid_selective",
                "iterative_repository_agent",
            })
            if self._config.strategy_name not in _approved_strategies:
                return self._build_failure_record(
                    scenario=scenario,
                    failures=(
                        FailureRecord(
                            failure_kind=FailureKind.harness_defect,
                            message="Unsupported SU-0010A regeneration condition",
                            stage="configuration",
                        ),
                    ),
                )

        self._state.start()
        start_time = time.monotonic()

        if self._config.enable_regeneration and self._config.strategy_name == "iterative_repository_agent":
            return self._run_iterative_flow(scenario, start_time)

        if self._config.enable_regeneration:
            try:
                self._budget.record_attempt()
            except BudgetExhaustedError:
                self._state.fail()
                record = RunRecord(
                    identity=self._build_run_identity(scenario),
                    status=RunStatus.timed_out,
                    failures=(FailureRecord(
                        failure_kind=FailureKind.timeout,
                        message="Budget exhausted before initial generation attempt",
                        stage="budget",
                    ),),
                    duration_seconds=time.monotonic() - start_time,
                )
            else:
                result = self._run_attempt(scenario, start_time)
                if isinstance(result, BenchmarkError):
                    self._state.fail()
                    record = RunRecord(
                        identity=self._build_run_identity(scenario),
                        status=RunStatus.failed,
                        failures=(
                            FailureRecord(
                                failure_kind=FailureKind.infrastructure,
                                message=str(result),
                                stage="runner",
                            ),
                        ),
                        duration_seconds=time.monotonic() - start_time,
                    )
                elif self._is_repairable_failure(result) and self._budget.can_attempt:
                    record = self._run_regeneration_repair_flow(
                        scenario=scenario,
                        first_record=result,
                        start_time=start_time,
                    )
                else:
                    if result.status == RunStatus.succeeded:
                        self._state.succeed()
                    else:
                        self._state.fail()
                    record = result
        else:
            repair_loop = RepairLoop(
                budget=self._budget,
                state_machine=self._state,
                attempt_fn=lambda _attempt: self._run_attempt(scenario, start_time),
            )
            outcome = repair_loop.execute()
            record = outcome.final_record

        duration = time.monotonic() - start_time

        identity = RunIdentity(
            run_id=record.identity.run_id if record.identity.run_id != "unknown" else self._build_run_id(scenario),
            protocol_version=self._config.protocol_version,
            repository_commit_sha=scenario.scenario_id,
            scenario_id=scenario.scenario_id,
            strategy_name=self._config.strategy_name,
        )

        return RunRecord(
            identity=identity,
            status=record.status,
            prediction=record.prediction,
            failures=record.failures,
            token_usage=record.token_usage,
            duration_seconds=duration,
            schema_version=record.schema_version,
            selection_prompt_tokens=record.selection_prompt_tokens,
            selection_completion_tokens=record.selection_completion_tokens,
            selection_total_tokens=record.selection_total_tokens,
            selection_model_calls=record.selection_model_calls,
            selection_duration_seconds=record.selection_duration_seconds,
            regeneration_prompt_tokens=record.regeneration_prompt_tokens,
            regeneration_completion_tokens=record.regeneration_completion_tokens,
            regeneration_total_tokens=record.regeneration_total_tokens,
            regeneration_model_calls=record.regeneration_model_calls,
            regeneration_duration_seconds=record.regeneration_duration_seconds,
            functional_validation_duration_seconds=record.functional_validation_duration_seconds,
            total_workflow_tokens=record.total_workflow_tokens,
            total_workflow_model_calls=record.total_workflow_model_calls,
            total_workflow_duration_seconds=record.total_workflow_duration_seconds,
            selected_artifact_count=record.selected_artifact_count,
            regenerated_artifact_count=record.regenerated_artifact_count,
            preserved_artifact_count=record.preserved_artifact_count,
            unresolved_human_review_count=record.unresolved_human_review_count,
            functional_validation_passed=record.functional_validation_passed,
        )

    def dry_run(self, scenario: Scenario) -> RunRecord:
        self._state.start()
        identity = self._build_run_identity(scenario)
        self._state.succeed()
        return RunRecord(
            identity=identity,
            status=RunStatus.succeeded,
            duration_seconds=0.0,
        )

    def _run_attempt(self, scenario: Scenario, start_time: float) -> RunRecord | BenchmarkError:
        try:
            if self._budget.timed_out:
                return RunRecord(
                    identity=self._build_run_identity(scenario),
                    status=RunStatus.timed_out,
                    duration_seconds=time.monotonic() - start_time,
                )

            repository_snapshot = self._build_repository_snapshot(scenario)
            requirement_change = self._build_requirement_change(scenario)
            artifact_universe = self._build_artifact_universe(scenario)

            selection_start = time.monotonic()
            prediction = self._strategy.analyze_impact(
                repository=repository_snapshot,
                requirement_change=requirement_change,
                artifact_universe=artifact_universe,
            )
            selection_duration = time.monotonic() - selection_start

            if prediction.errors:
                return RunRecord(
                    identity=self._build_run_identity(scenario),
                    status=RunStatus.failed,
                    prediction=prediction,
                    token_usage=prediction.token_usage or TokenUsage(),
                    failures=(
                        FailureRecord(
                            failure_kind=FailureKind.model_output,
                            message=prediction.errors[0],
                            details="; ".join(prediction.errors),
                            stage="analyze_impact",
                        ),
                    ),
                    duration_seconds=time.monotonic() - start_time,
                )

            if self._config.enable_regeneration:
                if self._backend is None:
                    return RunRecord(
                        identity=self._build_run_identity(scenario),
                        status=RunStatus.failed,
                        failures=(
                            FailureRecord(
                                failure_kind=FailureKind.harness_defect,
                                message="Regeneration is enabled but no LLM backend is configured.",
                                stage="configuration",
                            ),
                        ),
                        duration_seconds=time.monotonic() - start_time,
                        regenerated_artifact_count=0,
                        functional_validation_passed=None,
                    )
                return self._run_regeneration_flow(
                    scenario=scenario,
                    prediction=prediction,
                    requirement_change=requirement_change,
                    artifact_universe=artifact_universe,
                    start_time=start_time,
                    selection_duration=selection_duration,
                )

            return RunRecord(
                identity=self._build_run_identity(scenario),
                status=RunStatus.succeeded,
                prediction=prediction,
                token_usage=prediction.token_usage or TokenUsage(),
                duration_seconds=time.monotonic() - start_time,
                selection_duration_seconds=selection_duration,
                total_workflow_duration_seconds=selection_duration,
            )
        except BudgetExhaustedError:
            return RunRecord(
                identity=self._build_run_identity(scenario),
                status=RunStatus.timed_out,
                failures=(FailureRecord(
                    failure_kind=FailureKind.timeout,
                    message="Budget exhausted during attempt",
                    stage="budget",
                ),),
                duration_seconds=time.monotonic() - start_time,
            )
        except ModelBackendError as e:
            return RunRecord(
                identity=self._build_run_identity(scenario),
                status=RunStatus.failed,
                failures=(
                    FailureRecord(
                        failure_kind=FailureKind.model_output,
                        message=str(e.message) if hasattr(e, "message") else str(e),
                        details=f"{e.__class__.__name__}: {e!r}",
                        stage="backend.generate",
                    ),
                ),
                duration_seconds=time.monotonic() - start_time,
            )
        except ProtocolViolationError as e:
            return RunRecord(
                identity=self._build_run_identity(scenario),
                status=RunStatus.failed,
                failures=(
                    FailureRecord(
                        failure_kind=FailureKind.harness_defect,
                        message=str(e.message) if hasattr(e, "message") else str(e),
                        details=f"{e.__class__.__name__}: {e!r}",
                        stage="protocol",
                    ),
                ),
                duration_seconds=time.monotonic() - start_time,
            )
        except BenchmarkError as e:
            return RunRecord(
                identity=self._build_run_identity(scenario),
                status=RunStatus.failed,
                failures=(
                    FailureRecord(
                        failure_kind=FailureKind.infrastructure,
                        message=str(e.message) if hasattr(e, "message") else str(e),
                        details=f"{e.__class__.__name__}: {e!r}",
                        stage="runner",
                    ),
                ),
                duration_seconds=time.monotonic() - start_time,
            )

    def _run_regeneration_flow(
        self,
        scenario: Scenario,
        prediction: ImpactPrediction,
        requirement_change: RequirementChange,
        artifact_universe: ArtifactUniverse,
        start_time: float,
        selection_duration: float = 0.0,
    ) -> RunRecord:
        selector = ArtifactSelector()
        selection = selector.select(prediction, artifact_universe)
        regen_planner = RegenerationPlanner()
        plan = regen_planner.plan(selection, prediction)

        counts = compute_artifact_counts(prediction)

        self._last_prediction = prediction

        # Fail closed when regeneration is enabled but validation command is absent
        validation_command = self._config.validation_command
        if not validation_command or (
            isinstance(validation_command, list)
            and len(validation_command) == 1
            and not validation_command[0].strip()
        ):
            return RunRecord(
                identity=self._build_run_identity(scenario),
                status=RunStatus.failed,
                prediction=prediction,
                failures=(
                    FailureRecord(
                        failure_kind=FailureKind.harness_defect,
                        message="Regeneration enabled but validation_command is missing or empty",
                        details="enable_regeneration=True requires a non-empty validation_command",
                        stage="configuration",
                    ),
                ),
                duration_seconds=time.monotonic() - start_time,
                selection_duration_seconds=selection_duration,
                selected_artifact_count=counts.get("selected", 0),
                regenerated_artifact_count=0,
                preserved_artifact_count=counts.get("preserve", 0),
                unresolved_human_review_count=counts.get("human_review", 0),
                functional_validation_passed=None,
                total_workflow_duration_seconds=selection_duration,
            )

        # Record selection tokens BEFORE executor runs so remaining_tokens
        # reflects the true remaining workflow budget.
        selection_tok = prediction.token_usage or TokenUsage()
        if selection_tok.total_tokens > 0:
            self._budget.record_tokens(selection_tok.total_tokens)

        requirement_delta = f"{requirement_change.before} -> {requirement_change.after}"
        assert self._backend is not None
        executor = SharedRegenerationExecutor(self._backend)
        exec_result = executor.execute(
            plan, self._isolation, requirement_delta=requirement_delta,
            max_tokens=self._budget.remaining_tokens,
        )

        self._budget.record_tokens(exec_result.total_tokens)

        # Execute validation
        validator = FunctionalValidator()
        val_result = validator.validate(
            workspace_root=self._isolation.workspace.root,
            command=validation_command,
            timeout=self._config.validation_timeout,
        )
        self._last_val_result = val_result

        selection_tokens = prediction.token_usage or TokenUsage()
        selection_model_calls = 0
        total_tokens = selection_tokens.total_tokens + exec_result.total_tokens
        total_model_calls = selection_model_calls + exec_result.model_calls

        failures: list[FailureRecord] = []
        for f in exec_result.failures:
            failures.append(
                FailureRecord(
                    failure_kind=FailureKind.model_output,
                    message=f,
                    details="SharedRegenerationExecutor failure",
                    stage="regeneration",
                )
            )

        # Validation tri-state: None→not executed, True→passed, False→failed
        functional_validation_passed: bool | None = (
            val_result.passed if val_result is not None else None
        )
        if val_result is not None and not val_result.passed:
            failures.append(
                FailureRecord(
                    failure_kind=FailureKind.build,
                    message=f"Functional validation failed (exit={val_result.exit_code})",
                    details=f"stdout: {val_result.stdout[:500]}\nstderr: {val_result.stderr[:500]}",
                    stage="validation",
                )
            )

        status = RunStatus.failed if failures else RunStatus.succeeded

        # Actual regenerated count from executor result, not planned
        regenerated_count = sum(1 for a in exec_result.artifacts if a.status == "generated")

        # Workflow duration = selection + regeneration + validation
        regeneration_duration = exec_result.duration_seconds
        validation_duration = val_result.duration_seconds if val_result is not None else 0.0
        total_workflow_duration = selection_duration + regeneration_duration + validation_duration

        return RunRecord(
            identity=self._build_run_identity(scenario),
            status=status,
            prediction=prediction,
            token_usage=selection_tokens,
            duration_seconds=time.monotonic() - start_time,
            failures=tuple(failures),
            selection_prompt_tokens=selection_tokens.prompt_tokens,
            selection_completion_tokens=selection_tokens.completion_tokens,
            selection_total_tokens=selection_tokens.total_tokens,
            selection_model_calls=selection_model_calls,
            selection_duration_seconds=selection_duration,
            regeneration_prompt_tokens=exec_result.prompt_tokens,
            regeneration_completion_tokens=exec_result.completion_tokens,
            regeneration_total_tokens=exec_result.total_tokens,
            regeneration_model_calls=exec_result.model_calls,
            regeneration_duration_seconds=regeneration_duration,
            functional_validation_duration_seconds=validation_duration,
            functional_validation_passed=functional_validation_passed,
            total_workflow_tokens=total_tokens,
            total_workflow_model_calls=total_model_calls,
            total_workflow_duration_seconds=total_workflow_duration,
            selected_artifact_count=counts.get("selected", 0),
            regenerated_artifact_count=regenerated_count,
            preserved_artifact_count=counts.get("preserve", 0),
            unresolved_human_review_count=counts.get("human_review", 0),
        )

    def _is_repairable_failure(self, record: RunRecord) -> bool:
        if record.status != RunStatus.failed:
            return False
        if record.functional_validation_passed is not False:
            return False
        for f in record.failures:
            if f.failure_kind in (FailureKind.harness_defect, FailureKind.infrastructure, FailureKind.timeout):
                return False
        return True

    def _run_regeneration_repair_flow(
        self,
        scenario: Scenario,
        first_record: RunRecord,
        start_time: float,
    ) -> RunRecord:
        prediction = self._last_prediction
        if prediction is None:
            self._state.fail()
            return RunRecord(
                identity=self._build_run_identity(scenario),
                status=RunStatus.failed,
                failures=(
                    FailureRecord(
                        failure_kind=FailureKind.harness_defect,
                        message="Repair loop entered but prediction is unavailable",
                        stage="repair",
                    ),
                ),
                duration_seconds=time.monotonic() - start_time,
            )

        requirement_change = self._build_requirement_change(scenario)
        artifact_universe = self._build_artifact_universe(scenario)

        selector = ArtifactSelector()
        selection = selector.select(prediction, artifact_universe)
        regen_planner = RegenerationPlanner()
        plan = regen_planner.plan(selection, prediction)
        counts = compute_artifact_counts(prediction)

        requirement_delta = f"{requirement_change.before} -> {requirement_change.after}"
        assert self._backend is not None
        executor = SharedRegenerationExecutor(self._backend)
        validator = FunctionalValidator()

        selection_prompt = first_record.selection_prompt_tokens
        selection_completion = first_record.selection_completion_tokens
        selection_total = first_record.selection_total_tokens
        selection_calls = first_record.selection_model_calls
        selection_dur = first_record.selection_duration_seconds

        regen_prompt = first_record.regeneration_prompt_tokens
        regen_completion = first_record.regeneration_completion_tokens
        regen_total = first_record.regeneration_total_tokens
        regen_calls = first_record.regeneration_model_calls
        regen_dur = first_record.regeneration_duration_seconds

        val_dur = first_record.functional_validation_duration_seconds

        all_failures = list(first_record.failures)
        first_regen_count = first_record.regenerated_artifact_count

        # Build repair context from first validation failure
        repair_context: str | None = None
        if self._last_val_result is not None and not self._last_val_result.passed:
            repair_context = REPAIR_CONTEXT_PROMPT_TEMPLATE.format(
                exit_code=self._last_val_result.exit_code,
                stdout=self._last_val_result.stdout[:1000],
                stderr=self._last_val_result.stderr[:1000],
            )

        while self._budget.can_attempt:
            self._budget.record_attempt()

            exec_result = executor.execute(
                plan, self._isolation, requirement_delta, repair_context=repair_context,
                max_tokens=self._budget.remaining_tokens,
            )

            self._budget.record_tokens(exec_result.total_tokens)

            assert self._config.validation_command is not None
            val_result = validator.validate(
                workspace_root=self._isolation.workspace.root,
                command=self._config.validation_command,
                timeout=self._config.validation_timeout,
            )

            regen_prompt += exec_result.prompt_tokens
            regen_completion += exec_result.completion_tokens
            regen_total += exec_result.total_tokens
            regen_calls += exec_result.model_calls
            regen_dur += exec_result.duration_seconds
            val_dur += val_result.duration_seconds

            for f in exec_result.failures:
                all_failures.append(
                    FailureRecord(
                        failure_kind=FailureKind.model_output,
                        message=f,
                        details="SharedRegenerationExecutor failure",
                        stage="regeneration",
                    )
                )

            if val_result.passed:
                self._state.succeed()
                return RunRecord(
                    identity=self._build_run_identity(scenario),
                    status=RunStatus.succeeded,
                    prediction=prediction,
                    token_usage=prediction.token_usage or TokenUsage(),
                    failures=tuple(all_failures),
                    duration_seconds=time.monotonic() - start_time,
                    selection_prompt_tokens=selection_prompt,
                    selection_completion_tokens=selection_completion,
                    selection_total_tokens=selection_total,
                    selection_model_calls=selection_calls,
                    selection_duration_seconds=selection_dur,
                    regeneration_prompt_tokens=regen_prompt,
                    regeneration_completion_tokens=regen_completion,
                    regeneration_total_tokens=regen_total,
                    regeneration_model_calls=regen_calls,
                    regeneration_duration_seconds=regen_dur,
                    functional_validation_duration_seconds=val_dur,
                    functional_validation_passed=True,
                    total_workflow_tokens=selection_total + regen_total,
                    total_workflow_model_calls=selection_calls + regen_calls,
                    total_workflow_duration_seconds=selection_dur + regen_dur + val_dur,
                    selected_artifact_count=counts.get("selected", 0),
                    regenerated_artifact_count=sum(
                        1 for a in exec_result.artifacts if a.status == "generated"
                    ),
                    preserved_artifact_count=counts.get("preserve", 0),
                    unresolved_human_review_count=counts.get("human_review", 0),
                )

            all_failures.append(
                FailureRecord(
                    failure_kind=FailureKind.build,
                    message=f"Functional validation failed (exit={val_result.exit_code})",
                    details=f"stdout: {val_result.stdout[:500]}\nstderr: {val_result.stderr[:500]}",
                    stage="validation",
                )
            )

            # Update repair context for the next iteration
            repair_context = REPAIR_CONTEXT_PROMPT_TEMPLATE.format(
                exit_code=val_result.exit_code,
                stdout=val_result.stdout[:1000],
                stderr=val_result.stderr[:1000],
            )

            if not self._budget.can_attempt:
                break

        self._state.fail()
        total_tokens = selection_total + regen_total
        total_calls = selection_calls + regen_calls
        total_dur = selection_dur + regen_dur + val_dur

        return RunRecord(
            identity=self._build_run_identity(scenario),
            status=RunStatus.failed,
            prediction=prediction,
            token_usage=prediction.token_usage or TokenUsage(),
            failures=tuple(all_failures),
            duration_seconds=time.monotonic() - start_time,
            selection_prompt_tokens=selection_prompt,
            selection_completion_tokens=selection_completion,
            selection_total_tokens=selection_total,
            selection_model_calls=selection_calls,
            selection_duration_seconds=selection_dur,
            regeneration_prompt_tokens=regen_prompt,
            regeneration_completion_tokens=regen_completion,
            regeneration_total_tokens=regen_total,
            regeneration_model_calls=regen_calls,
            regeneration_duration_seconds=regen_dur,
            functional_validation_duration_seconds=val_dur,
            functional_validation_passed=False,
            total_workflow_tokens=total_tokens,
            total_workflow_model_calls=total_calls,
            total_workflow_duration_seconds=total_dur,
            selected_artifact_count=counts.get("selected", 0),
            regenerated_artifact_count=first_regen_count,
            preserved_artifact_count=counts.get("preserve", 0),
            unresolved_human_review_count=counts.get("human_review", 0),
        )

    def _run_iterative_flow(
        self,
        scenario: Scenario,
        start_time: float,
    ) -> RunRecord:
        try:
            if self._budget.timed_out:
                return RunRecord(
                    identity=self._build_run_identity(scenario),
                    status=RunStatus.timed_out,
                    duration_seconds=time.monotonic() - start_time,
                )

            repository_snapshot = self._build_repository_snapshot(scenario)
            requirement_change = self._build_requirement_change(scenario)
            artifact_universe = self._build_artifact_universe(scenario)

            validation_command = self._config.validation_command
            if not validation_command or (
                isinstance(validation_command, list)
                and len(validation_command) == 1
                and not validation_command[0].strip()
            ):
                return RunRecord(
                    identity=self._build_run_identity(scenario),
                    status=RunStatus.failed,
                    failures=(
                        FailureRecord(
                            failure_kind=FailureKind.harness_defect,
                            message="Iterative agent enabled but validation_command is missing or empty",
                            stage="configuration",
                        ),
                    ),
                    duration_seconds=time.monotonic() - start_time,
                    regenerated_artifact_count=0,
                    functional_validation_passed=None,
                )

            if self._backend is None:
                return RunRecord(
                    identity=self._build_run_identity(scenario),
                    status=RunStatus.failed,
                    failures=(
                        FailureRecord(
                            failure_kind=FailureKind.harness_defect,
                            message="Iterative agent enabled but no LLM backend is configured.",
                            stage="configuration",
                        ),
                    ),
                    duration_seconds=time.monotonic() - start_time,
                    regenerated_artifact_count=0,
                    functional_validation_passed=None,
                )

            requirement_delta = f"{requirement_change.before} -> {requirement_change.after}"
            executor = SharedRegenerationExecutor(self._backend)
            validator = FunctionalValidator()

            selection_total_prompt = 0
            selection_total_completion = 0
            selection_total_tok = 0
            selection_calls = 0
            selection_dur = 0.0

            regen_total_prompt = 0
            regen_total_completion = 0
            regen_total_tok = 0
            regen_calls = 0
            regen_dur = 0.0

            val_dur = 0.0
            all_failures: list[FailureRecord] = []
            total_regenerated = 0
            final_prediction: ImpactPrediction | None = None
            last_val_result: FunctionalValidationResult | None = None
            last_exec_result: RegenerationExecutionResult | None = None
            iteration = 0
            has_validation_run = False

            while self._budget.can_attempt:
                budget_remaining = self._budget.remaining_tokens
                if self._budget._max_tokens > 0 and budget_remaining <= 0:
                    break

                self._budget.record_attempt()

                if self._budget.timed_out:
                    break

                if iteration == 0:
                    selection_start = time.monotonic()
                    prediction = self._strategy.analyze_impact(
                        repository=repository_snapshot,
                        requirement_change=requirement_change,
                        artifact_universe=artifact_universe,
                        max_tokens=self._budget.remaining_tokens,
                    )
                    sel_dur = time.monotonic() - selection_start
                    selection_dur += sel_dur
                else:
                    if last_val_result is None:
                        break

                    workspace_summary = self._build_workspace_summary(
                        previous_prediction=final_prediction or prediction,
                        exec_result=last_exec_result,
                    )

                    revise_plan = getattr(self._strategy, "revise_plan", None)
                    if not callable(revise_plan):
                        return RunRecord(
                            identity=self._build_run_identity(scenario),
                            status=RunStatus.failed,
                            failures=(
                                FailureRecord(
                                    failure_kind=FailureKind.harness_defect,
                                    message="Strategy does not support revise_plan",
                                    stage="configuration",
                                ),
                            ),
                            duration_seconds=time.monotonic() - start_time,
                        )

                    selection_start = time.monotonic()
                    prediction = revise_plan(
                        requirement_change=requirement_change,
                        artifact_universe=artifact_universe,
                        previous_prediction=final_prediction or prediction,
                        exit_code=last_val_result.exit_code,
                        val_stdout=last_val_result.stdout,
                        val_stderr=last_val_result.stderr,
                        workspace_summary=workspace_summary,
                        remaining_attempts=self._budget.remaining_attempts,
                        remaining_tokens=self._budget.remaining_tokens,
                    )
                    sel_dur = time.monotonic() - selection_start
                    selection_dur += sel_dur

                final_prediction = prediction
                tok = prediction.token_usage or TokenUsage()
                selection_total_prompt += tok.prompt_tokens
                selection_total_completion += tok.completion_tokens
                selection_total_tok += tok.total_tokens
                selection_calls += 1
                self._budget.record_tokens(tok.total_tokens)

                if prediction.errors:
                    last_requires_iteration = getattr(self._strategy, "last_requires_iteration", True)
                    if not prediction.decisions and not last_requires_iteration:
                        break
                    all_failures.append(
                        FailureRecord(
                            failure_kind=FailureKind.model_output,
                            message=prediction.errors[0],
                            details="; ".join(prediction.errors),
                            stage="analyze_impact",
                        )
                    )
                    break

                if not self._budget.can_attempt:
                    if not has_validation_run:
                        all_failures.append(
                            FailureRecord(
                                failure_kind=FailureKind.timeout,
                                message="Token budget exhausted by agent reasoning before regeneration",
                                stage="budget",
                            )
                        )
                    break

                selector = ArtifactSelector()
                selection = selector.select(prediction, artifact_universe)
                regen_planner = RegenerationPlanner()
                plan = regen_planner.plan(selection, prediction)
                counts = compute_artifact_counts(prediction)

                if len(plan.regenerate_artifact_paths) == 0:
                    if not has_validation_run:
                        all_failures.append(
                            FailureRecord(
                                failure_kind=FailureKind.harness_defect,
                                message="Iterative agent selected no artifacts for regeneration on first attempt",
                                stage="selection",
                            )
                        )
                    break

                exec_result = executor.execute(
                    plan, self._isolation, requirement_delta=requirement_delta,
                    max_tokens=self._budget.remaining_tokens,
                )

                self._budget.record_tokens(exec_result.total_tokens)

                val_result = validator.validate(
                    workspace_root=self._isolation.workspace.root,
                    command=validation_command,
                    timeout=self._config.validation_timeout,
                )
                has_validation_run = True

                regen_total_prompt += exec_result.prompt_tokens
                regen_total_completion += exec_result.completion_tokens
                regen_total_tok += exec_result.total_tokens
                regen_calls += exec_result.model_calls
                regen_dur += exec_result.duration_seconds
                val_dur += val_result.duration_seconds
                last_val_result = val_result
                last_exec_result = exec_result

                iteration += 1

                for f in exec_result.failures:
                    all_failures.append(
                        FailureRecord(
                            failure_kind=FailureKind.model_output,
                            message=f,
                            details="SharedRegenerationExecutor failure",
                            stage="regeneration",
                        )
                    )

                if val_result.passed:
                    total_regenerated = sum(
                        1 for a in exec_result.artifacts if a.status == "generated"
                    )
                    selection_total = selection_total_prompt + selection_total_completion
                    total_tokens = selection_total + regen_total_tok
                    total_calls = selection_calls + regen_calls
                    total_dur = selection_dur + regen_dur + val_dur

                    return RunRecord(
                        identity=self._build_run_identity(scenario),
                        status=RunStatus.succeeded,
                        prediction=final_prediction,
                        token_usage=final_prediction.token_usage or TokenUsage(),
                        duration_seconds=time.monotonic() - start_time,
                        failures=tuple(all_failures),
                        selection_prompt_tokens=selection_total_prompt,
                        selection_completion_tokens=selection_total_completion,
                        selection_total_tokens=selection_total,
                        selection_model_calls=selection_calls,
                        selection_duration_seconds=selection_dur,
                        regeneration_prompt_tokens=regen_total_prompt,
                        regeneration_completion_tokens=regen_total_completion,
                        regeneration_total_tokens=regen_total_tok,
                        regeneration_model_calls=regen_calls,
                        regeneration_duration_seconds=regen_dur,
                        functional_validation_duration_seconds=val_dur,
                        functional_validation_passed=True,
                        total_workflow_tokens=total_tokens,
                        total_workflow_model_calls=total_calls,
                        total_workflow_duration_seconds=total_dur,
                        selected_artifact_count=counts.get("selected", 0),
                        regenerated_artifact_count=total_regenerated,
                        preserved_artifact_count=counts.get("preserve", 0),
                        unresolved_human_review_count=counts.get("human_review", 0),
                    )

                all_failures.append(
                    FailureRecord(
                        failure_kind=FailureKind.build,
                        message=f"Functional validation failed (exit={val_result.exit_code})",
                        details=f"stdout: {val_result.stdout[:500]}\nstderr: {val_result.stderr[:500]}",
                        stage="validation",
                    )
                )

                total_regenerated = sum(
                    1 for a in exec_result.artifacts if a.status == "generated"
                )

                if not self._budget.can_attempt:
                    break

                last_requires_iteration = getattr(self._strategy, "last_requires_iteration", True)
                if not last_requires_iteration:
                    break

            self._state.fail()
            selection_total = selection_total_prompt + selection_total_completion
            total_tokens = selection_total + regen_total_tok
            total_calls = selection_calls + regen_calls
            total_dur = selection_dur + regen_dur + val_dur

            return RunRecord(
                identity=self._build_run_identity(scenario),
                status=RunStatus.timed_out if self._budget.timed_out else RunStatus.failed,
                prediction=final_prediction,
                token_usage=final_prediction.token_usage or TokenUsage() if final_prediction else TokenUsage(),
                duration_seconds=time.monotonic() - start_time,
                failures=tuple(all_failures),
                selection_prompt_tokens=selection_total_prompt,
                selection_completion_tokens=selection_total_completion,
                selection_total_tokens=selection_total,
                selection_model_calls=selection_calls,
                selection_duration_seconds=selection_dur,
                regeneration_prompt_tokens=regen_total_prompt,
                regeneration_completion_tokens=regen_total_completion,
                regeneration_total_tokens=regen_total_tok,
                regeneration_model_calls=regen_calls,
                regeneration_duration_seconds=regen_dur,
                functional_validation_duration_seconds=val_dur,
                functional_validation_passed=False,
                total_workflow_tokens=total_tokens,
                total_workflow_model_calls=total_calls,
                total_workflow_duration_seconds=total_dur,
                selected_artifact_count=(
                    final_prediction
                    and len([d for d in final_prediction.decisions
                             if d.action in (ActionKind.regenerate, ActionKind.human_review)])
                    or 0
                ),
                regenerated_artifact_count=total_regenerated,
                preserved_artifact_count=(
                    final_prediction
                    and len([d for d in final_prediction.decisions
                             if d.action == ActionKind.preserve])
                    or 0
                ),
                unresolved_human_review_count=(
                    final_prediction
                    and len([d for d in final_prediction.decisions
                             if d.action == ActionKind.human_review])
                    or 0
                ),
            )
        except BudgetExhaustedError:
            return RunRecord(
                identity=self._build_run_identity(scenario),
                status=RunStatus.timed_out,
                failures=(FailureRecord(
                    failure_kind=FailureKind.timeout,
                    message="Budget exhausted during iterative agent execution",
                    stage="budget",
                ),),
                duration_seconds=time.monotonic() - start_time,
            )
        except ModelBackendError as e:
            return RunRecord(
                identity=self._build_run_identity(scenario),
                status=RunStatus.failed,
                failures=(
                    FailureRecord(
                        failure_kind=FailureKind.model_output,
                        message=str(e.message) if hasattr(e, "message") else str(e),
                        details=f"{e.__class__.__name__}: {e!r}",
                        stage="backend.generate",
                    ),
                ),
                duration_seconds=time.monotonic() - start_time,
            )
        except ProtocolViolationError as e:
            return RunRecord(
                identity=self._build_run_identity(scenario),
                status=RunStatus.failed,
                failures=(
                    FailureRecord(
                        failure_kind=FailureKind.harness_defect,
                        message=str(e.message) if hasattr(e, "message") else str(e),
                        details=f"{e.__class__.__name__}: {e!r}",
                        stage="protocol",
                    ),
                ),
                duration_seconds=time.monotonic() - start_time,
            )
        except BenchmarkError as e:
            return RunRecord(
                identity=self._build_run_identity(scenario),
                status=RunStatus.failed,
                failures=(
                    FailureRecord(
                        failure_kind=FailureKind.infrastructure,
                        message=str(e.message) if hasattr(e, "message") else str(e),
                        details=f"{e.__class__.__name__}: {e!r}",
                        stage="runner",
                    ),
                ),
                duration_seconds=time.monotonic() - start_time,
            )

    def _build_workspace_summary(
        self,
        previous_prediction: ImpactPrediction,
        exec_result: Any = None,
    ) -> str:
        parts = []
        if previous_prediction.decisions:
            parts.append("Previously selected artifacts:")
            for d in previous_prediction.decisions:
                parts.append(f"  - {d.artifact.path} ({d.action.value})")
        if exec_result is not None and hasattr(exec_result, "artifacts"):
            parts.append("Generated content (truncated to 200 chars per file):")
            max_paths = 10
            for i, art in enumerate(exec_result.artifacts):
                if i >= max_paths:
                    parts.append(f"  ... and {len(exec_result.artifacts) - max_paths} more")
                    break
                content_preview = art.content[:200].replace("\n", "\\n")
                parts.append(f"  - {art.path}: {content_preview}")
        summary = "\n".join(parts) if parts else "(empty workspace)"
        return summary[:3000]

    def _build_run_identity(self, scenario: Scenario) -> RunIdentity:
        return RunIdentity(
            run_id=self._build_run_id(scenario),
            protocol_version=self._config.protocol_version,
            repository_commit_sha=scenario.scenario_id,
            scenario_id=scenario.scenario_id,
            strategy_name=self._config.strategy_name,
        )

    def _build_run_id(self, scenario: Scenario) -> str:
        import uuid
        return f"{scenario.scenario_id}_{self._config.strategy_name}_{uuid.uuid4().hex[:8]}"

    def _active_snapshot(self) -> Path:
        active = self._isolation.active_snapshot_root
        if active is None:
            raise BenchmarkError(
                "Regeneration-enabled execution requires an active_snapshot_root. "
                "No active snapshot is configured."
            )
        if not active.is_dir():
            raise BenchmarkError(
                f"Active snapshot path does not exist or is not a directory: {active}"
            )
        return active

    def _build_repository_snapshot(self, scenario: Scenario) -> RepositorySnapshot:
        if self._config.enable_regeneration:
            return RepositorySnapshot(
                identity=RepositoryIdentity(
                    name=scenario.repository,
                    url=scenario.repository,
                ),
                commit_sha=scenario.scenario_id,
                path=str(self._active_snapshot()),
            )
        return RepositorySnapshot(
            identity=RepositoryIdentity(
                name=scenario.repository,
                url=scenario.repository,
            ),
            commit_sha=scenario.scenario_id,
            path=scenario.repository,
        )

    def _build_requirement_change(self, scenario: Scenario) -> RequirementChange:
        return RequirementChange(
            before=scenario.requirement_before,
            after=scenario.requirement_after,
            acceptance_criteria=tuple(c.description for c in scenario.acceptance_criteria),
        )

    def _build_artifact_universe(self, scenario: Scenario) -> ArtifactUniverse:
        if self._config.enable_regeneration:
            if self._config.editable_artifact_paths:
                return ArtifactUniverse(
                    artifacts=resolve_allowed_artifacts(
                        self._active_snapshot(),
                        self._config.editable_artifact_paths,
                    )
                )
            artifacts = discover_eligible_artifacts(self._active_snapshot())
            return ArtifactUniverse(artifacts=artifacts)
        # Legacy fixture compatibility only.
        # Ground Truth fallback is forbidden for regeneration-enabled and scientific execution.
        return ArtifactUniverse(artifacts=scenario.expected_affected_artifacts)

    def _build_failure_record(
        self,
        scenario: Scenario,
        failures: tuple[FailureRecord, ...],
    ) -> RunRecord:
        return RunRecord(
            identity=self._build_run_identity(scenario),
            status=RunStatus.failed,
            failures=failures,
            duration_seconds=0.0,
        )
