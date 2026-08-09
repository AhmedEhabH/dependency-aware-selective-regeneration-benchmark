# R4 Final Pre-Commit Closure

**Status:** Binding continuation for the current uncommitted R4 working tree  
**Branch:** `experiment/three-arm-smoke-v2`  
**Committed HEAD:** `b8724cc`  
**Independent audit model:** GPT-5.6 Thinking  
**Required OpenCode model:** DeepSeek V4 Flash Free — OpenCode Zen — Build  
**Scientific model later:** Qwen2.5-Coder-7B-Instruct on Kaggle  
**Goal:** finish R4 once, commit once, document once, audit, freeze  
**Do not start:** R5, R6, Kaggle, README, tag, or Pilot  

---

# 1. Decision

Preserve the current R4 implementation. Do not reset the whole working tree and do not start over.

The current production implementation has made substantial progress. Independent direct executions confirm that:

```text
positive total ceilings now reduce and stop later executor calls;
an executor overrun fails the run and preserves measured usage;
Repository Agent with zero allowance makes zero model calls;
the Windows full suite is green.
```

However, R4 is not ready for its first commit because the working tree contains unrelated lint-only edits, the committed report is being edited too early, several required tests are still nominal, configuration and record invariants are incomplete, and one metadata path does not always persist the resolved total.

This is still the internal correction window before the first R4 commit. It is not a post-commit patch cycle.

---

# 2. Current evidence

Researcher Windows evidence:

```text
1597 collected
1565 passed
32 skipped
0 failed
```

Independent focused evidence:

```text
R4 unit and integration tests pass;
Python compilation passes;
git diff --check is clean.
```

Independent direct executor case:

```text
per-call limit = 20
total ceiling = 30
backend reports 18 tokens per response

observed backend limits = [20, 2]
observed calls = 2
observed run status = failed
observed consumed tokens = 36
failure = backend completion overrun
```

The measured overrun is preserved, and a third call is not made. This is correct fail-closed behavior.

Independent direct Agent case:

```text
remaining total = 10
prompt count = 50

Agent backend calls = 0
regeneration backend calls = 0
selection tokens = 0
run status = failed
```

The Agent no longer calls the backend when the allowance is zero.

---

# 3. Restore unrelated files before any commit

The following current changes are lint-only, import-order-only, source-hash churn, or premature reporting. They are outside the R4 production contract.

Restore these exact files to `HEAD`:

```text
reports/latest_phase_report.md

src/benchmark/checkpoint/__init__.py
src/benchmark/checkpoint/package.py

tests/contract/test_three_arm_core.py

tests/evaluator_assets/todo_smoke_001_checks.py
tests/evaluator_assets/todo_smoke_001_checks.py.sha256
tests/evaluator_assets/todo_smoke_002_checks.py
tests/evaluator_assets/todo_smoke_002_checks.py.sha256
tests/evaluator_assets/todo_smoke_003_checks.py
tests/evaluator_assets/todo_smoke_003_checks.py.sha256

tests/unit/test_deterministic_run_id.py
tests/unit/test_hf_sync.py
tests/unit/test_su0005_explicit_identity.py
```

Reasons:

```text
the evaluator assets and hashes are frozen R3C scientific assets;
import sorting is not an R4 scientific change;
checkpoint package formatting is unrelated;
the final report must be regenerated after the code commit from actual Git evidence.
```

Use explicit file paths. Do not run a broad restore.

Do not restore the real R4 production or test work.

---

# 4. Authorized code and test scope

The R4 code commit may contain only these production files:

```text
seven_arm_benchmark.py
src/benchmark/checkpoint/persistence.py
src/benchmark/config/models.py
src/benchmark/core/models.py
src/benchmark/execution/budgets.py
src/benchmark/execution/pipeline.py
src/benchmark/execution/regeneration.py
src/benchmark/execution/runner.py
src/benchmark/llm/dry_run_backend.py
src/benchmark/llm/kaggle_qwen_backend.py
src/benchmark/llm/mock_backend.py
src/benchmark/llm/openrouter_backend.py
src/benchmark/statistics/reporting.py
src/benchmark/strategies/iterative_agent.py
```

Authorized tests:

```text
tests/unit/execution/test_r4_token_and_metrics.py
tests/integration/test_r4_metric_contract.py
tests/integration/test_scientific_smoke_v1_fixes.py
tests/integration/test_su0010a_regeneration.py
tests/integration/test_su0011_iterative_agent.py
tests/unit/execution/test_r3d_wiring.py
```

An additional existing test file may be modified only when a genuinely obsolete R4 assertion cannot be placed in the two new R4 files. Explain the exact dependency before editing.

No evaluator asset, migration runner, isolated evaluator, scenario YAML, bundle, notebook, README, or analysis algorithm may change.

---

# 5. Remaining production corrections

## 5.1 Resolved token-limit metadata

`_run_single_scenario_strategy` currently resolves:

```python
resolved_total = max_total_workflow_tokens or max_tokens
```

and passes `resolved_total` to `PipelineConfig`.

The output dictionary must persist the same resolved value:

```python
"max_total_workflow_tokens": resolved_total
```

It must not persist the unresolved explicit parameter when the legacy compatibility input supplied the actual positive total.

The value forwarded to `RunRecordData.model_metadata` must be exactly the value used by the Runner.

## 5.2 Conflict validation in direct APIs

Any public or semi-public execution entry that accepts both:

```text
max_tokens
max_total_workflow_tokens
```

must use the frozen conflict rule:

```text
both zero → unlimited
one positive → use it
both positive and equal → use it
both positive and different → ValueError
```

Do not use `explicit or legacy` before checking conflict.

Use one small private resolver in `seven_arm_benchmark.py` if needed. Do not add a new module.

## 5.3 RunnerConfig and PipelineConfig validation

Add `__post_init__` validation.

Reject:

```text
max_completion_tokens_per_call <= 0;
max_total_workflow_tokens < 0;
legacy max_tokens/max_tokens_per_run < 0;
boolean values for any token limit.
```

Resolve conflicts during validation or through a property that is always touched during construction. A configuration object with invalid token values must not remain silently usable.

## 5.4 ExecutionConfig strictness

Pydantic must not coerce:

```text
True → 1
False → 0
```

for R4 token limits.

Use strict integer validation for:

```text
max_completion_tokens_per_call
max_total_workflow_tokens
legacy max_tokens
```

Preserve existing valid integer behavior.

## 5.5 BudgetManager validation

Reject boolean values for:

```text
max_attempts
max_tokens
timeout_seconds
record_tokens(tokens)
```

Do not modify unrelated budget behavior.

## 5.6 RunRecord invariants

The current `RunRecord.__post_init__` validates only part of the R4 fields.

When any R4 workflow metric is used, require:

```text
selection_total_tokens
= selection_prompt_tokens + selection_completion_tokens

regeneration_total_tokens
= regeneration_prompt_tokens + regeneration_completion_tokens

repair_total_tokens
= repair_prompt_tokens + repair_completion_tokens

total_workflow_tokens
= selection_total_tokens
+ regeneration_total_tokens
+ repair_total_tokens

total_workflow_model_calls
= selection_model_calls
+ regeneration_model_calls
+ repair_model_calls

token_usage.prompt_tokens
= selection_prompt_tokens
+ regeneration_prompt_tokens
+ repair_prompt_tokens

token_usage.completion_tokens
= selection_completion_tokens
+ regeneration_completion_tokens
+ repair_completion_tokens

token_usage.total_tokens
= total_workflow_tokens

total_workflow_duration_seconds
= selection_duration_seconds
+ regeneration_duration_seconds
+ repair_duration_seconds
+ migration_duration_seconds
+ baseline_validation_duration_seconds
+ scenario_evaluator_duration_seconds
```

Use `math.isclose` for duration.

Do not add `selection_tool_duration_seconds`; it is a submetric of selection time.

Backward compatibility:

```text
a legacy record with every R4 stage metric at its default remains loadable;
a record using any R4 metric must satisfy all identities.
```

Validate every R4 count as a non-boolean, non-negative integer.

Validate every R4 duration as finite and non-negative.

## 5.7 Minor production cleanup

Remove the duplicated line:

```python
timeout = 1 if status == "timed_out" else 0
```

Do not perform other formatting cleanup.

---

# 6. Replace nominal tests with executable evidence

The current full suite is green partly because several tests call only the allowance helper or contain weak assertions.

Do not increase the test count for appearance. Replace nominal tests with the real path.

## 6.1 Executor tests

The following tests must instantiate and execute `SharedRegenerationExecutor`:

```text
test_three_files_each_receive_4096_when_total_unlimited
test_positive_total_ceiling_reduces_later_call
test_zero_allowance_skips_backend_call
test_backend_token_overrun_fails_closed_and_preserves_usage
test_executor_local_budget_contract
```

Required assertions include:

```text
actual captured max_tokens list;
actual backend call count;
actual result failures;
actual preserved measured token usage;
later artifacts not written after terminal overrun.
```

## 6.2 Agent tests

The following tests must instantiate `IterativeRepositoryAgentStrategy`, call `begin_run`, and execute the named method:

```text
test_agent_initial_call_receives_per_call_limit
test_agent_revision_call_receives_per_call_limit
test_agent_unlimited_total_does_not_shrink_later_calls
test_agent_positive_total_can_reduce_later_call
test_agent_zero_allowance_does_not_call_backend
test_agent_prediction_usage_is_incremental_not_cumulative
test_agent_eight_call_cap_is_independent_from_token_limit
test_agent_allowance_below_per_call_limit
```

Delete every `assert True`.

Test both `analyze_impact` and `revise_plan`.

## 6.3 Real entry propagation

Replace the direct `PipelineConfig` construction in:

```text
test_cli_explicit_limits_reach_pipeline_config
```

with a capture of the actual config created by:

```text
_run_single_scenario_strategy
```

Use:

```text
per-call = 2048
total = 9000
```

Assert exact config and record-dictionary values.

Add a compatibility case where:

```text
legacy total = 9000
explicit total = 0
```

and the metadata still reports `9000`.

Add a conflict case.

## 6.4 Public Agent metric tests

Add the missing public tests:

```text
test_public_agent_selection_tokens_are_not_double_counted
test_public_agent_tool_duration_is_submetric_only
test_public_agent_failed_run_preserves_selection_and_repair_metrics
```

Use exact sentinel values, not broad `>= 1` assertions.

## 6.5 Validation duration tests

Add:

```text
test_public_repair_accumulates_baseline_duration_across_attempts
test_public_repair_accumulates_evaluator_duration_across_attempts
test_public_total_duration_equals_stage_sum
```

Replace:

```python
assert duration >= 0
```

with exact deterministic duration assertions.

## 6.6 Complete boundary test

Strengthen:

```text
test_public_runner_to_jsonl_to_reporting_preserves_metric_identity
```

Assert every R4 field through:

```text
RunRecord
record_dict
RunRecordData
JSONL reload
NotebookExporter
```

Fields:

```text
all selection tokens/calls/durations/tool values;
all initial regeneration values;
all repair values and attempts;
all validation durations;
workflow totals;
per-call limit;
resolved total limit;
token accounting mode.
```

---

# 7. Required direct scripts

Run outside Pytest.

## Script A — unlimited executor

```text
three files
per-call = 4096
total = 0
```

Required:

```text
limits = [4096, 4096, 4096]
status succeeds
```

## Script B — positive total and overrun

```text
three files
per-call = 20
total = 30
responses report 18 tokens
```

Required:

```text
limits = [20, 2]
calls = 2
status fails
measured tokens preserved
third call absent
```

## Script C — Agent zero allowance and eight-call cap

Zero allowance:

```text
remaining = 10
prompt = 50
backend calls = 0
```

Independent cap:

```text
unlimited total
nine tool/model responses requested
actual model calls <= 8
bounded error after cap
```

## Script D — real entry to persistence/reporting

Use:

```text
per-call = 2048
total = 9000
```

Required:

```text
PipelineConfig = 2048 / 9000
record_dict = 2048 / 9000
RunRecordData metadata = 2048 / 9000
JSONL = 2048 / 9000
report output = complete R4 metrics
```

---

# 8. Gates

Run in this order:

```powershell
python -m pytest tests/unit/execution/test_r4_token_and_metrics.py -q
python -m pytest tests/integration/test_r4_metric_contract.py -q

python -m pytest `
  tests/unit/execution/test_r3d_wiring.py `
  tests/integration/test_scientific_smoke_v1_fixes.py `
  tests/integration/test_su0010a_regeneration.py `
  tests/integration/test_su0011_iterative_agent.py `
  -q

python -m pytest -q
```

Then:

```powershell
ruff check <only the authorized changed Python files>
mypy --strict <authorized changed production files>
python -m compileall src\benchmark seven_arm_benchmark.py `
  tests\unit\execution\test_r4_token_and_metrics.py `
  tests\integration\test_r4_metric_contract.py
git diff --check
```

No required R4 test may skip.

Do not run Ruff with automatic modification over frozen files.

---

# 9. RF-3 review

Before the code commit, verify:

```text
one allowance resolver;
executor decrements local total;
Agent decrements local total;
no ambiguous max_tokens in canonical R4 calls;
one metric accumulator;
no repair inside initial regeneration;
no double-counted Agent deltas;
no double-counted tool duration;
resolved limit reaches metadata;
complete persistence/reporting forwarding;
no duplicate repair_attempts;
no unrelated files remain modified.
```

No broad refactor.

---

# 10. Commits

## Code/test commit

Before staging, print:

```powershell
git diff --name-only
git diff --stat
git diff --check
```

Stage only authorized production and test paths.

Commit exactly:

```text
fix(metrics): separate per-call limits and workflow totals
```

## Documentation commit

After the code commit, generate a new `reports/latest_phase_report.md`.

Track and update:

```text
docs/ONE_PASS_PHASE_EXECUTION_PROTOCOL.md
docs/R3D_INDEPENDENT_AUDIT_AND_FREEZE_REPORT.md
docs/R4_PRECOMMIT_ROOT_AUDIT_AND_SINGLE_PASS_COMPLETION.md
docs/phase_specs/R4_SINGLE_PASS_SPEC.md
docs/phase_specs/R4_FINAL_PRECOMMIT_CLOSURE.md
docs/PROJECT_HANDOFF.md
docs/V2_R3B_TO_KAGGLE_NO_DISCRETION_EXECUTION_SPEC.md
reports/latest_phase_report.md
selective_updates/CHANGE_INDEX.md
selective_updates/records/TECHNICAL-DEBT-AND-REFACTOR-SCHEDULE.md
selective_updates/records/R4-TOKEN-AND-METRIC-CONTRACT.md
```

Do not update README.

Commit exactly:

```text
docs(state): record R4 completion pending audit
```

Require a clean tree.

---

# 11. Detailed visible report

OpenCode must print and persist a 2,200–3,000-word report.

It must clearly list:

```text
requested and actual model;
starting and final Git identity;
every production file and exact responsibility;
unrelated files restored;
all root defects and corrections;
real executor evidence;
real Agent evidence;
real entry evidence;
unit versus public versus integration tests;
exact arithmetic;
all four scripts;
RF-3;
full gate counts;
Ruff and mypy commands/results;
code and documentation commit scopes;
open and closed technical debt;
known limitations;
R5 blocked pending independent audit.
```

Do not print only a short summary and marker.

End exactly:

```text
R4_TOKEN_AND_METRIC_CONTRACT_AUDIT_REQUIRED
```

---

# 12. Project position

```text
R1–R3D                            accepted and frozen
R4 current implementation         preserved
R4 executor ceiling               independently reproduced as corrected
R4 Agent zero allowance           independently reproduced as corrected
R4 invariants and evidence        final completion required
R4 first commit                   pending
R5 nine local records             next immediately after R4 freeze
R6 bundle                         after R5
Kaggle                            after R6
stable scientific tag            after real-result audit
Pilot                             after Smoke
```

The next goal is not more infrastructure.

The next goal is:

```text
finish this one R4 working tree
→ independent audit
→ freeze
→ run the first nine local benchmark records.
```


# 13. Time-boxed execution plan

Use one uninterrupted OpenCode session for the remaining R4 work.

Recommended order:

```text
first 10 minutes:
restore unrelated files and confirm authorized diff;

next 25 minutes:
complete invariants, metadata resolution, and direct API conflict handling;

next 35 minutes:
replace nominal Executor and Agent tests and add missing public tests;

next 20 minutes:
run the four direct scripts and RF-3 review;

final period:
run focused, adjacent, full, and static gates;
commit code;
generate the full report;
commit documentation.
```

Do not stop after an intermediate green focused suite to ask whether to continue.

Do not spend time increasing the number of tests beyond the named contract.

When a new failure appears, classify it immediately as one of:

```text
R4 production defect;
obsolete test expectation;
test-fixture defect;
unrelated pre-existing failure;
environment/tooling failure.
```

Correct only the first three before commit.

For a claimed unrelated or pre-existing failure, provide:

```text
failing command;
failure text;
isolated rerun;
HEAD reproduction result;
reason it does not affect R4.
```

A test passing in isolation is not by itself proof that a full-suite failure is harmless. The full suite must be green before commit.

# 14. Stop conditions

Stop without committing when:

```text
an evaluator asset or its hash changes;
an R3B/R3C/R3D production file outside the authorized list is required;
a new dependency is required;
the real Qwen path cannot keep exact tokenizer accounting;
the public entry cannot carry the explicit limits without changing an unplanned API;
any required R4 test fails or skips;
the full suite fails;
Ruff or mypy reports a new R4 error;
the code staging includes documentation;
the documentation staging includes production code.
```

Print:

```text
R4_PHASE_BLOCKED

active model:
HEAD:
current diff:
first failing command:
root conflict:
files not committed:
```

Do not improvise around the blocker and do not create a partial commit.

# 15. Acceptance handoff

After both commits, the visible final response must provide enough information for an independent auditor to begin without asking OpenCode for clarification.

Print:

```text
code commit hash;
documentation commit hash;
git status --short;
focused R4 count;
R4 integration count;
R3D-adjacent count;
full-suite count;
Ruff result;
mypy result;
compileall result;
four direct-script outputs;
exact list of restored unrelated files;
exact list of committed production files;
exact list of committed tests;
exact list of documentation files;
remaining TD-0 count;
remaining TD-1 count.
```

The required counts are:

```text
remaining R4 TD-0 = 0
remaining R4 TD-1 = 0
```

Do not claim R4 accepted or frozen. State:

```text
R4 implementation complete;
R4 independent audit required;
R5 unauthorized until audit.
```

---

# R4 Completion Status (2026-07-31)

The single-pass closure described above was executed and committed:

```text
code commit:  e87d4ad  fix(metrics): separate per-call limits and workflow totals
docs commit:  docs(state): record R4 completion pending audit
```

Evidence: R4 unit 66 passed; R4 integration 31 passed; R3D-adjacent 177 passed; evaluator integrity 50 passed, 1 pre-existing skip; full suite 1576 passed, 32 skipped, 0 failed; direct scripts A/B/C1/C2/D acceptance met; Script D `2048 / 9000` at every boundary; ruff 0 new; mypy --strict 0 new (baseline vs HEAD `b8724cc`); compileall 0; `git diff --check` clean; remaining R4 TD-0 = 0, TD-1 = 0. Report: `reports/latest_phase_report.md` (2299 words).

Status: R4 implementation complete; independent audit required; R5 unauthorized until audit.
