# THREE-ARM-CORE-EXPERIMENT — Scientific Smoke V2: Three-Arm Core Experiment

**Date:** 2026-07-27
**Status:** FROZEN
**Branch:** experiment/three-arm-smoke-v2
**Base Commit:** 0a1c603 (HEAD of experiment/scientific-smoke-v1 before three-arm freeze)

---

## 1. Correction Record

### 1.1 Reason

The previous methodology-conformance WIP (experiment/scientific-smoke-v1, uncommitted) introduced overfitted tests that encoded Ground Truth expectations — specifically `test_selects_four_intended_localized_artifacts` asserting exact file-set equality before execution. This violated the evaluator-only Ground Truth policy and tuned signal parameters (stop words, AST extraction, thresholds, traceability) to match a single known answer. The WIP broke the full test suite and introduced design complexity that does not serve the core scientific question.

### 1.2 Corrections Applied

| # | Previous (broken) | Corrected |
|---|-------------------|-----------|
| C1 | Methodology conformance tests encoding exact artifact counts per change (test_selects_four_intended_localized_artifacts) | Selection tests verify determinism, non-emptiness, and Ground-Truth-free operation only |
| C2 | Hidden tests under tests/hidden_tests/ collected by default pytest | Evaluator-only assets stored in tests/evaluator_assets/ excluded from normal collection |
| C3 | Stop-word, AST extraction, threshold, and traceability tuning against a single todo-loc-001 answer | Parameter-free or repository-derived defaults; no per-scenario tuning |
| C4 | builder.py, semantic.py, traceability.py selection modules with WIP-level API | Preserved as originally implemented; no Ground-Truth-driven signal tuning |
| C5 | IterativeRepositoryAgentStrategy alias replacing the runner-facing class | Preserved original class name RepositoryAgentStrategy; no aliases |
| C6 | Manual kaggle_upload/code/ edits diverging from canonical source | kaggle_upload regenerated only through scripts/build_upload_bundle.py |
| C7 | db.sqlite3, __pycache__, .pytest_cache artifacts in tracked tree | Excluded via .gitignore; caches cleaned |

### 1.3 Protocol Amendment

Protocol v1.0 remains FROZEN (text unchanged). This record documents:

1. **Three-arm core experiment** (replacing the prior 7-arm scope for Smoke):
   - `full_scope_reference` (legacy ID: monolithic)
   - `dependency_aware_selective` (legacy ID: selective)
   - `repository_agent` (legacy ID: iterative_repository_agent)

2. **Scientific Smoke policy:** One controlled repository, exactly 3 independent changes, exactly 3 core arms, 1 repetition = 9 real runs total.

3. **Pilot policy:** At least 7 changes, at least 3 real repositories, each ≥5,000 LOC, permissive license, pinned commit, passing baseline test suite. Authorized only after real Smoke completes and is audited.

4. **Ground Truth is evaluator-only and post-hoc.** It must never influence ArtifactUniverse, dependency graph, prompts, file selection, agent tools, regeneration, or repair.

---

## 2. Core Scientific Question

> For a given natural-language requirement change, which strategy produces a correct implementation with the fewest unnecessary modifications, lowest token consumption, and fewest model calls?

### Three Confirmatory Arms

| Scientific Role | Legacy ID | How Scope Is Determined | Model Calls per Change |
|-----------------|-----------|------------------------|----------------------|
| full_scope_reference | monolithic | All eligible source artifacts | 1 call per artifact |
| dependency_aware_selective | selective | Repository graph + anchors + BFS | 1 call per selected artifact |
| repository_agent | iterative_repository_agent | Bounded LLM loop (list/read/search) | ≤8 total iterations |

All arms share:
- Same LLM backend
- Same temperature (0.0)
- Same per-call max_tokens (4096)
- Same SharedRegenerationExecutor for writing code
- Same validation pipeline
- Same isolated workspace

---

## 3. Scientific Smoke Policy

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

1. **todo-smoke-001 (localized):** Add Task priority with low/medium/high and default medium.
2. **todo-smoke-002 (cross-layer):** Add Task soft deletion — deleted_at field, exclusion from normal listings, restore endpoint.
3. **todo-smoke-003 (cross-cutting):** Only a Project owner may create, update, or delete Tasks in that Project; unauthorized operations return 403.

Each scenario starts from the same clean pinned baseline (b8a33e2). They are not cumulative.

---

## 4. Pilot Policy

Authorized only after real Smoke completes and passes independent audit.

| Criterion | Requirement |
|-----------|-------------|
| Minimum changes | 7 |
| Minimum repositories | 3 |
| Minimum LOC per repository | 5,000 |
| License | Permissive (MIT, BSD, Apache 2.0) |
| Commit | Pinned exact commit |
| Baseline | Passing reproducible test suite |

---

## 5. Historical Unused Arms

The following arms remain in the codebase as historical artifacts. They are excluded from the three-arm core Smoke:

- `static_only` (compiled_ai) — graph-only ablation
- `semantic_only` (delta_mcp) — semantic-only ablation
- `traceability_only` (incr_rtl) — traceability-only ablation
- `code_plan` — full-context code plan strategy

These are preserved for future ablation studies but not part of the confirmatory Smoke.

---

## 6. Effect on Previous Records

No previous records are modified. This amendment supersedes the methodology-conformance WIP scope defined in the uncommitted changes of experiment/scientific-smoke-v1 (stashed as `broken methodology-conformance WIP 2026-07-27`).

---

## 7. R6 Deployment Closure (2026-08-01)

The three-arm Scientific Smoke V2 deployment is **COMPLETE PENDING INDEPENDENT AUDIT** under the corrected R6 directive. Runtime source commit `cb25e9f`; deployed bundle commit `54a0462`; manifest committed-tree counts 0/0/0; Todo baseline tests deployed = 47 methods; evaluator assets deployed = 3 + 3 fingerprints. Local scripted records = 9/9; real Qwen records = 0/9; Kaggle not launched; push not performed; tag not created; Pilot not authorized. Smoke evidence is non-publication.

R6_DEPLOYMENT_CLOSURE_AUDIT_REQUIRED
