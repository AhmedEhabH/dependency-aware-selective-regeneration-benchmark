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

## Release facts

> **CURRENT TRUTH (2026-08-24, v0.9.20 RELEASED): accepted release =
> `v0.9.20-pilot-exec-ready` @ annotated tag peel == artifact source commit ==
> merge `febda7938db1284da4090d35e980db472149c3ad`; archive
> `dist/pilot-kaggle-upload.zip` SHA-256
> `56b1c2a9019a03892ce627321b9a415795ac95836ac415694bbc0995263c8024` (+ sidecar);
> trust/provenance 0 mismatches; dry-run 48/48; full suite 2346 passed /
> 33 skipped / 0 failed. The real Kaggle v0.9.19 run FAILED at the Saleor fast
> capability gate (Pytest exit 5 = no tests collected; services/env/Todo/
> django CMS all PASS) — v0.9.19 REJECTED FOR PILOT LAUNCH. Root cause: the gate
> argv concatenated a second `-m pytest` vector onto the already-resolved full
> primary command (Pytest read `-m pytest` as a marker expression). Local tests
> were false-green via a substring-based fake runner. Closed in v0.9.20: exact
> standalone gate argv + fail-fast invariant + exact-argv regression tests
> (RED/GREEN proven; target-proven on Linux CI runs 32650273641 / 32672656326 /
> 32676588800 — the last is the fully green no-model preflight on the released
> source state, pristine Saleor primary exit 0 in 775.71 s) + substring mock
> replaced by exact-command validation + evidence-backed baseline-flake policy
> (`pilot_saleor_baseline_flaky_profile.v1`, armed-if-evidenced) +
> `.github/workflows/pilot-preflight-target-shape.yml`. Stable-tag policy:
> `*-pilot-exec-ready` means all no-model preflight gates passed in
> target-shaped Linux CI. Report:
> `reports/V0920_ROOT_CAUSE_CLOSURE_REPORT.md`.
>
> **PRIOR TRUTH (HISTORICAL):** accepted source tag `v0.9.19-pilot-exec-ready`;
> tag peel/artifact source commit `2305991442a4f965d44bb066bb00c0a459fc395a`
> (REJECTED FOR PILOT LAUNCH 2026-08-24 by the defect above).

- **Accepted release/tag (CURRENT):** `v0.9.20-pilot-exec-ready` @ tag peel == artifact source commit == merge `febda7938db1284da4090d35e980db472149c3ad`; archive `56b1c2a9019a03892ce627321b9a415795ac95836ac415694bbc0995263c8024`; trust/provenance 0 mismatches; target-shaped CI green (run 32676588800)
- **v0.9.19 status:** REJECTED FOR PILOT LAUNCH 2026-08-24 — real Kaggle Saleor fast-gate Pytest exit 5 (artifact itself was internally GREEN; superseded by v0.9.20)
- **v0.9.18 status:** RELEASE-ONLY CLOSURE (release-only provenance/docs correction; no scientific or production code changes) — historical
- **v0.9.17 status:** REJECTED FOR ACCEPTED PILOT LAUNCH — tag/source-commit release-provenance mismatch (immutable tag peel `28a18e6...` != artifact source_commit `adf72d4...`; the artifact itself is internally trustworthy and the PGDG fix is GOOD)
- **v0.9.16 status:** RELEASE-ONLY CLOSURE (no production behavior changes; notebook anchors corrected) — historical
- **v0.9.15 status:** REJECTED FOR ACCEPTED PILOT LAUNCH — release finalization/artifact not completed (dist artifact still v0.9.14; code-manifest SHA stale; single-parent commit)
- **v0.9.14 status:** REJECTED — artifact notebook provenance did not match immutable tag notebook (historical; see CURRENT TRUTH above)

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

## Release provenance invariant

- Artifact source commit MUST equal immutable release tag peel.
- Create the tag explicitly on the accepted artifact source commit (not HEAD).
- Post-tag docs evidence commits are never tag targets.

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

## Project Export Rule (every mandatory stop)

At every STOP / Mandatory Stop Report, create a filtered audit ZIP in the
parent directory of `project/` named exactly `project-YYYY-MM-DD-HHmm.zip`
(local creation timestamp). This is workflow/documentation only — do NOT
create a release, move, or tag for this rule.

**Include:** ALL files tracked by `git ls-files` (source, tests, notebooks,
docs, configs, scripts, `benchmark_data/`, `reports/`, `runs_dryrun/`,
`.opencode/` workflow files, etc.), `.git/`,
`dist/pilot-kaggle-upload.zip`, `dist/pilot-kaggle-upload.zip.sha256`.

**Exclude:** `.mypy_cache/`, `.ruff_cache/`, `.pytest_cache/`,
`__pycache__/`, `*.pyc`, `.opencode/node_modules/`, `dist/_provcheck*`,
extracted `dist/pilot-kaggle-upload/`, `dist/pilot-repo-cache/`.

**Do not delete** anything from the real project. Only the share ZIP is
filtered.

After creation verify required members inside the ZIP (`.git/HEAD`,
`dist/pilot-kaggle-upload.zip`, `.sha256`), compute size + SHA-256, and
print:

```
PROJECT_EXPORT_READY
PROJECT_EXPORT_NAME=project-YYYY-MM-DD-HHmm.zip
PROJECT_EXPORT_PATH=<absolute path>
PROJECT_EXPORT_SIZE_BYTES=<bytes>
PROJECT_EXPORT_SHA256=<sha256>
UPLOAD_THIS_FILE=project-YYYY-MM-DD-HHmm.zip
```

The Stop Report must include this filename so the user knows which file to
upload.
