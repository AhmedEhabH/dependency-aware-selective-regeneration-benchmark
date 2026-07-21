# Dependency Direction Rules

## Allowed Dependency Directions

### Core layer (`src/benchmark/core/`) imports nothing from infrastructure:
- `enums.py`, `models.py`, `exceptions.py`, `protocols.py` — no internal imports from the project
- `registry.py` — imports from `protocols.py` only
- `context.py` — imports from `models.py`, `protocols.py`

### Configuration (`src/benchmark/config/`) imports:
- `models.py` → `core/enums.py`, `core/models.py`
- `loader.py` → `models.py`, `core/exceptions.py`
- `validation.py` → `models.py`, `core/exceptions.py`

### Repository adapters (`src/benchmark/repositories/`) import:
- `base.py` → `core/protocols.py`, `core/models.py`
- `loader.py` → `base.py`, `core/exceptions.py`
- `manifest.py` → `core/models.py`
- `snapshot.py` → `core/exceptions.py`
- `workspace.py` → `core/exceptions.py`
- Must **NOT** import `graph/`, `strategies/`, `llm/`, `evaluation/`

### Scenario services (`src/benchmark/scenarios/`) import:
- `models.py` → `core/enums.py`, `core/models.py`
- `loader.py` → `models.py`, `config/models.py`
- `validator.py` → `models.py`, `core/exceptions.py`
- `sequencing.py` → `models.py`

### Graph (`src/benchmark/graph/`) imports:
- `models.py` → `core/enums.py`, `core/models.py`
- `builder.py` → `models.py`, `repositories/base.py`
- `extractors/` → `models.py`, `repositories/snapshot.py`
- `traversal.py` → `models.py`

### Strategies (`src/benchmark/strategies/`) import:
- `base.py` → `core/protocols.py`, `core/models.py`
- `registry.py` → `base.py`, `core/exceptions.py`
- Each strategy → `base.py`, `core/models.py`, `graph/models.py`, `llm/base.py`
- Must **NOT** import `evaluation/`, `statistics/`, `provenance/`, `reporting/`

### LLM backends (`src/benchmark/llm/`) import:
- `base.py` → `core/protocols.py`, `core/models.py`, `core/exceptions.py`
- `mock_backend.py` → `base.py`
- `dry_run_backend.py` → `base.py`
- `kaggle_qwen_backend.py` → `base.py` (torch/transformers imported lazily inside methods)
- Must **NOT** import `strategies/`, `execution/`, `evaluation/`

### Execution (`src/benchmark/execution/`) imports:
- `runner.py` → `core/protocols.py`, `core/models.py`, `core/exceptions.py`, `strategies/base.py`, `llm/base.py`
- `pipeline.py` → `runner.py`, `core/context.py`
- `repair.py` → `core/protocols.py`, `core/exceptions.py`
- `budgets.py` → `core/enums.py`, `core/models.py`
- `isolation.py` → `core/exceptions.py`
- Must **NOT** import `evaluation/`, `statistics/`, `reporting/`

### Validation (`src/benchmark/validation/`) imports:
- `functional.py` → `core/protocols.py`, `core/models.py`, `core/exceptions.py`
- `regression.py` → `core/protocols.py`
- `architecture.py` → `core/protocols.py`, `graph/models.py`
- `leakage.py` → `core/protocols.py`
- `file_scope.py` → `core/enums.py`
- Must **NOT** import `strategies/`, `llm/`, `evaluation/`

### Evaluation (`src/benchmark/evaluation/`) imports:
- `scoring.py` → `core/models.py`, private ground truth (via config path)
- `impact_metrics.py` → `core/models.py`, `core/protocols.py`
- `preservation_metrics.py` → `core/models.py`
- `architecture_metrics.py` → `core/models.py`, `graph/models.py`
- `efficiency_metrics.py` → `core/models.py`
- Must **NOT** import `strategies/`, `llm/`, `execution/`

### Statistics (`src/benchmark/statistics/`) imports:
- All files → `core/models.py`, `evaluation/*` (result models only)
- Must **NOT** import `strategies/`, `llm/`, `execution/`

### Provenance (`src/benchmark/provenance/`) imports:
- All files → `core/models.py`, `core/exceptions.py`
- Must **NOT** import `strategies/`, `llm/`, `execution/`, `evaluation/`

### Reporting (`src/benchmark/reporting/`) imports:
- All files → `core/models.py`, `evaluation/*` (result models), `statistics/*` (report models), `provenance/*` (records)
- Must **NOT** import `strategies/`, `llm/`, `execution/`

## Explicit Prohibitions

- No circular imports between any two packages
- No global mutable state at module level
- No singleton registries (use instantiated registries injected via constructor)
- No import-time filesystem access
- No import-time network access
- No import-time environment mutation
- No `if model_name == ...` branching in core logic
- No `if repository == ...` branching in generic execution logic
- No notebook-defined business logic (notebooks are adapters only)
- No direct strategy access to scoring or hidden-test modules
- No import of torch, transformers, or CUDA in any module outside `llm/kaggle_qwen_backend.py`
- No import of `private_evaluation/` by any module under `src/benchmark/strategies/`, `execution/`, or `llm/`
