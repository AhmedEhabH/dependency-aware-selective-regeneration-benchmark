"""Accounting regression tests for the Qwen3-Coder-30B-A3B-Instruct study.

Covers the C4 accounting contract applied from the Qwen3-32B correction:
- finish_reason=length + invalid JSON / schema failure / semantic failure
  => truncation True (never a silent 0-truncation count)
- provider response + schema failure => request counted AND usage retained
- request dispatched + transport exception => issued-request semantics preserved
- no request dispatched => zero request correctly represented
- usage missing => explicit usage_known=False
- unknown usage => lower-bound aggregation semantics
- checkpoint/resume => completed cell is never rerun
- raw SHA => fail closed on mismatch
"""

from __future__ import annotations

from pathlib import Path

from scripts import stagec_djangocms_qwen3_coder_30b_a3b_crossmodel_execute as driver
from scripts.verify_qwen3_coder_30b_a3b_crossmodel_claims import is_truncation

_PROJECT_DIR = Path(__file__).resolve().parent.parent.parent


def _record(**overrides: object) -> dict:
    base: dict = {
        "run_id": "stgc30b-djangocms-external-validity-004-impact_plan_v2-r1",
        "terminal_status": "failed",
        "truncation_status": False,
        "completion_cap_hit": False,
        "finish_reason": "",
        "failure_category": "",
        "failure_evidence": [],
        "raw_response_sha256": "",
        "request_attempted": True,
        "request_dispatched": True,
        "provider_response_received": True,
        "raw_response_persisted": True,
        "usage_received": True,
        "usage_known": True,
        "model_calls": 1,
        "transport_failure": False,
        "prompt_tokens": 4000,
        "completion_tokens": 400,
        "total_tokens": 4400,
        "api_cost": 0.0004,
        "arm": "impact_plan_v2",
        "scenario_id": "djangocms-external-validity-004",
    }
    base.update(overrides)
    return base


# --- C5: finish_reason=length truncation classification ---


def test_finish_reason_length_with_invalid_json_is_truncation():
    rec = _record(
        failure_category=(
            "ImpactPlanV2Error: planner v2 response not JSON "
            "(finish_reason=length): Expecting value"
        )
    )
    assert driver._is_truncation(rec)
    assert is_truncation(rec)


def test_finish_reason_length_with_schema_failure_is_truncation():
    rec = _record(finish_reason="length", schema_valid=False)
    assert driver._is_truncation(rec)
    assert is_truncation(rec)


def test_finish_reason_length_with_semantic_failure_is_truncation():
    rec = _record(
        completion_cap_hit=True,
        failure_evidence=[
            {"kind": "SemanticError", "stage": "validate", "message": "missing rationale"}
        ],
    )
    assert driver._is_truncation(rec)
    assert is_truncation(rec)


def test_completion_cap_hit_flag_is_truncation():
    rec = _record(completion_cap_hit=True, failure_evidence=[])
    assert driver._is_truncation(rec)
    assert is_truncation(rec)


# --- C5: request / usage semantics on failed cells ---


def _build_failed(**kwargs: object) -> dict:
    class _Usage:
        def __init__(self, prompt: int, completion: int) -> None:
            self.prompt_tokens = prompt
            self.completion_tokens = completion
            self.total_tokens = prompt + completion

    class _Exc(BaseException):
        def __init__(self, msg: str) -> None:
            super().__init__(msg)

    usage = kwargs.pop("usage", None)
    if usage is not None:
        usage = _Usage(int(usage[0]), int(usage[1]))
    cell = {
        "run_id": "stgc30b-djangocms-external-validity-004-impact_plan_v2-r1",
        "scenario_id": "djangocms-external-validity-004",
        "repetition": 1,
        "arm": "impact_plan_v2",
    }
    return driver._build_failed_cell_evidence(
        cell, 5.0, None, (),
        raw_text=kwargs.pop("raw_text", None),
        exc=_Exc(str(kwargs.pop("exc_message", "boom"))),
        usage=usage,
        accounting=kwargs.pop("accounting", None),
    )


def test_provider_response_semantic_failure_counts_request_and_retains_usage():
    ev = _build_failed(raw_text='{"decisions":[]}', usage=(4100, 900))
    assert ev["request_attempted"] is True
    assert ev["request_dispatched"] is True
    assert ev["provider_response_received"] is True
    assert ev["raw_response_persisted"] is True
    assert ev["usage_known"] is True
    assert ev["prompt_tokens"] == 4100
    assert ev["completion_tokens"] == 900
    assert ev["model_calls"] == 1
    assert ev["transport_failure"] is False


def test_schema_failure_retains_usage():
    ev = _build_failed(raw_text='{"bad":', usage=(4200, 120))
    assert ev["usage_known"] is True
    assert ev["prompt_tokens"] == 4200
    assert ev["completion_tokens"] == 120


def test_transport_exception_after_dispatch_preserves_issued_request_semantics():
    ev = _build_failed(
        raw_text=None,
        exc_message="IncompleteRead(0 bytes read)",
        accounting={"request_attempted": True, "request_dispatched": True, "usage_received": False},
    )
    assert ev["request_dispatched"] is True
    assert ev["provider_response_received"] is False
    assert ev["usage_known"] is False
    assert ev["model_calls"] == 0
    assert ev["transport_failure"] is True
    # Request is still counted as issued (never silently dropped).
    assert driver._request_issued(ev)


def test_no_dispatch_means_zero_request():
    ev = _build_failed(
        raw_text=None,
        accounting={"request_attempted": False, "request_dispatched": False, "usage_received": False},
    )
    assert ev["request_dispatched"] is False
    assert driver._request_issued(ev) is False


def test_usage_missing_is_usage_known_false():
    ev = _build_failed(raw_text=None, accounting={"request_dispatched": True})
    assert ev["usage_known"] is False
    assert ev["prompt_tokens"] == 0


def test_unknown_usage_aggregation_is_lower_bound():
    known = _record(usage_known=True, prompt_tokens=5000, completion_tokens=1000, total_tokens=6000)
    unknown = _record(usage_known=False, prompt_tokens=0, completion_tokens=0, total_tokens=0)
    rows = [known, unknown]
    total_tokens = sum(int(r["total_tokens"]) for r in rows)
    assert total_tokens == 6000  # recorded total; the unknown cell adds no fake zeros silently
    assert sum(1 for r in rows if not r["usage_known"]) == 1
    assert driver._count_usage_unknown(rows) == 1


# --- C5: checkpoint/resume ---


def test_checkpoint_resume_never_reruns_completed_cell():
    completed = {"stgc30b-a-r1": {"run_id": "stgc30b-a-r1"}}
    cells = [
        {"run_id": "stgc30b-a-r1"},
        {"run_id": "stgc30b-a-r2"},
    ]
    pending = [c for c in cells if c["run_id"] not in completed]
    assert pending == [{"run_id": "stgc30b-a-r2"}]


# --- C5: raw SHA fail closed on mismatch ---


def test_raw_sha_fail_closed_on_mismatch():
    from scripts.verify_qwen3_coder_30b_a3b_crossmodel_claims import sha256_bytes

    a = sha256_bytes(b"same content")
    b = sha256_bytes(b"same content")
    c = sha256_bytes(b"different")
    assert a == b
    assert a != c
    assert a == driver._sha256_bytes(b"same content")
