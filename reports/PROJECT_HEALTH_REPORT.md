# Project Health Report

**Report Date:** 2026-08-07
**Project:** Dependency-Aware Selective Regeneration Benchmark
**Branch:** `fix/kaggle-smoke-v2-model-output-closure` (HEAD `5561f918`, pushed; Qwen 14B SELECTIVE CANARY SUCCESS accepted and recorded docs-only)
**R4/R5/R6 status:** R4 ACCEPTED AND FROZEN (`f5ae826`); R5 ACCEPTED AND FROZEN (`7761c48`); R6 ACCEPTED AND FROZEN (`949e9c2`) by the final independent re-audit (GPT-5.6 Thinking, 2026-08-01); milestone branch **published** to origin (freeze commit `4b2dd27` = first publication HEAD, local/remote equality verified).
**QWEN 14B SELECTIVE CANARY SUCCESS (2026-08-07):** independent GPT-5.6 Thinking audit **ACCEPTED SUCCESSFUL REAL CANARY**. Real engineering preflight **PASS** on 2×Tesla T4 (bnb-nf4, identity `qwen:14b-instruct-v1:bnb-nf4:cfg-cc9474140d25`, footprint 9,721,981,184 bytes, preflight 174.016 s, probe 68+17 tokens, minimum free VRAM 8.417 GiB, GPU-only). Canary `exp-20260807-131819` (`todo-smoke-001 / selective`, source/build `f7b1ebb`) **succeeded**: 3 selected / 2 preserved / 3 regenerated; migration `0004_task_priority.py`; 3 calls / 2,527 prompt + 720 completion = 3,247 tokens / 295.944 s / 0 repairs; functional validation PASS; evaluator PASS 10/10; HF `recovery_uploaded`. **Accepted real 14B canary records = 1 succeeded / 0 failed** (isolated selective-only plan — NOT 1/9). **Full 9-record Scientific Smoke V2 = NOT RUN.** Next action = one fresh Full-9 via `docs/KAGGLE_QWEN14B_FULL9_SCIENTIFIC_SMOKE_RUNBOOK.md`. Sentinel `QWEN14B_CANARY_SUCCESS_DOCUMENTED_FULL9_READY`. Docs-only closure; no code/tests/data/prompts/configs/notebook/kaggle_upload changes.
**Post-R6:** two real Kaggle attempts failed pre-model (`exp-20260801-024041`, `exp-20260801-024624`; both 0 model calls); real runtime blockers closed and pinned — fix `de3163f`, bundle pin `fb60972` (core accepted by the independent runtime-fix audit); R7A hardening closed all four audit findings (source `d50e89e`, bundle `4c73db6`); a later real attempt reached 81 model calls / 47,694 tokens with 0 succeeded / 0 regenerated files; the attempt `exp-20260801-123125` failed at runtime root (FP16 OOM + dependency drift). **R7B Smoke Finish complete (`bff0a82` + `17207bf`); R7C real-run root closure complete (`7a80e53` + `f01b8f0`) + correction imported (`ffa179a` + `6d6aa36`) + post-gate correction imported (`6f88823` + `5797fc0`, HEAD `5797fc0`, pushed); deterministic interpreter closure complete (`aac9914` + `311e084`); PRE-BENCHMARK FINAL SOURCE REPIN COMPLETE AND GREEN (`769d84e` + `e5d9430` declarations, deployment-only correction `f8d00d7`, HEAD `f8d00d7`, pushed) — previous `76a6b16` gate = 1,833 passed / 32 skipped / 1 failed (structural notebook-pin identity test, truthful, not forced green); complete clean suite then 1,834 passed / 32 skipped / 0 failed. POST-SMOKE CALIBRATION CLOSURE COMPLETE AND GREEN (`27c1693` runtime+tests, `56772fe` deployment pin, `231b0a5` test-fixture reconciliation; HEAD `231b0a5`, pushed, tree clean): four proven control defects closed — per-attempt atomic regeneration, repair no-progress detection, fail-closed calibration continuation gate, cooperative deadline semantics; first full gate's 9 failures = stale constant-output fixtures (not validly proven pre-existing), reconciled without changing any expectation; complete suite now **1,849 passed / 32 skipped / 0 failed**; mypy strict Success (77 files); ruff 93 = 93 baseline (0 new); bundle content-identical (147 files / 934,495 bytes). Calibration evidence `exp-20260803-002741` (9 records / 0 succeeded / 8 failed / 1 timed_out / 81 calls / 118,211 tokens) preserved, not accepted scientific evidence; latest real calibration = 0/9; no Kaggle rerun; no tag; Pilot not authorized; next action = one selective calibration canary only; sentinel `POST_SMOKE_CALIBRATION_CLOSURE_AUDIT_REQUIRED`.** **SELECTIVE CALIBRATION CANARY EXECUTED (2026-08-04):** the dedicated selective calibration canary ran under source/build `50ec2c1` — `exp-20260804-133523` (`todo-smoke-001 / selective`) **failed `model_output`**: 4 calls / 5,804 tokens / 257.596 s / 3 selected / 2 preserved / **0 written**; Qwen defects in `todo/models.py` (`max_length=5` vs MEDIUM length 6) and duplicated `Priority(models.TextChoices)` in `todo/serializers.py` + `todo/views.py`; first repair byte-identical → `repair_no_progress`; atomic write 0 files; vs previous selective run 41.6% fewer tokens / 33.3% fewer calls / 22.4% faster but identical initial generation tokens (3,372) and output hashes → **harness safety controls verified, Qwen code quality unchanged**; incidental monolithic `exp-20260804-133016` diagnostic only; continuous cell blocked fail-closed (`CALIBRATION_REVIEW_REQUIRED`); accepted dedicated canary records = 1, successful = 0; full 9-record experiment NOT run; no merge/tag/Pilot/Kaggle authorized; no stable release claimed; record `selective_updates/records/SELECTIVE-CANARY-RESULTS-2026-08-04.md`; sentinel `SELECTIVE_CANARY_RESULT_AUDIT_REQUIRED`.**

---

## Executive Summary

**QWEN 14B SELECTIVE CANARY SUCCESS (2026-08-07) — ACCEPTED AND RECORDED.** The
independent GPT-5.6 Thinking audit accepted the first successful real Qwen
canary. Real engineering preflight PASS on 2×Tesla T4 (bnb-nf4, min free VRAM
8.417 GiB, GPU-only) and the dedicated selective canary
`exp-20260807-131819` succeeded (3 selected / 2 preserved / 3 regenerated,
3 model calls / 3,247 tokens / 295.944 s / 0 repairs, functional validation
PASS, scenario evaluator PASS 10/10, HF `recovery_uploaded`). Accepted real 14B
canary records = **1 succeeded / 0 failed** (isolated selective-only plan —
NOT `1/9`). **Full 9-record Scientific Smoke V2 = NOT RUN**; next action = one
fresh Full-9 run via `docs/KAGGLE_QWEN14B_FULL9_SCIENTIFIC_SMOKE_RUNBOOK.md`.
14B crossed the 7B quality floor (25.0% fewer calls / 44.1% fewer tokens /
repair eliminated / 14.9% slower) — functional viability, not strategy
superiority. Docs-only closure; no merge/tag/Pilot; no stable release claimed.

The historical Qwen 14B engineering track (2026-08-01 → 2026-08-06) that led to
this canary is summarized below.

R6 deployment closure is **accepted, frozen, and published**. Post-R6, two real
Kaggle Scientific Smoke V2 runs launched from the published deployment failed
completely before any model call (both 9 planned / 0 succeeded / 9 failed /
0 model calls / 0 tokens; first failure = workspace isolation). The real
runtime blockers were closed and pinned into a corrected bundle, and the R7A
hardening closed the four independently reproduced findings. A further real
attempt reached **81 model calls / 47,694 tokens but produced 0 succeeded /
0 regenerated files (0/9)** — **not scientific evidence**. The **R7B Smoke
Finish** makes the Qwen Smoke run observable and executable on branch
`fix/kaggle-smoke-v2-finish` (runtime commit `bff0a82`, bundle pin `17207bf`),
and the **R7C real-run root closure** (branch `fix/kaggle-smoke-v2-real-run-root`,
`7a80e53` + `f01b8f0`) closed the four root contracts the FP16/deps-drift
attempt `exp-20260801-123125` exposed (exact runtime pins, int8 default, frozen
scenario context, infrastructure-nonrepairable repair) plus a
`--kaggle-preflight-only` gate. The prior R7C report incorrectly called a
1,451-test subset the full suite; the true first full suite was **23 failed /
1,759 passed / 32 skipped** (root cause = blanket `baseline_validation =>
infrastructure_nonrepairable`). The independent GPT-5.6 Thinking correction
(`ffa179a` + `6d6aa36`) makes the exact 23 former failures pass and corrects
DRF import mapping, exact version verification, fail-fast preflight,
driver-level VRAM, CPU-offload rejection, the Python 3.12 runtime contract, and
stale source identity. An independent post-gate audit on `5e47a1e` then found
the project-local `ImportError` was still bypassing repair, the bundled
preflight could not import `benchmark` without ambient `PYTHONPATH`, and
preflight output was buffered; its exact correction (`6f88823` + `5797fc0`,
HEAD `5797fc0`, pushed) was imported via bundle fast-forward. The deterministic
interpreter closure (`aac9914` + `311e084`) then bound bare interpreter tokens
to the active runtime at the post-generation execution boundary. The
**pre-benchmark final source repin** (branch
`fix/kaggle-smoke-v2-model-output-closure`, HEAD `f8d00d7`, pushed) declared
the complete pre-benchmark dependencies (`769d84e` + `e5d9430`), recreated the
clean environment from declarations only (Python 3.11.9), and repeated the
complete clean gate. The previous `76a6b16` gate had **1 failure, not a green
full suite**: **1,833 passed / 32 skipped / 1 failed** — the sole failure was the
notebook-pin identity test, structural because the mandated `pyproject.toml`
declaration change broke byte-identity with the pinned `aac9914` SOURCE_COMMIT
(root cause = dependency declarations changing `pyproject.toml` after the
`aac9914`/`311e084` deployment pin; no runtime/prompt/metric/scenario/evaluator/
data change needed); frozen artifacts were not modified to force green and the
truthful total is recorded. The exact deployment-only correction `f8d00d7`
(bundle fast-forward, exactly one commit) re-pins the deployment to source
snapshot `e5d9430` (SOURCE_COMMIT=e5d943065c6f4158c30a1cbbba39436ab2a7a898,
DEPLOYED_BUILD_ID=e5d9430), and the complete clean suite is now **green:
1,834 passed / 32 skipped / 0 failed**. Local engineering: local scripted
records = 9/9, bundled CLI dry-run = 9/9, Dataset Validation 285/5 (data
unchanged), Prompt Validation 158, Pipeline Smoke 220/12, Integration PASS,
Metric Verification 169, mypy strict Success (77 files), ruff 93 = 93 baseline
(0 new), compileall clean, all notebook cells compile, bundle build
content-identical. Historical `exp-20260801-210443` produced one failed
model-output terminal record under source `6f88823` — preserved, excluded
from the current `e5d9430` aggregation; current accepted real records = **0/9**;
no scientific evidence exists; no tag; no Pilot; no Kaggle launch. **POST-SMOKE
CALIBRATION CLOSURE COMPLETE (`27c1693` + `56772fe` + `231b0a5`, HEAD
`231b0a5`):** four proven calibration control defects closed (per-attempt atomic
regeneration, repair no-progress detection, fail-closed calibration continuation
gate, cooperative deadline semantics); full suite 1,849 passed / 32 skipped / 0
failed; calibration evidence `exp-20260803-002741` = 0/9 (preserved, not
accepted scientific evidence); sentinel `POST_SMOKE_CALIBRATION_CLOSURE_AUDIT_REQUIRED`.
**FINAL SELECTIVE CANARY READINESS CLOSURE COMPLETE (`50ec2c1` + `28ecc5a` +
`356722b`, HEAD `356722b`, pushed, tree clean):** the independent GPT-5.6
Thinking audit at `f727b3e` REJECTED canary readiness (full suite was green) on
three independently reproduced blockers — (1) the cooperative deadline was not
checked before every generation call (direct repro: 3 calls and false success
after a 1s deadline), now every in-flight call beyond the deadline consumes its
tokens, makes no next call, writes none of the staged attempt, and returns the
failed scientific terminal `scientific_budget_exhausted` (same guard on every
Iterative Agent call); (2) atomic-abort `regenerated_artifact_count` was false
(0 writes but count 1), now all staged `generated` statuses become
`aborted`/`rejected` and count = 0 with hashes/evidence preserved; (3) the
generic one-run cell selects `monolithic`, not `selective` — a dedicated
Selective Calibration Canary cell was added (`--strategy selective --max-runs 1
--new-experiment`, isolated output `runs/selective_calibration_canary`, NO
`--auto-resume-hf`, `AUTHORIZE_CONTINUOUS_AFTER_CALIBRATION_REVIEW = False`)
whose `_verify_selective_canary()` asserts exactly one current-source
`todo-smoke-001 / selective` record, model identity `qwen:1:int8`, model calls >
0, terminal scientific outcome, HF `recovery_uploaded`, checkpoint 3 planned / 1
completed / 2 pending. Deployment pinned: `SOURCE_COMMIT =
50ec2c1ca43c230aed4538be32ca7dab2ccc22e5`, `DEPLOYED_BUILD_ID = 50ec2c1`. Full
suite = **1,856 passed / 32 skipped / 0 failed**; grouped per-category 629
passed / 1 skipped; scripted dry run 9/9 exit 0 (fresh dir); mypy strict Success
(77 files); ruff 0 new; compileall clean; notebooks compile (8/8 bundle code
cells incl. canary cell); bundle content-identical (147 files / 948,250 bytes);
no stable release claimed; sentinel `FINAL_SELECTIVE_CANARY_READINESS_AUDIT_REQUIRED`.**
**QWEN 14B BNB-NF4 CANARY PREPARATION COMPLETE (2026-08-05) (Commit A `0ece665` `fix(model): add model-aware Qwen BNB quantization profiles` + Commit B `0a596b8` `chore(deploy): pin Qwen 14B NF4 selective-canary bundle`, HEAD `0a596b8`, pushed, local = remote, tree clean):** the frozen model-blind `qwen:1:int8` identity is replaced by the deterministic model-aware identity `qwen:<checkpoint-basename>:<quantization>:cfg-<12hex>` computed before auto-resume from `config.json` fields (model_type, hidden_size, num_hidden_layers, num_attention_heads) + requested mode + checkpoint quantization method — 7B bnb-int8 / 14B bnb-int8 / 14B bnb-nf4 always differ, so the generic auto-resume cell can no longer download the wrong experiment (contamination: it previously fetched `exp-20260804-133016` because both 7B and attempted 14B were `qwen:1:int8`); canonical modes `bnb-int8` / `bnb-nf4` / `fp16` via `--qwen-quantization` (default `bnb-int8`, unknown values exit 2); NF4 = `load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True` (Tesla T4); a prequantized non-bitsandbytes checkpoint fails fast `PREQUANTIZED_CHECKPOINT_INCOMPATIBLE` before tokenizer/model load with no fallback (the failed 14B GPTQ attempt `exp-20260804-195126` = 0 records / 0 calls / 0 tokens, preflight failed before probe, preserved as engineering evidence; GPTQ support deferred); notebook pinned to the unquantized `14b-instruct/1` base checkpoint (never `14b-instruct-gptq-int4`), `QWEN_QUANTIZATION = "bnb-nf4"`, `RUN_GENERIC_ONE_RUN = False`, isolated `runs/qwen14b_bnb_nf4_selective_canary`, fail-closed canary preflight gate, `--strategy selective --max-runs 1 --new-experiment`, no `--auto-resume-hf`, `SOURCE_COMMIT = 0ece665ef25e1b0ca3aa14f5f25977cadbd06d0c` / `DEPLOYED_BUILD_ID = 0ece665`. Full suite **1,877 passed / 32 skipped / 0 failed**; Dataset PASS (27 scenario files / 27 unique IDs / 0 duplicates, zero dataset changes in closure); Prompt 380; Pipeline Smoke 189; Scripted dry run 9/9 exit 0; Metric Verification 169; ruff 0 new (21 pre-existing); mypy 0 new (5 pre-existing); compileall clean; notebooks compile 8/8 + 8/8; bundle content-identical (147 files / 962,188 bytes), manifests verified, no cache files; no stable release claimed; record `QWEN14B-BNB-NF4-CANARY-READINESS.md`; sentinel `QWEN14B_NF4_CANARY_READINESS_AUDIT_REQUIRED`.**

**QWEN 14B FINAL PREFLIGHT CLOSURE COMPLETE (2026-08-05) (Commit A `0aa705d` `fix(model): close Qwen 14B Kaggle preflight blockers` + Commit B `cc7846b` `chore(deploy): repin final Qwen 14B preflight bundle`, HEAD `cc7846b`, pushed, local = remote, tree clean):** the three preflight blockers the independent audit reproduced on the `5ef6438` state are closed. (1) The canary used `SELECTIVE_CANARY_OUTPUT_DIR` before assignment — definition moved to the `setup-cell` after `OUTPUT_DIR`, duplicate assignment removed from the selective-calibration-canary cell. (2) The preflight incorrectly required exactly one visible GPU — `EXPECTED_VISIBLE_GPU_COUNTS = (1, 2)`, so real 2×Tesla T4 environments pass (`FAIL (N; expected 1 or 2)` otherwise). (3) The Kaggle numeric version directory produced a `qwen:1:*` readable identity — `_checkpoint_identity_slug` maps e.g. `/kaggle/input/models/qwen-lm/qwen2.5-coder/transformers/14b-instruct/1` → `14b-instruct-v1` → `qwen:14b-instruct-v1:bnb-nf4:cfg-<12hex>` in `compute_model_identity` and `checkpoint_basename`. Official gate = declared clean environment (Python 3.11.9 / pytest 8.4.2): full suite **1,890 passed / 32 skipped / 0 failed**; Dataset 285/5; Prompt 174; Pipeline Smoke 223/12; Dry Run 9/9 (exit 0, dashboard + evidence files present); Metric Verification 169; Ruff 0 new (91 pre-existing baseline in untouched files); mypy strict Success (77 files); compileall clean; notebook 8/8 + 8/8 compile; builder content-identical (147 files / 963,067 bytes); regression proofs **2-GPU otherwise-valid preflight = PASS** and **canary setup reaches subprocess construction without NameError**. Ambient pytest 9.1.1 is diagnostic only, never the gate. No Kaggle run / canary / continuous / merge / tag / Pilot; no model, quantization, prompt, data, scenario, evaluator, or metric change; no GPTQ/AWQ/GGUF/vLLM; **no real 14B result and no stable release claimed**; accepted real records = 0/9. Next action after independent audit = **Kaggle engineering preflight cell only**. Sentinel `QWEN14B_FINAL_PREFLIGHT_CLOSURE_AUDIT_REQUIRED`.**

**Legacy note:** Legacy Seven-Arm V1 results (including the `v0.7.0-smoke-passed` tag and the 7/7-arm Kaggle orchestration smoke) are **historical** and superseded. They are not V2 evidence. The current experiment is the Three-Arm Scientific Smoke V2 (`scientific-smoke-v2` profile): 3 frozen scenarios (todo-smoke-001/002/003) × 3 arms (monolithic, selective, iterative_repository_agent) × 1 repetition = 9 runs. Smoke evidence is non-publication.

**QWEN 14B NF4 TRANSFORMERS V4 LOADER CLOSURE COMPLETE (2026-08-05) (Commit A `41e9ad7` `fix(model): pin transformers==4.57.6 BNB loader and preserve static preflight metadata` + Commit B `920ab9b` `chore(deploy): repin Qwen 14B NF4 v4 loader closure bundle`, HEAD `920ab9b`, pushed, local = remote, tree clean):** the independent OOM audit reproduced the real preflight OOM at `9fd4eee` (full suite was green): transformers was unpinned, Kaggle image drift installed **5.0.0**, and its loader materialized the **14B BF16 weights on GPU before BNB-NF4 quantization** — OOM after 232.412 s at ~75% of 579 checkpoint params (tried 136 MiB; GPU 1 free 46.81 MiB; allocated 14.38 GiB; runtime Python 3.12.13 / transformers 5.0.0 / bitsandbytes 0.49.2 / accelerate 1.14.0 / torch 2.10.0+cu128). Fixes: (A) `requirements-smoke-kaggle.lock` + `requirements-kaggle.txt` pin `transformers==4.57.6` (torch stays unpinned — Kaggle torch preserved); (B) preflight `_REQUIRED_IMPORTS` requires the exact `"4.57.6"` — `dependency_import_verification` FAILs on any other version before staging/model load; (C) notebook `install-lock-cell` `EXPECTED_RUNTIME` gains transformers 4.57.6 with the fail-closed mismatch check; (D) `kaggle_qwen_backend._load_model` passes `low_cpu_mem_usage=True` for `bnb-int8`/`bnb-nf4` so the 4.57.x loader streams/quantizes in place instead of materializing the full-precision temporary copy; (E) preflight `_static_model_metadata` preserves `model_identity` / `checkpoint_basename` / `checkpoint_quantization_method` / `gpu_count` / `gpu_name` (from `config.json` + CUDA discovery, no weight load) when the load OOMs/fails. Gate = ambient Python 3.11.5 / pytest 9.1.1 (declared clean env `_workspace\cache\prebenchmark-py311` NOT present locally — independent audit should recreate it): full suite **1,898 passed / 32 skipped / 0 failed**; Ruff 0 new (86 pre-existing baseline in untouched files); mypy strict Success (77 files); compileall clean; notebook cells compile canonical + bundled; bundle pin identity PASS (`SOURCE_COMMIT=41e9ad7`); bundle integration 32 passed; builder content-identical (147 files / 964,859 bytes). Regression proofs: **preflight FAILs on transformers≠4.57.6 (incl. 5.0.0 / NOT_INSTALLED) before load**, **BNB int8+NF4 loads pass `low_cpu_mem_usage=True` (fp16 does not)**, **static model/GPU metadata preserved on failed probe**. No Kaggle run / canary / continuous / merge / tag / Pilot; no model, quantization, prompt, data, scenario, evaluator, or metric change; no GPTQ/AWQ/GGUF/vLLM (no new backend); **no real 14B result and no stable release claimed**; accepted real records = 0/9. Next action after independent audit = **Kaggle engineering preflight cell only**. Sentinel `QWEN14B_V4_LOADER_CLOSURE_AUDIT_REQUIRED`.**

**QWEN 14B MULTI-GPU VRAM PREFLIGHT CLOSURE COMPLETE (2026-08-06) (Commit A `f7b1ebb` `fix(model): enforce multi-GPU VRAM headroom per visible GPU` + Commit B `c8f5685` `chore(deploy): repin multi-GPU VRAM preflight bundle`, HEAD `c8f5685`, pushed, local = remote, tree clean):** the independent audit (`QWEN14B_MULTI_GPU_VRAM_PREFLIGHT_INDEPENDENT_AUDIT_2026-08-06.md`) found the preflight on the `897e323` state (full suite was green) read VRAM from **GPU 0 only** — `_qwen_probe_metrics` used `torch.cuda.memory_allocated(0)` / `memory_reserved(0)` / `mem_get_info(0)` / `synchronize(0)` and `vram_headroom` checked only that single free value, so a 2x Tesla T4 `device_map="auto"` 14B bnb-nf4 load could pass while GPU 1 had <2.0 GiB free. Fixes: (A) immutable `GpuVramSnapshot` (`device_index` / `gpu_name` / `allocated_gib` / `reserved_gib` / `free_gib` / `total_gib`); (B) `_collect_gpu_vram_snapshots()` synchronizes and reads allocated/reserved/free/total on **every** visible GPU (three-decimal rounding, never swallows a per-GPU failure, `()` when CUDA unavailable, no tensor allocation); (C) probe metrics — `free_vram_after_probe_gib = min(snapshot.free_gib)` with summed allocated/reserved scalars, `gpu_vram_by_device` persisted, preflight FAILs when `gpu_count > 0` but no snapshots; (D) minimum-free gate on **every** visible GPU (`vram_headroom: PASS (minimum free across 2 GPU(s)=X.XX GiB)` / `FAIL (GPU 1 free=0.12 GiB < 2.0 GiB)`, failing devices listed by index, never averaged/summed); (E) `_static_model_metadata` preserves per-GPU snapshots on failed model loads (CUDA still queryable); (F) `KaggleSmokePreflightResult.gpu_vram_by_device` + ordered per-GPU objects in `kaggle_smoke_preflight.v1` JSON + one human line per GPU, no existing JSON field removed. Official clean-env gate (`_workspace\cache\prebenchmark-py311-v4-loader`, Python 3.11.5 / **pytest 8.4.2 exactly**): full suite **1,915 passed / 32 skipped / 0 failed** (500.22 s; +17 net new tests); Metric Verification 169; Ruff 0 new (86 pre-existing baseline in untouched files); mypy strict Success (77 files); compileall clean; notebook cells compile canonical + bundled; bundle pin identity PASS (`SOURCE_COMMIT=f7b1ebb`); bundle integration 32 passed; builder content-identical (147 files / 968,722 bytes). Regression proofs: **1-GPU >= 2 GiB PASS**, **2-GPU both >= 2 GiB PASS**, **asymmetric GPU0 3.0 GiB / GPU1 0.125 GiB → FAIL (the audit reproduction)**, **both-low → FAIL listing devices 0 then 1**, **failed load preserves per-GPU snapshots**. No Kaggle run / preflight on Kaggle / canary / continuous / merge / tag / Pilot; no model, quantization, prompt, data, scenario, evaluator, or metric change; no GPTQ/AWQ/GGUF/vLLM (no new backend, no CPU/disk offload, no max_memory tuning); **no real 14B result and no stable release claimed**; accepted real records = 0/9. Next action after independent audit = **Kaggle engineering preflight cell only**. Sentinel `QWEN14B_MULTI_GPU_VRAM_CLOSURE_AUDIT_REQUIRED`. Record: `selective_updates/records/QWEN14B-MULTI-GPU-VRAM-PREFLIGHT-CLOSURE.md`.

**QWEN 14B NF4 V4 LOADER OFFICIAL GATE COMPLETE (2026-08-05) (docs/deploy commit `docs(deploy): finalize Qwen 14B NF4 loader gate truth`, HEAD pushed, local = remote, tree clean):** the missing official clean-environment gate for the loader closure is now run, and one stale Notebook markdown statement was corrected (docs/deploy only — no runtime code, tests, requirements, data, prompts, scenarios, strategies, evaluator logic, metrics, model settings, or runtime limits changed). The markdown cell immediately before `preflight-cell` in `notebooks/seven_arm_benchmark.ipynb` described the load as **int8** (`load_in_8bit=True` + `device_map="auto"` with `expandable_segments`) — stale; it now truthfully reads **Qwen 14B BNB-NF4 load** — `Qwen2.5-Coder-14B-Instruct` base checkpoint via BitsAndBytes NF4 (`load_in_4bit=True`, `bnb_4bit_quant_type="nf4"`, `bnb_4bit_compute_dtype=float16`, `bnb_4bit_use_double_quant=True`, `device_map="auto"`, Transformers 4.57.6). No executable code cell, `SOURCE_COMMIT`/`DEPLOYED_BUILD_ID` (`41e9ad7`), command, quantization setting, model path, timeout, token limit, or auth flag changed; bundle regenerated twice via `scripts/build_upload_bundle.py` — second run content-identical (147 files / 965,015 bytes; tree hash 26EA934F16A25C14788484CE1A75EFF4FB453E6C346F5FDCEE72D3004EC5B7D1), manifests verified, no cache files. **Official gate = fresh disposable env created from project declarations only (`_workspace\cache\prebenchmark-py311-v4-loader`, Python 3.11.5 / pytest 8.4.2 exactly; Django 5.2.16, DRF 3.17.1, pytest-django 4.12.0, pytest-asyncio 1.2.0, ruff 0.15.22, mypy 1.20.2):** full suite **1,898 passed / 32 skipped / 0 failed** (517.97 s); Dataset 281/4; Prompt 126/4; Pipeline Smoke 177; Scripted dry run `--profile scientific-smoke-v2` 9 planned / 9 terminal / 9 succeeded / 0 failed / exit 0; Metric Verification 169; Ruff 0 new (91 pre-existing baseline in untouched files); mypy strict Success (77 files); compileall clean; notebook code cells compile canonical + bundled; `git diff --check` clean. No Kaggle run / preflight / canary / continuous / merge / tag / Pilot; **no real 14B result and no stable release claimed**; accepted real records = 0/9. Next action after independent audit = **Kaggle engineering preflight cell only**. Sentinel `QWEN14B_V4_LOADER_OFFICIAL_GATE_AUDIT_REQUIRED`.**

---

## Current Post-R6 Health

### Test result

| Metric | Value |
|---|---|
| **Real 14B selective canary (2026-08-07)** | **SUCCEEDED** — `exp-20260807-131819` (`todo-smoke-001 / selective`, source/build `f7b1ebb`): 3 selected / 2 preserved / 3 regenerated; migration `0004_task_priority.py`; 3 model calls / 2,527 prompt + 720 completion = 3,247 tokens / 295.944 s / 0 repairs; functional validation PASS; scenario evaluator PASS 10/10; HF `recovery_uploaded`; accepted by independent GPT-5.6 Thinking audit |
| **Real engineering preflight (2026-08-07)** | **PASS** — 2×Tesla T4 (Python 3.12.13 / transformers 4.57.6 / bnb-nf4); identity `qwen:14b-instruct-v1:bnb-nf4:cfg-cc9474140d25`; footprint 9,721,981,184 bytes; preflight 174.016 s; probe 68+17 tokens; min free VRAM 8.417 GiB; GPU-only device map |
| Full suite (Qwen 14B multi-GPU VRAM preflight closure) | **1,915 passed / 32 skipped / 0 failed** — GREEN (official clean-env gate `_workspace\cache\prebenchmark-py311-v4-loader`, Python 3.11.5 / pytest 8.4.2 exactly, 500.22 s; +17 net new tests) |
| Full suite (Qwen 14B NF4 v4 loader official gate) | **1,898 passed / 32 skipped / 0 failed** — GREEN (official clean-env gate, fresh disposable env from declarations only, Python 3.11.5 / pytest 8.4.2 exactly, 517.97 s) |
| Full suite (Qwen 14B final preflight closure) | **1,890 passed / 32 skipped / 0 failed** — GREEN (official clean-env gate, pytest 8.4.2) |
| Full suite (Qwen 14B BNB-NF4 canary preparation closure) | **1,877 passed / 32 skipped / 0 failed** — GREEN |
| Full suite (final selective canary readiness closure) | **1,856 passed / 32 skipped / 0 failed** — GREEN |
| Grouped per-category (same closure) | 629 passed / 1 skipped |
| Dataset Validation | 285 passed / 5 skipped (27 scenario files / 27 unique IDs / 0 duplicates; zero closure dataset changes) |
| Prompt Validation | 174 passed |
| Pipeline Smoke | 223 passed / 12 skipped |
| Dry Run | scientific-smoke-v2 9/9 succeeded (exit 0; fresh runs dir) |
| Integration | PASS |
| Metric Verification | 169 passed |
| Regression proof | 2-GPU otherwise-valid preflight = PASS; canary reaches subprocess construction without NameError |
| Regression proof (multi-GPU VRAM) | 1-GPU >= 2 GiB PASS; 2-GPU both >= 2 GiB PASS; asymmetric GPU0 3.0 GiB / GPU1 0.125 GiB = FAIL; both-low = FAIL listing devices 0 then 1; failed load preserves per-GPU snapshots |
| Bundled CLI nine-cell dry-run regression | passed |
| Builder build | content-identical (147 files / 968,722 bytes); manifests verified; no cache files |

### Deployment bundle

| Category | Files | Bytes |
|---|---:|---:|
| code | 90 | — |
| data | 56 | — |
| notebooks | 1 | — |
| **total** | **147** | **968,722** |

### Integrity and content

```text
Builder                  = scripts/build_upload_bundle.py only (build verified, content-identical)
Runtime source           = f7b1ebb (fix(model): enforce multi-GPU VRAM headroom per visible GPU)
Deployment pin           = c8f5685 (chore(deploy): repin multi-GPU VRAM preflight bundle)
Deployment source        = f7b1ebb (SOURCE_COMMIT=f7b1ebb, DEPLOYED_BUILD_ID=f7b1ebb)
Notebook source identity = SOURCE_COMMIT=f7b1ebb, DEPLOYED_BUILD_ID=f7b1ebb
Qwen quantization        = bnb-nf4 (--qwen-quantization default bnb-int8; canonical modes bnb-int8/bnb-nf4/fp16)
Model identity           = qwen:<checkpoint-basename>:<quantization>:cfg-<12hex> (replaces frozen qwen:1:int8)
Canary output            = runs/qwen14b_bnb_nf4_selective_canary (isolated, RUN_GENERIC_ONE_RUN=False, no --auto-resume-hf)
Canary evidence          = exp-20260807-131819 succeeded (3/2/3, migration 0004, 3 calls, 3,247 tokens, 0 repairs, 295.944 s, evaluator 10/10, HF recovery_uploaded)
Full-9 runbook           = docs/KAGGLE_QWEN14B_FULL9_SCIENTIFIC_SMOKE_RUNBOOK.md (frozen, 3 scenarios x 3 strategies x 1 rep = 9 records)
HF results repo          = NabilDo/selective-regeneration-experiment-results
Preflight over bundle    = PASS (real Kaggle preflight 2026-08-07, min free VRAM 8.417 GiB, GPU-only)
```

### Static and type gates

```text
Ruff            = 0 new findings (21 pre-existing baseline)
Mypy --strict   = 0 new findings (5 pre-existing, identical to self-contained HEAD baseline)
Compileall      = clean (exit 0)
Notebook cells  = all compile (8/8 canonical + 8/8 bundled code cells)
git diff --check = clean
git status --short = clean
Benchmark data  = unchanged
```

---

## Phases and milestones

| Phase | Status |
|---|---|
| Phase 0 — Bootstrap and Environment | Complete |
| Phase 1 — Input Audit | Complete |
| Phase 2B — Research Protocol Freeze | Complete (v1.0 frozen) |
| Phase 3 — Repository and Scenario Preparation | Complete |
| Phase 4A–4F, 4F.1 — Benchmark core | Complete |
| R3B / R3C / R3D closures | Complete |
| R4 — token/metric contract | ACCEPTED AND FROZEN (`f5ae826`) |
| R5 — nine scripted production records | ACCEPTED AND FROZEN (`7761c48`) |
| R6 — deployment closure | ACCEPTED AND FROZEN (`949e9c2`; freeze commit `4b2dd27`) |
| R6 milestone-branch publication | PUBLISHED (upstream set, local/remote equal) |
| Kaggle attempts (2) | FAILED pre-model — preserved (`exp-20260801-024041`, `exp-20260801-024624`) |
| Kaggle runtime fix | COMMITTED AND PINNED (`de3163f`, `fb60972`) — core accepted by independent audit |
| R7A pre-rerun hardening | COMPLETE (`d50e89e` + `4c73db6`) — four audit findings closed |
| R7B Smoke Finish | COMPLETE (`bff0a82` + `17207bf`) — observable Qwen Smoke |
| R7C real-run root closure | COMPLETE (`7a80e53` + `f01b8f0`) + correction imported (`ffa179a` + `6d6aa36`) + post-gate correction imported (`6f88823` + `5797fc0`, HEAD `5797fc0`) — final full-gate audit required |
| Deterministic interpreter closure | COMPLETE (`aac9914` + `311e084`) — bare interpreter tokens bound to active runtime |
| Pre-benchmark reproducibility closure | COMPLETE AND GREEN (`769d84e` + `e5d9430` declarations; deployment-only correction `f8d00d7`, HEAD `f8d00d7`, pushed) — previous 76a6b16 gate 1,833 passed / 32 skipped / 1 failed (structural notebook-pin identity test, truthful, not forced green); complete clean suite now 1,834 passed / 32 skipped / 0 failed |
| Post-smoke calibration closure | COMPLETE (`27c1693` + `56772fe` + `231b0a5`, HEAD `231b0a5`) — four control defects closed; suite 1,849 passed / 32 skipped / 0 failed; calibration exp-20260803-002741 preserved 0/9 |
| Final selective canary readiness closure | COMPLETE (`50ec2c1` + `28ecc5a` + `356722b`, HEAD `356722b`, pushed) — audit at f727b3e REJECTED canary readiness; three blockers closed (per-call deadline, atomic metric truth, dedicated selective canary cell); suite 1,856 passed / 32 skipped / 0 failed; no stable release claimed; sentinel FINAL_SELECTIVE_CANARY_READINESS_AUDIT_REQUIRED |
| Selective calibration canary | EXECUTED (2026-08-04) — `exp-20260804-133523` (`todo-smoke-001 / selective`, source/build `50ec2c1`) failed `model_output`: 4 calls / 5,804 tokens / 257.596 s / 3 selected / 2 preserved / 0 written; `repair_no_progress` after byte-identical first repair; harness controls verified, Qwen code quality unchanged; incidental monolithic `exp-20260804-133016` diagnostic only; full 9-record experiment NOT run; no stable release claimed |
| Qwen 14B BNB-NF4 canary preparation | COMPLETE (2026-08-05) — Commit A `0ece665` + Commit B `0a596b8`, HEAD `0a596b8`, pushed, local = remote, tree clean; model-aware identity `qwen:<basename>:<mode>:cfg-<12hex>` replaces `qwen:1:int8`; bnb-nf4 profile; prequantized fail-fast; notebook pinned to unquantized 14b-instruct/1 with fail-closed canary gate; suite 1,877 passed / 32 skipped / 0 failed; next action = Kaggle engineering preflight only; no stable release claimed; sentinel QWEN14B_NF4_CANARY_READINESS_AUDIT_REQUIRED |
| Qwen 14B final preflight closure | COMPLETE (2026-08-05) — Commit A `0aa705d` + Commit B `cc7846b`, HEAD `cc7846b`, pushed, local = remote, tree clean; three independently reproduced preflight blockers closed (canary output dir used before assignment; preflight required exactly one visible GPU; numeric version dir produced `qwen:1:*` identity); official clean-env gate 1,890 passed / 32 skipped / 0 failed (pytest 8.4.2); regression proofs: 2-GPU preflight PASS + canary reaches subprocess construction without NameError; next action = Kaggle engineering preflight cell only after independent audit; no stable release claimed; sentinel QWEN14B_FINAL_PREFLIGHT_CLOSURE_AUDIT_REQUIRED |
| Qwen 14B NF4 transformers v4 loader closure | COMPLETE (2026-08-05) — Commit A `41e9ad7` + Commit B `920ab9b`, HEAD `920ab9b`, pushed, local = remote, tree clean; transformers pinned `4.57.6` (lock + requirements-kaggle.txt + notebook EXPECTED_RUNTIME + preflight `_REQUIRED_IMPORTS` fail-closed); BNB int8+NF4 loads pass `low_cpu_mem_usage=True`; `_static_model_metadata` preserves identity/gpu metadata on failed load; full suite 1,898 passed / 32 skipped / 0 failed (official clean-env gate, 2026-08-05 — see next row); regression proofs: preflight FAILs on transformers 5.0.0/absent before load, BNB loads pass low_cpu_mem_usage (fp16 does not), metadata preserved on failed probe; no stable release claimed; sentinel QWEN14B_V4_LOADER_CLOSURE_AUDIT_REQUIRED |
| Qwen 14B NF4 v4 loader official gate | COMPLETE (2026-08-05) — docs/deploy commit `docs(deploy): finalize Qwen 14B NF4 loader gate truth`, pushed, local = remote, tree clean; one stale int8 Notebook markdown cell corrected to truthful BNB-NF4 wording (docs-only; no executable cell / SOURCE_COMMIT `41e9ad7` / command / quantization / model path / timeout / token limit / auth changed); official gate = fresh disposable env from declarations only (Python 3.11.5 / pytest 8.4.2 exactly): full suite 1,898 passed / 32 skipped / 0 failed (517.97 s); Dataset 281/4; Prompt 126/4; Pipeline Smoke 177; Dry Run 9/9/9/0 exit 0; Metric 169; Ruff 0 new (91 baseline); mypy strict Success (77); compileall clean; bundle content-identical double rebuild (147 files / 965,015 bytes); git diff --check clean; next action = independent audit then Kaggle engineering preflight cell only; no stable release claimed; sentinel QWEN14B_V4_LOADER_OFFICIAL_GATE_AUDIT_REQUIRED |
| Qwen 14B multi-GPU VRAM preflight closure | COMPLETE (2026-08-06) — Commit A `f7b1ebb` + Commit B `c8f5685`, HEAD `c8f5685`, pushed, local = remote, tree clean; independent audit found preflight read VRAM from GPU 0 only; closed with `GpuVramSnapshot` + `_collect_gpu_vram_snapshots()` (synchronize + read every visible GPU, three-decimal rounding, never swallow a per-GPU failure), `free_vram_after_probe_gib = min(...)`, minimum-free gate on every visible GPU (>= 2.0 GiB), ordered per-GPU JSON (`gpu_vram_by_device`) + per-GPU human table lines, per-GPU snapshot preservation on failed loads via `_static_model_metadata`; official clean-env gate 1,915 passed / 32 skipped / 0 failed (500.22 s; pytest 8.4.2); Metric 169; Ruff 0 new (86 baseline); mypy strict Success (77); bundle content-identical (147 files / 968,722 bytes); regression proofs: 1-GPU PASS, 2-GPU both-healthy PASS, asymmetric GPU0 3.0 / GPU1 0.125 = FAIL (audit reproduction), both-low = FAIL listing 0 then 1, failed load preserves snapshots; next action = independent audit then Kaggle engineering preflight cell only; no stable release claimed; sentinel QWEN14B_MULTI_GPU_VRAM_CLOSURE_AUDIT_REQUIRED |
| Qwen 14B SELECTIVE CANARY SUCCESS | ACCEPTED AND RECORDED (2026-08-07) — real engineering preflight PASS (2×Tesla T4, bnb-nf4, identity `qwen:14b-instruct-v1:bnb-nf4:cfg-cc9474140d25`, min free VRAM 8.417 GiB, GPU-only); canary `exp-20260807-131819` (`todo-smoke-001 / selective`, source/build `f7b1ebb`) SUCCEEDED — 3 selected / 2 preserved / 3 regenerated, migration `0004_task_priority.py`, 3 calls / 3,247 tokens / 295.944 s / 0 repairs; functional validation PASS; evaluator PASS 10/10; HF `recovery_uploaded`; accepted real 14B canary records = 1 succeeded / 0 failed (isolated selective-only plan, NOT 1/9); full 9-record Scientific Smoke V2 = NOT RUN; next = one fresh Full-9 via runbook; no merge/tag/Pilot; docs-only closure; record QWEN14B-SELECTIVE-CANARY-SUCCESS-2026-08-07.md; sentinel QWEN14B_CANARY_SUCCESS_DOCUMENTED_FULL9_READY |
| Pilot | Not authorized |
| Research experiment | Planned |

---

## Known evidence boundary

```text
Local scripted production proof = 9/9
Generated bundle dry-run plan   = 9/9
Kaggle attempts                 = 2 failed pre-model (preserved, 0 model calls)
Latest real attempt             = exp-20260801-123125 (FP16 → OOM; deps drifted)
Historical experiment           = exp-20260801-210443 (ONE failed model-output terminal record
                                  under 6f88823 — preserved, excluded from current e5d9430 aggregation)
Selective calibration canary     = exp-20260804-133523 (dedicated, todo-smoke-001 / selective,
                                  source/build 50ec2c1, FAILED model_output, 0 files written — preserved)
Incidental monolithic run        = exp-20260804-133016 (diagnostic evidence only, NOT an accepted comparison)
14B GPTQ attempt                 = exp-20260804-195126 (0 records / 0 calls / 0 tokens, preflight failed before
                                  probe — GPTQConfig vs BitsAndBytesConfig conflict, preserved, GPTQ deferred)
QWEN 14B real preflight          = PASS (2026-08-07, 2x Tesla T4, bnb-nf4, min free VRAM 8.417 GiB, GPU-only)
QWEN 14B selective canary        = exp-20260807-131819 SUCCEEDED (todo-smoke-001 / selective, source/build f7b1ebb,
                                  3 selected / 2 preserved / 3 regenerated, migration 0004, 3 calls / 3,247 tokens /
                                  0 repairs / 295.944 s, functional validation PASS, evaluator 10/10, HF recovery_uploaded)
Accepted real 14B canary records = 1 succeeded / 0 failed (isolated selective-only plan — NOT 1/9)
Full 9-record Scientific Smoke V2 = NOT RUN
Real Qwen records (Full-9)       = 0/9 (not run)
Scientific evidence              = canary viability proven; FULL-9 NOT RUN — no efficiency claim yet
Real token/call/time comparison  = canary vs 7B only (25.0% fewer calls / 44.1% fewer tokens / repair eliminated / 14.9% slower)
Publication evidence             = unavailable
Pilot evidence                   = unavailable
```

No full-9 scientific claim is authorized before the real Full-9 result audit. The accepted canary proves functional viability of the 14B bnb-nf4 stack only. Smoke evidence is non-publication.

---
## Near goal

One fresh **Full-9 Scientific Smoke V2** run (3 scenarios × 3 strategies × 1 rep = 9 records) using the frozen runbook `docs/KAGGLE_QWEN14B_FULL9_SCIENTIFIC_SMOKE_RUNBOOK.md` — one engineering preflight + one benchmark process, fresh isolated experiment, never resume/merge the canary, then independent results audit. NOT a merge/tag/Pilot, NOT a fine-tune.

## Far goal

Independent real-result audit → stable `v2.0.0-scientific-smoke` tag → freeze
Pilot matrix → Pilot execution → research experiment → statistical analysis →
paper evidence package.

## Next action

Execute the frozen Full-9 runbook (`docs/KAGGLE_QWEN14B_FULL9_SCIENTIFIC_SMOKE_RUNBOOK.md`) for the Qwen 14B bnb-nf4 profile (identity `qwen:14b-instruct-v1:bnb-nf4:cfg-cc9474140d25`): fresh isolated Full-9 experiment, preflight-cell exactly once, then independent results audit. Do not merge/tag/Pilot/fine-tune or resume/merge the canary before the independent result audit.

QWEN14B_CANARY_SUCCESS_DOCUMENTED_FULL9_READY