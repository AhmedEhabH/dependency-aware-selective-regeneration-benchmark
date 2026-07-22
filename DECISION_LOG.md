# Decision Log

## Decision D001 — Bootstrap Phase
- **Date:** 2026-07-22
- **Decision ID:** D001
- **Status:** IMPLEMENTED
- **Category:** Engineering
- **Description:** Execute Phase 0 (Bootstrap and Environment) as the initial project phase.
- **Rationale:** The working directory is empty (except for `docs/OPENCODE_EXECUTION_GUIDE.md`). Per the guide, Phase 0 must be executed first.
- **Alternatives considered:** None — Phase 0 is the required first phase.
- **Impact:** Establishes project structure, Conda environment, state files, and Git baseline.
- **Evidence:** Successful directory creation, environment creation, and Git initialization.

---

## Decision D002 — Conda as Package Resolver
- **Date:** 2026-07-22
- **Decision ID:** D002
- **Status:** IMPLEMENTED
- **Category:** Engineering
- **Description:** Use `conda` (not mamba/micromamba) as the package resolver.
- **Rationale:** `conda` 23.10.0 is available. `mamba` and `micromamba` are not installed.
- **Alternatives considered:** 
  - Install mamba in base → rejected (forbidden by Section 3.2: "install packages into the base Conda environment")
  - Install mamba inside the project env → would complicate bootstrap (chicken-and-egg)
- **Impact:** Slower dependency resolution; no functional difference.

---

## Decision D003 — Environment Package Selection
- **Date:** 2026-07-22
- **Decision ID:** D003
- **Status:** IMPLEMENTED
- **Category:** Engineering
- **Description:** Define environment.yml with core Python 3.11 + numpy + pandas via Conda channels, and development/testing/linting packages via pip from requirements-dev.txt.
- **Rationale:** Conda provides pre-compiled binaries for numpy/pandas (no local build toolchain required). Pip is the standard for pure-Python dev tools. This hybrid approach follows Section 4.2 guidelines.
- **Alternatives considered:** 
  - All conda → some dev packages missing from conda-forge on Windows
  - All pip → would lose compiled-dependency optimization
- **Impact:** Faster installation, smaller environment file.

---

## Decision D004 — Kaggle Requirements Not Installed Locally
- **Date:** 2026-07-22
- **Decision ID:** D004
- **Status:** IMPLEMENTED
- **Category:** Engineering
- **Description:** Do not install `requirements-kaggle.txt` contents (torch, transformers, datasets, kagglehub) in the local environment.
- **Rationale:** Section 3.2 forbids downloading model weights or running LLM inference locally. torch would pull CUDA runtime; transformers would pull tokenizer files. These are Kaggle-only dependencies.
- **Alternatives considered:** Install torch CPU-only → still triggers 2+ GB download, against the spirit of "no local model"
- **Impact:** Local environment is ~500 MB instead of ~5 GB. All Kaggle-only dependencies must be validated on Kaggle.

---

## Decision D005 — Phase 1 Input Audit Completion
- **Date:** 2026-07-22
- **Decision ID:** D005
- **Status:** IMPLEMENTED
- **Category:** Engineering
- **Description:** Complete Phase 1 (Input Audit) and classify all existing benchmark outputs as `legacy_pilot`.
- **Rationale:** The execution guide specifies Phase 1 must follow Phase 0. Audit found zero pre-existing benchmark output files; paper is the sole authoritative input.
- **Alternatives considered:** N/A — Phase 1 order is fixed by the execution guide.
- **Impact:** Establishes baseline inventory of inputs, documents missing artifacts for later phases, and sets the paper as the authoritative constraint for all future implementation decisions.
- **Evidence:** reports/INPUT_AUDIT_REPORT.md documents all findings.

---

## Decision D006 — Phase 2A Protocol Draft
- **Date:** 2026-07-22
- **Decision ID:** D006
- **Status:** IMPLEMENTED
- **Category:** Protocol
- **Description:** Produce a complete draft of the research protocol covering RQ/H traceability, repository selection, artifact universe, ground truth, annotation, scenarios, baselines, metrics, statistical analysis, policies, validity, and reproducibility.
- **Rationale:** Phase 2 of the execution guide requires creating the research protocol before repository and implementation work begins.
- **Alternatives considered:** N/A — Phase 2 order is fixed by the execution guide.
- **Impact:** Establishes the full protocol draft with 21 sections. 14 decision items require researcher approval before the protocol can be frozen. No scientific decisions were frozen in this draft.
- **Evidence:** reports/PHASE2_PROTOCOL_DRAFT.md (21 sections, ~400+ lines).

---

## Decision D007 — Phase 2B Protocol Freeze
- **Date:** 2026-07-22
- **Decision ID:** D007
- **Status:** IMPLEMENTED
- **Category:** Protocol
- **Description:** Freeze Research Protocol v1.0 from Phase 2A draft by applying 14 researcher-approved decisions (DA-01 through DA-14) and 11 mandatory corrections (AC-01 through AC-11).
- **Rationale:** The researcher provided approved decisions in docs/FINAL_RESEARCH_PROTOCOL_DECISIONS.md. All REQUIRES_RESEARCHER_APPROVAL items are resolved. The protocol is now frozen and Phase 3 is authorized.
- **Alternatives considered:** N/A — researcher decisions are binding.
- **Contradictions corrected:**
  - §9.3 regression pass rate formula: "regressed/total inverted" → passed/total (AC-02)
  - §15.2 repair budget: max 3 → max 2 attempts (AC-05)
  - §15.4 strategy exclusion: "excluded from aggregates" → failures remain (AC-04)
  - §16.2 hidden tests: cross-validation offered as alternative → cross-validation not a substitute (AC-03)
  - §13.4 determinism: "temperature=0 → identical outputs" → best-effort reproducibility (AC-07)
  - §9.5 cost: "estimated monetary cost: USD" → no invented cost (AC-08)
  - §20.5 H5: "monotonically decreases" → perfect monotonicity not required (AC-10)
  - §3.5 time cutoff: "6 months" → "90 days" (DA-03)
  - §14.4 budget: "8.6M tokens" estimate → three-stage approach (DA-09)
- **Impact:** Research Protocol v1.0 is frozen. 8 frozen documents created under docs/. Phase 3 is authorized but has not started.
- **Evidence:** docs/FINAL_RESEARCH_PROTOCOL.md and 7 companion documents; reports/PHASE2B_PROTOCOL_FREEZE_REPORT.md.

---

## Decision D008 — Phase 3 Repository Selection and Scenario Preparation
- **Date:** 2026-07-22
- **Decision ID:** D008
- **Status:** IMPLEMENTED
- **Category:** Repository
- **Description:** Complete Phase 3 by selecting 3 confirmatory repositories (Controlled Django Todo, django CMS 5.0.0, Saleor Core 3.23.0), pinning their versions, creating architectural profiles, and designing 24 scenarios (8 per repo).
- **Rationale:** Phase 3 is required by the execution guide before benchmark implementation begins. Repository versions were selected per DA-03 (≥ 90 days old): django CMS 5.0.0 (437 days), Saleor Core 3.23.0 (104 days). The Controlled Django Todo is a synthetic repository created for benchmark control.
- **Alternatives considered:** 
  - ERPNext → replaced by Saleor (AC-10 correction, better architecture boundaries)
  - Apache Airflow → rejected (too large, unusual dependency patterns)
- **Repository versions frozen:**
  - django CMS 5.0.0: commit `0f633fc9fa213357f4202482aab2b0edad680f95`, released 2025-05-12
  - Saleor Core 3.23.0: commit `e11a5557eff29fbb2eed36e6ff3cd0af08ab9e10`, released 2026-04-09
  - Controlled Django Todo: v1.0.0 (synthetic, initial commit)
- **Scenario allocation:** 8 per repository = 3 localized + 3 moderate + 2 cross-cutting; all 8 change types covered per repo.
- **Impact:** Phase 3 deliverables complete. 35 files created (2 manifests, 3 profiles, 24 scenarios, 6 reports). Phase 4 (benchmark core implementation) is the next step.
- **Contradictions applied from protocol:**
  - ERPNext excluded per AC-10
  - Hidden tests per scenario per AC-03
  - Permissive licenses recorded per DA-02
- **Evidence:** All files under benchmark_data/ and reports/; PHASE3_REPOSITORY_SCENARIO_REPORT.md.

---

## Decision D009 — Phase 3.5 Static Architecture Audit
- **Date:** 2026-07-22
- **Decision ID:** D009
- **Status:** IMPLEMENTED
- **Category:** Architecture
- **Description:** Execute Phase 3.5 — Static Architecture Audit and Project Map. Inspect full repository layout, identify structural conflicts, define canonical project root, create project structure map, define 13-layer software architecture with 11 interface protocols, document dependency rules, create extension guide, define public/private boundary, split Phase 4 into 6 milestones, create architecture validation plan.
- **Rationale:** Phase 3.5 is inserted between Phase 3 (repository/scenario prep) and Phase 4 (implementation) to freeze architecture decisions, establish path policies, and create an implementation blueprint before any code is written. This prevents architectural drift during implementation.
- **Alternatives considered:** Proceed directly to Phase 4 — rejected because Phase 3 discovered a critical duplicate directory structure that would cause confusion during implementation.
- **Architecture decisions frozen:**
  - 11 interface protocols (ImpactStrategy, LLMBackend, etc.)
  - Protocol over ABC (Protocol for interfaces, ABC only for shared defaults)
  - Instantiated registries (no global singletons)
  - Dependency injection (constructor-based)
  - Lazy Kaggle imports (torch/transformers only inside methods)
  - Core isolation (Core imports nothing from infrastructure)
  - Immutable run records (frozen dataclasses)
  - Pydantic for configuration models
  - Private evaluation boundary (hidden tests, ground truth outside strategy-facing paths)
- **Critical structural finding:** Root-level `docs/` and `benchmark_data/` directories outside the Git repository contain stale/duplicate files. The canonical source of truth is `project/`. Remediation documented in `reports/PROJECT_STRUCTURE_CONFLICT_REPORT.md`.
- **Phase 4 milestones defined:**
  - 4A: Domain Models and Contracts (~12 files)
  - 4B: Loaders and Validation (~16 files)
  - 4C: Model Backends (~5 files)
  - 4D: Execution Core (~8 files)
  - 4E: Provenance and Result Storage (~6 files)
  - 4F: Architecture and Contract Tests (~8 files)
- **Impact:** Phase 3.5 deliverables complete. 8 new docs, 2 reports, 10 new architecture checks passed. Phase 4A is the exact next task.
- **Evidence:** All files under docs/ (16 total), reports/PHASE3_5_ARCHITECTURE_AUDIT.md, reports/PROJECT_STRUCTURE_CONFLICT_REPORT.md.

---

## Decision D010 — Phase 3.6 Structure Remediation and Baseline Commit
- **Date:** 2026-07-22
- **Decision ID:** D010
- **Status:** IMPLEMENTED
- **Category:** Structure
- **Description:** Execute Phase 3.6 — Structure Remediation and Baseline Commit. Resolve all structural conflicts identified in Phase 3.5: copy reference docs, delete stale files, fix scenario blast_radius inconsistencies (14 files), update .gitignore, create baseline Git commit covering all Phase 3/3.5/3.6 work.
- **Rationale:** The Phase 3.5 conflict report documented critical duplicate directory structure and scenario taxonomy inconsistencies that must be resolved before Phase 4 implementation begins. A baseline commit is needed to prevent working-tree-only state.
- **Alternatives considered:** Proceed directly to Phase 4A without remediation — rejected because stale outer copies could cause path confusion during implementation.
- **Actions executed:**
  - Copied `OPENCODE_EXECUTION_GUIDE.md` and `MASTER_IMPLEMENTATION_PLAN.md` into `project/docs/`
  - Deleted stale outer `FINAL_RESEARCH_PROTOCOL_DECISIONS.md` and `HUMAN_DECISIONS_REQUIRED.md`
  - Deleted stale outer `benchmark_data/` (incomplete duplicate)
  - Preserved `inputs/paper/` as immutable external data
  - Fixed blast_radius in 14 scenario YAMLs (6 localized, 6 moderate, 4 cross_cutting)
  - Deduplicated `.gitignore`, added `runs/`, added report exceptions
  - Validated full project tree (79 files, 15 dirs, scaffold-only src)
  - Created baseline commit `845ba49` (57 files, 7652 insertions)
- **Impact:** Phase 3.6 deliverables complete. Structural conflicts resolved. Working tree clean. Phase 4A (Domain Models and Contracts) is the exact next task.
- **Evidence:** `reports/PHASE3_6_STRUCTURE_REMEDIATION_REPORT.md`, Git commit `845ba49`.

---

## Decision D011 — Phase 4A Domain Models and Contracts
- **Date:** 2026-07-22
- **Decision ID:** D011
- **Status:** IMPLEMENTED
- **Category:** Core Implementation
- **Description:** Execute Phase 4A — Domain Models and Contracts. Implement all domain models (enums, exceptions, models, protocols, registry, context) in `src/benchmark/core/` and config models/loader/validation in `src/benchmark/config/`.
- **Rationale:** Phase 4A is the first implementation milestone (Layer 1 and 2 of the 13-layer architecture). Domain models must exist before loaders, strategies, or execution code can be written.
- **Alternatives considered:** Skip Phase 4A and implement everything at once — rejected because the architecture blueprint explicitly requires layered implementation and the milestone dependencies were defined in Phase 3.5.
- **Implementation scope:**
  - 6 StrEnum classes in `src/benchmark/core/enums.py`
  - 12 typed exception classes in `src/benchmark/core/exceptions.py`
  - 24 frozen dataclass models in `src/benchmark/core/models.py`
  - 11 runtime-checkable protocol interfaces in `src/benchmark/core/protocols.py`
  - Generic `Registry[T]` in `src/benchmark/core/registry.py`
  - `ExecutionContext` in `src/benchmark/core/context.py`
  - 7 Pydantic v2 config models in `src/benchmark/config/models.py`
  - YAML loader in `src/benchmark/config/loader.py`
  - Structural validation in `src/benchmark/config/validation.py`
  - 106 tests across 8 test files
  - `pyproject.toml` with ruff/mypy/pytest configuration
- **Design decisions:**
  - `ExecutionContext` is controlled-mutable (frozen=False) to allow budget/seed updates during execution
  - `Registry[T]` supports `freeze()` to prevent mutations after configuration is finalized
  - Pydantic models use `frozen=True` for immutability consistency
  - ImpactStrategy protocol permits BenchmarkError subclasses to propagate
- **Quality gates:**
  - Ruff: 0 violations ✅
  - Mypy strict: 0 errors ✅
  - Pytest: 106/106 passed in 0.75s ✅
  - pip check: no broken requirements ✅
  - Import isolation: torch/transformers not imported at package load ✅
- **Impact:** Phase 4A deliverables complete. Domain layer and config layer implemented. 17 source files created, 8 test files created, 2 documentation files created. Phase 4B (Loaders and Validation) is the exact next task.
- **Evidence:** `docs/PHASE4A_DOMAIN_MODEL_REFERENCE.md`, `reports/PHASE4A_DOMAIN_MODELS_REPORT.md`, all files under `src/benchmark/core/` and `src/benchmark/config/`.

---

## Decision D012 — Phase 4B Loaders and Validation
- **Date:** 2026-07-22
- **Decision ID:** D012
- **Status:** IMPLEMENTED
- **Category:** Core Implementation
- **Description:** Execute Phase 4B — Loaders and Validation. Implement repository adapters, manifest models, YAML loading, snapshot management, workspace isolation, scenario models (dual-format YAML), scenario loading, validation, and sequencing.
- **Rationale:** Phase 4B requires loaders and validation before execution pipeline can be built. Repository profiles, version manifests, and scenario YAMLs must be loadable from disk.
- **Alternatives considered:** Skip loaders and hardcode scenario data — rejected because it would make the benchmark data-driven as required by the architecture.
- **Implementation scope:**
  - `RepositoryLoaderBase` abstract base with `resolve_identity` / `resolve_snapshot`
  - `RepositoryManifest`, `RepositoryVersionEntry`, `RepositoryProfile`, `ManifestCollection` (frozen dataclasses)
  - `RepositoryLoader` YAML loading from `manifests/` and `repository_profiles/`
  - `SnapshotMetadata`, `create_snapshot_metadata()`, `validate_snapshot()`
  - `WorkspacePath`, `validate_workspace_path()`, `check_isolation()`
  - `ScenarioModel` with `to_core_scenario()` and dual-format expected_actions parsing
  - `ScenarioLoader` with `load_all()` and `load_by_repository()`
  - `ScenarioValidator` with required field checks and duplicate action detection
  - `ScenarioSequencer` ordering by blast_radius
  - 95 new tests (84 unit/contract + 11 integration); 206 total suite
- **Design decisions:**
  - Dual-format expected_actions: supports both standard `"path:Symbol": action` and action-grouped `action: [paths]` YAML formats
  - Deduplication in `to_core_scenario()` to handle real benchmark data
  - Snapshot validation reports all issues (does not raise) for composability
  - Workspace isolation uses `Path.resolve()` for accurate comparison
- **Quality gates:**
  - Ruff: 0 violations ✅
  - Mypy strict: 0 errors ✅
  - Pytest: 206/206 passed in 1.77s ✅
  - pip check: no broken requirements ✅
  - Import isolation: torch/transformers not imported at package load ✅
- **Impact:** Phase 4B deliverables complete. 11 production files created under `src/benchmark/repositories/` and `src/benchmark/scenarios/`. 14 test files created. Phase 4C (Model Backends) is the exact next task.
- **Evidence:** `docs/PHASE4B_LOADERS_AND_VALIDATION_REFERENCE.md`, `reports/PHASE4B_LOADERS_AND_VALIDATION_REPORT.md`, all files under `src/benchmark/repositories/` and `src/benchmark/scenarios/`.

---

## Decision D013 — Phase 4C Model Backends
- **Date:** 2026-07-22
- **Decision ID:** D013
- **Status:** IMPLEMENTED
- **Category:** LLM Backend
- **Description:** Execute Phase 4C — Model Backends. Implement MockLLMBackend, DryRunLLMBackend, and KaggleQwenBackend skeleton under `src/benchmark/llm/`. BackendFactory registry integration. Backend tests.
- **Rationale:** Phase 4C is required before execution pipeline (Phase 4D) can be built. The LLM backend abstraction must be in place with mock/dry-run for local testing and a Kaggle-safe skeleton that does not require local torch/transformers.
- **Alternatives considered:** Use a single backend class with mode flags — rejected because each backend has fundamentally different behavior (mock = deterministic, dry-run = file-based, kaggle = real model).
- **Implementation scope:**
  - `MockLLMBackend`: deterministic response, configurable text, token counting
  - `DryRunLLMBackend`: reads fixture JSON files, falls back to default response, never calls an API
  - `KaggleQwenBackend`: lazy torch/transformers imports, raises ModelBackendError when called locally (skeleton for Kaggle)
  - `BackendFactory`: wraps Registry[LLMBackend] with register/create/freeze/contains/len
  - 23 new tests (22 unit + 1 import isolation); 229 total suite
- **Design decisions:**
  - Lazy imports: torch/transformers only imported inside `_lazy_import()` method, never at module level
  - BackendFactory delegates to existing generic Registry instead of creating new registry type
  - ARG002 suppressed via per-file-ignores for protocol-conforming unused params
  - DryRun fixture format: `fixture_response.json` with `text`, `*_tokens`, `finish_reason`
- **Quality gates:**
  - Ruff: 0 violations ✅
  - Mypy strict: 0 errors ✅
  - Pytest: 229/229 passed in 2.01s ✅
  - pip check: no broken requirements ✅
  - Import isolation: `import benchmark.llm` does not import torch/transformers ✅
- **Impact:** Phase 4C deliverables complete. 5 production files, 6 test files, 2 doc files. Phase 4D (Execution Core) is the exact next task.
- **Evidence:** `docs/PHASE4C_MODEL_BACKENDS_REFERENCE.md`, `reports/PHASE4C_MODEL_BACKENDS_REPORT.md`, all files under `src/benchmark/llm/` and `tests/unit/llm/`.
