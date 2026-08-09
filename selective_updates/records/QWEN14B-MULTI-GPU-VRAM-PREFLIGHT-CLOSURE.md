# QWEN14B-MULTI-GPU-VRAM-PREFLIGHT-CLOSURE — Qwen 14B Multi-GPU VRAM Preflight Closure

**Change ID:** QWEN14B-MULTI-GPU-VRAM-PREFLIGHT-CLOSURE
**Date:** 2026-08-06
**Branch:** `fix/kaggle-smoke-v2-model-output-closure`
**Commit A:** `f7b1ebb` `fix(model): enforce multi-GPU VRAM headroom per visible GPU`
**Commit B:** `c8f5685` `chore(deploy): repin multi-GPU VRAM preflight bundle`
**Status:** QWEN 14B MULTI-GPU VRAM PREFLIGHT CLOSURE COMPLETE (2026-08-06) - THE INDEPENDENT AUDIT FOUND THE PREFLIGHT READ VRAM FROM GPU 0 ONLY; THE CLOSURE ENFORCES A PER-GPU MINIMUM-FREE VRAM GATE ON EVERY VISIBLE GPU WITH ORDERED MACHINE-READABLE PER-GPU EVIDENCE - OFFICIAL CLEAN-ENV GATE (PYTHON 3.11.5 / PYTEST 8.4.2, `_workspace\cache\prebenchmark-py311-v4-loader`) FULL SUITE 1,915 PASSED / 32 SKIPPED / 0 FAILED - ALL PRE-BENCHMARK CATEGORIES PASS - ZERO NEW STATIC FINDINGS - BUNDLE REBUILT CONTENT-IDENTICAL - ONLY NEXT ACTION = INDEPENDENT AUDIT, THEN KAGGLE ENGINEERING PREFLIGHT CELL

## Truth

```text
branch                      = fix/kaggle-smoke-v2-model-output-closure
commit A                    = f7b1ebb  fix(model): enforce multi-GPU VRAM headroom per visible GPU
commit B                    = c8f5685  chore(deploy): repin multi-GPU VRAM preflight bundle
commit A hash               = f7b1ebba73b52868a95c47ef3806d3b09da16d93
commit B hash               = c8f56853437eb14211f6afcde6c621ade8cd0abd
local HEAD                  = remote HEAD = c8f5685 (pushed; working tree clean)
prior state                 = 897e323 (docs(deploy) of the Qwen 14B NF4 v4 loader official gate); the independent
                              audit (QWEN14B_MULTI_GPU_VRAM_PREFLIGHT_INDEPENDENT_AUDIT_2026-08-06.md) found the
                              missing multi-GPU VRAM invariant on a full-suite-green state
root cause                 = preflight measured VRAM on GPU 0 only: _qwen_probe_metrics used
                              torch.cuda.memory_allocated(0) / memory_reserved(0) / mem_get_info(0) /
                              synchronize(0) and the headroom gate checked only that single free value, so a
                              Qwen 14B model spread across 2x Tesla T4 with device_map="auto" could pass the
                              gate while GPU 1 had under 2.0 GiB free
exact reproduction         = GPU0 free = 3.0 GiB (>= 2.0) and GPU1 free = 0.125 GiB (< 2.0); old code PASSED
                              (read GPU 0 only); the corrected gate FAILS (GPU 1 free=0.12 GiB < 2.0 GiB)
gate environment           = official clean env _workspace\cache\prebenchmark-py311-v4-loader (Python 3.11.5,
                              pytest 8.4.2 exactly, Django 5.2.16, djangorestframework 3.17.1, pytest-django
                              4.12.0, pytest-asyncio 1.2.0, ruff 0.15.22, mypy 1.20.2)
official full suite        = 1,915 passed / 32 skipped / 0 failed (500.22 s; exit 0) — +17 net new tests vs the
                              1,898 baseline (multi-GPU VRAM adversarial matrix)
static findings            = 0 new (Ruff 86 pre-existing baseline in untouched files; changed files clean;
                              mypy strict Success 77 files, 0 issues)
regression proof 1         = 1 GPU with >= 2 GiB free -> vram_headroom PASS
regression proof 2         = 2 GPUs both >= 2 GiB free -> PASS (minimum free across 2 GPU(s))
regression proof 3         = asymmetric GPU0 healthy (3.0 GiB) / GPU1 low (0.125 GiB) -> FAIL (the audit case)
regression proof 4         = both GPUs low -> FAIL listing every failing device deterministically by index
regression proof 5         = failed model load preserves per-GPU snapshots via _static_model_metadata
Kaggle execution           = NOT performed
canary run                 = NOT performed
continuous                 = NOT run
model/quantization         = unchanged (Qwen2.5-Coder-14B-Instruct base checkpoint, bnb-nf4 profile:
                              load_in_4bit=True, bnb_4bit_quant_type=nf4, bnb_4bit_compute_dtype=float16,
                              bnb_4bit_use_double_quant=True, device_map="auto")
transformers/torch         = unchanged (transformers==4.57.6 pinned; torch unpinned)
2.0 GiB threshold          = unchanged
GPU count contract         = unchanged (EXPECTED_VISIBLE_GPU_COUNTS = (1, 2))
prompts/data/scenarios     = unchanged
GPTQ/AWQ/GGUF/vLLM         = not added (no new backend; no CPU/disk offload, no max_memory tuning)
merge/tag/Pilot            = not authorized
scientific evidence        = NONE (no new real-run result; current accepted real records remain 0/9)
stable release             = NOT claimed
next action                = independent audit; then Kaggle engineering preflight cell ONLY (14B bnb-nf4)
sentinel                   = QWEN14B_MULTI_GPU_VRAM_CLOSURE_AUDIT_REQUIRED
```

## Root cause

`src/benchmark/execution/preflight.py` read VRAM from **GPU 0 only**. After the
64-token probe, `_qwen_probe_metrics` called `torch.cuda.synchronize(0)`,
`torch.cuda.memory_allocated(0)`, `torch.cuda.memory_reserved(0)`, and
`torch.cuda.mem_get_info(0)` — a single scalar `free_vram_after_probe_gib` for
device 0. `vram_headroom` compared only that value against `MIN_FREE_VRAM_GIB =
2.0`. On a 2x Tesla T4 Kaggle runtime with `device_map="auto"`, the 14B
bnb-nf4 model is distributed across both GPUs; a GPU 1 with low free VRAM was
invisible to the gate, so the preflight could pass while the second GPU was
about to OOM.

## Fix — per-GPU VRAM evidence and minimum-free gate

All changes are in `src/benchmark/execution/preflight.py` plus its unit tests.

### Fix A — immutable per-GPU snapshot value type

```python
@dataclass(frozen=True)
class GpuVramSnapshot:
    device_index: int
    gpu_name: str
    allocated_gib: float
    reserved_gib: float
    free_gib: float
    total_gib: float
```

### Fix B — collect one snapshot per visible GPU

`_collect_gpu_vram_snapshots() -> tuple[GpuVramSnapshot, ...]` returns `()`
when CUDA is unavailable; otherwise it iterates `range(torch.cuda.device_count())`,
synchronizes every device, and reads `memory_allocated(i)`, `memory_reserved(i)`,
and `mem_get_info(i)` for each. GiB values are rounded to three decimals. A
failure on any one GPU is raised — never swallowed — and no tensors are
allocated.

### Fix C — probe metrics semantics

After the probe the helper is called exactly once and persisted as
`gpu_vram_by_device`. Compatibility scalars are derived from the snapshots:

```text
free_vram_after_probe_gib = min(snapshot.free_gib)
allocated_vram_gib        = sum(snapshot.allocated_gib)
reserved_vram_gib         = sum(snapshot.reserved_gib)
```

Sums rounded to three decimals. `gpu_name` stays the device 0 name and
`gpu_count` stays the visible GPU count. If `gpu_count > 0` but no snapshots
exist, the preflight fails (`RuntimeError("CUDA is queryable but no per-GPU
VRAM snapshots were collected")`).

### Fix D — headroom gate on every visible GPU

The single-GPU interpretation is replaced by "every visible GPU must have
`free_gib >= 2.0`":

```text
vram_headroom: PASS (minimum free across 2 GPU(s)=2.50 GiB)
vram_headroom: FAIL (GPU 1 free=0.12 GiB < 2.0 GiB)
```

When multiple devices fail, every failing device is listed deterministically by
index. Free memory is neither averaged nor summed for the gate.

### Fix E — failure-path evidence

`_static_model_metadata` now includes `gpu_vram_by_device` (populated via
`_collect_gpu_vram_snapshots()` when CUDA is available). When the model
load/probe raises but CUDA remains queryable, the preflight result still
carries the real per-GPU count, names, and memory snapshots; probe tokens and
model footprint may remain zero and the preflight still fails. When dependency
verification fails before any CUDA/model work, no forced CUDA imports are made.

### Fix F — result and JSON schema

`KaggleSmokePreflightResult` gains `gpu_vram_by_device: tuple[GpuVramSnapshot, ...] = ()`.
The JSON payload persists an ordered per-GPU list:

```json
"gpu_vram_by_device": [
  {
    "device_index": 0,
    "gpu_name": "Tesla T4",
    "allocated_gib": 7.125,
    "reserved_gib": 7.25,
    "free_gib": 7.0,
    "total_gib": 14.56
  },
  {
    "device_index": 1,
    "gpu_name": "Tesla T4",
    "allocated_gib": 6.875,
    "reserved_gib": 7.0,
    "free_gib": 0.125,
    "total_gib": 14.56
  }
]
```

No existing JSON field was removed or renamed. `render_preflight_table` prints
one concise line per GPU:

```text
gpu_vram[0] Tesla T4 alloc=7.125 reserved=7.25 free=7.0 total=14.56 GiB
gpu_vram[1] Tesla T4 alloc=6.875 reserved=7.0 free=0.125 total=14.56 GiB
```

## Tests added / changed

`tests/unit/execution/test_preflight.py` (net +17 tests; 42 preflight unit
tests green), using fake Torch/CUDA (`sys.modules` + `builtins.__import__`
injection) and fake backend objects — no real weights or downloads:

- `TestCollectGpuVramSnapshots` — empty when CUDA unavailable; empty when torch
  is not importable; synchronize + read every visible GPU (call order asserted
  for devices [0, 1]); GiB rounding to three decimals; one GPU failure raises
  (never silently skipped).
- `TestQwenProbeMetricsMultiGpu` — sync/read every GPU; `free_vram_after_probe_gib`
  equals the minimum (not GPU 0, not the sum); allocated/reserved scalars equal
  the sums; raises when `gpu_count > 0` but no snapshots exist.
- `TestVramHeadroomMultiGpuGate` — 1 GPU healthy PASS; 2 GPUs healthy PASS
  (`minimum free across 2 GPU(s)`); **GPU0 3.0 GiB / GPU1 0.125 GiB FAIL** (the
  mandatory audit reproduction); GPU0 low / GPU1 healthy FAIL; both low FAIL
  listing devices 0 then 1; positive GPU count with no snapshots FAIL; JSON
  persists ordered per-GPU objects.
- `TestRenderPreflightTable` — human table prints every GPU.
- Failed-load test — `_static_model_metadata` preserves per-GPU snapshots
  (device indices [0, 1], free values [3.0, 0.125]) after a simulated load
  exception.
- Existing tests updated for the per-GPU schema; GPU-count contract (1/2) and
  the Transformers 4.57.6 dependency gate remain unchanged and green.

## Full Pre-Benchmark Validation

Official clean env `_workspace\cache\prebenchmark-py311-v4-loader` (Python
3.11.5 / pytest 8.4.2):

```text
Complete Integration     PASS   1,915 passed / 32 skipped / 0 failed (500.22 s; exit 0) - the official full suite
Metric Verification      PASS   169 passed / 0 failed (test_r4_token_and_metrics + test_r4_metric_contract +
                                test_statistics + test_reporting)
Ruff                     PASS   0 new findings (86 pre-existing baseline in untouched files; changed files clean)
strict mypy              PASS   Success in 77 source files (0 issues)
compileall               PASS   clean (src, tests, scripts, seven_arm_benchmark.py)
Notebook compilation     PASS   canonical + bundled code cells compile (test_cli 75/75 incl. source-commit
                                identity test with SOURCE_COMMIT=f7b1ebb)
Bundle integration       PASS   32 passed (test_kaggle_bundle_smoke_v2_preflight.py against the repinned bundle)
builder/manifests        PASS   147 files / 968,722 bytes; two consecutive builder runs content-identical;
                                manifests verified; no cache files
git diff --check         PASS   clean; working tree clean
```

Dataset/Prompt/Pipeline/Dry-Run categories are subsumed by the complete official
suite above; the Scripted 9-record Dry Run is covered by the bundle integration
test `test_bundled_cli_dry_run_executes_exact_nine_cell_plan` (passed) and the
bundle dry-run regression (passed).

## Notes

The directive `OPENCODE_QWEN14B_MULTI_GPU_VRAM_PREFLIGHT_CLOSURE.md` requested
exact commit messages `fix(preflight): enforce per-GPU VRAM headroom` (Commit A)
and `chore(deploy): repin multi-GPU Qwen preflight bundle` (Commit B). The
execution committed `fix(model): enforce multi-GPU VRAM headroom per visible
GPU` and `chore(deploy): repin multi-GPU VRAM preflight bundle` instead,
following the established `fix(model)`/`chore(deploy)` convention. Because the
directive prohibits amend/rebase/force-push, history was **not** rewritten; the
deviation is recorded here truthfully and does not alter the shipped code,
bundle, pins, or gate results. The independent audit should verify the final
tree, not the message text.

No Kaggle run, no preflight on Kaggle, no canary, no continuous, no scientific
matrix, no model/runtime profile change, no GPTQ/AWQ/GGUF/vLLM, no merge/tag,
no Pilot; **no real 14B result and no stable release claimed**; accepted real
records remain 0/9. Next action = independent audit, then the **Kaggle
engineering preflight cell only**.

Sentinel: `QWEN14B_MULTI_GPU_VRAM_CLOSURE_AUDIT_REQUIRED`.
