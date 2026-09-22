"""WP-2 Oracle Confirmation - deterministic F2P/P2P oracle semantics (ZERO API).

Defines the exact state construction, test-only patch derivation, JUnit
parsing, 3-run stability classification, failure taxonomy, task eligibility
flags, and deterministic selection strata/order used by the Oracle
Confirmation harness (scripts/wp2_oracle_confirm.py).

This module performs no model/API calls and never touches the 786 sealed
Saleor RESERVE outcomes.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Taxonomy constants
# ---------------------------------------------------------------------------
BEHAVIORAL_F2P = "BEHAVIORAL_F2P"
SYMBOL_ABSENCE_F2P = "SYMBOL_ABSENCE_F2P"
P2P_ONLY = "P2P_ONLY"
ENV_BROKEN = "ENV_BROKEN"
TEST_PATCH_APPLY_FAIL = "TEST_PATCH_APPLY_FAIL"
FLAKY = "FLAKY"
TARGET_ORACLE_INVALID = "TARGET_ORACLE_INVALID"
OTHER_REVIEW_REQUIRED = "OTHER_REVIEW_REQUIRED"

TASK_CLASSIFICATIONS = (
    BEHAVIORAL_F2P,
    SYMBOL_ABSENCE_F2P,
    P2P_ONLY,
    ENV_BROKEN,
    TEST_PATCH_APPLY_FAIL,
    FLAKY,
    TARGET_ORACLE_INVALID,
    OTHER_REVIEW_REQUIRED,
)

SELECTION_SALT = "wp2-oracle-confirmation-2026-09-22"


# ---------------------------------------------------------------------------
# Test-file path classification
# ---------------------------------------------------------------------------
def is_test_path(path: str) -> bool:
    parts = Path(path).parts
    base = Path(path).name
    return "tests" in parts or base.startswith("test_") or base.endswith("_test.py")


def is_sealed_outcome_source(path: str) -> bool:
    low = path.lower()
    if "saleor-reserve-300-rmcss" in low:
        return True
    if "saleor_candidate_metadata" in low or "candidate_metadata" in low:
        return True
    return "/transparency/" in low


# ---------------------------------------------------------------------------
# Test-only patch derivation (pure diff filter; callers pass git diff output)
# ---------------------------------------------------------------------------
def derive_test_only_patch_bytes(full_diff: str, test_paths: list[str]) -> str:
    """Filter a unified diff to only the given test-file paths.

    Returns the concatenated hunks whose 'diff --git a/<path>' line is in
    test_paths. Raises ValueError if no test path remains.
    """
    test_paths = set(test_paths)
    hunks: list[str] = []
    current: list[str] = []
    current_path: str | None = None

    def flush() -> None:
        nonlocal current, current_path
        if current_path is not None and current_path in test_paths and current:
            hunks.append("\n".join(current))
        current = []
        current_path = None

    for line in full_diff.splitlines():
        if line.startswith("diff --git "):
            flush()
            m = re.match(r"diff --git a/(.+?) b/(.+)$", line)
            if m:
                current_path = m.group(1)
                current = [line]
                continue
        if current_path is not None:
            current.append(line)
    flush()
    if not hunks:
        raise ValueError("test-only patch is empty")
    result = "\n\n".join(hunks)
    if not result.endswith("\n"):
        result += "\n"
    return result


# ---------------------------------------------------------------------------
# JUnit parsing
# ---------------------------------------------------------------------------
def parse_junit(xml_text: str) -> dict[str, str]:
    """Parse pytest JUnit XML into {node_id: outcome}.

    node_id is reconstructed to match pytest's collection node id:
    ``<file>::<name>`` when a ``file`` attribute is present, else
    ``<classname-as-path>.py::<name>`` (classname is the dotted module name,
    e.g. ``tests.test_m`` -> ``tests/test_m.py``). Outcome is one of
    passed/failed/error/skipped.
    """
    import xml.etree.ElementTree as ET

    nodes: dict[str, str] = {}
    root = ET.fromstring(xml_text)
    for tc in root.iter("testcase"):
        fname = tc.get("file")
        cname = tc.get("classname")
        name = tc.get("name") or "?"
        if fname:
            node_id = f"{fname}::{name}"
        elif cname:
            rel = cname.replace(".", "/") + ".py"
            node_id = f"{rel}::{name}"
        else:
            # collection failure: classname is empty and name is the module path
            node_id = name.replace(".", "/") + ".py"
        if tc.find("failure") is not None:
            nodes[node_id] = "failed"
        elif tc.find("error") is not None:
            nodes[node_id] = "error"
        elif tc.find("skipped") is not None:
            nodes[node_id] = "skipped"
        else:
            nodes[node_id] = "passed"
    return nodes


# ---------------------------------------------------------------------------
# 3-run stability
# ---------------------------------------------------------------------------
def three_run_stability(outcomes: list[str]) -> str:
    """Classify a node across 3 runs: STABLE_PASS / STABLE_FAIL / FLAKY."""
    if len(outcomes) != 3:
        raise ValueError("three_run_stability expects exactly 3 outcomes")
    if all(o == "passed" for o in outcomes):
        return "STABLE_PASS"
    if all(o in ("failed", "error") for o in outcomes):
        return "STABLE_FAIL"
    return FLAKY


_SYMBOL_ABSENCE_PATTERNS = (
    "ImportError:",
    "ModuleNotFoundError:",
    "AttributeError:",
    "NameError:",
    "cannot import name",
    "No module named",
)


def _looks_like_symbol_absence(failure_text: str) -> bool:
    return any(pat in failure_text for pat in _SYMBOL_ABSENCE_PATTERNS)


def classify_failure_reason(
    target_outcomes: list[str],
    parent_outcomes: list[str],
    parent_failure_text: str,
) -> str:
    """Classify a single test node under the frozen taxonomy."""
    target_stability = three_run_stability(target_outcomes)
    parent_stability = three_run_stability(parent_outcomes)
    if target_stability == FLAKY or parent_stability == FLAKY:
        return FLAKY
    if target_stability != "STABLE_PASS":
        return TARGET_ORACLE_INVALID
    if parent_stability == "STABLE_PASS":
        return P2P_ONLY
    # parent STABLE_FAIL
    if _looks_like_symbol_absence(parent_failure_text):
        return SYMBOL_ABSENCE_F2P
    if re.search(r"assert |AssertionError|expected exception|Traceback", parent_failure_text):
        return BEHAVIORAL_F2P
    return OTHER_REVIEW_REQUIRED


# ---------------------------------------------------------------------------
# Task eligibility
# ---------------------------------------------------------------------------
def task_eligibility(
    n_behavioral_f2p: int,
    n_symbol_absence_f2p: int,
    n_p2p: int,
    target_oracle_stable: bool,
    environment_valid: bool,
) -> dict:
    primary = n_behavioral_f2p >= 1 and target_oracle_stable and environment_valid
    extended = (
        (n_behavioral_f2p + n_symbol_absence_f2p) >= 1
        and target_oracle_stable
        and environment_valid
    )
    return {
        "PRIMARY_BEHAVIORAL_F2P_ELIGIBLE": primary,
        "EXTENDED_F2P_ELIGIBLE": extended,
        "n_behavioral_f2p": n_behavioral_f2p,
        "n_symbol_absence_f2p": n_symbol_absence_f2p,
        "n_p2p": n_p2p,
        "target_oracle_stable": target_oracle_stable,
        "environment_valid": environment_valid,
    }


# ---------------------------------------------------------------------------
# Selection (deterministic, outcome-blind)
# ---------------------------------------------------------------------------
def select_strong_tasks(candidates: list[dict]) -> list[dict]:
    return [c for c in candidates if c.get("f2p_candidacy") == "STRONG_F2P_CANDIDATE"]


def _selection_rank(task_id: str) -> str:
    return hashlib.sha256(f"{SELECTION_SALT}|{task_id}".encode()).hexdigest()


def build_selection_order(tasks: list[dict]) -> list[dict]:
    """Round-robin across non-empty strata; within stratum sort by hash rank.

    Strata keys come from structural metadata only: env_family,
    migration_or_config_heavy, changed_source_bin, n_modified_test_files_bin.
    """
    strata: dict[str, list[dict]] = {}
    for t in tasks:
        key = "|".join(
            [
                str(t.get("env_family", "UNKNOWN")),
                str(t.get("migration_or_config_heavy", False)),
                str(t.get("changed_source_bin", "UNKNOWN")),
                str(t.get("n_modified_test_files_bin", "UNKNOWN")),
            ]
        )
        strata.setdefault(key, []).append(t)
    ordered: list[dict] = []
    pool = {k: sorted(v, key=lambda t: _selection_rank(t["task_id"])) for k, v in strata.items()}
    while pool:
        for key in sorted(pool):
            queue = pool[key]
            if not queue:
                continue
            ordered.append(queue.pop(0))
        pool = {k: v for k, v in pool.items() if v}
    return ordered


# ---------------------------------------------------------------------------
# Attrition reconciliation
# ---------------------------------------------------------------------------
def reconcile_attrition(per_task: list[dict]) -> dict:
    counts: dict[str, int] = {}
    for t in per_task:
        cls = t.get("classification") or t.get("status") or "UNKNOWN"
        counts[cls] = counts.get(cls, 0) + 1
    total = len(per_task)
    accounted = sum(counts.values())
    return {
        **counts,
        "total": total,
        "unaccounted": total - accounted,
    }


def load_census(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
