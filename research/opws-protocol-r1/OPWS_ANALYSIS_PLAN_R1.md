# OPWS R1 — Statistical Analysis Plan (Frozen before outcomes)

**Mission:** M17_OPWS_PROTOCOL_FREEZE_R1
**Freeze date:** 2026-10-12
**Status:** FROZEN BEFORE ANY OPWS OUTCOME.

This plan is frozen exactly as written. It predeclares estimands, bootstrap
schedule and seeds, the frontier, and the interpretation guardrails. Population
identity (which tasks) is bound later by the population-binding schema only.

---

## 1. Population

- **Bound population:** the future Full-D7 READY population (identity/hash
  UNBOUND at this freeze). Binding is allowed only after the Full-D7
  scope/census issue is resolved and a valid population hash is frozen.
- **Primary paired eligible population (PPEP):** tasks that are
  `PRIMARY_PAIRED_ELIGIBLE` per `OPWS_ELIGIBILITY_FUNNEL_R1.json`
  (OPWS eligible AND RM_CSS + AGENT scope artifacts + GOLD validity control
  resolvable). Tasks invalidated to `OPWS_INVALID_TASKS.json` are excluded from
  arm scientific denominators with visible reasons.
- Eligibility is outcome-blind. No task is removed based on an observed OPWS
  result.

## 2. Estimands

Primary estimands on the PPEP:

1. **Δ JOINT**: difference in `JOINT_OPWS_PASS_RATE` between RM-CSS and AGENT.
2. **Δ BEHAVIOR**: difference in `BEHAVIOR_SUFFICIENCY_RATE` between RM-CSS and
   AGENT.

Each estimand is a **paired** difference on the exact same set of tasks.

## 3. Primary comparison

- Primary comparison: **RM-CSS vs AGENT** on the primary paired eligible
  population.
- Arm A: RM-CSS (OUR_METHOD).
- Arm B: AGENT (BUDGET_BOUNDED_ITERATIVE_AGENT).
- Analysis is paired; task is the resampling unit.

## 4. Primary uncertainty: paired task bootstrap

- `N_BOOTSTRAP = 10000`
- `BOOTSTRAP_SEED = 20261012`
- Method: resample the PPEP task indices with replacement; recompute the
  per-task rate difference per resample; report percentile CI
  `[q025, q975]` of the delta distribution (95% CI).
- Report per estimand: point estimate and 95% CI.
- **No superiority claim if the CI crosses 0.** Descriptive interpretation
  allowed; no winner token.

## 5. No non-inferiority / equivalence margin

- **No NI margin is chosen in this freeze.**
- A margin will not be introduced later to compensate for small n or for any
  post-outcome reason (owner correction #4).
- If a future amendment re-introduces an NI margin, it must be recorded in
  DECISIONS.md with an independent pre-outcome justification. Until then the
  predeclared analysis is **paired effect estimates + 95% CI** and the
  **sufficiency–scope frontier** (primary/descriptive).

## 6. Secondary comparisons (secondary / exploratory)

RM-CSS versus each of, on the arm's own eligible denominator:

- AGENTLESS_STYLE_ADAPTATION (literature-inspired localization adaptation)
- SIP (selective baseline)
- DENSE_K3, DENSE_K10, BM25_K3, BM25_K10 (retrieval baselines)
- BM25_TO_CIA_1HOP (CIA-style adaptation control) if registered

Contrasts reported: JOINT_OPWS_PASS_RATE delta, BEHAVIOR_SUFFICIENCY_RATE delta,
and paired scope-size differences (RM-CSS scope size − comparator scope size)
with the same bootstrap CI. Secondary contrasts are reported as
secondary/exploratory; nothing in this freeze upgrades them to primary.

**Select-all/ceiling and GOLD/diagnostic** are NOT ordinary competitors and are
excluded from the competitive secondary framing:

- SELECT_ALL: CEILING_CONTROL (maximal scope anchor on the frontier).
- GOLD: DIAGNOSTIC_ONLY (validity; never a competitive method).

## 7. Sufficiency–scope frontier (primary RQ3 object)

Predeclared table and plot:

| arm_id | joint pass rate | behavior sufficiency rate | preservation rate | mean scope size | median scope size | n_eligible |

- Per-task scatter: x = `scope_size_files`, y = behavior_sufficiency / joint
  pass rate, one point per arm-task, with per-arm aggregate markers.
- SELECT_ALL appears as the maximal-scope ceiling anchor; GOLD is plotted only
  if clearly labeled DIAGNOSTIC (preferred: kept out of the competitive plot and
  shown in the validity annex).
- No new opaque composite score is defined to manufacture a winner. The paper
  shows the tradeoff directly.
- Allowed qualitative interpretation: an arm is attractive when it preserves
  high observed sufficiency with a smaller scope.
- **No Pareto dominance is asserted unless the empirical points actually
  support it.**

## 8. RECALL_GAP reporting

- Predeclared: `historical_recall < 1 AND opws_joint_pass == 1`.
- Interpretation limited to: "some historically changed non-test file was not
  required under the frozen observed behavior + preservation contract."
- Reported per arm as a count/rate and in the frontier table; never presented
  as selector completeness and never as a failure (owner correction #5).

## 9. Sensitivity analyses (frozen)

1. **Reference-patch status treatment:** PRIMARY treatment vs the sensitivity
   treatment where reference ADDED and RENAMED-new-path files are excluded from
   every scope. Both reported; disagreement signaled as a sensitivity-limit
   note (owner correction #2).
2. Bootstrap CIs are recomputed under the sensitivity treatment as well.

## 10. Representativeness

- Report composition of PPEP vs the frozen MAIN_297 manifest (task-ID coverage,
  strata/eligibility reason-code distribution) as descriptive context.
- n_primary_paired and n_opws_eligible are reported; if n is small the analysis
  is reported as descriptive (pool rule n<40 → descriptive/supporting only per
  frozen M17 design) without changing estimands.

## 11. Validity / harness-consistency handling

- Tasks invalidated by GOLD/SELECT_ALL contract failures go to
  `OPWS_INVALID_TASKS.json` (OPWS_INVALID_CONTROL_FAILURE /
  HARNESS_CONSISTENCY_FAILURE) and are reported, not silently excluded.
- Aggregate denominators on the frontier reflect the arm-eligible population
  after visible invalidation.

## 12. Claim guardrails (frozen)

- Never call OPWS "generated-code correctness."
- Required wording: "behavioral sufficiency under the reference-patch /
  perfect-generator assumption."
- OPWS runtime is not LLM token efficiency.
- No post-outcome edits to estimands, seeds, bootstrap count, arm registry, or
  populations without a DECISIONS.md amendment that re-freezes the plan first.

## RQ6 (owner correction #6)

RQ6 perturbation design is **design-only** and deferred to a separate future
amendment. It is not part of this statistical plan, is not executed in this
mission, and does not gate RQ3.