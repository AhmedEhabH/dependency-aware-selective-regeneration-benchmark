# Project Health Report

**Report Date:** 2026-08-01
**Project:** Dependency-Aware Selective Regeneration Benchmark
**Branch:** `fix/kaggle-smoke-v2-finish` (from the post-R6 runtime-blockers tail)
**R4/R5/R6 status:** R4 ACCEPTED AND FROZEN (`f5ae826`); R5 ACCEPTED AND FROZEN (`7761c48`); R6 ACCEPTED AND FROZEN (`949e9c2`) by the final independent re-audit (GPT-5.6 Thinking, 2026-08-01); milestone branch **published** to origin (freeze commit `4b2dd27` = first publication HEAD, local/remote equality verified).
**Post-R6:** two real Kaggle attempts failed pre-model (`exp-20260801-024041`, `exp-20260801-024624`; both 0 model calls); real runtime blockers closed and pinned — fix `de3163f`, bundle pin `fb60972` (core accepted by the independent runtime-fix audit); R7A hardening closed all four audit findings (source `d50e89e`, bundle `4c73db6`); a later real attempt reached 81 model calls / 47,694 tokens with 0 succeeded / 0 regenerated files. **R7B Smoke Finish complete (`bff0a82` + `17207bf`) — observable Qwen Smoke; R7B_SMOKE_FINISH_AUDIT_REQUIRED.**

---

## Executive Summary

R6 deployment closure is **accepted, frozen, and published**. Post-R6, two real
Kaggle Scientific Smoke V2 runs launched from the published deployment failed
completely before any model call (both 9 planned / 0 succeeded / 9 failed /
0 model calls / 0 tokens; first failure = workspace isolation). The real
runtime blockers were closed and pinned into a corrected bundle, and the R7A
hardening closed the four independently reproduced findings. A further real
attempt reached **81 model calls / 47,694 tokens but produced 0 succeeded /
0 regenerated files (0/9)** — **not scientific evidence**. The **R7B Smoke
Finish** makes the Qwen Smoke run observable and executable on branch
`fix/kaggle-smoke-v2-finish` (runtime commit `bff0a82`, bundle pin `17207bf`):
strict single-fence JSON output normalization, Qwen chat-template token
counting + `inference_mode` + CUDA cache cleanup after every generation
(success/OOM/other-exception), one shared backend instance per process, live
progress line + cross-session ETA + structured log events, deterministic
dashboard artifacts under `OUTPUT_DIR/dashboard` allowlisted for HF recovery,
smoke-only `max_completion_tokens_per_call: 1024`, and a notebook live-run
rewrite (`kaggle_console.log` persistence, actionable failure errors,
dashboard display, continuous precondition gating). Local engineering is green:
local scripted records = 9/9, bundled CLI dry-run = 9/9, full suite = 1,735
passed. Real-model evidence remains absent: real Qwen records = 0/9; the failed
attempts are preserved and not deleted. An independent audit of the R7B Smoke
Finish is required before any Kaggle relaunch.

**Legacy note:** Legacy Seven-Arm V1 results (including the `v0.7.0-smoke-passed` tag and the 7/7-arm Kaggle orchestration smoke) are **historical** and superseded. They are not V2 evidence. The current experiment is the Three-Arm Scientific Smoke V2 (`scientific-smoke-v2` profile): 3 frozen scenarios (todo-smoke-001/002/003) × 3 arms (monolithic, selective, iterative_repository_agent) × 1 repetition = 9 runs. Smoke evidence is non-publication.

---

## Current Post-R6 Health

### Test result

| Metric | Value |
|---|---|
| Full suite (final gate, Windows / Python 3.11.5) | **1,735 passed / 32 skipped / 0 failed** |
| Focused set (directive §7, unit + integration) | all passed |
| CLI + builder + bundle preflight | 91 passed |
| Bundled CLI nine-cell dry-run regression | passed (1 passed) |
| Builder rerun | success; bundle valid; deterministic |

### Deployment bundle

| Category | Files | Bytes |
|---|---|---:|
| code | 88 | — |
| data | 56 | — |
| notebooks | 1 | 31,023 |
| **total** | **145** | **858,225** |

### Integrity and content

```text
Builder                  = scripts/build_upload_bundle.py only
R7B runtime source       = bff0a82 (fix(kaggle): make Qwen Smoke observable and executable)
R7B bundle pin           = 17207bf (chore(deploy): pin final observable Smoke V2 bundle)
Runtime fix commit       = de3163f (post-R6 runtime blockers; bundle fb60972)
R7A hardening            = d50e89e + 4c73db6 (four audit findings closed)
HF results repo          = NabilDo/selective-regeneration-experiment-results
Preflight over bundle    = passed
```

### Static and type gates

```text
Ruff            = 0 new findings versus b6a2031 (baseline 91, current 91)
Mypy --strict   = 0 issues
Compileall      = clean
git diff --check = clean
git status --short = clean
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
| Kaggle runtime fix | COMMITTED AND PINNED (`de3163f`, `fb60972`) — core accepted by independent audit |
| R7A pre-rerun hardening | COMPLETE (`d50e89e` + `4c73db6`) — four audit findings closed |
| R7B Smoke Finish | COMPLETE (`bff0a82` + `17207bf`) — observable Qwen Smoke; independent audit required |
| Kaggle relaunch + nine real Qwen records | Blocked until R7B Smoke Finish audit passes |
| Pilot | Not authorized |
| Research experiment | Planned |

---

## Known evidence boundary

```text
Local scripted production proof = 9/9
Generated bundle dry-run plan   = 9/9
Kaggle attempts                 = 2 failed pre-model (preserved, 0 model calls)
Latest real attempt             = 0/9, 81 model calls, 47,694 tokens, 0 regenerated files
Real Qwen records               = 0/9
Real token/call/time comparison = unavailable
Publication evidence            = unavailable
Pilot evidence                  = unavailable
```

No real-model success or efficiency claim is authorized before the real Smoke result audit. Smoke evidence is non-publication.

---

## Near goal

Independent R7B Smoke Finish audit → relaunch nine real Qwen Scientific Smoke V2 records (3 scenarios × 3 arms × 1 repetition) with the observable bundle.

## Far goal

Independent real-result audit → stable `v2.0.0-scientific-smoke` tag → freeze Pilot matrix → Pilot execution → research experiment → statistical analysis → paper evidence package.

## Next action

Independent audit of the R7B Smoke Finish. Do not relaunch Kaggle, tag, merge, or force-push before that audit passes.

R7B_SMOKE_FINISH_AUDIT_REQUIRED
