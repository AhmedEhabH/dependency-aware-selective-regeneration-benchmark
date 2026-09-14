"""Unit tests for the P1 serialized-record metric correction (ZERO API).

These tests prove the corrected metric definition: the serialized decision
count comes from the model's raw `decisions` payload, NOT from
`decoded_write_set_ids` (which counts only REGENERATE rows — the predicted
write-set size).

- Full-v2 must serialize exactly one decision per candidate.
- Sparse-v2 serializes only explicit non-PRESERVE decisions (may include
  VALIDATE / HUMAN_REVIEW rows that a REGENERATE-only count would drop).
"""

from __future__ import annotations

import json

import pytest

from benchmark.real_commits import p1_evaluation as p1


def _provider_envelope(content: str) -> str:
    return json.dumps(
        {
            "id": "gen-test",
            "choices": [
                {"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": content}}
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        }
    )


def test_full_v2_serialized_count_equals_candidate_count() -> None:
    candidate_count = 140
    decisions = [
        {"id": i, "action": "PRESERVE", "rationale": "no change", "confidence": 1.0,
         "reason_codes": ["no_change"], "evidence": []}
        for i in range(1, candidate_count + 1)
    ]
    decisions[0]["action"] = "REGENERATE"
    decisions[1]["action"] = "VALIDATE"
    payload = {"decisions": decisions}
    raw = _provider_envelope(json.dumps(payload))

    count, errors = p1.serialized_decision_count_from_raw(raw)
    assert errors == []
    assert count == candidate_count

    vres = p1.validate_p1_full(payload, candidate_count=candidate_count)
    assert vres["valid"]
    assert vres["decoded_candidate_count"] == candidate_count
    assert count == candidate_count
    assert len(vres["decoded_write_set_ids"]) == 1  # only the REGENERATE row


def test_sparse_serialized_count_derives_from_raw_decisions_not_write_set() -> None:
    candidate_count = 140
    decisions = [
        {"id": 3, "action": "REGENERATE", "rationale": "edit", "confidence": 1.0,
         "reason_codes": ["requirement_change"], "evidence": []},
        {"id": 17, "action": "VALIDATE", "rationale": "check boundary", "confidence": 0.8,
         "reason_codes": ["architecture"], "evidence": []},
        {"id": 42, "action": "HUMAN_REVIEW", "rationale": "unsafe", "confidence": 0.5,
         "reason_codes": ["scope_unsafe"], "evidence": []},
        {"id": 99, "action": "REGENERATE", "rationale": "edit", "confidence": 1.0,
         "reason_codes": ["requirement_change"], "evidence": []},
    ]
    payload = {"decisions": decisions}
    raw = _provider_envelope(json.dumps(payload))

    count, errors = p1.serialized_decision_count_from_raw(raw)
    assert errors == []
    assert count == 4  # REGENERATE(2) + VALIDATE(1) + HUMAN_REVIEW(1)

    vres = p1.validate_p1_sparse(payload, candidate_count=candidate_count)
    assert vres["valid"]
    assert len(vres["decoded_write_set_ids"]) == 2  # REGENERATE rows only
    assert count != len(vres["decoded_write_set_ids"])  # the core defect proof


def test_sparse_no_explicit_preserve_and_non_preserve_count() -> None:
    decisions = [
        {"id": 5, "action": "REGENERATE", "rationale": "edit", "confidence": 1.0,
         "reason_codes": ["requirement_change"], "evidence": []},
        {"id": 7, "action": "VALIDATE", "rationale": "check", "confidence": 0.9,
         "reason_codes": ["architecture"], "evidence": []},
    ]
    raw = _provider_envelope(json.dumps({"decisions": decisions}))

    count, errors = p1.serialized_decision_count_from_raw(raw)
    assert errors == []
    assert count == 2

    items = p1.raw_decision_items(raw)
    assert all(str(d.get("action") or "").upper() != "PRESERVE" for d in items)
    non_preserve = [d for d in items if str(d.get("action") or "").upper() != "PRESERVE"]
    assert count == len(non_preserve)


def test_serialized_count_malformed_raw_fails_closed() -> None:
    assert p1.serialized_decision_count_from_raw("not json")[0] == 0
    assert p1.serialized_decision_count_from_raw("{}")[0] == 0
    assert p1.serialized_decision_count_from_raw('{"choices": []}')[0] == 0
    assert p1.serialized_decision_count_from_raw(
        _provider_envelope("not json")
    )[0] == 0
    assert p1.serialized_decision_count_from_raw(
        _provider_envelope(json.dumps({"nope": []}))
    )[0] == 0


def test_p1_full_roundtrip_write_set_is_regenerate_only() -> None:
    mapping = p1.build_p1_candidate_map(["cms/a.py", "cms/b.py", "cms/c.py"])
    proxy = {"cms/a.py"}
    payload = p1.fixture_payload_for_arm(arm="full_v2", mapping=mapping, proxy_paths=proxy)
    vres = p1.validate_p1_full(payload, candidate_count=3)
    assert vres["valid"]
    assert vres["decoded_candidate_count"] == 3
    assert len(payload["decisions"]) == 3  # serialized = candidate count
    assert vres["decoded_write_set_ids"] == [1]  # REGENERATE only


def test_p1_sparse_roundtrip_serialized_is_explicit_non_preserve() -> None:
    mapping = p1.build_p1_candidate_map(["cms/a.py", "cms/b.py", "cms/c.py"])
    proxy = {"cms/a.py", "cms/c.py"}
    payload = p1.fixture_payload_for_arm(arm="sparse_v2", mapping=mapping, proxy_paths=proxy)
    vres = p1.validate_p1_sparse(payload, candidate_count=3)
    assert vres["valid"]
    assert len(payload["decisions"]) == 2  # only the two REGENERATE rows
    assert vres["decoded_write_set_ids"] == [1, 3]
    assert all(
        str(d.get("action") or "").upper() != "PRESERVE" for d in payload["decisions"]
    )


def test_serialized_decision_count_persisted_alongside_predicted_write_set() -> None:
    """The runner's per-cell evidence must carry both fields distinctly."""
    candidate_count = 140
    decisions = [
        {"id": i, "action": "PRESERVE", "rationale": "no change", "confidence": 1.0,
         "reason_codes": ["no_change"], "evidence": []}
        for i in range(1, candidate_count + 1)
    ]
    decisions[0]["action"] = "REGENERATE"
    payload = {"decisions": decisions}
    raw = _provider_envelope(json.dumps(payload))

    count, _ = p1.serialized_decision_count_from_raw(raw)
    vres = p1.validate_p1_full(payload, candidate_count=candidate_count)
    predicted_write_set_size = len(vres["decoded_write_set_ids"])

    assert count == candidate_count
    assert predicted_write_set_size == 1
    assert count != predicted_write_set_size


@pytest.mark.parametrize(
    ("arm", "actions"),
    [
        ("full_v2", ["PRESERVE", "REGENERATE", "VALIDATE", "HUMAN_REVIEW"]),
        ("sparse_v2", ["REGENERATE", "VALIDATE", "HUMAN_REVIEW"]),
    ],
)
def test_serialized_count_counts_all_actions(arm: str, actions: list[str]) -> None:
    candidate_count = len(actions)
    decisions = [
        {"id": i + 1, "action": a, "rationale": "x", "confidence": 0.9,
         "reason_codes": ["no_change"], "evidence": []}
        for i, a in enumerate(actions)
    ]
    raw = _provider_envelope(json.dumps({"decisions": decisions}))
    count, errors = p1.serialized_decision_count_from_raw(raw)
    assert errors == []
    assert count == candidate_count
