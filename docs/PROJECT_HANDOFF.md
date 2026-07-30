# Project Handoff — Dependency-Aware Selective Regeneration Benchmark

**Handoff Date:** 2026-07-30
**Prepared by:** OpenCode (engineering assistant)
**Handoff to:** Human researcher (subsequent sessions)
**Handoff type:** R3D ROOT CORRECTION — branch experiment/three-arm-smoke-v2, code commit 9e28790 (scientific wiring contract), docs commit (this commit)

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
- **R1 checkpoint:** b129d42 (feat(agent): complete bounded workspace exploration)
- **R2 checkpoint:** 5057e7d (fix(selection): correct R2 selective scope)
- **R3A checkpoint:** 3eaab60 (feat(scenarios): add V2 execution metadata)
- **R3B code-checkpoint:** c11f25e (feat(validation): add deterministic migration runner)
- **R3B correction-checkpoint:** c873d9f (fix(validation): close migration runner safety gaps)
- **R3B final-correction-checkpoint:** c635e42 (fix(validation): reject unsafe migration entries and malformed execution input)
- **R3B acceptance-closure-checkpoint:** f8faa08 (fix(validation): fail on untrusted migration after-state)
- **R3B root-refactor-checkpoint:** f8f95d2 (refactor(validation): model migration execution as trusted states)
- **R3B cross-platform-freeze-checkpoint:** feb5a44 (fix(validation): close cross-platform migration snapshot contract)
- **R3B docs-checkpoint:** 8c588e6 (docs(state): record R3B completion)
- **R3B correction-docs-checkpoint:** 8c588e6
- **R3B final-correction-docs-checkpoint:** 8c588e6
- **R3B root-refactor-docs-checkpoint:** 8c588e6
- **R3B cross-platform-freeze-docs-checkpoint:** 8c588e6
- **R3C functional-checkpoint:** 47e1a05 (test(validation): close R3C freeze evidence gaps) — independently accepted by GPT-5.6 Thinking
- **R3C lint-closure-checkpoint:** 7abec68 (test(validation): close residual R3C lint debt)
- **HEAD:** 7abec68
- **Working tree:** clean
- **Canonical V2 profile source:** PROFILES["scientific-smoke-v2"] in seven_arm_benchmark.py
- **Test suite:** 1424 passed, 32 skipped (60 focused evaluator unit, 51 focused evaluator integration, 9 skipped)
- **Lint:** ruff 0 violations
- **Types:** mypy strict 0 errors
- **Dependencies:** pip check clean
- **Benchmark data:** 3 repositories (todo, djangocms, saleor), 24 protocol scenarios + 3 smoke scenarios
- **Kaggle status:** BLOCKED — not authorized
- **Pilot status:** BLOCKED — not authorized
- **Selective scopes verified:** 001=models,serializers,views | 002=models,views | 003=models,permissions,serializers,views

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
| R3A — scenario execution metadata | COMPLETE | evaluator_asset, post_generation_command, require_new_migration |
| R3B — deterministic post-generation migration runner | ACCEPTED AND FROZEN at feb5a44 | Two final corrections applied: (1) lexical directory symlink rejected before resolve instead of after, (2) valid ordinary created numbered paths preserved as partial evidence when after-state untrusted; 109 focused tests + 12 symlink skipped (121 total), 1424 full suite |
| R3C — isolated scenario evaluator runner and three evaluator scripts | COMPLETE | Functional behavior independently accepted at 47e1a05 by GPT-5.6 Thinking; lint closure at 7abec68 (5 ruff violations fixed); final freeze confirmation pending this documentation audit |
| R3D — production Runner validation wiring | ROOT CORRECTED — audit pending | 54 public-path tests (54 pass), 1478 full suite (32 skip, 0 fail), Ruff/mypy/compileall clean; RF-2 pending |
| RF-3 — token/metric refactor | SCHEDULED after R4 | After R4 self-gates |
| RF-4 — full technical debt cleanup | SCHEDULED after R5 | After R5 nine records |
| **Execute Scientific Smoke V2 on Kaggle** | HIGH | Unauthorized — blocked until R3–R6 complete |
| Audit Smoke V2 results | HIGH | Independent verification before Pilot authorization |
| Integrate Pilot repositories | MEDIUM | ≥5K LOC, permissive license, pinned commit, passing tests |
| Run Pilot profile | MEDIUM | 7+ changes, 3+ repos, agent+selective |
| Merge to main | LOW | After successful Smoke V2 |
| Create stable tag | LOW | Only after real Smoke V2 passes and is audited |

## 9. Git State

```
Current branch:  experiment/three-arm-smoke-v2
R1 checkpoint:   b129d42 (feat(agent): complete bounded workspace exploration)
R2 checkpoint:   5057e7d (fix(selection): correct R2 selective scope)
R3A checkpoint:  3eaab60 (feat(scenarios): add V2 execution metadata)
R3B checkpoint:              c11f25e (feat(validation): add deterministic migration runner)
R3B correction:              c873d9f (fix(validation): close migration runner safety gaps)
R3B final correction:        c635e42 (fix(validation): reject unsafe migration entries and malformed execution input)
R3B acceptance closure:      f8faa08 (fix(validation): fail on untrusted migration after-state)
R3B root refactor:           f8f95d2 (refactor(validation): model migration execution as trusted states)
R3B cross-platform freeze:   feb5a44 (fix(validation): close cross-platform migration snapshot contract)
R3B docs:                    8c588e6 (docs(state): record R3B completion)
R3B acceptance docs:         8c588e6
R3B cross-platform freeze docs: 8c588e6
R3C functional:              47e1a05 (test(validation): close R3C freeze evidence gaps)
R3C lint-closure:            7abec68 (test(validation): close residual R3C lint debt)
HEAD:                        7abec68
Local/remote:         not yet pushed
Working tree:         clean
Tags:            v0.7.0-smoke-passed at 0c58250 (unchanged)
Stash:           broken methodology-conformance WIP 2026-07-27
Kaggle:          blocked
Pilot:           blocked
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

# Run focused Selective tests
python -m pytest tests/unit/selection/test_dependency_scope.py -v

# Verify three verified scopes
python -c "
from tests.unit.selection.test_dependency_scope import *
for n, s in [('001',SCENARIO_001),('002',SCENARIO_002),('003',SCENARIO_003)]:
    print(f'Scenario {n}: {select_dependency_scope(s, FIVE_UNIVERSE, DESCRIPTORS, TODO_GRAPH)}')
"

# Dry-run with canonical profile
python seven_arm_benchmark.py --dry-run

# Rebuild Kaggle bundle (not yet authorized)
# python scripts/build_upload_bundle.py
```

---

## 14. R3C Status — Isolated Scenario Evaluator System

**Status:** R3C FREEZE CLOSURE — DOCUMENTATION CLOSURE AUDIT REQUIRED
**Code checkpoints:** `47e1a05` (functional acceptance), `7abec68` (lint closure)
**Date:** 2026-07-30

### What was built

- `src/benchmark/execution/scenario_evaluator.py` — four-state evaluator (validation, trust, subprocess, payload parsing) with typed result objects
- `tests/support/evaluator_fixture_workspaces.py` — three fixture workspace builders; calls `run_post_generation_command`; one-fault variants derived from correct sources (626 lines)
- `tests/evaluator_assets/todo_smoke_001_checks.py` (10 checks), `_002` (9 checks), `_003` (10 checks) — all use identical fail-closed JSON structure
- `tests/integration/test_todo_smoke_evaluator_assets.py` (20 tests: 12 real subprocess runs + 8 integrity including baseline hashes, migration integrity, source isolation)
- `tests/unit/execution/test_scenario_evaluator.py` (57 tests: public-path truth table, symlink/workspace-leak rejection, subprocess exception coverage, isolation cleanup)

### Closure specifics (2026-07-30)

- TOCTOU tests now validate first, mutate second, then trust-load — proving the validate→mutate→trust transition
- Inode-based regular-file replacement test removed; replaced by content-frozen-at-trust-time proof
- Smoke 003 permission proof now invokes every configured permission class via `SimpleNamespace` and `TaskViewSet()`, not just checks class membership
- Source-isolation Boolean logic corrected: buggy `not exists() or not is_symlink()` replaced with `_assert_workspace_has_no_evaluator_assets` helper using AND logic
- 6 fake-Django lifecycle tests (3 assets × 2 failure modes) persist the setup/teardown JSON contract
- Evaluator hash tests are now read-only: metadata required to exist, never written
- Code/docs commit separation enforced: `test(validation)` commit contains code/tests only

### Quality gates

- Full suite: 1424 passed, 32 skipped, 0 failed
- Ruff: 0 errors (5 pre-existing violations in test_scenario_evaluator.py closed in lint-closure commit)
- R3B frozen files untouched
- R3C functional behavior independently accepted by GPT-5.6 Thinking at code checkpoint 47e1a05
- R3C lint debt closed (5 violations: 1 F841, 3 SIM117, 1 E501)
- Git tree: clean (after docs commit)

### Blocked

- R3D: CORRECTION APPLIED — code committed (9e28790);獨立 audit pending
- RF-2: part of R3D correction; completed code-side, pending audit pass
- RF-3: scheduled after R4
- RF-4: scheduled after R5
- Kaggle/Pilot/merge/tag: BLOCKED

---

**R3D_ROOT_CORRECTION_AUDIT_REQUIRED**
