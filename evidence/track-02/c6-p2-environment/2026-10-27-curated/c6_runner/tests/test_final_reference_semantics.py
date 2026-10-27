# -*- coding: utf-8 -*-
"""FINAL ORACLE CORRECTIONS — ISSUE 2 (negative / positive reference roles).

RED tests against runner v0.3.0. The mission mandates SEPARATE evaluation
roles:

  P code + P tests          -> starting-environment diagnostic (never PASS)
  P code + T tests          -> negative baseline F2P, evaluation-only
  T code + T tests          -> positive reference P2P, evaluation-only
  generated code + eval tests -> future E2E gate (NOT implemented here)

On v0.3.0 the reference runs P code + T tests only, labels it
POSITIVE_REFERENCE, grants PASS when the F2P tree goes green, turns an F2P
expected failure into FAIL (POSITIVE mode) or PASS (NEG mode), and lets a
green P/P diagnostic produce PASS in NONE mode. Every invariant below is
RED today.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from c6runner.errors import Blocked        # noqa: E402
from c6runner.verdicts import Verdict       # noqa: E402
from test_final_red import P_CONTENT, _variant_env, _runner  # noqa: E402

# A defect-detecting T test: its behavior depends on the T code fix
# ("VALUE = 2" only exists in the T code tree). On P code it must FAIL,
# on T code it must PASS.
T_TEST_REQUIRES_FIX = (
    "def test_code_has_fix():\n"
    "    with open('src/x.py') as f:\n"
    "        assert f.read() == 'VALUE = 2\\n'\n"
)


def _env_fix_detecting(tmp_path, oracle_mode="POSITIVE_REFERENCE"):
    return _variant_env(tmp_path, t_test_content=T_TEST_REQUIRES_FIX,
                        t_only_content="def test_oracle_y():\n    assert True\n",
                        oracle_mode=oracle_mode)


# ---------------------------------------------------------------------------
# P2P POSITIVE REFERENCE — T code + T tests
# ---------------------------------------------------------------------------
def test_red_p2p_positive_reference_uses_t_code_e2e(tmp_path):
    """The positive reference (T code + T tests) must gate the verdict: a
    defect-detecting contract is GREEN on T code -> PASS. v0.3.0 evaluates
    P code + T tests (which fails) -> FAIL. RED."""
    env = _env_fix_detecting(tmp_path)
    r = _runner(env, tmp_path)
    res = r.run_task(env["target"], plan=env["plan"])
    assert res["verdict"] == Verdict.PASS, \
        f"positive reference on T code must PASS, got {res['verdict'].value}"


def test_red_p2p_reference_tree_contains_t_code_not_p_code(tmp_path):
    """Workspace: the positive-reference evaluation tree must contain the T
    code bytes (VALUE=2); the F2P tree must contain P code (VALUE=1); the
    prospective input src/ must keep ONLY P bytes (VALUE=1)."""
    env = _env_fix_detecting(tmp_path)
    r = _runner(env, tmp_path)
    res = r.run_task(env["target"], plan=env["plan"])
    ws = res["workspace"]
    src_x = os.path.join(ws, "src", "src", "x.py")
    assert open(src_x, encoding="utf-8").read() == "VALUE = 1\n", \
        "prospective input must be P bytes only"
    # P2P tree (positive reference): T code + T tests
    p2p_x = os.path.join(ws, "eval_work", "src", "x.py")
    assert os.path.exists(p2p_x)
    assert open(p2p_x, encoding="utf-8").read() == "VALUE = 2\n", \
        "P2P evaluation tree must carry T CODE bytes, got the P byte value"

    # every evaluation tree must be labelled by role in the receipt
    roles = res["payload"].get("reference_definition", {}).get("roles") or {}
    assert roles.get("p2p") and roles.get("f2p") and roles.get("diagnostic"), \
        "reference roles must be explicitly enumerated: %r" % (roles,)


def test_red_f2p_expected_failure_not_broken_environment(tmp_path):
    """An expected F2P failure (P code + T tests red) must be recorded as the
    expected negative-baseline outcome — NOT BLOCKED as a broken environment
    — while the P2P-positive verdict stands."""
    env = _env_fix_detecting(tmp_path)
    r = _runner(env, tmp_path)
    res = r.run_task(env["target"], plan=env["plan"])
    payload = res["payload"]
    f2p = payload.get("negative_baseline_f2p") or {}
    assert f2p, "F2P negative-baseline evidence block missing"
    assert f2p.get("role") == "f2p", "F2P evidence must carry role label"
    assert f2p.get("outcome") == "expected_failure", \
        "expected F2P failure must be classified as expected_failure, got %r" \
        % f2p.get("outcome")
    assert res["verdict"] == Verdict.PASS, \
        "an expected F2P failure must not flip the P2P-positive verdict"
    # infra-failure markers must be absent for a valid failing baseline
    assert not f2p.get("blocked_reason")


def test_red_diagnostic_pp_never_pass_in_none_mode(tmp_path):
    """P code + P tests is a STARTING-ENVIRONMENT DIAGNOSTIC: even when it is
    green it must NEVER be a C6 PASS (no T reference contract). v0.3.0 NONE
    mode returns PASS. RED."""
    env = _env_fix_detecting(tmp_path, oracle_mode="NONE")
    r = _runner(env, tmp_path)
    res = r.run_task(env["target"], plan=env["plan"])
    assert res["verdict"] != Verdict.PASS, \
        "diagnostic P/P run must never be a PASS source"
    assert res["verdict"] in (Verdict.BLOCKED, Verdict.FAIL)


def test_red_green_pp_diagnostic_evidence_preserved(tmp_path):
    """The diagnostic evidence (P code + P tests) must be recorded distinctly
    in the receipt (starting_environment_diagnostic role)."""
    env = _env_fix_detecting(tmp_path)
    r = _runner(env, tmp_path)
    res = r.run_task(env["target"], plan=env["plan"])
    roles = res["payload"].get("reference_definition", {}).get("roles") or {}
    diag = roles.get("diagnostic") or {}
    assert diag.get("content") == "P code + P tests"


def test_red_t_bytes_never_prospective_input(tmp_path):
    """T code, T tests, the reference patch and oracle answers never become
    selector/generator-visible: src/ holds only P bytes; T-only paths are
    absent from the input command; the T code bytes appear ONLY in the P2P
    evaluation tree."""
    env = _env_fix_detecting(tmp_path)
    r = _runner(env, tmp_path)
    res = r.run_task(env["target"], plan=env["plan"])
    ws = res["workspace"]
    src_x = os.path.join(ws, "src", "src", "x.py")
    assert open(src_x, encoding="utf-8").read() == P_CONTENT["src/x.py"]
    # T-only oracle test may not exist under src/
    assert not os.path.exists(os.path.join(ws, "src", env["t_only"])), \
        "T-only test leaked into the prospective input"
    # input run command must not contain T-only paths
    in_cmd = res["payload"].get("execution", {}).get("effective_command") or []
    joined = " ".join(in_cmd)
    assert env["t_only"] not in joined, \
        "input run must never exercise T-only contract paths"
    # T code bytes are confined to the P2P evaluation tree
    src_bytes = open(src_x, encoding="utf-8").read()
    assert "VALUE = 2" not in src_bytes, "T code leaked into src/"


def test_red_neg_mode_expected_failure_is_f2p_grounded(tmp_path):
    """NEG_TESTS_EXPECTED_FAIL mode PASSes only when the F2P (P code + T
    tests) run genuinely fails; the receipt must show the F2P role, not a
    generic reference."""
    env = _env_fix_detecting(tmp_path, oracle_mode="NEG_TESTS_EXPECTED_FAIL")
    r = _runner(env, tmp_path)
    res = r.run_task(env["target"], plan=env["plan"])
    f2p = res["payload"].get("negative_baseline_f2p") or {}
    assert f2p.get("role") == "f2p" and f2p.get("outcome") == "expected_failure"
    # F2P baseline failed as expected -> NEG mode PASS (control behaved)
    assert res["verdict"] == Verdict.PASS
