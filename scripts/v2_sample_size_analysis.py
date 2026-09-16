#!/usr/bin/env python3
"""RealCommitImpactDataset-v2 — sample-size / power analysis (development-planning only).

Uses observed DEVELOPMENT evidence only (Sparse-v2 has_fn on the 30 v1
development tasks) to plan a V2 development set. NEVER tunes a test.

Sensitivity grid over plausible negative prevalence:
  5%, 10%, 13.3% (observed), 15%, 20%, 25%

For plausible development N values estimates:
- expected negatives;  P(negatives >= 10);  P(negatives >= 20)
- AUROC CI / bootstrap precision under plausible effects (simulated)
- AUPRC sensitivity to prevalence
- cost of 3-rep Sparse inference (frozen per-cell cost from the 90-cell run)
- cells / tokens / cost under the authorized ceilings (450 cells / 2.5M tokens / $1.00)

Outputs: reports/REAL_COMMIT_V2_SAMPLE_SIZE_ANALYSIS.md + research/transparency/v2_sample_size.json
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

OUT_JSON = _PROJECT_DIR / "research" / "transparency" / "v2_sample_size.json"
OUT_MD = _PROJECT_DIR / "reports" / "REAL_COMMIT_V2_SAMPLE_SIZE_ANALYSIS.md"

# Observed development evidence (frozen, from the 90-cell Sparse-v2 run).
OBSERVED_N = 30
OBSERVED_POS = 26
OBSERVED_NEG = 4
OBSERVED_NEG_PREV = OBSERVED_NEG / OBSERVED_N

# Frozen 90-cell Sparse-v2 run cost basis (TRAIN/VALIDATION, 3 reps/task).
CELLS_90 = 90
TOKENS_90 = 490747
COST_90 = 0.184088
TOKENS_PER_TASK_3REP = TOKENS_90 / OBSERVED_N
COST_PER_TASK_3REP = COST_90 / OBSERVED_N

# Authorized ceilings (mission file §C3).
CELL_CEILING = 450
TOKEN_CEILING = 2_500_000
COST_CEILING = 1.00
REPS = 3

NEG_PREV_GRID = (0.05, 0.10, OBSERVED_NEG_PREV, 0.15, 0.20, 0.25)
N_GRID = (60, 90, 120, 150, 180, 240, 300, 450)

# Simulated AUROC precision under plausible effect sizes.
EFFECT_AUROC = (0.60, 0.70, 0.80)
SIM_SEED = 20260916
SIM_N = 2000


def binom_cdf(k: int, n: int, p: float) -> float:
    """P(X <= k) for X ~ Binomial(n, p)."""
    return float(sum(math.comb(n, i) * (p**i) * ((1 - p) ** (n - i)) for i in range(k + 1)))


def prob_at_least(n: int, p: float, target: int) -> float:
    return 1.0 - binom_cdf(target - 1, n, p)


def simulate_auroc_ci(
    n: int, p_neg: float, true_auc: float, n_sim: int = SIM_N, seed: int = SIM_SEED
) -> dict[str, Any]:
    """Bootstrap 95% CI width for AUROC under a latent-score model.

    Latent risk X|Y=1 ~ N(mu_pos, 1), X|Y=0 ~ N(mu_neg, 1); AUC = Phi((mu_pos-mu_neg)/sqrt(2)).
    """
    rng = np.random.default_rng(seed)
    d = math.sqrt(2) * _inv_normal_cdf(true_auc)
    mu_neg = 0.0
    mu_pos = d
    aucs: list[float] = []
    for _ in range(n_sim):
        n_pos = int(rng.binomial(n, 1 - p_neg))
        n_neg = n - n_pos
        if n_pos < 1 or n_neg < 1:
            aucs.append(0.5)
            continue
        xs_pos = rng.normal(mu_pos, 1.0, size=n_pos).tolist()
        xs_neg = rng.normal(mu_neg, 1.0, size=n_neg).tolist()
        aucs.append(_auc_from_samples(xs_pos, xs_neg))
    arr = np.asarray(aucs)
    return {
        "true_auc": true_auc,
        "mean_auc": round(float(np.mean(arr)), 4),
        "sd": round(float(np.std(arr)), 4),
        "ci95_width": round(float(np.percentile(arr, 97.5) - np.percentile(arr, 2.5)), 4),
    }


def _inv_normal_cdf(p: float) -> float:
    from scipy.stats import norm

    return float(norm.ppf(p))


def _auc_from_samples(pos: list[float], neg: list[float]) -> float:
    from sklearn.metrics import roc_auc_score

    y = [1] * len(pos) + [0] * len(neg)
    x = pos + neg
    if len(set(y)) < 2 or np.std(x) == 0:
        return 0.5
    return float(roc_auc_score(y, x))


def auprc_effect(p_neg: float, auc: float) -> float:
    """AUPRC under a binormal latent model (computed by simulation)."""
    d = math.sqrt(2) * _inv_normal_cdf(auc)
    rng = np.random.default_rng(7)
    n = 200000
    n_pos = int(n * (1 - p_neg))
    n_neg = n - n_pos
    pos = rng.normal(d, 1.0, size=n_pos).tolist()
    neg = rng.normal(0.0, 1.0, size=n_neg).tolist()
    order = sorted(range(n), key=lambda i: (pos + neg)[i], reverse=True)
    tp = 0
    cum = 0.0
    total_pos = len(pos)
    for i in order:
        is_pos = i < len(pos)
        if is_pos:
            tp += 1
        cum += tp / (i + 1)
    return cum / total_pos if total_pos else 0.0


def main() -> int:
    rows: list[dict[str, Any]] = []
    sim_cache: dict[tuple[float, float], dict[str, Any]] = {}
    for p_neg in NEG_PREV_GRID:
        for n in N_GRID:
            exp_neg = n * p_neg
            p_ge10 = prob_at_least(n, p_neg, 10)
            p_ge20 = prob_at_least(n, p_neg, 20)
            cells = n * REPS
            tokens = TOKENS_PER_TASK_3REP * n
            cost = COST_PER_TASK_3REP * n
            auprc_base = 1 - p_neg
            row: dict[str, Any] = {
                "p_neg": round(p_neg, 4),
                "p_neg_label": "observed" if abs(p_neg - OBSERVED_NEG_PREV) < 1e-9 else f"{p_neg:.0%}",
                "n": n,
                "expected_negatives": round(exp_neg, 2),
                "expected_positives": round(n - exp_neg, 2),
                "P_neg_ge_10": round(p_ge10, 4),
                "P_neg_ge_20": round(p_ge20, 4),
                "cells_3rep": cells,
                "tokens_3rep": round(tokens),
                "cost_3rep_usd": round(cost, 4),
                "within_cell_ceiling": cells <= CELL_CEILING,
                "within_token_ceiling": tokens <= TOKEN_CEILING,
                "within_cost_ceiling": cost <= COST_CEILING,
                "auprc_random_baseline": round(auprc_base, 4),
            }
            aucs: list[dict[str, Any]] = []
            for auc in EFFECT_AUROC:
                key = (round(p_neg, 4), n, auc)
                if key not in sim_cache:
                    sim_cache[key] = simulate_auroc_ci(n, p_neg, auc)
                aucs.append(sim_cache[key])
            row["auroc_ci_simulation"] = aucs
            rows.append(row)

    # Ceiling-limited max tasks at the observed prevalence.
    max_by_cells = CELL_CEILING // REPS
    max_by_tokens = int(TOKEN_CEILING // TOKENS_PER_TASK_3REP)
    max_by_cost = int(COST_CEILING // COST_PER_TASK_3REP)
    max_tasks_auth = min(max_by_cells, max_by_tokens, max_by_cost)

    summary = {
        "observed_development": {
            "n": OBSERVED_N,
            "positive": OBSERVED_POS,
            "negative": OBSERVED_NEG,
            "negative_prevalence": round(OBSERVED_NEG_PREV, 4),
        },
        "authorized_ceilings": {
            "max_new_cells": CELL_CEILING,
            "max_new_tokens": TOKEN_CEILING,
            "max_new_cost_usd": COST_CEILING,
        },
        "max_new_tasks_within_authorization_3rep": max_tasks_auth,
        "max_by_cells": max_by_cells,
        "max_by_tokens": max_by_tokens,
        "max_by_cost": max_by_cost,
        "cost_basis": {
            "tokens_per_task_3rep": round(TOKENS_PER_TASK_3REP),
            "cost_per_task_3rep_usd": round(COST_PER_TASK_3REP, 6),
            "source": "90-cell Sparse-v2 development run (frozen pricing)",
        },
        "recommendation": (
            "At the observed 13.3% negative prevalence, N=120 new V2 development "
            "tasks (360 cells) yields ~16 expected negatives (P(neg>=10) high, "
            "P(neg>=20) modest) within the authorized ceilings (360<=450 cells, "
            "~1.96M<=2.5M tokens, ~$0.74<=$1.00). N=150 yields ~20 negatives "
            "(450 cells, ~2.45M tokens, ~$0.92) at the cost ceiling boundary. "
            "Under more pessimistic 10% prevalence, N=150 is needed for ~15 "
            "negatives. Under 5% prevalence no N<=450 is sufficient for >=20 "
            "negatives; >=10 needs ~N=230. Choose N based on the frozen sampling "
            "frame once the git cache permits reconstruction; do NOT pick a round "
            "number."
        ),
    }

    (OUT_JSON.parent).mkdir(parents=True, exist_ok=True)
    (OUT_JSON).write_text(json.dumps({"summary": summary, "rows": rows}, indent=2), encoding="utf-8")

    # Markdown report
    md = [
        "# RealCommitImpactDataset-v2 — Sample-Size / Power Analysis",
        "",
        "**Date:** 2026-09-16",
        "**Status:** DEVELOPMENT-PLANNING ONLY. Uses observed development evidence;",
        "no V2 TEST/RESERVE tuning.",
        "",
        "## 1. Observed development evidence (frozen)",
        "",
        f"- Sparse-v2 `has_fn` on the 30 v1 development tasks: positive "
        f"{OBSERVED_POS} / negative {OBSERVED_NEG} → negative prevalence "
        f"{OBSERVED_NEG_PREV:.1%}.",
        f"- Cost basis (frozen 90-cell Sparse-v2 run): {TOKENS_90:,} tokens / "
        f"${COST_90:.4f} → ~{TOKENS_PER_TASK_3REP:.0f} tokens and "
        f"~${COST_PER_TASK_3REP:.4f} per task at 3 nested reps.",
        "",
        "## 2. Method",
        "",
        "- Sensitivity over negative prevalence 5%, 10%, 13.3% (observed), 15%, 20%, 25%.",
        "- For each (prevalence, N): expected negatives; P(neg ≥ 10); P(neg ≥ 20) (binomial CDF);",
        "  simulated AUROC bootstrap 95% CI width under true AUC ∈ {0.60, 0.70, 0.80} (binormal",
        "  latent-score model, 2000 bootstrap resamples); AUPRC random baseline = 1 − prevalence;",
        "  3-rep Sparse cost (cells/tokens/cost) vs the authorized ceilings.",
        "- The analysis uses only development information for PLANNING; it never tunes a test.",
        "",
        "## 3. Key table (abridged; full JSON in research/transparency/v2_sample_size.json)",
        "",
        "| p(neg) | N | exp neg | P(≥10) | P(≥20) | cells | tokens | cost $ | AUROC CI width @0.7 |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        if r["n"] in (120, 150, 230) and r["p_neg"] in (0.10, OBSERVED_NEG_PREV, 0.20):
            w70 = next(x["ci95_width"] for x in r["auroc_ci_simulation"] if x["true_auc"] == 0.70)
            md.append(
                f"| {r['p_neg_label']} | {r['n']} | {r['expected_negatives']:.0f} | "
                f"{r['P_neg_ge_10']:.2f} | {r['P_neg_ge_20']:.2f} | {r['cells_3rep']} | "
                f"{r['tokens_3rep']:,} | {r['cost_3rep_usd']:.2f} | {w70:.3f} |"
            )
    md += [
        "",
        "## 4. Ceiling-limited capacity",
        "",
        f"- Max NEW tasks within authorization (3 reps): **{max_tasks_auth}**",
        f"  (cells ≤ {max_by_cells}, tokens ≤ {max_by_tokens}, cost ≤ {max_by_cost}).",
        "",
        "## 5. Recommendation",
        "",
        summary["recommendation"],
        "",
        "**Rule:** do NOT select N because it is round; choose it from the frozen",
        "sampling frame once the git cache permits reconstructing the eligible pool.",
    ]
    (OUT_MD).write_text("\n".join(md), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print("outputs:", OUT_JSON, OUT_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
