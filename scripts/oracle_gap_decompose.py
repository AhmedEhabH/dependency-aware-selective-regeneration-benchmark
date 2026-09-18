# ruff: noqa: E501, N803
#!/usr/bin/env python3
# ruff: noqa: E501
"""Section 3 — Oracle-gap decomposition per repo (DEVELOPMENT).

Quantifies where file-level quality is lost:
  1. FIRST-PASS RECALL LOSS  : Sparse FN / total positives
  2. FIRST-PASS PRECISION LOSS: Sparse FP / predicted positives
  3. RANKING LOSS            : Oracle-Add@B recovery minus actual composite@B recovery
  4. VERIFIER FALSE-REJECTION: (confirmatory POST-HOC only; no verifier calls on DEV)
  5. VERIFIER FALSE-ACCEPTANCE: (confirmatory POST-HOC only)
  6. BUDGET LOSS             : TP outside top-B even under perfect ranking

Frozen confirmatory (INTERNAL_TEST) verifier losses are reported separately as
POST-HOC. ZERO API. Tier T3.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from scripts.oracle_gap_data import load_all  # noqa: E402


def decompose(tasks) -> dict:
    tp = fp = fn = 0
    for t in tasks:
        pred = t.write_set
        pos = t.proxy
        tp += len(pred & pos)
        fp += len(pred - pos)
        fn += len(pos - pred)
    n_pos = tp + fn
    n_pred = tp + fp
    return {
        "n_tasks": len(tasks),
        "tp": tp, "fp": fp, "fn": fn, "n_positives": n_pos, "n_predicted": n_pred,
        "first_pass_recall_loss": round(fn / n_pos, 4) if n_pos else 0.0,
        "first_pass_precision_loss": round(fp / n_pred, 4) if n_pred else 0.0,
        "recall": round(tp / n_pos, 4) if n_pos else 0.0,
        "precision": round(tp / n_pred, 4) if n_pred else 0.0,
    }


def ranking_loss(tasks, B: int) -> dict:
    """Oracle-Add@B (perfect) recovery minus composite-ranked@B recovery."""
    oracle_rec = add_recovery(tasks, B)
    composite_rec = composite_recovery(tasks, B)
    return {
        "B": B,
        "oracle_add_recovery": oracle_rec,
        "composite_recovery": composite_rec,
        "ranking_loss": oracle_rec - composite_rec,
    }


def add_recovery(tasks, B: int) -> int:
    tot = 0
    for t in tasks:
        n_missed = sum(1 for c in t.candidates if c["is_missed_positive"])
        tot += min(B, n_missed)
    return tot


def composite_recovery(tasks, B: int) -> int:
    tot = 0
    for t in tasks:
        omitted = [c for c in t.candidates if c["path"] not in t.write_set]
        omitted.sort(key=lambda c: (-c["composite"], c["path"]))
        top = {c["path"] for c in omitted[:B]}
        tot += sum(1 for c in omitted if c["path"] in top and c["is_missed_positive"])
    return tot


def budget_loss(tasks, B: int) -> int:
    """True positives outside top-B even under perfect ranking."""
    tot = 0
    for t in tasks:
        n_missed = sum(1 for c in t.candidates if c["is_missed_positive"])
        tot += max(0, n_missed - min(B, n_missed))
    return tot


def main() -> int:
    tasks = load_all()
    dc = [t for t in tasks if t.repository == "djangocms"]
    sc = [t for t in tasks if t.repository == "saleor"]
    out = {"package": "oracle_gap_v1", "analysis_date": "2026-09-18", "tier": "T3",
           "note": "DEVELOPMENT error decomposition. Verifier components (4/5) only exist for the spent INTERNAL_TEST and are reported POST-HOC in the report.",
           "repos": {}}
    for name, ts in (("djangocms_dev", dc), ("saleor_dev", sc)):
        comp = decompose(ts)
        comp["ranking_loss_B5"] = ranking_loss(ts, 5)
        comp["ranking_loss_B10"] = ranking_loss(ts, 10)
        comp["budget_loss_B5"] = budget_loss(ts, 5)
        comp["budget_loss_B10"] = budget_loss(ts, 10)
        out["repos"][name] = comp

    (PROJECT_DIR / "reports" / "oracle_gap_decomposition.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")
    for name in ("djangocms_dev", "saleor_dev"):
        c = out["repos"][name]
        print(f"\n=== {name} ===")
        print("tp/fp/fn:", c["tp"], c["fp"], c["fn"], "| P,R:", c["precision"], c["recall"])
        print("first-pass recall loss:", c["first_pass_recall_loss"])
        print("first-pass precision loss:", c["first_pass_precision_loss"])
        print("ranking_loss@B5:", c["ranking_loss_B5"])
        print("ranking_loss@B10:", c["ranking_loss_B10"])
        print("budget_loss@B5:", c["budget_loss_B5"], " budget_loss@B10:", c["budget_loss_B10"])
    print("\noutput: reports/oracle_gap_decomposition.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
