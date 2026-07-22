# TODO

## Phase 0 — Bootstrap and Environment

### T001 — Create Repository Structure
- **Priority:** HIGH
- **Category:** Structure
- **Description:** Create directories: src/benchmark, tests, notebooks, scripts, reports
- **Acceptance Criteria:** All directories exist with __init__.py files
- **Dependencies:** None
- **Status:** COMPLETE_STATICALLY
- **Owner:** OpenCode
- **Evidence:** Directories verified via Get-ChildItem

### T002 — Create State Files
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create SYSTEM_STATE.md, TODO.md, DECISION_LOG.md, PROTOCOL_VERSION.md, docs/MASTER_IMPLEMENTATION_PLAN.md, docs/HUMAN_DECISIONS_REQUIRED.md
- **Acceptance Criteria:** All files present with required content
- **Dependencies:** T001
- **Status:** COMPLETE_STATICALLY
- **Owner:** OpenCode
- **Evidence:** Files written to disk

### T003 — Create Environment Files
- **Priority:** HIGH
- **Category:** Environment
- **Description:** Create environment.yml, requirements-dev.txt, requirements-kaggle.txt
- **Acceptance Criteria:** All three files present with correct package lists
- **Dependencies:** T001
- **Status:** COMPLETE_STATICALLY
- **Owner:** OpenCode
- **Evidence:** Files written to disk

### T004 — Create Conda Environment
- **Priority:** HIGH
- **Category:** Environment
- **Description:** Create `selective-regen-benchmark` with Python 3.11 via conda
- **Acceptance Criteria:** Environment exists and is activatable
- **Dependencies:** T003
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** conda env list output, environment.yml resolution

### T005 — Install Local Engineering Dependencies
- **Priority:** HIGH
- **Category:** Environment
- **Description:** Install packages from requirements-dev.txt inside the project Conda environment via pip
- **Acceptance Criteria:** All packages installed without conflicts
- **Dependencies:** T004
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** pip list output, pip check passing

### T006 — Validate Environment
- **Priority:** HIGH
- **Category:** Validation
- **Description:** Run pip check, import smoke tests, version checks, duplicate inspection, optional dependency checks
- **Acceptance Criteria:** All checks pass; no unresolved conflicts
- **Dependencies:** T005
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** Check outputs, LOCAL_ENVIRONMENT_REPORT.md

### T007 — Create Environment Report
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create reports/LOCAL_ENVIRONMENT_REPORT.md with all required sections
- **Acceptance Criteria:** Report contains all sections listed in Section 4.3 of the guide
- **Dependencies:** T006
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** File exists with complete content

### T008 — Create Phase Report
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create reports/latest_phase_report.md summarizing Phase 0
- **Acceptance Criteria:** Report lists completed tasks, created files, checks passed, next task
- **Dependencies:** T007
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** File exists with complete content

### T009 — Initialize Git Repository
- **Priority:** MEDIUM
- **Category:** VCS
- **Description:** Initialize Git repo, create .gitignore, make initial bootstrap commit
- **Acceptance Criteria:** Git repo exists with initial commit on main branch
- **Dependencies:** T001-T008
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** git log output

### T010 — Final Review and Handoff
- **Priority:** HIGH
- **Category:** Process
- **Description:** Review all files, verify environment, produce final message
- **Acceptance Criteria:** All files reviewed; environment activation command verified
- **Dependencies:** T009
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** Final message with handoff statement

## Phase 1 — Input Audit

### T101 — Inspect inputs/ Directory
- **Priority:** HIGH
- **Category:** Audit
- **Description:** Inspect all files under inputs/; verify immutability
- **Acceptance Criteria:** Complete inventory of inputs/ with file types, sizes, and descriptions
- **Dependencies:** T010
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** INPUT_AUDIT_REPORT.md Section 2

### T102 — Classify Existing Benchmark Outputs
- **Priority:** HIGH
- **Category:** Audit
- **Description:** Classify all existing benchmark outputs as legacy_pilot per preapproved decision
- **Acceptance Criteria:** Classification documented; zero legacy outputs verified
- **Dependencies:** T101
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** INPUT_AUDIT_REPORT.md Section 3

### T103 — Identify Reusable Components
- **Priority:** HIGH
- **Category:** Audit
- **Description:** Catalog all reusable components from Phase 0
- **Acceptance Criteria:** Comprehensive inventory with status and notes for each component
- **Dependencies:** T101
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** INPUT_AUDIT_REPORT.md Section 5

### T104 — Identify Errors, Leakage Risks, Metric Problems
- **Priority:** HIGH
- **Category:** Audit
- **Description:** Scan source material for errors, data leakage risks, metric design issues
- **Acceptance Criteria:** All findings documented with severity and recommendations
- **Dependencies:** T102, T103
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** INPUT_AUDIT_REPORT.md Sections 6, 7

### T105 — Create Migration Documentation
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create reports/INPUT_AUDIT_REPORT.md with full audit findings
- **Acceptance Criteria:** Report covers all Phase 1 requirements; missing inputs explicitly recorded
- **Dependencies:** T104
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** reports/INPUT_AUDIT_REPORT.md

### T106 — Update State Files
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Update SYSTEM_STATE.md, TODO.md, DECISION_LOG.md, reports/latest_phase_report.md for Phase 1
- **Acceptance Criteria:** All state files consistent; exact next task recorded
- **Dependencies:** T105
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** Git diff showing updates to all four files

## Phase 2A — Research Protocol Draft

### T201 — Draft Research Questions Traceability
- **Priority:** HIGH
- **Category:** Protocol
- **Description:** Produce full RQ-to-hypothesis-to-evaluation-phase traceability table
- **Acceptance Criteria:** All 5 RQs mapped to hypotheses, measures, and evaluation phases
- **Dependencies:** T106
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** PHASE2_PROTOCOL_DRAFT.md §1

### T202 — Draft Hypothesis Specification
- **Priority:** HIGH
- **Category:** Protocol
- **Description:** Specify all 5 hypotheses with measures, comparisons, and decision criteria
- **Acceptance Criteria:** Each hypothesis has primary comparison, measures, and interpretation criterion
- **Dependencies:** T201
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** PHASE2_PROTOCOL_DRAFT.md §2

### T203 — Draft Repository Selection Criteria
- **Priority:** HIGH
- **Category:** Protocol
- **Description:** Define selection criteria, acquisition policy, and architectural diversity targets
- **Acceptance Criteria:** Preapproved repos documented; selection criteria formalized
- **Dependencies:** T202
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** PHASE2_PROTOCOL_DRAFT.md §3

### T204 — Draft Candidate Artifact Universe
- **Priority:** HIGH
- **Category:** Protocol
- **Description:** Define artifact node types, edge types, granularity, and universe boundary
- **Acceptance Criteria:** All 10 node types, 7 edge types, attributes, and exclusions documented
- **Dependencies:** T202
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** PHASE2_PROTOCOL_DRAFT.md §4

### T205 — Draft Ground-Truth and Annotation Protocol
- **Priority:** HIGH
- **Category:** Protocol
- **Description:** Define ground-truth construction, annotation process, adjudication, and quality thresholds
- **Acceptance Criteria:** Full protocol from source materials to published annotations
- **Dependencies:** T204
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** PHASE2_PROTOCOL_DRAFT.md §5–6

### T206 — Draft Scenario Taxonomy
- **Priority:** HIGH
- **Category:** Protocol
- **Description:** Define change types, blast radius categories, scenario schema, and naming convention
- **Acceptance Criteria:** 8 change types, 3 blast radii, 8 scenarios per repo schema fully defined
- **Dependencies:** T203, T204
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** PHASE2_PROTOCOL_DRAFT.md §7

### T207 — Draft Baseline Definitions
- **Priority:** HIGH
- **Category:** Protocol
- **Description:** Define all 6+ baselines including ablation variants
- **Acceptance Criteria:** Every strategy named, described, and categorized (baseline/ablation/reference)
- **Dependencies:** T202
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** PHASE2_PROTOCOL_DRAFT.md §8

### T208 — Draft Metrics Suite
- **Priority:** HIGH
- **Category:** Protocol
- **Description:** Define primary and secondary metrics with formal definitions
- **Acceptance Criteria:** 6 primary metric categories + 5 secondary metric categories fully specified
- **Dependencies:** T201, T207
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** PHASE2_PROTOCOL_DRAFT.md §9–10

### T209 — Draft Statistical Analysis Plan
- **Priority:** HIGH
- **Category:** Protocol
- **Description:** Define tests, NI margin, corrections, power analysis, outlier policy
- **Acceptance Criteria:** Per-hypothesis test selection; reporting formats specified
- **Dependencies:** T208
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** PHASE2_PROTOCOL_DRAFT.md §11

### T210 — Draft Policies (Randomization, Seeds, Budget, Failure, Leakage)
- **Priority:** HIGH
- **Category:** Protocol
- **Description:** Define randomization, seed, execution budget, failure, and leakage prevention policies
- **Acceptance Criteria:** All 5 policies fully defined
- **Dependencies:** T209
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** PHASE2_PROTOCOL_DRAFT.md §12–16

### T211 — Draft Validity and Reproducibility Sections
- **Priority:** HIGH
- **Category:** Protocol
- **Description:** Document threats to validity and reproducibility protocol
- **Acceptance Criteria:** Construct/internal/external/conclusion validity + reproducibility plan
- **Dependencies:** T210
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** PHASE2_PROTOCOL_DRAFT.md §17–18

### T212 — Compile Full Protocol Draft
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Assemble all sections into reports/PHASE2_PROTOCOL_DRAFT.md with status tags
- **Acceptance Criteria:** All 21 sections present; every item tagged PREAPPROVED/PROPOSED/REQUIRES_RESEARCHER_APPROVAL
- **Dependencies:** T201–T211
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** reports/PHASE2_PROTOCOL_DRAFT.md

### T213 — Update State Files for Phase 2A
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Update SYSTEM_STATE.md, TODO.md, DECISION_LOG.md, reports/latest_phase_report.md for Phase 2A
- **Acceptance Criteria:** All state files consistent; 14 researcher decision items documented; exact next task recorded
- **Dependencies:** T212
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** Git diff showing updates to all four files

## Phase 2B — Protocol Freeze

### T301 — Apply Researcher Decisions DA-01 through DA-14
- **Priority:** HIGH
- **Category:** Protocol
- **Description:** Apply all 14 researcher-approved decisions to the draft protocol
- **Acceptance Criteria:** Every DA item from FINAL_RESEARCH_PROTOCOL_DECISIONS.md applied; contradictory draft wording overwritten
- **Dependencies:** T213
- **Status:** FROZEN
- **Owner:** Researcher + OpenCode
- **Evidence:** docs/RESEARCHER_DECISIONS_DA_AC.md

### T302 — Apply Mandatory Corrections AC-01 through AC-11
- **Priority:** HIGH
- **Category:** Protocol
- **Description:** Apply all 11 mandatory corrections from the researcher
- **Acceptance Criteria:** Every AC item applied; 9 contradictions corrected
- **Dependencies:** T301
- **Status:** FROZEN
- **Owner:** OpenCode
- **Evidence:** docs/RESEARCHER_DECISIONS_DA_AC.md (contradictions section)

### T303 — Create Frozen Protocol Documents
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create 7 protocol docs under docs/ and decision records
- **Acceptance Criteria:** All 8 docs/ files present with FROZEN status, v1.0
- **Dependencies:** T302
- **Status:** FROZEN
- **Owner:** OpenCode
- **Evidence:** SHA-256 checksums for all 8 documents

### T304 — Update State Files for Phase 2B
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Update PROTOCOL_VERSION.md, SYSTEM_STATE.md, TODO.md, DECISION_LOG.md, reports/PHASE2B_PROTOCOL_FREEZE_REPORT.md, reports/latest_phase_report.md
- **Acceptance Criteria:** All state files consistent; protocol_status: FROZEN; Phase 3 authorized
- **Dependencies:** T303
- **Status:** FROZEN
- **Owner:** OpenCode
- **Evidence:** Git diff showing updates to all files

### T305 — Validation of Frozen Protocol
- **Priority:** HIGH
- **Category:** Validation
- **Description:** Validate all frozen documents for internal consistency; no unresolved REQUIRES_RESEARCHER_APPROVAL; SHA-256 checksums
- **Acceptance Criteria:** 10 validation checks pass; checksums recorded
- **Dependencies:** T304
- **Status:** FROZEN
- **Owner:** OpenCode
- **Evidence:** SYSTEM_STATE.md local checks passed list

## Phase 3 — Repository and Scenario Preparation

### T401 — Select and Pin Repository Versions
- **Priority:** HIGH
- **Category:** Repository
- **Description:** Select 3 confirmatory repositories (todo, djangocms, saleor); pin versions with commit SHAs
- **Acceptance Criteria:** DA-01, DA-02, DA-03 compliance verified for all 3 repos
- **Dependencies:** T305
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** benchmark_data/manifests/repository_versions.yaml; REPOSITORY_SELECTION_REPORT.md

### T402 — Create Repository Profiles
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create architectural profiles for all 3 repositories with boundary analysis
- **Acceptance Criteria:** 3 profiles covering overview, architecture, artifact catalog, test suite, boundaries, limitations
- **Dependencies:** T401
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** benchmark_data/repository_profiles/{todo,djangocms,saleor}.yaml

### T403 — Create Scenario Definitions (24 YAML files)
- **Priority:** HIGH
- **Category:** Scenario
- **Description:** Design 8 scenarios per repository (3 localized, 3 moderate, 2 cross-cutting) covering all 8 change types
- **Acceptance Criteria:** All 24 YAML files with scenario_id, requirements, acceptance criteria, expected artifacts, hidden_tests
- **Dependencies:** T402
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** 24 files under benchmark_data/scenarios/

### T404 — Create Documentation Reports
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create 6 reports covering selection, architecture, scenario design, licensing, Kaggle feasibility, phase summary
- **Acceptance Criteria:** All reports present with complete content
- **Dependencies:** T403
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** 6 reports under reports/

### T405 — Create Manifests
- **Priority:** HIGH
- **Category:** Manifest
- **Description:** Create repositories.yaml and repository_versions.yaml manifests
- **Acceptance Criteria:** Both files present with frozen version metadata
- **Dependencies:** T401
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** benchmark_data/manifests/{repositories,repository_versions}.yaml

### T406 — Update State Files for Phase 3
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Update SYSTEM_STATE.md, TODO.md, DECISION_LOG.md, reports/latest_phase_report.md for Phase 3
- **Acceptance Criteria:** All state files consistent; Phase 3 recorded as COMPLETE; Phase 4 as next
- **Dependencies:** T404, T405
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Git diff showing updates to all files

## Phase 3.5 — Static Architecture Audit and Project Map

### T350 — Inspect Repository Layout and Identify Conflicts
- **Priority:** HIGH
- **Category:** Audit
- **Description:** Inspect full repository tree; identify duplicate directories, stale files, misplaced docs, naming inconsistencies, Git boundary issues
- **Acceptance Criteria:** Complete inventory of structural issues; documented root vs project conflicts
- **Dependencies:** T406
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** reports/PROJECT_STRUCTURE_CONFLICT_REPORT.md

### T351 — Define Canonical Project Root and Path Policy
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create docs/PROJECT_ROOT_AND_PATH_POLICY.md with canonical root, directory classification, remediation plan
- **Acceptance Criteria:** Policy states exact canonical root, classifies every directory, includes remediation for duplicates
- **Dependencies:** T350
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** docs/PROJECT_ROOT_AND_PATH_POLICY.md

### T352 — Create Project Structure Map
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create docs/PROJECT_STRUCTURE_MAP.md with complete proposed tree and directory responsibility tables
- **Acceptance Criteria:** Every proposed package has one responsibility documented; import rules per package
- **Dependencies:** T351
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** docs/PROJECT_STRUCTURE_MAP.md

### T353 — Define Software Architecture and Interfaces
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create docs/SOFTWARE_ARCHITECTURE.md with 13 layers, 11 interface specifications, model backend separation, import isolation
- **Acceptance Criteria:** All layers documented; all interfaces have responsibility, inputs, outputs, failure behavior, extension rules
- **Dependencies:** T352
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** docs/SOFTWARE_ARCHITECTURE.md

### T354 — Define Dependency Rules
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create docs/DEPENDENCY_RULES.md with allowed/prohibited dependency directions, import policies
- **Acceptance Criteria:** Every package has explicit import rules; 10 prohibited patterns documented
- **Dependencies:** T353
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** docs/DEPENDENCY_RULES.md

### T355 — Create Extension Guide (Plugin/Registry Design)
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create docs/EXTENSION_GUIDE.md with plugin lifecycle, registry design, protocol skeletons, factory pattern
- **Acceptance Criteria:** Adding a strategy/LLM/validator/metric does not require core changes; registry is not global singleton
- **Dependencies:** T354
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** docs/EXTENSION_GUIDE.md

### T356 — Define Public/Private Data Boundary
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create docs/PUBLIC_PRIVATE_DATA_BOUNDARY.md with classification, import isolation, data flow, audit checklist
- **Acceptance Criteria:** Private data inaccessible to strategies; data flow from execution to evaluation is unidirectional
- **Dependencies:** T355
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** docs/PUBLIC_PRIVATE_DATA_BOUNDARY.md

### T357 — Create Phase 4 Implementation Blueprint
- **Priority:** HIGH
- **Category:** Planning
- **Description:** Create docs/PHASE4_IMPLEMENTATION_BLUEPRINT.md with 6 milestones (4A–4F), files, tests, acceptance criteria
- **Acceptance Criteria:** Each milestone has dependencies, forbidden work, estimated complexity
- **Dependencies:** T353
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** docs/PHASE4_IMPLEMENTATION_BLUEPRINT.md

### T358 — Create Architecture Validation Plan
- **Priority:** HIGH
- **Category:** Planning
- **Description:** Create docs/ARCHITECTURE_VALIDATION_PLAN.md with 11 validation checks, tools, approaches
- **Acceptance Criteria:** Covers import boundaries, circular imports, layer isolation, no torch locally, no leakage
- **Dependencies:** T357
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** docs/ARCHITECTURE_VALIDATION_PLAN.md

### T359 — Create Architecture Audit Reports
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create reports/PHASE3_5_ARCHITECTURE_AUDIT.md and reports/PROJECT_STRUCTURE_CONFLICT_REPORT.md
- **Acceptance Criteria:** Reports document current tree, proposed tree, duplicate issues, remediation plan, architecture decisions
- **Dependencies:** T350–T358
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** reports/PHASE3_5_ARCHITECTURE_AUDIT.md, reports/PROJECT_STRUCTURE_CONFLICT_REPORT.md

### T360 — Update State Files for Phase 3.5
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Update SYSTEM_STATE.md, TODO.md, DECISION_LOG.md, reports/latest_phase_report.md for Phase 3.5
- **Acceptance Criteria:** All state files consistent; Phase 3.5 recorded as COMPLETE; Phase 4A as next
- **Dependencies:** T359
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Edits to all four state files

## Phase 3.6 — Structure Remediation and Baseline Commit

### T361 — Resolve Duplicate Documentation and Delete Stale Files
- **Priority:** HIGH
- **Category:** Structure
- **Description:** Copy outer OPENCODE_EXECUTION_GUIDE.md and MASTER_IMPLEMENTATION_PLAN.md into project/docs/. Delete stale outer FINAL_RESEARCH_PROTOCOL_DECISIONS.md and HUMAN_DECISIONS_REQUIRED.md. Delete stale outer benchmark_data/. Preserve inputs/ as immutable.
- **Acceptance Criteria:** Outer reference docs preserved in project/docs/; stale superseded files deleted; external inputs untouched
- **Dependencies:** T360
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Files copied, deleted, and verified via Test-Path

### T362 — Fix Scenario Taxonomy Inconsistencies
- **Priority:** HIGH
- **Category:** Scenario
- **Description:** Correct blast_radius in all 14 djangocms and saleor scenario YAMLs to use taxonomy-standard values (localized, moderate, cross_cutting)
- **Acceptance Criteria:** All 24 scenarios have blast_radius matching naming convention and SCENARIO_TAXONOMY.md
- **Dependencies:** T361
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** grep of blast_radius across all 24 scenario YAMLs shows only standard values

### T363 — Update .gitignore and Validate Project Tree
- **Priority:** HIGH
- **Category:** Structure
- **Description:** Deduplicate .gitignore, add runs/, add report exceptions. Validate full project tree structure.
- **Acceptance Criteria:** .gitignore clean; project tree has 18 docs, 29 benchmark_data, scaffold-only src/benchmark
- **Dependencies:** T362
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** git status clean; tree validated via Get-ChildItem

### T364 — Create Baseline Commit and Update State Files
- **Priority:** HIGH
- **Category:** VCS
- **Description:** Create git commit for all Phase 3, 3.5, 3.6 work. Create reports/PHASE3_6_STRUCTURE_REMEDIATION_REPORT.md. Update SYSTEM_STATE.md, TODO.md, DECISION_LOG.md, reports/latest_phase_report.md.
- **Acceptance Criteria:** Baseline commit created (845ba49); all state files consistent; working tree clean
- **Dependencies:** T363
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** git log, git status, state file diffs

## Phase 4A — Domain Models and Contracts

### T401 — Implement Enums
- **Priority:** HIGH
- **Category:** Core
- **Description:** Implement 6 StrEnum classes (ActionKind, ArtifactType, BlastRadius, RunStatus, FailureKind, EvidenceTier)
- **Acceptance Criteria:** All enums have stable string values; JSON/YAML serializable
- **Dependencies:** T364
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/core/enums.py, tests/unit/test_enums.py (8 tests)

### T402 — Implement Exception Hierarchy
- **Priority:** HIGH
- **Category:** Core
- **Description:** Implement typed exception hierarchy rooted at BenchmarkError with context dict support
- **Acceptance Criteria:** All 12 classes properly subclassed; context preserved in repr
- **Dependencies:** T401
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/core/exceptions.py, tests/unit/test_exceptions.py (15 tests)

### T403 — Implement Domain Models
- **Priority:** HIGH
- **Category:** Core
- **Description:** Implement 24 frozen dataclass models with post-init validation
- **Acceptance Criteria:** All models frozen; validation rejects empty strings/negative values/duplicates
- **Dependencies:** T401, T402
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/core/models.py, tests/unit/test_models.py (34 tests)

### T404 — Implement Protocol Interfaces
- **Priority:** HIGH
- **Category:** Core
- **Description:** Implement 11 runtime-checkable typing.Protocol interfaces
- **Acceptance Criteria:** All protocols have correct method signatures; conformance checkable via isinstance
- **Dependencies:** T403
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/core/protocols.py, tests/contract/test_protocol_conformance.py (11 tests)

### T405 — Implement Registry
- **Priority:** HIGH
- **Category:** Core
- **Description:** Implement generic Registry[T] with register, create, get, list_names, freeze
- **Acceptance Criteria:** Duplicate/unknown raise typed errors; freeze prevents registration
- **Dependencies:** T402
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/core/registry.py, tests/unit/test_registry.py (9 tests)

### T406 — Implement ExecutionContext
- **Priority:** HIGH
- **Category:** Core
- **Description:** Implement ExecutionContext with controlled immutability
- **Acceptance Criteria:** Defaults correct; private_evaluation_access defaults to False; empty strings rejected
- **Dependencies:** T403
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/core/context.py, tests/unit/test_context.py (9 tests)

### T407 — Implement Config Models
- **Priority:** HIGH
- **Category:** Config
- **Description:** Implement 7 Pydantic v2 config models with cross-field validation
- **Acceptance Criteria:** Kaggle backend rejected in local mode; budgets positive; YAML round-trip works
- **Dependencies:** T403
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/config/models.py, tests/unit/test_config_models.py (16 tests)

### T408 — Implement Config Loader and Validation
- **Priority:** HIGH
- **Category:** Config
- **Description:** Implement YAML config loader and structural validation
- **Acceptance Criteria:** Valid configs load; invalid configs raise typed errors
- **Dependencies:** T407
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/config/loader.py, src/benchmark/config/validation.py

### T409 — Create Package Setup
- **Priority:** HIGH
- **Category:** Build
- **Description:** Create pyproject.toml with project metadata, ruff/mypy/pytest configuration
- **Acceptance Criteria:** Package installable via pip install -e .; all linters runnable
- **Dependencies:** T401–T408
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** pyproject.toml

### T410 — Write Import Isolation Tests
- **Priority:** HIGH
- **Category:** Tests
- **Description:** Write subprocess test verifying torch/transformers not imported by benchmark package
- **Acceptance Criteria:** All 3 isolation tests pass
- **Dependencies:** T409
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** tests/test_import_isolation.py (3 tests)

### T411 — Run Quality Gates
- **Priority:** HIGH
- **Category:** Validation
- **Description:** Run ruff, mypy, pytest, pip check; fix all issues
- **Acceptance Criteria:** All quality gates pass
- **Dependencies:** T410
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** All 111 tests pass; ruff 0 violations; mypy 0 errors; pip check clean

### T412 — Create Documentation and Reports
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create docs/PHASE4A_DOMAIN_MODEL_REFERENCE.md and reports/PHASE4A_DOMAIN_MODELS_REPORT.md
- **Acceptance Criteria:** Both files present with complete content
- **Dependencies:** T411
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Both files written to disk

### T413 — Update State Files
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Update SYSTEM_STATE.md, TODO.md, DECISION_LOG.md, reports/latest_phase_report.md for Phase 4A
- **Acceptance Criteria:** All state files consistent; Phase 4B as exact next task
- **Dependencies:** T412
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Edits to all four state files

## Phase 4B — Loaders and Validation

### T4B01 — Implement RepositoryLoaderBase
- **Priority:** HIGH
- **Category:** Repositories
- **Description:** Implement abstract base with resolve_identity and resolve_snapshot in src/benchmark/repositories/base.py
- **Acceptance Criteria:** Base class defines interface; subclasses can override resolve_identity and resolve_snapshot
- **Dependencies:** T413
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/repositories/base.py

### T4B02 — Implement Manifest Models
- **Priority:** HIGH
- **Category:** Repositories
- **Description:** Implement RepositoryManifest, RepositoryVersionEntry, RepositoryProfile, ManifestCollection (frozen dataclasses) in src/benchmark/repositories/manifest.py
- **Acceptance Criteria:** All models frozen; validation rejects empties; duplicate detection in collection
- **Dependencies:** T4B01
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/repositories/manifest.py

### T4B03 — Implement RepositoryLoader
- **Priority:** HIGH
- **Category:** Repositories
- **Description:** Implement YAML loading from manifests/ and repository_profiles/ in src/benchmark/repositories/loader.py
- **Acceptance Criteria:** Loads real YAML files; builds ManifestCollection; raises typed errors on missing/invalid files
- **Dependencies:** T4B02
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/repositories/loader.py

### T4B04 — Implement Snapshot Metadata and Validation
- **Priority:** HIGH
- **Category:** Repositories
- **Description:** Implement SnapshotMetadata, create_snapshot_metadata(), validate_snapshot() in src/benchmark/repositories/snapshot.py
- **Acceptance Criteria:** Metadata creation validates fields; snapshot validation reports issues without raising
- **Dependencies:** T4B03
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/repositories/snapshot.py

### T4B05 — Implement Workspace Isolation
- **Priority:** HIGH
- **Category:** Repositories
- **Description:** Implement WorkspacePath, validate_workspace_path(), check_isolation() in src/benchmark/repositories/workspace.py
- **Acceptance Criteria:** Isolation check prevents same-path and nested-path violations; nonexistent paths allowed
- **Dependencies:** T4B04
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/repositories/workspace.py

### T4B06 — Implement Repositories Package Init
- **Priority:** HIGH
- **Category:** Repositories
- **Description:** Create src/benchmark/repositories/__init__.py with public exports
- **Acceptance Criteria:** All public classes and functions exported
- **Dependencies:** T4B05
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/repositories/__init__.py

### T4B07 — Implement ScenarioModel
- **Priority:** HIGH
- **Category:** Scenarios
- **Description:** Implement ScenarioModel dataclass with to_core_scenario() and dual-format expected_actions parsing in src/benchmark/scenarios/models.py
- **Acceptance Criteria:** Both standard and action-grouped YAML formats parsed; deduplication; conversion to core Scenario
- **Dependencies:** T413
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/scenarios/models.py

### T4B08 — Implement ScenarioLoader
- **Priority:** HIGH
- **Category:** Scenarios
- **Description:** Implement ScenarioLoader with load_all() and load_by_repository() in src/benchmark/scenarios/loader.py
- **Acceptance Criteria:** Loads all 24 real scenario YAMLs; raises typed errors on missing/invalid files
- **Dependencies:** T4B07
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/scenarios/loader.py

### T4B09 — Implement ScenarioValidator
- **Priority:** HIGH
- **Category:** Scenarios
- **Description:** Implement ScenarioValidator with required field checks and duplicate action detection in src/benchmark/scenarios/validator.py
- **Acceptance Criteria:** Validates required fields; detects duplicate expected_actions; validate_all returns all errors
- **Dependencies:** T4B08
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/scenarios/validator.py

### T4B10 — Implement ScenarioSequencer
- **Priority:** HIGH
- **Category:** Scenarios
- **Description:** Implement ScenarioSequencer ordering scenarios by blast_radius (localized → moderate → cross_cutting) in src/benchmark/scenarios/sequencing.py
- **Acceptance Criteria:** Ordering correct; ties broken by scenario_id; empty list handled; by-repository filtering works
- **Dependencies:** T4B09
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/scenarios/sequencing.py

### T4B11 — Implement Scenarios Package Init
- **Priority:** HIGH
- **Category:** Scenarios
- **Description:** Create src/benchmark/scenarios/__init__.py with public exports
- **Acceptance Criteria:** All public classes and functions exported
- **Dependencies:** T4B10
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/scenarios/__init__.py

### T4B12 — Write Repository Tests
- **Priority:** HIGH
- **Category:** Tests
- **Description:** Write unit tests for manifest (15), loader (8), snapshot (12), workspace (9); integration test (6)
- **Acceptance Criteria:** All 50 repository tests pass
- **Dependencies:** T4B06
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** 4 unit + 1 integration test files (50 tests)

### T4B13 — Write Scenario Tests
- **Priority:** HIGH
- **Category:** Tests
- **Description:** Write unit tests for models (11), loader (9), validator (7), sequencing (5); integration test (5)
- **Acceptance Criteria:** All 37 scenario tests pass
- **Dependencies:** T4B11
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** 4 unit + 1 integration test files (37 tests)

### T4B14 — Write Loaders Contract Tests
- **Priority:** HIGH
- **Category:** Tests
- **Description:** Write contract tests verifying RepositoryLoader and ScenarioLoader conform to RepositoryAdapter and ScenarioProvider protocols
- **Acceptance Criteria:** All 4 contract tests pass
- **Dependencies:** T4B12, T4B13
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** tests/contract/test_loaders_contract.py (4 tests)

### T4B15 — Run Quality Gates
- **Priority:** HIGH
- **Category:** Validation
- **Description:** Run ruff, mypy, pytest, pip check; fix all issues
- **Acceptance Criteria:** All quality gates pass; 206 total tests
- **Dependencies:** T4B14
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** 206/206 tests pass; ruff 0 violations; mypy 0 errors; pip check clean

### T4B16 — Create Documentation and Reports
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create docs/PHASE4B_LOADERS_AND_VALIDATION_REFERENCE.md and reports/PHASE4B_LOADERS_AND_VALIDATION_REPORT.md
- **Acceptance Criteria:** Both files present with complete content
- **Dependencies:** T4B15
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Both files written to disk

### T4B17 — Update State Files
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Update SYSTEM_STATE.md, TODO.md, DECISION_LOG.md, reports/latest_phase_report.md for Phase 4B
- **Acceptance Criteria:** All state files consistent; Phase 4C as exact next task
- **Dependencies:** T4B16
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Edits to all four state files

## Phase 4C — Model Backends

### T4C01 — Create LLM Package Structure
- **Priority:** HIGH
- **Category:** LLM
- **Description:** Create src/benchmark/llm/ package with __init__.py, base.py, mock_backend.py, dry_run_backend.py, kaggle_qwen_backend.py
- **Acceptance Criteria:** Package imports without torch or transformers
- **Dependencies:** T4B17
- **Status:** PENDING
- **Owner:** OpenCode
- **Evidence:** Package exists; import isolation verified

### T4C02 — Implement Backend Base and Registry Integration
- **Priority:** HIGH
- **Category:** LLM
- **Description:** Implement BackendFactory class that registers MockLLMBackend, DryRunLLMBackend, KaggleQwenBackend in a Registry and creates them by name
- **Acceptance Criteria:** Factory creates correct backend given name; unknown names raise typed errors
- **Dependencies:** T4C01
- **Status:** PENDING
- **Owner:** OpenCode
- **Evidence:** src/benchmark/llm/ and associated tests

### T4C03 — Implement MockLLMBackend
- **Priority:** HIGH
- **Category:** LLM
- **Description:** Implement deterministic mock backend returning fixture responses
- **Acceptance Criteria:** Returns configured response; LLMResponse with correct token_usage; deterministic
- **Dependencies:** T4C01
- **Status:** PENDING
- **Owner:** OpenCode
- **Evidence:** src/benchmark/llm/mock_backend.py

### T4C04 — Implement DryRunLLMBackend
- **Priority:** HIGH
- **Category:** LLM
- **Description:** Implement dry-run backend that loads fixture responses from files
- **Acceptance Criteria:** Reads responses from JSON files; falls back to default response; never calls an API
- **Dependencies:** T4C01
- **Status:** PENDING
- **Owner:** OpenCode
- **Evidence:** src/benchmark/llm/dry_run_backend.py

### T4C05 — Implement KaggleQwenBackend Skeleton
- **Priority:** HIGH
- **Category:** LLM
- **Description:** Implement safe skeleton with lazy torch/transformers imports; raises informative error if called outside Kaggle
- **Acceptance Criteria:** Imports without torch (lazy); generates sensible error message when called locally; actual inference code deferred to Kaggle
- **Dependencies:** T4C01
- **Status:** PENDING
- **Owner:** OpenCode
- **Evidence:** src/benchmark/llm/kaggle_qwen_backend.py; import test passes without torch

### T4C06 — Write Backend Tests
- **Priority:** HIGH
- **Category:** Tests
- **Description:** Write tests for mock backend deterministic output; dry-run fixture loading; import test that Kaggle backend does NOT require torch; factory integration tests
- **Acceptance Criteria:** All tests pass; import isolation verified
- **Dependencies:** T4C02, T4C03, T4C04, T4C05
- **Status:** PENDING
- **Owner:** OpenCode
- **Evidence:** Test files

### T4C07 — Run Quality Gates
- **Priority:** HIGH
- **Category:** Validation
- **Description:** Run ruff, mypy, pytest, pip check; fix all issues
- **Acceptance Criteria:** All quality gates pass
- **Dependencies:** T4C06
- **Status:** PENDING
- **Owner:** OpenCode
- **Evidence:** All tests pass; ruff 0 violations; mypy 0 errors; pip check clean

### T4C08 — Create Documentation and Reports
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create docs/PHASE4C_MODEL_BACKENDS_REFERENCE.md and reports/PHASE4C_MODEL_BACKENDS_REPORT.md
- **Acceptance Criteria:** Both files present with complete content
- **Dependencies:** T4C07
- **Status:** PENDING
- **Owner:** OpenCode
- **Evidence:** Both files written to disk

### T4C09 — Update State Files
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Update SYSTEM_STATE.md, TODO.md, DECISION_LOG.md, reports/latest_phase_report.md for Phase 4C
- **Acceptance Criteria:** All state files consistent; Phase 4D as exact next task
- **Dependencies:** T4C08
- **Status:** PENDING
- **Owner:** OpenCode
- **Evidence:** Edits to all four state files

### T4C10 — Branch Workflow (Commit, Push, Merge)
- **Priority:** HIGH
- **Category:** VCS
- **Description:** Create phase/4c-model-backends branch; commit all Phase 4C work; push branch; safe merge to main; push main
- **Acceptance Criteria:** Branch created, committed, pushed, merged; main clean and synced with origin
- **Dependencies:** T4C07
- **Status:** PENDING
- **Owner:** OpenCode
- **Evidence:** Git log shows branch/merge/push
