"""WP-2 unchanged-test P2P inventory V1 - unit tests (ZERO API).

Verifies amendment J: association rule (unchanged test file in same top-level
Saleor app as touched production files), stable 3/3 on BOTH parent and target,
and the deterministic 400-cap.
"""

from __future__ import annotations

from benchmark.wp2.p2p_inventory_v1 import (
    P2P_CAP,
    associate_unchanged_test_files,
    build_task_inventory,
    cap_nodes,
    stable_p2p_nodes,
)


def test_associate_unchanged_same_app_only() -> None:
    touched = ["saleor/product/models.py"]
    all_tests = [
        "saleor/product/tests/test_models.py",  # same app, unchanged
        "saleor/graphql/order/tests/test_order.py",  # different app
        "saleor/product/tests/test_changed.py",  # changed -> excluded
    ]
    diff = {"saleor/product/tests/test_changed.py"}
    out = associate_unchanged_test_files(
        touched_production_files=touched,
        all_test_files=all_tests,
        target_diff_paths=diff,
    )
    assert out == ["saleor/product/tests/test_models.py"]


def test_stable_p2p_nodes_both_states() -> None:
    outcomes = {
        "a.py::t1": {"parent": ["passed"] * 3, "target": ["passed"] * 3},
        "b.py::t2": {"parent": ["failed"] * 3, "target": ["passed"] * 3},
        "c.py::t3": {"parent": ["passed", "failed", "passed"], "target": ["passed"] * 3},
    }
    assert stable_p2p_nodes(outcomes) == ["a.py::t1"]


def test_cap_nodes_below_cap() -> None:
    nodes = [f"x.py::t{i}" for i in range(10)]
    assert cap_nodes(nodes) == sorted(nodes)


def test_cap_nodes_above_cap_deterministic() -> None:
    nodes = [f"x.py::t{i}" for i in range(500)]
    a = cap_nodes(nodes)
    b = cap_nodes(nodes)
    assert len(a) == P2P_CAP == 400
    assert a == b


def test_build_task_inventory_markers() -> None:
    outcomes = {
        "saleor/product/tests/test_models.py::test_ok": {
            "parent": ["passed"] * 3,
            "target": ["passed"] * 3,
        }
    }
    inv = build_task_inventory(
        task_id="saleor-rc-abc",
        touched_production_files=["saleor/product/models.py"],
        all_test_files=["saleor/product/tests/test_models.py"],
        target_diff_paths=set(),
        node_outcomes=outcomes,
    )
    assert inv["evaluator_only"] is True
    assert inv["invisible_to_generation"] is True
    assert inv["preservation_validation_complete"] is False
    assert inv["n_candidate_nodes"] == 1
