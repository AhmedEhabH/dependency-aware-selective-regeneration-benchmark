# Route B V2 — Robustness Closure (DEVELOPMENT only)

**Date:** 2026-09-17  **N development tasks:** 174
Analytic Random (hypergeometric expectation); budget curve B in {0,1,3,5,10}.

## Pooled omission recovery rate (macro ORR) by arm and B

| B | Sparse/B0 | AnalyticRandom | BM25 | PathToken | Graph | CIA | Hybrid | Oracle | InspectAll |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 1 | 0.000 | 0.006 | 0.046 | 0.002 | 0.005 | 0.046 | 0.046 | 0.509 | 0.879 |
| 3 | 0.000 | 0.017 | 0.113 | 0.003 | 0.052 | 0.118 | 0.118 | 0.815 | 0.879 |
| 5 | 0.000 | 0.028 | 0.161 | 0.003 | 0.089 | 0.163 | 0.163 | 0.858 | 0.879 |
| 10 | 0.000 | 0.057 | 0.226 | 0.006 | 0.148 | 0.251 | 0.251 | 0.879 | 0.879 |

## Best predeclared arm vs analytic Random (bootstrap CI)

Best arm: **CIA** (mean curve delta vs random 0.1178).

| B | delta | 95% CI |
|---|---:|---:|
| 1 | +0.041 | [+0.018, +0.069] |
| 3 | +0.100 | [+0.062, +0.142] |
| 5 | +0.136 | [+0.092, +0.184] |
| 10 | +0.194 | [+0.147, +0.246] |

## Progression gate

- best arm: CIA
- folds with positive direction: 5/5 (majority: True)
- B-curve points above analytic Random: 4/4
- corr(omitted-size, delta) = -0.119
- corr(universe-size, delta) = -0.117
- gate PASS: **True**

## Notes

- DEVELOPMENT only; DEV_VALIDATION was already inspected in V1 and is NOT a confirmatory set.
- Analytic Random (hypergeometric expectation) is the control for ranking-only arms.
- Oracle@B is ranking headroom; InspectAll is exhaustive reconsideration.
- Full machine-readable results: research/transparency/route_b_v2_results.json