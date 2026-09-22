"""WP-2 environment manager - isolated, version-aware (ZERO API).

Deterministic environment fingerprinting for candidate tasks (parent and
target commits) and fingerprint-family grouping. Actual dependency
installation is performed by scripts/wp2_oracle_confirm.py only inside
isolated venvs under ..\\_workspace\\wp2_oracle_confirmation\\envs\\.

This module performs no model/API calls and never touches the 786 sealed
Saleor RESERVE outcomes.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

FAMILY_SALT = "wp2-env-family-2026-09-22"

REQUIREMENT_FILES = (
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements.txt",
    "requirements.in",
    "Pipfile",
    "Pipfile.lock",
    "poetry.lock",
)


def parse_python_requirement(files: dict[str, str]) -> str:
    """Return the Python requirement string from pyproject/setup metadata."""
    pyproject = files.get("pyproject.toml", "")
    m = re.search(r'requires-python\s*=\s*["\']([^"\']+)["\']', pyproject)
    if m:
        return m.group(1)
    setup = files.get("setup.py", "")
    m = re.search(r'python_requires\s*=\s*["\']([^"\']+)["\']', setup)
    if m:
        return m.group(1)
    return "UNKNOWN"


def _django_constraint(files: dict[str, str]) -> str | None:
    text = "\n".join(
        files.get(name, "") for name in ("pyproject.toml", "setup.py", "setup.cfg", "requirements.txt")
    )
    m = re.search(r"django\s*[~<>=!]*\s*([0-9][0-9a-zA-Z.\-]*)", text, re.IGNORECASE)
    return m.group(0) if m else None


def _package_manager_markers(files: dict[str, str]) -> list[str]:
    markers: list[str] = []
    if "pyproject.toml" in files:
        markers.append("pyproject")
    if "poetry.lock" in files:
        markers.append("poetry")
    if "Pipfile" in files or "Pipfile.lock" in files:
        markers.append("pipenv")
    if "requirements.txt" in files:
        markers.append("pip-requirements")
    return sorted(markers)


def _db_cache_settings(files: dict[str, str]) -> dict:
    # Static detection only from settings.py if provided; otherwise empty.
    settings = files.get("saleor/settings.py", "")
    result = {"postgres": "postgres://" in settings or "postgres" in settings.lower()}
    result["redis"] = "redis" in settings.lower()
    return result


@dataclass
class EnvFingerprint:
    python_requirement: str
    dependency_files: dict[str, str] = field(default_factory=dict)
    package_manager_markers: list[str] = field(default_factory=list)
    django_version_constraint: str | None = None
    db_cache: dict = field(default_factory=dict)
    has_dockerfile: bool = False
    commit: str | None = None
    commit_date: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    def family(self) -> str:
        payload = {
            "python_requirement": self.python_requirement,
            "dependency_files": sorted(self.dependency_files.items()),
            "package_manager_markers": self.package_manager_markers,
            "django_version_constraint": self.django_version_constraint,
        }
        blob = hashlib.sha256(json_dumps(payload).encode("utf-8")).hexdigest()
        return f"{FAMILY_SALT}::{blob}"


def json_dumps(obj) -> str:
    import json

    return json.dumps(obj, sort_keys=True, ensure_ascii=False)


def _as_text(value: str | bytes) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value


def fingerprint_commit_from_files(files: dict[str, str | bytes]) -> EnvFingerprint:
    """Build a deterministic EnvFingerprint from a mapping of relpath->text.

    For dependency/requirement files the SHA-256 of the content is stored
    (not the text), so the fingerprint is stable and compact.
    """
    dep_hashes: dict[str, str] = {}
    for name in REQUIREMENT_FILES:
        value = files.get(name)
        if value is not None:
            dep_hashes[name] = hashlib.sha256(_as_text(value).encode("utf-8")).hexdigest()
    return EnvFingerprint(
        python_requirement=parse_python_requirement({k: _as_text(v) for k, v in files.items()}),
        dependency_files=dep_hashes,
        package_manager_markers=_package_manager_markers({k: _as_text(v) for k, v in files.items()}),
        django_version_constraint=_django_constraint({k: _as_text(v) for k, v in files.items()}),
        db_cache=_db_cache_settings({k: _as_text(v) for k, v in files.items()}),
        has_dockerfile="Dockerfile" in files,
    )


def fingerprint_family(fp: EnvFingerprint) -> str:
    return fp.family()


def short_family(fp: EnvFingerprint, n: int = 12) -> str:
    """Short, filesystem-safe family key (first n hex chars of the hash)."""
    return fp.family().split("::")[-1][:n]


def build_venv(env_root: Path, family: str, worktree: Path, python: Path) -> Path:
    """Build an isolated venv for a fingerprint family using uv.

    Uses ``uv venv`` + ``uv pip install -e <worktree>`` so the commit-era
    dependencies are installed exactly. Tests for other tasks in the same
    family reuse this venv by running pytest from their own worktree cwd
    (cwd takes import precedence for the ``saleor`` package). Raises
    RuntimeError if the build fails.
    """
    import shutil
    import subprocess

    venv_dir = env_root / family
    if (venv_dir / "Scripts" / "python.exe").exists():
        return venv_dir
    venv_dir.mkdir(parents=True, exist_ok=True)
    try:
        r = subprocess.run(
            ["uv", "venv", "--python", str(python), str(venv_dir)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=300,
            check=False,
        )
        if r.returncode != 0:
            raise RuntimeError(f"uv venv failed: {r.stderr[-800:]}")
        py = venv_dir / "Scripts" / "python.exe"
        r = subprocess.run(
            ["uv", "pip", "install", "--python", str(py), "-e", str(worktree)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=1800,
            check=False,
        )
        if r.returncode != 0:
            raise RuntimeError(f"uv pip install -e failed: {r.stderr[-1500:]}")
        for pkg in ("pytest", "pytest-django", "pytest-socket", "pytest-xdist"):
            r = subprocess.run(
                ["uv", "pip", "install", "--python", str(py), pkg],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=600,
                check=False,
            )
            if r.returncode != 0:
                raise RuntimeError(f"uv pip install {pkg} failed: {r.stderr[-500:]}")
    except subprocess.TimeoutExpired as exc:
        shutil.rmtree(venv_dir, ignore_errors=True)
        raise RuntimeError(f"venv build timed out for family {family}") from exc
    except Exception:
        shutil.rmtree(venv_dir, ignore_errors=True)
        raise
    return venv_dir
