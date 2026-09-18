# Precision-Safe Acceptance Pilot — Independent Audit

**Date:** 2026-09-18  **Tier:** T3  **Verdict:** **PASS** (11/11).

Recomputed from raw per-run records + recall data layer without importing the analyzer.

| Check | Result |
|---|---|
| A1_ledger_within_ceilings | PASS |
| A2_sidecars | PASS |
| A3_counts | PASS |
| A4_orr5_recompute | PASS |
| A5_decision | PASS |
| A5b_fail_points | PASS |
| A6_schema_rate | PASS |
| A6b_zero_partial_credit | PASS |
| A7_sealed_disjoint | PASS |
| A8_prompt_determinism | PASS |
| A10_f1_precision_protected | PASS |

Recomputed ORR@5:

| Repo | Arm A | Arm B |
|---|---:|---:|
| djangocms | 0.2225 | 0.1523 |
| saleor | 0.1278 | 0.2029 |

Machine-readable: reports/precision_safe_acceptance_audit.json