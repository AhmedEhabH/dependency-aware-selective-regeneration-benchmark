# SU-0007 — Continuous Execution, Run-State Semantics, and GPU Preflight

**Change ID:** SU-0007
**Title:** Continuous execution, run-state semantics, and GPU preflight gating
**Date:** 2026-07-25
**Requirement or defect:** Critical state-loss defect: resume flow normalizes checkpoint correctly but later constructs a new CheckpointData using empty state lists, destroying normalized prior state. Attempted-state terminology not documented. CPU preflight returns compatible=True when no CUDA GPU. Notebook wording inaccurate.
**Reason for change:** SU-0007 requires explicit run-state fields with enforced invariants, retryable-failure-aware resume, legacy normalization, strict GPU preflight gating, and corrected terminology
**Research/protocol impact:** None — infrastructure fix. Frozen protocol documents unchanged.

## Canonical Artifacts Affected
- `src/benchmark/checkpoint/checkpoint.py` — Added `succeeded_run_ids`, `retryable_run_ids`, `attempted_run_ids` fields; added `normalize_from_records()` method
- `src/benchmark/checkpoint/persistence.py` — Added `RETRYABLE_FAILURE_CLASSIFICATIONS`, `failure_is_retryable()`
- `src/benchmark/checkpoint/resume.py` — Fixed `validate_and_get_skip_ids()` to exclude retryable failures; added `get_normalized_checkpoint()` method; added normalization call
- `src/benchmark/llm/kaggle_qwen_backend.py` — Fixed CPU preflight: no-CUDA returns incompatible with clear message
- `seven_arm_benchmark.py` — Fixed critical state-loss: RESUME preserves normalized checkpoint state; START_NEW initializes empty; fixed preflight; maintained `attempted_run_ids` during execution
- `kaggle_upload/notebooks/seven_arm_benchmark.ipynb` — Updated wording: "Succeeded and explicitly non-retryable failed runs are skipped. Retryable environment failures are retried."
- `tests/unit/test_su0007_continuous_execution.py` — Added 42 tests covering all 11 required test cases

## Canonical Artifacts Explicitly Unaffected
- `benchmark_data/` (all 29 files)
- `configs/` (all 3 files)
- `docs/` (all frozen protocol documents)
- `src/benchmark/strategies/` (all 7 strategy files)
- `src/benchmark/evaluation/` (engine, metrics)
- `src/benchmark/statistics/` (analysis, reporting)

## Changes Implemented

### 1. Critical State-Loss Fix (`seven_arm_benchmark.py`)
- On RESUME: uses `resume_mgr.get_normalized_checkpoint()` to retain the full normalized prior state (succeeded, failed, retryable, completed, attempted IDs)
- On START_NEW: initializes empty state lists
- Preserved: profile, planned_run_ids, scenario_ids, strategy_names, source identity, deployed_build_id, succeeded_run_ids, failed_run_ids, retryable_run_ids, completed/attempted IDs
- Pending IDs recomputed as `planned - completed`

### 2. CheckpointData Schema (`checkpoint.py`)
- Added `attempted_run_ids: list[str]` with `field(default_factory=list)` (backward-compatible alias for completed_run_ids)
- Added `succeeded_run_ids: list[str]` and `retryable_run_ids: list[str]` with `field(default_factory=list)` (backward-compatible)
- Added `normalize_from_records(record_store)` method that recomputes all fields from run records:
  - `attempted = succeeded ∪ failed`
  - `pending = planned - attempted`
  - `succeeded ∩ failed = ∅`
  - `attempted ∩ pending = ∅`

### 3. ResumeManager Enhancement (`resume.py`)
- Added `get_normalized_checkpoint()` method that returns the full normalized CheckpointData
- `validate_and_get_skip_ids()` unchanged — still returns skip set only

### 4. Retryable Classification (`persistence.py`)
- Added `RETRYABLE_FAILURE_CLASSIFICATIONS = {"environment_preflight", "environment", "gpu_incompatible", "cuda_error"}`
- Added `failure_is_retryable(record) -> bool`

### 5. Resume Skip Policy (`resume.py`)
- Skip set = succeeded ∪ non-retryable failed
- Retryable failures NOT in skip set — retried on resume

### 6. GPU Preflight Fix (`kaggle_qwen_backend.py`)
- `preflight()` when no CUDA: returns `compatible=False` with message "CUDA GPU required for the configured Qwen backend."
- Previously returned `compatible=True` — incorrect for real Qwen execution
- Dry-run and mock execution remain allowed without CUDA

### 7. Notebook Wording (`kaggle_upload/notebooks/seven_arm_benchmark.ipynb`)
- Changed from "Completed runs are skipped" to "Succeeded and explicitly non-retryable failed runs are skipped. Retryable environment failures are retried."
- Documented `--max-runs 1` = one-run engineering chunk vs no limit = continue through remaining plan
- Updated GPU Requirement section to specify CUDA GPU requirement

### 8. Attempted-State Terminology
- Added `attempted_run_ids` field to CheckpointData
- `completed_run_ids` retained as backward-compatible alias
- Progress output reports: attempted, succeeded, failed, retryable, pending

## Validation
- **pytest**: 690 passed, 2 skipped
- **New tests**: 42 (all 11 required test cases verified)
- **ruff**: pre-existing issues only, no new issues from SU-0007
- **mypy**: pre-existing issues only, no new issues from SU-0007
- **pip check**: pre-existing conda/environment issues only
- **Bundle**: built and verified (102 files, 480,424 bytes)

## Required Test Evidence

| # | Test Name | Outcome |
|---|-----------|---------|
| 1 | `test_resume_preserves_succeeded_ids` | PASSED |
| 2 | `test_resume_preserves_failed_ids` | PASSED |
| 3 | `test_resume_preserves_retryable_ids` | PASSED |
| 4 | `test_succeeded_monolithic_stays_succeeded_after_agent_succeeds` | PASSED |
| 5 | `test_retryable_agent_failure_not_skipped` | PASSED |
| 6 | `test_after_retry_succeeds_full_state` | PASSED |
| 7 | `test_checkpoint_preserves_state_on_normalize` | PASSED |
| 8 | `test_qwen_preflight_no_cuda_returns_incompatible` | PASSED |
| 9 | `test_dry_run_preflight_returns_compatible_without_cuda` | PASSED |
| 10 | `test_no_max_runs_plan_includes_all_remaining` | PASSED |
| 11 | `test_max_runs_one_takes_exactly_one` | PASSED |

## Git State
- **Branch:** `fix/su-0007-run-state-semantics`
- **Base:** `1a1b845` (SU-0006 final commit on main)
- **Status:** Pending commit, merge, and push

## Status
**VALIDATED** — Quality gates passed, pending merge
