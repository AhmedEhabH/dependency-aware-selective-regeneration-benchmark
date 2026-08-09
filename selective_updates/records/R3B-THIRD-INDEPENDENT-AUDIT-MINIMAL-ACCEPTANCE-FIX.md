# R3B Third Independent Audit — Minimal Acceptance Fix

**Status:** One blocking production defect remains before R3C  
**Target branch:** `experiment/three-arm-smoke-v2`  
**Audited HEAD:** `8ec9f44`  
**Audited code checkpoint:** `c635e42`  
**Required execution model:** DeepSeek V4 Flash Free — OpenCode Zen — Build  
**Actual model displayed by the preceding OpenCode run:** Big Pickle  
**Independent audit model:** GPT-5.6 Thinking  
**Permitted next action:** correct R3B only  
**R3C, Kaggle, Pilot, merge, and stable tag:** blocked  

---

## 1. Final audit verdict

The latest R3B correction substantially improved the deterministic migration runner. The source tree is clean, both previous audit records are tracked, the full Windows suite supplied by the researcher reports `1273 passed, 15 skipped`, and an independent Linux run of the current focused migration-runner suite reports:

```text
73 passed
```

The following previously reported defects are now correctly addressed:

- relative workspace paths are normalized;
- migration-directory containment uses `Path.relative_to` rather than string prefixes;
- non-numbered Python files do not satisfy the required migration;
- timeout and subprocess exception paths proceed to after-state inspection;
- string and bytes command containers are rejected;
- whitespace-only command items are rejected;
- timeout must be a positive real integer and does not accept booleans or floats;
- command and migration-directory NUL values are rejected;
- migration-file symlinks present in a snapshot are diagnosed;
- snapshot read and resolution exceptions are converted to typed errors;
- audit documentation is committed and the working tree is clean.

One blocking defect remains:

> Errors discovered during the **after-state migration snapshot** are appended to `stderr`, but they do not make the result fail and do not make `existing_migrations_unchanged` false.

This allows the function to return `passed=True` while simultaneously reporting that an unsafe migration-file symlink exists. The independent audit reproduced this against the committed production function.

R3C must not begin until this single defect and the small related input-validation gap described below are fixed and covered by tests.

---

## 2. Exact reproduced false-success case

The audit created an ordinary generated workspace containing:

```text
todo/migrations/__init__.py
todo/migrations/0001_initial.py
```

The subprocess then created two entries:

```text
todo/migrations/0002_good.py
todo/migrations/0003_evil.py
```

`0002_good.py` was an ordinary valid numbered migration.

`0003_evil.py` was a symlink to a Python file outside the generated workspace.

The production function correctly detected the unsafe symlink and appended:

```text
migration file symlink is not allowed: todo/migrations/0003_evil.py
```

to the validation diagnostics. It also correctly excluded the unsafe symlink from `created_paths`.

However, because the ordinary `0002_good.py` supplied exactly one valid created migration and all old hashes matched, the final result was:

```text
passed=True
exit_code=0
created_paths=("todo/migrations/0002_good.py",)
existing_migrations_unchanged=True
```

while `stderr` simultaneously contained the symlink safety error.

This is internally contradictory and scientifically unsafe. A result cannot be successful when the runner has reported that it cannot trust the after-state migration directory.

A second reproduced case created only one unsafe symlink and used:

```python
require_new_migration=False
```

The result again returned `passed=True` because no migration count was required and after-snapshot errors were not part of the success condition.

---

## 3. Root cause

Current code performs:

```python
after, after_errors = _snapshot_migrations(workspace, migration_directory)

all_old_unchanged = True
diagnostics: list[str] = list(before_errors)
diagnostics.extend(after_errors)
```

It then compares old hashes and calculates valid created numbered paths.

The final success logic starts from:

```python
passed = all_old_unchanged
```

The boolean never incorporates `after_errors`.

Therefore:

```text
after_errors exist
AND old known files are unchanged
AND the valid migration count is acceptable
AND subprocess exit code is zero
```

produces a successful result.

The diagnostics are treated only as text. They are not treated as a failed integrity check.

The before-state path does not have this defect because `before_errors` causes an immediate failed result before subprocess execution.

---

## 4. Required production correction

Modify only:

```text
src/benchmark/execution/post_generation.py
```

after the subprocess and after-state snapshot.

Use one explicit boolean:

```python
after_snapshot_trusted = not after_errors
```

Then calculate:

```python
all_old_unchanged = after_snapshot_trusted
```

before comparing old hashes.

Equivalently:

```python
all_old_unchanged = not after_errors
```

The subsequent old-file comparison may change it to false but must never restore it to true.

The final `passed` condition must require all of the following:

```text
subprocess succeeded
after-state snapshot has no errors
all known old migration files still exist
all known old migration hashes are unchanged
required numbered-migration count is satisfied
```

A compact safe structure is:

```python
after, after_errors = _snapshot_migrations(workspace, migration_directory)

diagnostics = list(after_errors)
all_old_unchanged = not after_errors

for old_path, old_hash in before.items():
    if old_path not in after:
        all_old_unchanged = False
        diagnostics.append(...)
    elif after[old_path] != old_hash:
        all_old_unchanged = False
        diagnostics.append(...)

created = _created_numbered_migrations(...)

migration_count_ok = (
    not require_new_migration
    or len(created) == 1
)

passed = (
    cmd_passed
    and not after_errors
    and all_old_unchanged
    and migration_count_ok
)
```

When `after_errors` is non-empty:

```text
passed = False
exit_code = -1
existing_migrations_unchanged = False
```

even when:

- the subprocess exited zero;
- one valid numbered migration also exists;
- no new migration is required;
- every old file that was successfully read still matches.

The unsafe entry must remain excluded from `created_paths`.

Do not discard the valid ordinary created path. It may remain in `created_paths` as truthful partial evidence, while the complete stage fails.

Do not remove the safety diagnostic from `stderr`.

Do not weaken symlink rejection.

---

## 5. Required tests

Modify only:

```text
tests/unit/execution/test_post_generation.py
```

Add these exact production-path tests.

### 5.1 Valid migration plus unsafe external symlink

The symlink must be created by the subprocess or monkeypatched subprocess action **after the before snapshot**, not before calling the public function.

Arrange:

```text
before:
  __init__.py
  0001_initial.py

after:
  0002_good.py ordinary file
  0003_evil.py symlink to outside file
```

Call with:

```python
require_new_migration=True
```

Assert:

```python
result.passed is False
result.exit_code == -1
result.created_paths == ("todo/migrations/0002_good.py",)
result.existing_migrations_unchanged is False
"symlink" in result.stderr
```

This test is mandatory on platforms supporting symlinks. It may skip on Windows only when the operating system refuses symlink creation. It must run on Linux.

### 5.2 Unsafe symlink when no migration is required

Create the unsafe symlink after the before snapshot.

Call with:

```python
require_new_migration=False
```

Assert:

```python
result.passed is False
result.exit_code == -1
result.created_paths == ()
result.existing_migrations_unchanged is False
"symlink" in result.stderr
```

This proves after-state safety is independent of migration-count policy.

### 5.3 Synthetic after-snapshot error

Use `monkeypatch` on `_snapshot_migrations` with a call counter:

- first call returns a normal before snapshot and no errors;
- second call returns an after snapshot plus:
  `("simulated after-state inspection failure",)`.

The subprocess returns success.

Assert a typed failed result, integrity false, and the diagnostic in stderr.

This test must not depend on symlink privileges and therefore runs on Windows and Linux.

### 5.4 Existing ordinary valid control

Retain a control proving that one ordinary numbered migration and no snapshot errors still passes.

---

## 6. Minor input-validation closure

The second audit required `migration_directory` to be a non-empty, non-whitespace string.

Current code rejects only:

```python
len(migration_directory) == 0
```

A directory literally named with spaces can therefore be accepted, and the independent audit reproduced a successful result with:

```python
migration_directory="   "
```

Correct validation to:

```python
if (
    not isinstance(migration_directory, str)
    or not migration_directory.strip()
):
    return "migration_directory is not a valid POSIX path"
```

Continue preserving meaningful characters in normal paths. Do not call `.strip()` on the actual path used for execution; reject whitespace-only input rather than silently changing it.

Add a parameterized test covering:

```python
""
" "
"   "
"\t"
"\n"
```

Every case must return a typed failure with `exit_code=-1`.

This is a small closure of an already documented requirement and does not expand R3B’s scope.

---

## 7. Test-quality correction

The currently named tests:

```text
test_new_numbered_migration_symlink_to_outside_fails_closed
test_new_numbered_migration_symlink_inside_workspace_fails_closed
```

create the symlink **before** the function call. They prove that unsafe entries in the before snapshot fail, but they do not prove that a subprocess-created new symlink fails.

Do not delete them. Rename them only if doing so improves accuracy without unnecessary churn, or leave them and add the required after-state tests with explicit names such as:

```text
test_subprocess_created_external_symlink_forces_failure
test_subprocess_created_symlink_forces_failure_when_migration_not_required
```

The critical distinction is whether the unsafe entry exists before or after the initial snapshot.

---

## 8. Authorized files

Code checkpoint:

```text
src/benchmark/execution/post_generation.py
tests/unit/execution/test_post_generation.py
```

Documentation checkpoint:

```text
docs/PROJECT_HANDOFF.md
reports/latest_phase_report.md
docs/V2_R3B_TO_KAGGLE_NO_DISCRETION_EXECUTION_SPEC.md
selective_updates/CHANGE_INDEX.md
selective_updates/records/R3B-THIRD-INDEPENDENT-AUDIT-MINIMAL-ACCEPTANCE-FIX.md
```

The audit file itself must be placed at the exact final path above and committed.

Do not modify:

- Runner;
- Pipeline;
- core models;
- scenarios;
- evaluator assets;
- Selective;
- Repository Agent;
- README;
- Kaggle bundle;
- notebooks.

---

## 9. Required gates

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

Before the code commit, the changed list must contain only:

```text
src/benchmark/execution/post_generation.py
tests/unit/execution/test_post_generation.py
```

Create:

```text
fix(validation): fail on untrusted migration after-state
```

Then update and stage the five documentation/audit files.

Create:

```text
docs(audit): record R3B acceptance closure
```

Finally require:

```powershell
git status --short
```

to print no output.

---

## 10. Model-reporting requirement

The previous OpenCode response claimed:

```text
Model: DeepSeek V4 Flash Free
```

while the visible execution footer showed:

```text
Build · Big Pickle
```

The next task must run using:

```text
DeepSeek V4 Flash Free
Provider: OpenCode Zen
Mode: Build
```

The final report must state both:

- the requested model;
- the actual model shown by OpenCode’s execution footer.

Do not claim DeepSeek was used when the footer shows Big Pickle.

This model mismatch does not invalidate committed engineering code by itself, but it is a process-control failure and must not recur.

---

## 11. Final report contract

The final OpenCode response must include:

1. requested model;
2. actual footer model;
3. branch;
4. starting HEAD;
5. code commit;
6. documentation commit;
7. exact changed files;
8. valid migration plus unsafe symlink test;
9. unsafe symlink with `require_new_migration=False` test;
10. synthetic after-snapshot error test;
11. whitespace migration-directory test;
12. focused test count;
13. full-suite count;
14. Ruff result;
15. mypy result;
16. compileall result;
17. `git diff --check`;
18. clean `git status --short`;
19. R3C status;
20. Kaggle, Pilot, merge, and stable-tag status.

End exactly with:

```text
R3B_ACCEPTANCE_CLOSURE_AUDIT_REQUIRED
```

Do not start R3C.

---

## 12. Over-engineering assessment

This is a minimal correction, not a redesign.

The production change should be approximately:

- one boolean initialized from `after_errors`;
- one final success-condition adjustment;
- one whitespace-only validation check.

The tests are longer than the production change because they must reproduce the exact false-success boundary.

Do not introduce a new dataclass, service, framework, dependency, or reusable filesystem layer for this correction. Existing helpers are sufficient.

---

## 13. Project position

Current status:

```text
R1 Repository Agent                  complete
R2 Selective                         complete
R3A Scenario metadata               complete
R3B Migration runner                one minimal acceptance fix
R3C Isolated evaluators             blocked
R3D Runner wiring                   pending
R4 Token and metrics                pending
R5 Nine local non-dry records       pending
R6 Bundle and push                  pending
Kaggle                              blocked
Stable tag                          blocked
Pilot                               blocked
```

Near goal:

```text
Make after-state snapshot errors fatal
→ independent R3B acceptance audit
→ begin R3C
```

Distant goal:

```text
R3C evaluators
→ R3D validation wiring
→ R4 truthful metrics
→ R5 nine local records
→ R6 bundle and push
→ nine real Qwen Kaggle runs
→ independent result audit
→ v2.0.0-scientific-smoke tag
→ Pilot with 7–12 changes across at least three repositories
```

---


## 14. Independent auditor verification procedure

After OpenCode completes the correction, the next independent auditor should not rely only on the new unit-test count. The auditor should inspect the final production condition directly and run one adversarial script against the committed function.

The source inspection should confirm all of the following:

```text
after_errors participates in the integrity boolean;
after_errors participates in the final passed boolean;
after_errors cannot be overwritten by later successful old-hash comparisons;
unsafe entries remain absent from created_paths;
diagnostics remain visible in stderr;
successful ordinary migration behavior is unchanged.
```

The adversarial execution should create the unsafe symlink during subprocess execution, not before the public function begins. This distinction is essential because before-state errors were already handled correctly in the previous checkpoint. The unresolved defect exists only in the common after-state path.

A valid audit sequence is:

1. create a temporary workspace;
2. create `todo/migrations/__init__.py`;
3. create `todo/migrations/0001_initial.py`;
4. create an ordinary file outside the workspace;
5. call `run_post_generation_command`;
6. make the subprocess create one ordinary numbered migration;
7. make the same subprocess create one numbered symlink to the outside file;
8. require one new migration;
9. inspect the returned typed result.

The accepted result must be:

```text
passed=False
exit_code=-1
created_paths contains only the ordinary migration
existing_migrations_unchanged=False
stderr identifies the unsafe symlink
```

The auditor should then repeat the case with `require_new_migration=False`. The result must still fail, proving that filesystem trust is independent of whether a scenario requires a new numbered migration.

Finally, run a clean control where the subprocess creates only one ordinary numbered migration. That result must pass. This guards against correcting the false-success defect by making all after-state results fail indiscriminately.

The documentation audit should confirm:

- the new audit record is committed;
- the code and documentation commits are separate;
- R3B is not described as accepted before independent review;
- R3C remains blocked;
- the latest full-suite count is factual;
- no README, bundle, Runner, Pipeline, evaluator, Selective, or Agent files changed.

This verification procedure is intentionally small. It provides decisive evidence for the exact remaining defect without reopening already accepted R3B design decisions.

## 15. Definition of R3B acceptance

R3B may be marked independently accepted only when all of the following are true:

```text
input validation fails closed;
workspace and migration directory remain contained;
ordinary old migration files remain byte-identical;
unsafe or unreadable after-state entries force failure;
only ordinary numbered direct files count as migrations;
subprocess failures return typed evidence;
timeout results include truthful after-state evidence;
exactly one migration is required when configured;
the focused and full suites are green;
the Git tree is clean;
all referenced audit records are tracked.
```

Passing the command and finding one valid migration is necessary but not sufficient. The complete migration directory must also be trustworthy. This is the central condition missing from the current checkpoint.

Once the next independent audit confirms these points, no further R3B hardening should be performed unless R3D integration exposes a genuine production defect. The team should then move directly to R3C rather than continue speculative filesystem hardening.


**End of third independent R3B audit.**
