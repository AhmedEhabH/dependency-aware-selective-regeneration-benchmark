# WP-1b Post-Hoc Robustness and Limitations (2026-09-22)

Every item below is labelled one of:
**PRIMARY PREREGISTERED** · **SECONDARY PREREGISTERED** · **EXPLORATORY
PREREGISTERED** · **POST-HOC DESCRIPTIVE** · **PENDING EXTERNAL/BRAIN SCRIPT**.

Inputs are the frozen machine-readable artifacts only (see
`research/wp1b/wp1b_posthoc_robustness_input_manifest_2026-09-22.json`). No new
statistical algorithm was invented by OpenCode in this mission. Numbers are
quoted from the frozen JSONs, never from prose.

## 1. Primary P and S non-inferiority result — PRIMARY PREREGISTERED

`reports/wp1b_main297_result.json`

- **P (fail-closed, primary):** n=297, D = −0.006243848339918201,
  [Q2.5, Q97.5] = [−0.04488048757621672, +0.030762547682913435],
  Q5 = −0.0383314093433751; margin 0.05 → NI_SUPPORTED.
- **S (instrument-failure excluded):** n=295 (2 dropped: parser failure on
  `saleor-rc-094b1ec0f610`, `saleor-rc-37a3a7bbec31`), D =
  −0.011504765649930193, [Q2.5,Q97.5] = [−0.050202368045461694,
  +0.025468095259528607], Q5 = −0.04336616199062976.
- Final category: `RMCSS_NONINFERIOR_AT_LOWER_COST` (decision rules v2, verdict
  id 3).

## 2. Margin sensitivity — SECONDARY PREREGISTERED (reported, not decisive)

- Δ=0.03 → `INCONCLUSIVE_AT_THIS_N`; Δ=0.10 → `NI_SUPPORTED`.
- The Δ=0.03 reading must remain inconclusive in every summary.

## 3. Macro-F1 exploratory — EXPLORATORY PREREGISTERED

`reports/wp1b_main297_exploratory.json` X1:

- Agent macro-F1 = 0.397082534296782; RM-CSS macro-F1 = 0.34269371833245865;
  point (RM-CSS − Agent) = −0.054388815964323364. Macro-F1 favored the Agent;
  it is NOT the primary analysis and must not be concealed.

## 4. Variance substudy (15 tasks × 3 fresh replicates) — POST-HOC DESCRIPTIVE

`reports/wp1b_variance_15x3_result.json`

- Pooled F1 by replicate: {1: 0.3888888888888889, 2: 0.4383561643835616,
  3: 0.4788732394366197}; range 0.0899843505477308; mean 0.43537276423635674.
- **0.389 → 0.438 → 0.479 is NOT a trend claim.** It is execution variability;
  the main execution is not replicate 1; this is not three complete MAIN_50
  replications.
- Selected-set exact match (pairwise) = 0.4444444444444444;
  all-3-identical = 0.3333333333333333; mean pairwise Jaccard =
  0.6422222222222221; mean per-task F1 range = 0.13956709956709956.
- EMPTY = 0/45; truncation EMPTY = 0; cap hits = 0.

## 5. Cost accounting — PRIMARY PREREGISTERED (View A decides) + POST-HOC DESCRIPTIVE (billed)

- **Normalized/list-price (View A, ratio RM-CSS/Agent of per-task means):**
  model_calls ratio 0.27461858529819694 (CI [0.2708618331053351,
  0.2786116322701689]); total_tokens ratio 0.21389422598206467 (CI
  [0.209803826701223, 0.21793570430908216]); usd ratio 0.22071509763724523
  (CI [0.21636400950249024, 0.22498220760393717]). All upper < 1 → CHEAPER.
- Generative-tokens-only view: ratio 0.21336613317184888; coder-calls-only:
  ratio 0.13730929264909847.
- View B (setup amortized at N): +$0.000087/task → RM-CSS
  $0.005395855748116618/task.
- **Billed (POST-HOC DESCRIPTIVE, OpenRouter usage delta):** MAIN_297
  $3.430202 (before $24.733080 → after $28.163282); variance $0.623265.
  Billed usage is affected by provider caching; it is descriptive and must
  NEVER be presented as the preregistered normalized cost verdict.
- **Calls/tokens are the most provider-robust efficiency quantities:** RM-CSS
  2 calls/task and ~17,011 tokens/task vs Agent 7.28 calls/task and ~79,531
  tokens/task (View A).

## 6. X3 / X6 / X10 / X11 preregistered exploratory readings — EXPLORATORY PREREGISTERED

`reports/wp1b_main297_exploratory.json`

- **X3** band-teacher ceiling: `NO_TEACHER_HEADROOM` (hybrid − RM-CSS on
  [0.10,0.35): +0.029115333705271695, Q5 +0.01191717948494476). A near-miss is
  NOT a positive result.
- **X6** escalation frontier: `ESCALATION_NO_GAIN` (U1-REPLACE at 20%:
  −0.018778258778258783 vs random, p = 0.9950024987506247; gain capture at 20%
  = 0.1289865348971684). The negative preregistered reading remains negative.
- **X10** zero-generative dense anchor: size-matched dense F1 =
  0.2780952380952381, minus RM-CSS = −0.0787301587301587 → dense retrieval alone
  does not reproduce RM-CSS.
- **X11** tool quality: search_calls 977; non-consecutive duplicate share
  0.12698412698412698; zero-result search share 0.42681678607983625
  (multi-word 0.6861702127659575).

## 7. PENDING EXTERNAL/BRAIN SCRIPT

`PENDING_BRAIN_SCRIPT — not recomputed by OpenCode in this mission`

If the brain wishes to run a **run-noise / Q5 robustness** analysis (e.g.
sensitivity of Q5 to which specific runs/prediction draws are used, or
bootstrap-sensitivity around the Q5 boundary), no brain-reviewed script exists
in this repository at mission start, and OpenCode is not authorized to invent
the analysis. A future script must consume exactly these frozen inputs:

- `reports/wp1b_main297_result.json` (P and S statistics, bootstrap seed
  20260920, n_resamples 10000, task-level paired unit);
- `reports/wp1b_variance_15x3_result.json` (execution variability evidence,
  not a resampling unit for the primary);
- `research/wp1b/wp1b_decision_rules_v2.json` (verdict ordering and margin);
- `research/wp1b/wp1b_agent_budget_sensitivity_prereg.json` (AG16 sensitivity
  design; not a substitute for MAIN_297 primary);
- per-task predictions and labels under the frozen freeze tags
  `wp1b-main297-predictions-frozen-2026-09-22` /
  `wp1b-variance-predictions-frozen-2026-09-22`.

## 8. Claim discipline

- A post-hoc calculation must never become a primary claim.
- NI at Δ=0.05 ≠ superiority, ≠ equivalence, ≠ E2E correctness.
- Pooled micro-F1 (primary) vs macro-F1 (exploratory) stay distinct.
- Billed vs list/normalized USD stay distinct.
- 786 sealed Saleor RESERVE outcomes were never accessed.