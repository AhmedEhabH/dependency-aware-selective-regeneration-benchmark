# Start Here — New Session Entry Point

## Context

You are resuming work on the Dependency-Aware Selective Regeneration Benchmark.

**Current state:** R4 (token limits and truthful workflow metrics) is **ACCEPTED AND FROZEN** at `f5ae826`; R5 (nine non-dry scripted production records) is **ACCEPTED AND FROZEN** by the independent re-audit at `7761c48` on 2026-08-01 (recorded in `docs/R5_FINAL_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md`). R6 (deployment closure) is **ACCEPTED AND FROZEN** by the final independent re-audit (GPT-5.6 Thinking, 2026-08-01, HEAD `949e9c2`), recorded in `docs/R6_FINAL_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md`. The R6 freeze commit `4b2dd27` is the exact first publication HEAD; the milestone branch is **published** with upstream `origin/experiment/three-arm-smoke-v2` and local/remote equality was verified. Post-R6: **two real Kaggle attempts failed pre-model** (`exp-20260801-024041`, `exp-20260801-024624`; both 0 model calls; preserved, not deleted). The real runtime blockers were closed and pinned on branch `fix/kaggle-smoke-v2-runtime-blockers` (fix commit `de3163f`, bundle pin `fb60972`); the R7A hardening closed the four independently reproduced findings (`d50e89e` + `4c73db6`). A subsequent real attempt reached 81 model calls / 47,694 tokens but produced 0 succeeded / 0 regenerated files. The **R7B Smoke Finish** (branch `fix/kaggle-smoke-v2-finish`, commits `bff0a82` + `17207bf`) makes the Qwen Smoke run observable and executable (strict JSON normalization, CUDA cleanup after every generation, live progress + ETA + dashboard artifacts, smoke-only 1024 cap, notebook live-run rewrite with `kaggle_console.log`). **R7C real-run root closure** (branch `fix/kaggle-smoke-v2-real-run-root`, `7a80e53` + `f01b8f0`) closed the four root contracts the FP16/deps-drift attempt exposed; the prior R7C report incorrectly called a 1,451-test subset the full suite (true first full suite = 23 failed / 1,759 passed / 32 skipped; root cause = blanket `baseline_validation => infrastructure_nonrepairable`); the independent GPT-5.6 Thinking correction (`ffa179a` + `6d6aa36`, HEAD `6d6aa36`, pushed) makes the exact 23 former failures pass and corrects DRF import mapping, exact version verification, fail-fast preflight, driver-level VRAM, CPU-offload rejection, the Python 3.12 runtime contract, and stale source identity. Current full gate = **1,790 passed / 32 skipped / 0 failed**. Local scripted records = 9/9; bundled CLI dry-run = 9/9; real Qwen records = 0/9; tag not created; Pilot not authorized. Next: **independent full-gate audit of the corrected R7C branch**; do not relaunch Kaggle before that. All required reading is repository-contained; external prompt packages are historical provenance only and are not required to continue. An independent post-gate audit on `5e47a1e` then found (a) the project-local `ImportError` was incorrectly bypassing repair, (b) the bundled preflight could not import `benchmark` without ambient `PYTHONPATH`, and (c) preflight output was buffered; its exact correction (`6f88823` + `5797fc0`, HEAD `5797fc0`, pushed) makes project-local `ModuleNotFoundError`/`cannot import name` repairable (missing declared Django + CUDA OOM stay `infrastructure_nonrepairable`), bootstraps the bundled script's own `src/`, and streams/persists preflight output. Notebook source identity = `SOURCE_COMMIT 6f88823` / `DEPLOYED_BUILD_ID 6f88823`. Current full gate = 1,796 passed / 32 skipped / 0 failed; valid real Qwen remains 0/9; no scientific evidence exists; Kaggle remains blocked pending the final independent full-gate audit, after which only the engineering preflight cell is authorized (not the scientific One-Run cell).

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
Pilot = not authorized
push = R7C branch PUBLISHED — upstream origin/fix/kaggle-smoke-v2-real-run-root, local/remote equal
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

**R7C ROOT CORRECTION IMPORTED — FULL-GATE AUDIT REQUIRED.** Two real Kaggle attempts failed pre-model (both 0 model calls; preserved); the runtime blockers were closed on `fix/kaggle-smoke-v2-runtime-blockers` (`de3163f` + `fb60972`), the R7A hardening closed the four audit findings (`d50e89e` + `4c73db6`), a further real attempt reached 81 model calls / 47,694 tokens with 0 succeeded / 0 regenerated files, and the attempt `exp-20260801-123125` failed at runtime root (FP16 OOM + dependency drift). The **R7B Smoke Finish** (`fix/kaggle-smoke-v2-finish`, `bff0a82` + `17207bf`) made the Qwen Smoke run observable and executable, and the **R7C real-run root closure** (`fix/kaggle-smoke-v2-real-run-root`, `7a80e53` + `f01b8f0`) closed the four root contracts (environment memory, int8 memory, frozen scenario context, infrastructure-nonrepairable repair) plus the `--kaggle-preflight-only` gate. The prior R7C report incorrectly called a 1,451-test subset the full suite; the true first full suite was **23 failed / 1,759 passed / 32 skipped** (root cause = blanket `baseline_validation => infrastructure_nonrepairable`). The independent GPT-5.6 Thinking correction (`ffa179a` + `6d6aa36`, HEAD `6d6aa36`, pushed) makes the exact 23 former failures pass and corrects DRF import mapping, exact version verification, fail-fast preflight, driver-level VRAM, CPU-offload rejection, the Python 3.12 runtime contract, and stale source identity (`SOURCE_COMMIT=ffa179a` / `DEPLOYED_BUILD_ID=ffa179a`). Current full gate = **1,790 passed / 32 skipped / 0 failed**; mypy strict 0; compileall clean; builder rerun clean; identity test passes. Valid real Qwen remains **0/9**; Kaggle remains **blocked**. Next: independent full-gate audit of the corrected R7C branch (`R7C_CORRECTION_FULL_GATE_AUDIT_REQUIRED`), then update the Kaggle code dataset + notebook, then one real cell (require 1/9 succeeded), then the remaining eight. Do not relaunch Kaggle, tag, merge, or force-push before that audit passes. The independent post-gate audit on `5e47a1e` and its exact correction (`6f88823` + `5797fc0`, HEAD `5797fc0`, pushed) are now applied: project-local `ImportError` no longer bypasses repair (canonical classifier; missing declared Django + CUDA OOM stay `infrastructure_nonrepairable`), the bundled preflight boots the script's own `src/` in a clean subprocess without ambient `PYTHONPATH`, preflight output is streamed and persisted, and notebook source identity is `6f88823`. Current full gate = 1,796 passed / 32 skipped / 0 failed. Final independent full-gate audit of HEAD `5797fc0` required (`R7C_POST_AUDIT_FULL_GATE_REQUIRED`); after it passes, the only authorized Kaggle action is the engineering preflight cell - not the scientific One-Run cell - then update the Kaggle code dataset + notebook, then one real cell (require 1/9 succeeded), then the remaining eight. Do not relaunch Kaggle, tag, merge, or force-push before that final audit passes.

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
```

---

R7C_CORRECTION_FULL_GATE_AUDIT_REQUIRED
