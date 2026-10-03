"""M17 K07 - P2P/F2P contract logic for the qualification/main execution path.

Pure, deterministic, zero-Docker/zero-API contract helpers used by the
qualification executor and exercised by the K07 contract tests.

F2P contract:
- obtain the frozen failing-to-passing test node set from frozen evaluator
  artifacts;
- pass those exact nodes to the evaluator boundary;
- record per-node status;
- a task cannot be marked resolved when required F2P nodes are absent or
  unresolved;
- strict/robust semantics preserved.

P2P contract:
- frozen P2P-S/P2P-U identities are selector-blind (they carry no selector
  outcome);
- unchanged-test preservation is recorded separately from F2P;
- a P2P failure cannot be silently reclassified as infrastructure success;
- robust aggregation is deterministic.

Terminal classification vocabulary mirrors the frozen V3 oracle semantics
(oracle_semantics_v2) and the M17 plan exit tokens.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

# Frozen V3 classification vocabulary
BEHAVIORAL_F2P = "BEHAVIORAL_F2P"
SYMBOL_ABSENCE_F2P = "SYMBOL_ABSENCE_F2P"
PARENT_COLLECTION_ERROR = "PARENT_COLLECTION_ERROR"
P2P_ONLY = "P2P_ONLY"
FLAKY = "FLAKY"
TARGET_ORACLE_INVALID = "TARGET_ORACLE_INVALID"
OTHER_REVIEW_REQUIRED = "OTHER_REVIEW_REQUIRED"

F2P_CLASSES = (BEHAVIORAL_F2P, SYMBOL_ABSENCE_F2P)
P2P_CLASS = "STABLE_P2P"

# P2P-U node classes (frozen evaluator artifact)
P2P_U_CLASSES = ("STABLE_P2P", "TARGET_BROKEN", "PARENT_BROKEN", "BOTH_FAIL",
                 "FLAKY", "COLLECTION_ERROR")

TERMINAL_RESOLVED = "RESOLVED"
TERMINAL_F2P_PARTIAL = "F2P_PARTIAL"
TERMINAL_F2P_UNRESOLVED = "F2P_UNRESOLVED"
TERMINAL_P2P_REGRESSION = "P2P_REGRESSION"
TERMINAL_INFRA = "INFRA_UNRESOLVED"
TERMINAL_ENV_INSTALL_BLOCKED = "ENV_INSTALL_BLOCKED"


def canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha_obj(obj: Any) -> str:
    return hashlib.sha256(canon(obj).encode("utf-8")).hexdigest()


# ------------------------------------------------------------------ frozen F2P node set
def f2p_node_set_from_frozen(per_task_v2: dict, node_records: list[dict]) -> list[str]:  # noqa: ARG001
    """Frozen failing-to-passing test node set.

    ``per_task_v2`` is the frozen V2 per-task record (counts); ``node_records``
    is the per-node v3_class map obtained from the frozen evaluator artifacts.
    The F2P node set is the exact set of nodes whose v3_class is a frozen F2P
    class, bounded by the frozen count when the record is authoritative.
    Returns a sorted list; selector-blind (no selector field is read).
    """
    frozen_f2p = {
        n["node_id"] for n in node_records if n.get("v3_class") in F2P_CLASSES
    }
    # Deterministic, never invents nodes: if the evaluator node set is smaller
    # than the frozen count the task is unresolved (missing F2P nodes).
    return sorted(frozen_f2p)


def required_f2p_missing(frozen_count: int, obtained_nodes: list[str]) -> bool:
    return len(obtained_nodes) < frozen_count


def evaluate_nodes(node_set: list[str], evaluator: Any) -> dict[str, str]:
    """Pass the exact F2P nodes to the evaluator boundary; record per-node status."""
    out: dict[str, str] = {}
    for node in node_set:
        out[node] = evaluator(node)
    return out


def task_resolvable(*, frozen_count: int, node_set: list[str],
                    per_node_status: dict[str, str]) -> tuple[bool, list[str]]:
    """A task is resolved only when every required F2P node is present and passes.

    Returns (resolved, blockers). A node that is absent (missing from the set)
    or whose status is not a passing F2P outcome blocks resolution.
    """
    blockers: list[str] = []
    if required_f2p_missing(frozen_count, node_set):
        blockers.append(f"MISSING_F2P_NODES:{frozen_count}!={len(node_set)}")
    for node in node_set:
        status = per_node_status.get(node)
        if status is None:
            blockers.append(f"UNRESOLVED_NODE:{node}")
        elif status not in ("passed", "PASS"):
            blockers.append(f"FAILED_NODE:{node}:{status}")
    return not blockers, blockers


# ------------------------------------------------------------------ P2P contract
def p2p_nodes_from_frozen(p2p_s_eng: dict, p2pu_eng: dict | None, task_id: str) -> dict:
    """Selector-blind frozen P2P-S/P2P-U identity extraction for a task.

    Returns {"p2p_s_nodes": [...], "p2p_u_nodes": [...]}. Neither source carries
    a selector outcome; the extractor reads only node identities.
    """
    p2p_s: list[str] = []
    if p2p_s_eng:
        for row in p2p_s_eng.get("per_task", []):
            if row.get("task_id") == task_id:
                p2p_s = sorted(set(row.get("additions_v3", [])) | set(row.get("intersection", [])))
                break
    p2p_u: list[str] = []
    if p2pu_eng and p2pu_eng.get("task_id") == task_id:
        p2p_u = sorted(n for n, c in (p2pu_eng.get("node_classes") or {}).items()
                       if c == P2P_CLASS)
    return {"p2p_s_nodes": p2p_s, "p2p_u_nodes": p2p_u, "selector_blind": True}


def p2p_failure_reclassified(nodes: dict, per_node_status: dict[str, str]) -> list[str]:
    """A P2P node failure must never be silently reclassified as infra success.

    Returns a list of violations; empty means the P2P outcome is faithfully
    recorded. A node whose evaluator status is infra-like (COLLECTION_ERROR,
    INFRA, TARGET_BROKEN, PARENT_BROKEN, BOTH_FAIL) but which is a frozen
    stable-pass P2P identity is a masked regression.
    """
    bad = []
    for kind in ("p2p_s_nodes", "p2p_u_nodes"):
        for node in nodes.get(kind, []):
            st = per_node_status.get(node)
            if st is None:
                continue
            if st in ("passed", "PASS", "STABLE_P2P"):
                continue
            if st in ("INFRA", "infra", "COLLECTION_ERROR", "TARGET_BROKEN",
                      "PARENT_BROKEN", "BOTH_FAIL"):
                bad.append(f"P2P_REGRESSION_MASKED_AS_INFRA:{node}")
    return bad


def p2p_regressions(nodes: dict, per_node_status: dict[str, str]) -> list[str]:
    """Frozen stable-pass P2P identities that no longer pass (selector-blind).

    A P2P node whose evaluator status is a hard failure/regression (not infra,
    not passed) is a genuine P2P regression, recorded separately from F2P and
    never reclassified as infrastructure success.
    """
    bad = []
    for kind in ("p2p_s_nodes", "p2p_u_nodes"):
        for node in nodes.get(kind, []):
            st = per_node_status.get(node)
            if st is None:
                bad.append(f"P2P_UNRESOLVED:{node}")
            elif st in ("passed", "PASS", "STABLE_P2P"):
                continue
            elif st in ("INFRA", "infra", "COLLECTION_ERROR", "TARGET_BROKEN",
                        "PARENT_BROKEN", "BOTH_FAIL"):
                continue  # infra-masked handled separately by p2p_failure_reclassified
            else:
                bad.append(f"P2P_REGRESSION:{node}:{st}")
    return bad


def robust_aggregate(per_task: dict[str, dict]) -> dict:
    """Deterministic robust aggregation over per-task terminal classifications."""
    keys = sorted(per_task)
    out: dict[str, Any] = {"n_tasks": len(keys), "counts": {}, "tasks": {}}
    for tid in keys:
        rec = per_task[tid]
        terminal = rec.get("terminal", TERMINAL_INFRA)
        out["counts"][terminal] = out["counts"].get(terminal, 0) + 1
        out["tasks"][tid] = {"terminal": terminal,
                             "n_f2p": rec.get("n_f2p", 0),
                             "n_p2p": rec.get("n_p2p", 0)}
    out["aggregate_sha256"] = sha_obj({k: v for k, v in out.items()
                                       if k not in ("aggregate_sha256",)})
    return out


# ------------------------------------------------------------------ terminal classification
def terminal_classify(*, task_id: str, frozen_count: int, node_set: list[str],
                      per_node_status: dict[str, str], env_install_blocked: bool,
                      infra: bool, p2p_failures: list[str]) -> tuple[str, dict]:
    """Deterministic terminal classification for one task.

    Order (frozen fail-closed):
      1. env install blocked      -> ENV_INSTALL_BLOCKED
      2. infra                    -> INFRA_UNRESOLVED
      3. unresolved F2P           -> F2P_UNRESOLVED
      4. partial F2P              -> F2P_PARTIAL
      5. P2P regression           -> P2P_REGRESSION
      6. otherwise                -> RESOLVED
    """
    resolved, blockers = task_resolvable(frozen_count=frozen_count, node_set=node_set,
                                         per_node_status=per_node_status)
    evidence = {
        "task_id": task_id,
        "frozen_f2p_count": frozen_count,
        "obtained_f2p_nodes": node_set,
        "per_node_status": {k: v for k, v in sorted(per_node_status.items())},
        "blockers": blockers,
        "p2p_failures": sorted(p2p_failures),
    }
    if env_install_blocked:
        return TERMINAL_ENV_INSTALL_BLOCKED, evidence
    if infra:
        return TERMINAL_INFRA, evidence
    if not resolved:
        if len(node_set) < frozen_count and len(node_set) > 0:
            return TERMINAL_F2P_PARTIAL, evidence
        return TERMINAL_F2P_UNRESOLVED, evidence
    if p2p_failures:
        return TERMINAL_P2P_REGRESSION, evidence
    return TERMINAL_RESOLVED, evidence
