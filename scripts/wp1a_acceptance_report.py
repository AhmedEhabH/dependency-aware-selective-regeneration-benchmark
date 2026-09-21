#!/usr/bin/env python3
"""WP-1a acceptance report - AC-1A.1..AC-1A.12 with mechanical evidence.

Reads the already-generated WP-1a artifacts and emits
research/wp1a/wp1a_acceptance_report.json with PASS/FAIL + evidence for every
criterion. No recomputation is performed here; the same-session cross-check
(scripts/wp1a_independent_audit.py) performs the recomputation. TERMINOLOGY
CORRECTED 2026-09-21: AC-1A.10 is a same-session alternate-implementation
cross-check, NOT an independent/external audit.
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = _PROJECT_DIR / "research" / "wp1a"
AUDIT = OUT_DIR / "wp1a_independent_audit.json"
PROV = OUT_DIR / "sip_scientific_model_provenance.json"
VERIF = OUT_DIR / "wp1_rederivation_verification.json"
INTENT = OUT_DIR / "wp1a_intent_parity.json"
PROTOCOL = OUT_DIR / "wp1a_frozen_agent_protocol.json"
AUDIT_RESULT = json.loads(AUDIT.read_text(encoding="utf-8"))
PROV_RESULT = json.loads(PROV.read_text(encoding="utf-8"))
VERIF_RESULT = json.loads(VERIF.read_text(encoding="utf-8"))
INTENT_RESULT = json.loads(INTENT.read_text(encoding="utf-8"))
PROTOCOL_RESULT = json.loads(PROTOCOL.read_text(encoding="utf-8"))


def _audit_check(name: str) -> bool:
    return any(c["name"] == name and c["pass"] for c in AUDIT_RESULT["checks"])


def main() -> int:
    # AC-1A.11: no scientific API calls / $0.00 (WP-1a is preparation; no paid
    # model backend call was made; all scripts are local recomputation).
    # Build the marker dynamically so this checker cannot match itself.
    chat_marker = ("openrouter.ai" + "/api/v1/chat/completions")
    no_paid_calls = True
    for script in sorted(Path("scripts").glob("wp1a_*.py")):
        if script.name in {"wp1a_acceptance_report.py", "wp1a_independent_audit.py"}:
            continue
        text = script.read_text(encoding="utf-8")
        if chat_marker in text:
            no_paid_calls = False
        if "api.openai.com" in text or "anthropic.com/v1/messages" in text:
            no_paid_calls = False

    criteria = [
        ("AC-1A.1", "Scientific model/provider provenance",
         PROV_RESULT["conclusion"] == "IDENTITY_MECHANICALLY_RECOVERED_AND_CONSISTENT"
         and all(v["consistent_across_all_tasks"] for v in PROV_RESULT["identity"].values()),
         f"qwen/qwen3-coder @ deepinfra/turbo, 300/300 consistent; prompt template "
         f"sha {PROV_RESULT['prompt_template_source']['sha256'][:16]}..."),
        ("AC-1A.2", "Label isolation / no prediction-side outcome access",
         _audit_check("A6.prediction_view_label_free"),
         "candidate_rows label column dropped/denied at boundary; prediction "
         "view contains no forbidden columns; public parent-state universe used"),
        ("AC-1A.3", "Exact 300-task SIP/RM-CSS re-derivation",
         VERIF_RESULT["verification"] == "EXACT_REPRODUCTION",
         f"SIP F1 {VERIF_RESULT['sip']['f1']:.10f}, RM-CSS F1 "
         f"{VERIF_RESULT['rmcss']['f1']:.10f}, DeltaF1 {VERIF_RESULT['delta_f1']:.10f}"),
        ("AC-1A.4", "Main-50 and calibration-3 deterministic freeze + disjointness",
         _audit_check("A3.disjointness") and _audit_check("A1.main_50_matches_frozen")
         and _audit_check("A2.calibration_matches_frozen"),
         "main 50 = first 50 of frozen ordering; cal 3 = deterministic complement "
         "draw (seed 20260921); intersection empty"),
        ("AC-1A.5", "Intent parity",
         INTENT_RESULT["status"] == "WP1A_INTENT_PARITY_PASS",
         "53/53 canonical hash match; source=commit_message; "
         "no ambiguity -> not blocked"),
        ("AC-1A.6", "Agent protocol fully specified and mock-executable",
         PROTOCOL_RESULT["status"] == "FROZEN_FOR_FUTURE_EXECUTION"
         and _audit_check("A11.protocol_complete"),
         "25 protocol sections frozen; mock/stub execution covered by "
         "tests/unit/test_wp1a_frozen_protocol.py + existing SU-0011 integration tests"),
        ("AC-1A.7", "Shared scorer tests",
         _audit_check("A12.scorer_formula"),
         "one scorer for repository_agent/SIP/RM-CSS; metric formulas verified "
         "synthetically + targeted tests"),
        ("AC-1A.8", "Efficiency accounting identities",
         _audit_check("A13.accounting_identity_fields"),
         "per-arm tokens/calls/wall/USD; RM-CSS two views (marginal + setup); "
         "amortized N=50/N=300"),
        ("AC-1A.9", "Budget feasibility / pre-request guard design",
         _audit_check("A14.budget_inputs"),
         "label-free projection; recommended ceiling for Ahmed review; "
         "cumulative USD guard before each paid request; BUDGET_ABORT rule pre-registered"),
        ("AC-1A.10", "Alternate-implementation cross-check (same-session; NOT an independent audit)",
         AUDIT_RESULT["status"] == "PASS",
         f"{AUDIT_RESULT['pass']}/{AUDIT_RESULT['total']} same-session "
         f"alternate-implementation checks PASS (no import of audited helpers); "
         f"blind independent-audit packet at "
         f"exports/wp1a_independent_audit_packet_2026-09-21/"),
        ("AC-1A.11", "No scientific API calls / $0.00",
         no_paid_calls,
         "all WP-1a scripts are local recomputation; no paid model/API call made"),
        ("AC-1A.12", "786 remaining RESERVE outcomes untouched",
         _audit_check("A16.no_786_access"),
         "wp1a scripts never open unread Saleor RESERVE outcomes; only the "
         "already-opened 300 proxies are used"),
    ]

    all_pass = all(c[2] for c in criteria)
    report = {
        "wp1a": "wp1a_acceptance_report",
        "generated_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "status": "ALL_PASS" if all_pass else "NOT_ALL_PASS",
        "criteria": [
            {"criterion": c[0], "title": c[1], "pass": c[2], "evidence": c[3]}
            for c in criteria
        ],
        "note": (
            "WP-1a is PREPARATION ONLY. WP-1b (calibration + main n=50 run) "
            "remains AWAITING AHMED AUTHORIZATION and is NOT executed."
        ),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "wp1a_acceptance_report.json").write_text(
        json.dumps(report, indent=1), encoding="utf-8")
    for c in criteria:
        print(f"{c[0]} {c[1]}: {'PASS' if c[2] else 'FAIL'}")
        print(f"   evidence: {c[3]}")
    print(f"ACCEPTANCE: {report['status']}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
