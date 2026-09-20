# CLEAN SALEOR RESERVE REPLICATION - DRAFT PREREGISTRATION (2026-09-20)

**Status:** DRAFT ONLY - PREPARE ONLY. NOT EXECUTED. NOT AUTHORIZED.
**Marker:** `CLEAN_SALEOR_RESERVE_REPLICATION_AWAITS_AHMED_AUTHORIZATION`
**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731
**Mission reference:** STAGE-5 EXECUTION DEFECT correction (mission §19)

This document prepares a draft preregistration for a FUTURE clean untouched
replication on Saleor RESERVE. It must NOT be executed in this mission. It
opens NO sealed data, samples NO labels, and builds NO target-aware artifacts.

---

## 0. Why this exists

The corrected Stage-5 re-execution (this mission) ran on the SAME 139 tasks
that were exposed by the original (now invalid) Stage-5 evaluation. Those 139
tasks are NOT untouched. The only untouched population remaining in the current
benchmark split is **Saleor RESERVE** (1,086 tasks). A clean untouched
confirmation therefore requires a fresh frozen pipeline + a fresh untouched
sample from Saleor RESERVE.

## 1. Why NO new djangoCMS confirmation exists

The 59 djangoCMS RESERVE tasks were already exposed (used in the original and
corrected Stage-5 runs). There is NO remaining untouched djangoCMS confirmation
population in the current benchmark split. A future clean djangoCMS
confirmation would require:
- a newly mined frozen population; or
- a different untouched repository/time slice; or
- a new benchmark construction mission.
This mission does NOT perform any of those.

## 2. Proposed future design (for Ahmed's review)

- **Repository:** Saleor only (the only repository with an untouched sealed
  population in the current split).
- **Population:** seeded random sample of **150 Saleor RESERVE tasks**.
- **Sampling seed:** `20260920`.
- **Pipeline:** the frozen CORRECTED V2 pipeline (embedding-coverage-corrected;
  identical frozen scientific inputs: Qwen realization A, unit splitter, file
  aggregation, 11 features, scaler, LR coefficients, LR intercept, threshold
  0.20, candidate constants, parent-only history rules).
- **Pre-run gate:** the SAME label-free parity gate
  (`reports/stage5_parity_gate.json` checks) + independent parity audit.
- **Comparator:** Sparse (persisted write sets generated fresh for the 150
  tasks with the frozen Sparse-v2 strategy).
- **Primary endpoint:** repo-stratified pooled Delta F1 (V2 minus Sparse),
  task-paired bootstrap 10,000 resamples, seed 20260920.
- **No method changes.** No refit. No retuning. `IMPACT_LOCALIZATION_METHOD_
  SELECTION_CLOSED` holds.

## 3. Projected cost / resource estimates (NO execution)

Estimates assume the same frozen pricing ($0.01/M Qwen embeddings @ DeepInfra;
Sparse qwen3-coder route) and DEV/Stage-5-observed per-task magnitudes.

| item | estimate |
|---|---|
| Sparse write sets (150 tasks, qwen3-coder) | ~150 calls; ~1.84M tokens; ~$0.59 |
| Qwen query embeddings (150) | ~6,300 tokens; ~$0.00006 |
| New code-unit embeddings (blobs unseen in DEV/Stage-5 caches) | ~1,500-2,000 units; ~2-3M tokens; ~$0.02-0.03 |
| Total projected paid | ~$0.61-0.62 (dominated by Sparse) |
| Wall time | Sparse ~hours; dense scoring + memory ~1-2 h local |

A hard paid ceiling would be frozen BEFORE execution (e.g. $1.00 like the
original Stage-5 preregistration, or a tighter ceiling at Ahmed's discretion).

## 4. Governance requirements (for the future mission)

- New P-decision recorded append-only BEFORE any sample/label access.
- Preregistration committed/pushed/tagged BEFORE unsealing the 150 sampled
  RESERVE tasks.
- Same label-free parity gate before the evaluator loads labels.
- Result label: PASS/FAIL/MIXED per the frozen success rule (A and B).
- Saleor RESERVE population would be partially consumed (150 of 1,086) and must
  be treated as exposed thereafter.

## 5. NOT AUTHORIZED in this mission

- Opening Saleor RESERVE.
- Sampling Saleor RESERVE labels.
- Building target-aware artifacts.
- Executing any part of this draft.

**Marker: `CLEAN_SALEOR_RESERVE_REPLICATION_AWAITS_AHMED_AUTHORIZATION`**