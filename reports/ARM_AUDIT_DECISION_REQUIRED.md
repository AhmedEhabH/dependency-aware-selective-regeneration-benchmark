# Arm Audit — Decision Required

**Date:** 2026-07-25
**Branch:** audit/arm-to-protocol-execution
**Protocol Version:** 1.0 (FROZEN)
**Source Commit:** 0c831e3

---

## 1. Verified Benchmark Measurement Boundary

**The benchmark measures IMPACT ANALYSIS ONLY** — the `analyze_impact()` method call that returns an `ImpactPrediction`.

- **No regeneration** is executed by any arm.
- **No LLM generation** occurs in 6/7 arms (only `agent` calls an LLM).
- **No repair-loop generation** exists in the codebase (the `RepairLoop` infrastructure exists but strategies don't perform generation).
- **Token/model-call accounting** reflects only the (mostly absent) LLM calls during impact analysis.
- **Smoke/Pilot/Research profiles** differ only in scenario count, strategy subset, and repetitions — not in execution depth.

**Protocol Gap:** `FINAL_RESEARCH_PROTOCOL.md §6` and `EXPERIMENT_PROFILES.md` describe "full evolution" for pilot/research, but **no execution code implements regeneration**. The `BenchmarkRunner` only calls `analyze_impact()`.

---

## 2. Verified Mismatch Count

**Exact count: 4 mismatches** (arms where `llm_by_design=True` but `llm_attached=False`):

| Arm | llm_by_design | llm_attached | Mismatch |
|-----|---------------|--------------|----------|
| monolithic | True | False | **YES** |
| agent | True | True | No |
| selective | True | False | **YES** |
| compiled_ai | False | False | No |
| delta_mcp | True | False | **YES** |
| incr_rtl | False | False | No |
| code_plan | True | False | **YES** |

The previous report's count of 3 (selective, delta_mcp, code_plan) missed `monolithic`. The diagnostic in `seven_arm_benchmark.py:1164-1180` correctly identifies all 4.

---

## 3. Blocking Arms (Protocol Non-Compliance)

| Arm | Blocking Issue | Severity |
|-----|----------------|----------|
| **selective** | Primary treatment; protocol claims "hybrid graph + LLM"; implements graph + deterministic semantic + traceability with **zero LLM** | **BLOCKING** — invalidates H1/H2/H4 primary comparisons |
| **delta_mcp** | Protocol claims LLM-only ablation; implements deterministic Jaccard similarity with **zero LLM** | **BLOCKING** — invalidates ablation design |
| **code_plan** | Protocol claims LLM+graph; implements deterministic signal union with **zero LLM**; literature comparison is name-only | **BLOCKING** — invalidates literature reference |
| **monolithic** | Protocol claims LLM; implements deterministic "all regenerate" with **zero LLM** | **BLOCKING** — baseline mis-specified |

---

## 4. Documentation-Only Issues

| Issue | Files Affected | Severity |
|-------|----------------|----------|
| `STRATEGY_CAPABILITIES_DESIGN` table claims LLM for 5/7 arms | `seven_arm_benchmark.py:75-83` | High (source of mismatches) |
| `EXPERIMENT_PROFILES.md` describes arms with capabilities they don't have | `docs/EXPERIMENT_PROFILES.md:14-123` | High |
| `describe_capabilities()` diagnostic is correct but driven by wrong design table | `seven_arm_benchmark.py:86-119` | Medium |
| Protocol describes "graph → LLM executor" architecture not implemented | `FINAL_RESEARCH_PROTOCOL.md`, Master Proposal | High |
| Literature comparison tables claim reproductions that are name-only | `EXPERIMENT_PROFILES.md`, this audit | Medium |

---

## 5. Wiring Defects

| Defect | Location | Impact |
|--------|----------|--------|
| `selective` constructed without LLM backend despite design requiring it | `seven_arm_benchmark.py:218` — `make_strategy("selective", ...)` passes no backend | Arm cannot invoke LLM even if algorithm supported it |
| `delta_mcp` constructed without LLM backend | `seven_arm_benchmark.py:220` — `SemanticOnlyStrategy` instantiated with `{}` | Same |
| `code_plan` constructed without LLM backend | `seven_arm_benchmark.py:222` — `FullContextStrategy` instantiated with `{graph}` only | Same |
| `monolithic` has no LLM path at all | `strategies/monolithic.py` — no backend parameter, no LLM call | By implementation, not wiring |

---

## 6. Scientific-Design Mismatches

| Arm | Protocol Role | Actual Algorithm | Mismatch Type |
|-----|---------------|------------------|---------------|
| selective | Hybrid graph+LLM impact analysis | Deterministic 3-signal voter (graph/Jaccard/coverage) | **Algorithm replaced** — LLM executor removed |
| delta_mcp | LLM-only semantic ablation | Deterministic Jaccard threshold | **Algorithm replaced** — LLM removed |
| code_plan | Literature reproduction (planning + LLM edits) | Deterministic signal union | **Name-only reference** |
| compiled_ai | Compiled AI paradigm (amortized LLM) | Static graph propagation | **Name-only reference** |
| incr_rtl | Traceability-guided LLM regeneration | Coverage map lookup | **Name-only reference** |
| agent | Repository-retrieval baseline | Single-shot LLM classification | **Conceptual adaptation** (not iterative) |

---

## 7. Code Changes Required?

**YES — code changes are required for protocol compliance.**

### Option A: Keep implementations, correct names/roles/docs
- Rename arms to match actual algorithms (e.g., `selective` → `deterministic_hybrid_voter`, `delta_mcp` → `semantic_jaccard`, `code_plan` → `full_context_union`, `compiled_ai` → `static_graph_propagation`, `incr_rtl` → `traceability_coverage`)
- Update `STRATEGY_CAPABILITIES_DESIGN` to match reality (only `agent` has LLM)
- Update all protocol/experiment docs
- **Consequence:** Benchmark no longer tests the proposed method; primary treatment becomes a deterministic baseline

### Option B: Fix wiring to match design (add LLM backends)
- Inject `LLMBackend` into `selective`, `delta_mcp`, `code_plan`, `monolithic` constructors
- Modify algorithms to call LLM during impact analysis (for `selective`, `delta_mcp`, `code_plan`) or regeneration (for `monolithic` if regeneration added)
- **Consequence:** Arms gain LLM calls; token measurements become non-zero; but algorithms still don't match literature (no iterative edits, no planning, no spec-diff, no traceability-guided regen)

### Option C: Implement algorithms to match protocol/literature
- `selective`: Add LLM executor that regenerates artifacts in graph-determined scope
- `delta_mcp`: Implement spec-aware diff + LLM transformation + patch integration
- `code_plan`: Implement repository planning + iterative LLM edit chain
- `compiled_ai`: Implement one-time LLM compilation + zero-runtime execution
- `incr_rtl`: Implement traceability-guided localized LLM regeneration
- Add regeneration execution layer (shared orafter `analyze_impact()` for full-evolution arms
- **Consequence:** Major implementation effort; pilot/research blocked until complete

---

## 8. Documentation-Only Changes Sufficient?

**NO** — if the research intent is to test the protocol's proposed method (hybrid graph+LLM selective regeneration) and its ablations.

**YES** — if the research intent is redefined to compare deterministic impact-analysis methods only, with `agent` as the sole LLM baseline. This requires:
- Protocol amendment (AC-11 process)
- New hypotheses aligned with deterministic methods
- Explicit acceptance that no LLM-based selective regeneration is tested

---

## 9. Rerun Requirements

| Scenario | Required? | Details |
|----------|-----------|---------|
| Targeted smoke rerun (current arms) | **No** — current smoke passes orchestration | Would reproduce same mismatches |
| Full seven-arm smoke rerun after fixes | **Yes** — if any code changes made | Required to verify arm execution with corrected wiring/algorithms |
| Pilot rerun | **Blocked** until arm mismatches resolved | Pilot uses `agent` + `selective`; `selective` is blocking |
| Research rerun | **Blocked** | Research uses 4 arms including 3 mismatched |

---

## 10. Pilot Authorization Status

**PILOT NOT AUTHORIZED.**

**Blocking conditions:**
1. `selective` (primary treatment) has no LLM executor — violates H1/H2/H4 design
2. No regeneration execution layer exists — pilot "full evolution" cannot run
3. 4/7 arms have protocol mismatches — ablation design invalid
4. Literature references are name-only — validity threats unaddressed

**Minimum to authorize pilot:**
- Resolution of `selective` mismatch (Option A, B, or C above)
- Implementation of regeneration execution for at least `agent` and `selective`
- Protocol amendment if Option A chosen

---

## 11. Smallest Exact Researcher Decisions Required

| Decision ID | Decision Required | Options | Default Recommendation |
|-------------|-------------------|---------|------------------------|
| **RD-01** | Primary treatment (`selective`) algorithm | A: Keep deterministic voter, rename, amend protocol<br>B: Add LLM executor to existing voter<br>C: Implement full hybrid graph+LLM+regeneration | **C** (matches proposal) — but requires implementation |
| **RD-02** | Ablation arms (`delta_mcp`, `compiled_ai`, `incr_rtl`, `code_plan`) | A: Keep deterministic, rename, document as ablations of deterministic voter<br>B: Add LLM to match protocol design<br>C: Implement literature algorithms | **A** if RD-01=A; **C** if RD-01=C |
| **RD-03** | Measurement boundary | A: Impact analysis only (current)<br>B: Impact + regeneration for full-evolution arms<br>C: Full sequential evolution | **B** minimum for H2/H3/H4; **C** for protocol compliance |
| **RD-04** | Baseline (`monolithic`) | A: Keep deterministic all-regenerate (rename)<br>B: Add LLM regeneration to match design | **A** — baseline doesn't need LLM |
| **RD-05** | Literature comparison claims | A: Retract reproduction claims; label as "inspired by"<br>B: Implement to match literature | **A** for immediate pilot; **B** for confirmatory research |
| **RD-06** | Protocol amendment | A: Amend protocol to match current deterministic design<br>B: Amend implementation to match frozen protocol | **B** for scientific integrity; **A** only with full documentation of scope change |

---

## 12. Final Status

| Checkpoint | Status |
|------------|--------|
| Measurement boundary verified | ✓ Impact analysis only |
| Mismatch count verified | ✓ 4 mismatches |
| Blocking arms identified | ✓ 4 arms (selective, delta_mcp, code_plan, monolithic) |
| Documentation issues catalogued | ✓ 5 major doc mismatches |
| Wiring defects catalogued | ✓ 4 wiring omissions |
| Scientific-design mismatches | ✓ 6/7 arms name-only or algorithm-replaced |
| Code changes required | **YES** (for protocol compliance) |
| Documentation-only sufficient | **NO** (unless protocol amended) |
| Targeted smoke rerun required | **NO** (current smoke valid for orchestration only) |
| Full smoke rerun required | **YES** (after any code changes) |
| Pilot authorized | **NO** |
| Researcher decisions required | **6 decisions (RD-01 through RD-06)** |

---

**ARM_AUDIT_BLOCKED** — Pilot and Research phases blocked until RD-01 through RD-06 are resolved and corresponding implementation/documentation changes are made and smoke-validated.