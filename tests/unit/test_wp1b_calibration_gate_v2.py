"""WP-1b gate v2 tests — CG-10 instrument-validity gate.

Gate v2 (D3) adds two checks on top of CG-1..CG-9:
  CG-10  0 instrument-class tool errors across the whole calibration run
  CG-11  at least one task has >= 1 successful read_file (else STOP_FOR_REVIEW)

The existing Calibration-3 records are the RED evidence: the agent was blind
(0 successful reads, 9× `Max distinct files limit (30) reached` errors), so
gate v2 MUST FAIL (CG-10 FAIL) on them. Calibration-3b is the GREEN evidence.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

CAL3_DIR = PROJECT_DIR / "research" / "wp1b" / "calibration-3-2026-09-21"
GATE_V2 = PROJECT_DIR / "artifacts" / "wp1b_calibration_gate_v2.json"
CAL3_SIDECAR = CAL3_DIR / "wp1b_call_sidecar.jsonl"

_INPUT_FILES = (
    "calibration_run_records.jsonl",
    "wp1b_telemetry.jsonl",
    "wp1b_call_sidecar.jsonl",
    "pricing_preflight.json",
)


def _copy_cal3_inputs(tmp_path: Path) -> Path:
    cal_dir = tmp_path / "cal3"
    cal_dir.mkdir(parents=True, exist_ok=True)
    for name in _INPUT_FILES:
        src = CAL3_DIR / name
        if src.is_file():
            shutil.copy2(src, cal_dir / name)
    return cal_dir


def _run_gate_v2(cal_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PROJECT_DIR / "scripts" / "wp1b_calibration_gate.py"),
         "--gate", "v2", str(cal_dir)],
        cwd=PROJECT_DIR, capture_output=True, text=True, timeout=120,
    )


def test_gate_v2_definition_frozen() -> None:
    gate = json.loads(GATE_V2.read_text(encoding="utf-8"))
    assert gate["status"] == "FROZEN_BEFORE_INFERENCE"
    ids = [c["id"] for c in gate["checks"]]
    assert ids == [f"CG-{i}" for i in range(1, 12)]
    cg10 = next(c for c in gate["checks"] if c["id"] == "CG-10")
    assert "instrument" in cg10["condition"].lower()
    cg11 = next(c for c in gate["checks"] if c["id"] == "CG-11")
    assert "read_file" in cg11["condition"]


def test_gate_v2_cal3_sidecar_classification(tmp_path: Path) -> None:
    """The old Calibration-3 records must classify to 9 instrument errors and
    0 successful reads (the audit-derived counts, checked via the gate)."""
    from scripts.wp1b_sidecar_tool_audit import classify_record, error_class

    records = []
    for line in CAL3_SIDECAR.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    instrument_errors = 0
    successful_reads = 0
    for rec in records:
        cls = classify_record(rec)
        if cls.startswith("tool_error:"):
            msg = cls.split(":", 1)[1]
            if error_class(msg) == "INSTRUMENT_ERROR":
                instrument_errors += 1
        if rec.get("action") == "read_file" and cls == "tool_ok":
            successful_reads += 1
    assert instrument_errors == 9
    assert successful_reads == 0


def test_gate_v2_fails_on_old_calibration_3(tmp_path: Path) -> None:
    """RED evidence: gate v2 on the existing Calibration-3 records => CG-10 FAIL."""
    cal_dir = _copy_cal3_inputs(tmp_path)
    result = _run_gate_v2(cal_dir)
    assert result.returncode == 1, result.stdout + result.stderr
    out = json.loads(
        (cal_dir / "wp1b_calibration_gate_v2_result.json").read_text(encoding="utf-8")
    )
    assert out["gate_status"] == "FAIL"
    cg10 = next(c for c in out["checks"] if c["id"] == "CG-10")
    assert cg10["pass"] is False
    cg11 = next(c for c in out["checks"] if c["id"] == "CG-11")
    assert cg11["pass"] is False
