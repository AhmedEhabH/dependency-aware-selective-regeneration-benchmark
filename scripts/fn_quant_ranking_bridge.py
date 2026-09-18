#!/usr/bin/env python3
# ruff: noqa: E501, N803, N806
# B / M / N are the frozen budget / missed-count / omitted-count symbols of the
# Route-B protocol; line lengths and loop vars are code-formatting only.
"""RANKING BRIDGE (2026-09-18; T3 DEVELOPMENT; ZERO API).

Section 1 — reconfirm + freeze the measured ranking gap on djangoCMS DEV (174)
+ Saleor DEV (149): Sparse baseline, Route-B BM25+GraphNeighbor ORR @
K={1,3,5,10}, BM25-only ORR, reverse-1hop pool oracle availability, provider/
consumer pool availability, union-all availability, Oracle-Add, oracle-reviewer
F1.

Section 2 — exactly THREE transparent quantitative-structural rankers (frozen
before outcome inspection, feature provenance in
src/benchmark/recall/quant_rankers.py) compared at matched budget against
frozen Route-B, BM25-only, analytic Random, and Oracle ranking.

Outputs:
- reports/QUANT_STRUCTURAL_RANKING_BRIDGE_REPORT.md
- reports/fn_quant_ranking_bridge.json
- reports/fn_quant_ranking_bridge_gates.json
- reports/fn_quant_ranking_bridge_baseline_freeze.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PROJECT_DIR / "src"))

from benchmark.recall.ceilings import task_source_pool  # noqa: E402
from benchmark.recall.data import load_dev_tasks  # noqa: E402
from benchmark.recall.quant_rankers import (  # noqa: E402
    QUANT_RANKERS,
    artifact_corr,
    candidate_precision,
    deterministic_rank_time_ms,
    fold_direction,
    macro_orr,
    naive_union_f1,
    oracle_reviewer_f1,
    unique_fn_beyond_route_b,
)
from benchmark.recall.rankers import rank_bm25, rank_composite  # noqa: E402

OUT_MD = PROJECT_DIR / "reports" / "QUANT_STRUCTURAL_RANKING_BRIDGE_REPORT.md"
OUT_JSON = PROJECT_DIR / "reports" / "fn_quant_ranking_bridge.json"
OUT_GATES = PROJECT_DIR / "reports" / "fn_quant_ranking_bridge_gates.json"
OUT_BASELINE = PROJECT_DIR / "reports" / "fn_quant_ranking_bridge_baseline_freeze.json"

BUDGETS = (1, 3, 5, 10)
B_REF = 5
K_FOLDS = 5
SEED = 20260918

# Frozen reference values from the First-Pass Recall Baseline Freeze
# (reports/FIRST_PASS_RECALL_BASELINE_FREEZE.md) — Section 1 verification.
FROZEN_ROUTE_B = {
    "djangocms": {1: 0.0464, 3: 0.1177, 5: 0.1633, 10: 0.2512},
    "saleor": {1: 0.0775, 3: 0.1576, 5: 0.2369, 10: 0.3173},
}
FROZEN_BM25 = {
    # macro ORR to 3 decimals from FN_ADD_QUEUE_EVALUATION.md tables.
    "djangocms": {1: 0.046, 3: 0.113, 5: 0.161, 10: 0.226},
    "saleor": {1: 0.072, 3: 0.158, 5: 0.234, 10: 0.315},
}
FROZEN_REVERSE_1HOP = {"djangocms": 0.558, "saleor": 0.724}
FROZEN_UNION_ALL = {"djangocms": 0.725, "saleor": 0.870}
FROZEN_ORACLE_ADD = {"djangocms": 0.841, "saleor": 0.782}
FROZEN_ORACLE_REVIEWER_ROUTE_B = {"djangocms": 0.441, "saleor": 0.424}


def _fn_set(task) -> set[str]:
    return {c["path"] for c in task.candidates if c["is_missed_positive"]}


def _oracle_availability(tasks, source: str, K: int) -> float:
    """Fraction of total FN the source's oracle pool can surface at budget K."""
    total_fn = sum(t.n_missed for t in tasks)
    rec = 0
    for t in tasks:
        pool = task_source_pool(t, source).pool
        pool_fns = pool & _fn_set(t)
        rec += min(K, len(pool_fns))
    return round(rec / total_fn, 4) if total_fn else 0.0


def _oracle_add_f1(tasks, B: int) -> dict:
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
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": round(p, 4),
            "recall": round(r, 4), "f1": round(f1, 4)}


def _sparse_metrics(tasks) -> dict:
    tp = fp = fn = 0
    for t in tasks:
        pos = set(t.proxy)
        pred = set(t.write_set)
        tp += len(pred & pos)
        fp += len(pred - pos)
        fn += len(pos - pred)
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": round(p, 6),
            "recall": round(r, 6), "f1": round(f1, 6)}


def _oracle_reviewer_route_b(tasks, B: int) -> float:
    from benchmark.recall.quant_rankers import oracle_reviewer_f1

    return oracle_reviewer_f1(tasks, rank_composite, B)["f1"]


def section1(tasks_by_repo) -> dict:
    result = {}
    for name, ts in (("djangocms", tasks_by_repo["djangocms"]), ("saleor", tasks_by_repo["saleor"])):
        route_b = {str(B): round(macro_orr(ts, rank_composite, B), 4) for B in BUDGETS}
        bm25 = {str(B): round(macro_orr(ts, rank_bm25, B), 4) for B in BUDGETS}
        rev = _oracle_availability(ts, "GRAPH_REVERSE_1HOP", B_REF)
        cons_prov = _oracle_availability(ts, "UNION_CONSUMER_PROVIDER", B_REF)
        union_all = _oracle_availability(ts, "UNION_ALL", B_REF)
        oracle_add = _oracle_add_f1(ts, B_REF)
        oracle_rev_route_b = _oracle_reviewer_route_b(ts, B_REF)
        result[name] = {
            "n_tasks": len(ts),
            "sparse": _sparse_metrics(ts),
            "route_b_orr": route_b,
            "bm25_only_orr": bm25,
            "oracle_availability_reverse_1hop_K5": rev,
            "oracle_availability_consumer_provider_K5": cons_prov,
            "oracle_availability_union_all_K5": union_all,
            "oracle_add_f1_B5": oracle_add["f1"],
            "oracle_reviewer_route_b_f1_B5": oracle_rev_route_b,
            "verify": {
                "route_b_matches_frozen": {
                    str(B): abs(route_b[str(B)] - FROZEN_ROUTE_B[name][B]) < 1e-4 for B in BUDGETS
                },
                "bm25_matches_frozen": {
                    str(B): abs(bm25[str(B)] - FROZEN_BM25[name][B]) <= 0.002 for B in BUDGETS
                },
                "reverse_1hop_close": abs(rev - FROZEN_REVERSE_1HOP[name]) <= 0.005,
                "union_all_close": abs(union_all - FROZEN_UNION_ALL[name]) <= 0.005,
                "oracle_add_close": abs(oracle_add["f1"] - FROZEN_ORACLE_ADD[name]) <= 0.005,
                "oracle_reviewer_route_b_close": abs(oracle_rev_route_b - FROZEN_ORACLE_REVIEWER_ROUTE_B[name]) <= 0.01,
            },
        }
    return result


def _random_expectation(tasks, B):
    tot, denom = 0.0, 0
    for t in tasks:
        M, N = t.n_missed, t.omitted_size
        if M == 0 or N == 0:
            continue
        tot += min(B, N) * M / N
        denom += M
    return round(tot / denom, 4) if denom else 0.0


def _oracle_ranking_orr(tasks, B):
    """Oracle ranking: every FN placed first; ORR = min(B, fn)/fn capped at 1."""
    rs = []
    for t in tasks:
        M, N = t.n_missed, t.omitted_size
        if M == 0:
            rs.append(0.0)
            continue
        rs.append(min(B, M, N) / M)
    return round(sum(rs) / len(rs), 4) if rs else 0.0


def section2(tasks_by_repo) -> dict:
    result = {"formulas": {r: {"rationale": ""} for r in QUANT_RANKERS}, "repos": {}}
    for name, ts in (("djangocms", tasks_by_repo["djangocms"]), ("saleor", tasks_by_repo["saleor"])):
        per_b: dict = {}
        for B in BUDGETS:
            row: dict = {
                "route_b_macro_orr": round(macro_orr(ts, rank_composite, B), 4),
                "bm25_macro_orr": round(macro_orr(ts, rank_bm25, B), 4),
                "random_orr": _random_expectation(ts, B),
                "oracle_ranking_orr": _oracle_ranking_orr(ts, B),
                "route_b_naive_union_f1": naive_union_f1(ts, rank_composite, B)["f1"],
                "route_b_oracle_reviewer_f1": oracle_reviewer_f1(ts, rank_composite, B)["f1"],
                "quant": {},
            }
            for q, rfn in QUANT_RANKERS.items():
                row["quant"][q] = {
                    "macro_orr": round(macro_orr(ts, rfn, B), 4),
                    "orr_delta_vs_route_b": round(macro_orr(ts, rfn, B) - row["route_b_macro_orr"], 4),
                    "candidate_precision": round(candidate_precision(ts, rfn, B), 4),
                    "route_b_candidate_precision": round(candidate_precision(ts, rank_composite, B), 4),
                    "unique_fn_beyond_route_b": unique_fn_beyond_route_b(ts, rfn, B),
                    "naive_union_f1": naive_union_f1(ts, rfn, B)["f1"],
                    "oracle_reviewer_f1": oracle_reviewer_f1(ts, rfn, B)["f1"],
                }
            per_b[str(B)] = row
        # reference B=5 detail
        b5 = per_b["5"]
        for q, rfn in QUANT_RANKERS.items():
            d = b5["quant"][q]
            d["fold_direction_frac"] = [round(x, 3) for x in fold_direction(ts, rfn, B_REF, K_FOLDS, SEED)]
            d["fold_majority_positive"] = sum(1 for x in d["fold_direction_frac"] if x >= 0.5) >= 3
            corr_uni, corr_omi = artifact_corr(ts, rfn, B_REF)
            d["corr_universe_size"] = round(corr_uni, 3)
            d["corr_omitted_size"] = round(corr_omi, 3)
            d["artifact_free"] = abs(corr_uni) < 0.4 and abs(corr_omi) < 0.4
            d["deterministic_rank_time_ms_total"] = deterministic_rank_time_ms(ts, rfn)
        result["repos"][name] = {"n_tasks": len(ts), "total_fn": sum(t.n_missed for t in ts), "B": per_b}
    return result


def gate(s2: dict) -> dict:
    decision_rows = {}
    for q in QUANT_RANKERS:
        conds = {}
        for repo in ("djangocms", "saleor"):
            d = s2["repos"][repo]["B"]["5"]["quant"][q]
            rb_f1 = s2["repos"][repo]["B"]["5"]["route_b_naive_union_f1"]
            rb_rev = s2["repos"][repo]["B"]["5"]["route_b_oracle_reviewer_f1"]
            conds[repo] = {
                "orr_delta": d["orr_delta_vs_route_b"],
                "materially_better_orr": d["orr_delta_vs_route_b"] > 0.05,
                "fold_majority_positive": d["fold_majority_positive"],
                "naive_f1_not_clearly_worse": (rb_f1 - d["naive_union_f1"]) <= 0.05,
                "oracle_reviewer_improves_over_route_b": d["oracle_reviewer_f1"] >= rb_rev,
                "artifact_free": d["artifact_free"],
            }
        c1 = conds["djangocms"]["materially_better_orr"] and conds["saleor"]["materially_better_orr"]
        c2 = conds["djangocms"]["fold_majority_positive"] and conds["saleor"]["fold_majority_positive"]
        c3 = conds["djangocms"]["naive_f1_not_clearly_worse"] and conds["saleor"]["naive_f1_not_clearly_worse"]
        c4 = conds["djangocms"]["artifact_free"] and conds["saleor"]["artifact_free"]
        c5 = True  # no hidden-proxy features by construction (tested in unit suite)
        c6 = True  # deterministic count + BM25, strictly simpler than an LLM verifier
        pass_flag = all((c1, c2, c3, c4, c5, c6))
        decision_rows[q] = {
            "repos": conds,
            "gate": {"c1_orr_materially_better_both": c1, "c2_fold_majority_both": c2,
                     "c3_naive_f1_not_clearly_worse": c3, "c4_no_size_artifact": c4,
                     "c5_no_leakage": c5, "c6_simpler_than_verifier": c6,
                     "pass": pass_flag},
        }
    any_pass = any(r["gate"]["pass"] for r in decision_rows.values())
    decision = "QUANT_STRUCTURAL_RANKER_READY" if any_pass else "CHEAP_RANKING_CLOSED_FOR_NOW"
    return {"decision": decision, "reference_budget": B_REF, "rankers": decision_rows}


def main() -> int:
    tasks = load_dev_tasks()
    by_repo = {
        "djangocms": [t for t in tasks if t.repository == "djangocms"],
        "saleor": [t for t in tasks if t.repository == "saleor"],
    }

    s1 = section1(by_repo)
    s2 = section2(by_repo)
    g = gate(s2)

    baseline = {"package": "fn_quant_ranking_bridge_baseline_freeze", "date": "2026-09-18",
                "tier": "T3", "note": "Section-1 reconfirmation of the frozen ranking gap (DEVELOPMENT).",
                "repos": s1}
    OUT_BASELINE.write_text(json.dumps(baseline, indent=2), encoding="utf-8")

    result = {"package": "fn_quant_ranking_bridge", "date": "2026-09-18", "tier": "T3",
              "note": "Quantitative-structural ranking bridge (Section 1 baseline freeze + Section 2 rankers). ZERO API.",
              "formula_docs": "src/benchmark/recall/quant_rankers.py (provenance documented in module docstring)",
              "section1": s1, "section2": s2, "gate": g}
    OUT_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")
    OUT_GATES.write_text(json.dumps({"gates": [{"name": "quant_ranking_bridge", "passed": g["decision"] == "QUANT_STRUCTURAL_RANKER_READY", "decision": g["decision"], "detail": g}]}, indent=2), encoding="utf-8")

    md = [
        "# Quantitative-Structural Ranking Bridge (DEVELOPMENT, ZERO API)",
        "",
        "**Date:** 2026-09-18  **Tier:** T3  **Data:** djangoCMS DEV 174 + Saleor DEV 149",
        "",
        "## Section 1 — ranking-gap reconfirmation freeze",
        "",
        "| Repo | n | Sparse F1 | Route-B ORR@1/3/5/10 | BM25 ORR@5 | rev-1hop avail@5 | cons+prov avail@5 | UNION_ALL avail@5 | Oracle-Add F1@5 | oracle-reviewer F1@5 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, label in (("djangocms", "djangoCMS"), ("saleor", "Saleor")):
        r = s1[name]
        rb = " / ".join(f"{r['route_b_orr'][str(B)]:.3f}" for B in BUDGETS)
        md.append(
            f"| {label} | {r['n_tasks']} | {r['sparse']['f1']:.3f} | {rb} | {r['bm25_only_orr']['5']:.3f} "
            f"| {r['oracle_availability_reverse_1hop_K5']:.3f} | {r['oracle_availability_consumer_provider_K5']:.3f} "
            f"| {r['oracle_availability_union_all_K5']:.3f} | {r['oracle_add_f1_B5']:.3f} | {r['oracle_reviewer_route_b_f1_B5']:.3f} |"
        )
    md += [
        "",
        "Verification vs frozen numbers: ",
    ]
    for name, label in (("djangocms", "djangoCMS"), ("saleor", "Saleor")):
        v = s1[name]["verify"]
        md.append(f"- {label}: route-B exact " + ", ".join(f"B={B} {'OK' if v['route_b_matches_frozen'][str(B)] else 'MISMATCH'}" for B in BUDGETS)
                  + f"; reverse-1hop {'OK' if v['reverse_1hop_close'] else 'MISMATCH'}"
                  + f"; UNION_ALL {'OK' if v['union_all_close'] else 'MISMATCH'}"
                  + f"; Oracle-Add {'OK' if v['oracle_add_close'] else 'MISMATCH'}"
                  + f"; oracle-reviewer {'OK' if v['oracle_reviewer_route_b_close'] else 'MISMATCH'}")
    md += [
        "",
        "## Section 2 — three transparent quantitative-structural rankers",
        "",
        "Formulas (frozen before outcome inspection; feature provenance in `src/benchmark/recall/quant_rankers.py`):",
        "",
        "| ID | Formula |",
        "|---|---|",
        "| R1 BM25+RevSupport | score = bm25 + rev_norm (normalized reverse-seed-support count) |",
        "| R2 BM25+BidirSupport | score = bm25 + rev_norm + fwd_norm (both directions) |",
        "| R3 BM25+BidirNorm | score = bm25 + bidir_norm (single combined bidirectional term) |",
        "",
"Typed-edge support is NOT used (frozen graph exposes only untyped [src,dest] edges).",
        "",
    ]
    for label, repo_key in (("djangoCMS", "djangocms"), ("Saleor", "saleor")):
        b5 = s2["repos"][repo_key]["B"]["5"]
        md += [f"### {label} DEV @B=5", "",
               "| Ranker | ORR | dORR vs Route-B | cand. precision | unique FN > Route-B | naive union F1 | oracle-reviewer F1 | folds+ | artifact-free |",
               "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for q in QUANT_RANKERS:
            d = b5["quant"][q]
            md.append(
                f"| {q} | {d['macro_orr']:.3f} | {d['orr_delta_vs_route_b']:+.3f} | {d['candidate_precision']:.3f} "
                f"| {d['unique_fn_beyond_route_b']} | {d['naive_union_f1']:.3f} | {d['oracle_reviewer_f1']:.3f} "
                f"| {sum(1 for x in d['fold_direction_frac'] if x >= 0.5)}/{K_FOLDS} | {d['artifact_free']} |"
            )
        md.append("")
    md += [
        "## Gate decision",
        "",
        f"**{g['decision']}**",
        "",
        "| Ranker | c1 ORR>+0.05 both | c2 folds both | c3 naive-F1 ok | c4 artifact-free | c5 no-leak | c6 simpler | PASS |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for q, r in g["rankers"].items():
        gd = r["gate"]
        md.append(f"| {q} | {gd['c1_orr_materially_better_both']} | {gd['c2_fold_majority_both']} | "
                  f"{gd['c3_naive_f1_not_clearly_worse']} | {gd['c4_no_size_artifact']} | "
                  f"{gd['c5_no_leakage']} | {gd['c6_simpler_than_verifier']} | {gd['pass']} |")
    md += [
        "",
        "Machine-readable: reports/fn_quant_ranking_bridge.json, reports/fn_quant_ranking_bridge_gates.json, reports/fn_quant_ranking_bridge_baseline_freeze.json",
    ]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    for name, label in (("djangocms", "djangoCMS"), ("saleor", "Saleor")):
        b5 = s2["repos"][name]["B"]["5"]
        print(f"\n=== {label} ===")
        print("  Route-B ORR@5:", b5["route_b_macro_orr"], "BM25@5:", b5["bm25_macro_orr"],
              "Random@5:", b5["random_orr"], "Oracle@5:", b5["oracle_ranking_orr"])
        for q in QUANT_RANKERS:
            d = b5["quant"][q]
            print(f"  {q}: ORR={d['macro_orr']:.4f} d={d['orr_delta_vs_route_b']:+.4f} "
                  f"uniq={d['unique_fn_beyond_route_b']} F1B={d['naive_union_f1']:.3f} "
                  f"F1R={d['oracle_reviewer_f1']:.3f} folds={d['fold_direction_frac']}")
    print("\ndecision:", g["decision"])
    print("outputs:", OUT_MD, OUT_JSON, OUT_GATES, OUT_BASELINE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

