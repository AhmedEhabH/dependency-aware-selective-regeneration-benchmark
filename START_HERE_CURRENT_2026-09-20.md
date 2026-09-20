# START HERE - Current Research (2026-09-20)

This file is the entry map. Read it first, then open the referenced documents.
**Terminology:** SIP = Sparse Impact Plan (baseline); RM-CSS =
Repository-Memory Calibrated Set Selection (= SIP + Qwen dense ranking +
parent-only Repository Memory + calibrated ADD/KEEP/DROP). See
`docs/GLOSSARY.md`.

## What this research is

**Question.** Given a real GitHub issue and the repository state at the issue's
parent commit, which files would a developer change? We evaluate the selected
file set against the observed change-set (the actual diff) as an evaluation
proxy. Functional correctness / preservation are deferred until downstream
regeneration.

**Phase.** `Repository change localization / impact selection` — **method
selection CLOSED** (`IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED`). The current
clean evaluation is **`SALEOR_RESERVE_300_RMCSS`** (one Ahmed-authorized
untouched test of exactly 300 Saleor RESERVE tasks; in progress).

## Current position (one paragraph)

The first Stage-5 evaluation (139 tasks, one-shot) was declared
**EXECUTION-INVALID**: `STAGE5_V2_EXECUTION_INVALID_EMBEDDING_COVERAGE_DEFECT`
(a finite -1e9 sentinel was used for Stage-5 blobs missing from the DEV
embedding cache instead of NaN/new embeddings). **Its negative numbers are
HISTORICAL ONLY and must not be used scientifically** (they are NOT evidence
about generalization). The corrected re-execution on the same 139 exposed tasks
is **`STAGE5_CORRECTED_REEXECUTION_POSITIVE`**: pooled SIP F1 ≈ 0.2857,
RM-CSS F1 ≈ 0.3419, Delta F1 ≈ **+0.0562 (95% CI [+0.0185, +0.0945])**. The
corrected 139-task population was **exposed by the invalid run and is therefore
NOT untouched**. The current CLEAN untouched test is
`SALEOR_RESERVE_300_RMCSS`; its **Saleor RESERVE outcomes remain UNREAD** until
the preregistered parity gate passes.

## Read order

| # | File | Why |
|---|---|---|
| 1 | `docs/GLOSSARY.md` | SIP / RM-CSS terminology mapping |
| 2 | `00_CURRENT_RESEARCH_STATE.md` | authoritative scientific truth (top CURRENT TRUTH blocks) |
| 3 | `DECISIONS.md` (P84-P90) | governance + outcomes |
| 4 | `reports/STAGE5_EXECUTION_DEFECT_REPORT_2026-09-20.md` | why the first Stage-5 result is invalid |
| 5 | `reports/STAGE5_CORRECTED_REEXECUTION_2026-09-20.md` | corrected 139-task result (exposed, not untouched) |
| 6 | `reports/SALEOR_RESERVE_300_RMCSS_PREREGISTRATION_2026-09-20.md` | the current clean test preregistration |
| 7 | `docs/RESEARCH_JOURNEY.md` | chronological history (negatives = search-space reductions) |

## Do NOT (hard boundaries)

- Do not use the first Stage-5 FAIL numbers (`STAGE5_V2_FINAL_CONFIRMATION_FAIL`)
  as valid scientific evidence — superseded by P86/P87.
- Do not call the corrected 139-task re-execution untouched confirmation — it is
  `STAGE5_CORRECTED_REEXECUTION_POSITIVE` on an EXPOSED population.
- Do not start a new localization method for the current thesis
  (`IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED`; no V3).
- Do not rewrite historical reports/tags/verdicts:
  `INDEPENDENT_DENSE_RETRIEVAL_REPLICATED`, `CALIBRATED_SET_SELECTION_V1_FAIL`,
  `PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL`,
  `ISSUE_GROUNDED_INTENT_SIGNAL_NOT_SUPPORTED`, invalid Stage-5 FAIL.
- Do not open Saleor RESERVE outcomes until the amended preregistration is
  pushed/tagged AND the label-free parity gate passes.
- Do not compare our Acc@K percentages to external SWE-bench/LocAgent headlines
  as a winner/loser claim.

## ONE next scientific action

Continue the frozen `SALEOR_RESERVE_300_RMCSS` mission in the preregistered
order (SIP 300 → embeddings → RM-CSS features → label-free parity gate →
irreversible checkpoint → open outcomes once → PRIMARY + SECONDARY evaluation →
audits → final tag `saleor-reserve-300-rmcss-final-replication-2026-09-20`).
After closure, the next phase is `END_TO_END_SELECTIVE_REGENERATION`
(Functional Correctness, Preservation, Architecture Compliance, Efficiency) —
prepared as a handoff, NOT executed in this mission.