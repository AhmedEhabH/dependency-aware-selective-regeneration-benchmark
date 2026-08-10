# PILOT KAGGLE RUNBOOK — PILOT-EXEC-01

**Status:** READY FOR USE (Gate B). Pilot NOT started.
**Branches used:** `experiment/pilot-exec-01` (deployment work), then
`main` @ tag `v0.9.1-pilot-exec-ready` (deployment source).
**Execution contract:** `docs/PILOT_EXEC_01_EXECUTION_CONTRACT.md` (frozen
before any real Pilot model result).
**Bundle:** `dist/pilot-kaggle-upload/` + `dist/pilot-kaggle-upload.zip`
+ `.sha256`; built from the tagged source by
`scripts/build_pilot_upload_bundle.py`. `dist/` is gitignored.

> Do NOT upload the historical `kaggle_upload/` bundle (frozen Scientific
> Smoke deployment) as Pilot input. It is stale for the Pilot.

---

## 1. Before launching (all must be done first)

1. Confirm the working tree is at tag `v0.9.1-pilot-exec-ready` and
   `reports/PILOT_EXEC_01_DEPLOYMENT_FREEZE.md` records the exact tag->commit
   dereference and the bundle manifest SHA-256s.
2. Confirm `dist/pilot-kaggle-upload.zip.sha256` matches the freeze report.
3. Upload the bundle to Kaggle as the Pilot datasets:
   - **code dataset** — contents of `dist/pilot-kaggle-upload/code/` (root:
     `seven_arm_benchmark.py`, `src/benchmark/`, `configs/pilot.yaml`,
     `pyproject.toml`, `requirements-kaggle.txt`)
   - **data dataset** — contents of `dist/pilot-kaggle-upload/data/`
     (`benchmark_data/scenarios/`, `benchmark_data/manifests/`,
     `benchmark_data/repository_profiles/`)
   - Use NEW slug names for the Pilot (e.g. `pilot-benchmark-code` and
     `pilot-benchmark-data`). The Smoke dataset slugs are reserved evidence.
4. Record the actual Kaggle dataset slugs and the mounted model path
   (`/kaggle/input/<model-slug>`) and the exact HF results repo ID in the
   launch log BEFORE the first real Pilot cell.

## 2. Notebook cells (first launch)

- Cell 1 — install: `!pip install -r /kaggle/input/<pilot-code-slug>/requirements-kaggle.txt`
- Cell 2 — verify GPU (torch.cuda) and report GPU name.
- Cell 3 — model mount preflight: verify the mounted model path exists
  (same check as Smoke, against the recorded Pilot model path).
- Cell 4 — runtime identity preflight: print the dataset mount layout and
  the frozen identity file
  `/kaggle/input/<pilot-code-slug>/pilot_deployment_identity.json`
  (task = `PILOT-EXEC-01`, source tag = `v0.9.1-pilot-exec-ready`).
- Cell 5 — dry-run on the bundled code with the bundled data (mock, 48
  expected cells) before any real call.
- Cell 6 — model-load preflight (loads model with
  `--qwen-quantization bnb-nf4`, no scientific cells).
- Cell 7 — REAL Pilot launch (below).

## 3. Real Pilot launch (frozen flags)

```bash
python /kaggle/input/<pilot-code-slug>/seven_arm_benchmark.py \
    --backend kaggle-qwen \
    --profile pilot \
    --data-dir /kaggle/input/<pilot-data-slug> \
    --model-path /kaggle/input/<pilot-model-slug> \
    --qwen-quantization bnb-nf4 \
    --max-attempts 3 \
    --max-completion-tokens-per-call 4096 \
    --max-total-workflow-tokens 0 \
    --timeout 600 \
    --source-commit <40-char SHA from freeze report> \
    --source-tag v0.9.1-pilot-exec-ready \
    --output-dir /kaggle/working/runs/pilot-<experiment-id> \
    --hf-sync \
    --hf-repo-id <exact HF results repo id> \
    --new-experiment
```

- One continuous 48-cell session. No `--max-runs` subsetting for the Pilot.
- Every real/resume/preflight invocation MUST pass
  `--qwen-quantization bnb-nf4` explicitly (generic CLI default is `bnb-int8`).

## 4. Resume (external interruption only)

Same flags minus `--new-experiment`, adding `--resume-from-hf`; identical
experiment id / output-dir / model / source commit / quantization. Never
`--new-experiment` on resume.

## 5. Completion

- All 48 scientific cells must be terminal before Pilot success is claimed.
- Download the full `runs/` artifact (run_records.jsonl, checkpoint,
  benchmark_summary.json, COMPLETED marker, benchmark-results.zip,
  remote_sync.json) and move under `reports/results/` in the repo.
- Then freeze the Main-study per-run budgets from measured Pilot
  distributions (never before the Pilot results audit).
