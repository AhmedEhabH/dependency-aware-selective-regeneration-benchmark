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

## Decision D033 - v0.9.22 D9.6 Real 2x T4 Preflight PASS + Stable Tag Closure (PILOT-EXEC-01)

- **Date:** 2026-08-30
- **Decision ID:** D033
- **Status:** COMPLETE - real exact-artifact 2x T4 Kaggle preflight PASSED on 2026-08-30; annotated stable tag `v0.9.22-pilot-exec-ready` CREATED and PUSHED (peels to `478261ff595d3d64ed9d5bab32d1cc90d7dabd77`, tag object `fdcb409670e040a287811840ddbcab475816a7e5`); the real 48-cell Pilot has NOT started (only Step 8 `pilot-launch-cell` remains, in the same still-live Kaggle session).
- **Category:** Release / Stable-Tag / Independent Evidence Audit
- **Description:** Executed the bounded task pack `PILOT-EXEC-01-V0922-D9-6-REAL-T4-PASS-STABLE-TAG-CLOSURE.md`. Gate A (git safety, artifact+sidecar = `edae1b7e...8c4a`) and Gate B (independent audit of the 3 evidence files `runs-2026-08-30-112728.zip` / `pilot_bundle-2026-08-30-112733.zip` / `pilot-exec (12).ipynb`) both FULL PASS: deployment identity `478261ff...`/`v0.9.22-pilot-exec-ready`/48 cells/Qwen 14B/BNB-NF4 with all five manifest hashes recomputed and matched; repo preflight overall PASS (Todo/django CMS/Saleor all PASS + Saleor PostgreSQL + Valkey/Redis reachable); T4 SDPA GQA microprobe PASS on both `cuda:0`/`cuda:1` (Tesla T4 cc 7.5, Q/K/V + output on the intended device, `repeat_kv_sm75`); `model_preflight.json.passed == true` with exactly 2 Tesla T4, `model_identity == qwen:14b-instruct-v1:bnb-nf4:cfg-cc9474140d25`, sdpa / `flash_or_efficient_no_math`, short generation PASS (17 tokens), generation-deadline canary PASS (`deadline_fired==true`/`finish_reason==timeout`/4 tokens), long-context PASS (12044 prompt / 64 completion tokens); bundled canonical `validate_pilot_dryrun_evidence` PASS (48/48 unique IDs, repo 16-16-16, strategies 24-24, reps 24-24, all call+token counters 0, source `478261ff...` + `v0.9.22-pilot-exec-ready` + build `478261f` + `dry-run:mock`); notebook cells 0-7 no error outputs, launch/resume/verify/export cells UNEXECUTED, only run_records.jsonl is the 48-record dry-run, no HF token leak. On PASS, Gate C created the annotated tag at exactly `478261ff...` and pushed to origin, proving `git cat-file -t`=`tag`, local + remote peeled target == `478261ff...` (tag object `fdcb409670e040a287811840ddbcab475816a7e5` == remote `refs/tags/v0.9.22-pilot-exec-ready`), verified with the configured authenticated origin credentials (no anonymous/public probe). The artifact REMAINS `edae1b7e...8c4a`; no rebuild/finalizer was run.
- **Rationale:** The real 2x T4 model preflight was the MANDATORY one-shot gate before creating the stable tag. All evidence proved the exact D9.6 artifact runs correctly on the true target (2x Tesla T4, SDPA GQA `repeat_kv_sm75`, long-context 12044/64 with sdpa no-math policy, generation-deadline canary), so the owner-side-only annotated tag was created at the exact artifact source commit per the release-provenance invariant and pushed to origin. GitHub privacy is irrelevant to Kaggle execution; GitHub is owner-controlled source/release storage only.
- **Alternatives considered:** Not creating the tag until the full 48-cell Pilot finishes - rejected (the frozen protocol tags at the tested exact artifact source commit after the model preflight PASS; the Pilot launch is a separate later step gated on the tag, per the notebook's Step 8 STOP boundary). Running an anonymous/public tag-readability probe - rejected (GitHub stays private; only configured origin credentials are used).
- **Impact:** No code, tests, notebook, artifact, freeze, dataset, prompt, or metric changed; the runtime code is unchanged and the full suite remains the previously accepted **2538 passed / 33 skipped / 0 failed** (carried). The stable tag `v0.9.22-pilot-exec-ready` now exists and peels to `478261ff595d3d64ed9d5bab32d1cc90d7dabd77` (supersedes all earlier v0.9.22 candidate states; never resume rejected `exp-20260828-151335`). The real Pilot remains NOT STARTED. Docs/reports updated to record the closure.
- **Evidence:** Independent Gate B audit of all 3 evidence files + canonical `validate_pilot_dryrun_evidence` PASS + `validate_pilot_launch_authorization` evidence checks PASS (local run failed only on HF_TOKEN env absence, expected and non-blocking since notebook cell 20 confirms retrieval); tag local `cat-file -t` = `tag`, local + remote peel == `478261ff...`; artifact + sidecar re-verified == `edae1b7e...8c4a`; clean tree; report reports/V0922_D9_6_REAL_T4_PASS_STABLE_TAG_CLOSURE_REPORT.md.

---

## Decision D034 - v0.9.22 D10 All-Failed Pilot Viability Closure (D10.1 truth-only)

- **Date:** 2026-08-31
- **Decision ID:** D034
- **Status:** IMPLEMENTED ON BRANCH `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure` - D10.1 truth-only closure COMMITTED AND PUSHED (no production changes in D10.1); D10.2-D10.7 follow in the same closure (protocol 1.1, timeout 1200, pilot-canary gate, standalone fail-closed resume, terminality/viability split, tests-first, freeze/export/stop).
- **Category:** Experiment Governance / Release Policy / Internal Runtime Contract
- **Description:** The one permitted real 48-cell Pilot launched from the exact D9.6 artifact `edae1b7e...8c4a` (source `478261ff...`, tag `v0.9.22-pilot-exec-ready`) on 2026-08-30 finished **48/48 terminal failures / 0 succeeded / 0 evaluator-passed** (`exp-20260830-134232`; protocol 1.0; ~23,610 s; 293 model calls; 820,631 total tokens; classifications scientific_budget_exhausted=33, model_output=8, build=7; 33 runs killed at the 600 s workflow deadline; iterative agent "no paths selected" on several Saleor/djangoCMS/Todo scenarios; resume failed standalone with `NameError: PILOT_OUTPUT_DIR not defined`). D10.1 records this rejection truthfully in a dedicated report and in the CURRENT TRUTH docs, demotes the D9.6 current truth to PRIOR TRUTH, and appends this decision. The rejected experiment is preserved verbatim and NEVER resumed or counted. The stable annotated tag `v0.9.22-pilot-exec-ready` is NOT moved/re-created/re-forced; it still peels to `478261ff...` but is RETIRED as a launch candidate. Scientific version remains v0.9.22 (never v0.9.23); scientific inputs unchanged.
- **Rationale:** A 100%-failure real Pilot is not scientific evidence and must be disclosed truthfully, not silently dropped or rerun. The blockquote documentation trail must be corrected so the next operator does not reuse the rejected artifact/tag as a launch basis, and internal runtime/operability defects (deadline censoring, non-standalone resume, terminality/viability conflation) are corrected with tests before any future launch.
- **Alternatives considered:** Deleting or force-moving the stable tag - rejected (the tag is immutable release metadata; the correct action is to retire it as a launch candidate while leaving it untouched). Silently rerunning the Pilot - rejected (would violate the one-shot launch rule and mask the rejection). Creating v0.9.23 - rejected (scientific inputs did not change; stays v0.9.22).
- **Impact:** Docs/reports + DECISION_LOG updated with the D10 all-failed Pilot repeatedly rejected PRESERVATION invariant; a new CURRENT TRUTH ledger entry. No production/scientific code changed in D10.1. The next REAL Pilot launch requires a NEW freshly-finalized artifact (protocol 1.1, 1200 s, corrected resume + terminality/viability) with its own real pilot-canary pass and its own tag decision.
- **Evidence:** Reproduced from the real evidence (`evidence/qwen14b_bnb_nf4_pilot_48_wsfix_478261f/run_records.jsonl`, `benchmark_summary.json`, `dashboard/dashboard_summary.json`, `failure_records.json`, `experiment_id.txt`, `source_identity.json`): 48 records / 48 unique IDs / 48 failed / 0 succeeded / 33 scientific_budget_exhausted / 8 model_output / 7 build / 293 calls / 731,678 prompt + 88,953 completion = 820,631 tokens / ~23,610 s; resume `NameError` confirmed in the D9.6 notebook cell; report reports/V0922_D10_ALL_FAILED_PILOT_VIABILITY_CLOSURE_REPORT.md.

## Decision D035 - v0.9.22 D11 Saleor-Inclusive Pilot-Canary Pre-Pilot Viability Gate Closure (PILOT-EXEC-01)

- **Date:** 2026-09-01
- **Decision ID:** D035
- **Status:** IMPLEMENTED ON BRANCH `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure` - D11 candidate artifact `v0.9.22-d11-candidate` BUILT + PROVENANCE-VERIFIED FROZEN (0 mismatches); NOT A RELEASE; NO STABLE TAG MOVE; the next REAL Pilot launch requires a real pilot-canary pass on this or a fresh exact candidate with its own tag decision.
- **Category:** Pre-Pilot Operational Topology / Runtime Contract / Release Provenance
- **Description:** D11 (B1-B4) corrects the pilot-canary operational topology WITHOUT touching any scientific input (model Qwen2.5-Coder-14B-Instruct, BNB-NF4, sdpa `flash_or_efficient_no_math`, GQA `repeat_kv_sm75`, 12 scenarios, 3 repo pins Todo/django CMS/Saleor, 2 strategies, 2 reps = 48 cells, prompts, Ground Truth, metrics, max attempts 3, completion cap 4096, 12000/64 gate, timeout 1200). B1: `pilot-canary` profile now represents ALL THREE Pilot repos as a 6-cell matrix (`todo-loc-001`/`djangocms-cross-007`/`saleor-loc-001` x 2 strategies x 1 rep); fixes the contradictory `blast_radii` filter that dropped `djangocms-cross-007` (cross_cutting) and made the canary uncallable; `validate_pilot_canary_evidence` defaults 3-repo / 6-cell (2/2/2 repos, 3/3 strategies, rep1=6). B2: `--protocol-version` CLI default is now profile-derived via `resolve_profile_protocol` (pilot/pilot-canary -> 1.1; smoke/research/scientific-smoke-v1/v2 -> 1.0; explicit override always wins - fixes the pre-D11 bug where the CLI default 1.1 leaked into dry-run and non-Pilot profiles). B3: `benchmark_data/manifests/pilot_validation_commands.yaml` `protocol_version` 1.0 -> 1.1 to mirror `configs/pilot.yaml` (parity enforced by new tests). B4: a new executable integration test (`tests/integration/test_pilot_canary_execution_path.py`) invokes the actual CLI in dry-run mode against canonical scenario data and proves the six-cell saleor-inclusive canary topology. All blockers tests-first (RED then GREEN).
- **Rationale:** The D10 canary default was internally 1-repo/1-cell and its blast_radii filter silently excluded the cross-cutting django CMS scenario, so the canary could not both represent Saleor (the most-at-risk repo: 15/16 real Pilot Saleor cells were 600 s budget-censored) and be executable. Saleor must be in the canary before any further 48-cell GPU spend. Protocol 1.1 must not leak into non-Pilot profiles, and the validation manifest must agree with the Pilot config.
- **Alternatives considered:** Keeping a todo/djangocms 2-repo canary without Saleor - rejected (Saleor's timeout/viability risk is the whole reason a canary exists). Hard-coding per-profile defaults in the CLI - rejected (must be a single profile-derived resolver so every profile is consistent). Leaving `pilot_validation_commands.yaml` at 1.0 - rejected (launch/resume argv would embed protocol 1.0 while the profile and config are 1.1).
- **Impact:** Scientific version stays v0.9.22 (never v0.9.23). No scientific input changed; the 48-cell Pilot matrix is bit-identical (canary becoming 6 cells is NOT a scientific matrix change). D10 candidate (`v0.9.22-d10-candidate`, archive `d468ee63...`) SUPERSEDED by the D11 candidate; the retired `v0.9.22-pilot-exec-ready` tag (peel `478261ff...`) and the `edae1b7e...8c4a` artifact are NOT reused. Never resume `exp-20260828-151335` (0 accepted RunRecords); `exp-20260830-134232` remains REJECTED. Builds `b07da1a` (code) -> `c1c892b` (notebook anchor refresh + freeze report) -> `224c5a9` (provenance-verified freeze report); source commit `c1c892bb6c11c7cc399dee8e6631ea73a33d61a6`; candidate tag `v0.9.22-d11-candidate`; exact artifact `dist/pilot-kaggle-upload.zip` SHA-256 **`4554dced6a438893ed01cbdbce9756613c0b0951459a43eb9a4a467edee4cb8a`** (+ sidecar verified); freeze `reports/pilot_notebook_trust_freeze.json` status FROZEN, 0 provenance mismatches.
- **Evidence:** Gates 1-6 PASS (dataset 152/4, prompt 85, pipeline smoke 289/1, source dry-run pilot 48/48 + canary 6/6, integration, metric 254/9); full suite **2585 passed / 33 skipped / 0 failed**; exact-artifact dry-runs with the bundled code/data/notebook: Pilot **48/48** (repos 16/16/16, strategies 24/24, reps {1:24,2:24}, 0 model calls, 0 tokens, protocol 1.1, canonical `validate_pilot_dryrun_evidence` PASS) and pilot-canary **6/6** (repos 2/2/2, strategies 3/3, rep1=6, 0 calls, 0 tokens, protocol 1.1); report reports/V0922_D11_PILOT_CANARY_SALEOR_INCLUSIVE_CLOSURE_REPORT.md.

## Decision D036 - v0.9.22 D12 Notebook Orchestration Fix Closure (PILOT-EXEC-01)

- **Date:** 2026-09-01
- **Decision ID:** D036
- **Status:** IMPLEMENTED ON BRANCH `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure` - D12 candidate artifact `v0.9.22-d12-candidate` BUILT + PROVENANCE-VERIFIED FROZEN (0 mismatches); NOT A RELEASE; NO STABLE TAG MOVE; the next REAL Pilot launch requires a real pilot-canary pass on this or a fresh exact candidate with its own tag decision.
- **Category:** Notebook Orchestration / SCRIPT_PATH Definition Order
- **Description:** D12 fixes the verified in-flight blocker: `pilot-canary-cell` (cell 20) reads SCRIPT_PATH but only `dryrun-cell` (cell 22) defined it, so the canary could not run as an independent notebook stage (`NameError: name 'SCRIPT_PATH' is not defined`). The single canonical `SCRIPT_PATH = CODE_DIR / "seven_arm_benchmark.py"` + `FileNotFoundError` guard now lives in `pilot-archive-verify-cell` (cell 4) after CODE_DIR existence checks and before ANY use; the duplicate def/guard in the dry-run cell was deleted (exactly-one definition cell enforced by new integration tests `TestD12ScriptPathOrchestration`, 4 tests). RED proven: 4 tests FAILED on the D11 baseline (SCRIPT_PATH first defined in cell 22 but used in cell 20; pre-definition uses `[20]`; archive-verify cell missing the canonical def+guard; ast.parse passed). GREEN after fix: 4/4 pass. Nothing scientific changed (scenarios, prompts, Ground Truth, metrics, model, quantization, sdpa/GQA, 12 scenarios, 3 repo pins, 2 strategies, 2 reps = 48 cells, protocol 1.1, timeout 1200).
- **Rationale:** The canary cell must be runnable as an independent stage (after the archive-verify cell provisions code+data, before the full 48-cell pilot launch). Without a SCRIPT_PATH definition before cell 20's first use, any notebook execution starting at the canary cell raises NameError and blocks the pre-pilot canary gate.
- **Alternatives considered:** Defining SCRIPT_PATH in cell 20 (the canary cell itself) - rejected (introduces a second definition point and the exact-one-definition invariant would be harder to enforce). Defining SCRIPT_PATH at notebook top-level via a preceding cell that doesn't exist in the current 27-cell structure - rejected (would require restructuring cells beyond the minimal D12 scope).
- **Impact:** Scientific version stays v0.9.22 (never v0.9.23). No scientific input changed; the 48-cell Pilot matrix is bit-identical. D11 candidate (`v0.9.22-d11-candidate`, archive `4554dced...`) SUPERSEDED by the D12 candidate; the retired `v0.9.22-pilot-exec-ready` tag (peel `478261ff...`) and the `edae1b7e...8c4a` artifact are NOT reused. Builds `83d15dd` (code + RED test) -> `84acb8b` (notebook anchor refresh + freeze report) -> `f960abe` (provenance-verified freeze report) -> `fb84073` (release-tag constants); source commit `84acb8bb01bbae28d6bab260d029af539c80a229`; deployed build id `84acb8b`; created-utc 2026-09-01T18:40:35+00:00; candidate tag `v0.9.22-d12-candidate`; exact artifact `dist/pilot-kaggle-upload.zip` SHA-256 **`812d37555a42f8fbdfbbb2e5441c814fb733cfd424ca75c810ead96a0bc4346a`** (+ sidecar verified); freeze `reports/pilot_notebook_trust_freeze.json` status FROZEN, 0 provenance mismatches.
- **Evidence:** Gates 1-6 PASS (G1 dataset 267/4, G2 prompt 101/4, G3 pipeline smoke 722/14, G4 source dry-run pilot 48/48 + canary 6/6 + exact-artifact pilot 48/48 + canary 6/6, G5 integration 258, G6 metric 329/10); full suite **2589 passed / 33 skipped / 0 failed** (D11 was 2585/33/0; +4 exactly = the new regression); exact-artifact dry-runs (bundled code/data, protocol 1.1, every record + `source_identity.json` == `84acb8b...` + `v0.9.22-d12-candidate` + build `84acb8b`): Pilot **48/48** (repos 16/16/16, strategies 24/24, reps {1:24,2:24}, 0 calls/tokens) and pilot-canary **6/6** (repos 2/2/2, strategies 3/3, rep 1:6, 0 calls/tokens); canonical `validate_pilot_dryrun_evidence` PASS; report `reports/V0922_D12_NOTEBOOK_ORCHESTRATION_FIX_CLOSURE_REPORT.md`.


## Decision D037 - v0.9.22 D13 Canary Production-Scale Execution Closure (PILOT-EXEC-01)

- **Date:** 2026-09-02
- **Decision ID:** D037
- **Status:** IMPLEMENTED ON BRANCH `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure` - D13 candidate tag `v0.9.22-d13-candidate` SUPERSEDES the D12 candidate; NOT A RELEASE; NO STABLE TAG MOVE; the next REAL Pilot launch requires a real pilot-canary pass on this or a fresh exact candidate with its own tag decision, AND a closed B4 semantic-executability gate.
- **Category:** Production-Scale Execution Defects / Source-Editing / Token Budgets / Repository-Aware Migrations / Pilot Runtime Contract
- **Description:** D13 closes the root-cause blockers exposed by the 2026-09-02 real pilot-canary (6 planned/completed, 6 failed, 0 succeeded, ~5525 s, protocol 1.1, 2x Tesla T4; 4 deadline-censored and 2 Todo build-in-completion failures) WITHOUT touching any scientific input (model Qwen2.5-Coder-14B-Instruct, BNB-NF4, sdpa `flash_or_efficient_no_math`, GQA `repeat_kv_sm75`, 12 scenarios, 3 repo pins Todo/django CMS/Saleor, 2 strategies, 2 reps = 48 cells, prompts, Ground Truth, metrics, timeout 1200). B1: exact-patch source editing (`<<<<<<< SEARCH ... ======= ... >>>>>>> REPLACE`, multi-block, fail-closed, exact string match, no regex/fuzzy) shared by BOTH strategies via `ExecutorConfig.exact_patch` (replaces complete-file regeneration whose O(file) cost caused a 56k-char djangoCMS file to consume ~1154 s for only 1839 completion tokens; djangocms-cross-007 was deadline-censored). B2: separate agent-control-plane output cap (`AGENT_CONTROL_MAX_COMPLETION_TOKENS = 512`) from the source-edit cap (`control_cap = min(max_completion_tokens_per_call, AGENT_CONTROL_MAX_COMPLETION_TOKENS)` applied to `analyze_impact` and `revise_plan`). B3: repository-aware migrations - added `migration_directory: str = "todo/migrations"` to the `Scenario` dataclass and threaded it through `run_post_generation_command` (per-repo `validation_python` interpreter binding deferred). B4 (DEFERRED, known-incomplete): fail-closed semantic executability gate for all 12 Pilot scenarios (todo-loc-001 hidden priority-filter test, saleor-loc-002 `is_featured` absent, saleor-cross-007 create capability). Protocol: Pilot-only 1.1 -> 1.2 via `resolve_profile_protocol` (pilot/pilot-canary = 1.2; smoke/research/scientific-smoke-v1/v2 = 1.0; explicit override wins); preflight validators (preflight.py:1243, 1711), `configs/pilot.yaml`, `pilot_validation_commands.yaml`, and `build_pilot_upload_bundle.py` FROZEN_PROTOCOL_VERSION bumped; non-Pilot stays 1.0 and generic "1.1" source defaults not Pilot-coupled remain intact.
- **Rationale:** The 2026-09-02 real canary proved complete-file regeneration and unbounded/whole-file source editing violate the per-cell workflow deadline and token budget on large generated files, and that agent-control reasoning must not consume the source-edit allowance. Migrations must be repository-aware and every Pilot scenario must be semantically executable on the pinned base before another 48-cell GPU spend. The Pilot runtime contract must reflect the corrected production-grade execution semantics, so the Pilot-only protocol advances 1.1 -> 1.2.
- **Alternatives considered:** Keeping complete-file regeneration - rejected (proven it consumes ~1154 s / 1839 tokens on a 56k-char file and is deadline-censored). Raising the timeout - rejected (timeout stays 1200 s; the fix is cheaper editing, not more time). Reverting to no exact-patch and only tuning the selective strategy - rejected (the bug is production-scale execution; B6 explicitly says do NOT tune Hybrid Selective based on the Saleor outcome). Bumping protocol globally - rejected (only Pilot/canary moved to 1.2; non-Pilot stays 1.0).
- **Impact:** Scientific version stays v0.9.22 (never v0.9.23). No scientific input changed; the 48-cell Pilot matrix is bit-identical. D12 candidate (`v0.9.22-d12-candidate`, archive `812d3755...`) SUPERSEDED by the D13 candidate; the retired `v0.9.22-pilot-exec-ready` tag (peel `478261ff...`) and the `edae1b7e...8c4a` artifact are NOT reused; never resume `exp-20260828-151335` (0 accepted RunRecords); `exp-20260830-134232` remains REJECTED. New artifacts: `src/benchmark/execution/exact_patch.py`, `tests/unit/execution/test_exact_patch.py`, `tests/unit/execution/test_exact_patch_executor.py`, `tests/unit/strategies/test_agent_control_cap.py`. Candidate tag `v0.9.22-d13-candidate`. Closure artifact freeze + provenance verification and exact pilot 48 / canary 6 dry-runs were NOT run in this local closure; B4 executability gate is DEFERRED (known-incomplete) so the D13 candidate is NOT a launch basis.
- **Evidence:** Full unit/execution/strategy/pilot suites GREEN (768 passed / 27 skipped in the unit+execution+strategy+pilot subset; integration 37 passed on test_su0011_iterative_agent + test_pilot_multi_repo_production_path); preflight + pilot_canary_viability 159 passed after bumping preflight validators (preflight.py:1243, 1711) to 1.2; mypy clean on changed source; ruff clean on changed files; Python compile clean. Report: `reports/V0922_D13_CANARY_PRODUCTION_SCALE_EXECUTION_CLOSURE_REPORT.md`.


## Decision D038 - v0.9.22 D13r1 Canary Launch-Readiness Finalizer Closure (PILOT-EXEC-01)

- **Date:** 2026-09-03
- **Decision ID:** D038
- **Status:** IMPLEMENTED ON BRANCH `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure` - D13r1 candidate tag `v0.9.22-d13r1-candidate` SUPERSEDES the D13 candidate; CANARY_LAUNCH_BASIS=YES; FULL_48_LAUNCH_BASIS=NO; NOT A RELEASE; NO STABLE TAG MOVE; no Kaggle run in this closure.
- **Category:** Canary Launch-Readiness Finalization / Pre-Model Semantic Executability / Repository-Aware Migrations / Frozen Execution Identity
- **Description:** D13r1 FINALIZES the D13 closures WITHOUT touching any scientific input (model Qwen2.5-Coder-14B-Instruct, BNB-NF4, sdpa `flash_or_efficient_no_math`, GQA `repeat_kv_sm75`, 12 scenarios, 3 repo pins, 2 strategies, 2 reps = 48 cells, prompts, Ground Truth, metrics, timeout 1200). F1: the fail-closed semantic-executability gate is WIRED into the real pilot/pilot-canary PRE-MODEL launch path - `validate_pilot_launch_authorization` now runs `validate_pilot_semantic_executability` (scenario_dir + repository_roots) when a scenario_dir is supplied; the pilot-canary cell gates the 3 canary scenarios BEFORE any model call; the CLI `--require-launch-authorization` passes scenario_dir/scenario_ids; so the FULL 48-cell Pilot is NOT a launch basis while any scenario is semantically unexecutable (saleor-loc-002 `is_featured` known-absent, 7 unregistered scenarios fail closed). F2: per-repo `migration_directory` metadata added ONLY to the 3 canary scenarios (todo-loc-001 `todo/migrations`, saleor-loc-001 `saleor/product/migrations`, djangocms-cross-007 `cms/migrations`). F3: migration execution decoupled from `evaluator_asset` (a migration-only scenario with post_generation_command/require_new_migration and NO evaluator_asset is a valid configuration - the pre-F3 harness-defect "Scenario metadata requires evaluator" path for migration-bearing scenarios is removed). F4: the exact-patch repair-prompt contradiction removed - `REPAIR_CONTEXT_PROMPT_TEMPLATE` no longer instructs complete-file regeneration in patch mode (it now defers to the stated per-mode output contract). F5: `exact_patch` + `agent_control_max_completion_tokens` in the frozen config/provenance identity - `source_identity.json`, bundle identity, notebook `FROZEN_DEPLOYMENT` `{exact_patch: True, agent_control_max_completion_tokens: 512}`, `configs/pilot.yaml`, and ENFORCED by the dry-run + canary evidence validators.
- **Rationale:** The D13 canary-launch-readiness record explicitly deferred B4 (semantic executability NOT wired into any launch/validator path) and left the D13 candidate as NOT a launch basis. D13r1 closes exactly those remaining blockers so the canary (but not the full 48-cell Pilot) can be a genuine launch basis after a real target preflight. Keeping the gate PRE-MODEL (before any model call) means a semantically unexecutable scenario is caught on the ground before any GPU spend. Decoupling migration from evaluator_asset makes repository-aware migration-only scenarios operationally valid. Freezing exact_patch + the agent-control cap into the provenance identity makes the execution contract auditable from the artifact itself.
- **Alternatives considered:** Wiring the semantic gate into `validate_pilot_canary_evidence` only (post-run) - rejected (a pre-model gate is strictly earlier and never spends a model call). Expanding the semantic registry to all 12 Pilot scenarios - REJECTED per task (do NOT expand the all-12 semantic registry; the 7 unregistered scenarios FAIL CLOSED, which is the desired NON-launch-basis property for the full 48). Implementing Saleor cross-create support - REJECTED (explicitly out of scope). Tuning Selective / changing Qwen/Kaggle/timeout - REJECTED (B6; scientific inputs untouched).
- **Impact:** Scientific version stays v0.9.22 (never v0.9.23). No scientific input changed. Source commits: `41ceee3` (F1-F5 code + tests) -> `48e694d` (release-tag constants aligned to v0.9.22-d13r1-candidate) -> `6bc946a` (notebook anchor refresh + freeze report) -> `4acceba` (provenance-verified freeze report). **Candidate artifact** `dist/pilot-kaggle-upload.zip` SHA-256 **`9f120412cfef5dfb7f66a57c03380fc5149b45b20d53c60d623d1e81bc203461`** (+ sidecar verified) from source commit `6bc946a…` tag `v0.9.22-d13r1-candidate`; `--verify-source-provenance` **0 mismatches**; idempotent same-input rerun (archive SHA unchanged). The retired `v0.9.22-pilot-exec-ready` tag (peel `478261ff...`) and the `edae1b7e...8c4a` artifact are NOT reused; the D13 candidate (`v0.9.22-d13-candidate`, archive `6edd487a...`) is SUPERSEDED by this D13r1 candidate. Never resume `exp-20260828-151335`; `exp-20260830-134232` remains REJECTED.
- **Evidence:** Six gates GREEN. G1 dataset **333 passed / 4 skipped**; G2 prompt **132 passed / 4 skipped**; G3 pipeline smoke **930 passed / 23 skipped**; G4 source dry-runs Pilot **48/48** + canary **6/6** (0 calls, 0 tokens, protocol 1.2, canonical `validate_pilot_dryrun_evidence` PASS) + exact-artifact dry-runs Pilot **48/48** + canary **6/6** (repos 2/2/2, strategies 3/3, rep 1:6, 0 calls/tokens, source_commit `6bc946a`, exact_patch True, agent_control 512) + bundled-exact canary SEMANTIC PRE-MODEL gate **PASS** on the 3 canary scenarios; G6 metrics **194 passed**; G5 full suite **2650 passed / 34 skipped / 0 failed**. Production-shape tests added: 60k/85k short-patch (test_exact_patch), repair-prompt exact-patch contract (test_regeneration), semantic pre-model gate + launch-auth wiring (test_preflight), 3-repo migrations (test_scenarios_loader), migration-evaluator decoupling (test_runner/test_r3d_wiring). Report: `reports/V0922_D13R1_CANARY_LAUNCH_READINESS_CLOSURE_REPORT.md`.

## Decision D039 - v0.9.22 D13R2 Last Canary Hotfix Closure (PILOT-EXEC-01)

- **Date:** 2026-09-03
- **Decision ID:** D039
- **Status:** IMPLEMENTED ON BRANCH `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure` - D13R2 candidate tag `v0.9.22-d13r2-candidate` SUPERSEDES the D13r1 candidate; CANARY_LAUNCH_BASIS=YES; FULL_48_LAUNCH_BASIS=NO; NOT A RELEASE; NO STABLE TAG MOVE; no Kaggle run in this closure.
- **Category:** Canary Hotfix / Migration Executability Metadata / Semantic Migration Gate / Post-Generation Env Parity / Protocol-1.2 Config Identity
- **Description:** D13R2 is the LAST canary hotfix on the same D13 line (no D14) and closes the four audited defects H1-H4 WITHOUT touching any scientific input (model Qwen2.5-Coder-14B-Instruct, BNB-NF4, sdpa `flash_or_efficient_no_math`, GQA `repeat_kv_sm75`, 12 scenarios, 3 repo pins, 2 strategies, 2 reps = 48 cells, prompts, Ground Truth, metrics, timeout 1200). H1: the 3 canary scenarios (todo-loc-001, djangocms-cross-007, saleor-loc-001) now carry COMPLETE executable migration metadata - `post_generation_command` `python manage.py makemigrations todo|cms|product --noinput` + `require_new_migration: true` (was empty/False, so the runner never executed migration generation and could reproduce the previous Todo build failure). H2: the semantic gate now PROVES migration executability for the 3 canary scenarios via an explicit frozen map `_CANARY_MIGRATION_FIXTURES` (require_new_migration True + exact frozen command + exact `migration_directory`, fail-closed on any mismatch; never inferred from English text) - this propagates into the pre-model launch path. H3: migration generation now receives the frozen repository validation environment - `run_post_generation_command(..., env=...)` merges `validation_env` into the child env exactly like `FunctionalValidator` (`os.environ.copy()` + update; parent `os.environ` never mutated); the Runner passes `self._config.validation_env`. H4: `_compute_config_hash` now includes `exact_patch` + `agent_control_max_completion_tokens` (changing either changes the hash; D13r1 F5 contract).
- **Rationale:** The independent audit of the frozen D13r1 artifact found that D13r1 had added only migration directories, not executable migration metadata, so the migration stage could silently not run (H1); the semantic gate validated pinned-base sentinels only and returned PASS with empty commands (H2); the migration subprocess missed the frozen repository validation env required by Saleor (DATABASE_URL/CACHE_URL/SECRET_KEY/TZ) (H3); and config identity ignored the Protocol-1.2 execution controls (H4). All four are launch-readiness correctness defects on the canary line and are closed without any scientific input change.
- **Alternatives considered:** Inferring migration requirements from English scenario text at runtime - REJECTED (fail-closed frozen map is deterministic and auditable). Expanding the migration-executability registry to all 12 Pilot scenarios - REJECTED (Canary-only readiness; the 7 unregistered scenarios fail closed = desired non-launch-basis property). Adding a new env-merge mechanism instead of FunctionalValidator semantics - REJECTED (reuse the exact same child-env semantics for parity). Touching Qwen/Kaggle/timeout/Selective - REJECTED (scientific inputs untouched).
- **Impact:** Scientific version stays v0.9.22 (never v0.9.23). No scientific input changed. Source commits: `5daf88d` (Fix 1-4 code + tests) -> `87da8f3` (release-tag constants aligned to v0.9.22-d13r2-candidate) -> `fc1c7c8` (notebook anchor refresh + freeze report) -> `b7ebb22` (provenance-verified freeze report). **Candidate artifact** `dist/pilot-kaggle-upload.zip` SHA-256 **`65269528049b1f22f277c508f0b0db5b09d536e99fd31d306cfbbfb42e47ef9f`** (+ sidecar verified) from source commit `fc1c7c8...` tag `v0.9.22-d13r2-candidate`; two-pass finalizer `--verify-source-provenance` **0 mismatches**. The retired `v0.9.22-pilot-exec-ready` tag (peel `478261ff...`) and the `edae1b7e...8c4a` artifact are NOT reused; the D13r1 candidate (`v0.9.22-d13r1-candidate`, archive `9f120412...`) is SUPERSEDED by this D13R2 candidate and stays immutable historical evidence. Never resume `exp-20260828-151335`; `exp-20260830-134232` remains REJECTED.
- **Evidence:** Six gates GREEN. G1 dataset **276 passed / 4 skipped**; G2 prompt **77 passed**; G3 pipeline smoke **992 passed / 27 skipped**; G4 source dry-runs Pilot **48/48** + canary **6/6** (0 calls, 0 tokens, protocol 1.2, canonical `validate_pilot_dryrun_evidence` PASS) + exact-artifact dry-runs Pilot **48/48** + canary **6/6** (repos 2/2/2, strategies 3/3, rep 1:6, 0 calls/tokens, source_commit `fc1c7c8`, exact_patch True, agent_control 512) + bundled-exact canary SEMANTIC PRE-MODEL gate **PASS** on the 3 canary scenarios; G6 metrics **194 passed**; G5 full suite **2671 passed / 33 skipped / 0 failed**. New/updated tests: canary migration metadata + declared-only-on-3 (test_scenarios_loader), migration-executability fail-closed cases (test_semantic_executability), pre-model gate + no-backend-init (test_preflight), post-generation env parity (test_post_generation), config-hash controls (test_su0007). Report: `reports/V0922_D13R2_LAST_CANARY_HOTFIX_CLOSURE_REPORT.md`.

---

## Decision D040 - Scientific Reset: Retire Qwen14B / 2xT4 / old 48-cell track as the immediate scientific launch target (SCIENTIFIC-RESET-01)

- **Date:** 2026-09-04
- **Decision ID:** D040
- **Status:** ACCEPTED / FROZEN (researcher accepted the scientific-management decision). Documentation + decision-freeze only; NO runtime/model code changed; NO new scientific experiment started.
- **Category:** Scientific Direction / Research Management / Pre-Main Feasibility Gate
- **Description:** Qwen2.5-Coder-14B + Kaggle 2x T4 is RETIRED as the PRIMARY scientific inference path. The old 48-cell Pilot is NOT launched or repaired; no D14/D15 timeout or infrastructure engineering work is opened to force the old 48-cell matrix; the time-out is NOT increased. All previous runs, rejected experiments, canaries, candidate artifacts (D01 through D13R2), and the retired `v0.9.22-pilot-exec-ready` tag remain immutable **engineering feasibility evidence**. `exp-20260828-151335` (0 accepted RunRecords) is never resumed; `exp-20260830-134232` (48/48 terminal failures) remains REJECTED. The next scientific milestone is a pre-main Todo correctness-first micro-study (`SCIENTIFIC-MICROSTUDY-01`), not another release-readiness candidate.
- **Rationale:** The real execution evidence (48/48 terminal Pilot failures; 6/6 failed real canary; large-repo sustained-generation throughput limits; empty/fallback strategy-visible dependency graphs in djangoCMS/Saleor) shows the Qwen14B/T4 track no longer offers the fastest path to the first scientific result. Engineering feasibility has been demonstrated; scientific correctness evidence has not. The pre-main feasibility language (not "reset" as a scope change) is accepted.
- **Alternatives considered:** Continue D14/D15 engineering on the Kayla/Qwen14B line - REJECTED (would delay the first scientific table without changing the blockers). Raise the timeout to force the 48-cell matrix - REJECTED (existing D10 finding: timeout increases are internal corrections, not scientific gains). Launch the old 48-cell Pilot - REJECTED (no launch authorization; it is retired as a launch basis). Reducing the final thesis repository count as part of this task - REJECTED (any permanent reduction remains a supervisor-level scope amendment).
- **Impact:** Scientific version narrative pivots to `SCIENTIFIC-MICROSTUDY-01`. No scientific input, runtime code, scenario, evaluator, or metric changed. The current scientific target is Todo-only; djangoCMS is conditional on Todo GO + a real reproducible dependency graph; Saleor is not part of the immediate next task. The permanent final thesis scope is NOT decided here.
- **Evidence:** `docs/SCIENTIFIC_RESET_DECISION_2026-09-04.md`; `docs/POST_2018_RESEARCH_EVIDENCE_MATRIX.md` (M1-M14); `DECISION_LOG.md` D021-D039 history; real-run records `exp-20260830-134232` / `exp-20260902-canary` preserved verbatim.

---

## Decision D041 - Mandatory non-study operational model/provider acceptance gate before the scientific micro-study (SCIENTIFIC-RESET-01)

- **Date:** 2026-09-04
- **Decision ID:** D041
- **Status:** ACCEPTED / FROZEN (preregistration). Gate NOT yet executed - zero real calls in this task.
- **Category:** Model/Provider Operational Acceptance / Preregistration
- **Description:** Before any scientific Todo scenario is run, a non-study operational acceptance gate executes exactly **6 throwaway calls** (3 per candidate: T1 exact-patch task, T2 agent-control task, T3 repair task). The candidates are Candidate A = **DeepSeek V4 Flash 0731** and Candidate B = **Qwen2.5-Coder-32B-Instruct**; the winner is selected ONLY by the preregistered NON-SCIENTIFIC operational criteria (eligibility thresholds + ranked tie-breakers: format compliance, truncation, median latency, normalized cost, reproducibility contract) and is then frozen as the ONE exact model/provider/settings before the first scientific run. No scientific scenario is used to choose a model; DeepSeek is NOT pre-selected.
- **Rationale:** The model/provider must be operationally accepted (latency, truncation, format, transport reliability, usage accounting, no hidden scientific data) and frozen BEFORE scientific results exist, so model choice cannot be tuned on observed study outcomes (anti-cherry-picking).
- **Alternatives considered:** Skipping the gate and using a previously used model - REJECTED (no accepted scientific result exists to justify it). Selecting the model after a few scientific runs - REJECTED (post-outcome selection invalidates confirmatory go/no-go status).
- **Impact:** Blocks all scientific work until the gate completes and one configuration is frozen. If neither candidate is eligible, STOP and diagnose the gate only.
- **Evidence:** `_workspace/active/01_MODEL_PROVIDER_ACCEPTANCE_GATE.md`; `docs/PREMAIN_FEASIBILITY_PREREGISTRATION.md` section 1; `docs/POST_2018_RESEARCH_EVIDENCE_MATRIX.md` M11.

---

## Decision D042 - Freeze the Todo correctness-first micro-study design at 3 scenarios x 2 strategies x 5 reps = 30 attempted runs (SCIENTIFIC-RESET-01)

- **Date:** 2026-09-04
- **Decision ID:** D042
- **Status:** ACCEPTED / FROZEN (preregistration). Study NOT started; zero real calls in this task.
- **Category:** Study Design / Preregistration
- **Description:** The pre-main Todo scientific micro-study (`SCIENTIFIC-MICROSTUDY-01`) is frozen as **3 scenarios x 2 strategies (iterative repository-agent/Agent vs selective/Selective) x 5 independent repetitions = 30 attempted runs**. Evaluation reading order is fixed: correctness first, then preservation, then impact recall, then efficiency (efficiency is secondary and descriptive only among correctness+preservation-qualified runs; NO significance claim from n=5). Study failures are retained and classified.
- **Rationale:** A small, bounded, pre-main correctness-first study gives the FIRST SCIENTIFIC RESULTS TABLE with the fewest confounds; the large-repo inference-runtime confound is removed by using Todo only; multiple independent repetitions are required even at temperature=0.
- **Alternatives considered:** A smaller design (e.g., 3 reps) - REJECTED (would not support the >=4/5 thresholds). More scenarios/repos - REJECTED (the final thesis scope is not decided here; djangoCMS/Saleor have graph-eligibility problems). A full 48-cell style relaunch - REJECTED (D040).
- **Impact:** Bounds the next feature to one vertical slice ending in GO/NO-GO. Tripolar scope: Todo only now; djangoCMS conditional on GO + real dependency graph; Saleor not in the immediate path.
- **Evidence:** `_workspace/active/03_MICROSTUDY_GO_NOGO_RULES.md`; `docs/PREMAIN_FEASIBILITY_PREREGISTRATION.md` section 3.

---

## Decision D043 - Freeze GO/NO-GO thresholds BEFORE model calls (SCIENTIFIC-RESET-01)

- **Date:** 2026-09-04
- **Decision ID:** D043
- **Status:** ACCEPTED / FROZEN (preregistration).
- **Category:** Thresholds / Preregistration / Analysis
- **Description:** Per-scenario Selective gates (5 reps): **G1 correctness** = changed-requirement evaluator pass in >=4/5 AND Selective not worse than Agent by more than 1 passing repetition for the same scenario; **G2 preservation** = >=4/5 Selective runs with zero unintended preserve-artifact edits AND passing regression/preservation checks; **G3 impact recall** = >=4/5 Selective runs where the predicted regenerate-set contains every gold regenerate artifact (recall = 1.0); **G4 efficiency** = descriptive metrics only among correctness+preservation-qualified runs (tokens, calls, selected/regenerated artifacts, latency, repairs; medians + raw), no significance claim from n=5. **Study GO** = all 3 scenarios clear G1 AND all 3 clear G2 AND at least 2/3 clear G3. Otherwise NO-GO / bounded result (analyze failure modes, preserve the negative/bounded result, do not tune on outcomes). No post-hoc threshold edits: changing any threshold after seeing results invalidates the study as confirmatory go/no-go evidence and forces relabeling as exploratory.
- **Rationale:** Thresholds must exist before outcomes so the study is confirmatory rather than fitted to observed behavior.
- **Alternatives considered:** Setting thresholds after pilot runs - REJECTED (post-hoc threshold edits are prohibited). Requiring significance for GO - REJECTED (efficiency does not need to win to authorize the next stage).
- **Impact:** The GO/NO-GO computation is mechanical and auditable from the frozen threshold table.
- **Evidence:** `_workspace/active/03_MICROSTUDY_GO_NOGO_RULES.md`; `docs/PREMAIN_FEASIBILITY_PREREGISTRATION.md` section 4; `docs/POST_2018_RESEARCH_EVIDENCE_MATRIX.md` M13-M14.

---

## Decision D044 - Freeze Todo scenario IDs before scientific inference (SCIENTIFIC-RESET-01)

- **Date:** 2026-09-04
- **Decision ID:** D044
- **Status:** ACCEPTED / FROZEN (preregistration).
- **Category:** Dataset / Preregistration
- **Description:** The scientific scenario IDs are frozen as **todo-smoke-001** (localized), **todo-smoke-002** (moderate), **todo-smoke-003** (cross_cutting), selected mechanically (one pre-existing Todo scenario per blast-radius class, existing independent evaluator asset, explicit expected actions, selected without reference to strategy outcome; they are pre-existing smoke scenarios, not chosen because of the final 1/6 canary outcome). A mandatory pre-run evaluator audit (traceability, no hidden surprises, aisation/no leakage, independent pinned base) must pass before freezing the dataset; replacement before any scientific call is allowed only for contradiction / leakage / non-executability / invalid pinned-base, staying in the same blast-radius class. Scenario IDs never change because a strategy/model performs poorly.
- **Rationale:** Pre-registering scenario IDs and rationale before results removes dataset-selection degrees of freedom.
- **Alternatives considered:** Selecting scenarios from the 12 Pilot scenarios used in prior runs - REJECTED (the 12 include djangoCMS/Saleor scenarios with graph/executability problems and were the venue of failed runs; outcome-based selection is forbidden).
- **Impact:** The study dataset is fixed; the evaluator assets (`tests/evaluator_assets/todo_smoke_00*_checks.py`) and gold expected-actions are evaluation-only and must stay inaccessible to both strategies.
- **Evidence:** `_workspace/active/02_TODO_SCENARIO_PREREGISTRATION.md`; `docs/PREMAIN_FEASIBILITY_PREREGISTRATION.md` section 2.

---

## Decision D045 - Graph eligibility rule: verified-empty != fallback-empty (SCIENTIFIC-RESET-01)

- **Date:** 2026-09-04
- **Decision ID:** D045
- **Status:** ACCEPTED / FROZEN (preregistration).
- **Category:** Construct Validity / Graph Eligibility / Preregistration
- **Description:** An empty dependency graph is NOT automatically invalid. **verified-empty** (the extractor ran correctly and the scoped case genuinely has no dependency edges) = may remain a low-information but potentially legitimate observation. **fallback-empty / dependency evidence not established** (extractor did not actually run / degraded to a construct) = NOT eligible for a dependency-aware treatment claim. The current djangoCMS/Saleor concern is the fallback-style construct problem; Todo has a real graph with edges.
- **Rationale:** Confusing a failed/absent extraction with an empty result would let a dependency-aware claim rest on evidence that was never produced.
- **Alternatives considered:** Treating every empty graph as invalid - REJECTED (would discard legitimate low-information observations). Treating every empty graph as valid - REJECTED (would license claims on missing evidence).
- **Impact:** Any future djangoCMS extension (conditional on Todo GO) requires a real reproducible dependency graph; repository profile is not equal to a meaningful dependency graph.
- **Evidence:** `_workspace/active/07_CLAUDE_FEEDBACK_INTEGRATION.md` (amendment); `docs/PREMAIN_FEASIBILITY_PREREGISTRATION.md` section 5; `docs/POST_2018_RESEARCH_EVIDENCE_MATRIX.md` M6, M12.

---

## Decision D046 - Freeze PA-001 implementation clarification for SCIENTIFIC-MICROSTUDY-01 (five-file source universe, evidence obligations, fixed-provider identity, gold isolation)

- **Date:** 2026-09-05
- **Decision ID:** D046
- **Status:** ACCEPTED / FROZEN (preregistration amendment; before any new model call).
- **Category:** Preregistration / Measurement / Construct Validity
- **Description:** The audited implementation clarification is frozen BEFORE the model acceptance gate and before any scientific call: (1) the strategy-scored source-impact universe for the Todo micro-study is EXACTLY five files (todo/models.py, todo/serializers.py, todo/views.py, todo/permissions.py, todo/urls.py); migration directories are shared-executor obligations scored separately through migration_generation_passed / generated_migration_paths and never inflate or penalize selector regenerate recall. (2) Per-run evidence obligations: predicted_actions (dict path->action from the final prediction) and changed_artifact_paths (actual changed source paths against the frozen active snapshot) are persisted through RunRecord -> RunRecordData -> JSONL; migrations excluded from changed_artifact_paths. (3) OpenRouter requests carry exactly one pinned provider, allow_fallbacks=false, require_parameters where supported; model_identity shape openrouter:<model>@<provider>; provider/model/backend changes alter config_hash and Run IDs. (4) Scientific generation/repair prompts never receive scenario.expected_actions or gold artifact_instructions; edit action semantics come from RegenerationPlan.actions; generic Python contract guards stay active without gold context. (5) Frozen execution contract: workflow timeout 900 s, source cap 4096, agent-control cap 512, max attempts 3, no new total-workflow token ceiling, provider-reported usage is the metric of record. (6) Candidate provider policy: DeepSeek candidate must use the first-party DeepSeek provider if available (else STOP the gate for an amendment); Qwen candidate must be single-provider (else STOP); resolved provider slug persisted before the first call.
- **Rationale:** The independent audit found measurable gaps (gold expected-action leakage into the regeneration executor; missing provider pin/no-fallback; incomplete identity/config hash; missing predicted-action and actual-change persistence; need for a clean five-file scoring universe). These must be clarified in the preregistration BEFORE outcomes so scoring is not tuned post-hoc.
- **Alternatives considered:** Leaking scenario gold into the executor for simpler prompt building - REJECTED (violates evidence/strategy separation). Scoring migrations as selector recall - REJECTED (migrations are executor obligations). Counting model-preserved predictions instead of actual changed paths - REJECTED (preservation gate is about actual unintended changes).
- **Impact:** Binds the scientific micro-study to a clean measurement contract; no scientific scenario content is altered; historical profiles remain reproducible; the scientific profile is fail-closed against gold leakage.
- **Evidence:** `_workspace/active/01_INDEPENDENT_AUDIT_FINDINGS.md`; `_workspace/active/00_SCIENTIFIC_MICROSTUDY_01_MASTER.md` section "PA-001"; `docs/PREMAIN_FEASIBILITY_PREREGISTRATION.md` section 8.

## Decision D047 - Supersede the binary R/P micro-study and adopt the IMPACTPLAN-WIP-01 protocol (explicit R/P/V/H ImpactPlan treatment + Qwen3-Coder + fixed compatible provider)

- **Date:** 2026-09-05
- **Decision ID:** D047
- **Status:** ACCEPTED / FROZEN (preregistration amendment; before any new model call).
- **Category:** Preregistration / Construct Validity / Model Selection
- **Description:** SUPERSEDES the old SCIENTIFIC-MICROSTUDY-01 binary R/P treatment authorization (was `MICROSTUDY_REAL_RUN_AUTHORIZED=YES`; now `NO` until the new treatment passes independent audit). The new WIP protocol label is `scientific-wip-impactplan-v1`. The Selective treatment must produce and ENFORCE a first-class persisted `ImpactPlan`: every candidate artifact classified exactly once as R | P | V | H; `write_set == {R}`; P/V/H writes prohibited and physically blocked; `context_set` independent of action sets; validation/test obligations separate; every R cites strategy-visible evidence; low-confidence/conflict -> H; at most ONE versioned bounded expansion (v1 -> v2) then HUMAN_REVIEW; planner calls/tokens/latency/cost counted in the proposed-arm total. Evidence collector reuses the Todo static graph + descriptors and adds automatic repository-native test links + normalized visible constraints. Model freeze: primary scientific model `qwen/qwen3-coder` through the existing OpenRouter backend; provider policy is FIXED COMPATIBLE PROVIDER (NOT first-party): DeepInfra (Turbo) first, NovitaAI only if DeepInfra fails the frozen operational contract; `allow_fallbacks=false`; no provider shopping after freeze. The old first-party-DeepSeek rule (D046) and the two-candidate acceptance gate (DeepSeek V4 Flash / Qwen2.5-Coder-32B) are SUPERSEDED and remain historical. D046 evidence/plumbing (provider-pin identity, gold isolation, predicted_actions, changed_artifact_paths) is REUSED.
- **Rationale:** The independent construct audit (02_CURRENT_CODE_AND_EVIDENCE_AUDIT.md) found the current HybridSelectiveStrategy emits only R/P — it does not produce the full R/P/V/H ImpactPlan the thesis claims, and there is no first-class plan containing context set, validation obligations, architecture checks and versioned bounded expansion. Running the 30 cells now would create data about the wrong construct. Fixed compatible provider is the reproducibility requirement; first-party hosting is not.
- **Alternatives considered:** Run 30 now because old G1-G6 passed - REJECTED (validates old plumbing, not the treatment). Keep DeepSeek first-party as a scientific requirement - REJECTED (operational symptom, not scientific; D1/D7). Model-shop after outcomes - REJECTED (anti-cherry-picking).
- **Impact:** The unified research path proceeds: implement Stage-C ImpactPlan contract, revalidate the six gates against the NEW protocol, freeze Qwen3-Coder + one provider, independent audit, THEN (and only after audit) run the 30 scientific cells.
- **Evidence:** `_workspace/active/UNIFIED_RESEARCH_PATH_PACK/*` (00-10); `docs/PREMAIN_FEASIBILITY_PREREGISTRATION.md` section 9 (PA-002).

---

## Decision D048 - Bounded exact-patch delimiter-boundary recovery (FAST-RESULTS-01)

- **Date:** 2026-09-05
- **Decision ID:** D048
- **Status:** ACCEPTED / FROZEN (preregistration amendment; before any new model call).
- **Category:** Preregistration / Interface Contract / Model Selection
- **Description:** The acceptance gate A2 previously conflated semantic editing ability with one delimiter-boundary newline. The deterministic one-newline/unique-match adapter is now part of the frozen shared executor interface: when a SEARCH block has zero exact matches AND ends in two newline characters, remove exactly one trailing newline; the recovery succeeds ONLY if the trimmed candidate has exactly one literal match in the current content; any other whitespace/fuzzy difference remains a fail-closed rejection. The adapter is shared by both experimental arms and is frozen before scientific runs. Model (`qwen/qwen3-coder`), provider policy (DeepInfra first, no fallback), scenario IDs, thresholds, treatment, and protocol do NOT change. No scientific outcome existed when this amendment was made (the earlier A2 failures were operational-gate evidence only).
- **Rationale:** DeepInfra's A2 failure was one extra trailing newline in SEARCH before the `=======` divider - an interface-boundary formatting defect, not evidence that the model cannot reason about the edit. The recovery does not guess content: it is allowed only after exact-match failure and only for one unique literal candidate.
- **Alternatives considered:** General fuzzy whitespace matching - REJECTED (violates the literal/fail-closed executor contract and could mask real regressions). Model shopping after the gate failure - REJECTED (D047 anti-cherry-picking). Redesigning Stage C - REJECTED (the treatment construct was already audited).
- **Impact:** Unblocks rerunning the PRIMARY acceptance gate on DeepInfra only. If A1/A2/A3 pass 3/3 under the amended fixed interface, freeze model/provider, rerun the six gates + audit + full suite once, estimate cost, and if <= $2.50 run the frozen 30 Todo cells immediately.
- **Evidence:** `_workspace/active/FAST_RESULTS_01_PACK/00_DECISION_LOCK.md`; `docs/PREMAIN_FEASIBILITY_PREREGISTRATION.md` section 10 (PA-003); `tests/unit/execution/test_exact_patch.py::TestExactPatchBoundaryRecovery`.
