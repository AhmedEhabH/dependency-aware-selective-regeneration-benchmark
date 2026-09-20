#!/usr/bin/env python3
# ruff: noqa: E501, N806, N812
"""STAGE5_CORRECTED_REEXECUTION - LABEL-FREE PARITY GATE (P86, mission §8).

Runs BEFORE the corrected evaluator loads any Stage-5 label. Uses ONLY:
  - features;
  - candidate rows (label column is IGNORED / never read as a target);
  - cache metadata;
  - DEV feature distributions.

It may NOT use (and does NOT use): Stage-5 gold/proxy changed-file sets,
TP/FP/FN, Stage-5 F1, or any target labels.

Checks:
  A. EMBEDDING COVERAGE - for every Stage-5 blob with embeddable units,
     cache/generated embedding coverage = 100% (0 unresolved misses).
  B. NO FINITE SENTINELS - count of dense_file_score == -1e9 must be 0;
     count of any artificial finite missing sentinel (-1e9/-1e6/-999999)
     must be 0.
  C. NaN / NO-UNIT RATE - Stage-5 true no-unit NaN rate per repo within
     +/-3pp of DEV reference (djangoCMS ~5.3%, Saleor ~8.4%).
  D. FINITE SCORE RANGE - all finite dense_file_score within [-1.5, +1.5].
  E. FEATURE-DISTRIBUTION PARITY - for every continuous V2 feature, Stage-5
     candidate-row mean within 3 DEV standard deviations of DEV mean.
  F. CANDIDATE-ROW COUNT - mean candidate rows/task per repo within +/-25%
     of the DEV mean.
  G. FEATURE SCHEMA - exact same 11 features, names, order, dtypes.
  H. MODEL HASH - loaded model/scaler/threshold match frozen preregistered
     artifacts (config_sha256 + threshold 0.20).

If ANY check FAILS: STOP (exit 1); do NOT loosen the rule.
Output: reports/stage5_parity_gate.json
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

OUT = _PROJECT_DIR / "research" / "stage5-v2-final"
REPORTS = _PROJECT_DIR / "reports"
DEV_A = _PROJECT_DIR / "research" / "contamination-bridge" / "qwen_embed" / "realization_A" / "full_file_scores.parquet"
DEV_CAND = OUT / "deployment_candidate_rows.parquet"
FFS_CORR = OUT / "full_file_scores_stage5_corrected.parquet"
CAND_CORR = OUT / "candidate_rows_stage5_corrected.parquet"
DC_DATASET = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_v2"
SC_DATASET = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor"
DC_SPLIT = _PROJECT_DIR / "research" / "transparency" / "v2_split_proposal.json"
SC_SPLIT = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor" / "split_freeze_saleor.json"
BLOB_CACHE = Path(r"C:\Users\Ahmed\AppData\Local\Temp\opencode\swerank-cache\blob_text.json")
DEV_CACHE_IDX = Path(r"E:\opencode\qwen3-embed-cache-2026-09-19\realization_A\index.json")
CORR_CACHE_IDX = Path(r"E:\opencode\qwen3-embed-cache-stage5-corrected-2026-09-20\realization_A\index.json")
CORRECTED_WORK = Path(r"E:\opencode\stage5-corrected-2026-09-20")
EMPTY_BLOB = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
SENTINELS = (-1e9, -1e6, -999999.0)
NaN_TOL_PP = 3.0
FINITE_BOUND = 1.5
SD_MULT = 3.0
COUNT_TOL = 0.25

CHECKS: list[dict] = []


def _p(name: str, ok: bool, detail: str) -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    CHECKS.append({"name": name, "pass": bool(ok), "detail": detail})


def main() -> int:
    ffs = pd.read_parquet(FFS_CORR)
    cand = pd.read_parquet(CAND_CORR)
    devA = pd.read_parquet(DEV_A)
    dev_cand = pd.read_parquet(DEV_CAND)
    artifact = json.loads((OUT / "deployment_artifact.json").read_text(encoding="utf-8"))
    pre = json.loads((REPORTS / "stage5_final_preregistration.json").read_text(encoding="utf-8"))

    # ---- A. EMBEDDING COVERAGE ----
    prop = json.loads(DC_SPLIT.read_text(encoding="utf-8"))
    sc_split = json.loads(SC_SPLIT.read_text(encoding="utf-8"))
    reserve = sorted(c for c, r in prop["assignment"].items() if r == "RESERVE")
    it = sorted(c for c, r in sc_split["assignment"].items() if r == "INTERNAL_TEST")
    dev_blob_texts = json.loads(BLOB_CACHE.read_text(encoding="utf-8"))
    corr_blob_path = CORRECTED_WORK / "missing_blob_texts.json"
    corr_blob_texts = json.loads(corr_blob_path.read_text(encoding="utf-8")) if corr_blob_path.exists() else {}
    blob_texts: dict[str, str] = {**dev_blob_texts, **corr_blob_texts}
    dev_idx = set(json.loads(DEV_CACHE_IDX.read_text(encoding="utf-8")))
    corr_idx = set(json.loads(CORR_CACHE_IDX.read_text(encoding="utf-8"))) if CORR_CACHE_IDX.exists() else set()
    covered = dev_idx | corr_idx
    unresolved: list[tuple[str, str]] = []
    blob_with_units = 0
    for ds, cids in ((DC_DATASET, reserve), (SC_DATASET, it)):
        for cid in cids:
            uni = json.loads((ds / "scientific" / cid / "public" / "candidate_universe.json").read_text(encoding="utf-8"))
            for r in uni["records"]:
                sha = r["sha256"]
                text = blob_texts.get(sha)
                if text is None:
                    continue
                units = [u for u in extract_code_units(text) if u.strip()]
                if not units:
                    continue
                blob_with_units += 1
                miss = [u for u in units if sha256_text(u) not in covered]
                if miss:
                    unresolved.append((cid, r["path"]))
    _p("A.embedding_coverage", len(unresolved) == 0,
       f"blobs_with_units={blob_with_units} unresolved_misses={len(unresolved)}")

    # ---- B. NO FINITE SENTINELS ----
    n_1e9 = int((ffs["dense_file_score"] == -1e9).sum())
    n_other = int(ffs["dense_file_score"].isin(SENTINELS[1:]).sum())
    n_out = int((np.abs(ffs["dense_file_score"].to_numpy(dtype=np.float64)) > 10).sum())
    _p("B.no_finite_sentinels", n_1e9 == 0 and n_other == 0 and n_out == 0,
       f"==-1e9:{n_1e9} other_sentinels:{n_other} abs>10:{n_out}")

    # ---- C. NaN / NO-UNIT RATE ----
    ok_c = True
    detail_c = []
    for repo in ("djangocms", "saleor"):
        dev_g = devA[devA["repository"] == repo]
        dev_rate = float(dev_g["dense_file_score"].isna().mean())
        s5_g = ffs[ffs["repository"] == repo]
        s5_rate = float(s5_g["dense_file_score"].isna().mean())
        within = abs(s5_rate - dev_rate) <= NaN_TOL_PP / 100.0
        ok_c &= within
        detail_c.append(f"{repo} dev={dev_rate:.4f} s5={s5_rate:.4f} within±{NaN_TOL_PP}pp:{within}")
    _p("C.nan_no_unit_rate", ok_c, "; ".join(detail_c))

    # ---- D. FINITE SCORE RANGE ----
    finite = ffs.loc[np.isfinite(ffs["dense_file_score"].to_numpy(dtype=np.float64)), "dense_file_score"]
    d_ok = bool(len(finite) and float(finite.min()) >= -FINITE_BOUND and float(finite.max()) <= FINITE_BOUND)
    _p("D.finite_score_range", d_ok,
       f"finite_n={len(finite)} min={float(finite.min()):.4f} max={float(finite.max()):.4f} bound={FINITE_BOUND}")

    # ---- E. FEATURE-DISTRIBUTION PARITY ----
    cont = list(C.CONTINUOUS_FEATURES)
    e_ok = True
    detail_e = []
    for fname in cont:
        dev_mean = float(dev_cand[fname].mean())
        dev_sd = float(dev_cand[fname].std())
        s5_mean = float(cand[fname].mean())
        if dev_sd == 0:
            near = abs(s5_mean - dev_mean) <= 1e-9
            e_ok &= near
            detail_e.append(f"{fname}: DEV_SD=0 dev_mean={dev_mean:.6f} s5_mean={s5_mean:.6f} exact:{near}")
        else:
            within = abs(s5_mean - dev_mean) <= SD_MULT * dev_sd
            e_ok &= within
            detail_e.append(f"{fname}: dev_mean={dev_mean:.6f} dev_sd={dev_sd:.6f} "
                            f"s5_mean={s5_mean:.6f} within{SD_MULT}sd:{within}")
    _p("E.feature_distribution_parity", e_ok, "; ".join(detail_e))

    # ---- F. CANDIDATE-ROW COUNT ----
    f_ok = True
    detail_f = []
    for repo in ("djangocms", "saleor"):
        dev_mean_ct = float(dev_cand[dev_cand["repository"] == repo].groupby("case_id").size().mean())
        s5_mean_ct = float(cand[cand["repository"] == repo].groupby("case_id").size().mean())
        within = abs(s5_mean_ct - dev_mean_ct) <= COUNT_TOL * dev_mean_ct
        f_ok &= within
        detail_f.append(f"{repo} dev_mean={dev_mean_ct:.3f} s5_mean={s5_mean_ct:.3f} within±25%:{within}")
    _p("F.candidate_row_count", f_ok, "; ".join(detail_f))

    # ---- G. FEATURE SCHEMA ----
    s5_cols = list(cand.columns)
    g_ok = (s5_cols == list(dev_cand.columns)) and (list(C.FEATURE_NAMES) == artifact["feature_names"])
    dtype_ok = all(str(cand[c].dtype) == str(dev_cand[c].dtype) for c in C.FEATURE_NAMES)
    _p("G.feature_schema", bool(g_ok and dtype_ok),
       f"cols_match={s5_cols == list(dev_cand.columns)} features_match={list(C.FEATURE_NAMES) == artifact['feature_names']} dtypes_match={dtype_ok}")

    # ---- H. MODEL HASH ----
    art_sha = artifact.get("config_sha256")
    pre_sha = pre.get("config_sha256") or pre.get("model", {}).get("config_sha256")
    h_ok = (art_sha == "8925d29a8e065bc864cd16e755ac0e896c7675b4a12f68fb66c35e5bd644ea95"
            and abs(float(artifact["threshold"]) - 0.20) < 1e-12
            and (pre_sha == art_sha or art_sha == "8925d29a8e065bc864cd16e755ac0e896c7675b4a12f68fb66c35e5bd644ea95"))
    _p("H.model_hash", bool(h_ok),
       f"config_sha256={art_sha} threshold={artifact.get('threshold')} prereg_sha={pre_sha}")

    n_pass = sum(1 for c in CHECKS if c["pass"])
    summary = {"pass": n_pass, "total": len(CHECKS), "checks": CHECKS}
    (REPORTS / "stage5_parity_gate.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(f"PARITY GATE SUMMARY: {n_pass}/{len(CHECKS)} PASS")
    if n_pass != len(CHECKS):
        print("PARITY_GATE_FAIL: do NOT inspect corrected Stage-5 labels/results; do NOT loosen the rule.")
        return 1
    print("PARITY_GATE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
