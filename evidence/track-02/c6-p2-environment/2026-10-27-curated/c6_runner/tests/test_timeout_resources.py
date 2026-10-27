# -*- coding: utf-8 -*-
"""Timeout and resource overflow map to BLOCKED (infra), never PASS/FAIL."""
import json
import os

from c6runner.resources import ResourceLimits, run_limited, dir_size_mb
from c6runner.runner import C6Runner
from c6runner.verdicts import Verdict


def _fi(syn):
    doc = json.load(open(syn["frozen_inputs"], encoding="utf-8"))
    return {v["path"]: v["sha256"] for v in doc.values()}


def test_timeout_maps_to_blocked(syn, tmp_path):
    r = C6Runner(syn["freeze"], syn["auth"], syn["bare"], syn["ledger"],
                 syn["events"], os.path.dirname(syn["body"]),
                 str(tmp_path / "runs"), _fi(syn),
                 limits=ResourceLimits(timeout_s=1.0))
    import sys
    res = r.run_task(syn["target"],
                     command=[sys.executable, "-c", "import time; time.sleep(30)"],
                     test_paths=[syn["p_test"]], t_only_paths=[syn["t_only_test"]])
    assert res["verdict"] == Verdict.BLOCKED
    assert res["payload"]["execution"]["timeout"] is True


def test_disk_overflow_maps_to_blocked(syn, tmp_path):
    r = C6Runner(syn["freeze"], syn["auth"], syn["bare"], syn["ledger"],
                 syn["events"], os.path.dirname(syn["body"]),
                 str(tmp_path / "runs2"), _fi(syn),
                 limits=ResourceLimits(timeout_s=60, disk_mb=0.0001))
    import sys
    res = r.run_task(syn["target"],
                     command=[sys.executable, "-c",
                              "open('big.bin','wb').write(b'x'*(200*1024))"],
                     test_paths=[syn["p_test"]], t_only_paths=[syn["t_only_test"]])
    assert res["verdict"] == Verdict.BLOCKED
    assert res["payload"]["execution"]["resource_overflow"] is True


def test_trivial_command_is_vacuous_blocked(syn, tmp_path):
    """Negative control (F4): a trivial successful command executes ZERO
    tests and must NEVER map to PASS — it is a vacuous oracle -> BLOCKED."""
    r = C6Runner(syn["freeze"], syn["auth"], syn["bare"], syn["ledger"],
                 syn["events"], os.path.dirname(syn["body"]),
                 str(tmp_path / "runs3"), _fi(syn),
                 limits=ResourceLimits(timeout_s=60))
    import sys
    res = r.run_task(syn["target"],
                     command=[sys.executable, "-c", "print('ok')"],
                     test_paths=[syn["p_test"]], t_only_paths=[syn["t_only_test"]])
    assert res["verdict"] == Verdict.BLOCKED
    assert res["payload"]["execution"]["blocked_reason"] == "vacuous_oracle"


def test_valid_pytest_run_is_pass(syn, tmp_path):
    """Positive control: a genuine pytest run of the contract (2 tests pass)
    with a parsed report is a valid behavioral oracle -> PASS."""
    r = C6Runner(syn["freeze"], syn["auth"], syn["bare"], syn["ledger"],
                 syn["events"], os.path.dirname(syn["body"]),
                 str(tmp_path / "runs3b"), _fi(syn),
                 limits=ResourceLimits(timeout_s=60))
    import sys
    res = r.run_task(syn["target"],
                     command=[sys.executable, "-m", "pytest", "-q",
                              syn["p_test"], "-p", "no:cacheprovider"],
                     test_paths=[syn["p_test"]], t_only_paths=[])
    assert res["verdict"] == Verdict.PASS
    assert res["payload"]["execution"]["exit_code"] == 0
    assert res["payload"]["oracle_report"]["ran"] >= 1
    assert res["payload"]["execution"]["assertions_ok"] is True


def test_pytest_failure_report_maps_to_fail(tmp_path):
    """Semantic FAIL path: a REAL pytest run that ran tests and failed must
    map to FAIL (not BLOCKED), because the oracle report is valid."""
    import subprocess
    import sys
    from c6runner.oracle import parse_pytest_summary
    from c6runner.resources import RunResult
    from c6runner.verdicts import Verdict, decide_from_run

    d = tmp_path / "failproj"
    d.mkdir()
    (d / "test_f.py").write_text("def test_fail():\n    assert 1 == 2\n",
                                  encoding="utf-8")
    p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p",
                        "no:cacheprovider", "test_f.py"], cwd=str(d),
                       capture_output=True, text=True)
    report = parse_pytest_summary(p.stdout, exit_code=p.returncode)
    assert report.valid is True
    assert report.assertions_ok is False
    run = RunResult()
    run.exit_code = p.returncode
    run.assertions_ok = report.assertions_ok
    run.oracle_parity = (p.returncode == 0) and bool(run.assertions_ok)
    assert decide_from_run(run, object(), True) == Verdict.FAIL


def test_offline_gate_applied_by_default(syn, tmp_path):
    doc = json.load(open(syn["frozen_inputs"], encoding="utf-8"))
    r = C6Runner(syn["freeze"], syn["auth"], syn["bare"], syn["ledger"],
                 syn["events"], os.path.dirname(syn["body"]),
                 str(tmp_path / "runs5"), _fi(syn))
    import sys
    res = r.run_task(syn["target"],
                     command=[sys.executable, "-c", "import os; print(os.environ.get('C6_NETWORK_GATE'))"],
                     test_paths=[syn["p_test"]], t_only_paths=[syn["t_only_test"]])
    assert "1" in res["payload"]["execution"]["stdout_tail"]


def test_dir_size_mb_counts_work():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "a"), "wb") as f:
            f.write(b"x" * 1024)
        assert 0 < dir_size_mb(d) < 1