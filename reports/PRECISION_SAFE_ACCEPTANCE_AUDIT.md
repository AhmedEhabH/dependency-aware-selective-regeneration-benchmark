# Precision-Safe Acceptance Feasibility — Independent Audit

**Date:** 2026-09-18  **Tier:** T3 (zero-API)  **Verdict:** **PASS** (11/11).

Recomputed from raw Stage-4 per-run records + frozen registration + recall data layer,
without importing `scripts/precision_safe_feasibility_anatomy.py`.

| Check | Result |
|---|---|
| A1_stage4_evidence | PASS |
| A2_orr5_matches_frozen | PASS |
| A3_source_split_b5 | PASS |
| A4_cap_loss | PASS |
| A5_rule_K5_recompute | PASS |
| A6_matched_subset | PASS |
| A7_b10_saleor_folds | PASS |
| A8_sealed | PASS |
| A9_schema_taxonomy | PASS |
| A10_prompt_determinism | PASS |
| A11_fresh_sample_available | PASS |

Recomputed headline numbers:

- Frozen ORR@5: {'djangocms': {'arm_a': 0.1111, 'arm_b': 0.25}, 'saleor': {'arm_a': 0.3344, 'arm_b': 0.3574}}
- B=5 source split: {'djangocms': {'fn_route_b_top10': 7, 'fn_consumer_only': 4, 'fp_route_b_top10': 62, 'fp_consumer_only': 45}, 'saleor': {'fn_route_b_top10': 19, 'fn_consumer_only': 4, 'fp_route_b_top10': 66, 'fp_consumer_only': 41}}
- Cap loss (C=40): {'djangocms': {'total_fn': 61, 'fn_in_capped': 32, 'fn_lost_by_cap': 10}, 'saleor': {'total_fn': 85, 'fn_in_capped': 46, 'fn_lost_by_cap': 29}}
- Feasibility rule K=5: {'djangocms': {'candidate_precision': 0.1458, 'naive_union_f1': 0.4068}, 'saleor': {'candidate_precision': 0.2222, 'naive_union_f1': 0.2626}}

Machine-readable: reports/precision_safe_feasibility_audit.json