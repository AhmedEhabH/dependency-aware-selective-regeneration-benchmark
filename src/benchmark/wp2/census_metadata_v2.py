"""WP-2 census / evaluator-side metadata additions (amendment H) - ZERO API.

Deterministic evaluator-side fields for MAIN and relevant DEV census artifacts:
1. production files added in target but absent at parent;
2. number/list or hashed representation of Gold production files that already
   exist at parent;
3. RM-CSS empty-scope flag;
4. Agent empty-scope flag;
5. RM-CSS-vs-Agent scope-identical flag.

Metadata only. Never modifies frozen RM-CSS or Agent predictions.
"""
from __future__ import annotations

import hashlib
import json

from benchmark.wp2.oracle_semantics_v2 import is_test_path_v2

METADATA_VERSION = "census-evaluator-metadata-v1-2026-09-23"
METADATA_SALT = "wp2-evaluator-metadata-v1-2026-09-23"


def is_production_path(path: str) -> bool:
    """Production = not a test path (Gold production source definition)."""
    return not is_test_path_v2(path)


def parse_name_status(text: str) -> list[tuple[str, str]]:
    """Parse ``git diff --name-status`` text into (status, path) pairs.

    Handles the two-column rename/rename-edit form (``R100\told\tnew``), where
    only the new path is kept (status code preserved as given).
    """
    rows: list[tuple[str, str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("R"):
            if len(parts) >= 3:
                rows.append((status, parts[2]))
            continue
        if len(parts) >= 2:
            rows.append((status, parts[1]))
    return rows


def production_files_added_in_target(name_status_rows: list[tuple[str, str]]) -> list[str]:
    """Production files added in target but absent at parent (status A)."""
    return sorted(
        path for status, path in name_status_rows if status.startswith("A") and is_production_path(path)
    )


def gold_files_exist_at_parent(
    gold_production_files: list[str], parent_files: set[str]
) -> list[str]:
    """Gold (target-changed production) files that already exist at parent."""
    return sorted(p for p in gold_production_files if p in parent_files)


def gold_existing_at_parent_hash(gold_production_files: list[str], parent_files: set[str]) -> str:
    """Hashed representation of Gold production files that exist at parent."""
    existing = gold_files_exist_at_parent(gold_production_files, parent_files)
    payload = json.dumps(existing, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def scope_flags(rmcss_paths: list[str], agent_paths: list[str]) -> dict:
    """Deterministic evaluator-side scope flags (never mutates predictions)."""
    r_set = set(rmcss_paths or [])
    a_set = set(agent_paths or [])
    return {
        "rmcss_empty_scope": len(r_set) == 0,
        "agent_empty_scope": len(a_set) == 0,
        "scope_identical": r_set == a_set,
        "rmcss_scope_size": len(r_set),
        "agent_scope_size": len(a_set),
    }


def build_task_metadata(
    *,
    task_id: str,
    name_status_rows: list[tuple[str, str]],
    gold_production_files: list[str],
    parent_files: set[str],
    rmcss_paths: list[str],
    agent_paths: list[str],
) -> dict:
    """Assemble the deterministic evaluator-side metadata record for one task."""
    return {
        "task_id": task_id,
        "metadata_version": METADATA_VERSION,
        "added_in_target_absent_at_parent": production_files_added_in_target(
            name_status_rows
        ),
        "gold_files_exist_at_parent_count": len(
            gold_files_exist_at_parent(gold_production_files, parent_files)
        ),
        "gold_files_exist_at_parent_sha256": gold_existing_at_parent_hash(
            gold_production_files, parent_files
        ),
        **scope_flags(rmcss_paths, agent_paths),
    }
