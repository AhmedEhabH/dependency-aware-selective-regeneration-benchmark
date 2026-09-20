#!/usr/bin/env python3
"""PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2 — descriptive diagnostics (ZERO API).

Computes (frozen generator; NO model; labels used ONLY retrospectively):

  - DEEP_DENSE_MISS counts + dense-rank distribution (mission §3, verified);
  - dependency-cluster diagnostic (mission §4; oracle-style; NEVER inference
    seeds; NO graph features in V2);
  - deep-FN coverage report (mission §17): deep misses entering the memory
    candidate set (structural only / episodic only / both / union /
    unrecovered); also on tasks where Sparse is empty;
  - mechanism baselines (mission §18): historical-popularity (top NON-SPARSE by
    history_change_count) and seeded deterministic random (fixed seed 20260920,
    1000 repetitions) at the same candidate budget.

Outputs are DESCRIPTIVE. They are NOT used to tune K, support threshold,
memory features, or the history window.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))
sys.path.insert(0, str(_PROJECT_DIR / "scripts"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from benchmark.memory_rescue.history import CACHE_ROOT  # noqa: E402
from benchmark.recall.data import load_dev_tasks  # noqa: E402

OUT_DIR = _PROJECT_DIR / "research" / "memory-rescue-v2"
V1_FINALS = OUT_DIR.parent / "calibrated-set-selection-v1" / "final_oof_predictions_A.json"
V1_UNIVERSE = OUT_DIR.parent / "calibrated-set-selection-v1" / "candidate_universe_A.parquet"
MEMORY_CACHE = CACHE_ROOT / "memory_bundles.json"

RANDOM_SEED = 20260920
RANDOM_RESAMPLES = 1000


def _load_memory_sets() -> dict[str, dict]:
    raw = json.loads(MEMORY_CACHE.read_text(encoding="utf-8"))
    out = {}
    for cid, t in raw["tasks"].items():
        structural = set(t["variants"]["A"]["structural"])
        episodic = set(t["episodic"])
        out[cid] = {
            "structural": structural,
            "episodic": episodic,
            "union": structural | episodic,
            "history_change_count": {k: int(v) for k, v in t["history_change_count"].items()},
            "universe": (set(t["history_change_count"]) |
                         set(t["cochange_sparse"]) |
                         set(t["episode_similarity"])),
            "n_commits": int(t["n_production_changing_commits"]),
        }
    return out


def _v1_deep_misses(tasks, finals, universe, ranks) -> dict[str, list[str]]:
    """{repo: [(case_id, path)]} deep dense misses (frozen §3)."""
    univ = pd.read_parquet(universe)
    cand_by_task = univ.groupby("case_id")["file_path"].apply(set).to_dict()
    out: dict[str, list[tuple[str, str]]] = {"djangocms": [], "saleor": []}
    for t in tasks:
        sel = set(finals.get(t.case_id, []))
        cand = cand_by_task.get(t.case_id, set())
        for p in t.proxy:
            if p in sel:
                continue
            if p in cand:
                continue
            if (t.case_id, p) in ranks:
                out[t.repository].append((t.case_id, p))
    return out


def _dense_rank_map() -> dict[tuple[str, str], int]:
    scores = pd.read_parquet(
        _PROJECT_DIR / "research" / "contamination-bridge" / "qwen_embed"
        / "realization_A" / "full_file_scores.parquet")
    return {(r.case_id, r.file_path): int(r.dense_rank)
            for r in scores.itertuples(index=False)}


def deep_fn_coverage(tasks, deep_misses, mem_sets) -> dict:
    """Coverage of deep dense misses by the memory candidate set (frozen §17)."""
    out: dict[str, dict] = {}
    for repo in ("djangocms", "saleor"):
        entries = deep_misses[repo]
        structural_only = episodic_only = both = 0
        unrecovered = 0
        sparse_empty_recovered = sparse_empty_all = 0
        for cid, p in entries:
            m = mem_sets[cid]
            in_s = p in m["structural"]
            in_e = p in m["episodic"]
            if in_s and in_e:
                both += 1
            elif in_s:
                structural_only += 1
            elif in_e:
                episodic_only += 1
            else:
                unrecovered += 1
            t = next(t for t in tasks if t.case_id == cid)
            if not t.write_set:
                sparse_empty_all += 1
                if in_s or in_e:
                    sparse_empty_recovered += 1
        union_rec = structural_only + episodic_only + both
        out[repo] = {
            "n_deep_dense_misses": len(entries),
            "structural_only": structural_only,
            "episodic_only": episodic_only,
            "both": both,
            "union": union_rec,
            "unrecovered": unrecovered,
            "deep_fn_recovery_structural_only": round(structural_only / max(1, len(entries)), 4),
            "deep_fn_recovery_episodic_only": round(episodic_only / max(1, len(entries)), 4),
            "deep_fn_recovery_both": round(both / max(1, len(entries)), 4),
            "deep_fn_recovery_union": round(union_rec / max(1, len(entries)), 4),
            "sparse_empty_tasks_deep_misses": sparse_empty_all,
            "sparse_empty_tasks_recovered": sparse_empty_recovered,
            "sparse_empty_recovery_rate": round(sparse_empty_recovered / max(1, sparse_empty_all), 4),
        }
    return out


def popularity_baseline(tasks, deep_misses, mem_sets) -> dict:
    """Historical-popularity baseline: top NON-SPARSE by history_change_count.

    Same candidate budget (top-10 non-sparse per task, tie-break path
    ascending). Descriptive; NOT used to tune memory.
    """
    out: dict[str, dict] = {}
    for repo in ("djangocms", "saleor"):
        covered = 0
        for cid, p in deep_misses[repo]:
            m = mem_sets[cid]
            hcc = m["history_change_count"]
            universe = m["universe"]
            t = next(t for t in tasks if t.case_id == cid)
            non_sparse = [f for f in universe if f not in set(t.write_set)]
            pop = sorted(non_sparse, key=lambda f: (-hcc.get(f, 0), f))[:10]
            if p in set(pop):
                covered += 1
        n = len(deep_misses[repo])
        out[repo] = {"covered": covered, "n_deep_dense_misses": n,
                     "coverage_rate": round(covered / max(1, n), 4)}
    return out


def random_baseline(tasks, deep_misses, mem_sets) -> dict:
    """Seeded deterministic random baseline (mission §18).

    Same candidate count per task (top-10 non-sparse), fixed preregistered
    seed 20260920, 1000 resamples -> mean coverage + descriptive interval.
    """
    rng = random.Random(RANDOM_SEED)
    out: dict[str, dict] = {}
    for repo in ("djangocms", "saleor"):
        entries = deep_misses[repo]
        per_task: dict[str, list[str]] = {}
        for cid, p in entries:
            per_task.setdefault(cid, []).append(p)
        tasks_of = {t.case_id: t for t in tasks}
        pool: dict[str, list[str]] = {}
        for cid in per_task:
            m = mem_sets[cid]
            t = tasks_of[cid]
            universe = m["universe"]
            non_sparse = [f for f in universe if f not in set(t.write_set)]
            pool[cid] = non_sparse
        counts = []
        for _ in range(RANDOM_RESAMPLES):
            cov = 0
            for cid, positives in per_task.items():
                k = min(10, len(pool[cid]))
                pick = set(rng.sample(sorted(pool[cid]), k))
                cov += len(set(positives) & pick)
            counts.append(cov)
        arr = np.array(counts, dtype=np.float64)
        total = len(entries)
        out[repo] = {
            "n_resamples": RANDOM_RESAMPLES,
            "seed": RANDOM_SEED,
            "n_deep_dense_misses": total,
            "mean_covered": round(float(arr.mean()), 2),
            "mean_coverage_rate": round(float(arr.mean() / max(1, total)), 4),
            "ci95_covered": [round(float(np.percentile(arr, 2.5)), 2),
                             round(float(np.percentile(arr, 97.5)), 2)],
            "ci95_coverage_rate": [round(float(np.percentile(arr, 2.5) / max(1, total)), 4),
                                   round(float(np.percentile(arr, 97.5) / max(1, total)), 4)],
        }
    return out


def dependency_cluster_diagnostic(tasks, deep_misses, v1_finals) -> dict:
    """Descriptive oracle-style dependency-cluster diagnostic (mission §4).

    A. direct dependency/import relation to ANOTHER proxy-positive file from
       the same historical target change;
    B. directly adjacent (1 hop, undirected) to a V1-selected TRUE POSITIVE;
    C. within 2 hops (undirected) of a V1-selected TRUE POSITIVE.

    Oracle-style: uses evaluation labels ONLY for retrospective headroom
    analysis. NEVER inference seeds. NO graph features added to V2.
    """
    from benchmark.recall.data import (
        SALEOR_DATASET,
        V1_DATASET,
        V1_RECORDS,
        V2_DATASET,
        V2_RECORDS,
    )
    from scripts.route_b_v2_robustness import _load_run, load_case
    dataset_of = {}
    v1_cases = {r["case_id"] for r in _load_run(V1_RECORDS)}
    v2_cases = {r["case_id"] for r in _load_run(V2_RECORDS)}
    for cid, t in ((t.case_id, t) for t in tasks):
        repo = t.repository
        if repo == "djangocms":
            if cid in v1_cases:
                dataset_of[cid] = V1_DATASET
            elif cid in v2_cases:
                dataset_of[cid] = V2_DATASET
            else:
                raise RuntimeError(f"djangocms case {cid} not in v1/v2 records")
        else:
            dataset_of[cid] = SALEOR_DATASET

    def _adj(edges):
        adj = {}
        for s, d in edges:
            adj.setdefault(s, set()).add(d)
            adj.setdefault(d, set()).add(s)
        return adj

    out: dict[str, dict] = {}
    for repo in ("djangocms", "saleor"):
        entries = deep_misses[repo]
        a = b = c = 0
        for cid, p in entries:
            t = next(t for t in tasks if t.case_id == cid)
            case = load_case(cid, dataset_of[cid])
            adj = _adj(case["graph_edges"])
            proxy = set(t.proxy)
            v1_sel = set(v1_finals.get(cid, []))
            v1_tp = v1_sel & proxy
            # A: p shares a direct dependency/import relation with ANOTHER
            #    proxy-positive file from the same target change.
            neighbors = adj.get(p, set())
            if neighbors & (proxy - {p}):
                a += 1
            # B: p is directly adjacent (1 hop) to a V1-selected TP.
            if neighbors & v1_tp:
                b += 1
            # C: p is within 2 dependency hops of a V1-selected TP.
            two = set(neighbors)
            for n in neighbors:
                two.update(adj.get(n, set()))
            if two & v1_tp:
                c += 1
        n = len(entries)
        out[repo] = {
            "n_deep_dense_misses": n,
            "A_direct_relation_to_other_proxy_positive": a,
            "A_rate": round(a / max(1, n), 4),
            "B_adjacent_to_v1_true_positive": b,
            "B_rate": round(b / max(1, n), 4),
            "C_within_2_hops_of_v1_true_positive": c,
            "C_rate": round(c / max(1, n), 4),
        }
    return out


def main() -> int:
    tasks = load_dev_tasks()
    finals = json.loads(V1_FINALS.read_text(encoding="utf-8"))
    mem_sets = _load_memory_sets()
    ranks = _dense_rank_map()

    deep = _v1_deep_misses(tasks, finals, V1_UNIVERSE, ranks)
    coverage = deep_fn_coverage(tasks, deep, mem_sets)
    pop = popularity_baseline(tasks, deep, mem_sets)
    rnd = random_baseline(tasks, deep, mem_sets)
    dep = dependency_cluster_diagnostic(tasks, deep, finals)

    # deep-FN dense-rank distribution (mission §3)
    rank_dist = {}
    for repo in ("djangocms", "saleor"):
        v = np.array([ranks[(cid, p)] for cid, p in deep[repo]])
        rank_dist[repo] = {
            "count": int(len(v)),
            "median": float(np.median(v)),
            "mean": round(float(v.mean()), 1),
            "p25": float(np.percentile(v, 25)),
            "p75": float(np.percentile(v, 75)),
        }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "deep_dense_miss_counts": {r: len(v) for r, v in deep.items()},
        "deep_dense_miss_dense_rank_distribution": rank_dist,
        "deep_fn_coverage": coverage,
        "popularity_baseline": pop,
        "random_baseline": rnd,
        "dependency_cluster_diagnostic": dep,
    }
    (OUT_DIR / "deep_fn_coverage_report.json").write_text(
        json.dumps(payload, indent=1), encoding="utf-8")
    print(json.dumps(payload, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
