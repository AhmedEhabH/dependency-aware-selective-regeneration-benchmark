# Kaggle HF Sync Bundle Validation

Date: 2026-07-24
Git commit: `23ca0bf`
Branch: `main`

## Results

| Check | Status |
|---|---|
| Real benchmark data loads | PASS: 24/24 scenarios, 8 todo, 8 djangocms, 8 saleor, 0 rejected |
| Dry-run smoke execution | PASS: 7/7 runs success=7 failure=0 return=0 |
| Bundled CLI help | PASS: all required flags present |
| Bundle source structure | PASS: correct `src/benchmark/` package level |
| Bundle imports resolve | PASS: benchmark package, submodules load from bundle path |
| Notebook nbformat validation | PASS: 12 cells (7 code + 5 markdown) valid |
| No token printed | PASS: safe message only |
| No GitHub clone | PASS |
| No HF model download | PASS |
| `local_files_only=True` | PASS |
| All outputs cleared | PASS |
| Stale text removed | PASS |
| Corrected text present | PASS |
| `isInternetEnabled: true` | PASS |
| SHA-256 source=bundle | PASS: 73/73 files match |
| Notebook exists in bundle | PASS: `kaggle_upload/notebooks/seven_arm_benchmark.ipynb` |

## Bundle Contents

### Code Dataset

```
kaggle_upload/code/
  seven_arm_benchmark.py
  requirements-kaggle.txt
  pyproject.toml
  configs/
    pilot.yaml
    research.yaml
    smoke.yaml
  src/
    benchmark/
      __init__.py
      checkpoint/
        __init__.py  checkpoint.py  hf_sync.py  package.py  persistence.py  resume.py
      comparison/
        __init__.py  aggregator.py  ground_truth.py
      config/
        __init__.py  loader.py  models.py  validation.py
      core/
        __init__.py  context.py  enums.py  exceptions.py  models.py  protocols.py  registry.py
      evaluation/
        __init__.py  engine.py  metrics.py
      execution/
        __init__.py  budgets.py  isolation.py  pipeline.py  repair.py  runner.py  state_machine.py
      graph/
        __init__.py  builder.py  models.py
      llm/
        __init__.py  base.py  dry_run_backend.py  kaggle_qwen_backend.py  mock_backend.py
      repositories/
        __init__.py  base.py  loader.py  manifest.py  snapshot.py  workspace.py
      scenarios/
        __init__.py  loader.py  models.py  sequencing.py  validator.py
      selection/
        __init__.py  planner.py
      statistics/
        __init__.py  analysis.py  confidence_intervals.py  effect_sizes.py  reporting.py
      strategies/
        __init__.py  agent.py  code_plan.py  compiled_ai.py  delta_mcp.py  incr_rtl.py  monolithic.py  registry.py  selective.py
```

### Notebook

```
kaggle_upload/notebooks/seven_arm_benchmark.ipynb
  12 cells:
    0.  markdown — title and description
    1.  code    — discover datasets, PYTHONPATH, install deps
    2.  code    — GPU and model verification
    3.  code    — HF_TOKEN auth, env vars, verify private repo
    4.  markdown — Session 1 heading
    5.  code    — Session 1: smoke + hf-sync + max-runs 1
    6.  code    — display checkpoint.json, progress.json, run_records.jsonl, remote_sync.json
    7.  markdown — Session 2 heading
    8.  code    — Session 2: resume-from-hf + max-runs 1
    9.  code    — validate completed count=2, no duplicates, distinct run IDs
    10. markdown — notes (corrected stale text)
    11. markdown — disabled profiles notice
```

## Session Commands

### Session 1

```
--profile smoke
--max-runs 1
--hf-sync
--hf-repo-id NabilDo/selective-regeneration-experiment-results
--data-dir <DATA_DIR>
--model-path <MODEL_PATH>
--output-dir /kaggle/working/runs
```

### Session 2

```
--profile smoke
--resume-from-hf
--experiment-id <EXPERIMENT_ID>
--max-runs 1
--hf-sync
--hf-repo-id NabilDo/selective-regeneration-experiment-results
--data-dir <DATA_DIR>
--model-path <MODEL_PATH>
--output-dir /kaggle/working/runs
```

## Optional flags not implemented

The following flags are listed in the specification but do not exist in the
bundled CLI. They are not required for the notebook commands to work:

- `--hf-path-prefix`
- `--hf-sync-every-runs`
- `--hf-private`

## Versioning note

Tag `v0.5.0-kaggle-hf-sync` does not exist in git history. It was described
in a prior session but was never actually created. The stable tag
`v0.7.0-smoke-passed` remains the current release identifier.

---

```
KAGGLE_BUNDLE_READY
```

## Upload instructions

- **Code Dataset upload directory**: `kaggle_upload/code/`
- **Notebook upload file**: `kaggle_upload/notebooks/seven_arm_benchmark.ipynb`
- **Data Dataset update**: NOT required (data files unchanged)
- **Final main commit**: `23ca0bf`
- **Current stable tag**: `v0.7.0-smoke-passed`
- **Accidental auxiliary tag**: `v0.5.0-kaggle-hf-sync` — not in git history; aspirational from prior session
