# V2 Remaining Work — Production-Path Completion and Kaggle Authorization Contract

**Document status:** Mandatory continuation contract after independent audit  
**Target branch:** `experiment/three-arm-smoke-v2`  
**Current audited HEAD:** `5057e7d` *(amended R2 closure)*  
**Implementation model:** DeepSeek V4 Flash Free through OpenCode Zen, Build mode  
**Audit model:** GPT-5.6 Thinking  
**Local proof model:** test-only deterministic `ScriptedLLMBackend`  
**Real Smoke model after local proof:** Qwen2.5-Coder-7B-Instruct on Kaggle  
**Pilot:** forbidden in this document  
**Tag:** forbidden until real Qwen Smoke is completed and independently audited  

---

## 1. Binding verdict

Scientific Smoke V2 is **not finished** and is **not authorized for Kaggle yet**.

The green project suite is useful engineering evidence, but it is not proof that the scientific workflow works. The current repository has completed substantial preparation:

- truthful controlled Todo scenarios;
- a five-file LLM-editable policy;
- a safe ArtifactUniverse resolver;
- a full-scope Monolithic strategy;
- a repository-derived Selective implementation;
- the beginning of a tool-based Repository Agent;
- more than one thousand passing tests in the user’s Windows environment.

However, the audited source still lacks the production validation and measurement boundary required for a truthful Smoke. The current Agent implementation also contains correctness defects, and the current Selective behavior is degenerate on the actual three Smoke requests.

The acceptance condition remains:

```text
3 scenarios × 3 arms × 1 repetition
= 9 non-dry scripted production-path records
```

Each record must perform actual selection, actual SharedRegenerationExecutor calls, real workspace edits, deterministic migration generation, baseline tests, isolated scenario evaluation, and truthful non-zero metrics. Only after this local proof passes, the branch is committed, bundled, pushed, and independently audited may the real Kaggle Smoke be authorized.

This document defines the remaining work exactly. Do not substitute a different design.

---

## 2. Phase completion status

| Phase | Status | HEAD |
|-------|--------|------|
| R1 — Bounded Repository Agent | COMPLETE | `b129d42` |
| R2 — Corrected Selective Scope | COMPLETE | `5057e7d` |
| R3A — Scenario execution metadata | COMPLETE | `3eaab60` |
| R3B–R6 | NOT STARTED | — |

Pre-closure baseline: 1166 passed, 10 skipped.
Actual final: 1205 passed, 10 skipped.
Verified Selective scopes match specification exactly (001=3 files, 002=2 files, 003=4 files).
Three evaluator asset paths: `tests/evaluator_assets/todo_smoke_001_checks.py`, `tests/evaluator_assets/todo_smoke_002_checks.py`, `tests/evaluator_assets/todo_smoke_003_checks.py`.
Post-generation command: `python manage.py makemigrations todo --noinput`.
R3B migration runner is the next task.
Kaggle: blocked. Pilot: blocked. Merge: blocked. Stable tag: blocked.
Evaluator scripts, migration runner, token correction, and nine production records do not yet exist.

---

## 3. Audited current state

### 3.1 Git state

```text
Branch:                    experiment/three-arm-smoke-v2
R1 code checkpoint:        b129d42 (feat(agent): complete bounded workspace exploration)
R2 code checkpoint:        5057e7d (fix(selection): correct R2 selective scope)
R3A code checkpoint:       3eaab60 (feat(scenarios): add V2 execution metadata)
Working tree:              clean
Full suite:                1205 passed, 10 skipped
Kaggle:                    blocked
Pilot:                     blocked
```

The document you are reading is the sole continuation contract. Use `git rev-parse HEAD` to discover the current documentation commit hash — do not embed it in this file.

### 3.2 What the passing tests prove

The full suite result is:

```text
1174 passed
10 skipped
0 failed
```

This proves that the current tests are internally compatible with the implementation. It does not prove:
- that scenario-specific evaluator checks run;
- that `4096` is a per-call completion limit rather than a total workflow cap;
- that nine non-dry production records exist.

Tests must be extended to prove these behaviors directly.

---

## 3. Critical audit findings

### 3.1 Selective currently degenerates to full scope

The current `select_dependency_scope()` was executed against the real Todo profile, real dependency graph, five-file editable universe, and all three real V2 scenario requests.

The result was:

| Scenario | Selected paths |
|---|---|
| `todo-smoke-001` | all five editable paths |
| `todo-smoke-002` | all five editable paths |
| `todo-smoke-003` | all five editable paths |

The five paths are:

```text
todo/models.py
todo/serializers.py
todo/views.py
todo/permissions.py
todo/urls.py
```

This means the current Selective arm has the same regeneration scope as Monolithic for every Smoke change. It cannot demonstrate context or generation savings.

The cause is not Ground Truth leakage. The cause is an over-broad deterministic matcher:

- generic words such as `api`, `field`, `change`, `modification`, `endpoint`,
  `todo`, and `py` create seeds;
- broad trigger phrases such as “API additions or modifications” match several
  artifacts;
- negative public statements such as “todo/urls.py must not be modified” still
  contribute positive words that seed `todo/urls.py`;
- dependency traversal then adds more files.

The correction must remain Ground-Truth-free, but it must distinguish positive impact statements from explicit public exclusions.

### 3.2 Agent explores the wrong root

`IterativeRepositoryAgentStrategy.analyze_impact()` creates `RepositoryTools`
using `repository.path`.

For regeneration runs, `BenchmarkRunner._build_repository_snapshot()` currently
sets that path to the immutable active snapshot. The specification requires
the Agent to inspect the active isolated workspace.

The initial workspace and snapshot may be byte-identical, but the distinction
becomes critical after generation. The Agent must never mutate the snapshot,
and revision rounds must inspect the modified workspace.

### 3.3 Agent revision uses a fabricated `/tmp` root

`revise_plan()` currently creates:

```python
RepositoryTools(workspace_root="/tmp")
```

This is invalid on Windows, unrelated to the experiment workspace, and prevents
the revision loop from examining generated code. This must be removed entirely.

### 3.4 Eight-call cap is not global

Both `analyze_impact()` and `revise_plan()` create a new local
`call_count = 0` and allow up to `MAX_AGENT_CALLS`.

Therefore one run can make eight initial calls and another eight calls during
each revision. This violates the bounded Agent contract.

The cap must be eight total Agent-selection LLM calls for the complete run,
including invalid responses and revision rounds.

### 3.5 Legacy response parsing bypasses repository exploration

The current parser accepts the old structure:

```json
{"decisions": [...], "requires_iteration": ...}
```

and converts it directly into a final selection. The V2 Repository Agent
protocol requires one of four explicit actions:

- `list_files`;
- `read_file`;
- `search_text`;
- `final`.

The confirmatory V2 path must not silently accept the legacy single-shot
decision structure. Update old tests to the tool protocol. Do not preserve a
production bypass merely to keep old fixtures unchanged.

### 3.6 Tool inspection budget is not enforced by search

`RepositoryTools.read_file()` tracks inspected files, but `search_text()` scans
files without adding them to the inspected set and without stopping at the
30-file limit.

A single search can therefore inspect the complete repository while reporting
zero inspected files. This invalidates the Agent cost boundary.

`search_text()` must reserve every file before reading it, stop at the distinct
file cap, and expose the correct count.

### 3.7 Symlink safety is incomplete during recursive search

Direct `read_file()` resolves the requested path and generally blocks escape,
but recursive listing and searching do not consistently reject symlinked files
whose targets are outside the workspace.

Every file read during search must resolve beneath the workspace root. Escaping
symlinks must be skipped or reported as a tool error. No outside content may
enter the Agent prompt.

### 3.8 Agent metrics are not truthfully integrated

The strategy stores:

- model calls;
- tool calls;
- tool duration;
- tokens;
- inspected files.

But the current Runner does not persist all of these fields in `RunRecord`.

Additionally, `prediction.token_usage` is cumulative. If revision occurs, the
Runner sums cumulative totals again, causing double counting. The Runner also
increments `selection_calls` once per strategy invocation rather than using
the actual number of backend calls made inside the Agent loop.

Metrics must use per-invocation deltas and must persist complete run totals.

### 3.9 Evaluator and migration phases are absent

The current normal regeneration flow runs one functional validation command.
It does not yet:

- generate one migration;
- protect existing migration hashes;
- run scenario evaluator assets;
- record separate baseline, evaluator, and migration results;
- require all three stages to pass.

Therefore baseline tests could pass even when the requested feature was never
implemented.

### 3.10 Token semantics remain incorrect

`PipelineConfig` and `RunnerConfig` contain new names, but execution still
constructs `BudgetManager(max_tokens=config.max_tokens)`, and the executor is
called with `self._budget.remaining_tokens`.

`SharedRegenerationExecutor` subtracts previously consumed prompt and
completion tokens from that value and reduces later calls. This still treats
the supplied number as an aggregate workflow allowance.

The scientific requirement is:

```text
max_completion_tokens_per_call = 4096
```

Each model generation call receives this completion limit. An optional
independent total safety ceiling may exist, but it must be a separately named
larger value or zero for unlimited.

### 3.11 No nine-record production proof exists

The required test-only scripted backend, isolated evaluator execution, and
nine persisted non-dry records have not been implemented. A dry run is not a
substitute.

---

## 4. Execution rules

OpenCode must execute the following phases in order.

At the end of every phase:

1. run the exact focused tests;
2. run `git diff --name-only`;
3. verify that only authorized files changed;
4. run Ruff, mypy, compileall, and `git diff --check` where listed;
5. create the specified local checkpoint commit;
6. continue automatically to the next phase unless a genuine blocker exists.

Do not ask the user to type “continue” between phases.

Do not edit `kaggle_upload/` manually. Regenerate it once in the final phase.

Do not change Pilot repositories, add new arms, add embeddings, create a vector
database, create another CLI, or create another executor.

---

## 5. Phase R1 — stabilize and commit the existing Agent work

### Authorized files

```text
src/benchmark/strategies/repository_tools.py
src/benchmark/strategies/iterative_agent.py
src/benchmark/execution/runner.py
src/benchmark/core/models.py
tests/integration/test_su0011_iterative_agent.py
tests/integration/test_scientific_smoke_v1_fixes.py
tests/contract/test_three_arm_core.py
tests/unit/strategies/test_repository_tools.py
```

Create `tests/unit/strategies/test_repository_tools.py` if it does not exist.

Restore premature documentation changes (already done — b129d42 was checkpointed with clean state):

### 5.1 Bind the Agent to the actual workspace

Add this exact public method to `IterativeRepositoryAgentStrategy`:

```python
def begin_run(self, workspace_root: str | Path) -> None:
    """Bind one benchmark run to its isolated workspace and reset run metrics."""
```

It must:

- resolve `workspace_root`;
- require an existing directory;
- reset model calls, tool calls, tool duration, token totals, inspected files,
  transcript, last-requires-iteration, and remaining Agent calls;
- set `self._remaining_agent_calls = 8`;
- create one `RepositoryTools` instance bound to that workspace.

In `BenchmarkRunner._run_iterative_flow()`, immediately after validating that a
backend exists and before the first selection call:

```python
begin_run = getattr(self._strategy, "begin_run", None)
if not callable(begin_run):
    return a harness-defect RunRecord
begin_run(self._isolation.workspace.root)
```

Do not use `repository.path` to create tools. Do not create tools from `/tmp`.
`analyze_impact()` and `revise_plan()` must reuse the tools created by
`begin_run()`.

### 5.2 Enforce one global eight-call limit

Add a private method:

```python
def _generate_agent_response(self, prompt: str, max_completion_tokens: int) -> LLMResponse:
```

Before calling the backend:

- fail if `self._remaining_agent_calls <= 0`;
- decrement the remaining count exactly once for every attempted backend call,
  including invalid JSON and unknown actions;
- increment model-call metrics after a response is received;
- preserve backend exceptions for Runner handling.

Neither `analyze_impact()` nor `revise_plan()` may create a local independent
eight-call counter.

### 5.3 Use the exact JSON protocol

Remove production support for top-level `decisions`.

`_parse_action_response()` must accept only a JSON object containing `action`.

Invalid JSON must:

- consume a call;
- append a compact structured error to the next prompt;
- continue while calls remain.

Unknown actions must do the same.

For `final`:

- `selected_paths` must be a list;
- it must be non-empty;
- every item must be a string;
- values must be unique;
- every path must belong to ArtifactUniverse;
- invalid final output consumes a call and allows correction while calls remain;
- do not silently discard invalid paths and accept the remaining subset.

### 5.4 Make token usage incremental

For each `analyze_impact()` or `revise_plan()` invocation, capture counters at
entry and return only the token delta generated during that invocation in
`ImpactPrediction.token_usage`.

Keep cumulative properties for the final report, but do not return cumulative
tokens repeatedly.

Add properties:

```python
@property
def remaining_agent_calls(self) -> int: ...

@property
def compact_tool_transcript(self) -> tuple[str, ...]: ...
```

The transcript must include tool name, relative argument, success/failure, and
duration, but never full file contents.

### 5.5 Correct RepositoryTools

Add a helper:

```python
def _reserve_inspected_file(self, resolved: Path) -> str | None:
```

It must:

- resolve the path;
- verify it remains below `_root`;
- reject escaping symlinks;
- calculate POSIX relative path;
- add a new path to `_inspected`;
- return an error string when the 30-file cap would be exceeded.

`read_file()` and `search_text()` must use it.

For `search_text()`:

- reject an empty query;
- before reading each candidate file, reserve it;
- stop and return an error if the cap is reached;
- do not read symlinks escaping root;
- retain maximum 50 result lines;
- track files even when no query match is found.

`list_files()` must not include an escaping symlink target as a readable file.

### 5.6 Persist Agent metrics

Extend `RunRecord` with:

```python
selection_tool_calls: int = 0
selection_tool_duration_seconds: float = 0.0
selection_inspected_file_count: int = 0
selection_tool_transcript: tuple[str, ...] = ()
```

Validate non-negative numeric fields in `__post_init__`.

In `_run_iterative_flow()`, calculate model-call deltas from the strategy’s
actual `model_call_count` before and after each strategy invocation.

Persist tool totals from the strategy. Do not equate one strategy invocation
with one model call.

### R1 tests

Tests must prove:

- initial exploration reads the isolated workspace, not snapshot;
- revision reads the same modified workspace;
- `/tmp` is never used;
- initial plus revision model calls never exceed eight;
- invalid JSON and invalid final paths consume calls;
- legacy `decisions` output is rejected;
- search inspections count toward the 30-file limit;
- escaping symlinks are unreadable;
- RunRecord model calls equal actual backend calls;
- RunRecord tool calls and inspected count are non-zero after exploration;
- revision token totals are not double-counted.

Run:

```powershell
python -m pytest `
  tests/unit/strategies/test_repository_tools.py `
  tests/integration/test_su0011_iterative_agent.py `
  tests/integration/test_scientific_smoke_v1_fixes.py `
  tests/contract/test_three_arm_core.py `
  -q
ruff check src/benchmark/strategies src/benchmark/execution/runner.py src/benchmark/core/models.py tests
mypy --strict src/benchmark/strategies src/benchmark/execution/runner.py src/benchmark/core/models.py
python -m compileall src/benchmark/strategies src/benchmark/execution/runner.py
git diff --check
```

Commit:

```powershell
git add src/benchmark/strategies src/benchmark/execution/runner.py src/benchmark/core/models.py tests
git commit -m "feat(agent): complete bounded workspace exploration"
```

---

## 6. Phase R2 — correct Selective degeneracy without Ground Truth

### Authorized files

```text
src/benchmark/selection/dependency_scope.py
src/benchmark/strategies/selective.py
benchmark_data/repository_profiles/todo.yaml
tests/unit/selection/test_dependency_scope.py
tests/contract/test_three_arm_core.py
```

Do not read or import `expected_affected_artifacts` in production selection.

### 6.1 Add low-information filtering

Define one generic repository-independent set:

```python
LOW_INFORMATION_SOFTWARE_TERMS = frozenset({
    "add", "addition", "change", "changes", "code", "current", "existing",
    "file", "files", "implementation", "modify", "modified", "modification",
    "new", "required", "requirement", "support", "todo", "py",
})
```

This set must not contain scenario-specific domain terms such as `priority`,
`deleted`, `owner`, `project`, or `task`.

### 6.2 Build positive and negative public text

Use only:

- `RequirementChange.before`;
- `RequirementChange.after`;
- public acceptance criteria.

Create:

```python
@dataclass(frozen=True)
class RequirementSignals:
    positive_terms: frozenset[str]
    negative_descriptor_paths: frozenset[str]
```

A descriptor path becomes a public negative path only when its literal path,
path stem, category, or provided symbol appears in one of these forms:

```text
no changes to X
X must not be modified
X is not required
X changes are not required
without changing X
```

The parser must be generic and deterministic. It must not know scenario IDs or
Ground Truth.

Negative phrases must not contribute positive seed terms.

### 6.3 Replace the seed rules

For each descriptor, calculate:

- normalized path stem;
- normalized category;
- normalized provided-symbol phrases;
- normalized trigger phrases;
- normalized descriptive content terms after stop-word and low-information
  filtering.

A descriptor is a seed only when one of these conditions holds:

1. a complete provided-symbol phrase occurs in the positive public text;
2. the path stem or category occurs in positive terms and at least one
   additional meaningful descriptor term matches;
3. a trigger phrase has at least two distinct meaningful words, at least two
   words match, and matched words represent at least two-thirds of the trigger’s
   meaningful words.

The generic phrase `API additions or modifications` must not seed an artifact
merely because `api` and `modification` occur. Low-information words are
removed before ratio calculation.

### 6.4 Apply graph traversal and explicit public exclusions

The graph edge meaning remains:

```text
A -> B means A depends on B
```

Include each seed and its direct outgoing dependencies.

After traversal:

- intersect with ArtifactUniverse;
- remove paths explicitly excluded by public negative phrases;
- return sorted unique paths;
- fail closed if the final set is empty.

Do not add reverse traversal. Do not add scenario-specific branches.

### 6.5 Profile trigger cleanup

Keep repository-level triggers, but replace overly generic URL trigger:

```text
API additions or modifications (new endpoints)
```

with specific repository-level triggers:

```yaml
- router registration changes
- URL pattern changes
- manually registered endpoint paths
```

This is repository truth: DRF `@action` methods do not require `todo/urls.py`
changes.

Other descriptors may retain truthful triggers, but remove generic wording that
causes every artifact to seed on every API change.

### R2 acceptance tests

Tests must use the real three public scenarios and real profile without reading
Ground Truth.

Prove:

- all selections are deterministic and non-empty;
- all selected paths belong to the five-file universe;
- no scenario selects all five paths;
- `todo/urls.py` is not selected for any current Smoke request because none
  requires router registration or URL-pattern modification;
- scenario 002 does not select serializers because its public requirement says
  serializer changes are not required;
- mutating Ground Truth leaves every selection unchanged;
- removing all meaningful public terms fails closed;
- no `todo-smoke-` string appears in production selection code.

These tests assert public-contract behavior, not equality to
`expected_affected_artifacts`.

Run focused tests, full suite, Ruff, mypy, compileall, and diff check.

Commit:

```powershell
git add src/benchmark/selection src/benchmark/strategies/selective.py benchmark_data/repository_profiles/todo.yaml tests
git commit -m "fix(selection): prevent full-scope selective degeneration"
```

---

## 7. Phase R3 — scenario metadata, migration generation, and evaluator isolation

### Authorized production files

```text
src/benchmark/core/models.py
src/benchmark/scenarios/models.py
src/benchmark/scenarios/loader.py
src/benchmark/execution/post_generation.py
src/benchmark/execution/scenario_evaluator.py
src/benchmark/execution/runner.py
src/benchmark/execution/pipeline.py
seven_arm_benchmark.py
benchmark_data/scenarios/todo-smoke-001.yaml
benchmark_data/scenarios/todo-smoke-002.yaml
benchmark_data/scenarios/todo-smoke-003.yaml
tests/evaluator_assets/todo_smoke_001_checks.py
tests/evaluator_assets/todo_smoke_002_checks.py
tests/evaluator_assets/todo_smoke_003_checks.py
```

### 7.1 Scenario fields

Add to both loader model and core `Scenario`:

```python
evaluator_asset: str = ""
post_generation_command: tuple[str, ...] = ()
require_new_migration: bool = False
```

Load them from YAML. These are evaluator execution metadata and must not enter
LLM prompts.

Each Smoke YAML must contain:

```yaml
evaluator_asset: tests/evaluator_assets/todo_smoke_00N_checks.py
post_generation_command:
  - python
  - manage.py
  - makemigrations
  - todo
  - --noinput
require_new_migration: true
```

### 7.2 Post-generation runner

Create `src/benchmark/execution/post_generation.py`.

Define:

```python
@dataclass(frozen=True)
class PostGenerationResult:
    passed: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    created_paths: tuple[str, ...]
    existing_migrations_unchanged: bool
```

Before execution:

- hash every existing `todo/migrations/*.py`;
- exclude `__init__.py` from migration counts;
- record existing file paths.

Run the command in the isolated workspace.

After execution:

- all old migration files must have identical hashes;
- exactly one new numbered migration must exist when required;
- created paths must be repository-relative POSIX paths;
- any violation fails the run.

### 7.3 Scenario evaluator runner

Create `src/benchmark/execution/scenario_evaluator.py`.

It must:

- accept the canonical project root, evaluator relative path, generated
  workspace, Python executable, and timeout;
- require the asset to resolve below canonical `tests/evaluator_assets`;
- copy only the evaluator script to a temporary directory outside the workspace;
- invoke a fresh subprocess;
- put generated workspace first in `PYTHONPATH`;
- never import workspace Django modules into the benchmark parent process;
- parse exactly one JSON object with `passed`, `checks`, and `error`;
- return a typed result;
- fail closed on timeout, malformed JSON, non-zero exit, or missing script.

### 7.4 Evaluator scripts

Create exactly three scripts.

Each must:

- accept the workspace path as a command-line argument;
- set `DJANGO_SETTINGS_MODULE=config.settings`;
- prepend the workspace to `sys.path`;
- use Django’s test database facilities;
- run migrations;
- execute only evaluator-owned checks;
- output one compact JSON object;
- tear down the database;
- exit non-zero when checks fail.

Smoke 001 verifies:

- Priority enum and field;
- allowed values and default;
- serializer read/write behavior;
- priority query filtering;
- invalid priority rejection;
- baseline fields still work.

Smoke 002 verifies:

- soft delete retains the row;
- normal list and detail exclude deleted Task;
- deleted action lists deleted Tasks;
- restore restores it;
- data remains unchanged;
- Project and Tag behavior remains.

Smoke 003 verifies:

- Project creator becomes owner;
- owner is read-only;
- owner can update/delete Project;
- non-owner gets 403;
- Task create/update/delete follows `Task.project.owner`;
- reads remain authenticated and unrestricted as specified;
- Tag permission behavior remains unchanged.

### 7.5 Validation order

For every non-dry regeneration run:

1. apply generated source through `SharedRegenerationExecutor`;
2. run post-generation migration command;
3. run baseline Todo tests;
4. run scenario evaluator;
5. verify migration consistency;
6. succeed only if all pass and at least one model call and generated source
   artifact exist.

Add separate `RunRecord` fields:

```python
migration_generation_passed: bool | None
migration_duration_seconds: float
generated_migration_paths: tuple[str, ...]
baseline_validation_passed: bool | None
baseline_validation_duration_seconds: float
scenario_evaluator_passed: bool | None
scenario_evaluator_duration_seconds: float
scenario_evaluator_checks: tuple[str, ...]
```

Do not overload `functional_validation_passed`; retain it only as a deprecated
compatibility mirror of baseline validation if old tests require it.

Run focused tests and full quality gates.

Commit:

```powershell
git add src/benchmark/core src/benchmark/scenarios src/benchmark/execution seven_arm_benchmark.py benchmark_data/scenarios tests
git commit -m "feat(validation): add migrations and isolated evaluators"
```

---

## 8. Phase R4 — correct per-call token limits and stage accounting

### Authorized files

```text
src/benchmark/execution/budgets.py
src/benchmark/execution/pipeline.py
src/benchmark/execution/runner.py
src/benchmark/execution/regeneration.py
src/benchmark/execution/repair.py
src/benchmark/core/models.py
seven_arm_benchmark.py
related token, runner, backend, and persistence tests
```

### 8.1 Budget configuration

Construct `BudgetManager` with:

```python
max_tokens=config.max_total_workflow_tokens
```

Do not use legacy `config.max_tokens` for V2.

Keep old fields only as compatibility aliases for non-V2 tests.

### 8.2 Executor API

Change executor arguments to make semantics explicit:

```python
def execute(
    ...,
    max_completion_tokens_per_call: int = 4096,
    remaining_total_workflow_tokens: int = 0,
) -> RegenerationExecutionResult:
```

Every backend call receives `max_completion_tokens_per_call`.

When the optional total ceiling is zero, do not reduce later call limits.

When a positive total ceiling exists, it is an independent safety check. Do not
subtract prompt estimates from the API’s completion limit as though input and
output shared one `max_tokens` parameter.

### 8.3 Agent calls

The Agent’s backend calls receive the same
`max_completion_tokens_per_call=4096`.

The eight-call bound is separate from token limits.

### 8.4 Metrics

Persist and assert:

```text
selection_total = selection_prompt + selection_completion
regeneration_total = regeneration_prompt + regeneration_completion
repair_total = repair_prompt + repair_completion
total_workflow_tokens = selection_total + regeneration_total + repair_total
total_workflow_calls = selection_calls + regeneration_calls + repair_calls
```

Total duration must include:

- selection and tools;
- regeneration;
- repair;
- migration;
- baseline validation;
- scenario evaluator.

For a real Qwen backend, token counts must come from its tokenizer. The
approximate character fallback is allowed only for mock/scripted tests and must
be labelled approximate in records.

Commit:

```powershell
git add src/benchmark/execution src/benchmark/core/models.py seven_arm_benchmark.py tests
git commit -m "fix(metrics): separate per-call limits and workflow totals"
```

---

## 9. Phase R5 — prove nine non-dry scripted production records

Create exactly:

```text
tests/support/scripted_llm_backend.py
tests/support/scripted_smoke_v2.py
tests/integration/test_scientific_smoke_v2_production_path.py
```

The scripted backend is test support only. Production strategies must not
import it, and the real provider registry must not expose it.

It may identify:

- the public scenario requirement;
- requested artifact path;
- Agent tool stage.

It may return deterministic source content for the controlled Todo scenarios.
It must not influence Selective or Agent scope logic.

The support runner must use:

```text
dry_run=False
enable_regeneration=True
real staged immutable baseline snapshot
fresh workspace for every record
real Runner
real Monolithic/Selective/Agent strategies
real SharedRegenerationExecutor
real migration generation
real baseline tests
real isolated evaluator
real JSONL persistence and reload
```

Run nine records.

For every successful record assert:

- `status == succeeded`;
- model calls are non-zero;
- regeneration calls are non-zero;
- token totals are non-zero;
- generated source count is non-zero;
- migration passed;
- exactly one migration was created;
- baseline validation passed;
- scenario evaluator passed;
- workspace differs from snapshot;
- snapshot hash is unchanged;
- baseline tests, evaluator assets, config, and old migrations were not modified;
- persisted and reloaded identity and metrics match.

Additional scientific assertions:

- Monolithic selects five files;
- Selective selects a strict subset of five for every current Smoke scenario;
- Agent makes no more than eight selection calls;
- Agent tool metrics are non-zero;
- no arm sees Ground Truth or evaluator text;
- all code edits pass through the same executor class.

The test must fail if `dry_run=True` or if a successful record has zero calls,
tokens, or generated source.

Commit:

```powershell
git add tests/support tests/integration/test_scientific_smoke_v2_production_path.py
git commit -m "test(smoke): prove nine scripted production records"
```

---

## 10. Phase R6 — final cleanup, documentation, bundle, and push

Only after R5 passes:

1. update `README.md`;
2. update `docs/MASTER_IMPLEMENTATION_PLAN.md`;
3. update `docs/PROJECT_HANDOFF.md`;
4. update the amendment record and change index;
5. record exact current evidence, not real-model claims;
6. regenerate `kaggle_upload/` using the build script;
7. run the complete final gate.

The Handoff must include:

- branch and final HEAD;
- clean status;
- three arms and three changes;
- exact editable universe;
- local scripted proof result;
- exact command for real Kaggle Smoke;
- Kaggle status: authorized but not launched;
- Pilot status: blocked;
- tag status: blocked.

Final commands:

```powershell
python -m pytest -q
Push-Location benchmark_data/repositories/todo
python -m pytest -q
python manage.py check
Pop-Location
ruff check src tests seven_arm_benchmark.py scripts
mypy --strict src/benchmark
python -m compileall src/benchmark seven_arm_benchmark.py
python scripts/build_upload_bundle.py
git diff --check
python -m pytest tests/integration/test_scientific_smoke_v2_production_path.py -q
git status --short
```

Create the final documentation/bundle commit, then push:

```powershell
git push -u origin experiment/three-arm-smoke-v2
```

Do not launch Kaggle automatically. Do not merge. Do not create a tag.

---

## 11. Kaggle authorization rule

Real Kaggle Smoke becomes authorized only after:

- all R1–R6 commits exist;
- the branch is pushed;
- working tree is clean;
- local and remote HEAD are equal;
- nine non-dry scripted records pass;
- bundle parity passes;
- independent audit approves.

The real Kaggle matrix is:

```text
todo-smoke-001 × monolithic
todo-smoke-001 × selective
todo-smoke-001 × iterative_repository_agent
todo-smoke-002 × monolithic
todo-smoke-002 × selective
todo-smoke-002 × iterative_repository_agent
todo-smoke-003 × monolithic
todo-smoke-003 × selective
todo-smoke-003 × iterative_repository_agent
```

Model:

```text
Qwen2.5-Coder-7B-Instruct
temperature = 0.0
max_completion_tokens_per_call = 4096
```

Each change starts from the same pinned baseline.

---

## 12. Stable tag and Pilot rule

Do not create a stable V2 tag after local scripted proof.

Create an annotated stable tag only after:

- all nine real Qwen records finish;
- failures are preserved as data;
- token and timing totals are internally consistent;
- evaluator results exist;
- Ground Truth isolation is audited;
- deployed bundle equals pushed source;
- no post-result algorithm tuning occurs;
- independent audit approves.

Suggested later tag:

```text
v2.0.0-scientific-smoke
```

Pilot remains blocked until that tag exists.

Pilot minimum:

- at least seven changes;
- at least three repositories;
- every repository at least 5,000 LOC;
- exact pinned commits;
- permissive licenses;
- reproducible passing baseline tests.

---

## 13. Required final OpenCode report

The final response after all phases must contain:

1. commits created;
2. final HEAD;
3. clean working tree;
4. local/remote equality;
5. exact Selective paths for each scenario;
6. exact Agent selected paths, call counts, tool counts, and inspected counts;
7. proof Agent used workspace rather than snapshot;
8. proof total Agent selection calls never exceeded eight;
9. proof all code edits used SharedRegenerationExecutor;
10. migration path for all nine records;
11. baseline and evaluator results for all nine records;
12. a nine-row table of calls, tokens, selected files, generated files, and
    validation states;
13. snapshot integrity;
14. full tests;
15. Todo tests and Django check;
16. Ruff, mypy, compileall, bundle, and diff check;
17. documentation updated;
18. Kaggle authorization;
19. Pilot blocked;
20. tag blocked.

End exactly with:

```text
V2_LOCAL_PRODUCTION_PROOF_PASSED_KAGGLE_AUDIT_REQUIRED
```
