#!/usr/bin/env python3
# ruff: noqa: N806, N812
"""SALEOR_RESERVE_300_RMCSS - PRIMARY + SECONDARY evaluation (§20-23, §24).

PRIMARY: frozen all-DEV RM-CSS vs SIP on the 300 Saleor RESERVE tasks.
SECONDARY: DJANGO_ONLY_RMCSS_TRANSFER_MODEL vs SIP (non-gating).

Metrics: TP/FP/FN/P/R/F1/FNR; DeltaF1 with 10,000 task-paired bootstrap seed
20260920; PRIMARY verdict (PASS/INCONCLUSIVE/FAIL); SECONDARY verdict
(PASS/INCONCLUSIVE/FAIL). Required secondary metrics (set sizes, additions,
drops) and paired CIs for Delta P/R/FNR/F1 (PRIMARY).

Output: reports/saleor_reserve_300_rmcss_result.json
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

from benchmark.calibrated.policy import confusion, per_task_confusion  # noqa: E402
from benchmark.memory_rescue import candidates as C  # noqa: E402

OUT = _PROJECT_DIR / "research" / "saleor-reserve-300-rmcss"
REPORTS = _PROJECT_DIR / "reports"
CAND = OUT / "candidate_rows_saleor300.parquet"
PROXIES = OUT / "saleor_reserve_300_proxies.json"
PRIMARY_ART = _PROJECT_DIR / "research" / "stage5-v2-final" / "deployment_artifact.json"
TRANSFER_ART = OUT / "django_only_rmcss_transfer_model.json"
N_BOOT = 10000
SEED = 20260920
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


def _bootstrap_ci(v2c: list, spc: list, cids: list) -> dict:
    rng = random.Random(SEED)
    n = len(cids)

    def pool(contribs, idx):
        tp = sum(contribs[i][0] for i in idx)
        fp = sum(contribs[i][1] for i in idx)
        fn = sum(contribs[i][2] for i in idx)
        return 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0

    metrics = ("precision", "recall", "fnr", "f1")
    out = {}
    for m in metrics:
        deltas = np.empty(N_BOOT)
        for b in range(N_BOOT):
            idx = [rng.randrange(n) for _ in range(n)]
            dv = confusion(*(sum(v2c[i][j] for i in idx) for j in range(3)))[m]
            ds = confusion(*(sum(spc[i][j] for i in idx) for j in range(3)))[m]
            deltas[b] = dv - ds
        lo, hi = np.quantile(deltas, [0.025, 0.975])
        dp = confusion(*(sum(v2c[i][j] for i in range(n)) for j in range(3)))[m]
        sp = confusion(*(sum(spc[i][j] for i in range(n)) for j in range(3)))[m]
        out[m] = {"point_delta": float(dp - sp), "ci95_lower": float(lo), "ci95_upper": float(hi)}
    return out


def main() -> int:
    frame = pd.read_parquet(CAND)
    proxies = json.loads(PROXIES.read_text(encoding="utf-8"))["proxies"]
    cids = sorted(set(frame["case_id"]))
    assert len(cids) == 300, len(cids)

    primary = json.loads(PRIMARY_ART.read_text(encoding="utf-8"))
    transfer = json.loads(TRANSFER_ART.read_text(encoding="utf-8"))

    frame = frame.copy()
    frame["prob_primary"] = _apply_model(primary, frame)
    frame["prob_transfer"] = _apply_model(transfer, frame)

    rmcss_sets = {}
    xfer_sets = {}
    sip_sets = {}
    for cid, g in frame.groupby("case_id"):
        rmcss_sets[cid] = set(g.loc[g["prob_primary"] >= THRESHOLD, "file_path"])
        xfer_sets[cid] = set(g.loc[g["prob_transfer"] >= THRESHOLD, "file_path"])
        sip_sets[cid] = set(g.loc[g["in_sparse"] == 1, "file_path"])

    def eval_arm(pred: dict[str, set[str]], label: str) -> dict:
        c = [per_task_confusion(pred.get(cid, set()), set(proxies[cid])) for cid in cids]
        sc = [per_task_confusion(sip_sets[cid], set(proxies[cid])) for cid in cids]
        pool = tuple(sum(x[i] for x in c) for i in range(3))
        spool = tuple(sum(x[i] for x in sc) for i in range(3))
        ci = _bootstrap_ci(c, sc, cids)
        return {
            "confusion": confusion(*pool), "sip": confusion(*spool),
            "ci": ci, "per_task": c, "sip_per_task": sc,
            "label": label,
        }

    prim = eval_arm(rmcss_sets, "RM-CSS")
    xfer = eval_arm(xfer_sets, "transfer")

    # set sizes / additions / drops
    def set_stats(pred, sip):
        sizes = [len(pred[c]) for c in cids]
        add = [len(pred[c] - sip[c]) for c in cids]
        drop = [len(sip[c] - pred[c]) for c in cids]
        return {
            "mean_set_size": round(float(np.mean(sizes)), 4),
            "median_set_size": float(np.median(sizes)),
            "empty_set_rate": round(float(np.mean([1 if s == 0 else 0 for s in sizes])), 4),
            "mean_additions_vs_sip": round(float(np.mean(add)), 4),
            "mean_drops_vs_sip": round(float(np.mean(drop)), 4),
        }

    prim_stats = set_stats(rmcss_sets, sip_sets)
    xfer_stats = set_stats(xfer_sets, sip_sets)
    sip_stats = set_stats(sip_sets, sip_sets)

    # PRIMARY verdict
    d = prim["ci"]["f1"]
    if prim["confusion"]["f1"] - prim["sip"]["f1"] > 0 and d["ci95_lower"] > 0:
        prim_verdict = "SALEOR_RESERVE_300_RMCSS_PASS"
    elif prim["confusion"]["f1"] - prim["sip"]["f1"] > 0:
        prim_verdict = "SALEOR_RESERVE_300_RMCSS_INCONCLUSIVE"
    else:
        prim_verdict = "SALEOR_RESERVE_300_RMCSS_FAIL"

    # SECONDARY verdict
    d2 = xfer["ci"]["f1"]
    if xfer["confusion"]["f1"] - xfer["sip"]["f1"] > 0 and d2["ci95_lower"] > 0:
        xfer_verdict = "SECONDARY_CROSS_REPO_TRANSFER_PASS"
    elif xfer["confusion"]["f1"] - xfer["sip"]["f1"] > 0:
        xfer_verdict = "SECONDARY_CROSS_REPO_TRANSFER_INCONCLUSIVE"
    else:
        xfer_verdict = "SECONDARY_CROSS_REPO_TRANSFER_FAIL"

    result = {
        "n_tasks": len(cids),
        "primary": {
            "verdict": prim_verdict,
            "rmcss": prim["confusion"], "sip": prim["sip"],
            "delta_f1": prim["confusion"]["f1"] - prim["sip"]["f1"],
            "ci": prim["ci"],
            "set_stats": prim_stats,
        },
        "secondary_transfer": {
            "verdict": xfer_verdict,
            "transfer": xfer["confusion"], "sip": xfer["sip"],
            "delta_f1": xfer["confusion"]["f1"] - xfer["sip"]["f1"],
            "ci": xfer["ci"],
            "set_stats": xfer_stats,
        },
        "sip_set_stats": sip_stats,
        "bootstrap": {"n_resamples": N_BOOT, "seed": SEED, "ci": "[Q2.5,Q97.5]"},
        "threshold": THRESHOLD,
        "impact_localization_selection_closed": "IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED",
    }
    (REPORTS / "saleor_reserve_300_rmcss_result.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(json.dumps(result, indent=1))
    print("[s300-eval] PRIMARY verdict:", prim_verdict)
    print("[s300-eval] SECONDARY verdict:", xfer_verdict)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
