# RESULTS SUMMARY — Canonical Results Index

**Role:** Concise canonical summary of all results, with numbers traced to the
frozen artifacts in `docs/EXPERIMENT_LEDGER.md`. Negative results are reported
with equal weight. This is the research-landing numbers source for the 2026-10-02
closure.

Primary metric: **file-level impact correctness (file-level F1)** on
repository-level affected-file / editable change-scope selection.

---

## WP1 — Primary results

### E-1 djangoCMS explicit-v1 vs sparse-v2

- Explicit full-repository plan: valid 6/30, truncated 19.
- Sparse impact plan (v2): valid 29/30; P/R/F1 = **.741 / .866 / .798**.
- Interpretation: sparse serialization solves the output-feasibility/truncation
  problem of explicit full-repository plans.
- Artifact: `reports/scientific-stagec-djangocms-study-01/final_metrics.json`.

### E-2 Graph ablation

- OFF (no graph hint): F1 **.7940** (P .721, R .883).
- Hints (graph context): F1 **.8067** (P .814, R .800); precision **+9.2 pp**,
  FP **-19**, total tokens **×2.6**.
- Interpretation: graph hints may improve precision at material token cost; no
  universal graph claim.
- Artifact: `research/graph-c0-c1-c2-01/final_metrics.json`,
  `research/graph-c0-c1-c2-01/interpretation.json`.

### E-3 Oracle-gap bidirectional repair (CLOSED NEGATIVE)

- djangoCMS n=174: F1 **.3177**; Saleor n=149: F1 **.2605**; gate FAIL.
- Interpretation: post-hoc repair not adopted; first-pass recall/ranking
  remained the bottleneck.
- Artifact: `reports/oracle_gap_gates_validation.json` and mission records.

### E-4 Saleor RESERVE-300 (PRIMARY)

- n=300 clean reserve. SIP F1 **.2647**; RM-CSS F1 **.3569**; delta **+.0921**,
  95% CI **[.0691, .1156]** (bootstrap, seed 20260920). Verdict
  `SALEOR_RESERVE_300_RMCSS_PASS`; audit 15/15.
- Interpretation: RM-CSS improves selection quality over SIP on the clean
  Saleor reserve.
- Artifact: `reports/saleor_reserve_300_rmcss_result.json`.

### E-5 MAIN_297 selection (PRIMARY)

- n=297. Pooled file-level F1: Agent **.3631**, RM-CSS **.3568**, SIP **.2652**.
- Interpretation: RM-CSS is close to the bounded repository Agent under the
  frozen selection-only protocol.
- Artifact: `reports/wp1b_main297_result.json`.

### E-6 MAIN_297 efficiency (PRIMARY)

- RM-CSS uses **≈0.2746×** model calls and **≈0.2134×** generation tokens vs
  Agent (view A marginal).
- Interpretation: large interaction/cost reduction under the matched
  selection-only protocol.
- Artifact: `reports/wp1b_main297_result.json` (`cost_view_A_marginal`,
  `cost_sensitivity_not_decisive`).

### E-7 MAIN_297 non-inferiority (PRIMARY)

- Preregistered margin **0.05** supported (`NI_SUPPORTED`); margin **0.03**
  inconclusive at this n.
- Interpretation: selection-only non-inferiority at the 0.05 margin; NOT
  equivalence, NOT superiority.
- Artifact: `reports/wp1b_main297_result.json` (`margin`, `quality_verdict`,
  `sensitivity_margins_not_decisive`).

---

## WP2 — Supporting results

### E-8 Smoke v2.2 (supporting)

- DEV_TRAIN_ENG n=14: **62** generation episodes; APPLIED **50**;
  invalid-after-repair **11**; no-scope **1**.
- Interpretation: E2E pipeline works as an engineering pipeline; no selector
  ranking.
- Artifact: `research/wp2/e2e_smoke_eng_v22/`.

### E-9 Pilot-A (SUPPORTING NEGATIVE)

- 40 episodes: GOLD RESOLVED **0**; PLACEBO RESOLVED **0**.
- Interpretation: generator floor blocks meaningful downstream selector
  comparison.
- Artifact: `research/wp2/pilot_a_v1/`.

### E-10 M14R generator-capability probe (SUPPORTING NEGATIVE)

- 13 members / 4 variants: robust episodes **8/9/8/8** (G0–G3);
  `M14R_FLOOR_NOT_MET`; winner G0 (fallback).
- Interpretation: tested variants did not remove the generator floor.
- Artifact: `research/wp2/m14r_v1/m14r_summary.json`.

### E-11 M15-R OPWS (SUPPORTING DESCRIPTIVE)

- Pilot-B n=10: GOLD **10/10**; RM-CSS **3/10**; Agent r1/r2/r3 = **2/10,
  3/10, 2/10** (OPWS_ROBUST).
- Interpretation: selected scopes show limited reference-patch sufficiency on a
  small pilot; descriptive only.
- Artifact: `research/wp2/m15r_v1/opws_summary.json`.

### E-12 M15-R generation (SUPPORTING NEGATIVE)

- 10 tasks: Gold-solvable **1/10**; robust episodes **3**; S2 gate FAIL
  (`M15R_GOLD_FLOOR_FAIL_NO_GENERATION_CLAIM`); S3 not executed.
- Interpretation: no valid generation-based selector comparison; S3 correctly
  skipped.
- Artifact: `research/wp2/m15r_v1/m15r_summary.json`.

### E-13 M16-v1 (CLOSED PRE-EXPERIMENT / METHOD)

- Adapter preflight failed before R03; **no MAIN OPWS outcome exists**.
- Interpretation: instrument was not qualified for MAIN.
- Artifact: `docs/M16_V1_CLOSURE_2026-10-02.md`,
  `research/wp2/m16_v1/adapter/adapter_report.json`.

---

## Result-status legend

| Status | Meaning |
|---|---|
| PRIMARY | Directly answers the primary research question; claim-bearing |
| SUPPORTING | Downstream/supporting evidence; does not carry the primary claim |
| SUPPORTING DESCRIPTIVE | Descriptive only; no superiority/equivalence claim |
| SUPPORTING NEGATIVE | Negative result; bounds what can be claimed |
| CLOSED NEGATIVE | Not adopted; records a ruled-out direction |
| CLOSED PRE-EXPERIMENT / METHOD | Instrument never qualified; no experiment outcome |

All numbers above trace to the artifact paths in
`docs/EXPERIMENT_LEDGER.md`; interpretation is bound by
`docs/CLAIM_REGISTRY.md`.