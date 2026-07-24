from __future__ import annotations

from enum import StrEnum


class RunState(StrEnum):
    prepared = "prepared"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    timed_out = "timed_out"
    cancelled = "cancelled"


_TERMINAL_STATES: frozenset[RunState] = frozenset(
    {RunState.succeeded, RunState.failed, RunState.timed_out, RunState.cancelled}
)

_VALID_TRANSITIONS: dict[RunState, set[RunState]] = {
    RunState.prepared: {RunState.running},
    RunState.running: {RunState.succeeded, RunState.failed, RunState.timed_out, RunState.cancelled},
    RunState.succeeded: set(),
    RunState.failed: set(),
    RunState.timed_out: set(),
    RunState.cancelled: set(),
}


class InvalidTransitionError(RuntimeError):
    pass


class RunStateMachine:
    def __init__(self) -> None:
        self._state: RunState = RunState.prepared

    @property
    def state(self) -> RunState:
        return self._state

    @property
    def is_terminal(self) -> bool:
        return self._state in _TERMINAL_STATES

    @property
    def is_running(self) -> bool:
        return self._state == RunState.running

    @property
    def is_prepared(self) -> bool:
        return self._state == RunState.prepared

    @property
    def succeeded(self) -> bool:
        return self._state == RunState.succeeded

    def _transition(self, target: RunState) -> None:
        allowed = _VALID_TRANSITIONS.get(self._state, set())
        if target not in allowed:
            raise InvalidTransitionError(
                f"Cannot transition from {self._state} to {target}"
            )
        self._state = target

    def start(self) -> None:
        self._transition(RunState.running)

    def succeed(self) -> None:
        self._transition(RunState.succeeded)

    def fail(self) -> None:
        self._transition(RunState.failed)

    def timeout(self) -> None:
        self._transition(RunState.timed_out)

    def cancel(self) -> None:
        self._transition(RunState.cancelled)

    def guard_running(self) -> None:
        if self._state != RunState.running:
            raise InvalidTransitionError(
                f"Expected state 'running' but current state is '{self._state}'"
            )

    def assert_not_terminal(self) -> None:
        if self.is_terminal:
            raise InvalidTransitionError(
                f"Cannot act on terminal state '{self._state}'"
            )
