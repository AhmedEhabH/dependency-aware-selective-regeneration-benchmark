#!/usr/bin/env python3
"""Human minimal-spot-check form generator for the AI semantic audit (ZERO LLM).

Once the 10 rater batch outputs exist and
`scripts/semantic_ai_audit_agreement.py` has produced its analysis result JSON,
this generator builds `research/semantic_audit/ai_blinded_v1/human_spotcheck_form.csv`
containing:

- every inter-model disagreement (both rated, labels differ, or one abstained);
- the deterministic 10-row agreement sample (the spot-check seed is fixed).

The human task (documented in the form and the analysis protocol):
- review each row's packet evidence;
- record whether the packet evidence supports either / both / neither model label.

This is a MINIMAL human spot-check, NOT expert adjudication unless the reviewer
is documented as an expert.

Usage:
    python scripts/semantic_ai_audit_human_spotcheck.py <analysis_result.json>
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
OUT = PROJECT / "research" / "semantic_audit" / "ai_blinded_v1" / "human_spotcheck_form.csv"

FIELDNAMES = [
    "spot_check_kind",
    "neutral_case_id",
    "neutral_row_id",
    "semantic_role",
    "file_path",
    "chatgpt_label",
    "claude_label",
    "human_verdict",
    "notes",
]


def _row_meta(sealed: dict, neutral_row_id: str) -> dict:
    for ncid, cinfo in sealed["cases"].items():
        for r in cinfo["rows"]:
            if r["neutral_row_id"] == neutral_row_id:
                return {
                    "neutral_case_id": ncid,
                    "semantic_role": r["semantic_role"],
                    "file_path": r["file_path"],
                }
    return {"neutral_case_id": "", "semantic_role": "", "file_path": ""}


def generate(
    analysis_path: Path, sealed_path: Path | None = None, out_path: Path | None = None
) -> int:
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    if not sealed_path:
        sealed_path = Path(analysis.get("sealed_mapping_used", ""))
    sealed = json.loads(sealed_path.read_text(encoding="utf-8")) if sealed_path else {}

    rows_out = []
    # 1) disagreements
    for d in analysis.get("disagreements", []):
        meta = _row_meta(sealed, d["neutral_row_id"])
        rows_out.append(
            {
                "spot_check_kind": "disagreement",
                **meta,
                "neutral_row_id": d["neutral_row_id"],
                "chatgpt_label": d.get("chatgpt_label") or "(abstained)",
                "claude_label": d.get("claude_label") or "(abstained)",
                "human_verdict": "",
                "notes": "",
            }
        )
    # 2) deterministic agreement sample
    for nid in analysis.get("agreement_spotcheck_sample", []):
        meta = _row_meta(sealed, nid)
        rows_out.append(
            {
                "spot_check_kind": "agreement_sample",
                **meta,
                "neutral_row_id": nid,
                "chatgpt_label": "",
                "claude_label": "",
                "human_verdict": "",
                "notes": "",
            }
        )

    target = out_path or OUT
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows(rows_out)
    print("rows_written", len(rows_out))
    print("output:", target)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("analysis_result", type=Path, help="analysis JSON from semantic_ai_audit_agreement.py")
    parser.add_argument("--sealed", type=Path, default=None, help="sealed_mapping.json (default: from analysis)")
    parser.add_argument("--out", type=Path, default=None, help="output CSV (default: package human_spotcheck_form.csv)")
    args = parser.parse_args(argv)
    return generate(args.analysis_result, args.sealed, args.out)


if __name__ == "__main__":
    raise SystemExit(main())
