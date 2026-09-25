"""WP-2 DEV unchanged-test P2P inventory V1 (Mission-08) - unit tests (ZERO API).

Verifies the DEV inventory applies the IDENTICAL frozen P2P Preservation Rule
V1 (unchanged test file in same top-level Saleor app as touched production
files; frozen V1 sample salt; CAP=400 applied POST-STABILITY only), keeps split
membership, forbids outcome inspection during construction, and produces
reproducible hashes. Covers addendum Q2 (6-class P2P taxonomy), Q7 (no pre-cap),
Q8 (frozen salt), Q1 (test-support flag).
"""

from __future__ import annotations

import pytest

from benchmark.wp2.p2p_inventory_dev_v1 import (
    P2P_CAP,
    P2P_CLASS_BOTH_FAIL,
    P2P_CLASS_COLLECTION_ERROR,
    P2P_CLASS_FLAKY,
    P2P_CLASS_PARENT_BROKEN,
    P2P_CLASS_STABLE,
    P2P_CLASS_TARGET_BROKEN,
    P2P_SAMPLE_SALT_FROZEN,
    build_task_record,
    classify_p2p_node,
    dev_inventory_sha256,
    exclusion_reason,
    membership_sha256,
    record_p2p_outcomes,
    summarize_side_three_runs,
)
from benchmark.wp2.p2p_inventory_v1 import P2P_SAMPLE_SALT


def test_frozen_salt_reused(q8: None = None) -> None:
    assert P2P_SAMPLE_SALT_FROZEN == P2P_SAMPLE_SALT == "wp2-p2p-unchanged-sample-v1-2026-09-23"


def test_summarize_side_three_runs() -> None:
    assert summarize_side_three_runs(["passed"] * 3) == "STABLE_PASS"
    assert summarize_side_three_runs(["failed"] * 3) == "STABLE_FAIL"
    assert summarize_side_three_runs(["error"] * 3) == "STABLE_COLLECTION_ERROR"
    assert summarize_side_three_runs(["missing"] * 3) == "STABLE_COLLECTION_ERROR"
    assert summarize_side_three_runs(["passed", "failed", "passed"]) == "FLAKY"
    assert summarize_side_three_runs(["failed", "error", "failed"]) == "FLAKY"
    with pytest.raises(ValueError):
        summarize_side_three_runs(["passed"] * 2)


def test_classify_p2p_node_precedence() -> None:
    p3, t3 = ["passed"] * 3, ["passed"] * 3
    assert classify_p2p_node(p3, t3) == P2P_CLASS_STABLE
    assert classify_p2p_node(p3, ["failed"] * 3) == P2P_CLASS_TARGET_BROKEN
    assert classify_p2p_node(["failed"] * 3, t3) == P2P_CLASS_PARENT_BROKEN
    assert classify_p2p_node(["failed"] * 3, ["failed"] * 3) == P2P_CLASS_BOTH_FAIL
    # flaky has top precedence
    assert classify_p2p_node(["passed", "failed", "passed"], t3) == P2P_CLASS_FLAKY
    assert classify_p2p_node(p3, ["passed", "error", "passed"]) == P2P_CLASS_FLAKY
    # collection error next
    assert classify_p2p_node(["error"] * 3, t3) == P2P_CLASS_COLLECTION_ERROR
    assert classify_p2p_node(p3, ["missing"] * 3) == P2P_CLASS_COLLECTION_ERROR
    # flaky beats collection error
    assert classify_p2p_node(["error", "error", "passed"], ["error"] * 3) == P2P_CLASS_FLAKY


def test_record_p2p_outcomes_caps_stable_only(q7: None = None) -> None:
    nodes = [f"saleor/a/tests/test_x.py::test_{i}" for i in range(500)]
    classes = {n: P2P_CLASS_STABLE for n in nodes}
    classes["saleor/a/tests/test_x.py::test_broken"] = P2P_CLASS_TARGET_BROKEN
    rec = {
        "n_stable_p2p_nodes_before_cap": None,
        "n_stable_p2p_nodes_after_cap": None,
        "capped_stable": None,
        "preservation_nodes": [],
    }
    record_p2p_outcomes(rec, classes)
    assert rec["n_stable_p2p_nodes_before_cap"] == 500
    assert rec["n_stable_p2p_nodes_after_cap"] == P2P_CAP
    assert rec["capped_stable"] is True
    # only STABLE_P2P nodes are eligible; broken node never in preservation set
    assert "saleor/a/tests/test_x.py::test_broken" not in rec["preservation_nodes"]


def test_record_p2p_outcomes_below_cap() -> None:
    nodes = [f"saleor/a/tests/test_x.py::test_{i}" for i in range(10)]
    classes = {n: P2P_CLASS_STABLE for n in nodes}
    classes["saleor/a/tests/test_x.py::test_flaky"] = P2P_CLASS_FLAKY
    rec = {"n_stable_p2p_nodes_before_cap": None, "n_stable_p2p_nodes_after_cap": None,
           "capped_stable": None, "preservation_nodes": []}
    record_p2p_outcomes(rec, classes)
    assert rec["n_stable_p2p_nodes_before_cap"] == 10
    assert rec["n_stable_p2p_nodes_after_cap"] == 10
    assert rec["capped_stable"] is False


def test_build_task_record_non_oracle_valid_no_outcome_use() -> None:
    rec = build_task_record(
        task_id="saleor-rc-abc",
        split_role="DEV_TRAIN_ASSAY_HOLDOUT",
        parent_commit="p",
        target_commit="t",
        era_key="py39",
        python_requirement="~3.9",
        oracle_valid=False,
        no_changed_test_evidence=True,
        env_failed=False,
        touched_production_files=["saleor/product/models.py"],
        associated_unchanged_test_files=["saleor/product/tests/test_models.py"],
        candidate_nodes=None,
        changed_test_support_present=False,
    )
    assert rec["exclusion_reason"] == "NO_CHANGED_TEST_EVIDENCE"
    assert rec["node_discovery_status"] == "NOT_APPLICABLE"
    assert rec["n_discovered_candidate_nodes"] is None


def test_build_task_record_no_precap(q7: None = None) -> None:
    nodes = [f"saleor/graphql/tests/test_g.py::test_{i}" for i in range(1200)]
    rec = build_task_record(
        task_id="saleor-rc-xyz",
        split_role="DEV_TRAIN_ENG",
        parent_commit="p",
        target_commit="t",
        era_key="py312",
        python_requirement=">=3.12,<3.13",
        oracle_valid=True,
        no_changed_test_evidence=False,
        env_failed=False,
        touched_production_files=["saleor/graphql/schema.py"],
        associated_unchanged_test_files=["saleor/graphql/tests/test_g.py"],
        candidate_nodes=nodes,
        changed_test_support_present=True,
    )
    assert rec["oracle_valid"] is True
    # Q7: discovered set is NOT capped; cap only post-stability.
    assert rec["n_discovered_candidate_nodes"] == 1200
    assert len(rec["candidate_node_ids"]) == 1200
    assert rec["n_stable_p2p_nodes_before_cap"] is None
    assert rec["changed_test_support_present"] is True


def test_exclusion_reason_deterministic() -> None:
    assert exclusion_reason(oracle_valid=True, no_changed_test_evidence=False, env_failed=False) is None
    assert (
        exclusion_reason(oracle_valid=False, no_changed_test_evidence=False, env_failed=True)
        == "ENV_INSTALL_FAILED_C4"
    )
    assert (
        exclusion_reason(oracle_valid=False, no_changed_test_evidence=False, env_failed=False)
        == "NOT_ORACLE_VALID"
    )


def test_hashes_reproducible() -> None:
    payload = {"a": [1, 2], "b": {"c": "x"}}
    assert dev_inventory_sha256(payload) == dev_inventory_sha256(payload)
    ids = ["saleor-rc-b", "saleor-rc-a"]
    assert membership_sha256(ids) == membership_sha256(list(reversed(ids)))
    assert len(dev_inventory_sha256(payload)) == 64
    assert len(membership_sha256(ids)) == 64
