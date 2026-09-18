#!/usr/bin/env python3
# ruff: noqa: E501, N803, N806
# B / M / N are the frozen budget / missed-count / omitted-count symbols of the
# Route-B protocol; line lengths and loop vars are code-formatting only.
"""FIRST-PASS RECALL — Sections 6-8: ADD queues, matched-budget eval, oracle reviewer.

Defines at most THREE simple deterministic ADD-queue candidates on DEVELOPMENT
(frozen formulas, no hidden-proxy features, fixed tie-break, budgets
K in {1,3,5,10}) and compares them under the SAME inspection budget against:
  - Sparse baseline
  - current Route-B composite (BM25+GraphNeighbor, frozen)
  - BM25-only
  - analytic Random
  - Oracle-Add

Two views are reported (never conflated):
  A. ranking / recovery quality (ORR + unique FN beyond Route-B)
  B. naive final union F1 (top-K files simply unioned into the Sparse set)

Section 8: perfect-reviewer simulation — accept ONLY the true FNs in each
queue's top-K; report final F1, gap to Oracle-Add, and the split of loss into
ranking vs reviewer acceptance.

Outputs:
- reports/FN_ADD_QUEUE_EVALUATION.md
- reports/fn_add_queue_evaluation.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PROJECT_DIR / "src"))

from benchmark.recall.data import RecallTask, load_dev_tasks  # noqa: E402
from benchmark.recall.queues import (  # noqa: E402
    QUEUE_RANKERS,
    naive_union_metrics,
    oracle_reviewer_metrics,
)
from benchmark.recall.rankers import (  # noqa: E402
    rank_bm25,
    rank_composite,
    recovery,
)

OUT_MD = PROJECT_DIR / "reports" / "FN_ADD_QUEUE_EVALUATION.md"
OUT_JSON = PROJECT_DIR / "reports" / "fn_add_queue_evaluation.json"

BUDGETS = (1, 3, 5, 10)


def _fn_set(t: RecallTask) -> set[str]:
    return {c["path"] for c in t.candidates if c["is_missed_positive"]}


def _topk(t: RecallTask, ranked: list[str], B: int) -> list[str]:
    return ranked[: min(B, t.omitted_size)]


def _queue_macro(tasks, rfn, B):
    rs = [recovery(t, rfn(t), B) for t in tasks]
    return sum(r["orr"] for r in rs) / len(rs) if rs else 0.0


def _union_macro(tasks, queue_name, B):
    rows = [naive_union_metrics(t, queue_name, B) for t in tasks]
    return {k: round(sum(r[k] for r in rows), 1) for k in ("tp", "fp", "fn")}, rows


def _oracle_add_metrics(tasks, B):
    """Oracle-Add: add exactly min(B, fn) true FNs per task (zero FP)."""
    tp = fp = fn = 0
    for t in tasks:
        pos = set(t.proxy)
        pred = set(t.write_set)
        fn_set = pos - pred
        add = fn_set if B == "ALL" else set(list(sorted(fn_set))[:B])
        final = pred | add
        tp += len(final & pos)
        fp += len(final - pos)
        fn += len(pos - final)
    return _f1_metrics(tp, fp, fn)


def _f1_metrics(tp, fp, fn):
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": round(p, 4),
            "recall": round(r, 4), "f1": round(f1, 4)}


def _sparse_metrics(tasks):
    tp = fp = fn = 0
    for t in tasks:
        pos = set(t.proxy)
        pred = set(t.write_set)
        tp += len(pred & pos)
        fp += len(pred - pos)
        fn += len(pos - pred)
    return _f1_metrics(tp, fp, fn)


def _random_expectation(tasks, B):
    """Analytic hypergeometric expectation: E[X]=B*M/N summed / total."""
    tot = 0
    denom = 0
    for t in tasks:
        M = t.n_missed
        N = t.omitted_size
        if M == 0 or N == 0:
            continue
        tot += min(B, N) * M / N
        denom += M
    return round(tot / denom, 4) if denom else 0.0


def _union_f1(tasks, rfn, B):
    """Naive final union F1: top-B of a generic ranker unioned into Sparse."""
    tp = fp = fn = 0
    for t in tasks:
        ranked = rfn(t)
        Beff = min(B, t.omitted_size)
        added = set(ranked[:Beff])
        final = set(t.write_set) | added
        pos = set(t.proxy)
        tp += len(final & pos)
        fp += len(final - pos)
        fn += len(pos - final)
    return _f1_metrics(tp, fp, fn)


def _oracle_reviewer_f1(tasks, rfn, B):
    """Perfect-reviewer F1: only true FNs among top-B are accepted."""
    tp = fp = fn = 0
    for t in tasks:
        ranked = rfn(t)
        Beff = min(B, t.omitted_size)
        fn_set = set(t.proxy) - set(t.write_set)
        accepted = {p for p in ranked[:Beff] if p in fn_set}
        final = set(t.write_set) | accepted
        pos = set(t.proxy)
        tp += len(final & pos)
        fp += len(final - pos)
        fn += len(pos - final)
    return _f1_metrics(tp, fp, fn)


def main() -> int:
    tasks = load_dev_tasks()
    dc = [t for t in tasks if t.repository == "djangocms"]
    sc = [t for t in tasks if t.repository == "saleor"]

    result: dict = {
        "package": "fn_add_queue_evaluation",
        "date": "2026-09-18",
        "tier": "T3",
        "note": "Matched-budget DEVELOPMENT comparison. Queue formulas frozen pre-run; no hidden-proxy features; ZERO API. View A = ranking/recovery quality; View B = naive final union F1.",
        "queues": list(QUEUE_RANKERS),
        "budgets": list(BUDGETS),
        "repos": {},
    }

    for name, ts in (("djangocms_dev", dc), ("saleor_dev", sc)):
        sparse = _sparse_metrics(ts)
        route_b = {}
        bm25 = {}
        queues: dict = {q: {} for q in QUEUE_RANKERS}
        oracle_add = {}
        for B in BUDGETS:
            route_b[str(B)] = {
                "macro_orr": round(_queue_macro(ts, rank_composite, B), 4),
                "random_orr": _random_expectation(ts, B),
                "naive_union_f1": _union_f1(ts, rank_composite, B),
                "oracle_reviewer_f1": _oracle_reviewer_f1(ts, rank_composite, B),
            }
            bm25[str(B)] = {
                "macro_orr": round(_queue_macro(ts, rank_bm25, B), 4),
                "random_orr": _random_expectation(ts, B),
                "naive_union_f1": _union_f1(ts, rank_bm25, B),
                "oracle_reviewer_f1": _oracle_reviewer_f1(ts, rank_bm25, B),
            }
            oracle_add[str(B)] = _oracle_add_metrics(ts, B)
            for q in QUEUE_RANKERS:
                # view A
                qr = [recovery(t, QUEUE_RANKERS[q](t), B) for t in ts]
                macro = sum(r["orr"] for r in qr) / len(qr) if qr else 0.0
                # unique FN vs Route-B at same B
                uniq = 0
                overlap = 0
                total_fn = 0
                for t in ts:
                    Beff = min(B, t.omitted_size)
                    rt = set(rank_composite(t)[:Beff])
                    qt = set(QUEUE_RANKERS[q](t)[:Beff])
                    rfn = rt & _fn_set(t)
                    qfn = qt & _fn_set(t)
                    uniq += len(qfn - rfn)
                    overlap += len(qfn & rfn)
                    total_fn += t.n_missed
                # view B
                vB = [naive_union_metrics(t, q, B) for t in ts]
                agg_tp = sum(r["tp"] for r in vB)
                agg_fp = sum(r["fp"] for r in vB)
                agg_fn = sum(r["fn"] for r in vB)
                f1B = _f1_metrics(agg_tp, agg_fp, agg_fn)
                # oracle reviewer (view C, Section 8)
                vr = [oracle_reviewer_metrics(t, q, B) for t in ts]
                agg_tp2 = sum(r["tp"] for r in vr)
                agg_fp2 = sum(r["fp"] for r in vr)
                agg_fn2 = sum(r["fn"] for r in vr)
                f1R = _f1_metrics(agg_tp2, agg_fp2, agg_fn2)
                queues[q][str(B)] = {
                    "viewA_macro_orr": round(macro, 4),
                    "viewA_unique_fn_vs_routeB": uniq,
                    "viewA_overlap_routeB": overlap,
                    "viewA_total_fn": total_fn,
                    "viewB_naive_union_f1": f1B,
                    "viewC_oracle_reviewer_f1": f1R,
                    "n_accepted_by_reviewer": sum(r["n_accepted"] for r in vr),
                    "n_fns_in_top": sum(r["n_fns_in_top"] for r in vr),
                }
        result["repos"][name] = {
            "n_tasks": len(ts),
            "total_fn": sum(t.n_missed for t in ts),
            "sparse_baseline": sparse,
            "route_b_composite": route_b,
            "bm25_only": bm25,
            "queues": queues,
            "oracle_add": oracle_add,
        }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")

    md = [
        "# FN ADD-Queue Evaluation (matched budget, DEVELOPMENT)",
        "",
        "**Date:** 2026-09-18  **Tier:** T3 (ZERO API)  **Data:** djangoCMS DEV 174 + Saleor DEV 149",
        "",
        "Queue formulas (frozen, deterministic, no hidden-proxy features; tie-break = desc score then asc path):",
        "",
        "| ID | Formula | Rationale |",
        "|---|---|---|",
        "| Q1 BM25+ReverseDependency | score = bm25 + consumer | S006-like downstream consumers (taxonomy D, 16.8%/18.4% primary) |",
        "| Q2 BM25+ProviderConsumerSupport | score = bm25 + consumer + provider | directed dependency support (taxonomy D+E) |",
        "| Q3 BM25+ComplementaryUnion | score = bm25 + 2hop + co-change + sibling | INDIRECT_2HOP + HISTORY + STRUCTURAL_SIBLING union |",
        "",
        "**IMPORTANT — View A vs View B:** a queue may raise ORR while naive union F1 falls (FP additions).",
        "Both views are reported; superiority is claimed only on View A with View B not clearly worse.",
        "",
    ]
    for name, label in (("djangocms_dev", "djangoCMS DEV"), ("saleor_dev", "Saleor DEV")):
        r = result["repos"][name]
        md += [
            f"## {label} — sparse baseline + route-B",
            "",
            f"Sparse: TP {r['sparse_baseline']['tp']} FP {r['sparse_baseline']['fp']} "
            f"FN {r['sparse_baseline']['fn']} F1 {r['sparse_baseline']['f1']}",
            "",
            "| B | Route-B ORR | Random ORR | BM25 ORR | Oracle-Add F1 |",
            "|---|---:|---:|---:|---:|",
        ]
        for B in BUDGETS:
            rb = r["route_b_composite"][str(B)]
            b25 = r["bm25_only"][str(B)]
            oa = r["oracle_add"][str(B)]
            md.append(f"| {B} | {rb['macro_orr']:.3f} | {rb['random_orr']:.3f} | {b25['macro_orr']:.3f} | {oa['f1']:.3f} |")
        md += [
            "",
            f"### {label} — queue View A (macro ORR) + View B (naive union F1) + View C (oracle reviewer F1)",
            "",
            "| B | Ranker | ORR | unique FN vs Route-B | naive union F1 | oracle reviewer F1 |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        for B in BUDGETS:
            rb = r["route_b_composite"][str(B)]
            b25 = r["bm25_only"][str(B)]
            md.append(
                f"| {B} | Route-B | {rb['macro_orr']:.3f} | - | {rb['naive_union_f1']['f1']:.3f} | {rb['oracle_reviewer_f1']['f1']:.3f} |"
            )
            md.append(
                f"| {B} | BM25 | {b25['macro_orr']:.3f} | - | {b25['naive_union_f1']['f1']:.3f} | {b25['oracle_reviewer_f1']['f1']:.3f} |"
            )
            for q in QUEUE_RANKERS:
                d = r["queues"][q][str(B)]
                md.append(
                    f"| {B} | {q} | {d['viewA_macro_orr']:.3f} | {d['viewA_unique_fn_vs_routeB']} "
                    f"| {d['viewB_naive_union_f1']['f1']:.3f} | {d['viewC_oracle_reviewer_f1']['f1']:.3f} |"
                )

    md += [
        "",
        "## Oracle-Add reference (perfect add, zero FP)",
        "",
        "| Repo | B | F1 |",
        "|---|---:|---:|",
    ]
    for name, label in (("djangocms_dev", "djangoCMS"), ("saleor_dev", "Saleor")):
        for B in BUDGETS:
            oa = result["repos"][name]["oracle_add"][str(B)]
            md.append(f"| {label} | {B} | {oa['f1']:.3f} |")
    md += ["", "Machine-readable: reports/fn_add_queue_evaluation.json"]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    for name, label in (("djangocms_dev", "djangoCMS"), ("saleor_dev", "Saleor")):
        r = result["repos"][name]
        print(f"\n=== {label} ===")
        for B in (1, 3, 5, 10):
            row = "  ".join(
                f"{q}@{B} ORR={r['queues'][q][str(B)]['viewA_macro_orr']:.3f} "
                f"uniq={r['queues'][q][str(B)]['viewA_unique_fn_vs_routeB']} "
                f"F1B={r['queues'][q][str(B)]['viewB_naive_union_f1']['f1']:.3f} "
                f"F1R={r['queues'][q][str(B)]['viewC_oracle_reviewer_f1']['f1']:.3f}"
                for q in QUEUE_RANKERS
            )
            print(f"  B={B}: {row}")
    print("\noutputs:", OUT_MD, OUT_JSON)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
