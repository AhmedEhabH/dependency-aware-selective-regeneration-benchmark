# -*- coding: utf-8 -*-
"""Isolation: per-task workspaces are fresh, T-only oracle bytes never leak
into the prospective source tree, marker files do not cross tasks."""
import os

from c6runner.errors import C6Stop
from c6runner.resources import ResourceLimits, run_limited
from c6runner.runner import C6Runner


def make_runner(syn, tmp_path, offline=True):
    return C6Runner(
        freeze_path=syn["freeze"], auth_path=syn["auth"],
        git_dir=syn["bare"], ledger_path=syn["ledger"],
        h2_events_path=syn["events"], protected_cache_dir=os.path.dirname(syn["body"]),
        out_root=str(tmp_path / "runs"), frozen_inputs=_fi(syn),
        limits=ResourceLimits(timeout_s=30), offline=offline)


def _fi(syn):
    import json
    doc = json.load(open(syn["frozen_inputs"], encoding="utf-8"))
    return {v["path"]: v["sha256"] for v in doc.values()}


def test_two_tasks_get_distinct_workspaces(syn, tmp_path):
    r1 = make_runner(syn, tmp_path)
    out1 = r1.run_task(syn["target"], preflight_only=True,
                       test_paths=[syn["p_test"]], t_only_paths=[syn["t_only_test"]])
    out2 = r1.run_task(syn["target"], preflight_only=True,
                       test_paths=[syn["p_test"]], t_only_paths=[syn["t_only_test"]])
    assert out1["workspace"] != out2["workspace"]
    assert not os.path.commonpath([out1["workspace"], out2["workspace"]]).startswith(
        out1["workspace"] + os.sep)


def test_marker_does_not_leak_between_tasks(syn, tmp_path):
    r1 = make_runner(syn, tmp_path)
    res = r1.run_task(syn["target"], preflight_only=True,
                      test_paths=[syn["p_test"]], t_only_paths=[syn["t_only_test"]])
    # command not run in preflight; write a marker via run_limited inside task ws
    ws = res["workspace"]
    marker = os.path.join(ws, "src", "MARKER")
    with open(marker, "w") as f:
        f.write("leak")
    res2 = r1.run_task(syn["target"], preflight_only=True,
                       test_paths=[syn["p_test"]], t_only_paths=[syn["t_only_test"]])
    assert not os.path.exists(os.path.join(res2["workspace"], "src", "MARKER"))


def test_parent_materialized_at_src(syn, tmp_path):
    r1 = make_runner(syn, tmp_path)
    res = r1.run_task(syn["target"], preflight_only=True,
                      test_paths=[syn["p_test"]], t_only_paths=[syn["t_only_test"]])
    src = os.path.join(res["workspace"], "src")
    assert os.path.exists(os.path.join(src, "src", "x.py"))          # P layout
    assert open(os.path.join(src, "src", "x.py"), encoding="utf-8").read() == "VALUE = 1\n"  # P content
    # P-available test file present in the prospective source tree
    assert os.path.exists(os.path.join(src, "tests", "test_x.py"))


def test_offline_gate_blocks_network_in_child(syn, tmp_path):
    r1 = make_runner(syn, tmp_path)
    res = r1.run_task(syn["target"], preflight_only=True,
                      test_paths=[syn["p_test"]], t_only_paths=[syn["t_only_test"]])
    from c6runner.resources import run_limited
    rr = run_limited(
        [sys_executable(), "-c",
         "import urllib.request; urllib.request.urlopen('http://127.0.0.1:1')"],
        os.path.join(res["workspace"], "src"),
        ResourceLimits(timeout_s=30),
        os.path.join(res["workspace"], "logs"))
    assert rr.exit_code != 0
    assert rr.python_gate_active is True
    assert rr.os_isolation_active is False
    # the sitecustomize gate is python-children-only; it must NEVER be
    # reported as OS-level network enforcement (Finding F3)
    assert rr.network_enforced is False


def sys_executable():
    import sys
    return sys.executable