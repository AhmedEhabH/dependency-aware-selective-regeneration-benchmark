# SU-0010B1 — Repository-Derived Artifact Universe and Ground-Truth Leakage Removal

**Change ID:** SU-0010B1
**Title:** Repository-Derived Artifact Universe and Ground-Truth Leakage Removal
**Date:** 2026-07-26
**Requirement or defect:** Runner._build_artifact_universe() derived ArtifactUniverse from scenario.expected_affected_artifacts (Ground Truth), exposing the expected answer before prediction and invalidating scientific evaluation.
**Reason for change:** Scientific validity correction — candidate universe must come from repository filesystem, not Ground Truth.
**Research/protocol impact:** None — execution layer only. Impact strategies, benchmark data, frozen protocol documents, and comparison metrics unchanged.

## Old Leakage Path

`_build_artifact_universe()` at `src/benchmark/execution/runner.py:471`:

```python
def _build_artifact_universe(self, scenario: Scenario) -> ArtifactUniverse:
    return ArtifactUniverse(artifacts=scenario.expected_affected_artifacts)
```

This passed Ground Truth directly as the candidate universe, leaking expected answers to the strategy before prediction.

## New Repository-Derived Path

```
RepositorySnapshot workspace root
    ↓
discover_eligible_artifacts(snapshot_root)
    ↓
ArtifactUniverse
    ↓
ImpactStrategy.analyze_impact()
```

`_build_artifact_universe()` now uses filesystem discovery for regeneration-enabled execution, failing closed if the snapshot path is missing, and returning an empty universe (not Ground Truth) when no eligible files exist.

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
| `src/benchmark/execution/runner.py` | Modified `_build_artifact_universe()` to use filesystem discovery for regeneration-enabled execution. Added imports: `Path`, `discover_eligible_artifacts`. |

## Workspace.py Exception Required

No — `workspace.py` was not modified. The snapshot root is obtained from `self._isolation.workspace.root`.

## Discovery Rules

- Walk filesystem recursively under `snapshot_path`
- Include regular files only with matching extensions (default: `.py`, case-insensitive)
- Return paths relative to `snapshot_path`, normalized to POSIX separators
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
| `test_runner.py` | 14 | 14 | 0 | 0 |
| `test_su0010a_regeneration.py` | 43 | 43 | 0 | 0 |
| Full suite | 818 | 816 | 0 | 2 |

### Leakage Regression (critical assertion)

```
filesystem files:    src/actual_a.py, src/actual_b.py, src/unrelated.py
Ground Truth files:  src/ground_truth_only.py

universe contains actual_a.py, actual_b.py, unrelated.py        ✓
universe does NOT contain ground_truth_only.py                   ✓
```

### Missing Snapshot

When workspace root does not exist and `enable_regeneration=True`, the system fails closed via isolation check with a `RepositoryError`. No fallback to Ground Truth.

### Empty Snapshot

Empty workspace root with `enable_regeneration=True` produces an empty `ArtifactUniverse` (0 artifacts). No fallback to Ground Truth.

### Legacy Impact-Only Compatibility

`enable_regeneration=False` continues to use `scenario.expected_affected_artifacts` for fixture compatibility.

## Validation Gates

| Gate | Result |
|------|--------|
| pytest (full suite) | 816 passed, 2 skipped, 0 failed |
| ruff | All checks passed |
| mypy (changed files) | Success: no issues found |
| pip check | Pre-existing environment warnings only |
| Bundle | Code: 75 files, Data: 29 files, Notebooks: 1 files |

## Code/Data/Notebook Update Status

| Component | Status |
|-----------|--------|
| Code Dataset (`kaggle_upload/code/`) | Regenerated — 75 files |
| Data Dataset (`kaggle_upload/data/`) | Unchanged |
| Notebook Dataset (`kaggle_upload/notebooks/`) | Unchanged |

## Known Remaining Scientific Blockers

1. The `_build_repository_snapshot()` method in `runner.py` still uses `scenario.repository` (a repo name) as the path. This does not affect artifact universe construction (US-0010B1 scope), but the RepositorySnapshot path is incorrect for real filesystem use. SU-0010B2 or later correction is required to derive the snapshot path from the actual execution context.
2. Dependency-graph construction in `seven_arm_benchmark.py:build_dependency_graph()` still references `s.expected_affected_artifacts` for fallback minimal graph nodes. This is not an artifact universe concern, but it means evaluation metadata leaks into graph construction when no profile graph exists.
3. The snapshot path for artifact discovery is `workspace.root`, which conflates workspace and snapshot. A future change should separate the two to support multiple repos in the same workspace.
