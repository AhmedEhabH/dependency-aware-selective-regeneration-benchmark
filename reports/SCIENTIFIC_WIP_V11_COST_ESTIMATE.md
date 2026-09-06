# SCIENTIFIC-WIP-IMPACTPLAN-V1.1 — ADDITIONAL 30-RUN COST ESTIMATE (D051)

Estimated before any scientific v1.1 call, from actual acceptance-probe usage,
frozen per-role caps, and the frozen DeepInfra pricing snapshot.

## Frozen pricing (DeepInfra via OpenRouter, fp4 turbo)

- prompt: `$0.0000003` / token
- completion: `$0.000001` / token
- Source: `reports/SCIENTIFIC_MICROSTUDY_MODEL_FREEZE.json` (fetched 2026-09-06)

## Actual acceptance-probe usage (2026-09-06-v11 gate)

| Probe | prompt | completion | cost |
| --- | ---: | ---: | ---: |
| Agent E2E | 1298 | 152 | $0.000541 |
| ImpactPlan E2E | 944 | 284 | $0.000567 |

## Worst-case per-cell upper bound (frozen caps)

- Agent arm: 8 control calls x 1024 + patch 8192 + repair 8192 = 24576 completion max,
  plus ~40000 prompt worst case => **$0.0366**
- ImpactPlan arm: planner 4096 + patch 8192 + repair 8192 = 20480 completion max,
  plus ~16000 prompt worst case => **$0.0253**

## Historical calibration

`exp-20260905-225518` (30/30 terminal) reported ~$0.298 scientific API cost
=> ~$0.00993 per cell; 30 cells ~$0.298.

## Decision

- Worst-case 30-cell upper bound (15 agent + 15 impact_plan): **$0.928**
- Historical-calibrated realistic estimate: **~$0.298**
- Budget threshold: **$1.50**
- **DECISION: CONTINUE automatically.** Worst case is well below the threshold;
  no STOP is triggered by Phase 7.

```
V11_30RUN_COST_ESTIMATE_USD=0.298   (historical-calibrated)
V11_30RUN_COST_UPPER_BOUND_USD=0.928
V11_30RUN_COST_THRESHOLD_USD=1.50
V11_30RUN_COST_AUTHORIZED=YES
```