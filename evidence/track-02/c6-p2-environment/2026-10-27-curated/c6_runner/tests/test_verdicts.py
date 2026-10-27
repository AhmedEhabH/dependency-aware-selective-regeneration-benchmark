# -*- coding: utf-8 -*-
"""Verdict decision matrix: PASS/FAIL/BLOCKED separation and negative vs
reference oracle classification (decide_from_run unit tests)."""
import pytest

from c6runner.errors import CommandTimeout, ResourceOverflow
from c6runner.verdicts import Verdict, decide_from_run


class FakeRun:
    def __init__(self, exit_code=0, timeout=False, resource_overflow=False,
                 blocked_reason=None, assertions_ok=True, oracle_parity=None,
                 vacuous_oracle=False):
        self.exit_code = exit_code
        self.timeout = timeout
        self.resource_overflow = resource_overflow
        self.blocked_reason = blocked_reason
        self.assertions_ok = assertions_ok
        self.oracle_parity = oracle_parity
        self.vacuous_oracle = vacuous_oracle


class FakeLimits:
    pass


@pytest.mark.parametrize("run,oracle,expect", [
    (FakeRun(exit_code=0, oracle_parity=True), True, Verdict.PASS),
    (FakeRun(exit_code=0, oracle_parity=False), True, Verdict.FAIL),
    (FakeRun(exit_code=0, oracle_parity=None), False, Verdict.PASS),   # NEG oracle: no parity expectation
    (FakeRun(exit_code=1), True, Verdict.FAIL),
    (FakeRun(exit_code=0, assertions_ok=False), True, Verdict.FAIL),
    (FakeRun(exit_code=0, assertions_ok=None), True, Verdict.BLOCKED),
    (FakeRun(exit_code=0, assertions_ok=None, vacuous_oracle=True), True,
     Verdict.BLOCKED),
    (FakeRun(exit_code=0, timeout=True), True, Verdict.BLOCKED),
    (FakeRun(exit_code=0, resource_overflow=True), True, Verdict.BLOCKED),
    (FakeRun(exit_code=0, blocked_reason="env_mismatch"), True, Verdict.BLOCKED),
])
def test_decision_matrix(run, oracle, expect):
    assert decide_from_run(run, FakeLimits(), oracle) == expect


def test_negative_vs_reference_oracle_semantics():
    # reference oracle requires parity
    assert decide_from_run(FakeRun(exit_code=0, oracle_parity=False), FakeLimits(), True) == Verdict.FAIL
    # negative oracle has no positive parity expectation
    assert decide_from_run(FakeRun(exit_code=0, oracle_parity=None), FakeLimits(), False) == Verdict.PASS


def test_payload_schema_contains_five_field_identity(syn, tmp_path):
    import json
    import os
    from c6runner.runner import C6Runner
    doc = json.load(open(syn["frozen_inputs"], encoding="utf-8"))
    fi = {v["path"]: v["sha256"] for v in doc.values()}
    r = C6Runner(syn["freeze"], syn["auth"], syn["bare"], syn["ledger"],
                 syn["events"], os.path.dirname(syn["body"]),
                 str(tmp_path / "runs"), fi)
    res = r.run_task(syn["target"], preflight_only=True,
                     test_paths=[syn["p_test"]],
                     t_only_paths=[syn["t_only_test"]])
    ident = res["payload"]["identity"]
    for k in ("TASK_ID", "SCOPE_HASH", "REFERENCE_PATCH_HASH",
              "TEST_CONTRACT_HASH", "ENVIRONMENT_ID"):
        assert ident[k], k
    assert ident["TASK_ID"] == syn["target"]
    # receipt exists and its .sha256 sidecar equals the final bytes
    assert os.path.exists(res["receipt_path"])
    from c6runner.receipts import load_receipt
    _, digest = load_receipt(res["receipt_path"])
    side = open(res["receipt_path"] + ".sha256", encoding="utf-8").read().split()[0]
    assert digest == side