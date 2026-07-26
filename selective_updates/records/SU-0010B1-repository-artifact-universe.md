# SU-0010B1 — Repository-Derived Artifact Universe, Ground-Truth Leakage Removal, and Snapshot Root Separation

**Change ID:** SU-0010B1 (final snapshot-root correction applied 2026-07-26)
**Title:** Repository-Derived Artifact Universe, Ground-Truth Leakage Removal, and Snapshot Root Separation
**Date:** 2026-07-26
**Requirement or defect:** Runner._build_artifact_universe() derived ArtifactUniverse from scenario.expected_affected_artifacts (Ground Truth), exposing the expected answer before prediction and invalidating scientific evaluation. Additionally, the initial filesystem-discovery fix incorrectly used `workspace.root` instead of the separate immutable `snapshot_base`, conflating execution workspace with the repository snapshot.
**Reason for change:** Scientific validity correction — candidate universe must come from the repository filesystem (snapshot), not Ground Truth, and the snapshot root must be the immutable snapshot directory, not the execution workspace.
**Research/protocol impact:** None — execution layer only. Impact strategies, benchmark data, frozen protocol documents, and comparison metrics unchanged.

## Old Leakage Path

`_build_artifact_universe()` at `src/benchmark/execution/runner.py:471`:

```python
def _build_artifact_universe(self, scenario: Scenario) -> ArtifactUniverse:
    return ArtifactUniverse(artifacts=scenario.expected_affected_artifacts)
```

This passed Ground Truth directly as the candidate universe, leaking expected answers to the strategy before prediction.

## Intermediate (Pre-Correction) Path

```python
snapshot_root = Path(self._isolation.workspace.root)   # BUG: workspace, not snapshot
```

This still conflated execution workspace with the repository snapshot, allowing workspace-generated artifacts (runs/, tmp/, etc.) to appear in the candidate universe.

## Final Repository-Derived Path (after SU-0010B1 snapshot-root correction)

```
IsolationContext.snapshot_base
    ↓
discover_eligible_artifacts(snapshot_base)     ← reads snapshot_base only
    ↓
ArtifactUniverse
    ↓
ImpactStrategy.analyze_impact()
```

- `snapshot_base` must exist and be a directory
- Artifact discovery reads **only** snapshot_base
- `runs/`, `tmp/`, generated workspace outputs are never candidates
- Missing `snapshot_base` fails closed (`BenchmarkError`)
- Empty `snapshot_base` produces empty `ArtifactUniverse`
- No Ground Truth fallback

## Legacy Impact-Only Compatibility Boundary

When `enable_regeneration=False` and no actual repository snapshot is configured, the pre-existing fixture-compatible behavior (using `scenario.expected_affected_artifacts`) is preserved.

Code comment:

```
Legacy fixture compatibility only.
Ground Truth fallback is forbidden for regeneration-enabled and scientific execution.
```

This path must not be used when `enable_regeneration=True`.

## Production Files Changed

| File | Modification |
|------|-------------|
| `src/benchmark/repositories/snapshot.py` | Added `discover_eligible_artifacts()`, `_EXCLUDED_DIRS`, `_EXCLUDED_FILE_SUFFIXES`, `_is_egg_info_dir()`. New imports: `os`, `ArtifactType`, `ArtifactRef`. |
| `src/benchmark/execution/runner.py` | Modified `_build_artifact_universe()` to use filesystem discovery via `self._isolation.snapshot_base` (not `workspace.root`). Modified `_build_repository_snapshot()` to use `snapshot_base` when regeneration is enabled. |
| `kaggle_upload/code/src/benchmark/execution/runner.py` | Same changes applied. |
| `tests/unit/execution/test_runner.py` | Updated existing tests to place source files in snapshot_base; added `TestSnapshotSourceWorkspaceSeparation` and `TestRepositorySnapshotPathConsistency` test classes. |
| `tests/integration/test_su0010a_regeneration.py` | Updated `_setup_workspace` to write source files to both `snap_base` (for strategy discovery) and `ws_root` (for executor read/write). |

## Workspace.py Exception Required

No — `workspace.py` was not modified. The snapshot root is obtained from `IsolationContext.snapshot_base`.

## Discovery Rules

- Walk filesystem recursively under `snapshot_base`
- Include regular files only with matching extensions (default: `.py`, case-insensitive)
- Return paths relative to `snapshot_base`, normalized to POSIX separators
- Sort deterministically by normalized relative path
- Excluded directories: `.git`, `__pycache__`, `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `*.egg-info`, `runs`, `_auto_resume_temp`
- Excluded files: `*.pyc`
- `ArtifactType.source` used as neutral default (scientifically harmless — does not leak Ground Truth)
- Empty tuple returned when path does not exist or has no eligible files
- No access to Scenario, Ground Truth, expected artifacts, manifests, or evaluation data

## Test Results

### Recorded Totals

| Test Suite | Collected | Passed | Failed | Skipped |
|------------|-----------|--------|--------|---------|
| `test_repositories_snapshot.py` | 29 | 29 | 0 | 0 |
| `test_runner.py` | 14+ | 14+ | 0 | 0 |
| `test_su0010a_regeneration.py` | 43 | 43 | 0 | 0 |
| Full suite | ... | ... | ... | ... |

### Leakage Regression (critical assertion)

```
snapshot_base files:    src/source_a.py, src/source_b.py
workspace files:        runs/generated.py, tmp/temp.py, unrelated_workspace.py
Ground Truth files:     src/ground_truth_only.py

universe contains source_a.py, source_b.py                          ✓
universe excludes generated.py, temp.py, unrelated_workspace.py     ✓
universe does NOT contain ground_truth_only.py                      ✓
```

### Missing Snapshot Base

When `snapshot_base` does not exist and `enable_regeneration=True`, the system fails closed with a `BenchmarkError`. No fallback to Ground Truth.

### Empty Snapshot Base

Empty `snapshot_base` with `enable_regeneration=True` produces an empty `ArtifactUniverse` (0 artifacts). No fallback to Ground Truth.

### RepositorySnapshot Path Consistency

`RepositorySnapshot.path == str(self._isolation.snapshot_base)` for regeneration-enabled execution. Legacy impact-only path unchanged.

### Legacy Impact-Only Compatibility

`enable_regeneration=False` continues to use `scenario.expected_affected_artifacts` for fixture compatibility.

## Validation Gates

| Gate | Result |
|------|--------|
| pytest (full suite) | ... |
| ruff | ... |
| mypy --strict | ... |
| pip check | ... |
| Bundle | ... |

## Code/Data/Notebook Update Status

| Component | Status |
|-----------|--------|
| Code Dataset (`kaggle_upload/code/`) | Regenerated — 75 files |
| Data Dataset (`kaggle_upload/data/`) | Unchanged |
| Notebook Dataset (`kaggle_upload/notebooks/`) | Unchanged |

## Known Remaining Scientific Blockers

1. **artifact-universe leakage from expected_affected_artifacts: removed.** The candidate universe is now fully filesystem-derived from `snapshot_base`.
2. **source snapshot root separation: implemented.** `snapshot_base` is separate from `workspace.root`.
3. **CLI/Kaggle snapshot staging: not implemented.** The pipeline does not yet stage repository snapshots to `snapshot_base` in CLI or Kaggle execution contexts.
4. **dependency-graph Ground Truth fallback: still blocking before Scientific Smoke.** `seven_arm_benchmark.py:build_dependency_graph()` still references `s.expected_affected_artifacts` for fallback minimal graph nodes.
5. **This branch remains local/test-fixture validated only.** Not yet validated on Kaggle or against the full benchmark.
