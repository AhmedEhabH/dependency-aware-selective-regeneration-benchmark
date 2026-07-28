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


@dataclass(frozen=True)
class _ValidatedPostGenerationRequest:
    workspace_root: Path
    migration_directory_path: Path
    migration_directory_relative: str
    command: tuple[str, ...]
    require_new_migration: bool
    timeout: int


@dataclass(frozen=True)
class _MigrationSnapshot:
    trusted: bool
    hashes: dict[str, str]
    diagnostics: tuple[str, ...]


@dataclass(frozen=True)
class _CommandOutcome:
    succeeded: bool
    exit_code: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class _MigrationAssessment:
    passed: bool
    existing_unchanged: bool
    created_paths: tuple[str, ...]
    diagnostics: tuple[str, ...]


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
) -> _ValidatedPostGenerationRequest | str:
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

        resolved_workspace = wr.resolve()
        mig_dir_rel = migration_directory.replace("\\", "/")
        mig_path = resolved_workspace / mig_dir_rel

        resolved = mig_path.resolve()
        rel = _relative_to_root(resolved, resolved_workspace)
        if rel is None:
            return "migration_directory does not resolve under workspace_root"

        return _ValidatedPostGenerationRequest(
            workspace_root=resolved_workspace,
            migration_directory_path=mig_path,
            migration_directory_relative=mig_dir_rel,
            command=tuple(command),
            require_new_migration=require_new_migration,
            timeout=timeout,
        )
    except (OSError, RuntimeError, ValueError, TypeError) as exc:
        return f"workspace validation error: {exc}"


def _take_migration_snapshot(
    request: _ValidatedPostGenerationRequest,
) -> _MigrationSnapshot:
    mig_dir = request.migration_directory_path
    hashes: dict[str, str] = {}
    diagnostics: list[str] = []

    if not mig_dir.exists():
        diagnostics.append("migration directory does not exist")
        return _MigrationSnapshot(trusted=False, hashes={}, diagnostics=tuple(diagnostics))

    try:
        resolved = mig_dir.resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as exc:
        diagnostics.append(f"migration directory resolution error: {exc}")
        return _MigrationSnapshot(trusted=False, hashes={}, diagnostics=tuple(diagnostics))

    if not resolved.is_dir():
        diagnostics.append("migration directory is not a directory")
        return _MigrationSnapshot(trusted=False, hashes={}, diagnostics=tuple(diagnostics))

    if resolved.is_symlink():
        rel = _relative_to_root(mig_dir, request.workspace_root)
        diagnostics.append(
            f"migration directory is a symlink: {rel or mig_dir.name}"
        )
        return _MigrationSnapshot(trusted=False, hashes={}, diagnostics=tuple(diagnostics))

    ws_rel = _relative_to_root(resolved, request.workspace_root)
    if ws_rel is None:
        rel = _relative_to_root(mig_dir, request.workspace_root)
        diagnostics.append(
            f"migration directory resolves outside workspace: {rel or mig_dir.name}"
        )
        return _MigrationSnapshot(trusted=False, hashes={}, diagnostics=tuple(diagnostics))

    try:
        entries = sorted(resolved.iterdir(), key=lambda e: e.name)
    except (OSError, RuntimeError) as exc:
        diagnostics.append(f"migration directory listing error: {exc}")
        return _MigrationSnapshot(trusted=False, hashes={}, diagnostics=tuple(diagnostics))

    trusted = True
    for entry in entries:
        try:
            if entry.suffix != ".py":
                continue

            if entry.is_symlink():
                rel_entry = _relative_to_root(entry, request.workspace_root)
                diagnostics.append(
                    f"migration file symlink is not allowed: {rel_entry or entry.name}"
                )
                trusted = False
                continue

            if not entry.is_file():
                rel_entry = _relative_to_root(entry, request.workspace_root)
                diagnostics.append(
                    f"migration entry is not a regular file: {rel_entry or entry.name}"
                )
                trusted = False
                continue

            resolved_entry = entry.resolve(strict=True)

            if resolved_entry.parent != resolved:
                rel_entry = _relative_to_root(entry, request.workspace_root)
                diagnostics.append(
                    f"migration file resolves outside migration directory: "
                    f"{rel_entry or entry.name}"
                )
                trusted = False
                continue

            rel = _relative_to_root(resolved_entry, request.workspace_root)
            if rel is None:
                rel_entry = _relative_to_root(entry, request.workspace_root)
                diagnostics.append(
                    f"migration file resolves outside workspace: "
                    f"{rel_entry or entry.name}"
                )
                trusted = False
                continue

            hashes[rel] = _sha256(resolved_entry)

        except (OSError, RuntimeError, ValueError) as exc:
            rel_entry = _relative_to_root(entry, request.workspace_root)
            diagnostics.append(
                f"failed to inspect migration file {rel_entry or entry.name}: {exc}"
            )
            trusted = False

    return _MigrationSnapshot(
        trusted=trusted,
        hashes=hashes,
        diagnostics=tuple(diagnostics),
    )


def _run_command(
    request: _ValidatedPostGenerationRequest,
) -> _CommandOutcome:
    try:
        proc = subprocess.run(
            list(request.command),
            cwd=str(request.workspace_root),
            capture_output=True,
            text=True,
            timeout=request.timeout,
        )
        return _CommandOutcome(
            succeeded=proc.returncode == 0,
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )
    except subprocess.TimeoutExpired as e:
        stdout = _coerce_subprocess_text(e.stdout)
        stderr = _coerce_subprocess_text(e.stderr)
        if stderr:
            stderr += "\n"
        stderr += "Command timed out"
        return _CommandOutcome(
            succeeded=False,
            exit_code=-1,
            stdout=stdout,
            stderr=stderr,
        )
    except FileNotFoundError:
        return _CommandOutcome(
            succeeded=False,
            exit_code=-1,
            stdout="",
            stderr=f"Command not found: {request.command[0]}",
        )
    except ValueError as exc:
        return _CommandOutcome(
            succeeded=False,
            exit_code=-1,
            stdout="",
            stderr=f"Invalid subprocess argument: {exc}",
        )
    except OSError as e:
        return _CommandOutcome(
            succeeded=False,
            exit_code=-1,
            stdout="",
            stderr=f"OS error: {e}",
        )
    except subprocess.SubprocessError as e:
        return _CommandOutcome(
            succeeded=False,
            exit_code=-1,
            stdout="",
            stderr=f"Subprocess error: {e}",
        )


def _assess_migration_change(
    request: _ValidatedPostGenerationRequest,
    before: _MigrationSnapshot,
    after: _MigrationSnapshot,
) -> _MigrationAssessment:
    diagnostics: list[str] = list(before.diagnostics)
    diagnostics.extend(after.diagnostics)

    if not after.trusted:
        return _MigrationAssessment(
            passed=False,
            existing_unchanged=False,
            created_paths=(),
            diagnostics=tuple(diagnostics),
        )

    existing_unchanged = True
    for old_path, old_hash in before.hashes.items():
        if old_path not in after.hashes:
            existing_unchanged = False
            diagnostics.append(f"old migration deleted: {old_path}")
        elif after.hashes[old_path] != old_hash:
            existing_unchanged = False
            diagnostics.append(f"old migration modified: {old_path}")

    mig_dir_rel = request.migration_directory_relative
    before_set = set(before.hashes.keys())
    after_set = set(after.hashes.keys())
    new_paths = sorted(after_set - before_set)

    created_list: list[str] = []
    for p in new_paths:
        parts = p.split("/")
        if len(parts) != len(mig_dir_rel.split("/")) + 1:
            continue
        if not p.startswith(mig_dir_rel + "/"):
            continue
        filename = parts[-1]
        if NUMBERED_MIGRATION_RE.match(filename):
            created_list.append(p)
    created_paths = tuple(created_list)

    passed = before.trusted and existing_unchanged
    if request.require_new_migration and len(created_paths) != 1:
        passed = False
        if len(created_paths) == 0:
            diagnostics.append("expected exactly one new migration, got zero")
        else:
            diagnostics.append(
                f"expected exactly one new migration, got {len(created_paths)}"
            )

    return _MigrationAssessment(
        passed=passed,
        existing_unchanged=existing_unchanged,
        created_paths=created_paths,
        diagnostics=tuple(diagnostics),
    )


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

    request = validation_result

    before = _take_migration_snapshot(request)
    if not before.trusted:
        duration = time.monotonic() - start
        stderr = "\n".join(before.diagnostics)
        return PostGenerationResult(
            passed=False,
            exit_code=-1,
            stdout="",
            stderr=stderr,
            duration_seconds=duration,
        )

    command_outcome = _run_command(request)
    after = _take_migration_snapshot(request)
    assessment = _assess_migration_change(request, before, after)

    passed = command_outcome.succeeded and assessment.passed

    if not command_outcome.succeeded:
        exit_code = command_outcome.exit_code
    elif passed:
        exit_code = 0
    else:
        exit_code = -1

    full_stderr = command_outcome.stderr
    if assessment.diagnostics:
        full_stderr += "\n[post-generation validation]\n" + "\n".join(assessment.diagnostics)

    duration = time.monotonic() - start
    return PostGenerationResult(
        passed=passed,
        exit_code=exit_code,
        stdout=command_outcome.stdout,
        stderr=full_stderr,
        duration_seconds=duration,
        created_paths=assessment.created_paths,
        existing_migrations_unchanged=assessment.existing_unchanged,
    )
