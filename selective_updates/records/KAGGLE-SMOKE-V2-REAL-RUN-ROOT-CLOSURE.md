# KAGGLE-SMOKE-V2-REAL-RUN-ROOT-CLOSURE — R7C Real-Run Root Closure (R7C)

**Change ID:** KAGGLE-SMOKE-V2-REAL-RUN-ROOT-CLOSURE
**Date:** 2026-08-01
**Branch:** `fix/kaggle-smoke-v2-real-run-root` (from `fix/kaggle-smoke-v2-finish` tail at `fc5c908`)
**Directive:** `..\R7C_REAL_RUN_ROOT_CLOSURE_PACKAGE\02_OPENCODE_R7C_ROOT_CLOSURE_DIRECTIVE.md`
**Status:** IMPLEMENTATION COMPLETE + ROOT CORRECTION IMPORTED + POST-GATE CORRECTION IMPORTED — FINAL FULL-GATE AUDIT REQUIRED

## Truth

```text
latest real attempt    = exp-20260801-123125 (FP16 → OOM; deps drifted from lock)
scientific evidence    = NONE (not scientific evidence; no real-model success yet)
R7C implementation     = complete, committed, pushed; exact correction imported (ffa179a + 6d6aa36)
post-gate correction   = independent audit on 5e47a1e; exact correction imported (6f88823 + 5797fc0, HEAD 5797fc0)
root contracts         = environment memory + prompt contracts closed
preflight gate         = kaggle_smoke_preflight.v1 (6 checks; exit 0/1; no run side effects)
local scripted         = 9/9 (dry-run scientific-smoke-v2)
true first full suite  = 23 failed / 1,759 passed / 32 skipped (corrected full gate)
full suite after fix   = 1,790 passed / 32 skipped / 0 failed (Windows / Python 3.11.5)
full suite after post-gate fix = 1,796 passed / 32 skipped / 0 failed (Windows / Python 3.11.5)
Kaggle relaunch        = BLOCKED until the final independent full-gate audit passes
next authorized Kaggle action = engineering preflight cell only (not the scientific One-Run cell)
```

## Correction of prior R7C full-gate truth

The prior R7C report incorrectly called a **1,451-test subset the full suite**.
The true first full suite was **23 failed / 1,759 passed / 32 skipped**. The
root cause of the 23 failures was the blanket
`baseline_validation => infrastructure_nonrepairable` classification in
`src/benchmark/execution/runner.py`, which classified every normal baseline
test failure as infrastructure so the repair loop never ran.

An independent GPT-5.6 Thinking audit implemented and tested the exact
correction as two commits imported via bundle fast-forward:

```text
ffa179a  fix(kaggle): correct repair and preflight contracts
6d6aa36  chore(deploy): pin corrected R7C preflight bundle
```

The exact 23 former failures now pass. The correction also fixed: DRF import
mapping (`djangorestframework` distribution → `rest_framework` module), exact
version verification (not only `NOT_INSTALLED`), fail-fast preflight (stops
before any model load), driver-level VRAM (`torch.cuda.mem_get_info()`), CPU/
disk-offload rejection (non-empty device map without CPU/disk offload), the
Python 3.12 runtime contract (`>=3.11,<3.13`; preflight accepts 3.11/3.12), and
stale source identity (notebook then pinned `ffa179a` = `ffa179a`).

## Independent post-gate audit (on `5e47a1e`) and its exact correction

An independent post-gate audit was performed on `5e47a1e` and found three
remaining issues:

1. **Project-local `ImportError` incorrectly bypassed repair.** The prior
   blanket marker match in `_is_repairable_failure` returned non-repairable for
   any `modulenotfounderror`/`no module named`/`importerror`/`cannot import
   name` message, so a project-local missing module was classified as
   infrastructure instead of being repaired.
2. **Bundled preflight could not import `benchmark` without ambient
   `PYTHONPATH`.** The deployed script failed with `No module named 'benchmark'`
   in a clean subprocess.
3. **Preflight output was buffered.** The preflight gate produced no live,
   persisted output.

The exact correction was imported via bundle fast-forward as two commits:

```text
6f88823  fix(kaggle): align repair eligibility and script bootstrap
5797fc0  chore(deploy): pin audited preflight and live gate
```

What changed:

- **Repair eligibility aligned with the canonical classifier.** The blanket
  marker match is replaced by `classify_validation_repairability`, so a
  project-local `ModuleNotFoundError` and a generated `cannot import name` are
  **repairable**, while a missing declared Django dependency and CUDA OOM remain
  `infrastructure_nonrepairable` (proven by the new
  `RepairEligibilityUsesCanonicalClassifier` boundary test).
- **Bundled script bootstrap.** `seven_arm_benchmark.py` (root and bundled)
  inserts its own `src/` onto `sys.path` at startup when present, so the
  deployed CLI reaches its preflight in a clean subprocess without ambient
  `PYTHONPATH` (proven by `test_bundled_cli_bootstraps_src_without_ambient_pythonpath`).
- **Preflight live output.** Preflight output is streamed and persisted (proven
  by `preflight_streams_with_deployed_pythonpath`).
- **Source identity pinned.** Notebook `SOURCE_COMMIT = 6f88823`,
  `DEPLOYED_BUILD_ID = 6f88823` (proven by
  `test_notebook_source_commit_matches_deployed_runtime_tree`).

Current full gate (Windows / Python 3.11.5): full suite = **1,796 passed /
32 skipped / 0 failed**; ruff 0 new versus `5e47a1e` (93 = 93; the 6 findings
on changed files — ARG004 in runner.py, ARG001×2/E501/SIM102/SIM113 in
seven_arm_benchmark.py — all reproduce at `5e47a1e` with the same rule and file,
lines shifted exactly +6 by the added SRC_ROOT block); mypy --strict = 0 issues;
compileall = clean; notebook code cells 7/7 compile (canonical + generated);
builder rerun = content-identical (byte-hash equal; CRLF warnings only); bundle
manifests verified OK. Notebook source identity test passes with
`SOURCE_COMMIT = 6f88823b8395ed72c8b93d1421ffe093e472e856` and
`DEPLOYED_BUILD_ID = 6f88823`. Valid real Qwen remains **0/9**; no scientific
evidence exists yet; Kaggle remains **blocked** pending the final independent
full-gate audit. The next authorized Kaggle action after that audit is the
**engineering preflight cell only**, not the scientific One-Run cell.

## Root contract (from the failed real run)

The post-R7B real attempt `exp-20260801-123125` failed at runtime root before
any scientific value. The R7C directive names four root contracts the failure
exposed, each closed here:

1. **Environment memory — exact runtime pins** (`requirements-smoke-kaggle.lock`).
   The Kaggle session no longer matched the previously assumed runtime:
   Django==5.2.16, djangorestframework==3.17.1, pytest==8.4.2,
   pytest-django==4.12.0, accelerate==1.14.0, bitsandbytes==0.49.2.
   torch/transformers are intentionally **not** pinned (the Kaggle image
   provides them; pinning them would fight the image). The notebook installs
   this lock first and verifies `EXPECTED_RUNTIME` via `RUNTIME_ATTR`
   (`get_version`/`VERSION`/`__version__`), then writes
   `runtime_environment.json` (schema `kaggle_runtime_environment.v1`) under
   `OUTPUT_DIR.parent/"environment"`.
2. **Memory contract — int8 default.** The FP16 model exceeded GPU memory.
   Default model identity is now `qwen:1:int8`; `PYTORCH_ALLOC_CONF=expandable_segments:True`;
   `run_probe` seeds `torch.manual_seed(0)` for 64 deterministic tokens; the
   preflight enforces ≥2.0 GiB VRAM headroom after a real int8 load. No 4-bit
   fallback was added.
3. **Prompt contract — frozen scenario context.** `RegenerationScenarioContext`
   (repo identity, change, expected actions, blast radius, integrity rules) is
   frozen into the strategy prompts and is never part of the LLM output; when
   `expected_actions` is non-empty the preserved bytes must equal the originals
   (preserve-only enforcement).
4. **Repair contract — infrastructure-aware classification.**
   `FailureKind.infrastructure_nonrepairable` is applied on the first failure,
   running the strategy exactly once with zero LLM repair attempts, so
   OOM/load failures are classified, not retried to death. Repair **eligibility**
   is decided by the canonical `classify_validation_repairability` classifier
   (post-gate correction), so project-local import failures are repairable.

## Preflight gate

`src/benchmark/execution/preflight.py` adds `--kaggle-preflight-only` to the
CLI. Exit 0/1 only; no experiment, no RunRecord, no checkpoint.json, no
workspace, no HF state. Checks (schema `kaggle_smoke_preflight.v1`, 6 checks):
dependency version table, baseline staging, `manage.py check`,
`makemigrations --check`, real int8 Qwen load, and VRAM headroom. The notebook
runs this gate before the exec cell; a non-zero exit raises and stops the
session before any model call. Verified locally against a fake model directory:
exit 1 (deps/torch absent locally), baseline stage checks PASS, JSON written,
no checkpoint/workspace created. Post-gate: the bundled script now bootstraps
its own `src/` (clean-subprocess proof), and preflight output is streamed and
persisted.

## Commits

```text
A = 7a80e53  fix(kaggle): close environment memory and prompt contracts
             (lock, deps, CLI, preflight, int8 backend, runner classification,
             scenario context, tests)
B = f01b8f0  chore(deploy): pin preflighted int8 Smoke V2 bundle
             (notebook install-lock + preflight gate cells + secrets reorder,
              bundle rebuilt; 147 files / 894,735 bytes; notebook 36,351 bytes)
C = a4e9186  (previous R7C HEAD — published but broken: blanket baseline
             classification caused 23 full-suite failures)
D = ffa179a  fix(kaggle): correct repair and preflight contracts
             (independent GPT-5.6 Thinking audit; imported via bundle fast-forward)
E = 6d6aa36  chore(deploy): pin corrected R7C preflight bundle
             (SOURCE_COMMIT=ffa179a, DEPLOYED_BUILD_ID=ffa179a)
F = 5e47a1e  docs(audit): correct R7C full-gate and deployment truth
             (independent post-gate audit baseline)
G = 6f88823  fix(kaggle): align repair eligibility and script bootstrap
             (independent post-gate audit; imported via bundle fast-forward)
H = 5797fc0  chore(deploy): pin audited preflight and live gate
             (SOURCE_COMMIT=6f88823, DEPLOYED_BUILD_ID=6f88823; HEAD)
```

All pushed to `origin/fix/kaggle-smoke-v2-real-run-root`; local/remote equality
verified after each push. Current branch HEAD = `5797fc0`.

## Notebook cell sequence (directive order)

```text
0 markdown, 1 setup-cell, 2 install-lock-cell, 3 preflight md, 4 preflight-cell,
5 md, 6 secrets-cell, 7 exec-cell, 8 progress-cell, 9 continuous md,
10 continuous-smoke-cell, 11 notes md
```

`install-lock-cell` pip-installs `CODE_DIR / "requirements-smoke-kaggle.lock"`,
verifies `EXPECTED_RUNTIME`, writes `runtime_environment.json`. `secrets-cell`
was moved to after the preflight so auth is loaded only when the environment
and preflight have already passed. All 7 code cells compile (`ast.parse` and
full `py_compile`).

## Gates

```text
Changed-file diagnostics        git diff --check clean (CRLF warnings only)
Ruff on changed files            6 findings all reproduced at 5e47a1e with the same
                                 rule + file (ARG004 runner.py:642; ARG001 x2, E501,
                                 SIM102, SIM113 seven_arm_benchmark.py; lines shifted
                                 +6 by the added SRC_ROOT block) — 0 new
Ruff full tree                   93 findings = 93 at 5e47a1e (identical rule+file sets)
Mypy --strict src/benchmark      0 issues
Compileall                       clean
Notebook cells                   canonical + generated 7/7 code cells compile
Boundary regressions             runner eligibility 4; bundle bootstrap 1; cli 2 = 7 passed
Focused gates                    runner 45; cli+builder 84; r4 33; su0010a 61;
                                 su0011 25; bundle preflight 25; production-path 41
Full suite (final gate)          contract-first 1,451 was a SUBSET, not the suite;
                                 true first full suite 23 failed / 1,759 passed / 32 skipped;
                                 after correction 1,790 passed / 32 skipped / 0 failed;
                                 after post-gate correction 1,796 passed / 32 skipped / 0 failed
Dry-run                          scientific-smoke-v2 9/9 succeeded
Preflight-only (local, fake model) exit 1, 6 checks, no checkpoint/workspace
Builder rerun                    content-identical (byte-hash equal; CRLF warnings only)
Bundle manifests                 verified OK (code / data / notebook)
```

Pre-existing failures confirmed identical at the pristine base `fc5c908`
(worktree checks), not introduced here: `tests/unit tests/contract` ordering
(unit-first) → 1 asyncio event-loop failure;
`tests/integration/test_su0011_iterative_agent.py` → 8;
`tests/integration/test_su0010a_regeneration.py` → 9
(`TestBoundedRepairAttempts`). Canonical order `tests/contract tests/unit`
passes.

## Next action

Final independent full-gate audit of the corrected R7C branch (HEAD `5797fc0`):
verify the repair-eligibility classifier, the bundled clean-subprocess preflight
bootstrap, preflight live streaming, the boundary regressions, the notebook
source identity, and the complete full suite. After that audit passes, the only
authorized Kaggle action is the **engineering preflight cell** — not the
scientific One-Run cell. Then update the Kaggle code dataset + notebook, run one
real cell, and continue to 9/9. Kaggle relaunch is blocked until that final
audit passes. No tag, no merge, no force-push, no Kaggle relaunch.

R7C_POST_AUDIT_FULL_GATE_REQUIRED
