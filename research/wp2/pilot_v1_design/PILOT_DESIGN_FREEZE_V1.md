# WP2 Pilot Design Freeze V1 (M13B)

Status: **DESIGN_FROZEN_ZERO_API_NOT_AUTHORIZED_FOR_PAID_EXECUTION**

## Pilot-A (M14A): Gold vs Placebo assay calibration

- Tasks (12, protected ASSAY_HOLDOUT): b497f8d82426, b410358502a1, a91ea48a60a7, bbba01a02725, 6f37bd256e12, 5b0e5206c5fd, d3847fa5f518, 6459dd2d9135, 012472eb8482, 44c7495ca9bf, b14def73518c, a3c478408852
- Arms: GOLD_HARD, PLACEBO_HARD; replicates r1, r2; 48 episodes.
- Interface: UNCHANGED from Smoke v2.2 (SEARCH/REPLACE, 1 repair, qwen/qwen3-coder via deepinfra/turbo, allow_fallbacks=false, temperature 0, 8192 tokens).
- S0: zero-API V3.1 oracle readiness of all 26 eligible tasks, then the frozen replacement rule, before any paid call.

| Gate | Rule |
|---|---|
| A0_instrument | evidence integrity; zero protected-pool violations; zero applied_without_evaluation; zero architecture-scope violations |
| A1_completion | 100% planned episodes terminal (provider outages are pending, never terminal); evaluation complete |
| A2 | GOLD APPLIED >= 14/24 |
| A3 | GOLD RESOLVED >= 3/24 |
| A4 | PLACEBO RESOLVED <= 1/24 |
| A5 | GOLD - PLACEBO RESOLVED >= 2 and #tasks(gold>placebo) >= #tasks(placebo>gold) |

Gate calibration (binomial): {"P(A2 pass | gold_applied_rate=0.80)": 0.996, "P(A3 pass | gold_rate=0.15)": 0.72, "P(A3 pass | gold_rate=0.2)": 0.885, "P(A3 pass | gold_rate=0.25)": 0.96, "P(A4 pass | placebo_rate=0.03)": 0.839, "note": "binomial, episodes treated as independent (optimistic: two replicates per task are correlated); used only to avoid gates that fail by chance", "reference_old_gate_P(>=4/24 | 0.20)": 0.736}

Outcome tokens:

- `PILOT_A_GENERATOR_FLOOR_HOLD`: A2/A3/A5 fail -> HUMAN_DECISION (options: M14R interface probe on DEV_TRAIN_ENG only; never consume Pilot-B tasks)
- `PILOT_A_INSTRUMENT_FIX`: A0 or A1 fail -> instrument repair on ENG/synthetic evidence; no new protected outcomes
- `PILOT_A_PASS`: A0..A5 pass -> M15
- `PILOT_A_PLACEBO_LEAK_REVIEW`: A4 fail -> HUMAN_DECISION

Budget: expected $0.214, ceiling $1.0, evaluation ≈ 3.3 h.

## Pilot-B (M15): selector behavior (descriptive)

- Tasks (12, disjoint): 436f52ee3d0c, 34511f977388, 0a39d039049d, aca84e6c4252, 60c8722863c1, 9bf2755c9bd0, 05df3bec57e2, 9aa434eeefe7, 99d963aed3e5, eacffa70e721, ded69f9c7097, d7fe298a4752
- Arms: RMCSS_HARD, AGENT_HARD, GOLD_HARD (reference); r1, r2; 72 episodes.
- Agent localization REQUIRED first: one fresh Agent localization per task per replicate (r1, r2); replicate r uses Agent run r (selector stochasticity is part of the method); expected $0.556.
- Cost boundary: selector + generation + repair, provider-reported (ledger).
- Budget ceiling $2.5; evaluation ≈ 5.0 h.

## Research replicate rule

- for RM-CSS or Agent: endpoint-tuple agreement across r1/r2 < 0.75 OR |resolved_rate_r1 - resolved_rate_r2| > 0.10; never 1.
