"""PILOT-EXEC-01 KAGGLE-AUTO-EXPANDED-MOUNT: converge and freeze trust anchors.

The Pilot notebook embeds frozen trust anchors that are self-referential: the
archive SHA-256 hashes the deterministic ZIP (which contains the notebook), and
``notebook_manifest_sha256`` hashes the manifest (which hashes the notebook
bytes). ``FROZEN_SOURCE_COMMIT`` is the implementation commit that precedes the
freeze commit, so it is supplied explicitly and never derived.

This script iterates the deterministic bundle build until the notebook's frozen
values reproduce themselves (the fixpoint), leaving ``notebooks/pilot_exec_01.ipynb``
with the converged constants. The developer then commits the notebook as the
freeze commit, tags it, and rebuilds once from the tag to emit the exact
artifact whose identity matches the frozen anchors.

Idempotent: a run against an already-finalized notebook converges on the first
build and leaves every input byte-identical.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
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

MANIFEST_HASH_KEYS = (
    "code_manifest_sha256",
    "data_manifest_sha256",
    "notebook_manifest_sha256",
    "repository_snapshot_manifest_sha256",
    "kaggle_transport_path_map_sha256",
)


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


def _setup_cell_text(notebook_path: Path) -> str:
    nb = json.loads(notebook_path.read_text(encoding="utf-8"))
    cells = [c for c in nb["cells"] if c.get("id") == "setup-cell"]
    if len(cells) != 1:
        raise RuntimeError("expected exactly one 'setup-cell' in the Pilot notebook")
    src = cells[0]["source"]
    return src if isinstance(src, str) else "".join(src)


def read_frozen_values(notebook_path: Path) -> dict[str, Any]:
    text = _setup_cell_text(notebook_path)

    def capture(pattern: str) -> str:
        match = re.search(pattern, text)
        if match is None:
            raise RuntimeError(f"pattern not found in notebook: {pattern!r}")
        return match.group(1)

    return {
        "FROZEN_ARCHIVE_SHA": capture(r'FROZEN_ARCHIVE_SHA = "([0-9a-fA-F]+)"'),
        "FROZEN_SOURCE_COMMIT": capture(r'FROZEN_SOURCE_COMMIT = "([0-9a-fA-F]+)"'),
        "FROZEN_SOURCE_TAG": capture(r'FROZEN_SOURCE_TAG = "([^"]+)"'),
        "FROZEN_MANIFEST_HASHES": {
            key: capture(rf'"{key}": "([0-9a-fA-F]+)"') for key in MANIFEST_HASH_KEYS
        },
    }


def write_frozen_values(
    notebook_path: Path, current: dict[str, Any], desired: dict[str, Any]
) -> None:
    """Byte-level replace of the frozen anchor values.

    Every anchor value has a fixed length (64-hex archive/manifest hashes,
    40-hex source commit, tag string), so the replacements leave all other
    bytes (including CRLF line endings) untouched. The notebook JSON stores cell
    source with escaped quotes, so the byte patterns use the backslash-quote
    form; hex/tag values contain no escapes, so replacement is lossless.
    """

    def esc(value: str) -> str:
        return f'\\"{value}\\"'

    raw = notebook_path.read_bytes()
    replaces = [
        (
            f'FROZEN_ARCHIVE_SHA = {esc(current["FROZEN_ARCHIVE_SHA"])}',
            f'FROZEN_ARCHIVE_SHA = {esc(desired["FROZEN_ARCHIVE_SHA"])}',
        ),
        (
            f'FROZEN_SOURCE_COMMIT = {esc(current["FROZEN_SOURCE_COMMIT"])}',
            f'FROZEN_SOURCE_COMMIT = {esc(desired["FROZEN_SOURCE_COMMIT"])}',
        ),
        (
            f'FROZEN_SOURCE_TAG = {esc(current["FROZEN_SOURCE_TAG"])}',
            f'FROZEN_SOURCE_TAG = {esc(desired["FROZEN_SOURCE_TAG"])}',
        ),
    ]
    for key in MANIFEST_HASH_KEYS:
        replaces.append(
            (
                f'\\"{key}\\": {esc(current["FROZEN_MANIFEST_HASHES"][key])}',
                f'\\"{key}\\": {esc(desired["FROZEN_MANIFEST_HASHES"][key])}',
            )
        )
    for old, new in replaces:
        if old == new:
            continue
        if old.encode("utf-8") not in raw:
            raise RuntimeError(f"anchor pattern missing from notebook: {old!r}")
        raw = raw.replace(old.encode("utf-8"), new.encode("utf-8"))
    notebook_path.write_bytes(raw)


def converge(
    notebook_path: Path,
    output_root: Path,
    archive_path: Path,
    source_commit: str,
    source_tag: str,
    created_utc: str,
    repo_cache: Path | None,
    allow_acquire: bool,
    max_iterations: int,
    report_path: Path,
) -> dict[str, Any]:
    if len(source_commit) != 40 or not all(c in "0123456789abcdef" for c in source_commit):
        raise ValueError(f"source_commit must be a 40-char lowercase hex SHA, got {source_commit!r}")
    builder = load_pilot_builder()
    current = read_frozen_values(notebook_path)
    history: list[dict[str, Any]] = []
    archive_sha = ""
    for iteration in range(max_iterations + 1):
        identity = builder.build_pilot_bundle(
            output_root=output_root,
            archive_path=archive_path,
            source_commit=source_commit,
            source_tag=source_tag,
            created_utc=created_utc,
            repo_cache=repo_cache,
            allow_acquire=allow_acquire,
        )
        archive_sha = hashlib.sha256(archive_path.read_bytes()).hexdigest()
        desired = {
            "FROZEN_ARCHIVE_SHA": archive_sha,
            "FROZEN_SOURCE_COMMIT": source_commit,
            "FROZEN_SOURCE_TAG": source_tag,
            "FROZEN_MANIFEST_HASHES": {
                key: identity[key] for key in MANIFEST_HASH_KEYS
            },
        }
        changed = desired != current
        history.append(
            {
                "iteration": iteration,
                "archive_sha256": archive_sha,
                "notebook_manifest_sha256": identity["notebook_manifest_sha256"],
                "changed": changed,
            }
        )
        print(
            f"[freeze] iteration {iteration}: archive={archive_sha[:16]}... "
            f"notebook_manifest={identity['notebook_manifest_sha256'][:16]}... "
            f"changed={changed}"
        )
        if not changed:
            break
        write_frozen_values(notebook_path, current, desired)
        current = desired
    else:
        raise RuntimeError(
            f"frozen trust anchors failed to converge within {max_iterations} iterations"
        )

    report = {
        "status": "CONVERGED",
        "iterations": history,
        "source_commit": source_commit,
        "source_tag": source_tag,
        "created_utc": created_utc,
        "frozen_archive_sha256": current["FROZEN_ARCHIVE_SHA"],
        "frozen_source_commit": current["FROZEN_SOURCE_COMMIT"],
        "frozen_source_tag": current["FROZEN_SOURCE_TAG"],
        "frozen_manifest_hashes": current["FROZEN_MANIFEST_HASHES"],
        "notebook_sha256": hashlib.sha256(notebook_path.read_bytes()).hexdigest(),
        "output_root": str(output_root.resolve()),
        "archive_path": str(archive_path.resolve()),
        "archive_sha256": archive_sha,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"[freeze] CONVERGED after {len(history)} iteration(s); report: {report_path}")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Converge and freeze the Pilot notebook trust anchors (PILOT-EXEC-01).",
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
    parser.add_argument("--source-tag", type=str, default="v0.9.6-pilot-exec-ready")
    parser.add_argument("--created-utc", type=str, required=True)
    parser.add_argument("--max-iterations", type=int, default=8)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    converge(
        notebook_path=args.notebook,
        output_root=args.output_root,
        archive_path=args.archive_path,
        source_commit=args.source_commit,
        source_tag=args.source_tag,
        created_utc=args.created_utc,
        repo_cache=args.repo_cache,
        allow_acquire=args.allow_acquire,
        max_iterations=args.max_iterations,
        report_path=args.report,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
