# V2 Three-Arm Production Execution Specification

**Document status:** Authoritative implementation contract  
**Target branch:** `experiment/three-arm-smoke-v2`  
**Committed base HEAD:** `0a1c603`  
**Implementation model:** DeepSeek V4 Flash Free through OpenCode Zen, Build mode  
**Real experimental model after local proof:** Qwen2.5-Coder-7B-Instruct on Kaggle  
**Scope:** Complete Scientific Smoke V2 only. Pilot work is explicitly excluded.

---

## 1. Authority and execution rule

This document is the single authoritative contract for completing V2. OpenCode must execute the phases in the exact order written here. It must not redesign the project, invent parallel packages, substitute different algorithms, create additional arms, change the research question, or interpret passing unit tests as proof that the experiment works.

The implementation is complete only when the exact non-dry production path runs nine truthful local scripted records:

- 3 independent Todo changes;
- 3 arms;
- 1 repetition;
- real isolated workspaces;
- real scope selection;
- real SharedRegenerationExecutor calls;
- actual file changes;
- deterministic migration generation;
- baseline tests;
- scenario evaluator checks;
- non-zero token and call metrics;
- persisted records inspected after execution.

A normal `--dry-run` remains a planning and checkpoint wiring check. It is never evidence that a strategy, code generation, validation, evaluator, or metric path worked.

OpenCode must work phase by phase inside one continuous task. At the end of each phase it must run the listed gate. If a gate fails, it must repair only that phase before continuing. It must not skip a failed gate, classify a new failure as pre-existing without reproducing it at clean HEAD, or continue with partially correct code.

---

## 2. Scientific question and non-negotiable design

The benchmark asks:

> Given the same baseline repository, the same natural-language change request, the same LLM, and the same generation settings, can dependency-aware selective regeneration achieve comparable correctness and code quality with fewer tokens, fewer model calls, less time, and fewer unnecessary file modifications than broad full-scope regeneration and a repository-exploration agent?

The LLM writes every actual source-code change. The harness does not hardcode the implementation answer. The harness may deterministically select context, restrict editable files, run tools, apply generated source, generate migrations through Django, validate results, and calculate post-hoc metrics.

All three arms receive:

1. the same pinned Todo baseline;
2. the same public natural-language scenario request;
3. the same public acceptance criteria;
4. the same model identity;
5. temperature `0.0`;
6. the same `max_completion_tokens_per_call` value;
7. the same SharedRegenerationExecutor for writing source files;
8. the same migration command;
9. the same baseline validation;
10. the same scenario evaluator;
11. a fresh isolated workspace copied from the same immutable snapshot.

The arms differ only in scope acquisition:

- **Monolithic / full_scope_reference:** every allowed production file is selected.
- **Selective / dependency_aware_selective:** a deterministic repository-level dependency policy selects a smaller scope from public profile metadata and the natural-language requirement.
- **Iterative Repository Agent / repository_agent:** the LLM explores the active workspace using only bounded `list_files`, `read_file`, and `search_text` tools, then returns editable paths.

Ground Truth is post-hoc evaluator data only. It must never influence ArtifactUniverse construction, selective seeds, graph traversal, agent-visible text, generation prompts, repair prompts, validation inputs, or success decisions.

---

## 3. Frozen experiment size

### Scientific Smoke V2

- Repository: controlled Django Todo.
- Changes: exactly 3 independent changes.
- Arms: exactly 3.
- Repetitions initially: 1.
- Total real Smoke records: 9.
- Every change starts from the same clean pinned baseline; changes are not cumulative.

The scenarios are:

1. `todo-smoke-001`: Task priority and priority filtering.
2. `todo-smoke-002`: Task soft deletion, deleted list, and restore action.
3. `todo-smoke-003`: Project ownership and Project-owner Task authorization.

### Pilot policy, documentation only

Pilot remains unauthorized until the nine real Qwen Smoke records are completed and independently audited. The Pilot admission policy is:

- at least 7 changes;
- at least 3 real repositories;
- every Pilot repository has at least 5,000 LOC;
- permissive license;
- exact pinned commit;
- reproducible passing baseline test suite.

Do not select, clone, integrate, or test Pilot repositories while implementing this specification.

---

## 4. Canonical project structure

The following locations are canonical:

```text
src/benchmark/          production benchmark code
benchmark_data/         repositories, profiles, manifests, and scenarios
tests/                  unit, contract, integration, support, and evaluator assets
docs/                   maintained project and research documentation
selective_updates/      amendment and audit records
scripts/                build and verification utilities
seven_arm_benchmark.py  current CLI/orchestrator and profile registry
```

`kaggle_upload/` is generated output. Do not manually implement logic there. Restore or remove stale generated modifications before production work, then regenerate the complete bundle once after canonical code passes all gates.

Do not create a new top-level `benchmark/` package. Do not create a second CLI, a second executor, a second strategy registry, a second results schema, or a second profile system.

The sole V2 execution-profile source remains:

```python
PROFILES["scientific-smoke-v2"]
```

inside `seven_arm_benchmark.py`. `configs/smoke_v2.yaml` must not exist.

---

## 5. Phase 0 — preserve state and remove unrelated noise

### 5.1 Safety backup

From the project root, create these files outside the repository:

```powershell
git diff --binary > ..\three-arm-smoke-v2-pre-spec.patch
git status --short > ..\three-arm-smoke-v2-pre-spec-status.txt
git ls-files --others --exclude-standard > ..\three-arm-smoke-v2-pre-spec-untracked.txt
```

Do not reset the whole branch and do not delete the backup.

### 5.2 Restore known unrelated or generated edits

Restore these canonical files to committed HEAD because their current changes are formatting or unrelated WIP:

```powershell
git restore -- `
  src/benchmark/checkpoint/__init__.py `
  src/benchmark/checkpoint/package.py `
  scripts/rebuild_experiment_reports.py `
  tests/unit/test_deterministic_run_id.py `
  tests/unit/test_hf_sync.py `
  tests/unit/test_su0005_explicit_identity.py
```

Restore all generated mirrors and notebooks; they will be rebuilt once at the end:

```powershell
git restore -- kaggle_upload notebooks/seven_arm_benchmark.ipynb
Remove-Item -Recurse -Force kaggle_upload/data/scenarios/todo-smoke-*.yaml -ErrorAction SilentlyContinue
```

Keep the V2 scenario files, repository-profile corrections, V2 profile in `seven_arm_benchmark.py`, `pyproject.toml` evaluator exclusion, scenario-count test updates, core amendment, and documentation until later phases review or replace them.

### Phase 0 gate

```powershell
python -m pytest -q
```

Required: zero failures. Then print `git status --short` and confirm that generated Kaggle mirrors are clean.

---

## 6. Phase 1 — finish and checkpoint data truth

### Allowed files

- `benchmark_data/scenarios/todo-smoke-001.yaml`
- `benchmark_data/scenarios/todo-smoke-002.yaml`
- `benchmark_data/scenarios/todo-smoke-003.yaml`
- `benchmark_data/repository_profiles/todo.yaml`
- `tests/integration/test_scenarios_integration.py`
- `tests/unit/test_scenarios_loader.py`
- `tests/unit/test_subprocess_pythonpath.py`
- `docs/PROJECT_HANDOFF.md`
- `selective_updates/records/THREE-ARM-CORE-EXPERIMENT.md`

### Required textual cleanups

In `todo.yaml`:

- replace the unsupported phrase “full coverage” with “tests cover baseline model, serializer, view, and permission behaviours represented by the committed test suite”; do not claim measured coverage;
- replace architecture boundary 008 so it does not mention nonexistent `mark_complete`; use: “State-changing model operations must be explicit methods and must not be triggered by property access”;
- remove the duplicate `expected_action_types` key in the permissions artifact;
- preserve the exact five-item `llm_editable` list;
- preserve the corrected existing catalog paths and exact existing included paths.

In `docs/PROJECT_HANDOFF.md`:

- remove `configs/smoke_v2.yaml` from every current tree or current-file list;
- current branch is `experiment/three-arm-smoke-v2`;
- committed HEAD remains `0a1c603` until local checkpoint commits are created;
- working tree is dirty during implementation;
- production strategies, evaluators, token semantics, and scripted production proof are incomplete;
- Kaggle, Pilot, and stable tag are unauthorized;
- this specification is the authoritative next-action document.

### Negative textual gate

These commands must return zero forbidden matches:

```powershell
rg -n "todo_project/|mark_complete|full coverage" benchmark_data/repository_profiles/todo.yaml
rg -n "configs/smoke_v2\.yaml" docs/PROJECT_HANDOFF.md
```

A historical reference is not allowed in the live handoff. If history must be preserved, reference only “the removed duplicate V2 config” without writing the obsolete path.

### Phase 1 tests

```powershell
python -m pytest `
  tests/integration/test_scenarios_integration.py `
  tests/unit/test_scenarios_loader.py `
  tests/unit/test_repositories_manifest.py `
  tests/unit/test_subprocess_pythonpath.py `
  -q
python -m pytest -q
git diff --check
```

After an independent diff review inside the same OpenCode task, create a local checkpoint commit:

```powershell
git add benchmark_data/scenarios benchmark_data/repository_profiles/todo.yaml tests/integration/test_scenarios_integration.py tests/unit/test_scenarios_loader.py tests/unit/test_subprocess_pythonpath.py docs/PROJECT_HANDOFF.md selective_updates/records/THREE-ARM-CORE-EXPERIMENT.md pyproject.toml seven_arm_benchmark.py
git commit -m "docs(data): freeze truthful three-arm smoke contracts"
```

Do not push yet.

---

## 7. Phase 2 — safe editable ArtifactUniverse

### Purpose

A scientific regeneration run must never offer baseline tests, evaluator assets, configuration, existing migrations, caches, or database files as editable LLM targets.

### Files to modify

- `src/benchmark/repositories/snapshot.py`
- `src/benchmark/execution/runner.py`
- `src/benchmark/execution/pipeline.py`
- `seven_arm_benchmark.py`
- `tests/unit/test_repositories_snapshot.py`
- `tests/unit/execution/test_runner.py`
- `tests/contract/test_three_arm_core.py`

### Exact API to add

In `src/benchmark/repositories/snapshot.py`, add:

```python
def resolve_allowed_artifacts(
    snapshot_path: str | Path,
    allowed_paths: tuple[str, ...],
) -> tuple[ArtifactRef, ...]:
    ...
```

Required behaviour:

1. `snapshot_path` must be a directory; otherwise raise `RepositoryError`.
2. `allowed_paths` must be non-empty for scientific regeneration.
3. Every path must be repository-relative POSIX form.
4. Reject absolute paths, `..`, backslashes, duplicates, directories, and missing files.
5. Resolve every path and confirm it remains under the snapshot root.
6. Return sorted `ArtifactRef` objects with `ArtifactType.source`.
7. Do not call `discover_eligible_artifacts` inside this function.

Add to `PipelineConfig` and `RunnerConfig`:

```python
editable_artifact_paths: tuple[str, ...] = ()
max_completion_tokens_per_call: int = 4096
max_total_workflow_tokens: int = 0
```

Retain old `max_tokens_per_run` and `max_tokens` only as deprecated compatibility aliases during this phase. New V2 execution must use the explicit fields.

In `BenchmarkRunner._build_artifact_universe`, for `enable_regeneration=True`, replace broad discovery with:

```python
return ArtifactUniverse(
    artifacts=resolve_allowed_artifacts(
        self._active_snapshot(),
        self._config.editable_artifact_paths,
    )
)
```

Do not use scenario Ground Truth. Fail closed when the editable list is empty or invalid.

In `seven_arm_benchmark.py`, load the active repository profile once. Read:

```python
profile.artifact_universe["llm_editable"]
```

Pass that exact tuple through `PipelineConfig` to `RunnerConfig`. Do not duplicate the five paths in Python.

### Required tests

Tests must prove:

- the Todo V2 universe is exactly the five profile paths;
- tests, migrations, config, `manage.py`, `__init__.py`, caches, and DB files are absent;
- invalid, missing, absolute, duplicate, and traversal paths fail closed;
- changing `scenario.expected_affected_artifacts` does not change the universe;
- Runner uses the same resolver as production CLI configuration.

### Phase 2 gate

Run focused tests, then full suite, Ruff on changed files, mypy strict on changed production files, compileall, and `git diff --check`. Create:

```powershell
git commit -am "fix(execution): enforce profile-defined editable universe"
```

Do not push.

---

## 8. Phase 3 — full-scope reference contract

`MonolithicRegenerationStrategy` already returns `regenerate` for every ArtifactUniverse entry. Do not rewrite it unless a test exposes a real defect.

The required V2 behaviour is achieved by the safe five-file universe. Add behaviour tests only:

- prediction contains exactly five decisions;
- every decision is `regenerate`;
- no file outside the universe appears;
- the plan reaches SharedRegenerationExecutor through the actual Runner non-dry path;
- a successful regeneration run cannot report zero calls or zero generated files.

Do not give Monolithic tests or evaluator files. Do not combine all files into a new second prompt implementation. The current shared executor may call the LLM once per selected artifact; the same rule applies to Selective and agent-selected files.

No separate commit is required if only tests change; include these tests in the Phase 4 commit.

---

## 9. Phase 4 — deterministic dependency-aware Selective

### Remove the broken algorithm

In `src/benchmark/strategies/selective.py`, remove the current three-signal voting implementation. Specifically remove:

- seeding the graph with all ArtifactUniverse paths;
- path-only Jaccard similarity;
- traceability voting as a requirement for the main V2 selective arm;
- `human_review` as the normal result of a single weak signal.

Historical ablation classes may remain untouched. Only the V2 `HybridSelectiveStrategy` behaviour changes, while its public name remains for checkpoint compatibility.

### New file

Create exactly one new production module:

```text
src/benchmark/selection/dependency_scope.py
```

It must define:

```python
@dataclass(frozen=True)
class ArtifactDescriptor:
    path: str
    category: str
    description: str
    provides_symbols: tuple[str, ...]
    typical_change_triggers: tuple[str, ...]


def descriptors_from_profile(
    artifact_catalog: tuple[dict[str, object], ...],
    editable_paths: tuple[str, ...],
) -> tuple[ArtifactDescriptor, ...]:
    ...


def derive_requirement_terms(change: RequirementChange) -> frozenset[str]:
    ...


def select_dependency_scope(
    change: RequirementChange,
    artifact_universe: ArtifactUniverse,
    descriptors: tuple[ArtifactDescriptor, ...],
    graph: DependencyGraph,
) -> tuple[str, ...]:
    ...
```

### Exact deterministic algorithm

1. Build requirement text only from `before`, `after`, and public acceptance criteria.
2. Normalize lowercase words, snake_case parts, CamelCase parts, and singular/plural variants using deterministic string logic only.
3. Use one generic stop-word set containing common English function words. The list must not contain project-specific words and must not be changed per scenario.
4. For each editable descriptor, create terms from path stem, category, description, symbols, and change triggers.
5. A descriptor is a seed when either:
   - a normalized provided symbol appears in requirement terms; or
   - at least two non-stop requirement terms appear in its descriptor terms; or
   - a complete normalized trigger phrase has at least two matching content words.
6. If no seed exists, return an `ImpactPrediction` error. Do not silently select all files and do not consult Ground Truth.
7. The profile graph edge `A -> B` means A depends on B. Starting from a seed, include the seed and its direct dependencies by following outgoing edges.
8. For cross-cutting permission changes, the profile metadata itself should seed permissions and views through their triggers; do not add scenario-ID conditions.
9. Intersect the final paths with ArtifactUniverse.
10. Return sorted unique paths.

`HybridSelectiveStrategy.__init__` must accept:

```python
graph: DependencyGraph
artifact_descriptors: tuple[ArtifactDescriptor, ...]
```

`analyze_impact` must mark selected paths `regenerate` and every other universe path `preserve`. It must not use Ground Truth and must not contain `todo-smoke-*` strings.

In `seven_arm_benchmark.py`, construct descriptors from the loaded repository profile and pass them through `make_strategy` to the production strategy. No test-only builder may bypass this path.

### Tests

Do not assert exact equality to Ground Truth as the main strategy contract. Test:

- deterministic repeatability;
- non-empty selection for all three public change requests;
- no scenario ID branches;
- no Ground Truth access;
- every selected path belongs to the five-file universe;
- broad irrelevant text fails closed rather than selecting all;
- production Runner receives profile descriptors and graph;
- post-hoc precision and recall are calculated only after prediction.

A diagnostic test may print the selected paths for the three Smoke changes, but it must not tune or change the algorithm based on expected paths.

### Phase 4 gate and commit

Run focused selection, strategy, Runner, CLI, and contract tests; then full suite, Ruff, mypy, compileall, and diff check. Commit:

```powershell
git add src/benchmark/selection/dependency_scope.py src/benchmark/strategies/selective.py src/benchmark/selection/__init__.py seven_arm_benchmark.py tests
git commit -m "feat(selection): implement repository-derived selective scope"
```

Do not push.

---

## 10. Phase 5 — bounded Repository Agent

### Files

- `src/benchmark/strategies/iterative_agent.py`
- new `src/benchmark/strategies/repository_tools.py`
- `src/benchmark/strategies/__init__.py`
- `src/benchmark/execution/runner.py`
- related agent unit/integration/contract tests

### Exact tool API

Create:

```python
@dataclass(frozen=True)
class RepositoryToolResult:
    ok: bool
    output: str
    error: str = ""
    duration_seconds: float = 0.0


class RepositoryTools:
    def __init__(self, workspace_root: str | Path, max_distinct_files: int = 30) -> None: ...
    def list_files(self, path: str = ".") -> RepositoryToolResult: ...
    def read_file(self, path: str) -> RepositoryToolResult: ...
    def search_text(self, query: str, path: str = ".") -> RepositoryToolResult: ...
```

Rules:

- all paths resolve under active workspace;
- evaluator assets and Ground Truth data are outside workspace and inaccessible;
- reject absolute paths, traversal, symlinks escaping root, binary files, caches, databases, `.git`, and files larger than 200 KB;
- `list_files` returns sorted repository-relative paths, at most 200 entries;
- `read_file` returns at most 12,000 characters;
- `search_text` is literal, case-insensitive, returns at most 50 `path:line:text` matches;
- track distinct files read/searched;
- fail after 30 distinct inspected files.

### Agent loop protocol

Keep the class name `IterativeRepositoryAgentStrategy`. Do not create an incompatible alias.

The initial LLM call receives:

- public requirement before/after;
- public acceptance criteria;
- the five editable paths;
- JSON tool schema;
- no file contents unless returned by tools;
- no Ground Truth or evaluator text.

Each response must be exactly one JSON object with one of these actions:

```json
{"action":"list_files","path":"todo"}
{"action":"read_file","path":"todo/models.py"}
{"action":"search_text","query":"permission_classes","path":"todo"}
{"action":"final","selected_paths":["todo/models.py"],"rationale":"..."}
```

Maximum eight selection/retrieval LLM calls. Invalid JSON consumes a call and produces a structured error. Unknown actions fail closed. `selected_paths` must be non-empty, unique, and a subset of ArtifactUniverse. The strategy returns `ImpactPrediction`: selected paths regenerate; other paths preserve.

Preserve existing validation-feedback repair behaviour through `revise_plan`. Repair may revise selected paths, but it uses the same tool restrictions and remaining call limit. Do not create a second code-writing method. SharedRegenerationExecutor writes every source file.

Record on the strategy and propagate to RunRecord:

- selection prompt/completion/total tokens;
- selection model calls;
- selection duration;
- tool calls;
- tool duration;
- distinct files inspected;
- compact tool transcript with no full file content persisted.

### Phase 5 tests and commit

Test traversal, symlinks, binary/large file handling, deterministic ordering, file and call budgets, final subset validation, evaluator/Ground Truth isolation, and actual Runner use. Preserve all existing iterative-agent tests unless their old assertion directly contradicts the new defined repository-agent behaviour; replace such assertions with equivalent contract tests instead of deleting coverage.

Commit after all gates:

```powershell
git add src/benchmark/strategies tests
git commit -m "feat(agent): add bounded repository exploration loop"
```

---

## 11. Phase 6 — scenario execution contract, migrations, and evaluators

### Scenario model fields

Extend `ScenarioModel` and core `Scenario` with public execution metadata that is not Ground Truth and is never sent to the LLM:

```python
evaluator_asset: str = ""
post_generation_command: tuple[str, ...] = ()
require_new_migration: bool = False
```

Add these exact YAML values to all three V2 scenarios:

```yaml
evaluator_asset: tests/evaluator_assets/<scenario-id>_checks.py
post_generation_command:
  - python
  - manage.py
  - makemigrations
  - todo
  - --noinput
require_new_migration: true
```

The evaluator file name must match each scenario ID with hyphens replaced by underscores.

### Migration runner

Create exactly:

```text
src/benchmark/execution/post_generation.py
```

with:

```python
@dataclass(frozen=True)
class PostGenerationResult:
    passed: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    created_paths: tuple[str, ...]
```

Before command execution, snapshot existing `todo/migrations/*.py` paths and hashes. Run the command in the isolated workspace. After execution:

- existing migration hashes must remain unchanged;
- exactly one new numbered migration file must exist when `require_new_migration=True`;
- `__init__.py` is not counted;
- return created relative path;
- failure is a run failure, not a warning.

### Evaluator runner

Create exactly:

```text
src/benchmark/execution/scenario_evaluator.py
```

with a result dataclass and a function that:

1. validates that the evaluator asset is under the project’s canonical `tests/evaluator_assets/` directory;
2. copies only the evaluator script into a temporary directory outside the model-visible workspace;
3. executes it in a fresh Python subprocess with the generated workspace passed as an argument;
4. sets `PYTHONPATH` so imports resolve from the generated workspace first;
5. expects one JSON object with `passed`, `checks`, and `error`;
6. times out using Runner validation timeout;
7. never imports generated workspace Django modules into the parent benchmark process.

Create or replace exactly three evaluator files:

- `tests/evaluator_assets/todo_smoke_001_checks.py`
- `tests/evaluator_assets/todo_smoke_002_checks.py`
- `tests/evaluator_assets/todo_smoke_003_checks.py`

Each script must create its own temporary test database using Django’s test runner, run migrations, execute public acceptance checks, print one JSON object, tear down databases, restore environment state, and exit non-zero when any check fails.

Do not assume fields that do not exist in the baseline. Smoke 001 must create Project without an owner because Project owner belongs only to Smoke 003. Smoke 003 may create a Project through the API to verify creator assignment.

### Validation order

For every non-dry regeneration run:

1. SharedRegenerationExecutor applies LLM output.
2. Post-generation migration command runs.
3. Baseline command runs: `python -m pytest -q` in the generated Todo workspace.
4. Scenario evaluator runs.
5. Migration consistency result is checked.
6. Run succeeds only when all stages pass and at least one model call and one generated source artifact exist.

Add separate RunRecord fields for baseline validation, evaluator validation, and migration generation. Do not overload one boolean.

### Phase 6 commit

After focused and full gates:

```powershell
git add src/benchmark/execution src/benchmark/core/models.py src/benchmark/scenarios tests/evaluator_assets tests
git commit -m "feat(validation): add migrations and isolated scenario evaluators"
```

---

## 12. Phase 7 — token semantics and truthful metrics

### Configuration

The scientific setting is:

```text
max_completion_tokens_per_call = 4096
```

This is not the total workflow token cap. An optional independent runaway ceiling may be configured as `max_total_workflow_tokens=0` for unlimited locally or a clearly named larger value. Never reuse `4096` as the aggregate workflow budget.

Update:

- `PipelineConfig`;
- `RunnerConfig`;
- CLI argument naming and help;
- SharedRegenerationExecutor;
- IterativeRepositoryAgentStrategy;
- repair logic;
- persistence schema and report forwarding.

Each backend call must receive exactly `max_completion_tokens_per_call`, except when an explicit optional total safety ceiling has less remaining allowance. The normal confirmatory run must not be truncated by a 4096 aggregate limit.

For real Qwen scientific runs, token counting must use the backend tokenizer. The `len(text)//4` fallback is allowed only for mock/scripted engineering tests and must be labelled approximate. If a real backend cannot count tokens, fail before generation.

### Required metrics

Per run record:

- selection prompt, completion, total tokens;
- selection model calls and duration;
- tool calls, tool duration, files inspected;
- regeneration prompt, completion, total tokens;
- regeneration model calls and duration;
- repair prompt, completion, total tokens;
- repair calls and duration;
- migration duration and generated paths;
- baseline validation duration and pass/fail;
- evaluator duration and pass/fail;
- total workflow tokens, calls, and duration;
- files selected, generated, preserved, and unnecessarily modified;
- post-hoc impact precision and recall.

Assertions:

```text
selection_total = selection_prompt + selection_completion
regeneration_total = regeneration_prompt + regeneration_completion
repair_total = repair_prompt + repair_completion
total_workflow_tokens = selection_total + regeneration_total + repair_total
total_workflow_model_calls = selection_calls + regeneration_calls + repair_calls
```

Time totals must include selection/tool work, generation, repair, migration, baseline validation, and evaluator validation. Do not count setup that is identically shared and performed once outside every run unless the protocol explicitly decides to amortize it; document such shared setup separately.

Create a local checkpoint commit after all accounting tests pass.

---

## 13. Phase 8 — scripted backend through the real production path

### Test support only

Create:

```text
tests/support/scripted_llm_backend.py
tests/support/scripted_smoke_v2.py
tests/integration/test_scientific_smoke_v2_production_path.py
```

Do not add a scripted backend to the real provider registry or Kaggle CLI.

`ScriptedLLMBackend` must inspect prompts only to identify:

- scenario public requirement;
- requested artifact path;
- repository-agent tool action stage.

It may return deterministic valid source content for the controlled three scenarios. This is an orchestration fixture, not a strategy implementation. Production Selective and agent code must not import it.

The support runner must execute the actual non-dry production classes with:

```text
dry_run=False
enable_regeneration=True
real staged immutable snapshot
fresh workspace per record
real Runner
real strategies
real SharedRegenerationExecutor
real post-generation migration command
real baseline tests
real scenario evaluator
real record persistence
```

Run all 9 cells. Persist JSONL records under a temporary output directory. Inspect records after loading them back from disk.

### Mandatory record assertions

For every successful record:

- status is succeeded;
- `total_workflow_model_calls > 0`;
- `regeneration_model_calls > 0`;
- `regenerated_artifact_count > 0`;
- `total_workflow_tokens > 0`;
- baseline validation passed;
- scenario evaluator passed;
- migration generation passed;
- exactly one new migration path recorded;
- workspace differs from snapshot;
- snapshot hash before and after is identical;
- no baseline test, evaluator, config, or existing migration file was modified;
- persisted record reload equals the in-memory identity and metrics.

The 9-record test must fail when dry-run is accidentally enabled or when any strategy returns a no-op.

Do not claim real model quality from scripted outputs. The gate proves harness correctness only.

---

## 14. Phase 9 — final canonical cleanup, documentation, bundle, and Git

### Remove weak tests

Replace `tests/contract/test_three_arm_core.py` entirely if necessary. Final tests must not rely only on `isinstance`, `hasattr`, directory existence, or `python -c exit(0)`. They must prove the production behaviours defined above.

### Documentation

Update only after all local production-path tests pass:

- `README.md` — concise three-arm definition and current command;
- `docs/MASTER_IMPLEMENTATION_PLAN.md` — V2 local proof completed, real Kaggle pending;
- `docs/PROJECT_HANDOFF.md` — exact branch, final HEAD, clean status, commands, remaining work;
- `selective_updates/records/THREE-ARM-CORE-EXPERIMENT.md` — implementation facts, not claims of real results;
- `selective_updates/CHANGE_INDEX.md`;
- `selective_updates/metrics/change_metrics.jsonl`.

The Handoff must include:

- core research question;
- canonical structure;
- three arms;
- three Smoke changes;
- profile source;
- exact commands;
- exact local test evidence;
- real Kaggle status;
- Pilot admission policy;
- tag policy.

### Final validation

Run in this order:

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
```

Then inspect canonical/generated parity for every changed production file. The build script must be the only source of Kaggle mirrors.

Run the scripted nine-record production experiment once more after bundle generation.

### Focused commits

If phases created local checkpoint commits, create one final documentation/bundle commit. Otherwise split remaining work into these focused commits:

1. `docs(data): freeze truthful three-arm smoke contracts`
2. `fix(execution): enforce profile-defined editable universe`
3. `feat(selection): implement repository-derived selective scope`
4. `feat(agent): add bounded repository exploration loop`
5. `feat(validation): add migrations and isolated scenario evaluators`
6. `fix(metrics): separate per-call limits and workflow totals`
7. `test(smoke): prove nine scripted production-path records`
8. `chore(bundle): regenerate V2 deployable bundle`

Push only after every final gate passes:

```powershell
git push -u origin experiment/three-arm-smoke-v2
```

Do not launch Kaggle automatically. Do not merge. Do not create a tag.

---

## 15. Release and tag policy

A local scripted production-path success is not a stable scientific release. It authorizes preparing and launching the real Kaggle Smoke only.

A stable V2 tag is authorized only when:

1. the pushed branch exactly matches the deployed build;
2. Qwen runs all 9 cells;
3. every run record is persisted and auditable, including failures;
4. token, call, duration, and artifact metrics are non-zero and internally consistent;
5. correctness and regression results are available for all cells;
6. Ground Truth isolation is independently audited;
7. no post-result algorithm tuning occurs;
8. an independent code and result audit approves the milestone.

After approval, use an annotated tag such as:

```text
v2.0.0-scientific-smoke
```

Pilot remains blocked until that tag exists.

---

## 16. Forbidden implementation choices

OpenCode must not:

- create another branch;
- reset or discard work without the Phase 0 backup;
- create a parallel package or second harness;
- manually edit generated Kaggle mirrors;
- use OpenRouter;
- call a real LLM locally;
- add an embedding model, vector database, agent framework, or external dependency for selection;
- tune Selective using expected affected files;
- expose evaluator code to any arm;
- allow the LLM to edit tests, evaluator files, config, existing migrations, or database/cache artifacts;
- treat tests generated by the LLM as correctness evidence;
- treat dry-run success as execution proof;
- use scenario ID branches in production strategies;
- silently select every file when Selective or agent selection fails;
- report a successful run with zero generation calls or zero generated artifacts;
- modify historical ablation arms unless a shared-interface compatibility change is unavoidable and tested;
- start Pilot work;
- launch Kaggle, merge, or tag without explicit user instruction after final audit.

---

## 17. Final response contract

OpenCode’s final response must contain:

1. safety backup paths;
2. restored unrelated files;
3. data-truth negative-search results;
4. final editable universe paths;
5. Monolithic selected paths;
6. Selective descriptors, seeds, graph traversal, and final selected paths for each scenario;
7. repository-agent call count, tool count, inspected paths, and final selected paths for each scenario;
8. proof all arms used the same SharedRegenerationExecutor;
9. migration created path for every scripted record;
10. baseline and evaluator result for every scripted record;
11. token semantics and stage totals;
12. a nine-row table containing scenario, arm, status, calls, tokens, selected count, generated count, baseline pass, evaluator pass, migration pass;
13. snapshot integrity result;
14. full project tests;
15. Todo baseline tests and Django check;
16. Ruff, mypy, compileall, bundle, and diff check;
17. documentation updated;
18. commits and final HEAD;
19. clean working tree;
20. local/remote equality;
21. real Kaggle authorization status;
22. Pilot status;
23. stable-tag status.

The response must not say “ready” unless all scripted production-path gates pass. It must not say “stable” or “scientifically validated” before real Qwen execution and audit.

End exactly with:

```text
THREE_ARM_V2_LOCAL_PRODUCTION_PROOF_COMPLETE
```
