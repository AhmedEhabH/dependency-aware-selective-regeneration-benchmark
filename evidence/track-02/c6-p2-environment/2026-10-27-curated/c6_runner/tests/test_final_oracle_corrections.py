# -*- coding: utf-8 -*-
"""FINAL ORACLE CORRECTIONS — ISSUE 1 (all-skipped false pass).

RED tests against runner v0.3.0: a junit report containing ONLY skipped
(pytest.skip / pytest.xfail renders, or all-xpass, or zero-execution) is
currently parsed as a VALID oracle (ran counts skipped testcases, failures
== errors == 0, exit 0) and can produce a C6 PASS. The invariant asserted
here: a C6 PASS requires AT LEAST ONE genuinely executed, non-skipped test
and the skipped / xfailed / xpassed / zero-execution cases are tracked
explicitly and fail closed.

All junit XML shapes below are REAL bytes captured from pytest 8.3.4
(see work/c6_final_oracle_repro1.py + the raw output).
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from c6runner.oracle import parse_junit_report          # noqa: E402
from c6runner.resources import RunResult                # noqa: E402
from c6runner.verdicts import Verdict, decide_from_reference  # noqa: E402
from test_final_red import _variant_env, _runner        # noqa: E402

CONTRACT = ["tests/test_s.py"]

# Real pytest 8.3.4 junit bytes (classname/name simplified to the contract)
XML_ALL_SKIPPED = ('<?xml version="1.0" encoding="utf-8"?><testsuites>'
                   '<testsuite name="pytest" errors="0" failures="0" '
                   'skipped="2" tests="2">'
                   '<testcase classname="tests.test_s" name="test_skip_a">'
                   '<skipped type="pytest.skip" message="env unused"/></testcase>'
                   '<testcase classname="tests.test_s" name="test_skip_b">'
                   '<skipped type="pytest.skip" message="always off"/></testcase>'
                   '</testsuite></testsuites>')

XML_ALL_XFAIL = ('<?xml version="1.0" encoding="utf-8"?><testsuites>'
                 '<testsuite name="pytest" errors="0" failures="0" '
                 'skipped="2" tests="2">'
                 '<testcase classname="tests.test_s" name="test_xfail_a">'
                 '<skipped type="pytest.xfail" message="known gap"/></testcase>'
                 '<testcase classname="tests.test_s" name="test_xfail_b">'
                 '<skipped type="pytest.xfail" message="strict unset"/></testcase>'
                 '</testsuite></testsuites>')

# pytest renders XPASS testcases as PLAIN passed testcases (no marker) and the
# junit `skipped` attribute stays 0; only the terminal summary says "xpassed".
XML_ALL_XPASS = ('<?xml version="1.0" encoding="utf-8"?><testsuites>'
                 '<testsuite name="pytest" errors="0" failures="0" '
                 'skipped="0" tests="2">'
                 '<testcase classname="tests.test_s" name="test_xpass_a" '
                 'time="0.001"/>'
                 '<testcase classname="tests.test_s" name="test_xpass_b" '
                 'time="0.001"/>'
                 '</testsuite></testsuites>')

XML_MIXED = ('<?xml version="1.0" encoding="utf-8"?><testsuites>'
             '<testsuite name="pytest" errors="0" failures="0" '
             'skipped="2" tests="3">'
             '<testcase classname="tests.test_s" name="test_real_pass"/>'
             '<testcase classname="tests.test_s" name="test_skipped">'
             '<skipped type="pytest.skip" message="unused"/></testcase>'
             '<testcase classname="tests.test_s" name="test_xfailed">'
             '<skipped type="pytest.xfail" message="known gap"/></testcase>'
             '</testsuite></testsuites>')

XML_ZERO = ('<?xml version="1.0" encoding="utf-8"?><testsuites>'
            '<testsuite name="pytest" errors="0" failures="0" '
            'skipped="0" tests="0"/></testsuites>')


def _parse(xml_bytes, stdout, exit_code):
    import tempfile
    d = tempfile.mkdtemp(prefix="red_oracle_")
    p = os.path.join(d, "junit.xml")
    with open(p, "w", encoding="utf-8") as f:
        f.write(xml_bytes)
    return parse_junit_report(p, stdout, exit_code, CONTRACT)


def _run(run_rc, report):
    run = RunResult()
    run.exit_code = run_rc
    return run, report


# ---------------------------------------------------------------------------
# REPORT LEVEL — the four degeneracies must never be a valid PASS basis
# ---------------------------------------------------------------------------
def test_red_all_skipped_report_cannot_be_valid_pass():
    rep = _parse(XML_ALL_SKIPPED, "2 skipped in 0.06s\n", 0)
    # RED on v0.3.0: ran==2 (skipped testcases counted), valid True, PASS.
    assert rep.valid is False, \
        "all-skipped junit must not be a valid oracle: ran=%s" % rep.ran
    assert rep.assertions_ok is None, "all-skipped assertions must be unverified"
    run = RunResult()
    run.exit_code = 0
    assert decide_from_reference(run, rep, "POSITIVE_REFERENCE") \
        != Verdict.PASS


def test_red_all_xfail_report_cannot_be_valid_pass():
    rep = _parse(XML_ALL_XFAIL, "2 xfailed in 0.15s\n", 0)
    assert rep.valid is False, "all-xfail junit must be invalid (executed=0)"
    assert rep.xfailed == 2, "xfailed count must be explicit"
    assert rep.assertions_ok is None
    run = RunResult()
    run.exit_code = 0
    assert decide_from_reference(run, rep, "POSITIVE_REFERENCE") \
        != Verdict.PASS


def test_red_all_xpass_report_cannot_be_valid_pass():
    rep = _parse(XML_ALL_XPASS, "2 xpassed in 0.06s\n", 0)
    # xpass testcases ARE executed in junit terms, but every executed one was
    # an xpass: nothing genuinely passed as expected -> fail closed.
    assert rep.xpassed == 2, "xpassed count must be explicit"
    assert rep.valid is False, "all-xpass junit must be invalid (no genuine pass)"
    run = RunResult()
    run.exit_code = 0
    assert decide_from_reference(run, rep, "POSITIVE_REFERENCE") \
        != Verdict.PASS


def test_red_zero_execution_report_is_explicitly_vacuous():
    rep = _parse(XML_ZERO, "no tests ran in 0.01s\n", 5)
    assert rep.valid is False
    assert rep.vacuous is True
    assert rep.reason in ("no_tests", "zero_execution")
    run = RunResult()
    run.exit_code = 5
    assert decide_from_reference(run, rep, "POSITIVE_REFERENCE") \
        == Verdict.BLOCKED


def test_red_ran_is_only_genuinely_executed_non_skipped_tests():
    """`ran` must count testcases WITHOUT a <skipped> child only (real pytest:
    skip and xfail both render as <skipped>)."""
    rep = _parse(XML_MIXED, "1 passed, 1 skipped, 1 xfailed in 0.20s\n", 0)
    assert rep.ran == 1, "only test_real_pass genuinely executed: ran=%s" % rep.ran
    assert rep.skipped == 2          # junit skipped attribute (skip+xfail)
    assert rep.xfailed == 1          # explicit xfail bucket
    assert rep.valid is True         # one genuine executed green test exists
    run = RunResult()
    run.exit_code = 0
    assert decide_from_reference(run, rep, "POSITIVE_REFERENCE") \
        == Verdict.PASS


# ---------------------------------------------------------------------------
# E2E — a real pytest run whose contract is all-skipped must never PASS
# ---------------------------------------------------------------------------
T_SKIPPED = ("import pytest\n"
             "@pytest.mark.skip(reason='env unused')\n"
             "def test_skip_a():\n"
             "    assert True\n"
             "@pytest.mark.skipif(True, reason='always off')\n"
             "def test_skip_b():\n"
             "    assert True\n")

T_XFAIL = ("import pytest\n"
           "@pytest.mark.xfail(reason='known gap')\n"
           "def test_xf():\n"
           "    assert 1 == 2\n"
           "@pytest.mark.xfail(reason='known gap2')\n"
           "def test_xf2():\n"
           "    assert 2 == 3\n")

T_XPASS = ("import pytest\n"
           "@pytest.mark.xfail(reason='prevent strict')\n"
           "def test_xp():\n"
           "    assert True\n"
           "@pytest.mark.xfail(reason='prevent strict2')\n"
           "def test_xp2():\n"
           "    assert True\n")


@pytest.mark.parametrize("name,t_content,t_only_content", [
    ("all_skipped", T_SKIPPED,
     "import pytest\n@pytest.mark.skip(reason='no')\ndef test_y_skip():\n    assert True\n"),
    ("all_xfail", T_XFAIL,
     "import pytest\n@pytest.mark.xfail(reason='gap')\ndef test_y_xf():\n    assert 1 == 2\n"),
    ("all_xpass", T_XPASS,
     "import pytest\n@pytest.mark.xfail(reason='prevent')\ndef test_y_xp():\n    assert True\n"),
])
def test_red_e2e_degenerate_contract_never_pass(tmp_path, name, t_content,
                                                t_only_content):
    """E2E: the FULL M/A contract (P-available + T-only files together) made
    of skip/xfail/xpass only must NEVER produce a C6 PASS — the reference has
    no genuinely executed, non-skipped test."""
    env = _variant_env(tmp_path, t_test_content=t_content,
                       t_only_content=t_only_content)
    r = _runner(env, tmp_path)
    res = r.run_task(env["target"], plan=env["plan"])
    assert res["verdict"] != Verdict.PASS, \
        f"{name}: degenerate contract produced {res['verdict'].value}"
    # fail closed: a vacuous reference is BLOCKED, never semantic
    assert res["verdict"] == Verdict.BLOCKED
    report = res["payload"].get("oracle_report") or {}
    assert report.get("valid") is False, \
        f"{name}: reference report must be invalid: {report.get('reason')}"


def test_red_e2e_zero_execution_never_pass(tmp_path):
    """E2E: the M/A contract contains NO tests at all (pytest exit 5,
    tests=0) -> vacuous BLOCKED, never PASS/FAIL."""
    env = _variant_env(tmp_path, t_test_content="# no tests here\n",
                       t_only_content="# no tests here either\n")
    r = _runner(env, tmp_path)
    res = r.run_task(env["target"], plan=env["plan"])
    assert res["verdict"] != Verdict.PASS
    assert res["verdict"] == Verdict.BLOCKED
    # the reference junit report must be explicitly vacuous
    report = res["payload"].get("oracle_report") or {}
    assert report.get("vacuous") is True or report.get("valid") is False
