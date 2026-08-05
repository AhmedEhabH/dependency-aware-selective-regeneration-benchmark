# QWEN14B-NF4-TRANSFORMERS-V4-LOADER-CLOSURE — Qwen 14B NF4 Transformers v4 Loader Closure

**Change ID:** QWEN14B-NF4-TRANSFORMERS-V4-LOADER-CLOSURE
**Date:** 2026-08-05
**Branch:** `fix/kaggle-smoke-v2-model-output-closure`
**Commit A:** `41e9ad7` `fix(model): pin transformers==4.57.6 BNB loader and preserve static preflight metadata`
**Commit B:** `920ab9b` `chore(deploy): repin Qwen 14B NF4 v4 loader closure bundle`
**Status:** QWEN 14B NF4 TRANSFORMERS V4 LOADER CLOSURE - FULL SUITE GREEN (1,898 PASSED / 32 SKIPPED / 0 FAILED) - ZERO NEW STATIC FINDINGS - ADVERSARIAL LOADER TESTS PASS - ONLY NEXT ACTION = INDEPENDENT AUDIT, THEN KAGGLE ENGINEERING PREFLIGHT CELL

## Truth

```text
branch                      = fix/kaggle-smoke-v2-model-output-closure
commit A                    = 41e9ad7  fix(model): pin transformers==4.57.6 BNB loader and preserve static preflight metadata
commit B                    = 920ab9b  chore(deploy): repin Qwen 14B NF4 v4 loader closure bundle
commit A hash               = 41e9ad70c86ac696ce6ceaacd6b6892889bcc48a
commit B hash               = 920ab9b75ff86ae41722fc8ec0e6f381282f54b5
local HEAD                  = remote HEAD = 920ab9b (pushed; working tree clean)
prior state                 = 9fd4eee (docs(audit) of the final preflight closure); the independent OOM audit
                              (QWEN14B_NF4_KAGGLE_OOM_INDEPENDENT_AUDIT_2026-08-05.md) reproduced transformers 5.0.0
                              materializing the 14B BF16 weights on GPU BEFORE BNB-NF4 quantization -> OOM after
                              232.412 s at ~75% of 579 checkpoint params; tried 136 MiB; GPU 1 free 46.81 MiB;
                              allocated 14.38 GiB; runtime Python 3.12.13, transformers 5.0.0, bitsandbytes 0.49.2,
                              accelerate 1.14.0, torch 2.10.0+cu128
root cause                 = transformers was unpinned (Kaggle image drift -> 5.0.0); the new loader path
                              materialized a full-precision temporary copy before quantization, so the 14B BF16
                              weights alone exhausted Tesla T4 VRAM and OOM'd before BNB-NF4 could land
gate environment           = ambient Python 3.11.5 / pytest 9.1.1 (the declared clean env
                              _workspace\cache\prebenchmark-py311 was NOT present on this machine; independent audit
                              should recreate it from declarations for the official gate)
full test suite             = 1,898 passed / 32 skipped / 0 failed (539.32 s); +8 new adversarial tests vs the 1,890 gate
static findings             = 0 new (Ruff 86 pre-existing baseline in untouched files; changed files clean;
                              mypy strict Success 77 files, 0 issues)
regression proof 1          = preflight FAILs on transformers 5.0.0 / any version != 4.57.6 BEFORE staging/model load
regression proof 2          = BNB int8 + NF4 loads pass low_cpu_mem_usage=True; fp16 does not
regression proof 3          = static model/GPU metadata (identity, checkpoint basename, quantization method,
                              gpu_count, gpu_name) preserved when the model load OOMs/fails
Kaggle execution            = NOT performed
canary run                  = NOT performed
continuous                  = NOT run
model/quantization          = unchanged (Qwen2.5-Coder-14B-Instruct base checkpoint, bnb-nf4 profile: load_in_4bit=True,
                              bnb_4bit_quant_type=nf4, bnb_4bit_compute_dtype=float16, bnb_4bit_use_double_quant=True)
torch                       = preserved (Kaggle-provided torch; never pinned in the lock)
prompts/data/scenarios      = unchanged
GPTQ/AWQ/GGUF/vLLM          = not added (no new backend)
merge/tag/Pilot             = not authorized
scientific evidence         = NONE (no new real-run result; current accepted real records remain 0/9)
stable release              = NOT claimed
next action                 = independent audit; then Kaggle engineering preflight cell ONLY (14B bnb-nf4)
sentinel                    = QWEN14B_V4_LOADER_CLOSURE_AUDIT_REQUIRED
```

## Fixes

### Fix A — exact transformers pin (runtime lock + Kaggle requirements)

`requirements-smoke-kaggle.lock` gains `transformers==4.57.6` (installed by the
Notebook `install-lock-cell` before any experiment). `torch` remains
intentionally omitted so Kaggle's compatible GPU torch build is preserved and
recorded in `runtime_environment.json`. `requirements-kaggle.txt` moves
`transformers>=4.30` to `transformers==4.57.6` so the declared Kaggle runtime
matches the lock.

### Fix B — exact version required by preflight before any staging/model load

`src/benchmark/execution/preflight.py` `_REQUIRED_IMPORTS` changes the
`transformers` entry from `None` (record-only) to the exact `"4.57.6"`.
`dependency_import_verification` now FAILs on any other installed version and,
because `runtime_contract_failed` short-circuits, the preflight reports
`baseline_staging: SKIP`, `qwen_model_load[...]: SKIP` and never stages or loads
a 14B model under a non-canonical loader.

### Fix C — Notebook install-lock-cell expects transformers 4.57.6

`notebooks/seven_arm_benchmark.ipynb` `install-lock-cell` `EXPECTED_RUNTIME`
gains `"transformers": ("transformers", "transformers", "4.57.6")`. The existing
fail-closed mismatch check raises on any drift and the version is recorded in
`runtime_environment.json`.

### Fix D — low_cpu_mem_usage=True for BNB loading

`src/benchmark/llm/kaggle_qwen_backend.py` `_load_model` sets
`load_kwargs["low_cpu_mem_usage"] = True` inside the `bnb-int8`/`bnb-nf4`
branch. This tells the 4.57.x loader to stream/quantize weights in place instead
of materializing a full-precision temporary copy — the direct cause of the
reproduced OOM. `fp16` mode is unchanged.

### Fix E — static model/GPU metadata preserved when the load fails

`src/benchmark/execution/preflight.py` adds `_static_model_metadata(model_path,
quantization_mode)`, which derives `model_identity`, `model_checkpoint_basename`,
`checkpoint_quantization_method`, `gpu_count`, and `gpu_name` from `config.json`
and CUDA device discovery only — never loading weights. The probe-failure path
now fills `probe_metrics` from it, so a failed/OOM'd preflight still reports the
real model identity and GPU state (e.g. `qwen:14b-instruct-v1:bnb-nf4:cfg-...`,
`gpu_count=2`, `gpu_name=Tesla T4`) instead of empty/zero fields.

## Tests added / changed

- `tests/unit/execution/test_preflight.py`:
  - `test_fail_when_transformers_version_drifts` — `transformers=5.0.0` FAILs
    preflight with `transformers=5.0.0 (expected 4.57.6)` and the probe is
    skipped.
  - `test_fail_when_transformers_not_installed` — `transformers=NOT_INSTALLED`
    FAILs preflight.
  - `test_static_model_metadata_preserved_when_probe_fails` — a probe
    `RuntimeError("simulated CUDA OOM")` still yields the real model identity,
    basename, quantization mode, `gpu_count=2`, `gpu_name=Tesla T4`.
  - `TestStaticModelMetadata` (2 tests) — config.json-derived metadata without
    weight loading; missing checkpoint preserves mode with blank identity.
- `tests/unit/llm/test_llm_kaggle_qwen_backend.py`:
  - `test_bnb_nf4_load_passes_low_cpu_mem_usage`,
    `test_bnb_int8_load_passes_low_cpu_mem_usage` — `low_cpu_mem_usage is True`
    alongside the canonical quantization config.
  - `test_fp16_load_does_not_set_low_cpu_mem_usage`.
- `tests/integration/test_kaggle_bundle_smoke_v2_preflight.py`:
  `test_requirements_smoke_kaggle_lock_bundled_with_exact_pins` now requires
  `transformers==4.57.6` in the bundled lock and keeps the torch-must-not-be-
  pinned assertion.

## Full Pre-Benchmark Validation

```text
Full test suite            1,898 passed / 32 skipped / 0 failed (539.32 s; ambient Python 3.11.5 / pytest 9.1.1)
Ruff                        0 new findings (86 pre-existing baseline in untouched files; changed files clean)
strict mypy                 Success (77 files, 0 issues)
py_compile                  clean on changed files
Notebook                    install-lock-cell compiles; canonical + bundled code cells compile (test_cli suite)
Bundle pin identity         test_notebook_source_commit_matches_deployed_runtime_tree PASS (SOURCE_COMMIT=41e9ad7)
Bundle integration          32 passed (test_kaggle_bundle_smoke_v2_preflight.py)
builder/manifests           content-identical rerun (147 files / 964,859 bytes); manifests verified; no cache files
git diff --check            clean; working tree clean
```

## Notes

The declared clean gate environment `_workspace\cache\prebenchmark-py311`
(Python 3.11.9 / pytest 8.4.2) is not present on this machine, so the official
gate could not be reproduced locally; the full suite was run under the ambient
interpreter and is green. The independent audit should recreate the declared
environment from declarations and rerun the gate, then run the Kaggle
engineering preflight cell only — not the scientific One-Run cell, not a full
relaunch, not a fine-tune, not a tag/merge.
