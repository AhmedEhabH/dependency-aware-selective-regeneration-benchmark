"""WP-2 provenance schema V2 - unit tests (ZERO API).

Verifies oracle_harness_schema_v2: mandatory non-None provenance fields
(amendment D / Mission 07 §4) and the conditional postgres/redis pairing rule.
"""

from __future__ import annotations

import pytest

from benchmark.wp2.provenance_schema_v2 import (
    MANDATORY_FIELDS,
    ORACLE_HARNESS_SCHEMA_VERSION,
    make_provenance_record,
    provenance_fingerprint,
    validate_provenance,
)


def _complete_record() -> dict:
    return {
        "harness_version": "wp2-linux-harness-v2",
        "harness_commit_sha": "a" * 40,
        "classifier_bundle_sha256": "b" * 64,
        "os_distro": "debian-12-slim",
        "container_image_tag": "python:3.12-slim",
        "container_image_digest": "c" * 64,
        "python_executable": "/usr/local/bin/python",
        "python_version": "3.12.4",
        "installer_version": "uv-0.11.32",
        "lockfile_sha256": "d" * 64,
        "dependency_pip_freeze_hash": "e" * 64,
        "environment_fingerprint": "fam::" + "f" * 64,
        "parent_commit": "g" * 40,
        "target_commit": "h" * 40,
        "timestamp": "2026-09-23T00:00:00Z",
        "test_command": "pytest -q --ds=saleor.tests.settings",
        "junit_sha256": "i" * 64,
        "output_sha256": "j" * 64,
        "test_patch_rule_sha256": "k" * 64,
    }


def test_complete_record_valid() -> None:
    assert validate_provenance(_complete_record()) == []


def test_missing_mandatory_field_detected() -> None:
    record = _complete_record()
    record["harness_commit_sha"] = None
    assert "harness_commit_sha" in validate_provenance(record)


def test_empty_string_field_detected() -> None:
    record = _complete_record()
    record["classifier_bundle_sha256"] = ""
    assert "classifier_bundle_sha256" in validate_provenance(record)


def test_make_record_raises_on_missing_field() -> None:
    record = _complete_record()
    record["target_commit"] = None
    with pytest.raises(ValueError, match="target_commit"):
        make_provenance_record(record)


def test_all_mandatory_fields_covered_by_validation() -> None:
    assert len(MANDATORY_FIELDS) == 19


def test_conditional_postgres_pairing() -> None:
    record = _complete_record()
    record["postgres_version"] = "15.4"
    record["postgres_image_digest"] = None
    problems = validate_provenance(record)
    assert any("postgres" in p for p in problems)


def test_conditional_postgres_pair_ok() -> None:
    record = _complete_record()
    record["postgres_version"] = "15.4"
    record["postgres_image_digest"] = "p" * 64
    assert validate_provenance(record) == []


def test_schema_version() -> None:
    assert ORACLE_HARNESS_SCHEMA_VERSION == "oracle_harness_schema_v2"


def test_provenance_fingerprint_deterministic() -> None:
    r1 = _complete_record()
    r2 = _complete_record()
    assert provenance_fingerprint(r1) == provenance_fingerprint(r2)
    r2["timestamp"] = "2026-09-23T00:00:01Z"
    assert provenance_fingerprint(r1) != provenance_fingerprint(r2)
