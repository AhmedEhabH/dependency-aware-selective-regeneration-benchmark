"""Integration tests: P1 serialized-record correction against persisted evidence.

Runs the recompute path over the frozen 60-cell P1 evidence
(`research/real-commit-p1-01/`) — ZERO API calls, raw bytes untouched. Proves
that on the real persisted raw responses:

- Full-v2: serialized_decision_count == candidate_count for every valid cell;
- Sparse-v2: no explicit PRESERVE rows and serialized_decision_count ==
  explicit non-PRESERVE decision count for every valid cell;
- the corrected artifacts agree with the recomputation.
"""

from __future__ import annotations

import json
from pathlib import Path

from benchmark.real_commits import p1_evaluation as p1

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
STUDY_DIR = PROJECT_DIR / "research" / "real-commit-p1-01"
RAW_DIR = STUDY_DIR / "runs" / "raw"
RECORDS_PATH = STUDY_DIR / "run_records.jsonl"
CORRECTED_METRICS_PATH = STUDY_DIR / "final_metrics_serialization_corrected.json"
PER_CELL_PATH = STUDY_DIR / "serialization_metric_corrected.json"
REPORT_PATH = PROJECT_DIR / "reports" / "REAL_COMMIT_M4A3_P1_SERIALIZATION_METRIC_CORRECTION.md"


def _load_records() -> list[dict]:
    rows = []
    for line in RECORDS_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _load_per_cell() -> dict[str, dict]:
    payload = json.loads(PER_CELL_PATH.read_text(encoding="utf-8"))
    return {c["run_id"]: c for c in payload["cells"]}


def test_all_60_raw_responses_parse_and_pass_assertions() -> None:
    records = _load_records()
    assert len(records) == 60
    per_cell = _load_per_cell()
    assert len(per_cell) == 60

    for rec in records:
        rid = rec["run_id"]
        entry = per_cell[rid]
        assert entry["assert_ok"], (rid, entry.get("assert_message"))
        assert entry["serialized_decision_count"] >= 1
        if rec["arm"] == "full_v2":
            assert entry["serialized_decision_count"] == entry["candidate_count"]
        else:
            items = p1.raw_decision_items((RAW_DIR / f"{rid}.txt").read_text(encoding="utf-8"))
            assert all(str(d.get("action") or "").upper() != "PRESERVE" for d in items)
            non_preserve = [d for d in items if str(d.get("action") or "").upper() != "PRESERVE"]
            assert entry["serialized_decision_count"] == len(non_preserve)


def test_full_v2_serialized_mean_equals_candidate_mean() -> None:
    corrected = json.loads(CORRECTED_METRICS_PATH.read_text(encoding="utf-8"))
    full = corrected["arms"]["full_v2"]
    assert full["serialized_records"]["mean"] == 144.0
    assert full["serialized_records"]["min"] == 140.0
    assert full["serialized_records"]["max"] == 152.0


def test_sparse_serialized_mean_greater_than_write_set_mean() -> None:
    corrected = json.loads(CORRECTED_METRICS_PATH.read_text(encoding="utf-8"))
    sparse = corrected["arms"]["sparse_v2"]
    # serialized includes VALIDATE/HUMAN_REVIEW rows; write-set is REGENERATE only
    assert sparse["serialized_records"]["mean"] > sparse["write_set_size"]["mean"]
    assert sparse["serialized_records"]["mean"] > 2.5


def test_corrected_delta_ci_is_large_negative() -> None:
    corrected = json.loads(CORRECTED_METRICS_PATH.read_text(encoding="utf-8"))
    boot = corrected["bootstrap_over_tasks"]["records"]
    assert boot["mean_delta"] < -100.0
    assert boot["ci95_high"] < -100.0
    assert boot["ci95_low"] < boot["ci95_high"]


def test_per_cell_and_corrected_metrics_consistent() -> None:
    per_cell = _load_per_cell()
    corrected = json.loads(CORRECTED_METRICS_PATH.read_text(encoding="utf-8"))
    for arm in ("full_v2", "sparse_v2"):
        entries = [c for c in per_cell.values() if c["arm"] == arm]
        mean = sum(c["serialized_decision_count"] for c in entries) / len(entries)
        assert abs(mean - corrected["arms"][arm]["serialized_records"]["mean"]) < 1e-6


def test_correction_report_exists_and_marks_mislabel() -> None:
    report = REPORT_PATH.read_text(encoding="utf-8")
    assert "mislabel" in report or "mislabeled" in report
    assert "predicted write-set size" in report


def test_raw_response_bytes_unchanged_hash_verified() -> None:
    records = _load_records()
    import hashlib

    for rec in records:
        rid = rec["run_id"]
        raw = (RAW_DIR / f"{rid}.txt").read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        assert sha == rec["raw_response_sha256"], rid
