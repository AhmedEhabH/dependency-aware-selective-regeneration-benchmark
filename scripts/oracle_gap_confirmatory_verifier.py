# ruff: noqa: E501
#!/usr/bin/env python3
# ruff: noqa: E501
"""Confirmatory POST-HOC verifier loss numbers (spent djangoCMS INTERNAL_TEST).

Recomputes the verifier false-rejection / false-acceptance losses from frozen
records. POST-HOC only; never used for selection.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

RECORDS = PROJECT_DIR / "research" / "djangocms-confirmatory-route-b" / "run_records.jsonl"


def load() -> list[dict]:
    return [json.loads(line) for line in RECORDS.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    recs = load()
    sparse = [r for r in recs if r["arm"] == "sparse_v2" and r["terminal_status"] == "succeeded"]
    fs = {}
    for r in sparse:
        fs.setdefault(r["case_id"], r)
    ver5 = {r["case_id"]: r for r in recs if r["arm"] == "verifier" and r["B"] == 5}

    out = {"note": "POST-HOC confirmatory verifier decomposition (spent INTERNAL_TEST; not for selection)"}
    # composite-ranked recovery at B=5 (what the ranker offered the verifier)
    total_oracle_in_top5 = sum(v.get("oracle_recovered_in_top", 0) for v in ver5.values())
    total_verifier_recovered = sum(len(v.get("verifier_recovered", [])) for v in ver5.values())
    total_verifier_selected = sum(len(v.get("verifier_selected", [])) for v in ver5.values())
    # verifier false-acceptance: selected-but-not-recovered
    total_false_accepted = sum(
        len(set(v.get("verifier_selected", [])) - set(v.get("verifier_recovered", []))) for v in ver5.values()
    )
    # verifier false-rejection: oracle-in-top but not recovered
    total_false_rejected = 0
    for v in ver5.values():
        oracle_top = set(v.get("true_missed_in_top", []))
        recovered = set(v.get("verifier_recovered", []))
        total_false_rejected += len(oracle_top - recovered)

    out.update({
        "n_cases": len(ver5),
        "oracle_recovery_in_top5": total_oracle_in_top5,
        "composite_recovery_at_B5": 0,  # filled below
        "verifier_recovered_at_B5": total_verifier_recovered,
        "verifier_selected_at_B5": total_verifier_selected,
        "verifier_false_acceptance": total_false_accepted,
        "verifier_acceptance_precision": round(total_verifier_recovered / total_verifier_selected, 4) if total_verifier_selected else None,
        "verifier_false_rejection": total_false_rejected,
        "verifier_false_rejection_rate": round(total_false_rejected / total_oracle_in_top5, 4) if total_oracle_in_top5 else None,
    })
    (PROJECT_DIR / "reports" / "oracle_gap_confirmatory_verifier_posthoc.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
