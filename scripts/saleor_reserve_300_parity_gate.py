#!/usr/bin/env python3
# ruff: noqa: E501, N806, N812
"""SALEOR_RESERVE_300_RMCSS - LABEL-FREE PARITY GATE (§16).

Runs BEFORE loading hidden target outcomes. Uses ONLY features / candidate rows
(label column is all-zero/label-free) / cache metadata / DEV distributions.

Checks (frozen, §16):
  1 unresolved cache misses for embeddable blobs = 0
  2 finite missing-sentinel count = 0
  3 no-unit / NaN rate within ±3pp of frozen Saleor DEV rate (~8.35%)
  4 finite dense scores within [-1.5, +1.5]
  5 each continuous feature mean within 3 Saleor DEV SD of DEV mean
  6 candidate rows/task within ±25% of Saleor DEV
  7 exact 11-feature names/order
  8 primary model/scaler/threshold hashes exact
  9 secondary django-only model/scaler/threshold hashes exact
 10 sample manifest hash exact

If ANY fails: STOP; do NOT read hidden target outcomes; do NOT loosen the rule.
Output: reports/saleor_reserve_300_parity_gate.json
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

from benchmark.memory_rescue import candidates as C  # noqa: E402
from benchmark.signal.code_units import extract_code_units, sha256_text  # noqa: E402

OUT = _PROJECT_DIR / "research" / "saleor-reserve-300-rmcss"
REPORTS = _PROJECT_DIR / "reports"
DEV_A = _PROJECT_DIR / "research" / "contamination-bridge" / "qwen_embed" / "realization_A" / "full_file_scores.parquet"
DEV_CAND = _PROJECT_DIR / "research" / "stage5-v2-final" / "deployment_candidate_rows.parquet"
FFS = OUT / "full_file_scores_saleor300.parquet"
CAND = OUT / "candidate_rows_saleor300.parquet"
SC_DATASET = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor"
SAMPLE = OUT / "saleor_reserve_300_sample.json"
BLOB_CACHE = Path(r"C:\Users\Ahmed\AppData\Local\Temp\opencode\swerank-cache\blob_text.json")
CORRECTED_WORK = Path(r"E:\opencode\stage5-corrected-2026-09-20")
RESERVE_WORK = Path(r"E:\opencode\saleor-reserve-300-2026-09-20")
DEV_CACHE_IDX = Path(r"E:\opencode\qwen3-embed-cache-2026-09-19\realization_A\index.json")
CORR_CACHE_IDX = Path(r"E:\opencode\qwen3-embed-cache-stage5-corrected-2026-09-20\realization_A\index.json")
RES_CACHE_IDX = Path(r"E:\opencode\qwen3-embed-cache-saleor-reserve-300-2026-09-20\realization_A\index.json")
FROZEN_SHA = "8925d29a8e065bc864cd16e755ac0e896c7675b4a12f68fb66c35e5bd644ea95"
TRANSFER_SHA = "efb38c079a6ea15e6ada4ecdb65810f4afd1f5614ad28274f9516d2112740a67"
SAMPLE_SHA = "445b5e9d0aeeab9551e8feeb3e59e6b5bcfee793f029810a6efe0cbc8f126447"

CHECKS: list[dict] = []


def _p(name: str, ok: bool, detail: str) -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}", flush=True)
    CHECKS.append({"name": name, "pass": bool(ok), "detail": detail})


def main() -> int:
    ffs = pd.read_parquet(FFS)
    cand = pd.read_parquet(CAND)
    devA = pd.read_parquet(DEV_A)
    dev_cand = pd.read_parquet(DEV_CAND)
    sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
    selected = sample["selected_ids"]
    primary = json.loads((_PROJECT_DIR / "research" / "stage5-v2-final" / "deployment_artifact.json").read_text(encoding="utf-8"))
    transfer = json.loads((OUT / "django_only_rmcss_transfer_model.json").read_text(encoding="utf-8"))

    # 1. unresolved cache misses for embeddable blobs = 0
    dev_blob = json.loads(BLOB_CACHE.read_text(encoding="utf-8"))
    corr_blob = json.loads((CORRECTED_WORK / "missing_blob_texts.json").read_text(encoding="utf-8")) if (CORRECTED_WORK / "missing_blob_texts.json").exists() else {}
    res_blob = json.loads((RESERVE_WORK / "missing_blob_texts.json").read_text(encoding="utf-8")) if (RESERVE_WORK / "missing_blob_texts.json").exists() else {}
    blob_texts = {**dev_blob, **corr_blob, **res_blob}
    dev_idx = set(json.loads(DEV_CACHE_IDX.read_text(encoding="utf-8")))
    corr_idx = set(json.loads(CORR_CACHE_IDX.read_text(encoding="utf-8"))) if CORR_CACHE_IDX.exists() else set()
    res_idx = set(json.loads(RES_CACHE_IDX.read_text(encoding="utf-8"))) if RES_CACHE_IDX.exists() else set()
    covered = dev_idx | corr_idx | res_idx
    unresolved = 0
    blobs_with_units = 0
    for cid in selected:
        uni = json.loads((SC_DATASET / "scientific" / cid / "public" / "candidate_universe.json").read_text(encoding="utf-8"))
        for r in uni["records"]:
            text = blob_texts.get(r["sha256"])
            if text is None:
                continue
            units = [u for u in extract_code_units(text) if u.strip()]
            if not units:
                continue
            blobs_with_units += 1
            if any(sha256_text(u) not in covered for u in units):
                unresolved += 1
    _p("1.embedding_coverage", unresolved == 0, f"blobs_with_units={blobs_with_units} unresolved_misses={unresolved}")

    # 2. finite missing-sentinel count = 0
    n_1e9 = int((ffs["dense_file_score"] == -1e9).sum())
    n_1e6 = int((ffs["dense_file_score"] == -1e6).sum())
    n_999 = int((ffs["dense_file_score"] == -999999.0).sum())
    _p("2.no_finite_sentinels", n_1e9 == 0 and n_1e6 == 0 and n_999 == 0,
       f"==-1e9:{n_1e9} ==-1e6:{n_1e6} ==-999999:{n_999}")

    # 3. NaN rate within ±3pp of Saleor DEV (~8.35%)
    dev_rate = float(devA.loc[devA["repository"] == "saleor", "dense_file_score"].isna().mean())
    s5_rate = float(ffs["dense_file_score"].isna().mean())
    _p("3.nan_no_unit_rate", abs(s5_rate - dev_rate) <= 0.03,
       f"saleor_dev={dev_rate:.4f} reserve300={s5_rate:.4f} within±3pp:{abs(s5_rate - dev_rate) <= 0.03}")

    # 4. finite dense scores within [-1.5, +1.5]
    fin = ffs.loc[np.isfinite(ffs["dense_file_score"].to_numpy(dtype=np.float64)), "dense_file_score"]
    _p("4.finite_score_range", len(fin) > 0 and float(fin.min()) >= -1.5 and float(fin.max()) <= 1.5,
       f"min={float(fin.min()):.4f} max={float(fin.max()):.4f} bound=1.5")

    # 5. each continuous feature mean within 3 Saleor DEV SD
    dev_sc = dev_cand[dev_cand["repository"] == "saleor"]
    ok5 = True
    detail5 = []
    for f in list(C.CONTINUOUS_FEATURES):
        dm = float(dev_sc[f].mean())
        ds = float(dev_sc[f].std())
        sm = float(cand[f].mean())
        if ds == 0:
            near = abs(sm - dm) <= 1e-9
            ok5 &= near
            detail5.append(f"{f}: DEV_SD=0 dev={dm:.4f} s5={sm:.4f} exact:{near}")
        else:
            w = abs(sm - dm) <= 3.0 * ds
            ok5 &= w
            detail5.append(f"{f}: dev={dm:.4f} sd={ds:.4f} s5={sm:.4f} within3sd:{w}")
    _p("5.feature_means", ok5, "; ".join(detail5))

    # 6. candidate rows/task within ±25% of Saleor DEV
    dev_ct = float(dev_sc.groupby("case_id").size().mean())
    s5_ct = float(cand.groupby("case_id").size().mean())
    _p("6.candidate_rows_per_task", abs(s5_ct - dev_ct) <= 0.25 * dev_ct,
       f"dev={dev_ct:.3f} reserve300={s5_ct:.3f} within±25%:{abs(s5_ct - dev_ct) <= 0.25 * dev_ct}")

    # 7. exact 11-feature names/order
    _p("7.feature_schema", list(cand.columns) == list(dev_cand.columns)
       and list(C.FEATURE_NAMES) == primary["feature_names"],
       f"cols_match={list(cand.columns) == list(dev_cand.columns)} features_match={list(C.FEATURE_NAMES) == primary['feature_names']}")

    # 8. primary model/scaler/threshold hashes exact
    _p("8.primary_hashes", primary.get("config_sha256") == FROZEN_SHA
       and abs(float(primary["threshold"]) - 0.20) < 1e-12 and primary.get("realization") == "A",
       f"config_sha256={primary.get('config_sha256')} threshold={primary.get('threshold')} realization={primary.get('realization')}")

    # 9. secondary django-only model/scaler/threshold hashes exact
    _p("9.transfer_hashes", transfer.get("artifact_sha256") == TRANSFER_SHA
       and abs(float(transfer["threshold"]) - 0.20) < 1e-12 and transfer.get("model_id") == "DJANGO_ONLY_RMCSS_TRANSFER_MODEL",
       f"artifact_sha256={transfer.get('artifact_sha256')} threshold={transfer.get('threshold')}")

    # 10. sample manifest hash exact
    ids_text = "\n".join(selected) + "\n"
    import hashlib
    sha = hashlib.sha256(ids_text.encode("utf-8")).hexdigest()
    _p("10.sample_manifest_hash", sha == SAMPLE_SHA and len(selected) == 300,
       f"sha={sha} expected={SAMPLE_SHA}")

    n_pass = sum(1 for c in CHECKS if c["pass"])
    summary = {"pass": n_pass, "total": len(CHECKS), "checks": CHECKS}
    (REPORTS / "saleor_reserve_300_parity_gate.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(f"PARITY GATE SUMMARY: {n_pass}/{len(CHECKS)} PASS", flush=True)
    if n_pass != len(CHECKS):
        print("PARITY_GATE_FAIL: do NOT read hidden target outcomes; do NOT loosen the rule.")
        return 1
    print("PARITY_GATE_PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
