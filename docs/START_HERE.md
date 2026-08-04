# Start Here — New Session Entry Point

## Context

You are resuming work on the Dependency-Aware Selective Regeneration Benchmark.

**Current state:** R4 (token limits and truthful workflow metrics) is **ACCEPTED AND FROZEN** at `f5ae826`; R5 (nine non-dry scripted production records) is **ACCEPTED AND FROZEN** by the independent re-audit at `7761c48` on 2026-08-01 (recorded in `docs/R5_FINAL_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md`). R6 (deployment closure) is **ACCEPTED AND FROZEN** by the final independent re-audit (GPT-5.6 Thinking, 2026-08-01, HEAD `949e9c2`), recorded in `docs/R6_FINAL_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md`. The R6 freeze commit `4b2dd27` is the exact first publication HEAD; the milestone branch is **published** with upstream `origin/experiment/three-arm-smoke-v2` and local/remote equality was verified. Post-R6: **two real Kaggle attempts failed pre-model** (`exp-20260801-024041`, `exp-20260801-024624`; both 0 model calls; preserved, not deleted). The real runtime blockers were closed and pinned on branch `fix/kaggle-smoke-v2-runtime-blockers` (fix commit `de3163f`, bundle pin `fb60972`); the R7A hardening closed the four independently reproduced findings (`d50e89e` + `4c73db6`). A subsequent real attempt reached 81 model calls / 47,694 tokens but produced 0 succeeded / 0 regenerated files. The **R7B Smoke Finish** (branch `fix/kaggle-smoke-v2-finish`, commits `bff0a82` + `17207bf`) makes the Qwen Smoke run observable and executable (strict JSON normalization, CUDA cleanup after every generation, live progress + ETA + dashboard artifacts, smoke-only 1024 cap, notebook live-run rewrite with `kaggle_console.log`). **R7C real-run root closure** (branch `fix/kaggle-smoke-v2-real-run-root`, `7a80e53` + `f01b8f0`) closed the four root contracts the FP16/deps-drift attempt exposed; the prior R7C report incorrectly called a 1,451-test subset the full suite (true first full suite = 23 failed / 1,759 passed / 32 skipped; root cause = blanket `baseline_validation => infrastructure_nonrepairable`); the independent GPT-5.6 Thinking correction (`ffa179a` + `6d6aa36`, HEAD `6d6aa36`, pushed) makes the exact 23 former failures pass and corrects DRF import mapping, exact version verification, fail-fast preflight, driver-level VRAM, CPU-offload rejection, the Python 3.12 runtime contract, and stale source identity. Current full gate = **1,790 passed / 32 skipped / 0 failed**. Local scripted records = 9/9; bundled CLI dry-run = 9/9; real Qwen records = 0/9; tag not created; Pilot not authorized. Next: **independent full-gate audit of the corrected R7C branch**; do not relaunch Kaggle before that. All required reading is repository-contained; external prompt packages are historical provenance only and are not required to continue. An independent post-gate audit on `5e47a1e` then found (a) the project-local `ImportError` was incorrectly bypassing repair, (b) the bundled preflight could not import `benchmark` without ambient `PYTHONPATH`, and (c) preflight output was buffered; its exact correction (`6f88823` + `5797fc0`, HEAD `5797fc0`, pushed) makes project-local `ModuleNotFoundError`/`cannot import name` repairable (missing declared Django + CUDA OOM stay `infrastructure_nonrepairable`), bootstraps the bundled script's own `src/`, and streams/persists preflight output. Notebook source identity = `SOURCE_COMMIT 6f88823` / `DEPLOYED_BUILD_ID 6f88823`. Current full gate = 1,796 passed / 32 skipped / 0 failed; valid real Qwen remains 0/9; no scientific evidence exists; Kaggle remains blocked pending the final independent full-gate audit, after which only the engineering preflight cell is authorized (not the scientific One-Run cell). The **pre-benchmark final reproducibility closure** (branch fix/kaggle-smoke-v2-model-output-closure) then declared the complete pre-benchmark dependencies (769d84e + e5d9430), recreated the clean environment from declarations only, and repeated the complete clean gate. The previous 76a6b16 gate had 1 failure, not a green full suite (1,833 passed / 32 skipped / 1 failed; sole failure = the notebook-pin identity test, structural - root cause: dependency declarations changing pyproject.toml after the aac9914/311e084 deployment pin; no runtime/prompt/metric/scenario/evaluator/data change needed; not forced green). The exact deployment-only correction f8d00d7 (bundle fast-forward, exactly one commit) re-pins the deployment (SOURCE_COMMIT=e5d9430, DEPLOYED_BUILD_ID=e5d9430, bundled pyproject.toml byte-identical to canonical); the complete clean suite is now green: 1,834 passed / 32 skipped / 0 failed; historical exp-20260801-210443 produced one failed model-output terminal record under 6f88823 (preserved, excluded from the current e5d9430 aggregation); current accepted real records = 0/9. **POST-SMOKE CALIBRATION CLOSURE (2026-08-03): four proven calibration control defects closed on branch fix/kaggle-smoke-v2-model-output-closure — (A) per-attempt atomic regeneration (zero writes on any guard failure), (B) repair no-progress detection (`repair_no_progress` early-stop on identical repair hash), (C) fail-closed calibration continuation gate (`AUTHORIZE_CONTINUOUS_AFTER_CALIBRATION_REVIEW = False`), (D) cooperative deadline semantics (`scientific_budget_exhausted` scientific terminal; preflight/env/HF timeouts remain engineering blockers). Commits `27c1693` (runtime + tests) + `56772fe` (deployment pin `SOURCE_COMMIT=27c1693e22b1a68be0b299fb146d9ff1e500908b` / `DEPLOYED_BUILD_ID=27c1693`, bundle rebuilt) + `231b0a5` (test-fixture reconciliation: the nine first full-gate failures were stale constant-output fixtures activating the new no-progress contract, not validly proven pre-existing; all max-attempt/repair-count/duration/token/JSONL expectations preserved; side-by-side no-progress-vs-max-attempt boundary test added). Final gate: full suite = 1,849 passed / 32 skipped / 0 failed; mypy strict Success (77 files); ruff 93 = 93 baseline (0 new); bundle content-identical (147 files / 934,495 bytes); all notebook cells compile; tree clean; local = remote = 231b0a5. Calibration evidence `exp-20260803-002741` = 9 terminal records / 0 succeeded / 8 failed / 1 timed_out / 81 model calls / 118,211 tokens — preserved, not accepted scientific evidence; latest real calibration = 0/9; no Kaggle rerun; no tag; Pilot not authorized; next action = one selective calibration canary only after independent audit (sentinel POST_SMOKE_CALIBRATION_CLOSURE_AUDIT_REQUIRED).** On 2026-08-04 the **dedicated selective calibration canary was executed** (`exp-20260804-133523`, `todo-smoke-001 / selective`, source/build `50ec2c1`): it **failed with `model_output`** — 4 calls / 5,804 tokens / 257.596 s, 3 selected / 2 preserved / **0 written**; Qwen defects in `models.py` (`max_length=5` vs MEDIUM length 6) and duplicated `Priority(models.TextChoices)` in `serializers.py` + `views.py`; the first repair was byte-identical → `repair_no_progress`; atomic write wrote zero files. Vs the previous selective run the canary was 41.6% fewer tokens / 33.3% fewer calls / 22.4% faster, but initial generation tokens (3,372) and output hashes were **identical** — **harness safety controls verified, Qwen code quality unchanged**. The incidental monolithic run `exp-20260804-133016` is diagnostic evidence only. The continuous cell correctly blocked fail-closed (`CALIBRATION_REVIEW_REQUIRED`). Accepted dedicated canary records = 1, successful = 0; full 9-record experiment NOT run; no merge/tag/Pilot/Kaggle authorized; no stable release claimed. Next: independent result audit (`SELECTIVE_CANARY_RESULT_AUDIT_REQUIRED`), then a deliberate decision between repeating the canary and the full 9-record run. Record: `selective_updates/records/SELECTIVE-CANARY-RESULTS-2026-08-04.md`.

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
FINAL SELECTIVE CANARY READINESS closure = COMPLETE (independent GPT-5.6 Thinking audit REJECTED canary readiness at f727b3e — full suite was green but three blockers: per-call deadline, atomic metric truth, no selective canary cell; Commit A 50ec2c1 + Commit B 28ecc5a (pin SOURCE_COMMIT=50ec2c1ca43c230aed4538be32ca7dab2ccc22e5 / DEPLOYED_BUILD_ID=50ec2c1, dedicated selective-calibration-canary-cell, isolated output runs/selective_calibration_canary, no --auto-resume-hf, continuous not authorized) + test alignment 356722b; HEAD 356722b, pushed, tree clean; full suite 1,856 passed / 32 skipped / 0 failed; grouped per-category 629 passed / 1 skipped; dry run 9/9 exit 0 (fresh dir); mypy strict Success (77 files); ruff 0 new; compileall clean; notebooks compile (8/8 bundle incl. canary cell); bundle content-identical (147 files / 948,250 bytes); no stable release claimed; sentinel FINAL_SELECTIVE_CANARY_READINESS_AUDIT_REQUIRED
SELECTIVE CALIBRATION CANARY = EXECUTED (2026-08-04) — dedicated canary exp-20260804-133523 (todo-smoke-001 / selective, source/build 50ec2c1) FAILED model_output: 4 calls / 5,804 tokens / 257.596 s / 3 selected / 2 preserved / 0 written; initial 3 calls / 3,372 tokens, repair 1 call / 2,432 tokens (first repair byte-identical → repair_no_progress); atomic write 0 files; defects in todo/models.py (max_length=5 vs MEDIUM length 6) + duplicated Priority(models.TextChoices) in serializers.py and views.py; vs previous selective run 41.6% fewer tokens / 33.3% fewer calls / 22.4% faster but initial generation tokens and output hashes identical → harness controls verified, Qwen quality unchanged; incidental monolithic exp-20260804-133016 (6 calls / 7,927 tokens / 300.165 s / scientific_budget_exhausted) = diagnostic only; continuous cell blocked fail-closed by CALIBRATION_REVIEW_REQUIRED; accepted dedicated canary records = 1, successful = 0; full 9-record experiment NOT run; no merge/tag/Pilot/Kaggle authorized; record SELECTIVE-CANARY-RESULTS-2026-08-04; sentinel SELECTIVE_CANARY_RESULT_AUDIT_REQUIRED
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

**FINAL SELECTIVE CANARY READINESS - THREE AUDIT BLOCKERS CLOSED, FULL SUITE GREEN, INDEPENDENT RE-AUDIT REQUIRED.** The independent GPT-5.6 Thinking audit at ``f727b3e`` rejected canary readiness (full suite was green, but three blockers were independently reproduced): (1) the cooperative workflow deadline was not checked before every generation call (direct repro: 3 calls and false success after a 1s deadline) - now every in-flight call beyond the deadline consumes its tokens, makes no next call, writes none of the staged attempt, and returns the failed scientific terminal ``scientific_budget_exhausted``; (2) atomic-abort ``regenerated_artifact_count`` was false (0 writes but count 1) - now all staged ``generated`` statuses become ``aborted``/``rejected`` and count = 0 with hashes/evidence preserved; (3) the generic one-run cell selects ``monolithic``, not ``selective`` - a dedicated Selective Calibration Canary cell was added (``--strategy selective --max-runs 1 --new-experiment --backend kaggle-qwen --profile scientific-smoke-v2 --max-attempts 3 --max-completion-tokens-per-call 1024 --max-total-workflow-tokens 0 --timeout 300 --hf-sync``, isolated output ``runs/selective_calibration_canary``, NO ``--auto-resume-hf``, ``AUTHORIZE_CONTINUOUS_AFTER_CALIBRATION_REVIEW = False``) whose ``_verify_selective_canary()`` asserts exactly one current-source ``todo-smoke-001 / selective`` record, model identity ``qwen:1:int8``, model calls > 0, terminal scientific outcome, HF ``recovery_uploaded``, checkpoint 3 planned / 1 completed / 2 pending. Commits: ``50ec2c1`` (Commit A), ``28ecc5a`` (Commit B, pin ``SOURCE_COMMIT = 50ec2c1ca43c230aed4538be32ca7dab2ccc22e5`` / ``DEPLOYED_BUILD_ID = 50ec2c1``), ``356722b`` (test alignment). Full suite = **1,856 passed / 32 skipped / 0 failed**; grouped per-category 629 passed / 1 skipped; scripted dry run 9/9 exit 0 (fresh dir; default dir held a stale checkpoint causing ReportRebuildError); mypy strict Success (77 files); ruff 0 new; compileall clean; notebooks compile (8/8 bundle code cells incl. the canary cell); bundle content-identical (147 files / 948,250 bytes). Calibration ``exp-20260803-002741`` preserved, 0/9 success, not accepted scientific evidence; no Kaggle rerun; no tag; no merge; no stable release claimed; Pilot not authorized. **After the independent re-audit, run the dedicated selective calibration canary cell ONLY** (not the generic one-run cell, not the continuous cell, not a full relaunch, not a fine-tune, not a tag/merge).

**NOW EXECUTED (2026-08-04):** the dedicated selective calibration canary ran and **failed** (`exp-20260804-133523`, `todo-smoke-001 / selective`, source/build `50ec2c1`; `model_output`, 4 calls / 5,804 tokens / 257.596 s, 3 selected / 2 preserved / 0 written; `repair_no_progress` after a byte-identical first repair). Harness safety controls were verified and Qwen code quality was unchanged (identical initial generation tokens and output hashes vs the previous selective run); the incidental monolithic run `exp-20260804-133016` is diagnostic evidence only; the continuous cell correctly stopped fail-closed with `CALIBRATION_REVIEW_REQUIRED`. The full 9-record experiment is **NOT run**; no merge/tag/Pilot/Kaggle authorized; no stable release claimed. **Next:** independent audit of the canary results (`SELECTIVE_CANARY_RESULT_AUDIT_REQUIRED`), then a deliberate decision between repeating the dedicated selective canary and proceeding to the full 9-record run.

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

# Read final selective canary readiness closure record
cat selective_updates/records/SELECTIVE-CANARY-READINESS-CLOSURE.md

# Read selective calibration canary result record
cat selective_updates/records/SELECTIVE-CANARY-RESULTS-2026-08-04.md
```

---

SELECTIVE_CANARY_RESULT_AUDIT_REQUIRED
