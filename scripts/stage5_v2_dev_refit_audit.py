#!/usr/bin/env python3
"""STAGE5_V2_FINAL - INDEPENDENT AUDIT of the DEV refit config (T3, ZERO API).

Recomputes the final deployment V2 configuration from PERSISTED artifacts
WITHOUT importing scripts.stage5_v2_deployment_refit (the primary analyzer).
Uses benchmark.calibrated.policy + memory_rescue.candidates directly (these are
the frozen shared library, not the analyzer driver).

Checks:
  A1 DEV task count == 323;
  A2 candidate rows == preregistered count; feature schema == 11;
  A3 threshold recompute from 5-fold OOF (argmax micro-F1, tie HIGHER) matches;
  A4 coefficients/intercept/scaler recompute on all 323 rows matches artifact;
  A5 preregistration hash recomputation matches;
  A6 no sealed roles in the DEV-refit population (all DEV);
  A7 qwen model/provider are the frozen constants;
  A8 endpoint/success-rule frozen fields are as preregistered.
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

from benchmark.calibrated.folds import grouped_stratified_folds  # noqa: E402
from benchmark.calibrated.policy import fit_policy, predict_proba, select_threshold  # noqa: E402
from benchmark.memory_rescue import candidates as C  # noqa: E402, N812
from benchmark.recall.data import load_dev_tasks  # noqa: E402
from benchmark.signal.or_embeddings import (  # noqa: E402
    OPENROUTER_EMBED_MODEL,
    OPENROUTER_EMBED_PROVIDER,
)

OUT = _PROJECT_DIR / "research" / "stage5-v2-final"
REPORTS = _PROJECT_DIR / "reports"

CHECKS: list[dict] = []


def _p(name: str, ok: bool, detail: str) -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    CHECKS.append({"name": name, "pass": bool(ok), "detail": detail})


def main() -> int:
    art = json.loads((OUT / "deployment_artifact.json").read_text(encoding="utf-8"))
    pre = json.loads((REPORTS / "stage5_final_preregistration.json").read_text(encoding="utf-8"))
    frame = pd.read_parquet(OUT / "deployment_candidate_rows.parquet")
    tasks = load_dev_tasks()

    _p("A1.dev_tasks", len(tasks) == 323, f"n={len(tasks)}")
    _p("A2.candidate_rows", len(frame) == art["n_candidate_rows"] == 10734,
       f"rows={len(frame)}")
    _p("A2.feature_schema", art["feature_names"] == list(C.FEATURE_NAMES) and len(C.FEATURE_NAMES) == 11,
       "11 features exact order")

    # A3 threshold recompute
    repo_of = {cid: str(frame.loc[frame["case_id"] == cid, "repository"].iloc[0])
               for cid in sorted(set(frame["case_id"]))}
    case_ids = sorted(set(frame["case_id"]))
    fold_map = grouped_stratified_folds(case_ids, lambda c: repo_of[c], k=5, seed=20260920)
    probs, labels = [], []
    for fold in range(5):
        tr = frame[frame["case_id"].isin([c for c in case_ids if fold_map[c] != fold])]
        te = frame[frame["case_id"].isin([c for c in case_ids if fold_map[c] == fold])]
        sc, m = fit_policy(C.feature_matrix(tr), C.label_vector(tr),
                           continuous_cols=C.CONTINUOUS_FEATURES,
                           boolean_cols=C.BOOLEAN_FEATURES, feature_names=C.FEATURE_NAMES)
        probs.append(predict_proba(sc, m, C.feature_matrix(te),
                                   continuous_cols=C.CONTINUOUS_FEATURES,
                                   boolean_cols=C.BOOLEAN_FEATURES, feature_names=C.FEATURE_NAMES))
        labels.append(C.label_vector(te))
    t = select_threshold(np.concatenate(probs), np.concatenate(labels))
    _p("A3.threshold", abs(t - art["threshold"]) < 1e-12, f"threshold={t}")

    # A4 model recompute on all rows
    sc, m = fit_policy(C.feature_matrix(frame), C.label_vector(frame),
                       continuous_cols=C.CONTINUOUS_FEATURES,
                       boolean_cols=C.BOOLEAN_FEATURES, feature_names=C.FEATURE_NAMES)
    ok_coef = np.allclose([float(x) for x in m.coef_.ravel()], art["lr_coef"], atol=1e-8)
    ok_int = abs(float(m.intercept_[0]) - art["lr_intercept"]) < 1e-8
    ok_sc = (np.allclose(sc.mean_, art["scaler_mean"], atol=1e-8)
             and np.allclose(sc.scale_, art["scaler_scale"], atol=1e-8))
    _p("A4.model_recompute", ok_coef and ok_int and ok_sc, "coef/intercept/scaler match")

    # A5 prereg hash
    body = {k: v for k, v in pre.items() if k != "preregistration_sha256"}
    d = hashlib.sha256(json.dumps(body, indent=1, sort_keys=True).encode()).hexdigest()
    _p("A5.prereg_hash", d == pre["preregistration_sha256"], f"hash={d[:16]}")

    # A6 no sealed roles
    roles = {t.case_id: t.role for t in tasks}
    sealed = [c for c, r in roles.items() if r in ("RESERVE", "INTERNAL_TEST", "HELD_OUT_TEST")]
    _p("A6.no_sealed_in_dev", len(sealed) == 0, f"sealed_in_dev={len(sealed)}")

    _p("A7.qwen_constants", OPENROUTER_EMBED_MODEL == "qwen/qwen3-embedding-8b"
       and OPENROUTER_EMBED_PROVIDER == "DeepInfra",
       f"{OPENROUTER_EMBED_MODEL} @ {OPENROUTER_EMBED_PROVIDER}")

    _p("A8.endpoint_frozen",
       pre["primary_endpoint"]["resamples"] == 10000
       and pre["primary_endpoint"]["seed"] == 20260920
       and pre["success_rule"]["per_repo_ci_gating"] is False,
       "resamples/seed/success-rule match preregistration")

    n_pass = sum(1 for c in CHECKS if c["pass"])
    print(f"AUDIT SUMMARY: {n_pass}/{len(CHECKS)} PASS")
    (REPORTS / "stage5_dev_refit_audit.json").write_text(
        json.dumps({"pass": n_pass, "total": len(CHECKS), "checks": CHECKS}, indent=1),
        encoding="utf-8")
    return 0 if n_pass == len(CHECKS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
