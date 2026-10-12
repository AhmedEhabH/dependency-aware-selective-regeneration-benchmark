#!/usr/bin/env python3
# ruff: noqa: E501
"""M17_COMP_BASELINES_R2 — paired cluster bootstrap statistics.

RM-CSS vs EVERY pre-specified direct headline variant (BM25@1/3/5/10,
DENSE@1/3/5/10) plus the SIZE_MATCHED controls (BM25_SIZE_MATCHED,
DENSE_SIZE_MATCHED), with identical paired-cluster-bootstrap mechanics to the
frozen MAIN_297 analysis (task is the resampling unit; 10,000 resamples;
seed 20261012 recorded in the protocol freeze).

Statistics per comparison:
  Delta F1_micro = F1_micro(RM-CSS) - F1_micro(baseline)
  Delta Recall   = Recall(RM-CSS)  - Recall(baseline)
95% percentile CIs [q025, q975] + point estimates of both deltas.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parent.parent

METRICS = PROJECT / "research" / "competitor-baselines-r2" / "per_task_metrics_r2.json"
OUT = PROJECT / "research" / "competitor-baselines-r2" / "paired_bootstrap_r2.json"

N_RESAMPLES = 10_000
SEED = 20261012

DIRECT_VARIANTS = ["BM25@1", "BM25@3", "BM25@5", "BM25@10",
                   "DENSE@1", "DENSE@3", "DENSE@5", "DENSE@10"]
CONTROLLED_VARIANTS = ["BM25_SIZE_MATCHED", "DENSE_SIZE_MATCHED"]


def bootstrap_indices(n: int, *, n_resamples: int = N_RESAMPLES, seed: int = SEED) -> np.ndarray:
    rng = random.Random(seed)
    draws = np.empty((n_resamples, n), dtype=np.int64)
    for b in range(n_resamples):
        draws[b] = [rng.randrange(n) for _ in range(n)]
    return draws


def _f1(tp, fp, fn):
    den = 2 * tp + fp + fn
    if isinstance(den, np.ndarray):
        return np.where(den > 0, 2 * tp / np.where(den > 0, den, 1.0), 0.0)
    return 2 * tp / den if den else 0.0


def _recall(tp, fn):
    if isinstance(tp, np.ndarray):
        s = tp + fn
        return np.where(s > 0, tp / np.where(s > 0, s, 1.0), 0.0)
    return tp / (tp + fn) if (tp + fn) else 0.0


def main() -> int:
    data = json.loads(METRICS.read_text(encoding="utf-8"))
    per_task = data["per_task"]
    task_ids = sorted(per_task.keys())
    n = len(task_ids)
    assert n == 297, n

    def comps(arm: str) -> np.ndarray:
        arr = np.zeros((n, 3), dtype=np.float64)
        for i, t in enumerate(task_ids):
            c = per_task[t][f"{arm}_confusion"]
            arr[i] = (c["tp"], c["fp"], c["fn"])
        return arr

    rmcss = comps("RM-CSS")
    draws = bootstrap_indices(n)

    def delta_distribution(base: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        # returns (delta_f1, delta_recall) arrays over resamples; base = baseline per-task comps
        b_sub = base[draws]       # (B, n, 3)
        r_sub = rmcss[draws]      # (B, n, 3)
        r_tp, r_fp, r_fn = r_sub[:, :, 0], r_sub[:, :, 1], r_sub[:, :, 2]
        b_tp, b_fp, b_fn = b_sub[:, :, 0], b_sub[:, :, 1], b_sub[:, :, 2]
        r_f1 = _f1(r_tp.sum(axis=1), r_fp.sum(axis=1), r_fn.sum(axis=1))
        b_f1 = _f1(b_tp.sum(axis=1), b_fp.sum(axis=1), b_fn.sum(axis=1))
        r_rec = _recall(r_tp.sum(axis=1), r_fn.sum(axis=1))
        b_rec = _recall(b_tp.sum(axis=1), b_fn.sum(axis=1))
        return r_f1 - b_f1, r_rec - b_rec

    def point_delta(arm: str) -> tuple[float, float]:
        b = comps(arm)
        r_tp, r_fp, r_fn = rmcss[:, 0].sum(), rmcss[:, 1].sum(), rmcss[:, 2].sum()
        b_tp, b_fp, b_fn = b[:, 0].sum(), b[:, 1].sum(), b[:, 2].sum()
        return (_f1(r_tp, r_fp, r_fn) - _f1(b_tp, b_fp, b_fn),
                _recall(r_tp, r_fn) - _recall(b_tp, b_fn))

    results: dict = {
        "n_tasks": n,
        "n_resamples": N_RESAMPLES,
        "seed": SEED,
        "method": "paired cluster bootstrap over tasks; per-sample pooled micro confusion recomputed from the resampled tasks, then micro F1 and micro Recall",
        "comparisons": {"direct": DIRECT_VARIANTS, "size_matched_controls": CONTROLLED_VARIANTS},
        "rows": {},
    }
    for arm in DIRECT_VARIANTS + CONTROLLED_VARIANTS:
        d_f1, d_rec = delta_distribution(comps(arm))
        p_f1, p_rec = point_delta(arm)
        results["rows"][arm] = {
            "label": "DIRECT_SAME_PROTOCOL" if arm in DIRECT_VARIANTS else "SIZE_MATCHED_CONTROL",
            "delta_f1_micro": {
                "point": p_f1,
                "q025": float(np.quantile(d_f1, 0.025)),
                "q975": float(np.quantile(d_f1, 0.975)),
                "ci_crosses_zero": bool((np.quantile(d_f1, 0.025) < 0) and (np.quantile(d_f1, 0.975) > 0)),
            },
            "delta_recall": {
                "point": p_rec,
                "q025": float(np.quantile(d_rec, 0.025)),
                "q975": float(np.quantile(d_rec, 0.975)),
                "ci_crosses_zero": bool((np.quantile(d_rec, 0.025) < 0) and (np.quantile(d_rec, 0.975) > 0)),
            },
        }
        print(f"{arm:22s} dF1={p_f1:+.4f} [{results['rows'][arm]['delta_f1_micro']['q025']:+.4f}, "
              f"{results['rows'][arm]['delta_f1_micro']['q975']:+.4f}]   "
              f"dRecall={p_rec:+.4f} [{results['rows'][arm]['delta_recall']['q025']:+.4f}, "
              f"{results['rows'][arm]['delta_recall']['q975']:+.4f}]")

    OUT.write_text(json.dumps(results, indent=1, sort_keys=True), encoding="utf-8")
    print("wrote:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
