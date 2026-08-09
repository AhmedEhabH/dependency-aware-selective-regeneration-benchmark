# R3C Final Root Correction and Freeze Specification

**Document status:** Binding final correction contract  
**Target branch:** `experiment/three-arm-smoke-v2`  
**Audited documentation HEAD:** `77f275e`  
**Audited R3C correction code checkpoint:** `81429c1`  
**Accepted and frozen R3B checkpoint:** `feb5a44`  
**Independent audit model:** GPT-5.6 Thinking  
**Required OpenCode model:** DeepSeek V4 Flash Free through OpenCode Zen, Build mode  
**Real scientific model later:** Qwen2.5-Coder-7B-Instruct on Kaggle  
**Current permission:** correct R3C only, then stop  
**R3D, R4, R5, R6, Kaggle, Pilot, merge, and stable tag:** blocked  

---

# 1. Binding verdict

R3C is not yet independently accepted at commit `81429c1`.

The latest correction is materially better than the first R3C implementation:

- the public evaluator API is stable;
- the four private evaluator states remain;
- lexical asset symlinks are rejected in the normal validation path;
- the evaluator executes from a temporary directory outside both roots;
- the generated workspace is first in `PYTHONPATH`;
- the parser accepts exactly one three-key JSON object;
- the fixture builder now invokes the accepted R3B migration function;
- baseline numbered migrations are no longer deleted;
- twelve named correct/negative fixture runs exist;
- the Windows full suite reports `1391 passed, 27 skipped`;
- the independent Linux environment runs the evaluator-runner unit file with `62 passed`.

The remaining defects share four root causes and must be corrected in one cohesive task:

1. trust is validated once, but is not revalidated at the moment evaluator bytes are loaded;
2. the evaluator scripts do not guarantee a JSON result if teardown fails;
3. several semantic checks still do not cover the frozen scenario contract;
4. documentation and process evidence are not truthful or internally consistent.

This is the final planned R3C correction. After it passes the complete Windows and Linux audit matrix, R3C is frozen. Do not begin R3D in the same task.

---

# 2. Independent audit evidence

## 2.1 Repository state

The supplied report claimed:

```text
Working tree: clean
```

The actual supplied repository state is:

```text
?? docs/R3C_ROOT_ACCEPTANCE_CORRECTION_SPEC.md
```

The tree is not clean.

This document was deliberately placed in the repository by the researcher and is part of the continuation record. It must be tracked, moved to an explicitly tracked record path, or deliberately removed with the documentation explaining why. It cannot remain untracked while the report says the tree is clean.

The preferred action is to track it as:

```text
docs/R3C_ROOT_ACCEPTANCE_CORRECTION_SPEC.md
```

because it is the binding specification that produced `81429c1`.

This new final correction document must be tracked as:

```text
docs/R3C_FINAL_ROOT_CORRECTION_AND_FREEZE_SPEC.md
```

## 2.2 Independent unit evidence

The independent Linux environment ran:

```text
PYTHONPATH=src python -m pytest tests/unit/execution/test_scenario_evaluator.py -q
```

Result:

```text
62 passed
```

The current unit tests execute, but several required failure classes are still absent or only nominally tested.

## 2.3 Broken evaluator-root symlink inside generated workspace

The production validator rejects:

```text
workspace/tests/evaluator_assets
```

only through:

```python
workspace_evaluator_path.exists()
```

A broken symlink returns `False` for `exists()`.

The independent audit created:

```text
workspace/tests/evaluator_assets
    → missing target
```

The current validator returned a valid `_ValidatedEvaluatorRequest`.

A broken evaluator-root symlink is still an evaluator path inside the generated workspace and must fail closed.

## 2.4 Asset replacement after validation

The independent audit performed:

1. validate an ordinary evaluator file;
2. replace the lexical evaluator file with a symlink to an outside file;
3. call `_load_trusted_evaluator_asset`.

The current request stores only the already-resolved path. `_load_trusted_evaluator_asset` reads that path without rechecking the lexical source.

The current function loaded the outside bytes.

This is a trust-of-check/time-of-use defect. The benchmark does not need a generic anti-race framework, but it must revalidate the asset immediately before reading it.

## 2.5 Teardown exception produces no JSON

All three evaluator assets use:

```python
finally:
    runner.teardown_databases(...)
    runner.teardown_test_environment()

print(json.dumps(payload))
```

If teardown raises, execution leaves the `finally` block before the JSON print.

The independent audit used a minimal fake Django module where:

```text
setup_databases raises
teardown_test_environment also raises
```

The current Smoke 001 evaluator produced:

```text
stdout: empty
stderr: traceback
```

The required contract is exactly one JSON object on every expected setup, execution, or teardown failure path.

## 2.6 Test name does not match behavior

The current test:

```text
test_copy_write_failure_returns_typed_outcome
```

does not create a copy-write failure. It runs the normal success path and checks only that an outcome object exists.

The report therefore overstates copy-failure coverage.

Required copy-read, copy-write, and copied-hash-mismatch tests are not all present as real fault-injection tests.

## 2.7 Smoke 003 “one-fault” fixture changes two behaviors

The `task_owner_authority` variant modifies:

```text
todo/permissions.py
todo/views.py
```

It changes both object authorization and task-create authorization.

The report says every negative variant changes exactly one thing. That statement is false.

The intended expected failure is:

```text
task_update_uses_project_owner
```

The variant should therefore change only the object-authority rule while preserving correct task-create authorization.

## 2.8 Latest report contains rejected historical claims

`reports/latest_phase_report.md` begins with the corrected R3C report, then appends an old rejected R3C section containing claims such as:

```text
uv run -m pytest
pytest JSON report
EvaluatorVerdict
config validation
```

Those claims do not describe the committed implementation.

A file named `latest_phase_report.md` must contain the latest factual state only. Historical rejected material belongs in `selective_updates/records`, not appended after the current stop marker.

## 2.9 Continuation specification is stale

`docs/V2_R3B_TO_KAGGLE_NO_DISCRETION_EXECUTION_SPEC.md` still says:

```text
R3B independent audit pending
R3C single-pass implementation pending
```

R3B has already been accepted and frozen at `feb5a44`.

The V2 continuation document must be updated with the actual phase state and current evidence.

---

# 3. Accepted architecture that must not change

Preserve the public API:

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

Preserve the helper names:

```text
_validate_evaluator_request
_load_trusted_evaluator_asset
_execute_evaluator_subprocess
_parse_evaluator_payload
_combine_evaluator_diagnostics
```

No new public production module is allowed.

No generic secure-filesystem framework is allowed.

No shared fourth evaluator script is allowed.

---

# 4. Authorized code artifacts

Modify only:

```text
src/benchmark/execution/scenario_evaluator.py
tests/unit/execution/test_scenario_evaluator.py
tests/integration/test_todo_smoke_evaluator_assets.py
tests/support/evaluator_fixture_workspaces.py
tests/evaluator_assets/todo_smoke_001_checks.py
tests/evaluator_assets/todo_smoke_002_checks.py
tests/evaluator_assets/todo_smoke_003_checks.py
```

`src/benchmark/execution/__init__.py` is already correct and must remain unchanged unless import verification reveals a real export defect.

Do not modify:

```text
src/benchmark/execution/post_generation.py
tests/unit/execution/test_post_generation.py
runner.py
pipeline.py
core models
scenario models
scenario YAML
Selective
Repository Agent
README
Kaggle bundle
notebooks
token metrics
```

---

# 5. Runner correction A — revalidate the trusted asset at load time

## 5.1 Store the lexical path

Add a private field to `_ValidatedEvaluatorRequest`:

```python
evaluator_asset_lexical: Path
```

Keep:

```python
evaluator_asset_path
```

as the resolved path observed during validation.

Public API is unchanged.

## 5.2 Create one private live-asset resolver

Add:

```python
def _resolve_live_evaluator_asset(
    request: _ValidatedEvaluatorRequest,
) -> Path | str:
    ...
```

This is a private helper, not a new public abstraction.

It must revalidate immediately before reading:

1. evaluator root exists;
2. evaluator root is a real directory;
3. evaluator root is not a symlink;
4. lexical evaluator path is not a symlink;
5. every lexical parent below evaluator root is not a symlink;
6. strict resolution succeeds;
7. resolved path remains beneath evaluator root;
8. resolved path equals the resolved path stored during validation;
9. resolved path is a regular file.

Return a diagnostic string for any failure.

## 5.3 Load only the revalidated file

`_load_trusted_evaluator_asset` calls `_resolve_live_evaluator_asset`.

Read bytes only from the returned live resolved path.

Catch:

```text
OSError
RuntimeError
ValueError
```

Return a string failure rather than raising.

## 5.4 Required tests

Add:

```text
test_asset_replaced_by_external_symlink_after_validation_fails
test_asset_replaced_by_internal_symlink_after_validation_fails
test_asset_replaced_by_different_regular_file_after_validation_fails
test_evaluator_root_replaced_by_symlink_after_validation_fails
```

The last regular-file replacement test requires a different resolved identity. A normal content modification at the same path is allowed between validation and trust only when the trusted bytes are read from that same ordinary file. The copy then uses frozen trusted bytes.

Do not implement platform-specific inode identity as a requirement.

---

# 6. Runner correction B — workspace leak detection

Replace:

```python
workspace_evaluator_path.exists()
```

with a live-path test that rejects all of:

```text
ordinary file
ordinary directory
working symlink
broken symlink
```

A safe condition is:

```python
if workspace_evaluator_path.exists() or workspace_evaluator_path.is_symlink():
    ...
```

Catch filesystem exceptions through the existing validation boundary.

Add:

```text
test_workspace_broken_evaluator_root_symlink_fails_closed
```

Call both:

```text
_validate_evaluator_request
run_scenario_evaluator
```

The public result must contain:

```text
passed=False
exit_code=-1
non-empty error
```

---

# 7. Runner correction C — real copy-failure evidence

## 7.1 Write failure

Replace the nominal test with real fault injection.

Patch `Path.write_bytes` only after the trusted asset is loaded.

Raise:

```python
OSError("simulated copy write failure")
```

Require:

```text
succeeded=False
exit_code=-1
stderr contains "failed to copy evaluator asset"
```

## 7.2 Copied-file read failure

After writing the copied path, make its `read_bytes` raise.

Require typed failure.

## 7.3 Hash mismatch

Return bytes different from the trusted source during copied-file verification.

Require:

```text
succeeded=False
exit_code=-1
stderr contains "hash"
```

## 7.4 Exact subprocess call

Strengthen the existing test to assert the complete command:

```python
[
    request.python_executable,
    str(copied_path),
    str(request.generated_workspace),
]
```

It must also assert:

```text
cwd == temporary directory
capture_output is True
text is True
timeout exact
shell absent
workspace first in PYTHONPATH
PYTHONDONTWRITEBYTECODE == 1
```

---

# 8. Evaluator-script correction — one JSON even on teardown failure

Apply the same control flow to all three assets.

## 8.1 Workspace validation

`_workspace_from_argv` must raise `ValueError` rather than print and call `sys.exit`.

This centralizes all output in `main`.

## 8.2 Teardown errors

Inside `main`, keep:

```python
teardown_errors: list[str] = []
```

In `finally`, independently wrap:

```python
runner.teardown_databases
runner.teardown_test_environment
```

Each failure appends:

```text
teardown_databases: <type>: <message>
teardown_test_environment: <type>: <message>
```

After teardown:

- set `payload["passed"] = False`;
- append teardown errors to `payload["error"]`;
- print exactly one JSON object;
- return 1.

No teardown exception may escape.

## 8.3 Outer structure

The only direct stdout write in the script is the final JSON print.

All Django output remains captured.

## 8.4 Required non-Django process tests

Add an integration test helper that creates a minimal fake workspace containing:

```text
manage.py
config/settings.py
todo/
django/__init__.py
django/test/runner.py
```

It must not require the real Django package.

Run every evaluator asset against two fake-runner variants:

### Setup failure with successful teardown

Require exactly one failed JSON object.

### Setup failure plus teardown failure

Require exactly one failed JSON object containing the teardown diagnostic.

This gives six small cross-platform runs:

```text
3 evaluator assets × 2 failure modes
```

They run on Linux and Windows and close the “always JSON” contract without relying on the real Django dependency.

---

# 9. Smoke 001 semantic closure

Keep the ten frozen check names.

## 9.1 Priority filter

After the HIGH/MEDIUM/LOW test rows are created, require:

```text
HIGH row included
MEDIUM row excluded
LOW row excluded
every returned result has priority HIGH
```

## 9.2 Unfiltered list

Collect every Task primary key currently in the test database.

Require all keys appear in the unfiltered list.

The test remains below the configured page size.

## 9.3 Project and Tag regression

The current check is too narrow.

Require:

### Model schema

Project concrete fields:

```text
id
name
description
```

Tag concrete fields:

```text
id
name
color
```

Require baseline field properties:

```text
Project.name max_length 200
Project.description blank
Tag.name max_length 100 and unique
Tag.color max_length 7
```

### Serializers

Require exact fields:

```text
ProjectSerializer:
id, name, description

TagSerializer:
id, name, color
```

Require valid deserialization and save.

### API

Authenticated:

```text
POST project succeeds
GET project detail succeeds
POST tag succeeds
GET tag detail succeeds
duplicate tag name returns 400
```

This is still one named regression check.

---

# 10. Smoke 002 semantic closure

Keep the nine frozen check names.

## 10.1 Project and Tag regression

Replace the current ORM-existence-only check.

Require the same baseline model and serializer properties as Smoke 001.

Exercise:

```text
authenticated Project create/read
authenticated Tag create/read
duplicate Tag rejected
```

Do not impose a manager name on Project or Tag.

## 10.2 Deleted and normal list contents

For every list response:

- normalize pagination;
- require the intended target;
- require the active control is included or excluded correctly;
- require every returned deleted row has non-null `deleted_at` when that field is serialized;
- at minimum prove no active control appears in the deleted action.

## 10.3 Restore data

Keep the complete preservation check:

```text
title
description
status
project
tags
```

Also require the restored task appears in normal list and detail after restore.

---

# 11. Smoke 003 semantic and architecture closure

Keep the ten frozen check names.

## 11.1 Authenticated reads

The current check tests only list endpoints.

Create a Project, Task, and Tag, then require the non-owner authenticated client can:

```text
list Projects
retrieve Project
list Tasks
retrieve Task
list Tags
retrieve Tag
```

## 11.2 Permission logic must live in permissions.py

The frozen scenario states:

```text
Permission logic must be in permissions.py, not in views or models.
```

The current “correct” fixture denies non-owner task creation inside `TaskViewSet.perform_create`.

Move task-create authorization into the Task permission class.

A correct fixture may use one permission class for Task and Project or separate classes, but the decisive Task permission used by `TaskViewSet` must deny:

```text
POST task into another user's Project
```

through `has_permission`.

`TaskViewSet.perform_create` must only save the serializer and must not raise `PermissionDenied` for project ownership.

## 11.3 Evaluator proof

Inside `task_create_uses_project_owner`:

1. retain the API owner/non-owner create checks;
2. inspect `TaskViewSet.permission_classes`;
3. instantiate the configured permission classes;
4. build a POST request for the other user and other-owned project;
5. require at least one configured permission class returns `False` from `has_permission`.

This proves create authorization derives from the permission layer rather than only from view code.

Do not enforce one permission-class name.

## 11.4 Correct fixture update

Update `_SMOKE_003_CORRECT_SOURCES`:

- permission class handles Task POST ownership;
- Task view no longer performs the authorization check;
- Project owner assignment remains in `ProjectViewSet.perform_create`.

Use:

```python
serializer.save(owner=self.request.user)
```

without a concrete `User` type check.

## 11.5 One-fault `task_owner_authority`

The negative variant modifies only the object-level permission rule so update/delete use legacy `Task.owner`.

Do not modify `TaskViewSet.perform_create`.

The expected failed check remains:

```text
task_update_uses_project_owner
```

Add a source-diff test proving exactly one source file differs from the correct variant.

## 11.6 One-fault proof for all variants

For every negative variant:

- compare source dictionaries before workspace creation;
- require exactly one source file differs;
- require the exact intended replacement count is one.

The fixture builder may expose a private:

```python
_get_sources_for_variant(
    scenario_id: str,
    variant: str,
) -> dict[str, str]
```

for integration tests.

Do not create a public fixture framework.

---

# 12. Integration integrity closure

## 12.1 Apply assertions to all twelve variants

Inside `_EvaluatorHelper.run`, after workspace construction and before evaluator execution:

- assert `workspace/tests/evaluator_assets` does not exist or is not a symlink;
- assert every baseline migration path exists;
- assert every baseline migration SHA-256 equals the canonical baseline;
- assert exactly one additional numbered migration exists.

This makes the migration proof apply to all correct and negative fixtures, not only three separate integrity tests.

## 12.2 Baseline hash computation

Replace hardcoded migration hashes with hashes read from the canonical baseline at test start.

The baseline is frozen, but computed hashes are clearer and survive an explicitly audited baseline update.

## 12.3 Correct results

Require exact check tuples.

## 12.4 Negative results

Require:

```text
passed=False
exit_code != 0
expected named check in error
```

Also require the failure is not a top-level setup/import/migration error:

```text
result.error does not begin with ModuleNotFoundError
result.error does not begin with RuntimeError from fixture building
```

## 12.5 Canonical evaluator integrity

For each of the three canonical evaluator assets:

- hash before all integration runs;
- hash after;
- require equality.

---

# 13. Documentation correction

## 13.1 Track both specifications

Track:

```text
docs/R3C_ROOT_ACCEPTANCE_CORRECTION_SPEC.md
docs/R3C_FINAL_ROOT_CORRECTION_AND_FREEZE_SPEC.md
```

## 13.2 Rewrite latest report

`reports/latest_phase_report.md` must contain only:

```text
R3C final correction self-gates
current commits
current tests
current limitations
independent audit pending
```

Remove the appended rejected R3C report and malformed historical fragments.

Historical information remains in:

```text
selective_updates/records/R3C-SINGLE-PASS-IMPLEMENTATION-RECORD.md
selective_updates/records/R3C-ROOT-ACCEPTANCE-CORRECTION.md
```

## 13.3 Update V2 continuation state

Update the top state to:

```text
R3B accepted and frozen at feb5a44
R3C final correction self-gates passed
R3C independent audit pending
R3D next but blocked
```

Record current test evidence.

Do not rewrite the entire long specification.

## 13.4 Correct reports

Do not claim:

```text
clean tree
copy failure tested
every negative changes one file
always one JSON
```

unless the new tests prove those exact claims.

---

# 14. Incremental execution order

## Step 1 — Runner trust

Modify:

```text
scenario_evaluator.py
test_scenario_evaluator.py
```

Run:

```powershell
python -m py_compile src/benchmark/execution/scenario_evaluator.py
python -m pytest tests/unit/execution/test_scenario_evaluator.py -k "symlink or TrustedAsset or workspace_evaluator" -q
```

## Step 2 — Real copy-failure tests

Add and pass:

```text
copy write
copy read
hash mismatch
```

Then run the complete unit file.

## Step 3 — Evaluator lifecycle

Update all three evaluator assets.

Compile each immediately.

Run the six fake-Django failure-mode executions.

## Step 4 — Smoke 001

Update evaluator and fixtures.

Run four Smoke 001 fixture results.

## Step 5 — Smoke 002

Run four Smoke 002 fixture results.

## Step 6 — Smoke 003

Move create authorization into permissions, update evaluator, make task-owner negative one-file.

Run four Smoke 003 results.

## Step 7 — Cross-fixture integrity

Run all twelve fixtures with migration and baseline assertions.

## Step 8 — Complete focused and full gates

Only after all focused gates pass.

## Step 9 — Code commit

Commit code and tests only.

## Step 10 — Documentation commit

Track specs and update factual continuation files.

Stop for independent audit.

---

# 15. Required commands

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

The Windows full suite must have zero failures.

The next independent audit will run:

```text
Linux evaluator-runner unit tests
Linux fake-Django lifecycle tests
direct trust-boundary adversarial cases
source and documentation audit
```

The real-Django fixture suite may be accepted from the Windows environment when dependency parity and exact output are provided.

---

# 16. Commit messages

Code commit:

```text
fix(validation): close R3C trust lifecycle and semantic gaps
```

Documentation commit:

```text
docs(audit): record R3C final freeze candidate
```

Do not amend or squash previous commits.

---

# 17. Required detailed final report

Use the complete Section 29 format from:

```text
docs/R3B_FREEZE_AND_R3C_SINGLE_PASS_MASTER_SPEC.md
```

The artifact table must include every changed file.

The report must explicitly show:

```text
broken workspace evaluator symlink rejected
asset replacement after validation rejected
real copy write/read/hash faults tested
all three scripts survive teardown failure with one JSON
Smoke 001 Project/Tag regression coverage
Smoke 002 Project/Tag regression coverage
Smoke 003 list and retrieve coverage
Task create authorization located in permission class
task_owner_authority negative changes one source file
all 12 fixtures preserve old migration hashes
one new migration for all 12 fixtures
both R3C specs tracked
latest_phase_report contains no rejected false section
V2 continuation status current
git status --short empty
```

List all twelve fixture outcomes individually.

State:

```text
R3B accepted and frozen at feb5a44
R3C final correction self-gates passed
R3C independent audit pending
R3D blocked
Kaggle/Pilot/merge/tag blocked
```

End exactly:

```text
R3C_FINAL_FREEZE_AUDIT_REQUIRED
```

---

# 18. Over-engineering limits

This correction must reduce ambiguity, not add architecture.

Forbidden:

- new public evaluator fields;
- new production module;
- shared evaluator package;
- generic security library;
- pytest JSON-report dependency;
- source-code generation framework;
- inheritance hierarchy for three scripts;
- changes to R3B;
- changes to Runner or Pipeline.

Allowed:

- one private live-asset resolver;
- one private fixture source-selection helper;
- stronger existing evaluator checks;
- fake-Django lifecycle fixtures inside integration tests.

---

# 19. Freeze policy

After this correction passes the next independent audit:

```text
R3C is frozen.
```

Do not reopen R3C for speculative strengthening.

R3C may be reopened only when R3D integration produces a reproducible failure that contradicts this frozen matrix.

The next phase is then R3D production wiring.

---

**End of final R3C correction contract.**
