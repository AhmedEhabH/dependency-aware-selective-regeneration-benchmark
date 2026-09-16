# NEXT PHASE — Dynamic Research Platform + Living Review (2026-09-16)

**Task:** `PLUGGABLE_RESEARCH_HARNESS_V1` + `LIVING_SYSTEMATIC_REVIEW_V1`
**Classification:** T3 (new evaluation strategy / reusable experiment architecture).
This task introduces reusable experiment architecture; it is NOT a new
scientific experiment and produces no new scientific model/API calls.

**Model executing:** openrouter/deepseek/deepseek-v4-flash-0731
**Branch basis:** `main` @ `0ba7a1a` (clean tree; cheap-baselines block closed).

---

## 1. Purpose

The selection-stage benchmark and the cheap-baseline block produced frozen,
audited evidence but the research harness was hard-coded in places to one
repository (djangoCMS), one model route, one selection method and one K grid.
This milestone generalizes the harness minimally through explicit seams so the
next scientific step (**Omission-Risk Feature Study v1 — TRAIN/VALIDATION only**)
can be executed without rewriting frozen machinery, and so a living systematic
review exists as the proposal/literature base.

## 2. Goals (A–E)

- **A.** Minimally generalize the research harness: not hard-coded to one
  repository, model provider, selection method, K, or future verifier.
- **B.** Preserve all frozen scientific evidence byte-for-byte.
- **C.** Create a living systematic-review artifact + initial competitor matrix.
- **D.** Reproduce current Protocol-A cheap-baseline outputs through the
  compatibility layer (output-equivalence regression).
- **E.** Prepare the codebase for Omission-Risk Feature Study v1.

## 3. Required architecture seams

`DatasetAdapter`, `RepositoryView/SnapshotProvider`, `Ranker`, `Planner`,
`ModelBackend`, `RiskScorer` (interface only), `Verifier` (interface only),
`BudgetPolicy`, common `Evaluator`, versioned `ExperimentSpec`.

Rules:
- do NOT build a universal plugin framework;
- prefer Python `Protocol`/`ABC` + config;
- django-specific rules stay in a django adapter;
- future Saleor-specific rules stay in a Saleor adapter;
- method code cannot read hidden gold;
- model/provider names are config, not algorithm branches;
- budget is explicit and persisted;
- frozen historical generators/artifacts must not be rewritten.

## 4. Deliverables

| Artifact | Path |
|---|---|
| Harness package | `src/benchmark/harness/` |
| Living review doc | `docs/LIVING_SYSTEMATIC_REVIEW.md` |
| Competitor matrix | `research/literature/review_matrix.csv` |
| Search log | `research/literature/search_log.csv` |
| Idea ledger | `research/literature/idea_ledger.md` |
| Gate + audit reports | `reports/RESEARCH_HARNESS_V1_REPORT.md`, `_AUDIT.md`, `reports/research_harness_v1_gates.json` |
| Verification script | `scripts/verify_research_harness_v1.py` |
| Equivalence runner | `scripts/run_harness_protocol_a_equivalence.py` |

## 5. Validation (T3, all ZERO-API)

Six T3 gates + interface contract tests + hidden-gold access test + config
reproducibility test + Protocol-A output-equivalence regression + deterministic
ranking test + budget enforcement test + dataset-adapter isolation test. No new
scientific API/model calls.

## 6. Governance

Update `00_CURRENT_RESEARCH_STATE.md`, `PROGRESS.md`, `DECISIONS.md`,
`SYSTEM_STATE.md`, `TODO.md`, `docs/MSC_RESEARCH_ROADMAP_2026_2027.md`,
`README.md`. Maintain one current scientific source of truth. Merge audited
work to `main`; post-merge verification; DEV tag only if fully reproducible;
fresh light ZIP after merge/tag.

## 7. STOP CONDITION

After the harness + review foundation are complete and audited, STOP. Do NOT
start: omission-risk training/analysis, Saleor scientific execution, LocAgent
scientific calls, selective escalation, new model runs.