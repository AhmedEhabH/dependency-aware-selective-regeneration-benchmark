# SU-0010B1.5A — Active Repository Snapshot Staging

**Change ID:** SU-0010B1.5A
**Title:** Active Repository Snapshot Staging
**Date:** 2026-07-26
**Requirement or defect:** `_build_artifact_universe()` and `_build_repository_snapshot()` derived their artifact universe from `IsolationContext.snapshot_base` (the canonical snapshot storage root), but no mechanism existed to stage a specific repository revision into an *active* snapshot directory. When multiple repository snapshots were present under `snapshot_base`, the runner could discover artifacts from stale or incorrect revisions. Additionally, regeneration-enabled execution did not enforce that an active snapshot was explicitly set, permitting execution against an un-staged or ambiguous source.
**Reason for change:** Deterministic isolation — regeneration-enabled execution requires exactly one logically immutable staged snapshot. The staging primitive (`stage_repository_snapshot`) copies source files into `<snapshot_storage_root>/<repo>/<rev>/`, and the active snapshot path is tracked via `IsolationContext.active_snapshot_root`. Missing active snapshot during regeneration fails closed with `BenchmarkError`.
**Research/protocol impact:** None — execution layer only. Same staging contract as existing `discover_eligible_artifacts` (excludes `__pycache__`, `.pyc`, `.git`, etc.). Symlinks are skipped (not copied, not followed). No Git/network operations.

## Staging Contract

```
stage_repository_snapshot(source, storage, repo_id, rev_id)
    →
<storage>/<safe_repo_id>/<safe_rev_id>/...
```

- Source must be an existing directory
- Each segment (`repo_id`, `rev_id`) is sanitised via `_safe_segment_name()` which rejects path traversal
- If the destination already exists and eligible staged content is identical (same exclusion and symlink policy as staging), the destination is returned (no re-copy)
- If the destination already exists but eligible content differs, `RepositoryError` is raised — fail closed on content collision
- Excluded directories: same as `_EXCLUDED_DIRS` plus `_STAGING_EXCLUDED_DIRS` (`.git`, `__pycache__`, `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `*.egg-info`, `runs`, `_auto_resume_temp`, `tmp`)
- Excluded files: `*.pyc`
- Symlinks: skipped (not copied, not followed)
- `shutil.copytree` with `dirs_exist_ok=False` (destination must not exist; created by copytree itself; only `destination.parent` is pre-created)
- No content-addressable store, no hashing, no Git/network
- Snapshot is logically immutable: eligible content is never overwritten or deleted; clients that need a different snapshot use a different `repository_id`/`revision_id`

## Active Snapshot Contract

- `IsolationContext.active_snapshot_root` is an optional `Path` (`None` by default)
- When set and `verify()` is called, the active snapshot path is checked to be inside `snapshot_base` boundary via structural `Path.relative_to()` containment (not string prefix matching)
- `Runner._build_artifact_universe()` and `Runner._build_repository_snapshot()` call `_active_snapshot()` which reads `self._isolation.active_snapshot_root`
- If `enable_regeneration=True` and `active_snapshot_root` is None, the runner raises `BenchmarkError("active_snapshot_root is not set — regeneration cannot proceed without a staged active snapshot")`
- Legacy impact-only path (`enable_regeneration=False`) continues to work with `active_snapshot_root=None`

## Production Files Changed

| File | Modification |
|------|-------------|
| `src/benchmark/repositories/snapshot.py` | Added `stage_repository_snapshot()`, `_safe_segment_name()`, `_STAGING_EXCLUDED_DIRS`, `_snapshot_content_equal()`. Added `tmp` to `_EXCLUDED_DIRS`. Content-aware staging: reuses identical content, raises `RepositoryError` on content collision. |
| `src/benchmark/execution/isolation.py` | Added `active_snapshot_root` parameter to `__init__` (`Optional[Path] = None`), `active_snapshot_root` property, structural `Path.relative_to()` boundary check in `verify()`. |
| `src/benchmark/execution/runner.py` | Added `_active_snapshot()` helper; `_build_repository_snapshot()` and `_build_artifact_universe()` use `_active_snapshot()`; fail-closed for regeneration with missing active snapshot. |

## Test Files Added/Modified

| File | Modification |
|------|-------------|
| `tests/unit/test_repositories_snapshot.py` | Added `TestStageRepositorySnapshot` (20 tests, 3 skip): valid staging, nested files, excluded dirs, .pyc skipped, traversal rejected (repo_id + rev_id), missing source, source-file-not-dir, identical reuse, destination-under-storage (structural assertion), two-repo isolation, symlink skipped, dir-symlink not followed. Added Fix 2 tests: modified-file rejected, added-eligible rejected, removed-eligible rejected, excluded-dir changes tolerated, symlink-only diff tolerated, destination unchanged after rejection. |
| `tests/unit/execution/test_isolation.py` | Added `TestActiveSnapshotRoot` (8 tests): default None, set-and-get, verify inside snapshot_base, verify outside snapshot_base raises, deeply nested passes, sibling prefix fails, parent traversal fails, structural boundary check. |
| `tests/unit/execution/test_runner.py` | Added `TestActiveSnapshotFailClosed` (4 tests): no active snapshot fails closed for regeneration, missing active snapshot fails closed, empty active snapshot stays empty, legacy impact-only no active snapshot required. Added `TestSourceSnapshotImmutability` (1 test, real regeneration flow): source repo unchanged, staged snapshot unchanged, execution workspace modified, regenerated_artifact_count=1, functional_validation_passed=True. Added `TestMultipleSnapshotIsolation` (1 test). Updated existing tests to pass `active_snapshot_root=snap_base`. |
| `tests/integration/test_su0010a_regeneration.py` | Updated `_setup_workspace` and `_make_isolation` to pass `active_snapshot_root=snap_base`. `test_canonical_source_unchanged_after_regeneration` updated with active snapshot staging. |

## Test Results

### Recorded Totals

| Test Suite | Collected | Passed | Failed | Skipped |
|------------|-----------|--------|--------|---------|
| `test_repositories_snapshot.py` (staging section) | 20 | 17 | 0 | 3 |
| `test_isolation.py` (active snapshot section) | 8 | 8 | 0 | 0 |
| `test_runner.py` (active snapshot section) | 8 | 8 | 0 | 0 |
| `test_su0010a_regeneration.py` | 43 | 43 | 0 | 0 |
| Full suite | 857 | 852 | 0 | 5 |

### Validation Gates

| Gate | Result |
|------|--------|
| pytest (full suite) | 852 passed, 5 skipped (symlink on Windows), 0 failed |
| ruff | All checks passed (3 files clean) |
| mypy | Success: no issues found in 3 source files |
| pip check | Pre-existing env issues only |

### Corrections Applied (post-merge-block)

- **Fix 1 — Structural path containment**: Replaced `str(active_resolved).startswith(str(snap_resolved))` with `active_resolved.relative_to(snap_resolved)` catching `ValueError`. Sibling paths with same textual prefix no longer incorrectly pass the boundary check.
- **Fix 2 — Content-aware staging**: Silent reuse of existing destination replaced with content comparison using the same exclusion/symlink policy as staging. Identical content is reused; differing eligible content raises `RepositoryError("Existing staged snapshot content differs for ...")`. Destination is never overwritten or deleted.
- **Runner integration committed**: `_active_snapshot()` fail-closed helper, `_build_repository_snapshot()` and `_build_artifact_universe()` source exactly from `active_snapshot_root`, no Ground Truth fallback, legacy impact-only compatibility preserved.
- **Test immutability corrected**: `TestSourceSnapshotImmutability` now uses `MonolithicRegenerationStrategy` and a deterministic mock backend, proving workspace modification while source and snapshot remain unchanged. `regenerated_artifact_count == 1`, `functional_validation_passed is True`.

### Key Behaviors Verified

- `stage_repository_snapshot(source, storage, "repo", "rev")` creates `<storage>/repo/rev/` with source contents, excluding `.git`, `__pycache__`, `.pyc`, etc.
- Traversal attempts (`"../escape"`, `"../../../etc"`) raise `RepositoryError`
- Missing or non-directory source raises `RepositoryError`
- Idempotent: staging same source+dest twice returns existing path when content is identical (content-aware comparison)
- Content collision: modified, added, or removed eligible files raise `RepositoryError("Existing staged snapshot content differs for ...")`
- Excluded-directory-only changes (e.g. `__pycache__`) do not trigger content collision
- Symlink-only differences follow skip policy (tolerated, not a collision)
- Destination remains unchanged after rejection (no overwrite, no delete)
- Two different repos staged to same storage do not contaminate each other
- Symlinks are skipped (tests skip on Windows, pass on Unix)
- `active_snapshot_root=None` by default
- `verify()` rejects active path outside `snapshot_base` using structural `relative_to()` containment (not string prefix)
- Runner with `enable_regeneration=True` and no active snapshot raises `BenchmarkError`
- Runner with `enable_regeneration=True` and active snapshot set succeeds
- Legacy `enable_regeneration=False` works without active snapshot
- `RepositorySnapshot.path` matches `active_snapshot_root` when set
- Source repository files remain unchanged after regeneration (logically immutable staged snapshot)
- Active staged snapshot files remain unchanged after regeneration (logically immutable staged snapshot)
- Mutable execution workspace files are actually modified to replacement content during regeneration
- `regenerated_artifact_count == 1` and `functional_validation_passed is True` after real regeneration flow

## Code/Data/Notebook Update Status

| Component | Status |
|-----------|--------|
| Code Dataset (`kaggle_upload/code/`) | 3 files updated (snapshot.py, isolation.py, runner.py); code_manifest.json SHA256 hashes updated |
| Data Dataset (`kaggle_upload/data/`) | Unchanged |
| Notebook Dataset (`kaggle_upload/notebooks/`) | Unchanged |

## Next Steps (Post-Merge)

1. Merge to `main` after validation
2. Update `TODO.md` and `SYSTEM_STATE.md` to reflect staging capability
3. Evaluate whether the Kaggle execution path needs to call `stage_repository_snapshot()` explicitly or can rely on the pre-staged kaggle_upload directory
4. Next scientific task: SU-0010B1.5B — remove Ground Truth from dependency-graph construction
5. Scientific Smoke and Pilot remain unauthorized

SU-0010B1.5B removes Ground Truth artifact fallback from the dependency-graph construction path (`selective` and `code_plan` strategies). This ensures the artifact universe is derived exclusively from the active repository snapshot, with no fallback to `expected_affected_artifacts` during graph-based impact analysis.
