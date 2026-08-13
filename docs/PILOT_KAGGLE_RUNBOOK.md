# PILOT KAGGLE RUNBOOK — PILOT-EXEC-01

**Status:** READY FOR USE (Gates 9/10 complete; real-launch bundle frozen). Pilot NOT started.
**Branches used:** `fix/pilot-real-launch-closure` (real-launch closure work), then
`main` @ tag `v0.9.2-pilot-exec-ready` (deployment source).
**Execution contract:** `docs/PILOT_EXEC_01_EXECUTION_CONTRACT.md` (frozen
before any real Pilot model result).
**Bundle:** `dist/pilot-kaggle-upload/` + `dist/pilot-kaggle-upload.zip`
+ `.sha256`; built from the closure state (real repo cache: djangocms/saleor
at pinned SHAs, todo embedded) by
`scripts/build_pilot_upload_bundle.py`. `dist/` is gitignored.

> Do NOT upload the historical `kaggle_upload/` bundle (frozen Scientific
> Smoke deployment) as Pilot input. It is stale for the Pilot.

---

## Canonical Gate C deployment shape

Use ONE Kaggle Dataset for the frozen Pilot archive. The dataset must contain
at minimum:

- `pilot-kaggle-upload.zip`
- `pilot-kaggle-upload.zip.sha256`

Do not separately reconstruct code/data datasets by hand. The generic
two-dataset shape (code + data) used by the Scientific Smoke deployment does
NOT apply to the Pilot.

Frozen values (authoritative in
`reports/PILOT_EXEC_01_DEPLOYMENT_FREEZE.md`):

- Source tag: `v0.9.2-pilot-exec-ready` (peeled commit
  `e030be5f4736e22ce40cfa798633b186858b0221`)
- Archive SHA-256:
  `ecb7ea7c85d8bdc527a0384f141b47a1e84ee0b3c3f12b6b8305d880098015f1`
- Model: `Qwen/Qwen2.5-Coder-14B-Instruct`
- Quantization: `bnb-nf4`
- Previously accepted Kaggle model mount candidate:
  `/kaggle/input/models/qwen-lm/qwen2.5-coder/transformers/14b-instruct/1`
  (MUST be verified at runtime, not assumed)
- HF results repository:
  `NabilDo/selective-regeneration-experiment-results`
  (MUST be verified at runtime, not assumed)

The Kaggle preflight MUST verify the model mount and the HF results repo at
runtime instead of assuming them.

---

## 1. Before launching (all must be done first)

1. Confirm the working tree is at tag `v0.9.2-pilot-exec-ready` and
   `reports/PILOT_EXEC_01_DEPLOYMENT_FREEZE.md` records the exact tag->commit
   dereference and the bundle manifest SHA-256s.
2. Confirm `dist/pilot-kaggle-upload.zip.sha256` matches the freeze report.
3. Upload the frozen Pilot archive as ONE Kaggle Dataset containing exactly:
   - `pilot-kaggle-upload.zip`
   - `pilot-kaggle-upload.zip.sha256`
   Use a NEW slug for the Pilot (e.g. `pilot-benchmark-bundle`). The Smoke
   dataset slugs are reserved evidence. Do not create separate code/data
   datasets for the Pilot.
4. Record the actual Kaggle dataset slug, the mounted model path
   (`/kaggle/input/<model-slug>`), and the exact HF results repo ID in the
   launch log BEFORE the first real Pilot cell.

## 2. Notebook cells (first launch)

1. Resolve the attached dataset mount and verify the ZIP SHA-256 equals the
   frozen value above.
2. Extract the ZIP to `/kaggle/working/pilot_bundle`.
3. Verify
   `/kaggle/working/pilot_bundle/pilot_deployment_identity.json`
   (task = `PILOT-EXEC-01`, source tag = `v0.9.2-pilot-exec-ready`).
4. Verify the code/data manifests against the freeze report.
5. Define the bundled paths:
   ```python
   PILOT_CODE = "/kaggle/working/pilot_bundle/code"
   PILOT_DATA = "/kaggle/working/pilot_bundle/data"
   ```
6. Install:
   `!pip install -r /kaggle/working/pilot_bundle/code/requirements-kaggle.txt`
7. Verify GPU (torch.cuda) and report GPU name.
8. Model mount preflight: verify the mounted model path exists (same check as
   Smoke, against the recorded Pilot model path).
9. Bundled dry-run with the bundled code and bundled data (mock, 48 expected
   cells) before any real call:
   ```bash
   python /kaggle/working/pilot_bundle/code/seven_arm_benchmark.py \
       --dry-run \
       --profile pilot \
       --data-dir /kaggle/working/pilot_bundle/data \
       --qwen-quantization bnb-nf4
   ```
10. Model-load preflight (loads model with `--qwen-quantization bnb-nf4`, no
    scientific cells).
11. REAL Pilot launch (below).

## 3. Real Pilot launch (frozen flags)

```bash
python /kaggle/working/pilot_bundle/code/seven_arm_benchmark.py \
    --backend kaggle-qwen \
    --profile pilot \
    --data-dir /kaggle/working/pilot_bundle/data \
    --model-path /kaggle/input/<pilot-model-slug> \
    --qwen-quantization bnb-nf4 \
    --max-attempts 3 \
    --max-completion-tokens-per-call 4096 \
    --max-total-workflow-tokens 0 \
    --timeout 600 \
    --source-commit <40-char SHA from freeze report> \
    --source-tag v0.9.2-pilot-exec-ready \
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
