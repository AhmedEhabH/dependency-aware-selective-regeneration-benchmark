# Route B — Curve-Level Post-Hoc Characterization (POST-HOC, NOT preregistered)

**Date:** 2026-09-18  **Data:** djangoCMS V2 INTERNAL_TEST (80 tasks, authorized)
**Type:** POST-HOC / SENSITIVITY summary of the FROZEN confirmatory result.
**This does NOT retroactively redefine the preregistered primary endpoint; the frozen
decision (CONFIRMS) is unchanged.** Task = independent unit.

## 1. Denominator handling (explicit)

- Total tasks: **80**
- Tasks with zero Sparse FNs (M=0): **10** (12.5%) —
  the frozen macro ORR mean includes these tasks as 0.0 (same rule as the frozen
  confirmatory report). A positive-denominator-only sensitivity is reported as well.
- Tasks with a positive denominator (M>0): **70**

## 2. ORR @ B — macro (frozen rule) and micro (all tasks) + positive-only sensitivity

| B | arm | macro frozen (all 80) | macro positive-only | micro (all) | p5 | p25 | p50 | p75 | p95 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | Composite | 0.0591 | 0.0675 | 0.0503 | 0.0 | 0.0 | 0.0 | 0.0 | 0.5 |
| 1 | Verifier | 0.0294 | 0.0336 | 0.0251 | 0.0 | 0.0 | 0.0 | 0.0 | 0.1825 |
| 1 | AnalyticRandom | 0.0055 | 0.0063 | 0.0062 | 0.0043 | 0.0065 | 0.0068 | 0.007 | 0.0073 |
| 3 | Composite | 0.1098 | 0.1255 | 0.1156 | 0.0 | 0.0 | 0.0 | 0.125 | 0.5 |
| 3 | Verifier | 0.0632 | 0.0723 | 0.0603 | 0.0 | 0.0 | 0.0 | 0.0 | 0.5 |
| 3 | AnalyticRandom | 0.0166 | 0.019 | 0.0187 | 0.0129 | 0.0196 | 0.0204 | 0.0211 | 0.0218 |
| 5 | Composite | 0.165 | 0.1886 | 0.1759 | 0.0 | 0.0 | 0.0 | 0.3125 | 1.0 |
| 5 | Verifier | 0.1007 | 0.1151 | 0.1005 | 0.0 | 0.0 | 0.0 | 0.0 | 0.775 |
| 5 | AnalyticRandom | 0.0277 | 0.0317 | 0.0312 | 0.0215 | 0.0327 | 0.034 | 0.0352 | 0.0364 |
| 10 | Composite | 0.2669 | 0.305 | 0.3015 | 0.0 | 0.0 | 0.1833 | 0.5 | 1.0 |
| 10 | Verifier | 0.1793 | 0.2049 | 0.201 | 0.0 | 0.0 | 0.0 | 0.3646 | 1.0 |
| 10 | AnalyticRandom | 0.0554 | 0.0633 | 0.0625 | 0.0429 | 0.0655 | 0.068 | 0.0704 | 0.0728 |

## 3. AURC — area under ORR-vs-budget curve (B grid {0,1,3,5,10})

Normalized by the budget range (ceiling = 1.0). POST-HOC summary metric.

| arm | AURC (normalized) |
|---|---:|
| composite | 0.1553 |
| verifier | 0.0971 |
| analytic_random | 0.0277 |

## 4. Simultaneous + pointwise task-bootstrap band (B in {1,3,5,10})

- 4000 resamples of the frozen task unit (each task contributes its full B-curve).

| B | composite mean | pointwise CI95 | simultaneous band | verifier mean | verifier sim band |
|---|---:|---:|---:|---:|---:|
| 1 | 0.0591 | [0.0216, 0.1044] | [-0.0169, 0.1361] | 0.0294 | [-0.0376, 0.0969] |
| 3 | 0.1098 | [0.0615, 0.166] | [0.0339, 0.1869] | 0.0632 | [-0.0035, 0.131] |
| 5 | 0.165 | [0.1036, 0.2365] | [0.0893, 0.2423] | 0.1007 | [0.0341, 0.1685] |
| 10 | 0.2669 | [0.1964, 0.3421] | [0.1907, 0.3438] | 0.1793 | [0.1126, 0.2471] |

## 5. Interpretation (post-hoc, not a gate)

- AURC captures recovery across the whole budget curve, not a single B; the composite
  AURC is the area-based summary of the same ranked-recovery advantage.
- The simultaneous band is wider than pointwise bands because it holds coverage
  across ALL B jointly; pointwise CIs are shown for direct comparison with the
  frozen confirmatory intervals.
- The verifier AURC lies below the composite AURC because the verifier accepts only a
  subset of the top-B ranking, matching the frozen confirmatory report (verifier ORR
  < composite ORR at every B).
- Zero-FN tasks are 0 by definition; excluding them from the mean is the frozen
  denominator rule (documented, not a silent substitution).

Machine-readable: research/djangocms-confirmatory-route-b/curve_level_posthoc.json