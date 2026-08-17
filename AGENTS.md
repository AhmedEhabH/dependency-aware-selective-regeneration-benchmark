# AGENTS.md — Dependency-Aware Selective Regeneration Benchmark

## Project facts

- **Language:** Python 3.11
- **Source:** `src/benchmark/`
- **Entry:** `seven_arm_benchmark.py`
- **Tests:** Pytest (test suite under `tests/`)
- **Lint:** Ruff (pyproject.toml config)
- **Types:** Mypy strict (`pyproject.toml`)
- **Kaggle:** generated code under `kaggle_upload/code/`
- **Bundle:** `scripts/build_upload_bundle.py`
- **Docs:** `docs/`
- **Updates:** ledgers under `selective_updates/`

## Working rule

inspect minimally → edit narrowly → changed-file diagnostics → affected tests → full validation only at final gate

## Context rules

Start with:
```
git status --short
git diff --stat
git diff --name-only
```

Use exact searches before reading whole files. Read only:
- changed files
- related symbols
- directly affected tests
- necessary configuration (pyproject.toml)

Do not read entire repository, generated code (unless verifying derivatives), datasets, large logs, or unrelated documentation.

## Validation order

1. `git diff --check`
2. Ruff on changed Python files
3. Mypy on changed production Python files only
4. Python compile check on changed Python files
5. Targeted Pytest
6. Full Pytest only before commit/merge or when shared interfaces changed
7. Bundle only when production code changed

## Resource rules

- No pytest-xdist by default
- No watch mode, GPU, dataset/model downloads, clean rebuild
- No full test suite after every small patch
- No parallel heavy commands
- Trim logs to first root cause and relevant tail (~120 lines max)

## Git rules

Do not commit, push, merge, tag, reset, stash, force, or delete files unless explicitly requested in the current task.

## Scientific rules

- Ground Truth is evaluation-only.
- Do not claim Scientific Smoke or Pilot success without real execution.
- Keep PROJECT_HANDOFF and MASTER_IMPLEMENTATION_PLAN truthful.
- Update README only when user-facing behavior changes.
- Stable tag only after a successful Scientific Smoke audit.

## Stop / Blocker Reporting Contract

Before stopping for ANY reason (needs auth, missing input, blocker, task
complete, uncertain decision, permission rule, resource boundary), print a
structured report containing:

1. **Execution Identity** — provider, model, branch, HEAD, origin/main, tree state
2. **Why I Am Stopping** — exact reason; COMPLETE / BLOCKED / NEEDS AUTHORIZATION / NEEDS INPUT
3. **What I Completed** — per-file table: File | Symbol | Old | New | Why | Dependencies
4. **Verification Performed** — compile, lint, mypy, tests (PASS/FAIL/NOT RUN/BLOCKED with exact counts)
5. **Pre-Benchmark Validation** — dataset, prompt, pipeline, dry-run, integration, metrics
6. **Independent Self-Audit** — objective unchanged, plan adherence, over-engineering, debt, durability, freshness, tag state
7. **Exact Current State** — where project stops in the pipeline
8. **What Remains** — ordered remaining tasks
9. **What I Need From User** — minimum input or `Nothing — I can continue automatically.`
10. **Recommended Next Action** — exact next command; if existing instructions authorize it, continue without stopping

Never end with only "Proceed?" or a bare question.
