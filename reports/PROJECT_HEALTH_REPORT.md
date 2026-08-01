# Project Health Report

**Report Date:** 2026-08-01
**Project:** Dependency-Aware Selective Regeneration Benchmark
**Branch:** `fix/kaggle-smoke-v2-real-run-root` (from the post-R6 runtime-blockers tail)
**R4/R5/R6 status:** R4 ACCEPTED AND FROZEN (`f5ae826`); R5 ACCEPTED AND FROZEN (`7761c48`); R6 ACCEPTED AND FROZEN (`949e9c2`) by the final independent re-audit (GPT-5.6 Thinking, 2026-08-01); milestone branch **published** to origin (freeze commit `4b2dd27` = first publication HEAD, local/remote equality verified).
**Post-R6:** two real Kaggle attempts failed pre-model (`exp-20260801-024041`, `exp-20260801-024624`; both 0 model calls); real runtime blockers closed and pinned — fix `de3163f`, bundle pin `fb60972` (core accepted by the independent runtime-fix audit); R7A hardening closed all four audit findings (source `d50e89e`, bundle `4c73db6`); a later real attempt reached 81 model calls / 47,694 tokens with 0 succeeded / 0 regenerated files; the attempt `exp-20260801-123125` failed at runtime root (FP16 OOM + dependency drift). **R7B Smoke Finish complete (`bff0a82` + `17207bf`); R7C real-run root closure complete (`7a80e53` + `f01b8f0`) + correction imported (`ffa179a` + `6d6aa36`) + post-gate correction imported (`6f88823` + `5797fc0`, HEAD `5797fc0`, pushed); R7C_POST_AUDIT_FULL_GATE_REQUIRED.**

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
HEAD `5797fc0`, pushed) was imported via bundle fast-forward. Local engineering
is green: local scripted records = 9/9, bundled CLI dry-run = 9/9, full suite =
1,796 passed. Real-model evidence remains absent: real Qwen records = 0/9; the
failed attempts are preserved and not deleted; no scientific evidence exists
yet. A final independent full-gate audit of the corrected R7C branch is
required before any Kaggle relaunch, after which only the engineering preflight
cell is authorized (not the scientific One-Run cell).

**Legacy note:** Legacy Seven-Arm V1 results (including the `v0.7.0-smoke-passed` tag and the 7/7-arm Kaggle orchestration smoke) are **historical** and superseded. They are not V2 evidence. The current experiment is the Three-Arm Scientific Smoke V2 (`scientific-smoke-v2` profile): 3 frozen scenarios (todo-smoke-001/002/003) × 3 arms (monolithic, selective, iterative_repository_agent) × 1 repetition = 9 runs. Smoke evidence is non-publication.

---

## Current Post-R6 Health

### Test result

| Metric | Value |
|---|---|
| Full suite (final gate, Windows / Python 3.11.5) | **1,796 passed / 32 skipped / 0 failed** |
| Prior full-suite truth | "1,451" was a SUBSET; true first full suite 23 failed / 1,759 passed / 32 skipped |
| Boundary regressions (post-gate) | 7 passed (runner 4, bundle bootstrap 1, cli 2) |
| Regression gates (r4 + su0010a + su0011) | 119 passed |
| Preflight / runner / cli / builder | 25 / 45 / 84 / 11 passed |
| Scientific-smoke-v2 production path / bundle preflight | 41 / 25 passed |
| Bundled CLI nine-cell dry-run regression | passed |
| Builder rerun | success; content-identical; manifests verified |

### Deployment bundle

| Category | Files | Bytes |
|---|---|---:|
| code | 90 | — |
| data | 56 | — |
| notebooks | 1 | — |
| **total** | **147** | **895,759** |

### Integrity and content

```text
Builder                  = scripts/build_upload_bundle.py only
R7C runtime source       = 7a80e53 (fix(kaggle): close environment memory and prompt contracts)
R7C bundle pin           = f01b8f0 (chore(deploy): pin preflighted int8 Smoke V2 bundle)
R7C correction           = ffa179a + 6d6aa36 (SOURCE_COMMIT=ffa179a, DEPLOYED_BUILD_ID=ffa179a)
R7C post-gate correction = 6f88823 + 5797fc0 (HEAD 5797fc0; SOURCE_COMMIT=6f88823, DEPLOYED_BUILD_ID=6f88823)
Runtime fix commit       = de3163f (post-R6 runtime blockers; bundle fb60972)
R7A hardening            = d50e89e + 4c73db6 (four audit findings closed)
HF results repo          = NabilDo/selective-regeneration-experiment-results
Preflight over bundle    = passed
```

### Static and type gates

```text
Ruff            = 0 new versus 5e47a1e (93 = 93); ARG004 identity-locked; 5 pre-existing
                 seven_arm_benchmark.py findings reproduced at 5e47a1e
Mypy --strict   = 0 issues
Compileall      = clean
Notebook cells  = canonical + generated 7/7 code cells compile
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
| R7B Smoke Finish | COMPLETE (`bff0a82` + `17207bf`) — observable Qwen Smoke |
| R7C real-run root closure | COMPLETE (`7a80e53` + `f01b8f0`) + correction imported (`ffa179a` + `6d6aa36`) + post-gate correction imported (`6f88823` + `5797fc0`, HEAD `5797fc0`) — final full-gate audit required |
| Kaggle relaunch + nine real Qwen records | Blocked until the final full-gate audit of the corrected R7C branch passes; next authorized action = engineering preflight cell only |
| Pilot | Not authorized |
| Research experiment | Planned |

---

## Known evidence boundary

```text
Local scripted production proof = 9/9
Generated bundle dry-run plan   = 9/9
Kaggle attempts                 = 2 failed pre-model (preserved, 0 model calls)
Latest real attempt             = exp-20260801-123125 (FP16 → OOM; deps drifted)
Real Qwen records               = 0/9
Scientific evidence             = NONE (no real-model success yet)
Real token/call/time comparison = unavailable
Publication evidence            = unavailable
Pilot evidence                  = unavailable
```

No real-model success or efficiency claim is authorized before the real Smoke result audit. Smoke evidence is non-publication.

---

## Near goal

Final independent full-gate audit of the corrected R7C branch (HEAD `5797fc0`) → after it passes, the only authorized Kaggle action is the engineering preflight cell (not the scientific One-Run cell) → relaunch nine real Qwen Scientific Smoke V2 records (3 scenarios × 3 arms × 1 repetition) with the corrected preflighted bundle.

## Far goal

Independent real-result audit → stable `v2.0.0-scientific-smoke` tag → freeze Pilot matrix → Pilot execution → research experiment → statistical analysis → paper evidence package.

## Next action

Final independent full-gate audit of the corrected R7C branch (HEAD `5797fc0`). Do not relaunch Kaggle, tag, merge, or force-push before that audit passes.

R7C_POST_AUDIT_FULL_GATE_REQUIRED
