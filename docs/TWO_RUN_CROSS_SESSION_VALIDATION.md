# Two-Run Cross-Session Checkpoint & Hugging Face Resume Validation

**CHECKPOINT-RESUME VALIDATION / NON-PUBLICATION**

**Date:** 2026-07-24
**Commit:** `54ab97a`
**Profile:** `smoke` (1 scenario, 7 strategies, 1 rep, non-publication)
**HF Repo:** `NabilDo/selective-regeneration-experiment-results`

---

## Pre-Flight Checks

Perform these checks once, before Session 1.

### 1.1 Verify repository is private

```python
from huggingface_hub import HfApi
api = HfApi()
info = api.repo_info(
    repo_id="NabilDo/selective-regeneration-experiment-results",
    repo_type="dataset",
)
assert info.private is True, "Repository must be private"
print(f"Repository private: {info.private}")
print(f"Full name: {info.id}")
```

Expected output:
```
Repository private: True
Full name: NabilDo/selective-regeneration-experiment-results
```

### 1.2 Verify HF_TOKEN has write permission

```python
import os
from huggingface_hub import HfApi

token = os.environ.get("HF_TOKEN", "")
assert token, "HF_TOKEN not set"
api = HfApi()
who = api.whoami(token=token)
print(f"Authenticated as: {who['name']}")
print(f"Auth method: {who['auth']}")
```

Do not print the token value. Expected: the authenticated user name matches a collaborator on the private repo.

### 1.3 Verify Qwen model loads from Kaggle Model only

```python
import os
model_path = "/kaggle/input/qwen2-5-coder"
assert os.path.isdir(model_path), "Qwen model not mounted as Kaggle Model"
config_json = os.path.join(model_path, "config.json")
assert os.path.isfile(config_json), "config.json missing from model path"
print(f"Model found at: {model_path}")
print(f"Contents: {os.listdir(model_path)}")
```

### 1.4 Verify Internet is ON but limited to HF sync

In Kaggle notebook settings, ensure **Internet** is ON. The benchmark uses it only for `huggingface_hub` API calls. Model loading uses `local_files_only=True`.

---

## Session 1 — Execute Run 1

### 2.1 Notebook setup cell

```python
from kaggle_secrets import UserSecretsClient
import os

secrets = UserSecretsClient()
os.environ["HF_TOKEN"] = secrets.get_secret("HF_TOKEN")
os.environ["HF_RESULTS_REPO_ID"] = "NabilDo/selective-regeneration-experiment-results"
# HF_TOKEN is never printed
```

### 2.2 Install dependencies

```bash
!pip install -r /kaggle/input/benchmark-code/requirements-kaggle.txt
```

### 2.3 Verify GPU and model mount

```python
import torch
print(f"GPU: {torch.cuda.is_available()}, count: {torch.cuda.device_count()}")
model_path = "/kaggle/input/qwen2-5-coder"
print(f"Model exists: {os.path.isdir(model_path)}")
model_accessible = os.path.isdir(model_path)
```

### 2.4 Clone repo and checkout main

```bash
!git clone https://github.com/AhmedEhabH/dependency-aware-selective-regeneration-benchmark.git
%cd dependency-aware-selective-regeneration-benchmark/project
```

Record the source commit:
```python
!git rev-parse --short HEAD
```

### 2.5 Execute exactly one run with HF sync

```bash
python seven_arm_benchmark.py \
  --profile smoke \
  --max-runs 1 \
  --output-dir /kaggle/working/runs \
  --hf-sync \
  --hf-repo-id "$HF_RESULTS_REPO_ID"
```

### 2.6 Verify local checkpoint — Session 1

```python
import json
from pathlib import Path

runs_dir = Path("/kaggle/working/runs")

# checkpoint
cp = json.loads((runs_dir / "checkpoint.json").read_text())
print(f"EXPERIMENT_ID: {cp['profile']}/{cp['protocol_version']}/{cp['source_commit']}/{cp['execution_plan_hash']}")
print(f"COMPLETED_RUN_IDS: {cp['completed_run_ids']}")
print(f"PENDING_RUN_IDS: {cp['pending_run_ids']}")
print(f"TOTAL_PLANNED: {cp['total_planned']}")
print(f"TOTAL_COMPLETED: {cp['total_completed']}")
print(f"CONFIG_HASH: {cp['config_hash']}")
print(f"COMPLETION_STATUS: {cp['completion_status']}")

# records
records = [json.loads(line) for line in (runs_dir / "run_records.jsonl").read_text().strip().split("\n") if line]
print(f"RUN_RECORDS_COUNT: {len(records)}")
for r in records:
    print(f"  RUN_ID: {r['run_id']}, STATUS: {r['status']}")

# progress
progress = json.loads((runs_dir / "progress.json").read_text())
print(f"PROGRESS_COMPLETED: {progress['total_completed']}/{progress['total_planned']}")

# remote sync state
sync = json.loads((runs_dir / "remote_sync.json").read_text())
print(f"LAST_SYNC: {sync['last_sync']}")
print(f"REMOTE_PATH: {sync['remote_path']}")

assert cp["total_completed"] == 1, f"Expected 1 completed run, got {cp['total_completed']}"
print("\n=== SESSION 1 VERIFIED: 1 RUN COMPLETED ===")
```

### 2.7 Report Session 1 results

Copy these values from 2.6:

| Field | Value |
|-------|-------|
| Experiment ID | `<from profile/commit/config_hash>` |
| Source commit | `<from git rev-parse>` |
| Completed run IDs | `<list>` |
| Pending run count | `<total_planned - 1>` |
| Local checkpoint hash | `<config_hash>` |
| HF commit/URL | *(see below)* |

To get the Hugging Face commit:

```python
from huggingface_hub import HfApi
api = HfApi()
logs = api.list_repo_commits(
    repo_id="NabilDo/selective-regeneration-experiment-results",
    repo_type="dataset",
)
latest = logs[0]
print(f"HF_COMMIT: {latest.commit_id}")
print(f"HF_URL: https://huggingface.co/datasets/NabilDo/selective-regeneration-experiment-results/commit/{latest.commit_id}")
print(f"HF_DATE: {latest.created_at}")
```

Remote file tree for the experiment:

```python
files = api.get_repo_tree(
    repo_id="NabilDo/selective-regeneration-experiment-results",
    repo_type="dataset",
    path_in_repo=f"experiments/smoke/1.0/{cp['source_commit']}",
    recursive=True,
)
for f in files:
    print(f"{f.path}  ({f.size} bytes)")
```

---

## Session 2 — Resume from Hugging Face

Start a **new** Kaggle session. The first session may be terminated.

### 3.1 Same setup cells

Same as Session 1 (3.1–3.4). Repeat:

```python
from kaggle_secrets import UserSecretsClient
import os

secrets = UserSecretsClient()
os.environ["HF_TOKEN"] = secrets.get_secret("HF_TOKEN")
os.environ["HF_RESULTS_REPO_ID"] = "NabilDo/selective-regeneration-experiment-results"
```

```bash
!git clone https://github.com/AhmedEhabH/dependency-aware-selective-regeneration-benchmark.git
%cd dependency-aware-selective-regeneration-benchmark/project
```

### 3.2 Verify the same commit

```python
import subprocess
commit = subprocess.run(
    ["git", "rev-parse", "--short", "HEAD"],
    capture_output=True, text=True, timeout=5,
).stdout.strip()
print(f"SOURCE_COMMIT: {commit}")
assert commit == "<commit-from-session-1>", "Commit mismatch between sessions"
```

### 3.3 Resume from Hugging Face and execute run 2

```bash
python seven_arm_benchmark.py \
  --profile smoke \
  --resume-from-hf \
  --experiment-id "<experiment-id-from-session-1>" \
  --max-runs 1 \
  --output-dir /kaggle/working/runs \
  --hf-sync \
  --hf-repo-id "$HF_RESULTS_REPO_ID"
```

### 3.4 Verify checkpoint — Session 2

```python
import json
from pathlib import Path

runs_dir = Path("/kaggle/working/runs")

cp = json.loads((runs_dir / "checkpoint.json").read_text())
print(f"SAME_EXPERIMENT: profile={cp['profile']} commit={cp['source_commit']} config_hash={cp['config_hash']}")
print(f"COMPLETED_RUN_IDS: {cp['completed_run_ids']}")
print(f"TOTAL_COMPLETED: {cp['total_completed']}")
print(f"COMPLETION_STATUS: {cp['completion_status']}")

records = [json.loads(line) for line in (runs_dir / "run_records.jsonl").read_text().strip().split("\n") if line]
print(f"TOTAL_RUN_RECORDS: {len(records)}")
for r in records:
    print(f"  RUN_ID: {r['run_id']}, STATUS: {r['status']}")

# Verify no duplicates
run_ids = [r['run_id'] for r in records]
assert len(run_ids) == len(set(run_ids)), "DUPLICATE RUN IDS DETECTED"
assert len(run_ids) == 2, f"Expected 2 total run records, got {len(run_ids)}"
assert cp["total_completed"] == 2, f"Expected 2 completed, got {cp['total_completed']}"
```

### 3.5 Verify updated Hugging Face state

```python
from huggingface_hub import HfApi
api = HfApi()

logs = api.list_repo_commits(
    repo_id="NabilDo/selective-regeneration-experiment-results",
    repo_type="dataset",
)
latest = logs[0]
print(f"NEW_HF_COMMIT: {latest.commit_id}")
print(f"NEW_HF_URL: https://huggingface.co/datasets/NabilDo/selective-regeneration-experiment-results/commit/{latest.commit_id}")

files = api.get_repo_tree(
    repo_id="NabilDo/selective-regeneration-experiment-results",
    repo_type="dataset",
    path_in_repo=f"experiments/smoke/1.0/{cp['source_commit']}",
    recursive=True,
)
for f in files:
    print(f"{f.path}  ({f.size} bytes)")

# Verify recovery files exist and are updated
recovery_files = [f for f in files if "recovery" in f.path]
assert len(recovery_files) >= 1, "No recovery files found on HF after session 2"
print(f"RECOVERY_FILES_ON_HF: {len(recovery_files)}")
```

### 3.6 Checksum validation

```python
import hashlib

def sha256_of(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

local_records_hash = sha256_of(runs_dir / "run_records.jsonl")
local_checkpoint_hash = sha256_of(runs_dir / "checkpoint.json")
print(f"LOCAL_RECORDS_SHA256: {local_records_hash}")
print(f"LOCAL_CHECKPOINT_SHA256: {local_checkpoint_hash}")
```

---

## Report

### Session 1 Results

| Field | Value |
|-------|-------|
| Experiment ID | |
| Source commit | |
| Completed run IDs | |
| Pending run count | |
| Local checkpoint hash | |
| HF commit | |
| HF URL | |
| Remote file tree | |

### Session 2 Results

| Field | Value |
|-------|-------|
| Same experiment ID | |
| Downloaded checkpoint hash | |
| Skipped completed run ID | |
| Newly executed run ID | |
| Total completed count | 2 |
| Duplicated run IDs | NONE |
| Updated HF commit | |
| Updated HF URL | |
| Checksum validation | |

### Final Verdict

```
Cross-session Hugging Face resume: PASSED / FAILED
```

### Operational Authorization

If PASSED and all six assertions in 3.4 hold:

- [ ] Pilot is operationally authorized
- [ ] Pilot execution NOT started
