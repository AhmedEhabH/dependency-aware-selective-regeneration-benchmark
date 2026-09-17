# P2 Phase-1 Major Science Mission — Closure Report

**Date:** 2026-09-18
**Branch:** `main` (pre-merge; this report precedes the release step)
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731
**Mission:** OPENCODE_P2_PHASE1_MAJOR_SCIENCE_MISSION_2026-09-18
**Classification:** **CLOSED — fixed Route-B reviewer closure COMPLETE (ZERO
API); P2 Phase-1 = NEGATIVE (frozen); stronger methods NOT run (pre-registered
gate); literature expanded; semantic-audit blocker = AWAITING_HUMAN_RATINGS**

---

## 1. Executive verdict

The fixed Route-B reviewer-facing issues are closed WITHOUT changing the frozen
result: a curve-level POST-HOC characterization, a sparse-vs-full causal parity
audit (PARITY_VERIFIED), and a dataset operational-definition audit were
produced. The P2 Phase-1 common adaptive-budget DEVELOPMENT harness was built,
the four pre-registered policies (P2-P1..P2-P4) were implemented and evaluated
on djangoCMS DEV + Saleor DEV with ZERO new model calls, and the pre-registered
strong-method gate was FALSE — so the P2 Phase-1 result is **NEGATIVE** and is
frozen as a valid scientific result; the two stronger methods were NOT
implemented per mission §4. The literature landscape was expanded with 15
verified additions. The semantic-audit scientific blocker is reported
(AWAITING_HUMAN_RATINGS). Sealed sets remain sealed.

## 2. Scientific question

> Can an observable adaptive budget policy choose B_t per task so that expected
> omission recovery is comparable to or better than fixed-B while using fewer
> verifier candidates/calls/tokens/cost?

Answered on DEVELOPMENT (djangoCMS 174 + Saleor 149 tasks): **No** — under the
frozen composite ranker + measured verifier cost model, none of the four
pre-registered interpretable policies achieves comparable recovery at lower
cost on BOTH repositories.

## 3. Dataset / split and forbidden data

- djangoCMS DEV: DEV_TRAIN 117 + DEV_VALIDATION 27 + V1_DEV 30 = 174 tasks.
- Saleor DEV: 149 tasks.
- Constants derived on djangoCMS DEV_TRAIN ONLY; validated unchanged on
  DEV_VALIDATION + Saleor DEV.
- FORBIDDEN and untouched: opened djangoCMS INTERNAL_TEST (used only for frozen
  Route-B reporting), djangoCMS RESERVE, Saleor INTERNAL_TEST, Saleor RESERVE.

## 4. Validation-gate table

| Gate | Result | Evidence |
|---|---|---|
| 1 Dataset | PASS | counts 174/149; sealed sets not loaded |
| 2 Input/observable | PASS | PolicyView has no gold; all tasks have candidates |
| 3 Pipeline smoke | PASS | subset run + determinism |
| 4 Dry run | PASS | frozen_constants/results/per_task artifacts |
| 5 Integration | PASS | anchors reproduce frozen route_b_v2/transfer (tol 0.02) |
| 6 Metric verification | PASS | synthetic TP/FP/FN unit tests |
| Independent audit | PASS | `reports/P2_PHASE1_INDEPENDENT_AUDIT.md` |
| Gates JSON | PASS | `reports/p2_phase1_gates_validation.json`, `p2_phase1_gates.json` |

## 5. Main result table (P2, per repo, realized budget)

| Policy | djangoCMS mean B_t | djangoCMS macro ORR | Saleor mean B_t | Saleor macro ORR |
|---|---:|---:|---:|---:|
| fixed-B1 (anchor) | 1.0 | 0.0464 | 1.0 | 0.0775 |
| fixed-B3 (anchor) | 3.0 | 0.1177 | 3.0 | 0.1576 |
| fixed-B5 (anchor) | 5.0 | 0.1633 | 5.0 | 0.2369 |
| fixed-B10 (anchor) | 10.0 | 0.2512 | 10.0 | 0.3173 |
| P2-P1 score-gap | 1.61 | 0.0775 | 1.52 | 0.1151 |
| P2-P2 marginal-score | 8.47 | 0.2389 | 9.95 | 0.3173 |
| P2-P3 cost-ratio (tau=0.5) | 1.00 | 0.0464 | 9.03 | 0.2918 |
| P2-P4 learning-k analogue | 8.45 | 0.2389 | 9.94 | 0.3139 |

Metric definition: macro ORR @ realized B_t = mean over tasks of
(recovered Sparse-observed FNs within top-B_t of the frozen composite ranking /
all Sparse-observed FNs for that task); zero-FN tasks contribute 0 (frozen rule).

## 6. Development vs confirmatory label

ALL P2 evidence is **DEVELOPMENT** (djangoCMS DEV + Saleor DEV). Nothing is
confirmatory. The fixed Route-B confirmatory result (CONFIRMS) is unchanged and
reported only in its frozen form; the post-hoc characterization is labelled
POST-HOC.

## 7. Fair-comparison warning

P2 adaptive policies are compared against fixed-B anchors under the SAME frozen
composite ranker, the SAME measured cost model, and the SAME task unit. No
cross-split head-to-head with the opened INTERNAL_TEST is made; that set is
spent and excluded from P2 selection by design.

## 8. Interpretation

- P2-P1 stops early (mean B_t ≈ 1.5–1.6) because the composite score tail is
  sparse (58% zeros), losing ~half the fixed-B5 recovery for a marginal cost
  saving.
- P2-P2/P2-P4 converge to B_t ≈ 8.5–10, matching fixed-B10 at NO cost saving.
- P2-P3 is repo-asymmetric (djangoCMS stops at B_t=1, Saleor at B_t≈9 for the
  same tau) — a size/universe artifact, hence REJECTED_BY_DESIGN.
- The measured verifier cost model is dominated by a fixed per-call overhead
  (≈205 tokens), so within B∈[1,10] the cost lever is small; the recovery lever
  is large. A useful adaptive policy would need to recover like B=10 at a
  budget near B=3 — none of the four does on both repos.

## 9. What the result does NOT mean

- It does NOT mean fixed-B is worse than Sparse (the CONFIRMED Route-B result
  stands).
- It does NOT mean no adaptive policy could ever help — only that this
  pre-registered interpretable family does not on DEVELOPMENT.
- It does NOT validate a negative for Shichao-Zhang-style ideas in general
  (P2-P4 is a specific analogue; the landscape now maps 15 further options for
  Phase 2).
- The cost model is NOT provider-billed truth; it is a measured relative model.

## 10. Competitor/baseline implication

Within the shared-protocol, budget-matched comparison, fixed-B remains the
default operating point. The negative P2 Phase-1 result strengthens the
honesty of the thesis: adaptive B_t is reported as not-yet-justified, while the
fixed-B confirmatory line is the defended contribution.

## 11. Threats / caveats

- Single-model family (qwen/qwen3-coder) for the frozen Sparse first pass.
- Cost model measured on the confirmatory verifier (INTERNAL_TEST) but applied
  to DEV tasks for relative accounting — a modelling choice, not billing.
- The composite score tail sparsity (58% zeros) limits score-gap/marginal rules
  — a data-regime property, not a universal conclusion.
- P2-P3 rejection is driven by size asymmetry; a size-normalized alternative
  was not explored (Phase 2 candidate).
- Semantic audit remains human-blocked.

## 12. Tests / audit

- 31 new P2 tests (15 policy unit + 10 evaluator unit + 6 integration) PASS.
- Validation gates 6/6 PASS + independent audit PASS.
- Pre-existing suite re-run at the final gate.

## 13. Documentation changed

- `reports/ROUTE_B_CURVE_LEVEL_POSTHOC_CHARACTERIZATION.md` (+ JSON in
  research/djangocms-confirmatory-route-b/)
- `reports/SPARSE_FULL_CAUSAL_PARITY_AUDIT.md`
- `reports/DATASET_OPERATIONAL_DEFINITIONS.md`
- `reports/P2_PHASE1_HARNESS_RESULTS.md`, `P2_PHASE1_DECISION_GATE.md`,
  `P2_POLICY_SPECIFICATIONS.md`, `P2_PHASE1_INDEPENDENT_AUDIT.md`
- `reports/P2_ALGORITHM_LANDSCAPE_2026-09.md` (expanded §7)
- `reports/LITERATURE_DECISION_LEDGER.md` (expansion entry)
- `reports/SEMANTIC_AUDIT_ACTION_REQUIRED_FROM_HUMANS.md`
- `reports/NESTJS_READINESS_ZERO_API_2026-09-18.md`
- `reports/V15_SUPERVISOR_PATCH_LIST.md`
- `research/literature/p2_algorithm_landscape.csv` (24 → 39 rows)
- `research/p2-phase1/{frozen_constants,results_summary,per_task_rows}.json`
- `reports/p2_phase1_gates.json`, `reports/p2_phase1_gates_validation.json`
- Code: `src/benchmark/p2/*`, `scripts/p2_phase1_run.py`,
  `scripts/p2_phase1_gates.py`, `scripts/route_b_curve_level_posthoc.py`
- Tests: `tests/unit/test_p2_policies.py`, `tests/unit/test_p2_evaluate.py`,
  `tests/integration/test_p2_harness.py`

## 14. Git / main status

Pre-merge on `main` at HEAD `ae885cf`. Release step (branch → commit → push →
merge → verify → tag → export) is the next step.

## 15. Merge / tag

Pending the release step. Planned: descriptive milestone tag after merge and
verification.

## 16. Export

Pending the release step (LIGHT export after tag).

## 17. Where we are now

P2 Phase-1 scientific execution is COMPLETE and closed (negative). Remaining:
validation final gate, traceability updates, git/merge/tag, LIGHT export, and
the final report.

## 18. ONE next action

Execute the release step: update PROGRESS/DECISIONS/00_CURRENT_RESEARCH_STATE/
roadmap + ledgers, run the full test suite, branch, commit, push, merge to
`main`, verify, tag (`p2-phase1-negative-closure-2026-09-18`), LIGHT export,
and deliver the final report.