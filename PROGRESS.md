# PROGRESS.md — Execution Source of Truth

**Role:** Execution source of truth (what is being executed now, last completed
task, immediate next step, blockers). Scientific truth lives in
`00_CURRENT_RESEARCH_STATE.md`; decisions are recorded append-only in
`DECISIONS.md`.

**Branch:** `research/cheap-nonllm-baselines-v1`
**HEAD base:** `9b08b5bbfe36af36395686aa8aa8240694f060c4`
**Model:** openrouter/deepseek/deepseek-v4-flash-0731
**Task:** FIRST POST-ICCI EXPERIMENTAL BLOCK — Protocol A: cheap non-LLM
baselines (B0 Random@K, B1 BM25@K, B2 Path/identifier@K, B3 Graph@K, B4
Hybrid@K) on TRAIN 24 + VALIDATION 6 only. T3 classification.

---

## Now executing

- BLOCK COMPLETE — STOP for Ahmed's review per the stop condition.

## Last completed task

- Protocol A implemented, tested (32 unit/integration/leakage tests PASS),
  all six zero-API pre-benchmark gates + independent audit PASS, real
  TRAIN/VALIDATION run complete (`research/cheap-baselines-v1/`),
  `reports/CHEAP_BASELINES_V1_REPORT.md` + `_AUDIT.md` written, Saleor +
  omission-risk protocol drafts written.
- Governance aligned: `DECISIONS.md`, `PROGRESS.md`,
  `docs/EXECUTION_AND_VALIDATION_PROTOCOL_V2.md` created; PROTOCOL_VERSION.md
  CURRENT PHASE = "Repository change localization / impact selection";
  MSc roadmap Pillar 7 (Saleor) + Pillar 8 (Omission-risk) preserved.
- State docs updated; full validation (non-integration 2414 passed / 32 skipped /
  0 failed; affected integration 433 passed; pre-existing Stage-C wiring
  failures only — 2, confirmed pre-existing on HEAD); commit
  `3b83dd6` + pushed (`research/cheap-nonllm-baselines-v1`). No tag yet
  (development evidence; pending Ahmed's review).

## Immediate next step

- **STOP.** Next scientific step chosen after Ahmed reviews the cheap-baseline
  results. Do NOT auto-start Saleor / risk-detector / selective escalation /
  new LLM calls.

## Blockers

- None.