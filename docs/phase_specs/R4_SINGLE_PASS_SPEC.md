# R4 Single-Pass Specification — Token Limits and Truthful Workflow Metrics

**Document status:** Binding implementation contract  
**Phase:** R4 — Token and metric semantics  
**Target branch:** `experiment/three-arm-smoke-v2`  
**Committed starting HEAD:** `b8724cc`  
**Accepted and frozen prerequisites:** R3B, R3C, and R3D  
**Planning and independent-audit model:** GPT-5.6 Thinking  
**Required OpenCode model:** DeepSeek V4 Flash Free — OpenCode Zen — Build  
**Real scientific model later:** Qwen2.5-Coder-7B-Instruct on Kaggle  
**Current implementation permission:** R4 only  
**R5, R6, Kaggle, Pilot, merge, and stable tag:** blocked  
**Required final marker:** `R4_TOKEN_AND_METRIC_CONTRACT_AUDIT_REQUIRED`

---

# 1. Starting repository state

Before OpenCode reads or edits any production file, it must print:

```text
actual active model
branch
HEAD
git status --short
```

The authorized starting state is:

```text
branch = experiment/three-arm-smoke-v2
HEAD = b8724cc
```

The working tree is intentionally allowed to contain exactly these untracked documentation files:

```text
?? docs/ONE_PASS_PHASE_EXECUTION_PROTOCOL.md
?? docs/R3D_INDEPENDENT_AUDIT_AND_FREEZE_REPORT.md
?? docs/phase_specs/R4_SINGLE_PASS_SPEC.md
```

The researcher will place this specification at:

```text
project/docs/phase_specs/R4_SINGLE_PASS_SPEC.md
```

No other modified or untracked file is authorized at the start.

If the active model is not DeepSeek V4 Flash Free, make no changes and end exactly:

```text
MODEL_MISMATCH_NO_CHANGES
```

If the branch, HEAD, or dirty-file set differs, make no changes and end:

```text
PHASE_BLOCKED

actual model:
branch:
HEAD:
dirty files:
reason:
```

Do not reset, restore, delete, stage, or commit the three authorized documents during production implementation. They belong only in the R4 documentation commit.

---

# 2. R4 objective

R4 must make every token, model-call, repair, duration, persistence, and reporting field truthful for all three experimental arms.

R4 proves:

```text
1. 4096 is a per-backend-call completion limit.
2. 4096 is never treated as an aggregate workflow budget.
3. An optional positive total-workflow ceiling is independent.
4. Every LLM call belongs to exactly one stage:
   selection, regeneration, or repair.
5. Every token belongs to exactly one stage.
6. Every model call belongs to exactly one stage.
7. Every validation duration is accumulated exactly once.
8. Selection tool duration remains a submetric and is not double-counted.
9. Failed and successful records obey the same metric identities.
10. In-memory, entry, JSONL, and reporting values are identical.
11. Real Qwen token counts are tokenizer-derived and cannot silently fall back.
12. Mock and scripted engineering counts are explicitly labelled approximate.
```

R4 does not:

```text
run the nine local production records;
build the Kaggle bundle;
modify scenario evaluators;
modify migration validation;
modify scientific-validation ordering;
change Selective scope;
change Repository Agent call or tool caps;
change the Qwen model;
change result-analysis algorithms;
update README.
```

---

# 3. Root problems in the current code

OpenCode must correct the root causes, not preserve old behavior merely because old tests expect it.

## 3.1 Explicit token-limit fields exist but are unused

`PipelineConfig` and `RunnerConfig` contain:

```python
max_completion_tokens_per_call: int = 4096
max_total_workflow_tokens: int = 0
```

The Runner currently constructs `BudgetManager` from legacy:

```python
config.max_tokens
```

and passes:

```python
self._budget.remaining_tokens
```

to code-writing and Agent calls.

The explicit R4 fields do not own runtime behavior.

## 3.2 Per-call and aggregate limits are conflated

`SharedRegenerationExecutor` currently accepts one ambiguous argument:

```python
max_tokens
```

It subtracts consumed tokens and prompt estimates, then sends the remainder as the backend completion limit.

Consequences:

```text
a 4096 workflow ceiling can make the second file receive fewer tokens;
input prompt tokens are treated as though they share the API output limit;
the argument name does not reveal whether it means per-call or aggregate.
```

## 3.3 Repository Agent uses ambiguous remaining-token arguments

Initial selection and revision calls use:

```text
max_tokens
remaining_tokens
```

The normal per-call completion limit is not passed independently from the total-workflow ceiling.

## 3.4 Repair generation is counted as initial regeneration

The initial code-writing attempt and every later repair attempt are accumulated into:

```text
regeneration_prompt_tokens
regeneration_completion_tokens
regeneration_total_tokens
regeneration_model_calls
regeneration_duration_seconds
```

There are no explicit repair metrics in `RunRecord`.

## 3.5 Scientific stage durations are not cumulative across attempts

The final stage pass/failure evidence comes from the latest scientific attempt.

The current duration fields can represent only the latest attempt while `total_workflow_duration_seconds` includes several scientific attempts.

The arithmetic cannot be reconstructed from the persisted fields.

## 3.6 Legacy aggregate fields are misleading

`RunRecord.token_usage` often contains selection tokens only.

`RunRecordData.model_calls` is currently derived as:

```text
1 when token_usage.total > 0
```

rather than the real workflow call count.

`RunRecordData.repair_attempts` is derived from configured maximum attempts rather than actual repair attempts.

## 3.7 Token usage does not enforce its own identity

`TokenUsage` validates non-negative fields but does not require:

```text
total_tokens = prompt_tokens + completion_tokens
```

## 3.8 Real Qwen token counting silently falls back

`KaggleQwenBackend.count_prompt_tokens` catches any exception and returns:

```text
max(1, len(prompt) // 4)
```

Publication-quality Qwen execution must fail when the tokenizer is unavailable. It must never silently convert exact accounting into an approximation.

## 3.9 Configuration identity is incomplete

The canonical CLI has only:

```text
--max-tokens
```

The config hash does not include token-limit settings.

Changing a completion limit or a total ceiling may therefore produce the same canonical run identity.

## 3.10 Reporting and persistence have no repair stage

The persistence model and report serializer cannot preserve repair tokens, calls, duration, or exact repair attempts.

---

# 4. Exact read order

OpenCode reads these files completely, in this exact order, before editing:

```text
1.  docs/phase_specs/R4_SINGLE_PASS_SPEC.md
2.  docs/ONE_PASS_PHASE_EXECUTION_PROTOCOL.md
3.  docs/R3D_INDEPENDENT_AUDIT_AND_FREEZE_REPORT.md
4.  src/benchmark/core/models.py
5.  src/benchmark/execution/budgets.py
6.  src/benchmark/execution/regeneration.py
7.  src/benchmark/strategies/iterative_agent.py
8.  src/benchmark/execution/runner.py
9.  src/benchmark/execution/pipeline.py
10. src/benchmark/checkpoint/persistence.py
11. src/benchmark/statistics/reporting.py
12. src/benchmark/llm/kaggle_qwen_backend.py
13. src/benchmark/llm/mock_backend.py
14. src/benchmark/llm/dry_run_backend.py
15. src/benchmark/llm/openrouter_backend.py
16. src/benchmark/config/models.py
17. seven_arm_benchmark.py
18. tests/unit/execution/test_budgets.py
19. tests/unit/execution/test_pipeline.py
20. tests/unit/test_models.py
21. tests/unit/test_checkpoint.py
22. tests/unit/statistics/test_reporting.py
23. tests/unit/test_config_models.py
24. tests/unit/llm/test_llm_kaggle_qwen_backend.py
25. tests/integration/test_su0010a_regeneration.py
26. tests/integration/test_su0011_iterative_agent.py
27. tests/integration/test_scientific_smoke_v1_fixes.py
28. tests/unit/execution/test_r3d_wiring.py
```

After reading those files, OpenCode may create the two authorized R4 test files without searching for alternative locations.

Do not perform broad searches such as:

```text
find . -type f
rg token .
rg metrics .
```

A narrow exact-symbol search inside the authorized files is allowed.

When an unplanned production file is genuinely required, stop before modifying it and print:

```text
UNPLANNED_READ_REQUIRED
file:
dependency:
reason:
```

---

# 5. Artifact map

## 5.1 Production files to modify

```text
src/benchmark/core/models.py
src/benchmark/execution/budgets.py
src/benchmark/execution/regeneration.py
src/benchmark/strategies/iterative_agent.py
src/benchmark/execution/runner.py
src/benchmark/execution/pipeline.py
src/benchmark/checkpoint/persistence.py
src/benchmark/statistics/reporting.py
src/benchmark/llm/kaggle_qwen_backend.py
src/benchmark/llm/mock_backend.py
src/benchmark/llm/dry_run_backend.py
src/benchmark/llm/openrouter_backend.py
src/benchmark/config/models.py
seven_arm_benchmark.py
```

## 5.2 New test files

```text
tests/unit/execution/test_r4_token_and_metrics.py
tests/integration/test_r4_metric_contract.py
```

## 5.3 Existing test files authorized for compatibility updates

```text
tests/unit/execution/test_budgets.py
tests/unit/execution/test_pipeline.py
tests/unit/test_models.py
tests/unit/test_checkpoint.py
tests/unit/statistics/test_reporting.py
tests/unit/test_config_models.py
tests/unit/llm/test_llm_kaggle_qwen_backend.py
tests/integration/test_su0010a_regeneration.py
tests/integration/test_su0011_iterative_agent.py
tests/integration/test_scientific_smoke_v1_fixes.py
tests/unit/execution/test_r3d_wiring.py
```

Do not rewrite old test files broadly. Change only assertions and call signatures made obsolete by the frozen R4 contract.

## 5.4 Documentation files for the second commit

```text
docs/ONE_PASS_PHASE_EXECUTION_PROTOCOL.md
docs/R3D_INDEPENDENT_AUDIT_AND_FREEZE_REPORT.md
docs/phase_specs/R4_SINGLE_PASS_SPEC.md
docs/PROJECT_HANDOFF.md
docs/V2_R3B_TO_KAGGLE_NO_DISCRETION_EXECUTION_SPEC.md
reports/latest_phase_report.md
selective_updates/CHANGE_INDEX.md
selective_updates/records/TECHNICAL-DEBT-AND-REFACTOR-SCHEDULE.md
selective_updates/records/R4-TOKEN-AND-METRIC-CONTRACT.md
```

## 5.5 Frozen files

Do not modify:

```text
src/benchmark/execution/post_generation.py
src/benchmark/execution/scenario_evaluator.py
tests/unit/execution/test_post_generation.py
tests/unit/execution/test_scenario_evaluator.py
tests/evaluator_assets/
tests/support/evaluator_fixture_workspaces.py
scenario YAML files
Selective algorithm and dependency-scope logic
Repository Agent repository tools
Kaggle bundle
notebooks
README.md
```

---

# 6. Dependency map

## 6.1 Token configuration chain

```text
CLI arguments
→ _compute_config_hash
→ _run_single_scenario_strategy
→ PipelineConfig
→ RunnerConfig
→ BudgetManager
→ Agent selection calls
→ SharedRegenerationExecutor calls
```

Every edge must have a test.

## 6.2 Metric chain

```text
backend LLMResponse.TokenUsage
→ selection/regeneration/repair stage accumulator
→ RunRecord
→ seven_arm record_dict
→ RunRecordData
→ RunRecordStore JSONL
→ NotebookExporter
→ reports
```

Every stage field must survive every edge exactly.

## 6.3 Duration chain

```text
selection wall time
regeneration executor duration
repair executor duration
migration duration
baseline duration
evaluator duration
→ total_workflow_duration_seconds
```

`selection_tool_duration_seconds` is contained inside selection wall time and is not added again.

`duration_seconds` remains complete wall-clock run time. It is not required to equal the stage sum because it also includes orchestration overhead.

## 6.4 Compatibility chain

```text
legacy CLI --max-tokens
legacy PipelineConfig.max_tokens_per_run
legacy RunnerConfig.max_tokens
→ one resolved max_total_workflow_tokens
```

The V2 path uses only the explicit names after resolution.

---

# 7. Frozen names

## 7.1 Configuration fields

```python
max_completion_tokens_per_call: int = 4096
max_total_workflow_tokens: int = 0
```

`0` total means unlimited.

Legacy aliases remain:

```python
max_tokens: int = 0
max_tokens_per_run: int = 0
```

They are compatibility inputs only.

## 7.2 New RunRecord and RunRecordData fields

```python
repair_prompt_tokens: int = 0
repair_completion_tokens: int = 0
repair_total_tokens: int = 0
repair_model_calls: int = 0
repair_duration_seconds: float = 0.0
repair_attempts: int = 0
token_accounting_mode: str = "unknown"
```

## 7.3 Token-accounting mode values

Use exactly:

```text
exact_tokenizer
provider_reported
approximate_character
fixture_or_approximate
none
unknown
```

Built-in backends expose a class or instance attribute named:

```python
token_accounting_mode
```

Exact assignments:

```text
KaggleQwenBackend  → exact_tokenizer
OpenRouterBackend  → provider_reported
MockLLMBackend     → approximate_character
DryRunLLMBackend   → fixture_or_approximate
NullLLMBackend     → none
unknown custom     → unknown
```

A scripted R5 backend will later declare its own mode.

## 7.4 Budget names

Add:

```python
BudgetManager.has_total_token_limit
BudgetManager.remaining_total_tokens
```

Keep:

```python
BudgetManager.remaining_tokens
```

as a deprecated read-only compatibility alias returning the same value.

Do not access:

```python
_budget._max_tokens
```

outside `budgets.py`.

## 7.5 Shared allowance function

Add in `budgets.py`:

```python
def resolve_completion_allowance(
    *,
    max_completion_tokens_per_call: int,
    remaining_total_workflow_tokens: int,
    prompt_tokens: int,
) -> int:
    ...
```

## 7.6 Regeneration executor signature

Use exactly:

```python
def execute(
    self,
    plan: RegenerationPlan,
    isolation: IsolationContext,
    requirement_delta: str = "",
    repair_context: str | None = None,
    *,
    max_completion_tokens_per_call: int = 4096,
    remaining_total_workflow_tokens: int = 0,
) -> RegenerationExecutionResult:
    ...
```

Apply the same keyword-only names to `_execute_async`.

## 7.7 Iterative Agent signatures

Use exactly:

```python
def analyze_impact(
    ...,
    max_completion_tokens_per_call: int = 4096,
    remaining_total_workflow_tokens: int = 0,
) -> ImpactPrediction:
```

and:

```python
def revise_plan(
    ...,
    max_completion_tokens_per_call: int = 4096,
    remaining_total_workflow_tokens: int = 0,
) -> ImpactPrediction:
```

Do not retain ambiguous `remaining_tokens` in new V2 call sites.

## 7.8 Private metric accumulator

Add inside `runner.py`:

```python
@dataclass
class _WorkflowMetricAccumulator:
    ...
```

Required methods:

```python
@classmethod
def from_record(cls, record: RunRecord) -> _WorkflowMetricAccumulator:
    ...

def add_selection(
    self,
    usage: TokenUsage,
    *,
    model_calls: int,
    duration_seconds: float,
    tool_calls: int = 0,
    tool_duration_seconds: float = 0.0,
    inspected_file_count: int = 0,
) -> None:
    ...

def add_code_generation(
    self,
    result: RegenerationExecutionResult,
    *,
    is_repair: bool,
) -> None:
    ...

def add_scientific(
    self,
    result: _ScientificValidationResult,
) -> None:
    ...

def as_record_fields(
    self,
    *,
    final_scientific_result: _ScientificValidationResult | None,
    token_accounting_mode: str,
) -> dict[str, Any]:
    ...
```

Do not create a new production module for this one private phase accumulator.

## 7.9 Commit messages

Code and tests:

```text
fix(metrics): separate per-call limits and workflow totals
```

Documentation:

```text
docs(state): record R4 completion pending audit
```

---

# 8. Configuration resolution contract

## 8.1 Validation

For every explicit or legacy field:

```text
per-call limit must be > 0
total-workflow ceiling must be >= 0
legacy total aliases must be >= 0
```

Boolean values are invalid even though `bool` subclasses `int`.

## 8.2 Alias resolution

Use one rule in `PipelineConfig`, `RunnerConfig`, `ExecutionConfig`, and CLI conversion.

```text
explicit_total = max_total_workflow_tokens
legacy_total = max_tokens or max_tokens_per_run
```

Rules:

```text
explicit_total=0 and legacy_total=0
→ resolved total = 0

explicit_total>0 and legacy_total=0
→ resolved total = explicit_total

explicit_total=0 and legacy_total>0
→ resolved total = legacy_total
→ compatibility path

explicit_total>0 and legacy_total>0 and equal
→ resolved total = explicit_total

explicit_total>0 and legacy_total>0 and different
→ configuration error
```

Do not guess precedence.

Add read-only properties:

```python
PipelineConfig.resolved_max_total_workflow_tokens
RunnerConfig.resolved_max_total_workflow_tokens
ExecutionConfig.resolved_max_total_workflow_tokens
```

## 8.3 Runner construction

Construct:

```python
BudgetManager(
    max_attempts=config.max_attempts,
    max_tokens=config.resolved_max_total_workflow_tokens,
    timeout_seconds=config.timeout_seconds,
)
```

`BudgetManager` owns only the total workflow ceiling.

It never owns the per-call completion limit.

## 8.4 CLI

Add visible options:

```text
--max-completion-tokens-per-call
--max-total-workflow-tokens
```

Defaults:

```text
4096
0
```

Retain:

```text
--max-tokens
```

as a hidden deprecated compatibility option with default `None`.

When both the legacy option and a different positive explicit total are supplied, terminate with a clear parser/configuration error.

## 8.5 Config hash

`_compute_config_hash` must include the resolved values:

```text
max_completion_tokens_per_call
max_total_workflow_tokens
```

The legacy spelling does not create a different hash when it resolves to the same canonical value.

Changing either canonical value changes the hash.

---

# 9. Completion allowance contract

`resolve_completion_allowance` implements one rule for Agent and code-writing calls.

## 9.1 Unlimited total

When:

```text
remaining_total_workflow_tokens = 0
```

return exactly:

```text
max_completion_tokens_per_call
```

Prompt length and previous calls do not reduce it.

## 9.2 Positive total ceiling

When a positive total remains:

```text
available_after_prompt
= remaining_total_workflow_tokens - prompt_tokens
```

Return:

```text
max(
    0,
    min(
        max_completion_tokens_per_call,
        available_after_prompt,
    ),
)
```

This is the only case where the normal per-call completion limit may be reduced.

Use the backend’s `count_prompt_tokens`.

For Qwen this count must be exact.

For mock/scripted engineering backends it may be approximate and the record is labelled accordingly.

## 9.3 Zero allowance

When allowance is zero:

```text
do not call the backend;
record a bounded total-workflow-budget failure;
do not write an artifact;
do not increment model-call count.
```

## 9.4 Backend contract violation

When a backend returns token usage inconsistent with the supplied allowance or the remaining total:

```text
preserve the measured token usage;
fail the current artifact/call closed;
do not perform later calls;
record a budget/protocol diagnostic.
```

Do not discard consumed tokens.

---

# 10. Real Qwen accounting contract

## 10.1 Prompt counting

`KaggleQwenBackend.count_prompt_tokens` must:

```text
load the real tokenizer;
return tokenizer-derived count;
raise ModelBackendError when tokenizer loading/counting fails.
```

It must not return a character approximation.

## 10.2 Generation response

`KaggleQwenBackend.generate` remains authoritative for:

```text
prompt_tokens
completion_tokens
total_tokens
finish_reason
```

Add a defensive identity check before returning:

```text
total_tokens == prompt_tokens + completion_tokens
```

## 10.3 Engineering backends

Mock and dry-run backends may use character approximations.

They must expose the correct `token_accounting_mode`.

OpenRouter uses provider-reported usage and mode `provider_reported`.

---

# 11. TokenUsage and model invariants

## 11.1 TokenUsage

`TokenUsage.__post_init__` requires:

```text
all fields are integers, not booleans;
all fields are non-negative;
total_tokens == prompt_tokens + completion_tokens.
```

## 11.2 RunRecord metric values

Validate:

```text
all token and call counts are integers, not booleans, and non-negative;
all duration values are finite and non-negative;
repair_attempts is a non-negative integer;
token_accounting_mode is one of the frozen values.
```

## 11.3 Stage identities

For R4-generated records:

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
```

Use exact integer equality.

## 11.4 Duration identity

```text
total_workflow_duration_seconds
= selection_duration_seconds
+ regeneration_duration_seconds
+ repair_duration_seconds
+ migration_duration_seconds
+ baseline_validation_duration_seconds
+ scenario_evaluator_duration_seconds
```

Use `math.isclose` with:

```text
rel_tol=1e-9
abs_tol=1e-9
```

Do not add `selection_tool_duration_seconds` separately.

## 11.5 Legacy compatibility

Old persisted records missing R4 fields load with defaults.

Do not reject an old record merely because all stage metrics are zero while legacy `token_usage` is non-zero.

Every new Runner-produced record must satisfy the complete R4 identities.

---

# 12. Metric ownership

## 12.1 Selection

Selection owns:

```text
all LLM calls made to choose or revise the artifact scope;
all prompt/completion tokens from those calls;
strategy wall-clock time;
repository tool calls;
tool duration;
inspected file count;
tool transcript.
```

For Repository Agent, each revision call remains selection even after a failed validation attempt.

Returned `ImpactPrediction.token_usage` must contain only the delta produced by that call to `analyze_impact` or `revise_plan`.

Cumulative Agent totals must not be added again.

## 12.2 Initial regeneration

Regeneration owns:

```text
the first SharedRegenerationExecutor execution;
all code-writing backend calls in that execution;
its token usage;
its model calls;
its executor duration.
```

Several selected files may create several backend calls.

They all remain initial regeneration because they belong to the first code-writing attempt.

## 12.3 Repair

Repair owns:

```text
every SharedRegenerationExecutor execution after the first failed attempt;
every code-writing call containing repair/validation feedback;
its tokens;
its calls;
its executor duration;
the number of repair execution attempts.
```

Repository Agent selection revision stays selection.

Repository Agent code writing after the first failed attempt is repair.

## 12.4 Scientific stages

Migration, baseline, and evaluator:

```text
use no LLM tokens;
use no LLM model calls;
own their cumulative wall-clock durations across every initial and repair attempt.
```

Final booleans, migration paths, and evaluator checks reflect the latest available scientific attempt.

Durations are cumulative.

## 12.5 Legacy token_usage

For every new non-dry Runner record:

```python
token_usage = TokenUsage(
    prompt_tokens=(
        selection_prompt_tokens
        + regeneration_prompt_tokens
        + repair_prompt_tokens
    ),
    completion_tokens=(
        selection_completion_tokens
        + regeneration_completion_tokens
        + repair_completion_tokens
    ),
    total_tokens=total_workflow_tokens,
)
```

This legacy aggregate is no longer selection-only.

## 12.6 Legacy model_calls and repair_attempts

In `RunRecordData`:

```text
model_calls = total_workflow_model_calls
repair_attempts = exact repair_attempts
```

Never infer model calls from whether token usage is non-zero.

Never infer repair attempts from configured maximum attempts.

---

# 13. Workflow metric accumulator

The private `_WorkflowMetricAccumulator` is the only owner of arithmetic accumulation in Runner.

It stores:

```text
selection prompt/completion/calls/duration/tool submetrics
initial regeneration prompt/completion/calls/duration
repair prompt/completion/calls/duration/attempts
cumulative migration duration
cumulative baseline duration
cumulative evaluator duration
```

## 13.1 `add_selection`

Add only incremental `TokenUsage`.

Reject inconsistent usage through `TokenUsage`.

For iterative strategy, model-call count comes from strategy counter deltas.

## 13.2 `add_code_generation`

When `is_repair=False`, add to regeneration.

When `is_repair=True`, add to repair and increment `repair_attempts` once for the executor execution, not once per generated file.

## 13.3 `add_scientific`

Add each available stage duration independently:

```text
migration when migration result exists;
baseline when baseline result exists;
evaluator when evaluator result exists.
```

Do not add the aggregate `_ScientificValidationResult.duration_seconds` to the total identity.

The aggregate duration may include orchestration overhead and remains diagnostic only.

## 13.4 `from_record`

Reconstruct exact accumulator state from the first attempt before the repair loop.

It must preserve:

```text
selection fields;
initial regeneration fields;
existing repair fields;
cumulative validation durations;
tool submetrics.
```

## 13.5 `as_record_fields`

Return all frozen metric fields and the final stage evidence.

It computes the identities in one place.

Initial, successful repair, failed repair, successful Agent, failed Agent, timeout, and budget-exhaustion paths use this one mapping when stage metrics exist.

---

# 14. Runner call-limit behavior

## 14.1 Monolithic and Selective

For the first executor call:

```text
max_completion_tokens_per_call
= config.max_completion_tokens_per_call

remaining_total_workflow_tokens
= budget.remaining_total_tokens
```

After selection tokens are recorded.

For every repair executor call, pass the same per-call limit and current remaining total.

## 14.2 Repository Agent selection

Every Agent model call receives:

```text
max_completion_tokens_per_call
```

or the smaller positive exceptional allowance under a positive total ceiling.

The eight-call cap remains separate.

## 14.3 Repository Agent code writing

First executor execution is regeneration.

Later executor executions are repair.

## 14.4 Budget recording

Record measured tokens after every Agent or executor result.

Failed parsing, empty output, fenced output, backend error after token-bearing response, validation failure, and final failed run must preserve consumed token metrics.

Backend exceptions that produce no response add no tokens and no model call unless the backend call was actually initiated and the current existing contract counts it. R4 must choose one consistent rule and test it. The frozen rule is:

```text
a model call is counted when a backend LLMResponse is returned;
an exception without LLMResponse does not increment model_calls.
```

---

# 15. Persistence contract

Add all R4 fields to `RunRecordData`.

`RunRecordStore` must preserve them through actual JSONL append/load.

Backward compatibility:

```text
old JSONL without repair or accounting fields
→ loads with default values.
```

Idempotency:

```text
same run ID + identical R4 fields
→ idempotent skip.

same run ID + one different repair/token/accounting field
→ RunRecordIntegrityError.
```

`model_metadata` includes:

```text
model
dry_run
token_accounting_mode
max_completion_tokens_per_call
max_total_workflow_tokens
```

All values are serialized as strings where the existing metadata type requires strings.

---

# 16. Reporting contract

`NotebookExporter._serialize_record` includes:

```text
repair_prompt_tokens
repair_completion_tokens
repair_total_tokens
repair_model_calls
repair_duration_seconds
repair_attempts
token_accounting_mode
```

Existing stage fields remain.

Add aggregate report columns only when the current reporting API already serializes direct RunRecordData fields. Do not redesign statistical analysis.

Reporting tests use actual serializer output and assert exact values.

---

# 17. Entry-point contract

## 17.1 Function signatures

Update:

```text
run_arm
_stage_and_smoke_run
_run_single_scenario_strategy
```

to accept canonical explicit fields.

Legacy `max_tokens` may remain as an optional compatibility parameter only where existing external tests require it.

The canonical internal call uses:

```text
max_completion_tokens_per_call
max_total_workflow_tokens
```

## 17.2 Pipeline construction

Every real path passes both explicit fields to `PipelineConfig`.

## 17.3 Record dictionary

Add all repair and accounting fields.

## 17.4 `_to_run_record_data`

Forward every field.

Set:

```text
model_calls = total_workflow_model_calls
repair_attempts = record_dict repair_attempts
```

## 17.5 Config hash

Hash canonical resolved settings.

Equivalent legacy and explicit totals produce the same hash.

Different canonical settings produce different hashes.

---

# 18. Exact test architecture

## 18.1 New unit file

Create:

```text
tests/unit/execution/test_r4_token_and_metrics.py
```

Use module-level test functions grouped with comment headings.

Do not invent test classes that the report later claims incorrectly.

## 18.2 New integration file

Create:

```text
tests/integration/test_r4_metric_contract.py
```

It calls real public paths and actual persistence/reporting APIs.

## 18.3 Test helper restrictions

A helper may prepare deterministic backends and workspaces.

It must not:

```text
manually construct the final RunRecord being tested;
calculate expected values by calling the same production helper;
mock the public Runner orchestration;
skip the real persistence or reporting boundary.
```

---

# 19. Unit and property test matrix

Implement every test below. Names are frozen.

## A. TokenUsage

```text
test_token_usage_requires_integer_values
test_token_usage_rejects_boolean_values
test_token_usage_rejects_negative_values
test_token_usage_rejects_inconsistent_total
test_token_usage_accepts_exact_identity
```

## B. Configuration resolution

```text
test_runner_config_defaults_to_4096_per_call_and_unlimited_total
test_pipeline_config_defaults_to_4096_per_call_and_unlimited_total
test_execution_config_defaults_to_4096_per_call_and_unlimited_total
test_explicit_total_workflow_ceiling_resolves
test_legacy_runner_total_alias_resolves
test_legacy_pipeline_total_alias_resolves
test_equal_explicit_and_legacy_totals_are_allowed
test_conflicting_explicit_and_legacy_totals_fail
test_zero_or_negative_per_call_limit_fails
test_negative_total_workflow_limit_fails
test_boolean_token_limits_fail
```

## C. Budget and allowance

```text
test_unlimited_total_returns_full_per_call_allowance
test_previous_calls_do_not_reduce_unlimited_allowance
test_positive_total_reduces_allowance_only_when_needed
test_prompt_tokens_are_subtracted_only_under_positive_total
test_prompt_equal_to_remaining_total_returns_zero
test_allowance_rejects_invalid_inputs
test_budget_manager_exposes_total_limit_without_private_access
test_budget_manager_unlimited_remaining_is_zero_with_explicit_flag
test_budget_records_measured_tokens_on_failed_run
```

## D. SharedRegenerationExecutor

```text
test_three_files_each_receive_4096_when_total_unlimited
test_unlimited_call_does_not_subtract_prompt_estimate
test_positive_total_ceiling_reduces_later_call
test_zero_allowance_skips_backend_call
test_backend_token_overrun_fails_closed_and_preserves_usage
test_executor_rejects_zero_per_call_limit
test_executor_rejects_negative_remaining_total
test_executor_reports_exact_prompt_completion_total_and_calls
```

## E. Repository Agent limits and increments

```text
test_agent_initial_call_receives_per_call_limit
test_agent_revision_call_receives_per_call_limit
test_agent_unlimited_total_does_not_shrink_later_calls
test_agent_positive_total_can_reduce_later_call
test_agent_zero_allowance_does_not_call_backend
test_agent_prediction_usage_is_incremental_not_cumulative
test_agent_eight_call_cap_is_independent_from_token_limit
```

## F. Accumulator identities

```text
test_accumulator_selection_identity
test_accumulator_initial_regeneration_identity
test_accumulator_repair_identity
test_accumulator_cumulative_scientific_durations
test_accumulator_tool_duration_is_not_double_counted
test_accumulator_total_token_identity
test_accumulator_total_call_identity
test_accumulator_total_duration_identity
test_accumulator_from_record_preserves_all_metrics
test_accumulator_failed_record_preserves_consumed_metrics
```

## G. RunRecord semantics

```text
test_new_record_legacy_token_usage_mirrors_workflow_total
test_new_record_model_calls_equal_workflow_calls
test_repair_attempts_count_executor_attempts_not_files
test_record_rejects_negative_repair_metrics
test_record_rejects_invalid_accounting_mode
test_duration_identity_uses_float_tolerance
```

## H. Qwen and accounting mode

```text
test_qwen_prompt_count_uses_tokenizer
test_qwen_prompt_count_failure_raises_model_backend_error
test_qwen_response_token_identity
test_builtin_backends_expose_frozen_accounting_modes
```

---

# 20. Public-path and integration test matrix

Implement all tests below in:

```text
tests/integration/test_r4_metric_contract.py
```

## I. CLI and config identity

```text
test_cli_defaults_resolve_to_4096_and_unlimited
test_cli_explicit_limits_reach_pipeline_config
test_cli_conflicting_legacy_and_explicit_total_fails
test_config_hash_changes_with_per_call_limit
test_config_hash_changes_with_total_limit
test_legacy_and_explicit_equivalent_total_share_hash
```

## J. Monolithic and Selective

```text
test_public_monolithic_three_file_run_gives_each_call_4096
test_public_selective_three_file_run_gives_each_call_4096
test_public_monolithic_initial_and_repair_metrics_are_separate
test_public_selective_initial_and_repair_metrics_are_separate
test_public_failed_repair_preserves_all_consumed_tokens
```

For the repair tests, use:

```text
initial executor attempt;
validation failure;
one repair executor attempt;
success or terminal failure.
```

Assert exact numeric fields.

## K. Repository Agent

```text
test_public_agent_selection_revision_and_code_repair_are_separate
test_public_agent_selection_tokens_are_not_double_counted
test_public_agent_tool_duration_is_submetric_only
test_public_agent_failed_run_preserves_selection_and_repair_metrics
```

## L. Validation duration accumulation

```text
test_public_repair_accumulates_migration_duration_across_attempts
test_public_repair_accumulates_baseline_duration_across_attempts
test_public_repair_accumulates_evaluator_duration_across_attempts
test_public_total_duration_equals_stage_sum
```

Use deterministic patched typed stage results with sentinel durations.

## M. Persistence and reporting

```text
test_record_dict_contains_complete_r4_metrics
test_run_record_data_contains_complete_r4_metrics
test_jsonl_round_trip_preserves_complete_r4_metrics
test_old_jsonl_defaults_r4_fields
test_idempotency_compares_repair_fields
test_reporting_serializes_complete_r4_metrics
test_model_metadata_labels_exact_qwen_accounting
test_model_metadata_labels_approximate_engineering_accounting
```

## N. Complete boundary test

```text
test_public_runner_to_jsonl_to_reporting_preserves_metric_identity
```

This test must cross:

```text
public Runner
→ record dictionary
→ _to_run_record_data
→ RunRecordStore append/load
→ NotebookExporter
```

Use sentinel token and duration values and assert exact equality at every boundary.

---

# 21. Expected exact arithmetic example

At least one public integration test uses these values:

## Selection

```text
prompt = 11
completion = 7
calls = 1
duration = 1.0
tool duration = 0.25
```

## Initial regeneration

Two files:

```text
call 1 = prompt 13, completion 5
call 2 = prompt 17, completion 6
calls = 2
duration = 2.0
```

Totals:

```text
prompt = 30
completion = 11
total = 41
```

## Repair

One file:

```text
prompt = 19
completion = 8
calls = 1
duration = 3.0
repair_attempts = 1
```

## Validation durations across attempts

```text
migration = 0.4 + 0.6 = 1.0
baseline = 0.5 + 0.7 = 1.2
evaluator = 0.8 + 0.9 = 1.7
```

## Expected identities

```text
selection total = 18
regeneration total = 41
repair total = 27
total workflow tokens = 86

total workflow calls = 1 + 2 + 1 = 4

total workflow duration
= 1.0 + 2.0 + 3.0 + 1.0 + 1.2 + 1.7
= 9.9
```

Do not add `0.25` tool duration again.

Legacy aggregate:

```text
prompt = 11 + 30 + 19 = 60
completion = 7 + 11 + 8 = 26
total = 86
```

Every boundary must preserve these values.

---

# 22. Combined adversarial cases

## Case 1 — unlimited multi-file generation

```text
three selected files
per-call limit = 4096
total ceiling = 0
large prompt counts
```

Required backend limits:

```text
[4096, 4096, 4096]
```

## Case 2 — positive total ceiling

Use a deterministic backend and exact prompt counts.

```text
per-call limit = 20
remaining total = 30
first prompt = 5
first completion usage = 10
second prompt = 10
```

Required:

```text
first allowance = 20
known consumed after first = 15
second available after prompt = 5
second allowance = 5
```

A third call receives zero allowance and is not executed.

## Case 3 — failed repair

```text
selection succeeds
initial regeneration consumes tokens
baseline fails
repair regeneration consumes tokens
evaluator fails
run terminates
```

The failed record must preserve all selection, initial, repair, and validation metrics.

## Case 4 — Agent cumulative counters

```text
initial selection call
tool call
revision selection call
initial code generation
repair code generation
```

Returned predictions expose incremental token deltas.

Final selection totals equal the sum of the two Agent call deltas once, not twice.

---

# 23. Incremental implementation order

OpenCode must follow this order.

## Step 1 — TokenUsage and configuration models

Modify:

```text
core/models.py
config/models.py
pipeline.py
runner config definition only
```

Run:

```powershell
python -m py_compile <each file>
python -m pytest tests/unit/test_models.py tests/unit/test_config_models.py tests/unit/execution/test_pipeline.py -q
ruff check <each changed file>
mypy --strict <each changed production file>
```

Do not continue until clean.

## Step 2 — Budget allowance

Modify:

```text
budgets.py
```

Add focused R4 budget tests.

Run:

```powershell
python -m pytest tests/unit/execution/test_budgets.py tests/unit/execution/test_r4_token_and_metrics.py -k "allowance or budget" -q
```

## Step 3 — Regeneration executor

Modify:

```text
regeneration.py
```

Run exact three-file and positive-ceiling tests before editing Runner.

## Step 4 — Repository Agent

Modify:

```text
iterative_agent.py
```

Run Agent limit and incremental-token tests.

## Step 5 — Backend accounting modes

Modify the four backend files.

Compile and run backend tests.

## Step 6 — Runner accumulator and repair split

Modify:

```text
runner.py
```

First implement `_WorkflowMetricAccumulator`.

Then update:

```text
initial Monolithic/Selective;
repair Monolithic/Selective;
Agent initial;
Agent revision;
failed and timeout records.
```

After each path, run its smallest public-path test.

## Step 7 — Persistence and reporting

Modify:

```text
persistence.py
reporting.py
seven_arm_benchmark.py
```

Run actual JSONL and exporter tests.

## Step 8 — Full R4 integration

Run the complete new integration file.

## Step 9 — Adjacent R3D and old token tests

Run:

```text
R3D focused
SU0010A
SU0011
scientific_smoke_v1_fixes
```

Update only obsolete token semantics.

## Step 10 — Full suite

Run all tests.

## Step 11 — RF-3 bounded refactor

Perform the exact review in Section 26.

## Step 12 — rerun all gates

Only then stage the code commit.

---

# 24. Compile and quality gates

After every Python file:

```powershell
python -m py_compile <file>
ruff check <file>
```

For production files:

```powershell
mypy --strict <file>
```

Final focused gates:

```powershell
python -m pytest tests/unit/execution/test_r4_token_and_metrics.py -q

python -m pytest tests/integration/test_r4_metric_contract.py -q

python -m pytest `
  tests/unit/execution/test_budgets.py `
  tests/unit/execution/test_pipeline.py `
  tests/unit/test_models.py `
  tests/unit/test_checkpoint.py `
  tests/unit/statistics/test_reporting.py `
  tests/unit/test_config_models.py `
  tests/unit/llm/test_llm_kaggle_qwen_backend.py `
  -q

python -m pytest `
  tests/unit/execution/test_r3d_wiring.py `
  tests/integration/test_su0010a_regeneration.py `
  tests/integration/test_su0011_iterative_agent.py `
  tests/integration/test_scientific_smoke_v1_fixes.py `
  -q

python -m pytest -q
```

Static gates:

```powershell
ruff check `
  src/benchmark/core/models.py `
  src/benchmark/execution/budgets.py `
  src/benchmark/execution/regeneration.py `
  src/benchmark/strategies/iterative_agent.py `
  src/benchmark/execution/runner.py `
  src/benchmark/execution/pipeline.py `
  src/benchmark/checkpoint/persistence.py `
  src/benchmark/statistics/reporting.py `
  src/benchmark/llm/kaggle_qwen_backend.py `
  src/benchmark/llm/mock_backend.py `
  src/benchmark/llm/dry_run_backend.py `
  src/benchmark/llm/openrouter_backend.py `
  src/benchmark/config/models.py `
  seven_arm_benchmark.py `
  tests/unit/execution/test_r4_token_and_metrics.py `
  tests/integration/test_r4_metric_contract.py

mypy --strict `
  src/benchmark/core/models.py `
  src/benchmark/execution/budgets.py `
  src/benchmark/execution/regeneration.py `
  src/benchmark/strategies/iterative_agent.py `
  src/benchmark/execution/runner.py `
  src/benchmark/execution/pipeline.py `
  src/benchmark/checkpoint/persistence.py `
  src/benchmark/statistics/reporting.py `
  src/benchmark/llm/kaggle_qwen_backend.py `
  src/benchmark/config/models.py

python -m compileall `
  src/benchmark `
  seven_arm_benchmark.py `
  tests/unit/execution/test_r4_token_and_metrics.py `
  tests/integration/test_r4_metric_contract.py

git diff --check
```

No required R4 test may skip.

---

# 25. Direct scripts before commit

Run four short scripts outside Pytest.

## Script A — unlimited calls

Print:

```text
backend max_tokens list
prompt/completion usage
executor totals
```

Required:

```text
[4096, 4096, 4096]
```

## Script B — total ceiling

Print each prompt count, remaining total, and resolved allowance.

Required exact values from Combined Case 2.

## Script C — repair arithmetic

Run a public repair flow using the sentinel values in Section 21.

Print every metric and each identity result.

Every identity prints `True`.

## Script D — persistence/reporting

Persist the resulting record, reload it, serialize it, and print equality for every R4 field.

No manually reconstructed expected record.

---

# 26. RF-3 refactor checkpoint

RF-3 occurs after R4 tests pass and before the code commit.

Maximum effort:

```text
15% of R4 implementation time
```

Required checks:

```text
1. No new V2 call uses ambiguous `max_tokens`.
2. No Runner code accesses BudgetManager private fields.
3. One allowance function owns per-call/total interaction.
4. One accumulator owns workflow arithmetic.
5. No initial/repair/Agent path manually reimplements total equations.
6. No repair call remains inside regeneration metrics.
7. No scientific aggregate duration is added alongside individual stage durations.
8. No tool duration is added twice.
9. No cumulative Agent total is added as though it were a delta.
10. No entry/persistence/report field is missing.
11. Legacy aliases resolve once and disappear from the canonical path.
12. No dead compatibility branch introduced by R4 remains.
```

Allowed refactor:

```text
remove duplicate arithmetic;
replace local metric variables with accumulator;
rename ambiguous private locals;
remove direct private BudgetManager access;
delete obsolete token-limit helpers introduced by old fixes.
```

Forbidden:

```text
change R3D validation behavior;
change strategy selection;
change evaluator or migration code;
create a generic metrics framework;
modify statistical analysis.
```

Rerun all R4, R3D, integration, full-suite, Ruff, mypy, and compile gates after RF-3.

---

# 27. Code commit discipline

Before staging:

```powershell
git diff --name-only
git diff --stat
git diff --check
```

The output may contain only authorized production and test files.

Stage explicit paths only.

Do not use:

```text
git add .
git add -A
git commit -a
```

Commit exactly:

```text
fix(metrics): separate per-call limits and workflow totals
```

After commit, print:

```powershell
git show --name-status --stat --oneline HEAD
```

The three documentation files that were untracked at the start must remain untracked until the documentation step.

---

# 28. Documentation step

After the code commit and all gates, update:

```text
docs/PROJECT_HANDOFF.md
docs/V2_R3B_TO_KAGGLE_NO_DISCRETION_EXECUTION_SPEC.md
reports/latest_phase_report.md
selective_updates/CHANGE_INDEX.md
selective_updates/records/TECHNICAL-DEBT-AND-REFACTOR-SCHEDULE.md
```

Create:

```text
selective_updates/records/R4-TOKEN-AND-METRIC-CONTRACT.md
```

Track:

```text
docs/ONE_PASS_PHASE_EXECUTION_PROTOCOL.md
docs/R3D_INDEPENDENT_AUDIT_AND_FREEZE_REPORT.md
docs/phase_specs/R4_SINGLE_PASS_SPEC.md
```

State truthfully:

```text
R3D accepted and frozen at b8724cc;
R4 code checkpoint;
R4 self-gates passed;
R4 independent audit pending;
R5 and later phases blocked;
RF-3 completed;
open TD-0 and TD-1 count;
full-suite result;
focused and integration counts;
actual model footer.
```

Do not update README.

Commit exactly:

```text
docs(state): record R4 completion pending audit
```

---

# 29. Technical debt

Create or update these entries.

## TD-R4-001 — explicit token settings unused

Severity:

```text
TD-0 scientific comparability blocker
```

## TD-R4-002 — per-call and aggregate limits conflated

Severity:

```text
TD-0 execution comparability blocker
```

## TD-R4-003 — repair calls counted as regeneration

Severity:

```text
TD-0 metric validity blocker
```

## TD-R4-004 — stage durations cannot reconstruct total

Severity:

```text
TD-1 evidence blocker
```

## TD-R4-005 — legacy model-call and repair-attempt values are false

Severity:

```text
TD-1 persistence blocker
```

## TD-R4-006 — Qwen prompt-token fallback is approximate

Severity:

```text
TD-0 publication blocker
```

## TD-R4-007 — config hash omits token settings

Severity:

```text
TD-1 identity blocker
```

## TD-R4-008 — approximate accounting is unlabelled

Severity:

```text
TD-1 evidence blocker
```

## TD-RUNTIME-001 — deprecated event-loop API

Severity:

```text
TD-2
```

R4 may fix it only in files already modified when the fix is trivial and fully tested. Otherwise keep it scheduled for RF-4.

## TD-REPORT-001 — deprecated UTC API

Severity:

```text
TD-2
```

Do not expand R4 scope solely for this item.

At R4 self-gate completion:

```text
open R4 TD-0 = 0
open R4 TD-1 = 0
```

---

# 30. Detailed OpenCode report

OpenCode must print the complete report in the visible response and save it to:

```text
reports/latest_phase_report.md
```

Length:

```text
2,200–3,000 words
```

Use these exact headings:

```text
A. Requested and actual model
B. Git identity
C. R4 objective and frozen boundaries
D. Artifact before/after/dependency/test table
E. Configuration and alias resolution
F. Per-call and total-budget state machine
G. Workflow metric ownership
H. Arithmetic identities
I. Monolithic and Selective public evidence
J. Repository Agent public evidence
K. Repair metric evidence
L. Persistence and reporting round trip
M. Real Qwen versus approximate accounting
N. Failure matrix
O. Four direct adversarial scripts
P. Incremental failures and corrections
Q. RF-3 refactor evidence
R. Final gates
S. Commit-scope proof
T. Technical debt
U. Productivity metrics
V. Known limitations
W. Authorization
```

## 30.1 Artifact table

For every changed file:

| File | Before | After | Dependency impact | Exact proving tests |
|---|---|---|---|---|

Use actual Git diff, not the intended file list.

## 30.2 Test taxonomy

Separate counts for:

```text
unit/property;
public-path;
integration;
persistence/reporting;
adjacent regression;
full suite.
```

Do not claim every test is a public-path test.

## 30.3 Direct script table

Print actual inputs and outputs.

## 30.4 Arithmetic table

Print at least one complete numeric identity from Section 21.

## 30.5 Git proof

Print:

```text
git diff --name-status b8724cc..<code commit>
git show --stat <code commit>
git show --stat <documentation commit>
git status --short
```

Inside the persisted report write:

```text
Documentation commit: this commit
```

In the visible response print the actual documentation hash.

## 30.6 Final authorization

State:

```text
R3B frozen
R3C frozen
R3D frozen
R4 self-gates passed
R4 independent audit pending
R5 blocked
R6 blocked
Kaggle blocked
stable tag blocked
Pilot blocked
```

End exactly:

```text
R4_TOKEN_AND_METRIC_CONTRACT_AUDIT_REQUIRED
```

---

# 31. Productivity requirements

Report:

```text
planned production files
actual production files
unplanned production files
planned new test files
actual new test files
public-path tests
compile failures before commit
focused-test failures before commit
full-suite failures before commit
naming deviations
architecture deviations
model mismatch
empty commits
elapsed implementation time
```

Targets:

```text
unplanned production files = 0
naming deviations = 0
architecture deviations = 0
model mismatch = 0
empty commits = 0
post-audit correction cycles before freeze <= 1
```

Do not optimize for minimum elapsed time by omitting gates.

Improve speed by following the exact artifact and test plan without broad searching or architectural improvisation.

---

# 32. Stop conditions

Stop before further edits when:

```text
model mismatch;
branch or HEAD mismatch;
unexpected dirty file;
an unplanned production artifact is required;
the frozen names cannot be implemented;
an external dependency is required;
TokenUsage from real Qwen cannot be exact;
a required public-path test reveals a contradiction in this contract;
code staging contains documentation;
documentation staging is empty;
full suite fails.
```

Print:

```text
PHASE_BLOCKED

actual model:
branch:
HEAD:
dirty files:
first failing command:
contract conflict:
no changes made after blocker:
```

---

# 33. Acceptance definition

R4 can be accepted only when the independent audit can reproduce:

```text
three unlimited code-writing calls each receive 4096;
Agent unlimited calls do not shrink;
positive total ceiling gates calls correctly;
repair calls are separate from initial regeneration;
selection, regeneration, repair totals obey exact identities;
validation durations are cumulative and included once;
tool duration is not double-counted;
failed records preserve consumed metrics;
Qwen counting has no approximate fallback;
engineering records are labelled approximate;
config hash changes with canonical token settings;
JSONL and reporting equal in-memory values;
Windows full suite is green;
Linux focused and integration suites are green.
```

A large test count alone is not acceptance evidence.

---

# 34. Official project state after R4 self-gates

```text
R1 Repository Agent                  frozen
R2 Dependency-aware Selective        frozen
R3A Scenario metadata               frozen
R3B Migration runner                frozen
R3C Evaluator system                frozen
R3D Production scientific wiring    frozen
R4 Token and metric semantics       implementation complete, audit pending
R5 Nine local records               blocked
R6 Bundle and push                  blocked
Kaggle Smoke                        blocked
Stable scientific tag              blocked
Pilot                               blocked
```

---

# 35. Exact short execution prompt

Use the prompt below after this file is placed at the required project path.

```text
Use DeepSeek V4 Flash Free through OpenCode Zen in Build mode.

Print the active model, branch, HEAD, and git status before reading or editing.
Stop without changes on model, branch, HEAD, or dirty-file mismatch.

Branch:
experiment/three-arm-smoke-v2

Committed HEAD:
b8724cc

The only authorized starting untracked files are:
docs/ONE_PASS_PHASE_EXECUTION_PROTOCOL.md
docs/R3D_INDEPENDENT_AUDIT_AND_FREEZE_REPORT.md
docs/phase_specs/R4_SINGLE_PASS_SPEC.md

Read completely and execute literally:
docs/phase_specs/R4_SINGLE_PASS_SPEC.md

Implement R4 only.

Do not start R5.
Do not modify frozen R3B/R3C/R3D validation behavior.
Do not search broadly or invent alternative names, files, formulas, or tests.

Follow the exact read order, artifact map, dependency map, naming contract,
metric ownership, arithmetic identities, test matrix, incremental compile
order, four adversarial scripts, RF-3 checkpoint, gates, commit scopes, and
report format.

The code/test commit must be:
fix(metrics): separate per-call limits and workflow totals

The documentation commit must be:
docs(state): record R4 completion pending audit

Print and persist the complete 2,200–3,000-word report.
Require git status --short to print no output.

End exactly:
R4_TOKEN_AND_METRIC_CONTRACT_AUDIT_REQUIRED
```

---

**End of binding R4 single-pass specification.**

---

# R4 Completion Status (2026-07-31)

Executed and committed:

```text
code commit:  e87d4ad  fix(metrics): separate per-call limits and workflow totals
docs commit:  docs(state): record R4 completion pending audit
```

- R4 unit 66 passed; R4 integration 31 passed; R3D-adjacent 177 passed; evaluator integrity 50 passed, 1 pre-existing skip; full suite 1576 passed, 32 skipped, 0 failed.
- Direct scripts A/B/C1/C2/D acceptance met; Script D `2048 / 9000` at every metadata boundary.
- Ruff 0 new, mypy --strict 0 new (baseline vs HEAD worktree `b8724cc`); compileall 0; `git diff --check` clean.
- Remaining R4 TD-0 = 0, TD-1 = 0.
- Report: `reports/latest_phase_report.md` (2299 words).

Status: R4 implementation complete; independent audit required; R5 unauthorized until audit.

`R4_TOKEN_AND_METRIC_CONTRACT_AUDIT_REQUIRED`
