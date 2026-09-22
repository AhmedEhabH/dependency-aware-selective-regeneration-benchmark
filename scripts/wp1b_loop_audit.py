#!/usr/bin/env python3
"""WP-1b G12 - agent context-loop audit (ZERO API).

From a wp1b_call_sidecar.jsonl it computes, PER TASK:
  - total calls
  - useful tool calls (tool_ok)
  - rejected repeats (repeated identical tool request)
  - the longest run of consecutive rejected repeats
  - prompt-token growth between consecutive rejected calls (the fixed
    rejection sentence is the only appended text, so consecutive rejected
    calls show the per-rejection prompt growth)
  - spend (USD) on rejected calls

Classification reuses scripts/wp1b_sidecar_tool_audit.classify_record so the
audit and the gate share one source of truth.

Usage:
  python scripts/wp1b_loop_audit.py <calibration_dir> [--out <audit.json>]

Output:
  <calibration_dir>/wp1b_loop_audit.json   (or --out)

Exit codes:
  0  audit written
  2  input error
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))
sys.path.insert(0, str(_PROJECT_DIR / "scripts"))

from wp1b_sidecar_tool_audit import classify_record  # noqa: E402


def _load_sidecar(cal_dir: Path) -> list[dict[str, Any]]:
    sidecar_path = cal_dir / "wp1b_call_sidecar.jsonl"
    if not sidecar_path.is_file():
        raise FileNotFoundError(f"sidecar not found: {sidecar_path}")
    records: list[dict[str, Any]] = []
    for line in sidecar_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    if not records:
        raise ValueError(f"empty sidecar: {sidecar_path}")
    return records


def audit_sidecar(records: list[dict[str, Any]]) -> dict[str, Any]:
    per_task: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for rec in records:
        tid = rec.get("task_id", "")
        if tid not in per_task:
            order.append(tid)
            per_task[tid] = {
                "task_id": tid,
                "calls": 0,
                "useful_tool_calls": 0,
                "rejected_repeat": 0,
                "final": 0,
                "longest_rejection_run": 0,
                "current_rejection_run": 0,
                "rejected_spend_usd": 0.0,
                "rejected_prompt_growth_pairs": [],
                "last_rejected_prompt": None,
            }
        agg = per_task[tid]
        agg["calls"] += 1
        cls = classify_record(rec)
        prompt_tokens = int(rec.get("prompt_tokens", 0) or 0)
        if cls == "tool_ok":
            agg["useful_tool_calls"] += 1
            agg["current_rejection_run"] = 0
        elif cls == "rejected_repeat":
            agg["rejected_repeat"] += 1
            agg["rejected_spend_usd"] += float(rec.get("usd", 0.0) or 0.0)
            agg["current_rejection_run"] += 1
            agg["longest_rejection_run"] = max(
                agg["longest_rejection_run"], agg["current_rejection_run"]
            )
            if agg["last_rejected_prompt"] is not None:
                agg["rejected_prompt_growth_pairs"].append(
                    {
                        "from_prompt_tokens": agg["last_rejected_prompt"],
                        "to_prompt_tokens": prompt_tokens,
                        "delta_tokens": prompt_tokens - agg["last_rejected_prompt"],
                    }
                )
            agg["last_rejected_prompt"] = prompt_tokens
        else:
            # final / tool_error reset the run
            agg["current_rejection_run"] = 0
            if cls == "final":
                agg["final"] += 1

    per_task_list: list[dict[str, Any]] = []
    for tid in order:
        agg = per_task[tid]
        growth = agg["rejected_prompt_growth_pairs"]
        deltas = [g["delta_tokens"] for g in growth]
        per_task_list.append({
            "task_id": tid,
            "calls": agg["calls"],
            "useful_tool_calls": agg["useful_tool_calls"],
            "rejected_repeat": agg["rejected_repeat"],
            "final": agg["final"],
            "longest_rejection_run": agg["longest_rejection_run"],
            "rejected_spend_usd": round(agg["rejected_spend_usd"], 6),
            "rejected_prompt_growth_pairs": growth,
            "rejected_prompt_growth_deltas": deltas,
            "uniform_rejected_prompt_growth_tokens": (
                deltas[0] if len(set(deltas)) == 1 and deltas else None
            ),
        })

    totals = {
        "calls": sum(a["calls"] for a in per_task_list),
        "useful_tool_calls": sum(a["useful_tool_calls"] for a in per_task_list),
        "rejected_repeat": sum(a["rejected_repeat"] for a in per_task_list),
        "final": sum(a["final"] for a in per_task_list),
        "rejected_spend_usd": round(
            sum(a["rejected_spend_usd"] for a in per_task_list), 6
        ),
    }
    growth_deltas: list[int] = []
    for a in per_task_list:
        growth_deltas.extend(a["rejected_prompt_growth_deltas"])
    totals["uniform_rejected_prompt_growth_tokens"] = (
        growth_deltas[0] if len(set(growth_deltas)) == 1 and growth_deltas else None
    )
    return {
        "artifact": "wp1b_loop_audit",
        "per_task": per_task_list,
        "aggregate": totals,
    }


def _print_table(audit: dict[str, Any]) -> None:
    header = f"{'task':<26} {'calls':>5} {'useful':>6} {'reject':>7} {'run':>4} {'rej_spend$':>9}"
    print(header)
    print("-" * len(header))
    for ta in audit["per_task"]:
        print(
            f"{ta['task_id']:<26} {ta['calls']:>5} {ta['useful_tool_calls']:>6} "
            f"{ta['rejected_repeat']:>7} {ta['longest_rejection_run']:>4} "
            f"{ta['rejected_spend_usd']:>9}"
        )
    agg = audit["aggregate"]
    print("-" * len(header))
    print(
        f"{'Total':<26} {agg['calls']:>5} {agg['useful_tool_calls']:>6} "
        f"{agg['rejected_repeat']:>7} {'--':>4} {agg['rejected_spend_usd']:>9}"
    )
    print(
        f"[audit] uniform_rejected_prompt_growth_tokens="
        f"{agg['uniform_rejected_prompt_growth_tokens']}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("calibration_dir", help="calibration results directory")
    parser.add_argument("--out", help="output audit path (default <dir>/wp1b_loop_audit.json)")
    args = parser.parse_args(argv)

    cal_dir = Path(args.calibration_dir)
    try:
        records = _load_sidecar(cal_dir)
    except (FileNotFoundError, ValueError) as exc:
        print(f"[audit] ERROR: {exc}")
        return 2

    audit = audit_sidecar(records)
    out = Path(args.out) if args.out else cal_dir / "wp1b_loop_audit.json"
    out.write_text(json.dumps(audit, indent=1), encoding="utf-8")
    _print_table(audit)
    print(f"[audit] wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
