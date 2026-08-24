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

- Non-fast-forward merge of the branch to `main`: merge commit
  `4827045fce96eb4caa3645e3cf3c8434dca2a1a8` (== `origin/main`, pushed). The
  anchor-freeze notebook commit (`806ee7e`) rode on the branch so the anchored
  notebook is inside the tagged tree (V0921 pattern); an earlier untagged
  pre-freeze merge (`b622f58`) was superseded by this final merge.
- Anchors frozen for the PLANNED tag `v0.9.22-pilot-exec-ready` at
  `4827045fce96eb4caa3645e3cf3c8434dca2a1a8` via the idempotent two-pass
  finalizer with `--verify-source-provenance`: embedded trust validation +
  source-provenance gate **0 mismatches** (freeze evidence
  `reports/pilot_notebook_trust_freeze.json`; code_manifest_sha256 updated to
  `3c52b6200d8c1f2c80999ee09d1af0211adfaae71c3785c574737f606e0872a6`).
- Exact candidate artifact built from the merge commit:
  `dist/pilot-kaggle-upload.zip` SHA-256
  `9182ea2bb091f785ff325a1355caa5bb0f57283764215059092970bbd8014974`
  (+ `.sha256` sidecar, verified byte-equal).
- Exact-artifact dry-run gate: **48/48 succeeded / 48 unique IDs / 0 model
  calls / 0 tokens** from `dist/pilot-kaggle-upload/code/seven_arm_benchmark.py`.
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
  merge commit `4827045fce96eb4caa3645e3cf3c8434dca2a1a8`).
- No scientific claim is made or implied by this closure: Real Pilot remains
  NOT STARTED.
