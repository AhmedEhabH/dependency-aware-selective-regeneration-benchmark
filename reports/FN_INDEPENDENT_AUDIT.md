# Independent Audit — FIRST-PASS RECALL BOTTLENECK

**Date:** 2026-09-18  **Tier:** T3 (ZERO API)  **Method:** direct recomputation
from frozen records + case bundles, WITHOUT importing the analysis scripts.

## Headline recomputation

| Metric | djangoCMS | Saleor |
|---|---:|---:|
| Sparse TP/FP/FN | 125/155/382 | 99/193/369 |
| Sparse F1 | 0.3177 | 0.2605 |
| FN universe | 382 | 369 |
| Route-B composite ORR @B=5 | 0.1633 | 0.2369 |

## Checks

| check | recomputed | persisted | match |
|---|---:|---:|---:|
| djangocms_sparse_tp | 125 | 125 | True |
| djangocms_sparse_fp | 155 | 155 | True |
| djangocms_sparse_fn | 382 | 382 | True |
| saleor_sparse_tp | 99 | 99 | True |
| saleor_sparse_fp | 193 | 193 | True |
| saleor_sparse_fn | 369 | 369 | True |
| djangocms_routeB_B5 | 0.1633 | 0.1633 | True |
| saleor_routeB_B5 | 0.2369 | 0.2369 | True |
| djangocms_fn_universe | 382 | 382 | True |
| saleor_fn_universe | 369 | 369 | True |
| djangocms_total_tasks | 174 | 174 | True |
| saleor_total_tasks | 149 | 149 | True |
| djangocms_dev_primary_sums_to_total | 382 | 382 | True |
| saleor_dev_primary_sums_to_total | 369 | 369 | True |
| djangocms_dev_bm25_ceil_gte_reverse1hop | 0.9293 | 0.5576 | True |
| saleor_dev_bm25_ceil_gte_reverse1hop | 0.8808 | 0.7236 | True |
| djangocms_dev_q3_naive_f1_lt_q1 | 0.1883 | 0.2269 | True |
| saleor_dev_q3_naive_f1_lt_q1 | 0.1409 | 0.2392 | True |
| dev_case_count | 323 | 323 | True |

**All checks PASS: True**

Machine-readable: reports/fn_independent_audit.json