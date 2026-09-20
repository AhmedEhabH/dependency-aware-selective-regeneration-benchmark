#!/usr/bin/env python3
"""PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2 — parent-only memory build (T3, ZERO API).

Builds the per-task memory data (cached on D:, OUTSIDE the repository):

  - global per-repository commit index (sha, subject, body, changed paths);
  - per task, parent-only production-changing history (ancestors of P only,
    fail-closed): C(f), cochange_sparse (Sparse seeds), episodic signals
    (top-10 BM25 episodes by the frozen task intent), episode_similarity /
    episode_hit_count, n_production_changing_commits;
  - per task, per realization (A and B): the dense rank-1 file, cochange_top1
    map, and the structural candidate list.

This is the frozen memory generator. It does NOT fit any model and does NOT
inspect any outcome. The cache lives OUTSIDE Git/export.

Run:
  python scripts/memory_rescue_v2_history.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))
sys.path.insert(0, str(_PROJECT_DIR / "scripts"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from benchmark.memory_rescue.cochange import (  # noqa: E402
    cochange_memory_score_map,
    cochange_sparse_map,
    cochange_top1_map,
    structural_candidates,
)
from benchmark.memory_rescue.episodic import episode_signals  # noqa: E402
from benchmark.memory_rescue.history import CACHE_ROOT, RepoHistory, TaskHistory  # noqa: E402
from benchmark.recall.data import load_dev_tasks  # noqa: E402

DEV_REPOS = ("djangocms", "saleor")
QWEN_DIR = _PROJECT_DIR / "research" / "contamination-bridge" / "qwen_embed"
MEMORY_CACHE = CACHE_ROOT / "memory_bundles.json"


def _rank1_file(parquet: pd.DataFrame, case_id: str) -> str | None:
    g = parquet[parquet["case_id"] == case_id]
    if g.empty:
        return None
    idx = int(g["dense_rank"].to_numpy(dtype=np.int64).argmin())
    return str(g["file_path"].iloc[idx])


def main() -> int:
    t_start = time.perf_counter()
    tasks = load_dev_tasks()
    tasks_by_id = {t.case_id: t for t in tasks}
    if len(tasks_by_id) != 323:
        raise RuntimeError(f"expected 323 DEV tasks, got {len(tasks_by_id)}")

    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    parquets = {
        rid: pd.read_parquet(QWEN_DIR / f"realization_{rid}" / "full_file_scores.parquet")
        for rid in ("A", "B")
    }
    out: dict = {"case_count": len(tasks_by_id), "tasks": {}}
    timings: dict = {}

    for repo in DEV_REPOS:
        t0 = time.perf_counter()
        rh = RepoHistory(repo)
        timings[f"{repo}_index_load_s"] = round(time.perf_counter() - t0, 3)
        t1 = time.perf_counter()
        count = 0
        for task in tasks_by_id.values():
            if task.repository != repo:
                continue
            universe = set(task.universe_records)
            th = TaskHistory(rh, task.parent_commit, universe)
            sparse = set(task.write_set)
            cs = cochange_sparse_map(th, sparse)

            episode_records = [
                {"sha": rec.sha, "subject": rec.subject, "body": rec.body,
                 "paths": rec.paths}
                for rec in th.commits.values()
            ]
            ep = episode_signals(episode_records, task.intent_text) if episode_records else {}

            variants = {}
            for rid in ("A", "B"):
                r1 = _rank1_file(parquets[rid], task.case_id)
                ct1 = cochange_top1_map(th, r1)
                mem = cochange_memory_score_map(cs, ct1)
                structural = structural_candidates(
                    mem, th.history_change_count,
                    [f for f in universe if f not in sparse], k=10)
                variants[rid] = {
                    "rank1": r1,
                    "cochange_top1": {f: round(v, 12) for f, v in ct1.items()},
                    "structural": structural,
                }

            out["tasks"][task.case_id] = {
                "repository": repo,
                "parent": task.parent_commit,
                "history_change_count": {f: int(v) for f, v in th.history_change_count.items()},
                "cochange_sparse": {f: round(v, 12) for f, v in cs.items()},
                "episode_similarity": {f: v["episode_similarity"] for f, v in ep.items()},
                "episode_hit_count": {f: v["episode_hit_count"] for f, v in ep.items()},
                "episodic": _episodic_from(ep, universe, sparse),
                "n_production_changing_commits": th.n_production_changing_commits(),
                "variants": variants,
            }
            count += 1
        timings[f"{repo}_tasks"] = count
        timings[f"{repo}_build_s"] = round(time.perf_counter() - t1, 3)

    MEMORY_CACHE.write_text(json.dumps(out, sort_keys=True), encoding="utf-8")
    timings["total_s"] = round(time.perf_counter() - t_start, 3)
    timings["cache_path"] = str(MEMORY_CACHE)
    timings["cache_bytes"] = MEMORY_CACHE.stat().st_size

    for repo in DEV_REPOS:
        cids = [c for c, t in tasks_by_id.items() if t.repository == repo]
        n_hist = sum(1 for c in cids
                     if out["tasks"][c]["n_production_changing_commits"] > 0)
        n_str = sum(1 for c in cids if out["tasks"][c]["variants"]["A"]["structural"])
        n_ep = sum(1 for c in cids if out["tasks"][c]["episodic"])
        print(f"{repo}: {len(cids)} tasks | {n_hist} with history | "
              f"{n_str} with structural candidates | {n_ep} with episodic candidates")
    print(json.dumps(timings, indent=1))
    return 0


def _episodic_from(ep: dict, universe: set[str], sparse: set[str]) -> list[str]:
    """Top-10 NON-SPARSE files by episode_similarity > 0 (frozen §12)."""
    scored = [(ep[f]["episode_similarity"], f) for f in universe
              if f not in sparse and ep.get(f, {}).get("episode_similarity", 0.0) > 0.0]
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [f for _, f in scored[:10]]


if __name__ == "__main__":
    raise SystemExit(main())
