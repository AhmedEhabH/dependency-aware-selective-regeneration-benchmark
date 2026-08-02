# KAGGLE-SMOKE-V2-MODEL-OUTPUT-CLOSURE — Pre-Benchmark Final Reproducibility and Truth Closure

**Change ID:** KAGGLE-SMOKE-V2-MODEL-OUTPUT-CLOSURE
**Date:** 2026-08-03
**Branch:** `fix/kaggle-smoke-v2-model-output-closure`
**HEAD:** `e5d9430` (declaration commits `769d84e` + `e5d9430` pushed; local = remote; tree clean)
**Status:** PRE-BENCHMARK FINAL REPRODUCIBILITY AUDIT — BOUNDED CLOSURE COMPLETE — INDEPENDENT AUDIT REQUIRED

## Truth

```text
branch                 = fix/kaggle-smoke-v2-model-output-closure
HEAD                   = e5d9430 (pushed; local = remote; working tree clean)
runtime commit         = aac9914  fix(exec): bind Python scenario commands to active runtime
deployment pin         = 311e084  chore(deploy): pin deterministic-interpreter Smoke V2 bundle
declaration commits    = 769d84e + e5d9430 (dependency declarations only; runtime [project.dependencies] untouched)
historical experiment  = exp-20260801-210443 produced ONE failed model-output terminal record under source 6f88823
                         (preserved, not deleted; EXCLUDED from the current aac9914 scientific aggregation)
current aac9914 records = 0/9 (no accepted aac9914 records yet; no scientific evidence)
scientific evidence    = NONE (no real-model success yet)
tag                    = not created
Pilot                  = not authorized
Kaggle                 = not launched (next authorized action = engineering preflight after independent audit)
```

## Directive and scope

This is the bounded reproducibility-and-truth closure for the pre-benchmark
gate. The five steps were: (1) recover the exact dependency versions from the
previously passing environment; (2) declare every dependency needed to recreate
that environment purely from project declarations; (3) delete the environment
and recreate it from the declarations only; (4) repeat the complete clean gate
on the recreated environment; (5) correct the operational documentation to
match the observed truth.

No runtime code, benchmark data, scenarios, prompts, strategies, evaluators,
metrics, notebooks, or `kaggle_upload` content was modified. No manual pip
installs were performed outside the documented install command. No reset,
stash, clean, rebase, amend, force-push, branch creation, merge, or tag.

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

```text
Full suite            = 1,833 passed / 32 skipped / 1 failed (Windows / Python 3.11.9)
Dataset Validation    = PASS (285 passed / 5 skipped)
Prompt Validation     = PASS (158 passed)
Pipeline Smoke        = PASS (220 passed / 12 skipped)
Dry Run               = PASS (scientific-smoke-v2 9/9 succeeded, exit 0)
Integration           = PASS
Metric Verification   = PASS (169 passed)
Benchmark data        = unchanged (no data file modified by this closure)
Mypy --strict src/benchmark = Success: no issues found in 77 source files
Ruff check src tests seven_arm_benchmark.py scripts = 93 findings, IDENTICAL to
                         the 468a23a baseline (verified in a detached worktree:
                         93 = 93) — 0 new findings
Compileall             = clean (exit 0)
Bundle build           = success: 147 files / 928,329 bytes (code 90 files /
                         715,210 bytes; data 56 files / 172,210 bytes;
                         notebook 1 file / 40,909 bytes); no forbidden items;
                         manifests code 90 / data 56 / notebook 1 verified
git diff --check       = clean (LF->CRLF warning on requirements-dev.txt only)
```

The bundle is **+154 bytes** versus the pinned `311e084` bundle (928,175
bytes) because `pyproject.toml` is a canonical code source and the mandated
declaration change is part of it. `kaggle_upload` was regenerated by the
builder only for verification and then restored via
`git checkout -- kaggle_upload/code/pyproject.toml kaggle_upload/code_manifest.json`,
so `kaggle_upload` content is unchanged on the working tree.

## The single failing test — structural, reported truthfully, not forced green

```text
tests/unit/test_cli.py::TestScientificSmokeV1Profile::
    test_notebook_source_commit_matches_deployed_runtime_tree  FAILED
```

The notebook `notebooks/seven_arm_benchmark.ipynb` pins
`SOURCE_COMMIT = aac9914...`, and the identity test requires the working-tree
`pyproject.toml` to byte-match the `pyproject.toml` at commit `aac9914`. The
mandated dependency-declaration change necessarily invalidates that
byte-identity for `pyproject.toml`. Re-pinning the notebook would modify a
frozen notebook artifact and is a deployment action out of scope. Decision:
frozen artifacts were not modified to force a green result; the truthful total
of **1 failed / 1,833 passed / 32 skipped** is recorded here and in the state
documents.

## Historical versus current truth

The historical experiment `exp-20260801-210443` produced **one failed
model-output terminal record** under source commit `6f88823`. It is preserved
and must not be deleted, and it is **excluded** from the current `aac9914`
scientific aggregation. Current accepted `aac9914` records = **0/9**. No real
Qwen record exists; there is no scientific evidence; no tag; no Pilot; no
Kaggle launch.

## Commit ledger

```text
468a23a  docs(state): record deterministic-interpreter clean-env closure   (starting HEAD)
769d84e  chore(test): declare complete pre-benchmark dependencies          (pushed)
e5d9430  chore(test): declare remaining pre-benchmark dependencies         (pushed)
```

All pushed to `origin/fix/kaggle-smoke-v2-model-output-closure`; local = remote
verified after each push. Working tree clean.

## Next action

Independent audit of this closure, then update the Kaggle code dataset +
notebook, then the Kaggle **engineering preflight** cell only (not the
scientific One-Run cell). Do not relaunch Kaggle, tag, merge, or force-push
before that audit passes.

PRE_BENCHMARK_FINAL_REPRODUCIBILITY_AUDIT_REQUIRED
