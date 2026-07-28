# R3B — Deterministic post-generation migration runner

**Date:** 2026-07-28
**Status:** R3B CORRECTED — INDEPENDENT AUDIT REQUIRED
**Branch:** `experiment/three-arm-smoke-v2`
**Starting HEAD:** `2370a57` (docs(state): record R3A completion)
**R3B code-checkpoint:** `c11f25e` (feat(validation): add deterministic migration runner)
**R3B correction-checkpoint:** `c873d9f` (fix(validation): close migration runner safety gaps)

---

## Summary

R3B created one small production module, `src/benchmark/execution/post_generation.py`, that runs a scenario's post-generation command inside the isolated generated workspace and proves that migration generation is deterministic and safe.

An independent audit (GPT-5.6 Thinking) found 4 production defects and 2 fail-closed gaps. All 6 were corrected in this phase.

### New public API

- `PostGenerationResult` — frozen dataclass with `passed`, `exit_code`, `stdout`, `stderr`, `duration_seconds`, `created_paths`, `existing_migrations_unchanged`
- `run_post_generation_command` — function with input validation gates, SHA-256 migration hashing, subprocess execution, and after-state integrity checks

### Audit defects corrected

| # | Defect | Correction |
|---|--------|-----------|
| A | Relative `workspace_root` raises uncaught `ValueError` | Workspace resolved once at `wr.resolve()` after validation; used throughout |
| B | Unsafe string-prefix path containment | `Path.relative_to` used via `_relative_to_root` helper; `startswith` removed |
| C | `helper.py` incorrectly accepted as required migration | `NUMBERED_MIGRATION_RE = re.compile(r"^\d+_[A-Za-z0-9_]+\.py$")` added; non-numbered `.py` files excluded from created count |
| D | Timeout/exception paths skipped after-state inspection | Command outcome variables set in try/except then common after-state block runs unconditionally |
| E | Plain string accepted as `Sequence[str]` | `isinstance(command, (str, bytes))` rejected before validation loop |
| F | Whitespace-only command items accepted | `len(item) == 0` → `not item.strip()` |

### Input validation (fail-closed)

Validators return a typed `PostGenerationResult(exit_code=-1)` with diagnostic in stderr:

1. command is str or bytes (new — gap E)
2. workspace_root does not exist
3. workspace_root is not a directory
4. command is empty
5. command contains an empty item (now also rejects whitespace-only — gap F)
6. require_new_migration is not bool
7. timeout <= 0
8. migration_directory is absolute
9. migration_directory contains `..`
10. migration_directory contains backslash
11. migration_directory does not resolve under workspace_root (now using `relative_to` — defect B)
12. migration_directory does not exist
13. migration_directory is not a directory

### Migration integrity rules

- Before command: SHA-256 hash of every `*.py` file (including `__init__.py` and non-numbered helpers) under `todo/migrations`
- After command: re-hash and compare; changes, deletions, or modifications to old migrations fail
- New migrations must be direct children of the configured directory, match `NUMBERED_MIGRATION_RE`, and not be `__init__.py`
- Non-numbered `.py` files (e.g. `helper.py`) are no longer accepted as required new migrations
- `require_new_migration=True`: exactly one new numbered migration required
- `require_new_migration=False`: count is not gated, but command success and old-file integrity still required
- After-state inspection runs unconditionally after every subprocess outcome, including timeout and OS errors
- Available stdout/stderr preserved from `TimeoutExpired` via `_coerce_subprocess_text` normalizer
- Output paths are repository-relative sorted POSIX strings

### Subprocess execution

- `subprocess.run` with `list(command)`, `cwd=str(resolved_workspace)`, `capture_output=True`, `text=True`, `timeout=timeout`
- `shell=False` (default for list form)
- Graceful handling of `TimeoutExpired`, `FileNotFoundError`, `OSError` → typed failure; after-state inspected for all

### Test results

| Metric | Value |
|--------|-------|
| Focused tests (post_generation) | 49 passed + 1 skipped (symlink unavailable) = 50 total |
| Focused + validation execution tests | 58 passed |
| Full suite | 1254 passed, 11 skipped |
| Ruff | 0 errors |
| Mypy strict (changed production files) | 0 errors |
| Compileall | 0 errors |
| git diff --check | clean |

### All tests (50 collected)

1. test_valid_command_creates_one_migration_and_passes
2. test_created_path_is_repository_relative_posix
3. test_created_paths_are_sorted (strengthened — exact tuple asserted)
4. test_existing_numbered_migrations_unchanged
5. test_existing_init_py_unchanged
6. test_command_exits_non_zero_fails
7. test_command_timeout_fails
8. test_command_not_found_fails
9. test_missing_workspace_fails
10. test_workspace_path_is_file_fails
11. test_empty_command_fails
12. test_command_with_empty_item_fails
13. test_non_bool_require_new_migration_fails
14. test_zero_timeout_fails
15. test_negative_timeout_fails
16. test_absolute_migration_directory_fails
17. test_traversal_migration_directory_fails
18. test_backslash_migration_directory_fails
19. test_missing_migration_directory_fails
20. test_modified_old_numbered_migration_fails
21. test_deleted_old_numbered_migration_fails
22. test_modified_init_py_fails
23. test_zero_new_migrations_fails_when_required
24. test_two_new_migrations_fail_when_required
25. test_one_new_migration_passes_when_required
26. test_no_new_migration_may_pass_when_not_required
27. test_new_init_py_not_counted_as_numbered_migration
28. test_nested_py_file_not_counted
29. test_new_non_python_file_not_counted
30. test_duration_is_non_negative_for_success
31. test_duration_is_non_negative_for_failure
32. test_smoke_command_shape_tuple (strengthened — monkeypatch, exact call assertions)
33. **test_relative_workspace_root_is_supported_without_exception** (new — defect A)
34. **test_migration_directory_symlink_escape_fails_closed** (new — defect B, skipped on unsupported platform)
35. **test_sibling_prefix_path_is_not_treated_as_inside_workspace** (new — defect B)
36. **test_non_numbered_python_file_does_not_satisfy_required_migration** (new — defect C)
37. **test_numbered_migration_filename_is_required** (new — defect C)
38. **test_existing_non_numbered_python_file_is_still_integrity_protected** (new — defect C)
39. **test_timeout_without_changes_reports_existing_migrations_unchanged** (new — defect D)
40. **test_timeout_after_modifying_old_migration_detects_corruption** (new — defect D)
41. **test_failed_command_after_creating_migration_reports_created_path** (new — defect D)
42. **test_command_not_found_reports_unchanged_existing_migrations** (new — defect D)
43. **test_plain_string_command_fails_validation** (new — gap E)
44. **test_bytes_command_fails_validation** (new — gap E)
45. **test_whitespace_only_command_item_fails** (new — gap F)
46–50. Helper tests for `_coerce_subprocess_text` and `_relative_to_root`

### State

| Item | Status |
|------|--------|
| R3B migration runner (initial) | COMPLETE — `c11f25e` |
| R3B independent audit | FOUND 6 DEFECTS |
| R3B correction commit | `c873d9f` |
| R3B final status | CORRECTED, INDEPENDENT AUDIT REQUIRED |
| R3C isolated scenario evaluator | BLOCKED — R3B audit required |
| R3D-R6 | NOT STARTED |
| Kaggle | BLOCKED |
| Pilot | BLOCKED |
| Merge | BLOCKED |
| Stable tag | BLOCKED |

---

## Git History

| Commit | Description |
|--------|-------------|
| `c873d9f` | fix(validation): close migration runner safety gaps |
| `8c588e6` | docs(state): record R3B completion |
| `c11f25e` | feat(validation): add deterministic migration runner |
| `2370a57` | docs(state): record R3A completion |
| `3eaab60` | feat(scenarios): add V2 execution metadata |

---

**R3B_MIGRATION_RUNNER_CORRECTED_AUDIT_REQUIRED**
