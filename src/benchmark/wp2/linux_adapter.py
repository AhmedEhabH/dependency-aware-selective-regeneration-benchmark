"""WP-2 Linux filesystem / worktree adapter (amendment D, Mission 07 §5-6).

Historical Saleor commits contain filenames that are invalid on Windows (e.g.
``test_get_oembed_data[http:/www.youtube.com/watch?v=...].yaml`` with ``?``),
so the actual checkout used for tests must reside inside a Linux filesystem /
container volume, never mounted onto an NTFS path that recreates Windows
filename restrictions.

This module provides:
- a deterministic detector for Windows-invalid path characters;
- a guard that verifies a set of paths would NOT be Windows-constrained
  (evidence for the B1 gate);
- a thin, testable backend abstraction for executing commands in a Linux
  context (WSL2 or Docker), so the harness never shells out ad-hoc.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass

WINDOWS_INVALID_CHARS = frozenset('?*"<>|:')
WINDOWS_CONTROL = range(0x00, 0x20)


def contains_windows_invalid_char(relpath: str) -> bool:
    """True if a relative path component would be invalid on Windows."""
    for part in relpath.split("/"):
        if not part or part in (".", ".."):
            continue
        if part.endswith((".", " ")):
            return True
        for ch in part:
            if ch in WINDOWS_INVALID_CHARS or ord(ch) in WINDOWS_CONTROL:
                return True
    return False


def validate_linux_filesystem_required(paths: list[str]) -> list[str]:
    """Return the subset of paths that MUST live on a Linux filesystem.

    Any path with a Windows-invalid component (e.g. ``?``) must be checked out
    inside Linux; returning it here is the B1 gate evidence."""
    return [p for p in paths if contains_windows_invalid_char(p)]


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


class LinuxBackend:
    """Abstract Linux execution backend (WSL2 or Docker)."""

    def run(
        self,
        cmd: list[str],
        *,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        timeout_s: int = 900,
    ) -> CommandResult:
        raise NotImplementedError


class WslBackend(LinuxBackend):
    """Execute commands inside a WSL2 distro (e.g. Ubuntu-24.04)."""

    def __init__(self, distro: str = "Ubuntu-24.04") -> None:
        self.distro = distro

    def run(
        self,
        cmd: list[str],
        *,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        timeout_s: int = 900,
    ) -> CommandResult:
        full = ["wsl", "-d", self.distro, "--"]
        if cwd:
            full += ["cd", cwd, "&&"]
        if env:
            full += ["env"] + [f"{k}={v}" for k, v in env.items()]
        full += cmd
        r = subprocess.run(
            full,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout_s,
            check=False,
        )
        return CommandResult(r.returncode, r.stdout, r.stderr)


class DockerBackend(LinuxBackend):
    """Execute commands inside a running Docker container image."""

    def __init__(self, image: str, workdir: str = "/workspace") -> None:
        self.image = image
        self.workdir = workdir

    def run(
        self,
        cmd: list[str],
        *,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        timeout_s: int = 900,
    ) -> CommandResult:
        full = ["docker", "run", "--rm", "-w", cwd or self.workdir]
        for key, value in (env or {}).items():
            full += ["-e", f"{key}={value}"]
        full += [self.image] + cmd
        r = subprocess.run(
            full,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout_s,
            check=False,
        )
        return CommandResult(r.returncode, r.stdout, r.stderr)


class WslDockerBackend(LinuxBackend):
    """Execute the Docker CLI inside the WSL-local Docker Engine.

    The WSL-local engine (B0, user-authorized) is a separate execution substrate
    from Docker Desktop. All docker commands run via ``wsl -d Ubuntu-24.04 --
    docker ...`` so the CLI is never accidentally pointed back at Docker
    Desktop.
    """

    def __init__(self, distro: str = "Ubuntu-24.04", wsl_timeout_s: int = 3600) -> None:
        self.distro = distro
        self.wsl_timeout_s = wsl_timeout_s

    def run(
        self,
        cmd: list[str],
        *,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        timeout_s: int = 900,
    ) -> CommandResult:
        _ = cwd  # docker context/build dirs are passed as explicit args
        full = ["wsl", "-d", self.distro, "--"]
        if env:
            full += ["env"] + [f"{k}={v}" for k, v in env.items()]
        full += ["docker"] + cmd
        r = subprocess.run(
            full,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=max(timeout_s, self.wsl_timeout_s),
            check=False,
        )
        return CommandResult(r.returncode, r.stdout, r.stderr)


def translate_worktree_path(
    windows_path: str,
    *,
    mount_point: str = "/mnt/c",
    container_root: str = "/workspace",
) -> str:
    """Translate a Windows worktree path into a Linux container path.

    Deterministic rule (frozen): drive letter C: -> ``mount_point``; the
    portion of the path after the project root marker is preserved. This is a
    pure string transform used by the harness for container volume layout.
    """
    p = windows_path.replace("\\", "/")
    if p.startswith("C:"):
        p = p[2:].lstrip("/")
        p = f"{mount_point}/{p}"
    if p.startswith(mount_point):
        marker = "/master-2026-07-21-2355/"
        if marker in p:
            suffix = p.split(marker, 1)[1]
            return f"{container_root}/{suffix}"
    return p
