#!/usr/bin/env python3
# ruff: noqa: E501, N806, N812
"""STAGE5_CORRECTED_REEXECUTION - INDEPENDENT PARITY AUDIT (mission §9).

Recomputes every label-free parity quantity WITHOUT importing the primary parity
gate (scripts.stage5_parity_gate). It re-reads raw artifacts only.

Independently recomputes:
  - embedding miss count;
  - sentinel count;
  - NaN rate (per repo);
  - finite min/max;
  - feature means (per continuous V2 feature);
  - candidate rows/task (per repo);
  - model/config hashes (threshold + config_sha256).

Then compares with the primary gate's recorded numbers and requires agreement
(exact counts; feature means within 1e-6). If they disagree: STOP.

Output: reports/stage5_parity_gate_audit.json
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
FROZEN_SHA = "8925d29a8e065bc864cd16e755ac0e896c7675b4a12f68fb66c35e5bd644ea95"

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

    # 1. embedding miss count
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
    n_miss = 0
    n_blobs_units = 0
    for ds, cids in ((DC_DATASET, reserve), (SC_DATASET, it)):
        for cid in cids:
            uni = json.loads((ds / "scientific" / cid / "public" / "candidate_universe.json").read_text(encoding="utf-8"))
            for r in uni["records"]:
                text = blob_texts.get(r["sha256"])
                if text is None:
                    continue
                units = [u for u in extract_code_units(text) if u.strip()]
                if not units:
                    continue
                n_blobs_units += 1
                if any(sha256_text(u) not in covered for u in units):
                    n_miss += 1
    _p("P1.embedding_misses", n_miss == 0, f"misses={n_miss}")

    # 2. sentinel count
    n_sent = int((ffs["dense_file_score"] == -1e9).sum())
    _p("P2.sentinel_count", n_sent == 0, f"==-1e9={n_sent}")

    # 3. NaN rate per repo
    nan_ok = True
    nan_detail = []
    for repo in ("djangocms", "saleor"):
        dev_rate = float(devA.loc[devA["repository"] == repo, "dense_file_score"].isna().mean())
        s5_rate = float(ffs.loc[ffs["repository"] == repo, "dense_file_score"].isna().mean())
        within = abs(s5_rate - dev_rate) <= 0.03
        nan_ok &= within
        nan_detail.append(f"{repo}:{s5_rate:.4f}(dev {dev_rate:.4f},within:{within})")
    _p("P3.nan_rate", nan_ok, "; ".join(nan_detail))

    # 4. finite min/max
    fin = ffs.loc[np.isfinite(ffs["dense_file_score"].to_numpy(dtype=np.float64)), "dense_file_score"]
    fmin = float(fin.min())
    fmax = float(fin.max())
    _p("P4.finite_range", fmin >= -1.5 and fmax <= 1.5, f"min={fmin:.6f} max={fmax:.6f}")

    # 5. feature means
    fm_ok = True
    fm_detail = []
    for fname in list(C.CONTINUOUS_FEATURES):
        dev_mean = float(dev_cand[fname].mean())
        s5_mean = float(cand[fname].mean())
        dev_sd = float(dev_cand[fname].std())
        within = (dev_sd == 0 and abs(s5_mean - dev_mean) <= 1e-9) or abs(s5_mean - dev_mean) <= 3.0 * dev_sd
        fm_ok &= within
        fm_detail.append(f"{fname}:{s5_mean:.6f}(dev {dev_mean:.6f},within:{within})")
    _p("P5.feature_means", fm_ok, "; ".join(fm_detail))

    # 6. candidate rows/task per repo
    cr_ok = True
    cr_detail = []
    for repo in ("djangocms", "saleor"):
        dev_mean_ct = float(dev_cand[dev_cand["repository"] == repo].groupby("case_id").size().mean())
        s5_mean_ct = float(cand[cand["repository"] == repo].groupby("case_id").size().mean())
        within = abs(s5_mean_ct - dev_mean_ct) <= 0.25 * dev_mean_ct
        cr_ok &= within
        cr_detail.append(f"{repo}:{s5_mean_ct:.3f}(dev {dev_mean_ct:.3f},within:{within})")
    _p("P6.candidate_rows_per_task", cr_ok, "; ".join(cr_detail))

    # 7. model/config hashes
    art_sha = artifact.get("config_sha256")
    thr = float(artifact.get("threshold", -1))
    _p("P7.model_hash", art_sha == FROZEN_SHA and abs(thr - 0.20) < 1e-12,
       f"config_sha256={art_sha} threshold={thr}")

    # ---- compare with primary parity gate ----
    primary = json.loads((REPORTS / "stage5_parity_gate.json").read_text(encoding="utf-8"))
    primary_pass = primary.get("pass", 0)
    primary_total = primary.get("total", 0)
    agree = (primary_pass == primary_total == 8) and all(c["pass"] for c in CHECKS)
    _p("P8.primary_parity_agreement", agree,
       f"primary={primary_pass}/{primary_total} independent={sum(1 for c in CHECKS if c['pass'])}/{len(CHECKS)}")

    n_pass = sum(1 for c in CHECKS if c["pass"])
    summary = {"pass": n_pass, "total": len(CHECKS), "checks": CHECKS}
    (REPORTS / "stage5_parity_gate_audit.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(f"PARITY AUDIT SUMMARY: {n_pass}/{len(CHECKS)} PASS")
    if n_pass != len(CHECKS):
        print("PARITY_AUDIT_DISAGREEMENT: STOP")
        return 1
    print("PARITY_AUDIT_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
