# R4 Pre-Commit Root Audit and Single-Pass Completion

**Document status:** Binding continuation contract for the existing uncommitted R4 working tree  
**Target branch:** `experiment/three-arm-smoke-v2`  
**Committed starting HEAD:** `b8724cc`  
**Current phase:** R4 — token limits and truthful workflow metrics  
**Independent audit model:** GPT-5.6 Thinking  
**Required OpenCode model:** DeepSeek V4 Flash Free — OpenCode Zen — Build  
**Real experiment model later:** Qwen2.5-Coder-7B-Instruct on Kaggle  
**Decision:** preserve the current working tree, complete all remaining R4 root defects before the first commit  
**R5 and later phases:** blocked  
**Final marker:** `R4_TOKEN_AND_METRIC_CONTRACT_AUDIT_REQUIRED`

---

# 1. Decision

Do not commit the current R4 working tree yet.

Do not reset, restore, stash, or start over. The current implementation contains useful work and the broad Windows test suite is green, but independent audit reproduced scientific token-budget violations that the current tests do not detect.

The current R4 work is still one uncommitted phase. Completing it now is not post-commit patching. It is the required internal correction window before the first R4 code commit.

The supplied Windows result is:

```text
1594 collected
1562 passed
32 skipped
0 failed
```

Independent Linux focused execution produced:

```text
83 R4 tests passed
```

Compilation passed and `git diff --check` found no whitespace errors.

These results prove broad compatibility. They do not yet prove the R4 scientific contract because several tests execute only arithmetic helpers instead of the real executor, Agent, CLI, persistence, and reporting paths.

---

# 2. Work already accepted in the current working tree

Preserve the following changes.

## 2.1 Stage separation

The Runner now separates:

```text
selection
initial regeneration
repair regeneration
migration
baseline validation
scenario evaluator
```

Repair tokens and calls are no longer intentionally stored inside initial regeneration fields.

## 2.2 Workflow accumulator

`_WorkflowMetricAccumulator` is the right architecture.

It centralizes:

```text
selection tokens/calls/duration/tool submetrics;
initial generation tokens/calls/duration;
repair tokens/calls/duration/attempts;
cumulative migration/baseline/evaluator durations;
workflow total tokens/calls/duration.
```

Do not replace it with another framework.

## 2.3 Exact `TokenUsage` identity

`TokenUsage` now requires:

```text
total_tokens = prompt_tokens + completion_tokens
```

and rejects booleans, negative values, and non-integers.

## 2.4 Accounting labels

The built-in backends expose the intended modes:

```text
Kaggle Qwen  → exact_tokenizer
OpenRouter   → provider_reported
Mock         → approximate_character
Dry run      → fixture_or_approximate
Null         → none
```

## 2.5 Qwen prompt counting

The Qwen backend no longer silently falls back to character approximation when tokenizer counting fails.

## 2.6 Persistence and reporting fields

Repair fields and `token_accounting_mode` have been added to persistence and reporting surfaces.

## 2.7 Existing R3D regression

The full suite is green and R3D behavior remains intact.

---

# 3. Root blocker A — total-workflow ceiling is not enforced within one executor execution

## 3.1 Independent reproduction

A public Monolithic run was executed with:

```text
three generated files
max_completion_tokens_per_call = 20
max_total_workflow_tokens = 30
each backend response = 13 prompt + 5 completion = 18 total
```

Observed:

```text
backend max_tokens values = [20, 20, 20]
backend calls = 3
record total_workflow_tokens = 54
BudgetManager total_tokens = 54
BudgetManager exhausted = true
final status = succeeded
```

The run exceeded a ceiling of 30 tokens and still succeeded.

This is a TD-0 scientific comparability blocker.

## 3.2 Root cause

`SharedRegenerationExecutor._execute_async` receives one value:

```text
remaining_total_workflow_tokens
```

It passes that unchanged to `resolve_completion_allowance` for every artifact.

It does not subtract token usage returned by earlier calls in the same executor execution.

The Runner records the complete executor usage only after all files have been processed, which is too late to gate later calls.

## 3.3 Required correction

Inside `_execute_async`, initialize:

```python
local_remaining_total = remaining_total_workflow_tokens
```

For every artifact:

```text
calculate prompt tokens;
calculate allowance from local remaining;
skip and stop later backend calls when allowance is zero;
call backend;
record the returned usage immediately;
when total ceiling is positive, subtract returned total usage from local remaining.
```

Do not use completion usage alone. The total-workflow ceiling includes prompt plus completion tokens.

When the backend response uses more tokens than the allowed completion value or more total tokens than the remaining total ceiling:

```text
preserve measured usage;
mark the current artifact rejected;
append a bounded protocol/budget failure;
do not write generated content;
do not perform later backend calls.
```

The Runner may later record the measured usage in `BudgetManager`; the executor must still gate calls locally.

---

# 4. Root blocker B — Repository Agent ignores the canonical allowance contract

## 4.1 Independent reproduction

The Agent initial selection was called with:

```text
max_completion_tokens_per_call = 4096
remaining_total_workflow_tokens = 10
exact prompt count = 50
```

Observed:

```text
backend max_tokens = 4096
returned usage = 51
```

The correct behavior is zero allowance and no backend call.

## 4.2 Current implementation defects

`analyze_impact` always uses:

```python
gen_max = max_completion_tokens_per_call
```

and ignores `remaining_total_workflow_tokens`.

`revise_plan` uses the legacy positional:

```python
remaining_tokens
```

and ignores both canonical explicit parameters.

The unit tests named as Agent limit tests call only `resolve_completion_allowance`; they do not execute the Agent.

`test_agent_eight_call_cap_is_independent_from_token_limit` contains only:

```python
assert True
```

This is not evidence.

## 4.3 Required correction

Reuse `resolve_completion_allowance` in both:

```text
analyze_impact
revise_plan
```

Before every Agent model call:

```text
count the current prompt through backend.count_prompt_tokens;
resolve allowance using per-call and local total values;
when allowance is zero, do not call the backend;
after every returned response, subtract its total usage from local remaining.
```

The local remaining value must be updated across all tool/exploration calls inside the same `analyze_impact` or `revise_plan` invocation.

Preserve the eight-call cap as an independent limit.

The legacy arguments may remain for compatibility, but new Runner call sites must use the explicit fields as the canonical source.

## 4.4 Agent failure accounting

When initial Agent exploration consumes model responses but fails to select paths, every returned `ImpactPrediction` must include the incremental `TokenUsage`.

The current early failure returns can lose already-consumed tokens.

Failed records must preserve them.

## 4.5 Backend overrun

After a returned Agent response, verify:

```text
completion_tokens <= supplied allowance;
total_tokens <= local remaining total when the ceiling is positive.
```

On violation:

```text
preserve the returned usage;
stop further Agent calls;
return a bounded prediction error;
do not accept the selected plan as trusted.
```

---

# 5. Root blocker C — real CLI and experiment entry do not carry the explicit R4 limits

## 5.1 Current production chain

The main experiment path currently does:

```python
max_tokens = args.max_tokens
```

It does not resolve or pass:

```text
args.max_completion_tokens_per_call
args.max_total_workflow_tokens
```

`_run_single_scenario_strategy` has no explicit parameters for these fields and hardcodes:

```python
max_completion_tokens_per_call=4096
```

Therefore the new visible CLI options do not control the real benchmark execution.

## 5.2 Required correction

Update the exact signatures:

```text
_stage_and_smoke_run
_run_single_scenario_strategy
```

to accept:

```text
max_completion_tokens_per_call
max_total_workflow_tokens
```

The legacy `max_tokens` remains compatibility-only.

Resolve explicit and legacy totals once.

The real `main()` path passes the canonical explicit values.

The pipeline receives the resolved values without hardcoding.

## 5.3 Metadata truth

The record dictionary must contain:

```text
max_completion_tokens_per_call
max_total_workflow_tokens
```

`_to_run_record_data` must not silently use `4096` and `0` when a real run used different values.

The persisted `model_metadata` must match the actual run.

## 5.4 Direct API conflict

`run_arm` must reject different positive explicit and legacy totals instead of silently selecting one through `or`.

---

# 6. Root blocker D — configuration and record invariants are incomplete

## 6.1 Configuration validation

`RunnerConfig` and `PipelineConfig` currently do not reject:

```text
zero/negative per-call limit;
negative total limit;
boolean values.
```

`ExecutionConfig` may coerce booleans because its integer fields are not strict.

`resolve_completion_allowance` also accepts boolean values through Python integer comparison semantics.

Add bounded validation without a new framework.

## 6.2 Duplicate persistence field

`RunRecordData` defines `repair_attempts` twice:

```text
once in the original top-level fields;
once in the new repair block.
```

Keep exactly one field.

Do not preserve duplicate annotations merely because dataclasses currently tolerate the final override.

## 6.3 Workflow identities

Independent construction showed that `RunRecord` accepts inconsistent values such as:

```text
selection_prompt + selection_completion != selection_total;
stage totals != total_workflow_tokens;
stage calls != total_workflow_model_calls;
stage durations != total_workflow_duration_seconds.
```

For new R4 records, validate the identities.

Backward compatibility rule:

```text
old records with all R4 stage totals at defaults remain loadable;
a record using any R4 workflow metric must satisfy the complete identities.
```

Use `math.isclose` for duration.

Also require all count fields to be non-boolean non-negative integers and all duration fields to be finite non-negative numbers.

---

# 7. Evidence defects in the current R4 tests

The specification names 88 tests.

The two new files currently contain 83 tests.

Six required tests are missing:

```text
test_public_agent_selection_tokens_are_not_double_counted
test_public_agent_tool_duration_is_submetric_only
test_public_agent_failed_run_preserves_selection_and_repair_metrics
test_public_repair_accumulates_baseline_duration_across_attempts
test_public_repair_accumulates_evaluator_duration_across_attempts
test_public_total_duration_equals_stage_sum
```

Several existing tests pass without executing their named production behavior.

## 7.1 Replace helper-only executor tests

These tests must use `SharedRegenerationExecutor`, not only the allowance function:

```text
test_three_files_each_receive_4096_when_total_unlimited
test_positive_total_ceiling_reduces_later_call
test_zero_allowance_skips_backend_call
test_backend_token_overrun_fails_closed_and_preserves_usage
```

## 7.2 Replace helper-only Agent tests

These must instantiate `IterativeRepositoryAgentStrategy` and capture actual backend limits:

```text
test_agent_initial_call_receives_per_call_limit
test_agent_revision_call_receives_per_call_limit
test_agent_unlimited_total_does_not_shrink_later_calls
test_agent_positive_total_can_reduce_later_call
test_agent_zero_allowance_does_not_call_backend
test_agent_prediction_usage_is_incremental_not_cumulative
test_agent_eight_call_cap_is_independent_from_token_limit
```

Delete the `assert True`.

## 7.3 Strengthen public integration

The current duration test only asserts:

```text
migration_duration_seconds >= 0
```

It must use sentinel stage durations and prove exact accumulation across attempts.

The complete boundary test currently checks field presence and one repair field.

It must assert every R4 token, call, duration, limit, and accounting-mode value through:

```text
public Runner
→ record dictionary
→ RunRecordData
→ JSONL
→ NotebookExporter
```

## 7.4 Real CLI/config test

`test_cli_explicit_limits_reach_pipeline_config` currently constructs `PipelineConfig` directly.

It must capture the config produced by the real entry function.

## 7.5 Real metadata tests

The Qwen and approximate metadata tests must test the actual conversion path, not manually construct metadata with the expected label.

---

# 8. One bounded completion design

Do not redesign R4.

Complete the current architecture with these root changes only:

```text
1. Executor-local total-budget state and overrun detection.
2. Agent-local allowance state and overrun detection.
3. Explicit token-limit propagation through the real entry chain.
4. Strict bounded config and record invariants.
5. Replace nominal tests and add the six missing tests.
6. Run RF-3 against the completed code.
```

Do not create a new production module.

Do not modify R3B, R3C, R3D validation behavior, scenario YAML, evaluators, migration runner, selection algorithms, bundles, notebooks, or README.

---

# 9. Required direct adversarial scripts

Run these outside Pytest before committing.

## Script A — executor positive ceiling

Input:

```text
three files
per-call = 20
total = 30
responses = 18 tokens each
```

Required:

```text
no run can consume 54;
later calls are reduced/stopped;
final result records the exact consumed usage;
run cannot succeed after ceiling violation.
```

## Script B — Agent zero allowance

Input:

```text
prompt count = 50
remaining total = 10
```

Required:

```text
backend calls = 0
bounded budget error
usage = 0
```

## Script C — real entry propagation

Capture the `PipelineConfig` produced by `_run_single_scenario_strategy` using:

```text
per-call = 2048
total = 9000
```

Required exact values:

```text
2048
9000
```

The record metadata must contain the same values.

## Script D — complete failed record

Run:

```text
Agent selection
initial regeneration
validation failure
repair generation
terminal evaluator failure
```

Print and verify all identities, persistence values, reporting values, and accounting mode.

---

# 10. RF-3 exit criteria

RF-3 is complete only when:

```text
no new V2 call uses ambiguous max_tokens as canonical;
one allowance function owns prompt/per-call/total interaction;
executor and Agent both use that function;
one accumulator owns workflow arithmetic;
repair is never included in initial regeneration metrics;
Agent deltas are never added twice;
scientific durations are cumulative;
tool duration is not double-counted;
entry, persistence, and reporting fields match;
duplicate repair_attempts is removed;
no dead compatibility branch introduced by R4 remains.
```

Do not clean unrelated code.

---

# 11. Final gates before the first R4 commit

Run:

```text
all 88+ R4 tests;
R4 integration;
R3D focused;
SU0010A regeneration integration;
SU0011 Agent integration;
scientific smoke compatibility;
full suite;
Ruff;
mypy strict;
compileall;
git diff --check.
```

No required R4 test may skip.

The known platform skips outside R4 may remain and must be reported accurately.

---

# 12. Commit and reporting discipline

## Code/test commit

Contains production and test files only.

Commit exactly:

```text
fix(metrics): separate per-call limits and workflow totals
```

## Documentation commit

Track the three existing phase/audit documents and update all authorized R4 handoff, report, change-index, phase-record, and debt files.

Commit exactly:

```text
docs(state): record R4 completion pending audit
```

## Report

Print and persist a truthful 2,200–3,000-word report.

It must state clearly:

```text
what each file changed;
the four independent audit reproductions;
which old tests were obsolete;
which tests were nominal and replaced;
exact unit/public/integration counts;
exact arithmetic;
RF-3 result;
static gates;
commit scopes;
technical debt;
known limitations;
R5 remains blocked pending independent audit.
```

Do not answer with a short summary followed by a marker.

End exactly:

```text
R4_TOKEN_AND_METRIC_CONTRACT_AUDIT_REQUIRED
```

---

# 13. Current project status

```text
R1 Repository Agent                  frozen
R2 Dependency-aware Selective        frozen
R3A Scenario metadata               frozen
R3B Migration runner                frozen
R3C Evaluator system                frozen
R3D Production scientific wiring    frozen
R4 implementation foundation        substantial and preserved
R4 total-ceiling enforcement        blocked
R4 Agent allowance                  blocked
R4 real entry propagation           blocked
R4 test evidence                    incomplete
R4 first commit                     not authorized yet
R5 local records                    blocked
R6 bundle                           blocked
Kaggle                              blocked
stable tag                          blocked
Pilot                               blocked
```

Near goal:

```text
one pre-commit R4 root completion
→ code and documentation commits
→ independent audit
→ freeze R4
→ immediately execute R5 nine local records
```

No additional infrastructure phase is planned between R4 and the first local benchmark records.

---

# Completion Addendum (2026-07-31)

The pre-commit R4 root completion described by this binding contract was executed in a single pass and committed:

```text
code commit:  e87d4ad  fix(metrics): separate per-call limits and workflow totals
docs commit:  docs(state): record R4 completion pending audit
```

Evidence produced:

- All ten root defects (D1–D10) closed; remaining R4 TD-0 = 0, TD-1 = 0.
- `tests/unit/execution/test_r4_token_and_metrics.py` — 66 passed.
- `tests/integration/test_r4_metric_contract.py` — 31 passed.
- R3D-adjacent regression — 177 passed; evaluator integrity — 50 passed, 1 pre-existing skip.
- Full suite — 1576 passed, 32 skipped, 0 failed.
- Direct scripts A/B/C1/C2/D met §7 acceptance; Script D showed `2048 / 9000` at every metadata boundary.
- Ruff 0 new, mypy --strict 0 new (baseline verified against HEAD worktree `b8724cc`); compileall 0; `git diff --check` clean.
- Detailed report: `reports/latest_phase_report.md` (2299 words).

Status: R4 **implemented — independent audit required**; not accepted, not frozen. R5 unauthorized pending audit.

**Final marker: `R4_TOKEN_AND_METRIC_CONTRACT_AUDIT_REQUIRED`**
