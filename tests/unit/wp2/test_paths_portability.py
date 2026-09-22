"""WP-2 path/interpreter portability tests (ZERO API, no git, no network).

Guards against machine-specific absolute paths creeping back into executable
WP-2 code, and verifies dynamic repository/workspace/Python resolution and
override precedence. The PostgreSQL resolver may return None on non-Windows
systems; tests are written to be platform-tolerant where appropriate.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from benchmark.wp2.paths import (
    envs_root,
    forbidden_machine_paths,
    oracle_confirmation_root,
    repo_root,
    resolve_pg_bin,
    resolve_python_312,
    saleor_cache_venv_python,
    workspace_root,
    worktrees_root,
)

PROJECT = Path(__file__).resolve().parents[3]

# Executable WP-2 source/scripts to scan for machine-specific paths.
WP2_SCAN_FILES = [
    PROJECT / "src" / "benchmark" / "wp2" / "paths.py",
    PROJECT / "src" / "benchmark" / "wp2" / "oracle_confirmation.py",
    PROJECT / "src" / "benchmark" / "wp2" / "environment_manager.py",
    PROJECT / "src" / "benchmark" / "wp2" / "oracle_runner.py",
    PROJECT / "scripts" / "wp2_oracle_confirm.py",
]


def _strip_forbidden_def(text: str) -> str:
    """Remove the forbidden_machine_paths() tuple body (guard definitions)."""
    start = text.find("def forbidden_machine_paths")
    if start == -1:
        return text
    # cut from the def line to the closing ')' of the return tuple (approximate
    # by finding the first blank line after the tuple's closing paren)
    end = text.find("\n\n", start)
    if end == -1:
        end = len(text)
    return text[:start] + text[end:]


def test_no_machine_specific_paths_in_wp2_code() -> None:
    forbidden = forbidden_machine_paths()
    offenders: list[str] = []
    for path in WP2_SCAN_FILES:
        if not path.exists():
            continue
        text = _strip_forbidden_def(path.read_text(encoding="utf-8"))
        # normalize both the scanned source and fragments to a common form
        norm = text.replace("\\", "/").lower()
        for frag in forbidden:
            if frag.replace("\\", "/").lower() in norm:
                offenders.append(f"{path.name}:{frag}")
    assert offenders == [], f"machine-specific paths found: {offenders}"


def test_no_drive_letter_in_wp2_paths_module() -> None:
    """The paths module must not embed a C:\\-style drive literal (outside the
    guard-pattern definitions)."""
    text = (PROJECT / "src" / "benchmark" / "wp2" / "paths.py").read_text(encoding="utf-8")
    assert re_drive_letters_absent(_strip_forbidden_def(text))


def re_drive_letters_absent(text: str) -> bool:
    # a drive-letter literal would be something like r"C:\" or "C:/" outside a comment
    import re

    stripped = re.sub(r"#.*$", "", text, flags=re.M)
    return not re.search(r"['\"]?[A-Za-z]:[\\/]", stripped)


def test_repo_root_resolves_from_anywhere(tmp_path: Path) -> None:
    """repo_root() must resolve even when cwd is NOT the repo root."""
    saved = os.getcwd()
    try:
        os.chdir(tmp_path)
        root = repo_root()
        assert (root / "pyproject.toml").is_file() or (root / "AGENTS.md").is_file()
    finally:
        os.chdir(saved)


def test_workspace_override_env_var() -> None:
    os.environ["WP2_WORKSPACE_ROOT"] = str(Path("Z:/fake/workspace"))
    try:
        ws = workspace_root()
        assert str(ws).replace("\\", "/").endswith("Z:/fake/workspace")
    finally:
        del os.environ["WP2_WORKSPACE_ROOT"]


def test_workspace_override_explicit_precedence() -> None:
    os.environ["WP2_WORKSPACE_ROOT"] = "Z:/from_env"
    try:
        explicit = workspace_root(override="Z:/explicit")
        assert str(explicit).replace("\\", "/").endswith("Z:/explicit")
    finally:
        del os.environ["WP2_WORKSPACE_ROOT"]


def test_env_and_worktree_roots_derived_from_workspace() -> None:
    ws = Path("X:/ws")
    assert envs_root(ws) == ws / "wp2_oracle_confirmation" / "envs"
    assert worktrees_root(ws) == ws / "wp2_oracle_confirmation" / "worktrees"
    assert oracle_confirmation_root(ws) == ws / "wp2_oracle_confirmation"


def test_python_312_discovery_does_not_need_username() -> None:
    """resolve_python_312() must never depend on a user-profile literal."""
    py = resolve_python_312()
    # It may return None on machines without 3.12, but if found it must be valid.
    if py is not None:
        r = subprocess.run([str(py), "--version"], capture_output=True, text=True, encoding="utf-8")
        assert "3.12" in (r.stdout + r.stderr)


def test_missing_python_env_var_override_fails_closed() -> None:
    os.environ["WP2_PYTHON"] = "Z:/definitely/not/a/python.exe"
    try:
        # the resolver tries several mechanisms; if the invalid override is the
        # only candidate, or discovery cannot validate a 3.12, it returns None
        # rather than crashing with a hard-coded fallback.
        result = resolve_python_312()
        assert result is None or _is_real_312(result)
    finally:
        del os.environ["WP2_PYTHON"]


def _is_real_312(py: Path) -> bool:
    r = subprocess.run([str(py), "--version"], capture_output=True, text=True, encoding="utf-8")
    return "3.12" in (r.stdout + r.stderr)


def test_pg_bin_resolves_or_none() -> None:
    """PG bin resolution returns a path containing psql, or None (platform)."""
    pg = resolve_pg_bin()
    if pg is not None:
        assert (pg / "psql.exe").exists() or (pg / "psql").exists()


def test_windows_separators_do_not_affect_path_construction() -> None:
    ws = Path("C:/ws")  # forward slashes on any platform
    assert (envs_root(ws) / "envs").name == "envs"
    assert str(worktrees_root(ws)).endswith("worktrees")


def test_saleor_cache_venv_derived_from_workspace() -> None:
    ws = Path("Y:/ws")
    p = saleor_cache_venv_python(ws)
    assert p.parts[-4:] == ("saleor", ".venv", "Scripts", "python.exe")
