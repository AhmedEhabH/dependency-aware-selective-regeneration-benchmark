"""WP-2 unchanged-test P2P candidate inventory V1 (amendment J) - ZERO API.

Deterministic inventory of candidate UNCHANGED tests associated with
modules/packages touched by each task.

Frozen V1 rule (amendment J):
- consider unchanged test files in the SAME top-level Saleor app as touched
  production files;
- the test file itself must be unchanged by the target commit;
- keep nodes that pass stably 3/3 on BOTH parent and target;
- if >400 eligible nodes exist for one task, select a deterministic fixed-seed
  sample of 400;
- coverage-based association is NOT primary V1 (later sensitivity analysis).

The P2P oracle/candidate set is evaluator-only and MUST remain invisible to
future generation and repair. Creating the inventory does NOT validate the
final preservation oracle (E2E-G6).
"""
from __future__ import annotations

import hashlib

from benchmark.wp2.oracle_semantics_v2 import three_run_stability_v2

P2P_INVENTORY_VERSION = "p2p-unchanged-inventory-v1-2026-09-23"
P2P_CAP = 400
P2P_SAMPLE_SALT = "wp2-p2p-unchanged-sample-v1-2026-09-23"


def top_level_app(path: str) -> str:
    """First path segment after ``saleor/``."""
    parts = [p for p in path.split("/") if p]
    for idx, part in enumerate(parts):
        if part == "saleor" and idx + 1 < len(parts):
            return parts[idx + 1]
    return "UNKNOWN"


def associate_unchanged_test_files(
    *,
    touched_production_files: list[str],
    all_test_files: list[str],
    target_diff_paths: set[str],
) -> list[str]:
    """Unchanged test files in the same top-level Saleor app as touched
    production files (V1 association rule)."""
    touched_apps = {top_level_app(p) for p in touched_production_files}
    unchanged = [
        t
        for t in all_test_files
        if t not in target_diff_paths and top_level_app(t) in touched_apps
    ]
    return sorted(unchanged)


def stable_p2p_nodes(node_outcomes: dict[str, dict]) -> list[str]:
    """Nodes passing stably 3/3 on BOTH parent and target."""
    eligible: list[str] = []
    for node_id, states in node_outcomes.items():
        parent = states.get("parent") or states.get("parent_outcomes")
        target = states.get("target") or states.get("target_outcomes")
        if parent is None or target is None:
            continue
        if (
            three_run_stability_v2(list(parent)) == "STABLE_PASS"
            and three_run_stability_v2(list(target)) == "STABLE_PASS"
        ):
            eligible.append(node_id)
    return sorted(eligible)


def cap_nodes(node_ids: list[str], *, cap: int = P2P_CAP, salt: str = P2P_SAMPLE_SALT) -> list[str]:
    """Deterministic fixed-seed sample when >``cap`` eligible nodes exist."""
    if len(node_ids) <= cap:
        return sorted(node_ids)
    ordered = sorted(node_ids, key=lambda n: hashlib.sha256(f"{salt}|{n}".encode()).hexdigest())
    return ordered[:cap]


def build_task_inventory(
    *,
    task_id: str,
    touched_production_files: list[str],
    all_test_files: list[str],
    target_diff_paths: set[str],
    node_outcomes: dict[str, dict],
    cap: int = P2P_CAP,
) -> dict:
    """Build the V1 P2P candidate inventory record for one task."""
    associated_files = associate_unchanged_test_files(
        touched_production_files=touched_production_files,
        all_test_files=all_test_files,
        target_diff_paths=target_diff_paths,
    )
    stable = stable_p2p_nodes(node_outcomes)
    capped = cap_nodes(stable, cap=cap)
    return {
        "task_id": task_id,
        "inventory_version": P2P_INVENTORY_VERSION,
        "rule": (
            "unchanged test file, same top-level Saleor app as touched "
            "production file; stable 3/3 pass parent AND target; "
            "fixed-seed cap 400"
        ),
        "association_unchanged_test_files": associated_files,
        "n_associated_test_files": len(associated_files),
        "n_stable_p2p_nodes": len(stable),
        "capped": len(stable) > cap,
        "cap": cap,
        "n_candidate_nodes": len(capped),
        "candidate_nodes": capped,
        "evaluator_only": True,
        "invisible_to_generation": True,
        "preservation_validation_complete": False,
    }
