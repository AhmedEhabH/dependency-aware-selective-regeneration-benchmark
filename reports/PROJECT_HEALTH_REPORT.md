# Project Health Report

**Report Date:** 2026-07-25  
**Project:** Selective Regeneration Benchmark  
**Phase:** Research Design V2 Freeze Complete — SU-0003 Documented

---

## Executive Summary

Research Design V2 Freeze and Repository-Agent Baseline Audit completed. Phase A: Merged arm-to-protocol execution audit to `main` (commit `3a16596`). Phase B: Created `docs/research-design-v2` branch with 10 design documents recording researcher-approved decisions RD-V2-01 through RD-V2-06. Current `RepositoryAgentStrategy` audited and classified as `SINGLE_SHOT_LLM_SCOPE_BASELINE` (not iterative). Baseline acceptance criteria defined for iterative `repository_agent` (SU-0011). Shared regeneration executor designed for fair end-to-end comparison (SU-0010). Arm role/naming policy, external dataset policy, and implementation impact plan documented. No production code modified. All frozen protocol documents untouched. Pilot and Research phases remain blocked pending SU-0010 completion and baseline agent implementation.

---

## Phase Completion Status

| Phase | Status | Tests | Files | Quality Gates |
|-------|--------|-------|-------|---------------|
| Phase 0 — Bootstrap | ✅ COMPLETE | N/A | 7 dirs | All pass |
| Phase 1 — Input Audit | ✅ COMPLETE | N/A | 1 report | All pass |
| Phase 2A — Protocol Draft | ✅ COMPLETE | N/A | 1 draft | All pass |
| Phase 2B — Protocol Freeze | ✅ COMPLETE | N/A | 8 docs | All pass |
| Phase 3 — Repo/Scenario Prep | ✅ COMPLETE | N/A | 35 files | All pass |
| Phase 3.5 — Architecture Audit | ✅ COMPLETE | N/A | 10 docs | All pass |
| Phase 3.6 — Structure Remediation | ✅ COMPLETE | N/A | Baseline commit | All pass |
| Phase 3.7 — Canonical Remediation | ✅ COMPLETE | N/A | 1 script + ledger | All pass |
| **SU-0002 runs_dir Fix** | ✅ **VALIDATED** | **2 new** | **1 src + 1 test** | **ruff:0, mypy:0, pytest:613/615** |
| Phase 4A — Domain Models | ✅ COMPLETE | 111 | 17 src + 8 test | ruff:0, mypy:0, pytest:111/111 |
| Phase 4B — Loaders | ✅ COMPLETE | 206 | 11 src + 14 test | ruff:0, mypy:0, pytest:206/206 |
| Phase 4C — Model Backends | ✅ COMPLETE | 229 | 5 src + 6 test | ruff:0, mypy:0, pytest:229/229 |
| Phase 4D — Execution Core | ✅ COMPLETE | 288 | 7 src + 7 test | ruff:0, mypy:0, pytest:288/288 |
| Phase 4E — Impact Strategies | ✅ COMPLETE | 332 | 14 src + 3 test | ruff:0, mypy:0, pytest:332/332 |
| Phase 4F — Evaluation Engine | ✅ COMPLETE | 410 | 10 src + 15 test | ruff:0, mypy:0, pytest:410/410 |
| Phase 4F.1 — Scientific Remediation | ✅ COMPLETE | 441 | 7 modified + 2 docs | ruff:0, mypy:0, pytest:441/441 |
| **Kaggle Smoke Pass** | ✅ **PASSED** | **504** | **2 fixes (8+12 files)** | **ruff:0, mypy:0, pytest:504/505 (1 skipped)** |
| **SU-0003 RD-V2 Freeze** | ✅ **DOCUMENTED** | **0** | **10 docs + 8 state files** | **ruff:0, mypy:0, pytest:613/615** |

---

## Total Counts

| Metric | Count |
|--------|-------|
| **Production Files (src/benchmark/)** | 62 |
| **Test Files** | 15 |
| **Total Tests** | 613 (+1 skipped torch) |
| **Benchmark Scenarios** | 24 |
| **Repositories** | 3 (todo, djangocms, saleor) |
| **Strategies (legacy IDs)** | 7 (monolithic, agent, selective, compiled_ai, delta_mcp, incr_rtl, code_plan) |
| **Strategies (scientific roles)** | 8 (repository_agent, hybrid_selective, single_shot_llm_scope, static_only, semantic_only, traceability_only, full_scope_reference, retrieval_planning_variant) |

---

## Quality Gates

| Gate | Status | Details |
|------|--------|---------|
| **Ruff Lint** | ✅ PASS | 0 violations |
| **Mypy Strict** | ✅ PASS | 0 errors, 60 source files; 5 pre-existing in tests |
| **Pytest** | ✅ PASS | 613/615 passed (2 skipped: torch import) |
| **pip check** | ✅ PASS | No broken requirements |
| **Import Isolation** | ✅ PASS | No torch/transformers at package load |

---

## Scientific Protocol Coverage

| Category | Count | Percentage |
|----------|-------|------------|
| Implemented & validated | 14 | 74% |
| Partial | 1 | 5% |
| Missing | 3 | 16% |
| **Total requirements** | **19** | **100%** |

---

## Research Design V2 Decisions (Frozen)

| Decision | Summary |
|----------|---------|
| **RD-V2-01** | Primary comparison: iterative repository agent vs hybrid selective (matched LLM, repo, change, params, tools, budget, repair, validation, quality) |
| **RD-V2-02** | Arm roles: repository_agent, hybrid_selective, single_shot_llm_scope, static_only, semantic_only, traceability_only, full_scope_reference, retrieval_planning_variant |
| **RD-V2-03** | Literature claims = related work/inspiration only; no head-to-head stats vs published scores |
| **RD-V2-04** | Measurement boundary: selection + regen + repair + validation with per-stage token accounting |
| **RD-V2-05** | Efficiency claims require matched correctness/quality |
| **RD-V2-06** | Experiment A (impact accuracy), B (e2e evolution), C (ablations), D (optional external transfer) |

---

## Next Steps

**Blocked on researcher review of RD-V2 decisions.** If authorized:

1. **SU-0010** — Implement shared regeneration executor + types + validators (~21 days)
2. **SU-0011** — Implement iterative repository agent baseline (separate task)
3. Then: Pilot → Research execution on Kaggle

---

## Environment

- **Platform:** Windows (win32)
- **Python:** 3.11.15
- **Conda:** 23.10.0
- **Git:** 2.49.0
- **Conda Env:** `selective-regen-benchmark` (activated)

---

## Git Status

```
Branch: docs/research-design-v2
Status: 10 new design docs, 8 state files modified
Main:   merge commit 3a16596 (audit/arm-to-protocol-execution merged --no-ff)
Tags:   v0.7.0-smoke-passed at 0c58250 (unchanged)
```