#!/usr/bin/env python3
"""Deterministic, fail-closed materialization of frozen Pilot repository snapshots.

PILOT-EXEC-01 closure (``_workspace/active/PILOT-EXEC-01-REAL-LAUNCH-CLOSURE/
02_REPOSITORY_SNAPSHOT_CONTRACT.md``).

The real non-dry-run Pilot path in ``seven_arm_benchmark.py`` resolves every
selected repository from ``data_dir / "repositories" / repo_id`` and aborts
before model initialization when the source root is missing. The historical
Smoke bundle only embedded the ``todo`` tree, so the corrected Pilot bundle must
additionally carry the pinned django CMS and Saleor source trees.

Guarantees:

- materializes tracked files AT the exact pinned commit only (no floating
  branch/head; no ``.git`` directory in the deployment archive);
- fails closed when a materialized source does not match its pinned commit;
- reuses a reusable local acquisition cache (git checkouts) outside the bundle;
- emits deterministic per-repository snapshot evidence (requested SHA,
  resolved HEAD, file count, content hash, size).

The pinned SHAs mirror ``benchmark_data/manifests/repository_versions.yaml``.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tarfile
import time
import urllib.parse
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from benchmark.repositories.validation_commands import FrozenValidationCommand

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EMBEDDED_TODO_SOURCE = (
    PROJECT_ROOT / "benchmark_data" / "repositories" / "todo"
)

_STAGING_EXCLUDED_DIRS: frozenset[str] = frozenset({
    ".git",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "runs",
    "tmp",
    "_auto_resume_temp",
})


@dataclass(frozen=True)
class RepositoryPin:
    """Frozen identity of one Pilot repository source snapshot."""

    repo_id: str
    commit_sha: str
    mode: str  # "git" (external checkout cache) or "embedded" (canonical tree)
    url: str = ""
    embedded_source: Path | None = None


DEFAULT_PINS: tuple[RepositoryPin, ...] = (
    RepositoryPin(
        repo_id="todo",
        commit_sha="b8a33e20bdaf5b329114273063fbe8d5aa66e9cf",
        mode="embedded",
        url="https://github.com/ahmed-ehab/controlled-django-todo",
        embedded_source=EMBEDDED_TODO_SOURCE,
    ),
    RepositoryPin(
        repo_id="djangocms",
        commit_sha="0f633fc9fa213357f4202482aab2b0edad680f95",
        mode="git",
        url="https://github.com/django-cms/django-cms",
    ),
    RepositoryPin(
        repo_id="saleor",
        commit_sha="e11a5557eff29fbb2eed36e6ff3cd0af08ab9e10",
        mode="git",
        url="https://github.com/saleor/saleor",
    ),
)


@dataclass(frozen=True)
class SnapshotEvidence:
    repo_id: str
    mode: str
    requested_sha: str
    resolved_head: str
    file_count: int
    content_hash: str
    size_bytes: int


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _tree_content_hash(directory: Path) -> str:
    """Deterministic tree/content hash over eligible files.

    Mirrors the bundle ``_tree_sha256`` contract used by the deployment tests so
    the materialized snapshot evidence is reproducible.
    """
    digest = hashlib.sha256()
    eligible = [
        p.relative_to(directory).as_posix()
        for p in directory.rglob("*")
        if p.is_file()
        and p.name not in (".git",)
        and not any(part in _STAGING_EXCLUDED_DIRS for part in p.relative_to(directory).parts)
    ]
    for rel in sorted(eligible):
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update((directory / rel).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _count_files(directory: Path) -> int:
    return sum(
        1
        for p in directory.rglob("*")
        if p.is_file()
        and not any(part in _STAGING_EXCLUDED_DIRS for part in p.relative_to(directory).parts)
    )


def _total_size(directory: Path) -> int:
    return sum(
        p.stat().st_size
        for p in directory.rglob("*")
        if p.is_file()
        and not any(part in _STAGING_EXCLUDED_DIRS for part in p.relative_to(directory).parts)
    )


def _git(repo_path: Path, args: list[str], *, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_path), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed in {repo_path}: {result.stderr.strip()}"
        )
    return result.stdout.strip()


def _resolve_commit(repo_path: Path, commit_sha: str) -> str:
    resolved = _git(repo_path, ["rev-parse", "--verify", f"{commit_sha}^{{commit}}"])
    if len(resolved) != 40:
        raise RuntimeError(
            f"pinned commit {commit_sha} did not resolve to a 40-char SHA "
            f"in {repo_path}: {resolved!r}"
        )
    return resolved


def _export_git_tree(repo_path: Path, commit_sha: str, target_dir: Path) -> None:
    """Export tracked files at ``commit_sha`` into ``target_dir`` (no .git).

    Uses ``git archive`` (deterministic; honors the exact tree) and extracts
    with Python tarfile. Symlinks are skipped (never required by the benchmark
    validation paths and they are not portable on Windows).
    """
    result = subprocess.run(
        ["git", "-C", str(repo_path), "archive", "--format=tar", commit_sha],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git archive failed for {commit_sha} in {repo_path}: "
            f"{result.stderr.decode('utf-8', 'replace').strip()}"
        )
    target_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(result.stdout), mode="r:") as tf:
        for member in tf.getmembers():
            if member.isdir():
                continue
            if member.issym() or member.islnk():
                continue
            name = member.name.lstrip("./")
            if ".." in Path(name).parts:
                raise RuntimeError(
                    f"tar member escapes target directory: {member.name!r}"
                )
            out_path = target_dir / name
            out_path.parent.mkdir(parents=True, exist_ok=True)
            extracted = tf.extractfile(member)
            if extracted is None:
                continue
            data = extracted.read()
            out_path.write_bytes(data)


def _copy_embedded_tree(source: Path, target_dir: Path) -> None:
    if target_dir.is_dir():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    def _ignore(_dirpath: str, names: list[str]) -> list[str]:
        ignored: list[str] = []
        for name in names:
            if name in _STAGING_EXCLUDED_DIRS:
                ignored.append(name)
        return ignored

    shutil.copytree(source, target_dir, dirs_exist_ok=True, ignore=_ignore)


def materialize_repository(
    pin: RepositoryPin,
    repo_cache: Path | None,
    target_dir: Path,
    *,
    allow_acquire: bool = False,
) -> SnapshotEvidence:
    """Materialize one frozen repository snapshot and return its evidence.

    Fails closed on any identity mismatch. No ``.git`` directory is ever
    included in the output.
    """
    if pin.mode == "embedded":
        source = pin.embedded_source
        if source is None or not source.is_dir():
            raise RuntimeError(
                f"embedded source for '{pin.repo_id}' is missing: {source}"
            )
        _copy_embedded_tree(source, target_dir)
        resolved_head = "embedded"
    elif pin.mode == "git":
        if repo_cache is None:
            raise RuntimeError(
                f"repository '{pin.repo_id}' requires --repo-cache "
                f"(git checkout cache); none provided."
            )
        checkout = repo_cache / pin.repo_id
        if not (checkout / ".git").exists():
            raise RuntimeError(
                f"repo cache checkout for '{pin.repo_id}' is missing: {checkout}. "
                "Provide --repo-cache pointing at a directory containing git "
                "checkouts of djangocms and saleor at their pinned commits."
            )
        try:
            resolved_head = _resolve_commit(checkout, pin.commit_sha)
        except RuntimeError:
            if not allow_acquire:
                raise
            _git(checkout, ["fetch", "--quiet", "--depth", "1", "origin", pin.commit_sha])
            _git(checkout, ["fetch", "--quiet", "origin", pin.commit_sha])
            resolved_head = _resolve_commit(checkout, pin.commit_sha)
        if resolved_head != pin.commit_sha:
            raise RuntimeError(
                f"pinned commit mismatch for '{pin.repo_id}': requested "
                f"{pin.commit_sha} resolved to {resolved_head}"
            )
        if target_dir.is_dir():
            shutil.rmtree(target_dir)
        _export_git_tree(checkout, resolved_head, target_dir)
    else:
        raise RuntimeError(f"unsupported materialization mode: {pin.mode!r}")

    return SnapshotEvidence(
        repo_id=pin.repo_id,
        mode=pin.mode,
        requested_sha=pin.commit_sha,
        resolved_head=resolved_head,
        file_count=_count_files(target_dir),
        content_hash=_tree_content_hash(target_dir),
        size_bytes=_total_size(target_dir),
    )


def materialize_repositories(
    data_repositories_dir: Path,
    repo_cache: Path | None,
    pins: tuple[RepositoryPin, ...] = DEFAULT_PINS,
    *,
    allow_acquire: bool = False,
) -> dict[str, dict]:
    """Materialize every pinned repository under ``data_repositories_dir``.

    Returns an ordered mapping of repo_id -> evidence dict suitable for JSON
    manifest serialization. Fails closed on any missing/divergent source.
    """
    data_repositories_dir.mkdir(parents=True, exist_ok=True)
    evidence: dict[str, dict] = {}
    for pin in pins:
        target = data_repositories_dir / pin.repo_id
        result = materialize_repository(
            pin,
            repo_cache=repo_cache,
            target_dir=target,
            allow_acquire=allow_acquire,
        )
        evidence[pin.repo_id] = asdict(result)
    return evidence


# ---------------------------------------------------------------------------
# Engineering preflight: run each frozen validation command against a pristine
# staged snapshot and report PASS/FAIL per repository (05_REAL_PREBENCHMARK_GATE,
# Pipeline Smoke Test). The Kaggle notebook runs the same entry point.
# ---------------------------------------------------------------------------

DEFAULT_MANIFEST = (
    PROJECT_ROOT
    / "benchmark_data"
    / "manifests"
    / "pilot_validation_commands.yaml"
)


def _tail_output(raw: str, *, max_lines: int = 25) -> str:
    lines = [line.rstrip("\r") for line in raw.splitlines() if line.strip()]
    return "\n".join(lines[-max_lines:])

MAX_LOG_CHARS = 5_000_000


def _write_bounded_log(
    text: str, path: Path, *, limit: int = MAX_LOG_CHARS
) -> None:
    """Persist a full command log, capping pathological outputs.

    Keeps the head and the tail (the diagnostic first root cause and the final
    pytest summary both live at the edges), with an explicit truncation marker
    that is reserved inside the ``limit`` budget. Untruncated logs are written
    verbatim.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if len(text) <= limit:
        path.write_text(text, encoding="utf-8", newline="\n")
        return
    marker = f"\n... [TRUNCATED: output exceeded {limit} characters] ...\n"
    budget = limit - len(marker)
    if budget <= 0:
        path.write_text(marker, encoding="utf-8", newline="\n")
        return
    head_len = budget // 2
    tail_len = budget - head_len
    path.write_text(
        text[:head_len] + marker + text[-tail_len:],
        encoding="utf-8",
        newline="\n",
    )


def _load_lastfailed(staging_dir: Path) -> tuple[int, tuple[str, ...]] | None:
    """Parse the pytest ``lastfailed`` cache left by the primary run.

    Must be called BEFORE any serial rerun (a rerun rewrites the cache).
    Returns ``(count, sorted_nodeids)`` or ``None`` when absent/unreadable.
    """
    cache = staging_dir / ".pytest_cache" / "v" / "cache" / "lastfailed"
    if not cache.is_file():
        return None
    try:
        data = json.loads(cache.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    nodeids = tuple(sorted(str(key) for key in data if isinstance(key, str)))
    return len(nodeids), nodeids


def _group_failures_by_source_file(nodeids: tuple[str, ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for nodeid in nodeids:
        source = nodeid.split("::", 1)[0]
        counts[source] = counts.get(source, 0) + 1
    return dict(sorted(counts.items()))


def _failed_subtree_prefixes(nodeids: tuple[str, ...]) -> tuple[str, ...]:
    prefixes = {Path(nodeid.split("::", 1)[0]).parent.as_posix() for nodeid in nodeids}
    return tuple(sorted(prefixes))


BASELINE_PROFILE_SCHEMA = "pilot_saleor_baseline_flaky_profile.v1"

_PRECOMPUTED_UNSET = object()


def _serial_rerun_nodeid(
    python: str,
    staging_dir: Path,
    env: dict[str, str],
    timeout: int,
    nodeid: str,
    logs_dir: Path | None,
    log_prefix: str,
) -> dict[str, object]:
    """Serially (``-n 0``) rerun exactly one failing nodeid.

    Baseline-flake policy evidence: a pristine-baseline failure may only be
    classified as a pre-existing nondeterministic flake when this exact nodeid
    passes on a serial rerun (policy criterion 3/6).
    """
    argv = [python, "-m", "pytest", "-n", "0", "-q", "--no-header", "--tb=line", nodeid]
    result = _run_command(
        argv,
        staging_dir,
        env,
        timeout,
        f"baseline-flake-rerun-{_safe_log_stem(nodeid)}",
        logs_dir=logs_dir,
        log_prefix=log_prefix,
    )
    return {
        "nodeid": nodeid,
        "exit_code": result.get("exit_code"),
        "passed": bool(result.get("passed")),
        "duration_seconds": result.get("duration_seconds"),
        "log_path": result.get("log_path", ""),
    }


def _safe_log_stem(nodeid: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", nodeid)
    return stem[-120:] if len(stem) > 120 else stem


def build_baseline_profile_evidence(
    *,
    saleor_commit_sha: str,
    frozen_validation_command: Sequence[str],
    environment_versions: dict[str, object],
    full_run_exit_code: object,
    full_run_duration_seconds: object,
    failed_nodeids: Sequence[str],
    serial_reruns: Sequence[dict[str, object]],
    created_utc: str,
    profile_source_commit: str,
    platform_name: str,
) -> dict[str, object]:
    """Assemble the versioned baseline-flake evidence artifact payload."""
    return {
        "schema": BASELINE_PROFILE_SCHEMA,
        "task": "PILOT-EXEC-01",
        "saleor_commit_sha": saleor_commit_sha,
        "frozen_validation_command": list(frozen_validation_command),
        "environment_versions": environment_versions,
        "full_run_exit_code": full_run_exit_code,
        "full_run_duration_seconds": full_run_duration_seconds,
        "failed_nodeids": sorted(failed_nodeids),
        "failed_count": len(failed_nodeids),
        "per_nodeid_serial_rerun": [dict(v) for v in serial_reruns],
        "created_utc": created_utc,
        "profile_source_commit": profile_source_commit,
        "platform": platform_name,
    }


def load_baseline_profile(
    path: Path,
    *,
    expected_saleor_sha: str,
    expected_frozen_command: Sequence[str],
) -> dict[str, object]:
    """Load and validate the frozen baseline-flake profile (fail-closed).

    The profile is only usable when it matches the exact pinned Saleor snapshot
    and the exact frozen validation command, and every recorded flaky nodeid
    has a PASSING serial rerun recorded at profile-creation time.
    """
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"cannot read baseline profile {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"baseline profile {path} is not a JSON object")
    if payload.get("schema") != BASELINE_PROFILE_SCHEMA:
        raise RuntimeError(
            f"baseline profile {path} has unsupported schema "
            f"{payload.get('schema')!r} (expected {BASELINE_PROFILE_SCHEMA!r})"
        )
    if payload.get("saleor_commit_sha") != expected_saleor_sha:
        raise RuntimeError(
            f"baseline profile {path} targets Saleor snapshot "
            f"{payload.get('saleor_commit_sha')!r}, expected {expected_saleor_sha!r}"
        )
    recorded_command = payload.get("frozen_validation_command")
    if list(recorded_command or []) != list(expected_frozen_command):
        raise RuntimeError(
            f"baseline profile {path} was generated for a different frozen "
            f"validation command: {recorded_command!r}"
        )
    nodeids = payload.get("failed_nodeids")
    if (
        not isinstance(nodeids, list)
        or not nodeids
        or not all(isinstance(n, str) and n for n in nodeids)
    ):
        raise RuntimeError(
            f"baseline profile {path} has an empty or invalid failed_nodeids list"
        )
    reruns = payload.get("per_nodeid_serial_rerun")
    if not isinstance(reruns, list) or len(reruns) != len(nodeids):
        raise RuntimeError(
            f"baseline profile {path} lacks one serial rerun per failed nodeid"
        )
    seen: set[str] = set()
    for entry in reruns:
        if not isinstance(entry, dict) or isinstance(entry.get("nodeid"), str) is False:
            raise RuntimeError(
                f"baseline profile {path} has an invalid serial-rerun entry"
            )
        nodeid = entry["nodeid"]
        if nodeid not in nodeids or nodeid in seen:
            raise RuntimeError(
                f"baseline profile {path} serial reruns do not match failed_nodeids"
            )
        seen.add(nodeid)
        if entry.get("passed") is not True:
            raise RuntimeError(
                f"baseline profile {path} records nodeid {nodeid!r} as failing "
                "its profile-time serial rerun; deterministic failures are not flakes"
            )
    missing = [n for n in nodeids if n not in seen]
    if missing:
        raise RuntimeError(
            f"baseline profile {path} lacks serial reruns for: {missing[:5]}"
        )
    return payload


def classify_saleor_failures_against_profile(
    failed_nodeids: Sequence[str],
    serial_reruns: Sequence[dict[str, object]],
    baseline_profile: dict[str, object],
) -> dict[str, object]:
    """Compare observed pristine-baseline failures against the frozen profile.

    Policy (PILOT-EXEC-01 v0.9.20): every observed nodeid must already be in
    the frozen profile (exact nodeids, never directory allowlists), and every
    nodeid must STILL pass a current serial rerun; any new nodeid or any
    deterministically re-failing nodeid is a hard FAIL.
    """
    allowed = set(cast("list[str]", baseline_profile["failed_nodeids"]))
    unclassified = sorted({n for n in failed_nodeids if n not in allowed})
    if unclassified:
        return {
            "status": "FAILED_UNCLASSIFIED_NODEIDS",
            "profile_schema": baseline_profile.get("schema"),
            "observed_count": len(failed_nodeids),
            "unclassified_nodeids": unclassified,
            "classified": False,
        }
    deterministic = sorted(
        str(v["nodeid"]) for v in serial_reruns if not bool(v.get("passed"))
    )
    if deterministic:
        return {
            "status": "FAILED_DETERMINISTIC_SERIAL_FAILURES",
            "profile_schema": baseline_profile.get("schema"),
            "observed_count": len(failed_nodeids),
            "deterministic_failures": deterministic,
            "classified": False,
        }
    return {
        "status": "CLASSIFIED",
        "profile_schema": baseline_profile.get("schema"),
        "profile_created_utc": baseline_profile.get("created_utc"),
        "observed_count": len(failed_nodeids),
        "classified_nodeids": sorted(failed_nodeids),
        "classified": True,
    }


def _host_port_from_url(url: str) -> tuple[str, int] | None:
    parsed = urllib.parse.urlparse(url)
    if not parsed.hostname:
        return None
    port = parsed.port or {"http": 80, "https": 443, "postgres": 5432, "redis": 6379}.get(
        parsed.scheme, 5432
    )
    return parsed.hostname, int(port)


def _service_reachable(url: str, *, timeout: float = 5.0) -> bool:
    host_port = _host_port_from_url(url)
    if host_port is None:
        return False
    host, port = host_port
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _resolve_services(
    declared: tuple[str, ...], env: dict[str, str]
) -> list[dict[str, object]]:
    """Probe every service URL referenced by the frozen command env.

    ``postgres://`` / ``redis://`` URLs are reachability-checked over TCP. The
    SQLite backend requires no service and is reported as ``required: False``.
    """
    results: list[dict[str, object]] = []
    for value in sorted(env.values()):
        scheme = urllib.parse.urlparse(value).scheme
        if scheme not in {"postgres", "postgresql", "redis"}:
            continue
        name = "postgresql" if scheme.startswith("postgres") else "valkey"
        reachable = _service_reachable(value)
        results.append({
            "name": name,
            "url_scheme": scheme,
            "required": name in declared,
            "reachable": reachable,
        })
    for service in sorted(declared):
        if not any(r["name"] == service for r in results):
            results.append({"name": service, "required": True, "reachable": False})
    return results


def apply_windows_infra_workarounds(staged_dir: Path, repo_id: str) -> list[str]:
    """Apply documented win32-only environment compatibility shims to a staged copy.

    The staged copy is a disposable materialization; the source-of-truth tree is
    never modified. On Linux/Kaggle no shim is applied (see
    PILOT-READY-01-SALEOR-VALIDATION: ``saleor/core/rlimit.py`` imports the
    Unix-only ``resource`` module unconditionally).
    """
    applied: list[str] = []
    if sys.platform != "win32" or repo_id != "saleor":
        return applied
    target = staged_dir / "saleor" / "core" / "rlimit.py"
    if not target.is_file():
        raise RuntimeError(f"expected {target} for saleor win32 shim; missing")
    original = target.read_text(encoding="utf-8")
    if "except ImportError" in original:
        return applied
    guarded = original.replace(
        "import resource\n",
        "try:\n    import resource\nexcept ImportError:\n    resource = None\n",
        1,
    )
    guarded = guarded.replace(
        "RLIMIT_TYPE = resource.RLIMIT_DATA\n",
        "RLIMIT_TYPE = resource.RLIMIT_DATA if resource is not None else None\n",
        1,
    )
    guarded = guarded.replace(
        '        "Both `SOFT_MEMORY_LIMIT_IN_MB` and `HARD_MEMORY_LIMIT_IN_MB` must be set to enable memory limits."\n'
        "        )\n",
        '        "Both `SOFT_MEMORY_LIMIT_IN_MB` and `HARD_MEMORY_LIMIT_IN_MB` must be set to enable memory limits."\n'
        "        )\n\n"
        "    if resource is None:\n"
        "        return\n",
        1,
    )
    if guarded == original:
        raise RuntimeError(
            f"win32 rlimit guard for {target} did not change the file"
        )
    target.write_text(guarded, encoding="utf-8", newline="\n")
    applied.append("saleor/core/rlimit.py: guard Unix-only `resource` import (win32 only)")
    return applied


def _run_command(
    argv: Sequence[str],
    cwd: Path,
    env: dict[str, str],
    timeout: int,
    label: str,
    *,
    logs_dir: Path | None = None,
    log_prefix: str = "",
    heartbeat_sink: Any | None = None,
    heartbeat_interval: float = 30.0,
) -> dict[str, object]:
    """Run a command, capturing its full log, with a live heartbeat.

    The captured-log semantics (full bounded log, tail in the record,
    timeout fail-closed, FileNotFound fail-closed) are unchanged. A daemon
    heartbeat thread emits ``[repo-preflight]`` START/RUNNING/END lines on a
    ``heartbeat_sink`` (default ``print``) every ``heartbeat_interval`` seconds
    so long-running commands (e.g. the full Saleor suite) are observable instead
    of appearing hung. The thread always stops and is joined before returning.
    """
    import threading

    sink = heartbeat_sink if heartbeat_sink is not None else print
    repo_tag = log_prefix or "shared"
    log_path_rel = ""
    if logs_dir is not None:
        log_file = logs_dir / f"{log_prefix}-{label}.log"
        log_path_rel = log_file.relative_to(logs_dir.parent).as_posix()

    start = time.monotonic()
    sink(
        f"[repo-preflight] START repo={repo_tag} label={label} "
        f"timeout={timeout}s log={log_path_rel or 'none'}"
    )

    stop_event = threading.Event()

    def _heartbeat() -> None:
        while not stop_event.wait(heartbeat_interval):
            elapsed = round(time.monotonic() - start, 1)
            sink(
                f"[repo-preflight] RUNNING repo={repo_tag} label={label} "
                f"elapsed={elapsed}s"
            )

    heartbeat = threading.Thread(target=_heartbeat, daemon=True)
    heartbeat.start()
    try:
        proc = subprocess.run(
            argv,
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        duration = round(time.monotonic() - start, 2)
        combined = proc.stdout + proc.stderr
        record: dict[str, object] = {
            "label": label,
            "command": argv,
            "passed": proc.returncode == 0,
            "exit_code": proc.returncode,
            "duration_seconds": duration,
            "output_tail": _tail_output(combined),
        }
    except subprocess.TimeoutExpired as exc:
        duration = round(time.monotonic() - start, 2)
        parts: list[str] = []
        out = getattr(exc, "output", None)
        if out:
            parts.append(out if isinstance(out, str) else out.decode(errors="replace"))
        err = getattr(exc, "stderr", None)
        if err:
            parts.append(err if isinstance(err, str) else err.decode(errors="replace"))
        combined = "\n".join(parts) if parts else ""
        record = {
            "label": label,
            "command": argv,
            "passed": False,
            "exit_code": -1,
            "duration_seconds": duration,
            "output_tail": _tail_output(combined),
        }
    except FileNotFoundError:
        duration = round(time.monotonic() - start, 2)
        combined = f"command not found: {argv[0]}"
        record = {
            "label": label,
            "command": argv,
            "passed": False,
            "exit_code": -1,
            "duration_seconds": duration,
            "output_tail": combined,
        }
    finally:
        stop_event.set()
        heartbeat.join(timeout=1.0)
    sink(
        f"[repo-preflight] END repo={repo_tag} label={label} "
        f"exit={record['exit_code']} duration={record['duration_seconds']}s"
    )

    if logs_dir is not None:
        log_file = logs_dir / f"{log_prefix}-{label}.log"
        _write_bounded_log(combined, log_file)
        record["log_path"] = log_file.relative_to(logs_dir.parent).as_posix()
    return record


_DIAGNOSTIC_VERSIONS_SNIPPET = r"""import json, os, sys, platform, time
out = {
    "python_version": "%d.%d.%d" % sys.version_info[:3],
    "platform": platform.platform(),
    "timezone": (time.tzname[0] if time.tzname else ""),
    "cpu_count": os.cpu_count(),
    "pytest_version": getattr(__import__("pytest"), "__version__", ""),
}
try:
    out["xdist_version"] = __import__("xdist").__version__
except Exception as exc:
    out["xdist_version"] = "unavailable: %s" % type(exc).__name__
try:
    db_url = os.environ.get("DATABASE_URL", "")
    conn_mod = None
    try:
        import psycopg2 as conn_mod
    except Exception:
        try:
            import psycopg as conn_mod
        except Exception:
            pass
    if conn_mod is not None and db_url:
        conn = conn_mod.connect(db_url)
        cur = conn.cursor()
        cur.execute("SHOW server_version")
        out["postgresql_server_version"] = str(cur.fetchone()[0])
        conn.close()
    else:
        out["postgresql_server_version"] = "no DATABASE_URL or driver"
except Exception as exc:
    out["postgresql_server_version"] = "unavailable: %s" % type(exc).__name__
try:
    import redis
    info = redis.Redis.from_url(os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")).info("server")
    out["redis_server_version"] = str(info.get("redis_version", info.get("valkey_version", "")))
except Exception as exc:
    out["redis_server_version"] = "unavailable: %s" % type(exc).__name__
print(json.dumps(out, sort_keys=True))
"""


def _collect_diagnostic_versions(
    python: str, env: dict[str, str], *, timeout: int = 90
) -> dict[str, object]:
    """Best-effort environment versions (python/platform/PG/Redis)."""
    try:
        proc = subprocess.run(
            [python, "-c", _DIAGNOSTIC_VERSIONS_SNIPPET],
            cwd=str(PROJECT_ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if proc.returncode != 0:
            return {
                "error": (
                    f"exit={proc.returncode}: "
                    f"{_tail_output(proc.stdout + proc.stderr)}"
                )
            }
        payload = json.loads(proc.stdout)
        if not isinstance(payload, dict):
            return {"error": "unexpected non-object stdout"}
        return payload
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}


def _run_lastfailed_serial(
    python: str,
    staging_dir: Path,
    env: dict[str, str],
    timeout: int,
    logs_dir: Path | None,
) -> dict[str, object]:
    """Serial, single-process rerun of just the lastfailed tests.

    Diagnostic-only: the result is never added to the declared command list and
    never changes the primary verdict.
    """
    argv = [python, "-m", "pytest", "--lf", "-n", "0", "-x", "-vv", "--tb=long"]
    return _run_command(
        argv,
        staging_dir,
        env,
        timeout,
        "lastfailed-serial",
        logs_dir=logs_dir,
        log_prefix=staging_dir.name,
    )


_SKIPPED_NO_LASTFAILED: dict[str, object] = {
    "lastfailed_serial_status": "SKIPPED_NO_LASTFAILED",
    "lastfailed_serial_command": None,
    "lastfailed_serial_exit_code": None,
    "lastfailed_serial_passed": None,
    "lastfailed_serial_output_tail": "",
    "lastfailed_serial_log_path": "",
}


def _collect_saleor_failure_diagnostics(
    *,
    python: str,
    staging_dir: Path,
    env: dict[str, str],
    timeout: int,
    primary: dict[str, object],
    logs_dir: Path | None,
    precomputed_lastfailed: object = _PRECOMPUTED_UNSET,
) -> dict[str, object]:
    """Persistable evidence for a FAILED Saleor primary run.

    Captures the pytest ``lastfailed`` cache BEFORE the serial rerun, groups the
    failing nodeids by source file and subtree prefix, and runs a serial
    ``--lf`` rerun to prove whether the failures reproduce head-of-file.

    The serial diagnostic is only executed when the primary run left a non-empty
    ``lastfailed`` cache.  An absent, unreadable, or empty cache is recorded as
    ``SKIPPED_NO_LASTFAILED`` so the diagnostic can never accidentally become a
    full serial Saleor suite.

    ``precomputed_lastfailed`` lets a caller that captured the cache BEFORE any
    baseline-flake serial reruns (which rewrite the cache) preserve the true
    primary failure set; omit it to read the current on-disk cache.
    """
    if precomputed_lastfailed is _PRECOMPUTED_UNSET:
        lastfailed = _load_lastfailed(staging_dir)
    else:
        lastfailed = cast(
            "tuple[int, tuple[str, ...]] | None", precomputed_lastfailed
        )
    nodeids = lastfailed[1] if lastfailed is not None else ()
    if lastfailed is not None and len(nodeids) > 0:
        raw = _run_lastfailed_serial(python, staging_dir, env, timeout, logs_dir)
        serial: dict[str, object] = {
            "lastfailed_serial_status": "RAN",
            "lastfailed_serial_command": raw.get("command"),
            "lastfailed_serial_exit_code": raw.get("exit_code"),
            "lastfailed_serial_passed": raw.get("passed"),
            "lastfailed_serial_output_tail": raw.get("output_tail", ""),
            "lastfailed_serial_log_path": raw.get("log_path", ""),
        }
    else:
        serial = dict(_SKIPPED_NO_LASTFAILED)
    return {
        "repo_id": "saleor",
        "primary_command": primary.get("command"),
        "primary_exit_code": primary.get("exit_code"),
        "primary_command_log_path": primary.get("log_path", ""),
        "failed_count": len(nodeids),
        "failed_nodeids": list(nodeids),
        "failures_by_source_file": _group_failures_by_source_file(nodeids),
        "failed_subtree_prefixes": list(_failed_subtree_prefixes(nodeids)),
        "lastfailed_cache_read": lastfailed is not None,
        **serial,
        "diagnostic_versions": _collect_diagnostic_versions(python, env),
        "created_utc": datetime.now(UTC).isoformat(),
    }


def run_repo_preflight(
    repo_id: str,
    staging_dir: Path,
    repo_cache: Path | None,
    venv_python: str,
    command: FrozenValidationCommand,
    timeout: int,
    pins: tuple[RepositoryPin, ...] = DEFAULT_PINS,
    repo_source: Path | None = None,
    logs_dir: Path | None = None,
    diagnostics_dir: Path | None = None,
    baseline_profile: dict[str, object] | None = None,
    emit_baseline_profile_path: Path | None = None,
    profile_source_commit: str = "unrecorded",
) -> dict[str, object]:
    """Materialize one pristine snapshot and run every frozen command in it.

    ``repo_source`` (an already-materialized repository tree, e.g. a bundled
    Kaggle snapshot) bypasses git-checkout materialization while preserving the
    pristine-staging contract: the tree is re-staged with the same
    deterministic copy rules and evidence is recomputed over the staged copy.

    PASS/FAIL is fail-closed: ``passed`` requires BOTH every declared required
    service to be reachable AND every frozen command to exit 0. The returned
    record distinguishes service checks, command checks and the overall result.

    Saleor baseline-flake policy (v0.9.20): when the PRISTINE primary command
    fails with exactly the frozen baseline-flaky nodeid set (loaded via
    ``baseline_profile``) AND every failed nodeid still passes a current serial
    rerun, the failure is explicitly classified instead of failing the
    preflight. Any new nodeid, any deterministically re-failing nodeid, or a
    missing/unmatched profile fails closed. Raw command results always keep
    their truthful non-zero exit codes; the classification is recorded
    separately in ``baseline_classification``.
    """
    pin = next((p for p in pins if p.repo_id == repo_id), None)
    if pin is None:
        raise RuntimeError(f"no RepositoryPin defined for '{repo_id}'")
    if repo_source is not None:
        if not repo_source.is_dir():
            raise RuntimeError(
                f"repo_source for '{repo_id}' is not a directory: {repo_source}"
            )
        _copy_embedded_tree(repo_source, staging_dir)
        evidence = SnapshotEvidence(
            repo_id=pin.repo_id,
            mode="bundled",
            requested_sha=pin.commit_sha,
            resolved_head="bundled",
            file_count=_count_files(staging_dir),
            content_hash=_tree_content_hash(staging_dir),
            size_bytes=_total_size(staging_dir),
        )
    else:
        evidence = materialize_repository(
            pin,
            repo_cache=repo_cache,
            target_dir=staging_dir,
            allow_acquire=True,
        )
    workarounds = apply_windows_infra_workarounds(staging_dir, repo_id)
    print(
        f"  STAGING repo={repo_id} mode={evidence.mode} "
        f"files={evidence.file_count} hash={evidence.content_hash[:12]}"
    )
    env = dict(os.environ)
    env.update(command.env_dict())
    services = _resolve_services(command.services, command.env_dict())
    services_passed = all(
        not bool(entry["required"]) or bool(entry["reachable"]) for entry in services
    )
    runs: list[dict[str, object]] = []
    all_passed = True
    saleor_gate_record: dict[str, object] | None = None

    # Fast Saleor capability gate: run the known failing checkout test serially
    # BEFORE the full 6k primary suite. This proves PG15 migration/constraint
    # path without spending ~13 minutes on the full suite.
    if repo_id == "saleor" and services_passed:
        saleor_gate_test = (
            "saleor/graphql/checkout/tests/benchmark/test_checkout_mutations.py"
            "::test_create_checkout"
        )
        gate_argv = [
            venv_python,
            "-m", "pytest", "-n", "0", "-x", "--tb=line", "--no-header", "-q",
            saleor_gate_test,
        ]
        if gate_argv.count("-m") != 1 or gate_argv[1:3] != ["-m", "pytest"]:
            raise RuntimeError("invalid Saleor capability-gate argv")
        print(f"  Saleor fast capability gate: {saleor_gate_test}")
        gate_result = _run_command(
            gate_argv,
            staging_dir,
            env,
            min(timeout, 300),
            "saleor-gate",
            logs_dir=logs_dir,
            log_prefix=repo_id,
            heartbeat_sink=print,
            heartbeat_interval=30.0,
        )
        saleor_gate_record = gate_result
        if not gate_result.get("passed"):
            gate_log = gate_result.get("log_path", "")
            gate_tail = cast(str, gate_result.get("output_tail", ""))
            print(
                f"  Saleor fast capability gate: FAIL (exit={gate_result.get('exit_code')})\n"
                f"  Skipping full 6k Saleor suite. Gate log: {gate_log}\n"
                f"  Output tail: {gate_tail[:500]}"
            )
            runs.append(gate_result)
            all_passed = False
            result_record: dict[str, object] = {
                "repo_id": repo_id,
                "mode": evidence.mode,
                "requested_sha": evidence.requested_sha,
                "resolved_head": evidence.resolved_head,
                "file_count": evidence.file_count,
                "content_hash": evidence.content_hash,
                "applied_workarounds": workarounds,
                "services": services,
                "services_passed": services_passed,
                "commands": runs,
                "command_passed": False,
                "passed": False,
                "saleor_gate_skipped_full_suite": True,
                "saleor_capability_gate": gate_result,
            }
            if diagnostics_dir is not None:
                diagnostics_dir.mkdir(parents=True, exist_ok=True)
                diagnostics = _collect_saleor_failure_diagnostics(
                    python=venv_python,
                    staging_dir=staging_dir,
                    env=env,
                    timeout=timeout,
                    primary=gate_result,
                    logs_dir=logs_dir,
                )
                diagnostics_path = diagnostics_dir / "saleor_failure_diagnostics.json"
                diagnostics_path.write_text(
                    json.dumps(diagnostics, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
            return result_record
        print("  Saleor fast capability gate: PASS")

    for label, argv in (
        ("primary", command.resolve_interpreter(venv_python)),
        *(
            (f"additional-{idx}", list(extra))
            for idx, extra in enumerate(command.resolved_additional_commands(venv_python))
        ),
    ):
        result = _run_command(
            argv,
            staging_dir,
            env,
            timeout,
            label,
            logs_dir=logs_dir,
            log_prefix=repo_id,
        )
        runs.append(result)
        all_passed = all_passed and bool(result["passed"])
    result_record = {
        "repo_id": repo_id,
        "mode": evidence.mode,
        "requested_sha": evidence.requested_sha,
        "resolved_head": evidence.resolved_head,
        "file_count": evidence.file_count,
        "content_hash": evidence.content_hash,
        "applied_workarounds": workarounds,
        "services": services,
        "services_passed": services_passed,
        "commands": runs,
        "command_passed": all_passed,
        "saleor_capability_gate": saleor_gate_record,
    }
    baseline_tolerated = False
    if repo_id == "saleor" and runs and not bool(runs[0].get("passed")):
        # Capture the primary failure set BEFORE any serial rerun rewrites the
        # pytest lastfailed cache.
        captured_lastfailed = _load_lastfailed(staging_dir)
        failed_nodeids = captured_lastfailed[1] if captured_lastfailed else ()
        serial_reruns: list[dict[str, object]] = []
        if failed_nodeids and (
            baseline_profile is not None or emit_baseline_profile_path is not None
        ):
            serial_reruns = [
                _serial_rerun_nodeid(
                    venv_python,
                    staging_dir,
                    env,
                    min(timeout, 300),
                    nodeid,
                    logs_dir,
                    repo_id,
                )
                for nodeid in sorted(failed_nodeids)
            ]
        if emit_baseline_profile_path is not None:
            profile_payload = build_baseline_profile_evidence(
                saleor_commit_sha=pin.commit_sha,
                frozen_validation_command=list(command.command),
                environment_versions=dict(
                    _collect_diagnostic_versions(venv_python, env)
                ),
                full_run_exit_code=runs[0].get("exit_code"),
                full_run_duration_seconds=runs[0].get("duration_seconds"),
                failed_nodeids=failed_nodeids,
                serial_reruns=serial_reruns,
                created_utc=datetime.now(UTC).isoformat(),
                profile_source_commit=profile_source_commit,
                platform_name=sys.platform,
            )
            emit_baseline_profile_path.parent.mkdir(parents=True, exist_ok=True)
            emit_baseline_profile_path.write_text(
                json.dumps(profile_payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            result_record["emitted_baseline_profile"] = {
                "path": str(emit_baseline_profile_path),
                "nodeid_count": len(failed_nodeids),
                "all_serial_passed": all(
                    bool(v.get("passed")) for v in serial_reruns
                ),
            }
        if baseline_profile is not None:
            if not failed_nodeids:
                classification: dict[str, object] = {
                    "status": "NOT_CLASSIFIED_NO_LASTFAILED",
                    "profile_schema": baseline_profile.get("schema"),
                    "observed_count": 0,
                    "classified": False,
                }
            else:
                classification = classify_saleor_failures_against_profile(
                    failed_nodeids, serial_reruns, baseline_profile
                )
            result_record["baseline_classification"] = classification
            baseline_tolerated = bool(classification["classified"])
        if diagnostics_dir is not None:
            diagnostics_dir.mkdir(parents=True, exist_ok=True)
            diagnostics = _collect_saleor_failure_diagnostics(
                python=venv_python,
                staging_dir=staging_dir,
                env=env,
                timeout=timeout,
                primary=runs[0],
                logs_dir=logs_dir,
                precomputed_lastfailed=captured_lastfailed,
            )
            diagnostics_path = diagnostics_dir / "saleor_failure_diagnostics.json"
            diagnostics_path.write_text(
                json.dumps(diagnostics, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            result_record["failure_diagnostics"] = {
                "path": diagnostics_path.relative_to(diagnostics_dir).as_posix(),
                "failed_count": diagnostics["failed_count"],
                "failed_subtree_prefixes": diagnostics["failed_subtree_prefixes"],
            }
    result_record["passed"] = (all_passed or baseline_tolerated) and services_passed
    return result_record


def run_preflight(
    manifest_path: Path,
    staging_root: Path,
    repo_cache: Path | None,
    venv_pythons: dict[str, str],
    repos: tuple[str, ...],
    timeout: int,
    repo_sources: dict[str, Path] | None = None,
    baseline_profile_path: Path | None = None,
    emit_baseline_profile_path: Path | None = None,
    profile_source_commit: str = "unrecorded",
) -> dict[str, object]:
    """Run the frozen validation contract against pristine staged snapshots."""
    from benchmark.repositories.validation_commands import load_validation_commands

    manifest = load_validation_commands(manifest_path)
    baseline_profile: dict[str, object] | None = None
    if baseline_profile_path is not None:
        pin = next(
            (p for p in DEFAULT_PINS if p.repo_id == "saleor"), None
        )
        if pin is None:
            raise RuntimeError("no RepositoryPin defined for 'saleor'")
        baseline_profile = load_baseline_profile(
            baseline_profile_path,
            expected_saleor_sha=pin.commit_sha,
            expected_frozen_command=list(manifest.require("saleor").command),
        )
    results: dict[str, object] = {}
    all_passed = True
    for repo_id in repos:
        command = manifest.require(repo_id)
        python = venv_pythons.get(repo_id)
        if not python:
            raise RuntimeError(
                f"no interpreter provided for '{repo_id}' (--venv-python {repo_id}=<path>)"
            )
        repo_staging = staging_root / repo_id
        if repo_staging.is_dir():
            shutil.rmtree(repo_staging)
        repo_staging.mkdir(parents=True, exist_ok=True)
        try:
            result = run_repo_preflight(
                repo_id=repo_id,
                staging_dir=repo_staging,
                repo_cache=repo_cache,
                venv_python=python,
                command=command,
                timeout=timeout,
                repo_source=(repo_sources or {}).get(repo_id),
                logs_dir=staging_root / "logs",
                diagnostics_dir=staging_root,
                baseline_profile=baseline_profile,
                emit_baseline_profile_path=(
                    emit_baseline_profile_path if repo_id == "saleor" else None
                ),
                profile_source_commit=profile_source_commit,
            )
        except Exception as exc:
            result = {
                "repo_id": repo_id,
                "passed": False,
                "error": f"{type(exc).__name__}: {exc}",
            }
        results[repo_id] = result
        all_passed = all_passed and bool(result["passed"])
    return {
        "task": "PILOT-EXEC-01",
        "manifest": str(manifest_path),
        "created_utc": datetime.now(UTC).isoformat(),
        "platform": sys.platform,
        "staging_root": str(staging_root),
        "overall": "PASS" if all_passed else "FAIL",
        "repositories": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pilot_repo_snapshot",
        description=(
            "Deterministic, fail-closed materialization and engineering "
            "preflight of frozen Pilot repository snapshots."
        ),
    )
    subparsers = parser.add_subparsers(dest="command")

    materialize = subparsers.add_parser("materialize", help="materialize snapshots")
    materialize.add_argument("--output-root", type=Path, required=True)
    materialize.add_argument("--repo-cache", type=Path, default=None)
    materialize.add_argument("--allow-acquire", action="store_true", default=False)

    preflight = subparsers.add_parser(
        "preflight",
        help="run the frozen validation command per repo on pristine snapshots",
    )
    preflight.add_argument(
        "--manifest", type=Path, default=DEFAULT_MANIFEST
    )
    preflight.add_argument("--staging-root", type=Path, required=True)
    preflight.add_argument("--repo-cache", type=Path, default=None)
    preflight.add_argument(
        "--venv-python",
        action="append",
        default=[],
        metavar="repo_id=path",
        help="Python interpreter for one repository (repeatable).",
    )
    preflight.add_argument(
        "--repo-source",
        action="append",
        default=[],
        metavar="repo_id=path",
        help=(
            "Already-materialized repository tree to preflight (repeatable); "
            "bypasses git-checkout materialization for bundled Kaggle snapshots."
        ),
    )
    preflight.add_argument(
        "--repos",
        default="todo,djangocms,saleor",
        help="Comma-separated repositories to preflight (default: all).",
    )
    preflight.add_argument(
        "--timeout", type=int, default=3600, help="Per-command timeout (seconds)."
    )
    preflight.add_argument(
        "--baseline-profile",
        type=Path,
        default=None,
        help=(
            "Frozen Saleor baseline-flake profile JSON; when provided, a "
            "pristine primary failure whose exact nodeids all match the "
            "profile AND still pass serial reruns is classified instead of "
            "failing the preflight (fail-closed otherwise)."
        ),
    )
    preflight.add_argument(
        "--emit-baseline-profile",
        type=Path,
        default=None,
        help=(
            "Write baseline-flake evidence (exact failed nodeids + per-nodeid "
            "serial rerun verdicts) to this path after a failed pristine "
            "Saleor run. Never changes the pass/fail verdict."
        ),
    )
    preflight.add_argument(
        "--profile-source-commit",
        default="unrecorded",
        help="Project source commit recorded inside an emitted baseline profile.",
    )
    preflight.add_argument("--out", type=Path, required=True, help="Result JSON path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "materialize":
        evidence = materialize_repositories(
            data_repositories_dir=args.output_root / "data" / "repositories",
            repo_cache=args.repo_cache,
            allow_acquire=args.allow_acquire,
        )
        print(json.dumps(evidence, indent=2, sort_keys=True))
        return 0
    if args.command == "preflight":
        venv_pythons: dict[str, str] = {}
        for item in args.venv_python:
            repo_id, _, python = item.partition("=")
            if not repo_id or not python:
                raise SystemExit(f"invalid --venv-python value: {item!r}")
            venv_pythons[repo_id] = python
        repo_sources: dict[str, Path] = {}
        for item in args.repo_source:
            repo_id, _, source = item.partition("=")
            if not repo_id or not source:
                raise SystemExit(f"invalid --repo-source value: {item!r}")
            repo_sources[repo_id] = Path(source)
        repos = tuple(r for r in args.repos.split(",") if r)
        result = run_preflight(
            manifest_path=args.manifest,
            staging_root=args.staging_root,
            repo_cache=args.repo_cache,
            venv_pythons=venv_pythons,
            repos=repos,
            timeout=args.timeout,
            repo_sources=repo_sources,
            baseline_profile_path=args.baseline_profile,
            emit_baseline_profile_path=args.emit_baseline_profile,
            profile_source_commit=args.profile_source_commit,
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(f"overall: {result['overall']}")
        repositories = cast("dict[str, dict[str, object]]", result["repositories"])
        for repo_id, entry in repositories.items():
            print(f"  {repo_id}: {'PASS' if entry['passed'] else 'FAIL'}")
        return 0 if result["overall"] == "PASS" else 1
    raise SystemExit("subcommand required: materialize | preflight")


if __name__ == "__main__":
    raise SystemExit(main())
