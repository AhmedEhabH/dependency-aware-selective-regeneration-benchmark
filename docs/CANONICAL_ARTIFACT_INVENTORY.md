# Canonical Artifact Inventory

**Audit Date:** 2026-07-24
**Canonical Root:** `project/` (where `.git` lives)
**Branch:** `audit/canonical-project-architecture`
**Purpose:** Exhaustive inventory of every significant artifact group in the project.

---

## Artifact ID Conventions

- **AID-SCI-xxx** — Scientific artifacts
- **AID-SRC-xxx** — Source artifacts
- **AID-DEP-xxx** — Deployment artifacts
- **AID-RUN-xxx** — Runtime artifacts
- **AID-GEN-xxx** — Generated / disposable artifacts

---

## Scientific Artifacts

### AID-SCI-001 — Paper Inputs (PDF)

| Field | Value |
|-------|-------|
| Name | MSc Proposal PDF |
| Physical Path | `<parent>/inputs/paper/MSc_Proposal_Selective_Regeneration_Revised.pdf` |
| Artifact Type | Scientific source (PDF) |
| Purpose | Authoritative constraint for all scientific decisions |
| Authoritative Source | Immutable external input |
| Generated Derivative | None |
| Runtime-Only or Source-Controlled | Source-controlled (outside Git, immutable) |
| Git-Tracked Status | Not tracked (outside repo) |
| Owner Component | Research protocol |
| Producers | Original author (MSc student) |
| Consumers | Protocol definition, scenario design |
| Update Trigger | None (immutable) |
| Synchronization Method | None |
| Expected Checksum Relationship | Fixed SHA-256 per commit |
| Safe to Delete | No |
| Contains Scientific Evidence | Yes (proposal only, not results) |
| Contains Private/Hidden Material | No |
| Current Consistency Status | Consistent (unmodified since acquisition) |

### AID-SCI-002 — Paper Inputs (LaTeX)

| Field | Value |
|-------|-------|
| Name | MSc Proposal LaTeX |
| Physical Path | `<parent>/inputs/paper/MSc_Proposal_Selective_Regeneration_Revised.tex` |
| Artifact Type | Scientific source (LaTeX) |
| Purpose | Authoritative constraint (editable source) |
| Authoritative Source | Immutable external input |
| Generated Derivative | The PDF is a derivative of this .tex |
| Runtime-Only or Source-Controlled | Source-controlled (outside Git) |
| Git-Tracked Status | Not tracked |
| Owner Component | Research protocol |
| Producers | Original author |
| Consumers | Protocol definition |
| Update Trigger | None (immutable) |
| Synchronization Method | None |
| Expected Checksum Relationship | PDF should be derivable from .tex |
| Safe to Delete | No |
| Contains Scientific Evidence | Yes |
| Contains Private/Hidden Material | No |
| Current Consistency Status | Consistent |

### AID-SCI-003 — Frozen Research Protocol

| Field | Value |
|-------|-------|
| Name | FINAL_RESEARCH_PROTOCOL.md |
| Physical Path | `project/docs/FINAL_RESEARCH_PROTOCOL.md` |
| Artifact Type | Frozen protocol document (Markdown) |
| Purpose | Canonical research protocol v1.0 |
| Authoritative Source | `docs/` (canonical Git-tracked) |
| Generated Derivative | None (frozen) |
| Runtime-Only or Source-Controlled | Source-controlled |
| Git-Tracked Status | Tracked |
| Owner Component | Research protocol |
| Producers | Phase 2B protocol freeze |
| Consumers | All benchmark code, scenario design, evaluation |
| Update Trigger | Formal protocol amendment only |
| Synchronization Method | Git commit |
| Expected Checksum Relationship | SHA-256 `9D4A140C1CBA19C3076AF8C71AD859F243C31836FECD6026C2CD86CFC271B148` |
| Safe to Delete | No |
| Contains Scientific Evidence | Yes (research design) |
| Contains Private/Hidden Material | No |
| Current Consistency Status | Frozen, checksum verified |

### AID-SCI-004 — Frozen Companion Docs (7 docs)

| Field | Value |
|-------|-------|
| Names | GROUND_TRUTH_PROTOCOL.md, SCENARIO_TAXONOMY.md, STATISTICAL_ANALYSIS_PLAN.md, EXECUTION_AND_FAILURE_POLICY.md, LEAKAGE_PREVENTION_PROTOCOL.md, REPRODUCIBILITY_PROTOCOL.md, RESEARCHER_DECISIONS_DA_AC.md |
| Physical Path | `project/docs/` (each) |
| Artifact Type | Frozen protocol companion documents (Markdown) |
| Purpose | Supporting protocols for the research |
| Authoritative Source | `project/docs/` |
| Generated Derivative | None |
| Runtime-Only or Source-Controlled | Source-controlled |
| Git-Tracked Status | Tracked |
| Owner Component | Research protocol |
| Producers | Phase 2B |
| Consumers | All downstream code and scenario design |
| Update Trigger | Formal amendment only |
| Synchronization Method | Git commit |
| Expected Checksum Relationship | Known SHA-256 per document (recorded in SYSTEM_STATE.md) |
| Safe to Delete | No |
| Contains Scientific Evidence | Yes |
| Contains Private/Hidden Material | No |
| Current Consistency Status | Frozen, checksum verified against SYSTEM_STATE.md |

### AID-SCI-005 — Scenarios (24 YAML)

| Field | Value |
|-------|-------|
| Name | Scenario definitions |
| Physical Path | `project/benchmark_data/scenarios/*.yaml` (24 files) |
| Artifact Type | Scientific input data (YAML) |
| Purpose | Define repository-specific requirement changes, acceptance criteria, expected actions |
| Authoritative Source | `project/benchmark_data/scenarios/` |
| Generated Derivative | Bundled copies in `kaggle_upload/data/scenarios/` |
| Runtime-Only or Source-Controlled | Source-controlled |
| Git-Tracked Status | Tracked |
| Owner Component | Scenario design (Phase 3) |
| Producers | Phase 3 scenario generation |
| Consumers | ScenarioLoader, strategies, evaluation |
| Update Trigger | Protocol amendment or scenario refinement per DA-07 |
| Synchronization Method | Git commit; bundle via `kaggle_upload/data/` |
| Expected Checksum Relationship | Canonical → bundle should be identical |
| Safe to Delete | No |
| Contains Scientific Evidence | Yes (contains expected actions / ground truth) |
| Contains Private/Hidden Material | Hidden tests field in YAML |
| Current Consistency Status | Consistent. 24/24 files present. Outer data bundle matches canonical. |

### AID-SCI-006 — Repository Manifests

| Field | Value |
|-------|-------|
| Names | `repositories.yaml`, `repository_versions.yaml` |
| Physical Path | `project/benchmark_data/manifests/` |
| Artifact Type | Scientific input data (YAML) |
| Purpose | Pin repository URLs, versions, commit SHAs |
| Authoritative Source | `project/benchmark_data/manifests/` |
| Generated Derivative | Bundled in `kaggle_upload/data/manifests/` |
| Runtime-Only or Source-Controlled | Source-controlled |
| Git-Tracked Status | Tracked |
| Owner Component | Phase 3 repository selection |
| Producers | Phase 3 |
| Consumers | RepositoryLoader, scenario definitions |
| Update Trigger | Repository version change (protocol amendment) |
| Synchronization Method | Git commit; bundle |
| Expected Checksum Relationship | Identity |
| Safe to Delete | No |
| Contains Scientific Evidence | Yes (version pins affect reproducibility) |
| Contains Private/Hidden Material | No |
| Current Consistency Status | Consistent |

### AID-SCI-007 — Repository Profiles

| Field | Value |
|-------|-------|
| Names | `todo.yaml`, `djangocms.yaml`, `saleor.yaml` |
| Physical Path | `project/benchmark_data/repository_profiles/` |
| Artifact Type | Scientific input data (YAML) |
| Purpose | Architecture descriptions per repository |
| Authoritative Source | `project/benchmark_data/repository_profiles/` |
| Generated Derivative | Bundled in `kaggle_upload/data/repository_profiles/` |
| Runtime-Only or Source-Controlled | Source-controlled |
| Git-Tracked Status | Tracked |
| Owner Component | Phase 3 |
| Producers | Phase 3 |
| Consumers | ProfileGraphBuilder, strategies |
| Update Trigger | Profile refinement |
| Synchronization Method | Git commit; bundle |
| Expected Checksum Relationship | Identity |
| Safe to Delete | No |
| Contains Scientific Evidence | Yes (architecture descriptions inform strategies) |
| Contains Private/Hidden Material | No |
| Current Consistency Status | Consistent |

### AID-SCI-008 — Ground Truth

| Field | Value |
|-------|-------|
| Name | Ground truth (expected actions) |
| Physical Path | Embedded in `project/benchmark_data/scenarios/*.yaml` (expected_actions field) |
| Artifact Type | Scientific annotation data |
| Purpose | Correct answer key for evaluating strategy predictions |
| Authoritative Source | `project/benchmark_data/scenarios/*.yaml` (embedded) |
| Generated Derivative | None (extracted at evaluation time) |
| Runtime-Only or Source-Controlled | Source-controlled |
| Git-Tracked Status | Tracked (embedded in scenario YAMLs) |
| Owner Component | Phase 3 scenario design |
| Producers | Phase 3 |
| Consumers | Evaluation engine (comparison, metrics) |
| Update Trigger | Scenario refinement |
| Synchronization Method | Git commit |
| Expected Checksum Relationship | N/A (embedded) |
| Safe to Delete | No |
| Contains Scientific Evidence | Yes (primary evaluation target) |
| Contains Private/Hidden Material | Hidden tests referenced but not included in public YAML |
| Current Consistency Status | Consistent |

### AID-SCI-009 — Metrics and Statistical Plans

| Field | Value |
|-------|-------|
| Name | Statistical analysis plan |
| Physical Path | `project/docs/STATISTICAL_ANALYSIS_PLAN.md` |
| Artifact Type | Frozen protocol document |
| Purpose | Defines statistical tests, margins, corrections |
| Authoritative Source | `project/docs/STATISTICAL_ANALYSIS_PLAN.md` |
| Generated Derivative | Implementation in `src/benchmark/statistics/` |
| Runtime-Only or Source-Controlled | Source-controlled |
| Git-Tracked Status | Tracked |
| Owner Component | Research protocol |
| Producers | Phase 2B |
| Consumers | Statistics package, evaluation |
| Update Trigger | Protocol amendment |
| Synchronization Method | Git commit |
| Expected Checksum Relationship | SHA-256 `FA8B76C41FF05462E80675B297917A904ECD4605CA5AD54C84740A38B6AB1D4C` |
| Safe to Delete | No |
| Contains Scientific Evidence | Yes (analysis methodology) |
| Contains Private/Hidden Material | No |
| Current Consistency Status | Frozen, checksum verified |

---

## Source Artifacts

### AID-SRC-001 — seven_arm_benchmark.py (Canonical)

| Field | Value |
|-------|-------|
| Name | Main benchmark CLI script |
| Physical Path | `project/seven_arm_benchmark.py` |
| Artifact Type | Python executable script |
| Purpose | CLI entry point for dry-run and real benchmark execution |
| Authoritative Source | `project/seven_arm_benchmark.py` |
| Generated Derivative | Bundled copies in `project/kaggle_upload/code/` and `<parent>/kaggle_upload/code/` |
| Runtime-Only or Source-Controlled | Source-controlled |
| Git-Tracked Status | Tracked |
| Owner Component | CLI / Entry point |
| Producers | Phase 4E-4F implementation |
| Consumers | CLI users, Kaggle notebook, tests |
| Update Trigger | Code changes; bundle regeneration |
| Synchronization Method | Git commit; bundle copy |
| Expected Checksum Relationship | Canonical = inner bundle (identity), outer bundle may be stale |
| Safe to Delete | No |
| Contains Scientific Evidence | No (execution logic) |
| Contains Private/Hidden Material | No |
| Current Consistency Status | Canonical SHA-256: `D28E2D9DFB4E3067418017303DAF813483F94CDC45849F5168E3470B0D0828DA`. Inner bundle MATCHES. Outer bundle DIFFERS (stale). |

### AID-SRC-002 — src/benchmark/ package

| Field | Value |
|-------|-------|
| Name | Benchmark source package |
| Physical Path | `project/src/benchmark/` (14 subpackages, ~55 .py files) |
| Artifact Type | Python package (source) |
| Purpose | All benchmark logic: core, config, repositories, scenarios, graph, strategies, llm, execution, evaluation, comparison, statistics, checkpoint, selection |
| Authoritative Source | `project/src/benchmark/` |
| Generated Derivative | Bundled in `project/kaggle_upload/code/src/` and `<parent>/kaggle_upload/code/src/` |
| Runtime-Only or Source-Controlled | Source-controlled |
| Git-Tracked Status | Tracked |
| Owner Component | All benchmark implementation |
| Producers | Phases 4A–4F, checkpoint/resume |
| Consumers | CLI, tests, evaluation |
| Update Trigger | Code changes |
| Synchronization Method | Git commit; bundle copy |
| Expected Checksum Relationship | Canonical = inner bundle (66/66 files match after normalization). Outer bundle has 1 content mismatch. |
| Safe to Delete | No |
| Contains Scientific Evidence | No (implementation) |
| Contains Private/Hidden Material | No |
| Current Consistency Status | Inner bundle consistent (66/66 match). Outer bundle has 1 content mismatch (`checkpoint/hf_sync.py`). |

### AID-SRC-003 — Configuration Profiles

| Field | Value |
|-------|-------|
| Names | `smoke.yaml`, `pilot.yaml`, `research.yaml` |
| Physical Path | `project/configs/` |
| Artifact Type | YAML configuration |
| Purpose | Execution profiles for benchmark runs |
| Authoritative Source | `project/configs/` |
| Generated Derivative | Bundled in `project/kaggle_upload/code/configs/` |
| Runtime-Only or Source-Controlled | Source-controlled |
| Git-Tracked Status | Tracked |
| Owner Component | Execution configuration |
| Producers | Phase 4 |
| Consumers | Benchmark pipeline, CLI |
| Update Trigger | Profile parameter changes |
| Synchronization Method | Git commit; bundle |
| Expected Checksum Relationship | Canonical = bundle (line-ending differences only) |
| Safe to Delete | No |
| Contains Scientific Evidence | No (execution parameters) |
| Contains Private/Hidden Material | No |
| Current Consistency Status | Consistent (only CRLF differences between canonical and inner bundle) |

### AID-SRC-004 — Tests

| Field | Value |
|-------|-------|
| Name | Test suite |
| Physical Path | `project/tests/` (~44 .py files across unit, integration, contract, fixtures) |
| Artifact Type | Python test files |
| Purpose | Verify correctness of all benchmark components |
| Authoritative Source | `project/tests/` |
| Generated Derivative | None |
| Runtime-Only or Source-Controlled | Source-controlled |
| Git-Tracked Status | Tracked |
| Owner Component | All implementation phases |
| Producers | Phases 4A–4F, checkpoint/resume |
| Consumers | Developers, CI |
| Update Trigger | Code changes, defect fixes |
| Synchronization Method | Git commit |
| Expected Checksum Relationship | Self-consistent |
| Safe to Delete | No |
| Contains Scientific Evidence | No (verification) |
| Contains Private/Hidden Material | No |
| Current Consistency Status | Consistent. 504 tests pass, 1 skipped (torch). |

### AID-SRC-005 — Notebook (Canonical)

| Field | Value |
|-------|-------|
| Name | seven_arm_benchmark.ipynb |
| Physical Path | `project/notebooks/seven_arm_benchmark.ipynb` |
| Artifact Type | Jupyter notebook |
| Purpose | Kaggle execution entry point |
| Authoritative Source | `project/notebooks/` |
| Generated Derivative | Bundled copies in `project/kaggle_upload/notebooks/` and `<parent>/kaggle_upload/notebooks/` |
| Runtime-Only or Source-Controlled | Source-controlled |
| Git-Tracked Status | Tracked |
| Owner Component | Notebook |
| Producers | Phase 4F |
| Consumers | Kaggle executor |
| Update Trigger | Notebook changes |
| Synchronization Method | Git commit; bundle |
| Expected Checksum Relationship | Canonical = inner bundle (match). Outer bundle differs. |
| Safe to Delete | No |
| Contains Scientific Evidence | No (execution wrapper) |
| Contains Private/Hidden Material | No |
| Current Consistency Status | Inner bundle MATCHES (`A153DE85`). Outer bundle differs (stale). |

### AID-SRC-006 — Environment Files

| Field | Value |
|-------|-------|
| Names | `environment.yml`, `requirements-dev.txt`, `requirements-kaggle.txt`, `requirements-lock.txt` |
| Physical Path | `project/` (root) |
| Artifact Type | Dependency specification |
| Purpose | Reproducible environment definition |
| Authoritative Source | `project/` root |
| Generated Derivative | `requirements-kaggle.txt` bundled in `kaggle_upload/code/` |
| Runtime-Only or Source-Controlled | Source-controlled |
| Git-Tracked Status | Tracked |
| Owner Component | Environment |
| Producers | Phase 0, updated per phase |
| Consumers | Conda, pip, Kaggle environment |
| Update Trigger | Dependency changes |
| Synchronization Method | Git commit; bundle |
| Expected Checksum Relationship | Canonical = bundle (line-ending differences only) |
| Safe to Delete | No |
| Contains Scientific Evidence | No |
| Contains Private/Hidden Material | No |
| Current Consistency Status | Consistent |

### AID-SRC-007 — Scripts (empty)

| Field | Value |
|-------|-------|
| Name | scripts/ |
| Physical Path | `project/scripts/` |
| Artifact Type | Empty directory |
| Purpose | Intended for utility scripts (validate_protocol.py, build_upload_bundle.py, etc.) |
| Authoritative Source | N/A (empty) |
| Generated Derivative | None |
| Runtime-Only or Source-Controlled | Source-controlled |
| Git-Tracked Status | Tracked (empty dir) |
| Owner Component | Infrastructure |
| Producers | Not yet created |
| Consumers | Not yet |
| Update Trigger | When scripts are implemented |
| Synchronization Method | N/A |
| Expected Checksum Relationship | N/A |
| Safe to Delete | No (structural placeholder) |
| Contains Scientific Evidence | No |
| Contains Private/Hidden Material | No |
| Current Consistency Status | Empty (placeholder) |

### AID-SRC-008 — pyproject.toml

| Field | Value |
|-------|-------|
| Name | Project metadata and tool configuration |
| Physical Path | `project/pyproject.toml` |
| Artifact Type | Build/configuration file (TOML) |
| Purpose | Package metadata, ruff/mypy/pytest config |
| Authoritative Source | `project/pyproject.toml` |
| Generated Derivative | Bundled in `kaggle_upload/code/` |
| Runtime-Only or Source-Controlled | Source-controlled |
| Git-Tracked Status | Tracked |
| Owner Component | Build system |
| Producers | Phase 4A |
| Consumers | pip, ruff, mypy, pytest |
| Update Trigger | Configuration changes |
| Synchronization Method | Git commit; bundle |
| Expected Checksum Relationship | Canonical = inner bundle (MATCH). Outer bundle also MATCHES. |
| Safe to Delete | No |
| Contains Scientific Evidence | No |
| Contains Private/Hidden Material | No |
| Current Consistency Status | Consistent |

---

## Deployment Artifacts

### AID-DEP-001 — Inner Kaggle Code Bundle (canonical bundle)

| Field | Value |
|-------|-------|
| Name | Inner kaggle_upload/code/ |
| Physical Path | `project/kaggle_upload/code/` |
| Artifact Type | Deployment bundle (directory tree) |
| Purpose | Kaggle Code Dataset payload |
| Authoritative Source | Generated from canonical source |
| Generated Derivative | Yes (from `project/` source + configs) |
| Runtime-Only or Source-Controlled | Source-controlled (tracked) |
| Git-Tracked Status | Tracked |
| Owner Component | Deployment |
| Producers | Bundle generation process |
| Consumers | Kaggle notebook (mounted as Dataset) |
| Update Trigger | Source code changes requiring bundle regeneration |
| Synchronization Method | Manual regeneration + commit |
| Expected Checksum Relationship | Source files should match canonical originals (66/66 verified) |
| Safe to Delete | Yes (regenerable) |
| Contains Scientific Evidence | No |
| Contains Private/Hidden Material | No |
| Current Consistency Status | ***Contains `.git/` directory (full repo history)*** — should not be in deployment bundle. Contains `__pycache__/`, `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`, `*.egg-info/`, empty `benchmark_data/`, empty `docs/`. |

### AID-DEP-002 — Inner Kaggle Data Bundle

| Field | Value |
|-------|-------|
| Name | Inner kaggle_upload/data/ |
| Physical Path | `project/kaggle_upload/data/` |
| Artifact Type | Deployment bundle (directory tree) |
| Purpose | Kaggle Data Dataset payload |
| Authoritative Source | Generated from benchmark_data/ |
| Generated Derivative | Yes |
| Runtime-Only or Source-Controlled | Source-controlled (tracked) |
| Git-Tracked Status | Tracked |
| Owner Component | Deployment |
| Producers | Bundle generation |
| Consumers | Kaggle notebook |
| Update Trigger | Data changes |
| Synchronization Method | Manual regeneration |
| Expected Checksum Relationship | Files should match canonical benchmark_data/ |
| Safe to Delete | Yes (regenerable) |
| Contains Scientific Evidence | Yes (scenarios contain ground truth) |
| Contains Private/Hidden Material | Hidden test references |
| Current Consistency Status | ***EMPTY*** — `project/kaggle_upload/data/` has no files. The outer bundle `<parent>/kaggle_upload/data/` has the actual data. This is a synchronization failure. |

### AID-DEP-003 — Outer Kaggle Code Bundle (stale)

| Field | Value |
|-------|-------|
| Name | Outer kaggle_upload/code/ |
| Physical Path | `<parent>/kaggle_upload/code/` |
| Artifact Type | Deployment bundle (directory tree) — STALE |
| Purpose | Previously generated Kaggle Code Dataset payload |
| Authoritative Source | Should be identical to inner bundle |
| Generated Derivative | Yes (stale version) |
| Runtime-Only or Source-Controlled | Outside Git |
| Git-Tracked Status | Not tracked (outside repo) |
| Owner Component | Deployment (legacy) |
| Producers | Previous bundle generation |
| Consumers | (no longer used) |
| Update Trigger | Should be regenerated from canonical when needed |
| Synchronization Method | Manual |
| Expected Checksum Relationship | Should match canonical. Currently 1 source file content-mismatches. |
| Safe to Delete | Yes, after verifying inner bundle is correct |
| Contains Scientific Evidence | No |
| Contains Private/Hidden Material | No |
| Current Consistency Status | ***STALE*** — `seven_arm_benchmark.py` content-differs, `hf_sync.py` content-differs. Does NOT have `.git/` or caches. |

### AID-DEP-004 — Outer Kaggle Data Bundle (populated)

| Field | Value |
|-------|-------|
| Name | Outer kaggle_upload/data/ |
| Physical Path | `<parent>/kaggle_upload/data/` |
| Artifact Type | Deployment bundle (directory tree) — POPULATED |
| Purpose | Contains actual scenario, manifest, profile YAMLs |
| Authoritative Source | `project/benchmark_data/` |
| Generated Derivative | Yes (correct data copy) |
| Runtime-Only or Source-Controlled | Outside Git |
| Git-Tracked Status | Not tracked |
| Owner Component | Deployment |
| Producers | Previous bundle generation |
| Consumers | (no longer actively used) |
| Update Trigger | Should be regenerated along with code bundle |
| Synchronization Method | Manual |
| Expected Checksum Relationship | All 29 data files MATCH canonical. |
| Safe to Delete | Yes, after migrating to inner bundle |
| Contains Scientific Evidence | Yes |
| Contains Private/Hidden Material | Yes (hidden test refs in scenarios) |
| Current Consistency Status | Data content is CORRECT (matches canonical). However this bundle lives outside Git at `<parent>/kaggle_upload/data/` while the inner one at `project/kaggle_upload/data/` is EMPTY. |

### AID-DEP-005 — Kaggle Notebook Bundle

| Field | Value |
|-------|-------|
| Name | Bundled notebook |
| Physical Path | `project/kaggle_upload/notebooks/seven_arm_benchmark.ipynb` and `<parent>/kaggle_upload/notebooks/seven_arm_benchmark.ipynb` |
| Artifact Type | Deployment bundle (ipynb) |
| Purpose | Notebook for Kaggle execution |
| Authoritative Source | `project/notebooks/seven_arm_benchmark.ipynb` |
| Generated Derivative | Yes |
| Runtime-Only or Source-Controlled | Tracked (inner), not tracked (outer) |
| Git-Tracked Status | Tracked (inner), untracked (outer) |
| Owner Component | Deployment |
| Producers | Bundle generation |
| Consumers | Kaggle |
| Update Trigger | Notebook changes |
| Synchronization Method | Manual |
| Expected Checksum Relationship | Inner MATCHES. Outer DIFFERS (stale). |
| Safe to Delete | Yes (regenerable) |
| Contains Scientific Evidence | No |
| Contains Private/Hidden Material | No |
| Current Consistency Status | Inner MATCHES canonical. Outer is stale (line-ending only) — but still differs in raw hash. |

---

## Runtime Artifacts

### AID-RUN-001 — Local runs/ Directory

| Field | Value |
|-------|-------|
| Name | Local run output |
| Physical Path | `project/runs/` |
| Artifact Type | Runtime output |
| Purpose | Generated run records, logs, checkpoints |
| Authoritative Source | Non-deterministic (generated at runtime) |
| Generated Derivative | Yes |
| Runtime-Only or Source-Controlled | Runtime-only |
| Git-Tracked Status | Gitignored |
| Owner Component | Execution pipeline |
| Producers | BenchmarkRunner |
| Consumers | Evaluation, statistics, HF sync |
| Update Trigger | Every benchmark run |
| Synchronization Method | None (not synced) |
| Expected Checksum Relationship | N/A (non-deterministic) |
| Safe to Delete | Yes |
| Contains Scientific Evidence | Yes (run records are evidence) |
| Contains Private/Hidden Material | No |
| Current Consistency Status | ***Does not exist*** — no `runs/` directory found. |

### AID-RUN-002 — Kaggle /kaggle/working/runs/

| Field | Value |
|-------|-------|
| Name | Kaggle working directory |
| Physical Path | `/kaggle/working/runs/` (Kaggle only) |
| Artifact Type | Runtime output |
| Purpose | Generated on Kaggle during real execution |
| Authoritative Source | N/A (runtime) |
| Generated Derivative | Yes |
| Runtime-Only or Source-Controlled | Runtime-only |
| Git-Tracked Status | N/A (Kaggle) |
| Owner Component | Execution pipeline |
| Producers | BenchmarkRunner on Kaggle |
| Consumers | HF sync, download to local |
| Update Trigger | Every benchmark run on Kaggle |
| Synchronization Method | HF sync |
| Expected Checksum Relationship | N/A |
| Safe to Delete | Yes |
| Contains Scientific Evidence | Yes (run records) |
| Contains Private/Hidden Material | No |
| Current Consistency Status | ***Not examined*** — Kaggle remote only. |

### AID-RUN-003 — Hugging Face Experiment Recovery Files

| Field | Value |
|-------|-------|
| Name | HF Experiment Recovery |
| Physical Path | Remote: `experiments/<profile>/<version>/<tag>/<id>/recovery/` |
| Artifact Type | Remote synced runtime data |
| Purpose | Enables cross-session resume |
| Authoritative Source | Generated (synced from Kaggle) |
| Generated Derivative | Yes |
| Runtime-Only or Source-Controlled | Remote runtime |
| Git-Tracked Status | N/A |
| Owner Component | Checkpoint / HF sync |
| Producers | hf_sync.py |
| Consumers | resume.py, subsequent Kaggle sessions |
| Update Trigger | After each run during --hf-sync |
| Synchronization Method | Hugging Face Dataset API |
| Expected Checksum Relationship | Local checkpoint → remote should be identical |
| Safe to Delete | Yes (regenerable by re-running) |
| Contains Scientific Evidence | Yes (intermediate results) |
| Contains Private/Hidden Material | No |
| Current Consistency Status | ***Not examined*** — remote only. |

### AID-RUN-004 — _auto_resume_temp/

| Field | Value |
|-------|-------|
| Name | Auto-resume temporary directory |
| Physical Path | `project/_auto_resume_temp/` |
| Artifact Type | Runtime temporary directory |
| Purpose | Test fixtures for auto-resume feature |
| Authoritative Source | Generated (empty directories) |
| Generated Derivative | Yes |
| Runtime-Only or Source-Controlled | Tracked (contains empty dir structure) |
| Git-Tracked Status | Tracked |
| Owner Component | Checkpoint/resume |
| Producers | Test setup / resume logic |
| Consumers | Tests |
| Update Trigger | When running resume-related tests |
| Synchronization Method | None |
| Expected Checksum Relationship | N/A (empty dirs) |
| Safe to Delete | Yes |
| Contains Scientific Evidence | No |
| Contains Private/Hidden Material | No |
| Current Consistency Status | Contains only empty directories. All temp files cleaned up. |

### AID-RUN-005 — benchmark-results.zip

| Field | Value |
|-------|-------|
| Name | Benchmark results archive |
| Physical Path | `project/benchmark-results.zip` |
| Artifact Type | Compressed result archive (ZIP) |
| Purpose | Full results package from benchmark run |
| Authoritative Source | Generated (runtime) |
| Generated Derivative | Yes |
| Runtime-Only or Source-Controlled | Runtime-only |
| Git-Tracked Status | Untracked (gitignored? — appears in `git status` as untracked) |
| Owner Component | Execution pipeline |
| Producers | Benchmark run |
| Consumers | Analysis, HF sync |
| Update Trigger | Benchmark completion |
| Synchronization Method | Manual download, HF sync |
| Expected Checksum Relationship | N/A |
| Safe to Delete | Yes |
| Contains Scientific Evidence | Yes (contains all run records) |
| Contains Private/Hidden Material | No |
| Current Consistency Status | Present and untracked. Origin unknown — likely from a previous real/Kaggle run or smoke test. |

---

## Generated / Disposable Artifacts

### AID-GEN-001 — __pycache__/

| Field | Value |
|-------|-------|
| Name | Python bytecode cache |
| Physical Path | Multiple: `project/src/**/__pycache__/`, `project/tests/**/__pycache__/`, `project/kaggle_upload/code/**/__pycache__/`, `project/__pycache__/` |
| Artifact Type | Bytecode cache |
| Purpose | Speed up Python imports |
| Authoritative Source | Generated by Python |
| Generated Derivative | Yes |
| Runtime-Only or Source-Controlled | Runtime-only |
| Git-Tracked Status | Gitignored |
| Owner Component | Python runtime |
| Producers | Python interpreter |
| Consumers | Python import system |
| Update Trigger | Source file modification |
| Synchronization Method | None |
| Expected Checksum Relationship | N/A |
| Safe to Delete | Yes |
| Contains Scientific Evidence | No |
| Contains Private/Hidden Material | No |
| Current Consistency Status | Present in 15+ locations. ***Also present inside deployment bundles*** — should be excluded. |

### AID-GEN-002 — .mypy_cache/

| Field | Value |
|-------|-------|
| Name | MyPy type-checking cache |
| Physical Path | `project/.mypy_cache/`, `project/kaggle_upload/code/.mypy_cache/` |
| Artifact Type | Type-checking cache |
| Purpose | Speed up mypy invocations |
| Authoritative Source | Generated by mypy |
| Generated Derivative | Yes |
| Runtime-Only or Source-Controlled | Runtime-only |
| Git-Tracked Status | Gitignored |
| Owner Component | mypy |
| Producers | mypy |
| Consumers | mypy |
| Update Trigger | Source file modification |
| Synchronization Method | None |
| Expected Checksum Relationship | N/A |
| Safe to Delete | Yes |
| Contains Scientific Evidence | No |
| Contains Private/Hidden Material | No |
| Current Consistency Status | Present. ***Also present inside deployment bundles.*** |

### AID-GEN-003 — .pytest_cache/

| Field | Value |
|-------|-------|
| Name | Pytest cache |
| Physical Path | `project/.pytest_cache/`, `project/kaggle_upload/code/.pytest_cache/` |
| Artifact Type | Test cache |
| Purpose | Speed up pytest re-runs |
| Authoritative Source | Generated by pytest |
| Generated Derivative | Yes |
| Runtime-Only or Source-Controlled | Runtime-only |
| Git-Tracked Status | Gitignored |
| Owner Component | pytest |
| Producers | pytest |
| Consumers | pytest |
| Update Trigger | Test run |
| Synchronization Method | None |
| Expected Checksum Relationship | N/A |
| Safe to Delete | Yes |
| Contains Scientific Evidence | No |
| Contains Private/Hidden Material | No |
| Current Consistency Status | Present. ***Also present inside deployment bundles.*** |

### AID-GEN-004 — .ruff_cache/

| Field | Value |
|-------|-------|
| Name | Ruff cache |
| Physical Path | `project/.ruff_cache/`, `project/kaggle_upload/code/.ruff_cache/` |
| Artifact Type | Linter cache |
| Purpose | Speed up ruff checks |
| Authoritative Source | Generated by ruff |
| Generated Derivative | Yes |
| Runtime-Only or Source-Controlled | Runtime-only |
| Git-Tracked Status | Gitignored |
| Owner Component | ruff |
| Producers | ruff |
| Consumers | ruff |
| Update Trigger | Source file modification |
| Synchronization Method | None |
| Expected Checksum Relationship | N/A |
| Safe to Delete | Yes |
| Contains Scientific Evidence | No |
| Contains Private/Hidden Material | No |
| Current Consistency Status | Present. ***Also present inside deployment bundles.*** |

### AID-GEN-005 — *.egg-info/

| Field | Value |
|-------|-------|
| Name | Package metadata (editable install) |
| Physical Path | `project/src/selective_regen_benchmark.egg-info/`, `project/kaggle_upload/code/src/selective_regen_benchmark.egg-info/` |
| Artifact Type | Package metadata |
| Purpose | Records installed package metadata during `pip install -e .` |
| Authoritative Source | Generated by pip |
| Generated Derivative | Yes |
| Runtime-Only or Source-Controlled | Runtime-only |
| Git-Tracked Status | Gitignored |
| Owner Component | pip |
| Producers | `pip install -e .` |
| Consumers | Python import system |
| Update Trigger | Re-install |
| Synchronization Method | None |
| Expected Checksum Relationship | N/A |
| Safe to Delete | Yes |
| Contains Scientific Evidence | No |
| Contains Private/Hidden Material | No |
| Current Consistency Status | ***Present inside deployment bundles*** — should be excluded. |
