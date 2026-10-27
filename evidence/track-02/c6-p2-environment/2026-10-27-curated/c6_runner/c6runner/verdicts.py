# -*- coding: utf-8 -*-
"""Verdict taxonomy. PASS/FAIL/BLOCKED/GLOBAL_STOP are distinct; the safety
gate reads exit code + assertions + oracle parity, never a PASS string."""
import enum


class Verdict(enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    GLOBAL_STOP = "GLOBAL_STOP"


VERDICT_STOP_LIKE = {Verdict.BLOCKED, Verdict.GLOBAL_STOP}
VERDICT_SEMANTIC = {Verdict.PASS, Verdict.FAIL}


def decide_from_run(run, limits, oracle_expected_ok: bool) -> Verdict:
    """Deterministic verdict mapping.

    run: RunResult(exit_code, timeout, resource_overflow, assertions_ok,
                   oracle_parity, vacuous_oracle)
    - timeout/resource overflow/blocked_reason -> BLOCKED (infra, not semantic)
    - assertions_ok is None (oracle not established: no report / 0 tests ran)
      -> BLOCKED (vacuous oracle) — a trivial successful command can never PASS
    - exit != 0 or assertions failed -> FAIL (semantic) when env is valid
    - exit == 0 + assertions ok + oracle parity -> PASS
    """
    if run.timeout:
        return Verdict.BLOCKED
    if run.resource_overflow:
        return Verdict.BLOCKED
    if run.blocked_reason:
        return Verdict.BLOCKED
    if getattr(run, "vacuous_oracle", False):
        return Verdict.BLOCKED
    if run.assertions_ok is None:
        # no valid oracle was established (no report, or no tests ran)
        return Verdict.BLOCKED
    if run.exit_code != 0 or not run.assertions_ok:
        return Verdict.FAIL
    if oracle_expected_ok and not run.oracle_parity:
        return Verdict.FAIL
    return Verdict.PASS


def decide_from_reference(run, junit_report, oracle_mode) -> Verdict:
    """Verdict from one evaluation-only reference ROLE (issue 2).

    - No machine-readable junit evidence / vacuous (incl. all-skipped /
      all-xfail / all-xpass / zero-execution) / identity or consistency
      failure -> BLOCKED (never PASS; findings F3 + issue 1).
    - POSITIVE_REFERENCE (P2P = T code + T tests): PASS iff report valid,
      >=1 genuinely executed non-skipped test, failures==errors==0 and
      exit 0; any executed semantic failure -> FAIL.
    - NEG_TESTS_EXPECTED_FAIL (F2P = P code + T tests): PASS iff report
      valid and semantic failures exist with exit != 0 (the negative
      baseline failed as expected); an unexpectedly green run -> FAIL.
    - NONE: no reference contract -> BLOCKED here (caller must not route).
    `run` carries timeout/overflow/blocked infra markers. An expected F2P
    failure is recorded as the baseline outcome by the caller (never as a
    broken environment).
    """
    if run.timeout or run.resource_overflow or run.blocked_reason:
        return Verdict.BLOCKED
    if junit_report is None or not junit_report.valid:
        return Verdict.BLOCKED
    ok = (junit_report.failures == 0 and junit_report.errors == 0)
    if oracle_mode == "POSITIVE_REFERENCE":
        return Verdict.PASS if (ok and run.exit_code == 0) else Verdict.FAIL
    if oracle_mode == "NEG_TESTS_EXPECTED_FAIL":
        return Verdict.PASS if (not ok and run.exit_code != 0) else Verdict.FAIL
    return Verdict.BLOCKED