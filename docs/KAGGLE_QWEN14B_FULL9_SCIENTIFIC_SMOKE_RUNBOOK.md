# Kaggle Runbook — Qwen2.5-Coder-14B Full 9-Record Scientific Smoke V2

**Purpose:** run the first coherent real three-arm Scientific Smoke V2 after
the accepted successful Qwen 14B Selective canary.

## Frozen identity

```text
Runtime source:
f7b1ebba73b52868a95c47ef3806d3b09da16d93

Build:
f7b1ebb

Model:
Qwen2.5-Coder-14B-Instruct base

Quantization:
bnb-nf4

Expected model identity:
qwen:14b-instruct-v1:bnb-nf4:cfg-cc9474140d25

Profile:
scientific-smoke-v2

Protocol:
1.0

Matrix:
3 frozen todo scenarios × 3 frozen strategies × 1 repetition = 9 records
```

The accepted canary `exp-20260807-131819` remains separate calibration evidence.
Do not resume or merge it into this experiment.

## 1. Kaggle assets

Use the already audited deployment bundle pinned to `f7b1ebb`.

Attach:

```text
dependency-aware-selective-regeneration-code
dependency-aware-selective-regeneration-data
Qwen2.5-Coder-14B-Instruct
```

Expected model path:

```text
/kaggle/input/models/qwen-lm/qwen2.5-coder/transformers/14b-instruct/1
```

Use a GPU session with the expected 2 × Tesla T4 when available.

## 2. Runtime setup

Run the canonical:

```text
setup-cell
install-lock-cell
secrets-cell
```

Require the exact runtime lock including:

```text
pytest 8.4.2
accelerate 1.14.0
bitsandbytes 0.49.2
transformers 4.57.6
```

Torch is Kaggle-provided.

## 3. Engineering preflight policy

### New Kaggle session

Run the engineering `preflight-cell` exactly once.

Require:

```text
passed = true
model identity = qwen:14b-instruct-v1:bnb-nf4:cfg-cc9474140d25
GPU-only device map
GPU count = 1 or 2
every visible GPU free >= 2.0 GiB after probe
```

### Same still-live session as an already accepted identical preflight

Do not rerun an identical preflight solely for ceremony.

Never run the dedicated Selective Canary preflight again.

## 4. Full-9 output directory

Use a fresh isolated directory:

```text
/kaggle/working/runs/qwen14b_bnb_nf4_full9_scientific_smoke
```

It must not contain the canary experiment or old 7B data.

## 5. Full-9 command

Run one process, with no `--strategy` and no `--max-runs`:

```python
import subprocess
import sys
from pathlib import Path

FULL9_OUTPUT_DIR = Path(
    "/kaggle/working/runs/qwen14b_bnb_nf4_full9_scientific_smoke"
)
FULL9_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

full9_cmd = [
    sys.executable,
    "-u",
    str(SCRIPT_PATH),
    "--backend", "kaggle-qwen",
    "--profile", "scientific-smoke-v2",
    "--qwen-quantization", "bnb-nf4",
    "--max-attempts", "3",
    "--protocol-version", "1.0",
    "--max-completion-tokens-per-call", "1024",
    "--max-total-workflow-tokens", "0",
    "--timeout", "300",
    "--hf-sync",
    "--new-experiment",
    "--hf-repo-id", HF_RESULTS_REPO_ID,
    "--source-commit", "f7b1ebba73b52868a95c47ef3806d3b09da16d93",
    "--deployed-build-id", "f7b1ebb",
    "--data-dir", str(DATA_DIR),
    "--model-path", MODEL_PATH,
    "--output-dir", str(FULL9_OUTPUT_DIR),
]

print("Running Full-9:", " ".join(full9_cmd))
result = subprocess.run(full9_cmd, text=True)
print("Full-9 return code:", result.returncode)
if result.returncode != 0:
    raise RuntimeError(f"Full-9 process failed with return code {result.returncode}")
```

Do not add:

```text
--strategy
--max-runs
--auto-resume-hf
```

for the initial invocation.

The benchmark process must load the backend once and reuse it across the matrix.

## 6. If the Kaggle session is interrupted

Do not start a new experiment.

Resume the same experiment using the existing supported resume workflow and
exact identity. Preserve the original output/HF experiment ID.

Never merge the prior Selective canary into the Full-9 experiment.

## 7. Expected matrix

Require exactly these 9 terminal cells:

```text
todo-smoke-001 × monolithic
todo-smoke-001 × selective
todo-smoke-001 × iterative_repository_agent

todo-smoke-002 × monolithic
todo-smoke-002 × selective
todo-smoke-002 × iterative_repository_agent

todo-smoke-003 × monolithic
todo-smoke-003 × selective
todo-smoke-003 × iterative_repository_agent
```

The exact order may follow the frozen execution plan; the set must be exact.

Scientific failure of an individual implementation is an accepted terminal
record. Infrastructure/harness/environment failure is not.

## 8. Stop rules

Stop the session and preserve evidence when:

```text
model load fails
CUDA OOM
CPU/disk offload appears
model identity changes
source/build identity changes
HF recovery fails after a terminal record
checkpoint becomes inconsistent
harness exception prevents a RunRecord
```

Do not alter model, prompt, evaluator, budgets, or timeout to make a failing
scientific record pass.

## 9. Required outputs

Preserve/download:

```text
Executed Notebook
Full runs ZIP

<full9-dir>/experiment_id.txt
<full9-dir>/source_identity.json
<full9-dir>/environment_metadata.json
<full9-dir>/checkpoint.json
<full9-dir>/progress.json
<full9-dir>/run_records.jsonl
<full9-dir>/benchmark_summary.json
<full9-dir>/failure_records.json   # if present
<full9-dir>/remote_sync.json
<full9-dir>/dashboard/**
<full9-dir>/workspace/**           # preserve generated evidence
```

## 10. Do not do after completion

Even if all 9 records succeed:

```text
do not merge
do not tag
do not start Pilot
do not modify prompts/data/evaluator
```

First upload the Notebook and complete runs archive for independent result audit.
