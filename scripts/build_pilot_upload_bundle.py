#!/usr/bin/env python3
"""Pilot-specific deterministic deployment bundle builder (PILOT-EXEC-01).

Reuses the historical deterministic builder (``scripts/build_upload_bundle.py``)
without changing its semantics. It only redirects the output root to
``dist/pilot-kaggle-upload/`` and omits the frozen Scientific Smoke notebook.

Guarantees:

- never clears or writes ``kaggle_upload/`` (historical Smoke bundle stays
  byte-identical);
- includes the canonical Pilot notebook ``notebooks/pilot_exec_01.ipynb`` and a
  non-empty, hash-verifiable ``notebook_manifest.json``;
- materializes ALL THREE pinned repository source trees
  (``data/repositories/{todo,djangocms,saleor}``) at their exact immutable
  commits, failing closed on any identity mismatch and recording per-repository
  snapshot evidence;
- emits ``pilot_deployment_identity.json`` carrying the frozen Pilot launch
  contract;
- archives the bundle deterministically to ``dist/pilot-kaggle-upload.zip``.

``created_utc`` is an explicit CLI input so a second build with identical
inputs is byte-identical (deterministic archive generation). ``--repo-cache``
points at a reusable local acquisition cache of git checkouts for the external
pinned repositories (django CMS, Saleor).
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import re
import shutil
import sys
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
HISTORICAL_SMOKE_UPLOAD = PROJECT_ROOT / "kaggle_upload"

DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "dist" / "pilot-kaggle-upload"
DEFAULT_ARCHIVE_PATH = PROJECT_ROOT / "dist" / "pilot-kaggle-upload.zip"
DEFAULT_REPO_CACHE = PROJECT_ROOT / "dist" / "pilot-repo-cache"

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

PILOT_NOTEBOOK = PROJECT_ROOT / "notebooks" / "pilot_exec_01.ipynb"
PILOT_RUNTIME_LOCK = PROJECT_ROOT / "requirements-pilot-kaggle.lock"

PILOT_SNAPSHOT_SCRIPT = SCRIPTS_DIR / "pilot_repo_snapshot.py"
PILOT_ENVS_SCRIPT = SCRIPTS_DIR / "pilot_kaggle_repo_envs.py"

# ---- Kaggle transport-safe archive member encoding -------------------------
#
# Kaggle rejects upload archive members whose names fall outside
# ``[A-Za-z0-9._/-]`` (observed: ``[``, ``]``, ``&``, ``@``, ``=`` in exact
# upstream repository filenames) and reserves any path component matching the
# ``__name__`` pattern (``^__.*__$``; the old ``__kaggle_transport__`` root was
# rejected by Kaggle for exactly this reason). The canonical execution tree on
# disk is never renamed: unsafe members are transported inside the ZIP under
# deterministic hashed blob names plus a root-level path map, and the Pilot
# notebook restores the exact original paths BEFORE any manifest / snapshot
# verification. A mandatory pre-upload archive validator scans EVERY ZIP member
# and fails closed on any unsafe-special-char or reserved-name component.
KAGGLE_SAFE_COMPONENT_RE = re.compile(r"^[A-Za-z0-9._-]+$")
KAGGLE_RESERVED_NAME_RE = re.compile(r"^__.*__$")
TRANSPORT_BLOB_PREFIX = "kaggle_transport"
TRANSPORT_FILES_DIR = f"{TRANSPORT_BLOB_PREFIX}/files"
TRANSPORT_MAP_NAME = "kaggle_transport_path_map.json"

# Stable manifest/map hashes the Pilot notebook freezes in its setup cell.
# These are INDEPENDENT of the notebook bytes (unlike the archive SHA and the
# notebook-manifest SHA), so the bundled notebook can be trusted against the
# deployment identity at build time and verified against the mounted tree at
# runtime. Shared with the deterministic freezer
# (scripts/finalize_pilot_notebook_trust.py) so the builder gate and the
# freezer parse the exact same anchors.
STABLE_MANIFEST_HASH_KEYS = (
    "code_manifest_sha256",
    "data_manifest_sha256",
    "repository_snapshot_manifest_sha256",
    "kaggle_transport_path_map_sha256",
)


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


def validate_bundled_notebook_trust(identity: dict[str, Any], bundled_notebook: Path) -> list[str]:
    """Fail-closed comparison of the bundled notebook trust anchors vs identity.

    Returns every mismatch as a human-readable message; an empty list means the
    artifact is upload-ready. The bundled notebook is parsed from the exact
    bytes the archive will carry (setup cell), so a stale embedded anchor can
    never survive a release build.
    """
    frozen = read_frozen_values(bundled_notebook)
    mismatches: list[str] = []
    if frozen["FROZEN_SOURCE_TAG"] != identity["source_tag"]:
        mismatches.append(
            f"FROZEN_SOURCE_TAG={frozen['FROZEN_SOURCE_TAG']!r} "
            f"!= identity source_tag={identity['source_tag']!r}"
        )
    for key, value in frozen["FROZEN_DEPLOYMENT"].items():
        if identity.get(key) != value:
            mismatches.append(
                f"FROZEN_DEPLOYMENT[{key}]={value!r} != identity={identity.get(key)!r}"
            )
    for key in STABLE_MANIFEST_HASH_KEYS:
        frozen_hash = frozen["FROZEN_MANIFEST_HASHES"][key]
        if frozen_hash != identity[key]:
            mismatches.append(
                f"FROZEN_MANIFEST_HASHES[{key}]={frozen_hash} != identity={identity[key]}"
            )
    return mismatches


def is_kaggle_safe_name(rel_path: str) -> bool:
    """True when every path component is Kaggle-safe.

    A member is Kaggle-safe only when each component stays inside the
    ``[A-Za-z0-9._-]`` charset AND no component matches the reserved
    ``__name__`` pattern (``^__.*__$``).
    """
    if not rel_path:
        return False
    return all(
        KAGGLE_SAFE_COMPONENT_RE.match(comp) is not None
        and KAGGLE_RESERVED_NAME_RE.match(comp) is None
        for comp in rel_path.split("/")
    )


def kaggle_unsafe_members(members: Iterable[str]) -> tuple[list[str], list[str]]:
    """Classify archive members as (unsafe-charset, reserved-name) offenders."""
    unsafe_chars: list[str] = []
    reserved_names: list[str] = []
    for member in members:
        if not member:
            unsafe_chars.append(member)
            continue
        for comp in member.split("/"):
            if not KAGGLE_SAFE_COMPONENT_RE.match(comp):
                unsafe_chars.append(member)
                break
            if KAGGLE_RESERVED_NAME_RE.match(comp):
                reserved_names.append(member)
                break
    return unsafe_chars, reserved_names


def validate_archive_members_kaggle_ready(members: Iterable[str]) -> tuple[int, int]:
    """Mandatory pre-upload archive validator (fail closed).

    Rejects the artifact if ANY ZIP member has a path component with
    characters outside ``[A-Za-z0-9._-]`` or a component matching the
    reserved ``^__.*__$`` pattern. Returns
    ``(unsafe_special_char_count, reserved_name_count)``, which is always
    ``(0, 0)`` when the artifact is Kaggle-ready.
    """
    scanned = list(members)
    unsafe_chars, reserved_names = kaggle_unsafe_members(scanned)
    if unsafe_chars or reserved_names:
        raise RuntimeError(
            "KAGGLE PRE-UPLOAD VALIDATION FAILED - archive is NOT Kaggle-ready "
            f"({len(scanned)} members scanned): "
            f"unsafe-special-char members={unsafe_chars!r}; "
            f"reserved-name components={reserved_names!r}"
        )
    return len(unsafe_chars), len(reserved_names)


def transport_blob_name(rel_path: str) -> str:
    """Deterministic safe blob member name for one original archive member."""
    return f"{TRANSPORT_FILES_DIR}/{_sha256_bytes(rel_path.encode('utf-8'))}.blob"


def build_transport_path_map(bundle_root: Path) -> dict[str, str]:
    """Deterministic mapping of ``blob -> original path`` for unsafe members.

    Safe members are never mapped. Fails closed on any transport-name
    collision or on a canonical member that collides with the transport
    namespace.
    """
    files = sorted(
        p.relative_to(bundle_root).as_posix()
        for p in bundle_root.rglob("*")
        if p.is_file() and p.name != TRANSPORT_MAP_NAME
    )
    for rel in files:
        if rel.startswith(f"{TRANSPORT_BLOB_PREFIX}/") or rel == TRANSPORT_BLOB_PREFIX:
            raise RuntimeError(
                f"canonical member collides with the reserved transport namespace: {rel}"
            )
    mapping: dict[str, str] = {}
    seen_blobs: set[str] = set()
    for rel in files:
        if is_kaggle_safe_name(rel):
            continue
        blob = transport_blob_name(rel)
        if blob in seen_blobs or blob in files:
            raise RuntimeError(f"transport blob collision for member: {rel}")
        seen_blobs.add(blob)
        mapping[blob] = rel
    return mapping


def write_transport_path_map(bundle_root: Path, mapping: dict[str, str]) -> str:
    """Emit the root-level transport path map and return its SHA-256."""
    target = bundle_root / TRANSPORT_MAP_NAME
    target.write_text(
        json.dumps(mapping, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return _sha256_bytes(target.read_bytes())


def _load_pilot_repo_snapshot() -> ModuleType:
    """Load ``scripts/pilot_repo_snapshot.py`` as an explicit local module.

    The deployment tests load this builder with
    ``importlib.util.spec_from_file_location``, which never guarantees
    ``scripts/`` on ``sys.path``. A sibling top-level import therefore fails
    collection with ``ModuleNotFoundError``; explicit file-based loading keeps
    both direct script execution and dynamic test loading valid. The loaded
    module is cached so tests can deterministically patch its behavior.
    """
    module_name = "pilot_repo_snapshot_bundled"
    cached = sys.modules.get(module_name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(
        module_name,
        PILOT_SNAPSHOT_SCRIPT,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load scripts/pilot_repo_snapshot.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


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


def _redirect_builder(builder: Any, output_root: Path, notebook: Path) -> None:
    """Redirect the reused builder's output constants to the Pilot root only.

    The Pilot builder may bundle a notebook that lives outside ``PROJECT_ROOT``
    (a frozen temp copy produced by the finalizer). The reused historical
    builder verifies flat notebook sources with ``src.relative_to(base_rel)``,
    which crashes for out-of-tree sources; the flat (basename-only) notebook
    comparison does not need the relative path, so the verification is wrapped
    to fall back to the bare filename in that case.
    """
    builder.KAGGLE_UPLOAD = output_root
    builder.KAGGLE_CODE = output_root / "code"
    builder.KAGGLE_DATA = output_root / "data"
    builder.KAGGLE_NOTEBOOKS = output_root / "notebooks"
    if not notebook.is_file():
        raise RuntimeError(f"Pilot notebook missing: {notebook}")
    builder.CANONICAL_NOTEBOOK_SOURCES = [notebook]
    original_verify = builder.verify_bundle

    def _verify_flat_notebook(
        canonical: list[Path],
        bundle_base: Path,
        base_rel: Path | None = None,
        flat: bool = False,
    ) -> int:
        if not flat:
            return int(original_verify(canonical, bundle_base, base_rel))
        errors = 0
        for src in canonical:
            try:
                rel = src.relative_to(
                    builder.PROJECT_ROOT if base_rel is None else base_rel
                )
            except ValueError:
                rel = Path(src.name)
            bundle_path = bundle_base / src.name
            if src.is_file():
                if not bundle_path.exists():
                    print(f"  MISSING: {bundle_path}")
                    errors += 1
                elif builder.normalized_sha256(src) != builder.normalized_sha256(bundle_path):
                    print(f"  MISMATCH: {rel}")
                    errors += 1
        return errors

    builder.verify_bundle = _verify_flat_notebook


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
    notebook_manifest = output_root / "notebook_manifest.json"
    transport_map = output_root / TRANSPORT_MAP_NAME
    for path, label in (
        (code_manifest, "code_manifest"),
        (data_manifest, "data_manifest"),
        (notebook_manifest, "notebook_manifest"),
        (transport_map, TRANSPORT_MAP_NAME),
    ):
        if not path.is_file():
            raise RuntimeError(f"{label} manifest missing: {path}")
    notebook_entries = json.loads(notebook_manifest.read_text(encoding="utf-8"))
    if not notebook_entries:
        raise RuntimeError("notebook_manifest must be non-empty for the Pilot bundle")
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
        "notebook_manifest_sha256": _sha256_bytes(notebook_manifest.read_bytes()),
        "kaggle_transport_path_map_sha256": _sha256_bytes(transport_map.read_bytes()),
    }


def regenerate_data_manifest(output_root: Path) -> None:
    """Regenerate data_manifest.json after repository snapshot materialization.

    The reused historical builder generates the data manifest before external
    pinned repository trees are materialized; the corrected Pilot bundle must
    manifest every materialized repository file.
    """
    builder = _load_historical_builder()
    data_manifest = builder.generate_manifest(output_root / "data", "data")
    builder.write_manifest(data_manifest, output_root / "data_manifest.json")


def regenerate_code_manifest(output_root: Path) -> None:
    """Regenerate code_manifest.json after the Pilot runtime lock is added."""
    builder = _load_historical_builder()
    code_manifest = builder.generate_manifest(output_root / "code", "code")
    builder.write_manifest(code_manifest, output_root / "code_manifest.json")


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
    transport_map = build_transport_path_map(bundle_root)
    on_disk_map = json.loads((bundle_root / TRANSPORT_MAP_NAME).read_text(encoding="utf-8"))
    if transport_map != on_disk_map:
        raise RuntimeError(
            "transport path map on disk does not match the deterministic scan of the bundle tree"
        )
    unsafe_orig = sorted(rel for rel in files if not is_kaggle_safe_name(rel))
    if set(transport_map.values()) != set(unsafe_orig):
        raise RuntimeError(
            "transport map members do not match unsafe members in the bundle tree"
        )
    for rel in unsafe_orig:
        if transport_map[transport_blob_name(rel)] != rel:
            raise RuntimeError(
                f"transport map does not round-trip original member: {rel}"
            )
    member_for = {rel: transport_blob_name(rel) for rel in unsafe_orig}
    planned_members = [member_for.get(rel, rel) for rel in files]
    validate_archive_members_kaggle_ready(planned_members)
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel in files:
            member = member_for.get(rel, rel)
            info = zipfile.ZipInfo(member, date_time=date_time)
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, (bundle_root / rel).read_bytes())
    with zipfile.ZipFile(archive_path, "r") as zf:
        validate_archive_members_kaggle_ready(zf.namelist())
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
    repo_cache: Path | None = None,
    allow_acquire: bool = False,
    notebook: Path | None = None,
    validate_notebook_trust: bool = True,
) -> dict[str, Any]:
    if output_root.resolve() == HISTORICAL_SMOKE_UPLOAD.resolve():
        raise RuntimeError("refusing to build the Pilot bundle over the historical Smoke bundle")
    builder = _load_historical_builder()
    notebook_path = PILOT_NOTEBOOK if notebook is None else notebook
    _redirect_builder(builder, output_root, notebook_path)
    errors = builder.build_bundle()
    if errors:
        raise RuntimeError(f"reused bundle builder reported {errors} verification error(s)")

    # Add the Pilot-specific pinned runtime lock to the code bundle and
    # regenerate the code manifest so the archive manifests every file.
    if not PILOT_RUNTIME_LOCK.is_file():
        raise RuntimeError(f"Pilot runtime lock missing: {PILOT_RUNTIME_LOCK}")
    lock_dst = output_root / "code" / PILOT_RUNTIME_LOCK.name
    shutil.copy2(PILOT_RUNTIME_LOCK, lock_dst)
    builder.normalize_text(lock_dst)

    # The Kaggle preflight consumes the shared snapshot/preflight module and the
    # repository-environment provisioning helper; they must ride in the code
    # bundle (the historical builder never included scripts/). Only the Pilot
    # bundle gains these files.
    if not PILOT_SNAPSHOT_SCRIPT.is_file():
        raise RuntimeError(f"Pilot snapshot script missing: {PILOT_SNAPSHOT_SCRIPT}")
    snapshot_dst = output_root / "code" / "scripts" / PILOT_SNAPSHOT_SCRIPT.name
    snapshot_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PILOT_SNAPSHOT_SCRIPT, snapshot_dst)
    builder.normalize_text(snapshot_dst)

    if not PILOT_ENVS_SCRIPT.is_file():
        raise RuntimeError(f"Pilot repository-env provisioning helper missing: {PILOT_ENVS_SCRIPT}")
    envs_dst = output_root / "code" / "scripts" / PILOT_ENVS_SCRIPT.name
    shutil.copy2(PILOT_ENVS_SCRIPT, envs_dst)
    builder.normalize_text(envs_dst)

    regenerate_code_manifest(output_root)

    snapshot_evidence = _load_pilot_repo_snapshot().materialize_repositories(
        data_repositories_dir=output_root / "data" / "repositories",
        repo_cache=repo_cache,
        allow_acquire=allow_acquire,
    )
    regenerate_data_manifest(output_root)
    snapshot_manifest = {
        "task": FROZEN_TASK,
        "protocol_version": FROZEN_PROTOCOL_VERSION,
        "repositories": snapshot_evidence,
    }
    snapshot_manifest_path = output_root / "repository_snapshot_manifest.json"
    snapshot_manifest_path.write_text(
        json.dumps(snapshot_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    transport_map = build_transport_path_map(output_root)
    write_transport_path_map(output_root, transport_map)

    identity = build_identity(output_root, source_commit, source_tag, created_utc)
    identity["repository_snapshot_manifest_sha256"] = _sha256_bytes(
        snapshot_manifest_path.read_bytes()
    )
    write_identity(output_root, identity)

    if validate_notebook_trust:
        bundled_notebook = output_root / "notebooks" / notebook_path.name
        mismatches = validate_bundled_notebook_trust(identity, bundled_notebook)
        if mismatches:
            raise RuntimeError(
                "PILOT DEPLOYMENT MANIFEST/MAP SHA MISMATCH - embedded notebook "
                "trust validation FAILED (stale frozen anchors in the bundled "
                "notebook):\n- " + "\n- ".join(mismatches)
            )

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
        required=True,
        help="Exact pre-execution stable release tag (e.g. v0.9.10-pilot-exec-ready).",
    )
    parser.add_argument(
        "--created-utc",
        type=str,
        default=None,
        help="Explicit ISO-8601 UTC creation timestamp (deterministic builds).",
    )
    parser.add_argument(
        "--notebook",
        type=Path,
        default=None,
        help=(
            "Pilot notebook source to bundle (default: "
            f"{PILOT_NOTEBOOK}). Used by the finalizer to bundle the exact "
            "frozen copy; the canonical path is used for normal release builds."
        ),
    )
    parser.add_argument(
        "--repo-cache",
        type=Path,
        default=None,
        help=(
            "Reusable local acquisition cache containing git checkouts of the "
            f"external pinned repositories (djangocms, saleor). Default: {DEFAULT_REPO_CACHE}"
        ),
    )
    parser.add_argument(
        "--allow-acquire",
        action="store_true",
        default=False,
        help="Allow fetching a missing pinned commit into the repo cache.",
    )
    args = parser.parse_args()
    if args.source_commit is None:
        args.source_commit = _git_head_sha()
    if args.created_utc is None:
        args.created_utc = datetime.now().astimezone().isoformat()
    if args.repo_cache is None:
        args.repo_cache = DEFAULT_REPO_CACHE
    return args


def main() -> int:
    args = parse_args()
    build_pilot_bundle(
        output_root=args.output_root,
        archive_path=args.archive_path,
        source_commit=args.source_commit,
        source_tag=args.source_tag,
        created_utc=args.created_utc,
        repo_cache=args.repo_cache,
        allow_acquire=args.allow_acquire,
        notebook=args.notebook,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
