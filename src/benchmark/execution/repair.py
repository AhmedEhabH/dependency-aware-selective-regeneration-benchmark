from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from benchmark.core.enums import FailureKind, RunStatus
from benchmark.core.exceptions import BenchmarkError
from benchmark.core.models import FailureRecord, RunIdentity, RunRecord
from benchmark.execution.budgets import BudgetManager
from benchmark.execution.state_machine import RunStateMachine


@dataclass
class RepairOutcome:
    success: bool
    final_record: RunRecord
    total_attempts: int
    failures: tuple[FailureRecord, ...] = ()


AttemptGenerator = Callable[[int], RunRecord | BenchmarkError]
FailureClassifier = Callable[[RunRecord], FailureKind | None]


class RepairLoop:
    def __init__(
        self,
        budget: BudgetManager,
        state_machine: RunStateMachine,
        attempt_fn: AttemptGenerator,
        classifier: FailureClassifier | None = None,
    ) -> None:
        self._budget = budget
        self._state = state_machine
        self._attempt_fn = attempt_fn
        self._classifier = classifier or _default_classifier

    def execute(self) -> RepairOutcome:
        failures: list[FailureRecord] = []
        final_record: RunRecord | None = None

        while self._budget.can_attempt:
            self._budget.record_attempt()
            result = self._attempt_fn(self._budget.state.total_attempts)

            if isinstance(result, BenchmarkError):
                failure_kind = _classify_error(result)
                failures.append(
                    FailureRecord(
                        failure_kind=failure_kind,
                        message=str(result),
                        details=result.__class__.__name__,
                    )
                )
                if self._budget.can_attempt:
                    continue
                final_record = RunRecord(
                    identity=_dummy_identity(),
                    status=RunStatus.failed,
                    failures=tuple(failures),
                )
                break

            if result.status == RunStatus.succeeded:
                self._state.succeed()
                return RepairOutcome(
                    success=True,
                    final_record=result,
                    total_attempts=self._budget.state.total_attempts,
                    failures=(),
                )

            failure_kind = self._classifier(result) or FailureKind.model_output
            failures.append(
                FailureRecord(
                    failure_kind=failure_kind,
                    message=f"Attempt {self._budget.state.total_attempts}: {result.status.value}",
                )
            )

            if not self._budget.can_attempt:
                final_record = RunRecord(
                    identity=result.identity,
                    status=RunStatus.failed,
                    prediction=result.prediction,
                    failures=tuple(failures),
                    token_usage=result.token_usage,
                    duration_seconds=result.duration_seconds,
                )
                break

        if final_record is None:
            final_record = RunRecord(
                identity=_dummy_identity(),
                status=RunStatus.failed,
                failures=tuple(failures),
            )

        self._state.fail()
        return RepairOutcome(
            success=False,
            final_record=final_record,
            total_attempts=self._budget.state.total_attempts,
            failures=tuple(failures),
        )


def _default_classifier(record: RunRecord) -> FailureKind:
    if record.status == RunStatus.timed_out:
        return FailureKind.timeout
    return FailureKind.model_output


def _classify_error(err: BenchmarkError) -> FailureKind:
    name = type(err).__name__
    if "Timeout" in name or "Budget" in name:
        return FailureKind.timeout
    if "Model" in name:
        return FailureKind.model_output
    return FailureKind.infrastructure


def _dummy_identity() -> RunIdentity:
    return RunIdentity(
        run_id="unknown",
        protocol_version="0.0",
        repository_commit_sha="0000000",
        scenario_id="unknown",
        strategy_name="unknown",
    )
