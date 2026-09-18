#!/usr/bin/env python3
# ruff: noqa: E501, N806, B007, B905
# B / K / M / N are the frozen budget / budget-point / missed-count /
# omitted-count symbols of the Route-B protocol; line lengths and loop vars
# are code-formatting only.
"""FIRST-PASS RECALL — Section 4+5: source-specific recall ceilings + complementarity.

For each cheap source and budget K in {1,3,5,10,ALL}:
  - oracle FN recovery count / ORR ceiling
  - marginal gain beyond the current Route-B composite
  - overlap with Route-B recovered FNs / unique contribution
  - candidate queue size (inspections per task)
  - expected Random recovery under the same queue size

Section 5: complementarity (Jaccard overlap of top-K queues, unique FN
recovery per source, pairwise/triple union gains, diminishing returns, repo
consistency).

Outputs:
- reports/FN_SOURCE_SPECIFIC_RECALL_CEILINGS.md
- reports/fn_source_specific_recall_ceilings.json
- reports/fn_source_complementarity.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PROJECT_DIR / "src"))

from benchmark.recall.ceilings import (  # noqa: E402
    BUDGETS,
    SOURCES,
    source_stats,
    task_source_pool,
)
from benchmark.recall.data import load_dev_tasks  # noqa: E402
from benchmark.recall.rankers import rank_bm25, rank_composite, rank_path_token  # noqa: E402

OUT_MD = PROJECT_DIR / "reports" / "FN_SOURCE_SPECIFIC_RECALL_CEILINGS.md"
OUT_JSON = PROJECT_DIR / "reports" / "fn_source_specific_recall_ceilings.json"
OUT_COMP = PROJECT_DIR / "reports" / "fn_source_complementarity.json"


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b) if (a | b) else 0.0


def main() -> int:
    tasks = load_dev_tasks()
    dc = [t for t in tasks if t.repository == "djangocms"]
    sc = [t for t in tasks if t.repository == "saleor"]

    ceilings: dict = {"package": "fn_source_ceiling_v1", "date": "2026-09-18", "tier": "T3",
                      "note": "Oracle characterization of candidate availability. No source uses the hidden proxy in its pool or ranking. ZERO API.", "repos": {}}
    for name, ts in (("djangocms_dev", dc), ("saleor_dev", sc)):
        total_fn = sum(t.n_missed for t in ts)
        per_source: dict = {}
        for src in SOURCES:
            per_source[src] = {}
            for K in BUDGETS:
                rows = [source_stats(t, src, K) for t in ts]
                total_ceiling = sum(r["oracle_ceiling"] for r in rows)
                total_queue = sum(r["queue_size"] for r in rows)
                total_route_b = sum(r["route_b_recovered_fns"] for r in rows)
                total_overlap = sum(r["overlap_with_route_b"] for r in rows)
                total_unique = sum(r["unique_fns"] for r in rows)
                total_random = sum(r["expected_random"] for r in rows)
                per_source[src][str(K)] = {
                    "oracle_fn_recovery": total_ceiling,
                    "oracle_orr": round(total_ceiling / total_fn, 4) if total_fn else 0.0,
                    "n_fns_in_pool_total": sum(r["n_fns_in_pool"] for r in rows),
                    "queue_size_total": total_queue,
                    "queue_size_mean_per_task": round(total_queue / len(ts), 4) if ts else 0.0,
                    "route_b_recovered_fns": total_route_b,
                    "overlap_with_route_b": total_overlap,
                    "unique_beyond_route_b": total_unique,
                    "expected_random_recovery": round(total_random, 4),
                    "random_orr": round(total_random / total_fn, 4) if total_fn else 0.0,
                }
        ceilings["repos"][name] = {"n_tasks": len(ts), "total_fn": total_fn, "sources": per_source}

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(ceilings, indent=2), encoding="utf-8")

    # ---------------- Section 5: complementarity ----------------
    comp: dict = {"package": "fn_complementarity_v1", "date": "2026-09-18", "tier": "T3",
                  "note": "Top-K candidate-queue overlap + unique FN recovery. Deterministic rankers, ZERO API.", "repos": {}}
    rankers = {"BM25": rank_bm25, "PATH_TOKEN": rank_path_token, "ROUTE_B_COMPOSITE": rank_composite}
    for name, ts in (("djangocms_dev", dc), ("saleor_dev", sc)):
        total_fn = sum(t.n_missed for t in ts)
        rows_all: dict = {}
        # top-K sets per ranker at K=5 (reference) and K=10
        for K in (5, 10):
            topk: dict[str, list[set]] = {r: [] for r in rankers}
            for t in ts:
                B_eff = min(K, t.omitted_size)
                for rname, rfn in rankers.items():
                    topk[rname].append(set(rfn(t)[:B_eff]))
            # Jaccard matrix (mean over tasks)
            jac: dict[str, dict[str, float]] = {}
            for a in rankers:
                jac[a] = {}
                for b in rankers:
                    jac[a][b] = round(float(sum(_jaccard(ta, tb) for ta, tb in zip(topk[a], topk[b])) / len(ts)), 4)
            # unique FN recovery per ranker (FN inside top-K, not in Sparse)
            uniq: dict[str, dict] = {}
            for rname, rfn in rankers.items():
                rec = 0
                tot = 0
                for t in ts:
                    B_eff = min(K, t.omitted_size)
                    top = set(rfn(t)[:B_eff])
                    fn_top = {c["path"] for c in t.candidates if c["path"] in top and c["is_missed_positive"]}
                    rec += len(fn_top)
                    tot += t.n_missed
                uniq[rname] = {"recovered_fns": rec, "orr": round(rec / tot, 4) if tot else 0.0}
            rows_all[str(K)] = {"jaccard_topK": jac, "fn_recovery": uniq}
        comp["repos"][name] = {"n_tasks": len(ts), "total_fn": total_fn, "topK": rows_all}

    # pairwise/triple union gains at K=5: oracle-ceiling of the UNION pool,
    # i.e. candidate-availability complementarity (pool-level, not ranker).
    # Base = current Route-B composite (BM25+1hop). We measure the marginal
    # pool-coverage ceiling when adding NON-BM25 complementary sources on top
    # of each other (diminishing-return build-up), plus the full complementary
    # union. BM25 alone is NOT the base: its pool already covers the universe,
    # so the interesting question is how many FNs the non-BM25 sources can
    # surface at all and how much they add over each other.
    pair_unions: dict = {}
    # Cumulative build-up: each step adds a complementary source to the pool.
    build_steps = [
        ("BASE_ROUTE_B_1HOP", "GRAPH_1HOP"),
        ("+REVERSE_1HOP", "GRAPH_REVERSE_1HOP"),
        ("+FORWARD_1HOP", "GRAPH_FORWARD_1HOP"),
        ("+2HOP", "GRAPH_2HOP"),
        ("+HISTORY", "HISTORY_COCHANGE"),
        ("+SIBLING", "STRUCTURAL_SIBLING"),
    ]
    for name, ts in (("djangocms_dev", dc), ("saleor_dev", sc)):
        total_fn = sum(t.n_missed for t in ts)
        row = {}
        for label, src in build_steps:
            rec = 0
            queue_total = 0
            for t in ts:
                # cumulative pool = union of all sources added up to this step
                pool: set[str] = set()
                for _, s in build_steps[: build_steps.index((label, src)) + 1]:
                    pool |= set(task_source_pool(t, s).pool)
                fns = {c["path"] for c in t.candidates if c["is_missed_positive"]}
                pool_fns = pool & fns
                q = min(5, len(pool))
                rec += min(5, len(pool_fns))
                queue_total += q
            row[label] = {
                "oracle_union_ceil_fn": rec,
                "oracle_union_ceil_orr": round(rec / total_fn, 4) if total_fn else 0.0,
                "queue_total": queue_total,
            }
        # marginal gain of each added source (ceiling at this step - previous)
        prev = 0
        for label, _ in build_steps:
            cur = row[label]["oracle_union_ceil_fn"]
            row[label]["marginal_fn_over_prev"] = cur - prev
            prev = cur
        pair_unions[name] = row
    comp["union_gains_at_K5_pool_ceiling"] = pair_unions
    OUT_COMP.write_text(json.dumps(comp, indent=2), encoding="utf-8")

    # ---------------- report ----------------
    md = [
        "# FN Source-Specific Recall Ceilings + Complementarity",
        "",
        "**Date:** 2026-09-18  **Tier:** T3 (ZERO API)  **Data:** djangoCMS DEV 174 + Saleor DEV 149",
        "",
        "Oracle-Recall ceiling = max FNs a source can surface at budget K if its ranking",
        "were perfect among the candidates its deterministic pool can emit. The hidden proxy",
        "is never used in a pool or ranking.",
        "",
        "## Section 4 — Oracle ceilings per source",
        "",
        f"### djangoCMS DEV (total FN = {sum(t.n_missed for t in dc)})",
        "",
        "| Source | K | ORR ceil | FN rec | queue/task | Route-B rec | overlap | unique | Random ORR |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for src in SOURCES:
        for K in BUDGETS:
            d = ceilings["repos"]["djangocms_dev"]["sources"][src][str(K)]
            md.append(
                f"| {src} | {K} | {d['oracle_orr']:.3f} | {d['oracle_fn_recovery']} "
                f"| {d['queue_size_mean_per_task']:.2f} | {d['route_b_recovered_fns']} "
                f"| {d['overlap_with_route_b']} | {d['unique_beyond_route_b']} | {d['random_orr']:.3f} |"
            )
    md += ["", f"### Saleor DEV (total FN = {sum(t.n_missed for t in sc)})", "",
           "| Source | K | ORR ceil | FN rec | queue/task | Route-B rec | overlap | unique | Random ORR |",
           "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for src in SOURCES:
        for K in BUDGETS:
            d = ceilings["repos"]["saleor_dev"]["sources"][src][str(K)]
            md.append(
                f"| {src} | {K} | {d['oracle_orr']:.3f} | {d['oracle_fn_recovery']} "
                f"| {d['queue_size_mean_per_task']:.2f} | {d['route_b_recovered_fns']} "
                f"| {d['overlap_with_route_b']} | {d['unique_beyond_route_b']} | {d['random_orr']:.3f} |"
            )
    md += [
        "",
        "## Section 5 — Complementarity",
        "",
        "### Jaccard overlap of top-K candidate queues (mean over tasks)",
        "",
    ]
    for repo_key, label in (("djangocms_dev", "djangoCMS DEV"), ("saleor_dev", "Saleor DEV")):
        for K in (5, 10):
            jac = comp["repos"][repo_key]["topK"][str(K)]["jaccard_topK"]
            md += [f"#### {label} @K={K}", "", "| | BM25 | PATH_TOKEN | ROUTE_B |", "|---|---:|---:|---:|"]
            for a in ("BM25", "PATH_TOKEN", "ROUTE_B_COMPOSITE"):
                md.append(f"| {a} | {jac[a]['BM25']:.3f} | {jac[a]['PATH_TOKEN']:.3f} | {jac[a]['ROUTE_B_COMPOSITE']:.3f} |")
            md.append("")
    md += ["### FN recovery per top-K ranker", "", "| Repo | K | BM25 ORR | PATH_TOKEN ORR | ROUTE_B ORR |", "|---|---:|---:|---:|---:|"]
    for repo_key, label in (("djangocms_dev", "djangoCMS"), ("saleor_dev", "Saleor")):
        for K in (5, 10):
            r = comp["repos"][repo_key]["topK"][str(K)]["fn_recovery"]
            md.append(f"| {label} | {K} | {r['BM25']['orr']:.3f} | {r['PATH_TOKEN']['orr']:.3f} | {r['ROUTE_B_COMPOSITE']['orr']:.3f} |")
    md += ["", "### Union-gain combos @K=5 (oracle pool ceiling; marginal FN over previous combo)", "", "| Repo | Combo | ORR ceil | marginal FN |", "|---|---:|---:|---:|"]
    for repo_key, label in (("djangocms_dev", "djangoCMS"), ("saleor_dev", "Saleor")):
        for combo, d in comp["union_gains_at_K5_pool_ceiling"][repo_key].items():
            md.append(f"| {label} | {combo} | {d['oracle_union_ceil_orr']:.3f} | {d['marginal_fn_over_prev']} |")
    md += [
        "",
        "Machine-readable: reports/fn_source_specific_recall_ceilings.json, reports/fn_source_complementarity.json",
    ]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    for name, ts in (("djangocms", dc), ("saleor", sc)):
        c = ceilings["repos"][name + "_dev"]
        print(f"\n=== {name} (total FN {c['total_fn']}) ===")
        for src in SOURCES:
            d5 = c["sources"][src]["5"]
            print(f"  {src:<24} ORRceil@5={d5['oracle_orr']:.3f} unique_beyond_routeB={d5['unique_beyond_route_b']}")
    print("\noutputs:", OUT_MD, OUT_JSON, OUT_COMP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
