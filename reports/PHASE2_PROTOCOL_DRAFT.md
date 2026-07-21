# Phase 2A — Research Protocol Draft

**Status:** DRAFT — NOT FROZEN
**Date:** 2026-07-22

> This document is a **draft** research protocol for the Dependency-Aware Selective Regeneration benchmark. Every section is tagged with one of:
> - **PREAPPROVED** — directly from the paper or execution guide; do not reopen unless a blocking issue arises.
> - **PROPOSED** — a reasonable default chosen by the implementer; can be adjusted without researcher approval.
> - **REQUIRES_RESEARCHER_APPROVAL** — a scientific decision that must be confirmed or overridden by the researcher before the protocol is frozen.

---

## Table of Contents

1. [Research Questions Traceability](#1-research-questions-traceability)
2. [Hypothesis Traceability](#2-hypothesis-traceability)
3. [Repository Selection Criteria](#3-repository-selection-criteria)
4. [Candidate Artifact Universe](#4-candidate-artifact-universe)
5. [Ground-Truth Construction Protocol](#5-ground-truth-construction-protocol)
6. [Annotation Protocol](#6-annotation-protocol)
7. [Scenario Taxonomy](#7-scenario-taxonomy)
8. [Baseline Definitions](#8-baseline-definitions)
9. [Primary Metrics](#9-primary-metrics)
10. [Secondary Metrics](#10-secondary-metrics)
11. [Statistical Analysis Plan](#11-statistical-analysis-plan)
12. [Randomization Policy](#12-randomization-policy)
13. [Seed Policy](#13-seed-policy)
14. [Execution Budget](#14-execution-budget)
15. [Failure Policy](#15-failure-policy)
16. [Leakage Prevention Policy](#16-leakage-prevention-policy)
17. [Threats to Validity](#17-threats-to-validity)
18. [Reproducibility Protocol](#18-reproducibility-protocol)
19. [Change-Impact Strategy Inventory](#19-change-impact-strategy-inventory)
20. [Acceptance Criteria per Hypothesis](#20-acceptance-criteria-per-hypothesis)
21. [Decision Items Requiring Researcher Approval](#21-decision-items-requiring-researcher-approval)

---

## 1. Research Questions Traceability

### 1.1 RQ1 — Impact Identification
- **Status:** PREAPPROVED (Paper §IV-A)
- **Question:** How accurately can dependency-aware approaches identify heterogeneous software artifacts affected by a natural-language requirement change?
- **Measured by:** Precision, recall, F1, false-negative rate, false-positive rate, impact-set size, action-classification accuracy
- **Addressed by:** H1
- **Evaluation phase:** Phase 1 of the evaluation protocol (impact-analysis only, no code generation)

### 1.2 RQ2 — Evolution Correctness
- **Status:** PREAPPROVED (Paper §IV-A)
- **Question:** Can selective regeneration implement changed requirements while preserving behaviour that should remain unchanged?
- **Measured by:** Changed-requirement test pass rate, regression pass rate, unintended diff size, repair iterations
- **Addressed by:** H2
- **Evaluation phase:** Phase 2 of the evaluation protocol (controlled evolution execution)

### 1.3 RQ3 — Architectural Consistency
- **Status:** PREAPPROVED (Paper §IV-A)
- **Question:** To what extent can architecture-aware selective regeneration preserve declared architectural and design constraints during evolution?
- **Measured by:** Architecture-rule pass rate, design-constraint satisfaction, boundary violations
- **Addressed by:** H3
- **Evaluation phase:** Phase 3 of the evaluation protocol (architecture and preservation evaluation)

### 1.4 RQ4 — Efficiency
- **Status:** PREAPPROVED (Paper §IV-A)
- **Question:** Under equivalent correctness conditions, how much regeneration work, token consumption, model calls, latency, and estimated cost can selective regeneration avoid relative to repository-retrieval agent workflows?
- **Measured by:** Input/output tokens, model calls, regenerated artifacts, latency, execution time, estimated cost
- **Addressed by:** H4
- **Evaluation phase:** Phase 2 + Phase 4 (efficiency reported only for equivalently correct runs)

### 1.5 RQ5 — Generality and Sensitivity
- **Status:** PREAPPROVED (Paper §IV-A)
- **Question:** How do repository architecture, project size, change type, dependency strategy, and LLM choice influence impact accuracy and selective-regeneration benefit?
- **Measured by:** Interaction effects, savings curves, per-stratum breakdowns
- **Addressed by:** H5
- **Evaluation phase:** Phase 4 (sensitivity, ablation, boundary cases)

### 1.6 RQ-to-Hypothesis Map

| RQ | Primary Hypothesis | Secondary Hypotheses | Evaluation Phase |
|----|--------------------|----------------------|------------------|
| RQ1 | H1 | — | Eval Phase 1 |
| RQ2 | H2 | — | Eval Phase 2 |
| RQ3 | H3 | — | Eval Phase 3 |
| RQ4 | H4 | H5 | Eval Phase 2 + 4 |
| RQ5 | H5 | H1, H4 | Eval Phase 4 |

---

## 2. Hypothesis Traceability

### 2.1 H1 — Hybrid Impact Superiority
- **Status:** PREAPPROVED (Paper §IV-B)
- **Statement:** A hybrid typed dependency model will achieve higher recall and lower false-negative rates than static-only, semantic-only, or retrieval-only impact analysis.
- **Primary comparison:** Hybrid graph vs. static-only, semantic-only, traceability-only, and retrieval-only impact analysis
- **Primary measures:** Recall, false-negative rate, precision, F1, action accuracy
- **Decision criterion:** Supported if the hybrid method improves recall and reduces missed affected artifacts without unacceptable over-selection (FPR increase > 0.10 deemed unacceptable per PROPOSED threshold)

### 2.2 H2 — Preservation Non-Inferiority
- **Status:** PREAPPROVED (Paper §IV-B)
- **Statement:** Selective regeneration will preserve unchanged behaviour at a rate statistically non-inferior to a repository-level agent baseline when both approaches satisfy the changed requirements.
- **Primary comparison:** Selective execution vs. repository-agent baseline on matched changes
- **Primary measures:** Changed-requirement success, regression pass rate, unintended diffs, repair iterations
- **Decision criterion:** Evaluated using non-inferiority (NI margin PROPOSED at Δ = 0.05 for regression pass rate) and paired comparisons for secondary outcomes

### 2.3 H3 — Architecture Validation Gap
- **Status:** PREAPPROVED (Paper §IV-B)
- **Statement:** Explicit architecture validation will detect violations not captured by functional tests alone.
- **Primary comparison:** Functional tests alone vs. functional plus architecture validation
- **Primary measures:** Architecture-rule violations, design-constraint satisfaction
- **Decision criterion:** Supported if explicit architecture checks reveal violations not detected by functional tests in at least one repository

### 2.4 H4 — Selective Efficiency
- **Status:** PREAPPROVED (Paper §IV-B)
- **Statement:** For localized and moderately propagating changes, selective regeneration will reduce regenerated artifacts and token consumption without reducing correctness.
- **Primary comparison:** Successful selective runs vs. equivalently correct baseline runs
- **Primary measures:** Regenerated artifacts, tokens, calls, latency, cost
- **Decision criterion:** Efficiency reported only under equivalent correctness conditions. Effect size with confidence interval reported per comparison

### 2.5 H5 — Blast Radius Boundary
- **Status:** PREAPPROVED (Paper §IV-B)
- **Statement:** Efficiency benefits will decrease as change blast radius increases and may disappear for repository-wide changes.
- **Primary comparison:** Changes grouped by blast radius and change type
- **Primary measures:** Interaction effects, savings curves
- **Decision criterion:** Supported if benefits decline as propagation broadens and approach zero for repository-wide changes

### 2.6 Hypothesis-Experiment Traceability (from paper)

| Hyp. | Experiment | Measures | Criterion |
|------|-----------|----------|-----------|
| H1 | Impact analysis comparison (no generation) | Recall, FNR, precision, F1, action accuracy | Hybrid improves recall; FPR ≤ baseline + 0.10 |
| H2 | Controlled evolution runs | Regression pass rate, unintended diffs | Non-inferior (NI margin PROPOSED Δ=0.05) |
| H3 | Functional vs. functional+architecture | Violation detection rate | Architecture reveals violations tests miss |
| H4 | Correctness-matched runs | Tokens, artifacts, calls, latency | Effect size + CI; conditional on correctness |
| H5 | Blast-radius strata | Savings curves, interaction effects | Monotonic decline; near-zero at broadest |

---

## 3. Repository Selection Criteria

### 3.1 Preapproved Repository Set
- **Status:** PREAPPROVED (Execution Guide §2)
- **Repositories:**
  1. **Small:** Controlled Django Todo application
  2. **Medium:** django CMS
  3. **Large:** Saleor Core
  4. **Stress (optional):** ERPNext

### 3.2 Selection Criteria (from paper)
- **Status:** PREAPPROVED (Paper §VI-A)
- Availability of automated tests and build instructions
- Identifiable architecture and module boundaries
- Realistic size feasible for repeated controlled runs
- Diversity of domains, architectures, and change types
- Permissive licences and reproducible historical states

### 3.3 Target Architectural Diversity
- **Status:** PROPOSED
- The four repositories should cover:
  - Layered REST application (Todo)
  - Modular CMS with plugin architecture (django CMS)
  - E-commerce with service-oriented/modular monolith structure (Saleor)
  - ERP with complex cross-module dependencies (ERPNext, if included)

### 3.4 Repository Acquisition Policy
- **Status:** PROPOSED
- Clone from official upstream at a fixed commit SHA
- Pin repository versions in a manifest file (`repos/manifest.json`)
- Do not modify upstream repositories; snapshot only
- Document licences for each repository

### 3.5 Exclusions
- **Status:** REQUIRES_RESEARCHER_APPROVAL
- If a repository lacks a test suite, is it excluded or are scenarios limited?
- If a repository licence changes before the experiment, what is the fallback?
- Time window cutoff for upstream changes (e.g., repos older than N months are preferred for stability)

---

## 4. Candidate Artifact Universe

### 4.1 Artifact Node Types
- **Status:** PREAPPROVED (Paper §V-B)
- The framework will represent the following heterogeneous artifact types:
  1. Requirements (structured change specifications)
  2. Domain entities / models
  3. Interfaces / API contracts
  4. Services / business logic modules
  5. Database objects / schemas / migrations
  6. Tests (unit, integration, functional)
  7. Documentation (inline, external, README)
  8. Configurations (settings, deployment config)
  9. Architecture decisions / ADRs
  10. Deployment artifacts (Dockerfile, CI config)

### 4.2 Granularity
- **Status:** PROPOSED
- Default granularity: **file-level** for source code, test, and config artifacts
- Finer granularity (function/class level) considered where practical for dependency analysis
- Documentation: section/block level where structure exists
- Each artifact node shall have a stable identifier (file path + optional anchor)

### 4.3 Artifact Node Attributes
- **Status:** PROPOSED
- Each node records:
  - `id`: stable identifier
  - `type`: one of the types in §4.1
  - `path`: file path or logical location
  - `content_hash`: SHA-256 of canonical content
  - `language` or `format`
  - `timestamp`: last modification time (from VCS or filesystem)

### 4.4 Edge Types
- **Status:** PREAPPROVED (Paper §V-B)
- Seven edge types:
  1. **Derivation** — artifact A was generated/specified from B
  2. **Structural** — imports, calls, inheritance, schema use, data flow
  3. **Traceability** — requirement-to-design, requirement-to-test, requirement-to-code
  4. **Semantic** — conceptual dependency from text or model analysis
  5. **Validation** — test T validates artifact A or requirement R
  6. **Architectural** — component constrained by ADR or boundary
  7. **Provenance** — artifact produced from spec version X or prompt Y

### 4.5 Edge Attributes
- **Status:** PROPOSED
- Each edge records:
  - `source_id`, `target_id`
  - `type`: edge type from §4.4
  - `weight` or `confidence` (optional, default 1.0)
  - `source`: how the edge was derived (static analysis, annotation, LLM)
  - `bidirectional`: flag for symmetric relations

### 4.6 Universe Boundary
- **Status:** PROPOSED
- The candidate artifact universe for each repository consists of all tracked source files plus selected non-source artifacts (README, CI config, migration files, etc.)
- Excluded by default: vendored dependencies, generated files, binary assets, `.git` internals
- Exclusion list must be documented per repository

---

## 5. Ground-Truth Construction Protocol

### 5.1 Ground-Truth Dimensions
- **Status:** PREAPPROVED (Paper §VI-C)
- Ground truth must distinguish:
  - **Regenerate** — artifact content must change
  - **Preserve** — artifact must remain unchanged
  - **Validate only** — artifact unchanged but must be re-validated
  - **Human review** — insufficient confidence for automated decision

### 5.2 Ground-Truth Sources
- **Status:** PROPOSED
- Ground truth will be constructed from:
  1. **Repository history** — actual changes in analogous past commits
  2. **Static analysis** — dependency graphs, call graphs, data-flow analysis
  3. **Test coverage** — which tests exercise which artifacts
  4. **Architecture documentation** — ADRs, module boundaries
  5. **Independent expert annotation** — at least two annotators per scenario

### 5.3 Annotation Process
- **Status:** PREAPPROVED (Paper §VI-C)
- At least two annotators label the expected action for each candidate artifact
- Agreement reported (Cohen's kappa or similar)
- Disagreements resolved through documented adjudication

### 5.4 Ground-Truth Format
- **Status:** PROPOSED
- Each ground-truth record:
  ```yaml
  scenario_id: STR
  artifact_id: STR
  artifact_type: STR
  expected_action: regenerate | preserve | validate_only | human_review
  justification: STR
  annotator_id: STR
  confidence: 1-5
  adjudicated: bool
  final_action: STR (after adjudication if needed)
  ```

### 5.5 Quality Thresholds
- **Status:** REQUIRES_RESEARCHER_APPROVAL
- Minimum inter-annotator agreement (kappa ≥ 0.70 PROPOSED)
- Minimum number of scenarios per repository (8 PREAPPROVED)
- When is an artifact excluded from ground truth (e.g., unanimous "unknown")?
- How to handle artifacts where annotators disagree on regenerate vs. validate only

### 5.6 Ground-Truth Publication
- **Status:** PROPOSED
- Ground-truth annotations will be included in the replication package
- Annotator identities may be anonymized
- Adjudication records will be included

---

## 6. Annotation Protocol

### 6.1 Annotator Qualifications
- **Status:** REQUIRES_RESEARCHER_APPROVAL
- Minimum expertise level required
- Whether annotators may be authors of the study
- Training materials and pilot annotation round

### 6.2 Annotation Materials
- **Status:** PROPOSED
- Each annotator receives:
  - Repository snapshot (commit SHA)
  - Requirement change description (before/after)
  - Acceptance criteria
  - List of candidate artifacts with types
  - Annotation guidelines (what each action means)
  - Example annotations from a pilot scenario (not in main study)

### 6.3 Annotation Independence
- **Status:** PROPOSED
- Annotators work independently without discussion
- Annotations submitted through a structured form (CSV or YAML template)
- No access to each other's annotations until adjudication

### 6.4 Adjudication Process
- **Status:** PROPOSED
- Disagreements resolved by a third reviewer or discussion between original annotators
- Adjudication recorded with rationale
- If agreement cannot be reached after two rounds, artifact marked as `human_review` default

### 6.5 Pilot Annotation
- **Status:** PROPOSED
- One pilot scenario per repository used for annotator training
- Pilot results not included in final ground truth
- Annotator feedback used to refine guidelines

### 6.6 Annotation Tooling
- **Status:** PROPOSED
- Simple structured format (YAML/CSV) usable with any text editor or spreadsheet
- No custom annotation platform required
- Scripts provided to validate annotation format and compute agreement

---

## 7. Scenario Taxonomy

### 7.1 Preapproved Distribution
- **Status:** PREAPPROVED (Execution Guide §2)
- Per repository: 8 scenarios = 3 localized, 3 moderate, 2 cross-cutting

### 7.2 Change Types (from paper)
- **Status:** PREAPPROVED (Paper §VI-B)
- Schema and field changes
- API additions or modifications
- Validation and business-rule changes
- Permissions and authorization changes
- Cross-entity relationships
- Workflow changes
- Architecture-sensitive changes
- Selected broad changes to test the limits of selectivity

### 7.3 Blast Radius Classification
- **Status:** PROPOSED

| Category | Definition | Expected artifacts affected | Count per repo |
|----------|-----------|---------------------------|----------------|
| Localized | Single module, few files | 1-5 | 3 |
| Moderate | Crosses module boundaries but contained | 5-15 | 3 |
| Cross-cutting | Spans multiple layers/modules | 15+ | 2 |

### 7.4 Scenario Schema
- **Status:** PROPOSED
- Each scenario defines:
  ```yaml
  scenario_id: STR (e.g., "todo-local-001")
  repository: STR
  change_type: STR (from §7.2)
  blast_radius: localized | moderate | cross_cutting
  requirement_before: STR
  requirement_after: STR
  rationale: STR
  acceptance_criteria: [STR]
  expected_affected_artifacts: [artifact_id]
  expected_actions: {artifact_id: action}
  regression_obligations: [test_id or artifact_id]
  architecture_constraints: [STR]
  ```

### 7.5 Scenario Naming Convention
- **Status:** PROPOSED
  ```
  {repo}-{blast}-{NN}
  ```
  Where `repo` = todo | djangocms | saleor | erpnext, `blast` = loc | mod | cross, `NN` = sequential 01-08

### 7.6 Scenario Exclusion Rules
- **Status:** REQUIRES_RESEARCHER_APPROVAL
- Scenarios that cannot be implemented because repository lacks the relevant feature
- Scenarios where requirement change is ambiguous or contradictory
- Policy for replacing excluded scenarios

---

## 8. Baseline Definitions

### 8.1 Repository-Agent Baseline
- **Status:** PREAPPROVED (Paper §VI-D)
- **Name:** `repository_agent`
- **Description:** Retrieves and updates repository context using an agentic workflow without an external typed impact controller
- **Implementation notes:** Will be implemented as a retrieval-augmented generation pipeline that receives the full repository context (or relevant subset via embedding retrieval) and generates patches without dependency-graph scoping
- **Model:** PREAPPROVED as qwen-lm/qwen2.5-coder (on Kaggle)

### 8.2 Full Regeneration / Reference Baseline
- **Status:** PREAPPROVED (Paper §VI-D)
- **Name:** `full_regeneration`
- **Description:** Regenerates or broadly reconstructs the relevant application slice
- **Usage:** Used where computationally feasible; may be limited for large repositories
- **Status:** PARTIALLY PROPOSED — exact scope needs definition

### 8.3 Static-Only Impact Analysis
- **Status:** PREAPPROVED (Execution Guide §2)
- **Name:** `static_only`
- **Description:** Structural dependencies without semantic or traceability signals
- **Scope:** Imports, inheritance, function calls, schema references

### 8.4 Semantic/Retrieval-Only Impact Analysis
- **Status:** PREAPPROVED (Execution Guide §2)
- **Name:** `semantic_only`
- **Description:** Embedding or LLM relevance without static graph propagation
- **Scope:** Dense retrieval over source code + documentation

### 8.5 Traceability-Only Impact Analysis
- **Status:** PREAPPROVED (Execution Guide §2)
- **Name:** `traceability_only` (additional impact strategy)
- **Description:** Explicit requirement-artifact links only
- **Scope:** Where trace links exist from requirements to design/code/tests

### 8.6 Hybrid Selective Regeneration
- **Status:** PREAPPROVED (Execution Guide §2)
- **Name:** `hybrid_selective`
- **Description:** Combines typed dependency signals and action classification
- **This is the proposed method being evaluated**

### 8.7 Full Context Baseline (Conditional)
- **Status:** PREAPPROVED (Execution Guide §2)
- **Name:** `full_context`
- **Description:** Full repository context provided as input
- **Usage:** Only when feasible (repository size permits)
- **Status:** PROPOSED — trigger condition: total repository LOC < 50,000

### 8.8 Ablation Variants
- **Status:** PROPOSED
- Ablation removes individual components from the hybrid method:
  - `hybrid_minus_semantic` — no semantic edges
  - `hybrid_minus_traceability` — no traceability edges
  - `hybrid_minus_validation` — no validation edges
  - `hybrid_minus_architectural` — no architectural edges
- These are secondary baselines for ablation analysis (H5)

---

## 9. Primary Metrics

### 9.1 Impact Correctness (RQ1, H1)
- **Status:** PREAPPROVED (Paper §VI-F, Table III)
- Precision: TP / (TP + FP)
- Recall: TP / (TP + FN)
- F1: 2 * P * R / (P + R)
- False-negative rate: FN / (TP + FN)
- False-positive rate: FP / (FP + TN)
- Impact-set size: |predicted_impacted|
- Action-classification accuracy: correct_action / total_actions

### 9.2 Functional Correctness (RQ2, H2)
- **Status:** PREAPPROVED (Paper §VI-F, Table III)
- Build success: binary (pass/fail)
- Changed-requirement test pass rate: passed / total_req_tests
- Task success: binary (all acceptance criteria met)
- First-pass acceptance: binary (no repair iterations needed)
- Repair iterations: count

### 9.3 Preservation (RQ2, H2)
- **Status:** PREAPPROVED (Paper §VI-F, Table III)
- Regression pass rate: regressed_tests / total_regression_tests (inverted)
- Unintended diff size: lines added/deleted outside expected impact set
- Unchanged-test failures: count of tests that passed before but fail after
- Behavioural equivalence: where applicable (e.g., output comparison)

### 9.4 Architecture (RQ3, H3)
- **Status:** PREAPPROVED (Paper §VI-F, Table III)
- Architecture-rule pass rate: passed_rules / total_rules
- Design-constraint satisfaction: satisfied / total_constraints
- Boundary violations: count of cross-boundary accesses

### 9.5 Efficiency (RQ4, H4)
- **Status:** PREAPPROVED (Paper §VI-F, Table III)
- Input tokens: total
- Output tokens: total
- Model calls: count
- Regenerated artifacts: count
- Latency: wall-clock time (seconds)
- Execution time: total pipeline time (seconds)
- Estimated monetary cost: USD (based on model API pricing or compute)

### 9.6 Explainability (Supplementary)
- **Status:** PREAPPROVED (Paper §VI-F, Table III)
- Supported-edge ratio: impacted_artifacts_with_supporting_edges / total_impacted
- Rationale completeness: PROPOSED — qualitative scale (none, partial, full)
- Reviewer agreement: PROPOSED — kappa on action-justification pairs
- Unsupported-selection rate: PROPOSED — selected_without_edge / total_selected

---

## 10. Secondary Metrics

### 10.1 Cost-Efficiency Ratios
- **Status:** PROPOSED
- Tokens per correct artifact: total_tokens / correctly_impacted_artifacts
- Calls per correct run: model_calls / successful_runs
- Efficiency score: (regeneration_work_avoided) / (total_regeneration_work_in_baseline)

### 10.2 Process Metrics
- **Status:** PROPOSED
- Pipeline stage timing: breakdown of wall-clock by stage (retrieval, impact analysis, generation, validation)
- Graph construction time: seconds
- Prompt size per strategy: average tokens
- Repair success rate: repairs / repair_attempts

### 10.3 Sensitivity Metrics
- **Status:** PROPOSED
- Per-strategy variance across repositories: coefficient of variation for each primary metric
- Per-change-type breakdown: same metrics by scenario taxonomy
- Per-model comparison: when multiple LLMs are used

### 10.4 Agreement Metrics
- **Status:** PROPOSED
- Annotator agreement: Cohen's kappa (and/or Krippendorff's alpha for 3+ annotators)
- Annotator confidence distribution
- Adjudication rate: disagreed_artifacts / total_artifacts

### 10.5 Leakage Detection Metrics
- **Status:** PROPOSED
- Ground-truth contamination check: are any evaluation artifacts visible in training/prompt data?
- Information leakage: does the method use any signal that trivially reveals ground-truth labels?
- These are not numeric metrics but binary audit checks to be run before analysis

---

## 11. Statistical Analysis Plan

### 11.1 Comparison Structure
- **Status:** PREAPPROVED (Paper §VI-G)
- Paired comparisons: each method processes the same repository state and change
- Per-change-type stratification
- Per-repository reporting
- Per-model reporting (when multiple models)
- Failed runs retained and analysed (not discarded)

### 11.2 Primary Analysis
- **Status:** PROPOSED

| Hypothesis | Test | Details |
|-----------|------|---------|
| H1 (recall) | Paired bootstrap CI | Compare recall distributions across strategies; report median difference with 95% CI |
| H1 (FNR) | Paired bootstrap CI | As above for false-negative rate |
| H2 (preservation) | Non-inferiority test | One-sided test with NI margin Δ = 0.05; report p-value and CI for regression pass rate difference |
| H3 (architecture) | Descriptive + McNemar | Compare violation detection rates; McNemar's test for paired binary outcomes |
| H4 (efficiency) | Paired bootstrap / Wilcoxon | Effect size (Cliff's delta or Cohen's d) with 95% CI; conditional on equivalent correctness |
| H5 (sensitivity) | Mixed-effects model | regression medel: efficiency ~ blast_radius * strategy + (1|repository) + (1|scenario) |

### 11.3 Non-Inferiority Margin
- **Status:** REQUIRES_RESEARCHER_APPROVAL
- PROPOSED: Δ = 0.05 (5 percentage points) for regression pass rate
- Rationale: A 5% regression rate increase is detectable and practically meaningful
- Alternative: Δ = 0.03 (stricter) or Δ = 0.10 (more lenient)

### 11.4 Multiple-Comparison Correction
- **Status:** PROPOSED
- Primary hypotheses (H1-H5): no correction (each tests a distinct claim with its own measure)
- Secondary/exploratory comparisons: Bonferroni-Holm or Benjamini-Hochberg within each family
- Explicit report of which corrections were applied

### 11.5 Effect Size Reporting
- **Status:** PROPOSED
- Report effect sizes with confidence intervals for all primary comparisons
- Cohen's d for normally distributed outcomes
- Cliff's delta for non-parametric comparisons
- Interpretation thresholds documented

### 11.6 Power Analysis (Pre-Study)
- **Status:** PROPOSED
- Minimum detectable effect size given 8 scenarios × 3+ strategies × 2+ repositories = 48+ paired observations
- Post-hoc power estimation may be reported but not used as exclusion criterion

### 11.7 Outlier and Excluded-Data Policy
- **Status:** PROPOSED
- All runs reported in raw form; exclusions documented with rationale
- Exclusion criteria: infrastructure failure (not model error), human error in scenario definition
- Sensitivity analysis with and without excluded points

### 11.8 Reporting Format
- **Status:** PROPOSED
- Per-change results in table (each row = one scenario × one strategy)
- Per-repository summary statistics
- Aggregate results with forest plots or similar
- Failed runs reported separately with reasons

---

## 12. Randomization Policy

### 12.1 Scenario Order
- **Status:** PROPOSED
- Scenarios within a repository are executed in a fixed order (sequential evolution)
- The order is the same across all compared strategies within one repository
- Order is determined once and documented

### 12.2 Strategy Execution Order
- **Status:** PROPOSED
- Within each scenario, strategies execute in randomized order to control for order effects
- Randomization seed documented per scenario-strategy pair

### 12.3 Repository Order
- **Status:** PROPOSED
- Repositories executed in order of increasing size (Todo → django CMS → Saleor)
- This is not randomized (size is a controlled variable, not a confound)

### 12.4 Model Calls (Multiple Runs)
- **Status:** PROPOSED
- For stochastic models: minimum 3 runs per (scenario × strategy) cell
- If variance is high (coefficient of variation > 0.30), increase to 5 runs
- Budget permitting (see §14)

---

## 13. Seed Policy

### 13.1 Random Seed Recording
- **Status:** PROPOSED
- Every stochastic operation records its random seed
- Seeds recorded in run provenance metadata

### 13.2 Fixed Seeds for Deterministic Components
- **Status:** PROPOSED
- Static analysis: not applicable (deterministic)
- Embedding/retrieval: set random seed if model supports it; record if not
- LLM generation: use model's default seeding mechanism; record if configurable

### 13.3 Seed Inventory
- **Status:** PROPOSED
- Python random seed
- NumPy random seed
- LLM temperature and top_p
- LLM seed parameter (if supported by model API)
- Data-shuffling seeds

### 13.4 Reproducibility Verification
- **Status:** PROPOSED
- Before the main experiment, verify that re-running with the same seed(s) produces identical deterministic results for the mock backend
- For the real model, same-seed runs should produce identical outputs when temperature=0

---

## 14. Execution Budget

### 14.1 Scenario Count
- **Status:** PREAPPROVED (Execution Guide §2)
- 8 scenarios per repository × 3 primary repositories = 24 scenarios minimum
- 8 × 4 = 32 if ERPNext is included

### 14.2 Strategy Count (Impact Analysis Only)
- **Status:** PROPOSED
- Strategies for impact analysis evaluation (no generation): 6
  - repository_agent (as retrieval-based impact predictor)
  - static_only
  - semantic_only
  - traceability_only
  - hybrid_selective
  - full_context (conditional)
- Total impact-analysis runs: 24 scenarios × 6 strategies = 144 runs

### 14.3 Strategy Count (Full Evolution)
- **Status:** PROPOSED
- Full evolution strategies: 4 (repository_agent baseline, hybrid_selective, static_only, semantic_only)
- Traceability-only folded into ablation analysis if resources permit
- Total full-evolution runs: 24 scenarios × 4 strategies × 3 seeds = 288 runs

### 14.4 LLM Call Budget (Estimated)
- **Status:** REQUIRES_RESEARCHER_APPROVAL
- Estimated token budget per run (PROPOSED): 10K-50K input, 2K-10K output
- Estimated total: 288 runs × ~30K tokens = ~8.6M tokens
- This is a rough estimate; actuals depend on repository size and scenario complexity
- The researcher must confirm if the Kaggle budget (free GPU hours) and Qwen model limits are sufficient

### 14.5 Budget Contingency
- **Status:** PROPOSED
- If budget exhausted mid-study, freeze the completed portion as a partial result
- Prioritize completion of smaller repositories over larger ones
- Prioritize impact-analysis evaluation (no generation) over full evolution if partial

---

## 15. Failure Policy

### 15.1 Run Failure Classification
- **Status:** PROPOSED

| Failure Type | Definition | Handling |
|-------------|-----------|----------|
| Infrastructure | System crash, OOM, network timeout | Retry (up to 3x); if persistent, report and exclude |
| Model error | Model returns empty/truncated/nonsensical output | Retry (up to 2x) with same prompt; if persistent, record as model failure |
| Build failure | Generated code does not compile/build | Record as failed run; attempt repair (up to 2x) |
| Test failure | Changed-requirement tests fail | Record as failed run; attempt repair (up to 3x) |
| Timeout | Run exceeds time budget (PROPOSED: 30 min per scenario) | Terminate; record as timeout failure |

### 15.2 Repair Policy
- **Status:** PROPOSED
- Repair attempts use the same strategy's generation (LLM receives failing test output)
- Maximum repair iterations: 3 per scenario
- Repair success rate reported as secondary metric
- If repair fails, the run is marked as failed and included in analysis

### 15.3 Partial Completion
- **Status:** PROPOSED
- If a strategy fails on some scenarios but not others, all results are reported
- No imputation of missing values for failed runs
- Per-scenario sample sizes reported alongside aggregate statistics

### 15.4 Strategy Exclusion
- **Status:** PROPOSED
- If a strategy fails completely on a repository (all scenarios fail), it is reported but marked as excluded from that repository's aggregate
- The exclusion is documented in the analysis

### 15.5 Run Cancellation
- **Status:** PROPOSED
- A run may be manually cancelled if it exceeds 2× the expected runtime
- Cancellation reason documented in run log

---

## 16. Leakage Prevention Policy

### 16.1 Ground-Truth Isolation
- **Status:** PROPOSED
- Ground-truth annotations stored separately from evaluation pipeline code
- Evaluation code does not have access to ground-truth labels during execution
- Ground-truth files loaded only during the comparison/analysis stage

### 16.2 Hidden Test Split
- **Status:** PROPOSED
- At minimum: a held-out set of scenarios for final validation (PROPOSED: 2 of 8 per repository)
- Alternatively: cross-validation across scenarios
- The held-out set is not used for any tuning or threshold selection

### 16.3 Static Snapshot Isolation
- **Status:** PROPOSED
- Each repository snapshot is pinned by commit SHA before any analysis
- No dynamic repository alteration during impact analysis
- All strategies see the same repository state

### 16.4 Annotation Non-Contamination
- **Status:** PROPOSED
- Annotators do not have access to strategy outputs during annotation
- Strategy outputs are generated after ground-truth is finalized
- Annotators are blinded to which strategy produced which result (where feasible)

### 16.5 Cache Exclusion
- **Status:** PROPOSED
- No caching of ground-truth answers in the execution pipeline
- Random seeds recorded to detect accidental determinism that could reveal patterns

### 16.6 Data Flow Verification
- **Status:** PROPOSED
- Before analysis, audit the data pipeline to confirm:
  - No ground-truth file is imported or loaded by any strategy module
  - No strategy module reads annotation files
  - Evaluation scripts load annotations only for scoring, not for execution control
- This audit is documented

### 16.7 Pre-Registration of Analyses
- **Status:** PROPOSED
- Primary analyses (hypothesis tests, metrics) specified before seeing results
- Exploratory analyses clearly labelled as post-hoc
- Analysis plan registered (in this document or an appendix) before experiment execution

### 16.8 Post-Hoc Analysis Policy
- **Status:** PROPOSED
- Any analysis not pre-registered is labelled as "exploratory"
- Exploratory findings are reported with asterisks and clear disclaimers
- No multiple-comparison correction applied to exploratory analyses (reported raw)

---

## 17. Threats to Validity

### 17.1 Construct Validity
- **Status:** PREAPPROVED (Paper §VIII-A)
- Token count alone does not represent software-evolution quality
- Covered by including impact accuracy, regression, architecture compliance, and explainability
- Artifact impact cannot be inferred solely from files changed in a human patch
- Addressed by: ground truth distinguishes editing from validation obligations
- **PROPOSED addition:** Metric validation — verify that selected metrics correlate with expert judgement on a pilot subset

### 17.2 Internal Validity
- **Status:** PREAPPROVED (Paper §VIII-B)
- Confounds: prompt differences, model differences, tool access, repair policies
- Addressed by: matched settings, predefined stopping conditions, multiple runs, separated graph construction from test outcomes
- **PROPOSED addition:** Verify that impact-analysis accuracy is not confounded by retrieval quality (measure retrieval recall separately)
- **PROPOSED addition:** Record all model parameters per run

### 17.3 External Validity
- **Status:** PREAPPROVED (Paper §VIII-C)
- Small number of repositories cannot represent all software
- Addressed by: architectural and domain diversity, inclusion of broad changes, conclusions bounded to evaluated settings
- **PROPOSED addition:** Report repository characteristics (LOC, module count, test count, dependency graph density) to aid generalizability assessment

### 17.4 Conclusion Validity
- **Status:** PREAPPROVED (Paper §VIII-D)
- Single-run estimates may be misleading
- Addressed by: per-change results, confidence intervals, effect sizes, paired analyses, failed runs retained
- **PROPOSED addition:** Power analysis before main experiment; sensitivity analysis for outlier scenarios

### 17.5 Additional Threats (PROPOSED)

| Threat | Mitigation |
|--------|-----------|
| **Annotation bias** — annotators familiar with the research hypothesis may bias labels | Blinding annotators to study hypotheses where feasible; using external annotators if budget allows |
| **Model obsolescence** — results may not generalize to newer LLMs | Document model version; replicate with a second model if budget allows |
| **Repository selection bias** — chosen repos may favour one strategy | Document all selection criteria; report negative results even if unfavourable |
| **Tooling bugs** — implementation errors in impact analysis or metrics | Unit tests for all analysis components; manual verification on a pilot scenario |
| **LLM prompt sensitivity** — small prompt changes affect results | Version-controlled prompts; same prompts used across all comparable strategies; prompt templates public in replication package |

---

## 18. Reproducibility Protocol

### 18.1 Replication Package Contents
- **Status:** PREAPPROVED (Paper §VI-H)
- Repository snapshots or reproducible commit references
- Requirement changes (structured specifications)
- Ground-truth annotations
- Prompts (version-controlled)
- Dependency extraction scripts
- Graph data
- Model settings (temperature, top_p, max_tokens, seed)
- Raw logs
- Analysis notebooks
- Environment instructions

### 18.2 Additional Package Contents (PROPOSED)
- **Status:** PROPOSED
- Docker/Kaggle environment specification
- Run scripts with fixed seeds
- Pre/post processing scripts
- Output manifests
- README with step-by-step reproduction instructions
- Licence file for replication package

### 18.3 Version Control
- **Status:** PROPOSED
- All code, prompts, and configuration files under version control (Git)
- Each experiment run tagged with unique run ID
- Run provenance recorded in structured metadata (JSON/YAML)

### 18.4 Platform Documentation
- **Status:** PROPOSED
- Kaggle environment: GPU type, CUDA version, Python version, package versions
- Local environment: same (as in Phase 0 report)
- All dependencies version-pinned

### 18.5 Output Archiving
- **Status:** PROPOSED
- Raw model outputs preserved (not just aggregate metrics)
- Proprietary-model outputs archived where licensing permits
- Output filenames include run ID and timestamp

### 18.6 Data Availability
- **Status:** REQUIRES_RESEARCHER_APPROVAL
- Where will the replication package be hosted? (PROPOSED: Zenodo + GitHub)
- What licence for the replication package? (PROPOSED: CC-BY 4.0)
- Can model outputs from commercial APIs be redistributed? (Researcher to confirm)

---

## 19. Change-Impact Strategy Inventory

### 19.1 Full Strategy Table

| ID | Name | Description | Status | Category |
|----|------|-------------|--------|----------|
| S01 | `repository_agent` | Full agentic workflow with retrieval, planning, execution, testing | PREAPPROVED | Baseline |
| S02 | `full_regeneration` | Broadly regenerates relevant application slice | PREAPPROVED | Reference |
| S03 | `static_only` | Structural dependencies only | PREAPPROVED | Ablation |
| S04 | `semantic_only` | Embedding/LLM relevance only | PREAPPROVED | Ablation |
| S05 | `traceability_only` | Explicit requirement-artifact links only | PREAPPROVED | Ablation |
| S06 | `hybrid_selective` | Combined typed dependency + action classification | PREAPPROVED | Proposed |
| S07 | `full_context` | Full repository context (when feasible) | PREAPPROVED | Reference |
| S08 | `hybrid_minus_semantic` | Hybrid without semantic edges | PROPOSED | Ablation |
| S09 | `hybrid_minus_traceability` | Hybrid without traceability edges | PROPOSED | Ablation |
| S10 | `hybrid_minus_architectural` | Hybrid without architectural edges | PROPOSED | Ablation |

### 19.2 Strategy Application Phases

| Phase | Strategies Used | Generation? |
|-------|----------------|-------------|
| Eval Phase 1 (Impact Analysis) | S03, S04, S05, S06, S01 (as impact predictor), S07 (if feasible) | No |
| Eval Phase 2 (Evolution) | S01, S06, S03, S04 | Yes |
| Eval Phase 3 (Architecture) | S01, S06, S03 + architecture validation | Yes |
| Eval Phase 4 (Sensitivity) | All feasible + S08, S09, S10 | Yes (subset) |

---

## 20. Acceptance Criteria per Hypothesis

### 20.1 H1 — Hybrid Impact Superiority
- **Status:** PROPOSED (except recall priority which is PREAPPROVED)
- **Primary:** Hybrid recall ≥ max(static_recall, semantic_recall, traceability_recall)
- **Primary:** Hybrid FNR ≤ min(static_FNR, semantic_FNR, traceability_FNR)
- **Secondary:** Hybrid precision not degraded by more than 0.10 vs. best non-hybrid
- **Stopping criterion for non-support:** If hybrid underperforms on recall vs. static-only in 2+ repositories, H1 is not supported

### 20.2 H2 — Preservation Non-Inferiority
- **Status:** PROPOSED (non-inferiority margin REQUIRES_RESEARCHER_APPROVAL)
- **Primary:** Regression pass rate of selective is non-inferior to baseline (NI margin Δ PROPOSED = 0.05, one-sided CI)
- **Secondary:** Unintended diff size (selective ≤ baseline)
- **Stopping criterion for non-support:** If lower bound of CI for regression pass rate difference < -Δ, H2 is not supported

### 20.3 H3 — Architecture Validation Gap
- **Status:** PROPOSED
- **Primary:** Architecture validation detects ≥ 1 violation not detected by functional tests in at least one repository
- **Secondary:** Fraction of total violations detected only by architecture checks
- **Stopping criterion for non-support:** If zero additional violations detected across all repositories, H3 is not supported

### 20.4 H4 — Selective Efficiency
- **Status:** PROPOSED
- **Primary:** For localized + moderate changes, regenerated artifacts (selective) < regenerated artifacts (baseline) with effect size CI excluding zero
- **Secondary:** Token consumption and model calls lower for selective vs. baseline
- **Constraint:** Efficiency compared only for runs where both selective and baseline satisfy correctness criteria
- **Stopping criterion for non-support:** If effect size CI includes zero for both regenerated artifacts and tokens, H4 is not supported for that change type

### 20.5 H5 — Blast Radius Boundary
- **Status:** PROPOSED
- **Primary:** Significant interaction (blast_radius × strategy) in mixed-effects model
- **Secondary:** Savings ratio monotonically decreases from localized to cross-cutting
- **Stopping criterion for non-support:** If savings ratio at cross-cutting is not significantly lower than at localized (or positive), H5 is not supported

---

## 21. Decision Items Requiring Researcher Approval

The following items in this draft are marked `REQUIRES_RESEARCHER_APPROVAL`. They must be confirmed or overridden before the protocol is frozen.

| ID | Section | Item | PROPOSED Default | Alternatives |
|----|---------|------|------------------|--------------|
| DA-01 | §3.5 | Repository exclusion policy for missing test suites | Exclude repo; document reason | Limit scenarios to testable subset |
| DA-02 | §3.5 | Fallback if repo licence changes | Document and re-evaluate | Exclude and replace |
| DA-03 | §3.5 | Upstream change cutoff | Use repos older than 6 months | Use latest stable release |
| DA-04 | §5.5 | Minimum inter-annotator agreement | κ ≥ 0.70 | κ ≥ 0.60 or κ ≥ 0.80 |
| DA-05 | §5.5 | Handling unresolved annotator disagreement | Default to `human_review` | Third annotator decides |
| DA-06 | §6.1 | Annotator qualifications | Author + one independent researcher | Two external annotators + author adjudicates |
| DA-07 | §7.6 | Scenario replacement policy | Replace with similar change type from same repo | Exclude scenario; reduce N |
| DA-08 | §11.3 | Non-inferiority margin (H2) | Δ = 0.05 | Δ = 0.03 or Δ = 0.10 |
| DA-09 | §14.4 | Execution budget and Kaggle feasibility | ~8.6M tokens estimated | Researcher confirms/revises |
| DA-10 | §18.6 | Replication package hosting | Zenodo + GitHub | GitHub only; OSF; institutional repository |
| DA-11 | §18.6 | Replication package licence | CC-BY 4.0 | MIT; CC0; institutional requirement |
| DA-12 | §18.6 | Model output redistribution | Where licensing permits | No redistribution; summaries only |
| DA-13 | §2.2 | H1 FPR threshold for "unacceptable over-selection" | FPR increase > 0.10 | 0.05 or 0.15 |
| DA-14 | §11.4 | Multiple-comparison correction for secondary analyses | Benjamini-Hochberg within families | Bonferroni; no correction |

---

> **End of Phase 2A Protocol Draft**
>
> Status: DRAFT — NOT FROZEN
>
> All scientific decisions remain subject to researcher review and approval.
> No implementation work should begin based on this draft.
> The protocol will be frozen only after researcher approval of all REQUIRES_RESEARCHER_APPROVAL items.
