
from benchmark.core.enums import FailureKind, RunStatus
from benchmark.core.exceptions import BenchmarkError
from benchmark.core.models import RunIdentity, RunRecord
from benchmark.execution.budgets import BudgetManager
from benchmark.execution.repair import RepairLoop
from benchmark.execution.state_machine import RunState, RunStateMachine


def _identity() -> RunIdentity:
    return RunIdentity(
        run_id="test", protocol_version="1.0", repository_commit_sha="a", scenario_id="s1", strategy_name="t",
    )


class TestRepairLoop:
    def test_succeeds_on_first_attempt(self) -> None:
        budget = BudgetManager(max_attempts=3)
        sm = RunStateMachine()
        sm.start()

        def attempt_fn(_attempt: int) -> RunRecord:
            return RunRecord(identity=_identity(), status=RunStatus.succeeded)

        loop = RepairLoop(budget=budget, state_machine=sm, attempt_fn=attempt_fn)
        outcome = loop.execute()
        assert outcome.success is True
        assert outcome.total_attempts == 1
        assert outcome.final_record.status == RunStatus.succeeded

    def test_retries_on_failure(self) -> None:
        budget = BudgetManager(max_attempts=3)
        sm = RunStateMachine()
        sm.start()
        call_count = 0

        def attempt_fn(_attempt: int) -> RunRecord:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return RunRecord(identity=_identity(), status=RunStatus.failed)
            return RunRecord(identity=_identity(), status=RunStatus.succeeded)

        loop = RepairLoop(budget=budget, state_machine=sm, attempt_fn=attempt_fn)
        outcome = loop.execute()
        assert outcome.success is True
        assert outcome.total_attempts == 3
        assert call_count == 3

    def test_exhausts_attempts_and_fails(self) -> None:
        budget = BudgetManager(max_attempts=2)
        sm = RunStateMachine()
        sm.start()

        def attempt_fn(_attempt: int) -> RunRecord:
            return RunRecord(identity=_identity(), status=RunStatus.failed)

        loop = RepairLoop(budget=budget, state_machine=sm, attempt_fn=attempt_fn)
        outcome = loop.execute()
        assert outcome.success is False
        assert outcome.total_attempts == 2
        assert outcome.final_record.status == RunStatus.failed
        assert len(outcome.failures) == 2

    def test_handles_benchmark_error(self) -> None:
        budget = BudgetManager(max_attempts=2)
        sm = RunStateMachine()
        sm.start()

        def attempt_fn(_attempt: int) -> RunRecord | BenchmarkError:
            return BenchmarkError("model error")

        loop = RepairLoop(budget=budget, state_machine=sm, attempt_fn=attempt_fn)
        outcome = loop.execute()
        assert outcome.success is False
        assert len(outcome.failures) == 2
        assert outcome.failures[0].failure_kind == FailureKind.infrastructure

    def test_custom_classifier(self) -> None:
        budget = BudgetManager(max_attempts=2)
        sm = RunStateMachine()
        sm.start()

        def attempt_fn(_attempt: int) -> RunRecord:
            return RunRecord(identity=_identity(), status=RunStatus.failed)

        def classifier(_record: RunRecord) -> FailureKind | None:
            return FailureKind.build

        loop = RepairLoop(budget=budget, state_machine=sm, attempt_fn=attempt_fn, classifier=classifier)
        outcome = loop.execute()
        assert outcome.failures[0].failure_kind == FailureKind.build

    def test_classifier_returns_none(self) -> None:
        budget = BudgetManager(max_attempts=1)
        sm = RunStateMachine()
        sm.start()

        def attempt_fn(_attempt: int) -> RunRecord:
            return RunRecord(identity=_identity(), status=RunStatus.failed)

        def classifier(_record: RunRecord) -> FailureKind | None:
            return None

        loop = RepairLoop(budget=budget, state_machine=sm, attempt_fn=attempt_fn, classifier=classifier)
        outcome = loop.execute()
        assert outcome.failures[0].failure_kind == FailureKind.model_output

    def test_timed_out_record(self) -> None:
        budget = BudgetManager(max_attempts=2)
        sm = RunStateMachine()
        sm.start()

        def attempt_fn(_attempt: int) -> RunRecord:
            return RunRecord(identity=_identity(), status=RunStatus.timed_out)

        loop = RepairLoop(budget=budget, state_machine=sm, attempt_fn=attempt_fn)
        outcome = loop.execute()
        assert outcome.success is False
        assert outcome.failures[0].failure_kind == FailureKind.timeout

    def test_repair_loop_transitions_state(self) -> None:
        budget = BudgetManager(max_attempts=1)
        sm = RunStateMachine()
        sm.start()

        def attempt_fn(_attempt: int) -> RunRecord:
            return RunRecord(identity=_identity(), status=RunStatus.failed)

        loop = RepairLoop(budget=budget, state_machine=sm, attempt_fn=attempt_fn)
        loop.execute()
        assert sm.state == RunState.failed
