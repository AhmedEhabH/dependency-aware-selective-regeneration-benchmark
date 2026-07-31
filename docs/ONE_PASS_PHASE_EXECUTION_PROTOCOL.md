# One-Pass Phase Execution Protocol

**Applies to:** R4, R5, R6, Kaggle Smoke preparation, and Pilot preparation  
**Purpose:** finish each phase as one cohesive feature, permit one bounded correction when necessary, audit once, and freeze  
**Authority:** GPT-5.6 Thinking independent audit  
**OpenCode execution model:** DeepSeek V4 Flash Free - OpenCode Zen - Build  
**Scientific execution model later:** Qwen2.5-Coder-7B-Instruct on Kaggle  
**Phase status (2026-07-31):** R4 implemented and committed (`e87d4ad`) pending independent audit; R5 unauthorized until audit; R6 and Kaggle blocked.

---

# 1. Core rule

Every phase follows this lifecycle:

```text
complete phase specification
→ one cohesive implementation pass
→ tests and compile while building
→ one bounded internal correction/refactor pass
→ code commit
→ detailed report and documentation commit
→ independent audit
→ either freeze or one root-correction pass
→ final audit
→ freeze
```

Forbidden lifecycle:

```text
vague prompt
→ partial feature
→ commit
→ discover one edge case
→ patch
→ discover another edge case
→ patch
→ documentation patch
→ lint patch
→ evidence patch
```

A phase is planned as a complete state contract, not as a list of happy-path outputs.

---

# 2. Maximum correction policy

## Before the first code commit

OpenCode may correct any number of implementation mistakes inside the same working tree.

This is not counted as patching. It is normal implementation.

The first code commit occurs only after:

```text
focused tests pass;
integration tests pass;
static checks pass;
bounded refactor completes;
direct adversarial cases pass.
```

## After independent audit

The independent auditor chooses one outcome.

### ACCEPT

```text
freeze immediately
```

### ROOT_CORRECTION REQUIRED

One bounded correction task is allowed.

The correction specification must group all reproduced blockers by root cause.

It must not create one prompt per failing assertion.

After that correction:

```text
re-audit
→ freeze
```

### CONTRACT FAILURE

When a second independent audit still exposes a TD-0 or TD-1 root defect, do not issue another small patch.

Stop and produce:

```text
phase root-cause review;
failed assumptions;
state model revision;
replacement plan.
```

The phase is then rebuilt as one coherent correction, not extended with micro-patches.

---

# 3. Required phase specification file

Every phase has exactly one authoritative implementation document:

```text
docs/phase_specs/<PHASE>_SINGLE_PASS_SPEC.md
```

Example:

```text
docs/phase_specs/R4_SINGLE_PASS_SPEC.md
```

The file is created before OpenCode edits production code.

It must contain all sections below.

---

# 4. Section A — phase objective

State in measurable terms what the phase proves.

Bad:

```text
improve metrics
```

Good:

```text
every persisted non-dry record reports exact selection, regeneration,
migration, baseline, evaluator, repair, and total token/call/duration values;
total identities hold; no stage is double-counted; per-call completion limit
remains independent from total workflow budget.
```

State what is deliberately outside scope.

---

# 5. Section B — exact read order

List every file OpenCode may read before the first edit.

Use a numbered order:

```text
1. phase spec
2. primary production module
3. direct config model
4. direct record model
5. persistence conversion
6. reporting conversion
7. existing focused tests
8. existing integration tests
```

OpenCode must not start with broad search.

When an unplanned file is genuinely required, it stops and prints:

```text
UNPLANNED_READ_REQUIRED
file:
dependency:
reason:
```

No file is modified after this marker.

---

# 6. Section C — artifact map

List every artifact as one of:

```text
production — modify
production — read only
test — modify
test — add
documentation — modify
frozen — prohibited
```

For each modifiable artifact, specify:

```text
current owner;
new responsibility;
incoming dependencies;
outgoing dependents;
public names;
private names;
tests that prove it.
```

The phase spec must explain why every directly affected dependency is either changed or deliberately unchanged.

---

# 7. Section D — frozen naming contract

Before implementation, freeze:

```text
module names
public classes
public functions
private state dataclasses
private helpers
record fields
JSON keys
failure-stage names
test file names
test class/function naming
commit messages
final marker
```

OpenCode may not invent synonyms.

When a name in the existing repository conflicts with the planned contract, the specification decides the compatibility strategy before implementation.

---

# 8. Section E — state machine

Express the phase as states and transitions.

Template:

```text
untrusted request
→ validated configuration
→ trusted stage inputs
→ stage outcomes
→ combined assessment
→ persisted record
→ report view
```

For each state define:

```text
input;
owned data;
trust condition;
failure representation;
next state;
persistence fields.
```

No Boolean may be separated from its diagnostic evidence when they can diverge.

---

# 9. Section F — success equation

Write one explicit final equation.

Example:

```text
passed =
    configuration_valid
    and generation_calls > 0
    and generated_source_count > 0
    and migration_passed
    and baseline_passed
    and evaluator_passed
```

Metric phases use arithmetic identities.

Example:

```text
total_workflow_tokens =
    selection_total_tokens
    + regeneration_total_tokens
    + repair_total_tokens
```

Every term must have one owner.

No field may be calculated in more than one production module.

---

# 10. Section G — complete failure matrix

List dimensions, not scattered examples.

Common dimensions:

```text
input type;
missing configuration;
path state;
command outcome;
subprocess exception;
payload validity;
stage ordering;
partial evidence;
persistence round trip;
reporting serialization;
cross-platform behavior.
```

For each equivalence class define:

```text
detection owner;
expected failure stage;
expected failure kind;
later stages skipped or executed;
repair eligibility;
persisted evidence;
test name.
```

Add at least three combined adversarial cases.

---

# 11. Section H — tests before implementation

The specification defines tests before production code is edited.

Required categories:

## Unit contract tests

Prove individual state transitions.

## Public-path tests

Call the real public entry point.

Private helper tests do not replace these.

## Integration tests

Cross real module boundaries.

## Persistence tests

Use actual save and load APIs.

Manual `json.dumps` is not persistence evidence.

## Reporting tests

Use actual serializer/reporting APIs.

## Isolation tests

Prove hidden assets and canonical sources remain outside generated workspaces.

## Cross-platform tests

When filesystem, paths, subprocesses, or symlinks are involved:

```text
Windows full suite
and
Linux focused suite
```

## Property tests

For arithmetic, budgets, counts, and invariants.

---

# 12. Test-quality rules

A test is invalid when:

```text
its name claims a transition it does not execute;
it passes because of an unrelated earlier failure;
it manually constructs the expected final result;
it mocks the entire behavior under test;
its assertions are inside an optional `if`;
it accepts either of two unrelated outputs;
it modifies repository metadata;
a platform skip is the only evidence;
it calls only a private helper while claiming public behavior.
```

Every negative fixture must contain one conceptual defect.

Every negative result must identify the intended failed check or stage.

---

# 13. Integration strength

A phase integration test must cross the boundaries the phase exists to connect.

Template:

```text
real entry configuration
→ real public orchestrator
→ real stage result types
→ final record
→ persistence
→ reload
→ reporting
```

Mocks may replace expensive external services, but not the orchestration under test.

The final report lists every crossed boundary.

---

# 14. Incremental implementation order

OpenCode follows a fixed order.

## Step 1

Add or update tests for one state.

Run the smallest test.

## Step 2

Implement that state.

Run:

```text
py_compile
focused test
Ruff on changed file
mypy on changed production file
```

## Step 3

Proceed to the next state.

Do not write all production files before compiling the first.

## Step 4

Run public-path tests.

## Step 5

Run integration and persistence tests.

## Step 6

Run the complete focused group.

## Step 7

Run the full suite.

---

# 15. Compile and static gates

After every changed Python production file:

```powershell
python -m py_compile <file>
ruff check <file>
mypy --strict <file>
```

After every changed test file:

```powershell
python -m py_compile <file>
ruff check <file>
python -m pytest <smallest-target> -q
```

Final:

```text
focused tests
adjacent tests
integration tests
full suite
Ruff
mypy
compileall
git diff --check
```

No commit while any required gate fails.

---

# 16. Bounded refactor before commit

Each phase includes one refactor checkpoint before the code commit.

Time budget:

```text
maximum 15% of implementation effort
```

Allowed:

```text
remove duplicated phase orchestration;
consolidate repeated field mapping;
replace mutable flags with typed states;
remove dead code introduced by the phase;
reduce duplicated fixtures;
align names with frozen contract;
make success equation explicit.
```

Forbidden:

```text
unrelated cleanup;
generic future framework;
public API redesign;
touching frozen phases;
optimizing hypothetical future repositories.
```

The phase spec names the refactor checkpoint:

```text
RF-<phase>
```

---

# 17. Technical-debt policy

Every debt item has:

```text
ID
phase
artifact
category
severity
evidence
impact
planned checkpoint
status
```

## TD-0 — scientific blocker

Must close before phase commit.

## TD-1 — production/evidence blocker

Must close before phase commit.

## TD-2 — maintainability

Close in the phase refactor when directly related.

Otherwise schedule at a named checkpoint.

## TD-3 — cosmetic

Do not interrupt delivery.

The report states:

```text
TD closed
TD deferred
new TD introduced
```

“None” requires evidence.

---

# 18. Direct adversarial scripts

Before the code commit, run at least three direct scripts outside Pytest.

They must not duplicate test setup verbatim.

Examples:

```text
invalid configuration before any model call;
first attempt failure followed by successful repair;
field sentinel through public record/persistence/reporting;
arithmetic extremes;
missing/zero/unlimited budget;
partial stage evidence.
```

Print exact inputs and outputs in the final report.

---

# 19. Commit discipline

## Code commit

Contains:

```text
production files
test files
necessary deterministic test metadata
```

No reports or handoff documents.

Use explicit staging.

Forbidden:

```text
git add .
git add -A
git commit -a
```

Before commit:

```text
git diff --name-only
git diff --cached --name-only
```

## Documentation commit

Contains:

```text
phase specification
latest detailed report
project handoff
continuation plan
change index
phase record
technical debt schedule
```

No production or test files.

No empty commit.

---

# 20. Detailed OpenCode report

OpenCode must print the report in the visible response and save it to:

```text
reports/latest_phase_report.md
```

Length:

```text
1,800–2,500 words
```

Required headings:

```text
A. Requested and actual model
B. Git identity
C. Objective and frozen boundaries
D. Artifact before/after/dependency/test table
E. State machine
F. Success equation
G. Failure matrix
H. Public-path evidence
I. Integration boundaries
J. Persistence/reporting evidence
K. Direct adversarial scripts
L. Incremental failures and corrections
M. Refactor evidence
N. Final gates
O. Commit scope
P. Technical debt
Q. Productivity metrics
R. Known limitations
S. Authorization
```

The final visible response prints the actual documentation commit hash.

Inside the report file, use:

```text
Documentation commit: this commit
```

to avoid impossible self-reference.

---

# 21. Model identity rule

OpenCode prints the active model before reading or editing.

When the active model differs from the requested model:

```text
make no changes
MODEL_MISMATCH_NO_CHANGES
```

The final footer is the source of truth.

The report records both:

```text
requested model
actual footer model
```

---

# 22. Independent audit contract

The independent audit does not trust:

```text
OpenCode summary;
test count alone;
documentation claims;
green full suite alone.
```

It checks:

```text
Git scope;
public source;
test semantics;
focused Linux execution;
Windows full-suite evidence;
direct adversarial reproduction;
persistence/reporting paths;
documentation truth.
```

Audit outcomes:

```text
ACCEPT_AND_FREEZE
ROOT_CORRECTION_REQUIRED
CONTRACT_FAILURE_REPLAN
```

---

# 23. Freeze contract

After acceptance:

```text
phase status = accepted and frozen
```

No additional phase work for:

```text
style;
speculative hardening;
test-count increases;
documentation hash self-reference;
non-blocking TD-2 outside scheduled checkpoint.
```

A frozen phase reopens only when a later real production path produces a reproducible contradiction.

---

# 24. Refactor and debt schedule

## R4 — RF-3

After R4 implementation and before its code commit:

```text
centralize arithmetic identities;
remove deprecated metric aliases used by new code;
prove no double counting;
align config and persisted names.
```

## R5 — RF-4

After the first successful nine local records and before final R5 freeze:

```text
remove test-only production leakage;
remove dead local experiment setup;
consolidate record/report construction;
close all open TD-0 and TD-1;
review scheduled TD-2;
rerun all nine records.
```

## R6

No broad code refactor.

Only:

```text
bundle parity;
deployment blockers;
documentation and source hash consistency.
```

## Post-Kaggle

No algorithm changes based on observed results.

Only evidence-integrity defects may be corrected, while preserving original records.

---

# 25. Productivity metrics

Every phase reports:

```text
planned production files
actual production files
unplanned production files
planned tests
actual tests
public-path tests
integration boundaries
compile failures before commit
focused failures before commit
architecture deviations
naming deviations
empty commits
model mismatches
audit correction cycles
elapsed time
```

Targets:

```text
unplanned production files = 0
architecture deviations = 0
naming deviations = 0
empty commits = 0
model mismatches = 0
post-audit root corrections <= 1
TD-0 at freeze = 0
TD-1 at freeze = 0
```

---

# 26. Stop conditions

OpenCode stops without improvising when:

```text
active model mismatch;
wrong branch or HEAD;
dirty tree not authorized by continuation prompt;
unplanned production file required;
public contract conflict;
new external dependency required;
focused test reveals state-model contradiction;
full suite failure;
code staging contains documentation;
documentation staging is empty.
```

Marker:

```text
PHASE_BLOCKED
model:
HEAD:
dirty files:
first failing command:
root reason:
```

---

# 27. R4 application

Before R4 implementation, GPT-5.6 Thinking will create:

```text
docs/phase_specs/R4_SINGLE_PASS_SPEC.md
```

It must identify exact metric owners and arithmetic identities before any edits.

OpenCode will not be asked to discover the architecture.

R4 will be implemented once, internally corrected before commit, independently audited, and frozen under this protocol.

---

# 28. Current official state

```text
R1 Repository Agent                  frozen
R2 Dependency-aware Selective        frozen
R3A Scenario metadata               frozen
R3B Migration runner                frozen
R3C Evaluator system                frozen
R3D Production scientific wiring    frozen
R4 Token and metric semantics       next
R5 Nine local records               pending
R6 Bundle and push                  pending
Kaggle Smoke                        blocked
Stable scientific tag              blocked
Pilot                               blocked
```

---

**This protocol replaces the patch-driven phase workflow.**
