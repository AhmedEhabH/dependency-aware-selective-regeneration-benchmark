# ruff: noqa: E501
#!/usr/bin/env python3
# ruff: noqa: E501
"""Section 3 (quantified) — contribution of each loss to final F1 loss.

Decomposition in F1 terms on DEVELOPMENT:
  1. FIRST-PASS RECALL LOSS
  2. FIRST-PASS PRECISION LOSS
  3. RANKING LOSS
  4. VERIFIER FALSE-REJECTION LOSS  (POST-HOC; confirmatory only)
  5. VERIFIER FALSE-ACCEPTANCE LOSS (POST-HOC; confirmatory only)
  6. BUDGET LOSS

Final F1 = F1(Sparse) after the actual Route-B add-only correction.
We report F1 deltas against idealized corrections to show what dominates.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from scripts.oracle_gap_ceilings import (  # noqa: E402
    _metrics,
    oracle_add,
    oracle_drop,
    per_task_counts,
    route_b_add_only,
)
from scripts.oracle_gap_data import load_all  # noqa: E402


def main() -> int:
    tasks = load_all()
    dc = [t for t in tasks if t.repository == "djangocms"]
    sc = [t for t in tasks if t.repository == "saleor"]
    out = {"package": "oracle_gap_v1", "analysis_date": "2026-09-18", "tier": "T3",
           "note": "DEVELOPMENT F1-loss decomposition. Verifier losses (4/5) exist only for the spent INTERNAL_TEST -> reported POST-HOC in the report.",
           "repos": {}}
    for name, ts in (("djangocms_dev", dc), ("saleor_dev", sc)):
        counts = per_task_counts(ts)
        sparse_tp = sum(c["tp"] for c in counts)
        sparse_fp = sum(c["fp"] for c in counts)
        sparse_fn = sum(c["fn"] for c in counts)
        sparse = _metrics(sparse_tp, sparse_fp, sparse_fn)
        routeb5 = route_b_add_only(ts, 5)
        oracle_add_all = oracle_add(counts, None)
        oracle_drop_all = oracle_drop(counts, None)
        oracle_add(counts, None)
        out["repos"][name] = {
            "sparse_f1": sparse["f1"],
            "route_b_add_only_B5_f1": routeb5["f1"],
            "route_b_B5_f1_delta_vs_sparse": round(routeb5["f1"] - sparse["f1"], 4),
            "oracle_add_all_f1": oracle_add_all["f1"],
            "oracle_drop_all_f1": oracle_drop_all["f1"],
            "first_pass_recall_loss_F1_delta_to_oracle_add": round(oracle_add_all["f1"] - sparse["f1"], 4),
            "first_pass_precision_loss_F1_delta_to_oracle_drop": round(oracle_drop_all["f1"] - sparse["f1"], 4),
            "ranking_loss_at_B5": (lambda: (lambda o, c: {"oracle_recovery": o, "composite_recovery": c, "loss": o - c})(
                sum(min(5, sum(1 for cc in t.candidates if cc["is_missed_positive"])) for t in ts),
                sum(1 for t in ts for cc in sorted([c for c in t.candidates if c["path"] not in t.write_set], key=lambda c: (-c["composite"], c["path"]))[:5] if cc["is_missed_positive"])
            ))(),
        }
    (PROJECT_DIR / "reports" / "oracle_gap_decomposition_f1.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")
    for name in ("djangocms_dev", "saleor_dev"):
        r = out["repos"][name]
        print(f"\n=== {name} ===")
        print("Sparse F1:", r["sparse_f1"])
        print("Route-B add-only B=5 F1:", r["route_b_add_only_B5_f1"], f"(delta {r['route_b_B5_f1_delta_vs_sparse']})")
        print("Oracle-Add ALL F1:", r["oracle_add_all_f1"], f"(recall-loss delta {r['first_pass_recall_loss_F1_delta_to_oracle_add']})")
        print("Oracle-Drop ALL F1:", r["oracle_drop_all_f1"], f"(precision-loss delta {r['first_pass_precision_loss_F1_delta_to_oracle_drop']})")
        print("Ranking loss@B5:", r["ranking_loss_at_B5"])
    print("\noutput: reports/oracle_gap_decomposition_f1.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
