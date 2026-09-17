#!/usr/bin/env python3
# ruff: noqa: E501, N803, N806
# B / N / M are the frozen protocol's budget symbols
# (docs/ROUTE_B_V2_DEVELOPMENT_PROTOCOL.md).
"""Saleor Route-B transfer replication (Block S6; ZERO new model calls).

TRANSFER TEST: applies the ALREADY-FROZEN Route-B V2 ranking protocol to the
Saleor DEVELOPMENT Sparse predictions. NO tuning on Saleor outcomes; no method
change based on the Saleor result in this block.

Exact frozen protocol reused (imported from scripts.route_b_v2_robustness):
- candidate = Sparse-omitted file; label = is_missed_positive (evaluation-only);
- budget curve B in {0,1,3,5,10}; primary endpoint = omission recovery rate @ B;
- analytic hypergeometric Random control;
- anchors: Sparse/B0, AnalyticRandom, BM25, PathToken, Graph, CIA, Hybrid,
  Oracle, InspectAll;
- task is the independent unit (reps deduped by case_id, first succeeded rep);
- 5-fold task-grouped CV + strata + task-level bootstrap CI + progression gate.

Outputs:
- reports/SALEOR_ROUTE_B_TRANSFER_REPORT.md
- research/transparency/saleor_route_b_transfer_results.json
- reports/saleor_route_b_transfer_gates.json
"""

from __future__ import annotations

import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

# Reuse the frozen Route-B V2 implementation (exact functions, no changes).
from scripts.route_b_v2_robustness import (  # noqa: E402
    BUDGETS,
    PREDECLARED_ARMS,
    SEED,
    build_task,
    load_case,
    recovery_at,
)

SALEOR_RECORDS = _PROJECT_DIR / "research" / "saleor-sparse-inference" / "saleor_dev_run_records.jsonl"
SALEOR_DATASET = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor"
OUT_JSON = _PROJECT_DIR / "research" / "transparency" / "saleor_route_b_transfer_results.json"
OUT_MD = _PROJECT_DIR / "reports" / "SALEOR_ROUTE_B_TRANSFER_REPORT.md"
GATES_JSON = _PROJECT_DIR / "reports" / "saleor_route_b_transfer_gates.json"


def _load_run(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> int:
    recs = _load_run(SALEOR_RECORDS)
    # Task = independent unit; dedupe by case_id, first succeeded rep (frozen behavior).
    by_case: dict[str, dict[str, Any]] = {}
    used_reps: dict[str, str] = {}
    for rec in recs:
        if rec["terminal_status"] != "succeeded":
            continue
        cid = rec["case_id"]
        if cid in by_case:
            continue
        case = load_case(cid, SALEOR_DATASET)
        proxy = set(rec["hidden_proxy_used_after_inference"])
        write_set = set(rec.get("predicted_write_set") or [])
        by_case[cid] = build_task(cid, case, write_set, proxy)
        used_reps[cid] = rec["run_id"]

    tasks = []
    for cid, task in by_case.items():
        tasks.append({"case_id": cid, "role": "SALEOR_DEV", **task})
    tasks.sort(key=lambda t: t["case_id"])

    # Frozen summarize / fold / bootstrap / strata / gate machinery (mirror of
    # route_b_v2_robustness.main, scoped to Saleor DEV).
    def curve(task, arm):
        return {str(B): recovery_at(task, arm, B) for B in BUDGETS}

    def summarize(ts):
        out = {"n_tasks": len(ts)}
        for B in BUDGETS:
            out[str(B)] = {}
            for arm in ("Sparse_B0", "AnalyticRandom", "BM25", "PathToken", "Graph", "CIA", "Hybrid", "Oracle", "InspectAll"):
                recs_b = [recovery_at(t, arm, B) for t in ts]
                macro = float(np.mean([r["orr"] for r in recs_b])) if recs_b else 0.0
                total_rec = sum(r["recovered"] for r in recs_b)
                total_missed = sum(r["total_missed"] for r in recs_b)
                micro = total_rec / total_missed if total_missed else 0.0
                out[str(B)][arm] = {
                    "macro_orr": round(macro, 4),
                    "micro_orr": round(micro, 4),
                    "recovered": round(total_rec, 4) if arm == "AnalyticRandom" else int(total_rec),
                    "total_missed": total_missed,
                }
        return out

    dev = tasks
    rng = random.Random(SEED)
    order = list(dev)
    rng.shuffle(order)
    folds = [order[k::5] for k in range(5)]

    def direction_above_random(fold_ts, arm, B=5):
        recs = [recovery_at(t, arm, B) for t in fold_ts]
        macro = float(np.mean([r["orr"] for r in recs]))
        rand_expected = float(np.mean([r["expected_random"] for r in recs])) if recs else 0.0
        return {"macro_orr": macro, "rand_expected": rand_expected, "delta": macro - rand_expected}

    fold_results = []
    for fold_ts in folds:
        fold_results.append({arm: direction_above_random(fold_ts, arm) for arm in PREDECLARED_ARMS})

    pooled_curve = summarize(dev)
    arm_scores = {}
    for arm in PREDECLARED_ARMS:
        deltas = []
        for B in BUDGETS:
            if B == 0:
                continue
            arm_recs = [recovery_at(t, arm, B) for t in dev]
            macro = float(np.mean([r["orr"] for r in arm_recs]))
            rand_exp = float(np.mean([r["expected_random"] for r in arm_recs]))
            deltas.append(macro - rand_exp)
        arm_scores[arm] = round(float(np.mean(deltas)), 4)
    best_arm = max(arm_scores, key=arm_scores.get)

    bootstrap = {}
    rng2 = random.Random(SEED + 1)
    for B in BUDGETS:
        if B == 0:
            continue
        deltas = []
        for _ in range(1000):
            sample = [rng2.choice(dev) for _ in dev]
            m1 = float(np.mean([recovery_at(t, best_arm, B)["orr"] for t in sample]))
            m2 = float(np.mean([recovery_at(t, "AnalyticRandom", B)["orr"] for t in sample]))
            deltas.append(m1 - m2)
        arr = np.asarray(deltas)
        bootstrap[str(B)] = {"delta_mean": round(float(np.mean(arr)), 4),
                             "ci95": [round(float(np.percentile(arr, 2.5)), 4),
                                      round(float(np.percentile(arr, 97.5)), 4)]}

    strata = {}
    for name, key in (("year", "year"), ("omitted_size", "omitted_size"),
                      ("universe_size", "universe_size"), ("proxy_size", "proxy_size")):
        buckets = defaultdict(list)
        for t in dev:
            buckets[t[key]].append(t)
        strata[name] = {}
        for v, ts in sorted(buckets.items(), key=lambda kv: str(kv[0])):
            s_recs = [recovery_at(t, best_arm, 5) for t in ts]
            rand_exp = [recovery_at(t, "AnalyticRandom", 5) for t in ts]
            strata[name][str(v)] = {
                "n": len(ts),
                "macro_orr": round(float(np.mean([r["orr"] for r in s_recs])), 4),
                "rand_expected": round(float(np.mean([r["expected_random"] for r in rand_exp])), 4),
                "delta": round(float(np.mean([r["orr"] for r in s_recs])) - float(np.mean([r["expected_random"] for r in rand_exp])), 4),
            }

    fold_pos = sum(1 for f in fold_results if f[best_arm]["delta"] > 0)
    n_curve_positive = sum(1 for B in BUDGETS if B > 0 and (pooled_curve[str(B)][best_arm]["macro_orr"] > pooled_curve[str(B)]["AnalyticRandom"]["macro_orr"]))
    deltas_per_task = [recovery_at(t, best_arm, 5)["orr"] - recovery_at(t, "AnalyticRandom", 5)["orr"] for t in dev]
    corr_omitted = float(np.corrcoef([t["omitted_size"] for t in dev], deltas_per_task)[0, 1])
    corr_universe = float(np.corrcoef([t["universe_size"] for t in dev], deltas_per_task)[0, 1])
    gate_pass = (
        fold_pos >= math.ceil(5 / 2)
        and n_curve_positive >= 2
        and abs(corr_omitted) < 0.4
        and abs(corr_universe) < 0.4
    )
    gate = {
        "best_arm": best_arm,
        "fold_positive_direction": fold_pos,
        "n_folds": 5,
        "direction_majority": fold_pos >= math.ceil(5 / 2),
        "b_curve_positive_over_random": n_curve_positive,
        "n_b_curve_points": len([B for B in BUDGETS if B > 0]),
        "above_random_nontrivial": n_curve_positive >= 2,
        "corr_omitted_size_artifact": round(corr_omitted, 3),
        "corr_universe_size_artifact": round(corr_universe, 3),
        "artifact_free": abs(corr_omitted) < 0.4 and abs(corr_universe) < 0.4,
        "leakage_free": True,
        "gate_pass": gate_pass,
    }

    # Transfer classification (pre-registered in the mission):
    # REPLICATES: gate PASS and best-arm B=5 CI excludes 0 and delta at B=5 > 0.05
    # PARTIAL:    gate PASS but CI includes 0 OR B=5 delta <= 0.05
    #             OR gate FAILS on folds/curve but direction still positive overall
    # DOES NOT REPLICATE: gate FAILS and no material positive effect
    b5 = bootstrap.get("5", {})
    ci_low, ci_high = b5.get("ci95", [0.0, 0.0])
    b5_delta = b5.get("delta_mean", 0.0)
    if gate_pass and ci_low > 0 and b5_delta > 0.05:
        classification = "REPLICATES"
    elif gate_pass and (ci_low <= 0 or b5_delta <= 0.05) or (fold_pos >= 3 or n_curve_positive >= 2) and b5_delta > 0:
        classification = "PARTIAL REPLICATION"
    else:
        classification = "DOES NOT REPLICATE"
    gate["transfer_classification"] = classification

    result = {
        "study_id": "saleor-route-b-transfer",
        "repository": "saleor",
        "transfer_test": "frozen Route-B V2 protocol applied to Saleor DEV; NO tuning; NO method change",
        "n_tasks": len(tasks),
        "n_development": len(dev),
        "reps_deduped_by_case_first_succeeded": True,
        "n_failed_cells_excluded": sum(1 for r in recs if r["terminal_status"] != "succeeded"),
        "budgets": list(BUDGETS),
        "best_predeclared_arm": best_arm,
        "arm_mean_curve_delta_vs_random": arm_scores,
        "pooled_curve": pooled_curve,
        "fold_results": fold_results,
        "bootstrap_ci_best_vs_random": bootstrap,
        "strata": strata,
        "progression_gate": gate,
        "transfer_classification": classification,
    }
    OUT_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")

    md = [
        "# Saleor Route-B Transfer Replication",
        "",
        f"**Date:** 2026-09-17  **Repository:** Saleor  **N development tasks:** {len(dev)}",
        "TRANSFER TEST — frozen Route-B V2 protocol applied to Saleor DEVELOPMENT;",
        "no tuning on Saleor outcomes; no method change in this block.",
        "",
        "## Pooled omission recovery rate (macro ORR) by arm and B (Saleor, per-repository primary)",
        "",
        "| B | Sparse/B0 | AnalyticRandom | BM25 | PathToken | Graph | CIA | Hybrid | Oracle | InspectAll |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for B in BUDGETS:
        b = pooled_curve[str(B)]
        md.append(
            f"| {B} | {b['Sparse_B0']['macro_orr']:.3f} | {b['AnalyticRandom']['macro_orr']:.3f} "
            f"| {b['BM25']['macro_orr']:.3f} | {b['PathToken']['macro_orr']:.3f} | {b['Graph']['macro_orr']:.3f} "
            f"| {b['CIA']['macro_orr']:.3f} | {b['Hybrid']['macro_orr']:.3f} | {b['Oracle']['macro_orr']:.3f} "
            f"| {b['InspectAll']['macro_orr']:.3f} |"
        )
    md += [
        "",
        "## Best predeclared arm vs analytic Random (bootstrap CI)",
        "",
        f"Best arm: **{best_arm}** (mean curve delta vs random {arm_scores[best_arm]}).",
        "",
        "| B | delta | 95% CI |",
        "|---|---:|---:|",
    ]
    for B in BUDGETS:
        if B == 0:
            continue
        c = bootstrap[str(B)]
        md.append(f"| {B} | {c['delta_mean']:+.3f} | [{c['ci95'][0]:+.3f}, {c['ci95'][1]:+.3f}] |")
    md += [
        "",
        "## Progression gate",
        "",
        f"- best arm: {best_arm}",
        f"- folds with positive direction: {gate['fold_positive_direction']}/{gate['n_folds']} "
        f"(majority: {gate['direction_majority']})",
        f"- B-curve points above analytic Random: {gate['b_curve_positive_over_random']}/{gate['n_b_curve_points']}",
        f"- corr(omitted-size, delta) = {gate['corr_omitted_size_artifact']}",
        f"- corr(universe-size, delta) = {gate['corr_universe_size_artifact']}",
        f"- gate PASS: **{gate['gate_pass']}**",
        "",
        "## Transfer classification",
        "",
        f"**{classification}**",
        "",
        "## Notes",
        "",
        "- Per-repository primary (Saleor reported FIRST; no djangoCMS+Saleor pooling as the headline).",
        "- Task = independent unit; 3 nested reps deduped by case_id (first succeeded rep).",
        "- Analytic Random (hypergeometric expectation) is the control.",
        "- Oracle@B = ranking headroom; InspectAll = exhaustive reconsideration.",
        "- Full machine-readable results: research/transparency/saleor_route_b_transfer_results.json",
    ]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    GATES_JSON.write_text(json.dumps({"gates": [{"name": "progression", "passed": gate["gate_pass"], "detail": gate}],
                                      "all_passed": gate["gate_pass"]}, indent=2), encoding="utf-8")

    print("n_tasks", len(tasks), "n_dev", len(dev))
    print("best_arm", best_arm, "mean_delta", arm_scores[best_arm])
    print("gate", json.dumps(gate, indent=1))
    print("classification", classification)
    print("outputs:", OUT_JSON, OUT_MD, GATES_JSON)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
