# R3C Root Acceptance Correction Specification

**Document status:** Binding correction contract  
**Target branch:** `experiment/three-arm-smoke-v2`  
**Audited documentation HEAD:** `64a3032`  
**Audited R3C code checkpoint:** `0d168d0`  
**Accepted and frozen R3B checkpoint:** `feb5a44`  
**Independent audit model:** GPT-5.6 Thinking  
**Required OpenCode model:** DeepSeek V4 Flash Free through OpenCode Zen, Build mode  
**Real scientific model later:** Qwen2.5-Coder-7B-Instruct on Kaggle  
**Current permission:** correct R3C only  
**R3D, Kaggle, Pilot, merge, and stable tag:** blocked  

---

# 1. Binding audit verdict

R3C is **not accepted** at checkpoint `0d168d0`.

The current branch contains useful foundations:

- the correct public API names;
- the four approved private state names;
- evaluator copying to a temporary directory;
- a separate subprocess;
- exact JSON-object parsing;
- typed `ScenarioEvaluatorResult`;
- three standalone evaluator asset files;
- twelve named fixture variants;
- a clean Git tree;
- a green Windows full suite reported by the researcher;
- forty-seven evaluator-runner unit tests that also pass in the independent Linux environment.

However, the phase does not yet prove the scientific behavior it claims.

The root causes are broader than one edge-case patch:

1. the evaluator-runner trust boundary is incomplete;
2. the standalone evaluator scripts are not guaranteed to emit exactly one JSON object on every failure path;
3. the scenario checks are too weak and in one case impose a forbidden implementation-specific manager name;
4. the fixture integration bypasses the accepted R3B production runner and deletes all baseline migrations;
5. several unit tests have names that claim behavior they do not assert;
6. negative fixtures often contain more than one defect, so a failing evaluator does not prove it detected the named defect;
7. the documentation record describes an implementation that does not exist in the committed source.

This correction must fix the complete R3C contract in one bounded pass. It must not start R3D.

---

# 2. Independent evidence

## 2.1 Git and file scope

The audited history is:

```text
64a3032 docs(state): record R3C implementation pending audit
0d168d0 feat(validation): add isolated scenario evaluator system
341cc99 docs(audit): record R3B cross-platform freeze candidate
feb5a44 fix(validation): close cross-platform migration snapshot contract
```

The working tree in the supplied archive is clean.

The code commit changed exactly the eight intended R3C code/test artifacts.

## 2.2 Independent unit-test execution

The independent Linux environment ran:

```text
PYTHONPATH=src python -m pytest tests/unit/execution/test_scenario_evaluator.py -q
```

Result:

```text
47 passed
```

This proves the tests are executable. It does not prove their claims are strong enough.

## 2.3 Independent integration attempt

The independent environment attempted:

```text
PYTHONPATH=src python -m pytest tests/integration/test_todo_smoke_evaluator_assets.py -q
```

The environment does not contain Django, so subprocess fixture construction failed with:

```text
ModuleNotFoundError: No module named 'django'
```

This is an audit-environment limitation, not by itself a project-code defect. The Windows suite supplied by the researcher reports the integration tests passing.

The blocking findings below come from direct production-source inspection, direct runner adversarial executions that do not require Django, and comparison with the frozen scenario contracts.

## 2.4 Direct runner adversarial evidence

The current validator accepts a selected evaluator file that is a symlink to another ordinary file inside `tests/evaluator_assets`.

Reason:

```python
evaluator_asset_path = (...).resolve()
if evaluator_asset_path.is_symlink():
```

The lexical symlink has already been followed before `is_symlink()` is called.

The current validator also accepts a generated workspace that contains:

```text
tests/evaluator_assets/checks.py
```

The master contract requires evaluator assets to remain absent from the model-visible workspace.

Both cases were reproduced against the committed function.

---

# 3. Accepted architecture that must be preserved

Do not replace the complete public evaluator runner.

Preserve:

```python
@dataclass(frozen=True)
class ScenarioEvaluatorResult:
    passed: bool
    exit_code: int
    checks: tuple[str, ...]
    error: str
    stdout: str
    stderr: str
    duration_seconds: float
```

Preserve:

```python
def run_scenario_evaluator(
    canonical_project_root: str | Path,
    evaluator_asset: str,
    generated_workspace: str | Path,
    *,
    python_executable: str,
    timeout: int = 180,
) -> ScenarioEvaluatorResult:
    ...
```

Preserve the private state names:

```text
_ValidatedEvaluatorRequest
_TrustedEvaluatorAsset
_EvaluatorCommandOutcome
_ParsedEvaluatorPayload
```

Preserve the private helper names:

```text
_validate_evaluator_request
_load_trusted_evaluator_asset
_execute_evaluator_subprocess
_parse_evaluator_payload
_combine_evaluator_diagnostics
```

Do not add a generic subprocess framework.

Do not add a shared fourth evaluator asset.

Do not modify R3B production or tests.

---

# 4. Authorized artifacts and dependency map

## 4.1 Production runner

```text
src/benchmark/execution/scenario_evaluator.py
```

Direct dependencies:

```text
pathlib
tempfile
hashlib
json
subprocess
os
time
```

Public dependents:

```text
src/benchmark/execution/__init__.py
future R3D BenchmarkRunner wiring
integration evaluator tests
```

## 4.2 Public export

```text
src/benchmark/execution/__init__.py
```

No change is expected unless the current export is accidentally altered.

## 4.3 Unit tests

```text
tests/unit/execution/test_scenario_evaluator.py
```

Must prove the production public composition, not only private helpers.

## 4.4 Evaluator assets

```text
tests/evaluator_assets/todo_smoke_001_checks.py
tests/evaluator_assets/todo_smoke_002_checks.py
tests/evaluator_assets/todo_smoke_003_checks.py
```

They are benchmark-owned hidden evaluator logic.

They must never enter a generated workspace.

## 4.5 Fixture builders

```text
tests/support/evaluator_fixture_workspaces.py
```

Must integrate with accepted R3B:

```text
run_post_generation_command
```

The current direct `subprocess.run` migration helper is forbidden.

## 4.6 Integration tests

```text
tests/integration/test_todo_smoke_evaluator_assets.py
```

Must prove:

```text
baseline copy
→ one-fault source fixture
→ production R3B migration runner
→ old migrations unchanged
→ exactly one new migration
→ production R3C evaluator runner
→ standalone evaluator
→ Django test database
→ exact result
```

## 4.7 Documentation after code gates

```text
docs/PROJECT_HANDOFF.md
reports/latest_phase_report.md
docs/R3B_FREEZE_AND_R3C_SINGLE_PASS_MASTER_SPEC.md
docs/V2_R3B_TO_KAGGLE_NO_DISCRETION_EXECUTION_SPEC.md
selective_updates/CHANGE_INDEX.md
selective_updates/records/R3C-SINGLE-PASS-IMPLEMENTATION-RECORD.md
selective_updates/records/R3C-ROOT-ACCEPTANCE-CORRECTION.md
```

---

# 5. Root defect A — evaluator asset trust

## 5.1 Lexical asset symlink

The current code resolves the selected file before checking whether the selected path itself is a symlink.

Correct order:

```python
asset_lexical = evaluator_root / relative_suffix

if asset_lexical.is_symlink():
    return "evaluator_asset must not be a symlink"

for component in lexical parents below evaluator_root:
    if component.is_symlink():
        return "evaluator_asset path must not contain symlink components"

asset_resolved = asset_lexical.resolve(strict=True)
asset_resolved.relative_to(evaluator_root)
```

Use narrow typed exception conversion.

The three approved assets are direct children, but the helper should remain correct for nested assets.

## 5.2 Workspace evaluator leakage

Reject when the generated workspace contains:

```text
<workspace>/tests/evaluator_assets
```

as a file, directory, or symlink.

This is deliberately stricter than checking only the selected filename. It prevents any evaluator asset from becoming model-visible.

Return typed validation failure before temporary-directory creation.

## 5.3 Path ancestry

Replace string-prefix checks with a private `Path.relative_to` containment helper.

Use it for:

- evaluator asset beneath evaluator root;
- temporary directory outside generated workspace;
- temporary directory outside canonical project root.

Do not use `str(path).startswith(...)`.

## 5.4 Required tests

Add persistent tests:

```text
test_asset_internal_symlink_fails_closed
test_asset_parent_symlink_component_fails_closed
test_workspace_evaluator_root_directory_fails_closed
test_workspace_evaluator_root_file_fails_closed
test_workspace_evaluator_root_symlink_fails_closed
test_sibling_prefix_is_not_treated_as_containment
```

Every test calls `_validate_evaluator_request`.

At least two tests call the public `run_scenario_evaluator` and prove:

```text
passed=False
exit_code=-1
error is non-empty
```

---

# 6. Root defect B — runner tests do not prove their names

The current tests named:

```text
test_exact_command_and_cwd
test_workspace_in_pythonpath
```

only run an evaluator and assert success.

They do not inspect the command, `cwd`, environment, or timeout.

Replace them with monkeypatched subprocess tests that capture the exact call.

Required assertions:

```python
command == [
    request.python_executable,
    str(copied_path),
    str(request.generated_workspace),
]

cwd == str(temporary_directory)
capture_output is True
text is True
timeout == request.timeout
"shell" not in kwargs
env["PYTHONDONTWRITEBYTECODE"] == "1"
env["PYTHONPATH"].split(os.pathsep)[0] == str(request.generated_workspace)
```

The fake subprocess returns an object equivalent to:

```python
subprocess.CompletedProcess(command, 0, json_payload, "")
```

## 6.1 Missing subprocess tests

Add:

```text
test_timeout_with_string_output
test_timeout_with_byte_output
test_subprocess_value_error
test_subprocess_os_error
test_subprocess_error
```

Every case must return `_EvaluatorCommandOutcome`, not raise.

## 6.2 Copy/trust tests

Add:

```text
test_source_change_after_trust_does_not_change_copied_bytes
test_copy_write_failure_returns_typed_outcome
test_copy_read_failure_returns_typed_outcome
test_copied_hash_mismatch_returns_typed_outcome
```

The source-change test proves the trusted bytes, not the later source path, are copied.

## 6.3 Real truth-table tests

The current truth-table test manually constructs:

```python
ScenarioEvaluatorResult(passed=expected_passed, ...)
```

It therefore proves only that a Boolean field preserves the value assigned to it.

Replace it.

Each truth-table row must call `run_scenario_evaluator`.

Use valid temporary roots and monkeypatch only `_execute_evaluator_subprocess`.

Let the real payload parser and public final expression run.

Required rows:

| Exit | Payload passed | Error | Checks | Expected |
|---:|---:|---|---|---:|
| 0 | true | empty | non-empty | pass |
| 1 | true | empty | non-empty | fail |
| 0 | false | non-empty | non-empty | fail |
| 1 | false | non-empty | non-empty | fail |
| 0 | true | empty | empty | fail |
| 0 | true | non-empty | non-empty | parse/final failure |
| 0 | false | empty | non-empty | parse/final failure |

For every failed public result:

```text
passed=False
error or stderr contains a useful diagnostic
duration_seconds >= 0
```

## 6.4 Isolation tests

The current `test_temp_outside_workspace` only asserts success.

Add tests that capture the temporary `cwd` from the fake subprocess and prove it is outside both roots.

Add:

```text
test_temp_directory_removed_after_success
test_temp_directory_removed_after_failure
test_only_selected_asset_is_present_in_temp
test_evaluator_never_written_to_workspace
```

---

# 7. Root defect C — standalone evaluator process contract

Every evaluator must always print exactly one JSON object, including unexpected failures.

The current scripts catch only `AssertionError` inside individual checks. `AttributeError`, `ImportError`, database setup failure, serializer exceptions, and permission exceptions can escape without JSON.

## 7.1 Exact common script flow

Use this structure independently in all three scripts:

```python
def _workspace_from_argv() -> Path:
    ...

def _response_items(response) -> list[dict]:
    ...

def _record_check(
    name: str,
    checks: list[str],
    errors: list[str],
    function: Callable[[], None],
) -> None:
    try:
        function()
    except Exception as exc:
        errors.append(f"{name}: {type(exc).__name__}: {exc}")
    else:
        checks.append(name)

def main() -> int:
    payload = {"passed": False, "checks": [], "error": ""}
    captured = io.StringIO()
    runner = None
    old_config = None
    environment_ready = False

    try:
        workspace = _workspace_from_argv()
        sys.path.insert(0, str(workspace))
        os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
        os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

        with redirect_stdout(captured), redirect_stderr(captured):
            import django
            django.setup()

            runner = DiscoverRunner(
                verbosity=0,
                interactive=False,
            )
            runner.setup_test_environment()
            environment_ready = True
            old_config = runner.setup_databases()

            checks, errors = _run_checks()

        payload = {
            "passed": not errors,
            "checks": checks,
            "error": "; ".join(errors),
        }
    except Exception as exc:
        captured_text = captured.getvalue()[-1000:]
        detail = f"{type(exc).__name__}: {exc}"
        if captured_text:
            detail += f" | captured: {captured_text}"
        payload = {
            "passed": False,
            "checks": payload.get("checks", []),
            "error": detail,
        }
    finally:
        if runner is not None:
            with redirect_stdout(captured), redirect_stderr(captured):
                if old_config is not None:
                    runner.teardown_databases(old_config)
                if environment_ready:
                    runner.teardown_test_environment()

    print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
    return 0 if payload["passed"] else 1
```

The exact implementation may use local functions, but the state and behavior must match.

## 7.2 Workspace validation inside the script

Require:

```text
manage.py exists
config/settings.py exists
todo/ exists and is a directory
```

Reject any other argument count.

## 7.3 Environment assignment

Use:

```python
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
```

Do not use `setdefault`.

The parent process may already have a different Django setting.

## 7.4 Stable error naming

Every failed semantic check prefixes the exact check name.

Integration tests use this to prove the named negative fixture failed for the intended reason.

---

# 8. Root defect D — Smoke 001 evaluator semantics

The current evaluator checks only a subset of the frozen contract.

## 8.1 `task_priority_enum`

Require:

- `Task.Priority` exists;
- it is a Django `TextChoices` subclass;
- stored values are exactly:
  `HIGH`, `MEDIUM`, `LOW`;
- no extra stored values.

## 8.2 `task_priority_field`

Use:

```python
field = Task._meta.get_field("priority")
```

Require:

- field exists;
- exact choice values are HIGH/MEDIUM/LOW;
- default resolves to MEDIUM.

## 8.3 `task_priority_default`

Create without priority, refresh, require MEDIUM.

## 8.4 `task_priority_valid_values`

For every valid value:

- serializer accepts it;
- save succeeds;
- serialized output returns it.

## 8.5 `task_serializer_priority`

Require:

- field exists;
- not read-only;
- DRF choice set exactly matches three values.

Do not accept an arbitrary IntegerField or CharField without choices.

## 8.6 `task_priority_invalid_rejected`

Require both:

- serializer rejects URGENT;
- API POST returns 400.

## 8.7 `task_priority_filter`

Create one HIGH, one MEDIUM, one LOW task.

GET:

```text
/api/tasks/?priority=HIGH
```

Normalize paginated or list response.

Require:

- HIGH task included;
- MEDIUM and LOW excluded;
- every returned row has priority HIGH.

A status-code-only assertion is forbidden.

## 8.8 `task_unfiltered_list`

GET without query.

Require all three task IDs appear.

## 8.9 `baseline_task_fields`

Create Task with:

```text
title
description
status
owner
project
tags
```

Require all values preserved and timestamps populated.

## 8.10 `project_and_tag_regression`

Create and serialize Project and Tag.

Exercise authenticated API create/read behavior.

No Project or Tag schema change may be required.

---

# 9. Root defect E — Smoke 002 evaluator semantics

## 9.1 Do not require `all_objects`

The current evaluator directly calls:

```python
Task.all_objects
```

This rejects valid implementations that use another unfiltered-manager name.

Use:

```python
Task._base_manager
```

for retained-row and direct-row access.

This is mandatory.

## 9.2 One scenario flow

Create:

- authenticated user;
- project;
- tag;
- active control task;
- target task with non-default description and status;
- attach tag.

DELETE target.

Require successful destroy response.

Then perform all nine checks from the same coherent state where appropriate.

## 9.3 `soft_delete_retains_row`

Use `_base_manager`.

## 9.4 `soft_delete_sets_timestamp`

Refresh through `_base_manager`.

## 9.5 `default_manager_excludes_deleted`

Require target absent from `Task.objects`.

## 9.6 `normal_list_excludes_deleted`

Require target absent and active control present.

## 9.7 `deleted_detail_is_404`

Require 404.

## 9.8 `deleted_action_lists_deleted`

Require:

- deleted target included;
- active control excluded.

## 9.9 `restore_action_restores`

POST restore.

Require:

- response 200;
- `deleted_at` null;
- normal list includes target;
- detail returns 200.

## 9.10 `soft_deleted_data_preserved`

After restoration verify:

```text
title
description
status
project
tags
```

## 9.11 `project_and_tag_regression`

Prove normal Project and Tag behavior remains functional.

---

# 10. Root defect F — Smoke 003 evaluator semantics

## 10.1 `project_owner_field`

Require:

- model field exists;
- it is a ForeignKey;
- remote model is the configured user model.

Do not require non-null.

## 10.2 `project_creator_becomes_owner`

Create through API and require authenticated creator.

Also POST another user’s owner ID and prove it cannot override creator assignment.

## 10.3 `project_owner_read_only`

Inspect `ProjectSerializer().fields["owner"].read_only`.

Do not infer read-only from a GET response.

## 10.4 `project_owner_can_write`

Owner may PATCH own project.

Owner may DELETE a separate own project.

## 10.5 `project_non_owner_forbidden`

Non-owner PATCH and DELETE both return 403.

Any authenticated user may still create a new project.

## 10.6 `task_create_uses_project_owner`

Project owner can create Task.

Other authenticated user receives 403.

## 10.7 `task_update_uses_project_owner`

Create a task whose legacy:

```text
Task.owner = other user
Task.project.owner = owner user
```

Require:

- project owner PATCH succeeds;
- legacy Task.owner user PATCH returns 403.

This is the decisive authority test.

## 10.8 `task_delete_uses_project_owner`

Use a separate task with the same authority conflict.

Require project owner DELETE succeeds and legacy Task.owner user receives 403 on another equivalent task.

## 10.9 `authenticated_reads_unrestricted`

Other user may:

- list projects;
- retrieve project;
- list tasks;
- retrieve task;
- list tags;
- retrieve tag.

## 10.10 `tag_permissions_unchanged`

Baseline behavior is:

- authenticated non-staff may create Tag;
- non-staff object update/delete is forbidden;
- staff object update is allowed.

Test all three.

Do not merely test Tag creation.

---

# 11. Root defect G — fixture architecture bypasses R3B

The current helper:

```python
_run_makemigrations
```

deletes every existing numbered migration and directly calls `subprocess.run`.

This violates:

- existing migrations remain byte-identical;
- exactly one **new** migration;
- required R3B-to-R3C integration.

## 11.1 Replace migration helper

Import:

```python
from benchmark.execution.post_generation import run_post_generation_command
```

Create:

```python
def _run_required_migration(workspace: Path) -> None:
    result = run_post_generation_command(
        workspace,
        (
            sys.executable,
            "manage.py",
            "makemigrations",
            "todo",
            "--noinput",
        ),
        require_new_migration=True,
        timeout=180,
    )
    if not result.passed:
        raise RuntimeError(
            f"post-generation migration failed: "
            f"exit={result.exit_code}; "
            f"stderr={result.stderr}; "
            f"created={result.created_paths}"
        )
```

Never delete an existing migration.

Do not call `migrate` in the builder.

## 11.2 Reduce duplicated fixtures

The current fixture file is 1,778 lines and duplicates complete source files for every variant.

Refactor within the same authorized file.

Use:

```python
_SMOKE_001_CORRECT_SOURCES: dict[str, str]
_SMOKE_002_CORRECT_SOURCES: dict[str, str]
_SMOKE_003_CORRECT_SOURCES: dict[str, str]
```

Each dictionary contains only source files changed by that scenario.

Create:

```python
def _apply_single_replacement(
    sources: dict[str, str],
    path: str,
    old: str,
    new: str,
) -> dict[str, str]:
```

Require the old fragment occurs exactly once.

Each negative variant starts from the correct dictionary and applies exactly one conceptual mutation.

Do not duplicate full source files per variant.

## 11.3 Exact one-fault variants

Smoke 001:

```text
wrong_default:
  only MEDIUM default becomes HIGH

missing_filter:
  only TaskViewSet.get_queryset priority filtering is removed

invalid_serializer_choice:
  only serializer priority field becomes IntegerField
```

Task.Priority remains nested in every Smoke 001 variant.

Smoke 002:

```text
hard_delete:
  only perform_destroy permanently deletes

deleted_visible_in_normal_list:
  only normal queryset uses the unfiltered manager

restore_keeps_timestamp:
  only restore fails to clear deleted_at
```

All actions and managers otherwise remain correct.

Smoke 003:

```text
task_owner_authority:
  only task create/update/delete authority uses legacy Task.owner

project_non_owner_write_allowed:
  only ProjectViewSet uses baseline IsProjectMember for object writes

project_owner_writable:
  only ProjectSerializer owner is writable
```

All unrelated project/task/tag behavior remains correct.

## 11.4 Migration proof

After every builder:

- baseline numbered migration files still exist;
- their SHA-256 hashes match baseline;
- exactly one new numbered migration exists;
- no evaluator asset exists in workspace.

Builders still return `Path`.

---

# 12. Root defect H — integration tests are too permissive

## 12.1 Correct fixtures

For every correct variant assert exact check tuple.

Smoke 001 expected tuple:

```text
task_priority_enum
task_priority_field
task_priority_default
task_priority_valid_values
task_serializer_priority
task_priority_invalid_rejected
task_priority_filter
task_unfiltered_list
baseline_task_fields
project_and_tag_regression
```

Smoke 002 and Smoke 003 use their frozen exact lists.

## 12.2 Negative fixtures

Do not assert only:

```python
assert not result.passed
```

Also assert the intended failed check name appears in `result.error`.

Expected categories:

```text
todo-smoke-001 / wrong_default:
  task_priority_default

todo-smoke-001 / missing_filter:
  task_priority_filter

todo-smoke-001 / invalid_serializer_choice:
  task_serializer_priority

todo-smoke-002 / hard_delete:
  soft_delete_retains_row

todo-smoke-002 / deleted_visible_in_normal_list:
  default_manager_excludes_deleted

todo-smoke-002 / restore_keeps_timestamp:
  restore_action_restores

todo-smoke-003 / task_owner_authority:
  task_update_uses_project_owner

todo-smoke-003 / project_non_owner_write_allowed:
  project_non_owner_forbidden

todo-smoke-003 / project_owner_writable:
  project_owner_read_only
```

This proves each negative fixture tests its name.

## 12.3 Baseline integrity

Replace the current “baseline unchanged” test.

Before fixture construction, hash every baseline file.

After all fixture/evaluator work, hash the baseline again.

Require exact mapping equality.

## 12.4 Workspace migration integrity

For a built workspace:

- every baseline migration path exists;
- every baseline migration hash matches;
- exactly one new numbered migration exists.

## 12.5 Source isolation

Require:

```text
workspace/tests/evaluator_assets does not exist
workspace/scenario_evaluator.py does not exist
canonical evaluator hash before == after
```

## 12.6 JSON and temporary behavior

Require exact one-object stdout.

The runner parser already enforces this; the integration test must assert parsing and expected checks.

---

# 13. Documentation correction

The current R3C record and latest report describe code that is not present.

Examples of false statements:

```text
validates config dict
runs uv run -m pytest
uses pytest JSON report
parses summary/collectors/tests
maps to EvaluatorVerdict
uses deterministic mock responses
```

The committed production module actually copies one Python evaluator script, executes it, and parses:

```json
{"passed": ..., "checks": ..., "error": ...}
```

Rewrite the R3C record from the actual implementation.

Also correct:

```text
R3B independent audit: accepted and frozen at feb5a44
```

Do not leave R3B as “independent audit pending.”

The R3C correction documentation must say:

```text
R3C correction self-gates passed
independent audit pending
R3D blocked
```

Do not claim R3C accepted.

---

# 14. Incremental implementation order

OpenCode must execute this order.

## Step 1 — Runner trust and unit tests

Modify only:

```text
scenario_evaluator.py
test_scenario_evaluator.py
```

Add lexical symlink and workspace-leak rejection.

Run:

```powershell
python -m py_compile src/benchmark/execution/scenario_evaluator.py
python -m pytest tests/unit/execution/test_scenario_evaluator.py -k "InputValidation or TrustedAsset" -q
```

## Step 2 — Subprocess and truth-table tests

Strengthen exact command/env/cwd tests.

Add expected subprocess exceptions.

Replace fake truth table with public-path truth table.

Run the complete unit file.

## Step 3 — Common evaluator process architecture

Update all three evaluator assets to the same fail-closed JSON structure.

Compile all three.

Run a minimal correct Smoke 001 fixture.

## Step 4 — Smoke 001 semantic checks and one-fault fixtures

Complete correct and three negative runs.

Do not proceed until all four match expected check names.

## Step 5 — Smoke 002

Complete all four.

## Step 6 — Smoke 003

Complete all four.

## Step 7 — Cross-module integrity

Add R3B production migration integration, baseline hashes, old migration hashes, source isolation.

## Step 8 — Final code gates

Run all focused and full gates.

## Step 9 — Code commit

Commit only code/test artifacts.

## Step 10 — Documentation

Rewrite factual handoff and reports.

Commit documentation separately.

Stop for independent audit.

---

# 15. Required gates

```powershell
python -m pytest tests/unit/execution/test_scenario_evaluator.py -q

python -m pytest tests/integration/test_todo_smoke_evaluator_assets.py -q

python -m pytest `
  tests/unit/execution/test_scenario_evaluator.py `
  tests/integration/test_todo_smoke_evaluator_assets.py `
  tests/unit/execution/test_post_generation.py `
  -q

python -m pytest -q

ruff check `
  src/benchmark/execution/scenario_evaluator.py `
  src/benchmark/execution/__init__.py `
  tests/unit/execution/test_scenario_evaluator.py `
  tests/integration/test_todo_smoke_evaluator_assets.py `
  tests/support/evaluator_fixture_workspaces.py `
  tests/evaluator_assets

mypy --strict src/benchmark/execution/scenario_evaluator.py

python -m compileall `
  src/benchmark/execution/scenario_evaluator.py `
  tests/evaluator_assets

git diff --check
git diff --name-only
git diff --stat
```

No full-suite failure is allowed.

---

# 16. Authorized code files

```text
src/benchmark/execution/scenario_evaluator.py
tests/unit/execution/test_scenario_evaluator.py
tests/integration/test_todo_smoke_evaluator_assets.py
tests/support/evaluator_fixture_workspaces.py
tests/evaluator_assets/todo_smoke_001_checks.py
tests/evaluator_assets/todo_smoke_002_checks.py
tests/evaluator_assets/todo_smoke_003_checks.py
```

`src/benchmark/execution/__init__.py` should remain unchanged unless export verification exposes a real issue.

Forbidden:

```text
post_generation.py
test_post_generation.py
runner.py
pipeline.py
scenario YAML
Selective
Repository Agent
README
Kaggle bundle
notebooks
```

---

# 17. Commit messages

Code:

```text
fix(validation): complete R3C evaluator acceptance contract
```

Documentation:

```text
docs(audit): record R3C acceptance correction
```

Do not amend or squash previous R3C commits.

The history should preserve that independent audit corrected a materially inaccurate first implementation.

---

# 18. Required final report

Use the exact headings from Section 29 of the master spec.

The report must include an artifact table for every changed file.

It must explicitly state:

```text
fixture builder now calls run_post_generation_command
old migration hashes preserved
one new migration per fixture
negative variants are one-fault mutations
each negative fails the expected named check
runner rejects lexical asset symlinks
runner rejects evaluator assets inside workspace
truth table calls public run_scenario_evaluator
all three evaluator scripts always print one JSON object
```

It must list the twelve fixture results individually.

It must report:

```text
Requested model
Actual footer model
Starting HEAD
Code commit
Documentation commit
Final HEAD
Focused counts
Integration count
Full-suite count
Ruff
mypy
compileall
diff check
working tree
```

It must state:

```text
R3B accepted and frozen at feb5a44
R3C correction self-gates passed
R3C independent audit pending
R3D blocked
Kaggle/Pilot/merge/tag blocked
```

End exactly:

```text
R3C_ACCEPTANCE_CORRECTION_AUDIT_REQUIRED
```

---

# 19. Over-engineering limits

The correction should reduce complexity rather than add it.

Required limits:

- no new public API;
- no new production module;
- no shared evaluator helper module;
- no external dependency;
- no pytest JSON-report system;
- no generic fixture framework;
- no broad inheritance hierarchy;
- one correct-source dictionary per scenario;
- one single-replacement helper;
- one production migration helper;
- three standalone evaluator scripts;
- one runner module.

The current 1,778-line fixture file should become materially smaller by deriving negative variants from correct sources.

Do not measure success only by lower line count. Measure it by:

```text
one source of truth
one defect per negative variant
one real R3B migration path
one exact evaluator result
```

---

# 20. Project status

Current truthful status:

```text
R1 Repository Agent                  accepted
R2 Selective                         accepted
R3A Scenario metadata               accepted
R3B Migration runner                accepted and frozen
R3C Evaluator runner foundation     implemented
R3C semantic/integration contract   correction required
R3D Runner wiring                   blocked
R4 Token and metrics                pending
R5 Nine local records               pending
R6 Bundle and push                  pending
Kaggle                              blocked
Stable tag                          blocked
Pilot                               blocked
```

Near goal:

```text
one cohesive R3C acceptance correction
→ independent audit
→ freeze R3C
→ begin R3D
```

Distant goal:

```text
R3D validation wiring
→ R4 truthful metrics
→ R5 nine non-dry local records
→ R6 bundle and push
→ nine real Qwen Kaggle runs
→ independent result audit
→ v2.0.0-scientific-smoke tag
→ Pilot
```

---

**End of binding R3C correction contract.**
