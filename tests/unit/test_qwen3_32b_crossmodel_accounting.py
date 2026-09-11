"""Regression tests for the Qwen3-32B cross-model truncation classifier.

Accounting audit (2026-09-11): the ``truncation_status`` field was only set on
the success-path evidence builder, so failed Sparse-v2 cells truncated at the
frozen 4096 completion cap (``finish_reason=length``) were not counted as
truncations. These tests lock the corrected classifier in the cross-model
driver and its zero-API verifier.
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts import stagec_djangocms_qwen3_32b_crossmodel_execute as driver
from scripts.verify_qwen3_32b_crossmodel_claims import is_truncation

_PROJECT_DIR = Path(__file__).resolve().parent.parent.parent


def _record(**overrides: object) -> dict:
    base: dict = {
        "run_id": "x-r1",
        "terminal_status": "failed",
        "truncation_status": False,
        "finish_reason": "",
        "failure_category": "",
        "failure_evidence": [],
        "raw_response_sha256": "",
    }
    base.update(overrides)
    return base


def test_success_path_truncation_flag_counts():
    assert driver._is_truncation(_record(truncation_status=True))
    assert is_truncation(_record(truncation_status=True))


def test_finish_reason_length_field_counts():
    rec = _record(finish_reason="length")
    assert driver._is_truncation(rec)
    assert is_truncation(rec)


def test_failure_message_finish_reason_length_counts():
    rec = _record(
        failure_category=(
            "ImpactPlanV2Error: planner v2 response not JSON "
            "(finish_reason=length): Expecting value"
        )
    )
    assert driver._is_truncation(rec)
    assert is_truncation(rec)


def test_unterminated_raw_json_counts():
    study_dir = _PROJECT_DIR / "reports" / driver.STUDY_ID
    raw = study_dir / "runs" / "raw" / "stgc32b-djangocms-external-validity-004-impact_plan_v2-r1.txt"
    assert raw.is_file(), f"missing fixture raw: {raw}"
    rec = _record(
        run_id="stgc32b-djangocms-external-validity-004-impact_plan_v2-r1",
        failure_category="ImpactPlanV2Error: planner v2 response not JSON",
        raw_response_sha256="24cf3176d70d8fe1ff409854e22741ce31cc471f905643056b230e19d7c449e6",
    )
    assert driver._is_truncation(rec)
    assert is_truncation(rec)


def test_valid_json_invariant_failure_is_not_truncation():
    rec = _record(
        run_id="stgc32b-djangocms-external-validity-002-impact_plan_v2-r2",
        failure_category="ImpactPlanV2Error: conflicting decisions",
        raw_response_sha256="cb03da0615ee",
    )
    # No raw file match below would be false; here we simulate a valid-JSON raw.
    assert not driver._is_truncation(rec)
    assert not is_truncation(rec)


def test_real_records_truncation_counts():
    recs_path = (
        _PROJECT_DIR
        / "reports"
        / driver.STUDY_ID
        / "run_records.jsonl"
    )
    records = [
        json.loads(line)
        for line in recs_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    v1 = [r for r in records if r["arm"] == "impact_plan"]
    v2 = [r for r in records if r["arm"] == "impact_plan_v2"]
    assert sum(1 for r in v1 if driver._is_truncation(r)) == 24
    assert sum(1 for r in v2 if driver._is_truncation(r)) == 6
    assert sum(1 for r in records if driver._is_truncation(r)) == 30
    # the six corrected Sparse-v2 truncations are exactly the flagged cells
    flagged = {
        f"stgc32b-djangocms-external-validity-004-impact_plan_v2-r{i}" for i in range(1, 6)
    } | {"stgc32b-djangocms-external-validity-008-impact_plan_v2-r2"}
    v2_truncated = {r["run_id"] for r in v2 if driver._is_truncation(r)}
    assert v2_truncated == flagged


def test_model_calls_zero_cells_raw_persistence():
    recs_path = (
        _PROJECT_DIR
        / "reports"
        / driver.STUDY_ID
        / "run_records.jsonl"
    )
    records = [
        json.loads(line)
        for line in recs_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    zero_calls = [r for r in records if r.get("model_calls") == 0]
    assert len(zero_calls) == 8
    raw_dir = _PROJECT_DIR / "reports" / driver.STUDY_ID / "runs" / "raw"
    with_raw = [r for r in zero_calls if r.get("raw_response_sha256")]
    assert len(with_raw) == 7
    no_raw = [r for r in zero_calls if not r.get("raw_response_sha256")]
    assert len(no_raw) == 1
    assert no_raw[0]["run_id"] == "stgc32b-djangocms-external-validity-006-impact_plan-r3"
    for r in with_raw:
        assert (raw_dir / f"{r['run_id']}.txt").is_file()
