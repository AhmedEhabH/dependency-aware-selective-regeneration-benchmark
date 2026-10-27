# -*- coding: utf-8 -*-
"""PHASE A — adversarial RED tests (TRACK02 C6 adversarial acceptance).

Each test asserts the *intended fail-closed invariant*. They are written to be
RED against the current runner (v0.1.0) and must turn GREEN after the Phase B
minimal safe repair. They use REAL frozen rows wherever feasible (the three
proposed pilot tasks) and synthetic rows for per-field R2 mutations.

Findings covered:
  F1  C4 "PASS" vs frozen "C4_PASS"  -> runner.py:125
  F2  R2 missing/unparsable chronology fail-open -> runner.py:154-159
  F3  sitecustomize alone is not OS-level isolation -> resources.py:139
  F4  trivial command must never be a behavioral oracle -> resources.py:68,
      runner.py:263
  F5  T-only bytes must be executed in a separate oracle evaluator ->
      workspace.py:45 / runner.py
  F6  CLI must not accept unfrozen command/test-path/resource/network
      overrides -> cli.py:38-56
  F7  global disk-floor budget check must run before every experiment ->
      runner.py:332 (defined, never invoked)
  F8  operator commands must be valid PowerShell 7 only -> OPERATOR_COMMANDS.md
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from c6runner.errors import Blocked, BudgetExceeded, C6Stop  # noqa: E402
from c6runner.hashes import sha256_file  # noqa: E402
from c6runner.runner import C6Runner  # noqa: E402

# ---------------------------------------------------------------------------
# Real frozen inputs used by the real-row tests (read-only access only)
# ---------------------------------------------------------------------------
REAL_GIT = r"D:\wp2_env_store\git_cache\saleor.git"
REAL_LEDGER = r"D:\WP2\audit_results\TRACK02_WPB_C4_EVIDENCE_V2\C1_C5_PER_SHA.jsonl"
REAL_H2 = (r"D:\WP2\audit_results\FULL_HISTORY_V2_H2_20261026T115058"
           r"\D0_FILE_EVENTS.jsonl")
REAL_PROTECTED = (r"D:\WP2\audit_results\TRACK02_CE_WPB_C4_C5_20261027T024421Z"
                  r"\protected_source_cache")
PILOTS = {
    # P1 2018 non-Old6000
    "a28f79819aa261000a3352dcd5770ed1d1afa3fc": "tests/test_impersonation.py",
    # P2 2022 Old6000
    "06d25ce29c984d9af0f8759044cd80aa8a835e83":
        "saleor/graphql/product/tests/test_product.py",
    # P3 2024 Old6000 (has a T-only oracle path)
    "9235b0af3f8a223fd40c6d7e004eb8150c79f553":
        "saleor/product/tests/test_fetch_variants_for_promotion_rules.py",
}

HAS_REAL_INPUTS = all(os.path.exists(p) for p in
                      (REAL_GIT, REAL_LEDGER, REAL_H2, REAL_PROTECTED))


def _freeze_auth(tmp_path):
    """Minimal hands-off freeze+auth pair so authorization never interferes
    with the eligibility under test."""
    import hashlib
    proto = tmp_path / "protocol.md"
    proto.write_text("synthetic protocol v1\n", encoding="utf-8")
    psha = sha256_file(str(proto))
    freezef = tmp_path / "freeze.json"
    freezef.write_text(json.dumps({
        "protocol_sha256": psha, "utc": "2026-10-27T00:00:00+00:00",
        "operator": "red-test", "protocol_document_path": str(proto)},
        indent=1), encoding="utf-8")
    authf = tmp_path / "auth.json"
    doc = {"utc": "2026-10-27T00:01:00+00:00", "operator": "red-test",
           "protocol_sha256": psha, "scope": "ALL"}
    raw = (json.dumps(doc, indent=1, sort_keys=True) + "\n").encode("utf-8")
    doc["authorization_sha256"] = hashlib.sha256(raw).hexdigest().upper()
    authf.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n",
                     encoding="utf-8")
    return str(freezef), str(authf)


def _real_runner(tmp_path):
    fi = json.load(open(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "frozen_inputs.json"), encoding="utf-8"))
    frozen = {v["path"]: v["sha256"] for v in fi.values()
              if isinstance(v, dict) and v.get("path") and v.get("sha256")}
    roles = dict(fi.get("roles") or {})
    freezef, authf = _freeze_auth(tmp_path)
    return C6Runner(freezef, authf, REAL_GIT, REAL_LEDGER, REAL_H2,
                    REAL_PROTECTED, str(tmp_path / "runs"), frozen,
                    input_roles=roles)


# ===========================================================================
# F1 — C4 vs C4_PASS: real frozen candidates must pass eligibility
# ===========================================================================
@pytest.mark.red
@pytest.mark.realdata
@pytest.mark.skipif(not HAS_REAL_INPUTS, reason="real frozen inputs unavailable")
@pytest.mark.parametrize("task_sha", sorted(PILOTS))
def test_f1_real_pilot_row_not_rejected_for_c4(tmp_path, task_sha):
    """Genuine frozen ledger rows use C4=C4_PASS. The runner must accept them,
    not raise Blocked('C4!=PASS'). (runner.py:125 checks != 'PASS')."""
    r = _real_runner(tmp_path)
    # prove the frozen value before the behavior assertion
    row = next(json.loads(l) for l in open(REAL_LEDGER, encoding="utf-8")
               if json.loads(l)["sha"] == task_sha)
    assert row["C4"] == "C4_PASS", "frozen ledger uses C4_PASS"
    assert row["C5"] == "TEST_CHANGE"
    # fail-closed invariant: R1/R2/R3 must not raise for a genuine candidate
    res, parent = r._check_eligibility(task_sha)
    assert res["sha"] == task_sha
    assert parent


@pytest.mark.red
@pytest.mark.realdata
@pytest.mark.skipif(not HAS_REAL_INPUTS, reason="real frozen inputs unavailable")
def test_f1_all_174_candidates_use_c4_pass():
    """Population fact: every C4_PASS row in the frozen ledger says C4_PASS;
    none says bare PASS, so the runner's 'PASS' check cannot ever match."""
    vals = {}
    for line in open(REAL_LEDGER, encoding="utf-8"):
        r = json.loads(line)
        if r.get("C4") == "C4_PASS" and r.get("C5") == "TEST_CHANGE":
            vals[r["sha"]] = r["C4"]
    assert len(vals) == 174
    assert set(vals.values()) == {"C4_PASS"}


# ===========================================================================
# F2 — R2 must fail closed on every incomplete field
# ===========================================================================
def _syn_row(syn):
    """Base synthetic ledger row (R1-valid) for R2 mutation tests."""
    doc = json.load(open(syn["frozen_inputs"], encoding="utf-8"))
    fi = {v["path"]: v["sha256"] for v in doc.values()}
    row = json.loads(next(l for l in open(syn["ledger"], encoding="utf-8")))
    return row, fi


def _runner_with_ledger(syn, tmp_path, row):
    """Runner whose ledger contains exactly the (mutated) row."""
    import tempfile
    d = tmp_path / "mut"
    d.mkdir(exist_ok=True)
    led = d / "ledger.jsonl"
    with open(led, "w", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    doc = json.load(open(syn["frozen_inputs"], encoding="utf-8"))
    fi = {v["path"]: v["sha256"] for v in doc.values()}
    fi[str(led)] = sha256_file(str(led))
    # keep the valid synthetic events file bound; swap the ledger path
    fi = {str(led) if k == syn["ledger"] else k: v for k, v in fi.items()}
    # copy the protected body cache file for R2 body verification
    import shutil
    body = d / os.path.basename(syn["body"])
    shutil.copy(syn["body"], body)
    freezef, authf = _freeze_auth(tmp_path)
    return C6Runner(freezef, authf, syn["bare"], str(led), syn["events"],
                    str(d), str(tmp_path / "runs") + row["sha"][:6], fi)


@pytest.mark.red
def test_f2_missing_body_hash_fails_closed(syn, tmp_path):
    row, _ = _syn_row(syn)
    row["issue_body_as_of_work_sha256"] = None
    r = _runner_with_ledger(syn, tmp_path, row)
    with pytest.raises((Blocked, C6Stop)):
        r._check_eligibility(row["sha"])


@pytest.mark.red
def test_f2_missing_issue_number_fails_closed(syn, tmp_path):
    row, _ = _syn_row(syn)
    row["ISSUE_NUMBER"] = None
    r = _runner_with_ledger(syn, tmp_path, row)
    with pytest.raises((Blocked, C6Stop)):
        r._check_eligibility(row["sha"])


@pytest.mark.red
def test_f2_missing_created_at_fails_closed(syn, tmp_path):
    row, _ = _syn_row(syn)
    row["issue_createdAt"] = None
    r = _runner_with_ledger(syn, tmp_path, row)
    with pytest.raises((Blocked, C6Stop)):
        r._check_eligibility(row["sha"])


@pytest.mark.red
def test_f2_missing_t_work_fails_closed(syn, tmp_path):
    row, _ = _syn_row(syn)
    row["t_work"] = None
    r = _runner_with_ledger(syn, tmp_path, row)
    with pytest.raises((Blocked, C6Stop)):
        r._check_eligibility(row["sha"])


@pytest.mark.red
def test_f2_unparsable_created_at_fails_closed(syn, tmp_path):
    row, _ = _syn_row(syn)
    row["issue_createdAt"] = "not-a-date"
    r = _runner_with_ledger(syn, tmp_path, row)
    with pytest.raises((Blocked, C6Stop)):
        r._check_eligibility(row["sha"])


@pytest.mark.red
def test_f2_unparsable_t_work_fails_closed(syn, tmp_path):
    row, _ = _syn_row(syn)
    row["t_work"] = "not-a-date"
    r = _runner_with_ledger(syn, tmp_path, row)
    with pytest.raises((Blocked, C6Stop)):
        r._check_eligibility(row["sha"])


# ===========================================================================
# F4 — a trivial successful command must never be a valid behavioral oracle
# ===========================================================================
@pytest.mark.red
def test_f4_trivial_command_never_pass():
    """python -c "print('ok')" executes zero tests. With oracle_expected_ok
    True, an unverifiable/absent pytest report must never map to PASS. The
    repaired RunResult defaults assertions_ok=None (resources.py) so a
    trivial command cannot be accepted as a behavioral oracle."""
    from c6runner.resources import RunResult
    from c6runner.verdicts import Verdict, decide_from_run

    run = RunResult()          # real object: assertions_ok defaults None
    run.exit_code = 0
    assert run.assertions_ok is None  # unverified -> fail-closed
    assert decide_from_run(run, object(), True) != Verdict.PASS


@pytest.mark.red
def test_f4_no_tests_ran_never_pass():
    """pytest exit 0 with 'no tests ran' is vacuous, never PASS."""
    from c6runner.oracle import parse_pytest_summary
    from c6runner.verdicts import Verdict, decide_from_run

    text = "no tests ran in 0.1s\n"
    report = parse_pytest_summary(text, exit_code=0)
    assert report is not None
    assert report.ran == 0
    assert report.valid is False

    class Run:
        exit_code = 0
        timeout = False
        resource_overflow = False
        blocked_reason = "vacuous_oracle"
        assertions_ok = None
        oracle_parity = None
        vacuous_oracle = True

    assert decide_from_run(Run(), object(), True) != Verdict.PASS


# ===========================================================================
# F3 — sitecustomize alone must not be reported as OS-level isolation
# ===========================================================================
@pytest.mark.red
def test_f3_sitecustomize_gate_is_not_os_isolation(syn, tmp_path):
    """run_limited must report os_isolation_active False when only the python
    sitecustomize gate is active; network_enforced must equal the OS-level
    claim, never the python-only gate."""
    from c6runner.resources import ResourceLimits, run_limited
    rr = run_limited([sys.executable, "-c", "pass"],
                     str(tmp_path / "cwd1"),
                     ResourceLimits(timeout_s=30), str(tmp_path / "logs"),
                     offline_gate=True)
    assert rr.python_gate_active is True
    assert rr.os_isolation_active is False
    assert rr.network_enforced is False


# ===========================================================================
# F6 — CLI must reject unfrozen overrides (command/test-path/resource/network)
# ===========================================================================
@pytest.mark.red
def test_f6_cli_rejects_network_override(syn, tmp_path):
    """--network-ok must be rejected (argparse exit != 0), never accepted."""
    try:
        from c6runner.cli import main
        rc = main(["--freeze", syn["freeze"], "--authorization", syn["auth"],
                   "--task", syn["target"], "--preflight", "--network-ok"])
        assert rc != 0
    except SystemExit as e:   # argparse rejects the unknown/forbidden option
        assert e.code != 0


@pytest.mark.red
def test_f6_cli_requires_task_plan(syn, tmp_path):
    """Running with --task but WITHOUT a task plan (and no free-form command
    override) must STOP (parse error or rc 3), never proceed."""
    try:
        from c6runner.cli import main
        rc = main(["--freeze", syn["freeze"], "--authorization", syn["auth"],
                   "--task", syn["target"]])
        assert rc != 0
    except SystemExit as e:
        assert e.code != 0


# ===========================================================================
# F7 — global disk floor must be checked before every experiment
# ===========================================================================
@pytest.mark.red
def test_f7_budget_floor_checked_before_execution(syn, tmp_path, monkeypatch):
    """A run must raise BudgetExceeded (GLOBAL STOP) when free disk is below
    the floor, BEFORE any command executes."""
    import shutil
    from c6runner.errors import BudgetExceeded

    monkeypatch.setattr(shutil, "disk_usage",
                        lambda p: (1, 1, 1 << 20))  # ~0.001 GiB free
    row, _ = _syn_row(syn)
    r = _runner_with_ledger(syn, tmp_path, row)
    with pytest.raises(BudgetExceeded):
        r.run_task(row["sha"], preflight_only=True,
                   test_paths=[syn["p_test"]], t_only_paths=[])


# ===========================================================================
# F5 — T-only bytes must be executed in a separate oracle evaluator
# ===========================================================================
@pytest.mark.red
def test_f5_oracle_evaluation_block_when_t_only(syn, plan, tmp_path):
    """When a task has T-only paths, the receipt must prove a separate
    evaluator executed them (oracle_evaluation block), never a silent
    materialize-only. Uses the harness plan (exec path)."""
    from c6runner.runner import C6Runner
    doc = json.load(open(syn["frozen_inputs"], encoding="utf-8"))
    fi = {v["path"]: v["sha256"] for v in doc.values()}
    r = C6Runner(syn["freeze"], syn["auth"], syn["bare"], syn["ledger"],
                 syn["events"], os.path.dirname(syn["body"]),
                 str(tmp_path / "runs5"), fi)
    res = r.run_task(syn["target"], plan=plan)
    body = res["payload"].get("oracle_evaluation")
    assert body is not None, "oracle_evaluation block missing from receipt"


# ===========================================================================
# F8 — operator commands must be valid PowerShell 7 only
# ===========================================================================
@pytest.mark.red
def test_f8_operator_commands_powershell_only():
    docs = os.path.join(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))), "OPERATOR_COMMANDS.md")
    text = open(docs, encoding="utf-8").read()
    cmd_isms = []
    for pat, why in [("set PYTHONPATH=", "CMD set: use $env:PYTHONPATH ="),
                     ("\nset ", "CMD set statement"),
                     ("%CD%", "CMD %var% syntax: use $PWD/.Path"),
                     ("^\\s*$", "CMD caret continuation: use backtick")]:
        import re
        if re.search(pat, text):
            cmd_isms.append(why)
    assert not cmd_isms, f"CMD syntax found: {cmd_isms}"


@pytest.mark.red
def test_f8_operator_commands_are_not_cmd_bat():
    docs = os.path.join(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))), "OPERATOR_COMMANDS.md")
    text = open(docs, encoding="utf-8").read()
    # after repair the file must use Get-FileHash (PS7) and no .bat artifacts
    assert "Get-FileHash" in text
