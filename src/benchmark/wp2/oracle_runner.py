"""WP-2 Oracle Confirmation runner - deterministic F2P/P2P execution (ZERO API).

Executes Oracle Confirmation for one task using isolated git worktrees from the
read-only Saleor cache:

1. TARGET state worktree  -> run the evaluator test set 3x.
2. PARENT+TTEST worktree  -> checkout parent, apply the derived test-only
   patch, run the same test set 3x.
3. Classify each test node under the frozen taxonomy and produce task-level
   eligibility flags.

The Saleor cache repository is never modified; worktrees live under
..\\_workspace\\wp2_oracle_confirmation\\worktrees\\.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

from benchmark.wp2.oracle_confirmation import (
    is_test_path,
    parse_junit,
)
from benchmark.wp2.paths import resolve_pg_bin, worktrees_root

# Where isolated worktrees live (outside the project tree).
WORKTREES_ROOT = worktrees_root()

PG_BIN = resolve_pg_bin()


class OracleRunError(RuntimeError):
    pass


def _run(cmd: list[str], cwd: Path, timeout_s: int = 900) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout_s,
        check=False,
    )


def _git(cache: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(cache), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def derive_test_only_patch_from_cache(cache: Path, parent: str, target: str) -> bytes:
    """Derive the test-only patch (parent..target restricted to test paths).

    Returns raw patch bytes. Raises ValueError if the patch is empty.
    """
    diff = _git(cache, "diff", "--name-status", parent, target)
    if diff.returncode != 0:
        raise OracleRunError(f"git diff --name-status failed: {diff.stderr}")
    test_paths: list[str] = []
    for line in diff.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        path = parts[1]
        if is_test_path(path):
            test_paths.append(path)
    if not test_paths:
        raise ValueError("no changed test paths")
    patch = _git(cache, "diff", parent, target, "--", *test_paths)
    if patch.returncode != 0:
        raise OracleRunError(f"git diff (test paths) failed: {patch.stderr}")
    result = patch.stdout
    if not result.endswith("\n"):
        result += "\n"
    return result.encode("utf-8")


def _patch_applies(worktree: Path, patch_bytes: bytes, patch_path: Path) -> bool:
    patch_path.write_bytes(patch_bytes)
    chk = _git(worktree, "apply", "--check", str(patch_path))
    return chk.returncode == 0


def _apply_patch(worktree: Path, patch_path: Path) -> bool:
    app = _git(worktree, "apply", str(patch_path))
    return app.returncode == 0


class OracleConfirmationRunner:
    def __init__(self, cache: Path, worktrees_root: Path = WORKTREES_ROOT) -> None:
        self.cache = cache
        self.worktrees_root = worktrees_root
        self.worktrees_root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    def _add_worktree(self, name: str, commit: str) -> Path:
        wt = self.worktrees_root / name
        if wt.exists():
            shutil.rmtree(wt, ignore_errors=True)
            _git(self.cache, "worktree", "prune")
        r = _git(self.cache, "worktree", "add", "--detach", str(wt), commit)
        if r.returncode != 0 or not (wt / "saleor").is_dir():
            raise OracleRunError(f"worktree add failed for {name}: {r.stderr}")
        return wt

    def _remove_worktree(self, name: str) -> None:
        wt = self.worktrees_root / name
        if wt.exists():
            _git(self.cache, "worktree", "remove", "--force", str(wt))
        _git(self.cache, "worktree", "prune")

    # ------------------------------------------------------------------ #
    def discover_test_nodes(self, worktree: Path, test_files: list[str], python: Path) -> dict:
        """Run pytest --collect-only on target to obtain exact node IDs."""
        env = os.environ.copy()
        env["DATABASE_URL"] = "postgres://saleor:saleor@127.0.0.1:5433/saleor"
        env["CACHE_URL"] = "locmem://"
        cmd = [
            str(python),
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "--collect-only",
            "-q",
            "-o",
            "addopts=",
            "--ds=saleor.tests.settings",
        ] + test_files
        r = subprocess.run(
            cmd,
            cwd=str(worktree),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=900,
            env=env,
            check=False,
        )
        nodes: list[str] = []
        for line in r.stdout.splitlines():
            line = line.strip()
            if "::" in line and not line.startswith(("=", "ERROR", "error", "No tests")):
                nodes.append(line)
        return {
            "nodes": nodes,
            "returncode": r.returncode,
            "stdout_tail": r.stdout[-2000:],
            "stderr_tail": r.stderr[-2000:],
        }

    def run_evaluator(
        self,
        worktree: Path,
        node_ids: list[str],
        python: Path,
        junit_path: Path,
        timeout_s: int = 900,
    ) -> dict:
        """Run pytest --junitxml with the exact node IDs; return structured output."""
        env = os.environ.copy()
        env["DATABASE_URL"] = "postgres://saleor:saleor@127.0.0.1:5433/saleor"
        env["CACHE_URL"] = "locmem://"
        cmd = [
            str(python),
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "-o",
            "addopts=",
            "--ds=saleor.tests.settings",
            "--disable-socket",
            "--reuse-db",
            "--junitxml",
            str(junit_path),
            "-q",
        ] + node_ids
        t0 = time.monotonic()
        try:
            r = subprocess.run(
                cmd,
                cwd=str(worktree),
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=timeout_s,
                env=env,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return {
                "returncode": -1,
                "timed_out": True,
                "duration_s": time.monotonic() - t0,
                "junit": {},
                "stdout_tail": "",
                "stderr_tail": "timeout",
            }
        duration = time.monotonic() - t0
        junit_nodes: dict[str, str] = {}
        if junit_path.exists():
            try:
                junit_nodes = parse_junit(junit_path.read_text(encoding="utf-8"))
            except Exception as exc:
                junit_nodes = {"__junit_parse_error__": str(exc)}
        return {
            "returncode": r.returncode,
            "timed_out": False,
            "duration_s": round(duration, 3),
            "junit": junit_nodes,
            "stdout_tail": r.stdout[-2000:],
            "stderr_tail": r.stderr[-2000:],
        }


def collect_test_files(cache: Path, parent: str, target: str) -> list[str]:
    diff = _git(cache, "diff", "--name-status", parent, target)
    paths = []
    for line in diff.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        path = parts[1]
        if is_test_path(path):
            paths.append(path)
    return paths
