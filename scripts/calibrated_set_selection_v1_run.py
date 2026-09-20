#!/usr/bin/env python3
# ruff: noqa: N803, N812
"""CALIBRATED_SET_SELECTION_V1 — primary analyzer (T3, DEVELOPMENT, ZERO API).

Mission: CALIBRATED_SET_SELECTION_V1 (DEV-ONLY FINAL FILE-SET POLICY).

Primary score realization: Qwen realization A (generated chronologically first;
the choice is independent of downstream calibrated-policy performance).
Realization B is used ONLY for the frozen realization-B robustness rerun.

Pipeline (frozen in docs/CALIBRATED_SET_SELECTION_V1_IMPACT_DECLARATION_2026-09-20.md):
  1. build the frozen candidate universe (Sparse KEEP/DROP files UNION the
     top-20 NON-SPARSE files by frozen Qwen dense rank);
  2. construct the 7 frozen features per candidate file (labels joined for
     evaluation only);
  3. deterministic 5-fold OUTER task-grouped, repository-stratified CV;
     per fold: scaler + L2-LR fit on outer-training tasks ONLY; INNER 5-fold
     task-grouped OOF threshold selection (argmax pooled micro-F1 over
     0.01..0.99, tie-break HIGHER); frozen threshold applied to outer held-out
     probabilities; final set = {candidate : prob >= threshold};
  4. pooled per-repository TP/FP/FN/P/R/F1/FNR; paired task bootstrap CIs
     (10,000 resamples, seed 20260920); calibration diagnostics (10 equal-width
     bins); error decomposition; set-size analysis; the frozen primary gate.

ZERO sealed data. NO Stage-5 execution. NO paid API calls. Deterministic.

Run:
  python scripts/calibrated_set_selection_v1_run.py                 # realization A (primary)
  python scripts/calibrated_set_selection_v1_run.py --realization B # robustness rerun
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from benchmark.calibrated import analysis as A  # noqa: E402
from benchmark.calibrated import features as F  # noqa: E402
from benchmark.calibrated import folds as Fd  # noqa: E402
from benchmark.recall.data import load_dev_tasks  # noqa: E402

OUT_DIR = _PROJECT_DIR / "research" / "calibrated-set-selection-v1"
QWEN_DIR = _PROJECT_DIR / "research" / "contamination-bridge" / "qwen_embed"
SWERANK_RANKINGS = _PROJECT_DIR / "research" / "strong-localization-signal" / "swerank" / "task_rankings.json"

SEALED_PREFIXES = ()
DEV_REPOS = ("djangocms", "saleor")
FOLD_SEED = 20260920
N_FOLDS = 5


def _load_run(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sealed_guard(tasks) -> None:
    """Fail-closed: only the 323 DEV case IDs are allowed (no sealed split)."""
    ids = [t.case_id for t in tasks]
    if len(ids) != 323:
        raise RuntimeError(f"expected 323 DEV tasks, got {len(ids)}")
    if len(set(ids)) != 323:
        raise RuntimeError("duplicate DEV case ids")
    for t in tasks:
        if t.repository not in DEV_REPOS:
            raise RuntimeError(f"unexpected repository {t.repository}")


def verified_baselines(tasks_by_id: dict) -> dict:
    """Recompute frozen baselines from raw artifacts (Sparse, Route-B, Qwen, SweRank)."""
    def contrib(write_set, proxy, ranked, omitted_size, B):
        final = set(write_set) | set(ranked[: min(B, omitted_size)])
        tp = len(final & set(proxy))
        fp = len(final - set(proxy))
        fn = len(set(proxy) - final)
        return tp, fp, fn

    def pooled(contribs):
        tp = sum(c[0] for c in contribs)
        fp = sum(c[1] for c in contribs)
        fn = sum(c[2] for c in contribs)
        return {"tp": tp, "fp": fp, "fn": fn,
                "f1": 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0,
                "precision": tp / (tp + fp) if (tp + fp) else 0.0,
                "recall": tp / (tp + fn) if (tp + fn) else 0.0,
                "fnr": fn / (tp + fn) if (tp + fn) else 0.0}

    qwen_rankings = json.loads(
        (QWEN_DIR / "realization_A" / "task_rankings.json").read_text(encoding="utf-8"))
    swe = json.loads(SWERANK_RANKINGS.read_text(encoding="utf-8"))

    out: dict = {}
    for repo in DEV_REPOS:
        cids = [c for c in qwen_rankings if qwen_rankings[c]["repository"] == repo]
        sparse = []
        routeb5 = []
        qwen5 = []
        qwen1 = []
        for cid in cids:
            t = tasks_by_id[cid]
            r = qwen_rankings[cid]
            sparse.append(contrib(t.write_set, t.proxy, [], r["omitted_size"], 0))
            routeb5.append(contrib(t.write_set, t.proxy, r["routeb_ranked"], r["omitted_size"], 5))
            qwen5.append(contrib(t.write_set, t.proxy, r["qwen_ranked"], r["omitted_size"], 5))
            qwen1.append(contrib(t.write_set, t.proxy, r["qwen_ranked"], r["omitted_size"], 1))
        out[repo] = {
            "sparse": pooled(sparse),
            "routeb_b5": pooled(routeb5),
            "qwen_b5": pooled(qwen5),
            "qwen_b1": pooled(qwen1),
        }
    for repo in DEV_REPOS:
        cids = [c for c in swe if swe[c]["repository"] == repo]
        swe5 = []
        swe1 = []
        for cid in cids:
            t = tasks_by_id[cid]
            r = swe[cid]
            swe5.append(contrib(t.write_set, t.proxy, r["swe_ranked"], r["omitted_size"], 5))
            swe1.append(contrib(t.write_set, t.proxy, r["swe_ranked"], r["omitted_size"], 1))
        out[repo]["swerank_b5"] = pooled(swe5)
        out[repo]["swerank_b1"] = pooled(swe1)

    # SweRank exact-rank omitted-positive hit rates (POST-HOC diagnostic).
    hit = {}
    for repo in DEV_REPOS:
        c = {}
        for _cid, r in swe.items():
            if r["repository"] != repo:
                continue
            fn = set(r["fn_paths"])
            for i, f in enumerate(r["swe_ranked"][:5], start=1):
                if f in fn:
                    c[i] = c.get(i, 0) + 1
        hit[repo] = {str(k): v for k, v in sorted(c.items())}
    out["swerank_rank_hits"] = hit
    return out


def _hash_oof(oof: list[dict], final_sets: dict) -> str:
    blob = json.dumps(
        {"oof": [[r["case_id"], r["file_path"], round(r["prob"], 9)] for r in oof],
         "sets": {k: v for k, v in sorted(final_sets.items())}},
        sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def run_realization(rid: str, tasks_by_id: dict, fold_map: dict) -> dict:
    """Run the frozen pipeline for one realization and persist artifacts."""
    parquet = QWEN_DIR / f"realization_{rid}" / "full_file_scores.parquet"
    df = pd.read_parquet(parquet)
    if set(df["repository"].unique()) != set(DEV_REPOS):
        raise RuntimeError("unexpected repository set in score artifact")
    rows = F.build_rows(df, tasks_by_id, top_add_universe=F.TOP_ADD_UNIVERSE)
    frame = F.rows_to_frame(rows)

    results = A.run_nested_cv(frame, tasks_by_id, fold_map, n_folds=N_FOLDS)
    gate = A.evaluate_gate(results)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(OUT_DIR / f"candidate_universe_{rid}.parquet", index=False, compression="zstd")
    pd.DataFrame(results["oof"]).to_parquet(
        OUT_DIR / f"oof_probabilities_{rid}.parquet", index=False, compression="zstd")
    OUT_DIR.joinpath(f"fold_assignments_{rid}.json").write_text(
        json.dumps(fold_map, sort_keys=True, indent=1), encoding="utf-8")
    OUT_DIR.joinpath(f"final_oof_predictions_{rid}.json").write_text(
        json.dumps(results["final_sets"], sort_keys=True, indent=1), encoding="utf-8")
    OUT_DIR.joinpath(f"repo_metrics_{rid}.json").write_text(
        json.dumps(results["repo_metrics"], indent=1), encoding="utf-8")
    OUT_DIR.joinpath(f"bootstrap_ci_{rid}.json").write_text(
        json.dumps(results["bootstrap"], indent=1), encoding="utf-8")
    OUT_DIR.joinpath(f"calibration_{rid}.json").write_text(
        json.dumps(results["calibration"], indent=1), encoding="utf-8")
    OUT_DIR.joinpath(f"error_decomposition_{rid}.json").write_text(
        json.dumps(results["error_decomposition"], indent=1), encoding="utf-8")
    OUT_DIR.joinpath(f"set_size_analysis_{rid}.json").write_text(
        json.dumps(results["set_size"], indent=1), encoding="utf-8")
    OUT_DIR.joinpath(f"fold_details_{rid}.json").write_text(
        json.dumps(results["per_fold"], indent=1), encoding="utf-8")
    OUT_DIR.joinpath(f"gate_{rid}.json").write_text(json.dumps(gate, indent=1), encoding="utf-8")
    return results, gate


def robustness_ab(res_a: dict, gate_a: dict, res_b: dict, gate_b: dict) -> dict:
    """Frozen realization-B robustness comparison (mission 27)."""
    common = sorted(set(res_a["final_sets"]) & set(res_b["final_sets"]))
    same = sum(1 for c in common if set(res_a["final_sets"][c]) == set(res_b["final_sets"][c]))
    jac = []
    for c in common:
        sa, sb = set(res_a["final_sets"][c]), set(res_b["final_sets"][c])
        u = sa | sb
        jac.append(len(sa & sb) / len(u) if u else 1.0)
    verdict_same = bool(gate_a["both_repos_pass"] == gate_b["both_repos_pass"])
    out = {
        "n_tasks_common": len(common),
        "exact_same_selected_set_percentage": round(100.0 * same / len(common), 2) if common else None,
        "jaccard_mean": round(float(np.mean(jac)), 4) if jac else None,
        "jaccard_median": round(float(np.median(jac)), 4) if jac else None,
        "jaccard_min": round(float(np.min(jac)), 4) if jac else None,
        "jaccard_max": round(float(np.max(jac)), 4) if jac else None,
        "gate_verdict_same": bool(verdict_same),
        "gate_a": {r: gate_a["gate"][r]["pass"] for r in DEV_REPOS},
        "gate_b": {r: gate_b["gate"][r]["pass"] for r in DEV_REPOS},
    }
    for repo in DEV_REPOS:
        out[f"f1_{repo}_A"] = res_a["repo_metrics"][repo]["policy"]["f1"]
        out[f"f1_{repo}_B"] = res_b["repo_metrics"][repo]["policy"]["f1"]
        out[f"delta_f1_{repo}_A_minus_B"] = (
            res_a["repo_metrics"][repo]["policy"]["f1"] - res_b["repo_metrics"][repo]["policy"]["f1"])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--realization", choices=("A", "B"), default="A")
    ap.add_argument("--determinism-reruns", type=int, default=2)
    args = ap.parse_args()

    tasks = load_dev_tasks()
    sealed_guard(tasks)
    tasks_by_id = {t.case_id: t for t in tasks}

    baselines = verified_baselines(tasks_by_id)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.joinpath("verified_baselines.json").write_text(
        json.dumps(baselines, indent=1), encoding="utf-8")

    fold_map = Fd.grouped_stratified_folds(sorted(tasks_by_id), lambda c: tasks_by_id[c].repository,
                                           k=N_FOLDS, seed=FOLD_SEED)

    # Gate G: deterministic local rerun -> identical OOF predictions + final sets.
    determinism = {}
    hashes = []
    for rep in range(args.determinism_reruns):
        res, gate = run_realization(args.realization, tasks_by_id, fold_map)
        h = _hash_oof(res["oof"], res["final_sets"])
        hashes.append(h)
        if rep == 0:
            primary_res, primary_gate = res, gate
    determinism = {
        "reruns": args.determinism_reruns,
        "oof_and_sets_identical": len(set(hashes)) == 1,
        "sha256": hashes,
    }
    OUT_DIR.joinpath(f"determinism_{args.realization}.json").write_text(
        json.dumps(determinism, indent=1), encoding="utf-8")

    results, gate = primary_res, primary_gate
    OUT_DIR.joinpath(f"results_{args.realization}.json").write_text(
        json.dumps({"realization": args.realization, "results": results, "gate": gate},
                   indent=1), encoding="utf-8")

    if args.realization == "A":
        # Primary verdict file.
        verdict = {
            "realization": "A",
            "verdict": None,
            "gate": gate,
            "baselines_verified": baselines,
            "determinism": determinism,
        }
        both = gate["both_repos_pass"]
        verdict["verdict"] = "CALIBRATED_SET_SELECTION_V1_PASS" if both else "CALIBRATED_SET_SELECTION_V1_FAIL"
        OUT_DIR.joinpath("verdict_A.json").write_text(json.dumps(verdict, indent=1), encoding="utf-8")
        print(json.dumps({"verdict_primary_A": verdict["verdict"],
                          "gate_both_repos": both,
                          "pareto": gate["pareto_success"],
                          "determinism_identical": determinism["oof_and_sets_identical"]}, indent=1))
    else:
        # Robustness: requires the A verdict artifacts present.
        verdict_a_path = OUT_DIR / "verdict_A.json"
        if not verdict_a_path.exists():
            print("run realization A first (primary verdict required for A/B robustness)")
            return 1
        va = json.loads(verdict_a_path.read_text(encoding="utf-8"))
        ra = json.loads((OUT_DIR / "results_A.json").read_text(encoding="utf-8"))
        rb = json.loads((OUT_DIR / f"results_{args.realization}.json").read_text(encoding="utf-8"))
        rob = robustness_ab(ra["results"], va["gate"], rb["results"], rb["gate"])
        OUT_DIR.joinpath("robustness_ab.json").write_text(json.dumps(rob, indent=1), encoding="utf-8")
        verdict_b = {"realization": "B",
                     "verdict": "CALIBRATED_SET_SELECTION_V1_PASS" if rb["gate"]["both_repos_pass"]
                     else "CALIBRATED_SET_SELECTION_V1_FAIL",
                     "gate": rb["gate"]}
        OUT_DIR.joinpath("verdict_B.json").write_text(json.dumps(verdict_b, indent=1), encoding="utf-8")

        a_verdict = va["verdict"]
        b_verdict = verdict_b["verdict"]
        final = None
        if a_verdict == "CALIBRATED_SET_SELECTION_V1_PASS" and b_verdict == "CALIBRATED_SET_SELECTION_V1_PASS":
            final = "CALIBRATED_SET_SELECTION_V1_PASS"
        elif a_verdict != b_verdict:
            final = "CALIBRATED_SET_SELECTION_V1_ROBUSTNESS_INCONCLUSIVE"
        else:
            final = "CALIBRATED_SET_SELECTION_V1_FAIL"
        OUT_DIR.joinpath("final_verdict.json").write_text(
            json.dumps({"verdict": final, "verdict_A": a_verdict, "verdict_B": b_verdict,
                        "robustness": rob}, indent=1), encoding="utf-8")
        print(json.dumps({"final_verdict": final, "verdict_A": a_verdict, "verdict_B": b_verdict,
                          "exact_same_set_pct": rob["exact_same_selected_set_percentage"],
                          "jaccard_mean": rob["jaccard_mean"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
