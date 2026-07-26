from datetime import UTC, datetime
from pathlib import Path

import pytest

from benchmark.core.enums import ArtifactType
from benchmark.core.exceptions import RepositoryError
from benchmark.core.models import ArtifactRef
from benchmark.repositories.snapshot import (
    SnapshotMetadata,
    create_snapshot_metadata,
    discover_eligible_artifacts,
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


class TestDiscoverEligibleArtifacts:
    def test_python_files_discovered_recursively(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "src").mkdir()
        (repo / "src" / "main.py").write_text("")
        (repo / "src" / "utils.py").write_text("")
        (repo / "tests").mkdir()
        (repo / "tests" / "test_main.py").write_text("")
        result = discover_eligible_artifacts(repo)
        paths = {r.path for r in result}
        assert paths == {"src/main.py", "src/utils.py", "tests/test_main.py"}

    def test_non_python_files_excluded_by_default(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "main.py").write_text("")
        (repo / "readme.md").write_text("")
        (repo / "data.json").write_text("")
        (repo / "config.yaml").write_text("")
        result = discover_eligible_artifacts(repo)
        paths = {r.path for r in result}
        assert paths == {"main.py"}

    def test_custom_extensions_supported(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "main.py").write_text("")
        (repo / "main.js").write_text("")
        (repo / "main.ts").write_text("")
        result = discover_eligible_artifacts(repo, extensions=(".js", ".ts"))
        paths = {r.path for r in result}
        assert paths == {"main.js", "main.ts"}

    def test_excluded_cache_and_git_directories_ignored(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        for d in (".git", "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache"):
            (repo / d).mkdir(parents=True)
        (repo / "src").mkdir()
        (repo / "src" / "main.py").write_text("")
        (repo / ".git" / "config").write_text("")
        (repo / "__pycache__" / "foo.pyc").write_text("")
        result = discover_eligible_artifacts(repo)
        paths = {r.path for r in result}
        assert paths == {"src/main.py"}

    def test_egg_info_directories_ignored(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "src").mkdir()
        (repo / "src" / "main.py").write_text("")
        (repo / "mylib.egg-info").mkdir()
        (repo / "mylib.egg-info" / "PKG-INFO").write_text("")
        result = discover_eligible_artifacts(repo)
        paths = {r.path for r in result}
        assert paths == {"src/main.py"}

    def test_pyc_files_excluded(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "main.py").write_text("")
        (repo / "module.pyc").write_text("")
        (repo / "src").mkdir()
        (repo / "src" / "util.pyc").write_text("")
        result = discover_eligible_artifacts(repo)
        paths = {r.path for r in result}
        assert paths == {"main.py"}

    def test_relative_paths_returned(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "src" / "nested").mkdir(parents=True)
        (repo / "src" / "nested" / "deep.py").write_text("")
        result = discover_eligible_artifacts(repo)
        assert len(result) == 1
        assert result[0].path == "src/nested/deep.py"

    def test_posix_path_normalization(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        nested = repo / "a" / "b"
        nested.mkdir(parents=True)
        (nested / "deep.py").write_text("")
        (repo / "root.py").write_text("")
        result = discover_eligible_artifacts(repo)
        paths = {r.path for r in result}
        assert "a/b/deep.py" in paths
        assert "root.py" in paths
        assert all("\\" not in r.path for r in result)

    def test_deterministic_ordering(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        for name in ("z.py", "a.py", "m.py", "b.py"):
            (repo / name).write_text("")
        result = discover_eligible_artifacts(repo)
        paths = [r.path for r in result]
        assert paths == ["a.py", "b.py", "m.py", "z.py"]

    def test_missing_path_returns_empty_tuple(self) -> None:
        result = discover_eligible_artifacts("/nonexistent/path/that/does/not/exist")
        assert result == ()

    def test_empty_directory_returns_empty_tuple(self, tmp_path: Path) -> None:
        repo = tmp_path / "empty_repo"
        repo.mkdir()
        result = discover_eligible_artifacts(repo)
        assert result == ()

    def test_no_dependency_on_expected_affected_artifacts(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "main.py").write_text("")
        result = discover_eligible_artifacts(repo)
        assert len(result) == 1
        assert all(isinstance(r, ArtifactRef) for r in result)

    def test_default_type_is_source(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "main.py").write_text("")
        result = discover_eligible_artifacts(repo)
        assert len(result) == 1
        assert result[0].artifact_type == ArtifactType.source

    def test_case_insensitive_extension_matching(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "main.PY").write_text("")
        (repo / "helper.py").write_text("")
        result = discover_eligible_artifacts(repo)
        paths = {r.path for r in result}
        assert paths == {"helper.py", "main.PY"}

    def test_runs_directory_excluded(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "runs").mkdir()
        (repo / "runs" / "output.py").write_text("")
        (repo / "src").mkdir()
        (repo / "src" / "main.py").write_text("")
        result = discover_eligible_artifacts(repo)
        paths = {r.path for r in result}
        assert paths == {"src/main.py"}

    def test_auto_resume_temp_excluded(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "_auto_resume_temp").mkdir()
        (repo / "_auto_resume_temp" / "state.py").write_text("")
        (repo / "src").mkdir()
        (repo / "src" / "main.py").write_text("")
        result = discover_eligible_artifacts(repo)
        paths = {r.path for r in result}
        assert paths == {"src/main.py"}
