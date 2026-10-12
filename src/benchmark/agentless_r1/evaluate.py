"""Agentless-style evaluate: freeze predictions, then load gold and score.

All 297-per-task predictions are assembled into a prediction artifact and
SHA-256 sidecarred BEFORE the gold proxies artifact is opened. Scoring uses the
exact same file-level evaluator as RM-CSS / SIP / Agent on MAIN_297
(``benchmark.wp1a.scorer`` per_task_confusion / ArmConfusion +
``benchmark.wp1b.main_scoring`` pooled()).

Statistics: paired cluster bootstrap over tasks, 10,000 resamples, seed
20261012 (frozen in the protocol freeze, same mechanics as R2 / MAIN_297).
"""

from __future__ import annotations

import hashlib
import json
import random
import statistics
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np

from benchmark.wp1a.scorer import ArmConfusion, per_task_confusion

N_RESAMPLES: int = 10_000
BOOTSTRAP_SEED: int = 20261012


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json_lf(path: Path, payload: Any) -> None:
    path.write_bytes((json.dumps(payload, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8"))


def freeze_predictions(
    per_task: Mapping[str, Mapping[str, Any]],
    task_ids: Sequence[str],
    output_json: Path,
    sidecar_txt: Path,
) -> Path:
    """Write the prediction freeze and its .sha256 sidecar (LF canonical)."""
    payload = {
        "records": [{"task_id": tid, **per_task[tid]} for tid in task_ids],
        "n_tasks": len(task_ids),
    }
    text = json.dumps(payload, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    output_json.write_bytes(text.encode("utf-8"))
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    sidecar_txt.write_text(digest + "\n", encoding="utf-8")
    return output_json


def load_prediction_sets(path: Path, task_ids: Sequence[str]) -> dict[str, frozenset[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    preds: dict[str, frozenset[str]] = {}
    for tid in task_ids:
        entry = next(r for r in data["records"] if r["task_id"] == tid)
        preds[tid] = frozenset(str(p) for p in entry["prediction_set"])
    return preds


def load_gold(path: Path) -> dict[str, frozenset[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("opened_once") is not True:
        raise ValueError("gold proxies artifact is not the opened-once RESERVE-300 set")
    return {t: frozenset(v) for t, v in data["proxies"].items()}


def compute_confusions(
    preds: Mapping[str, frozenset[str]],
    gold: Mapping[str, frozenset[str]],
    task_ids: Sequence[str],
) -> dict[str, ArmConfusion]:
    return {t: per_task_confusion(set(preds.get(t, frozenset())), set(gold[t])) for t in task_ids}


def pooled_metrics(confusions: Sequence[ArmConfusion]) -> dict[str, float | int]:
    tp = sum(c.tp for c in confusions)
    fp = sum(c.fp for c in confusions)
    fn = sum(c.fn for c in confusions)
    den_p = tp + fp
    den_r = tp + fn
    den_f = 2 * tp + fp + fn
    return {
        "tp": tp, "fp": fp, "fn": fn,
        "precision": tp / den_p if den_p else 0.0,
        "recall": tp / den_r if den_r else 0.0,
        "fnr": fn / den_r if den_r else 0.0,
        "f1": 2 * tp / den_f if den_f else 0.0,
    }


def size_statistics(sizes: Sequence[int]) -> dict[str, float | int]:
    if not sizes:
        return {"mean": 0.0, "median": 0.0, "min": 0, "max": 0}
    return {
        "mean": statistics.fmean(sizes),
        "median": statistics.median(sizes),
        "min": min(sizes),
        "max": max(sizes),
    }


def bootstrap_indices(n: int, *, n_resamples: int = N_RESAMPLES, seed: int = BOOTSTRAP_SEED) -> np.ndarray:
    rng = random.Random(seed)
    draws = np.empty((n_resamples, n), dtype=np.int64)
    for b in range(n_resamples):
        draws[b] = [rng.randrange(n) for _ in range(n)]
    return draws


def _comp_array(
    comps: Mapping[str, ArmConfusion], task_ids: Sequence[str], draws: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    arr = np.array([[comps[t].tp, comps[t].fp, comps[t].fn] for t in task_ids], dtype=np.float64)
    sums = arr[draws].sum(axis=1)
    return sums[:, 0], sums[:, 1], sums[:, 2]


def delta_f1_and_recall(
    a_comps: Mapping[str, ArmConfusion],
    b_comps: Mapping[str, ArmConfusion],
    task_ids: Sequence[str],
) -> dict[str, float]:
    draws = bootstrap_indices(len(task_ids))
    a_tp, a_fp, a_fn = _comp_array(a_comps, task_ids, draws)
    b_tp, b_fp, b_fn = _comp_array(b_comps, task_ids, draws)
    a_den = 2 * a_tp + a_fp + a_fn
    b_den = 2 * b_tp + b_fp + b_fn
    a_f1 = np.where(a_den > 0, 2 * a_tp / np.where(a_den > 0, a_den, 1.0), 0.0)
    b_f1 = np.where(b_den > 0, 2 * b_tp / np.where(b_den > 0, b_den, 1.0), 0.0)
    a_r_den = a_tp + a_fn
    b_r_den = b_tp + b_fn
    a_rec = np.where(a_r_den > 0, a_tp / np.where(a_r_den > 0, a_r_den, 1.0), 0.0)
    b_rec = np.where(b_r_den > 0, b_tp / np.where(b_r_den > 0, b_r_den, 1.0), 0.0)
    d_f1 = a_f1 - b_f1
    d_rec = a_rec - b_rec
    a_p = pooled_metrics(list(a_comps.values()))
    b_p = pooled_metrics(list(b_comps.values()))
    return {
        "delta_f1_point": float(a_p["f1"] - b_p["f1"]),
        "delta_f1_q025": float(np.quantile(d_f1, 0.025)),
        "delta_f1_q975": float(np.quantile(d_f1, 0.975)),
        "delta_recall_point": float(a_p["recall"] - b_p["recall"]),
        "delta_recall_q025": float(np.quantile(d_rec, 0.025)),
        "delta_recall_q975": float(np.quantile(d_rec, 0.975)),
        "n_resamples": N_RESAMPLES,
        "seed": BOOTSTRAP_SEED,
    }
