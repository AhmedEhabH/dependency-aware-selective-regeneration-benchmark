# SU-0002 — runs_dir NameError Fix

**Change ID:** SU-0002
**Title:** Initialize runs_dir (output_dir) before auto-resume logic to fix NameError
**Date:** 2026-07-24
**Requirement or defect:** NameError: name 'runs_dir' is not defined in seven_arm_benchmark.py during START_NEW path
**Reason for change:** The variable `runs_dir` was used at line 957 in the START_NEW path but was never defined. The correct variable is `output_dir` which is parsed from `--output-dir` CLI argument.
**Research/protocol impact:** None — infrastructure fix only. Frozen protocol documents unchanged.

## Canonical Artifacts Affected
- `seven_arm_benchmark.py` (line 957: `runs_dir` → `output_dir`)
- `tests/unit/test_cli.py` (added regression tests for SU-0002)

## Canonical Artifacts Explicitly Unaffected
- `src/benchmark/` (all 14 packages, 66 files)
- `benchmark_data/` (all 29 files)
- `configs/` (all 3 files)
- `notebooks/seven_arm_benchmark.ipynb`
- `pyproject.toml`, `requirements-kaggle.txt`, `requirements-dev.txt`
- `docs/FINAL_RESEARCH_PROTOCOL.md` and 7 companion docs (frozen)

## Generated Derivatives Affected
- `project/kaggle_upload/code/seven_arm_benchmark.py`

## Runtime Artifacts Affected
- None

## Pre-Change Evidence
- Real Kaggle traceback showed `NameError: name 'runs_dir' is not defined` at line 957 in `seven_arm_benchmark.py` during START_NEW path
- Variable `runs_dir` used but never defined; `output_dir` was the correct variable (defined at line 828)

## Impact Analysis
- Bug only affects CLI execution when `--auto-resume-hf` is NOT used (START_NEW path)
- RESUME path and `--resume-from-hf` path already used `output_dir` correctly
- Fix: replace `runs_dir` with `output_dir` at line 957
- No other code paths affected

## Planned Minimal Diff
```
seven_arm_benchmark.py: -1/+1 lines (runs_dir → output_dir)
tests/unit/test_cli.py: +2 regression tests
```

## Actual Files Changed
- `seven_arm_benchmark.py` (1 line changed)
- `tests/unit/test_cli.py` (2 tests added)

## Actual Lines Added/Deleted
- Added: 25 lines (test code)
- Deleted: 1 line (variable name)

## Targeted Tests
- `tests/unit/test_cli.py::TestRunsDirBugFix::test_start_new_path_no_nameerror`
- `tests/unit/test_cli.py::TestRunsDirBugFix::test_resume_path_no_nameerror`

## Full Quality Gates
- `python -m pytest tests/unit/test_cli.py`: 17 passed
- `python -m pytest tests/`: 613 passed, 2 skipped
- `ruff check src tests seven_arm_benchmark.py scripts`: pre-existing issues only (no new)
- `mypy --strict src tests seven_arm_benchmark.py scripts`: pre-existing issues only (no new)
- `python -m pip check`: conda env issues only (project deps clean)

## Bundle Synchronization
- `python scripts/build_upload_bundle.py`: SUCCESS (0 errors)
- Code bundle: 72 files, 293,668 bytes
- Data bundle: 29 files, 135,604 bytes (unchanged)
- Notebook bundle: 1 file, 8,575 bytes (unchanged)

## Source-to-Derivative Checksum Result
- `seven_arm_benchmark.py`: normalized SHA-256 matches (canonical ↔ bundle)
- `kaggle_upload/data/`: 29 files, all checksums match canonical
- `kaggle_upload/notebooks/`: 1 file, checksum matches canonical

## Engineering Elapsed Time
null (not measured)

## OpenCode/Model Used
nemotron-3-ultra (via OpenCode)

## Agent Token Usage
null (not available)

## Defects Detected
1. `runs_dir` undefined in START_NEW path at line 957

## Defects Introduced
0

## Quality Outcome
preserved

## Git Branch
`fix/su-0002-runs-dir-nameerror`

## Branch Commit
HEAD (to be recorded after commit)

## Merge Commit
(pending --no-ff merge to main)

## Final Main Commit
(pending)

## Deployment Status
not_deployed (local verification only)

## Rollback Plan
- Revert branch merge
- `scripts/build_upload_bundle.py` is idempotent — can rebuild from canonical sources

## Residual Risks
- None identified

## Next Exact Task
SU-0003 — (next requirement from backlog)