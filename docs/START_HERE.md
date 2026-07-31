# Start Here — New Session Entry Point

## Context

You are resuming work on the Dependency-Aware Selective Regeneration Benchmark.

**Current state:** R4 (token limits and truthful workflow metrics) is **ACCEPTED AND FROZEN** at HEAD `a46213c` on branch `experiment/three-arm-smoke-v2` (independent re-audit by GPT-5.6 Thinking, 2026-07-31). R5 — nine non-dry scripted production records through the real production orchestration path — is **AUTHORIZED / IN PROGRESS**. R6, Kaggle, Pilot, merge, and stable tag remain **BLOCKED**. README is intentionally deferred to R6. Smoke evidence is non-publication.

**Phase state:**
```text
R4 = accepted and frozen
R5 = authorized/in progress
R6 = blocked
Kaggle = blocked
README = intentionally deferred to R6
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

## R5 Execution Order

R5 is governed by `..\OPENCODE_R5_NINE_RECORDS_SINGLE_PASS_DIRECTIVE.md` (repo root). The required matrix is 3 frozen Todo Smoke V2 scenarios × 3 scientific arms (monolithic, selective, iterative_repository_agent) × 1 repetition = 9 non-dry production-path records. Primary R5 files:

```text
tests/support/scripted_llm_backend.py
tests/support/scripted_smoke_v2.py
tests/integration/test_scientific_smoke_v2_production_path.py
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
| `docs/R4_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md` | R4 freeze record |
| `SYSTEM_STATE.md` | Current system state |
| `TODO.md` | Task list |
| `DECISION_LOG.md` | Decision history |
| `reports/latest_phase_report.md` | Latest phase summary (R4 freeze) |
| `reports/PROJECT_HEALTH_REPORT.md` | Project health dashboard |

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

**Execute R5 — nine non-dry scripted production records.** R4 is frozen; R5 is authorized. Build the scripted deterministic backend and harness, prove one scenario across all three arms, expand to the full 3 × 3 matrix, prove persistence/isolation/negative controls, run gates, and commit. Do not start R6 or Kaggle.

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
```

---

**R4_ACCEPTED_R5_AUTHORIZED**