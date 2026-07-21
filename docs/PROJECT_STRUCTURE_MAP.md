# Project Structure Map — Dependency-Aware Selective Regeneration Benchmark

**Phase:** 3.5 — Static Architecture Audit and Project Map
**Date:** 2026-07-22
**Status:** FROZEN

---

## 1. Complete Directory Tree

```
project/
├── .git/                          # Git repository (existing)
├── .gitignore                     # Ignore rules (existing)
├── .gitattributes                 # Git attributes (existing)
├── environment.yml                # Conda environment spec (existing)
├── requirements-dev.txt           # Dev dependencies (existing)
├── requirements-kaggle.txt        # Kaggle-specific deps (existing)
├── requirements-lock.txt          # Locked deps (existing)
├── pyproject.toml                 # NEW — proposed Project metadata, tool config, package build
├── SYSTEM_STATE.md                # Phase tracking, task list (existing)
├── TODO.md                        # Task items (existing)
├── DECISION_LOG.md                # Architecture decisions (existing)
├── PROTOCOL_VERSION.md            # Protocol version tracking (existing)
│
├── docs/                          # Frozen design documentation (8 existing + 8 Phase 3.5)
│   ├── FINAL_RESEARCH_PROTOCOL.md
│   ├── EXECUTION_AND_FAILURE_POLICY.md
│   ├── GROUND_TRUTH_PROTOCOL.md
│   ├── SCENARIO_TAXONOMY.md
│   ├── STATISTICAL_ANALYSIS_PLAN.md
│   ├── REPRODUCIBILITY_PROTOCOL.md
│   ├── RESEARCHER_DECISIONS_DA_AC.md
│   ├── LEAKAGE_PREVENTION_PROTOCOL.md
│   ├── PUBLIC_PRIVATE_DATA_BOUNDARY.md       (Phase 3.5)
│   ├── PROJECT_ROOT_AND_PATH_POLICY.md       (Phase 3.5)
│   ├── PROJECT_STRUCTURE_MAP.md              (Phase 3.5) ← this file
│   ├── SOFTWARE_ARCHITECTURE.md              (Phase 3.5)
│   ├── DEPENDENCY_RULES.md                   (Phase 3.5)
│   ├── EXTENSION_GUIDE.md                    (Phase 3.5)
│   ├── PHASE4_IMPLEMENTATION_BLUEPRINT.md    (Phase 3.5)
│   └── ARCHITECTURE_VALIDATION_PLAN.md       (Phase 3.5)
│
├── benchmark_data/                # Input data (existing + proposed additions)
│   ├── manifests/                 # Repository manifests, version pins
│   ├── repository_profiles/       # Architecture descriptions per repo
│   ├── scenarios/                 # Scenario YAML definitions
│   ├── controlled_repo_spec/      # PROPOSED — Synthetic Django Todo spec
│   ├── public_tests/              # PROPOSED — Tests visible to strategies (Phase 4)
│   ├── annotations/               # PROPOSED — Public annotations (Phase 6)
│   ├── graph_specs/               # PROPOSED — Pre-computed graph specs (Phase 6)
│   └── README.md                  # PROPOSED — Data directory documentation (Phase 9)
│
├── private_evaluation/            # PROPOSED — Data never visible to strategies (Phase 6)
│   ├── hidden_tests/              # Held-back tests for final scoring
│   ├── ground_truth/              # Expected action labels
│   └── README.md                  # Access control documentation
│
├── src/
│   └── benchmark/
│       ├── __init__.py            # Package init (existing)
│       ├── cli.py                 # PROPOSED — CLI entry point
│       ├── core/                  # PROPOSED — Layer 1: domain models, protocols, enums
│       ├── config/                # PROPOSED — Layer 2: config models, loader, validation
│       ├── repositories/          # PROPOSED — Layer 3: repository adapters
│       ├── scenarios/             # PROPOSED — Layer 4: scenario services
│       ├── graph/                 # PROPOSED — Layer 5: dependency graph, extractors
│       ├── strategies/            # PROPOSED — Layer 6: strategy plugins
│       ├── llm/                   # PROPOSED — Layer 7: LLM backends
│       ├── execution/             # PROPOSED — Layer 8: runner, pipeline, repair
│       ├── validation/            # PROPOSED — Layer 9: validators
│       ├── evaluation/            # PROPOSED — Layer 10: metrics, scoring
│       ├── statistics/            # PROPOSED — Layer 11: statistical analysis
│       ├── provenance/            # PROPOSED — Layer 12: audit trail, hashing
│       ├── reporting/             # PROPOSED — Layer 13: output formatting
│       └── utils/                 # PROPOSED — Shared utilities (logging, file I/O)
│
├── tests/                         # Test suite (existing + proposed)
│   ├── unit/                      # PROPOSED — Unit tests (per module)
│   ├── contract/                  # PROPOSED — Protocol conformance tests
│   ├── integration/               # PROPOSED — Cross-module integration tests
│   ├── architecture/              # PROPOSED — Layer dependency, import checks
│   ├── fixtures/                  # PROPOSED — Test fixtures (mock repos, scenarios)
│   └── conftest.py                # Pytest configuration (existing)
│
├── configs/                       # PROPOSED — Execution configuration profiles (Phase 4)
│   ├── smoke.yaml                 # Quick smoke test config
│   ├── pilot.yaml                 # Pilot study config
│   └── research.yaml              # Full research run config
│
├── scripts/                       # Utility scripts (existing + proposed)
│   ├── validate_protocol.py       # PROPOSED — Validate protocol compliance
│   ├── validate_scenarios.py      # PROPOSED — Validate scenario definitions
│   ├── validate_manifests.py      # PROPOSED — Validate repository manifests
│   ├── build_upload_bundle.py     # PROPOSED — Build Kaggle submission bundle
│   └── audit_leakage.py           # PROPOSED — Audit for data leakage
│
├── notebooks/                     # Jupyter notebooks
│   ├── local/                     # PROPOSED — Notebooks for local analysis
│   ├── kaggle/                    # PROPOSED — Kaggle kernel notebooks
│   └── README.md                  # Notebook usage guide
│
├── reports/                       # Generated reports (existing)
│
├── runs/                          # PROPOSED — Generated run output directory
│
├── kaggle_upload/                 # PROPOSED — Kaggle submission package (Phase 9)
│   ├── code/                      # Kaggle-compatible source bundle
│   └── data/                      # Kaggle-compatible data bundle
│
├── repositories/                  # PROPOSED — Cloned / generated repositories
│   └── controlled_todo/           # Synthetic Django Todo repo
│
└── release/                       # PROPOSED — Final release build (Phase 9)
```

---

## 2. Top-Level Directory Tables

### 2.1 Root Files

| File | Responsibility | Version Controlled | Phase Created |
|------|---------------|-------------------|---------------|
| `.gitignore` | Ignore patterns for generated files, caches, secrets | Yes | Phase 0 |
| `.gitattributes` | Git LFS, line-ending rules | Yes | Phase 0 |
| `environment.yml` | Conda environment for reproducibility | Yes | Phase 0 |
| `requirements-dev.txt` | Local development dependencies | Yes | Phase 0 |
| `requirements-kaggle.txt` | Kaggle-specific subset of deps | Yes | Phase 0 |
| `requirements-lock.txt` | Pinned transitive deps | Yes | Phase 0 |
| `pyproject.toml` | Package metadata, tool config (ruff, mypy, pytest) | Yes | Phase 4 |
| `SYSTEM_STATE.md` | Phase tracking, completed work, current task | Yes | Phase 0 |
| `TODO.md` | Remaining tasks, priorities | Yes | Phase 0 |
| `DECISION_LOG.md` | Architecture decision records | Yes | Phase 0 |
| `PROTOCOL_VERSION.md` | Protocol version tracking and changelog | Yes | Phase 2B |

### 2.2 `docs/`

| Directory | Responsibility | Allowed Content | Forbidden Content | Public/Private | Version Controlled | Local/Kaggle/Shared | Phase Created | May Import From |
|-----------|---------------|----------------|-------------------|---------------|-------------------|---------------------|---------------|-----------------|
| `docs/` | Frozen design documentation | Markdown files only | Generated content, code, data | Public | Yes | Shared | Phase 0 | N/A |

### 2.3 `benchmark_data/`

| Directory | Responsibility | Allowed Content | Forbidden Content | Public/Private | Version Controlled | Local/Kaggle/Shared | Phase Created | May Import From |
|-----------|---------------|----------------|-------------------|---------------|-------------------|---------------------|---------------|-----------------|
| `benchmark_data/` | Public benchmark input data | YAML, JSON, markdown, Python | Private ground truth, hidden tests | Public | Yes | Shared | Phase 2B | N/A |
| `benchmark_data/manifests/` | Repository manifests and version pins | `repositories.yaml`, `repository_versions.yaml` | Repo contents | Public | Yes | Shared | Phase 3 | N/A |
| `benchmark_data/repository_profiles/` | Architecture descriptions per repo | `todo.yaml`, `djangocms.yaml`, `saleor.yaml` | Private ground truth | Public | Yes | Shared | Phase 3 | N/A |
| `benchmark_data/scenarios/` | Scenario definitions | Scenario YAMLs (24 total) | Ground truth actions | Public | Yes | Shared | Phase 3 | N/A |
| `benchmark_data/controlled_repo_spec/` | Synthetic Django Todo spec (proposed) | YAML/JSON spec files | Generated repo | Public | Yes | Shared | Phase 4 | N/A |
| `benchmark_data/public_tests/` | Tests visible to strategies (proposed) | Test files | Hidden tests | Public | Yes | Shared | Phase 4 | N/A |
| `benchmark_data/annotations/` | Public annotations (proposed) | Annotation metadata | Private adjudication | Public | Yes | Shared | Phase 6 | N/A |
| `benchmark_data/graph_specs/` | Pre-computed graph specs (proposed) | Graph JSON/YAML | Ground truth | Public | Yes | Shared | Phase 6 | N/A |

### 2.4 `private_evaluation/`

| Directory | Responsibility | Allowed Content | Forbidden Content | Public/Private | Version Controlled | Local/Kaggle/Shared | Phase Created | May Import From |
|-----------|---------------|----------------|-------------------|---------------|-------------------|---------------------|---------------|-----------------|
| `private_evaluation/` | Data never visible to strategies | Hidden tests, ground truth, scoring | Code that strategies could read | Private | Yes (git-crypt or access-controlled) | Local only | Phase 6 | N/A |
| `private_evaluation/hidden_tests/` | Tests only used during final scoring | Test files | Public strategies | Private | Yes | Local | Phase 6 | N/A |
| `private_evaluation/ground_truth/` | Expected action labels | Ground truth YAML/JSON | Strategy output | Private | Yes | Local | Phase 6 | N/A |

### 2.5 `src/benchmark/`

| Directory | Responsibility | Allowed Content | Forbidden Content | Public/Private | Version Controlled | Local/Kaggle/Shared | Phase Created | May Import From |
|-----------|---------------|----------------|-------------------|---------------|-------------------|---------------------|---------------|-----------------|
| `src/benchmark/` | Top-level package | `__init__.py`, `cli.py`, subpackages | Private data, notebooks | Public | Yes | Shared | Phase 0 | stdlib |
| `src/benchmark/core/` | Domain models, protocols, enums, exceptions (Layer 1) | Python modules | Concrete strategies, LLM code, Kaggle code, repo-specific code | Public | Yes | Shared | Phase 4 | stdlib |
| `src/benchmark/config/` | Config models, loader, validation (Layer 2) | Python modules | Private data, execution code | Public | Yes | Shared | Phase 4 | `core` |
| `src/benchmark/repositories/` | Repository adapters (Layer 3) | Python modules | LLM code, evaluation code | Public | Yes | Shared | Phase 4 | `core`, `config` |
| `src/benchmark/scenarios/` | Scenario loading, validation, sequencing (Layer 4) | Python modules | Private ground truth, evaluation | Public | Yes | Shared | Phase 4 | `core`, `config` |
| `src/benchmark/graph/` | Dependency graph, extractors, traversal (Layer 5) | Python modules | LLM code, strategy code | Public | Yes | Shared | Phase 4 | `core`, `config` |
| `src/benchmark/strategies/` | Strategy plugins (Layer 6) | Python modules | Private data, evaluation code, Kaggle-specific code | Public | Yes | Shared | Phase 4 | `core`, `config`, `repositories`, `graph` |
| `src/benchmark/llm/` | LLM backends (Layer 7) | Python modules | Private data, repositories, strategies | Public | Yes | Shared | Phase 4 | `core` |
| `src/benchmark/execution/` | Runner, pipeline, repair, budgets (Layer 8) | Python modules | Private ground truth | Public | Yes | Shared | Phase 4 | `core`, `config`, `repositories`, `scenarios`, `strategies`, `llm` |
| `src/benchmark/validation/` | Functional, regression, architecture validation (Layer 9) | Python modules | Private ground truth | Public | Yes | Shared | Phase 4 | `core`, `config`, `repositories` |
| `src/benchmark/evaluation/` | Metrics, scoring (Layer 10) | Python modules | Strategy execution code | Public | Yes | Local only (reads private data) | Phase 4 | `core`, `config`, `private_evaluation` |
| `src/benchmark/statistics/` | Statistical analysis (Layer 11) | Python modules | Private data directly | Public | Yes | Shared | Phase 4 | `core`, `config`, `evaluation` |
| `src/benchmark/provenance/` | Audit trail, hashing (Layer 12) | Python modules | Private data | Public | Yes | Shared | Phase 4 | `core` |
| `src/benchmark/reporting/` | Output formatting (Layer 13) | Python modules | Private data, strategy code | Public | Yes | Shared | Phase 4 | all lower layers |
| `src/benchmark/utils/` | Shared utilities | Python modules | Private data, domain logic | Public | Yes | Shared | Phase 4 | stdlib |

### 2.6 `tests/`

| Directory | Responsibility | Allowed Content | Forbidden Content | Public/Private | Version Controlled | Local/Kaggle/Shared | Phase Created | May Import From |
|-----------|---------------|----------------|-------------------|---------------|-------------------|---------------------|---------------|-----------------|
| `tests/` | Test suite root | `conftest.py`, subdirectories | Production code, private data | Public | Yes | Local | Phase 0 | `src/benchmark` |
| `tests/unit/` | Per-module unit tests | Test files | Integration fixtures, private data | Public | Yes | Local | Phase 4 | `src/benchmark`, `tests/fixtures` |
| `tests/contract/` | Protocol conformance tests | Test files | Implementation-specific tests | Public | Yes | Local | Phase 4 | `src/benchmark/core` |
| `tests/integration/` | Cross-module tests | Test files | Unit tests | Public | Yes | Local | Phase 4 | `src/benchmark`, `tests/fixtures` |
| `tests/architecture/` | Layer import checks, dependency rules | Test files | Domain logic tests | Public | Yes | Local | Phase 4 | `src/benchmark` |
| `tests/fixtures/` | Shared test fixtures | Mock repos, mock LLM responses, test scenarios | Private data | Public | Yes | Local | Phase 4 | `src/benchmark`, `core` |

### 2.7 `configs/`

| Directory | Responsibility | Allowed Content | Forbidden Content | Public/Private | Version Controlled | Local/Kaggle/Shared | Phase Created | May Import From |
|-----------|---------------|----------------|-------------------|---------------|-------------------|---------------------|---------------|-----------------|
| `configs/` | Execution configuration profiles | YAML files | Code, data | Public | Yes | Shared | Phase 4 | N/A (consumed by `src/benchmark/config`) |

### 2.8 `scripts/`

| Directory | Responsibility | Allowed Content | Forbidden Content | Public/Private | Version Controlled | Local/Kaggle/Shared | Phase Created | May Import From |
|-----------|---------------|----------------|-------------------|---------------|-------------------|---------------------|---------------|-----------------|
| `scripts/` | Utility scripts | Standalone Python scripts | Library code, private data | Public | Yes | Local | Phase 3 | `src/benchmark`, stdlib |

### 2.9 `notebooks/`

| Directory | Responsibility | Allowed Content | Forbidden Content | Public/Private | Version Controlled | Local/Kaggle/Shared | Phase Created | May Import From |
|-----------|---------------|----------------|-------------------|---------------|-------------------|---------------------|---------------|-----------------|
| `notebooks/` | Jupyter notebooks | `.ipynb` files | Production code, private data | Public | Yes | Shared (local) / Kaggle (kaggle/) | Phase 0 | `src/benchmark` |
| `notebooks/local/` | Local analysis notebooks | `.ipynb` | Kaggle-specific APIs | Public | Yes | Local | Phase 4 | `src/benchmark` |
| `notebooks/kaggle/` | Kaggle kernel notebooks | `.ipynb` | Local-specific paths | Public | Yes | Kaggle | Phase 9 | `src/benchmark` (bundled) |

### 2.10 `reports/`

| Directory | Responsibility | Allowed Content | Forbidden Content | Public/Private | Version Controlled | Local/Kaggle/Shared | Phase Created | May Import From |
|-----------|---------------|----------------|-------------------|---------------|-------------------|---------------------|---------------|-----------------|
| `reports/` | Generated reports | Markdown, PDF, HTML | Code, source data | Public | Yes | Shared | Phase 3 | N/A (generated) |

### 2.11 `runs/`

| Directory | Responsibility | Allowed Content | Forbidden Content | Public/Private | Version Controlled | Local/Kaggle/Shared | Phase Created | May Import From |
|-----------|---------------|----------------|-------------------|---------------|-------------------|---------------------|---------------|-----------------|
| `runs/` | Generated run output (proposed) | JSON, logs, provenance DB, test results | Source code, private data | Public | No (gitignored) | Local | Phase 4 | N/A (generated) |

### 2.12 `kaggle_upload/`

| Directory | Responsibility | Allowed Content | Forbidden Content | Public/Private | Version Controlled | Local/Kaggle/Shared | Phase Created | May Import From |
|-----------|---------------|----------------|-------------------|---------------|-------------------|---------------------|---------------|-----------------|
| `kaggle_upload/` | Kaggle submission package (proposed) | Source bundle, data bundle | Private data, notebooks | Public | Yes | Shared (for build), Kaggle (deployed) | Phase 9 | N/A (assembled by `scripts/build_upload_bundle.py`) |
| `kaggle_upload/code/` | Kaggle-compatible source | Bundled `src/benchmark/` subset | Local-specific code | Public | Yes | Kaggle | Phase 9 | N/A |
| `kaggle_upload/data/` | Kaggle-compatible data | Bundled `benchmark_data/` subset | Private evaluation data | Public | Yes | Kaggle | Phase 9 | N/A |

### 2.13 `repositories/`

| Directory | Responsibility | Allowed Content | Forbidden Content | Public/Private | Version Controlled | Local/Kaggle/Shared | Phase Created | May Import From |
|-----------|---------------|----------------|-------------------|---------------|-------------------|---------------------|---------------|-----------------|
| `repositories/` | Cloned/generated repos (proposed) | Git repos, source code | Private data, evaluation data | Public | No (gitignored, auto-generated/cloned) | Local | Phase 4 | N/A (consumed by `src/benchmark/repositories`) |
| `repositories/controlled_todo/` | Synthetic Django Todo repo | Python files, tests, migrations | Private ground truth | Public | No (generated) | Local | Phase 4 | N/A |

### 2.14 `release/`

| Directory | Responsibility | Allowed Content | Forbidden Content | Public/Private | Version Controlled | Local/Kaggle/Shared | Phase Created | May Import From |
|-----------|---------------|----------------|-------------------|---------------|-------------------|---------------------|---------------|-----------------|
| `release/` | Final release build (proposed) | Bundled code, data, docs | Development artifacts | Public | Yes | Shared | Phase 9 | N/A (assembled) |

---

## 3. Import Dependency Matrix (src/benchmark/)

```
core → (none)
config → core
repositories → core, config
scenarios → core, config
graph → core, config
strategies → core, config, repositories, graph
llm → core
execution → core, config, repositories, scenarios, strategies, llm
validation → core, config, repositories
evaluation → core, config, (private_evaluation — data only, not code)
statistics → core, config, evaluation
provenance → core
reporting → all lower layers
utils → stdlib
```

---

## 4. Version Control Rules

| Pattern | Git-tracked | Gitignored |
|---------|-------------|------------|
| `src/benchmark/**/*.py` | Yes | — |
| `docs/*.md` | Yes | — |
| `benchmark_data/**` | Yes | — |
| `private_evaluation/**` | Yes (git-crypt or restricted) | — |
| `configs/*.yaml` | Yes | — |
| `scripts/*.py` | Yes | — |
| `notebooks/**/*.ipynb` | Yes | — |
| `pyproject.toml` | Yes | — |
| `reports/**` | Yes | — |
| `runs/**` | — | Yes |
| `repositories/**` | — | Yes |
| `__pycache__/**` | — | Yes |
| `*.egg-info/**` | — | Yes |
| `.mypy_cache/**` | — | Yes |
| `.ruff_cache/**` | — | Yes |
| `.pytest_cache/**` | — | Yes |
| `.venv/**` | — | Yes |

---

## 5. Data Classification Summary

| Classification | Directories | Accessible By |
|---------------|-------------|---------------|
| **Public** — visible to all | `benchmark_data/`, `configs/`, `src/benchmark/` | All strategies, all evaluation |
| **Private** — hidden from strategies | `private_evaluation/` | Only `evaluation/` and `statistics/` modules |
| **Generated** — not version-controlled | `runs/`, `repositories/` | Execution pipeline, evaluation |
| **Kaggle-only** — bundled for Kaggle | `notebooks/kaggle/`, `kaggle_upload/` | Kaggle runtime environment |
