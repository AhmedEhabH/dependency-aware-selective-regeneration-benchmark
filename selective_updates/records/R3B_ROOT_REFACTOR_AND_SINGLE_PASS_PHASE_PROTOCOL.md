# R3B Root Refactor and Single-Pass Phase Delivery Protocol

**Document type:** Authoritative engineering correction and workflow contract  
**Target branch:** `experiment/three-arm-smoke-v2`  
**Audited branch HEAD:** `fddd26f`  
**Audited R3B acceptance-closure code commit:** `f8faa08`  
**Independent review model:** GPT-5.6 Thinking  
**Required OpenCode model:** DeepSeek V4 Flash Free through OpenCode Zen, Build mode  
**Real scientific model later:** Qwen2.5-Coder-7B-Instruct on Kaggle  
**R3C:** blocked until the bounded R3B root refactor passes independent review  
**Kaggle, Pilot, merge, and stable tag:** blocked  

---

## 1. Executive decision

The researcher’s concern is correct: R3B evolved through a sequence of narrow corrections. Each correction fixed a real defect, but the implementation and audit process became reactive:

```text
implement
→ discover one missed failure mode
→ patch one boolean or validation branch
→ add tests
→ discover another missed failure mode
```

The correct response is not another isolated one-line patch. It is also not a broad rewrite of the benchmark.

The required action is one **bounded root refactor** of `post_generation.py` that preserves its public API but reorganizes the internal logic around explicit trusted states:

```text
validated request
→ trusted before snapshot
→ typed command outcome
→ trusted after snapshot
→ deterministic migration delta
→ one final success decision
```

The refactor must eliminate the class of defect in which an error is collected as diagnostic text but forgotten in the success boolean.

After this refactor, R3B should be frozen. Further speculative hardening is forbidden. R3B may be reopened only if R3D production integration reveals a reproducible defect.

The second part of this document changes the workflow for every future phase. R3C and later phases must begin with a complete failure matrix, state-transition contract, and adversarial tests. OpenCode must not declare a phase complete merely because the original focused tests and full suite are green.

---

## 2. Independent audit of the current checkpoint

The current checkpoint has strong evidence:

```text
Windows full suite supplied by researcher:
1279 passed, 17 skipped

Independent Linux focused suite:
81 passed
```

The latest corrections successfully cover:

- relative workspace paths;
- directory-prefix containment;
- migration-file symlinks;
- numbered migration filenames;
- timeout type validation;
- malformed command values;
- NUL rejection;
- timeout after-state inspection;
- subprocess exception conversion;
- filesystem read failures;
- after-snapshot error fatality;
- whitespace-only migration-directory rejection.

The Git tree in the supplied archive is clean. The three audit records are tracked.

However, the implementation remains structurally fragile.

### 2.1 Current structural weaknesses

The public function currently performs all of these responsibilities:

1. validates primitive input;
2. resolves workspace paths;
3. resolves the migration directory;
4. snapshots files;
5. hashes files;
6. launches a subprocess;
7. normalizes subprocess errors;
8. snapshots again;
9. compares old files;
10. filters new migration names;
11. builds diagnostics;
12. calculates success;
13. translates success into exit-code semantics;
14. constructs the result.

This is too many responsibilities for one mutable control flow.

Other warning signs:

- `_validate_inputs` returns either a tuple or a string;
- `_snapshot_migrations` returns a dictionary plus a separate errors tuple;
- trust is inferred by callers rather than represented in the snapshot;
- the validated resolved migration path is returned but discarded as `_resolved`;
- the migration directory is resolved again later from the original string;
- multiple booleans are mutated independently;
- command failure and integrity failure use partially different return paths;
- success is derived through sequential mutation rather than one explicit expression;
- the tests grew around discovered branches instead of one defined state matrix;
- documentation declared “independent audit satisfied” before the independent auditor reviewed the final commit.

These issues explain why each local fix could be correct while another combination remained untested.

### 2.2 A remaining directly reproduced edge

The independent audit also reproduced this current behavior:

```text
before:
  migration directory exists but contains no Python files

subprocess:
  deletes the migration directory

require_new_migration=False

current result:
  passed=True
  existing_migrations_unchanged=True
```

The real Todo baseline has `__init__.py`, so this does not invalidate the immediate Smoke baseline. It does prove that the snapshot helper treats a missing after-state directory as an empty trusted snapshot.

This is the last concrete example needed to justify the root refactor. The fix must come from the trusted-snapshot model, not a special `if directory_missing` patch in the public function.

---

## 3. Refactor boundaries

### 3.1 Preserve the public API

Do not rename:

```python
@dataclass(frozen=True)
class PostGenerationResult:
    passed: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    created_paths: tuple[str, ...] = ()
    existing_migrations_unchanged: bool = False
```

Do not rename:

```python
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

Do not change scenario YAML. Do not wire Runner. Do not start R3C.

### 3.2 Authorized production file

Modify only:

```text
src/benchmark/execution/post_generation.py
```

### 3.3 Authorized test file

Modify only:

```text
tests/unit/execution/test_post_generation.py
```

### 3.4 Authorized state files after the code commit

```text
docs/PROJECT_HANDOFF.md
reports/latest_phase_report.md
docs/V2_R3B_TO_KAGGLE_NO_DISCRETION_EXECUTION_SPEC.md
selective_updates/CHANGE_INDEX.md
selective_updates/records/R3B-ROOT-REFACTOR-AND-SINGLE-PASS-PHASE-PROTOCOL.md
```

### 3.5 Forbidden scope

Do not modify:

- `runner.py`;
- `pipeline.py`;
- core models;
- scenario models or YAML;
- evaluator assets;
- Selective;
- Repository Agent;
- token accounting;
- README;
- Kaggle bundle;
- notebooks;
- dependencies.

---

## 4. Target internal design

The refactor should use a few small private immutable structures. These are not a new framework. They represent the states already present in the function.

### 4.1 Validated request

Create:

```python
@dataclass(frozen=True)
class _ValidatedPostGenerationRequest:
    workspace_root: Path
    migration_directory_path: Path
    migration_directory_relative: str
    command: tuple[str, ...]
    require_new_migration: bool
    timeout: int
```

The validator should return:

```python
_ValidatedPostGenerationRequest | str
```

Returning a typed request removes repeated normalization.

Required properties:

- workspace root is absolute and resolved;
- migration path is the lexical expected location beneath workspace;
- migration relative path is normalized POSIX;
- command is frozen as a tuple;
- timeout is a positive non-bool integer;
- `require_new_migration` is bool.

The field `migration_directory_path` should remain the lexical path:

```python
workspace_root / migration_directory_relative
```

Snapshotting must validate its actual state each time. Do not permanently trust the resolution performed before the subprocess, because the subprocess can change or replace the directory.

### 4.2 Trusted migration snapshot

Create:

```python
@dataclass(frozen=True)
class _MigrationSnapshot:
    trusted: bool
    hashes: dict[str, str]
    diagnostics: tuple[str, ...]
```

The snapshot object itself owns the trust conclusion. Callers must not infer trust from `len(diagnostics)` in multiple locations.

Create one function:

```python
def _take_migration_snapshot(
    request: _ValidatedPostGenerationRequest,
) -> _MigrationSnapshot:
    ...
```

This function validates the complete state every time it is called.

### 4.3 Command outcome

Create:

```python
@dataclass(frozen=True)
class _CommandOutcome:
    succeeded: bool
    exit_code: int
    stdout: str
    stderr: str
```

Create:

```python
def _run_command(
    request: _ValidatedPostGenerationRequest,
) -> _CommandOutcome:
    ...
```

All subprocess exception handling lives here. It never raises expected subprocess exceptions.

### 4.4 Migration assessment

Create:

```python
@dataclass(frozen=True)
class _MigrationAssessment:
    passed: bool
    existing_unchanged: bool
    created_paths: tuple[str, ...]
    diagnostics: tuple[str, ...]
```

Create:

```python
def _assess_migration_change(
    request: _ValidatedPostGenerationRequest,
    before: _MigrationSnapshot,
    after: _MigrationSnapshot,
) -> _MigrationAssessment:
    ...
```

The assessment must calculate all filesystem conditions in one place.

### 4.5 Public orchestrator

After validation, the public function becomes conceptually:

```python
before = _take_migration_snapshot(request)
if not before.trusted:
    return failed_before_result(...)

command_outcome = _run_command(request)
after = _take_migration_snapshot(request)
assessment = _assess_migration_change(request, before, after)

passed = command_outcome.succeeded and assessment.passed

return PostGenerationResult(
    passed=passed,
    exit_code=(
        command_outcome.exit_code
        if not command_outcome.succeeded
        else 0 if passed else -1
    ),
    stdout=command_outcome.stdout,
    stderr=_combine_diagnostics(
        command_outcome.stderr,
        assessment.diagnostics,
    ),
    duration_seconds=...,
    created_paths=assessment.created_paths,
    existing_migrations_unchanged=assessment.existing_unchanged,
)
```

There must be one final success expression.

Do not mutate `passed` repeatedly.

---

## 5. Complete trusted-snapshot contract

`_take_migration_snapshot` must treat the snapshot as untrusted when any of the following is true:

1. migration directory does not exist;
2. migration path is not a directory;
3. migration directory is a symlink;
4. migration directory resolves outside the workspace;
5. migration directory resolution raises;
6. directory listing raises;
7. any direct `.py` entry is a symlink;
8. any direct `.py` entry is not a regular file;
9. an entry resolves outside the migration directory;
10. an entry resolves outside the workspace;
11. a file disappears during inspection;
12. a file cannot be read;
13. hashing raises;
14. relative path conversion fails.

A trusted snapshot contains hashes for every direct ordinary `.py` file, including:

```text
__init__.py
numbered migrations
non-numbered helper Python files
```

Existing non-numbered Python files remain integrity protected even though they do not count as newly created numbered migrations.

Ignore:

- nested directories;
- direct non-Python files;

for migration counting. Their presence alone need not make the snapshot untrusted.

All hash paths must be repository-relative POSIX strings.

Sort entries and diagnostics deterministically.

### 5.1 Missing after-state directory

The refactor must fix the reproduced false success.

A missing or replaced migration directory after the command produces:

```text
after.trusted=False
assessment.passed=False
assessment.existing_unchanged=False
final passed=False
final exit_code=-1 when command itself exited zero
```

This is true even when the before snapshot contained no Python files and `require_new_migration=False`.

---

## 6. Complete assessment contract

The migration assessment passes only when:

```text
before.trusted is True
after.trusted is True
every before path exists after
every before hash equals the after hash
and:
    require_new_migration is False
    OR exactly one newly created numbered migration exists
```

Created numbered migration rules:

- direct child of the configured migration directory;
- ordinary file already accepted into the trusted after snapshot;
- filename matches:
  `^\d+_[A-Za-z0-9_]+\.py$`;
- path was absent from the before snapshot;
- sorted repository-relative POSIX output.

An unsafe entry never appears in `created_paths`.

When after snapshot is untrusted, `existing_unchanged=False` even when all readable old hashes happen to match. An untrusted state cannot prove integrity.

Diagnostics include:

- before/after snapshot errors;
- deleted old files;
- changed old files;
- wrong migration count.

---

## 7. Complete command-outcome contract

Use:

```python
subprocess.run(
    list(request.command),
    cwd=str(request.workspace_root),
    capture_output=True,
    text=True,
    timeout=request.timeout,
)
```

Do not use `shell=True`.

Handle:

- `TimeoutExpired`;
- `FileNotFoundError`;
- `ValueError`;
- `OSError`;
- `SubprocessError`.

Return strings for stdout and stderr.

The command outcome does not inspect migrations. The public orchestrator always performs the after snapshot after `_run_command` returns, regardless of command success.

The subprocess outcome and migration assessment remain independent:

```text
command failed + filesystem trusted
→ final failure, existing_unchanged may be true

command succeeded + filesystem untrusted
→ final failure, exit_code -1

command failed + filesystem corrupted
→ final failure with both diagnostics

command succeeded + filesystem correct
→ potential success
```

---

## 8. Input-validation matrix

The refactor must preserve all current validation behavior.

### Workspace

Reject:

- missing;
- non-directory;
- null;
- integer;
- list;
- mapping;
- path conversion or resolution error.

Support valid relative and absolute paths.

### Command

Reject:

- plain string;
- bytes;
- empty sequence;
- non-string item;
- empty item;
- whitespace-only item;
- item containing NUL.

Freeze valid command to tuple.

### Timeout

Require:

```python
type(timeout) is int
timeout > 0
```

Reject bool, float, string, null, zero, and negative.

### Migration directory

Require:

- non-empty, non-whitespace string;
- no NUL;
- no backslash;
- no `..` path component;
- not absolute;
- expected lexical path lies under workspace.

The trusted snapshot then validates its live filesystem state.

### Migration requirement

Require bool.

---

## 9. Test refactor and full invariant matrix

Do not merely add another individual regression test. Reorganize the test file into clear groups while preserving existing coverage.

Suggested groups:

```text
TestInputValidation
TestTrustedMigrationSnapshot
TestCommandOutcome
TestMigrationAssessment
TestPublicOrchestration
TestRegressionCases
```

Deleting duplicate tests is permitted only when the replacement is parameterized and proves the same or stronger behavior. Do not reduce coverage to make the file shorter.

### 9.1 Input validation

Cover all valid and invalid inputs from Section 8.

### 9.2 Snapshot trust

Cover:

- ordinary directory;
- missing directory;
- directory becomes missing after command;
- empty directory becomes missing after command;
- directory path becomes file;
- directory symlink before command;
- directory symlink created during command;
- external directory symlink;
- internal directory symlink;
- file symlink;
- broken symlink;
- unreadable/read-error file;
- resolve error;
- listing error;
- ordinary numbered file;
- ordinary non-numbered Python file;
- nested Python file ignored;
- non-Python file ignored.

### 9.3 Command outcomes

Cover:

- success;
- non-zero;
- timeout with string output;
- timeout with byte output;
- command not found;
- ValueError;
- OSError;
- SubprocessError.

### 9.4 Assessment truth table

Use parameterized tests for this matrix:

| Command | Before trusted | After trusted | Old unchanged | Required | Created count | Final |
|---|---:|---:|---:|---:|---:|---:|
| success | yes | yes | yes | yes | 1 | pass |
| success | yes | yes | yes | yes | 0 | fail |
| success | yes | yes | yes | yes | 2 | fail |
| success | yes | yes | yes | no | 0 | pass |
| success | yes | no | unknown | no | 0 | fail |
| success | yes | no | unknown | yes | 1 valid | fail |
| success | yes | yes | no | no | 0 | fail |
| failure | yes | yes | yes | no | 0 | fail |
| failure | yes | yes | no | no | 0 | fail |

The table is the root protection against “diagnostic collected but forgotten.”

### 9.5 Production public-path adversarial tests

Keep explicit end-to-end tests for:

- valid migration;
- valid migration plus unsafe file symlink;
- missing migration directory after command;
- empty migration directory deleted after command;
- timeout after old-file modification;
- failed command after creating migration;
- relative workspace;
- migration-directory escape.

These tests must call `run_post_generation_command`, not only private helpers.

---

## 10. R3B acceptance and freeze policy

The refactor phase is accepted only when:

- focused tests pass on Windows;
- focused tests pass on Linux during independent audit;
- full suite passes;
- Ruff passes;
- mypy strict passes;
- compileall passes;
- `git diff --check` passes;
- changed files are exactly authorized;
- working tree is clean;
- documentation says “audit required,” not “independent audit satisfied.”

After the independent audit accepts this refactor:

```text
R3B is frozen.
```

Do not continue searching for speculative edge cases inside R3B. The next work is R3C. Reopen R3B only for a reproduced failure from R3D integration or real controlled execution.

---

## 11. Commit plan

Code commit:

```text
refactor(validation): model migration execution as trusted states
```

Documentation commit:

```text
docs(audit): record R3B root refactor
```

The documentation must record:

- the reason for replacing patch-driven control flow;
- code checkpoint hash;
- actual focused and full test counts;
- working-tree state;
- R3B audit pending;
- R3C blocked pending independent audit;
- Kaggle/Pilot/merge/tag blocked.

End OpenCode’s response with:

```text
R3B_ROOT_REFACTOR_AUDIT_REQUIRED
```

---

# Part II — Single-pass protocol for every future phase

## 12. Why previous phases required repeated correction

The main cause was not insufficient effort or an incapable model. The process gave the implementation model incomplete forms of certainty.

The pattern was:

1. a prose requirement described intended normal behavior;
2. OpenCode implemented the shortest design satisfying visible examples;
3. tests asserted those examples;
4. independent audit combined states not represented in the examples;
5. a defect appeared;
6. a narrow correction added one branch and one test.

A full test suite cannot catch a new contract when the contract’s negative states were never encoded.

Another process defect was mixing roles:

- OpenCode implemented;
- OpenCode evaluated its own completion;
- OpenCode wrote documentation claiming independent satisfaction;
- the actual independent audit happened afterward.

The future protocol separates these roles.

---

## 13. Mandatory phase sequence

Every future phase uses this sequence.

### Step 1 — Contract extraction

Before editing, OpenCode writes a concise internal table containing:

- public inputs;
- trusted inputs;
- private/forbidden inputs;
- outputs;
- side effects;
- success invariants;
- failure invariants;
- persistence fields;
- security boundaries;
- compatibility requirements.

No code before this table is complete.

### Step 2 — State machine

Define named states and transitions.

For R3C, examples will be:

```text
request validated
→ evaluator asset trusted
→ temporary directory created
→ evaluator copied
→ subprocess completed
→ stdout parsed
→ semantic result assessed
→ typed result returned
```

Every terminal state has defined output.

### Step 3 — Failure matrix

List combinations, not only individual errors.

For each operation include:

- valid;
- malformed input;
- missing path;
- wrong type;
- traversal;
- symlink;
- timeout;
- non-zero process;
- malformed output;
- correct output with wrong exit code;
- wrong output with zero exit code;
- failure plus filesystem side effect;
- diagnostic plus otherwise-valid state.

### Step 4 — Tests before implementation

Create tests for:

- normal cases;
- every failure-matrix row;
- at least three combined adversarial states;
- one production-path integration;
- one isolation proof;
- one persistence round trip when relevant.

Run tests and show that new tests fail for the expected reason before implementation, when practical.

### Step 5 — Cohesive implementation

Implement the state model in one pass.

Use immutable typed internal outcomes rather than separate data-plus-error tuples whose relationship callers must remember.

### Step 6 — Self red-team before commit

OpenCode must run three direct adversarial scripts not copied from the unit tests.

For R3C these should include:

- valid JSON plus unexpected stdout noise;
- evaluator symlink or path replacement;
- exit zero with `passed=false` and exit non-zero with `passed=true`.

### Step 7 — Gates

Run:

- focused tests;
- adjacent subsystem tests;
- production-path integration;
- full suite;
- Ruff;
- mypy;
- compileall;
- diff check;
- changed-file check.

### Step 8 — Code commit

Commit code only.

### Step 9 — Factual documentation

Documentation states:

```text
implementation complete
self-gates passed
independent audit pending
```

It must not state:

```text
independent audit satisfied
```

until the auditor approves in a later turn.

### Step 10 — Independent audit

The independent auditor:

- reads code;
- runs focused tests;
- runs direct adversarial cases;
- reviews phase invariants;
- either accepts the phase or reports one root-level correction.

The auditor should not produce a long sequence of one-case patches. If more than one defect shares a structural cause, the auditor requests one bounded refactor.

---

## 14. R3C pre-implementation architecture

R3C must follow the same trusted-state design from the start.

Use these conceptual private structures:

```python
_ValidatedEvaluatorRequest
_TrustedEvaluatorAsset
_EvaluatorCommandOutcome
_ParsedEvaluatorPayload
```

The public result remains:

```python
ScenarioEvaluatorResult
```

The single final success rule must be explicit:

```text
request valid
AND evaluator asset trusted
AND subprocess exit code == 0
AND stdout is exactly one JSON object
AND payload passed is True
AND payload error is empty
```

No collected error may remain only a diagnostic while success stays true.

R3C’s failure matrix must be completed before its code is written. It must include:

- path traversal;
- absolute paths;
- backslashes;
- evaluator root symlink;
- evaluator file symlink;
- missing asset;
- workspace equals canonical root;
- temporary directory accidentally inside workspace;
- copy failure;
- timeout;
- command not found;
- extra stdout before JSON;
- extra stdout after JSON;
- malformed JSON;
- missing fields;
- wrong field types;
- empty check names;
- exit zero with failed payload;
- non-zero with passed payload;
- error text with passed true;
- evaluator source copied into workspace;
- PYTHONPATH order;
- cleanup after success and failure.

This work should allow R3C to be completed in one implementation cycle followed by one independent audit.

---

## 15. Preventing over-engineering

A root refactor does not mean unlimited abstraction.

Use these limits:

- no external dependency;
- no generic subprocess framework shared across unrelated phases;
- no plugin system;
- no inheritance hierarchy;
- no new public API beyond the approved phase API;
- no abstraction used only once unless it represents a trusted state;
- maximum four small private state dataclasses in one module;
- one public orchestration function;
- one direct responsibility per helper.

The goal is explicit correctness, not architecture for hypothetical future products.

---

## 16. Current project position

Truthful status before this refactor:

```text
R1 Repository Agent                  complete
R2 Selective                         complete
R3A Scenario metadata               complete
R3B Migration runner                functionally broad, root refactor required
R3C Isolated evaluators             blocked
R3D Production wiring               pending
R4 Token and metrics                pending
R5 Nine local non-dry records       pending
R6 Bundle and push                  pending
Kaggle                              blocked
Stable tag                          blocked
Pilot                               blocked
```

Near goal:

```text
one bounded R3B trusted-state refactor
→ one independent acceptance audit
→ R3C single-pass implementation
```

Distant goal:

```text
R3C
→ R3D
→ R4
→ nine non-dry local records
→ bundle and push
→ nine real Qwen Kaggle records
→ independent result audit
→ stable V2 tag
→ Pilot with 7–12 changes and at least three repositories
```

---

## 17. Final instruction to the implementation model

Do not treat this document as permission to begin R3C.

Complete the R3B root refactor only. Stop for audit.

The objective is not to add more checks around the existing mutable flow. The objective is to replace the mutable flow with explicit trusted states and one final success equation while preserving the public API and scientific behavior.

---

**End of authoritative root-refactor and future phase protocol.**

---

## Appendix A — Refactor completion record

**Completed:** 2026-07-28  
**Code checkpoint:** `f8f95d2` (refactor(validation): model migration execution as trusted states)  
**Previous acceptance-closure checkpoint:** `f8faa08`  
**Working tree:** clean  

### Reason for replacing patch-driven control flow

R3B evolved through a sequence of narrow corrections, each fixing a real defect but leaving the mutable control flow structurally fragile. An independent audit found that the snapshot helper treated a missing after-state directory as empty trusted, producing false success for `require_new_migration=False` with an empty directory deleted during execution. The correct response was a bounded root refactor replacing patch-driven control flow with explicit immutable trusted states.

### Changes made

| File | Lines |
|------|-------|
| `src/benchmark/execution/post_generation.py` | +1359 −730 |
| `tests/unit/execution/test_post_generation.py` | reorganized into 7 groups with parametrized truth table |

### Internal state types introduced

- `_ValidatedPostGenerationRequest` — typed validated input
- `_MigrationSnapshot` — owns its own trust conclusion (`trusted: bool`) after 14 conditions
- `_CommandOutcome` — typed subprocess result, never raises expected exceptions
- `_MigrationAssessment` — deterministic assessment passing only when all invariants hold

### Test results

| Metric | Result |
|--------|--------|
| Focused `post_generation` | 108 passed, 10 skipped (symlink unavailable on Windows) |
| Adjacent execution tests | 265 passed, 11 skipped |
| Full suite | 1313 passed, 20 skipped |
| Ruff | 0 errors |
| Mypy strict (production files) | 0 errors |
| Compileall | 0 errors |
| `git diff --check` | clean (CRLF warning only) |

### State

- **R3B:** ROOT REFACTOR — INDEPENDENT AUDIT PENDING
- **R3C:** BLOCKED — pending independent audit
- **Kaggle:** BLOCKED
- **Pilot:** BLOCKED
- **Merge:** BLOCKED
- **Stable tag:** BLOCKED

### Required final line

R3B_ROOT_REFACTOR_AUDIT_REQUIRED
