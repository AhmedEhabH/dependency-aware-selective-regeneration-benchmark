# Hugging Face Results Persistence

## Purpose

Automatic checkpoint synchronization to a private Hugging Face Dataset repository after every benchmark run. Enables free Kaggle session termination and resumption without losing progress.

## Remote Repository

- **ID:** `NabilDo/selective-regeneration-experiment-results`
- **Type:** Dataset (private)
- **Visibility verified at runtime** before upload

## Authentication

- **Source:** `HF_TOKEN` from Kaggle Secrets or environment variable
- **Never printed, logged, serialized, committed, or included in exception messages**
- Read-only at runtime via `os.environ.get("HF_TOKEN", "")`

## Remote Layout

```
experiments/
  <profile>/
    <protocol-version>/
      <source-tag-or-commit>/
        <experiment-id>/
          recovery/                    ← updated every run
            run_records.jsonl
            checkpoint.json
            progress.json
            benchmark_summary.partial.json
            remote_sync.json
          snapshots/
            chunk-0001/                ← immutable after creation
              benchmark-results-chunk-0001.zip
              MANIFEST.json
            chunk-0002/
              ...
          final/                       ← written on completion
            benchmark-results.zip
            MANIFEST.json
```

## Per-Run Sync Sequence

1. Run completes or fails
2. RunRecord appended locally and flushed
3. checkpoint.json updated atomically
4. progress.json updated
5. Recovery files uploaded to `recovery/` on Hugging Face
6. Every 2 runs: immutable chunk snapshot uploaded to `snapshots/chunk-NNNN/`
7. On completion: final snapshot + final ZIP uploaded

## Failure Handling

- **Local checkpoint always written before remote upload**
- Remote failure does not corrupt local files
- Bounded exponential backoff: `delay = base_delay * 2^attempt` (max 3 retries)
- On persistent failure: `remote_sync_failure.json` written locally
- Benchmark execution continues if local checkpoint is intact

## Security Filter (Allowlist)

Only the following file patterns are uploaded:

- `run_records.jsonl`
- `checkpoint.json`
- `progress.json`
- `benchmark_summary*`
- `MANIFEST.json`, `manifest.json`
- `environment_metadata.json`
- `failure_records.json`
- `remote_sync.json`, `remote_sync_failure.json`
- `COMPLETED`

The following are **rejected**:

- Tokens, credentials, `.netrc`, `.ssh/`, `.kaggle/`
- Model weights (`*.safetensors`, `*.bin`, `pytorch_model*`)
- Hugging Face cache content
- Hidden tests, ground truth
- Absolute Windows paths
- Files outside the runs directory

## Resume from Hugging Face

`--resume-from-hf` downloads the recovery state from Hugging Face and validates:

1. Protocol version match
2. Config hash match
3. Source commit match
4. Model identity match
5. Scenario set match
6. Strategy set match
7. Completed run IDs are skipped

Incompatible experiments are rejected with a clear error.

## CLI Commands

```bash
# Start new experiment with automatic sync
python seven_arm_benchmark.py \
  --profile pilot \
  --max-runs 2 \
  --output-dir /kaggle/working/runs \
  --hf-sync \
  --hf-repo-id "$HF_RESULTS_REPO_ID"

# Resume from Hugging Face
python seven_arm_benchmark.py \
  --profile pilot \
  --resume-from-hf \
  --experiment-id "<experiment-id>" \
  --max-runs 2 \
  --output-dir /kaggle/working/runs \
  --hf-sync \
  --hf-repo-id "$HF_RESULTS_REPO_ID"
```
