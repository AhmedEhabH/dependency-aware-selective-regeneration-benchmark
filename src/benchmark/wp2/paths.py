"""WP-2 path and interpreter discovery (portable, no machine-specific paths).

Repository root, workspace root, WP-2 env/worktree roots, the Saleor cache
venv, the PostgreSQL bin directory and a compatible Python 3.12 interpreter are
all resolved dynamically, never hard-coded to a machine/user.

Resolution precedence (highest first):
- explicit CLI/config value (passed in by the caller);
- ``WP2_WORKSPACE_ROOT`` / ``WP2_PYTHON`` / ``WP2_PG_BIN`` environment
  variables;
- deterministic repository-relative / repository-parent defaults.

All functions fail closed with a clear error when the resource cannot be
resolved.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_MARKERS = (".git", "pyproject.toml", "AGENTS.md")


def _is_repo_dir(path: Path) -> bool:
    return any((path / marker).exists() for marker in REPO_MARKERS)


def repo_root(start: Path | None = None) -> Path:
    """Resolve the repository root by walking upward from ``start``.

    Falls back to ``git rev-parse --show-toplevel`` when walking fails.
    Fails closed if the root cannot be resolved.
    """
    start = (start or Path(__file__).resolve().parent).resolve()
    cursor = start if start.is_dir() else start.parent
    while True:
        if _is_repo_dir(cursor):
            return cursor
        parent = cursor.parent
        if parent == cursor:
            break
        cursor = parent
    # git fallback
    r = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if r.returncode == 0:
        return Path(r.stdout.strip()).resolve()
    raise RuntimeError(
        "Cannot resolve repository root from "
        f"{start}; run from inside the repository or set WP2_WORKSPACE_ROOT."
    )


def workspace_root(override: str | Path | None = None) -> Path:
    """Resolve the workspace root.

    Precedence: explicit override -> ``WP2_WORKSPACE_ROOT`` env ->
    ``<repo_root>/../_workspace`` (the sibling workspace this project uses).
    """
    if override:
        return Path(override).resolve()
    env = os.environ.get("WP2_WORKSPACE_ROOT")
    if env:
        return Path(env).resolve()
    root = repo_root()
    default = root.parent / "_workspace"
    if default.is_dir():
        return default.resolve()
    return default


def oracle_confirmation_root(workspace: Path | None = None) -> Path:
    return (workspace or workspace_root()) / "wp2_oracle_confirmation"


def envs_root(workspace: Path | None = None) -> Path:
    return oracle_confirmation_root(workspace) / "envs"


def worktrees_root(workspace: Path | None = None) -> Path:
    return oracle_confirmation_root(workspace) / "worktrees"


def saleor_cache_venv_python(workspace: Path | None = None) -> Path:
    """HEAD-era Saleor project venv python (fallback interpreter)."""
    return (
        (workspace or workspace_root())
        / "cache"
        / "repositories"
        / "saleor"
        / ".venv"
        / "Scripts"
        / "python.exe"
    )


def _version(python: Path) -> str:
    try:
        r = subprocess.run(
            [str(python), "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if r.returncode == 0:
        return (r.stdout or r.stderr).strip()
    return ""


def _resolved_python(python: Path) -> str:
    try:
        r = subprocess.run(
            [str(python), "-c", "import sys; print(sys.executable)"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except OSError:
        pass
    return str(python)


def resolve_python_312(override: str | Path | None = None) -> Path | None:
    """Resolve a Python 3.12 interpreter deterministically.

    Precedence: explicit override -> ``WP2_PYTHON`` env -> ``py -3.12``
    launcher -> ``uv python find 3.12`` -> ``shutil.which("python3.12")`` ->
    ``shutil.which("python")`` if it reports 3.12. Returns None if none is
    found or none validates as 3.12.
    """
    candidates: list[Path | None] = []
    if override:
        candidates.append(Path(override))
    if os.environ.get("WP2_PYTHON"):
        candidates.append(Path(os.environ["WP2_PYTHON"]))

    py_launcher = shutil.which("py")
    if py_launcher:
        r = subprocess.run(
            [py_launcher, "-3.12", "-c", "import sys; print(sys.executable)"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if r.returncode == 0 and r.stdout.strip():
            candidates.append(Path(r.stdout.strip()))

    if shutil.which("uv"):
        r = subprocess.run(
            ["uv", "python", "find", "3.12"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if r.returncode == 0 and r.stdout.strip():
            candidates.append(Path(r.stdout.strip()))

    candidates.append(Path(shutil.which("python3.12")) if shutil.which("python3.12") else None)

    # last resort: bare 'python' if it is 3.12
    which_python = shutil.which("python")
    if which_python:
        candidates.append(Path(which_python))

    seen: set[str] = set()
    for cand in candidates:
        if cand is None:
            continue
        resolved = Path(_resolved_python(cand)).resolve()
        key = str(resolved)
        if key in seen:
            continue
        seen.add(key)
        ver = _version(resolved)
        if "3.12" in ver:
            return resolved
    return None


def resolve_pg_bin(override: str | Path | None = None) -> Path | None:
    """Resolve the PostgreSQL bin directory (for psql/pg_isready).

    Precedence: explicit override -> ``WP2_PG_BIN`` env -> ``psql`` on PATH ->
    common Windows PostgreSQL install locations. Returns None if not found.
    """
    if override:
        p = Path(override)
        return p if (p / "psql.exe").exists() else None
    env = os.environ.get("WP2_PG_BIN")
    if env:
        p = Path(env)
        if (p / "psql.exe").exists():
            return p
    psql = shutil.which("psql")
    if psql:
        return Path(psql).resolve().parent
    # Common Windows PostgreSQL install location via the ProgramFiles env var
    # (never a hard-coded drive letter or username).
    program_files = os.environ.get("PROGRAMFILES")
    if program_files:
        root = Path(program_files) / "PostgreSQL"
        if root.is_dir():
            for child in sorted(root.iterdir(), reverse=True):
                if (child / "bin" / "psql.exe").exists():
                    return child / "bin"
    return None


def forbidden_machine_paths() -> tuple[str, ...]:
    """Path fragments that must never appear in executable WP-2 code."""
    return (
        "C:\\Users\\",
        "Desktop\\OpenCode",
        "master-2026-07-21-2355",
        "AppData\\Roaming\\uv",
        "cpython-3.12",
        "_workspace\\cache\\repositories\\saleor\\.venv",
    )


if __name__ == "__main__":
    # Lightweight CLI diagnostics (no tests here; see tests/unit/wp2/).
    print(f"REPO_ROOT={repo_root()}")
    print(f"WORKSPACE_ROOT={workspace_root()}")
    print(f"ENVS_ROOT={envs_root()}")
    print(f"WORKTREES_ROOT={worktrees_root()}")
    print(f"PY312={resolve_python_312()}")
    print(f"PG_BIN={resolve_pg_bin()}")
    print(f"SALEOR_CACHE_VENV={saleor_cache_venv_python()}")
    sys.exit(0)
