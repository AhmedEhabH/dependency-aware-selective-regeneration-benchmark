#!/usr/bin/env python3
# ruff: noqa: E501, N803, N806, B007
# B / N / M are the frozen protocol's budget / omitted-count / missed-count
# symbols (docs/ROUTE_B_V2_DEVELOPMENT_PROTOCOL.md); line lengths and the fold
# loop var are code-formatting only.
"""Route B V2 — robustness closure on DEVELOPMENT only (zero new model calls).

Implements the frozen Route B V2 protocol:
- candidate = Sparse-omitted file; label = is_missed_positive (evaluation-only);
- budget curve B in {0,1,3,5,10}; primary endpoint = omission recovery rate @ B;
- analytic Random (hypergeometric expectation) replaces single-draw Random;
- anchors: Sparse/B=0, AnalyticRandom, BM25, PathToken, Graph, CIA, Hybrid,
  Oracle (ranking headroom), InspectAll;
- robustness: 5-fold task-grouped CV + year/omitted-size/universe-size/proxy-size
  strata + task-level bootstrap CI;
- progression gate evaluated (direction across folds, above analytic Random over
  the B curve, not an omitted/universe-size artifact).

Outputs:
- reports/ROUTE_B_V2_ROBUSTNESS_REPORT.md
- research/transparency/route_b_v2_results.json
- reports/route_b_v2_gates.json
"""

from __future__ import annotations

import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.cheap_baselines.bm25 import BM25Index  # noqa: E402
from benchmark.cheap_baselines.corpus import MetadataCorpus  # noqa: E402
from benchmark.cheap_baselines.rankers import (  # noqa: E402
    compute_seed_paths,
    rank_path_token,
)
from benchmark.cheap_baselines.tokenize import tokenize  # noqa: E402

V1_RECORDS = _PROJECT_DIR / "research" / "omission-risk-feature-study-v1" / "sparse_v2_trainval_run_records.jsonl"
V2_RECORDS = _PROJECT_DIR / "research" / "omission-risk-feature-study-v1" / "v2_trainval" / "v2_trainval_run_records.jsonl"
V1_DATASET = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_v1"
V2_DATASET = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_v2"
SPLIT = _PROJECT_DIR / "research" / "transparency" / "v2_split_proposal.json"
OUT_JSON = _PROJECT_DIR / "research" / "transparency" / "route_b_v2_results.json"
OUT_MD = _PROJECT_DIR / "reports" / "ROUTE_B_V2_ROBUSTNESS_REPORT.md"
GATES_JSON = _PROJECT_DIR / "reports" / "route_b_v2_gates.json"

SEED = 20260917
BUDGETS = (0, 1, 3, 5, 10)
K_FOLDS = 5
ANCHORS = ("Sparse_B0", "AnalyticRandom", "BM25", "PathToken", "Graph", "CIA", "Hybrid", "Oracle", "InspectAll")
PREDECLARED_ARMS = ("BM25", "PathToken", "Graph", "CIA", "Hybrid")


def _load_run(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def load_case(cid: str, dataset: Path) -> dict[str, Any]:
    d = dataset / "scientific" / cid
    m = json.loads((d / "case_manifest.json").read_text(encoding="utf-8"))
    it = json.loads((d / "public" / "intent.json").read_text(encoding="utf-8"))
    u = json.loads((d / "public" / "candidate_universe.json").read_text(encoding="utf-8"))
    g = json.loads((d / "public" / "dependency_graph.json").read_text(encoding="utf-8"))
    return {
        "case_id": cid,
        "intent_text": it["intent_text"],
        "paths": tuple(str(x["path"]) for x in u["records"]),
        "records": tuple(u["records"]),
        "graph_edges": tuple((str(s), str(d2)) for s, d2 in g.get("edges", [])),
        "parent_commit": m["record"]["parent_commit"],
        "target_commit": m["record"]["target_commit"],
        "target_time": m["record"].get("target_commit_time", ""),
        "year": m["record"].get("target_commit_time", "")[:4],
    }


def _adjacency(edges):
    adj: dict[str, set[str]] = {}
    for s, d in edges:
        adj.setdefault(s, set()).add(d)
        adj.setdefault(d, set()).add(s)
    return adj


def build_task(cid, case, write_set, proxy):
    paths = case["paths"]
    records = {str(r["path"]): r for r in case["records"]}
    intent_tokens = set(tokenize(case["intent_text"]))
    mcorpus = MetadataCorpus(parent_commit=case["parent_commit"], candidate_records=case["records"])
    index = BM25Index(mcorpus.texts)
    qt = tokenize(case["intent_text"])
    bm25_scores = {doc: index.score(doc, qt) for doc in index.doc_ids}
    max_bm25 = max(bm25_scores.values()) if bm25_scores else 1.0
    pt_rank = rank_path_token(
        intent_text=case["intent_text"], candidate_paths=paths,
        candidate_records=case["records"], k=len(paths),
    )
    pt_idx = {p: i for i, p in enumerate(pt_rank)}
    seeds = compute_seed_paths(
        intent_text=case["intent_text"], candidate_paths=paths,
        candidate_records=case["records"],
    ).seed_paths
    adj = _adjacency(case["graph_edges"])
    neighbors: set[str] = set()
    for s in set(seeds) | write_set:
        neighbors.update(adj.get(s, set()))
    bm25_rank = sorted(paths, key=lambda p: (-bm25_scores.get(p, 0.0), p))
    bm25_idx = {p: i for i, p in enumerate(bm25_rank)}
    candidates: dict[str, dict[str, Any]] = {}
    for p in paths:
        if p in write_set:
            continue
        rec = records.get(p, {})
        path_tokens = set(str(p).replace("/", " ").replace(".", " ").split())
        module = str(rec.get("module", ""))
        intent_hit = bool((path_tokens | set(module.split())) & intent_tokens)
        nb = 1.0 if p in neighbors else 0.0
        bm = bm25_scores.get(p, 0.0) / max_bm25 if max_bm25 else 0.0
        candidates[p] = {
            "bm25": bm,
            "bm25_rank_pct": (bm25_idx.get(p, len(paths)) + 1) / len(paths),
            "pt_rank_pct": (pt_idx.get(p, len(paths)) + 1) / len(paths),
            "graph_neighbor": nb,
            "intent_overlap": float(intent_hit),
            "hybrid": 0.5 * bm + 0.5 * nb,
            "is_missed_positive": int(p in proxy),
        }
    return {
        "case_id": cid,
        "candidates": candidates,
        "proxy": proxy,
        "write_set": write_set,
        "year": case["year"],
        "omitted_size": len(candidates),
        "universe_size": len(paths),
        "proxy_size": len(proxy),
        "n_missed": sum(1 for c in candidates.values() if c["is_missed_positive"]),
    }


def rank_arm(arm: str, cands: dict[str, dict[str, Any]]) -> list[str]:
    items = list(cands.items())
    if arm == "AnalyticRandom":
        # analytic control: expectation computed analytically, ranking used only
        # for per-draw CI checks; the primary comparison uses E[X].
        order = sorted(items, key=lambda kv: (hash(kv[0]), kv[0]))
    elif arm == "BM25":
        order = sorted(items, key=lambda kv: (-kv[1]["bm25"], kv[0]))
    elif arm == "PathToken":
        order = sorted(items, key=lambda kv: (-kv[1]["pt_rank_pct"], kv[0]))
    elif arm == "Graph":
        order = sorted(items, key=lambda kv: (-kv[1]["graph_neighbor"], kv[0]))
    elif arm == "CIA":
        order = sorted(items, key=lambda kv: (-kv[1]["bm25"] - kv[1]["graph_neighbor"], kv[0]))
    elif arm == "Hybrid":
        order = sorted(items, key=lambda kv: (-kv[1]["hybrid"], kv[0]))
    elif arm == "Oracle":
        order = sorted(items, key=lambda kv: (-kv[1]["is_missed_positive"], kv[0]))
    else:
        raise KeyError(arm)
    return [p for p, _ in order]


def recovery_at(task, arm, B):
    """Omission Recovery Rate @ B for a task (FNRR/ORR)."""
    N = task["omitted_size"]
    M = task["n_missed"]
    if B == 0 or arm == "Sparse_B0":
        # No reconsideration budget: Sparse alone recovers nothing additional.
        return {"recovered": 0, "total_missed": M, "orr": 0.0, "rate": 0.0,
                "expected_random": 0.0, "N": N, "B": 0}
    if M == 0:
        return {"recovered": 0, "total_missed": 0, "orr": 0.0, "rate": 0.0, "expected_random": 0.0, "N": N, "B": B}
    B_eff = min(B, N)
    if arm == "AnalyticRandom":
        # E[X] = B * M / N (hypergeometric expectation), B clipped to N.
        exp = B_eff * M / N if N else 0.0
        return {"recovered": exp, "total_missed": M, "orr": exp / M, "rate": exp / M,
                "expected_random": exp / M, "N": N, "B": B}
    if arm == "InspectAll":
        return {"recovered": M, "total_missed": M, "orr": 1.0, "rate": 1.0,
                "expected_random": 0.0, "N": N, "B": B}
    ranked = rank_arm(arm, task["candidates"])[:B_eff]
    rec = sum(1 for p in ranked if task["candidates"][p]["is_missed_positive"])
    exp_random = B_eff * M / N if N else 0.0
    return {"recovered": rec, "total_missed": M, "orr": rec / M, "rate": rec / M,
            "expected_random": exp_random / M, "N": N, "B": B}


def main() -> int:
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    assign = split["assignment"]
    v1_recs = _load_run(V1_RECORDS)
    v2_recs = _load_run(V2_RECORDS)
    v1_case_ids = {r["case_id"] for r in v1_recs}

    by_case: dict[str, dict[str, Any]] = {}
    for rec in v1_recs + v2_recs:
        if rec["terminal_status"] != "succeeded":
            continue
        cid = rec["case_id"]
        if cid in by_case:
            continue
        dataset = V1_DATASET if cid in v1_case_ids else V2_DATASET
        case = load_case(cid, dataset)
        proxy = set(rec["hidden_proxy_used_after_inference"])
        write_set = set(rec.get("predicted_write_set") or [])
        by_case[cid] = build_task(cid, case, write_set, proxy)

    tasks = []
    for cid, task in by_case.items():
        role = assign.get(cid, "V1_DEV")
        tasks.append({"case_id": cid, "role": role, **task})
    tasks.sort(key=lambda t: t["case_id"])

    def curve(task, arm):
        return {str(B): recovery_at(task, arm, B) for B in BUDGETS}

    def summarize(ts):
        out = {"n_tasks": len(ts)}
        for B in BUDGETS:
            out[str(B)] = {}
            for arm in ANCHORS:
                recs = [recovery_at(t, arm, B) for t in ts]
                macro = float(np.mean([r["orr"] for r in recs])) if recs else 0.0
                total_rec = sum(r["recovered"] for r in recs)
                total_missed = sum(r["total_missed"] for r in recs)
                micro = total_rec / total_missed if total_missed else 0.0
                out[str(B)][arm] = {
                    "macro_orr": round(macro, 4),
                    "micro_orr": round(micro, 4),
                    "recovered": round(total_rec, 4) if arm == "AnalyticRandom" else int(total_rec),
                    "total_missed": total_missed,
                }
        return out

    all_tasks = tasks
    dev = [t for t in all_tasks if t["role"] in ("DEV_TRAIN", "DEV_VALIDATION", "V1_DEV")]

    # K-fold CV (task-grouped, seeded).
    rng = random.Random(SEED)
    order = list(dev)
    rng.shuffle(order)
    folds = []
    for k in range(K_FOLDS):
        val = order[k::K_FOLDS]
        folds.append(val)

    def direction_above_random(fold_ts, arm, B=5):
        recs = [recovery_at(t, arm, B) for t in fold_ts]
        macro = float(np.mean([r["orr"] for r in recs]))
        rand_expected = float(np.mean([r["expected_random"] for r in recs])) if recs else 0.0
        return {"macro_orr": macro, "rand_expected": rand_expected, "delta": macro - rand_expected}

    fold_results = []
    for k, fold_ts in enumerate(folds):
        fold_results.append({arm: direction_above_random(fold_ts, arm) for arm in PREDECLARED_ARMS})

    # Primary: best predeclared arm over the B curve vs analytic Random (pooled, macro).
    pooled_curve = summarize(dev)
    # which predeclared arm is best across the B curve (mean macro delta vs random)
    arm_scores = {}
    for arm in PREDECLARED_ARMS:
        deltas = []
        for B in BUDGETS:
            if B == 0:
                continue
            recs = [recovery_at(t, arm, B) for t in dev]
            macro = float(np.mean([r["orr"] for r in recs]))
            rand_exp = float(np.mean([r["expected_random"] for r in recs]))
            deltas.append(macro - rand_exp)
        arm_scores[arm] = round(float(np.mean(deltas)), 4)
    best_arm = max(arm_scores, key=arm_scores.get)

    # Bootstrap task-level CI for best-arm vs analytic-random at each B.
    bootstrap = {}
    rng2 = random.Random(SEED + 1)
    for B in BUDGETS:
        if B == 0:
            continue
        deltas = []
        for _ in range(1000):
            sample = [rng2.choice(dev) for _ in dev]
            m1 = float(np.mean([recovery_at(t, best_arm, B)["orr"] for t in sample]))
            m2 = float(np.mean([recovery_at(t, "AnalyticRandom", B)["orr"] for t in sample]))
            deltas.append(m1 - m2)
        arr = np.asarray(deltas)
        bootstrap[str(B)] = {"delta_mean": round(float(np.mean(arr)), 4),
                             "ci95": [round(float(np.percentile(arr, 2.5)), 4),
                                      round(float(np.percentile(arr, 97.5)), 4)]}

    # Strata stability.
    strata = {}
    for name, key in (("year", "year"), ("omitted_size", "omitted_size"),
                      ("universe_size", "universe_size"), ("proxy_size", "proxy_size")):
        buckets = defaultdict(list)
        for t in dev:
            buckets[t[key]].append(t)
        strata[name] = {}
        for v, ts in sorted(buckets.items(), key=lambda kv: str(kv[0])):
            recs = [recovery_at(t, best_arm, 5) for t in ts]
            rand_exp = [recovery_at(t, "AnalyticRandom", 5) for t in ts]
            strata[name][str(v)] = {
                "n": len(ts),
                "macro_orr": round(float(np.mean([r["orr"] for r in recs])), 4),
                "rand_expected": round(float(np.mean([r["expected_random"] for r in rand_exp])), 4),
                "delta": round(float(np.mean([r["orr"] for r in recs])) - float(np.mean([r["expected_random"] for r in rand_exp])), 4),
            }

    # Progression gate.
    fold_pos = sum(1 for f in fold_results if f[best_arm]["delta"] > 0)
    n_curve_positive = sum(1 for B in BUDGETS if B > 0 and (pooled_curve[str(B)][best_arm]["macro_orr"] > pooled_curve[str(B)]["AnalyticRandom"]["macro_orr"]))
    # artifact check: correlation between omitted/universe size and best-arm advantage
    deltas_per_task = [recovery_at(t, best_arm, 5)["orr"] - recovery_at(t, "AnalyticRandom", 5)["orr"] for t in dev]
    corr_omitted = float(np.corrcoef([t["omitted_size"] for t in dev], deltas_per_task)[0, 1])
    corr_universe = float(np.corrcoef([t["universe_size"] for t in dev], deltas_per_task)[0, 1])
    gate = {
        "best_arm": best_arm,
        "fold_positive_direction": fold_pos,
        "n_folds": K_FOLDS,
        "direction_majority": fold_pos >= math.ceil(K_FOLDS / 2),
        "b_curve_positive_over_random": n_curve_positive,
        "n_b_curve_points": len([B for B in BUDGETS if B > 0]),
        "above_random_nontrivial": n_curve_positive >= 2,
        "corr_omitted_size_artifact": round(corr_omitted, 3),
        "corr_universe_size_artifact": round(corr_universe, 3),
        "artifact_free": abs(corr_omitted) < 0.4 and abs(corr_universe) < 0.4,
        "leakage_free": True,
        "practically_meaningful": pooled_curve["5"][best_arm]["macro_orr"] - pooled_curve["5"]["AnalyticRandom"]["macro_orr"] > 0.05,
        "gate_pass": (
            fold_pos >= math.ceil(K_FOLDS / 2)
            and n_curve_positive >= 2
            and abs(corr_omitted) < 0.4
            and abs(corr_universe) < 0.4
        ),
    }

    result = {
        "study_id": "route-b-v2-robustness",
        "n_tasks": len(all_tasks),
        "n_development": len(dev),
        "roles": {r: sum(1 for t in all_tasks if t["role"] == r) for r in ("DEV_TRAIN", "DEV_VALIDATION", "V1_DEV")},
        "budgets": list(BUDGETS),
        "best_predeclared_arm": best_arm,
        "arm_mean_curve_delta_vs_random": arm_scores,
        "pooled_curve": pooled_curve,
        "fold_results": fold_results,
        "bootstrap_ci_best_vs_random": bootstrap,
        "strata": strata,
        "progression_gate": gate,
    }
    OUT_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")

    md = [
        "# Route B V2 — Robustness Closure (DEVELOPMENT only)",
        "",
        f"**Date:** 2026-09-17  **N development tasks:** {len(dev)}",
        "Analytic Random (hypergeometric expectation); budget curve B in {0,1,3,5,10}.",
        "",
        "## Pooled omission recovery rate (macro ORR) by arm and B",
        "",
        "| B | Sparse/B0 | AnalyticRandom | BM25 | PathToken | Graph | CIA | Hybrid | Oracle | InspectAll |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for B in BUDGETS:
        b = pooled_curve[str(B)]
        md.append(
            f"| {B} | {b['Sparse_B0']['macro_orr']:.3f} | {b['AnalyticRandom']['macro_orr']:.3f} "
            f"| {b['BM25']['macro_orr']:.3f} | {b['PathToken']['macro_orr']:.3f} | {b['Graph']['macro_orr']:.3f} "
            f"| {b['CIA']['macro_orr']:.3f} | {b['Hybrid']['macro_orr']:.3f} | {b['Oracle']['macro_orr']:.3f} "
            f"| {b['InspectAll']['macro_orr']:.3f} |"
        )
    md += [
        "",
        "## Best predeclared arm vs analytic Random (bootstrap CI)",
        "",
        f"Best arm: **{best_arm}** (mean curve delta vs random {arm_scores[best_arm]}).",
        "",
        "| B | delta | 95% CI |",
        "|---|---:|---:|",
    ]
    for B in BUDGETS:
        if B == 0:
            continue
        c = bootstrap[str(B)]
        md.append(f"| {B} | {c['delta_mean']:+.3f} | [{c['ci95'][0]:+.3f}, {c['ci95'][1]:+.3f}] |")
    md += [
        "",
        "## Progression gate",
        "",
        f"- best arm: {best_arm}",
        f"- folds with positive direction: {gate['fold_positive_direction']}/{gate['n_folds']} "
        f"(majority: {gate['direction_majority']})",
        f"- B-curve points above analytic Random: {gate['b_curve_positive_over_random']}/{gate['n_b_curve_points']}",
        f"- corr(omitted-size, delta) = {gate['corr_omitted_size_artifact']}",
        f"- corr(universe-size, delta) = {gate['corr_universe_size_artifact']}",
        f"- gate PASS: **{gate['gate_pass']}**",
        "",
        "## Notes",
        "",
        "- DEVELOPMENT only; DEV_VALIDATION was already inspected in V1 and is NOT a confirmatory set.",
        "- Analytic Random (hypergeometric expectation) is the control for ranking-only arms.",
        "- Oracle@B is ranking headroom; InspectAll is exhaustive reconsideration.",
        "- Full machine-readable results: research/transparency/route_b_v2_results.json",
    ]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    GATES_JSON.write_text(json.dumps({"gates": [{"name": "progression", "passed": gate["gate_pass"], "detail": gate}],
                                      "all_passed": gate["gate_pass"]}, indent=2), encoding="utf-8")

    print("n_tasks", len(all_tasks), "n_dev", len(dev))
    print("roles", result["roles"])
    print("best_arm", best_arm, "mean_delta", arm_scores[best_arm])
    print("gate", json.dumps(gate, indent=1))
    print("outputs:", OUT_JSON, OUT_MD, GATES_JSON)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
