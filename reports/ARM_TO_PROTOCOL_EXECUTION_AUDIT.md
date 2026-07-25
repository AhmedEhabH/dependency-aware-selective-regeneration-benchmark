# Arm-to-Protocol Execution Audit — Detailed Matrix

**Date:** 2026-07-25
**Branch:** audit/arm-to-protocol-execution
**Protocol Version:** 1.0 (FROZEN)
**Source Commit:** 0c831e397faa15ae31dc1442c5273f1e8d134253

---

## Arm Matrix

| Field | monolithic | agent | selective | compiled_ai | delta_mcp | incr_rtl | code_plan |
|-------|------------|-------|-----------|-------------|-----------|----------|-----------|
| **implementation_class** | MonolithicRegenerationStrategy | RepositoryAgentStrategy | HybridSelectiveStrategy | StaticOnlyStrategy | SemanticOnlyStrategy | TraceabilityOnlyStrategy | FullContextStrategy |
| **actual_algorithm** | Deterministic: all artifacts → regenerate | Single-shot LLM classification of full repo context | Deterministic 3-signal voter (graph BFS + Jaccard semantic + coverage lookup) | Deterministic: graph BFS from all artifacts → regenerate reachable | Deterministic: Jaccard token overlap (req text vs path) ≥ 0.5 → regenerate | Deterministic: coverage map lookup → covered artifacts → regenerate | Deterministic: union of graph BFS + Jaccard semantic (0.3) + coverage lookup → any signal → regenerate |
| **measurement_boundary** | analyze_impact() only | analyze_impact() only (1 LLM call) | analyze_impact() only (0 LLM) | analyze_impact() only (0 LLM) | analyze_impact() only (0 LLM) | analyze_impact() only (0 LLM) | analyze_impact() only (0 LLM) |
| **llm_accepted** | True (design) | True | True (design) | False | True (design) | False | True (design) |
| **actual_backend** | None | KaggleQwenBackend / MockLLMBackend | None | None | None | None | None |
| **llm_invoked_during_impact** | No | Yes | No | No | No | No | No |
| **llm_invoked_during_regeneration** | N/A (no regeneration) | N/A (no regeneration) | N/A (no regeneration) | N/A (no regeneration) | N/A (no regeneration) | N/A (no regeneration) | N/A (no regeneration) |
| **model_calls_in_smoke** | 0 | 0* | 0 | 0 | 0 | 0 | 0 |
| **prompt_tokens_smoke** | 0 | 0* | 0 | 0 | 0 | 0 | 0 |
| **completion_tokens_smoke** | 0 | 0* | 0 | 0 | 0 | 0 | 0 |
| **total_tokens_smoke** | 0 | 0* | 0 | 0 | 0 | 0 | 0 |
| **graph_used** | No | No | Yes (BFS undirected) | Yes (BFS undirected) | No | No | Yes (BFS undirected) |
| **semantic_mechanism** | None | None (LLM internal) | Jaccard token overlap (req text vs artifact path) | None | Jaccard token overlap (req text vs artifact path) | None | Jaccard token overlap (req text vs artifact path, threshold 0.3) |
| **traceability_mechanism** | None | None | Coverage map (test → sources union) | None | None | Coverage map (test → sources union) | Coverage map (test → sources union) |
| **regeneration_performed** | No | No | No | No | No | No | No |
| **claimed_protocol_role** | Baseline (worst-case) | Repository-retrieval baseline | **Primary treatment** — hybrid graph+LLM | Ablation — graph only | Ablation — LLM only | Ablation — traceability only | Literature reference — CodePlan |
| **role_supported_by_code** | Baseline (deterministic) | LLM classifier (no retrieval loop) | Deterministic voter — **no LLM** | Graph-only ablation ✓ | **Not LLM-only** — deterministic semantic | Traceability-only ablation ✓ | **Not CodePlan** — deterministic union |
| **literature_relationship** | N/A (baseline) | CONCEPTUAL_ADAPTATION (RepoCoder-like context, no iteration) | NAME_ONLY_REFERENCE (proposed method not implemented) | NAME_ONLY_REFERENCE (Compiled AI paradigm not implemented) | NAME_ONLY_REFERENCE (DeltaMCP not implemented) | NAME_ONLY_REFERENCE (IncreRTL not implemented) | NAME_ONLY_REFERENCE (CodePlan not implemented) |
| **documentation_accurate** | **No** — design claims LLM | Partially — design matches, but not iterative retrieval | **No** — design claims LLM, code has none | Partially — design says no LLM, code has none; but claims "Compiled AI" paradigm | **No** — design claims LLM, code has none | Partially — design says no LLM, code has none; but claims "IncreRTL" | **No** — design claims LLM, code has none; claims CodePlan reproduction |
| **comparison_fairness** | Baseline vs LLM (agent) — mismatched work | LLM impact analysis only — not comparable to selective's deterministic analysis | Deterministic vs LLM (agent) — **mismatched boundaries** | Deterministic vs deterministic — fair for graph ablation | Deterministic vs LLM (agent) — **mismatched boundaries** | Deterministic vs deterministic — fair for traceability ablation | Deterministic vs LLM (agent) — **mismatched boundaries** |
| **smoke_membership** | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| **pilot_membership** | No | Yes | Yes | No | No | No | No |
| **research_membership** | No | Yes | Yes | Yes | Yes | No | No |
| **classification** | EXPECTED_NON_LLM_BASELINE | EXPECTED_AMORTIZED_ZERO_RUNTIME_TOKENS* | EXPECTED_ZERO_TOKENS_FOR_IMPACT_ANALYSIS | EXPECTED_ZERO_TOKENS_FOR_IMPACT_ANALYSIS | EXPECTED_ZERO_TOKENS_FOR_IMPACT_ANALYSIS | EXPECTED_NON_LLM_BASELINE | EXPECTED_ZERO_TOKENS_FOR_IMPACT_ANALYSIS |
| **required_action** | Fix design table (llm:false) | No code change; doc clarification | **BLOCKING** — RD-01 decision needed | Fix literature claim (NAME_ONLY) | **BLOCKING** — RD-02 decision needed | Fix literature claim (NAME_ONLY) | **BLOCKING** — RD-02 decision needed |

\* Dry-run uses `MockLLMBackend` but `runner.dry_run()` bypasses strategy entirely. Real run would show tokens for `agent` only.

---

## Classification Definitions

| Classification | Meaning |
|----------------|---------|
| EXPECTED_ZERO_TOKENS_FOR_IMPACT_ANALYSIS | Arm correctly uses zero LLM tokens during impact analysis stage (by design, no LLM invoked) |
| EXPECTED_AMORTIZED_ZERO_RUNTIME_TOKENS | Arm would have zero runtime tokens under Compiled AI paradigm (one-time compilation), but this is not implemented |
| EXPECTED_NON_LLM_BASELINE | Arm is intentionally non-LLM baseline (monolithic, incr_rtl) |
| WIRING_DEFECT | Arm should have LLM but wiring omits it (selective, delta_mcp, code_plan, monolithic per design table) |
| MISSING_REGENERATION_EXECUTION | All arms — no regeneration layer exists in codebase |
| DOCUMENTATION_MISMATCH | Docs claim capabilities not in implementation |
| SCIENTIFIC_DESIGN_MISMATCH | Algorithm differs fundamentally from protocol/literature role |
| INSUFFICIENT_EVIDENCE | Cannot determine (not used here) |

---

## Detailed Per-Arm Findings

### monolithic
- **Design table claim:** `{"llm": true, "graph": false}`
- **Actual:** No LLM, no graph. Returns all artifacts as `regenerate`.
- **Mismatch:** `llm_by_design=True` but `llm_attached=False` → **MISMATCH** (diagnostic at seven_arm_benchmark.py:1164-1180 confirms)
- **Classification:** EXPECTED_NON_LLM_BASELINE (but design table wrong)
- **Required:** Fix `STRATEGY_CAPABILITIES_DESIGN["monolithic"]["llm"] = False`

### agent
- **Design table claim:** `{"llm": true, "graph": false}`
- **Actual:** LLM backend injected, called once per `analyze_impact()`. Prompt contains full artifact list. Parses JSON response for impacted paths.
- **Mismatch:** None — `llm_by_design=True`, `llm_attached=True` → MATCH
- **Note:** Not iterative retrieval-generation (RepoCoder); single-shot classification. Conceptual adaptation only.
- **Classification:** EXPECTED_AMORTIZED_ZERO_RUNTIME_TOKENS (misnomer — has tokens in real run, zero in dry-run due to bypass)

### selective (PRIMARY TREATMENT — BLOCKING)
- **Design table claim:** `{"llm": true, "graph": true}`
- **Actual:** Graph injected, **no LLM backend**. Algorithm: graph BFS + Jaccard semantic + coverage lookup → vote (≥2 signals=regenerate, 1=human_review, 0=preserve).
- **Mismatch:** `llm_by_design=True`, `llm_attached=False` → **MISMATCH**
- **Protocol role:** "Hybrid graph + LLM impact analysis" — **not implemented**
- **Literature:** Proposed method in Master Proposal — **not reproduced**
- **Classification:** EXPECTED_ZERO_TOKENS_FOR_IMPACT_ANALYSIS (but should be LLM-backed per protocol)
- **Required:** RD-01 decision (keep deterministic vs add LLM vs implement full method)

### compiled_ai
- **Design table claim:** `{"llm": false, "graph": true}`
- **Actual:** Graph injected, no LLM. Algorithm: graph BFS from all artifacts (treats all as changed) → regenerate reachable.
- **Mismatch:** None — `llm_by_design=False`, `llm_attached=False` → MATCH
- **Protocol role:** "Static analysis ablation" — **implemented correctly as graph-only**
- **Literature:** Compiled AI (Trooskens 2026) — **name only**; no compilation, no amortization, no zero-runtime paradigm
- **Classification:** EXPECTED_ZERO_TOKENS_FOR_IMPACT_ANALYSIS
- **Required:** Fix literature claim in EXPERIMENT_PROFILES.md (NAME_ONLY_REFERENCE)

### delta_mcp (BLOCKING)
- **Design table claim:** `{"llm": true, "graph": false}`
- **Actual:** No graph, **no LLM**. Algorithm: Jaccard(token_overlap(req_text, artifact_path)) ≥ 0.5 → regenerate.
- **Mismatch:** `llm_by_design=True`, `llm_attached=False` → **MISMATCH**
- **Protocol role:** "LLM-only ablation" — **implemented as deterministic semantic-only**
- **Literature:** DeltaMCP (Pujara 2026) — **name only**; no spec-diff, no LLM transformation, no patch integration
- **Classification:** EXPECTED_ZERO_TOKENS_FOR_IMPACT_ANALYSIS (but should be LLM-backed per protocol)
- **Required:** RD-02 decision

### incr_rtl
- **Design table claim:** `{"llm": false, "graph": false}`
- **Actual:** No graph, no LLM. Algorithm: coverage map union → covered artifacts → regenerate.
- **Mismatch:** None — `llm_by_design=False`, `llm_attached=False` → MATCH
- **Protocol role:** "Traceability-only ablation" — **implemented correctly as coverage lookup**
- **Literature:** IncreRTL (Chen 2026) — **name only**; no traceability-guided selection, no LLM regeneration
- **Classification:** EXPECTED_NON_LLM_BASELINE
- **Required:** Fix literature claim in EXPERIMENT_PROFILES.md (NAME_ONLY_REFERENCE)

### code_plan (BLOCKING)
- **Design table claim:** `{"llm": true, "graph": true}`
- **Actual:** Graph injected, **no LLM**. Algorithm: union of graph BFS + Jaccard semantic (0.3) + coverage lookup → any signal → regenerate.
- **Mismatch:** `llm_by_design=True`, `llm_attached=False` → **MISMATCH**
- **Protocol role:** "Literature reference — replicates CodePlan" — **not replicated**
- **Literature:** CodePlan (Bairi 2023) — **name only**; no planning, no iterative LLM edits, no retrieval
- **Classification:** EXPECTED_ZERO_TOKENS_FOR_IMPACT_ANALYSIS (but should be LLM-backed per protocol)
- **Required:** RD-02 decision

---

## Fairness Audit: Agent vs Selective

| Dimension | agent | selective | Fair? |
|-----------|-------|-----------|-------|
| **Model identity** | Qwen2.5-Coder | N/A (no LLM) | **No** — different backends |
| **Generation parameters** | temp=0, max_tokens=4096 | N/A | **No** |
| **Prompt boundary** | Full repo context + artifact list | N/A | **No** |
| **Context exposure** | All artifacts in prompt | Graph + semantic + coverage (deterministic) | **No** |
| **Artifact candidate set** | All artifacts (LLM selects) | All artifacts (voter selects) | Same universe |
| **Generation obligation** | LLM must output valid JSON | Deterministic vote | **No** |
| **Token budget** | 4096 output tokens | 0 | **No** |
| **Repair attempts** | 2 (via RepairLoop) | 0 (no generation to repair) | **No** |
| **Max attempts** | 3 | 1 (analyze_impact only) | **No** |
| **Timeout** | Configurable | 0 (no LLM call) | **No** |
| **Failure handling** | ModelBackendError → failed run | No LLM failures possible | **No** |
| **Evaluation path** | Impact prediction only | Impact prediction only | Same (impact only) |
| **Ground-truth access** | No (blind prediction) | No (blind prediction) | Same |

**Verdict:** Comparison of `agent` (LLM impact analysis) vs `selective` (deterministic impact analysis) is **not a valid token-efficiency comparison**. Different work boundaries: LLM inference vs deterministic computation. Efficiency claims (H4) require equivalent correctness conditions (per protocol H4 criterion), which cannot be established without regeneration and validation.

**Valid comparison options:**
1. **Impact-analysis vs impact-analysis** — both deterministic: compare `selective` vs `compiled_ai` vs `delta_mcp` vs `incr_rtl` vs `code_plan` (all zero-LLM)
2. **End-to-end vs end-to-end** — requires regeneration layer for both `agent` and `selective` with same repair budget
3. **LLM-impact vs LLM-impact** — requires `selective` to have LLM executor (Option B/C in RD-01)

---

## Seven-Arm Design Structure

| Arm | Research Hypothesis | Primary/Secondary/Exploratory | Smoke Role | Pilot Role | Research Role | Ablation/Reference Role |
|-----|---------------------|-------------------------------|------------|------------|---------------|------------------------|
| monolithic | H1 (worst-case recall=1.0) | Secondary (baseline) | All 7 arms execute | Reference only | Impact-only | Baseline reference |
| agent | H1, H2, H4 (baseline) | Primary (baseline) | All 7 arms execute | **Primary baseline** | Full evolution | Retrieval baseline |
| selective | **H1, H2, H3, H4, H5 (treatment)** | **Primary (treatment)** | All 7 arms execute | **Primary treatment** | Full evolution | N/A (treatment) |
| compiled_ai | H1 (graph-only recall) | Secondary (ablation) | All 7 arms execute | Not used | Impact-only | Graph ablation |
| delta_mcp | H1 (semantic-only recall) | Secondary (ablation) | All 7 arms execute | Not used | Impact-only | Semantic ablation |
| incr_rtl | H1 (traceability-only recall) | Secondary (ablation) | All 7 arms execute | Not used | Impact-only (optional) | Traceability ablation |
| code_plan | H1 (literature comparison) | Exploratory (reference) | All 7 arms execute | Not used | Impact-only | Literature reference |

**Design Assessment:** The seven arms form an **inconsistent experimental set**:
- Only 2 arms (`agent`, `selective`) are in pilot — but `selective` doesn't match protocol design
- Research profile includes 4 arms for "full evolution" but only `agent` has generation capability (and it's not wired for regeneration)
- Three ablation arms (`compiled_ai`, `delta_mcp`, `incr_rtl`) are deterministic — valid for impact-analysis ablation but not for "full evolution"
- `code_plan` is name-only literature reference in all profiles
- `monolithic` is baseline but mis-specified in design table

**Protocol requires amendment or implementation correction before pilot/research.**

---

## Required Actions Summary

| Action | Arms Affected | Type | Priority |
|--------|---------------|------|----------|
| Fix `STRATEGY_CAPABILITIES_DESIGN` table | All | Code (seven_arm_benchmark.py:75-83) | Immediate |
| Fix `EXPERIMENT_PROFILES.md` literature claims | selective, compiled_ai, delta_mcp, incr_rtl, code_plan | Documentation | Immediate |
| RD-01: Decide `selective` algorithm | selective | Researcher decision | **Blocking** |
| RD-02: Decide ablation arms fate | delta_mcp, code_plan, compiled_ai, incr_rtl | Researcher decision | **Blocking** |
| RD-03: Define measurement boundary | All | Researcher decision | **Blocking** |
| RD-04: Decide `monolithic` baseline | monolithic | Researcher decision | High |
| RD-05: Retract/implement literature claims | compiled_ai, delta_mcp, incr_rtl, code_plan | Researcher decision | High |
| RD-06: Protocol amendment vs implementation fix | All | Researcher decision | **Blocking** |
| Implement regeneration layer (if RD-03=B/C) | agent, selective, compiled_ai, delta_mcp | Code | Post-decision |
| Full smoke rerun | All | Validation | Post-code-changes |

---

**ARM_AUDIT_BLOCKED** — Cannot proceed to Pilot or Research without researcher decisions RD-01 through RD-06 and corresponding implementation.