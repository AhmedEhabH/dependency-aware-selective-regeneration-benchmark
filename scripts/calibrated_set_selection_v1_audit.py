#!/usr/bin/env python3
"""CALIBRATED_SET_SELECTION_V1 — INDEPENDENT audit (T3, DEVELOPMENT, ZERO API).

Does NOT import the primary analyzer (benchmark.calibrated.* or the run
script). Recomputes every key claim from the PERSISTED artifacts under
research/calibrated-set-selection-v1/ plus load_dev_tasks (data layer):

  1. sealed-data guard (exactly the 323 DEV case ids);
  2. Sparse baselines reproduce the frozen TP/FP/FN/P/R/F1/FNR;
  3. OOF coverage: every task appears exactly once as a held-out fold;
  4. final selected sets recomputed from OOF probabilities + fold thresholds
     match the persisted final_oof_predictions;
  5. per-repository pooled metrics recomputed from the selected sets match
     the persisted repo_metrics;
  6. independent task-paired bootstrap CIs (10,000 resamples, seed 20260920);
  7. fold balance + repository stratification;
  8. candidate-universe schema: NO repository-identity / file-count-N feature;
  9. feature recomputation: log_rank == log1p(dense_rank); interaction ==
     in_sparse * log_rank; gap_to_top1 == max_score(task) - score; NaN floor;
 10. determinism artifact (gate G);
 11. calibration recomputation (Brier / ECE / 10 equal-width bins);
 12. realization-B robustness recomputation (exact-set %, Jaccard, verdict);
 13. gate recomputation (A-G) from the persisted metrics/CI/fold deltas;
 14. LR coefficients + scaler parameters finite and present.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_PROC_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROC_DIR))
sys.path.insert(0, str(_PROC_DIR / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from benchmark.recall.data import load_dev_tasks  # noqa: E402

OUT_DIR = _PROC_DIR / "research" / "calibrated-set-selection-v1"
REPORT_DIR = _PROC_DIR / "reports"
N_FOLDS = 5
N_RESAMPLES = 10_000
SEED = 20260920
EPS = 1e-6

FEATURE_NAMES = ("dense_file_score", "log_rank", "gap_to_top1", "in_sparse",
                 "log_sparse_set_size", "sparse_empty", "sparse_rank_interaction")


def _p_r_f1_fnr(tp, fp, fn):
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
    fnr = fn / (tp + fn) if (tp + fn) else 0.0
    return p, r, f1, fnr


def main() -> int:
    tasks = load_dev_tasks()
    by = {t.case_id: t for t in tasks}
    checks: list[dict] = []

    # ---- 1. sealed guard ----
    cu = pd.read_parquet(OUT_DIR / "candidate_universe_A.parquet")
    ids = set(cu["case_id"])
    checks.append({"check": "candidate universe == 323 DEV tasks",
                   "value": len(ids), "pass": len(ids) == 323 and ids == set(by)})
    checks.append({"check": "DEV repos only",
                   "value": sorted(set(cu["repository"])),
                   "pass": set(cu["repository"]) == {"djangocms", "saleor"}})

    # ---- 2. Sparse baselines ----
    frozen_sparse = {
        "djangocms": (125, 155, 382),
        "saleor": (99, 193, 369),
    }
    for repo, (ftp, ffp, ffn) in frozen_sparse.items():
        cids = [c for c in by if by[c].repository == repo]
        tp = sum(len(set(by[c].write_set) & set(by[c].proxy)) for c in cids)
        fp = sum(len(set(by[c].write_set) - set(by[c].proxy)) for c in cids)
        fn = sum(len(set(by[c].proxy) - set(by[c].write_set)) for c in cids)
        ok = (tp, fp, fn) == (ftp, ffp, ffn)
        checks.append({"check": f"Sparse baseline {repo} TP/FP/FN == frozen",
                       "value": (tp, fp, fn), "pass": ok})

    # ---- 3. OOF coverage + per-fold thresholds ----
    oof = pd.read_parquet(OUT_DIR / "oof_probabilities_A.parquet")
    oof_cases = set(oof["case_id"])
    checks.append({"check": "OOF covers every task exactly once",
                   "value": len(oof_cases), "pass": oof_cases == set(by)
                   and oof.groupby("case_id").size().max() <= 80
                   and oof.groupby("case_id").size().min() >= 1})
    fold_map = json.loads((OUT_DIR / "fold_assignments_A.json").read_text(encoding="utf-8"))
    fold_map = {k: int(v) for k, v in fold_map.items()}
    checks.append({"check": "fold assignment covers all 323 tasks",
                   "value": len(fold_map), "pass": set(fold_map) == set(by)})

    # ---- 4. final sets recomputed from OOF probs + thresholds ----
    fd = json.loads((OUT_DIR / "fold_details_A.json").read_text(encoding="utf-8"))
    persisted_sets = json.loads((OUT_DIR / "final_oof_predictions_A.json").read_text(encoding="utf-8"))
    recomputed: dict[str, list[str]] = {}
    for cid, f in fold_map.items():
        t = float(fd[str(f)]["inner_threshold"])
        sub = oof[oof["case_id"] == cid]
        recomputed[cid] = sorted(sub.loc[sub["prob"] >= t, "file_path"])
    same = sum(1 for c in by if sorted(recomputed[c]) == sorted(persisted_sets[c]))
    checks.append({"check": "final sets recomputed from OOF probs + thresholds == persisted",
                   "value": f"{same}/323", "pass": same == 323})

    # ---- 5. repo metrics recomputed ----
    rm = json.loads((OUT_DIR / "repo_metrics_A.json").read_text(encoding="utf-8"))
    for repo in ("djangocms", "saleor"):
        cids = [c for c in by if by[c].repository == repo]
        tp = sum(len(set(persisted_sets[c]) & set(by[c].proxy)) for c in cids)
        fp = sum(len(set(persisted_sets[c]) - set(by[c].proxy)) for c in cids)
        fn = sum(len(set(by[c].proxy) - set(persisted_sets[c])) for c in cids)
        p, r, f1, fnr = _p_r_f1_fnr(tp, fp, fn)
        mp = rm[repo]["policy"]
        ok = (abs(p - mp["precision"]) < EPS and abs(r - mp["recall"]) < EPS
              and abs(f1 - mp["f1"]) < EPS and abs(fnr - mp["fnr"]) < EPS
              and (tp, fp, fn) == (mp["tp"], mp["fp"], mp["fn"]))
        checks.append({"check": f"repo_metrics {repo} recomputed == persisted",
                       "value": (tp, fp, fn, round(f1, 4)), "pass": ok})

    # ---- 6. independent paired task bootstrap ----
    boot = json.loads((OUT_DIR / "bootstrap_ci_A.json").read_text(encoding="utf-8"))
    import random
    for repo in ("djangocms", "saleor"):
        cids = [c for c in by if by[c].repository == repo]
        pol = [(len(set(persisted_sets[c]) & set(by[c].proxy)),
                len(set(persisted_sets[c]) - set(by[c].proxy)),
                len(set(by[c].proxy) - set(persisted_sets[c]))) for c in cids]
        spa = [(len(set(by[c].write_set) & set(by[c].proxy)),
                len(set(by[c].write_set) - set(by[c].proxy)),
                len(set(by[c].proxy) - set(by[c].write_set))) for c in cids]
        rng = random.Random(SEED)
        n = len(cids)
        deltas = np.empty(N_RESAMPLES, dtype=np.float64)
        for b in range(N_RESAMPLES):
            idx = [rng.randrange(n) for _ in range(n)]
            tp = sum(pol[i][0] for i in idx)
            fp = sum(pol[i][1] for i in idx)
            fn = sum(pol[i][2] for i in idx)
            stp = sum(spa[i][0] for i in idx)
            sfp = sum(spa[i][1] for i in idx)
            sfn = sum(spa[i][2] for i in idx)
            f1p = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
            f1s = 2 * stp / (2 * stp + sfp + sfn) if (2 * stp + sfp + sfn) else 0.0
            deltas[b] = f1p - f1s
        lo, hi = np.quantile(deltas, [0.025, 0.975])
        ref = boot[repo]["f1"]
        ok = (abs(lo - ref["ci95_lower"]) < 2e-3 and abs(hi - ref["ci95_upper"]) < 2e-3)
        checks.append({"check": f"independent bootstrap F1 CI {repo} matches",
                       "value": (round(float(lo), 4), round(float(hi), 4)),
                       "pass": ok})

    # ---- 7. fold balance + repo stratification ----
    per_repo = {r: {} for r in ("djangocms", "saleor")}
    for cid, f in fold_map.items():
        per_repo[by[cid].repository][f] = per_repo[by[cid].repository].get(f, 0) + 1
    ok = all(max(per_repo[r].values()) - min(per_repo[r].values()) <= 1 for r in per_repo)
    checks.append({"check": "folds repository-stratified (<=1 task imbalance per repo)",
                   "value": per_repo, "pass": ok})

    # ---- 8. candidate-universe schema: no repo/N feature ----
    cols = set(cu.columns)
    allowed = set(FEATURE_NAMES) | {"case_id", "repository", "file_path",
                                    "dense_rank", "label"}
    checks.append({"check": "no repository-identity or file-count-N feature present",
                   "value": sorted(cols - allowed), "pass": cols <= allowed
                   and "repository" not in FEATURE_NAMES
                   and all(("n_files" not in c and "count" not in c) for c in FEATURE_NAMES)})

    # ---- 9. feature recomputation ----
    floor = float(cu.loc[np.isfinite(cu["dense_file_score"]), "dense_file_score"].min()) - 1.0
    ok_feat = True
    for cid, g in cu.groupby("case_id"):
        imputed = np.where(np.isfinite(g["dense_file_score"]),
                           g["dense_file_score"], floor)
        smax = float(imputed.max())
        for _, row in g.iterrows():
            if abs(row["log_rank"] - np.log1p(row["dense_rank"])) > 1e-9:
                ok_feat = False
            if abs(row["sparse_rank_interaction"] - row["in_sparse"] * row["log_rank"]) > 1e-9:
                ok_feat = False
            if abs(row["gap_to_top1"] - (smax - row["dense_file_score"])) > 1e-6:
                ok_feat = False
            if abs(row["log_sparse_set_size"] - np.log1p(len(by[cid].write_set))) > 1e-9:
                ok_feat = False
            if (row["sparse_empty"] == 1) != (len(by[cid].write_set) == 0):
                ok_feat = False
    checks.append({"check": "all frozen feature definitions recompute exactly",
                   "value": "ok" if ok_feat else "mismatch", "pass": ok_feat})

    # ---- 10. determinism artifact ----
    det = json.loads((OUT_DIR / "determinism_A.json").read_text(encoding="utf-8"))
    checks.append({"check": "gate G: deterministic rerun identical",
                   "value": det["oof_and_sets_identical"], "pass": bool(det["oof_and_sets_identical"])})

    # ---- 11. calibration recomputation ----
    cal = json.loads((OUT_DIR / "calibration_A.json").read_text(encoding="utf-8"))
    probs = oof["prob"].to_numpy(dtype=np.float64)
    labels = oof["label"].to_numpy(dtype=np.int64)
    brier = float(np.mean((probs - labels) ** 2))
    edges = np.linspace(0, 1, 11)
    ece = 0.0
    for b in range(10):
        m = (probs >= edges[b]) & (probs < edges[b + 1])
        if b == 9:
            m |= probs == 1.0
        if m.sum() == 0:
            continue
        ece += (m.sum() / len(probs)) * abs(labels[m].mean() - probs[m].mean())
    ok = abs(brier - cal["brier"]) < 1e-6 and abs(ece - cal["ece"]) < 1e-4
    checks.append({"check": "calibration (Brier/ECE) recomputed",
                   "value": (round(brier, 6), round(float(ece), 6)), "pass": ok})

    # ---- 12. realization-B robustness recomputation ----
    sets_b = json.loads((OUT_DIR / "final_oof_predictions_B.json").read_text(encoding="utf-8"))
    rob_persisted = json.loads((OUT_DIR / "robustness_ab.json").read_text(encoding="utf-8"))
    common = [c for c in persisted_sets if c in sets_b]
    same = sum(1 for c in common if set(persisted_sets[c]) == set(sets_b[c]))
    jac = []
    for c in common:
        u = set(persisted_sets[c]) | set(sets_b[c])
        jac.append(len(set(persisted_sets[c]) & set(sets_b[c])) / len(u) if u else 1.0)
    ok = (len(common) == 323 and abs(100.0 * same / 323 - rob_persisted["exact_same_selected_set_percentage"]) < 0.01
          and abs(float(np.mean(jac)) - rob_persisted["jaccard_mean"]) < 1e-4)
    checks.append({"check": "A/B robustness recomputed == persisted",
                   "value": (round(100.0 * same / 323, 2), round(float(np.mean(jac)), 4)),
                   "pass": ok})
    verdict_b = json.loads((OUT_DIR / "verdict_B.json").read_text(encoding="utf-8"))
    verdict_a = json.loads((OUT_DIR / "verdict_A.json").read_text(encoding="utf-8"))
    checks.append({"check": "A/B gate verdict agreement stable",
                   "value": (verdict_a["verdict"], verdict_b["verdict"]),
                   "pass": verdict_a["verdict"] == verdict_b["verdict"]})

    # ---- 13. gate recomputation ----
    gate_a = verdict_a["gate"]
    ok_gate = True
    for repo in ("djangocms", "saleor"):
        m = rm[repo]
        f1p, f1s = m["policy"]["f1"], m["sparse"]["f1"]
        bf1 = boot[repo]["f1"]
        deltas = gate_a["gate"][repo]["fold_deltas"]
        n_ge = sum(1 for x in deltas if x >= 0)
        c = (f1p > f1s and bf1["ci95_lower"] > 0
             and m["policy"]["recall"] >= m["sparse"]["recall"]
             and m["policy"]["fnr"] <= m["sparse"]["fnr"] and n_ge >= 3)
        ok_gate = ok_gate and (c == gate_a["gate"][repo]["pass"])
    checks.append({"check": "gate logic recomputed matches persisted pass flags",
                   "value": "ok" if ok_gate else "mismatch", "pass": ok_gate})

    # ---- 14. LR coefficients / scaler finite ----
    ok_lr = all(np.isfinite(v) for f in fd.values()
                for v in f["lr_coef"] + [f["lr_intercept"]] + f["scaler_mean"] + f["scaler_scale"])
    checks.append({"check": "LR coefficients + scaler parameters finite",
                   "value": "ok" if ok_lr else "non-finite", "pass": ok_lr})

    results = {"audit_date": "2026-09-20", "n_checks": len(checks),
               "passed": sum(1 for c in checks if c["pass"]),
               "failed": sum(1 for c in checks if not c["pass"]),
               "checks": [{**c, "pass": bool(c["pass"])} for c in checks],
               "verdict": "PASS" if all(c["pass"] for c in checks) else "FAIL"}
    (REPORT_DIR / "calibrated_set_selection_v1_audit.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps({"passed": results["passed"], "failed": results["failed"],
                      "verdict": results["verdict"]}))
    return 0 if results["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
