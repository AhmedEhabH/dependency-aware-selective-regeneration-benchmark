# PILOT KAGGLE RUNBOOK — PILOT-EXEC-01

**Status:** READY FOR USE (Kaggle filename transport correction merged + tagged
`v0.9.5-pilot-exec-ready`; bundle rebuilt from the exact tag). Pilot NOT started.
**Branches used:** `fix/pilot-kaggle-filename-transport` (Kaggle-safe ZIP
encoding correction), `fix/pilot-kaggle-reserved-transport-name` (reserved
`__name__` transport-root correction), then
`main` @ tag `v0.9.5-pilot-exec-ready` (deployment source).
**Execution contract:** `docs/PILOT_EXEC_01_EXECUTION_CONTRACT.md` (frozen
before any real Pilot model result).
**Bundle:** `dist/pilot-kaggle-upload/` + `dist/pilot-kaggle-upload.zip`
+ `.sha256`; built from the TAGGED SOURCE `v0.9.5-pilot-exec-ready` (real repo
cache: djangocms/saleor at pinned SHAs, todo embedded) by
`scripts/build_pilot_upload_bundle.py`. `dist/` is gitignored. The archive
contains the 18-cell Pilot notebook including the `service-bootstrap-cell`
that provisions PostgreSQL + Valkey/Redis on a fresh Kaggle session AND the
`transport-restore-cell` that makes the ZIP Kaggle-safe.

**Kaggle filename transport (why the ZIP is now safe to upload):** the pinned
upstream repos contain filenames with `[ ] & @ =` (e.g. Saleor cassettes),
which the Kaggle Dataset upload rejects; Kaggle also reserves any path
component matching `^__.*__$`, so the transport root is
`kaggle_transport` (NOT `__kaggle_transport__`). The archive stores such files
under `kaggle_transport/files/<blob>` (names matching `^[A-Za-z0-9._/-]+$` only,
no reserved `__name__` component) with an exact-path map
`kaggle_transport/kaggle_transport_path_map.json` (SHA-256 bound into
`pilot_deployment_identity.json`). A mandatory pre-upload validator scans EVERY
ZIP member and fails closed on any unsafe-special-char or reserved-name
component before the artifact is declared Kaggle-ready. The notebook's
`transport-restore-cell` restores the EXACT original paths/bytes before any
manifest or repository verification. Canonical upstream filenames are NEVER
renamed or deleted — the encoding is ZIP-only and fully reversible.

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
`reports/PILOT_EXEC_01_DEPLOYMENT_FREEZE.md` — updated for the Kaggle
filename transport correction):

- Source tag: `v0.9.5-pilot-exec-ready` (peeled commit recorded in the
  deployment freeze report; previous execution-ready points
  `v0.9.3-pilot-exec-ready` (service bootstrap) and
  `v0.9.2-pilot-exec-ready` @ `e030be5f4736e22ce40cfa798633b186858b0221`
  are historical and NOT moved)
- Archive SHA-256: recorded in the deployment freeze report and in
  `dist/pilot-kaggle-upload.zip.sha256` after the exact tagged rebuild
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

1. Confirm the working tree is at tag `v0.9.5-pilot-exec-ready` and
   `reports/PILOT_EXEC_01_DEPLOYMENT_FREEZE.md` records the exact tag->commit
   dereference and the bundle manifest SHA-256s.
2. Confirm `dist/pilot-kaggle-upload.zip.sha256` matches the freeze report.
   Use the zip + sidecar as ONE frozen unit; never re-zip the folder by hand.
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

0. The notebook runs its `service-bootstrap-cell` after dataset/repo snapshot
   verification and BEFORE the repo-specific preflight / any repository
   validation / any model load. It provisions PostgreSQL `127.0.0.1:5433`
   (role/db `saleor/saleor@saleor`) and Valkey/Redis `127.0.0.1:6379`
   (persistence disabled) idempotently, installing OS packages via apt-get
   when the services are absent. This requires the Kaggle notebook to have
   **Internet ENABLED** (the cell fails loudly, never silently, if the OS
   install is needed and offline). Model loading itself remains offline.
   Prints `SALEOR VALIDATION SERVICE BOOTSTRAP: PASSED` on success; any
   install/startup/health failure STOPS the run before validation/model load.
1. Resolve the attached dataset mount and verify the ZIP SHA-256 equals the
   frozen value above.
2. Extract the ZIP to `/kaggle/working/pilot_bundle`.
3. Run the notebook's `transport-restore-cell`: it verifies
   `kaggle_transport_path_map.json` SHA-256 against the identity and restores
   every transport-encoded canonical repository filename from
   `kaggle_transport/files/` back to its EXACT original path (rejects
   traversal/drive/`..` destinations, destination collisions, missing blobs,
   and any leftover blob), then removes `kaggle_transport/`. This happens
   BEFORE any manifest or repository verification. Canonical upstream
   filenames are never renamed — the ZIP is Kaggle-safe (zero unsafe member
   names under `^[A-Za-z0-9._/-]+$` and zero reserved `__name__` components)
   because unsafe names ride in the transport directory until this cell
   restores them.
4. Verify
   `/kaggle/working/pilot_bundle/pilot_deployment_identity.json`
   (task = `PILOT-EXEC-01`, source tag = `v0.9.5-pilot-exec-ready`).
6. Verify the code/data manifests against the freeze report.
7. Define the bundled paths:
   ```python
   PILOT_CODE = "/kaggle/working/pilot_bundle/code"
   PILOT_DATA = "/kaggle/working/pilot_bundle/data"
   ```
8. Install:
   `!pip install -r /kaggle/working/pilot_bundle/code/requirements-kaggle.txt`
9. Verify GPU (torch.cuda) and report GPU name.
10. Model mount preflight: verify the mounted model path exists (same check as
    Smoke, against the recorded Pilot model path).
11. Bundled dry-run with the bundled code and bundled data (mock, 48 expected
    cells) before any real call:
    ```bash
    python /kaggle/working/pilot_bundle/code/seven_arm_benchmark.py \
        --dry-run \
        --profile pilot \
        --data-dir /kaggle/working/pilot_bundle/data \
        --qwen-quantization bnb-nf4
    ```
12. Model-load preflight (loads model with `--qwen-quantization bnb-nf4`, no
    scientific cells).
13. REAL Pilot launch (below).

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
    --source-tag v0.9.5-pilot-exec-ready \
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
