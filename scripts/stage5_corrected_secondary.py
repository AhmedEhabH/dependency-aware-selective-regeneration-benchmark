#!/usr/bin/env python3
"""STAGE5_CORRECTED_REEXECUTION - secondary metrics + Acc@K/Hit@K/Recall@K.

Computes the mandatory secondary results for the corrected Stage-5 run:
  - per-repo TP/FP/FN/P/R/F1/FNR (V2 vs Sparse, point + delta);
  - set-size analysis (mean/median/empty rate/additions/drops);
  - Acc@K / Hit@K / Recall@K for the corrected V2 Stage-5 ranking
    (descending corrected V2 probability over the corrected candidate universe).

Descriptive only; NOT gate criteria. Uses the exact audited definitions.
Output: reports/stage5_corrected_secondary_result.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))
sys.path.insert(0, str(_PROJECT_DIR / "scripts"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from benchmark.calibrated.policy import confusion, per_task_confusion  # noqa: E402

OUT = _PROJECT_DIR / "research" / "stage5-v2-final"
REPORTS = _PROJECT_DIR / "reports"
DC_SPLIT = _PROJECT_DIR / "research" / "transparency" / "v2_split_proposal.json"
SC_SPLIT = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor" / "split_freeze_saleor.json"
KS = (1, 3, 5)
THRESHOLD = 0.20
PROB_PATH = OUT / "v2_probabilities_stage5_corrected.parquet"


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
    frame = pd.read_parquet(PROB_PATH)
    sparse_recs = [json.loads(line) for line in
                   (OUT / "sparse_stage5_run_records.jsonl").read_text(encoding="utf-8").splitlines()
                   if line.strip()]
    sparse_ws: dict[str, set[str]] = {}
    for r in sparse_recs:
        if r["terminal_status"] == "succeeded":
            sparse_ws.setdefault(r["case_id"], set(r["predicted_write_set"]))

    import importlib
    p1 = importlib.import_module("benchmark.real_commits.p1_evaluation")
    proxy: dict[str, set[str]] = {}
    for r in roles:
        ds = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_v2" if r["repo"] == "djangocms" \
            else _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor"
        proxy[r["case_id"]] = set(p1.load_hidden_proxy_paths(ds, r["case_id"]))

    v2_sets, v2_rank = {}, {}
    for cid, g in frame.groupby("case_id"):
        g = g.sort_values(["prob", "file_path"], ascending=[False, True])
        v2_rank[cid] = list(g["file_path"])
        v2_sets[cid] = set(g.loc[g["prob"] >= THRESHOLD, "file_path"])

    secondary: dict = {}
    for repo in ("djangocms", "saleor"):
        cids = [r["case_id"] for r in roles if r["repo"] == repo]
        v2c = [per_task_confusion(v2_sets[c], proxy[c]) for c in cids]
        spc = [per_task_confusion(sparse_ws[c], proxy[c]) for c in cids]
        sizes_sparse = [len(sparse_ws[c]) for c in cids]
        sizes_v2 = [len(v2_sets[c]) for c in cids]
        additions = [len(v2_sets[c] - sparse_ws[c]) for c in cids]
        drops = [len(sparse_ws[c] - v2_sets[c]) for c in cids]
        secondary[repo] = {
            "n_tasks": len(cids),
            "sparse": confusion(*(tuple(sum(x[i] for x in spc) for i in range(3)))),
            "v2": confusion(*(tuple(sum(x[i] for x in v2c) for i in range(3)))),
            "set_size_sparse": {"mean": round(float(np.mean(sizes_sparse)), 4),
                                "median": float(np.median(sizes_sparse)),
                                "empty": int(sum(1 for s in sizes_sparse if s == 0))},
            "set_size_v2": {"mean": round(float(np.mean(sizes_v2)), 4),
                            "median": float(np.median(sizes_v2)),
                            "empty": int(sum(1 for s in sizes_v2 if s == 0))},
            "additions_mean": round(float(np.mean(additions)), 4),
            "drops_mean": round(float(np.mean(drops)), 4),
        }

    def compat(table_ids: list[str]) -> dict:
        acc = {k: 0 for k in KS}
        hit = {k: 0 for k in KS}
        rec = {k: 0.0 for k in KS}
        n = 0
        for cid in table_ids:
            g = proxy.get(cid, set())
            if not g or cid not in v2_rank:
                continue
            order = v2_rank[cid]
            n += 1
            for k in KS:
                inter = len(set(order[:k]) & g)
                acc[k] += 1 if inter == min(len(g), k) else 0
                hit[k] += 1 if inter >= 1 else 0
                rec[k] += inter / len(g)
        return {"n_tasks": n,
                "acc": {k: round(acc[k] / n, 6) if n else 0.0 for k in KS},
                "hit": {k: round(hit[k] / n, 6) if n else 0.0 for k in KS},
                "recall": {k: round(rec[k] / n, 6) if n else 0.0 for k in KS}}

    all_ids = [r["case_id"] for r in roles]
    secondary["compat"] = {
        "all": compat(all_ids),
        "djangocms": compat([r["case_id"] for r in roles if r["repo"] == "djangocms"]),
        "saleor": compat([r["case_id"] for r in roles if r["repo"] == "saleor"]),
    }

    (REPORTS / "stage5_corrected_secondary_result.json").write_text(
        json.dumps(secondary, indent=1), encoding="utf-8")
    print(json.dumps(secondary, indent=1))
    print("[s5c-secondary] DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
