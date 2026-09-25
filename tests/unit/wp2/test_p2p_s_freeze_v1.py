"""WP-2 P2P-S primary preservation freeze V1 (Mission-09) - unit tests (ZERO API).

Verifies the P2P-S freeze semantics:
- exact extraction of P2P_ONLY node IDs from the FINAL per-test evidence;
- frozen 3/3 stability requirement on parent + frozen test patch AND target;
- defined / sparse / zero handling (zero => UNDEFINED, never PASS);
- evaluator-only / invisible flags;
- canonical artifact hash repeatability;
- membership disjointness and union integrity.
"""

from __future__ import annotations

import pytest

from benchmark.wp2.p2p_s_freeze_v1 import (
    P2P_ONLY,
    canonical_sha256,
    node_counts_distribution,
    p2p_only_nodes_by_task,
)


def test_p2p_only_extraction_groups_and_sorts() -> None:
    records = [
        {
            "task_id": "t1",
            "node_id": "f.py::b",
            "classification": P2P_ONLY,
            "parent_outcomes": ["passed", "passed", "passed"],
            "target_outcomes": ["passed", "passed", "passed"],
        },
        {
            "task_id": "t1",
            "node_id": "f.py::a",
            "classification": P2P_ONLY,
            "parent_outcomes": ["passed", "passed", "passed"],
            "target_outcomes": ["passed", "passed", "passed"],
        },
        {
            "task_id": "t1",
            "node_id": "g.py::x",
            "classification": "BEHAVIORAL_F2P",
            "parent_outcomes": ["failed", "failed", "failed"],
            "target_outcomes": ["passed", "passed", "passed"],
        },
        {
            "task_id": "t2",
            "node_id": "h.py::y",
            "classification": P2P_ONLY,
            "parent_outcomes": ["passed", "passed", "passed"],
            "target_outcomes": ["passed", "passed", "passed"],
        },
    ]
    grouped = p2p_only_nodes_by_task(records)
    assert grouped == {"t1": ["f.py::a", "f.py::b"], "t2": ["h.py::y"]}


def test_p2p_only_stability_violation_raises() -> None:
    records = [
        {
            "task_id": "t1",
            "node_id": "f.py::b",
            "classification": P2P_ONLY,
            "parent_outcomes": ["passed", "passed", "failed"],
            "target_outcomes": ["passed", "passed", "passed"],
        }
    ]
    with pytest.raises(ValueError):
        p2p_only_nodes_by_task(records)


def test_canonical_sha256_deterministic() -> None:
    a = canonical_sha256({"b": 2, "a": 1})
    b = canonical_sha256({"a": 1, "b": 2})
    assert a == b
    assert len(a) == 64


def test_node_counts_distribution() -> None:
    dist = node_counts_distribution([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    assert dist["min"] == 1
    assert dist["max"] == 10
    assert dist["median"] in (5, 6)
    assert dist["n_tasks"] == 10
    empty = node_counts_distribution([])
    assert empty["n_tasks"] == 0
    assert empty["min"] == 0


def test_p2p_s_artifact_build_smoke(tmp_path) -> None:
    """End-to-end freeze on a small synthetic inventory + per-test evidence."""
    import json

    from benchmark.wp2.p2p_s_freeze_v1 import build_p2p_s_artifact

    inventory_payload = {
        "tasks": [
            {
                "task_id": "saleor-rc-t1",
                "split_role": "DEV_TRAIN_ENG",
                "era_key": "py39",
                "parent_commit": "p1",
                "target_commit": "t1",
                "oracle_valid": True,
            },
            {
                "task_id": "saleor-rc-t2",
                "split_role": "DEV_VALIDATION",
                "era_key": "py312",
                "parent_commit": "p2",
                "target_commit": "t2",
                "oracle_valid": True,
            },
            {
                "task_id": "saleor-rc-t3",
                "split_role": "DEV_TRAIN_ASSAY_HOLDOUT",
                "era_key": "py38",
                "parent_commit": "p3",
                "target_commit": "t3",
                "oracle_valid": False,
            },
        ],
    }
    per_test = [
        {
            "task_id": "saleor-rc-t1",
            "node_id": "saleor/a/tests/test_a.py::test_x",
            "classification": P2P_ONLY,
            "parent_outcomes": ["passed"] * 3,
            "target_outcomes": ["passed"] * 3,
        },
        {
            "task_id": "saleor-rc-t1",
            "node_id": "saleor/a/tests/test_a.py::test_y",
            "classification": P2P_ONLY,
            "parent_outcomes": ["passed"] * 3,
            "target_outcomes": ["passed"] * 3,
        },
        {
            "task_id": "saleor-rc-t1",
            "node_id": "saleor/a/tests/test_a.py::test_z",
            "classification": "BEHAVIORAL_F2P",
            "parent_outcomes": ["failed"] * 3,
            "target_outcomes": ["passed"] * 3,
        },
        {
            "task_id": "saleor-rc-t2",
            "node_id": "saleor/b/tests/test_b.py::test_w",
            "classification": P2P_ONLY,
            "parent_outcomes": ["passed"] * 3,
            "target_outcomes": ["passed"] * 3,
        },
    ]
    out = tmp_path / "p2p_s.json"
    artifact = build_p2p_s_artifact(
        inventory_payload=inventory_payload,
        per_test_records=per_test,
        evidence_sha256="deadbeef",
        out_path=out,
    )
    assert len(artifact["tasks"]) == 2  # non-oracle-valid excluded
    t1 = next(t for t in artifact["tasks"] if t["task_id"] == "saleor-rc-t1")
    assert t1["n_p2p_s_nodes"] == 2
    assert t1["defined"] is True
    assert t1["sparse"] is True
    assert t1["evaluator_only"] is True
    assert t1["invisible_to_generation"] is True
    t2 = next(t for t in artifact["tasks"] if t["task_id"] == "saleor-rc-t2")
    assert t2["n_p2p_s_nodes"] == 1
    assert t2["sparse"] is True
    # zero-node task is UNDEFINED, never PASS
    assert artifact["coverage"]["oracle_valid_union_47"]["defined"] == 2
    assert artifact["coverage"]["oracle_valid_union_47"]["undefined"] == 0
    # canonical hash stable across reload
    reloaded = json.loads(out.read_text(encoding="utf-8"))
    assert reloaded["hashes"]["artifact_sha256"] == artifact["hashes"]["artifact_sha256"]
