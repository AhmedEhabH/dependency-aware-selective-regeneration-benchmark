# Phase 4 Implementation Blueprint

Split into **6 milestones**:

---

## Phase 4A — Domain Models and Contracts

- **Files to create:** about 12
  - `src/benchmark/core/__init__.py`, `models.py`, `enums.py`, `exceptions.py`, `protocols.py`, `registry.py`, `context.py`
  - `src/benchmark/config/__init__.py`, `models.py`, `loader.py`, `validation.py`
  - `tests/test_core_models.py`, `tests/test_core_protocols.py`, `tests/test_config_models.py`
- **Classes and interfaces:** `BenchmarkConfig`, `RunRecord`, `ImpactStrategy` (Protocol), `Budget`, `Scenario`, `TaskOutcome` enum, `BenchmarkError`, `Registry`, `ExecutionContext`
- **Tests:** model immutability, protocol structural typing, config parsing
- **Acceptance criteria:** all models are frozen/immutable dataclasses; protocols are typed; config models use Pydantic; enums are StrEnum; exceptions are typed; no external dependencies except stdlib + pydantic
- **Dependencies:** none
- **Forbidden work:** no infrastructure loaders, no LLM code, no strategy logic, no evaluation
- **Estimated complexity:** medium
- **Completion status:** PENDING

---

## Phase 4B — Loaders and Validation

- **Files to create:** about 16
  - `src/benchmark/repositories/__init__.py`, `base.py`, `loader.py`, `manifest.py`, `snapshot.py`, `workspace.py`
  - `src/benchmark/scenarios/__init__.py`, `models.py`, `loader.py`, `validator.py`, `sequencing.py`
  - Tests for each loader
- **Classes and interfaces:** `RepositoryLoader`, `Manifest`, `Snapshot`, `Workspace`, `ScenarioModel`, `ScenarioLoader`, `ScenarioValidator`, `ScenarioSequencer`
- **Tests:** manifest YAML loading, scenario YAML loading, config validation rejects bad configs, snapshot creates immutable checkout
- **Acceptance criteria:** manifests load from YAML; scenarios load from YAML; validation rejects invalid configs; snapshot creates immutable checkout
- **Dependencies:** Phase 4A, PyYAML
- **Forbidden work:** no LLM backends, no execution pipeline, no strategy code
- **Estimated complexity:** medium
- **Completion status:** PENDING

---

## Phase 4C — Model Backends

- **Files to create:** about 5
  - `src/benchmark/llm/__init__.py`, `base.py`, `mock_backend.py`, `dry_run_backend.py`, `kaggle_qwen_backend.py` (skeleton only)
- **Classes and interfaces:** `LLMBackend` (Protocol), `MockLLMBackend`, `DryRunLLMBackend`, `KaggleQwenBackend`
- **Tests:** mock backend deterministic output; dry-run backend fixture loading; import test that local import does NOT require torch
- **Acceptance criteria:** mock backend returns fixture responses; dry-run loads from files; kaggle_qwen_backend can be imported locally without torch error (lazy imports)
- **Dependencies:** Phase 4A
- **Forbidden work:** no execution pipeline, no strategy implementation, no evaluation
- **Estimated complexity:** medium
- **Completion status:** PENDING

---

## Phase 4D — Execution Core

- **Files to create:** about 8
  - `src/benchmark/execution/__init__.py`, `runner.py`, `pipeline.py`, `repair.py`, `budgets.py`, `isolation.py`
  - Tests for pipeline, budget enforcement, isolation
- **Classes and interfaces:** `BenchmarkRunner`, `BenchmarkPipeline`, `RepairLoop`, `BudgetManager`, `IsolationContext`
- **Tests:** pipeline processes scenario through strategy; repair loop respects budget; isolation prevents cross-run contamination; run records are immutable
- **Acceptance criteria:** pipeline processes scenario through strategy; repair loop respects budget; isolation prevents cross-run contamination; run records are immutable
- **Dependencies:** Phase 4A, 4B, 4C
- **Forbidden work:** no evaluation logic, no statistics, no provenance reporting
- **Estimated complexity:** high
- **Completion status:** PENDING

---

## Phase 4E — Impact Strategies

- **Files to create:** about 8
  - `src/benchmark/strategies/__init__.py`, `registry.py`, `validation.py`
  - `src/benchmark/graph/__init__.py`, `models.py`, `builder.py`
  - `src/benchmark/selection/__init__.py`, `planner.py`
  - Associated tests
- **Classes and interfaces:** `ImpactStrategy` concrete implementations (monolithic, agent, selective, compiled_ai, delta_mcp, incr_rtl, code_plan), `StrategyRegistry`, `StrategyValidator`, `DependencyGraph`, `GraphBuilder`, `ArtifactSelector`, `RegenerationPlanner`
- **Tests:** Strategy conformance to ImpactStrategy protocol; graph construction and traversal; artifact selection correctness; regeneration plan ordering; strategy registry lifecycle
- **Acceptance criteria:** All 7 strategies implement the ImpactStrategy protocol; dependency graph builds correctly from scenarios; artifact selection returns correct impacted files; regeneration plan follows correct ordering; strategy registry supports freeze/lookup; strategy validation rejects invalid configurations.
- **Dependencies:** Phase 4D execution core
- **Forbidden work:** no evaluation metrics, no statistical analysis, no scoring, no result comparison, no reporting
- **Estimated complexity:** high
- **Completion status:** PENDING

---

## Phase 4F — Evaluation Engine

- **Files to create:** about 10
  - `src/benchmark/evaluation/__init__.py`, `engine.py`, `metrics.py`
  - `src/benchmark/comparison/__init__.py`, `ground_truth.py`, `aggregator.py`
  - `src/benchmark/statistics/__init__.py`, `analysis.py`, `reporting.py`
  - Associated tests
- **Classes and interfaces:** `EvaluationEngine`, `MetricComputer`, `GroundTruthComparator`, `ResultAggregator`, `StatisticalAnalyzer`, `ConfidenceIntervalCalculator`, `EffectSizeComputer`, `NotebookExporter`, `PublicationTableBuilder`
- **Tests:** Metric computation matches ground truth; comparison produces correct pass/fail; aggregation handles partial results; statistical analysis produces valid confidence intervals; effect sizes computed correctly; notebook export produces valid JSON; publication tables format correctly
- **Acceptance criteria:** Evaluation engine processes run records; all primary and secondary metrics computed; ground truth comparison matches expectations; results aggregated across scenarios and repositories; statistical analysis produces confidence intervals and effect sizes; data exported in notebook-ready format; publication tables generated correctly.
- **Dependencies:** Phase 4E impact strategies
- **Forbidden work:** no strategy changes, no execution changes, no graph modifications
- **Estimated complexity:** high
- **Completion status:** PENDING
