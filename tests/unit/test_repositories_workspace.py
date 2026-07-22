from pathlib import Path

import pytest

from benchmark.core.exceptions import RepositoryError
from benchmark.repositories.workspace import (
    WorkspacePath,
    check_isolation,
    validate_workspace_path,
)


class TestWorkspacePath:
    def test_valid_creation(self) -> None:
        w = WorkspacePath(root="/tmp/workspace")
        assert w.root == "/tmp/workspace"
        assert str(w.snapshots).endswith("snapshots")
        assert str(w.runs).endswith("runs")
        assert str(w.temp).endswith("tmp")

    def test_empty_root_raises(self) -> None:
        with pytest.raises(ValueError, match="WorkspacePath.root"):
            WorkspacePath(root="")


class TestValidateWorkspacePath:
    def test_nonexistent_path_raises(self, tmp_path: Path) -> None:
        with pytest.raises(RepositoryError, match="does not exist"):
            validate_workspace_path(tmp_path / "nonexistent")

    def test_file_path_raises(self, tmp_path: Path) -> None:
        f = tmp_path / "file.txt"
        f.write_text("", encoding="utf-8")
        with pytest.raises(RepositoryError, match="not a directory"):
            validate_workspace_path(f)

    def test_valid_directory_returns_resolved(self, tmp_path: Path) -> None:
        result = validate_workspace_path(tmp_path)
        assert result == tmp_path.resolve()


class TestCheckIsolation:
    def test_same_path_violation(self, tmp_path: Path) -> None:
        violations = check_isolation(tmp_path, tmp_path)
        assert len(violations) == 1
        assert "same as workspace" in violations[0]

    def test_nested_path_violation(self, tmp_path: Path) -> None:
        nested = tmp_path / "snapshots" / "repo"
        violations = check_isolation(tmp_path, nested)
        assert len(violations) == 1
        assert "inside workspace" in violations[0]

    def test_separate_paths_no_violation(self, tmp_path: Path) -> None:
        ws = tmp_path / "workspace"
        snap = tmp_path / "snapshots_external"
        ws.mkdir()
        snap.mkdir()
        violations = check_isolation(ws, snap)
        assert len(violations) == 0

    def test_nonexistent_path_no_violations(self) -> None:
        ws = Path("z:/nonexistent_workspace_xyz")
        snap = Path("z:/nonexistent_snap_xyz")
        violations = check_isolation(ws, snap)
        assert len(violations) == 0
