#!/usr/bin/env python3
"""T12 M02-D2 — frozen materializer input-schema helpers (OFFLINE, stdlib only).

Mission: T12_M02_D2_INPUT_CONTRACT_20261027 (Track 1.2).  This module is the
single source of truth for the *offline-provable* portion of the frozen
``opws_phase3b_patch_materialize.py`` input contract, re-implemented with the
standard library only so it can run anywhere (no frozen-worktree import, no
benchmark package, no network, no execution).

EVERY constant and rule below is a verbatim transcription of the frozen
materializer / opws_phase2_plan sources (read-only) on 2026-10-27:

* ``{"scope": [paths]}`` scope-json file schema — materializer CLI lines
  1151-1155 and 1174-1176; canonical scope-path spellings + canonical scope
  hash recipe from ``scripts/opws_phase2_plan.py`` lines 105-166.
* ``{"changes": {path: status}}`` classification-json file schema —
  materializer CLI lines 1156-1158; ``FROZEN_STATUSES`` line 427;
  ``normalize_classification`` lines 428-453.
* frozen status derivation — ``git diff --name-status -z --no-renames`` from
  ``git_name_status_map`` lines 337-380 (statuses M/D/A; R -> R_OLD/R_NEW;
  C/T/U/X/B fail closed).
* census status mapping ``CENSUS_STATUS_TO_FROZEN`` line 426 and the
  ``TestPathAuthority`` shape ``{changed_paths, test_paths, source}`` lines
  395-424.

This module performs NO git calls by default (``git_name_status_map`` remains
an explicit opt-in) and NEVER reads outcomes, gold labels or JUnit.  It only
normalizes and hashes inputs under the frozen schema.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------
# Frozen constants (verbatim from the pinned materializer sources)
# --------------------------------------------------------------------------

# ``FROZEN_STATUSES`` — materialize.py line 427.
FROZEN_STATUSES: tuple[str, ...] = ("M", "D", "A", "R_OLD", "R_NEW")

# ``CENSUS_STATUS_TO_FROZEN`` — materialize.py line 426 (renamed is NOT in
# this map: a census rename record names ONE pair head without per-side
# paths/flags, so it needs an explicit side authority — never a guess).
CENSUS_STATUS_TO_FROZEN: dict[str, str] = {"modified": "M", "added": "A", "deleted": "D"}

# Frozen diff vectors — materialize.py lines 93-107:
# DIFF_SETTINGS lines 93-98 and DIFF_FLAGS lines 100-107.
DIFF_SETTINGS: tuple[str, ...] = (
    "-c",
    "diff.noprefix=false",
    "-c",
    "diff.mnemonicPrefix=false",
)
DIFF_FLAGS: tuple[str, ...] = (
    "--no-renames",
    "--full-index",
    "--binary",
    "--no-ext-diff",
    "--no-color",
    "--no-textconv",
)

# Canonical scope-path rule (opws_phase2_plan.py lines 103-147): NO ``.`` /
# ``..`` traversal or redundant components, NO aliasing, repository-relative
# forward-slash spellings only.
_DRIVE_PREFIX_RE = re.compile(r"^[A-Za-z]:[\\/]?")
_FORBIDDEN_PATH_COMPONENTS = ("", ".", "..")


class SchemaError(Exception):
    """Fail-closed input-schema violation (never silently dropped)."""


def canonicalize_scope_paths(paths: Any, context: str = "scope") -> tuple[list[str], int]:
    """Validate + dedupe a scope path list under the frozen canonical rule.

    Mirrors ``opws_phase2_plan.normalize_scope_paths`` (lines 135-148):
    fail closed on non-list input or any invalid path (absolute, drive
    prefix, backslash, empty, ``.``/``..`` component); returns
    ``(sorted unique canonical paths, duplicate_count)``.
    """
    if not isinstance(paths, (list, tuple)):
        raise SchemaError(f"{context}: scope paths must be a list, got {type(paths).__name__}")
    canonical: list[str] = []
    for raw in paths:
        canonical.append(canonicalize_scope_path(raw, context=context))
    unique = sorted(set(canonical))
    return unique, len(canonical) - len(unique)


def canonicalize_scope_path(path: Any, context: str = "scope") -> str:
    """Canonical repository-relative forward-slash spelling (frozen rule)."""
    if not isinstance(path, str) or path == "":
        raise SchemaError(f"{context}: scope path must be a non-empty string, got {path!r}")
    if "\\" in path:
        raise SchemaError(f"{context}: backslash not allowed in repository-relative scope path: {path!r}")
    if _DRIVE_PREFIX_RE.match(path):
        raise SchemaError(
            f"{context}: absolute drive prefix not allowed in repository-relative scope path: {path!r}"
        )
    if path.startswith("/"):
        raise SchemaError(f"{context}: absolute leading-slash path is not repository-relative: {path!r}")
    for comp in path.split("/"):
        if comp in _FORBIDDEN_PATH_COMPONENTS:
            raise SchemaError(
                f"{context}: path component {comp!r} forbidden in repository-relative scope path: {path!r}"
            )
    return path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_scope_hash(paths: list[str]) -> str:
    """Frozen canonical scope hash (``compute_canonical_scope_hash``,
    opws_phase2_plan.py lines 157-166).

    Normalize (canonical rule), deduplicate, sort lexicographically (byte
    order); canonical JSON = ``json.dumps(sorted_list, sort_keys=False,
    ensure_ascii=False, separators=(",", ":"))``; hash input = that canonical
    JSON encoded UTF-8.
    """
    normalized, _ = canonicalize_scope_paths(paths, context="scope")
    canonical = json.dumps(normalized, sort_keys=False, ensure_ascii=False, separators=(",", ":"))
    return sha256_bytes(canonical.encode("utf-8"))


def normalize_classification(
    classification: dict[str, Any],
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """Validate + canonicalize a frozen change classification.

    Mirrors ``normalize_classification`` (materialize.py lines 428-453):
    returns ``(canonical_classification, invalid_records)``; each invalid
    record names the offending path and reason (fail-closed guard, never
    silently dropped).  Statuses outside ``FROZEN_STATUSES`` and path
    spellings outside the canonical rule are rejected.
    """
    if not isinstance(classification, dict):
        raise SchemaError("classification must be a dict {path: status}")
    canonical: dict[str, str] = {}
    invalid: list[dict[str, Any]] = []
    for raw_path, status in classification.items():
        try:
            path = canonicalize_scope_path(raw_path, context="classification")
        except SchemaError as exc:
            invalid.append({"path": raw_path, "reason": f"INVALID_PATH: {exc}"})
            continue
        if status not in FROZEN_STATUSES:
            invalid.append(
                {
                    "path": path,
                    "reason": f"UNSUPPORTED_STATUS: {status!r} (frozen statuses: {FROZEN_STATUSES})",
                }
            )
            continue
        canonical[path] = status
    return canonical, invalid


def parse_name_status_z(fields: list[bytes]) -> dict[str, str]:
    """Parse the frozen ``git diff -z --name-status`` NUL stream.

    Mirrors ``git_name_status_map`` (materialize.py lines 337-380): first
    token per record = status, then path fields.  Statuses M/D/A; R =
    R_OLD(old) + R_NEW(new) (defensive; with ``--no-renames`` git never emits
    R); C/T/U/X/B fail closed (not part of the frozen R1 primary set);
    truncated records fail closed.
    """
    out: dict[str, str] = {}
    i = 0
    while i < len(fields):
        raw = fields[i]
        if not raw:
            i += 1
            continue
        status = raw.decode("utf-8", "replace")[:2]
        status_letter = status[0]
        if status_letter not in ("A", "C", "D", "M", "R", "T", "U", "X", "B"):
            raise SchemaError(f"unparseable git name-status token: {status!r}")
        if status_letter == "R":
            if i + 2 >= len(fields):
                raise SchemaError(f"truncated rename record for {raw!r}")
            old = fields[i + 1].decode("utf-8", "replace")
            new = fields[i + 2].decode("utf-8", "replace")
            out[old] = "R_OLD"
            out[new] = "R_NEW"
            i += 3
            continue
        if status_letter in ("C", "T", "U", "X", "B"):
            raise SchemaError(f"unsupported git status {status_letter!r} for path record")
        if i + 1 >= len(fields):
            raise SchemaError(f"truncated status record {status!r}")
        path = fields[i + 1].decode("utf-8", "replace")
        if status_letter == "A":
            out[path] = "A"
        elif status_letter == "D":
            out[path] = "D"
        else:
            out[path] = "M"
        i += 2
    return out


def git_name_status_map(repo: Path, parent: str, target: str) -> dict[str, str]:
    """Frozen file-status classification via read-only ``git diff``.

    Protocol-identical to ``git_name_status_map`` (materialize.py line 337):
    ``git diff -z --name-status <DIFF_FLAGS> <parent> <target>`` with the
    frozen ``-c`` settings; read-only, no side effects.  Raises SchemaError on
    a non-zero git return code without inspecting any output content.
    """
    cmd = ["git", "-C", str(repo), *DIFF_SETTINGS, "diff", "-z", "--name-status",
           *DIFF_FLAGS, parent, target]
    proc = subprocess.run(cmd, capture_output=True, check=False)
    if proc.returncode != 0:
        raise SchemaError(
            f"git name-status failed rc={proc.returncode} for {parent}..{target} "
            "(read-only diff; no output content inspected)"
        )
    return parse_name_status_z(proc.stdout.split(b"\x00"))


def census_changes_map(records: list[dict[str, Any]]) -> dict[str, str]:
    """Map frozen census per-path records to frozen classification statuses.

    Mirrors ``census_records_to_authority`` (materialize.py lines 583-640),
    restricted to the status map: ``modified -> M, added -> A, deleted -> D``;
    a ``renamed`` record is AMBIGUOUS without an explicit side authority and
    raises SchemaError (sides are never guessed from filenames).
    """
    out: dict[str, str] = {}
    for rec in records:
        path = rec.get("path")
        status = rec.get("status")
        if not isinstance(path, str) or not path:
            raise SchemaError(f"census record missing path: {rec!r}")
        if status not in CENSUS_STATUS_TO_FROZEN and status != "renamed":
            raise SchemaError(
                f"census record status unsupported for {path!r}: {status!r} "
                "(TEST_CLASSIFICATION_AUTHORITY_MISSING)"
            )
        if status == "renamed":
            raise SchemaError(
                f"census renamed record {path!r} lacks explicit side authority "
                "(RENAMED_SIDE_AUTHORITY_MISSING; old/new sides never guessed)"
            )
        norm = canonicalize_scope_path(path, context="census-record")
        out[norm] = CENSUS_STATUS_TO_FROZEN[status]
    return out


def build_test_path_authority(
    records: list[dict[str, Any]],
    rename_sides: dict[str, tuple[str, str, bool, bool]] | None = None,
) -> dict[str, Any]:
    """Build the frozen ``TestPathAuthority`` dict from census records.

    Mirrors ``census_records_to_authority`` (materialize.py lines 583-644):
    ``changed_paths`` = COMPLETE changed-path universe; ``test_paths`` =
    paths flagged ``test_file``; ``source`` = "census".  Renamed records
    require an explicit ``rename_sides`` table or fail closed.
    """
    changed: set[str] = set()
    tests: set[str] = set()
    for rec in records:
        path = rec.get("path")
        status = rec.get("status")
        if not isinstance(path, str) or not path:
            raise SchemaError(f"census record missing path: {rec!r}")
        if status not in CENSUS_STATUS_TO_FROZEN and status != "renamed":
            raise SchemaError(
                f"census record status unsupported for {path!r}: {status!r} "
                "(TEST_CLASSIFICATION_AUTHORITY_MISSING)"
            )
        norm = canonicalize_scope_path(path, context="census-record")
        flag = bool(rec.get("test_file"))
        if status == "renamed":
            if not rename_sides or norm not in rename_sides:
                raise SchemaError(
                    f"census renamed record {norm!r} lacks explicit side authority "
                    "(RENAMED_SIDE_AUTHORITY_MISSING; old/new sides never guessed): "
                    "supply rename_sides={{path: (old, new, old_is_test, new_is_test)}}"
                )
            old, new, old_flag, new_flag = rename_sides[norm]
            for side, side_flag in ((old, old_flag), (new, new_flag)):
                changed.add(side)
                if side_flag:
                    tests.add(side)
            continue
        changed.add(norm)
        if flag:
            tests.add(norm)
    return {
        "changed_paths": sorted(changed),
        "test_paths": sorted(tests),
        "source": "census",
    }
