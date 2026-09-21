"""WP-1b Calibration-3 gate tests (frozen-before-inference + evaluator).

Protects Architecture Compliance (gate must be frozen before calibration) and
the Impact Correctness validity dimension (instrumentation sanity).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

ARTIFACTS = PROJECT_DIR / "artifacts"
GATE = ARTIFACTS / "wp1b_calibration_gate.json"


def _run_gate(cal_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PROJECT_DIR / "scripts" / "wp1b_calibration_gate.py"), str(cal_dir)],
        cwd=PROJECT_DIR, capture_output=True, text=True, timeout=120,
    )


def _write_synthetic_calibration(cal_dir: Path, *, silent_parser: bool = False,
                                 accounting_corrupt: bool = False) -> None:
    cal_dir.mkdir(parents=True, exist_ok=True)
    records = []
    telemetry = []
    for i in range(3):
        tid = f"cal-{i}"
        total = 100 + i * 10
        prompt = 70 + i * 5
        completion = total - prompt
        if accounting_corrupt and i == 0:
            completion = total - prompt + 5  # breaks identity
        records.append({
            "task_id": tid,
            "model": "qwen/qwen3-coder",
            "route": "openrouter:qwen/qwen3-coder@deepinfra/turbo",
            "temperature": 0.0,
            "agent_control_max_completion_tokens": 512,
            "max_agent_calls": 8,
            "token_usage": {"prompt_tokens": prompt, "completion_tokens": completion,
                            "total_tokens": total, "usd_cost": 0.0001},
        })
        malformed = 1 if (silent_parser and i == 0) else 0
        empty_reason = (
            "round_cap" if (silent_parser and i == 0)  # silent: misclassified
            else "parser_failure" if malformed else "none"
        )
        telemetry.append({
            "task_id": tid,
            "model_calls": 8,
            "control_truncation_count": 0,
            "cap_hit_count": 0,
            "malformed_count": malformed,
            "schema_invalid_count": 0,
            "valid_final_count": 1 if empty_reason == "none" else 0,
            "finish_reason_distribution": {"stop": 8},
            "empty_reason": empty_reason,
            "prediction_empty": empty_reason != "none",
            "final_answer_truncated": False,
        })
    (cal_dir / "calibration_run_records.jsonl").write_text(
        "\n".join(json.dumps(r) for r in records), encoding="utf-8")
    (cal_dir / "wp1b_telemetry.jsonl").write_text(
        "\n".join(json.dumps(t) for t in telemetry), encoding="utf-8")
    pricing = {
        "checks": {"no_drift": True},
        "frozen_calibration_ceiling_usd": 0.10,
    }
    (cal_dir / "pricing_preflight.json").write_text(json.dumps(pricing), encoding="utf-8")


def test_gate_is_frozen_before_inference() -> None:
    gate = json.loads(GATE.read_text(encoding="utf-8"))
    assert gate["status"] == "FROZEN_BEFORE_INFERENCE"
    ids = [c["id"] for c in gate["checks"]]
    assert ids == [f"CG-{i}" for i in range(1, 10)]
    assert "No F1-based calibration continuation rule is frozen" in gate["performance_rule"]


def test_gate_pass_on_clean_synthetic_calibration(tmp_path: Path) -> None:
    cal_dir = tmp_path / "cal_pass"
    _write_synthetic_calibration(cal_dir)
    result = _run_gate(cal_dir)
    assert result.returncode == 0, result.stdout + result.stderr
    out = json.loads((ARTIFACTS / "wp1b_calibration_gate_result.json").read_text(encoding="utf-8"))
    assert out["gate_status"] == "PASS"
    assert all(c["pass"] for c in out["checks"])


def test_gate_fails_on_silent_parser_failure(tmp_path: Path) -> None:
    cal_dir = tmp_path / "cal_silent_parser"
    _write_synthetic_calibration(cal_dir, silent_parser=True)
    result = _run_gate(cal_dir)
    assert result.returncode == 1
    out = json.loads((ARTIFACTS / "wp1b_calibration_gate_result.json").read_text(encoding="utf-8"))
    assert out["gate_status"] == "FAIL"
    cg4 = next(c for c in out["checks"] if c["id"] == "CG-4")
    assert cg4["pass"] is False


def test_gate_fails_on_corrupted_accounting(tmp_path: Path) -> None:
    cal_dir = tmp_path / "cal_corrupt"
    _write_synthetic_calibration(cal_dir, accounting_corrupt=True)
    result = _run_gate(cal_dir)
    assert result.returncode == 1
    out = json.loads((ARTIFACTS / "wp1b_calibration_gate_result.json").read_text(encoding="utf-8"))
    assert out["gate_status"] == "FAIL"
    cg8 = next(c for c in out["checks"] if c["id"] == "CG-8")
    assert cg8["pass"] is False


def test_gate_definition_only_when_no_dir() -> None:
    result = subprocess.run(
        [sys.executable, str(PROJECT_DIR / "scripts" / "wp1b_calibration_gate.py")],
        cwd=PROJECT_DIR, capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0
    assert "FROZEN (not evaluated)" in result.stdout
