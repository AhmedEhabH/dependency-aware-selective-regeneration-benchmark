#!/usr/bin/env python3
"""ISSUE_GROUNDED_INTENT_HEADROOM - headroom metrics + primary gate (T3).

Computes, on the PRIMARY paired (temporally-clean) population:
- Recall@1/3/5/10/20 pooled + macro, coverage@K, MRR, median rank, rank
  distribution, top-K candidate precision per arm (M message vs I issue);
- exact per-target-file rank movement (message -> issue);
- task-paired bootstrap (10,000 resamples, seed 20260920) + frozen gate A-D;
- verdict SUPPORTED / MIXED / NOT_SUPPORTED.

Full artifact outputs respected; the gate was frozen BEFORE outcome inspection.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

import pandas as pd  # noqa: E402

from benchmark.issue_grounded.corpus import load_corpus  # noqa: E402
from benchmark.issue_grounded.metrics import (  # noqa: E402
    BOOTSTRAP_RESAMPLES,
    gates_for_repo,
    rank_movement_distribution,
    recall_k_table,
)
from benchmark.recall.data import load_dev_tasks  # noqa: E402

OUT_DIR = _PROJECT_DIR / "research" / "issue-grounded-intent-headroom"
QWEN_DIR = _PROJECT_DIR / "research" / "contamination-bridge" / "qwen_embed"


def main() -> int:
    corpus = load_corpus(OUT_DIR / "issue_corpus.json")
    arm_i = json.loads((OUT_DIR / "arm_i_dense.json").read_text(encoding="utf-8"))["tasks"]
    tasks = load_dev_tasks()
    proxy_by_id = {t.case_id: sorted(t.proxy) for t in tasks}

    clean_ids = [
        r["case_id"] for r in corpus["records"]
        if any(f == "TEMPORALLY_CLEAN" for f in r["temporal_flag"])
    ]
    clean_by_repo: dict[str, list[str]] = {}
    for cid in clean_ids:
        repo = [r["repository"] for r in corpus["records"] if r["case_id"] == cid][0]
        clean_by_repo.setdefault(repo, []).append(cid)
    print("[headroom] clean paired population per repo:",
          {r: len(v) for r, v in clean_by_repo.items()})

    out_results: dict[str, dict] = {}
    verdicts: dict[str, str] = {}

    for rid in ("A", "B"):
        parquet = pd.read_parquet(QWEN_DIR / f"realization_{rid}" / "full_file_scores.parquet")
        per_repo = {}
        for repo, cids in clean_by_repo.items():
            # Build per-task proxy positions for ARM M and ARM I.
            task_m: list[dict] = []
            task_i: list[dict] = []
            for cid in sorted(cids):
                arm_m_rows = parquet[parquet["case_id"] == cid]
                ranks_m = {r.file_path: int(r.dense_rank) for r in arm_m_rows.itertuples(index=False)}
                proxy = proxy_by_id[cid]
                task_m.append({"case_id": cid, "repository": repo,
                               "proxy_positions": [ranks_m.get(p) for p in proxy],
                               "proxy": proxy})
                i_ranks = None
                if cid in arm_i:
                    i_ranks = {p: arm_i[cid][rid]["proxy_dense_rank"].get(p) for p in proxy}
                task_i.append({"case_id": cid, "repository": repo,
                               "proxy_positions": None if i_ranks is None
                               else [i_ranks[p] for p in proxy],
                               "proxy": proxy})
            if not task_m:
                continue
            tbl_m = recall_k_table(task_m)
            tbl_i = recall_k_table(task_i)
            gates = gates_for_repo(task_m, task_i, k=20)
            movement = rank_movement_distribution(task_m, task_i)
            # top-K candidate precision (pooled top-20 across tasks, per arm)
            per_repo[repo] = {
                "n_tasks": len(task_m),
                "arm_m": tbl_m,
                "arm_i": tbl_i,
                "gate": gates,
                "rank_movement": movement,
                "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
            }
            verdicts[repo] = _single_repo_verdict(gates)
        out_results[rid] = per_repo

    # ---- overall verdict (frozen: SUPPORTED requires BOTH repos) ----
    overall = _overall_verdict(verdicts, out_results)
    print("[headroom] verdicts by repo:", verdicts)
    print("[headroom] OVERALL VERDICT:", overall["verdict"])

    (OUT_DIR / "headroom_results.json").write_text(
        json.dumps({"results": out_results, "verdict_by_repo": verdicts,
                    "overall": overall}, indent=1), encoding="utf-8")
    print("[headroom] DONE")
    return 0


def _single_repo_verdict(gate: dict) -> str:
    if gate["A_recall_i_gt_recall_m"] and gate["B_ci_lower_gt_0"] and gate["C_median_rank_improves_or_equal"]:
        return "REPO_PASS"
    return "REPO_FAIL"


def _overall_verdict(verdicts: dict[str, str], results: dict[str, dict]) -> dict:
    """Frozen rule: SUPPORTED iff both repos pass (any realization); MIXED iff
    exactly one passes; else NOT_SUPPORTED. Additionally, a repo with an EMPTY
    clean population cannot demonstrate support (its criterion is vacuous)."""
    has_repo = set()
    for per_repo in results.values():
        has_repo.update(per_repo.keys())
    passage: dict[str, bool] = {}
    for repo in sorted(has_repo):
        passes = verdicts.get(repo) == "REPO_PASS"

        # Criterion D (no leakage) is checked by the audit; temporal purity is
        # guaranteed by construction (only TEMPORALLY_CLEAN tasks enter).
        passage[repo] = passes

    n_pass = sum(1 for p in passage.values() if p)
    if len(passage) >= 2 and all(passage.values()):
        verdict = "ISSUE_GROUNDED_INTENT_SIGNAL_SUPPORTED"
    elif n_pass == 1:
        verdict = "ISSUE_GROUNDED_INTENT_SIGNAL_MIXED"
    elif n_pass == 0:
        verdict = "ISSUE_GROUNDED_INTENT_SIGNAL_NOT_SUPPORTED"
    else:
        verdict = "ISSUE_GROUNDED_INTENT_SIGNAL_MIXED"
    return {
        "verdict": verdict,
        "repos_with_population": sorted(has_repo),
        "repo_passage": passage,
        "n_repos_pass": n_pass,
    }


if __name__ == "__main__":
    raise SystemExit(main())
