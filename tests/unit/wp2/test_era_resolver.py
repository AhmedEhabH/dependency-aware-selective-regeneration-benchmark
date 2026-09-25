"""WP-2 era environment resolver - unit tests (ZERO API).

Verifies amendment D: one controlled base image per era, deterministic
resolution, NO silent fallback on unknown eras, digest overlay, and
commit-Dockerfile inspection (evidence only).
"""

from __future__ import annotations

import pytest

from benchmark.wp2.era_resolver import (
    era_dockerfile_text,
    era_for_python_requirement,
    inspect_commit_dockerfile,
    resolve_era,
    task_image_dockerfile_text,
)


def test_resolve_era_deterministic() -> None:
    a = resolve_era(python_requirement=">=3.12,<3.13", lockfile_sha256="L" * 64)
    b = resolve_era(python_requirement=">=3.12,<3.13", lockfile_sha256="L" * 64)
    assert a == b
    assert a["era_key"] == "py312"
    assert a["python_version"] == "3.12"
    assert a["lockfile_sha256"] == "L" * 64


def test_unknown_era_no_silent_fallback() -> None:
    with pytest.raises(KeyError):
        era_for_python_requirement("~3.7")


def test_digest_overlay_at_freeze() -> None:
    r = resolve_era(
        python_requirement="~3.9",
        digests={"py39": "abc" * 21 + "ab"},
    )
    assert r["image_digest"].startswith("abc")


def test_era_fingerprint_changes_with_lockfile() -> None:
    r1 = resolve_era(python_requirement="~3.8", lockfile_sha256="a" * 64)
    r2 = resolve_era(python_requirement="~3.8", lockfile_sha256="b" * 64)
    assert r1["era_fingerprint_sha256"] != r2["era_fingerprint_sha256"]


def test_inspect_commit_dockerfile_extracts_system_packages() -> None:
    dockerfile = (
        "FROM python:3.8-slim\n"
        "RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev gettext\n"
        "RUN pip install -e .\n"
    )
    pkgs = inspect_commit_dockerfile(dockerfile)
    assert "build-essential" in pkgs
    assert "libpq-dev" in pkgs
    assert "gettext" in pkgs
    assert "pip" not in pkgs


def test_era_table_covers_observed_requirements() -> None:
    for req in ("~3.8", "~3.9", "~3.12", ">=3.12,<3.13"):
        spec = era_for_python_requirement(req)
        assert spec.base_image.endswith("-slim")


def test_era_digests_frozen_not_empty() -> None:
    for req in ("~3.8", "~3.9", "~3.12", ">=3.12,<3.13"):
        spec = era_for_python_requirement(req)
        assert spec.image_digest.startswith("sha256:")
        assert len(spec.image_digest) == 7 + 64


def test_era_dockerfile_one_per_era_deterministic() -> None:
    df = era_dockerfile_text("py312")
    assert "python:3.12-slim" in df
    assert "apt-get install" in df
    assert "uv==0.11.32" in df
    assert df == era_dockerfile_text("py312")


def test_era_dockerfile_pins_installer_and_digest() -> None:
    df = era_dockerfile_text("py38")
    assert "pip==21.3.1" in df
    assert "sha256:" in df


def test_task_image_requires_lockfile_no_fallback() -> None:
    with pytest.raises(ValueError, match="silent dependency fallback"):
        task_image_dockerfile_text("py312", None)
    with pytest.raises(ValueError, match="silent dependency fallback"):
        task_image_dockerfile_text("py312", "   \n  ")


def test_task_image_layers_era_base() -> None:
    df = task_image_dockerfile_text("py312", "django==4.2.1\n")
    assert "FROM wp2-era-py312:latest" in df
    assert "uv pip install" in df
