#!/usr/bin/env python3
"""T12 M02-D2 — RD-8: reference-patch ``--classification-json`` provenance
(OFFLINE, read-only git + frozen census, stdlib only).

Mission: T12_M02_D2_INPUT_CONTRACT_20261027 (Track 1.2), Task 2.

QUESTION
--------
Can the materializer's required ``{"changes": {path: status}}`` classification
(parser lines 1156-1158; ``FROZEN_STATUSES`` line 427; COMPLETE change set
enforced by ``_authority_for_classification``) be deterministically derived
from the ALREADY-FROZEN parent->target reference diff under the ORIGINAL
scientific protocol — without inventing any label?

ANSWER (this module, evidence in receipts)
------------------------------------------
YES, deterministically and reproducibly:

1. The frozen protocol's OWN status classifier is ``git diff --name-status -z
   --no-renames`` producing exactly ``M``/``D``/``A`` (R1 §3 statuses;
   materialize.py ``git_name_status_map`` lines 337-380; ``DIFF_FLAGS`` lines
   100-107).  Rename becomes ``D(old)+A(new)`` — the complete physical change
   set, no similarity heuristics; ``R_OLD``/``R_NEW`` exist only in explicit
   task classifications.  Binary/symlink/submodule content is FAIL-CLOSED at
   materialize time by ``verify_path_supported`` (lines 666-706) — the input
   contract records per-path side evidence, it does not guess.

2. The frozen census per-task ``changed_paths`` records (status per path,
   ``test_file`` flag, 2026-09-22) are the frozen test-path AUTHORITY
   (materialize.py ``census_records_to_authority`` lines 583-644); they
   reproduce the same M/D/A statuses via ``CENSUS_STATUS_TO_FROZEN`` and name
   the common-behavior `test_paths` — never by filename heuristics.

3. Cross-check: git-derived map MUST equal census-derived map (same path set
   and statuses), else fail closed (policy: the change-set classification is
   the materializer's COMPLETE change set; two independent frozen authorities
   must agree).

STATUS: PROPOSED_NEW_DERIVATION_PENDING_RESEARCHER_RD8_APPROVAL.  The derived
artifacts are NOT historically frozen (no frozen per-arm classification JSON
shipped with the R7 kit or the frozen plan); they are a NEW, byte-pinned,
reproducible derivation for researcher RD-8 approval.  No eligibility,
label or scientific claim is invented.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

_SCRIPTS = Path(__file__).resolve().parent
_schema_spec = importlib.util.spec_from_file_location(
    "t12_m02_materializer_schema", _SCRIPTS / "t12_m02_materializer_schema.py")
assert _schema_spec is not None and _schema_spec.loader is not None
_schema_mod = importlib.util.module_from_spec(_schema_spec)
_schema_spec.loader.exec_module(_schema_mod)
FROZEN_STATUSES = _schema_mod.FROZEN_STATUSES
build_test_path_authority = _schema_mod.build_test_path_authority
canonical_scope_hash = _schema_mod.canonical_scope_hash
census_changes_map = _schema_mod.census_changes_map
git_name_status_map = _schema_mod.git_name_status_map
sha256_file = _schema_mod.sha256_file

SCHEMA = "t12_m02_classification_provenance_receipt_v1"
RULE_VERSION = "t12_m02_classification_derivation_v1"
DERIVATION_STATUS = "PROPOSED_NEW_DERIVATION_PENDING_RESEARCHER_RD8_APPROVAL"


class ClassificationError(Exception):
    """Fail-closed classification derivation problem (typed)."""


def cross_check(git_map: dict[str, str],
                census_map: dict[str, str]) -> dict[str, Any]:
    """Exact equality check of the two independent frozen authorities."""
    diff = {
        "only_in_git": sorted(set(git_map) - set(census_map)),
        "only_in_census": sorted(set(census_map) - set(git_map)),
        "status_mismatch": {
            p: {"git": git_map[p], "census": census_map[p]}
            for p in sorted(set(git_map) & set(census_map))
            if git_map[p] != census_map[p]
        },
    }
    equal = not any(diff.values())
    return {"equal": equal, "diff": diff}


def pick_supported_sides(repo: Path, target: str, parent: str,
                         paths: list[str]) -> dict[str, dict[str, str]]:
    """Per-path side evidence (modes) for the derived classification.

    Read-only git ``ls-tree``/``cat-file`` calls — fails closed (typed
    reason) on symlink/submodule/unsupported modes and on binary (NUL)
    content, mirroring the materializer's ``verify_path_supported``.  This is
    the input-contract's evidence record; the materializer re-enforces the
    same checks at materialize time.
    """
    import subprocess

    evidence: dict[str, dict[str, str]] = {}
    for path in paths:
        sides: dict[str, str] = {}
        for label, ref in (("parent", parent), ("target", target)):
            r = subprocess.run(["git", "-C", str(repo), "ls-tree", "-z", ref, "--", path],
                               capture_output=True, check=False)
            if r.returncode != 0:
                raise ClassificationError(f"GIT_LS_TREE_FAILED: {path}")
            entry = r.stdout.split(b"\x00", 1)[0].decode("utf-8", "replace")
            if not entry:
                sides[label] = "MISSING"
                continue
            mode = entry.split(" ", 1)[0]
            sides[label] = mode
            if mode in ("120000", "160000") or mode not in ("100644", "100755"):
                raise ClassificationError(
                    f"UNSUPPORTED_MODE: {path} {label} mode={mode} (fail closed; "
                    "extraction never guesses binary/symlink handling)"
                )
            blob = subprocess.run(["git", "-C", str(repo), "cat-file", "blob", f"{ref}:{path}"],
                                  capture_output=True, check=False)
            if blob.returncode != 0:
                raise ClassificationError(f"GIT_CAT_FILE_FAILED: {path}")
            if b"\x00" in blob.stdout:
                raise ClassificationError(
                    f"BINARY_CONTENT: {path} {label} (NUL byte; fail closed; "
                    "binary diff handling is never guessed by the input contract)"
                )
        evidence[path] = sides
    return evidence


def build_classification_artifacts(
    *,
    repo: Path,
    parent: str,
    target: str,
    census_records: list[dict[str, Any]],
    task_id: str,
    out_dir: Path,
) -> dict[str, Any]:
    """Derive + write the classification and test-authority JSON artifacts.

    Writes (byte-pinned, canonical JSON files):
      classification_<task>.json {"changes": {path: status}}
      test_authority_<task>.json {"changed_paths", "test_paths", "source"}
    Returns the receipt dict (never silently drops anything).
    """
    git_map = git_name_status_map(repo, parent, target)
    census_map = census_changes_map(census_records)
    authority = build_test_path_authority(census_records)

    xcheck = cross_check(git_map, census_map)
    if not xcheck["equal"]:
        raise ClassificationError(
            f"CROSS_CHECK_FAILED: git name-status != census classification "
            f"({xcheck['diff']!r}) — refusing to derive on a non-identical change set"
        )

    changed = sorted(git_map)
    census_meta = [r for r in census_records if isinstance(r, dict)]
    extras = pick_supported_sides(repo, target, parent, changed)

    classification = {"changes": dict(sorted(git_map.items()))}
    classification_file = out_dir / f"classification_{task_id}.json"
    authority_file = out_dir / f"test_authority_{task_id}.json"

    def _write(p: Path, payload: Any) -> str:
        p.write_text(json.dumps(payload, sort_keys=True, ensure_ascii=False) + "\n",
                     encoding="utf-8")
        return str(sha256_file(p))

    cls_sha = _write(classification_file, classification)
    auth_sha = _write(authority_file, authority)
    scope_like = sorted(git_map)

    receipt: dict[str, Any] = {
        "schema": SCHEMA,
        "rule_version": RULE_VERSION,
        "task_id": task_id,
        "derivation_status": DERIVATION_STATUS,
        "source_parent_commit": parent,
        "source_target_commit": target,
        "census_source": "research/wp2/wp2_saleor_main297_census_2026-09-22.json",
        "census_records_count": len(census_meta),
        "census_changed_paths_count": len(authority["changed_paths"]),
        "census_test_paths_count": len(authority["test_paths"]),
        "git_statuses": sorted({s for s in git_map.values()}),
        "changed_path_count": len(changed),
        "cross_check": xcheck,
        "per_path_side_evidence": extras,
        "unknown_statuses_encountered": [],
        "renamed_pairs": [],
        "test_authority": authority,
        "classification_artifact": str(classification_file),
        "classification_sha256": cls_sha,
        "classification_changes_count": len(classification["changes"]),
        "test_authority_artifact": str(authority_file),
        "test_authority_sha256": auth_sha,
        "scope_like_changes_hash": canonical_scope_hash(scope_like),
        "classification_parser_note": (
            "frozen parser: classification-json must be {\"changes\": {path: status}} "
            "with status in " + ", ".join(FROZEN_STATUSES) + "; COMPLETE change set "
            "== test-authority.changed_paths; test membership ONLY from the census"
        ),
        "frozen": False,
        "label": DERIVATION_STATUS,
        "label_reason": (
            "derived offline from the already-frozen parent->target reference diff "
            "under the ORIGINAL scientific protocol (git name-status M/D/A, no-renames) "
            "cross-checked against the frozen per-task census; NO historically frozen "
            "per-arm classification JSON exists (verified 2026-10-27); researcher "
            "approval under RD-8 is required before any M02-E admission"
        ),
    }
    (out_dir / f"classification_{task_id}.receipt.json").write_text(
        json.dumps(receipt, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return receipt


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="t12_m02_classification_provenance",
        description="Offline RD-8 classification derivation from the frozen "
                    "parent->target reference diff + census (writes artifacts).")
    ap.add_argument("--repo", required=True, help="read-only saleor git cache path")
    ap.add_argument("--parent", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--census", required=True, help="frozen census JSON path")
    ap.add_argument("--task-id", required=True)
    ap.add_argument("--out", required=True, help="output directory")
    args = ap.parse_args(argv)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    census_data = json.loads(Path(args.census).read_text(encoding="utf-8"))
    census_records = next(
        (r.get("changed_paths") for r in census_data.get("tasks", [])
         if isinstance(r, dict) and r.get("task_id") == args.task_id), None)
    if census_records is None:
        print(f"STOP:CENSUS_TASK_MISSING: {args.task_id}", file=sys.stderr)
        return 3
    parent_oid = subprocess_check_oid(Path(args.repo), args.parent)
    target_oid = subprocess_check_oid(Path(args.repo), args.target)
    receipt = build_classification_artifacts(
        repo=Path(args.repo), parent=parent_oid, target=target_oid,
        census_records=census_records, task_id=args.task_id, out_dir=out)
    print(json.dumps({k: v for k, v in receipt.items() if k != "test_authority"},
                     sort_keys=True, ensure_ascii=False, default=str))
    return 0


def subprocess_check_oid(repo: Path, oid: str) -> str:
    import subprocess

    r = subprocess.run(["git", "-C", str(repo), "rev-parse", f"{oid}^{{commit}}"],
                       capture_output=True, text=True, check=False)
    if r.returncode != 0:
        raise ClassificationError(f"OID_UNRESOLVED: {oid}")
    full = r.stdout.strip()
    if len(full) != 40:
        raise ClassificationError(f"OID_NOT_FULL_40_HEX: {oid}")
    return full


if __name__ == "__main__":
    sys.exit(main())
