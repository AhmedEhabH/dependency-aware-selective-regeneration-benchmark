from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from benchmark.core.enums import ArtifactType
from benchmark.core.exceptions import RepositoryError
from benchmark.core.models import ArtifactRef


@dataclass(frozen=True)
class SnapshotMetadata:
    repository_id: str
    commit_sha: str
    path: str
    created_at: datetime
    verified: bool = False

    def __post_init__(self) -> None:
        if not self.repository_id:
            raise ValueError("SnapshotMetadata.repository_id must not be empty")
        if not self.commit_sha:
            raise ValueError("SnapshotMetadata.commit_sha must not be empty")
        if not self.path:
            raise ValueError("SnapshotMetadata.path must not be empty")


def create_snapshot_metadata(
    repository_id: str,
    commit_sha: str,
    path: str | Path,
    verified: bool = False,
) -> SnapshotMetadata:
    if not repository_id:
        raise RepositoryError("repository_id must not be empty")
    if not commit_sha:
        raise RepositoryError("commit_sha must not be empty")
    if not path:
        raise RepositoryError("path must not be empty")
    return SnapshotMetadata(
        repository_id=repository_id,
        commit_sha=commit_sha,
        path=str(path),
        created_at=datetime.now(UTC),
        verified=verified,
    )


def validate_snapshot(metadata: SnapshotMetadata) -> list[str]:
    errors: list[str] = []
    if metadata.commit_sha in ("TBD", "", "unknown"):
        errors.append(f"Commit SHA is not resolved: {metadata.commit_sha}")
    resolved = Path(metadata.path)
    if not resolved.exists():
        errors.append(f"Snapshot path does not exist: {metadata.path}")
    if not resolved.is_dir():
        errors.append(f"Snapshot path is not a directory: {metadata.path}")
    return errors


_EXCLUDED_DIRS: frozenset[str] = frozenset({
    ".git",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "runs",
    "tmp",
    "_auto_resume_temp",
})

_EXCLUDED_FILE_SUFFIXES: frozenset[str] = frozenset({
    ".pyc",
})

# Directories excluded during llm_editable directory-policy expansion.
# This is the profile policy as exercised by the frozen repositories:
# tests, migrations, caches, and generated artifacts are never editable.
_EXPANSION_EXCLUDED_DIRS: frozenset[str] = _EXCLUDED_DIRS | frozenset({
    "tests",
    "test",
    "migrations",
    "node_modules",
})


def _is_egg_info_dir(path: Path) -> bool:
    return path.suffix == ".egg-info" and path.is_dir()


_STAGING_EXCLUDED_DIRS: frozenset[str] = frozenset({
    ".git",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "runs",
    "tmp",
    "_auto_resume_temp",
})


def _safe_segment_name(name: str) -> str:
    if ".." in name or "/" in name or "\\" in name:
        raise RepositoryError(f"Path traversal detected in identifier: {name!r}")
    clean = Path(name).name
    if not clean:
        raise RepositoryError(f"Empty or invalid repository/revision identifier: {name!r}")
    return clean


def _snapshot_content_equal(left: Path, right: Path) -> bool:
    def _eligible_paths(root: Path) -> frozenset[Path]:
        result: set[Path] = set()
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [
                d
                for d in dirnames
                if d not in _STAGING_EXCLUDED_DIRS
                and not _is_egg_info_dir(Path(dirpath) / d)
            ]
            for filename in filenames:
                full = Path(dirpath) / filename
                if full.is_symlink():
                    continue
                if any(filename.endswith(suffix) for suffix in _EXCLUDED_FILE_SUFFIXES):
                    continue
                rel = full.relative_to(root)
                result.add(rel)
        return frozenset(result)

    left_paths = _eligible_paths(left)
    right_paths = _eligible_paths(right)
    if left_paths != right_paths:
        return False
    return all(
        (left / rel_path).read_bytes() == (right / rel_path).read_bytes()
        for rel_path in left_paths
    )


def stage_repository_snapshot(
    source_root: str | Path,
    snapshot_storage_root: str | Path,
    repository_id: str,
    revision_id: str,
) -> Path:
    source = Path(source_root)
    if not source.is_dir():
        raise RepositoryError(
            f"Source repository path does not exist or is not a directory: {source}"
        )

    storage = Path(snapshot_storage_root)
    safe_repo = _safe_segment_name(repository_id)
    safe_rev = _safe_segment_name(revision_id)
    destination = storage / safe_repo / safe_rev

    if destination.is_dir():
        if _snapshot_content_equal(source, destination):
            return destination
        raise RepositoryError(
            f"Existing staged snapshot content differs for {safe_repo}/{safe_rev}"
        )

    destination.parent.mkdir(parents=True, exist_ok=True)

    def _ignore_patterns(dirpath: str, names: list[str]) -> list[str]:
        ignored: list[str] = []
        for name in names:
            full = Path(dirpath) / name
            if full.is_symlink():
                ignored.append(name)
                continue
            if name in _STAGING_EXCLUDED_DIRS:
                ignored.append(name)
                continue
            if name.endswith(".pyc"):
                ignored.append(name)
                continue
            if _is_egg_info_dir(full):
                ignored.append(name)
                continue
        return ignored

    shutil.copytree(
        source,
        destination,
        ignore=_ignore_patterns,
        symlinks=False,
        dirs_exist_ok=False,
    )

    return destination


def _validate_policy_path(path_str: str, seen: set[str]) -> str:
    if "\\" in path_str:
        raise RepositoryError(f"Backslash rejected (use POSIX form): {path_str}")
    if path_str.startswith("/"):
        raise RepositoryError(f"Absolute path rejected: {path_str}")
    if ".." in path_str.split("/"):
        raise RepositoryError(f"Path traversal rejected: {path_str}")
    if path_str in seen:
        raise RepositoryError(f"Duplicate path: {path_str}")
    seen.add(path_str)
    return path_str.replace("\\", "/")


def _discover_eligible_source_files(dir_path: Path) -> list[str]:
    """Recursively list repository-relative .py files under a directory.

    Tests, migrations, caches, generated artifacts, and symlinks are excluded.
    Deterministic sorted order. No Ground Truth enters here.
    """
    files: list[str] = []
    for dirpath, dirnames, filenames in os.walk(dir_path):
        dirnames[:] = [
            d for d in dirnames if d not in _EXPANSION_EXCLUDED_DIRS
            and not _is_egg_info_dir(Path(dirpath) / d)
        ]
        for filename in filenames:
            if any(filename.endswith(suffix) for suffix in _EXCLUDED_FILE_SUFFIXES):
                continue
            full = Path(dirpath) / filename
            if full.is_symlink():
                continue
            if full.suffix.lower() == ".py":
                files.append(full.relative_to(dir_path).as_posix())
    files.sort()
    return files


def expand_editable_paths(
    snapshot_path: str | Path,
    allowed_paths: tuple[str, ...],
) -> tuple[str, ...]:
    """Expand an llm_editable policy to concrete eligible source files.

    The runtime artifact universe stays file-granular: directory policy
    entries (django CMS ``cms/middleware/``, Saleor ``saleor/core/``, ...) are
    deterministically expanded to their concrete repository-relative .py files.
    Strict guards:
      - repository-relative only (no absolute / backslash / traversal);
      - duplicate normalized paths rejected;
      - tests, migrations, caches, generated artifacts never expandable;
      - a directory entry must resolve to at least one file or fail closed.
    """
    root = Path(snapshot_path)
    if not root.is_dir():
        raise RepositoryError(f"Snapshot path is not a directory: {snapshot_path}")
    if not allowed_paths:
        raise RepositoryError("allowed_paths must be non-empty for scientific regeneration")

    expanded: list[str] = []
    raw_seen: set[str] = set()
    for path_str in allowed_paths:
        posix_form = _validate_policy_path(path_str, raw_seen)
        resolved = (root / posix_form).resolve()
        if not resolved.exists():
            raise RepositoryError(f"Path does not exist: {path_str}")
        try:
            resolved.relative_to(root.resolve())
        except ValueError:
            raise RepositoryError(f"Path escapes snapshot root: {path_str}") from None
        if resolved.is_dir():
            files = _discover_eligible_source_files(resolved)
            if not files:
                raise RepositoryError(
                    f"Directory policy entry resolved to no eligible source files: {path_str}"
                )
            rel_dir = posix_form.rstrip("/")
            expanded.extend(
                f"{rel_dir}/{f}" if rel_dir else f
                for f in files
            )
        elif resolved.is_file():
            expanded.append(posix_form.rstrip("/"))
        else:
            raise RepositoryError(f"Path is not a regular file: {path_str}")

    seen: set[str] = set()
    result: list[str] = []
    for p in expanded:
        if p in seen:
            raise RepositoryError(f"Duplicate path after expansion: {p}")
        seen.add(p)
        result.append(p)
    result.sort()
    return tuple(result)


def resolve_allowed_artifacts(
    snapshot_path: str | Path,
    allowed_paths: tuple[str, ...],
) -> tuple[ArtifactRef, ...]:
    root = Path(snapshot_path)
    if not root.is_dir():
        raise RepositoryError(f"Snapshot path is not a directory: {snapshot_path}")

    if not allowed_paths:
        raise RepositoryError("allowed_paths must be non-empty for scientific regeneration")

    seen: set[str] = set()
    result: list[ArtifactRef] = []

    for path_str in allowed_paths:
        if "\\" in path_str:
            raise RepositoryError(f"Backslash rejected (use POSIX form): {path_str}")
        if path_str.startswith("/"):
            raise RepositoryError(f"Absolute path rejected: {path_str}")
        if ".." in path_str.split("/"):
            raise RepositoryError(f"Path traversal rejected: {path_str}")
        if path_str in seen:
            raise RepositoryError(f"Duplicate path: {path_str}")
        seen.add(path_str)

        posix_form = path_str.replace("\\", "/")
        resolved = (root / posix_form).resolve()
        if not resolved.exists():
            raise RepositoryError(f"Path does not exist: {path_str}")
        if resolved.is_dir():
            raise RepositoryError(f"Path is a directory (must be a file): {path_str}")
        try:
            resolved.relative_to(root.resolve())
        except ValueError:
            raise RepositoryError(f"Path escapes snapshot root: {path_str}") from None

        result.append(ArtifactRef(path=posix_form, artifact_type=ArtifactType.source))

    result.sort(key=lambda r: r.path)
    return tuple(result)


def discover_eligible_artifacts(
    snapshot_path: str | Path,
    extensions: tuple[str, ...] = (".py",),
) -> tuple[ArtifactRef, ...]:
    root = Path(snapshot_path)
    if not root.is_dir():
        return ()

    normalized_extensions = tuple(ext.lower() for ext in extensions)
    result: list[ArtifactRef] = []

    for dirpath, dirnames, filenames in os.walk(root):
        dir_rel = Path(dirpath).relative_to(root)

        # Prune excluded directories in-place to prevent descent
        dirnames[:] = [
            d
            for d in dirnames
            if d not in _EXCLUDED_DIRS and not _is_egg_info_dir(Path(dirpath) / d)
        ]

        for filename in filenames:
            if any(filename.endswith(suffix) for suffix in _EXCLUDED_FILE_SUFFIXES):
                continue
            file_rel = dir_rel / filename
            ext = file_rel.suffix.lower()
            if ext in normalized_extensions:
                posix_path = file_rel.as_posix()
                result.append(ArtifactRef(path=posix_path, artifact_type=ArtifactType.source))

    result.sort(key=lambda r: r.path)
    return tuple(result)
