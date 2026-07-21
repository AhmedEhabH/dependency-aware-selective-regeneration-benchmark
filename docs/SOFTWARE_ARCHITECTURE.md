# Software Architecture — Dependency-Aware Selective Regeneration Benchmark

**Phase:** 3.5 — Static Architecture Audit and Project Map
**Date:** 2026-07-22
**Status:** FROZEN

---

## 1. Layering Overview

The architecture is organised as **13 layers**. Each layer depends _inward_ only: a layer may import from any layer with a lower number, but never from a higher-numbered layer.

| Layer # | Layer Name | Phase Created | Public/Internal |
|----------|------------|---------------|-----------------|
| 1 | Domain / Core | Phase 4 | Public |
| 2 | Configuration | Phase 4 | Public |
| 3 | Repository Adapters | Phase 4 | Internal |
| 4 | Scenario Services | Phase 4 | Internal |
| 5 | Graph & Impact Analysis | Phase 4 | Internal |
| 6 | Strategy Plugins | Phase 4 | Internal |
| 7 | LLM Backends | Phase 4 | Internal |
| 8 | Execution Orchestration | Phase 4 | Internal |
| 9 | Validation | Phase 4 | Internal |
| 10 | Evaluation & Metrics | Phase 4 | Internal |
| 11 | Statistics | Phase 4 | Internal |
| 12 | Provenance | Phase 4 | Internal |
| 13 | Reporting | Phase 4 | Internal |

### Key Rule: Core Must NOT Depend On

- Concrete strategy implementations
- Qwen, Kaggle, or any cloud-specific backend
- Notebooks (Jupyter / Kaggle kernels)
- Repository-specific code (e.g. todo-specific logic)
- Reporting formats (Markdown, CSV, JSON)
- OS-specific paths

---

## 2. Layer 1 — Domain / Core

**Responsibility:** Immutable data models, enums, exceptions, protocols (`typing.Protocol`), the registry, and the execution context. This is the innermost layer; everything depends on it.

**Key classes / interfaces:**

| Name | Kind | Description |
|------|------|-------------|
| `ImpactPrediction` | `dataclass` (frozen) | Strategy output: list of `(artifact_path, action)` pairs where action ∈ `{regenerate, preserve, validate_only, human_review}` |
| `ActionKind` | `Enum` | `REGENERATE`, `PRESERVE`, `VALIDATE_ONLY`, `HUMAN_REVIEW` |
| `RequirementChange` | `dataclass` (frozen) | Before/after text + acceptance criteria |
| `ArtifactUniverse` | `dataclass` (frozen) | Set of candidate artifact paths + types |
| `RepositorySnapshot` | `dataclass` (frozen) | File tree, metadata, commit SHA |
| `Scenario` | `dataclass` (frozen) | Repository, change, universe, constraints |
| `RunRecord` | `dataclass` (frozen) | Strategy name, scenario id, prediction, timestamps, errors |
| `ValidationReport` | `dataclass` (frozen) | Validation results for a single run |
| `LLMResponse` | `dataclass` (frozen) | Text content, token counts, finish reason |
| `AnalysisReport` | `dataclass` (frozen) | Combined statistical results |
| `BenchmarkError` | `Exception` subclass | Base exception for all benchmark errors |
| `ImpactStrategy` | `typing.Protocol` | Interface for strategies |
| `LLMBackend` | `typing.Protocol` | Interface for LLM providers |
| `RepositoryAdapter` | `typing.Protocol` | Interface for repo operations |
| `ScenarioProvider` | `typing.Protocol` | Interface for scenario loading |
| `DependencyExtractor` | `typing.Protocol` | Interface for graph building |
| `ExecutionRunner` | `typing.Protocol` | Interface for running strategies |
| `Validator` | `typing.Protocol` | Interface for validation |
| `Metric` | `typing.Protocol` | Interface for metrics |
| `StatisticsAnalyzer` | `typing.Protocol` | Interface for stats |
| `ResultWriter` | `typing.Protocol` | Interface for writing results |
| `ProvenanceRecorder` | `typing.Protocol` | Interface for provenance events |

**Dependencies:** None (stdlib only)

**Phase created:** Phase 4

**Public/Internal:** Public — all layers import from here.

---

## 3. Layer 2 — Configuration

**Responsibility:** Config models, loader, validation (Pydantic-based). Reads YAML configs and produces validated configuration objects.

**Key classes:**

| Name | Kind | Description |
|------|------|-------------|
| `BenchmarkConfig` | `BaseModel` | Top-level config: strategies, backends, scenarios, execution params |
| `ConfigLoader` | class | Loads YAML → validates → returns `BenchmarkConfig` |
| `StrategyConfig` | `BaseModel` | Strategy name, parameters, LLM backend ref |
| `ExecutionConfig` | `BaseModel` | Timeouts, retries, parallelism, budgets |

**Dependencies:** Layer 1 (Core models)

**Phase created:** Phase 4

**Public/Internal:** Public

---

## 4. Layer 3 — Repository Adapters

**Responsibility:** Base class, loader, snapshot, manifest, workspace management. Abstracts local/remote repositories.

**Key classes:**

| Name | Kind | Description |
|------|------|-------------|
| `RepositoryAdapter` | `Protocol` | `clone(url, ref) → RepositorySnapshot`, `checkout(sha)`, `run_tests(paths)` |
| `GitRepositoryAdapter` | class | Concrete implementation using `gitpython` |
| `ControlledTodoAdapter` | class | Specialised adapter for the synthetic Django Todo repo |
| `SnapshotManager` | class | Caches and serves `RepositorySnapshot` instances |
| `WorkspaceManager` | class | Handles clone, cleanup, isolation per run |

**Dependencies:** Layers 1–2

**Phase created:** Phase 4

**Public/Internal:** Internal

---

## 5. Layer 4 — Scenario Services

**Responsibility:** Scenario models, loader, validator, sequencing.

**Key classes:**

| Name | Kind | Description |
|------|------|-------------|
| `ScenarioProvider` | `Protocol` | `get_scenario(id) → Scenario`, `list_scenarios(repo_id) → list[Scenario]` |
| `YamlScenarioProvider` | class | Loads scenarios from `benchmark_data/scenarios/` |
| `ScenarioValidator` | class | Validates scenario prerequisites (repo version, artifact universe) |
| `ScenarioSequencer` | class | Orders scenarios for execution (avoiding interference) |

**Dependencies:** Layers 1–2

**Phase created:** Phase 4

**Public/Internal:** Internal

---

## 6. Layer 5 — Graph and Impact Analysis

**Responsibility:** Models, builder, extractors, traversal for dependency graphs.

**Key classes:**

| Name | Kind | Description |
|------|------|-------------|
| `DependencyGraph` | `dataclass` | Nodes = artifacts, edges = dependency relations |
| `DependencyExtractor` | `Protocol` | `build_graph(snapshot) → DependencyGraph` |
| `PythonImportExtractor` | class | Extracts import-level edges from Python files |
| `DjangoModelExtractor` | class | Extracts model-level edges (ForeignKey, ManyToMany, signals) |
| `ImpactPropagator` | class | BFS/DFS traversal from changed artifacts to compute impact set |
| `ScopeReducer` | class | Filters impact set by change type (localised vs cross-cutting) |

**Dependencies:** Layers 1–2

**Phase created:** Phase 4

**Public/Internal:** Internal

---

## 7. Layer 6 — Strategy Plugins

**Responsibility:** Base protocol, registry, 7 concrete strategy implementations.

**Key classes:**

| Name | Kind | Description |
|------|------|-------------|
| `ImpactStrategy` | `Protocol` | `analyze_impact(repository, requirement_change, artifact_universe) → ImpactPrediction` |
| `RepositoryAgentStrategy` | class | Full repository context + LLM-powered analysis |
| `StaticOnlyStrategy` | class | Static dependency graph only |
| `SemanticOnlyStrategy` | class | Semantic similarity / embedding-based only |
| `TraceabilityOnlyStrategy` | class | Test-coverage traceability only |
| `HybridSelectiveStrategy` | class | Combines static + semantic + traceability |
| `FullContextStrategy` | class | All signals available (upper-bound reference) |
| `MonolithicRegenerationStrategy` | class | Baseline: regenerate everything |

**Dependencies:** Layers 1–5 (strategies may use graph analysis adapters)

**Phase created:** Phase 4

**Public/Internal:** Internal

**Extension rules:** To add a new strategy, create a file in `src/benchmark/strategies/`, implement `ImpactStrategy`, and register in `strategies/registry.py`.

---

## 8. Layer 7 — LLM Backends

**Responsibility:** Base protocol, mock backend, dry-run backend, Kaggle Qwen backend.

**Key classes:**

| Name | Kind | Description |
|------|------|-------------|
| `LLMBackend` | `Protocol` | `async generate(prompt, temperature, max_tokens) → LLMResponse` |
| `MockLLMBackend` | class | Deterministic, fixture-based responses for unit tests |
| `DryRunBackend` | class | Returns placeholder responses, no real API calls |
| `KaggleQwenBackend` | class | Torch/Transformers inference; lazy-imports torch and transformers |

**Import isolation:** `KaggleQwenBackend` must `import torch` and `import transformers` inside method bodies, not at module level. This ensures the module can be imported in environments without those packages.

**Dependencies:** Layer 1

**Phase created:** Phase 4

**Public/Internal:** Internal

---

## 9. Layer 8 — Execution Orchestration

**Responsibility:** Runner, pipeline, repair, budgets, isolation.

**Key classes:**

| Name | Kind | Description |
|------|------|-------------|
| `ExecutionRunner` | `Protocol` | `run_strategy(strategy, scenario) → RunRecord` |
| `SequentialRunner` | class | Runs strategies one at a time |
| `ParallelRunner` | class | Runs strategies in parallel with resource limits |
| `RepairLoop` | class | Iterative repair cycle (run tests → fix → rerun) |
| `BudgetController` | class | Enforces timeouts, token budgets, iteration limits |
| `WorkspaceIsolator` | class | Ensures each run gets a clean workspace |

**Dependencies:** Layers 1–7

**Phase created:** Phase 4

**Public/Internal:** Internal

---

## 10. Layer 9 — Validation

**Responsibility:** Functional, regression, architecture, leakage, file scope validation.

**Key classes:**

| Name | Kind | Description |
|------|------|-------------|
| `Validator` | `Protocol` | `validate(snapshot, result) → ValidationReport` |
| `FunctionalValidator` | class | Runs tests and checks pass rates |
| `RegressionValidator` | class | Ensures unchanged artifacts still pass |
| `ArchitectureValidator` | class | Checks architecture constraints are met |
| `LeakageChecker` | class | Verifies strategies did not access private data |
| `FileScopeValidator` | class | Ensures only predicted artifacts were modified |

**Dependencies:** Layers 1–8

**Phase created:** Phase 4

**Public/Internal:** Internal

---

## 11. Layer 10 — Evaluation and Metrics

**Responsibility:** Scoring, impact metrics, preservation metrics, architecture metrics, efficiency metrics.

**Key classes:**

| Name | Kind | Description |
|------|------|-------------|
| `Metric` | `Protocol` | `name: str` property, `compute(prediction, ground_truth) → float` |
| `ImpactPrecision` | class | TP / (TP + FP) for regenerate actions |
| `ImpactRecall` | class | TP / (TP + FN) for regenerate actions |
| `ImpactF1` | class | Harmonic mean of precision and recall |
| `PreservationAccuracy` | class | Correctly preserved / total preserved |
| `ArchitectureCompliance` | class | % of predictions respecting architecture constraints |
| `EfficiencyScore` | class | Tokens used / correct predictions |
| `ScoringEngine` | class | Orchestrates all metrics, computes aggregate scores |

**Dependencies:** Layers 1–2 (metrics), Layer 10 imports private ground truth data

**Phase created:** Phase 4

**Public/Internal:** Internal

---

## 12. Layer 11 — Statistics

**Responsibility:** Paired tests, bootstrap, non-inferiority, multiple comparison corrections.

**Key classes:**

| Name | Kind | Description |
|------|------|-------------|
| `StatisticsAnalyzer` | `Protocol` | `analyze(results) → AnalysisReport` |
| `PairedTTest` | class | Strategy A vs Strategy B comparison |
| `BootstrapCI` | class | Non-parametric confidence intervals |
| `NonInferiorityTest` | class | Tests if selective strategy is non-inferior to monolithic |
| `HolmBonferroni` | class | Multiple comparison correction |

**Dependencies:** Layers 1–2, Layer 10 (evaluation results)

**Phase created:** Phase 4

**Public/Internal:** Internal

---

## 13. Layer 12 — Provenance

**Responsibility:** Models, recorder, hashing for full audit trail.

**Key classes:**

| Name | Kind | Description |
|------|------|-------------|
| `ProvenanceRecorder` | `Protocol` | `record(event) → void` |
| `ProvenanceEvent` | `dataclass` | Timestamp, layer, action, input hash, output hash |
| `SqliteProvenanceRecorder` | class | Persists events to SQLite |
| `ContentHasher` | class | SHA-256 hashing of artifacts and predictions |

**Dependencies:** Layer 1

**Phase created:** Phase 4

**Public/Internal:** Internal

---

## 14. Layer 13 — Reporting

**Responsibility:** Raw results, summaries, manifests.

**Key classes:**

| Name | Kind | Description |
|------|------|-------------|
| `ResultWriter` | `Protocol` | `write_run(record) → void` |
| `JsonResultWriter` | class | Writes results as JSON |
| `MarkdownSummaryWriter` | class | Generates human-readable Markdown summaries |
| `ManifestGenerator` | class | Generates reproducibility manifests |

**Dependencies:** Layers 1–12

**Phase created:** Phase 4

**Public/Internal:** Internal

---

## 15. Interface Specifications

### 15.1 `ImpactStrategy` (Layer 6)

| Item | Specification |
|------|---------------|
| **Responsibility** | Determine which artifacts to regenerate, preserve, validate-only, or send for human review |
| **Input types** | `repository: RepositorySnapshot`, `requirement_change: RequirementChange`, `artifact_universe: ArtifactUniverse` |
| **Output type** | `ImpactPrediction` |
| **Failure behavior** | Must never raise; returns `ImpactPrediction(errors=[...])` |
| **Lifecycle** | One call per scenario; stateless between calls |
| **Side effects** | None (read-only analysis) |
| **Extension rules** | New strategies implement `ImpactStrategy` and register in `strategies/registry.py` |
| **Example** | `HybridSelectiveStrategy` builds a graph, runs embeddings, traces tests, then combines signals |

### 15.2 `LLMBackend` (Layer 7)

| Item | Specification |
|------|---------------|
| **Responsibility** | Provide LLM text generation with configurable temperature and token limits |
| **Input types** | `prompt: str`, `temperature: float`, `max_tokens: int` |
| **Output type** | `LLMResponse` (text, token_counts, finish_reason) |
| **Failure behavior** | Raises `LLMError` on API failure; retry is handled by caller |
| **Lifecycle** | Multiple calls per run; may be stateful (some backends cache) |
| **Side effects** | Network calls for remote backends; file I/O for mock backend |
| **Extension rules** | New backends implement `LLMBackend`; add factory entry in `llm/` module |
| **Example** | `MockLLMBackend` returns fixture text; `KaggleQwenBackend` runs local inference |

### 15.3 `RepositoryAdapter` (Layer 3)

| Item | Specification |
|------|---------------|
| **Responsibility** | Clone, checkout, test execution on a repository |
| **Input types** | `clone(url, ref)`, `checkout(sha)`, `run_tests(paths)` |
| **Output types** | `RepositorySnapshot`, `None`, `TestResult` |
| **Failure behavior** | Raises `RepositoryError` on clone/checkout failure; `TestError` on test infrastructure failure |
| **Lifecycle** | One adapter instance per repository; cloned once, checked out many times |
| **Side effects** | Disk I/O (clone, checkout), process execution (tests) |
| **Extension rules** | New adapters implement `RepositoryAdapter`; add factory entry |
| **Example** | `GitRepositoryAdapter` runs `git clone`, `git checkout`; `ControlledTodoAdapter` generates synthetic repo |

### 15.4 `ScenarioProvider` (Layer 4)

| Item | Specification |
|------|---------------|
| **Responsibility** | Load and list scenarios from benchmark data |
| **Input types** | `get_scenario(id: str)`, `list_scenarios(repo_id: str)` |
| **Output types** | `Scenario`, `list[Scenario]` |
| **Failure behavior** | Raises `ScenarioNotFoundError` for missing IDs |
| **Lifecycle** | Loaded once at startup; scenarios are immutable |
| **Side effects** | File I/O (YAML loading) |
| **Extension rules** | New providers implement `ScenarioProvider` |
| **Example** | `YamlScenarioProvider` reads `benchmark_data/scenarios/<id>.yaml` |

### 15.5 `DependencyExtractor` (Layer 5)

| Item | Specification |
|------|---------------|
| **Responsibility** | Build a dependency graph from a repository snapshot |
| **Input types** | `snapshot: RepositorySnapshot` |
| **Output type** | `DependencyGraph` |
| **Failure behavior** | Returns empty graph on parse errors; logs warnings |
| **Lifecycle** | One call per scenario per strategy that uses graphs |
| **Side effects** | None (in-memory parsing) |
| **Extension rules** | New extractors implement `DependencyExtractor` |
| **Example** | `PythonImportExtractor` parses `import`/`from` statements; `DjangoModelExtractor` parses model relations |

### 15.6 `ExecutionRunner` (Layer 8)

| Item | Specification |
|------|---------------|
| **Responsibility** | Execute a strategy against a scenario and produce a run record |
| **Input types** | `strategy: ImpactStrategy`, `scenario: Scenario` |
| **Output type** | `RunRecord` |
| **Failure behavior** | Catches all exceptions; embeds errors in `RunRecord` |
| **Lifecycle** | One call per (strategy, scenario) pair |
| **Side effects** | Disk I/O (workspace), process execution (tests), possibly network (LLM) |
| **Extension rules** | New runners implement `ExecutionRunner` |
| **Example** | `SequentialRunner` calls strategy, waits, validates, returns record |

### 15.7 `Validator` (Layer 9)

| Item | Specification |
|------|---------------|
| **Responsibility** | Validate a strategy's result against the repository snapshot |
| **Input types** | `snapshot: RepositorySnapshot`, `result: RunRecord` |
| **Output type** | `ValidationReport` |
| **Failure behavior** | Never raises; partial validation is reported in the report |
| **Lifecycle** | One call per run, after execution completes |
| **Side effects** | None (pure validation) |
| **Extension rules** | New validators implement `Validator` |
| **Example** | `FunctionalValidator` runs tests; `LeakageChecker` checks file access logs |

### 15.8 `Metric` (Layer 10)

| Item | Specification |
|------|---------------|
| **Responsibility** | Compute a single scalar score comparing prediction to ground truth |
| **Input types** | `prediction: ImpactPrediction`, `ground_truth: ImpactPrediction` |
| **Output type** | `float` |
| **Failure behavior** | Returns `0.0` or `NaN` on invalid input; never raises |
| **Lifecycle** | One call per (metric, run) |
| **Side effects** | None |
| **Extension rules** | New metrics implement `Metric` with `name: str` property |
| **Example** | `ImpactPrecision` computes `TP / (TP + FP)` for regenerate actions |

### 15.9 `StatisticsAnalyzer` (Layer 11)

| Item | Specification |
|------|---------------|
| **Responsibility** | Perform statistical analysis on aggregated results |
| **Input types** | `results: list[RunRecord]` (or aggregated scores) |
| **Output type** | `AnalysisReport` |
| **Failure behavior** | Returns report with warnings if assumptions violated |
| **Lifecycle** | One call per evaluation phase |
| **Side effects** | None |
| **Extension rules** | New analyzers implement `StatisticsAnalyzer` |
| **Example** | `BootstrapCI` computes 95% confidence intervals via resampling |

### 15.10 `ResultWriter` (Layer 13)

| Item | Specification |
|------|---------------|
| **Responsibility** | Persist a run record to output |
| **Input types** | `record: RunRecord` |
| **Output type** | `void` |
| **Failure behavior** | Raises `WriteError` on I/O failure |
| **Lifecycle** | Called after each run completes |
| **Side effects** | File I/O |
| **Extension rules** | New writers implement `ResultWriter` |
| **Example** | `JsonResultWriter` appends to `runs/<strategy>/<scenario>.json` |

### 15.11 `ProvenanceRecorder` (Layer 12)

| Item | Specification |
|------|---------------|
| **Responsibility** | Record every meaningful event for auditability |
| **Input types** | `event: ProvenanceEvent` |
| **Output type** | `void` |
| **Failure behavior** | Logs error but does not halt execution |
| **Lifecycle** | Called throughout the pipeline; one recorder instance per run |
| **Side effects** | File I/O (SQLite or append-only log) |
| **Extension rules** | New recorders implement `ProvenanceRecorder` |
| **Example** | `SqliteProvenanceRecorder` inserts into `provenance.db` |

---

## 16. Protocol vs ABC Guidelines

| Use-case | Use `typing.Protocol` | Use `abc.ABC` |
|----------|----------------------|---------------|
| Structural subtyping (duck typing) | Always preferred | Never |
| Shared default implementation needed | No | Yes |
| Method override detection at runtime | No | Yes (`@abstractmethod`) |
| Interface without state | Yes | Not needed |
| Interface with shared helper methods | No | Yes |

**Default choice:** `typing.Protocol`. Only use `abc.ABC` when a base class genuinely provides reusable default logic that all implementations share.

---

## 17. Controlled Django Todo Location

| Item | Path |
|------|------|
| Repository specification | `benchmark_data/controlled_repo_spec/` (YAML or JSON spec files) |
| Generated repository | `repositories/controlled_todo/` (auto-generated from spec) |

The controlled Django Todo is a synthetically generated repository that:
- Represents a simple Django Todo application with models, views, templates, URLs, tests
- Has a known, fully documented dependency graph (no unknown edges)
- Serves as the simplest test case for selective regeneration strategies
- The spec defines the exact file tree, dependencies, and semantics
- The generated repo at `repositories/controlled_todo/` is git-initialised with multiple commits

---

## 18. Architecture Validation Points

Every commit / PR touching the `src/benchmark/` package must pass:

1. **Layer import check:** No layer N module imports from layer N+1 or higher
2. **Protocol conformance:** Each strategy, backend, adapter, etc. conforms to its protocol
3. **Immutable outputs:** All data models are frozen (dataclass frozen or `@property` read-only)
4. **No private data in public code:** `strategies/` and `execution/` never import from `private_evaluation/`
5. **Lazy imports:** `KaggleQwenBackend` lazily imports torch/transformers
