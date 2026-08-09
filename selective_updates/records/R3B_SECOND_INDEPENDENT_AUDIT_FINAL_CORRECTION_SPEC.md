# R3B Second Independent Audit and Final Correction Specification

**Status:** Mandatory final correction before R3C  
**Target branch:** `experiment/three-arm-smoke-v2`  
**Audited HEAD:** `3569a88`  
**Audited correction code commit:** `c873d9f`  
**Previous R3B implementation commit:** `c11f25e`  
**Independent audit model:** GPT-5.6 Thinking  
**Last OpenCode execution shown by the tool:** Big Pickle  
**Required next OpenCode execution model:** DeepSeek V4 Flash Free through OpenCode Zen, Build mode  
**Real experimental model later:** Qwen2.5-Coder-7B-Instruct on Kaggle  
**R3C:** blocked  
**Kaggle, Pilot, merge, and stable tag:** blocked  

---

## 1. Binding audit verdict

The first R3B correction fixed the six defects described in the first independent audit:

1. relative workspace paths;
2. string-prefix directory containment;
3. non-numbered files such as `helper.py`;
4. timeout paths skipping ordinary after-state comparison;
5. string and bytes command containers;
6. whitespace-only command items.

The supplied Windows full suite is green with `1254 passed, 11 skipped`, and the second independent audit ran all fifty focused post-generation tests successfully on Linux.

Nevertheless, R3B is **not accepted yet**. Direct adversarial execution of the actual committed production function exposed three remaining defects:

1. a numbered migration path that is a symlink to a file outside the generated workspace is accepted as a valid new migration;
2. malformed `timeout` types can raise uncaught `TypeError`, while booleans and floats are incorrectly accepted;
3. a command item containing an embedded NUL byte raises uncaught `ValueError` from `subprocess.run`.

The audit also found one repository-state defect:

4. `selective_updates/records/R3B-INDEPENDENT-AUDIT-AND-CORRECTION.md` remains untracked, although `CHANGE_INDEX.md` references it and OpenCode described the tree as clean.

These defects are narrow and can be fixed without redesigning the module. R3C must not begin until the fixes and tests below pass and the two audit records are tracked.

---

## 2. Evidence reproduced by the independent audit

### 2.1 Focused test evidence

The committed focused suite ran:

```text
50 passed
```

on Linux. This confirms that OpenCode’s new tests are real and that the ordinary intended paths remain stable.

### 2.2 Escaping migration-file symlink was accepted

The audit created:

```text
<workspace>/todo/migrations/__init__.py
<outside>/outside.py
```

Then the subprocess created:

```text
<workspace>/todo/migrations/0002_evil.py
```

as a symlink to `<outside>/outside.py`.

The actual committed production function returned the equivalent of:

```text
passed=True
exit_code=0
created_paths=("todo/migrations/0002_evil.py",)
existing_migrations_unchanged=True
```

This violates the contract that every created migration path must resolve beneath the generated workspace. The current code checks the lexical entry path with `relative_to`, but does not resolve the migration file itself before hashing and counting it. `Path.read_bytes()` follows the symlink, so the runner reads an external file and accepts the symlink as a numbered migration.

### 2.3 Invalid timeout values leak or pass

The audit called the real function with these values:

```python
timeout="1"
timeout=None
timeout=True
timeout=1.5
```

Observed behavior:

```text
"1"  → uncaught TypeError
None → uncaught TypeError
True → accepted
1.5  → accepted
```

The public API declares `timeout: int`, and the specification requires a positive integer. Python booleans are subclasses of integers, so a simple `isinstance(timeout, int)` is insufficient. The validation must require a real integer and reject bool, float, string, null, and arbitrary objects with a typed failure result.

### 2.4 Embedded NUL leaks ValueError

The audit passed:

```python
command=["bad\x00name"]
```

The value is a non-empty string, so current validation accepts it. `subprocess.run` then raises:

```text
ValueError: embedded null byte
```

The exception escapes the public function. This contradicts the requirement that malformed execution input and ordinary subprocess/path failures return `PostGenerationResult` rather than crash the benchmark Runner.

### 2.5 Repository state is not clean

Current `git status --short` contains:

```text
?? selective_updates/records/R3B-INDEPENDENT-AUDIT-AND-CORRECTION.md
```

Therefore the working tree is not clean. The file is not incidental temporary data: `selective_updates/CHANGE_INDEX.md` explicitly references it as the R3B audit record. If the branch is pushed or cloned now, that record will be absent and the change index will contain a broken reference.

The final R3B documentation closure must track:

```text
selective_updates/records/R3B-INDEPENDENT-AUDIT-AND-CORRECTION.md
selective_updates/records/R3B-SECOND-INDEPENDENT-AUDIT-FINAL-CORRECTION.md
```

The second filename is the intended destination for this document.

---

## 3. Required production fix A — migration-file symlink containment

### 3.1 Scientific requirement

The post-generation stage must prove that the generated migration is a real direct regular file inside the active workspace. It may not accept:

- a symlink to an external file;
- a symlink to another internal file;
- a broken symlink;
- a directory named like a migration;
- a nested file;
- an external file reached through a replaced migration-directory symlink.

Django `makemigrations` creates ordinary files. Rejecting symlink migration files does not restrict valid expected behavior and gives the clearest fail-closed rule.

### 3.2 Why the current check is insufficient

Current `_snapshot_migrations` performs logic equivalent to:

```python
for entry in migration_directory.iterdir():
    if entry.is_file() and entry.suffix == ".py":
        relative = entry.relative_to(workspace_root)
        hash = entry.read_bytes()
```

For a symlink inside the workspace:

- `entry.relative_to(workspace_root)` succeeds lexically;
- `entry.is_file()` follows the symlink and returns true;
- `entry.read_bytes()` follows the symlink;
- the numbered filename matches the regular expression;
- the external target is accepted.

Directory containment and file containment are different checks. The migration directory was safely resolved at input validation, but every file discovered after command execution must also be validated.

### 3.3 Exact correction

Change snapshotting so it reports both hashes and safety diagnostics. A private shape such as this is sufficient:

```python
@dataclass(frozen=True)
class _MigrationSnapshot:
    hashes: dict[str, str]
    errors: tuple[str, ...]
```

A tuple return is also acceptable:

```python
tuple[dict[str, str], tuple[str, ...]]
```

Do not create a public framework.

For every direct entry under the resolved migration directory:

1. use `entry.is_symlink()` before `entry.is_file()`;
2. if it is a symlink and its suffix is `.py`, append a diagnostic and do not hash or count it;
3. for an ordinary `.py` file, call `entry.resolve(strict=True)`;
4. require the resolved file to remain under the resolved workspace;
5. require `resolved_entry.parent == resolved_migration_directory`;
6. derive the persisted path from the ordinary lexical entry after safety validation;
7. hash the resolved regular file;
8. catch `OSError`, `RuntimeError`, and `ValueError` from stat, resolve, read, or relative-path operations and return diagnostics instead of leaking.

Examples of diagnostics:

```text
migration file symlink is not allowed: todo/migrations/0002_evil.py
migration file resolves outside workspace: todo/migrations/0002_evil.py
failed to inspect migration file todo/migrations/0002_test.py: ...
```

The before-state must fail closed if it already contains unsafe migration entries.

The after-state must:

- mark the stage failed;
- set `existing_migrations_unchanged=False` when the after-state cannot be trusted;
- exclude unsafe entries from `created_paths`;
- append the safety diagnostic to `[post-generation validation]`.

### 3.4 Required tests

Add persistent tests:

```text
test_new_numbered_migration_symlink_to_outside_fails_closed
test_new_numbered_migration_symlink_inside_workspace_fails_closed
test_existing_migration_symlink_fails_before_command
test_broken_numbered_migration_symlink_fails_closed
```

On Windows, symlink creation may require privileges. The symlink tests may skip only when the operating system genuinely refuses symlink creation. They must run on Linux CI or independent audit environments.

Also add a non-symlink ordinary numbered file control proving the new checks do not reject valid migrations.

---

## 4. Required production fix B — exact timeout type

### 4.1 Validation rule

Require:

```python
type(timeout) is int
```

or equivalently:

```python
isinstance(timeout, int) and not isinstance(timeout, bool)
```

Then require:

```python
timeout > 0
```

Using `type(timeout) is int` is simplest for this API.

Return:

```text
passed=False
exit_code=-1
stderr="timeout must be a positive integer"
```

for:

- `None`;
- `True`;
- `False`;
- `1.5`;
- `"1"`;
- lists;
- dictionaries;
- arbitrary objects;
- zero;
- negative integers.

Do not evaluate `timeout <= 0` before validating the type.

### 4.2 Required tests

Add parameterized tests covering:

```python
None
True
False
1.5
"1"
[]
{}
object()
0
-1
```

Every case must prove:

- no exception escapes;
- `passed is False`;
- `exit_code == -1`;
- the error mentions a positive integer.

Also preserve one success test with `timeout=1` or another positive integer.

---

## 5. Required production fix C — malformed subprocess values

### 5.1 Embedded NUL validation

Before launching the subprocess, reject any command item containing:

```python
"\x00"
```

Use a clear message:

```text
command item contains NUL
```

The command still allows normal spaces inside meaningful arguments. Existing empty and whitespace-only rules remain.

### 5.2 Scoped exception handling

Even with proactive validation, `subprocess.run` may raise `ValueError` for other malformed platform-specific values. Add a scoped handler around the subprocess call:

```python
except ValueError as exc:
    cmd_exit_code = -1
    cmd_stderr = f"Invalid subprocess argument: {exc}"
    cmd_passed = False
```

Also catch:

```python
except subprocess.SubprocessError as exc:
```

after the specific `TimeoutExpired` handler.

Do not wrap the entire function in `except Exception`. Broad exception swallowing can hide programming defects. Catch only expected path, filesystem, and subprocess exceptions at the operation where they may occur.

After a subprocess launch was attempted, continue through the common after-state inspection just as with timeout and `OSError`.

### 5.3 Required tests

Add:

```text
test_command_item_with_nul_fails_validation
test_subprocess_value_error_returns_typed_failure
test_subprocess_error_returns_typed_failure
```

Use monkeypatch for the latter two and assert that after-state integrity remains truthfully reported.

---

## 6. Recommended input-boundary hardening

This section is required because the public function is intended to fail closed.

### 6.1 Workspace-root type and path errors

Before calling `Path(workspace_root)`, require:

```python
isinstance(workspace_root, (str, Path))
```

Reject null, integer, list, mapping, and arbitrary objects with a typed failure.

Wrap:

- `Path(...)`;
- `.exists()`;
- `.is_dir()`;
- `.resolve()`;

in a narrow `try/except (OSError, RuntimeError, ValueError, TypeError)` inside validation.

### 6.2 Migration-directory validation

Require a non-empty, non-whitespace string.

Reject embedded NUL.

Continue rejecting:

- absolute paths;
- `..`;
- backslashes;
- paths resolving outside the workspace.

Use `Path(migration_directory).is_absolute()` in addition to containment. Containment remains the authoritative cross-platform safety check.

### 6.3 Snapshot filesystem errors

A migration file may disappear between directory listing and hashing, or may become unreadable. Snapshotting must return a diagnostic, not raise.

Add a monkeypatch test that makes hashing raise `OSError`, then prove typed failure.

These checks are small and prevent another audit cycle caused by the same “never leak ordinary filesystem exceptions” contract.

---

## 7. Test corrections

### 7.1 Do not test private helpers instead of production paths

The sibling-prefix test currently calls `_relative_to_root` directly. Keep that small unit test, but add at least one production-function containment test that passes a migration-directory symlink escaping to a sibling with the same textual prefix.

### 7.2 Subprocess-call test output types

The monkeypatched `CompletedProcess` currently returns byte stdout/stderr despite `text=True`. Return strings to match the real API:

```python
CompletedProcess(command, 0, "", "")
```

This avoids silently placing bytes into fields declared as strings.

### 7.3 Explicit result assertions

For every malformed input:

```python
assert result.passed is False
assert result.exit_code == -1
assert isinstance(result.stdout, str)
assert isinstance(result.stderr, str)
assert result.duration_seconds >= 0
```

### 7.4 No test-only acceptance of an unsafe file

The valid migration control must create an ordinary file, then assert:

```python
assert not created_path.is_symlink()
assert created_path.resolve().is_relative_to(workspace.resolve())
```

Use a `relative_to` try/except if supporting Python versions before `Path.is_relative_to`.

---

## 8. Documentation and repository state

### 8.1 Track the first audit record

Add:

```text
selective_updates/records/R3B-INDEPENDENT-AUDIT-AND-CORRECTION.md
```

It must no longer appear as untracked.

### 8.2 Track this second audit record

Place this file at:

```text
selective_updates/records/R3B-SECOND-INDEPENDENT-AUDIT-FINAL-CORRECTION.md
```

Add it to the documentation commit.

### 8.3 Update state truthfully

Update:

```text
docs/PROJECT_HANDOFF.md
reports/latest_phase_report.md
docs/V2_R3B_TO_KAGGLE_NO_DISCRETION_EXECUTION_SPEC.md
selective_updates/CHANGE_INDEX.md
```

Record:

- initial R3B commit `c11f25e`;
- first correction `c873d9f`;
- second/final correction commit;
- exact final test count;
- first audit record tracked;
- second audit record tracked;
- R3B remains “corrected — independent acceptance pending” until the next audit;
- R3C remains blocked;
- Kaggle, Pilot, merge, and stable tag remain blocked.

Do not call the working tree clean until:

```powershell
git status --short
```

prints no output.

---

## 9. Authorized files

Production and tests:

```text
src/benchmark/execution/post_generation.py
tests/unit/execution/test_post_generation.py
```

Audit and state documents:

```text
selective_updates/records/R3B-INDEPENDENT-AUDIT-AND-CORRECTION.md
selective_updates/records/R3B-SECOND-INDEPENDENT-AUDIT-FINAL-CORRECTION.md
docs/PROJECT_HANDOFF.md
reports/latest_phase_report.md
docs/V2_R3B_TO_KAGGLE_NO_DISCRETION_EXECUTION_SPEC.md
selective_updates/CHANGE_INDEX.md
```

Do not modify:

- `runner.py`;
- `pipeline.py`;
- core models;
- scenarios;
- evaluators;
- Selective;
- Agent;
- README;
- bundles;
- notebooks.

---

## 10. Exact quality gates

Run:

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

Before the code commit, only the two code/test files may be staged.

Code commit:

```text
fix(validation): reject unsafe migration entries and malformed execution input
```

Then stage the two audit records and four state files.

Documentation commit:

```text
docs(audit): record final R3B safety correction
```

Finally run:

```powershell
git status --short
git log --oneline --decorate -8
```

`git status --short` must print nothing.

---

## 11. Required final report

The OpenCode response must include:

1. requested model and actual model shown by OpenCode;
2. starting HEAD;
3. code correction commit;
4. documentation commit;
5. exact changed files;
6. external symlink migration rejection evidence;
7. internal symlink migration rejection evidence;
8. timeout-type fail-closed evidence;
9. embedded-NUL fail-closed evidence;
10. subprocess `ValueError` typed-result evidence;
11. filesystem snapshot error evidence;
12. focused test count;
13. full-suite count;
14. Ruff;
15. mypy;
16. compileall;
17. diff check;
18. proof both audit records are tracked;
19. empty `git status --short`;
20. R3C, Kaggle, Pilot, merge, and tag status.

End exactly with:

```text
R3B_FINAL_CORRECTION_AUDIT_REQUIRED
```

Do not start R3C.

---

## 12. Over-engineering assessment

This correction is still not over-engineering. The required production changes are:

- resolve and validate each migration entry;
- reject symlinks;
- validate one integer field correctly;
- reject NUL;
- catch two expected subprocess exception classes;
- return filesystem diagnostics from the existing snapshot helper.

No new dependency, framework, public service, plugin, or architecture layer is needed.

Do not introduce a generalized secure-filesystem package. Keep the logic private to `post_generation.py`.

---

## 13. Project position

After this correction and independent acceptance:

```text
R1 Repository Agent                  complete
R2 Selective                         complete
R3A Scenario metadata               complete
R3B Migration runner                complete
R3C Isolated evaluators             next
R3D Runner wiring                   pending
R4 Token and metrics                pending
R5 Nine local non-dry records       pending
R6 Bundle and push                  pending
Real Qwen Kaggle Smoke              blocked
Stable tag                          blocked
Pilot                               blocked
```

The near goal is to accept R3B and begin R3C.

The distant goal remains:

```text
R3C evaluators
→ R3D validation wiring
→ R4 truthful metrics
→ R5 nine local records
→ R6 bundle and push
→ nine real Qwen Kaggle runs
→ independent result audit
→ v2.0.0-scientific-smoke tag
→ Pilot with 7–12 changes and at least three repositories
```

---

**End of second independent R3B audit and final correction specification.**
