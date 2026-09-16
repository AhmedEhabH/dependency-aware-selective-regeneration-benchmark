# PROGRESS.md — Execution Source of Truth

**Role:** Execution source of truth (what is being executed now, last completed
task, immediate next step, blockers). Scientific truth lives in
`00_CURRENT_RESEARCH_STATE.md`; decisions are recorded append-only in
`DECISIONS.md`.

**Branch:** `research/omission-risk-sparse-v2-inference-v1` (to be merged into `main`)
**HEAD base:** `15d1b3f` (main, omission-risk milestone closed + DEV tag)
**Model:** openrouter/deepseek/deepseek-v4-flash-0731
**Task:** OMISSION_RISK_FEATURE_STUDY_V1 — registered Sparse-v2-label
development-inference EXECUTED (approved 90-cell run, TRAIN/VALIDATION only;
90/90 valid; 490,747 tokens / $0.184 within the 600,000-token AND $0.30 hard
stop; class-balance gate FAILED → descriptive/single-feature only, no
multivariable RiskScorer).

---

## Now executing

- **REGISTERED SPARSE-v2-LABEL STUDY COMPLETE + AUDITED.** Approved 90-cell
  Sparse-v2 development-inference run on TRAIN/VALIDATION executed: 90/90
  valid, 0 failures, 0 truncations, raw responses + sha256 sidecars persisted
  and verified. Task-level Sparse-v2 `has_fn` prevalence 86.7% (26/30, 4
  negatives); class-balance gate FAILED (neg < 10) → NO multivariable
  RiskScorer; descriptive/single-feature rerun only. Report
  `reports/OMISSION_RISK_SPARSE_V2_INFERENCE_REPORT.md`; audit
  `reports/OMISSION_RISK_INFERENCE_AUDIT.md` (31/31 PASS). Awaiting merge to
  main + DEV tag + export.

## Last completed task

- Sparse-v2 development inference (90 cells) + label computation + feature
  analysis rerun + comparison vs deterministic first pass + final report +
  independent audit (all PASS). Run evidence:
  `research/omission-risk-feature-study-v1/sparse_v2_trainval_*` (+ runs/raw
  sidecars); analysis: `research/omission-risk-feature-study-v1/sparse_v2_label_analysis/`;
  gates: `reports/omission_risk_inference_gates.json`.

## Immediate next step

- **Merge to main + DEV tag + fresh export (fixed hygiene).** Commit →
  push research branch → merge main → post-merge verify → push main → DEV tag
  `omission-risk-sparse-v2-inference-v1-dev-2026-09-16` → fresh export without
  embedding `dist/pilot-kaggle-upload.zip` in a LIGHT export. Then STOP.

## Blockers

- Pre-existing environmental: pinned djangocms git cache absent
  (benchmark_data/repositories/djangocms) — parent-commit corpus not
  re-materializable; documented in the repository evidence audit.