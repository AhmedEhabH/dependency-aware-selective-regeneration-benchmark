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

## Phase 4E — Provenance and Result Storage

- **Files to create:** about 6
  - `src/benchmark/provenance/__init__.py`, `models.py`, `recorder.py`, `hashing.py`
  - `src/benchmark/reporting/__init__.py`, `raw_results.py`
  - Associated tests
- **Classes and interfaces:** `ProvenanceRecord`, `ProvenanceRecorder`, `ContentHasher`, `RawResultWriter`
- **Tests:** hashing stability; atomic JSONL writes; run ID uniqueness
- **Acceptance criteria:** each run has unique ID; record hashes are deterministic; JSONL writes are atomic; output manifests validate
- **Dependencies:** Phase 4A
- **Forbidden work:** no strategy changes, no evaluation logic, no execution changes
- **Estimated complexity:** low
- **Completion status:** PENDING

---

## Phase 4F — Architecture and Contract Tests

- **Files to create:** about 8
  - Import boundary tests (verify layer isolation)
  - Plugin contract tests (verify each strategy implements `ImpactStrategy`)
  - Mock execution tests (full pipeline with mocks)
  - Leakage boundary tests (verify no private imports leak)
  - Deterministic serialization tests
- **Tests:** import boundary, plugin contract, mock execution, leakage boundary, deterministic serialization
- **Acceptance criteria:** all architecture tests pass; no circular imports; no private module imported by strategy modules; deterministic output verified
- **Dependencies:** Phases 4A–4E complete
- **Forbidden work:** no new production code; test-only milestone
- **Estimated complexity:** medium
- **Completion status:** PENDING
