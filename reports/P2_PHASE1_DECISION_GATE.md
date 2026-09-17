# P2 Phase-1 Decision Gate — Adaptive-Budget Policies (DEVELOPMENT)

**Date:** 2026-09-18
**Tier:** T3 scientific DEVELOPMENT closure (ZERO API)
**Data:** djangoCMS DEV (174 tasks) + Saleor DEV (149 tasks); djangoCMS
DEV_TRAIN (117) used ONLY to derive the frozen constants.
**Decision:** **P2 Phase-1 = NEGATIVE** — no P2-P1..P4 policy shows a useful
recovery-cost trade-off on BOTH repositories. Stronger-method implementation
is NOT triggered (pre-registered gate; mission §4: if the simple four fail,
freeze the negative result and STOP stronger-method implementation — a valid
scientific result).

---

## 1. Per-policy results (realized budget; composite ranking; measured cost)

### djangoCMS DEV (n=174)

| Policy | mean B_t | macro ORR | micro ORR | mean cost $ | oracle-gap | over-alloc | under-alloc |
|---|---:|---:|---:|---:|---:|---:|---:|
| fixed-B1 (anchor) | 1.0 | 0.0464 | 0.0445 | 7.0e-05 | 0.0856 | 0.0 | 0.2047 |
| fixed-B3 (anchor) | 3.0 | 0.1177 | 0.1126 | 8.0e-05 | 0.1163 | 1.276 | 0.1334 |
| fixed-B5 (anchor) | 5.0 | 0.1633 | 0.1623 | 9.0e-05 | 0.1434 | 2.759 | 0.0879 |
| fixed-B10 (anchor) | 10.0 | 0.2512 | 0.2644 | 1.15e-04 | 0.2084 | 6.782 | 0.0 |
| P2-P1 score-gap | 1.61 | 0.0775 | 0.0681 | 7.3e-05 | 0.1092 | 0.368 | 0.1737 |
| P2-P2 marginal-score | 8.47 | 0.2389 | 0.2513 | 1.07e-04 | 0.2034 | 5.483 | 0.0123 |
| P2-P4 learning-k analogue | 8.45 | 0.2389 | 0.2513 | 1.07e-04 | 0.2035 | 5.460 | 0.0123 |
| P2-P3 cost-ratio tau=0.5 | 1.00 | 0.0464 | 0.0445 | 7.0e-05 | 0.0856 | 0.0 | 0.2047 |
| P2-P3 cost-ratio tau=1.0 | 1.55 | 0.0610 | 0.0628 | 7.3e-05 | 0.0964 | 0.391 | 0.1902 |
| P2-P3 cost-ratio tau=2.0 | 10.0 | 0.2512 | 0.2644 | 1.15e-04 | 0.2084 | 6.782 | 0.0 |

### Saleor DEV (n=149)

| Policy | mean B_t | macro ORR | micro ORR | mean cost $ | oracle-gap | over-alloc | under-alloc |
|---|---:|---:|---:|---:|---:|---:|---:|
| fixed-B1 (anchor) | 1.0 | 0.0775 | 0.0678 | 7.0e-05 | 0.1649 | 0.0 | 0.2398 |
| fixed-B3 (anchor) | 3.0 | 0.1576 | 0.1518 | 8.0e-05 | 0.1809 | 1.181 | 0.1597 |
| fixed-B5 (anchor) | 5.0 | 0.2369 | 0.2141 | 9.0e-05 | 0.2390 | 2.591 | 0.0804 |
| fixed-B10 (anchor) | 10.0 | 0.3173 | 0.3008 | 1.15e-04 | 0.3098 | 6.617 | 0.0 |
| P2-P1 score-gap | 1.52 | 0.1151 | 0.0976 | 7.3e-05 | 0.1906 | 0.322 | 0.2022 |
| P2-P2 marginal-score | 9.95 | 0.3173 | 0.3008 | 1.15e-04 | 0.3098 | 6.571 | 0.0 |
| P2-P4 learning-k analogue | 9.94 | 0.3139 | 0.2981 | 1.15e-04 | 0.3065 | 6.571 | 0.0034 |
| P2-P3 cost-ratio tau=0.5 | 9.03 | 0.2918 | 0.2683 | 1.10e-04 | 0.2874 | 6.0 | 0.0255 |
| P2-P3 cost-ratio tau=1.0 | 10.0 | 0.3173 | 0.3008 | 1.15e-04 | 0.3098 | 6.617 | 0.0 |
| P2-P3 cost-ratio tau=2.0 | 10.0 | 0.3173 | 0.3008 | 1.15e-04 | 0.3098 | 6.617 | 0.0 |

## 2. Per-policy classification

| Policy | Class | Primary finding |
|---|---:|---|
| P2-P1 score-gap | **NEGATIVE** | Stops very early (mean B_t 1.5–1.6) because most candidate scores are 0 (sparse tail); recovers only ~47% (djangoCMS) / ~49% (Saleor) of the fixed-B5 ORR at a marginal cost saving. Not a useful trade-off. |
| P2-P2 marginal-score | **NEGATIVE** | With tau_marg=1.0 it converges to B_t ≈ 8.5–10, recovering no more than fixed-B10 at no cost saving. Under-allocation is tiny, but the policy provides no savings. |
| P2-P3 cost-ratio | **NEGATIVE / REJECTED_BY_DESIGN** | Repo-asymmetric: at tau=0.5 it stops at B_t=1 on djangoCMS (ORR 0.0464, same as fixed-B1) but at B_t=9.0 on Saleor (ORR 0.2918, near fixed-B10) — the operating point is dominated by the omitted-size / universe-size distribution, i.e. a repo-identity/size artifact, not a transferable signal. tau is a declared ratio, NOT monetary truth. |
| P2-P4 learning-k analogue | **NEGATIVE** | Behaves like P2-P2 (both read the same score structure); converges to B_t ≈ 8.5–10 with no savings. The transferred "select k per query from score structure" does not beat fixed-B on this score distribution. |

## 3. Stronger-method gate (pre-registered)

Rule (frozen before outcomes): proceed to at most TWO stronger methods iff any
of P2-P1..P4 shows, on BOTH repositories, mean verifier cost strictly below
fixed-B5 AND macro ORR within 5% of fixed-B5.

Result: **gate = False** on every policy (each either saves cost but loses
>50% of recovery, or matches recovery at no cost saving). Therefore the two
stronger methods (cost-sensitive expected-loss stopping; one-step/joint
ranking+budget) are **NOT implemented**. This is the frozen negative per
mission §4.

## 4. Confound / artifact checks

- **No hidden-gold leakage:** policies consume only `PolicyView`
  (composite scores, omitted/universe size); proxy and labels are structurally
  absent (unit-tested). The only place gold is used is evaluation.
- **No djangoCMS INTERNAL_TEST / RESERVE / Saleor INTERNAL_TEST/RESERVE
  loading** (integration-tested; fail-closed).
- **Repo identity:** P2-P3 is repo-asymmetric by construction (cost-ratio vs
  task-size proxy), which is exactly why it is rejected; P2-P1/P2-P2/P2-P4
  behave consistently across repos (same qualitative negative).
- **τ derivation:** tau_marg derived on djangoCMS DEV_TRAIN ONLY; validated
  unchanged on DEV_VALIDATION + Saleor DEV (integration-tested).

## 5. What this DOES and DOES NOT mean

- **Does mean:** with the frozen composite ranker + measured verifier cost
  model, simple interpretable adaptive budgets provide no recovery-cost
  advantage over fixed-B on DEVELOPMENT. P2 adaptive-budget, in this simple
  family, is NOT a proven contribution.
- **Does NOT mean:** (1) that fixed-B is worse than Sparse alone — the fixed
  Route-B CONFIRMED result stands; (2) that no adaptive policy could ever
  help — this is a Phase-1 negative for this pre-registered family; (3) that
  the verifier model is provider-billed cost truth — it is a measured relative
  model; (4) any confirmatory claim — all evidence here is DEVELOPMENT.

## 6. Phase-2 candidate selection

Selected candidates for Phase 2: **NONE**. Per the P2 common evaluation
contract §8, a candidate is scientifically justified only if it Pareto-
dominates or matches recovery at lower cost on BOTH repositories with
uncertainty accounting; no P2-P1..P4 policy does. Saleor INTERNAL_TEST remains
sealed for a possible future confirmation ONLY after a policy is frozen — not
the case here.

## 7. Evidence

- Harness results: `research/p2-phase1/results_summary.json`
- Per-task rows: `research/p2-phase1/per_task_rows.json`
- Frozen constants: `research/p2-phase1/frozen_constants.json`
- Gates: `reports/p2_phase1_gates.json`
- Harness report: `reports/P2_PHASE1_HARNESS_RESULTS.md`
- Code: `src/benchmark/p2/`, `scripts/p2_phase1_run.py`
- Tests: `tests/unit/test_p2_policies.py`, `tests/unit/test_p2_evaluate.py`,
  `tests/integration/test_p2_harness.py`