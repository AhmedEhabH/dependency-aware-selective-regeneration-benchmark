"""Unit tests for RealCommitImpactDataset-v1 provenance + MINER_DEV split (ZERO API)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from benchmark.real_commits.miner import (
    make_case_id,
    normalize_intent,
)
from benchmark.real_commits.models import (
    SCHEMA_VERSION,
    SplitRole,
    canonical_json,
    compute_canonical_record_hash,
)


def test_make_case_id_deterministic() -> None:
    target = "0f633fc9fa213357f4202482aab2b0edad680f95"
    assert make_case_id(target) == "djangocms-rc-0f633fc9fa21"
    assert make_case_id(target) == make_case_id(target)
    assert make_case_id(target) != make_case_id("a" * 40)


def test_canonical_json_sort_keys() -> None:
    assert canonical_json({"b": 1, "a": 2}) == canonical_json({"a": 2, "b": 1})


def test_record_hash_timestamp_only_excluded() -> None:
    base = {
        "schema_version": SCHEMA_VERSION,
        "case_id": "djangocms-rc-x",
        "parent_commit": "a" * 40,
        "target_commit": "b" * 40,
        "created_utc": "2026-09-13T10:00:00+00:00",
    }
    a = compute_canonical_record_hash(base)
    base2 = dict(base)
    base2["created_utc"] = "2026-09-14T10:00:00+00:00"
    assert compute_canonical_record_hash(base2) == a
    base3 = dict(base)
    base3["target_commit"] = "c" * 40
    assert compute_canonical_record_hash(base3) != a


def test_miner_dev_split_excluded_from_heldout() -> None:
    """MINER_DEV is a distinct value and NEVER equals HELD_OUT_TEST."""
    assert SplitRole.MINER_DEV != SplitRole.HELD_OUT_TEST
    assert SplitRole.MINER_DEV.value == "MINER_DEV"
    # A MINER_DEV record may never carry a HELD_OUT_TEST split.
    assert SplitRole.MINER_DEV not in (SplitRole.HELD_OUT_TEST,)


def test_malformed_schema_rejected(tmp_path: Path) -> None:
    """Malformed JSON / non-dict manifests must fail closed when reloaded."""
    from benchmark.real_commits.validation import load_case_manifest

    dataset = tmp_path / "dataset"
    case = dataset / "miner_dev" / "djangocms-rc-x"
    case.mkdir(parents=True)
    (case / "case_manifest.json").write_text("not json", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        load_case_manifest(dataset, "djangocms-rc-x")


def test_normalized_intent_deterministic() -> None:
    a = normalize_intent("  fix:  add page\nvalidation  ")
    b = normalize_intent("fix: add page validation")
    assert a == b == "fix: add page validation"
