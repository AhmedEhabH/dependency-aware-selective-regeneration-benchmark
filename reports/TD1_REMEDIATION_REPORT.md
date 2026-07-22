# TD-1 Remediation Report

**Date:** 2026-07-22
**Protocol Version:** 1.0 (FROZEN)
**Status:** REMEDIATED — All quality gates pass

## Root Cause

During Phase 4D (Execution Core), `BenchmarkRunner._run_attempt` was implemented with a shortcut that passed the `Scenario` object directly to `ImpactStrategy.analyze_impact()` for all three protocol parameters (`repository`, `requirement_change`, `artifact_universe`). The `ImpactStrategy` protocol expects distinct domain objects (`RepositorySnapshot`, `RequirementChange`, `ArtifactUniverse`), not `Scenario`. Three `# type: ignore[arg-type]` comments were added to suppress the resulting mypy errors, masking the type violation.

## Files Changed

| File | Change |
|------|--------|
| `src/benchmark/execution/runner.py` | Added imports for `ArtifactUniverse`, `RepositoryIdentity`, `RepositorySnapshot`, `RequirementChange`. Added three private extraction methods. Updated `_run_attempt` to construct and pass correct domain objects. Removed 3 `# type: ignore[arg-type]` comments. |
| `tests/unit/execution/test_runner.py` | Updated `_FakeStrategy` to record arguments. Added `test_run_extracts_correct_domain_objects` verifying correct type extraction and field mapping. |

## Tests Affected

| Test | Status |
|------|--------|
| All 288 existing tests | PASSED (no regressions) |
| `test_run_extracts_correct_domain_objects` (new) | PASSED |

**Total: 289/289 passed**

## Why the Previous Implementation Was Incorrect

The frozen `ImpactStrategy` protocol (`src/benchmark/core/protocols.py:21-28`) defines:

```python
class ImpactStrategy(Protocol):
    def analyze_impact(
        self,
        repository: RepositorySnapshot,
        requirement_change: RequirementChange,
        artifact_universe: ArtifactUniverse,
    ) -> ImpactPrediction:
        ...
```

The previous implementation passed `Scenario` (a different frozen dataclass) for all three parameters. While both `Scenario` and the expected types are frozen dataclasses from the same models module, they have fundamentally different structures:

- `RepositorySnapshot` requires `identity: RepositoryIdentity`, `commit_sha: str`, `path: str`
- `RequirementChange` requires `before: str`, `after: str`, optional `acceptance_criteria: tuple[str, ...]`
- `ArtifactUniverse` requires `artifacts: tuple[ArtifactRef, ...]`
- `Scenario` has `scenario_id`, `repository`, `change_type`, `blast_radius`, `requirement_before`, `requirement_after`, etc.

Passing `Scenario` where these distinct types are expected violates the protocol contract. Any concrete strategy implementation would receive a `Scenario` object instead of the domain objects it was designed to process.

## Why the Fix Aligns with the Frozen Protocol

The fix adds three private extraction methods that construct the correct domain objects from a `Scenario`:

1. `_build_repository_snapshot(scenario)` → `RepositorySnapshot` using `scenario.repository` for identity and path, `scenario.scenario_id` for commit_sha
2. `_build_requirement_change(scenario)` → `RequirementChange` using `scenario.requirement_before/after` and mapping `AcceptanceCriterion` descriptions to strings
3. `_build_artifact_universe(scenario)` → `ArtifactUniverse` using `scenario.expected_affected_artifacts` directly (already `tuple[ArtifactRef, ...]`)

The `_run_attempt` method now constructs these objects and passes them with the correct types. No `type: ignore` comments are needed. The `ImpactStrategy` protocol is unchanged.

## Confirmation: No Scientific Protocol Changed

This fix is purely an engineering correction. It does not alter:

- The frozen research protocol documents (8 SHA-256 checksums unchanged)
- The `ImpactStrategy` protocol signature
- The `Scenario` model or its fields
- Any strategy implementation logic
- Any evaluation, metrics, or statistical analysis
- The benchmark data (scenarios, manifests, profiles)

The fix ensures that strategy implementations receive the correct domain objects they were designed to process, rather than a `Scenario` wrapper.

## Quality Gates

| Gate | Result |
|------|--------|
| `python -m pytest` | 289/289 passed (3.24s) |
| `ruff check src tests` | All checks passed (0 violations) |
| `mypy --strict src tests` | Success: no issues found (73 files) |
| `python -m pip check` | No broken requirements (pre-existing conda env conflicts only) |
