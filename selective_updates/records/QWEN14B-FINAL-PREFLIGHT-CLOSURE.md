# QWEN14B-FINAL-PREFLIGHT-CLOSURE — Final Qwen 14B NF4 Preflight Closure

**Change ID:** QWEN14B-FINAL-PREFLIGHT-CLOSURE
**Date:** 2026-08-05
**Branch:** `fix/kaggle-smoke-v2-model-output-closure`
**Commit A:** `0aa705d` `fix(model): close Qwen 14B Kaggle preflight blockers`
**Commit B:** `cc7846b` `chore(deploy): repin final Qwen 14B preflight bundle`
**Status:** QWEN 14B FINAL PREFLIGHT CLOSURE - ZERO TEST FAILURES (1,890 PASSED / 32 SKIPPED / 0 FAILED IN THE DECLARED PYTEST 8.4.2 CLEAN ENVIRONMENT) - ZERO NEW STATIC FINDINGS - TWO EXPLICIT REGRESSION PROOFS PASS - ONLY NEXT ACTION = KAGGLE ENGINEERING PREFLIGHT CELL

## Truth

```text
branch                      = fix/kaggle-smoke-v2-model-output-closure
commit A                    = 0aa705d  fix(model): close Qwen 14B Kaggle preflight blockers
commit B                    = cc7846b  chore(deploy): repin final Qwen 14B preflight bundle
commit A hash               = 0aa705d1c071827421461922c24f59f45fced029
commit B hash               = cc7846b152a83ae8ea6cfb6b6d56ae1c0f8733a6
local HEAD                  = remote HEAD = cc7846b (pushed; working tree clean)
prior state                 = 5ef6438 was full-suite green but the independent audit rejected real preflight
root cause 1                = the canary used SELECTIVE_CANARY_OUTPUT_DIR before assignment
root cause 2                = the preflight incorrectly required exactly one visible GPU
root cause 3                = the Kaggle numeric version directory produced a qwen:1:* readable identity
gate environment            = declared clean env _workspace\cache\prebenchmark-py311 (Python 3.11.9, pytest 8.4.2)
full test suite             = 1,890 passed / 32 skipped / 0 failed (the only official gate; ambient pytest 9 is NOT the gate)
static findings             = 0 new (Ruff 91 pre-existing in untouched files; changed files clean; mypy strict Success 77 files)
regression proof 1          = 2-GPU otherwise-valid preflight = PASS
regression proof 2          = canary setup reaches subprocess construction without NameError
Kaggle execution            = NOT performed
canary run                  = NOT performed
continuous                  = NOT run
model/quantization          = unchanged (Qwen2.5-Coder-14B-Instruct, bnb-nf4)
prompts/data/scenarios      = unchanged
GPTQ/AWQ/GGUF/vLLM          = not added
merge/tag/Pilot             = not authorized
scientific evidence         = NONE (no new real-run result; current accepted real records remain 0/9)
stable release              = NOT claimed
next action                 = Kaggle engineering preflight cell ONLY (14B bnb-nf4), after independent audit
sentinel                    = QWEN14B_FINAL_PREFLIGHT_CLOSURE_AUDIT_REQUIRED
```

## Fixes

### Fix A — canary output dir used before assignment (notebook)

`notebooks/seven_arm_benchmark.ipynb`: `SELECTIVE_CANARY_OUTPUT_DIR` was assigned
inside the `selective-calibration-canary` cell, after
`CANARY_PREFLIGHT_DIR = SELECTIVE_CANARY_OUTPUT_DIR / "preflight"` — a
`NameError` the moment the canary cell ran. The definition moved to the
`setup-cell` (immediately after `OUTPUT_DIR`), and the duplicate assignment in
the canary cell was removed. Cell order now: setup (defines
`SELECTIVE_CANARY_OUTPUT_DIR`) → ... → selective-calibration-canary (uses it).

### Fix B — preflight required exactly one visible GPU (preflight.py)

`src/benchmark/execution/preflight.py`:
`EXPECTED_VISIBLE_GPU_COUNTS = (1, 2)`; the `gpu_count_expected` check now
passes for 1 or 2 visible GPUs and reports `FAIL (N; expected 1 or 2)`
otherwise. Real 2x Tesla T4 Kaggle environments are no longer rejected.

### Fix C — numeric version dir produced qwen:1:* identity (kaggle_qwen_backend.py)

`src/benchmark/llm/kaggle_qwen_backend.py`: added `import re` and
`_checkpoint_identity_slug(model_path)` which maps a numeric final directory
(e.g. `/kaggle/input/models/qwen-lm/qwen2.5-coder/transformers/14b-instruct/1`)
to `<parent>-v<version>` (e.g. `14b-instruct-v1`), lowercased and sanitized to
`[a-z0-9._-]`. `compute_model_identity` and the `checkpoint_basename` property
now use the slug, so real Kaggle paths produce readable identities
(`qwen:14b-instruct-v1:bnb-nf4:cfg-<12hex>`) instead of `qwen:1:...`.

## Tests added

- `tests/unit/execution/test_preflight.py`:
  `test_gpu_count_matrix` (parametrized 1 / 2 / 0 / 3) and
  `test_two_visible_gpus_otherwise_valid_preflight_passes`.
- `tests/unit/llm/test_llm_kaggle_qwen_backend.py`:
  `TestCheckpointIdentitySlug` (6 tests: v1 vs v2 distinction, slug
  construction, sanitization, checkpoint_basename property).
- `tests/integration/test_kaggle_bundle_smoke_v2_preflight.py`:
  `TestKaggleCanaryOutputDefinitionOrder` (2 tests: definition order/placement,
  reduced-canary exec proof that subprocess construction is reached without
  NameError).

## Full Pre-Benchmark Validation — declared clean environment (pytest 8.4.2)

```text
Dataset Validation          285 passed / 5 skipped
Prompt Validation           174 passed
Pipeline Smoke Test         223 passed / 12 skipped
Scripted 9-record Dry Run   9 planned / 9 terminal / 9 succeeded / 0 failed / exit 0; dashboard + evidence files present
Complete Integration Test   1,890 passed / 32 skipped / 0 failed
Metric Verification         169 passed
Ruff                        0 new findings (91 pre-existing baseline in untouched files; changed files clean)
strict mypy                 Success (77 files, 0 issues)
compileall                  clean
Notebook compilation        8/8 code cells canonical + 8/8 bundled
builder/manifests           content-identical rerun (147 files / 963,067 bytes); manifests verified; no cache files
regression proof 1          2-GPU otherwise-valid preflight = PASS
regression proof 2          canary setup reaches subprocess construction without NameError
git diff --check            clean; working tree clean
```

## Notes

The ambient pytest 9.1.1 result is diagnostic only and never the official gate;
all totals above were produced with the declared pytest 8.4.2 clean environment.
The independent audit must rerun the Kaggle engineering preflight cell only —
not the scientific One-Run cell, not a full relaunch, not a fine-tune, not a
tag/merge.
