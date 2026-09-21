# Impact Declaration — wp1a-selection-baseline-preparation

**Date:** 2026-09-21
**Branch:** `feat/wp1a-selection-baseline-preparation`
**Tier:** T3 (freezes scientific harness semantics, data-flow leakage
boundaries, accounting and future experiment invariants)
**Scientific API spend:** $0.00 (this work package makes NO paid scientific
model/API call; no repository-agent scientific execution; no scoring of future
main n=50 agent predictions; no WP-1b / WP-2 / G6 / Smoke / Pilot / E2E
regeneration / cross-language work).
**Status:** PREPARATION ONLY — WP-1b remains AWAITING_AHMED_AUTHORIZATION.

This declaration is recorded BEFORE any edit in this work package, per the
WP-1a task contract section 1.

---

## 1. Purpose

Prepare WP-1 scientifically and mechanically so a later paid WP-1b can run a
same-protocol Repository-Agent vs SIP vs RM-CSS selection-only comparison
without hidden model mismatch, label leakage, re-derivation drift, biased
sample selection, or ambiguous accounting.

## 2. Artifacts / features affected

- **NO scientific localization method is changed.** SIP, RM-CSS, the frozen
  deployment artifact, the frozen threshold, the frozen 11-feature RM-CSS
  schema, realization A, parent-only memory artifacts are READ-ONLY frozen
  inputs.
- **NO production runtime change is required** unless the minimal harness
  audit below finds a label-free parent-state boundary defect in the existing
  iterative repository agent. The current agent (`IterativeRepositoryAgentStrategy`
  in `src/benchmark/strategies/iterative_agent.py` + `RepositoryTools` in
  `repository_tools.py`) is expected to already satisfy the parent-only
  boundary (WP-0/G7 closed runner-level leakage); the WP-1a audit verifies and
  freezes it with mock/stub backends only.

## 3. Dependencies affected

- **Direct dependency on frozen Saleor-300 artifacts** (read-only):
  `research/saleor-reserve-300-rmcss/sip_300_run_records.jsonl`,
  `candidate_rows_saleor300.parquet`,
  `full_file_scores_saleor300.parquet`,
  `memory_bundles_saleor300.json`,
  `saleor_reserve_300_sample.json` / `.txt`,
  `saleor_reserve_300_proxies.json`,
  `django_only_rmcss_transfer_model.json`,
  `reports/saleor_reserve_300_rmcss_result.json` (+ audit),
  `research/stage5-v2-final/deployment_artifact.json`.
- **No dependency on the 786 unread Saleor RESERVE outcomes.** They are not
  accessed, listed, or scored.

## 4. Exact files expected to change / be created

New files (this branch):

- `docs/WP1A_IMPACT_DECLARATION_2026-09-21.md` (this file)
- `docs/WP1_REPOSITORY_AGENT_SELECTION_ONLY_BASELINE_DRAFT.md` — amended ONLY
  to (a) correct the scientific model claim to the mechanically-verified
  SIP model identity, (b) mark WP-1a preparation complete, (c) keep
  DO_NOT_EXECUTE. No scientific contract change.
- `research/wp1a/sip_scientific_model_provenance.json` — Correction A
  (machine-readable SIP scientific model/provider provenance).
- `research/wp1a/wp1a_label_free_schema.json` — Correction B label-free
  prediction view/schema.
- `research/wp1a/sip_rmcss_per_task_predictions.json` — Correction C frozen
  per-task prediction artifact (SIP predicted set, RM-CSS predicted set,
  task IDs, prediction hashes, source/config/model hashes).
- `research/wp1a/sip_rmcss_per_task_predictions.sha256` — SHA-256 manifest.
- `research/wp1a/wp1_rederivation_verification.json` — exact 300-task
  reproduction check result.
- `research/wp1a/wp1_main_50_manifest.json` — deterministic main n=50 freeze.
- `research/wp1a/wp1_calibration_3_manifest.json` — deterministic calibration
  n=3 freeze (disjoint from main 50).
- `research/wp1a/wp1a_intent_parity.json` — per-task intent hash/source/task
  identifiers for main + calibration sets.
- `research/wp1a/wp1a_frozen_agent_protocol.json` — frozen future-execution
  repository-agent protocol.
- `research/wp1a/wp1a_failure_semantics.json` — pre-registered failure
  semantics.
- `research/wp1a/wp1a_shared_scorer_schema.json` — shared scorer metric/stat
  contract.
- `research/wp1a/wp1a_accounting_schema.json` — efficiency accounting schema
  (two RM-CSS cost views).
- `research/wp1a/wp1a_budget_model.json` — label-free budget feasibility model
  + recommended future ceiling.
- `research/wp1a/wp1a_cost_quality_categories.json` — pre-registered outcome
  categories.
- `research/wp1a/wp1a_independent_audit.json` — same-session
  alternate-implementation cross-check result (TERMINOLOGY CORRECTED
  2026-09-21; not an independent/external audit).
- `research/wp1a/wp1a_acceptance_report.json` — AC-1A.1..12 report.
- `scripts/wp1a_*.py` — generation/verification/audit scripts (one per
  deliverable).
- `tests/unit/test_wp1a_*.py` — targeted tests.
- `selective_updates/records/SU-0013-repository-agent-selection-baseline-preparation.md`
  — selective update record (SU-0013 verified free; highest existing is
  SU-0012).
- `DECISIONS.md` — append-only entry (Decision WP1A).
- `PROGRESS.md` — current state update.

Possibly (only if the minimal harness audit finds a boundary defect, then
minimal harness fix + mock test only):

- `src/benchmark/strategies/iterative_agent.py` and/or
  `src/benchmark/strategies/repository_tools.py` (minimal label-free
  parent-state boundary fix).

## 5. Documentation / governance files

- `docs/WP1_REPOSITORY_AGENT_SELECTION_ONLY_BASELINE_DRAFT.md` (model
  correction + status note only)
- `DECISIONS.md` (append-only)
- `PROGRESS.md` (current state)
- `00_CURRENT_RESEARCH_STATE.md` — NOT modified in this WP (the state file
  records scientific results; WP-1a produces no scientific result). If a
  governance note is required it is recorded in PROGRESS.md/DECISIONS.md only.

## 6. Tests / scripts to add

- `tests/unit/test_wp1a_model_provenance.py` (Correction A)
- `tests/unit/test_wp1a_label_isolation.py` (Correction B)
- `tests/unit/test_wp1a_rederivation.py` (Correction C)
- `tests/unit/test_wp1a_sample_freeze.py` (main-50/cal-3 + disjointness)
- `tests/unit/test_wp1a_intent_parity.py`
- `tests/unit/test_wp1a_frozen_protocol.py` (protocol completeness +
  mock-executability against parent-only boundary)
- `tests/unit/test_wp1a_shared_scorer.py`
- `tests/unit/test_wp1a_accounting.py`
- `tests/unit/test_wp1a_budget_model.py`
- `tests/unit/test_wp1a_cost_quality_categories.py`
- `tests/unit/test_wp1a_independent_audit.py`
- `tests/unit/test_wp1a_acceptance.py`

Affected regressions re-run: existing WP-0 leakage tests
(`test_artifact_universe_no_ground_truth.py`), iterative-agent mock tests
(`tests/integration/test_su0011_iterative_agent.py`), calibrated/scorer tests.

## 7. Edge cases

- SIP transport-failed tasks (2/300, HTTP 429) -> their stored predictions are
  EMPTY (fail-closed). The per-task re-derivation must treat them as EMPTY
  prediction, not exclude them.
- `candidate_rows_saleor300.parquet` label column (all-zero placeholder):
  prediction loaders MUST drop/deny it at the boundary.
- Future repository-agent "no paths selected" -> EMPTY prediction in the
  fail-closed primary analysis (not silent exclusion).
- Main/calibration sets must be disjoint; intersection assertion must be
  mechanically verified.
- Intent parity: the future agent intent must be byte/canonical-hash-identical
  to the stored SIP intent per task.
- Budget: cumulative USD guard checked before each paid request; main-run
  ceiling frozen before main task 1; hitting the ceiling mid-main-run =
  `BUDGET_ABORT_INVALID_FOR_PRIMARY_COMPARISON` (no ordered partial n<50
  primary table).

## 8. Tier / risk

**Tier T3** — this work freezes scientific harness semantics, data-flow
leakage boundaries, accounting identities and future experiment invariants.
Failure to close model parity, label isolation, or exact re-derivation blocks
WP-1b authorization.

## 9. Out of scope (explicitly NOT done here)

- Executing the repository agent scientifically (no live model calls).
- Scoring future main n=50 repository-agent predictions (they do not exist).
- WP-1b (calibration + main run), WP-2 E2E Phase-0, G6 oracle, Smoke, Pilot,
  E2E regeneration, cross-language work.
- Any paid scientific model/API call.
- Accessing the 786 unread Saleor RESERVE outcomes.
- Changing SIP / RM-CSS / the frozen deployment artifact / thresholds /
  features / sample.

## 10. Acceptance criteria summary (detailed report in
`research/wp1a/wp1a_acceptance_report.json`)

AC-1A.1 model/provider provenance; AC-1A.2 label isolation; AC-1A.3 exact 300
re-derivation; AC-1A.4 main-50/cal-3 deterministic freeze + disjointness;
AC-1A.5 intent parity; AC-1A.6 agent protocol frozen + mock-executable;
AC-1A.7 shared scorer tests; AC-1A.8 accounting identities; AC-1A.9 budget
feasibility/pre-request guard; AC-1A.10 same-session cross-check (NOT an
independent audit; blind independent-audit packet prepared 2026-09-21);
AC-1A.11 $0.00
scientific API spend; AC-1A.12 786 RESERVE outcomes untouched.