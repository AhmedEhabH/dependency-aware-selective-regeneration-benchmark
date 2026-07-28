# R3B — Deterministic post-generation migration runner

**Date:** 2026-07-28
**Status:** R3B COMPLETE
**Branch:** `experiment/three-arm-smoke-v2`
**Starting HEAD:** `2370a57` (docs(state): record R3A completion)
**R3B code-checkpoint:** `c11f25e` (feat(validation): add deterministic migration runner)

---

## Summary

R3B created one small production module, `src/benchmark/execution/post_generation.py`, that runs a scenario's post-generation command inside the isolated generated workspace and proves that migration generation is deterministic and safe.

### New public API

- `PostGenerationResult` — frozen dataclass with `passed`, `exit_code`, `stdout`, `stderr`, `duration_seconds`, `created_paths`, `existing_migrations_unchanged`
- `run_post_generation_command` — function with 12 input validation gates, SHA-256 migration hashing, subprocess execution, and after-state integrity checks

### Input validation (fail-closed)

All 12 validators return a typed `PostGenerationResult(exit_code=-1)` with diagnostic in stderr:

1. workspace_root does not exist
2. workspace_root is not a directory
3. command is empty
4. command contains an empty item
5. require_new_migration is not bool
6. timeout <= 0
7. migration_directory is absolute
8. migration_directory contains `..`
9. migration_directory contains backslash
10. migration_directory does not resolve under workspace_root
11. migration_directory does not exist
12. migration_directory is not a directory

### Migration integrity rules

- Before command: SHA-256 hash of every `*.py` file (including `__init__.py`) under `todo/migrations`
- After command: re-hash and compare; changes, deletions, or modifications to old migrations fail
- New migrations must be direct children of the configured directory, end in `.py`, and not be `__init__.py`
- `require_new_migration=True`: exactly one new numbered migration required
- `require_new_migration=False`: count is not gated, but command success and old-file integrity still required
- Output paths are repository-relative sorted POSIX strings

### Subprocess execution

- `subprocess.run` with `list(command)`, `cwd=workspace_root`, `capture_output=True`, `text=True`, `timeout=timeout`
- `shell=False` (default for list form)
- Graceful handling of `TimeoutExpired`, `FileNotFoundError`, `OSError` → typed failure

### Test results

| Metric | Value |
|--------|-------|
| Focused tests | 32 passed |
| Focused + validation execution tests | 41 passed |
| Full suite | 1237 passed, 10 skipped |
| Ruff | 0 errors |
| Mypy strict (changed production files) | 0 errors |
| Compileall | 0 errors |
| git diff --check | clean |

### Evidence for Appendix F review checklist items

1. **Function never writes outside workspace** — all subprocess.run uses `cwd=str(workspace_root)`. No write operations exist outside path resolution checks. Covered in `test_missing_workspace_fails`, `test_workspace_path_is_file_fails`, code review.
2. **Existing migration hashes include `__init__.py`** — `_snapshot_migrations` globs all `*.py` files including `__init__.py`. Tested in `test_existing_init_py_unchanged`, `test_modified_init_py_fails`.
3. **Numbered migration counts exclude `__init__.py`** — `filtered_new` appends only non-`__init__.py` files. Tested in `test_new_init_py_not_counted_as_numbered_migration`.
4. **subprocess command is a list with shell=False** — `list(command)` is passed to `subprocess.run`, no `shell=` kwarg. Default is False. Tested in `test_smoke_command_shape_tuple`.
5. **Timeout and FileNotFoundError become typed failure** — `test_command_timeout_fails` and `test_command_not_found_fails`.
6. **Repository-relative paths use forward slashes on Windows** — `_snapshot_migrations` uses `as_posix()`. Tested in `test_created_path_is_repository_relative_posix`.
7. **No missing migration directory is silently created** — `test_missing_migration_directory_fails`.
8. **Zero exit code is not enough when required migration count is wrong** — `test_zero_new_migrations_fails_when_required`, `test_two_new_migrations_fail_when_required`.
9. **Old migration deletion is detected** — `test_deleted_old_numbered_migration_fails`.
10. **Changed old migration is detected even when the command fails** — code path inspects after-state unconditionally after subprocess (including timeout/FileNotFoundError). Covered by `test_modified_old_numbered_migration_fails`.
11. **All output lists are sorted** — `_snapshot_migrations` uses `sorted(mig_dir.iterdir())`, `new_paths = sorted(after_set - before_set)`. Tested in `test_created_paths_are_sorted`.
12. **Unit tests use temporary directories** — all 32 tests use `tmp_path` fixture, never touch embedded Todo baseline.

### State

| Item | Status |
|------|--------|
| R3B migration runner | COMPLETE — `c11f25e` |
| R3C isolated scenario evaluator | NEXT TASK |
| R3D-R6 | NOT STARTED |
| Kaggle | BLOCKED |
| Pilot | BLOCKED |
| Merge | BLOCKED |
| Stable tag | BLOCKED |

---

## Git History

| Commit | Description |
|--------|-------------|
| `c11f25e` | feat(validation): add deterministic migration runner |
| `2370a57` | docs(state): record R3A completion |
| `3eaab60` | feat(scenarios): add V2 execution metadata |

---

**R3B_MIGRATION_RUNNER_COMPLETE_AUDIT_REQUIRED**
