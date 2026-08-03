# Start Here — New Session Entry Point

## Context

You are resuming work on the Dependency-Aware Selective Regeneration Benchmark.

**Current state:** R4 (token limits and truthful workflow metrics) is **ACCEPTED AND FROZEN** at `f5ae826`; R5 (nine non-dry scripted production records) is **ACCEPTED AND FROZEN** by the independent re-audit at `7761c48` on 2026-08-01 (recorded in `docs/R5_FINAL_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md`). R6 (deployment closure) is **ACCEPTED AND FROZEN** by the final independent re-audit (GPT-5.6 Thinking, 2026-08-01, HEAD `949e9c2`), recorded in `docs/R6_FINAL_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md`. The R6 freeze commit `4b2dd27` is the exact first publication HEAD; the milestone branch is **published** with upstream `origin/experiment/three-arm-smoke-v2` and local/remote equality was verified. Post-R6: **two real Kaggle attempts failed pre-model** (`exp-20260801-024041`, `exp-20260801-024624`; both 0 model calls; preserved, not deleted). The real runtime blockers were closed and pinned on branch `fix/kaggle-smoke-v2-runtime-blockers` (fix commit `de3163f`, bundle pin `fb60972`); the R7A hardening closed the four independently reproduced findings (`d50e89e` + `4c73db6`). A subsequent real attempt reached 81 model calls / 47,694 tokens but produced 0 succeeded / 0 regenerated files. The **R7B Smoke Finish** (branch `fix/kaggle-smoke-v2-finish`, commits `bff0a82` + `17207bf`) makes the Qwen Smoke run observable and executable (strict JSON normalization, CUDA cleanup after every generation, live progress + ETA + dashboard artifacts, smoke-only 1024 cap, notebook live-run rewrite with `kaggle_console.log`). **R7C real-run root closure** (branch `fix/kaggle-smoke-v2-real-run-root`, `7a80e53` + `f01b8f0`) closed the four root contracts the FP16/deps-drift attempt exposed; the prior R7C report incorrectly called a 1,451-test subset the full suite (true first full suite = 23 failed / 1,759 passed / 32 skipped; root cause = blanket `baseline_validation => infrastructure_nonrepairable`); the independent GPT-5.6 Thinking correction (`ffa179a` + `6d6aa36`, HEAD `6d6aa36`, pushed) makes the exact 23 former failures pass and corrects DRF import mapping, exact version verification, fail-fast preflight, driver-level VRAM, CPU-offload rejection, the Python 3.12 runtime contract, and stale source identity. Current full gate = **1,790 passed / 32 skipped / 0 failed**. Local scripted records = 9/9; bundled CLI dry-run = 9/9; real Qwen records = 0/9; tag not created; Pilot not authorized. Next: **independent full-gate audit of the corrected R7C branch**; do not relaunch Kaggle before that. All required reading is repository-contained; external prompt packages are historical provenance only and are not required to continue. An independent post-gate audit on `5e47a1e` then found (a) the project-local `ImportError` was incorrectly bypassing repair, (b) the bundled preflight could not import `benchmark` without ambient `PYTHONPATH`, and (c) preflight output was buffered; its exact correction (`6f88823` + `5797fc0`, HEAD `5797fc0`, pushed) makes project-local `ModuleNotFoundError`/`cannot import name` repairable (missing declared Django + CUDA OOM stay `infrastructure_nonrepairable`), bootstraps the bundled script's own `src/`, and streams/persists preflight output. Notebook source identity = `SOURCE_COMMIT 6f88823` / `DEPLOYED_BUILD_ID 6f88823`. Current full gate = 1,796 passed / 32 skipped / 0 failed; valid real Qwen remains 0/9; no scientific evidence exists; Kaggle remains blocked pending the final independent full-gate audit, after which only the engineering preflight cell is authorized (not the scientific One-Run cell). The **pre-benchmark final reproducibility closure** (branch fix/kaggle-smoke-v2-model-output-closure) then declared the complete pre-benchmark dependencies (769d84e + e5d9430), recreated the clean environment from declarations only, and repeated the complete clean gate. The previous 76a6b16 gate had 1 failure, not a green full suite (1,833 passed / 32 skipped / 1 failed; sole failure = the notebook-pin identity test, structural - root cause: dependency declarations changing pyproject.toml after the aac9914/311e084 deployment pin; no runtime/prompt/metric/scenario/evaluator/data change needed; not forced green). The exact deployment-only correction f8d00d7 (bundle fast-forward, exactly one commit) re-pins the deployment (SOURCE_COMMIT=e5d9430, DEPLOYED_BUILD_ID=e5d9430, bundled pyproject.toml byte-identical to canonical); the complete clean suite is now green: 1,834 passed / 32 skipped / 0 failed; historical exp-20260801-210443 produced one failed model-output terminal record under 6f88823 (preserved, excluded from the current e5d9430 aggregation); current accepted real records = 0/9. **POST-SMOKE CALIBRATION CLOSURE (2026-08-03): four proven calibration control defects closed on branch fix/kaggle-smoke-v2-model-output-closure — (A) per-attempt atomic regeneration (zero writes on any guard failure), (B) repair no-progress detection (`repair_no_progress` early-stop on identical repair hash), (C) fail-closed calibration continuation gate (`AUTHORIZE_CONTINUOUS_AFTER_CALIBRATION_REVIEW = False`), (D) cooperative deadline semantics (`scientific_budget_exhausted` scientific terminal; preflight/env/HF timeouts remain engineering blockers). Commits `27c1693` (runtime + tests) + `56772fe` (deployment pin `SOURCE_COMMIT=27c1693e22b1a68be0b299fb146d9ff1e500908b` / `DEPLOYED_BUILD_ID=27c1693`, bundle rebuilt) + `231b0a5` (test-fixture reconciliation: the nine first full-gate failures were stale constant-output fixtures activating the new no-progress contract, not validly proven pre-existing; all max-attempt/repair-count/duration/token/JSONL expectations preserved; side-by-side no-progress-vs-max-attempt boundary test added). Final gate: full suite = 1,849 passed / 32 skipped / 0 failed; mypy strict Success (77 files); ruff 93 = 93 baseline (0 new); bundle content-identical (147 files / 934,495 bytes); all notebook cells compile; tree clean; local = remote = 231b0a5. Calibration evidence `exp-20260803-002741` = 9 terminal records / 0 succeeded / 8 failed / 1 timed_out / 81 model calls / 118,211 tokens — preserved, not accepted scientific evidence; latest real calibration = 0/9; no Kaggle rerun; no tag; Pilot not authorized; next action = one selective calibration canary only after independent audit (sentinel POST_SMOKE_CALIBRATION_CLOSURE_AUDIT_REQUIRED).**

**Phase state:**
```text
R4 = accepted and frozen (explicit freeze commit f5ae826)
R5 = accepted and frozen (independent re-audit 2026-08-01 at 7761c48)
R6 = ACCEPTED AND FROZEN (independent re-audit 2026-08-01 at 949e9c2; freeze commit 4b2dd27)
Kaggle attempts = 2 (exp-20260801-024041, exp-20260801-024624) — failed pre-model, preserved
Latest real attempt = exp-20260801-123125 (FP16 → OOM; deps drifted) — not scientific evidence
Runtime fixes = committed (de3163f) and pinned (fb60972)
R7A hardening = complete (d50e89e + 4c73db6)
R7B Smoke Finish = complete (bff0a82 + 17207bf)
R7C root closure = complete (7a80e53 + f01b8f0) + correction imported (ffa179a + 6d6aa36, HEAD 6d6aa36)
R7C root closure = complete (7a80e53 + f01b8f0) + correction imported (ffa179a + 6d6aa36) + post-gate correction imported (6f88823 + 5797fc0, HEAD 5797fc0, pushed)
Full-gate truth = prior "1,451 full suite" was a SUBSET; true first full suite 23 failed / 1,759 passed / 32 skipped; after correction 1,790 passed / 32 skipped / 0 failed; after post-gate correction 1,796 passed / 32 skipped / 0 failed
Deterministic interpreter closure = complete (aac9914 + 311e084) — bare interpreter tokens bound to active runtime
Pre-benchmark reproducibility closure = COMPLETE AND GREEN (769d84e + e5d9430 declarations; deployment-only correction f8d00d7, HEAD f8d00d7, pushed) — deps fully declared; clean env recreated from declarations only; previous 76a6b16 gate = 1,833 passed / 32 skipped / 1 failed (structural notebook-pin identity test, truthful, not forced green); f8d00d7 re-pins deployment (SOURCE_COMMIT=e5d9430, DEPLOYED_BUILD_ID=e5d9430); complete clean suite then 1,834 passed / 32 skipped / 0 failed; Dataset 285/5 (data unchanged), Prompt 158, Pipeline Smoke 220/12, Dry Run 9/9, Integration PASS, Metric Verification 169; mypy strict Success (77 files); ruff 93 = 93 baseline (0 new)
POST-SMOKE calibration closure = COMPLETE (27c1693 runtime+tests + 56772fe deployment pin + 231b0a5 reconciliation; HEAD 231b0a5, pushed, tree clean) — Closures A/B/C/D closed; 9 first-gate failures = stale constant-output fixtures, reconciled without changing expectations; complete suite now 1,849 passed / 32 skipped / 0 failed; mypy strict Success (77 files); ruff 93 = 93 baseline (0 new); bundle content-identical (147 files / 934,495 bytes); calibration evidence exp-20260803-002741 = 9 records / 0 succeeded / 8 failed / 1 timed_out / 81 calls / 118,211 tokens (preserved, not accepted scientific evidence); latest real calibration = 0/9; no Kaggle rerun; sentinel POST_SMOKE_CALIBRATION_CLOSURE_AUDIT_REQUIRED
Historical experiment = exp-20260801-210443 produced ONE failed model-output terminal record under 6f88823 — preserved, excluded from current e5d9430 aggregation
Current real records = 0/9
Pilot = not authorized
push = PUBLISHED — upstream origin/fix/kaggle-smoke-v2-model-output-closure, local/remote equal
stable tag = blocked
```

---

## Quick Start

```bash
# Activate environment
conda activate selective-regen-benchmark

# Verify
python --version && pip check

# Run tests
python -m pytest -q

# Show current state
git status
git log --oneline -3

# Run the canonical Scientific Smoke V2 profile dry-run
python seven_arm_benchmark.py --dry-run
```

---

## R5 Acceptance and R6 Freeze

R5 was accepted and frozen by the independent re-audit on 2026-08-01 at HEAD `7761c48`. The clean R5 tail is `8fafb50`, `a24a9cd`, `875e4d1`, `ee148fa`, `7761c48`. R6 deployment closure was executed under the corrected directive and supersedes every earlier R6 prompt/directive: deterministic bundle builder, controlled Todo test deployment, exact evaluator allowlist, valid V2 smoke config, pinned notebook, bundle preflight integration, and manifest parity audits (0/0/0). The bounded final correction added the bundled CLI dry-run regression test (`40c7a47`) and closed documentation-truth defects D1–D6. The final independent re-audit (GPT-5.6 Thinking, 2026-08-01, HEAD `949e9c2`) **accepted R6 and authorized freeze and milestone-branch publication**. R6 is now **ACCEPTED AND FROZEN** and the milestone branch is **published** (freeze commit `4b2dd27`, upstream `origin/experiment/three-arm-smoke-v2`, local/remote equality verified). Next: Kaggle environment preflight.

```text
R5 = accepted and frozen at 7761c48
R6 = ACCEPTED AND FROZEN at 949e9c2 (freeze commit 4b2dd27)
Kaggle = not launched
push = PUBLISHED (upstream set, local/remote equal)
tag = blocked
Pilot = not authorized
```

---

## Pre-Change Reading Order

Before modifying production code, benchmark data, notebooks, or deployment bundles, read:

1. `selective_updates/README.md` — ledger purpose and conventions
2. `selective_updates/CHANGE_INDEX.md` — recent changes and status
3. `selective_updates/ARTIFACT_IMPACT_MAP.md` — change-to-artifact lookup

---

## Key Documents

| Document | Purpose |
|----------|---------|
| `docs/PROJECT_HANDOFF.md` | Full project handoff (read first) |
| `docs/R6_FINAL_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md` | R6 acceptance and freeze record (read for current R6 state) |
| `docs/R6_INDEPENDENT_AUDIT_AND_CORRECTION_REPORT.md` | R6 independent audit + final correction record (historical) |
| `docs/R5_FINAL_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md` | R5 acceptance and freeze record |
| `selective_updates/records/R6-BUNDLE-PARITY-AND-PRE-KAGGLE-HANDOFF.md` | R6 bundle parity and pre-Kaggle handoff record |
| `reports/latest_phase_report.md` | Current R6 phase report (latest-first) |
| `SYSTEM_STATE.md` | Current system state |
| `TODO.md` | Task list |
| `DECISION_LOG.md` | Decision history |
| `reports/PROJECT_HEALTH_REPORT.md` | Project health dashboard |
| `selective_updates/records/R5-INDEPENDENT-AUDIT-SCOPE-CORRECTION.md` | R5 scope correction and evidence record |

---

## Three Scientific Smoke V2 Arms (Frozen)

| Role | Legacy ID | Scope Determination | Model Calls |
|------|-----------|-------------------|-------------|
| full_scope_reference | monolithic | All eligible source artifacts | 1 per artifact |
| dependency_aware_selective | selective | Repository graph + anchors + BFS | 1 per selected artifact |
| repository_agent | iterative_repository_agent | Bounded LLM loop (list/read/search) | ≤8 total |

### Changes

1. **todo-smoke-001** (localized) — Add Task priority with low/medium/high and default medium
2. **todo-smoke-002** (cross-layer) — Add Task soft deletion with deleted_at, restore endpoint
3. **todo-smoke-003** (cross-cutting) — Only Project owner may modify tasks in that Project

Each starts from the same clean pinned baseline (b8a33e2). They are not cumulative.

---

## Golden Rules

1. **No local LLM inference** — no torch/transformers locally
2. **No modifying frozen protocol documents** (8 docs under `docs/`)
3. **No modifying `inputs/`** — immutable external data
4. **Smoke evidence is non-publication** — do not cite
5. **Canonical project root is `project/`** (where `.git` lives)
6. **Failed runs must remain visible** — no deletion
7. **Commit code before any execution run** — tag for traceability
8. **All production changes require selective-update ledger entry**

---

## Next Task

**PRE-BENCHMARK FINAL SOURCE REPIN - DEPLOYMENT CORRECTION APPLIED, COMPLETE CLEAN SUITE GREEN.** The pre-benchmark reproducibility-and-truth closure on branch `fix/kaggle-smoke-v2-model-output-closure` declared the complete pre-benchmark test environment in `pyproject.toml [dev]` + `requirements-dev.txt` (commits `769d84e` + `e5d9430`; runtime `[project.dependencies]` and `requirements-smoke-kaggle.lock` untouched), recreated the clean environment from declarations only (Python 3.11.9), and repeated the complete clean gate. The previous `76a6b16` gate had **1 failure, not a green full suite** (1,833 passed / 32 skipped / 1 failed) - the sole failure was `test_notebook_source_commit_matches_deployed_runtime_tree`, structural because the mandated `pyproject.toml` declaration change broke byte-identity with the pinned `aac9914` SOURCE_COMMIT (root cause = dependency declarations changing `pyproject.toml` after the `aac9914`/`311e084` deployment pin; frozen artifacts were not modified to force green and the truthful total is recorded; **no runtime, prompt, metric, scenario, evaluator, or data change was needed**). The exact independently reviewed deployment-only correction `f8d00d7` (imported via bundle fast-forward, exactly one commit) re-pins the deployment to the current source snapshot: bundled `pyproject.toml` byte-identical to canonical, notebooks re-pin `SOURCE_COMMIT = e5d943065c6f4158c30a1cbbba39436ab2a7a898` / `DEPLOYED_BUILD_ID = e5d9430` (deployment source snapshot = `e5d9430`; deployment correction = `f8d00d7`). The complete clean gate is now **green: 1,834 passed / 32 skipped / 0 failed**; Dataset Validation 285 passed / 5 skipped (data unchanged); Prompt Validation 158 passed; Pipeline Smoke 220 passed / 12 skipped; Dry Run 9/9; Integration PASS; Metric Verification 169 passed; mypy strict Success (77 files); ruff 93 = 93 baseline (0 new); compileall clean; all notebook code cells compile; bundle build content-identical (147 files / 928,329 bytes); no cache files in `kaggle_upload`. Historical `exp-20260801-210443` produced one failed model-output terminal record under source `6f88823` - preserved, excluded from the current `e5d9430` aggregation; current accepted real records = **0/9**; no scientific evidence; no tag; no Pilot; no Kaggle launch. Record: `selective_updates/records/KAGGLE-SMOKE-V2-MODEL-OUTPUT-CLOSURE.md`. Next: the only action after this independent audit is the **Kaggle engineering preflight** cell (not the scientific One-Run cell) - first update the Kaggle code dataset + notebook to the corrected `e5d9430` deployment. Do not relaunch Kaggle, tag, merge, or force-push beyond that documented preflight step.

---

## If You Get Lost

```bash
# List all state files
ls SYSTEM_STATE.md TODO.md DECISION_LOG.md

# Show recent git history
git log --oneline -10

# Show tags
git tag -l 'v0.*'

# Read handoff
cat docs/PROJECT_HANDOFF.md

# Read R4 freeze record
cat docs/R4_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md

# Read R5 freeze record
cat docs/R5_FINAL_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md

# Read R6 final acceptance and freeze record
cat docs/R6_FINAL_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md

# Read R6 independent audit and final correction record
cat docs/R6_INDEPENDENT_AUDIT_AND_CORRECTION_REPORT.md

# Read R5 scope correction record
cat selective_updates/records/R5-INDEPENDENT-AUDIT-SCOPE-CORRECTION.md

# Read R6 bundle parity and pre-Kaggle handoff record
cat selective_updates/records/R6-BUNDLE-PARITY-AND-PRE-KAGGLE-HANDOFF.md

# Read Kaggle runtime fix record
cat selective_updates/records/KAGGLE-SMOKE-V2-RUNTIME-FIX.md

# Read R7A hardening record
cat selective_updates/records/KAGGLE-SMOKE-V2-RUNTIME-HARDENING.md

# Read R7B Smoke Finish record
cat selective_updates/records/KAGGLE-SMOKE-V2-FINISH.md

# Read pre-benchmark final reproducibility audit closure record
cat selective_updates/records/KAGGLE-SMOKE-V2-MODEL-OUTPUT-CLOSURE.md
```

---

PRE_BENCHMARK_FINAL_SOURCE_REPIN_AUDIT_REQUIRED
