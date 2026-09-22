"""WP-1b variance substudy (15 tasks x 3 fresh replicates) - preregistered metrics.

``docs/WP1B_VARIANCE_SUBSTUDY_PREREGISTRATION_2026-09-21.md``: the first main
execution does NOT count as replicate 1; the substudy estimates execution
variability and is NOT evidence equivalent to three MAIN_50 replications.
"""
from __future__ import annotations

import itertools
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

import numpy as np

from benchmark.wp1a.scorer import ArmConfusion, per_task_confusion


def _f1(c: ArmConfusion) -> float:
    return c.f1


def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def _var(xs: Sequence[float]) -> float:
    return float(np.var(np.asarray(xs, dtype=np.float64))) if len(xs) > 1 else 0.0


def _mean(xs: Iterable[float]) -> float:
    vals = list(xs)
    return float(np.mean(np.asarray(vals, dtype=np.float64))) if vals else 0.0


def score_variance(
    per_item: Mapping[str, Mapping[str, Any]],
    labels: Mapping[str, frozenset[str]],
    *,
    telemetry: Mapping[str, Mapping[str, Any]] | None = None,
    main_predictions: Mapping[str, frozenset[str]] | None = None,
) -> dict[str, Any]:
    """``per_item`` is the variance freeze ``per_task`` block keyed ``<task>#r<k>``."""
    by_task: dict[str, dict[int, Mapping[str, Any]]] = {}
    for key, entry in per_item.items():
        by_task.setdefault(str(entry["task_id"]), {})[int(entry["replicate"])] = dict(entry, work_key=key)
    reps = sorted({r for d in by_task.values() for r in d})
    tasks = sorted(by_task)
    per_task_rows: list[dict[str, Any]] = []
    pair_exact = 0
    pair_total = 0
    jaccards: list[float] = []
    all_identical = 0
    for tid in tasks:
        runs = by_task[tid]
        sets = {r: frozenset(runs[r]["selected_paths"]) for r in runs}
        f1s = [_f1(per_task_confusion(set(sets[r]), set(labels[tid]))) for r in sorted(runs)]
        for a, b in itertools.combinations(sorted(runs), 2):
            pair_total += 1
            pair_exact += int(sets[a] == sets[b])
            jaccards.append(_jaccard(sets[a], sets[b]))
        all_identical += int(len(set(sets.values())) == 1)
        row = {
            "task_id": tid,
            "f1_by_replicate": f1s,
            "f1_mean": _mean(f1s),
            "f1_range": max(f1s) - min(f1s),
            "size_variance": _var([len(s) for s in sets.values()]),
            "prompt_token_variance": _var([float(runs[r]["prompt_tokens"]) for r in runs]),
            "completion_token_variance": _var([float(runs[r]["completion_tokens"]) for r in runs]),
            "usd_variance": _var([float(runs[r]["usd_cost"]) for r in runs]),
            "latency_variance": _var([float(runs[r].get("latency_s_sum", 0.0)) for r in runs]),
            "calls_by_replicate": [int(runs[r]["model_calls"]) for r in sorted(runs)],
            "empty_by_replicate": [str(runs[r]["empty_reason"]) for r in sorted(runs)],
        }
        if main_predictions is not None and tid in main_predictions:
            row["jaccard_vs_main_run_descriptive"] = [
                _jaccard(sets[r], main_predictions[tid]) for r in sorted(runs)
            ]
        per_task_rows.append(row)

    pooled_by_rep: dict[str, float] = {}
    for r in reps:
        comps = [per_task_confusion(set(by_task[t][r]["selected_paths"]), set(labels[t]))
                 for t in tasks if r in by_task[t]]
        tp = sum(c.tp for c in comps)
        fp = sum(c.fp for c in comps)
        fn = sum(c.fn for c in comps)
        pooled_by_rep[str(r)] = ArmConfusion(tp, fp, fn).f1
    pooled_vals = list(pooled_by_rep.values())

    runs_flat = [e for d in by_task.values() for e in d.values()]
    cap_hits = 0
    if telemetry is not None:
        cap_hits = sum(int(t.get("cap_hit_count", 0)) for t in telemetry.values())
    return {
        "artifact": "wp1b_variance_substudy_result",
        "n_tasks": len(tasks),
        "replicates": reps,
        "n_runs": len(runs_flat),
        "aggregate_pooled_f1_by_replicate": pooled_by_rep,
        "aggregate_pooled_f1_mean": _mean(pooled_vals),
        "aggregate_pooled_f1_range": (max(pooled_vals) - min(pooled_vals)) if pooled_vals else 0.0,
        "per_task_f1_mean_of_ranges": _mean(r["f1_range"] for r in per_task_rows),
        "selected_set_exact_match_rate_pairwise": pair_exact / pair_total if pair_total else 0.0,
        "selected_set_all_replicates_identical_rate": all_identical / len(tasks) if tasks else 0.0,
        "selected_set_mean_pairwise_jaccard": _mean(jaccards),
        "mean_prediction_size_variance": _mean(r["size_variance"] for r in per_task_rows),
        "mean_prompt_token_variance": _mean(r["prompt_token_variance"] for r in per_task_rows),
        "mean_completion_token_variance": _mean(r["completion_token_variance"] for r in per_task_rows),
        "mean_usd_variance": _mean(r["usd_variance"] for r in per_task_rows),
        "mean_latency_variance": _mean(r["latency_variance"] for r in per_task_rows),
        "cap_hit_frequency": cap_hits,
        "final_answer_truncation_frequency": sum(1 for e in runs_flat if e["empty_reason"] == "truncation"),
        "empty_frequency": sum(1 for e in runs_flat if e["prediction_empty"]),
        "provider_route_frequency": "not observable per call; single pinned provider deepinfra/turbo with "
                                    "allow_fallbacks=false and require_parameters=true",
        "per_task": per_task_rows,
        "interpretation_boundary": "Execution variability only; NOT evidence equivalent to three complete "
                                   "MAIN_50 replications. The main execution is not replicate 1.",
    }
