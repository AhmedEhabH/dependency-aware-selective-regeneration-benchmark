# SU-0008 — Rebuild Complete Cross-Session Smoke Reports

**Change ID:** SU-0008
**Title:** Rebuild complete cross-session smoke reports from persisted run records
**Date:** 2026-07-25
**Requirement or defect:** Final reporting layer is inconsistent with raw records: benchmark_summary.json omits strategies completed in prior sessions, smoke_progress_summary.json reports incorrect succeeded/failed counts for resumed runs, progress.json reports stage=running despite 7/7 completion.
**Reason for change:** results_agg is built from in-memory records produced during the current invocation only; on resume, previously completed runs are in run_records.jsonl but NOT loaded into results_agg. Reports must be rebuilt from persisted records.
**Research/protocol impact:** None — infrastructure fix. Frozen protocol documents unchanged.

## Canonical Artifacts Affected
- `src/benchmark/checkpoint/reports.py` — NEW: deterministic report rebuild module
- `src/benchmark/checkpoint/checkpoint.py` — Added ProgressData cross-session fields
- `src/benchmark/checkpoint/__init__.py` — Export rebuild_experiment_reports
- `seven_arm_benchmark.py` — Finalize block uses rebuild_experiment_reports()
- `scripts/rebuild_experiment_reports.py` — NEW: offline CLI repair tool
- `tests/unit/test_su0008_cross_session_reporting.py` — NEW: 23 tests

## Canonical Artifacts Explicitly Unaffected
- `benchmark_data/` (all 29 files)
- `configs/` (all 3 files)
- `docs/` (all frozen protocol documents)
- `src/benchmark/strategies/` (all 7 strategy files)
- `src/benchmark/evaluation/` (engine, metrics)
- `src/benchmark/statistics/` (analysis, reporting)
- `src/benchmark/llm/` (all backends)
- `src/benchmark/checkpoint/resume.py`
- `src/benchmark/checkpoint/persistence.py`
- `src/benchmark/checkpoint/hf_sync.py`
- `src/benchmark/checkpoint/package.py`

## Changes Implemented

### 1. Deterministic Report Rebuild Module (`reports.py`)
- Pure function `rebuild_experiment_reports(runs_dir)` that:
  - Loads checkpoint.json and all run_records.jsonl
  - Validates raw evidence (no missing, duplicate, or unexpected Run IDs)
  - Builds results_agg from ALL persisted records (cross-session safe)
  - Writes benchmark_summary.json, benchmark_summary.partial.json
  - Writes smoke_progress_summary.json (one row per planned strategy)
  - Writes progress.json with cross-session fields
  - Returns audit report dict
- Idempotent: same input → byte-equivalent output
- No GPU, no HF token, no model inference required

### 2. ProgressData Cross-Session Fields
- Added: `total_attempted`, `total_succeeded`, `total_retryable`, `completion_status`
- Added: `experiment_run_duration_seconds`, `session_elapsed_seconds`, `report_generated_at`
- Added: `experiment_wall_clock_seconds` (null with reason for cross-session)

### 3. Main Benchmark Finalize Block
- Replaced in-memory `results_agg` final summary with `rebuild_experiment_reports()`
- All derived reports now built from persisted records on disk

### 4. Offline Repair CLI
- `scripts/rebuild_experiment_reports.py <runs-dir>`
- Prints audit report, validates consistency, returns nonzero on error

### 5. Tests (23 total)
- Completed cross-session smoke (7 tests)
- Partial resumed smoke (3 tests)
- Invalid evidence / fail closed (5 tests)
- Idempotency (1 test)
- Token aggregation (2 tests)
- Duration aggregation (1 test)
- No misleading completed report (2 tests)
- Per-strategy detail fields (1 test)
- Duplicate run ID detection (1 test)

## Pre-change Evidence
- benchmark_summary.json only contained records from the last invocation (missing monolithic and agent in resumed sessions)
- smoke_progress_summary.json reported incorrect succeeded/failed counts
- progress.json reported stage=running despite 7/7 completion

## Git History
- **Branch:** `fix/su-0008-cross-session-reporting`
- **Branch commit:** `e7b7703`
- **Merge commit:** `63dede1`
- **Final main commit:** `730cace`

## Post-change Evidence
- All 718 tests pass (23 new SU-0008 tests)
- Bundle rebuilt and verified (code, data, notebook OK)
- report rebuild produces correct 7-strategy summary
- progress.json reports stage=completed with all correct counts
- Token totals: 344 (325 prompt + 19 completion)
- Duration totals: sum of all 7 RunRecord durations
- Deployment status: not_deployed
- Quality outcome: preserved
