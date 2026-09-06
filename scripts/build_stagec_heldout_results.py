"""STAGE-C-HELDOUT-CHALLENGE-01 (D053) selection-only results builder.

Reads the persisted ``run_records.jsonl`` (RunRecordData) produced by the
``scientific-stagec-heldout-01`` profile and computes the frozen held-out
measurement contract metrics (``02_MEASUREMENT_AND_FAIRNESS_CONTRACT.md``):

- source-gold normalization (expected_actions -> source paths only)
- precision / recall / F1 / FNR / full-recall / write-set size
- per-scenario x arm and 30-per-arm aggregates
- ImpactPlan descriptive R/P/V/H metrics
- Agent descriptive tool/inspection metrics
- selection-stage efficiency (calls/tokens/latency/OpenRouter cost)
- comparative deltas (ImpactPlan vs Agent): token, model-call, API-cost,
  latency percentage deltas

Metric definitions are REUSED from ``scripts.build_stagec_selection_results``
(no fork). This is a standalone analysis module (not the framework). It never
writes to the raw records and makes no functional-correctness or end-to-end
efficiency claim (selection-stage comparison only).
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_stagec_selection_results import (  # noqa: E402
    STRATEGY_AGENT,
    STRATEGY_IMPACT_PLAN,
    _impact_plan_rates,
    _load_jsonl,
    _mean_median,
    _record_cost,
    compute_run_metrics,
    load_pricing,
)

PROTOCOL = "scientific-stagec-heldout-01"

HELDOUT_SCENARIO_IDS = (
    "todo-heldout-001",
    "todo-heldout-002",
    "todo-heldout-003",
    "todo-heldout-004",
    "todo-heldout-005",
    "todo-heldout-006",
)

ROWS_COUNT = 60


def gold_for_scenario(scenario_id: str, scenarios_dir: Path) -> set[str]:
    """Load the scenario YAML's expected_actions and normalize to source paths.

    Reuses the exact normalization semantics of the Stage-C selection-01 study
    (source files only, migration/test/symbol paths excluded).
    """
    from scripts.build_stagec_selection_results import gold_for_scenario as _gold

    return _gold(scenario_id, scenarios_dir)


def _fmt(v: Any, digits: int = 4) -> str:
    if isinstance(v, float):
        return f"{v:.{digits}f}"
    return str(v)


def _record_selection_evidence(rec: dict[str, Any]) -> dict[str, Any]:
    return rec.get("selection_study") or {}


def _regen_sets(recs: list[dict[str, Any]]) -> list[set[str]]:
    return [
        {p for p, a in (r.get("predicted_actions") or {}).items() if a == "regenerate"}
        for r in recs
    ]


def _pct_delta(base: float, alt: float) -> float:
    if base == 0:
        return 0.0
    return (alt - base) / base * 100.0


def agg_table(
    groups: dict[tuple[str, str], list[dict[str, Any]]],
    gold_map: dict[str, set[str]],
    pricing: dict[str, float],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for (scenario_id, strategy_id), recs in sorted(groups.items()):
        gold = gold_map.get(scenario_id, set())
        n = len(recs)
        valid = [r for r in recs if r.get("status") == "succeeded"]
        metrics = [compute_run_metrics(s, gold) for s in _regen_sets(recs)]
        full_recall = sum(1 for m in metrics if m["full_recall"])
        write_sets = [m["write_set_size"] for m in metrics]
        calls = [int(r.get("total_workflow_model_calls", 0)) for r in recs]
        tokens = [int((r.get("token_usage") or {}).get("total", 0)) for r in recs]
        latency = [float(r.get("total_workflow_duration_seconds", 0.0)) for r in recs]

        row: dict[str, Any] = {
            "scenario_id": scenario_id,
            "strategy_id": strategy_id,
            "n": n,
            "valid_finals": len(valid),
            "full_recall_count": full_recall,
            "precision_mean": _mean_median([m["precision"] for m in metrics])[0],
            "precision_median": _mean_median([m["precision"] for m in metrics])[1],
            "recall_mean": _mean_median([m["recall"] for m in metrics])[0],
            "recall_median": _mean_median([m["recall"] for m in metrics])[1],
            "f1_mean": _mean_median([m["f1"] for m in metrics])[0],
            "f1_median": _mean_median([m["f1"] for m in metrics])[1],
            "fnr_mean": _mean_median([m["fnr"] for m in metrics])[0],
            "fnr_median": _mean_median([m["fnr"] for m in metrics])[1],
            "write_set_size_mean": _mean_median(write_sets)[0] if write_sets else 0.0,
            "write_set_size_median": _mean_median(write_sets)[1] if write_sets else 0.0,
            "model_calls": sum(calls),
            "tokens": sum(tokens),
            "latency_seconds": sum(latency),
            "api_cost_usd": sum(_record_cost(r, pricing) for r in recs),
        }

        if strategy_id == STRATEGY_AGENT:
            finalized = sum(1 for r in recs if r.get("status") == "succeeded")
            tool_calls = [int(r.get("selection_tool_calls", 0)) for r in recs]
            control_calls = [int(r.get("selection_model_calls", 0)) for r in recs]
            inspected = [int(r.get("selection_inspected_file_count", 0)) for r in recs]
            row["agent_finalization_rate"] = (finalized / n) if n else 0.0
            row["agent_tool_calls"] = sum(tool_calls)
            row["agent_control_calls"] = sum(control_calls)
            row["agent_inspected_files"] = sum(inspected)
        if strategy_id == STRATEGY_IMPACT_PLAN:
            rates = [_impact_plan_rates(r) for r in recs]
            row["R"] = sum(x["R"] for x in rates)
            row["P"] = sum(x["P"] for x in rates)
            row["V"] = sum(x["V"] for x in rates)
            row["H"] = sum(x["H"] for x in rates)
            row["human_review_rate_mean"] = _mean_median([x["human_review_rate"] for x in rates])[0]
            row["validate_only_rate_mean"] = _mean_median([x["validate_only_rate"] for x in rates])[0]
        rows.append(row)
    return rows


def _arm_agg(
    all_recs: list[dict[str, Any]],
    arm_label: str,
    gold_map: dict[str, set[str]],
    pricing: dict[str, float],
) -> dict[str, Any]:
    n = len(all_recs)
    valid = [r for r in all_recs if r.get("status") == "succeeded"]
    per_run: list[dict[str, Any]] = []
    for r in all_recs:
        sid = r.get("scenario_id", "")
        gold = gold_map.get(sid, set())
        regen = {p for p, a in (r.get("predicted_actions") or {}).items() if a == "regenerate"}
        per_run.append(compute_run_metrics(regen, gold))
    full_recall = sum(1 for m in per_run if m["full_recall"])
    write_sets = [m["write_set_size"] for m in per_run]
    calls = [int(r.get("total_workflow_model_calls", 0)) for r in all_recs]
    tokens = [int((r.get("token_usage") or {}).get("total", 0)) for r in all_recs]
    latency = [float(r.get("total_workflow_duration_seconds", 0.0)) for r in all_recs]

    row: dict[str, Any] = {
        "scenario_id": "__all__",
        "strategy_id": arm_label,
        "n": n,
        "valid_finals": len(valid),
        "full_recall_count": full_recall,
        "precision_mean": _mean_median([m["precision"] for m in per_run])[0],
        "precision_median": _mean_median([m["precision"] for m in per_run])[1],
        "recall_mean": _mean_median([m["recall"] for m in per_run])[0],
        "recall_median": _mean_median([m["recall"] for m in per_run])[1],
        "f1_mean": _mean_median([m["f1"] for m in per_run])[0],
        "f1_median": _mean_median([m["f1"] for m in per_run])[1],
        "fnr_mean": _mean_median([m["fnr"] for m in per_run])[0],
        "fnr_median": _mean_median([m["fnr"] for m in per_run])[1],
        "write_set_size_mean": _mean_median(write_sets)[0] if write_sets else 0.0,
        "write_set_size_median": _mean_median(write_sets)[1] if write_sets else 0.0,
        "model_calls": sum(calls),
        "tokens": sum(tokens),
        "latency_seconds": sum(latency),
        "api_cost_usd": sum(_record_cost(r, pricing) for r in all_recs),
    }
    if arm_label == STRATEGY_AGENT:
        tool_calls = [int(r.get("selection_tool_calls", 0)) for r in all_recs]
        control_calls = [int(r.get("selection_model_calls", 0)) for r in all_recs]
        inspected = [int(r.get("selection_inspected_file_count", 0)) for r in all_recs]
        row["agent_finalization_rate"] = (len(valid) / n) if n else 0.0
        row["agent_tool_calls"] = sum(tool_calls)
        row["agent_control_calls"] = sum(control_calls)
        row["agent_inspected_files"] = sum(inspected)
    if arm_label == STRATEGY_IMPACT_PLAN:
        rates = [_impact_plan_rates(r) for r in all_recs]
        row["R"] = sum(x["R"] for x in rates)
        row["P"] = sum(x["P"] for x in rates)
        row["V"] = sum(x["V"] for x in rates)
        row["H"] = sum(x["H"] for x in rates)
        row["human_review_rate_mean"] = _mean_median([x["human_review_rate"] for x in rates])[0]
        row["validate_only_rate_mean"] = _mean_median([x["validate_only_rate"] for x in rates])[0]
    return row


def build(
    runs_dir: Path,
    scenarios_dir: Path,
    reports_dir: Path,
) -> dict[str, Any]:
    from benchmark.checkpoint.persistence import RunRecordData

    records = [RunRecordData(**r) for r in _load_jsonl(runs_dir / "run_records.jsonl")]
    rec_dicts: list[dict[str, Any]] = [dict(vars(r)) for r in records]

    gold_map = {sid: gold_for_scenario(sid, scenarios_dir) for sid in HELDOUT_SCENARIO_IDS}
    pricing = load_pricing(reports_dir)

    if not rec_dicts:
        return {
            "protocol": PROTOCOL,
            "records": 0,
            "gold": {k: sorted(v) for k, v in gold_map.items()},
            "rows": [],
            "agents": [],
            "impact_plans": [],
            "cost_usd": 0.0,
            "deltas": {},
        }

    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for r in rec_dicts:
        groups.setdefault((r.get("scenario_id", ""), r.get("strategy_id", "")), []).append(r)

    rows = agg_table(groups, gold_map, pricing)

    agent_recs = [r for (sid, arm), recs in groups.items() if arm == STRATEGY_AGENT for r in recs]
    impact_recs = [r for (sid, arm), recs in groups.items() if arm == STRATEGY_IMPACT_PLAN for r in recs]

    agents = [_arm_agg(agent_recs, STRATEGY_AGENT, gold_map, pricing)]
    impact_plans = [_arm_agg(impact_recs, STRATEGY_IMPACT_PLAN, gold_map, pricing)]

    def _arm_totals(recs: list[dict[str, Any]]) -> dict[str, float]:
        tok = sum(int((r.get("token_usage") or {}).get("total", 0)) for r in recs)
        calls = sum(int(r.get("total_workflow_model_calls", 0)) for r in recs)
        cost = sum(_record_cost(r, pricing) for r in recs)
        lat = sum(float(r.get("total_workflow_duration_seconds", 0.0)) for r in recs)
        return {"tokens": float(tok), "calls": float(calls), "cost": cost, "latency": lat}

    ag = _arm_totals(agent_recs)
    ip = _arm_totals(impact_recs)
    deltas = {
        "impactplan_token_delta_pct": _pct_delta(ag["tokens"], ip["tokens"]),
        "impactplan_call_delta_pct": _pct_delta(ag["calls"], ip["calls"]),
        "impactplan_cost_delta_pct": _pct_delta(ag["cost"], ip["cost"]),
        "impactplan_latency_delta_pct": _pct_delta(ag["latency"], ip["latency"]),
    }

    cost_usd = sum(_record_cost(r, pricing) for r in rec_dicts)
    return {
        "protocol": PROTOCOL,
        "records": len(rec_dicts),
        "gold": {k: sorted(v) for k, v in gold_map.items()},
        "rows": rows,
        "agents": agents,
        "impact_plans": impact_plans,
        "cost_usd": cost_usd,
        "deltas": deltas,
    }


def write_reports(out: dict[str, Any], reports_dir: Path) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    csv_path = reports_dir / "STAGEC_HELDOUT_01_RESULTS.csv"
    md_path = reports_dir / "STAGEC_HELDOUT_01_RESULTS.md"
    dec_path = reports_dir / "STAGEC_HELDOUT_01_DECISION.md"

    all_rows = list(out["rows"]) + out["agents"] + out["impact_plans"]
    fields = ["scenario_id", "strategy_id"]
    seen: list[str] = []
    for row in all_rows:
        for k in row:
            if k not in seen:
                seen.append(k)
    for fe in fields:
        if fe not in seen:
            seen.insert(0, fe)

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=seen)
        writer.writeheader()
        for row in all_rows:
            writer.writerow({k: _fmt(v) for k, v in row.items()})

    lines = [
        "# STAGE-C-HELDOUT-CHALLENGE-01 results",
        "",
        "- Label: FOLLOW-UP HELD-OUT COMPONENT STUDY",
        f"- Protocol: {PROTOCOL}",
        f"- Records: {out['records']}/{ROWS_COUNT}",
        f"- Exact API cost: ${out['cost_usd']:.6f}",
        "",
        "Selection-stage efficiency comparison only. No functional-correctness or",
        "end-to-end efficiency claim is made.",
        "",
    ]
    for row in all_rows:
        lines.append(f"## {row.get('scenario_id','')} / {row.get('strategy_id','')}")
        for k, v in row.items():
            lines.append(f"- {k}: {_fmt(v)}")
        lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    d = out["deltas"]
    dec_lines = [
        "# STAGE-C-HELDOUT-CHALLENGE-01 DECISION (FOLLOW-UP HELD-OUT COMPONENT STUDY)",
        "",
        f"Records: {out['records']}/{ROWS_COUNT} attempted.",
        f"Cost: ${out['cost_usd']:.6f}.",
        "",
        "Comparative deltas (ImpactPlan vs Agent, negative = fewer/cheaper):",
        f"- ImpactPlan token delta: {d['impactplan_token_delta_pct']:.2f}%",
        f"- ImpactPlan model-call delta: {d['impactplan_call_delta_pct']:.2f}%",
        f"- ImpactPlan API-cost delta: {d['impactplan_cost_delta_pct']:.2f}%",
        f"- ImpactPlan latency delta: {d['impactplan_latency_delta_pct']:.2f}%",
        "",
        "Selection accuracy is reported per scenario and per arm in the CSV/MD tables.",
        "No significance testing at n=5/scenario/arm. No end-to-end claim.",
        "",
        "NEXT_ACTION=archive evidence, conclude TODO_SELECTION_SATURATED, evidence tag",
        "`stagec-heldout-selection-01`, LIGHT whitelist export; no executor change.",
        "",
    ]
    dec_path.write_text("\n".join(dec_lines), encoding="utf-8")


def main() -> int:
    runs_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("reports/scientific_stagec_heldout_01")
    scenarios_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("benchmark_data/scenarios")
    reports_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("reports")
    out = build(runs_dir, scenarios_dir, reports_dir)
    write_reports(out, reports_dir)
    print("STAGEC_HELDOUT_01_RESULTS_READY")
    print(f"records={out['records']}")
    print(f"cost_usd={out['cost_usd']:.6f}")
    print(f"rows={len(out['rows'])}")
    print(f"wrote {reports_dir / 'STAGEC_HELDOUT_01_RESULTS.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
