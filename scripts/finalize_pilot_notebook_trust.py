"""PILOT-EXEC-01 KAGGLE-AUTO-EXPANDED-MOUNT: deterministic stable-anchor freezer.

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

This script is a deterministic single-pass freezer: build once, verify the
frozen anchors against the emitted identity, write the four stable manifest
hashes, then REBUILD once to confirm invariance (the frozen values reproduce
byte-identically and the notebook is left unchanged). No hash iteration.
Idempotent: re-running against an already-frozen notebook changes nothing.
"""

from __future__ import annotations

import argparse
import ast
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

STABLE_MANIFEST_HASH_KEYS = (
    "code_manifest_sha256",
    "data_manifest_sha256",
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


def _parse_deployment(text: str) -> dict[str, Any]:
    match = re.search(r"FROZEN_DEPLOYMENT\s*=\s*\{.*?\}", text, re.DOTALL)
    if match is None:
        raise RuntimeError("FROZEN_DEPLOYMENT block not found in notebook")
    value = ast.literal_eval(match.group(0).split("=", 1)[1].strip())
    if not isinstance(value, dict) or not value:
        raise RuntimeError("FROZEN_DEPLOYMENT must be a non-empty dict literal")
    return value


def read_frozen_values(notebook_path: Path) -> dict[str, Any]:
    text = _setup_cell_text(notebook_path)

    def capture(pattern: str) -> str:
        match = re.search(pattern, text)
        if match is None:
            raise RuntimeError(f"pattern not found in notebook: {pattern!r}")
        return match.group(1)

    return {
        "FROZEN_SOURCE_TAG": capture(r'FROZEN_SOURCE_TAG = "([^"]+)"'),
        "FROZEN_DEPLOYMENT": _parse_deployment(text),
        "FROZEN_MANIFEST_HASHES": {
            key: capture(rf'"{key}": "([0-9a-fA-F]+)"') for key in STABLE_MANIFEST_HASH_KEYS
        },
    }


def write_frozen_values(
    notebook_path: Path, current: dict[str, Any], desired: dict[str, Any]
) -> None:
    """Byte-level replace of the four stable manifest hashes.

    Every value has a fixed length (64 hex chars), so the replacements leave
    all other bytes (including CRLF line endings) untouched. The notebook JSON
    stores cell source with escaped quotes, so the byte patterns use the
    backslash-quote form; hex values contain no escapes, so replacement is
    lossless. Idempotent: equal old/new values are skipped.
    """

    def esc(value: str) -> str:
        return f'\\"{value}\\"'

    raw = notebook_path.read_bytes()
    for key in STABLE_MANIFEST_HASH_KEYS:
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

    def build_and_verify() -> tuple[dict[str, Any], str]:
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
        if identity["source_tag"] != current["FROZEN_SOURCE_TAG"]:
            raise RuntimeError(
                f"notebook FROZEN_SOURCE_TAG does not match the build tag: "
                f"notebook={current['FROZEN_SOURCE_TAG']!r} build={identity['source_tag']!r}"
            )
        mismatch = [k for k, v in current["FROZEN_DEPLOYMENT"].items() if identity.get(k) != v]
        if mismatch:
            raise RuntimeError(
                "built identity does not match the notebook FROZEN_DEPLOYMENT: "
                + "; ".join(f"{k}={identity.get(k)!r}" for k in mismatch)
            )
        return identity, archive_sha

    identity, archive_sha = build_and_verify()
    desired = {
        "FROZEN_SOURCE_TAG": source_tag,
        "FROZEN_MANIFEST_HASHES": {key: identity[key] for key in STABLE_MANIFEST_HASH_KEYS},
    }

    notebook_bytes_before = notebook_path.read_bytes()
    write_frozen_values(notebook_path, current, desired)
    notebook_changed = notebook_path.read_bytes() != notebook_bytes_before

    # Rebuild invariance check: a second build from the (now) frozen notebook
    # must reproduce identical stable anchors. The archive SHA is only required
    # to be invariant when the freeze did not change the notebook (already
    # frozen, idempotent run) — a fresh freeze legitimately changes the archive
    # because the archive embeds the notebook bytes themselves.
    identity2, archive_sha2 = build_and_verify()
    for key in STABLE_MANIFEST_HASH_KEYS:
        if identity2[key] != identity[key]:
            raise RuntimeError(
                f"rebuild invariance failed for {key}: {identity[key]} != {identity2[key]}"
            )
    if not notebook_changed and archive_sha2 != archive_sha:
        raise RuntimeError(
            f"rebuild invariance failed for archive: {archive_sha} != {archive_sha2}"
        )
    archive_sha = archive_sha2

    report = {
        "status": "FROZEN",
        "source_commit": source_commit,
        "source_tag": source_tag,
        "created_utc": created_utc,
        "frozen_source_tag": current["FROZEN_SOURCE_TAG"],
        "frozen_deployment": current["FROZEN_DEPLOYMENT"],
        "frozen_manifest_hashes": {key: identity[key] for key in STABLE_MANIFEST_HASH_KEYS},
        "archive_sha256": archive_sha,
        "notebook_sha256": hashlib.sha256(
            (output_root / "notebooks" / "pilot_exec_01.ipynb").read_bytes()
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
            "recording machine."
        ),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"[freeze] FROZEN single pass + invariance OK; archive={archive_sha[:16]}... "
        f"report: {report_path}"
    )
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Deterministic single-pass freeze of the Pilot notebook stable anchors "
            "(PILOT-EXEC-01), plus one rebuild invariance check."
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
    parser.add_argument("--source-tag", type=str, default="v0.9.8-pilot-exec-ready")
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
