"""PILOT-EXEC-01: deterministic stable-anchor freezer (release trust gate).

The Pilot notebook embeds only frozen anchors that are INDEPENDENT of the
notebook bytes and of the final Git commit: ``FROZEN_SOURCE_TAG``, the
``FROZEN_DEPLOYMENT`` identity, and the four stable manifest/map hashes
(``code``, ``data``, ``repository_snapshot``, ``kaggle_transport_path_map``).

The archive SHA-256 and the notebook-manifest SHA-256 are NOT frozen: each
hashes content that includes the notebook bytes themselves, so any embedded
value would need to equal its own hash (uncomputable). They are instead
verified self-consistently at runtime (sidecar vs actual ZIP SHA in archive
mode; manifest file hash vs identity field; manifest notebook entry vs the
bundled notebook bytes). ``FROZEN_SOURCE_COMMIT`` is not embedded either; the
deployed ``source_commit`` equals the final tag peel and is recorded/verified
externally in the freeze report.

This script is the ONLY authorized bridge from stale -> frozen notebook
anchors. It performs exactly TWO builder passes:

1. a controlled DISCOVERY build with the embedded-notebook trust gate disabled
   (``validate_notebook_trust=False``) - legitimate because the notebook still
   embeds the OLD anchors while bundled code changed; the emitted identity is
   the source of truth for the new anchors;
2. writes the new ``FROZEN_SOURCE_TAG`` and the four stable manifest hashes
   into the notebook bytes (byte-level, CRLF-safe, idempotent);
3. a validation-enabled REBUILD (``validate_notebook_trust=True``) that passes
   the exact same fail-closed gate production release builds use, plus an
   invariance check confirming the stable anchors reproduce byte-identically
   and an idempotent second run changes nothing.

No hash iteration. No casual ``--skip-trust`` flag exists anywhere; the gate is
only relaxed for this internal discovery pass.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
DEFAULT_NOTEBOOK = PROJECT_ROOT / "notebooks" / "pilot_exec_01.ipynb"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "dist" / "pilot-kaggle-upload"
DEFAULT_ARCHIVE_PATH = PROJECT_ROOT / "dist" / "pilot-kaggle-upload.zip"
DEFAULT_REPO_CACHE = PROJECT_ROOT / "dist" / "pilot-repo-cache"
DEFAULT_REPORT = PROJECT_ROOT / "reports" / "pilot_notebook_trust_freeze.json"


def load_pilot_builder() -> Any:
    spec = importlib.util.spec_from_file_location(
        "build_pilot_upload_bundle_trust_freeze",
        str(SCRIPTS_DIR / "build_pilot_upload_bundle.py"),
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load build_pilot_upload_bundle.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_frozen_values(notebook_path: Path) -> dict[str, Any]:
    """Delegate to the shared notebook parsing in the Pilot bundle builder."""
    values = load_pilot_builder().read_frozen_values(notebook_path)
    if not isinstance(values, dict):
        raise RuntimeError("unexpected frozen-values type from Pilot builder")
    return values


def write_frozen_values(
    notebook_path: Path, current: dict[str, Any], desired: dict[str, Any]
) -> None:
    """Byte-level replace of the source tag and the four stable manifest hashes.

    Every hash value has a fixed length (64 hex chars), so those replacements
    leave all other bytes (including CRLF line endings) untouched. The source
    tag replacement carries its own fixed-length markers
    (``FROZEN_SOURCE_TAG = \"...\"``) so it is likewise a lossless, length-safe
    byte swap. The notebook JSON stores cell source with escaped quotes, so the
    byte patterns use the backslash-quote form; hex values contain no escapes,
    so replacement is lossless. Idempotent: equal old/new values are skipped.
    """

    def esc(value: str) -> str:
        return f'\\"{value}\\"'

    raw = notebook_path.read_bytes()

    old_tag = f"FROZEN_SOURCE_TAG = {esc(current['FROZEN_SOURCE_TAG'])}"
    new_tag = f"FROZEN_SOURCE_TAG = {esc(desired['FROZEN_SOURCE_TAG'])}"
    if old_tag != new_tag:
        if old_tag.encode("utf-8") not in raw:
            raise RuntimeError(f"FROZEN_SOURCE_TAG pattern missing from notebook: {old_tag!r}")
        raw = raw.replace(old_tag.encode("utf-8"), new_tag.encode("utf-8"))

    builder = load_pilot_builder()
    for key in builder.STABLE_MANIFEST_HASH_KEYS:
        old = f'\\"{key}\\": {esc(current["FROZEN_MANIFEST_HASHES"][key])}'
        new = f'\\"{key}\\": {esc(desired["FROZEN_MANIFEST_HASHES"][key])}'
        if old == new:
            continue
        if old.encode("utf-8") not in raw:
            raise RuntimeError(f"anchor pattern missing from notebook: {old!r}")
        raw = raw.replace(old.encode("utf-8"), new.encode("utf-8"))
    notebook_path.write_bytes(raw)


def freeze(
    notebook_path: Path,
    output_root: Path,
    archive_path: Path,
    source_commit: str,
    source_tag: str,
    created_utc: str,
    repo_cache: Path | None,
    allow_acquire: bool,
    report_path: Path,
) -> dict[str, Any]:
    if len(source_commit) != 40 or not all(c in "0123456789abcdef" for c in source_commit):
        raise ValueError(f"source_commit must be a 40-char lowercase hex SHA, got {source_commit!r}")
    builder = load_pilot_builder()
    current = read_frozen_values(notebook_path)

    def build_and_verify(*, validate: bool) -> tuple[dict[str, Any], str]:
        identity = builder.build_pilot_bundle(
            output_root=output_root,
            archive_path=archive_path,
            source_commit=source_commit,
            source_tag=source_tag,
            created_utc=created_utc,
            repo_cache=repo_cache,
            allow_acquire=allow_acquire,
            notebook=notebook_path,
            validate_notebook_trust=validate,
        )
        archive_sha = hashlib.sha256(archive_path.read_bytes()).hexdigest()
        if identity["source_commit"] != source_commit:
            raise RuntimeError(
                f"identity source_commit mismatch: identity={identity['source_commit']!r} "
                f"expected={source_commit!r}"
            )
        if identity["source_tag"] != source_tag:
            raise RuntimeError(
                f"identity source_tag mismatch: identity={identity['source_tag']!r} "
                f"expected={source_tag!r}"
            )
        return identity, archive_sha

    # Discovery build: the ONLY authorized bridge from stale -> frozen anchors.
    # The notebook legitimately still embeds the OLD anchors (bundled code
    # changed since the last freeze), so the embedded-notebook trust gate is
    # disabled for this single private pass. The emitted identity is the source
    # of truth for the new anchors.
    identity, archive_sha = build_and_verify(validate=False)
    desired = {
        "FROZEN_SOURCE_TAG": source_tag,
        "FROZEN_MANIFEST_HASHES": {
            key: identity[key] for key in builder.STABLE_MANIFEST_HASH_KEYS
        },
    }

    notebook_bytes_before = notebook_path.read_bytes()
    write_frozen_values(notebook_path, current, desired)
    notebook_changed = notebook_path.read_bytes() != notebook_bytes_before

    # Validation-enabled rebuild: must pass the exact same fail-closed gate used
    # by production release builds (stale source tag / deployment field / any of
    # the four manifest hashes all abort here). The archive SHA is only required
    # to be invariant when the freeze did not change the notebook (already
    # frozen, idempotent run) - a fresh freeze legitimately changes the archive
    # because the archive embeds the notebook bytes themselves.
    identity2, archive_sha2 = build_and_verify(validate=True)
    for key in builder.STABLE_MANIFEST_HASH_KEYS:
        if identity2[key] != identity[key]:
            raise RuntimeError(
                f"rebuild invariance failed for {key}: {identity[key]} != {identity2[key]}"
            )
    if not notebook_changed and archive_sha2 != archive_sha:
        raise RuntimeError(
            f"rebuild invariance failed for archive: {archive_sha} != {archive_sha2}"
        )
    archive_sha = archive_sha2
    final = read_frozen_values(notebook_path)

    report = {
        "status": "FROZEN",
        "source_commit": source_commit,
        "source_tag": source_tag,
        "created_utc": created_utc,
        "frozen_source_tag": final["FROZEN_SOURCE_TAG"],
        "frozen_deployment": final["FROZEN_DEPLOYMENT"],
        "frozen_manifest_hashes": {
            key: identity2[key] for key in builder.STABLE_MANIFEST_HASH_KEYS
        },
        "archive_sha256": archive_sha,
        "notebook_sha256": hashlib.sha256(
            (output_root / "notebooks" / notebook_path.name).read_bytes()
        ).hexdigest(),
        "notebook_source_sha256": hashlib.sha256(notebook_path.read_bytes()).hexdigest(),
        "output_root": str(output_root.resolve()),
        "archive_path": str(archive_path.resolve()),
        "note": (
            "source_commit must equal the final tag peel; the deployed identity "
            "source_commit is recorded here and must be re-verified after the "
            "immutable tag is created. notebook_sha256 hashes the DEPLOYED "
            "(line-ending-normalized) notebook bytes inside the artifact; "
            "notebook_source_sha256 hashes the source notebook file on this "
            "recording machine. Discovery build (validate_notebook_trust=False) "
            "+ validation-enabled rebuild (validate_notebook_trust=True) "
            "confirmed; the artifact is the validation-enabled rebuild."
        ),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"[freeze] FROZEN discovery+validation OK; archive={archive_sha[:16]}... "
        f"report: {report_path}"
    )
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Deterministic two-pass freeze of the Pilot notebook stable anchors "
            "(PILOT-EXEC-01): discovery build (trust gate off), write anchors, "
            "then validation-enabled rebuild (trust gate on) + invariance check."
        ),
    )
    parser.add_argument("--notebook", type=Path, default=DEFAULT_NOTEBOOK)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--archive-path", type=Path, default=DEFAULT_ARCHIVE_PATH)
    parser.add_argument("--repo-cache", type=Path, default=DEFAULT_REPO_CACHE)
    parser.add_argument(
        "--allow-acquire",
        action="store_true",
        default=False,
        help="Allow fetching a missing pinned commit into the repo cache.",
    )
    parser.add_argument("--source-commit", type=str, required=True)
    parser.add_argument(
        "--source-tag",
        type=str,
        required=True,
        help="Exact pre-execution stable release tag (e.g. v0.9.10-pilot-exec-ready).",
    )
    parser.add_argument("--created-utc", type=str, required=True)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    freeze(
        notebook_path=args.notebook,
        output_root=args.output_root,
        archive_path=args.archive_path,
        source_commit=args.source_commit,
        source_tag=args.source_tag,
        created_utc=args.created_utc,
        repo_cache=args.repo_cache,
        allow_acquire=args.allow_acquire,
        report_path=args.report,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
