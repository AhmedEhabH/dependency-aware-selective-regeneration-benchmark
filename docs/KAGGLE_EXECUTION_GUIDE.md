# Kaggle Execution Guide

**Date:** 2026-07-24
**Applies to:** Qwen2.5-Coder benchmark on Kaggle

---

## 1. Prerequisites

- Kaggle account (any tier)
- `HF_TOKEN` (HuggingFace write token) — required for result synchronization
- `HF_RESULTS_REPO_ID` — `NabilDo/selective-regeneration-experiment-results`
- Internet-enabled Kaggle notebook (set in notebook metadata) — model loading remains offline

---

## 2. What to Upload

### 2.1 Notebook
Upload `notebooks/seven_arm_benchmark.ipynb` to Kaggle as a new notebook.

### 2.2 Datasets

Create two Kaggle Datasets:

**benchmark-code** (code + configs):
- `seven_arm_benchmark.py` (root)
- `src/benchmark/` (full package tree)
- `configs/smoke.yaml`, `configs/pilot.yaml`, `configs/research.yaml`
- `pyproject.toml`
- `requirements-kaggle.txt`

**benchmark-data** (scenarios + repositories):
- `benchmark_data/scenarios/` (24 files)
- `benchmark_data/manifests/` (2 files)
- `benchmark_data/repository_profiles/` (3 files)

### 2.3 Model
Qwen2.5-Coder must be available as a Kaggle Model. Model loading uses `local_files_only=True` from the attached Kaggle Model — no HuggingFace download.

### 2.4 Pilot bundle (PILOT-EXEC-01)

For the Pilot, upload the **frozen Pilot deployment archive** generated from
the `v0.9.3-pilot-exec-ready` tag as **ONE Kaggle Dataset** containing at
minimum:

- `pilot-kaggle-upload.zip`
- `pilot-kaggle-upload.zip.sha256`

Do not separately reconstruct code/data datasets by hand: the generic
two-dataset shape in 2.2 applies to the Scientific Smoke deployment, NOT to
the Pilot. Inside the notebook the archive is extracted to
`/kaggle/working/pilot_bundle` and the bundled `code/` and `data/` are used
directly (see 3.7).

Never upload the historical `kaggle_upload/` bundle as Pilot input: it is the
frozen Scientific Smoke deployment evidence and is stale relative to current
Pilot canonical sources. Verify the uploaded archive SHA-256 against
`reports/PILOT_EXEC_01_DEPLOYMENT_FREEZE.md` before launching. Kaggle slugs
used by the Pilot differ from the Smoke bundle's slugs.

---

## 3. Notebook Workflow

### Cell 1 — Install dependencies
```python
!pip install -r /kaggle/input/benchmark-code/requirements-kaggle.txt
```

### Cell 2 — Verify GPU
```python
import torch
print(f"GPU available: {torch.cuda.is_available()}")
print(f"GPU count: {torch.cuda.device_count()}")
if torch.cuda.is_available():
    print(f"GPU name: {torch.cuda.get_device_name(0)}")
```

### Cell 3 — Verify Qwen model mount
```python
import os
model_path = "/kaggle/input/qwen2-5-coder"
if os.path.exists(model_path):
    print(f"Model found: {os.listdir(model_path)}")
else:
    print("WARNING: Qwen model not mounted. Benchmark will fail at model load.")
```

### Cell 4 — Clone repo
```python
!git clone https://github.com/anomalyco/opencode-benchmark.git
%cd opencode-benchmark/project
```

### Cell 5 — Secure setup (HF token)
```python
from kaggle_secrets import UserSecretsClient
import os

secrets = UserSecretsClient()
os.environ["HF_TOKEN"] = secrets.get_secret("HF_TOKEN")
os.environ["HF_RESULTS_REPO_ID"] = (
    "NabilDo/selective-regeneration-experiment-results"
)
# Note: HF_TOKEN is never printed
```

### Cell 6 — Dry-run smoke validation
```python
!python /kaggle/input/benchmark-code/seven_arm_benchmark.py \
    --dry-run \
    --profile smoke \
    --data-dir /kaggle/input/benchmark-data
```

### Cell 7 — Pilot bundle prep (PILOT-EXEC-01)

```python
import hashlib, zipfile, json
from pathlib import Path

dataset_mount = Path("/kaggle/input/<pilot-benchmark-bundle>")  # ONE dataset slug
archive = dataset_mount / "pilot-kaggle-upload.zip"
sidecar = dataset_mount / "pilot-kaggle-upload.zip.sha256"

# 1) Verify the archive SHA-256 equals the frozen value (from the freeze report
#    and dist/pilot-kaggle-upload.zip.sha256 — updated for v0.9.3-pilot-exec-ready)
frozen_sha = "<SHA-256 from dist/pilot-kaggle-upload.zip.sha256>"
actual_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
assert actual_sha == frozen_sha, f"SHA-256 mismatch: {actual_sha}"

# 2) Extract to /kaggle/working/pilot_bundle
bundle_root = Path("/kaggle/working/pilot_bundle")
with zipfile.ZipFile(archive) as z:
    z.extractall(bundle_root)

# 3) Verify the frozen deployment identity
identity = json.loads(
    (bundle_root / "pilot_deployment_identity.json").read_text(encoding="utf-8")
)
assert identity["task"] == "PILOT-EXEC-01"
assert identity["source_tag"] == "v0.9.3-pilot-exec-ready"

# 4) Verify code/data manifests against the freeze report
#    code_manifest.json / data_manifest.json under bundle_root

# 5) Define the bundled paths used by every later cell
PILOT_CODE = str(bundle_root / "code")
PILOT_DATA = str(bundle_root / "data")
```

```python
!pip install -r /kaggle/working/pilot_bundle/code/requirements-kaggle.txt
```

### Cell 8 — Real Pilot launch (PILOT-EXEC-01, 48-cell matrix)
```bash
# Uncomment when ready for real execution. The Pilot launch contract is frozen:
# --qwen-quantization bnb-nf4 is EXPLICIT (generic CLI default is bnb-int8).
# Do NOT pass --max-runs 2 for the Pilot; run one continuous 48-cell session.
# python /kaggle/working/pilot_bundle/code/seven_arm_benchmark.py \
#     --backend kaggle-qwen \
#     --profile pilot \
#     --data-dir /kaggle/working/pilot_bundle/data \
#     --model-path "$MODEL_PATH" \
#     --qwen-quantization bnb-nf4 \
#     --max-attempts 3 \
#     --max-completion-tokens-per-call 4096 \
#     --max-total-workflow-tokens 0 \
#     --timeout 600 \
#     --source-commit "<40-char SHA>" \
#     --source-tag v0.9.3-pilot-exec-ready \
#     --output-dir /kaggle/working/runs/pilot-<experiment-id> \
#     --hf-sync \
#     --hf-repo-id "$HF_RESULTS_REPO_ID" \
#     --new-experiment
```

### Cell 9 — Resume the SAME Pilot experiment after external interruption
```bash
# Resume only the same compatible experiment (identical source/model/config/
# matrix/quantization). Never --new-experiment on resume.
# python /kaggle/working/pilot_bundle/code/seven_arm_benchmark.py \
#     --profile pilot \
#     --data-dir /kaggle/working/pilot_bundle/data \
#     --model-path "$MODEL_PATH" \
#     --qwen-quantization bnb-nf4 \
#     --resume-from-hf \
#     --output-dir /kaggle/working/runs/pilot-<experiment-id> \
#     --hf-sync \
#     --hf-repo-id "$HF_RESULTS_REPO_ID"
```

### Cell 10 — View results
```python
import json
summary_path = "runs/benchmark_summary.json"
with open(summary_path) as f:
    print(json.dumps(json.load(f), indent=2))
```

---

## 4. Execution Profiles

| Profile | Scenarios | Strategies | Reps | Est. Time | Publication | Command |
|---------|-----------|-----------|------|-----------|-------------|---------|
| smoke | 1 (djangocms-feature-toggle) | All 7 | 1 | < 30 min | No | `--profile smoke` |
| pilot | 12 (4 per repo × 3 repos) | iterative_repository_agent, selective | 2 | 48 cells (48 planned) | No | `--profile pilot --qwen-quantization bnb-nf4` |
| research | 24 (8 per repo × 3 repos) | agent, selective, compiled_ai, delta_mcp | 3 | ~6-9h | Yes | `--profile research` |

Custom profiles can be created by adding YAML files to `configs/`.

---

## 5. Outputs

All outputs go to `runs/`:
- `run_records.jsonl` — Per-run persistent records (JSONL, append-only)
- `checkpoint.json` — Atomic checkpoint state
- `progress.json` — Live progress tracking
- `benchmark_summary.json` — Final run-level summary
- `benchmark_summary.partial.json` — Partial summary (updated after every run)
- `COMPLETED` — Marker file (written when all runs finish)
- `benchmark-results.zip` — Full results package
- `remote_sync.json` — Last HF sync status
- `remote_sync_failure.json` — Persistent sync failure records

---

## 6. Required Secrets

Set up Kaggle Secrets (Add-ons → Secrets) with:

| Key | Value | Notes |
|-----|-------|-------|
| `HF_TOKEN` | Your HuggingFace write token | Never printed or logged |
| | `NabilDo/selective-regeneration-experiment-results` | Repository ID is set via `HF_RESULTS_REPO_ID` env var |

The token is read in a secure setup cell that does not display it.

---

## 7. Checkpoint and Resume

The benchmark automatically saves checkpoint state after every run. If a Kaggle session is terminated:

1. **Local checkpoint** is at `/kaggle/working/runs/` (persistent across sessions if saved as Dataset output)
2. **HF sync** pushes recovery files to HuggingFace after every run when `--hf-sync` is enabled
3. **Resume locally:** `--resume` flag reads existing checkpoint in output directory
4. **Resume from HF:** `--resume-from-hf` downloads and validates recovery state from HuggingFace

---

## 8. Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| "ModelBackendError: KaggleQwenBackend not available locally" | Running on local machine | Run only on Kaggle |
| torch.cuda.is_available() = False | No GPU on Kaggle session | Enable GPU accelerator in Notebook settings |
| FileNotFoundError: /kaggle/input/benchmark-data | Dataset not uploaded | Create benchmark-data Dataset and attach |
| HuggingFace Hub connection error | No internet or no HF_TOKEN | Enable internet, set HF_TOKEN |
| OOM during model load | GPU memory insufficient | Use P40 or T4 GPU; reduce batch size if applicable |
| "HF repo visibility check failed" | Repo not found or public | Ensure `NabilDo/selective-regeneration-experiment-results` exists and is private |
| "Resume validation failed" | Incompatible experiment | Verify protocol version, config hash, source commit match |
| Remote sync failure logged | HF Hub transient error | Execution continues; retry with `--resume-from-hf` in next session |

---

## 9. Session Limits

- **Kaggle session:** 9 hours max; auto-shuts down at limit
- **GPU hours:** 30 hours/week (free tier); more with Kaggle Pro
- **Smoke profile:** Well within limits (~30 min)
- **Pilot profile:** 48 cells planned; wall time depends on real Qwen 14B
  bnb-nf4 generation and must be measured by the Pilot (no pre-Pilot estimate).
- **Research profile:** ~6-9 hours — may hit limit with larger models

---

## 10. Results Management

- Download all `runs/` artifacts before session expires
- Move to `reports/results/` in repo
- Tag the commit corresponding to Kaggle results
- SHA-256 checksum results for audit trail
