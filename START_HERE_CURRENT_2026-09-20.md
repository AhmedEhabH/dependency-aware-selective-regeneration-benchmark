# START HERE - Current Research (2026-09-20)

This file is the entry map. Read it first, then open the referenced documents.

## What this research is

**Question.** Given a real GitHub issue and the repository state at the issue's
parent commit, which files would a developer change? We evaluate the selected
file set against the observed change-set (the actual diff) as an evaluation
proxy. Functional correctness / preservation are deferred until downstream
regeneration.

**Phase.** `Repository change localization / impact selection` — **method
selection now CLOSED by the one-shot Stage-5 confirmation.**

## Current position (one paragraph)

After the five-day method-search cycle, the single best frozen DEV candidate
(Repository Memory V2) was frozen, preregistered, and evaluated **ONCE** on
untouched evidence (djangoCMS RESERVE 59 + Saleor INTERNAL_TEST 80, n=139).
**`STAGE5_V2_FINAL_CONFIRMATION_FAIL`**: pooled V2 F1 0.2269 vs Sparse 0.2857;
Delta F1 **−0.0588 (95% CI [−0.1119,−0.0084])**, both repositories negative.
The V2 improvement did NOT survive the untouched confirmation; Sparse is more
precise and more sensitive on the confirmatory population.
`IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED`. The thesis now reports Sparse,
dense recovery, V1, V2, the untouched confirmation outcome, and limitations.

## Read order

| # | File | Why |
|---|---|---|
| 1 | `reports/STAGE5_V2_FINAL_CONFIRMATORY_REPORT_2026-09-20.md` | the one-shot confirmation result |
| 2 | `reports/STAGE5_FINAL_PREREGISTRATION_2026-09-20.md` | what was frozen before unsealing |
| 3 | `00_CURRENT_RESEARCH_STATE.md` | authoritative scientific truth (top CURRENT TRUTH blocks) |
| 4 | `DECISIONS.md` (P84/P85) | governance + outcome |
| 5 | `reports/LOCAGENT_NATIVE_METRIC_COMPATIBILITY_2026-09-20.md` | Acc@K compatibility facts |
| 6 | `docs/RESEARCH_JOURNEY.md` | chronological history (negatives = search-space reductions) |

## Do NOT (hard boundaries)

- Do not open or re-run the Stage-5 confirmatory tasks (one look only).
- Do not start a new localization method for the current thesis
  (`NO_FURTHER_LOCALIZATION_METHOD_SHOPPING_FOR_CURRENT_THESIS`).
- Do not rewrite any frozen verdict: `INDEPENDENT_DENSE_RETRIEVAL_REPLICATED`,
  `CALIBRATED_SET_SELECTION_V1_FAIL`, `PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL`,
  `ISSUE_GROUNDED_INTENT_SIGNAL_NOT_SUPPORTED`, `STAGE5_V2_FINAL_CONFIRMATION_FAIL`.
- Do not open the remaining sealed sets (djangoCMS RESERVE remainder, Saleor
  RESERVE). Do not run Stage 5 again.
- Do not compare our Acc@K percentages to external SWE-bench/LocAgent
  headlines as a winner/loser claim.

## ONE next scientific action

With explicit authorization in a SEPARATE mission: execute
`EXTERNAL_VALIDITY_AND_END_TO_END_REGENERATION` (cross-repository/language
transfer, downstream code regeneration, functional correctness, preservation,
architecture compliance, end-to-end efficiency). Until then, the current phase
is `THESIS_AND_PAPER_EVIDENCE_CLOSURE`.