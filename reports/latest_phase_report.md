# Research Design V2 Freeze and Repository-Agent Baseline Audit

**Date:** 2026-07-25  
**Status:** COMPLETE — Ready for Researcher Review  
**Branch:** `docs/research-design-v2`  
**Evidence:** 10 design docs created, audit merged to main, state files updated

---

## Summary

Executed Research Design V2 Freeze and Repository-Agent Baseline Audit per AGENTS.md instructions. Two-phase execution:

**Phase A — Audit Merge:** Merged `audit/arm-to-protocol-execution` into `main` (merge commit `3a16596`). Adds 3 audit reports: `ARM_TO_PROTOCOL_EXECUTION_AUDIT.md`, `ARM_AUDIT_DECISION_REQUIRED.md`, `EXISTING_TAGS_AUDIT.md`.

**Phase B — Design Branch:** Created `docs/research-design-v2` branch documenting all researcher-approved experimental design decisions (RD-V2-01 through RD-V2-06). Produced 10 design documents:

1. `reports/REPOSITORY_AGENT_BASELINE_AUDIT.md` — Current agent classified as `SINGLE_SHOT_LLM_SCOPE_BASELINE`
2. `docs/REPOSITORY_AGENT_BASELINE_SPEC.md` — Iterative baseline acceptance criteria (max 5 rounds, 30 files, 6 calls, 50K tokens)
3. `docs/SHARED_REGENERATION_EXECUTOR_DESIGN.md` — Shared executor architecture for all end-to-end arms
4. `docs/ARM_ROLE_AND_NAMING_POLICY.md` — Legacy→scientific role mapping, naming rules, checkpoint compatibility
5. `docs/EXTERNAL_DATASET_EVALUATION_POLICY.md` — Experiment D gate: license, ground truth, no leakage, local execution mandatory
6. `reports/SU0010_IMPLEMENTATION_IMPACT_PLAN.md` — 11-node dependency graph from ImpactPrediction to Kaggle Bundle (~21 days)
7. `docs/EXPERIMENTAL_DESIGN_V2.md` — Experiments A/B/C/D, hypotheses, arm roles, measurement boundary
8. `docs/END_TO_END_MEASUREMENT_BOUNDARY.md` — Per-stage token accounting (selection/regen/repair/validation)
9. `reports/RESEARCH_DESIGN_V2_DECISION_REPORT.md` — Consolidated decision record
10. Updated all non-frozen state files (DECISION_LOG.md, TODO.md, SYSTEM_STATE.md, latest_phase_report.md, PROJECT_HEALTH_REPORT.md, PROJECT_HANDOFF.md, START_HERE.md, CHANGE_INDEX.md)

---

## Approved Research Decisions (Frozen for RD-V2)

| Decision | Summary |
|----------|---------|
| **RD-V2-01** | Primary comparison = iterative repository agent vs hybrid selective (matched LLM, repo, change, params, tools, budget, repair, validation, quality) |
| **RD-V2-02** | Arm roles: repository_agent, hybrid_selective, single_shot_llm_scope, static_only, semantic_only, traceability_only, full_scope_reference, retrieval_planning_variant |
| **RD-V2-03** | Literature claims = related work/inspiration only; no head-to-head stats vs published scores |
| **RD-V2-04** | Measurement boundary = selection + regen + repair + validation with per-stage token accounting |
| **RD-V2-05** | Efficiency claims require matched correctness/quality |
| **RD-V2-06** | Experiment A (impact accuracy), B (e2e evolution), C (ablations), D (optional external transfer) |

---

## Deliverables

| Artifact | Status |
|----------|--------|
| Audit merge to main | COMPLETE (merge commit `3a16596`) |
| Design branch `docs/research-design-v2` | COMPLETE (10 docs) |
| Agent classification | `SINGLE_SHOT_LLM_SCOPE_BASELINE` (not iterative) |
| Baseline acceptance criteria | DOCUMENTED (`REPOSITORY_AGENT_BASELINE_SPEC.md`) |
| Shared executor design | DOCUMENTED (`SHARED_REGENERATION_EXECUTOR_DESIGN.md`) |
| Arm role/naming policy | DOCUMENTED (`ARM_ROLE_AND_NAMING_POLICY.md`) |
| External dataset policy | DOCUMENTED (`EXTERNAL_DATASET_EVALUATION_POLICY.md`) |
| SU-0010 implementation plan | DOCUMENTED (`SU0010_IMPLEMENTATION_IMPACT_PLAN.md`) |
| Experimental design V2 | DOCUMENTED (`EXPERIMENTAL_DESIGN_V2.md`) |
| Measurement boundary spec | DOCUMENTED (`END_TO_END_MEASUREMENT_BOUNDARY.md`) |
| Decision report | DOCUMENTED (`RESEARCH_DESIGN_V2_DECISION_REPORT.md`) |
| State files updated | COMPLETE (8 files) |

---

## Quality Gates

| Gate | Result |
|------|--------|
| No production code modified | ✅ PASS |
| Frozen protocol docs untouched | ✅ PASS |
| Documentation-only changes | ✅ PASS |
| Git history clean on design branch | ✅ PASS |
| All prior quality gates preserved | ✅ PASS (613 tests, ruff 0, mypy 0) |

---

## Selective-Update Ledger

**Change ID:** SU-0003  
**Title:** Research Design V2 Freeze and Repository-Agent Baseline Audit  
**Canonical artifacts affected:** 10 new design docs, 8 state files updated  
**Derivatives regenerated:** 0 (no production code changes)  
**Quality outcome:** preserved  
**Record:** `project/selective_updates/records/SU-0003-research-design-v2-freeze.md`  
**Metrics:** `project/selective_updates/metrics/change_metrics.jsonl`

---

## Residual Risks

| Risk | Mitigation |
|------|------------|
| Pilot/Research blocked until SU-0010 + SU-0011 | Researcher authorization required |
| Current `agent` arm not iterative repository agent | SU-0011 addresses; honest labeling in place |
| No regeneration layer exists | SU-0010 addresses shared executor |
| Literature claims are name-only | Policy frozen (RD-V2-03); no stats vs published |
| Protocol amendment may be needed | Formal process documented; no silent edits |

---

## Next Exact Task

**Await researcher review of RD-V2 decisions.** If authorized:
1. Implement SU-0010 (shared regeneration executor + types + validators) — ~21 days
2. Implement SU-0011 (iterative repository agent baseline) — separate task
3. Then: Pilot → Research execution on Kaggle

---

## Git History

| Commit | Description |
|--------|-------------|
| `3a16596` | Merge audit/arm-to-protocol-execution into main (--no-ff) |
| `docs/research-design-v2` | Branch with 10 RD-V2 design documents |
| `reports/RESEARCH_DESIGN_V2_DECISION_REPORT.md` | Consolidated decision record |

---

**RESEARCH_DESIGN_V2_READY_FOR_RESEARCHER_REVIEW**