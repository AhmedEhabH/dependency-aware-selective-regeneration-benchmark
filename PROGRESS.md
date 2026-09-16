# PROGRESS.md — Execution Source of Truth

**Role:** Execution source of truth (what is being executed now, last completed
task, immediate next step, blockers). Scientific truth lives in
`00_CURRENT_RESEARCH_STATE.md`; decisions are recorded append-only in
`DECISIONS.md`.

**Branch:** `research/omission-risk-feature-study-v1` (to be merged into `main`)
**HEAD base:** `a973a2a` (main, research-harness milestone closed + DEV tag)
**Model:** openrouter/deepseek/deepseek-v4-flash-0731
**Task:** OMISSION_RISK_FEATURE_STUDY_V1 — T3 feature-family study (ZERO new
scientific LLM/API calls; deterministic-first-pass development analysis
COMPLETE; registered Sparse-v2-label study DEFERRED).

---

## Now executing

- **BLOCK COMPLETE AS A DEVELOPMENT ANALYSIS.** The Omission-Risk Feature Study
  V1 milestone is closed: Phase-B preflight A–G + six T3 gates + independent
  audit PASS; deterministic-first-pass development analysis (metadata-corpus
  BM25@K, 83 features, n=30) reported with a near-chance result; registered
  Sparse-v2-label study DEFERRED. Awaiting Ahmed's decision on the frozen
  DEVELOPMENT-INFERENCE protocol (`docs/OMISSION_RISK_DEVELOPMENT_INFERENCE_PROTOCOL.md`;
  90-cell Sparse-v2 run, ~$0.19). No LLM call will be made without approval.

## Last completed task

- Omission-Risk Feature Study V1 (deterministic-first-pass development
  analysis): `research/omission-risk-feature-study-v1/*`, reports
  `reports/OMISSION_RISK_FEATURE_STUDY_V1_REPORT.md` / `_AUDIT.md`,
  `reports/OMISSION_RISK_REPOSITORY_EVIDENCE_AUDIT.md`,
  `docs/OMISSION_RISK_DEVELOPMENT_INFERENCE_PROTOCOL.md`; 19 new unit tests;
  ruff + mypy clean; gates JSON persisted
  (`reports/omission_risk_feature_study_v1_gates.json`). Literature: Shichao
  Zhang line + 8 priority rows verified (living review V1.1).

## Immediate next step

- **STOP / AWAIT DECISION.** Review `docs/OMISSION_RISK_DEVELOPMENT_INFERENCE_PROTOCOL.md`
  and approve (or reject) the 90-cell Sparse-v2 development-inference run on
  TRAIN/VALIDATION (~$0.19) — OR accept the deterministic-first-pass
  development evidence as the delivered output and defer the registered study.
  Do NOT start omission-risk training, Saleor scientific execution, LocAgent
  scientific calls, selective escalation, or new model runs.

## Blockers

- None for the delivered development analysis. New scientific LLM/API calls are
  BLOCKED pending Ahmed's approval of the DEVELOPMENT-INFERENCE protocol.
- Pre-existing environmental: pinned djangocms git cache absent
  (benchmark_data/repositories/djangocms) — parent-commit corpus not
  re-materializable; documented in the repository evidence audit.