"""Unit tests for RealCommitImpactDataset-v1 record models (M4A-1, ZERO API)."""

from __future__ import annotations

import pytest

from benchmark.real_commits.models import (
    EXCLUSION_REASON_CODES,
    SCHEMA_VERSION,
    SplitRole,
    compute_canonical_dataset_manifest_hash,
    compute_canonical_record_hash,
    sha256_json,
    sha256_text,
)


def test_split_role_values() -> None:
    assert SplitRole.MINER_DEV.value == "MINER_DEV"
    assert SplitRole.TRAIN.value == "TRAIN"
    assert SplitRole.VALIDATION.value == "VALIDATION"
    assert SplitRole.HELD_OUT_TEST.value == "HELD_OUT_TEST"
    assert len(SplitRole) == 4


def test_exclusion_reason_codes_complete() -> None:
    required = {
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
    }
    assert required <= set(EXCLUSION_REASON_CODES)


def test_canonical_record_hash_ignores_only_declared_timestamp() -> None:
    record: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "case_id": "c1",
        "created_utc": "2026-09-13T00:00:00+00:00",
        "value": 1,
    }
    h1 = compute_canonical_record_hash(record)
    # Different timestamp, same content -> same hash.
    record2 = dict(record)
    record2["created_utc"] = "2026-09-14T00:00:00+00:00"
    assert compute_canonical_record_hash(record2) == h1
    # Content change -> different hash.
    record3 = dict(record)
    record3["value"] = 2
    assert compute_canonical_record_hash(record3) != h1


def test_canonical_record_hash_deterministic_and_self_excluded() -> None:
    record: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "case_id": "c2",
        "created_utc": "2026-09-13T00:00:00+00:00",
        "canonical_record_sha256": "IGNORE-ME",
    }
    h = compute_canonical_record_hash(record)
    record["canonical_record_sha256"] = "DIFFERENT-VALUE"
    assert compute_canonical_record_hash(record) == h
    assert h != "IGNORE-ME"


def test_dataset_manifest_hash_deterministic() -> None:
    m1: dict[str, object] = {"schema_version": SCHEMA_VERSION, "case_ids": ["a", "b"]}
    m2: dict[str, object] = {"schema_version": SCHEMA_VERSION, "case_ids": ["a", "b"]}
    assert compute_canonical_dataset_manifest_hash(m1) == compute_canonical_dataset_manifest_hash(m2)
    m3: dict[str, object] = {"schema_version": SCHEMA_VERSION, "case_ids": ["a", "c"]}
    assert compute_canonical_dataset_manifest_hash(m1) != compute_canonical_dataset_manifest_hash(m3)


def test_sha256_helpers() -> None:
    assert sha256_text("abc") == sha256_text("abc")
    assert sha256_text("abc") != sha256_text("abd")
    assert sha256_json({"b": 1, "a": 2}) == sha256_json({"a": 2, "b": 1})


def test_malformed_sha_rejected() -> None:
    import subprocess
    import tempfile

    from benchmark.real_commits.miner import verify_commit_sha

    with tempfile.TemporaryDirectory() as tmp:
        cache = __import__("pathlib").Path(tmp)
        cache.mkdir(exist_ok=True)
        subprocess.run(["git", "-C", str(cache), "init", "-q", "-b", "main"], check=True)
        # Fail-closed: malformed / nonexistent SHAs must raise (ValueError on
        # mismatch, RuntimeError when git cannot resolve the object at all).
        with pytest.raises((ValueError, RuntimeError)):
            verify_commit_sha(cache, "not-a-valid-sha" * 3)
        with pytest.raises((ValueError, RuntimeError)):
            verify_commit_sha(cache, "0" * 40)
