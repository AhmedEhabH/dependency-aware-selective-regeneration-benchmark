# R3B — Final Cross-Platform Freeze Candidate

**Date:** 2026-07-29
**Status:** R3B CROSS-PLATFORM FREEZE — INDEPENDENT AUDIT PENDING
**Branch:** `experiment/three-arm-smoke-v2`
**Code commit:** `feb5a44` (fix(validation): close cross-platform migration snapshot contract)
**Previous R3B root-refactor code-checkpoint:** `f8f95d2`

---

## Corrections applied

### 1. Reject lexical migration-directory symlink before resolve

The previous symlink check in `_take_migration_snapshot` tested `resolved.is_symlink()` after `mig_dir.resolve(strict=True)`. After resolution, `resolved` points to the symlink target and is no longer a symlink path. An internal directory symlink whose target remains inside the workspace would pass the check, producing a false success.

The fix moves the `is_symlink()` check to `mig_dir` before resolution, wrapped in the same narrow filesystem exception handling used for snapshot operations. Internal and external directory symlinks both fail closed.

### 2. Preserve valid ordinary numbered migration paths as partial evidence

When an after-state snapshot is untrusted (e.g. because a separate unsafe symlink entry exists), `_assess_migration_change` previously returned early with empty `created_paths`. The independent Linux audit identified two failing tests that expected valid ordinary numbered migration paths to remain visible.

The fix removes the early return. It computes `existing_unchanged` as `before.trusted and after.trusted` (not as `True`), still compares known old hashes for diagnostic completeness (but never restores `existing_unchanged` to `True` after an untrusted snapshot), always calculates valid numbered created paths from `after.hashes`, and evaluates the final `passed` expression as `before.trusted and after.trusted and existing_unchanged` (plus the optional migration-count check).

Result: `passed=False`, `exit_code=-1`, `existing_migrations_unchanged=False`, valid ordinary numbered paths appear in `created_paths`, unsafe entries remain excluded.

## Test coverage added

| Test | Class | Purpose |
|------|-------|---------|
| `test_internal_directory_symlink` | TestTrustedMigrationSnapshot | Unit proof that internal dir symlink is caught before resolve |
| `test_internal_directory_symlink_public_path` | TestPublicOrchestration | Public-path proof that internal symlink forces `passed=False`, `exit_code=-1`, `existing_unchanged=False` |
| `test_synthetic_cross_platform_assessment` | TestMigrationAssessment | Platform-independent synthetic proof that valid paths survive untrusted after-state |
| `test_created_paths_preserved_when_after_untrusted` | TestMigrationAssessment | Renamed and updated to match new preserved-path contract |

## Gate results

| Gate | Result |
|------|--------|
| Focused `-k "partial or assessment"` | 16 passed |
| Full test_post_generation.py | 109 passed, 12 skipped (Windows symlink) |
| Combined + validation | 118 passed, 12 skipped |
| Full suite | 1314 passed, 22 skipped |
| Ruff | 0 violations |
| Mypy strict | 0 errors |
| compileall | 0 errors |
| git diff --check | clean |

## Phase authorization

Implementation self-gates passed.
Independent audit pending.
Next phase (R3C) remains blocked.
