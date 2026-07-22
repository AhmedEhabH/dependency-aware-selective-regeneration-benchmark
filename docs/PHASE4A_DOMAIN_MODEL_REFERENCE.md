# Phase 4A — Domain Model Reference

**Protocol Version:** 1.0 (FROZEN)
**Date:** 2026-07-22
**Status:** COMPLETE

---

## 1. Enums

All enums use `StrEnum` (Python 3.11+ `enum.StrEnum`) for stable string values suitable for JSON/YAML serialization.

### ActionKind

| Member | String Value |
|--------|-------------|
| `regenerate` | `"regenerate"` |
| `preserve` | `"preserve"` |
| `validate_only` | `"validate_only"` |
| `human_review` | `"human_review"` |

### ArtifactType

| Member | String Value |
|--------|-------------|
| `requirement` | `"requirement"` |
| `source` | `"source"` |
| `test` | `"test"` |
| `migration` | `"migration"` |
| `api_schema` | `"api_schema"` |
| `documentation` | `"documentation"` |
| `configuration` | `"configuration"` |
| `architecture` | `"architecture"` |
| `deployment` | `"deployment"` |

### BlastRadius

| Member | String Value |
|--------|-------------|
| `localized` | `"localized"` |
| `moderate` | `"moderate"` |
| `cross_cutting` | `"cross_cutting"` |

### RunStatus

| Member | String Value |
|--------|-------------|
| `prepared` | `"prepared"` |
| `running` | `"running"` |
| `succeeded` | `"succeeded"` |
| `failed` | `"failed"` |
| `timed_out` | `"timed_out"` |
| `cancelled` | `"cancelled"` |

### FailureKind

| Member | String Value |
|--------|-------------|
| `infrastructure` | `"infrastructure"` |
| `model_output` | `"model_output"` |
| `build` | `"build"` |
| `changed_requirement` | `"changed_requirement"` |
| `regression` | `"regression"` |
| `architecture` | `"architecture"` |
| `timeout` | `"timeout"` |
| `harness_defect` | `"harness_defect"` |

### EvidenceTier

| Member | String Value |
|--------|-------------|
| `engineering_validation` | `"engineering_validation"` |
| `smoke` | `"smoke"` |
| `pilot` | `"pilot"` |
| `confirmatory` | `"confirmatory"` |
| `exploratory` | `"exploratory"` |
| `legacy_pilot` | `"legacy_pilot"` |

---

## 2. Domain Models

### Requirement and Artifact Models

#### `RequirementChange`
- **Kind:** frozen dataclass
- **Fields:** `before: str`, `after: str`, `acceptance_criteria: tuple[str, ...]`
- **Validation:** `before` and `after` must not be empty.

#### `ArtifactRef`
- **Kind:** frozen dataclass
- **Fields:** `path: str`, `artifact_type: ArtifactType`
- **Validation:** `path` must not be empty.

#### `ArtifactUniverse`
- **Kind:** frozen dataclass
- **Fields:** `artifacts: tuple[ArtifactRef, ...]`
- **Validation:** Rejects duplicate `path` values.
- **Methods:** `contains(path: str) -> bool`

#### `ArchitectureConstraint`
- **Kind:** frozen dataclass
- **Fields:** `description: str`
- **Validation:** `description` must not be empty.

#### `AcceptanceCriterion`
- **Kind:** frozen dataclass
- **Fields:** `description: str`
- **Validation:** `description` must not be empty.

### Repository and Scenario Models

#### `RepositoryIdentity`
- **Kind:** frozen dataclass
- **Fields:** `name: str`, `url: str`

#### `RepositorySnapshot`
- **Kind:** frozen dataclass
- **Fields:** `identity: RepositoryIdentity`, `commit_sha: str`, `path: str`

#### `Scenario`
- **Kind:** frozen dataclass
- **Fields:** `scenario_id`, `repository`, `change_type`, `blast_radius`, `requirement_before`, `requirement_after`, `rationale`, `acceptance_criteria`, `expected_affected_artifacts`, `expected_actions`, `architecture_constraints`, `hidden_tests`

#### `ScenarioSequence`
- **Kind:** frozen dataclass
- **Validation:** Rejects duplicate `scenario_id` values.

### Impact Models

#### `SupportingEvidence`
- **Kind:** frozen dataclass
- **Fields:** `description: str`, `source: str`

#### `ImpactDecision`
- **Kind:** frozen dataclass
- **Fields:** `artifact: ArtifactRef`, `action: ActionKind`, `rationale: str`, `supporting_evidence: tuple[SupportingEvidence, ...]`

#### `ImpactPrediction`
- **Kind:** frozen dataclass
- **Fields:** `decisions: tuple[ImpactDecision, ...]`, `errors: tuple[str, ...]`

### Execution Models

#### `Budget`
- **Kind:** frozen dataclass
- **Fields:** `max_iterations: int = 3`, `max_tokens: int = 0`, `timeout_seconds: int = 0`
- **Validation:** `max_iterations >= 1`, all fields >= 0.
- **Iteration semantics:** `max_iterations` is the total number of attempts including the initial generation. Default `3` = 1 initial generation + up to 2 LLM repair attempts (aligned with §4 of `EXECUTION_AND_FAILURE_POLICY.md`).

#### `TokenUsage`
- **Kind:** frozen dataclass
- **Fields:** `prompt_tokens`, `completion_tokens`, `total_tokens`

#### `LLMResponse`
- **Kind:** frozen dataclass
- **Fields:** `text: str`, `token_usage: TokenUsage`, `finish_reason: str`

#### `ExecutionContext`
- **Kind:** frozen dataclass with `update_budget()` and `update_random_seed()` setter methods for controlled mutation during the execution pipeline.
- **Location:** `core/context.py`
- **Fields:** `protocol_version`, `run_id`, `repository_identity`, `scenario_id`, `strategy_name`, `backend_name`, `working_directory`, `public_data_paths`, `private_evaluation_access: bool = False`, `random_seed`, `budget`, `start_timestamp`, `evidence_tier`, `publication_eligible: bool = False`
- **Immutable fields (all except `budget` and `random_seed`):** `protocol_version`, `run_id`, `repository_identity`, `scenario_id`, `strategy_name`, `backend_name`, `working_directory`, `public_data_paths`, `private_evaluation_access`, `start_timestamp`, `evidence_tier`, `publication_eligible`. Any attempt to set these after construction raises `AttributeError`.
- **Mutable fields only via methods:** `update_budget(budget)` and `update_random_seed(seed)`.
- **Public/Private:** `private_evaluation_access` defaults to `False`; frozen after construction so strategies cannot enable it.

#### `RunIdentity`
- **Kind:** frozen dataclass
- **Fields:** `run_id`, `protocol_version`, `repository_commit_sha`, `scenario_id`, `strategy_name`, `timestamp`

#### `RunRecord`
- **Kind:** frozen dataclass
- **Fields:** `identity: RunIdentity`, `status: RunStatus`, `prediction`, `failures`, `token_usage`, `duration_seconds`, `schema_version`

#### `FailureRecord`
- **Kind:** frozen dataclass
- **Fields:** `failure_kind: FailureKind`, `message: str`, `details: str`

### Validation and Result Models

#### `ValidationCheck`
- **Kind:** frozen dataclass
- **Fields:** `name: str`, `passed: bool`, `message: str`

#### `ValidationReport`
- **Kind:** frozen dataclass
- **Fields:** `run_identity`, `checks`, `passed`, `schema_version`

#### `MetricValue`
- **Kind:** frozen dataclass
- **Fields:** `name: str`, `value: float | None`, `unit: str`
- **Undefined metrics:** `value` can be `None` explicitly (not converted to zero).

#### `AnalysisReport`
- **Kind:** frozen dataclass
- **Fields:** `title`, `metrics`, `summary`, `schema_version`

### Graph and Provenance Models

#### `DependencyGraph`
- **Kind:** frozen dataclass
- **Fields:** `nodes: tuple[str, ...]`, `edges: tuple[tuple[str, str], ...]`, `metadata: dict`

#### `ProvenanceEvent`
- **Kind:** frozen dataclass
- **Fields:** `timestamp`, `layer`, `action`, `input_hash`, `output_hash`, `metadata`

### Schema Versions
- `MODEL_SCHEMA_VERSION = "1.0"` — applied to `RunRecord`, `ValidationReport`, `AnalysisReport`.

---

## 3. Exception Hierarchy

```
BenchmarkError (base)
├── ConfigurationError
├── ValidationError
├── RegistryError
│   ├── DuplicateRegistrationError
│   └── UnknownRegistrationError
├── RepositoryError
├── ScenarioError
├── ModelBackendError
├── BudgetExceededError
├── ProtocolViolationError
└── SerializationError
```

All exceptions carry an optional `context: dict` for structured information.

---

## 4. Protocol Interfaces

All protocols are `typing.Protocol` decorated with `@runtime_checkable`.

| Protocol | Key Method(s) | Input | Output |
|----------|---------------|-------|--------|
| `ImpactStrategy` | `analyze_impact(repo, change, universe)` | RepositorySnapshot, RequirementChange, ArtifactUniverse | ImpactPrediction |
| `LLMBackend` | `async generate(prompt, temperature, max_tokens)` | str, float, int | LLMResponse |
| `RepositoryAdapter` | `clone(url, ref)`, `checkout(sha)`, `run_tests(paths)` | str, str, list[str] | RepositorySnapshot, None, dict |
| `ScenarioProvider` | `get_scenario(id)`, `list_scenarios(repo_id)` | str, str\|None | Scenario, list[Scenario] |
| `DependencyExtractor` | `build_graph(snapshot)` | RepositorySnapshot | DependencyGraph |
| `ExecutionRunner` | `run_strategy(strategy, scenario)` | ImpactStrategy, Scenario | RunRecord |
| `Validator` | `validate(snapshot, result)` | RepositorySnapshot, RunRecord | ValidationReport |
| `Metric` | `compute(prediction, ground_truth)` | ImpactPrediction, ImpactPrediction | float |
| `StatisticsAnalyzer` | `analyze(results)` | list[RunRecord] | AnalysisReport |
| `ResultWriter` | `write_run(record)` | RunRecord | None |
| `ProvenanceRecorder` | `record(event)` | ProvenanceEvent | None |

---

## 5. Registry

The `Registry[T]` is a generic, explicitly instantiated registry.

- **Registration:** `register(name, entry)` — raises `DuplicateRegistrationError` if name exists.
- **Lookup:** `create(name, **kwargs)` — raises `UnknownRegistrationError` if not found.
- **Inspection:** `get(name)`, `list_names()`, `__contains__`, `__len__`
- **Freeze:** `freeze()` — prevents further registrations; raises `RuntimeError`.
- **No global singleton:** Each registry instance is independent.

---

## 6. Configuration Models (Pydantic v2)

All config models are `pydantic.BaseModel` with `frozen=True`.

| Model | Description |
|-------|-------------|
| `BenchmarkConfig` | Top-level: strategies, backends, repos, execution, output |
| `StrategyConfig` | Strategy name, params, LLM backend reference |
| `BackendConfig` | Backend name, kind (mock|dry_run|kaggle_qwen), params |
| `RepositoryConfig` | Repository name, URL, ref |
| `ScenarioSelectionConfig` | Filters for selecting scenarios |
| `ExecutionConfig` | Budget, seed, evidence tier |
| `OutputConfig` | Output directory, format, provenance toggle |

### Validation Rules
- Kaggle backend (`kaggle_qwen`) cannot be selected in `local` execution mode.
- Strategy names must not be empty.
- Execution budgets must be positive.

---

## 7. Public/Private Data Restrictions

- `ExecutionContext.private_evaluation_access` defaults to `False`.
- `ExecutionContext.public_data_paths` contains paths visible to strategies.
- Private evaluation paths (hidden tests, ground truth) must never be passed as `public_data_paths`.
- Strategies receive only public data through `ImpactStrategy.analyze_impact`.

---

## 8. Serialization Rules

- All enums serialize as their string values (via `StrEnum`)
- All frozen dataclasses support `==` and `hash()` for value equality
- All models can be serialized via YAML or JSON by converting to dicts
- Timestamps use UTC timezone-aware `datetime` objects
