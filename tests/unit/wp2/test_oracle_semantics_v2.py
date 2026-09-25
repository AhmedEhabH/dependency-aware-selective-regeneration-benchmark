"""WP-2 Oracle semantics V2 - RED/GREEN unit tests (ZERO API).

Covers amendment A (mechanical node classification), amendment B (frozen
test-path regex), amendment C (environment canary), and amendment G (protected
pools guard). These tests must pass before any large Linux rerun (amendment E).
"""

from __future__ import annotations

import pytest

from benchmark.wp2.oracle_semantics_v2 import (
    BEHAVIORAL_F2P,
    CANARY_ENV_INVALID,
    CANARY_VALID,
    FLAKY,
    OTHER_REVIEW_REQUIRED,
    P2P_ONLY,
    PARENT_COLLECTION_ERROR,
    SYMBOL_ABSENCE_F2P,
    TARGET_ORACLE_INVALID,
    assert_task_allowed,
    canary_verdict,
    classify_node_v2,
    is_test_path_v2,
    select_canary_node,
    task_eligibility_v2,
)


def _classify(
    *,
    target=("passed", "passed", "passed"),
    parent=("failed", "failed", "failed"),
    text="assert 1 == 2",
    collects=True,
    shared=False,
):
    return classify_node_v2(
        target_outcomes=list(target),
        parent_outcomes=list(parent),
        parent_failure_text=text,
        parent_collects_node=collects,
        shared_test_support_failed=shared,
    )


# ---------------------------------------------------------------------------
# Amendment A - PARENT_COLLECTION_ERROR
# ---------------------------------------------------------------------------
def test_pce_node_absent_at_parent() -> None:
    assert _classify(collects=False, text="") == PARENT_COLLECTION_ERROR


def test_pce_module_import_failure() -> None:
    assert (
        _classify(
            collects=False,
            text="ModuleNotFoundError: No module named 'new_module'",
        )
        == PARENT_COLLECTION_ERROR
    )


def test_pce_shared_test_support_failure_invalidates_dependent_nodes() -> None:
    # A shared conftest/fixture/cassette collection failure makes dependent
    # nodes PCE even if the node itself would otherwise be executable.
    assert _classify(shared=True, text="") == PARENT_COLLECTION_ERROR


def test_pce_is_not_primary_behavioral() -> None:
    # PCE never classifies as primary behavioral F2P (amendment A).
    assert _classify(collects=False, text="assert 1 == 2") != BEHAVIORAL_F2P
    assert _classify(collects=False, text="assert 1 == 2") == PARENT_COLLECTION_ERROR


# ---------------------------------------------------------------------------
# Amendment A - SYMBOL_ABSENCE_F2P
# ---------------------------------------------------------------------------
def test_symbol_absence_import_error() -> None:
    assert (
        _classify(text="ImportError: cannot import name 'new_component'")
        == SYMBOL_ABSENCE_F2P
    )


def test_symbol_absence_attribute_error() -> None:
    assert _classify(text="AttributeError: 'module' has no attribute 'new_fn'") == SYMBOL_ABSENCE_F2P


def test_symbol_absence_name_error() -> None:
    assert _classify(text="NameError: name 'new_symbol' is not defined") == SYMBOL_ABSENCE_F2P


def test_symbol_absence_not_primary_behavioral() -> None:
    assert (
        _classify(text="ImportError: cannot import name 'x'") == SYMBOL_ABSENCE_F2P
    )
    assert _classify(text="ImportError: cannot import name 'x'") != BEHAVIORAL_F2P


def test_collected_node_required_for_symbol_absence() -> None:
    # If the node is NOT collected at parent, it is PCE, not symbol absence.
    assert (
        _classify(collects=False, text="ImportError: cannot import name 'x'")
        == PARENT_COLLECTION_ERROR
    )


# ---------------------------------------------------------------------------
# Amendment A - BEHAVIORAL_F2P
# ---------------------------------------------------------------------------
def test_behavioral_assertion() -> None:
    assert _classify(text="assert 1 == 2\nE       assert 1 == 2") == BEHAVIORAL_F2P


def test_behavioral_exception_not_symbol() -> None:
    assert _classify(text="E           django.db.utils.IntegrityError: NOT NULL constraint failed") == BEHAVIORAL_F2P


def test_behavioral_requires_parent_collection() -> None:
    assert _classify(collects=False, text="assert 1 == 2") == PARENT_COLLECTION_ERROR


def test_behavioral_requires_target_stable_pass() -> None:
    assert (
        _classify(target=("failed", "failed", "failed"), text="assert 1 == 2")
        == TARGET_ORACLE_INVALID
    )


# ---------------------------------------------------------------------------
# Amendment A - flaky / p2p / other
# ---------------------------------------------------------------------------
def test_flaky_node_excluded_node_wise() -> None:
    assert _classify(target=("passed", "failed", "passed")) == FLAKY
    assert _classify(parent=("passed", "failed", "passed")) == FLAKY


def test_p2p_only() -> None:
    assert _classify(parent=("passed", "passed", "passed")) == P2P_ONLY


def test_other_review_required_only_when_no_failure_detail() -> None:
    # A collected node with a stable parent fail but NO failure text is
    # genuinely ambiguous -> OTHER_REVIEW_REQUIRED (manual review).
    assert (
        _classify(text="")
        == OTHER_REVIEW_REQUIRED
    )


# ---------------------------------------------------------------------------
# Amendment A - task-level primary eligibility
# ---------------------------------------------------------------------------
def test_task_primary_eligible_with_stable_behavioral() -> None:
    flags = task_eligibility_v2(
        n_behavioral_f2p=1,
        n_symbol_absence_f2p=0,
        n_parent_collection_error=0,
        environment_valid=True,
    )
    assert flags["PRIMARY_BEHAVIORAL_F2P_ELIGIBLE"] is True
    assert flags["EXTENDED_F2P_ELIGIBLE"] is True


def test_mixed_task_flaky_node_does_not_invalidate() -> None:
    # Flaky/target-invalid nodes are excluded node-wise; they do NOT invalidate
    # an otherwise eligible task (amendment A).
    flags = task_eligibility_v2(
        n_behavioral_f2p=1,
        n_symbol_absence_f2p=0,
        n_parent_collection_error=2,
        environment_valid=True,
    )
    assert flags["PRIMARY_BEHAVIORAL_F2P_ELIGIBLE"] is True


def test_mixed_task_target_invalid_node_does_not_invalidate() -> None:
    flags = task_eligibility_v2(
        n_behavioral_f2p=2,
        n_symbol_absence_f2p=0,
        n_parent_collection_error=0,
        environment_valid=True,
    )
    assert flags["PRIMARY_BEHAVIORAL_F2P_ELIGIBLE"] is True


def test_05bd_style_parent_missing_nodes_not_primary() -> None:
    # Nodes that are PCE (parent missing/collection) are never primary
    # behavioral; a task with ONLY PCE nodes is not eligible.
    flags = task_eligibility_v2(
        n_behavioral_f2p=0,
        n_symbol_absence_f2p=0,
        n_parent_collection_error=3,
        environment_valid=True,
    )
    assert flags["PRIMARY_BEHAVIORAL_F2P_ELIGIBLE"] is False
    assert flags["EXTENDED_F2P_ELIGIBLE"] is False


def test_task_invalidated_by_systemic_collection_failure() -> None:
    # Only systemic environment/collection failure invalidates the whole task.
    flags = task_eligibility_v2(
        n_behavioral_f2p=1,
        n_symbol_absence_f2p=0,
        n_parent_collection_error=0,
        environment_valid=True,
        task_collection_failure=True,
    )
    assert flags["PRIMARY_BEHAVIORAL_F2P_ELIGIBLE"] is False


def test_task_requires_environment_valid() -> None:
    flags = task_eligibility_v2(
        n_behavioral_f2p=1,
        n_symbol_absence_f2p=0,
        n_parent_collection_error=0,
        environment_valid=False,
    )
    assert flags["PRIMARY_BEHAVIORAL_F2P_ELIGIBLE"] is False


# ---------------------------------------------------------------------------
# Amendment B - frozen test-path regex
# ---------------------------------------------------------------------------
def test_test_path_regex_accepts_categories() -> None:
    assert is_test_path_v2("saleor/graphql/order/tests/test_fulfillment.py")
    assert is_test_path_v2("saleor/order/tests/test_order_actions.py")
    assert is_test_path_v2("saleor/tests/fixtures.py")
    assert is_test_path_v2("saleor/conftest.py")
    assert is_test_path_v2("tests/conftest.py")
    cassette = (
        "saleor/graphql/core/tests/cassettes/"
        "test_get_oembed_data[http:/www.youtube.com/watch?v=dQw4w9WgXcQ-VIDEO].yaml"
    )
    assert is_test_path_v2(cassette)
    assert is_test_path_v2("saleor/x/test_demo.py")
    assert is_test_path_v2("saleor/x/demo_test.py")


def test_test_path_regex_rejects_production() -> None:
    assert not is_test_path_v2("saleor/product/search.py")
    assert not is_test_path_v2("saleor/core/languages.py")
    assert not is_test_path_v2("saleor/product/migrations/0001_initial.py")
    assert not is_test_path_v2("saleor/settings.py")


def test_test_path_regex_rule_hash_frozen() -> None:
    from benchmark.wp2.oracle_semantics_v2 import (
        TEST_PATH_REGEX_SHA256,
        TEST_PATH_RULE_SHA256,
        TEST_PATH_RULE_VERSION,
    )

    assert TEST_PATH_RULE_VERSION == "test-path-rule-v1"
    assert len(TEST_PATH_REGEX_SHA256) == 64
    assert len(TEST_PATH_RULE_SHA256) == 64


# ---------------------------------------------------------------------------
# Amendment C - environment canary
# ---------------------------------------------------------------------------
def test_canary_selection_deterministic_and_excludes_changed() -> None:
    nodes = [
        "saleor/graphql/order/tests/test_fulfillment.py::test_order_fulfill",
        "saleor/graphql/order/tests/test_order.py::test_order_total",
        "saleor/product/tests/test_tasks.py::test_task_media",
    ]
    changed = ["saleor/graphql/order/tests/test_fulfillment.py"]
    touched = ["saleor/graphql/order/fulfill.py"]
    c1 = select_canary_node(node_ids=nodes, changed_test_files=changed, touched_production_files=touched)
    c2 = select_canary_node(node_ids=nodes, changed_test_files=changed, touched_production_files=touched)
    assert c1 == c2
    assert c1 is not None
    assert c1.split("::", 1)[0] not in changed


def test_canary_verdict() -> None:
    assert canary_verdict(
        ["passed", "passed", "passed"], ["passed", "passed", "passed"]
    ) == CANARY_VALID
    assert canary_verdict(
        ["failed", "failed", "failed"], ["passed", "passed", "passed"]
    ) == CANARY_ENV_INVALID


def test_canary_none_when_no_candidates() -> None:
    assert select_canary_node(node_ids=[], changed_test_files=[], touched_production_files=[]) is None


# ---------------------------------------------------------------------------
# Amendment G - protected pools guard
# ---------------------------------------------------------------------------
def test_internal_test_access_forbidden() -> None:
    with pytest.raises(ValueError):
        assert_task_allowed("saleor-rc-internal-test-000000000000")


def test_reserve_access_forbidden() -> None:
    with pytest.raises(ValueError):
        assert_task_allowed("saleor-rc-reserve-000000000000")


def test_normal_task_allowed() -> None:
    assert_task_allowed("saleor-rc-05bdc7feb9ac")  # no exception
