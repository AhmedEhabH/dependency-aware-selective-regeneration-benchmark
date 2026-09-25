"""WP-2 P2P-S primary preservation freeze V1 (Mission-09) - ZERO API.

P2P-S is the SWE-bench-aligned changed-test PASS_TO_PASS preservation set,
strengthened relative to ordinary single-run evaluation by requiring stable
3/3 pass on BOTH (a) parent + frozen test patch AND (b) target.

Frozen definition (Mission-09 section 5, using the EXISTING frozen C2/C4
P2P_ONLY classification from the FINAL Mission-07/C4 per-test evidence):

- node is in changed/test-patch test scope (C2/C4 P2P_ONLY classification);
- parent + frozen test patch = stable PASS 3/3;
- target = stable PASS 3/3.

The extraction is a pure deterministic function of the FINAL per-test evidence
JSONL and the frozen DEV inventory task metadata (split / era). No new oracle
construction execution happens in Mission-09 (section 5: "No new P2P-S oracle
construction execution").

Semantics:
- defined   = n_p2p_s_nodes > 0
- sparse    = 0 < n_p2p_s_nodes < 10
- A task with zero P2P-S nodes is UNDEFINED for P2P-S, never automatic PASS.
- evaluator_only = true; invisible_to_generation = true.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from benchmark.wp2.p2p_inventory_dev_v1 import (
    membership_sha256,
)

P2P_S_VERSION = "wp2-p2p-s-v1-2026-09-25"
EVIDENCE_IDENTITY = "mission-07-c4-per-test-dev-v2-2026-09-23"
EVIDENCE_SOURCE = "research/wp2/oracle_confirmation_linux_v2_2026-09-23/per_test_dev_v2.jsonl"
P2P_ONLY = "P2P_ONLY"


def canonical_sha256(payload: dict) -> str:
    """Canonical SHA-256 over a JSON payload (sorted keys)."""
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def load_per_test_records(path: Path) -> list[dict]:
    """Load the FINAL per-test evidence JSONL records."""
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def p2p_only_nodes_by_task(records: list[dict]) -> dict[str, list[str]]:
    """Node IDs classified P2P_ONLY, grouped by task.

    Verifies the frozen stability requirement mechanically: every P2P_ONLY
    record must have parent = ['passed']*3 and target = ['passed']*3.
    """
    result: dict[str, list[str]] = {}
    for rec in records:
        if rec.get("classification") != P2P_ONLY:
            continue
        parent = rec.get("parent_outcomes") or []
        target = rec.get("target_outcomes") or []
        if parent != ["passed", "passed", "passed"] or target != ["passed", "passed", "passed"]:
            raise ValueError(f"P2P_ONLY record violates 3/3 stability: {rec.get('node_id')}")
        result.setdefault(rec["task_id"], []).append(rec["node_id"])
    for task_id in result:
        result[task_id] = sorted(set(result[task_id]))
    return result


def node_counts_distribution(counts: list[int]) -> dict:
    """Deterministic quantiles (nearest-rank) over non-empty counts."""
    counts = sorted(counts)

    def pct(p: float) -> int:
        if not counts:
            return 0
        idx = int(p / 100.0 * (len(counts) - 1))
        return counts[idx]

    return {
        "min": pct(0),
        "p25": pct(25),
        "median": pct(50),
        "p75": pct(75),
        "max": pct(100),
        "n_tasks": len(counts),
    }


def build_p2p_s_artifact(
    *,
    inventory_payload: dict,
    per_test_records: list[dict],
    evidence_sha256: str,
    out_path: Path,
) -> dict:
    """Assemble the frozen P2P-S artifact (Mission-09 section 5).

    ``inventory_payload`` is the frozen DEV unchanged-test inventory (used for
    split_role / era_key / task metadata only). ``per_test_records`` is the
    FINAL per-test evidence JSONL. Returns the artifact payload and writes it
    to ``out_path``.
    """
    oracle_valid = [t for t in inventory_payload["tasks"] if t.get("oracle_valid")]
    p2p_by_task = p2p_only_nodes_by_task(per_test_records)

    tasks: list[dict] = []
    for row in sorted(oracle_valid, key=lambda r: r["task_id"]):
        task_id = row["task_id"]
        node_ids = p2p_by_task.get(task_id, [])
        n = len(node_ids)
        tasks.append(
            {
                "task_id": task_id,
                "split": row["split_role"],
                "era": row["era_key"],
                "parent_commit": row["parent_commit"],
                "target_commit": row["target_commit"],
                "p2p_s_node_ids": node_ids,
                "n_p2p_s_nodes": n,
                "defined": n > 0,
                "sparse": 0 < n < 10,
                "evaluator_only": True,
                "invisible_to_generation": True,
                "source_evidence_identity": EVIDENCE_IDENTITY,
                "source_evidence_sha256": evidence_sha256,
            }
        )

    membership: dict[str, list[str]] = {
        "DEV_TRAIN_ENG": sorted(r["task_id"] for r in tasks if r["split"] == "DEV_TRAIN_ENG"),
        "DEV_TRAIN_ASSAY_HOLDOUT": sorted(r["task_id"] for r in tasks if r["split"] == "DEV_TRAIN_ASSAY_HOLDOUT"),
        "DEV_VALIDATION": sorted(r["task_id"] for r in tasks if r["split"] == "DEV_VALIDATION"),
    }
    split_counts: dict[str, dict] = {}
    for split_name, ids in membership.items():
        members = [t for t in tasks if t["task_id"] in ids]
        defined = [t for t in members if t["defined"]]
        split_counts[split_name] = {
            "tasks": len(ids),
            "n_p2p_s_nodes": sum(t["n_p2p_s_nodes"] for t in members),
            "defined": len(defined),
            "undefined": len(members) - len(defined),
            "sparse": sum(1 for t in members if t["sparse"]),
        }
    split_counts["oracle_valid_union_47"] = {
        "tasks": len(tasks),
        "n_p2p_s_nodes": sum(t["n_p2p_s_nodes"] for t in tasks),
        "defined": sum(1 for t in tasks if t["defined"]),
        "undefined": sum(1 for t in tasks if not t["defined"]),
        "sparse": sum(1 for t in tasks if t["sparse"]),
    }

    zero_tasks = [t["task_id"] for t in tasks if t["n_p2p_s_nodes"] == 0]
    sparse_tasks = [t["task_id"] for t in tasks if t["sparse"]]

    payload = {
        "artifact": "wp2_dev_p2p_s_v1",
        "artifact_version": P2P_S_VERSION,
        "date": "2026-09-25",
        "scope": "oracle-valid DEV union (47 tasks)",
        "definition": (
            "SWE-bench-aligned changed-test PASS_TO_PASS preservation, "
            "strengthened with 3/3 stability on both parent+frozen-test-patch "
            "and target states (frozen Mission-07/C4 P2P_ONLY classification). "
            "Not claimed byte-for-byte identical to the SWE-bench implementation."
        ),
        "node_definition": (
            "node in changed/test-patch test scope; parent + frozen test patch = "
            "stable PASS 3/3; target = stable PASS 3/3"
        ),
        "source_evidence": {
            "identity": EVIDENCE_IDENTITY,
            "path": EVIDENCE_SOURCE,
            "sha256": evidence_sha256,
        },
        "task_metric": {
            "denominator": "tasks where P2P-S is DEFINED (n_p2p_s_nodes > 0)",
            "pass_rule": "generated-patch task PASS = ALL frozen P2P-S nodes pass",
            "zero_node": "UNDEFINED and excluded from metric denominator; never automatic PASS",
            "node_level": "secondary/descriptive only",
        },
        "evaluator_only": True,
        "invisible_to_generation": True,
        "tasks": tasks,
        "membership": membership,
        "coverage": split_counts,
        "distribution": {
            "zero_node_tasks": zero_tasks,
            "sparse_tasks_lt_10": sparse_tasks,
            "all_task_counts": node_counts_distribution([t["n_p2p_s_nodes"] for t in tasks]),
            "defined_task_counts": node_counts_distribution(
                [t["n_p2p_s_nodes"] for t in tasks if t["defined"]]
            ),
        },
    }
    payload["expected_review_facts"] = {
        "n_defined_expected": "46/47 tasks defined",
        "n_undefined_expected": "1/47 task zero/undefined",
        "sparse_expected": "approximately 9 tasks have <10 nodes",
        "eng_zero_task_expected": "saleor-rc-39b4138e8550",
        "note": (
            "These are Mission-09 prior expectations to verify mechanically; "
            "if actual machine-readable evidence differs, evidence wins and the "
            "discrepancy is reported."
        ),
    }
    payload["hashes"] = {
        "artifact_sha256": canonical_sha256(
            {k: v for k, v in payload.items() if k != "hashes"}
        ),
        "membership_eng_sha256": membership_sha256(membership["DEV_TRAIN_ENG"]),
        "membership_assay_holdout_sha256": membership_sha256(membership["DEV_TRAIN_ASSAY_HOLDOUT"]),
        "membership_dev_validation_sha256": membership_sha256(membership["DEV_VALIDATION"]),
        "membership_union_47_sha256": membership_sha256(
            [t["task_id"] for t in tasks]
        ),
    }
    out_path.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
    return payload


def verify_p2p_s_artifact(payload: dict) -> dict:
    """Independent verification of the frozen P2P-S artifact."""
    tasks = payload["tasks"]
    checks = {
        "n_tasks_is_47": len(tasks) == 47,
        "membership_disjoint": (
            len(
                set(payload["membership"]["DEV_TRAIN_ENG"])
                & set(payload["membership"]["DEV_TRAIN_ASSAY_HOLDOUT"])
                & set(payload["membership"]["DEV_VALIDATION"])
            )
            == 0
        ),
        "membership_union_is_47": len(tasks) == len(
            set(payload["membership"]["DEV_TRAIN_ENG"])
            | set(payload["membership"]["DEV_TRAIN_ASSAY_HOLDOUT"])
            | set(payload["membership"]["DEV_VALIDATION"])
        ),
        "all_evaluator_only": all(t["evaluator_only"] for t in tasks),
        "all_invisible": all(t["invisible_to_generation"] for t in tasks),
        "defined_consistent": all((t["n_p2p_s_nodes"] > 0) == t["defined"] for t in tasks),
        "sparse_consistent": all((0 < t["n_p2p_s_nodes"] < 10) == t["sparse"] for t in tasks),
        "node_ids_sorted_unique": all(t["p2p_s_node_ids"] == sorted(set(t["p2p_s_node_ids"])) for t in tasks),
    }
    artifact_hash = payload["hashes"]["artifact_sha256"]
    recomputed = canonical_sha256(
        {k: v for k, v in payload.items() if k != "hashes"}
    )
    checks["artifact_hash_stable"] = artifact_hash == recomputed
    return {
        "checks": checks,
        "all_pass": all(checks.values()),
        "n_defined": sum(1 for t in tasks if t["defined"]),
        "n_undefined": sum(1 for t in tasks if not t["defined"]),
        "undefined_tasks": [t["task_id"] for t in tasks if not t["defined"]],
        "sparse_tasks": [t["task_id"] for t in tasks if t["sparse"]],
    }
