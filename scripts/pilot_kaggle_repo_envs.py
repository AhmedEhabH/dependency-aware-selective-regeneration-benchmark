#!/usr/bin/env python3
"""PILOT-EXEC-01: dependency-aware repository environment provisioning closure.

Solves the exact Kaggle failure observed on the real Pilot session
(``pilot-repo-preflight-cell``)::

    /usr/bin/python3 -m venv /kaggle/working/pilot_envs/djangocms
    -> Command [ENV/bin/python3, -m ensurepip, --upgrade, --default-pip]
       returned non-zero exit status 1

Root cause: the Kaggle benchmark interpreter cannot bootstrap ``ensurepip``
into a fresh ``venv``. Every Python 3.10+ ``venv`` that is not created with
``--without-pip`` attempts an ``ensurepip`` bootstrap and fails on that
session. The tools/uv env used the SAME latent pattern (``-m venv`` then
``ENV/bin/python -m pip install uv``) and would fail identically.

The fix (02_EXACT_PROVISIONING_DESIGN.md):

- every stdlib venv is created with ``--without-pip`` (``ensurepip`` never
  runs; the target env is a deliberately pip-less tool/target);
- the host (benchmark) pip manages the isolated no-pip target envs via
  ``pip --python <target>`` (documented pip 22.3+ feature for envs without
  pip) - NO repository dependency is ever installed into the benchmark/model
  interpreter;
- a dedicated no-pip ``tools`` env receives ``uv`` via host pip ``--python``;
- django CMS: ``uv pip install -r test_requirements/django-5.0.txt`` from the
  frozen snapshot root with ``--python <django venv>``;
- Saleor: ``uv venv .venv --python <existing 3.12>`` with
  ``UV_PYTHON_DOWNLOADS=never`` (no silent Python download/switch) then
  ``uv sync --locked`` against the frozen ``uv.lock``;
- completion markers (``.pilot_env_ready.json``, schema
  ``pilot_repo_environment.v1``) record schema, repo id, Pilot source tag,
  Python major/minor and dependency file + SHA-256; a valid marker + health
  probe allows reuse; any mismatch rebuilds ONLY the specific private env dir;
- visible ``START``/``END``/elapsed output with heartbeats on long installs and
  a provisioning log that never records secret values.

This module is bundled into the Kaggle artifact under
``code/scripts/pilot_kaggle_repo_envs.py``; the notebook cell is a thin caller.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.parse
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO

MARKER_SCHEMA = "pilot_repo_environment.v1"
MARKER_NAME = ".pilot_env_ready.json"

REQUIRED_OS_PACKAGES: tuple[str, ...] = ("gettext", "gcc", "libpq-dev")

# Every upstream OS prerequisite above is mandatory (gettext + gcc for django
# CMS ``manage.py test`` asset/markup building, libpq-dev for Saleor's psycopg).
# They are installed in ONE apt transaction - unlike the Redis alternatives bug,
# there is no candidate fallback to choose from.
_APT_ENV: dict[str, str] = {"DEBIAN_FRONTEND": "noninteractive"}
_APT_UPDATED: bool = False

DEFAULT_SERVICE_URLS: tuple[tuple[str, str], ...] = (
    ("postgresql", "postgres://saleor:saleor@127.0.0.1:5433/saleor"),
    ("valkey", "redis://127.0.0.1:6379/0"),
)

_SALEOR_REQUIRED_SERVICES: frozenset[str] = frozenset({"postgresql", "valkey"})

_IDENTITY_KEYS: tuple[str, ...] = (
    "schema",
    "repo_id",
    "source_tag",
    "python_major_minor",
    "dependency_sha256",
)

_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(HF_TOKEN\s*=\s*)[^\s;,}]+"),
    re.compile(r"(SECRET_KEY\s*=\s*)[^\s;,}]+"),
    re.compile(r"(PGPASSWORD\s*=\s*)[^\s;,}]+"),
)


class ProvisioningError(RuntimeError):
    """Fail-closed provisioning failure with the command, exit code and tail."""

    def __init__(
        self,
        message: str,
        *,
        command: list[str] | None = None,
        exit_code: int | None = None,
        tail: str | None = None,
    ) -> None:
        super().__init__(message)
        self.command = command
        self.exit_code = exit_code
        self.tail = tail


class ProvisioningLog:
    """Appends sanitized provisioning lines to stdout and the log file."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path: Path | None = Path(path) if path else None
        self._fh: TextIO | None = None
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._fh = self.path.open("a", encoding="utf-8", newline="\n")

    def emit(self, message: object) -> None:
        line = _sanitize(str(message))
        print(line, flush=True)
        if self._fh is not None:
            self._fh.write(line + "\n")
            self._fh.flush()

    def close(self) -> None:
        if self._fh is not None:
            self._fh.close()
            self._fh = None


def _sanitize(text: str) -> str:
    out = text
    for pattern in _SECRET_PATTERNS:
        out = pattern.sub(r"\1***", out)
    return out


def _tail_output(raw: str, *, max_lines: int = 25) -> str:
    lines = [line.rstrip("\r") for line in raw.splitlines() if line.strip()]
    return "\n".join(lines[-max_lines:])


def run_command(
    argv: list[str] | tuple[str, ...],
    *,
    cwd: str | Path | None = None,
    env: dict[str, str] | None = None,
    timeout: int | None = None,
    log: ProvisioningLog | None = None,
    label: str = "",
    heartbeat: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run ``argv`` with visible START/END/elapsed output and fail-closed tail."""
    argv_list = [str(a) for a in argv]
    command_repr = " ".join(argv_list)
    stage = label or command_repr
    start = time.monotonic()
    if log is not None:
        log.emit(f"START {stage}")

    stop = threading.Event()

    def _beat() -> None:
        while not stop.wait(30):
            if log is not None:
                log.emit(f"  [elapsed {time.monotonic() - start:.0f}s] {stage} still running")

    timer: threading.Thread | None = None
    if heartbeat and log is not None:
        timer = threading.Thread(target=_beat, daemon=True)
        timer.start()
    try:
        proc = subprocess.run(
            argv_list,
            cwd=str(cwd) if cwd else None,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        if timer is not None:
            stop.set()
            timer.join()
        if log is not None:
            log.emit(f"END {stage} FAILED elapsed={time.monotonic() - start:.0f}s timeout={timeout}s")
        raise ProvisioningError(
            f"command timed out after {timeout}s: {command_repr}",
            command=argv_list,
            exit_code=-1,
            tail=_tail_output(str(getattr(exc, "output", "") or "")),
        ) from exc
    if timer is not None:
        stop.set()
        timer.join()
    elapsed = time.monotonic() - start
    if proc.returncode != 0:
        tail = _tail_output((proc.stdout or "") + (proc.stderr or ""))
        if log is not None:
            log.emit(f"END {stage} FAILED elapsed={elapsed:.0f}s exit={proc.returncode}\n{tail}")
        raise ProvisioningError(
            f"command failed (exit={proc.returncode}): {command_repr}",
            command=argv_list,
            exit_code=proc.returncode,
            tail=tail,
        )
    if log is not None:
        log.emit(f"END {stage} elapsed={elapsed:.0f}s exit=0")
    return proc


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _interpreter_for(env_dir: Path) -> Path | None:
    for name in ("bin/python", "bin/python3", "Scripts/python.exe", ".venv/bin/python"):
        candidate = Path(env_dir) / name
        if candidate.is_file():
            return candidate
    return None


def _python_version(interpreter: Path | str, *, log: ProvisioningLog | None = None) -> tuple[int, int]:
    proc = run_command(
        [str(interpreter), "-c", "import sys; print('%d.%d' % sys.version_info[:2])"],
        log=log,
        label="python version probe",
        timeout=120,
    )
    text = (proc.stdout or "").strip()
    if not text:
        raise ProvisioningError(f"python version probe returned no output for {interpreter}")
    parts = text.splitlines()[-1].split(".")
    if len(parts) < 2:
        raise ProvisioningError(f"unexpected python version output: {text!r}")
    return (int(parts[0]), int(parts[1]))


def _python_is_venv(interpreter: Path | str, *, log: ProvisioningLog | None = None) -> bool:
    proc = run_command(
        [str(interpreter), "-c", "import sys; print(0 if sys.prefix == sys.base_prefix else 1)"],
        log=log,
        label="venv isolation probe",
        timeout=120,
    )
    return (proc.stdout or "").strip().endswith("1")


def _import_probe(interpreter: Path | str, module: str, *, log: ProvisioningLog | None = None) -> bool:
    try:
        run_command([str(interpreter), "-c", f"import {module}"], log=log, label=f"import {module} probe", timeout=120)
        return True
    except ProvisioningError:
        return False


def _django_probe(interpreter: Path | str, *, log: ProvisioningLog | None = None) -> bool:
    code = (
        "import django; v = django.VERSION[:2]; "
        "assert v[0] == 5 and 0 <= v[1] < 1, v; "
        "import cms"
    )
    try:
        run_command([str(interpreter), "-c", code], log=log, label="django 5.0 + cms probe", timeout=120)
        return True
    except ProvisioningError:
        return False


def _django_version(interpreter: Path | str, *, log: ProvisioningLog | None = None) -> str:
    proc = run_command(
        [str(interpreter), "-c", "import django; print(django.get_version())"],
        log=log,
        label="django version probe",
        timeout=120,
    )
    text = (proc.stdout or "").strip()
    if not text:
        raise ProvisioningError(f"django version probe returned no output for {interpreter}")
    return text.splitlines()[-1]


def _saleor_probe(interpreter: Path | str, *, log: ProvisioningLog | None = None) -> bool:
    return _import_probe(interpreter, "saleor", log=log)


def _uv_version(uv_bin: Path, *, log: ProvisioningLog | None = None) -> str:
    proc = run_command([str(uv_bin), "--version"], log=log, label="uv version probe", timeout=120)
    text = (proc.stdout or "").strip()
    if not text:
        raise ProvisioningError(f"uv version probe returned no output for {uv_bin}")
    return text.splitlines()[-1].removeprefix("uv").strip() or text.splitlines()[-1]


def _read_marker(env_dir: Path) -> dict[str, Any] | None:
    marker_path = Path(env_dir) / MARKER_NAME
    if not marker_path.is_file():
        return None
    try:
        data = json.loads(marker_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _write_marker(env_dir: Path, marker: dict[str, Any]) -> None:
    target = Path(env_dir)
    target.mkdir(parents=True, exist_ok=True)
    (target / MARKER_NAME).write_text(
        json.dumps(marker, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _needs_rebuild(
    env_dir: Path,
    expected: dict[str, Any],
    *,
    probe: Callable[[Path], bool],
) -> str | None:
    """Return the rebuild reason or ``None`` when the env is valid and reusable."""
    if not Path(env_dir).is_dir():
        return "env path absent"
    marker_path = Path(env_dir) / MARKER_NAME
    if not marker_path.is_file():
        return "completion marker missing"
    marker = _read_marker(env_dir)
    for key in _IDENTITY_KEYS:
        if marker is None or marker.get(key) != expected[key]:
            return f"marker {key} mismatch"
    interp = _interpreter_for(env_dir)
    if interp is None:
        return "interpreter missing"
    actual = list(_python_version(interp))
    if actual != expected["python_major_minor"]:
        return "python version mismatch"
    if not probe(interp):
        return "health probe failed"
    return None


def _remove_private_env(env_dir: Path, *, log: ProvisioningLog | None = None) -> None:
    """Remove ONLY the specific private environment directory - never more."""
    target = Path(env_dir)
    if target.exists() or target.is_symlink():
        if log is not None:
            log.emit(f"Removing incomplete private environment {target}")
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
        else:
            target.unlink()


def create_no_pip_venv(
    python_exe: str | Path,
    env_dir: str | Path,
    *,
    log: ProvisioningLog | None = None,
) -> Path:
    """Create a stdlib venv with ``--without-pip`` (ensurepip never runs)."""
    host = Path(python_exe)
    target = Path(env_dir)
    target.parent.mkdir(parents=True, exist_ok=True)
    if log is not None:
        log.emit(f"Creating no-pip venv {target} with {host} (--without-pip; ensurepip never runs)")
    run_command(
        [str(host), "-m", "venv", "--without-pip", str(target)],
        log=log,
        label="venv --without-pip",
        timeout=600,
    )
    interp = _interpreter_for(target)
    if interp is None:
        raise ProvisioningError(f"venv created but no interpreter found under {target}")
    host_version = _python_version(host, log=log)
    env_version = _python_version(interp, log=log)
    if env_version != host_version:
        raise ProvisioningError(
            f"venv python version {env_version} does not match host {host_version} for {target}"
        )
    if not _python_is_venv(interp, log=log):
        raise ProvisioningError(
            f"expected an isolated venv but {interp} reports sys.prefix == sys.base_prefix"
        )
    return interp


def host_pip_target_ok(
    host_python: str | Path,
    target_interpreter: str | Path,
    *,
    log: ProvisioningLog | None = None,
) -> None:
    """Fail-fast: host pip must support ``--python`` target management."""
    run_command(
        [str(host_python), "-m", "pip", "--python", str(target_interpreter), "--version"],
        log=log,
        label="host pip --python capability probe",
        timeout=300,
    )


_PIP_TARGET_VERIFIED: set[str] = set()


def install_with_host_pip(
    host_python: str | Path,
    target_interpreter: str | Path,
    args: list[str] | tuple[str, ...],
    *,
    cwd: str | Path | None = None,
    env: dict[str, str] | None = None,
    log: ProvisioningLog | None = None,
    heartbeat: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Install into the isolated no-pip target env via host pip ``--python``."""
    target_key = str(target_interpreter)
    if target_key not in _PIP_TARGET_VERIFIED:
        host_pip_target_ok(host_python, target_interpreter, log=log)
        _PIP_TARGET_VERIFIED.add(target_key)
    return run_command(
        [str(host_python), "-m", "pip", "--python", str(target_interpreter), *[str(a) for a in args]],
        cwd=cwd,
        env=env,
        log=log,
        label="host pip --python install (isolated target env)",
        timeout=1800,
        heartbeat=heartbeat,
    )


def install_with_uv(
    uv_bin: str | Path,
    target_interpreter: str | Path,
    args: list[str] | tuple[str, ...],
    *,
    cwd: str | Path | None = None,
    env: dict[str, str] | None = None,
    log: ProvisioningLog | None = None,
    heartbeat: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Install into the isolated target env via uv pip ``--python``."""
    return run_command(
        [str(uv_bin), "pip", "install", "--python", str(target_interpreter), *[str(a) for a in args]],
        cwd=cwd,
        env=env,
        log=log,
        label="uv pip install (isolated target env)",
        timeout=1800,
        heartbeat=heartbeat,
    )


def _apt_get_available() -> bool:
    return shutil.which("apt-get") is not None


def _apt_update_once(log: ProvisioningLog | None = None) -> None:
    global _APT_UPDATED
    if _APT_UPDATED:
        return
    run_command(["apt-get", "update", "-qq"], env=_APT_ENV, log=log, label="apt-get update", timeout=600)
    _APT_UPDATED = True


_OS_PACKAGE_PROBES: dict[str, tuple[str, ...]] = {
    "gettext": ("msgfmt",),
    "gcc": ("gcc",),
    "libpq-dev": ("pg_config",),
}


def _probe_os_packages(packages: tuple[str, ...]) -> list[str]:
    missing: list[str] = []
    for package in packages:
        probes = _OS_PACKAGE_PROBES.get(package, (package,))
        if not any(shutil.which(candidate) is not None for candidate in probes):
            missing.append(package)
    return missing


def ensure_os_prerequisites(
    packages: tuple[str, ...] = REQUIRED_OS_PACKAGES,
    *,
    log: ProvisioningLog | None = None,
) -> dict[str, Any]:
    """Install all mandatory upstream OS prerequisites (one apt transaction)."""
    packages = tuple(packages)
    missing = _probe_os_packages(packages)
    if not missing:
        return {"packages": sorted(packages), "installed": False, "already_present": True}
    if not _apt_get_available():
        raise ProvisioningError(
            "required upstream OS packages are missing and apt-get is not available: "
            + ", ".join(missing)
        )
    if log is not None:
        log.emit(f"Installing upstream OS prerequisites in ONE apt transaction: {' '.join(missing)}")
    _apt_update_once(log=log)
    run_command(
        ["apt-get", "install", "-y", *missing],
        env=_APT_ENV,
        log=log,
        label="apt-get install upstream OS prerequisites",
        timeout=1200,
        heartbeat=True,
    )
    still_missing = _probe_os_packages(packages)
    if still_missing:
        raise ProvisioningError(
            "required upstream OS packages still missing after install: " + ", ".join(still_missing)
        )
    return {"packages": sorted(packages), "installed": True, "already_present": False}


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


def _probe_services(urls: tuple[tuple[str, str], ...] = DEFAULT_SERVICE_URLS) -> dict[str, dict[str, Any]]:
    return {
        name: {"url": url, "reachable": _service_reachable(url)}
        for name, url in urls
    }


def _find_python_312() -> Path | None:
    candidates = (shutil.which("python3.12"), "/usr/bin/python3.12", "/usr/local/bin/python3.12")
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate)
    return None


def provision_uv_tool(
    host_python: str | Path,
    tools_env: str | Path,
    *,
    source_tag: str,
    log: ProvisioningLog | None = None,
) -> dict[str, Any]:
    """Provision the dedicated no-pip uv tool env (host pip ``--python``)."""
    tools_env = Path(tools_env)
    host_version = _python_version(host_python, log=log)
    expected: dict[str, Any] = {
        "schema": MARKER_SCHEMA,
        "repo_id": "uv-tool",
        "source_tag": source_tag,
        "python_major_minor": list(host_version),
        "dependency_file": "uv",
        "dependency_sha256": "uv-tool",
    }

    def _uv_probe_checked(interp: Path) -> bool:
        uv_bin = interp.parent / "uv"
        if not uv_bin.is_file():
            return False
        try:
            run_command([str(uv_bin), "--version"], log=None, label="uv version probe", timeout=120)
            return True
        except ProvisioningError:
            return False

    reason = _needs_rebuild(tools_env, expected, probe=_uv_probe_checked)
    if reason is None:
        interp = _interpreter_for(tools_env)
        uv_bin = tools_env / "bin" / "uv"
        marker = _read_marker(tools_env)
        version = (marker or {}).get("uv_version", "") or _uv_version(uv_bin, log=log)
        return {
            "repo_id": "uv-tool",
            "env": str(tools_env),
            "python": str(interp) if interp else "",
            "bin": str(uv_bin),
            "uv_version": version,
            "version": version,
            "reused": True,
            "marker": str(tools_env / MARKER_NAME),
        }
    if log is not None:
        log.emit(f"START provision_uv_tool (rebuild: {reason})")
    _remove_private_env(tools_env, log=log)
    interp = create_no_pip_venv(host_python, tools_env, log=log)
    install_with_host_pip(host_python, interp, ["install", "uv"], log=log, heartbeat=True)
    uv_bin = tools_env / "bin" / "uv"
    if not uv_bin.is_file():
        raise ProvisioningError(f"uv binary missing after host pip --python install: {uv_bin}")
    version = _uv_version(uv_bin, log=log)
    marker = dict(expected)
    marker["uv_version"] = version
    _write_marker(tools_env, marker)
    if log is not None:
        log.emit(f"END provision_uv_tool: uv {version} at {uv_bin}")
    return {
        "repo_id": "uv-tool",
        "env": str(tools_env),
        "python": str(interp),
        "bin": str(uv_bin),
        "uv_version": version,
        "version": version,
        "reused": False,
        "marker": str(tools_env / MARKER_NAME),
    }


def provision_djangocms(
    host_python: str | Path,
    env_dir: str | Path,
    djangocms_root: str | Path,
    *,
    uv_bin: str | Path,
    source_tag: str,
    log: ProvisioningLog | None = None,
) -> dict[str, Any]:
    """Provision the isolated django CMS env from the exact frozen requirements."""
    env_dir = Path(env_dir)
    djangocms_root = Path(djangocms_root)
    req = djangocms_root / "test_requirements" / "django-5.0.txt"
    if not req.is_file():
        raise ProvisioningError(f"django CMS dependency file missing: {req} (test_requirements/django-5.0.txt)")
    dep_sha = _sha256_file(req)
    host_version = _python_version(host_python, log=log)
    expected: dict[str, Any] = {
        "schema": MARKER_SCHEMA,
        "repo_id": "djangocms",
        "source_tag": source_tag,
        "python_major_minor": list(host_version),
        "dependency_file": "test_requirements/django-5.0.txt",
        "dependency_sha256": dep_sha,
    }

    def _probe(interp: Path) -> bool:
        return _django_probe(interp, log=log)

    reason = _needs_rebuild(env_dir, expected, probe=_probe)
    if reason is None:
        return _djangocms_evidence(env_dir, host_version, dep_sha, source_tag, reused=True)
    if log is not None:
        log.emit(f"START provision_djangocms (rebuild: {reason})")
    _remove_private_env(env_dir, log=log)
    interp = create_no_pip_venv(host_python, env_dir, log=log)
    install_with_uv(
        uv_bin,
        interp,
        ["-r", "test_requirements/django-5.0.txt"],
        cwd=djangocms_root,
        log=log,
        heartbeat=True,
    )
    if not _django_probe(interp, log=log):
        raise ProvisioningError("django CMS health probe failed after install (Django >=5.0,<5.1 + import cms)")
    django_version = _django_version(interp, log=log)
    marker = dict(expected)
    marker["django_version"] = django_version
    _write_marker(env_dir, marker)
    if log is not None:
        log.emit(f"END provision_djangocms: Django {django_version} at {interp}")
    return _djangocms_evidence(
        env_dir,
        host_version,
        dep_sha,
        source_tag,
        reused=False,
        django_version=django_version,
    )


def _djangocms_evidence(
    env_dir: Path,
    host_version: tuple[int, int],
    dep_sha: str,
    source_tag: str,
    *,
    reused: bool,
    django_version: str = "",
) -> dict[str, Any]:
    marker = _read_marker(env_dir)
    interp = _interpreter_for(env_dir)
    return {
        "repo_id": "djangocms",
        "env": str(env_dir),
        "python": str(interp) if interp else "",
        "dependency_file": "test_requirements/django-5.0.txt",
        "dependency_sha256": dep_sha,
        "python_minor": list(host_version),
        "django_version": django_version or (marker or {}).get("django_version", ""),
        "source_tag": source_tag,
        "reused": reused,
        "marker": str(env_dir / MARKER_NAME),
    }


def provision_saleor(
    work_dir: str | Path,
    saleor_source: str | Path,
    *,
    uv_bin: str | Path,
    source_tag: str,
    python_312: str | Path | None = None,
    require_services: bool = True,
    log: ProvisioningLog | None = None,
) -> dict[str, Any]:
    """Provision the Saleor locked env (existing Python 3.12, uv sync --locked)."""
    work_dir = Path(work_dir)
    saleor_source = Path(saleor_source)
    if not saleor_source.is_dir():
        raise ProvisioningError(f"saleor source snapshot missing: {saleor_source}")
    lock = saleor_source / "uv.lock"
    if not lock.is_file():
        raise ProvisioningError(f"saleor uv.lock missing in source snapshot: {lock}")
    lock_sha = _sha256_file(lock)
    py312 = python_312 or _find_python_312()
    if py312 is None:
        raise ProvisioningError(
            "no existing Python 3.12 interpreter found for the Saleor .venv; "
            "refusing to silently download or switch Python"
        )
    py312_path = Path(py312)
    expected: dict[str, Any] = {
        "schema": MARKER_SCHEMA,
        "repo_id": "saleor",
        "source_tag": source_tag,
        "python_major_minor": [3, 12],
        "dependency_file": "uv.lock",
        "dependency_sha256": lock_sha,
    }

    def _probe(interp: Path) -> bool:
        return _saleor_probe(interp, log=log)

    reason = _needs_rebuild(work_dir, expected, probe=_probe)
    if reason is None:
        return _saleor_evidence(
            work_dir, lock_sha, source_tag, reused=True, require_services=require_services
        )
    if log is not None:
        log.emit(f"START provision_saleor (rebuild: {reason})")
    _remove_private_env(work_dir, log=log)
    if log is not None:
        log.emit(f"Copying exact frozen Saleor snapshot to {work_dir}")
    shutil.copytree(saleor_source, work_dir)
    uv_env = dict(os.environ)
    uv_env["UV_PYTHON_DOWNLOADS"] = "never"
    if log is not None:
        log.emit(f"Creating Saleor .venv with EXISTING Python {py312_path} (UV_PYTHON_DOWNLOADS=never)")
    run_command(
        [str(uv_bin), "venv", ".venv", "--python", str(py312_path)],
        cwd=work_dir,
        env=uv_env,
        log=log,
        label="uv venv .venv (existing 3.12)",
        timeout=600,
    )
    venv_py = work_dir / ".venv" / "bin" / "python"
    if not venv_py.is_file():
        raise ProvisioningError(f"Saleor .venv interpreter missing after uv venv: {venv_py}")
    if _python_version(venv_py, log=log) != (3, 12):
        raise ProvisioningError("Saleor .venv resolved to a non-3.12 interpreter; refusing to proceed")
    if log is not None:
        log.emit("Running uv sync --locked in the Saleor working copy")
    run_command(
        [str(uv_bin), "sync", "--locked"],
        cwd=work_dir,
        env=uv_env,
        log=log,
        label="uv sync --locked",
        timeout=2400,
        heartbeat=True,
    )
    if not _saleor_probe(venv_py, log=log):
        raise ProvisioningError("Saleor health probe failed after uv sync --locked (import saleor)")
    marker = dict(expected)
    _write_marker(work_dir, marker)
    if log is not None:
        log.emit(f"END provision_saleor: PASSED at {venv_py}")
    return _saleor_evidence(
        work_dir, lock_sha, source_tag, reused=False, require_services=require_services
    )


def _saleor_evidence(
    work_dir: Path,
    lock_sha: str,
    source_tag: str,
    *,
    reused: bool,
    require_services: bool,
) -> dict[str, Any]:
    venv_py = work_dir / ".venv" / "bin" / "python"
    services = _probe_services()
    if require_services:
        unreachable = sorted(
            name for name in _SALEOR_REQUIRED_SERVICES if not services[name]["reachable"]
        )
        if unreachable:
            raise ProvisioningError(
                "PostgreSQL/Redis services not reachable after Saleor provisioning: "
                + ", ".join(unreachable)
            )
    return {
        "repo_id": "saleor",
        "work": str(work_dir),
        "python": str(venv_py),
        "python_minor": [3, 12],
        "dependency_file": "uv.lock",
        "dependency_sha256": lock_sha,
        "source_tag": source_tag,
        "services": services,
        "reused": reused,
        "marker": str(work_dir / MARKER_NAME),
    }


def provision_repository_envs(
    host_python: str | Path,
    pilot_envs_root: str | Path,
    data_repositories_dir: str | Path,
    *,
    source_tag: str,
    log_path: str | Path | None = None,
    require_services: bool = True,
    ensure_os_packages: bool = True,
) -> dict[str, Any]:
    """Provision every repository validation environment and return evidence."""
    start = time.monotonic()
    pilot_envs_root = Path(pilot_envs_root)
    data_repositories_dir = Path(data_repositories_dir)
    log = ProvisioningLog(log_path)
    try:
        log.emit("=== PILOT REPOSITORY ENVIRONMENT PROVISIONING ===")
        log.emit(f"host python: {host_python}")
        log.emit(f"source tag:  {source_tag}")
        pilot_envs_root.mkdir(parents=True, exist_ok=True)
        if ensure_os_packages:
            ensure_os_prerequisites(log=log)
        uv_evidence = provision_uv_tool(
            host_python, pilot_envs_root / "tools", source_tag=source_tag, log=log
        )
        djangocms_evidence = provision_djangocms(
            host_python,
            pilot_envs_root / "djangocms",
            data_repositories_dir / "djangocms",
            uv_bin=Path(uv_evidence["bin"]),
            source_tag=source_tag,
            log=log,
        )
        saleor_evidence = provision_saleor(
            pilot_envs_root / "saleor",
            data_repositories_dir / "saleor",
            uv_bin=Path(uv_evidence["bin"]),
            source_tag=source_tag,
            require_services=require_services,
            log=log,
        )
        repositories = {
            "djangocms": djangocms_evidence,
            "saleor": saleor_evidence,
        }
        evidence: dict[str, Any] = {
            "schema": "pilot_repo_environment_provisioning.v1",
            "source_tag": source_tag,
            "created_utc": datetime.now(UTC).isoformat(),
            "prerequisites": {"packages": sorted(REQUIRED_OS_PACKAGES)},
            "uv": uv_evidence,
            "repositories": repositories,
            "djangocms": djangocms_evidence,
            "saleor": saleor_evidence,
        }
        log.emit(
            f"=== PILOT REPOSITORY ENVIRONMENT PROVISIONING: PASSED "
            f"(elapsed={time.monotonic() - start:.1f}s) ==="
        )
        return evidence
    finally:
        log.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pilot_kaggle_repo_envs",
        description="Provision the isolated Pilot repository validation environments (no model call).",
    )
    parser.add_argument(
        "--host-python",
        default=sys.executable,
        help="Benchmark/model interpreter used only as the venv source and pip --python caller.",
    )
    parser.add_argument("--pilot-envs-root", type=Path, required=True)
    parser.add_argument("--data-repositories-dir", type=Path, required=True)
    parser.add_argument("--source-tag", required=True)
    parser.add_argument("--log-path", type=Path, default=None)
    parser.add_argument("--no-services", action="store_true", help="Skip the Saleor service probe.")
    parser.add_argument("--skip-os-prerequisites", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    evidence = provision_repository_envs(
        host_python=args.host_python,
        pilot_envs_root=args.pilot_envs_root,
        data_repositories_dir=args.data_repositories_dir,
        source_tag=args.source_tag,
        log_path=args.log_path,
        require_services=not args.no_services,
        ensure_os_packages=not args.skip_os_prerequisites,
    )
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
