"""WP-2 era environment resolver (amendment D) - one controlled base image per
Python/environment era (ZERO API).

For each task the era is derived from the commit's Python requirement and
lockfile SHA. The resolver:
- picks ONE controlled base image per era (immutable tag + digest);
- supplies the fixed system-library superset for the era;
- pins the installer (pip / uv) version for the era;
- uses the commit's own lockfile/dependency metadata (never current HEAD deps);
- fails closed on unknown eras (NO silent fallback to a newer/global env);
- forces offline test execution after environment construction.

Commit Dockerfiles are NOT executed as the experimental platform; they may only
be inspected as evidence for required apt/system packages.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json

ERA_SALT = "wp2-era-resolver-v1-2026-09-23"


@dataclasses.dataclass(frozen=True)
class EraSpec:
    era_key: str
    python_requirement: str
    base_image: str
    image_digest: str
    python_version: str
    installer_version: str
    pip_version: str
    system_packages: tuple[str, ...]
    lockfile_sha256: str | None = None

    def to_dict(self) -> dict:
        return {
            "era_key": self.era_key,
            "python_requirement": self.python_requirement,
            "base_image": self.base_image,
            "image_digest": self.image_digest,
            "python_version": self.python_version,
            "installer_version": self.installer_version,
            "pip_version": self.pip_version,
            "system_packages": list(self.system_packages),
            "lockfile_sha256": self.lockfile_sha256,
        }


# Era table keyed by canonical python requirement. Immutable digests recorded at
# B0 preflight (2026-09-23) from the WSL-local Docker Engine pulls.
ERA_TABLE: dict[str, EraSpec] = {
    "~3.8": EraSpec(
        era_key="py38",
        python_requirement="~3.8",
        base_image="python:3.8-slim",
        image_digest="sha256:1d52838af602b4b5a831beb13a0e4d073280665ea7be7f69ce2382f29c5a613f",
        python_version="3.8",
        installer_version="uv-0.11.32",
        pip_version="pip-21.3.1",
        system_packages=(
            "build-essential",
            "libpq-dev",
            "libffi-dev",
            "libjpeg-dev",
            "libxml2-dev",
            "gettext",
            "zlib1g-dev",
            "libssl-dev",
            "libmagic1",
            "libmagic-mgc",
            "file",
            "libcairo2",
            "libglib2.0-0",
            "libpango-1.0-0",
            "libpangocairo-1.0-0",
            "libgdk-pixbuf-2.0-0",
        ),
    ),
    "~3.9": EraSpec(
        era_key="py39",
        python_requirement="~3.9",
        base_image="python:3.9-slim",
        image_digest="sha256:2d97f6910b16bd338d3060f261f53f144965f755599aab1acda1e13cf1731b1b",
        python_version="3.9",
        installer_version="uv-0.11.32",
        pip_version="pip-22.0.4",
        system_packages=(
            "build-essential",
            "libpq-dev",
            "libffi-dev",
            "libjpeg-dev",
            "libxml2-dev",
            "gettext",
            "zlib1g-dev",
            "libssl-dev",
            "libmagic1",
            "libmagic-mgc",
            "file",
            "libcairo2",
            "libglib2.0-0",
            "libpango-1.0-0",
            "libpangocairo-1.0-0",
            "libgdk-pixbuf-2.0-0",
        ),
    ),
    "~3.12": EraSpec(
        era_key="py312",
        python_requirement="~3.12",
        base_image="python:3.12-slim",
        image_digest="sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9",
        python_version="3.12",
        installer_version="uv-0.11.32",
        pip_version="pip-23.2.1",
        system_packages=(
            "build-essential",
            "libpq-dev",
            "libffi-dev",
            "libjpeg-dev",
            "libxml2-dev",
            "gettext",
            "zlib1g-dev",
            "libssl-dev",
            "libmagic1",
            "libmagic-mgc",
            "file",
            "libcairo2",
            "libglib2.0-0",
            "libpango-1.0-0",
            "libpangocairo-1.0-0",
            "libgdk-pixbuf-2.0-0",
        ),
    ),
    ">=3.12,<3.13": EraSpec(
        era_key="py312",
        python_requirement=">=3.12,<3.13",
        base_image="python:3.12-slim",
        image_digest="sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9",
        python_version="3.12",
        installer_version="uv-0.11.32",
        pip_version="pip-23.2.1",
        system_packages=(
            "build-essential",
            "libpq-dev",
            "libffi-dev",
            "libjpeg-dev",
            "libxml2-dev",
            "gettext",
            "zlib1g-dev",
            "libssl-dev",
            "libmagic1",
            "libmagic-mgc",
            "file",
            "libcairo2",
            "libglib2.0-0",
            "libpango-1.0-0",
            "libpangocairo-1.0-0",
            "libgdk-pixbuf-2.0-0",
        ),
    ),
}

DEFAULT_LOCKFILE_SHA256 = "none-lockfile"


def era_for_python_requirement(python_requirement: str) -> EraSpec:
    """Resolve an era spec from a commit's Python requirement.

    Raises KeyError on an unknown requirement (no silent fallback)."""
    spec = ERA_TABLE.get(python_requirement)
    if spec is None:
        raise KeyError(
            f"no era for python requirement {python_requirement!r}; "
            "refusing silent fallback (amendment D)"
        )
    return spec


def resolve_era(
    *,
    python_requirement: str,
    lockfile_sha256: str | None = DEFAULT_LOCKFILE_SHA256,
    digests: dict[str, str] | None = None,
) -> dict:
    """Deterministic era resolution with optional digest overlay.

    ``digests`` maps era_key -> immutable image digest recorded at preflight
    freeze time (C1). Returns a dict of the era spec with the digest overlay
    applied and an era fingerprint.
    """
    spec = era_for_python_requirement(python_requirement)
    digest = spec.image_digest
    if digests and spec.era_key in digests:
        digest = digests[spec.era_key]
    payload = {
        **spec.to_dict(),
        "image_digest": digest,
        "lockfile_sha256": lockfile_sha256,
    }
    payload["era_fingerprint_sha256"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return payload


def inspect_commit_dockerfile(dockerfile_text: str) -> list[str]:
    """Extract apt/system package names from a commit Dockerfile (evidence only).

    Returns a sorted, de-duplicated list of tokens that look like apt package
    names on ``RUN apt-get install ...`` lines. This is inspection-only; the
    commit Dockerfile is never executed as the experimental platform.
    """
    import re

    packages: set[str] = set()
    for line in dockerfile_text.splitlines():
        if "apt-get install" not in line.lower():
            continue
        for tok in re.findall(r"[a-zA-Z0-9][a-zA-Z0-9+.\-]*", line):
            low = tok.lower()
            if low in ("install", "y", "q", "apt-get", "no-install-recommends", "rm"):
                continue
            packages.add(tok)
    return sorted(packages)


# ---------------------------------------------------------------------------
# Controlled era base images (one Dockerfile per era, NOT per commit)
# ---------------------------------------------------------------------------
def era_dockerfile_text(era_key: str) -> str:
    """One controlled era base-image Dockerfile (amendment D).

    The era base is built once from the pinned immutable base image with the
    fixed system-library superset and pinned installer versions. Task images
    layer commit lockfile/dependency metadata on top of this base; the
    repository's own production Dockerfiles are never used as the platform.
    """
    spec = ERA_TABLE.get(era_key) or next(
        (s for s in ERA_TABLE.values() if s.era_key == era_key), None
    )
    if spec is None:
        raise KeyError(f"no era spec for era_key {era_key!r}")
    packages = " ".join(spec.system_packages)
    return (
        f"# Controlled {spec.era_key} era base image (frozen 2026-09-23)\n"
        f"FROM {spec.base_image}@{spec.image_digest}\n"
        f"ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1\n"
        f"RUN apt-get update && apt-get install -y --no-install-recommends "
        f"{packages} \\\n"
        f"    && rm -rf /var/lib/apt/lists/*\n"
        f"# pinned installer version per era (amendment D)\n"
        f"RUN pip install --no-cache-dir 'uv==0.11.32' 'pip=={spec.pip_version.removeprefix('pip-')}'\n"
        f"LABEL wp2.era={spec.era_key} wp2.era_digest={spec.image_digest}\n"
    )


def task_image_dockerfile_text(era_key: str, requirements_text: str | None) -> str:
    """Task image Dockerfile: era base + commit lockfile/dependency metadata.

    ``requirements_text`` is the commit's own lockfile/requirements content
    (never current HEAD dependencies). Raises if no lockfile is available
    (NO silent dependency fallback, amendment D).
    """
    if not requirements_text or not requirements_text.strip():
        raise ValueError(
            "no commit lockfile/dependency metadata available; refusing "
            "silent dependency fallback (amendment D)"
        )
    return (
        f"FROM wp2-era-{era_key}:latest\n"
        f"WORKDIR /app\n"
        f"COPY requirements.txt /tmp/requirements.txt\n"
        f"RUN uv pip install --system -r /tmp/requirements.txt\n"
    )
