# KAGGLE-SMOKE-V2-REAL-RUN-ROOT-CLOSURE — R7C Real-Run Root Closure (R7C)

**Change ID:** KAGGLE-SMOKE-V2-REAL-RUN-ROOT-CLOSURE
**Date:** 2026-08-01
**Branch:** `fix/kaggle-smoke-v2-real-run-root` (from `fix/kaggle-smoke-v2-finish` tail at `fc5c908`)
**Directive:** `..\R7C_REAL_RUN_ROOT_CLOSURE_PACKAGE\02_OPENCODE_R7C_ROOT_CLOSURE_DIRECTIVE.md`
**Status:** IMPLEMENTATION COMPLETE — ROOT CONTRACTS CLOSED; INDEPENDENT REAL-RUN ROOT CLOSURE AUDIT REQUIRED

## Truth

```text
latest real attempt    = exp-20260801-123125 (FP16 → OOM; deps drifted from lock)
scientific evidence    = NONE (not scientific evidence)
R7C implementation     = complete, committed, pushed pending independent audit
root contracts         = environment memory + prompt contracts closed (lock + int8 + context)
preflight gate         = kaggle_smoke_preflight.v1 (6 checks; exit 0/1; no run side effects)
local scripted         = 9/9 (dry-run scientific-smoke-v2)
full suite (contract-first) = 1,451 passed / 31 skipped / 0 failed
Kaggle relaunch        = BLOCKED until the independent R7C real-run root closure audit passes
```

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
C = docs     docs(audit): record real-run root closure and int8 preflight
             (this record, SYSTEM_STATE.md, PROJECT_HANDOFF.md, TODO.md,
              CHANGE_INDEX.md, change_metrics.jsonl)
```

All pushed to `origin/fix/kaggle-smoke-v2-real-run-root`; local/remote equality
verified after each push.

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
Ruff on changed files            clean (pre-existing 5 in seven_arm_benchmark.py left)
Mypy --strict src/benchmark      0 issues (6 source files)
Compileall                       clean
Unit batches                     preflight+runner+llm+builder 74 passed;
                                 cli+models 118 passed
Integration                      scientific-smoke-v2 production path 41 passed;
                                 bundle preflight 24 passed (TestKaggleBundleR7CRuntimeClosure)
Full suite (final gate)          contract-first 1,451 passed / 31 skipped / 0 failed
Dry-run                          scientific-smoke-v2 9/9 succeeded
Preflight-only (local, fake model) exit 1, 6 checks, no checkpoint/workspace
Builder rerun                    no diff (deterministic)
```

Pre-existing failures confirmed identical at the pristine base `fc5c908`
(worktree checks), not introduced here: `tests/unit tests/contract` ordering
(unit-first) → 1 asyncio event-loop failure;
`tests/integration/test_su0011_iterative_agent.py` → 8;
`tests/integration/test_su0010a_regeneration.py` → 9
(`TestBoundedRepairAttempts`). Canonical order `tests/contract tests/unit`
passes.

## Next action

Independent audit of the R7C real-run root closure: verify the environment
memory contract (lock + install cell), the int8 memory contract, the frozen
scenario-context prompt contract, and the infrastructure-nonrepairable repair
contract, plus the preflight gate. Then update the Kaggle code dataset +
notebook, run one real cell, and continue to 9/9. Kaggle relaunch is blocked
until that audit passes. No tag, no merge, no force-push, no Kaggle relaunch.

R7C_REAL_RUN_ROOT_CLOSURE_AUDIT_REQUIRED
