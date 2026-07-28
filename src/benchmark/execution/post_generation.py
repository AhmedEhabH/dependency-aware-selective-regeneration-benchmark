from __future__ import annotations

import hashlib
import re
import subprocess
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

NUMBERED_MIGRATION_RE = re.compile(r"^\d+_[A-Za-z0-9_]+\.py$")


@dataclass(frozen=True)
class PostGenerationResult:
    passed: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    created_paths: tuple[str, ...] = ()
    existing_migrations_unchanged: bool = False


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative_to_root(path: Path, root: Path) -> str | None:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return None


def _coerce_subprocess_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _validate_inputs(
    workspace_root: str | Path,
    command: Sequence[str],
    *,
    require_new_migration: bool,
    timeout: int,
    migration_directory: str,
) -> tuple[Path, Path] | str:
    try:
        if isinstance(command, (str, bytes)):
            return "command must be a non-string sequence of non-empty strings"
        if not isinstance(workspace_root, (str, Path)):
            return "workspace_root must be a string or Path"
        if type(timeout) is not int:
            return "timeout must be a positive integer"
        if timeout <= 0:
            return "timeout must be a positive integer"
        if not isinstance(require_new_migration, bool):
            return "require_new_migration must be a bool"
        if not isinstance(migration_directory, str) or not migration_directory.strip():
            return "migration_directory is not a valid POSIX path"
        if "\x00" in migration_directory:
            return "migration_directory must not contain NUL"
        if migration_directory.startswith("/"):
            return "migration_directory must not be absolute"
        if ".." in migration_directory.split("/"):
            return "migration_directory must not contain '..'"
        if "\\" in migration_directory:
            return "migration_directory must not contain backslash"
        if len(command) == 0:
            return "command is empty"
        for item in command:
            if not isinstance(item, str):
                return "command contains a non-string item"
            if not item.strip():
                return "command contains an empty item"
            if "\x00" in item:
                return "command item contains NUL"

        wr = Path(workspace_root)
        if not wr.exists():
            return "workspace_root does not exist"
        if not wr.is_dir():
            return "workspace_root is not a directory"

        workspace = wr.resolve()
        resolved = (workspace / migration_directory).resolve()
        rel = _relative_to_root(resolved, workspace)
        if rel is None:
            return "migration_directory does not resolve under workspace_root"
        if not resolved.exists():
            return "migration_directory does not exist"
        if not resolved.is_dir():
            return "migration_directory is not a directory"
        return (workspace, resolved)
    except (OSError, RuntimeError, ValueError, TypeError) as exc:
        return f"workspace validation error: {exc}"


def _snapshot_migrations(
    workspace_root: Path, migration_directory: str
) -> tuple[dict[str, str], tuple[str, ...]]:
    mig_dir = (workspace_root / migration_directory).resolve()
    result: dict[str, str] = {}
    errors: list[str] = []
    if not mig_dir.is_dir():
        return result, tuple(errors)
    for entry in sorted(mig_dir.iterdir()):
        try:
            if not entry.is_symlink() and entry.is_file() and entry.suffix == ".py":
                resolved = entry.resolve(strict=True)
                if resolved.parent != mig_dir.resolve():
                    errors.append(
                        f"migration file resolves outside migration directory: "
                        f"{_relative_to_root(entry, workspace_root)}"
                    )
                    continue
                rel = _relative_to_root(resolved, workspace_root)
                if rel is None:
                    errors.append(
                        f"migration file resolves outside workspace: "
                        f"{_relative_to_root(entry, workspace_root)}"
                    )
                    continue
                result[rel] = _sha256(resolved)
            elif entry.is_symlink() and entry.suffix == ".py":
                rel_entry = _relative_to_root(entry, workspace_root)
                errors.append(
                    f"migration file symlink is not allowed: {rel_entry or entry.name}"
                )
        except (OSError, RuntimeError, ValueError) as exc:
            rel_entry = _relative_to_root(entry, workspace_root)
            errors.append(
                f"failed to inspect migration file "
                f"{rel_entry or entry.name}: {exc}"
            )
    return result, tuple(errors)


def _created_numbered_migrations(
    before: dict[str, str],
    after: dict[str, str],
    mig_dir_rel: str,
) -> tuple[str, ...]:
    before_set = set(before.keys())
    after_set = set(after.keys())
    new_paths = sorted(after_set - before_set)

    filtered: list[str] = []
    for p in new_paths:
        parts = p.split("/")
        if len(parts) != len(mig_dir_rel.split("/")) + 1:
            continue
        if not p.startswith(mig_dir_rel + "/"):
            continue
        filename = parts[-1]
        if not NUMBERED_MIGRATION_RE.match(filename):
            continue
        filtered.append(p)

    return tuple(filtered)


def run_post_generation_command(
    workspace_root: str | Path,
    command: Sequence[str],
    *,
    require_new_migration: bool,
    timeout: int = 180,
    migration_directory: str = "todo/migrations",
) -> PostGenerationResult:
    start = time.monotonic()

    validation_result = _validate_inputs(
        workspace_root=workspace_root,
        command=command,
        require_new_migration=require_new_migration,
        timeout=timeout,
        migration_directory=migration_directory,
    )
    if isinstance(validation_result, str):
        duration = time.monotonic() - start
        return PostGenerationResult(
            passed=False,
            exit_code=-1,
            stdout="",
            stderr=validation_result,
            duration_seconds=duration,
        )

    workspace, _resolved = validation_result

    before, before_errors = _snapshot_migrations(workspace, migration_directory)
    if before_errors:
        duration = time.monotonic() - start
        stderr = "\n".join(before_errors)
        return PostGenerationResult(
            passed=False,
            exit_code=-1,
            stdout="",
            stderr=stderr,
            duration_seconds=duration,
        )

    cmd_exit_code: int = -1
    cmd_stdout: str = ""
    cmd_stderr: str = ""
    cmd_passed: bool = False

    try:
        proc = subprocess.run(
            list(command),
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        cmd_exit_code = proc.returncode
        cmd_stdout = proc.stdout
        cmd_stderr = proc.stderr
        cmd_passed = proc.returncode == 0
    except subprocess.TimeoutExpired as e:
        cmd_exit_code = -1
        cmd_stdout = _coerce_subprocess_text(e.stdout)
        cmd_stderr = _coerce_subprocess_text(e.stderr)
        if cmd_stderr:
            cmd_stderr += "\n"
        cmd_stderr += "Command timed out"
        cmd_passed = False
    except FileNotFoundError:
        cmd_exit_code = -1
        cmd_stdout = ""
        cmd_stderr = f"Command not found: {command[0]}"
        cmd_passed = False
    except ValueError as exc:
        cmd_exit_code = -1
        cmd_stdout = ""
        cmd_stderr = f"Invalid subprocess argument: {exc}"
        cmd_passed = False
    except OSError as e:
        cmd_exit_code = -1
        cmd_stdout = ""
        cmd_stderr = f"OS error: {e}"
        cmd_passed = False
    except subprocess.SubprocessError as e:
        cmd_exit_code = -1
        cmd_stdout = ""
        cmd_stderr = f"Subprocess error: {e}"
        cmd_passed = False

    after, after_errors = _snapshot_migrations(workspace, migration_directory)

    diagnostics: list[str] = list(after_errors)
    all_old_unchanged = not after_errors
    for old_path, old_hash in before.items():
        if old_path not in after:
            all_old_unchanged = False
            diagnostics.append(f"old migration deleted: {old_path}")
        elif after[old_path] != old_hash:
            all_old_unchanged = False
            diagnostics.append(f"old migration modified: {old_path}")

    mig_dir_rel = migration_directory.replace("\\", "/")
    created = _created_numbered_migrations(before, after, mig_dir_rel)

    if not cmd_passed:
        duration = time.monotonic() - start
        full_stderr = cmd_stderr
        if diagnostics:
            full_stderr += "\n[post-generation validation]\n" + "\n".join(diagnostics)
        return PostGenerationResult(
            passed=False,
            exit_code=cmd_exit_code,
            stdout=cmd_stdout,
            stderr=full_stderr,
            duration_seconds=duration,
            created_paths=created,
            existing_migrations_unchanged=all_old_unchanged,
        )

    passed = all_old_unchanged
    if not all_old_unchanged:
        passed = False
    if require_new_migration and len(created) != 1:
        passed = False
        if len(created) == 0:
            diagnostics.append("expected exactly one new migration, got zero")
        else:
            diagnostics.append(
                f"expected exactly one new migration, got {len(created)}"
            )

    if not passed:
        cmd_exit_code = -1

    full_stderr = cmd_stderr
    if diagnostics:
        full_stderr += "\n[post-generation validation]\n" + "\n".join(diagnostics)

    duration = time.monotonic() - start
    return PostGenerationResult(
        passed=passed,
        exit_code=cmd_exit_code,
        stdout=cmd_stdout,
        stderr=full_stderr,
        duration_seconds=duration,
        created_paths=created,
        existing_migrations_unchanged=all_old_unchanged,
    )
