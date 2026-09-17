# Adaptive Budget P2 — Pre-Registration Note

**Date:** 2026-09-17 (updated same day for the V1.4 pre-confirmatory
readiness mission; status unchanged)
**Tier:** T3 scientific documentation (ZERO LLM)
**Model:** openrouter/deepseek/deepseek-v4-flash-0731
**Status:** **CONDITIONAL — AFTER FIXED ROUTE-B CONFIRMATION** (P2 is NOT
complete; no learned adaptive policy is fitted here).

---

## 1. Purpose

Pre-register the P2 adaptive-budget program: observable candidate/task features
that could support **marginal stopping** (deciding when to stop adding
verification budget per task), separated into (a) deployable observables and
(b) Oracle-derived exploratory analyses. P2 stays conditional because the fixed
Route-B budget curve must first be confirmed (djangoCMS INTERNAL_TEST).

## 2. Current exploratory evidence (DEVELOPMENT only, not confirmatory)

From `docs/ADAPTIVE_VERIFICATION_BUDGET_RESEARCH_NOTE.md` (153 dev tasks with
≥1 missed):

- 83% of tasks reach ≥90% of Oracle@10 with B<5.
- Best-B=1 on 33% of tasks; best-B=3 on 50%.
- Marginal gain B=1→3: +0.348; B=3→5: +0.049; B=5→10: +0.024.
- ⇒ Diminishing returns after B≈3, but the per-task "when to stop" signal is
  NOT yet a deployable observable.

## 3. Observable candidate/task features (deployable, parent-visible only)

These features are computable BEFORE any verifier call and are candidates for
marginal-stopping rules. They contain NO hidden gold / no future state.

1. **Score gap:** difference between the top-ranked candidate's
   `BM25+Graph-Neighbor Composite` (historical label: Classical-CIA) score and
   the (B+1)-th candidate's score, or the largest adjacent score gap in the
   ranked list. Interpretable as "confidence that the next candidate adds
   value."
2. **Marginal score threshold:** the raw composite/BM25 score of the B-th
   ranked candidate (absolute threshold signal).
3. **Cost-ratio:** accumulated verifier tokens/cost spent on this task up to B,
   divided by a task-size proxy (omitted-set size or candidate-universe size);
   a normalized "spend so far" signal.
4. **Dispersion:** score variance / interquartile range of the top-K ranked
   candidates (flatter tail ⇒ stop earlier).
5. **Task size:** omitted-set size and candidate-universe size (fixed per task;
   used only to normalize, never as a gold signal).

All five are defined on parent-visible inputs only; none uses the hidden proxy,
gold, or any confirmatory outcome. The exact composite formula is the frozen
`score(p) = normalized_BM25(p) + binary_graph_neighbor(p)` from the Route-B V2
protocol (rank order is what feeds the rules; raw magnitude is used only for
the marginal-score-threshold rule).

## 4. Pre-registered future policies (2–3, simple, fixed)

These are pre-registered DEFINITIONS. **No policy is selected using
confirmatory data; no winner is chosen here.** Each policy is a deterministic
stopping rule parameterized by a pre-registered constant:

- **P2-P1 — Score-gap stopping:** stop at the smallest B ∈ {1,3,5,10} where the
  adjacent score gap drops below a pre-registered threshold τ_gap (e.g., 0.10
  relative to the top score). Fixed τ before seeing confirmatory outcomes.
- **P2-P2 — Marginal-score threshold:** stop at the smallest B where the B-th
  candidate's absolute score < τ_marg (pre-registered, e.g., 25th percentile of
  the development score distribution computed BEFORE confirmatory results).
- **P2-P3 — Cost-ratio stopping:** stop when accumulated verifier cost /
  task-size proxy ≥ τ_cost (pre-registered; protects total budget on large
  tasks).

Each policy will be evaluated ONLY on confirmatory data after the fixed Route-B
confirmation, against the fixed-B baselines (B=1,3,5,10), reporting per-policy
recovery-vs-budget trade-off. No policy that was tuned on development outcomes
is eligible.

## 5. Explicit exclusions (do NOT do)

- Do NOT fit a learned adaptive policy (e.g., trained classifier for stopping)
  on DEVELOPMENT and claim transfer; that would be an un-pre-registered learned
  model.
- Do NOT select the "winner" among P2-P1/P2-P2/P2-P3 using confirmatory data.
- Do NOT claim adaptive budget as a contribution until a pre-registered policy
  is evaluated on confirmatory data.
- Do NOT resurrect the binary task-level RiskScorer (rejected; negative result
  stands).
- Do NOT tune τ_gap / τ_marg / τ_cost on any confirmatory outcome.

## 6. Train / dev-only evaluation plan (exact)

P2 rule evaluation happens in two strictly separated phases:

1. **Development (TRAIN/VALIDATION, djangoCMS DEV + Saleor DEV):** the three
   candidate features are computed and their distributions (score-gap
   percentiles, marginal-score percentiles, cost-ratio percentiles) are
   recorded. This is the ONLY phase that informs the fixed τ constants. No
   rule is "chosen" here; the three rules are pre-registered as candidate
   definitions and all are carried forward with their frozen τ values.
2. **Confirmatory (djangoCMS INTERNAL_TEST, after fixed Route-B confirmation):**
   all three pre-registered rules are applied with their frozen τ values; each
   is scored against the fixed-B baselines (B=1,3,5,10) on recovery-vs-budget
   and cost. Reporting is per-rule and descriptive; no winner is declared from
   a confirmatory outcome in the same session.

## 7. Stop / fail criteria (pre-registered)

- **Marginal-gain sanity gate (dev-only):** if on development data the marginal
  ORR gain B=1→3, B=3→5, B=5→10 does not diminish monotonically on the pooled
  curve, the "diminishing returns" motivation is weakened; P2 proceeds only as
  a descriptive sensitivity, not as a primary claim.
- **Confirmatory fail criterion:** if no pre-registered P2 rule recovers at
  least as many FNs as the best fixed-B baseline (B=5) at no greater cost, the
  adaptive-budget program is closed as NEGATIVE and reported — no further
  rule-fitting.
- **Integrity stop:** any use of INTERNAL_TEST outcomes to adjust a τ or to
  reorder/delete a pre-registered rule aborts the P2 evaluation and is
  reported as a protocol violation.

## 8. Gate to leave CONDITIONAL → ACTIVE

P2 becomes ACTIVE only when BOTH hold:
1. Fixed Route-B confirmatory test (djangoCMS INTERNAL_TEST) is executed and the
   frozen progression gate is PASS (or a frozen negative result is recorded);
2. A separate pre-registered adaptive-budget protocol (with frozen τ constants
   and evaluation plan) is approved.

## 9. Evidence that would CLOSE P2 as NEGATIVE

- The fixed Route-B confirmatory gate FAILS (no material recovery above
  analytic Random) — the adaptive program is moot and is closed as negative.
- On confirmatory data, no pre-registered P2 rule dominates fixed-B baselines
  on recovery-vs-cost (see §7) — closed as negative, reported truthfully.
- The development marginal-gain sanity gate fails (§7) and the descriptive
  sensitivity shows no cost advantage — closed as negative.

## 10. Relationship to the proposal

Proposal V1.4 lists adaptive budget as future/conditional work (ρ =
sensitivity; status CONDITIONAL, §11.6 "Future work"). This note makes the
future work precise and prevents overfitting. It does not change any proposal
claim.