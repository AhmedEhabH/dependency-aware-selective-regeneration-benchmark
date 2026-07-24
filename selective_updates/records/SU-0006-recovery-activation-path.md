# SU-0006 — Activate Downloaded HF Recovery State at the Canonical Output Directory

**Change ID:** SU-0006
**Title:** Activate downloaded HF recovery state at the canonical output directory
**Date:** 2026-07-25
**Requirement or defect:** Real Kaggle auto-resume downloads recovery files successfully but places them in the wrong directory hierarchy, causing "No checkpoint found in downloaded recovery state" validation failure
**Reason for change:** `HfResumeManager.download_and_validate()` uses `local_dir=str(self._runs_dir)` with `hf_hub_download`, which preserves the full repo directory structure under `self._runs_dir`. Files end up at `<runs_dir>/experiments/.../recovery/checkpoint.json` but validation expects them at `<runs_dir>/checkpoint.json`.
**Research/protocol impact:** None — infrastructure fix only. Frozen protocol documents unchanged.

## Canonical Artifacts Affected
- `src/benchmark/checkpoint/hf_sync.py` — download_and_validate() rewritten to use isolated temp dir + atomic activation

## Canonical Artifacts Explicitly Unaffected
- `benchmark_data/` (all 29 files)
- `configs/` (all 3 files)
- `docs/FINAL_RESEARCH_PROTOCOL.md` and 7 companion docs (frozen)
- `src/benchmark/checkpoint/checkpoint.py` — CheckpointData schema unchanged
- `src/benchmark/checkpoint/persistence.py` — RunRecordStore unchanged
- `src/benchmark/checkpoint/resume.py` — ResumeManager unchanged
- Deterministic Run ID generation unchanged
- Compatibility comparator unchanged

## Pre-Change Evidence
- Real Kaggle trace: candidate exp-20260724-203139 discovered, selected, downloaded
- Downloaded files exist at: `/kaggle/working/runs/experiments/smoke/1.0/v0.7.0-smoke-passed/exp-20260724-203139/recovery/checkpoint.json`
- Validation expects: `/kaggle/working/runs/checkpoint.json`
- Error: "No checkpoint found in downloaded recovery state"

## Git Branch
`fix/su-0006-recovery-activation-path`

## Commits
- Branch: `2e4c7bb` — fix(kaggle): activate downloaded recovery state at output root
- Merge: `d2d72ca` — merge into main

## Validation
- **pytest**: 648 passed, 2 skipped (pre-existing)
- **mypy --strict**: Clean (0 errors)
- **ruff**: Clean (after 3 import fixes in test file)
- **bundle**: Verified (72 code files, 29 data, 1 notebook, 462,709 bytes total)

## Status
**MERGED** — 2026-07-25
