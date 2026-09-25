"""WP-2 Oracle harness provenance schema V2 (ZERO API).

Implements ``oracle_harness_schema_v2`` (Mission 07 §4) with the amendment-D
requirement that no required provenance field may be ``None``.

Every per-task / per-test V2 record MUST contain the mandatory fields below;
conditional fields (database/service identities) are required whenever the run
uses that service. Validation fails closed.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json

ORACLE_HARNESS_SCHEMA_VERSION = "oracle_harness_schema_v2"
SCHEMA_SALT = "wp2-oracle-harness-schema-v2-2026-09-23"

MANDATORY_FIELDS = (
    "harness_version",
    "harness_commit_sha",
    "classifier_bundle_sha256",
    "os_distro",
    "container_image_tag",
    "container_image_digest",
    "python_executable",
    "python_version",
    "installer_version",
    "lockfile_sha256",
    "dependency_pip_freeze_hash",
    "environment_fingerprint",
    "parent_commit",
    "target_commit",
    "timestamp",
    "test_command",
    "junit_sha256",
    "output_sha256",
    "test_patch_rule_sha256",
)

CONDITIONAL_FIELDS = (
    "postgres_version",
    "postgres_image_digest",
    "redis_version",
    "redis_image_digest",
)

ALL_FIELDS = MANDATORY_FIELDS + CONDITIONAL_FIELDS


@dataclasses.dataclass(frozen=True)
class ProvenanceRecord:
    harness_version: str
    harness_commit_sha: str
    classifier_bundle_sha256: str
    os_distro: str
    container_image_tag: str
    container_image_digest: str
    python_executable: str
    python_version: str
    installer_version: str
    lockfile_sha256: str
    dependency_pip_freeze_hash: str
    environment_fingerprint: str
    parent_commit: str
    target_commit: str
    timestamp: str
    test_command: str
    junit_sha256: str
    output_sha256: str
    test_patch_rule_sha256: str
    postgres_version: str | None = None
    postgres_image_digest: str | None = None
    redis_version: str | None = None
    redis_image_digest: str | None = None

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


def validate_provenance(record: dict) -> list[str]:
    """Return a list of missing/None required fields ([] == valid).

    Mandatory fields must be present and non-None/non-empty. Conditional fields
    must be non-None/non-empty whenever the run reports using that service: a
    version without a digest (or digest without version) is a violation.
    """
    problems: list[str] = []
    for field in MANDATORY_FIELDS:
        value = record.get(field)
        if value is None or (isinstance(value, str) and value == ""):
            problems.append(field)
    for v_field, d_field in (
        ("postgres_version", "postgres_image_digest"),
        ("redis_version", "redis_image_digest"),
    ):
        v = record.get(v_field)
        d = record.get(d_field)
        if v is None and d is None:
            continue  # service not used
        if v is None or d is None:
            problems.append(f"{v_field}/{d_field} must both be present")
    return problems


def provenance_fingerprint(record: dict) -> str:
    """Deterministic SHA-256 over the normalized provenance record."""
    payload = json.dumps(record, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def make_provenance_record(record: dict) -> dict:
    """Build a validated provenance record dict.

    Raises ValueError listing all missing mandatory fields so no provenance
    field is ever silently ``None`` (amendment D).
    """
    problems = validate_provenance(record)
    if problems:
        raise ValueError(
            "incomplete provenance record; missing/None fields: "
            + ", ".join(problems)
        )
    out = {k: record[k] for k in ALL_FIELDS if k in record}
    out["schema"] = ORACLE_HARNESS_SCHEMA_VERSION
    out["provenance_sha256"] = provenance_fingerprint(
        {k: out[k] for k in ALL_FIELDS if k in out}
    )
    return out
