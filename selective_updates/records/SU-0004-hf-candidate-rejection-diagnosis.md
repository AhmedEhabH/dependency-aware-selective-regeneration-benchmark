# SU-0004 — HF Candidate Rejection Diagnosis

**Change ID:** SU-0004
**Title:** Diagnose real HF auto-resume candidate rejection
**Date:** 2026-07-25
**Requirement or defect:** Real Kaggle auto-resume fails to resume compatible incomplete experiments; creates duplicate experiments instead
**Reason for change:** Two consecutive real Kaggle executions (exp-20260724-192456 and exp-20260724-192701) both ran the same deterministic run (djangocms-cross-007_monolithic_rep1_21b1d7b9) instead of the second execution resuming and skipping to the next arm. The compatible incomplete experiment was not detected/resumed.
**Research/protocol impact:** None — infrastructure fix only. Frozen protocol documents unchanged.

## Canonical Artifacts Affected
- `src/benchmark/checkpoint/hf_sync.py` — candidate discovery, validation, and selection logic
- `seven_arm_benchmark.py` — auto-resume invocation, Run ID consistency
- `notebooks/seven_arm_benchmark.ipynb` — progress messaging for auto-resume

## Canonical Artifacts Explicitly Unaffected
- `benchmark_data/` (all 29 files)
- `configs/` (all 3 files)
- `docs/FINAL_RESEARCH_PROTOCOL.md` and 7 companion docs (frozen)

## Generated Derivatives Affected
- `kaggle_upload/code/seven_arm_benchmark.py`
- `kaggle_upload/code/src/benchmark/checkpoint/hf_sync.py`

## Runtime Artifacts Affected
- `runs/` directory (experiment discovery)
- Kaggle HF repo experiments

## Pre-Change Evidence
- Real Kaggle trace: two consecutive executions created separate experiments (exp-20260724-192456 and exp-20260724-192701) instead of resuming
- Both ran `djangocms-cross-007_monolithic_rep1_21b1d7b9` (same deterministic Run ID) instead of skipping to next arm (agent)
- Both checkpoints reported: Completed: 1/7, Pending: 6, Status: incomplete
- Expected: Second execution should RESUME, skip monolithic, execute agent → Completed: 2/7, Pending: 5

## Impact Analysis
The auto-resume discovery path (`--auto-resume-hf`) in `resolve_auto_resume()` calls `list_compatible_experiments()` which:
1. Lists files in HF repo under `experiments/{profile}/{protocol_version}/{source_commit}/`
2. Extracts experiment IDs from paths
3. For each experiment ID, downloads `checkpoint.json` and `run_records.jsonl` from recovery/
4. Validates compatibility (protocol, config_hash, source_commit, model_identity, scenarios, strategies)
5. Separates complete vs incomplete experiments
6. Selection logic: if exactly 1 incomplete → RESUME; if multiple incomplete → ERROR (requires explicit ID); if 0 incomplete but 1 complete → ALREADY_COMPLETE; if 0 → START_NEW

The bug: Compatible incomplete experiments exist but are not being detected/selected. Root cause candidates:
1. `experiment_ids` set not populated from HF API listing (variable not defined)
2. Temp directory uses `_auto_resume_temp/` in repo root instead of `tempfile.TemporaryDirectory()`
3. Candidate validation exceptions silently swallowed with `continue`
4. Multiple compatible incomplete experiments not handled — should select most recent by `last_update` and log superseded candidates
4. Checkpoint `last_update` timestamp used for recency comparison
5. Run ID generation uses `config_hash` that may differ between discovery and execution

## Planned Minimal Diff
1. `hf_sync.py`: Fix `experiment_ids` population from HF API; use `tempfile.TemporaryDirectory()`; log candidate rejection reasons with structured diagnostic records; select most recent incomplete by `checkpoint.last_update`; log superseded candidates
2. `seven_arm_benchmark.py`: Ensure `protocol_version` included in Run ID payload; pass `args.protocol_version` to `_build_execution_plan`
3. `notebooks/seven_arm_benchmark.ipynb`: Update progress cell to show correct resume status
4. Add diagnostic logging for every candidate: experiment_id, remote_prefix, checkpoint_found, checkpoint_downloaded, profile_match, protocol_match, source_identity_match, config_hash_match, model_identity_match, planned_run_ids_match, completion_status, compatible, rejection_reason
4. Add integration test for 1→2→3 auto-resume sequence

## Actual Files Changed
(To be filled after implementation)

## Actual Lines Added/Deleted
(To be filled after implementation)

## Targeted Tests
- `tests/unit/test_hf_sync.py` — new auto-resume discovery tests
- `tests/integration/test_auto_resume.py` — new integration test for 1→2→3 resume sequence

## Full Quality Gates
- `python -m pytest tests/unit/test_hf_sync.py -v --tb=short`
- `python -m pytest tests/ -v --tb=short`
- `ruff check src tests seven_arm_benchmark.py scripts`
- `mypy --strict src tests seven_arm_benchmark.py scripts`
- `python -m pip check`
- `python scripts/build_upload_bundle.py`

## Bundle Synchronization
- `python scripts/build_upload_bundle.py`: SUCCESS (0 errors)
- Code bundle checksum verified
- Data bundle checksums unchanged
- Notebook bundle checksum unchanged

## Engineering Elapsed Time
null (not measured)

## OpenCode/Model Used
nemotron-3-ultra (via OpenCode)

## Agent Token Usage
null (not available)

## Defects Detected
1. `experiment_ids` not populated from HF API response
2. `_auto_resume_temp/` used instead of proper temp directory
3. Candidate exceptions silently swallowed
4. Multiple compatible incomplete experiments not handled (silent START_NEW)
4. Run ID inconsistency between discovery and execution
4. No diagnostic logging for candidate rejection reasons

## Defects Introduced
0 (target)

## Quality Outcome
preserved

## Git Branch
`diagnose/su-0004-hf-candidate-rejection`

## Branch Commit
(to be recorded after commit)

## Merge Commit
(pending --no-ff merge to main)

## Final Main Commit
(pending)

## Deployment Status
bundle_built_not_uploaded

## Rollback Plan
- Revert branch merge
- `scripts/build_upload_bundle.py` is idempotent — can rebuild from canonical sources

## Residual Risks
- Real Kaggle auto-resume retest required before pilot/research
- Run ID consistency across sessions depends on config_hash stability

## Next Exact Task
SU-0005 — (next requirement from backlog)