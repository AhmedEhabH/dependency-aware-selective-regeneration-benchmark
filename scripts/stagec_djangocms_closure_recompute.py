#!/usr/bin/env python3
"""POST-STUDY CLOSURE: recompute EVERY study fact from the 60 raw run records.

Zero scientific calls. Persists a closure recomputation artifact that the
reports are then regenerated from.
"""

from __future__ import annotations
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from benchmark.external_validity import study_runtime as wiring

PROJECT_DIR = wiring.PROJECT_DIR
STUDY_DIR = PROJECT_DIR / "reports" / "scientific-stagec-djangocms-study-01"
RECORDS_PATH = STUDY_DIR / "run_records.jsonl"
MANIFEST_PATH = STUDY_DIR / "manifest_60.json"

ARMS = ("iterative_repository_agent", "impact_plan")


def load_records() -> list[dict]:
    out = []
    for line in RECORDS_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def classify_failure(rec: dict) -> str:
    """Deterministic failure classification from raw evidence."""
    cat = str(rec.get("failure_category", ""))
    msgs = " | ".join(str(e.get("message", "")) for e in rec.get("failure_evidence", []) or [])
    blob = cat + " | " + msgs
    if "finish_reason=length" in blob:
        return "completion_truncation_4096_cap"
    if "planner produced unknown paths" in blob:
        return "unknown_path_non_universe"
    if "OpenRouter HTTP 429" in blob:
        return "provider_http_429"
    if "no paths selected" in blob:
        return "empty_selection_fail_closed"
    if "harness_exception" in cat or "ValueError" in blob:
        return "harness_defect"
    return f"other:{cat[:60]}"


def main() -> int:
    records = load_records()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest_ids = {c["run_id"] for c in manifest["cells"]}
    record_ids = {r["run_id"] for r in records}

    assert len(manifest["cells"]) == 60, "manifest cells != 60"
    assert len(records) == 60, f"records = {len(records)} != 60"
    assert record_ids == manifest_ids, "record/run_id mismatch with manifest"
    assert len(record_ids) == 60, "duplicate run_id"

    valid = [r for r in records if r["terminal_status"] == "succeeded"]
    failed = [r for r in records if r["terminal_status"] != "succeeded"]

    # Per-arm valid/failed
    arm_counts = {}
    for arm in ARMS:
        arm_recs = [r for r in records if r["arm"] == arm]
        v = [r for r in arm_recs if r["terminal_status"] == "succeeded"]
        f = [r for r in arm_recs if r["terminal_status"] != "succeeded"]
        arm_counts[arm] = {
            "total": len(arm_recs),
            "valid": len(v),
            "failed": len(f),
            "valid_rate": round(len(v) / len(arm_recs), 6),
        }

    # Failure taxonomy
    taxonomy: dict[str, dict] = {}
    for f in failed:
        kind = classify_failure(f)
        entry = taxonomy.setdefault(kind, {"count": 0, "arm_counts": {}, "run_ids": []})
        entry["count"] += 1
        entry["arm_counts"][f["arm"]] = entry["arm_counts"].get(f["arm"], 0) + 1
        entry["run_ids"].append(f["run_id"])

    # Truncation raw-evidence verification
    trunc = [r for r in failed if classify_failure(r) == "completion_truncation_4096_cap"]
    trunc_evidence = []
    for r in trunc:
        trunc_evidence.append(
            {
                "run_id": r["run_id"],
                "finish_reason": r.get("finish_reason", ""),
                "truncation_status": r.get("truncation_status", False),
                "completion_tokens": r.get("completion_tokens", 0),
                "max_cap": 4096,
            }
        )

    def micro(rows: list[dict]) -> dict:
        selected = sum(int(r["predicted_write_set_size"]) for r in rows)
        tp = sum(int(r["tp"]) for r in rows)
        fp = sum(int(r["fp"]) for r in rows)
        fn = sum(int(r["fn"]) for r in rows)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        fnr = fn / (tp + fn) if (tp + fn) else 0.0
        return {
            "selected": selected,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": round(precision, 6),
            "recall": round(recall, 6),
            "f1": round(f1, 6),
            "fnr": round(fnr, 6),
        }

    def stats(values: list[float]) -> dict:
        if not values:
            return {"mean": None, "median": None, "min": None, "max": None}
        return {
            "mean": round(statistics.mean(values), 6),
            "median": round(statistics.median(values), 6),
            "min": round(min(values), 6),
            "max": round(max(values), 6),
        }

    # Valid-run headline (micro) + all-cell operational
    valid_headline: dict[str, dict] = {}
    all_cell: dict[str, dict] = {}
    macro: dict[str, dict] = {}
    for arm in ARMS:
        v = [r for r in valid if r["arm"] == arm]
        a = [r for r in records if r["arm"] == arm]
        m = micro(v)
        valid_headline[arm] = {
            **m,
            "tokens": sum(int(r["total_tokens"]) for r in v),
            "model_calls": sum(int(r["model_calls"]) for r in v),
            "tool_calls": sum(int(r["tool_calls"]) for r in v),
            "read_file_calls": sum(int(r.get("explicit_read_file_count", 0)) for r in v),
            "inspected_files": sum(int(r.get("inspected_file_count", 0)) for r in v),
            "time": round(sum(float(r["latency_seconds"]) for r in v), 6),
            "cost": round(sum(float(r["api_cost"]) for r in v), 6),
        }
        all_cell[arm] = {
            "valid": arm_counts[arm]["valid"],
            "failed": arm_counts[arm]["failed"],
            "valid_rate": arm_counts[arm]["valid_rate"],
            "tokens": sum(int(r["total_tokens"]) for r in a),
            "model_calls": sum(int(r["model_calls"]) for r in a),
            "tool_calls": sum(int(r["tool_calls"]) for r in a),
            "read_file_calls": sum(int(r.get("explicit_read_file_count", 0)) for r in a),
            "time": round(sum(float(r["latency_seconds"]) for r in a), 6),
            "cost": round(sum(float(r["api_cost"]) for r in a), 6),
        }
        macro[arm] = {
            "valid_runs": len(v),
            "mean_precision": stats([float(r["precision"]) for r in v])["mean"],
            "median_precision": stats([float(r["precision"]) for r in v])["median"],
            "mean_recall": stats([float(r["recall"]) for r in v])["mean"],
            "median_recall": stats([float(r["recall"]) for r in v])["median"],
            "mean_f1": stats([float(r["f1"]) for r in v])["mean"],
            "median_f1": stats([float(r["f1"]) for r in v])["median"],
            "full_recall_rate": round(
                sum(1 for r in v if r.get("full_recall")) / len(v), 6
            ) if v else None,
            "selected_set_size": stats([float(r["predicted_write_set_size"]) for r in v]),
            "tokens": stats([float(r["total_tokens"]) for r in v]),
            "model_calls": stats([float(r["model_calls"]) for r in v]),
            "latency": stats([float(r["latency_seconds"]) for r in v]),
            "cost": stats([float(r["api_cost"]) for r in v]),
        }

    # Latency outliers (valid runs, mean + 2 sd)
    lat_all = [float(r["latency_seconds"]) for r in valid]
    lat_mean = statistics.mean(lat_all)
    lat_sd = statistics.stdev(lat_all) if len(lat_all) > 1 else 0.0
    outliers = sorted(
        [r["run_id"] for r in valid if float(r["latency_seconds"]) > lat_mean + 2 * lat_sd]
    )

    # Per-scenario valid-only (N/A when zero valid)
    per_scenario = {}
    for sid in sorted(wiring.final_scenario_ids()):
        per_scenario[sid] = {}
        for arm in ARMS:
            v = [r for r in valid if r["arm"] == arm and r["scenario_id"] == sid]
            m = micro(v)
            per_scenario[sid][arm] = {
                "valid_runs": len(v),
                **m,
                "tokens": sum(int(r["total_tokens"]) for r in v),
                "model_calls": sum(int(r["model_calls"]) for r in v),
                "time": round(sum(float(r["latency_seconds"]) for r in v), 6),
                "cost": round(sum(float(r["api_cost"]) for r in v), 6),
            }

    # ImpactPlan relative to Agent (all-cell)
    agent_all, impact_all = all_cell["iterative_repository_agent"], all_cell["impact_plan"]
    relative = {
        "tokens_pct": round((impact_all["tokens"] - agent_all["tokens"]) / agent_all["tokens"] * 100, 2),
        "model_calls_pct": round((impact_all["model_calls"] - agent_all["model_calls"]) / agent_all["model_calls"] * 100, 2),
        "cost_pct": round((impact_all["cost"] - agent_all["cost"]) / agent_all["cost"] * 100, 2),
        "time_pct": round((impact_all["time"] - agent_all["time"]) / agent_all["time"] * 100, 2),
    }

    total_cost = round(sum(float(r["api_cost"]) for r in records), 6)

    result = {
        "recomputed_at": __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat(),
        "manifest_cells": len(manifest["cells"]),
        "records": len(records),
        "records_equal_manifest": record_ids == manifest_ids,
        "valid": len(valid),
        "failed": len(failed),
        "arm_counts": arm_counts,
        "failure_taxonomy": {
            kind: {"count": v["count"], "arm_counts": v["arm_counts"]}
            for kind, v in sorted(taxonomy.items())
        },
        "truncation_raw_evidence": trunc_evidence,
        "valid_headline_micro": valid_headline,
        "all_cell_operational": all_cell,
        "impactplan_relative_to_agent_all_cell": relative,
        "macro_valid_runs": macro,
        "per_scenario_valid": per_scenario,
        "latency_outliers_valid": outliers,
        "total_recorded_cost_usd": total_cost,
        "totals_all_cell": {
            "tokens": sum(int(r["total_tokens"]) for r in records),
            "model_calls": sum(int(r["model_calls"]) for r in records),
            "tool_calls": sum(int(r["tool_calls"]) for r in records),
            "read_file_calls": sum(int(r.get("explicit_read_file_count", 0)) for r in records),
            "time": round(sum(float(r["latency_seconds"]) for r in records), 6),
            "cost": total_cost,
        },
    }

    out_path = STUDY_DIR / "closure_recompute.json"
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    print(f"persisted={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())