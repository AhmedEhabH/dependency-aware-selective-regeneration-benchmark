# Experimental Design V2

**Date:** 2026-07-25
**Branch:** docs/research-design-v2
**Protocol Version:** 1.0 (FROZEN)
**Source Commit:** 3a16596
**Status:** DESIGN — Research Design V2 Freeze

---

## 1. Primary Scientific Comparison (RD-V2-01)

### 1.1 Confirmatory Comparison

> **Representative iterative repository-agent workflow**  
> vs  
> **Hybrid dependency-aware selective workflow**

Both arms use **matched**:
- LLM (Qwen2.5-Coder-7B-Instruct)
- Repository state (same commit, same artifact universe)
- Requirement change (same scenario)
- Generation parameters (temp=0.0, max_tokens=4096)
- Tool access (file read, grep, list)
- Attempt budget (max 3 attempts)
- Repair policy (bounded, error-context injection)
- Validation gates (functional → regression → architecture)
- Quality criteria (correctness, preservation, architecture)

### 1.2 Research Question (Refined)

> **Agent chooses scope implicitly** (via iterative LLM reasoning)  
> vs  
> **External dependency-aware impact controller governs scope explicitly** (graph + semantic + traceability signals)

This is **not** "AI vs non-AI" — both arms use the same LLM.

---

## 2. Experimental Arm Roles (RD-V2-02)

| Scientific Role | Legacy ID | Category | Experiment Membership |
|-----------------|-----------|----------|----------------------|
| `repository_agent` | `agent` (future) | **Main baseline** | A (impact), B (e2e) |
| `hybrid_selective` | `selective` | **Proposed treatment** | A (impact), B (e2e), C (ablation) |
| `single_shot_llm_scope` | `agent` (current) | Optional LLM baseline | A (impact) |
| `static_only` | `compiled_ai` | Graph ablation | A (impact), C (ablation) |
| `semantic_only` | `delta_mcp` | Semantic ablation | A (impact), C (ablation) |
| `traceability_only` | `incr_rtl` | Traceability ablation | A (impact), C (ablation) |
| `full_scope_reference` | `monolithic` | Upper-bound reference | A (impact) |
| `retrieval_planning_variant` | `code_plan` | Exploratory reference | A (impact) |

**Legacy IDs remain in code/checkpoints.** All new documents use scientific roles.

---

## 3. Experiment Structure (RD-V2-06)

### 3.1 Experiment A — Impact Accuracy

**Question:** Which scope selection method achieves highest precision/recall against ground truth?

| Candidate Conditions | Metrics |
|---------------------|---------|
| `repository_agent` (scope prediction) | Precision, Recall, F1, FNR, Impact-Set Size |
| `single_shot_llm_scope` (scope prediction) | Action-Classification Correctness |
| `hybrid_selective` | |
| `static_only` | |
| `semantic_only` | |
| `traceability_only` | |
| `full_scope_reference` | |

**Design:** All arms run `analyze_impact()` only (no regeneration). Ground truth from `ExpectedArtifact` annotations.

### 3.2 Experiment B — End-to-End Evolution

**Question:** Which workflow achieves best task success with minimal regressions under matched resources?

| Candidate Conditions | Metrics |
|---------------------|---------|
| `repository_agent` (iterative) | Task Success, Regression Failures, Architecture Violations |
| `hybrid_selective` | Unintended Changes, Unchanged Artifact Preservation |
| `static_only` | Regenerated Artifact Count, Tokens, Model Calls, Latency |
| `semantic_only` | Repair Attempts, Patch Size |

**Design:** Full pipeline — scope selection → shared regeneration executor → validation → bounded repair. All use **same executor** (see `SHARED_REGENERATION_EXECUTOR_DESIGN.md`).

### 3.3 Experiment C — Ablations and Boundaries

**Question:** How does each signal contribute? Where does the method fail?

| Analysis | Conditions |
|----------|------------|
| Remove static signal | `hybrid_selective` vs `semantic_only` + `traceability_only` |
| Remove semantic signal | `hybrid_selective` vs `static_only` + `traceability_only` |
| Remove traceability signal | `hybrid_selective` vs `static_only` + `semantic_only` |
| Localized vs cross-cutting | Stratify by `blast_radius` |
| Blast-radius interaction | Signal agreement rate × blast radius |

**Design:** Uses Experiment A predictions + Experiment B outcomes.

### 3.4 Experiment D — Optional External Transfer

**Question:** Do results generalize to an independent dataset?

| Candidate Conditions | Requirements |
|---------------------|--------------|
| All 7 local arms on external dataset | Per `EXTERNAL_DATASET_EVALUATION_POLICY.md` |

**Purpose:** Transfer/generalization testing only. **Not** direct ranking vs published scores.

---

## 4. Measurement Boundary (RD-V2-04)

### 4.1 Confirmatory End-to-End Cost Includes

- Scope selection (Experiment A)
- Context construction (retrieval for agent; graph build for selective)
- Regeneration (LLM generation per artifact)
- Repair (bounded loop with error context)
- Validation (functional, regression, architecture)

### 4.2 Required Per-Stage Accounting

| Stage | Fields |
|-------|--------|
| **Selection** | `selection_prompt_tokens`, `selection_completion_tokens`, `selection_total_tokens`, `selection_model_calls`, `selection_duration_seconds` |
| **Regeneration** | `regeneration_prompt_tokens`, `regeneration_completion_tokens`, `regeneration_total_tokens`, `regeneration_model_calls`, `regeneration_duration_seconds` |
| **Repair** | `repair_tokens`, `repair_model_calls`, `repair_duration_seconds` |
| **Validation** | `validation_duration_seconds` |
| **Totals** | `total_workflow_tokens`, `total_workflow_model_calls`, `total_workflow_duration_seconds` |

**Token efficiency claims valid only under comparable correctness and quality outcomes.**

---

## 5. Code Quality and Correctness (RD-V2-05)

### 5.1 Primary Measures

| Measure | Definition |
|---------|------------|
| Impact precision | TP / (TP + FP) on `regenerate` decisions |
| Impact recall | TP / (TP + FN) on ground-truth affected |
| False-negative rate | FN / (TP + FN) |
| Impact-set size | |{artifacts marked regenerate}| |
| Changed-requirement success | % scenarios where all acceptance criteria pass |
| Functional test pass rate | % hidden tests passing post-regeneration |
| Regression failures | Count of previously passing tests now failing |
| Architecture violations | Layer crossing, forbidden deps, cycles |
| Build result | Pass/Fail (compile, type-check) |
| Lint/static-analysis result | Pass/Fail (ruff, mypy) |
| Unintended diffs | Files changed outside predicted scope |
| Unchanged-artifact preservation | % `preserve` artifacts byte-identical |
| Repair attempts | Count per scenario |
| Patch size | Lines changed per artifact |

**Efficiency results MUST NOT be interpreted independently of correctness.**

---

## 6. Baseline and Treatment Specifications

### 6.1 `repository_agent` (Main Baseline) — Not Yet Implemented

| Property | Specification |
|----------|---------------|
| Retrieval rounds | ≤ 5 |
| Files inspected | ≤ 30 total |
| Model calls | 1 initial + ≤ 5 retrieval = ≤ 6 |
| Tools | `read_file`, `list_dir`, `grep` |
| Termination | Confident decision OR budget exhausted |
| Scope output | `ImpactPrediction` (regenerate/preserve/human_review) |

*See `REPOSITORY_AGENT_BASELINE_SPEC.md` for full spec.*

### 6.2 `hybrid_selective` (Treatment) — Implemented

| Property | Specification |
|----------|---------------|
| Graph signal | Undirected BFS from all artifacts |
| Semantic signal | Jaccard token overlap (threshold 0.5) |
| Traceability signal | Coverage map union |
| Decision rule | ≥2 signals → regenerate; 1 signal → human_review; 0 → preserve |
| LLM calls | 0 (deterministic voter) |
| Output | `ImpactPrediction` |

### 6.3 `single_shot_llm_scope` (Current `agent`) — Implemented

| Property | Specification |
|----------|---------------|
| Prompt | Full artifact list + requirement change |
| Model calls | 1 |
| Output | JSON list of paths → `ImpactPrediction` |
| Tools | None |

---

## 7. Hypothesis Mapping

| Hypothesis | Experiment | Primary Comparison | Decision Criterion |
|------------|------------|-------------------|-------------------|
| H1: Impact accuracy | A | `hybrid_selective` vs `repository_agent` / `single_shot_llm_scope` | F1 non-inferiority (Δ=0.05) + recall superiority |
| H2: Preservation quality | B | `hybrid_selective` vs `repository_agent` | Unchanged preservation ↑, unintended diffs ↓ |
| H3: Architecture preservation | B | `hybrid_selective` vs `repository_agent` | Architecture violations ↓ |
| H4: Token efficiency | B | `hybrid_selective` vs `repository_agent` | Total tokens ↓ under matched correctness |
| H5: Ablation contribution | C | Signal removal effects | Each signal contributes significantly |

---

## 8. Statistical Analysis Plan

| Analysis | Method | Correction |
|----------|--------|------------|
| H1 (F1) | Paired bootstrap CI (repo-scenario-rep matched) | BH (FDR) across scenarios |
| H2/H3 (preservation) | Paired bootstrap CI | Holm (FWER) |
| H4 (tokens) | Paired bootstrap CI (log-scale) | BH |
| H5 (ablations) | Within-subject contrast | BH |
| Non-inferiority | One-sided CI vs Δ=0.05 | — |
| Sensitivity | NI margins 0.03, 0.10 | — |

Per `STATISTICAL_ANALYSIS_PLAN.md` and `DA-08`, `DA-14`.

---

## 9. Execution Profiles (Aligned)

| Profile | Scenarios | Arms | Reps | Purpose |
|---------|-----------|------|------|---------|
| smoke | 1 | All 7 | 1 | Orchestration validation |
| pilot | 12 (4/repo) | `repository_agent`, `hybrid_selective` | 2 | Descriptive, feasibility |
| research | 24 | `repository_agent`, `hybrid_selective`, `static_only`, `semantic_only` | 3 | Publication evidence |

**Note:** `repository_agent` must be implemented before pilot/research.

---

## 10. Implementation Dependencies

| Dependency | Document | Status |
|------------|----------|--------|
| Shared regeneration executor | `SHARED_REGENERATION_EXECUTOR_DESIGN.md` | DESIGN |
| Repository agent baseline spec | `REPOSITORY_AGENT_BASELINE_SPEC.md` | DESIGN |
| Arm role/naming policy | `ARM_ROLE_AND_NAMING_POLICY.md` | FROZEN |
| External dataset policy | `EXTERNAL_DATASET_EVALUATION_POLICY.md` | FROZEN |
| Implementation impact plan | `SU0010_IMPLEMENTATION_IMPACT_PLAN.md` | DESIGN |

---

## 11. Change Log from Protocol v1.0

| Change | Rationale | Document |
|--------|-----------|----------|
| `agent` → `single_shot_llm_scope` (current) | Honest labeling; not iterative | `ARM_ROLE_AND_NAMING_POLICY.md` |
| `repository_agent` added (future) | Required for confirmatory comparison | `REPOSITORY_AGENT_BASELINE_SPEC.md` |
| `selective` → `hybrid_selective` | Descriptive; matches algorithm | `ARM_ROLE_AND_NAMING_POLICY.md` |
| Ablation arms renamed | `compiled_ai`→`static_only`, etc. | `ARM_ROLE_AND_NAMING_POLICY.md` |
| Measurement boundary formalized | Per-stage token accounting | `END_TO_END_MEASUREMENT_BOUNDARY.md` |
| Shared executor mandated | Fair comparison requirement | `SHARED_REGENERATION_EXECUTOR_DESIGN.md` |
| Literature claims restricted | RD-V2-03 compliance | `ARM_ROLE_AND_NAMING_POLICY.md` |

---

## 12. Status

| Checkpoint | Status |
|------------|--------|
| RD-V2-01 Primary comparison | DEFINED |
| RD-V2-02 Arm roles | FROZEN |
| RD-V2-03 Literature claims | FROZEN |
| RD-V2-04 Measurement boundary | DOCUMENTED |
| RD-V2-05 Quality/correctness | DOCUMENTED |
| RD-V2-06 Experiment structure | DOCUMENTED |
| Baseline spec | DESIGN |
| Shared executor design | DESIGN |
| Naming policy | FROZEN |
| External dataset policy | FROZEN |
| Implementation plan | DESIGN |

**Research Design V2 is ready for researcher review.**
**No silent protocol edits authorized.** Formal amendment process may be required before publication.