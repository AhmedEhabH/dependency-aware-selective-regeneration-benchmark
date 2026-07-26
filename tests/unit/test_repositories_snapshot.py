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
    stage_repository_snapshot,
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

    def test_tmp_excluded_from_discovery(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "tmp").mkdir()
        (repo / "tmp" / "scratch.py").write_text("")
        (repo / "src").mkdir()
        (repo / "src" / "work.py").write_text("")
        result = discover_eligible_artifacts(repo)
        paths = {r.path for r in result}
        assert paths == {"src/work.py"}


class TestStageRepositorySnapshot:
    def test_valid_source_staging(self, tmp_path: Path) -> None:
        source = tmp_path / "source"
        source.mkdir()
        (source / "main.py").write_text("content")
        storage = tmp_path / "storage"
        storage.mkdir()
        result = stage_repository_snapshot(source, storage, "myrepo", "rev1")
        expected = storage / "myrepo" / "rev1"
        assert result == expected
        assert expected.is_dir()
        assert (expected / "main.py").read_text() == "content"

    def test_nested_files_copied(self, tmp_path: Path) -> None:
        source = tmp_path / "source"
        source.mkdir()
        nested = source / "src" / "sub"
        nested.mkdir(parents=True)
        (nested / "deep.py").write_text("nested")
        (source / "root.py").write_text("root")
        storage = tmp_path / "storage"
        storage.mkdir()
        result = stage_repository_snapshot(source, storage, "r", "v1")
        assert (result / "src/sub/deep.py").read_text() == "nested"
        assert (result / "root.py").read_text() == "root"

    def test_excluded_directories_not_copied(self, tmp_path: Path) -> None:
        source = tmp_path / "source"
        source.mkdir()
        (source / "src").mkdir()
        (source / "src" / "work.py").write_text("keep")
        for d in (".git", "__pycache__", "runs", "tmp", "_auto_resume_temp"):
            (source / d).mkdir(parents=True)
            (source / d / "ignored.py").write_text("drop")
        storage = tmp_path / "storage"
        storage.mkdir()
        result = stage_repository_snapshot(source, storage, "r", "v1")
        assert (result / "src/work.py").exists()
        assert not (result / ".git" / "ignored.py").exists()
        assert not (result / "__pycache__" / "ignored.py").exists()
        assert not (result / "runs" / "ignored.py").exists()
        assert not (result / "tmp" / "ignored.py").exists()
        assert not (result / "_auto_resume_temp" / "ignored.py").exists()

    def test_pyc_not_copied(self, tmp_path: Path) -> None:
        source = tmp_path / "source"
        source.mkdir()
        (source / "keep.py").write_text("keep")
        (source / "drop.pyc").write_text("")
        storage = tmp_path / "storage"
        storage.mkdir()
        result = stage_repository_snapshot(source, storage, "r", "v1")
        assert (result / "keep.py").exists()
        assert not (result / "drop.pyc").exists()

    def test_repository_id_traversal_rejected(self, tmp_path: Path) -> None:
        source = tmp_path / "source"
        source.mkdir()
        (source / "f.py").write_text("")
        storage = tmp_path / "storage"
        storage.mkdir()
        from benchmark.core.exceptions import RepositoryError
        with pytest.raises(RepositoryError, match="traversal"):
            stage_repository_snapshot(source, storage, "../escape", "v1")

    def test_revision_id_traversal_rejected(self, tmp_path: Path) -> None:
        source = tmp_path / "source"
        source.mkdir()
        (source / "f.py").write_text("")
        storage = tmp_path / "storage"
        storage.mkdir()
        from benchmark.core.exceptions import RepositoryError
        with pytest.raises(RepositoryError, match="traversal"):
            stage_repository_snapshot(source, storage, "repo", "../../escape")

    def test_missing_source_rejected(self, tmp_path: Path) -> None:
        storage = tmp_path / "storage"
        storage.mkdir()
        from benchmark.core.exceptions import RepositoryError
        with pytest.raises(RepositoryError, match="does not exist"):
            stage_repository_snapshot(tmp_path / "nonexistent", storage, "r", "v1")

    def test_source_file_not_directory_rejected(self, tmp_path: Path) -> None:
        source = tmp_path / "file.txt"
        source.write_text("")
        storage = tmp_path / "storage"
        storage.mkdir()
        from benchmark.core.exceptions import RepositoryError
        with pytest.raises(RepositoryError, match="not a directory"):
            stage_repository_snapshot(source, storage, "r", "v1")

    def test_identical_snapshot_reused(self, tmp_path: Path) -> None:
        source = tmp_path / "source"
        source.mkdir()
        (source / "a.py").write_text("data")
        storage = tmp_path / "storage"
        storage.mkdir()
        r1 = stage_repository_snapshot(source, storage, "r", "v1")
        r2 = stage_repository_snapshot(source, storage, "r", "v1")
        assert r1 == r2
        assert r2 == storage / "r" / "v1"
        assert (r2 / "a.py").read_text() == "data"

    def test_modified_file_content_rejected(self, tmp_path: Path) -> None:
        source = tmp_path / "source"
        source.mkdir()
        (source / "a.py").write_text("original")
        storage = tmp_path / "storage"
        storage.mkdir()
        stage_repository_snapshot(source, storage, "r", "v1")
        (source / "a.py").write_text("modified")
        with pytest.raises(RepositoryError, match="content differs"):
            stage_repository_snapshot(source, storage, "r", "v1")

    def test_added_eligible_file_rejected(self, tmp_path: Path) -> None:
        source = tmp_path / "source"
        source.mkdir()
        (source / "a.py").write_text("")
        storage = tmp_path / "storage"
        storage.mkdir()
        stage_repository_snapshot(source, storage, "r", "v1")
        (source / "b.py").write_text("")
        with pytest.raises(RepositoryError, match="content differs"):
            stage_repository_snapshot(source, storage, "r", "v1")

    def test_removed_eligible_file_rejected(self, tmp_path: Path) -> None:
        source = tmp_path / "source"
        source.mkdir()
        (source / "a.py").write_text("")
        (source / "b.py").write_text("")
        storage = tmp_path / "storage"
        storage.mkdir()
        stage_repository_snapshot(source, storage, "r", "v1")
        (source / "b.py").unlink()
        with pytest.raises(RepositoryError, match="content differs"):
            stage_repository_snapshot(source, storage, "r", "v1")

    def test_excluded_dir_changes_tolerated(self, tmp_path: Path) -> None:
        source = tmp_path / "source"
        source.mkdir()
        (source / "a.py").write_text("")
        (source / "__pycache__").mkdir()
        (source / "__pycache__" / "cache.py").write_text("old")
        storage = tmp_path / "storage"
        storage.mkdir()
        r1 = stage_repository_snapshot(source, storage, "r", "v1")
        (source / "__pycache__" / "cache.py").write_text("new")
        (source / "__pycache__" / "extra.py").write_text("")
        r2 = stage_repository_snapshot(source, storage, "r", "v1")
        assert r1 == r2

    def test_symlink_only_diff_tolerated(self, tmp_path: Path) -> None:
        source = tmp_path / "source"
        source.mkdir()
        (source / "real.py").write_text("same")
        storage = tmp_path / "storage"
        storage.mkdir()
        r1 = stage_repository_snapshot(source, storage, "r", "v1")
        try:
            (source / "link.py").symlink_to("real.py")
        except (OSError, NotImplementedError):
            pytest.skip("symlink not supported on this platform")
        r2 = stage_repository_snapshot(source, storage, "r", "v1")
        assert r1 == r2
        assert not (r2 / "link.py").exists()

    def test_destination_unchanged_after_rejection(self, tmp_path: Path) -> None:
        source = tmp_path / "source"
        source.mkdir()
        (source / "a.py").write_text("original")
        storage = tmp_path / "storage"
        storage.mkdir()
        r1 = stage_repository_snapshot(source, storage, "r", "v1")
        original_content = (r1 / "a.py").read_text()
        (source / "a.py").write_text("modified")
        with pytest.raises(RepositoryError):
            stage_repository_snapshot(source, storage, "r", "v1")
        assert (r1 / "a.py").read_text() == original_content

    def test_destination_under_storage(self, tmp_path: Path) -> None:
        source = tmp_path / "source"
        source.mkdir()
        (source / "f.py").write_text("")
        storage = tmp_path / "storage"
        storage.mkdir()
        result = stage_repository_snapshot(source, storage, "repo", "rev")
        result.resolve().relative_to(storage.resolve())

    def test_two_repositories_do_not_contaminate(self, tmp_path: Path) -> None:
        src_a = tmp_path / "src_a"
        src_a.mkdir()
        (src_a / "a.py").write_text("from a")
        src_b = tmp_path / "src_b"
        src_b.mkdir()
        (src_b / "b.py").write_text("from b")
        storage = tmp_path / "storage"
        storage.mkdir()
        r_a = stage_repository_snapshot(src_a, storage, "repo_a", "v1")
        r_b = stage_repository_snapshot(src_b, storage, "repo_b", "v1")
        assert (r_a / "a.py").exists()
        assert not (r_a / "b.py").exists()
        assert (r_b / "b.py").exists()
        assert not (r_b / "a.py").exists()

    def test_symlink_skipped(self, tmp_path: Path) -> None:
        source = tmp_path / "source"
        source.mkdir()
        (source / "real.py").write_text("real")
        link = source / "link.py"
        try:
            link.symlink_to("real.py")
        except (OSError, NotImplementedError):
            pytest.skip("symlink not supported on this platform")
        storage = tmp_path / "storage"
        storage.mkdir()
        result = stage_repository_snapshot(source, storage, "r", "v1")
        assert (result / "real.py").exists()
        assert not (result / "link.py").exists()

    def test_directory_symlink_not_followed(self, tmp_path: Path) -> None:
        source = tmp_path / "source"
        source.mkdir()
        (source / "real_dir").mkdir()
        (source / "real_dir" / "f.py").write_text("ok")
        link = source / "link_dir"
        try:
            link.symlink_to("real_dir", target_is_directory=True)
        except (OSError, NotImplementedError):
            pytest.skip("directory symlink not supported on this platform")
        storage = tmp_path / "storage"
        storage.mkdir()
        result = stage_repository_snapshot(source, storage, "r", "v1")
        assert (result / "real_dir" / "f.py").exists()
        assert not (result / "link_dir" / "f.py").exists()
