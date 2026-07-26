from __future__ import annotations

import os
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
    "_auto_resume_temp",
})

_EXCLUDED_FILE_SUFFIXES: frozenset[str] = frozenset({
    ".pyc",
})


def _is_egg_info_dir(path: Path) -> bool:
    return path.suffix == ".egg-info" and path.is_dir()


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
