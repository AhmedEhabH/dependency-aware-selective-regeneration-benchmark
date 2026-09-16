#!/usr/bin/env python3
"""Saleor Stage-2 sample-size analysis (zero scientific calls, development planning).

Uses the reconstructed Saleor sampling frame (1316 independent eligible) and
the djangoCMS development negative-prevalence sensitivity (5-25%) to recommend
a Saleor development N. Never tunes a test.

Outputs:
- reports/SALEOR_SAMPLE_SIZE_ANALYSIS.md
- research/transparency/saleor_sample_size.json
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))

FRAME = _PROJECT_DIR / "research" / "transparency" / "saleor_sampling_frame_reconstructed.json"
OUT_JSON = _PROJECT_DIR / "research" / "transparency" / "saleor_sample_size.json"
OUT_MD = _PROJECT_DIR / "reports" / "SALEOR_SAMPLE_SIZE_ANALYSIS.md"

# djangoCMS observed development negative prevalence (development evidence only).
OBSERVED_NEG_PREV = 13.3 / 100.0
NEG_GRID = (0.05, 0.10, OBSERVED_NEG_PREV, 0.15, 0.20, 0.25)
N_GRID = (60, 90, 120, 150, 200, 300, 400, 600)

# djangoCMS 3-rep Sparse inference cost basis (frozen 90-cell + V2 runs).
# V2: 144 tasks / 2,501,964 tokens / $0.8728 -> per-task (3 reps) ~17,374 tokens / $0.0061.
TOKENS_PER_TASK = 17374
COST_PER_TASK = 0.00606


def binom_cdf(k, n, p):
    return sum(math.comb(n, i) * (p**i) * ((1 - p) ** (n - i)) for i in range(k + 1))


def prob_at_least(n, p, target):
    return 1.0 - binom_cdf(target - 1, n, p)


def main() -> int:
    frame = json.loads(FRAME.read_text(encoding="utf-8"))
    eligible = frame["independent_eligible_pool"]["n"]
    rows = []
    for p_neg in NEG_GRID:
        for n in N_GRID:
            rows.append(
                {
                    "p_neg": round(p_neg, 4),
                    "p_neg_label": "observed" if abs(p_neg - OBSERVED_NEG_PREV) < 1e-9 else f"{p_neg:.0%}",
                    "n": n,
                    "expected_neg": round(n * p_neg, 1),
                    "P_neg_ge_10": round(prob_at_least(n, p_neg, 10), 4),
                    "P_neg_ge_20": round(prob_at_least(n, p_neg, 20), 4),
                    "tokens_3rep": round(n * TOKENS_PER_TASK),
                    "cost_3rep_usd": round(n * COST_PER_TASK, 2),
                    "within_450_cells": (3 * n) <= 450,
                }
            )
    # Recommendation at observed prevalence.
    rec = {}
    for target in (10, 20):
        for n in N_GRID:
            if prob_at_least(n, OBSERVED_NEG_PREV, target) >= 0.8:
                rec[f"n_for_P_ge{target}_0.8"] = n
                break
    result = {
        "eligible_pool": eligible,
        "recommendation": {
            **rec,
            "n_120_negatives_observed": round(120 * OBSERVED_NEG_PREV, 1),
            "n_150_negatives_observed": round(150 * OBSERVED_NEG_PREV, 1),
            "note": (
                "Saleor eligible pool (1316) >> djangoCMS (329); N=120-150 Saleor "
                "development tasks is comfortably within the pool and the "
                "450-cell/2.5M-token/$1.00 ceiling pattern."
            ),
        },
        "rows": rows,
    }
    OUT_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")

    md = [
        "# Saleor Stage-2 — Sample-Size Analysis",
        "",
        f"**Date:** 2026-09-16  **Eligible pool:** {eligible} (reconstructed).",
        "Uses djangoCMS development negative-prevalence sensitivity; NEVER tunes a test.",
        "",
        "## Key rows (observed prevalence 13.3%)",
        "",
        "| N | exp neg | P(>=10) | P(>=20) | 3-rep tokens | 3-rep cost $ | <=450 cells |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        if r["p_neg_label"] == "observed" and r["n"] in (120, 150, 200, 300):
            md.append(
                f"| {r['n']} | {r['expected_neg']:.0f} | {r['P_neg_ge_10']:.2f} | "
                f"{r['P_neg_ge_20']:.2f} | {r['tokens_3rep']:,} | {r['cost_3rep_usd']:.2f} | {r['within_450_cells']} |"
            )
    md += [
        "",
        "## Recommendation",
        "",
        result["recommendation"]["note"],
        "",
        "Saleor's eligible pool (1316) is 4x djangoCMS's (329), so a quantitative",
        "Stage-2 development set (e.g. N=120-150) plus an untouched internal test",
        "is fully supported without consuming the pool.",
    ]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print("eligible_pool", eligible)
    print("recommendation", json.dumps(result["recommendation"], indent=1))
    print("outputs:", OUT_JSON, OUT_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
