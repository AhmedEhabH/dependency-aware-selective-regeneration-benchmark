"""WP-1a sample freeze tests (AC-1A.4) + intent parity tests (AC-1A.5)."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

RESEARCH = PROJECT_DIR / "research" / "saleor-reserve-300-rmcss"
WP1A = PROJECT_DIR / "research" / "wp1a"
SAMPLE_SHA = "445b5e9d0aeeab9551e8feeb3e59e6b5bcfee793f029810a6efe0cbc8f126447"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_main_50_is_first_50_of_frozen_ordering() -> None:
    sample = json.loads((RESEARCH / "saleor_reserve_300_sample.json").read_text(encoding="utf-8"))
    ids = sample["selected_ids"]
    main = json.loads((WP1A / "wp1_main_50_manifest.json").read_text(encoding="utf-8"))
    assert main["task_ids"] == ids[:50]
    assert main["n"] == 50
    assert len(set(main["task_ids"])) == 50


def test_calibration_3_deterministic_and_disjoint() -> None:
    import numpy as np
    sample = json.loads((RESEARCH / "saleor_reserve_300_sample.json").read_text(encoding="utf-8"))
    ids = sample["selected_ids"]
    main_50 = ids[:50]
    complement = sorted(set(ids) - set(main_50))
    rng = np.random.default_rng(20260921)
    expected = sorted(str(x) for x in rng.choice(
        np.asarray(complement, dtype=object), size=3, replace=False))
    cal = json.loads((WP1A / "wp1_calibration_3_manifest.json").read_text(encoding="utf-8"))
    assert cal["task_ids"] == expected
    assert len(set(cal["task_ids"])) == 3
    assert set(cal["task_ids"]).isdisjoint(set(main_50))


def test_sample_freeze_hash() -> None:
    sample = json.loads((RESEARCH / "saleor_reserve_300_sample.json").read_text(encoding="utf-8"))
    ids_text = "\n".join(sample["selected_ids"]) + "\n"
    assert _sha256_text(ids_text) == SAMPLE_SHA


def test_freeze_aggregate_disjointness() -> None:
    agg = json.loads((WP1A / "wp1_sample_freeze.json").read_text(encoding="utf-8"))
    assert agg["intersection_empty"] is True
    assert agg["intersection_size"] == 0
    assert agg["all_from_opened_300"] is True
    assert agg["786_reserve_outcomes_not_accessed"] is True


def test_intent_parity_pass() -> None:
    p = json.loads((WP1A / "wp1a_intent_parity.json").read_text(encoding="utf-8"))
    assert p["status"] == "WP1A_INTENT_PARITY_PASS"
    assert p["n_canonical_hash_match"] == 53
    assert not p["blocked"]


def test_intent_hash_recomputed() -> None:
    p = json.loads((WP1A / "wp1a_intent_parity.json").read_text(encoding="utf-8"))
    for cid, entry in p["per_task"].items():
        intent_path = (
            PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor"
            / "scientific" / cid / "public" / "intent.json"
        )
        intent = json.loads(intent_path.read_text(encoding="utf-8"))
        assert _sha256_text(intent["intent_text"]) == entry["intent_text_sha256"]
        assert entry["canonical_hash_match"] is True
        assert entry["intent_source"] == "commit_message"
