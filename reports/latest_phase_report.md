# R3B — Final Cross-Platform Freeze Candidate

**Date:** 2026-07-29
**Status:** R3B CROSS-PLATFORM FREEZE — INDEPENDENT AUDIT PENDING
**Branch:** `experiment/three-arm-smoke-v2`
**Reason for freeze:** The independent Linux audit of the R3B root-refactored module found two failing tests and one false success. Both defects are closed by the two corrections in this freeze. No further R3B corrections are authorized by the master spec.

**Previous R3B root-refactor code-checkpoint:** `f8f95d2`
**Cross-platform freeze code-checkpoint:** `feb5a44`

---

## Summary

Two targeted production corrections and four test additions close the cross-platform gap. The public API (`PostGenerationResult`, `run_post_generation_command`) and the four-state architecture (`_ValidatedPostGenerationRequest`, `_MigrationSnapshot`, `_CommandOutcome`, `_MigrationAssessment`) remain unchanged.

### Correction 1: Lexical symlink check before resolve

Location: `_take_migration_snapshot`

Before:
```python
resolved = mig_dir.resolve(strict=True)
if resolved.is_symlink():  # ineffective — resolved is the target
```

After:
```python
if mig_dir.is_symlink():   # catches internal and external symlinks
    return untrusted
resolved = mig_dir.resolve(strict=True)
```

An internal directory symlink whose target remains inside the workspace would previously produce `trusted=True` because `resolved.is_symlink()` returned `False` (the target is not a symlink). The fix checks the lexical path before resolution.

### Correction 2: Preserve valid ordinary created paths as partial evidence

Location: `_assess_migration_change`

Before:
```python
if not after.trusted:
    return _MigrationAssessment(
        passed=False, existing_unchanged=False, created_paths=(), ...
    )
```

After:
```python
existing_unchanged = before.trusted and after.trusted
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
