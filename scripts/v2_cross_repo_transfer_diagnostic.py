#!/usr/bin/env python3
# ruff: noqa: N806, N812
"""SALEOR_RESERVE_300_RMCSS - leave-one-repository cross-transfer diagnostic.

Uses ONLY already-exposed data (djangoCMS DEV, Saleor DEV, corrected exposed
Saleor Stage-5). EXPOSED-DATA MOTIVATION ONLY - does NOT count as final
transfer evidence and does NOT access Saleor RESERVE.

Reproduces the frozen cross-repository diagnostic:
  - train djangoCMS DEV ONLY -> test Saleor DEV;
  - train djangoCMS DEV ONLY -> test corrected exposed Saleor Stage-5;
  - reverse: train Saleor DEV ONLY -> test djangoCMS DEV (expected weaker).

Exact RM-CSS recipe for the transfer model (L2-LR C=1.0 liblinear max_iter=1000
random_state=0; StandardScaler on the 9 continuous features; boolean pass
through; 5-fold task-grouped OOF threshold on the TRAINING repo only, grid
0.01..0.99 step 0.01, argmax pooled micro-F1, tie-break higher).

Output: reports/v2_cross_repo_transfer.json
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
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

from benchmark.calibrated.folds import grouped_stratified_folds, split_by_fold  # noqa: E402
from benchmark.calibrated.policy import (  # noqa: E402
    per_task_confusion,
    select_threshold,
)
from benchmark.memory_rescue import candidates as C  # noqa: E402

OUT = _PROJECT_DIR / "research" / "stage5-v2-final"
REPORTS = _PROJECT_DIR / "reports"
DEV_CAND = OUT / "deployment_candidate_rows.parquet"
STAGE5_CORR = OUT / "candidate_rows_stage5_corrected.parquet"
DC_SPLIT = _PROJECT_DIR / "research" / "transparency" / "v2_split_proposal.json"
SC_SPLIT = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor" / "split_freeze_saleor.json"
N_BOOT = 10000
SEED = 20260920


def _confusion(tp, fp, fn):
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": f1, "fnr": 1.0 - r}


def fit_threshold(frame: pd.DataFrame, repo: str) -> float:
    """5-fold task-grouped OOF threshold on the training repo rows only."""
    repo_ids = sorted(set(frame.loc[frame["repository"] == repo, "case_id"]))
    repo_of = {cid: repo for cid in repo_ids}
    fold_map = grouped_stratified_folds(repo_ids, lambda c: repo_of[c], k=5, seed=SEED)
    probs: list[np.ndarray] = []
    labels: list[np.ndarray] = []
    for fold in range(5):
        tr, te = split_by_fold(fold_map, fold)
        trf = frame[frame["case_id"].isin(tr)]
        tef = frame[frame["case_id"].isin(te)]
        idx_cont = [C.FEATURE_NAMES.index(c) for c in C.CONTINUOUS_FEATURES]
        idx_bool = [C.FEATURE_NAMES.index(c) for c in C.BOOLEAN_FEATURES]
        sc = StandardScaler()
        Xtr = C.feature_matrix(trf)
        Xtr_cont = sc.fit_transform(Xtr[:, idx_cont])
        Xtr_bool = Xtr[:, idx_bool].astype(np.float64)
        m = LogisticRegression(penalty="l2", C=1.0, solver="liblinear", max_iter=1000, random_state=0)
        m.fit(np.concatenate([Xtr_cont, Xtr_bool], axis=1), C.label_vector(trf))
        Xte = C.feature_matrix(tef)
        Xte_cont = sc.transform(Xte[:, idx_cont])
        Xte_bool = Xte[:, idx_bool].astype(np.float64)
        probs.append(m.predict_proba(np.concatenate([Xte_cont, Xte_bool], axis=1))[:, 1])
        labels.append(C.label_vector(tef))
    return float(select_threshold(np.concatenate(probs), np.concatenate(labels)))


def train_on_repo(frame: pd.DataFrame, repo: str, threshold: float):
    """Fit the transfer model on `repo` rows; return (scaler, model, threshold)."""
    idx_cont = [C.FEATURE_NAMES.index(c) for c in C.CONTINUOUS_FEATURES]
    idx_bool = [C.FEATURE_NAMES.index(c) for c in C.BOOLEAN_FEATURES]
    train = frame[frame["repository"] == repo]
    sc = StandardScaler()
    X = C.feature_matrix(train)
    X_cont = sc.fit_transform(X[:, idx_cont])
    X_bool = X[:, idx_bool].astype(np.float64)
    m = LogisticRegression(penalty="l2", C=1.0, solver="liblinear", max_iter=1000, random_state=0)
    m.fit(np.concatenate([X_cont, X_bool], axis=1), C.label_vector(train))
    return sc, m, threshold


def apply_model(sc, m, threshold, frame: pd.DataFrame) -> dict[str, set[str]]:
    idx_cont = [C.FEATURE_NAMES.index(c) for c in C.CONTINUOUS_FEATURES]
    idx_bool = [C.FEATURE_NAMES.index(c) for c in C.BOOLEAN_FEATURES]
    X = C.feature_matrix(frame)
    X_cont = sc.transform(X[:, idx_cont])
    X_bool = X[:, idx_bool].astype(np.float64)
    prob = m.predict_proba(np.concatenate([X_cont, X_bool], axis=1))[:, 1]
    frame = frame.copy()
    frame["prob"] = prob
    out: dict[str, set[str]] = {}
    for cid, g in frame.groupby("case_id"):
        out[cid] = set(g.loc[g["prob"] >= threshold, "file_path"])
    return out


def eval_split(frame: pd.DataFrame, _repo: str, sip_sets: dict[str, set[str]],
               rmcss_sets: dict[str, set[str]], proxy: dict[str, set[str]]) -> dict:
    cids = sorted(set(frame["case_id"]))
    sip_c = [per_task_confusion(sip_sets.get(c, set()), proxy[c]) for c in cids]
    rm_c = [per_task_confusion(rmcss_sets.get(c, set()), proxy[c]) for c in cids]
    sip_pool = tuple(sum(x[i] for x in sip_c) for i in range(3))
    rm_pool = tuple(sum(x[i] for x in rm_c) for i in range(3))
    sip = _confusion(*sip_pool)
    rmcss = _confusion(*rm_pool)
    delta_point = rmcss["f1"] - sip["f1"]

    rng = random.Random(SEED)
    pos = {c: i for i, c in enumerate(cids)}
    deltas = np.empty(N_BOOT)
    for b in range(N_BOOT):
        idx = [pos[c] for c in (cids[rng.randrange(len(cids))] for _ in range(len(cids)))]
        stp = sum(sip_c[i][0] for i in idx)
        sfp = sum(sip_c[i][1] for i in idx)
        sfn = sum(sip_c[i][2] for i in idx)
        rtp = sum(rm_c[i][0] for i in idx)
        rfp = sum(rm_c[i][1] for i in idx)
        rfn = sum(rm_c[i][2] for i in idx)
        f1s = 2 * stp / (2 * stp + sfp + sfn) if (2 * stp + sfp + sfn) else 0.0
        f1r = 2 * rtp / (2 * rtp + rfp + rfn) if (2 * rtp + rfp + rfn) else 0.0
        deltas[b] = f1r - f1s
    lo, hi = np.quantile(deltas, [0.025, 0.975])
    return {"n_tasks": len(cids), "sip": sip, "rmcss": rmcss,
            "delta_f1_point": delta_point, "ci95_lower": float(lo), "ci95_upper": float(hi)}


def main() -> int:
    def load_proxy(cid: str, repo: str) -> set[str]:
        ds = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_v2" if repo == "djangocms" \
            else _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor"
        p = ds / "scientific" / cid / "hidden" / "observed_change_set_proxy.json"
        if not p.exists() and repo == "djangocms":
            p = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_v1" / "scientific" \
                / cid / "hidden" / "observed_change_set_proxy.json"
        if not p.exists():
            raise FileNotFoundError(f"proxy missing for {cid}: {p}")
        data = json.loads(p.read_text(encoding="utf-8"))
        return set(sorted(str(x) for x in data.get("paths", [])))

    dev = pd.read_parquet(DEV_CAND)
    s5 = pd.read_parquet(STAGE5_CORR)
    results: dict = {}

    # Full hidden proxies (NOT restricted to the candidate universe)
    dev_proxy = {cid: load_proxy(cid, repo) for cid, repo in
                 zip(dev["case_id"], dev["repository"], strict=True)}
    s5_proxy = {cid: load_proxy(cid, repo) for cid, repo in
                zip(s5["case_id"], s5["repository"], strict=True)}

    # SIP sets per frame from in_sparse
    def sip_sets(frame: pd.DataFrame) -> dict[str, set[str]]:
        return {cid: set(g.loc[g["in_sparse"] == 1, "file_path"]) for cid, g in frame.groupby("case_id")}

    dev_sip = sip_sets(dev)
    s5_sip = sip_sets(s5)

    # --- djangoCMS DEV -> Saleor DEV ---
    dc_thr = fit_threshold(dev, "djangocms")
    sc, m, thr = train_on_repo(dev, "djangocms", dc_thr)
    sc_dev = dev[dev["repository"] == "saleor"]
    rmcss_sc_dev = apply_model(sc, m, thr, sc_dev)
    results["django_dev_to_saleor_dev"] = {
        "threshold": dc_thr,
        **eval_split(sc_dev, "saleor", dev_sip, rmcss_sc_dev, dev_proxy),
    }

    # --- djangoCMS DEV -> corrected exposed Saleor Stage-5 ---
    sc5 = s5[s5["repository"] == "saleor"]
    rmcss_sc5 = apply_model(sc, m, thr, sc5)
    results["django_dev_to_saleor_stage5"] = {
        "threshold": dc_thr,
        **eval_split(sc5, "saleor", s5_sip, rmcss_sc5, s5_proxy),
    }

    # --- Saleor DEV -> djangoCMS DEV (reverse; expected weaker) ---
    sc_thr = fit_threshold(dev, "saleor")
    sc2, m2, thr2 = train_on_repo(dev, "saleor", sc_thr)
    dc_dev = dev[dev["repository"] == "djangocms"]
    rmcss_dc_dev = apply_model(sc2, m2, thr2, dc_dev)
    results["saleor_dev_to_django_dev"] = {
        "threshold": sc_thr,
        **eval_split(dc_dev, "djangocms", dev_sip, rmcss_dc_dev, dev_proxy),
    }

    (REPORTS / "v2_cross_repo_transfer.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(json.dumps(results, indent=1))
    print("[xfer] wrote reports/v2_cross_repo_transfer.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
