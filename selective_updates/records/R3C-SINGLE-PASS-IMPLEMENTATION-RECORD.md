# R3C — Single-Pass Isolated Scenario Evaluator System

**Date:** 2026-07-29
**Status:** R3C SINGLE-PASS IMPLEMENTATION — INDEPENDENT AUDIT REQUIRED
**Branch:** `experiment/three-arm-smoke-v2`
**Model:** DeepSeek V4 Flash Free

---

## Requirement

Implement Section B (R3C) of the master specification: an isolated scenario evaluator system that validates Django-based evaluator assets via subprocess execution in dedicated temporary workspaces, with deterministic mock responses, exact JSON payload validation, and typed result objects.

## Implementation Summary

### Production code (`src/benchmark/execution/scenario_evaluator.py`)

Four-state evaluator architecture:

1. **Validation (`_ValidatedEvaluatorRequest`)** — Ensures evaluator paths, config, timeout, and required keys are present and well-typed. Rejects empty paths, missing keys, non-JSON serialisable config, negative timeouts. 20 input validation tests + 2 skipped.

2. **Trust (`_TrustedEvaluatorAsset`)** — Verifies the source path exists within a permitted directory, resolves symlinks safely, and rejects paths that escape the workspace. 2 trust tests.

3. **Execution (`_EvaluatorCommandOutcome`)** — Runs `uv run -m pytest ... --no-header -q --json-report ...` with a 120s default timeout. Captures stdout, stderr, return code. Handles file-not-found, timeout, non-zero exit. 3 subprocess tests.

4. **Payload parsing (`_ParsedEvaluatorPayload`)** — Reads the JSON report file, parses `summary`, `collectors`, `tests`, `created`, `duration`, `exitcode`. Validates `exitcode` ∈ {0,1,2,5}, `tests` is a list, each test has `outcome`, `nodeid`, `duration`. 12 payload parsing tests.

Additional integrity:
- **Truth table** — 4 combinations of exitcode/tests map to EvaluatorVerdict.trusted, .violation, .incomplete, .error
- **Isolation** — 3 tests verifying empty workspace detection, missing source path, missing requirements.txt

### Evaluator fixtures (`tests/support/evaluator_fixture_workspaces.py`)

Three builders with four variants each (correct + three incorrect):
- `build_todo_smoke_001_workspace` — Task model with Priority enum, CharField choices, DRF serializer, priority-filter viewset
- `build_todo_smoke_002_workspace` — SoftDeleteModel (is_deleted, deleted_at), default manager exclusion, restore action
- `build_todo_smoke_003_workspace` — Owner-based permission system, creator-as-owner, UnrestrictedIsOwnerOrAdmin permission

Each builder clears old migrations, runs makemigrations + migrate, overwrites only the required files.

Key fixes discovered during implementation:
- `_base_manager` not assignable in Django model definition — replaced with `all_objects` manager pattern
- `Priority` inner class must be inside `Task`, not at module level
- Non-nullable `Project.owner` ForeignKey needs `null=True, blank=True` to pass makemigrations

### Evaluator assets (`tests/evaluator_assets/todo_smoke_00{1,2,3}_checks.py`)

- Smoke-001: 10 checks (enum, field, default, valid values, serializer, invalid value rejection, priority filter, unfiltered list, baseline fields, project/tag regression)
- Smoke-002: 9 checks (row retention, timestamp, default manager exclusion, normal list exclusion, 404 detail, deleted action listing, restore, data preservation, project/tag regression)
- Smoke-003: 10 checks (owner field, creator-as-owner, read-only exposure, owner write, non-owner forbidden, task create/update/delete authorization, unrestricted reads, tag permission unchanged)

### Integration tests (`tests/integration/test_todo_smoke_evaluator_assets.py`)

12 real subprocess runs (3 scenarios × 4 variants) + 5 integrity tests:
- `test_pytest_does_not_collect` — verifying the evaluator asset doesn't appear in the outer test suite
- `test_json_stdout_contains_payload` — ensuring the JSON report format is preserved
- `test_source_directory_not_copied_to_workspace` — verifying source isolation
- `test_baseline_workspace_unchanged_after_run` — ensuring the evaluator workspace is ephemeral
- `test_exactly_one_migration_file_generated` — checking migration hygiene

### Unit tests (`tests/unit/execution/test_scenario_evaluator.py`)

47 tests total:
- InputValidation: 20 + 2 skipped (mock/unauthenticated backends)
- TrustedAsset: 2
- Subprocess: 3
- PayloadParsing: 12
- TruthTable: 4
- Isolation: 3
- Edge: 1 (empty workspace)

## Quality Gates

| Gate | Result |
|------|--------|
| Full pytest | 1376 passed, 24 skipped, 0 failed |
| Ruff (all Python) | 0 errors, 0 warnings |
| Mypy strict (all Python) | 0 errors |
| py_compile (all new files) | All pass |
| git diff --check | Clean |

## Files Changed

| File | Status |
|------|--------|
| `src/benchmark/execution/scenario_evaluator.py` | NEW (production evaluator) |
| `src/benchmark/execution/__init__.py` | MODIFIED (export `ScenarioEvaluatorResult`, `run_scenario_evaluator`) |
| `tests/unit/execution/test_scenario_evaluator.py` | NEW (47 unit tests) |
| `tests/integration/test_todo_smoke_evaluator_assets.py` | NEW (17 integration tests) |
| `tests/support/evaluator_fixture_workspaces.py` | NEW (fixture workspace builders) |
| `tests/evaluator_assets/todo_smoke_001_checks.py` | NEW (10 evaluator checks) |
| `tests/evaluator_assets/todo_smoke_002_checks.py` | NEW (9 evaluator checks) |
| `tests/evaluator_assets/todo_smoke_003_checks.py` | NEW (10 evaluator checks) |

## Excluded Files (R3B Freeze — not modified)

- `src/benchmark/execution/post_generation.py`
- `tests/unit/execution/test_post_generation.py`
- Runner, Pipeline, token metrics, README, Kaggle bundle, notebooks, Selective, Repository Agent

## Blocked Items

- Kaggle, Pilot, merge, and stable tag: BLOCKED until R3C independent audit passes
- R3D (Kaggle deployment): BLOCKED until R3C accepted

---

## Git History

| Commit | Description |
|--------|-------------|
| `0d168d0` | feat(validation): add isolated scenario evaluator system |
| `341cc99` | docs(audit): record R3B cross-platform freeze candidate |

---

**R3C_SINGLE_PASS_IMPLEMENTATION_AUDIT_REQUIRED**
