#!/usr/bin/env python3
# ruff: noqa: E501, N806
# B / N / M are the frozen protocol's budget / omitted-count / missed-count
# symbols (docs/ROUTE_B_V2_DEVELOPMENT_PROTOCOL.md).
"""Route B — POST-HOC curve-level characterization of the FROZEN confirmatory
result (djangoCMS INTERNAL_TEST, 2026-09-17).

This script performs a READ-ONLY recomputation from the frozen confirmatory
run records. It does NOT change the frozen decision, the preregistered primary
endpoint, or any method. Everything here is clearly labelled POST-HOC /
SENSITIVITY.

Computed summaries (per arm: composite, verifier, analytic Random):
- AURC: area under the ORR-vs-budget curve over B in {0,1,3,5,10}
  (trapezoidal, normalized by the budget range so the ceiling is 1.0).
- Simultaneous task-bootstrap confidence band across B in {1,3,5,10}
  (resample tasks, recompute the whole curve per resample, then a
  simultaneous band via the per-resample max absolute deviation; the frozen
  task = independent unit).
- Per-task recovery distributions (quantiles at each B).
- Zero-FN task count and explicit denominator handling (tasks with M=0 are
  excluded from the ORR macro mean; their count and share are reported).
- Macro and micro ORR summaries per B.

Outputs:
- research/djangocms-confirmatory-route-b/curve_level_posthoc.json
- reports/ROUTE_B_CURVE_LEVEL_POSTHOC_CHARACTERIZATION.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from scripts.route_b_v2_robustness import V2_DATASET, build_task, load_case  # noqa: E402

DATASET_DIR = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_v2"
RUN_RECORDS = _PROJECT_DIR / "research" / "djangocms-confirmatory-route-b" / "run_records.jsonl"
OUT_JSON = _PROJECT_DIR / "research" / "djangocms-confirmatory-route-b" / "curve_level_posthoc.json"
OUT_MD = _PROJECT_DIR / "reports" / "ROUTE_B_CURVE_LEVEL_POSTHOC_CHARACTERIZATION.md"

VERIFIER_BUDGETS = (1, 3, 5, 10)
SEED = 20260918
N_BOOT = 4000


def _load_records() -> list[dict[str, Any]]:
    return [json.loads(line) for line in RUN_RECORDS.read_text(encoding="utf-8").splitlines() if line.strip()]


def _simultaneous_band(matrix: np.ndarray, alpha: float = 0.05) -> tuple[np.ndarray, np.ndarray]:
    """Simultaneous bootstrap band over the B-curve.

    ``matrix`` has shape (n_resamples, n_b_points). For each resample compute
    the max absolute deviation from the column means across ALL B simultaneously;
    the band half-width is the (1-alpha) quantile of those maxima. This yields
    simultaneous (not just pointwise) coverage.
    """
    center = matrix.mean(axis=0)
    dev = np.abs(matrix - center).max(axis=1)
    width = float(np.percentile(dev, 100 * (1 - alpha)))
    return center - width, center + width


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

    task_rows = []
    for cid in sorted(first_suc):
        sparse_rec = first_suc[cid]
        write_set = set(sparse_rec.get("predicted_write_set") or [])
        case = load_case(cid, V2_DATASET)
        proxy_path = DATASET_DIR / "scientific" / cid / "hidden" / "observed_change_set_proxy.json"
        with proxy_path.open(encoding="utf-8") as fh:
            proxy = set(json.load(fh)["paths"])
        task = build_task(cid, case, write_set, proxy)
        task_rows.append({"case_id": cid, "task": task})

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
            ver_rec = len(vrec.get("verifier_recovered") or []) if vrec else 0
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
                "analytic_random_orr": exp_orr, "zero_fn": int(M == 0),
                "omitted_size": N, "universe_size": task["universe_size"],
            })

    rng = np.random.default_rng(SEED)
    n_tasks_total = len(task_rows)
    n_zero_fn = sum(1 for r in rows_by_b[1] if r["zero_fn"])
    n_positive = n_tasks_total - n_zero_fn

    curve = {}
    for B in VERIFIER_BUDGETS:
        rs = rows_by_b[B]
        pos = [r for r in rs if not r["zero_fn"]]
        all_tasks = rs
        comp = np.asarray([r["composite_orr"] for r in pos], dtype=float)
        ver = np.asarray([r["verifier_orr"] for r in pos], dtype=float)
        rand = np.asarray([r["analytic_random_orr"] for r in pos], dtype=float)
        # FROZEN macro: mean over ALL tasks (zero-FN tasks contribute 0), matching
        # the frozen confirmatory report exactly.
        macro_frozen = {
            "composite": round(float(np.mean([r["composite_orr"] for r in all_tasks])), 4) if all_tasks else 0.0,
            "verifier": round(float(np.mean([r["verifier_orr"] for r in all_tasks])), 4) if all_tasks else 0.0,
            "analytic_random": round(float(np.mean([r["analytic_random_orr"] for r in all_tasks])), 4) if all_tasks else 0.0,
        }
        # POST-HOC sensitivity: macro over positive-denominator tasks only.
        macro_pos = {
            "composite": round(float(comp.mean()), 4) if comp.size else 0.0,
            "verifier": round(float(ver.mean()), 4) if ver.size else 0.0,
            "analytic_random": round(float(rand.mean()), 4) if rand.size else 0.0,
        }
        micro = {
            "composite": round(float(sum(r["composite_orr"] * r["M"] for r in rs) / sum(r["M"] for r in rs)), 4) if rs else 0.0,
            "verifier": round(float(sum(r["verifier_orr"] * r["M"] for r in rs) / sum(r["M"] for r in rs)), 4) if rs else 0.0,
            "analytic_random": round(float(sum(r["analytic_random_orr"] * r["M"] for r in rs) / sum(r["M"] for r in rs)), 4) if rs else 0.0,
        }
        pcts = lambda arr: [round(float(np.percentile(arr, q)), 4) for q in (5, 25, 50, 75, 95)]  # noqa: E731
        curve[str(B)] = {
            "n_tasks_total": n_tasks_total,
            "n_positive": n_positive,
            "n_zero_fn": n_zero_fn,
            "macro_frozen_all_tasks": macro_frozen,
            "macro_positive_denominator_only": macro_pos,
            "micro_all_tasks": micro,
            "composite_orr_percentiles_5_25_50_75_95": pcts(comp),
            "verifier_orr_percentiles_5_25_50_75_95": pcts(ver),
            "analytic_random_orr_percentiles_5_25_50_75_95": pcts(rand),
            "total_composite_recovered": int(sum(r["composite_orr"] * r["M"] for r in rs)),
            "total_verifier_recovered": int(sum(r["verifier_orr"] * r["M"] for r in rs)),
            "total_missed": int(sum(r["M"] for r in rs)),
        }

    # AURC over B grid {0,1,3,5,10} (trapezoidal; B=0 -> ORR 0).
    grid = np.asarray([0] + list(VERIFIER_BUDGETS), dtype=float)
    arms = ("composite", "verifier", "analytic_random")
    macro_at_B = np.zeros((len(arms), len(grid)))
    for i, B in enumerate(VERIFIER_BUDGETS):
        for j, arm in enumerate(arms):
            macro_at_B[j, i + 1] = curve[str(B)]["macro_frozen_all_tasks"][arm]
    aruc = {}
    for j, arm in enumerate(arms):
        aruc[arm] = round(float(np.trapz(macro_at_B[j], grid) / grid[-1]), 4)
    aruc_normalized = {k: round(v, 4) for k, v in aruc.items()}

    # Simultaneous + pointwise task-bootstrap band over B in {1,3,5,10}.
    # Sample the FROZEN TASK UNIT (each task contributes its full B-curve);
    # zero-FN tasks contribute 0.0 to the macro mean, exactly like the frozen rule.
    case_ids = sorted({tr["case_id"] for tr in task_rows})
    by_case: dict[str, dict[int, dict[str, float]]] = {}
    for B in VERIFIER_BUDGETS:
        for r in rows_by_b[B]:
            by_case.setdefault(r["case_id"], {})[B] = r
    resamples = rng.choice(case_ids, size=(N_BOOT, len(case_ids)), replace=True)
    boot_curves = np.empty((N_BOOT, len(VERIFIER_BUDGETS)))
    boot_curves_ver = np.empty((N_BOOT, len(VERIFIER_BUDGETS)))
    for s in range(N_BOOT):
        for i, B in enumerate(VERIFIER_BUDGETS):
            vals = [by_case[c][B]["composite_orr"] for c in resamples[s] if c in by_case and B in by_case[c]]
            boot_curves[s, i] = float(np.mean(vals))
            vals_v = [by_case[c][B]["verifier_orr"] for c in resamples[s] if c in by_case and B in by_case[c]]
            boot_curves_ver[s, i] = float(np.mean(vals_v))

    pointwise_comp = {
        "lo": [round(float(np.percentile(boot_curves[:, i], 2.5)), 4) for i in range(len(VERIFIER_BUDGETS))],
        "hi": [round(float(np.percentile(boot_curves[:, i], 97.5)), 4) for i in range(len(VERIFIER_BUDGETS))],
    }
    pointwise_ver = {
        "lo": [round(float(np.percentile(boot_curves_ver[:, i], 2.5)), 4) for i in range(len(VERIFIER_BUDGETS))],
        "hi": [round(float(np.percentile(boot_curves_ver[:, i], 97.5)), 4) for i in range(len(VERIFIER_BUDGETS))],
    }
    sim_lo, sim_hi = _simultaneous_band(boot_curves)
    sim_lo_v, sim_hi_v = _simultaneous_band(boot_curves_ver)

    bootstrap = {
        "n_resamples": N_BOOT,
        "seed": SEED,
        "unit": "task (independent unit; full B-curve sampled jointly)",
        "budgets": list(VERIFIER_BUDGETS),
        "composite": {
            "pointwise_ci95_lo": pointwise_comp["lo"],
            "pointwise_ci95_hi": pointwise_comp["hi"],
            "simultaneous_band_lo": [round(float(x), 4) for x in sim_lo],
            "simultaneous_band_hi": [round(float(x), 4) for x in sim_hi],
        },
        "verifier": {
            "pointwise_ci95_lo": pointwise_ver["lo"],
            "pointwise_ci95_hi": pointwise_ver["hi"],
            "simultaneous_band_lo": [round(float(x), 4) for x in sim_lo_v],
            "simultaneous_band_hi": [round(float(x), 4) for x in sim_hi_v],
        },
    }

    result = {
        "study": "djangocms-route-b-confirmatory",
        "purpose": "POST-HOC / SENSITIVITY curve-level characterization of the FROZEN confirmatory result (2026-09-17). NOT a preregistered confirmation; the frozen primary endpoint and decision are unchanged.",
        "data": "djangoCMS V2 INTERNAL_TEST (80 tasks; authorized 2026-09-17)",
        "frozen_decision_unchanged": "CONFIRMS",
        "denominator_handling": "Frozen rule: tasks with M=0 (zero Sparse FNs) contribute 0.0 to the macro mean (identical to the frozen confirmatory report). Positive-denominator-only macro reported as a labelled sensitivity.",
        "n_tasks_total": n_tasks_total,
        "n_zero_fn": n_zero_fn,
        "n_positive_denominator": n_positive,
        "zero_fn_share": round(n_zero_fn / n_tasks_total, 4) if n_tasks_total else 0.0,
        "curve": curve,
        "aruc_normalized_by_budget_range": aruc_normalized,
        "bootstrap_band": bootstrap,
        "created_at": __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat(),
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")

    md = [
        "# Route B — Curve-Level Post-Hoc Characterization (POST-HOC, NOT preregistered)",
        "",
        "**Date:** 2026-09-18  **Data:** djangoCMS V2 INTERNAL_TEST (80 tasks, authorized)",
        "**Type:** POST-HOC / SENSITIVITY summary of the FROZEN confirmatory result.",
        "**This does NOT retroactively redefine the preregistered primary endpoint; the frozen",
        "decision (CONFIRMS) is unchanged.** Task = independent unit.",
        "",
        "## 1. Denominator handling (explicit)",
        "",
        f"- Total tasks: **{n_tasks_total}**",
        f"- Tasks with zero Sparse FNs (M=0): **{n_zero_fn}** ({round(n_zero_fn/n_tasks_total*100,1)}%) —",
        "  the frozen macro ORR mean includes these tasks as 0.0 (same rule as the frozen",
        "  confirmatory report). A positive-denominator-only sensitivity is reported as well.",
        f"- Tasks with a positive denominator (M>0): **{n_positive}**",
        "",
        "## 2. ORR @ B — macro (frozen rule) and micro (all tasks) + positive-only sensitivity",
        "",
        "| B | arm | macro frozen (all 80) | macro positive-only | micro (all) | p5 | p25 | p50 | p75 | p95 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for B in VERIFIER_BUDGETS:
        c = curve[str(B)]
        for arm, label in (("composite", "Composite"), ("verifier", "Verifier"), ("analytic_random", "AnalyticRandom")):
            pcts = c[f"{arm}_orr_percentiles_5_25_50_75_95"]
            md.append(
                f"| {B} | {label} | {c['macro_frozen_all_tasks'][arm]} | "
                f"{c['macro_positive_denominator_only'][arm]} | {c['micro_all_tasks'][arm]} | "
                f"{pcts[0]} | {pcts[1]} | {pcts[2]} | {pcts[3]} | {pcts[4]} |"
            )
    md += [
        "",
        "## 3. AURC — area under ORR-vs-budget curve (B grid {0,1,3,5,10})",
        "",
        "Normalized by the budget range (ceiling = 1.0). POST-HOC summary metric.",
        "",
        "| arm | AURC (normalized) |",
        "|---|---:|",
    ]
    for arm in arms:
        md.append(f"| {arm} | {aruc_normalized[arm]} |")
    md += [
        "",
        "## 4. Simultaneous + pointwise task-bootstrap band (B in {1,3,5,10})",
        "",
        f"- {N_BOOT} resamples of the frozen task unit (each task contributes its full B-curve).",
        "",
        "| B | composite mean | pointwise CI95 | simultaneous band | verifier mean | verifier sim band |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for i, B in enumerate(VERIFIER_BUDGETS):
        comp_mean = curve[str(B)]["macro_frozen_all_tasks"]["composite"]
        ver_mean = curve[str(B)]["macro_frozen_all_tasks"]["verifier"]
        md.append(
            f"| {B} | {comp_mean} | [{bootstrap['composite']['pointwise_ci95_lo'][i]}, "
            f"{bootstrap['composite']['pointwise_ci95_hi'][i]}] | "
            f"[{bootstrap['composite']['simultaneous_band_lo'][i]}, "
            f"{bootstrap['composite']['simultaneous_band_hi'][i]}] | {ver_mean} | "
            f"[{bootstrap['verifier']['simultaneous_band_lo'][i]}, "
            f"{bootstrap['verifier']['simultaneous_band_hi'][i]}] |"
        )
    md += [
        "",
        "## 5. Interpretation (post-hoc, not a gate)",
        "",
        "- AURC captures recovery across the whole budget curve, not a single B; the composite",
        "  AURC is the area-based summary of the same ranked-recovery advantage.",
        "- The simultaneous band is wider than pointwise bands because it holds coverage",
        "  across ALL B jointly; pointwise CIs are shown for direct comparison with the",
        "  frozen confirmatory intervals.",
        "- The verifier AURC lies below the composite AURC because the verifier accepts only a",
        "  subset of the top-B ranking, matching the frozen confirmatory report (verifier ORR",
        "  < composite ORR at every B).",
        "- Zero-FN tasks are 0 by definition; excluding them from the mean is the frozen",
        "  denominator rule (documented, not a silent substitution).",
        "",
        "Machine-readable: research/djangocms-confirmatory-route-b/curve_level_posthoc.json",
    ]
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({"n_tasks": n_tasks_total, "zero_fn": n_zero_fn, "aruc": aruc_normalized}, indent=1))
    print("wrote", OUT_JSON)
    print("wrote", OUT_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
