# R5-BASELINE-CONTRACT-001 — Pre-Results Smoke V2 Baseline Contract Amendment

**Amendment ID:** R5-BASELINE-CONTRACT-001
**Date:** 2026-07-31
**Trigger:** Independent blocker audit (2026-07-31) confirmed a data contract
contradiction between the frozen baseline regression assertions and the three
frozen Smoke V2 scenarios. The authoritative replacement for the pre-existing
frozen-data prohibition is limited to the amendment specified in
`..\R5_BLOCKER_INDEPENDENT_AUDIT_2026-07-31.md` and
`..\OPENCODE_R5_CONTRACT_CORRECTION_AND_RESUME_DIRECTIVE.md`.

## No scientific result existed

This amendment was applied before any Smoke V2 record was produced. The R5
phase was blocked at Step 2 (the first Monolithic cell) by baseline-validation
failures. No scenario evaluator result, no persisted record, and no metric was
generated from the old rules. Therefore this is a pre-results correction, not a
post-hoc adjustment to observed outcomes.

## Old contradictory rules

- `test_task_serializer_fields` required the exact serializer field set
  `{id, title, description, status, project, tags, created_at, updated_at}` —
  but `todo-smoke-001` correctly adds a `priority` field, so the exact set is
  unsatisfiable for the corrected source.
- `test_project_serializer_fields` required the exact field set
  `{id, name, description}` — but `todo-smoke-003` correctly adds an `owner`
  field, so the exact set is unsatisfiable for the corrected source.
- `TaskViewSetTest.setUp` created the common project with
  `Project.objects.create(...)`, bypassing the public Project API, so
  `todo-smoke-003` could not assign `Project.owner` through the real path.
- `test_update_unowned_task_forbidden` created the unowned task inside the
  common project, making the 403 expectation unreachable under correct
  `todo-smoke-003` authorization semantics.
- The `todo-smoke-002` correct-source fixture required `todo/serializers.py`,
  which forced an over-specified serializer (one exposing `deleted_at`) that
  contradicted the baseline Project/Tag serializer contract.
- The smoke-002 evaluator asserted every `/api/tasks/deleted/` row exposes a
  non-null `deleted_at` response field, an unstated requirement not present in
  the frozen scenario YAML or the baseline serializer.

## New rules

- `test_task_serializer_fields` and `test_project_serializer_fields` assert
  baseline-field *preservation* (the required baseline fields must be present),
  not an exact set. `TagSerializer` remains exact and unchanged.
- `TaskViewSetTest.setUp` creates the common project through the authenticated
  `POST /api/projects/` API and loads it from the returned ID.
- `test_update_unowned_task_forbidden` creates a separate authenticated API
  client for another user, creates an independent project through that user's
  API, creates the task in that other project, and still asserts exactly
  HTTP 403 from the original client.
- The `todo-smoke-002` correct-source fixture keys are exactly
  `todo/models.py` and `todo/views.py`; `todo/serializers.py` is removed, so
  Monolithic and Selective returns the baseline serializer content.
- The smoke-002 evaluator preserves all database timestamp, exclusion,
  restore, data-preservation, Project, and Tag checks; it removes only the
  unstated `deleted_at`-response-field loop inside `_deleted_action_lists_deleted`.
  The canonical SHA-256 is recomputed from the raw LF bytes.

## Why this is not post-hoc tuning

- The amendment changes only baseline regression assertions and the evaluator
  over-constraint; it does not weaken any scenario requirement, evaluator
  check name, or negative variant.
- Every preserved check still fails its negative variant (proven by the
  evaluator suite). `_soft_delete_sets_timestamp` remains the authoritative
  timestamp requirement.
- The exact changed-source-path contract is unchanged and independently
  asserted by the new compatibility gate (001 = models, serializers, views;
  002 = models, views; 003 = models, serializers, permissions, views).

## Exact code/data commit

`8fafb50` — `fix(validation): reconcile Smoke V2 baseline contracts`

Seven files:

```text
benchmark_data/repositories/todo/todo/tests/test_serializers.py
benchmark_data/repositories/todo/todo/tests/test_views.py
benchmark_data/manifests/repository_versions.yaml
tests/support/evaluator_fixture_workspaces.py
tests/evaluator_assets/todo_smoke_002_checks.py
tests/evaluator_assets/todo_smoke_002_checks.py.sha256
tests/integration/test_todo_smoke_evaluator_assets.py
```

Production source files changed: NONE. Scenario YAML files changed: NONE.

## Compatibility test evidence

- Baseline repository suite before scenario changes: 47 passed, 0 failed.
- Correct-fixture compatibility gate (three scenarios): 3 passed — baseline
  suite green in each workspace, evaluator green, exactly one new migration,
  old migrations byte-identical, exact changed-source paths match the frozen
  expected sets, baseline test files byte-identical, no evaluator assets in the
  workspace.
- Complete evaluator suite: 53 passed, 1 pre-existing skip.
- Full test suite: 1598 passed, 32 skipped, 0 failed.

## Status

```text
R5 status: RESUMED (Step 2 Monolithic cell green)
R6 status: BLOCKED
Kaggle status: BLOCKED
Push status: BLOCKED
Tag status: BLOCKED
```
