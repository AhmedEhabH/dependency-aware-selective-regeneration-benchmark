# -*- coding: utf-8 -*-
"""Dependency / source integrity failures must fail closed."""
import json
import os

from c6runner.errors import C6Stop, FrozenInputDrift
from c6runner.hashes import sha256_file
from c6runner.runner import C6Runner


def _mk(syn, tmp_path):
    doc = json.load(open(syn["frozen_inputs"], encoding="utf-8"))
    fi = {v["path"]: v["sha256"] for v in doc.values()}
    return C6Runner(syn["freeze"], syn["auth"], syn["bare"], syn["ledger"],
                    syn["events"], os.path.dirname(syn["body"]),
                    str(tmp_path / "runs"), fi)


def _run(r, syn):
    return r.run_task(syn["target"], preflight_only=True,
                      test_paths=[syn["p_test"]], t_only_paths=[syn["t_only_test"]])


def test_ledger_c5_hash_drift_is_stop(syn, tmp_path):
    # tamper the ledger row's C5_test_paths_hash -> recompute mismatch -> STOP
    rows = [json.loads(l) for l in open(syn["ledger"], encoding="utf-8")]
    rows[0]["C5_test_paths_hash"] = "0" * 64
    tampered = os.path.join(syn["data_dir"], "ledger_tampered.jsonl")
    with open(tampered, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    doc = json.load(open(syn["frozen_inputs"], encoding="utf-8"))
    fi = {v["path"]: v["sha256"] for v in doc.values()}
    # swap in tampered ledger and rehash the declaration
    fi = {**fi}
    fi[tampered] = sha256_file(tampered)
    fi.pop(syn["ledger"])
    try:
        r = C6Runner(syn["freeze"], syn["auth"], syn["bare"], tampered,
                     syn["events"], os.path.dirname(syn["body"]),
                     str(tmp_path / "runs2"), fi)
        _run(r, syn)
        raise AssertionError("expected STOP on C5 hash drift")
    except FrozenInputDrift:
        pass


def test_frozen_input_hash_mismatch_is_stop(syn, tmp_path):
    doc = json.load(open(syn["frozen_inputs"], encoding="utf-8"))
    fi = {v["path"]: v["sha256"] for v in doc.values()}
    fi[syn["events"]] = "0" * 64  # wrong declared hash
    r = C6Runner(syn["freeze"], syn["auth"], syn["bare"], syn["ledger"],
                 syn["events"], os.path.dirname(syn["body"]),
                 str(tmp_path / "runs3"), fi)
    try:
        r.verify_frozen_inputs()
        raise AssertionError("expected STOP on frozen-input mismatch")
    except FrozenInputDrift:
        pass


def test_missing_frozen_input_is_stop(syn, tmp_path):
    doc = json.load(open(syn["frozen_inputs"], encoding="utf-8"))
    fi = {v["path"]: v["sha256"] for v in doc.values()}
    fi[os.path.join(syn["data_dir"], "does_not_exist.jsonl")] = "0" * 64
    r = C6Runner(syn["freeze"], syn["auth"], syn["bare"], syn["ledger"],
                 syn["events"], os.path.dirname(syn["body"]),
                 str(tmp_path / "runs4"), fi)
    try:
        r.verify_frozen_inputs()
        raise AssertionError("expected STOP on missing frozen input")
    except FrozenInputDrift:
        pass


def test_unknown_candidate_is_blocked(syn, tmp_path):
    r = _mk(syn, tmp_path)
    res = r.run_task("1" * 40, preflight_only=True,
                     test_paths=[syn["p_test"]], t_only_paths=[])
    assert res["verdict"].value == "BLOCKED"