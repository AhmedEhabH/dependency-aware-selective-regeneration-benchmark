# Start Here — New Session Entry Point

## Context

You are resuming work on the Dependency-Aware Selective Regeneration Benchmark.

**Last session outcome:** Research Design V2 Freeze and Repository-Agent Baseline Audit completed. Arm-to-protocol execution audit merged to `main` (commit `3a16596`). Created `docs/research-design-v2` branch with 10 design documents recording researcher-approved decisions RD-V2-01 through RD-V2-06. Current `RepositoryAgentStrategy` audited and classified as `SINGLE_SHOT_LLM_SCOPE_BASELINE` (not iterative).

**Current state:** Engineering validation complete (Kaggle smoke passed twice, tag `v0.7.0-smoke-passed` at `0c58250`). Research Design V2 documented and ready for researcher review. Pilot and research experiments have **not started**. Smoke evidence is non-publication.

---

## Quick Start

```bash
# Activate environment
conda activate selective-regen-benchmark

# Verify
python --version && pip check

# Run tests (613 passing, 1 skipped torch)
python -m pytest tests/ -v --tb=short

# Switch to RD-V2 design branch
git checkout docs/research-design-v2

# Verify tag
git tag -l 'v0.7*'
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
| `SYSTEM_STATE.md` | Current system state |
| `TODO.md` | Task list (next: SU-0010 authorization) |
| `DECISION_LOG.md` | Decision history (last: D023) |
| `docs/KAGGLE_EXECUTION_GUIDE.md` | How to run on Kaggle |
| `reports/latest_phase_report.md` | Latest phase summary (RD-V2 freeze) |
| `reports/PROJECT_HEALTH_REPORT.md` | Project health dashboard |

---

## Research Design V2 Summary (Frozen)

| Decision | Summary |
|----------|---------|
| **RD-V2-01** | Primary comparison: iterative repository agent vs hybrid selective (matched LLM, repo, change, params, tools, budget, repair, validation, quality) |
| **RD-V2-02** | Arm roles: repository_agent, hybrid_selective, single_shot_llm_scope, static_only, semantic_only, traceability_only, full_scope_reference, retrieval_planning_variant |
| **RD-V2-03** | Literature claims = related work/inspiration only; no head-to-head stats vs published scores |
| **RD-V2-04** | Measurement boundary: selection + regen + repair + validation with per-stage token accounting |
| **RD-V2-05** | Efficiency claims require matched correctness/quality |
| **RD-V2-06** | Experiment A (impact accuracy), B (e2e evolution), C (ablations), D (optional external transfer) |

**Current agent classification:** `SINGLE_SHOT_LLM_SCOPE_BASELINE` (single LLM call, no iteration, no tools, no generation, no repair).

**Required for confirmatory comparison:** `repository_agent` (iterative, bounded retrieval, file inspection, scope selection) — SU-0011.

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

**Await researcher review of RD-V2 decisions.** If authorized:

1. **SU-0010** — Implement shared regeneration executor + types + validators (~21 days)
2. **SU-0011** — Implement iterative repository agent baseline (separate task)
3. **K004** — Implement checkpoint/resume for long-running profiles
4. Then: Pilot → Research execution on Kaggle

---

## RD-V2 Design Documents (on `docs/research-design-v2` branch)

| Document | Purpose |
|----------|---------|
| `reports/REPOSITORY_AGENT_BASELINE_AUDIT.md` | Current agent audit → SINGLE_SHOT_LLM_SCOPE_BASELINE |
| `docs/REPOSITORY_AGENT_BASELINE_SPEC.md` | Iterative baseline acceptance criteria (SU-0011) |
| `docs/SHARED_REGENERATION_EXECUTOR_DESIGN.md` | Shared executor for all end-to-end arms (SU-0010) |
| `docs/ARM_ROLE_AND_NAMING_POLICY.md` | Legacy→scientific role mapping, naming rules |
| `docs/EXTERNAL_DATASET_EVALUATION_POLICY.md` | Experiment D gate: license, ground truth, no leakage |
| `reports/SU0010_IMPLEMENTATION_IMPACT_PLAN.md` | Dependency graph ImpactPrediction → Kaggle Bundle |
| `docs/EXPERIMENTAL_DESIGN_V2.md` | Experiments A/B/C/D, hypotheses, arm roles |
| `docs/END_TO_END_MEASUREMENT_BOUNDARY.md` | Per-stage token accounting (selection/regen/repair/validation) |
| `reports/RESEARCH_DESIGN_V2_DECISION_REPORT.md` | Consolidated decision record |

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

# Switch to RD-V2 branch
git checkout docs/research-design-v2
```

---

**RESEARCH_DESIGN_V2_READY_FOR_RESEARCHER_REVIEW**