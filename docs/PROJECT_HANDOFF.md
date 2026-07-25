# Project Handoff — Dependency-Aware Selective Regeneration Benchmark

**Handoff Date:** 2026-07-25
**Prepared by:** OpenCode (engineering assistant)
**Handoff to:** Human researcher (Ethan / subsequent sessions)
**Handoff type:** Research Design V2 Freeze Complete — Awaiting Researcher Review

---

## 1. Executive Summary

The benchmark infrastructure for the Dependency-Aware Selective Regeneration study is **feature-complete, locally validated, and Kaggle-smoke-passed**. All six Phase 4 milestones (4A–4F) are implemented, tested, and merged. Phase 4F.1 remediation closed 5 scientific gaps. Two production fixes (failure propagation, graph wiring) were required for real Qwen execution. **Kaggle real smoke passed twice**: all 7 strategy arms succeeded with real Qwen2.5-Coder-7B-Instruct inference confirmed.

**Research Design V2 Freeze** completed: Arm-to-protocol execution audit merged to `main`. Created `docs/research-design-v2` branch with 10 design documents recording researcher-approved experimental design decisions (RD-V2-01 through RD-V2-06). Current `RepositoryAgentStrategy` audited and classified as `SINGLE_SHOT_LLM_SCOPE_BASELINE` (not iterative). Baseline acceptance criteria defined for iterative `repository_agent` (SU-0011). Shared regeneration executor designed for fair end-to-end comparison (SU-0010). Arm role/naming policy, external dataset policy, and implementation impact plan documented. No production code modified. All frozen protocol documents untouched. Pilot and Research phases remain blocked pending SU-0010 completion and baseline agent implementation.

**What remains:** Researcher review of RD-V2 decisions → SU-0010 authorization (shared executor) → SU-0011 authorization (iterative repository agent) → Checkpoint/resume → Pilot → Research.

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
| **RD-V2 Freeze** | **DOCUMENTED** | 10 design docs on `docs/research-design-v2` branch |
| **Checkpoint/Resume** | **NEXT (SU-0010)** | Required for pilot/research profiles |

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
- **RD-V2 branch:** `docs/research-design-v2` with 10 design documents
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
- **Selective-update ledger:** `project/selective_updates/` with SU-0001 (canonical remediation), SU-0002 (runs_dir fix), SU-0003 (RD-V2 freeze)

---

## 5. Research Design V2 Decisions (Frozen)

| Decision | Summary |
|----------|---------|
| **RD-V2-01** | Primary comparison: iterative repository agent vs hybrid selective (matched LLM, repo, change, params, tools, budget, repair, validation, quality) |
| **RD-V2-02** | Arm roles: repository_agent, hybrid_selective, single_shot_llm_scope, static_only, semantic_only, traceability_only, full_scope_reference, retrieval_planning_variant |
| **RD-V2-03** | Literature claims = related work/inspiration only; no head-to-head stats vs published scores |
| **RD-V2-04** | Measurement boundary: selection + regen + repair + validation with per-stage token accounting |
| **RD-V2-05** | Efficiency claims require matched correctness/quality |
| **RD-V2-06** | Experiment A (impact accuracy), B (e2e evolution), C (ablations), D (optional external transfer) |

**Current agent classification:** `SINGLE_SHOT_LLM_SCOPE_BASELINE` — single LLM call with full artifact list, no iteration, no tools, no generation, no repair.

**Required for confirmatory comparison:** `repository_agent` (iterative, bounded retrieval, file inspection, scope selection) — SU-0011.

---

## 6. What's Not Yet Done (Post-RD-V2)

| Task | Priority | Notes |
|------|----------|-------|
| **SU-0010: Shared Regeneration Executor** | HIGH | Required for all end-to-end arms; ~21 days; authorized after RD-V2 review |
| **SU-0011: Iterative Repository Agent** | HIGH | Required for confirmatory comparison; separate task from SU-0010 |
| **Checkpoint/Resume (K004)** | HIGH | Required for pilot (~2-3h) and research (~6-9h) due to Kaggle 9h limit |
| **Run Pilot Profile** | MEDIUM | 12 scenarios, agent+selective, 2 reps; descriptive only (non-publication) |
| **Run Research Profile** | MEDIUM | 24 scenarios, 4 strategies, 3 reps; publication-quality evidence |
| **Arm-to-protocol alignment review** | SCIENTIFIC GATE | Before first publication claim; ensure protocol compliance |
| **Paper writing** | OUT OF SCOPE | Not part of benchmark engineering |

---

## 7. Key Architecture Decisions

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
| Selective update policy | All changes require a ledger record under `project/selective_updates/records/` |
| Bundle generation | Automated via `scripts/build_upload_bundle.py` |

---

## 8. Remaining Scientific Gaps (Pre-Existing, Not Affected by RD-V2)

| Gap | Details | Requires |
|-----|---------|----------|
| McNemar's test (H3) | Architecture-level detection metric needed | Protocol amendment |
| Architecture validation metrics (H3, AC-09) | No architecture metric in evaluation scope | Protocol amendment |
| Blast-radius interaction test (H5, AC-10) | Interaction term in mixed-effects model | Protocol amendment |

These gaps were identified during Phase 4F audit and confirmed unchanged by RD-V2. They do not block pilot or research execution. Results collected now are valid for H1, H2, and limited H4/H5 analysis but cannot support full H3 or H5 interaction claims. No protocol amendment is required before pilot execution.

---

## 9. Risks and Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Kaggle Qwen model mount fails | Medium | Notebook detects and warns; fallback to CPU prints warning |
| 9h Kaggle session limit exceeded | Low for smoke/pilot; Medium for research | Research may need multi-session or selected subset |
| GitHub rate limiting on Kaggle | Low | Notebook clones from public repo; retry logic |
| Environment drift between local/Kaggle | Medium | requirements-kaggle.txt pinned; dry-run tests same pipeline |
| No ground truth leakage | Low | Private evaluation boundary; hidden tests in scenario YAMLs |
| Paper vs. implementation drift | Low | Phase 4F audit verified protocol alignment |

---

## 10. Getting Started for Next Session

```bash
# 1. Activate environment
conda activate selective-regen-benchmark

# 2. Verify environment
python --version && pip check

# 3. Run tests (613 passing, 1 skipped torch)
python -m pytest tests/ -v --tb=short

# 4. Verify RD-V2 branch
git checkout docs/research-design-v2
git log --oneline -3

# 5. Read key state files
cat SYSTEM_STATE.md
cat TODO.md
cat DECISION_LOG.md  # last entry: D023

# 6. Review RD-V2 design docs (in docs/research-design-v2 branch)
# docs/REPOSITORY_AGENT_BASELINE_SPEC.md
# docs/SHARED_REGENERATION_EXECUTOR_DESIGN.md
# docs/ARM_ROLE_AND_NAMING_POLICY.md
# docs/EXTERNAL_DATASET_EVALUATION_POLICY.md
# docs/EXPERIMENTAL_DESIGN_V2.md
# docs/END_TO_END_MEASUREMENT_BOUNDARY.md
# reports/REPOSITORY_AGENT_BASELINE_AUDIT.md
# reports/SU0010_IMPLEMENTATION_IMPACT_PLAN.md
# reports/RESEARCH_DESIGN_V2_DECISION_REPORT.md

# 7. Check latest phase report
cat reports/latest_phase_report.md

# 8. Check health report
cat reports/PROJECT_HEALTH_REPORT.md
```

---

## 11. Key File Map

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
| **RD-V2 design docs** | `project/docs/REPOSITORY_AGENT_BASELINE_SPEC.md`, `SHARED_REGENERATION_EXECUTOR_DESIGN.md`, `ARM_ROLE_AND_NAMING_POLICY.md`, `EXTERNAL_DATASET_EVALUATION_POLICY.md`, `EXPERIMENTAL_DESIGN_V2.md`, `END_TO_END_MEASUREMENT_BOUNDARY.md` |
| **RD-V2 audit/plan** | `project/reports/REPOSITORY_AGENT_BASELINE_AUDIT.md`, `SU0010_IMPLEMENTATION_IMPACT_PLAN.md`, `RESEARCH_DESIGN_V2_DECISION_REPORT.md` |

---

## 11. Git State

```
Main branch:   merge commit 3a16596 (audit/arm-to-protocol-execution merged --no-ff)
Current branch: docs/research-design-v2 (10 design docs, 8 state files modified)
Tags:          v0.7.0-smoke-passed at 0c58250 (unchanged)
Working tree:  Modified state files on docs/research-design-v2; no production code changes
```

---

## 12. Golden Rules

1. **No local LLM inference** — no torch/transformers locally
2. **No modifying frozen protocol documents** (8 docs under `docs/`)
3. **No modifying `inputs/`** — immutable external data
4. **Smoke evidence is non-publication** — do not cite
5. **Canonical project root is `project/`** (where `.git` lives)
6. **Failed runs must remain visible** — no deletion
7. **Commit code before any execution run** — tag for traceability
8. **All production changes require selective-update ledger entry**

---

## 13. If You Get Lost

```bash
# List all state files
ls SYSTEM_STATE.md TODO.md DECISION_LOG.md

# Show recent git history
git log --oneline -10

# Show tags
git tag -l 'v0.*'

# Read handoff
cat docs/PROJECT_HANDOFF.md

# Switch to RD-V2 branch
git checkout docs/research-design-v2
```

---

**RESEARCH_DESIGN_V2_READY_FOR_RESEARCHER_REVIEW**