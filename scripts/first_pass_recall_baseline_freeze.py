#!/usr/bin/env python3
# ruff: noqa: E501
"""FIRST-PASS RECALL — Section 1: baseline freeze + FN universe (DEVELOPMENT only).

Recomputes from frozen artifacts (ZERO API):
- Sparse TP/FP/FN/P/R/F1 per repo (djangoCMS DEV 174, Saleor DEV 149);
- Route-B fixed-B composite metrics (B in {1,3,5,10});
- per-task Sparse FN file sets, per-task candidate universe, per-task observed
  proxy set.

Verifies the known aggregate diagnostic (djangoCMS FN=382, Saleor FN=369).

Outputs:
- reports/FIRST_PASS_RECALL_BASELINE_FREEZE.md
- reports/first_pass_recall_baseline_freeze.json
- research/first-pass-recall-bottleneck/fn_universe.json (per-task FN sets)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PROJECT_DIR / "src"))

from benchmark.recall.data import aggregate_tp_fp_fn, load_dev_tasks  # noqa: E402
from benchmark.recall.rankers import composite_recovery  # noqa: E402

OUT_MD = PROJECT_DIR / "reports" / "FIRST_PASS_RECALL_BASELINE_FREEZE.md"
OUT_JSON = PROJECT_DIR / "reports" / "first_pass_recall_baseline_freeze.json"
OUT_FN = PROJECT_DIR / "research" / "first-pass-recall-bottleneck" / "fn_universe.json"

KNOWN = {"djangocms": 382, "saleor": 369}


def main() -> int:
    tasks = load_dev_tasks()
    dc = [t for t in tasks if t.repository == "djangocms"]
    sc = [t for t in tasks if t.repository == "saleor"]

    result: dict = {
        "package": "first_pass_recall_baseline_freeze",
        "date": "2026-09-18",
        "tier": "T3",
        "note": "DEVELOPMENT only (djangoCMS DEV 174 + Saleor DEV 149). ZERO API. Frozen artifacts only.",
        "repos": {},
    }
    fn_universe: dict = {}
    for name, ts in (("djangocms", dc), ("saleor", sc)):
        sparse = aggregate_tp_fp_fn(ts)
        route_b = {f"B{B}": composite_recovery(ts, B) for B in (1, 3, 5, 10)}
        per_task = []
        for t in ts:
            per_task.append(
                {
                    "case_id": t.case_id,
                    "role": t.role,
                    "year": t.year,
                    "tp": len(t.write_set & t.proxy),
                    "fp": len(t.write_set - t.proxy),
                    "fn": len(t.proxy - t.write_set),
                    "proxy_size": len(t.proxy),
                    "write_set_size": len(t.write_set),
                    "universe_size": t.universe_size,
                    "omitted_size": t.omitted_size,
                    "n_missed": t.n_missed,
                    "fn_paths": list(t.fn_paths),
                    "proxy_paths": sorted(t.proxy),
                }
            )
        known = KNOWN[name]
        verified = sparse["fn"] == known
        result["repos"][name] = {
            "n_tasks": len(ts),
            "sparse_baseline": sparse,
            "route_b_fixed_b_composite": route_b,
            "fn_matches_known_diagnostic": verified,
            "known_fn": known,
            "per_task": per_task,
        }
        fn_universe[name] = {t.case_id: list(t.fn_paths) for t in ts}

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")
    OUT_FN.write_text(json.dumps(fn_universe, indent=1), encoding="utf-8")

    md = [
        "# First-Pass Recall Baseline Freeze",
        "",
        "**Date:** 2026-09-18  **Tier:** T3 (ZERO API, ZERO model calls)",
        "**Data:** djangoCMS DEVELOPMENT (174) + Saleor DEVELOPMENT (149), frozen artifacts only.",
        "",
        "## 1. Sparse baseline per repo (first-succeeded-rep write set)",
        "",
        "| Repo | n | TP | FP | FN | P | R | F1 | FNR |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in ("djangocms", "saleor"):
        s = result["repos"][name]["sparse_baseline"]
        md.append(
            f"| {name} DEV | {s['n_tasks']} | {s['tp']} | {s['fp']} | {s['fn']} "
            f"| {s['precision']:.4f} | {s['recall']:.4f} | {s['f1']:.4f} | {s['fnr']:.4f} |"
        )
    md += [
        "",
        "Known-diagnostic verification (FN):",
    ]
    for name in ("djangocms", "saleor"):
        r = result["repos"][name]
        md.append(
            f"- {name}: recomputed FN **{r['sparse_baseline']['fn']}** vs known "
            f"**{r['known_fn']}** -> {'MATCH' if r['fn_matches_known_diagnostic'] else 'DIFFERS'}."
        )
    md += [
        "",
        "## 2. Route-B fixed-B composite (macro ORR)",
        "",
        "| Repo | B=1 | B=3 | B=5 | B=10 |",
        "|---|---:|---:|---:|---:|",
    ]
    for name in ("djangocms", "saleor"):
        rb = result["repos"][name]["route_b_fixed_b_composite"]
        md.append(
            f"| {name} | {rb['B1']['macro_orr']:.4f} | {rb['B3']['macro_orr']:.4f} "
            f"| {rb['B5']['macro_orr']:.4f} | {rb['B10']['macro_orr']:.4f} |"
        )
    md += [
        "",
        "## 3. Per-task FN universe",
        "",
        "Per-task FN file sets, candidate universes, and proxy sets are persisted in "
        "`reports/first_pass_recall_baseline_freeze.json` and "
        "`research/first-pass-recall-bottleneck/fn_universe.json`.",
        "",
        "## 4. Notes",
        "",
        "- First-succeeded-rep write set is the frozen Sparse first pass.",
        "- The hidden proxy identifies FN files ONLY after the fact (evaluation-only).",
        "- No INTERNAL_TEST / RESERVE set is loaded.",
    ]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    for name in ("djangocms", "saleor"):
        s = result["repos"][name]["sparse_baseline"]
        rb = result["repos"][name]["route_b_fixed_b_composite"]
        print(name, "sparse", s["tp"], s["fp"], s["fn"], "P", round(s["precision"], 4), "R", round(s["recall"], 4), "F1", round(s["f1"], 4))
        print(name, "routeb", {B: rb[f"B{B}"]["macro_orr"] for B in (1, 3, 5, 10)})
    print("outputs:", OUT_MD, OUT_JSON, OUT_FN)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
