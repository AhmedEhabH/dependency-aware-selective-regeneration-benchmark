# Pre-Benchmark Final Reproducibility Audit Closure — Latest Phase Report

## Executive decision

The pre-benchmark reproducibility-and-truth closure is **complete** on branch
`fix/kaggle-smoke-v2-model-output-closure` (HEAD `e5d9430`, pushed, local =
remote, tree clean). The pre-benchmark test environment is now fully declared
in `pyproject.toml [dev]` + `requirements-dev.txt` (commits `769d84e` +
`e5d9430`; runtime `[project.dependencies]` and `requirements-smoke-kaggle.lock`
untouched), the clean environment was deleted and recreated from declarations
only (Python 3.11.9, `_workspace\cache\prebenchmark-py311`), and the complete
clean gate was repeated. Result: full suite = **1,833 passed / 32 skipped /
1 failed**. The sole failure is
`test_notebook_source_commit_matches_deployed_runtime_tree`: the mandated
`pyproject.toml` declaration change breaks byte-identity with the pinned
`aac9914` SOURCE_COMMIT; frozen artifacts were not modified to force green and
the truthful total is recorded. Dataset Validation 285 passed / 5 skipped;
Prompt Validation 158 passed; Pipeline Smoke 220 passed / 12 skipped; Dry Run
9/9 succeeded (exit 0); Integration PASS; Metric Verification 169 passed;
mypy strict Success (77 files); ruff 93 findings = 468a23a baseline (0 new);
compileall clean; bundle build verified (147 files / 928,329 bytes) then
`kaggle_upload` restored unchanged; git diff --check clean; tree clean.
Historical `exp-20260801-210443` produced one failed model-output terminal
record under source `6f88823` — preserved, excluded from the current `aac9914`
aggregation; current accepted `aac9914` records = **0/9**; no scientific
evidence exists; no tag; no Pilot; no Kaggle launch. Next: independent audit
(`PRE_BENCHMARK_FINAL_REPRODUCIBILITY_AUDIT_REQUIRED`), then update the Kaggle
code dataset + notebook, then the Kaggle **engineering preflight** cell only
(not the scientific One-Run cell).

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
Declaration 2      = e5d9430  chore(test): declare remaining pre-benchmark dependencies (HEAD)
Failed attempts    = exp-20260801-024041, exp-20260801-024624 (preserved; not deleted)
Latest real attempt = exp-20260801-123125 (FP16 → OOM; deps drifted; not scientific evidence)
Historical experiment = exp-20260801-210443 (ONE failed model-output terminal record under 6f88823;
                          preserved; excluded from current aac9914 aggregation)
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

## What the R7B Smoke Finish changed

- **Strict output normalization** (`src/benchmark/llm/output_normalization.py`):
  single-fenced JSON object extraction with regex fallback when `ast.parse`
  fails; empty/partial responses fail closed (fixes 0% normalization coverage).
- **Kaggle Qwen backend** (`kaggle_qwen_backend.py`): Qwen chat-template token
  counting, deterministic single-`json.loads` parsing, `inference_mode()` +
  best-effort CUDA cache cleanup after every generation (success, OOM,
  other-exception), one shared backend instance per process (single model
  initialization).
- **Progress + cross-session ETA** (`seven_arm_benchmark.py`):
  `_render_progress_line` per run; `_estimate_run_eta` from the persisted
  ledger; `RUN`/`STAGE`/`REGEN`/`HF` structured log events.
- **Deterministic dashboard** (`checkpoint/reports.py`
  `write_dashboard_artifacts`): `dashboard_summary.json`, `run_matrix.csv`,
  `strategy_summary.csv`, `failure_summary.csv` under `OUTPUT_DIR/dashboard`,
  allowlisted for HF recovery (`checkpoint/hf_sync.py`).
- **Smoke-only cap** (`configs/smoke.yaml`): `max_completion_tokens_per_call: 1024`.
- **Notebook rewrite** (`notebooks/seven_arm_benchmark.ipynb`, pinned to
  `bff0a82`): `_run_benchmark_live` (Popen streaming, stderr→stdout,
  `kaggle_console.log`), `_load_smoke_evidence`, `_display_smoke_dashboard`,
  `_raise_actionable_smoke_error` + `ScientificSmokeExecutionError`,
  `_validate_continuous_precondition`, executable `max-runs 1` exec cell +
  guarded continuous cell.

## Fix evidence

```text
Pre-benchmark categories (declarations-only recreated environment)  all passed
  Dataset Validation           285 passed / 5 skipped
  Prompt Validation            158 passed
  Pipeline Smoke               220 passed / 12 skipped
  Dry Run                      scientific-smoke-v2 9/9 succeeded, exit 0
  Integration                  PASS
  Metric Verification          169 passed
Full suite (repeated clean gate)  1,833 passed / 32 skipped / 1 failed
  sole failure = test_notebook_source_commit_matches_deployed_runtime_tree
                 (structural: mandated pyproject.toml declaration change breaks
                  byte-identity with pinned aac9914 SOURCE_COMMIT; frozen
                  artifacts not modified to force green — reported truthfully)
Mypy strict src/benchmark      Success: no issues found in 77 source files
Ruff                          93 findings = 468a23a baseline (verified in a
                              detached worktree; 93 = 93) — 0 new findings
Compileall                    clean (exit 0)
git diff --check              clean (LF->CRLF warning on requirements-dev.txt only)
Benchmark data                unchanged
```

## Bundle inventory

```text
code = 90 files; data = 56 files; notebooks = 1; total = 147 files / 928,329 bytes
Builder = scripts/build_upload_bundle.py only; build verified (no forbidden items;
         manifests code 90 / data 56 / notebook 1) then kaggle_upload restored via
         git checkout -- kaggle_upload/code/pyproject.toml kaggle_upload/code_manifest.json
(+154 bytes vs the pinned 311e084 bundle because pyproject.toml is a canonical code
 source and the mandated declaration change is part of it; kaggle_upload content unchanged)
```

## Exact gates

```text
git diff --check    clean
Ruff                93 = 93 vs 468a23a baseline (0 new)
Mypy strict         Success: no issues found in 77 source files
Compileall          clean
notebook cells      unchanged (7/7 compile as pinned)
full suite          1,833 passed / 32 skipped / 1 failed (structural notebook-pin test, not forced green)
identity test       test_notebook_source_commit_matches_deployed_runtime_tree FAILS
                    (structural — pinned SOURCE_COMMIT=aac9914 requires byte-identity
                     pyproject.toml; mandated declaration change breaks it; truthful total recorded)
bundle build        verified (147 files / 928,329 bytes) then kaggle_upload restored
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
Pre-benchmark reproducibility closure = COMPLETE (769d84e + e5d9430, HEAD e5d9430, pushed) —
                  deps fully declared; clean env recreated from declarations only; repeated full gate
                  1,833 passed / 32 skipped / 1 failed (sole failure = notebook-pin identity test, structural,
                  not forced green); Dataset 285/5, Prompt 158, Pipeline Smoke 220/12, Dry Run 9/9,
                  Integration PASS, Metric Verification 169; mypy strict Success (77 files); ruff 93 = 93 baseline (0 new)
Historical experiment = exp-20260801-210443 produced ONE failed model-output terminal record under 6f88823 —
                  preserved, excluded from current aac9914 aggregation
Current aac9914 records = 0/9
Local scripted Smoke = 9/9
Bundled CLI dry-run  = 9/9
Real Qwen Smoke      = 0/9
Scientific evidence  = NONE (no real-model success yet)
Tag                  = not created
Pilot                = not authorized
```

## Near goal

Independent audit of the pre-benchmark reproducibility closure (HEAD `e5d9430`)
→ after it passes, update the Kaggle code dataset + notebook → the only
authorized Kaggle action is the engineering preflight cell (not the scientific
One-Run cell) → one real cell (require 1/9 succeeded) → remaining eight real
Qwen Scientific Smoke V2 records → independent result audit.

## Far goal

Independent real-result audit → stable `v2.0.0-scientific-smoke` tag → freeze
Pilot matrix → Pilot execution → research experiment → statistical analysis →
paper evidence package.

## Next action

**Independent pre-benchmark reproducibility audit (HEAD `e5d9430`).** Do not
relaunch Kaggle, tag, merge, or force-push before that audit passes.

PRE_BENCHMARK_FINAL_REPRODUCIBILITY_AUDIT_REQUIRED
