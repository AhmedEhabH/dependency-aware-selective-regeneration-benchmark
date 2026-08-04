# QWEN14B-BNB-NF4-CANARY-READINESS — Qwen 14B BNB-NF4 Canary Closure

**Change ID:** QWEN14B-BNB-NF4-CANARY-READINESS
**Date:** 2026-08-05
**Branch:** `fix/kaggle-smoke-v2-model-output-closure`
**Commit A:** `0ece665` `fix(model): add model-aware Qwen BNB quantization profiles`
**Commit B:** `0a596b8` `chore(deploy): pin Qwen 14B NF4 selective-canary bundle`
**Status:** QWEN 14B BNB-NF4 CANARY PREPARATION COMPLETE - ZERO TEST FAILURES (1,877 PASSED / 32 SKIPPED / 0 FAILED) - ZERO NEW STATIC FINDINGS - ONLY NEXT ACTION = KAGGLE PREFLIGHT

## Truth

```text
branch                      = fix/kaggle-smoke-v2-model-output-closure
commit A                    = 0ece665  fix(model): add model-aware Qwen BNB quantization profiles
commit B                    = 0a596b8  chore(deploy): pin Qwen 14B NF4 selective-canary bundle
local HEAD                  = remote HEAD = 0a596b8 (pushed; working tree clean)
identity before             = qwen:1:int8 (frozen, model-blind)
identity after              = qwen:<checkpoint-basename>:<quantization>:cfg-<12hex of SHA-256 of canonical payload>
canonical modes             = bnb-int8, bnb-nf4, fp16
notebook model path         = /kaggle/input/models/qwen-lm/qwen2.5-coder/transformers/14b-instruct/1
notebook quantization       = bnb-nf4
notebook canary output      = /kaggle/working/runs/qwen14b_bnb_nf4_selective_canary
generic one-run cell        = disabled by default (RUN_GENERIC_ONE_RUN = False)
continuous authorization    = False
full test suite             = 1,877 passed / 32 skipped / 0 failed
static findings             = 0 new (Ruff 21 pre-existing; mypy 5 pre-existing, identical rule set to self-contained HEAD baseline)
Kaggle execution            = NOT performed
tag                         = not created
Pilot                       = not authorized
scientific evidence         = NONE (no new real-run result in this closure)
next action                 = Kaggle engineering preflight ONLY (14B bnb-nf4)
```

## Preserved failed 14B GPTQ attempt - engineering evidence only

```text
Notebook model path        = Qwen2.5-Coder-14B-Instruct-GPTQ-Int4
Backend requested           = BitsAndBytes int8
Preflight                   = failed before model probe
Root cause                  = GPTQConfig checkpoint + BitsAndBytesConfig loader conflict
Dedicated selective exp     = exp-20260804-195126
Scientific records          = 0
Model calls                 = 0
Tokens                      = 0
```

Identity contamination: the generic auto-resume cell downloaded
`exp-20260804-133016` because both the 7B and the attempted 14B runs were
incorrectly labeled `qwen:1:int8`. That is identity contamination, not a 14B
result. Historical `qwen:1:int8` records are preserved and never rewritten.

## Why GPTQ support was deferred

GPTQ is a different quantization stack (checkpoint pre-quantized with
`GPTQConfig`), incompatible with the bitsandbytes runtime already declared for
the Kaggle backend. The official unquantized
`Qwen2.5-Coder-14B-Instruct` checkpoint is quantized on load with bitsandbytes,
so no GPTQ/AWQ/GGUF/vLLM/ExLlama/AutoGPTQ/GPTQModel/model-server support is
added in this phase.

## Exact 14B BNB-NF4 profile (Tesla T4)

```python
BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)
```

Canonical modes: `bnb-int8` (preserves the existing 7B `load_in_8bit=True`
behavior), `bnb-nf4` (above), `fp16` (float16 on T4). CLI flag
`--qwen-quantization {bnb-int8,bnb-nf4,fp16}` default `bnb-int8`; unknown values
exit 2 before any execution. No automatic fallback.

## Model-aware identity (mandatory scientific fix)

Replaced the frozen `qwen:1:int8` with a deterministic identity derived before
auto-resume from `config.json` fields (model_type, hidden_size,
num_hidden_layers, num_attention_heads) + requested mode + checkpoint
quantization method + SHA-256 (first 12 hex chars) of the canonical payload:

```text
qwen:<checkpoint-basename>:<quantization>:cfg-<12hex>
```

Verified to differ across 7B bnb-int8 / 14B bnb-int8 / 14B bnb-nf4, and stable
for identical config bytes. Weight loading is never required to compute the
identity. Auto-resume and checkpoint validation reject any identity mismatch.

## Prequantized-checkpoint fail-fast

If a checkpoint carries a non-bitsandbytes `quantization_config`
(GPTQ/AWQ/GGUF/...) while bnb-int8 or bnb-nf4 is requested, load fails before
tokenizer/model load:

```text
PREQUANTIZED_CHECKPOINT_INCOMPATIBLE:
checkpoint quantization=gptq
requested loader=bnb-nf4
attach the unquantized Qwen2.5-Coder-14B-Instruct checkpoint
```

## Gate totals

```text
Dataset Validation      PASS   27 scenario files / 27 unique IDs / 0 duplicates / 3 smoke IDs; zero dataset changes in closure
Prompt Validation       PASS   380 passed / 10 skipped / 0 failed
Pipeline Smoke Test     PASS   189 passed / 12 skipped / 0 failed
Scripted 9-record Dry   PASS   9/9 succeeded / 0 failed / exit 0 (scientific-smoke-v2, fresh dir)
Complete Integration    PASS   1,877 passed / 32 skipped / 0 failed (full tests suite, 631.20 s)
Metric Verification     PASS   169 passed / 0 failed
Ruff                    PASS   0 new findings (21 pre-existing: 5 seven_arm_benchmark.py + 16 test_hf_sync.py, line-set identical to HEAD)
strict mypy             PASS   0 new findings (5 pre-existing in seven_arm_benchmark.py, identical rule set to self-contained HEAD baseline)
compileall              PASS   8 changed Python files compile
Notebook compilation    PASS   canonical 8/8 code cells + bundled 8/8 code cells compile
builder/manifests       PASS   147 files / 962,188 bytes; rerun content-identical; manifests verified; no cache files
```

## Authorized files changed

```text
src/benchmark/llm/kaggle_qwen_backend.py    (NF4 profile, CANONICAL_QUANTIZATION_MODES, compute_model_identity, quantization-aware _load_model, prequantized fail-fast)
src/benchmark/execution/preflight.py        (qwen_model_load[<mode>], gpu_count_expected, checkpoint_not_prequantized, requested_quantization_mode, checkpoint fields)
seven_arm_benchmark.py                      (--qwen-quantization, identity via compute_model_identity, config-hash includes qwen_quantization)
tests/unit/llm/test_llm_kaggle_qwen_backend.py  (23 passed)
tests/unit/execution/test_preflight.py          (15 passed)
tests/unit/test_cli.py                          (TestModelIdentity + TestQwenQuantizationFlag)
tests/unit/test_hf_sync.py                      (identity-mismatch rejection updated)
tests/integration/test_kaggle_bundle_smoke_v2_preflight.py  (30 passed)
notebooks/seven_arm_benchmark.ipynb         (14B base path, QWEN_QUANTIZATION, RUN_GENERIC_ONE_RUN, canary preflight gate, pin 0ece665)
kaggle_upload/**                            (builder-generated only)
```

## Commit hashes and remote equality

```text
commit A = 0ece665ef25e1b0ca3aa14f5f25977cadbd06d0c  fix(model): add model-aware Qwen BNB quantization profiles
commit B = 0a596b83bd971aacad52806461c237a72784eaef  chore(deploy): pin Qwen 14B NF4 selective-canary bundle
local HEAD = remote HEAD = 0a596b8 (pushed; working tree clean)
```

## Next action

```text
Kaggle engineering preflight ONLY for the 14B bnb-nf4 profile
(after independent readiness audit if required).
No Kaggle scientific run, merge, tag, or Pilot.
```

Sentinel: `QWEN14B_NF4_CANARY_READINESS_AUDIT_REQUIRED`
