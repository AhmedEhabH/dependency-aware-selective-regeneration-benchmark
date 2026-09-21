# WP-1b NI Margin — Decision Required (G1)

**Date:** 2026-09-21
**Status:** BLOCKER G1 — DECISION REQUIRED. No F1 non-inferiority margin for
the WP-1b selection-only comparison is frozen in an authoritative pre-result
artifact.

> **NO PAID WP-1b EXECUTION IS AUTHORIZED UNTIL THIS VALUE IS FROZEN.**

---

## 1. Why this document exists

The WP-1 hypothesis is stated as "without lower file-set F1" — a non-inferiority
claim. The WP-1a scorer schema explicitly says *"No non-inferiority margin is
silently chosen"*, while the WP-1a cost-quality categories encode a
point-estimate rule (`RM-CSS F1 >= Agent F1`). A point estimate that is
numerically positive must NOT automatically become a statistically supported
non-inferiority/superiority claim. This document records the full NI-margin
provenance, states that no authoritative numeric F1 margin exists for this
experiment, and requires an explicit prospective decision before WP-1b.

## 2. NI-margin provenance table

| # | Source | Value | Scope | Date | Commit | Authority | Applicable to WP-1b F1? |
|---|--------|-------|-------|------|--------|-----------|---------------------------|
| 1 | `docs/FINAL_RESEARCH_PROTOCOL.md` (DA-08) | Δ = 0.05 (+ sensitivity 0.03, 0.10) | Regression pass rate (H2 preservation, E2E) | 2026-07-22 | `845ba49` | FROZEN (v1.0) | NO — different outcome (regression pass rate, not F1) |
| 2 | `docs/STATISTICAL_ANALYSIS_PLAN.md` | Δ = 0.05 (+ 0.03, 0.10) | Regression pass rate (H2); one-sided 95% CI lower bound > −0.05 | 2026-07-22 | `845ba49` | FROZEN (v1.0) | NO — different outcome |
| 3 | `docs/EXPERIMENTAL_DESIGN_V2.md` (H1) | F1 non-inferiority Δ = 0.05 + recall superiority (+ sensitivity 0.03, 0.10) | `hybrid_selective` vs `repository_agent` / `single_shot_llm_scope` | 2026-07-26 | `559636c` / `b203b21` | DESIGN document (NOT in the frozen protocol set of `PROTOCOL_VERSION.md`) | CANDIDATE — hybrid_selective is the ancestor of the frozen RM-CSS; authority for THIS selection-only experiment is not established |
| 4 | `docs/END_TO_END_MEASUREMENT_BOUNDARY.md` | Δ = 0.05 | Task success (E2E boundary) | 2026-07-26 | `b203b21` | Boundary doc | NO — E2E task success |
| 5 | `docs/SWERANK_EMBED_BASELINE_PROTOCOL_FROZEN.md` | 0.05 pooled-recall points (conservative; rationale at F1 ~0.2–0.4) | Recall vs Route-B (SweRank embed) | 2026-09-19 | `9f043c6` | FROZEN (different comparison) | Precedent for a margin rationale in the same F1 operating region; NOT a WP-1b F1 margin |
| 6 | `docs/CALIBRATED_SET_SELECTION_V1_IMPACT_DECLARATION_2026-09-20.md` | "NO arbitrary non-inferiority margin. F1 is the preregistered primary criterion" | RM-CSS vs Sparse (V1 realization gate) | 2026-09-20 | `23d1d07` | FROZEN (predecessor gate) | Precedent: an earlier RM-CSS gate explicitly declined to freeze an F1 NI margin |
| 7 | `research/wp1a/wp1a_shared_scorer_schema.json` | "No non-inferiority margin is silently chosen" | WP-1b shared scorer | 2026-09-21 | `c53d918` | WP-1a frozen | Explicitly NO margin chosen |
| 8 | `research/wp1a/wp1a_cost_quality_categories.json` | point-estimate `RM-CSS F1 >= Agent F1` | WP-1b outcome categories | 2026-09-21 | `c53d918` | WP-1a frozen | CONFLICTS with a CI-based NI rule (see section 3) |
| 9 | `docs/WP1_REPOSITORY_AGENT_SELECTION_ONLY_BASELINE_DRAFT.md` §10.9 | "Do NOT invent a non-inferiority margin unless an already-authoritative source-of-truth document defines one for THIS selection-only experiment; use the categorical cost-quality rules" | WP-1 | 2026-09-21 | `c53d918` | Draft (DO_NOT_EXECUTE) | Explicitly defers the margin question |

**Conclusion:** No numeric F1 NI margin for the WP-1b selection-only comparison
is frozen in an authoritative pre-result artifact. The only candidate numeric
value is Δ = 0.05 F1 from `docs/EXPERIMENTAL_DESIGN_V2.md` (H1), whose scope
(`hybrid_selective` vs `repository_agent`) closely matches the WP-1b comparison
but whose authority for THIS experiment is not established by any frozen
protocol document. There are no TWO authoritative pre-result artifacts with
conflicting margins (the DA-08 margin governs a different outcome), so no
conflict-STOP applies; instead the "no defensible numeric margin exists" rule
applies.

## 3. Internal contradiction to resolve

The WP-1a cost-quality categories treat `RM-CSS F1 >= Agent F1` as
`RM_CSS_COST_QUALITY_DOMINANCE`. That is a point-estimate rule. A +0.001 F1
point advantage would satisfy it, yet a +0.001 F1 advantage is not a
statistically supported non-inferiority or dominance claim. The frozen
statistical plan's comparison machinery is CI-based (paired task bootstrap,
95% percentile CI). Before WP-1b, the decision rule must be clarified to
distinguish:

- non-inferiority (frozen margin Δ, one-sided CI lower bound > −Δ);
- statistical superiority (two-sided CI lower bound > 0);
- descriptive point advantage (point estimate positive, CI ambiguous);
- inconclusive comparison (CI crosses the decision boundary).

The candidate decision-rule preregistration is recorded in
`artifacts/wp1b_ci_decision_rule_preregistration_2026-09-21.json` and will be
activated only together with a prospectively frozen margin.

## 4. Why selecting the margin after WP-1b would be a protocol violation

- AC-11 / `docs/FINAL_RESEARCH_PROTOCOL.md` amendment rules forbid changing the
  NI margin "after the first main result is observed" without a recorded,
  prospective amendment.
- Choosing a margin after seeing the WP-1b F1 delta would be outcome-driven
  selection, invalidating the comparison's confirmatory status.
- The WP-1a freeze already committed to "no silent margin"; a post-outcome
  margin would contradict that recorded decision.

## 5. Clauses that constrain the decision

- `docs/FINAL_RESEARCH_PROTOCOL.md` DA-08 + AC-11 (amendment rules; only the
  regression-pass-rate margin is frozen, procedure: one-sided 95% CI lower
  bound > −Δ).
- `docs/STATISTICAL_ANALYSIS_PLAN.md` (paired bootstrap CIs; one-sided NI
  procedure; sensitivity reporting at 0.03/0.10).
- `docs/WP1_REPOSITORY_AGENT_SELECTION_ONLY_BASELINE_DRAFT.md` §10.8–10.9
  (categorical rules; do-not-invent rule).
- `research/wp1a/wp1a_shared_scorer_schema.json` (bootstrap delta-F1 CI
  crossing zero = "NO_DIFFERENCE_DETECTED_AT_THIS_N (not equivalence)").

## 6. Scientifically defensible ways to choose a margin prospectively

These are options for Ahmed/supervisor; this document does NOT recommend a
value merely to unblock execution.

- **A. Confirm the design-V2 H1 margin applies.** If Ahmed/supervisor
  authoritatively resolves that `docs/EXPERIMENTAL_DESIGN_V2.md` H1 governs
  the WP-1b selection-only comparison (hybrid_selective → frozen RM-CSS vs
  repository_agent), then Δ = 0.05 F1 with sensitivity at 0.03/0.10 becomes the
  frozen pre-existing margin. This is the strongest candidate because it is a
  pre-existing, pre-result numeric value for essentially the same comparison.
- **B. Define a claim-framing change (no NI margin).** Instead of a
  non-inferiority claim, restrict the WP-1b claim to descriptive
  cost-quality categories plus superiority testing (two-sided CI lower bound
  > 0). This removes the need for a margin but narrows the thesis claim.
- **C. Reference-anchored margin.** Use a margin derived from the frozen
  RM-CSS-vs-SIP operating point (F1 ~0.2–0.4) following the SWERANK precedent
  that 5 points is not material at these F1 levels. This is a new prospective
  choice requiring its own justification; it is not pre-existing.
- **D. Instrument-aware margin.** Combine the F1 margin decision with the G2
  completion-cap decision so that instrument failures are bounded before any
  NI comparison (see `docs/WP1B_AGENT_COMPLETION_CAP_PROVENANCE_2026-09-21.md`).

## 7. Consequences of each class of choice

- **Δ = 0.05 F1 (option A):** conservative at the observed F1 operating
  region; a one-sided 95% CI lower bound > −0.05 supports "without lower F1";
  sensitivity at 0.03/0.10 bounds fragility.
- **Claim-framing change (option B):** no margin to defend; the thesis must
  drop the "without lower F1" wording and rely on superiority + cost-quality
  categories.
- **Smaller margin (< 0.05):** stricter; harder to support non-inferiority;
  requires its own pre-outcome rationale.
- **Larger margin (> 0.05):** more permissive; risks accepting a material F1
  regression; requires explicit justification why a larger loss is acceptable.
- **No margin resolved:** WP-1b stays blocked (this document), or runs with
  descriptive categories only after an explicit scope decision.

## 8. Required decision inputs

1. Confirm or override the authority of `docs/EXPERIMENTAL_DESIGN_V2.md` H1 for
   the WP-1b selection-only comparison (option A), OR
2. choose a claim-framing change (option B), OR
3. provide a different prospective margin with justification (options C/D),
   OR
4. defer WP-1b.

## 9. Falsifiers

- This recommendation would be wrong if a frozen authoritative artifact
  predating WP-1a already defines an F1 NI margin for the selection-only
  comparison that this audit missed (in that case use that value instead).
- It would be wrong if Ahmed/supervisor has already made a documented margin
  decision that is not reflected in the repository artifacts examined here.