# Project Handoff — Dependency-Aware Selective Regeneration Benchmark

**Handoff Date:** 2026-07-27
**Prepared by:** OpenCode (engineering assistant)
**Handoff to:** Human researcher (subsequent sessions)
**Handoff type:** THREE-ARM-CORE-EXPERIMENT RECOVERED — branch experiment/three-arm-smoke-v2

---

## 1. Executive Summary

The project was recovered from a broken methodology-conformance work-in-progress that overfitted selection signals to Ground Truth, broke the full test suite (36 failures), and introduced untested design complexity. All WIP changes were stashed as `broken methodology-conformance WIP 2026-07-27`. The last green baseline at commit `0a1c603` (1063 passed, 5 skipped, 0 failed) was confirmed and a new branch `experiment/three-arm-smoke-v2` was created from it.

The three-arm core experiment is now frozen:
- `full_scope_reference` (monolithic) — regenerate all eligible artifacts
- `dependency_aware_selective` (selective) — repository graph + anchor/keyword mapping
- `repository_agent` (iterative_repository_agent) — bounded LLM loop with list/read/search tools

All arms share the same LLM backend, temperature (0.0), per-call max_tokens (4096), SharedRegenerationExecutor, and isolated workspace.

## 2. Canonical Structure

```
project/
├── src/benchmark/               canonical production code
├── benchmark_data/              repositories, profiles, scenarios
│   ├── manifests/
│   ├── repository_profiles/
│   ├── repositories/todo/       pinned to b8a33e2
│   └── scenarios/               24 protocol scenarios + 3 smoke scenarios
├── tests/
│   ├── contract/                protocol and architecture contract tests
│   ├── evaluator_assets/        NOT collected by pytest; run via subprocess
│   ├── hidden_tests/            (removed — was WIP-only; does not exist on clean baseline)
│   ├── integration/
│   └── unit/
├── configs/
│   └── smoke.yaml               (historical; V2 profile defined in seven_arm_benchmark.py)
├── docs/
│   ├── FINAL_RESEARCH_PROTOCOL.md  v1.0 FROZEN
│   ├── MASTER_IMPLEMENTATION_PLAN.md
│   ├── PROJECT_HANDOFF.md
│   └── ...
├── selective_updates/
│   ├── CHANGE_INDEX.md
│   ├── metrics/change_metrics.jsonl
│   └── records/
│       ├── SCIENTIFIC-SMOKE-V1.md
│       ├── THREE-ARM-CORE-EXPERIMENT.md
│       └── ...
├── scripts/
│   └── build_upload_bundle.py
├── kaggle_upload/               mirror regenerated only via build_upload_bundle.py
├── seven_arm_benchmark.py       CLI entry point
└── pyproject.toml
```

## 3. Current State

- **Branch:** experiment/three-arm-smoke-v2
- **HEAD:** 0a1c603 (commit — chore(data): pin controlled-repo SHA to b8a33e2 and regenerate bundle)
- **Working tree:** dirty with uncommitted V2 work (scenario contract corrections, profile fixes)
- **Canonical V2 profile source:** PROFILES["scientific-smoke-v2"] in seven_arm_benchmark.py (the removed duplicate V2 config)
- **Test suite:** baseline 1063 passed, 5 skipped, 0 failed (at clean HEAD); current suite includes additional V2 tests
- **Lint:** ruff 0 violations
- **Types:** mypy strict 0 errors
- **Dependencies:** pip check clean
- **Benchmark data:** 3 repositories (todo, djangocms, saleor), 24 protocol scenarios + 3 smoke scenarios
- **Kaggle status:** Not launched and not authorized

## 4. Core Scientific Question

> For a given natural-language requirement change, which strategy produces a correct implementation with the fewest unnecessary modifications, lowest token consumption, and fewest model calls?

### Three Confirmatory Arms

| Role | Legacy ID | Scope Determination | Model Calls |
|------|-----------|-------------------|-------------|
| full_scope_reference | monolithic | All eligible source artifacts | 1 per artifact |
| dependency_aware_selective | selective | Repository graph + anchors + BFS | 1 per selected artifact |
| repository_agent | iterative_repository_agent | Bounded LLM loop (list/read/search) | ≤8 total |

### Shared Across All Arms

- Same LLM backend (Qwen2.5-Coder on Kaggle)
- Same temperature (0.0)
- Same per-call max_tokens (4096)
- Same SharedRegenerationExecutor for writing code
- Same validation pipeline
- Same isolated workspace

## 5. Scientific Smoke V2 Policy

| Dimension | Value |
|-----------|-------|
| Repositories | 1 (controlled Django Todo) |
| Independent changes | 3 |
| Arms | 3 |
| Repetitions | 1 |
| Total real runs | 9 |
| Execution platform | Kaggle (Qwen2.5-Coder) |
| Evidence tier | scientific_smoke_v2 (non-publication) |

### Changes

1. **todo-smoke-001** (localized) — Add Task priority with low/medium/high and default medium
2. **todo-smoke-002** (cross-layer) — Add Task soft deletion with deleted_at, restore endpoint
3. **todo-smoke-003** (cross-cutting) — Only Project owner may modify tasks in that Project

Each starts from the same clean pinned baseline (b8a33e2). They are not cumulative.

## 6. Pilot Policy

Authorized only after real Smoke V2 completes and passes independent audit.

| Criterion | Requirement |
|-----------|-------------|
| Minimum changes | 7 |
| Minimum repositories | 3 |
| Minimum LOC per repository | 5,000 |
| License | Permissive (MIT, BSD, Apache 2.0) |
| Commit | Pinned exact commit |
| Baseline | Passing reproducible test suite |

## 7. What Is Complete (may include historical items)

- Baseline recovery from 0a1c603 (1063 pass, 5 skip) — historical
- Three-arm core experiment amendment (THREE-ARM-CORE-EXPERIMENT.md) — historical
- Three smoke scenarios drafted (todo-smoke-001, 002, 003) — being corrected against baseline
- Evaluator-only test assets in tests/evaluator_assets/ (pytest-norecursed)
- Contract tests for all 13 required contracts
- All 7 historical strategy arms preserved — historical
- kaggle_upload regenerable via build_upload_bundle.py
- Caches and build artifacts excluded

## 8. What Remains

| Task | Priority | Notes |
|------|----------|-------|
| Complete scenario contract corrections | HIGH | V2-01B in progress |
| Complete repository profile truth corrections | HIGH | V2-01B in progress |
| Safe ArtifactUniverse implementation | HIGH | V2-02 after independent approval |
| **Execute Scientific Smoke V2 on Kaggle** | HIGH | Unauthorized — blocked until V2-01/V2-02 complete |
| Audit Smoke V2 results | HIGH | Independent verification before Pilot authorization |
| Integrate Pilot repositories | MEDIUM | ≥5K LOC, permissive license, pinned commit, passing tests |
| Run Pilot profile | MEDIUM | 7+ changes, 3+ repos, agent+selective |
| Merge to main | LOW | After successful Smoke V2 |
| Create stable tag | LOW | Only after real Smoke V2 passes and is audited |

## 9. Git State

```
Current branch:  experiment/three-arm-smoke-v2
HEAD:            0a1c603 (chore(data): pin controlled-repo SHA to b8a33e2)
Local/remote:    not yet pushed
Working tree:    dirty (uncommitted V2 data-truth corrections)
Tags:            v0.7.0-smoke-passed at 0c58250 (unchanged)
Stash:           broken methodology-conformance WIP 2026-07-27
```

## 10. Stash Recovery

The broken WIP is stashed as `broken methodology-conformance WIP 2026-07-27` on the original branch `experiment/scientific-smoke-v1`. A patch file `broken-methodology-wip.patch` and status file `broken-methodology-wip-status.txt` were saved to the parent directory for reference. The stash contains:

- Overfitted methodology conformance tests (test_methodology_conformance.py)
- Hidden tests under tests/hidden_tests/
- Signal tuning (stop words, AST extraction, thresholds, traceability)
- Selective signal modules (builder.py, semantic.py, traceability.py)
- Class alias for IterativeRepositoryAgentStrategy

None of these should be applied without explicit authorization.

## 11. V2-01 → V2-01B — Data-Truth Corrections (2026-07-28)

### V2-01 (completed earlier)

| Item | Status |
|------|--------|
| Scenario contracts corrected against actual controlled baseline | Done |
| Profile llm_editable policy frozen | Done |
| Duplicate V2 config removed | Done |

### V2-01B (this task)

| Item | Status |
|------|--------|
| todo-smoke-003 IsProjectMember baseline behavior corrected | Done |
| TagViewSet constraint corrected | Done |
| todo.yaml artifact_catalog paths corrected (no todo_project/) | Done |
| Source descriptions corrected to actual baseline | Done |
| artifact_universe.included replaced with exact verified list | Done |
| artifact_universe.excluded replaced with policy exclusions | Done |
| Data-truth tests strengthened | Done |
| PROJECT_HANDOFF corrected to reflect dirty state | Done |

**Remaining for V2 complete:**
- Production strategies still not corrected
- Production-path scripted proof not run
- Evaluator and production-path work incomplete
- Kaggle unauthorized
- Pilot unauthorized
- No stable tag authorized
- Next task after independent approval: V2-02 Safe ArtifactUniverse

**Scope:** Data-contract-only task. No strategies, Runner, Pipeline, LLM backends,
checkpointing, notebooks, or Kaggle execution were modified. Do not claim Smoke
readiness after this task.

## 12. Getting Started

```bash
# Activate environment
conda activate selective-regen-benchmark

# Verify baseline
python -m pytest -q

# Check current state
git log --oneline -3
git status

# Run contract tests
python -m pytest tests/contract/test_three_arm_core.py -v

# Dry-run with canonical profile (use --dry-run without deprecated config file)
python seven_arm_benchmark.py --dry-run

# Rebuild Kaggle bundle (not yet authorized)
# python scripts/build_upload_bundle.py
```

---

**THREE_ARM_CORE_EXPERIMENT_RECOVERED**
