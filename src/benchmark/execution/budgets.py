from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Protocol


class Clock(Protocol):
    def now(self) -> float:
        ...


class SystemClock:
    def now(self) -> float:
        return time.time()


@dataclass
class AttemptSnapshot:
    attempt_number: int
    started_at: float
    tokens_consumed: int = 0


@dataclass
class BudgetState:
    total_attempts: int = 0
    total_tokens: int = 0
    start_time: float = 0.0
    attempts: list[AttemptSnapshot] = field(default_factory=list)
    exhausted: bool = False


class BudgetManager:
    def __init__(
        self,
        max_attempts: int = 3,
        max_tokens: int = 0,
        timeout_seconds: int = 0,
        clock: Clock | None = None,
    ) -> None:
        if isinstance(max_attempts, bool):
            raise ValueError("max_attempts must be an integer, not bool")
        if isinstance(max_tokens, bool):
            raise ValueError("max_tokens must be an integer, not bool")
        if isinstance(timeout_seconds, bool):
            raise ValueError("timeout_seconds must be an integer, not bool")
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if max_tokens < 0:
            raise ValueError("max_tokens must be >= 0")
        if timeout_seconds < 0:
            raise ValueError("timeout_seconds must be >= 0")
        self._max_attempts = max_attempts
        self._max_tokens = max_tokens
        self._timeout_seconds = timeout_seconds
        self._clock = clock or SystemClock()
        self._state = BudgetState(start_time=self._clock.now())

    @property
    def max_attempts(self) -> int:
        return self._max_attempts

    @property
    def state(self) -> BudgetState:
        return self._state

    @property
    def elapsed(self) -> float:
        return self._clock.now() - self._state.start_time

    @property
    def remaining_attempts(self) -> int:
        return self._max_attempts - self._state.total_attempts

    @property
    def remaining_tokens(self) -> int:
        if self._max_tokens <= 0:
            return 0
        return max(0, self._max_tokens - self._state.total_tokens)

    @property
    def has_total_token_limit(self) -> bool:
        return self._max_tokens > 0

    @property
    def remaining_total_tokens(self) -> int:
        return self.remaining_tokens

    @property
    def runtime_remaining_total_tokens(self) -> int | None:
        """Runtime allowance passed to executors and strategies.

        Returns None when no total workflow limit is configured (unlimited),
        0 when a configured limit has been exhausted exactly, and a positive
        integer when a configured limit still has remaining allowance.
        """
        if not self.has_total_token_limit:
            return None
        return max(0, self._max_tokens - self._state.total_tokens)

    @property
    def can_attempt(self) -> bool:
        return not (
            self._state.exhausted
            or self._state.total_attempts >= self._max_attempts
            or (self._timeout_seconds > 0 and self.elapsed >= self._timeout_seconds)
        )

    @property
    def timed_out(self) -> bool:
        if self._timeout_seconds <= 0:
            return False
        return self.elapsed >= self._timeout_seconds

    def record_attempt(self, tokens: int = 0) -> AttemptSnapshot:
        if not self.can_attempt:
            self._state.exhausted = True
            raise BudgetExhaustedError(
                f"No remaining budget: attempts={self._state.total_attempts}/{self._max_attempts}, "
                f"elapsed={self.elapsed:.1f}s timeout={self._timeout_seconds}s"
            )
        if self._max_tokens > 0 and self._state.total_tokens + tokens > self._max_tokens:
            self._state.exhausted = True
            raise BudgetExhaustedError(
                f"Token budget exceeded: {self._state.total_tokens + tokens} > {self._max_tokens}"
            )
        snapshot = AttemptSnapshot(
            attempt_number=self._state.total_attempts + 1,
            started_at=self._clock.now(),
            tokens_consumed=tokens,
        )
        self._state.total_attempts += 1
        self._state.total_tokens += tokens
        self._state.attempts.append(snapshot)
        return snapshot

    def record_tokens(self, tokens: int) -> None:
        if isinstance(tokens, bool):
            raise ValueError("tokens must be an integer, not bool")
        if tokens < 0:
            raise ValueError(f"tokens must be >= 0, got {tokens}")
        self._state.total_tokens += tokens
        if self._state.attempts:
            self._state.attempts[-1].tokens_consumed += tokens
        if self._max_tokens > 0 and self._state.total_tokens >= self._max_tokens:
            self._state.exhausted = True

    def reset(self) -> None:
        self._state = BudgetState(start_time=self._clock.now())


class BudgetExhaustedError(RuntimeError):
    pass


def resolve_completion_allowance(
    *,
    max_completion_tokens_per_call: int,
    remaining_total_workflow_tokens: int | None,
    prompt_tokens: int,
) -> int:
    """Resolve the completion allowance for a single model call.

    ``remaining_total_workflow_tokens`` is a runtime allowance where None means
    "no total workflow limit configured" (unlimited), 0 means "a configured
    limit has been exhausted exactly" (no further calls), and a positive
    integer is the remaining configured allowance.
    """
    if isinstance(max_completion_tokens_per_call, bool):
        raise ValueError("max_completion_tokens_per_call must be an integer, not bool")
    if isinstance(remaining_total_workflow_tokens, bool):
        raise ValueError("remaining_total_workflow_tokens must be an integer, not bool")
    if isinstance(prompt_tokens, bool):
        raise ValueError("prompt_tokens must be an integer, not bool")
    if max_completion_tokens_per_call < 1:
        raise ValueError(
            f"max_completion_tokens_per_call must be >= 1, got {max_completion_tokens_per_call}"
        )
    if remaining_total_workflow_tokens is not None and remaining_total_workflow_tokens < 0:
        raise ValueError(
            f"remaining_total_workflow_tokens must be >= 0, got {remaining_total_workflow_tokens}"
        )
    if prompt_tokens < 0:
        raise ValueError(
            f"prompt_tokens must be >= 0, got {prompt_tokens}"
        )
    if remaining_total_workflow_tokens is None:
        return max_completion_tokens_per_call
    if remaining_total_workflow_tokens == 0:
        return 0
    available_after_prompt = remaining_total_workflow_tokens - prompt_tokens
    return max(0, min(max_completion_tokens_per_call, available_after_prompt))
