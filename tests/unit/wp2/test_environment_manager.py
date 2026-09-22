"""WP-2 environment manager - unit tests (ZERO API, no git, no network).

Tests deterministic environment fingerprinting from synthetic file maps and
fingerprint-family grouping. No real dependency installation occurs here.
"""

from __future__ import annotations

import hashlib
import json

from benchmark.wp2.environment_manager import (
    EnvFingerprint,
    fingerprint_commit_from_files,
    fingerprint_family,
    parse_python_requirement,
)


def test_parse_python_requirement_pyproject() -> None:
    text = '[project]\nrequires-python = ">=3.12,<3.13"\n'
    assert parse_python_requirement({"pyproject.toml": text}) == ">=3.12,<3.13"


def test_parse_python_requirement_setup() -> None:
    text = 'python_requires=">=3.11,<3.12",\n'
    assert parse_python_requirement({"setup.py": text}) == ">=3.11,<3.12"


def test_parse_python_requirement_unknown() -> None:
    assert parse_python_requirement({}) == "UNKNOWN"


def test_fingerprint_dependency_files_hashed() -> None:
    files = {
        "requirements.txt": b"django==5.2\n",
        "pyproject.toml": b'[project]\nrequires-python = ">=3.12,<3.13"\n',
    }
    fp = fingerprint_commit_from_files(files)
    assert fp.dependency_files["requirements.txt"] == hashlib.sha256(b"django==5.2\n").hexdigest()
    assert fp.dependency_files["pyproject.toml"] == hashlib.sha256(
        b'[project]\nrequires-python = ">=3.12,<3.13"\n'
    ).hexdigest()
    assert fp.python_requirement == ">=3.12,<3.13"


def test_fingerprint_django_present() -> None:
    files = {"pyproject.toml": b'[project]\ndependencies = ["django~=5.2.13"]\n'}
    fp = fingerprint_commit_from_files(files)
    assert fp.django_version_constraint is not None


def test_fingerprint_family_groups_identical() -> None:
    files = {"pyproject.toml": b'[project]\nrequires-python = ">=3.12,<3.13"\n'}
    fp = fingerprint_commit_from_files(files)
    assert fingerprint_family(fp) == fingerprint_family(fp)


def test_fingerprint_family_distinguishes_python() -> None:
    a = fingerprint_commit_from_files({"pyproject.toml": b'[project]\nrequires-python = ">=3.12,<3.13"\n'})
    b = fingerprint_commit_from_files({"pyproject.toml": b'[project]\nrequires-python = ">=3.11,<3.12"\n'})
    assert fingerprint_family(a) != fingerprint_family(b)


def test_env_fingerprint_json_roundtrip() -> None:
    fp = fingerprint_commit_from_files({"pyproject.toml": b'[project]\nrequires-python = ">=3.12,<3.13"\n'})
    as_dict = fp.to_dict()
    clone = EnvFingerprint(**as_dict)
    assert clone.python_requirement == fp.python_requirement
    assert clone.dependency_files == fp.dependency_files


def test_fingerprint_deterministic_json() -> None:
    files = {"pyproject.toml": b'[project]\nrequires-python = ">=3.12,<3.13"\n', "setup.cfg": b"[tool:pytest]\n"}
    a = fingerprint_commit_from_files(files)
    b = fingerprint_commit_from_files(files)
    assert json.dumps(a.to_dict(), sort_keys=True) == json.dumps(b.to_dict(), sort_keys=True)