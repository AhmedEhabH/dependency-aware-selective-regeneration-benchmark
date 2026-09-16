# Adaptive Verification Budget — Research Note (future-mechanism horizon)

**Date:** 2026-09-17
**Tier:** T2/T3 exploratory (ZERO model calls; DEVELOPMENT-only)
**Status:** EXPLORATORY HORIZON — NOT a contribution; fixed-budget Route B is
the frozen mechanism. This note preserves the broader research horizon inspired
by the Shichao Zhang adaptive/cost-sensitive kNN line and selective-prediction /
learning-to-defer / resource-allocation literature.

---

## 1. Old failed idea (do NOT resurrect)

```
task -> { verify whole task / do not verify }
```
The task-level binary RiskScorer route was investigated and rejected: the
signal did not replicate at V2 scale and the pooled signal was a
candidate-universe-size artifact. It stays closed.

## 2. Future candidate

```
task/candidate evidence -> marginal expected recovery -> choose B_t / stopping point
```

Formally, a policy such as:

```
B_t* = argmin_B [ C_verify(B) + rho * E[ remaining omission loss | evidence, B ] ]
```

where `rho` is a **sensitivity**, not a claimed monetary truth.

## 3. Exploratory evidence (DEVELOPMENT only, 2026-09-17)

Using the Route B V2 per-task Oracle recovery curves (153 tasks with >=1
Sparse-observed FN among omitted candidates):

| Statistic | Value | Implication |
|---|---|---|
| Fraction of tasks reaching >=90% of Oracle@10 with B<5 | **83%** | fixed B=5 is wasteful on most tasks |
| Fraction with best-B = 1 | 33% | many tasks recover at tiny budget |
| Fraction with best-B = 3 | 50% | B=3 is the modal optimal |
| Marginal gain B=1->3 | +0.348 | large first increment |
| Marginal gain B=3->5 | +0.049 | sharply diminishing |
| Marginal gain B=5->10 | +0.024 | near-saturated |

This is exploratory: it shows per-task budget heterogeneity is plausibly worth
pursuing AFTER fixed-budget Route B is established and a frozen confirmatory
test exists. It is NOT evidence for a learned adaptive policy, and no complex
adaptive model is fitted.

## 4. Decision output

- **Decision:** `WORTH-PURSUING AFTER FIXED ROUTE-B` (exploratory signal only).
- Conditions for pursuit: (a) fixed-budget Route B frozen; (b) a confirmatory
  test available; (c) the adaptive policy remains a simple marginal-benefit /
  stopping rule (no learned model, no tuning per fold).

## 5. Relation to the literature (Track B — algorithmic inspiration, NOT a
novelty-competitor list)

- Shichao Zhang adaptive-resource line: Learning-k for kNN; Challenges in KNN;
  KNN One-Step; Cost-sensitive KNN; Demand-driven KNN; adaptive-neighborhood.
- Selective prediction / learning-to-defer / cost-sensitive resource allocation.

These inspire: adaptive verification budget B_t; marginal-benefit stopping;
expected miss-loss vs verification cost; joint candidate-selection +
budget-selection. None is presented as direct SE novelty evidence.

## 6. Do NOT overclaim

- This is NOT a contribution and NOT a thesis mechanism yet.
- It does NOT resurrect the binary task RiskScorer.
- No learned adaptive policy is implemented tonight.

## 7. Traceability

- Exploratory data: `research/transparency/adaptive_budget_exploratory.json`.
- Related decisions: DECISIONS D-017 (B-curve), D-018 (analytic Random),
  E-018 (Route B V2), D-016 (CIA frozen).