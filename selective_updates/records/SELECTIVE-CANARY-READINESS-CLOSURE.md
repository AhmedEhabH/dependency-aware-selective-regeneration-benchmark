# SELECTIVE-CANARY-READINESS-CLOSURE — Final Selective Canary Readiness Closure

**Change ID:** SELECTIVE-CANARY-READINESS-CLOSURE (Final Selective Canary Readiness Closure)
**Date:** 2026-08-04
**Branch:** `fix/kaggle-smoke-v2-model-output-closure`
**HEAD:** `356722b` (pushed; local = remote; working tree clean)
**Status:** FINAL SELECTIVE CANARY READINESS CLOSURE COMPLETE — INDEPENDENT AUDIT REJECTED CANARY READINESS AT f727b3e, THREE BLOCKERS CLOSED, FOCUSED + FULL GATES GREEN (1,856 PASSED / 32 SKIPPED / 0 FAILED) — INDEPENDENT RE-AUDIT REQUIRED BEFORE THE DEDICATED SELECTIVE CANARY CELL

## Truth

```text
branch                    = fix/kaggle-smoke-v2-model-output-closure
HEAD                      = 356722b (pushed; local = remote; working tree clean)
f727b3e truth             = full suite was green but the independent audit rejected canary readiness
direct timeout repro      = 3 calls and false success after deadline (configured 1s, 3 selected artifacts, budget advanced after call 1)
direct atomic metric repro = 0 writes but regenerated_artifact_count = 1 (artifact 2 rejected; all staged, none written)
generic one-run cell      = selected monolithic (todo-smoke-001 / monolithic), NOT selective
commit A                  = 50ec2c1  fix(smoke): enforce per-call deadline and atomic metric truth
commit B                  = 28ecc5a  chore(deploy): pin selective-canary-ready Smoke V2 bundle
commit B2 (test alignment)= 356722b  test(smoke): align affected unit tests with atomic metric truth
complete test totals      = 1,856 passed / 32 skipped / 0 failed (full suite); 629 passed / 1 skipped (grouped per-category)
calibration evidence      = exp-20260803-002741 (9 terminal records: 0 succeeded / 8 failed / 1 timed_out; 81 model calls;
                           118,211 total tokens) - PRESERVED, 0/9 success, not accepted scientific evidence
latest real calibration   = 0/9 successful records (preserved as evidence)
scientific evidence       = NONE (no accepted scientific result yet)
Kaggle rerun              = NOT performed
tag                       = not created
Pilot                     = not authorized
stable release            = NOT claimed
next action               = run the dedicated selective calibration canary cell ONLY, after independent re-audit
```

## The three audit blockers closed

- **Blocker 1 - per-call cooperative deadline.** The workflow budget deadline is
  now checked before every selection, generation, and repair model call, not only
  before entering the whole regeneration attempt. When an in-flight call returns
  beyond the deadline, its tokens/call count are consumed and recorded, no next
  model call is made, none of the staged attempt is written, and the run returns
  the failed scientific terminal `scientific_budget_exhausted` with truthful
  elapsed time and configured budget retained. The same guard applies to every
  internal Iterative Agent model call, not only once before `analyze_impact()`.
  Direct adversarial proof:
  - `TestRunner.test_generation_deadline_stops_after_first_model_call` — 1s
    deadline, 3 selected artifacts, budget advanced after call 1: exactly 1
    model call, failed terminal `scientific_budget_exhausted`,
    `regenerated_artifact_count == 0`, 15 tokens retained.
  - `TestRepairDeadline.test_repair_deadline_stops_after_first_repair_call` —
    backend rewinds `_budget._state.start_time` by 1000s during repair call 2:
    exactly 2 model calls, failed terminal, `regenerated_artifact_count == 0`,
    `repair_model_calls == 1`, repair tokens > 0 retained.
  - `TestIterativeAgentDeadline.test_agent_selection_deadline_stops_after_first_call`
    — guard permits one selection call, second pre-check fails: exactly 1 call,
    `model_call_budget_exhausted` flag set, 50 tokens preserved.
- **Blocker 2 - atomic metric truth.** When an atomic regeneration attempt
  aborts, all staged `generated` statuses become `aborted` or `rejected`,
  `regenerated_artifact_count = 0`, and preserved response hashes/evidence remain
  available. An all-valid attempt still commits every artifact exactly once. This
  is metric/evidence truth, not a change to the scientific formula.
  `tests/unit/execution/test_r4_token_and_metrics.py` now asserts the truthful
  staged statuses (`["aborted", "aborted", "rejected"]` / `["aborted", "rejected"]`)
  instead of the pre-closure buggy `generated` list the audit rejected.
- **Blocker 3 - dedicated selective canary cell.** The generic one-run
  notebook cell is NOT a selective canary (execution-plan order is scenario
  first, then strategies, so it starts `todo-smoke-001 / monolithic`). A
  dedicated, separately named Selective Calibration Canary cell
  (`selective-calibration-canary-cell`) was added with:
  `--strategy selective --max-runs 1 --new-experiment --max-attempts 3
  --max-completion-tokens-per-call 1024 --max-total-workflow-tokens 0 --timeout 300
  --backend kaggle-qwen --profile scientific-smoke-v2 --hf-sync` plus data-dir,
  model-path, and isolated output dir `runs/selective_calibration_canary`. It does
  NOT use `--auto-resume-hf` and does NOT authorize the continuous cell
  (`AUTHORIZE_CONTINUOUS_AFTER_CALIBRATION_REVIEW = False`). `_verify_selective_canary()`
  asserts exactly one RunRecord with `scenario_id = todo-smoke-001` and
  `strategy_id = selective`, current source/build identity, model identity
  `qwen:1:int8`, model calls > 0, terminal scientific success/failure outcome,
  HF `recovery_uploaded`, checkpoint `total_planned = 3` / `completed = 1` /
  `pending = 2`.

## Deployment pin

The canonical and generated notebooks are pinned to:

```text
SOURCE_COMMIT   = 50ec2c1ca43c230aed4538be32ca7dab2ccc22e5
DEPLOYED_BUILD_ID = 50ec2c1
```

Bundle rebuilt via `scripts/build_upload_bundle.py`: 147 files / 948,250 bytes;
manifests verified (code 90 / data 56 / notebook 1); rerun content-identical
(tree hash `3b8d5b0ebf5e3ab8`); no cache files in `kaggle_upload`; all 8 bundle
notebook code cells compile.

## Commit ledger

```text
f727b3e  docs(audit): record calibration results and safety closure           (starting HEAD; audit REJECTED)
50ec2c1  fix(smoke): enforce per-call deadline and atomic metric truth         (Commit A, pushed)
28ecc5a  chore(deploy): pin selective-canary-ready Smoke V2 bundle            (Commit B, pushed)
356722b  test(smoke): align affected unit tests with atomic metric truth       (test alignment, pushed)
```

All pushed to `origin/fix/kaggle-smoke-v2-model-output-closure`; local = remote
verified after each push. Working tree clean.

## Validation

```text
Dataset Validation   = PASS (data unchanged)
Prompt Validation    = PASS (169 focused prompt/context/runner/model/scenario tests passed independently)
Pipeline Smoke Test  = PASS (the two independently reproduced defects now proven closed by direct adversarial tests)
Scripted Dry Run     = PASS (9/9, exit 0, --profile scientific-smoke-v2 into a fresh runs dir)
Integration Test     = PASS (complete integration test green)
Metric Verification  = PASS (169 metric tests passed; atomic-abort count truth asserted)
Ruff                 = 0 new findings (93 = 93 baseline)
strict mypy          = Success (77 files)
compileall           = clean (exit 0)
Notebook compilation = PASS (8/8 bundle code cells; canary cell compiles)
builder/manifests    = content-identical; manifests verified
full suite           = 1,856 passed / 32 skipped / 0 failed
grouped per-category = 629 passed / 1 skipped
git diff --check     = clean
working tree         = clean
```

## Next action

The independent audit at `f727b3e` rejected canary readiness; all three blockers
are now closed, pinned, and gated. **After the independent re-audit, the only
authorized Kaggle action is running the dedicated selective calibration canary
cell** (the `selective-calibration-canary-cell`, output to
`runs/selective_calibration_canary`) — NOT the generic one-run cell, NOT the
continuous cell, NOT a full relaunch, NOT a fine-tune, NOT a tag/merge.

FINAL_SELECTIVE_CANARY_READINESS_AUDIT_REQUIRED
