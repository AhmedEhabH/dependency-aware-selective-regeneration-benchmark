# Project Health Report

**Report Date:** 2026-08-03
**Project:** Dependency-Aware Selective Regeneration Benchmark
**Branch:** `fix/kaggle-smoke-v2-model-output-closure` (HEAD `e5d9430`, pushed)
**R4/R5/R6 status:** R4 ACCEPTED AND FROZEN (`f5ae826`); R5 ACCEPTED AND FROZEN (`7761c48`); R6 ACCEPTED AND FROZEN (`949e9c2`) by the final independent re-audit (GPT-5.6 Thinking, 2026-08-01); milestone branch **published** to origin (freeze commit `4b2dd27` = first publication HEAD, local/remote equality verified).
**Post-R6:** two real Kaggle attempts failed pre-model (`exp-20260801-024041`, `exp-20260801-024624`; both 0 model calls); real runtime blockers closed and pinned — fix `de3163f`, bundle pin `fb60972` (core accepted by the independent runtime-fix audit); R7A hardening closed all four audit findings (source `d50e89e`, bundle `4c73db6`); a later real attempt reached 81 model calls / 47,694 tokens with 0 succeeded / 0 regenerated files; the attempt `exp-20260801-123125` failed at runtime root (FP16 OOM + dependency drift). **R7B Smoke Finish complete (`bff0a82` + `17207bf`); R7C real-run root closure complete (`7a80e53` + `f01b8f0`) + correction imported (`ffa179a` + `6d6aa36`) + post-gate correction imported (`6f88823` + `5797fc0`, HEAD `5797fc0`, pushed); deterministic interpreter closure complete (`aac9914` + `311e084`); PRE-BENCHMARK FINAL REPRODUCIBILITY CLOSURE COMPLETE (`769d84e` + `e5d9430`, HEAD `e5d9430`, pushed); PRE_BENCHMARK_FINAL_REPRODUCIBILITY_AUDIT_REQUIRED.**

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
`fix/kaggle-smoke-v2-finish` (runtime commit `bff0a82`, bundle pin `17207bf`),
and the **R7C real-run root closure** (branch `fix/kaggle-smoke-v2-real-run-root`,
`7a80e53` + `f01b8f0`) closed the four root contracts the FP16/deps-drift
attempt `exp-20260801-123125` exposed (exact runtime pins, int8 default, frozen
scenario context, infrastructure-nonrepairable repair) plus a
`--kaggle-preflight-only` gate. The prior R7C report incorrectly called a
1,451-test subset the full suite; the true first full suite was **23 failed /
1,759 passed / 32 skipped** (root cause = blanket `baseline_validation =>
infrastructure_nonrepairable`). The independent GPT-5.6 Thinking correction
(`ffa179a` + `6d6aa36`) makes the exact 23 former failures pass and corrects
DRF import mapping, exact version verification, fail-fast preflight,
driver-level VRAM, CPU-offload rejection, the Python 3.12 runtime contract, and
stale source identity. An independent post-gate audit on `5e47a1e` then found
the project-local `ImportError` was still bypassing repair, the bundled
preflight could not import `benchmark` without ambient `PYTHONPATH`, and
preflight output was buffered; its exact correction (`6f88823` + `5797fc0`,
HEAD `5797fc0`, pushed) was imported via bundle fast-forward. The deterministic
interpreter closure (`aac9914` + `311e084`) then bound bare interpreter tokens
to the active runtime at the post-generation execution boundary. The
**pre-benchmark final reproducibility closure** (branch
`fix/kaggle-smoke-v2-model-output-closure`, HEAD `e5d9430`, pushed) declared
the complete pre-benchmark dependencies (`769d84e` + `e5d9430`), recreated the
clean environment from declarations only (Python 3.11.9), and repeated the
complete clean gate. Local engineering: local scripted records = 9/9, bundled
CLI dry-run = 9/9, Dataset Validation 285/5, Prompt Validation 158, Pipeline
Smoke 220/12, Integration PASS, Metric Verification 169, mypy strict Success
(77 files), ruff 93 = 93 baseline (0 new), compileall clean, and the full suite
= **1,833 passed / 32 skipped / 1 failed** — the sole failure is the
notebook-pin identity test, structural because the mandated `pyproject.toml`
declaration change breaks byte-identity with the pinned `aac9914` SOURCE_COMMIT;
frozen artifacts were not modified to force green and the truthful total is
recorded. Historical `exp-20260801-210443` produced one failed model-output
terminal record under source `6f88823` — preserved, excluded from the current
`aac9914` aggregation; current accepted `aac9914` records = **0/9**; no
scientific evidence exists; no tag; no Pilot; no Kaggle launch. A final
independent pre-benchmark reproducibility audit is required before any Kaggle
relaunch, after which only the engineering preflight cell is authorized (not
the scientific One-Run cell).

**Legacy note:** Legacy Seven-Arm V1 results (including the `v0.7.0-smoke-passed` tag and the 7/7-arm Kaggle orchestration smoke) are **historical** and superseded. They are not V2 evidence. The current experiment is the Three-Arm Scientific Smoke V2 (`scientific-smoke-v2` profile): 3 frozen scenarios (todo-smoke-001/002/003) × 3 arms (monolithic, selective, iterative_repository_agent) × 1 repetition = 9 runs. Smoke evidence is non-publication.

---

## Current Post-R6 Health

### Test result

| Metric | Value |
|---|---|
| Full suite (recreated clean env, Windows / Python 3.11.9) | **1,833 passed / 32 skipped / 1 failed** |
| Sole failure | notebook-pin identity test — structural (mandated pyproject.toml declaration change breaks byte-identity with pinned aac9914 SOURCE_COMMIT); frozen artifacts not modified to force green; reported truthfully |
| Dataset Validation | 285 passed / 5 skipped |
| Prompt Validation | 158 passed |
| Pipeline Smoke | 220 passed / 12 skipped |
| Dry Run | scientific-smoke-v2 9/9 succeeded (exit 0) |
| Integration | PASS |
| Metric Verification | 169 passed |
| Bundled CLI nine-cell dry-run regression | passed |
| Builder build | success (147 files / 928,329 bytes) then kaggle_upload restored |

### Deployment bundle

| Category | Files | Bytes |
|---|---:|---:|
| code | 90 | 715,210 |
| data | 56 | 172,210 |
| notebooks | 1 | 40,909 |
| **total** | **147** | **928,329** |

### Integrity and content

```text
Builder                  = scripts/build_upload_bundle.py only (build verified, then kaggle_upload restored)
Runtime source           = aac9914 (fix(exec): bind Python scenario commands to active runtime)
Deployment pin           = 311e084 (chore(deploy): pin deterministic-interpreter Smoke V2 bundle)
Declaration commits      = 769d84e + e5d9430 (HEAD e5d9430)
Notebook source identity = SOURCE_COMMIT=aac9914, DEPLOYED_BUILD_ID=aac9914
HF results repo          = NabilDo/selective-regeneration-experiment-results
Preflight over bundle    = passed (historical R7C gate)
```

### Static and type gates

```text
Ruff            = 93 findings = 468a23a baseline (verified in a detached worktree; 93 = 93) — 0 new
Mypy --strict   = Success: no issues found in 77 source files
Compileall      = clean (exit 0)
Notebook cells  = unchanged (7/7 code cells compile as pinned)
git diff --check = clean (LF->CRLF warning on requirements-dev.txt only)
git status --short = clean
Benchmark data  = unchanged
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
| R7B Smoke Finish | COMPLETE (`bff0a82` + `17207bf`) — observable Qwen Smoke |
| R7C real-run root closure | COMPLETE (`7a80e53` + `f01b8f0`) + correction imported (`ffa179a` + `6d6aa36`) + post-gate correction imported (`6f88823` + `5797fc0`, HEAD `5797fc0`) — final full-gate audit required |
| Deterministic interpreter closure | COMPLETE (`aac9914` + `311e084`) — bare interpreter tokens bound to active runtime |
| Pre-benchmark reproducibility closure | COMPLETE (`769d84e` + `e5d9430`, HEAD `e5d9430`, pushed) — deps fully declared; clean env recreated from declarations only; repeated full gate 1,833 passed / 32 skipped / 1 failed (structural notebook-pin test, not forced green) |
| Kaggle relaunch + nine real Qwen records | Blocked until the independent pre-benchmark audit and the final full-gate audit pass; next authorized action = engineering preflight cell only |
| Pilot | Not authorized |
| Research experiment | Planned |

---

## Known evidence boundary

```text
Local scripted production proof = 9/9
Generated bundle dry-run plan   = 9/9
Kaggle attempts                 = 2 failed pre-model (preserved, 0 model calls)
Latest real attempt             = exp-20260801-123125 (FP16 → OOM; deps drifted)
Historical experiment           = exp-20260801-210443 (ONE failed model-output terminal record
                                  under 6f88823 — preserved, excluded from current aac9914 aggregation)
Current aac9914 records         = 0/9
Real Qwen records               = 0/9
Scientific evidence             = NONE (no real-model success yet)
Real token/call/time comparison = unavailable
Publication evidence            = unavailable
Pilot evidence                  = unavailable
```

No real-model success or efficiency claim is authorized before the real Smoke result audit. Smoke evidence is non-publication.

---

## Near goal

Independent audit of the pre-benchmark reproducibility closure (HEAD `e5d9430`) → after it passes, the only authorized Kaggle action is the engineering preflight cell (not the scientific One-Run cell) → update the Kaggle code dataset + notebook → relaunch nine real Qwen Scientific Smoke V2 records (3 scenarios × 3 arms × 1 repetition) with the corrected preflighted bundle.

## Far goal

Independent real-result audit → stable `v2.0.0-scientific-smoke` tag → freeze Pilot matrix → Pilot execution → research experiment → statistical analysis → paper evidence package.

## Next action

Independent pre-benchmark reproducibility audit (HEAD `e5d9430`). Do not relaunch Kaggle, tag, merge, or force-push before that audit passes.

PRE_BENCHMARK_FINAL_REPRODUCIBILITY_AUDIT_REQUIRED
