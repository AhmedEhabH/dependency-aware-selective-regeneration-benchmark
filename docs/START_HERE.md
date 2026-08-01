# Start Here — New Session Entry Point

## Context

You are resuming work on the Dependency-Aware Selective Regeneration Benchmark.

**Current state:** R4 (token limits and truthful workflow metrics) is **ACCEPTED AND FROZEN** at `f5ae826`; R5 (nine non-dry scripted production records) is **ACCEPTED AND FROZEN** by the independent re-audit at HEAD `7761c48` on 2026-08-01 (recorded in `docs/R5_FINAL_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md`). R6 (deployment closure) passed the independent audit (GPT-5.6 Thinking, 2026-08-01, HEAD `da6ccf3`), and its **final correction is COMPLETE PENDING INDEPENDENT RE-AUDIT** (test commit `40c7a47` plus documentation-truth cleanup at current documentation HEAD), recorded in `docs/R6_INDEPENDENT_AUDIT_AND_CORRECTION_REPORT.md` and `selective_updates/records/R6-BUNDLE-PARITY-AND-PRE-KAGGLE-HANDOFF.md`. Local scripted records = 9/9; real Qwen records = 0/9; Kaggle not launched; push not performed; tag not created; Pilot not authorized. Do not push, tag, merge, or launch Kaggle before the independent R6 re-audit. All required reading is repository-contained; external prompt packages are historical provenance only and are not required to continue.

**Phase state:**
```text
R4 = accepted and frozen (explicit freeze commit f5ae826)
R5 = accepted and frozen (independent re-audit 2026-08-01 at 7761c48)
R6 = technical implementation passed independent audit; final correction complete pending re-audit
Kaggle = not launched
Pilot = not authorized
push = blocked pending re-audit
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

## R5 Acceptance and R6 Status

R5 was accepted and frozen by the independent re-audit on 2026-08-01 at HEAD `7761c48`. The clean R5 tail is `8fafb50`, `a24a9cd`, `875e4d1`, `ee148fa`, `7761c48`. R6 deployment closure was executed under the corrected directive and supersedes every earlier R6 prompt/directive: deterministic bundle builder, controlled Todo test deployment, exact evaluator allowlist, valid V2 smoke config, pinned notebook, bundle preflight integration, and manifest parity audits (0/0/0). The independent audit (GPT-5.6 Thinking, 2026-08-01, HEAD `da6ccf3`) passed the R6 technical implementation and bundle; the bounded final correction added the bundled CLI dry-run regression test (`40c7a47`) and closed documentation-truth defects D1–D6. R6 is now **FINAL CORRECTION COMPLETE PENDING INDEPENDENT RE-AUDIT**. Do not push, tag, merge, or launch Kaggle before the independent R6 re-audit.

```text
R5 = accepted and frozen at 7761c48
R6 = final correction complete pending re-audit
Kaggle = not launched
push = blocked pending re-audit
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
| `docs/R6_INDEPENDENT_AUDIT_AND_CORRECTION_REPORT.md` | R6 independent audit + final correction record (read for current R6 state) |
| `docs/R5_FINAL_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md` | R5 acceptance and freeze record |
| `selective_updates/records/R6-BUNDLE-PARITY-AND-PRE-KAGGLE-HANDOFF.md` | R6 bundle parity and pre-Kaggle handoff record |
| `reports/latest_phase_report.md` | Current R6 correction phase report (latest-first) |
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

**R6 final correction: COMPLETE PENDING INDEPENDENT RE-AUDIT.** The independent audit (GPT-5.6 Thinking, 2026-08-01, HEAD `da6ccf3`) passed the R6 technical implementation and bundle. The bounded correction pass closed TD-R6-ENTRYPOINT-001 (test commit `40c7a47`, bundled CLI dry-run 9/9) and documentation-truth defects D1–D6 (current documentation HEAD). Runtime source commit `cb25e9f`; deployed bundle commit `54a0462`. Next: independent R6 re-audit of the final correction, then push, Kaggle preflight, and nine real Qwen records. Do not push, tag, merge, or launch Kaggle before acceptance.

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

# Read R6 independent audit and final correction record
cat docs/R6_INDEPENDENT_AUDIT_AND_CORRECTION_REPORT.md

# Read R5 scope correction record
cat selective_updates/records/R5-INDEPENDENT-AUDIT-SCOPE-CORRECTION.md

# Read R6 bundle parity and pre-Kaggle handoff record
cat selective_updates/records/R6-BUNDLE-PARITY-AND-PRE-KAGGLE-HANDOFF.md
```

---

R6_FINAL_CORRECTION_REAUDIT_REQUIRED