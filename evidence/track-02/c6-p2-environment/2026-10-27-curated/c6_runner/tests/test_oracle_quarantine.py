# -*- coding: utf-8 -*-
"""T-only evaluation tests are quarantined: present under oracle/, NEVER under
src/ (prospective task input)."""
import os

from c6runner.errors import C6Stop
from c6runner.runner import C6Runner
from conftest import T_ONLY_CONTENT


def _mk(syn, tmp_path):
    import json
    doc = json.load(open(syn["frozen_inputs"], encoding="utf-8"))
    fi = {v["path"]: v["sha256"] for v in doc.values()}
    return C6Runner(syn["freeze"], syn["auth"], syn["bare"], syn["ledger"],
                    syn["events"], os.path.dirname(syn["body"]),
                    str(tmp_path / "runs"), fi)


def test_t_only_test_in_oracle_dir_only(syn, tmp_path):
    r = _mk(syn, tmp_path)
    res = r.run_task(syn["target"], preflight_only=True,
                     test_paths=[syn["p_test"]], t_only_paths=[syn["t_only_test"]])
    oracle_path = os.path.join(res["workspace"], "oracle", syn["t_only_test"])
    src_path = os.path.join(res["workspace"], "src", syn["t_only_test"])
    assert os.path.exists(oracle_path), "T-only test must be materialized as oracle"
    assert open(oracle_path, encoding="utf-8").read() == T_ONLY_CONTENT
    assert not os.path.exists(src_path), "T-only test must NEVER appear in src"


def test_oracle_identity_in_receipt(syn, tmp_path):
    r = _mk(syn, tmp_path)
    res = r.run_task(syn["target"], preflight_only=True,
                     test_paths=[syn["p_test"]], t_only_paths=[syn["t_only_test"]])
    orb = res["payload"]["oracle_quarantine"]["t_only_files"]
    assert any(e["path"] == syn["t_only_test"] for e in orb)
    assert all(e["blob"] for e in orb)


def test_p_available_t_bytes_quarantined_in_oracle_not_src(syn, tmp_path):
    """F7 spec: the T bytes of EVERY M/A contract path (including P-available
    ones) are quarantined under oracle/ and NEVER enter the prospective input
    tree (src holds only the P bytes of that test file)."""
    r = _mk(syn, tmp_path)
    res = r.run_task(syn["target"], preflight_only=True,
                     test_paths=[syn["p_test"]], t_only_paths=[syn["t_only_test"]])
    ws = res["workspace"]
    oracle_p = os.path.join(ws, "oracle", syn["p_test"])
    src_p = os.path.join(ws, "src", syn["p_test"])
    assert os.path.exists(src_p), "P bytes of the M/A test must be in src"
    assert os.path.exists(oracle_p), \
        "T bytes of the M/A test must be quarantined under oracle/"
    n_src = open(src_p, encoding="utf-8").read().count("def test_")
    n_oracle = open(oracle_p, encoding="utf-8").read().count("def test_")
    assert n_src == 1 and n_oracle == 2, \
        f"src has the P version ({n_src}), oracle has the T version ({n_oracle})"