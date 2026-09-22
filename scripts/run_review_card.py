#!/usr/bin/env python3
"""WP-1b Review Card generator (ZERO API, standing tool).

Writes REVIEW_CARD.md into a calibration results directory. The card has a
per-call table, a per-task summary, and anomaly flags split into BLOCKING and
INFORMATIONAL (Ahmed's clarification 2026-09-22).

BLOCKING anomalies (any one fails the run):
  B1  any instrument-class tool error
  B2  a run of >= 3 consecutive identical rejected requests
  B3  zero successful reads across ALL tasks in the run
  B4  cost ratio to the budget-v2 worst case > 1.0 on any task
  B5  other contract-defined hard failures (EMPTY prediction, scientific-knob
      drift, or a FAILING calibration gate check)

INFORMATIONAL anomalies (do NOT fail the run):
  I1  an individual task with zero read_file calls
  I2  search/list-only task behavior (>= 1 tool call but zero reads)
  I3  ordinary frozen-policy-limit events
  I4  identical normalized tool output/error repeated >= 3 times
      (content-normalized, so equal string LENGTH alone cannot create a flag)
  I5  prompt growth < 25 tokens across >= 2 consecutive calls

Usage:
  python scripts/run_review_card.py <records_dir>

Output:
  <records_dir>/REVIEW_CARD.md

Exit codes:
  0  card written
  2  input error
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path
from typing import Any

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))
sys.path.insert(0, str(_PROJECT_DIR / "scripts"))

from wp1b_sidecar_tool_audit import (  # noqa: E402
    classify_record,
    error_class,
)

FROZEN_MODEL = "qwen/qwen3-coder"
FROZEN_ROUTE_FRAGMENT = "deepinfra/turbo"
FROZEN_TEMPERATURE = 0.0
FROZEN_MAX_AGENT_CALLS = 8
BUDGET_MODEL_V2 = _PROJECT_DIR / "research" / "wp1b" / "wp1b_budget_model_v2.json"

_WS = re.compile(r"\s+")


def _normalize(text: str) -> str:
    """Content normalization for the identical-output/error anomaly (I4).

    Whitespace collapse + casefold. Purely LENGTH-based equality is never used,
    so equal string lengths alone cannot create a false anomaly.
    """
    return _WS.sub(" ", text.strip()).casefold()


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _load_budget_worst_case() -> dict[str, float]:
    if not BUDGET_MODEL_V2.is_file():
        return {}
    data = json.loads(BUDGET_MODEL_V2.read_text(encoding="utf-8"))
    wc = data.get("worst_case_per_task", {})
    return {tid: float(v["worst_case_usd"]) for tid, v in wc.items() if "worst_case_usd" in v}


def _build_review(cal_dir: Path) -> dict[str, Any]:
    records = _load_jsonl(cal_dir / "calibration_run_records.jsonl")
    sidecar = _load_jsonl(cal_dir / "wp1b_call_sidecar.jsonl")
    telemetry = _load_jsonl(cal_dir / "wp1b_telemetry.jsonl")
    pricing = json.loads((cal_dir / "pricing_preflight.json").read_text(encoding="utf-8"))
    worst_case = _load_budget_worst_case()

    per_call_rows: list[dict[str, Any]] = []
    per_task: dict[str, dict[str, Any]] = {}
    instrument_errors_total = 0
    successful_reads_total = 0
    calls_total = 0
    rejected_total = 0
    runs: dict[str, int] = {}

    normalized_outcomes: dict[str, int] = {}
    task_tool_ok: dict[str, int] = {}

    for rec in sidecar:
        tid = rec.get("task_id", "")
        calls_total += 1
        cls = classify_record(rec)
        agg = per_task.setdefault(tid, {
            "task_id": tid,
            "calls": 0,
            "useful_tool_calls": 0,
            "rejected_repeat": 0,
            "final": 0,
            "tool_error": 0,
            "instrument_errors": 0,
            "agent_misuse": 0,
            "frozen_policy_limit": 0,
            "successful_reads": 0,
            "longest_rejection_run": 0,
            "current_rejection_run": 0,
            "rejected_spend_usd": 0.0,
            "prompt_tokens": [],
            "truncation_events": 0,
            "search_result_cap_hits": 0,
            "tool_error_messages": {},
        })
        agg["calls"] += 1
        args = _format_args(rec)
        rejected = cls == "rejected_repeat"
        ok = cls == "tool_ok"
        error_text = ""
        if cls == "tool_ok":
            agg["useful_tool_calls"] += 1
            task_tool_ok[tid] = task_tool_ok.get(tid, 0) + 1
            if rec.get("action") == "read_file":
                agg["successful_reads"] += 1
                successful_reads_total += 1
            agg["current_rejection_run"] = 0
        elif cls == "rejected_repeat":
            agg["rejected_repeat"] += 1
            rejected_total += 1
            agg["rejected_spend_usd"] += float(rec.get("usd", 0.0) or 0.0)
            agg["current_rejection_run"] += 1
            agg["longest_rejection_run"] = max(agg["longest_rejection_run"], agg["current_rejection_run"])
        elif cls.startswith("tool_error:"):
            msg = cls.split(":", 1)[1]
            error_text = msg
            agg["tool_error"] += 1
            agg["tool_error_messages"][msg] = agg["tool_error_messages"].get(msg, 0) + 1
            norm = _normalize(msg)
            normalized_outcomes[norm] = normalized_outcomes.get(norm, 0) + 1
            cls_class = error_class(msg)
            if cls_class == "INSTRUMENT_ERROR":
                agg["instrument_errors"] += 1
                instrument_errors_total += 1
            elif cls_class == "FROZEN_POLICY_LIMIT":
                agg["frozen_policy_limit"] += 1
            else:
                agg["agent_misuse"] += 1
            agg["current_rejection_run"] = 0
        else:
            agg["current_rejection_run"] = 0
            if cls == "final":
                agg["final"] += 1
        if bool(rec.get("observation_truncated", False)):
            agg["truncation_events"] += 1
        if int(rec.get("search_result_cap_hit", 0) or 0):
            agg["search_result_cap_hits"] += 1
        per_call_rows.append({
            "task_id": tid,
            "k": rec.get("call_index", 0),
            "action": rec.get("action", ""),
            "arguments": args,
            "ok": (
                "ok" if ok else ("rejected" if rejected else (
                    "error" if error_text else ("final" if cls == "final" else "")
                ))
            ),
            "error_text": error_text,
            "chars_raw": rec.get("tool_output_chars_raw", 0),
            "chars_shown": rec.get("tool_output_chars_shown", 0),
            "rejected": rejected,
            "prompt_tokens": int(rec.get("prompt_tokens", 0) or 0),
        })

    runs = {tid: a["longest_rejection_run"] for tid, a in per_task.items()}

    # Per-task summary numbers from records/telemetry
    tel_by_task = {t["task_id"]: t for t in telemetry}
    rec_by_task = {r["task_id"]: r for r in records}
    per_task_summary: list[dict[str, Any]] = []
    for tid in sorted(per_task):
        agg = per_task[tid]
        tel = tel_by_task.get(tid, {})
        rec = rec_by_task.get(tid, {})
        usage = rec.get("token_usage", {})
        usd = float(usage.get("usd_cost", 0.0))
        wc = worst_case.get(tid)
        per_task_summary.append({
            "task_id": tid,
            "calls": agg["calls"],
            "useful_tool_calls": agg["useful_tool_calls"],
            "successful_reads": agg["successful_reads"],
            "rejected_repeat": agg["rejected_repeat"],
            "longest_rejection_run": agg["longest_rejection_run"],
            "instrument_errors": agg["instrument_errors"],
            "agent_misuse": agg["agent_misuse"],
            "frozen_policy_limit": agg["frozen_policy_limit"],
            "truncation_events": agg["truncation_events"],
            "search_result_cap_hits": agg["search_result_cap_hits"],
            "prompt_tokens": int(usage.get("prompt_tokens", 0)),
            "completion_tokens": int(usage.get("completion_tokens", 0)),
            "total_tokens": int(usage.get("total_tokens", 0)),
            "actual_usd": usd,
            "worst_case_usd": wc,
            "cost_ratio": (usd / wc) if wc else None,
            "empty_reason": tel.get("empty_reason", "unknown"),
            "rejected_spend_usd": round(agg["rejected_spend_usd"], 6),
        })

    # ---- anomaly flags ----
    blocking: list[dict[str, Any]] = []
    informational: list[dict[str, Any]] = []

    if instrument_errors_total > 0:
        blocking.append({
            "id": "B1",
            "detail": f"{instrument_errors_total} instrument-class tool errors across the run",
        })
    if any(v >= 3 for v in runs.values()):
        blocking.append({
            "id": "B2",
            "detail": f"run(s) of >= 3 consecutive identical rejected requests: {runs}",
        })
    if successful_reads_total == 0 and per_task:
        blocking.append({"id": "B3", "detail": "zero successful read_file across ALL tasks in the run"})
    for s in per_task_summary:
        if s["cost_ratio"] is not None and s["cost_ratio"] > 1.0:
            blocking.append({"id": "B4", "detail": f"cost ratio {s['cost_ratio']:.3f} > 1.0 on {s['task_id']}"})
    empties = [s["task_id"] for s in per_task_summary if s["empty_reason"] != "none"]
    if empties:
        blocking.append({"id": "B5", "detail": f"EMPTY prediction(s) (contract hard failure): {empties}"})
    for rec in records:
        drift = []
        if rec.get("model") != FROZEN_MODEL:
            drift.append("model")
        if FROZEN_ROUTE_FRAGMENT not in str(rec.get("route", "")):
            drift.append("route")
        if abs(float(rec.get("temperature", -1)) - FROZEN_TEMPERATURE) > 1e-9:
            drift.append("temperature")
        if int(rec.get("max_agent_calls", -1)) != FROZEN_MAX_AGENT_CALLS:
            drift.append("max_agent_calls")
        if drift:
            blocking.append({"id": "B5", "detail": f"scientific-knob drift on {rec.get('task_id')}: {drift}"})
    gate_path = cal_dir / "wp1b_calibration_gate_v3_result.json"
    if gate_path.is_file():
        gate = json.loads(gate_path.read_text(encoding="utf-8"))
        failed = [c["id"] for c in gate.get("checks", []) if not c["pass"]]
        if failed:
            blocking.append({"id": "B5", "detail": f"calibration gate FAIL on check(s): {failed}"})

    for s in per_task_summary:
        if s["successful_reads"] == 0:
            informational.append({
                "id": "I1",
                "detail": f"task {s['task_id']} has 0 read_file calls",
            })
            if s["useful_tool_calls"] > 0:
                informational.append({
                    "id": "I2",
                    "detail": (
                        f"task {s['task_id']} is search/list-only "
                        f"(0 reads, {s['useful_tool_calls']} tool calls)"
                    ),
                })
    for s in per_task_summary:
        if s["frozen_policy_limit"] > 0:
            informational.append({
                "id": "I3",
                "detail": (
                    f"task {s['task_id']}: {s['frozen_policy_limit']} "
                    "frozen-policy-limit event(s)"
                ),
            })
        if s["search_result_cap_hits"] > 0:
            informational.append({
                "id": "I3",
                "detail": (
                    f"task {s['task_id']}: {s['search_result_cap_hits']} "
                    "search-result-cap hit(s)"
                ),
            })
    for norm, count in sorted(normalized_outcomes.items()):
        if count >= 3:
            informational.append({
                "id": "I4",
                "detail": (
                    f"identical normalized tool output/error repeated {count} "
                    f"times: '{norm[:80]}'"
                ),
            })
    for tid in sorted(per_task):
        prompts = [int(c["prompt_tokens"]) for c in per_call_rows if c["task_id"] == tid]
        if len(prompts) >= 2:
            small = sum(
                1 for a, b in zip(prompts, prompts[1:], strict=False)
                if 0 <= (b - a) < 25
            )
            if small >= 1:
                informational.append({
                    "id": "I5",
                    "detail": (
                        f"task {tid}: prompt growth < 25 tokens on {small} of "
                        f"{len(prompts) - 1} consecutive-call deltas"
                    ),
                })

    return {
        "artifact": "wp1b_review_card",
        "records_dir": str(cal_dir),
        "evaluated_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "per_call": per_call_rows,
        "per_task": per_task_summary,
        "aggregate": {
            "calls": calls_total,
            "useful_tool_calls": sum(task_tool_ok.values()),
            "rejected_repeat": rejected_total,
            "rejected_share": (rejected_total / calls_total) if calls_total else 0.0,
            "successful_reads": successful_reads_total,
            "instrument_errors": instrument_errors_total,
            "pricing_no_drift": bool(pricing.get("checks", {}).get("no_drift")),
        },
        "blocking_anomalies": blocking,
        "informational_anomalies": informational,
    }


def _format_args(rec: dict[str, Any]) -> str:
    parts = []
    path = rec.get("path", "")
    query = rec.get("query", "")
    if path:
        parts.append(f'path="{path}"')
    if query:
        parts.append(f'query="{query}"')
    return " ".join(parts)


def _render_markdown(review: dict[str, Any]) -> str:
    agg = review["aggregate"]
    lines: list[str] = []
    lines.append("# WP-1b Review Card")
    lines.append("")
    lines.append(f"- records_dir: `{review['records_dir']}`")
    lines.append(f"- evaluated_utc: {review['evaluated_utc']}")
    lines.append(f"- calls: {agg['calls']} | useful tool calls: {agg['useful_tool_calls']} | "
                 f"rejected repeats: {agg['rejected_repeat']} ({agg['rejected_share']:.1%} share) | "
                 f"successful reads: {agg['successful_reads']} | instrument errors: {agg['instrument_errors']}")
    lines.append("")
    lines.append("## Per-call table")
    lines.append("")
    lines.append("| task | k | action | arguments | outcome | error text | chars raw/shown | rejected |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for c in review["per_call"]:
        lines.append(
            f"| {c['task_id']} | {c['k']} | {c['action']} | {c['arguments']} | {c['ok']} | "
            f"{c['error_text']} | {c['chars_raw']}/{c['chars_shown']} | {c['rejected']} |"
        )
    lines.append("")
    lines.append("## Per-task summary")
    lines.append("")
    lines.append("| task | calls | useful | reads | rejects | longest run | instr err | empty | cost ratio | USD |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for s in review["per_task"]:
        cr = f"{s['cost_ratio']:.3f}" if s["cost_ratio"] is not None else "n/a"
        lines.append(
            f"| {s['task_id']} | {s['calls']} | {s['useful_tool_calls']} | {s['successful_reads']} | "
            f"{s['rejected_repeat']} | {s['longest_rejection_run']} | {s['instrument_errors']} | "
            f"{s['empty_reason']} | {cr} | {s['actual_usd']:.6f} |"
        )
    lines.append("")
    lines.append("## Anomaly flags")
    lines.append("")
    lines.append("### BLOCKING")
    if review["blocking_anomalies"]:
        for a in review["blocking_anomalies"]:
            lines.append(f"- **{a['id']}** {a['detail']}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("### INFORMATIONAL")
    if review["informational_anomalies"]:
        for a in review["informational_anomalies"]:
            lines.append(f"- {a['id']} {a['detail']}")
    else:
        lines.append("- none")
    lines.append("")
    verdict = "BLOCKED" if review["blocking_anomalies"] else "NO_BLOCKING_ANOMALIES"
    lines.append(f"## Verdict: {verdict}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("records_dir", help="calibration results directory")
    args = parser.parse_args(argv)

    cal_dir = Path(args.records_dir)
    for required in ("calibration_run_records.jsonl", "wp1b_call_sidecar.jsonl", "wp1b_telemetry.jsonl"):
        if not (cal_dir / required).is_file():
            print(f"[review-card] ERROR: missing {required} in {cal_dir}")
            return 2

    review = _build_review(cal_dir)
    (cal_dir / "REVIEW_CARD.md").write_text(_render_markdown(review), encoding="utf-8")
    print(f"[review-card] BLOCKING={len(review['blocking_anomalies'])} "
          f"INFORMATIONAL={len(review['informational_anomalies'])}")
    for a in review["blocking_anomalies"]:
        print(f"[review-card] BLOCKING {a['id']}: {a['detail']}")
    for a in review["informational_anomalies"]:
        print(f"[review-card] INFO {a['id']}: {a['detail']}")
    print(f"[review-card] wrote {cal_dir / 'REVIEW_CARD.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
