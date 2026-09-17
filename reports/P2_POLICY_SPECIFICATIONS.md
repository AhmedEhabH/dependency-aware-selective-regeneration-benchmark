# P2 Policy Specifications — P2-P1..P4 (pre-registered, interpretable)

**Date:** 2026-09-18
**Tier:** T3 scientific documentation (ZERO API)
**Status:** FROZEN before evaluation on DEV_VALIDATION / Saleor DEV. Constants
derived ONLY on djangoCMS DEV_TRAIN (117 tasks) where derivation is required;
declared constants are frozen as declared.
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731

For every policy: definition, required features, no-gold proof, complexity,
tie/failure rule, tests, development results per repo, matched fixed-B
comparison.

---

## P2-P1 — Score-gap stopping

- **Definition (exact, frozen):** rank omitted candidates by the frozen
  composite score `s(p) = normalized_BM25(p) + binary_graph_neighbor(p)`
  descending (ties by path ascending). For B in {1,3,5,10}, define the
  relative adjacent gap `gap(B) = (s_B - s_{B+1}) / s_1` (with `s_{B+1} = 0`
  when B == N). Emit
  `B_t = min{ B in {1,3,5,10} : gap(B) < tau_gap or B >= N }`, default 10.
- **Frozen constant:** `tau_gap = 0.10` (declared in
  `docs/ADAPTIVE_BUDGET_P2_PRE_REGISTRATION_NOTE.md`).
- **Required features:** composite scores of all omitted candidates
  (observable; BM25 + graph-neighbor both parent-visible).
- **No-gold proof:** uses only composite scores + omitted size N; proxy/labels
  are structurally absent from `PolicyView` (unit-tested).
- **Complexity:** O(N log N) sorting once per task (same as the frozen ranker);
  O(B) rule evaluation.
- **Tie/failure rule:** B capped to [1, N]; N=0 → B_t=0; s_1=0 (all flat) →
  B_t=1 (no signal, stop immediately).
- **Unit tests:** `tests/unit/test_p2_policies.py::TestScoreGap`.
- **Integration tests:** `tests/integration/test_p2_harness.py`.
- **DEV results (djangoCMS/Saleor):** mean B_t 1.61/1.52; macro ORR 0.0775/0.1151
  (≈47–49% of fixed-B5). Matched fixed-B point: fixed-B3 (lower cost, lower
  recovery). **NEGATIVE.**

## P2-P2 — Marginal-score stopping

- **Definition (exact):** rank by composite descending. For B in {1,3,5,10},
  emit `B_t = min{ B : s_B < tau_marg or B >= N }`, default 10.
- **Frozen constant:** `tau_marg = 1.0` = 25th percentile of the per-task
  TOP-1 composite scores on djangoCMS DEV_TRAIN ONLY (derived before any
  DEV_VALIDATION / Saleor outcome; recorded in `frozen_constants.json`).
- **Required features:** composite scores (observable).
- **No-gold proof:** only observable scores; label/proxy absent (unit-tested).
- **Complexity:** O(N log N) once; O(B) rule.
- **Tie/failure rule:** B capped to [1, N]; N=0 → 0; empty score list handled.
- **Unit tests:** `TestMarginalScore`.
- **DEV results:** mean B_t 8.47/9.95; macro ORR 0.2389/0.3173 ≈ fixed-B10 at
  the same cost. **NEGATIVE** (no cost saving).

## P2-P3 — Cost-ratio stopping

- **Definition (exact):** for B in {1,3,5,10}, emit
  `B_t = min{ B : verifier_tokens(B) / omitted_size >= tau_cost }`, default 10.
  `verifier_tokens(B) = 204.51 + 7.40*B` (measured model).
- **Frozen constants:** declared cost-ratio sensitivity grid
  `tau_cost in {0.5, 1.0, 2.0}` — a declared ratio, NEVER presented as
  monetary truth.
- **Required features:** measured token model + omitted-size N (observable).
- **No-gold proof:** no label/proxy used (unit-tested).
- **Complexity:** O(1) per candidate-B evaluation.
- **Tie/failure rule:** B capped to [1, N]; N=0 → 0.
- **Unit tests:** `TestCostRatio`.
- **DEV results:** repo-asymmetric (djangoCMS tau=0.5 → B_t=1, ORR 0.0464;
  Saleor tau=0.5 → B_t=9.0, ORR 0.2918) — the operating point is driven by
  omitted-size/universe-size distributions. **NEGATIVE / REJECTED_BY_DESIGN**
  (size/repo artifact).

## P2-P4 — Learning-k analogue

- **Definition (exact):** adapt "select k per query from the score structure"
  (Zhang line) to verification budgets: rank by composite descending; for B in
  {1,3,5,10}, emit `B_t = min{ B : cumulative_top_B_score / total_score >=
  tau_energy }`, default 10.
- **Transferred concept:** per-query (per-task) selection of the neighborhood /
  budget count from the observable score structure (difficulty-aware k).
- **NOT transferred:** kNN labels, distance geometry, majority voting, or any
  fitted/learned classifier. This is a deterministic score-mass rule.
- **Frozen constant:** `tau_energy = 0.90` (declared).
- **Required features:** composite scores (observable).
- **No-gold proof:** only observable scores (unit-tested).
- **Complexity:** O(N log N) once; O(B) rule.
- **Tie/failure rule:** B capped to [1, N]; total score 0 → B_t=1.
- **Unit tests:** `TestLearningK`.
- **DEV results:** mean B_t 8.45/9.94; macro ORR 0.2389/0.3139 ≈ fixed-B10 at
  same cost. **NEGATIVE** (no savings; behaves like P2-P2 on this score
  distribution).

---

## Decision (frozen)

All four policies are **NEGATIVE** (P2-P3 additionally REJECTED_BY_DESIGN as a
size/repo artifact). Stronger methods are NOT triggered. P2 Phase-1 = negative
closure; the fixed-B thesis (CONFIRMED) stands. Saleor INTERNAL_TEST remains
sealed.