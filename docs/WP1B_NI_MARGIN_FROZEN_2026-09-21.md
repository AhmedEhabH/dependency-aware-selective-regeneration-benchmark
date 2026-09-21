# WP-1b NI Margin — FROZEN (G1) — 2026-09-21

**Status:** FROZEN BEFORE RESULT. **Authority:** D1 + D2 in the Ahmed decision
block (see `DECISIONS.md`, `WP1B_G2_COMPLETION_CAP` is a separate decision).
Machine-readable: `research/wp1b/wp1b_ni_margin_frozen.json`.

## 1. Decision

- **Margin (D1):** Δ = 0.05, absolute pooled micro-F1. Sensitivity Δ = 0.03 and
  0.10 (reported, not decisive).
- **Statistic:** D = F1_pooled(RM-CSS) − F1_pooled(Agent) over the same N task
  IDs, where F1_pooled = 2·ΣTP / (Σ|pred| + Σ|gold|). This is the aggregation
  that reproduces the frozen RESERVE-300 values 0.26474622770919065 /
  0.35687263556116017.
- **CI:** paired task bootstrap, 10,000 resamples, seed 20260920; each resample
  draws task IDs with replacement and recomputes both pooled F1 values.
- **NI decision:** the 5th percentile (Q5) of the bootstrap D distribution
  (one-sided 95 % lower bound, per `docs/STATISTICAL_ANALYSIS_PLAN.md` §3)
  > −0.05. Also report [Q2.5, Q97.5].
- **Q5 vs reporting CI:** the NI decision uses Q5 while the reporting CI in
  `wp1a_shared_scorer_schema.json` is [Q2.5, Q97.5]. They are different
  quantities, not a conflict.

## 2. Inheritance (D2)

Design-V2 H1 (quoted in full):

> H1: Impact accuracy | A | `hybrid_selective` vs `repository_agent` /
> `single_shot_llm_scope` | F1 non-inferiority (Δ=0.05) + recall superiority

Only the **margin** is inherited. The **recall-superiority** half of H1 is NOT
inherited; recall is reported as a secondary descriptive metric with CI.

## 3. Coherence anchor (pre-result, from frozen data)

The frozen RM-CSS − SIP gain on RESERVE-300 is **+0.0921**, CI [+0.0691,
+0.1156]. Δ = 0.05 is **below** the lower bound 0.0691, so an NI verdict cannot
hide an F1 loss as large as the method gain the thesis itself claims. Δ = 0.03
is about 50 % of that lower bound (the stricter sensitivity).

> The RM-CSS-vs-SIP effect-size comparison is used ONLY as a coherence/scale
> anchor, NOT as proof that the same effect distribution applies to
> RM-CSS-vs-Agent.

## 4. Relative size

Δ = 0.05 is about **14.0 %** of RM-CSS F1 on RESERVE-300 (0.3569) and about
**12.7 %** on MAIN_50 (0.3923).

## 5. Falsifiers

- This freeze is wrong if an authoritative frozen artifact defines a different
  F1 NI margin for the selection-only comparison (none was found; see
  `docs/WP1B_NI_MARGIN_DECISION_REQUIRED_2026-09-21.md`).
- It is wrong if the margin is misread as the [Q2.5,Q97.5] reporting CI rather
  than the Q5 one-sided rule.