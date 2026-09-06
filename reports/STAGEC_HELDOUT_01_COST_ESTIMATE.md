# STAGE-C-HELDOUT-CHALLENGE-01 (D053) — COST ESTIMATE

- Frozen pricing (from `reports/SCIENTIFIC_MICROSTUDY_MODEL_FREEZE.json`, DeepInfra turbo fp4):
  - prompt: $0.0000003 / token
  - completion: $0.000001 / token
- Provider/model: qwen/qwen3-coder @ DeepInfra, pinned, fallback OFF, temperature 0.0.

## Real probe calibration (G5 non-study probes, one per arm, on held-out scenario todo-heldout-001)

| Arm | probe prompt tokens | probe completion tokens | probe total tokens | probe model calls | probe cost ($/run) |
|-----|--------------------:|------------------------:|-------------------:|------------------:|-------------------:|
| iterative_repository_agent | 7341 | 287 | 7628 | 8 | 0.002489 |
| impact_plan | 966 | 824 | 1790 | 1 | 0.001114 |

Note: the held-out user-level scenario caused the Agent to explore with 8 model
calls (vs 1-selection probing in the smoke study); ImpactPlan still completed
with a single planner call.

## 60-run estimate

| Arm | runs | est. cost |
|-----|-----:|----------:|
| iterative_repository_agent | 30 | $0.074680 |
| impact_plan | 30 | $0.033414 |
| **Total** | **60** | **$0.108094** |

## Decision

- Hard stop: `ESTIMATED_HELDOUT_STUDY_COST_USD <= 0.20`.
- **ESTIMATE = $0.108 <= $0.20 → CONTINUE AUTOMATICALLY with all 60 real runs.**