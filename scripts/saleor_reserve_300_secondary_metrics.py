#!/usr/bin/env python3
# ruff: noqa: E501, N806, N812
"""SALEOR_RESERVE_300_RMCSS - ranking compatibility, characterization, error
decomposition, efficiency (§25-28). Descriptive only.

Output: reports/saleor_reserve_300_rmcss_secondary_metrics.json
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
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

from benchmark.memory_rescue import candidates as C  # noqa: E402

OUT = _PROJECT_DIR / "research" / "saleor-reserve-300-rmcss"
REPORTS = _PROJECT_DIR / "reports"
CAND = OUT / "candidate_rows_saleor300.parquet"
PROXIES = OUT / "saleor_reserve_300_proxies.json"
PRIMARY_ART = _PROJECT_DIR / "research" / "stage5-v2-final" / "deployment_artifact.json"
KS = (1, 3, 5)
THRESHOLD = 0.20


def _apply_model(artifact: dict, frame: pd.DataFrame) -> np.ndarray:
    scaler = StandardScaler()
    scaler.mean_ = np.asarray(artifact["scaler_mean"], dtype=np.float64)
    scaler.scale_ = np.asarray(artifact["scaler_scale"], dtype=np.float64)
    scaler.var_ = scaler.scale_ ** 2
    scaler.n_features_in_ = len(artifact["scaler_mean"])
    model = LogisticRegression(penalty="l2", C=1.0, solver="liblinear", max_iter=1000, random_state=0)
    idx_cont = [C.FEATURE_NAMES.index(c) for c in C.CONTINUOUS_FEATURES]
    idx_bool = [C.FEATURE_NAMES.index(c) for c in C.BOOLEAN_FEATURES]
    X = C.feature_matrix(frame)
    X_cont = scaler.transform(X[:, idx_cont])
    X_bool = X[:, idx_bool].astype(np.float64)
    model.coef_ = np.asarray(artifact["lr_coef"], dtype=np.float64).reshape(1, -1)
    model.intercept_ = np.asarray([artifact["lr_intercept"]], dtype=np.float64)
    model.classes_ = np.asarray([0, 1])
    model.n_features_in_ = X_cont.shape[1] + X_bool.shape[1]
    return model.predict_proba(np.concatenate([X_cont, X_bool], axis=1))[:, 1]


def main() -> int:
    frame = pd.read_parquet(CAND)
    proxies = json.loads(PROXIES.read_text(encoding="utf-8"))["proxies"]
    primary = json.loads(PRIMARY_ART.read_text(encoding="utf-8"))
    frame = frame.copy()
    frame["prob"] = _apply_model(primary, frame)
    cids = sorted(set(frame["case_id"]))
    rank = {}
    rmcss_sets = {}
    for cid, g in frame.groupby("case_id"):
        g = g.sort_values(["prob", "file_path"], ascending=[False, True])
        rank[cid] = list(g["file_path"])
        rmcss_sets[cid] = set(g.loc[g["prob"] >= THRESHOLD, "file_path"])
    sip_sets = {cid: set(g.loc[g["in_sparse"] == 1, "file_path"]) for cid, g in frame.groupby("case_id")}

    # ---- ranking compatibility (Acc@K / Hit@K / Recall@K) ----
    def compat(id_subset: list[str]) -> dict:
        acc = {k: 0 for k in KS}
        hit = {k: 0 for k in KS}
        rec = {k: 0.0 for k in KS}
        n = 0
        n_g1 = 0
        g1 = {k: 0 for k in KS}
        for cid in id_subset:
            g = set(proxies[cid])
            if not g or cid not in rank:
                continue
            order = rank[cid]
            n += 1
            is_g1 = len(g) == 1
            if is_g1:
                n_g1 += 1
            for k in KS:
                inter = len(set(order[:k]) & g)
                acc[k] += 1 if inter == min(len(g), k) else 0
                hit[k] += 1 if inter >= 1 else 0
                rec[k] += inter / len(g)
                if is_g1:
                    g1[k] += 1 if inter >= 1 else 0
        return {
            "n_tasks": n,
            "acc": {k: round(acc[k] / n, 6) if n else 0.0 for k in KS},
            "hit": {k: round(hit[k] / n, 6) if n else 0.0 for k in KS},
            "recall": {k: round(rec[k] / n, 6) if n else 0.0 for k in KS},
            "g1_slice": {"n_tasks": n_g1, "hit": {k: round(g1[k] / n_g1, 6) if n_g1 else 0.0 for k in KS}},
        }

    compat_all = compat(cids)

    # ---- temporal / task characterization ----
    # target-file (proxy) count distribution
    sizes = [len(proxies[c]) for c in cids]
    char = {
        "final_n": len(cids),
        "target_file_count": {
            "mean": round(float(np.mean(sizes)), 4), "median": float(np.median(sizes)),
            "min": int(min(sizes)), "max": int(max(sizes)),
        },
        "sip_empty_count": int(sum(1 for c in cids if not sip_sets[c])),
        "rmcss_empty_count": int(sum(1 for c in cids if not rmcss_sets[c])),
        "candidate_set_size_mean": round(float(frame.groupby('case_id').size().mean()), 4),
        "rmcss_selected_set_size_mean": round(float(rmcss_sets and np.mean([len(s) for s in rmcss_sets.values()])), 4),
        "sip_selected_set_size_mean": round(float(np.mean([len(s) for s in sip_sets.values()])), 4),
    }
    # commit-message word-count distribution (from intents)
    wc = []
    for cid in cids:
        intent = json.loads((_PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor" / "scientific" / cid / "public" / "intent.json").read_text(encoding="utf-8"))
        wc.append(len(intent["intent_text"].split()))
    char["commit_message_word_count"] = {
        "mean": round(float(np.mean(wc)), 2), "median": float(np.median(wc)),
        "min": int(min(wc)), "max": int(max(wc)),
    }

    # ---- error decomposition (PRIMARY RM-CSS) ----
    dec = {"sip_tp_retained": 0, "sip_tp_dropped": 0, "sip_fp_dropped": 0,
           "sip_fp_retained": 0, "omitted_positives_added": 0, "new_fp_added": 0}
    fn = {"not_generated": 0, "generated_but_rejected": 0, "sip_tp_dropped": 0}
    for cid in cids:
        g = set(proxies[cid])
        sp = sip_sets[cid]
        rm = rmcss_sets[cid]
        dec["sip_tp_retained"] += len(sp & g & rm)
        dec["sip_tp_dropped"] += len((sp & g) - rm)
        dec["sip_fp_dropped"] += len((sp - g) - rm)
        dec["sip_fp_retained"] += len((sp - g) & rm)
        dec["omitted_positives_added"] += len((g - sp) & rm)
        dec["new_fp_added"] += len((rm - sp) - g)
        # remaining FN
        rem_fn = g - rm
        cand_rows = set(frame.loc[frame["case_id"] == cid, "file_path"])
        fn["not_generated"] += len(rem_fn - cand_rows)
        fn["generated_but_rejected"] += len((rem_fn & cand_rows) - sp)
        fn["sip_tp_dropped"] += len(rem_fn & sp)

    result = {"ranking_compatibility": compat_all, "characterization": char,
              "error_decomposition": dec}
    (REPORTS / "saleor_reserve_300_rmcss_secondary_metrics.json").write_text(
        json.dumps(result, indent=1), encoding="utf-8")
    print(json.dumps(result, indent=1))
    print("[s300-secondary-metrics] DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
