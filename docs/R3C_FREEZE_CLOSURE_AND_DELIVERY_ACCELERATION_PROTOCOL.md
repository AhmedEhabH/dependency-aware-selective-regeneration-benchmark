# R3C Freeze Closure and Delivery Acceleration Protocol

**Document role:** Authoritative execution and process-control contract  
**Target branch:** `experiment/three-arm-smoke-v2`  
**Audited HEAD:** `36e396d`  
**Audited R3C code checkpoint:** `4a100bf`  
**Accepted R3B checkpoint:** `feb5a44`  
**Independent audit model:** GPT-5.6 Thinking  
**Required OpenCode implementation model:** DeepSeek V4 Flash Free through OpenCode Zen, Build mode  
**Actual model displayed by the last OpenCode execution:** Big Pickle  
**Real scientific model later:** Qwen2.5-Coder-7B-Instruct on Kaggle  
**Immediate permission:** complete the bounded R3C freeze closure and print the full report  
**R3D, R4, R5, R6, Kaggle, Pilot, merge, and stable tag:** blocked until the independent R3C freeze audit  

---

# 1. Executive answer

The detailed report required from OpenCode was not printed.

The last OpenCode response printed:

```text
R3C_FINAL_FREEZE_AUDIT_REQUIRED
```

with a short todo list and two commit hashes. It did not print the mandatory 1,000–1,800-word Section 29 report. The persisted `reports/latest_phase_report.md` is also a short phase summary, not the detailed artifact-by-artifact report required by the master specification.

The Git history shows a second process defect:

```text
4a100bf fix(validation): close R3C trust lifecycle and semantic gaps
36e396d docs(audit): record R3C final freeze candidate
```

The code commit includes:

- two large specification documents;
- `reports/latest_phase_report.md`;
- evaluator `.sha256` metadata;
- all code and tests.

The documentation commit is empty.

This violates the required separation:

```text
code and tests
→ code commit

documentation and records
→ documentation commit
```

The next task must correct the remaining R3C evidence gaps and must print and persist the complete report. It must not begin R3D.

---

# 2. Independent audit summary

## 2.1 Evidence that passes

The supplied Windows environment reports:

```text
1414 passed
32 skipped
0 failed
```

The independent Linux environment executed:

```text
PYTHONPATH=src python -m pytest tests/unit/execution/test_scenario_evaluator.py -q
```

with:

```text
67 passed
2 skipped
0 failed
```

The independent audit also executed all three standalone evaluator scripts through a fake-Django lifecycle in two failure modes:

```text
setup_databases failure with successful teardown
setup_databases failure with teardown failure
```

Result:

```text
6 of 6 scripts emitted exactly one valid JSON object
all returned exit code 1
all preserved the setup error
all teardown-failure cases preserved the teardown diagnostic
```

The live evaluator-asset trust code rejects an evaluator file replaced by an external symlink after request validation when `_load_trusted_evaluator_asset` is called on the validated request.

The working tree in the supplied ZIP is clean.

## 2.2 Evidence that remains weak or false

The current repository still contains these concrete problems.

### A. Actual model mismatch

The task requested DeepSeek V4 Flash Free.

The visible execution footer says:

```text
Build · Big Pickle
```

The report must use the footer as the source of truth.

### B. The detailed report is absent

The required report was neither printed nor persisted in the required format.

### C. Code/documentation commit separation failed

The code commit includes documentation and audit specifications.

The documentation commit is empty.

### D. TOCTOU tests do not perform TOCTOU

Tests named:

```text
test_asset_replaced_by_external_symlink_after_validation_fails
test_asset_replaced_by_internal_symlink_after_validation_fails
test_evaluator_root_replaced_by_symlink_after_validation_fails
```

replace files or directories before calling `run_scenario_evaluator`.

`run_scenario_evaluator` then performs validation after the replacement.

Those tests prove ordinary pre-validation rejection. They do not prove:

```text
validate ordinary asset
→ mutate filesystem
→ trust/load stage rejects mutation
```

The evaluator-root replacement test attempts `Path.unlink()` on a non-empty directory and skips on Linux. It therefore provides no evidence.

### E. A regular-file replacement test is conceptually invalid

The test named:

```text
test_asset_replaced_by_different_regular_file_after_validation_fails
```

replaces the file before calling the public function. It also attempts to infer identity through inode reuse, while production code compares only resolved paths.

The frozen contract does not require inode identity. It requires:

- lexical path remains ordinary;
- path remains beneath evaluator root;
- path resolves to the same resolved location;
- trusted bytes are read once and copied from memory.

Delete this misleading test or rewrite it to prove the actual frozen contract.

### F. Permission-layer proof is incomplete

Smoke 003 `task_create_uses_project_owner` verifies:

- owner API POST succeeds;
- non-owner API POST returns 403;
- `TaskViewSet.permission_classes` contains `IsProjectOwner`.

It does not invoke the configured permission objects.

An implementation could:

- include a permissive `IsProjectOwner`;
- deny creation inside `TaskViewSet.perform_create`;
- pass the current evaluator.

This violates the frozen scenario requirement that authorization logic belongs in `permissions.py`.

### G. Source-isolation assertion is logically incorrect

The integration helper uses:

```python
assert not leaker.exists() or not leaker.is_symlink()
```

For an ordinary evaluator directory:

```text
not exists = False
not symlink = True
False OR True = True
```

The assertion passes even though the evaluator directory exists.

The correct absence condition is:

```python
assert not leaker.exists() and not leaker.is_symlink()
```

or one explicit helper that treats file, directory, working symlink, and broken symlink as contamination.

### H. Lifecycle behavior is not protected by persistent tests

The independent audit proved the scripts currently emit JSON on setup/teardown failures, but the repository does not contain the required six fake-Django regression tests.

Future edits can break this behavior without detection.

### I. Canonical hash tests may mutate the repository

The test currently writes a `.sha256` file when it is absent.

Tests must never repair repository metadata while running.

The metadata files are now tracked. The test must fail when metadata is absent rather than write it.

### J. Documentation is still stale

`docs/PROJECT_HANDOFF.md` still describes R3B as independent-audit pending in some sections and contains old current-state rows.

`reports/latest_phase_report.md` does not contain the required detailed report.

The V2 continuation file is not fully synchronized with the final R3C candidate.

---

# 3. Immediate R3C closure goal

The closure has five goals only.

```text
1. Make tests prove the behaviors their names claim.
2. Make Smoke 003 prove that Task POST authorization is in configured permissions.
3. Make source-isolation assertions logically correct.
4. Persist the fake-Django lifecycle contract and immutable hash metadata.
5. Print and persist a truthful detailed report, with correct commit separation.
```

Do not redesign `scenario_evaluator.py`.

Do not rewrite fixture architecture.

Do not add more evaluator check names.

Do not begin R3D.

---

# 4. Authorized files

## 4.1 Code and test commit

Modify only:

```text
tests/unit/execution/test_scenario_evaluator.py
tests/integration/test_todo_smoke_evaluator_assets.py
tests/evaluator_assets/todo_smoke_003_checks.py
tests/support/evaluator_fixture_workspaces.py
```

Modify `src/benchmark/execution/scenario_evaluator.py` only if a corrected real TOCTOU test exposes a production failure. Do not modify it preemptively.

Do not modify Smoke 001 or Smoke 002 evaluator assets unless a focused test proves a real defect.

## 4.2 Documentation commit

Modify only:

```text
reports/latest_phase_report.md
docs/PROJECT_HANDOFF.md
docs/V2_R3B_TO_KAGGLE_NO_DISCRETION_EXECUTION_SPEC.md
docs/R3C_FREEZE_CLOSURE_AND_DELIVERY_ACCELERATION_PROTOCOL.md
selective_updates/CHANGE_INDEX.md
selective_updates/records/R3C-FINAL-FREEZE-CLOSURE.md
selective_updates/records/TECHNICAL-DEBT-AND-REFACTOR-SCHEDULE.md
```

The protocol file is this document and must be tracked at:

```text
docs/R3C_FREEZE_CLOSURE_AND_DELIVERY_ACCELERATION_PROTOCOL.md
```

## 4.3 Frozen files

Do not modify:

```text
src/benchmark/execution/post_generation.py
tests/unit/execution/test_post_generation.py
src/benchmark/execution/runner.py
src/benchmark/execution/pipeline.py
scenario YAML
README.md
kaggle_upload/
notebooks/
Selective
Repository Agent
token metrics
```

---

# 5. Correct TOCTOU tests

## 5.1 External asset symlink after validation

Use this exact flow:

```python
request = _validate_evaluator_request(...)
assert isinstance(request, _ValidatedEvaluatorRequest)

request.evaluator_asset_lexical.unlink()
request.evaluator_asset_lexical.symlink_to(outside_file)

trusted = _load_trusted_evaluator_asset(request)

assert isinstance(trusted, str)
assert "symlink" in trusted.lower()
```

Do not call `run_scenario_evaluator`, because it would revalidate from the beginning and would not test the transition between validation and trust.

## 5.2 Internal asset symlink after validation

Same flow, with the symlink target inside evaluator root.

Require rejection.

## 5.3 Evaluator root replacement after validation

Use:

```python
request = _validate_evaluator_request(...)
shutil.rmtree(request.evaluator_root)
request.evaluator_root.symlink_to(replacement_root, target_is_directory=True)

trusted = _load_trusted_evaluator_asset(request)
```

Require rejection.

Do not call `unlink()` on a directory.

## 5.4 Ordinary content mutation after trust

The supported contract is:

```text
load trusted asset bytes
→ source file changes later
→ copied evaluator uses frozen trusted bytes
```

Keep one test for this behavior.

Do not require inode identity.

Delete the misleading different-regular-file test or replace it with:

```text
test_same_ordinary_path_content_is_frozen_at_trust_time
```

## 5.5 Cross-platform evidence

Symlink tests may skip on Windows when the operating system refuses symlink creation.

At least one synthetic test must monkeypatch `_resolve_live_evaluator_asset` or the lexical-path state so the trust transition is tested on every platform.

---

# 6. Permission-layer proof

## 6.1 Preserve API behavior

Keep:

```text
project owner Task POST → 201
other user Task POST → 403
```

## 6.2 Invoke configured permission classes

Inside `task_create_uses_project_owner`, import:

```python
from types import SimpleNamespace
from todo.views import TaskViewSet
```

Create:

```python
owner_request = SimpleNamespace(
    user=owner,
    method="POST",
    data={"project": project.pk},
)

other_request = SimpleNamespace(
    user=other,
    method="POST",
    data={"project": project.pk},
)
```

Create a view instance:

```python
view = TaskViewSet()
```

Evaluate every configured permission:

```python
owner_results = [
    bool(permission().has_permission(owner_request, view))
    for permission in TaskViewSet.permission_classes
]

other_results = [
    bool(permission().has_permission(other_request, view))
    for permission in TaskViewSet.permission_classes
]
```

Require:

```text
all owner_results are True
at least one other_result is False
```

This proves the configured permission layer participates in the denial.

Do not require one class name.

Do not parse `request.data` twice.

Do not use a DRF `Request` object that can raise `RawPostDataException`.

## 6.3 Correct fixture

`TaskViewSet.perform_create` must contain only:

```python
serializer.save()
```

No project-owner authorization.

The configured permission class must own the POST authorization.

## 6.4 Negative variant

`task_owner_authority` continues changing only `todo/permissions.py`.

The expected failure remains:

```text
task_update_uses_project_owner
```

The correct fixture and negative fixture must differ in exactly one source file.

---

# 7. Source-isolation correction

Create one test helper:

```python
def _assert_workspace_has_no_evaluator_assets(workspace: Path) -> None:
    evaluator_root = workspace / "tests" / "evaluator_assets"
    assert not evaluator_root.exists()
    assert not evaluator_root.is_symlink()
    assert not (workspace / "scenario_evaluator.py").exists()
```

Call it:

- inside `_EvaluatorHelper.run`;
- in every all-variant migration-integrity test;
- in the dedicated source-isolation test.

This helper rejects:

```text
ordinary file
ordinary directory
working symlink
broken symlink
copied script at workspace root
```

Add a unit test for the helper with:

```text
ordinary directory
ordinary file
broken symlink when supported
```

---

# 8. Fake-Django lifecycle regression tests

## 8.1 Location

Add the tests to:

```text
tests/integration/test_todo_smoke_evaluator_assets.py
```

They do not require the real Django package.

## 8.2 Fake workspace

Create:

```text
manage.py
config/settings.py
todo/
django/__init__.py
django/test/runner.py
```

The fake `django.setup()` is a no-op.

## 8.3 Mode A

`setup_databases()` raises:

```text
RuntimeError("setup db boom")
```

Teardown succeeds.

For each evaluator asset, execute it directly with `sys.executable`.

Require:

```text
exit code 1
stdout parses as exactly one JSON object
passed is false
checks is a list
error contains "setup db boom"
```

## 8.4 Mode B

`setup_databases()` raises and `teardown_test_environment()` raises:

```text
RuntimeError("teardown boom")
```

For each asset require:

```text
one JSON object
error contains setup db boom
error contains teardown_test_environment
error contains teardown boom
```

Total:

```text
3 assets × 2 modes = 6 lifecycle runs
```

## 8.5 No accidental local import

Set subprocess `PYTHONPATH` to the fake workspace first.

The evaluator must not import benchmark code.

---

# 9. Immutable evaluator hash tests

The three tracked metadata files are:

```text
tests/evaluator_assets/todo_smoke_001_checks.py.sha256
tests/evaluator_assets/todo_smoke_002_checks.py.sha256
tests/evaluator_assets/todo_smoke_003_checks.py.sha256
```

The test must:

1. require the metadata file exists;
2. read its content;
3. validate it is exactly one lowercase 64-character SHA-256 string;
4. calculate the evaluator hash;
5. compare equality.

Forbidden:

```python
if not metadata_path.exists():
    metadata_path.write_text(...)
```

Tests must never mutate the repository.

When an evaluator changes intentionally:

- update the `.sha256` file in the code commit;
- show the old and new hash in the detailed report.

---

# 10. Detailed report requirements

The report is a deliverable, not an optional summary.

It must be printed in the OpenCode response and saved verbatim to:

```text
reports/latest_phase_report.md
```

Length:

```text
1,200–2,000 words
```

Use these exact headings.

## A. Model identity

```text
Requested model:
Actual footer model:
Provider:
Mode:
Elapsed time:
```

The final footer model is authoritative.

## B. Git identity

```text
Branch:
Starting HEAD:
Code commit:
Documentation commit:
Final HEAD:
Working tree:
```

## C. Objective and frozen boundaries

Explain:

- what R3C proves;
- which files are frozen;
- why R3D remains blocked.

## D. Exact artifact changes

Use this table:

| File | Before | After | Reason | Dependency impact | Proving tests |
|---|---|---|---|---|---|

Every changed file gets one row.

The “After” column must name exact functions, checks, or assertions.

## E. State-machine evidence

Print:

```text
validation
→ live asset trust
→ frozen trusted bytes
→ isolated subprocess
→ exact JSON parse
→ typed result
```

Explain every failure representation.

## F. Evaluator semantics

For each scenario:

- list exact check names;
- state what each check proves;
- state each negative variant and expected check.

## G. Twelve fixture results

Print twelve rows with:

```text
scenario
variant
passed
exit code
checks
error category
migration path
old migrations unchanged
evaluator absent from workspace
```

Do not print only “12/12 passed.”

## H. Six lifecycle results

Print six rows.

## I. Failure-matrix evidence

Include:

- external symlink after validation;
- internal symlink after validation;
- evaluator-root replacement after validation;
- broken workspace evaluator symlink;
- copy write failure;
- copy read failure;
- copy hash mismatch;
- teardown failure;
- payload contradiction;
- non-zero exit with passed payload.

## J. Incremental build history

List commands in execution order.

Include every temporary failure encountered and how it was resolved.

Do not hide failed focused tests.

## K. Final gates

Print exact command and exact result for:

```text
unit evaluator tests
integration evaluator tests
unit + integration + R3B tests
full suite
Ruff
mypy
compileall
git diff --check
git status --short
```

## L. Commit-scope proof

Print:

```text
git diff --name-only <start>..<code-commit>
git show --stat <code-commit>
git show --stat <docs-commit>
```

The code commit must contain code/tests only.

The docs commit must contain docs/records only.

## M. Technical debt impact

Print:

```text
Debt closed:
Debt intentionally deferred:
New debt introduced:
```

“None” requires evidence.

## N. Productivity metrics

Print:

```text
planned production files
actual production files
planned test files
actual test files
compile failures before commit
focused-test failures before commit
independent-audit correction cycles
elapsed implementation time
```

## O. Authorization

State:

```text
R3B accepted and frozen at feb5a44
R3C self-gates passed
R3C independent audit pending
R3D blocked
Kaggle/Pilot/merge/tag blocked
```

## P. Marker

```text
R3C_FREEZE_CLOSURE_AUDIT_REQUIRED
```

---

# 11. Commit discipline

## 11.1 Code commit

Before staging:

```powershell
git diff --name-only
```

Only code/test files may appear.

Stage explicit paths.

Commit:

```text
test(validation): close R3C freeze evidence gaps
```

Use `fix(validation)` instead only if production code actually changes.

## 11.2 Documentation commit

After the code commit:

- write the complete report;
- update handoff;
- update V2 continuation state;
- add debt schedule;
- add closure record;
- track this protocol.

Commit:

```text
docs(audit): record R3C freeze closure
```

## 11.3 No empty commits

Before every commit:

```powershell
git diff --cached --name-only
```

If empty, do not commit.

## 11.4 No broad staging

Forbidden:

```text
git add .
git add -A
git commit -a
```

---

# 12. Development operating model for speed

The project must stop treating implementation and audit as a sequence of improvised patches.

Every feature phase uses one fixed pipeline.

## 12.1 Phase 0 — Architecture preflight

Before editing, write:

```text
feature goal
public API
authorized artifacts
dependency map
state machine
success equation
failure equivalence classes
integration path
persistence impact
documentation impact
```

Time budget:

```text
10–15% of phase effort
```

Do not spend more than 20% unless a public contract is genuinely ambiguous.

## 12.2 Phase 1 — Tests first at contract boundaries

Write tests for:

```text
input types
normal success
each failure equivalence class
three combined adversarial cases
one real public-path integration
one persistence or isolation proof
```

The objective is not maximum test count.

The objective is coverage of the state dimensions.

## 12.3 Phase 2 — Incremental implementation

Implement one state at a time.

After each production file:

```text
py_compile
smallest focused test
Ruff for the file
mypy for production file
```

Do not write all artifacts before first execution.

## 12.4 Phase 3 — Integration before completion claim

Run the real cross-module path.

No phase may be called complete based only on unit tests.

## 12.5 Phase 4 — Bounded refactor sweep

Before the code commit, perform one refactor review.

Time budget:

```text
maximum 15% of phase implementation time
```

Allowed:

- remove duplicate branches;
- replace data-plus-error tuples with typed states;
- consolidate repeated test fixtures;
- improve names to frozen pattern;
- remove dead code introduced by the phase;
- make success equations explicit.

Forbidden:

- unrelated cleanup;
- public API redesign;
- generic frameworks;
- speculative optimization;
- touching frozen prior phases.

## 12.6 Phase 5 — Self-red-team

Run at least three direct cases that are not copied verbatim from unit tests.

Record them in the report.

## 12.7 Phase 6 — Commit and report

Code commit first.

Documentation second.

Independent audit pending.

---

# 13. Technical-debt classification

Every debt item receives:

```text
ID
phase introduced
artifact
category
severity
evidence
impact
owner phase
planned checkpoint
status
```

## 13.1 Severity

### TD-0 — scientific correctness blocker

Examples:

- Ground Truth leakage;
- evaluator leakage;
- false success;
- wrong model settings;
- cumulative scenarios;
- missing real validation.

Action:

```text
fix before next phase
```

### TD-1 — production-path blocker

Examples:

- field dropped from persistence;
- non-dry path bypass;
- subprocess crash;
- incorrect token accounting;
- broken resume identity.

Action:

```text
fix before next phase
```

### TD-2 — maintainability risk

Examples:

- duplicated fixtures;
- misleading test names;
- dead private helpers;
- stale handoff;
- mixed code/docs commit;
- tests that mutate metadata.

Action:

```text
schedule at the next debt checkpoint
```

### TD-3 — cosmetic or optional

Examples:

- wording;
- formatting;
- minor local naming where public names are stable.

Action:

```text
do not interrupt the current delivery path
```

Only TD-0 and TD-1 block phase progression.

A TD-2 item blocks only when it directly increases the probability of a wrong next-phase implementation.

---

# 14. Refactor schedule

Refactoring is event-based, not continuous random cleanup.

## Checkpoint RF-1 — R3C freeze closure

Scope:

```text
test accuracy
evidence persistence
documentation truth
commit discipline
```

No production architecture rewrite.

## Checkpoint RF-2 — after R3D wiring

Purpose:

```text
remove duplicated validation orchestration
ensure one shared migration/baseline/evaluator sequence
verify result-field forwarding
remove compatibility branches created only for wiring
```

Time budget:

```text
one bounded task
maximum 20% of R3D implementation effort
```

Do not begin R4 until RF-2 passes the focused Runner and persistence tests.

## Checkpoint RF-3 — after R4 metrics

Purpose:

```text
normalize metric naming
remove deprecated internal token aliases where safe
centralize arithmetic identities
ensure no double-counting
```

This is a metrics refactor, not a general codebase cleanup.

## Checkpoint RF-4 — after R5 nine records

Purpose:

```text
remove test-only leakage from production package
verify scripted backend cannot enter provider registry
remove dead experiment setup
compress duplicated report construction
close all TD-0 and TD-1
review TD-2 before bundle
```

This is the final code refactor before R6.

## Checkpoint RF-5 — after R6 bundle

No broad code refactor.

Allowed only:

```text
bundle parity defects
deployment blockers
documentation inconsistencies
```

The goal is to preserve the source that will be run on Kaggle.

## Checkpoint RF-6 — after real Smoke

Do not modify experimental algorithms in response to observed results.

Only:

```text
result-processing defects
record-integrity defects
reproducibility metadata defects
```

may be fixed, with original records preserved.

---

# 15. Technical-debt schedule table

| Checkpoint | Trigger | Debt classes | Maximum scope | Exit evidence |
|---|---|---|---|---|
| R3C closure | before R3C freeze | TD-0/TD-1 plus directly related TD-2 | R3C tests/docs | focused Linux + Windows full suite |
| RF-2 | after R3D self-gates | TD-0/TD-1 in orchestration, selected TD-2 duplication | Runner/Pipeline/persistence only | integration sequence and round trip |
| RF-3 | after R4 self-gates | token/metric TD-0/1/2 | metrics and config only | arithmetic property tests |
| RF-4 | after R5 nine records | all TD-0/1; selected TD-2 | local production proof path | nine records rerun |
| R6 closure | after bundle | deployment TD-0/1 | docs/bundle/parity | source/build hash parity |
| Post-Smoke | after real records | evidence defects only | records/reports | preserved original results |

Do not create a weekly or time-based refactor task. This project is milestone-driven.

---

# 16. Debt register seed

The documentation commit creates:

```text
selective_updates/records/TECHNICAL-DEBT-AND-REFACTOR-SCHEDULE.md
```

Seed it with these items.

## TD-R3C-001 — misleading TOCTOU tests

Severity:

```text
TD-2
```

Closure:

```text
rewrite tests to mutate after validation
```

Checkpoint:

```text
R3C closure
```

## TD-R3C-002 — missing lifecycle regression tests

Severity:

```text
TD-1 because hidden evaluator output is a production contract
```

Closure:

```text
six fake-Django tests
```

## TD-R3C-003 — incomplete permission-layer proof

Severity:

```text
TD-0 scientific contract
```

Closure:

```text
invoke configured permissions
```

## TD-R3C-004 — source-isolation Boolean error

Severity:

```text
TD-1
```

Closure:

```text
single absence helper
```

## TD-R3C-005 — tests mutate hash metadata

Severity:

```text
TD-2
```

Closure:

```text
metadata required and read-only
```

## TD-PROCESS-001 — code/docs commit mixing

Severity:

```text
TD-2
```

Closure:

```text
explicit staging and report proof
```

## TD-PROCESS-002 — empty documentation commit

Severity:

```text
TD-2
```

Closure:

```text
cached diff required before commit
```

## TD-PROCESS-003 — actual model mismatch

Severity:

```text
TD-1 process-control
```

Closure:

```text
model preflight and footer truth
```

---

# 17. Productivity measurements

Every phase records:

```text
planned files
actual files
planned public APIs
actual public APIs
test cases planned
test cases added
integration runs planned
integration runs executed
focused failures before commit
compile failures before commit
post-commit defects
audit cycles
elapsed time
```

## 17.1 Targets

R3D onward:

```text
architecture deviations: 0
unplanned production files: 0
empty commits: 0
false clean-tree claims: 0
model identity mismatches: 0
one implementation cycle
one independent audit cycle
```

## 17.2 Test quality metrics

Do not optimize only for test count.

Track:

```text
public-path coverage
state-transition coverage
negative equivalence classes
combined adversarial cases
cross-platform-required cases
integration boundary count
test-name/assertion match
```

## 17.3 Documentation quality metrics

Track:

```text
current report accuracy
handoff current HEAD
next phase correct
blocked phases correct
artifact table complete
known limitations factual
```

---

# 18. Stop conditions

OpenCode stops without improvisation when:

```text
actual model is not requested model;
HEAD differs;
tree is dirty before work;
authorized file is missing;
an unplanned production file is required;
a frozen public API must change;
a focused test reveals a contract contradiction;
full suite has a failure;
code commit staging contains documentation;
documentation commit staging is empty.
```

Use:

```text
PHASE_BLOCKED

actual model:
HEAD:
dirty files:
first failing command:
reason:
no changes made after blocker:
```

---

# 19. Immediate OpenCode execution order

## Step 1 — preflight

Print:

```text
actual active model
branch
HEAD
status
```

Stop on mismatch.

## Step 2 — tests only

Correct the TOCTOU tests.

Add source-isolation helper tests.

Add six lifecycle tests.

Strengthen permission proof.

Do not edit production code unless a corrected test fails against production behavior.

## Step 3 — smallest focused runs

Run:

```powershell
python -m pytest tests/unit/execution/test_scenario_evaluator.py -q
python -m pytest tests/integration/test_todo_smoke_evaluator_assets.py -k "lifecycle or source_isolation or permission" -q
```

## Step 4 — complete integration

Run all evaluator integration tests.

## Step 5 — adjacent R3B proof

Run:

```powershell
python -m pytest `
  tests/unit/execution/test_scenario_evaluator.py `
  tests/integration/test_todo_smoke_evaluator_assets.py `
  tests/unit/execution/test_post_generation.py `
  -q
```

## Step 6 — full gates

Run full suite and static checks.

## Step 7 — bounded refactor review

Review only the four authorized code/test files.

No new architecture.

## Step 8 — code commit

Explicit staging.

## Step 9 — documentation and detailed report

Write the complete report verbatim to file and response.

Create debt register.

Update current handoff and V2 state.

## Step 10 — documentation commit

Explicit staging.

Verify clean tree.

Stop.

---

# 20. Exact commands

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
  tests/unit/execution/test_scenario_evaluator.py `
  tests/integration/test_todo_smoke_evaluator_assets.py `
  tests/evaluator_assets/todo_smoke_003_checks.py `
  tests/support/evaluator_fixture_workspaces.py

python -m compileall `
  tests/unit/execution/test_scenario_evaluator.py `
  tests/integration/test_todo_smoke_evaluator_assets.py `
  tests/evaluator_assets

git diff --check
git diff --name-only
git diff --stat
git status --short
```

When production `scenario_evaluator.py` changes, additionally run:

```powershell
ruff check src/benchmark/execution/scenario_evaluator.py
mypy --strict src/benchmark/execution/scenario_evaluator.py
python -m py_compile src/benchmark/execution/scenario_evaluator.py
```

---

# 21. Exact commit messages

Code/test commit:

```text
test(validation): close R3C freeze evidence gaps
```

When production code changes:

```text
fix(validation): close R3C freeze evidence gaps
```

Documentation commit:

```text
docs(audit): freeze R3C evidence and delivery protocol
```

---

# 22. Final status after independent acceptance

Expected:

```text
R1 Repository Agent                  accepted
R2 Selective                         accepted
R3A Scenario metadata               accepted
R3B Migration runner                accepted and frozen
R3C Evaluator system                accepted and frozen
R3D Runner wiring                   next
R4 Token and metrics                pending
R5 Nine local records               pending
R6 Bundle and push                  pending
Kaggle                              blocked
Stable tag                          blocked
Pilot                               blocked
```

No tag is created at R3C.

---

# 23. Exact short prompt for OpenCode

```text
Use:

DeepSeek V4 Flash Free
Provider: OpenCode Zen
Mode: Build

Print the actual active model before reading or editing.

If the actual model is not DeepSeek V4 Flash Free, make no changes and end:

MODEL_MISMATCH_NO_CHANGES

Branch:

experiment/three-arm-smoke-v2

Current HEAD:

36e396d

Read completely:

docs/R3C_FREEZE_CLOSURE_AND_DELIVERY_ACCELERATION_PROTOCOL.md

Execute the R3C freeze closure only.

Do not start R3D.

Correct the evidence and semantic gaps exactly as specified:

- make TOCTOU tests validate first and mutate second;
- delete or rewrite the invalid inode-based regular replacement test;
- invoke configured Task permission classes for owner/non-owner POST proof;
- correct source-isolation Boolean logic through one helper;
- add all six fake-Django lifecycle tests;
- make evaluator hash tests read-only;
- print and persist the complete 1,200–2,000-word report;
- create and track the technical-debt/refactor schedule;
- enforce a code/test-only commit followed by a docs-only commit;
- never create an empty commit.

Do not modify R3B, Runner, Pipeline, scenario YAML, README, bundle, notebook,
Selective, Agent, or metrics.

Run every focused, integration, adjacent, full, and static gate in the protocol.

Create:

test(validation): close R3C freeze evidence gaps

Use fix(validation) only when production code changes.

Then create:

docs(audit): freeze R3C evidence and delivery protocol

Print the complete detailed report in the response and save the same report to:

reports/latest_phase_report.md

Require git status --short to print no output.

End exactly:

R3C_FREEZE_CLOSURE_AUDIT_REQUIRED
```

---


# Appendix K — Complete R3C freeze evidence matrix

This matrix is binding for the immediate closure. OpenCode must map every row to
one test name in the detailed report. Rows marked “public” must call the public
runner. Rows marked “trust transition” must retain a validated request and then
mutate the filesystem.

## K.1 Input boundary

| ID | Case | Level | Required result |
|---|---|---|---|
| K-001 | valid canonical root, asset, workspace | public | evaluator may execute |
| K-002 | canonical root missing | public | typed validation failure |
| K-003 | canonical root is a file | public | typed validation failure |
| K-004 | evaluator root missing | validation | typed failure |
| K-005 | evaluator root is ordinary symlink | validation | typed failure |
| K-006 | asset empty | validation | typed failure |
| K-007 | asset whitespace | validation | typed failure |
| K-008 | asset contains NUL | validation | typed failure |
| K-009 | asset contains backslash | validation | typed failure |
| K-010 | asset absolute | validation | typed failure |
| K-011 | asset traversal | validation | typed failure |
| K-012 | asset wrong suffix | validation | typed failure |
| K-013 | asset missing | validation | typed failure |
| K-014 | asset lexical symlink | public | typed failure |
| K-015 | asset parent symlink | validation | typed failure |
| K-016 | workspace missing | public | typed failure |
| K-017 | workspace file | public | typed failure |
| K-018 | workspace equals canonical root | public | typed failure |
| K-019 | workspace nested in canonical root | public | typed failure |
| K-020 | canonical root nested in workspace | public | typed failure |
| K-021 | workspace evaluator directory | public | typed failure |
| K-022 | workspace evaluator file | public | typed failure |
| K-023 | workspace working evaluator symlink | public | typed failure |
| K-024 | workspace broken evaluator symlink | public | typed failure |
| K-025 | empty Python executable | validation | typed failure |
| K-026 | Python executable NUL | validation | typed failure |
| K-027 | timeout bool/float/string/null | validation | typed failure |
| K-028 | timeout zero/negative | validation | typed failure |

## K.2 Trust transitions

| ID | Transition | Required test sequence | Required result |
|---|---|---|---|
| K-101 | asset becomes external symlink | validate → mutate → load | rejected at trust |
| K-102 | asset becomes internal symlink | validate → mutate → load | rejected at trust |
| K-103 | evaluator root becomes symlink | validate → remove directory safely → symlink → load | rejected |
| K-104 | asset deleted | validate → delete → load | rejected |
| K-105 | evaluator root deleted | validate → delete root → load | rejected |
| K-106 | ordinary source changes before trust | validate → modify same ordinary path → load | new bytes trusted |
| K-107 | source changes after trust | load trusted bytes → modify source → execute | frozen trusted bytes copied |
| K-108 | copied file differs | trusted bytes → corrupt copy verification | typed hash failure |

The difference between K-106 and K-107 must be explicit:

- before trust, the latest valid ordinary content is the trusted asset;
- after trust, copied execution uses the frozen bytes.

Do not require inode identity.

## K.3 Subprocess boundary

| ID | Case | Required result |
|---|---|---|
| K-201 | exact success command | exact argv/cwd/env/options |
| K-202 | exit 1 with valid failed payload | public failure preserving payload |
| K-203 | exit non-zero with passed payload | public failure |
| K-204 | timeout string output | typed failure and text preserved |
| K-205 | timeout byte output | typed failure and decoded text |
| K-206 | command missing | typed failure |
| K-207 | ValueError | typed failure |
| K-208 | OSError | typed failure |
| K-209 | SubprocessError | typed failure |
| K-210 | temporary directory creation failure | typed failure |
| K-211 | copy write failure | typed failure |
| K-212 | copied read failure | typed failure |
| K-213 | copied hash mismatch | typed failure |
| K-214 | temp directory inside workspace | rejected |
| K-215 | temp directory inside canonical root | rejected |
| K-216 | temp cleanup after success | path absent |
| K-217 | temp cleanup after failure | path absent |
| K-218 | only selected asset copied | exact temp contents |
| K-219 | evaluator never written to workspace | absence helper passes |

## K.4 Payload boundary

| ID | Payload state | Required result |
|---|---|---|
| K-301 | exact valid object | parsed |
| K-302 | surrounding whitespace | parsed |
| K-303 | extra stdout before JSON | rejected |
| K-304 | extra stdout after JSON | rejected |
| K-305 | empty stdout | rejected |
| K-306 | malformed JSON | rejected |
| K-307 | array/string/null top level | rejected |
| K-308 | missing passed | rejected |
| K-309 | missing checks | rejected |
| K-310 | missing error | rejected |
| K-311 | unknown key | rejected |
| K-312 | passed wrong type | rejected |
| K-313 | checks wrong type | rejected |
| K-314 | check item wrong type | rejected |
| K-315 | empty check | rejected |
| K-316 | duplicate check | rejected |
| K-317 | error wrong type | rejected |
| K-318 | passed true + error text | rejected |
| K-319 | passed false + empty error | rejected |
| K-320 | passed true + empty checks | final failure |

## K.5 Evaluator lifecycle

Each evaluator asset must pass every row.

| ID | Stage | Injected failure | Required stdout |
|---|---|---|---|
| K-401 | argv | wrong argument count | one failed JSON |
| K-402 | workspace | missing manage.py | one failed JSON |
| K-403 | workspace | missing settings.py | one failed JSON |
| K-404 | workspace | missing todo directory | one failed JSON |
| K-405 | django import | ImportError | one failed JSON |
| K-406 | django setup | RuntimeError | one failed JSON |
| K-407 | setup environment | RuntimeError | one failed JSON |
| K-408 | setup database | RuntimeError | one failed JSON |
| K-409 | semantic check | AssertionError | one failed JSON with check name |
| K-410 | semantic check | unexpected exception | one failed JSON with check name |
| K-411 | teardown database | RuntimeError | one failed JSON with teardown diagnostic |
| K-412 | teardown environment | RuntimeError | one failed JSON with teardown diagnostic |
| K-413 | setup + teardown | both fail | one failed JSON containing both |
| K-414 | all checks pass | none | one passed JSON |

The immediate closure persists K-408 and K-413 for all three assets. Other rows
may remain covered through common structure and existing real integration, but
the final report must state which rows are direct tests and which are source
inspection.

## K.6 Smoke 001 semantic matrix

| Check | Required proof |
|---|---|
| task_priority_enum | nested TextChoices, exact values, no extras |
| task_priority_field | field exists, exact choices, default MEDIUM |
| task_priority_default | model create without value stores MEDIUM |
| task_priority_valid_values | serializer and API accept three values |
| task_serializer_priority | writable exact ChoiceField semantics |
| task_priority_invalid_rejected | serializer and API reject URGENT |
| task_priority_filter | HIGH included, MEDIUM/LOW excluded |
| task_unfiltered_list | all created control IDs present |
| baseline_task_fields | title, description, status, owner, project, tags, timestamps |
| project_and_tag_regression | frozen models, serializers, create/read, duplicate Tag rejection |

Negative variants:

```text
wrong_default → task_priority_default
missing_filter → task_priority_filter
invalid_serializer_choice → task_serializer_priority
```

## K.7 Smoke 002 semantic matrix

| Check | Required proof |
|---|---|
| soft_delete_retains_row | `_base_manager` row remains |
| soft_delete_sets_timestamp | deleted_at non-null |
| default_manager_excludes_deleted | target absent |
| normal_list_excludes_deleted | target absent, active present |
| deleted_detail_is_404 | exact 404 |
| deleted_action_lists_deleted | target present, active absent |
| restore_action_restores | timestamp cleared, list/detail restored |
| soft_deleted_data_preserved | title, description, status, project, tags |
| project_and_tag_regression | frozen model/serializer/API behavior |

Negative variants:

```text
hard_delete → soft_delete_retains_row
deleted_visible_in_normal_list → default_manager_excludes_deleted
restore_keeps_timestamp → restore_action_restores
```

## K.8 Smoke 003 semantic matrix

| Check | Required proof |
|---|---|
| project_owner_field | ForeignKey to configured user |
| project_creator_becomes_owner | API creator, override blocked |
| project_owner_read_only | serializer field read-only |
| project_owner_can_write | owner update/delete |
| project_non_owner_forbidden | non-owner update/delete 403; create allowed |
| task_create_uses_project_owner | API behavior and configured permission proof |
| task_update_uses_project_owner | conflict with legacy Task.owner |
| task_delete_uses_project_owner | conflict with legacy Task.owner |
| authenticated_reads_unrestricted | list and retrieve Project/Task/Tag |
| tag_permissions_unchanged | create non-staff, object writes staff-only |

Negative variants:

```text
task_owner_authority → task_update_uses_project_owner
project_non_owner_write_allowed → project_non_owner_forbidden
project_owner_writable → project_owner_read_only
```

# Appendix L — R3D preliminary artifact and dependency map

This appendix is planning only. R3D is not authorized by the immediate prompt.
It exists to prevent a future broad repository search.

## L.1 Expected production artifacts

```text
src/benchmark/execution/runner.py
src/benchmark/execution/pipeline.py
src/benchmark/core/models.py
src/benchmark/checkpoint/persistence.py
src/benchmark/statistics/reporting.py
seven_arm_benchmark.py
```

Potential adjacent production artifact:

```text
src/benchmark/execution/validation.py
```

Read it but modify only if baseline validation cannot be represented through
the existing API.

## L.2 Expected test artifacts

```text
tests/unit/execution/test_runner.py
tests/unit/execution/test_pipeline.py
tests/unit/test_models.py
tests/unit/test_checkpoint.py
tests/unit/statistics/test_reporting.py
tests/contract/test_three_arm_core.py
tests/integration/test_scientific_smoke_v1_fixes.py
tests/integration/test_su0010a_regeneration.py
tests/integration/test_su0011_iterative_agent.py
```

One new focused integration file may be authorized in the R3D master spec.

## L.3 Exact production dependency chain

```text
ScenarioModel
→ Scenario
→ PipelineConfig
→ RunnerConfig
→ BenchmarkRunner
→ SharedRegenerationExecutor
→ run_post_generation_command
→ FunctionalValidator
→ run_scenario_evaluator
→ RunRecord
→ RunRecordData
→ RunRecordStore
→ reports
```

Every arrow receives a focused test.

## L.4 R3D success sequence

```text
generation guard
→ migration
→ baseline validation
→ scenario evaluator
→ optional bounded repair
→ final typed record
```

The sequence must be one private Runner method.

Every arm and repair path calls the same method.

## L.5 R3D failure stages

```text
generation_guard
regeneration
migration_generation
baseline_validation
scenario_evaluator
configuration
budget
```

The stage name is persisted.

## L.6 R3D integration matrix

Minimum:

| Arm/path | Migration | Baseline | Evaluator | Expected |
|---|---|---|---|---|
| Monolithic initial | pass | pass | pass | success |
| Selective initial | pass | pass | pass | success |
| Agent initial | pass | pass | pass | success |
| Monolithic repair | fail then pass | pass | pass | repaired success |
| Selective repair | pass | fail then pass | pass | repaired success |
| Agent revision | pass | pass | fail then pass | repaired success |
| any | fail | skipped | skipped | failure |
| any | pass | fail | skipped | failure |
| any | pass | pass | fail | failure |

## L.7 R3D debt checkpoint

After R3D tests pass, RF-2 checks:

- duplicated validation calls;
- missing stage forwarding;
- old functional-validation naming;
- compatibility mirrors;
- repair feedback duplication;
- Agent call-count handling;
- persistence defaults;
- report serialization.

No unrelated codebase cleanup.

# Appendix M — R4, R5, and R6 acceleration plan

## M.1 R4 token and metric contract

R4 should be one phase with one metrics master file.

Frozen names:

```text
max_completion_tokens_per_call
max_total_workflow_tokens
selection_*
regeneration_*
repair_*
migration_*
baseline_validation_*
scenario_evaluator_*
total_workflow_*
```

Required property tests:

```text
total tokens equal stage sum
total calls equal stage sum
total duration equals non-overlapping stage sum
selection revisions are incremental
tool duration is not double-counted
per-call completion limit remains 4096
unlimited total does not shrink later calls
```

RF-3 occurs before R4 documentation commit.

## M.2 R5 nine-record production proof

R5 uses:

```text
3 scenarios × 3 arms × 1 repetition
```

Every record must be non-dry and must traverse:

```text
selection
generation
migration
baseline
evaluator
persistence
```

Use the scripted backend only as deterministic model output.

R5 proof is not a model-quality result.

RF-4 follows the first successful nine-record run, then the same nine-record
test is rerun after cleanup.

## M.3 R6 deployment

R6 is documentation, bundle, parity, and push.

No broad refactor.

Required:

```text
canonical source equals generated bundle
no test backend in bundle
no local absolute path
no untracked file
local HEAD equals remote HEAD
real Kaggle not launched automatically
```

# Appendix N — Verbatim detailed-report template

OpenCode should fill this template rather than invent a shorter report.

```markdown
# R3C Freeze Closure Detailed Report

## A. Model identity

Requested model:
Actual footer model:
Provider:
Mode:
Elapsed time:

## B. Git identity

Branch:
Starting HEAD:
Code/test commit:
Documentation commit:
Final HEAD:
Working tree:

## C. Objective and boundaries

[Five to eight sentences.]

## D. Artifact-by-artifact modifications

| File | Before | After | Reason | Dependencies | Tests |
|---|---|---|---|---|---|

## E. State-machine evidence

validation
→ live trust
→ frozen bytes
→ copy/hash
→ subprocess
→ payload
→ public result

[Explain every state.]

## F. Scenario evaluator semantics

### Smoke 001
[Ten checks and three variants.]

### Smoke 002
[Nine checks and three variants.]

### Smoke 003
[Ten checks and three variants.]

## G. Twelve fixture outcomes

| Scenario | Variant | Pass | Exit | Checks/error | Migration | Old hashes | Isolation |
|---|---|---:|---:|---|---|---|---|

## H. Six lifecycle outcomes

| Asset | Mode | Exit | JSON | Error |
|---|---|---:|---:|---|

## I. Failure matrix

| Failure | Test | Expected | Actual |
|---|---|---|---|

## J. Incremental build history

| Order | Command | Result | Action |
|---:|---|---|---|

## K. Final gates

| Command | Result |
|---|---|

## L. Commit scope

[Print exact Git commands and output.]

## M. Documentation updates

| File | Exact current-state change |
|---|---|

## N. Technical debt

Debt closed:
Debt deferred:
Debt introduced:

## O. Productivity

Planned files:
Actual files:
Focused failures:
Compile failures:
Elapsed:
Audit cycles:

## P. Authorization

R3B:
R3C:
R3D:
Kaggle:
Tag:
Pilot:

R3C_FREEZE_CLOSURE_AUDIT_REQUIRED
```

# Appendix O — Productivity failure diagnosis

Low productivity is diagnosed from evidence, not mood.

## O.1 Architecture churn

Indicator:

```text
same public behavior implemented through more than two structural rewrites
```

Action:

```text
stop patches
create one state model
freeze after audit
```

## O.2 Test churn

Indicator:

```text
test count rises but the same bug class recurs
```

Action:

```text
replace example list with a truth table
```

## O.3 Naming churn

Indicator:

```text
same concept renamed more than once in one phase
```

Action:

```text
freeze naming before implementation
```

## O.4 Documentation churn

Indicator:

```text
current report includes historical rejected content
```

Action:

```text
latest report current-only; history in records
```

## O.5 Model mismatch

Indicator:

```text
requested model differs from footer
```

Action:

```text
no-change stop before work
```

## O.6 Broad search cost

Indicator:

```text
OpenCode reads more than planned artifacts before first edit
```

Action:

```text
exact read order and dependency map
```

## O.7 Late compile failures

Indicator:

```text
compile first occurs after multiple files are written
```

Action:

```text
compile after every Python artifact
```

## O.8 Repeated audit cycles

Indicator:

```text
more than one independent correction cycle per phase
```

Action:

```text
root-cause correction and mandatory debt checkpoint
```

# Appendix P — Phase velocity dashboard

The technical-debt record should include this table after every phase.

| Metric | Target | Actual | Pass |
|---|---:|---:|---:|
| planned production files | exact | | |
| unplanned production files | 0 | | |
| naming deviations | 0 | | |
| compile failures after commit | 0 | | |
| empty commits | 0 | | |
| false clean claims | 0 | | |
| detailed report printed | 1 | | |
| detailed report persisted | 1 | | |
| independent correction cycles | ≤1 | | |
| TD-0 open at phase exit | 0 | | |
| TD-1 open at phase exit | 0 | | |
| full-suite failures | 0 | | |

The dashboard is a process metric. It must not be mixed with the scientific
experiment record.

# Appendix Q — Final researcher decision rule

Authorize the next phase only when:

```text
model footer truthful
code scope truthful
docs scope truthful
full suite green
focused cross-platform evidence green
detailed report present
technical debt register current
independent audit accepts
```

Do not authorize the next phase because OpenCode says “unblocked.”

The independent audit decision is authoritative.


**End of authoritative protocol.**


# Appendix A — Detailed artifact inspection checklist

This appendix is used before the code commit. Every answer must be recorded in
the detailed report.

## A.1 `tests/unit/execution/test_scenario_evaluator.py`

Inspect:

- every test name;
- the exact operation performed before the assertion;
- whether the public function or private helper is appropriate;
- whether a test can pass because of an unrelated failure;
- whether a platform skip is the only evidence;
- whether the test mutates before or after validation;
- whether patched functions are restored;
- whether filesystem cleanup is automatic;
- whether the assertion proves the declared state transition.

Required questions:

1. Does every “after validation” test call `_validate_evaluator_request` first?
2. Does it retain the returned request?
3. Does it mutate after request construction?
4. Does it call `_load_trusted_evaluator_asset` on the retained request?
5. Does it assert a specific trust diagnostic?
6. Is there a platform-independent synthetic equivalent?
7. Does the ordinary trusted-bytes test prove frozen content?
8. Do subprocess tests assert the exact copied path?
9. Do copy-failure tests induce the named failure?
10. Does every failed outcome have exit code -1?

## A.2 `tests/integration/test_todo_smoke_evaluator_assets.py`

Inspect:

- helper source isolation;
- baseline hashes;
- migration hashes;
- new migration count;
- evaluator canonical hash;
- lifecycle fake workspace;
- exact stdout;
- negative expected check;
- correct exact check tuple;
- exit code.

Required questions:

1. Is evaluator absence expressed with AND rather than OR?
2. Is broken-symlink absence checked?
3. Does every one of twelve variants run the integrity helper?
4. Does every negative result have non-zero exit?
5. Does every negative identify the intended check?
6. Does every correct result have exact check ordering?
7. Does no test write repository metadata?
8. Do lifecycle tests avoid requiring Django?
9. Are temporary workspaces isolated by test?
10. Does test collection avoid evaluator scripts?

## A.3 `tests/evaluator_assets/todo_smoke_003_checks.py`

Inspect:

- top-level exception behavior;
- teardown behavior;
- permission proof;
- owner and non-owner requests;
- Project owner override;
- object-level authority;
- Task create authority;
- Tag baseline permissions;
- list and retrieve reads.

Required questions:

1. Does Task create denial come from configured permission classes?
2. Does the evaluator call those permission objects?
3. Can a view-only denial pass?
4. Does the project owner pass permission checks?
5. Does the other user fail at least one permission?
6. Are Task update and delete tested with conflicting legacy owner?
7. Are Project and Task list/retrieve unrestricted?
8. Are Tag list/retrieve unrestricted?
9. Does non-staff Tag update/delete remain forbidden?
10. Does staff Tag update remain allowed?

## A.4 `tests/support/evaluator_fixture_workspaces.py`

Inspect:

- correct Smoke 003 permission class;
- Task view `perform_create`;
- one-fault source variant;
- migration runner;
- source dictionaries.

Required questions:

1. Is authorization absent from TaskViewSet `perform_create`?
2. Is POST ownership in a permission class?
3. Does task-owner negative change one file?
4. Does every replacement occur exactly once?
5. Does every builder use R3B?
6. Are old migrations untouched?
7. Does every variant create one new migration?
8. Is no evaluator asset copied?
9. Are correct source dictionaries the only source of truth?
10. Does no baseline source get edited in place?

# Appendix B — Technical-debt review checklist

At every scheduled checkpoint, review these categories.

## B.1 Scientific debt

- hidden information entering strategy input;
- evaluator text entering generation context;
- Ground Truth entering selection;
- unequal model settings;
- cumulative workspaces;
- failed records discarded;
- algorithm tuning after results;
- dry-run counted as execution.

## B.2 Production-path debt

- module exists but is not wired;
- field exists in core model but is dropped by wrapper;
- persistence defaults hide missing fields;
- validation skipped on repair;
- Agent path differs from other arms after selection;
- subprocess runs in wrong cwd;
- snapshot mutable;
- migration count not enforced.

## B.3 Test debt

- test name does not match assertions;
- private helper tested but public composition untested;
- negative fixture has multiple defects;
- test accepts multiple unrelated results;
- assertion guarded by `if` and may disappear;
- test mutates source repository;
- platform skip is only evidence;
- mocks replace the complete behavior under test.

## B.4 Documentation debt

- current HEAD wrong;
- current count stale;
- next phase wrong;
- blocked phase marked unblocked;
- detailed report missing;
- rejected design appended to current report;
- file reference untracked;
- empty documentation commit;
- commit claims files not present.

## B.5 Architectural debt

- one function owns too many states;
- error text and trust Boolean separate;
- duplicated source fixtures;
- public names drift;
- compatibility alias used by new code;
- generic framework added for one phase;
- mutable global state in test support;
- production imports test code.

# Appendix C — R3D readiness preflight

R3D must not start until R3C is accepted.

When it starts, the planning document must identify these exact dependency
edges:

```text
ScenarioModel.evaluator_asset
→ core Scenario
→ PipelineConfig canonical project root
→ RunnerConfig canonical project root
→ BenchmarkRunner validation helper
→ run_post_generation_command
→ FunctionalValidator baseline command
→ run_scenario_evaluator
→ RunRecord stage fields
→ RunRecordData
→ JSONL persistence
→ reports
```

R3D must use one validation sequence for:

```text
Monolithic initial
Selective initial
Monolithic repair
Selective repair
Repository Agent initial
Repository Agent revision
```

The next plan must list exact files before editing:

```text
runner.py
pipeline.py
core models
persistence
reporting
entry point
focused tests
integration tests
```

R3D must not begin with a broad repository search.

# Appendix D — Refactor decision rules

Perform a refactor only when at least one condition holds:

1. two production branches implement the same state transition;
2. a trust result and error text can diverge;
3. a public field is reconstructed in three or more places;
4. a fixture source is duplicated across variants;
5. a compatibility alias is used by new V2 code;
6. a function cannot be tested without mocking unrelated behavior;
7. a bug class recurs twice because state ownership is unclear.

Do not refactor when:

1. the only benefit is fewer lines;
2. code is old but stable and outside the path;
3. the phase is about to run the real experiment;
4. a hypothetical future repository may need the abstraction;
5. naming preference is the only concern;
6. test data is verbose but accurately represents different semantics.

# Appendix E — Daily operating checklist for the researcher

Before sending a phase prompt:

- confirm selected model in UI;
- confirm branch;
- confirm HEAD;
- confirm clean tree;
- place the master spec at the exact path;
- confirm the spec is tracked or will be tracked;
- ensure the prompt authorizes one phase only.

After OpenCode returns:

- read the footer model;
- compare reported model to footer;
- inspect git status;
- inspect git log;
- inspect code and docs commit file scopes;
- run full suite on Windows;
- export a fresh ZIP;
- request independent audit;
- do not authorize next phase from OpenCode’s self-report.

After independent acceptance:

- update handoff status;
- freeze the phase;
- start the next master spec;
- do not create a stable tag unless the release criteria are met.

# Appendix F — Detailed report scoring rubric

Score each category from 0 to 2.

## Model truth

0: model absent or false  
1: requested model only  
2: requested and footer model both present and consistent

## Git truth

0: no commits/status  
1: commits but no scope proof  
2: commits, scope proof, and clean tree

## Artifact explanation

0: “implemented/refactored” only  
1: files listed  
2: before/after/reason/dependencies/tests for every file

## State-machine explanation

0: absent  
1: names only  
2: inputs, outputs, failure representation for every state

## Test evidence

0: test count only  
1: focused and full counts  
2: failure matrix, integration runs, direct adversarial evidence

## Documentation truth

0: stale or contradictory  
1: current status only  
2: exact updates plus limitations and next blocked phase

## Technical debt

0: ignored  
1: generic “none”  
2: closed, deferred, and newly introduced items with IDs

A report scoring below 12 of 14 is rejected.

# Appendix G — Definition of done by phase

A phase is complete only when:

```text
contract is frozen
implementation uses canonical path
unit matrix passes
integration path passes
cross-platform-required evidence passes
code commit has exact scope
documentation commit has exact scope
working tree is clean
detailed report is printed and persisted
independent audit accepts
```

A green full suite alone is not definition of done.

# Appendix H — No-repeat policy

After R3C is accepted:

- no further R3C edge-case search;
- no R3C refactor for style;
- no evaluator check expansion;
- no fixture architecture changes;
- no hash metadata changes;

unless R3D exposes a reproducible contract failure.

This prevents audit from becoming unlimited exploratory hardening.

# Appendix I — Fast-path principles

Speed comes from reducing rework, not removing validation.

Use:

```text
one phase
one master spec
one artifact map
one state machine
one failure matrix
one integration path
one code commit
one docs commit
one independent audit
```

Avoid:

```text
large vague prompt
broad repository search
naming invention
happy-path-only tests
late compile
self-declared independent acceptance
multiple micro-patches without root analysis
```

# Appendix J — Evidence bundle for a new conversation

A new AI or account needs:

```text
branch name
current HEAD
last accepted phase
current phase code commit
current phase docs commit
master spec
latest detailed report
project handoff
technical debt register
full-suite output
independent audit decision
```

The handoff must not depend on conversation memory.

