#!/usr/bin/env python3
"""WP-1b Calibration-3 gate evaluator (mission section 23; ZERO API).

Reads the frozen gate definition (artifacts/wp1b_calibration_gate.json) and
evaluates each check against a calibration results directory. The gate is
frozen BEFORE inference; this script is the machine-checkable evaluation.

Expected calibration results directory layout (produced by the future
authorized WP-1b calibration run):
  calibration_run_records.jsonl   per-task run records (with protocol metadata
                                  and token_usage)
  wp1b_telemetry.jsonl            per-task telemetry records (schema:
                                  src/benchmark/wp1b/telemetry.py PER_TASK_FIELDS)
  pricing_preflight.json          the G6 pricing preflight artifact

Usage:
  python scripts/wp1b_calibration_gate.py <calibration_dir>
With no argument, prints the frozen gate definition only (exit 0).

Output: artifacts/wp1b_calibration_gate_result.json
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
GATE = _PROJECT_DIR / "artifacts" / "wp1b_calibration_gate.json"
RESULT_OUT = _PROJECT_DIR / "artifacts" / "wp1b_calibration_gate_result.json"

FROZEN_MODEL = "qwen/qwen3-coder"
FROZEN_TEMPERATURE = 0.0
FROZEN_MAX_AGENT_CALLS = 8
FROZEN_ROUTE_FRAGMENT = "deepinfra/turbo"
CAL_N = 3


def _load_records(cal_dir: Path) -> dict:
    records = []
    for line in (cal_dir / "calibration_run_records.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    telemetry = []
    tel_path = cal_dir / "wp1b_telemetry.jsonl"
    if tel_path.exists():
        for line in tel_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                telemetry.append(json.loads(line))
    pricing = json.loads((cal_dir / "pricing_preflight.json").read_text(encoding="utf-8"))
    return {"records": records, "telemetry": telemetry, "pricing": pricing}


def evaluate(cal_dir: Path) -> dict:
    data = _load_records(cal_dir)
    records = data["records"]
    telemetry = data["telemetry"]
    pricing = data["pricing"]

    n_records = len(records)
    results: list[dict] = []

    def _check(cid: str, ok: bool, detail: str) -> None:
        results.append({"id": cid, "pass": bool(ok), "detail": detail})

    required_protocol_fields = ("task_id", "model", "route", "temperature",
                                "agent_control_max_completion_tokens",
                                "max_agent_calls")
    complete = all(all(f in (r or {}) for f in required_protocol_fields) for r in records)

    _check("CG-1", n_records == CAL_N and complete,
           f"records={n_records}/{CAL_N} metadata_complete={complete}")

    protocol_ok = all(
        r.get("model") == FROZEN_MODEL
        and FROZEN_ROUTE_FRAGMENT in str(r.get("route", ""))
        and abs(float(r.get("temperature", -1)) - FROZEN_TEMPERATURE) < 1e-9
        and int(r.get("agent_control_max_completion_tokens", -1)) > 0
        and int(r.get("max_agent_calls", -1)) == FROZEN_MAX_AGENT_CALLS
        for r in records
    )
    _check("CG-2", protocol_ok, "all protocol metadata fields match frozen values")

    classified = all(
        t["valid_final_count"] > 0 or t["empty_reason"] in (
            "truncation", "round_cap", "parser_failure", "infrastructure")
        for t in telemetry
    )
    _check("CG-3", len(telemetry) == CAL_N and classified,
           f"telemetry={len(telemetry)}/{CAL_N} all_classified={classified}")

    silent_parser = any(t["malformed_count"] > 0 and t["empty_reason"] != "parser_failure"
                        for t in telemetry)
    _check("CG-4", not silent_parser,
           "silent_parser_failures=" + str(sum(
               1 for t in telemetry if t["malformed_count"] > 0 and t["empty_reason"] != "parser_failure")))

    unclassified = sum(1 for t in telemetry if t["empty_reason"] not in (
        "truncation", "round_cap", "parser_failure", "infrastructure", "none"))
    _check("CG-5", unclassified == 0, f"unclassified_EMPTY={unclassified}")

    no_drift = bool(pricing.get("checks", {}).get("no_drift"))
    record_route_ok = all(FROZEN_ROUTE_FRAGMENT in str(r.get("route", "")) for r in records)
    _check("CG-6", no_drift and record_route_ok,
           f"pricing_no_drift={no_drift} record_route_ok={record_route_ok}")

    knob_drift = any(
        abs(float(r.get("temperature", -1)) - FROZEN_TEMPERATURE) > 1e-9
        or int(r.get("max_agent_calls", -1)) != FROZEN_MAX_AGENT_CALLS
        for r in records
    )
    _check("CG-7", not knob_drift, "unexpected_knob_drift=" + str(knob_drift))

    accounting_ok = all(
        int(r.get("token_usage", {}).get("total_tokens", -1))
        == int(r.get("token_usage", {}).get("prompt_tokens", -1))
        + int(r.get("token_usage", {}).get("completion_tokens", -1))
        for r in records
    )
    _check("CG-8", accounting_ok, "accounting_identity_ok=" + str(accounting_ok))

    ceiling = pricing.get("frozen_calibration_ceiling_usd")
    if ceiling is not None:
        total = sum(float(r.get("token_usage", {}).get("usd_cost", 0.0)) for r in records)
        _check("CG-9", total <= float(ceiling), f"calibration_usd={total:.6f} ceiling={float(ceiling):.6f}")
    else:
        _check("CG-9", True, "ceiling not supplied by pricing preflight; no overrun assertion")

    all_pass = all(c["pass"] for c in results)
    result = {
        "artifact": "wp1b_calibration_gate_result",
        "evaluated_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "gate_status": "PASS" if all_pass else "FAIL",
        "checks": results,
        "note": "Calibration gate evaluated on a frozen check-set (artifacts/wp1b_calibration_gate.json). "
                "It is an instrumentation/protocol sanity gate; calibration F1 does not gate the main run.",
    }
    RESULT_OUT.write_text(json.dumps(result, indent=1), encoding="utf-8")
    for c in results:
        print(f"[gate] {c['id']}: {'PASS' if c['pass'] else 'FAIL'} - {c['detail']}")
    print(f"[gate] GATE: {result['gate_status']}")
    return result


def main() -> int:
    if len(sys.argv) < 2:
        gate = json.loads(GATE.read_text(encoding="utf-8"))
        print(f"[gate] FROZEN (not evaluated): {gate['artifact']} status={gate['status']}")
        print("[gate] provide a calibration results directory to evaluate.")
        return 0
    cal_dir = Path(sys.argv[1])
    if not cal_dir.is_dir():
        print(f"[gate] ERROR: calibration directory not found: {cal_dir}")
        return 1
    result = evaluate(cal_dir)
    return 0 if result["gate_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
