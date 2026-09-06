"""STAGE-C LATENCY DECOMPOSITION — deterministic analysis.

Consumes both Stage-C selection-only raw record files:

- ``reports/scientific_stagec_selection_01/run_records.jsonl`` (smoke study)
- ``reports/scientific_stagec_heldout_01/run_records.jsonl`` (held-out study)

and computes per study/arm:

- n
- total selection duration
- mean / median / p90 / max run duration
- total model calls
- total tool calls
- total tool duration
- total prompt/completion/total tokens
- CALL-EQUIVALENT duration = total selection duration / total model calls
  (explicitly NOT provider per-call latency)
- top-3 run-duration outliers with run IDs

The script never modifies the raw records.
"""

from __future__ import annotations

import csv
import json
import statistics
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
SMOKE_RUNS = ROOT / "reports" / "scientific_stagec_selection_01" / "run_records.jsonl"
HELDOUT_RUNS = ROOT / "reports" / "scientific_stagec_heldout_01" / "run_records.jsonl"
DEFAULT_OUT_CSV = ROOT / "reports" / "STAGEC_LATENCY_DECOMPOSITION.csv"
DEFAULT_OUT_MD = ROOT / "reports" / "STAGEC_LATENCY_DECOMPOSITION.md"

AGENT = "iterative_repository_agent"
IMPACT_PLAN = "impact_plan"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not path.is_file():
        return out
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def p90(values: list[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = max(0, min(len(s) - 1, round(0.9 * (len(s) - 1))))
    return s[k]


def _outliers(recs: list[dict[str, Any]], top: int = 3) -> list[tuple[str, float]]:
    ranked = sorted(
        ((r.get("run_id", ""), float(r.get("total_workflow_duration_seconds", 0.0))) for r in recs),
        key=lambda x: x[1],
        reverse=True,
    )
    return ranked[:top]


def aggregate(recs: list[dict[str, Any]]) -> dict[str, Any]:
    durations = [float(r.get("total_workflow_duration_seconds", 0.0)) for r in recs]
    calls = [int(r.get("total_workflow_model_calls", 0)) for r in recs]
    tool_calls = [int(r.get("selection_tool_calls", 0)) for r in recs]
    tool_dur = [float(r.get("selection_tool_duration_seconds", 0.0)) for r in recs]
    tokens = [(r.get("token_usage") or {}) for r in recs]
    prompt = sum(int(t.get("prompt", 0)) for t in tokens)
    completion = sum(int(t.get("completion", 0)) for t in tokens)
    total_tokens = sum(int(t.get("total", 0)) for t in tokens)
    total_dur = sum(durations)
    total_calls = sum(calls)
    return {
        "n": len(recs),
        "total_selection_duration": round(total_dur, 6),
        "mean_run_duration": round(statistics.mean(durations), 6) if durations else 0.0,
        "median_run_duration": round(statistics.median(durations), 6) if durations else 0.0,
        "p90_run_duration": round(p90(durations), 6),
        "max_run_duration": round(max(durations, default=0.0), 6),
        "total_model_calls": total_calls,
        "total_tool_calls": sum(tool_calls),
        "total_tool_duration": round(sum(tool_dur), 6),
        "total_prompt_tokens": prompt,
        "total_completion_tokens": completion,
        "total_tokens": total_tokens,
        "call_equivalent_duration": round(total_dur / total_calls, 6) if total_calls else 0.0,
        "top3_outlier_run_ids": [
            {"run_id": rid, "duration_seconds": d} for rid, d in _outliers(recs)
        ],
    }


def build(smoke_path: Path, heldout_path: Path) -> list[dict[str, Any]]:
    smoke = load_jsonl(smoke_path)
    heldout = load_jsonl(heldout_path)
    rows: list[dict[str, Any]] = []
    for study_name, recs in (("smoke", smoke), ("heldout", heldout)):
        for arm in (AGENT, IMPACT_PLAN):
            arm_recs = [r for r in recs if r.get("strategy_id") == arm]
            agg = aggregate(arm_recs)
            agg = {"study": study_name, "arm": arm, **agg}
            rows.append(agg)
    return rows


def _fmt(v: Any) -> str:
    if isinstance(v, float):
        return f"{v:.6f}"
    if isinstance(v, list):
        return "; ".join(f"{x['run_id']}={x['duration_seconds']:.3f}s" for x in v)
    return str(v)


def write_reports(rows: list[dict[str, Any]], csv_path: Path, md_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["study", "arm", "n", "total_selection_duration", "mean_run_duration",
              "median_run_duration", "p90_run_duration", "max_run_duration",
              "total_model_calls", "total_tool_calls", "total_tool_duration",
              "total_prompt_tokens", "total_completion_tokens", "total_tokens",
              "call_equivalent_duration", "top3_outlier_run_ids"]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: _fmt(r.get(k)) for k in fields})

    lines = [
        "# STAGE-C LATENCY DECOMPOSITION",
        "",
        "Per study/arm selection-stage latency metrics. `call_equivalent_duration` is "
        "`total_selection_duration / total_model_calls` and is a per-run WORKLOAD label, "
        "NOT provider per-call latency.",
        "",
    ]
    for r in rows:
        lines.append(f"## {r['study']} / {r['arm']}")
        for k in fields:
            if k in ("study", "arm"):
                continue
            lines.append(f"- {k}: {_fmt(r.get(k))}")
        lines.append("")
    lines.append("## Reporting rule")
    lines.append("")
    lines.append("Always report BOTH the total-latency delta AND the median-run latency.")
    lines.append("The held-out `-51.81%` total-latency delta is NOT a stable algorithmic ")
    lines.append("speedup: two Agent held-out outliers materially affect the total.")
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    smoke_path = Path(sys.argv[1]) if len(sys.argv) > 1 else SMOKE_RUNS
    heldout_path = Path(sys.argv[2]) if len(sys.argv) > 2 else HELDOUT_RUNS
    csv_path = Path(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_OUT_CSV
    md_path = Path(sys.argv[4]) if len(sys.argv) > 4 else DEFAULT_OUT_MD
    rows = build(smoke_path, heldout_path)
    write_reports(rows, csv_path, md_path)
    print("STAGEC_LATENCY_DECOMPOSITION_READY")
    for r in rows:
        print(f"{r['study']}/{r['arm']}: n={r['n']} total={r['total_selection_duration']}s "
              f"median={r['median_run_duration']}s p90={r['p90_run_duration']}s "
              f"calls={r['total_model_calls']} call_eq={r['call_equivalent_duration']}s "
              f"tokens={r['total_tokens']}")
    print(f"wrote {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
