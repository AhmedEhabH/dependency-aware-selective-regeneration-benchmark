# Extension Guide — Plugin and Registry Design — v1.0

**Phase:** 3.5 — Static Architecture Audit and Project Map  
**Date:** 2026-07-22  
**Status:** FROZEN

---

## 1. Design Principle

The benchmark core must be extensible without modification. Adding a new strategy, LLM backend, repository adapter, validator, or metric must not require changing core modules. This is achieved through:

1. **Protocol-based interfaces** (typing.Protocol) — no ABC base class coupling
2. **Explicit dependency injection** — no hidden imports or global state
3. **Factory functions** — registered via explicit configuration, not auto-discovery
4. **Instantiated registries** — not module-level singletons

## 2. Plugin Lifecycle

```
configuration
  → validated by config loader
  → factory selects implementation
  → interface implementation instantiated
  → injected into runner / pipeline
  → produces immutable result
  → result consumed by next stage
```

Configuration is the sole entry point for selecting implementations. A strategy is chosen by name in YAML; the factory maps the name to a concrete class.

## 3. Extension Points

### 3.1 Adding a New Strategy

1. Create a new Python file in `src/benchmark/strategies/`
2. Implement the `ImpactStrategy` protocol
3. Add a factory entry in `src/benchmark/strategies/registry.py`
4. Reference the strategy by name in configuration YAML

Files to modify: new strategy file + `strategies/registry.py`  
Files NOT to modify: `core/`, `execution/`, `evaluation/`

### 3.2 Adding a New LLM Backend

1. Create a new Python file in `src/benchmark/llm/`
2. Implement the `LLMBackend` protocol
3. Add a factory entry in `src/benchmark/llm/__init__.py` or factory module
4. Reference the backend by name in configuration YAML

Files to modify: new backend file + LLM factory  
Files NOT to modify: `strategies/`, `execution/`, `core/`

### 3.3 Adding a New Repository Adapter

1. Create a new Python file in `src/benchmark/repositories/`
2. Implement the `RepositoryAdapter` protocol
3. Register in `src/benchmark/repositories/__init__.py`
4. The adapter handles cloning, snapshotting, and test execution

Files to modify: new adapter file + repository factory  
Files NOT to modify: `core/`, `scenarios/`

### 3.4 Adding a New Validator

1. Create a new Python file in `src/benchmark/validation/`
2. Implement the `Validator` protocol
3. Register in configuration (validators are composed as a chain)

Files to modify: new validator file + validation chain configuration  
Files NOT to modify: `execution/`, `evaluation/`

### 3.5 Adding a New Metric

1. Create a new Python file in `src/benchmark/evaluation/`
2. Implement the `Metric` protocol
3. Register in evaluation configuration

Files to modify: new metric file + metric registry  
Files NOT to modify: `core/`, `strategies/`, `execution/`

## 4. Registry Design

```python
# src/benchmark/strategies/registry.py — NOT a global singleton

class StrategyRegistry:
    """Explicitly instantiated registry. Not a module-level singleton."""

    def __init__(self):
        self._strategies: dict[str, type[ImpactStrategy]] = {}

    def register(self, name: str, strategy_cls: type[ImpactStrategy]) -> None:
        if name in self._strategies:
            raise ValueError(f"Duplicate strategy name: {name}")
        self._strategies[name] = strategy_cls

    def create(self, name: str, **kwargs) -> ImpactStrategy:
        if name not in self._strategies:
            raise ValueError(f"Unknown strategy: {name}")
        return self._strategies[name](**kwargs)

    @property
    def available(self) -> list[str]:
        return sorted(self._strategies)
```

The registry is instantiated by the configuration loader and injected into the runner. No module-level `registry = StrategyRegistry()`.

## 5. Protocol Definitions (Skeletons)

```python
# src/benchmark/core/protocols.py

from typing import Protocol, runtime_checkable

@runtime_checkable
class ImpactStrategy(Protocol):
    def analyze_impact(
        self,
        repository: RepositorySnapshot,
        requirement_change: RequirementChange,
        artifact_universe: ArtifactUniverse,
    ) -> ImpactPrediction:
        ...

    @property
    def name(self) -> str: ...


@runtime_checkable
class LLMBackend(Protocol):
    async def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        ...


@runtime_checkable
class RepositoryAdapter(Protocol):
    def clone(self, url: str, ref: str) -> RepositorySnapshot: ...
    def checkout(self, sha: str) -> RepositorySnapshot: ...
    def run_tests(self, paths: list[str] | None = None) -> TestResult: ...


@runtime_checkable
class ScenarioProvider(Protocol):
    def get_scenario(self, scenario_id: str) -> Scenario: ...
    def list_scenarios(self, repository_id: str) -> list[Scenario]: ...


@runtime_checkable
class DependencyExtractor(Protocol):
    def build_graph(self, snapshot: RepositorySnapshot) -> DependencyGraph: ...


@runtime_checkable
class ExecutionRunner(Protocol):
    async def run_strategy(
        self,
        strategy: ImpactStrategy,
        scenario: Scenario,
    ) -> RunRecord:
        ...


@runtime_checkable
class Validator(Protocol):
    def validate(
        self,
        snapshot: RepositorySnapshot,
        result: ModificationResult,
    ) -> ValidationReport:
        ...


@runtime_checkable
class Metric(Protocol):
    @property
    def name(self) -> str: ...
    def compute(
        self,
        prediction: ImpactPrediction,
        ground_truth: GroundTruth,
    ) -> float: ...


@runtime_checkable
class StatisticsAnalyzer(Protocol):
    def analyze(self, results: list[RunRecord]) -> AnalysisReport: ...


@runtime_checkable
class ResultWriter(Protocol):
    def write_run(self, record: RunRecord) -> None: ...


@runtime_checkable
class ProvenanceRecorder(Protocol):
    def record(self, event: ProvenanceEvent) -> None: ...
```

## 6. Factory Pattern

```python
# Example factory for LLMBackend

def create_llm_backend(config: BackendConfig) -> LLMBackend:
    if config.backend_type == "mock":
        return MockLLMBackend(seed=config.seed)
    elif config.backend_type == "dry_run":
        return DryRunBackend(fixture_path=config.fixture_path)
    elif config.backend_type == "kaggle_qwen":
        return KaggleQwenBackend(
            model_path=config.model_path,
            device=config.device,
        )
    else:
        raise ValueError(f"Unknown LLM backend: {config.backend_type}")
```

## 7. Prohibited Patterns

- No `import torch` at module level in any file under `src/benchmark/core/` or `src/benchmark/strategies/`
- No `if model_name == "qwen"` branching in strategy or execution code
- No `if repo_name == "saleor"` branching in generic execution logic
- No global `registry` singleton at module level
- No `__init_subclass__` or metaclass-based auto-registration
- No `importlib`-based plugin discovery from the filesystem
- No `except Exception` without re-raising or classification
