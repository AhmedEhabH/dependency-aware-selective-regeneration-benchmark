#!/usr/bin/env python3
"""Classical/static CIA baseline V1 — deterministic, ZERO LLM (Milestone D).

Implements a fair classical change-impact-analysis baseline on the V2
development cases (150: 120 DEV_TRAIN + 30 DEV_VALIDATION), using ONLY
parent-visible inputs:

- input seed from intent-token ∩ candidate-token (the frozen non-leaking seed
  rule; NEVER the hidden proxy);
- budgeted propagation over the parent-only dependency graph:
    - CIA-1H: 1-hop reverse-dependency closure (seed ∪ dependents-of-seed);
    - CIA-2H: 2-hop budgeted propagation;
    - CIA-BFS: bounded BFS (graph ranker, hop-bounded) for comparison;
- BM25 and path_token included as lexical controls.

Each arm emits a ranked candidate list; P/R/F1/FNR are computed against the
hidden observed-change proxy (evaluation-time only). Graph build cost is
separated from query cost (graph built once per case from parent; query =
seeding + propagation).

Outputs:
- reports/CLASSICAL_CIA_BASELINE_V1_REPORT.md
- research/transparency/classical_cia_v1_results.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.cheap_baselines.bm25 import BM25Index  # noqa: E402
from benchmark.cheap_baselines.corpus import MetadataCorpus  # noqa: E402
from benchmark.cheap_baselines.rankers import (  # noqa: E402
    rank_graph,
    rank_path_token,
)
from benchmark.cheap_baselines.tokenize import tokenize  # noqa: E402

DATASET = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_v2"
MANIFEST = DATASET / "v2_development_manifest.json"
OUT_JSON = _PROJECT_DIR / "research" / "transparency" / "classical_cia_v1_results.json"
OUT_MD = _PROJECT_DIR / "reports" / "CLASSICAL_CIA_BASELINE_V1_REPORT.md"

K_VALUES = (1, 3, 5, 10)


def _load_case(cid: str) -> dict[str, Any]:
    case_dir = DATASET / "scientific" / cid
    intent = json.loads((case_dir / "public" / "intent.json").read_text(encoding="utf-8"))
    universe = json.loads((case_dir / "public" / "candidate_universe.json").read_text(encoding="utf-8"))
    graph = json.loads((case_dir / "public" / "dependency_graph.json").read_text(encoding="utf-8"))
    proxy = json.loads((case_dir / "hidden" / "observed_change_set_proxy.json").read_text(encoding="utf-8"))
    return {
        "case_id": cid,
        "intent_text": intent["intent_text"],
        "paths": tuple(str(r["path"]) for r in universe["records"]),
        "records": tuple(universe["records"]),
        "graph_edges": tuple((str(s), str(d)) for s, d in graph.get("edges", [])),
        "proxy": set(str(p) for p in proxy.get("paths", [])),
    }


def _adjacency(edges: tuple[tuple[str, str], ...]) -> dict[str, set[str]]:
    adj: dict[str, set[str]] = {}
    for s, d in edges:
        adj.setdefault(s, set()).add(d)
        adj.setdefault(d, set()).add(s)
    return adj


def _dependents(seeds: set[str], edges: tuple[tuple[str, str], ...]) -> set[str]:
    """Reverse-dependency closure: files that import (depend on) the seeds."""
    adj = _adjacency(edges)
    out: set[str] = set()
    for s in seeds:
        out.update(adj.get(s, set()))
    return out


def _cia_1hop(seed_paths: set[str], edges) -> tuple[str, ...]:
    depend = _dependents(seed_paths, edges)
    sel = seed_paths | depend
    ranked = sorted(sel, key=lambda p: (p not in seed_paths, p))
    return tuple(ranked)


def _cia_2hop(seed_paths: set[str], edges, max_hops: int = 2) -> tuple[str, ...]:
    adj = _adjacency(edges)
    dist: dict[str, int] = {}
    frontier = list(seed_paths)
    for n in frontier:
        dist[n] = 0
    hops = 0
    while frontier and hops < max_hops:
        hops += 1
        nxt: list[str] = []
        for node in frontier:
            for nb in adj.get(node, set()):
                if nb not in dist:
                    dist[nb] = hops
                    nxt.append(nb)
        frontier = nxt
    ranked = sorted(dist, key=lambda p: (dist[p], p))
    return tuple(ranked)


def _metrics(selected: set[str], proxy: set[str]) -> dict[str, Any]:
    tp = len(selected & proxy)
    fp = len(selected - proxy)
    fn = len(proxy - selected)
    prec = tp / len(selected) if selected else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) else 0.0
    return {
        "tp": tp, "fp": fp, "fn": fn, "selected": len(selected),
        "precision": round(prec, 6), "recall": round(rec, 6), "f1": round(f1, 6),
        "fnr": round(fn / (tp + fn) if (tp + fn) else 0.0, 6),
        "proxy_size": len(proxy),
    }


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cases = [r["case_id"] for r in manifest["cases"]]

    arms = ["BM25", "PATH_TOKEN", "GRAPH@K", "CIA_1H", "CIA_2H"]
    per_case: dict[str, dict[str, Any]] = {}
    agg: dict[str, dict[str, Any]] = {
        a: {k: {"tp": 0, "fp": 0, "fn": 0, "selected": 0} for k in K_VALUES} for a in arms
    }
    proxy_total = 0

    for cid in cases:
        c = _load_case(cid)
        proxy_total += len(c["proxy"])
        mcorpus = MetadataCorpus(parent_commit="", candidate_records=c["records"])
        index = BM25Index(mcorpus.texts)
        query_terms = tokenize(c["intent_text"])
        scores = {doc: index.score(doc, query_terms) for doc in index.doc_ids}
        bm25_rank = tuple(sorted(c["paths"], key=lambda p: (-scores.get(p, 0.0), p)))
        pt_rank = rank_path_token(
            intent_text=c["intent_text"], candidate_paths=c["paths"],
            candidate_records=c["records"], k=10,
        )
        graph_rank, seeds, reason = rank_graph(
            intent_text=c["intent_text"], candidate_paths=c["paths"],
            candidate_records=c["records"], graph_edges=c["graph_edges"], k=10,
        )
        seed_paths = set(seeds)
        cia1 = _cia_1hop(seed_paths, c["graph_edges"])
        cia2 = _cia_2hop(seed_paths, c["graph_edges"], max_hops=2)

        ranked = {
            "BM25": bm25_rank,
            "PATH_TOKEN": pt_rank,
            "GRAPH@K": graph_rank,
            "CIA_1H": cia1,
            "CIA_2H": cia2,
        }
        row: dict[str, Any] = {"case_id": cid, "proxy_size": len(c["proxy"]), "n_seeds": len(seed_paths)}
        for arm in arms:
            for k in K_VALUES:
                sel = set(ranked[arm][:k])
                m = _metrics(sel, c["proxy"])
                row[f"{arm}_k{k}"] = m
                agg[arm][k]["tp"] += m["tp"]
                agg[arm][k]["fp"] += m["fp"]
                agg[arm][k]["fn"] += m["fn"]
                agg[arm][k]["selected"] += m["selected"]
        per_case[cid] = row

    results: dict[str, Any] = {"n_cases": len(cases), "arms": arms, "k_values": list(K_VALUES)}
    micro: dict[str, Any] = {}
    for arm in arms:
        micro[arm] = {}
        for k in K_VALUES:
            a = agg[arm][k]
            prec = a["tp"] / a["selected"] if a["selected"] else 0.0
            rec = a["tp"] / (a["tp"] + a["fn"]) if (a["tp"] + a["fn"]) else 0.0
            f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) else 0.0
            micro[arm][str(k)] = {
                "tp": a["tp"], "fp": a["fp"], "fn": a["fn"],
                "selected": a["selected"],
                "precision": round(prec, 6), "recall": round(rec, 6), "f1": round(f1, 6),
                "fnr": round(a["fn"] / (a["tp"] + a["fn"]) if (a["tp"] + a["fn"]) else 0.0, 6),
            }
    results["micro"] = micro
    results["per_case"] = per_case
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(results, indent=2), encoding="utf-8")

    md = [
        "# Classical / Static CIA Baseline V1",
        "",
        "**Date:** 2026-09-16  **Tier:** T3  **Zero LLM cost**",
        f"**Data:** V2 development cases (N={len(cases)}: 120 DEV_TRAIN + 30 DEV_VALIDATION)",
        "",
        "## Method",
        "",
        "- Input seed = intent-token ∩ candidate-token (frozen non-leaking rule; never the proxy).",
        "- CIA-1H: seed ∪ 1-hop reverse-dependency closure (dependents of seeds).",
        "- CIA-2H: 2-hop budgeted propagation.",
        "- GRAPH@K: bounded BFS from seeds (frozen ranker).",
        "- BM25 / PATH_TOKEN: lexical controls.",
        "- Graph build cost (parent AST import graph, built once per case) is SEPARATED from",
        "  query cost (seeding + propagation).",
        "",
        "## Micro-averaged results (pooled over cases)",
        "",
        "| Arm | K | P | R | F1 | FNR |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for arm in arms:
        for k in K_VALUES:
            m = micro[arm][str(k)]
            md.append(f"| {arm} | {k} | {m['precision']:.3f} | {m['recall']:.3f} | {m['f1']:.3f} | {m['fnr']:.3f} |")
    md += [
        "",
        "## Notes",
        "",
        "- Development-only evidence; compared against BM25 on the same cases, NOT against P1 held-out numbers.",
        "- CIA arms emit a variable-size selected set (closure), so K slices the ranked closure;",
        "  fixed-K comparison keeps the lexical arms at matched output budgets.",
        "- The historical diff remains an OBSERVED CHANGE-SET PROXY, never semantic gold.",
    ]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    for arm in arms:
        row = micro[arm]["10"]
        print(f"{arm} K10: P={row['precision']:.3f} R={row['recall']:.3f} F1={row['f1']:.3f} FNR={row['fnr']:.3f}")
    print("outputs:", OUT_JSON, OUT_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
