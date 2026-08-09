# R3D In-Progress Audit and Completion Addendum

**Document status:** Binding continuation addendum  
**Target branch:** `experiment/three-arm-smoke-v2`  
**Starting committed HEAD:** `e61eb9a`  
**Current state:** uncommitted R3D correction work in progress  
**Independent audit model:** GPT-5.6 Thinking  
**Required OpenCode model:** DeepSeek V4 Flash Free — OpenCode Zen — Build  
**Last independently confirmed R3D OpenCode footer:** Big Pickle  
**Current active OpenCode model:** must be printed and verified before continuing  
**R4 and later phases:** blocked  

---

# 1. Decision

Do not reset the current working tree.

Do not commit the current work yet.

The current changes are useful and the full Windows suite is green, but four root-level R3D contract defects remain. Committing now would preserve another partially-correct phase checkpoint and force another correction cycle.

The current working tree contains:

```text
seven_arm_benchmark.py
src/benchmark/execution/runner.py
src/benchmark/statistics/reporting.py
tests/unit/execution/test_r3d_wiring.py
docs/R3D_ROOT_CORRECTION_AND_RF2_SINGLE_PASS_SPEC.md
```

The Windows evidence reports:

```text
1495 collected
1463 passed
32 skipped
0 failed
```

The independent Linux focused suite reports:

```text
tests/unit/execution/test_r3d_wiring.py
39 passed
```

Green tests do not authorize a commit when tests do not exercise the complete production contract.

---

# 2. Improvements already accepted in the working tree

Preserve these changes.

## 2.1 Typed scientific state

`_ScientificValidationResult` now owns:

```text
PostGenerationResult
FunctionalValidationResult
ScenarioEvaluatorResult
passed
failed_stage
failure_kind
feedback
duration
```

This is correct.

## 2.2 One scientific validation sequence

The sequence is now:

```text
generation guard
→ migration generation
→ baseline validation
→ isolated evaluator
→ final decision
```

This is the correct R3D architecture.

## 2.3 Shared field mapper

`_scientific_record_fields` correctly maps stage results and makes:

```text
functional_validation_passed
```

a compatibility mirror of:

```text
baseline_validation_passed
```

It also makes compatibility duration equal baseline duration.

## 2.4 Failure and feedback helpers

These helpers are conceptually correct:

```text
_failure_from_scientific_result
_scientific_feedback_channels
```

They should be completed rather than replaced.

## 2.5 Public wrapper

Using:

```python
dataclasses.replace(record, identity=..., duration_seconds=...)
```

is correct and eliminates future field-loss defects.

## 2.6 Entry and persistence forwarding

The current edits correctly add:

```text
canonical_project_root
python_executable
selection_tool_calls
selection_tool_duration_seconds
selection_inspected_file_count
selection_tool_transcript
```

to the entry conversion and reporting surfaces.

---

# 3. Blocking defect A — scientific preflight is still late

## 3.1 Direct reproduction

With:

```text
enable_regeneration=True
validation_command=None
```

the public Runner returns a configuration failure, but the strategy is called once before that failure.

Observed:

```text
strategy calls = 1
failure stage = configuration
message = validation_command is missing or empty
```

The required behavior is:

```text
strategy calls = 0
backend calls = 0
executor calls = 0
```

## 3.2 Root cause

`_validate_scientific_configuration` does not validate `validation_command`.

The same check remains duplicated later inside:

```text
_run_regeneration_flow
_run_iterative_flow
```

This is incomplete RF-2.

## 3.3 Required correction

Inside `_validate_scientific_configuration`, when regeneration is enabled, reject:

```text
None
[]
[""]
["   "]
```

and any list containing a non-string or whitespace-only item.

Use one small private command validation rule consistent with the existing validation API.

Then remove the duplicated late validation-command blocks from:

```text
_run_regeneration_flow
_run_iterative_flow
```

The only scientific configuration decision must happen before strategy analysis and model generation.

## 3.4 Required tests

Add real public tests:

```text
test_missing_baseline_command_fails_before_strategy
test_whitespace_baseline_command_fails_before_strategy
test_invalid_baseline_command_item_fails_before_strategy
test_agent_missing_baseline_command_fails_before_begin_run
```

Assert zero calls to:

```text
strategy.analyze_impact
strategy.begin_run
SharedRegenerationExecutor.execute
backend.generate
```

Do not test only `_validate_scientific_configuration`.

---

# 4. Blocking defect B — migration and evaluator failures remain non-repairable

## 4.1 Direct migration reproduction

A real Monolithic production path was run with:

```text
attempt 1 migration fails
attempt 2 migration would pass
max_attempts=3
```

Observed:

```text
backend generation calls = 1
migration calls = 1
final status = failed
functional_validation_passed = None
```

No repair attempt occurred.

## 4.2 Direct evaluator reproduction

A real Monolithic path was run with:

```text
baseline passes
attempt 1 evaluator fails
attempt 2 evaluator would pass
max_attempts=3
```

Observed:

```text
backend generation calls = 1
evaluator calls = 1
final status = failed
functional_validation_passed = True
scenario_evaluator_passed = False
```

No repair attempt occurred.

## 4.3 Root cause

`_is_repairable_failure` still contains:

```python
if record.functional_validation_passed is not False:
    return False
```

But this field mirrors baseline only:

```text
migration failure → None
evaluator failure → True
```

The compatibility field must never control complete scientific repair.

The current unit tests hide this defect by manually constructing migration and evaluator records with:

```text
functional_validation_passed=False
```

Those records cannot be produced by `_scientific_record_fields`.

## 4.4 Required correction

Remove the compatibility-field gate.

Use only:

```text
record.status == failed
no harness/infrastructure/timeout failure
at least one repairable stage exists
budget allows repair
```

Repairable stages:

```text
generation_guard
regeneration
migration_generation
baseline_validation
scenario_evaluator
```

Do not make:

```text
configuration
isolation
budget
protocol
```

repairable.

## 4.5 Existing regression test

The old test:

```text
test_generation_rejection_no_repair
```

conflicts with the frozen R3D contract.

Update it to prove bounded repair after an empty/rejected first generation response:

```text
attempt 1 produces no generated source
attempt 2 produces valid source
final status succeeds
exactly two generation calls
```

Do not restore the obsolete behavior merely to keep an old test green.

## 4.6 Required production-path tests

Add:

```text
test_monolithic_migration_failure_repairs_to_success
test_selective_migration_failure_repairs_to_success
test_monolithic_evaluator_failure_repairs_to_success
test_selective_evaluator_failure_repairs_to_success
test_generation_guard_failure_repairs_to_success
test_harness_failure_never_repairs
test_timeout_never_repairs
```

Use the real public `run()` path.

Patch stage functions to return exact typed results in sequence.

Assert the second generation actually occurs.

---

# 5. Blocking defect C — Agent transcript is still dropped

## 5.1 Direct reproduction

A real iterative Runner was supplied an Agent strategy with:

```text
selection_tool_calls = 2
compact_tool_transcript = ("TOOL A", "TOOL B")
```

The final record contained:

```text
selection_tool_calls = 2
selection_tool_transcript = ()
```

The persistence and reporting layers can now carry the transcript, but Runner never writes it.

## 5.2 Required correction

In the iterative flow, read the current strategy property:

```python
tuple(getattr(self._strategy, "compact_tool_transcript", ()))
```

and forward it to both:

```text
successful Agent record
failed/timed-out Agent record
```

Do not create a new public field.

## 5.3 Required tests

Use the real iterative path:

```text
test_agent_success_preserves_tool_transcript
test_agent_failure_preserves_tool_transcript
test_agent_transcript_reaches_entry_record_dict
test_agent_transcript_reaches_run_record_data
test_agent_transcript_survives_jsonl_round_trip
test_agent_transcript_reaches_reporting
```

Use sentinel transcript entries and assert exact equality.

---

# 6. Blocking defect D — repair duration and regeneration feedback diverge

## 6.1 Initial repair duration

The repair flow initializes:

```python
val_dur = first_record.functional_validation_duration_seconds
```

This is baseline duration only.

The first attempt may also contain migration and evaluator time.

The final repaired record therefore undercounts the initial validation sequence.

Use:

```python
val_dur = (
    first_record.migration_duration_seconds
    + first_record.baseline_validation_duration_seconds
    + first_record.scenario_evaluator_duration_seconds
)
```

Then add full scientific sequence duration for each repair attempt.

Do not redesign R4 metrics in this phase.

## 6.2 Agent regeneration failure feedback

When:

```text
SharedRegenerationExecutor has failures
scientific validation itself passes
```

the next Agent revision reads the passed `_last_scientific_result`.

`_scientific_feedback_channels` then produces empty generic feedback.

Track the latest revision channels independently:

```text
scientific failure → scientific stage channels
executor failure → bounded executor failure text
```

The next `revise_plan` must receive the actual failed production stage.

A local variable is sufficient:

```python
last_feedback_channels: tuple[int, str, str] | None
```

Do not introduce a new public result class.

## 6.3 Evaluator feedback completion

For evaluator failure, include bounded:

```text
evaluator stdout
evaluator stderr
semantic error
public check names
```

Do not include:

```text
evaluator source
asset content
Ground Truth
hidden-test descriptions
```

## 6.4 Required tests

Add real iterative tests:

```text
test_agent_regeneration_failure_receives_executor_feedback
test_agent_migration_failure_receives_migration_feedback
test_agent_evaluator_failure_receives_checks_and_error
test_agent_feedback_is_bounded
test_agent_feedback_contains_no_evaluator_source
```

No Agent test may be skipped.

---

# 7. Test suite corrections

The current 39-test file is executable but several tests remain nominal.

## 7.1 Replace helper-only preflight tests

The following must call public production paths:

```text
missing canonical root
missing Python executable
missing evaluator
missing migration command
missing baseline command
```

Assert strategy/backend/executor were not called.

## 7.2 Replace nominal V2 success

Current:

```text
test_all_v2_stages_pass
```

uses no migration, no baseline, and no evaluator.

Replace with exact typed stage results:

```text
migration passed with one created path
baseline passed
evaluator passed with checks
```

Assert exact call order:

```text
migration
baseline
evaluator
```

## 7.3 Replace migration-name-only tests

The zero/two/changed migration tests currently fail for an unrelated missing migration-directory condition.

Patch:

```text
run_post_generation_command
```

with exact `PostGenerationResult` values representing:

```text
zero created migration
two created migrations
old migration changed
```

or construct real controlled migration directories.

The assertion must prove the named state.

## 7.4 Replace final-wrapper attribute test

Patch `_run_attempt` to return a `RunRecord` with sentinel values in every:

```text
selection tool
migration
baseline
evaluator
duration
artifact-count
```

field.

Call public `run()`.

Assert every sentinel survives exactly.

## 7.5 Replace conversion dataclass test

Call actual:

```python
seven_arm_benchmark._to_run_record_data
```

Do not construct `RunRecordData` manually and read the values back.

## 7.6 Persistence conflict test

Add:

```text
same run ID + identical new fields → idempotent
same run ID + one changed new field → RunRecordIntegrityError
```

## 7.7 Leakage tests

Require:

```text
strategy was called
evaluator was called
assertions executed
canonical snapshot hash unchanged
evaluator asset absent from workspace
```

A loop over an empty call list is not evidence.

---

# 8. RF-2 completion rules

RF-2 is not complete until all are true:

```text
one configuration preflight
one scientific stage orchestrator
one stage-to-record mapper
one stage-to-failure mapper
one feedback mapper
one public wrapper using replace
no baseline compatibility gate controls overall repair
no duplicated validation-command checks
no Agent baseline-only revision state
no manual scientific field extraction in initial, repair, or Agent flow
```

Do not refactor unrelated selection, graph, backend, or metric arithmetic.

---

# 9. Required direct adversarial scripts

Run all three before committing.

## Script A — production preflight

Call public `run()` with:

```text
enable_regeneration=True
validation_command=None
```

Print:

```text
strategy calls
backend calls
executor calls
failure stage
```

Required:

```text
0
0
0
configuration
```

## Script B — repair matrix

Run two real public cases:

```text
migration fail → pass
evaluator fail → pass
```

Required:

```text
both final statuses succeed
both execute a second generation attempt
```

## Script C — Agent evidence

Run:

```text
attempt 1 evaluator fails
attempt 2 succeeds
```

Print:

```text
revise feedback
selection tool calls
selection tool transcript
final evaluator fields
```

Require checks/error present and source absent.

---

# 10. Final gates

Run:

```powershell
python -m pytest tests/unit/execution/test_r3d_wiring.py -q

python -m pytest `
  tests/unit/execution/test_runner.py `
  tests/unit/execution/test_pipeline.py `
  tests/unit/test_models.py `
  tests/unit/test_checkpoint.py `
  tests/unit/statistics/test_reporting.py `
  tests/contract/test_three_arm_core.py `
  -q

python -m pytest `
  tests/integration/test_scientific_smoke_v1_fixes.py `
  tests/integration/test_su0010a_regeneration.py `
  tests/integration/test_su0011_iterative_agent.py `
  -q

python -m pytest -q
```

Then:

```powershell
ruff check <all changed Python files>
mypy --strict <all changed production files>
python -m compileall <all changed Python files>
git diff --check
```

No required R3D or Agent test may be skipped.

---

# 11. Commit and documentation sequence

## Code commit

Before staging:

```powershell
git diff --name-only
git diff --cached --name-only
```

The code commit contains production and test files only.

Commit:

```text
fix(validation): complete R3D scientific wiring contract
```

## Documentation commit

Track:

```text
docs/R3D_ROOT_CORRECTION_AND_RF2_SINGLE_PASS_SPEC.md
docs/R3D_IN_PROGRESS_AUDIT_AND_COMPLETION_ADDENDUM.md
```

Update:

```text
docs/PROJECT_HANDOFF.md
reports/latest_phase_report.md
docs/V2_R3B_TO_KAGGLE_NO_DISCRETION_EXECUTION_SPEC.md
selective_updates/CHANGE_INDEX.md
selective_updates/records/TECHNICAL-DEBT-AND-REFACTOR-SCHEDULE.md
selective_updates/records/R3D-PRODUCTION-WIRING.md
```

Commit:

```text
docs(audit): record R3D correction pending audit
```

No empty commit.

No documentation in the code commit.

---

# 12. Required final report

Print and persist the full R3D report.

It must include:

```text
requested model
actual footer model
starting HEAD
code commit
documentation commit
exact files
preflight direct script
migration repair direct script
evaluator repair direct script
Agent feedback direct script
all R3D focused counts
all adjacent/integration counts
full-suite count
Ruff
mypy
compileall
diff check
RF-2 evidence
technical debt closed
technical debt deferred
clean tree
```

It must list every repair and Agent path separately.

Do not answer with:

```text
all work complete
continue?
```

End exactly:

```text
R3D_ROOT_CORRECTION_AUDIT_REQUIRED
```

---

# 13. Project status

```text
R1 Repository Agent                  accepted
R2 Selective                         accepted
R3A Scenario metadata               accepted
R3B Migration runner                accepted and frozen
R3C Evaluator system                accepted and frozen
R3D current working tree            substantial progress
R3D preflight                       incomplete
R3D repair routing                  broken
R3D Agent transcript                dropped
R3D RF-2                            incomplete
R4                                  blocked
R5                                  pending
R6                                  pending
Kaggle                              blocked
Stable tag                          blocked
Pilot                               blocked
```

Near goal:

```text
finish the current R3D working tree correctly
→ commit once
→ independent audit
→ freeze R3D
→ begin R4
```

Do not discard the current work. Correct the root contract before committing.


# 14. Independent acceptance definition

R3D can be accepted only when the independent audit can reproduce all of the following from the committed public paths:

```text
configuration defects stop before any strategy or model call;
Monolithic migration failure reaches a bounded repair attempt;
Selective evaluator failure reaches a bounded repair attempt;
Repository Agent revises from the actual failed stage;
Repository Agent keeps its exact tool transcript;
the public wrapper preserves all stage and Agent fields;
the entry point supplies canonical root and Python executable;
RunRecordData and JSONL preserve every new field;
reporting emits every new field;
failure stages remain exact and machine-readable.
```

The independent audit will not use the total test count as a substitute for these behaviors.

After R3D is accepted:

```text
R3D is frozen.
```

Do not reopen R3D for formatting or speculative edge cases. RF-2 is part of this correction and must be completed before the code commit, not deferred to R4.

# 15. Over-engineering constraints

This continuation is a root correction but not a redesign.

Expected production changes are limited to:

```text
one preflight rule;
one repair-eligibility correction;
one Agent feedback variable;
one Agent transcript forwarding change;
one repair-duration initialization correction;
removal of two duplicate late configuration checks.
```

The larger work is in replacing nominal tests with public-path evidence.

Forbidden:

- a new public validation service;
- a generic workflow engine;
- a new record-builder framework;
- changes to R3B or R3C;
- metrics renaming assigned to R4;
- unrelated Runner cleanup;
- changing model or selection algorithms.

This scope is the fastest route to a reliable R3D commit because it preserves the current useful implementation while removing the exact causes that would make R5 records incomplete or prevent repair.
