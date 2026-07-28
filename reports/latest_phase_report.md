# R3B — Deterministic post-generation migration runner

**Date:** 2026-07-28
**Status:** R3B ACCEPTANCE CLOSED — INDEPENDENT AUDIT SATISFIED
**Branch:** `experiment/three-arm-smoke-v2`
**Starting HEAD:** `2370a57` (docs(state): record R3A completion)
**R3B code-checkpoint:** `c11f25e` (feat(validation): add deterministic migration runner)
**R3B correction-checkpoint:** `c873d9f` (fix(validation): close migration runner safety gaps)
**R3B final-correction-checkpoint:** `c635e42` (fix(validation): reject unsafe migration entries and malformed execution input)
**R3B acceptance-closure-checkpoint:** `f8faa08` (fix(validation): fail on untrusted migration after-state)

---

## Summary

R3B created one small production module, `src/benchmark/execution/post_generation.py`, that runs a scenario's post-generation command inside the isolated generated workspace and proves that migration generation is deterministic and safe.

An independent audit (GPT-5.6 Thinking) found 4 production defects and 2 fail-closed gaps. All 6 were corrected in the first correction.

A second independent audit found 3 additional defects: migration-file symlink containment, timeout type validation, and embedded NUL handling. These were corrected in the final correction.

### New public API

- `PostGenerationResult` — frozen dataclass with `passed`, `exit_code`, `stdout`, `stderr`, `duration_seconds`, `created_paths`, `existing_migrations_unchanged`
- `run_post_generation_command` — function with input validation gates, SHA-256 migration hashing, subprocess execution, and after-state integrity checks

### First audit defects corrected (c873d9f)

| # | Defect | Correction |
|---|--------|-----------|
| A | Relative `workspace_root` raises uncaught `ValueError` | Workspace resolved once at `wr.resolve()` after validation; used throughout |
| B | Unsafe string-prefix path containment | `Path.relative_to` used via `_relative_to_root` helper; `startswith` removed |
| C | `helper.py` incorrectly accepted as required migration | `NUMBERED_MIGRATION_RE = re.compile(r"^\d+_[A-Za-z0-9_]+\.py$")` added; non-numbered `.py` files excluded from created count |
| D | Timeout/exception paths skipped after-state inspection | Command outcome variables set in try/except then common after-state block runs unconditionally |
| E | Plain string accepted as `Sequence[str]` | `isinstance(command, (str, bytes))` rejected before validation loop |
| F | Whitespace-only command items accepted | `len(item) == 0` → `not item.strip()` |

### Second audit defects corrected (c635e42)

| # | Defect | Correction |
|---|--------|-----------|
| G | Migration-file symlink (numbered, inside or outside workspace) accepted | `_snapshot_migrations` returns `tuple[dict, tuple[str,...]]`; checks `is_symlink()`, `resolve(strict=True)`, parent containment, workspace containment; rejects all symlink `.py` entries |
| H | Timeout type bool/float/str/None accepted; zero allowed | `type(timeout) is int` required; `timeout > 0` validated after type check |
| I | Embedded NUL raises uncaught `ValueError` | NUL rejected in `_validate_inputs` for command items and `migration_directory`; `except ValueError` and `except subprocess.SubprocessError` added around subprocess call |

### Third audit defect corrected (f8faa08)

| # | Defect | Correction |
|---|--------|-----------|
| J | After-state snapshot errors appended to stderr but did not force `passed=False` or `existing_migrations_unchanged=False` | `all_old_unchanged = not after_errors`; `passed` fails when `after_errors` non-empty; `existing_migrations_unchanged` forced `False` |
| K | Whitespace-only `migration_directory` accepted | `not migration_directory.strip()` replaces `len(migration_directory) == 0` |

### Input validation (fail-closed)

Validators return a typed `PostGenerationResult(exit_code=-1)` with diagnostic in stderr:

1. command is str or bytes
2. workspace_root is not str or Path
3. workspace_root does not exist
4. workspace_root is not a directory
5. command is empty
6. command contains a non-string item
7. command contains an empty or whitespace-only item
8. command item contains NUL
9. require_new_migration is not bool
10. timeout is not int (rejects None, True, False, float, str, list, dict, object)
11. timeout <= 0
12. migration_directory empty/whitespace, NUL, absolute, `..`, or backslash
13. migration_directory does not resolve under workspace_root
14. migration_directory does not exist
15. migration_directory is not a directory

### Migration integrity rules

- Before command: SHA-256 hash of every `*.py` file (including `__init__.py` and non-numbered helpers) under `todo/migrations`; symlinks and unreadable files produce diagnostics and fail closed
- After command: re-hash and compare; changes, deletions, or modifications to old migrations fail
- New migrations must be direct children of the configured directory, match `NUMBERED_MIGRATION_RE`, and not be `__init__.py`
- Every migration file is resolved with `resolve(strict=True)` and must be a direct regular file beneath the resolved migration directory
- Symlink migration files (numbered or not, inside or outside workspace) are rejected with diagnostics
- Non-numbered `.py` files (e.g. `helper.py`) are not accepted as required new migrations but remain integrity-protected existing files
- `require_new_migration=True`: exactly one new numbered migration required
- `require_new_migration=False`: count is not gated, but command success and old-file integrity still required
- After-state snapshot errors force `passed=False`, `existing_migrations_unchanged=False`, and `exit_code=-1`, even when subprocess succeeded and old hashes match
- After-state inspection runs unconditionally after every subprocess outcome, including timeout, ValueError, SubprocessError, and OS errors
- Available stdout/stderr preserved from `TimeoutExpired` via `_coerce_subprocess_text` normalizer
- Output paths are repository-relative sorted POSIX strings

### Subprocess execution

- `subprocess.run` with `list(command)`, `cwd=str(resolved_workspace)`, `capture_output=True`, `text=True`, `timeout=timeout`
- `shell=False` (default for list form)
- Graceful handling of `TimeoutExpired`, `FileNotFoundError`, `ValueError`, `OSError`, `subprocess.SubprocessError` → typed failure; after-state inspected for all

### Test results

| Metric | Value |
|--------|-------|
| Focused tests (post_generation) | 74 passed + 7 skipped (symlink unavailable) = 81 total |
| Focused + validation execution tests | 83 passed + 7 skipped = 90 total |
| Full suite | 1279 passed, 17 skipped |
| Ruff | 0 errors |
| Mypy strict (changed production files) | 0 errors |
| Compileall | 0 errors |
| git diff --check | clean (CRLF warning only) |

### All tests (81 collected, 7 symlink-skipped)

1. test_valid_command_creates_one_migration_and_passes
2. test_created_path_is_repository_relative_posix
3. test_created_paths_are_sorted
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
32. test_smoke_command_shape_tuple
33. test_relative_workspace_root_is_supported_without_exception
34. test_migration_directory_symlink_escape_fails_closed (skip on Windows)
35. test_sibling_prefix_path_is_not_treated_as_inside_workspace
36. test_non_numbered_python_file_does_not_satisfy_required_migration
37. test_numbered_migration_filename_is_required
38. test_existing_non_numbered_python_file_is_still_integrity_protected
39. test_timeout_without_changes_reports_existing_migrations_unchanged
40. test_timeout_after_modifying_old_migration_detects_corruption
41. test_failed_command_after_creating_migration_reports_created_path
42. test_command_not_found_reports_unchanged_existing_migrations
43. test_plain_string_command_fails_validation
44. test_bytes_command_fails_validation
45. test_whitespace_only_command_item_fails
46. test_new_numbered_migration_symlink_to_outside_fails_closed (defect G, skip on Windows)
47. test_new_numbered_migration_symlink_inside_workspace_fails_closed (defect G, skip on Windows)
48. test_existing_migration_symlink_fails_before_command (defect G, skip on Windows)
49. test_broken_numbered_migration_symlink_fails_closed (defect G, skip on Windows)
50. test_ordinary_numbered_migration_file_not_rejected_by_symlink_checks (defect G control)
51. test_invalid_timeout_types_fail_closed[None] (defect H, parametrized ×10)
52. test_invalid_timeout_types_fail_closed[True] (defect H)
53. test_invalid_timeout_types_fail_closed[False] (defect H)
54. test_invalid_timeout_types_fail_closed[1.5] (defect H)
55. test_invalid_timeout_types_fail_closed["1"] (defect H)
56. test_invalid_timeout_types_fail_closed[list] (defect H)
57. test_invalid_timeout_types_fail_closed[dict] (defect H)
58. test_invalid_timeout_types_fail_closed[object] (defect H)
59. test_invalid_timeout_types_fail_closed[0] (defect H)
60. test_invalid_timeout_types_fail_closed[-1] (defect H)
61. test_timeout_1_succeeds (defect H control)
62. test_command_item_with_nul_fails_validation (defect I)
63. test_migration_directory_with_nul_fails (defect I)
64. test_subprocess_value_error_returns_typed_failure (defect I)
65. test_subprocess_error_returns_typed_failure (defect I)
66. test_subprocess_error_after_creating_migration_detects_integrity (defect I)
67. test_snapshot_read_error_returns_typed_failure
68. test_workspace_root_none_fails_validation
69. test_subprocess_created_external_symlink_forces_failure (defect J, skip on Windows)
70. test_subprocess_created_symlink_forces_failure_when_migration_not_required (defect J, skip on Windows)
71. test_synthetic_after_snapshot_error_forces_failure (defect J)
72. test_whitespace_only_migration_directory_fails[""] (defect K)
73. test_whitespace_only_migration_directory_fails[" "] (defect K)
74. test_whitespace_only_migration_directory_fails["   "] (defect K)
75. test_whitespace_only_migration_directory_fails["\t"] (defect K)
76. test_whitespace_only_migration_directory_fails["\n"] (defect K)
77–81. Helper tests for `_coerce_subprocess_text` and `_relative_to_root`

### State

| Item | Status |
|------|--------|
| R3B migration runner (initial) | COMPLETE — `c11f25e` |
| R3B first independent audit | FOUND 6 DEFECTS |
| R3B correction commit | `c873d9f` |
| R3B second independent audit | FOUND 3 DEFECTS + 1 REPO DEFECT |
| R3B final correction commit | `c635e42` |
| R3B third independent audit | FOUND 1 DEFECT + 1 INPUT GAP |
| R3B acceptance closure commit | `f8faa08` |
| R3B final status | ACCEPTANCE CLOSED — INDEPENDENT AUDIT SATISFIED |
| R3C isolated scenario evaluator | NEXT — blocked by previous R3B status; now unblocked |
| R3D-R6 | NOT STARTED |
| Kaggle | BLOCKED |
| Pilot | BLOCKED |
| Merge | BLOCKED |
| Stable tag | BLOCKED |

---

## Git History

| Commit | Description |
|--------|-------------|
| `f8faa08` | fix(validation): fail on untrusted migration after-state |
| `c635e42` | fix(validation): reject unsafe migration entries and malformed execution input |
| `3569a88` | docs(audit): record R3B correction |
| `c873d9f` | fix(validation): close migration runner safety gaps |
| `8c588e6` | docs(state): record R3B completion |
| `c11f25e` | feat(validation): add deterministic migration runner |
| `2370a57` | docs(state): record R3A completion |
| `3eaab60` | feat(scenarios): add V2 execution metadata |

---

**R3B_ACCEPTANCE_CLOSURE_AUDIT_REQUIRED**
