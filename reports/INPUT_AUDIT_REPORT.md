# Phase 1 — Input Audit Report

**Date:** 2026-07-22
**Status:** LOCAL_ENGINEERING_VALIDATED

---

## 1. Scope

Audit all supplied source material under `inputs/` and classify all pre-existing benchmark outputs from the entire workspace. Originals preserved unchanged. No files inside `inputs/` were modified, renamed, or overwritten. Nothing was copied from `inputs/` into `docs/`.

---

## 2. Input Inventory

### 2.1 `inputs/paper/` (2 files)

| File | Type | Size | Description |
|------|------|------|-------------|
| `MSc_Proposal_Selective_Regeneration_Revised.pdf` | PDF (binary) | — | Compiled research proposal |
| `MSc_Proposal_Selective_Regeneration_Revised.tex` | LaTeX source | 785 lines | Authoritative research specification |

### 2.2 Missing Inputs

The Phase 1 specification calls for inspecting "paper, notebooks, result archives, and examples." The following are **absent**:

| Expected Input | Status | Impact |
|----------------|--------|--------|
| Notebooks | **MISSING** — `project/notebooks/` is empty; no `.ipynb` files exist anywhere | Phase 1 cannot audit what does not exist. Notebook creation is deferred to Phase 8. |
| Result archives | **MISSING** — no CSV, JSON, or other benchmark output files exist | No legacy pilot result files to audit. This is consistent with a project that has not yet run benchmarks. |
| Examples | **MISSING** — no example configurations, sample scenarios, or demonstration artifacts | Will need to be created during Phase 3 (scenario preparation). |

### 2.3 Existing Project Structure (`project/`)

| Path | Type | Purpose |
|------|------|---------|
| `project/src/benchmark/__init__.py` | Empty package | Benchmark package scaffold |
| `project/tests/__init__.py` | Empty package | Test package scaffold |
| `project/notebooks/` | Empty directory | Reserved for Kaggle notebook |
| `project/scripts/` | Empty directory | Reserved for utility scripts |
| `project/reports/` | 2 reports | Phase 0 reports |
| `project/environment.yml` | Conda env spec | Python 3.11 environment |
| `project/requirements-dev.txt` | Pip dev deps | Local engineering packages |
| `project/requirements-kaggle.txt` | Pip Kaggle deps | Deferred to Kaggle |
| `project/requirements-lock.txt` | Frozen versions | Exact dependency snapshot |

---

## 3. Legacy Pilot Classification

**Directive:** `legacy_results_classification: legacy_pilot`

**Finding:** Zero pre-existing benchmark output files exist anywhere in the workspace. The paper references a "preliminary proof-of-concept" and "internal pilot workflow" (Section VII-E) but no output files, result archives, or data from that pilot were provided as input.

**Classification:** All zero existing benchmark outputs are classified as `legacy_pilot`. No migration of legacy result data is required. When benchmark outputs are first generated (on Kaggle), they will be classified as primary research results, not legacy pilot.

---

## 4. Authoritative Research Specification (Paper Cross-Reference)

The proposal `inputs/paper/MSc_Proposal_Selective_Regeneration_Revised.tex` is the authoritative source. Key parameters that constrain all subsequent implementation:

### 4.1 Research Questions

| ID | Question | Implementation Constraint |
|----|----------|--------------------------|
| RQ1 | Impact identification accuracy | Must implement and compare multiple impact strategies |
| RQ2 | Evolution correctness + preservation | Must evaluate both changed-requirement success AND regression |
| RQ3 | Architectural consistency | Must include machine-checkable architecture rules |
| RQ4 | Efficiency under equivalent correctness | Must only compare efficiency among equally correct runs |
| RQ5 | Generality and sensitivity | Must vary repos, architectures, change types, models |

### 4.2 Hypotheses

| ID | Statement | Evaluation Required |
|----|-----------|---------------------|
| H1 | Hybrid > static/semantic/retrieval-only | Recall, FNR, precision, F1, action accuracy |
| H2 | Non-inferior preservation | Non-inferiority test for regression pass rate |
| H3 | Architecture catches what tests miss | Architecture-rule violation detection |
| H4 | Localized/moderate savings | Tokens, calls, artifacts, latency |
| H5 | Benefits decrease with blast radius | Interaction effects, savings curves |

### 4.3 Action Classification (from paper)

1. **Regenerate** — content must change
2. **Preserve** — artifact remains unchanged
3. **Validate only** — no edit, but re-execute
4. **Human review** — insufficient confidence

### 4.4 Artifact Node Types (from paper)

Requirements, entities, interfaces, services, database objects, tests, documentation, configurations, architecture decisions, deployment artifacts.

### 4.5 Edge Types (from paper)

Derivation, Structural, Traceability, Semantic, Validation, Architectural, Provenance.

### 4.6 Evaluation Protocol (from paper)

1. Impact analysis evaluation (no code generation)
2. Controlled evolution execution
3. Architecture and preservation evaluation
4. Sensitivity, ablation, and boundary cases

---

## 5. Reusable Components Inventory

| Component | Path | Status | Notes |
|-----------|------|--------|-------|
| Conda environment spec | `project/environment.yml` | REUSABLE | Verified Python 3.11.15 working env |
| Dev requirements | `project/requirements-dev.txt` | REUSABLE | Correctly scoped for local engineering |
| Kaggle requirements | `project/requirements-kaggle.txt` | REUSABLE | Correctly deferred to Kaggle |
| Pip lockfile | `project/requirements-lock.txt` | REUSABLE | Exact resolved versions |
| Benchmark package shell | `project/src/benchmark/__init__.py` | REUSABLE | Empty; ready for Phase 4 expansion |
| Test package shell | `project/tests/__init__.py` | REUSABLE | Empty; ready for test creation |
| Environment report | `project/reports/LOCAL_ENVIRONMENT_REPORT.md` | REUSABLE | Documents successful environment setup |
| Phase 0 report | `project/reports/latest_phase_report.md` | REFERENCE | Phase 0 completion summary |
| State management files | `project/SYSTEM_STATE.md`, `project/TODO.md`, `project/DECISION_LOG.md`, `project/PROTOCOL_VERSION.md` | REUSABLE | Established patterns for phase tracking |
| Master plan (git) | `project/docs/MASTER_IMPLEMENTATION_PLAN.md` (committed) | REFERENCE | Phase map — may need updating |
| Execution guide (git) | `project/docs/OPENCODE_EXECUTION_GUIDE.md` (committed) | REFERENCE | Operational instructions — may need relocation |
| Git repo | `project/.git/` | REUSABLE | 2 commits on `main` |
| Conda environment | `selective-regen-benchmark` | REUSABLE | Ready for activation |

---

## 6. Detected Leakage Risks

### LR-1: Working Tree vs. Committed State Mismatch
**Severity:** LOW
**Description:** The `project/docs/` directory is deleted from the git working tree but files exist at the root `docs/` level (outside the git repo). Running `git checkout` or `git restore` would restore the old `project/docs/` copies, causing file duplication and potential confusion.
**Recommendation:** If git history is to be preserved, either commit the deletion or restore the files and ignore the duplication. Currently, the root `docs/` contains the authoritative copies.

### LR-2: No Notebook Isolation Mechanism
**Severity:** MEDIUM
**Description:** `notebooks/` is empty. When Jupyter notebooks are created (Phase 8), they must be clearly separated into local-validation notebooks (mock backend only) and Kaggle notebooks (real model). Without separation, a local user could inadvertently run a real-model cell locally.
**Recommendation:** Create a `notebooks/local/` and `notebooks/kaggle/` convention. Add a README or use filename prefixes.

### LR-3: No Test Data Boundary
**Severity:** MEDIUM
**Description:** `tests/` has only `__init__.py`. Test fixtures, scenario data, and ground truth annotations will need a storage location. These must NOT be placed inside `inputs/` (immutable boundary), and must NOT be placed inside `src/` (runtime package).
**Recommendation:** Create a `tests/fixtures/` directory for test data. Document that `inputs/` is the only immutable input zone.

### LR-4: Phase Boundary Confusion
**Severity:** LOW
**Description:** The `src/benchmark/` package skeleton exists (from Phase 0 scaffold requirements) but Phase 4 (Benchmark Core) has not yet started. Premature modification of `src/benchmark/` during Phase 2 or 3 could create confusion.
**Recommendation:** Enforce phase gates. Do not write benchmark core code before Phase 4.

### LR-5: Paper vs. Implementation Drift Risk
**Severity:** LOW
**Description:** The proposal is the authoritative spec. Any implementation decision that conflicts with the proposal must be documented, not silently resolved. Currently no conflicts exist.
**Recommendation:** Maintain a living cross-reference table between paper sections and implementation artifacts.

---

## 7. Error and Conflict Analysis

### 7.1 Errors in Source Material
**None found.** The LaTeX proposal is well-structured, internally consistent, and compiles without errors.

### 7.2 Conflicts Between Paper and Preapproved Decisions
**None found.** The preapproved decisions (Section 2 of the execution guide) and the paper are fully aligned:
- Paper: "at least two LLM families" ↔ Preapproved: `qwen-lm/qwen2.5-coder` (provides one concrete model; paper allows additional)
- Paper: "at least three repositories" ↔ Preapproved: 4 repos (ERPNext optional) — consistent
- Paper: action classification (4 types) ↔ Preapproved: core + additional strategies — consistent

### 7.3 Identified Metric Considerations
- Paper correctly prioritizes correctness > efficiency (Section IV-C)
- Ground truth must distinguish "regenerate" from "validate only" — file diffs alone are insufficient
- No explicit treatment of "uncertain" or "don't know" in action classification — may need to be added
- Paper specifies non-inferiority testing (not just non-significant difference) for preservation claims

---

## 8. Migration Documentation

### 8.1 What to Migrate
Nothing needs migration. No legacy result files exist.

### 8.2 What to Create Next (Phase 2)
- Research protocol document (RQs, hypotheses, metrics traceability)
- Ground truth protocol
- Candidate artifact universe definition
- Scenario schema
- Primary and secondary outcome definitions
- Statistical analysis plan

### 8.3 What to Preserve
- All `inputs/` files — untouched
- All `project/` state files — updated this session
- Conda environment — do not recreate

---

## 9. Input Immutability Verification

- `inputs/paper/MSc_Proposal_Selective_Regeneration_Revised.pdf` — UNCHANGED
- `inputs/paper/MSc_Proposal_Selective_Regeneration_Revised.tex` — UNCHANGED
- No files were modified, renamed, or overwritten inside `inputs/`
- Nothing was copied from `inputs/` into `docs/`
- All analysis artifacts created under `reports/` or `docs/`

**Status:** INPUT IMMUTABILITY PRESERVED ✅
