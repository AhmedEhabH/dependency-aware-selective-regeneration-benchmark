# WP-2 Power and Assay-Sensitivity Planning (2026-09-22)

Status: ZERO-API planning only. **No final NI margin and no final Research Run
n are chosen here.** Numeric scenarios computed with a fixed seed
(`scripts/wp2_power_scenarios.py` → `research/wp2/wp2_power_scenarios_2026-09-22.json`).

## Confirmed oracle pool (measured by Oracle Confirmation, fixed harness)

- primary behavioral F2P eligible: **8**
- extended F2P (behavioral + symbol-absence): **9**
- environment-valid tasks: **13**
- attempted changed-test candidates: **220 / 220**

Decision: `WP2_F2P_POOL_SMALL` — primary behavioral n = 8 < 60 after exhausting
all 220 changed-test candidates.

## Paired binary power under effect-size scenarios (n = 8)

| True difference | Simulated one-sided paired power |
|---|---:|
| 5 pp | 0.081 |
| 10 pp | 0.115 |
| 15 pp | 0.154 |
| 20 pp | 0.200 |

At n = 8, even a 20pp true difference has only ~20% power: the confirmed pool
is far too small for a powered selector comparison. This is expected and is
exactly why the plan targets estimation-first alternatives.

## Single-arm resolved-proportion CI widths

| n | rate 0.3 | rate 0.5 | rate 0.7 |
|---|---:|---:|---:|
| 8 | width ~0.63 | ~0.65 | ~0.63 |
| 13 | ~0.50 | ~0.51 | ~0.50 |
| 60 | ~0.23 | ~0.25 | ~0.23 |
| 100 | ~0.18 | ~0.20 | ~0.18 |

At n = 8 the CI is ~0.6 wide (essentially uninformative); at n ≥ 60 it narrows
to ~0.25, which is enough for a coarse estimation-first claim.

## Assay-sensitivity recommendation

Per Design v1 §6.6, a future "RM-CSS ≈ Agent functionally" result is
interpretable only if the instrument can show that scope matters. Before any
selector comparison, the Pilot must demonstrate **Gold-vs-Placebo sensitivity**:
Gold/meaningful scope must not be indistinguishable from the random placebo, and
the generator must solve a non-trivial fraction of confirmed tasks. No numeric
Pilot threshold is invented here.

## Options (presented, NOT executed)

1. **Estimation-first RQ** with confidence intervals on the single-arm resolved
   proportion (feasible at n ≈ 9 extended).
2. **Extended F2P** including symbol-absence as secondary (n = 9) — reported
   transparently, kept separate from primary behavioral.
3. **New prospective mining** outside the sealed 786 (never open the reserve).
4. **Cross-repository expansion** (e.g. a Django/e2e-capable repository) to grow
   the confirmed pool.

## Recommended next step before any paid E2E

`Pilot Gold-vs-Placebo calibration` on the 8 confirmed behavioral F2P tasks
(fixed generator, fixed validator): measure whether Gold scope separates from
Placebo scope. Only then decide whether a selector comparison is informative at
the achievable n.