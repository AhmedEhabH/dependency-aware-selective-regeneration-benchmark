"""RealCommitImpactDataset-v1 record models.

M4A-1: deterministic, versioned schema for real historical djangoCMS commit
records. ZERO scientific LLM/API calls. The observed change-set proxy is an
OBSERVED CHANGE-SET PROXY — never semantic P/R/V/H ground truth.
"""

from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

SCHEMA_VERSION: str = "real-commit-impact-dataset-v1"
MINER_VERSION: str = "real-commit-miner-v1.0.0"

REPOSITORY_URL_DJANGOCMS: str = "https://github.com/django-cms/django-cms"
LICENSE_MANIFEST_REF: str = (
    "BSD-3-Clause; benchmark_data/manifests/repositories.yaml#djangocms"
)
DJANGOCMS_ANCHOR_COMMIT: str = "0f633fc9fa213357f4202482aab2b0edad680f95"

DEFAULT_TOTAL_DIFF_CEILING: int = 40
DEFAULT_PROXY_MIN: int = 1
DEFAULT_PROXY_MAX: int = 12


class SplitRole(StrEnum):
    MINER_DEV = "MINER_DEV"
    TRAIN = "TRAIN"
    VALIDATION = "VALIDATION"
    HELD_OUT_TEST = "HELD_OUT_TEST"


class EligibilityDecision(StrEnum):
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"


# Section 9 exclusion reason codes (frozen for v1; M4A-2 adds miner_dev_target).
EXCLUSION_REASON_CODES: tuple[str, ...] = (
    "merge_commit",
    "no_meaningful_intent",
    "no_production_source_change",
    "tests_only",
    "migrations_only",
    "generated_or_vendor_only",
    "whitespace_only",
    "production_add_delete_rename_copy_v1_unsupported",
    "proxy_not_subset_of_parent_universe",
    "proxy_too_large",
    "diff_too_large",
    "intent_path_leakage",
    "duplicate_or_related_change",
    "miner_dev_target",
)

# Conservative change taxonomy (intent-derived, NOT diff-derived semantic gold).
CHANGE_TYPE_VOCAB: tuple[str, ...] = (
    "bugfix",
    "feature",
    "refactor",
    "style",
    "docs",
    "build",
    "ci",
    "test",
    "chore",
    "release",
    "unknown",
)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(payload: Any) -> str:
    """Deterministic canonical JSON serialization (sort_keys, compact separators)."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_json(payload: Any) -> str:
    return sha256_hex(canonical_json(payload).encode("utf-8"))


def sha256_text(text: str) -> str:
    return sha256_hex(text.encode("utf-8"))


class CaseManifest(BaseModel):
    """Persisted per-case manifest (schema + record + artifact paths)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = SCHEMA_VERSION
    miner_version: str = MINER_VERSION
    record: dict[str, Any]
    public_artifact_paths: dict[str, str] = Field(default_factory=dict)
    hidden_artifact_paths: dict[str, str] = Field(default_factory=dict)
    canonical_record_sha256: str = ""

    @model_validator(mode="after")
    def _require_canonical_hash(self) -> CaseManifest:
        if not self.canonical_record_sha256:
            raise ValueError("canonical_record_sha256 must be set")
        return self


class DatasetManifest(BaseModel):
    """Dataset-level manifest for benchmark_data/real_commit_impact_v1."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = SCHEMA_VERSION
    miner_version: str = MINER_VERSION
    dataset_version: str = "v1"
    repository: str = "djangocms"
    repository_url: str = REPOSITORY_URL_DJANGOCMS
    anchor_commit: str = DJANGOCMS_ANCHOR_COMMIT
    created_utc: str
    case_ids: list[str] = Field(default_factory=list)
    cases: list[dict[str, Any]] = Field(default_factory=list)
    canonical_manifest_sha256: str = ""


def compute_canonical_record_hash(record: dict[str, Any]) -> str:
    """Canonical record hash ignoring only declared timestamp-only metadata.

    Excludes ``created_utc`` and the self-referential ``canonical_record_sha256``.
    """
    payload = {
        key: value for key, value in record.items()
        if key not in {"created_utc", "canonical_record_sha256"}
    }
    return sha256_json(payload)


def compute_canonical_dataset_manifest_hash(manifest: dict[str, Any]) -> str:
    payload = {
        key: value for key, value in manifest.items()
        if key != "canonical_manifest_sha256"
    }
    return sha256_json(payload)
