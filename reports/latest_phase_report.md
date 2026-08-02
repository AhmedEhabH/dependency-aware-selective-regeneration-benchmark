# Pre-Benchmark Final Source Repin — Latest Phase Report

## Executive decision

The pre-benchmark reproducibility-and-truth closure is **complete and green** on
branch `fix/kaggle-smoke-v2-model-output-closure` (HEAD `f8d00d7`, pushed, local
= remote, tree clean). The pre-benchmark test environment is fully declared in
`pyproject.toml [dev]` + `requirements-dev.txt` (commits `769d84e` + `e5d9430`;
runtime `[project.dependencies]` and `requirements-smoke-kaggle.lock` untouched),
the clean environment was deleted and recreated from declarations only (Python
3.11.9, `_workspace\cache\prebenchmark-py311`), and the complete clean gate was
repeated.

The previous `76a6b16` gate had **1 failure, not a green full suite**:
**1,833 passed / 32 skipped / 1 failed**. The sole failure was
`test_notebook_source_commit_matches_deployed_runtime_tree`, structural because
the mandated `pyproject.toml` declaration change broke byte-identity with the
pinned `aac9914` SOURCE_COMMIT (frozen artifacts were not modified to force
green and the truthful total was recorded). **Root cause:** dependency
declarations changing `pyproject.toml` after the `aac9914`/`311e084` deployment
pin. **No runtime, prompt, metric, scenario, evaluator, or data change was
needed.**

The exact independently reviewed **deployment-only correction** `f8d00d7`
(imported via bundle fast-forward, exactly one commit) re-pins the deployment to
the current source snapshot `e5d9430`: bundled `kaggle_upload/code/pyproject.toml`
is now byte-identical to canonical, and both notebooks re-pin
`SOURCE_COMMIT = e5d943065c6f4158c30a1cbbba39436ab2a7a898` /
`DEPLOYED_BUILD_ID = e5d9430` (deployment source snapshot = `e5d9430`;
deployment correction = `f8d00d7`). The complete clean suite is now **green:
1,834 passed / 32 skipped / 0 failed** (the identity test passes). Dataset
Validation 285 passed / 5 skipped (data unchanged); Prompt Validation 158
passed; Pipeline Smoke 220 passed / 12 skipped; Dry Run 9/9 succeeded (exit 0);
Integration PASS; Metric Verification 169 passed; mypy strict Success (77
files); ruff 93 = 93 baseline (0 new); compileall clean; all notebook code cells
compile; bundle build content-identical (147 files / 928,329 bytes); manifests
verified; no cache files in `kaggle_upload`; git diff --check clean; tree clean.
Historical `exp-20260801-210443` produced one failed model-output terminal
record under source `6f88823` — preserved, excluded from the current `e5d9430`
aggregation; current accepted real records = **0/9**; no scientific evidence
exists; no tag; no Pilot; no Kaggle launch. Next: the only action after this
independent audit is the **Kaggle engineering preflight** cell (not the
scientific One-Run cell), after updating the Kaggle code dataset + notebook to
the corrected `e5d9430` deployment.

This report is the current, latest-first post-R6 report. The R6 acceptance,
freeze, and publication detail belongs to
`docs/R6_FINAL_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md` and
`selective_updates/records/R6-BUNDLE-PARITY-AND-PRE-KAGGLE-HANDOFF.md` and is
not repeated here. The prior R7C root-closure report is preserved as history
in `selective_updates/records/KAGGLE-SMOKE-V2-REAL-RUN-ROOT-CLOSURE.md`.

## Models used

```text
Requested model:  DeepSeek V4 Flash Free through OpenCode Zen
Actual model:     opencode/deepseek-v4-flash-free
Mode:             Build
Provider:         OpenCode Zen
```

## Branch and commits

```text
Branch             = fix/kaggle-smoke-v2-model-output-closure (from the deterministic-interpreter tail)
R6 accepted HEAD   = 949e9c2; R6 freeze commit 4b2dd27 (published milestone branch)
Runtime commit     = aac9914  fix(exec): bind Python scenario commands to active runtime
Deployment pin     = 311e084  chore(deploy): pin deterministic-interpreter Smoke V2 bundle
Declaration 1      = 769d84e  chore(test): declare complete pre-benchmark dependencies
Declaration 2      = e5d9430  chore(test): declare remaining pre-benchmark dependencies
Deployment correction = f8d00d7  chore(deploy): repin reproducible pre-benchmark source snapshot (HEAD)
Deployment source = e5d9430 (SOURCE_COMMIT=e5d943065c6f4158c30a1cbbba39436ab2a7a898, DEPLOYED_BUILD_ID=e5d9430)
Failed attempts    = exp-20260801-024041, exp-20260801-024624 (preserved; not deleted)
Latest real attempt = exp-20260801-123125 (FP16 → OOM; deps drifted; not scientific evidence)
Historical experiment = exp-20260801-210443 (ONE failed model-output terminal record under 6f88823;
                          preserved; excluded from current e5d9430 aggregation)
Record             = selective_updates/records/KAGGLE-SMOKE-V2-MODEL-OUTPUT-CLOSURE.md
```

## The failed attempts (truth)

```text
exp-20260801-024041  planned 9 / succeeded 0 / failed 9 / model calls 0 / tokens 0
exp-20260801-024624  planned 9 / succeeded 0 / failed 9 / model calls 0 / tokens 0
exp-20260801-123125  failed at runtime root (FP16 OOM; deps drifted from lock)
```

The first two attempts failed at the first arm/scenario triplet during
workspace **isolation** before any LLM call; the later attempt reached the
model (81 calls, 47,694 tokens) but every record failed selection/validation;
the root-closure attempt failed before any model call at runtime root. None of
these outputs are scientific evidence. They remain visible on the results
dataset and must not be deleted.

## Fix evidence

```text
Pre-benchmark categories (declarations-only recreated environment)  all passed
  Dataset Validation           285 passed / 5 skipped (data unchanged)
  Prompt Validation            158 passed
  Pipeline Smoke               220 passed / 12 skipped
  Dry Run                      scientific-smoke-v2 9/9 succeeded, exit 0
  Integration                  PASS
  Metric Verification          169 passed
Full suite (previous 76a6b16 gate)  1,833 passed / 32 skipped / 1 failed (NOT green)
  sole failure = test_notebook_source_commit_matches_deployed_runtime_tree
                 (structural: mandated pyproject.toml declaration change breaks
                  byte-identity with pinned aac9914 SOURCE_COMMIT; root cause =
                  dependency declarations changing pyproject.toml after the
                  aac9914/311e084 deployment pin; no runtime/prompt/metric/scenario/
                  evaluator/data change needed; frozen artifacts not modified to force
                  green — reported truthfully)
Full suite (after deployment-only correction f8d00d7)  1,834 passed / 32 skipped / 0 failed (GREEN)
  identity test now passes (working-tree pyproject.toml byte-matches pinned
  e5d9430 SOURCE_COMMIT)
Mypy strict src/benchmark      Success: no issues found in 77 source files
Ruff                          93 findings = 76a6b16 baseline (re-exported and re-run;
                              93 = 93) — 0 new findings
Compileall                    clean (exit 0)
Notebook cells                all compile (canonical 7/7 + generated 7/7)
git diff --check              clean
Benchmark data                unchanged
```

## Bundle inventory

```text
code = 90 files; data = 56 files; notebooks = 1; total = 147 files / 928,329 bytes
Builder = scripts/build_upload_bundle.py only; build verified and content-identical
         (manifests code 90 / data 56 / notebook 1; no cache files in kaggle_upload)
```

## Exact gates

```text
git diff --check    clean
Ruff                93 = 93 vs 76a6b16 baseline (0 new)
Mypy strict         Success: no issues found in 77 source files
Compileall          clean
notebook cells      all compile (7/7 canonical + 7/7 generated)
full suite          1,834 passed / 32 skipped / 0 failed (green)
identity test       test_notebook_source_commit_matches_deployed_runtime_tree PASSES
                    (deployment re-pinned to SOURCE_COMMIT=e5d9430 by f8d00d7)
bundle build        content-identical (147 files / 928,329 bytes); manifests verified
```

## Current status

```text
R4 = accepted and frozen (f5ae826)
R5 = accepted and frozen (7761c48)
R6 = ACCEPTED AND FROZEN (949e9c2; freeze commit 4b2dd27; branch published)
Kaggle attempts = 2 (exp-20260801-024041, exp-20260801-024624) — failed pre-model, preserved
Latest real attempt = exp-20260801-123125 (FP16 → OOM; deps drifted) — not scientific evidence
Runtime fixes  = committed (de3163f) and pinned (fb60972) — core accepted by independent audit
R7A hardening  = complete (d50e89e + 4c73db6) — four audit findings closed
R7B Smoke Finish = complete (bff0a82 + 17207bf)
R7C root closure = complete (7a80e53 + f01b8f0) + correction imported (ffa179a + 6d6aa36)
                    + post-gate correction imported (6f88823 + 5797fc0, HEAD 5797fc0, pushed)
Full-gate truth = prior "1,451 full suite" was a SUBSET; true first full suite
                  23 failed / 1,759 passed / 32 skipped; after correction 1,790 passed / 32 skipped / 0 failed;
                  after post-gate correction 1,796 passed / 32 skipped / 0 failed
Deterministic interpreter closure = complete (aac9914 + 311e084) — bare interpreter tokens bound to active runtime
Pre-benchmark reproducibility closure = COMPLETE AND GREEN (769d84e + e5d9430 declarations;
                  deployment-only correction f8d00d7, HEAD f8d00d7, pushed) — previous 76a6b16 gate
                  1,833 passed / 32 skipped / 1 failed (structural notebook-pin identity test, truthful,
                  not forced green); f8d00d7 re-pins deployment to e5d9430; complete clean suite now
                  1,834 passed / 32 skipped / 0 failed; Dataset 285/5 (data unchanged), Prompt 158,
                  Pipeline Smoke 220/12, Dry Run 9/9, Integration PASS, Metric Verification 169;
                  mypy strict Success (77 files); ruff 93 = 93 baseline (0 new)
Historical experiment = exp-20260801-210443 produced ONE failed model-output terminal record under 6f88823 —
                  preserved, excluded from current e5d9430 aggregation
Current real records = 0/9
Local scripted Smoke = 9/9
Bundled CLI dry-run  = 9/9
Real Qwen Smoke      = 0/9
Scientific evidence  = NONE (no real-model success yet)
Tag                  = not created
Pilot                = not authorized
```

## Near goal

Independent audit complete and its exact deployment-only correction applied
(`f8d00d7`, pushed) → the only authorized Kaggle action is the engineering
preflight cell (not the scientific One-Run cell) → update the Kaggle code
dataset + notebook to the corrected `e5d9430` deployment → run the engineering
preflight → one real cell (require 1/9 succeeded) → remaining eight real Qwen
Scientific Smoke V2 records → independent result audit.

## Far goal

Independent real-result audit → stable `v2.0.0-scientific-smoke` tag → freeze
Pilot matrix → Pilot execution → research experiment → statistical analysis →
paper evidence package.

## Next action

**Only Kaggle engineering preflight** after this independent audit (HEAD
`f8d00d7`): update the Kaggle code dataset + notebook to the corrected
`e5d9430` deployment, then run the preflight cell only. Do not relaunch Kaggle,
tag, merge, or force-push beyond that documented preflight step.

PRE_BENCHMARK_FINAL_SOURCE_REPIN_AUDIT_REQUIRED
