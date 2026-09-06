"""STAGE-C-SELECTION-01 (D052) selection-only results builder.

Reads the persisted ``run_records.jsonl`` (RunRecordData) produced by the
``scientific-stagec-selection-01`` profile and computes the frozen measurement
contract metrics (``01_MEASUREMENT_CONTRACT.md``):

- source-gold normalization (expected_actions -> source paths only)
- precision / recall / F1 / FNR / full-recall / write-set size
- per-scenario x arm and 15-per-arm aggregates
- ImpactPlan descriptive R/P/V/H metrics
- Agent descriptive tool/inspection metrics
- selection-stage efficiency (calls/tokens/latency/OpenRouter cost)

This is a standalone analysis module (not the framework). It never writes to
the raw records and makes no scientific claim about end-to-end correctness.
"""

from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path
from typing import Any

from benchmark.checkpoint.persistence import RunRecordData

FIVE_FILE_UNIVERSE = frozenset(
    {
        "todo/models.py",
        "todo/serializers.py",
        "todo/views.py",
        "todo/permissions.py",
        "todo/urls.py",
    }
)

STRATEGY_AGENT = "iterative_repository_agent"
STRATEGY_IMPACT_PLAN = "impact_plan"
PROTOCOL = "scientific-stagec-selection-01"

_FREEZE_PRICING_DEFAULTS = {
    "prompt_per_token_usd": 0.0000003,
    "completion_per_token_usd": 0.000001,
}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not path.is_file():
        return out
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def normalize_gold_actions(scenario) -> set[str]:
    """Normalize ``expected_actions`` to source-file paths ONLY.

    Migration directories/artifacts and evaluator/test files are NOT part of
    source-selection recall. Symbol markers (e.g. ``path#symbol``) are stripped.
    Only files inside the five-file source universe are kept.
    """
    gold: set[str] = set()
    for ref, action in getattr(scenario, "expected_actions", ()) or ():
        if action != "regenerate" and action not in ("regenerate",):
            continue
        path = str(getattr(ref, "path", ""))
        if not path:
            continue
        clean = path.split("#", 1)[0]
        segs = clean.split("/")
        if "migrations" in segs or "tests" in segs:
            continue
        if clean.endswith("/"):
            continue
        if clean in FIVE_FILE_UNIVERSE:
            gold.add(clean)
    return gold


def gold_for_scenario(scenario_id: str, scenarios_dir: Path) -> set[str]:
    """Load the scenario YAML's expected_actions and normalize to source paths."""
    import yaml

    p = scenarios_dir / f"{scenario_id}.yaml"
    if not p.is_file():
        return set()
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    actions = data.get("expected_actions") or {}
    gold: set[str] = set()
    for path, action in actions.items():
        if action not in ("modify", "create", "regenerate"):
            continue
        clean = path.split("#", 1)[0]
        segs = clean.split("/")
        if "migrations" in segs or "tests" in segs:
            continue
        if clean.endswith("/"):
            continue
        if clean in FIVE_FILE_UNIVERSE:
            gold.add(clean)
    return gold


def compute_run_metrics(predicted_regenerate: set[str], gold: set[str]) -> dict[str, float | bool | int]:
    tp = len(predicted_regenerate & gold)
    fn = len(gold - predicted_regenerate)
    predicted_size = len(predicted_regenerate)
    precision = tp / predicted_size if predicted_size else 0.0
    recall = tp / len(gold) if gold else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    fnr = fn / len(gold) if gold else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "fnr": fnr,
        "full_recall": bool(gold and recall >= 1.0),
        "write_set_size": predicted_size,
    }


def _mean_median(values: list[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    return sum(values) / len(values), float(statistics.median(values))


def _fmt(v: Any, digits: int = 4) -> str:
    if isinstance(v, float):
        return f"{v:.{digits}f}"
    return str(v)


def load_pricing(reports_dir: Path) -> dict[str, float]:
    freeze = reports_dir / "SCIENTIFIC_MICROSTUDY_MODEL_FREEZE.json"
    if freeze.is_file():
        data = json.loads(freeze.read_text(encoding="utf-8"))
        pricing = data.get("pricing", {})
        default_prompt = _FREEZE_PRICING_DEFAULTS["prompt_per_token_usd"]
        default_completion = _FREEZE_PRICING_DEFAULTS["completion_per_token_usd"]
        return {
            "prompt_per_token_usd": float(
                pricing.get("prompt_per_token_usd", default_prompt)
            ),
            "completion_per_token_usd": float(
                pricing.get("completion_per_token_usd", default_completion)
            ),
        }
    return dict(_FREEZE_PRICING_DEFAULTS)


def _record_cost(rec: dict[str, Any], pricing: dict[str, float]) -> float:
    tok = rec.get("token_usage") or {}
    prompt = int(tok.get("prompt", 0))
    completion = int(tok.get("completion", 0))
    return prompt * pricing["prompt_per_token_usd"] + completion * pricing["completion_per_token_usd"]


def _impact_plan_rates(rec: dict[str, Any]) -> dict[str, Any]:
    plan = rec.get("impact_plan") or {}
    plan_body = plan.get("plan") if isinstance(plan, dict) else None
    if not isinstance(plan_body, dict):
        return {
            "R": 0, "P": 0, "V": 0, "H": 0,
            "human_review_rate": 0.0, "validate_only_rate": 0.0,
        }
    decisions = plan_body.get("decisions", [])
    counts: dict[str, int] = {"regenerate": 0, "preserve": 0, "validate_only": 0, "human_review": 0}
    for d in decisions:
        action = d.get("action", "") if isinstance(d, dict) else ""
        if action in counts:
            counts[action] += 1
    total = sum(counts.values())
    return {
        "R": counts["regenerate"],
        "P": counts["preserve"],
        "V": counts["validate_only"],
        "H": counts["human_review"],
        "human_review_rate": (counts["human_review"] / total) if total else 0.0,
        "validate_only_rate": (counts["validate_only"] / total) if total else 0.0,
    }


def _selection_evidence(rec: dict[str, Any]) -> dict[str, Any]:
    return rec.get("selection_study") or {}


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
        metrics = [compute_run_metrics(set((r.get("predicted_actions") or {}).keys()), gold) for r in recs]
        regen_sets = [
            {p for p, a in (r.get("predicted_actions") or {}).items() if a == "regenerate"}
            for r in recs
        ]
        full_recall = sum(1 for r in recs if compute_run_metrics(
            {p for p, a in (r.get("predicted_actions") or {}).items() if a == "regenerate"},
            gold,
        )["full_recall"])
        write_sets = [len(s) for s in regen_sets]
        calls = [int(r.get("total_workflow_model_calls", 0)) for r in recs]
        tokens = [int((r.get("token_usage") or {}).get("total", 0)) for r in recs]
        latency = [float(r.get("total_workflow_duration_seconds", 0.0)) for r in recs]
        cost = sum(_record_cost(r, pricing) for r in recs)

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
            "api_cost_usd": cost,
        }

        if strategy_id == STRATEGY_AGENT:
            finalized = sum(1 for r in recs if r.get("status") == "succeeded")
            tool_calls = [int((r.get("selection_study") or {}).get("agent_tool_calls", 0)) for r in recs]
            row["agent_finalization_rate"] = (finalized / n) if n else 0.0
            row["agent_tool_calls"] = sum(tool_calls)
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


def build(
    runs_dir: Path,
    scenarios_dir: Path,
    reports_dir: Path,
) -> dict[str, Any]:
    records = [RunRecordData(**r) for r in _load_jsonl(runs_dir / "run_records.jsonl")]
    recs = [vars(r) for r in records]
    # Backward-compatible access to dict-of-dicts from RunRecordData.
    rec_dicts: list[dict[str, Any]] = []
    for r in recs:
        d = dict(r)
        study = d.get("selection_study")
        if isinstance(study, RunRecordData):
            d["selection_study"] = vars(study)
        rec_dicts.append(d)

    ids = ("todo-smoke-001", "todo-smoke-002", "todo-smoke-003")
    gold_map = {sid: gold_for_scenario(sid, scenarios_dir) for sid in ids}
    pricing = load_pricing(reports_dir)

    if not rec_dicts:
        builder_summary: dict[str, Any] = {
            "protocol": PROTOCOL,
            "records": 0,
            "gold": {k: sorted(v) for k, v in gold_map.items()},
            "rows": [],
            "agents": [],
            "impact_plans": [],
            "cost_usd": 0.0,
        }
        return builder_summary

    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for r in rec_dicts:
        groups.setdefault((r.get("scenario_id", ""), r.get("strategy_id", "")), []).append(r)

    rows = agg_table(groups, gold_map, pricing)

    agent_groups = {k: v for k, v in groups.items() if k[1] == STRATEGY_AGENT}
    impact_groups = {k: v for k, v in groups.items() if k[1] == STRATEGY_IMPACT_PLAN}

    def _arm_agg(subgroups: dict[tuple[str, str], list[dict[str, Any]]]) -> list[dict[str, Any]]:
        if not subgroups:
            return []
        all_recs: list[dict[str, Any]] = []
        for v in subgroups.values():
            all_recs.extend(v)
        agg_gold: set[str] = set()
        for k in subgroups:
            agg_gold |= gold_map.get(k[0], set())
        sub = {("__all__", "__all__"): all_recs}
        return agg_table(sub, {"__all__": agg_gold}, pricing)

    agents = _arm_agg(agent_groups)
    impact_plans = _arm_agg(impact_groups)

    cost_usd = sum(_record_cost(r, pricing) for r in rec_dicts)
    return {
        "protocol": PROTOCOL,
        "records": len(rec_dicts),
        "gold": {k: sorted(v) for k, v in gold_map.items()},
        "rows": rows,
        "agents": agents,
        "impact_plans": impact_plans,
        "cost_usd": cost_usd,
    }


def write_reports(out: dict[str, Any], reports_dir: Path) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    csv_path = reports_dir / "STAGEC_SELECTION_01_RESULTS.csv"
    md_path = reports_dir / "STAGEC_SELECTION_01_RESULTS.md"
    dec_path = reports_dir / "STAGEC_SELECTION_01_DECISION.md"

    all_rows = list(out["rows"]) + out["agents"] + out["impact_plans"]
    fields = ["scenario_id", "strategy_id"]
    seen: list[str] = []
    for row in all_rows:
        for k in row:
            if k not in seen:
                seen.append(k)
    for f in fields:
        if f not in seen:
            seen.insert(0, f)

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=seen)
        writer.writeheader()
        for row in all_rows:
            writer.writerow({k: _fmt(v) for k, v in row.items()})

    lines = [
        "# STAGE-C-SELECTION-01 results",
        "",
        "- Label: EXPLORATORY COMPONENT STUDY",
        f"- Protocol: {PROTOCOL}",
        f"- Records: {out['records']}/30",
        f"- Exact API cost: ${out['cost_usd']:.6f}",
        "",
        "No functional-correctness or end-to-end efficiency claim is made.",
        "",
    ]
    for row in all_rows:
        lines.append(f"## {row.get('scenario_id','')} / {row.get('strategy_id','')}")
        for k, v in row.items():
            lines.append(f"- {k}: {_fmt(v)}")
        lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    dec_lines = [
        "# STAGE-C-SELECTION-01 DECISION (EXPLORATORY COMPONENT STUDY)",
        "",
        f"Records: {out['records']}/30 attempted.",
        f"Cost: ${out['cost_usd']:.6f}.",
        "",
        "No confirmatory GO threshold is applied (frozen-before-calls exploratory design).",
        "The selection-only component evidence is reported in the CSV/MD tables.",
        "",
        "NEXT_ACTION=document and archive evidence (no executor change in this study).",
        "",
    ]
    dec_path.write_text("\n".join(dec_lines), encoding="utf-8")


def main() -> int:
    import sys

    runs_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("reports/scientific_stagec_selection_01")
    scenarios_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("benchmark_data/scenarios")
    reports_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("reports")
    out = build(runs_dir, scenarios_dir, reports_dir)
    write_reports(out, reports_dir)
    print("STAGEC_SELECTION_01_RESULTS_READY")
    print(f"records={out['records']}")
    print(f"cost_usd={out['cost_usd']:.6f}")
    print(f"rows={len(out['rows'])}")
    print(f"wrote {reports_dir / 'STAGEC_SELECTION_01_RESULTS.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
