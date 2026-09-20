#!/usr/bin/env python3
# ruff: noqa: E501
"""STAGE5_CORRECTED_REEXECUTION - DEFECT IMPACT ANALYSIS (mission §15).

Directly compares the INVALID Stage-5 execution against the CORRECTED one:
  - number of file scores changed;
  - number of candidate probabilities changed;
  - number of previously forced-zero Sparse files restored;
  - among the 34 previously affected Sparse proxy TPs: how many are retained by
    corrected V2;
  - TP/FP/FN difference and F1 difference (per repo + pooled);
  - how corrected embeddings affect dense top-20, dense rank-1,
    structural-memory seeds (rank-1 matters), candidate universe, final
    predictions.

Output: reports/stage5_corrected_impact_analysis.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

import pandas as pd  # noqa: E402

from benchmark.calibrated.policy import confusion, per_task_confusion  # noqa: E402

OUT = _PROJECT_DIR / "research" / "stage5-v2-final"
REPORTS = _PROJECT_DIR / "reports"
DC_SPLIT = _PROJECT_DIR / "research" / "transparency" / "v2_split_proposal.json"
SC_SPLIT = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor" / "split_freeze_saleor.json"

INV_FFS = OUT / "full_file_scores_stage5.parquet"
COR_FFS = OUT / "full_file_scores_stage5_corrected.parquet"
INV_PROB = OUT / "v2_probabilities_stage5.parquet"
COR_PROB = OUT / "v2_probabilities_stage5_corrected.parquet"
INV_CR = OUT / "candidate_rows_stage5.parquet"
COR_CR = OUT / "candidate_rows_stage5_corrected.parquet"


def _roles() -> list[dict]:
    prop = json.loads(DC_SPLIT.read_text(encoding="utf-8"))
    sc = json.loads(SC_SPLIT.read_text(encoding="utf-8"))
    out = []
    for cid, r in prop["assignment"].items():
        if r == "RESERVE":
            out.append({"case_id": cid, "repo": "djangocms"})
    for cid, r in sc["assignment"].items():
        if r == "INTERNAL_TEST":
            out.append({"case_id": cid, "repo": "saleor"})
    return out


def main() -> int:
    roles = _roles()
    inv_ffs = pd.read_parquet(INV_FFS)
    cor_ffs = pd.read_parquet(COR_FFS)
    inv_vp = pd.read_parquet(INV_PROB)
    cor_vp = pd.read_parquet(COR_PROB)

    # ---- 1. number of file scores changed ----
    m = inv_ffs.merge(cor_ffs, on=["case_id", "file_path"], suffixes=("_inv", "_cor"))
    # NaN vs NaN -> equal; NaN vs finite -> changed
    both_nan = m["dense_file_score_inv"].isna() & m["dense_file_score_cor"].isna()
    same = (m["dense_file_score_inv"] == m["dense_file_score_cor"]) | both_nan
    score_changed2 = int((~same).sum())

    # ---- 2. number of candidate probabilities changed ----
    pm = inv_vp.merge(cor_vp, on=["case_id", "file_path"], suffixes=("_inv", "_cor"))
    prob_changed = int((pm["prob_inv"] != pm["prob_cor"]).sum())
    sel_changed = int((pm["selected_inv"] != pm["selected_cor"]).sum())

    # ---- 3. previously forced-zero Sparse files restored ----
    inv_sp0 = set(zip(inv_vp.loc[inv_vp["in_sparse"] == 1].loc[inv_vp["prob"] == 0, "case_id"],
                      inv_vp.loc[inv_vp["in_sparse"] == 1].loc[inv_vp["prob"] == 0, "file_path"],
                      strict=True))
    cor_sel = set(zip(cor_vp.loc[cor_vp["selected"] == 1, "case_id"],
                      cor_vp.loc[cor_vp["selected"] == 1, "file_path"],
                      strict=True))
    restored = [x for x in inv_sp0 if x in cor_sel]
    # a Sparse file forced to 0 in invalid; restored = now selected in corrected
    # (it may not be in corrected candidate universe; treat as not selected)
    n_restored = len(restored)

    # ---- 4. among the 34 previously affected Sparse proxy TPs ----
    inv_sp0_tp = set(zip(inv_vp.loc[(inv_vp["in_sparse"] == 1) & (inv_vp["prob"] == 0) & (inv_vp["label"] == 1), "case_id"],
                        inv_vp.loc[(inv_vp["in_sparse"] == 1) & (inv_vp["prob"] == 0) & (inv_vp["label"] == 1), "file_path"],
                        strict=True))
    n_34 = len(inv_sp0_tp)
    retained = [x for x in inv_sp0_tp if x in cor_sel]
    # also: how many of the 34 are in the corrected candidate universe at all
    cor_universe = set(zip(cor_vp["case_id"], cor_vp["file_path"], strict=True))
    in_cor_uni = [x for x in inv_sp0_tp if x in cor_universe]
    n_34_retained = len(retained)

    # ---- 5/6. TP/FP/FN/F1 difference (invalid vs corrected) ----
    import importlib
    p1 = importlib.import_module("benchmark.real_commits.p1_evaluation")
    proxy = {}
    for r in roles:
        ds = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_v2" if r["repo"] == "djangocms" \
            else _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor"
        proxy[r["case_id"]] = set(p1.load_hidden_proxy_paths(ds, r["case_id"]))

    def sets(vp_df: pd.DataFrame) -> dict[str, set[str]]:
        return {cid: set(g.loc[g["selected"] == 1, "file_path"]) for cid, g in vp_df.groupby("case_id")}

    inv_sets = sets(inv_vp)
    cor_sets = sets(cor_vp)
    pooled = {}
    per_repo = {}
    for repo in ("djangocms", "saleor"):
        cids = [r["case_id"] for r in roles if r["repo"] == repo]
        inv_c = [per_task_confusion(inv_sets.get(c, set()), proxy[c]) for c in cids]
        cor_c = [per_task_confusion(cor_sets.get(c, set()), proxy[c]) for c in cids]
        inv_pool = tuple(sum(x[i] for x in inv_c) for i in range(3))
        cor_pool = tuple(sum(x[i] for x in cor_c) for i in range(3))
        per_repo[repo] = {
            "invalid": {"tpfpfn": inv_pool, **confusion(*inv_pool)},
            "corrected": {"tpfpfn": cor_pool, **confusion(*cor_pool)},
            "delta_tp": cor_pool[0] - inv_pool[0],
            "delta_fp": cor_pool[1] - inv_pool[1],
            "delta_fn": cor_pool[2] - inv_pool[2],
            "delta_f1": confusion(*cor_pool)["f1"] - confusion(*inv_pool)["f1"],
        }
        pooled.setdefault("tpfpfn_inv", [0, 0, 0])
        pooled.setdefault("tpfpfn_cor", [0, 0, 0])
        for i in range(3):
            pooled["tpfpfn_inv"][i] += inv_pool[i]
            pooled["tpfpfn_cor"][i] += cor_pool[i]
    pooled["confusion_inv"] = confusion(*pooled["tpfpfn_inv"])
    pooled["confusion_cor"] = confusion(*pooled["tpfpfn_cor"])
    pooled["delta_tp"] = pooled["tpfpfn_cor"][0] - pooled["tpfpfn_inv"][0]
    pooled["delta_fp"] = pooled["tpfpfn_cor"][1] - pooled["tpfpfn_inv"][1]
    pooled["delta_fn"] = pooled["tpfpfn_cor"][2] - pooled["tpfpfn_inv"][2]
    pooled["delta_f1"] = pooled["confusion_cor"]["f1"] - pooled["confusion_inv"]["f1"]

    # ---- 7. ranking effects ----
    # dense top-20 selection + rank-1 + structural seed changes
    cor_f = cor_vp.merge(inv_vp[["case_id", "file_path", "dense_rank"]],
                         on=["case_id", "file_path"], suffixes=("", "_inv"))
    rank1_changed = 0
    top20_changed = 0
    for _cid, g in cor_f.groupby("case_id"):
        r1_cor = g.loc[g["dense_rank"] == 1, "file_path"]
        r1_inv = g.loc[g["dense_rank_inv"] == 1, "file_path"]
        if len(r1_cor) and len(r1_inv) and list(r1_cor) != list(r1_inv):
            rank1_changed += 1
        top20_cor = set(g.loc[g["dense_rank"] <= 20, "file_path"])
        top20_inv = set(g.loc[g["dense_rank_inv"] <= 20, "file_path"])
        if top20_cor != top20_inv:
            top20_changed += 1

    result = {
        "file_scores_changed": score_changed2,
        "candidate_probabilities_changed": int(prob_changed),
        "selected_flags_changed": int(sel_changed),
        "previously_forced_zero_sparse_files": len(inv_sp0),
        "forced_zero_sparse_restored_by_corrected_v2": n_restored,
        "affected_sparse_proxy_tp_count": n_34,
        "affected_sparse_proxy_tp_retained_by_corrected_v2": n_34_retained,
        "affected_sparse_proxy_tp_in_corrected_universe": len(in_cor_uni),
        "pooled_invalid_vs_corrected": pooled,
        "per_repo_invalid_vs_corrected": per_repo,
        "ranking_effects": {
            "tasks_with_dense_rank1_changed": rank1_changed,
            "tasks_with_dense_top20_changed": top20_changed,
            "n_tasks": len(roles),
        },
    }
    (REPORTS / "stage5_corrected_impact_analysis.json").write_text(
        json.dumps(result, indent=1), encoding="utf-8")
    print(json.dumps(result, indent=1))
    print("[s5c-impact] DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
