"""Verify Omission-Risk Feature Study V1: six gates + independent audit.

Persists the gate results to reports/omission_risk_feature_study_v1_gates.json
and prints the summary. Deterministic, ZERO API.
"""

from __future__ import annotations

import json
from pathlib import Path

from benchmark.omission_risk import gates


def main() -> int:
    gate_results = gates.run_six_gates()
    audit = gates.audit_checks()
    payload = {
        "study_id": "OMISSION_RISK_FEATURE_STUDY_V1",
        "model": "openrouter/deepseek/deepseek-v4-flash-0731",
        "date": "2026-09-16",
        "gates": gate_results,
        "audit": audit,
        "all_gates_pass": gates.all_gates_pass(gate_results),
        "audit_pass": audit["passed"],
        "zero_llm_calls": True,
    }
    out = Path("reports/omission_risk_feature_study_v1_gates.json")
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    for g in gate_results:
        n_ok = sum(1 for c in g["checks"] if c["ok"])
        print(f"Gate {g['gate']} {g['name']}: PASS={g['passed']} ({n_ok}/{len(g['checks'])})")
    print("AUDIT:", audit["passed"], f"({sum(1 for c in audit['checks'] if c['ok'])}/{len(audit['checks'])})")
    print("ALL_GATES_PASS:", gates.all_gates_pass(gate_results))
    return 0 if (gates.all_gates_pass(gate_results) and audit["passed"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
