import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from benchmark.execution.post_generation import (
    _assess_migration_change,
    _coerce_subprocess_text,
    _MigrationSnapshot,
    _relative_to_root,
    _run_command,
    _take_migration_snapshot,
    _ValidatedPostGenerationRequest,
    run_post_generation_command,
)


def _create_migration_dir(base: Path, files: dict[str, str] | None = None) -> Path:
    mig = base / "todo" / "migrations"
    mig.mkdir(parents=True, exist_ok=True)
    if files:
        for name, content in files.items():
            (mig / name).write_text(content)
    return mig


def _smoke_command() -> list[str]:
    code = (
        "import pathlib; p = pathlib.Path('todo/migrations'); "
        "n = len([f for f in p.iterdir() if f.suffix == '.py' "
        "and f.name != '__init__.py']); "
        "(p / '0001_auto.py').write_text(f'# migration {n+1}')"
    )
    return [sys.executable, "-c", code]


# =============================================================================
# TestInputValidation
# =============================================================================


class TestInputValidation:
    def test_workspace_root_none_fails(self, tmp_path: Path) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        result = run_post_generation_command(
            workspace_root=None,  # type: ignore[arg-type]
            command=[sys.executable, "-c", "exit(0)"],
            require_new_migration=False,
            timeout=10,
        )
        assert result.passed is False
        assert result.exit_code == -1

    def test_missing_workspace_fails(self, tmp_path: Path) -> None:
        missing = tmp_path / "does_not_exist"
        result = run_post_generation_command(
            workspace_root=missing,
            command=[sys.executable, "-c", "exit(0)"],
            require_new_migration=False,
            timeout=10,
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert "does not exist" in result.stderr

    def test_workspace_path_is_file_fails(self, tmp_path: Path) -> None:
        f = tmp_path / "afile.txt"
        f.write_text("not a dir")
        result = run_post_generation_command(
            workspace_root=f,
            command=[sys.executable, "-c", "exit(0)"],
            require_new_migration=False,
            timeout=10,
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert "not a directory" in result.stderr

    def test_empty_command_fails(self, tmp_path: Path) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[],
            require_new_migration=False,
            timeout=10,
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert "empty" in result.stderr

    def test_command_with_empty_item_fails(self, tmp_path: Path) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=["python", ""],
            require_new_migration=False,
            timeout=10,
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert "empty" in result.stderr

    def test_whitespace_only_command_item_fails(self, tmp_path: Path) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=["python", "  "],
            require_new_migration=False,
            timeout=10,
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert "empty" in result.stderr

    def test_plain_string_command_fails(self, tmp_path: Path) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command="python -c exit(0)",  # type: ignore[arg-type]
            require_new_migration=False,
            timeout=10,
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert "non-string sequence" in result.stderr

    def test_bytes_command_fails(self, tmp_path: Path) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=b"python -c exit(0)",  # type: ignore[arg-type]
            require_new_migration=False,
            timeout=10,
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert "non-string sequence" in result.stderr

    def test_non_bool_require_new_migration_fails(self, tmp_path: Path) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", "exit(0)"],
            require_new_migration=1,  # type: ignore[arg-type]
            timeout=10,
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert "bool" in result.stderr

    @pytest.mark.parametrize(
        "bad_timeout",
        [
            None,
            True,
            False,
            1.5,
            "1",
            [],
            {},
            object(),
            0,
            -1,
        ],
    )
    def test_invalid_timeout_types_fail_closed(
        self, tmp_path: Path, bad_timeout: object
    ) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", "exit(0)"],
            require_new_migration=False,
            timeout=bad_timeout,  # type: ignore[arg-type]
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert isinstance(result.stdout, str)
        assert isinstance(result.stderr, str)
        assert result.duration_seconds >= 0
        assert "positive integer" in result.stderr

    def test_zero_timeout_fails(self, tmp_path: Path) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", "exit(0)"],
            require_new_migration=False,
            timeout=0,
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert "positive integer" in result.stderr

    def test_negative_timeout_fails(self, tmp_path: Path) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", "exit(0)"],
            require_new_migration=False,
            timeout=-1,
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert "positive integer" in result.stderr

    def test_timeout_1_succeeds(self, tmp_path: Path) -> None:
        _create_migration_dir(
            tmp_path, {"__init__.py": "# init", "0001_initial.py": "# old"}
        )
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=_smoke_command(),
            require_new_migration=True,
            timeout=30,
        )
        assert result.passed is True

    def test_absolute_migration_directory_fails(self, tmp_path: Path) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", "exit(0)"],
            require_new_migration=False,
            timeout=10,
            migration_directory="/todo/migrations",
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert "absolute" in result.stderr

    def test_traversal_migration_directory_fails(self, tmp_path: Path) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", "exit(0)"],
            require_new_migration=False,
            timeout=10,
            migration_directory="todo/../etc/migrations",
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert ".." in result.stderr

    def test_backslash_migration_directory_fails(self, tmp_path: Path) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", "exit(0)"],
            require_new_migration=False,
            timeout=10,
            migration_directory="todo\\migrations",
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert "backslash" in result.stderr

    def test_missing_migration_directory_fails(self, tmp_path: Path) -> None:
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", "exit(0)"],
            require_new_migration=False,
            timeout=10,
            migration_directory="todo/migrations",
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert "does not exist" in result.stderr

    @pytest.mark.parametrize(
        "bad_path",
        [
            "",
            " ",
            "   ",
            "\t",
            "\n",
        ],
    )
    def test_whitespace_only_migration_directory_fails(
        self, tmp_path: Path, bad_path: str
    ) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", "exit(0)"],
            require_new_migration=False,
            timeout=10,
            migration_directory=bad_path,
        )
        assert result.passed is False
        assert result.exit_code == -1

    def test_command_item_with_nul_fails(self, tmp_path: Path) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=["bad\x00name"],
            require_new_migration=False,
            timeout=10,
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert "NUL" in result.stderr

    def test_migration_directory_with_nul_fails(self, tmp_path: Path) -> None:
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", "exit(0)"],
            require_new_migration=False,
            timeout=10,
            migration_directory="todo/\x00migrations",
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert "NUL" in result.stderr

    def test_relative_workspace_root_is_supported(self, tmp_path: Path) -> None:
        _create_migration_dir(
            tmp_path, {"__init__.py": "# init", "0001_initial.py": "# old"}
        )
        cwd = os.getcwd()
        try:
            os.chdir(tmp_path.parent)
            rel = Path(os.path.basename(str(tmp_path)))
            result = run_post_generation_command(
                workspace_root=rel,
                command=_smoke_command(),
                require_new_migration=True,
                timeout=30,
                migration_directory="todo/migrations",
            )
            assert result.passed is True
            assert len(result.created_paths) == 1
            for p in result.created_paths:
                assert not p.startswith("/")
                assert "\\" not in p
                assert p == p.replace("\\", "/")
                assert p.startswith("todo/migrations/")
        finally:
            os.chdir(cwd)


# =============================================================================
# TestTrustedMigrationSnapshot
# =============================================================================


class TestTrustedMigrationSnapshot:
    def _make_request(self, tmp_path: Path) -> _ValidatedPostGenerationRequest:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        wr = tmp_path.resolve()
        return _ValidatedPostGenerationRequest(
            workspace_root=wr,
            migration_directory_path=wr / "todo" / "migrations",
            migration_directory_relative="todo/migrations",
            command=(sys.executable, "-c", "exit(0)"),
            require_new_migration=False,
            timeout=10,
        )

    def test_ordinary_directory(self, tmp_path: Path) -> None:
        req = self._make_request(tmp_path)
        snap = _take_migration_snapshot(req)
        assert snap.trusted is True
        assert len(snap.hashes) >= 1
        assert len(snap.diagnostics) == 0

    def test_missing_directory(self, tmp_path: Path) -> None:
        req = self._make_request(tmp_path)
        mig_path = req.migration_directory_path
        import shutil
        shutil.rmtree(mig_path)
        snap = _take_migration_snapshot(req)
        assert snap.trusted is False
        assert "does not exist" in " ".join(snap.diagnostics)

    def test_directory_becomes_missing_after_command(self, tmp_path: Path) -> None:
        req = self._make_request(tmp_path)
        import shutil
        shutil.rmtree(req.migration_directory_path)
        snap = _take_migration_snapshot(req)
        assert snap.trusted is False
        assert "does not exist" in " ".join(snap.diagnostics)

    def test_empty_directory_becomes_missing(self, tmp_path: Path) -> None:
        _create_migration_dir(tmp_path, {})
        wr = tmp_path.resolve()
        req = _ValidatedPostGenerationRequest(
            workspace_root=wr,
            migration_directory_path=wr / "todo" / "migrations",
            migration_directory_relative="todo/migrations",
            command=(sys.executable, "-c", "exit(0)"),
            require_new_migration=False,
            timeout=10,
        )
        import shutil
        shutil.rmtree(req.migration_directory_path)
        snap = _take_migration_snapshot(req)
        assert snap.trusted is False
        assert "does not exist" in " ".join(snap.diagnostics)

    def test_directory_path_is_file(self, tmp_path: Path) -> None:
        req = self._make_request(tmp_path)
        mig_path = req.migration_directory_path
        import shutil
        shutil.rmtree(mig_path)
        mig_path.write_text("not a directory")
        snap = _take_migration_snapshot(req)
        assert snap.trusted is False

    def test_directory_symlink(self, tmp_path: Path) -> None:
        try:
            (tmp_path / "_sym_probe").symlink_to(tmp_path)
            (tmp_path / "_sym_probe").unlink()
        except OSError:
            pytest.skip("symlink not supported on this platform")
        outside = tmp_path / "outside_mig"
        outside.mkdir()
        (outside / "__init__.py").write_text("# outside")
        ws = tmp_path / "ws"
        ws.mkdir()
        link = ws / "todo" / "migrations"
        link.parent.mkdir(parents=True)
        link.symlink_to(outside, target_is_directory=True)
        wr = ws.resolve()
        req = _ValidatedPostGenerationRequest(
            workspace_root=wr,
            migration_directory_path=wr / "todo" / "migrations",
            migration_directory_relative="todo/migrations",
            command=(sys.executable, "-c", "exit(0)"),
            require_new_migration=False,
            timeout=10,
        )
        snap = _take_migration_snapshot(req)
        assert snap.trusted is False

    def test_external_directory_symlink_at_resolve(self, tmp_path: Path) -> None:
        try:
            (tmp_path / "_sym_probe").symlink_to(tmp_path)
            (tmp_path / "_sym_probe").unlink()
        except OSError:
            pytest.skip("symlink not supported on this platform")
        outside = tmp_path / "outside_mig"
        outside.mkdir()
        (outside / "__init__.py").write_text("# outside")
        ws = tmp_path / "ws"
        ws.mkdir()
        inner = ws / "todo"
        inner.mkdir()
        link = inner / "migrations"
        link.symlink_to(outside, target_is_directory=True)
        wr = ws.resolve()
        req = _ValidatedPostGenerationRequest(
            workspace_root=wr,
            migration_directory_path=wr / "todo" / "migrations",
            migration_directory_relative="todo/migrations",
            command=(sys.executable, "-c", "exit(0)"),
            require_new_migration=False,
            timeout=10,
        )
        snap = _take_migration_snapshot(req)
        assert snap.trusted is False

    def test_file_symlink_rejected(self, tmp_path: Path) -> None:
        try:
            (tmp_path / "_sym_probe").symlink_to(tmp_path)
            (tmp_path / "_sym_probe").unlink()
        except OSError:
            pytest.skip("symlink not supported on this platform")
        mig = _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        target = tmp_path / "outside.py"
        target.write_text("# outside")
        link = mig / "0002_evil.py"
        link.symlink_to(target)
        req = self._make_request(tmp_path)
        snap = _take_migration_snapshot(req)
        assert snap.trusted is False
        assert "symlink" in " ".join(snap.diagnostics)

    def test_broken_symlink_rejected(self, tmp_path: Path) -> None:
        try:
            (tmp_path / "_sym_probe").symlink_to(tmp_path)
            (tmp_path / "_sym_probe").unlink()
        except OSError:
            pytest.skip("symlink not supported on this platform")
        mig = _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        link = mig / "0002_broken.py"
        link.symlink_to(tmp_path / "does_not_exist.py")
        req = self._make_request(tmp_path)
        snap = _take_migration_snapshot(req)
        assert snap.trusted is False

    def test_unreadable_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        import benchmark.execution.post_generation as pg
        original = pg._sha256

        def broken_sha256(path: Path) -> str:
            raise OSError("simulated read failure")

        monkeypatch.setattr(pg, "_sha256", broken_sha256)
        try:
            req = self._make_request(tmp_path)
            snap = _take_migration_snapshot(req)
            assert snap.trusted is False
            assert "failed to inspect" in " ".join(snap.diagnostics)
        finally:
            pg._sha256 = original

    def test_ordinary_numbered_file(self, tmp_path: Path) -> None:
        _create_migration_dir(
            tmp_path, {"__init__.py": "# init", "0001_initial.py": "# content"}
        )
        req = self._make_request(tmp_path)
        snap = _take_migration_snapshot(req)
        assert snap.trusted is True

    def test_ordinary_non_numbered_python_file(self, tmp_path: Path) -> None:
        _create_migration_dir(
            tmp_path, {"__init__.py": "# init", "helper.py": "# helper"}
        )
        req = self._make_request(tmp_path)
        snap = _take_migration_snapshot(req)
        assert snap.trusted is True

    def test_nested_python_file_ignored(self, tmp_path: Path) -> None:
        mig = _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        sub = mig / "sub"
        sub.mkdir()
        (sub / "nested.py").write_text("# nested")
        req = self._make_request(tmp_path)
        snap = _take_migration_snapshot(req)
        assert snap.trusted is True
        assert not any("nested" in k for k in snap.hashes)

    def test_non_python_file_ignored(self, tmp_path: Path) -> None:
        mig = _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        (mig / "data.txt").write_text("not python")
        req = self._make_request(tmp_path)
        snap = _take_migration_snapshot(req)
        assert snap.trusted is True

    def test_sibling_prefix_path_not_inside_workspace(self, tmp_path: Path) -> None:
        workspace = tmp_path / "prefix_work"
        workspace.mkdir()
        sibling = tmp_path / "prefix_work_extra"
        sibling.mkdir()
        assert _relative_to_root(sibling, workspace) is None

    def test_internal_directory_symlink(self, tmp_path: Path) -> None:
        try:
            (tmp_path / "_sym_probe").symlink_to(tmp_path)
            (tmp_path / "_sym_probe").unlink()
        except OSError:
            pytest.skip("symlink not supported on this platform")
        real_mig = tmp_path / "real_migrations"
        real_mig.mkdir()
        (real_mig / "__init__.py").write_text("# real")
        link = tmp_path / "todo" / "migrations"
        link.parent.mkdir(parents=True)
        link.symlink_to(real_mig, target_is_directory=True)
        wr = tmp_path.resolve()
        req = _ValidatedPostGenerationRequest(
            workspace_root=wr,
            migration_directory_path=wr / "todo" / "migrations",
            migration_directory_relative="todo/migrations",
            command=(sys.executable, "-c", "exit(0)"),
            require_new_migration=False,
            timeout=10,
        )
        snap = _take_migration_snapshot(req)
        assert snap.trusted is False
        assert "migration directory is a symlink" in " ".join(snap.diagnostics)


# =============================================================================
# TestCommandOutcome
# =============================================================================


class TestCommandOutcome:
    def _make_request(self, tmp_path: Path) -> _ValidatedPostGenerationRequest:
        wr = tmp_path.resolve()
        return _ValidatedPostGenerationRequest(
            workspace_root=wr,
            migration_directory_path=wr / "todo" / "migrations",
            migration_directory_relative="todo/migrations",
            command=(sys.executable, "-c", "exit(0)"),
            require_new_migration=False,
            timeout=10,
        )

    def test_success(self, tmp_path: Path) -> None:
        req = self._make_request(tmp_path)
        outcome = _run_command(req)
        assert outcome.succeeded is True
        assert outcome.exit_code == 0

    def test_non_zero(self, tmp_path: Path) -> None:
        req = _ValidatedPostGenerationRequest(
            workspace_root=tmp_path.resolve(),
            migration_directory_path=tmp_path / "todo" / "migrations",
            migration_directory_relative="todo/migrations",
            command=(sys.executable, "-c", "exit(42)"),
            require_new_migration=False,
            timeout=10,
        )
        outcome = _run_command(req)
        assert outcome.succeeded is False
        assert outcome.exit_code == 42

    def test_timeout_string_output(self, tmp_path: Path) -> None:
        req = _ValidatedPostGenerationRequest(
            workspace_root=tmp_path.resolve(),
            migration_directory_path=tmp_path / "todo" / "migrations",
            migration_directory_relative="todo/migrations",
            command=(sys.executable, "-c", "import time; time.sleep(10)"),
            require_new_migration=False,
            timeout=1,
        )
        outcome = _run_command(req)
        assert outcome.succeeded is False
        assert outcome.exit_code == -1
        assert "timed out" in outcome.stderr.lower()

    def test_command_not_found(self, tmp_path: Path) -> None:
        req = _ValidatedPostGenerationRequest(
            workspace_root=tmp_path.resolve(),
            migration_directory_path=tmp_path / "todo" / "migrations",
            migration_directory_relative="todo/migrations",
            command=("nonexistent_cmd_xyz123",),
            require_new_migration=False,
            timeout=10,
        )
        outcome = _run_command(req)
        assert outcome.succeeded is False
        assert outcome.exit_code == -1
        assert "not found" in outcome.stderr

    def test_value_error(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        def fake_run(*args: object, **kwargs: object) -> object:
            raise ValueError("bad value")

        monkeypatch.setattr("subprocess.run", fake_run)
        req = self._make_request(tmp_path)
        outcome = _run_command(req)
        assert outcome.succeeded is False
        assert outcome.exit_code == -1
        assert "bad value" in outcome.stderr

    def test_os_error(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        def fake_run(*args: object, **kwargs: object) -> object:
            raise OSError("os failure")

        monkeypatch.setattr("subprocess.run", fake_run)
        req = self._make_request(tmp_path)
        outcome = _run_command(req)
        assert outcome.succeeded is False
        assert outcome.exit_code == -1
        assert "OS error" in outcome.stderr

    def test_subprocess_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class FakeSubprocessError(subprocess.SubprocessError):
            pass

        def fake_run(*args: object, **kwargs: object) -> object:
            raise FakeSubprocessError("subprocess failure")

        monkeypatch.setattr("subprocess.run", fake_run)
        req = self._make_request(tmp_path)
        outcome = _run_command(req)
        assert outcome.succeeded is False
        assert outcome.exit_code == -1


# =============================================================================
# TestMigrationAssessment — invariant truth table
# =============================================================================


class TestMigrationAssessment:
    def _request(
        self, tmp_path: Path, require_new_migration: bool = False
    ) -> _ValidatedPostGenerationRequest:
        wr = tmp_path.resolve()
        return _ValidatedPostGenerationRequest(
            workspace_root=wr,
            migration_directory_path=wr / "todo" / "migrations",
            migration_directory_relative="todo/migrations",
            command=(sys.executable, "-c", "exit(0)"),
            require_new_migration=require_new_migration,
            timeout=10,
        )

    # Parametrized truth table from spec section 9.4
    # | Command | Before | After | Old unchanged | Required | Created | Final |
    # | success | yes    | yes   | yes           | yes      | 1       | pass  |
    @pytest.mark.parametrize(
        "before_trusted,after_trusted,before_hashes,after_hashes,require_new,created_count,expect_passed",
        [
            # row 1: everything ok, required=yes, created=1 → pass
            (True, True,
             {"todo/migrations/__init__.py": "a"},
             {"todo/migrations/__init__.py": "a", "todo/migrations/0001_a.py": "b"},
             True, 1, True),
            # row 2: everything ok, required=yes, created=0 → fail
            (True, True,
             {"todo/migrations/__init__.py": "a"},
             {"todo/migrations/__init__.py": "a"},
             True, 0, False),
            # row 3: everything ok, required=yes, created=2 → fail
            (True, True,
             {"todo/migrations/__init__.py": "a"},
             {"todo/migrations/__init__.py": "a", "todo/migrations/0001_a.py": "b", "todo/migrations/0002_b.py": "c"},
             True, 2, False),
            # row 4: everything ok, required=no, created=0 → pass
            (True, True,
             {"todo/migrations/__init__.py": "a"},
             {"todo/migrations/__init__.py": "a"},
             False, 0, True),
            # row 5: after untrusted, required=no → fail
            (True, False,
             {"todo/migrations/__init__.py": "a"},
             {},
             False, 0, False),
            # row 6: after untrusted, required=yes → fail
            (True, False,
             {"todo/migrations/__init__.py": "a"},
             {},
             True, 0, False),
            # row 7: old changed, required=no → fail
            (True, True,
             {"todo/migrations/__init__.py": "a"},
             {"todo/migrations/__init__.py": "b"},
             False, 0, False),
            # row 8: command failure, everything ok, required=no → pass (assessment passes)
            (True, True,
             {"todo/migrations/__init__.py": "a"},
             {"todo/migrations/__init__.py": "a"},
             False, 0, True),
            # row 9: command failure, old changed, required=no → fail
            (True, True,
             {"todo/migrations/__init__.py": "a"},
             {"todo/migrations/__init__.py": "b"},
             False, 0, False),
        ],
    )
    def test_assessment_truth_table(
        self,
        tmp_path: Path,
        before_trusted: bool,
        after_trusted: bool,
        before_hashes: dict[str, str],
        after_hashes: dict[str, str],
        require_new: bool,
        created_count: int,
        expect_passed: bool,
    ) -> None:
        req = self._request(tmp_path, require_new_migration=require_new)
        before = _MigrationSnapshot(
            trusted=before_trusted,
            hashes=before_hashes,
            diagnostics=(),
        )
        after = _MigrationSnapshot(
            trusted=after_trusted,
            hashes=after_hashes,
            diagnostics=(),
        )
        assessment = _assess_migration_change(req, before, after)
        assert assessment.passed is expect_passed

    def test_after_untrusted_unchanged_forced_false(self, tmp_path: Path) -> None:
        req = self._request(tmp_path)
        before = _MigrationSnapshot(
            trusted=True,
            hashes={"todo/migrations/__init__.py": "hash1"},
            diagnostics=(),
        )
        after = _MigrationSnapshot(
            trusted=False,
            hashes={"todo/migrations/__init__.py": "hash1"},
            diagnostics=("snapshot error",),
        )
        assessment = _assess_migration_change(req, before, after)
        assert assessment.passed is False
        assert assessment.existing_unchanged is False
        assert assessment.created_paths == ()
        assert "snapshot error" in assessment.diagnostics

    def test_existing_changed_detected(self, tmp_path: Path) -> None:
        req = self._request(tmp_path)
        before = _MigrationSnapshot(
            trusted=True,
            hashes={"todo/migrations/__init__.py": "hash1"},
            diagnostics=(),
        )
        after = _MigrationSnapshot(
            trusted=True,
            hashes={"todo/migrations/__init__.py": "hash2"},
            diagnostics=(),
        )
        assessment = _assess_migration_change(req, before, after)
        assert assessment.passed is False
        assert assessment.existing_unchanged is False
        assert "modified" in " ".join(assessment.diagnostics)

    def test_existing_deleted_detected(self, tmp_path: Path) -> None:
        req = self._request(tmp_path)
        before = _MigrationSnapshot(
            trusted=True,
            hashes={"todo/migrations/__init__.py": "hash1"},
            diagnostics=(),
        )
        after = _MigrationSnapshot(
            trusted=True,
            hashes={},
            diagnostics=(),
        )
        assessment = _assess_migration_change(req, before, after)
        assert assessment.passed is False
        assert assessment.existing_unchanged is False
        assert "deleted" in " ".join(assessment.diagnostics)

    def test_before_errors_in_diagnostics(self, tmp_path: Path) -> None:
        req = self._request(tmp_path)
        before = _MigrationSnapshot(
            trusted=True,
            hashes={},
            diagnostics=("before error",),
        )
        after = _MigrationSnapshot(
            trusted=True,
            hashes={},
            diagnostics=(),
        )
        assessment = _assess_migration_change(req, before, after)
        assert "before error" in assessment.diagnostics

    def test_after_errors_in_diagnostics(self, tmp_path: Path) -> None:
        req = self._request(tmp_path)
        before = _MigrationSnapshot(
            trusted=True,
            hashes={},
            diagnostics=(),
        )
        after = _MigrationSnapshot(
            trusted=True,
            hashes={},
            diagnostics=("after error",),
        )
        assessment = _assess_migration_change(req, before, after)
        assert "after error" in assessment.diagnostics

    def test_created_paths_preserved_when_after_untrusted(self, tmp_path: Path) -> None:
        req = self._request(tmp_path)
        before = _MigrationSnapshot(
            trusted=True,
            hashes={},
            diagnostics=(),
        )
        after = _MigrationSnapshot(
            trusted=False,
            hashes={"todo/migrations/0001_a.py": "hash"},
            diagnostics=(),
        )
        assessment = _assess_migration_change(req, before, after)
        assert assessment.created_paths == ("todo/migrations/0001_a.py",)
        assert assessment.passed is False
        assert assessment.existing_unchanged is False

    def test_synthetic_cross_platform_assessment(self, tmp_path: Path) -> None:
        req = self._request(tmp_path)
        before = _MigrationSnapshot(
            trusted=True,
            hashes={"todo/migrations/__init__.py": "a"},
            diagnostics=(),
        )
        after = _MigrationSnapshot(
            trusted=False,
            hashes={
                "todo/migrations/__init__.py": "a",
                "todo/migrations/0002_good.py": "b",
            },
            diagnostics=("unsafe entry",),
        )
        assessment = _assess_migration_change(req, before, after)
        assert assessment.passed is False
        assert assessment.existing_unchanged is False
        assert assessment.created_paths == ("todo/migrations/0002_good.py",)


# =============================================================================
# TestPublicOrchestration — production-path end-to-end
# =============================================================================


class TestPublicOrchestration:
    def test_valid_command_creates_one_migration_and_passes(
        self, tmp_path: Path
    ) -> None:
        _create_migration_dir(
            tmp_path, {"__init__.py": "# init", "0001_initial.py": "# old"}
        )
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=_smoke_command(),
            require_new_migration=True,
            timeout=30,
            migration_directory="todo/migrations",
        )
        assert result.passed is True
        assert result.exit_code == 0
        assert len(result.created_paths) == 1
        assert result.existing_migrations_unchanged is True

    def test_valid_migration_with_unsafe_file_symlink(
        self, tmp_path: Path
    ) -> None:
        try:
            (tmp_path / "_sym_probe").symlink_to(tmp_path)
            (tmp_path / "_sym_probe").unlink()
        except OSError:
            pytest.skip("symlink not supported on this platform")
        _create_migration_dir(
            tmp_path, {"__init__.py": "# init", "0001_initial.py": "# old"}
        )
        outside = tmp_path / "outside_target.py"
        outside.write_text("# outside target")
        code = (
            "import pathlib, os; "
            "p = pathlib.Path('todo/migrations'); "
            "(p / '0002_good.py').write_text('# good'); "
            "os.symlink("
            "str(pathlib.Path('..') / 'outside_target.py'), "
            "str(p / '0003_evil.py')"
            ")"
        )
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", code],
            require_new_migration=True,
            timeout=30,
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert result.created_paths == ("todo/migrations/0002_good.py",)
        assert result.existing_migrations_unchanged is False
        assert "symlink" in result.stderr

    def test_missing_migration_directory_after_command(
        self, tmp_path: Path
    ) -> None:
        _create_migration_dir(
            tmp_path, {"__init__.py": "# init", "0001_initial.py": "# old"}
        )
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[
                sys.executable,
                "-c",
                "import shutil; "
                "shutil.rmtree('todo/migrations')",
            ],
            require_new_migration=False,
            timeout=10,
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert result.existing_migrations_unchanged is False

    def test_empty_migration_directory_deleted_after_command_fails(
        self, tmp_path: Path
    ) -> None:
        _create_migration_dir(tmp_path, {})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[
                sys.executable,
                "-c",
                "import shutil; "
                "shutil.rmtree('todo/migrations')",
            ],
            require_new_migration=False,
            timeout=10,
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert result.existing_migrations_unchanged is False

    def test_timeout_after_old_file_modification(
        self, tmp_path: Path
    ) -> None:
        _create_migration_dir(
            tmp_path,
            {"__init__.py": "# init", "0001_initial.py": "# original"},
        )
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[
                sys.executable,
                "-c",
                "import pathlib, time; "
                "pathlib.Path('todo/migrations/0001_initial.py')"
                ".write_text('# modified'); "
                "time.sleep(10)",
            ],
            require_new_migration=False,
            timeout=2,
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert result.existing_migrations_unchanged is False
        assert "modified" in result.stderr.lower()

    def test_failed_command_after_creating_migration(
        self, tmp_path: Path
    ) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[
                sys.executable,
                "-c",
                "import pathlib; "
                "pathlib.Path('todo/migrations/0001_auto.py')"
                ".write_text('# new'); exit(1)",
            ],
            require_new_migration=False,
            timeout=10,
        )
        assert result.passed is False
        assert result.exit_code == 1
        assert "todo/migrations/0001_auto.py" in result.created_paths

    def test_relative_workspace(self, tmp_path: Path) -> None:
        _create_migration_dir(
            tmp_path, {"__init__.py": "# init", "0001_initial.py": "# old"}
        )
        cwd = os.getcwd()
        try:
            os.chdir(tmp_path.parent)
            rel = Path(os.path.basename(str(tmp_path)))
            result = run_post_generation_command(
                workspace_root=rel,
                command=_smoke_command(),
                require_new_migration=True,
                timeout=30,
                migration_directory="todo/migrations",
            )
            assert result.passed is True
            assert len(result.created_paths) == 1
        finally:
            os.chdir(cwd)

    def test_migration_directory_escape(self, tmp_path: Path) -> None:
        outside = tmp_path / "outside" / "migrations"
        outside.mkdir(parents=True)
        (outside / "__init__.py").write_text("# outside")
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        link = workspace / "todo" / "migrations"
        link.parent.mkdir(parents=True)
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError:
            pytest.skip("symlink not supported on this platform")
        result = run_post_generation_command(
            workspace_root=workspace,
            command=[sys.executable, "-c", "exit(0)"],
            require_new_migration=False,
            timeout=10,
            migration_directory="todo/migrations",
        )
        assert result.passed is False
        assert result.exit_code == -1

    def test_internal_directory_symlink_public_path(self, tmp_path: Path) -> None:
        try:
            (tmp_path / "_sym_probe").symlink_to(tmp_path)
            (tmp_path / "_sym_probe").unlink()
        except OSError:
            pytest.skip("symlink not supported on this platform")
        real_mig = tmp_path / "real_migrations"
        real_mig.mkdir()
        (real_mig / "__init__.py").write_text("# real")
        link = tmp_path / "todo" / "migrations"
        link.parent.mkdir(parents=True)
        link.symlink_to(real_mig, target_is_directory=True)
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", "exit(0)"],
            require_new_migration=False,
            timeout=10,
            migration_directory="todo/migrations",
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert result.existing_migrations_unchanged is False


# =============================================================================
# TestRegressionCases — existing public-API regression tests
# =============================================================================


class TestRegressionCases:
    def test_created_path_is_repository_relative_posix(
        self, tmp_path: Path
    ) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=_smoke_command(),
            require_new_migration=True,
        )
        assert result.passed is True
        for p in result.created_paths:
            assert not p.startswith("/")
            assert "\\" not in p
            assert p == p.replace("\\", "/")
            assert p.startswith("todo/migrations/")

    def test_created_paths_are_sorted(self, tmp_path: Path) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[
                sys.executable,
                "-c",
                textwrap.dedent(
                    """
                import pathlib
                p = pathlib.Path('todo/migrations')
                (p / '0002_b.py').write_text('# b')
                (p / '0001_a.py').write_text('# a')
            """
                ),
            ],
            require_new_migration=False,
        )
        assert result.passed is True
        assert result.created_paths == (
            "todo/migrations/0001_a.py",
            "todo/migrations/0002_b.py",
        )

    def test_existing_numbered_migrations_unchanged(self, tmp_path: Path) -> None:
        _create_migration_dir(
            tmp_path, {"__init__.py": "# init", "0001_initial.py": "# stable"}
        )
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=_smoke_command(),
            require_new_migration=True,
        )
        assert result.passed is True
        assert result.existing_migrations_unchanged is True

    def test_existing_init_py_unchanged(self, tmp_path: Path) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init content"})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=_smoke_command(),
            require_new_migration=True,
        )
        assert result.passed is True
        assert result.existing_migrations_unchanged is True

    def test_command_exits_non_zero_fails(self, tmp_path: Path) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", "exit(1)"],
            require_new_migration=False,
            timeout=10,
        )
        assert result.passed is False
        assert result.exit_code == 1

    def test_command_timeout_fails(self, tmp_path: Path) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", "import time; time.sleep(10)"],
            require_new_migration=False,
            timeout=1,
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert "timed out" in result.stderr.lower()

    def test_command_not_found_fails(self, tmp_path: Path) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=["nonexistent_cmd_xyz123"],
            require_new_migration=False,
            timeout=10,
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert "not found" in result.stderr

    def test_command_not_found_reports_unchanged_existing_migrations(
        self, tmp_path: Path
    ) -> None:
        _create_migration_dir(
            tmp_path, {"__init__.py": "# init", "0001_initial.py": "# old"}
        )
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=["nonexistent_cmd_xyz123"],
            require_new_migration=False,
            timeout=10,
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert result.existing_migrations_unchanged is True

    def test_modified_old_numbered_migration_fails(self, tmp_path: Path) -> None:
        _create_migration_dir(
            tmp_path,
            {"__init__.py": "# init", "0001_initial.py": "# original"},
        )
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[
                sys.executable,
                "-c",
                "import pathlib; "
                "pathlib.Path('todo/migrations/0001_initial.py')"
                ".write_text('# modified')",
            ],
            require_new_migration=False,
        )
        assert result.passed is False
        assert result.existing_migrations_unchanged is False

    def test_deleted_old_numbered_migration_fails(self, tmp_path: Path) -> None:
        _create_migration_dir(
            tmp_path, {"__init__.py": "# init", "0001_initial.py": "# old"}
        )
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[
                sys.executable,
                "-c",
                "import pathlib; "
                "pathlib.Path('todo/migrations/0001_initial.py').unlink()",
            ],
            require_new_migration=False,
            timeout=10,
        )
        assert result.passed is False
        assert result.existing_migrations_unchanged is False

    def test_modified_init_py_fails(self, tmp_path: Path) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# original init"})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[
                sys.executable,
                "-c",
                "import pathlib; "
                "pathlib.Path('todo/migrations/__init__.py')"
                ".write_text('# modified init')",
            ],
            require_new_migration=False,
        )
        assert result.passed is False
        assert result.existing_migrations_unchanged is False

    def test_zero_new_migrations_fails_when_required(self, tmp_path: Path) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", "exit(0)"],
            require_new_migration=True,
            timeout=10,
        )
        assert result.passed is False
        assert (
            "zero" in result.stderr
            or "0" in result.stderr
            or "expected" in result.stderr
        )

    def test_two_new_migrations_fail_when_required(self, tmp_path: Path) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[
                sys.executable,
                "-c",
                textwrap.dedent(
                    """
                import pathlib
                p = pathlib.Path('todo/migrations')
                (p / '0001_a.py').write_text('# a')
                (p / '0002_b.py').write_text('# b')
            """
                ),
            ],
            require_new_migration=True,
            timeout=10,
        )
        assert result.passed is False
        assert (
            "expected" in result.stderr or "got 2" in result.stderr
        )

    def test_one_new_migration_passes_when_required(self, tmp_path: Path) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=_smoke_command(),
            require_new_migration=True,
            timeout=30,
        )
        assert result.passed is True
        assert len(result.created_paths) == 1

    def test_no_new_migration_may_pass_when_not_required(
        self, tmp_path: Path
    ) -> None:
        _create_migration_dir(
            tmp_path, {"__init__.py": "# init", "0001_initial.py": "# old"}
        )
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", "exit(0)"],
            require_new_migration=False,
            timeout=10,
        )
        assert result.passed is True
        assert len(result.created_paths) == 0

    def test_new_init_py_not_counted_as_numbered_migration(
        self, tmp_path: Path
    ) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# original"})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[
                sys.executable,
                "-c",
                textwrap.dedent(
                    """
                import pathlib
                p = pathlib.Path('todo/migrations')
                (p / '__init__.py').write_text('# modified')
            """
                ),
            ],
            require_new_migration=True,
            timeout=10,
        )
        assert result.passed is False
        assert len(result.created_paths) == 0

    def test_nested_py_file_not_counted(self, tmp_path: Path) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[
                sys.executable,
                "-c",
                textwrap.dedent(
                    """
                import pathlib
                p = pathlib.Path('todo/migrations/sub')
                p.mkdir(exist_ok=True)
                (p / 'helper.py').write_text('# nested')
            """
                ),
            ],
            require_new_migration=False,
            timeout=10,
        )
        assert result.passed is True
        for cp in result.created_paths:
            assert "sub/helper.py" not in cp

    def test_new_non_python_file_not_counted(self, tmp_path: Path) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[
                sys.executable,
                "-c",
                "import pathlib; "
                "pathlib.Path('todo/migrations/data.txt')"
                ".write_text('not a migration')",
            ],
            require_new_migration=False,
            timeout=10,
        )
        assert result.passed is True

    def test_duration_is_non_negative_for_success(self, tmp_path: Path) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", "exit(0)"],
            require_new_migration=False,
            timeout=10,
        )
        assert result.duration_seconds >= 0

    def test_duration_is_non_negative_for_failure(self, tmp_path: Path) -> None:
        result = run_post_generation_command(
            workspace_root=tmp_path / "nonexistent",
            command=[sys.executable, "-c", "exit(0)"],
            require_new_migration=False,
            timeout=10,
        )
        assert result.duration_seconds >= 0

    def test_smoke_command_shape_tuple(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})

        call_kwargs: dict = {}

        def fake_run(*args: object, **kwargs: object) -> object:
            call_kwargs["popenargs"] = args
            call_kwargs.update(kwargs)
            from subprocess import CompletedProcess

            return CompletedProcess(
                list(args[0] if args else []),
                0,
                "",
                "",
            )

        monkeypatch.setattr("subprocess.run", fake_run)

        command_tuple = (
            "python",
            "manage.py",
            "makemigrations",
            "todo",
            "--noinput",
        )
        run_post_generation_command(
            workspace_root=tmp_path,
            command=command_tuple,
            require_new_migration=False,
            timeout=10,
        )

        assert call_kwargs.get("popenargs") == (list(command_tuple),)
        assert Path(call_kwargs.get("cwd", "")).resolve() == Path(
            tmp_path
        ).resolve()
        assert call_kwargs.get("capture_output") is True
        assert call_kwargs.get("text") is True
        assert call_kwargs.get("timeout") == 10
        assert "shell" not in call_kwargs or not call_kwargs["shell"]

    def test_numbered_migration_filename_validation(
        self, tmp_path: Path
    ) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[
                sys.executable,
                "-c",
                "import pathlib; "
                "pathlib.Path('todo/migrations/0001.py')"
                ".write_text('# no stem')",
            ],
            require_new_migration=True,
            timeout=10,
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert len(result.created_paths) == 0

    def test_non_numbered_python_file_does_not_satisfy_required_migration(
        self, tmp_path: Path
    ) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[
                sys.executable,
                "-c",
                "import pathlib; "
                "pathlib.Path('todo/migrations/helper.py')"
                ".write_text('# helper')",
            ],
            require_new_migration=True,
            timeout=10,
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert len(result.created_paths) == 0

    def test_existing_non_numbered_python_file_integrity_protected(
        self, tmp_path: Path
    ) -> None:
        _create_migration_dir(
            tmp_path,
            {
                "__init__.py": "# init",
                "helper.py": "# helper",
                "0001_initial.py": "# stable",
            },
        )
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[
                sys.executable,
                "-c",
                "import pathlib; "
                "pathlib.Path('todo/migrations/helper.py')"
                ".write_text('# modified helper')",
            ],
            require_new_migration=False,
            timeout=10,
        )
        assert result.passed is False
        assert result.existing_migrations_unchanged is False
        assert "helper.py" in result.stderr

    def test_timeout_without_changes_reports_unchanged(
        self, tmp_path: Path
    ) -> None:
        _create_migration_dir(
            tmp_path, {"__init__.py": "# init", "0001_initial.py": "# old"}
        )
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", "import time; time.sleep(10)"],
            require_new_migration=False,
            timeout=1,
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert result.existing_migrations_unchanged is True

    def test_subprocess_error_after_creating_migration_detects_integrity(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _create_migration_dir(
            tmp_path, {"__init__.py": "# init", "0001_initial.py": "# old"}
        )
        calls = 0

        def fake_run(*args: object, **kwargs: object) -> object:
            nonlocal calls
            calls += 1
            import pathlib
            pathlib.Path(
                str(tmp_path / "todo" / "migrations" / "0001_initial.py")
            ).write_text("# modified by subprocess error")
            raise ValueError("bad")

        monkeypatch.setattr("subprocess.run", fake_run)

        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", "exit(0)"],
            require_new_migration=False,
            timeout=10,
        )
        assert result.passed is False
        assert result.existing_migrations_unchanged is False

    def test_snapshot_read_error_returns_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})

        import benchmark.execution.post_generation as pg

        original = pg._sha256

        def broken_sha256(path: Path) -> str:
            raise OSError("simulated read failure")

        monkeypatch.setattr(pg, "_sha256", broken_sha256)
        try:
            result = run_post_generation_command(
                workspace_root=tmp_path,
                command=[sys.executable, "-c", "exit(0)"],
                require_new_migration=False,
                timeout=10,
            )
        finally:
            pg._sha256 = original

        assert result.passed is False
        assert result.exit_code == -1

    def test_subprocess_created_external_symlink_forces_failure(
        self, tmp_path: Path
    ) -> None:
        _create_migration_dir(
            tmp_path, {"__init__.py": "# init", "0001_initial.py": "# old"}
        )
        outside = tmp_path / "outside_target.py"
        outside.write_text("# outside target")
        try:
            (tmp_path / "_symlink_probe").symlink_to(tmp_path)
            (tmp_path / "_symlink_probe").unlink()
        except OSError:
            pytest.skip("symlink not supported on this platform")

        code = (
            "import pathlib, os; "
            "p = pathlib.Path('todo/migrations'); "
            "(p / '0002_good.py').write_text('# good'); "
            "os.symlink("
            "str(pathlib.Path('..') / 'outside_target.py'), "
            "str(p / '0003_evil.py')"
            ")"
        )
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", code],
            require_new_migration=True,
            timeout=30,
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert result.created_paths == ("todo/migrations/0002_good.py",)
        assert result.existing_migrations_unchanged is False
        assert "symlink" in result.stderr

    def test_subprocess_created_symlink_when_migration_not_required(
        self, tmp_path: Path
    ) -> None:
        _create_migration_dir(
            tmp_path, {"__init__.py": "# init", "0001_initial.py": "# old"}
        )
        outside = tmp_path / "outside_target.py"
        outside.write_text("# outside target")
        try:
            (tmp_path / "_symlink_probe").symlink_to(tmp_path)
            (tmp_path / "_symlink_probe").unlink()
        except OSError:
            pytest.skip("symlink not supported on this platform")

        code = (
            "import pathlib, os; "
            "p = pathlib.Path('todo/migrations'); "
            "os.symlink("
            "str(pathlib.Path('..') / 'outside_target.py'), "
            "str(p / '0003_evil.py')"
            ")"
        )
        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", code],
            require_new_migration=False,
            timeout=30,
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert result.created_paths == ()
        assert result.existing_migrations_unchanged is False
        assert "symlink" in result.stderr

    def test_synthetic_after_snapshot_error_forces_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _create_migration_dir(
            tmp_path, {"__init__.py": "# init", "0001_initial.py": "# old"}
        )
        import benchmark.execution.post_generation as pg

        call_count = 0
        original_snapshot = pg._take_migration_snapshot

        def fake_snapshot(
            request: _ValidatedPostGenerationRequest,
        ) -> _MigrationSnapshot:
            nonlocal call_count
            call_count += 1
            after = original_snapshot(request)
            if call_count == 1:
                return after
            return _MigrationSnapshot(
                trusted=False,
                hashes=after.hashes,
                diagnostics=("simulated after-state inspection failure",),
            )

        monkeypatch.setattr(pg, "_take_migration_snapshot", fake_snapshot)

        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", "exit(0)"],
            require_new_migration=False,
            timeout=30,
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert result.existing_migrations_unchanged is False
        assert "simulated after-state inspection failure" in result.stderr

    def test_ordinary_numbered_migration_not_rejected_by_symlink_checks(
        self, tmp_path: Path
    ) -> None:
        mig = _create_migration_dir(
            tmp_path, {"__init__.py": "# init", "0001_initial.py": "# old"}
        )
        created = mig / "0002_normal.py"
        created.write_text("# new migration")
        assert not created.is_symlink()
        assert created.resolve().relative_to(tmp_path.resolve())

        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=_smoke_command(),
            require_new_migration=True,
            timeout=30,
        )
        assert result.passed is True

    def test_existing_migration_symlink_fails_before_command(
        self, tmp_path: Path
    ) -> None:
        outside = tmp_path / "outside"
        outside.mkdir()
        target = outside / "helper.py"
        target.write_text("# outside helper")

        mig = tmp_path / "todo" / "migrations"
        mig.mkdir(parents=True)
        init = mig / "__init__.py"
        init.write_text("# init")
        link = mig / "existing_link.py"
        try:
            link.symlink_to(target)
        except OSError:
            pytest.skip("symlink not supported on this platform")

        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", "exit(0)"],
            require_new_migration=False,
            timeout=10,
        )
        assert result.passed is False
        assert result.exit_code == -1
        assert "symlink" in result.stderr

    def test_broken_numbered_migration_symlink_fails_closed(
        self, tmp_path: Path
    ) -> None:
        _create_migration_dir(tmp_path, {"__init__.py": "# init"})
        mig = tmp_path / "todo" / "migrations"
        link = mig / "0002_broken.py"
        try:
            link.symlink_to(tmp_path / "does_not_exist.py")
        except OSError:
            pytest.skip("symlink not supported on this platform")

        result = run_post_generation_command(
            workspace_root=tmp_path,
            command=[sys.executable, "-c", "exit(0)"],
            require_new_migration=False,
            timeout=10,
        )
        assert result.passed is False
        assert result.exit_code == -1


# =============================================================================
# TestHelpers
# =============================================================================


class TestHelpers:
    def test_coerce_subprocess_text_none(self) -> None:
        assert _coerce_subprocess_text(None) == ""

    def test_coerce_subprocess_text_str(self) -> None:
        assert _coerce_subprocess_text("hello") == "hello"

    def test_coerce_subprocess_text_bytes(self) -> None:
        assert _coerce_subprocess_text(b"hello") == "hello"

    def test_relative_to_root_nested(self, tmp_path: Path) -> None:
        root = tmp_path / "base"
        root.mkdir()
        child = root / "sub" / "file.py"
        child.parent.mkdir()
        child.write_text("# test")
        assert _relative_to_root(child, root) == "sub/file.py"

    def test_relative_to_root_outside(self, tmp_path: Path) -> None:
        a = tmp_path / "a"
        a.mkdir()
        b = tmp_path / "b"
        b.mkdir()
        assert _relative_to_root(b, a) is None

    def test_sibling_prefix_path_not_inside(self, tmp_path: Path) -> None:
        workspace = tmp_path / "prefix_work"
        workspace.mkdir()
        sibling = tmp_path / "prefix_work_extra"
        sibling.mkdir()
        assert _relative_to_root(sibling, workspace) is None
