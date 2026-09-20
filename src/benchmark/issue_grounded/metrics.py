"""Issue-grounded intent headroom - headroom metrics (T3).

Frozen metric definitions:

- target-file Recall@K = (# proxy-changed target files ranked within top K) /
  (# proxy-changed target files), over the FULL dense universe (incl. Sparse).
- task coverage@K = task has >=1 proxy target in top K.
- median target-file rank; mean reciprocal rank (1/rank per proxy file, 0 when
  absent); rank distribution; top-K candidate precision (proxy fraction of top
  K candidate files); exact rank movement per target file.
- task-paired bootstrap (>=10,000 resamples, seed 20260920) for Delta Recall@K
  and the primary gate.

All functions are pure given (proxy files per task, dense ranks per task).
"""
from __future__ import annotations

import random
import statistics
from typing import Any

RECALL_K = (1, 3, 5, 10, 20)
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20260920


def recall_at_k(proxy_ranked_positions: list[int | None], k: int) -> float:
    """Recall@K over a task's proxy target files.

    proxy_ranked_positions[i] = dense rank (1-based) of proxy file i, or None
    when the file has no dense rank in the universe (cannot be counted).
    """
    eligible = [p for p in proxy_ranked_positions if p is not None]
    if not eligible:
        return 0.0
    return sum(1 for p in eligible if p <= k) / len(eligible)


def task_coverage_at_k(proxy_ranked_positions: list[int | None], k: int) -> int:
    eligible = [p for p in proxy_ranked_positions if p is not None]
    return int(any(p <= k for p in eligible))


def mrr(proxy_ranked_positions: list[int | None]) -> float:
    eligible = [p for p in proxy_ranked_positions if p is not None]
    if not eligible:
        return 0.0
    return sum(1.0 / p for p in eligible) / len(eligible)


def median_rank(proxy_ranked_positions: list[int | None]) -> float | None:
    eligible = [p for p in proxy_ranked_positions if p is not None]
    if not eligible:
        return None
    return float(statistics.median(eligible))


def candidate_precision_at_k(dense_ranks: dict[str, int], proxy: set[str], k: int) -> float:
    """Top-K candidate precision: proxy fraction of the top K candidate files."""
    top = sorted(dense_ranks.items(), key=lambda kv: (kv[1], kv[0]))[:k]
    if not top:
        return 0.0
    return sum(1 for p, _ in top if p in proxy) / len(top)


def _task_positions(
    tasks: list[dict[str, Any]],
    dense_ranks_by_task: dict[str, dict[str, int]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for t in tasks:
        ranks = dense_ranks_by_task.get(t["case_id"], {})
        positions = [ranks.get(p) for p in t["proxy"]]
        out.append(
            {
                "case_id": t["case_id"],
                "repository": t["repository"],
                "proxy_positions": positions,
                "proxy_size": len(t["proxy"]),
            }
        )
    return out


def pooled_recall_at_k(task_positions: list[dict[str, Any]], k: int) -> float:
    """Pooled Recall@K over all tasks (File-level)."""
    hits = sum(1 for t in task_positions for p in t["proxy_positions"] if p is not None and p <= k)
    total = sum(1 for t in task_positions for p in t["proxy_positions"] if p is not None)
    return hits / total if total else 0.0


def macro_recall_at_k(task_positions: list[dict[str, Any]], k: int) -> float:
    if not task_positions:
        return 0.0
    return sum(recall_at_k(t["proxy_positions"], k) for t in task_positions) / len(task_positions)


def paired_bootstrap_delta(
    task_m: list[dict[str, Any]],
    task_i: list[dict[str, Any]],
    k: int,
    n_resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, float]:
    """Task-paired bootstrap for Delta Recall@K (macro, task unit).

    Returns: point_delta, ci_lower, ci_upper, mean, std, n_boot.
    """
    assert len(task_m) == len(task_i)
    n = len(task_m)
    rng = random.Random(seed)
    raw_m = [recall_at_k(t["proxy_positions"], k) for t in task_m]
    raw_i = [recall_at_k(t["proxy_positions"], k) for t in task_i]
    deltas = [i - m for m, i in zip(raw_m, raw_i, strict=True)]
    point = sum(deltas) / n if n else 0.0

    if n == 0:
        return {"point_delta": 0.0, "ci_lower": 0.0, "ci_upper": 0.0,
                "mean": 0.0, "std": 0.0, "n_boot": 0, "n_tasks": 0}

    boot: list[float] = []
    for _ in range(n_resamples):
        sample = [deltas[rng.randrange(n)] for _ in range(n)]
        boot.append(sum(sample) / n)
    boot.sort()
    lo = boot[int(0.025 * n_resamples)]
    hi = boot[int(0.975 * n_resamples)]
    return {
        "point_delta": round(point, 6),
        "ci_lower": round(lo, 6),
        "ci_upper": round(hi, 6),
        "mean": round(statistics.mean(boot), 6),
        "std": round(statistics.stdev(boot), 6),
        "n_boot": n_resamples,
        "n_tasks": n,
    }


def gates_for_repo(
    task_m: list[dict[str, Any]],
    task_i: list[dict[str, Any]],
    k: int = 20,
) -> dict[str, Any]:
    """Frozen gate criteria A-D per repository (pooled Recall@K definition)."""
    rm = pooled_recall_at_k(task_m, k)
    ri = pooled_recall_at_k(task_i, k)
    boot = paired_bootstrap_delta(task_m, task_i, k)
    med_m = _pooled_median_rank(task_m)
    med_i = _pooled_median_rank(task_i)

    # C: median target-file rank improves or stays equal (pooled). If the
    # pooled median is undefined (no ranked proxy files), treat as not violated
    # ONLY when both arms are empty; otherwise the criterion is not met.
    if med_m is None and med_i is None:
        c = True
    elif med_m is None or med_i is None:
        c = False
    else:
        c = med_i <= med_m

    return {
        "k": k,
        "recall_m": round(rm, 6),
        "recall_i": round(ri, 6),
        "A_recall_i_gt_recall_m": bool(ri > rm),
        "B_ci_lower_gt_0": bool(boot["ci_lower"] > 0),
        "C_median_rank_improves_or_equal": bool(c),
        "median_rank_m": med_m,
        "median_rank_i": med_i,
        "bootstrap": boot,
    }


def _pooled_median_rank(task_positions: list[dict[str, Any]]) -> float | None:
    all_ranks = [p for t in task_positions for p in t["proxy_positions"] if p is not None]
    if not all_ranks:
        return None
    return float(statistics.median(all_ranks))


def rank_movement_distribution(
    task_m: list[dict[str, Any]],
    task_i: list[dict[str, Any]],
) -> dict[str, Any]:
    """Exact per-target-file rank movement (message->issue)."""
    moves: list[int] = []
    for tm, ti in zip(task_m, task_i, strict=True):
        for pm, pi in zip(tm["proxy_positions"], ti["proxy_positions"], strict=True):
            if pm is None or pi is None:
                continue
            moves.append(pi - pm)
    if not moves:
        return {"n_moved": 0, "improved": 0, "worsened": 0, "unchanged": 0}
    return {
        "n_moved": len(moves),
        "improved": sum(1 for m in moves if m < 0),
        "worsened": sum(1 for m in moves if m > 0),
        "unchanged": sum(1 for m in moves if m == 0),
        "median_change": statistics.median(moves),
        "mean_change": round(statistics.mean(moves), 4),
    }


def recall_k_table(task_positions: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for k in RECALL_K:
        out[f"Recall@{k}"] = {
            "pooled": pooled_recall_at_k(task_positions, k),
            "macro": macro_recall_at_k(task_positions, k),
        }
    out["coverage"] = {}
    for k in (1, 3, 5, 10, 20):
        cov = sum(task_coverage_at_k(t["proxy_positions"], k) for t in task_positions)
        out["coverage"][f"@{k}"] = round(cov / len(task_positions), 6) if task_positions else 0.0
    mrr_vals = [mrr(t["proxy_positions"]) for t in task_positions if t["proxy_positions"]]
    if mrr_vals:
        out["mrr"] = {"mean": round(statistics.mean(mrr_vals), 6), "n": len(mrr_vals)}
    else:
        out["mrr"] = {"mean": 0.0, "n": 0}
    meds = [median_rank(t["proxy_positions"]) for t in task_positions if t["proxy_positions"]]
    if meds:
        out["median_rank"] = {"mean": round(statistics.mean(meds), 4), "n": len(meds)}
    else:
        out["median_rank"] = {"mean": None, "n": 0}
    out["n_tasks"] = float(len(task_positions))
    return out
