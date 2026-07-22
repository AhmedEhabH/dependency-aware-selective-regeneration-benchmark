# Phase 4D — Execution Core Reference

**Date:** 2026-07-22
**Protocol Version:** 1.0 (FROZEN)
**Layer:** 8 — Execution Orchestration
**Status:** COMPLETE

## Overview

Phase 4D implements the execution orchestration layer: runner, pipeline, budgets, repair loop, isolation context, and state machine. These components coordinate `ImpactStrategy`, `LLMBackend`, `Scenario`, and `IsolationContext` into `RunRecord` instances through a configurable attempt/repair lifecycle.

## Architecture

```
ScenarioProvider
      │
      ▼
BenchmarkPipeline ──► BenchmarkRunner ──► RepairLoop ──► RunRecord
      │                      │                 │
      │                      ├─ BudgetManager  │
      │                      ├─ RunStateMachine│
      │                      └─ IsolationContext│
      │                                        │
      └─ dry_run ──► BenchmarkRunner.dry_run()
```

## Module Reference

### `budgets.py`

| Class | Responsibility |
|-------|---------------|
| `Clock` (Protocol) | Injectable time source |
| `SystemClock` | Real wall-clock implementation |
| `AttemptSnapshot` | Records per-attempt metadata |
| `BudgetState` | Tracks total attempts, tokens, elapsed time |
| `BudgetManager` | Enforces max_attempts, max_tokens, timeout_seconds |
| `BudgetExhaustedError` | Raised when budget cannot accommodate another attempt |

Key behaviors:
- `record_attempt(tokens)` increments attempt counter and token accumulator
- `can_attempt` returns `False` when exhausted, max attempts reached, or timed out
- `reset()` clears all state for reuse
- Injectable `Clock` protocol enables deterministic testing

### `state_machine.py`

| Class | Responsibility |
|-------|---------------|
| `RunState` (StrEnum) | 6 states: prepared, running, succeeded, failed, timed_out, cancelled |
| `RunStateMachine` | Enforces typed transitions with terminal-state protection |
| `InvalidTransitionError` | Raised on illegal state transitions |

Valid transitions:
```
prepared → running → succeeded
                   → failed
                   → timed_out
                   → cancelled
```
Terminal states (no outgoing transitions): `succeeded`, `failed`, `timed_out`, `cancelled`

### `repair.py`

| Class | Responsibility |
|-------|---------------|
| `RepairOutcome` | Result of repair loop: success/fail, final record, attempt count |
| `RepairLoop` | Executes and repairs with configurable BudgetManager and FailureClassifier |

Key behaviors:
- 1 initial generation + up to 2 repair attempts = max 3 total (default)
- `AttemptGenerator` returns `RunRecord` on success or `BenchmarkError` on infrastructure failure
- Configurable `FailureClassifier` maps failed records to `FailureKind`
- State machine transitioned to `succeeded` or `failed` at end

### `isolation.py`

| Class | Responsibility |
|-------|---------------|
| `IsolationReport` | Pass/fail with violation messages |
| `IsolationContext` | Verifies workspace isolation, private data access, run/temp directory creation |

Key behaviors:
- `verify()` runs `check_isolation` from Phase 4B workspace utilities
- `check_private_data_access()` detects paths containing `private`, `secret`, `hidden`, `.kaggle`, `ground_truth`
- `make_run_directory()` / `make_temp_directory()` create isolated directories

### `runner.py`

| Class | Responsibility |
|-------|---------------|
| `RunnerConfig` | Configuration for a single runner |
| `BenchmarkRunner` | Coordinates strategy + backend + isolation into RunRecord |

Key behaviors:
- `run(scenario)` — Runs strategy through repair loop; returns RunRecord
- `dry_run(scenario)` — Skips strategy execution; returns success RunRecord with 0 duration
- Creates `RunIdentity` with `protocol_version`, `scenario_id`, `strategy_name`
- `BudgetManager` limits attempts per run
- `RunStateMachine` tracks lifecycle

### `pipeline.py`

| Class | Responsibility |
|-------|---------------|
| `PipelineConfig` | Configuration for the pipeline |
| `PipelineResult` | Aggregated result with counts |
| `BenchmarkPipeline` | Orchestrates multiple runs with single/batch/dry-run modes |

Key behaviors:
- `run_scenario(scenario)` — Single scenario through BenchmarkRunner
- `run_scenario_by_id(scenario_id)` — Resolves scenario from provider, then runs
- `run_all(scenario_ids)` — Batch execution with optional scenario filtering
- Dry-run mode skips strategy execution entirely

## Dependencies

- **Phase 4A**: `RunRecord`, `RunStatus`, `FailureKind`, `Budget`, `TokenUsage`, `RunIdentity`, `Scenario`, `FailureRecord`, `ImpactStrategy`, `LLMBackend`, `ExecutionContext`, `ScenarioProvider`
- **Phase 4B**: `WorkspacePath`, `validate_workspace_path`, `check_isolation`
- **Phase 4C**: MockLLMBackend, DryRunLLMBackend, BackendFactory (for integration testing)

## Forbidden Dependencies

This module must never import:
- `benchmark.core.models.ImpactPrediction` (used at runtime via protocol)
- `benchmark.core.models.LLMResponse` (returned by backend, not used directly)
- `benchmark.evaluation` or any scoring/evaluation code
- `private_evaluation/` or any module containing hidden tests or ground truth
- `torch`, `transformers`, `accelerate`, `bitsandbytes`, `datasets`, `kagglehub`

## Export Surface

```python
from benchmark.execution import (
    BenchmarkPipeline,
    BenchmarkRunner,
    BudgetManager,
    IsolationContext,
    RepairLoop,
    RunStateMachine,
)
```
