#!/usr/bin/env python3
"""Pilot-specific deterministic deployment bundle builder (PILOT-EXEC-01).

Reuses the historical deterministic builder (``scripts/build_upload_bundle.py``)
without changing its semantics. It only redirects the output root to
``dist/pilot-kaggle-upload/`` and omits the frozen Scientific Smoke notebook.

Guarantees:

- never clears or writes ``kaggle_upload/`` (historical Smoke bundle stays
  byte-identical);
- emits ``pilot_deployment_identity.json`` carrying the frozen Pilot launch
  contract;
- archives the bundle deterministically to ``dist/pilot-kaggle-upload.zip``.

``created_utc`` is an explicit CLI input so a second build with identical
inputs is byte-identical (deterministic archive generation).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
HISTORICAL_SMOKE_UPLOAD = PROJECT_ROOT / "kaggle_upload"

DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "dist" / "pilot-kaggle-upload"
DEFAULT_ARCHIVE_PATH = PROJECT_ROOT / "dist" / "pilot-kaggle-upload.zip"

FROZEN_SOURCE_TAG = "v0.9.1-pilot-exec-ready"
FROZEN_TASK = "PILOT-EXEC-01"
FROZEN_PROTOCOL_VERSION = "1.0"
FROZEN_MODEL_NAME = "Qwen/Qwen2.5-Coder-14B-Instruct"
FROZEN_QUANTIZATION = "bnb-nf4"
FROZEN_TIMEOUT_SECONDS = 600
FROZEN_MAX_ATTEMPTS = 3
FROZEN_MAX_COMPLETION_TOKENS = 4096
FROZEN_MAX_TOTAL_WORKFLOW_TOKENS = 0
FROZEN_SCENARIO_COUNT = 12
FROZEN_STRATEGY_COUNT = 2
FROZEN_REPETITIONS = 2
FROZEN_EXPECTED_CELLS = 48


def _load_historical_builder() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "build_upload_bundle_pilot_reused",
        SCRIPTS_DIR / "build_upload_bundle.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load scripts/build_upload_bundle.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _redirect_builder(builder: Any, output_root: Path) -> None:
    """Redirect the reused builder's output constants to the Pilot root only."""
    builder.KAGGLE_UPLOAD = output_root
    builder.KAGGLE_CODE = output_root / "code"
    builder.KAGGLE_DATA = output_root / "data"
    builder.KAGGLE_NOTEBOOKS = output_root / "notebooks"
    builder.CANONICAL_NOTEBOOK_SOURCES = []


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_head_sha() -> str:
    import subprocess

    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git rev-parse HEAD failed: {result.stderr.strip()}")
    sha = result.stdout.strip()
    if len(sha) != 40:
        raise RuntimeError(f"unexpected git HEAD: {sha!r}")
    return sha


def build_identity(
    output_root: Path,
    source_commit: str,
    source_tag: str,
    created_utc: str,
) -> dict[str, Any]:
    code_manifest = output_root / "code_manifest.json"
    data_manifest = output_root / "data_manifest.json"
    for path, label in ((code_manifest, "code_manifest"), (data_manifest, "data_manifest")):
        if not path.is_file():
            raise RuntimeError(f"{label} manifest missing: {path}")
    return {
        "task": FROZEN_TASK,
        "protocol_version": FROZEN_PROTOCOL_VERSION,
        "source_commit": source_commit,
        "source_tag": source_tag,
        "model_name": FROZEN_MODEL_NAME,
        "quantization": FROZEN_QUANTIZATION,
        "timeout_seconds": FROZEN_TIMEOUT_SECONDS,
        "max_attempts": FROZEN_MAX_ATTEMPTS,
        "max_completion_tokens_per_call": FROZEN_MAX_COMPLETION_TOKENS,
        "max_total_workflow_tokens": FROZEN_MAX_TOTAL_WORKFLOW_TOKENS,
        "scenario_count": FROZEN_SCENARIO_COUNT,
        "strategy_count": FROZEN_STRATEGY_COUNT,
        "repetitions": FROZEN_REPETITIONS,
        "expected_cells": FROZEN_EXPECTED_CELLS,
        "created_utc": created_utc,
        "code_manifest_sha256": _sha256_bytes(code_manifest.read_bytes()),
        "data_manifest_sha256": _sha256_bytes(data_manifest.read_bytes()),
    }


def write_identity(output_root: Path, identity: dict[str, Any]) -> None:
    target = output_root / "pilot_deployment_identity.json"
    target.write_text(
        json.dumps(identity, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def create_deterministic_zip(bundle_root: Path, archive_path: Path, created_utc: str) -> str:
    import zipfile

    dt = datetime.fromisoformat(created_utc)
    date_time = (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    files = sorted(
        p.relative_to(bundle_root).as_posix()
        for p in bundle_root.rglob("*")
        if p.is_file()
    )
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel in files:
            info = zipfile.ZipInfo(rel, date_time=date_time)
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, (bundle_root / rel).read_bytes())
    archive_sha = _sha256_bytes(archive_path.read_bytes())
    archive_path.with_name(archive_path.name + ".sha256").write_text(
        archive_sha + "\n", encoding="utf-8", newline="\n"
    )
    return archive_sha


def build_pilot_bundle(
    output_root: Path,
    archive_path: Path,
    source_commit: str,
    source_tag: str,
    created_utc: str,
) -> dict[str, Any]:
    if output_root.resolve() == HISTORICAL_SMOKE_UPLOAD.resolve():
        raise RuntimeError("refusing to build the Pilot bundle over the historical Smoke bundle")
    builder = _load_historical_builder()
    _redirect_builder(builder, output_root)
    errors = builder.build_bundle()
    if errors:
        raise RuntimeError(f"reused bundle builder reported {errors} verification error(s)")
    identity = build_identity(output_root, source_commit, source_tag, created_utc)
    write_identity(output_root, identity)
    archive_sha = create_deterministic_zip(output_root, archive_path, created_utc)
    print(f"Pilot deployment identity: {output_root / 'pilot_deployment_identity.json'}")
    print(f"Pilot archive: {archive_path}")
    print(f"Pilot archive SHA-256: {archive_sha}")
    return identity


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the deterministic Pilot Kaggle deployment bundle (PILOT-EXEC-01).",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help=f"Pilot bundle output root (default: {DEFAULT_OUTPUT_ROOT})",
    )
    parser.add_argument(
        "--archive-path",
        type=Path,
        default=DEFAULT_ARCHIVE_PATH,
        help=f"Deterministic archive path (default: {DEFAULT_ARCHIVE_PATH})",
    )
    parser.add_argument(
        "--source-commit",
        type=str,
        default=None,
        help="Exact 40-char Git SHA for the deployment identity (default: git HEAD).",
    )
    parser.add_argument(
        "--source-tag",
        type=str,
        default=FROZEN_SOURCE_TAG,
        help=f"Pre-execution stable tag (default: {FROZEN_SOURCE_TAG}).",
    )
    parser.add_argument(
        "--created-utc",
        type=str,
        default=None,
        help="Explicit ISO-8601 UTC creation timestamp (deterministic builds).",
    )
    args = parser.parse_args()
    if args.source_commit is None:
        args.source_commit = _git_head_sha()
    if args.created_utc is None:
        args.created_utc = datetime.now().astimezone().isoformat()
    return args


def main() -> int:
    args = parse_args()
    build_pilot_bundle(
        output_root=args.output_root,
        archive_path=args.archive_path,
        source_commit=args.source_commit,
        source_tag=args.source_tag,
        created_utc=args.created_utc,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
