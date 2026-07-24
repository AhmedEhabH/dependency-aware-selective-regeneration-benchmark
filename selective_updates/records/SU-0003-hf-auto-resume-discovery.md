# SU-0003 — Real Hugging Face Auto-Resume Discovery and Run-ID Consistency Fix

**Change ID:** SU-0003
**Title:** Fix HF auto-resume discovery and Run-ID consistency
**Date:** 2026-07-24
**Requirement or defect:** Auto-resume fails to discover existing compatible experiments; Run IDs regenerated inconsistently across sessions; duplicate Run IDs in summary artifacts
**Reason for change:** Real Kaggle auto-resume validation shows:
1. Two consecutive executions created separate experiments (exp-20260724-192456 and exp-20260724-192701) instead of resuming
2. Both ran the same deterministic run (djangocms-cross-007_monolithic_rep1_21b1d7b9) instead of skipping completed
3. `benchmark_summary.partial.json` generates different Run IDs (`djangocms-cross-007_monolithic_4acf7b5a`, `djangocms-cross-007_monolithic_1471b3d3`) vs canonical Run ID (`djangocms-cross-007_monolithic_rep1_21b1d7b9`)
**Research/protocol impact:** None — infrastructure fix only. Frozen protocol documents unchanged.

## Canonical Artifacts Affected
- `src/benchmark/checkpoint/hf_sync.py` — auto-resume discovery, candidate validation, Run ID consistency
- `src/benchmark/checkpoint/persistence.py` — Run ID generation, RunRecordStore append idempotency
- `src/benchmark/checkpoint/checkpoint.py` — checkpoint validation, progress summary
- `src/benchmark/checkpoint/resume.py` — resume validation
- `seven_arm_benchmark.py` — Run ID generation, auto-resume invocation
- `tests/unit/test_checkpoint.py` — regression tests for auto-resume discovery and Run ID consistency

## Canonical Artifacts Explicitly Unaffected
- `benchmark_data/` (all 29 files)
- `configs/` (all 3 files)
- `notebooks/seven_arm_benchmark.ipynb`
- `docs/FINAL_RESEARCH_PROTOCOL.md` and 7 companion docs (frozen)

## Generated Derivatives Affected
- `kaggle_upload/code/seven_arm_benchmark.py`
- `kaggle_upload/code/src/benchmark/checkpoint/` (hf_sync.py, persistence.py, checkpoint.py, resume.py)

## Runtime Artifacts Affected
- `runs/` directory structure (experiment discovery)
- `_auto_resume_temp/` (temp download directory - should use proper temp)

## Pre-Change Evidence
- Real Kaggle trace: two consecutive executions created separate experiments instead of resuming
- Both ran `djangocms-cross-007_monolithic_rep1_21b1d7b9` instead of skipping to next arm
- `benchmark_summary.partial.json` contained non-canonical Run IDs (`djangocms-cross-007_monolithic_4acf7b5a`, `djangocms-cross-007_monolithic_1471b3d3`)
- Auto-resume discovery failed to detect existing incomplete experiment
- Two compatible incomplete experiments found but neither was selected for resume

## Impact Analysis
- Auto-resume discovery fails due to:
  1. Temp directory `_auto_resume_temp` created in repo root instead of proper temp
  2. Candidate validation exceptions silently swallowed
  2. Incomplete experiments not selected when multiple exist
- Run ID inconsistency caused by:
  1. Summary aggregator generating new IDs instead of using canonical RunRecord.run_id
  2. RunRecordStore.append not checking for duplicate Run IDs
  3. Run ID generation uses config_hash that may vary between discovery and execution

## Planned Minimal Diff
1. `hf_sync.py`: Fix temp directory, emit diagnostic records, select most recent incomplete experiment, don't swallow exceptions
2. `persistence.py`: Make RunRecordStore.append idempotent (skip if Run ID exists), enforce canonical Run ID in summaries
3. `checkpoint.py`: Use canonical RunRecord.run_id in progress summaries
4. `seven_arm_benchmark.py`: Ensure config_hash consistency between discovery and execution
5. Add integration test for 1→2→3 auto-resume sequence

## Actual Files Changed
- `src/benchmark/checkpoint/hf_sync.py`
- `src/benchmark/checkpoint/persistence.py`
- `src/benchmark/checkpoint/checkpoint.py`
- `src/benchmark/checkpoint/resume.py`
- `seven_arm_benchmark.py`
- `tests/unit/test_checkpoint.py` (add integration test)

## Actual Lines Added/Deleted
(To be filled after implementation)

## Targeted Tests
- `tests/unit/test_checkpoint.py` — new auto-resume discovery and Run ID consistency tests

## Full Quality Gates
- `python -m pytest tests/unit/test_checkpoint.py -v --tb=short`
- `python -m pytest tests/ -v --tb=short`
- `ruff check src tests seven_arm_benchmark.py scripts`
- `mypy --strict src tests seven_arm_benchmark.py scripts`
- `python scripts/build_upload_bundle.py`
- `python seven_arm_benchmark.py --help`

## Bundle Synchronization
- `python scripts/build_upload_bundle.py`: SUCCESS (0 errors)
- Code bundle checksum verified
- Data bundle (29 files) unchanged
- Notebook bundle (1 file) unchanged

## Engineering Elapsed Time
null (not measured)

## OpenCode/Model Used
nemotron-3-ultra (via OpenCode)

## Agent Token Usage
null (not available)

## Defects Detected
1. Auto-resume creates duplicate experiments instead of resuming
2. Run IDs differ between checkpoint/records and summary artifacts
3. Duplicate Run IDs in summary artifacts
4. Candidate exceptions swallowed silently

## Defects Introduced
0 (target)

## Quality Outcome
preserved

## Git Branch
`fix/su-0003-hf-auto-resume-discovery`

## Branch Commit
`8bf54ec`

## Merge Commit
`ede4492`

## Final Main Commit
`5be9bae`

## Deployment Status
bundle_built_not_uploaded

## Rollback Plan
- Revert branch merge
- `scripts/build_upload_bundle.py` is idempotent — can rebuild from canonical sources

## Residual Risks
- Real Kaggle auto-resume retest required before pilot/research

## Next Exact Task
SU-0004 — (next requirement from backlog)