from pathlib import Path

from benchmark.execution.isolation import IsolationContext
from benchmark.repositories.workspace import WorkspacePath


class TestMakeIsolationSharedSnapshot:
    """KAGGLE-SMOKE-V2: shared snapshot storage accepted for every arm."""

    @staticmethod
    def _make_shared_topology(tmp_path: Path) -> tuple[Path, Path, Path]:
        """Build shared storage + a staged snapshot + a child arm workspace."""
        storage = tmp_path / "workspace" / "snapshots"
        active = storage / "todo" / "todo-smoke-001"
        active.mkdir(parents=True)
        (active / "todo" / "models.py").parent.mkdir(parents=True)
        (active / "todo" / "models.py").write_text("class Task: pass\n")
        arm_ws = tmp_path / "workspace" / "monolithic"
        return storage, active, arm_ws

    def test_shared_snapshot_accepted_for_all_three_arm_workspaces(self, tmp_path: Path) -> None:
        from seven_arm_benchmark import make_isolation

        storage, active, _ = self._make_shared_topology(tmp_path)
        for strategy in ("monolithic", "selective", "iterative_repository_agent"):
            arm_ws = tmp_path / "workspace" / strategy
            isolation = make_isolation(
                arm_ws,
                active_snapshot_root=active,
                snapshot_storage_root=storage,
            )
            report = isolation.verify()
            assert report.passed, f"{strategy}: {report.message}"
            assert isolation.snapshot_base == storage.resolve()

    def test_active_snapshot_strict_descendant_of_declared_storage(self, tmp_path: Path) -> None:
        from seven_arm_benchmark import make_isolation

        storage, active, arm_ws = self._make_shared_topology(tmp_path)
        isolation = make_isolation(
            arm_ws,
            active_snapshot_root=active,
            snapshot_storage_root=storage,
        )
        rel = isolation.active_snapshot_root.resolve().relative_to(
            isolation.snapshot_base.resolve()
        )
        assert rel != Path(".")
        assert rel.parts, "active snapshot must be a strict descendant"

    def test_default_arm_snapshots_base_rejects_shared_active(self, tmp_path: Path) -> None:
        """Without the explicit storage root the arm-local base must reject the shared active."""
        from seven_arm_benchmark import make_isolation

        storage, active, arm_ws = self._make_shared_topology(tmp_path)
        isolation = make_isolation(arm_ws, active_snapshot_root=active)
        report = isolation.verify()
        assert report.passed is False
        assert "outside" in report.message

    def test_outside_prefix_sibling_still_fails(self, tmp_path: Path) -> None:
        from seven_arm_benchmark import make_isolation

        storage = tmp_path / "workspace" / "snapshots"
        storage.mkdir(parents=True)
        sibling = tmp_path / "workspace" / "snapshots-extra" / "repo" / "rev1"
        sibling.mkdir(parents=True)
        arm_ws = tmp_path / "workspace" / "monolithic"
        isolation = make_isolation(
            arm_ws,
            active_snapshot_root=sibling,
            snapshot_storage_root=storage,
        )
        report = isolation.verify()
        assert report.passed is False

    def test_workspace_source_populated_from_immutable_active_snapshot(self, tmp_path: Path) -> None:
        from seven_arm_benchmark import make_isolation

        storage, active, arm_ws = self._make_shared_topology(tmp_path)
        make_isolation(
            arm_ws,
            active_snapshot_root=active,
            snapshot_storage_root=storage,
        )
        assert (arm_ws / "todo" / "models.py").is_file()
        assert (arm_ws / "todo" / "models.py").read_text() == "class Task: pass\n"

    def test_snapshot_storage_root_without_active_snapshot(self, tmp_path: Path) -> None:
        from seven_arm_benchmark import make_isolation

        storage = tmp_path / "workspace" / "snapshots"
        storage.mkdir(parents=True)
        arm_ws = tmp_path / "workspace" / "monolithic"
        isolation = make_isolation(arm_ws, snapshot_storage_root=storage)
        assert isolation.snapshot_base == storage.resolve()
        assert isolation.verify().passed


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
