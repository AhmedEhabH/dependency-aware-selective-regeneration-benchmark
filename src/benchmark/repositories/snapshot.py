from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from benchmark.core.exceptions import RepositoryError


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
