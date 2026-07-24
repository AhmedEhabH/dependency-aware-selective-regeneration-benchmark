# SU-0001 — Canonical Structure Remediation

**Change ID:** SU-0001
**Title:** Canonical structure remediation and reproducible bundle generation
**Date:** 2026-07-24
**Requirement or defect:** Architecture audit findings: inner `kaggle_upload/` empty/polluted, outer bundle stale, no automated bundle builder, no change ledger
**Reason for change:** Enable reproducible Kaggle deployment bundles, establish traceable change management, clean up structural drift
**Research/protocol impact:** None — infrastructure only. Frozen protocol documents unchanged.

## Canonical Artifacts Affected
- `scripts/build_upload_bundle.py` (new)
- `.gitignore` (additions)
- `docs/PROPOSED_CANONICAL_PROJECT_STRUCTURE.md` (status → IMPLEMENTED)
- `docs/IMPLEMENTED_ARCHITECTURE_BASELINE.md` (bundle generation section)
- `docs/SELECTIVE_PROJECT_UPDATE_POLICY.md` (status → ADOPTED, ledger reference added)
- `docs/SOURCE_OF_TRUTH_MATRIX.md` (post-remediation classifications)
- `docs/START_HERE.md` (pre-change reading order added)
- `docs/PROJECT_HANDOFF.md` (selective-update ledger section added)
- `SYSTEM_STATE.md` (phase updated)
- `TODO.md` (Phase 3.7 added)
- `DECISION_LOG.md` (D021 added)
- `reports/latest_phase_report.md` (to be updated)
- `reports/PROJECT_HEALTH_REPORT.md` (to be updated)

## Canonical Artifacts Explicitly Unaffected
- `src/benchmark/` (all 14 packages, 66 files)
- `benchmark_data/` (all 29 files)
- `configs/` (all 3 files)
- `notebooks/seven_arm_benchmark.ipynb`
- `seven_arm_benchmark.py`
- `pyproject.toml`, `requirements-kaggle.txt`, `requirements-dev.txt`
- `tests/` (all 44 files)
- `docs/FINAL_RESEARCH_PROTOCOL.md` and 7 companion docs (frozen)

## Generated Derivatives Affected
- `project/kaggle_upload/code/` (72 files)
- `project/kaggle_upload/data/` (29 files)
- `project/kaggle_upload/notebooks/` (1 file)

## Runtime Artifacts Affected
- `_auto_resume_temp/` (deleted)
- `benchmark-results.zip` (deleted)

## Pre-Change Evidence
- Inner `kaggle_upload/data/` empty (0 files vs required 29)
- Inner `kaggle_upload/code/` contained `.git/`, `__pycache__/`, `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`, `*.egg-info/`
- Outer `kaggle_upload/data/` had 29 correct files but outside Git
- No automated bundle builder existed (`scripts/` empty)
- No change ledger existed
- `runs_dir` NameError defect identified but NOT fixed in this phase

## Impact Analysis
- Bundle builder must copy only allowlisted canonical sources
- Must exclude all cache/metadata directories
- Must generate SHA-256 manifests and verify against canonical sources
- Must normalize line endings consistently
- Outer duplicates must be verified against rebuilt inner bundle before deletion
- Selective-update ledger must not duplicate architecture docs

## Planned Minimal Diff
1. Create `scripts/build_upload_bundle.py`
2. Run builder to populate inner bundle
3. Verify bundle checksums
4. Update `.gitignore`
5. Delete `_auto_resume_temp/` and `benchmark-results.zip`
6. Update documentation status fields
7. Create `project/selective_updates/` ledger structure
8. Record SU-0001

## Actual Files Changed
- `scripts/build_upload_bundle.py` (new, ~330 lines)
- `.gitignore` (4 lines added)
- `docs/PROPOSED_CANONICAL_PROJECT_STRUCTURE.md` (status line)
- `docs/IMPLEMENTED_ARCHITECTURE_BASELINE.md` (bundle section + deviations)
- `docs/SELECTIVE_PROJECT_UPDATE_POLICY.md` (status + pre-read + record requirement)
- `docs/SOURCE_OF_TRUTH_MATRIX.md` (classification updates + resolution table)
- `docs/START_HERE.md` (pre-change reading order)
- `docs/PROJECT_HANDOFF.md` (ledger section + renumbering)
- `SYSTEM_STATE.md` (phase + branch + next task)
- `TODO.md` (Phase 3.7 tasks)
- `DECISION_LOG.md` (D021 added)
- `_auto_resume_temp/` (deleted)
- `benchmark-results.zip` (deleted)
- `project/selective_updates/` (new directory with 6 files)

## Actual Lines Added/Deleted
- Added: ~600
- Deleted: ~50

## Targeted Tests
- Bundle builder self-verification: 0 errors
- Full test suite: pytest (504/505 pass, 1 skipped torch import)

## Full Quality Gates
- `ruff check src tests seven_arm_benchmark.py scripts`: 0 violations
- `mypy --strict src tests seven_arm_benchmark.py scripts`: 0 errors
- `python -m pytest tests/ -v --tb=short`: 504 passed, 1 skipped
- `python -m pip check`: clean

## Bundle Synchronization
- `python scripts/build_upload_bundle.py`: SUCCESS (0 verification errors)
- Code bundle: 72 files, 293,662 bytes
- Data bundle: 29 files, 135,604 bytes (24 scenarios + 2 manifests + 3 profiles)
- Notebook bundle: 1 file, 8,575 bytes
- Manifests generated: `code_manifest.json`, `data_manifest.json`, `notebook_manifest.json`

## Source-to-Derivative Checksum Result
- All 102 bundled files match canonical sources (normalized line-endings)
- 0 mismatches, 0 missing, 0 unexpected

## Engineering Elapsed Time
null (not measured)

## OpenCode/Model Used
nemotron-3-ultra (via OpenCode)

## Agent Token Usage
null (not available)

## Defects Detected
1. Inner data bundle empty
2. Inner code bundle contained forbidden items (.git, caches, egg-info)
3. Outer bundle stale (data outside Git, code differing)
4. No automated bundle builder
5. No change ledger

## Defects Introduced
0

## Quality Outcome
preserved

## Git Branch
`chore/canonical-project-remediation`

## Branch Commit
HEAD (to be recorded after final commit)

## Merge Commit
(pending --no-ff merge to main)

## Final Main Commit
(pending)

## Deployment Status
not_deployed (Kaggle bundle rebuilt locally; outer duplicates pending deletion)

## Rollback Plan
- Revert branch merge
- `scripts/build_upload_bundle.py` is idempotent — can rebuild from canonical sources
- Outer duplicates unchanged until explicitly deleted

## Residual Risks
- `runs_dir` NameError defect still open (SU-0002)
- Outer `<parent>/kaggle_upload/` and `<parent>/docs/` not yet deleted (requires manual verification + user command if outside Git root)
- Selective-update ledger requires adoption by future agents

## Next Exact Task
SU-0002 — Selective `runs_dir` NameError fix (minimal scope: `src/benchmark/execution/pipeline.py`, related test, bundle rebuild, ledger record)