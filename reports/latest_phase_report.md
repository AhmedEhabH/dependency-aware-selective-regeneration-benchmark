# R3B — Root Refactor: Model Migration Execution as Trusted States

**Date:** 2026-07-28
**Status:** R3B ROOT REFACTOR — INDEPENDENT AUDIT PENDING
**Branch:** `experiment/three-arm-smoke-v2`
**Reason for refactor:** The previous R3B implementation evolved through a sequence of narrow corrections, each fixing a real defect but leaving the mutable control flow structurally fragile. An independent audit found that the snapshot helper treated a missing after-state directory as empty trusted, producing false success for `require_new_migration=False` with an empty directory deleted during execution. The correct response was a bounded root refactor replacing patch-driven control flow with explicit immutable trusted states.

**Previous R3B acceptance-closure:** `f8faa08` (fix(validation): fail on untrusted migration after-state)
**R3B root-refactor code-checkpoint:** `f8f95d2` (refactor(validation): model migration execution as trusted states)

---

## Summary

The internal flow of `post_generation.py` was reorganized around four explicit immutable state types, preserving the public API (`PostGenerationResult`, `run_post_generation_command`):

- `_ValidatedPostGenerationRequest` — typed validated input, removing repeated normalization from the orchestrator
- `_MigrationSnapshot` — owns its own trust conclusion (`trusted: bool`) after validating all 14 filesystem conditions
- `_CommandOutcome` — typed subprocess result, never raises expected exceptions
- `_MigrationAssessment` — deterministic assessment passing only when all invariants hold

The orchestrator follows one explicit expression:

```python
validated request
→ trusted before snapshot
→ typed command outcome
→ trusted after snapshot
→ deterministic migration assessment
→ one final success expression: passed = command_outcome.succeeded and assessment.passed
```

### Changes from the previous mutable flow

- `_validate_inputs` now returns `_ValidatedPostGenerationRequest | str` instead of `tuple[Path, Path] | str`
- `_snapshot_migrations` replaced by `_take_migration_snapshot` returning `_MigrationSnapshot` (trusted bool + hashes + diagnostics)
- Inline subprocess block extracted into `_run_command` returning `_CommandOutcome`
- Inline comparison logic extracted into `_assess_migration_change` returning `_MigrationAssessment`
- A missing after-state directory (even when before was empty and `require_new_migration=False`) now correctly forces `passed=False`, `existing_unchanged=False`, `exit_code=-1`
- Diagnostics from before and after snapshots are always combined into assessment diagnostics
- All 14 trust conditions checked inside `_take_migration_snapshot`, not spread across the orchestrator

### Integrity conditions enforced by `_take_migration_snapshot`

| # | Condition | Result |
|---|-----------|--------|
| 1 | migration directory does not exist | untrusted |
| 2 | migration path is not a directory | untrusted |
| 3 | migration directory is a symlink | untrusted |
| 4 | migration directory resolves outside workspace | untrusted |
| 5 | migration directory resolution raises | untrusted |
| 6 | directory listing raises | untrusted |
| 7 | direct `.py` entry is a symlink | untrusted |
| 8 | direct `.py` entry is not a regular file | untrusted |
| 9 | entry resolves outside migration directory | untrusted |
| 10 | entry resolves outside workspace | untrusted |
| 11 | file disappears during inspection | untrusted |
| 12 | file cannot be read | untrusted |
| 13 | hashing raises | untrusted |
| 14 | relative path conversion fails | untrusted |

### Exit code logic

```
if not command_outcome.succeeded  → exit_code = command_outcome.exit_code
elif passed                        → exit_code = 0
else                               → exit_code = -1
```

### Assessment truth table (parameterized)

| Before trusted | After trusted | Old unchanged | Required | Created | Final |
|:---:|:---:|:---:|:---:|:---:|:---:|
| yes | yes | yes | yes | 1 | pass |
| yes | yes | yes | yes | 0 | fail |
| yes | yes | yes | yes | 2 | fail |
| yes | yes | yes | no | 0 | pass |
| yes | no | unknown | no | 0 | fail |
| yes | no | unknown | yes | 0 | fail |
| yes | yes | no | no | 0 | fail |
| yes | yes | yes | no | 0 | pass (assessment) |
| yes | yes | no | no | 0 | fail |

### Test results

| Metric | Value |
|--------|-------|
| Focused tests (post_generation) | 108 passed + 10 skipped (symlink unavailable) = 118 total |
| Adjacent execution tests | 265 passed + 11 skipped = 276 total |
| Full suite | 1313 passed, 20 skipped |
| Ruff | 0 errors |
| Mypy strict (changed production files) | 0 errors |
| Compileall | 0 errors |
| git diff --check | clean (CRLF warning only) |

### Test organization

| Class | Tests | Scope |
|-------|-------|-------|
| TestInputValidation | 34 | All valid/invalid inputs from spec section 8 |
| TestTrustedMigrationSnapshot | 15 | All 14 trust conditions |
| TestCommandOutcome | 7 | All subprocess error types |
| TestMigrationAssessment | 16 | Truth table + edge cases |
| TestPublicOrchestration | 8 | Production-path adversarial end-to-end |
| TestRegressionCases | 30 | All existing regression tests preserved |
| TestHelpers | 6 | Helper functions |

### State

| Item | Status |
|------|--------|
| R3B previous acceptance closure | `f8faa08` |
| R3B root refactor code commit | `f8f95d2` |
| R3B final status | ROOT REFACTOR — INDEPENDENT AUDIT PENDING |
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
| `f8f95d2` | refactor(validation): model migration execution as trusted states |
| `fddd26f` | docs(audit): record R3B acceptance closure |
| `f8faa08` | fix(validation): fail on untrusted migration after-state |
| `c635e42` | fix(validation): reject unsafe migration entries and malformed execution input |
| `c873d9f` | fix(validation): close migration runner safety gaps |
| `c11f25e` | feat(validation): add deterministic migration runner |

---

**R3B_ROOT_REFACTOR_AUDIT_REQUIRED**
