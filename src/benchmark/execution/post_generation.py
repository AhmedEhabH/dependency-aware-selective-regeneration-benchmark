from __future__ import annotations

import hashlib
import subprocess
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


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


def _validate_inputs(
    workspace_root: str | Path,
    command: Sequence[str],
    *,
    require_new_migration: bool,
    timeout: int,
    migration_directory: str,
) -> str | None:
    wr = Path(workspace_root)
    if not wr.exists():
        return "workspace_root does not exist"
    if not wr.is_dir():
        return "workspace_root is not a directory"
    if len(command) == 0:
        return "command is empty"
    for item in command:
        if not isinstance(item, str) or len(item) == 0:
            return "command contains an empty item"
    if not isinstance(require_new_migration, bool):
        return "require_new_migration must be a bool"
    if timeout <= 0:
        return "timeout must be greater than zero"
    if not isinstance(migration_directory, str) or len(migration_directory) == 0:
        return "migration_directory is not a valid POSIX path"
    if migration_directory.startswith("/"):
        return "migration_directory must not be absolute"
    if ".." in migration_directory.split("/"):
        return "migration_directory must not contain '..'"
    if "\\" in migration_directory:
        return "migration_directory must not contain backslash"
    resolved = (wr / migration_directory).resolve()
    if not str(resolved).startswith(str(wr.resolve())):
        return "migration_directory does not resolve under workspace_root"
    if not resolved.exists():
        return "migration_directory does not exist"
    if not resolved.is_dir():
        return "migration_directory is not a directory"
    return None


def _snapshot_migrations(
    workspace_root: Path, migration_directory: str
) -> dict[str, str]:
    mig_dir = (workspace_root / migration_directory).resolve()
    result: dict[str, str] = {}
    if not mig_dir.is_dir():
        return result
    for entry in sorted(mig_dir.iterdir()):
        if entry.is_file() and entry.suffix == ".py":
            rel = entry.relative_to(workspace_root).as_posix()
            result[rel] = _sha256(entry)
    return result


def run_post_generation_command(
    workspace_root: str | Path,
    command: Sequence[str],
    *,
    require_new_migration: bool,
    timeout: int = 180,
    migration_directory: str = "todo/migrations",
) -> PostGenerationResult:
    start = time.monotonic()
    validation_error = _validate_inputs(
        workspace_root=workspace_root,
        command=command,
        require_new_migration=require_new_migration,
        timeout=timeout,
        migration_directory=migration_directory,
    )
    if validation_error is not None:
        duration = time.monotonic() - start
        return PostGenerationResult(
            passed=False,
            exit_code=-1,
            stdout="",
            stderr=validation_error,
            duration_seconds=duration,
        )

    wr = Path(workspace_root)

    before = _snapshot_migrations(wr, migration_directory)

    try:
        proc = subprocess.run(
            list(command),
            cwd=str(wr),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        cmd_exit_code = proc.returncode
        cmd_stdout = proc.stdout
        cmd_stderr = proc.stderr
        cmd_passed = proc.returncode == 0
    except subprocess.TimeoutExpired:
        duration = time.monotonic() - start
        return PostGenerationResult(
            passed=False,
            exit_code=-1,
            stdout="",
            stderr="Command timed out",
            duration_seconds=duration,
        )
    except FileNotFoundError:
        duration = time.monotonic() - start
        return PostGenerationResult(
            passed=False,
            exit_code=-1,
            stdout="",
            stderr=f"Command not found: {command[0]}",
            duration_seconds=duration,
        )
    except OSError as e:
        duration = time.monotonic() - start
        return PostGenerationResult(
            passed=False,
            exit_code=-1,
            stdout="",
            stderr=f"OS error: {e}",
            duration_seconds=duration,
        )

    after = _snapshot_migrations(wr, migration_directory)

    all_old_unchanged = True
    diagnostics: list[str] = []
    for old_path, old_hash in before.items():
        if old_path not in after:
            all_old_unchanged = False
            diagnostics.append(f"old migration deleted: {old_path}")
        elif after[old_path] != old_hash:
            all_old_unchanged = False
            diagnostics.append(f"old migration modified: {old_path}")

    before_set = set(before.keys())
    after_set = set(after.keys())
    new_paths = sorted(after_set - before_set)

    filtered_new: list[str] = []
    mig_dir_rel = migration_directory.replace("\\", "/")
    for p in new_paths:
        parts = p.split("/")
        if len(parts) != len(mig_dir_rel.split("/")) + 1:
            continue
        if not p.startswith(mig_dir_rel + "/"):
            continue
        if not p.endswith(".py"):
            continue
        filename = parts[-1]
        if filename == "__init__.py":
            continue
        filtered_new.append(p)

    created = tuple(filtered_new)

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
