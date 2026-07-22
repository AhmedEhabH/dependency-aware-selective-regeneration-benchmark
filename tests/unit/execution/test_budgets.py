import pytest

from benchmark.execution.budgets import BudgetExhaustedError, BudgetManager


class TestBudgetManager:
    def test_default_construction(self) -> None:
        bm = BudgetManager()
        assert bm.max_attempts == 3
        assert bm.remaining_attempts == 3
        assert bm.can_attempt is True
        assert bm.timed_out is False

    def test_custom_parameters(self) -> None:
        bm = BudgetManager(max_attempts=5, max_tokens=1000, timeout_seconds=60)
        assert bm.max_attempts == 5
        assert bm.remaining_attempts == 5
        assert bm.can_attempt is True

    def test_invalid_max_attempts_raises(self) -> None:
        with pytest.raises(ValueError, match="max_attempts"):
            BudgetManager(max_attempts=0)

    def test_invalid_max_tokens_raises(self) -> None:
        with pytest.raises(ValueError, match="max_tokens"):
            BudgetManager(max_tokens=-1)

    def test_invalid_timeout_raises(self) -> None:
        with pytest.raises(ValueError, match="timeout_seconds"):
            BudgetManager(timeout_seconds=-1)

    def test_record_attempt_increments(self) -> None:
        bm = BudgetManager(max_attempts=3)
        s1 = bm.record_attempt()
        assert s1.attempt_number == 1
        assert bm.state.total_attempts == 1
        assert bm.remaining_attempts == 2

        s2 = bm.record_attempt()
        assert s2.attempt_number == 2
        assert bm.state.total_attempts == 2

        s3 = bm.record_attempt()
        assert s3.attempt_number == 3
        assert bm.state.total_attempts == 3
        assert bm.remaining_attempts == 0

    def test_cannot_exceed_max_attempts(self) -> None:
        bm = BudgetManager(max_attempts=1)
        bm.record_attempt()
        assert bm.can_attempt is False
        with pytest.raises(BudgetExhaustedError, match="No remaining budget"):
            bm.record_attempt()

    def test_token_budget_enforced(self) -> None:
        bm = BudgetManager(max_attempts=5, max_tokens=100)
        bm.record_attempt(tokens=60)
        assert bm.can_attempt is True
        with pytest.raises(BudgetExhaustedError, match="Token budget exceeded"):
            bm.record_attempt(tokens=50)

    def test_reset_clears_state(self) -> None:
        bm = BudgetManager(max_attempts=2)
        bm.record_attempt()
        bm.record_attempt()
        assert bm.can_attempt is False
        bm.reset()
        assert bm.can_attempt is True
        assert bm.state.total_attempts == 0
        assert bm.state.total_tokens == 0

    def test_timed_out_property(self) -> None:
        class FastClock:
            def __init__(self: "FastClock") -> None:
                self._now = 0.0

            def now(self: "FastClock") -> float:
                return self._now

            def advance(self: "FastClock", seconds: float) -> None:
                self._now += seconds

        clock = FastClock()
        bm = BudgetManager(timeout_seconds=10, clock=clock)
        assert bm.timed_out is False
        assert bm.can_attempt is True
        clock.advance(11)
        assert bm.timed_out is True
        assert bm.can_attempt is False

    def test_elapsed_time(self) -> None:
        class AdvancingClock:
            def __init__(self: "AdvancingClock") -> None:
                self._base = 100.0

            def now(self: "AdvancingClock") -> float:
                return self._base

            def advance(self: "AdvancingClock", seconds: float) -> None:
                self._base += seconds

        clock = AdvancingClock()
        bm = BudgetManager(clock=clock)
        clock.advance(10)
        assert bm.elapsed == 10.0

    def test_attempt_tracks_tokens(self) -> None:
        bm = BudgetManager(max_attempts=3, max_tokens=1000)
        s = bm.record_attempt(tokens=42)
        assert s.tokens_consumed == 42
        assert bm.state.total_tokens == 42

    def test_starts_with_zero_attempts(self) -> None:
        bm = BudgetManager()
        assert bm.state.total_attempts == 0
        assert bm.state.total_tokens == 0

    def test_exhausted_flag_persists(self) -> None:
        bm = BudgetManager(max_attempts=1)
        bm.record_attempt()
        assert bm.can_attempt is False
        with pytest.raises(BudgetExhaustedError):
            bm.record_attempt()
        assert bm.state.exhausted is True
