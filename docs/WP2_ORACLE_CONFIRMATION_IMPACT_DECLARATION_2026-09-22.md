# Impact Declaration — wp2-oracle-confirmation-design-v1

> Tier **T3** · Scientific/model API spend **$0.00** · ZERO LLM/embedding/
> OpenRouter/E2E-generation calls · Deterministic oracle-confirmation
> infrastructure + experimental-design freeze preparation.

## Purpose

Build and test a zero-LLM Oracle Confirmation harness, execute it on the 20
strong F2P candidates plus deterministic stratified modified-test waves, and
produce WP-2 causal E2E design v1, power/assay-sensitivity planning, Smoke
proposal v2, and novelty boundaries. No generation experiment and no AG16 paid
run happen here.

## New artifacts (intended)

**src/benchmark/wp2/**
- `paths.py` — portable, tested repository-root / workspace-root / env-root /
  worktree-root / Python-3.12 / PostgreSQL-bin discovery (env-var overrides,
  no machine-specific paths).
- `oracle_confirmation.py` — deterministic F2P/P2P oracle semantics: state
  construction, test discovery, JUnit parsing, 3-run stability classification,
  failure taxonomy, eligibility flags.
- `environment_manager.py` — isolated, version-aware environment fingerprinting
  and construction under `..\_workspace\wp2_oracle_confirmation\` (workspace
  root resolved dynamically via `WP2_WORKSPACE_ROOT` or repository-relative
  default).
- `oracle_runner.py` — per-task runner: worktree isolation, test-only patch
  application, 3x parent + 3x target runs, classification.

**scripts/**
- `wp2_oracle_confirm.py` — Oracle Confirmation launcher (worktree isolation,
  test-only patch derivation, 3x parent + 3x target runs, resume).
- `wp2_oracle_summary.py` — summary/attrition reconciliation and reporting.

**tests/unit/wp2/ and tests/integration/wp2/**
- unit: classification, test-only diff, JUnit parsing, 3-run stability,
  taxonomy, strata/order determinism, no-selector-outcome fields, no-sealed
  path, fingerprint determinism, resume, attrition reconciliation.
- integration: synthetic repos proving behavioral F2P, symbol-absence F2P,
  P2P-only, flaky, source-free test-only patch, resume no-rerun, 786-guard.

**research/wp2/**
- `wp2_design_reference_manifest_2026-09-22.json`
- `wp2_oracle_confirmation_selection_2026-09-22.json`
- `wp2_e2e_design_v1_2026-09-22.json`
- `oracle_confirmation_2026-09-22/{run_state,per_task,per_test,environment_fingerprints,attrition,summary}.json/.jsonl`
- `wp2_p2p_candidate_inventory_2026-09-22.json`
- `wp2_power_scenarios_2026-09-22.json`
- `wp2_smoke_candidate_proposal_v2_2026-09-22.json`
- `research/literature/wp2_verified_references_2026-09-22.bib`

**docs/**
- `WP2_CENSUS_TASK_CANDIDATE_SELECTION_RATIONALE_2026-09-22.md`
- `WP2_SMOKE_PROPOSAL_REVIEW_2026-09-22.md`
- `WP2_E2E_CAUSAL_DESIGN_V1_2026-09-22.md`
- `WP2_ORACLE_CONFIRMATION_REPORT_2026-09-22.md`
- `WP2_POWER_AND_ASSAY_SENSITIVITY_PLANNING_2026-09-22.md`
- `WP2_SMOKE_SELECTION_V2_2026-09-22.md`
- `WP2_NOVELTY_AND_RELATED_WORK_BOUNDARY_2026-09-22.md`
- `WP2_ORACLE_CONFIRMATION_DESIGN_V1_STOP_REPORT_2026-09-22.md`

**Governance (current-facing only):** `README.md`, `docs/LIVE_STATUS.json`,
`PROGRESS.md`, `TODO.md`, `00_CURRENT_RESEARCH_STATE.md`, existing current
START_HERE file, `DECISIONS.md` (append-only).

## Dependencies

- `dist/pilot-repo-cache/saleor` (read-only cache; commits verified for all
  changed-test candidates).
- `benchmark_data/real_commit_impact_saleor/scientific/<task>/case_manifest.json`
  (parent/target commits).
- Prior census: `research/wp2/wp2_saleor_main297_census_2026-09-22.json`.

## Isolation and guards

- Worktrees under `..\_workspace\wp2_oracle_confirmation\worktrees\`; the
  Saleor cache is never mutated.
- Isolated envs under `..\_workspace\wp2_oracle_confirmation\envs\<fingerprint>\`.
- Postgres/Redis may be used locally only if already available, with isolated
  test DB/schema names.
- Resource ceilings: env build 30 min; per-test replicate 15 min; overall
  Oracle Confirmation soft wall-clock 12 h; disk hard ceiling 80 GB (evict only
  mission-created caches).
- 786 sealed Saleor RESERVE outcomes: never accessed; guard fails closed.
- Test patches / F2P/P2P identifiers: evaluator-only; never exposed to a future
  generator.
- No global/system destructive changes.

## Risks

- Environment cannot be reproduced for some historical commits -> `ENV_BROKEN`
  classified, not improvised.
- Test-only patch cannot apply to parent -> `TEST_PATCH_APPLY_FAIL`.
- Flakiness -> `FLAKY`. All attrition reasons preserved; no silent drops.
- Full suite may exceed 50 min -> run once at final gate with 5,400,000 ms
  timeout, log to file, compare failures to the known-failures artifact.

## Decision block (appended to DECISIONS.md)

`WP2_ORACLE_CONFIRMATION_DESIGN_V1 - APPROVED (2026-09-22)` — O1..O17.

Decided by **Ahmed Ehab**, 2026-09-22. Supervisor informed: no.