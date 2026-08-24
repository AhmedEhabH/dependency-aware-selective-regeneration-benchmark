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

> **CURRENT TRUTH (2026-08-24, v0.9.22 CANDIDATE — TARGET MEMORY PROOF PENDING): branch
> `fix/pilot-v0922-long-context-attention-memory-closure` implements the long-context
> attention memory closure on top of clean main `58d1be533c98ca9bafc9a344f2a73f8a140b9540`
> (v0.9.21 reconciled).** The real Kaggle v0.9.21 model preflight PASSED repository
> preflight / dependencies / Qwen 14B BNB-NF4 load (`qwen_model_load[bnb-nf4]: PASS` —
> the old 2026-08-05 model-load OOM fix still works) / GPU-only device map / 2x Tesla T4 /
> per-GPU headroom (min free 7.764 GiB) / short generation probe, then FAILED at the
> long-context probe with CUDA OOM: 12,044 prompt tokens / 64-token output budget /
> **failed allocation 21.62 GiB == exactly `12044*12044*40*4 bytes = 21.6153 GiB`, the
> full float32 40-head quadratic attention score matrix** — proving the effective runtime
> attention path had materialized the math/eager fallback during prompt prefill
> (offloaded KV cache does not cover prefill attention; device_map=auto is not tensor
> parallelism). v0.9.21 Real Pilot REJECTED BEFORE LAUNCH for this reason; no Experiment
> ID / no RunRecord created; no stable tag moved. The v0.9.22 candidate closes it WITHOUT
> touching any scientific input (model Qwen2.5-Coder-14B-Instruct, BNB-NF4, 12 scenarios,
> 3 repo pins, 2 strategies, 2 reps = 48 cells, prompts, Ground Truth, metrics,
> --timeout 600, --validation-timeout 1800, max attempts 3, completion cap 4096, the
> 12000-token long-context gate, the 64-token probe): Task A explicit
> `attn_implementation="sdpa"` at from_pretrained; Task B fail-closed CUDA generation
> inside `sdpa_kernel([FLASH_ATTENTION, EFFICIENT_ATTENTION])` (no math/eager fallback;
> missing torch.nn.attention API on CUDA fails closed); Task C canonical attention
> evidence (`requested/effective_attn_implementation`,
> `sdpa_kernel_policy=flash_or_efficient_no_math`) persisted in preflight JSON, rendered
> in the human table, enforced by the new fail-closed `attention_policy` check and by
> pilot launch authorization; Task D corrected OOM diagnosis (long-prompt OOM reports
> prompt-prefill attention evidence + free GiB and never advises completion-cap
> reduction); Tasks E/F regression-guard every prior memory fix and the unchanged
> 12000/64 gate. RED/GREEN proven: 12 backend + 18 preflight contract tests failed
> against v0.9.21 code before the fix. Full suite **2407 passed / 33 skipped / 0
> failed**; dry-run pilot profile 48/48 (unique IDs, 0 model calls, 0 tokens). NO stable
> tag exists yet: per the one-shot flow the exact candidate artifact is built from the
> merge commit and the real 2x T4 Kaggle model preflight (same 12k target, same 64-token
> probe) is MANDATORY before creating `v0.9.22-pilot-exec-ready`; if the Kaggle proof
> fails, return to the SAME v0.9.22 task (never spawn v0.9.23). Report:
> `reports/V0922_LONG_CONTEXT_ATTENTION_MEMORY_CLOSURE_REPORT.md`.
>
> **PRIOR TRUTH (2026-08-24, HISTORICAL): accepted release =
> `v0.9.21-pilot-exec-ready` @ annotated tag peel == artifact source commit ==
> merge `e308047c9c05f38316d80ce565bac1b51d105bfa`; archive
> `dist/pilot-kaggle-upload.zip` SHA-256
> `62e377467e225d336cbcaa70a2c610b5080e329e1a4e6578fbcbdc1af7dbee40` (+ sidecar);
> trust/provenance 0 mismatches; exact-artifact dry-run 48/48; full suite 2370 passed /
> 33 skipped / 0 failed; target-shaped no-model preflight GREEN on the released source
> state (CI run 32694137255; Gates 1-3 green in run 32692489617: production
> FunctionalValidator real targets exit 0 with provisioned interpreters + frozen env;
> Saleor full primary exit 0 in 941.42s < the new explicit 1800s per-cell validation
> budget). v0.9.20 closed the Saleor preflight root cause but was NOT accepted for Real
> Pilot launch: an independent audit found that generated-workspace validation used
> sys.executable for every repository (B1), discarded the frozen validation env (B2), and
> hardcoded a 180s validation timeout below the measured 775.71s/941.42s Saleor runtime
> (B3). v0.9.21 closes all three with --validation-python mappings,
--validation-timeout 1800 on launch+resume, and frozen-env propagation through
PipelineConfig/RunnerConfig into FunctionalValidator. The v0.9.21 repository/per-cell
fixes remain VALID and are carried forward; the Real Pilot was rejected before launch
only because the fresh real 12k model probe exposed the attention-prefill OOM now closed
by the v0.9.22 candidate. Report:
> `reports/V0921_PER_CELL_VALIDATION_RUNTIME_CLOSURE_REPORT.md`.
>
> **PRIOR TRUTH (2026-08-24 earlier in the day, HISTORICAL): accepted release =
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

- **Accepted release/tag:** `v0.9.21-pilot-exec-ready` @ tag peel == artifact source commit == merge `e308047c9c05f38316d80ce565bac1b51d105bfa`; archive `62e377467e225d336cbcaa70a2c610b5080e329e1a4e6578fbcbdc1af7dbee40`; trust/provenance 0 mismatches; target-shaped CI green with Gates 1-3 (runs 32692489617 / 32694137255) — **superseded as launch candidate by the v0.9.22 attention closure (Real Pilot rejected before launch at the real 12k attention-prefill OOM); no v0.9.22 stable tag until the real 2x T4 12k probe PASSES**
- **v0.9.22 candidate (CURRENT):** branch `fix/pilot-v0922-long-context-attention-memory-closure`; long-context attention memory closure (Tasks A-F above); full suite 2407 passed / 33 skipped / 0 failed; dry-run pilot 48/48
- **v0.9.20 status:** internally trustworthy; no-model target preflight GREEN; superseded for Real Pilot launch by v0.9.21 after the independent audit found the per-cell validation runtime parity blockers (B1 interpreter routing / B2 frozen env discarded / B3 180s timeout below measured runtime)
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
