# Start Here — New Session Entry Point

## Context

You are resuming work on the Dependency-Aware Selective Regeneration Benchmark.

**Last session outcome:** Kaggle real smoke passed twice. All 7 strategy arms succeeded with real Qwen2.5-Coder-7B-Instruct inference confirmed. Tag `v0.7.0-smoke-passed` at commit `0c58250`.

**Current state:** Engineering validation complete. Pilot and research experiments have **not started**. Smoke evidence is non-publication.

---

## Quick Start

```bash
# Activate environment
conda activate selective-regen-benchmark

# Verify
python --version && pip check

# Run tests (504 passing, 1 skipped torch)
python -m pytest tests/ -v --tb=short

# Verify tag
git tag -l 'v0.7*'
```

---

## Key Documents

| Document | Purpose |
|----------|---------|
| `docs/PROJECT_HANDOFF.md` | Full project handoff (read first) |
| `SYSTEM_STATE.md` | Current system state |
| `TODO.md` | Task list (next: checkpoint/resume) |
| `DECISION_LOG.md` | Decision history (last: D020) |
| `docs/KAGGLE_EXECUTION_GUIDE.md` | How to run on Kaggle |
| `reports/latest_phase_report.md` | Latest phase summary |
| `reports/PROJECT_HEALTH_REPORT.md` | Project health dashboard |

---

## Golden Rules

1. **No local LLM inference** — no torch/transformers locally
2. **No modifying frozen protocol documents** (8 docs under `docs/`)
3. **No modifying `inputs/`** — immutable external data
4. **Smoke evidence is non-publication** — do not cite
5. **Canonical project root is `project/`** (where `.git` lives)
6. **Failed runs must remain visible** — no deletion
7. **Commit code before any execution run** — tag for traceability

---

## Next Task

Implement **Kaggle checkpoint/resume support** for long-running profiles (pilot ~2-3h, research ~6-9h). See `TODO.md` task K004 for details.

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
```