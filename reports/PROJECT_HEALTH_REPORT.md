# Project Health Report

**Report Date:** 2026-08-05
**Project:** Dependency-Aware Selective Regeneration Benchmark
**Branch:** `fix/kaggle-smoke-v2-model-output-closure` (HEAD `0a596b8`, pushed; Qwen 14B BNB-NF4 canary preparation closure ingested docs-only)
**R4/R5/R6 status:** R4 ACCEPTED AND FROZEN (`f5ae826`); R5 ACCEPTED AND FROZEN (`7761c48`); R6 ACCEPTED AND FROZEN (`949e9c2`) by the final independent re-audit (GPT-5.6 Thinking, 2026-08-01); milestone branch **published** to origin (freeze commit `4b2dd27` = first publication HEAD, local/remote equality verified).
**Post-R6:** two real Kaggle attempts failed pre-model (`exp-20260801-024041`, `exp-20260801-024624`; both 0 model calls); real runtime blockers closed and pinned — fix `de3163f`, bundle pin `fb60972` (core accepted by the independent runtime-fix audit); R7A hardening closed all four audit findings (source `d50e89e`, bundle `4c73db6`); a later real attempt reached 81 model calls / 47,694 tokens with 0 succeeded / 0 regenerated files; the attempt `exp-20260801-123125` failed at runtime root (FP16 OOM + dependency drift). **R7B Smoke Finish complete (`bff0a82` + `17207bf`); R7C real-run root closure complete (`7a80e53` + `f01b8f0`) + correction imported (`ffa179a` + `6d6aa36`) + post-gate correction imported (`6f88823` + `5797fc0`, HEAD `5797fc0`, pushed); deterministic interpreter closure complete (`aac9914` + `311e084`); PRE-BENCHMARK FINAL SOURCE REPIN COMPLETE AND GREEN (`769d84e` + `e5d9430` declarations, deployment-only correction `f8d00d7`, HEAD `f8d00d7`, pushed) — previous `76a6b16` gate = 1,833 passed / 32 skipped / 1 failed (structural notebook-pin identity test, truthful, not forced green); complete clean suite then 1,834 passed / 32 skipped / 0 failed. POST-SMOKE CALIBRATION CLOSURE COMPLETE AND GREEN (`27c1693` runtime+tests, `56772fe` deployment pin, `231b0a5` test-fixture reconciliation; HEAD `231b0a5`, pushed, tree clean): four proven control defects closed — per-attempt atomic regeneration, repair no-progress detection, fail-closed calibration continuation gate, cooperative deadline semantics; first full gate's 9 failures = stale constant-output fixtures (not validly proven pre-existing), reconciled without changing any expectation; complete suite now **1,849 passed / 32 skipped / 0 failed**; mypy strict Success (77 files); ruff 93 = 93 baseline (0 new); bundle content-identical (147 files / 934,495 bytes). Calibration evidence `exp-20260803-002741` (9 records / 0 succeeded / 8 failed / 1 timed_out / 81 calls / 118,211 tokens) preserved, not accepted scientific evidence; latest real calibration = 0/9; no Kaggle rerun; no tag; Pilot not authorized; next action = one selective calibration canary only; sentinel `POST_SMOKE_CALIBRATION_CLOSURE_AUDIT_REQUIRED`.** **SELECTIVE CALIBRATION CANARY EXECUTED (2026-08-04):** the dedicated selective calibration canary ran under source/build `50ec2c1` — `exp-20260804-133523` (`todo-smoke-001 / selective`) **failed `model_output`**: 4 calls / 5,804 tokens / 257.596 s / 3 selected / 2 preserved / **0 written**; Qwen defects in `todo/models.py` (`max_length=5` vs MEDIUM length 6) and duplicated `Priority(models.TextChoices)` in `todo/serializers.py` + `todo/views.py`; first repair byte-identical → `repair_no_progress`; atomic write 0 files; vs previous selective run 41.6% fewer tokens / 33.3% fewer calls / 22.4% faster but identical initial generation tokens (3,372) and output hashes → **harness safety controls verified, Qwen code quality unchanged**; incidental monolithic `exp-20260804-133016` diagnostic only; continuous cell blocked fail-closed (`CALIBRATION_REVIEW_REQUIRED`); accepted dedicated canary records = 1, successful = 0; full 9-record experiment NOT run; no merge/tag/Pilot/Kaggle authorized; no stable release claimed; record `selective_updates/records/SELECTIVE-CANARY-RESULTS-2026-08-04.md`; sentinel `SELECTIVE_CANARY_RESULT_AUDIT_REQUIRED`.**

---

## Executive Summary

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

---

## Current Post-R6 Health

### Test result

| Metric | Value |
|---|---|
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
| Bundled CLI nine-cell dry-run regression | passed |
| Builder build | content-identical (147 files / 962,188 bytes); manifests verified; no cache files |

### Deployment bundle

| Category | Files | Bytes |
|---|---:|---:|
| code | 90 | — |
| data | 56 | — |
| notebooks | 1 | — |
| **total** | **147** | **962,188** |

### Integrity and content

```text
Builder                  = scripts/build_upload_bundle.py only (build verified, content-identical)
Runtime source           = 0ece665 (fix(model): add model-aware Qwen BNB quantization profiles)
Deployment pin           = 0a596b8 (chore(deploy): pin Qwen 14B NF4 selective-canary bundle)
Deployment source        = 0ece665 (SOURCE_COMMIT=0ece665ef25e1b0ca3aa14f5f25977cadbd06d0c, DEPLOYED_BUILD_ID=0ece665)
Notebook source identity = SOURCE_COMMIT=0ece665, DEPLOYED_BUILD_ID=0ece665
Qwen quantization        = bnb-nf4 (--qwen-quantization default bnb-int8; canonical modes bnb-int8/bnb-nf4/fp16)
Model identity           = qwen:<checkpoint-basename>:<quantization>:cfg-<12hex> (replaces frozen qwen:1:int8)
Canary output            = runs/qwen14b_bnb_nf4_selective_canary (isolated, RUN_GENERIC_ONE_RUN=False, no --auto-resume-hf)
HF results repo          = NabilDo/selective-regeneration-experiment-results
Preflight over bundle    = passed (historical R7C gate; 14B prequantized fail-fast added)
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
Current real records            = 0/9 (1 accepted dedicated canary record, 0 successful)
Real Qwen records               = 0/9
Scientific evidence             = NONE (no real-model success yet)
Real token/call/time comparison = unavailable
Publication evidence            = unavailable
Pilot evidence                  = unavailable
```

No real-model success or efficiency claim is authorized before the real Smoke result audit. Smoke evidence is non-publication.

---
## Near goal

Kaggle engineering preflight for the Qwen 14B BNB-NF4 selective canary (after
the independent readiness audit; `QWEN14B_NF4_CANARY_READINESS_AUDIT_REQUIRED`).
After the preflight, a deliberate decision between repeating the dedicated
selective canary cell (output `runs/qwen14b_bnb_nf4_selective_canary`) and
proceeding to the full 9-record run — NOT a merge/tag/Pilot, NOT a fine-tune,
NOT a full relaunch.

## Far goal

Independent real-result audit → stable `v2.0.0-scientific-smoke` tag → freeze
Pilot matrix → Pilot execution → research experiment → statistical analysis →
paper evidence package.

## Next action

Independent audit of the Qwen 14B BNB-NF4 canary preparation closure (HEAD
`0a596b8`, record `QWEN14B-BNB-NF4-CANARY-READINESS.md`). After it passes, run
the Kaggle engineering preflight ONLY for the 14B bnb-nf4 profile; then decide:
repeat the dedicated canary cell OR proceed to the full 9-record run. Do not
merge/tag/Pilot/fine-tune or relaunch Kaggle before the independent result audit.

QWEN14B_NF4_CANARY_READINESS_AUDIT_REQUIRED