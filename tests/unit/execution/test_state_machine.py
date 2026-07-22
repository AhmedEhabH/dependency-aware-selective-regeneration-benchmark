import pytest

from benchmark.execution.state_machine import InvalidTransitionError, RunState, RunStateMachine


class TestRunStateMachine:
    def test_initial_state_is_prepared(self) -> None:
        sm = RunStateMachine()
        assert sm.state == RunState.prepared
        assert sm.is_prepared is True
        assert sm.is_terminal is False
        assert sm.is_running is False

    def test_start_transitions_to_running(self) -> None:
        sm = RunStateMachine()
        sm.start()
        assert sm.state == RunState.running
        assert sm.is_running is True
        assert sm.is_prepared is False

    def test_succeed_from_running(self) -> None:
        sm = RunStateMachine()
        sm.start()
        sm.succeed()
        assert sm.state == RunState.succeeded
        assert sm.is_terminal is True
        assert sm.succeeded is True

    def test_fail_from_running(self) -> None:
        sm = RunStateMachine()
        sm.start()
        sm.fail()
        assert sm.state == RunState.failed
        assert sm.is_terminal is True

    def test_timeout_from_running(self) -> None:
        sm = RunStateMachine()
        sm.start()
        sm.timeout()
        assert sm.state == RunState.timed_out
        assert sm.is_terminal is True

    def test_cancel_from_running(self) -> None:
        sm = RunStateMachine()
        sm.start()
        sm.cancel()
        assert sm.state == RunState.cancelled
        assert sm.is_terminal is True

    def test_cannot_start_from_running(self) -> None:
        sm = RunStateMachine()
        sm.start()
        with pytest.raises(InvalidTransitionError, match="Cannot transition from running"):
            sm.start()

    def test_cannot_succeed_from_prepared(self) -> None:
        sm = RunStateMachine()
        with pytest.raises(InvalidTransitionError, match="Cannot transition from prepared to succeeded"):
            sm.succeed()

    def test_cannot_fail_from_prepared(self) -> None:
        sm = RunStateMachine()
        with pytest.raises(InvalidTransitionError, match="prepared to failed"):
            sm.fail()

    def test_cannot_transition_from_terminal(self) -> None:
        sm = RunStateMachine()
        sm.start()
        sm.succeed()
        with pytest.raises(InvalidTransitionError):
            sm.fail()
        with pytest.raises(InvalidTransitionError):
            sm.timeout()
        with pytest.raises(InvalidTransitionError):
            sm.cancel()
        with pytest.raises(InvalidTransitionError):
            sm.start()

    def test_guard_running_passes_when_running(self) -> None:
        sm = RunStateMachine()
        sm.start()
        sm.guard_running()

    def test_guard_running_raises_when_not_running(self) -> None:
        sm = RunStateMachine()
        with pytest.raises(InvalidTransitionError, match="Expected state 'running'"):
            sm.guard_running()

        sm.start()
        sm.succeed()
        with pytest.raises(InvalidTransitionError, match="Expected state 'running'"):
            sm.guard_running()

    def test_assert_not_terminal(self) -> None:
        sm = RunStateMachine()
        sm.assert_not_terminal()
        sm.start()
        sm.assert_not_terminal()
        sm.succeed()
        with pytest.raises(InvalidTransitionError, match="terminal"):
            sm.assert_not_terminal()

    def test_full_lifecycle(self) -> None:
        sm = RunStateMachine()
        start_state = sm.state
        assert start_state == RunState.prepared
        sm.start()
        running_state = sm.state
        assert running_state == RunState.running
        assert sm.is_running is True
        sm.succeed()
        final_state = sm.state
        assert final_state == RunState.succeeded
        assert sm.succeeded is True

    def test_fail_lifecycle(self) -> None:
        sm = RunStateMachine()
        sm.start()
        sm.fail()
        assert sm.state is RunState.failed
        assert sm.is_terminal is True

    def test_all_terminal_states(self) -> None:
        for terminal_state in [RunState.succeeded, RunState.failed, RunState.timed_out, RunState.cancelled]:
            sm = RunStateMachine()
            sm.start()
            if terminal_state == RunState.succeeded:
                sm.succeed()
            elif terminal_state == RunState.failed:
                sm.fail()
            elif terminal_state == RunState.timed_out:
                sm.timeout()
            elif terminal_state == RunState.cancelled:
                sm.cancel()
            assert sm.is_terminal is True
            assert sm.state == terminal_state
