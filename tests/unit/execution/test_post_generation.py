import os
import sys
import textwrap
from pathlib import Path

import pytest

from benchmark.execution.post_generation import (
    _coerce_subprocess_text,
    _relative_to_root,
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


class TestPostGenerationResult:
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
        assert "greater than zero" in result.stderr

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
        assert "greater than zero" in result.stderr

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
                b"",
                b"",
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

    # --- New tests from R3B independent audit ---

    def test_relative_workspace_root_is_supported_without_exception(
        self, tmp_path: Path
    ) -> None:
        _create_migration_dir(
            tmp_path, {"__init__.py": "# init", "0001_initial.py": "# old"}
        )
        cwd = os.getcwd()
        try:
            os.chdir(tmp_path.parent)
            rel = Path(os.path.basename(tmp_path))
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

    def test_migration_directory_symlink_escape_fails_closed(
        self, tmp_path: Path
    ) -> None:
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
        assert "does not resolve" in result.stderr

    def test_sibling_prefix_path_is_not_treated_as_inside_workspace(
        self, tmp_path: Path
    ) -> None:
        workspace = tmp_path / "prefix_work"
        workspace.mkdir()
        sibling = tmp_path / "prefix_work_extra"
        sibling.mkdir()
        assert _relative_to_root(sibling, workspace) is None

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

    def test_numbered_migration_filename_is_required(
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

    def test_existing_non_numbered_python_file_is_still_integrity_protected(
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

    def test_timeout_without_changes_reports_existing_migrations_unchanged(
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

    def test_timeout_after_modifying_old_migration_detects_corruption(
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
        assert "modified" in result.stderr

    def test_failed_command_after_creating_migration_reports_created_path(
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

    def test_plain_string_command_fails_validation(
        self, tmp_path: Path
    ) -> None:
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

    def test_bytes_command_fails_validation(self, tmp_path: Path) -> None:
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
