# KAGGLE-SMOKE-V2-REAL-RUN-ROOT-CLOSURE — R7C Real-Run Root Closure (R7C)

**Change ID:** KAGGLE-SMOKE-V2-REAL-RUN-ROOT-CLOSURE
**Date:** 2026-08-01
**Branch:** `fix/kaggle-smoke-v2-real-run-root` (from `fix/kaggle-smoke-v2-finish` tail at `fc5c908`)
**Directive:** `..\R7C_REAL_RUN_ROOT_CLOSURE_PACKAGE\02_OPENCODE_R7C_ROOT_CLOSURE_DIRECTIVE.md`
**Status:** IMPLEMENTATION COMPLETE + ROOT CORRECTION IMPORTED — FULL-GATE AUDIT REQUIRED

## Truth

```text
latest real attempt    = exp-20260801-123125 (FP16 → OOM; deps drifted from lock)
scientific evidence    = NONE (not scientific evidence)
R7C implementation     = complete, committed, pushed; exact correction imported (ffa179a + 6d6aa36)
root contracts         = environment memory + prompt contracts closed (lock + int8 + context)
preflight gate         = kaggle_smoke_preflight.v1 (6 checks; exit 0/1; no run side effects)
local scripted         = 9/9 (dry-run scientific-smoke-v2)
true first full suite  = 23 failed / 1,759 passed / 32 skipped (corrected full gate)
full suite after fix   = 1,790 passed / 32 skipped / 0 failed (Windows / Python 3.11.5)
Kaggle relaunch        = BLOCKED until the independent full-gate audit passes
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
stale source identity (notebook now pins `ffa179a` = `ffa179a`).

Current full gate (Windows / Python 3.11.5): full suite = **1,790 passed /
32 skipped / 0 failed**; mypy --strict = 0 issues; compileall = clean; builder
rerun = clean; identity test `test_notebook_source_commit_matches_deployed_runtime_tree`
passes with `SOURCE_COMMIT = ffa179ade389193082ee1a11af4d29e86c351e08` and
`DEPLOYED_BUILD_ID = ffa179a`. Valid real Qwen remains **0/9**; Kaggle remains
**blocked** pending the independent full-gate audit.

One new Ruff finding (ARG004, unused `stage` argument in
`classify_validation_repairability`) is inherent to the reviewed commit: the
correction removed the blanket clause that used `stage`, and the fix cannot be
applied because `src/benchmark/execution/runner.py` and `pyproject.toml` are
byte-identity-locked to `ffa179a` by the deployment identity test. It is
documented, not silently resolved.

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
   OOM/load failures are classified, not retried to death.

## Preflight gate

`src/benchmark/execution/preflight.py` adds `--kaggle-preflight-only` to the
CLI. Exit 0/1 only; no experiment, no RunRecord, no checkpoint.json, no
workspace, no HF state. Checks (schema `kaggle_smoke_preflight.v1`, 6 checks):
dependency version table, baseline staging, `manage.py check`,
`makemigrations --check`, real int8 Qwen load, and VRAM headroom. The notebook
runs this gate before the exec cell; a non-zero exit raises and stops the
session before any model call. Verified locally against a fake model directory:
exit 1 (deps/torch absent locally), baseline stage checks PASS, JSON written,
no checkpoint/workspace created.

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
```

All pushed to `origin/fix/kaggle-smoke-v2-real-run-root`; local/remote equality
verified after each push. Current branch HEAD = `6d6aa36`.

## Notebook cell sequence (directive order)

```text
0 markdown, 1 setup-cell, 2 install-lock-cell, 3 preflight md, 4 preflight-cell,
5 md, 6 secrets-cell, 7 exec-cell, 8 progress-cell, 9 continuous md,
10 continuous-smoke-cell, 11 notes md
```

`install-lock-cell` pip-installs `CODE_DIR / "requirements-smoke-kaggle.lock"`,
verifies `EXPECTED_RUNTIME`, writes `runtime_environment.json`. `secrets-cell`
was moved to after the preflight so auth is loaded only when the environment
and preflight have already passed. All 7 code cells compile (`ast.parse`).

## Gates

```text
Changed-file diagnostics        git diff --check clean (CRLF warnings only)
Ruff on changed files            clean except ARG004 (see correction section;
                                 inherent to reviewed commit, identity-locked)
Mypy --strict src/benchmark      0 issues
Compileall                       clean
Regression gates                 r4-metric-contract + su0010a + su0011 = 119 passed;
                                 preflight 13; runner 41; cli 72; builder 11;
                                 scientific-smoke-v2 production path 41;
                                 bundle preflight 24
Full suite (final gate)          contract-first 1,451 was a SUBSET, not the suite;
                                 true first full suite 23 failed / 1,759 passed / 32 skipped;
                                 after correction 1,790 passed / 32 skipped / 0 failed
Dry-run                          scientific-smoke-v2 9/9 succeeded
Preflight-only (local, fake model) exit 1, 6 checks, no checkpoint/workspace
Builder rerun                    no content diff (deterministic; CRLF warnings only)
```

Pre-existing failures confirmed identical at the pristine base `fc5c908`
(worktree checks), not introduced here: `tests/unit tests/contract` ordering
(unit-first) → 1 asyncio event-loop failure;
`tests/integration/test_su0011_iterative_agent.py` → 8;
`tests/integration/test_su0010a_regeneration.py` → 9
(`TestBoundedRepairAttempts`). Canonical order `tests/contract tests/unit`
passes.

## Next action

Independent full-gate audit of the corrected R7C branch (HEAD `6d6aa36`):
verify the repair classifier, the preflight dependency/version/VRAM/device-map
contracts, the Python 3.12 runtime contract, the notebook source identity, the
exact 23 former failures passing, and the current full gate. Then update the
Kaggle code dataset + notebook, run one real cell, and continue to 9/9. Kaggle
relaunch is blocked until that audit passes. No tag, no merge, no force-push,
no Kaggle relaunch.

R7C_CORRECTION_FULL_GATE_AUDIT_REQUIRED
