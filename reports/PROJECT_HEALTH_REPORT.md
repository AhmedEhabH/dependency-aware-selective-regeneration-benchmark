# Project Health Report

**Report Date:** 2026-08-01
**Project:** Dependency-Aware Selective Regeneration Benchmark
**Branch:** `experiment/three-arm-smoke-v2`
**Accepted HEAD:** `949e9c2249004dbdeecc5ece531f72867611859c`
**R4/R5/R6 status:** R4 ACCEPTED AND FROZEN (`f5ae826`); R5 ACCEPTED AND FROZEN (`7761c48`); R6 ACCEPTED AND FROZEN (`949e9c2`) by the final independent re-audit (GPT-5.6 Thinking, 2026-08-01). Branch **published** to origin — freeze commit `4b2dd27` = exact first publication HEAD, upstream `origin/experiment/three-arm-smoke-v2`, local/remote equality verified.

---

## Executive Summary

R6 deployment closure is **accepted, frozen, and published**. The final independent re-audit (GPT-5.6 Thinking, 2026-08-01, audited HEAD `949e9c2`) accepted the R6 technical implementation, the generated Kaggle deployment bundle, and the bounded final correction (one deployed-entrypoint regression test `40c7a47` plus documentation-truth cleanup at `949e9c2`). The R6 freeze commit `4b2dd27` was published as the exact first publication HEAD with upstream set; local/remote equality was verified. Local engineering is deployment-ready: local scripted records = 9/9, bundled CLI dry-run = 9/9, manifests 0/0/0 mismatches. Real-model evidence remains absent: real Qwen records = 0/9, Kaggle not launched, no publication claim authorized. Next action is Kaggle environment preflight, then nine real Qwen Smoke records.

**Legacy note:** Legacy Seven-Arm V1 results (including the `v0.7.0-smoke-passed` tag and the 7/7-arm Kaggle orchestration smoke) are **historical** and superseded. They are not V2 evidence. The current experiment is the Three-Arm Scientific Smoke V2 (`scientific-smoke-v2` profile): 3 frozen scenarios (todo-smoke-001/002/003) × 3 arms (monolithic, selective, iterative_repository_agent) × 1 repetition = 9 runs. Smoke evidence is non-publication.

---

## Current R6 Health

### Test result

| Metric | Value |
|---|---|
| Full suite (final accepted R6 re-audit, Windows / Python 3.11.5) | **1,648 passed / 32 skipped / 0 failed** |
| Tests collected | 1,680 |
| Independent focused tests (Linux / Python 3.13) | 71 passed / 0 failed |
| Bundled CLI nine-cell dry-run regression | passed (1 passed) |
| Builder rerun | success; no tracked diff; tree clean |

### Deployment bundle

| Category | Files | Bytes |
|---|---:|---:|
| code | 87 | 619,346 |
| data | 56 | 172,210 |
| notebooks | 1 | 14,078 |
| **total** | **144** | **805,634** |

The three manifest files add 15,659 bytes and are intentionally outside their own category manifests.

### Integrity and content

```text
Git committed-tree manifest mismatches: code 0 / data 0 / notebook 0
Canonical/generated normalized parity problems = 0
Builder rerun working-tree changes             = 0
Sensitive/absolute-path scan findings          = 0
```

### Deployed controlled assets

```text
Todo baseline tests deployed   = exact five files / 47 test methods
Evaluator assets deployed      = 3 .py + 3 .sha256 fingerprints
tests/support files            = 0
scripted/harness files         = 0
forbidden artifacts            = 0
```

### Static and type gates

```text
Ruff            = 0 new findings vs starting HEAD 7761c48 (94 baseline findings identical, zero new)
Mypy --strict   = 0 new errors vs starting HEAD 7761c48
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
| Kaggle preflight + nine real Qwen records | Next |
| Pilot | Not authorized |
| Research experiment | Planned |

---

## Known evidence boundary

```text
Local scripted production proof = 9/9
Generated bundle dry-run plan   = 9/9
Manifest integrity              = 0/0/0 mismatches
Real Qwen records               = 0/9
Kaggle run                      = not launched
Real token/call/time comparison = unavailable
Publication evidence            = unavailable
Pilot evidence                  = unavailable
```

No real-model success or efficiency claim is authorized before the real Smoke result audit. Smoke evidence is non-publication.

---

## Near goal

Kaggle environment preflight → nine real Qwen Scientific Smoke V2 records (3 scenarios × 3 arms × 1 repetition).

## Far goal

Independent real-result audit → stable `v2.0.0-scientific-smoke` tag → freeze Pilot matrix → Pilot execution → research experiment → statistical analysis → paper evidence package.

## Next action

Kaggle environment preflight, then nine real Qwen Smoke records. Do not tag, merge, force-push, or launch Kaggle now.

R6_FROZEN_BRANCH_PUBLISHED_KAGGLE_PREFLIGHT_REQUIRED
