#!/usr/bin/env python3
"""WP-1b MAIN-mode Review Card (ZERO API, label-free) for a MAIN_297 / variance run.

Calibration Review Cards (scripts/run_review_card.py) treat any EMPTY
prediction, any 3-long rejection run or any cost ratio > 1 as BLOCKING. That is
right for a 3-task instrument check and WRONG for a 297-task scientific run,
where per-task agent behaviour is DATA. In MAIN mode:

BLOCKING (instrument-level only; mirrors the runner halts H1-H7):
  M1 the run halted (halt_report.json present) or is incomplete
  M2 instrument-class tool errors in > 5% of items
  M3 transport-failure (infrastructure) EMPTY in > 5% of items
  M4 a frozen-knob / protocol / model / route drift in any record
  M5 allow_ground_truth_universe is not False in any record
  M6 accounting mismatch (AC-14): for any kept record, the ledger USD of its
     attempt_id differs from the record usd_cost by > $0.000001, or the ledger
     total differs from (sum of kept record USD + abandoned-attempt USD)
INFORMATIONAL (reported with distributions, never blocking):
  EMPTY by reason, forced finals, rejected repeats and longest runs,
  non-consecutive duplicate requests, zero-result searches, 0-read items,
  observation truncation, cost ratio to budget-v2 worst case, retries.

Usage: python scripts/wp1b_main_review_card.py <run_dir>   -> <run_dir>/MAIN_REVIEW_CARD.md (+ .json)
Exit: 0 no BLOCKING | 1 at least one BLOCKING item | 2 usage | 3 run dir unreadable
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

import numpy as np  # noqa: E402

from benchmark.wp1b import main_runner as mr  # noqa: E402
from benchmark.wp1b.exploratory import x11_tool_quality  # noqa: E402

USD_TOLERANCE = 1e-6


def reconcile_ledger(records: list[dict[str, Any]], ledger: list[dict[str, Any]]) -> dict[str, Any]:
    """AC-14, attempt-aware: restarted / crashed attempts spend real money but
    produce no kept record, so the ledger total is (kept record USD + abandoned
    attempt USD), and each kept record must equal the ledger USD of its own
    attempt_id."""
    by_attempt: dict[str, float] = {}
    for e in ledger:
        if e.get("kind") == "call":
            aid = str(e.get("attempt_id") or e.get("work_key"))
            by_attempt[aid] = by_attempt.get(aid, 0.0) + float(e.get("usd", 0.0))
    kept = {str(r.get("attempt_id") or r.get("work_key")): float(r["token_usage"]["usd_cost"]) for r in records}
    mismatched = [aid for aid, usd in kept.items() if abs(by_attempt.get(aid, 0.0) - usd) > USD_TOLERANCE]
    abandoned = {aid: usd for aid, usd in by_attempt.items() if aid not in kept}
    ledger_total = sum(by_attempt.values())
    kept_total = sum(kept.values())
    abandoned_total = sum(abandoned.values())
    return {
        "ledger_total_usd": round(ledger_total, 6),
        "kept_records_usd": round(kept_total, 6),
        "abandoned_attempts_usd": round(abandoned_total, 6),
        "abandoned_attempts": len(abandoned),
        "per_record_mismatches": mismatched,
        "total_matches": abs(ledger_total - kept_total - abandoned_total) <= USD_TOLERANCE,
        "ok": not mismatched and abs(ledger_total - kept_total - abandoned_total) <= USD_TOLERANCE,
    }


def build_card(run_dir: Path) -> dict[str, Any]:
    records, _ = mr.read_jsonl_tolerant(run_dir / mr.RECORDS_FILE)
    ledger, ledger_bad = mr.read_jsonl_tolerant(run_dir / mr.LEDGER_FILE)
    telemetry, _ = mr.read_jsonl_tolerant(run_dir / mr.TELEMETRY_FILE)
    sidecar, _ = mr.read_jsonl_tolerant(run_dir / mr.SIDECAR_FILE)
    state = json.loads((run_dir / mr.STATE_FILE).read_text(encoding="utf-8"))
    summary_path = run_dir / mr.SUMMARY_FILE
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    n = len(records)
    total = int(state.get("n_items", n))
    tel_by = {str(t["work_key"]): t for t in telemetry}

    empty: dict[str, int] = {}
    for r in records:
        if r.get("prediction_empty"):
            empty[str(r["empty_reason"])] = empty.get(str(r["empty_reason"]), 0) + 1
    calls_hist: dict[str, int] = {}
    for r in records:
        calls_hist[str(r["model_calls"])] = calls_hist.get(str(r["model_calls"]), 0) + 1
    reads = [int(tel_by.get(str(r["work_key"]), {}).get("successful_reads", 0)) for r in records]
    rejected = [int(tel_by.get(str(r["work_key"]), {}).get("rejected_repeat_count", 0)) for r in records]
    instrument_items = sum(
        1 for r in records
        if any(str(m) in mr.INSTRUMENT_TOOL_ERRORS
               for m in (tel_by.get(str(r["work_key"]), {}).get("tool_error_counts") or {}))
    )
    infra_items = sum(1 for r in records if r.get("infra_failure"))
    ratios = [float(r["token_usage"]["usd_cost"]) / float(r["worst_case_usd_budget_v2"])
              for r in records if float(r.get("worst_case_usd_budget_v2", 0)) > 0]
    drift = [r["work_key"] for r in records
             if r.get("protocol") != mr.PROTOCOL_ID or r.get("model") != mr.FROZEN_MODEL
             or r.get("route") != mr.FROZEN_ROUTE or r.get("max_agent_calls") != mr.FROZEN_MAX_AGENT_CALLS
             or r.get("agent_control_max_completion_tokens") != mr.FROZEN_AGENT_CAP
             or r.get("temperature") != mr.FROZEN_TEMPERATURE]
    gt = [r["work_key"] for r in records if r.get("allow_ground_truth_universe") is not False]
    halted = (run_dir / mr.HALT_FILE).exists()
    history = run_dir / "halt_history"
    resolved_halts = sorted(p.name for p in history.iterdir()) if history.is_dir() else []

    blocking = []
    if halted or n < total or summary.get("status") != "COMPLETE":
        blocking.append(f"M1 run halted or incomplete ({n}/{total}; status {summary.get('status')})")
    if n and instrument_items / n > 0.05:
        blocking.append(f"M2 instrument-class tool errors in {instrument_items}/{n} items")
    if n and infra_items / n > 0.05:
        blocking.append(f"M3 transport-failure EMPTY in {infra_items}/{n} items")
    if drift:
        blocking.append(f"M4 knob/protocol drift in {len(drift)} records (first {drift[:3]})")
    if gt:
        blocking.append(f"M5 allow_ground_truth_universe not False in {len(gt)} records")
    recon = reconcile_ledger(records, ledger)
    if not recon["ok"] or ledger_bad:
        blocking.append(f"M6 ledger/record accounting mismatch (per-record {recon['per_record_mismatches'][:3]}, "
                        f"total_matches={recon['total_matches']}, unparseable ledger lines={len(ledger_bad)})")

    tq = x11_tool_quality(sidecar)
    usd = [float(r["token_usage"]["usd_cost"]) for r in records]
    return {
        "artifact": "wp1b_main_review_card",
        "run_label": state.get("run_label"),
        "items": f"{n}/{total}",
        "status": summary.get("status"),
        "ledger_usd": summary.get("ledger_usd"),
        "ledger_reconciliation_AC14": recon,
        "blocking": blocking,
        "verdict": "NO_BLOCKING_INSTRUMENT_ANOMALIES" if not blocking else "BLOCKING_INSTRUMENT_ANOMALY",
        "informational": {
            "resolved_halts_before_completion": resolved_halts,
            "empty_by_reason": empty,
            "empty_rate": sum(empty.values()) / n if n else 0.0,
            "forced_final_items": sum(1 for r in records if r.get("forced_final")),
            "calls_histogram": dict(sorted(calls_hist.items(), key=lambda kv: int(kv[0]))),
            "items_with_zero_reads": sum(1 for x in reads if x == 0),
            "mean_successful_reads": float(np.mean(reads)) if reads else 0.0,
            "rejected_repeat_share_of_calls": (sum(rejected) / max(1, sum(int(r["model_calls"]) for r in records))),
            "items_with_rejected_repeats": sum(1 for x in rejected if x > 0),
            "instrument_error_items": instrument_items,
            "infra_failure_items": infra_items,
            "transport_retries": sum(int(r.get("transport_retries", 0)) for r in records),
            "http_attempts": sum(int(r.get("http_attempts", 0)) for r in records),
            "logical_calls": sum(int(r["model_calls"]) for r in records),
            "cost_ratio_to_worst_case": {
                "mean": float(np.mean(ratios)) if ratios else None,
                "max": max(ratios) if ratios else None,
                "items_above_1": sum(1 for x in ratios if x > 1.0),
            },
            "usd_per_item": {"mean": float(np.mean(usd)) if usd else None,
                             "median": float(np.median(usd)) if usd else None},
            "tool_quality_X11": tq,
        },
    }


def render(card: dict[str, Any]) -> str:
    info = card["informational"]
    lines = [f"# WP-1b MAIN-mode Review Card - {card['run_label']}\n",
             f"- items: {card['items']} · status: {card['status']} · ledger USD: {card['ledger_usd']}",
             f"- verdict: **{card['verdict']}**",
             f"- AC-14 ledger reconciliation: {json.dumps(card['ledger_reconciliation_AC14'], sort_keys=True)}\n",
             "## BLOCKING (instrument-level only)\n"]
    lines += [f"- {b}" for b in card["blocking"]] or ["- none"]
    lines += ["", "## INFORMATIONAL (agent behaviour = data, never blocking)\n"]
    for k, v in info.items():
        lines.append(f"- {k}: {json.dumps(v, sort_keys=True)}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print("usage: wp1b_main_review_card.py <run_dir>")
        return 2
    run_dir = Path(args[0])
    run_dir = run_dir if run_dir.is_absolute() else _PROJECT_DIR / run_dir
    try:
        card = build_card(run_dir)
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        print(f"[card] ERROR: cannot read run dir {run_dir}: {exc}")
        return 3
    (run_dir / "MAIN_REVIEW_CARD.json").write_text(json.dumps(card, indent=1, sort_keys=True), encoding="utf-8")
    (run_dir / "MAIN_REVIEW_CARD.md").write_text(render(card), encoding="utf-8")
    print(f"[card] {card['verdict']} ({len(card['blocking'])} blocking)")
    for b in card["blocking"]:
        print(f"[card] BLOCKING: {b}")
    return 1 if card["blocking"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
