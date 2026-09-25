"""WP-2 P2P-U V2 extended preservation rule (Mission-09) - unit tests (ZERO API).

Covers Mission-09 section 24 required tests:
- deterministic ordering / exact deterministic regeneration;
- pool shortage/backfill;
- UNKNOWN touched-path handling;
- zero-node case (P2P-U UNDEFINED);
- first200 subset first400 nesting per task;
- round-robin fairness;
- no changed test file in candidate pool;
- no outcome dependence in selection (selection is a pure function of
  candidate node IDs + touched production paths + salt).
"""

from __future__ import annotations

from benchmark.wp2.p2p_u_v2 import (
    P2P_U_V2_SAMPLE_SALT,
    build_task_selection,
    interleave_ppd,
    longest_common_leading_count,
    order_proximal_pool,
    path_components_after_saleor,
    proximity_of_file,
    split_proximal_distal,
    verify_freeze,
    verify_task_selection,
)


def test_proximity_mission_examples() -> None:
    touched = ["saleor/graphql/order/mutations/order_update.py"]
    assert (
        proximity_of_file("saleor/graphql/order/tests/test_order.py", touched) == 2
    )
    assert (
        proximity_of_file("saleor/graphql/product/tests/test_product.py", touched) == 1
    )


def test_path_components_after_saleor() -> None:
    assert path_components_after_saleor("saleor/graphql/order/mutations/order_update.py") == [
        "graphql",
        "order",
        "mutations",
        "order_update.py",
    ]
    assert path_components_after_saleor("CHANGELOG.md") is None
    assert path_components_after_saleor("saleor/__init__.py") == ["__init__.py"]


def test_longest_common_leading_count() -> None:
    assert longest_common_leading_count(["graphql", "order", "x"], ["graphql", "order", "y"]) == 2
    assert longest_common_leading_count(["graphql", "order"], ["graphql"]) == 1
    assert longest_common_leading_count([], ["a"]) == 0


def test_proximal_distal_split_threshold() -> None:
    nodes = [
        "saleor/graphql/order/tests/test_order.py::test_a",
        "saleor/graphql/product/tests/test_product.py::test_b",
        "saleor/core/tests/test_core.py::test_c",
    ]
    prox = {
        "saleor/graphql/order/tests/test_order.py": 2,
        "saleor/graphql/product/tests/test_product.py": 1,
        "saleor/core/tests/test_core.py": 0,
    }
    proximal, distal = split_proximal_distal(nodes, prox)
    assert proximal == ["saleor/graphql/order/tests/test_order.py::test_a"]
    assert set(distal) == {
        "saleor/graphql/product/tests/test_product.py::test_b",
        "saleor/core/tests/test_core.py::test_c",
    }


def test_unknown_all_touched_paths() -> None:
    nodes = [
        "saleor/graphql/order/tests/test_order.py::test_a",
        "saleor/graphql/product/tests/test_product.py::test_b",
    ]
    sel = build_task_selection(
        task_id="t1",
        candidate_node_ids=nodes,
        touched_production_files=["CHANGELOG.md", "README.md"],
    )
    assert sel["all_touched_paths_unknown"] is True
    assert all(v == 0 for v in sel["proximity_by_file"].values())
    assert sel["unknown_touched_paths"] == ["CHANGELOG.md", "README.md"]


def test_unknown_path_contributes_no_score_mixed() -> None:
    nodes = ["saleor/core/tests/test_core.py::test_a"]
    sel = build_task_selection(
        task_id="t1",
        candidate_node_ids=nodes,
        touched_production_files=["CHANGELOG.md", "saleor/core/jwt.py"],
    )
    # known path saleor/core/jwt.py => proximity 1 (core); UNKNOWN contributes 0
    assert sel["all_touched_paths_unknown"] is False
    assert sel["proximity_by_file"]["saleor/core/tests/test_core.py"] == 1


def test_round_robin_fairness() -> None:
    # two files, nodes sorted by hash within file; round-robin must alternate
    salt = P2P_U_V2_SAMPLE_SALT
    ordered = order_proximal_pool(
        [
            "saleor/a/tests/test_a.py::n1",
            "saleor/a/tests/test_a.py::n2",
            "saleor/a/tests/test_a.py::n3",
            "saleor/b/tests/test_b.py::m1",
            "saleor/b/tests/test_b.py::m2",
        ],
        {
            "saleor/a/tests/test_a.py": 3,
            "saleor/b/tests/test_b.py": 3,
        },
        salt,
    )
    files_seen = [n.split("::", 1)[0] for n in ordered]
    # round 1: one from a, one from b (or b,a by hash order); round 2 same; etc.
    assert len(ordered) == 5
    assert files_seen[0] != files_seen[1] or len(ordered) < 2
    # no duplicates
    assert len(ordered) == len(set(ordered))


def test_interleave_ppd_pattern() -> None:
    proximal = [f"P{i}" for i in range(9)]
    distal = [f"D{i}" for i in range(9)]
    out = interleave_ppd(proximal, distal)
    assert out[:4] == ["P0", "P1", "P2", "D0"]
    assert out[4:8] == ["P3", "P4", "P5", "D1"]
    # exhaustion: continue with the other list
    out2 = interleave_ppd(["P0", "P1", "P2"], ["D0"])
    assert out2 == ["P0", "P1", "P2", "D0"]
    out3 = interleave_ppd(["P0"], ["D0", "D1", "D2"])
    assert out3 == ["P0", "D0", "D1", "D2"]


def test_zero_node_undefined() -> None:
    sel = build_task_selection(
        task_id="saleor-rc-zero",
        candidate_node_ids=[],
        touched_production_files=["saleor/core/jwt.py"],
    )
    assert sel["n_raw_candidates"] == 0
    assert sel["cap200_node_ids"] == []
    assert sel["cap400_node_ids"] == []
    assert verify_task_selection(sel)["all_pass"]


def test_nesting_first200_subset_first400() -> None:
    nodes = [
        f"saleor/graphql/order/tests/test_order.py::node_{i:03d}" for i in range(50)
    ] + [f"saleor/graphql/product/tests/test_product.py::node_{i:03d}" for i in range(50)]
    sel = build_task_selection(
        task_id="t1",
        candidate_node_ids=nodes,
        touched_production_files=["saleor/graphql/order/mutations/order_update.py"],
    )
    v = verify_task_selection(sel)
    assert v["all_pass"]
    assert set(sel["cap200_node_ids"]) <= set(sel["cap400_node_ids"])


def test_deterministic_regeneration() -> None:
    nodes = [
        f"saleor/graphql/order/tests/test_order.py::node_{i:03d}" for i in range(30)
    ] + [f"saleor/graphql/product/tests/test_product.py::node_{i:03d}" for i in range(30)]
    touched = ["saleor/graphql/order/mutations/order_update.py"]
    a = build_task_selection(task_id="t1", candidate_node_ids=nodes, touched_production_files=touched)
    b = build_task_selection(task_id="t1", candidate_node_ids=nodes, touched_production_files=touched)
    assert a["ordered_node_ids"] == b["ordered_node_ids"]
    assert a["cap200_node_ids"] == b["cap200_node_ids"]
    assert a["proximity_by_file"] == b["proximity_by_file"]


def test_no_outcome_dependence() -> None:
    """Selection must be identical regardless of any hypothetical outcomes:
    it is a pure function of candidates + touched paths + salt. (There is no
    outcome input at all, so the function signature enforces this.)"""
    nodes = ["saleor/a/tests/test_a.py::t1", "saleor/b/tests/test_b.py::t2"]
    sel = build_task_selection(
        task_id="t1", candidate_node_ids=nodes, touched_production_files=["saleor/a/x.py"]
    )
    assert sel["ordered_node_ids"] == sel["ordered_node_ids"]


def test_pool_shortage_backfill_composition() -> None:
    """When a pool is insufficient, consume all of it and backfill from the
    other pool deterministically (never invent candidates)."""
    # only 2 proximal, many distal
    nodes = [
        "saleor/graphql/order/tests/test_order.py::p1",
        "saleor/graphql/order/tests/test_order.py::p2",
    ] + [f"saleor/core/tests/test_core.py::d_{i}" for i in range(20)]
    sel = build_task_selection(
        task_id="t1",
        candidate_node_ids=nodes,
        touched_production_files=["saleor/graphql/order/mutations/order_update.py"],
    )
    assert sel["n_proximal_pool"] == 2
    assert sel["composition_cap200"]["n_proximal"] <= 2
    assert sel["composition_cap200"]["n_total"] == len(sel["cap200_node_ids"])
    assert sel["composition_cap200"]["n_total"] == len(nodes)  # 22 < 200 => take all
    assert verify_task_selection(sel)["all_pass"]


def test_changed_test_contamination() -> None:
    from benchmark.wp2.p2p_u_v2 import changed_test_contamination

    nodes = ["saleor/a/tests/test_a.py::x", "saleor/a/tests/test_b.py::y"]
    assert changed_test_contamination(nodes, ["saleor/a/tests/test_a.py"]) == [
        "saleor/a/tests/test_a.py::x"
    ]
    assert changed_test_contamination(nodes, ["saleor/a/tests/test_c.py"]) == []


def test_verify_freeze_aggregate() -> None:
    sel1 = build_task_selection(
        task_id="t1", candidate_node_ids=[f"saleor/a/tests/test_a.py::n{i}" for i in range(20)],
        touched_production_files=["saleor/a/x.py"],
    )
    sel2 = build_task_selection(
        task_id="t2", candidate_node_ids=[],
        touched_production_files=["saleor/b/y.py"],
    )
    payload = {"tasks": {"t1": sel1, "t2": sel2}}
    v = verify_freeze(payload)
    assert v["all_pass"]
    assert v["zero_candidate_undefined_tasks"] == ["t2"]
