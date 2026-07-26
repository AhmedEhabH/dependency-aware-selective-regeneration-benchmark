from pathlib import Path

from benchmark.execution.isolation import IsolationContext
from benchmark.repositories.workspace import WorkspacePath


class TestIsolationContext:
    def test_verify_creates_report(self, tmp_path: Path) -> None:
        ws = WorkspacePath(root=str(tmp_path))
        ctx = IsolationContext(workspace=ws, snapshot_base=tmp_path)
        report = ctx.verify()
        assert report.passed is False
        assert len(report.violations) > 0

    def test_passes_with_valid_separation(self, tmp_path: Path) -> None:
        ws_root = tmp_path / "workspace"
        ws_root.mkdir()
        snap_base = tmp_path / "snapshots"
        snap_base.mkdir()
        ws = WorkspacePath(root=str(ws_root))
        ctx = IsolationContext(workspace=ws, snapshot_base=snap_base)
        report = ctx.verify()
        assert report.passed is True

    def test_private_data_check(self, tmp_path: Path) -> None:
        ws = WorkspacePath(root=str(tmp_path))
        ctx = IsolationContext(workspace=ws)
        private_path = tmp_path / "private" / "data.txt"
        private_path.parent.mkdir()
        private_path.write_text("secret")
        report = ctx.check_private_data_access(paths=(str(private_path),))
        assert report.passed is False

    def test_private_data_check_public_path(self, tmp_path: Path) -> None:
        ws = WorkspacePath(root=str(tmp_path))
        ctx = IsolationContext(workspace=ws)
        public_path = tmp_path / "public" / "data.txt"
        public_path.parent.mkdir()
        public_path.write_text("ok")
        report = ctx.check_private_data_access(paths=(str(public_path),))
        assert report.passed is True

    def test_make_run_directory(self, tmp_path: Path) -> None:
        ws = WorkspacePath(root=str(tmp_path))
        ws.runs.mkdir(parents=True)
        ctx = IsolationContext(workspace=ws)
        run_dir = ctx.make_run_directory("run-001")
        assert run_dir.exists()
        assert run_dir.is_dir()
        assert run_dir.name == "run-001"

    def test_make_temp_directory(self, tmp_path: Path) -> None:
        ws = WorkspacePath(root=str(tmp_path))
        ws.temp.mkdir(parents=True)
        ctx = IsolationContext(workspace=ws)
        tmp_dir = ctx.make_temp_directory(prefix="test")
        assert tmp_dir.exists()
        assert tmp_dir.is_dir()
        assert tmp_dir.name.startswith("test_")

    def test_workspace_property(self, tmp_path: Path) -> None:
        ws = WorkspacePath(root=str(tmp_path))
        ctx = IsolationContext(workspace=ws)
        assert ctx.workspace is ws

    def test_snapshot_base_default(self, tmp_path: Path) -> None:
        ws = WorkspacePath(root=str(tmp_path))
        ctx = IsolationContext(workspace=ws)
        assert ctx.snapshot_base == ws.snapshots

    def test_custom_validator(self, tmp_path: Path) -> None:
        ws_root = tmp_path / "workspace"
        ws_root.mkdir()
        snap_base = tmp_path / "snapshots"
        snap_base.mkdir()

        def always_fail(_base: Path) -> list[str]:
            return ["custom violation"]

        ctx = IsolationContext(
            workspace=WorkspacePath(root=str(ws_root)),
            snapshot_base=snap_base,
            validator=always_fail,
        )
        report = ctx.verify()
        assert report.passed is False
        assert "custom violation" in report.message


class TestActiveSnapshotRoot:
    def test_defaults_to_none(self, tmp_path: Path) -> None:
        ws = WorkspacePath(root=str(tmp_path))
        ctx = IsolationContext(workspace=ws)
        assert ctx.active_snapshot_root is None

    def test_stored_correctly(self, tmp_path: Path) -> None:
        ws = WorkspacePath(root=str(tmp_path))
        active = tmp_path / "snapshots" / "myrepo" / "v1"
        ctx = IsolationContext(workspace=ws, active_snapshot_root=active)
        assert ctx.active_snapshot_root == active

    def test_verify_fails_when_active_equals_snapshot_base(self, tmp_path: Path) -> None:
        ws_root = tmp_path / "workspace"
        ws_root.mkdir()
        snap_base = tmp_path / "storage"
        snap_base.mkdir()
        ws = WorkspacePath(root=str(ws_root))
        ctx = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=snap_base)
        report = ctx.verify()
        assert report.passed is False
        assert "strict descendant" in report.message

    def test_verify_passes_when_active_within_snapshot_base(self, tmp_path: Path) -> None:
        ws_root = tmp_path / "workspace"
        ws_root.mkdir()
        snap_base = tmp_path / "storage"
        snap_base.mkdir()
        active = snap_base / "repo" / "rev1"
        active.mkdir(parents=True)
        ws = WorkspacePath(root=str(ws_root))
        ctx = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active)
        report = ctx.verify()
        assert report.passed is True

    def test_verify_fails_when_active_outside_snapshot_base(self, tmp_path: Path) -> None:
        ws_root = tmp_path / "workspace"
        ws_root.mkdir()
        snap_base = tmp_path / "storage"
        snap_base.mkdir()
        active = tmp_path / "outside" / "repo" / "rev1"
        active.mkdir(parents=True)
        ws = WorkspacePath(root=str(ws_root))
        ctx = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active)
        report = ctx.verify()
        assert report.passed is False
        assert "outside" in report.message

    def test_deeply_nested_active_passes(self, tmp_path: Path) -> None:
        ws_root = tmp_path / "workspace"
        ws_root.mkdir()
        snap_base = tmp_path / "storage"
        snap_base.mkdir()
        active = snap_base / "a" / "b" / "c" / "d" / "e"
        active.mkdir(parents=True)
        ws = WorkspacePath(root=str(ws_root))
        ctx = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active)
        report = ctx.verify()
        assert report.passed is True

    def test_sibling_prefix_fails(self, tmp_path: Path) -> None:
        ws_root = tmp_path / "workspace"
        ws_root.mkdir()
        snap_base = tmp_path / "storage"
        snap_base.mkdir()
        active = tmp_path / "storage-extra" / "repo" / "rev1"
        active.mkdir(parents=True)
        ws = WorkspacePath(root=str(ws_root))
        ctx = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active)
        report = ctx.verify()
        assert report.passed is False

    def test_parent_traversal_fails(self, tmp_path: Path) -> None:
        ws_root = tmp_path / "workspace"
        ws_root.mkdir()
        snap_base = tmp_path / "storage"
        snap_base.mkdir()
        active = tmp_path / "storage" / ".." / "etc"
        active.resolve().parent.mkdir(parents=True, exist_ok=True)
        active = active.resolve()
        ws = WorkspacePath(root=str(ws_root))
        ctx = IsolationContext(workspace=ws, snapshot_base=snap_base, active_snapshot_root=active)
        report = ctx.verify()
        assert report.passed is False

    def test_structural_boundary_check(self, tmp_path: Path) -> None:
        ws_root = tmp_path / "workspace"
        ws_root.mkdir()
        snap_base = tmp_path / "storage"
        snap_base.mkdir()
        prefix_sibling = tmp_path / "storage_extra"
        prefix_sibling.mkdir()
        ws = WorkspacePath(root=str(ws_root))
        ctx = IsolationContext(
            workspace=ws, snapshot_base=snap_base, active_snapshot_root=prefix_sibling
        )
        report = ctx.verify()
        assert report.passed is False
