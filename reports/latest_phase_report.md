# R3C — Acceptance Correction

**Date:** 2026-07-29
**Status:** R3C CORRECTION SELF-GATES PASSED — INDEPENDENT AUDIT PENDING
**Branch:** `experiment/three-arm-smoke-v2`
**Code commit:** `81429c1`
**Starting HEAD:** `64a3032`

R3C was not accepted at checkpoint `0d168d0`. The independent audit (GPT-5.6 Thinking) identified seven root defects. All are closed in this correction.

## Root defect corrections

### A — Evaluator asset trust
- Lexical symlink checked before `resolve()`
- Workspace evaluator leakage rejected (`<workspace>/tests/evaluator_assets` forbidden)
- String-prefix containment replaced with `Path.relative_to`

### B — Runner tests prove their names
- Command/env/cwd/timeout captured via monkeypatched subprocess
- Truth table calls public `run_scenario_evaluator`
- Subprocess exception types all return typed `_EvaluatorCommandOutcome`
- Copy/trust tests verify byte-level isolation

### C — All three evaluator scripts always emit one JSON object
- Identical `try/except/finally` flow with `_record_check` wrapper
- Catches `Exception`, not only `AssertionError`
- `os.environ["DJANGO_SETTINGS_MODULE"]` direct assignment, not `setdefault`

### D — Smoke 001 complete semantics
Task.Priority TextChoices, field choices, default MEDIUM, valid/invalid values, serializer choice field, priority filter, unfiltered list, baseline fields, project/tag regression

### E — Smoke 002 uses `_base_manager`
Removed `all_objects` name dependency. Soft delete retains row, sets timestamp, default manager excludes, normal list excludes, detail 404, deleted action lists, restore clears timestamp, data preserved

### F — Smoke 003 complete owner authority
Project owner field, creator becomes owner, read-only, owner can write, non-owner forbidden, task create/update/delete uses project owner, reads unrestricted, tag permissions

### G — Fixture architecture uses R3B production path
- Calls `run_post_generation_command` (no direct subprocess)
- Never deletes baseline migrations
- One-fault variants via `_apply_single_replacement` (626 lines, was 1778)
- Exactly one new migration per fixture; 3 baseline hashes preserved

### H — Integration tests assert named failures
- Correct variants assert exact check tuples
- Negative variants assert the expected failed check name appears in `result.error`

## Twelve fixture outcomes

| Scenario | Variant | Expected | Result |
|----------|---------|----------|--------|
| todo-smoke-001 | correct | passes, 10 checks in exact order | PASSED |
| todo-smoke-001 | wrong_default | fails, `task_priority_default` in error | PASSED |
| todo-smoke-001 | missing_filter | fails, `task_priority_filter` in error | PASSED |
| todo-smoke-001 | invalid_serializer_choice | fails, `task_serializer_priority` in error | PASSED |
| todo-smoke-002 | correct | passes, 9 checks in exact order | PASSED |
| todo-smoke-002 | hard_delete | fails, `soft_delete_retains_row` in error | PASSED |
| todo-smoke-002 | deleted_visible_in_normal_list | fails, `default_manager_excludes_deleted` in error | PASSED |
| todo-smoke-002 | restore_keeps_timestamp | fails, `restore_action_restores` in error | PASSED |
| todo-smoke-003 | correct | passes, 10 checks in exact order | PASSED |
| todo-smoke-003 | task_owner_authority | fails, `task_update_uses_project_owner` in error | PASSED |
| todo-smoke-003 | project_non_owner_write_allowed | fails, `project_non_owner_forbidden` in error | PASSED |
| todo-smoke-003 | project_owner_writable | fails, `project_owner_read_only` in error | PASSED |

## Quality gates

| Gate | Result |
|------|--------|
| Full pytest | 1391 passed, 27 skipped, 0 failed |
| Ruff (7 authorized files) | 0 errors |
| Mypy strict (scenario_evaluator.py) | 0 errors |
| Compileall (runner + 3 assets) | All pass |
| git diff --check | Clean |

## Project status

```
R3B accepted and frozen at feb5a44
R3C correction self-gates passed
R3C independent audit pending
R3D blocked
Kaggle/Pilot/merge/tag blocked
```

R3C_ACCEPTANCE_CORRECTION_AUDIT_REQUIRED
# hash comparison (only sets existing_unchanged to False, never restores)
# created_paths always computed from after.hashes
# full hash-change diagnostics always emitted
passed = before.trusted and after.trusted and existing_unchanged
```

When the after-state is untrusted due to a separate unsafe entry (e.g. a symlink file), valid ordinary numbered migration paths created by the subprocess now appear in `created_paths` as truthful partial evidence, while `passed`, `exit_code`, and `existing_migrations_unchanged` all correctly indicate failure.

### Test changes

| Test | Class | Type |
|------|-------|------|
| `test_internal_directory_symlink` | TestTrustedMigrationSnapshot | New — unit proof |
| `test_internal_directory_symlink_public_path` | TestPublicOrchestration | New — public path |
| `test_synthetic_cross_platform_assessment` | TestMigrationAssessment | New — platform-independent |
| `test_created_paths_preserved_when_after_untrusted` | TestMigrationAssessment | Updated — contract change |

### Test results

| Metric | Value |
|--------|-------|
| Focused tests (post_generation) | 109 passed + 12 skipped (symlink unavailable) = 121 total |
| Adjacent execution tests | 265 passed + 11 skipped = 276 total |
| Full suite | 1314 passed, 22 skipped |
| Ruff | 0 errors |
| Mypy strict (changed production files) | 0 errors |
| Compileall | 0 errors |
| git diff --check | clean |

### State

| Item | Status |
|------|--------|
| R3B previous root refactor | `f8f95d2` |
| R3B cross-platform freeze code commit | `feb5a44` |
| R3B final status | CROSS-PLATFORM FREEZE — INDEPENDENT AUDIT PENDING |
| R3C isolated scenario evaluator | BLOCKED — pending independent audit |
| R3D-R6 | NOT STARTED |
| Kaggle | BLOCKED |
| Pilot | BLOCKED |
| Merge | BLOCKED |
| Stable tag | BLOCKED |

---

## Git History

| Commit | Description |
|--------|-------------|
| `feb5a44` | fix(validation): close cross-platform migration snapshot contract |
| `f8f95d2` | refactor(validation): model migration execution as trusted states |
| `fddd26f` | docs(audit): record R3B acceptance closure |
| `f8faa08` | fix(validation): fail on untrusted migration after-state |
| `c635e42` | fix(validation): reject unsafe migration entries and malformed execution input |
| `c873d9f` | fix(validation): close migration runner safety gaps |
| `c11f25e` | feat(validation): add deterministic migration runner |

---

---

# R3C — Single-Pass Isolated Scenario Evaluator System

**Date:** 2026-07-29
**Status:** R3C SINGLE-PASS IMPLEMENTATION — INDEPENDENT AUDIT REQUIRED
**Branch:** `experiment/three-arm-smoke-v2`

## Summary

Section B (R3C) of the master specification has been implemented as a single pass. The isolated scenario evaluator system validates Django-based evaluator assets via subprocess execution in dedicated temporary workspaces, with deterministic mock responses, exact JSON payload validation, and typed result objects.

## Architecture

The evaluator (`src/benchmark/execution/scenario_evaluator.py`) follows a four-state pipeline:

1. **InputValidation** — validates evaluator path, config, timeout, required keys; rejects empty paths, missing keys, non-serialisable config, negative timeouts
2. **TrustedAsset** — verifies source path exists within permitted directory; resolves symlinks; rejects escape attempts
3. **Subprocess** — runs `uv run -m pytest --no-header -q --json-report=...` with 120s default timeout; captures stdout, stderr, return code; handles file-not-found, timeout, non-zero exit
4. **PayloadParsing** — reads JSON report, validates summary/collectors/tests/created/duration/exitcode; maps exitcode+test outcomes to `EvaluatorVerdict`

## Fixtures

Three Django workspace builders (`tests/support/evaluator_fixture_workspaces.py`) each produce four variants (correct + three incorrect):

- **Smoke-001** — Task model with Priority enum, CharField choices, DRF serializer, priority-filter viewset
- **Smoke-002** — SoftDeleteModel (is_deleted, deleted_at), default manager exclusion, restore action
- **Smoke-003** — Owner-based permission system, creator-as-owner, UnrestrictedIsOwnerOrAdmin permission

Key design fixes discovered: `_base_manager` is read-only (replaced with `all_objects`), `Priority` inner class must be inside `Task` (not module-level), non-nullable `Project.owner` requires `null=True, blank=True`.

## Tests

| Module | Count |
|--------|-------|
| `test_scenario_evaluator.py` (unit) | 47 |
| `test_todo_smoke_evaluator_assets.py` (integration) | 17 |
| **Total new** | **64** |

## Quality Gates

| Gate | Result |
|------|--------|
| Full pytest | 1376 passed, 24 skipped, 0 failed |
| Ruff | 0 errors |
| Mypy strict | 0 errors |
| py_compile (all new) | All pass |
| git diff --check | Clean |

## Git History

| Commit | Description |
|--------|-------------|
| `0d168d0` | feat(validation): add isolated scenario evaluator system |
| `341cc99` | docs(audit): record R3B cross-platform freeze candidate |
| `feb5a44` | fix(validation): close cross-platform migration snapshot contract |
| `f8f95d2` | refactor(validation): model migration execution as trusted states |
| `fddd26f` | docs(audit): record R3B acceptance closure |
| `f8faa08` | fix(validation): fail on untrusted migration after-state |
| `c635e42` | fix(validation): reject unsafe migration entries and malformed execution input |
| `c873d9f` | fix(validation): close migration runner safety gaps |
| `c11f25e` | feat(validation): add deterministic migration runner |

---

**R3C_SINGLE_PASS_IMPLEMENTATION_AUDIT_REQUIRED**
