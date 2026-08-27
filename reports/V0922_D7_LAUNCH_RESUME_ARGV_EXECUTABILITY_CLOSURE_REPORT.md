# v0.9.22 D7 Launch/Resume Validation-ARGV Executability Closure

**Date:** 2026-08-27  
**Branch:** `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure`  
**Starting HEAD:** `1b857fc9fce77e6b637ef292c393d28620e92fdc`  
**Artifact source / future tag target:** `3ebc75dad2f47c8985ce045bcdc8907ce2d52f3c`  
**Freeze-report commit:** `acae4c4`  
**Exact artifact:** `dist/pilot-kaggle-upload.zip` SHA-256 `e0a649375104b44d1de7bc5f39145f81bc21365a4380755e73cb1efb719390a8`  
**Stable tag:** does not exist; real 2x T4 proof remains mandatory

## Closure

D6 was already resolved before D7 began: branch push parity and a verified
post-push project export were proven at `1b857fc…`. D7 independently reproduced
a separate launch-safety defect in both `pilot-launch-cell` and
`pilot-resume-cell`: the three `--validation-python` mappings and
`--validation-timeout 1800` were present as notebook text but absent from the
assigned command-list AST because seven adjacent source elements in each cell
lacked newline terminators and were consumed by the preceding comment.

The narrow fix adds only the missing newline terminators. Exact AST tests now
locate `exec_cmd` / `resume_cmd` and require, in order, the live Todo, django CMS,
and Saleor interpreter expressions, one live validation timeout of `1800`, their
position before `--hf-repo-id`, and the unchanged scientific `--timeout 600`.
Canonical and freshly built bundled notebooks also require newline-preserving
list-backed code-cell serialization, and the bundled notebook must satisfy the
same executable argv contract.

## RED / GREEN evidence

- RED against starting behavior: AST count was zero for
  `pilot-launch-cell`; serialization failed at launch source element 35. The
  equivalent resume defect was independently inspected at elements 13–19.
- Focused GREEN: 3/3 AST/newline/fresh-bundle tests.
- Affected regression GREEN: 102/102, including D1–D5 GQA, executable
  microprobe/fail-closed AST, real `_run_tee` timeout, mojibake, notebook, and
  v0.9.21 validation-runtime suites.
- Ruff on both changed Python tests: PASS.
- Python 3.11 compile on both changed Python tests: PASS.
- Canonical and exact extracted bundled notebook code-cell AST compile: PASS.
- Full acceptance: **2442 passed / 33 skipped / 0 failed**.

## Exact artifact acceptance

The deterministic two-pass finalizer ran with
`--source-commit 3ebc75dad2f47c8985ce045bcdc8907ce2d52f3c`, planned tag
`v0.9.22-pilot-exec-ready`, and `--verify-source-provenance`, without
`--allow-acquire`. The freeze report is `FROZEN`; provenance has zero
mismatches; archive, sidecar, and freeze-report hashes all equal
`e0a649375104b44d1de7bc5f39145f81bc21365a4380755e73cb1efb719390a8`.

Fresh extraction plus the exact bundled CLI dry-run passed **48/48**: 48 unique
IDs, Todo/django CMS/Saleor 16/16/16, iterative/selective 24/24, repetitions
24/24, zero model calls, zero tokens, and every record source commit equal to
`3ebc75dad2f47c8985ce045bcdc8907ce2d52f3c`.

## Scientific and release truth

No dataset, scenario, prompt, Ground Truth, metric, evaluator, repository pin,
model, quantization, SDPA/GQA policy, 12000/64 gate, strategy, repetition,
attempt, or token budget changed. `ce40b330…` / `f72ecda…` are superseded and
must not be uploaded. No Kaggle run occurred. No tag was created. The next
action remains the real 2x T4 model-preflight-only proof using the exact new
artifact; create `v0.9.22-pilot-exec-ready` at `3ebc75d…` only after the GQA
microprobe, short probe, and 12k probe all pass. Do not launch 48 cells while
untagged; on failure return to this same v0.9.22 task.

