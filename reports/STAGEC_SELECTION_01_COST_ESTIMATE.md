# STAGE-C-SELECTION-01 (D052) — COST ESTIMATE

- Frozen pricing (from `reports/SCIENTIFIC_MICROSTUDY_MODEL_FREEZE.json`, DeepInfra turbo fp4):
  - prompt: $0.0000003 / token
  - completion: $0.000001 / token
- Provider/model: qwen/qwen3-coder @ DeepInfra, pinned, fallback OFF, temperature 0.0.

## Real probe calibration (G5 non-study probes, one per arm)

| Arm | probe prompt tokens | probe completion tokens | probe cost ($/run) |
|-----|--------------------:|------------------------:|-------------------:|
| iterative_repository_agent | 4340 | 138 | 0.001440 |
| impact_plan | 2168 | 38 | 0.000688 |

## 30-run estimate

| Arm | runs | est. cost |
|-----|-----:|----------:|
| iterative_repository_agent | 15 | $0.021600 |
| impact_plan | 15 | $0.010326 |
| **Total** | **30** | **$0.031926** |

## Decision

- Hard stop: `ESTIMATED_SELECTION_STUDY_COST_USD <= 0.25`.
- **ESTIMATE = $0.032 <= $0.25 → CONTINUE AUTOMATICALLY with all 30 runs.**

The selection-only design (analyze_impact once per run, no regeneration/repair/
evaluator) stays well under the guard.