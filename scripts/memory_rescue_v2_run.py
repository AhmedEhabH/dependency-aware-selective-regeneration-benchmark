#!/usr/bin/env python3
# ruff: noqa: N812
"""PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2 — primary analyzer (T3, ZERO API).

Mission: PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2
(HISTORY-AUGMENTED DEEP FALSE-NEGATIVE RECOVERY).

Primary score realization: Qwen realization A (chronologically first; the
choice is independent of downstream performance). Realization B is used ONLY
for the frozen realization-B robustness rerun.

Pipeline (frozen in docs/PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_IMPACT_
DECLARATION_2026-09-20.md):
  1. build the frozen V2 candidate universe (Sparse UNION Qwen dense top-20
     NON-SPARSE UNION memory candidates: top-10 structural by
     cochange_memory_score > 0 UNION top-10 episodic by episode_similarity);
  2. construct the EXACTLY-11 frozen features (7 V1 + cochange_sparse +
     cochange_top1 + log_history_change_count + episode_similarity);
  3. reuse the EXACT V1 outer fold assignments and the EXACT V1 model /
     scaler / inner-OOF threshold procedure (L2-LR C=1.0 liblinear
     max_iter=1000 seed 0; StandardScaler on continuous fit on training rows
     only; inner argmax pooled micro-F1 on 0.01..0.99, tie-break HIGHER);
  4. pooled per-repo P/R/F1/FNR; paired task bootstrap CIs (10,000 resamples,
     seed 20260920); calibration; error decomposition with channel
     attribution; set sizes; intent stratification; sparse-empty results;
     the frozen primary gate (A-G, unchanged from V1).

ZERO sealed data. NO Stage-5 execution. NO paid API calls. Deterministic.

Run:
  python scripts/memory_rescue_v2_run.py                 # realization A (primary)
  python scripts/memory_rescue_v2_run.py --realization B # robustness rerun
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
sys.path.insert(0, str(_PROJECT_DIR / "scripts"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from benchmark.calibrated.folds import grouped_stratified_folds  # noqa: E402
from benchmark.memory_rescue import analysis as MA  # noqa: E402
from benchmark.memory_rescue import candidates as C  # noqa: E402
from benchmark.memory_rescue.history import CACHE_ROOT  # noqa: E402
from benchmark.recall.data import load_dev_tasks  # noqa: E402

OUT_DIR = _PROJECT_DIR / "research" / "memory-rescue-v2"
QWEN_DIR = _PROJECT_DIR / "research" / "contamination-bridge" / "qwen_embed"
V1_FOLD_FILE = _PROJECT_DIR / "research" / "calibrated-set-selection-v1" / "fold_assignments_A.json"
MEMORY_CACHE = CACHE_ROOT / "memory_bundles.json"

DEV_REPOS = ("djangocms", "saleor")
FOLD_SEED = 20260920
N_FOLDS = 5


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


def load_memory_bundles(realization: str) -> dict[str, C.MemoryBundle]:
    """Load the cached per-task memory data and select the realization variant."""
    if not MEMORY_CACHE.exists():
        raise RuntimeError(
            f"memory cache missing: {MEMORY_CACHE}\n"
            "run scripts/memory_rescue_v2_history.py first")
    raw = json.loads(MEMORY_CACHE.read_text(encoding="utf-8"))
    out: dict[str, C.MemoryBundle] = {}
    for cid, t in raw["tasks"].items():
        v = t["variants"][realization]
        out[cid] = C.MemoryBundle(
            history_change_count={k: int(x) for k, x in t["history_change_count"].items()},
            cochange_sparse={k: float(x) for k, x in t["cochange_sparse"].items()},
            episode_similarity={k: float(x) for k, x in t["episode_similarity"].items()},
            episode_hit_count={k: int(x) for k, x in t["episode_hit_count"].items()},
            n_production_changing_commits=int(t["n_production_changing_commits"]),
            cochange_top1={k: float(x) for k, x in v["cochange_top1"].items()},
            structural=list(v["structural"]),
            episodic=list(t["episodic"]),
        )
    return out


def load_v1_fold_map(tasks_by_id: dict) -> dict[str, int]:
    """Reuse the EXACT V1 outer fold assignments (frozen; mission §20).

    Loads the persisted V1 fold map AND recomputes it deterministically; a
    mismatch is a hard error (proves exact reuse).
    """
    persisted = json.loads(V1_FOLD_FILE.read_text(encoding="utf-8"))
    recomp = grouped_stratified_folds(
        sorted(tasks_by_id), lambda c: tasks_by_id[c].repository, k=N_FOLDS, seed=FOLD_SEED)
    if persisted != recomp:
        raise RuntimeError("V1 fold assignment file does not match deterministic recompute")
    return persisted


def _hash_oof(oof: list[dict], final_sets: dict) -> str:
    blob = json.dumps(
        {"oof": [[r["case_id"], r["file_path"], round(r["prob"], 9)] for r in oof],
         "sets": {k: v for k, v in sorted(final_sets.items())}},
        sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def run_realization(rid: str, tasks_by_id: dict, fold_map: dict,
                    memory: dict) -> dict:
    """Run the frozen V2 pipeline for one realization and persist artifacts."""
    parquet = QWEN_DIR / f"realization_{rid}" / "full_file_scores.parquet"
    df = pd.read_parquet(parquet)
    if set(df["repository"].unique()) != set(DEV_REPOS):
        raise RuntimeError("unexpected repository set in score artifact")
    rows, provenance = C.build_rows_with_provenance(df, tasks_by_id, memory)
    frame = C.rows_to_frame(rows)

    results = MA.run_nested_cv_v2(frame, tasks_by_id, fold_map, provenance=provenance,
                                  n_folds=N_FOLDS)
    gate = MA.evaluate_gate(results)

    # descriptive stratified / sparse-empty analysis
    policy_contribs = {}
    sparse_contribs = {}
    oof_df = pd.DataFrame(results["oof"])
    for cid in tasks_by_id:
        sub = oof_df[oof_df["case_id"] == cid]
        sel = set(sub.loc[sub["selected"] == 1, "file_path"])
        sp = set(tasks_by_id[cid].write_set)
        pr = set(tasks_by_id[cid].proxy)
        policy_contribs[cid] = (len(sel & pr), len(sel - pr), len(pr - sel))
        sparse_contribs[cid] = (len(sp & pr), len(sp - pr), len(pr - sp))
    intent = MA.intent_stratification(tasks_by_id, policy_contribs, sparse_contribs)
    sparse_empty = MA.sparse_empty_metrics(tasks_by_id, policy_contribs)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(OUT_DIR / f"candidate_universe_{rid}.parquet", index=False,
                     compression="zstd")
    oof_df.to_parquet(OUT_DIR / f"oof_probabilities_{rid}.parquet", index=False,
                      compression="zstd")
    OUT_DIR.joinpath(f"fold_assignments_{rid}.json").write_text(
        json.dumps(fold_map, sort_keys=True, indent=1), encoding="utf-8")
    OUT_DIR.joinpath(f"provenance_{rid}.json").write_text(
        json.dumps({k: {f: sorted(v) for f, v in p.items()}
                    for k, p in provenance.items()}, sort_keys=True, indent=1),
        encoding="utf-8")
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
    OUT_DIR.joinpath(f"intent_stratification_{rid}.json").write_text(
        json.dumps(intent, indent=1), encoding="utf-8")
    OUT_DIR.joinpath(f"sparse_empty_{rid}.json").write_text(
        json.dumps(sparse_empty, indent=1), encoding="utf-8")
    OUT_DIR.joinpath(f"gate_{rid}.json").write_text(json.dumps(gate, indent=1), encoding="utf-8")
    return results, gate, intent, sparse_empty


def robustness_ab(res_a: dict, gate_a: dict, res_b: dict, gate_b: dict) -> dict:
    """Frozen realization-B robustness comparison (mission §32)."""
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
        for m in ("f1", "precision", "recall", "fnr"):
            out[f"{m}_{repo}_A"] = res_a["repo_metrics"][repo]["policy"][m]
            out[f"{m}_{repo}_B"] = res_b["repo_metrics"][repo]["policy"][m]
            out[f"delta_{m}_{repo}_A_minus_B"] = (
                res_a["repo_metrics"][repo]["policy"][m] - res_b["repo_metrics"][repo]["policy"][m])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--realization", choices=("A", "B"), default="A")
    ap.add_argument("--determinism-reruns", type=int, default=2)
    args = ap.parse_args()

    tasks = load_dev_tasks()
    sealed_guard(tasks)
    tasks_by_id = {t.case_id: t for t in tasks}
    fold_map = load_v1_fold_map(tasks_by_id)
    memory = load_memory_bundles(args.realization)

    # Gate G: deterministic local rerun -> identical OOF predictions + sets.
    determinism = {}
    hashes = []
    for rep in range(args.determinism_reruns):
        res, gate, intent, sparse_empty = run_realization(
            args.realization, tasks_by_id, fold_map, memory)
        h = _hash_oof(res["oof"], res["final_sets"])
        hashes.append(h)
        if rep == 0:
            primary = (res, gate, intent, sparse_empty)
    determinism = {
        "reruns": args.determinism_reruns,
        "oof_and_sets_identical": len(set(hashes)) == 1,
        "sha256": hashes,
    }
    OUT_DIR.joinpath(f"determinism_{args.realization}.json").write_text(
        json.dumps(determinism, indent=1), encoding="utf-8")

    results, gate, intent, sparse_empty = primary
    OUT_DIR.joinpath(f"results_{args.realization}.json").write_text(
        json.dumps({"realization": args.realization, "results": results, "gate": gate},
                   indent=1), encoding="utf-8")

    if args.realization == "A":
        verdict = {
            "realization": "A",
            "verdict": None,
            "gate": gate,
            "determinism": determinism,
        }
        verdict["verdict"] = ("PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_PASS"
                              if gate["both_repos_pass"]
                              else "PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL")
        OUT_DIR.joinpath("verdict_A.json").write_text(json.dumps(verdict, indent=1),
                                                      encoding="utf-8")
        print(json.dumps({"verdict_primary_A": verdict["verdict"],
                          "gate_both_repos": gate["both_repos_pass"],
                          "pareto": gate["pareto_success"],
                          "determinism_identical": determinism["oof_and_sets_identical"]},
                         indent=1))
    else:
        verdict_a_path = OUT_DIR / "verdict_A.json"
        if not verdict_a_path.exists():
            print("run realization A first (primary verdict required for A/B robustness)")
            return 1
        va = json.loads(verdict_a_path.read_text(encoding="utf-8"))
        ra = json.loads((OUT_DIR / "results_A.json").read_text(encoding="utf-8"))
        rb = json.loads((OUT_DIR / f"results_{args.realization}.json").read_text(encoding="utf-8"))
        rob = robustness_ab(ra["results"], va["gate"], rb["results"], rb["gate"])
        OUT_DIR.joinpath("robustness_ab.json").write_text(json.dumps(rob, indent=1),
                                                          encoding="utf-8")
        verdict_b = {"realization": "B",
                     "verdict": ("PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_PASS"
                                 if rb["gate"]["both_repos_pass"]
                                 else "PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL"),
                     "gate": rb["gate"]}
        OUT_DIR.joinpath("verdict_B.json").write_text(json.dumps(verdict_b, indent=1),
                                                      encoding="utf-8")
        a_verdict = va["verdict"]
        b_verdict = verdict_b["verdict"]
        pass_str = "PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_PASS"
        if a_verdict == pass_str and b_verdict == pass_str:
            final = pass_str
        elif a_verdict != b_verdict:
            final = "PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_ROBUSTNESS_INCONCLUSIVE"
        else:
            final = "PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL"
        OUT_DIR.joinpath("final_verdict.json").write_text(
            json.dumps({"verdict": final, "verdict_A": a_verdict, "verdict_B": b_verdict,
                        "robustness": rob}, indent=1), encoding="utf-8")
        print(json.dumps({"final_verdict": final, "verdict_A": a_verdict,
                          "verdict_B": b_verdict,
                          "exact_same_set_pct": rob["exact_same_selected_set_percentage"],
                          "jaccard_mean": rob["jaccard_mean"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
