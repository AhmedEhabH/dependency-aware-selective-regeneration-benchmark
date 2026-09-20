#!/usr/bin/env python3
# ruff: noqa: N812
"""PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2 — descriptive channel ablations.

Mission §31 (mechanism understanding ONLY; NOT used to redefine V2, NOT used
to select the better channel post hoc):

  PRIMARY V2 = dense + structural history + episodic history.
  Ablation A (structural-removed): memory candidates = episodic only; the
    cochange_sparse / cochange_top1 features are zeroed (constant -> no
    signal under StandardScaler; functionally equivalent to removing them).
  Ablation B (episodic-removed): memory candidates = structural only; the
    episode_similarity feature is zeroed.

Same frozen model / folds / threshold procedure as V2. Realization A primary.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))
sys.path.insert(0, str(_PROJECT_DIR / "scripts"))

import pandas as pd  # noqa: E402

from benchmark.memory_rescue import analysis as MA  # noqa: E402
from benchmark.memory_rescue import candidates as C  # noqa: E402
from benchmark.recall.data import load_dev_tasks  # noqa: E402
from scripts.memory_rescue_v2_run import (  # noqa: E402
    load_memory_bundles,
    load_v1_fold_map,
    sealed_guard,
)

OUT_DIR = _PROJECT_DIR / "research" / "memory-rescue-v2" / "ablations"
QWEN_DIR = _PROJECT_DIR / "research" / "contamination-bridge" / "qwen_embed"


def ablation_memory(memory: dict, kind: str) -> dict:
    """Return a MemoryBundle copy with one channel removed (descriptive)."""
    out = {}
    for cid, b in memory.items():
        if kind == "structural":
            out[cid] = C.MemoryBundle(
                history_change_count=b.history_change_count,
                cochange_sparse={},            # zeroed (channel removed)
                episode_similarity=b.episode_similarity,
                episode_hit_count=b.episode_hit_count,
                n_production_changing_commits=b.n_production_changing_commits,
                cochange_top1=None,            # zeroed
                structural=None,               # structural candidates removed
                episodic=b.episodic,
            )
        elif kind == "episodic":
            out[cid] = C.MemoryBundle(
                history_change_count=b.history_change_count,
                cochange_sparse=b.cochange_sparse,
                episode_similarity={},         # zeroed (channel removed)
                episode_hit_count={},
                n_production_changing_commits=b.n_production_changing_commits,
                cochange_top1=b.cochange_top1,
                structural=b.structural,
                episodic=None,                 # episodic candidates removed
            )
        else:
            raise ValueError(kind)
    return out


def run_ablation(name: str, memory: dict, tasks_by_id: dict, fold_map: dict) -> dict:
    parquet = QWEN_DIR / "realization_A" / "full_file_scores.parquet"
    df = pd.read_parquet(parquet)
    rows, _ = C.build_rows_with_provenance(df, tasks_by_id, memory)
    frame = C.rows_to_frame(rows)
    results = MA.run_nested_cv_v2(frame, tasks_by_id, fold_map, provenance=None,
                                  n_folds=5)
    gate = MA.evaluate_gate(results)
    return {
        "name": name,
        "repo_metrics": results["repo_metrics"],
        "bootstrap": results["bootstrap"],
        "fold_deltas": results["fold_deltas"],
        "gate": gate,
    }


def main() -> int:
    tasks = load_dev_tasks()
    sealed_guard(tasks)
    tasks_by_id = {t.case_id: t for t in tasks}
    fold_map = load_v1_fold_map(tasks_by_id)
    memory = load_memory_bundles("A")

    out = {}
    for name, kind in (("structural_removed", "structural"),
                       ("episodic_removed", "episodic")):
        mem = ablation_memory(memory, kind)
        out[name] = run_ablation(name, mem, tasks_by_id, fold_map)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "ablations.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    for name, r in out.items():
        for repo in ("djangocms", "saleor"):
            m = r["repo_metrics"][repo]
            f1p = m["policy"]["f1"]
            f1s = m["sparse"]["f1"]
            ci = r["bootstrap"][repo]["f1"]
            print(f"{name} {repo}: F1 {f1s:.4f} -> {f1p:.4f} "
                  f"Delta {ci['point_delta']:+.4f} [{ci['ci95_lower']:+.4f}, "
                  f"{ci['ci95_upper']:+.4f}] gate_pass={r['gate']['gate'][repo]['pass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
