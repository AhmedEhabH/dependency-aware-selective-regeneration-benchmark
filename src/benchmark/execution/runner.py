from __future__ import annotations

import json
import logging
import re
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
    RegenerationScenarioContext,
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

logger = logging.getLogger(__name__)


_EXTERNAL_RUNTIME_MODULES = frozenset(
    {
        "accelerate",
        "bitsandbytes",
        "django",
        "pytest",
        "pytest_django",
        "rest_framework",
        "torch",
        "transformers",
    }
)
_MISSING_MODULE_RE = re.compile(r"no module named ['\"]([^'\"]+)['\"]", re.IGNORECASE)
_TRACEBACK_ROOT_RE = re.compile(
    r"^(?P<kind>[A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception)):\s*(?P<message>.*)$",
    re.MULTILINE,
)


def _compact_head_tail(text: str, *, head: int = 500, tail: int = 1800) -> str:
    """Compact command output while retaining the traceback root at the end."""
    if not text:
        return ""
    if len(text) <= head + tail + 32:
        return text
    omitted = len(text) - head - tail
    return f"{text[:head]}\n... [{omitted} chars omitted] ...\n{text[-tail:]}"


def _extract_root_cause(stderr: str, stdout: str = "") -> str:
    """Extract the last exception line or last non-empty output line."""
    combined = f"{stdout}\n{stderr}"
    matches = list(_TRACEBACK_ROOT_RE.finditer(combined))
    if matches:
        match = matches[-1]
        return f"{match.group('kind')}: {match.group('message')}".strip()
    lines = [line.strip() for line in combined.splitlines() if line.strip()]
    return lines[-1] if lines else "(root cause unavailable)"


def _format_prior_generation_failures(failures: tuple[FailureRecord, ...] | list[FailureRecord]) -> str:
    messages: list[str] = []
    for failure in failures:
        if failure.stage != "regeneration":
            continue
        if failure.message not in messages:
            messages.append(failure.message)
    if not messages:
        return "- (none recorded)"
    return "\n".join(
        f"- {_compact_head_tail(message, head=400, tail=800)}"
        for message in messages[:10]
    )


@dataclass
class _WorkflowMetricAccumulator:
    selection_prompt_tokens: int = 0
    selection_completion_tokens: int = 0
    selection_model_calls: int = 0
    selection_duration_seconds: float = 0.0
    selection_tool_calls: int = 0
    selection_tool_duration_seconds: float = 0.0
    selection_inspected_file_count: int = 0

    regeneration_prompt_tokens: int = 0
    regeneration_completion_tokens: int = 0
    regeneration_model_calls: int = 0
    regeneration_duration_seconds: float = 0.0

    repair_prompt_tokens: int = 0
    repair_completion_tokens: int = 0
    repair_model_calls: int = 0
    repair_duration_seconds: float = 0.0
    repair_attempts: int = 0

    migration_duration_seconds: float = 0.0
    baseline_validation_duration_seconds: float = 0.0
    scenario_evaluator_duration_seconds: float = 0.0

    @classmethod
    def from_record(cls, record: RunRecord) -> _WorkflowMetricAccumulator:
        return cls(
            selection_prompt_tokens=record.selection_prompt_tokens,
            selection_completion_tokens=record.selection_completion_tokens,
            selection_model_calls=record.selection_model_calls,
            selection_duration_seconds=record.selection_duration_seconds,
            selection_tool_calls=record.selection_tool_calls,
            selection_tool_duration_seconds=record.selection_tool_duration_seconds,
            selection_inspected_file_count=record.selection_inspected_file_count,
            regeneration_prompt_tokens=record.regeneration_prompt_tokens,
            regeneration_completion_tokens=record.regeneration_completion_tokens,
            regeneration_model_calls=record.regeneration_model_calls,
            regeneration_duration_seconds=record.regeneration_duration_seconds,
            repair_prompt_tokens=record.repair_prompt_tokens,
            repair_completion_tokens=record.repair_completion_tokens,
            repair_model_calls=record.repair_model_calls,
            repair_duration_seconds=record.repair_duration_seconds,
            repair_attempts=record.repair_attempts,
            migration_duration_seconds=record.migration_duration_seconds,
            baseline_validation_duration_seconds=record.baseline_validation_duration_seconds,
            scenario_evaluator_duration_seconds=record.scenario_evaluator_duration_seconds,
        )

    def add_selection(
        self,
        usage: TokenUsage,
        *,
        model_calls: int,
        duration_seconds: float,
        tool_calls: int = 0,
        tool_duration_seconds: float = 0.0,
        inspected_file_count: int = 0,
    ) -> None:
        self.selection_prompt_tokens += usage.prompt_tokens
        self.selection_completion_tokens += usage.completion_tokens
        self.selection_model_calls += model_calls
        self.selection_duration_seconds += duration_seconds
        self.selection_tool_calls += tool_calls
        self.selection_tool_duration_seconds += tool_duration_seconds
        self.selection_inspected_file_count += inspected_file_count

    def add_code_generation(
        self,
        result: RegenerationExecutionResult,
        *,
        is_repair: bool,
    ) -> None:
        if is_repair:
            self.repair_prompt_tokens += result.prompt_tokens
            self.repair_completion_tokens += result.completion_tokens
            self.repair_model_calls += result.model_calls
            self.repair_duration_seconds += result.duration_seconds
            self.repair_attempts += 1
        else:
            self.regeneration_prompt_tokens += result.prompt_tokens
            self.regeneration_completion_tokens += result.completion_tokens
            self.regeneration_model_calls += result.model_calls
            self.regeneration_duration_seconds += result.duration_seconds

    def add_scientific(
        self,
        result: _ScientificValidationResult,
    ) -> None:
        if result.migration is not None:
            self.migration_duration_seconds += result.migration.duration_seconds
        if result.baseline is not None:
            self.baseline_validation_duration_seconds += result.baseline.duration_seconds
        if result.evaluator is not None:
            self.scenario_evaluator_duration_seconds += result.evaluator.duration_seconds

    def as_record_fields(
        self,
        *,
        final_scientific_result: _ScientificValidationResult | None,
        token_accounting_mode: str,
    ) -> dict[str, Any]:
        fields: dict[str, Any] = {
            "selection_prompt_tokens": self.selection_prompt_tokens,
            "selection_completion_tokens": self.selection_completion_tokens,
            "selection_total_tokens": self.selection_prompt_tokens + self.selection_completion_tokens,
            "selection_model_calls": self.selection_model_calls,
            "selection_duration_seconds": self.selection_duration_seconds,
            "selection_tool_calls": self.selection_tool_calls,
            "selection_tool_duration_seconds": self.selection_tool_duration_seconds,
            "selection_inspected_file_count": self.selection_inspected_file_count,
            "regeneration_prompt_tokens": self.regeneration_prompt_tokens,
            "regeneration_completion_tokens": self.regeneration_completion_tokens,
            "regeneration_total_tokens": self.regeneration_prompt_tokens + self.regeneration_completion_tokens,
            "regeneration_model_calls": self.regeneration_model_calls,
            "regeneration_duration_seconds": self.regeneration_duration_seconds,
            "repair_prompt_tokens": self.repair_prompt_tokens,
            "repair_completion_tokens": self.repair_completion_tokens,
            "repair_total_tokens": self.repair_prompt_tokens + self.repair_completion_tokens,
            "repair_model_calls": self.repair_model_calls,
            "repair_duration_seconds": self.repair_duration_seconds,
            "repair_attempts": self.repair_attempts,
            "token_accounting_mode": token_accounting_mode,
            "migration_duration_seconds": self.migration_duration_seconds,
            "baseline_validation_duration_seconds": self.baseline_validation_duration_seconds,
            "scenario_evaluator_duration_seconds": self.scenario_evaluator_duration_seconds,
            "total_workflow_tokens": (
                self.selection_prompt_tokens + self.selection_completion_tokens
                + self.regeneration_prompt_tokens + self.regeneration_completion_tokens
                + self.repair_prompt_tokens + self.repair_completion_tokens
            ),
            "total_workflow_model_calls": (
                self.selection_model_calls
                + self.regeneration_model_calls
                + self.repair_model_calls
            ),
            "total_workflow_duration_seconds": (
                self.selection_duration_seconds
                + self.regeneration_duration_seconds
                + self.repair_duration_seconds
                + self.migration_duration_seconds
                + self.baseline_validation_duration_seconds
                + self.scenario_evaluator_duration_seconds
            ),
        }
        if final_scientific_result is not None:
            sci_fields = _scientific_record_fields_static(final_scientific_result)
            cumulative_durations = {
                "migration_duration_seconds",
                "baseline_validation_duration_seconds",
                "scenario_evaluator_duration_seconds",
            }
            for k, v in sci_fields.items():
                if k not in cumulative_durations:
                    fields[k] = v
        return fields


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
    validation_env: dict[str, str] = field(default_factory=dict)
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
            raise ValueError("RunnerConfig.max_completion_tokens_per_call must be integer, not bool")
        if isinstance(self.validation_timeout, bool) or self.validation_timeout <= 0:
            n = self.validation_timeout
            raise ValueError(f"RunnerConfig.validation_timeout must be a positive integer, got {n}")
        if isinstance(self.max_total_workflow_tokens, bool):
            raise ValueError("RunnerConfig.max_total_workflow_tokens must be integer, not bool")
        if isinstance(self.max_tokens, bool):
            raise ValueError("RunnerConfig.max_tokens must be integer, not bool")
        if self.max_completion_tokens_per_call <= 0:
            n = self.max_completion_tokens_per_call
            raise ValueError(f"RunnerConfig.max_completion_tokens_per_call must be > 0, got {n}")
        if self.max_total_workflow_tokens < 0:
            n = self.max_total_workflow_tokens
            raise ValueError(f"RunnerConfig.max_total_workflow_tokens must be >= 0, got {n}")
        if self.max_tokens < 0:
            n = self.max_tokens
            raise ValueError(f"RunnerConfig.max_tokens must be >= 0, got {n}")
        if isinstance(self.agent_control_max_completion_tokens, bool):
            raise ValueError(
                "RunnerConfig.agent_control_max_completion_tokens must be integer, not bool"
            )
        if self.agent_control_max_completion_tokens <= 0:
            n = self.agent_control_max_completion_tokens
            raise ValueError(
                "RunnerConfig.agent_control_max_completion_tokens must be > 0, got {n}"
            )
        _ = self.resolved_max_total_workflow_tokens

    @property
    def resolved_max_total_workflow_tokens(self) -> int:
        explicit_total = self.max_total_workflow_tokens
        legacy_total = self.max_tokens
        if explicit_total > 0 and legacy_total > 0 and explicit_total != legacy_total:
            raise ValueError(
                f"Explicit max_total_workflow_tokens ({explicit_total}) and "
                f"legacy max_tokens ({legacy_total}) are both positive but differ"
            )
        if explicit_total > 0:
            return explicit_total
        if legacy_total > 0:
            return legacy_total
        return 0


def _scientific_record_fields_static(
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
            max_tokens=config.resolved_max_total_workflow_tokens,
            timeout_seconds=config.timeout_seconds,
        )
        self._last_prediction: ImpactPrediction | None = None
        self._last_scientific_result: _ScientificValidationResult | None = None
        self._last_regeneration_hashes: dict[str, str] = {}

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
            logger.info("STAGE_START scenario=%s stage=generation_guard", scenario.scenario_id)
            stage_start = time.monotonic()
            er = exec_result
            model_calls = getattr(er, "model_calls", 0)
            artifacts = getattr(er, "artifacts", [])
            generated_count = sum(
                1 for a in artifacts if getattr(a, "status", "") == "generated"
            )
            if model_calls == 0 or generated_count == 0:
                feedback_parts.append("Generation guard: no model calls or no generated source")
                logger.info(
                    "STAGE_END scenario=%s stage=generation_guard passed=False elapsed=%.3f",
                    scenario.scenario_id, time.monotonic() - stage_start,
                )
                return _build(False, "generation_guard", FailureKind.build)
            logger.info(
                "STAGE_END scenario=%s stage=generation_guard passed=True elapsed=%.3f",
                scenario.scenario_id, time.monotonic() - stage_start,
            )

        # Stage 2 — post-generation migration
        pgc = scenario.post_generation_command
        if scenario.require_new_migration and not pgc:
            feedback_parts.append("Harness defect: require_new_migration=True but command is empty")
            return _build(False, "configuration", FailureKind.harness_defect)
        if pgc:
            logger.info("STAGE_START scenario=%s stage=migration_generation", scenario.scenario_id)
            stage_start = time.monotonic()
            from benchmark.execution.post_generation import run_post_generation_command
            migration_result = run_post_generation_command(
                workspace_root=self._isolation.workspace.root,
                command=pgc,
                require_new_migration=scenario.require_new_migration,
                migration_directory=scenario.migration_directory,
                timeout=self._config.validation_timeout,
                resolved_interpreter=self._config.validation_python,
                env=self._config.validation_env,
            )
            if not migration_result.passed:
                m_stdout = _compact_head_tail(migration_result.stdout)
                m_stderr = _compact_head_tail(migration_result.stderr)
                feedback_parts.append(f"Migration failed: exit={migration_result.exit_code}")
                if m_stdout:
                    feedback_parts.append(f"stdout: {m_stdout}")
                if m_stderr:
                    feedback_parts.append(f"stderr: {m_stderr}")
                logger.info(
                    "STAGE_END scenario=%s stage=migration_generation passed=False elapsed=%.3f",
                    scenario.scenario_id, time.monotonic() - stage_start,
                )
                return _build(False, "migration_generation", FailureKind.build)
            logger.info(
                "STAGE_END scenario=%s stage=migration_generation passed=True elapsed=%.3f",
                scenario.scenario_id, time.monotonic() - stage_start,
            )

        # Stage 3 — baseline validation
        validation_command = self._config.validation_command
        if validation_command:
            logger.info("STAGE_START scenario=%s stage=baseline_validation", scenario.scenario_id)
            stage_start = time.monotonic()
            validator = FunctionalValidator()
            baseline_result = validator.validate(
                workspace_root=self._isolation.workspace.root,
                command=validation_command,
                timeout=self._config.validation_timeout,
                env=dict(self._config.validation_env),
            )
            if not baseline_result.passed:
                b_stdout = _compact_head_tail(baseline_result.stdout)
                b_stderr = _compact_head_tail(baseline_result.stderr)
                feedback_parts.append(
                    f"Baseline validation failed (exit={baseline_result.exit_code})"
                )
                if b_stdout:
                    feedback_parts.append(f"stdout: {b_stdout}")
                if b_stderr:
                    feedback_parts.append(f"stderr: {b_stderr}")
                logger.info(
                    "STAGE_END scenario=%s stage=baseline_validation passed=False elapsed=%.3f",
                    scenario.scenario_id, time.monotonic() - stage_start,
                )
                return _build(False, "baseline_validation", FailureKind.build)
            logger.info(
                "STAGE_END scenario=%s stage=baseline_validation passed=True elapsed=%.3f",
                scenario.scenario_id, time.monotonic() - stage_start,
            )

        # Stage 4 — isolated scenario evaluator
        evaluator_asset = scenario.evaluator_asset
        if evaluator_asset:
            logger.info("STAGE_START scenario=%s stage=scenario_evaluator", scenario.scenario_id)
            stage_start = time.monotonic()
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
                e_error = _compact_head_tail(evaluator_result.error)
                e_checks = evaluator_result.checks
                check_str = ", ".join(str(c) for c in e_checks[:5]) if e_checks else ""
                feedback_parts.append("Scenario evaluator failed")
                if check_str:
                    feedback_parts.append(f"checks: {check_str}")
                if e_error:
                    feedback_parts.append(f"error: {e_error}")
                logger.info(
                    "STAGE_END scenario=%s stage=scenario_evaluator passed=False elapsed=%.3f",
                    scenario.scenario_id, time.monotonic() - stage_start,
                )
                return _build(False, "scenario_evaluator", FailureKind.build)
            logger.info(
                "STAGE_END scenario=%s stage=scenario_evaluator passed=True elapsed=%.3f",
                scenario.scenario_id, time.monotonic() - stage_start,
            )

        # Stage 5 — final success decision
        return _build(True, None, None)

    # -------------------------------------------------------------------
    # RF-2: 5 private helpers
    # -------------------------------------------------------------------

    def _requires_scenario_evaluator(self, scenario: Scenario) -> bool:
        # D13r1 F3: the scenario evaluator is coupled ONLY to ``evaluator_asset``.
        # Post-generation migration execution (``post_generation_command`` /
        # ``require_new_migration``) is a standalone scientific stage and must
        # NOT drag an evaluator requirement behind it (a migration-only scenario
        # with no evaluator_asset is valid and must run its migration stage).
        return bool(scenario.evaluator_asset)

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
        # D13r1 F3: a migration-only scenario (post_generation_command /
        # require_new_migration WITHOUT evaluator_asset) is a valid configuration
        # — migration execution is decoupled from the scenario evaluator.
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
        return _scientific_record_fields_static(result)

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
            details=_compact_head_tail(result.feedback) if result.feedback else "",
            stage=stage,
        )

    def _scientific_feedback_channels(
        self,
        result: _ScientificValidationResult,
    ) -> tuple[int, str, str]:
        stage = result.failed_stage
        if stage == "migration_generation" and result.migration is not None:
            ec = result.migration.exit_code
            so = _compact_head_tail(result.migration.stdout)
            se = _compact_head_tail(result.migration.stderr)
        elif stage == "baseline_validation" and result.baseline is not None:
            ec = result.baseline.exit_code
            so = _compact_head_tail(result.baseline.stdout)
            se = _compact_head_tail(result.baseline.stderr)
        elif stage == "scenario_evaluator" and result.evaluator is not None:
            ec = result.evaluator.exit_code
            so = _compact_head_tail(result.evaluator.stdout)
            parts = []
            if result.evaluator.stderr:
                parts.append(_compact_head_tail(result.evaluator.stderr))
            if result.evaluator.error:
                parts.append(_compact_head_tail(result.evaluator.error))
            if result.evaluator.checks:
                parts.append("checks: " + ", ".join(str(c) for c in result.evaluator.checks[:5]))
            se = "; ".join(parts)
        else:
            ec = -1
            so = ""
            se = _compact_head_tail(result.feedback) if result.feedback else ""
        return ec, so, se

    def _build_repair_context(
        self,
        result: _ScientificValidationResult | None,
        failures: tuple[FailureRecord, ...] | list[FailureRecord],
    ) -> str | None:
        """Build repair evidence without truncating away the root exception."""
        generation_failures = _format_prior_generation_failures(failures)
        if result is None or result.passed:
            if generation_failures == "- (none recorded)":
                return None
            return REPAIR_CONTEXT_PROMPT_TEMPLATE.format(
                stage="regeneration",
                exit_code=-1,
                root_cause="Generation/scope output was rejected",
                generation_failures=generation_failures,
                stdout="(none)",
                stderr="(none)",
            )
        ec, so, se = self._scientific_feedback_channels(result)
        return REPAIR_CONTEXT_PROMPT_TEMPLATE.format(
            stage=result.failed_stage or "scientific_validation",
            exit_code=ec,
            root_cause=_extract_root_cause(se, so),
            generation_failures=generation_failures,
            stdout=so or "(none)",
            stderr=se or "(none)",
        )

    @staticmethod
    def classify_validation_repairability(
        *,
        exit_code: int,
        stdout: str,
        stderr: str,
        stage: str,  # noqa: ARG004  (pre-existing; reserved for classification context)
    ) -> str:
        """Classify a validation failure as repairable_code or infrastructure_nonrepairable.

        Infrastructure failures (missing modules/dependencies, missing
        executables, exit code 127, GPU/model/resource failures) are never
        repairable by the LLM; the Run must stop without entering the repair
        loop. Only generated-code, migration-content, baseline-test, and
        evaluator failures may be repairable.
        """
        combined_raw = f"{stdout}\n{stderr}"
        combined = combined_raw.lower()
        if exit_code == 127:
            return "infrastructure_nonrepairable"
        if any(
            marker in combined
            for marker in (
                "command not found",
                "executable not found",
                "no such file or directory: 'python'",
                "dependency_import_verification: fail",
                "kaggle smoke preflight failed",
            )
        ):
            return "infrastructure_nonrepairable"
        if any(
            marker in combined
            for marker in (
            "outofmemory",
            "out of memory",
            "cuda error",
            "cuda out of memory",
            "failed to allocate",
            )
        ):
            return "infrastructure_nonrepairable"

        # Missing declared third-party runtime packages are infrastructure.
        # Missing project-local modules and ordinary ImportError/cannot-import
        # failures are generated-code defects and remain repairable.
        missing = _MISSING_MODULE_RE.search(combined_raw)
        if missing is not None:
            missing_module = missing.group(1)
            if missing_module in _EXTERNAL_RUNTIME_MODULES:
                return "infrastructure_nonrepairable"
        return "repairable_code"

    def _infrastructure_failure_from_scientific_result(
        self,
        result: _ScientificValidationResult,
    ) -> FailureRecord:
        """Create one truthful infrastructure failure without duplication."""
        ec, so, se = self._scientific_feedback_channels(result)
        original = self._failure_from_scientific_result(result)
        evidence = [
            "classification=infrastructure_nonrepairable",
            f"original_kind={original.failure_kind.value}",
            f"stage={result.failed_stage or 'scientific_validation'}",
            f"exit_code={ec}",
        ]
        if so:
            evidence.append(f"stdout={_compact_head_tail(so, head=300, tail=1200)}")
        if se:
            evidence.append(f"stderr={_compact_head_tail(se, head=300, tail=1200)}")
        return FailureRecord(
            failure_kind=FailureKind.infrastructure_nonrepairable,
            message=original.message,
            details=" | ".join(evidence),
            stage=result.failed_stage or "scientific_validation",
        )

    def _build_scenario_context(self, scenario: Scenario) -> RegenerationScenarioContext:
        if self._config.scientific_gold_isolation:
            # D046 / PA-001: the scientific profile is fail-closed against gold
            # leakage. expected_actions (gold) and gold artifact_instructions are
            # NEVER exposed to generation/repair prompts. Visible requirements,
            # acceptance criteria, and architecture constraints may still be shared.
            return RegenerationScenarioContext(
                scenario_id=scenario.scenario_id,
                requirement_before=scenario.requirement_before,
                requirement_after=scenario.requirement_after,
                acceptance_criteria=tuple(
                    c.description for c in scenario.acceptance_criteria
                ),
                architecture_constraints=tuple(
                    c.description for c in scenario.architecture_constraints
                ),
                expected_actions=(),
                artifact_instructions=(),
                gold_isolated=True,
            )
        expected_actions: list[tuple[str, str]] = []
        for ref, action in scenario.expected_actions:
            if action == ActionKind.regenerate:
                label = "create" if ref.path.endswith("/") else "modify"
                expected_actions.append((ref.path, label))
        return RegenerationScenarioContext(
            scenario_id=scenario.scenario_id,
            requirement_before=scenario.requirement_before,
            requirement_after=scenario.requirement_after,
            acceptance_criteria=tuple(
                c.description for c in scenario.acceptance_criteria
            ),
            architecture_constraints=tuple(
                c.description for c in scenario.architecture_constraints
            ),
            expected_actions=tuple(expected_actions),
            artifact_instructions=scenario.expected_artifact_instructions,
        )

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
                "impact_plan",
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
        # D9: install the cooperative in-flight deadline guard on the strategy AND
        # the shared backend for every run, so the backend never retains a prior
        # run's deadline guard. Must happen before any model call.
        self._apply_model_call_guards()

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
                record = self._workflow_budget_exhausted_record(
                    scenario,
                    start_time,
                    "Budget exhausted before initial generation attempt",
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
                else:
                    result = self._reclassify_infrastructure_failure(result)
                    if self._is_repairable_failure(result) and self._budget.can_attempt:
                        record = self._run_regeneration_repair_flow(
                            scenario=scenario,
                            first_record=result,
                            start_time=start_time,
                        )
                    else:
                        if result.status == RunStatus.succeeded:
                            self._state.succeed()
                        elif not self._state.is_terminal:
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

    def _workflow_budget_exhausted_record(
        self,
        scenario: Scenario,
        start_time: float,
        message: str,
        *,
        acc: _WorkflowMetricAccumulator | None = None,
        token_accounting_mode: str = "unknown",
    ) -> RunRecord:
        """Model/strategy workflow budget exhaustion is a scientific terminal outcome.

        Cooperative model-call boundary: the deadline is checked before every
        selection, generation, and repair model call, and no new call is
        started after the deadline. This is a cooperative boundary in the
        benchmark process, NOT an unsafe kill of a GPU thread. Preflight,
        model-loading, environment, harness, and required-HF timeouts remain
        engineering blockers and are classified elsewhere.

        ``acc`` (when provided) preserves the calls/tokens already consumed
        before the deadline fired; ``regenerated_artifact_count`` is always
        zero because no attempt is committed under the atomic contract.
        """
        elapsed = time.monotonic() - start_time
        budget_note = (
            f"configured_budget={{max_attempts={self._budget.max_attempts};"
            f"max_total_workflow_tokens={self._config.resolved_max_total_workflow_tokens};"
            f"timeout_seconds={self._config.timeout_seconds}}};"
            f"actual_elapsed_seconds={elapsed:.3f}"
        )
        fields: dict[str, Any] = {}
        if acc is not None:
            fields = acc.as_record_fields(
                final_scientific_result=None,
                token_accounting_mode=token_accounting_mode,
            )
            legacy_prompt = (
                fields["selection_prompt_tokens"]
                + fields["regeneration_prompt_tokens"]
                + fields["repair_prompt_tokens"]
            )
            legacy_completion = (
                fields["selection_completion_tokens"]
                + fields["regeneration_completion_tokens"]
                + fields["repair_completion_tokens"]
            )
            token_usage = TokenUsage(
                prompt_tokens=legacy_prompt,
                completion_tokens=legacy_completion,
                total_tokens=fields["total_workflow_tokens"],
            )
        else:
            token_usage = TokenUsage()
        self._state.fail()
        return RunRecord(
            identity=self._build_run_identity(scenario),
            status=RunStatus.failed,
            token_usage=token_usage,
            failures=(
                FailureRecord(
                    failure_kind=FailureKind.scientific_budget_exhausted,
                    message=f"{message} ({budget_note})",
                    details=budget_note,
                    stage="budget",
                ),
            ),
            duration_seconds=elapsed,
            regenerated_artifact_count=0,
            **fields,
        )

    def _apply_strategy_model_call_guard(self) -> None:
        """Hand the cooperative deadline to any strategy that opts in.

        The iterative agent strategy checks the guard before and after every
        internal selection/revision model call. Standard strategies do not
        implement the optional setter and are unaffected.
        """
        setter = getattr(self._strategy, "set_model_call_guard", None)
        if callable(setter):
            setter(lambda: not self._budget.timed_out)

    def _apply_backend_model_call_guard(self) -> None:
        """Hand the cooperative in-flight deadline to the shared LLM backend.

        Installed for EVERY run so a shared backend can never retain a prior
        run's deadline guard (each Runner owns a fresh ``BudgetManager``; the
        lambda closes over THIS run's budget). Only backends that implement the
        optional setter are affected; Mock/OpenRouter backends are untouched.
        """
        if self._backend is None:
            return
        setter = getattr(self._backend, "set_model_call_guard", None)
        if callable(setter):
            setter(lambda: not self._budget.timed_out)

    def _apply_model_call_guards(self) -> None:
        """Install the cooperative deadline guard on strategy AND backend."""
        self._apply_strategy_model_call_guard()
        self._apply_backend_model_call_guard()

    def _strategy_model_call_budget_exhausted(self) -> bool:
        return bool(getattr(self._strategy, "model_call_budget_exhausted", False))

    def _run_attempt(self, scenario: Scenario, start_time: float) -> RunRecord | BenchmarkError:
        try:
            if self._budget.timed_out:
                return self._workflow_budget_exhausted_record(
                    scenario,
                    start_time,
                    "Workflow deadline reached before selection model call",
                )

            self._apply_strategy_model_call_guard()
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

            if self._strategy_model_call_budget_exhausted():
                return self._workflow_budget_exhausted_record(
                    scenario,
                    start_time,
                    "Workflow deadline reached during selection model calls",
                )

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
            return self._workflow_budget_exhausted_record(
                scenario,
                start_time,
                "Workflow budget exhausted during attempt",
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
        # Stage-C ImpactPlan arm: if the strategy produced a first-class plan,
        # build the executable plan from its write_set (write_set == {R}) and
        # persist the plan BEFORE any source write. Otherwise use the legacy
        # selector path (unchanged).
        impact_plan = prediction.impact_plan
        if impact_plan is not None:
            from benchmark.selection.planner import plan_from_impact_plan

            plan = plan_from_impact_plan(impact_plan)
            self._persist_impact_plan(impact_plan, scenario)
        else:
            selector = ArtifactSelector()
            selection = selector.select(prediction, artifact_universe)
            regen_planner = RegenerationPlanner()
            plan = regen_planner.plan(selection, prediction)

        counts = compute_artifact_counts(prediction)

        self._last_prediction = prediction

        selection_tok = prediction.token_usage or TokenUsage()
        if selection_tok.total_tokens > 0:
            self._budget.record_tokens(selection_tok.total_tokens)

        requirement_delta = f"{requirement_change.before} -> {requirement_change.after}"
        assert self._backend is not None
        executor = SharedRegenerationExecutor(
            self._backend,
            can_start_model_call=lambda: not self._budget.timed_out,
        )

        token_accounting_mode = getattr(
            self._backend, "token_accounting_mode", "unknown"
        )

        acc = _WorkflowMetricAccumulator()
        acc.add_selection(
            selection_tok,
            model_calls=int(getattr(self._strategy, "model_call_count", 0)),
            duration_seconds=selection_duration,
        )

        # --- planner cost for the impact-plan arm (counted in proposed total) ---
        impact_plan_hash = ""
        impact_plan_version = ""
        impact_plan_parent_hash: str | None = None
        planner_metrics = self._impact_plan_metrics(impact_plan)

        if self._budget.timed_out:
            return self._workflow_budget_exhausted_record(
                scenario,
                start_time,
                "Workflow deadline reached before generation model call",
            )

        exec_result = executor.execute(
            plan, self._isolation, requirement_delta=requirement_delta,
            scenario_context=self._build_scenario_context(scenario),
            max_completion_tokens_per_call=self._config.max_completion_tokens_per_call,
            remaining_total_workflow_tokens=self._budget.runtime_remaining_total_tokens,
            enable_exact_patch=self._config.exact_patch,
        )

        self._budget.record_tokens(exec_result.total_tokens)

        self._last_regeneration_hashes = dict(exec_result.artifact_hashes)

        if exec_result.model_call_budget_exhausted:
            acc.add_code_generation(exec_result, is_repair=False)
            return self._workflow_budget_exhausted_record(
                scenario,
                start_time,
                "Workflow deadline reached during generation model calls",
                acc=acc,
                token_accounting_mode=token_accounting_mode,
            )

        sci_result = self._execute_scientific_validation(scenario, exec_result)

        acc.add_code_generation(exec_result, is_repair=False)
        if sci_result is not None:
            acc.add_scientific(sci_result)

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

        # --- one bounded expansion (v2) for the impact-plan arm ---
        expansion_count = 0
        escalated_to_h = False
        if (
            impact_plan is not None
            and sci_result is not None
            and not sci_result.passed
            and impact_plan.plan_version == "v1"
        ):
            expand = getattr(self._strategy, "expand_plan", None)
            if callable(expand):
                v2_prediction = self._expand_plan_once(
                    scenario=scenario,
                    requirement_change=requirement_change,
                    artifact_universe=artifact_universe,
                    strategy_expand=expand,
                    failure_summary=(sci_result.feedback or "validation failed"),
                    parent_plan=impact_plan,
                )
                if v2_prediction is not None and v2_prediction.impact_plan is not None:
                    v2_plan_obj = v2_prediction.impact_plan
                    v2_plan = plan_from_impact_plan(v2_plan_obj)
                    self._persist_impact_plan(v2_plan_obj, scenario)
                    v2_tok = v2_prediction.token_usage or TokenUsage()
                    acc.add_selection(
                        v2_tok,
                        model_calls=int(getattr(self._strategy, "model_call_count", 0)),
                        duration_seconds=0.0,
                    )
                    v2_exec = executor.execute(
                        v2_plan, self._isolation, requirement_delta=requirement_delta,
                        scenario_context=self._build_scenario_context(scenario),
                        max_completion_tokens_per_call=self._config.max_completion_tokens_per_call,
                        remaining_total_workflow_tokens=self._budget.runtime_remaining_total_tokens,
                        enable_exact_patch=self._config.exact_patch,
                    )
                    self._budget.record_tokens(v2_exec.total_tokens)
                    v2_sci = self._execute_scientific_validation(scenario, v2_exec)
                    acc.add_code_generation(v2_exec, is_repair=True)
                    if v2_sci is not None:
                        acc.add_scientific(v2_sci)
                    expansion_count += 1
                    if v2_exec.model_call_budget_exhausted:
                        return self._workflow_budget_exhausted_record(
                            scenario,
                            start_time,
                            "Workflow deadline reached during impact-plan expansion",
                            acc=acc,
                            token_accounting_mode=token_accounting_mode,
                        )
                    if v2_sci is not None and v2_sci.passed and not v2_exec.failures:
                        # resolved by v2: succeed below
                        sci_result = v2_sci
                        exec_result = v2_exec
                        failures = []
                        for f_msg in v2_exec.failures:
                            failures.append(
                                FailureRecord(
                                    failure_kind=FailureKind.model_output,
                                    message=f_msg,
                                    details="SharedRegenerationExecutor failure (v2)",
                                    stage="regeneration",
                                )
                            )
                        impact_plan_hash = v2_plan_obj.plan_hash
                        impact_plan_version = v2_plan_obj.plan_version
                        impact_plan_parent_hash = v2_plan_obj.parent_plan_hash
                        planner_metrics = self._impact_plan_metrics(v2_plan_obj)
                    else:
                        escalated_to_h = True
                        failures.append(
                            FailureRecord(
                                failure_kind=FailureKind.build,
                                message=(
                                    "ImpactPlan bounded expansion (v2) exhausted; "
                                    "escalating to HUMAN_REVIEW"
                                ),
                                details=(
                                    f"plan_version={impact_plan.plan_version} parent_hash={impact_plan.plan_hash}"
                                ),
                                stage="human_review",
                            )
                        )
                        if v2_sci is not None and not v2_sci.passed:
                            failures.append(
                                self._failure_from_scientific_result(v2_sci)
                            )
                        impact_plan_hash = v2_plan_obj.plan_hash
                        impact_plan_version = v2_plan_obj.plan_version
                        impact_plan_parent_hash = v2_plan_obj.parent_plan_hash
                        planner_metrics = self._impact_plan_metrics(v2_plan_obj)

        # --- final record assembly ---
        if sci_result is not None and not sci_result.passed and impact_plan is None:
            failures.append(
                self._failure_from_scientific_result(sci_result)
            )
        elif impact_plan is not None and sci_result is not None and not sci_result.passed:
            # Impact-plan arm: if v1 failed and expansion did not resolve the
            # failure (or was not attempted), the v1 failure must be recorded.
            if not escalated_to_h:
                failures.append(
                    self._failure_from_scientific_result(sci_result)
                )
            if expansion_count == 0:
                # No bounded expansion was available/possible -> escalate to H.
                escalated_to_h = True
                failures.append(
                    FailureRecord(
                        failure_kind=FailureKind.build,
                        message=(
                            "ImpactPlan v1 failed and no further bounded expansion "
                            "was possible; escalating to HUMAN_REVIEW"
                        ),
                        details=(
                            f"plan_version={impact_plan.plan_version} "
                            f"parent_hash={impact_plan.parent_plan_hash}"
                        ),
                        stage="human_review",
                    )
                )

        status = RunStatus.failed if failures else RunStatus.succeeded

        regenerated_count = sum(1 for a in exec_result.artifacts if a.status == "generated")
        if impact_plan is not None and impact_plan_hash == "":
            impact_plan_hash = impact_plan.plan_hash
            impact_plan_version = impact_plan.plan_version
            impact_plan_parent_hash = impact_plan.parent_plan_hash
            planner_metrics = self._impact_plan_metrics(impact_plan)

        fields = acc.as_record_fields(
            final_scientific_result=sci_result,
            token_accounting_mode=token_accounting_mode,
        )

        legacy_prompt = (
            fields["selection_prompt_tokens"]
            + fields["regeneration_prompt_tokens"]
            + fields["repair_prompt_tokens"]
        )
        legacy_completion = (
            fields["selection_completion_tokens"]
            + fields["regeneration_completion_tokens"]
            + fields["repair_completion_tokens"]
        )

        return RunRecord(
            identity=self._build_run_identity(scenario),
            status=status,
            prediction=prediction,
            token_usage=TokenUsage(
                prompt_tokens=legacy_prompt,
                completion_tokens=legacy_completion,
                total_tokens=fields["total_workflow_tokens"],
            ),
            duration_seconds=time.monotonic() - start_time,
            failures=tuple(failures),
            **fields,
            selected_artifact_count=counts.get("selected", 0),
            regenerated_artifact_count=regenerated_count,
            preserved_artifact_count=counts.get("preserve", 0),
            unresolved_human_review_count=counts.get("human_review", 0),
            predicted_actions=self._predicted_actions_map(prediction),
            changed_artifact_paths=self._compute_changed_artifact_paths(),
            # Stage-C impact-plan evidence
            impact_plan=None if impact_plan is None else {
                "plan": self._impact_plan_to_dict(impact_plan),
                "final_after_expansion": bool(
                    impact_plan is not None and expansion_count > 0
                ),
            },
            impact_plan_hash=impact_plan_hash,
            impact_plan_version=impact_plan_version,
            impact_plan_parent_hash=impact_plan_parent_hash,
            impact_expansion_count=expansion_count,
            escalated_to_human_review=escalated_to_h,
            prohibited_write_attempts=exec_result.prohibited_write_attempts,
            planner_prompt_tokens=planner_metrics["prompt_tokens"],
            planner_completion_tokens=planner_metrics["completion_tokens"],
            planner_total_tokens=planner_metrics["total_tokens"],
            planner_model_calls=planner_metrics["model_calls"],
            planner_latency_seconds=planner_metrics["latency_seconds"],
        )

    def _is_repairable_failure(self, record: RunRecord) -> bool:
        if record.status != RunStatus.failed:
            return False
        for f in record.failures:
            if f.failure_kind in (
                FailureKind.harness_defect,
                FailureKind.infrastructure,
                FailureKind.infrastructure_nonrepairable,
                FailureKind.timeout,
            ):
                return False
            combined = f"{f.message}\n{f.details}"
            if self.classify_validation_repairability(
                exit_code=-1,
                stdout="",
                stderr=combined,
                stage=f.stage,
            ) == "infrastructure_nonrepairable":
                return False
            if f.stage in (
                "generation_guard", "regeneration", "migration_generation",
                "baseline_validation", "scenario_evaluator",
            ):
                return True
        return False

    def _reclassify_infrastructure_failure(self, record: RunRecord) -> RunRecord:
        """Promote an infrastructure validation failure to the first FailureRecord.

        When the failing scientific validation is infrastructure (missing declared
        runtime package, missing executable, CUDA/OOM, or exit 127), the Run is not
        repairable by the model. The classification must be the first failure so
        ``_is_repairable_failure`` stops without entering the repair loop and the
        persisted failure_classification is truthful.
        """
        last_sci = self._last_scientific_result
        if last_sci is None or last_sci.passed:
            return record
        ec, so, se = self._scientific_feedback_channels(last_sci)
        if self.classify_validation_repairability(
            exit_code=ec,
            stdout=so,
            stderr=se,
            stage=last_sci.failed_stage or "",
        ) != "infrastructure_nonrepairable":
            return record
        infra = self._infrastructure_failure_from_scientific_result(last_sci)
        failures = list(record.failures)
        for index, failure in enumerate(failures):
            if failure.stage == infra.stage:
                failures[index] = infra
                break
        else:
            failures.insert(0, infra)
        return replace(record, failures=tuple(failures))

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
        executor = SharedRegenerationExecutor(
            self._backend,
            can_start_model_call=lambda: not self._budget.timed_out,
        )

        token_accounting_mode = getattr(
            self._backend, "token_accounting_mode", "unknown"
        )

        acc = _WorkflowMetricAccumulator.from_record(first_record)

        all_failures = list(first_record.failures)
        first_regen_count = first_record.regenerated_artifact_count

        repair_context: str | None = None
        last_sci = self._last_scientific_result
        if last_sci is not None and not last_sci.passed:
            ec, so, se = self._scientific_feedback_channels(last_sci)
            repair_context = self._build_repair_context(last_sci, all_failures)
            repairability = self.classify_validation_repairability(
                exit_code=ec,
                stdout=so,
                stderr=se,
                stage=last_sci.failed_stage or "",
            )
            if repairability == "infrastructure_nonrepairable":
                self._state.fail()
                infra = self._infrastructure_failure_from_scientific_result(last_sci)
                retained = tuple(f for f in all_failures if f.stage != infra.stage)
                return replace(
                    first_record,
                    failures=(infra, *retained),
                    duration_seconds=time.monotonic() - start_time,
                )

        while self._budget.can_attempt:
            self._budget.record_attempt()

            prior_hashes = dict(self._last_regeneration_hashes) or None
            exec_result = executor.execute(
                plan, self._isolation, requirement_delta, repair_context=repair_context,
                scenario_context=self._build_scenario_context(scenario),
                max_completion_tokens_per_call=self._config.max_completion_tokens_per_call,
                remaining_total_workflow_tokens=self._budget.runtime_remaining_total_tokens,
                prior_attempt_hashes=prior_hashes,
                enable_exact_patch=self._config.exact_patch,
            )
            self._last_regeneration_hashes = dict(exec_result.artifact_hashes)

            self._budget.record_tokens(exec_result.total_tokens)

            if exec_result.model_call_budget_exhausted:
                acc.add_code_generation(exec_result, is_repair=True)
                return self._workflow_budget_exhausted_record(
                    scenario,
                    start_time,
                    "Workflow deadline reached during regeneration repair calls",
                    acc=acc,
                    token_accounting_mode=token_accounting_mode,
                )

            no_progress = exec_result.repair_no_progress

            sci_result = self._execute_scientific_validation(scenario, exec_result)

            acc.add_code_generation(exec_result, is_repair=True)
            if sci_result is not None:
                acc.add_scientific(sci_result)

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
                fields = acc.as_record_fields(
                    final_scientific_result=sci_result,
                    token_accounting_mode=token_accounting_mode,
                )
                legacy_prompt = (
                    fields["selection_prompt_tokens"]
                    + fields["regeneration_prompt_tokens"]
                    + fields["repair_prompt_tokens"]
                )
                legacy_completion = (
                    fields["selection_completion_tokens"]
                    + fields["regeneration_completion_tokens"]
                    + fields["repair_completion_tokens"]
                )
                return RunRecord(
                    identity=self._build_run_identity(scenario),
                    status=RunStatus.succeeded,
                    prediction=prediction,
                    token_usage=TokenUsage(
                        prompt_tokens=legacy_prompt,
                        completion_tokens=legacy_completion,
                        total_tokens=fields["total_workflow_tokens"],
                    ),
                    failures=tuple(all_failures),
                    duration_seconds=time.monotonic() - start_time,
                    **fields,
                    selected_artifact_count=counts.get("selected", 0),
                    regenerated_artifact_count=sum(
                        1 for a in exec_result.artifacts if a.status == "generated"
                    ),
                    preserved_artifact_count=counts.get("preserve", 0),
                    unresolved_human_review_count=counts.get("human_review", 0),
                    predicted_actions=self._predicted_actions_map(prediction),
                    changed_artifact_paths=self._compute_changed_artifact_paths(),
                )

            if sci_result is not None and not sci_result.passed:
                ec, so, se = self._scientific_feedback_channels(sci_result)
                repairability = self.classify_validation_repairability(
                    exit_code=ec,
                    stdout=so,
                    stderr=se,
                    stage=sci_result.failed_stage or "",
                )
                if repairability == "infrastructure_nonrepairable":
                    all_failures.append(
                        self._infrastructure_failure_from_scientific_result(sci_result)
                    )
                    break
                all_failures.append(
                    self._failure_from_scientific_result(sci_result)
                )

            if no_progress:
                all_failures.append(
                    FailureRecord(
                        failure_kind=FailureKind.model_output,
                        message="repair_no_progress: repair reproduced the prior "
                        "attempt output; stopping repair rounds",
                        details="repair_no_progress=true",
                        stage="regeneration",
                    )
                )
                break

            attempt_failures = tuple(
                FailureRecord(
                    failure_kind=FailureKind.model_output,
                    message=message,
                    details="SharedRegenerationExecutor failure",
                    stage="regeneration",
                )
                for message in exec_result.failures
            )
            repair_context = self._build_repair_context(
                sci_result,
                attempt_failures,
            )

            if not self._budget.can_attempt:
                break

        self._state.fail()
        if self._budget.timed_out:
            all_failures.append(
                FailureRecord(
                    failure_kind=FailureKind.scientific_budget_exhausted,
                    message="Workflow deadline reached during regeneration repair rounds",
                    stage="budget",
                )
            )
        sci = self._last_scientific_result
        fields = acc.as_record_fields(
            final_scientific_result=sci,
            token_accounting_mode=token_accounting_mode,
        )
        legacy_prompt = (
            fields["selection_prompt_tokens"]
            + fields["regeneration_prompt_tokens"]
            + fields["repair_prompt_tokens"]
        )
        legacy_completion = (
            fields["selection_completion_tokens"]
            + fields["regeneration_completion_tokens"]
            + fields["repair_completion_tokens"]
        )
        return RunRecord(
            identity=self._build_run_identity(scenario),
            status=RunStatus.failed,
            prediction=prediction,
            token_usage=TokenUsage(
                prompt_tokens=legacy_prompt,
                completion_tokens=legacy_completion,
                total_tokens=fields["total_workflow_tokens"],
            ),
            failures=tuple(all_failures),
            duration_seconds=time.monotonic() - start_time,
            **fields,
            selected_artifact_count=counts.get("selected", 0),
            regenerated_artifact_count=first_regen_count,
            preserved_artifact_count=counts.get("preserve", 0),
            unresolved_human_review_count=counts.get("human_review", 0),
            predicted_actions=self._predicted_actions_map(prediction),
            changed_artifact_paths=self._compute_changed_artifact_paths(),
        )

    def _run_iterative_flow(
        self,
        scenario: Scenario,
        start_time: float,
    ) -> RunRecord:
        try:
            if self._budget.timed_out:
                return self._workflow_budget_exhausted_record(
                    scenario,
                    start_time,
                    "Workflow deadline reached before iterative agent selection",
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
            self._apply_strategy_model_call_guard()

            requirement_delta = f"{requirement_change.before} -> {requirement_change.after}"
            executor = SharedRegenerationExecutor(
                self._backend,
                can_start_model_call=lambda: not self._budget.timed_out,
            )

            token_accounting_mode = getattr(
                self._backend, "token_accounting_mode", "unknown"
            )

            acc = _WorkflowMetricAccumulator()

            all_failures: list[FailureRecord] = []
            total_regenerated = 0
            final_prediction: ImpactPrediction | None = None
            last_exec_result: RegenerationExecutionResult | None = None
            last_feedback_channels: tuple[int, str, str] | None = None
            iteration = 0
            has_validation_run = False

            while self._budget.can_attempt:
                if self._budget.has_total_token_limit and self._budget.remaining_tokens <= 0:
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
                        max_completion_tokens_per_call=self._config.max_completion_tokens_per_call,
                        remaining_total_workflow_tokens=self._budget.runtime_remaining_total_tokens,
                    )
                    sel_dur = time.monotonic() - selection_start
                    mc_after = getattr(self._strategy, "model_call_count", 0)
                    tc_after = getattr(self._strategy, "tool_call_count", 0)
                    td_after = getattr(self._strategy, "tool_duration_seconds", 0.0)
                    ic_after = getattr(self._strategy, "inspected_file_count", 0)
                    sel_calls_delta = mc_after - strategy_model_calls_before
                    sel_tool_delta = tc_after - strategy_tool_calls_before
                    sel_tool_dur_delta = td_after - strategy_tool_dur_before
                    sel_inspected_delta = ic_after - strategy_inspected_before

                    tok = prediction.token_usage or TokenUsage()
                    acc.add_selection(
                        tok,
                        model_calls=sel_calls_delta,
                        duration_seconds=sel_dur,
                        tool_calls=sel_tool_delta,
                        tool_duration_seconds=sel_tool_dur_delta,
                        inspected_file_count=sel_inspected_delta,
                    )
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
                        max_completion_tokens_per_call=self._config.max_completion_tokens_per_call,
                        remaining_total_workflow_tokens=self._budget.runtime_remaining_total_tokens,
                    )
                    sel_dur = time.monotonic() - selection_start
                    mc_after = getattr(self._strategy, "model_call_count", 0)
                    tc_after = getattr(self._strategy, "tool_call_count", 0)
                    td_after = getattr(self._strategy, "tool_duration_seconds", 0.0)
                    ic_after = getattr(self._strategy, "inspected_file_count", 0)
                    sel_calls_delta = mc_after - strategy_model_calls_before
                    sel_tool_delta = tc_after - strategy_tool_calls_before
                    sel_tool_dur_delta = td_after - strategy_tool_dur_before
                    sel_inspected_delta = ic_after - strategy_inspected_before

                    tok = prediction.token_usage or TokenUsage()
                    acc.add_selection(
                        tok,
                        model_calls=sel_calls_delta,
                        duration_seconds=sel_dur,
                        tool_calls=sel_tool_delta,
                        tool_duration_seconds=sel_tool_dur_delta,
                        inspected_file_count=sel_inspected_delta,
                    )

                final_prediction = prediction
                self._budget.record_tokens(tok.total_tokens)

                if self._strategy_model_call_budget_exhausted():
                    return self._workflow_budget_exhausted_record(
                        scenario,
                        start_time,
                        "Workflow deadline reached during iterative agent selection model calls",
                        acc=acc,
                        token_accounting_mode=token_accounting_mode,
                    )

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
                    scenario_context=self._build_scenario_context(scenario),
                    max_completion_tokens_per_call=self._config.max_completion_tokens_per_call,
                    remaining_total_workflow_tokens=self._budget.runtime_remaining_total_tokens,
                    enable_exact_patch=self._config.exact_patch,
                )

                self._budget.record_tokens(exec_result.total_tokens)

                if exec_result.model_call_budget_exhausted:
                    acc.add_code_generation(exec_result, is_repair=iteration > 0)
                    return self._workflow_budget_exhausted_record(
                        scenario,
                        start_time,
                        "Workflow deadline reached during iterative agent generation calls",
                        acc=acc,
                        token_accounting_mode=token_accounting_mode,
                    )

                sci_result = self._execute_scientific_validation(scenario, exec_result)
                has_validation_run = True

                is_repair = iteration > 0
                acc.add_code_generation(exec_result, is_repair=is_repair)
                if sci_result is not None:
                    acc.add_scientific(sci_result)
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
                    fields = acc.as_record_fields(
                        final_scientific_result=sci_result,
                        token_accounting_mode=token_accounting_mode,
                    )
                    legacy_prompt = (
                        fields["selection_prompt_tokens"]
                        + fields["regeneration_prompt_tokens"]
                        + fields["repair_prompt_tokens"]
                    )
                    legacy_completion = (
                        fields["selection_completion_tokens"]
                        + fields["regeneration_completion_tokens"]
                        + fields["repair_completion_tokens"]
                    )

                    tool_transcript = tuple(getattr(self._strategy, "compact_tool_transcript", ()))
                    return RunRecord(
                        identity=self._build_run_identity(scenario),
                        status=RunStatus.succeeded,
                        prediction=final_prediction,
                        token_usage=TokenUsage(
                            prompt_tokens=legacy_prompt,
                            completion_tokens=legacy_completion,
                            total_tokens=fields["total_workflow_tokens"],
                        ),
                        duration_seconds=time.monotonic() - start_time,
                        failures=tuple(all_failures),
                        selection_tool_transcript=tool_transcript,
                        **fields,
                        selected_artifact_count=counts.get("selected", 0),
                        regenerated_artifact_count=total_regenerated,
                        preserved_artifact_count=counts.get("preserve", 0),
                        unresolved_human_review_count=counts.get("human_review", 0),
                        predicted_actions=self._predicted_actions_map(final_prediction),
                        changed_artifact_paths=self._compute_changed_artifact_paths(),
                    )

                repairability = "repairable_code"
                if sci_result is not None and not sci_result.passed:
                    ec, so, se = self._scientific_feedback_channels(sci_result)
                    if exec_result.failures:
                        generation_feedback = "\n".join(
                            f"- {failure}" for failure in exec_result.failures
                        )
                        se = (
                            f"{se}\nGeneration/scope failures:\n"
                            f"{generation_feedback}"
                        ).strip()
                    last_feedback_channels = (ec, so, se)
                    repairability = self.classify_validation_repairability(
                        exit_code=ec,
                        stdout=so,
                        stderr=se,
                        stage=sci_result.failed_stage or "",
                    )
                elif exec_result.failures:
                    last_feedback_channels = (
                        -1,
                        "",
                        _compact_head_tail("\n".join(exec_result.failures)),
                    )
                else:
                    last_feedback_channels = None

                if repairability == "infrastructure_nonrepairable":
                    all_failures.append(
                        self._infrastructure_failure_from_scientific_result(sci_result)
                    )
                    break

                if sci_result is not None and not sci_result.passed:
                    all_failures.append(
                        self._failure_from_scientific_result(sci_result)
                    )
                elif exec_result.failures:
                    all_failures.append(
                        FailureRecord(
                            failure_kind=FailureKind.model_output,
                            message="Executor failures present",
                            details=_compact_head_tail("\n".join(exec_result.failures)),
                            stage="regeneration",
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
            tool_transcript = tuple(getattr(self._strategy, "compact_tool_transcript", ()))
            sci = self._last_scientific_result
            if self._budget.timed_out:
                all_failures.append(
                    FailureRecord(
                        failure_kind=FailureKind.scientific_budget_exhausted,
                        message="Workflow deadline reached during iterative agent execution",
                        stage="budget",
                    )
                )
            fields = acc.as_record_fields(
                final_scientific_result=sci,
                token_accounting_mode=token_accounting_mode,
            )
            legacy_prompt = (
                fields["selection_prompt_tokens"]
                + fields["regeneration_prompt_tokens"]
                + fields["repair_prompt_tokens"]
            )
            legacy_completion = (
                fields["selection_completion_tokens"]
                + fields["regeneration_completion_tokens"]
                + fields["repair_completion_tokens"]
            )

            return RunRecord(
                identity=self._build_run_identity(scenario),
                status=RunStatus.failed,
                prediction=final_prediction,
                token_usage=TokenUsage(
                    prompt_tokens=legacy_prompt,
                    completion_tokens=legacy_completion,
                    total_tokens=fields["total_workflow_tokens"],
                ) if final_prediction else TokenUsage(),
                duration_seconds=time.monotonic() - start_time,
                failures=tuple(all_failures),
                selection_tool_transcript=tool_transcript,
                **fields,
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
                predicted_actions=self._predicted_actions_map(final_prediction),
                changed_artifact_paths=self._compute_changed_artifact_paths(),
            )
        except BudgetExhaustedError:
            return self._workflow_budget_exhausted_record(
                scenario,
                start_time,
                "Budget exhausted during iterative agent execution",
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

    def _predicted_actions_map(
        self, prediction: ImpactPrediction | None
    ) -> dict[str, str]:
        """Persist the strategy's final per-path decision/action map.

        D046 / PA-001: reconstructing the predicted regenerate-set exactly
        requires the actual predicted action for every decision path.
        """
        if prediction is None:
            return {}
        return {d.artifact.path: d.action.value for d in prediction.decisions}

    def _compute_changed_artifact_paths(self) -> tuple[str, ...]:
        """Actual source-change evidence against the frozen active snapshot.

        D046 / PA-001: preservation is scored from ACTUAL unintended changes to
        preserve artifacts, not from the model predicting ``preserve``. Compare
        every editable candidate artifact between the active snapshot and the
        execution workspace; any byte-difference is an actual changed path.
        Generated migrations are NOT editable candidates and stay in the
        separate ``generated_migration_paths`` field.

        Returns empty when no active snapshot is configured (legacy / non-scientific
        contexts; always populated for the scientific profile).
        """
        if self._isolation.active_snapshot_root is None:
            return ()
        snapshot = Path(self._active_snapshot())
        workspace_root = Path(self._isolation.workspace.root)
        changed: list[str] = []
        for rel in self._config.editable_artifact_paths:
            snapshot_file = snapshot / rel
            workspace_file = (workspace_root / rel).resolve()
            if not snapshot_file.is_file():
                continue
            try:
                if not workspace_file.is_file():
                    changed.append(rel)
                    continue
                if snapshot_file.read_bytes() != workspace_file.read_bytes():
                    changed.append(rel)
            except OSError:
                changed.append(rel)
        changed.sort()
        return tuple(changed)

    def _persist_impact_plan(self, plan: Any, scenario: Scenario) -> None:
        """Persist the ImpactPlan sidecar BEFORE any source write (Stage-C)."""
        try:
            from benchmark.selection.impact_planner import to_plan_dict

            plan_dir = Path(self._isolation.workspace.root) / "impact_plans"
            plan_dir.mkdir(parents=True, exist_ok=True)
            run_tag = self._build_run_id(scenario)
            sidecar = plan_dir / f"{run_tag}_{plan.plan_version}.json"
            sidecar.write_text(
                json.dumps(to_plan_dict(plan), indent=2, sort_keys=True),
                encoding="utf-8",
            )
            logger.info(
                "IMPACT_PLAN_PERSISTED path=%s plan_version=%s hash=%s",
                sidecar, plan.plan_version, plan.plan_hash,
            )
        except Exception as exc:
            logger.warning("ImpactPlan persistence failed: %s", exc)

    def _impact_plan_metrics(self, plan: Any) -> dict[str, int]:
        if plan is None:
            return {
                "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
                "model_calls": 0, "latency_seconds": 0,
            }
        tu = getattr(plan, "planner_token_usage", None)
        prompt = getattr(tu, "prompt_tokens", 0)
        completion = getattr(tu, "completion_tokens", 0)
        total = getattr(tu, "total_tokens", prompt + completion)
        return {
            "prompt_tokens": int(prompt),
            "completion_tokens": int(completion),
            "total_tokens": int(total),
            "model_calls": int(getattr(plan, "planner_model_calls", 0)),
            "latency_seconds": int(round(float(getattr(plan, "planner_latency_seconds", 0.0)))),
        }

    def _impact_plan_to_dict(self, plan: Any) -> dict[str, Any]:
        try:
            from benchmark.selection.impact_planner import to_plan_dict

            return to_plan_dict(plan)
        except Exception:
            return {}

    def _expand_plan_once(
        self,
        *,
        scenario: Scenario,
        requirement_change: RequirementChange,
        artifact_universe: ArtifactUniverse,
        strategy_expand: Any,
        failure_summary: str,
        parent_plan: Any,
    ) -> ImpactPrediction | None:
        try:
            repository_snapshot = self._build_repository_snapshot(scenario)
            result = strategy_expand(
                repository_snapshot,
                requirement_change,
                artifact_universe,
                failure_summary=failure_summary,
                parent_plan=parent_plan,
            )
            if result is None:
                return None
            assert isinstance(result, ImpactPrediction)
            return result
        except Exception as exc:
            logger.warning("ImpactPlan expansion error: %s", exc)
            return None

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
