# Arm Role and Naming Policy

**Date:** 2026-07-25
**Branch:** docs/research-design-v2
**Protocol Version:** 1.0 (FROZEN)
**Source Commit:** 3a16596
**Status:** POLICY — Research Design V2 Decision

---

## 1. Purpose

This document establishes the **official scientific display roles and naming** for all experimental arms in Research Design V2 (RD-V2), per RD-V2-02. It maps legacy internal IDs to approved roles, specifies which IDs remain for compatibility, and defines migration rules for historical data.

---

## 2. Legacy ID → Scientific Role Mapping

| Legacy Internal ID | Approved Scientific Role | Display Name (Figures/Tables) | Short Code |
|--------------------|-------------------------|-------------------------------|------------|
| `monolithic` | `full_scope_reference` | Full-Scope Reference | FSR |
| `agent` | `single_shot_llm_scope` | Single-Shot LLM Scope | SSLS |
| `selective` | `hybrid_selective` | Hybrid Selective | HS |
| `compiled_ai` | `static_only` | Static-Only Ablation | SOA |
| `delta_mcp` | `semantic_only` | Semantic-Only Ablation | SeOA |
| `incr_rtl` | `traceability_only` | Traceability-Only Ablation | TOA |
| `code_plan` | `retrieval_planning_variant` | Retrieval-Planning Variant | RPV |

### 2.1 Role Definitions (per RD-V2-02)

| Role | Description |
|------|-------------|
| **repository_agent** | Main realistic baseline — iterative repository-aware workflow (NOT yet implemented; see SU-0011) |
| **hybrid_selective** | Proposed treatment — explicit graph, semantic, and traceability-based scope governance (current `selective` implementation) |
| **single_shot_llm_scope** | Optional simple LLM scope-selection baseline — one-call implementation (current `agent` implementation) |
| **static_only** | Static/dependency graph ablation (current `compiled_ai`) |
| **semantic_only** | Semantic-signal ablation (current `delta_mcp`) |
| **traceability_only** | Traceability ablation (current `incr_rtl`) |
| **full_scope_reference** | Worst-case/upper-bound reference only (current `monolithic`) |
| **retrieval_planning_variant** | Exploratory planning/union variant (current `code_plan`) |

---

## 3. Compatibility Rules

### 3.1 Internal IDs That Remain (Checkpoint/Run ID Compatibility)

| ID | Retention Reason |
|----|------------------|
| `monolithic`, `agent`, `selective`, `compiled_ai`, `delta_mcp`, `incr_rtl`, `code_plan` | Embedded in historical Run IDs, checkpoint files, HF datasets, published logs |
| `STRATEGY_NAMES` list in `seven_arm_benchmark.py` | Source of truth for execution pipeline |
| Strategy class names (`RepositoryAgentStrategy`, `HybridSelectiveStrategy`, etc.) | Python module/class identifiers |

**These MUST NOT be renamed** in production code to preserve:
- Checkpoint resume capability
- Historical Run ID readability
- HF dataset schema compatibility
- Kaggle bundle reproducibility

### 3.2 Names in New Figures/Tables (Scientific Output)

| Context | Required Naming |
|---------|-----------------|
| Paper figures (bar plots, line charts) | **Display Name** column from Table 2 (e.g., "Hybrid Selective", "Static-Only Ablation") |
| Paper tables (results, ablations) | **Display Name** or **Short Code** (e.g., "HS", "SOA") |
| Statistical analysis reports | **Scientific Role** (e.g., `hybrid_selective`, `static_only`) |
| Notebook exports | **Display Name** with **Short Code** in parentheses |
| LaTeX/CSV publication tables | **Display Name** |

### 3.3 Historical Results Retain Legacy Labels

| Artifact | Label Policy |
|----------|--------------|
| Frozen protocol documents (`docs/FINAL_RESEARCH_PROTOCOL.md`, etc.) | **Retain legacy IDs** — these are frozen |
| Existing benchmark summary JSON (`benchmark_summary.json`) | **Retain legacy IDs** — historical evidence |
| Kaggle smoke results (tag `v0.7.0-smoke-passed`) | **Retain legacy IDs** — engineering validation |
| HF dataset records | **Retain legacy IDs** — schema frozen |
| Prior reports (`reports/PHASE4E_*.md`, etc.) | **Retain legacy IDs** — historical record |

### 3.4 Legacy Run ID Readability

Historical Run IDs follow pattern:
```
{scenario_id}_{legacy_strategy_id}_rep{repetition}_{hash}
```
Example: `todo-mod-001_agent_rep1_a1b2c3d4`

**Policy:** Keep legacy strategy ID in Run ID. **Do not retroactively rewrite.**

Mapping table for interpretation:
```
todo-mod-001_agent_rep1_...    → single_shot_llm_scope
todo-mod-001_selective_rep1_... → hybrid_selective
todo-mod-001_monolithic_rep1_... → full_scope_reference
```

---

## 4. Schema Migration (Future)

### 4.1 Current Schema (v1.0)

```python
# RunIdentity.strategy_name: str  # legacy ID
```

### 4.2 Proposed Schema v1.1 (Post-Publication)

```python
@dataclass(frozen=True)
class RunIdentity:
    run_id: str                    # unchanged (contains legacy ID)
    protocol_version: str
    repository_commit_sha: str
    scenario_id: str
    strategy_name: str             # legacy ID (for compatibility)
    scientific_role: str           # NEW: e.g., "hybrid_selective"
    display_name: str              # NEW: e.g., "Hybrid Selective"
    short_code: str                # NEW: e.g., "HS"
```

### 4.3 Migration Process

1. **Add fields** to `RunIdentity` (optional, default from mapping table)
2. **Backfill** historical records via one-time migration script
3. **Update** `ReportGenerator` to use new fields
4. **Deprecate** `strategy_name` for scientific use (keep for compatibility)
5. **Version** protocol → 1.1

**Timeline:** Post-publication only. No migration in RD-V2.

---

## 5. Literature Reference Policy (per RD-V2-03)

| Literature Method | Our Arm | Citation Style |
|-------------------|---------|----------------|
| RepoCoder (Zhang et al. 2023) | Conceptual ancestor of `single_shot_llm_scope` | "inspired by RepoCoder-style context feeding" |
| Compiled AI (Trooskens 2026) | Name-only reference for `static_only` | "static-only ablation (named after Compiled AI paradigm)" |
| DeltaMCP (Pujara 2026) | Name-only reference for `semantic_only` | "semantic-only ablation (named after DeltaMCP paradigm)" |
| IncreRTL (Chen 2026) | Name-only reference for `traceability_only` | "traceability-only ablation (named after IncreRTL paradigm)" |
| CodePlan (Bairi 2023) | Name-only reference for `retrieval_planning_variant` | "retrieval-planning variant (named after CodePlan paradigm)" |

**Strict prohibition:** Do not claim "reproduces," "implements," "faithfully replicates," or "matches" any literature method unless independent fidelity evidence exists (which it does not for any arm).

---

## 6. Implementation Checklist

- [ ] Update `docs/EXPERIMENT_PROFILES.md` — replace arm descriptions with scientific roles
- [ ] Update `seven_arm_benchmark.py` — add `SCIENTIFIC_ROLE_MAP` constant (display only)
- [ ] Update `ReportGenerator` — use display names in new reports
- [ ] Create `docs/ARM_ROLE_MAPPING_TABLE.md` — standalone reference for reviewers
- [ ] Verify no production code renames legacy IDs
- [ ] Verify frozen protocol documents unchanged

---

## 7. Quick Reference Card

```
┌─────────────────────┬──────────────────────────┬──────────────────┬──────────┐
│ Legacy ID           │ Scientific Role          │ Display Name     │ Short    │
├─────────────────────┼──────────────────────────┼──────────────────┼──────────┤
│ monolithic          │ full_scope_reference     │ Full-Scope Ref   │ FSR      │
│ agent               │ single_shot_llm_scope    │ Single-Shot LLM  │ SSLS     │
│ selective           │ hybrid_selective         │ Hybrid Selective │ HS       │
│ compiled_ai         │ static_only              │ Static-Only      │ SOA      │
│ delta_mcp           │ semantic_only            │ Semantic-Only    │ SeOA     │
│ incr_rtl            │ traceability_only        │ Traceability-Only│ TOA      │
│ code_plan           │ retrieval_planning_var   │ Retrieval-Plan   │ RPV      │
└─────────────────────┴──────────────────────────┴──────────────────┴──────────┘

NOT implemented yet (future SU-0011):
repository_agent     │ Representative iterative repo-aware workflow
```

---

**Policy Status:** FROZEN for RD-V2 — all scientific documents must use approved roles
**Enforcement:** CI check on new documentation (grep for legacy IDs in figure/table captions)
**Exception:** Frozen protocol documents, historical reports, checkpoint/code internals