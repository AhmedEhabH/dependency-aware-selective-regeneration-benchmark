# KAGGLE-SMOKE-V2-MODEL-OUTPUT-CLOSURE — Pre-Benchmark Final Reproducibility and Truth Closure

**Change ID:** KAGGLE-SMOKE-V2-MODEL-OUTPUT-CLOSURE
**Date:** 2026-08-03
**Branch:** `fix/kaggle-smoke-v2-model-output-closure`
**HEAD:** `f8d00d7` (deployment-only correction, imported via bundle fast-forward from `e5d9430`; pushed; local = remote; tree clean)
**Status:** PRE-BENCHMARK FINAL SOURCE REPIN — DEPLOYMENT CORRECTION APPLIED AND PUSHED — INDEPENDENT AUDIT ACCEPTED — COMPLETE CLEAN SUITE GREEN (1,834 PASSED / 32 SKIPPED / 0 FAILED)

## Truth

```text
branch                 = fix/kaggle-smoke-v2-model-output-closure
HEAD                   = f8d00d7 (pushed; local = remote; working tree clean)
deployment correction  = f8d00d7  chore(deploy): repin reproducible pre-benchmark source snapshot
deployment source      = e5d9430  (SOURCE_COMMIT = e5d943065c6f4158c30a1cbbba39436ab2a7a898;
                                   DEPLOYED_BUILD_ID = e5d9430)
runtime commit         = aac9914  fix(exec): bind Python scenario commands to active runtime
deployment pin         = 311e084  chore(deploy): pin deterministic-interpreter Smoke V2 bundle
declaration commits    = 769d84e + e5d9430 (dependency declarations only; runtime [project.dependencies] untouched)
historical experiment  = exp-20260801-210443 produced ONE failed model-output terminal record under source 6f88823
                         (preserved, not deleted; EXCLUDED from the current e5d9430 scientific aggregation)
current e5d9430 records = 0/9 (no accepted real records yet; no scientific evidence)
scientific evidence    = NONE (no real-model success yet)
tag                    = not created
Pilot                  = not authorized
Kaggle                 = not launched (next authorized action = engineering preflight after independent audit)
```

## Directive and scope

This is the bounded reproducibility-and-truth closure for the pre-benchmark
gate, plus the exact independent audit correction that closed it. The original
five steps were: (1) recover the exact dependency versions from the previously
passing environment; (2) declare every dependency needed to recreate that
environment purely from project declarations; (3) delete the environment and
recreate it from the declarations only; (4) repeat the complete clean gate on
the recreated environment; (5) correct the operational documentation to match
the observed truth. The previous closure recorded the truthful result
**1 failed / 1,833 passed / 32 skipped** — it was NOT a green full suite.

The independent audit then supplied the exact **deployment-only correction**
(`f8d00d7`, imported via bundle fast-forward from `e5d9430`) that re-pins the
deployment to the current source snapshot without any runtime, prompt, metric,
scenario, evaluator, or data change. It is applied verbatim; no rewrite, no
redesign, no alternative implementation.

## Root cause of the single previous failure

The previous `76a6b16` gate had **1 failure, not a green full suite**. Root
cause: the mandated dependency-declaration change altered the canonical
`pyproject.toml` after the `aac9914`/`311e084` deployment pin, breaking
byte-identity between the working-tree `pyproject.toml` and the `pyproject.toml`
at the pinned `aac9914` SOURCE_COMMIT. The notebook-pin identity test
`test_notebook_source_commit_matches_deployed_runtime_tree` necessarily failed.
The prior closure reported this truthfully instead of forcing the frozen
artifacts green.

**No runtime, prompt, metric, scenario, evaluator, or data change was needed.**
The failure was a deployment-pin identity defect only, closed by the
deployment-only correction.

## The deployment-only correction (f8d00d7)

The exact independently reviewed correction (bundle
`PRE_BENCHMARK_FINAL_REPIN_EXACT.bundle`, fetched and fast-forwarded, exactly
one commit) re-pins the deployment to the current source snapshot:

1. **`kaggle_upload/code/pyproject.toml`** gains the six declaration lines
   (`tabulate==0.10.0`, `httpx==0.28.1`, `Jinja2==3.1.6`,
   `pytest-asyncio==1.2.0`, `huggingface_hub==0.24.0`, `types-pyyaml>=6.0,<7`)
   so the bundled `pyproject.toml` is **byte-identical** to the canonical one
   (verified: identical, 1,948 bytes).
2. **Notebook re-pin** in both canonical (`notebooks/seven_arm_benchmark.ipynb`)
   and generated (`kaggle_upload/notebooks/seven_arm_benchmark.ipynb`):
   `SOURCE_COMMIT = e5d943065c6f4158c30a1cbbba39436ab2a7a898`,
   `DEPLOYED_BUILD_ID = e5d9430`.
3. **Manifests** `kaggle_upload/code_manifest.json` and
   `kaggle_upload/notebook_manifest.json` re-verified.

Result: the working-tree `pyproject.toml` now byte-matches the pinned
`e5d9430` SOURCE_COMMIT, and the identity test passes. The deployment source
snapshot is now `e5d9430`; the deployment correction is `f8d00d7`.

No runtime, prompt, metric, scenario, evaluator, or data file was touched.

## Complete clean gate after the correction (prebenchmark-py311, declarations-only environment)

```text
Full suite            = 1,834 passed / 32 skipped / 0 failed (Windows / Python 3.11.9)
Dataset Validation    = PASS (285 passed / 5 skipped); benchmark data unchanged
Prompt Validation     = PASS (158 passed)
Pipeline Smoke        = PASS (220 passed / 12 skipped)
Dry Run               = PASS (scientific-smoke-v2 9/9 succeeded, exit 0)
Integration           = PASS
Metric Verification   = PASS (169 passed)
Mypy --strict src/benchmark = Success: no issues found in 77 source files
Ruff check src tests seven_arm_benchmark.py scripts = 93 findings, IDENTICAL to
                         the 76a6b16 baseline (exported and re-run; 93 = 93) — 0 new findings
Compileall             = clean (exit 0)
Notebook cells         = all compile (canonical 7/7 + generated 7/7)
Bundle build           = success: 147 files / 928,329 bytes (code 90 files / 715,210 bytes;
                         data 56 files / 172,210 bytes; notebook 1 file / 40,909 bytes);
                         builder rerun content-identical; manifests code 90 / data 56 / notebook 1 verified
git diff --check       = clean
git status --short     = clean (no cache files in kaggle_upload)
```

Focused identity gates passed on the correction: the two notebook-pin tests in
`tests/unit/test_cli.py` and the full `tests/unit/test_build_upload_bundle.py`
(13 passed), and every code cell in the canonical and generated notebooks
compiles.

## Step 1 — exact versions recovered from the previously passing environment

```text
tabulate = 0.10.0   httpx = 0.28.1   Jinja2 = 3.1.6
pytest   = 8.4.2    ruff = 0.15.22   mypy = 1.20.2
```

## Step 2 — complete dependency declarations

`[project.optional-dependencies].dev` in `pyproject.toml` and
`requirements-dev.txt` now declare the full pre-benchmark test environment:

```text
Django==5.2.16            djangorestframework==3.17.1
pytest-django==4.12.0     pytest-asyncio==1.2.0
tabulate==0.10.0          httpx==0.28.1
Jinja2==3.1.6             huggingface_hub==0.24.0
types-pyyaml>=6.0,<7      pytest>=8.0,<9
(plus pre-existing ruff, mypy, pytest-cov, jsonschema, pyyaml, click,
 jupyter, nbformat, nbconvert, pre-commit in requirements-dev.txt)
```

Rationale for the exact pins discovered by the declarations-only gate:

- `pytest-asyncio==1.2.0` — required by the `addopts = --asyncio-mode=auto` in
  `pyproject.toml`.
- `huggingface_hub==0.24.0` — the 1.x line made `hf_hub_download` keyword-only
  and removed `local_dir_use_symlinks`, which breaks the positional calls in
  `src/benchmark/checkpoint/hf_sync.py` and fails strict mypy; 0.24.0 provides
  both.
- `types-pyyaml>=6.0,<7` — required for mypy strict `yaml` stubs.

Runtime `[project.dependencies]` in `pyproject.toml` was **not** changed.
`requirements-smoke-kaggle.lock` was **not** changed.

Commits: `769d84e` (`chore(test): declare complete pre-benchmark dependencies`),
`e5d9430` (`chore(test): declare remaining pre-benchmark dependencies`). Both
pushed; local = remote verified.

## Step 3 — environment recreated from declarations only

```text
py -3.11 -m venv ..\_workspace\cache\prebenchmark-py311
python -m pip install --upgrade pip
python -m pip install -e ".[dev]" "pytest==8.4.2" "ruff==0.15.22" "mypy==1.20.2"
```

```text
Python = 3.11.9          pytest = 8.4.2           Django = 5.2.16
DRF    = 3.17.1          pytest-django = 4.12.0   tabulate = 0.10.0
httpx  = 0.28.1          Jinja2 = 3.1.6           ruff = 0.15.22
mypy   = 1.20.2
```

## Step 4 — complete clean gate on the recreated environment

The first full repetition of the gate (previous closure, HEAD `e5d9430`)
produced the truthful **1,833 passed / 32 skipped / 1 failed** result recorded
above. After the deployment-only re-pin (`f8d00d7`), the complete clean gate is
**green**: full suite **1,834 passed / 32 skipped / 0 failed** — the
previously failing notebook-pin identity test now passes because the
working-tree `pyproject.toml` byte-matches the pinned `e5d9430` SOURCE_COMMIT.
All six pre-benchmark validation categories PASS (Dataset 285/5 with data
unchanged, Prompt 158, Pipeline Smoke 220/12, Dry Run 9/9, Integration, Metric
Verification 169); mypy strict Success (77 files); ruff 93 = 93 baseline (0
new); compileall clean; every notebook code cell compiles; bundle build
content-identical (147 files / 928,329 bytes); manifests verified; no cache
files in `kaggle_upload`; `git diff --check` clean; working tree clean.

## Historical versus current truth

The historical experiment `exp-20260801-210443` produced **one failed
model-output terminal record** under source commit `6f88823`. It is preserved
and must not be deleted, and it is **excluded** from the current `e5d9430`
scientific aggregation. Current accepted real records = **0/9**. No real Qwen
record exists; there is no scientific evidence; no tag; no Pilot; no Kaggle
launch.

## Commit ledger

```text
468a23a  docs(state): record deterministic-interpreter clean-env closure   (starting HEAD)
769d84e  chore(test): declare complete pre-benchmark dependencies          (pushed)
e5d9430  chore(test): declare remaining pre-benchmark dependencies         (pushed)
f8d00d7  chore(deploy): repin reproducible pre-benchmark source snapshot   (deployment-only correction, pushed)
```

All pushed to `origin/fix/kaggle-smoke-v2-model-output-closure`; local = remote
verified after each push. Working tree clean.

## Next action

The independent audit has been performed and its exact deployment-only
correction is applied and pushed. **The only next action after this
independent audit is the Kaggle engineering preflight** — the preflight cell
only, not the scientific One-Run cell, and only after updating the Kaggle code
dataset + notebook to the corrected `e5d9430` deployment. Do not relaunch
Kaggle, tag, merge, or force-push beyond the documented preflight step.

PRE_BENCHMARK_FINAL_SOURCE_REPIN_AUDIT_REQUIRED
