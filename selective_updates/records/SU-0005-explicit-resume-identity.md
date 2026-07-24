# SU-0005 — Fix Explicit HF Resume Identity, Canonical Run IDs, and Idempotent Persistence

**Change ID:** SU-0005
**Title:** Fix explicit HF resume identity, canonical Run IDs, and idempotent persistence
**Date:** 2026-07-25
**Requirement or defect:** Six confirmed defects: unsafe underscore-split strategy extraction from Run IDs; checkpoints lack explicit execution identity; RunRecordStore not idempotent; canonical Run ID not enforced in summaries; unexpected candidate failures silently skipped; ledger inconsistencies
**Reason for change:** Real Kaggle auto-resume fails because strategy names containing underscores (compiled_ai, delta_mcp, incr_rtl, code_plan) are truncated by `rid.split("_", 2)` extraction, causing the remote strategy set to never equal the expected seven-arm strategy set. Additionally, checkpoints lack authoritative explicit scenario/strategy identity, RunRecordStore allows duplicate records, and summaries may carry non-canonical Run IDs.
**Research/protocol impact:** None — infrastructure fix only. Frozen protocol documents unchanged.

## Canonical Artifacts Affected
- `src/benchmark/checkpoint/checkpoint.py` — CheckpointData gains scenario_ids, strategy_names, planned_run_ids authoritatively
- `src/benchmark/checkpoint/hf_sync.py` — replace underscore-split with CompatibilityResult comparator; safe legacy policy
- `src/benchmark/checkpoint/persistence.py` — RunRecordStore idempotent append with integrity check
- `seven_arm_benchmark.py` — persist explicit identity into checkpoint; enforce canonical Run ID in summaries
- `notebooks/seven_arm_benchmark.ipynb` — fix progress cell and auto-resume markdown

## Canonical Artifacts Explicitly Unaffected
- `benchmark_data/` (all 29 files)
- `configs/` (all 3 files)
- `docs/FINAL_RESEARCH_PROTOCOL.md` and 7 companion docs (frozen)

## Pre-Change Evidence
- Strategy names compiled_ai, delta_mcp, incr_rtl, code_plan corrupted by `split("_", 2)` to compiled, delta, incr, code
- Remote strategy set {compiled, delta, incr, code, monolithic, agent, selective} != expected {compiled_ai, delta_mcp, incr_rtl, code_plan, monolithic, agent, selective}
- CheckpointData lacks scenario_ids/strategy_names authoritative fields
- RunRecordStore.append() creates duplicate records on re-run
- Summaries may carry non-canonical Run IDs from pipeline

## Git Branch
`fix/su-0005-explicit-resume-identity`
