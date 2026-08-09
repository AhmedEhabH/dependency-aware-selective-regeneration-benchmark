# R3D Root Correction and RF-2 Single-Pass Specification

**Document status:** Binding correction and refactor contract  
**Target branch:** `experiment/three-arm-smoke-v2`  
**Audited documentation HEAD:** `e61eb9a`  
**Audited R3D code checkpoint:** `e8d5eb4`  
**Accepted and frozen R3C checkpoint:** `c8c8213`  
**Independent audit model:** GPT-5.6 Thinking  
**Required OpenCode model:** DeepSeek V4 Flash Free through OpenCode Zen, Build mode  
**Actual model displayed by the preceding OpenCode run:** Big Pickle  
**Real scientific model later:** Qwen2.5-Coder-7B-Instruct on Kaggle  
**Current permission:** correct R3D and complete RF-2 only  
**R4, R5, R6, Kaggle, Pilot, merge, and stable tag:** blocked  

---

# 1. Binding audit verdict

R3D is **not accepted** at `e8d5eb4`.

The code checkpoint introduces a useful foundation:

- one `_execute_scientific_validation` entry point;
- migration before baseline before evaluator;
- generation-call and generated-artifact guards;
- new migration, baseline, and evaluator fields on `RunRecordData`;
- reporting fields for the three validation stages;
- a focused R3D test file;
- a green Windows full suite reported as `1451 passed, 33 skipped`;
- an independent Linux focused result of `27 passed, 1 skipped`.

However, the real production entry point is not configured to run the evaluator, the final `BenchmarkRunner.run()` wrapper discards the new fields, repair and Repository Agent revision do not work for migration/evaluator failures, several persistence/reporting fields are dropped, V2 missing metadata can return success, failure stages are collapsed, and most of the claimed 28 tests do not prove their names.

The planned RF-2 refactor was explicitly cancelled by OpenCode even though the researcher required it. This is the root reason duplicated record construction and validation feedback diverged.

The next task must correct the complete R3D contract and perform RF-2 in one bounded pass. It must not start R4.

---

# 2. Independent audit evidence

## 2.1 Git and process evidence

The supplied history is:

```text
e61eb9a docs(state): record R3D completion pending audit
e8d5eb4 feat(validation): wire migrations and evaluators into Runner
c8c8213 docs(state): synchronize R3C freeze handoff
```

The tree in the supplied ZIP is clean.

The requested model was DeepSeek V4 Flash Free, but the visible footer was:

```text
Build · Big Pickle
```

The footer is authoritative. The implementation report must not state DeepSeek was used.

The code commit contains `docs/PROJECT_HANDOFF.md`. The documentation commit changes only one line in `reports/latest_phase_report.md`. The required code/docs scope separation was therefore not followed.

The persisted latest report is still the R3C report with one R3D sentence inserted. It is not the required R3D artifact-by-artifact report.

## 2.2 Focused test evidence

The independent Linux environment ran:

```text
PYTHONPATH=src python -m pytest tests/unit/execution/test_r3d_wiring.py -q
```

Result:

```text
27 passed
1 skipped
```

The skipped test is the required Repository Agent production-path validation test.

Many passing tests are nominal rather than contractual:

- the Selective parameter is not applied to the Runner configuration;
- migration zero/two/changed tests fail because no migration directory exists rather than creating the named state;
- the all-stages success test runs no migration and no evaluator;
- the final-wrapper test asserts only `status`;
- the persistence test constructs a dataclass and checks assigned fields;
- the JSON test manually calls `json.dumps`, not `RunRecordStore`;
- evaluator-prompt and snapshot tests contain no assertions;
- repair tests assert only `result.passed is False`;
- the eight-call Agent test runs a non-Agent compatibility path;
- the missing-evaluator test actually supplies a canonical root through a helper fallback.

Test count is therefore not evidence of the required 28 behaviors.

## 2.3 Real entry-point configuration is absent

The production `_run_single_scenario_strategy` creates `PipelineConfig` without:

```text
canonical_project_root
python_executable
```

The independent audit captured the real constructed configuration:

```text
canonical_project_root = None
python_executable = ""
```

Every real V2 scenario has an evaluator asset. The run therefore performs model generation and later fails because the canonical root is missing.

The required values are:

```python
canonical_project_root=Path(__file__).resolve().parent
python_executable=sys.executable
```

This is a direct production blocker.

## 2.4 Final Runner wrapper drops stage and Agent fields

The audit patched `_run_attempt` to return a `RunRecord` containing:

```text
selection_tool_calls=7
selection_tool_transcript=("t",)
migration_generation_passed=True
generated_migration_paths=("m.py",)
baseline_validation_passed=True
scenario_evaluator_passed=True
```

The public `run()` result contained:

```text
selection_tool_calls=0
selection_tool_transcript=()
migration_generation_passed=None
generated_migration_paths=()
baseline_validation_passed=None
scenario_evaluator_passed=None
```

The manual reconstruction in `run()` does not forward the new fields or the existing Agent-tool fields.

## 2.5 V2 missing evaluator can return success

The independent audit called `_execute_scientific_validation` for:

```text
scenario_id=todo-smoke-001
evaluator_asset=""
post_generation_command=()
require_new_migration=False
baseline passed
one model call
one generated source
```

The committed method returned:

```text
passed=True
```

The required V2 metadata fail-closed rule is absent.

## 2.6 Empty Python executable silently succeeds

With:

```text
evaluator_asset non-empty
canonical_project_root valid
python_executable=""
```

the committed code substitutes:

```python
sys.executable
```

and may return success.

The researcher’s R3D contract requires missing Python executable configuration to fail closed. Defaults must be populated by Pipeline and entry point, not repaired silently inside validation.

## 2.7 Repair is blocked for migration and evaluator failures

`_is_repairable_failure` allows repair only when:

```python
functional_validation_passed is False
```

Current records represent:

```text
migration failure  → baseline mirror None
evaluator failure  → baseline mirror True
baseline failure   → baseline mirror False
```

Independent direct result:

```text
migration failure repairable: False
evaluator failure repairable: False
baseline failure repairable: True
```

Therefore Monolithic and Selective repair cannot repair migration or evaluator failures, although Section 34 requires both feedback paths.

The compatibility baseline mirror must not control complete scientific repair eligibility.

## 2.8 Repository Agent revision receives the wrong feedback

For an evaluator failure after a passing baseline, the Agent loop stores:

```python
last_val_result = sci_result.baseline
```

The audit ran a two-iteration Agent sequence. `revise_plan` received:

```text
exit_code=0
stdout="BASELINE_OK"
stderr=""
```

instead of:

```text
failed stage=scenario_evaluator
public checks
evaluator error
```

For a migration failure, `sci_result.baseline` is `None`; the next Agent iteration exits before `revise_plan`, so no revision occurs.

The required Agent test is skipped, which allowed this defect to remain.

## 2.9 Failure stages are collapsed

The specification requires:

```text
generation_guard
regeneration
migration_generation
baseline_validation
scenario_evaluator
configuration
budget
```

The current initial, repair, and Agent flows record validation failures as:

```text
scientific_validation
```

This prevents exact failure classification, correct repair routing, and truthful persistence.

## 2.10 Selection-tool persistence remains incomplete

`RunRecordData` has:

```text
selection_tool_calls
selection_tool_duration_seconds
selection_inspected_file_count
selection_tool_transcript
```

but:

- `BenchmarkRunner.run()` drops them;
- `_run_single_scenario_strategy` does not place them in `record_dict`;
- `_to_run_record_data` does not forward them;
- `NotebookExporter._serialize_record` does not serialize them.

The independent audit passed values `7`, `1.5`, `9`, and `["a"]` into `_to_run_record_data`; the resulting persisted object contained zeros and an empty transcript.

## 2.11 Failed repair/Agent records lose last stage evidence

Initial records extract stage fields from the current scientific result.

Final failed repair and Agent records set only:

```text
functional_validation_passed=False
```

and discard:

```text
migration result
generated migration paths
baseline result
evaluator checks
stage durations
```

A failed record is scientifically important and must preserve all available evidence.

## 2.12 Compatibility duration is not truthful

`functional_validation_passed` is intended only as a compatibility mirror of `baseline_validation_passed`.

The current code sets:

```text
functional_validation_duration_seconds =
migration + baseline + evaluator sequence duration
```

This no longer represents functional/baseline validation duration and risks double counting in R4.

For R3D, the compatibility duration must mirror the baseline duration. The full validation sequence contributes to total workflow duration through the sum of stage durations.

---

# 3. Accepted boundaries

Do not modify frozen R3B or R3C.

Preserve these public names:

```text
BenchmarkRunner
RunnerConfig
PipelineConfig
RunRecord
RunRecordData
```

Preserve:

```text
run_post_generation_command
run_scenario_evaluator
FunctionalValidator
```

Do not change scenario YAML, evaluator semantics, Selective algorithm, Repository Agent protocol, LLM backends, README, bundle, notebooks, or real experiment configuration.

Do not create a generic validation framework.

---

# 4. Authorized production files

```text
src/benchmark/execution/runner.py
src/benchmark/execution/pipeline.py
src/benchmark/core/models.py
src/benchmark/checkpoint/persistence.py
src/benchmark/statistics/reporting.py
seven_arm_benchmark.py
```

Modify `src/benchmark/execution/validation.py` only if a focused test proves a required typed behavior cannot be expressed through its existing API.

---

# 5. Authorized test files

```text
tests/unit/execution/test_r3d_wiring.py
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

The already-created `test_r3d_wiring.py` is explicitly authorized for the correction. Do not move it merely to satisfy the earlier file list.

---

# 6. RF-2 target design

RF-2 is mandatory before the correction code commit.

## 6.1 Typed scientific result

Use actual types:

```python
from benchmark.execution.post_generation import PostGenerationResult
from benchmark.execution.scenario_evaluator import ScenarioEvaluatorResult
```

Define:

```python
@dataclass(frozen=True)
class _ScientificValidationResult:
    migration: PostGenerationResult | None
    baseline: FunctionalValidationResult | None
    evaluator: ScenarioEvaluatorResult | None
    passed: bool
    failed_stage: str | None
    failure_kind: FailureKind | None
    feedback: str
    duration_seconds: float
```

No `object` and no `getattr` should be required for known stage results.

Every return path sets:

- `failed_stage`;
- `failure_kind`;
- bounded feedback;
- all stage results obtained before the failure.

Every call assigns:

```python
self._last_scientific_result = result
```

including failures.

## 6.2 One V2 metadata rule

Add a private helper:

```python
def _requires_scenario_evaluator(scenario: Scenario) -> bool:
    return bool(
        scenario.post_generation_command
        or scenario.require_new_migration
        or scenario.evaluator_asset
    )
```

For the current Smoke contract:

```text
post_generation metadata or require_new_migration
→ evaluator_asset must be non-empty
```

Legacy scenarios with all three fields empty retain compatibility.

Do not hardcode the three scenario IDs.

## 6.3 Preflight before model generation

Add:

```python
def _validate_scientific_configuration(
    self,
    scenario: Scenario,
) -> FailureRecord | None:
    ...
```

Call it from `run()` after isolation and before:

- Agent selection;
- backend generation;
- regeneration execution.

Fail with stage `configuration` and kind `harness_defect` when:

- regeneration is enabled and baseline command is empty;
- new migration is required but post-generation command is empty;
- scientific metadata requires an evaluator but evaluator asset is empty;
- evaluator asset is non-empty and canonical root is missing;
- evaluator asset is non-empty and Python executable is empty/whitespace.

Do not silently substitute `sys.executable` inside validation.

## 6.4 Real entry-point configuration

In `seven_arm_benchmark.py`, pass:

```python
canonical_project_root=Path(__file__).resolve().parent
python_executable=sys.executable
```

to `PipelineConfig`.

Add a focused test that captures the real `PipelineConfig` constructed by `_run_single_scenario_strategy`.

## 6.5 Exact stage sequence

`_execute_scientific_validation` remains the single stage orchestrator:

```text
generation_guard
→ migration_generation
→ baseline_validation
→ scenario_evaluator
→ final decision
```

Use these exact stage names.

Success for current V2 requires:

```text
model_calls > 0
generated source count > 0
migration passed
exactly one generated migration when required
baseline passed
evaluator passed when required
```

Later stages are skipped after an earlier untrusted failure.

## 6.6 One result-to-record mapping

Add one private helper:

```python
def _scientific_record_fields(
    result: _ScientificValidationResult | None,
) -> dict[str, Any]:
    ...
```

It returns exactly:

```text
migration_generation_passed
migration_duration_seconds
generated_migration_paths
baseline_validation_passed
baseline_validation_duration_seconds
scenario_evaluator_passed
scenario_evaluator_duration_seconds
scenario_evaluator_checks
functional_validation_passed
functional_validation_duration_seconds
```

Rules:

```text
functional_validation_passed == baseline_validation_passed
functional_validation_duration_seconds == baseline_validation_duration_seconds
```

Use this helper in:

- initial success/failure;
- repair success/failure;
- Agent success/failure.

No path manually reconstructs these fields independently.

## 6.7 Preserve final wrapper fields through `replace`

`RunRecord` is a frozen dataclass.

Replace the manual `run()` reconstruction with:

```python
from dataclasses import replace

return replace(
    record,
    identity=identity,
    duration_seconds=duration,
)
```

This preserves all current and future fields automatically.

Do not maintain another manual field list.

## 6.8 Stage-specific failure record

Add:

```python
def _failure_from_scientific_result(
    result: _ScientificValidationResult,
) -> FailureRecord:
    ...
```

Use:

```text
failure_kind = result.failure_kind
stage = result.failed_stage
message = bounded stage-specific message
details = bounded public feedback
```

Do not use `scientific_validation` as a persisted stage.

## 6.9 Repair eligibility

Replace compatibility-mirror gating.

A failed record is repairable when:

- status is failed;
- no failure kind is harness_defect, infrastructure, or timeout;
- at least one failure stage is:
  `generation_guard`, `regeneration`, `migration_generation`,
  `baseline_validation`, or `scenario_evaluator`;
- budget allows another attempt.

Migration and evaluator failures must reach the repair loop.

## 6.10 Shared repair feedback channels

Add:

```python
def _scientific_feedback_channels(
    result: _ScientificValidationResult,
) -> tuple[int, str, str]:
    ...
```

Mapping:

### Migration

```text
exit_code
stdout
stderr
```

### Baseline

```text
exit_code
stdout
stderr
```

### Evaluator

```text
exit_code
stdout
stderr plus public check names and error
```

Bounds:

```text
stdout <= 1000 characters
stderr/error <= 1000 characters
```

Never include:

- evaluator source;
- evaluator path content;
- Ground Truth;
- hidden-test descriptions.

Use the same channels for:

- Monolithic/Selective repair context;
- Repository Agent `revise_plan`.

## 6.11 Agent revision state

Replace:

```python
last_val_result
```

with:

```python
last_scientific_result
```

A migration, baseline, or evaluator failure can trigger revision.

`revise_plan` receives channels from the exact failed stage.

The Agent eight-call selection cap remains unchanged and must be tested through the real iterative flow.

## 6.12 Preserve failure evidence

Track the latest scientific result in repair and Agent loops.

The final failed record includes the latest available migration, baseline, evaluator, checks, paths, and durations.

Do not discard failed-attempt evidence.

---

# 7. Persistence and reporting completion

## 7.1 Entry record dictionary

Add:

```text
selection_tool_calls
selection_tool_duration_seconds
selection_inspected_file_count
selection_tool_transcript
```

to the dictionary returned by `_run_single_scenario_strategy`.

## 7.2 Conversion

Forward the same four fields in `_to_run_record_data`.

Convert tuple transcript to JSON list.

## 7.3 Reporting

Add the same four fields to `NotebookExporter._serialize_record`.

## 7.4 Real store round trip

Tests must use:

```python
RunRecordStore.append
RunRecordStore.load_all
```

Do not replace the persistence test with manual `json.dumps`.

## 7.5 Backward compatibility

A JSONL record missing all new fields loads with defaults.

An idempotent append with identical new fields remains idempotent.

A conflicting record differing only in one new field raises `RunRecordIntegrityError`.

---

# 8. Complete R3D test replacement

Do not keep nominal tests merely to preserve the number 28.

A test name must match its assertions.

## 8.1 Production entry and preflight

1. real `_run_single_scenario_strategy` passes canonical root and Python executable;
2. missing canonical root fails before regeneration executor call;
3. missing Python executable fails before regeneration executor call;
4. V2 metadata with missing evaluator fails before regeneration;
5. missing required migration command fails before regeneration;
6. legacy scenario with all metadata empty retains compatibility.

## 8.2 Exact stage order

For Monolithic and Selective, call the real regeneration flow with patched stage functions and record:

```text
migration
baseline
evaluator
```

Assert exact order and one call each.

For Repository Agent initial flow, assert the same order through the real iterative path.

No Agent test may be skipped.

## 8.3 Failure matrix

Create exact typed stage results, not unrelated filesystem failures:

7. migration command failure → stage migration_generation;
8. zero new migration → migration_generation;
9. two new migrations → migration_generation;
10. old migration changed → migration_generation;
11. baseline failure → evaluator not called;
12. evaluator failure → run failed;
13. baseline failure cannot be overridden;
14. all V2 stages pass;
15. zero model calls → generation_guard;
16. zero generated source → generation_guard.

Use real `PostGenerationResult`, `FunctionalValidationResult`, and `ScenarioEvaluatorResult` objects.

## 8.4 Wrapper and record evidence

17. public `run()` preserves every field, including all selection-tool fields;
18. failed initial record preserves partial stage evidence;
19. failed repair record preserves latest stage evidence;
20. failed Agent record preserves latest stage evidence;
21. compatibility baseline mirror and duration are exact.

## 8.5 Persistence and reporting

22. `_to_run_record_data` preserves all fields;
23. actual JSONL save/reload preserves all fields;
24. old record defaults load;
25. idempotent equality includes new fields;
26. reporting serializer contains all fields;
27. entry-point record dictionary contains all fields.

## 8.6 Leakage and isolation

28. evaluator metadata does not reach strategy inputs;
29. evaluator asset/path/check descriptions do not reach generation prompts;
30. evaluator asset never appears in workspace;
31. canonical snapshot hashes remain unchanged.

Tests 29–31 require actual assertions and before/after evidence.

## 8.7 Repair and Agent feedback

32. migration failure triggers Monolithic/Selective repair and bounded migration feedback;
33. baseline failure triggers repair and bounded baseline output;
34. evaluator failure triggers repair with checks/error but no source;
35. Agent migration failure calls `revise_plan` with migration feedback;
36. Agent evaluator failure calls `revise_plan` with evaluator checks/error;
37. Agent revision still respects the eight-call selection cap.

## 8.8 Configuration and stage classification

38. every failed scientific stage produces its exact `FailureRecord.stage`;
39. missing metadata uses `FailureKind.harness_defect`;
40. migration/baseline/evaluator correctness uses `FailureKind.build`.

More than 28 tests is acceptable because the original claimed tests did not cover the contract. Do not optimize for a fixed count.

---

# 9. Direct adversarial self-tests

Before the code commit, OpenCode runs three scripts outside Pytest.

## A. Entry configuration

Capture production `PipelineConfig` and print:

```text
canonical_project_root
python_executable
```

## B. Final wrapper

Create an inner record with sentinel values in every stage and Agent field.

Run through public `BenchmarkRunner.run()`.

Print equality of every field.

## C. Agent evaluator feedback

Run a two-attempt Agent flow:

```text
attempt 1 evaluator fails with check/error
attempt 2 succeeds
```

Print the exact `revise_plan` exit/stdout/stderr.

No evaluator source may appear.

---

# 10. RF-2 exit criteria

RF-2 is complete only when:

- one stage orchestrator exists;
- one scientific-to-record mapping exists;
- one stage-specific failure mapper exists;
- one repair-feedback mapper exists;
- public wrapper uses `dataclasses.replace`;
- repair and Agent use `_ScientificValidationResult`, not baseline-only state;
- no new V2 path uses `functional_validation_passed` as overall scientific success;
- no duplicated manual stage-field extraction remains in initial, repair, and Agent paths.

Do not refactor unrelated Runner selection, budget, regeneration, or state-machine logic.

---

# 11. Required quality gates

Run incrementally after each production file.

Final commands:

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

ruff check `
  src/benchmark/execution/runner.py `
  src/benchmark/execution/pipeline.py `
  src/benchmark/core/models.py `
  src/benchmark/checkpoint/persistence.py `
  src/benchmark/statistics/reporting.py `
  seven_arm_benchmark.py `
  tests/unit/execution/test_r3d_wiring.py `
  tests/unit/execution/test_runner.py `
  tests/unit/execution/test_pipeline.py `
  tests/unit/test_models.py `
  tests/unit/test_checkpoint.py `
  tests/unit/statistics/test_reporting.py `
  tests/integration/test_su0010a_regeneration.py `
  tests/integration/test_su0011_iterative_agent.py

mypy --strict `
  src/benchmark/execution/runner.py `
  src/benchmark/execution/pipeline.py `
  src/benchmark/core/models.py `
  src/benchmark/checkpoint/persistence.py `
  src/benchmark/statistics/reporting.py

python -m compileall `
  src/benchmark/execution/runner.py `
  src/benchmark/execution/pipeline.py `
  src/benchmark/core/models.py `
  src/benchmark/checkpoint/persistence.py `
  src/benchmark/statistics/reporting.py `
  seven_arm_benchmark.py

git diff --check
git diff --name-only
git diff --stat
```

No required R3D test may be skipped.

---

# 12. Commit discipline

## 12.1 Code commit

Stage explicit production and test files only.

Commit:

```text
fix(validation): complete R3D scientific wiring contract
```

## 12.2 Documentation commit

Update:

```text
docs/PROJECT_HANDOFF.md
reports/latest_phase_report.md
docs/V2_R3B_TO_KAGGLE_NO_DISCRETION_EXECUTION_SPEC.md
selective_updates/CHANGE_INDEX.md
selective_updates/records/TECHNICAL-DEBT-AND-REFACTOR-SCHEDULE.md
selective_updates/records/R3D-PRODUCTION-WIRING.md
docs/R3D_ROOT_CORRECTION_AND_RF2_SINGLE_PASS_SPEC.md
```

Commit:

```text
docs(audit): record R3D correction pending audit
```

No documentation file belongs in the code commit.

No empty documentation commit.

---

# 13. Technical debt register additions

Add these entries.

## TD-R3D-001 — production entry omits evaluator configuration

Severity:

```text
TD-0 scientific blocker
```

## TD-R3D-002 — final wrapper drops scientific and Agent fields

Severity:

```text
TD-1 evidence blocker
```

## TD-R3D-003 — migration/evaluator failures are not repairable

Severity:

```text
TD-0 execution blocker
```

## TD-R3D-004 — Agent receives baseline output for evaluator failure

Severity:

```text
TD-0 arm-contract blocker
```

## TD-R3D-005 — failure stages collapsed

Severity:

```text
TD-1 persistence and repair blocker
```

## TD-R3D-006 — selection-tool fields dropped from persistence/reporting

Severity:

```text
TD-1 evidence blocker
```

## TD-R3D-007 — nominal R3D tests

Severity:

```text
TD-1 because production wiring was not proven
```

## TD-PROCESS-004 — RF-2 cancelled despite binding phase plan

Severity:

```text
TD-2 process debt
```

## TD-PROCESS-005 — R3D report absent and code/docs mixed

Severity:

```text
TD-2 handoff debt
```

All TD-0 and TD-1 items must be closed before R3D acceptance.

---

# 14. Required detailed report

Print and persist a 1,800–2,500-word R3D report.

Required headings:

```text
A. Requested and actual model
B. Git identity
C. R3D objective and frozen boundaries
D. Artifact-by-artifact before/after table
E. Scientific validation state machine
F. Preflight evidence
G. Monolithic, Selective, repair, and Agent paths
H. Failure-stage matrix
I. Repair and Agent feedback evidence
J. Wrapper, persistence, JSONL, entry, and reporting evidence
K. Forty-contract-test results
L. Three direct adversarial scripts
M. RF-2 refactor evidence
N. Incremental failures and fixes
O. Final gates
P. Commit-scope proof
Q. Technical debt
R. Productivity metrics
S. Authorization
```

Report the model shown in the OpenCode footer.

State:

```text
R3B accepted and frozen
R3C accepted and frozen
R3D correction self-gates passed
R3D independent audit pending
R4 blocked
Kaggle/Pilot/merge/tag blocked
```

End exactly:

```text
R3D_ROOT_CORRECTION_AUDIT_REQUIRED
```

---

# 15. Over-engineering limits

The correction may add only these private structural helpers:

```text
_validate_scientific_configuration
_requires_scenario_evaluator
_scientific_record_fields
_failure_from_scientific_result
_scientific_feedback_channels
```

A smaller equivalent is acceptable.

Forbidden:

- new public validation service;
- plugin system;
- new external dependency;
- generic record builder framework;
- changes to R3B/R3C;
- changes to selection algorithms;
- changes to model backends;
- metrics redesign assigned to R4.

---

# 16. Project position

Current truthful status:

```text
R1 Repository Agent                  accepted
R2 Selective                         accepted
R3A Scenario metadata               accepted
R3B Migration runner                accepted and frozen
R3C Evaluator system                accepted and frozen
R3D wiring foundation               implemented
R3D production contract             correction required
R4 Token semantics                  blocked
R5 Nine local records               pending
R6 Bundle and push                  pending
Kaggle                              blocked
Stable tag                          blocked
Pilot                               blocked
```

Near goal:

```text
one cohesive R3D correction + RF-2
→ independent audit
→ freeze R3D
→ begin R4
```

Distant goal:

```text
R4 truthful metrics
→ R5 nine local non-dry records
→ RF-4 cleanup and rerun
→ R6 bundle and push
→ nine real Qwen Kaggle runs
→ independent result audit
→ v2.0.0-scientific-smoke tag
→ Pilot
```

---

**End of binding R3D correction specification.**
