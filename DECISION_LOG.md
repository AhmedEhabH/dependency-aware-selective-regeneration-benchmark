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
- **Impact:** Phase 3.5 deliverables complete. 8 new docs, 2 reports, 10 new architecture checks passed. Phase 4A (Domain Models and Contracts) is the exact next task.
- **Evidence:** All files under docs/ (16 total), reports/PHASE3_5_ARCHITECTURE_AUDIT.md, reports/PROJECT_STRUCTURE_CONFLICT_REPORT.md.
