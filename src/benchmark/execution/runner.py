from __future__ import annotations

import time
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from benchmark.core.enums import ActionKind, FailureKind, RunStatus
from benchmark.core.exceptions import BenchmarkError, ModelBackendError, ProtocolViolationError
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
from benchmark.execution.post_generation import PostGenerationResult
from benchmark.execution.regeneration import (
    REPAIR_CONTEXT_PROMPT_TEMPLATE,
    RegenerationExecutionResult,
    SharedRegenerationExecutor,
)
from benchmark.execution.repair import RepairLoop
from benchmark.execution.scenario_evaluator import ScenarioEvaluatorResult
from benchmark.execution.state_machine import RunStateMachine
from benchmark.execution.validation import FunctionalValidationResult, FunctionalValidator
from benchmark.repositories.snapshot import resolve_allowed_artifacts
from benchmark.selection.planner import ArtifactSelector, RegenerationPlanner, compute_artifact_counts


@dataclass(frozen=True)
class _ScientificValidationResult:
    migration: PostGenerationResult | None
    baseline: FunctionalValidationResult | None
    evaluator: ScenarioEvaluatorResult | None
    passed: bool
    failed_stage: str | None
    failure_kind: FailureKind | None
    feedback: str
    duration_seconds: float


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
    canonical_project_root: str | Path | None = None
    python_executable: str = ""
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
        self._last_scientific_result: _ScientificValidationResult | None = None

    @property
    def state(self) -> RunStateMachine:
        return self._state

    @property
    def budget(self) -> BudgetManager:
        return self._budget

    def _execute_scientific_validation(
        self,
        scenario: Scenario,
        exec_result: object | None = None,
    ) -> _ScientificValidationResult:
        start = time.monotonic()
        feedback_parts: list[str] = []
        migration_result: PostGenerationResult | None = None
        baseline_result: FunctionalValidationResult | None = None
        evaluator_result: ScenarioEvaluatorResult | None = None

        def _build(
            passed: bool,
            failed_stage: str | None,
            failure_kind: FailureKind | None,
        ) -> _ScientificValidationResult:
            nonlocal migration_result, baseline_result, evaluator_result, feedback_parts, start
            elapsed = time.monotonic() - start
            r = _ScientificValidationResult(
                migration=migration_result,
                baseline=baseline_result,
                evaluator=evaluator_result,
                passed=passed,
                failed_stage=failed_stage,
                failure_kind=failure_kind,
                feedback="; ".join(feedback_parts),
                duration_seconds=elapsed,
            )
            self._last_scientific_result = r
            return r

        # Stage 1 — generation guard
        if exec_result is not None:
            er = exec_result
            model_calls = getattr(er, "model_calls", 0)
            artifacts = getattr(er, "artifacts", [])
            generated_count = sum(
                1 for a in artifacts if getattr(a, "status", "") == "generated"
            )
            if model_calls == 0 or generated_count == 0:
                feedback_parts.append("Generation guard: no model calls or no generated source")
                return _build(False, "generation_guard", FailureKind.build)

        # Stage 2 — post-generation migration
        pgc = scenario.post_generation_command
        if scenario.require_new_migration and not pgc:
            feedback_parts.append("Harness defect: require_new_migration=True but command is empty")
            return _build(False, "configuration", FailureKind.harness_defect)
        if pgc:
            from benchmark.execution.post_generation import run_post_generation_command
            migration_result = run_post_generation_command(
                workspace_root=self._isolation.workspace.root,
                command=pgc,
                require_new_migration=scenario.require_new_migration,
                timeout=self._config.validation_timeout,
            )
            if not migration_result.passed:
                m_stdout = migration_result.stdout[:1000]
                m_stderr = migration_result.stderr[:1000]
                feedback_parts.append(f"Migration failed: exit={migration_result.exit_code}")
                if m_stdout:
                    feedback_parts.append(f"stdout: {m_stdout[:500]}")
                if m_stderr:
                    feedback_parts.append(f"stderr: {m_stderr[:500]}")
                return _build(False, "migration_generation", FailureKind.build)

        # Stage 3 — baseline validation
        validation_command = self._config.validation_command
        if validation_command:
            validator = FunctionalValidator()
            baseline_result = validator.validate(
                workspace_root=self._isolation.workspace.root,
                command=validation_command,
                timeout=self._config.validation_timeout,
            )
            if not baseline_result.passed:
                b_stdout = baseline_result.stdout[:1000]
                b_stderr = baseline_result.stderr[:1000]
                feedback_parts.append(
                    f"Baseline validation failed (exit={baseline_result.exit_code})"
                )
                if b_stdout:
                    feedback_parts.append(f"stdout: {b_stdout[:500]}")
                if b_stderr:
                    feedback_parts.append(f"stderr: {b_stderr[:500]}")
                return _build(False, "baseline_validation", FailureKind.build)

        # Stage 4 — isolated scenario evaluator
        evaluator_asset = scenario.evaluator_asset
        if evaluator_asset:
            cpr = self._config.canonical_project_root
            if not cpr:
                feedback_parts.append(
                    "Harness defect: evaluator_asset is non-empty but canonical_project_root is None"
                )
                return _build(False, "configuration", FailureKind.harness_defect)
            pe = self._config.python_executable
            if not pe or not pe.strip():
                feedback_parts.append(
                    "Harness defect: evaluator_asset is non-empty but python_executable is empty"
                )
                return _build(False, "configuration", FailureKind.harness_defect)
            from benchmark.execution.scenario_evaluator import run_scenario_evaluator
            evaluator_result = run_scenario_evaluator(
                canonical_project_root=cpr,
                evaluator_asset=evaluator_asset,
                generated_workspace=self._isolation.workspace.root,
                python_executable=pe,
                timeout=self._config.validation_timeout,
            )
            if not evaluator_result.passed:
                e_error = evaluator_result.error[:1000]
                e_checks = evaluator_result.checks
                check_str = ", ".join(str(c) for c in e_checks[:5]) if e_checks else ""
                feedback_parts.append("Scenario evaluator failed")
                if check_str:
                    feedback_parts.append(f"checks: {check_str}")
                if e_error:
                    feedback_parts.append(f"error: {e_error[:500]}")
                return _build(False, "scenario_evaluator", FailureKind.build)

        # Stage 5 — final success decision
        return _build(True, None, None)

    # -------------------------------------------------------------------
    # RF-2: 5 private helpers
    # -------------------------------------------------------------------

    def _requires_scenario_evaluator(self, scenario: Scenario) -> bool:
        return bool(
            scenario.post_generation_command
            or scenario.require_new_migration
            or scenario.evaluator_asset
        )

    def _validate_scientific_configuration(
        self,
        scenario: Scenario,
    ) -> FailureRecord | None:
        if (
            scenario.require_new_migration
            and not scenario.post_generation_command
        ):
            return FailureRecord(
                failure_kind=FailureKind.harness_defect,
                message="require_new_migration=True but post_generation_command is empty",
                stage="configuration",
            )
        if self._requires_scenario_evaluator(scenario) and not scenario.evaluator_asset:
            return FailureRecord(
                failure_kind=FailureKind.harness_defect,
                message="Scenario metadata requires evaluator but evaluator_asset is empty",
                stage="configuration",
            )
        if scenario.evaluator_asset:
            if not                 self._config.canonical_project_root:
                return FailureRecord(
                    failure_kind=FailureKind.harness_defect,
                    message="evaluator_asset is non-empty but canonical_project_root is None",
                    stage="configuration",
                )
            pe = self._config.python_executable
            if not pe or not pe.strip():
                return FailureRecord(
                    failure_kind=FailureKind.harness_defect,
                    message="evaluator_asset is non-empty but python_executable is empty/whitespace",
                    stage="configuration",
                )
        if self._config.enable_regeneration:
            vc = self._config.validation_command
            if not vc:
                return FailureRecord(
                    failure_kind=FailureKind.harness_defect,
                    message="enable_regeneration=True requires a non-empty validation_command",
                    stage="configuration",
                )
            if isinstance(vc, list):
                for item in vc:
                    if not isinstance(item, str) or not item.strip():
                        return FailureRecord(
                            failure_kind=FailureKind.harness_defect,
                            message="validation_command contains a non-string or whitespace-only item",
                            stage="configuration",
                        )
        return None

    def _scientific_record_fields(
        self,
        result: _ScientificValidationResult | None,
    ) -> dict[str, Any]:
        if result is None:
            return {
                "migration_generation_passed": None,
                "migration_duration_seconds": 0.0,
                "generated_migration_paths": (),
                "baseline_validation_passed": None,
                "baseline_validation_duration_seconds": 0.0,
                "scenario_evaluator_passed": None,
                "scenario_evaluator_duration_seconds": 0.0,
                "scenario_evaluator_checks": (),
                "functional_validation_passed": None,
                "functional_validation_duration_seconds": 0.0,
            }
        mig = result.migration
        bas = result.baseline
        eva = result.evaluator
        mig_passed = mig.passed if mig is not None else None
        mig_dur = mig.duration_seconds if mig is not None else 0.0
        mig_paths = mig.created_paths if mig is not None else ()
        bas_passed = bas.passed if bas is not None else None
        bas_dur = bas.duration_seconds if bas is not None else 0.0
        eva_passed = eva.passed if eva is not None else None
        eva_dur = eva.duration_seconds if eva is not None else 0.0
        eva_checks = eva.checks if eva is not None else ()
        return {
            "migration_generation_passed": mig_passed,
            "migration_duration_seconds": mig_dur,
            "generated_migration_paths": tuple(mig_paths),
            "baseline_validation_passed": bas_passed,
            "baseline_validation_duration_seconds": bas_dur,
            "scenario_evaluator_passed": eva_passed,
            "scenario_evaluator_duration_seconds": eva_dur,
            "scenario_evaluator_checks": tuple(eva_checks),
            "functional_validation_passed": bas_passed,
            "functional_validation_duration_seconds": bas_dur,
        }

    def _failure_from_scientific_result(
        self,
        result: _ScientificValidationResult,
    ) -> FailureRecord:
        stage = result.failed_stage or "scientific_validation"
        kind = result.failure_kind or FailureKind.build
        if stage == "generation_guard":
            msg = "Generation guard: no model calls or no generated source"
        elif stage == "migration_generation":
            msg = result.feedback or "Migration generation failed"
        elif stage == "baseline_validation":
            msg = result.feedback or "Baseline validation failed"
        elif stage == "scenario_evaluator":
            msg = result.feedback or "Scenario evaluator failed"
        else:
            msg = result.feedback or "Scientific validation failed"
        return FailureRecord(
            failure_kind=kind,
            message=msg,
            details=result.feedback[:1000] if result.feedback else "",
            stage=stage,
        )

    def _scientific_feedback_channels(
        self,
        result: _ScientificValidationResult,
    ) -> tuple[int, str, str]:
        stage = result.failed_stage
        if stage == "migration_generation" and result.migration is not None:
            ec = result.migration.exit_code
            so = result.migration.stdout[:1000]
            se = result.migration.stderr[:1000]
        elif stage == "baseline_validation" and result.baseline is not None:
            ec = result.baseline.exit_code
            so = result.baseline.stdout[:1000]
            se = result.baseline.stderr[:1000]
        elif stage == "scenario_evaluator" and result.evaluator is not None:
            ec = result.evaluator.exit_code
            so = result.evaluator.stdout[:1000]
            se = result.evaluator.error[:1000]
            if result.evaluator.checks:
                checks_str = "checks: " + ", ".join(str(c) for c in result.evaluator.checks[:5])
                se = se[:800] + "; " + checks_str if se else checks_str
            se = se[:1000]
        else:
            ec = -1
            so = ""
            se = result.feedback[:1000] if result.feedback else ""
        return ec, so, se

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

        # Preflight scientific configuration before model generation
        if self._config.enable_regeneration:
            config_failure = self._validate_scientific_configuration(scenario)
            if config_failure is not None:
                self._state.fail()
                return replace(
                    self._build_failure_record(scenario, failures=(config_failure,)),
                    duration_seconds=time.monotonic() - start_time,
                )

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

        return replace(record, identity=identity, duration_seconds=duration)

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

        # Execute scientific validation (shared sequence)
        sci_result = self._execute_scientific_validation(scenario, exec_result)

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

        # Validation tri-state from scientific result
        if sci_result is not None and not sci_result.passed:
            failures.append(
                self._failure_from_scientific_result(sci_result)
            )

        status = RunStatus.failed if failures else RunStatus.succeeded

        # Actual regenerated count from executor result, not planned
        regenerated_count = sum(1 for a in exec_result.artifacts if a.status == "generated")

        # Workflow duration = selection + regeneration + validation
        regeneration_duration = exec_result.duration_seconds
        validation_duration = sci_result.duration_seconds if sci_result is not None else 0.0
        total_workflow_duration = selection_duration + regeneration_duration + validation_duration

        fields = self._scientific_record_fields(sci_result)

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
            total_workflow_tokens=total_tokens,
            total_workflow_model_calls=total_model_calls,
            total_workflow_duration_seconds=total_workflow_duration,
            **fields,
            selected_artifact_count=counts.get("selected", 0),
            regenerated_artifact_count=regenerated_count,
            preserved_artifact_count=counts.get("preserve", 0),
            unresolved_human_review_count=counts.get("human_review", 0),
        )

    def _is_repairable_failure(self, record: RunRecord) -> bool:
        if record.status != RunStatus.failed:
            return False
        for f in record.failures:
            if f.failure_kind in (FailureKind.harness_defect, FailureKind.infrastructure, FailureKind.timeout):
                return False
            if f.stage in (
                "generation_guard", "regeneration", "migration_generation",
                "baseline_validation", "scenario_evaluator",
            ):
                return True
        return False

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

        val_dur = (
            first_record.migration_duration_seconds
            + first_record.baseline_validation_duration_seconds
            + first_record.scenario_evaluator_duration_seconds
        )

        all_failures = list(first_record.failures)
        first_regen_count = first_record.regenerated_artifact_count

        # Build repair context from first scientific result
        repair_context: str | None = None
        last_sci = self._last_scientific_result
        if last_sci is not None and not last_sci.passed:
            ec, so, se = self._scientific_feedback_channels(last_sci)
            repair_context = REPAIR_CONTEXT_PROMPT_TEMPLATE.format(
                exit_code=ec,
                stdout=so,
                stderr=se,
            )

        while self._budget.can_attempt:
            self._budget.record_attempt()

            exec_result = executor.execute(
                plan, self._isolation, requirement_delta, repair_context=repair_context,
                max_tokens=self._budget.remaining_tokens,
            )

            self._budget.record_tokens(exec_result.total_tokens)

            sci_result = self._execute_scientific_validation(scenario, exec_result)

            regen_prompt += exec_result.prompt_tokens
            regen_completion += exec_result.completion_tokens
            regen_total += exec_result.total_tokens
            regen_calls += exec_result.model_calls
            regen_dur += exec_result.duration_seconds
            val_dur += sci_result.duration_seconds if sci_result is not None else 0.0

            for failure_msg in exec_result.failures:
                all_failures.append(
                    FailureRecord(
                        failure_kind=FailureKind.model_output,
                        message=failure_msg,
                        details="SharedRegenerationExecutor failure",
                        stage="regeneration",
                    )
                )

            if sci_result is not None and sci_result.passed and not exec_result.failures:
                self._state.succeed()
                fields = self._scientific_record_fields(sci_result)
                total_tok = selection_total + regen_total
                total_calls_val = selection_calls + regen_calls
                total_dur_val = selection_dur + regen_dur + val_dur
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
                    **fields,
                    total_workflow_tokens=total_tok,
                    total_workflow_model_calls=total_calls_val,
                    total_workflow_duration_seconds=total_dur_val,
                    selected_artifact_count=counts.get("selected", 0),
                    regenerated_artifact_count=sum(
                        1 for a in exec_result.artifacts if a.status == "generated"
                    ),
                    preserved_artifact_count=counts.get("preserve", 0),
                    unresolved_human_review_count=counts.get("human_review", 0),
                )

            if sci_result is not None and not sci_result.passed:
                all_failures.append(
                    self._failure_from_scientific_result(sci_result)
                )

            # Update repair context from scientific result
            if sci_result is not None and not sci_result.passed:
                ec, so, se = self._scientific_feedback_channels(sci_result)
                repair_context = REPAIR_CONTEXT_PROMPT_TEMPLATE.format(
                    exit_code=ec, stdout=so, stderr=se,
                )
            elif exec_result.failures:
                repair_context = "; ".join(exec_result.failures)[:1500]
            else:
                repair_context = None

            if not self._budget.can_attempt:
                break

        self._state.fail()
        total_tokens = selection_total + regen_total
        total_calls = selection_calls + regen_calls
        total_dur = selection_dur + regen_dur + val_dur

        # Failed record preserves latest available stage evidence
        sci = self._last_scientific_result
        fields = self._scientific_record_fields(sci)
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
            **fields,
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

            begin_run = getattr(self._strategy, "begin_run", None)
            if not callable(begin_run):
                return RunRecord(
                    identity=self._build_run_identity(scenario),
                    status=RunStatus.failed,
                    failures=(
                        FailureRecord(
                            failure_kind=FailureKind.harness_defect,
                            message="Strategy does not support begin_run",
                            stage="configuration",
                        ),
                    ),
                    duration_seconds=time.monotonic() - start_time,
                )
            begin_run(self._isolation.workspace.root)

            requirement_delta = f"{requirement_change.before} -> {requirement_change.after}"
            executor = SharedRegenerationExecutor(self._backend)

            selection_total_prompt = 0
            selection_total_completion = 0
            selection_total_tok = 0
            selection_calls = 0
            selection_dur = 0.0
            selection_tool_calls = 0
            selection_tool_duration = 0.0
            selection_inspected = 0

            regen_total_prompt = 0
            regen_total_completion = 0
            regen_total_tok = 0
            regen_calls = 0
            regen_dur = 0.0

            val_dur = 0.0
            all_failures: list[FailureRecord] = []
            total_regenerated = 0
            final_prediction: ImpactPrediction | None = None
            last_exec_result: RegenerationExecutionResult | None = None
            last_feedback_channels: tuple[int, str, str] | None = None
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
                    strategy_model_calls_before = getattr(self._strategy, "model_call_count", 0)
                    strategy_tool_calls_before = getattr(self._strategy, "tool_call_count", 0)
                    strategy_tool_dur_before = getattr(self._strategy, "tool_duration_seconds", 0.0)
                    strategy_inspected_before = getattr(self._strategy, "inspected_file_count", 0)

                    selection_start = time.monotonic()
                    prediction = self._strategy.analyze_impact(
                        repository=repository_snapshot,
                        requirement_change=requirement_change,
                        artifact_universe=artifact_universe,
                        max_tokens=self._budget.remaining_tokens,
                    )
                    sel_dur = time.monotonic() - selection_start
                    selection_dur += sel_dur

                    mc_after = getattr(self._strategy, "model_call_count", 0)
                    tc_after = getattr(self._strategy, "tool_call_count", 0)
                    td_after = getattr(self._strategy, "tool_duration_seconds", 0.0)
                    ic_after = getattr(self._strategy, "inspected_file_count", 0)
                    selection_calls += (mc_after - strategy_model_calls_before)
                    selection_tool_calls += (tc_after - strategy_tool_calls_before)
                    selection_tool_duration += (td_after - strategy_tool_dur_before)
                    selection_inspected += (ic_after - strategy_inspected_before)
                else:
                    last_sci = self._last_scientific_result
                    if last_sci is None:
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

                    strategy_model_calls_before = getattr(self._strategy, "model_call_count", 0)
                    strategy_tool_calls_before = getattr(self._strategy, "tool_call_count", 0)
                    strategy_tool_dur_before = getattr(self._strategy, "tool_duration_seconds", 0.0)
                    strategy_inspected_before = getattr(self._strategy, "inspected_file_count", 0)

                    fb = last_feedback_channels
                    if fb is None:
                        fb = self._scientific_feedback_channels(last_sci)
                    channels = fb
                    ec, so, se = channels
                    selection_start = time.monotonic()
                    prediction = revise_plan(
                        requirement_change=requirement_change,
                        artifact_universe=artifact_universe,
                        previous_prediction=final_prediction or prediction,
                        exit_code=ec,
                        val_stdout=so,
                        val_stderr=se,
                        workspace_summary=workspace_summary,
                        remaining_attempts=self._budget.remaining_attempts,
                        remaining_tokens=self._budget.remaining_tokens,
                    )
                    sel_dur = time.monotonic() - selection_start
                    selection_dur += sel_dur

                    mc_after = getattr(self._strategy, "model_call_count", 0)
                    tc_after = getattr(self._strategy, "tool_call_count", 0)
                    td_after = getattr(self._strategy, "tool_duration_seconds", 0.0)
                    ic_after = getattr(self._strategy, "inspected_file_count", 0)
                    selection_calls += (mc_after - strategy_model_calls_before)
                    selection_tool_calls += (tc_after - strategy_tool_calls_before)
                    selection_tool_duration += (td_after - strategy_tool_dur_before)
                    selection_inspected += (ic_after - strategy_inspected_before)

                final_prediction = prediction
                tok = prediction.token_usage or TokenUsage()
                selection_total_prompt += tok.prompt_tokens
                selection_total_completion += tok.completion_tokens
                selection_total_tok += tok.total_tokens
                # selection_calls is now tracked via deltas from strategy, no longer 1 per iteration
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

                sci_result = self._execute_scientific_validation(scenario, exec_result)
                has_validation_run = True

                regen_total_prompt += exec_result.prompt_tokens
                regen_total_completion += exec_result.completion_tokens
                regen_total_tok += exec_result.total_tokens
                regen_calls += exec_result.model_calls
                regen_dur += exec_result.duration_seconds
                val_dur += sci_result.duration_seconds if sci_result is not None else 0.0
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

                if sci_result is not None and sci_result.passed and not exec_result.failures:
                    total_regenerated = sum(
                        1 for a in exec_result.artifacts if a.status == "generated"
                    )
                    selection_total = selection_total_prompt + selection_total_completion
                    total_tok = selection_total + regen_total_tok
                    total_calls_val = selection_calls + regen_calls
                    total_dur_val = selection_dur + regen_dur + val_dur
                    fields = self._scientific_record_fields(sci_result)

                    tool_transcript = tuple(getattr(self._strategy, "compact_tool_transcript", ()))
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
                        selection_tool_calls=selection_tool_calls,
                        selection_tool_duration_seconds=selection_tool_duration,
                        selection_inspected_file_count=selection_inspected,
                        selection_tool_transcript=tool_transcript,
                        regeneration_prompt_tokens=regen_total_prompt,
                        regeneration_completion_tokens=regen_total_completion,
                        regeneration_total_tokens=regen_total_tok,
                        regeneration_model_calls=regen_calls,
                        regeneration_duration_seconds=regen_dur,
                        **fields,
                        total_workflow_tokens=total_tok,
                        total_workflow_model_calls=total_calls_val,
                        total_workflow_duration_seconds=total_dur_val,
                        selected_artifact_count=counts.get("selected", 0),
                        regenerated_artifact_count=total_regenerated,
                        preserved_artifact_count=counts.get("preserve", 0),
                        unresolved_human_review_count=counts.get("human_review", 0),
                    )

                if sci_result is not None and not sci_result.passed:
                    all_failures.append(
                        self._failure_from_scientific_result(sci_result)
                    )
                elif exec_result.failures:
                    all_failures.append(
                        FailureRecord(
                            failure_kind=FailureKind.model_output,
                            message="Executor failures present",
                            details="; ".join(exec_result.failures)[:1000],
                            stage="regeneration",
                        )
                    )

                if sci_result is not None and not sci_result.passed:
                    last_feedback_channels = self._scientific_feedback_channels(sci_result)
                elif exec_result.failures:
                    last_feedback_channels = (-1, "", "; ".join(exec_result.failures)[:1000])
                else:
                    last_feedback_channels = None

                total_regenerated = sum(
                    1 for a in exec_result.artifacts if a.status == "generated"
                )

                if not self._budget.can_attempt:
                    break

                last_requires_iteration = getattr(self._strategy, "last_requires_iteration", True)
                if not last_requires_iteration:
                    break

            self._state.fail()
            tool_transcript = tuple(getattr(self._strategy, "compact_tool_transcript", ()))
            selection_total = selection_total_prompt + selection_total_completion
            total_tokens = selection_total + regen_total_tok
            total_calls = selection_calls + regen_calls
            total_dur = selection_dur + regen_dur + val_dur
            sci = self._last_scientific_result
            fields = self._scientific_record_fields(sci)

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
                selection_tool_calls=selection_tool_calls,
                selection_tool_duration_seconds=selection_tool_duration,
                selection_inspected_file_count=selection_inspected,
                selection_tool_transcript=tool_transcript,
                regeneration_prompt_tokens=regen_total_prompt,
                regeneration_completion_tokens=regen_total_completion,
                regeneration_total_tokens=regen_total_tok,
                regeneration_model_calls=regen_calls,
                regeneration_duration_seconds=regen_dur,
                **fields,
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
            return ArtifactUniverse(
                artifacts=resolve_allowed_artifacts(
                    self._active_snapshot(),
                    self._config.editable_artifact_paths,
                )
            )

        # Legacy impact-only fixture compatibility only.
        return ArtifactUniverse(
            artifacts=scenario.expected_affected_artifacts
        )

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
