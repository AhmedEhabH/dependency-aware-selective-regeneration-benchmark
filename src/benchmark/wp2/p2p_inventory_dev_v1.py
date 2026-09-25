"""WP-2 DEV unchanged-test P2P candidate inventory V1 (Mission-08) - ZERO API.

Deterministic DEV inventory using the IDENTICAL frozen P2P Preservation Rule V1
(amendment J) applied to the DEV pool:

- candidate test file must be unchanged by the target commit;
- candidate test file must be in the same top-level Saleor app as touched
  production files;
- deterministic node discovery (pytest --collect-only at target, era env);
- evaluator-only; invisible to generation/repair;
- CAP=400 IS APPLIED AFTER STABILITY FILTERING ONLY (addendum Q7): ALL
  discovered candidate nodes are executed (parent 3/3 + target 3/3), the
  STABLE_P2P nodes are retained, and only then is the deterministic fixed-seed
  cap=400 applied. NO pre-cap of discovered nodes.
- coverage-based association is NOT primary V1;
- no outcome inspection during inventory construction (node stability 3/3 on
  parent AND target is determined only by the later evaluator run).

The MAIN-only inventory (amendment J) covers MAIN 220. This module covers the
frozen DEV pool (DEV_TRAIN 120 + DEV_VALIDATION 30). Split membership comes
from the frozen dev-split-v2 artifact and MUST NOT change.

Sampling salt is the frozen Mission-07 V1 salt (addendum Q8); a new artifact
version/date is the only DEV-specific identity.
"""
from __future__ import annotations

import hashlib
import json

from benchmark.wp2.dev_split_v2 import DEV_SPLIT_VERSION
from benchmark.wp2.p2p_inventory_v1 import P2P_CAP, P2P_INVENTORY_VERSION, P2P_SAMPLE_SALT

P2P_DEV_INVENTORY_VERSION = "p2p-unchanged-inventory-dev-v1-2026-09-25"
P2P_RULE_VERSION = P2P_INVENTORY_VERSION  # frozen V1 identity (addendum Q8)
P2P_SAMPLE_SALT_FROZEN = P2P_SAMPLE_SALT  # wp2-p2p-unchanged-sample-v1-2026-09-23
DEV_SPLIT_REFERENCE = DEV_SPLIT_VERSION

NODE_DISCOVERY_COLLECTED = "COLLECTED"
NODE_DISCOVERY_PENDING = "PENDING"
NODE_DISCOVERY_NOT_APPLICABLE = "NOT_APPLICABLE"

# ---------------------------------------------------------------------------
# Q2 - mutually exclusive P2P node classification
# ---------------------------------------------------------------------------
SIDE_STABLE_PASS = "STABLE_PASS"
SIDE_STABLE_FAIL = "STABLE_FAIL"
SIDE_STABLE_COLLECTION_ERROR = "STABLE_COLLECTION_ERROR"
SIDE_FLAKY = "FLAKY"

P2P_CLASS_STABLE = "STABLE_P2P"
P2P_CLASS_TARGET_BROKEN = "TARGET_BROKEN"
P2P_CLASS_PARENT_BROKEN = "PARENT_BROKEN"
P2P_CLASS_BOTH_FAIL = "BOTH_FAIL"
P2P_CLASS_FLAKY = "FLAKY"
P2P_CLASS_COLLECTION_ERROR = "COLLECTION_ERROR"

P2P_CLASSES = (
    P2P_CLASS_STABLE,
    P2P_CLASS_TARGET_BROKEN,
    P2P_CLASS_PARENT_BROKEN,
    P2P_CLASS_BOTH_FAIL,
    P2P_CLASS_FLAKY,
    P2P_CLASS_COLLECTION_ERROR,
)


def summarize_side_three_runs(outcomes: list[str]) -> str:
    """Per-side 3-run summary (addendum Q2).

    ``outcomes`` elements are one of ``passed`` / ``failed`` / ``error`` /
    ``missing``. Returns STABLE_PASS (3/3 passed), STABLE_FAIL (3/3 failed in
    execution), STABLE_COLLECTION_ERROR (3/3 error/missing, i.e. systematic
    collection failure), or FLAKY (any mixed/non-stable outcome).
    """
    if len(outcomes) != 3:
        raise ValueError("summarize_side_three_runs expects exactly 3 outcomes")
    if all(o == "passed" for o in outcomes):
        return SIDE_STABLE_PASS
    if all(o == "failed" for o in outcomes):
        return SIDE_STABLE_FAIL
    if all(o in ("error", "missing") for o in outcomes):
        return SIDE_STABLE_COLLECTION_ERROR
    return SIDE_FLAKY


def classify_p2p_node(parent_outcomes: list[str], target_outcomes: list[str]) -> str:
    """Exactly one P2P class per node (addendum Q2 precedence)."""
    p = summarize_side_three_runs(parent_outcomes)
    t = summarize_side_three_runs(target_outcomes)
    if p == SIDE_FLAKY or t == SIDE_FLAKY:
        return P2P_CLASS_FLAKY
    if p == SIDE_STABLE_COLLECTION_ERROR or t == SIDE_STABLE_COLLECTION_ERROR:
        return P2P_CLASS_COLLECTION_ERROR
    if p == SIDE_STABLE_PASS and t == SIDE_STABLE_PASS:
        return P2P_CLASS_STABLE
    if p == SIDE_STABLE_PASS and t == SIDE_STABLE_FAIL:
        return P2P_CLASS_TARGET_BROKEN
    if p == SIDE_STABLE_FAIL and t == SIDE_STABLE_PASS:
        return P2P_CLASS_PARENT_BROKEN
    return P2P_CLASS_BOTH_FAIL


def dev_inventory_sha256(payload: dict) -> str:
    """Canonical SHA-256 over the full inventory payload (sorted keys)."""
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def membership_sha256(task_ids: list[str]) -> str:
    """Canonical SHA-256 over a sorted task-id membership list."""
    blob = json.dumps(sorted(task_ids), sort_keys=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def apply_cap_stable_only(
    stable_p2p_node_ids: list[str], *, cap: int = P2P_CAP, salt: str = P2P_SAMPLE_SALT_FROZEN
) -> list[str]:
    """POST-STABILITY fixed-seed cap (addendum Q7/Q8) using the frozen V1 salt."""
    from benchmark.wp2.p2p_inventory_v1 import cap_nodes

    return cap_nodes(stable_p2p_node_ids, cap=cap, salt=salt)


def exclusion_reason(*, oracle_valid: bool, no_changed_test_evidence: bool, env_failed: bool) -> str | None:
    """Deterministic single exclusion reason for tasks outside the 47 union."""
    if oracle_valid:
        return None
    if no_changed_test_evidence:
        return "NO_CHANGED_TEST_EVIDENCE"
    if env_failed:
        return "ENV_INSTALL_FAILED_C4"
    return "NOT_ORACLE_VALID"


def build_task_record(
    *,
    task_id: str,
    split_role: str,
    parent_commit: str,
    target_commit: str,
    era_key: str,
    python_requirement: str,
    oracle_valid: bool,
    no_changed_test_evidence: bool,
    env_failed: bool,
    touched_production_files: list[str],
    associated_unchanged_test_files: list[str],
    candidate_nodes: list[str] | None,
    changed_test_support_present: bool,
) -> dict:
    """Assemble one DEV inventory task record.

    ``candidate_nodes`` is the FULL discovered node list (NOT capped) for the
    47 oracle-valid tasks (addendum Q7/Q9); None for other tasks. The
    scientific cap is post-stability (``n_stable_p2p_nodes_*`` fields are
    filled by the evaluator run, never during construction).
    """
    from benchmark.wp2.p2p_inventory_v1 import top_level_app

    reason = exclusion_reason(
        oracle_valid=oracle_valid,
        no_changed_test_evidence=no_changed_test_evidence,
        env_failed=env_failed,
    )
    base = {
        "task_id": task_id,
        "split_role": split_role,
        "parent_commit": parent_commit,
        "target_commit": target_commit,
        "era_key": era_key,
        "python_requirement": python_requirement,
        "oracle_valid": oracle_valid,
        "exclusion_reason": reason,
        "touched_production_apps": sorted({top_level_app(p) for p in touched_production_files}),
        "n_associated_unchanged_test_files": len(associated_unchanged_test_files),
        "associated_unchanged_test_files": associated_unchanged_test_files,
        "changed_test_support_present": changed_test_support_present,
    }
    if not oracle_valid:
        base.update(
            {
                "n_discovered_candidate_nodes": None,
                "n_stable_p2p_nodes_before_cap": None,
                "n_stable_p2p_nodes_after_cap": None,
                "capped_stable": None,
                "candidate_node_ids": [],
                "preservation_nodes": [],
                "node_discovery_status": NODE_DISCOVERY_NOT_APPLICABLE,
                "zero_candidate_nodes": None,
            }
        )
        return base
    discovered = sorted(candidate_nodes or [])
    base.update(
        {
            "n_discovered_candidate_nodes": len(discovered),
            "n_stable_p2p_nodes_before_cap": None,
            "n_stable_p2p_nodes_after_cap": None,
            "capped_stable": None,
            "candidate_node_ids": discovered,
            "preservation_nodes": [],
            "node_discovery_status": NODE_DISCOVERY_COLLECTED,
            "zero_candidate_nodes": len(discovered) == 0,
        }
    )
    return base


def record_p2p_outcomes(task_record: dict, node_classes: dict[str, str]) -> None:
    """Fill post-execution stability/cap fields (addendum Q7).

    ``node_classes`` maps node_id -> one of the six P2P classes. Only
    STABLE_P2P nodes enter the preservation set; the frozen fixed-seed cap=400
    is applied to the STABLE_P2P set only.
    """
    stable = sorted(n for n, cls in node_classes.items() if cls == P2P_CLASS_STABLE)
    capped = apply_cap_stable_only(stable)
    task_record["n_stable_p2p_nodes_before_cap"] = len(stable)
    task_record["n_stable_p2p_nodes_after_cap"] = len(capped)
    task_record["capped_stable"] = len(stable) > P2P_CAP
    task_record["preservation_nodes"] = capped
