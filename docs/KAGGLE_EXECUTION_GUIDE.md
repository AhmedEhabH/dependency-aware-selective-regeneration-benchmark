# Kaggle Execution Guide

**Date:** 2026-07-23
**Applies to:** Qwen2.5-Coder benchmark on Kaggle

---

## 1. Prerequisites

- Kaggle account (any tier)
- `HF_TOKEN` (HuggingFace read token) — only needed if Qwen is not available as a Kaggle Model
- Internet-enabled Kaggle notebook (set in notebook metadata)

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
If Qwen2.5-Coder is not available as a Kaggle Model, create a Kaggle Dataset from HuggingFace:
```
https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct
```

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

### Cell 5 — Dry-run smoke validation
```python
!python /kaggle/input/benchmark-code/seven_arm_benchmark.py \
    --dry-run \
    --profile smoke \
    --data-dir /kaggle/input/benchmark-data
```

### Cell 6 — Real smoke execution
```python
# Uncomment when ready for real execution:
# !python /kaggle/input/benchmark-code/seven_arm_benchmark.py \
#     --profile smoke \
#     --data-dir /kaggle/input/benchmark-data \
#     --hf-token {HF_TOKEN}
```

### Cell 7 — View results
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
| pilot | 12 (4 per repo × 3 repos) | agent, selective | 2 | ~2-3h | No | `--profile pilot` |
| research | 24 (8 per repo × 3 repos) | agent, selective, compiled_ai, delta_mcp | 3 | ~6-9h | Yes | `--profile research` |

Custom profiles can be created by adding YAML files to `configs/`.

---

## 5. Outputs

All outputs go to `runs/`:
- `benchmark_summary.json` — Run-level summary (per arm success/failure counts, durations)
- `runs/YYYYMMDD_HHMMSS_<run_id>/` — Individual run records
- `runs/benchmark_results.json` — Full results (pilot/research only)
- `runs/publication_tables/` — LaTeX, CSV, Markdown tables (research only)

---

## 6. Required Secrets

If your HF token is not available as a Kaggle Secret:
```python
import os
os.environ["HF_TOKEN"] = "hf_..."  # NOT RECOMMENDED for publication
```

Prefer Kaggle notebook Secrets (Add-ons → Secrets) with key `HF_TOKEN`.

---

## 7. Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| "ModelBackendError: KaggleQwenBackend not available locally" | Running on local machine | Run only on Kaggle |
| torch.cuda.is_available() = False | No GPU on Kaggle session | Enable GPU accelerator in Notebook settings |
| FileNotFoundError: /kaggle/input/benchmark-data | Dataset not uploaded | Create benchmark-data Dataset and attach |
| HuggingFace Hub connection error | No internet or no HF_TOKEN | Enable internet, set HF_TOKEN |
| OOM during model load | GPU memory insufficient | Use P40 or T4 GPU; reduce batch size if applicable |

---

## 8. Session Limits

- **Kaggle session:** 9 hours max; auto-shuts down at limit
- **GPU hours:** 30 hours/week (free tier); more with Kaggle Pro
- **Smoke profile:** Well within limits (~30 min)
- **Pilot profile:** ~2-3 hours
- **Research profile:** ~6-9 hours — may hit limit with larger models

---

## 9. Results Management

- Download all `runs/` artifacts before session expires
- Move to `reports/results/` in repo
- Tag the commit corresponding to Kaggle results
- SHA-256 checksum results for audit trail
