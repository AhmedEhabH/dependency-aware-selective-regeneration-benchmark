# Project Health Report

**Report Date:** 2026-07-23  
**Project:** Selective Regeneration Benchmark  
**Phase:** Kaggle Smoke Passed — Engineering Validation Complete

---

## Executive Summary

Kaggle real smoke passed twice. All 7 strategy arms succeeded with real Qwen2.5-Coder-7B-Instruct inference confirmed (325 prompt + 19 completion tokens). Two production fixes applied: failure propagation (real Qwen errors, token_usage, smoke-stage tagging) and graph wiring (ProfileGraphBuilder, capabilities design, NullLLMBackend). Smoke evidence is non-publication. Next task: implement checkpoint/resume for long-running profiles.

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
| Phase 4A — Domain Models | ✅ COMPLETE | 111 | 17 src + 8 test | ruff:0, mypy:0, pytest:111/111 |
| Phase 4B — Loaders | ✅ COMPLETE | 206 | 11 src + 14 test | ruff:0, mypy:0, pytest:206/206 |
| Phase 4C — Model Backends | ✅ COMPLETE | 229 | 5 src + 6 test | ruff:0, mypy:0, pytest:229/229 |
| Phase 4D — Execution Core | ✅ COMPLETE | 288 | 7 src + 7 test | ruff:0, mypy:0, pytest:288/288 |
| Phase 4E — Impact Strategies | ✅ COMPLETE | 332 | 14 src + 3 test | ruff:0, mypy:0, pytest:332/332 |
| Phase 4F — Evaluation Engine | ✅ COMPLETE | 410 | 10 src + 15 test | ruff:0, mypy:0, pytest:410/410 |
| Phase 4F.1 — Scientific Remediation | ✅ COMPLETE | 441 | 7 modified + 2 new docs | ruff:0, mypy:0, pytest:441/441 |
| **Kaggle Smoke Pass** | ✅ **PASSED** | **504** | **2 fixes (8+12 files)** | **ruff:0, mypy:0, pytest:504/505 (1 skipped torch)** |

---

## Total Counts

| Metric | Count |
|--------|-------|
| **Production Files (src/benchmark/)** | 62 |
| **Test Files** | 15 |
| **Total Tests** | 504 (+1 skipped torch) |
| **Benchmark Scenarios** | 24 |
| **Repositories** | 3 (todo, djangocms, saleor) |
| **Strategies** | 7 (monolithic, agent, selective, compiled_ai, delta_mcp, incr_rtl, code_plan) |

---

## Quality Gates

| Gate | Status | Details |
|------|--------|---------|
| **Ruff Lint** | ✅ PASS | 0 violations |
| **Mypy Strict** | ✅ PASS | 0 errors, 60 source files; 5 pre-existing in tests |
| **Pytest** | ✅ PASS | 504/505 passed (1 skipped: torch import) |
| **pip check** | ✅ PASS | No broken requirements |

---

## Scientific Protocol Coverage

| Category | Count | Percentage |
|----------|-------|------------|
| Implemented & validated | 14 | 74% |
| Partial | 1 | 5% |
| Missing | 3 | 16% |
| **Total requirements** | **19** | **100%** |

---

## Next Steps

Kaggle smoke passed. Remaining work:

1. Implement checkpoint/resume support for long-running profiles
2. Run pilot experiment (12 scenarios, agent+selective, 2 reps)
3. Run research experiment (24 scenarios, 4 strategies, 3 reps)
4. Arm-to-protocol alignment review (scientific gate before publication)
5. Paper writing (out of scope of benchmark engineering)

---

## Environment

- **Platform:** Windows (win32)
- **Python:** 3.11.5
- **Conda:** 2.21.0
- **Git:** 2.49.0
- **Conda Env:** `selective-regen-benchmark` (activated)