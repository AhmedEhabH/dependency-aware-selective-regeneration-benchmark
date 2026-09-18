# Bounded Semantic Expansion Pilot — Independent Audit

**Date:** 2026-09-18  **Tier:** T3  **Verdict:** **PASS** (8/8).

Recomputed from raw per-run records + recall data layer without importing the analyzer.

| Check | Result |
|---|---|
| A1_ledger_within_ceilings | PASS |
| A2_sidecars | PASS |
| A3_counts | PASS |
| A4_orr_recompute | PASS |
| A5_decision | PASS |
| A6_gate_fail_points | PASS |
| A7_sealed | PASS |
| A8_no_prompt_leak | PASS |

Recomputed ORR@5:

| Repo | Arm A | Arm B |
|---|---:|---:|
| djangocms | 0.1111 | 0.25 |
| saleor | 0.3344 | 0.3574 |

Machine-readable: reports/bounded_semantic_expansion_audit.json