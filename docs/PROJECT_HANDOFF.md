# Project Handoff — Dependency-Aware Selective Regeneration Benchmark

**Handoff Date:** 2026-07-23
**Prepared by:** OpenCode (engineering assistant)
**Handoff to:** Human researcher (Ethan / subsequent sessions)
**Handoff type:** Kaggle smoke passed → pilot/research next

---

## 1. Executive Summary

The benchmark infrastructure for the Dependency-Aware Selective Regeneration study is **feature-complete, locally validated, and Kaggle-smoke-passed**. All six Phase 4 milestones (4A–4F) are implemented, tested, and merged. Phase 4F.1 remediation closed 5 scientific gaps. Two production fixes (failure propagation, graph wiring) were required for real Qwen execution. **Kaggle real smoke passed twice**: all 7 strategy arms succeeded with real Qwen2.5-Coder-7B-Instruct inference confirmed.

**What remains:** Implement checkpoint/resume, run pilot and research experiments, analyze results.

---

## 2. Phase Completion Status

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 0 | LOCAL_ENGINEERING_VALIDATED | Bootstrap, Conda env, Git baseline |
| Phase 1 | LOCAL_ENGINEERING_VALIDATED | Input audit, paper as authoritative source |
| Phase 2A | DRAFT (superseded) | Research protocol draft |
| Phase 2B | FROZEN | Protocol v1.0 frozen, 8 companion docs |
| Phase 3 | COMPLETE | 3 repos, 24 scenarios, manifests/profiles |
| Phase 3.5 | COMPLETE | Architecture audit, 13-layer design |
| Phase 3.6 | COMPLETE | Structure remediation, baseline commit |
| Phase 4A | COMPLETE | Domain models, enums, exceptions, protocols, config |
| Phase 4B | COMPLETE | Loaders, validation, workspace isolation |
| Phase 4C | COMPLETE | Mock/DryRun/Kaggle LLM backends |
| Phase 4D | COMPLETE | Budget, state machine, repair, runner, pipeline |
| Phase 4E | COMPLETE | 7 strategy arms, graph, selection |
| Phase 4F | COMPLETE | Evaluation engine, metrics, statistics, reporting |
| Phase 4F.1 | COMPLETE | Scientific remediation (5 gaps closed) |
| **Kaggle Smoke** | **PASSED** | 7/7 arms, Qwen confirmed, non-publication |
| **Checkpoint/Resume** | **NEXT** | Required for pilot/research profiles |

---

## 3. Current System State

- **Test suite:** 504/505 passing (1 skipped: torch import), pytest
- **Lint:** ruff 0 violations
- **Types:** mypy --strict: 0 errors (src)
- **Dependencies:** pip check clean (pre-existing conda issues unrelated); torch/transformers NOT imported locally
- **Environment:** Conda env `selective-regen-benchmark` (Python 3.11.15)
- **Architecture:** 13-layer design, protocol-based interfaces, dependency injection
- **Frozen protocol:** Research Protocol v1.0, 8 companion documents with SHA-256 checksums
- **Benchmark data:** 24 scenarios across 3 repositories (todo, djangocms, saleor)
- **Kaggle smoke:** PASSED — tag `v0.7.0-smoke-passed`, commit `0c58250`, 7/7 arms, Qwen confirmed
- **GitHub:** https://github.com/AhmedEhabH/dependency-aware-selective-regeneration-benchmark

---

## 4. What's Working

- **All 7 strategy arms** implemented: monolithic, agent, selective, compiled_ai, delta_mcp, incr_rtl, code_plan
- **Full evaluation pipeline:** metrics (recall, precision, F1, specificity, FPR, FNR, accuracy), confidence intervals (bootstrap, normal, Wilson, Agresti-Coull), effect sizes (Cohen's d, Cliff's delta), statistical tests (Mann-Whitney U, NI tests), multiple-comparison corrections (BH, Holm), paired analysis
- **Execution pipeline:** state machine, budget management, repair loops, workspace isolation, batch/dry-run modes
- **Kaggle backend:** skeleton with lazy imports, safe locally; real Qwen2.5-Coder inference confirmed on Kaggle
- **Dry-run mode:** deterministic mock responses, no API calls, full pipeline validation
- **2 benchmark scripts:** `notebooks/seven_arm_benchmark.ipynb` (Kaggle) and `seven_arm_benchmark.py` (local/CLI)
- **Kaggle real smoke:** passed twice — 7/7 arms, Qwen inference confirmed (325 prompt + 19 completion tokens)
- **3 execution profiles:** smoke (1 scenario), pilot (12x2x2), research (24x4x3)
- **Profile configs:** `configs/smoke.yaml`, `configs/pilot.yaml`, `configs/research.yaml`

---

## 5. What's Not Yet Done (Post-Smoke)

| Task | Priority | Notes |
|------|----------|-------|
| Implement checkpoint/resume | HIGH | Required for pilot (~2-3h) and research (~6-9h) due to Kaggle 9h session limit |
| Run pilot profile | MEDIUM | 12 scenarios, agent+selective, 2 reps; descriptive findings only (non-publication) |
| Run research profile | MEDIUM | 24 scenarios, 4 strategies, 3 reps; publication-quality evidence |
| Arm-to-protocol alignment review | SCIENTIFIC GATE | Review before first publication claim; ensure protocol compliance |
| Paper writing | OUT OF SCOPE | Not part of benchmark engineering |

---

## 6. Key Architecture Decisions

| Decision | Details |
|----------|---------|
| Phase 4E/4F split (D015) | Strategies separated from evaluation for independent testing |
| Protocol over ABC | `typing.Protocol` for all interfaces; ABC only for shared defaults |
| No global singletons | `Registry[T]` is instantiated and injected |
| Lazy Kaggle imports | `torch`/`transformers` only imported inside methods, never at module level |
| Immutable run records | `RunRecord` is a frozen dataclass |
| Canonical project root | `project/` is the Git root; `docs/` at repo root is legacy |
| Conda + hybrid pip | Conda for compiled deps (numpy, pandas), pip for dev tools |
| Protocol currently frozen | Protocol v1.0; amendments require formal process |

---

## 7. Remaining Scientific Gaps (Pre-Existing, Not Affected by Smoke)

| Gap | Details | Requires |
|-----|---------|----------|
| McNemar's test (H3) | Architecture-level detection metric needed | Protocol amendment |
| Architecture validation metrics (H3, AC-09) | No architecture metric in evaluation scope | Protocol amendment |
| Blast-radius interaction test (H5, AC-10) | Interaction term in mixed-effects model | Protocol amendment |

These gaps were identified during Phase 4F audit and confirmed unchanged by smoke. They do not block pilot or research execution. Results collected now are valid for H1, H2, and limited H4/H5 analysis but cannot support full H3 or H5 interaction claims. No protocol amendment is required before pilot execution.

---

## 8. Risks and Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Kaggle Qwen model mount fails | Medium | Notebook detects and warns; fallback to CPU prints warning |
| 9h Kaggle session limit exceeded | Low for smoke/pilot; Medium for research | Research may need multi-session or selected subset |
| GitHub rate limiting on Kaggle | Low | Notebook clones from public repo; retry logic |
| Environment drift between local/Kaggle | Medium | requirements-kaggle.txt pinned; dry-run tests same pipeline |
| No ground truth leakage | Low | Private evaluation boundary; hidden tests in scenario YAMLs |
| Paper vs. implementation drift | Low | Phase 4F audit verified protocol alignment |

---

## 9. Getting Started for Next Session

```bash
# 1. Activate environment
conda activate selective-regen-benchmark

# 2. Verify environment
python --version && pip check

# 3. Run tests
python -m pytest tests/ -v --tb=short

# 4. Verify dry-run smoke (no API calls)
python seven_arm_benchmark.py --dry-run --profile smoke

# 5. Check all state files
cat SYSTEM_STATE.md
cat TODO.md
cat DECISION_LOG.md  # last entry: D020

# 6. Verify smoke tag
git log --oneline -3
git tag -l 'v0.7*'
```

---

## 10. Key File Map

| Purpose | Path |
|---------|------|
| Frozen protocol | `project/docs/FINAL_RESEARCH_PROTOCOL.md` |
| Protocol companion docs | `project/docs/GROUND_TRUTH_PROTOCOL.md`, `SCENARIO_TAXONOMY.md`, `STATISTICAL_ANALYSIS_PLAN.md`, `EXECUTION_AND_FAILURE_POLICY.md`, `LEAKAGE_PREVENTION_PROTOCOL.md`, `REPRODUCIBILITY_PROTOCOL.md`, `RESEARCHER_DECISIONS_DA_AC.md` |
| Architecture docs | `project/docs/SOFTWARE_ARCHITECTURE.md`, `DEPENDENCY_RULES.md`, `EXTENSION_GUIDE.md`, `PHASE4_IMPLEMENTATION_BLUEPRINT.md` |
| Execution guide | `project/docs/OPENCODE_EXECUTION_GUIDE.md` |
| Kaggle execution guide | `project/docs/KAGGLE_EXECUTION_GUIDE.md` |
| Experiment profiles | `project/docs/EXPERIMENT_PROFILES.md` |
| Results and evidence policy | `project/docs/RESULTS_AND_EVIDENCE_POLICY.md` |
| System state | `project/SYSTEM_STATE.md` |
| Decision log | `project/DECISION_LOG.md` |
| TODO list | `project/TODO.md` |
| Start here | `project/docs/START_HERE.md` |
| Phase reports | `project/reports/PHASE4*.md` |
| Audit reports | `project/reports/PHASE4F_INDEPENDENT_SCIENTIFIC_AUDIT.md`, `PHASE4F_1_SCIENTIFIC_REMEDIATION_REPORT.md` |
| Kaggle readiness | `project/reports/KAGGLE_SMOKE_READINESS_REPORT.md`, `KAGGLE_FEASIBILITY_REPORT.md` |
| Phase 4F report | `project/reports/PHASE4F_EVALUATION_ENGINE_REPORT.md` |
| Final local prep report | `project/reports/FINAL_LOCAL_PREPARATION_REPORT.md` |

---

## 11. Git State

Kaggle smoke passed at commit `0c58250`. Tag `v0.7.0-smoke-passed` created and pushed. Main is up to date with origin/main.

**Current branch:** `docs/persist-smoke-handoff` (being merged into `main`)
**Latest commit:** `0c58250` (tag `v0.7.0-smoke-passed`)
**Working tree:** Updated state files, new handoff documents, moved report
**Staging:** After merge, working tree will be clean
