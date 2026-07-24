# Implemented Architecture Baseline

**Audit Date:** 2026-07-24
**Branch:** `audit/canonical-project-architecture`
**Purpose:** Describe what the code currently does — not what plans claim it should do.

---

## Package/Module Boundaries (As Implemented)

### `src/benchmark/core/` — Domain Layer
- `enums.py` — 6 StrEnum classes
- `exceptions.py` — 12 exception classes with typed hierarchy
- `models.py` — 24 frozen dataclasses
- `protocols.py` — 11 runtime-checkable protocols
- `registry.py` — Generic `Registry[T]`
- `context.py` — `ExecutionContext`
- **Dependency direction:** No internal imports from other benchmark packages. ✓

### `src/benchmark/config/` — Configuration Layer
- `models.py` — 7 Pydantic v2 config models
- `loader.py` — YAML config loader
- `validation.py` — Structural validation
- **Dependency direction:** Imports from `core/` only. ✓

### `src/benchmark/repositories/` — Repository Layer
- `base.py`, `manifest.py`, `loader.py`, `snapshot.py`, `workspace.py`
- **Dependency direction:** Imports from `core/`, `config/`. Does not import `graph/`, `strategies/`, `llm/`, `evaluation/`. ✓

### `src/benchmark/scenarios/` — Scenario Layer
- `models.py`, `loader.py`, `validator.py`, `sequencing.py`
- **Dependency direction:** Imports from `core/`, `config/`. ✓

### `src/benchmark/graph/` — Graph Layer
- `models.py`, `builder.py`
- **Dependency direction:** Imports from `core/`, `repositories/`. ✓

### `src/benchmark/strategies/` — Strategy Layer
- 7 concrete strategies + `registry.py`
- **Dependency direction:** Imports from `core/`, `graph/`, `llm/`. Does NOT import `evaluation/`, `statistics/`, `provenance/`, `reporting/`. ✓

### `src/benchmark/llm/` — LLM Backend Layer
- `base.py`, `mock_backend.py`, `dry_run_backend.py`, `kaggle_qwen_backend.py`
- **Dependency direction:** Imports from `core/` only. Lazy torch/transformers. ✓

### `src/benchmark/execution/` — Execution Layer
- `budgets.py`, `state_machine.py`, `repair.py`, `isolation.py`, `runner.py`, `pipeline.py`
- **Dependency direction:** Imports from `core/`, `strategies/`, `llm/`. Does NOT import `evaluation/`, `statistics/`, `reporting/`. ✓

### `src/benchmark/evaluation/` — Evaluation Layer
- `engine.py`, `metrics.py`
- **Dependency direction:** Imports from `core/`. ✓

### `src/benchmark/comparison/` — Comparison Layer
- `ground_truth.py`, `aggregator.py`
- **Dependency direction:** Imports from `core/`. ✓

### `src/benchmark/statistics/` — Statistics Layer
- `analysis.py`, `confidence_intervals.py`, `effect_sizes.py`, `reporting.py`
- **Dependency direction:** Imports from `core/`, `evaluation/`. Does NOT import `strategies/`, `llm/`, `execution/`. ✓

### `src/benchmark/selection/` — Selection Layer
- `planner.py`
- **Dependency direction:** Imports from `core/`. ✓

### `src/benchmark/checkpoint/` — Checkpoint Layer (not in original architecture doc)
- `checkpoint.py`, `hf_sync.py`, `package.py`, `persistence.py`, `resume.py`
- **NOT documented in SOFTWARE_ARCHITECTURE.md** — added during checkpoint/resume feature
- **Deviations:** Does not appear in the 13-layer architecture. Dependency direction: imports from `core/`, `config/`, `execution/`.

---

## CLI Entry Points

| Entry Point | Location | Purpose |
|------------|----------|---------|
| Main CLI | `project/seven_arm_benchmark.py` | `--dry-run`, `--profile`, `--max-runs`, `--output-dir`, `--hf-sync`, `--resume-from-hf`, `--experiment-id` |
| Python module | `python -m src.benchmark` | Via `src/benchmark/__init__.py` (CLI not yet implemented here) |

---

## Notebook Entry Point

| Notebook | Location | Purpose |
|----------|----------|---------|
| Kaggle notebook | `project/notebooks/seven_arm_benchmark.ipynb` | Step-by-step: install deps, verify GPU, mount Qwen, clone repo, secure setup, dry-run, real run, resume, view results |

---

## Kaggle Mount Discovery

The `KaggleQwenBackend` implements mount discovery:
- Checks `/kaggle/input/qwen2-5-coder` for model files
- Uses `local_files_only=True` in transformers pipeline
- Raises informative error when called locally (not on Kaggle)
- Lazy-imports torch/transformers inside method body

---

## Strategy Construction

Strategies are constructed via `STRATEGY_CAPABILITIES_DESIGN` dictionary in `seven_arm_benchmark.py`. Each strategy declares:
- `needs_llm`: whether it requires an LLM backend
- `needs_graph`: whether it requires a dependency graph
- `graph_type`: what kind of graph to build

The `create_strategies()` function iterates profiles and strategies from config, creates the appropriate backends and graphs, and instantiates strategies.

---

## Backend Construction

Backends are constructed through:
1. `BackendFactory` registry in `src/benchmark/llm/`
2. Registered types: `mock`, `dry_run`, `kaggle_qwen`, `null`
3. Factory creates backend by name from config
4. NullLLMBackend for strategies that don't need LLM

---

## Execution Pipeline

1. `BenchmarkPipeline` receives config (profile, strategies, scenarios)
2. For each (scenario, strategy, repetition):
   a. `BenchmarkRunner` creates IsolationContext
   b. Constructs `RepositorySnapshot`, `RequirementChange`, `ArtifactUniverse` from Scenario
   c. Runs strategy via `RepairLoop` (1+2 attempt lifecycle)
   d. Produces `RunRecord` (frozen dataclass)
3. Pipeline aggregates results
4. Checkpoint written after each run

---

## Checkpoint/Resume

Implemented in `src/benchmark/checkpoint/`:
- `checkpoint.py` — CheckpointManager for local state
- `resume.py` — Resume logic (skip completed runs)
- `hf_sync.py` — HuggingFace Dataset upload/download
- `package.py` — Experiment packaging
- `persistence.py` — Snapshot/chunk management

Supports:
- `--output-dir` for local checkpoints
- `--hf-sync` for remote sync
- `--resume` for local resume
- `--resume-from-hf` for cross-session resume
- Auto-resume via `_auto_resume_temp/` (test infrastructure)

---

## HuggingFace Synchronization

Implemented in `hf_sync.py`:
- Uploads recovery files after each run
- Creates immutable chunk snapshots every 2 runs
- Final snapshot on completion
- Validates compatibility on resume (protocol version, config hash, source commit)
- Uses exponential backoff for transient failures
- Allowlist-based file upload filter

---

## Evaluation and Statistics

Evaluation pipeline:
1. `GroundTruthComparator` compares strategy predictions to expected actions
2. `EvaluationEngine` computes metrics per scenario
3. `ResultAggregator` aggregates across scenarios/repos
4. `StatisticalAnalyzer` runs tests (Mann-Whitney U, non-inferiority)
5. `ConfidenceIntervalCalculator` (bootstrap, normal, Wilson, Agresti-Coull)
6. `EffectSizeComputer` (Cohen's d, Cliff's delta)
7. Multiple comparison corrections (BH, Holm)
8. `NotebookExporter`, `PublicationTableBuilder` for output

---

## Bundle Generation

Bundle generation is manual:
1. Copy `seven_arm_benchmark.py` → `kaggle_upload/code/`
2. Copy `src/benchmark/` → `kaggle_upload/code/src/`
3. Copy configs → `kaggle_upload/code/configs/`
4. Copy `pyproject.toml`, `requirements-kaggle.txt` → `kaggle_upload/code/`
5. Copy `benchmark_data/` → `kaggle_upload/data/`
6. Copy notebook → `kaggle_upload/notebooks/`

**No automated build script exists.** The `scripts/` directory is empty.

---

## Known Deviations from Existing Architecture Documentation

| Deviation | Documented In | Implemented As | Impact |
|-----------|--------------|---------------|--------|
| `checkpoint/` package not in 13-layer architecture | SOFTWARE_ARCHITECTURE.md (13 layers) | `checkpoint/` exists as 14th package | Architecture doc is incomplete |
| `comparison/` package not in architecture | SOFTWARE_ARCHITECTURE.md | `comparison/` exists with GroundTruthComparator, ResultAggregator | Architecture doc is incomplete |
| `selection/` package not in architecture | SOFTWARE_ARCHITECTURE.md | `selection/` exists with ArtifactSelector, RegenerationPlanner | Architecture doc is incomplete |
| No automated bundle script | PROJECT_STRUCTURE_MAP.md proposes `scripts/build_upload_bundle.py` | `scripts/` is empty | Bundle regeneration is manual and error-prone |
| `kaggle_upload/data/` empty | PROJECT_STRUCTURE_MAP.md lists data bundle as proposed | Bundled data resides only in outer `<parent>/kaggle_upload/data/` | Deployment failure if inner bundle used |
| `private_evaluation/` not created | PUBLIC_PRIVATE_DATA_BOUNDARY.md proposes it | Directory does not exist | No concern yet (no private evaluation data) |
| `repositories/` not created | PROJECT_STRUCTURE_MAP.md proposes cloned repos | Directory does not exist | Not needed until repo cloning implemented |
| `runs/` not created | PROJECT_STRUCTURE_MAP.md proposes it | Directory does not exist | No runs executed yet (after smoke) |
| `release/` not created | PROJECT_STRUCTURE_MAP.md proposes it | Directory does not exist | Not yet in release phase |
| Bundle contains `.git/` and caches | Not documented | Present in `project/kaggle_upload/code/` | Bloated bundle, security concern |
