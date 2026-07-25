# SU-0010A — Minimal Shared Regeneration Path

**Change ID:** SU-0010A
**Title:** Minimal Shared Regeneration Path
**Date:** 2026-07-25
**Requirement or defect:** Current benchmark execution terminates at impact analysis (ImpactPrediction → RunRecord). No regeneration or validation occurs. Need the smallest real end-to-end regeneration path: ImpactStrategy → planner → executor → validator → RunRecord.
**Reason for change:** Enable actual file regeneration and functional validation in isolated workspaces, not just impact prediction.
**Research/protocol impact:** None — execution layer only. Impact strategies, benchmark data, and frozen protocol documents unchanged.

## Canonical Artifacts Affected
- `src/benchmark/core/models.py` — Added 19 optional/defaulted fields to RunRecord
- `src/benchmark/selection/planner.py` — Added compute_artifact_counts(), RegenerationPlan properties, deterministic policy documentation
- `src/benchmark/execution/runner.py` — Added _run_regeneration_flow(), RunnerConfig.enable_regeneration/validation_command/validation_timeout, forward new RunRecord fields from repair loop
- `src/benchmark/execution/__init__.py` — Export new modules
- `src/benchmark/selection/__init__.py` — Export compute_artifact_counts
- `src/benchmark/execution/regeneration.py` — NEW: SharedRegenerationExecutor, GeneratedArtifact, RegenerationExecutionResult, built-in prompt template
- `src/benchmark/execution/validation.py` — NEW: FunctionalValidator, FunctionalValidationResult

## Canonical Artifacts Explicitly Unaffected
- `src/benchmark/core/protocols.py` — unchanged
- `src/benchmark/execution/pipeline.py` — unchanged
- `src/benchmark/strategies/**` — unchanged (agent.py, selective.py, monolithic.py, etc.)

## Correction Dependency-Blocker Exception
- `src/benchmark/execution/repair.py` — Modified as an approved blocker exception: `RepairLoop.execute()` previously reconstructed a new `RunRecord` on failure with only 6 fields (identity, status, prediction, failures, token_usage, duration_seconds), discarding all SU-0010A regeneration metrics. Fixed with `dataclasses.replace()` to preserve all fields when a prior RunRecord exists. Approved during SU-0010A correction pass.
- `src/benchmark/checkpoint/**` — unchanged
- `src/benchmark/statistics/**` — unchanged
- `src/benchmark/comparison/**` — unchanged
- `src/benchmark/strategies/**` — unchanged
- `src/benchmark/graph/**` — unchanged
- `src/benchmark/llm/**` — unchanged
- `seven_arm_benchmark.py` — unchanged
- `benchmark_data/**` — unchanged
- `configs/**` — unchanged
- `notebooks/**` — unchanged

## Changes Implemented

### 1. RunRecord Metrics (`models.py`)
- Added 19 optional/defaulted fields for selection, regeneration, validation, and total workflow metrics
- All fields have defaults (0/False) so old serialized records load properly
- Validation ensures non-negative durations

### 2. Planner Policy (`planner.py`)
- `compute_artifact_counts()` returns regenerate/preserve/human_review counts from an ImpactPrediction
- `RegenerationPlan.regenerate_artifact_paths` and `.human_review_artifact_paths` properties
- Deterministic ordering: regenerate → human_review → validate_only
- Preserve artifacts excluded from execution plan

### 3. SharedRegenerationExecutor (`regeneration.py` NEW)
- Types: `GeneratedArtifact`, `RegenerationExecutionResult`, `SharedRegenerationExecutor`
- Receives RegenerationPlan and IsolationContext
- Reads source files from isolated workspace only
- Builds bounded prompt with requirement delta, artifact path, current content
- Calls existing LLMBackend interface
- Rejects malformed/empty responses
- Rejects path traversal
- Writes generated content only inside isolated workspace
- Records: prompt/completion/total tokens, model calls, duration, per-artifact status
- Human_review artifacts skipped (recorded as unresolved)
- Sequential processing; no parallel execution

### 4. FunctionalValidator (`validation.py` NEW)
- Types: `FunctionalValidationResult`, `FunctionalValidator`
- Runs one explicit command in workspace directory
- Enforces timeout, captures exit code, stdout, stderr
- Returns pass/fail with duration

### 5. Runner Integration (`runner.py`)
- New `_run_regeneration_flow()` method called when `enable_regeneration=True` and backend is not None
- Flow: prediction → ArtifactSelector → RegenerationPlanner → SharedRegenerationExecutor → FunctionalValidator → RunRecord
- All metrics propagated through RepairLoop to final RunRecord
- Legacy impact-only path unchanged when `enable_regeneration=False`

### 6. Tests (39 total)
- 11 planner tests (3 new for properties, 3 new for compute_artifact_counts)
- 10 regeneration executor unit tests
- 7 functional validator unit tests
- 11 integration tests covering full_scope, hybrid_selective, comparison, legacy, token accounting, artifact selection

## Pre-change Evidence
- Runner produced RunRecord directly from ImpactPrediction (no regeneration/validation)
- No SharedRegenerationExecutor existed
- No FunctionalValidator existed
- RunRecord had no regeneration or validation metrics

## Git History
- **Branch:** `fix/su-0010a-minimal-shared-regeneration`
- **Branch commit:** `cae20b5` (initial implementation), `8cb9c61` (metrics update), `ae33330` (docs: fill commit hash)
- **Correction commit:** `HEAD` after applying targeted SU-0010A corrections
- **Merge commit:** TBD (not merged)
- **Final main commit:** TBD

## Correction Pass (SU-0010A corrections applied 2026-07-25)

### Correction 1 — Empty selective scope stays empty
Removed fallback in `ArtifactSelector.select()` that silently converted empty selective predictions to full-scope selection. A prediction with only `preserve` decisions now correctly produces an empty `ArtifactSelection`, an empty `RegenerationPlan`, and zero regeneration calls. `full_scope_reference` strategies (e.g., `MonolithicRegenerationStrategy`) still select all eligible artifacts through their own decisions.

### Correction 2 — Validation tri-state semantics
`RunRecord.functional_validation_passed` changed from `bool = False` to `bool | None = None`. Semantics: `None` = validation not executed, `True` = validation passed (exit 0), `False` = validation failed or timed out. When `enable_regeneration=True` and `validation_command` is missing/empty/whitespace-only, the runner fails closed with a configuration error before claiming success.

### Correction 3 — Actual regenerated artifact count
`regenerated_artifact_count` computed from executor results (`sum(1 for a in exec_result.artifacts if a.status == "generated"`) instead of planned decisions. Artifacts with status rejected, skipped, or failed are no longer counted as regenerated. `selected_artifact_count` still reflects planned scope.

### Correction 4 — Model-call aggregation
`total_workflow_model_calls = selection_model_calls + regeneration_model_calls`. For currently supported SU-0010A strategies (Monolithic, HybridSelective), `selection_model_calls = 0` since they are rule-based.

### Correction 5 — Selection duration
`selection_duration_seconds` measured around `strategy.analyze_impact()`. `total_workflow_duration_seconds = selection_duration_seconds + regeneration_duration_seconds + functional_validation_duration_seconds`. All stage durations are non-negative.

### Correction 6 — Malformed output rejection
Generation output is now rejected when: empty, whitespace-only, starts with Markdown code fence (`` ``` ``), or ends with Markdown code fence. Rejected output does not modify workspace files. Token and model-call accounting still reflects the actual model call.

### Correction 7 — Workspace isolation preserved
All writes remain inside isolated workspace. Canonical sources remain byte-identical. Path traversal and absolute paths outside workspace are rejected. Empty plans modify nothing.

### Correction 8 — Asyncio test-order regression
**Root cause:** `SharedRegenerationExecutor.execute()` used `asyncio.run()`, which in Python 3.11 closes the event loop and leaves the thread-local loop reference pointing to a closed loop. Subsequent calls to `asyncio.get_event_loop().run_until_complete()` in `RepositoryAgentStrategy.analyze_impact()` would fail when the Agent tests ran after SU-0010A tests in the same session.

**Fix:** Save the previous event loop before `asyncio.run()` and restore it afterward. If no previous loop existed, set a fresh event loop. This prevents cross-test pollution without modifying `agent.py`.

### Dependency-blocker: repair.py
`RepairLoop.execute()` reconstructed a new `RunRecord` on failure with only 6 fields, discarding all SU-0010A regeneration/validation/selection metrics. Fixed with `dataclasses.replace()` to preserve all fields when a prior `RunRecord` exists. Approved as a blocker exception during the correction pass.

## Post-correction Evidence
- All 779 tests pass (29 new SU-0010A correction tests)
- Bundle rebuilt and verified (code OK, data OK, notebook OK)
- Empty selective scope remains empty (zero model calls, zero regenerated artifacts)
- Empty selective scope does not modify workspace files
- Full-scope reference still regenerates all eligible fixture artifacts
- Missing validation (None command) fails closed
- Validation tri-state correctly distinguishes None/True/False
- Actual regenerated count matches executor-generated artifacts only
- Planned-but-rejected artifacts not counted as regenerated
- Total model calls equal selection + regeneration calls
- Selection duration measured and non-negative
- Total workflow duration equals selection + regeneration + validation durations (±0.01s tolerance)
- Markdown-fenced generation output rejected
- Rejected output does not modify workspace files
- Canonical source files remain byte-identical
- asyncio test-order regression eliminated: Agent tests pass after SU-0010A tests in the same session
- ruff strict pass on all changed files
- mypy strict pass on all production files
- pip check: no new dependency issues
- Code bundle verification passes
- Data and notebook bundles unchanged

## Ground-Truth Universe Boundary (Correction Record)
BLOCKING_BEFORE_SCIENTIFIC_SMOKE — NOT_BLOCKING_FOR_MINIMAL_VERTICAL_SLICE_MERGE

SU-0010A operates on controlled fixture artifact universes.
The current Runner still derives ArtifactUniverse from
scenario.expected_affected_artifacts.
This is not valid for confirmatory execution and must be replaced
before Scientific Smoke/Pilot with a repository-derived eligible
artifact universe that does not expose ground truth.

## Dataset Update Truth (Final Correction Pass)
Code Dataset:
UPDATE REQUIRED before any future Kaggle deployment,
because kaggle_upload/code changed.

Data Dataset:
NO UPDATE REQUIRED.

Notebook:
NO UPDATE REQUIRED.

## Known Limitations (deferred to SU-0010B)
- Checkpoint/resume schemas not extended for regeneration metrics
- Reporting/statistics don't include regeneration or validation metrics
- No repair loop for regeneration failures
- No parallel task execution
- No generalized unified-diff framework
- Validation requires explicit command (no repo-specific command inference)
- Kaggle deployment not updated to enable regeneration path

- Deployment status: bundle_built_not_uploaded
- Quality outcome: preserved
