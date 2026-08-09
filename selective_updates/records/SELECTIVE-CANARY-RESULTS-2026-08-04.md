# SELECTIVE-CANARY-RESULTS-2026-08-04 — Selective Calibration Canary Result

**Change ID:** SELECTIVE-CANARY-RESULTS-2026-08-04 (Selective Calibration Canary Result Ingestion)
**Date:** 2026-08-04
**Branch:** `fix/kaggle-smoke-v2-model-output-closure`
**HEAD:** `25bfe04` before this commit (pushed; local = remote; working tree clean)
**Status:** DEDICATED SELECTIVE CALIBRATION CANARY EXECUTED AND DOCUMENTED — THE HARNESS SAFETY CONTROLS WORKED; QWEN CODE QUALITY DID NOT IMPROVE — NO SUCCESSFUL IMPLEMENTATION; NO MERGE/TAG/PILOT/KAGGLE AUTHORIZED

## Execution identity

```text
audit model               = GPT-5.6 Thinking (independent audit of the canary results)
execution model           = Qwen2.5-Coder-7B-Instruct, int8, 2× Tesla T4 (Kaggle)
deployed source/build     = 50ec2c1 (SOURCE_COMMIT = 50ec2c1ca43c230aed4538be32ca7dab2ccc22e5,
                             DEPLOYED_BUILD_ID = 50ec2c1)
dedicated canary          = exp-20260804-133523 (todo-smoke-001 / selective)
incidental monolithic     = exp-20260804-133016 (todo-smoke-001 / monolithic) — diagnostic only
continuous cell           = blocked fail-closed by CALIBRATION_REVIEW_REQUIRED
```

## Dedicated selective canary — exp-20260804-133523

```text
scenario:                       todo-smoke-001
strategy:                       selective
status:                         failed
classification:                 model_output
selected artifacts:             3
preserved artifacts:            2
regenerated/written artifacts:  0
model calls:                    4
tokens:                         5,804
duration:                       257.596 seconds
initial generation calls:       3
repair calls:                   1
initial tokens:                 3,372
repair tokens:                  2,432
HF state:                       recovery_uploaded
checkpoint:                     1 completed / 2 pending
```

### Failure causes

- `todo/models.py`: `Task.Priority.MEDIUM` has length 6 but Qwen used
  `max_length=5`.
- `todo/serializers.py`: Qwen duplicated `Priority(models.TextChoices)` in the
  serializer module.
- `todo/views.py`: Qwen duplicated `Priority(models.TextChoices)` in the view
  module.
- The first repair of `models.py` was byte-identical to the initial response.
- `repair_no_progress` stopped the rest of the repair round.
- Atomic application wrote zero files; the workspace code stayed at baseline.

## Comparison with the previous selective run on the same scenario

| Metric | Previous selective | Current selective | Improvement |
|---|---:|---:|---:|
| Calls | 6 | 4 | 33.3% fewer |
| Tokens | 9,944 | 5,804 | 41.6% fewer |
| Duration | 331.863 s | 257.596 s | 22.4% faster |
| Repair calls | 3 | 1 | 66.7% fewer |
| Repair tokens | 6,572 | 2,432 | 63.0% fewer |
| Repair duration | 148.680 s | 74.724 s | 49.7% faster |
| Written artifacts | 0 | 0 | unchanged |

Initial generation tokens were exactly `3,372` in both runs, and the response
SHA-256 values for the three generated files were unchanged. Therefore the model
produced the same bad code; the improvement came entirely from harness controls.

## Incidental generic monolithic run — exp-20260804-133016

The executed notebook also ran its generic one-run cell before the dedicated
canary.

```text
experiment:                     exp-20260804-133016
scenario:                       todo-smoke-001
strategy:                       monolithic
status:                         failed
classification:                 scientific_budget_exhausted
model calls:                    6
tokens:                         7,927
duration:                       300.165 seconds
written artifacts:             0
HF state:                       recovery_uploaded
```

The run generated all five artifacts, including the two preserve-only paths,
then began one repair call. The cooperative deadline stopped the run at about
300 seconds. **This run was NOT the authorized canary** and is retained as
diagnostic calibration evidence only; it must not be called an accepted
comparison result.

## Current selective versus current monolithic

| Metric | Selective | Monolithic | Selective advantage |
|---|---:|---:|---:|
| Calls | 4 | 6 | 33.3% fewer |
| Tokens | 5,804 | 7,927 | 26.8% fewer |
| Duration | 257.596 s | 300.165 s | 14.2% faster |
| Generated scope | 3 required files | 5 files incl. 2 preserve-only | selective is correct |
| Written files | 0 | 0 | tie |
| Working implementation | no | no | tie |

The shared three Qwen outputs were effectively the same bad outputs. Selective
wins on scope and resources, not on functional correctness.

## Closest implementation observed so far

The closest functional attempt remains the historical
`todo-smoke-002 / iterative_repository_agent` run. Its first attempt reached the
scenario evaluator and passed four checks before failing the core soft-delete
requirements. It later regressed during repair.

No current `todo-smoke-001` run reached migration, baseline tests, or the
scenario evaluator.

## Notebook safety result

The continuous cell was executed after the canary but stopped with:

```text
CALIBRATION_REVIEW_REQUIRED
```

This red cell is expected fail-closed behavior. It made no additional scientific
model calls and did not launch the remaining runs.

## Current scientific truth

```text
accepted current dedicated canary records: 1
successful current dedicated canary records: 0
full current 9-record experiment: not run
historical 9-record calibration: 0/9 successful
```

The current evidence supports:

- Selective scope reduction works.
- No-progress detection materially reduces wasted calls and tokens.
- Atomic writes and the continuation gate work.
- Qwen 7B at temperature 0 has a repeatable output-quality floor on
  `todo-smoke-001`.

It does not support:

- a successful implementation;
- a functional superiority claim between strategies;
- a stable scientific release or Pilot authorization.

## Truth statement

```text
dedicated canary experiment    = exp-20260804-133523
source/build                   = 50ec2c1
strategy / scenario            = selective / todo-smoke-001
result                         = 4 calls, 5,804 tokens, 257.596 seconds;
                                 3 selected, 2 preserved, 0 written;
                                 failure model_output
model output defects           = models/serializers/views (max_length=5; duplicated
                                 Priority(models.TextChoices) in serializer and view)
repair_no_progress             = triggered after the first repair was byte-identical
vs previous selective          = 41.6% fewer tokens, 33.3% fewer calls, 22.4% faster
incidental monolithic run      = exp-20260804-133016 — diagnostic evidence only,
                                 NOT the authorized canary, NOT an accepted comparison:
                                 6 calls, 7,927 tokens, 300.165 seconds,
                                 scientific_budget_exhausted
continuous cell                = correctly blocked by CALIBRATION_REVIEW_REQUIRED
accepted current dedicated canary records = 1
successful current records     = 0
full current 9-record experiment = NOT run
merge / tag / Pilot / Kaggle   = NOT authorized
model quality                  = unchanged (output hashes and initial generation tokens
                                 matched the previous run); only harness efficiency improved
stable release                 = NOT claimed
```

## Validation

```text
Markdown formatting    = verified (records/ledgers/docs)
JSONL formatting       = verified (change_metrics.jsonl parses as JSON lines)
git diff --check       = clean
code / tests / data    = NOT modified (documentation- and ledger-only)
git status --short     = clean after push
local HEAD = remote HEAD = <new commit>
```

## Next action

Independent audit of the canary results. No merge, tag, Pilot, or additional
Kaggle execution is authorized. The incidental monolithic run
(`exp-20260804-133016`) is diagnostic calibration evidence only, not an accepted
comparison result.

SELECTIVE_CANARY_RESULTS_DOCUMENTED
