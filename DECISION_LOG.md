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

---

## Decision D014 — Phase 4D Execution Core
- **Date:** 2026-07-22
- **Decision ID:** D014
- **Status:** IMPLEMENTED
- **Category:** Execution Orchestration
- **Description:** Execute Phase 4D — Execution Core. Implement BudgetManager, RunStateMachine, RepairLoop, IsolationContext, BenchmarkRunner, and BenchmarkPipeline under `src/benchmark/execution/`.
- **Rationale:** Phase 4D implements Layer 8 (Execution Orchestration) of the 13-layer architecture. The execution pipeline is required before strategies, graph analysis, and evaluation (Phase 4E) can be built.
- **Alternatives considered:** Implement execution and strategies together — rejected because the blueprint explicitly separates orchestration (4D) from strategy composition (4E).
- **Implementation scope:**
  - `BudgetManager`: injectable Clock, multi-axis enforcement (attempts/tokens/timeout), per-attempt tracking, reset
  - `RunStateMachine`: 6-state lifecycle (prepared→running→succeeded/failed/timed_out/cancelled), typed transitions, terminal-state protection
  - `RepairLoop`: 1+2 attempt lifecycle, configurable FailureClassifier, BudgetManager integration
  - `IsolationContext`: wraps Phase 4B workspace utilities, private data detection, run/temp directory creation
  - `BenchmarkRunner`: coordinates ImpactStrategy + LLMBackend + IsolationContext into RunRecord
  - `BenchmarkPipeline`: single/batch/dry-run modes, PipelineResult aggregation
  - 59 new tests across 6 test files; 288 total suite
- **Design decisions:**
  - `BudgetManager` uses injectable `Clock` protocol for deterministic timeout testing
  - `RepairLoop` manages state machine transitions (runner does not call `state_machine.succeed/fail` directly)
  - `IsolationContext` delegates to Phase 4B utilities — no new isolation logic
  - `BenchmarkRunner.dry_run()` is separate from `run()` — returns success Record with 0 duration
  - `PipelineConfig.dry_run` flag enables pipeline-level dry-run without strategy execution
  - No concrete strategy or repository names used in generic execution code — dependency injection throughout
  - No imports from `private_evaluation/`, ground truth, hidden tests, or scoring code
- **Quality gates:**
  - Ruff: 0 violations ✅
  - Mypy strict: 0 errors ✅
  - Pytest: 288/288 passed in 2.24s ✅
  - pip check: no broken requirements ✅
  - Import isolation: torch/transformers not imported at package load ✅
  - Budget validation: 14 tests covering attempts, tokens, timeout, reset, edge cases ✅
  - Repair validation: 8 tests covering success, retry, exhaustion, error handling, classification ✅
  - Isolation validation: 9 tests covering workspace, private data, directories, custom validator ✅
  - Runner validation: 7 tests covering lifecycle, dry_run, isolation failure, budget config, run_id ✅
  - Pipeline validation: 6 tests covering dry-run, batch, failure tracking, non-dry modes ✅
  - State machine validation: 13 tests covering all transitions, terminal protection, guard methods ✅
- **Impact:** Phase 4D deliverables complete. 7 production files, 7 test files, 2 documentation files created. Phase 4E (Strategies, Graph, Evaluation, Statistics) is the exact next task.
- **Evidence:** `docs/PHASE4D_EXECUTION_CORE_REFERENCE.md`, `reports/PHASE4D_EXECUTION_CORE_REPORT.md`, all files under `src/benchmark/execution/` and `tests/unit/execution/`.

---

## Decision D015 — Split Phase 4E Into Implementation and Evaluation Phases
- **Date:** 2026-07-22
- **Decision ID:** D015
- **Status:** IMPLEMENTED
- **Category:** Planning
- **Description:** Split the originally planned Phase 4E into two separate phases: Phase 4E (Impact Strategies) and Phase 4F (Evaluation Engine). Phase 4E covers strategy implementation, dependency graph, artifact selection, regeneration planning, strategy registry, and strategy validation — with no evaluation metrics, no statistical analysis, and no scoring. Phase 4F covers evaluation engine, metric computation, ground truth comparison, result aggregation, statistical analysis (confidence intervals, effect sizes), notebook-ready export, and publication tables.
- **Rationale:** The original Phase 4E scope was too large, combining strategy implementation (high complexity, 7 distinct arms) with evaluation/statistics (also high complexity). Splitting reduces risk by allowing each phase to be independently implemented, tested, verified, and merged. This mirrors the successful Phase 4A–4D subphasing pattern.
- **Alternatives considered:**
  - Keep monolithic Phase 4E — rejected because combining strategies and evaluation in one phase would create a ~1500-line diff with 4+ packages, increasing merge risk and review burden
  - Split into 3+ subphases — rejected; two phases is sufficient and keeps planning simple
- **Impact:**
  - Phase 4E now covers: strategies (7 arms), graph, selection, planning, registry, validation
  - Phase 4F now covers: evaluation, metrics, comparison, aggregation, statistics, reporting, exports
  - Phase 4E depends on Phase 4D; Phase 4F depends on Phase 4E
  - All planning documents updated: MASTER_IMPLEMENTATION_PLAN.md, PHASE4_IMPLEMENTATION_BLUEPRINT.md, SYSTEM_STATE.md, TODO.md, DECISION_LOG.md
  - No change to frozen research protocol documents
- **Evidence:** Updated phase table in `docs/MASTER_IMPLEMENTATION_PLAN.md`, updated milestone descriptions in `docs/PHASE4_IMPLEMENTATION_BLUEPRINT.md`, Phase 4E/4F task blocks in `TODO.md`. Documentation branch pushed and merged to `main`.

---

## Decision D016 — TD-1 Runner Protocol Remediation
- **Date:** 2026-07-22
- **Decision ID:** D016
- **Status:** IMPLEMENTED
- **Category:** Engineering Correction
- **Description:** Remediate TD-1 by refactoring `BenchmarkRunner._run_attempt` to construct the correct domain objects (`RepositorySnapshot`, `RequirementChange`, `ArtifactUniverse`) from `Scenario` before calling `ImpactStrategy.analyze_impact()`. Remove all `# type: ignore[arg-type]` from the runner path.
- **Rationale:** The frozen `ImpactStrategy` protocol requires `RepositorySnapshot`, `RequirementChange`, and `ArtifactUniverse` parameters. Passing `Scenario` (a different type) with `type: ignore` comments violated the protocol contract and would cause failures in any concrete strategy implementation that relied on the correct types.
- **Alternatives considered:**
  - Make `Scenario` subclass or conform to all three types — rejected because `Scenario` is a distinct domain concept with different fields
  - Change the protocol to accept `Scenario` — rejected because the protocol is frozen and strategies need distinct domain objects
  - Add adapter layer in strategy implementations — rejected because it would duplicate extraction logic across 7 strategies
- **Implementation:**
  - Added `_build_repository_snapshot()`, `_build_requirement_change()`, `_build_artifact_universe()` private methods
  - Updated `_run_attempt` to construct and pass correct types
  - Removed 3 `# type: ignore[arg-type]` comments
  - Added `test_run_extracts_correct_domain_objects` test
- **Impact:** Phase 4E is now authorized. No scientific protocol changed. No frozen documents affected. 289/289 tests passing.
- **Evidence:** `reports/TD1_REMEDIATION_REPORT.md`, git branch `fix/td1-runner-protocol`.

---

## Decision D017 — Phase 4E Impact Strategies
- **Date:** 2026-07-22
- **Decision ID:** D017
- **Status:** IMPLEMENTED
- **Category:** Core Implementation
- **Description:** Execute Phase 4E — Impact Strategies. Implement 7 strategy patterns (monolithic, agent, selective, compiled_ai, delta_mcp, incr_rtl, code_plan), StrategyRegistry, graph package (models, extractors, propagator, scope reducer), and selection package (artifact selector, regeneration planner).
- **Rationale:** Phase 4E implements Layer 5 (Dependency Graph), Layer 6 (Impact Strategies), and Layer 7 (Artifact Selection) of the 13-layer architecture. These are required before Phase 4F (Evaluation Engine) can compare strategy predictions against ground truth.
- **Alternatives considered:**
  - Implement strategies without graph/selection packages — rejected because selective and full-context strategies depend on graph propagation
  - Use ABC base classes for strategies — rejected per architecture decision to use Protocol for interfaces
- **Implementation scope:**
  - `src/benchmark/strategies/`: 7 strategy implementations + StrategyRegistry
  - `src/benchmark/graph/`: DependencyGraphModel, PythonImportExtractor, ImpactPropagator, ScopeReducer
  - `src/benchmark/selection/`: ArtifactSelector, RegenerationPlanner
  - 43 new tests across 3 test files; 332 total suite
- **Design decisions:**
  - Dependency injection throughout — strategies accept injectable components (graph, coverage map, LLM backend)
  - No global singletons — StrategyRegistry is instantiated and injected
  - Protocol conformance — all strategies implement ImpactStrategy protocol structurally
  - ARG002 suppressed for strategy files — protocol-mandated parameters not always used by every strategy
  - Graph models separate from core — extends (does not modify) minimal DependencyGraph
- **Quality gates:**
  - Ruff: 0 violations ✅
  - Mypy strict: 0 errors ✅
  - Pytest: 332/332 passed (2.53s) ✅
  - pip check: no broken requirements ✅
- **Impact:** Phase 4E deliverables complete. 14 production files created across 3 packages. 3 test files created. Phase 4F (Evaluation Engine) is the exact next task.
- **Evidence:** `reports/PHASE4E_IMPACT_STRATEGIES_REPORT.md`, all files under `src/benchmark/strategies/`, `src/benchmark/graph/`, `src/benchmark/selection/`, and associated test files.

---

## Decision D018 — Phase 4F Evaluation Engine

- **Date:** 2026-07-22
- **Decision ID:** D018
- **Status:** IMPLEMENTED
- **Category:** Evaluation
- **Description:** Execute Phase 4F — Evaluation Engine. Implement ground-truth comparison, metric computation, run aggregation, statistical analysis (confidence intervals, effect sizes), notebook-ready exports, and publication-ready result tables.
- **Rationale:** Phase 4F implements Layer 5 (Evaluation) of the 13-layer architecture. It provides the scientific evaluation pipeline to compare strategy predictions against ground truth and produce analysis-ready outputs.
- **Alternatives considered:**
  - Build evaluation into strategy implementations — rejected because it would tightly couple evaluation logic to strategy code
  - Use external analysis tools — rejected because the benchmark needs integrated, reproducible evaluation
- **Implementation scope:**
  - `src/benchmark/evaluation/`: EvaluationEngine, MetricComputer
  - `src/benchmark/comparison/`: GroundTruthComparator, ResultAggregator
  - `src/benchmark/statistics/`: StatisticalAnalyzer, ConfidenceIntervalCalculator, EffectSizeComputer, NotebookExporter, PublicationTableBuilder
  - 73 new tests across 3 test files; 405 total suite
- **Design decisions:**
  - Metrics computed per-run, aggregated across scenarios
  - Bootstrap CI with 1000 samples for non-parametric estimates
  - Effect sizes: Cohen's d (parametric), Cliff's delta (non-parametric)
  - Non-inferiority margin Δ = 0.05 per DA-08 for pass rate comparisons
  - Export formats: JSON for notebooks, CSV/Markdown/LaTeX for publications
- **Quality gates:**
  - Ruff: 0 violations ✅
  - Mypy strict: 0 errors ✅
  - Pytest: 405/405 passed ✅
  - pip check: no broken requirements ✅
- **Impact:** Phase 4F deliverables complete. 11 production files created across 3 packages. 8 test files created. Project is feature-complete from infrastructure perspective. Phase 5 (if any) would be scientific analysis.
- **Evidence:** `docs/PHASE4F_EVALUATION_ENGINE_REFERENCE.md`, `reports/PHASE4F_EVALUATION_ENGINE_REPORT.md`, all files under `src/benchmark/evaluation/`, `src/benchmark/comparison/`, `src/benchmark/statistics/`, and associated test files.

---

## Decision D019 — Phase 4F.1 Scientific Evaluation Remediation

- **Date:** 2026-07-23
- **Decision ID:** D019
- **Status:** IMPLEMENTED
- **Category:** Scientific Remediation
- **Description:** Execute Phase 4F.1 — Scientific Evaluation Remediation. Close 5 scientific gaps identified by the Phase 4F independent audit: aggregate_run_records full implementation, paired bootstrap CI for H1, BH/Holm multiple-comparison corrections, NI sensitivity margins at 0.03/0.10, generalized binomial CI.
- **Rationale:** The Phase 4F audit found that the implementation covered approximately 70% of the frozen statistical plan. The remaining gaps were design-level issues that could be remediated without protocol amendment.
- **Alternatives considered:**
  - Leave gaps as-is and proceed to Kaggle — rejected because the gaps affect statistical validity of H1 and H2
  - Amend the frozen protocol — rejected because the gaps were implementation gaps, not protocol conflicts
- **Implementation scope:**
  - `aggregate_run_records` full implementation (micro + macro equal-weight)
  - `paired_bootstrap_ci()` matching on (repository, scenario, repetition)
  - `benjamini_hochberg()` + `holm_correction()` procedures
  - `non_inferiority_test()` with `sensitivity_margins=(0.03, 0.10)`
  - `binomial_ci()` generalized z-score via `scipy.stats.norm.ppf`
  - Bug fix: BH implementation (descending sort → ascending + step-down)
  - 31 new tests; 441 total
- **Design decisions:**
  - Macro aggregation uses equal-weight repository averaging (not scenario-count-weighted) per protocol
  - Paired analysis requires ≥ 2 matched cells to compute bootstrap CI
  - BH uses ascending sort + step-down monotonicity (standard Benjamini-Hochberg)
  - Holm uses step-down Bonferroni with early stopping
  - NI sensitivity returns dict mapping margin → bool for multi-margin evaluation
- **Quality gates:**
  - Ruff: 0 violations ✅
  - Mypy strict: 0 errors (src) ✅
  - Pytest: 441/441 passed ✅
  - pip check: no broken requirements ✅
- **Impact:** Protocol coverage increased from 9/19 to 14/19 implemented-and-validated requirements. The project is ready for Kaggle smoke execution.
- **Evidence:** `reports/PHASE4F_1_SCIENTIFIC_REMEDIATION_REPORT.md`, updated `reports/PHASE4F_INDEPENDENT_SCIENTIFIC_AUDIT.md`.

---

## Decision D020 — Kaggle Smoke Pass

- **Date:** 2026-07-23
- **Decision ID:** D020
- **Status:** IMPLEMENTED
- **Category:** Engineering Validation
- **Description:** Execute real Kaggle smoke run with Qwen2.5-Coder-7B-Instruct to validate deployment before pilot/research. Two engineering fixes were required before smoke could pass: failure propagation (real Qwen errors, token_usage, smoke-stage tagging) and graph wiring (ProfileGraphBuilder, capabilities design, NullLLMBackend for non-LLM strategies).
- **Rationale:** The frozen protocol requires real Qwen execution on Kaggle. Smoke must pass before pilot and research profiles can be executed. Previous dry-run and mock validation on local machine could not verify real model inference, GPU, or Kaggle deployment.
- **Alternatives considered:**
  - Proceed directly to pilot without smoke — rejected because smoke validates infrastructure with minimal cost/time
  - Run smoke locally — rejected because local LLM inference is forbidden (no torch/transformers locally)
- **Fix 1 — Failure Propagation** (branch `fix/real-qwen-failure-propagation`):
  - `models.py`: Added `token_usage` fields to `RunRecord`; added `stage` field (`smoke`, `pilot`, `research`)
  - `agent.py`: Removed blanket `except Exception`; specific exception handling only
  - `runner.py`: Prediction errors for failed strategies → failed status
  - `repair.py`: Preserve `prediction_errors` for failed runs
  - `kaggle_qwen_backend.py`: Lifecycle logging (`__init__`, `generate`), GPU preflight check, `after_success` returns `LLMResponse`
  - Merged at `b08bb55`
- **Fix 2 — Graph Wiring** (branch `fix/kaggle-graph-strategy-wiring`):
  - `graph/builder.py`: `ProfileGraphBuilder` that builds graph from profile scenario
  - `pipeline.py`: `NullableBackend` → `NullLLMBackend` for strategies that don't need LLM
  - `runner.py`: Accept `NullableBackend` as backend type
  - `mock_backend.py`: Added `NullLLMBackend` (raises if called)
  - Strategies: agent, compiled_ai, selective, code_plan accept optional `dependency_graph` parameter
  - `seven_arm_benchmark.py`: `STRATEGY_CAPABILITIES_DESIGN` replaces `STRATEGY_LLM_DESIGN`; `describe_capabilities()` reports `needs_llm`, `needs_graph`, `graph_type`; `build_dependency_graph()` builds from profile or falls back to minimal artifact graph
  - Merged at `e8aefc5` → main at `0c58250`
- **Results:**
  - Kaggle real smoke passed twice
  - 7/7 strategy arms succeeded
  - Real Qwen2.5-Coder-7B-Instruct inference confirmed (325 prompt + 19 completion tokens)
  - Smoke evidence is non-publication (engineering validation only)
  - 504/505 tests pass (1 skipped: torch import); ruff 0 violations; mypy 0 errors (src)
- **Impact:** Kaggle deployment validated. Qwen inference pipeline proven. Tag `v0.7.0-smoke-passed` created at `0c58250`. Next task: implement checkpoint/resume for long-running profiles.
- **Evidence:** Tag `v0.7.0-smoke-passed` at commit `0c58250` (main). `reports/latest_phase_report.md` updated.

---

## Decision D021 — Canonical Structure Remediation and Selective-Update Ledger

- **Date:** 2026-07-24
- **Decision ID:** D021
- **Status:** IMPLEMENTED
- **Category:** Structure / Governance
- **Description:** Execute Phase 3.7 — Canonical Structure Remediation. Merge audit documentation, implement deterministic bundle builder `scripts/build_upload_bundle.py`, populate and validate inner `kaggle_upload/` (72 code files, 29 data files, 1 notebook), remove forbidden items (`.git/`, caches, egg-info), add disposable artifacts to `.gitignore`, delete `_auto_resume_temp/` and `benchmark-results.zip`, update all architecture documentation to IMPLEMENTED/ADOPTED status, establish `project/selective_updates/` ledger with SU-0001 record, prepare outer duplicates for deletion.
- **Rationale:** The audit revealed structural drift: inner bundle was empty/polluted, outer bundle was stale, no automated bundle generation, no change ledger. Remediation ensures reproducible deployment bundles and traceable change management.
- **Alternatives considered:**
  - Manual bundle maintenance — rejected as error-prone and caused current drift
  - Keep outer bundle as canonical — rejected because outer is outside Git root and cannot be versioned with project
- **Implementation scope:**
  - `scripts/build_upload_bundle.py` (deterministic, self-verifying)
  - `.gitignore` additions: `_auto_resume_temp/`, `benchmark-results.zip`, `**/__pycache__/`, `*.pyc`, `*.egg-info/`
  - `project/kaggle_upload/` rebuilt: code (72 files), data (29 files), notebooks (1 file)
  - Documentation updates: PROPOSED_CANONICAL_PROJECT_STRUCTURE.md, IMPLEMENTED_ARCHITECTURE_BASELINE.md, SELECTIVE_PROJECT_UPDATE_POLICY.md, SOURCE_OF_TRUTH_MATRIX.md, SYSTEM_STATE.md, START_HERE.md, PROJECT_HANDOFF.md
  - Selective-update ledger: `project/selective_updates/` with README.md, CHANGE_INDEX.md, ARTIFACT_IMPACT_MAP.md, templates/CHANGE_RECORD_TEMPLATE.md, records/SU-0001-canonical-structure-remediation.md, metrics/change_metrics.jsonl
- **Quality gates:**
  - Bundle builder: verification passed (0 errors)
  - Tests: pytest passes
  - Ruff: 0 violations
  - Mypy: 0 errors
  - Pip check: clean
- **Impact:** Reproducible Kaggle bundles; traceable change management; outer duplicates ready for deletion. Next task: selective `runs_dir` NameError fix (SU-0002).
- **Evidence:** Branch `chore/canonical-project-remediation`; `scripts/build_upload_bundle.py`; `project/kaggle_upload/`; `project/selective_updates/`

---

## Decision D022 — Selective runs_dir NameError Fix (SU-0002)

- **Date:** 2026-07-24
- **Decision ID:** D022
- **Status:** IMPLEMENTED
- **Category:** Bugfix / CLI
- **Description:** Fix NameError in `seven_arm_benchmark.py` where `runs_dir` was used but not defined in START_NEW path (line 957). The variable `output_dir` (defined at line 828 from `--output-dir` CLI argument) is the correct variable. Fix is minimal: replace `runs_dir` with `output_dir` at line 957.
- **Rationale:** The bug prevented CLI execution when `--auto-resume-hf` is not used (START_NEW path). RESUME and `--resume-from-hf` paths already used `output_dir` correctly. Fix is a single variable name change.
- **Alternatives considered:**
  - Define `runs_dir = output_dir` as alias — rejected as unnecessary indirection
  - Use `Path(args.output_dir).resolve()` inline — rejected as less readable
- **Implementation scope:**
  - `seven_arm_benchmark.py`: line 957 `runs_dir` → `output_dir`
  - `tests/unit/test_cli.py`: added `TestRunsDirBugFix` class with 2 regression tests
- **Quality gates:**
  - `python -m pytest tests/unit/test_cli.py`: 17 passed (2 new tests)
  - `python -m pytest tests/`: 613 passed, 2 skipped
  - Bundle builder: verification passed (0 errors)
  - All pre-existing lint/type issues unchanged
- **Impact:** CLI executes without NameError for START_NEW path. RESUME and `--resume-from-hf` paths unaffected. Bundle rebuilt and verified.
- **Evidence:** Branch `fix/su-0002-runs-dir-nameerror`; `scripts/build_upload_bundle.py`; SU-0002 record

---

## Decision D023 — Research Design V2 Freeze and Repository-Agent Baseline Audit

- **Date:** 2026-07-25
- **Decision ID:** D023
- **Status:** DOCUMENTED — Awaiting Researcher Review
- **Category:** Research Design / Documentation
- **Description:** Execute Research Design V2 Freeze and Repository-Agent Baseline Audit. Merge completed arm-to-protocol execution audit (`audit/arm-to-protocol-execution`) into `main`. Create `docs/research-design-v2` branch recording all researcher-approved experimental design decisions (RD-V2-01 through RD-V2-06). Audit current `RepositoryAgentStrategy` end-to-end and classify it. Define baseline acceptance criteria for iterative repository agent. Design shared regeneration executor for fair end-to-end comparison. Establish arm role/naming policy mapping legacy IDs to scientific roles. Define external dataset evaluation policy for Experiment D. Trace implementation dependency graph for SU-0010.
- **Rationale:** The arm audit revealed 4/7 arms have protocol mismatches (llm_by_design=True but no LLM attached), the measurement boundary excludes regeneration/repair, and the primary comparison (agent vs selective) is invalid for token-efficiency claims. RD-V2 restructures the experiment to compare a true iterative repository agent against the hybrid selective method, with honest labeling of current implementations.
- **Alternatives considered:**
  - Keep current design and amend protocol — rejected because it would legitimize name-only literature comparisons and invalid token-efficiency claims
  - Implement full literature reproductions — rejected as out of scope for this research cycle
- **Actions executed:**
  - Merged `audit/arm-to-protocol-execution` into `main` at commit `3a16596` (merge commit `3a16596` on main)
  - Created `docs/research-design-v2` branch
  - Authored 10 design documents:
    1. `reports/REPOSITORY_AGENT_BASELINE_AUDIT.md` — Current agent = `SINGLE_SHOT_LLM_SCOPE_BASELINE`
    2. `docs/REPOSITORY_AGENT_BASELINE_SPEC.md` — Iterative baseline spec (max 5 rounds, 30 files, 6 calls, 50K tokens)
    3. `docs/SHARED_REGENERATION_EXECUTOR_DESIGN.md` — Shared executor architecture (selection→plan→executor→patch→validate→repair)
    4. `docs/ARM_ROLE_AND_NAMING_POLICY.md` — Legacy→scientific role map, naming rules, compatibility
    5. `docs/EXTERNAL_DATASET_EVALUATION_POLICY.md` — Experiment D gate: license, ground truth, no leakage, local execution mandatory
    6. `reports/SU0010_IMPLEMENTATION_IMPACT_PLAN.md` — 11-node dependency graph, ~21 day estimate
    7. `docs/EXPERIMENTAL_DESIGN_V2.md` — Experiments A/B/C/D, hypotheses, arm roles, measurement
    8. `docs/END_TO_END_MEASUREMENT_BOUNDARY.md` — Per-stage token accounting (selection/regen/repair/validation)
    9. `reports/RESEARCH_DESIGN_V2_DECISION_REPORT.md` — Consolidated decision record
  - Updated state files (this log, TODO.md, SYSTEM_STATE.md, reports/latest_phase_report.md, reports/PROJECT_HEALTH_REPORT.md, docs/PROJECT_HANDOFF.md, docs/START_HERE.md, selective_updates/CHANGE_INDEX.md)
- **Approved Research Decisions (Frozen for RD-V2):**
  - RD-V2-01: Primary comparison = iterative repository agent vs hybrid selective (matched LLM, repo, change, params, tools, budget, repair, validation, quality)
  - RD-V2-02: Arm roles: repository_agent, hybrid_selective, single_shot_llm_scope, static_only, semantic_only, traceability_only, full_scope_reference, retrieval_planning_variant
  - RD-V2-03: Literature claims = related work/inspiration only; no head-to-head stats vs published scores
  - RD-V2-04: Measurement boundary = selection + regen + repair + validation with per-stage token accounting
  - RD-V2-05: Efficiency claims require matched correctness/quality
  - RD-V2-06: Experiment A (impact accuracy), B (e2e evolution), C (ablations), D (optional external transfer)
- **Impact:** Research Design V2 documented and ready for researcher review. No production code modified. SU-0010 (shared executor + types + validators) and SU-0011 (iterative repository agent) identified as required implementation tasks. Pilot and Research phases remain blocked pending SU-0010 completion and baseline agent implementation. Frozen protocol documents untouched — formal amendment may be needed before publication.
- **Evidence:** Branch `docs/research-design-v2` with 10 design docs; merge commit `3a16596` on `main`; updated state files.

---

## Decision D024 — PILOT-READY-01 Closure (Multi-Repo Selective Input Contracts)

- **Date:** 2026-08-10
- **Decision ID:** D024
- **Status:** IMPLEMENTED — CLOSED
- **Category:** Engineering (feature closure, branch `feat/pilot-ready-01`)
- **Description:** Close Pilot readiness by fixing the multi-repo selective input-contract defects found by the local Pilot readiness dry-runs: (A) `build_dependency_graph` reused ONE dependency graph built from the first repository's snapshot on mixed-repository plans — now fails closed on mixed repositories and `build_repository_dependency_graphs` builds one graph per repository (Pilot run loop uses `_dep_graphs[repository_id]`); (B) editable-path expansion applied globally instead of per repository profile — now per-repository `expand_editable_paths` in `src/benchmark/repositories/snapshot.py` (root discovery includes allowed-artifact pattern parents; per-profile allowlist; single `ProfileArtifactDescriptor.profile_id` invariant); (C) artifact-catalog normalization produced category-key descriptors for django CMS/Saleor — `_normalize_artifact_catalog`/`descriptors_from_profile` yield file-granular descriptors ⊆ per-repo editable universe; (D) stale real-smoke expectation — `STRATEGIES_WITH_MISSING_PREREQS = {"agent"}` in `tests/integration/test_real_smoke.py`. Added focused multi-repo production-path contract `tests/integration/test_pilot_multi_repo_production_path.py` (12 tests, repeated twice with no state leak). Frozen Pilot matrix unchanged (Qwen2.5-Coder-14B-Instruct / bnb-nf4 / 600s / 12 scenarios / 2 strategies / 2 repetitions = 48 cells; Todo / django CMS / Saleor).
- **Rationale:** The local dry-runs proved the old one-graph-per-plan model could not faithfully represent per-repository dependency universes; without the fix the frozen 48-cell Pilot would compare strategies over incorrect input universes, invalidating scientific claims.
- **Alternatives considered:**
  - Keep one merged graph with a repository-id field — rejected: would re-introduce cross-repository dependencies and violate per-repo editable-universe semantics
  - Force each repository into its own experiment plan — rejected: changes the frozen Pilot design
- **Impact:** Pilot input universes are now per-repository and file-granular; full suite 2,026 passed / 33 skipped / 0 failed; exact fresh 48-cell Pilot dry-run 48/48 deterministic green (config_hash `7ef6ffc7a2c0d369`, source_commit `34ecf78`); no scientific inputs (prompts/metrics/evaluators/thresholds/Ground Truth/matrix) changed; 5 pre-existing mypy + 3 pre-existing ruff findings recorded as debt. Pilot = NOT STARTED; next task = `PILOT-EXEC-01`; stable tag `v0.9.0-pilot-ready` after non-ff main merge.
- **Evidence:** Gates 1–7 (14 / 9 / 12×2 / static clean / 48-cell dry-run / 142 / 2,026); commit `34ecf78` pushed (local = remote); `reports/PILOT_READY_01_FINAL_REPORT.md`.

(End of file)

---

## Decision D025 - PILOT-EXEC-01 Execution Contract Pre-registration (Gate B)

- **Date:** 2026-08-10
- **Decision ID:** D025
- **Status:** PRE-REGISTERED (before any real Pilot model result)
- **Category:** Scientific (Pilot budget/execution pre-registration, branch `experiment/pilot-exec-01`)
- **Description:** Pre-register the frozen PILOT-EXEC-01 execution contract before any real Pilot model result is observed. Scientific matrix = 3 repositories (todo / djangocms / saleor) x 12 frozen scenario IDs (configs/pilot.yaml) x 2 strategies (iterative_repository_agent, selective) x 2 repetitions = 48 cells. Model = Qwen/Qwen2.5-Coder-14B-Instruct, quantization bnb-nf4, temperature 0. Per-run budget = 600s uniform timeout, max 3 attempts (initial + 2 repairs), max completion 4096 tokens/call, workflow-token ceiling 0 (unlimited for Pilot, per DA-09: budgets frozen AFTER Pilot). Stage budget = frozen 48-cell matrix; no performance-driven reruns; infrastructure retry policy = up to 3 retries with identical scientific inputs. Full contract recorded in docs/PILOT_EXEC_01_EXECUTION_CONTRACT.md.
- **Rationale:** Gate B of PILOT-EXEC-01 requires the budget/execution contract to exist BEFORE any real Pilot model cell so that no budget parameter can be tuned from observed outcomes (03_BUDGET_PREREGISTRATION.md).
- **Alternatives considered:** Freeze Main-study budgets before the Pilot - rejected: DA-09 requires measuring realistic Pilot token/call/time distributions first.
- **Impact:** No scientific inputs (prompts/metrics/evaluators/thresholds/Ground Truth/matrix/model/quantization/timeout/repair policy) changed. Pilot = NOT STARTED. Real Pilot launch deferred until the user confirms the actual Kaggle mounted model path and HF results repository ID.
- **Evidence:** docs/PILOT_EXEC_01_EXECUTION_CONTRACT.md; deployment freeze evidence in tests/integration/test_pilot_deployment_bundle.py (12 passed), bundled exact fresh 48-cell dry-run 48/48 (todo 16 / djangocms 16 / saleor 16; iterative_repository_agent 24 / selective 24; rep1 24 / rep2 24), full suite 2,038 passed / 33 skipped / 0 failed.

---

## Decision D026 - AI Account-Transfer Docs Reconciliation (docs-only)

- **Date:** 2026-08-22
- **Decision ID:** D026
- **Status:** IMPLEMENTED (docs branch `docs/account-transfer-handoff-v0919`, non-ff merge to main; NO new release tag)
- **Category:** Documentation / Account Transfer
- **Description:** Make a weaker AI/new account able to understand the CURRENT v0.9.19 project state without reading contradictory historical "current" sections. Added the single authoritative snapshot `docs/AI_ACCOUNT_TRANSFER_HANDOFF.md` (current truth, frozen protocol, exact 12 Pilot scenario IDs incl. djangocms-mod-005, release history/rejections, recurring errors + permanent guards, git/release invariants, OpenCode working rules, exact next action, source-of-truth hierarchy). Reconciled README.md, AGENTS.md, SYSTEM_STATE.md, TODO.md, docs/PROJECT_HANDOFF.md, docs/MASTER_IMPLEMENTATION_PLAN.md, reports/latest_phase_report.md, reports/PROJECT_HEALTH_REPORT.md, reports/PILOT_EXEC_01_FINAL_REPORT.md, reports/PILOT_EXEC_01_DEPLOYMENT_FREEZE.md: stale "CURRENT" labels marked HISTORICAL/SUPERSEDED; TODO.md converted to a short current board with the old content preserved as a read-only historical ledger. Current truth recorded: release = v0.9.19-pilot-exec-ready; tag peel == artifact source commit = 2305991442a4f965d44bb066bb00c0a459fc395a; main is a post-tag docs/evidence child; v0.9.19 trust/provenance GREEN; OpenCode full suite = 2330 passed / 34 skipped / 0 failed; Real Pilot NOT STARTED; next action = fresh Kaggle v0.9.19 target preflight, then launch the accepted 48-cell Pilot in the same session if all target gates pass; do NOT open v0.9.20 without real target evidence.
- **Rationale:** Multiple superseded "Current" sections across state files created contradictions for account transfer; a weaker AI needs one authoritative entry point plus clearly marked history.
- **Alternatives considered:** Rewriting/deleting historical sections - rejected: history is valuable evidence and ledgers must stay truthful and append-only.
- **Impact:** Docs-only. NO production code, tests, notebook, configs/manifests, scientific protocol, deployment artifact, or immutable tag changed. No new release tag.
- **Evidence:** Branch `docs/account-transfer-handoff-v0919`; docs/static sanity checks only (no full-suite rerun required for a docs-only change).

---

## Decision D027 - v0.9.20 Saleor Preflight Root-Cause Closure and Baseline-Flake Policy

- **Date:** 2026-08-24
- **Decision ID:** D027
- **Status:** IMPLEMENTED on branch `fix/pilot-v0920-saleor-preflight-root-closure` (v0.9.20-pilot-exec-ready CANDIDATE; stable tag NOT created yet)
- **Category:** Infrastructure / Test Harness / Release Policy
- **Description:** The real Kaggle v0.9.19 session failed at the Saleor fast capability gate with Pytest exit 5 (no tests collected) after every earlier stage passed; `v0.9.19-pilot-exec-ready` is REJECTED FOR PILOT LAUNCH. Root cause: `run_repo_preflight` concatenated a second `-m pytest` vector onto the already-resolved frozen primary command, so Pytest parsed `-m pytest` as a marker expression and collected nothing; the local suite was false-green because a substring-based fake runner returned success whenever the argv contained "test_create_checkout". Closed: (1) exact standalone gate argv + fail-fast invariant (`RuntimeError` unless exactly one `-m` and `argv[1:3] == ["-m", "pytest"]`); (2) exact-argv contract tests with recorded RED/GREEN proof (RED = 2 failed against the v0.9.19 line; GREEN = 36 passed after fix), target-proven on Linux CI run 32650273641 (gate PASS, exactly 1 nodeid collected, Todo/django CMS PASS); (3) substring mock replaced by exact-command validation rejecting duplicate `-m`, inherited primary paths, and the marker expression; (4) evidence-backed Saleor baseline-flake policy `pilot_saleor_baseline_flaky_profile.v1`: exact frozen nodeids only (never directory allowlists), profile-time serial-rerun PASS required for membership, runtime re-verification via current serial `-n 0` reruns, new nodeids / deterministic re-failures / missing cache all FAIL CLOSED, raw exit-code truth always preserved in command records; (5) profile emitted by `--emit-baseline-profile`, committed as `reports/pilot_saleor_baseline_flaky_profile.json`, shipped at `code/reports/` inside the bundle, wired fail-closed into the deployed preflight cell; (6) target-shaped no-model Linux preflight workflow `.github/workflows/pilot-preflight-target-shape.yml` whose raised per-command budget (14400 s; job cap 330 min) is CI harness headroom only — the frozen validation command/paths/notebook budget are unchanged.
- **Rationale:** Two weeks of Kaggle blockers share one process defect: releases were labeled execution-ready from component-mocked local greens without one target-shaped proof of each blocking command. The stable-tag policy is corrected to: `*-pilot-exec-ready` means all no-model preflight gates passed in target-shaped Linux CI, not merely local pytest green. The documented Gate 9 evidence (33/38/36 pristine order/pricing failures across three runs on the pinned snapshot) proves a strict non-zero=FAIL preflight can never reach execution-ready; the policy classifies ONLY that exact evidence-backed set without excluding any test or reducing scope.
- **Alternatives considered:** Skipping the full Saleor primary command, deleting failing tests, reducing frozen validation paths, changing the pin, or silently marking failures PASS — ALL REJECTED (explicitly forbidden). A broad directory allowlist — rejected (exact nodeids only).
- **Impact:** No scientific inputs changed (model, quantization, scenarios, strategies, repetitions, 48 cells, prompts, metrics, repository pins, timeout 600, max attempts, completion tokens, Ground Truth, regression-obligation scope). Known open seam documented for the NEXT task: per-cell generated-workspace validation resolves the full frozen Saleor command under `validation_timeout=180` (`seven_arm_benchmark.py`) and will surface during real Pilot Stage 3.
- **Evidence:** `reports/V0920_ROOT_CAUSE_CLOSURE_REPORT.md`; `reports/target-evidence/run-32650273641/`; CI runs 32650273641 (argv-fix target proof) and the baseline-profile evidence runs; RED/GREEN outputs recorded in this decision and the closure report.

---

## Decision D028 - v0.9.21 Per-Cell Validation Runtime Closure

- **Date:** 2026-08-24
- **Decision ID:** D028
- **Status:** IMPLEMENTED AND RELEASED (`v0.9.21-pilot-exec-ready` @ tag peel == artifact source commit == merge `e308047c9c05f38316d80ce565bac1b51d105bfa`)
- **Category:** Infrastructure / Execution Runtime / Release Policy
- **Description:** After v0.9.20 (Saleor preflight root-cause closure), an independent audit found that the scientific generated-workspace per-cell validation path had NO runtime parity with the pristine preflight proven GREEN by v0.9.20 — three launch blockers: B1 seven_arm_benchmark.py resolved every frozen validation command with sys.executable while the preflight uses provisioned per-repository interpreters (Todo benchmark python; django CMS pilot_envs/djangocms/bin/python; Saleor pilot_envs/saleor/.venv/bin/python); B2 FunctionalValidator.validate() had no environment parameter so benchmark_data/manifests/pilot_validation_commands.yaml frozen env (Saleor DATABASE_URL/CACHE_URL/SECRET_KEY/TZ) was discarded; B3 PipelineConfig hardcoded validation_timeout=180s while target-shaped evidence measured the full Saleor primary at 775.71s (later 941.42s). Closures: repeatable --validation-python repo_id=path flag with fail-closed parsing (duplicates/malformed/nonexistent rejected before model initialization; no silent sys.executable fallback via resolve_frozen_validation_runtime); validation_env propagated PipelineConfig -> RunnerConfig -> FunctionalValidator executing os.environ.copy() + overrides (parent never mutated); --validation-timeout explicit positive budget with Pilot notebook launch AND resume passing 1800s explicitly (legacy 180 default preserved for compatibility; scientific --timeout 600 untouched). Evidence: RED recorded (the v0.9.20 validator fails all four new env-propagation tests; old routing precondition proves silent sys.executable fallback); 24 new regression tests; full suite 2370 passed / 33 skipped / 0 failed; target-shaped Linux CI Gates 1-3 GREEN (run 32692489617: Gate 1 production FunctionalValidator real staged Todo/django CMS/Saleor targets exit 0 with provisioned interpreters + exact frozen env, Gate 3 resolution contract without substring mocks, Gate 2 Saleor full primary exit 0 in 941.42s < 1800s) and the complete no-model preflight GREEN on the final released source state (run 32694137255).
- **Rationale:** A correct generated workspace could not have been validated during the Real Pilot: Saleor dependencies are deliberately isolated from the benchmark/model interpreter, its frozen env was dropped, and 180s could not contain the measured suite. Launching v0.9.20 would have failed every Saleor cell at Stage 3.
- **Alternatives considered:** Installing repository dependencies into the model interpreter — rejected (breaks deliberate isolation). Raising validation_timeout above 1800 without evidence or making it unbounded — rejected (bounded/fail-closed required). Redesigning FunctionalValidator globally — rejected (minimal optional-env parameter only).
- **Impact:** No scientific inputs changed (model, quantization, scenarios, strategies, repetitions, 48 cells, prompts, metrics, repository pins, frozen validation command paths/scope, timeout 600, attempts, completion tokens, Ground Truth).
- **Evidence:** reports/V0921_PER_CELL_VALIDATION_RUNTIME_CLOSURE_REPORT.md; CI runs 32692489617 / 32694137255 (Gates 1-3 + full preflight GREEN); artifact dist/pilot-kaggle-upload.zip SHA-256 62e377467e225d336cbcaa70a2c610b5080e329e1a4e6578fbcbdc1af7dbee40; trust/provenance 0 mismatches; dry-run 48/48.

---

## Decision D029 - v0.9.22 Long-Context Attention Memory Closure

- **Date:** 2026-08-24
- **Decision ID:** D029
- **Status:** IMPLEMENTED ON BRANCH `fix/pilot-v0922-long-context-attention-memory-closure` — CANDIDATE, TARGET MEMORY PROOF PENDING (no stable tag until the real Kaggle 2x T4 12k probe PASSES)
- **Category:** Infrastructure / Model Runtime / Release Policy
- **Description:** The real Kaggle v0.9.21 model preflight passed repository preflight, dependencies, Qwen 14B BNB-NF4 load (`qwen_model_load[bnb-nf4]: PASS`), GPU-only device map, 2x Tesla T4, per-GPU headroom (min free 7.764 GiB) and the short generation probe, then FAILED at the long-context probe with CUDA OOM: 12,044 prompt tokens / 64-token output budget / failed allocation 21.62 GiB == exactly `12044*12044*40*4 bytes = 21.6153 GiB`, the full float32 40-head quadratic attention score matrix. Diagnosis: the effective runtime attention path materialized the math/eager fallback during prompt prefill (offloaded KV cache does not cover prefill attention; device_map=auto is not tensor parallelism). v0.9.21 Real Pilot REJECTED BEFORE LAUNCH (no Experiment ID / no RunRecord created; no stable tag moved; the v0.9.21 repository/per-cell fixes remain valid and are carried forward). Closures WITHOUT touching any scientific input: Task A explicit `attn_implementation="sdpa"` at from_pretrained; Task B fail-closed CUDA generation inside `sdpa_kernel([FLASH_ATTENTION, EFFICIENT_ATTENTION])` (math/eager fallback impossible; missing torch.nn.attention API on CUDA fails closed before generation); Task C canonical attention evidence (`requested/effective_attn_implementation`, `sdpa_kernel_policy=flash_or_efficient_no_math`) persisted in preflight JSON, rendered in the human table, enforced by a new fail-closed `attention_policy` check and by pilot launch authorization; Task D corrected OOM diagnosis (long-prompt OOM reports prompt-prefill attention evidence + free GiB and never advises completion-cap reduction; short-prompt OOM keeps the old advice); Tasks E/F regression-guard every prior memory fix (transformers==4.57.6 pin, NF4 low_cpu_mem_usage load, offloaded KV cache, GPU-only device map) and the unchanged 12000-token/64-token long-context gate.
- **Rationale:** The OOM arithmetic is exact proof of a quadratic float32 attention materialization that fused kernels would never allocate; only an explicit SDPA request plus a kernel allowlist can close both the silent-fallback root cause and its recurrence. Fail-closed beats fail-open because a silent math fallback reproduces the same OOM on target without any local signal.
- **Alternatives considered:** Raising completion cap or reducing prompt size — rejected (changes frozen scientific inputs and does not address prefill attention). Switching to flash-attention-only — rejected (T4 SM75 lacks FA2 support; SDPA efficient kernels are the correct target backend). Trusting device_map=auto or cache_implementation="offloaded" to bound prefill — rejected (target evidence disproved both).
- **Impact:** No scientific inputs changed (model Qwen2.5-Coder-14B-Instruct, quantization BNB-NF4, 12 scenarios, 3 repo pins, 2 strategies, 2 reps = 48 cells, prompts, Ground Truth, metrics, --timeout 600, --validation-timeout 1800, max attempts 3, completion cap 4096, 12000-token long-context gate, 64-token probe).
- **Evidence:** RED/GREEN proven (12 backend + 18 preflight contract tests failed against v0.9.21 code before the fix); full suite 2407 passed / 33 skipped / 0 failed; dry-run pilot profile 48/48 (unique IDs, 0 model calls, 0 tokens); report reports/V0922_LONG_CONTEXT_ATTENTION_MEMORY_CLOSURE_REPORT.md.

## Decision D030 - v0.9.22 GQA Microprobe, Notebook, and Export Integrity Closure (D1-D6)

- **Date:** 2026-08-27
- **Decision ID:** D030
- **Status:** IMPLEMENTED ON BRANCH `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure` — CANDIDATE, REAL T4 PROOF PENDING (no stable tag until the real Kaggle 2x T4 12k probe PASSES; return to the SAME v0.9.22 task if it fails, never spawn v0.9.23)
- **Category:** Infrastructure / Model Runtime / Notebook Provenance / Release Policy
- **Description:** Bounded correction D1-D6 on the v0.9.22 candidate (built on `ba08392552545baa15c10ae5db2e95ce7496a720` + the T4 GQA SDPA/preflight-observability closure). D1: `_gqa_microprobe_expand_kv` uses local tensor repeat-KV (`repeat_interleave` on the head axis), NOT a fabricated `torch.nn.functional.repeat_kv`; D2: the microprobe allocates Q/K/V explicitly on each target `cuda:<index>`, synchronizes the device after SDPA, records/verifies per-device evidence (exact geometry 40/8/8 -> 40/40/40, FP16, seq 68; FLASH+EFFICIENT only, MATH excluded) and `all_passed` only when every visible device passes finite+shape+device; D3: `pilot-repo-preflight-cell` restored to a 210-element newline-preserving source (was a 172-element all-comment no-op) that `compile("".join(source), ...)` succeeds on and whose AST carries executable microprobe + fail-closed `raise` + `_run_tee` nodes; D4: `_run_tee` enforces its deadline WHILE the child runs (terminate->kill->reap, bounded tail) instead of only after EOF; D5: em-dash mojibake (`â€"`) restored to proper em dashes (0 mojibake in canonical + bundled); D6: export rebuilt only after final commit/push and verified by fresh extraction (empty git status, extracted HEAD == report HEAD, origin ref == HEAD, artifact + sidecar match, trust freeze tracked & byte-identical). Frozen scientific contract UNCHANGED (model Qwen2.5-Coder-14B-Instruct, BNB-NF4, sdpa, kernel policy `flash_or_efficient_no_math` (MATH disabled), GQA compat `KAGGLE_SDPA_GQA_COMPATIBILITY = "repeat_kv_sm75"`, 12 scenarios, 3 pins, 2 strategies, 2 reps = 48 cells, prompts, Ground Truth, metrics, --timeout 600, --validation-timeout 1800, max attempts 3, completion cap 4096, 12000/64 gate).
- **Rationale:** The prior candidate's notebook `pilot-repo-preflight-cell` had been reduced to a no-op with a fabricated repeat-KV import and mojibake; D1-D5 restore a truthful, executable, deadline-bounded preflight that would actually exercise the GQA microprobe on target, and D6 guarantees the exported artifact matches the finally-pushed source.
- **Alternatives considered:** Keeping the fabricated `torch.nn.functional.repeat_kv` import and the no-op cell — rejected (non-executable, would silently skip the microprobe). Only enforcing the deadline after EOF in `_run_tee` — rejected (a hung child would never be reaped within budget).
- **Impact:** No scientific inputs changed. Supersedes the prior v0.9.22 candidate identity `de0c5bd8...`/`bfbc935f...`.
- **Evidence:** Full suite 2441 passed / 33 skipped / 0 failed; exact final-artifact dry-run 48/48 (48 unique IDs, repos 16/16/16, strategies 24/24, reps 24/24, 0 model calls/tokens, every record source commit == `f72ecda0e7dac10e81dae34daa6bb1610c94b9ee`); exact artifact `dist/pilot-kaggle-upload.zip` SHA-256 `ce40b33019feba58d8cabeef2244a765e157cdba4288a9d9ea2eb186de46a24d` (+ sidecar verified) built from source commit `f72ecda0e7dac10e81dae34daa6bb1610c94b9ee` via the idempotent two-pass finalizer with `--verify-source-provenance` (0 mismatches; `reports/pilot_notebook_trust_freeze.json` FROZEN); report reports/V0922_GQA_MICROPROBE_NOTEBOOK_EXPORT_INTEGRITY_CLOSURE_REPORT.md.

## Decision D031 - v0.9.22 Kaggle/GitHub Boundary Correction (D9.6)

- **Date:** 2026-08-29
- **Decision ID:** D031
- **Status:** IMPLEMENTED ON BRANCH `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure` — CANDIDATE, REAL T4 PROOF PENDING (no stable tag until the real Kaggle 2x T4 GQA microprobe + generation-deadline canary + short + 12k probe PASSES; the annotated `v0.9.22-pilot-exec-ready` tag is created and locally verified against the owner-controlled, locally verified source commit only after real preflight passes; return to the SAME v0.9.22 task if it fails, never spawn v0.9.23)
- **Category:** Infrastructure / Release Policy / Runtime Isolation
- **Description:** D9.6 corrects the Kaggle/GitHub boundary: the D9.5 runtime remote tag-peel gate (`verify_remote_annotated_tag_peel`, `KAGGLE_PUBLIC_CANONICAL_REMOTE`, `REMOTE_TAG_PROOF_TIMEOUT_SECONDS`, `PILOT_STABLE_TAG`) is REMOVED. Kaggle launch and resume NEVER contact GitHub (no `git ls-remote`, no token, no `GIT_*`). `validate_pilot_launch_authorization` (pure local evidence: preflight JSON, sdpa kernel policy, mandatory generation-deadline canary) is the ONLY pre-command gate and is wired into BOTH `pilot-launch-cell` AND `pilot-resume-cell` before command construction (the resume cell previously lacked the local authorization gate). The stable tag is owner-side only and locally verified against the owner-controlled, locally verified source commit after real preflight passes. RED: the D9.5 baseline left 10 boundary-test failures (tag-peel machinery in `preflight.py` + notebook; missing resume-cell authorization gate). GREEN: focused boundary + notebook/finalizer/provenance suites green; full acceptance 2538 passed / 33 skipped / 0 failed.
- **Rationale:** A Kaggle launch/resume gate that contacts GitHub is fragile and unnecessary: the repository visibility is owner-controlled and out of scope for the benchmark runtime, and the authorization gate needs only local evidence. Removing it lets Kaggle run fully offline from GitHub and keeps the release-tag verification as an owner-side, pre-launch action.
- **Alternatives considered:** Keeping the remote annotated-tag-peel gate and merely making it best-effort — rejected (a runtime GitHub/network dependency in Kaggle launch/resume is not acceptable; it would be fragile and could block a legitimate launch). Adding a GitHub token to Kaggle — rejected (never required; no credential is needed for the local authorization gate).
- **Impact:** No scientific inputs changed. Supersedes the D9 artifact `913e8065...`/source `9ea02b3...` and all earlier v0.9.22 candidates. D9.6_SOURCE_COMMIT `6ff1c93ed355b6dc73fa3ebd18ba6079ace39ab6`, exact artifact SHA-256 `03d8d0ae37b995a362ee90c53a1851588ad024f13ead033814399210ce54dfc4`, sidecar matches, FROZEN 0 mismatches, idempotent.
- **Evidence:** RED 10 boundary failures on the D9.5 baseline; full suite 2538 passed / 33 skipped / 0 failed; exact fresh-extraction bundled dry-run 48/48 (48 unique IDs, repos 16/16/16, strategies 24/24, reps 24/24, 0 calls/tokens; every record + `source_identity.json` == `6ff1c93...`); repo-wide runtime/notebook audit and current-truth doc regression pass; report reports/V0922_D9_6_KAGGLE_GITHUB_BOUNDARY_CLOSURE_REPORT.md.
## Decision D032 - v0.9.22 Notebook Markdown Cell-Labels Closure (D9.6 NBNAV)

- **Date:** 2026-08-29
- **Decision ID:** D032
- **Status:** IMPLEMENTED ON BRANCH `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure` - CANDIDATE, REAL 2x T4 PROOF PENDING (no stable tag until the real Kaggle GQA microprobe + generation-deadline canary + short + 12k probe PASSES; the annotated `v0.9.22-pilot-exec-ready` tag is created and locally verified against the owner-controlled, locally verified source commit only after real preflight passes; return to the SAME v0.9.22 task if it fails, never spawn v0.9.23)
- **Category:** Notebook Navigation / Documentation / Release Provenance
- **Description:** D9.6 notebook-navigation refinement on top of the D9.6 Kaggle/GitHub boundary correction: 11 exact Markdown navigation cells (`pilot-step-00..10-*md`, e.g. Step 04 model-preflight, Step 08 STOP boundary, Step 09 launch, Step 10 resume) were inserted between the (byte-identical, unchanged) 16 executable code cells in `notebooks/pilot_exec_01.ipynb` so Kaggle's Table of Contents names every operational stage and a visible pre-launch STOP boundary guards `pilot-launch`. Nothing scientific, nothing in production/runtime code, and not the Kaggle/GitHub boundary changed. New regression tests: `tests/integration/test_pilot_notebook_contract.py` (TestMarkdownNavigation, TestCodeCellsUnchangedFromBaseline, TestBundledNotebookParity) and `tests/integration/test_pilot_deployment_bundle.py` (TestPilotBundleKeepsMarkdownNavigation). Witnesses: notebook diff 126 insertions / 0 deletions; code cells compile 16/16; RED-to-GREEN established for the new tests.
- **Rationale:** Kaggle's Table of Contents renders only the notebook's active headers, so the 16 bare exec cells were not individually navigable and there was no visible guard before `pilot-launch`. Adding named Markdown stage headers and an explicit STOP boundary improves operator observability without touching any executable code-cell source.
- **Alternatives considered:** Renaming code cells or inserting more code cells - rejected (would change executable source). Adding the labels to the code cells' markdown comments only - rejected (invisible to Kaggle's ToC).
- **Impact:** No scientific inputs changed; D9.6 boundary correction carried forward unchanged (Kaggle launch/resume never contact GitHub; stable tag is owner-side and locally verified). New source commit `478261ff595d3d64ed9d5bab32d1cc90d7dabd77` (build `478261f`), exact artifact SHA-256 `edae1b7e5be7ebab642d1e3c068dda3842a8061b8b04ab84c027d43a38dc8c4a`, sidecar matches, FROZEN 0 provenance mismatches, idempotent; stable code/data/repository-snapshot/transport manifest hashes unchanged from D9.6; notebook_manifest_sha256 `9d3edac4c20c00ab73a1ecda10d52322a5c57756820ed03f3a6162615e19adb6`, deployed bundle notebook SHA `6720293b922e06a80ecdc44a6d16e5eb12cc777d23c24a7076d005872d7aba68` == canonical source blob. D9.6 artifact `03d8d0ae...`/source `6ff1c93...` SUPERSEDED (do not upload).
- **Evidence:** New notebook-nav/contract/bundle tests RED on baseline then GREEN; canonical + bundled notebooks compile 16/16; exact fresh-extraction bundled dry-run 48/48 (48 unique IDs, repos 16/16/16, strategies 24/24, reps 24/24, 0 calls/tokens; canonical `validate_pilot_dryrun_evidence` PASS — every record + `source_identity.json` == `478261f...` and build id `478261f`); full acceptance 2538 passed / 33 skipped / 0 failed (unchanged); report reports/V0922_D9_6_NOTEBOOK_MARKDOWN_NAVIGATION_CLOSURE_REPORT.md.
