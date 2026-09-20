#!/usr/bin/env python3
# ruff: noqa: E501, N806, N812
"""STAGE5_CORRECTED_REEXECUTION - apply frozen final V2 model + primary endpoint.

Applies the frozen final deployment V2 model (DEV refit, threshold 0.20) to the
CORRECTED Stage-5 candidate rows (embedding-coverage defect repaired) and
computes the EXACT preregistered primary endpoint:

  - V2 final sets (candidate prob >= 0.20);
  - Sparse final sets (persisted write sets, reused exactly);
  - per-repo P/R/F1/FNR + TP/FP/FN for V2 and Sparse;
  - PRIMARY endpoint: repo-stratified pooled micro-F1 difference (V2 - Sparse),
    10,000 resamples, seed 20260920, CI95 [Q2.5,Q97.5];
  - direction consistency (dc point delta > 0 AND saleor point delta > 0);
  - corrected result label.

The corrected result label is ONE OF:
  STAGE5_CORRECTED_REEXECUTION_POSITIVE
  STAGE5_CORRECTED_REEXECUTION_NEGATIVE
  STAGE5_CORRECTED_REEXECUTION_MIXED
(NOT STAGE5_V2_FINAL_CONFIRMATION_PASS), because the population is no longer
untouched.

No model retraining. No threshold change. Deterministic.
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

from benchmark.calibrated.policy import confusion, per_task_confusion  # noqa: E402
from benchmark.memory_rescue import candidates as C  # noqa: E402

OUT = _PROJECT_DIR / "research" / "stage5-v2-final"
REPORTS = _PROJECT_DIR / "reports"
ARTIFACT = json.loads((OUT / "deployment_artifact.json").read_text(encoding="utf-8"))
DC_SPLIT = _PROJECT_DIR / "research" / "transparency" / "v2_split_proposal.json"
SC_SPLIT = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor" / "split_freeze_saleor.json"
N_BOOT = 10000
SEED = 20260920
THRESHOLD = float(ARTIFACT["threshold"])
ROWS_PATH = OUT / "candidate_rows_stage5_corrected.parquet"
PROB_PATH = OUT / "v2_probabilities_stage5_corrected.parquet"
RESULT_PATH = REPORTS / "stage5_corrected_reexecution_result.json"


def _case_roles() -> list[dict]:
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
    rows = pd.read_parquet(ROWS_PATH)
    roles = _case_roles()
    assert len(roles) == 139, len(roles)

    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    scaler = StandardScaler()
    scaler.mean_ = np.asarray(ARTIFACT["scaler_mean"], dtype=np.float64)
    scaler.scale_ = np.asarray(ARTIFACT["scaler_scale"], dtype=np.float64)
    scaler.var_ = scaler.scale_ ** 2
    scaler.n_features_in_ = len(ARTIFACT["scaler_mean"])
    model = LogisticRegression(penalty="l2", C=1.0, solver="liblinear",
                               max_iter=1000, random_state=0)

    idx_cont = [C.FEATURE_NAMES.index(c) for c in C.CONTINUOUS_FEATURES]
    idx_bool = [C.FEATURE_NAMES.index(c) for c in C.BOOLEAN_FEATURES]

    X = C.feature_matrix(rows)
    X_cont = scaler.transform(X[:, idx_cont])
    X_bool = X[:, idx_bool].astype(np.float64)
    X_scaled = np.concatenate([X_cont, X_bool], axis=1)
    coef = np.asarray(ARTIFACT["lr_coef"], dtype=np.float64).reshape(1, -1)
    intercept = np.asarray([ARTIFACT["lr_intercept"]], dtype=np.float64)
    model.coef_ = coef
    model.intercept_ = intercept
    model.classes_ = np.asarray([0, 1])
    model.n_features_in_ = X_scaled.shape[1]

    rows = rows.copy()
    rows["prob"] = model.predict_proba(X_scaled)[:, 1]
    rows["selected"] = (rows["prob"].to_numpy() >= THRESHOLD).astype(int)
    rows.to_parquet(PROB_PATH, index=False, compression="zstd")

    v2_sets: dict[str, set[str]] = {}
    sparse_sets: dict[str, set[str]] = {}
    for cid, g in rows.groupby("case_id"):
        v2_sets[cid] = set(g.loc[g["selected"] == 1, "file_path"])
        sparse_sets[cid] = set(g.loc[g["in_sparse"] == 1, "file_path"])

    import importlib
    p1 = importlib.import_module("benchmark.real_commits.p1_evaluation")
    task_proxy: dict[str, set[str]] = {}
    for r in roles:
        ds = (_PROJECT_DIR / "benchmark_data" / "real_commit_impact_v2") if r["repo"] == "djangocms" \
            else (_PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor")
        task_proxy[r["case_id"]] = set(p1.load_hidden_proxy_paths(ds, r["case_id"]))

    repo_metrics: dict[str, dict] = {}
    repo_conf: dict[str, dict[str, dict]] = {}
    for repo in ("djangocms", "saleor"):
        cids = [r["case_id"] for r in roles if r["repo"] == repo]
        v2c = [per_task_confusion(v2_sets[c], task_proxy[c]) for c in cids]
        spc = [per_task_confusion(sparse_sets[c], task_proxy[c]) for c in cids]
        vtpfpfn = tuple(sum(x[i] for x in v2c) for i in range(3))
        stpfpfn = tuple(sum(x[i] for x in spc) for i in range(3))
        repo_metrics[repo] = {"v2": confusion(*vtpfpfn), "sparse": confusion(*stpfpfn),
                              "n_tasks": len(cids)}
        repo_conf[repo] = {"v2": vtpfpfn, "sparse": stpfpfn}

    dc_ids = [r["case_id"] for r in roles if r["repo"] == "djangocms"]
    sc_ids = [r["case_id"] for r in roles if r["repo"] == "saleor"]
    rng = random.Random(SEED)

    def pool_f1(contribs: dict[str, tuple], ids: list[str]) -> float:
        tp = sum(contribs[c][0] for c in ids)
        fp = sum(contribs[c][1] for c in ids)
        fn = sum(contribs[c][2] for c in ids)
        return 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0

    v2_contrib = {r["case_id"]: per_task_confusion(v2_sets[r["case_id"]], task_proxy[r["case_id"]])
                  for r in roles}
    sp_contrib = {r["case_id"]: per_task_confusion(sparse_sets[r["case_id"]], task_proxy[r["case_id"]])
                  for r in roles}

    deltas = np.empty(N_BOOT, dtype=np.float64)
    for b in range(N_BOOT):
        dc_sample = [dc_ids[rng.randrange(len(dc_ids))] for _ in range(len(dc_ids))]
        sc_sample = [sc_ids[rng.randrange(len(sc_ids))] for _ in range(len(sc_ids))]
        both = dc_sample + sc_sample
        deltas[b] = pool_f1(v2_contrib, both) - pool_f1(sp_contrib, both)
    lo, hi = np.quantile(deltas, [0.025, 0.975])

    pooled_tp_v = sum(v2_contrib[c][0] for c in dc_ids + sc_ids)
    pooled_fp_v = sum(v2_contrib[c][1] for c in dc_ids + sc_ids)
    pooled_fn_v = sum(v2_contrib[c][2] for c in dc_ids + sc_ids)
    pooled_tp_s = sum(sp_contrib[c][0] for c in dc_ids + sc_ids)
    pooled_fp_s = sum(sp_contrib[c][1] for c in dc_ids + sc_ids)
    pooled_fn_s = sum(sp_contrib[c][2] for c in dc_ids + sc_ids)
    f1_v_point = 2 * pooled_tp_v / (2 * pooled_tp_v + pooled_fp_v + pooled_fn_v) if (2 * pooled_tp_v + pooled_fp_v + pooled_fn_v) else 0.0
    f1_s_point = 2 * pooled_tp_s / (2 * pooled_tp_s + pooled_fp_s + pooled_fn_s) if (2 * pooled_tp_s + pooled_fp_s + pooled_fn_s) else 0.0
    delta_point = f1_v_point - f1_s_point

    dc_delta = repo_metrics["djangocms"]["v2"]["f1"] - repo_metrics["djangocms"]["sparse"]["f1"]
    sc_delta = repo_metrics["saleor"]["v2"]["f1"] - repo_metrics["saleor"]["sparse"]["f1"]

    A = delta_point > 0 and lo > 0
    B = dc_delta > 0 and sc_delta > 0
    if A and B:
        label = "STAGE5_CORRECTED_REEXECUTION_POSITIVE"
    elif A and not B:
        label = "STAGE5_CORRECTED_REEXECUTION_MIXED"
    else:
        label = "STAGE5_CORRECTED_REEXECUTION_NEGATIVE"

    result = {
        "primary_endpoint": {
            "n_dc": len(dc_ids), "n_saleor": len(sc_ids), "n_total": 139,
            "pooled_v2_f1": f1_v_point, "pooled_sparse_f1": f1_s_point,
            "delta_f1_point": delta_point,
            "ci95_lower": float(lo), "ci95_upper": float(hi),
            "resamples": N_BOOT, "seed": SEED,
        },
        "direction_consistency": {
            "dc_delta_f1": dc_delta, "saleor_delta_f1": sc_delta,
            "pass": bool(B),
        },
        "criteria": {"A_pooled_pass": bool(A), "B_direction_pass": bool(B)},
        "repo_metrics": repo_metrics,
        "repo_conf": repo_conf,
        "verdict": label,
        "impact_localization_selection_closed": "IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED",
        "disclosed_deviation": "embedding-coverage execution defect repaired; population previously exposed",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(json.dumps(result, indent=1))
    print("[s5c-eval] DONE verdict:", label)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
