# PROGRESS.md — Execution Source of Truth

**Role:** Execution source of truth (what is being executed now, last completed
task, immediate next step, blockers). Scientific truth lives in
`00_CURRENT_RESEARCH_STATE.md`; decisions are recorded append-only in
`DECISIONS.md`.

**Branch:** `feat/djangocms-confirmatory-p2-program-2026-09-17` (HEAD `7a458bd`;
to merge to `main` as the confirmatory + P2-program milestone)
**Model:** openrouter/deepseek/deepseek-v4-flash-0731
**Task:** DJANGOCMS CONFIRMATORY RUN + P2 FIVE-MONTH ALGORITHM PROGRAM +
PROPOSAL COVER (2026-09-17) — confirmatory INTERNAL_TEST EXECUTED (CONFIRMS),
P2 literature/program underway — **IN PROGRESS (real confirmatory run done;
P2 DEV-only)**

---

## Now executing

- **Block A COMPLETE:** djangoCMS V2 INTERNAL_TEST confirmatory run executed
  (Ahmed-authorized) under the frozen V2 protocol + budget: **560 calls /
  1,470,174 tokens / $0.505917**, 0 failures, 0 excluded; composite ranker
  beats analytic Random at every B with CIs excluding zero; gate PASS →
  **classification CONFIRMS**.
- **Block B IN PROGRESS:** freezing the fixed Route-B story (state/ledgers
  updated; DEV vs CONFIRMATORY vs P2 evidence separated).
- **Remaining:** C. P2 literature landscape; D. P2 roadmap; E. P2 common
  evaluation contract; F. proposal cover/title page; G. timeline alignment;
  H. semantic-audit package; I. traceability/git/release; J. final report.

## Last completed task

- Confirmatory run closure: result report
  (`reports/DJANGOCMS_ROUTE_B_CONFIRMATORY_RESULT.md`), machine JSON
  (`research/djangocms-confirmatory-route-b/confirmatory_metrics.json`), raw
  manifest (560/560 SHA verified), audit
  (`reports/DJANGOCMS_CONFIRMATORY_AUDIT.md`).

## Immediate next step

- Block C: P2 five-month algorithm program — systematic literature landscape
  (Tracks A/B), `reports/P2_ALGORITHM_LANDSCAPE_2026-09.md`,
  `research/literature/p2_algorithm_landscape.csv`, literature ledger update.

## Blockers

- None for this mission.
- Pre-existing environmental: pinned djangocms git cache absent at
  benchmark_data/repositories/djangocms (parent-commit corpus not
  re-materializable for legacy tests; INTERNAL_TEST bundles were materialized
  from dist/real-commit-cache/djangocms instead).
- Saleor parent-visible history cache absent (dist/real-commit-cache/saleor) —
  no Saleor co-change arm; recorded UNAVAILABLE in the ablation.