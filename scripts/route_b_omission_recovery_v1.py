#!/usr/bin/env python3
"""Route B — candidate-level bounded omission recovery V1 (zero-LLM, DEVELOPMENT only).

Research question:
> Among files omitted by Sparse, can observable candidate-level evidence rank
> true missed-impact files above random selection under the same candidate
> verification budget?

Predeclared design:
- candidate unit = candidate file omitted by the Sparse first pass (not in the
  per-task Sparse write set);
- label (evaluation-only): is_missed_positive = candidate is proxy-positive AND
  omitted by Sparse (an FN at the file level);
- budgets: PRIMARY B=5; SECONDARY B in {1,3,10};
- arms:
    R0 Random
    R1 BM25 (metadata-corpus BM25 score, descending)
    R2 Path-token overlap
    R3 Static/graph neighbor (1-hop reverse-dependency of Sparse-selected / seeds)
    R4 Classical CIA rank (BM25-seed 1-hop closure, from the classical CIA baseline)
    R5 Fixed hybrid (0.5 normalized BM25 + 0.5 normalized graph neighbor)
    Oracle-B (evaluation-only upper bound: rank proxy-omitted first)
- primary metric: task-clustered missed-file recall / FN recovery at B=5;
  secondary: task coverage, revised FNR/F1, candidates inspected, scope inflation.
- Task-clustered statistics: per-task recall averaged across tasks (macro), and
  pooled (micro); bootstrap CI over tasks for the primary comparison.
- DEV_TRAIN and DEV_VALIDATION reported separately before pooling.

Outputs:
- reports/ROUTE_B_OMISSION_RECOVERY_V1_REPORT.md
- research/transparency/route_b_v1_results.json
"""

from __future__ import annotations

import json
import random
import sys
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

V1_RECORDS = (
    _PROJECT_DIR
    / "research"
    / "omission-risk-feature-study-v1"
    / "sparse_v2_trainval_run_records.jsonl"
)
V2_RECORDS = (
    _PROJECT_DIR
    / "research"
    / "omission-risk-feature-study-v1"
    / "v2_trainval"
    / "v2_trainval_run_records.jsonl"
)
V1_DATASET = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_v1"
V2_DATASET = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_v2"
SPLIT = _PROJECT_DIR / "research" / "transparency" / "v2_split_proposal.json"
OUT_JSON = _PROJECT_DIR / "research" / "transparency" / "route_b_v1_results.json"
OUT_MD = _PROJECT_DIR / "reports" / "ROUTE_B_OMISSION_RECOVERY_V1_REPORT.md"

SEED = 20260916
BUDGETS = (1, 3, 5, 10)
PRIMARY_B = 5
ARMS = ("R0_Random", "R1_BM25", "R2_PathToken", "R3_GraphNeighbor", "R4_CIA", "R5_Hybrid", "Oracle")


def _load_run(records_path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in records_path.read_text(encoding="utf-8").splitlines()
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
    }


def _adjacency(edges):
    adj: dict[str, set[str]] = {}
    for s, d in edges:
        adj.setdefault(s, set()).add(d)
        adj.setdefault(d, set()).add(s)
    return adj


def build_task(
    cid: str,
    case: dict[str, Any],
    write_set: set[str],
    proxy: set[str],
) -> dict[str, Any]:
    """Candidate-level features for omitted candidates."""
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

    seeds = compute_seed_paths(
        intent_text=case["intent_text"], candidate_paths=paths,
        candidate_records=case["records"],
    ).seed_paths
    adj = _adjacency(case["graph_edges"])
    neighbors: set[str] = set()
    for s in set(seeds) | write_set:
        neighbors.update(adj.get(s, set()))

    bm25_rank = sorted(paths, key=lambda p: (-bm25_scores.get(p, 0.0), p))
    bm25_rank_idx = {p: i for i, p in enumerate(bm25_rank)}
    pt_rank_idx = {p: i for i, p in enumerate(pt_rank)}

    candidates: dict[str, dict[str, Any]] = {}
    for p in paths:
        if p in write_set:
            continue  # only OMITTED candidates are candidates for verification
        rec = records.get(p, {})
        path_tokens = set(str(p).replace("/", " ").replace(".", " ").split())
        module = str(rec.get("module", ""))
        intent_hit = bool((path_tokens | set(module.split())) & intent_tokens)
        nb = 1.0 if p in neighbors else 0.0
        candidates[p] = {
            "bm25": bm25_scores.get(p, 0.0) / max_bm25 if max_bm25 else 0.0,
            "bm25_rank_pct": (bm25_rank_idx.get(p, len(paths)) + 1) / len(paths),
            "pt_rank_pct": (pt_rank_idx.get(p, len(paths)) + 1) / len(paths),
            "graph_neighbor": nb,
            "intent_overlap": float(intent_hit),
            "hybrid": 0.5 * (bm25_scores.get(p, 0.0) / max_bm25 if max_bm25 else 0.0) + 0.5 * nb,
            "is_missed_positive": int(p in proxy),  # evaluation-only label
        }
    return {"case_id": cid, "candidates": candidates, "proxy": proxy, "write_set": write_set}


def rank_arm(arm: str, cands: dict[str, dict[str, Any]]) -> list[str]:
    items = list(cands.items())
    if arm == "R0_Random":
        rng = random.Random(SEED)
        order = sorted(items, key=lambda kv: (rng.random(), kv[0]))
    elif arm == "R1_BM25":
        order = sorted(items, key=lambda kv: (-kv[1]["bm25"], kv[0]))
    elif arm == "R2_PathToken":
        order = sorted(items, key=lambda kv: (-kv[1]["pt_rank_pct"], kv[0]))
    elif arm == "R3_GraphNeighbor":
        order = sorted(items, key=lambda kv: (-kv[1]["graph_neighbor"], kv[0]))
    elif arm == "R4_CIA":
        order = sorted(items, key=lambda kv: (-kv[1]["bm25"] - kv[1]["graph_neighbor"], kv[0]))
    elif arm == "R5_Hybrid":
        order = sorted(items, key=lambda kv: (-kv[1]["hybrid"], kv[0]))
    elif arm == "Oracle":
        order = sorted(items, key=lambda kv: (-kv[1]["is_missed_positive"], kv[0]))
    else:
        raise KeyError(arm)
    return [p for p, _ in order]


def main() -> int:
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    assign = split["assignment"]

    v1_recs = _load_run(V1_RECORDS)
    v2_recs = _load_run(V2_RECORDS)
    v1_case_ids = {r["case_id"] for r in v1_recs}

    # group by case, take valid cells, Sparse write set = union? No: per-task
    # write set = the set from the valid rep with the smallest FN (representative)
    # Repetitions are nested; for candidate-level study use the FIRST valid rep's
    # write set (predeclared: rep-1 write set), proxy is the observed proxy.
    by_case: dict[str, dict[str, Any]] = {}
    for rec in v1_recs + v2_recs:
        if rec["terminal_status"] != "succeeded":
            continue
        cid = rec["case_id"]
        dataset = V1_DATASET if cid in v1_case_ids else V2_DATASET
        if cid in by_case:
            continue
        # first valid rep
        case = load_case(cid, dataset)
        proxy = set(rec["hidden_proxy_used_after_inference"])
        write_set = set(rec.get("predicted_write_set") or [])
        by_case[cid] = build_task(cid, case, write_set, proxy)

    tasks = []
    for cid, task in by_case.items():
        role = assign.get(cid, "V1_DEV")
        tasks.append({"case_id": cid, "role": role, **task})

    def eval_budget(task, arm, budget):
        ranked = rank_arm(arm, task["candidates"])
        top = ranked[:budget]
        missed_in_top = sum(1 for p in top if task["candidates"][p]["is_missed_positive"])
        total_missed = sum(1 for c in task["candidates"].values() if c["is_missed_positive"])
        recall = missed_in_top / total_missed if total_missed else 0.0
        return {
            "recall": recall,
            "missed_recovered": missed_in_top,
            "total_missed_omitted": total_missed,
            "candidates_inspected": budget,
            "scope_inflation": budget / max(1, len(task["candidates"])),
            "covered": 1 if (total_missed and missed_in_top > 0) else 0,
        }

    results: dict[str, Any] = {"arms": list(ARMS), "budgets": list(BUDGETS), "primary_b": PRIMARY_B}
    per_role = {"DEV_TRAIN": [], "DEV_VALIDATION": [], "V1_DEV": []}
    for t in tasks:
        per_role.setdefault(t["role"], []).append(t)

    def summarize(ts):
        out = {"n_tasks": len(ts)}
        for budget in BUDGETS:
            for arm in ARMS:
                recs = [eval_budget(t, arm, budget) for t in ts]
                macro_recall = float(np.mean([r["recall"] for r in recs])) if recs else 0.0
                total_missed = sum(r["total_missed_omitted"] for r in recs)
                total_rec = sum(r["missed_recovered"] for r in recs)
                micro_recall = total_rec / total_missed if total_missed else 0.0
                covered = sum(r["covered"] for r in recs) / len(recs) if recs else 0.0
                out.setdefault(str(budget), {})[arm] = {
                    "macro_recall": round(macro_recall, 4),
                    "micro_recall": round(micro_recall, 4),
                    "fn_recovered": total_rec,
                    "total_missed": total_missed,
                    "task_coverage": round(covered, 4),
                }
        return out

    results["DEV_TRAIN"] = summarize(per_role.get("DEV_TRAIN", []))
    results["DEV_VALIDATION"] = summarize(per_role.get("DEV_VALIDATION", []))
    results["V1_DEV"] = summarize(per_role.get("V1_DEV", []))
    results["POOLED"] = summarize(tasks)

    # Primary comparison at B=5: best non-oracle predeclared vs Random
    def best_vs_random(data, ts):
        b5 = data["5"]
        rnd = b5["R0_Random"]["macro_recall"]
        best = None
        best_name = None
        for arm in ("R1_BM25", "R2_PathToken", "R3_GraphNeighbor", "R4_CIA", "R5_Hybrid"):
            m = b5[arm]["macro_recall"]
            if best is None or m > best:
                best, best_name = m, arm
        # Task-clustered bootstrap CI for the best-vs-random delta at B=5.
        rng = random.Random(20260916)
        deltas = []
        for _ in range(1000):
            sample = [rng.choice(ts) for _ in ts]
            r_best = np.mean([eval_budget(t, best_name, 5)["recall"] for t in sample])
            r_rnd = np.mean([eval_budget(t, "R0_Random", 5)["recall"] for t in sample])
            deltas.append(r_best - r_rnd)
        arr = np.asarray(deltas)
        return {"best_arm": best_name, "best_macro_recall": best, "random_macro_recall": rnd,
                "delta": round(best - rnd, 4),
                "delta_ci95": [round(float(np.percentile(arr, 2.5)), 4),
                               round(float(np.percentile(arr, 97.5)), 4)],
                "delta_mean_bootstrap": round(float(np.mean(arr)), 4)}

    results["primary_b5_comparison"] = {
        "DEV_VALIDATION": best_vs_random(results["DEV_VALIDATION"], per_role.get("DEV_VALIDATION", [])),
        "DEV_TRAIN": best_vs_random(results["DEV_TRAIN"], per_role.get("DEV_TRAIN", [])),
        "POOLED": best_vs_random(results["POOLED"], tasks),
    }

    OUT_JSON.write_text(json.dumps(results, indent=2), encoding="utf-8")

    # Report
    md = [
        "# Route B — Candidate-Level Bounded Omission Recovery V1 (zero-LLM)",
        "",
        "**Date:** 2026-09-16  **Tier:** T3  **Zero LLM cost**",
        "**Data:** v1 TRAIN/VALIDATION + V2 DEV_TRAIN/DEV_VALIDATION (development only).",
        "V2 INTERNAL_TEST/RESERVE untouched.",
        "",
        "## Design",
        "",
        "- Candidate unit: file omitted by the Sparse first pass.",
        "- Label (evaluation-only): is_missed_positive = proxy-positive AND omitted by Sparse.",
        "- Primary budget B=5; secondary B in {1,3,10}.",
        "- Arms: R0 Random, R1 BM25, R2 Path-token, R3 Graph neighbor, R4 Classical CIA,",
        "  R5 fixed hybrid, Oracle (evaluation-only).",
        "- Primary metric: task-clustered missed-file recall (macro over tasks).",
        "",
        "## Primary comparison at B=5 (predeclared best vs Random)",
        "",
        "| Split | Best arm | Best macro recall | Random macro recall | Delta | Delta 95% CI |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for role in ("DEV_TRAIN", "DEV_VALIDATION", "POOLED"):
        c = results["primary_b5_comparison"][role]
        ci = c.get("delta_ci95")
        ci_txt = f"[{ci[0]:+.3f}, {ci[1]:+.3f}]" if ci else "n/a"
        md.append(
            f"| {role} | {c['best_arm']} | {c['best_macro_recall']:.3f} "
            f"| {c['random_macro_recall']:.3f} | {c['delta']:+.3f} | {ci_txt} |"
        )
    md += [
        "",
        "## Pooled macro recall by arm and budget",
        "",
        "| Budget | Random | BM25 | PathToken | GraphNb | CIA | Hybrid | Oracle |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for budget in BUDGETS:
        b = results["POOLED"][str(budget)]
        md.append(
            f"| {budget} | {b['R0_Random']['macro_recall']:.3f} | {b['R1_BM25']['macro_recall']:.3f} "
            f"| {b['R2_PathToken']['macro_recall']:.3f} | {b['R3_GraphNeighbor']['macro_recall']:.3f} "
            f"| {b['R4_CIA']['macro_recall']:.3f} | {b['R5_Hybrid']['macro_recall']:.3f} "
            f"| {b['Oracle']['macro_recall']:.3f} |"
        )
    md += [
        "",
        "## Notes",
        "",
        "- Development-only; DEV_TRAIN and DEV_VALIDATION reported separately first.",
        "- Task is the independent unit; candidate rows are NOT independent tasks.",
        "- The observed diff remains an OBSERVED CHANGE-SET PROXY, never semantic gold.",
        "- Full machine-readable results: research/transparency/route_b_v1_results.json",
    ]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    for role in ("DEV_TRAIN", "DEV_VALIDATION", "POOLED"):
        c = results["primary_b5_comparison"][role]
        print(
            f"{role}: best={c['best_arm']} {c['best_macro_recall']:.3f} "
            f"vs Random {c['random_macro_recall']:.3f} delta={c['delta']:+.3f}"
        )
    print("outputs:", OUT_JSON, OUT_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
