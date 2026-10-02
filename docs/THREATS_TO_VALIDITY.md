# THREATS TO VALIDITY

**Role:** Consolidated threats to validity across the primary and supporting
results. This is a disclosure document; it does not weaken the supported claims
— it bounds their interpretation. Wording rules in
[`CLAIM_REGISTRY.md`](CLAIM_REGISTRY.md) are binding.

---

## Primary results (WP1)

### 1. Selection / survivorship bias (RESERVE-300 and MAIN_297)

- RESERVE-300 is a clean untouched reserve, but eligibility filters
  (changed-test evidence, installability, behavioral F2P, GOLD_HARD scoped-gold
  pass) are structural; the paired comparison is internally valid on the
  evaluated population, while level estimates may be optimistic for MAIN
  overall.
- MAIN_297 is a frozen manifest; the agent is a **budget-bounded** baseline
  (8 calls, 1024-token control cap, 2000-char observation window). Claims are
  against that bounded agent, never "the best possible agent".

### 2. Observed change-set proxy, not semantic gold

- File-level F1 is scored against the parent→target changed production-file set
  (an observed change-set proxy). No P/R/V/H semantic gold is fabricated from
  diffs. This bounds the construct: the metric measures file-overlap with the
  historical change, not semantic necessity.

### 3. Non-inferiority is not equivalence or superiority

- MAIN_297 supports NI at the preregistered Δ=0.05; Δ=0.03 is inconclusive at
  this n; macro-F1 and the point estimate favor the Agent. Never present NI as
  equivalence or superiority.

### 4. Cost accounting

- View A ratios (calls/tokens/USD at list price) are the provider-robust
  efficiency claims; billed usage differs due to provider caching. Always label
  which accounting is reported.

### 5. Representation studies are single-model

- djangoCMS explicit-v1 vs sparse-v2 and the graph ablation are single-model
  (Qwen3-Coder family) studies on one repository; no cross-model or
  cross-repository generalization claim is made.

## Supporting results (WP2)

### 6. Small-sample descriptive endpoints

- M15-R OPWS is Pilot-B n=10, descriptive only. It shows limited
  reference-patch sufficiency for RM-CSS (3/10) and Agent (2/10–3/10) scopes on
  that small sample; no superiority claim.

### 7. Generator floor (Pilot-A, M14R, M15-R generation)

- No tested generator variant cleared the capability floor (Pilot-A GOLD/PLACEBO
  resolved 0; M14R robust 8/9/8/8; M15-R S2 gate failed, S3 correctly skipped).
  These are supporting negatives: no generation-based selector comparison is
  valid, and "generator correctness is solved" is forbidden.

### 8. Pipeline validity is engineering, not ranking

- Smoke v2.2 demonstrates the E2E pipeline runs as an engineering pipeline; it
  provides no selector ranking and no E2E superiority evidence.

### 9. M16-v1 contributed no outcome

- M16-v1 stopped as a pre-experiment adapter failure; no MAIN OPWS outcome
  exists. Any sentence presenting M16-v1 as a result is forbidden.

## Methodology / instrument

### 10. Repetition collapse in historical C4-V3 oracle construction

- The frozen C4-V3 path classified changed-test nodes on the final repetition
  only (documented instrument amendment M16_R1). Historical ENG/M14R/M15-R
  oracle sets are affected; M16 was to retain per-repetition outcomes but never
  reached that phase. This is a disclosed instrument limitation, not a
  re-interpretation of results.

### 11. Single Agent run variance

- The MAIN_297 δ CI omits Agent run-to-run variance; the 15×3 variance
  substudy bounds it only descriptively.

### 12. Repository scope

- All primary evidence is Saleor (Python/Django). No language-agnostic claim is
  made; cross-language generalization (WP3) is optional and not started.

## Mitigations in place

- Selector-blind eligibility/readiness ordering in WP2 designs;
- frozen decision rules and preregistered margins;
- sealed RESERVE outcomes (never opened/read/scored/sampled);
- append-only decision record and immutable result tags;
- every paid run ends with a review card; MAIN-mode cards gate only on
  instrument-level anomalies.

## Reference

Experiment-by-experiment allowed interpretation is recorded in
[`docs/EXPERIMENT_LEDGER.md`](EXPERIMENT_LEDGER.md); the binding wording rules
are in [`docs/CLAIM_REGISTRY.md`](CLAIM_REGISTRY.md).