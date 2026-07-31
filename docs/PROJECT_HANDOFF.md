# Project Handoff — Dependency-Aware Selective Regeneration Benchmark

**Handoff Date:** 2026-08-01
**Prepared by:** OpenCode (engineering assistant)
**Handoff to:** Human researcher (subsequent sessions)
**Handoff type:** R4 ACCEPTED AND FROZEN (explicit freeze commit f5ae826) — R5 ACCEPTED AND FROZEN (independent re-audit 2026-08-01 at 7761c48) — R6 AUTHORIZED AND IN PROGRESS — branch experiment/three-arm-smoke-v2; R6 deployment closure follows the corrected directive in ..\R6_OpenCode_Package_CORRECTED\ (supersedes all earlier R6 directives); Kaggle/push/tag/merge/Pilot = BLOCKED

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
- **R3D code-checkpoint:** 9e28790 (fix(validation): complete R3D scientific wiring contract)
- **R3D final-evidence-checkpoint:** 11f88f5 (fix(validation): close final R3D evidence gaps)
- **R3D docs-checkpoint:** e61eb9a (docs(state): record R3D completion pending audit)
- **R4 code-checkpoint:** e87d4ad (fix(metrics): separate per-call limits and workflow totals)
- **R4 audit-correction commits:** c928bd9 (fix(validation): pin evaluator assets to canonical LF), cc32b17 (fix(metrics): preserve exhausted workflow token budgets), a46213c (docs(audit): record R4 audit corrections)
- **R4 freeze:** f5ae826 — ACCEPTED AND FROZEN by independent re-audit (GPT-5.6 Thinking, 2026-07-31); commit `a46213c` recorded the R4 audit corrections, `f5ae826` is the explicit acceptance/freeze commit
- **R5 benchmark correction:** 8fafb50 (fix(validation): reconcile Smoke V2 baseline contracts) — pre-results amendment R5-BASELINE-CONTRACT-001, no Smoke V2 record existed
- **R5 amendment docs:** a24a9cd (docs(protocol): record pre-results Smoke V2 baseline amendment)
- **R5 execution fix:** 875e4d1 (fix(execution): preserve generated file bytes on Windows) — exactly 2 files
- **R5 test proof:** ee148fa (test(smoke): prove nine scripted production records) — exactly 3 files
- **R5 audit docs commit:** this commit (docs(audit): accept and freeze R5 production path proof) — documentation only
- **R5 acceptance/freeze:** ACCEPTED AND FROZEN by independent re-audit (GPT-5.6 Thinking, 2026-08-01) at 7761c48; recorded in docs/R5_FINAL_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md
- **HEAD:** this commit (R5 accepted and frozen; R6 authorized/in progress)
- **Working tree:** clean
- **Canonical V2 profile source:** PROFILES["scientific-smoke-v2"] in seven_arm_benchmark.py
- **Test suite:** (final full-suite result recorded in this commit's docs) — 1,625 passed / 32 skipped / 0 failed
- **Lint:** ruff 0 new findings vs backup branch
- **Types:** mypy strict 0 new errors vs backup branch
- **Dependencies:** pip check clean
- **Benchmark data:** 3 repositories (todo, djangocms, saleor), 24 protocol scenarios + 3 smoke scenarios
- **Kaggle status:** BLOCKED — not authorized
- **Pilot status:** BLOCKED — not authorized
- **R5 status:** ACCEPTED AND FROZEN at 7761c48 (nine non-dry scripted production records = 9/9)
- **R6 status:** AUTHORIZED / IN PROGRESS — deployment closure
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
| R3D — production Runner validation wiring | ACCEPTED | 1478 full suite; R4 depends on it |
| R4 — token limits and truthful workflow metrics | ACCEPTED AND FROZEN at a46213c | Independent re-audit accepted on 2026-07-31; two defects closed (exact exhaustion, evaluator LF pinning) |
| RF-3 — token/metric refactor | COMPLETE | Delivered inside R4 |
| RF-4 — full technical debt cleanup | SCHEDULED | R5 scoped RF-4 checks passed (no R5 code change required); full cleanup remains for R6 window |
| **R5 — nine non-dry scripted production records** | **CORRECTION COMPLETE — PENDING INDEPENDENT RE-AUDIT** | Nine records all succeeded; scripted engineering proof only; scope correction rebuilt the local tail without the accidental 6650b00 Kaggle bundle content; R5_SCOPE_CLEANUP_REAUDIT_REQUIRED |
| **Execute Scientific Smoke V2 on Kaggle** | HIGH | Unauthorized — blocked until R6 complete |
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
R3D code:                    9e28790 (fix(validation): complete R3D scientific wiring contract)
R3D docs:                    e61eb9a (docs(state): record R3D completion pending audit)
R3D final evidence:          11f88f5 (fix(validation): close final R3D evidence gaps)
R4 code:                     e87d4ad (fix(metrics): separate per-call limits and workflow totals)
R4 audit corrections:        c928bd9 (.gitattributes), cc32b17 (production + tests), a46213c (docs)
R4 freeze:                   f5ae826 (ACCEPTED AND FROZEN — independent re-audit 2026-07-31)
R5 benchmark correction:     8fafb50 (fix(validation): reconcile Smoke V2 baseline contracts)
R5 amendment docs:           a24a9cd (docs(protocol): record pre-results Smoke V2 baseline amendment)
R5 execution fix:            875e4d1 (fix(execution): preserve generated file bytes on Windows) — 2 files
R5 test proof:               ee148fa (test(smoke): prove nine scripted production records) — 3 files
R5 audit docs commit:        docs(audit): record R5 completion pending re-audit (this commit, docs only)
HEAD:                        this commit (docs(audit): record R5 completion pending re-audit)
Local/remote:         not yet pushed
Working tree:         clean
Tags:            v0.7.0-smoke-passed at 0c58250 (unchanged)
Stash:           broken methodology-conformance WIP 2026-07-27
Kaggle:          blocked
Pilot:           blocked
R6:              blocked
README:          intentionally deferred to R6
```

> Note: the original R5 tail (6650b00, 88b6f84, c3ecad2) was rebuilt because
> `6650b00` accidentally committed 31 premature `kaggle_upload/` derivative
> files and introduced a committed notebook-manifest mismatch. The final R5
> branch contains no `kaggle_upload` diff from `f5ae826`. The pre-rebuild state
> is preserved on `backup/r5-pre-audit-c3ecad2`. See
> `selective_updates/records/R5-INDEPENDENT-AUDIT-SCOPE-CORRECTION.md` and
> `..\R5_INDEPENDENT_AUDIT_SCOPE_AND_EVIDENCE_2026-07-31.md`.

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

- R3D: FINAL FREEZE CANDIDATE — code committed (11f88f5); independent audit pending
- RF-2: part of R3D correction; complete
- RF-3: scheduled after R4
- RF-4: scheduled after R5
- Kaggle/Pilot/merge/tag: BLOCKED

---

## 15. R3D Status — Production Runner Validation Wiring

**Status:** R3D FINAL FREEZE CANDIDATE — INDEPENDENT AUDIT REQUIRED
**Code checkpoints:** `9e28790` (root correction), `11f88f5` (final evidence closure)
**Date:** 2026-07-31

### What was built

- **`_validate_scientific_configuration`** — preflight check for canonical_project_root, python_executable, evaluator_asset, validation_command before any model call
- **`_execute_scientific_validation`** — orchestrates post-generation migration, baseline validation, and scenario evaluator; returns `_ScientificValidationResult` with per-stage bounded outputs
- **`_scientific_record_fields`** — maps validation result to RunRecord dict; gracefully handles None
- **`_failure_from_scientific_result`** — converts failed result into FailureRecord with correct stage/kind
- **`_scientific_feedback_channels`** — produces (exit_code, stdout, stderr) bounded at 1000 chars per channel; evaluator branch includes stderr + error + public check names
- **`_is_repairable_failure`** — gating: migration, evaluator, and generation_guard are repairable; pre-flight/config failures are not
- **RF-2 deduplication** — single enforcement point in `_validate_scientific_configuration`; pre-flight and late duplicate checks removed from seven_arm_benchmark.py and runner.py
- **`selection_tool_transcript`** — preserved in both success/failure return paths and reporting serializer

### RF-2 (Orchestration Deduplication)

Single enforcement point: `_validate_scientific_configuration` in runner.py. Pre-flight `validation_command` check removed from `seven_arm_benchmark.py`. Duplicate late checks removed from `_run_regeneration_flow` and `_run_iterative_flow`.

### Final evidence closure (11f88f5)

- Evaluator stderr channel: constructed from `evaluator.stderr`, `evaluator.error`, and `checks`; bounded at 1000 chars; no evaluator source, Ground Truth, or hidden descriptions
- 7 public-path tests replace 5 prior nominal tests: entry config, monolithic migration repair, selective evaluator repair, agent evaluator revision + transcript, feedback channel content, duration aggregation, record round-trip
- Truthful Git-derived report at `reports/latest_phase_report.md` (2269 words)

### Quality gates

- Full suite: 1478 passed, 32 skipped, 0 failed
- 54 focused R3D wiring tests (7 public-path, 18 private-helper, 7 persistence, 1 reporting)
- Ruff: 0 errors on changed files
- Mypy strict: 0 errors on changed production files
- Compileall: all OK
- Git tree: clean
- Commit separation: code (9e28790) → docs (e61eb9a) → final evidence (11f88f5)

### Blocked

- R3D freeze: blocks R4 (truthful metrics), R5 (nine local records), R6 (bundle and push), Kaggle execution, Pilot

---

## 16. R4 Status — Token Limits and Truthful Workflow Metrics

**Status:** R4 ACCEPTED AND FROZEN — independent re-audit by GPT-5.6 Thinking on 2026-07-31 accepted the audit corrections and froze R4 for progression to R5
**Starting HEAD:** `b8724cc`
**Code commit:** `e87d4ad` — `fix(metrics): separate per-call limits and workflow totals`
**Audit-correction commits:** `c928bd9` — `fix(validation): pin evaluator assets to canonical LF`; `cc32b17` — `fix(metrics): preserve exhausted workflow token budgets`
**Freeze HEAD:** `f5ae826` (explicit acceptance/freeze commit; `a46213c` recorded the audit corrections)
**Date:** 2026-07-31

### What was built

- **Single allowance resolver** — `budgets.resolve_completion_allowance(*, max_completion_tokens_per_call, remaining_total_workflow_tokens, prompt_tokens)`; zero total → per-call limit; otherwise `max(0, min(per_call, remaining − prompt))`.
- **Frozen conflict rule at every constructor** — `PipelineConfig`, `RunnerConfig`, `ExecutionConfig`: both zero → unlimited; one positive → it; both positive equal → it; both positive different → constructor-time `ValueError`.
- **Stage-split truthful metrics** — `_WorkflowMetricAccumulator` tracks selection / initial regeneration / repair / migration / baseline / evaluator separately; `total_workflow_*` equals the exact stage sum; `repair_attempts` increments once per repair executor call.
- **Executor/Agent limit separation** — executor `SharedRegenerationExecutor.execute(..., max_completion_tokens_per_call, remaining_total_workflow_tokens)`; agent `analyze_impact`/`revise_plan` use explicit per-call + remaining-total; `MAX_AGENT_CALLS = 8`.
- **Resolved total forwarded everywhere** — `seven_arm_benchmark.py` `record_dict` carries `max_completion_tokens_per_call`/`max_total_workflow_tokens`; `_to_run_record_data` forwards them plus `max_attempts` into `model_metadata`; survives JSONL reload and report.
- **Real test evidence** — `test_r4_token_and_metrics.py` (66 tests), `test_r4_metric_contract.py` (31 tests); zero `assert True`.

### Audit corrections (2026-07-31)

- **Defect A** — exact workflow-budget exhaustion reopened an exhausted budget as unlimited because `0` was overloaded as both "no limit" and "exhausted". Fixed by `budgets.runtime_remaining_total_tokens` (`None` = unlimited, `0` = exhausted, positive = remaining) and `int | None` semantics in `resolve_completion_allowance`, executor, and agent, with `has_limit` accounting guards; all five Runner call sites forward the runtime allowance. Five-group exact-exhaustion regression + integration production-path tests added.
- **Defect B** — evaluator integrity was platform-dependent: committed `.sha256` are canonical LF but Windows checkout produced CRLF. `.gitattributes` pins `tests/evaluator_assets/todo_smoke_*_checks.py` to `text eol=lf`; worktree rewritten to canonical LF, SHA-256 still matches the committed `.sha256`, index/worktree byte-identical.

### Quality gates

- 9.1 R4 unit: 66 passed; 9.2 R4 integration: 31 passed; 9.3 R3D-adjacent: 177 passed; 9.4 evaluator integrity: 50 passed, 1 pre-existing skip
- Full suite: 1576 passed, 32 skipped, 0 failed
- Ruff: 0 new errors (pre-existing tracked-file findings verified vs HEAD worktree)
- Mypy --strict: 0 new errors (10 pre-existing in seven_arm_benchmark.py, verified vs HEAD worktree)
- Compileall: exit 0; `git diff --check`: clean
- Direct scripts A/B/C1/C2/D all met §7 acceptance; Script D showed 2048/9000 at all five boundaries
- Code commit `e87d4ad`: 21 files, 3052 insertions, 307 deletions (14 production + 7 tests)

### Audit-correction gates (2026-07-31)

- R4 unit: 72 passed; R4 integration: 33 passed; R3D-adjacent (r3d_wiring + repair): 62 passed; evaluator integrity: 50 passed, 1 pre-existing skip; full suite: 1584 passed, 32 skipped, 0 failed
- Ruff: 88 findings = baseline `ccdb49c` (0 new); Mypy --strict on the 4 changed production files: 0 errors; compileall: exit 0; `git diff --check`: clean
- Defect B proven: worktree SHA-256 matches committed `.sha256` for all three evaluator files; index/worktree blobs byte-identical; zero CR bytes; `git ls-files --eol` shows `i/lf w/lf`

### Freeze (2026-07-31)

The independent re-audit accepted R4 at the explicit acceptance/freeze commit `f5ae826`. See `docs/R4_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md`.

### Blocked

- R5 freeze: blocks R6 (bundle and push), Kaggle execution, Pilot. R6 remains blocked pending R5 completion and independent audit.
- R5 is in progress; R6 is blocked.

---

**R4_ACCEPTED_R5_SCOPE_CORRECTION_REAUDIT_REQUIRED**

---

## 17. R5 Baseline-Contract Amendment — R5-BASELINE-CONTRACT-001

**Status:** AMENDED AND COMMITTED — R5 RESUMED
**Correction commit:** `8fafb50` — `fix(validation): reconcile Smoke V2 baseline contracts`
**Date:** 2026-07-31

### Trigger

An independent blocker audit (`..\R5_BLOCKER_INDEPENDENT_AUDIT_2026-07-31.md`)
confirmed a data contract contradiction between the frozen baseline regression
assertions and the three frozen Smoke V2 scenarios. R5 was blocked at Step 2
(the first Monolithic cell) at `baseline_validation`. No Smoke V2 record
existed, so the correction is pre-results. Full scope, gate order, and final
marker are defined in `..\OPENCODE_R5_CONTRACT_CORRECTION_AND_RESUME_DIRECTIVE.md`.

### What changed (7 files, production = NONE, scenario YAML = NONE)

- `test_serializers.py`: ProjectSerializer/TaskSerializer field assertions are
  now baseline-field preservation; TagSerializer stays exact.
- `test_views.py`: common project created through the authenticated Project API;
  unowned-task forbidden test creates its project via another user's API client;
  exact HTTP 403 preserved.
- `evaluator_fixture_workspaces.py`: smoke-002 correct-source keys exactly
  `todo/models.py` + `todo/views.py`.
- `todo_smoke_002_checks.py` + `.sha256`: removed only the unstated
  `deleted_at`-response-field loop; canonical LF SHA-256 recomputed.
- `test_todo_smoke_evaluator_assets.py`: three-scenario correct-fixture
  compatibility gate (`test_correct_fixture_passes_baseline_and_evaluator_*`).
- `repository_versions.yaml`: Todo notes record the amendment; pinned SHA unchanged.

### Evidence

- Baseline repository suite: 47 passed.
- Compatibility gate: 3 scenarios passed (baseline + evaluator + one migration +
  unchanged old migrations + exact changed-source paths + unchanged baseline tests
  + no evaluator assets in workspace).
- Complete evaluator suite: 53 passed, 1 pre-existing skip.
- Full suite: 1598 passed, 32 skipped, 0 failed.
- R5 status = RESUMED; R6/Kaggle/push/tag = BLOCKED.

Record: `selective_updates/records/R5-BASELINE-CONTRACT-AMENDMENT.md`.

---

## 18. R5 Scope Correction and Evidence Tightening (2026-07-31)

**Status:** CORRECTION COMPLETE — PENDING INDEPENDENT RE-AUDIT
**Audit source:** `..\R5_INDEPENDENT_AUDIT_SCOPE_AND_EVIDENCE_2026-07-31.md`
**Directive source:** `..\OPENCODE_R5_SCOPE_CLEANUP_DIRECTIVE.md`
**Backup branch:** `backup/r5-pre-audit-c3ecad2` (preserved until re-audit)

An independent audit found the original R5 tail acceptable in production
behavior but mis-scoped in git history: commit `6650b00` claimed one execution
fix while also committing 31 premature `kaggle_upload/` files, introducing a
committed notebook-manifest mismatch. Because the branch had no upstream, the
local R5 tail was rebuilt cleanly:

- `8fafb50` and `a24a9cd` preserved untouched.
- `875e4d1` — rewritten execution fix (exactly 2 files).
- `ee148fa` — rewritten R5 test proof (exactly 3 files).
- This commit — R5 audit documentation only.
- No `kaggle_upload/` change from `f5ae826`; no bundle rebuild; no README
  change; no push; no tag.

Three evidence boundaries were tightened: exact selected/generated path and
count assertions for all nine cells (`generation_paths_requested`,
`selected_artifact_count`, `regeneration_model_calls`,
`regenerated_artifact_count`, `preserved_artifact_count`); the snapshot
mutation control now proves an accepted-hash → mutated-hash transition
(`snapshot_hash_before != snapshot_hash_after`, `record.status == failed`);
and persisted timestamps are captured immediately before/after the real
pipeline run (`started_at <= ended_at`, timezone-aware, all nine records).
Negative-control documentation was corrected: dry-run and no-regeneration are
valid guarded no-op modes; no-new-migration is a failed validation control;
the remaining failure controls fail at their exact intended stage.

The Git-tree bundle-manifest issue is recorded as R6 debt
`TD-R6-BUNDLE-MANIFEST-001` and was not fixed inside R5
(`scripts/build_upload_bundle.py` was not modified). The Git-tree manifest
mismatch counts are reported in
`selective_updates/records/R5-INDEPENDENT-AUDIT-SCOPE-CORRECTION.md`.

Next action: R6 deployment closure under the corrected directive
(`..\R6_OpenCode_Package_CORRECTED\02_OPENCODE_R6_CORRECTED_EXECUTION_DIRECTIVE.md`),
then an independent R6 audit before push. Kaggle, push, tag, merge, and Pilot
remain BLOCKED.

## 19. R5 Acceptance and R6 Authorization (2026-08-01)

**Status:** R5 ACCEPTED AND FROZEN — R6 AUTHORIZED AND IN PROGRESS
**Audit source:** `..\R5_FINAL_INDEPENDENT_REAUDIT_ACCEPTANCE_2026-08-01.md`
**Directive source:** `..\R6_OpenCode_Package_CORRECTED\02_OPENCODE_R6_CORRECTED_EXECUTION_DIRECTIVE.md` (supersedes every earlier R6 directive)
**Backup branch:** `backup/r6-pre-execution-7761c48` (created 2026-08-01; no tag)

The independent re-audit accepted and froze R5 at `7761c48` on 2026-08-01.
Local scripted Smoke V2 evidence = 9/9 records succeeded, 0 failed. Real Qwen
records = 0/9. The R6 corrected plan closes the deployment gaps found by the
audit (TD-R6-BUNDLE-MANIFEST-001, missing controlled Todo tests, missing
evaluator assets, V1 notebook/smoke config, and future-hash identity rules)
with a deterministic builder, an exact evaluator allowlist, controlled Todo
test deployment, a valid V2 smoke config, a pinned notebook, a bundle
preflight integration, and committed-byte manifest parity audits. R6 does not
modify production Runner, strategies, metrics, regeneration, evaluator
behavior, frozen scenarios, evaluator assets, or controlled Todo source/tests.

Next action: complete R6, stop for the independent R6 audit before push.

**R5_ACCEPTED_R6_AUTHORIZED**
