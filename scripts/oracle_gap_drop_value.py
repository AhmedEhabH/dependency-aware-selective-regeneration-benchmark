# ruff: noqa: E501, N806
#!/usr/bin/env python3
# ruff: noqa: E501
"""Diagnostic — is the DROP side worth anything even under ORACLE review?

Compares, at matched total inspection budget K:
  - oracle add-only @A=K        (perfect adds, D=0)
  - oracle bidirectional (A,D)   (perfect adds + perfect drops, A+D=K)
  - oracle drop-only @D=K        (perfect drops, A=0)
over every split of K, on DEVELOPMENT. Determines whether bidirectional adds
value over add-only, and whether drop-only can rescue precision.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from scripts.oracle_gap_ceilings import oracle_add, oracle_bi, oracle_drop, per_task_counts  # noqa: E402
from scripts.oracle_gap_data import load_all  # noqa: E402

BUDGETS = (1, 2, 3, 5, 8, 10)


def main() -> int:
    tasks = load_all()
    dc = [t for t in tasks if t.repository == "djangocms"]
    sc = [t for t in tasks if t.repository == "saleor"]
    out = {"package": "oracle_gap_v1", "analysis_date": "2026-09-18", "tier": "T3",
           "note": "Matched-inspection comparison of oracle add-only vs bidirectional vs drop-only (DEVELOPMENT). INTERNAL_TEST unused.", "repos": {}}
    for name, ts in (("djangocms_dev", dc), ("saleor_dev", sc)):
        counts = per_task_counts(ts)
        rows = []
        for K in BUDGETS:
            add = oracle_add(counts, K)
            drop = oracle_drop(counts, K)
            best_bi = None
            best_f1 = -1
            for A in range(0, K + 1):
                D = K - A
                m = oracle_bi(counts, A, D)
                if m["f1"] > best_f1:
                    best_f1 = m["f1"]
                    best_bi = (A, D, m)
            rows.append({
                "K": K,
                "add_only_A=K": {"f1": add["f1"], "P": add["precision"], "R": add["recall"]},
                "drop_only_D=K": {"f1": drop["f1"], "P": drop["precision"], "R": drop["recall"]},
                "best_bidirectional": {"A": best_bi[0], "D": best_bi[1], "f1": best_bi[2]["f1"],
                                       "P": best_bi[2]["precision"], "R": best_bi[2]["recall"]},
                "bi_beats_add_only": best_f1 > add["f1"],
            })
        out["repos"][name] = rows
    (PROJECT_DIR / "reports" / "oracle_matched_budget_drop_value.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")
    for name in ("djangocms_dev", "saleor_dev"):
        print(f"\n=== {name} (matched inspection K) ===")
        for r in out["repos"][name]:
            a = r["add_only_A=K"]["f1"]
            d = r["drop_only_D=K"]["f1"]
            b = r["best_bidirectional"]
            print(f"  K={r['K']}: add-only F1={a} drop-only F1={d} best-bi(A={b['A']},D={b['D']}) F1={b['f1']} bi_beats_add={r['bi_beats_add_only']}")
    print("\noutput: reports/oracle_matched_budget_drop_value.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
