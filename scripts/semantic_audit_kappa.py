#!/usr/bin/env python3
"""Semantic-proxy two-rater agreement: Cohen's kappa + raw agreement + sensitivity.

Reads two filled rater forms (CSV) with the same item ordering (blinded order),
computes:
- per-file raw agreement (fraction of items where both raters assign the same
  category);
- Cohen's kappa (sklearn.metrics.cohen_kappa_score);
- sensitivity analysis treating '2_related_optional' as positive vs negative:
  agreement and kappa under that recoding.

No human judgments are fabricated here; this script consumes only files a human
has filled. INTERNAL_TEST/RESERVE are never opened.

Usage:
    python scripts/semantic_audit_kappa.py rater_form_A_filled.csv rater_form_B_filled.csv
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
OUT = PROJECT / "research" / "semantic_audit"


def load_ratings(path: Path) -> dict[str, str]:
    ratings = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ratings[(row["case_id"], row["item_index"])] = (row.get("rater_category") or "").strip()
    return ratings


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: semantic_audit_kappa.py <raterA.csv> <raterB.csv>")
        return 2
    a = load_ratings(Path(sys.argv[1]))
    b = load_ratings(Path(sys.argv[2]))
    keys = sorted(a.keys() & b.keys())
    if not keys:
        print("no matched items")
        return 2
    cat_a = [a[k] for k in keys]
    cat_b = [b[k] for k in keys]

    from sklearn.metrics import cohen_kappa_score

    raw_agree = sum(1 for x, y in zip(cat_a, cat_b, strict=True) if x == y) / len(keys)
    kappa = float(cohen_kappa_score(cat_a, cat_b))

    # Sensitivity: recode to binary where 1_required is always positive and
    # 2_related_optional is counted positive or negative per the flag.
    def recode(vals, optional_positive):
        out = []
        for v in vals:
            if v == "1_required":
                out.append(1)
            elif v == "2_related_optional":
                out.append(1 if optional_positive else 0)
            else:  # 3_incidental / 4_not_determinable / empty
                out.append(0)
        return out

    sens_neg = recode(cat_a, False)
    sens_neg_b = recode(cat_b, False)
    sens_pos = recode(cat_a, True)
    sens_pos_b = recode(cat_b, True)
    agree_neg = sum(1 for x, y in zip(sens_neg, sens_neg_b, strict=True) if x == y) / len(keys)
    agree_pos = sum(1 for x, y in zip(sens_pos, sens_pos_b, strict=True) if x == y) / len(keys)
    kappa_neg = float(cohen_kappa_score(sens_neg, sens_neg_b))
    kappa_pos = float(cohen_kappa_score(sens_pos, sens_pos_b))

    result = {
        "n_items": len(keys),
        "n_cases": len({k[0] for k in keys}),
        "raw_agreement": round(raw_agree, 4),
        "cohen_kappa": round(kappa, 4),
        "sensitivity_related_as_negative": {
            "raw_agreement": round(agree_neg, 4),
            "cohen_kappa": round(kappa_neg, 4),
        },
        "sensitivity_related_as_positive": {
            "raw_agreement": round(agree_pos, 4),
            "cohen_kappa": round(kappa_pos, 4),
        },
        "note": "Consumes only human-filled forms; no judgments fabricated.",
    }
    (OUT / "kappa_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    print("output:", OUT / "kappa_result.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
