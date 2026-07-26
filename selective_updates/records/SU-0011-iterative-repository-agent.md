# SU-0011 — Iterative Repository Agent

**Change ID:** SU-0011
**Title:** Iterative Repository Agent (Audit Corrections Applied)
**Date:** 2026-07-26
**Requirement or defect:** Current `RepositoryAgentStrategy` is a single-shot LLM scope baseline — one LLM call, no iteration, no validation feedback. For confirmatory comparison (RD-V2-01), an iterative agent that inspects repository state, revises its plan, selects artifacts, regenerates, validates, and uses validation feedback within strict execution budgets is required. Audit corrections applied: cumulative token accounting, budget exhaustion check between reasoning and regeneration, fair token-budget semantics across arms, requires_iteration control state (no magic string), backend exception propagation (no broad catch), type-ignore removal, and documentation updates.
**Reason for change:** Enable fair end-to-end comparison between iterative LLM-based planning and hybrid selective strategies. The iterative agent is the primary experimental arm.
**Research/protocol impact:** None — new strategy arm added alongside existing ones. Protocol v1.0 unchanged.

## Canonical Artifacts Affected
- `seven_arm_benchmark.py` — Added `iterative_repository_agent` to `STRATEGY_NAMES`, `STRATEGY_CAPABILITIES_DESIGN`, `make_strategy()`, `describe_capabilities()`
- `src/benchmark/execution/runner.py` — Added `iterative_repository_agent` to approved strategies, `_run_iterative_flow()` orchestrator, `_build_workspace_summary()` helper, `record_tokens` for strategy calls
- `src/benchmark/strategies/iterative_agent.py` — NEW: `IterativeRepositoryAgentStrategy` class with `analyze_impact()` and `revise_plan()` methods
- `src/benchmark/strategies/__init__.py` — Export `IterativeRepositoryAgentStrategy`
- `tests/integration/test_su0011_iterative_agent.py` — NEW: 18 integration tests
- `tests/integration/test_su0010a_regeneration.py` — Added guard test for `iterative_repository_agent` in `TestStrategyGuard`
- `tests/unit/execution/test_regression_fixes.py` — Added `iterative_repository_agent` to frozen design constants

## Canonical Artifacts Explicitly Unaffected
- `src/benchmark/core/models.py` — unchanged
- `src/benchmark/core/protocols.py` — unchanged
- `src/benchmark/core/enums.py` — unchanged
- `src/benchmark/execution/regeneration.py` — unchanged (reused `SharedRegenerationExecutor`)
- `src/benchmark/execution/validation.py` — unchanged (reused `FunctionalValidator`)
- `src/benchmark/execution/budgets.py` — unchanged
- `src/benchmark/selection/planner.py` — unchanged (reused `ArtifactSelector`, `RegenerationPlanner`)
- `src/benchmark/strategies/**/*.py` — other strategies unchanged
- `src/benchmark/checkpoint/**` — unchanged
- `benchmark_data/**` — unchanged
- `configs/**` — unchanged
- `notebooks/**` — unchanged

## Changes Implemented

### 1. Strategy Class (`strategies/iterative_agent.py` NEW)
- `IterativeRepositoryAgentStrategy` with two methods:
  - `analyze_impact()` — Initial single-shot analysis using `INITIAL_PROMPT_TEMPLATE`
  - `revise_plan()` — Revision using `REVISE_PROMPT_TEMPLATE` with validation feedback, workspace summary, remaining budget
- JSON-based response parsing with `requires_iteration` stop signal
- Token usage propagation via `object.__setattr__` (ImpactPrediction is frozen)
- Error handling for JSON parse failures, invalid decisions, unknown paths
- `__iterative_stop__` sentinel error signals no further iterations needed

### 2. Registration (`seven_arm_benchmark.py`)
- Added to `STRATEGY_NAMES` as 8th arm
- `STRATEGY_CAPABILITIES_DESIGN` entry: `{"llm": True, "graph": False}`
- `make_strategy()` creates `IterativeRepositoryAgentStrategy(backend=backend)`
- `describe_capabilities()` imports and class maps updated

### 3. Runner Orchestration (`runner.py`)
- Approved strategies set includes `iterative_repository_agent`
- Dispatch in `run()`: if `enable_regeneration and strategy_name == "iterative_repository_agent"`, calls `_run_iterative_flow(scenario, start_time)`
- `_run_iterative_flow()`:
  - Iterative loop bounded by `max_attempts` and `max_tokens`
  - Iteration 0: `analyze_impact()` for initial planning
  - Iterations 1+: `revise_plan()` with validation feedback, workspace summary, remaining budget
  - Regeneration via `SharedRegenerationExecutor`
  - Validation via `FunctionalValidator`
  - Strategy calls counted as model calls against token budget (`self._budget.record_tokens()`)
  - Stop conditions: validation pass, `__iterative_stop__`, budget exhaustion, timeout, error
  - All selection/regeneration/validation metrics aggregated
- `_build_workspace_summary()`: formats previous decisions and generated artifact previews

### 4. Tests (18 new integration tests)
- Single iteration success
- Two iterations (fail then succeed)
- Changes artifact selection after feedback
- Validation output in revise prompt
- Workspace content in revise prompt
- No ground truth leakage
- Agent stop signal prevents iteration
- Max attempts bounds iterations
- Token budget stops agent reasoning
- Timeout stops loop
- Non-repairable failures (config, backend)
- Source/snapshot immutability preserved
- Selection metrics counted once per decision
- Regeneration metrics aggregated
- Validation duration aggregated
- No double counting
- Checkpoint-compatible output
- SU-0010A guard test for iterative_repository_agent

## Pre-change Evidence
- Benchmark had 7 arms; no iterative agent existed
- Runner had no iterative flow; `analyze_impact` called once per run

## Git History
- **Branch:** `feature/su-0011-iterative-repository-agent`
- **Branch commit:** based on main at `2f7697b`

## Quality Gates
- Full test suite: 932 passed, 16 skipped, 0 failed
- ruff: 0 errors in changed files (4 pre-existing E501 cosmetic line-length warnings in string literals)
- mypy strict: 0 errors across all 70 source files

## Audit Corrections Applied
1. **Cumulative token accounting:** `BudgetManager.record_tokens()` now accumulates within one attempt (the per-attempt snapshot accumulates all `record_tokens` calls).
2. **Budget check between reasoning and regeneration:** After recording agent tokens, `_run_iterative_flow` checks `can_attempt` before starting regeneration; exhausted budget prevents regeneration and preserves agent metrics.
3. **Fair token-budget semantics:** Non-iterative regeneration arms now also record selection tokens against `max_tokens`. The budget meaning is consistent: total model-token budget = selection/agent tokens + regeneration tokens.
4. **requires_iteration control state:** Replaced magic `__iterative_stop__` string with `last_requires_iteration` read-only property. `requires_iteration=false` with no decisions stops immediately; with decisions executes once then stops.
5. **Backend exception propagation:** Removed broad `except Exception` in `analyze_impact()` and `revise_plan()`; `ModelBackendError` and runtime failures propagate to the runner's existing error handling.
6. **Type-ignore removal:** Replaced `# type: ignore[attr-defined]` with `getattr` capability check; removed `artifact_type=None` malformed entry handling (entries are now skipped); added `assert self._backend is not None` in place of type ignores for `SharedRegenerationExecutor`.
7. **Documentation:** Updated README.md with Comparison Arms section; updated PROJECT_HANDOFF.md, MASTER_IMPLEMENTATION_PLAN.md, SU-0011 record, CHANGE_INDEX.md, and change_metrics.jsonl.

## Known Limitations
- Strategy class not part of `ImpactStrategy` protocol (`revise_plan` is iterative-agent-specific, accessed via `getattr` runtime check)
- Workspace summary uses `last_exec_result` which may be None on first revision (handled safely)
- Budget recording of strategy tokens uses private `_max_tokens`/`_state` attributes (same pattern as existing code)

## Deployment Status: awaiting_merge
## Quality Outcome: preserved
