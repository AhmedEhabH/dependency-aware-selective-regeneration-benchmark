# V2 R3B-to-Kaggle No-Discretion Execution Specification

**Document status:** Authoritative continuation contract  
**Target branch:** `experiment/three-arm-smoke-v2`  
**Current documentation HEAD at audit time:** `2370a573622f416eeea6bc70845817c5d08f9882`  
**Current audited R3A code checkpoint:** `3eaab6058328cfb8a84e8262fcef4977d9a3b245`  
**Implementation model:** DeepSeek V4 Flash Free through OpenCode Zen, Build mode  
**Independent audit model:** GPT-5.6 Thinking  
**Local production-proof backend:** deterministic test-only `ScriptedLLMBackend`  
**Real scientific Smoke model after local proof:** `Qwen2.5-Coder-7B-Instruct` on Kaggle  
**Temperature for the real experiment:** `0.0`  
**Per-call completion limit:** `4096` tokens  
**Current local evidence supplied by the researcher:** `1424 passed, 32 skipped, 0 failed` on Windows/Python 3.11  
**Phase status:** R4 ACCEPTED AND FROZEN at a46213c (independent re-audit by GPT-5.6 Thinking on 2026-07-31); R5 RESUMED after pre-results baseline-contract amendment R5-BASELINE-CONTRACT-001 (correction commit 8fafb50)
**R4 audit-correction commits:** c928bd9 (.gitattributes), cc32b17 (4 production + 2 test files), a46213c (5 docs)
**R5 baseline-contract amendment:** R5-BASELINE-CONTRACT-001 (2026-07-31) — pre-results, no Smoke V2 record existed; production files changed = NONE; scenario YAML changed = NONE; 7 correction files committed as 8fafb50; record in selective_updates/records/R5-BASELINE-CONTRACT-AMENDMENT.md
**R5 execution directive:** ..\OPENCODE_R5_NINE_RECORDS_SINGLE_PASS_DIRECTIVE.md
**R5 correction directive:** ..\OPENCODE_R5_CONTRACT_CORRECTION_AND_RESUME_DIRECTIVE.md
**Next permitted phase:** R5 — nine non-dry scripted production records (AUTHORIZED — current)
**Kaggle:** blocked  
**Pilot:** blocked  
**Merge:** blocked  
**Stable V2 tag:** blocked  
**README:** intentionally deferred to R6

---

## 0. How to use this document

This document exists to remove implementation discretion from OpenCode while completing the remaining Scientific Smoke V2 production path. It is intentionally explicit. OpenCode must read the complete document before editing code. It must execute phases in order and stop at the end of each phase for an independent audit. It must never jump directly from the current state to Kaggle, even when the unit-test suite remains green.

The allowed execution order is:

```text
R3B — deterministic post-generation migration runner
R3C — isolated scenario evaluator runner and three evaluator scripts
R3D — wire migration, baseline tests, and evaluators into every non-dry Runner path
R4  — correct token semantics, stage metrics, and persistence
R5  — prove nine non-dry scripted production-path records
R6  — final documentation, bundle, parity, push, and Kaggle authorization audit
K1  — researcher-controlled real Kaggle Smoke, only after independent authorization
K2  — independent result audit and stable tag decision
P1  — Pilot planning, only after the stable V2 Smoke tag exists
```

OpenCode must execute **only one phase per task unless the researcher explicitly authorizes more**. A phase is not complete because some focused tests pass. A phase is complete only when:

1. every required behavior is implemented in the real canonical path;
2. every required positive and negative test exists;
3. the full project suite has zero failures;
4. Ruff, mypy, compile checks, and `git diff --check` pass;
5. the changed-file list contains only authorized files;
6. the phase has a focused local checkpoint commit;
7. handoff and phase-report documents state the actual result without exaggeration;
8. an independent audit accepts the phase.

This document supersedes stale current-state descriptions in older continuation notes when those descriptions conflict with the current commits above. It does not supersede the frozen scientific invariants defined by the V2 three-arm contract.

---

## 1. Current project state that must be preserved

The branch already contains the following accepted work:

### 1.1 Safe editable universe

Scientific regeneration is restricted to the exact production-file policy loaded from the Todo repository profile. The editable universe is:

```text
todo/models.py
todo/serializers.py
todo/views.py
todo/permissions.py
todo/urls.py
```

Baseline tests, evaluator assets, configuration, existing migrations, caches, databases, `manage.py`, and package initialization files are not LLM-editable artifacts. Empty or invalid editable policies fail closed. Ground Truth does not construct this universe.

### 1.2 Monolithic reference arm

The Monolithic or `full_scope_reference` arm selects all five allowed production files. It is the full-scope cost and correctness reference. It must not be rewritten into a different implementation. It still uses the shared code-generation executor and receives no test or evaluator code.

### 1.3 Dependency-aware Selective arm

The Selective arm uses only:

- public requirement text;
- public acceptance criteria;
- public repository-profile metadata;
- artifact symbols and change triggers;
- the repository dependency graph;
- explicit public negative constraints.

It does not use scenario IDs, `expected_affected_artifacts`, `expected_actions`, evaluator source, hidden-test text, generated outcomes, or prior experimental results.

The accepted Smoke scopes are frozen before real-model execution:

```text
todo-smoke-001:
  todo/models.py
  todo/serializers.py
  todo/views.py

todo-smoke-002:
  todo/models.py
  todo/views.py

todo-smoke-003:
  todo/models.py
  todo/permissions.py
  todo/serializers.py
  todo/views.py
```

Do not tune the Selective algorithm or the reverse-consumer threshold after seeing Qwen results.

### 1.4 Bounded Repository Agent arm

The Repository Agent explores the active isolated workspace with bounded:

- `list_files`;
- `read_file`;
- `search_text`.

The complete selection/retrieval process has a maximum of eight LLM calls per run, including invalid responses and revisions. It may inspect no more than thirty distinct files. It must return a non-empty subset of the five-file ArtifactUniverse. The same `SharedRegenerationExecutor` writes all selected source files.

### 1.5 R3A scenario execution metadata

All three V2 Smoke scenarios now load:

```python
evaluator_asset: str
post_generation_command: tuple[str, ...]
require_new_migration: bool
```

The exact values are:

```text
todo-smoke-001 evaluator:
tests/evaluator_assets/todo_smoke_001_checks.py

todo-smoke-002 evaluator:
tests/evaluator_assets/todo_smoke_002_checks.py

todo-smoke-003 evaluator:
tests/evaluator_assets/todo_smoke_003_checks.py
```

Every Smoke scenario has this command:

```text
python manage.py makemigrations todo --noinput
```

Every Smoke scenario has:

```text
require_new_migration = True
```

This metadata must remain outside `RequirementChange`, selection prompts, generation prompts, repair prompts, Agent tool results, and strategy-visible repository content.

### 1.6 Evidence boundary

The currently supplied `1205 passed, 10 skipped` result is strong engineering evidence for completed R1, R2, and R3A work. It does not prove:

- migration creation;
- migration integrity;
- scenario correctness;
- evaluator isolation;
- correct validation order;
- truthful per-call token semantics;
- complete stage metrics;
- nine non-dry production records;
- Kaggle readiness;
- real-model correctness.

OpenCode must never describe the current state as “Smoke completed,” “Kaggle ready,” “stable,” or “scientifically validated.”

---

## 2. Scientific invariants that no phase may change

### 2.1 Same experiment input

All three arms receive the same:

- pinned Todo baseline;
- natural-language `requirement_before`;
- natural-language `requirement_after`;
- public acceptance criteria;
- backend model identity;
- temperature;
- per-call completion-token limit;
- isolated workspace construction;
- migration command;
- baseline test command;
- scenario evaluator;
- result schema.

The changes are independent. Every run starts from the same immutable baseline. Scenario 002 does not start from Scenario 001 output. Scenario 003 does not start from Scenario 002 output.

### 2.2 Only scope acquisition differs

The arms may differ only in how editable source files are selected:

```text
Monolithic:
select all five allowed source files.

Selective:
deterministic public metadata + public requirement + dependency graph.

Repository Agent:
bounded LLM repository exploration.
```

After selection, every source-code edit must use the same `SharedRegenerationExecutor`. Do not implement a special writer for one arm. Do not let the Agent directly patch files. Do not let Selective use hardcoded implementations. Do not let Monolithic use evaluator information.

### 2.3 The LLM writes source code

The harness may:

- choose context;
- limit editable files;
- execute bounded tools;
- ask for complete file replacement;
- validate output;
- run `makemigrations`;
- run baseline tests;
- run isolated evaluator checks;
- request bounded repair;
- calculate metrics.

The harness may not hardcode the scientific implementation inside production strategies. The test-only scripted backend may return deterministic fixture implementations to prove orchestration, but production code must never import that backend.

### 2.4 Ground Truth is post-hoc

Ground Truth includes:

- `expected_affected_artifacts`;
- `expected_actions`;
- hidden evaluator expectations used for assessment;
- post-hoc precision and recall labels.

Ground Truth may be read by evaluation code only after a strategy has returned a prediction. It must not influence:

- ArtifactUniverse;
- repository profile construction;
- Selective seeds;
- graph traversal;
- Agent prompt content;
- Agent tool content;
- generation prompts;
- repair prompts;
- migration execution;
- baseline validation;
- scenario success decisions.

### 2.5 Evaluator source is private from the arms

The three evaluator scripts live in the benchmark project, not in the generated Todo workspace. The selection strategies and code-generation backend must never see their source or their exact check implementation.

The evaluator runner may copy one selected evaluator script to a temporary directory outside the model-visible workspace immediately before execution. It may pass the workspace path as a command-line argument. It must not copy evaluator scripts into the workspace.

### 2.6 Tests are not editable artifacts

The LLM does not write:

- baseline tests;
- evaluator scripts;
- configuration;
- existing migrations;
- database files;
- cache files;
- results;
- documentation.

Baseline tests and evaluator scripts are evidence owned by the harness, not output owned by the model.

### 2.7 Failed runs remain data

A real Kaggle run that fails is still an experimental record. Do not delete it, silently retry it with changed logic, or tune the algorithm after observing it. Environmental preflight failures may be retried under the existing resume policy, but model-output and correctness failures remain visible.

---

## 3. Operational rules for every remaining phase

### 3.1 Branch and state

Work only on:

```text
experiment/three-arm-smoke-v2
```

Do not create another branch. Do not merge. Do not rebase. Do not reset the complete branch. Do not apply the historical broken-methodology stash. Do not modify old commits except when a phase explicitly authorizes amending the immediately preceding unpushed code checkpoint.

At the beginning of every phase print:

```powershell
git branch --show-current
git rev-parse HEAD
git status --short
git log --oneline --decorate -8
```

The tree must be clean before starting a new phase. If it is not clean, stop and report exact files before editing.

### 3.2 Small phases, not broad implementation

OpenCode must not implement R3B through R6 in one response. The intended workflow is:

```text
implement one phase
run focused tests
run the full suite
run quality gates
commit code
update state documents
commit documentation
stop for independent audit
```

This prevents a green high-level summary from hiding a wrong literal path, missing flag, weak test, or unconnected production method.

### 3.3 Authorized files

Each phase lists its authorized files. OpenCode must print:

```powershell
git diff --name-only
git diff --stat
```

before committing. Any unexpected file is a failed gate. Do not classify an unexpected edit as harmless. Restore it or explain the blocker.

### 3.4 Test order

Use this order:

1. exact unit test for the new behavior;
2. all focused tests for the changed subsystem;
3. integration or contract test that uses the production construction path;
4. full project suite;
5. Ruff on changed Python files;
6. mypy strict on changed production files;
7. `compileall` on changed production files;
8. `git diff --check`;
9. exact negative searches;
10. changed-file scope check.

A focused test result never replaces the full suite.

### 3.5 Documentation policy

Update continuously:

- `docs/PROJECT_HANDOFF.md`;
- `reports/latest_phase_report.md`;
- `docs/V2_R3B_TO_KAGGLE_NO_DISCRETION_EXECUTION_SPEC.md` phase-status table;
- `selective_updates/CHANGE_INDEX.md`.

Update `README.md` only at R6, when the user-facing local production path is complete. Updating README after every internal microphase creates noise and stale claims. Continuous documentation means maintaining the handoff and latest report after each phase, while README reflects stable user-facing milestones.

### 3.6 Tag policy

Do not create a stable tag during R3B, R3C, R3D, R4, R5, or R6.

A local scripted production proof authorizes the real Kaggle Smoke; it is not a stable scientific release.

The suggested stable tag:

```text
v2.0.0-scientific-smoke
```

is authorized only after all nine real Qwen runs exist, all records are preserved, results and metrics are independently audited, Ground Truth isolation is approved, and the deployed bundle equals the pushed source.

---

# PHASE R3B — Deterministic post-generation migration runner

## 4. R3B goal

R3B creates one small production module that runs a scenario’s post-generation command inside the isolated generated workspace and proves that migration generation is deterministic and safe.

R3B does **not** wire the runner yet. It does not create evaluators. It does not change token accounting. It does not create scripted Smoke records. It only creates and tests the reusable migration stage.

The core question for R3B is:

> After the LLM modifies source files, can the harness run `makemigrations`, detect exactly one new migration when required, prove every old migration remains byte-identical, and return a typed result without touching the immutable snapshot?

## 5. R3B authorized files

Modify or create only:

```text
src/benchmark/execution/post_generation.py
src/benchmark/execution/__init__.py
tests/unit/execution/test_post_generation.py
docs/PROJECT_HANDOFF.md
reports/latest_phase_report.md
docs/V2_R3B_TO_KAGGLE_NO_DISCRETION_EXECUTION_SPEC.md
selective_updates/CHANGE_INDEX.md
```

Do not modify:

```text
src/benchmark/execution/runner.py
src/benchmark/execution/pipeline.py
src/benchmark/core/models.py
seven_arm_benchmark.py
scenario YAML
evaluator assets
README.md
kaggle_upload/
notebooks/
```

## 6. R3B exact production API

Create:

```python
# src/benchmark/execution/post_generation.py

from __future__ import annotations

import hashlib
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Sequence


@dataclass(frozen=True)
class PostGenerationResult:
    passed: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    created_paths: tuple[str, ...] = ()
    existing_migrations_unchanged: bool = False


def run_post_generation_command(
    workspace_root: str | Path,
    command: Sequence[str],
    *,
    require_new_migration: bool,
    timeout: int = 180,
    migration_directory: str = "todo/migrations",
) -> PostGenerationResult:
    ...
```

Do not rename the dataclass or function. Do not create a class wrapper. Do not create a generic task-execution framework. One function and small private helpers are sufficient.

## 7. R3B input validation

`run_post_generation_command` must fail closed and return a failed typed result for invalid execution input. It must not raise ordinary input or subprocess errors to the Runner.

Validate:

1. `workspace_root` exists;
2. `workspace_root` is a directory;
3. `command` is non-empty;
4. every command item is a non-empty string;
5. `require_new_migration` is a bool;
6. `timeout` is greater than zero;
7. `migration_directory` is a repository-relative POSIX path;
8. `migration_directory` is not absolute;
9. it contains no `..`;
10. it contains no backslash;
11. after resolution, it remains under `workspace_root`;
12. the migration directory exists and is a directory.

Use `exit_code=-1` for validation, timeout, command-not-found, or operating-system failures. Put the diagnostic in `stderr`. Set `duration_seconds` to the elapsed non-negative duration even on failure.

Do not create a missing migration directory automatically. A missing expected Django migration directory is a harness or generated-project failure.

## 8. R3B migration snapshot rules

Before running the command:

- list every direct `*.py` file under `todo/migrations`;
- include `__init__.py` when hashing existing files;
- exclude `__init__.py` only from numbered-migration creation counts;
- calculate SHA-256 from raw bytes;
- record each existing repository-relative POSIX path;
- record its hash.

Do not recurse into nested directories. Django app migrations are direct files under the migration directory.

Use a private helper equivalent to:

```python
def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
```

Use sorted paths everywhere for deterministic output.

## 9. R3B subprocess execution

Run:

```python
subprocess.run(
    list(command),
    cwd=str(workspace_root),
    capture_output=True,
    text=True,
    timeout=timeout,
)
```

Do not use `shell=True`. Do not join command items into one shell string. Do not execute the command at the benchmark project root. The command must run in the generated Todo workspace.

Handle:

- `subprocess.TimeoutExpired`;
- `FileNotFoundError`;
- `OSError`.

For a timeout use:

```text
exit_code = -1
passed = False
stderr contains "timed out"
```

For command not found use:

```text
exit_code = -1
passed = False
stderr identifies command[0]
```

## 10. R3B after-state rules

After the subprocess finishes, inspect migrations even when the command failed. This allows the harness to detect that a failed command still corrupted an existing migration.

Calculate:

```text
before_all = existing *.py paths before command
after_all  = existing *.py paths after command
new_paths  = after_all - before_all
```

The protected old migration result is true only when:

- every old path still exists;
- every old path has the same SHA-256 hash.

A deleted old migration is a change and must fail.

A renamed old migration appears as one missing old path and one new path; it must fail.

A changed `__init__.py` must fail even though it is not counted as a numbered migration.

Created migration paths must:

- be sorted;
- be repository-relative POSIX strings;
- resolve beneath the workspace;
- end in `.py`;
- be direct children of the configured migration directory;
- exclude `__init__.py`.

When `require_new_migration=True`, success requires exactly one new numbered migration.

When `require_new_migration=False`, the migration-count condition is satisfied regardless of the number created, but command success and old-file integrity are still required. R3D will skip the post-generation stage entirely when there is no command.

The final result is passed only when:

```text
subprocess exit code == 0
AND existing_migrations_unchanged is True
AND (
    require_new_migration is False
    OR len(created_paths) == 1
)
```

If the command exits zero but creates no required migration, return failed.

If it exits zero but creates two migrations, return failed.

If it creates one migration but modifies an old migration, return failed.

Include an explanatory diagnostic in `stderr`. Preserve original subprocess stdout and stderr, appending harness diagnostics with a clear separator such as:

```text
[post-generation validation]
...
```

## 11. R3B unit tests

Create `tests/unit/execution/test_post_generation.py`. Use temporary directories and tiny Python commands. Do not invoke Django for every unit test. Unit tests should create a fake `todo/migrations` structure and use `sys.executable -c` commands to create or modify files.

Required tests:

1. valid command creates exactly one migration and passes;
2. created path is repository-relative POSIX;
3. created paths are sorted;
4. existing numbered migrations remain unchanged;
5. existing `__init__.py` remains unchanged;
6. command exits non-zero and result fails;
7. command timeout fails;
8. command not found fails;
9. missing workspace fails;
10. workspace path that is a file fails;
11. empty command fails;
12. command containing an empty item fails;
13. non-bool `require_new_migration` fails;
14. zero timeout fails;
15. negative timeout fails;
16. absolute migration directory fails;
17. traversal migration directory fails;
18. backslash migration directory fails;
19. missing migration directory fails;
20. modified old numbered migration fails;
21. deleted old numbered migration fails;
22. modified `__init__.py` fails;
23. exactly zero new migrations fails when required;
24. exactly two new migrations fail when required;
25. one new migration passes when required;
26. no new migration may pass when not required;
27. a new `__init__.py` is not counted as a numbered migration;
28. a nested `.py` file is not counted;
29. a new non-Python file is not counted;
30. result duration is non-negative for success and failure.

At least one test must use the current exact Smoke command shape as a tuple:

```python
("python", "manage.py", "makemigrations", "todo", "--noinput")
```

but replace the executable behavior with a controlled fixture or monkeypatch. Do not require a live Django project in every unit test.

## 12. R3B quality gate

Run:

```powershell
python -m pytest tests/unit/execution/test_post_generation.py -q
python -m pytest tests/unit/execution/test_post_generation.py tests/unit/execution/test_validation.py -q
python -m pytest -q
ruff check src/benchmark/execution/post_generation.py src/benchmark/execution/__init__.py tests/unit/execution/test_post_generation.py
mypy --strict src/benchmark/execution/post_generation.py
python -m compileall src/benchmark/execution/post_generation.py
git diff --check
git diff --name-only
```

The changed-file list before the code commit must contain exactly:

```text
src/benchmark/execution/post_generation.py
src/benchmark/execution/__init__.py
tests/unit/execution/test_post_generation.py
```

Create the code commit:

```powershell
git add src/benchmark/execution/post_generation.py src/benchmark/execution/__init__.py tests/unit/execution/test_post_generation.py
git commit -m "feat(validation): add deterministic migration runner"
```

Then update the four state documents. Record:

- R3B complete;
- code-checkpoint hash;
- actual final test count;
- exact API name;
- old migration integrity evidence;
- R3C next;
- Kaggle blocked;
- stable tag blocked.

Create:

```powershell
git add docs/PROJECT_HANDOFF.md reports/latest_phase_report.md docs/V2_R3B_TO_KAGGLE_NO_DISCRETION_EXECUTION_SPEC.md selective_updates/CHANGE_INDEX.md
git commit -m "docs(state): record R3B completion"
```

Stop. Do not start R3C in the same task.

---

# PHASE R3C — Isolated scenario evaluation

## 13. R3C goal

R3C creates:

1. a safe evaluator-subprocess runner;
2. three evaluator scripts;
3. tests proving evaluator isolation and correctness.

R3C does not wire the main Runner yet. It must test each evaluator script against deterministic hand-prepared fixture workspaces so the scripts are known to accept correct implementations and reject incorrect implementations before R3D connects them to generation.

## 14. R3C authorized files

Create or modify only:

```text
src/benchmark/execution/scenario_evaluator.py
src/benchmark/execution/__init__.py
tests/evaluator_assets/todo_smoke_001_checks.py
tests/evaluator_assets/todo_smoke_002_checks.py
tests/evaluator_assets/todo_smoke_003_checks.py
tests/unit/execution/test_scenario_evaluator.py
tests/integration/test_todo_smoke_evaluator_assets.py
tests/support/evaluator_fixture_workspaces.py
docs/PROJECT_HANDOFF.md
reports/latest_phase_report.md
docs/V2_R3B_TO_KAGGLE_NO_DISCRETION_EXECUTION_SPEC.md
selective_updates/CHANGE_INDEX.md
```

Do not modify Runner, Pipeline, token code, Selective, Agent, scenario YAML, or baseline Todo tests.

`tests/evaluator_assets` remains excluded from ordinary pytest collection. The integration tests execute the assets explicitly through the evaluator runner.

## 15. R3C exact runner API

Create:

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

Do not rename this API. Do not import Django in this module. The parent benchmark process must remain isolated from generated project imports.

## 16. Evaluator path validation

The evaluator path is benchmark-owned metadata. Validate it before copying:

- it is a non-empty string;
- it is repository-relative POSIX;
- it is not absolute;
- it contains no `..`;
- it contains no backslash;
- it ends with `.py`;
- its normalized parent starts with exactly `tests/evaluator_assets`;
- it resolves beneath `<canonical_project_root>/tests/evaluator_assets`;
- it exists and is a regular file;
- it is not a symlink escaping the evaluator root.

Reject:

```text
C:\...
/tmp/...
../...
tests\...
tests/evaluator_assets/../../secret.py
docs/evaluator.py
tests/test_normal_pytest_file.py
```

Validate the generated workspace:

- exists;
- is a directory;
- is not the same path as the canonical project root;
- does not contain the canonical evaluator file;
- may contain generated source and migrations.

Validate `python_executable` as a non-empty string and `timeout > 0`.

Return typed failure results rather than leaking ordinary path or subprocess exceptions.

## 17. Evaluator temporary directory and subprocess

Use `tempfile.TemporaryDirectory(prefix="benchmark_evaluator_")` without placing it under the generated workspace. After creation, resolve it and verify it is not inside the workspace.

Copy only the selected evaluator script to the temporary directory. Use a neutral filename such as:

```text
scenario_evaluator.py
```

Do not copy sibling evaluator scripts, tests, scenario YAML, Ground Truth, or repository profiles.

Run:

```python
command = [
    python_executable,
    str(copied_script),
    str(generated_workspace_resolved),
]
```

Build environment from `os.environ.copy()`.

Set:

```python
env["PYTHONDONTWRITEBYTECODE"] = "1"
env["PYTHONPATH"] = (
    str(generated_workspace_resolved)
    + os.pathsep
    + env.get("PYTHONPATH", "")
)
```

The generated workspace must be the first Python path entry.

Use:

```python
subprocess.run(
    command,
    cwd=str(temp_directory),
    env=env,
    capture_output=True,
    text=True,
    timeout=timeout,
)
```

Do not use `shell=True`.

## 18. Exact evaluator JSON contract

The evaluator script prints exactly one JSON object to stdout:

```json
{
  "passed": true,
  "checks": ["check name 1", "check name 2"],
  "error": ""
}
```

The runner must parse `stdout.strip()` with one `json.loads` call. Extra non-whitespace stdout before or after JSON is malformed output and fails.

Require:

- top-level mapping;
- `passed` is bool;
- `checks` is a list;
- every check is a non-empty string;
- `error` is string;
- no required field is missing.

The final runner result passes only when:

```text
subprocess exit code == 0
AND parsed passed == True
AND parsed error == ""
```

A script may return JSON with `passed=False` and exit code 1. Preserve parsed checks and error, but the runner result is failed.

Non-zero exit with `passed=True` still fails.

Malformed JSON fails.

Timeout fails with `exit_code=-1`.

Missing script fails with `exit_code=-1`.

The runner may preserve full stdout/stderr in the typed result, but Runner persistence must later store only bounded failure excerpts.

## 19. Common evaluator-script structure

Each evaluator script is standalone. Do not create a fourth shared evaluator module because the approved contract calls for exactly three assets, and copying a hidden helper into the subprocess would complicate isolation.

Each script must:

1. accept exactly one workspace argument;
2. resolve the workspace;
3. verify `manage.py`, `config/settings.py`, and `todo/` exist;
4. prepend workspace to `sys.path`;
5. set `DJANGO_SETTINGS_MODULE=config.settings`;
6. set `PYTHONDONTWRITEBYTECODE=1`;
7. import Django only after path and environment setup;
8. call `django.setup()`;
9. use Django’s test runner database setup;
10. run migrations in the test database;
11. execute evaluator-owned checks;
12. tear down databases and test environment in `finally`;
13. print exactly one compact JSON object;
14. return 0 for passed and 1 for failed.

Recommended safe skeleton:

```python
def main() -> int:
    payload = {"passed": False, "checks": [], "error": ""}
    captured = io.StringIO()
    old_config = None
    runner = None

    try:
        workspace = validate_workspace_argument()
        sys.path.insert(0, str(workspace))
        os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
        os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

        with redirect_stdout(captured), redirect_stderr(captured):
            import django
            django.setup()

            from django.test.runner import DiscoverRunner
            runner = DiscoverRunner(verbosity=0, interactive=False)
            runner.setup_test_environment()
            old_config = runner.setup_databases()

            checks = execute_checks()
            payload = {"passed": True, "checks": checks, "error": ""}
    except Exception as exc:
        payload = {
            "passed": False,
            "checks": payload.get("checks", []),
            "error": f"{type(exc).__name__}: {exc}",
        }
    finally:
        if runner is not None and old_config is not None:
            with redirect_stdout(captured), redirect_stderr(captured):
                runner.teardown_databases(old_config)
                runner.teardown_test_environment()

    print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
    return 0 if payload["passed"] else 1
```

Do not print debug text to stdout. Captured Django output may be incorporated into the `error` field only when useful and bounded.

## 20. Smoke 001 evaluator requirements

The Smoke 001 evaluator checks the generated workspace for Task priority behavior.

It must verify at least:

### Model

- `Task.Priority` exists;
- it is based on Django `TextChoices`;
- stored values are exactly `HIGH`, `MEDIUM`, `LOW`;
- `Task` has a `priority` model field;
- the field default is `MEDIUM`;
- the field choices contain exactly the required values;
- creating a Task without priority stores `MEDIUM`;
- creating with `HIGH` stores `HIGH`;
- existing `title`, `description`, `status`, `project`, `tags`, `created_at`, and `updated_at` behavior works.

### Serializer

- `TaskSerializer` exposes `priority`;
- the field is writable;
- `HIGH`, `MEDIUM`, and `LOW` validate;
- `URGENT` is rejected;
- serializer output returns the stored priority;
- existing serializer fields remain usable.

### API

- authenticated list without a priority query returns tasks of multiple priorities;
- `GET /api/tasks/?priority=HIGH` returns only high-priority tasks;
- the response handles the configured paginator correctly;
- no priority query retains unfiltered behavior;
- Project and Tag creation and serialization remain functional.

Do not assume Project has an owner in Scenario 001. Create Project with baseline-compatible arguments only.

The checks list should use stable names such as:

```text
task_priority_enum
task_priority_default
task_serializer_priority
task_priority_invalid_rejected
task_priority_filter
task_unfiltered_list
baseline_task_fields
project_and_tag_regression
```

## 21. Smoke 002 evaluator requirements

The Smoke 002 evaluator checks soft deletion.

Use an authenticated API client. Create a Project, Tag, and Task with meaningful data. Attach the Tag. Then:

- DELETE the Task;
- require a successful delete status consistent with DRF destroy behavior;
- prove the row still exists through `Task._base_manager` or another manager that bypasses the filtered default manager;
- prove `deleted_at` is non-null;
- prove `Task.objects` excludes the deleted row;
- prove normal list excludes it;
- prove detail endpoint returns 404;
- prove `/api/tasks/deleted/` includes it and excludes active tasks;
- POST `/api/tasks/{id}/restore/`;
- prove `deleted_at` returns to null;
- prove the Task returns to normal list and detail;
- prove title, description, status, project, and tags are preserved;
- prove Project and Tag normal behavior remains functional.

The evaluator must not require a specific secondary-manager name. Using `_base_manager` avoids forcing `all_objects` or another implementation detail.

Stable check names:

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

## 22. Smoke 003 evaluator requirements

The Smoke 003 evaluator checks project-owner authorization.

Create at least:

- owner user;
- other authenticated user;
- staff user;
- API clients for each.

Verify:

### Project model and serializer

- `Project.owner` exists and is a ForeignKey to the user model;
- creating a Project through the API as the owner user sets `Project.owner` automatically;
- posting another user’s owner ID cannot override creator assignment;
- `ProjectSerializer` exposes owner read-only;
- authenticated reads remain available.

Do not enforce non-null database configuration beyond observable required behavior, because migration compatibility may require a nullable transition. The API-created Project must have a real owner.

### Project writes

- owner may update own Project;
- non-owner update returns 403;
- non-owner delete returns 403;
- owner may delete own Project;
- any authenticated user may create a Project.

### Task writes

- owner may create a Task inside own Project;
- another user may not create a Task inside the owner’s Project;
- project owner may update a Task even when the legacy `Task.owner` field points to someone else;
- non-project-owner update returns 403;
- non-project-owner delete returns 403;
- project owner delete succeeds;
- task authority derives from `Task.project.owner`, not `Task.owner`.

### Reads and Tag regression

- authenticated users can list and retrieve Projects;
- authenticated users can list and retrieve Tasks regardless of ownership;
- TagViewSet behavior remains baseline-compatible;
- an authenticated non-staff user can create a Tag as before;
- non-staff object update remains forbidden as before;
- staff object update remains allowed as before.

Stable check names:

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

## 23. Evaluator fixture integration tests

Create `tests/support/evaluator_fixture_workspaces.py`. This is test support only. It may copy the baseline Todo repository to temporary directories and write deterministic correct or incorrect source fixtures for each scenario.

Do not import test support from production code.

For each evaluator:

1. create a workspace representing a correct implementation;
2. execute the real evaluator runner;
3. require passed;
4. create one or more deliberately incorrect variants;
5. require failed for the correct reason category.

Required negative fixtures:

### Smoke 001

- wrong default priority;
- missing priority filter;
- serializer rejects valid HIGH or accepts URGENT.

### Smoke 002

- hard deletion;
- normal list includes deleted;
- restore does not clear timestamp.

### Smoke 003

- Task permission still uses `Task.owner`;
- non-owner Project update succeeds;
- serializer owner is writable.

The integration test may use deterministic source strings copied from a known-correct fixture. This proves evaluator correctness only. It is not the R5 scripted LLM backend.

## 24. R3C gate and commits

Run:

```powershell
python -m pytest tests/unit/execution/test_scenario_evaluator.py -q
python -m pytest tests/integration/test_todo_smoke_evaluator_assets.py -q
python -m pytest tests/unit/execution/test_scenario_evaluator.py tests/integration/test_todo_smoke_evaluator_assets.py -q
python -m pytest -q
ruff check src/benchmark/execution/scenario_evaluator.py src/benchmark/execution/__init__.py tests/unit/execution/test_scenario_evaluator.py tests/integration/test_todo_smoke_evaluator_assets.py tests/support/evaluator_fixture_workspaces.py tests/evaluator_assets
mypy --strict src/benchmark/execution/scenario_evaluator.py
python -m compileall src/benchmark/execution/scenario_evaluator.py tests/evaluator_assets
git diff --check
git diff --name-only
```

Code commit:

```powershell
git add src/benchmark/execution/scenario_evaluator.py src/benchmark/execution/__init__.py tests/evaluator_assets tests/unit/execution/test_scenario_evaluator.py tests/integration/test_todo_smoke_evaluator_assets.py tests/support/evaluator_fixture_workspaces.py
git commit -m "feat(validation): add isolated scenario evaluators"
```

Documentation commit:

```powershell
git add docs/PROJECT_HANDOFF.md reports/latest_phase_report.md docs/V2_R3B_TO_KAGGLE_NO_DISCRETION_EXECUTION_SPEC.md selective_updates/CHANGE_INDEX.md
git commit -m "docs(state): record R3C completion"
```

Stop for audit. Do not start R3D automatically.

---

# PHASE R3D — Production Runner validation wiring

## 25. R3D goal

R3D connects the already-tested migration and evaluator modules to every non-dry regeneration path:

- Monolithic normal flow;
- Selective normal flow;
- Monolithic/Selective repair flow;
- Repository Agent initial flow;
- Repository Agent revision flow.

No successful regeneration run may bypass migration generation, baseline tests, or scenario evaluation when the scenario requires them.

## 26. R3D authorized files

```text
src/benchmark/execution/runner.py
src/benchmark/execution/pipeline.py
src/benchmark/execution/validation.py
src/benchmark/core/models.py
src/benchmark/checkpoint/persistence.py
src/benchmark/statistics/reporting.py
seven_arm_benchmark.py
tests/unit/execution/test_runner.py
tests/unit/execution/test_pipeline.py
tests/unit/test_models.py
tests/unit/test_checkpoint.py
tests/unit/statistics/test_reporting.py
tests/contract/test_three_arm_core.py
tests/integration/test_scientific_smoke_v1_fixes.py
tests/integration/test_su0010a_regeneration.py
tests/integration/test_su0011_iterative_agent.py
new focused integration tests if necessary
docs/PROJECT_HANDOFF.md
reports/latest_phase_report.md
docs/V2_R3B_TO_KAGGLE_NO_DISCRETION_EXECUTION_SPEC.md
selective_updates/CHANGE_INDEX.md
```

Do not change evaluator semantics, Selective scope, Agent protocol, or scenario YAML.

## 27. Runner and Pipeline configuration

Add to `PipelineConfig` and `RunnerConfig`:

```python
canonical_project_root: str | Path | None = None
python_executable: str = sys.executable
```

Because a dataclass default must be evaluated safely, `python_executable` may default to `sys.executable` at module load or use a simple string field populated by Pipeline.

Pass both fields from Pipeline to Runner.

In `seven_arm_benchmark.py`, pass:

```python
canonical_project_root=Path(__file__).resolve().parent
python_executable=sys.executable
```

The canonical project root points to the directory containing `seven_arm_benchmark.py`, `tests`, and `src`.

Fail closed before generation when a non-dry V2 scenario has a non-empty evaluator asset but no valid canonical project root.

## 28. One shared validation sequence

Avoid duplicating three-stage validation logic in four Runner flows. Add one small private typed result and one private method in `runner.py`.

Equivalent structure:

```python
@dataclass(frozen=True)
class _ScientificValidationResult:
    migration: PostGenerationResult | None
    baseline: FunctionalValidationResult | None
    evaluator: ScenarioEvaluatorResult | None
    passed: bool
    feedback: str
    duration_seconds: float


def _execute_scientific_validation(
    self,
    scenario: Scenario,
) -> _ScientificValidationResult:
    ...
```

This private helper is not a new public framework. Its purpose is to force all arms and all repair paths through the same validation order.

## 29. Validation stage order

For every non-dry regeneration attempt:

### Stage 1 — source generation guard

Before migration:

- at least one backend generation call occurred;
- at least one source artifact has status `generated`;
- no successful record is allowed with zero generated source;
- path-rejected or empty generations are failures.

When generation has partial failures but at least one file was written, validation may still run to provide repair feedback, but final success remains impossible until an attempt has no executor failures.

### Stage 2 — migration generation

If `scenario.post_generation_command` is non-empty, call:

```python
run_post_generation_command(
    workspace_root=self._isolation.workspace.root,
    command=scenario.post_generation_command,
    require_new_migration=scenario.require_new_migration,
    timeout=self._config.validation_timeout,
)
```

If `require_new_migration=True` and the command is empty, fail as a harness defect.

If the migration stage fails, do not mark the run successful. Baseline and evaluator execution may be skipped for that attempt because the generated project cannot be trusted to have the required schema. Include migration stdout/stderr in repair feedback.

### Stage 3 — baseline validation

Run the configured baseline command in the generated workspace with `FunctionalValidator`.

This is the repository regression suite. For Todo the discovered command is based on `python -m pytest`; verbosity flags do not affect correctness. All arms use the same command.

Rename semantics in new code and records to `baseline_validation`. Retain `functional_validation_passed` only as a compatibility mirror equal to `baseline_validation_passed`.

If baseline validation fails, do not run the scenario evaluator for that attempt. Include bounded stdout/stderr in repair feedback.

### Stage 4 — isolated scenario evaluator

When `scenario.evaluator_asset` is non-empty, call:

```python
run_scenario_evaluator(
    canonical_project_root=self._config.canonical_project_root,
    evaluator_asset=scenario.evaluator_asset,
    generated_workspace=self._isolation.workspace.root,
    python_executable=self._config.python_executable,
    timeout=self._config.validation_timeout,
)
```

If the evaluator asset is empty for a V2 Smoke scenario, fail closed.

For legacy non-V2 tests or scenarios with empty evaluator metadata, scenario evaluation may remain not executed (`None`) unless the profile explicitly requires it.

### Stage 5 — success decision

A V2 regeneration attempt succeeds only when:

```text
executor failures are empty
regeneration model calls > 0
generated source count > 0
migration result passed == True
exactly one generated migration path exists
baseline result passed == True
scenario evaluator result passed == True
```

No old `validation_command=[python -c exit(0)]` unit fixture may accidentally establish scientific V2 success without scenario metadata. Such fixtures may continue testing generic compatibility paths, but new V2 contract tests must exercise all stages.

## 30. Failure stages

Use distinct `FailureRecord.stage` values:

```text
generation_guard
regeneration
migration_generation
baseline_validation
scenario_evaluator
configuration
budget
```

Use `FailureKind.harness_defect` for missing required metadata or invalid canonical configuration.

Use `FailureKind.build` for migration, baseline, or evaluator correctness failures unless a more specific existing enum is suitable.

Do not label evaluator failure as a model-backend transport error.

## 31. Repair feedback

Current repair feedback is built only from one functional validation result. Replace it with a bounded combined message from the first failed stage.

Maximum persisted or prompted feedback per stage:

```text
stdout: 1000 characters
stderr/error: 1000 characters
```

The repair prompt may say:

```text
Previous scientific validation failed.

Stage: migration_generation | baseline_validation | scenario_evaluator
Exit code: ...
Stdout:
...
Stderr or error:
...
```

Do not include evaluator source, exact evaluator code, Ground Truth paths, or hidden-test descriptions. Only include observed failure output that a normal developer would receive from executing validation.

For evaluator failure, include the evaluator’s public check names and error text, not the script source.

Repository Agent `revise_plan` may receive the same bounded validation feedback and workspace summary. It must retain the global eight-call selection cap.

## 32. RunRecord forwarding

`RunRecord` already contains several stage fields. Validate and forward all of them through the final `BenchmarkRunner.run()` reconstruction. The current wrapper drops some fields. The final record must preserve:

```text
selection_tool_calls
selection_tool_duration_seconds
selection_inspected_file_count
selection_tool_transcript

migration_generation_passed
migration_duration_seconds
generated_migration_paths

baseline_validation_passed
baseline_validation_duration_seconds

scenario_evaluator_passed
scenario_evaluator_duration_seconds
scenario_evaluator_checks

functional_validation_passed compatibility mirror
```

Add non-negative validation in `RunRecord.__post_init__` for migration, baseline, and evaluator durations.

## 33. Persistent RunRecordData

Extend `RunRecordData` with the same stage and Agent-tool fields:

```python
selection_tool_calls: int = 0
selection_tool_duration_seconds: float = 0.0
selection_inspected_file_count: int = 0
selection_tool_transcript: list[str] = field(default_factory=list)

migration_generation_passed: bool | None = None
migration_duration_seconds: float = 0.0
generated_migration_paths: list[str] = field(default_factory=list)

baseline_validation_passed: bool | None = None
baseline_validation_duration_seconds: float = 0.0

scenario_evaluator_passed: bool | None = None
scenario_evaluator_duration_seconds: float = 0.0
scenario_evaluator_checks: list[str] = field(default_factory=list)
```

Use JSON-compatible lists in persistence and tuples in immutable core models.

Update:

- `_run_single_scenario_strategy` record dictionary;
- `_to_run_record_data`;
- checkpoint load and idempotent equality;
- reporting serializers;
- final summaries.

Backward-compatible old JSONL records load through defaults.

## 34. R3D tests

Required production-path tests include:

1. Monolithic non-dry attempt executes migration, baseline, evaluator in order;
2. Selective non-dry attempt executes the same order;
3. Repository Agent non-dry attempt executes the same order;
4. migration failure prevents success;
5. missing required migration command fails before false success;
6. zero new migration fails;
7. two new migrations fail;
8. changed old migration fails;
9. baseline failure prevents evaluator execution;
10. evaluator failure prevents success;
11. evaluator pass cannot override baseline failure;
12. all stages pass and successful record has non-zero calls and generated source;
13. zero calls cannot be successful;
14. zero generated source cannot be successful;
15. final `run()` wrapper preserves every stage field;
16. persistent conversion preserves every field;
17. JSONL save/reload preserves every field;
18. old records missing new fields still load;
19. evaluator metadata never reaches strategy;
20. evaluator metadata never reaches generation prompt;
21. evaluator script never appears inside workspace;
22. snapshot remains unchanged;
23. repair after migration failure receives bounded public error;
24. repair after baseline failure receives bounded test output;
25. repair after evaluator failure receives checks/error but not evaluator source;
26. iterative Agent revision still obeys eight total selection calls;
27. generic legacy scenario with empty metadata retains compatibility behavior;
28. V2 Smoke scenario with missing evaluator metadata fails closed.

## 35. R3D gate and commits

Run all focused Runner, Pipeline, persistence, and three-arm contract tests, then:

```powershell
python -m pytest -q
ruff check src/benchmark/execution src/benchmark/core/models.py src/benchmark/checkpoint/persistence.py src/benchmark/statistics/reporting.py seven_arm_benchmark.py tests
mypy --strict src/benchmark/execution src/benchmark/core/models.py src/benchmark/checkpoint/persistence.py src/benchmark/statistics/reporting.py
python -m compileall src/benchmark/execution src/benchmark/core/models.py src/benchmark/checkpoint/persistence.py src/benchmark/statistics/reporting.py seven_arm_benchmark.py
git diff --check
```

Code commit:

```powershell
git add src/benchmark/execution src/benchmark/core/models.py src/benchmark/checkpoint/persistence.py src/benchmark/statistics/reporting.py seven_arm_benchmark.py tests
git commit -m "feat(validation): wire migrations and evaluators into Runner"
```

Documentation commit:

```powershell
git add docs/PROJECT_HANDOFF.md reports/latest_phase_report.md docs/V2_R3B_TO_KAGGLE_NO_DISCRETION_EXECUTION_SPEC.md selective_updates/CHANGE_INDEX.md
git commit -m "docs(state): record R3D completion"
```

Stop for audit.

---

# PHASE R4 — Token semantics and truthful stage metrics

## 36. R4 goal

R4 separates:

```text
maximum completion tokens per backend call
```

from:

```text
optional maximum total workflow tokens
```

The value `4096` is the completion limit supplied independently to every normal backend call. It is not the total token allowance for an entire run.

## 37. Configuration names

The authoritative fields are:

```python
max_completion_tokens_per_call: int = 4096
max_total_workflow_tokens: int = 0
```

`0` for total workflow means unlimited.

Legacy:

```python
max_tokens
max_tokens_per_run
```

may remain only as deprecated compatibility aliases for old non-V2 tests. The V2 profile and canonical CLI must use explicit names.

Add CLI arguments:

```text
--max-completion-tokens-per-call
--max-total-workflow-tokens
```

Defaults:

```text
4096
0
```

Keep `--max-tokens` hidden or deprecated only if existing tests require it. When both new and legacy fields are provided, fail with a clear configuration error rather than guessing precedence.

Include the new fields in config hash and source identity.

## 38. BudgetManager construction

Construct the total-workflow budget with:

```python
BudgetManager(
    max_attempts=config.max_attempts,
    max_tokens=config.max_total_workflow_tokens,
    timeout_seconds=config.timeout_seconds,
)
```

Do not pass `max_completion_tokens_per_call` into `BudgetManager`.

Attempts, elapsed timeout, and optional total tokens remain independent dimensions.

## 39. SharedRegenerationExecutor API

Replace ambiguous:

```python
max_tokens
```

with:

```python
def execute(
    self,
    plan: RegenerationPlan,
    isolation: IsolationContext,
    requirement_delta: str = "",
    repair_context: str | None = None,
    *,
    max_completion_tokens_per_call: int = 4096,
    remaining_total_workflow_tokens: int = 0,
) -> RegenerationExecutionResult:
```

Validate:

- per-call completion limit is positive;
- remaining total is non-negative.

For every backend generation call, the normal `max_tokens` argument equals `max_completion_tokens_per_call`.

Do not subtract prompt-token estimates from the per-call completion limit.

When total workflow is unlimited, every call gets 4096.

When an optional positive total ceiling exists, stop before a call only when the known consumed workflow tokens already meet or exceed the ceiling. If remaining total is smaller than the per-call completion limit, the backend call may receive the smaller positive value as a safety ceiling. Document this as exceptional total-budget truncation.

Do not treat prompt and completion as sharing one API output limit.

## 40. Agent backend calls

Repository Agent selection calls use the same per-call completion limit.

The eight-call cap remains independent.

Selection token usage must be incremental. A strategy revision must expose only the tokens added by that revision through the returned prediction or a separate delta property. Runner must not add cumulative totals more than once.

## 41. Repair metrics

Add explicit repair fields to `RunRecord` and `RunRecordData`:

```python
repair_prompt_tokens: int = 0
repair_completion_tokens: int = 0
repair_total_tokens: int = 0
repair_model_calls: int = 0
repair_duration_seconds: float = 0.0
```

The initial generation attempt belongs to regeneration metrics.

Any later generation call containing validation repair context belongs to repair metrics, even when it rewrites the same selected files.

For the Repository Agent:

- selection revision calls remain selection;
- code-writing calls after failure remain repair;
- repository tools remain selection-tool metrics.

## 42. Required arithmetic

For every record:

```text
selection_total_tokens
= selection_prompt_tokens + selection_completion_tokens

regeneration_total_tokens
= regeneration_prompt_tokens + regeneration_completion_tokens

repair_total_tokens
= repair_prompt_tokens + repair_completion_tokens

total_workflow_tokens
= selection_total_tokens
+ regeneration_total_tokens
+ repair_total_tokens

total_workflow_model_calls
= selection_model_calls
+ regeneration_model_calls
+ repair_model_calls
```

Validation stages do not use LLM tokens, but their durations are included.

```text
total_workflow_duration_seconds
= selection_duration_seconds
+ regeneration_duration_seconds
+ repair_duration_seconds
+ migration_duration_seconds
+ baseline_validation_duration_seconds
+ scenario_evaluator_duration_seconds
```

Tool duration is already part of selection wall time. Do not add it again if selection duration surrounds tool execution. Persist tool duration as a submetric without double-counting it in the total.

## 43. Token count trust

For real Qwen:

- prompt and completion counts come from the model tokenizer;
- backend response `TokenUsage` is authoritative;
- if real backend token counting is unavailable, fail before scientific generation.

The `len(text)//4` fallback is allowed only in mock or scripted engineering tests. Label approximate token accounting in model metadata or record metadata. Do not mix approximate engineering values with real Qwen publication values.

## 44. R4 tests

Test:

- 4096 reaches every normal generation call;
- three selected files produce three calls, each with 4096;
- previous calls do not reduce later per-call limits when total is unlimited;
- optional total ceiling can stop or reduce a later call;
- prompt estimate is not subtracted from normal completion limit;
- Agent selection receives the same limit;
- invalid zero/negative per-call limit fails;
- negative total ceiling fails;
- stage arithmetic identities hold;
- repair calls are separated;
- cumulative Agent token usage is not double counted;
- tool duration is not double-counted;
- migration, baseline, and evaluator durations are included once;
- persistence round-trip preserves all fields;
- reports aggregate the new fields;
- config hash changes when either token setting changes;
- real backend without tokenizer fails;
- scripted/mock fallback is marked approximate.

Commit code, then docs, then stop for audit.

**R4 completion status (2026-07-31):** implemented on `experiment/three-arm-smoke-v2`, code commit `e87d4ad`. Full suite 1576 passed / 32 skipped / 0 failed; R4 unit 66, R4 integration 31, R3D-adjacent 177, evaluator integrity 50 + 1 pre-existing skip; direct scripts A/B/C1/C2/D acceptance met; 0 new ruff/mypy errors vs HEAD baseline. R4 is NOT accepted and NOT frozen; independent audit required before R5.

---

# PHASE R5 — Nine non-dry scripted production records

## 45. R5 purpose

R5 is the decisive local engineering proof. It does not evaluate Qwen quality. It proves the complete harness can execute the scientific matrix without dry-run bypasses.

The matrix is:

```text
3 scenarios × 3 arms × 1 repetition = 9 records
```

## 46. R5 exact files

Create:

```text
tests/support/scripted_llm_backend.py
tests/support/scripted_smoke_v2.py
tests/integration/test_scientific_smoke_v2_production_path.py
```

Modify production files only when a production-path test exposes a genuine defect. Such fixes require their own focused code commit before the final R5 test commit.

## 47. Scripted backend restrictions

The scripted backend may inspect prompts only to identify:

- public scenario requirement;
- requested artifact path;
- Agent tool action stage.

It may return deterministic complete source files for the controlled Todo scenarios.

It must not:

- choose Selective paths;
- choose Monolithic paths;
- alter the dependency graph;
- read expected affected artifacts;
- read evaluator scripts;
- import production strategy internals;
- enter the real backend factory;
- appear in Kaggle provider choices.

Production source must not import from `tests.support`.

## 48. Deterministic fixture implementations

The scripted backend needs correct complete content for:

- Scenario 001 models, serializers, views;
- Scenario 002 models, views;
- Scenario 003 models, serializers, permissions, views.

For a requested selected file, return the correct complete file. For Monolithic files that are not required by the scenario, return their exact baseline content so they remain byte-identical despite a model call. This is acceptable because R5 proves orchestration, not model creativity.

For Agent selection prompts, return bounded tool actions followed by final paths. Tool behavior must be real. The backend may use a deterministic sequence per public requirement:

```text
list_files
search_text
read_file
final
```

Do not exceed eight selection calls.

## 49. Fresh workspace per record

Every cell must:

1. stage or reuse one immutable baseline snapshot;
2. calculate snapshot hash before the run;
3. create a fresh generated workspace copied from that snapshot;
4. construct a fresh strategy instance;
5. construct a fresh backend instance or reset its per-run state;
6. run non-dry with regeneration enabled;
7. persist the record;
8. calculate snapshot hash after the run;
9. inspect workspace differences;
10. delete only temporary test workspaces after assertions.

Never reuse a modified workspace between cells.

## 50. Real production classes

The test must use:

- real `ScenarioLoader`;
- real repository manifest/profile loader;
- real ArtifactUniverse resolver;
- real dependency graph;
- real `make_strategy`;
- real `BenchmarkPipeline`;
- real `BenchmarkRunner`;
- real `SharedRegenerationExecutor`;
- real post-generation runner;
- real baseline test command;
- real scenario evaluator runner;
- real `RunRecordData` conversion;
- real `RunRecordStore`.

Do not manually call strategies and then synthesize success records.

## 51. Per-record assertions

Every succeeded record must have:

```text
status == succeeded
dry_run == False
total_workflow_model_calls > 0
regeneration_model_calls > 0
total_workflow_tokens > 0
regenerated_artifact_count > 0
migration_generation_passed == True
len(generated_migration_paths) == 1
baseline_validation_passed == True
scenario_evaluator_passed == True
functional_validation_passed == True
failures is empty
```

Also assert arithmetic identities and non-negative durations.

## 52. Isolation assertions

For every record:

- workspace path differs from snapshot;
- snapshot content hash before equals after;
- old migration hashes remain unchanged;
- exactly one new workspace migration exists;
- baseline tests are unchanged;
- evaluator assets are not in workspace;
- configuration files are unchanged;
- database and cache files are not selected;
- only allowed source files and the new migration differ;
- no file outside workspace is modified.

## 53. Arm assertions

### Monolithic

- selects exactly five editable source files;
- sends generation calls for all five;
- preserved count is zero;
- unrelated source may remain byte-identical when scripted backend returns baseline.

### Selective

- Scenario 001 selects exactly three accepted files;
- Scenario 002 selects exactly two;
- Scenario 003 selects exactly four;
- selected scope is a strict subset of five;
- no Ground Truth access occurs.

### Repository Agent

- selection model calls are between one and eight;
- tool calls are non-zero;
- inspected file count is non-zero and at most thirty;
- selected paths are non-empty subset of five;
- Agent reads active workspace;
- evaluator source is never returned by tools;
- complete selection call count never exceeds eight, including revision.

## 54. Persistence assertions

Persist all nine records to temporary JSONL.

Reload and assert:

- exactly nine records;
- unique canonical run IDs;
- three scenario IDs;
- three strategy IDs;
- one repetition;
- identity and status match in-memory records;
- stage metrics match;
- migration paths match;
- evaluator checks match;
- Agent tool metrics match;
- failures would be preserved if present;
- re-appending identical record is idempotent;
- conflicting same run ID raises integrity error.

## 55. Negative controls

The R5 test suite must deliberately prove it fails when:

- `dry_run=True`;
- regeneration disabled;
- backend returns no generation calls;
- backend returns empty source;
- strategy returns no selected artifacts;
- migration command creates no migration;
- baseline command is replaced with `exit(0)` while evaluator is absent;
- evaluator is skipped;
- snapshot is mutated;
- persisted metrics are zeroed.

These may be separate focused tests and do not need to run all nine cells for every negative condition.

## 56. R5 evidence table

After the nine-record test, print or construct a table with:

```text
scenario
arm
status
selection calls
tool calls
regeneration calls
repair calls
total calls
selection tokens
regeneration tokens
repair tokens
total tokens
selected count
generated count
migration path
baseline pass
evaluator pass
snapshot unchanged
```

Do not claim that the token magnitudes predict real Qwen costs. They are scripted engineering metrics.

## 57. R5 gate

Run the single nine-record integration test, focused persistence tests, full suite, Ruff, mypy, compileall, and diff check.

Create:

```powershell
git commit -m "test(smoke): prove nine scripted production records"
```

Update handoff and report:

```text
Local production-path proof: complete
Real Qwen Smoke: pending and not yet run
Kaggle authorization: pending independent R5 audit
Pilot: blocked
Stable tag: blocked
```

Stop for independent audit.

---

# PHASE R6 — Final documentation, bundle, parity, and push

## 58. R6 purpose

R6 prepares an auditable deployable branch after R5 is independently accepted. R6 does not launch Kaggle.

## 59. Documentation

Update:

```text
README.md
docs/MASTER_IMPLEMENTATION_PLAN.md
docs/PROJECT_HANDOFF.md
reports/latest_phase_report.md
selective_updates/records/THREE-ARM-CORE-EXPERIMENT.md
selective_updates/CHANGE_INDEX.md
selective_updates/metrics/change_metrics.jsonl
docs/V2_R3B_TO_KAGGLE_NO_DISCRETION_EXECUTION_SPEC.md
```

State only local evidence:

```text
LOCAL_PRODUCTION_PATH_VALIDATED
REAL_QWEN_SMOKE_NOT_RUN
KAGGLE_AUTHORIZATION_PENDING_OR_APPROVED_BY_AUDIT
PILOT_BLOCKED
STABLE_TAG_BLOCKED
```

README should explain the three arms and the real command without claiming results.

## 60. Bundle rules

Run only:

```powershell
python scripts/build_upload_bundle.py
```

Do not manually edit:

```text
kaggle_upload/
notebooks/seven_arm_benchmark.ipynb
```

Inspect canonical/generated parity for every changed production file.

Require:

- same source content;
- same scenario YAML;
- same evaluator assets if the bundle needs them;
- same CLI;
- same protocol version;
- no local absolute paths;
- no secrets;
- no scripted test backend;
- no test fixture implementations.

## 61. Final local gate

Run in order:

```powershell
python -m pytest -q

Push-Location benchmark_data/repositories/todo
python -m pytest -q
python manage.py check
Pop-Location

ruff check src tests seven_arm_benchmark.py scripts
mypy --strict src/benchmark
python -m compileall src/benchmark seven_arm_benchmark.py
python scripts/build_upload_bundle.py
git diff --check
python -m pytest tests/integration/test_scientific_smoke_v2_production_path.py -q
git status --short
```

Run the nine-record proof after bundle generation to ensure the build process did not break canonical execution.

## 62. Push policy

After all gates and an independent R6 audit:

```powershell
git push -u origin experiment/three-arm-smoke-v2
git rev-parse HEAD
git rev-parse origin/experiment/three-arm-smoke-v2
git status --short
```

Require local and remote equality and clean tree.

Do not merge.

Do not tag.

Do not launch Kaggle automatically.

---

# KAGGLE PHASE K1 — Researcher-controlled real Smoke

## 63. Authorization prerequisites

The researcher may launch Kaggle only when an independent audit confirms:

- R1 through R6 complete;
- nine scripted records pass;
- branch pushed;
- local/remote equal;
- bundle parity passes;
- working tree clean;
- Ground Truth and evaluator isolation approved;
- Qwen tokenizer accounting available;
- experiment profile contains exactly three scenarios and three arms.

## 64. Real matrix

Run exactly:

```text
todo-smoke-001 × monolithic
todo-smoke-001 × selective
todo-smoke-001 × iterative_repository_agent

todo-smoke-002 × monolithic
todo-smoke-002 × selective
todo-smoke-002 × iterative_repository_agent

todo-smoke-003 × monolithic
todo-smoke-003 × selective
todo-smoke-003 × iterative_repository_agent
```

One repetition initially.

Every cell starts from the same pinned Todo baseline.

## 65. Real model configuration

```text
Model: Qwen2.5-Coder-7B-Instruct
Temperature: 0.0
max_completion_tokens_per_call: 4096
max_total_workflow_tokens: 0 unless a separately documented safety ceiling is approved
```

Do not use OpenRouter.

Do not use a different model for one arm.

Do not change prompts between arms except scope-acquisition-specific content.

## 66. Real-result handling

Persist every result, including failure.

Do not tune Selective or Agent after seeing results.

Do not silently rerun failed model-output cells.

Environmental resumable failures follow the documented checkpoint policy.

After completion, preserve:

- source commit;
- deployed build ID;
- model identity;
- tokenizer identity;
- Kaggle hardware;
- configuration hash;
- nine JSONL records;
- logs;
- generated workspaces or bounded diffs;
- evaluator results;
- migration paths;
- snapshot integrity evidence.

---

# KAGGLE PHASE K2 — Independent result audit and tag decision

## 67. Audit questions

The audit must answer:

1. Did all nine planned cells produce records?
2. Did every cell use the same model and settings?
3. Did every change start from the same baseline?
4. Did all code edits use `SharedRegenerationExecutor`?
5. Did any arm see Ground Truth?
6. Did any arm see evaluator source?
7. Are token arithmetic identities correct?
8. Are model-call totals correct?
9. Are duration totals correct?
10. Did every success create exactly one migration?
11. Did baseline tests pass for every success?
12. Did scenario evaluators pass for every success?
13. Were old migrations and snapshot preserved?
14. Did Selective remain frozen?
15. Did Agent remain within eight calls and thirty files?
16. Does deployed bundle equal pushed source?
17. Were failures preserved honestly?
18. Is the evidence sufficient for a stable Smoke tag?

## 68. Stable tag decision

Only after approval:

```powershell
git tag -a v2.0.0-scientific-smoke -m "Scientific Smoke V2: 3 changes x 3 arms, real Qwen execution audited"
git push origin v2.0.0-scientific-smoke
```

Do not create the tag based only on local scripted records.

---

# PILOT PHASE P1 — Later work, explicitly blocked now

## 69. Pilot minimum

Pilot begins only after the stable Smoke tag exists.

Minimum:

```text
7 to 12 independent changes
3 or more real repositories
every repository at least 5,000 LOC
permissive license
exact pinned commit
reproducible passing baseline tests
same proposed Selective and Repository Agent arms
```

The Pilot must test generalization. Do not tune profile triggers to exact expected files after seeing Ground Truth. Repository metadata may be prepared from public source before execution, then frozen.

---

# APPENDIX A — Exact status vocabulary

Use:

```text
COMPLETE_STATICALLY
LOCAL_ENGINEERING_VALIDATED
LOCAL_PRODUCTION_PATH_VALIDATED
REAL_QWEN_SMOKE_NOT_RUN
VALIDATED_ON_KAGGLE
REQUIRES_KAGGLE
BLOCKED
REQUIRES_RESEARCHER_APPROVAL
```

Do not use “ready” without naming what it is ready for.

Examples:

```text
R3B migration module is LOCAL_ENGINEERING_VALIDATED.
V2 is not yet LOCAL_PRODUCTION_PATH_VALIDATED.
Real Qwen Smoke is REQUIRES_KAGGLE.
Pilot is BLOCKED.
Stable tag is BLOCKED.
```

---

# APPENDIX B — Phase stop markers

R3B:

```text
R3B_MIGRATION_RUNNER_COMPLETE_AUDIT_REQUIRED
```

R3C:

```text
R3C_ISOLATED_EVALUATORS_COMPLETE_AUDIT_REQUIRED
```

R3D:

```text
R3D_PRODUCTION_VALIDATION_WIRING_COMPLETE_AUDIT_REQUIRED
```

R4:

```text
R4_TOKEN_AND_METRIC_CONTRACT_COMPLETE_AUDIT_REQUIRED
```

R5:

```text
V2_LOCAL_PRODUCTION_PROOF_PASSED_KAGGLE_AUDIT_REQUIRED
```

R6:

```text
V2_BRANCH_PUSHED_KAGGLE_LAUNCH_REQUIRES_RESEARCHER
```

OpenCode must stop after the marker for the authorized phase.

---

# APPENDIX C — Forbidden implementation choices

OpenCode must not:

- create another branch;
- merge;
- tag early;
- launch Kaggle automatically;
- use OpenRouter;
- call a real model locally;
- add a new agent framework;
- add embeddings or a vector database;
- add scenario-ID branches to production strategies;
- read Ground Truth during selection;
- copy evaluator source into the workspace;
- expose evaluator text in prompts;
- let the LLM edit tests;
- let the LLM edit existing migrations;
- hand-write migration SQL;
- manually edit generated Kaggle mirrors;
- treat `--dry-run` as execution proof;
- treat a green old test suite as proof of a new untested contract;
- accept zero generation calls as success;
- accept zero generated source as success;
- accept missing evaluator execution as success;
- hide failed real runs;
- tune Selective after results;
- combine R3B through R6 in one uncontrolled task;
- introduce a broad abstraction when one typed function is sufficient.

---

# APPENDIX D — Required report after each phase

OpenCode’s phase report must contain:

1. branch;
2. starting HEAD;
3. ending code-checkpoint hash;
4. ending documentation-checkpoint hash;
5. exact changed files;
6. exact new public APIs;
7. focused tests and counts;
8. full suite and counts;
9. Ruff;
10. mypy;
11. compileall;
12. `git diff --check`;
13. working-tree status;
14. current phase status;
15. exact next phase;
16. Kaggle status;
17. Pilot status;
18. stable-tag status;
19. any known limitation;
20. the exact phase stop marker.

Do not ask “shall I continue?” after a phase. Stop and wait for the researcher’s independent audit.

---

# APPENDIX E — Researcher workflow

The researcher should use this document as follows:

```text
1. Put this file in project/docs/.
2. Confirm the file exists.
3. Send OpenCode a short prompt authorizing R3B only.
4. Let OpenCode complete R3B and stop.
5. Export a fresh ZIP.
6. Request an independent audit.
7. If accepted, send a new short prompt authorizing R3C only.
8. Repeat through R6.
9. Launch Kaggle only after explicit authorization.
10. Create the stable tag only after real-result audit.
```

The goal is fast progress without hidden architectural drift. The detailed plan is written once. Each OpenCode task is small, literal, testable, and independently auditable.

---

**End of authoritative continuation contract.**

## APPENDIX F — R3B detailed review checklist
### 1. Verify the function never writes outside the generated workspace.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 2. Verify existing migration hashes include __init__.py.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 3. Verify numbered migration counts exclude __init__.py.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 4. Verify the subprocess command is passed as a list and shell=False.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 5. Verify timeout and FileNotFoundError become typed failure results.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 6. Verify repository-relative paths use forward slashes on Windows.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 7. Verify no missing migration directory is silently created.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 8. Verify a zero exit code is not enough when the required migration count is wrong.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 9. Verify an old migration deletion is detected.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 10. Verify a changed old migration is detected even when the command fails.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 11. Verify all output lists are sorted.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 12. Verify unit tests use temporary directories and do not alter the embedded Todo baseline.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.


## APPENDIX F — R3C detailed review checklist
### 1. Verify the parent benchmark module never imports Django from the generated workspace.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 2. Verify the evaluator asset must be below tests/evaluator_assets.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 3. Verify evaluator traversal and absolute paths fail before subprocess launch.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 4. Verify only one evaluator file is copied.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 5. Verify temporary evaluator directory is outside the workspace.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 6. Verify the workspace is first in PYTHONPATH.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 7. Verify evaluator stdout contains exactly one JSON object.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 8. Verify non-zero exit cannot be overridden by passed=true.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 9. Verify passed=false cannot be overridden by exit zero.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 10. Verify malformed checks values fail closed.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 11. Verify each evaluator uses a Django test database and tears it down.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 12. Verify evaluator assets are not collected by ordinary pytest discovery.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 13. Verify correct fixture workspaces pass and deliberately wrong fixtures fail.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.


## APPENDIX F — R3D detailed review checklist
### 1. Verify normal Monolithic and Selective flows call one shared validation helper.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 2. Verify Repository Agent initial and revision flows call the same helper.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 3. Verify required migration metadata is checked before false success.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 4. Verify baseline validation runs only in the generated workspace.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 5. Verify evaluator runs only after baseline passes.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 6. Verify compatibility functional_validation_passed mirrors baseline only.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 7. Verify final RunRecord reconstruction forwards every field.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 8. Verify persistent RunRecordData forwards every field.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 9. Verify evaluator source and hidden tests never enter repair context.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 10. Verify success requires non-zero calls and generated source.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 11. Verify snapshot remains immutable across repair attempts.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 12. Verify missing canonical project root fails closed for V2 evaluator execution.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.


## APPENDIX F — R4 detailed review checklist
### 1. Verify 4096 is passed to each normal backend call independently.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 2. Verify max_total_workflow_tokens=0 does not reduce later calls.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 3. Verify BudgetManager uses only the total-workflow ceiling.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 4. Verify prompt estimates are not subtracted from the completion limit.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 5. Verify repair metrics are separate from initial regeneration.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 6. Verify selection revisions are not double counted.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 7. Verify tool time is not double added to total duration.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 8. Verify config hash contains both new token settings.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 9. Verify real Qwen token counts come from the tokenizer.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 10. Verify approximate counts are labelled engineering-only.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 11. Verify JSONL persistence and reporting include repair and validation metrics.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.


## APPENDIX F — R5 detailed review checklist
### 1. Verify exactly nine records are written.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 2. Verify each record is non-dry.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 3. Verify every record has a fresh workspace.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 4. Verify every record starts from the same snapshot.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 5. Verify the snapshot hash remains unchanged.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 6. Verify every success has exactly one new migration.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 7. Verify every success passes baseline and evaluator stages.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 8. Verify all source writes use SharedRegenerationExecutor.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 9. Verify Selective scopes equal the frozen pre-experiment scopes.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 10. Verify Agent calls and tools remain within bounds.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 11. Verify evaluator assets never appear in prompts or workspace.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 12. Verify persistence reload exactly matches in-memory stage metrics.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 13. Verify negative controls fail when stages are bypassed.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.


## APPENDIX F — R6 detailed review checklist
### 1. Verify README claims only local scripted proof.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 2. Verify MASTER_IMPLEMENTATION_PLAN names real Kaggle as pending.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 3. Verify PROJECT_HANDOFF contains exact commands and current commits.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 4. Verify bundle was generated, not manually edited.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 5. Verify no scripted backend enters Kaggle upload.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 6. Verify canonical and generated production files match.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 7. Verify full project tests and controlled Todo tests pass.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 8. Verify Django manage.py check passes.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 9. Verify Ruff, mypy, compileall, and diff check pass.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 10. Verify the nine-record test passes after bundle generation.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 11. Verify local and remote HEAD are equal after push.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.
### 12. Verify no tag or merge occurred.

OpenCode must demonstrate this item with a test, a direct source inspection, or a command result. A summary statement without evidence is not sufficient. When the item concerns a negative boundary, the test must deliberately attempt the forbidden or invalid behavior and prove that execution fails closed. When the item concerns a metric, the test must assert the exact numeric identity rather than merely checking that a field exists. When the item concerns path isolation, the test must compare resolved paths and must work on Windows as well as POSIX. The phase report must state where the evidence lives so a new model or researcher can reproduce it without relying on conversation memory.


## APPENDIX G — Code-review matrix for independent auditors

The auditor should review the implementation at three levels.

### G.1 Literal contract level

Check exact names, paths, flags, field types, and commands. Typical failures at this level include:

- a generic evaluator path instead of one file per scenario;
- omitting `--noinput`;
- accepting a tuple where YAML must supply a list;
- coercing a number to a string instead of rejecting it;
- using a future commit hash inside the same commit;
- recording a clean tree while untracked files exist.

A full suite can remain green while these mistakes exist because old tests may not assert the new contract. Therefore literal assertions are mandatory.

### G.2 Production-connection level

Check that new modules are actually invoked by the canonical non-dry path. A correct `PostGenerationResult` class that no Runner calls is incomplete. A correct evaluator script that is never executed is incomplete. A correctly populated `RunRecord` that is dropped during serialization is incomplete.

For each stage, trace:

```text
scenario YAML
→ ScenarioModel
→ core Scenario
→ PipelineConfig / RunnerConfig
→ BenchmarkRunner
→ stage module
→ core RunRecord
→ record dictionary
→ RunRecordData
→ JSONL
→ report
```

Any missing arrow is a production-path defect.

### G.3 Scientific-validity level

Check that implementation does not change the experiment question.

Questions:

- Did one arm receive more validation information?
- Did one arm write code through a different executor?
- Did Selective see expected files?
- Did Agent see evaluator source?
- Did Monolithic receive tests?
- Did one arm get a larger per-call token limit?
- Did repair budgets differ?
- Did one scenario start from a modified prior scenario?
- Were failures removed?
- Was the algorithm changed after results?

A technically green implementation with any of these asymmetries is scientifically invalid.

## APPENDIX H — Failure decision matrix

### H.1 Source generation failure

Examples:

- backend exception;
- empty output;
- Markdown-fenced output;
- traversal path;
- zero generated files.

Action:

- mark attempt failed;
- preserve failure;
- run later validation only when useful feedback can be produced from partial generated state;
- never mark success;
- use bounded repair only while attempt and token budgets remain.

### H.2 Migration failure

Examples:

- `makemigrations` non-zero;
- no required migration;
- two new migrations;
- old migration changed;
- migration timeout.

Action:

- mark `migration_generation_passed=False`;
- do not run baseline or evaluator for that attempt;
- provide bounded command output to repair;
- preserve old-migration integrity result.

### H.3 Baseline failure

Action:

- mark `baseline_validation_passed=False`;
- do not run evaluator;
- include bounded pytest output in repair;
- preserve migration evidence.

### H.4 Evaluator failure

Action:

- mark `scenario_evaluator_passed=False`;
- include check names and error in repair;
- never include evaluator source;
- preserve baseline and migration pass evidence.

### H.5 Budget exhaustion

Action:

- stop additional model calls;
- record timeout or failed state according to existing policy;
- do not fabricate zero-token success;
- preserve metrics consumed before exhaustion.

### H.6 Harness configuration failure

Examples:

- missing evaluator root;
- missing required command;
- invalid editable policy;
- missing workspace.

Action:

- fail before or during the earliest safe stage;
- classify as harness or infrastructure defect;
- do not attribute it to the model;
- do not create a scientific success record.

## APPENDIX I — Definition of “near completion”

The project is not “almost done” merely because most source-selection work is complete. Completion has layers:

```text
Layer 1: scope contracts
Layer 2: safe code writing
Layer 3: deterministic migrations
Layer 4: baseline regression
Layer 5: scenario correctness
Layer 6: truthful metrics
Layer 7: persisted nine-cell local proof
Layer 8: deployable bundle
Layer 9: real Qwen execution
Layer 10: independent result audit and stable tag
```

At the current audited state, Layers 1 and 2 are substantially complete and R3A metadata is complete. Layers 3 through 8 remain engineering work. Layers 9 and 10 remain scientific execution and audit. This wording prevents optimism from being confused with evidence.

