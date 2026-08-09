# Kaggle Runbook — Qwen2.5-Coder-14B Full 9-Record Scientific Smoke V2

**Purpose:** run a fresh corrected three-arm Scientific Smoke V2 after the
first Full-9 was scientifically REJECTED for workspace contamination and the
runtime workspace-isolation defect was fixed.

This runbook distinguishes exactly four phases of evidence:

- accepted selective canary `exp-20260807-131819` — accepted, separate
  calibration evidence;
- rejected Full-9 `exp-20260807-205422` — RUN under runtime source/build
  `f7b1ebb` but scientifically REJECTED because generated files leaked across
  reused strategy workspaces;
- **accepted clean 300-second Full-9 baseline** — RUN under corrected runtime
  source/build `7f2a450` with `--timeout 300`; remains valid and preserved:
  **9/9 terminal / 2 successes / 7 scientific failures / 0 engineering
  blockers**, with three runs reaching/crossing the ~300-second workflow
  ceiling (~307–337 s). This is the accepted 300-second baseline and MUST NOT
  be overwritten or relabeled;
- **T600 confirmatory Full-9 (FULL9-T600-01)** — **EXECUTED AND ACCEPTED** on
  2026-08-09 (SMOKE-V2-CLOSE-01): run `exp-20260808-222843`, launched under
  the SAME corrected runtime source/build `7f2a450` with the uniform
  scientific per-run workflow timeout raised **300 → 600** and a NEW fail-closed
  output namespace
  `/kaggle/working/runs/qwen14b_bnb_nf4_full9_scientific_smoke_wsfix_7f2a450_t600`
  and evidence archive prefix `corrected-full9-t600-wsfix-7f2a450-`; result =
  **9/9 terminal / 2 successes / 7 scientific failures / 0 engineering
  blockers / 0 budget-exhausted / 63 model calls / 77,929 tokens / max run
  ≈373 s / Full-9 verification PASS / HF synchronization PASS** — the SAME 2/9
  result as the accepted 300-second baseline (timeout sensitivity confirmed;
  NOT an improvement claim). No further Kaggle Full-9 is authorized.

## FULL9-T600-01 — confirmatory timeout-sensitivity Full-9 (T600)

**Status: EXECUTED AND ACCEPTED (2026-08-09, SMOKE-V2-CLOSE-01) — experiment
closed; run `exp-20260808-222843` recorded above. The instructions below are
the frozen launch runbook (historical reference; do NOT relaunch).**

### Rationale

> The accepted 300-second clean Full-9 showed three runs at or beyond the
> scientific per-run workflow ceiling (~307–337 seconds). To reduce timeout
> censoring while preserving equal computational opportunity across strategies,
> the scientific workflow timeout was increased uniformly to 600 seconds for
> one confirmatory Full-9. All other frozen scientific inputs remain unchanged.

### Contract

- **600 seconds applies uniformly** to monolithic, selective, and
  iterative_repository_agent — every strategy receives the same per-run
  workflow budget; **no strategy receives extra time**.
- All three strategies share the same single Full-9 command and therefore the
  same 600-second per-run workflow budget.
- The **300-second baseline is NOT invalidated or replaced** — it remains the
  accepted clean baseline; T600 is a separate confirmatory timeout-sensitivity
  experiment.
- **Do NOT increase the timeout beyond 600.** If the T600 experiment also
  accumulates runs near 600 seconds, do NOT automatically raise the timeout
  again — analyze the duration/repair distribution and pre-register the Pilot
  budget instead.
- T600 changes ONLY the uniform scientific per-run workflow timeout 300 → 600;
  all other frozen scientific inputs (model, prompts, strategies, scenarios,
  evaluator, metrics, max attempts, token budgets, deployment identity
  `7f2a450`) remain unchanged.
- Output namespace (fail-closed, same non-empty guard):
  `/kaggle/working/runs/qwen14b_bnb_nf4_full9_scientific_smoke_wsfix_7f2a450_t600`
- Evidence archive prefix: `corrected-full9-t600-wsfix-7f2a450-`
  (the export cell produces `corrected-full9-t600-wsfix-7f2a450-<stamp>.zip`).

## Frozen identity

```text
Runtime source:
7f2a4509482dc7e62c2b243374592e9a88e2ff48

Build:
7f2a450

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

The previous Full-9 exp-20260807-205422 used runtime source f7b1ebb and is REJECTED scientific evidence. Its records, checkpoint, local output directory, and strategy workspaces must never be resumed, merged, copied forward, or used as the output base for this corrected run.

The accepted clean 300-second Full-9 baseline (runtime source/build `7f2a450`,
`--timeout 300`, output
`/kaggle/working/runs/qwen14b_bnb_nf4_full9_scientific_smoke_wsfix_7f2a450`)
remains valid, preserved, and separate. The T600 confirmatory Full-9 runs into
its OWN new output namespace
`/kaggle/working/runs/qwen14b_bnb_nf4_full9_scientific_smoke_wsfix_7f2a450_t600`;
it must NOT resume, merge, copy forward, or reuse the 300-second baseline
output directory, the rejected `exp-20260807-205422`, or the accepted canary.

## 1. Kaggle assets

Use the already audited deployment bundle pinned to the corrected runtime
`7f2a450`. The deployment was re-pinned by `e29c017` after the workspace-isolation
fix. Do not attach the pre-fix `f7b1ebb` bundle for the current launch.

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

Run the canonical order exactly once for a new Kaggle session:

```text
setup-cell
install-lock-cell
preflight-cell
secrets-cell
Full-9 cell
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

Use a fresh isolated directory that is fail-closed against pre-existing records:

```text
/kaggle/working/runs/qwen14b_bnb_nf4_full9_scientific_smoke_wsfix_7f2a450_t600
```

This is the T600 confirmatory Full-9 namespace. It must not contain the canary
experiment, the rejected Full-9 `exp-20260807-205422`, the accepted 300-second
Full-9 baseline
(`qwen14b_bnb_nf4_full9_scientific_smoke_wsfix_7f2a450` — without the `_t600`
suffix), or old 7B data.

Evidence archive prefix (written by the export-evidence cell under
`/kaggle/working`):

```text
corrected-full9-t600-wsfix-7f2a450-<stamp>.zip
```

## 5. Full-9 command

Run one process. The initial invocation must not include `--strategy`,
`--max-runs`, or `--auto-resume-hf`:

```python
import subprocess
import sys
from pathlib import Path

FULL9_OUTPUT_DIR = Path(
    "/kaggle/working/runs/qwen14b_bnb_nf4_full9_scientific_smoke_wsfix_7f2a450_t600"
)

if FULL9_OUTPUT_DIR.exists() and any(FULL9_OUTPUT_DIR.iterdir()):
    raise RuntimeError(
        "Refusing to start corrected Full-9 in a non-empty output directory: "
        f"{FULL9_OUTPUT_DIR}"
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
    "--timeout", "600",
    "--hf-sync",
    "--new-experiment",
    "--hf-repo-id", HF_RESULTS_REPO_ID,
    "--source-commit", "7f2a4509482dc7e62c2b243374592e9a88e2ff48",
    "--deployed-build-id", "7f2a450",
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

Note: the uniform scientific per-run workflow timeout is **`--timeout 600`**
for the T600 confirmatory Full-9. It applies identically to monolithic,
selective, and iterative_repository_agent. Do NOT raise it above 600. Do NOT
fall back to 300 for this confirmatory run.

Do not add:

```text
--strategy
--max-runs
--auto-resume-hf
```

for the initial invocation.

Do not automatically delete or clean the output directory if it is non-empty.
Fail closed instead, as the guard above does.

The benchmark process must load the backend once and reuse it across the matrix.

## 6. If the Kaggle session is interrupted

Resume only after this corrected experiment has actually started and has a
valid experiment identity. Do not start a new experiment.

Resume the same experiment using the existing supported resume workflow and
exact identity. Preserve the original output/HF experiment ID.

Never resume, merge, or copy forward the rejected Full-9 `exp-20260807-205422`
or the accepted selective canary `exp-20260807-131819` into the corrected
Full-9 experiment. Also never resume or reuse the accepted 300-second Full-9
baseline experiment — the T600 run is a separate confirmatory experiment with
its own experiment identity and its own `_t600` output namespace.

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

Evidence archive naming for the T600 run:
`corrected-full9-t600-wsfix-7f2a450-<stamp>.zip`.

## 9a. Pre-benchmark validation recorded for the T600 contract (FULL9-T600-01)

Carried forward and recorded at contract time (2026-08-08) before this run:

```text
Dataset Validation       PASS / carried forward — zero drift
Prompt Validation        PASS / carried forward — zero drift
Pipeline Smoke Test      PASS — T600 command and fail-closed _t600 namespace contract validated
Dry Run                  PASS — exact 3x3 no-model/bundled dry-run contract validated with scientific timeout 600
Integration Test         PASS — final executable full suite: 1947 passed / 33 skipped / 0 failed
Metric Verification      PASS / carried forward — zero metric/evaluator drift
```

## 10. Do not do after completion

Even if all 9 records succeed:

```text
do not merge
do not tag
do not start Pilot
do not modify prompts/data/evaluator
do not raise the scientific workflow timeout above 600
do not run a second Full-9 from this session
```

If a future Pilot run accumulates runs near 600 seconds, analyze the
duration/repair distribution and pre-register the Pilot budget instead of
raising the timeout again.

## 11. Accepted T600 result record (SMOKE-V2-CLOSE-01, 2026-08-09)

The T600 confirmatory Full-9 was executed once and accepted:

```text
Experiment:      exp-20260808-222843
Runtime source:  7f2a4509482dc7e62c2b243374592e9a88e2ff48
Build:           7f2a450
Timeout:         uniform --timeout 600 (per-run workflow budget, all arms)
Output namespace: /kaggle/working/runs/qwen14b_bnb_nf4_full9_scientific_smoke_wsfix_7f2a450_t600
Evidence prefix: corrected-full9-t600-wsfix-7f2a450-
Result:          9/9 terminal / 2 successes / 7 scientific failures / 0 engineering blockers
Budget:          0 budget-exhausted / 63 model calls / 77,929 tokens
Timing:          max run ≈373 s (well under the 600 s ceiling)
Verification:    Full-9 verification PASS / HF synchronization PASS
Judgment:        SAME 2/9 result as the accepted clean 300-second baseline
                 → timeout sensitivity confirmed; the 300-second baseline
                 signal was NOT distorted by timeout censoring.
                 This is NOT an improvement claim.
```

The accepted clean 300-second baseline and this accepted T600 run are the two
accepted Scientific Smoke V2 evidence sets. The uniform per-run workflow
timeout is now frozen at **600s**. No further Kaggle Full-9 is authorized; the
next authorized action is the independent delta audit of the closure
(SMOKE-V2-CLOSE-01), then main merge + stable tag `v0.8.0-smoke-v2-complete`,
then `PILOT-READY-01`.
