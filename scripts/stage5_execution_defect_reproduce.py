#!/usr/bin/env python3
# ruff: noqa: N806
"""STAGE5_V2_EXECUTION_INVALID_EMBEDDING_COVERAGE_DEFECT - independent
reproduction of the defect counts from the PERSISTED invalid Stage-5 artifacts.

Re-reads ONLY raw persisted artifacts (parquet/json/jsonl) and recomputes the
mission reproduction counts A-H. It does NOT import the Stage-5 analyzer
(scripts.stage5_v2_*). It does NOT read corrected artifacts or labels.

Output: reports/stage5_execution_defect_reproduction.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

OUT = _PROJECT_DIR / "research" / "stage5-v2-final"
REPORTS = _PROJECT_DIR / "reports"
DEV_A = _PROJECT_DIR / "research" / "contamination-bridge" / "qwen_embed" / "realization_A" / "full_file_scores.parquet"

SENTINEL = -1e9


def main() -> int:
    ffs = pd.read_parquet(OUT / "full_file_scores_stage5.parquet")
    vp = pd.read_parquet(OUT / "v2_probabilities_stage5.parquet")
    cr = pd.read_parquet(OUT / "candidate_rows_stage5.parquet")
    devA = pd.read_parquet(DEV_A)

    # --- A. full-file score rows == finite sentinel -1e9 ---
    sent = ffs[ffs["dense_file_score"] == SENTINEL]
    n_sentinel = int(len(sent))

    # --- B. among sentinel rows, files whose paths had valid embeddings in DEV ---
    dev_valid_paths = set(devA.loc[np.isfinite(devA["dense_file_score"].to_numpy()), "file_path"])
    sent_dev = sent[sent["file_path"].isin(dev_valid_paths)]
    b_total = int(len(sent_dev))
    b_by_repo = {r: int((sent_dev["repository"] == r).sum()) for r in ("djangocms", "saleor")}

    # --- C/D/E/G. candidate rows forced to predicted probability exactly 0 ---
    prob0 = vp[vp["prob"] == 0]
    c_total = int(len(vp))
    c_forced0 = int(len(prob0))
    sparse = vp[vp["in_sparse"] == 1]
    sparse0 = sparse[sparse["prob"] == 0]
    d_total = int(len(sparse))
    d_forced0 = int(len(sparse0))
    e_proxy_tp = int((sparse0["label"] == 1).sum())
    nsp_gold = vp[(vp["in_sparse"] == 0) & (vp["label"] == 1)]
    g_total = int(len(nsp_gold))
    g_forced0 = int((nsp_gold["prob"] == 0).sum())

    # --- F. total Sparse true positives dropped by the invalid V2; how many hit ---
    sel = vp[vp["selected"] == 1]
    score_of = vp.set_index(["case_id", "file_path"])["dense_file_score"].to_dict()
    recs = [json.loads(line) for line in
            (OUT / "sparse_stage5_run_records.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()]
    sparse_ws: dict[str, set[str]] = {}
    for r in recs:
        if r["terminal_status"] == "succeeded":
            sparse_ws.setdefault(r["case_id"], set(r["predicted_write_set"]))
    gold = {cid: set(g.loc[g["label"] == 1, "file_path"]) for cid, g in vp.groupby("case_id")}
    dropped: list[tuple[str, str, float]] = []
    for cid, ws in sparse_ws.items():
        stp = ws & gold.get(cid, set())
        v2sel = set(sel.loc[sel["case_id"] == cid, "file_path"])
        for f in (stp - v2sel):
            dropped.append((cid, f, float(score_of.get((cid, f), np.nan))))
    f_total = len(dropped)
    f_hit = sum(1 for _, _, s in dropped if s == SENTINEL)

    # --- H. distribution sanity ---
    h_cand_mean = float(cr["dense_file_score"].mean())
    h_dev_mean = float(devA["dense_file_score"].mean())

    repro = {
        "mission": "STAGE5_V2_EXECUTION_INVALID_EMBEDDING_COVERAGE_DEFECT",
        "reproduced_from": "persisted invalid Stage-5 artifacts (research/stage5-v2-final)",
        "sentinel": SENTINEL,
        "A_full_file_score_sentinel_rows": n_sentinel,
        "B_sentinel_rows_with_valid_dev_embedding_path": {
            "total": b_total,
            "djangocms": b_by_repo["djangocms"],
            "saleor": b_by_repo["saleor"],
        },
        "C_candidate_rows_forced_prob0": {"forced0": c_forced0, "total": c_total},
        "D_sparse_candidate_rows_forced_prob0": {"forced0": d_forced0, "total": d_total},
        "E_sparse_proxy_tp_among_forced0": e_proxy_tp,
        "F_sparse_tp_dropped_by_invalid_v2": {
            "dropped_total": f_total,
            "directly_hit_by_defect": f_hit,
        },
        "G_gold_non_sparse_candidate_rows_forced0": {"forced0": g_forced0, "total": g_total},
        "H_candidate_dense_score_mean": h_cand_mean,
        "H_dev_dense_score_mean": h_dev_mean,
        "H_distribution_inconsistent": bool(h_cand_mean < 0),
    }
    (REPORTS / "stage5_execution_defect_reproduction.json").write_text(
        json.dumps(repro, indent=1), encoding="utf-8")
    print(json.dumps(repro, indent=1))
    print("[repro] wrote reports/stage5_execution_defect_reproduction.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
