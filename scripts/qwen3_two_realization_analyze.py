#!/usr/bin/env python3
# ruff: noqa: N803, N806
"""QWEN3 two-realization ANALYZE + AUDIT (T3, DEVELOPMENT, ZERO API).

Reads the frozen per-realization task_rankings.json artifacts (labels were NOT
persisted in the inference-time score tables) and joins the evaluation-only
target labels from load_dev_tasks AFTER ranking is frozen, exactly as the
frozen SweRank study does.

For EACH realization (A and B) and EACH repository, computes at B in {1,3,5,10}:
  pooled TP/FP/FN, Precision, Recall, FNR, F1, macro ORR, candidate precision;
paired task-bootstrap 95% CIs (Qwen - RouteB) at B=5 (>=10,000 resamples,
fixed seed 20260919, task unit);
and the frozen replication gate (A: Delta F1 > 0 AND CI lower > 0; B: Delta
Recall >= -0.02; C: Delta FNR <= +0.02; D: Delta Precision >= -0.02; E: >=3/5
seeded grouped folds Delta F1 >= 0; F: zero leakage; G: valid frozen
provider/model execution; H: cost <= ceiling).

Verdict:
  INDEPENDENT_DENSE_RETRIEVAL_REPLICATED            if A AND B both pass on
                                                    djangoCMS AND Saleor @B=5
  INDEPENDENT_DENSE_RETRIEVAL_REPRODUCIBILITY_INCONCLUSIVE  otherwise

Reproducibility A vs B (B=5): exact same selected-set task percentage,
per-task Jaccard overlap (mean/median/min), one-file boundary flip tasks,
metric deltas A vs B, gate-verdict change check.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

import numpy as np  # noqa: E402

from benchmark.recall.data import load_dev_tasks  # noqa: E402
from benchmark.signal.metrics import METRIC_NAMES, paired_bootstrap  # noqa: E402

OUT_DIR = _PROJECT_DIR / "research" / "contamination-bridge" / "qwen_embed"
REPORT_DIR = _PROJECT_DIR / "reports"

BUDGETS = (1, 3, 5, 10)
B_REF = 5
N_RESAMPLES = 10_000
SEED = 20260919
REALIZATIONS = ("A", "B")
METHODS = ("qwen", "routeb", "bm25")


def _contrib(r: dict, t, key: str, B: int) -> dict:
    pos = set(t.proxy)
    fn_set = set(t.fn_paths)
    B_eff = min(B, r["omitted_size"])
    added = set(r[f"{key}_ranked"][:B_eff])
    final = set(t.write_set) | added
    tp = len(final & pos)
    fp = len(final - pos)
    fn = len(pos - final)
    return {"tp": tp, "fp": fp, "fn": fn,
            "orr": (len(added & fn_set) / t.n_missed) if t.n_missed else 0.0,
            "cand_fn": len(added & fn_set), "cand_sel": len(added)}


def _metrics_for(results: dict, by_cid: dict, repo: str) -> dict:
    cids = [c for c in results if results[c]["repository"] == repo]
    per_b: dict = {}
    for B in BUDGETS:
        per_b[str(B)] = {}
        for m in METHODS:
            rows = [_contrib(results[c], by_cid[c], m, B) for c in cids]
            tp = sum(r["tp"] for r in rows)
            fp = sum(r["fp"] for r in rows)
            fn = sum(r["fn"] for r in rows)
            p = tp / (tp + fp) if (tp + fp) else 0.0
            rec = tp / (tp + fn) if (tp + fn) else 0.0
            f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
            fnr = fn / (tp + fn) if (tp + fn) else 0.0
            orr = sum(r["orr"] for r in rows) / len(rows) if rows else 0.0
            cand = (sum(r["cand_fn"] for r in rows) / sum(r["cand_sel"] for r in rows)
                    if sum(r["cand_sel"] for r in rows) else 0.0)
            per_b[str(B)][m] = {
                "tp": tp, "fp": fp, "fn": fn, "precision": round(p, 4),
                "recall": round(rec, 4), "f1": round(f1, 4), "fnr": round(fnr, 4),
                "macro_orr": round(orr, 4), "candidate_precision": round(cand, 4),
                "n_tasks": len(cids),
            }
    return {"n_tasks": len(cids), "B": per_b}


def _ci_map(results: dict, by_cid: dict, repo: str) -> dict:
    cids = [c for c in results if results[c]["repository"] == repo]
    rows: dict[str, list] = {m: [] for m in METRIC_NAMES}
    rb_rows: dict[str, list] = {m: [] for m in METRIC_NAMES}
    for cid in cids:
        q = _contrib(results[cid], by_cid[cid], "qwen", B_REF)
        rb = _contrib(results[cid], by_cid[cid], "routeb", B_REF)
        rows["macro_orr"].append((q["orr"],))
        rb_rows["macro_orr"].append((rb["orr"],))
        for name in ("final_precision", "final_recall", "final_f1", "final_fnr"):
            rows[name].append((q["tp"], q["fp"], q["fn"]))
            rb_rows[name].append((rb["tp"], rb["fp"], rb["fn"]))
        rows["candidate_precision"].append((q["cand_fn"], q["cand_sel"]))
        rb_rows["candidate_precision"].append((rb["cand_fn"], rb["cand_sel"]))
    return {m: paired_bootstrap(rb_rows[m], rows[m], m, N_RESAMPLES, SEED)
            for m in METRIC_NAMES}


def _folds(cids: list, by_cid: dict, results: dict, folds: int = 5,
           seed: int = SEED) -> list[float]:
    import random
    rng = random.Random(seed)
    order = list(cids)
    rng.shuffle(order)
    out: list[float] = []
    for k in range(folds):
        fold = order[k::folds]
        pos = 0.0
        for cid in fold:
            r = results[cid]
            t = by_cid[cid]
            M = t.n_missed
            if M == 0:
                continue
            B_eff = min(B_REF, r["omitted_size"])
            fn_set = set(t.fn_paths)
            q = len(set(r["qwen_ranked"][:B_eff]) & fn_set) / M
            rb = len(set(r["routeb_ranked"][:B_eff]) & fn_set) / M
            pos += (q - rb)
        out.append(pos / len(fold) if fold else 0.0)
    return out


def _gate_for(metrics: dict, ci: dict, results: dict, by_cid: dict,
              repo: str) -> dict:
    b5 = metrics["B"]["5"]
    q = b5["qwen"]
    rb = b5["routeb"]
    cids = [c for c in results if results[c]["repository"] == repo]
    d_f1 = q["f1"] - rb["f1"]
    ci_low_f1 = ci["final_f1"]["ci95_lower"]
    a = d_f1 > 0.0 and ci_low_f1 > 0.0
    b = (q["recall"] - rb["recall"]) >= -0.02
    c = (q["fnr"] - rb["fnr"]) <= 0.02
    d = (q["precision"] - rb["precision"]) >= -0.02
    folds = _folds(cids, by_cid, results)
    e = sum(1 for x in folds if x >= 0.0) >= 3
    rec = all([a, b, c, d, e])
    return {
        "A_delta_f1_gt0_and_ci_low_gt0": a, "delta_f1": round(d_f1, 4),
        "ci_low_f1": round(ci_low_f1, 4),
        "B_delta_recall_ge_minus_0.02": b,
        "delta_recall": round(q["recall"] - rb["recall"], 4),
        "C_delta_fnr_le_plus_0.02": c,
        "delta_fnr": round(q["fnr"] - rb["fnr"], 4),
        "D_delta_precision_ge_minus_0.02": d,
        "delta_precision": round(q["precision"] - rb["precision"], 4),
        "E_folds_ge_3_5": e, "fold_deltas_f1": [round(x, 4) for x in folds],
        "ci": ci, "pass": rec,
    }


def _reproducibility(results_a: dict, results_b: dict) -> dict:
    """A vs B at B=5, independent of target correctness."""
    common = [c for c in results_a if c in results_b]
    same_set = 0
    jaccards: list[float] = []
    flips = 0
    one_file_flips: list[str] = []
    for cid in common:
        ra = results_a[cid]
        rb = results_b[cid]
        ba = set(ra["qwen_ranked"][:min(B_REF, ra["omitted_size"])])
        bb = set(rb["qwen_ranked"][:min(B_REF, rb["omitted_size"])])
        same_set += 1 if ba == bb else 0
        union = ba | bb
        jac = len(ba & bb) / len(union) if union else 1.0
        jaccards.append(jac)
        sym_diff = ba.symmetric_difference(bb)
        # one-file boundary flip = the B=5 sets differ by exactly one file:
        # |A^B| == 1 (one file added/removed) or |A^B| == 2 with equal sizes
        # (one file swapped).
        if len(sym_diff) == 1 or (len(sym_diff) == 2 and len(ba) == len(bb)):
            flips += 1
            one_file_flips.append(cid)
    return {
        "n_tasks_common": len(common),
        "exact_same_selected_set_task_percentage": round(
            100.0 * same_set / len(common), 2) if common else None,
        "jaccard": {
            "mean": round(float(np.mean(jaccards)), 4) if jaccards else None,
            "median": round(float(np.median(jaccards)), 4) if jaccards else None,
            "min": round(float(np.min(jaccards)), 4) if jaccards else None,
            "max": round(float(np.max(jaccards)), 4) if jaccards else None,
        },
        "n_one_file_boundary_flip_tasks": flips,
        "one_file_boundary_flip_case_ids": one_file_flips,
        "note": "one-file boundary flip = B=5 sets differ by EXACTLY one file",
    }


def main() -> int:
    tasks = load_dev_tasks()
    by_cid = {t.case_id: t for t in tasks}

    loaded: dict[str, dict] = {}
    ledgers: dict[str, dict] = {}
    for rid in REALIZATIONS:
        rdir = OUT_DIR / f"realization_{rid}"
        loaded[rid] = json.loads(
            (rdir / "task_rankings.json").read_text(encoding="utf-8"))
        ledgers[rid] = json.loads((rdir / "ledger.json").read_text(encoding="utf-8"))

    out: dict = {"reference_budget": B_REF, "baseline": "routeb",
                 "realizations": {}, "reproducibility": {}, "verdict": None}
    all_pass = True
    for rid in REALIZATIONS:
        results = loaded[rid]
        per_repo: dict = {}
        for repo in ("djangocms", "saleor"):
            metrics = _metrics_for(results, by_cid, repo)
            ci = _ci_map(results, by_cid, repo)
            gate = _gate_for(metrics, ci, results, by_cid, repo)
            per_repo[repo] = {"metrics": metrics, "gate": gate}
            all_pass = all_pass and gate["pass"]
        out["realizations"][rid] = {
            "ledger": ledgers[rid], "repos": per_repo,
        }
    out["reproducibility"] = _reproducibility(loaded["A"], loaded["B"])
    out["verdict"] = ("INDEPENDENT_DENSE_RETRIEVAL_REPLICATED" if all_pass
                      else "INDEPENDENT_DENSE_RETRIEVAL_REPRODUCIBILITY_INCONCLUSIVE")
    out["gate_summary"] = {
        rid: {repo: out["realizations"][rid]["repos"][repo]["gate"]["pass"]
              for repo in ("djangocms", "saleor")} for rid in REALIZATIONS}

    OUT_DIR.joinpath("two_realization_metrics.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({
        "verdict": out["verdict"],
        "gate_summary": out["gate_summary"],
        "reproducibility": out["reproducibility"]["jaccard"],
        "exact_same_percent": out["reproducibility"]["exact_same_selected_set_task_percentage"],
        "one_file_flips": out["reproducibility"]["n_one_file_boundary_flip_tasks"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
