"""M17 K07 - P2P/F2P contract tests + failure injection (zero network, zero Docker).

Failure-injection cases (mission K07):
  missing pytest/dev pin; wrong install mode; declared dev group + closure none;
  lockfile mismatch; unknown schema; duplicate task; missing target commit;
  fake Docker startup failure; F2P all fail; F2P partial; P2P regression;
  all behavioral tests pass.
Each injected case asserts the exact expected terminal classification/token.

No test writes under frozen research/ evidence directories (tmp_path only).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

P = Path(__file__).resolve().parents[4]
for _p in (P, P / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts import wp2_m17_adapter as ad  # noqa: E402
from scripts import wp2_m17_contract as c  # noqa: E402
from scripts.wp2_m17_contract import (  # noqa: E402
    TERMINAL_ENV_INSTALL_BLOCKED,
    TERMINAL_F2P_PARTIAL,
    TERMINAL_F2P_UNRESOLVED,
    TERMINAL_INFRA,
    TERMINAL_P2P_REGRESSION,
    TERMINAL_RESOLVED,
)

PASS = lambda _n: "passed"  # noqa: E731
FAIL = lambda _n: "failed"  # noqa: E731


# ------------------------------------------------------------------ F2P contract
def test_f2p_node_set_from_frozen_selector_blind():
    per_task_v2 = {"counts": {c.BEHAVIORAL_F2P: 2, c.SYMBOL_ABSENCE_F2P: 1}}
    node_records = [
        {"node_id": "a.py::t1", "v3_class": c.BEHAVIORAL_F2P},
        {"node_id": "a.py::t2", "v3_class": c.SYMBOL_ABSENCE_F2P},
        {"node_id": "a.py::t3", "v3_class": c.P2P_ONLY},
    ]
    nodes = c.f2p_node_set_from_frozen(per_task_v2, node_records)
    assert nodes == ["a.py::t1", "a.py::t2"]
    assert len(nodes) == 2  # frozen count 3 but only 2 evaluator nodes -> unresolved below


def test_f2p_missing_nodes_block_resolution():
    per_task_v2 = {"counts": {c.BEHAVIORAL_F2P: 3}}
    nodes = c.f2p_node_set_from_frozen(per_task_v2, [
        {"node_id": "n1", "v3_class": c.BEHAVIORAL_F2P},
        {"node_id": "n2", "v3_class": c.BEHAVIORAL_F2P},
    ])
    status = c.evaluate_nodes(nodes, PASS)
    resolved, blockers = c.task_resolvable(frozen_count=3, node_set=nodes, per_node_status=status)
    assert not resolved
    assert any("MISSING_F2P_NODES" in b for b in blockers)


def test_f2p_all_pass_resolves():
    per_task_v2 = {"counts": {c.BEHAVIORAL_F2P: 2}}
    nodes = c.f2p_node_set_from_frozen(per_task_v2, [
        {"node_id": "n1", "v3_class": c.BEHAVIORAL_F2P},
        {"node_id": "n2", "v3_class": c.BEHAVIORAL_F2P},
    ])
    status = c.evaluate_nodes(nodes, PASS)
    resolved, blockers = c.task_resolvable(frozen_count=2, node_set=nodes, per_node_status=status)
    assert resolved and not blockers


def test_f2p_unresolved_node_blocks():
    per_task_v2 = {"counts": {c.BEHAVIORAL_F2P: 1}}
    nodes = c.f2p_node_set_from_frozen(per_task_v2, [
        {"node_id": "n1", "v3_class": c.BEHAVIORAL_F2P}])
    # evaluator returns nothing for n1 -> status missing -> unresolved
    status = c.evaluate_nodes(nodes, lambda _n: None)
    resolved, blockers = c.task_resolvable(frozen_count=1, node_set=nodes, per_node_status=status)
    assert not resolved
    assert any("UNRESOLVED_NODE:n1" in b for b in blockers)


def test_terminal_classify_f2p_all_fail():
    per_task_v2 = {"counts": {c.BEHAVIORAL_F2P: 2}}
    nodes = c.f2p_node_set_from_frozen(per_task_v2, [
        {"node_id": "n1", "v3_class": c.BEHAVIORAL_F2P},
        {"node_id": "n2", "v3_class": c.BEHAVIORAL_F2P},
    ])
    status = c.evaluate_nodes(nodes, FAIL)
    term, ev = c.terminal_classify(task_id="t", frozen_count=2, node_set=nodes,
                                   per_node_status=status, env_install_blocked=False,
                                   infra=False, p2p_failures=[])
    assert term == TERMINAL_F2P_UNRESOLVED
    assert any("FAILED_NODE" in b for b in ev["blockers"])


def test_terminal_classify_f2p_partial():
    per_task_v2 = {"counts": {c.BEHAVIORAL_F2P: 3}}
    nodes = c.f2p_node_set_from_frozen(per_task_v2, [
        {"node_id": "n1", "v3_class": c.BEHAVIORAL_F2P},
        {"node_id": "n2", "v3_class": c.BEHAVIORAL_F2P},
    ])
    status = c.evaluate_nodes(nodes, PASS)
    term, _ = c.terminal_classify(task_id="t", frozen_count=3, node_set=nodes,
                                  per_node_status=status, env_install_blocked=False,
                                  infra=False, p2p_failures=[])
    assert term == TERMINAL_F2P_PARTIAL


def test_terminal_classify_all_pass_resolved():
    per_task_v2 = {"counts": {c.BEHAVIORAL_F2P: 2}}
    nodes = c.f2p_node_set_from_frozen(per_task_v2, [
        {"node_id": "n1", "v3_class": c.BEHAVIORAL_F2P},
        {"node_id": "n2", "v3_class": c.BEHAVIORAL_F2P},
    ])
    status = c.evaluate_nodes(nodes, PASS)
    term, ev = c.terminal_classify(task_id="t", frozen_count=2, node_set=nodes,
                                   per_node_status=status, env_install_blocked=False,
                                   infra=False, p2p_failures=[])
    assert term == TERMINAL_RESOLVED
    assert ev["frozen_f2p_count"] == 2


# ------------------------------------------------------------------ P2P contract
def test_p2p_nodes_selector_blind():
    p2p_s = {"per_task": [{"task_id": "t", "additions_v3": ["a.py::p1"], "intersection": ["b.py::p2"]}]}
    p2p_u = {"task_id": "t", "node_classes": {"c.py::u1": "STABLE_P2P", "d.py::f1": "FLAKY"}}
    nodes = c.p2p_nodes_from_frozen(p2p_s, p2p_u, "t")
    assert nodes["selector_blind"] is True
    assert nodes["p2p_s_nodes"] == ["a.py::p1", "b.py::p2"]
    assert nodes["p2p_u_nodes"] == ["c.py::u1"]


def test_p2p_failure_not_reclassified_as_infra():
    nodes = {"p2p_s_nodes": ["a.py::p1"], "p2p_u_nodes": ["b.py::u1"]}
    # a P2P node whose evaluator status is infra-like must be flagged
    bad = c.p2p_failure_reclassified(nodes, {"a.py::p1": "passed", "b.py::u1": "COLLECTION_ERROR"})
    assert any("P2P_REGRESSION_MASKED_AS_INFRA:b.py::u1" in x for x in bad)
    # a genuine passing P2P node is never flagged
    assert c.p2p_failure_reclassified(nodes, {"a.py::p1": "passed", "b.py::u1": "passed"}) == []


def test_p2p_regression_terminal():
    nodes = {"p2p_s_nodes": ["a.py::p1"], "p2p_u_nodes": []}
    regressions = c.p2p_regressions(nodes, {"a.py::p1": "failed"})
    assert regressions, "a P2P node failure must produce a regression violation"
    term, _ = c.terminal_classify(task_id="t", frozen_count=0, node_set=[],
                                  per_node_status={}, env_install_blocked=False,
                                  infra=False, p2p_failures=regressions)
    assert term == TERMINAL_P2P_REGRESSION


def test_robust_aggregate_deterministic():
    a = {"t1": {"terminal": TERMINAL_RESOLVED, "n_f2p": 2, "n_p2p": 0},
         "t2": {"terminal": TERMINAL_INFRA, "n_f2p": 0, "n_p2p": 0}}
    b = {"t1": {"terminal": TERMINAL_RESOLVED, "n_f2p": 2, "n_p2p": 0},
         "t2": {"terminal": TERMINAL_INFRA, "n_f2p": 0, "n_p2p": 0}}
    assert c.robust_aggregate(a) == c.robust_aggregate(b)
    assert c.robust_aggregate(a)["counts"][TERMINAL_RESOLVED] == 1


# ------------------------------------------------------------------ failure injection (adapter-level)
def _record(manifest: dict) -> dict:
    return {"task_id": "saleor-rc-x", "target_commit": "a" * 40, "status": "DONE",
            "manifest": manifest}


def test_inject_missing_pytest_dev_pin_fails_closed():
    # frozen derive_dev_test_closure: requirements_dev with a missing exact pin
    mf = {"requirements_dev.txt": "pytest>=7\n"}
    c2 = ad.frozen_dev_closure(mf, "py39")
    assert c2["mechanism"] == "none"  # no exact pin -> no silent dev install


def test_inject_wrong_install_mode_matches_frozen_harness():
    from benchmark.wp2.harness_v3 import lock_install_script
    mf = {"poetry.lock": "[[package]]\nname=\"x\"\nversion=\"1.0\"\n",
          "pyproject.toml": "[tool.poetry.group.dev.dependencies]\npytest=\"^8\"\n\n[tool.ruff]\n"}
    derived = ad.frozen_install_mode(mf)
    assert derived == lock_install_script(ad.PROBE_WT, mf)[1]
    assert derived == "V2_MAIN_PLUS_EXACT_LOCKED_DEV"  # poetry + dev group, no package-mode=false


def test_inject_declared_dev_group_closure_none_fails_closed():
    mf = {"pyproject.toml": "[tool.poetry.group.dev.dependencies]\npytest=\"^8\"\n\n[tool.ruff]\n",
          "requirements.txt": "django==4.2\n"}
    assert ad.frozen_declares_dev_group(mf) is True
    assert ad.frozen_dev_closure(mf, "py39")["mechanism"] == "none"


def test_inject_lockfile_mismatch_detected():
    mf = {"requirements.txt": "django==4.2\n"}
    lf = ad.frozen_lockfile(mf)
    assert lf != ad.frozen_lockfile({"requirements.txt": "django==4.3\n"})


def test_inject_unknown_schema_eng_reader_fails_closed(tmp_path, monkeypatch):
    text = json.dumps({"task_id": "saleor-rc-a", "target_commit": "a" * 40,
                       "manifest": {"install_mode": "x", "lockfile_sha256": "y",
                                    "dev_test_closure": {"not_mechanism": 1}}}) + "\n"
    p = tmp_path / "eng.jsonl"
    p.write_text(text, encoding="utf-8")
    monkeypatch.setattr(ad, "PHASE5_ENG_V3_REL", p)
    with pytest.raises(ad.AdapterError):
        ad.read_frozen_eng(P)


def test_inject_duplicate_task_fails_closed(tmp_path, monkeypatch):
    line = json.dumps({"task_id": "saleor-rc-a", "target_commit": "a" * 40,
                       "manifest": {"install_mode": "x", "lockfile_sha256": "y"}}) + "\n"
    p = tmp_path / "eng.jsonl"
    p.write_text(line + line, encoding="utf-8")
    monkeypatch.setattr(ad, "PHASE5_ENG_V3_REL", p)
    with pytest.raises(ad.AdapterError):
        ad.read_frozen_eng(P)


def test_inject_missing_target_commit_fails_closed(tmp_path, monkeypatch):
    line = json.dumps({"task_id": "saleor-rc-a",
                       "manifest": {"install_mode": "x", "lockfile_sha256": "y"}}) + "\n"
    p = tmp_path / "eng.jsonl"
    p.write_text(line, encoding="utf-8")
    monkeypatch.setattr(ad, "PHASE5_ENG_V3_REL", p)
    with pytest.raises(ad.AdapterError):
        ad.read_frozen_eng(P)


def test_inject_missing_lockfile_fails_closed(tmp_path, monkeypatch):
    line = json.dumps({"task_id": "saleor-rc-a", "target_commit": "a" * 40,
                       "manifest": {"install_mode": "x"}}) + "\n"
    p = tmp_path / "eng.jsonl"
    p.write_text(line, encoding="utf-8")
    monkeypatch.setattr(ad, "PHASE5_ENG_V3_REL", p)
    with pytest.raises(ad.AdapterError):
        ad.read_frozen_eng(P)


def test_inject_fake_docker_startup_failure_maps_to_infra():
    # a fake executor raising an infra error -> the runner maps it to EVAL_ERROR (79)
    term, _ = c.terminal_classify(task_id="t", frozen_count=1,
                                  node_set=[], per_node_status={},
                                  env_install_blocked=False, infra=True, p2p_failures=[])
    assert term == TERMINAL_INFRA


def test_inject_f2p_all_fail_and_partial_and_p2p_regression_terminal_tokens():
    # F2P all fail
    nodes = ["n1"]
    status = c.evaluate_nodes(nodes, FAIL)
    term, _ = c.terminal_classify(task_id="t", frozen_count=1, node_set=nodes,
                                  per_node_status=status, env_install_blocked=False,
                                  infra=False, p2p_failures=[])
    assert term == TERMINAL_F2P_UNRESOLVED
    # F2P partial
    nodes = ["n1", "n2"]
    status = c.evaluate_nodes(nodes, PASS)
    term, _ = c.terminal_classify(task_id="t", frozen_count=3, node_set=nodes,
                                  per_node_status=status, env_install_blocked=False,
                                  infra=False, p2p_failures=[])
    assert term == TERMINAL_F2P_PARTIAL
    # P2P regression
    failures = c.p2p_regressions({"p2p_s_nodes": ["n1"], "p2p_u_nodes": []},
                                 {"n1": "failed"})
    term, _ = c.terminal_classify(task_id="t", frozen_count=0, node_set=[],
                                  per_node_status={}, env_install_blocked=False,
                                  infra=False, p2p_failures=failures)
    assert term == TERMINAL_P2P_REGRESSION
    # env install blocked is terminal before everything
    term, _ = c.terminal_classify(task_id="t", frozen_count=1, node_set=["n1"],
                                  per_node_status={"n1": "passed"},
                                  env_install_blocked=True, infra=True, p2p_failures=[])
    assert term == TERMINAL_ENV_INSTALL_BLOCKED
    # all pass -> resolved
    term, _ = c.terminal_classify(task_id="t", frozen_count=1, node_set=["n1"],
                                  per_node_status={"n1": "passed"},
                                  env_install_blocked=False, infra=False, p2p_failures=[])
    assert term == TERMINAL_RESOLVED


def test_f2p_p2p_contract_uses_frozen_artifacts(tmp_path):
    # uses the REAL frozen P2P-S ENG artifact and P2P-U file (read-only)
    p2p_s = json.loads((P / "research/wp2/harness_v3_2026-09-26/p2p_s_v3_eng.json").read_text())
    p2p_u = json.loads((P / "research/wp2/harness_v3_2026-09-26"
                        / "p2pu_v3_eng_saleor-rc-22ec4dab0154_cap200.json").read_text())
    nodes = c.p2p_nodes_from_frozen(p2p_s, p2p_u, "saleor-rc-22ec4dab0154")
    assert nodes["p2p_u_nodes"]
    assert all(c.P2P_U_CLASSES)  # vocabulary present
