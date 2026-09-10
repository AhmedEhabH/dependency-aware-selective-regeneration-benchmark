"""Focused tests for the paper-claim verifier (V7 evidence hardening).

Covers the three requested verifier behaviors without building a new testing
framework:

1. aggregation correctness (arm_stats recomputation)
2. missing-evidence fail-closed (load_jsonl / load_json)
3. hash-mismatch fail-closed (verify_raw_hashes)
"""

from __future__ import annotations

import hashlib

import scripts.verify_paper_claims as vpc

VALID_RECORDS = [
    {
        "arm": "impact_plan_v2",
        "terminal_status": "succeeded",
        "truncation_status": False,
        "tp": 1,
        "fp": 2,
        "fn": 0,
        "full_recall": True,
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "total_tokens": 150,
        "model_calls": 1,
        "api_cost": 0.01,
        "scenario_id": "scenario-001",
        "repetition": 1,
    },
    {
        "arm": "impact_plan_v2",
        "terminal_status": "succeeded",
        "truncation_status": False,
        "tp": 0,
        "fp": 1,
        "fn": 1,
        "full_recall": False,
        "prompt_tokens": 200,
        "completion_tokens": 60,
        "total_tokens": 260,
        "model_calls": 1,
        "api_cost": 0.02,
        "scenario_id": "scenario-001",
        "repetition": 2,
    },
    {
        "arm": "impact_plan_v2",
        "terminal_status": "failed",
        "truncation_status": True,
        "tp": 0,
        "fp": 0,
        "fn": 0,
        "full_recall": False,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "model_calls": 0,
        "api_cost": 0.0,
        "scenario_id": "scenario-001",
        "repetition": 3,
    },
]


def test_arm_stats_aggregation_correctness() -> None:
    stats = vpc.arm_stats(VALID_RECORDS, "impact_plan_v2")
    assert stats["recorded"] == 3
    assert stats["valid"] == 2
    assert stats["failed"] == 1
    assert stats["truncations"] == 1
    assert stats["tp"] == 1
    assert stats["fp"] == 3
    assert stats["fn"] == 1
    assert stats["prompt_tokens"] == 300
    assert stats["completion_tokens"] == 110
    assert stats["total_tokens"] == 410
    assert abs(stats["precision"] - (1 / 4)) < 1e-9
    assert abs(stats["recall"] - (1 / 2)) < 1e-9
    assert stats["full_recall_count"] == 1


def test_missing_evidence_fails_closed(tmp_path) -> None:
    v = vpc.Verifier()
    missing = v.load_jsonl(tmp_path / "nope.jsonl")
    assert missing == []
    assert v.failures, "missing run records must register a failure"

    v2 = vpc.Verifier()
    assert v2.load_json(tmp_path / "nope.json") is None
    assert v2.failures, "missing json artifact must register a failure"


def test_hash_mismatch_fails_closed(tmp_path) -> None:
    raw = tmp_path / "runs" / "raw"
    raw.mkdir(parents=True)
    payload = b'{"decisions": []}'
    (raw / "run-a.txt").write_bytes(payload)
    (raw / "run-a.sha256").write_text(hashlib.sha256(payload).hexdigest())

    (raw / "run-b.txt").write_bytes(payload)
    (raw / "run-b.sha256").write_text("0" * 64)

    records = [
        {"run_id": "run-a", "raw_response_sha256": hashlib.sha256(payload).hexdigest()},
        {"run_id": "run-b", "raw_response_sha256": "0" * 64},
    ]
    mismatches = vpc.verify_raw_hashes(tmp_path, records)
    assert len(mismatches) == 1
    assert "run-b" in mismatches[0]


def test_verifier_smoke_on_real_evidence() -> None:
    """The canonical verifier must exit 0 on the frozen repo evidence."""
    assert vpc.main() == 0
