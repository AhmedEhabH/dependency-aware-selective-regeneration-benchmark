from datetime import UTC, datetime
from pathlib import Path

import pytest

from benchmark.core.exceptions import RepositoryError
from benchmark.repositories.snapshot import (
    SnapshotMetadata,
    create_snapshot_metadata,
    validate_snapshot,
)


class TestSnapshotMetadata:
    def test_valid_creation(self) -> None:
        m = SnapshotMetadata(
            repository_id="todo",
            commit_sha="abc123",
            path="/tmp/snapshots/todo",
            created_at=datetime.now(UTC),
        )
        assert m.repository_id == "todo"
        assert m.commit_sha == "abc123"

    def test_empty_id_raises(self) -> None:
        from datetime import datetime

        with pytest.raises(ValueError, match="SnapshotMetadata.repository_id"):
            SnapshotMetadata(
                repository_id="",
                commit_sha="abc",
                path="/tmp/snap",
                created_at=datetime.now(UTC),
            )

    def test_empty_sha_raises(self) -> None:
        from datetime import datetime

        with pytest.raises(ValueError, match="SnapshotMetadata.commit_sha"):
            SnapshotMetadata(
                repository_id="todo",
                commit_sha="",
                path="/tmp/snap",
                created_at=datetime.now(UTC),
            )

    def test_empty_path_raises(self) -> None:
        from datetime import datetime

        with pytest.raises(ValueError, match="SnapshotMetadata.path"):
            SnapshotMetadata(
                repository_id="todo",
                commit_sha="abc",
                path="",
                created_at=datetime.now(UTC),
            )


class TestCreateSnapshotMetadata:
    def test_valid_creation(self, tmp_path: Path) -> None:
        meta = create_snapshot_metadata(
            repository_id="todo",
            commit_sha="abc123def",
            path=str(tmp_path / "snapshots" / "todo"),
        )
        assert meta.repository_id == "todo"
        assert meta.commit_sha == "abc123def"
        assert meta.verified is False

    def test_verified_flag(self, tmp_path: Path) -> None:
        meta = create_snapshot_metadata(
            repository_id="todo",
            commit_sha="abc123",
            path=str(tmp_path / "snap"),
            verified=True,
        )
        assert meta.verified is True

    def test_empty_id_raises(self) -> None:
        with pytest.raises(RepositoryError, match="repository_id must not be empty"):
            create_snapshot_metadata(repository_id="", commit_sha="abc", path="/tmp")

    def test_empty_sha_raises(self) -> None:
        with pytest.raises(RepositoryError, match="commit_sha must not be empty"):
            create_snapshot_metadata(repository_id="todo", commit_sha="", path="/tmp")

    def test_empty_path_raises(self) -> None:
        with pytest.raises(RepositoryError, match="path must not be empty"):
            create_snapshot_metadata(
                repository_id="todo", commit_sha="abc", path=""
            )


class TestValidateSnapshot:
    def test_tbd_sha_reported(self) -> None:
        from datetime import datetime

        meta = SnapshotMetadata(
            repository_id="todo",
            commit_sha="TBD",
            path="/tmp/nonexistent",
            created_at=datetime.now(UTC),
        )
        errors = validate_snapshot(meta)
        assert any("TBD" in e for e in errors)

    def test_nonexistent_path_reported(self) -> None:
        from datetime import datetime

        meta = SnapshotMetadata(
            repository_id="todo",
            commit_sha="abc123",
            path="/tmp/nonexistent_snapshot_path",
            created_at=datetime.now(UTC),
        )
        errors = validate_snapshot(meta)
        assert any("does not exist" in e for e in errors)

    def test_file_path_reported(self, tmp_path: Path) -> None:
        from datetime import datetime

        f = tmp_path / "file.txt"
        f.write_text("content", encoding="utf-8")
        meta = SnapshotMetadata(
            repository_id="todo",
            commit_sha="abc123",
            path=str(f),
            created_at=datetime.now(UTC),
        )
        errors = validate_snapshot(meta)
        assert any("not a directory" in e for e in errors)

    def test_valid_snapshot_no_errors(self, tmp_path: Path) -> None:
        from datetime import datetime

        snap_dir = tmp_path / "snapshots" / "todo"
        snap_dir.mkdir(parents=True)
        meta = SnapshotMetadata(
            repository_id="todo",
            commit_sha="abc123def",
            path=str(snap_dir),
            created_at=datetime.now(UTC),
        )
        errors = validate_snapshot(meta)
        assert len(errors) == 0
