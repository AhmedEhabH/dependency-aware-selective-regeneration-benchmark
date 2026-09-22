#!/usr/bin/env python3
"""WP-1b Calibration gate evaluator (mission section 23; ZERO API).

Reads the frozen gate definition (artifacts/wp1b_calibration_gate.json for v1,
artifacts/wp1b_calibration_gate_v2.json for --gate v2, or
artifacts/wp1b_calibration_gate_v3.json for --gate v3) and evaluates each
check against a calibration results directory. The gate is frozen BEFORE
inference; this script is the machine-checkable evaluation.

Expected calibration results directory layout (produced by the authorized
WP-1b calibration run):
  calibration_run_records.jsonl   per-task run records (with protocol metadata
                                  and token_usage)
  wp1b_telemetry.jsonl            per-task telemetry records (schema:
                                  src/benchmark/wp1b/telemetry.py PER_TASK_FIELDS)
  wp1b_call_sidecar.jsonl         per-call sidecar records (gate v2 only)
  pricing_preflight.json          the G6 pricing preflight artifact

Usage:
  python scripts/wp1b_calibration_gate.py [--gate v2] <calibration_dir>
With no argument, prints the frozen gate definition only (exit 0).

Gate v2 adds CG-10 (0 instrument-class tool errors) and CG-11 (>= 1
successful read_file in >= 1 task). The per-call classification and the
INSTRUMENT_ERROR / AGENT_MISUSE / FROZEN_POLICY_LIMIT classes are shared with
scripts/wp1b_sidecar_tool_audit.py.

Result is written as <calibration_dir>/wp1b_calibration_gate_result.json
(v1) or <calibration_dir>/wp1b_calibration_gate_v2_result.json (--gate v2).
"""
from __future__ import annotations

import argparse
import datetime
import json
from pathlib import Path
from typing import Any

_PROJECT_DIR = Path(__file__).resolve().parent.parent
GATE = _PROJECT_DIR / "artifacts" / "wp1b_calibration_gate.json"
GATE_V2 = _PROJECT_DIR / "artifacts" / "wp1b_calibration_gate_v2.json"
GATE_V3 = _PROJECT_DIR / "artifacts" / "wp1b_calibration_gate_v3.json"

FROZEN_MODEL = "qwen/qwen3-coder"
FROZEN_TEMPERATURE = 0.0
FROZEN_MAX_AGENT_CALLS = 8
FROZEN_ROUTE_FRAGMENT = "deepinfra/turbo"
CAL_N = 3

BUDGET_MODEL_V2 = _PROJECT_DIR / "research" / "wp1b" / "wp1b_budget_model_v2.json"


def _load_records(cal_dir: Path, *, with_sidecar: bool = False) -> dict:
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
    data = {"records": records, "telemetry": telemetry, "pricing": pricing}
    if with_sidecar:
        sidecar = []
        sc_path = cal_dir / "wp1b_call_sidecar.jsonl"
        if sc_path.is_file():
            for line in sc_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    sidecar.append(json.loads(line))
        data["sidecar"] = sidecar
    return data


def _check(results: list[dict], cid: str, ok: bool, detail: str) -> None:
    results.append({"id": cid, "pass": bool(ok), "detail": detail})


def _run_cg1_9(results: list[dict], data: dict) -> None:
    records = data["records"]
    telemetry = data["telemetry"]
    pricing = data["pricing"]

    n_records = len(records)

    required_protocol_fields = ("task_id", "model", "route", "temperature",
                                "agent_control_max_completion_tokens",
                                "max_agent_calls")
    complete = all(all(f in (r or {}) for f in required_protocol_fields) for r in records)

    _check(results, "CG-1", n_records == CAL_N and complete,
           f"records={n_records}/{CAL_N} metadata_complete={complete}")

    protocol_ok = all(
        r.get("model") == FROZEN_MODEL
        and FROZEN_ROUTE_FRAGMENT in str(r.get("route", ""))
        and abs(float(r.get("temperature", -1)) - FROZEN_TEMPERATURE) < 1e-9
        and int(r.get("agent_control_max_completion_tokens", -1)) > 0
        and int(r.get("max_agent_calls", -1)) == FROZEN_MAX_AGENT_CALLS
        for r in records
    )
    _check(results, "CG-2", protocol_ok, "all protocol metadata fields match frozen values")

    classified = all(
        t["valid_final_count"] > 0 or t["empty_reason"] in (
            "truncation", "round_cap", "parser_failure", "infrastructure")
        for t in telemetry
    )
    _check(results, "CG-3", len(telemetry) == CAL_N and classified,
           f"telemetry={len(telemetry)}/{CAL_N} all_classified={classified}")

    silent_parser = any(t["malformed_count"] > 0 and t["empty_reason"] != "parser_failure"
                        for t in telemetry)
    _check(results, "CG-4", not silent_parser,
           "silent_parser_failures=" + str(sum(
               1 for t in telemetry if t["malformed_count"] > 0 and t["empty_reason"] != "parser_failure")))

    unclassified = sum(1 for t in telemetry if t["empty_reason"] not in (
        "truncation", "round_cap", "parser_failure", "infrastructure", "none"))
    _check(results, "CG-5", unclassified == 0, f"unclassified_EMPTY={unclassified}")

    no_drift = bool(pricing.get("checks", {}).get("no_drift"))
    record_route_ok = all(FROZEN_ROUTE_FRAGMENT in str(r.get("route", "")) for r in records)
    _check(results, "CG-6", no_drift and record_route_ok,
           f"pricing_no_drift={no_drift} record_route_ok={record_route_ok}")

    knob_drift = any(
        abs(float(r.get("temperature", -1)) - FROZEN_TEMPERATURE) > 1e-9
        or int(r.get("max_agent_calls", -1)) != FROZEN_MAX_AGENT_CALLS
        for r in records
    )
    _check(results, "CG-7", not knob_drift, "unexpected_knob_drift=" + str(knob_drift))

    accounting_ok = all(
        int(r.get("token_usage", {}).get("total_tokens", -1))
        == int(r.get("token_usage", {}).get("prompt_tokens", -1))
        + int(r.get("token_usage", {}).get("completion_tokens", -1))
        for r in records
    )
    _check(results, "CG-8", accounting_ok, "accounting_identity_ok=" + str(accounting_ok))

    ceiling = pricing.get("frozen_calibration_ceiling_usd")
    if ceiling is not None:
        total = sum(float(r.get("token_usage", {}).get("usd_cost", 0.0)) for r in records)
        _check(results, "CG-9", total <= float(ceiling), f"calibration_usd={total:.6f} ceiling={float(ceiling):.6f}")
    else:
        _check(results, "CG-9", True, "ceiling not supplied by pricing preflight; no overrun assertion")


def _load_budget_worst_case() -> dict[str, float]:
    """Load the budget-v2 per-task worst-case USD map (report-only)."""
    if not BUDGET_MODEL_V2.is_file():
        return {}
    data = json.loads(BUDGET_MODEL_V2.read_text(encoding="utf-8"))
    wc = data.get("worst_case_per_task", {})
    return {tid: float(v["worst_case_usd"]) for tid, v in wc.items() if "worst_case_usd" in v}


def _classify_sidecar_for_gate(sidecar: list[dict]) -> dict:
    """Classify every sidecar call and tally the three error classes.

    Uses scripts/wp1b_sidecar_tool_audit.classify_record + error_class so gate
    v2 and the mechanical audit share one classification source of truth.
    """
    from wp1b_sidecar_tool_audit import classify_record, error_class

    tallies = {
        "instrument_errors": 0,
        "agent_misuse": 0,
        "frozen_policy_limit": 0,
        "successful_reads": 0,
        "rejected_repeat": 0,
        "tool_ok": 0,
        "tool_error_total": 0,
    }
    per_task_reads: dict[str, int] = {}
    per_task_search_hits: dict[str, int] = {}
    per_task_rejects: dict[str, int] = {}
    instrument_messages: dict[str, int] = {}
    agent_misuse_messages: dict[str, int] = {}
    frozen_policy_messages: dict[str, int] = {}
    for rec in sidecar:
        cls = classify_record(rec)
        tid = rec.get("task_id", "")
        action = rec.get("action", "")
        if cls == "tool_ok":
            tallies["tool_ok"] += 1
            if action == "read_file":
                tallies["successful_reads"] += 1
                per_task_reads[tid] = per_task_reads.get(tid, 0) + 1
            if action == "search_text" and int(rec.get("search_results_returned", 0) or 0) > 0:
                per_task_search_hits[tid] = per_task_search_hits.get(tid, 0) + 1
        elif cls == "rejected_repeat":
            tallies["rejected_repeat"] += 1
            per_task_rejects[tid] = per_task_rejects.get(tid, 0) + 1
        elif cls.startswith("tool_error:"):
            msg = cls.split(":", 1)[1]
            tallies["tool_error_total"] += 1
            cls_class = error_class(msg)
            if cls_class == "INSTRUMENT_ERROR":
                tallies["instrument_errors"] += 1
                instrument_messages[msg] = instrument_messages.get(msg, 0) + 1
            elif cls_class == "AGENT_MISUSE":
                tallies["agent_misuse"] += 1
                agent_misuse_messages[msg] = agent_misuse_messages.get(msg, 0) + 1
            elif cls_class == "FROZEN_POLICY_LIMIT":
                tallies["frozen_policy_limit"] += 1
                frozen_policy_messages[msg] = frozen_policy_messages.get(msg, 0) + 1
    return {
        **tallies,
        "per_task_reads": per_task_reads,
        "per_task_search_hits": per_task_search_hits,
        "per_task_rejects": per_task_rejects,
        "instrument_messages": instrument_messages,
        "agent_misuse_messages": agent_misuse_messages,
        "frozen_policy_messages": frozen_policy_messages,
    }


def evaluate(cal_dir: Path) -> dict:
    data = _load_records(cal_dir)
    results: list[dict] = []
    _run_cg1_9(results, data)

    all_pass = all(c["pass"] for c in results)
    result = {
        "artifact": "wp1b_calibration_gate_result",
        "evaluated_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "gate_status": "PASS" if all_pass else "FAIL",
        "checks": results,
        "note": "Calibration gate evaluated on a frozen check-set (artifacts/wp1b_calibration_gate.json). "
                "It is an instrumentation/protocol sanity gate; calibration F1 does not gate the main run.",
    }
    (cal_dir / "wp1b_calibration_gate_result.json").write_text(
        json.dumps(result, indent=1), encoding="utf-8")
    for c in results:
        print(f"[gate] {c['id']}: {'PASS' if c['pass'] else 'FAIL'} - {c['detail']}")
    print(f"[gate] GATE: {result['gate_status']}")
    return result


def evaluate_v2(cal_dir: Path) -> dict:
    """Gate v2: CG-1..CG-9 + CG-10 + CG-11 + report-only metrics.

    The per-call sidecar (wp1b_call_sidecar.jsonl) is required. On Calibration-3
    (pre-A4) the sidecar lacks tool_ok/tool_error, so classification falls back
    to the mechanical audit length-based reconstruction.
    """
    data = _load_records(cal_dir, with_sidecar=True)
    results: list[dict] = []
    _run_cg1_9(results, data)

    sidecar = data.get("sidecar", [])
    sidecar_ok = len(sidecar) > 0
    tallies: dict[str, Any] = (
        _classify_sidecar_for_gate(sidecar) if sidecar else {
            "instrument_errors": 0, "agent_misuse": 0, "frozen_policy_limit": 0,
            "successful_reads": 0, "rejected_repeat": 0, "tool_ok": 0,
            "tool_error_total": 0, "per_task_reads": {}, "per_task_search_hits": {},
            "per_task_rejects": {}, "instrument_messages": {},
            "agent_misuse_messages": {}, "frozen_policy_messages": {},
        }
    )

    _check(results, "CG-10", sidecar_ok and tallies["instrument_errors"] == 0,
           f"instrument_errors={tallies['instrument_errors']} "
           f"messages={tallies['instrument_messages']} sidecar={sidecar_ok}")

    max_reads = max(tallies["per_task_reads"].values(), default=0)
    _check(results, "CG-11", sidecar_ok and max_reads >= 1,
           f"per_task_successful_reads={tallies['per_task_reads']} max={max_reads}")

    # ---------- report-only metrics ----------
    worst_case = _load_budget_worst_case()
    cost_ratios: dict[str, float | None] = {}
    for r in data["records"]:
        tid = r.get("task_id", "")
        usd = float(r.get("token_usage", {}).get("usd_cost", 0.0))
        wc = worst_case.get(tid)
        cost_ratios[tid] = (usd / wc) if wc else None

    report_only: dict[str, Any] = {
        "per_task": [],
        "aggregate": {
            "calls": len(sidecar),
            "tool_ok": tallies["tool_ok"],
            "instrument_errors": tallies["instrument_errors"],
            "agent_misuse": tallies["agent_misuse"],
            "frozen_policy_limit": tallies["frozen_policy_limit"],
            "rejected_repeat": tallies["rejected_repeat"],
            "successful_reads": tallies["successful_reads"],
            "instrument_messages": tallies["instrument_messages"],
            "agent_misuse_messages": tallies["agent_misuse_messages"],
            "frozen_policy_messages": tallies["frozen_policy_messages"],
        },
    }
    tel_by_task = {t["task_id"]: t for t in data["telemetry"]}
    for tid in sorted({r.get("task_id", "") for r in data["records"]}):
        t = tel_by_task.get(tid, {})
        report_only["per_task"].append({
            "task_id": tid,
            "llm_calls": int(t.get("model_calls", 0)),
            "successful_reads": tallies["per_task_reads"].get(tid, 0),
            "search_calls_with_hits": tallies["per_task_search_hits"].get(tid, 0),
            "rejected_repeat": tallies["per_task_rejects"].get(tid, 0),
            "observation_truncation_rate": t.get("observation_truncation_rate", 0.0),
            "finish_reason_distribution": t.get("finish_reason_distribution", {}),
            "prompt_tokens": int(
                next((r.get("token_usage", {}).get("prompt_tokens", 0)
                      for r in data["records"] if r.get("task_id") == tid), 0)),
            "completion_tokens": int(
                next((r.get("token_usage", {}).get("completion_tokens", 0)
                      for r in data["records"] if r.get("task_id") == tid), 0)),
            "total_tokens": int(
                next((r.get("token_usage", {}).get("total_tokens", 0)
                      for r in data["records"] if r.get("task_id") == tid), 0)),
            "actual_usd": float(
                next((r.get("token_usage", {}).get("usd_cost", 0.0)
                      for r in data["records"] if r.get("task_id") == tid), 0.0)),
            "worst_case_usd": worst_case.get(tid),
            "cost_ratio": cost_ratios.get(tid),
        })

    all_pass = all(c["pass"] for c in results)
    result = {
        "artifact": "wp1b_calibration_gate_v2_result",
        "evaluated_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "gate_status": "PASS" if all_pass else "FAIL",
        "checks": results,
        "report_only": report_only,
        "note": "Gate v2 evaluated on a frozen check-set (artifacts/wp1b_calibration_gate_v2.json). "
                "CG-10/CG-11 check the INSTRUMENT validity of the agent's tools, NOT labels and NOT F1. "
                "Distinguish GATE PASS from INSTRUMENT VALID.",
    }
    (cal_dir / "wp1b_calibration_gate_v2_result.json").write_text(
        json.dumps(result, indent=1), encoding="utf-8")
    for c in results:
        print(f"[gate] {c['id']}: {'PASS' if c['pass'] else 'FAIL'} - {c['detail']}")
    print(f"[gate] GATE: {result['gate_status']}")
    print(f"[gate] report_only: instrument_errors={report_only['aggregate']['instrument_errors']} "
          f"successful_reads={report_only['aggregate']['successful_reads']} "
          f"rejected_repeat={report_only['aggregate']['rejected_repeat']}")
    return result


def _rejection_run_analysis(sidecar: list[dict]) -> dict:
    """Per-task longest run of consecutive rejected repeats + aggregate share.

    CG-12: a run of >= 3 consecutive identical rejected requests is the
    deterministic context loop (Calibration-3b had runs of 6 and 4). Uses the
    same classify_record source of truth as the audit.
    """
    from wp1b_sidecar_tool_audit import classify_record

    per_task_longest: dict[str, int] = {}
    per_task_runs: dict[str, list[int]] = {}
    current: dict[str, int] = {}
    rejected_total = 0
    calls_total = 0
    for rec in sidecar:
        calls_total += 1
        tid = rec.get("task_id", "")
        cls = classify_record(rec)
        if cls == "rejected_repeat":
            rejected_total += 1
            current[tid] = current.get(tid, 0) + 1
        else:
            if current.get(tid, 0):
                per_task_runs.setdefault(tid, []).append(current[tid])
                per_task_longest[tid] = max(per_task_longest.get(tid, 0), current[tid])
                current[tid] = 0
    for tid, run in current.items():
        if run:
            per_task_runs.setdefault(tid, []).append(run)
            per_task_longest[tid] = max(per_task_longest.get(tid, 0), run)
    return {
        "per_task_longest_run": per_task_longest,
        "per_task_runs": per_task_runs,
        "rejected_repeat_calls": rejected_total,
        "calls": calls_total,
        "rejected_repeat_share": (rejected_total / calls_total) if calls_total else 0.0,
    }


def evaluate_v3(cal_dir: Path) -> dict:
    """Gate v3: CG-1..CG-11 (as v2) + CG-12 (no >= 3 consecutive rejected repeats).

    Also reports the rejected-repeat share of all calls. Run against the
    Calibration-3b records BEFORE Calibration-3c: CG-12 must FAIL (runs of 6
    and 4) as the RED proof that the gate catches the loop prospectively.
    """
    data = _load_records(cal_dir, with_sidecar=True)
    results: list[dict] = []
    _run_cg1_9(results, data)

    sidecar = data.get("sidecar", [])
    sidecar_ok = len(sidecar) > 0
    tallies: dict[str, Any] = (
        _classify_sidecar_for_gate(sidecar) if sidecar else {
            "instrument_errors": 0, "agent_misuse": 0, "frozen_policy_limit": 0,
            "successful_reads": 0, "rejected_repeat": 0, "tool_ok": 0,
            "tool_error_total": 0, "per_task_reads": {}, "per_task_search_hits": {},
            "per_task_rejects": {}, "instrument_messages": {},
            "agent_misuse_messages": {}, "frozen_policy_messages": {},
        }
    )

    _check(results, "CG-10", sidecar_ok and tallies["instrument_errors"] == 0,
           f"instrument_errors={tallies['instrument_errors']} "
           f"messages={tallies['instrument_messages']} sidecar={sidecar_ok}")

    max_reads = max(tallies["per_task_reads"].values(), default=0)
    _check(results, "CG-11", sidecar_ok and max_reads >= 1,
           f"per_task_successful_reads={tallies['per_task_reads']} max={max_reads}")

    run_analysis = _rejection_run_analysis(sidecar)
    longest_by_task = run_analysis["per_task_longest_run"]
    cg12_ok = sidecar_ok and all(v <= 2 for v in longest_by_task.values())
    _check(results, "CG-12", cg12_ok,
           f"per_task_longest_rejection_run={longest_by_task} "
           f"rejected_share={run_analysis['rejected_repeat_share']:.3f} "
           f"rejected_calls={run_analysis['rejected_repeat_calls']}")

    # ---------- report-only metrics ----------
    worst_case = _load_budget_worst_case()
    cost_ratios: dict[str, float | None] = {}
    for r in data["records"]:
        tid = r.get("task_id", "")
        usd = float(r.get("token_usage", {}).get("usd_cost", 0.0))
        wc = worst_case.get(tid)
        cost_ratios[tid] = (usd / wc) if wc else None

    report_only: dict[str, Any] = {
        "per_task": [],
        "aggregate": {
            "calls": len(sidecar),
            "tool_ok": tallies["tool_ok"],
            "instrument_errors": tallies["instrument_errors"],
            "agent_misuse": tallies["agent_misuse"],
            "frozen_policy_limit": tallies["frozen_policy_limit"],
            "rejected_repeat": tallies["rejected_repeat"],
            "rejected_repeat_share": run_analysis["rejected_repeat_share"],
            "successful_reads": tallies["successful_reads"],
            "instrument_messages": tallies["instrument_messages"],
            "agent_misuse_messages": tallies["agent_misuse_messages"],
            "frozen_policy_messages": tallies["frozen_policy_messages"],
        },
    }
    tel_by_task = {t["task_id"]: t for t in data["telemetry"]}
    for tid in sorted({r.get("task_id", "") for r in data["records"]}):
        t = tel_by_task.get(tid, {})
        report_only["per_task"].append({
            "task_id": tid,
            "llm_calls": int(t.get("model_calls", 0)),
            "successful_reads": tallies["per_task_reads"].get(tid, 0),
            "search_calls_with_hits": tallies["per_task_search_hits"].get(tid, 0),
            "rejected_repeat": tallies["per_task_rejects"].get(tid, 0),
            "longest_rejection_run": longest_by_task.get(tid, 0),
            "observation_truncation_rate": t.get("observation_truncation_rate", 0.0),
            "finish_reason_distribution": t.get("finish_reason_distribution", {}),
            "prompt_tokens": int(
                next((r.get("token_usage", {}).get("prompt_tokens", 0)
                      for r in data["records"] if r.get("task_id") == tid), 0)),
            "completion_tokens": int(
                next((r.get("token_usage", {}).get("completion_tokens", 0)
                      for r in data["records"] if r.get("task_id") == tid), 0)),
            "total_tokens": int(
                next((r.get("token_usage", {}).get("total_tokens", 0)
                      for r in data["records"] if r.get("task_id") == tid), 0)),
            "actual_usd": float(
                next((r.get("token_usage", {}).get("usd_cost", 0.0)
                      for r in data["records"] if r.get("task_id") == tid), 0.0)),
            "worst_case_usd": worst_case.get(tid),
            "cost_ratio": cost_ratios.get(tid),
        })

    all_pass = all(c["pass"] for c in results)
    result = {
        "artifact": "wp1b_calibration_gate_v3_result",
        "evaluated_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "gate_status": "PASS" if all_pass else "FAIL",
        "checks": results,
        "report_only": report_only,
        "note": "Gate v3 evaluated on a frozen check-set (artifacts/wp1b_calibration_gate_v3.json). "
                "CG-12 makes a run of >= 3 consecutive rejected repeats a GATING instrument defect "
                "(the deterministic context loop). CG-10/CG-11/CG-12 check the INSTRUMENT validity "
                "of the agent's tools, NOT labels and NOT F1. Distinguish GATE PASS from INSTRUMENT VALID.",
    }
    (cal_dir / "wp1b_calibration_gate_v3_result.json").write_text(
        json.dumps(result, indent=1), encoding="utf-8")
    for c in results:
        print(f"[gate] {c['id']}: {'PASS' if c['pass'] else 'FAIL'} - {c['detail']}")
    print(f"[gate] GATE: {result['gate_status']}")
    print(f"[gate] report_only: instrument_errors={report_only['aggregate']['instrument_errors']} "
          f"successful_reads={report_only['aggregate']['successful_reads']} "
          f"rejected_repeat={report_only['aggregate']['rejected_repeat']} "
          f"rejected_share={report_only['aggregate']['rejected_repeat_share']:.3f}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="WP-1b calibration gate evaluator")
    parser.add_argument("calibration_dir", nargs="?")
    parser.add_argument("--gate", choices=("v1", "v2", "v3"), default="v1",
                        help="gate version to evaluate (default v1)")
    args = parser.parse_args()

    if args.gate == "v3":
        gate = json.loads(GATE_V3.read_text(encoding="utf-8"))
        artifact_name = gate["artifact"]
    elif args.gate == "v2":
        gate = json.loads(GATE_V2.read_text(encoding="utf-8"))
        artifact_name = gate["artifact"]
    else:
        gate = json.loads(GATE.read_text(encoding="utf-8"))
        artifact_name = gate["artifact"]

    if args.calibration_dir is None:
        print(f"[gate] FROZEN (not evaluated): {artifact_name} status={gate['status']}")
        print("[gate] provide a calibration results directory to evaluate.")
        return 0

    cal_dir = Path(args.calibration_dir)
    if not cal_dir.is_dir():
        print(f"[gate] ERROR: calibration directory not found: {cal_dir}")
        return 1

    if args.gate == "v3":
        result = evaluate_v3(cal_dir)
    elif args.gate == "v2":
        result = evaluate_v2(cal_dir)
    else:
        result = evaluate(cal_dir)
    return 0 if result["gate_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
