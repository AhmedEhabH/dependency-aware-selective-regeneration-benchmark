"""M17 K06/K07 - deterministic fake qualification executor (zero Docker, zero WSL, zero API).

Replaces the real V3 oracle/readiness Docker boundary so the real controller and
the qualification command chain can be exercised in a fake world. The fake world
is driven by an optional JSON spec:
    {"default_status": "DONE", "per_task": {"<task_id>": {"status": ...,
     "classification": ..., "counts": {...}}}}
Read from the path in env ``M17_FAKE_WORLD`` (or generated deterministically
from the task id when absent).

The ``classification``/``counts`` mirror the frozen V3 oracle semantics schema
(BEHAVIORAL_F2P / NOT_PRIMARY terminal classes) so contract tests can assert
that the runner records per-node status and strict/robust semantics without
inventing a new taxonomy.
"""
from __future__ import annotations

import hashlib
import json
import os

DEFAULT_WORLD = {"default_status": "DONE", "per_task": {}}


class FakeInfraError(OSError):
    """Simulated infrastructure interruption (maps to EVAL_ERROR / resume)."""


def _load_world() -> dict:
    path = os.environ.get("M17_FAKE_WORLD")
    if not path or not os.path.exists(path):
        return DEFAULT_WORLD
    return json.loads(open(path, encoding="utf-8").read())


def _node_statuses(task_id: str) -> dict:
    """Deterministic fake per-node statuses keyed by node id."""
    w = _load_world()
    per = w.get("per_task", {}).get(task_id, {})
    n_f2p = per.get("n_behavioral_f2p", 1)
    nodes = {}
    for i in range(n_f2p):
        node = f"saleor/tests/test_{task_id.split('-')[-1][:6]}.py::test_f2p_{i}"
        nodes[node] = "BEHAVIORAL_F2P"
    if per.get("n_p2p", 0):
        for i in range(per["n_p2p"]):
            node = f"saleor/tests/test_{task_id.split('-')[-1][:6]}.py::test_p2p_{i}"
            nodes[node] = "STABLE_P2P"
    return nodes


class FakeExecutor:
    """Deterministic fake qualification executor for tests / fake world."""

    def run_task(self, task_id: str, spec: dict) -> dict:
        w = _load_world()
        per = w.get("per_task", {}).get(task_id, {})
        if w.get("infra_raise") or os.environ.get("M17_FAKE_INFRA_ONCE"):
            # deterministic one-shot infra interruption (resumable, EVAL_ERROR)
            raise FakeInfraError("M17_SIM_INFRA: simulated infrastructure interruption")
        status = per.get("status", w.get("default_status", "DONE"))
        classification = per.get("classification", "BEHAVIORAL_F2P" if status == "DONE" else "NOT_PRIMARY")
        nodes = _node_statuses(task_id)
        n_f2p = sum(1 for v in nodes.values() if v == "BEHAVIORAL_F2P")
        rec = {
            "status": status,
            "classification": classification,
            "n_nodes": len(nodes),
            "counts": {
                "BEHAVIORAL_F2P": n_f2p,
                "SYMBOL_ABSENCE_F2P": per.get("n_symbol_absence_f2p", 0),
                "PARENT_COLLECTION_ERROR": per.get("n_parent_collection_error", 0),
                "P2P_ONLY": 0,
                "FLAKY": per.get("n_flaky", 0),
                "TARGET_ORACLE_INVALID": 0,
                "OTHER_REVIEW_REQUIRED": 0,
            },
            "node_records": [
                {
                    "node_id": n,
                    "v3_class": c,
                    "target_outcomes": ["passed", "passed", "passed"],
                    "parent_outcomes": ["failed", "failed", "failed"],
                }
                for n, c in sorted(nodes.items())
            ],
            "f2p_nodes": sorted(n for n, c in nodes.items() if c == "BEHAVIORAL_F2P"),
            "p2p_nodes": sorted(n for n, c in nodes.items() if c == "STABLE_P2P"),
            "wall_s": 1.0,
            "executor": "tests.unit.wp2.m17.sim.fake_executor.FakeExecutor",
        }
        return rec


def fake_hash(task_id: str) -> str:
    return hashlib.sha256(f"m17-fake|{task_id}".encode()).hexdigest()
