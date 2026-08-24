# PILOT-EXEC-01 — v0.9.22 Long-Context Attention Memory Closure Report

**Task:** PILOT-EXEC-01-V0922-LONG-CONTEXT-ATTENTION-MEMORY-CLOSURE
**Branch:** `fix/pilot-v0922-long-context-attention-memory-closure` (from clean main `58d1be533c98ca9bafc9a344f2a73f8a140b9540`, v0.9.21 reconciled)
**Status:** v0.9.22 CANDIDATE — release mechanics COMPLETE, TARGET MEMORY PROOF PENDING (no stable tag until the real Kaggle 2x T4 12k probe PASSES)
**Frozen scientific contract:** UNCHANGED (model `Qwen/Qwen2.5-Coder-14B-Instruct`, BNB-NF4, 12 scenarios, 3 repository pins, 2 strategies, 2 repetitions = 48 cells, prompts, Ground Truth, metrics, model/request timeout 600 s, per-cell validation timeout 1800 s, max attempts 3, completion cap 4096, the 12000-token long-context gate, the 64-token probe)

---

## 1. Target evidence (why this closure exists)

The real Kaggle v0.9.21 model preflight passed every stage before the failure:

| Stage | Result |
|---|---|
| Repository preflight | PASS |
| Dependencies | PASS |
| Qwen 14B BNB-NF4 load | PASS (`qwen_model_load[bnb-nf4]: PASS` — the 2026-08-05 dependency-drift OOM fix still works) |
| GPU-only device map | PASS |
| 2x Tesla T4 | PASS |
| Per-GPU headroom | PASS (minimum free 7.764 GiB) |
| Short generation probe | PASS |
| **Long-context probe (12k)** | **FAIL — CUDA OOM** |

OOM arithmetic: **12,044 prompt tokens / 64-token output budget / failed
allocation 21.62 GiB == exactly `12044*12044*40*4 bytes = 21.6153 GiB` — the
full float32 40-head quadratic attention score matrix.**

Diagnosis: the effective runtime attention path materialized the math/eager
fallback during prompt prefill. Offloaded KV cache does not cover prefill
attention; `device_map=auto` is not tensor parallelism. Consequence:
**v0.9.21 Real Pilot REJECTED BEFORE LAUNCH** — no Experiment ID / no RunRecord
created; no stable tag moved; the v0.9.21 repository/per-cell fixes remain
VALID and are carried forward.

## 2. Tasks and closures

### Task A — Explicit SDPA request at load — CLOSED

`from_pretrained(..., attn_implementation="sdpa")` via
`KAGGLE_ATTENTION_IMPLEMENTATION`; the requested value is recorded in evidence.

### Task B — Fail-closed fused-kernel generation policy — CLOSED

Every CUDA generation runs inside
`sdpa_kernel([SDPBackend.FLASH_ATTENTION, SDPBackend.EFFICIENT_ATTENTION])`
(`_sdpa_kernel_policy_context`): the math/eager fallback cannot materialize a
quadratic float32 score matrix on target. Missing `torch.nn.attention` API on
CUDA fails closed with `ModelBackendError` BEFORE any generation attempt;
non-CUDA paths keep `nullcontext()`.

### Task C — Canonical attention evidence + enforcement — CLOSED

Backend properties `requested_attention_implementation`,
`effective_attention_implementation` (reads `model.config._attn_implementation`),
`sdpa_kernel_policy=flash_or_efficient_no_math`. Preflight persists
`requested_attn_implementation` / `effective_attn_implementation` /
`sdpa_kernel_policy` in the JSON payload, renders them in the human table, adds
the fail-closed `attention_policy` check (`SKIP` only when no probe ran;
`FAIL` blocks the 12k long-context probe), and enforces the canonical triple in
`validate_pilot_launch_authorization`.

### Task D — Corrected OOM diagnosis — CLOSED

Long-prompt OOMs (>= `LONG_PROMPT_PREFILL_OOM_TOKEN_THRESHOLD == 2048` prompt
tokens) report prompt-prefill attention evidence plus free-GiB headroom and
NEVER advise completion-cap reduction (the completion cap is a frozen
scientific input and was never the cause). Short-prompt OOMs keep the prior
advice. The original exception text is embedded and chained.

### Tasks E/F — Regression guards — CLOSED

New tests regression-guard every prior memory fix (transformers==4.57.6 pin,
NF4 `low_cpu_mem_usage` load path, offloaded KV cache, GPU-only device map,
per-GPU VRAM gate) and the unchanged 12000-token/64-token long-context gate
constants.

## 3. RED/GREEN evidence

- **RED:** with unmodified v0.9.21 code, **12 backend contract tests**
  (`TestSDPAAttentionContract`, `TestAttentionEvidenceProperties`,
  `TestOOMDiagnosisLongPrompt`) and **18 preflight contract tests**
  (`TestAttentionPolicyGate` + authorization negatives) FAIL: no
  `attn_implementation` kwarg, no kernel policy context, no canonical evidence,
  wrong OOM message.
- **GREEN:** all pass after the fix. Full suite **2407 passed / 33 skipped /
  0 failed** (baseline 2370/33/0).
- Dry-run pilot profile: **48/48 succeeded / 48 unique IDs / 0 model calls /
  0 tokens** (repos todo/djangocms/saleor x16 each; strategies 24/24).

## 4. Release mechanics (COMPLETE except the mandatory Kaggle proof)

> **SUPERSEDED CANDIDATE IDENTITY:** the first candidate anchor freeze rode on
> merge `4827045fce96eb4caa3645e3cf3c8434dca2a1a8` with artifact
> `9182ea2bb091f785ff325a1355caa5bb0f57283764215059092970bbd8014974`; that
> identity is HISTORICAL. The current exact candidate is the consistency
> closure below.

### Final candidate — consistency closure (2026-08-24)

- Non-fast-forward merge of `fix/pilot-v0922-candidate-consistency-closure` to
  `main`: merge commit `ba08392552545baa15c10ae5db2e95ce7496a720`
  (== `origin/main`, pushed). Expected scientific/runtime code delta vs the
  superseded candidate: NONE (tests + release-test constants only).
- Candidate consistency audit (see Section 7): four stale release-test
  constants corrected; one order-dependence test-isolation fix; working-tree
  hygiene restored; full suite **2407 passed / 33 skipped / 0 failed**
  (2440 collected); focused integration 161 passed including the re-enabled
  real expanded-artifact simulation.
- Anchors frozen for the PLANNED tag `v0.9.22-pilot-exec-ready` at
  `ba08392552545baa15c10ae5db2e95ce7496a720` via the idempotent two-pass
  finalizer with `--verify-source-provenance`: embedded trust validation +
  source-provenance gate **0 mismatches** (freeze evidence
  `reports/pilot_notebook_trust_freeze.json`; bundled notebook anchors were
  already correct and required no change).
- Exact candidate artifact built from the merge commit:
  `dist/pilot-kaggle-upload.zip` SHA-256
  `3fd986262936972a6f12adbae21e844adef488dfd76ef0e4b2e6e434b2aa65b3`
  (+ `.sha256` sidecar, verified byte-equal).
- Exact-artifact dry-run gate: **48/48 succeeded / 48 unique IDs /
  repositories todo/djangocms/saleor 16/16/16 / strategies
  selective/iterative_repository_agent 24/24 / repetitions 1|2 x24/24 /
  0 model calls / 0 tokens / every record
  `source_commit == ba08392552545baa15c10ae5db2e95ce7496a720`** from
  `dist/pilot-kaggle-upload/code/seven_arm_benchmark.py`.
- **MANDATORY before tagging:** fresh real Kaggle 2x T4 model preflight ONLY —
  same 12k target, same 64-token probe — requiring `qwen_model_load[bnb-nf4]:
  PASS`, short probe PASS, 12k probe PASS, and
  `requested_attn_implementation=sdpa / effective_attn_implementation=sdpa /
  sdpa_kernel_policy=flash_or_efficient_no_math` with
  `attention_policy: PASS`.
- On PASS: annotate `v0.9.22-pilot-exec-ready` AT the tested merge commit,
  push the tag, then launch the accepted 48-cell Pilot in a fresh session.
- On FAIL: return to the SAME v0.9.22 task (never spawn v0.9.23).

## 5. Alternatives rejected

- Raising the completion cap or shrinking prompts — changes frozen scientific
  inputs and does not address prefill attention.
- FlashAttention-only policy — T4 (SM75) lacks FA2 support; SDPA efficient
  kernels are the correct target backend.
- Trusting `device_map=auto` or offloaded KV cache to bound prefill memory —
  disproven by the exact OOM arithmetic above.
- Silent fallback retention (fail-open) — reproduces the same OOM on target
  without local signal.

## 6. Known open items

- The stable tag `v0.9.22-pilot-exec-ready` does not exist yet; it may be
  created ONLY after the Section 4 Kaggle model-preflight proof PASSES (at
  merge commit `ba08392552545baa15c10ae5db2e95ce7496a720`).
- No scientific claim is made or implied by this closure: Real Pilot remains
  NOT STARTED.

## 7. Candidate consistency audit (2026-08-24, PILOT-EXEC-01 closure)

Independent audit findings and closures, BEFORE the mandatory target proof:

1. **Stale release-test constants** — after the first candidate anchor freeze,
   three full-suite failures (`2403 passed / 34 skipped / 3 failed`, 2440
   collected) were all one release-constant mismatch: tests still expected
   `v0.9.21-pilot-exec-ready` while the notebook/dist identity said v0.9.22.
   Corrected to `v0.9.22-pilot-exec-ready` in
   `tests/integration/test_pilot_deployment_bundle.py` (`PILOT_SOURCE_TAG`),
   `tests/integration/test_pilot_notebook_contract.py`
   (`EXPECTED_FROZEN_SOURCE_TAG`),
   `tests/integration/test_pilot_release_provenance.py`
   (`TARGET_RELEASE_TAG`), `tests/integration/test_pilot_repo_env_provisioning.py`
   (`SOURCE_TAG`). The fourth constant participates in the release-sequencing
   contract. This also re-enabled the previously-skipped real expanded-artifact
   simulation, which now PASSES against the frozen dist artifact. No production
   code was changed to satisfy these tests.
2. **Test-isolation fix (Linux order dependence)** —
   `TestSDPAAttentionContract.test_missing_sdpa_api_on_cuda_fails_closed`
   could be contaminated by an already-cached real/fake
   `sys.modules["torch.nn.attention"]`: the test replaced `torch`/`torch.nn`
   with fakes but left the cached child importable, silently degrading the
   fail-closed contract. Fixed by explicitly removing the cached child before
   installing the fake no-attention runtime, plus a pre-populated-cache
   regression condition inside the same test (RED proven: reverting only the
   removal makes the test fail with "DID NOT RAISE"; GREEN: full backend file
   60/60 regardless of order). Production `_sdpa_kernel_policy_context()`
   untouched.
3. **Generated dry-run working-tree hygiene** — untracked evidence directories
   `runs_dryrun/v0922_attention_closure/`,
   `runs_dryrun/v0922_attention_closure_pilot/`,
   `runs_dryrun/v0922_candidate_artifact/` were verified as recorded in this
   tracked report (Section 3/4) and then deleted; they were never added to Git.
4. **Post-correction full-suite result** — **2407 passed / 33 skipped /
   0 failed** (2440 collected; +1 pass / -1 skip vs the failing run is exactly
   the re-enabled expanded-artifact simulation; the three fixed failures are
   the constants above).
5. **Exact new candidate source commit** — non-ff merge to main:
   `ba08392552545baa15c10ae5db2e95ce7496a720` (pushed).
6. **Exact new artifact SHA** —
   `3fd986262936972a6f12adbae21e844adef488dfd76ef0e4b2e6e434b2aa65b3`
   (+ sidecar byte-equal); trust/provenance **0 mismatches** at that source
   commit; exact-artifact dry-run **48/48** with the new source commit in every
   record (details in Section 4).
7. **Target T4 proof still PENDING** — the long-context attention memory fix
   is NOT yet proven on the real Kaggle 2x Tesla T4 environment; the fresh
   model-preflight-only run (12k probe) is the mandatory next action. v0.9.22
   is NOT accepted/marked stable by this audit.
