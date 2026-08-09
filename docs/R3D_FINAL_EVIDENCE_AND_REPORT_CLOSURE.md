# R3D Final Evidence and Report Closure

**Document status:** Binding final closure contract
**Target branch:** `experiment/three-arm-smoke-v2`
**Audited HEAD:** `35506f0`
**Audited code checkpoint:** `9e28790`
**Accepted and frozen prior checkpoint:** R3C at `c8c8213`
**Independent audit model:** GPT-5.6 Thinking
**Required OpenCode model:** DeepSeek V4 Flash Free — OpenCode Zen — Build
**Last OpenCode footer:** DeepSeek V4 Flash Free
**Current permission:** close R3D evidence/reporting gaps only
**R4 and later phases:** blocked

---

# 1. Executive verdict

The OpenCode response was not an acceptable detailed report.

The visible response contained only:

```text
git commit output
R3D_ROOT_CORRECTION_AUDIT_REQUIRED
```

It did not print the required 1,800–2,500-word R3D report.

A longer report exists in `reports/latest_phase_report.md`, but it is not reliable enough to serve as an authoritative handoff. It contains incorrect file statuses, nonexistent test names and test classes, inaccurate diff statistics, and claims that all 54 tests are public-path tests even though several tests call only private helpers or manually construct persistence objects.

The production implementation at `9e28790` is substantially better than the preceding R3D checkpoint. Independent direct executions confirmed that the principal production flows now work:

```text
missing scientific configuration
→ fails before strategy call

migration failure
→ enters bounded repair
→ second generation attempt
→ succeeds

evaluator failure
→ enters bounded repair
→ second generation attempt
→ succeeds

Repository Agent evaluator failure
→ revise_plan receives evaluator error and check name
→ second attempt succeeds

Repository Agent transcript
→ preserved in final RunRecord
```

The functional R3D core is therefore close to acceptance. It must not be rewritten.

One production feedback defect and several evidence/reporting defects remain. They can be closed in one small task without another architecture refactor.

---

# 2. Audited repository state

The supplied repository has:

```text
Branch: experiment/three-arm-smoke-v2
HEAD: 35506f0
Working tree: clean
```

Commits:

```text
9e28790 fix(validation): complete R3D scientific wiring contract
35506f0 docs(audit): record R3D correction pending audit
```

The code commit changed:

```text
seven_arm_benchmark.py
src/benchmark/execution/runner.py
src/benchmark/statistics/reporting.py
tests/integration/test_su0010a_regeneration.py
tests/unit/execution/test_r3d_wiring.py
tests/unit/execution/test_runner.py
```

The documentation commit changed:

```text
docs/PROJECT_HANDOFF.md
docs/R3D_IN_PROGRESS_AUDIT_AND_COMPLETION_ADDENDUM.md
docs/R3D_ROOT_CORRECTION_AND_RF2_SINGLE_PASS_SPEC.md
reports/latest_phase_report.md
selective_updates/CHANGE_INDEX.md
selective_updates/records/R3D-PRODUCTION-WIRING.md
selective_updates/records/TECHNICAL-DEBT-AND-REFACTOR-SCHEDULE.md
```

The commit separation is now correct.

Windows evidence supplied by the researcher:

```text
1510 collected
1478 passed
32 skipped
0 failed
```

Independent Linux evidence:

```text
tests/unit/execution/test_r3d_wiring.py
54 passed

R3D adjacent unit/contract group
217 passed
```

Independent integration execution was not used as acceptance evidence because several long integration files exceeded the audit environment's per-command time budget. The full Windows suite and independent direct production scripts provide the relevant R3D evidence.

---

# 3. Independent direct production evidence

## 3.1 Configuration preflight

The public `BenchmarkRunner.run()` path was executed with:

```text
enable_regeneration=True
validation_command=None
```

Observed:

```text
strategy calls = 0
status = failed
failure stage = configuration
failure kind = harness_defect
```

This proves the configuration failure occurs before model generation.

## 3.2 Migration failure repair

The public Monolithic path was executed with:

```text
attempt 1:
  generated source present
  migration fails with MIG_FAIL

attempt 2:
  generated source present
  migration succeeds with one path
  baseline succeeds
  evaluator succeeds
```

Observed:

```text
final status = succeeded
executor calls = 2
migration calls = 2
baseline calls = 1
evaluator calls = 1
regeneration_model_calls = 2
final generated migration path preserved
```

The initial migration failure is preserved in the record's failure history.

## 3.3 Evaluator failure repair

The public Monolithic path was executed with:

```text
attempt 1:
  migration passes
  baseline passes
  evaluator fails

attempt 2:
  migration passes
  baseline passes
  evaluator passes
```

Observed:

```text
final status = succeeded
executor calls = 2
migration calls = 2
baseline calls = 2
evaluator calls = 2
scenario_evaluator_passed = true
```

This confirms migration and evaluator failures are now repairable.

## 3.4 Repository Agent feedback and transcript

A real iterative Runner path was executed with:

```text
attempt 1:
  evaluator fails
  public check = task_priority_filter
  semantic error = EVAL_BAD
  evaluator stdout = EVAL_OUT
  evaluator stderr = EVAL_STDERR

attempt 2:
  succeeds
```

Observed `revise_plan` input:

```text
exit_code = 1
val_stdout = EVAL_OUT
val_stderr = EVAL_BAD; checks: task_priority_filter
```

Observed final record:

```text
selection_tool_transcript = ("TOOL A", "TOOL B")
scenario_evaluator_passed = true
scenario_evaluator_checks = ("task_priority_filter",)
```

The revision uses the correct failed scientific stage and the transcript is preserved.

However, the evaluator subprocess stderr `EVAL_STDERR` was not included in the revision feedback. This is the remaining production defect.

---

# 4. Remaining production defect

## 4.1 Evaluator stderr is discarded

Current `_scientific_feedback_channels` behavior for the evaluator stage is conceptually:

```python
stdout = evaluator.stdout
stderr_channel = evaluator.error
append checks
```

It does not include:

```python
evaluator.stderr
```

The frozen R3D feedback contract requires bounded public feedback from:

```text
evaluator stdout
evaluator stderr
semantic error
public check names
```

Subprocess stderr may contain useful import, runtime, or environment diagnostics that are not duplicated in the semantic error.

## 4.2 Exact correction

Inside the evaluator branch of `_scientific_feedback_channels`, construct the stderr channel from:

```text
evaluator.stderr
evaluator.error
checks
```

Each source is bounded.

The final channel must be at most 1,000 characters.

Suggested behavior:

```python
parts = []

if result.evaluator.stderr:
    parts.append(result.evaluator.stderr[:400])

if result.evaluator.error:
    parts.append(result.evaluator.error[:400])

if result.evaluator.checks:
    parts.append(
        "checks: " + ", ".join(
            str(check)
            for check in result.evaluator.checks[:5]
        )
    )

stderr_channel = "; ".join(parts)[:1000]
```

Do not include:

```text
evaluator source
evaluator asset contents
Ground Truth
hidden check descriptions
canonical evaluator path content
```

This is one local correction, not a refactor.

---

# 5. Evidence gaps in the committed test file

The current test file contains 54 passing tests, but the report overstates what they prove.

## 5.1 Entry-point test is not an entry-point test

The test named:

```text
test_real_entry_passes_canonical_root_and_python_exe
```

calls the local `_make_runner` test helper.

It does not call:

```text
seven_arm_benchmark._run_single_scenario_strategy
```

The production source currently passes the correct values, but no regression test protects that behavior.

Required replacement:

- patch `BenchmarkPipeline`;
- call `_run_single_scenario_strategy`;
- capture the actual `PipelineConfig`;
- assert:
  `canonical_project_root == Path(seven_arm_benchmark.__file__).resolve().parent`;
- assert:
  `python_executable == sys.executable`.

## 5.2 Repair tests do not prove fail-then-pass

Tests named:

```text
test_monolithic_migration_failure_repairs_attempted
test_monolithic_evaluator_failure_repairs_attempted
```

call `_run_regeneration_repair_flow` directly and assert the final result remains failed.

They do not prove:

```text
public run
→ first attempt fails
→ second generation occurs
→ second validation succeeds
→ final record succeeds
```

The independent audit proved the behavior directly, but the repository must preserve it through tests.

Required tests:

```text
test_public_monolithic_migration_failure_repairs_to_success
test_public_selective_evaluator_failure_repairs_to_success
```

Both call `BenchmarkRunner.run()`.

## 5.3 Agent feedback test does not execute the Agent

The test:

```text
test_agent_evaluator_failure_receives_checks_and_error
```

calls `_execute_scientific_validation` and `_scientific_feedback_channels`.

It does not call:

```text
_run_iterative_flow
revise_plan
```

Required test:

```text
test_public_agent_evaluator_failure_revises_and_preserves_transcript
```

It must assert:

```text
revise_plan called once
stdout contains evaluator stdout
stderr channel contains evaluator stderr
stderr channel contains semantic error
stderr channel contains public check
stderr channel does not contain evaluator source
final transcript exact
final evaluator result passed
```

## 5.4 Repair duration test has no duration assertion

The test:

```text
test_repair_validation_duration_sums_all_stages
```

asserts only:

```text
result.status == failed
```

It does not assert the duration.

Replace it with a deterministic public or focused test that asserts the exact sum of:

```text
initial migration duration
initial baseline duration
initial evaluator duration
repair scientific duration
```

Do not test wall-clock `duration_seconds`; test the stage aggregate field.

## 5.5 Persistence tests are fragmented

The persistence layer itself is tested correctly, and `_to_run_record_data` is tested correctly.

The missing combined proof is:

```text
Runner Agent record
→ seven_arm record_dict
→ _to_run_record_data
→ RunRecordStore append/load
→ NotebookExporter
```

A single focused integration-style unit test should use sentinel values and prove the complete forwarding chain.

No new production API is required.

---

# 6. Problems in the persisted report

`reports/latest_phase_report.md` is longer than the visible response, but it is not reliable.

## 6.1 Incorrect file status

The report describes `tests/unit/execution/test_r3d_wiring.py` as a new file in the correction commit.

Git shows it was modified; it already existed in the preceding R3D implementation.

## 6.2 Incorrect diff statistics

The report describes small `runner.py` line changes that do not match the actual commit diff.

The actual code commit includes a large Runner and test rewrite.

## 6.3 Nonexistent test classes and names

The report lists classes such as:

```text
TestValidationCommandPreflight
TestRepairEligibility
TestBoundedGeneration
```

The committed R3D test file uses module-level test functions.

It also lists test names that do not exist verbatim.

## 6.4 Unsupported “all public-path” claim

The report says all 54 tests are public-path tests.

Several tests call:

```text
_validate_scientific_configuration
_execute_scientific_validation
_scientific_feedback_channels
_is_repairable_failure
_scientific_record_fields
```

directly.

Private-helper tests are useful, but the report must describe them accurately.

## 6.5 Missing direct-script evidence

The master correction specification required three direct adversarial scripts.

The report does not list the actual inputs and outputs of those scripts.

## 6.6 File list mismatch

The report lists a documentation artifact not present in the documentation commit.

The final report must derive file scope from Git commands, not from an intended file list.

---

# 7. Required truthful final report

OpenCode must print the complete report in the visible response and save it to:

```text
reports/latest_phase_report.md
```

Length:

```text
1,800–2,500 words
```

Required sections:

## A. Model identity

```text
Requested model
Actual footer model
Provider
Mode
Elapsed time
```

## B. Git identity

```text
Branch
Starting HEAD
Code commit
Documentation commit
Final HEAD
Working tree
```

## C. R3D objective

Explain the exact production sequence:

```text
configuration preflight
→ strategy and generation
→ migration
→ baseline
→ evaluator
→ bounded repair or Agent revision
→ persistence
```

## D. Artifact table

For every changed file:

| File | Before | After | Reason | Dependency impact | Exact evidence |
|---|---|---|---|---|---|

Use actual Git diff results.

## E. RF-2 result

Explain:

```text
one configuration preflight
one scientific orchestrator
one record-field mapper
one failure mapper
one feedback mapper
dataclasses.replace wrapper
```

## F. Production direct scripts

List exact inputs and outputs for:

```text
configuration preflight
migration fail-to-pass repair
evaluator fail-to-pass repair
Agent evaluator revision
```

## G. Test taxonomy

Separate:

```text
public-path tests
private-helper tests
persistence tests
reporting tests
integration tests
```

Do not describe all tests as public-path.

## H. Complete gates

Report exact commands and counts.

## I. Commit scope

Use actual output of:

```text
git diff --name-status e61eb9a..9e28790
git diff --name-status 9e28790..HEAD
git show --stat 9e28790
git show --stat HEAD
```

## J. Technical debt

State:

```text
TD closed
TD still open
new TD introduced
```

The current open items are:

```text
TD-R3D-008 evaluator stderr omitted from Agent/repair feedback
TD-R3D-009 public-path regression tests incomplete
TD-PROCESS-006 R3D report contains inaccurate evidence
TD-PROCESS-007 visible OpenCode response omitted the required report
```

## K. Authorization

State:

```text
R3D final closure self-gates passed
independent audit pending
R4 blocked
```

Do not claim independent acceptance.

---

# 8. Authorized final closure files

## Code/test commit

Modify only:

```text
src/benchmark/execution/runner.py
tests/unit/execution/test_r3d_wiring.py
```

Modify one additional existing test file only if the real entry-point test cannot be located naturally in `test_r3d_wiring.py`.

Do not modify:

```text
pipeline.py
core models
persistence.py
R3B
R3C
scenario YAML
Agent strategy
Selective strategy
metrics
README
bundle
notebooks
```

## Documentation commit

Modify only:

```text
reports/latest_phase_report.md
docs/PROJECT_HANDOFF.md
docs/V2_R3B_TO_KAGGLE_NO_DISCRETION_EXECUTION_SPEC.md
selective_updates/CHANGE_INDEX.md
selective_updates/records/R3D-PRODUCTION-WIRING.md
selective_updates/records/TECHNICAL-DEBT-AND-REFACTOR-SCHEDULE.md
docs/R3D_FINAL_EVIDENCE_AND_REPORT_CLOSURE.md
```

---

# 9. Exact final closure tests

Add or replace these tests:

```text
test_real_entry_builds_scientific_pipeline_config
test_public_monolithic_migration_failure_repairs_to_success
test_public_selective_evaluator_failure_repairs_to_success
test_public_agent_evaluator_failure_revises_and_preserves_transcript
test_evaluator_feedback_includes_stdout_stderr_error_and_checks
test_repair_validation_duration_uses_complete_stage_sum
test_agent_record_round_trip_preserves_complete_evidence
```

No test may be skipped.

No test may assert only object type or status when its name claims a transition.

---

# 10. Gates

Run:

```powershell
python -m pytest tests/unit/execution/test_r3d_wiring.py -q

python -m pytest `
  tests/unit/execution/test_r3d_wiring.py `
  tests/unit/execution/test_runner.py `
  tests/unit/execution/test_pipeline.py `
  tests/unit/test_checkpoint.py `
  tests/unit/statistics/test_reporting.py `
  tests/contract/test_three_arm_core.py `
  -q

python -m pytest `
  tests/integration/test_su0010a_regeneration.py `
  tests/integration/test_su0011_iterative_agent.py `
  -q

python -m pytest -q

ruff check `
  src/benchmark/execution/runner.py `
  tests/unit/execution/test_r3d_wiring.py

mypy --strict src/benchmark/execution/runner.py

python -m compileall `
  src/benchmark/execution/runner.py `
  tests/unit/execution/test_r3d_wiring.py

git diff --check
```

---

# 11. Commits

Code/test commit:

```text
fix(validation): close final R3D evidence gaps
```

Documentation commit:

```text
docs(audit): record final R3D freeze candidate
```

Do not amend or squash the prior R3D commits.

---

# 12. Over-engineering limits

This final closure is intentionally small.

Production change:

```text
one evaluator feedback branch
```

Test changes:

```text
replace nominal evidence with public-path evidence
```

Documentation change:

```text
replace inaccurate report with Git-derived report
```

Forbidden:

- new helper framework;
- new public dataclass;
- Runner redesign;
- refactor of Agent strategy;
- metric arithmetic redesign;
- broad cleanup.

After this closure passes independent audit, R3D is frozen.

---

# 13. Current status

```text
R1 Repository Agent                  accepted
R2 Selective                         accepted
R3A Scenario metadata               accepted
R3B Migration runner                accepted and frozen
R3C Evaluator system                accepted and frozen
R3D scientific wiring core          independently reproduced
R3D evaluator feedback              one small defect
R3D test evidence                   incomplete
R3D report                          inaccurate and not visibly printed
R4                                  blocked
R5                                  pending
R6                                  pending
Kaggle                              blocked
Stable tag                          blocked
Pilot                               blocked
```

Near goal:

```text
one small R3D evidence closure
→ one independent audit
→ freeze R3D
→ begin R4
```

Distant goal:

```text
R4 truthful metrics
→ R5 nine local records
→ RF-4 cleanup and rerun
→ R6 bundle and push
→ nine real Qwen Kaggle runs
→ independent results audit
→ v2.0.0-scientific-smoke tag
→ Pilot
```

---

**End of final R3D evidence and report closure.**
