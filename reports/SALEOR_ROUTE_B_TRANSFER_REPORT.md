# Saleor Route-B Transfer Replication

**Date:** 2026-09-17  **Repository:** Saleor  **N development tasks:** 149
TRANSFER TEST — frozen Route-B V2 protocol applied to Saleor DEVELOPMENT;
no tuning on Saleor outcomes; no method change in this block.

## Pooled omission recovery rate (macro ORR) by arm and B (Saleor, per-repository primary)

| B | Sparse/B0 | AnalyticRandom | BM25 | PathToken | Graph | CIA | Hybrid | Oracle | InspectAll |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 1 | 0.000 | 0.001 | 0.072 | 0.000 | 0.005 | 0.077 | 0.077 | 0.477 | 0.852 |
| 3 | 0.000 | 0.004 | 0.158 | 0.000 | 0.005 | 0.158 | 0.158 | 0.748 | 0.852 |
| 5 | 0.000 | 0.006 | 0.234 | 0.000 | 0.005 | 0.237 | 0.237 | 0.818 | 0.852 |
| 10 | 0.000 | 0.012 | 0.315 | 0.006 | 0.009 | 0.317 | 0.317 | 0.851 | 0.852 |

## Best predeclared arm vs analytic Random (bootstrap CI)

Best arm: **CIA** (mean curve delta vs random 0.1915).

| B | delta | 95% CI |
|---|---:|---:|
| 1 | +0.076 | [+0.044, +0.109] |
| 3 | +0.154 | [+0.110, +0.202] |
| 5 | +0.231 | [+0.180, +0.287] |
| 10 | +0.304 | [+0.243, +0.367] |

## Progression gate

- best arm: CIA
- folds with positive direction: 5/5 (majority: True)
- B-curve points above analytic Random: 4/4
- corr(omitted-size, delta) = -0.048
- corr(universe-size, delta) = -0.048
- gate PASS: **True**

## Transfer classification

**REPLICATES**

## Notes

- Per-repository primary (Saleor reported FIRST; no djangoCMS+Saleor pooling as the headline).
- Task = independent unit; 3 nested reps deduped by case_id (first succeeded rep).
- Analytic Random (hypergeometric expectation) is the control.
- Oracle@B = ranking headroom; InspectAll = exhaustive reconsideration.
- Full machine-readable results: research/transparency/saleor_route_b_transfer_results.json