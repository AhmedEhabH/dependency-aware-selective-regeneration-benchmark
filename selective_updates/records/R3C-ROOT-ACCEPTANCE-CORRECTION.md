# R3C — Acceptance Correction Record

**Date:** 2026-07-29
**Status:** R3C CORRECTION SELF-GATES PASSED — INDEPENDENT AUDIT PENDING
**Branch:** `experiment/three-arm-smoke-v2`
**Model:** DeepSeek V4 Flash Free through OpenCode Zen, Build mode
**Code commit:** `81429c1`
**Starting HEAD:** `64a3032`

---

## 1. Binding audit context

R3C was **not accepted** at checkpoint `0d168d0`. The independent audit (GPT-5.6 Thinking) identified seven root defects:

| Defect | Description |
|--------|-------------|
| A | Evaluator asset trust — lexical symlink checked after resolve; workspace evaluator leakage allowed |
| B | Runner unit tests did not prove their names — command/env/cwd never inspected; truth table constructed `ScenarioEvaluatorResult` manually |
| C | Standalone evaluator scripts could emit non-JSON output on unexpected exceptions |
| D | Smoke 001 semantic checks too weak |
| E | Smoke 002 required `all_objects` manager name; used wrong unfiltered access |
| F | Smoke 003 project-owner permission contract incomplete |
| G | Fixture builder bypassed R3B `run_post_generation_command`; deleted baseline migrations; duplicated 1778-line sources |
| H | Integration tests asserted only `not result.passed` — never proved the named check failed |

## 2. Changes applied

### 2.1 Production runner (`scenario_evaluator.py`)

- Fixed symlink check order: lexical parent components are checked before `resolve()`
- Added workspace evaluator leak rejection: `<workspace>/tests/evaluator_assets` existence is forbidden
- Replaced string-prefix containment checks with `Path.relative_to` via `_containment_check` helper
- All four private state names preserved: `_ValidatedEvaluatorRequest`, `_TrustedEvaluatorAsset`, `_EvaluatorCommandOutcome`, `_ParsedEvaluatorPayload`
- All five private helper names preserved: `_validate_evaluator_request`, `_load_trusted_evaluator_asset`, `_execute_evaluator_subprocess`, `_parse_evaluator_payload`, `_combine_evaluator_diagnostics`
- Public API preserved: `ScenarioEvaluatorResult`, `run_scenario_evaluator`

### 2.2 Unit tests — 57 passed, 5 skipped

- Added symlink rejection tests: `test_asset_internal_symlink_fails_closed`, `test_asset_parent_symlink_component_fails_closed`
- Added workspace leak tests: `test_workspace_evaluator_root_directory_fails_closed`, `test_workspace_evaluator_root_file_fails_closed`, `test_workspace_evaluator_root_symlink_fails_closed`
- Added `test_sibling_prefix_is_not_treated_as_containment`
- Replaced `test_exact_command_and_cwd` and `test_workspace_in_pythonpath` with monkeypatched subprocess tests proving exact command, env, cwd, timeout
- Added subprocess exception tests: `test_timeout_with_string_output`, `test_timeout_with_byte_output`, `test_subprocess_value_error`, `test_subprocess_os_error`, `test_subprocess_error`
- Added copy/trust tests: `test_source_change_after_trust_does_not_change_copied_bytes`, `test_copy_write_failure_returns_typed_outcome`
- Replaced fake truth-table with `run_scenario_evaluator` public-path truth table (7 rows)
- Added isolation tests: `test_temp_directory_removed_after_success`, `test_temp_directory_removed_after_failure`, `test_only_selected_asset_is_present_in_temp`, `test_evaluator_never_written_to_workspace`

### 2.3 Evaluator assets — common fail-closed JSON structure

All three scripts (`todo_smoke_001_checks.py`, `todo_smoke_002_checks.py`, `todo_smoke_003_checks.py`) use identical common flow:

- `_workspace_from_argv()` — validates workspace contains `manage.py`, `config/settings.py`, `todo/`
- `_record_check()` — wraps every check; catches `Exception` (not only `AssertionError`)
- `os.environ["DJANGO_SETTINGS_MODULE"]` — direct assignment, not `setdefault`
- `try/except/finally` — always prints exactly one JSON object with `sort_keys=True`
- `finally` block — tears down databases and test environment

### 2.4 Smoke 001 semantic checks (10 checks)

`task_priority_enum`, `task_priority_field`, `task_priority_default`, `task_priority_valid_values`, `task_serializer_priority`, `task_priority_invalid_rejected`, `task_priority_filter`, `task_unfiltered_list`, `baseline_task_fields`, `project_and_tag_regression`

### 2.5 Smoke 002 semantic checks (9 checks, uses `_base_manager`)

`soft_delete_retains_row`, `soft_delete_sets_timestamp`, `default_manager_excludes_deleted`, `normal_list_excludes_deleted`, `deleted_detail_is_404`, `deleted_action_lists_deleted`, `restore_action_restores`, `soft_deleted_data_preserved`, `project_and_tag_regression`

### 2.6 Smoke 003 semantic checks (10 checks)

`project_owner_field`, `project_creator_becomes_owner`, `project_owner_read_only`, `project_owner_can_write`, `project_non_owner_forbidden`, `task_create_uses_project_owner`, `task_update_uses_project_owner`, `task_delete_uses_project_owner`, `authenticated_reads_unrestricted`, `tag_permissions_unchanged`

### 2.7 Fixture workspace builder — 626 lines (was 1778)

- Calls `run_post_generation_command` from `benchmark.execution.post_generation`
- `_run_required_migration` replaces forbidden `_run_makemigrations` — never deletes migrations
- Three correct-source dicts: `_SMOKE_001_CORRECT_SOURCES`, `_SMOKE_002_CORRECT_SOURCES`, `_SMOKE_003_CORRECT_SOURCES`
- `_apply_single_replacement` derives 9 negative variants with exactly one conceptual mutation
- Each negative variant asserts the old fragment occurs exactly once

### 2.8 Integration tests — 20 passed

- Correct variants assert exact check tuples
- Negative variants assert the expected failed check name appears in `result.error`
- Baseline hash preservation verified (before/after fixture+eval run)
- Workspace migration integrity: 3 baseline hashes match, exactly 4 migrations
- Source isolation: no `tests/evaluator_assets` in workspace, canonical hash unchanged
- JSON output asserted as single object

## 3. Quality gates

| Gate | Result |
|------|--------|
| Full pytest | 1391 passed, 27 skipped, 0 failed |
| Ruff (7 authorized files) | 0 errors |
| Mypy strict (`scenario_evaluator.py`) | 0 errors |
| Compileall (runner + 3 assets) | All pass |
| `git diff --check` | Clean |
| Working tree | Clean |

## 4. Files changed (code commit `81429c1`)

| File | Status |
|------|--------|
| `src/benchmark/execution/scenario_evaluator.py` | MODIFIED (trust fixes, workspace leak check, Path.relative_to containment) |
| `tests/unit/execution/test_scenario_evaluator.py` | MODIFIED (57 tests, public-path truth table) |
| `tests/evaluator_assets/todo_smoke_001_checks.py` | MODIFIED (common fail-closed JSON flow, 10 checks) |
| `tests/evaluator_assets/todo_smoke_002_checks.py` | MODIFIED (common fail-closed JSON flow, 9 checks) |
| `tests/evaluator_assets/todo_smoke_003_checks.py` | MODIFIED (common fail-closed JSON flow, 10 checks) |
| `tests/support/evaluator_fixture_workspaces.py` | MODIFIED (one-fault variants, run_post_generation_command) |
| `tests/integration/test_todo_smoke_evaluator_assets.py` | MODIFIED (exact checks, named failures, baseline integrity) |

## 5. Project status

```
R1 Repository Agent                  accepted
R2 Selective                         accepted
R3A Scenario metadata               accepted
R3B Migration runner                accepted and frozen at feb5a44
R3C Evaluator runner foundation     correction self-gates passed
R3C semantic/integration contract   independent audit pending
R3D Runner wiring                   blocked
R4 Token and metrics                pending
R5 Nine local records               pending
R6 Bundle and push                  pending
Kaggle                              blocked
Stable tag                          blocked
Pilot                               blocked
```

## 6. Twelve fixture outcomes

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

## 7. Correction verification

- [x] fixture builder now calls `run_post_generation_command`
- [x] old migration hashes preserved (3 baseline hashes match per workspace)
- [x] one new migration per fixture (4 migrations total per workspace)
- [x] negative variants are one-fault mutations (9 variants, each changes exactly one thing)
- [x] each negative fails the expected named check
- [x] runner rejects lexical asset symlinks
- [x] runner rejects evaluator assets inside workspace
- [x] truth table calls public `run_scenario_evaluator`
- [x] all three evaluator scripts always print one JSON object

```
R3B accepted and frozen at feb5a44
R3C correction self-gates passed
R3C independent audit pending
R3D blocked
Kaggle/Pilot/merge/tag blocked
```

R3C_ACCEPTANCE_CORRECTION_AUDIT_REQUIRED