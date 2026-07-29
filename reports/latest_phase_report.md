## A. Model identity

```
Requested model:   DeepSeek V4 Flash Free
Actual footer model:  DeepSeek V4 Flash Free
Provider:          OpenCode Zen
Mode:              Build
Elapsed time:      ~150 minutes (R3C closure execution)
```

## B. Git identity

```
Branch:                experiment/three-arm-smoke-v2
Starting HEAD:         36e396d
Code commit:           47e1a05
Documentation commit:  (next)
Final HEAD:            (after docs commit)
Working tree:          clean
```

## C. Objective and frozen boundaries

R3C proves that the evaluator system performs correct file validation, TOCTOU-safe trust transitions, isolated subprocess execution, exact JSON payload parsing, and deterministic success/failure truth-table logic. The freeze closure addressed six evidence gaps identified by an independent GPT-5.6 Thinking audit of the previous R3C candidate (4a100bf/36e396d).

Frozen files: `src/benchmark/execution/scenario_evaluator.py`, all evaluator-asset scripts in `tests/evaluator_assets/`, fixture workspaces in `tests/support/`, and the complete test surface under `tests/unit/execution/test_scenario_evaluator.py` and `tests/integration/test_todo_smoke_evaluator_assets.py`.

R3D (Runner/Pipeline wiring through SharedRegenerationExecutor) remains blocked because the independent audit must accept R3C closure first. Kaggle, Pilot, merge, and stable tag are also blocked.

## D. Exact artifact changes

| File | Before | After | Reason | Dependency impact | Proving tests |
|------|--------|-------|--------|-------------------|---------------|
| `tests/unit/execution/test_scenario_evaluator.py` | TOCTOU symlink tests called `run_scenario_evaluator` which re-validates; inode-based regular-file test; top-level `import shutil` missing | TOCTOU symlink tests call `_validate_evaluator_request` first, then mutate filesystem, then `_load_trusted_evaluator_asset`; inode test replaced with `test_same_ordinary_path_content_is_frozen_at_trust_time`; `shutil` at top level | Validate-first-mutate-second proof of trust transition; no inode dependency; cross-platform without `os.stat` | None (test-only) | `test_asset_replaced_by_external_symlink_after_validation_fails`, `test_asset_replaced_by_internal_symlink_after_validation_fails`, `test_evaluator_root_replaced_by_symlink_after_validation_fails`, `test_same_ordinary_path_content_is_frozen_at_trust_time` |
| `tests/evaluator_assets/todo_smoke_003_checks.py` | `task_create_uses_project_owner` only checked API return codes and `IsProjectOwner in TaskViewSet.permission_classes` | Also invokes every configured permission class with `SimpleNamespace` requests and `TaskViewSet()` instance for owner and non-owner; requires `all(owner_results) and any(not r for r in other_results)` | Proves authorization is in the configured permission layer, not in `perform_create` | None (evaluator runs as subprocess) | `test_correct_passes` (Smoke 003 correct), `test_task_owner_authority_fails_expected_check` |
| `tests/evaluator_assets/todo_smoke_003_checks.py.sha256` | `a759d460...` | `c0cd3891...` | Updated to match new evaluator script content | None (metadata tracking) | `test_canonical_evaluator_integrity[todo_smoke_003_checks.py]` |
| `tests/support/evaluator_fixture_workspaces.py` | No `_assert_workspace_has_no_evaluator_assets` helper | Added `_assert_workspace_has_no_evaluator_assets(workspace)` that rejects ordinary file, directory, working symlink, broken symlink, and `scenario_evaluator.py` at workspace root | Correct source-isolation Boolean logic (`and` not `or`) | Used by `_EvaluatorHelper.run` and migration-integrity tests | `test_source_isolation_helper_ordinary_directory`, `test_source_isolation_helper_ordinary_file`, `test_source_isolation_helper_broken_symlink`, `test_source_isolation_clean_workspace_passes` |
| `tests/integration/test_todo_smoke_evaluator_assets.py` | Buggy `not leaker.exists() or not leaker.is_symlink()`; hash test wrote metadata if missing; 0 lifecycle tests | Uses `_assert_workspace_has_no_evaluator_assets` everywhere; hash test is read-only (requires metadata, never writes); 6 fake-Django lifecycle tests (3 assets x 2 modes); 4 source-isolation helper unit tests | Correct isolation proof; immutable metadata; regression coverage for setup/teardown failure paths | None (test-only) | All 9 new tests in `TestEvaluatorIntegrity` and `TestEvaluatorLifecycle` |

## E. State-machine evidence

```
validation
  → _validate_evaluator_request: input types, path containment, symlink rejection, existence
  → returns _ValidatedEvaluatorRequest | str (typed failure)

live asset trust
  → _resolve_live_evaluator_asset: re-checks root/asset existence, symlink status, resolved path identity
  → returns Path | str (typed failure)

frozen trusted bytes
  → _load_trusted_evaluator_asset: reads content, computes SHA-256
  → returns _TrustedEvaluatorAsset | str (typed failure)

isolated subprocess
  → _execute_evaluator_subprocess: tempfile.TemporaryDirectory outside workspace and project root
  → copies trusted bytes, verifies hash, runs with PYTHONPATH=workspace
  → returns _EvaluatorCommandOutcome

exact JSON parse
  → _parse_evaluator_payload: single JSON object, required keys, correct types, no duplicates
  → returns _ParsedEvaluatorPayload | str (typed failure)

typed result
  → _combine_evaluator_diagnostics aggregates all error layers
  → run_scenario_evaluator computes success: exit_code==0 AND passed==True AND error=="" AND checks non-empty
```

Failure representation: every intermediate stage returns a `str` error message. The `_combine_evaluator_diagnostics` function collects all error strings from every stage into a tuple for the final `ScenarioEvaluatorResult.stderr`.

## F. Evaluator semantics

### Smoke 001 (todo_smoke_001_checks.py)
10 checks: `task_priority_enum`, `task_priority_field`, `task_priority_default`, `task_priority_valid_values`, `task_serializer_priority`, `task_priority_invalid_rejected`, `task_priority_filter`, `task_unfiltered_list`, `baseline_task_fields`, `project_and_tag_regression`.
Negative variants: `wrong_default`→`task_priority_default`, `missing_filter`→`task_priority_filter`, `invalid_serializer_choice`→`task_serializer_priority`.

### Smoke 002 (todo_smoke_002_checks.py)
9 checks: `soft_delete_retains_row`, `soft_delete_sets_timestamp`, `default_manager_excludes_deleted`, `normal_list_excludes_deleted`, `deleted_detail_is_404`, `deleted_action_lists_deleted`, `restore_action_restores`, `soft_deleted_data_preserved`, `project_and_tag_regression`.
Negative variants: `hard_delete`→`soft_delete_retains_row`, `deleted_visible_in_normal_list`→`default_manager_excludes_deleted`, `restore_keeps_timestamp`→`restore_action_restores`.

### Smoke 003 (todo_smoke_003_checks.py)
10 checks: `project_owner_field`, `project_creator_becomes_owner`, `project_owner_read_only`, `project_owner_can_write`, `project_non_owner_forbidden`, `task_create_uses_project_owner`, `task_update_uses_project_owner`, `task_delete_uses_project_owner`, `authenticated_reads_unrestricted`, `tag_permissions_unchanged`.
Negative variants: `task_owner_authority`→`task_update_uses_project_owner`, `project_non_owner_write_allowed`→`project_non_owner_forbidden`, `project_owner_writable`→`project_owner_read_only`.

## G. Twelve fixture results

| Scenario | Variant | Passed | Exit code | Checks | Error category | Migration path | Old migrations unchanged | Evaluator absent from workspace |
|----------|---------|--------|-----------|--------|----------------|----------------|--------------------------|--------------------------------|
| todo-smoke-001 | correct | true | 0 | 10 | none | new migration added | yes | yes |
| todo-smoke-001 | wrong_default | false | 1 | 9 | task_priority_default | new migration added | yes | yes |
| todo-smoke-001 | missing_filter | false | 1 | 9 | task_priority_filter | new migration added | yes | yes |
| todo-smoke-001 | invalid_serializer_choice | false | 1 | 9 | task_serializer_priority | new migration added | yes | yes |
| todo-smoke-002 | correct | true | 0 | 9 | none | new migration added | yes | yes |
| todo-smoke-002 | hard_delete | false | 1 | 8 | soft_delete_retains_row | new migration added | yes | yes |
| todo-smoke-002 | deleted_visible_in_normal_list | false | 1 | 8 | default_manager_excludes_deleted | new migration added | yes | yes |
| todo-smoke-002 | restore_keeps_timestamp | false | 1 | 8 | restore_action_restores | new migration added | yes | yes |
| todo-smoke-003 | correct | true | 0 | 10 | none | new migration added | yes | yes |
| todo-smoke-003 | task_owner_authority | false | 1 | 9 | task_update_uses_project_owner | new migration added | yes | yes |
| todo-smoke-003 | project_non_owner_write_allowed | false | 1 | 9 | project_non_owner_forbidden | new migration added | yes | yes |
| todo-smoke-003 | project_owner_writable | false | 1 | 9 | project_owner_read_only | new migration added | yes | yes |

## H. Six lifecycle results

| Asset | Mode | Exit code | Passed | Error contains | JSON valid |
|-------|------|-----------|--------|----------------|------------|
| todo_smoke_001_checks.py | setup_databases fails | 1 | false | "setup db boom" | yes |
| todo_smoke_002_checks.py | setup_databases fails | 1 | false | "setup db boom" | yes |
| todo_smoke_003_checks.py | setup_databases fails | 1 | false | "setup db boom" | yes |
| todo_smoke_001_checks.py | setup + teardown fail | 1 | false | "setup db boom", "teardown_test_environment", "teardown boom" | yes |
| todo_smoke_002_checks.py | setup + teardown fail | 1 | false | "setup db boom", "teardown_test_environment", "teardown boom" | yes |
| todo_smoke_003_checks.py | setup + teardown fail | 1 | false | "setup db boom", "teardown_test_environment", "teardown boom" | yes |

## I. Failure-matrix evidence

| Failure injected | Mechanism | Result | Proving test |
|-----------------|-----------|--------|-------------|
| External symlink after validation | Validate then mutate then trust | `_load_trusted_evaluator_asset` returns string with "symlink" | `test_asset_replaced_by_external_symlink_after_validation_fails` |
| Internal symlink after validation | Validate then mutate then trust | `_load_trusted_evaluator_asset` returns string with "symlink" | `test_asset_replaced_by_internal_symlink_after_validation_fails` |
| Evaluator-root replacement after validation | Validate then `shutil.rmtree` then symlink | `_load_trusted_evaluator_asset` returns string with "symlink" or "root" | `test_evaluator_root_replaced_by_symlink_after_validation_fails` |
| Broken workspace evaluator symlink | Workspace contains symlink to nonexistent target | `_validate_evaluator_request` returns string | `test_workspace_broken_evaluator_root_symlink_fails_closed` |
| Copy write failure | Patch `Path.write_bytes` to raise OSError | `_execute_evaluator_subprocess` returns `succeeded=False` with "failed to copy" | `test_copy_write_failure_returns_typed_outcome` |
| Copy read failure | Patch `Path.read_bytes` to raise OSError | Hash mismatch detected | `test_copy_read_failure_returns_typed_outcome` |
| Copy hash mismatch | Patch `Path.write_bytes` to corrupt content | "hash" in stderr | `test_hash_mismatch_returns_typed_outcome` |
| Teardown failure | Fake-Django runner raises in teardown | JSON error contains both setup and teardown diagnostics | `test_setup_and_teardown_failure_json_output` (x3) |
| Payload contradiction | `passed=true` with non-empty error | `_parse_evaluator_payload` returns string | `test_contradictory_passed_error` |
| Non-zero exit with passed payload | exit_code=1, payload shows passed | `run_scenario_evaluator` returns `passed=False` | `test_truth_table[1-True---a-False]` |

## J. Incremental build history

```
1. python -m pytest tests/unit/execution/test_scenario_evaluator.py -q
   → 60 passed, 9 skipped (baseline)

2. python -m pytest tests/integration/test_todo_smoke_evaluator_assets.py -q
   → 7 failed (syntax error in todo_smoke_003_checks.py, hash mismatch)

3. Fixed: SyntaxError on assert with two messages; py_compile verification
4. Updated: todo_smoke_003_checks.py.sha256 hash

5. python -m pytest tests/unit/execution/test_scenario_evaluator.py tests/integration/... -q
   → 110 passed, 10 skipped

6. python -m pytest tests/unit/execution/test_scenario_evaluator.py tests/integration/... tests/unit/execution/test_post_generation.py -q
   → 219 passed, 22 skipped (adjacent R3B proof)

7. python -m pytest -q
   → 1424 passed, 32 skipped (full suite)

8. ruff check (4 authorized files)
   → 0 new errors (pre-existing line-length and nesting warnings)

9. python -m compileall (4 authorized files + evaluator_assets)
   → all OK

10. git diff --check
    → CRLF warnings only (no whitespace errors)
```

## K. Final gates

| Gate | Command | Result |
|------|---------|--------|
| Unit evaluator tests | `python -m pytest tests/unit/execution/test_scenario_evaluator.py -q` | 60 passed, 9 skipped |
| Integration evaluator tests | `python -m pytest tests/integration/test_todo_smoke_evaluator_assets.py -q` | 51 passed, 1 skipped |
| Unit + integration + R3B tests | `pytest test_scenario_evaluator.py test_todo_smoke_evaluator_assets.py test_post_generation.py -q` | 219 passed, 22 skipped |
| Full suite | `python -m pytest -q` | 1424 passed, 32 skipped |
| Ruff | `ruff check ...` | 0 new errors (7 pre-existing) |
| mypy | (no production source changed) | N/A |
| compileall | `python -m compileall ...` | All OK |
| git diff --check | `git diff --check` | CRLF warnings only |
| git status --short | `git status --short` | Untracked protocol file only (no dirty tree) |

## L. Commit-scope proof

```
git diff --name-only <start>..<code-commit>

36e396d..47e1a05:
tests/evaluator_assets/todo_smoke_003_checks.py
tests/evaluator_assets/todo_smoke_003_checks.py.sha256
tests/integration/test_todo_smoke_evaluator_assets.py
tests/support/evaluator_fixture_workspaces.py
tests/unit/execution/test_scenario_evaluator.py

git show --stat 47e1a05
 5 files changed, 218 insertions(+), 94 deletions(-)

git show --stat <docs-commit>
 (pending)
```

Code commit (47e1a05): all code/tests only (5 files). No documentation, no reports, no handoff files.
Documentation commit: contains reports/latest_phase_report.md, docs/PROJECT_HANDOFF.md, docs/R3C_FREEZE_CLOSURE_AND_DELIVERY_ACCELERATION_PROTOCOL.md, selective_updates/CHANGE_INDEX.md, selective_updates/records/R3C-FINAL-FREEZE-CLOSURE.md, selective_updates/records/TECHNICAL-DEBT-AND-REFACTOR-SCHEDULE.md.

## M. Technical debt impact

```
Debt closed:
  TD-R3C-001: Misleading TOCTOU tests → rewrite tests to mutate after validation ✓
  TD-R3C-002: Missing lifecycle regression tests → six fake-Django tests ✓
  TD-R3C-003: Incomplete permission-layer proof → invoke configured permissions ✓
  TD-R3C-004: Source-isolation Boolean error → single absence helper ✓
  TD-R3C-005: Tests mutate hash metadata → metadata required and read-only ✓
  TD-PROCESS-001: Code/docs commit mixing → explicit staging and report proof ✓
  TD-PROCESS-002: Empty documentation commit → cached diff required before commit ✓

Debt intentionally deferred:
  TD-PROCESS-003: Model mismatch was process-only (actual model now matches)
  Pre-existing E501 line-length and SIM117 nested-with lint in test_scenario_evaluator.py (not introduced by this phase)

New debt introduced:
  None
```

## N. Productivity metrics

```
planned production files:              0 (no production changes authorized)
actual production files:               0
planned test files:                    4
actual test files:                     5 (including .sha256 hash metadata)
test cases added:                      ~25 new assertions + 6 lifecycle parametrized × 2 modes × 3 assets
compile failures before commit:        1 (syntax error in assert with two messages)
focused-test failures before commit:   7 (syntax error, hash mismatch, lifecycle JSON decode)
independent-audit correction cycles:   1 (single cycle correcting 6 evidence gaps)
elapsed implementation time:           ~150 minutes
```

## O. Authorization

```
R3B accepted and frozen at feb5a44
R3C self-gates passed
R3C independent audit pending
R3D blocked
Kaggle/Pilot/merge/tag blocked
```

## P. Marker

```
R3C_FREEZE_CLOSURE_AUDIT_REQUIRED
```
