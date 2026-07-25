# Research Design V2 Decision Report

**Date:** 2026-07-25
**Branch:** docs/research-design-v2
**Protocol Version:** 1.0 (FROZEN)
**Source Commit:** 3a16596 (main, post audit merge)
**Status:** DECISION RECORD — Researcher Review Required

---

## 1. Executive Summary

This report records the **Research Design V2 (RD-V2)** decisions that restructure the experimental framework before implementation (SU-0010). The decisions address critical mismatches identified in the Arm-to-Protocol Execution Audit (`reports/ARM_TO_PROTOCOL_EXECUTION_AUDIT.md`) and establish a scientifically valid comparison framework.

**Key outcome:** The confirmatory comparison is redefined from "Agent vs Selective" to **Repository Agent (iterative) vs Hybrid Selective (explicit governance)**, with honest labeling of current implementations.

---

## 2. Decisions Recorded

### RD-V2-01: Primary Scientific Comparison
**Decision:** The confirmatory comparison is:
```
Representative iterative repository-agent workflow
vs
Hybrid dependency-aware selective workflow
```
**Both must use matched:**
- LLM, repository state, requirement change, generation parameters
- Tool access, attempt budget, repair policy, validation gates, quality criteria

**Research question (not AI vs non-AI):**
> *Agent chooses scope implicitly vs External dependency-aware impact controller governs scope explicitly*

**Status:** FROZEN — defines the scientific target for SU-0010/SU-0011.

---

### RD-V2-02: Experimental Arm Roles
**Decision:** Approved scientific roles and display names:

| Role | Display Name | Legacy ID | Status |
|------|-------------|-----------|--------|
| `repository_agent` | Repository Agent | `agent` (future) | **Not implemented** (SU-0011) |
| `hybrid_selective` | Hybrid Selective | `selective` | Implemented (deterministic voter) |
| `single_shot_llm_scope` | Single-Shot LLM Scope | `agent` (current) | Implemented |
| `static_only` | Static-Only Ablation | `compiled_ai` | Implemented |
| `semantic_only` | Semantic-Only Ablation | `delta_mcp` | Implemented |
| `traceability_only` | Traceability-Only Ablation | `incr_rtl` | Implemented |
| `full_scope_reference` | Full-Scope Reference | `monolithic` | Implemented |
| `retrieval_planning_variant` | Retrieval-Planning Variant | `code_plan` | Implemented |

**Legacy IDs remain in code/checkpoints.** New documents use scientific roles.
**Status:** FROZEN.

---

### RD-V2-03: Literature Claims
**Decision:** Literature-named methods (Compiled AI, DeltaMCP, IncreRTL, CodePlan, RepoCoder, OpenCode, Claude Code) are **name-only references** for:
- Related Work
- Novelty positioning
- Design inspiration
- Qualitative comparison
- External validity discussion

**They are NOT controlled competitors unless faithfully reproduced.**
Published metrics from incompatible environments: **contextual cross-study evidence only**.
**Prohibited:** head-to-head ranking, statistical superiority claims, effect-size comparison, replacement for executable baseline.
**Status:** FROZEN.

---

### RD-V2-04: Measurement Boundary
**Decision:** Confirmatory end-to-end cost includes:
```
Scope selection → Context construction → Regeneration → Repair → Validation
```

**Required per-stage accounting (all arms):**

| Stage | Fields |
|-------|--------|
| Selection | prompt/completion/total tokens, model calls, duration |
| Regeneration | prompt/completion/total tokens, model calls, duration |
| Repair | prompt/completion/total tokens, model calls, duration |
| Validation | duration only |
| **Totals** | workflow tokens, model calls, duration |

**Efficiency claims valid only under matched correctness/quality.**
**Status:** FROZEN — `END_TO_END_MEASUREMENT_BOUNDARY.md`.

---

### RD-V2-05: Code Quality and Correctness
**Decision:** Primary correctness/preservation measures:
- Impact precision, recall, false-negative rate, impact-set size
- Changed-requirement success, functional test pass rate
- Regression failures, architecture violations, build result
- Lint/static-analysis result, unintended diffs
- Unchanged-artifact preservation, repair attempts, patch size

**Efficiency results must not be interpreted independently of correctness.**
**Status:** FROZEN.

---

### RD-V2-06: Experiment Structure
**Decision:** Four experiments defined:

| Experiment | Purpose | Arms |
|------------|---------|------|
| **A — Impact Accuracy** | Precision/recall/F1/FNR/size | All 7 (impact only) |
| **B — End-to-End Evolution** | Task success, regression, tokens, latency | `repository_agent`, `hybrid_selective`, `static_only`, `semantic_only` |
| **C — Ablations/Boundaries** | Signal removal, blast-radius interaction | `hybrid_selective` variants |
| **D — External Transfer** | Generalization (one dataset max) | All local arms on external data |

**Status:** FROZEN — `EXPERIMENTAL_DESIGN_V2.md`.

---

## 3. Audit Findings Driving Decisions

### 3.1 Measurement Boundary (Confirmed)
- **Benchmark measures IMPACT ANALYSIS ONLY** — no regeneration executed by any arm
- 6/7 arms use zero LLM tokens during impact analysis
- Smoke/Pilot/Research profiles differ only in scenario count/strategy subset — not execution depth

### 3.2 Mismatch Count (Verified: 4)
| Arm | llm_by_design | llm_attached | Mismatch |
|-----|---------------|--------------|----------|
| monolithic | True | False | **YES** |
| agent | True | True | No |
| selective | True | False | **YES** |
| compiled_ai | False | False | No |
| delta_mcp | True | False | **YES** |
| incr_rtl | False | False | No |
| code_plan | True | False | **YES** |

### 3.3 Blocking Arms (Protocol Non-Compliance)
- **selective** (primary treatment): claims "hybrid graph+LLM", implements deterministic voter
- **delta_mcp**: claims LLM-only ablation, implements Jaccard similarity
- **code_plan**: claims LLM+graph reproduction, implements signal union
- **monolithic**: claims LLM, implements all-regenerate

### 3.4 Scientific-Design Mismatches
All ablation arms are **name-only references** to literature — no faithful reproduction exists.

### 3.5 Fairness Audit: Agent vs Selective
- Different backends (Qwen vs none)
- Different boundaries (LLM inference vs deterministic computation)
- Different repair budgets (3 vs 1)
- **Conclusion:** Current comparison invalid for token-efficiency claims (H4)

---

## 4. Required Actions

### 4.1 Implementation (Post-Decision)

| Task | Document | Priority |
|------|----------|----------|
| Implement `repository_agent` (iterative) | `REPOSITORY_AGENT_BASELINE_SPEC.md` | **SU-0011** |
| Implement shared regeneration executor | `SHARED_REGENERATION_EXECUTOR_DESIGN.md` | **SU-0010** |
| Extend `TokenUsage` / `RunRecord` per measurement boundary | `END_TO_END_MEASUREMENT_BOUNDARY.md` | SU-0010 |
| Add per-stage token accounting to runner/executor | — | SU-0010 |
| Rename arm labels in reports/figures (not code) | `ARM_ROLE_AND_NAMING_POLICY.md` | Immediate |

### 4.2 Documentation Updates (This Branch)
- [x] `REPOSITORY_AGENT_BASELINE_AUDIT.md` — current agent classification
- [x] `REPOSITORY_AGENT_BASELINE_SPEC.md` — baseline acceptance criteria
- [x] `SHARED_REGENERATION_EXECUTOR_DESIGN.md` — executor design
- [x] `ARM_ROLE_AND_NAMING_POLICY.md` — mapping, display names, compatibility
- [x] `EXTERNAL_DATASET_EVALUATION_POLICY.md` — Experiment D gate
- [x] `EXPERIMENTAL_DESIGN_V2.md` — experiment structure, hypotheses
- [x] `END_TO_END_MEASUREMENT_BOUNDARY.md` — measurement spec
- [x] `SU0010_IMPLEMENTATION_IMPACT_PLAN.md` — dependency graph
- [ ] Update state files (next section)

### 4.3 Protocol Documents (FROZEN — No Edits)
- `docs/FINAL_RESEARCH_PROTOCOL.md` — **DO NOT MODIFY**
- `docs/GROUND_TRUTH_PROTOCOL.md` — **DO NOT MODIFY**
- `docs/STATISTICAL_ANALYSIS_PLAN.md` — **DO NOT MODIFY**
- All other `docs/*.md` with FROZEN status

**Note:** Formal amendment/reconciliation process may be required before publication. No silent protocol edit authorized.

---

## 5. Current Agent Classification

**Audit Result:** `SINGLE_SHOT_LLM_SCOPE_BASELINE`

**Evidence:**
- Single LLM call with full artifact list in prompt
- No iterative retrieval, no file inspection, no context refinement
- No tool use, no generation, no validation, no repair
- Returns `ImpactPrediction` only

**Not:** REPRESENTATIVE_ITERATIVE_REPOSITORY_AGENT, PARTIAL_AGENT_WORKFLOW, ENGINEERING_MOCK, INSUFFICIENT_EVIDENCE

**Implication:** Current `agent` arm must be labeled `single_shot_llm_scope` in all scientific outputs. A true `repository_agent` requires SU-0011 implementation.

---

## 6. Baseline Acceptance Result

**`REPOSITORY_AGENT_BASELINE_SPEC.md`** defines minimum reproducible behavior for `repository_agent`:
- Natural-language requirement input, no ground-truth access
- Iterative bounded retrieval (max 5 rounds, 30 files, 6 model calls, 50K tokens)
- Tool interfaces: `read_file`, `list_dir`, `grep`
- Shared regeneration executor, shared validation, shared repair policy
- Same model/decoding parameters, same max attempt/timeout
- Complete token/tool-call accounting, deterministic controls

**Status:** DESIGN COMPLETE — awaiting SU-0011 authorization.

---

## 7. Approved Arm-Role Mapping

| Legacy ID | Scientific Role | Display Name | Short |
|-----------|----------------|--------------|-------|
| monolithic | full_scope_reference | Full-Scope Reference | FSR |
| agent (current) | single_shot_llm_scope | Single-Shot LLM Scope | SSLS |
| selective | hybrid_selective | Hybrid Selective | HS |
| compiled_ai | static_only | Static-Only Ablation | SOA |
| delta_mcp | semantic_only | Semantic-Only Ablation | SeOA |
| incr_rtl | traceability_only | Traceability-Only Ablation | TOA |
| code_plan | retrieval_planning_variant | Retrieval-Planning Variant | RPV |
| (future) | repository_agent | Repository Agent | RA |

**Code/checkpoints:** Legacy IDs unchanged.
**Figures/tables/new docs:** Scientific roles required.

---

## 8. Measurement Boundary Summary

| Stage | Included | Key Metrics |
|-------|----------|-------------|
| Selection | ✅ | tokens, calls, duration |
| Context Construction | ✅ | (part of selection/regen) |
| Regeneration | ✅ | tokens, calls, duration |
| Repair | ✅ | tokens, calls, duration |
| Validation | ✅ | duration only |
| **Outside** | ❌ | Setup, checkpointing, reporting |

**Fair comparison requires:** Same executor, same validators, same repair policy, matched correctness.

---

## 9. Shared Executor Dependency Graph Summary

```
ImpactPrediction → RegenerationPlan → Shared LLM Executor → Patch Application
→ Validation (Func → Regr → Arch) → Bounded Repair Loop → RunRecord
→ Checkpoint → Reports → Kaggle Bundle
```

**11 nodes** with owning modules, interfaces, dependencies, tests, unaffected areas.
Full detail: `SU0010_IMPLEMENTATION_IMPACT_PLAN.md`.

---

## 10. External Dataset Policy Summary

- Eligible only if: license + changes + corpus + ground truth + compatible unit + no leakage + reproducible + comparable metrics
- **All local arms run on same external dataset**
- Published scores: **contextual only** — no statistical comparison
- No dataset selected yet — researcher decision required
- Full policy: `EXTERNAL_DATASET_EVALUATION_POLICY.md`

---

## 11. SU-0010 Implementation Tasks

| Phase | Nodes | Effort |
|-------|-------|--------|
| 1. Core Types | `RegenerationPlan`, `Patch`, `ExecutionResult`, `ValidationResult` | 2d |
| 2. Planner Extension | `RegenerationPlanner.plan()` | 1d |
| 3. Patch Applier | Unified diff, rollback, isolation | 3d |
| 4. Validators | Functional, Regression, Architecture (parallel) | 4d |
| 5. Regeneration Executor | LLM-backed, token accounting | 3d |
| 6. Repair Loop Integration | Multi-validator pipeline | 2d |
| 7. RunRecord/Checkpoint | Extended schema | 2d |
| 8. Reports | Experiment A–D generators | 2d |
| 9. Bundle & Integration | Kaggle smoke, E2E test | 2d |
| **Total** | | **~21 days** |

**Blockers:** None (design complete). Requires researcher authorization.

---

## 12. SU-0011 Agent Work Required?

**YES.** The confirmatory comparison (RD-V2-01) requires a `repository_agent` implementing iterative repository-aware workflow. Current `agent` (`single_shot_llm_scope`) does not satisfy this. SU-0011 is **required for pilot/research authorization**.

---

## 13. Current Results Scientifically Usable?

| Result Set | Usable For |
|------------|------------|
| Kaggle smoke (`v0.7.0-smoke-passed`) | Engineering validation only (orchestration, GPU, model loading) |
| Dry-run benchmarks | Pipeline syntax, deterministic mock behavior |
| Arm audit reports | Design decisions, mismatch documentation |
| **Impact accuracy (Experiment A)** | **NOT YET** — requires shared executor for regeneration arms |
| **End-to-end (Experiment B)** | **NOT YET** — no regeneration layer exists |
| Published literature comparisons | **NO** — name-only references, no faithful reproduction |

**No publication evidence exists.** Pilot and Research phases **blocked** until SU-0010/SU-0011 complete.

---

## 14. Pilot Authorization

**PILOT NOT AUTHORIZED.**

**Blocking conditions (from audit):**
1. `selective` (primary treatment) has no LLM executor — violates H1/H2/H4 design
2. No regeneration execution layer exists — pilot "full evolution" cannot run
3. 4/7 arms have protocol mismatches — ablation design invalid
4. Literature references are name-only — validity threats unaddressed

**Minimum to authorize pilot:**
- `repository_agent` implemented (SU-0011) OR research question reframed
- Shared regeneration executor implemented (SU-0010)
- Protocol amendment if Option A (keep deterministic) chosen for `selective`

---

## 15. Working Tree Status

```
Branch: docs/research-design-v2
New files:
  reports/REPOSITORY_AGENT_BASELINE_AUDIT.md
  docs/REPOSITORY_AGENT_BASELINE_SPEC.md
  docs/SHARED_REGENERATION_EXECUTOR_DESIGN.md
  docs/ARM_ROLE_AND_NAMING_POLICY.md
  docs/EXTERNAL_DATASET_EVALUATION_POLICY.md
  reports/SU0010_IMPLEMENTATION_IMPACT_PLAN.md
  docs/EXPERIMENTAL_DESIGN_V2.md
  docs/END_TO_END_MEASUREMENT_BOUNDARY.md
  reports/RESEARCH_DESIGN_V2_DECISION_REPORT.md
Modified (pending):
  DECISION_LOG.md, TODO.md, SYSTEM_STATE.md
  reports/latest_phase_report.md, reports/PROJECT_HEALTH_REPORT.md
  docs/PROJECT_HANDOFF.md, docs/START_HERE.md
  selective_updates/CHANGE_INDEX.md
```

---

## 16. Historical Evidence Boundary (per RD-V2 researcher review)

**Existing seven-arm smoke: VALID for engineering orchestration, real Qwen inference, impact-strategy execution, checkpoint/resume, recovery, and cross-session reporting.**

**Existing seven-arm smoke: NOT VALID as evidence of end-to-end regeneration, code-quality comparison, workflow token efficiency, Pilot findings, or publication findings.**

Do not delete, alter, or reinterpret historical RunRecords.

---

## 17. NILES and Historical Compatibility (per RD-V2 researcher review)

**The NILES paper and historical engineering results remain separate artifacts.**

**No previous result will be silently relabeled or reinterpreted.**

**Any preliminary simulation remains exploratory, non-confirmatory, and is not a faithful reproduction of a named literature system.**

Do not rename production modules, internal strategy IDs, historical Run IDs, checkpoints, or existing result files.

---

## 18. Final Recommendation (per RD-V2 researcher review)

**Agent decision:**

```
KEEP_CURRENT_AGENT_AS_SINGLE_SHOT_BASELINE_AND_BUILD_ITERATIVE_AGENT
```

**Implementation order:**

```
SHARED_EXECUTOR_FIRST
ITERATIVE_AGENT_SECOND
```

**Pilot authorization:**

```
NOT AUTHORIZED
```

---

## 19. Final Status

**RESEARCH_DESIGN_V2_FINALIZED_FOR_RESEARCHER_APPROVAL**

All decisions documented, designs complete, no silent protocol edits, implementation plans traced. Awaiting researcher decisions on:
1. SU-0010 authorization (shared executor + types + validators)
2. SU-0011 authorization (repository agent iterative baseline)
3. Experiment D dataset selection (if any)
4. Protocol amendment vs implementation correction path