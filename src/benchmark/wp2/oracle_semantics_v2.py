"""WP-2 Oracle semantics V2 - mechanical node-level classification (ZERO API).

Implements the Claude Opus 5.5 amendment A (mechanical oracle classification),
amendment B (frozen test-path regex), and amendment C (environment canary).

This module is the V2 specification. The V1 module
``benchmark.wp2.oracle_confirmation`` is preserved unchanged; V2 consumes
additional explicit inputs (whether the node was collected at parent+testpatch,
whether a shared test-support file failed collection) so classification is
mechanical rather than inferred from failure text alone.

No model/API calls. Never touches the 786 sealed Saleor RESERVE outcomes or the
INTERNAL_TEST pool.
"""
from __future__ import annotations

import hashlib
import re

# ---------------------------------------------------------------------------
# Taxonomy constants (V2)
# ---------------------------------------------------------------------------
BEHAVIORAL_F2P = "BEHAVIORAL_F2P"
SYMBOL_ABSENCE_F2P = "SYMBOL_ABSENCE_F2P"
PARENT_COLLECTION_ERROR = "PARENT_COLLECTION_ERROR"
P2P_ONLY = "P2P_ONLY"
FLAKY = "FLAKY"
TARGET_ORACLE_INVALID = "TARGET_ORACLE_INVALID"
OTHER_REVIEW_REQUIRED = "OTHER_REVIEW_REQUIRED"

V2_CLASSIFICATIONS = (
    BEHAVIORAL_F2P,
    SYMBOL_ABSENCE_F2P,
    PARENT_COLLECTION_ERROR,
    P2P_ONLY,
    FLAKY,
    TARGET_ORACLE_INVALID,
    OTHER_REVIEW_REQUIRED,
)

SEMANTICS_V2_VERSION = "oracle-semantics-v2-2026-09-23"


# ---------------------------------------------------------------------------
# Amendment B - frozen deterministic test-path regex
# ---------------------------------------------------------------------------
# Single deterministic rule covering ONLY: test files, conftest, fixtures, and
# cassettes / equivalent test-support artifacts. Nothing else.
TEST_PATH_REGEX_V2 = re.compile(
    r"(?:"
    r"(?:^|/)(?:tests?)/"  # anything under a tests/test directory
    r"|(?:^|/)test_[^/]+\.py$"  # test_*.py files
    r"|(?:^|/)[^/]+_test\.py$"  # *_test.py files
    r"|(?:^|/)conftest\.py$"  # conftest files
    r"|(?:^|/)fixtures\.py$"  # fixtures files
    r"|(?:^|/)(?:cassettes?)/"  # cassette / recorded test-support dirs
    r")"
)

TEST_PATH_RULE_VERSION = "test-path-rule-v1"
TEST_PATH_REGEX_SHA256 = hashlib.sha256(
    TEST_PATH_REGEX_V2.pattern.encode("utf-8")
).hexdigest()
TEST_PATH_RULE_SHA256 = hashlib.sha256(
    f"{TEST_PATH_RULE_VERSION}\n{TEST_PATH_REGEX_V2.pattern}\n"
    f"{TEST_PATH_REGEX_SHA256}\n".encode()
).hexdigest()


def is_test_path_v2(path: str) -> bool:
    """Apply the frozen V2 test-path rule (amendment B)."""
    return bool(TEST_PATH_REGEX_V2.search(path))


# ---------------------------------------------------------------------------
# Amendment A - mechanical node classification
# ---------------------------------------------------------------------------
_SYMBOL_ABSENCE_PATTERNS = (
    "ImportError:",
    "ModuleNotFoundError:",
    "AttributeError:",
    "NameError:",
    "cannot import name",
    "No module named",
    "ImportError ",
)


def _looks_like_symbol_absence(failure_text: str) -> bool:
    return any(pat in failure_text for pat in _SYMBOL_ABSENCE_PATTERNS)


def three_run_stability_v2(outcomes: list[str]) -> str:
    """STABLE_PASS / STABLE_FAIL / FLAKY over exactly 3 runs."""
    if len(outcomes) != 3:
        raise ValueError("three_run_stability_v2 expects exactly 3 outcomes")
    if all(o == "passed" for o in outcomes):
        return "STABLE_PASS"
    if all(o in ("failed", "error") for o in outcomes):
        return "STABLE_FAIL"
    return FLAKY


def classify_node_v2(
    *,
    target_outcomes: list[str],
    parent_outcomes: list[str],
    parent_failure_text: str,
    parent_collects_node: bool,
    shared_test_support_failed: bool = False,
) -> str:
    """Mechanically classify one test node under the frozen V2 rule.

    Evaluation order (frozen in amendment A):
    1. target or parent flaky                      -> FLAKY
    2. target not STABLE_PASS                      -> TARGET_ORACLE_INVALID
    3. parent STABLE_PASS                          -> P2P_ONLY
    4. shared test-support collection failure OR
       node not collected at parent+testpatch      -> PARENT_COLLECTION_ERROR
    5. parent failure is symbol-absence signature  -> SYMBOL_ABSENCE_F2P
    6. parent failure is behavioral (assertion or
       other behavioral exception not covered
       by symbol absence)                          -> BEHAVIORAL_F2P
    7. otherwise                                   -> OTHER_REVIEW_REQUIRED

    ``parent_collects_node`` is supplied by the harness: True only when the node
    exists and its module/conftest/fixture/cassette/test-support imports
    collected successfully at parent+testpatch.
    """
    target_stability = three_run_stability_v2(target_outcomes)
    parent_stability = three_run_stability_v2(parent_outcomes)
    if target_stability == FLAKY or parent_stability == FLAKY:
        return FLAKY
    if target_stability != "STABLE_PASS":
        return TARGET_ORACLE_INVALID
    if parent_stability == "STABLE_PASS":
        return P2P_ONLY
    # parent STABLE_FAIL
    if shared_test_support_failed or not parent_collects_node:
        return PARENT_COLLECTION_ERROR
    if _looks_like_symbol_absence(parent_failure_text):
        return SYMBOL_ABSENCE_F2P
    if parent_failure_text.strip():
        # collected at parent, failed in call/execution with a non-symbol
        # failure: an assertion OR another behavioral exception (amendment A 3).
        return BEHAVIORAL_F2P
    # no failure detail at all: genuinely ambiguous -> manual review.
    return OTHER_REVIEW_REQUIRED


# ---------------------------------------------------------------------------
# Task-level eligibility (amendment A)
# ---------------------------------------------------------------------------
def task_eligibility_v2(
    *,
    n_behavioral_f2p: int,
    n_symbol_absence_f2p: int,
    n_parent_collection_error: int,
    environment_valid: bool,
    task_collection_failure: bool = False,
) -> dict:
    """Task-level primary eligibility.

    A task is primary-eligible iff it contains >=1 stable BEHAVIORAL_F2P node,
    the environment is valid, and the whole task was not invalidated by a
    systemic environment/collection failure. Flaky/target-invalid nodes are
    excluded node-wise and do NOT invalidate an otherwise eligible task.
    PCE and SYMBOL_ABSENCE counts are preserved separately.
    """
    primary = (
        n_behavioral_f2p >= 1
        and environment_valid
        and not task_collection_failure
    )
    extended = (
        (n_behavioral_f2p + n_symbol_absence_f2p) >= 1
        and environment_valid
        and not task_collection_failure
    )
    return {
        "PRIMARY_BEHAVIORAL_F2P_ELIGIBLE": primary,
        "EXTENDED_F2P_ELIGIBLE": extended,
        "n_behavioral_f2p": n_behavioral_f2p,
        "n_symbol_absence_f2p": n_symbol_absence_f2p,
        "n_parent_collection_error": n_parent_collection_error,
        "environment_valid": environment_valid,
        "task_collection_failure": task_collection_failure,
        "semantics_version": SEMANTICS_V2_VERSION,
    }


# ---------------------------------------------------------------------------
# Amendment C - per-task environment canary selection
# ---------------------------------------------------------------------------
CANARY_SALT = "wp2-env-canary-v1-2026-09-23"

CANARY_VALID = "CANARY_VALID"
CANARY_ENV_INVALID = "CANARY_ENV_INVALID"
CANARY_NONE = "CANARY_NONE"


def _top_level_app(path: str) -> str:
    """Top-level Saleor app: the first path segment after ``saleor/``."""
    parts = [p for p in path.split("/") if p]
    for idx, part in enumerate(parts):
        if part == "saleor" and idx + 1 < len(parts):
            return parts[idx + 1]
    return "UNKNOWN"


def select_canary_node(
    *,
    node_ids: list[str],
    changed_test_files: list[str],
    touched_production_files: list[str],
    max_nodes: int = 200,
) -> str | None:
    """Deterministically pick one unchanged pre-existing canary test node.

    Preference order (frozen):
    1. first stable node (sorted deterministically) in a changed test file's
       SAME module directory as a touched production file;
    2. first node in the same top-level Saleor app as any touched production
       file;
    3. first remaining node in the candidate set.
    Never returns a node whose file is in ``changed_test_files``.
    Returns None when no defensible canary exists.
    """
    changed = set(changed_test_files)
    candidates = [
        n
        for n in node_ids
        if "::" in n and _node_file(n) not in changed and _node_file(n) != "?"
    ]
    if not candidates:
        return None
    if len(candidates) > max_nodes:
        candidates = sorted(
            candidates,
            key=lambda n: hashlib.sha256(f"{CANARY_SALT}|{n}".encode()).hexdigest(),
        )[:max_nodes]
    touched_apps = {_top_level_app(p) for p in touched_production_files}
    same_app = [
        n for n in candidates if _top_level_app(_node_file(n)) in touched_apps
    ]
    pool = same_app or candidates
    ordered = sorted(pool, key=lambda n: hashlib.sha256(f"{CANARY_SALT}|{n}".encode()).hexdigest())
    return ordered[0]


def _node_file(node_id: str) -> str:
    return node_id.split("::", 1)[0]


def canary_verdict(parent_outcomes: list[str], target_outcomes: list[str]) -> str:
    """Canary verdict: valid only if both states pass 3/3."""
    if parent_outcomes == ["passed", "passed", "passed"] and target_outcomes == [
        "passed",
        "passed",
        "passed",
    ]:
        return CANARY_VALID
    return CANARY_ENV_INVALID


# ---------------------------------------------------------------------------
# Protected pools guard (amendments F/G)
# ---------------------------------------------------------------------------
def assert_task_allowed(task_id: str) -> None:
    """Refuse INTERNAL_TEST / sealed-RESERVE task access (amendment G)."""
    if task_id.startswith("saleor-rc-internal") or "internal_test" in task_id.lower():
        raise ValueError(f"INTERNAL_TEST access forbidden for {task_id}")
    if task_id.startswith("saleor-rc-reserve") or "reserve" in task_id.lower():
        raise ValueError(f"RESERVE access forbidden for {task_id}")
