#!/usr/bin/env python3
# ruff: noqa: E501, N806, N812
"""SALEOR_RESERVE_300_RMCSS - INDEPENDENT LABEL-FREE PARITY AUDIT (§17).

Independently recomputes every label-free parity quantity WITHOUT importing the
primary parity gate (scripts.saleor_reserve_300_parity_gate) or the primary
evaluator. Re-reads raw artifacts only.

Recomputes: cache coverage; sentinel count; NaN rate; dense min/max; feature
means; candidate counts; schema; artifact hashes; sample hash. Then compares
with the primary parity gate's recorded results; they must agree.

Output: reports/saleor_reserve_300_parity_gate_audit.json
"""
from __future__ import annotations

import hashlib
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

    # 1 cache coverage
    dev_blob = json.loads(BLOB_CACHE.read_text(encoding="utf-8"))
    corr_blob = json.loads((CORRECTED_WORK / "missing_blob_texts.json").read_text(encoding="utf-8")) if (CORRECTED_WORK / "missing_blob_texts.json").exists() else {}
    res_blob = json.loads((RESERVE_WORK / "missing_blob_texts.json").read_text(encoding="utf-8")) if (RESERVE_WORK / "missing_blob_texts.json").exists() else {}
    blob_texts = {**dev_blob, **corr_blob, **res_blob}
    dev_idx = set(json.loads(DEV_CACHE_IDX.read_text(encoding="utf-8")))
    corr_idx = set(json.loads(CORR_CACHE_IDX.read_text(encoding="utf-8"))) if CORR_CACHE_IDX.exists() else set()
    res_idx = set(json.loads(RES_CACHE_IDX.read_text(encoding="utf-8"))) if RES_CACHE_IDX.exists() else set()
    covered = dev_idx | corr_idx | res_idx
    n_miss = 0
    for cid in selected:
        uni = json.loads((SC_DATASET / "scientific" / cid / "public" / "candidate_universe.json").read_text(encoding="utf-8"))
        for r in uni["records"]:
            text = blob_texts.get(r["sha256"])
            if text is None:
                continue
            units = [u for u in extract_code_units(text) if u.strip()]
            if units and any(sha256_text(u) not in covered for u in units):
                n_miss += 1
    _p("A1.cache_coverage", n_miss == 0, f"unresolved_misses={n_miss}")

    # 2 sentinel count
    n_sent = int((ffs["dense_file_score"] == -1e9).sum())
    _p("A2.sentinel_count", n_sent == 0, f"==-1e9:{n_sent}")

    # 3 NaN rate
    dev_rate = float(devA.loc[devA["repository"] == "saleor", "dense_file_score"].isna().mean())
    s5_rate = float(ffs["dense_file_score"].isna().mean())
    _p("A3.nan_rate", abs(s5_rate - dev_rate) <= 0.03, f"dev={dev_rate:.4f} s5={s5_rate:.4f}")

    # 4 finite range
    fin = ffs.loc[np.isfinite(ffs["dense_file_score"].to_numpy(dtype=np.float64)), "dense_file_score"]
    _p("A4.finite_range", float(fin.min()) >= -1.5 and float(fin.max()) <= 1.5,
       f"min={float(fin.min()):.6f} max={float(fin.max()):.6f}")

    # 5 feature means within 3 SD
    dev_sc = dev_cand[dev_cand["repository"] == "saleor"]
    ok5 = True
    for f in list(C.CONTINUOUS_FEATURES):
        dm = float(dev_sc[f].mean())
        ds = float(dev_sc[f].std())
        sm = float(cand[f].mean())
        ok5 &= (abs(sm - dm) <= 3.0 * ds) if ds > 0 else (abs(sm - dm) <= 1e-9)
    _p("A5.feature_means", ok5, "all 9 continuous features within 3 Saleor DEV SD")

    # 6 candidate rows/task
    dev_ct = float(dev_sc.groupby("case_id").size().mean())
    s5_ct = float(cand.groupby("case_id").size().mean())
    _p("A6.candidate_rows_per_task", abs(s5_ct - dev_ct) <= 0.25 * dev_ct,
       f"dev={dev_ct:.3f} s5={s5_ct:.3f}")

    # 7 schema
    _p("A7.schema", list(cand.columns) == list(dev_cand.columns)
       and list(C.FEATURE_NAMES) == primary["feature_names"], "11-feature schema exact")

    # 8 primary hashes
    _p("A8.primary_hashes", primary.get("config_sha256") == FROZEN_SHA
       and abs(float(primary["threshold"]) - 0.20) < 1e-12,
       f"config_sha256={primary.get('config_sha256')} threshold={primary.get('threshold')}")

    # 9 transfer hashes
    _p("A9.transfer_hashes", transfer.get("artifact_sha256") == TRANSFER_SHA
       and abs(float(transfer["threshold"]) - 0.20) < 1e-12,
       f"artifact_sha256={transfer.get('artifact_sha256')} threshold={transfer.get('threshold')}")

    # 10 sample hash
    ids_text = "\n".join(selected) + "\n"
    sha = hashlib.sha256(ids_text.encode("utf-8")).hexdigest()
    _p("A10.sample_hash", sha == SAMPLE_SHA and len(selected) == 300, f"sha={sha}")

    # agreement with primary gate
    gate = json.loads((REPORTS / "saleor_reserve_300_parity_gate.json").read_text(encoding="utf-8"))
    agree = gate.get("pass", 0) == gate.get("total", 0) == 10 and all(c["pass"] for c in CHECKS)
    _p("A11.primary_agreement", agree,
       f"primary={gate.get('pass')}/{gate.get('total')} independent={sum(1 for c in CHECKS if c['pass'])}/{len(CHECKS)}")

    n_pass = sum(1 for c in CHECKS if c["pass"])
    summary = {"pass": n_pass, "total": len(CHECKS), "checks": CHECKS}
    (REPORTS / "saleor_reserve_300_parity_gate_audit.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(f"PARITY AUDIT SUMMARY: {n_pass}/{len(CHECKS)} PASS", flush=True)
    if n_pass != len(CHECKS):
        print("PARITY_AUDIT_DISAGREEMENT: STOP")
        return 1
    print("PARITY_AUDIT_PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
