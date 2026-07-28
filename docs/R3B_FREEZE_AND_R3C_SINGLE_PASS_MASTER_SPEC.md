# R3B Freeze and R3C Single-Pass Master Specification

**Document status:** Binding execution contract  
**Repository branch:** `experiment/three-arm-smoke-v2`  
**Audited documentation HEAD:** `800a62d`  
**Audited R3B refactor code checkpoint:** `f8f95d2`  
**Independent audit model:** GPT-5.6 Thinking  
**Required OpenCode model:** DeepSeek V4 Flash Free through OpenCode Zen, Build mode  
**Actual model displayed in the preceding OpenCode run:** `opencode/big-pickle`  
**Real scientific model later:** Qwen2.5-Coder-7B-Instruct on Kaggle  
**Current permission:** complete Section A only, then stop for independent audit  
**R3C execution permission:** blocked until Section A is independently accepted  
**Kaggle, Pilot, merge, and stable tag:** blocked  

---

# 0. Purpose

This file solves two problems at once.

First, it closes the final cross-platform defects in R3B without returning to open-ended patching. The R3B public API and trusted-state architecture remain fixed. Only two concrete mismatches found by independent Linux execution may be corrected. After that, R3B is frozen.

Second, it provides the complete single-pass implementation contract for R3C before OpenCode begins that phase. It specifies every artifact, dependency, name, state, test category, integration fixture, command, commit, and final report section. OpenCode should not need to search the repository broadly or invent architecture.

This document is intentionally larger than the short OpenCode prompt. The short prompt only tells OpenCode which section is authorized. All implementation detail lives here.

---

# 1. Why productivity was poor

The previous workflow produced many green test runs but low phase-level productivity. The reasons were process defects, not a lack of effort.

## 1.1 Features were described as outputs rather than complete state contracts

Earlier instructions often said:

```text
run a migration command;
detect one migration;
protect old migrations.
```

That describes the happy path. It does not define every state that can exist before and after the subprocess. Missing states were discovered one at a time:

```text
relative workspace;
directory escape;
helper.py instead of migration;
timeout after mutation;
unsafe symlink;
untrusted after-state with otherwise valid output;
missing directory after execution.
```

The correct planning unit is not an individual edge case. It is a state machine and a truth table.

## 1.2 Unit tests were added around examples instead of around invariants

A test proving one symlink fails does not prove all symlink timing and location combinations fail. Some tests created unsafe entries before the initial snapshot, while the production defect appeared only when the subprocess created the unsafe entry afterward.

Future tests must cover:

```text
before state
× command outcome
× after state
× semantic payload
```

rather than isolated examples.

## 1.3 Integration tests were too late and too weak

Many previous tests called private helpers directly or used success commands that did not execute the real production sequence. Private-helper tests are useful, but they cannot prove that the canonical public function composes helpers correctly.

Every future phase must include at least:

- one real public-path success;
- one real public-path failure;
- one combined adversarial public-path case;
- one cross-module integration case;
- one isolation proof.

## 1.4 Cross-platform skipped tests hid failures

Windows skipped symlink tests. The Windows full suite stayed green while the same committed focused suite failed on Linux. A phase involving filesystem or subprocess behavior cannot be accepted using only one operating system.

For filesystem phases:

```text
Windows full suite
AND Linux focused suite
```

are required before acceptance.

## 1.5 Naming and artifacts were not frozen early enough

When names are not fixed before implementation, OpenCode searches, invents alternatives, then rewrites code and tests to align with the new names.

Every phase from now on has:

- exact public names;
- exact private names;
- exact file paths;
- exact test class names;
- exact result fields;
- exact check names;
- exact commit messages.

OpenCode must not rename them.

## 1.6 OpenCode was allowed to make architecture decisions

The model sometimes simplified or generalized requirements:

- one generic evaluator instead of three assets;
- omitted command arguments;
- coercion instead of fail-closed validation;
- diagnostics collected without affecting success.

The master spec now defines the architecture. OpenCode implements it rather than choosing it.

## 1.7 Quality gates were concentrated at the end

Compile, type-check, lint, and integration errors were discovered after many edits.

Future phases use incremental gates:

```text
write one production artifact
→ compile it
→ run its smallest unit test
→ continue

write one evaluator asset
→ compile it
→ run its one fixture
→ continue
```

The final full suite remains required, but it is not the first time the code is executed.

## 1.8 Reports were too short

A report such as:

```text
mutable flow replaced with four states
1313 tests passed
```

does not tell the researcher:

- what each state owns;
- which decisions moved;
- which dependencies changed;
- which tests prove each invariant;
- which files were intentionally untouched;
- which risks remain.

The final report contract in this document requires an artifact-by-artifact explanation.

---

# 2. Permanent execution rules

These rules apply to Section A, R3C, and every later phase.

## 2.1 Exact read order

OpenCode reads only the files listed in the phase read order. It must not perform broad repository searches unless a listed file contains an unresolved import or the spec identifies an exact unknown.

When an additional file is genuinely required, OpenCode must print:

```text
UNPLANNED_READ_REQUIRED
file:
reason:
dependency that led to it:
```

and stop before changing that file.

## 2.2 No architecture discretion

When the spec gives a name, file, dataclass, field, command, validation rule, or state, OpenCode uses it exactly.

When the spec does not define behavior, OpenCode chooses the smallest behavior consistent with existing code and records the choice before implementation. It may not create a new framework or public API to resolve ambiguity.

## 2.3 No broad staging

Forbidden:

```text
git add .
git add src
git add tests
git commit -a
```

Use exact file paths listed by the phase.

## 2.4 Incremental compile gate

After each changed Python production file:

```powershell
python -m py_compile <file>
```

After each evaluator script:

```powershell
python -m py_compile <evaluator-file>
```

After each logical unit:

```powershell
python -m pytest <smallest-relevant-test> -q
```

OpenCode must fix compile and focused failures before editing the next logical unit.

## 2.5 Code before documentation

Sequence:

```text
production code
→ focused tests
→ integration tests
→ full suite
→ static gates
→ code commit
→ documentation
→ documentation commit
→ clean-tree proof
```

Do not update reports while code is still failing.

## 2.6 Documentation truth

OpenCode may write:

```text
implementation complete;
self-gates passed;
independent audit pending.
```

OpenCode may not write:

```text
independent audit accepted;
phase independently validated;
next phase unblocked.
```

Only GPT-5.6 Thinking independent audit may authorize the next phase.

## 2.7 Model truth

The final report states:

```text
Requested model:
Actual model shown in footer:
```

The footer is authoritative. A response must not claim DeepSeek when the footer shows Big Pickle.

## 2.8 No stable tag before real results

No tag during R3B, R3C, R3D, R4, R5, or R6.

The first stable V2 tag is allowed only after nine real Qwen Kaggle runs and independent result audit.

---

# SECTION A — R3B final cross-platform acceptance and freeze

# 3. Independent audit evidence

The Windows suite supplied by the researcher reports:

```text
1313 passed, 20 skipped
```

The independent Linux command:

```bash
PYTHONPATH=src python -m pytest tests/unit/execution/test_post_generation.py -q
```

collected 118 tests and produced:

```text
116 passed
2 failed
```

Both failures expect the valid ordinary migration path to remain visible when a separate unsafe migration symlink makes the after-state untrusted.

The current code returns:

```text
created_paths=()
```

because `_assess_migration_change` returns early when `after.trusted` is false.

The independent audit also reproduced this public-path false success:

```text
todo/migrations is an internal directory symlink
target remains inside workspace
command exits zero
require_new_migration=False
result passed=True
```

The root cause is:

```python
resolved = mig_dir.resolve(strict=True)
if resolved.is_symlink():
```

After resolution, `resolved` refers to the target. It is no longer the lexical symlink path. The correct symlink check is on `mig_dir` before resolution.

These are the only R3B corrections authorized by this document.

---

# 4. R3B artifacts and dependency impact

## 4.1 Modified production artifact

```text
src/benchmark/execution/post_generation.py
```

Affected private components:

```text
_take_migration_snapshot
_assess_migration_change
```

Unaffected public API:

```text
PostGenerationResult
run_post_generation_command
```

Unaffected modules:

```text
runner.py
pipeline.py
validation.py
core models
scenario models
scenario YAML
Selective
Repository Agent
```

## 4.2 Modified test artifact

```text
tests/unit/execution/test_post_generation.py
```

Affected test groups:

```text
TestTrustedMigrationSnapshot
TestMigrationAssessment
TestPublicOrchestration
TestRegressionCases
```

## 4.3 Documentation artifacts after code gates

```text
docs/PROJECT_HANDOFF.md
reports/latest_phase_report.md
docs/V2_R3B_TO_KAGGLE_NO_DISCRETION_EXECUTION_SPEC.md
selective_updates/CHANGE_INDEX.md
selective_updates/records/R3B-FINAL-CROSS-PLATFORM-FREEZE.md
```

The file containing this master spec must be tracked as:

```text
docs/R3B_FREEZE_AND_R3C_SINGLE_PASS_MASTER_SPEC.md
```

---

# 5. R3B exact code correction

## 5.1 Reject the lexical migration-directory symlink

Inside `_take_migration_snapshot`, before resolving:

```python
if mig_dir.is_symlink():
    relative = _relative_to_root(mig_dir, request.workspace_root)
    return _MigrationSnapshot(
        trusted=False,
        hashes={},
        diagnostics=(
            f"migration directory is a symlink: {relative or mig_dir.name}",
        ),
    )
```

Wrap `is_symlink()` in the same narrow filesystem exception handling used for snapshot operations.

Do not check `resolved.is_symlink()` as the primary symlink check. That check is ineffective after following the link.

This rule rejects internal and external directory symlinks.

## 5.2 Preserve valid partial created-path evidence

`_MigrationSnapshot` already contains hashes for valid ordinary Python files even when another entry causes:

```text
trusted=False
```

`_assess_migration_change` must compute:

- deleted or modified old paths;
- valid newly created numbered paths;

before returning the final assessment.

Do not return early solely because `after.trusted` is false.

Required semantics:

```text
after.trusted=False
→ assessment.passed=False
→ existing_unchanged=False
→ valid ordinary created numbered paths remain in created_paths
→ unsafe entries remain excluded
```

This produces truthful partial evidence while preventing success.

A suitable order is:

```python
diagnostics = before + after diagnostics

existing_unchanged = before.trusted and after.trusted

compare known old hashes
calculate new valid numbered paths from after.hashes
evaluate migration-count diagnostics
passed = (
    before.trusted
    and after.trusted
    and existing_unchanged
    and migration_count_ok
)
```

Once `existing_unchanged` is false because a snapshot is untrusted, later hash matches must not restore it to true.

## 5.3 No other production changes

Do not rename the four private state dataclasses.

Do not reorganize the full module again.

Do not add another public result field.

Do not create a generic snapshot library.

After these two corrections, R3B is frozen.

---

# 6. R3B exact tests

## 6.1 Internal directory symlink unit test

Create a real migration target directory inside the workspace.

Create:

```text
workspace/todo/migrations → workspace/real_migrations
```

Call `_take_migration_snapshot`.

Assert:

```text
trusted=False
diagnostic contains "migration directory is a symlink"
```

The test may skip on Windows only when symlink creation is unavailable.

## 6.2 Internal directory symlink public-path test

Create the same internal symlink before calling `run_post_generation_command`.

Use a successful Python command and `require_new_migration=False`.

Assert:

```text
passed=False
exit_code=-1
existing_migrations_unchanged=False
```

## 6.3 Valid migration plus unsafe file symlink

Retain the current Linux tests, but make their outside target path unambiguously correct.

The subprocess creates:

```text
todo/migrations/0002_good.py
todo/migrations/0003_evil.py → workspace/outside_target.py
```

Assert:

```text
passed=False
exit_code=-1
created_paths=("todo/migrations/0002_good.py",)
existing_migrations_unchanged=False
stderr contains "symlink"
```

## 6.4 Synthetic cross-platform assessment test

Construct:

```python
before = _MigrationSnapshot(
    trusted=True,
    hashes={"todo/migrations/__init__.py": "a"},
    diagnostics=(),
)

after = _MigrationSnapshot(
    trusted=False,
    hashes={
        "todo/migrations/__init__.py": "a",
        "todo/migrations/0002_good.py": "b",
    },
    diagnostics=("unsafe entry",),
)
```

Assert:

```text
passed=False
existing_unchanged=False
created_paths=("todo/migrations/0002_good.py",)
```

This test runs on Windows and guarantees the semantics even when symlink tests skip.

## 6.5 Focused Linux expectation

The focused test file must have zero failures on Linux.

The final independent audit will run the exact test file from the archive. OpenCode must not report R3B complete using only Windows results.

---

# 7. R3B gates and commits

## 7.1 Start proof

```powershell
git branch --show-current
git rev-parse HEAD
git status --short
git log --oneline --decorate -8
```

Expected HEAD:

```text
800a62d
```

Expected tree:

```text
clean
```

## 7.2 Incremental gates

After editing production code:

```powershell
python -m py_compile src/benchmark/execution/post_generation.py
```

After adding the synthetic assessment test:

```powershell
python -m pytest tests/unit/execution/test_post_generation.py -k "partial or assessment" -q
```

After adding symlink tests:

```powershell
python -m pytest tests/unit/execution/test_post_generation.py -q
```

## 7.3 Complete gates

```powershell
python -m pytest tests/unit/execution/test_post_generation.py -q

python -m pytest `
  tests/unit/execution/test_post_generation.py `
  tests/unit/execution/test_validation.py `
  -q

python -m pytest -q

ruff check `
  src/benchmark/execution/post_generation.py `
  tests/unit/execution/test_post_generation.py

mypy --strict src/benchmark/execution/post_generation.py

python -m compileall src/benchmark/execution/post_generation.py

git diff --check
git diff --name-only
git diff --stat
```

Before code commit, exactly two files may be changed.

## 7.4 Code commit

```text
fix(validation): close cross-platform migration snapshot contract
```

## 7.5 Documentation commit

Track this master spec and create the short audit record.

Update factual state only.

```text
docs(audit): record R3B cross-platform freeze candidate
```

## 7.6 Stop marker

```text
R3B_CROSS_PLATFORM_FREEZE_AUDIT_REQUIRED
```

Do not start R3C in the same task.

---

# SECTION B — R3C single-pass implementation contract

R3C remains unauthorized until the independent auditor accepts Section A.

After authorization, OpenCode uses this section without requesting another architecture decision.

---

# 8. R3C feature definition

R3C provides isolated scenario correctness evaluation.

It creates:

1. one safe evaluator runner in benchmark production code;
2. exactly three standalone evaluator assets;
3. deterministic fixture-workspace support;
4. unit tests for the runner state machine;
5. integration tests proving each evaluator accepts a correct workspace and rejects incorrect workspaces.

R3C does not connect the main BenchmarkRunner. That is R3D.

R3C does not change token metrics. That is R4.

R3C does not run a real LLM.

---

# 9. R3C exact read order

OpenCode must read these files in order before editing:

```text
1. docs/R3B_FREEZE_AND_R3C_SINGLE_PASS_MASTER_SPEC.md
2. src/benchmark/execution/post_generation.py
3. src/benchmark/execution/validation.py
4. src/benchmark/execution/__init__.py
5. src/benchmark/scenarios/models.py
6. benchmark_data/scenarios/todo-smoke-001.yaml
7. benchmark_data/scenarios/todo-smoke-002.yaml
8. benchmark_data/scenarios/todo-smoke-003.yaml
9. pyproject.toml
10. benchmark_data/repositories/todo/config/settings.py
11. benchmark_data/repositories/todo/config/urls.py
12. benchmark_data/repositories/todo/todo/models.py
13. benchmark_data/repositories/todo/todo/serializers.py
14. benchmark_data/repositories/todo/todo/permissions.py
15. benchmark_data/repositories/todo/todo/views.py
16. benchmark_data/repositories/todo/todo/urls.py
17. benchmark_data/repositories/todo/todo/tests/test_models.py
18. benchmark_data/repositories/todo/todo/tests/test_serializers.py
19. benchmark_data/repositories/todo/todo/tests/test_permissions.py
20. benchmark_data/repositories/todo/todo/tests/test_views.py
```

Do not search for alternative evaluator architecture.

---

# 10. R3C artifact map

## 10.1 New production artifact

```text
src/benchmark/execution/scenario_evaluator.py
```

Owns:

- request validation;
- evaluator asset trust;
- temporary copy;
- subprocess execution;
- JSON parsing;
- semantic success decision;
- typed result.

## 10.2 Modified export artifact

```text
src/benchmark/execution/__init__.py
```

Exports only:

```text
ScenarioEvaluatorResult
run_scenario_evaluator
```

## 10.3 New evaluator assets

```text
tests/evaluator_assets/todo_smoke_001_checks.py
tests/evaluator_assets/todo_smoke_002_checks.py
tests/evaluator_assets/todo_smoke_003_checks.py
```

Each is standalone.

## 10.4 New test support

```text
tests/support/evaluator_fixture_workspaces.py
```

Owns deterministic baseline copies and correct/incorrect fixture source content.

Production code must not import it.

## 10.5 New unit tests

```text
tests/unit/execution/test_scenario_evaluator.py
```

## 10.6 New integration tests

```text
tests/integration/test_todo_smoke_evaluator_assets.py
```

## 10.7 Documentation after code commit

```text
docs/PROJECT_HANDOFF.md
reports/latest_phase_report.md
docs/R3B_FREEZE_AND_R3C_SINGLE_PASS_MASTER_SPEC.md
selective_updates/CHANGE_INDEX.md
selective_updates/records/R3C-SINGLE-PASS-IMPLEMENTATION-RECORD.md
```

No README changes in R3C.

---

# 11. R3C naming contract

## 11.1 Public names

```python
ScenarioEvaluatorResult
run_scenario_evaluator
```

## 11.2 Private state names

```python
_ValidatedEvaluatorRequest
_TrustedEvaluatorAsset
_EvaluatorCommandOutcome
_ParsedEvaluatorPayload
```

Do not choose synonyms.

## 11.3 Private helper names

```python
_validate_evaluator_request
_load_trusted_evaluator_asset
_execute_evaluator_subprocess
_parse_evaluator_payload
_combine_evaluator_diagnostics
```

## 11.4 Test class names

```python
TestEvaluatorInputValidation
TestTrustedEvaluatorAsset
TestEvaluatorSubprocess
TestEvaluatorPayloadParsing
TestEvaluatorSuccessTruthTable
TestEvaluatorIsolation
```

## 11.5 Fixture builder names

```python
build_todo_smoke_001_workspace
build_todo_smoke_002_workspace
build_todo_smoke_003_workspace
```

Each accepts:

```python
destination: Path
variant: str = "correct"
```

## 11.6 Exact variant names

Smoke 001:

```text
correct
wrong_default
missing_filter
invalid_serializer_choice
```

Smoke 002:

```text
correct
hard_delete
deleted_visible_in_normal_list
restore_keeps_timestamp
```

Smoke 003:

```text
correct
task_owner_authority
project_non_owner_write_allowed
project_owner_writable
```

No additional variant naming.

---

# 12. R3C public API

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

All fields are required. Do not add defaults that hide missing construction data.

---

# 13. R3C state ownership

## 13.1 `_ValidatedEvaluatorRequest`

Fields:

```python
canonical_project_root: Path
evaluator_root: Path
evaluator_asset_path: Path
evaluator_asset_relative: str
generated_workspace: Path
python_executable: str
timeout: int
```

All Paths are resolved absolute paths.

## 13.2 `_TrustedEvaluatorAsset`

Fields:

```python
source_path: Path
relative_path: str
content: bytes
sha256: str
```

The source asset must be read before the temporary directory is created. The copied file hash must match.

## 13.3 `_EvaluatorCommandOutcome`

Fields:

```python
succeeded: bool
exit_code: int
stdout: str
stderr: str
```

## 13.4 `_ParsedEvaluatorPayload`

Fields:

```python
passed: bool
checks: tuple[str, ...]
error: str
```

One final expression determines the public result.

---

# 14. Input and path validation

## 14.1 Canonical root

Accept `str | Path`.

Require:

- exists;
- directory;
- resolves successfully;
- contains `tests/evaluator_assets`;
- evaluator root is a real directory;
- evaluator root is not a symlink.

## 14.2 Evaluator asset

Require:

- non-empty string;
- not whitespace-only;
- no NUL;
- no backslash;
- not absolute;
- no `..`;
- normalized path starts exactly with `tests/evaluator_assets/`;
- `.py` suffix;
- direct or nested regular file under evaluator root;
- not symlink;
- resolves beneath evaluator root;
- exists and readable.

The three approved assets are direct files.

## 14.3 Generated workspace

Accept `str | Path`.

Require:

- exists;
- directory;
- resolved;
- not equal to canonical root;
- canonical root is not inside workspace;
- workspace is not inside canonical root;
- no approved evaluator asset exists inside workspace.

## 14.4 Python executable

Require non-empty, non-whitespace string without NUL.

Do not require it to be an absolute path.

## 14.5 Timeout

Require:

```python
type(timeout) is int
timeout > 0
```

---

# 15. Evaluator copy and temporary directory

Use:

```python
tempfile.TemporaryDirectory(prefix="benchmark_evaluator_")
```

After creation:

- resolve it;
- prove it is outside generated workspace;
- prove it is outside canonical project root;
- copy evaluator bytes to:
  `scenario_evaluator.py`;
- hash copied bytes;
- require copied hash equals trusted source hash.

Do not copy:

- sibling evaluator scripts;
- scenario YAML;
- Ground Truth;
- tests;
- repository profiles.

Run the evaluator from the temporary directory.

---

# 16. Subprocess contract

Command:

```python
[
    python_executable,
    str(copied_evaluator_path),
    str(generated_workspace),
]
```

Environment:

```python
env = os.environ.copy()
env["PYTHONDONTWRITEBYTECODE"] = "1"
env["PYTHONPATH"] = (
    str(generated_workspace)
    + os.pathsep
    + env.get("PYTHONPATH", "")
)
```

Execute:

```python
subprocess.run(
    command,
    cwd=str(temporary_directory),
    env=env,
    capture_output=True,
    text=True,
    timeout=timeout,
)
```

Handle:

```text
TimeoutExpired
FileNotFoundError
ValueError
OSError
SubprocessError
```

No shell.

---

# 17. JSON payload contract

The evaluator prints exactly one JSON object:

```json
{"passed":true,"checks":["check_name"],"error":""}
```

Rules:

- stdout stripped must parse with one `json.loads`;
- top-level object only;
- exact required keys:
  `passed`, `checks`, `error`;
- no missing keys;
- no unknown keys;
- `passed` bool;
- `checks` list;
- every check non-empty string;
- no duplicate check names;
- `error` string;
- when `passed=True`, error must be empty;
- when `passed=False`, error must be non-empty.

Extra stdout before or after JSON makes parsing fail.

Stderr does not affect parsing but remains preserved.

---

# 18. Final evaluator success equation

Public result passes only when:

```text
request valid
AND evaluator asset trusted
AND copy hash matches
AND subprocess exit code == 0
AND payload parsed
AND payload passed == True
AND payload error == ""
AND checks is non-empty
```

Contradictory states fail:

```text
exit 0 + passed false
exit non-zero + passed true
passed true + non-empty error
passed false + empty error
```

No diagnostic may be collected without affecting the corresponding trust state.

---

# 19. Standalone evaluator common architecture

Each evaluator asset contains its own small helpers. Do not create a shared fourth evaluator module.

Required flow:

```text
validate one workspace argument
set environment
prepend workspace to sys.path
capture Django stdout/stderr
django.setup()
DiscoverRunner.setup_test_environment()
DiscoverRunner.setup_databases()
execute named checks
teardown databases
teardown environment
print exactly one JSON object
exit 0 or 1
```

Use `try/finally`.

The script must not import benchmark code.

The script must not read scenario YAML or Ground Truth.

The script may inspect generated Django models, serializers, permissions, URLs, and API behavior.

---

# 20. Smoke 001 evaluator

Exact check names:

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

Required behavior is defined by the scenario YAML.

The evaluator must support paginated response data.

It must reject `URGENT`.

It must verify all three allowed stored values.

It must prove Project and Tag baseline behavior.

---

# 21. Smoke 002 evaluator

Exact check names:

```text
soft_delete_retains_row
soft_delete_sets_timestamp
default_manager_excludes_deleted
normal_list_excludes_deleted
deleted_detail_is_404
deleted_action_lists_deleted
restore_action_restores
soft_deleted_data_preserved
project_and_tag_regression
```

Use `_base_manager` when checking retained row so no custom manager name is imposed.

Verify tags and core fields survive restoration.

---

# 22. Smoke 003 evaluator

Exact check names:

```text
project_owner_field
project_creator_becomes_owner
project_owner_read_only
project_owner_can_write
project_non_owner_forbidden
task_create_uses_project_owner
task_update_uses_project_owner
task_delete_uses_project_owner
authenticated_reads_unrestricted
tag_permissions_unchanged
```

Do not require one particular permission class name.

Do not use Task.owner as authority.

Verify owner assignment through API.

Verify Tag behavior exactly matches baseline.

---

# 23. Fixture workspace architecture

`tests/support/evaluator_fixture_workspaces.py` copies the baseline Todo repository.

It overwrites only the source files required by each correct or incorrect fixture.

It then calls the production:

```python
run_post_generation_command
```

with the exact command:

```python
(
    sys.executable,
    "manage.py",
    "makemigrations",
    "todo",
    "--noinput",
)
```

Require one migration before evaluator execution.

This creates an early cross-module integration between R3B and R3C without wiring BenchmarkRunner.

Fixture builders return the workspace path.

No fixture code enters production packages.

---

# 24. R3C unit test matrix

Unit tests must cover at least:

## Input validation

- valid paths;
- missing canonical root;
- canonical root file;
- missing evaluator root;
- evaluator root symlink;
- empty asset;
- whitespace asset;
- NUL;
- backslash;
- traversal;
- absolute;
- wrong extension;
- missing file;
- asset symlink;
- workspace missing;
- workspace file;
- workspace equals canonical root;
- workspace nested under canonical root;
- canonical root nested under workspace;
- empty Python executable;
- NUL executable;
- invalid timeout types.

## Trusted asset

- valid content and SHA-256;
- read failure;
- file changes between read and copy;
- copied hash mismatch;
- copy failure.

## Subprocess

- exact command;
- exact cwd;
- workspace first in PYTHONPATH;
- byte and string timeout output;
- command not found;
- ValueError;
- OSError;
- SubprocessError.

## Payload parsing

- valid;
- whitespace around JSON;
- extra stdout before;
- extra stdout after;
- malformed JSON;
- non-object;
- missing keys;
- unknown keys;
- wrong types;
- empty check;
- duplicate check;
- contradictory passed/error.

## Truth table

Parameterize command and payload combinations.

## Isolation

- temp outside workspace;
- evaluator not copied into workspace;
- only one asset copied;
- temp cleaned after success;
- temp cleaned after failure.

---

# 25. R3C integration test matrix

For each scenario:

```text
correct variant passes
three named incorrect variants fail
expected check category appears
```

Total minimum:

```text
3 correct runs
9 negative runs
```

Also test:

- ordinary pytest does not collect evaluator scripts;
- evaluator stdout is exactly JSON;
- source evaluator never appears in workspace;
- baseline snapshot remains unchanged;
- generated workspace receives exactly one migration.

The integration test calls the real runner and real evaluator assets.

---

# 26. R3C incremental build sequence

OpenCode must follow this sequence exactly.

## Step 1

Create `scenario_evaluator.py` dataclasses and validation only.

Run:

```powershell
python -m py_compile src/benchmark/execution/scenario_evaluator.py
python -m pytest tests/unit/execution/test_scenario_evaluator.py -k "InputValidation" -q
```

## Step 2

Add asset trust and copy.

Run trusted-asset tests.

## Step 3

Add subprocess outcome.

Run subprocess tests.

## Step 4

Add JSON parser and truth table.

Run payload and truth-table tests.

## Step 5

Export public names.

Compile import.

## Step 6

Create Smoke 001 evaluator and fixture variants.

Compile and run only Smoke 001 integration.

## Step 7

Create Smoke 002 evaluator and variants.

Compile and run only Smoke 002.

## Step 8

Create Smoke 003 evaluator and variants.

Compile and run only Smoke 003.

## Step 9

Run complete R3C tests.

## Step 10

Run full suite and static gates.

This sequence prevents writing three broken evaluator scripts before the runner works.

---

# 27. R3C complete gates

```powershell
python -m pytest tests/unit/execution/test_scenario_evaluator.py -q

python -m pytest tests/integration/test_todo_smoke_evaluator_assets.py -q

python -m pytest `
  tests/unit/execution/test_scenario_evaluator.py `
  tests/integration/test_todo_smoke_evaluator_assets.py `
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

---

# 28. R3C commits

Code commit:

```text
feat(validation): add isolated scenario evaluator system
```

Documentation commit:

```text
docs(state): record R3C implementation pending audit
```

Stop marker:

```text
R3C_SINGLE_PASS_IMPLEMENTATION_AUDIT_REQUIRED
```

---

# 29. Detailed OpenCode final report contract

Every phase report must be between 1,000 and 1,800 words. It must be detailed but not repetitive.

Use these exact headings.

## A. Model and execution identity

```text
Requested model:
Actual footer model:
Provider:
Mode:
Elapsed time:
```

## B. Git identity

```text
Branch:
Starting HEAD:
Code commit:
Documentation commit:
Final HEAD:
Working tree:
```

## C. Phase objective

Explain in 3–6 sentences what the phase was required to prove.

## D. Artifact-by-artifact modifications

Use a table:

| File | Before | After | Why | Direct dependencies | Tests proving it |
|---|---|---|---|---|---|

Every changed file gets one row.

Do not write only “refactored.”

For production files, name:

- classes;
- functions;
- fields;
- validation rules;
- state transitions;
- exceptions handled.

For tests, name:

- test classes;
- positive cases;
- negative cases;
- integration cases.

## E. Dependency impact

List:

```text
Changed dependencies:
Read-only dependencies:
Deliberately unaffected artifacts:
```

Explain why each dependent file did or did not require modification.

## F. Public API and naming

List every public name added or preserved.

List every private state name added.

State:

```text
Naming deviations: none
```

or report the deviation and stop.

## G. State machine implemented

Print the exact state flow.

For every state, explain:

- input;
- trusted data;
- output;
- failure representation.

## H. Failure matrix evidence

Use a table:

| Failure category | Test name | Expected result | Actual result |
|---|---|---|---|

Include combined adversarial cases, not only primitive validation.

## I. Integration evidence

Explain the real public-path sequence used.

State whether private helpers alone were insufficient.

For R3C, list all 12 fixture runs.

## J. Incremental build evidence

List each compile/test checkpoint in chronological order.

This proves errors were caught early.

## K. Final gates

Use exact command and exact count/result.

Do not write “all clean” without command names.

## L. Changed-file and scope proof

Print:

```text
git diff --name-only <start>..<code-commit>
git show --stat --oneline <code-commit>
git show --stat --oneline <docs-commit>
```

State unauthorized changes: none.

## M. Documentation updates

For each documentation file, state the exact status line changed.

## N. Known limitations

Do not say “none” automatically.

State only factual remaining boundaries.

## O. Phase authorization

State:

```text
Implementation self-gates passed.
Independent audit pending.
Next phase remains blocked.
```

## P. Final marker

Use the exact phase marker.

---

# 30. Detailed report quality rules

Forbidden report phrases without evidence:

```text
everything works
fully secure
all edge cases covered
production ready
independent audit satisfied
no limitations
```

Use:

```text
all listed contract cases passed
no known failure inside the frozen matrix
independent audit pending
```

The report must include actual model footer truth.

---

# 31. Permanent naming pattern

Use these patterns for future phases.

Production modules:

```text
snake_case.py
```

Public result dataclasses:

```text
<StageName>Result
```

Public execution functions:

```text
run_<stage_name>
```

Private validated request:

```text
_Validated<StageName>Request
```

Private process result:

```text
_<StageName>CommandOutcome
```

Unit tests:

```text
test_<module_name>.py
```

Integration tests:

```text
test_<domain>_<phase>_integration.py
```

Audit records:

```text
<PHASE>-<UPPERCASE-DESCRIPTION>.md
```

Code commits:

```text
feat(...)
fix(...)
refactor(...)
test(...)
```

Documentation commits:

```text
docs(state)
docs(audit)
```

Do not alternate names once frozen.

---

# 32. Productivity metrics for future phases

The phase report records:

```text
number of production files changed
number of test files changed
number of new tests
number of integration runs
number of compile failures during implementation
number of focused-test failures during implementation
number of corrections before code commit
number of independent-audit correction cycles
```

Target:

```text
one implementation cycle
one independent audit
zero architecture rewrites
zero naming rewrites
zero compile failures after code commit
```

These metrics measure process quality without changing scientific experiment metrics.

---

# 33. Acceptance philosophy

“Cover all possibilities” does not mean inventing infinitely many filesystem or framework behaviors.

It means:

1. define the state dimensions;
2. cover every equivalence class;
3. cover important combinations;
4. prove the public composition;
5. freeze the contract.

After R3B Section A is accepted, no more speculative R3B edge-case searching is authorized.

After R3C’s complete matrix passes and independent audit accepts it, move to R3D.

---

# 34. Immediate researcher workflow

1. Place this file at:

```text
project/docs/R3B_FREEZE_AND_R3C_SINGLE_PASS_MASTER_SPEC.md
```

2. Send OpenCode the short Section A prompt.

3. Receive the detailed report.

4. Export a fresh ZIP.

5. Run one independent Linux-focused audit.

6. When accepted, send the Section B R3C prompt using this same file.

No new R3C architecture file should be needed.

---

# 35. Section A short prompt

```text
Use DeepSeek V4 Flash Free through OpenCode Zen in Build mode.
Do not use Big Pickle.

Branch:
experiment/three-arm-smoke-v2

Current HEAD:
800a62d

Read completely:
docs/R3B_FREEZE_AND_R3C_SINGLE_PASS_MASTER_SPEC.md

Execute SECTION A only.

Correct only:
src/benchmark/execution/post_generation.py
tests/unit/execution/test_post_generation.py

Implement exactly:
1. reject the lexical migration-directory symlink before resolve;
2. preserve valid ordinary created numbered paths as partial evidence when
   another unsafe entry makes the after snapshot untrusted;
3. keep passed=False and existing_migrations_unchanged=False for every
   untrusted after snapshot;
4. add the exact internal-directory-symlink and synthetic cross-platform tests.

Do not redesign the module again.
Do not start R3C.

Run every Section A incremental and final gate.
Create the exact code and documentation commits.
Print the full detailed report using Section 29.

End exactly:
R3B_CROSS_PLATFORM_FREEZE_AUDIT_REQUIRED
```

---

# 36. Section B short prompt after authorization

```text
Use DeepSeek V4 Flash Free through OpenCode Zen in Build mode.

Branch:
experiment/three-arm-smoke-v2

Read completely:
docs/R3B_FREEZE_AND_R3C_SINGLE_PASS_MASTER_SPEC.md

Independent audit has accepted Section A.
Execute SECTION B only: R3C.

Follow the exact read order, artifact map, naming contract, state machine,
failure matrix, fixture variants, incremental build sequence, final gates,
commit messages, and report contract.

Do not modify Runner, Pipeline, token metrics, README, bundle, Selective, or
Repository Agent.

Do not start R3D.

End exactly:
R3C_SINGLE_PASS_IMPLEMENTATION_AUDIT_REQUIRED
```

---

**End of master specification.**

# Appendix A — Artifact dependency matrix

## A.1 `src/benchmark/execution/scenario_evaluator.py`

**Incoming dependency:** Scenario YAML evaluator_asset through future Runner configuration  
**Implementation dependencies:** pathlib, tempfile, shutil, subprocess, json, hashlib, os, time  
**Outgoing contract:** ScenarioEvaluatorResult and run_scenario_evaluator  
**Required evidence:** unit state-machine tests and integration fixture runs

OpenCode must explain this artifact in the final report. It must state what the
artifact owned before the phase, what it owns after the phase, and why no
neighboring artifact requires modification. Imports must follow existing
project style. Test-only support must never be imported by production code.
Any dependency not listed here is an unplanned dependency and triggers the
`UNPLANNED_READ_REQUIRED` stop rule.

## A.2 `src/benchmark/execution/__init__.py`

**Incoming dependency:** scenario_evaluator public exports  
**Implementation dependencies:** scenario_evaluator module  
**Outgoing contract:** two added __all__ names only  
**Required evidence:** import isolation and full suite

OpenCode must explain this artifact in the final report. It must state what the
artifact owned before the phase, what it owns after the phase, and why no
neighboring artifact requires modification. Imports must follow existing
project style. Test-only support must never be imported by production code.
Any dependency not listed here is an unplanned dependency and triggers the
`UNPLANNED_READ_REQUIRED` stop rule.

## A.3 `tests/evaluator_assets/todo_smoke_001_checks.py`

**Incoming dependency:** Todo models, serializers, views, URLs and Django test database  
**Implementation dependencies:** Django, DRF inside generated workspace  
**Outgoing contract:** exact JSON payload  
**Required evidence:** correct + wrong_default + missing_filter + invalid_serializer_choice

OpenCode must explain this artifact in the final report. It must state what the
artifact owned before the phase, what it owns after the phase, and why no
neighboring artifact requires modification. Imports must follow existing
project style. Test-only support must never be imported by production code.
Any dependency not listed here is an unplanned dependency and triggers the
`UNPLANNED_READ_REQUIRED` stop rule.

## A.4 `tests/evaluator_assets/todo_smoke_002_checks.py`

**Incoming dependency:** Todo soft-deletion implementation and API  
**Implementation dependencies:** Django, DRF inside generated workspace  
**Outgoing contract:** exact JSON payload  
**Required evidence:** correct + hard_delete + deleted_visible + restore_keeps_timestamp

OpenCode must explain this artifact in the final report. It must state what the
artifact owned before the phase, what it owns after the phase, and why no
neighboring artifact requires modification. Imports must follow existing
project style. Test-only support must never be imported by production code.
Any dependency not listed here is an unplanned dependency and triggers the
`UNPLANNED_READ_REQUIRED` stop rule.

## A.5 `tests/evaluator_assets/todo_smoke_003_checks.py`

**Incoming dependency:** Project owner, task project-owner authorization, Tag regression  
**Implementation dependencies:** Django, DRF inside generated workspace  
**Outgoing contract:** exact JSON payload  
**Required evidence:** correct + three permission/serializer negatives

OpenCode must explain this artifact in the final report. It must state what the
artifact owned before the phase, what it owns after the phase, and why no
neighboring artifact requires modification. Imports must follow existing
project style. Test-only support must never be imported by production code.
Any dependency not listed here is an unplanned dependency and triggers the
`UNPLANNED_READ_REQUIRED` stop rule.

## A.6 `tests/support/evaluator_fixture_workspaces.py`

**Incoming dependency:** baseline Todo copy and R3B post-generation command  
**Implementation dependencies:** shutil, pathlib, exact source templates  
**Outgoing contract:** workspace Path  
**Required evidence:** all evaluator integration tests

OpenCode must explain this artifact in the final report. It must state what the
artifact owned before the phase, what it owns after the phase, and why no
neighboring artifact requires modification. Imports must follow existing
project style. Test-only support must never be imported by production code.
Any dependency not listed here is an unplanned dependency and triggers the
`UNPLANNED_READ_REQUIRED` stop rule.

## A.7 `tests/unit/execution/test_scenario_evaluator.py`

**Incoming dependency:** scenario_evaluator private and public contracts  
**Implementation dependencies:** pytest, monkeypatch, temporary directories  
**Outgoing contract:** no production exports  
**Required evidence:** all unit matrix groups

OpenCode must explain this artifact in the final report. It must state what the
artifact owned before the phase, what it owns after the phase, and why no
neighboring artifact requires modification. Imports must follow existing
project style. Test-only support must never be imported by production code.
Any dependency not listed here is an unplanned dependency and triggers the
`UNPLANNED_READ_REQUIRED` stop rule.

## A.8 `tests/integration/test_todo_smoke_evaluator_assets.py`

**Incoming dependency:** real runner, real assets, real Django fixture workspaces  
**Implementation dependencies:** fixture builders and post-generation runner  
**Outgoing contract:** no production exports  
**Required evidence:** 12 minimum real evaluator runs

OpenCode must explain this artifact in the final report. It must state what the
artifact owned before the phase, what it owns after the phase, and why no
neighboring artifact requires modification. Imports must follow existing
project style. Test-only support must never be imported by production code.
Any dependency not listed here is an unplanned dependency and triggers the
`UNPLANNED_READ_REQUIRED` stop rule.


# Appendix B — Failure-class planning checklist

## B.1 primitive type validation

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.2 path normalization

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.3 path traversal

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.4 lexical symlink

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.5 resolved containment

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.6 missing filesystem entry

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.7 wrong filesystem entry type

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.8 filesystem mutation between validation and use

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.9 filesystem read failure

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.10 copy failure

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.11 copy hash mismatch

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.12 temporary-directory placement

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.13 subprocess timeout

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.14 subprocess command missing

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.15 subprocess malformed argument

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.16 subprocess operating-system error

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.17 subprocess protocol error

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.18 non-zero exit

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.19 empty stdout

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.20 extra stdout before JSON

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.21 extra stdout after JSON

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.22 malformed JSON

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.23 wrong top-level type

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.24 missing JSON key

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.25 unknown JSON key

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.26 wrong JSON field type

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.27 empty check name

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.28 duplicate check name

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.29 contradictory passed/error payload

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.30 exit/payload contradiction

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.31 workspace contamination

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.32 canonical-source mutation

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.

## B.33 temporary cleanup after failure

For this failure class, the phase implementation must answer four questions
before code is committed:

1. Which trusted state first detects the failure?
2. Which typed result field represents it?
3. Which public-path test proves the failure cannot be forgotten by the final
   success equation?
4. Which integration or isolation test proves that handling the failure does
   not mutate the canonical project or generated workspace unexpectedly?

A private-helper test alone is not sufficient when the failure can occur
during composition. The final report must cite the exact test name and actual
result. When the class is not applicable to an artifact, the report must say
why rather than silently omit it.


# Appendix C — Compile and test failure prevention checklist

Before editing:

- confirm branch and clean tree;
- confirm current HEAD;
- confirm every authorized file exists or is intentionally new;
- confirm Python version;
- confirm pytest excludes evaluator assets;
- confirm the three scenario metadata paths exactly match planned assets.

For every Python file:

- write imports and dataclass/function skeleton;
- run `py_compile`;
- run Ruff on the file;
- run mypy when the file is production;
- then add behavior.

For every public function:

- add type-validation tests first;
- add happy-path unit test;
- add failure truth table;
- add public composition test;
- only then connect integration fixtures.

For every evaluator:

- compile before execution;
- run against one correct fixture;
- run against one negative fixture;
- inspect stdout manually once;
- verify exactly one JSON object;
- then add remaining variants.

Before code commit:

- no skipped test may be the only evidence for an invariant;
- no test name may claim behavior it does not exercise;
- no test may contain `if len(...)` guards that allow assertions to disappear;
- no test may accept either of two unrelated results;
- no private helper may be tested while the public path remains untested;
- no model footer mismatch may be hidden.

# Appendix D — Integration strength requirements

Integration is considered strong only when it crosses real boundaries.

R3C integration must cross:

```text
baseline repository copy
→ deterministic source fixture
→ production post-generation command
→ generated migration
→ production evaluator runner
→ copied standalone evaluator
→ separate Python process
→ Django test database
→ real API/model/serializer/permission checks
→ exact JSON payload
→ typed ScenarioEvaluatorResult
```

Mocking is allowed in unit tests but not as the only integration evidence.

The integration test must assert:

- source workspace path;
- migration path;
- evaluator source location;
- temporary evaluator location;
- subprocess exit;
- payload check names;
- canonical baseline hash unchanged;
- evaluator not present in workspace;
- temporary directory removed.

# Appendix E — Detailed report example structure

The report should not merely reproduce the todo list. It should describe the
actual implementation.

Example artifact row:

| File | Before | After | Why | Dependencies | Evidence |
|---|---|---|---|---|---|
| `scenario_evaluator.py` | did not exist | adds four immutable states, one public result, one public runner | isolate hidden evaluator execution from generated workspace | scenario metadata, Python subprocess, evaluator assets | 61 unit tests, truth table, 12 integration runs |

Example state explanation:

```text
_ValidatedEvaluatorRequest receives untrusted caller values and emits only
resolved paths and frozen command settings. It never reads evaluator content.

_TrustedEvaluatorAsset reads and hashes exactly one approved asset and proves
that the asset is an ordinary file under tests/evaluator_assets.

_EvaluatorCommandOutcome converts subprocess completion and expected process
exceptions into strings and an exit code.

_ParsedEvaluatorPayload accepts only the exact JSON schema.

The public result passes only when all four states are trusted.
```

Example limitation:

```text
The evaluator runner is not yet connected to BenchmarkRunner. This is expected
and belongs to R3D. R3C proves the runner and assets independently.
```

# Appendix F — Stop conditions

OpenCode must stop immediately when:

- requested model is not available and footer model differs;
- starting HEAD differs from the prompt;
- working tree is not clean;
- an unauthorized file is modified;
- a required existing file is missing;
- the spec conflicts with a frozen public API;
- a new dependency appears necessary;
- a focused test exposes an architectural contradiction;
- evaluator integration requires modifying the Todo baseline;
- full suite has any failure.

The response then prints:

```text
PHASE_BLOCKED
reason:
files changed:
last passing command:
first failing command:
```

Do not continue by improvising.
