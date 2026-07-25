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
- `src/benchmark/execution/repair.py` — unchanged
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
- **Branch commit:** `cae20b5` (initial), `8cb9c61` (metrics update)
- **Merge commit:** TBD (not merged)
- **Final main commit:** TBD

## Post-change Evidence
- All 716 tests pass (39 new SU-0010A tests)
- Bundle rebuilt and verified (code OK, data OK, notebook OK)
- End-to-end full_scope_reference (monolithic): 3 artifacts regenerated, validation passed, token accounting consistent
- End-to-end hybrid_selective (selective): regenerates strict subset vs full_scope_on_fixture
- Legacy impact-only path produces identical RunRecord behavior with new default fields
- Total workflow tokens consistent with stage sums
- Canonical source files preserved byte-identical (except CRLF→LF normalization in bundle)

## Known Limitations (deferred to SU-0010B)
- Checkpoint/resume schemas not extended for regeneration metrics
- Reporting/statistics don't include regeneration or validation metrics
- No repair loop for regeneration failures
- No parallel task execution
- No generalized unified-diff framework
- Validation requires explicit command (no repo-specific command inference)
- Kaggle deployment not updated to enable regeneration path

- Deployment status: not_deployed
- Quality outcome: preserved
