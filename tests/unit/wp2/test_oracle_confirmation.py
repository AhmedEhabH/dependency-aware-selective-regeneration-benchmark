"""WP-2 Oracle Confirmation - unit tests (ZERO API, no git, no network).

Tests the pure semantics: test-file path classification, JUnit parsing,
3-run stability classification, failure taxonomy, task eligibility flags,
selection strata/order determinism, no-selector-outcome usage, no-sealed-path
access, fingerprint determinism, and attrition reconciliation.
"""

from __future__ import annotations

import json

import pytest

from benchmark.wp2.environment_manager import (
    fingerprint_commit_from_files,
    fingerprint_family,
)
from benchmark.wp2.oracle_confirmation import (
    FLAKY,
    OTHER_REVIEW_REQUIRED,
    SYMBOL_ABSENCE_F2P,
    TARGET_ORACLE_INVALID,
    build_selection_order,
    classify_failure_reason,
    derive_test_only_patch_bytes,
    is_test_path,
    parse_junit,
    reconcile_attrition,
    select_strong_tasks,
    task_eligibility,
    three_run_stability,
)


# ---------------------------------------------------------------------------
# test-file path classification
# ---------------------------------------------------------------------------
def test_is_test_path_rules() -> None:
    assert is_test_path("saleor/product/tests/test_tasks.py")
    assert is_test_path("saleor/tests/fixtures.py")
    assert is_test_path("saleor/graphql/order/tests/test_fulfillment.py")
    assert is_test_path("saleor/graphql/order/tests/test_fulfillment_refund_products.py")
    assert not is_test_path("saleor/product/search.py")
    assert not is_test_path("saleor/core/languages.py")


# ---------------------------------------------------------------------------
# JUnit parsing
# ---------------------------------------------------------------------------
def test_parse_junit_nodes() -> None:
    xml = """<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" tests="3" errors="0" failures="1" skipped="0">
  <testcase classname="test_demo" name="test_passes" file="saleor/x/tests/test_demo.py" line="3"/>
  <testcase classname="test_demo" name="test_fails" file="saleor/x/tests/test_demo.py" line="9">
    <failure message="assert 1 == 2">assert 1 == 2</failure>
  </testcase>
  <testcase classname="test_demo" name="test_errors" file="saleor/x/tests/test_demo.py" line="12">
    <error message="ImportError: No module named 'new_component'">Traceback...</error>
  </testcase>
</testsuite>"""
    nodes = parse_junit(xml)
    assert len(nodes) == 3
    assert nodes["saleor/x/tests/test_demo.py::test_passes"] == "passed"
    assert nodes["saleor/x/tests/test_demo.py::test_fails"] == "failed"
    assert nodes["saleor/x/tests/test_demo.py::test_errors"] == "error"


def test_parse_junit_skipped() -> None:
    xml = (
        '<testsuite name="pytest" tests="1">'
        '<testcase classname="c" name="t" file="f.py"><skipped/></testcase>'
        "</testsuite>"
    )
    nodes = parse_junit(xml)
    assert nodes["f.py::t"] == "skipped"


# ---------------------------------------------------------------------------
# 3-run stability
# ---------------------------------------------------------------------------
def test_three_run_stability_stable_pass() -> None:
    assert three_run_stability(["passed", "passed", "passed"]) == "STABLE_PASS"


def test_three_run_stability_stable_fail() -> None:
    assert three_run_stability(["failed", "failed", "failed"]) == "STABLE_FAIL"


def test_three_run_stability_flaky() -> None:
    assert three_run_stability(["passed", "failed", "passed"]) == FLAKY
    assert three_run_stability(["failed", "passed", "failed"]) == FLAKY
    assert three_run_stability(["passed", "passed", "failed"]) == FLAKY


# ---------------------------------------------------------------------------
# failure taxonomy
# ---------------------------------------------------------------------------
def test_classify_failure_reason_behavioral() -> None:
    assert (
        classify_failure_reason(
            target_outcomes=["passed", "passed", "passed"],
            parent_outcomes=["failed", "failed", "failed"],
            parent_failure_text="assert 1 == 2\nE       assert 1 == 2",
        )
        == "BEHAVIORAL_F2P"
    )


def test_classify_failure_reason_symbol_absence() -> None:
    assert (
        classify_failure_reason(
            target_outcomes=["passed", "passed", "passed"],
            parent_outcomes=["error", "error", "error"],
            parent_failure_text="ImportError: cannot import name 'new_component'",
        )
        == SYMBOL_ABSENCE_F2P
    )


def test_classify_failure_reason_p2p_only() -> None:
    assert (
        classify_failure_reason(
            target_outcomes=["passed", "passed", "passed"],
            parent_outcomes=["passed", "passed", "passed"],
            parent_failure_text="",
        )
        == "P2P_ONLY"
    )


def test_classify_failure_reason_flaky() -> None:
    assert (
        classify_failure_reason(
            target_outcomes=["passed", "failed", "passed"],
            parent_outcomes=["failed", "failed", "failed"],
            parent_failure_text="assert 1 == 2",
        )
        == FLAKY
    )


def test_classify_failure_reason_target_invalid() -> None:
    assert (
        classify_failure_reason(
            target_outcomes=["failed", "failed", "failed"],
            parent_outcomes=["failed", "failed", "failed"],
            parent_failure_text="assert 1 == 2",
        )
        == TARGET_ORACLE_INVALID
    )


def test_classify_failure_reason_other() -> None:
    assert (
        classify_failure_reason(
            target_outcomes=["passed", "passed", "passed"],
            parent_outcomes=["failed", "failed", "failed"],
            parent_failure_text="unexpected: Segmentation fault during teardown",
        )
        == OTHER_REVIEW_REQUIRED
    )


# ---------------------------------------------------------------------------
# task eligibility
# ---------------------------------------------------------------------------
def test_task_eligibility_primary_behavioral() -> None:
    flags = task_eligibility(
        n_behavioral_f2p=2,
        n_symbol_absence_f2p=0,
        n_p2p=1,
        target_oracle_stable=True,
        environment_valid=True,
    )
    assert flags["PRIMARY_BEHAVIORAL_F2P_ELIGIBLE"] is True
    assert flags["EXTENDED_F2P_ELIGIBLE"] is True


def test_task_eligibility_extended_only() -> None:
    flags = task_eligibility(
        n_behavioral_f2p=0,
        n_symbol_absence_f2p=3,
        n_p2p=0,
        target_oracle_stable=True,
        environment_valid=True,
    )
    assert flags["PRIMARY_BEHAVIORAL_F2P_ELIGIBLE"] is False
    assert flags["EXTENDED_F2P_ELIGIBLE"] is True


def test_task_eligibility_requires_env_valid() -> None:
    flags = task_eligibility(
        n_behavioral_f2p=2,
        n_symbol_absence_f2p=0,
        n_p2p=0,
        target_oracle_stable=True,
        environment_valid=False,
    )
    assert flags["PRIMARY_BEHAVIORAL_F2P_ELIGIBLE"] is False
    assert flags["EXTENDED_F2P_ELIGIBLE"] is False


# ---------------------------------------------------------------------------
# test-only patch derivation (pure diff filter; no git in unit tests)
# ---------------------------------------------------------------------------
def test_derive_test_only_patch_excludes_production() -> None:
    full_diff = (
        "diff --git a/saleor/product/search.py b/saleor/product/search.py\n"
        "@@ -1 +1 @@\n-OLD\n+NEW\n"
        "diff --git a/saleor/product/tests/test_tasks.py b/saleor/product/tests/test_tasks.py\n"
        "@@ -1 +1 @@\n-OLD\n+NEW\n"
    )
    test_paths = ["saleor/product/tests/test_tasks.py"]
    patch = derive_test_only_patch_bytes(full_diff, test_paths)
    assert "search.py" not in patch
    assert "test_tasks.py" in patch


def test_derive_test_only_patch_requires_nonempty() -> None:
    with pytest.raises(ValueError):
        derive_test_only_patch_bytes("", ["saleor/product/tests/test_tasks.py"])


# ---------------------------------------------------------------------------
# selection strata / order determinism
# ---------------------------------------------------------------------------
def test_select_strong_tasks_all_20() -> None:
    candidates = [
        {"task_id": f"saleor-rc-{i:012x}", "f2p_candidacy": "STRONG_F2P_CANDIDATE"}
        for i in range(20)
    ]
    candidates += [
        {"task_id": f"saleor-rc-m{i:012x}", "f2p_candidacy": "MODIFIED_TEST_CANDIDATE"}
        for i in range(5)
    ]
    strong = select_strong_tasks(candidates)
    assert len(strong) == 20
    assert all(c["f2p_candidacy"] == "STRONG_F2P_CANDIDATE" for c in strong)


def test_build_selection_order_deterministic() -> None:
    tasks = [
        {
            "task_id": f"saleor-rc-{i:012x}",
            "f2p_candidacy": "MODIFIED_TEST_CANDIDATE",
            "env_family": "fam1" if i % 2 == 0 else "fam2",
            "migration_or_config_heavy": i % 3 == 0,
            "changed_source_bin": "SMALL" if i % 2 == 0 else "LARGE",
            "n_modified_test_files_bin": "1" if i % 2 == 0 else ">1",
        }
        for i in range(40)
    ]
    order1 = build_selection_order(tasks)
    order2 = build_selection_order(tasks)
    assert [t["task_id"] for t in order1] == [t["task_id"] for t in order2]
    assert len(order1) == 40


# ---------------------------------------------------------------------------
# environment fingerprint determinism
# ---------------------------------------------------------------------------
def test_fingerprint_commit_from_files_deterministic() -> None:
    files = {
        "pyproject.toml": b'[project]\nrequires-python = ">=3.12,<3.13"\n',
        "setup.cfg": b"[tool:pytest]\ntestpaths = saleor\n",
    }
    fp1 = fingerprint_commit_from_files(files)
    fp2 = fingerprint_commit_from_files(files)
    assert fp1 == fp2
    assert ">=3.12,<3.13" in fp1.python_requirement
    fam1 = fingerprint_family(fp1)
    fam2 = fingerprint_family(fp2)
    assert fam1 == fam2


# ---------------------------------------------------------------------------
# no sealed path access (786 guard)
# ---------------------------------------------------------------------------
def test_no_sealed_path_access_guard() -> None:
    # The oracle confirmation selection must never enumerate the 786 sealed
    # outcomes. Assert our selection helpers raise on any path that looks like
    # a sealed outcome source.
    from benchmark.wp2.oracle_confirmation import is_sealed_outcome_source

    assert is_sealed_outcome_source("research/saleor-reserve-300-rmcss/saleor_reserve_300_sample.json")
    assert is_sealed_outcome_source("research/transparency/saleor_candidate_metadata.json")
    assert not is_sealed_outcome_source("benchmark_data/real_commit_impact_saleor/scientific/x/case_manifest.json")


# ---------------------------------------------------------------------------
# attrition reconciliation
# ---------------------------------------------------------------------------
def test_reconcile_attrition() -> None:
    per_task = [
        {"task_id": "a", "classification": "BEHAVIORAL_F2P"},
        {"task_id": "b", "classification": "P2P_ONLY"},
        {"task_id": "c", "classification": "FLAKY"},
    ]
    result = reconcile_attrition(per_task)
    assert result["BEHAVIORAL_F2P"] == 1
    assert result["P2P_ONLY"] == 1
    assert result["FLAKY"] == 1
    assert result["total"] == 3
    # every row present -> reconcile
    assert result["unaccounted"] == 0


def test_reconcile_attrition_no_silent_drop() -> None:
    per_task = [
        {"task_id": "a", "classification": "BEHAVIORAL_F2P"},
        {"task_id": "b", "classification": "ENV_BROKEN"},
        {"task_id": "c", "classification": "TEST_PATCH_APPLY_FAIL"},
        {"task_id": "d", "classification": "OTHER_REVIEW_REQUIRED"},
    ]
    result = reconcile_attrition(per_task)
    assert result["ENV_BROKEN"] == 1
    assert result["TEST_PATCH_APPLY_FAIL"] == 1
    assert result["OTHER_REVIEW_REQUIRED"] == 1
    assert result["total"] == 4
    assert result["unaccounted"] == 0


# ---------------------------------------------------------------------------
# selection JSON contract: no selector-outcome fields
# ---------------------------------------------------------------------------
def test_selection_manifest_no_selector_outcomes() -> None:
    # The selection manifest schema must never carry RM-CSS/Agent F1 or success.
    manifest = json.loads(
        (
            __import__("pathlib").Path(__file__).resolve().parents[3]
            / "research"
            / "wp2"
            / "wp2_oracle_confirmation_selection_2026-09-22.json"
        ).read_text(encoding="utf-8")
    )
    forbidden = ("f1", "success", "tp", "fp", "fn", "recall", "precision")
    assert not any(
        any(k in forbidden for k in item)
        for item in manifest.get("selection", {}).get("tasks", [])
    )
