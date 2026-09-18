# ruff: noqa: E501
"""Section 1 — verify the confirmatory (spent djangoCMS INTERNAL_TEST) error budget.

POST-HOC ONLY. Recomputes Sparse baseline + verifier B=5 aggregates from frozen
records. Never used to select a method.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

RECORDS = PROJECT_DIR / "research" / "djangocms-confirmatory-route-b" / "run_records.jsonl"
LEDGER = PROJECT_DIR / "research" / "djangocms-confirmatory-route-b" / "confirmatory_metrics.json"
CURVE = PROJECT_DIR / "research" / "djangocms-confirmatory-route-b" / "curve_level_posthoc.json"


def load_records() -> list[dict]:
    out = []
    for line in RECORDS.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def first_succeeded_by_case(recs: list[dict]) -> dict[str, dict]:
    out = {}
    for r in recs:
        if r.get("terminal_status") == "succeeded" and r["case_id"] not in out:
            out[r["case_id"]] = r
    return out


def agg(rows: list[dict]) -> dict:
    tp = sum(r["tp"] for r in rows)
    fp = sum(r["fp"] for r in rows)
    fn = sum(r["fn"] for r in rows)
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": round(p, 4), "recall": round(r, 4), "f1": round(f1, 4), "n_positives": tp + fn}


def main() -> int:
    recs = load_records()
    print("total records:", len(recs))
    # arms present
    from collections import Counter

    print("arm counts:", dict(Counter(r.get("arm") for r in recs)))
    print("terminal status:", dict(Counter(r.get("terminal_status") for r in recs)))

    # Sparse baseline: first succeeded per case
    fs = first_succeeded_by_case(recs)
    print("\nn cases with a succeeded sparse rep:", len(fs))

    # The confirmatory run records include BOTH sparse first pass and verifier?
    # Check run_id / arm patterns.
    sparse_rows = [r for r in recs if (r.get("arm") or "").startswith("sparse") and r.get("terminal_status") == "succeeded"]
    print("succeeded sparse-arm records:", len(sparse_rows))

    # Ledger may hold the canonical aggregates
    led = json.loads(LEDGER.read_text(encoding="utf-8"))
    print("\nconfirmatory_ledger.json:", json.dumps(led, indent=1)[:800])
    metrics = json.loads((PROJECT_DIR / "research" / "djangocms-confirmatory-route-b" / "confirmatory_metrics.json").read_text(encoding="utf-8"))
    print("\nconfirmatory_metrics.json keys:", list(metrics.keys()))
    print(json.dumps(metrics, indent=1)[:1500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
