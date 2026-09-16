# PROGRESS.md — Execution Source of Truth

**Role:** Execution source of truth (what is being executed now, last completed
task, immediate next step, blockers). Scientific truth lives in
`00_CURRENT_RESEARCH_STATE.md`; decisions are recorded append-only in
`DECISIONS.md`.

**Branch:** `research/harness-v1-living-review-01` (to be merged into `main`)
**HEAD base:** `0ba7a1a` (main, cheap-baselines block closed + DEV tag)
**Model:** openrouter/deepseek/deepseek-v4-flash-0731
**Task:** PLUGGABLE_RESEARCH_HARNESS_V1 + LIVING_SYSTEMATIC_REVIEW_V1 — T3
reusable experiment architecture (NOT a new scientific experiment; ZERO new
scientific API/model calls).

---

## Now executing

- **BLOCK COMPLETE AND CLOSED** — PLUGGABLE_RESEARCH_HARNESS_V1 +
  LIVING_SYSTEMATIC_REVIEW_V1 merged to `main`; post-merge verification PASS;
  DEV tag `research-harness-v1-dev-2026-09-16` created (peels to merge commit
  `4eb8dcc` == `main`); light export `project-2026-09-16-0443.zip` created +
  verified. STOP.

## Last completed task

- Harness + review foundation complete and audited; see
  `reports/RESEARCH_HARNESS_V1_REPORT.md` / `_AUDIT.md`. Full Protocol-A
  equivalence (600 rows) byte-identical; 44 new tests; gates 97/97 checks PASS;
  full suite 3270 passed / 33 skipped / 2 pre-existing environmental failures
  (missing pinned djangocms repo checkout).

## Immediate next step

- **STOP.** ONE next scientific step (NOT started, not authorized without
  review): **OMISSION_RISK_FEATURE_STUDY_V1 (TRAIN/VALIDATION only)** — feature
  families + routing metrics per `reports/RESEARCH_HARNESS_V1_REPORT.md` §9 and
  `research/literature/idea_ledger.md` I1/I2/I5/I6. Do NOT auto-start
  omission-risk training/analysis, Saleor scientific execution, LocAgent
  scientific calls, selective escalation, or new model runs. Pending:
  authorization to push `main` + the DEV tag to `origin`.

## Blockers

- None (2 full-suite failures are pre-existing environmental: pinned
  `benchmark_data/repositories/djangocms` checkout absent; confirmed identical
  on clean base).