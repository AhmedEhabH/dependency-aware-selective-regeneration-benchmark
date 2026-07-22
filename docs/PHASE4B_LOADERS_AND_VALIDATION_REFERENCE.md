# Phase 4B — Loaders and Validation Reference

## Production Files

### `src/benchmark/repositories/` (6 files)

| File | Classes/Functions | Description |
|------|------------------|-------------|
| `__init__.py` | — | Public exports |
| `base.py` | `RepositoryLoaderBase` | Abstract base with `resolve_identity`, `resolve_snapshot` |
| `manifest.py` | `RepositoryManifest`, `RepositoryVersionEntry`, `RepositoryProfile`, `ManifestCollection` | Frozen dataclass models for manifest data |
| `loader.py` | `RepositoryLoader` | YAML loading from `manifests/` and `repository_profiles/`, builds `ManifestCollection` |
| `snapshot.py` | `SnapshotMetadata`, `create_snapshot_metadata()`, `validate_snapshot()` | Snapshot metadata creation and validation |
| `workspace.py` | `WorkspacePath`, `validate_workspace_path()`, `check_isolation()` | Workspace isolation safety checks |

### `src/benchmark/scenarios/` (5 files)

| File | Classes/Functions | Description |
|------|------------------|-------------|
| `__init__.py` | — | Public exports |
| `models.py` | `ScenarioModel`, `_parse_blast_radius()`, `_parse_artifact_ref()`, `_parse_action_kind()` | YAML-mapped dataclass with `to_core_scenario()` conversion, handles both standard and Saleor expected_actions formats |
| `loader.py` | `ScenarioLoader` | Loads scenario YAML files, supports `load_all()`, `load_by_repository()` |
| `validator.py` | `ScenarioValidator` | Validates required fields and duplicate expected actions |
| `sequencing.py` | `ScenarioSequencer` | Orders scenarios by blast_radius (localized → moderate → cross_cutting) |

## Dependency Rules (per `docs/DEPENDENCY_RULES.md`)

- `repositories/` imports: `core/protocols.py`, `core/models.py`, `core/exceptions.py`
- `scenarios/` imports: `core/enums.py`, `core/models.py`, `config/models.py`, `core/exceptions.py`
- Neither package imports `graph/`, `strategies/`, `llm/`, `evaluation/`, or `config/`

## Test Files (14 files)

### Unit tests (10)
- `tests/unit/test_repositories_manifest.py` — 15 tests
- `tests/unit/test_repositories_loader.py` — 8 tests
- `tests/unit/test_repositories_snapshot.py` — 12 tests
- `tests/unit/test_repositories_workspace.py` — 9 tests
- `tests/unit/test_scenarios_models.py` — 11 tests
- `tests/unit/test_scenarios_loader.py` — 9 tests
- `tests/unit/test_scenarios_validator.py` — 7 tests
- `tests/unit/test_scenarios_sequencing.py` — 5 tests

### Integration tests (2)
- `tests/integration/test_repositories_integration.py` — 6 tests (against real benchmark_data)
- `tests/integration/test_scenarios_integration.py` — 5 tests (against real benchmark_data)

### Contract tests (1)
- `tests/contract/test_loaders_contract.py` — 4 tests

### Existing Phase 4A tests (retained)
- All 111 original Phase 4A tests continue to pass

## Scenario YAML Formats Supported

### Standard format (todo, djangocms):
```yaml
expected_actions:
  "path:Symbol": modify
  "path:Symbol2": create
```

### Action-grouped format (saleor):
```yaml
expected_actions:
  modify:
    - path1.py
    - path2.py
  create:
    - path3.py
```

Both formats are normalized to `{path: action}` internally.

## Validation Results

### Unit/contract tests: 192 passed
### Integration tests (real data): 11 passed
### Total: 206 passed
### Ruff: All checks passed
### mypy --strict: Success, no issues found
### pip check: No package conflicts from project dependencies

## Key Design Decisions

1. Duplicate expected actions are deduplicated in `to_core_scenario()` to handle real benchmark data
2. Repository profiles support multiple YAML schemas (todo vs saleor naming conventions)
3. Scenario validation is strict for required fields but tolerates duplicates via deduplication
4. Snapshot validation reports all issues (does not raise) for composability
5. Workspace isolation uses `Path.resolve()` for accurate comparison
