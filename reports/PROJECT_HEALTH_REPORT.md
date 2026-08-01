# Project Health Report

**Report Date:** 2026-08-01
**Project:** Dependency-Aware Selective Regeneration Benchmark
**Branch:** `fix/kaggle-smoke-v2-runtime-blockers` (from R6-published `experiment/three-arm-smoke-v2`)
**R4/R5/R6 status:** R4 ACCEPTED AND FROZEN (`f5ae826`); R5 ACCEPTED AND FROZEN (`7761c48`); R6 ACCEPTED AND FROZEN (`949e9c2`) by the final independent re-audit (GPT-5.6 Thinking, 2026-08-01); milestone branch **published** to origin (freeze commit `4b2dd27` = first publication HEAD, local/remote equality verified).
**Post-R6:** two real Kaggle attempts failed pre-model (`exp-20260801-024041`, `exp-20260801-024624`; both 0 model calls); real runtime blockers closed and pinned — fix `de3163f`, bundle pin `fb60972`. **KAGGLE_RUNTIME_FIX_AUDIT_REQUIRED.**

---

## Executive Summary

R6 deployment closure is **accepted, frozen, and published**. Post-R6, two real
Kaggle Scientific Smoke V2 runs launched from the published deployment failed
completely before any model call (both 9 planned / 0 succeeded / 9 failed /
0 model calls / 0 tokens; first failure = workspace isolation). The real
runtime blockers were closed under the Kaggle Runtime Blockers Fix directive on
branch `fix/kaggle-smoke-v2-runtime-blockers` and pinned into a corrected
bundle: shared-snapshot isolation root, Kaggle Qwen fail-closed `--model-path`
validation + `qwen:` identity, non-zero session exit on failed last run,
batched truthful HF upload, `mark_completed(completed_with_failures=...)`, and
notebook guardrails (`discover_model()` fail-closed, `_verify_scientific_run()`
in both run cells, `NabilDo/selective-regeneration-experiment-results`,
`Terminal: n/9`). Local engineering is green: local scripted records = 9/9,
bundled CLI dry-run = 9/9, preflight = 15 passed, last full suite = 1,676
passed. Real-model evidence remains absent: real Qwen records = 0/9; the two
failed attempts are preserved and not deleted. An independent runtime-fix audit
is required before any Kaggle relaunch.

**Legacy note:** Legacy Seven-Arm V1 results (including the `v0.7.0-smoke-passed` tag and the 7/7-arm Kaggle orchestration smoke) are **historical** and superseded. They are not V2 evidence. The current experiment is the Three-Arm Scientific Smoke V2 (`scientific-smoke-v2` profile): 3 frozen scenarios (todo-smoke-001/002/003) × 3 arms (monolithic, selective, iterative_repository_agent) × 1 repetition = 9 runs. Smoke evidence is non-publication.

---

## Current Post-R6 Health

### Test result

| Metric | Value |
|---|---|
| Full suite (last full gate, Windows / Python 3.11.5) | **1,676 passed / 32 skipped / 0 failed** |
| Kaggle bundle preflight | **15 passed** (incl. `TestKaggleBundleRuntimeGuardrails`, 6) |
| Combined unit + integration (isolation, cli, hf_sync, production path, real smoke, todo smoke evaluator) | 254 passed / 2 skipped |
| Bundled CLI nine-cell dry-run regression | passed (1 passed) |
| Builder rerun | success; bundle valid |

### Deployment bundle

| Category | Files | Bytes |
|---|---|---:|
| code | 87 | — |
| data | 56 | — |
| notebooks | 1 | 18,137 |
| **total** | **144** | **815,004** |

### Integrity and content

```text
Builder                  = scripts/build_upload_bundle.py only
Runtime source commit    = de3163f12d51c31d3f488897ed2047821da3b190
Deployed build id        = de3163f
Deployment pin commit    = fb60972
HF results repo          = NabilDo/selective-regeneration-experiment-results
Preflight over bundle    = 15 passed
```

### Static and type gates

```text
Ruff            = 0 new findings (pre-existing baseline unchanged)
Mypy --strict   = base 5 pre-existing errors only, 0 new
Compileall      = clean
git diff --check = clean
git status --short = clean (after Commit C)
pip check       = clean
```

---

## Phases and milestones

| Phase | Status |
|---|---|
| Phase 0 — Bootstrap and Environment | Complete |
| Phase 1 — Input Audit | Complete |
| Phase 2B — Research Protocol Freeze | Complete (v1.0 frozen) |
| Phase 3 — Repository and Scenario Preparation | Complete |
| Phase 4A–4F, 4F.1 — Benchmark core | Complete |
| R3B / R3C / R3D closures | Complete |
| R4 — token/metric contract | ACCEPTED AND FROZEN (`f5ae826`) |
| R5 — nine scripted production records | ACCEPTED AND FROZEN (`7761c48`) |
| R6 — deployment closure | ACCEPTED AND FROZEN (`949e9c2`; freeze commit `4b2dd27`) |
| R6 milestone-branch publication | PUBLISHED (upstream set, local/remote equal) |
| Kaggle attempts (2) | FAILED pre-model — preserved (`exp-20260801-024041`, `exp-20260801-024624`) |
| Kaggle runtime fix | FIXES COMMITTED AND PINNED (`de3163f`, `fb60972`) — AUDIT REQUIRED |
| Kaggle relaunch + nine real Qwen records | Blocked until runtime-fix audit passes |
| Pilot | Not authorized |
| Research experiment | Planned |

---

## Known evidence boundary

```text
Local scripted production proof = 9/9
Generated bundle dry-run plan   = 9/9
Kaggle attempts                 = 2 failed pre-model (preserved, 0 model calls)
Real Qwen records               = 0/9
Real token/call/time comparison = unavailable
Publication evidence            = unavailable
Pilot evidence                  = unavailable
```

No real-model success or efficiency claim is authorized before the real Smoke result audit. Smoke evidence is non-publication.

---

## Near goal

Independent runtime-fix audit → relaunch nine real Qwen Scientific Smoke V2 records (3 scenarios × 3 arms × 1 repetition) with the corrected bundle.

## Far goal

Independent real-result audit → stable `v2.0.0-scientific-smoke` tag → freeze Pilot matrix → Pilot execution → research experiment → statistical analysis → paper evidence package.

## Next action

Independent audit of the runtime fixes. Do not relaunch Kaggle, tag, merge, or force-push before that audit passes.

KAGGLE_RUNTIME_FIX_AUDIT_REQUIRED
