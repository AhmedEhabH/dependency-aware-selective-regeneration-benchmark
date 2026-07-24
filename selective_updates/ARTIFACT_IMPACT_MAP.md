# Artifact Impact Map

Concise lookup mapping common change types to affected artifacts, tests, gates, and deployment actions.

Do not duplicate `CANONICAL_ARTIFACT_INVENTORY.md`. This is a change-to-artifact lookup for planning.

---

## Change Type → Impact Mapping

| Change Type | Canonical Artifact | Likely Derivatives | Targeted Tests | Full Gates | Scientific Approval | Deployment Action |
|-------------|-------------------|--------------------|----------------|------------|---------------------|-------------------|
| **CLI-only defect** | `seven_arm_benchmark.py` | `kaggle_upload/code/seven_arm_benchmark.py` | `tests/unit/test_cli.py` | ruff, mypy, pytest | No | Rebuild bundle |
| **Checkpoint defect** | `src/benchmark/checkpoint/*` | `kaggle_upload/code/src/benchmark/checkpoint/` | `tests/unit/checkpoint/` | ruff, mypy, pytest | No | Rebuild bundle |
| **Graph builder defect** | `src/benchmark/graph/*` | `kaggle_upload/code/src/benchmark/graph/` | `tests/unit/graph/` | ruff, mypy, pytest | No | Rebuild bundle |
| **Strategy defect** | `src/benchmark/strategies/*` | `kaggle_upload/code/src/benchmark/strategies/` | `tests/unit/strategies/` | ruff, mypy, pytest | No | Rebuild bundle |
| **LLM backend defect** | `src/benchmark/llm/*` | `kaggle_upload/code/src/benchmark/llm/` | `tests/unit/llm/` | ruff, mypy, pytest | No | Rebuild bundle |
| **Execution defect** | `src/benchmark/execution/*` | `kaggle_upload/code/src/benchmark/execution/` | `tests/unit/execution/` | ruff, mypy, pytest | No | Rebuild bundle |
| **Evaluation defect** | `src/benchmark/evaluation/*` | `kaggle_upload/code/src/benchmark/evaluation/` | `tests/unit/evaluation/` | ruff, mypy, pytest | No | Rebuild bundle |
| **Selection defect** | `src/benchmark/selection/*` | `kaggle_upload/code/src/benchmark/selection/` | `tests/unit/selection/` | ruff, mypy, pytest | No | Rebuild bundle |
| **Statistics defect** | `src/benchmark/statistics/*` | `kaggle_upload/code/src/benchmark/statistics/` | `tests/unit/statistics/` | ruff, mypy, pytest | No | Rebuild bundle |
| **Config profile change** | `configs/*.yaml` | `kaggle_upload/code/configs/` | `tests/contract/test_config_contract.py` | ruff, mypy, pytest | No | Rebuild bundle |
| **Scenario change** | `benchmark_data/scenarios/*` | `kaggle_upload/data/scenarios/` | `tests/unit/scenarios/`, `tests/integration/test_scenarios_integration.py` | ruff, mypy, pytest | **Yes** (protocol) | Rebuild data bundle |
| **Repository profile change** | `benchmark_data/repository_profiles/*` | `kaggle_upload/data/repository_profiles/` | `tests/unit/repositories/`, `tests/integration/test_repositories_integration.py` | ruff, mypy, pytest | **Yes** (protocol) | Rebuild data bundle |
| **Manifest change** | `benchmark_data/manifests/*` | `kaggle_upload/data/manifests/` | `tests/unit/repositories/` | ruff, mypy, pytest | No | Rebuild data bundle |
| **Notebook workflow change** | `notebooks/seven_arm_benchmark.ipynb` | `kaggle_upload/notebooks/seven_arm_benchmark.ipynb` | Manual verification on Kaggle | nbformat validation | No | Rebuild notebook bundle |
| **Documentation (operational)** | `docs/START_HERE.md`, `docs/PROJECT_HANDOFF.md`, `docs/SELECTIVE_PROJECT_UPDATE_POLICY.md` | None | None | None | No | Commit only |
| **Frozen protocol doc** | `docs/FINAL_RESEARCH_PROTOCOL.md` | None | None | None | **Required** | Forbidden |
| **Core domain model change** | `src/benchmark/core/*` | `kaggle_upload/code/src/benchmark/core/` | All unit tests | ruff, mypy, pytest | **Yes** (protocol) | Rebuild bundle |
| **New strategy arm** | `src/benchmark/strategies/*.py` + `seven_arm_benchmark.py` | Code + notebook bundles | New strategy tests + full suite | ruff, mypy, pytest | **Yes** (protocol) | Rebuild all bundles |

---

## Field Definitions

- **Canonical Artifact**: The source file(s) that must be edited
- **Likely Derivatives**: Generated bundles that will be regenerated
- **Targeted Tests**: Minimal test set to run for fast feedback
- **Full Gates**: Complete quality gates required before merge
- **Scientific Approval**: Whether protocol review is required
- **Deployment Action**: What to do after merge (usually `scripts/build_upload_bundle.py`)