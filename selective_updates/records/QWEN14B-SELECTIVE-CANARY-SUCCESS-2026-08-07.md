# QWEN14B-SELECTIVE-CANARY-SUCCESS — First Successful Real Qwen 14B Selective Canary

**Change ID:** QWEN14B-SELECTIVE-CANARY-SUCCESS-2026-08-07
**Date:** 2026-08-07
**Branch:** `fix/kaggle-smoke-v2-model-output-closure`
**Commit:** `docs(results): record successful Qwen 14B selective canary`
**Status:** ACCEPTED SUCCESSFUL REAL CANARY (independent GPT-5.6 Thinking audit) — RECORDED IN PROJECT DOCS (DOCUMENTATION ONLY; NO CODE/TEST/DEPLOY CHANGE)

## Truth

```text
branch                      = fix/kaggle-smoke-v2-model-output-closure
documentation HEAD          = 5561f91845914b320ddc1cb61701cacd94f8502b
experiment                  = exp-20260807-131819
runtime source              = f7b1ebba73b52868a95c47ef3806d3b09da16d93
build                       = f7b1ebb
model                       = Qwen2.5-Coder-14B-Instruct (base checkpoint)
quantization                = BitsAndBytes NF4 (load_in_4bit, bnb_4bit_quant_type=nf4,
                              bnb_4bit_compute_dtype=float16, bnb_4bit_use_double_quant=True)
model identity              = qwen:14b-instruct-v1:bnb-nf4:cfg-cc9474140d25
hardware                    = 2 x Tesla T4
scenario                    = todo-smoke-001
strategy                    = selective
status                      = succeeded
failure classification      = none
accepted real 14B canary    = 1 succeeded / 0 failed (checkpoint: 1 succeeded / 0 failed / 2 pending)
full 9-record Smoke V2      = NOT RUN (do NOT call this canary 1/9; it was an isolated selective-only plan)
merge/tag/Pilot             = not authorized
stable release              = NOT claimed
next action                 = one fresh Full-9 Scientific Smoke V2 using the frozen runbook
sentinel                    = QWEN14B_CANARY_SUCCESS_DOCUMENTED_FULL9_READY
```

## 1. Preflight — real runtime and per-GPU memory

The engineering preflight passed on the real target environment (Python 3.12.13,
Django 5.2.16, DRF 3.17.1, pytest 8.4.2, accelerate 1.14.0, bitsandbytes 0.49.2,
torch 2.10.0+cu128, transformers 4.57.6). Model footprint 9,721,981,184 bytes;
GPU count 2; preflight duration 174.016 s; probe tokens 68 + 17.

| GPU | Allocated GiB | Reserved GiB | Free GiB | Total GiB |
|---:|---:|---:|---:|---:|
| 0 | 3.311 | 3.379 | 11.054 | 14.562 |
| 1 | 5.957 | 6.016 | 8.417 | 14.562 |

Minimum free VRAM = **8.417 GiB**, far above the frozen 2.0 GiB headroom
threshold. Device map was GPU-only (no CPU/disk offload). The dedicated canary
repeated the preflight (150.004 s, same identity, GPU count 2, minimum free
VRAM 8.417 GiB, probe 68 + 17 tokens) and passed again. This establishes that
the base 14B checkpoint loads under the NF4 runtime on 2×T4 without offload.

## 2. Generated artifacts and exact changes

Only the expected source scope changed.

| Artifact | Change |
|---|---|
| `todo/models.py` | Added `Priority(models.TextChoices)` with `HIGH/MEDIUM/LOW` and a `priority` `CharField(max_length=6, default=MEDIUM)` |
| `todo/serializers.py` | Added `priority` to `TaskSerializer.Meta.fields` only |
| `todo/views.py` | Added a `get_queryset()` filter on the request `priority` parameter |
| `todo/migrations/0004_task_priority.py` | Exactly one new migration adding `priority` with `max_length=6`, default `MEDIUM`, three allowed choices |

Preserved unchanged: `todo/permissions.py`, `todo/urls.py`, Project behavior,
Tag behavior, existing migrations. Generated scope: 3 selected / 2 preserved /
3 regenerated.

**Model-output quality note (non-blocking):** the generated `views.py` includes
an unused `from django.db.models import Q` import. It did not alter the
evaluator result. The accepted evidence workspace must NOT be modified or
regenerated.

## 3. Scenario evaluator — 10/10 named checks

| # | Check | Result |
|--:|---|---|
| 1 | task_priority_enum | PASS |
| 2 | task_priority_field | PASS |
| 3 | task_priority_default | PASS |
| 4 | task_priority_valid_values | PASS |
| 5 | task_serializer_priority | PASS |
| 6 | task_priority_invalid_rejected | PASS |
| 7 | task_priority_filter | PASS |
| 8 | task_unfiltered_list | PASS |
| 9 | baseline_task_fields | PASS |
| 10 | project_and_tag_regression | PASS |

Functional validation = PASS. The evaluator independently checks `Task.Priority`
is a Django `TextChoices`; exact values `HIGH/MEDIUM/LOW`; default `MEDIUM`;
serializer exposes a writable ChoiceField; all three valid priorities POST and
read back; invalid `URGENT` rejected with HTTP 400; `?priority=HIGH` includes
only HIGH tasks; unfiltered list still returns ordinary tasks; existing
owner/tags/project/status/timestamps remain functional; Project and Tag
model/serializer/API behavior intact. Substantially stronger evidence than
compilation alone.

## 4. Tokens / calls / timing

| Metric | Value |
|---|---:|
| Model calls | 3 |
| Regeneration model calls | 3 |
| Repair model calls | 0 |
| Prompt tokens | 2,527 |
| Completion tokens | 720 |
| Total workflow tokens | 3,247 |
| Repair attempts | 0 |
| Workflow duration | 295.944 s |
| Functional validation | PASS |
| Migration generation | PASS |
| Scenario evaluator | PASS (10/10) |
| Unresolved human review | 0 |

## 5. Qwen 14B vs Qwen 7B on the same scenario/strategy

Latest accepted 7B selective calibration (`todo-smoke-001`/selective) vs the
current 14B NF4 selective canary:

| Metric | 7B | 14B NF4 | Change |
|---|---:|---:|---:|
| Success | No | **Yes** | model-quality floor crossed |
| Model calls | 4 | **3** | 25.0% fewer |
| Tokens | 5,804 | **3,247** | 44.1% fewer |
| Repair calls | 1 | **0** | eliminated |
| Workflow time | 257.596 s | 295.944 s | 14.9% slower |

The 14B run is slower because the larger model is more expensive to load and
generate with, but materially more useful because it produced a correct
implementation without repair. This demonstrates functional viability, **not**
strategy superiority, and evidences a 7B capacity/instruction-following floor
for this task — not yet proof that 14B succeeds on every scenario.

## 6. HF persistence evidence

Local execution evidence reports `last_sync = recovery_uploaded`, with logs of
successful uploads of RunRecord, checkpoint, progress, summary, dashboard,
source identity, and snapshot chunk to the configured HF repository. This audit
verifies uploaded local logs and archive only; it does not claim an
independently live-fetched Hugging Face state.

## 7. Continuous-cell fail-closed explanation

The Notebook's continuous cell was executed after the successful dedicated
canary, but correctly **failed closed with zero model calls**. Reason: it
validates the generic `/runs/scientific_smoke_v2` experiment; `RUN_GENERIC_ONE_RUN`
remained disabled so that generic experiment had no record; the successful
record lives in the isolated `qwen14b_bnb_nf4_selective_canary` experiment.
This is not a scientific or model failure. Do NOT patch the continuous workflow
before the Full-9 run; use a new isolated Full-9 experiment instead.

## 8. Pre-Benchmark categories

| Category | Decision | Explanation |
|---|---|---|
| Dataset Validation | PASS | Frozen 27-scenario data and todo baseline used; expected scenario scope preserved |
| Prompt Validation | PASS | Frozen prompt path produced valid contract-following outputs for all three selected source files |
| Pipeline Smoke Test | PASS | Real 14B load, GPU-only placement, multi-GPU headroom, generation, migration, baseline and evaluator all passed |
| Dry Run | PASS | Official source/bundle previously completed scripted 9/9 and runtime source was unchanged for this canary |
| Integration Test | PASS | Official clean gate for this source line was 1,915 passed / 32 skipped / 0 failed |
| Metric Verification | PASS | RunRecord, summary, checkpoint, tokens and artifact counts are internally consistent |
| Real Model Quality | PASS for todo-smoke-001/selective | One correct functional implementation, zero repairs |
| HF Recovery Persistence | PASS from local logs | recovery upload completed |
| Full 9-record Scientific Smoke | NOT RUN | next scientific action |
| Overall | CANARY ACCEPTED | proceed to one coherent Full-9 Smoke experiment |

## 9. Current / near / far goals

```text
Current:
real 14B engineering preflight = PASS
accepted real 14B selective canary = 1 succeeded / 0 failed
full 9-record Scientific Smoke V2 = not run

Near:
record evidence in project docs (this record);
run one fresh 3 scenarios x 3 arms = 9-record Scientific Smoke V2
using the frozen runbook (docs/KAGGLE_QWEN14B_FULL9_SCIENTIFIC_SMOKE_RUNBOOK.md).

Far:
audit 9 records -> merge accepted Smoke closure -> stable scientific-smoke tag
-> freeze Pilot -> Pilot -> research experiment -> statistical analysis/paper.

Keep:
main merge = not authorized
stable scientific tag = not yet
Pilot = not authorized
```

## 10. Scope / over-engineering decision

Do NOT make another runtime, prompt, model, strategy, evaluator, metric, or
memory change before the Full-9 run. Do NOT repair the unused `Q` import in the
accepted generated workspace (evidence, not production project code). Do NOT
create another comparative canary. Fastest scientifically valid path: record →
one fresh 9-record Scientific Smoke V2 → independent results audit.

## Notes

Documentation-only closure. No Python, YAML, tests, runtime lock, scenario
data, prompt, Notebook executable cell, or `kaggle_upload/**` was changed.
No Kaggle run, no preflight rerun, no full test suite rerun (1,915 suite
skipped per directive), no merge, no tag, no Pilot. Commit message exactly
`docs(results): record successful Qwen 14B selective canary`; pushed; working
tree clean; local HEAD = remote HEAD.
