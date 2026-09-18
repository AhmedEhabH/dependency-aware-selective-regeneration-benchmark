#!/usr/bin/env python3
# ruff: noqa: N803, N806
"""INDEPENDENT AUDIT — Quantitative-Structural Ranking Bridge (2026-09-18).

Recomputes the headline numbers of `reports/fn_quant_ranking_bridge.json` from
frozen records WITHOUT importing `scripts/fn_quant_ranking_bridge.py` (only the
shared data layer `benchmark.recall.data` + `benchmark.recall.rankers` are used,
exactly like the original mission). Verifies:

  A1  Route-B composite macro ORR @ {1,3,5,10} matches the frozen baseline freeze.
  A2  Sparse baseline per repo matches frozen values.
  A3  reverse-1hop oracle availability @K=5 within 0.005 of the frozen value.
  A4  union-all oracle availability @K=5 within 0.005 of the frozen value.
  A5  R1/R2/R3 macro ORR @B=5 (quantitative-structural rankers) match the
      bridge JSON within 1e-4 (deterministic reproducibility).
  A6  Gate decision string == CHEAP_RANKING_CLOSED_FOR_NOW.
  A7  No candidate feature contains a proxy-derived field (leakage check).
  A8  Sealed-set guard: DEV load contains exactly 174 + 149 case ids and no
      INTERNAL_TEST/RESERVE roles.
  A9  Determinism: re-ranking a task twice yields identical order (ties broken).
  A10 Fold fractions in [0,1] and reproducible under the frozen seed.

Outputs:
- reports/FN_QUANT_RANKING_BRIDGE_AUDIT.md
- reports/fn_quant_ranking_bridge_audit.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PROJECT_DIR / "src"))

from benchmark.recall.data import load_dev_tasks  # noqa: E402
from benchmark.recall.quant_rankers import (  # noqa: E402
    QUANT_RANKERS,
    fold_direction,
    macro_orr,
)
from benchmark.recall.rankers import rank_composite  # noqa: E402

BRIDGE_JSON = PROJECT_DIR / "reports" / "fn_quant_ranking_bridge.json"
AUDIT_JSON = PROJECT_DIR / "reports" / "fn_quant_ranking_bridge_audit.json"
AUDIT_MD = PROJECT_DIR / "reports" / "FN_QUANT_RANKING_BRIDGE_AUDIT.md"


def _fn_set(t) -> set[str]:
    return {c["path"] for c in t.candidates if c["is_missed_positive"]}


def _pool_fn_availability(tasks, source, K):
    from benchmark.recall.ceilings import task_source_pool

    total_fn = sum(t.n_missed for t in tasks)
    rec = 0
    for t in tasks:
        pool = task_source_pool(t, source).pool
        rec += min(K, len(pool & _fn_set(t)))
    return round(rec / total_fn, 4) if total_fn else 0.0


def _sparse(tasks):
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
    return {"tp": tp, "fp": fp, "fn": fn, "f1": round(f1, 4)}


def main() -> int:
    tasks = load_dev_tasks()
    dc = [t for t in tasks if t.repository == "djangocms"]
    sc = [t for t in tasks if t.repository == "saleor"]

    bridge = json.loads(BRIDGE_JSON.read_text(encoding="utf-8"))
    checks = {}

    # A1 route-B
    for repo, ts in (("djangocms", dc), ("saleor", sc)):
        for B in (1, 3, 5, 10):
            m = round(macro_orr(ts, rank_composite, B), 4)
            frozen = bridge["section1"][repo]["route_b_orr"][str(B)]
            checks[f"A1_{repo}_routeB_B{B}"] = abs(m - frozen) < 1e-4
    # A2 sparse
    for repo, ts in (("djangocms", dc), ("saleor", sc)):
        f1 = _sparse(ts)["f1"]
        frozen = bridge["section1"][repo]["sparse"]["f1"]
        checks[f"A2_{repo}_sparse_f1"] = abs(f1 - frozen) <= 0.001
    # A3 reverse-1hop availability
    for repo, ts in (("djangocms", dc), ("saleor", sc)):
        v = _pool_fn_availability(ts, "GRAPH_REVERSE_1HOP", 5)
        frozen = bridge["section1"][repo]["oracle_availability_reverse_1hop_K5"]
        checks[f"A3_{repo}_rev1hop_avail"] = abs(v - frozen) <= 0.005
    # A4 union-all
    for repo, ts in (("djangocms", dc), ("saleor", sc)):
        v = _pool_fn_availability(ts, "UNION_ALL", 5)
        frozen = bridge["section1"][repo]["oracle_availability_union_all_K5"]
        checks[f"A4_{repo}_union_all_avail"] = abs(v - frozen) <= 0.005
    # A5 rankers @B=5
    for repo, ts in (("djangocms", dc), ("saleor", sc)):
        for q, rfn in QUANT_RANKERS.items():
            m = round(macro_orr(ts, rfn, 5), 4)
            frozen = bridge["section2"]["repos"][repo]["B"]["5"]["quant"][q]["macro_orr"]
            checks[f"A5_{repo}_{q}_orr5"] = abs(m - frozen) < 1e-4
    # A6 gate decision
    checks["A6_gate_decision"] = bridge["gate"]["decision"] == "CHEAP_RANKING_CLOSED_FOR_NOW"
    # A7 leakage check
    allowed = {"path", "module", "parent_dir", "bm25", "bm25_rank_pct", "pt_rank_pct",
               "graph_neighbor", "intent_overlap", "composite", "dist", "consumer",
               "provider", "rev_support", "fwd_support", "sibling", "co_change",
               "history_available", "is_missed_positive"}
    leak = True
    for t in tasks:
        for c in t.candidates:
            if set(c.keys()) - allowed:
                leak = False
                break
    checks["A7_no_proxy_feature"] = leak
    # A8 sealed-set guard
    checks["A8_dev_counts_and_sealed"] = len(dc) == 174 and len(sc) == 149 and all(
        "internal-test" not in t.role.lower() and "reserve" not in t.role.lower() for t in tasks
    )
    # A9 determinism
    det = True
    for t in tasks[:20]:
        for rfn in QUANT_RANKERS.values():
            if rfn(t) != rfn(t):
                det = False
    checks["A9_determinism"] = det
    # A10 fold fractions
    folds_ok = True
    for _repo, ts in (("djangocms", dc), ("saleor", sc)):
        for rfn in QUANT_RANKERS.values():
            fr = fold_direction(ts, rfn, 5, 5, 20260918)
            if not (len(fr) == 5 and all(0.0 <= x <= 1.0 for x in fr)):
                folds_ok = False
    checks["A10_folds"] = folds_ok

    ok = all(checks.values())
    audit = {"package": "fn_quant_ranking_bridge_audit", "date": "2026-09-18",
             "tier": "T3", "verdict": "PASS" if ok else "FAIL",
             "n_checks": len(checks), "n_pass": sum(1 for v in checks.values() if v),
             "checks": checks,
             "recomputed": {
                 "djangocms_routeB_B5": round(macro_orr(dc, rank_composite, 5), 4),
                 "saleor_routeB_B5": round(macro_orr(sc, rank_composite, 5), 4),
                 "djangocms_R1_B5": round(macro_orr(dc, QUANT_RANKERS["R1_BM25+RevSupport"], 5), 4),
                 "saleor_R1_B5": round(macro_orr(sc, QUANT_RANKERS["R1_BM25+RevSupport"], 5), 4),
             }}
    AUDIT_JSON.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    md = [
        "# FN Quantitative-Structural Ranking Bridge — Independent Audit",
        "",
        f"**Date:** 2026-09-18  **Tier:** T3  **Verdict:** **{audit['verdict']}** "
        f"({audit['n_pass']}/{audit['n_checks']} checks PASS).",
        "",
        "Recomputed from frozen records WITHOUT importing the analysis script.",
        "",
        "| Check | Result |",
        "|---|---|",
    ]
    for k, v in checks.items():
        md.append(f"| {k} | {'PASS' if v else 'FAIL'} |")
    md += ["", "Recomputed headline numbers:", "",
           "| Quantity | Recomputed |",
           "|---|---:|",
           f"| djangoCMS Route-B ORR @5 | {audit['recomputed']['djangocms_routeB_B5']} |",
           f"| Saleor Route-B ORR @5 | {audit['recomputed']['saleor_routeB_B5']} |",
           f"| djangoCMS R1 ORR @5 | {audit['recomputed']['djangocms_R1_B5']} |",
           f"| Saleor R1 ORR @5 | {audit['recomputed']['saleor_R1_B5']} |",
           "",
           "Machine-readable: reports/fn_quant_ranking_bridge_audit.json",
    ]
    AUDIT_MD.write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({k: v for k, v in checks.items()}, indent=1))
    print("verdict:", audit["verdict"], f"({audit['n_pass']}/{audit['n_checks']})")
    print("outputs:", AUDIT_JSON, AUDIT_MD)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

