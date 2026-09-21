"""WP-1b Calibration-3 sidecar tool-audit tests (AC-T1).

The mechanical audit script scripts/wp1b_sidecar_tool_audit.py must reproduce
the Calibration-3 tool-call counts exactly from the raw sidecar:
  3 forced final answers / 5 tool calls returning data (3 list_files +
  2 search_text) / 9 tool errors from the 30-file limit (7 search_text +
  2 read_file) / 7 rejected repeated requests / 0 successful read_file.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from scripts.wp1b_sidecar_tool_audit import (  # noqa: E402
    ERROR_CATALOG,
    audit_sidecar,
    classify_record,
    error_class,
)

CAL3_DIR = PROJECT_DIR / "research" / "wp1b" / "calibration-3-2026-09-21"


def _load_cal3_sidecar() -> list[dict]:
    records = []
    for line in (CAL3_DIR / "wp1b_call_sidecar.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def test_audit_reproduces_345947_counts() -> None:
    records = _load_cal3_sidecar()
    audit = audit_sidecar(records)
    agg = audit["aggregate"]
    assert agg["calls"] == 24
    assert agg["final"] == 3
    assert agg["tool_ok"] == 5
    assert agg["tool_error"] == 9
    assert agg["rejected_repeat"] == 7
    assert agg["successful_reads"] == 0


def test_audit_per_task_counts() -> None:
    records = _load_cal3_sidecar()
    audit = audit_sidecar(records)
    by_task = {t["task_id"]: t for t in audit["per_task"]}
    assert by_task["saleor-rc-349d46d906ad"]["successful_reads"] == 0
    assert by_task["saleor-rc-b05633dae118"]["successful_reads"] == 0
    assert by_task["saleor-rc-d52a55471bfc"]["successful_reads"] == 0
    # 7 search_text errors + 2 read_file errors = 9, all the limit message.
    err_msgs: dict[str, int] = {}
    for rec in records:
        cls = classify_record(rec)
        if cls.startswith("tool_error:"):
            msg = cls.split(":", 1)[1]
            err_msgs[msg] = err_msgs.get(msg, 0) + 1
    assert err_msgs == {"Max distinct files limit (30) reached": 9}


def test_error_classification_vocabulary() -> None:
    assert error_class("Max distinct files limit (30) reached") == "INSTRUMENT_ERROR"
    assert error_class("Cannot read file") == "INSTRUMENT_ERROR"
    assert error_class("Skipped path") == "INSTRUMENT_ERROR"
    assert error_class("Invalid path") == "AGENT_MISUSE"
    assert error_class("Not a file") == "AGENT_MISUSE"
    assert error_class("Not a directory") == "AGENT_MISUSE"
    assert error_class("Not a file or directory") == "AGENT_MISUSE"
    assert error_class("Empty query") == "AGENT_MISUSE"
    assert error_class("File too large") == "FROZEN_POLICY_LIMIT"
    assert error_class("Binary file") == "FROZEN_POLICY_LIMIT"
    # Unknown/legacy errors stay fail-closed instrument.
    assert error_class("Some unexpected error") == "INSTRUMENT_ERROR"


def test_error_catalog_contains_expected_keys() -> None:
    assert "Max distinct files limit (30) reached" in ERROR_CATALOG
    assert set(ERROR_CATALOG.values()) <= {"INSTRUMENT_ERROR", "AGENT_MISUSE", "FROZEN_POLICY_LIMIT"}
