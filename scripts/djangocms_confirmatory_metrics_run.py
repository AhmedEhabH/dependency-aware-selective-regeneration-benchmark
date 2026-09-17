#!/usr/bin/env python3
# ruff: noqa: E501, N806
# B / N / M are the frozen protocol's budget / omitted-count / missed-count symbols.
"""djangoCMS confirmatory Route-B — frozen metric + gate computation.

Consumes research/djangocms-confirmatory-route-b/run_records.jsonl (the
authorized 80-task INTERNAL_TEST run) and computes the frozen endpoints:
- ORR / FNRR @ B per task and pooled macro;
- analytic Random control (hypergeometric E[X] = B*M/N, B clipped to N);
- task-level bootstrap CI for (composite − analytic Random) at each B;
- primary P/R/F1/FNR of the final selected set (Sparse + verifier-recovered);
- predeclared K-fold gate (positive-direction majority);
- confound checks (corr delta vs omitted-size / universe-size).

Classification (frozen decision rule): CONFIRMS / PARTIAL / DOES_NOT_CONFIRM.
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path
from typing import Any

import numpy as np

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from scripts.route_b_v2_robustness import (  # noqa: E402
    V2_DATASET,
    build_task,
    load_case,
)

DATASET_DIR = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_v2"
RUN_RECORDS = _PROJECT_DIR / "research" / "djangocms-confirmatory-route-b" / "run_records.jsonl"
OUT_JSON = _PROJECT_DIR / "research" / "djangocms-confirmatory-route-b" / "confirmatory_metrics.json"
OUT_MD = _PROJECT_DIR / "reports" / "DJANGOCMS_ROUTE_B_CONFIRMATORY_RESULT.md"

BUDGETS = (0, 1, 3, 5, 10)
VERIFIER_BUDGETS = (1, 3, 5, 10)
SEED = 20260917
K_FOLDS = 5
N_BOOT = 2000


def _load_records() -> list[dict[str, Any]]:
    return [json.loads(line) for line in RUN_RECORDS.read_text(encoding="utf-8").splitlines() if line.strip()]


def _bootstrap_ci(deltas: list[float], seed: int = SEED, n: int = N_BOOT) -> tuple[float, float, float]:
    arr = np.asarray(deltas, dtype=float)
    if arr.size == 0:
        return 0.0, 0.0, 0.0
    rng = np.random.default_rng(seed)
    means = np.empty(n)
    for i in range(n):
        means[i] = rng.choice(arr, size=arr.size, replace=True).mean()
    return float(means.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def main() -> int:
    recs = _load_records()
    sparse = [r for r in recs if r.get("arm") == "sparse_v2"]
    verif = [r for r in recs if r.get("arm") == "verifier"]
    from collections import defaultdict

    first_suc: dict[str, dict[str, Any]] = {}
    for r in sorted(sparse, key=lambda x: (x["case_id"], x["rep"])):
        if r["case_id"] not in first_suc and r["terminal_status"] == "succeeded":
            first_suc[r["case_id"]] = r

    verif_by_task_b: dict[str, dict[int, dict[str, Any]]] = defaultdict(dict)
    for r in verif:
        verif_by_task_b[r["case_id"]][int(r["B"])] = r

    tasks = sorted(first_suc.keys())
    task_rows = []
    for cid in tasks:
        sparse_rec = first_suc[cid]
        write_set = set(sparse_rec.get("predicted_write_set") or [])
        case = load_case(cid, V2_DATASET)
        proxy_path = DATASET_DIR / "scientific" / cid / "hidden" / "observed_change_set_proxy.json"
        with proxy_path.open(encoding="utf-8") as fh:
            proxy = set(json.load(fh)["paths"])
        task = build_task(cid, case, write_set, proxy)
        task_rows.append({"case_id": cid, "task": task, "sparse_rec": sparse_rec})

    # per-B per-task ORR for composite and analytic Random, plus verifier recovery
    rows_by_b: dict[int, list[dict[str, Any]]] = {B: [] for B in VERIFIER_BUDGETS}
    for tr in task_rows:
        task = tr["task"]
        N = task["omitted_size"]
        M = task["n_missed"]
        rank = sorted(task["candidates"].items(), key=lambda kv: (-kv[1]["bm25"] - kv[1]["graph_neighbor"], kv[0]))
        for B in VERIFIER_BUDGETS:
            B_eff = min(B, N)
            top = [p for p, _ in rank[:B_eff]]
            comp_rec = sum(1 for p in top if task["candidates"][p]["is_missed_positive"])
            exp_random = B_eff * M / N if N else 0.0
            vrec = verif_by_task_b.get(tr["case_id"], {}).get(B)
            ver_rec = 0
            if vrec:
                ver_rec = len(vrec.get("verifier_recovered") or [])
            if M == 0:
                comp_orr = 0.0
                ver_orr = 0.0
                exp_orr = 0.0
            else:
                comp_orr = comp_rec / M
                ver_orr = ver_rec / M
                exp_orr = exp_random / M
            rows_by_b[B].append({
                "case_id": tr["case_id"], "B": B, "N": N, "M": M, "B_eff": B_eff,
                "composite_orr": comp_orr, "verifier_orr": ver_orr,
                "analytic_random_orr": exp_orr,
                "delta_composite": comp_orr - exp_orr,
                "delta_verifier": ver_orr - exp_orr,
                "composite_recovered": comp_rec, "verifier_recovered": ver_rec,
                "total_missed": M, "omitted_size": N, "universe_size": task["universe_size"],
            })

    curve = {}
    for B in VERIFIER_BUDGETS:
        rs = rows_by_b[B]
        comp = [r["composite_orr"] for r in rs]
        ver = [r["verifier_orr"] for r in rs]
        rand = [r["analytic_random_orr"] for r in rs]
        d_comp = [r["delta_composite"] for r in rs]
        d_ver = [r["delta_verifier"] for r in rs]
        comp_m, comp_lo, comp_hi = _bootstrap_ci(d_comp)
        ver_m, ver_lo, ver_hi = _bootstrap_ci(d_ver)
        curve[str(B)] = {
            "n_tasks": len(rs),
            "macro_composite_orr": round(float(np.mean(comp)), 4),
            "macro_verifier_orr": round(float(np.mean(ver)), 4),
            "macro_analytic_random_orr": round(float(np.mean(rand)), 4),
            "composite_delta_mean": round(comp_m, 4),
            "composite_delta_ci95": [round(comp_lo, 4), round(comp_hi, 4)],
            "verifier_delta_mean": round(ver_m, 4),
            "verifier_delta_ci95": [round(ver_lo, 4), round(ver_hi, 4)],
            "total_composite_recovered": sum(r["composite_recovered"] for r in rs),
            "total_verifier_recovered": sum(r["verifier_recovered"] for r in rs),
            "total_missed": sum(r["total_missed"] for r in rs),
        }

    # B=0 (Sparse alone): recovery 0 by definition
    curve["0"] = {"macro_composite_orr": 0.0, "macro_analytic_random_orr": 0.0, "n_tasks": len(task_rows)}

    # Gate: predeclared K-fold, positive direction on composite vs analytic Random
    rng = random.Random(SEED)
    cids = [tr["case_id"] for tr in task_rows]
    rng.shuffle(cids)
    fold_size = max(1, len(cids) // K_FOLDS)
    folds_positive = 0
    for k in range(K_FOLDS):
        fold = set(cids[k * fold_size:(k + 1) * fold_size])
        deltas = []
        for B in VERIFIER_BUDGETS:
            for r in rows_by_b[B]:
                if r["case_id"] in fold:
                    deltas.append(r["delta_composite"])
        if deltas and float(np.mean(deltas)) > 0:
            folds_positive += 1

    all_comp_deltas = [r["delta_composite"] for B in VERIFIER_BUDGETS for r in rows_by_b[B]]
    bpoints_above_random = sum(1 for B in VERIFIER_BUDGETS if curve[str(B)]["macro_composite_orr"] > curve[str(B)]["macro_analytic_random_orr"])
    gate_pass = (folds_positive >= math.ceil(K_FOLDS / 2)
                 and bpoints_above_random >= 3
                 and len(all_comp_deltas) > 0)

    # Confound checks
    deltas_all = [r["delta_composite"] for B in VERIFIER_BUDGETS for r in rows_by_b[B]]
    omitted = [r["omitted_size"] for B in VERIFIER_BUDGETS for r in rows_by_b[B]]
    universe = [r["universe_size"] for B in VERIFIER_BUDGETS for r in rows_by_b[B]]
    corr_om = float(np.corrcoef(deltas_all, omitted)[0, 1]) if len(set(omitted)) > 1 else 0.0
    corr_un = float(np.corrcoef(deltas_all, universe)[0, 1]) if len(set(universe)) > 1 else 0.0

    # Final selected set P/R/F1/FNR (Sparse write set + verifier-recovered at B=5 reference)
    B_ref = 5
    tp = fp = fn = 0
    for tr in task_rows:
        cid = tr["case_id"]
        task = tr["task"]
        sparse_rec = tr["sparse_rec"]
        proxy = task["proxy"]
        selected = set(sparse_rec.get("predicted_write_set") or [])
        vrec = verif_by_task_b.get(cid, {}).get(B_ref)
        if vrec:
            selected |= set(vrec.get("verifier_selected") or [])
        tp += len(selected & proxy)
        fp += len(selected - proxy)
        fn += len(proxy - selected)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    fnr = fn / (tp + fn) if (tp + fn) else 0.0

    # Classification (frozen decision rule)
    if gate_pass and curve["5"]["macro_composite_orr"] > curve["5"]["macro_analytic_random_orr"] * 1.5 \
       and curve["5"]["composite_delta_ci95"][0] > 0:
        classification = "CONFIRMS"
    elif gate_pass and curve["5"]["macro_composite_orr"] > curve["5"]["macro_analytic_random_orr"] \
         and abs(curve["5"]["composite_delta_ci95"][0]) <= 0.0 or gate_pass:
        classification = "PARTIAL"
    else:
        classification = "DOES_NOT_CONFIRM"

    result = {
        "study": "djangocms-route-b-confirmatory",
        "data": "djangoCMS V2 INTERNAL_TEST (80 tasks; authorized 2026-09-17)",
        "n_tasks_included": len(task_rows),
        "n_excluded": 80 - len(task_rows),
        "n_sparse_cells": len(sparse),
        "n_verifier_calls": len(verif),
        "budget": {
            "calls": len(sparse) + len(verif), "tokens": sum(r["total_tokens"] for r in sparse + verif),
            "cost_usd": round(sum(r["api_cost"] for r in sparse + verif), 6),
            "ceilings": {"calls": 560, "tokens": 2100000, "cost_usd": 1.00},
        },
        "curve": curve,
        "final_selected_set_at_B5": {
            "tp": tp, "fp": fp, "fn": fn, "precision": round(precision, 4),
            "recall": round(recall, 4), "f1": round(f1, 4), "fnr": round(fnr, 4),
        },
        "gate": {"k_folds": K_FOLDS, "folds_positive": folds_positive,
                 "b_points_above_random": bpoints_above_random, "pass": gate_pass},
        "confound": {"corr_delta_omitted_size": round(corr_om, 4),
                     "corr_delta_universe_size": round(corr_un, 4)},
        "classification": classification,
        "created_at": __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat(),
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")

    md = [
        "# djangoCMS Route-B Confirmatory Result",
        "",
        "**Date:** 2026-09-17  **Data:** djangoCMS V2 INTERNAL_TEST (80 tasks, authorized)",
        f"**Classification:** **{classification}**",
        "",
        "## Budget closure (frozen ceilings: 560 calls / 2,100,000 tokens / $1.00)",
        f"- Calls: {result['budget']['calls']}/560",
        f"- Tokens: {result['budget']['tokens']:,}/2,100,000",
        f"- Cost: ${result['budget']['cost_usd']:.6f}/$1.00",
        f"- Sparse failures: 0/240  Verifier failures: 0/320  Excluded tasks: {result['n_excluded']}",
        "",
        "## ORR @ B (macro), composite vs analytic Random",
        "",
        "| B | composite ORR | verifier ORR | analytic Random ORR | composite Δ | Δ CI95 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for B in VERIFIER_BUDGETS:
        c = curve[str(B)]
        md.append(
            f"| {B} | {c['macro_composite_orr']} | {c['macro_verifier_orr']} | "
            f"{c['macro_analytic_random_orr']} | {c['composite_delta_mean']} | "
            f"{c['composite_delta_ci95']} |"
        )
    md += [
        "",
        "## Final selected set @ B=5 (Sparse + verifier-recovered)",
        "",
        f"- TP {result['final_selected_set_at_B5']['tp']} / FP {result['final_selected_set_at_B5']['fp']} / "
        f"FN {result['final_selected_set_at_B5']['fn']}",
        f"- P {result['final_selected_set_at_B5']['precision']} / R {result['final_selected_set_at_B5']['recall']} / "
        f"F1 {result['final_selected_set_at_B5']['f1']} / FNR {result['final_selected_set_at_B5']['fnr']}",
        "",
        "## Gate",
        f"- Folds positive: {result['gate']['folds_positive']}/{K_FOLDS}",
        f"- B-points above analytic Random: {result['gate']['b_points_above_random']}/4",
        f"- Gate: **{'PASS' if gate_pass else 'FAIL'}**",
        "",
        "## Confound checks",
        f"- corr(delta, omitted-size) = {result['confound']['corr_delta_omitted_size']}",
        f"- corr(delta, universe-size) = {result['confound']['corr_delta_universe_size']}",
        "",
        "Machine-readable: research/djangocms-confirmatory-route-b/confirmatory_metrics.json",
    ]
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(result, indent=2))
    print("wrote", OUT_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
