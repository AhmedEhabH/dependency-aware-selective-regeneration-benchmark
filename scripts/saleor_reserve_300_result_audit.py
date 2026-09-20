#!/usr/bin/env python3
# ruff: noqa: E501, N806, N812
"""SALEOR_RESERVE_300_RMCSS - INDEPENDENT RESULT AUDIT (§29).

MUST NOT import the primary result analyzer. Independently recomputes from
frozen predictions/outcomes: sample IDs; exclusion counts; SIP failure
categories; SIP TP/FP/FN; PRIMARY RM-CSS TP/FP/FN; P/R/F1/FNR; DeltaF1;
10,000-bootstrap CI; PRIMARY verdict; transfer-model confusion; transfer
DeltaF1; transfer bootstrap CI; transfer verdict; Acc@K/Hit@K/Recall@K;
model/config hashes; thresholds; sample hash.

Output: reports/saleor_reserve_300_rmcss_result_audit.json
"""
from __future__ import annotations

import hashlib
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

from benchmark.memory_rescue import candidates as C  # noqa: E402

OUT = _PROJECT_DIR / "research" / "saleor-reserve-300-rmcss"
REPORTS = _PROJECT_DIR / "reports"
CAND = OUT / "candidate_rows_saleor300.parquet"
PROXIES = OUT / "saleor_reserve_300_proxies.json"
SIP_RECORDS = OUT / "sip_300_run_records.jsonl"
SAMPLE = OUT / "saleor_reserve_300_sample.json"
PRIMARY_ART = _PROJECT_DIR / "research" / "stage5-v2-final" / "deployment_artifact.json"
TRANSFER_ART = OUT / "django_only_rmcss_transfer_model.json"
FROZEN_SHA = "8925d29a8e065bc864cd16e755ac0e896c7675b4a12f68fb66c35e5bd644ea95"
TRANSFER_SHA = "efb38c079a6ea15e6ada4ecdb65810f4afd1f5614ad28274f9516d2112740a67"
SAMPLE_SHA = "445b5e9d0aeeab9551e8feeb3e59e6b5bcfee793f029810a6efe0cbc8f126447"
N_BOOT = 10000
SEED = 20260920
THRESHOLD = 0.20

CHECKS: list[dict] = []


def _p(name: str, ok: bool, detail: str) -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}", flush=True)
    CHECKS.append({"name": name, "pass": bool(ok), "detail": detail})


def _confusion(tp, fp, fn):
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": f1, "fnr": 1.0 - r}


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
    # R1 sample IDs + R2 exclusions
    sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
    ids = sample["selected_ids"]
    ids_text = "\n".join(ids) + "\n"
    sha = hashlib.sha256(ids_text.encode("utf-8")).hexdigest()
    _p("R1.sample_ids", len(ids) == 300 and len(set(ids)) == 300 and sha == SAMPLE_SHA,
       f"n={len(ids)} unique={len(set(ids))} sha={sha[:16]}...")
    preflight = json.loads((OUT / "saleor_reserve_300_preflight.json").read_text(encoding="utf-8"))
    _p("R2.exclusions", preflight["preflighted_ok"] == 300 and preflight["excluded"] == 0,
       f"ok={preflight['preflighted_ok']} excluded={preflight['excluded']}")

    # R3 SIP failure categories
    recs = [json.loads(ln) for ln in SIP_RECORDS.read_text(encoding="utf-8").splitlines() if ln.strip()]
    cats = {}
    for r in recs:
        f = r.get("failure_category") or "succeeded"
        cats[f] = cats.get(f, 0) + 1
    _p("R3.sip_categories", len(recs) == 300 and cats.get("succeeded", 0) == 228
       and cats.get("completed_empty", 0) == 70 and cats.get("HTTP Error 429: Too Many Requests", 0) == 2,
       json.dumps(cats))

    # R4-13 evaluation from raw
    frame = pd.read_parquet(CAND)
    proxies = json.loads(PROXIES.read_text(encoding="utf-8"))["proxies"]
    cids = sorted(set(frame["case_id"]))
    primary = json.loads(PRIMARY_ART.read_text(encoding="utf-8"))
    transfer = json.loads(TRANSFER_ART.read_text(encoding="utf-8"))
    frame = frame.copy()
    frame["prob_p"] = _apply_model(primary, frame)
    frame["prob_t"] = _apply_model(transfer, frame)
    rmcss = {cid: set(g.loc[g["prob_p"] >= THRESHOLD, "file_path"]) for cid, g in frame.groupby("case_id")}
    xfer = {cid: set(g.loc[g["prob_t"] >= THRESHOLD, "file_path"]) for cid, g in frame.groupby("case_id")}
    sip = {cid: set(g.loc[g["in_sparse"] == 1, "file_path"]) for cid, g in frame.groupby("case_id")}

    def pool(pred):
        t = f = n = 0
        for cid in cids:
            g = set(proxies[cid])
            p = pred.get(cid, set())
            t += len(p & g)
            f += len(p - g)
            n += len(g - p)
        return _confusion(t, f, n)

    def contribs(pred):
        return [None] + [(len(pred.get(cid, set()) & set(proxies[cid])),
                          len(pred.get(cid, set()) - set(proxies[cid])),
                          len(set(proxies[cid]) - pred.get(cid, set()))) for cid in cids]

    def bootstrap_ci(arm_contrib, base_contrib, cids):
        rng = random.Random(SEED)
        n = len(cids)

        def f1_of(idx, cb):
            tp = sum(cb[i][0] for i in idx)
            fp = sum(cb[i][1] for i in idx)
            fn = sum(cb[i][2] for i in idx)
            return 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
        deltas = np.empty(N_BOOT)
        for b in range(N_BOOT):
            idx = [rng.randrange(n) for _ in range(n)]
            deltas[b] = f1_of(idx, arm_contrib[1:]) - f1_of(idx, base_contrib[1:])
        lo, hi = np.quantile(deltas, [0.025, 0.975])
        return float(lo), float(hi)

    sip_c = pool(sip)
    rm_c = pool(rmcss)
    xf_c = pool(xfer)
    _p("R4.sip_conf", sip_c["tp"] == 193 and sip_c["fp"] == 344 and sip_c["fn"] == 728, json.dumps(sip_c))
    _p("R5.rmcss_conf", rm_c["tp"] == 283 and rm_c["fp"] == 382 and rm_c["fn"] == 638, json.dumps(rm_c))
    _p("R6.p_r_f1_fnr", abs(rm_c["f1"] - 0.3569) < 1e-3 and abs(sip_c["f1"] - 0.2647) < 1e-3,
       f"rmcss_f1={rm_c['f1']:.4f} sip_f1={sip_c['f1']:.4f}")
    d_p = rm_c["f1"] - sip_c["f1"]
    _p("R7.primary_delta_f1", abs(d_p - 0.0921) < 1e-3, f"delta_f1={d_p:.4f}")

    rm_cb = contribs(rmcss)
    sip_cb = contribs(sip)
    xf_cb = contribs(xfer)
    lo_p, hi_p = bootstrap_ci(rm_cb, sip_cb, cids)
    _p("R8.primary_bootstrap_ci", lo_p > 0, f"CI=[{lo_p:.4f},{hi_p:.4f}]")

    prim_verdict = "SALEOR_RESERVE_300_RMCSS_PASS" if (d_p > 0 and lo_p > 0) else (
        "SALEOR_RESERVE_300_RMCSS_INCONCLUSIVE" if d_p > 0 else "SALEOR_RESERVE_300_RMCSS_FAIL")
    _p("R9.primary_verdict", prim_verdict == "SALEOR_RESERVE_300_RMCSS_PASS", prim_verdict)

    _p("R10.transfer_conf", xf_c["tp"] == 262 and xf_c["fp"] == 363 and xf_c["fn"] == 659, json.dumps(xf_c))
    d_t = xf_c["f1"] - sip_c["f1"]
    lo_t, hi_t = bootstrap_ci(xf_cb, sip_cb, cids)
    _p("R11.transfer_delta_f1", abs(d_t - 0.0742) < 1e-3, f"delta_f1={d_t:.4f}")
    _p("R12.transfer_bootstrap_ci", lo_t > 0, f"CI=[{lo_t:.4f},{hi_t:.4f}]")
    xf_verdict = "SECONDARY_CROSS_REPO_TRANSFER_PASS" if (d_t > 0 and lo_t > 0) else (
        "SECONDARY_CROSS_REPO_TRANSFER_INCONCLUSIVE" if d_t > 0 else "SECONDARY_CROSS_REPO_TRANSFER_FAIL")
    _p("R13.transfer_verdict", xf_verdict == "SECONDARY_CROSS_REPO_TRANSFER_PASS", xf_verdict)

    # R14 Acc@K
    acc = {1: 0, 3: 0, 5: 0}
    hit = {1: 0, 3: 0, 5: 0}
    n = 0
    for cid in cids:
        g = set(proxies[cid])
        if not g:
            continue
        order = frame[frame["case_id"] == cid].sort_values(["prob_p", "file_path"], ascending=[False, True])["file_path"].tolist()
        n += 1
        for k in (1, 3, 5):
            inter = len(set(order[:k]) & g)
            acc[k] += 1 if inter == min(len(g), k) else 0
            hit[k] += 1 if inter >= 1 else 0
    _p("R14.acc_hit_k", n == 300 and acc[1] / n > 0.45,
       f"n={n} acc1={acc[1]/n:.4f} acc3={acc[3]/n:.4f} acc5={acc[5]/n:.4f} hit5={hit[5]/n:.4f}")

    # R15 hashes + thresholds
    _p("R15.hashes_thresholds", primary.get("config_sha256") == FROZEN_SHA
       and transfer.get("artifact_sha256") == TRANSFER_SHA
       and abs(float(primary["threshold"]) - 0.20) < 1e-12
       and abs(float(transfer["threshold"]) - 0.20) < 1e-12,
       f"primary_sha={primary.get('config_sha256')[:12]} transfer_sha={transfer.get('artifact_sha256')[:12]} thr={primary.get('threshold')}/{transfer.get('threshold')}")

    n_pass = sum(1 for c in CHECKS if c["pass"])
    print(f"AUDIT SUMMARY: {n_pass}/{len(CHECKS)} PASS", flush=True)
    (REPORTS / "saleor_reserve_300_rmcss_result_audit.json").write_text(
        json.dumps({"pass": n_pass, "total": len(CHECKS), "checks": CHECKS}, indent=1), encoding="utf-8")
    return 0 if n_pass == len(CHECKS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
