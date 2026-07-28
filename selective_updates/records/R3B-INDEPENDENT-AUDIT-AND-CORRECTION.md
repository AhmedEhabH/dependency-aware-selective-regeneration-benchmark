# R3B Independent Audit and Correction Specification

**Status:** Mandatory correction before R3C  
**Target branch:** `experiment/three-arm-smoke-v2`  
**Audited documentation HEAD:** `0b08fc3`  
**Audited R3B code checkpoint:** `c11f25e`  
**Independent audit model:** GPT-5.6 Thinking  
**OpenCode implementation model:** DeepSeek V4 Flash Free through OpenCode Zen, Build mode  
**Kaggle:** blocked  
**Pilot:** blocked  
**Stable tag:** blocked  
**Next permitted work:** correct R3B only  

---

## 1. Audit conclusion

R3B is close, but it is not accepted yet.

The public API, focused unit suite, documentation split, commit structure, and most of the intended behavior are present. The supplied project suite is green with `1237 passed, 10 skipped`, and the independent environment also executed the 32 R3B tests successfully.

However, an independent source review and direct adversarial execution exposed four production defects that the current test suite does not catch:

1. a relative `workspace_root` can raise an uncaught `ValueError`;
2. path containment uses unsafe string-prefix comparison;
3. a non-numbered Python file such as `helper.py` is incorrectly accepted as the required new migration;
4. timeout and operating-system exception paths return before performing the required after-state migration integrity inspection.

There are also two smaller fail-closed gaps:

5. a plain string is accepted as `Sequence[str]` and is split into characters;
6. whitespace-only command items are accepted.

These are not theoretical style issues. They directly affect the scientific guarantee that the migration runner executes only inside the generated workspace, identifies a genuine numbered Django migration, preserves every old migration, and always returns typed evidence instead of leaking exceptions.

R3C must not begin until these defects are corrected, covered by persistent tests, and independently audited.

---

## 2. What OpenCode implemented correctly

The following work should be preserved:

- `PostGenerationResult` exists as a frozen dataclass.
- `run_post_generation_command` exists with the approved public name.
- commands are executed with a list and without `shell=True`;
- subprocess execution uses the generated workspace as `cwd`;
- existing direct Python files under the migration directory are hashed;
- `__init__.py` is included in old-file integrity checks;
- `__init__.py` is excluded from the created migration count;
- zero and multiple created files fail when one is required;
- old migration modification and deletion are detected on ordinary completed commands;
- output paths are repository-relative POSIX strings in the tested absolute-workspace case;
- the code and documentation were committed separately;
- Runner, Pipeline, scenario YAML, evaluators, Selective, Agent, README, generated bundle, and notebooks were not modified;
- the working tree is clean;
- documentation records R3C as the next phase and keeps Kaggle, Pilot, and stable tagging blocked.

This correction must be narrow. Do not rewrite the module into a general execution framework. Do not add external dependencies. Do not start evaluator work.

---

## 3. Reproduced defect A — relative workspace raises an exception

### 3.1 Current behavior

The function validates:

```python
wr = Path(workspace_root)
```

but later passes the unresolved path into `_snapshot_migrations`.

Inside `_snapshot_migrations`, the migration directory is resolved to an absolute path:

```python
mig_dir = (workspace_root / migration_directory).resolve()
```

Each file is then converted to a relative path using:

```python
entry.relative_to(workspace_root)
```

When `workspace_root` is relative, `entry` is absolute but `workspace_root` is still relative. `Path.relative_to` raises:

```text
ValueError: '<absolute migration path>' is not in the subpath of '<relative workspace>'
```

The independent audit reproduced this with a real temporary relative workspace.

### 3.2 Why it matters

The public function accepts `str | Path`. It does not state that paths must already be absolute. A production helper should either reject relative paths explicitly or normalize them safely. The intended design is to accept a valid workspace and return a typed result, not leak a raw exception.

R3D may receive workspace paths constructed by another subsystem. Assuming absolute paths without enforcing or normalizing that invariant is unsafe.

### 3.3 Required correction

Resolve the workspace exactly once after validation:

```python
workspace = Path(workspace_root).resolve()
```

Use this resolved path for:

- migration-directory resolution;
- snapshots;
- subprocess `cwd`;
- relative-path conversion.

Private helpers should receive the resolved workspace.

The function must work with both absolute and relative valid workspace input and return the same repository-relative migration path.

Add a persistent test:

```text
test_relative_workspace_root_is_supported_without_exception
```

The test must temporarily change to the workspace parent or compute a relative path, call the real function, and assert:

- no exception;
- result passed;
- one created numbered migration;
- created path is repository-relative POSIX.

---

## 4. Reproduced defect B — unsafe path containment

### 4.1 Current behavior

Containment is checked with:

```python
if not str(resolved).startswith(str(wr.resolve())):
    ...
```

String prefixes are not filesystem ancestry.

Example:

```text
workspace root: /tmp/run/work
resolved target: /tmp/run/workevil/migrations
```

The second string starts with the first string even though it is a sibling outside the workspace.

A symlink inside `work` can point to `workevil/migrations`. The current string-prefix check accepts it. The later snapshot then crashes when it attempts to make the outside file relative to the real workspace.

The audit reproduced this behavior.

### 4.2 Why it matters

This violates the most important R3B boundary:

> the migration directory must resolve beneath the active generated workspace.

A malformed profile, symlink, or future integration defect must not let the post-generation stage inspect or treat outside files as generated migrations.

A crash is also not a valid typed fail-closed result.

### 4.3 Required correction

Never use string `startswith` for path containment.

Use `Path.relative_to` in a controlled check:

```python
def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True
```

Or use an equivalent helper returning the relative path.

Validation should:

1. resolve the workspace;
2. resolve the migration directory;
3. call `relative_to(workspace)`;
4. return a typed validation error when it fails.

Do not continue to snapshot after containment fails.

Add tests:

```text
test_migration_directory_symlink_escape_fails_closed
test_sibling_prefix_path_is_not_treated_as_inside_workspace
```

On platforms where creating symlinks is unavailable, skip only the symlink-specific test with an explicit reason. The pure ancestry helper or sibling-prefix behavior must still have a non-skipped test.

The result must be:

```text
passed = False
exit_code = -1
stderr contains a containment diagnostic
```

No raw `ValueError` may escape.

---

## 5. Reproduced defect C — helper.py counts as a migration

### 5.1 Current behavior

New files are filtered only by:

- direct child of migration directory;
- `.py` suffix;
- filename is not `__init__.py`.

Therefore:

```text
todo/migrations/helper.py
```

is treated as a created migration.

The audit executed a command creating only `helper.py` with:

```text
require_new_migration=True
```

The current result incorrectly returned:

```text
passed=True
created_paths=("todo/migrations/helper.py",)
```

### 5.2 Why it matters

The contract requires exactly one **new numbered migration**.

A Python helper, backup, temporary file, or invalid generated artifact is not a Django migration. Accepting it can produce false scientific success:

- the model changes a database field;
- `makemigrations` fails to create a real migration;
- another `.py` file appears;
- the harness reports migration success incorrectly.

### 5.3 Required correction

Define one explicit filename rule for newly created numbered migration files.

Use a compiled standard-library regex equivalent to:

```python
NUMBERED_MIGRATION_RE = re.compile(r"^\d+_[A-Za-z0-9_]+\.py$")
```

A filename counts only when:

- it is a direct child of the migration directory;
- it matches the numbered migration regex;
- it is not `__init__.py`.

Do not require exactly four digits because Django numbering can exceed four digits in large histories. Require one or more digits followed by an underscore and a safe migration stem.

Examples that count:

```text
0001_initial.py
0004_task_priority.py
12_auto_20260728_1000.py
10000_large_history.py
```

Examples that do not count:

```text
helper.py
migration.py
_backup.py
0001.py
0001-.py
__init__.py
notes.txt
sub/0002_nested.py
```

Existing Python files should still be hashed regardless of whether their names are numbered, because all existing direct `.py` files in the migration directory are protected from modification.

Add tests:

```text
test_non_numbered_python_file_does_not_satisfy_required_migration
test_numbered_migration_filename_is_required
test_existing_non_numbered_python_file_is_still_integrity_protected
```

---

## 6. Reproduced defect D — timeout skips after-state inspection

### 6.1 Current behavior

The function returns immediately from:

```python
except subprocess.TimeoutExpired:
```

before calculating the after-state snapshot.

A subprocess may change or delete an old migration and then time out. The current function does not inspect what happened.

The audit used a command that:

1. rewrote `0001_initial.py`;
2. slept longer than the timeout.

The returned result failed because of timeout, but it did not derive migration integrity from the after-state or append an old-migration modification diagnostic. `existing_migrations_unchanged=False` appeared only because that is the dataclass default, not because the corruption was detected.

A timeout that makes no migration change also incorrectly returns `existing_migrations_unchanged=False`, so the field is not truthful on this path.

### 6.2 Why it matters

R3B is not only a command runner. It is a migration-integrity evidence stage.

The contract explicitly requires inspecting migrations even after command failure because a failed or timed-out command may have partially modified the workspace.

Later Runner and record metrics will rely on:

```text
existing_migrations_unchanged
created_paths
stderr diagnostics
```

These fields must describe the actual after-state.

### 6.3 Required correction

Do not return from subprocess exception handlers before after-state inspection.

Use local command outcome variables:

```python
exit_code: int
stdout: str
stderr: str
command_succeeded: bool
```

For each outcome:

- normal completion;
- timeout;
- command not found;
- `OSError`;

set these variables, then continue to one common after-state inspection block.

For `TimeoutExpired`, preserve any available `stdout` and `stderr`. Python may return bytes or strings depending on platform and options. Add a small private normalizer:

```python
def _coerce_subprocess_text(value: str | bytes | None) -> str:
    ...
```

After every attempted subprocess launch:

1. snapshot after-state;
2. compare all old files;
3. identify created numbered paths;
4. append diagnostics;
5. build one final typed result.

For validation failures that occur before subprocess launch, no after-state command inspection is needed.

For `FileNotFoundError`, after-state should normally equal before-state, and `existing_migrations_unchanged` should truthfully be `True`.

For timeout with no changes, it should also be `True`.

For timeout after modification, it must be `False` and the diagnostic must identify the changed path.

Add tests:

```text
test_timeout_without_changes_reports_existing_migrations_unchanged
test_timeout_after_modifying_old_migration_detects_corruption
test_failed_command_after_creating_migration_reports_created_path
test_command_not_found_reports_unchanged_existing_migrations
```

---

## 7. Fail-closed gap E — plain string command

### 7.1 Current behavior

The type is `Sequence[str]`. A Python `str` is also a sequence of strings.

Passing:

```python
command="python"
```

causes validation to iterate over characters and accept each one. The function later executes:

```python
list(command)
```

which becomes:

```python
["p", "y", "t", "h", "o", "n"]
```

This fails as command-not-found instead of rejecting an invalid command container.

### 7.2 Required correction

Explicitly reject:

```python
isinstance(command, (str, bytes))
```

The diagnostic should say the command must be a non-string sequence of non-empty strings.

Add:

```text
test_plain_string_command_fails_validation
test_bytes_command_fails_validation
```

---

## 8. Fail-closed gap F — whitespace command items

The current validation uses:

```python
len(item) == 0
```

A command item containing only spaces passes.

Use:

```python
not item.strip()
```

Do not alter meaningful spaces inside a valid argument.

Add:

```text
test_whitespace_only_command_item_fails
```

---

## 9. Test-quality corrections

### 9.1 Sorted-path test

The current test says:

```python
if len(result.created_paths) >= 2:
    assert ...
```

This can pass without proving two paths were recognized.

Change it to assert:

```python
assert result.created_paths == (
    "todo/migrations/0001_a.py",
    "todo/migrations/0002_b.py",
)
```

### 9.2 Smoke command-shape test

The existing test monkeypatches `subprocess.run` by direct global assignment and asserts only that it was called.

Use pytest `monkeypatch` and assert:

- command was converted to the exact list;
- `cwd` is the resolved workspace;
- `capture_output=True`;
- `text=True`;
- correct timeout;
- no `shell=True` argument.

The fake subprocess should return a small `CompletedProcess`-compatible object and create a numbered migration so the complete call passes.

### 9.3 Tests must prove typed failure

For each new invalid case, assert:

```text
result.passed is False
result.exit_code == -1
no exception is raised
```

Do not assert only that a substring exists.

---

## 10. Exact implementation shape

Keep the module small. A suitable internal structure is:

```python
@dataclass(frozen=True)
class PostGenerationResult:
    ...

def _sha256(path: Path) -> str:
    ...

def _relative_to_root(path: Path, root: Path) -> str | None:
    ...

def _validate_inputs(...) -> tuple[Path, Path] | str:
    ...

def _snapshot_migrations(
    workspace_root: Path,
    migration_directory: Path,
) -> dict[str, str]:
    ...

def _created_numbered_migrations(
    before: dict[str, str],
    after: dict[str, str],
    migration_directory_relative: str,
) -> tuple[str, ...]:
    ...

def _coerce_subprocess_text(value: str | bytes | None) -> str:
    ...

def run_post_generation_command(...) -> PostGenerationResult:
    ...
```

Do not introduce:

- a generic executor class;
- a strategy object;
- plugin registration;
- external path libraries;
- a migration parser;
- Django imports;
- Runner wiring.

R3B remains one deterministic utility module.

---

## 11. Required changed files

The correction may modify only:

```text
src/benchmark/execution/post_generation.py
tests/unit/execution/test_post_generation.py
docs/PROJECT_HANDOFF.md
reports/latest_phase_report.md
docs/V2_R3B_TO_KAGGLE_NO_DISCRETION_EXECUTION_SPEC.md
selective_updates/CHANGE_INDEX.md
```

`src/benchmark/execution/__init__.py` should not need modification unless the public export was accidentally removed. It is already correct.

Do not modify:

- Runner;
- Pipeline;
- core models;
- scenario YAML;
- evaluator assets;
- Selective;
- Repository Agent;
- README;
- generated bundle;
- notebooks.

---

## 12. Required gates

Run focused tests:

```powershell
python -m pytest tests/unit/execution/test_post_generation.py -q
```

Run the migration and validation unit area:

```powershell
python -m pytest `
  tests/unit/execution/test_post_generation.py `
  tests/unit/execution/test_validation.py `
  -q
```

Run full suite:

```powershell
python -m pytest -q
```

Quality gates:

```powershell
ruff check `
  src/benchmark/execution/post_generation.py `
  tests/unit/execution/test_post_generation.py

mypy --strict src/benchmark/execution/post_generation.py

python -m compileall src/benchmark/execution/post_generation.py

git diff --check
git diff --name-only
git diff --stat
```

Before the code commit, `git diff --name-only` must contain exactly:

```text
src/benchmark/execution/post_generation.py
tests/unit/execution/test_post_generation.py
```

---

## 13. Commit policy

The R3B commits have not been pushed. Correct the immediately preceding R3B checkpoints rather than creating misleading corrective history.

First amend the R3B code commit while preserving the later documentation commit safely.

Recommended safe process:

```powershell
git status --short
git branch --show-current
git rev-parse HEAD
```

Because HEAD is the documentation commit, do not use a blind `git commit --amend` on the current HEAD for code.

Use an interactive rebase only if OpenCode can do it safely and preserve both commits, or create one explicit correction commit if rewriting the two local commits introduces avoidable risk.

The preferred practical choice for speed and safety is:

```powershell
git add src/benchmark/execution/post_generation.py tests/unit/execution/test_post_generation.py
git commit -m "fix(validation): close migration runner safety gaps"
```

This is acceptable because the defects were discovered by an independent audit after the original code and documentation checkpoints.

Then update documentation to state:

- R3B initial checkpoint: `c11f25e`;
- independent audit found path, numbered-file, and exception-state defects;
- correction checkpoint hash;
- final test count;
- R3B accepted only after next independent audit;
- R3C remains blocked.

Commit:

```powershell
git add docs/PROJECT_HANDOFF.md reports/latest_phase_report.md docs/V2_R3B_TO_KAGGLE_NO_DISCRETION_EXECUTION_SPEC.md selective_updates/CHANGE_INDEX.md
git commit -m "docs(audit): record R3B correction"
```

Do not claim R3B independently accepted inside the implementation task. Use:

```text
R3B_CORRECTED_AUDIT_REQUIRED
```

---

## 14. Why R3C remains blocked

The evaluator runner will rely on the same principles:

- safe resolved paths;
- strict containment;
- typed errors;
- subprocess isolation;
- truthful evidence after failure.

Starting R3C while R3B still contains a prefix-containment bug and uncaught relative-path exception would duplicate unsafe patterns into the evaluator module.

Correcting R3B first gives OpenCode one safe path helper pattern to repeat carefully without creating a shared abstraction.

---

## 15. Over-engineering assessment

The correction is not over-engineering.

The required changes are:

- resolve one root path;
- replace string-prefix containment with `Path.relative_to`;
- add one standard-library regex;
- unify after-state inspection;
- reject malformed command containers;
- strengthen tests.

No new package, dependency, framework, protocol, or public API is needed.

Do not add generalized filesystem-security infrastructure. Keep the helpers private to `post_generation.py`. R3C can implement its own explicit evaluator containment checks from its own contract.

---

## 16. Project status after correction

Expected status:

```text
R1 Repository Agent                  complete
R2 Selective                         complete
R3A Scenario execution metadata      complete
R3B Migration runner                 corrected, audit required
R3C Evaluators                       blocked
R3D Runner wiring                    blocked
R4 Tokens and metrics                blocked
R5 Nine local production records     blocked
R6 Bundle and push                   blocked
Kaggle                               blocked
Stable tag                           blocked
Pilot                                blocked
```

The near goal is an independently accepted migration runner.

The distant goal remains:

```text
R3C isolated evaluators
→ R3D production validation wiring
→ R4 truthful tokens and metrics
→ R5 nine non-dry scripted records
→ R6 bundle and push
→ nine real Qwen Kaggle runs
→ independent result audit
→ stable V2 Smoke tag
→ Pilot with 7–12 changes and at least three repositories
```

---

## 17. Required final OpenCode report

The final response must contain:

1. branch;
2. starting HEAD;
3. correction code commit;
4. documentation commit;
5. exact changed files;
6. relative-workspace test evidence;
7. symlink/sibling containment evidence;
8. non-numbered `helper.py` rejection evidence;
9. timeout corruption detection evidence;
10. command-container rejection evidence;
11. focused test count;
12. full-suite count;
13. Ruff result;
14. mypy result;
15. compileall result;
16. diff-check result;
17. clean working tree;
18. R3C blocked status;
19. Kaggle/Pilot/tag status;
20. exact marker:

```text
R3B_CORRECTED_AUDIT_REQUIRED
```

Do not ask to continue. Stop for an independent audit.

---

**End of R3B independent audit and correction specification.**
