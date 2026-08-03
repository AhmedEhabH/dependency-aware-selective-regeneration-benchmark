from __future__ import annotations

from typing import Any

from seven_arm_benchmark import (
    _decide_session_exit_code,
    _should_stop_after_terminal_run,
    _terminal_record_outcome,
)


class TestSessionExitCode:
    """Scientific model failures are data; engineering blockers fail the job."""

    @staticmethod
    def _decide(**kwargs: Any) -> int:
        defaults: dict[str, Any] = {
            "max_runs": 1,
            "all_runs_completed": False,
            "session_created_run_count": 1,
            "last_run_status": "succeeded",
            "hf_uploader_configured": False,
            "hf_sync_ok": True,
            "total_failed": 0,
            "last_run_failure_classification": "",
            "engineering_blocker_count": 0,
            "last_run_outcome": "",
        }
        defaults.update(kwargs)
        return _decide_session_exit_code(**defaults)

    def test_one_succeeded_cell_returns_zero(self) -> None:
        assert self._decide(last_run_status="succeeded") == 0

    def test_one_scientific_failure_returns_zero(self) -> None:
        assert self._decide(
            last_run_status="failed",
            last_run_failure_classification="model_output",
            total_failed=1,
        ) == 0

    def test_one_engineering_failure_returns_nonzero(self) -> None:
        assert self._decide(
            last_run_status="failed",
            last_run_failure_classification="infrastructure_nonrepairable",
            engineering_blocker_count=1,
        ) == 1
        assert self._decide(last_run_status="timed_out") == 1
        assert self._decide(last_run_status="cancelled") == 1

    def test_nine_scientific_terminal_failures_return_zero(self) -> None:
        assert self._decide(
            all_runs_completed=True,
            total_failed=9,
            engineering_blocker_count=0,
        ) == 0

    def test_complete_plan_with_engineering_blocker_returns_nonzero(self) -> None:
        assert self._decide(
            all_runs_completed=True,
            total_failed=1,
            engineering_blocker_count=1,
        ) == 1

    def test_complete_plan_with_all_success_returns_zero(self) -> None:
        assert self._decide(all_runs_completed=True, total_failed=0) == 0

    def test_hf_sync_failure_returns_nonzero(self) -> None:
        assert self._decide(
            hf_uploader_configured=True,
            hf_sync_ok=False,
        ) == 1

    def test_incomplete_without_max_runs_engineering_blocker_exits_nonzero(self) -> None:
        assert self._decide(
            max_runs=0,
            last_run_status="failed",
            last_run_failure_classification="infrastructure_nonrepairable",
            engineering_blocker_count=1,
        ) == 1

    def test_continuous_scientific_failure_remains_zero(self) -> None:
        assert self._decide(
            max_runs=0,
            last_run_status="failed",
            last_run_failure_classification="model_output",
            engineering_blocker_count=0,
            total_failed=1,
        ) == 0

    def test_terminal_record_outcome(self) -> None:
        assert _terminal_record_outcome({"status": "succeeded"}) == (
            "scientific_success"
        )
        assert _terminal_record_outcome(
            {
                "status": "failed",
                "failure_classification": "model_output",
                "failure_details": [
                    {"kind": "build", "stage": "migration_generation"}
                ],
            }
        ) == "scientific_failure"
        assert _terminal_record_outcome(
            {
                "status": "failed",
                "failure_classification": "infrastructure_nonrepairable",
            }
        ) == "engineering_blocker"
        assert _terminal_record_outcome(
            {"status": "failed", "failure_classification": "unknown"}
        ) == "engineering_blocker"

        assert _terminal_record_outcome(
            {
                "status": "failed",
                "failure_classification": "model_output",
                "failure_details": [
                    {"kind": "model_output"},
                    {"kind": "infrastructure_nonrepairable"},
                ],
            }
        ) == "engineering_blocker"

    def test_scientific_budget_exhaustion_is_scientific_terminal(self) -> None:
        assert _terminal_record_outcome(
            {
                "status": "failed",
                "failure_classification": "scientific_budget_exhausted",
                "failure_details": [
                    {"kind": "scientific_budget_exhausted", "stage": "budget"}
                ],
            }
        ) == "scientific_failure"
        assert self._decide(
            last_run_status="failed",
            last_run_failure_classification="scientific_budget_exhausted",
            total_failed=1,
        ) == 0
        assert (
            _should_stop_after_terminal_run(
                last_run_outcome="scientific_failure",
                hf_uploader_configured=True,
                hf_sync_ok=True,
            )
            is False
        )

    def test_preflight_timeout_is_engineering_blocker(self) -> None:
        assert _terminal_record_outcome(
            {
                "status": "failed",
                "failure_classification": "environment_preflight",
                "failure_details": [
                    {
                        "kind": "environment_preflight",
                        "stage": "preflight",
                        "message": "Command timed out after 180s",
                    }
                ],
            }
        ) == "engineering_blocker"
        assert self._decide(
            last_run_status="failed",
            last_run_failure_classification="environment_preflight",
            engineering_blocker_count=1,
        ) == 1

    def test_hf_timeout_is_engineering_blocker(self) -> None:
        assert (
            _should_stop_after_terminal_run(
                last_run_outcome="scientific_success",
                hf_uploader_configured=True,
                hf_sync_ok=False,
            )
            is True
        )
        assert self._decide(
            hf_uploader_configured=True,
            hf_sync_ok=False,
        ) == 1

    def test_incomplete_exit_uses_full_terminal_outcome(self) -> None:
        assert self._decide(
            last_run_status="failed",
            last_run_failure_classification="model_output",
            last_run_outcome="engineering_blocker",
        ) == 1
        assert self._decide(
            last_run_status="failed",
            last_run_failure_classification="model_output",
            last_run_outcome="scientific_failure",
        ) == 0


class TestShouldStopAfterTerminalRun:
    """Scientific results persist and continue; engineering blocks stop."""

    def test_scientific_success_does_not_stop(self) -> None:
        assert (
            _should_stop_after_terminal_run(
                last_run_outcome="scientific_success",
                hf_uploader_configured=True,
                hf_sync_ok=True,
            )
            is False
        )

    def test_scientific_failure_does_not_stop(self) -> None:
        assert (
            _should_stop_after_terminal_run(
                last_run_outcome="scientific_failure",
                hf_uploader_configured=True,
                hf_sync_ok=True,
            )
            is False
        )

    def test_engineering_blocker_stops(self) -> None:
        assert (
            _should_stop_after_terminal_run(
                last_run_outcome="engineering_blocker",
                hf_uploader_configured=False,
                hf_sync_ok=True,
            )
            is True
        )

    def test_required_hf_sync_failure_stops(self) -> None:
        assert (
            _should_stop_after_terminal_run(
                last_run_outcome="scientific_success",
                hf_uploader_configured=True,
                hf_sync_ok=False,
            )
            is True
        )

    def test_unconfigured_hf_sync_failure_does_not_stop(self) -> None:
        assert (
            _should_stop_after_terminal_run(
                last_run_outcome="scientific_success",
                hf_uploader_configured=False,
                hf_sync_ok=False,
            )
            is False
        )
