# PROGRESS.md — Execution Source of Truth

**Role:** Execution source of truth (what is being executed now, last completed
task, immediate next step, blockers). Scientific truth lives in
`00_CURRENT_RESEARCH_STATE.md`; decisions are recorded append-only in
`DECISIONS.md`.

**Branch:** `research/cheap-nonllm-baselines-v1` (merged into `main`)
**HEAD base:** `9b08b5bbfe36af36395686aa8aa8240694f060c4`
**Model:** openrouter/deepseek/deepseek-v4-flash-0731
**Task:** FIRST POST-ICCI EXPERIMENTAL BLOCK — Protocol A: cheap non-LLM
baselines (B0 Random@K, B1 BM25@K, B2 Path/identifier@K, B3 Graph@K, B4
Hybrid@K) on TRAIN 24 + VALIDATION 6 only. T3 classification.

---

## Now executing

- **BLOCK COMPLETE AND CLOSED** — Protocol-A finalization (interpretation
  corrections, sensitivity diagnostic, report rewrite, milestone-format patch,
  docs sync, merge to main, DEV tag, light export).

## Last completed task

- Protocol A implemented, tested (32 unit/integration/leakage tests PASS +
  5 new sensitivity tests), all six zero-API pre-benchmark gates + independent
  audit PASS (now including the path-mention sensitivity audit assertions),
  real TRAIN/VALIDATION run complete (`research/cheap-baselines-v1/`).
- **Finalization:** over-strong BM25-vs-LLM claim corrected to the safe wording
  (BM25 = meaningful zero-LLM localization signal on development data; LLM
  comparison untested under a shared fresh confirmatory protocol); K presented
  as an operating-point curve (VALIDATION primary table: BM25@3 F1 0.279
  precision point, BM25@10 F1 0.306 recall point), not a final config;
  path-mention sensitivity diagnostic (3 TRAIN cases) computed + persisted +
  tested (material ordering unchanged; frozen dataset untouched); graph/hybrid/
  efficiency interpretations bounded; `reports/CHEAP_BASELINES_V1_REPORT.md`
  rewritten A–T; `docs/EXECUTION_AND_VALIDATION_PROTOCOL_V2.md` §9.2 detailed
  closure-format exception added.
- State docs synchronized (00_CURRENT_RESEARCH_STATE, PROGRESS, DECISIONS P10
  superseding P9, SYSTEM_STATE, TODO, MSc roadmap).
- Commit + push research branch; merge into `main`; rerun tests + audit after
  merge; push `main`; verify `main == origin/main`; tag
  `cheap-baselines-v1-dev-2026-09-16` (DEV evidence only) created + pushed;
  light export recreated after merge/tag.

## Immediate next step

- **STOP.** Next scientific step chosen after Ahmed reviews the closure: the
  recommended next step is **design + freeze the omission-risk detection
  protocol** on TRAIN/VALIDATION (fixing the BM25 operating point by a primary
  selection objective), then bounded/selective graph verification, then a
  FRESH confirmatory LLM-vs-BM25 comparison (Saleor or new non-exposed split).
  Do NOT auto-start Saleor / risk-detector / selective escalation / new LLM
  calls.

## Blockers

- None.