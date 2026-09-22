#!/usr/bin/env python3
"""WP-1b zero-API dry-run acceptance check (label-free).

Reads a ``--kind dry_run`` output directory and verifies, before the first paid
MAIN_297 call:
  D1 all 297 items completed, 0 crash/halt, 0 infrastructure failures;
  D2 every item produced a non-empty stub prediction (i.e. a non-empty universe
     and a readable prompt);
  D3 call-1 prompt size matches the budget-v2 base prompt (+ the G12 counter
     line) within 500 characters on every task (the budget model still describes
     the prompt that will be sent);
  D4 per-item wall time (materialization + stub) and a projected paid runtime;
  D5 a projected paid cost range = sum(budget-v2 worst case) x the Calibration-3c
     cost-ratio range [0.331, 0.645] (descriptive; the ceiling guard is separate).

Usage: python scripts/wp1b_dry_run_check.py research/wp1b/dry-run-zero-api-2026-09-22
Exit: 0 all checks pass | 1 a check failed (STOP, report) | 2 input error
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.wp1b import main_runner as mr  # noqa: E402

BUDGET_V2 = _PROJECT_DIR / "research" / "wp1b" / "wp1b_budget_model_v2.json"
CAL3C_RATIO_RANGE = (0.331, 0.645)
PROMPT_TOLERANCE_CHARS = 500
PAID_SECONDS_PER_CALL_EST = (1.0, 2.6)  # Calibration-3c observed latency range per call
PAID_CALLS_PER_TASK_EST = (4, 8)


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print("usage: wp1b_dry_run_check.py <dry_run_dir>")
        return 2
    run_dir = Path(args[0])
    run_dir = run_dir if run_dir.is_absolute() else _PROJECT_DIR / run_dir
    records, bad = mr.read_jsonl_tolerant(run_dir / mr.RECORDS_FILE)
    ledger, _ = mr.read_jsonl_tolerant(run_dir / mr.LEDGER_FILE)
    state = json.loads((run_dir / mr.STATE_FILE).read_text(encoding="utf-8"))
    budget = json.loads(BUDGET_V2.read_text(encoding="utf-8"))["worst_case_per_task"]
    checks: dict[str, object] = {}
    failures: list[str] = []

    n_total = int(state.get("n_items", 0))
    infra = [r["work_key"] for r in records if r.get("infra_failure")]
    checks["D1_complete"] = {"records": len(records), "expected": n_total, "torn_lines": len(bad),
                             "halt_report_present": (run_dir / mr.HALT_FILE).exists(), "infra": len(infra)}
    if len(records) != n_total or bad or (run_dir / mr.HALT_FILE).exists() or infra or n_total != 297:
        failures.append("D1")

    empty = [r["work_key"] for r in records if r.get("prediction_empty")]
    checks["D2_non_empty_stub_predictions"] = {"empty": len(empty), "first": empty[:5]}
    if empty:
        failures.append("D2")

    first_call = {}
    for e in ledger:
        if e.get("kind") == "call" and int(e.get("call_index", 0)) == 1:
            first_call[str(e["task_id"])] = int(e["prompt_tokens"])
    diffs = []
    for r in records:
        tid = str(r["task_id"])
        if tid in first_call and tid in budget:
            approx_chars = 4 * first_call[tid]
            diffs.append((abs(approx_chars - float(budget[tid]["base_prompt_chars"])), tid,
                          approx_chars - float(budget[tid]["base_prompt_chars"])))
    diffs.sort(reverse=True)
    worst = diffs[0] if diffs else (0.0, "", 0.0)
    checks["D3_prompt_vs_budget_v2"] = {
        "tasks_compared": len(diffs),
        "max_abs_diff_chars": round(worst[0], 1),
        "worst_task": worst[1],
        "median_signed_diff_chars": round(sorted(d[2] for d in diffs)[len(diffs) // 2], 1) if diffs else None,
        "note": "stub token count = len(prompt)//4, so chars are approximate (+-3); the G12 counter adds ~70 chars",
    }
    if not diffs or worst[0] > PROMPT_TOLERANCE_CHARS:
        failures.append("D3")

    walls = sorted(float(r.get("wall_seconds", 0.0)) for r in records)
    per_item_overhead = walls[len(walls) // 2] if walls else 0.0
    lo = len(records) * (per_item_overhead + PAID_CALLS_PER_TASK_EST[0] * PAID_SECONDS_PER_CALL_EST[0])
    hi = len(records) * (per_item_overhead + PAID_CALLS_PER_TASK_EST[1] * PAID_SECONDS_PER_CALL_EST[1] + 10.0)
    checks["D4_runtime"] = {"median_item_wall_seconds_dry": round(per_item_overhead, 2),
                            "max_item_wall_seconds_dry": round(walls[-1], 2) if walls else None,
                            "projected_paid_hours_range": [round(lo / 3600, 2), round(hi / 3600, 2)]}

    ids = [str(r["task_id"]) for r in records]
    worst_sum = sum(float(budget[t]["worst_case_usd"]) for t in ids if t in budget)
    checks["D5_projected_paid_cost_usd"] = {
        "budget_v2_worst_case_sum": round(worst_sum, 4),
        "projected_range_from_cal3c_ratios": [round(worst_sum * CAL3C_RATIO_RANGE[0], 2),
                                              round(worst_sum * CAL3C_RATIO_RANGE[1], 2)],
        "frozen_ceiling": 21.50,
    }
    verdict = "DRY_RUN_PASS" if not failures else f"DRY_RUN_FAIL({','.join(failures)})"
    out = {"artifact": "wp1b_dry_run_check", "verdict": verdict, "checks": checks}
    (run_dir / "dry_run_check.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"[dry-run] {verdict}")
    print(json.dumps(checks, indent=1))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
