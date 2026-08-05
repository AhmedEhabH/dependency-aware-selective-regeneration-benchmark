# System State

## Current Phase
**QWEN 14B FINAL PREFLIGHT CLOSURE COMPLETE — THE THREE INDEPENDENTLY REPRODUCED PREFLIGHT BLOCKERS ARE CLOSED (CANARY OUTPUT DIR USED BEFORE ASSIGNMENT; PREFLIGHT REQUIRED EXACTLY ONE VISIBLE GPU; NUMERIC VERSION DIR PRODUCED A `qwen:1:*` READABLE IDENTITY); OFFICIAL CLEAN-ENV GATE (PYTHON 3.11.9 / PYTEST 8.4.2) FULL SUITE 1,890 PASSED / 32 SKIPPED / 0 FAILED, ZERO NEW STATIC FINDINGS, TWO EXPLICIT REGRESSION PROOFS PASS; NEXT ACTION = KAGGLE ENGINEERING PREFLIGHT CELL ONLY AFTER INDEPENDENT AUDIT; NO MERGE/TAG/PILOT/SCIENTIFIC RUN; NO STABLE RELEASE CLAIMED** (branch `fix/kaggle-smoke-v2-model-output-closure`, Commit A `0aa705d` + Commit B `cc7846b`, pushed, local = remote, tree clean; accepted real records remain 0/9; sentinel `QWEN14B_FINAL_PREFLIGHT_CLOSURE_AUDIT_REQUIRED`)

The Qwen 14B final preflight closure (2026-08-05) closed three blockers on top
of the previous Qwen 14B BNB-NF4 canary preparation state (`5ef6438` was
full-suite green but the independent audit rejected real preflight): the canary
cell referenced `SELECTIVE_CANARY_OUTPUT_DIR` before assignment (definition now
in the `setup-cell` after `OUTPUT_DIR`); the preflight
`EXPECTED_VISIBLE_GPU_COUNTS = (1, 2)` now accepts real 2×Tesla T4 environments
(`FAIL (N; expected 1 or 2)` otherwise); and `_checkpoint_identity_slug` maps
numeric version dirs to `<parent>-v<version>` so real Kaggle paths read
`qwen:14b-instruct-v1:bnb-nf4:cfg-<12hex>` instead of `qwen:1:*`. Official gate
in the declared clean environment (Python 3.11.9 / pytest 8.4.2): full suite
**1,890 passed / 32 skipped / 0 failed**; Dataset 285/5; Prompt 174; Pipeline
Smoke 223/12; Dry Run 9/9 (exit 0, dashboard + evidence files present); Metric
Verification 169; Ruff 0 new (91 pre-existing baseline in untouched files);
mypy strict Success (77 files); compileall clean; notebook 8/8 + 8/8 compile;
builder content-identical (147 files / 963,067 bytes); regression proofs:
2-GPU otherwise-valid preflight = PASS and canary setup reaches subprocess
construction without NameError. Ambient pytest 9.1.1 is diagnostic only, never
the official gate. No Kaggle run, no canary, no continuous, no
model/quantization/prompt/data/scenario change, no GPTQ/AWQ/GGUF/vLLM; **no real
14B result and no stable release claimed**; accepted real records = 0/9. Next
action after independent audit = Kaggle engineering preflight cell only. Record:
`selective_updates/records/QWEN14B-FINAL-PREFLIGHT-CLOSURE.md`.

The Qwen 14B BNB-NF4 canary closure (2026-08-05) replaced the frozen, model-blind
`qwen:1:int8` identity with `qwen:<checkpoint-basename>:<quantization>:cfg-<12hex>`,
computed before auto-resume from `config.json` fields (model_type, hidden_size,
num_hidden_layers, num_attention_heads) + requested mode + checkpoint
quantization method + SHA-256 (first 12 hex) of the canonical payload — so 7B
bnb-int8, 14B bnb-int8, and 14B bnb-nf4 always produce distinct identities and
auto-resume can no longer download the wrong experiment. An explicit
`bnb-nf4` profile was added (`load_in_4bit=True, bnb_4bit_quant_type="nf4",
bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True`, Tesla T4)
with canonical modes `bnb-int8`/`bnb-nf4`/`fp16` selectable via
`--qwen-quantization` (default `bnb-int8`; unknown values exit 2). A checkpoint
that already carries a non-bitsandbytes `quantization_config` (e.g. GPTQ) now
fails fast before tokenizer/model load with
`PREQUANTIZED_CHECKPOINT_INCOMPATIBLE`; no automatic fallback. The notebook is
pinned to the official unquantized `/kaggle/input/models/qwen-lm/qwen2.5-coder/
transformers/14b-instruct/1` (never `14b-instruct-gptq-int4`) with
`QWEN_QUANTIZATION = "bnb-nf4"`, `RUN_GENERIC_ONE_RUN = False`, an isolated
`qwen14b_bnb_nf4_selective_canary` output dir, and a fail-closed canary
preflight assertion (preflight passed, expected 14B identity, bnb-nf4, not
prequantized, GPU-only device map, free-VRAM threshold) before the benchmark
invocation; the canary keeps `--strategy selective --max-runs 1
--new-experiment` and never uses `--auto-resume-hf`. Preserved engineering
evidence: the failed 14B GPTQ attempt (`exp-20260804-195126`, 0 records /
0 calls / 0 tokens, preflight failed before the probe — GPTQConfig +
BitsAndBytesConfig conflict) and the auto-resume identity contamination
(downloaded `exp-20260804-133016` because both 7B and attempted 14B were
labeled `qwen:1:int8`). GPTQ support is deferred (different quantization stack,
incompatible with the declared bitsandbytes runtime). Full suite **1,877 passed
/ 32 skipped / 0 failed**; Dataset Validation PASS (27 scenarios / 27 unique
IDs, zero closure dataset changes); Prompt Validation 380 passed; Pipeline
Smoke 189 passed; Scripted 9-record dry run 9/9 exit 0; Metric Verification
169 passed; Ruff 0 new (21 pre-existing); strict mypy 0 new (5 pre-existing,
identical rule set to a self-contained HEAD baseline); compileall clean;
notebook cells compile 8/8 canonical + 8/8 bundled; builder rerun
content-identical (147 files / 962,188 bytes), manifests verified, no cache
files. Notebook identity = `SOURCE_COMMIT 0ece665ef25e1b0ca3aa14f5f25977cadbd06d0c`
/ `DEPLOYED_BUILD_ID 0ece665`. Commit A = `0ece665`
(`fix(model): add model-aware Qwen BNB quantization profiles`); Commit B =
`0a596b8` (`chore(deploy): pin Qwen 14B NF4 selective-canary bundle`); both
pushed, local = remote. Record:
`selective_updates/records/QWEN14B-BNB-NF4-CANARY-READINESS.md`. Sentinel:
`QWEN14B_NF4_CANARY_READINESS_AUDIT_REQUIRED`.

The pre-benchmark final reproducibility closure is **complete and green**. Dependency declarations in `pyproject.toml [dev]` + `requirements-dev.txt` now cover the full pre-benchmark test environment: Django==5.2.16, djangorestframework==3.17.1, pytest-django==4.12.0, pytest-asyncio==1.2.0, tabulate==0.10.0, httpx==0.28.1, Jinja2==3.1.6, huggingface_hub==0.24.0, types-pyyaml>=6.0,<7, pytest>=8.0,<9 (runtime `[project.dependencies]` and `requirements-smoke-kaggle.lock` untouched). The clean environment was deleted and recreated from declarations only (Python 3.11.9, `_workspace\cache\prebenchmark-py311`) and the complete clean gate was repeated. The previous `76a6b16` gate had **1 failure, not a green full suite**: `test_notebook_source_commit_matches_deployed_runtime_tree` failed because the mandated `pyproject.toml` declaration change broke byte-identity with the pinned `aac9914` SOURCE_COMMIT (frozen artifacts were not modified to force green and the truthful total 1,833 passed / 32 skipped / 1 failed was recorded). Root cause was dependency declarations changing `pyproject.toml` after the `aac9914`/`311e084` deployment pin; **no runtime, prompt, metric, scenario, evaluator, or data change was needed**. The exact independently reviewed deployment-only correction `f8d00d7` (imported via bundle fast-forward, exactly one commit) re-pins the deployment: bundled `kaggle_upload/code/pyproject.toml` gains the six declaration lines and becomes byte-identical to canonical, and both notebooks re-pin `SOURCE_COMMIT = e5d943065c6f4158c30a1cbbba39436ab2a7a898` / `DEPLOYED_BUILD_ID = e5d9430` (deployment source snapshot = `e5d9430`; deployment correction = `f8d00d7`). The complete clean gate after the correction is **green**: full suite = **1,834 passed / 32 skipped / 0 failed**; Dataset Validation 285 passed / 5 skipped (data unchanged); Prompt Validation 158 passed; Pipeline Smoke 220 passed / 12 skipped; Dry Run 9/9; Integration PASS; Metric Verification 169 passed; mypy strict Success (77 files); ruff 93 = 93 baseline (0 new); compileall clean; every notebook code cell compiles (7/7 canonical + 7/7 generated); bundle build content-identical (147 files / 928,329 bytes); manifests verified; no cache files in `kaggle_upload`. Historical `exp-20260801-210443` produced one failed model-output terminal record under source `6f88823` — preserved, excluded from the current `e5d9430` aggregation; current accepted real records = 0/9. Record: `selective_updates/records/KAGGLE-SMOKE-V2-MODEL-OUTPUT-CLOSURE.md`. Sentinel: `PRE_BENCHMARK_FINAL_SOURCE_REPIN_AUDIT_REQUIRED`.

R6 remains ACCEPTED AND FROZEN (`949e9c2`, freeze `4b2dd27`, branch published). Two real Kaggle Scientific Smoke V2 runs launched from the published deployment failed completely before any model call (`exp-20260801-024041` and `exp-20260801-024624`; both 9 planned / 0 succeeded / 9 failed / 0 model calls). The core runtime blockers were fixed and accepted by the independent runtime-fix audit; the R7A hardening closed the four reproduced findings and is recorded at `selective_updates/records/KAGGLE-SMOKE-V2-RUNTIME-HARDENING.md`. A subsequent real attempt reached 81 model calls / 47,694 tokens but produced 0 succeeded / 0 regenerated files. The R7B Smoke Finish (`bff0a82` + `17207bf`) makes the Qwen Smoke run observable and executable: strict single-fence JSON normalization, Qwen chat-template token counting + `inference_mode` + CUDA cache cleanup after every generation (success/OOM/other-exception), one shared backend instance per process, live progress line + cross-session ETA + structured log events, deterministic dashboard artifacts written under `OUTPUT_DIR/dashboard` and allowlisted for HF recovery, smoke-only `max_completion_tokens_per_call: 1024`, and a rewritten notebook with live subprocess streaming, actionable failure errors, dashboard display, continuous precondition gating, and `kaggle_console.log` persistence. Bundle rebuilt via `scripts/build_upload_bundle.py` (145 files / 858,225 bytes; notebook 31,023 bytes). Full suite = 1,735 passed / 32 skipped / 0 failed. An independent audit of the published repository ZIP found that the canonical and generated notebooks contained invalid Python code cells: the structural notebook edit inserted real newline characters inside ordinary quoted string literals (e.g. `print("\n` and `"\n".join(...)`), so `setup-cell`, `exec-cell`, and `continuous-smoke-cell` each raised `SyntaxError: unterminated string literal`. Root cause: invalid newline escaping in structurally edited cells; the missing check was full Python compilation of notebook code cells. Every damaged string literal was corrected to an escaped `\n` sequence (dashboard headings, per-run table heading, matrix heading, failure-causes heading, actionable-error separators, `"\n".join(lines)`, continuous-precondition messages, live-output heading, return-code line, final console-tail joins), and the parametrized regression `test_all_deployed_notebook_code_cells_compile` (covering both notebooks) was added. Bundle rebuilt via `scripts/build_upload_bundle.py` (145 files / 858,134 bytes; notebook 30,932 bytes); canonical and generated notebooks now compile 5/5 code cells with exact parity. **R7B runtime implementation remains accepted pending a short re-audit; valid real Qwen remains 0/9; Kaggle remains blocked pending that re-audit.**

## Phase State
```text
R4 = accepted and frozen (explicit freeze commit f5ae826)
R5 = accepted and frozen (independent re-audit 2026-08-01, recorded at 7761c48)
R6 = ACCEPTED AND FROZEN (independent re-audit 2026-08-01, recorded at 949e9c2; freeze commit 4b2dd27)
Kaggle attempts = 2 (exp-20260801-024041, exp-20260801-024624) — both failed pre-model, preserved
Latest real attempt = exp-20260801-123125 (FP16 → OOM; deps drifted) — not scientific evidence
Runtime fixes = committed (de3163f) and pinned (fb60972) — core accepted by independent audit
R7A hardening = complete (remote sync truth, notebook schema, HF fixtures, docs) — d50e89e + 4c73db6
R7B Smoke Finish = complete (observable Qwen smoke) — bff0a82 + 17207bf
R7B notebook compile correction = applied (4c7a0af) — invalid newline escaping fixed, regression added
R7C root closure = COMPLETE (environment memory + prompt contracts) — 7a80e53 + f01b8f0; exact correction imported ffa179a + 6d6aa36
R7C full-gate truth = prior "1,451 full suite" was a SUBSET; true first full suite 23 failed / 1,759 passed / 32 skipped; after correction 1,790 passed / 32 skipped / 0 failed
R7C post-gate audit = performed on 5e47a1e (independent); exact correction imported 6f88823 + 5797fc0 (HEAD 5797fc0, pushed); full gate now 1,796 passed / 32 skipped / 0 failed
Deterministic interpreter closure = complete — aac9914 + 311e084 (bare interpreter tokens bound to active runtime); clean-env full gate 1,834 passed / 32 skipped / 0 failed (pre-declaration)
Pre-benchmark reproducibility closure = COMPLETE — dependencies fully declared (769d84e + e5d9430); clean env recreated from declarations only; previous 76a6b16 gate = 1,833 passed / 32 skipped / 1 failed (structural notebook-pin identity test, truthful, not forced green — root cause: declaration change to pyproject.toml after the aac9914/311e084 pin); deployment-only correction f8d00d7 (bundle fast-forward) re-pins SOURCE_COMMIT=e5d9430, DEPLOYED_BUILD_ID=e5d9430 and makes bundled pyproject.toml byte-identical to canonical; COMPLETE CLEAN SUITE NOW GREEN = 1,834 passed / 32 skipped / 0 failed; Dataset 285/5 (data unchanged), Prompt 158, Pipeline Smoke 220/12, Dry Run 9/9, Integration PASS, Metric Verification 169; mypy strict Success (77 files); ruff 93 = 93 baseline (0 new)
Historical experiment = exp-20260801-210443 produced ONE failed model-output terminal record under 6f88823 — preserved, excluded from current e5d9430 aggregation
POST-SMOKE calibration closure = COMPLETE — Closure A per-attempt atomic regeneration, Closure B repair no-progress detection (repair_no_progress), Closure C calibration continuation gate (AUTHORIZE_CONTINUOUS_AFTER_CALIBRATION_REVIEW=False, fail-closed), Closure D cooperative deadline semantics (scientific_budget_exhausted terminal); commits 27c1693 (runtime+tests) + 56772fe (bundle/notebook pin, SOURCE_COMMIT=27c1693e22b1a68be0b299fb146d9ff1e500908b, DEPLOYED_BUILD_ID=27c1693) + 231b0a5 (test-fixture reconciliation); first full gate's 9 failures were stale constant-output fixtures, not validly proven pre-existing; COMPLETE SUITE GREEN = 1,849 passed / 32 skipped / 0 failed; mypy strict Success (77 files); ruff 93 = 93 baseline (0 new); bundle content-identical (147 files / 934,495 bytes); calibration evidence exp-20260803-002741 = 9 terminal records / 0 succeeded / 8 failed / 1 timed_out / 81 model calls / 118,211 tokens (0/9, preserved, not accepted scientific evidence); no Kaggle rerun; audit marker POST_SMOKE_CALIBRATION_CLOSURE_AUDIT_REQUIRED
FINAL SELECTIVE CANARY READINESS closure = COMPLETE — independent audit (GPT-5.6 Thinking) REJECTED canary readiness at f727b3e (full suite green but three blockers: (1) cooperative deadline not checked before every generation call — direct repro 3 calls and false success after deadline; (2) regenerated_artifact_count=1 with 0 writes on atomic abort — direct repro; (3) generic one-run cell selects monolithic, not selective — execution-plan order is scenario-first); Commit A 50ec2c1 (fix(smoke): enforce per-call deadline and atomic metric truth) + Commit B 28ecc5a (chore(deploy): pin selective-canary-ready Smoke V2 bundle, SOURCE_COMMIT=50ec2c1ca43c230aed4538be32ca7dab2ccc22e5, DEPLOYED_BUILD_ID=50ec2c1, dedicated selective-calibration-canary-cell with _verify_selective_canary asserting exactly one todo-smoke-001/selective record, isolated output runs/selective_calibration_canary, no --auto-resume-hf, continuous not authorized) + test alignment 356722b (align affected unit tests with atomic metric truth: model_call_budget_exhausted=False on MagicMock exec_ret, r4 assertions updated to aborted/rejected staged statuses, asyncio loop fix in TestIterativeAgentDeadline); direct adversarial proofs added (TestGenerationDeadline 1 call, TestRepairDeadline 2 calls + repair_model_calls 1, TestIterativeAgentDeadline 1 call); FULL SUITE GREEN = 1,856 passed / 32 skipped / 0 failed (571.57s); grouped per-category 629 passed / 1 skipped; scripted dry run --profile scientific-smoke-v2 into fresh dir = 9/9 exit 0 (default runs dir had stale checkpoint → ReportRebuildError); mypy strict Success (77 files); ruff 0 new (175 pre-existing repo-wide, 19 pre-existing E501 in test_r4_token_and_metrics.py); compileall clean; notebooks compile 8/8 bundle code cells incl. canary cell; bundle content-identical (147 files / 948,250 bytes, tree hash 3b8d5b0ebf5e3ab8); calibration exp-20260803-002741 preserved, 0/9, not accepted scientific evidence; no Kaggle rerun; no stable release claimed; audit marker FINAL_SELECTIVE_CANARY_READINESS_AUDIT_REQUIRED
SELECTIVE CALIBRATION CANARY = EXECUTED (2026-08-04) — dedicated canary exp-20260804-133523 (todo-smoke-001 / selective, source/build 50ec2c1) FAILED model_output: 4 calls / 5,804 tokens / 257.596 s / 3 selected / 2 preserved / 0 written; initial 3 calls / 3,372 tokens, repair 1 call / 2,432 tokens (first repair byte-identical → repair_no_progress stopped the round); atomic application wrote 0 files; defects in todo/models.py (max_length=5 vs MEDIUM length 6) + duplicated Priority(models.TextChoices) in todo/serializers.py and todo/views.py; vs previous selective run 41.6% fewer tokens / 33.3% fewer calls / 22.4% faster but initial generation tokens (3,372) and output hashes identical → harness safety controls verified, Qwen code quality unchanged; HF recovery_uploaded; checkpoint total_planned 3 / 1 completed / 2 pending; incidental monolithic exp-20260804-133016 (6 calls / 7,927 tokens / 300.165 s / scientific_budget_exhausted / 0 written) = diagnostic evidence only, NOT the authorized canary, NOT an accepted comparison; continuous cell blocked fail-closed by CALIBRATION_REVIEW_REQUIRED; accepted current dedicated canary records = 1, successful = 0; full 9-record experiment NOT run; no merge/tag/Pilot/Kaggle authorized; record selective_updates/records/SELECTIVE-CANARY-RESULTS-2026-08-04.md; audit marker SELECTIVE_CANARY_RESULT_AUDIT_REQUIRED
QWEN 14B BNB-NF4 CANARY PREPARATION = COMPLETE (2026-08-05) — Commit A 0ece665 (fix(model): add model-aware Qwen BNB quantization profiles) + Commit B 0a596b8 (chore(deploy): pin Qwen 14B NF4 selective-canary bundle), both pushed, local = remote; model-aware identity qwen:<checkpoint-basename>:<quantization>:cfg-<12hex> replaces frozen qwen:1:int8 (blocks auto-resume cross-model contamination; verified 7B int8 / 14B int8 / 14B NF4 differ); canonical modes bnb-int8 / bnb-nf4 / fp16 via --qwen-quantization (default bnb-int8, unknown exits 2); NF4 profile = load_in_4bit=True, bnb_4bit_quant_type=nf4, bnb_4bit_compute_dtype=float16, bnb_4bit_use_double_quant=True (T4); prequantized non-bnb checkpoint fails fast (PREQUANTIZED_CHECKPOINT_INCOMPATIBLE) before model load; notebook pinned to 14b-instruct/1 base (never gptq-int4), QWEN_QUANTIZATION=bnb-nf4, RUN_GENERIC_ONE_RUN=False, isolated qwen14b_bnb_nf4_selective_canary output, fail-closed canary preflight gate, no --auto-resume-hf, SOURCE_COMMIT=0ece665 / DEPLOYED_BUILD_ID=0ece665; preserved engineering evidence = failed 14B GPTQ attempt exp-20260804-195126 (0 records / 0 calls / 0 tokens, preflight failed before probe, GPTQConfig + BitsAndBytesConfig conflict) + auto-resume contamination downloaded exp-20260804-133016 (7B and attempted 14B both labeled qwen:1:int8); GPTQ support deferred (incompatible quantization stack); FULL SUITE GREEN = 1,877 passed / 32 skipped / 0 failed; Dataset 27 scenarios / 27 IDs / 0 duplicates (no closure dataset changes); Prompt 380 passed; Pipeline Smoke 189 passed; Scripted dry run 9/9 exit 0; Metric Verification 169 passed; ruff 0 new (21 pre-existing); mypy 0 new (5 pre-existing, identical rule set to self-contained HEAD baseline); compileall clean; notebooks compile 8/8 canonical + 8/8 bundled; bundle content-identical rerun (147 files / 962,188 bytes), manifests verified, no cache files; next action = Kaggle engineering preflight ONLY for 14B bnb-nf4; audit marker QWEN14B_NF4_CANARY_READINESS_AUDIT_REQUIRED
Current real records = 0/9
Real Qwen records = 0/9
Pilot = not authorized
README = updated
push = PUBLISHED — fix branch upstream origin/fix/kaggle-smoke-v2-model-output-closure, local = remote
stable tag = blocked
next action = Kaggle engineering preflight ONLY for the 14B bnb-nf4 profile (independent readiness audit first if required); NOT a merge/tag/Pilot, NOT a scientific canary/9-record run, NOT a fine-tune, NOT a full relaunch
```

## Previous Phase
**R5 — Nine Non-Dry Scripted Production Records — ACCEPTED AND FROZEN**

R5 proved exactly nine non-dry scripted production records (3 frozen scenarios × 3 arms × 1 repetition) through the real production orchestration path. R5 was accepted by the independent re-audit on 2026-08-01 at `7761c48`. The cleaned R5 tail is `8fafb50`, `a24a9cd`, `875e4d1`, `ee148fa`, `7761c48`. The old contaminated tail is preserved on `backup/r5-pre-audit-c3ecad2`.

## Current Task
The **dedicated selective calibration canary** has been executed and its result
ingested (record: `selective_updates/records/SELECTIVE-CANARY-RESULTS-2026-08-04.md`).
`exp-20260804-133523` (`todo-smoke-001 / selective`, source/build `50ec2c1`)
**failed with classification `model_output`**: 4 model calls / 5,804 tokens /
257.596 seconds, 3 artifacts selected / 2 preserved / **0 written**. Qwen's
outputs were defective in `todo/models.py` (`max_length=5` for a `MEDIUM` value
of length 6) and duplicated `Priority(models.TextChoices)` in both
`todo/serializers.py` and `todo/views.py`; the first repair was byte-identical,
so `repair_no_progress` stopped the round and the atomic write produced zero
files. Versus the previous selective run on the same scenario, the canary used
41.6% fewer tokens, 33.3% fewer calls, and was 22.4% faster, but the initial
generation tokens (3,372) and the three output SHA-256 hashes were **identical**
— meaning the harness safety controls (deadline, no-progress detection, atomic
writes, continuation gate) worked exactly as designed while **Qwen code quality
did not improve**. The incidental monolithic run `exp-20260804-133016`
(6 calls / 7,927 tokens / 300.165 s / `scientific_budget_exhausted`) is
diagnostic evidence only. The continuous cell correctly stopped fail-closed with
`CALIBRATION_REVIEW_REQUIRED`. No successful implementation exists; the full
9-record experiment is **not run**; merge/tag/Pilot/Kaggle remain **not
authorized**. Next: independent audit of the canary results, then a deliberate
decision between repeating the canary and proceeding to the full 9-record run.
 The real attempt `exp-20260801-123125` failed at runtime root (FP16 model exceeded GPU memory; dependency versions had drifted from the previously assumed runtime). R7C (`fix/kaggle-smoke-v2-real-run-root`, commits `7a80e53` + `f01b8f0`) closes the four root contracts: **(1) environment memory** — exact runtime pins in `requirements-smoke-kaggle.lock` (Django==5.2.16, djangorestframework==3.17.1, pytest==8.4.2, pytest-django==4.12.0, accelerate==1.14.0, bitsandbytes==0.49.2, transformers==4.57.6 — Qwen14B NF4 transformers v4 loader closure (2026-08-05); torch intentionally unpinned, Kaggle image provides its GPU torch build) installed and verified in the notebook `install-lock-cell` (`EXPECTED_RUNTIME` via `RUNTIME_ATTR`, `runtime_environment.json` schema `kaggle_runtime_environment.v1`); **(2) memory contract** — int8 default (`qwen:1:int8`), `PYTORCH_ALLOC_CONF=expandable_segments:True`, seeded 64-token `run_probe`, preflight ≥2.0 GiB VRAM headroom; **(3) prompt contract** — frozen `RegenerationScenarioContext` in strategy prompts, preserve-only byte-identity enforcement when `expected_actions` is non-empty; **(4) repair contract** — `FailureKind.infrastructure_nonrepairable` first-failure, one execution, zero LLM repair. `src/benchmark/execution/preflight.py` adds `--kaggle-preflight-only` (exit 0/1, no experiment/RunRecord/checkpoint/workspace/HF state; schema `kaggle_smoke_preflight.v1`, 6 checks), run as a notebook gate cell before the exec cell; `secrets-cell` moved after preflight. Notebook now: setup → install lock → preflight → secrets → run. Bundle rebuilt via `scripts/build_upload_bundle.py` (147 files / 894,735 bytes; notebook 36,351 bytes). Full suite (contract-first) = 1,451 passed / 31 skipped / 0 failed was a SUBSET mislabeled as full suite — the true first full suite was 23 failed / 1,759 passed / 32 skipped (root cause: blanket `baseline_validation => infrastructure_nonrepairable` in `src/benchmark/execution/runner.py`); the independent GPT-5.6 Thinking correction was imported via bundle fast-forward (`ffa179a` + `6d6aa36`, HEAD `6d6aa36`, pushed): the exact 23 former failures now pass, and DRF import mapping, exact version verification, fail-fast preflight, driver-level VRAM, CPU-offload rejection, Python 3.12 runtime contract, and stale source identity (SOURCE_COMMIT=ffa179a / DEPLOYED_BUILD_ID=ffa179a) were corrected. Current full gate (Windows / Python 3.11.5) = 1,790 passed / 32 skipped / 0 failed; mypy strict 0; compileall clean; builder rerun clean. Valid real Qwen remains 0/9; Kaggle remains blocked pending the independent full-gate audit. Current task: **independent full-gate audit of the corrected R7C branch** (`R7C_CORRECTION_FULL_GATE_AUDIT_REQUIRED`), then update the Kaggle code dataset + notebook, then one real cell, then continue to 9/9 — blocked on the audit. **R7C post-gate correction imported (independent post-gate audit on e47a1e\, exact correction f88823\ + /97fc0\, HEAD /97fc0\, pushed):** the audit found (a) the project-local \ImportError\ was incorrectly bypassing repair (the blanket marker match is replaced by the canonical \classify_validation_repairability\ classifier, so project-local \ModuleNotFoundError\ and \cannot import name\ are repairable while missing declared Django and CUDA OOM stay \infrastructure_nonrepairable\), (b) the bundled preflight could not import \enchmark\ without an ambient \PYTHONPATH\ (the bundled script now bootstraps its own \src/\ and reaches its preflight in a clean subprocess), and (c) preflight output was buffered (now streamed and persisted). Notebook source identity is now \SOURCE_COMMIT = 6f88823\, \DEPLOYED_BUILD_ID = 6f88823\. Current full gate (Windows / Python 3.11.5) = 1,796 passed / 32 skipped / 0 failed; mypy strict 0; compileall clean; builder rerun content-identical; bundle manifests verified. Valid real Qwen remains 0/9; no scientific evidence exists yet; Kaggle remains blocked pending the final independent full-gate audit, after which the only authorized Kaggle action is the engineering preflight cell - not the scientific One-Run cell.

## Recent Non-Phase Additions
- Added `README.md` (project overview, architecture, usage, license)
- Added `LICENSE` (MIT, copyright Ahmed Ehab H.)
- Added `reports/PROJECT_HEALTH_REPORT.md` (engineering dashboard)
- Legacy Seven-Arm Kaggle orchestration smoke passed (tag `v0.7.0-smoke-passed`): 7/7 arms, Qwen inference, non-publication — **historical orchestration evidence only, not V2 evidence**
- Audit merge commit `3a16596` on `main` adds `ARM_TO_PROTOCOL_EXECUTION_AUDIT.md`, `ARM_AUDIT_DECISION_REQUIRED.md`, `EXISTING_TAGS_AUDIT.md`

## Completed Work
- [x] Phase 0 — Bootstrap and Environment (LOCAL_ENGINEERING_VALIDATED)
- [x] Phase 1 — Input Audit (LOCAL_ENGINEERING_VALIDATED)
- [x] Phase 2A — Research Protocol Draft (DRAFT — superseded by v1.0)
- [x] Phase 2B — Protocol Freeze (FROZEN)
- [x] Phase 3 — Repository and Scenario Preparation (COMPLETE)
- [x] Phase 3.5 — Static Architecture Audit and Project Map (COMPLETE)
- [x] Phase 3.6 — Structure Remediation and Baseline Commit (COMPLETE)
- [x] **Phase 4A — Domain Models and Contracts** (COMPLETE)
- [x] **Phase 4B — Loaders and Validation** (COMPLETE, MERGED, AND PUSHED)
- [x] Implement 6 StrEnum classes (ActionKind, ArtifactType, BlastRadius, RunStatus, FailureKind, EvidenceTier)
- [x] Implement 12 typed exception classes with context dict
- [x] Implement 24 frozen dataclass domain models with post-init validation
- [x] Implement 11 runtime-checkable protocol interfaces
- [x] Implement generic Registry[T] with freeze/lookup/list support
- [x] Implement ExecutionContext (controlled-immutable)
- [x] Implement 7 Pydantic v2 config models with cross-field validation
- [x] Implement YAML config loader and structural validation
- [x] Create package setup (pyproject.toml) with ruff/mypy/pytest config
- [x] Write 111 Phase 4A unit/contract/isolation tests (all passing)
- [x] Install package in editable mode for import resolution
- [x] Verify Phase 4A quality gates: ruff (pass), mypy (pass), pytest (111/111 pass), pip check (pass)
- [x] Create docs/PHASE4A_DOMAIN_MODEL_REFERENCE.md
- [x] Create reports/PHASE4A_DOMAIN_MODELS_REPORT.md
- [x] **Phase 4B — Loaders and Validation** (COMPLETE, MERGED, AND PUSHED)
- [x] Implement RepositoryLoaderBase with resolve_identity/resolve_snapshot
- [x] Implement RepositoryManifest, RepositoryVersionEntry, RepositoryProfile, ManifestCollection (frozen dataclasses)
- [x] Implement RepositoryLoader (YAML loading from manifests/ and repository_profiles/)
- [x] Implement SnapshotMetadata, create_snapshot_metadata, validate_snapshot
- [x] Implement WorkspacePath, validate_workspace_path, check_isolation
- [x] Implement ScenarioModel with to_core_scenario() and dual-format expected_actions parsing
- [x] Implement ScenarioLoader (load_all, load_by_repository)
- [x] Implement ScenarioValidator (required fields, duplicate actions)
- [x] Implement ScenarioSequencer (order by blast_radius)
- [x] Write 95 new Phase 4B tests (84 unit/contract + 11 integration)
- [x] Verify Phase 4B quality gates: 206/206 tests pass; ruff 0 violations; mypy 0 errors; pip check clean
- [x] Create docs/PHASE4B_LOADERS_AND_VALIDATION_REFERENCE.md
- [x] Create reports/PHASE4B_LOADERS_AND_VALIDATION_REPORT.md
- [x] Merge Phase 4B into main (commit `2fdc3c4`)
- [x] Reconcile SYSTEM_STATE.md for Phase 4B completion (this update)
- [x] Batch update all state files for Phase 4B → 4C transition
- [x] **Phase 4C — Model Backends** (COMPLETE, MERGED, AND PUSHED)
- [x] Implement MockLLMBackend (deterministic, configurable response text)
- [x] Implement DryRunLLMBackend (fixture JSON loading with fallback)
- [x] Implement KaggleQwenBackend skeleton (lazy torch/transformers imports, safe locally)
- [x] Implement BackendFactory wrapping Registry[LLMBackend] with register/create/freeze
- [x] Write 23 new Phase 4C tests (22 unit + 1 isolation)
- [x] Verify Phase 4C quality gates: 229/229 tests pass; ruff 0 violations; mypy 0 errors; pip check clean
- [x] Create docs/PHASE4C_MODEL_BACKENDS_REFERENCE.md
- [x] Create reports/PHASE4C_MODEL_BACKENDS_REPORT.md
- [x] Reconcile SYSTEM_STATE.md for Phase 4C completion (this update)
- [x] Batch update all state files for Phase 4C → 4D transition
- [x] **Phase 4D — Execution Core** (COMPLETE, MERGED, AND PUSHED)
- [x] Implement BudgetManager with injectable Clock, multi-axis budget enforcement
- [x] Implement RunStateMachine with 6-state typed transitions and terminal-state protection
- [x] Implement RepairLoop with 1+2 attempt lifecycle and configurable FailureClassifier
- [x] Implement IsolationContext wrapping Phase 4B workspace utilities
- [x] Implement BenchmarkRunner coordinating strategy+backend+isolation into RunRecord
- [x] Implement BenchmarkPipeline with single/batch/dry-run modes
- [x] Write 59 new Phase 4D tests (all passing)
- [x] Verify Phase 4D quality gates: 288/288 tests pass; ruff 0 violations; mypy 0 errors; pip check clean
- [x] Create docs/PHASE4D_EXECUTION_CORE_REFERENCE.md
- [x] Create reports/PHASE4D_EXECUTION_CORE_REPORT.md
- [x] Reconcile SYSTEM_STATE.md for Phase 4D completion (this update)
- [x] Batch update all state files for Phase 4D → 4E transition
- [x] **Phase 4E — Impact Strategies** (COMPLETE, MERGED, AND PUSHED)
- [x] Implement 7 strategy patterns: monolithic, agent, selective, compiled_ai, delta_mcp, incr_rtl, code_plan
- [x] Implement StrategyRegistry with register/create/freeze/lookup
- [x] Implement graph package: DependencyNode, DependencyEdge, DependencyGraphModel, PythonImportExtractor, ImpactPropagator, ScopeReducer
- [x] Implement selection package: ArtifactSelector, RegenerationPlanner
- [x] Write 43 new Phase 4E tests (all passing)
- [x] Verify Phase 4E quality gates: 332/332 tests pass; ruff 0 violations; mypy 0 errors; pip check clean
- [x] Create reports/PHASE4E_IMPACT_STRATEGIES_REPORT.md
- [x] Reconcile SYSTEM_STATE.md for Phase 4E completion
- [x] Batch update all state files for Phase 4E → 4F transition
- [x] **Phase 4F — Evaluation Engine** (COMPLETE)
- [x] Create `src/benchmark/evaluation/` package with EvaluationEngine, MetricComputer
- [x] Create `src/benchmark/comparison/` package with GroundTruthComparator, ResultAggregator
- [x] Create `src/benchmark/statistics/` package with StatisticalAnalyzer, ConfidenceIntervalCalculator, EffectSizeComputer, NotebookExporter, PublicationTableBuilder
- [x] Implement primary metrics: recall, precision, F1, specificity, FPR, FNR
- [x] Implement secondary metrics: accuracy, action_accuracy
- [x] Implement confidence intervals: bootstrap, normal, Wilson, Agresti-Coull
- [x] Implement effect sizes: Cohen's d, Cliff's delta
- [x] Implement statistical analysis: Mann-Whitney U, non-inferiority tests
- [x] Implement notebook export: JSON, DataFrame
- [x] Implement publication tables: CSV, Markdown, LaTeX
- [x] Write 73 new Phase 4F tests (all passing)
- [x] Verify Phase 4F quality gates: 405/405 tests pass; ruff 0 violations; mypy 0 errors; pip check clean
- [x] Independent scientific audit: 2 defects found/fixed, 5 regression tests added (410 total)
- [x] Create docs/PHASE4F_EVALUATION_ENGINE_REFERENCE.md
- [x] Create reports/PHASE4F_EVALUATION_ENGINE_REPORT.md
- [x] Create reports/PHASE4F_INDEPENDENT_SCIENTIFIC_AUDIT.md
- [x] Reconcile SYSTEM_STATE.md for Phase 4F completion and audit
- [x] **Phase 4F.1 — Scientific Evaluation Remediation** (COMPLETE)
- [x] Full `aggregate_run_records` implementation (micro + macro equal-weight)
- [x] `paired_bootstrap_ci()` for H1 (matched on repo-scenario-rep)
- [x] `benjamini_hochberg()` + `holm_correction()` for DA-14
- [x] NI sensitivity margins at 0.03 and 0.10 (DA-08)
- [x] Generalized binomial CI via `scipy.stats.norm.ppf`
- [x] Fixed BH implementation bug (descending sort → ascending + step-down)
- [x] 31 new tests (441 total); all quality gates pass
- [x] Create reports/PHASE4F_1_SCIENTIFIC_REMEDIATION_REPORT.md
- [x] **Kaggle Smoke Pass** (engineering validation complete)
- [x] Fix failure propagation: real Qwen errors, token_usage, smoke-stage tagging
- [x] Fix graph wiring: ProfileGraphBuilder, capabilities design, NullLLMBackend
- [x] 20 new regression tests (504 total + 1 skipped torch); all quality gates pass
- [x] Tag `v0.7.0-smoke-passed` at commit `0c58250` (main branch)

### Phase 4A/4B/4C Production — 22 files
6 under `src/benchmark/core/`: `__init__.py`, `context.py`, `enums.py`, `exceptions.py`, `models.py`, `protocols.py`, `registry.py`
7 under `src/benchmark/config/`: `__init__.py`, `models.py`, `loader.py`, `validation.py`
6 under `src/benchmark/repositories/`: `__init__.py`, `base.py`, `manifest.py`, `loader.py`, `snapshot.py`, `workspace.py`
5 under `src/benchmark/scenarios/`: `__init__.py`, `models.py`, `loader.py`, `validator.py`, `sequencing.py`
5 under `src/benchmark/llm/`: `__init__.py`, `base.py`, `mock_backend.py`, `dry_run_backend.py`, `kaggle_qwen_backend.py`

### Phase 4D Production — 7 files
All under `src/benchmark/execution/`: `__init__.py`, `budgets.py`, `state_machine.py`, `repair.py`, `isolation.py`, `runner.py`, `pipeline.py`

### Phase 4F Production — 11 files
Evaluation package: `src/benchmark/evaluation/__init__.py`, `engine.py`, `metrics.py`
Comparison package: `src/benchmark/comparison/__init__.py`, `ground_truth.py`, `aggregator.py`
Statistics package: `src/benchmark/statistics/__init__.py`, `analysis.py`, `confidence_intervals.py`, `effect_sizes.py`, `reporting.py`

### Tests (Phase 4A–4F)
8 unit test files: `test_repositories_manifest.py` (15), `test_repositories_loader.py` (8), `test_repositories_snapshot.py` (12), `test_repositories_workspace.py` (9), `test_scenarios_models.py` (11), `test_scenarios_loader.py` (9), `test_scenarios_validator.py` (7), `test_scenarios_sequencing.py` (5)
2 integration test files: `test_repositories_integration.py` (6), `test_scenarios_integration.py` (5)
1 contract test file: `test_loaders_contract.py` (4)
3 test package init files

### Phase 4D Tests — 7 files
All under `tests/unit/execution/`: `__init__.py`, `test_budgets.py` (14), `test_state_machine.py` (13), `test_repair.py` (8), `test_isolation.py` (9), `test_runner.py` (7), `test_pipeline.py` (6)

### Phase 4E Tests — 3 files
All under `tests/unit/strategies/` and `tests/unit/graph/`, `tests/unit/selection/`: `__init__.py`, `test_strategies.py` (21), `test_graph.py` (16), `test_planner.py` (6)

### Phase 4F Tests — 8 files
All under `tests/unit/evaluation/`, `tests/unit/comparison/`, `tests/unit/statistics/`: `__init__.py` (×3), `test_engine.py` (7), `test_metrics.py` (13), `test_comparison.py` (14), `test_statistics.py` (24), `test_reporting.py` (15)

### Documentation (Phase 4A–4F)
`docs/PHASE4A_DOMAIN_MODEL_REFERENCE.md`, `docs/PHASE4B_LOADERS_AND_VALIDATION_REFERENCE.md`, `docs/PHASE4C_MODEL_BACKENDS_REFERENCE.md`, `docs/PHASE4D_EXECUTION_CORE_REFERENCE.md`, `docs/PHASE4F_EVALUATION_ENGINE_REFERENCE.md`
`reports/PHASE4A_DOMAIN_MODELS_REPORT.md`, `reports/PHASE4B_LOADERS_AND_VALIDATION_REPORT.md`, `reports/PHASE4C_MODEL_BACKENDS_REPORT.md`, `reports/PHASE4D_EXECUTION_CORE_REPORT.md`, `reports/PHASE4F_EVALUATION_ENGINE_REPORT.md`, `reports/PROJECT_HEALTH_REPORT.md`

## Phase 4C — Files Created (5 production + 6 test + 2 doc = 13 new files, 1 modified)

### Production — 5 files
All under `src/benchmark/llm/`: `__init__.py`, `base.py`, `mock_backend.py`, `dry_run_backend.py`, `kaggle_qwen_backend.py`

### Tests — 6 files
5 files under `tests/unit/llm/`: `__init__.py`, `test_llm_mock_backend.py` (6), `test_llm_dry_run_backend.py` (5), `test_llm_kaggle_qwen_backend.py` (3), `test_llm_factory.py` (8)
1 modified: `tests/test_import_isolation.py` (added LLM-specific import test)

### Documentation — 2 files
`docs/PHASE4C_MODEL_BACKENDS_REFERENCE.md`, `reports/PHASE4C_MODEL_BACKENDS_REPORT.md`

## Frozen Protocol Checksums (SHA-256)

| Document | Checksum |
|----------|----------|
| `docs/FINAL_RESEARCH_PROTOCOL.md` | `9D4A140C1CBA19C3076AF8C71AD859F243C31836FECD6026C2CD86CFC271B148` |
| `docs/GROUND_TRUTH_PROTOCOL.md` | `83F1ADB28CD99B6859BD7BE8189B22C2D272538CBB19B386D921F9DC728DD9E5` |
| `docs/SCENARIO_TAXONOMY.md` | `5FA4D7114E1993E2D8FB570EC9BAC4129F3956B09E7555C200C118E206D9BB62` |
| `docs/STATISTICAL_ANALYSIS_PLAN.md` | `FA8B76C41FF05462E80675B297917A904ECD4605CA5AD54C84740A38B6AB1D4C` |
| `docs/EXECUTION_AND_FAILURE_POLICY.md` | `FB3072880A6EBDD259707F9F64F50D56DF6DD4B04DBDE80E1E2867C80295F49E` |
| `docs/LEAKAGE_PREVENTION_PROTOCOL.md` | `F78AF1F57C8A59EA324E1996B4B172F7A02EF9D0D8EB66DD1D02F9EFD2B53910` |
| `docs/REPRODUCIBILITY_PROTOCOL.md` | `A59A666CC740BF2F9F9D9D193422892C1E064D99F6D264250C5625CFB35DB02E` |
| `docs/RESEARCHER_DECISIONS_DA_AC.md` | `1884352AF8813E794A25A1BAE947269BB343C788A22A933F59754B7DEE607BD3` |

## Environment Status
- **Platform:** Windows (win32)
- **Python (project env):** 3.11.5
- **Conda:** Anaconda (at C:\Users\Ahmed\AppData\Local\anaconda3)
- **Git:** 2.49.0
- **Project env:** `selective-regen-benchmark` — ACTIVATED AND VALIDATED
- **Package resolver:** conda (defaults channel) + pip
- **Dependency conflicts:** None

## Phase 4D — Files Created (7 production + 7 test + 2 doc = 16 new files)

### Production — 7 files
All under `src/benchmark/execution/`: `__init__.py`, `budgets.py`, `state_machine.py`, `repair.py`, `isolation.py`, `runner.py`, `pipeline.py`

### Tests — 7 files
All under `tests/unit/execution/`: `__init__.py`, `test_budgets.py` (14), `test_state_machine.py` (13), `test_repair.py` (8), `test_isolation.py` (9), `test_runner.py` (7), `test_pipeline.py` (6)

### Documentation — 2 files
`docs/PHASE4D_EXECUTION_CORE_REFERENCE.md`, `reports/PHASE4D_EXECUTION_CORE_REPORT.md`

## Local Checks Passed (Phase 4A + 4B + 4C + 4D + 4E)
- 6 StrEnum classes with stable string values: ✅
- 12 exception classes in typed hierarchy: ✅
- 24 frozen dataclass domain models with post-init validation: ✅
- 11 runtime-checkable protocol interfaces: ✅
- Generic Registry[T] with freeze/lookup/list: ✅
- ExecutionContext with controlled immutability: ✅
- 7 Pydantic v2 config models with cross-field validation: ✅
- YAML config loader and structural validation: ✅
- Package installable in editable mode: ✅
- Ruff lint+format: 0 violations (all source and test files): ✅
- Mypy strict: 0 errors (93 files): ✅
- Pytest: 441/441 passed: ✅
- pip check: no broken requirements: ✅
- Import isolation: torch/transformers not imported by benchmark.llm: ✅
- MockLLMBackend: deterministic output, protocol conformance: ✅
- DryRunLLMBackend: fixture loading with fallback: ✅
- KaggleQwenBackend: local execution raises ModelBackendError, lazy imports safe: ✅
- BackendFactory: register/create/freeze/contains/len with Registry: ✅
- Repository loader: loads real manifests and profiles: ✅
- Scenario loader: loads all 24 real scenario YAMLs: ✅
- Scenario validation: all scenarios pass structural validation: ✅
- Snapshot metadata: creation and validation: ✅
- Workspace isolation: prevents cross-run contamination: ✅
- All prior Phase 3/3.5/3.6 checks: ✅
- BudgetManager: injectable clock, multi-axis enforcement, reset: ✅
- RunStateMachine: 6-state lifecycle, typed transitions, terminal-state protection: ✅
- RepairLoop: 1+2 attempt lifecycle, error/benchmark handling, custom classifier: ✅
- IsolationContext: workspace verification, private data detection, directory creation: ✅
- BenchmarkRunner: full run lifecycle, dry_run, isolation failure, budget config: ✅
- BenchmarkPipeline: single/batch/dry-run modes, failure tracking: ✅
- Import isolation: benchmark.execution does not import torch/transformers: ✅
- 7 strategy implementations with ImpactStrategy protocol conformance: ✅
- StrategyRegistry with register/create/freeze/lookup: ✅
- Graph package: DependencyGraphModel, PythonImportExtractor, ImpactPropagator, ScopeReducer: ✅
- Selection package: ArtifactSelector, RegenerationPlanner: ✅
- Import isolation: benchmark.strategies, benchmark.graph, benchmark.selection do not import torch/transformers: ✅

## Kaggle Checks Pending
- Real model loading or inference
- Qwen model discovery
- GPU/torch availability
- Real benchmark runs
- Runtime metrics

## Current Branch
`fix/kaggle-smoke-v2-real-run-root` (from the `fix/kaggle-smoke-v2-finish` tail at `fc5c908`; R7C runtime commit `7a80e53`; bundle pin commit `f01b8f0`; exact correction `ffa179a` + `6d6aa36`; post-gate correction `6f88823` + `5797fc0`; HEAD `5797fc0`; R4/R5/R6 history untouched)

## Latest Commit
`chore(deploy): pin audited preflight and live gate` (5797fc0) — deployment commit of the independent post-gate correction imported via bundle fast-forward (SOURCE_COMMIT = 6f88823, DEPLOYED_BUILD_ID = 6f88823), fast-forwarded onto `5e47a1e` and pushed. The exact correction commits are `6f88823` (fix(kaggle): align repair eligibility and script bootstrap) and `5797fc0` (chore(deploy): pin audited preflight and live gate).

## Known Risks
1. **LR-3 — No test data boundary:** Test fixtures need a defined home outside `inputs/` and `src/`.
2. **LR-5 — Paper vs. implementation drift:** Must document any conflict rather than silently resolving.
3. **LR-7 — django CMS and Saleor not yet cloned locally:** Test suite runnability not verified locally beyond manifest documentation.
4. **LR-8 — Scenario content quality:** YAML files generated by automated agents; manual review recommended before Phase 4.

## Exact Next Task
1. Independent audit of the canary results (SELECTIVE_CANARY_RESULT_AUDIT_REQUIRED): verify exp-20260804-133523 truth, harness-control verification, and the harness-vs-model conclusion
2. Deliberate decision (after the audit): repeat the dedicated selective canary cell OR proceed to the full 9-record run; do not merge/tag/Pilot/fine-tune
3. Record the decision truthfully in the docs/ledgers
4. Do not tag, merge, force-push, or relaunch Kaggle before the independent result audit

## Handoff Notes
Phase 4A–4F complete, Phase 4F.1 complete, R3B/R3C/R3D closures complete, R4 token/metric contract ACCEPTED AND FROZEN at `f5ae826`, R5 nine-scripted-records ACCEPTED AND FROZEN by the independent re-audit at `7761c48` on 2026-08-01 (recorded in `docs/R5_FINAL_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md`). R6 deployment closure is **ACCEPTED AND FROZEN** by the final independent re-audit (GPT-5.6 Thinking, 2026-08-01, HEAD `949e9c2`), recorded in `docs/R6_FINAL_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md`; freeze commit `4b2dd27`; milestone branch published with upstream `origin/experiment/three-arm-smoke-v2`. Post-R6: **two real Kaggle attempts failed pre-model** — `exp-20260801-024041` and `exp-20260801-024624` (both 9 planned / 0 succeeded / 9 failed / 0 model calls; first failure = isolation). All real runtime blockers were closed under the Kaggle Runtime Blockers Fix directive (record: `selective_updates/records/KAGGLE-SMOKE-V2-RUNTIME-FIX.md`): shared-snapshot isolation root, Kaggle Qwen fail-closed `--model-path` validation + `qwen:` identity, non-zero exit on failed last run, batched truthful HF upload, `mark_completed(completed_with_failures=...)`, and notebook guardrails (`discover_model()`, `_verify_scientific_run()` in both run cells, `NabilDo/selective-regeneration-experiment-results`, `Terminal: n/9`). Fix commit `de3163f12d51c31d3f488897ed2047821da3b190`; deployment pin commit `fb60972` (bundle rebuilt via `scripts/build_upload_bundle.py`: 87 code + 56 data + 1 notebook = 144 files / 815,004 bytes; notebook 18,137 bytes). Local scripted records = 9/9; bundled CLI dry-run = 9/9; real Qwen records = 0/9; Kaggle attempts = 2 failed, preserved, not deleted. Preflight suite = 15 passed (incl. `TestKaggleBundleRuntimeGuardrails`, 6); combined unit+integration = 254 passed / 2 skipped; R7A pre-rerun hardening closed all four independently reproduced findings (record: selective_updates/records/KAGGLE-SMOKE-V2-RUNTIME-HARDENING.md): remote recovery remote_sync.json committed as recovery_uploaded (never pending; failed_local_safe on failure, failure record retained), notebook status cell reads last_sync/timestamp/remote_path/details, HF exception fixtures use httpx.Response/RuntimeError (huggingface_hub 1.x constructor compatible), current docs use the actual final gate. Full suite = 1,688 passed / 32 skipped / 0 failed. Mypy strict = 0 issues; Ruff = 0 new violations versus d9068fd. R7B Smoke Finish (record: selective_updates/records/KAGGLE-SMOKE-V2-FINISH.md) on branch `fix/kaggle-smoke-v2-finish` makes the Qwen Smoke run observable and executable: runtime commit `bff0a82` (strict single-fence JSON normalization, Qwen chat-template token counting, inference_mode + CUDA cache cleanup after every generation, one shared backend instance per process, live progress line + cross-session ETA + structured log events, dashboard artifacts under OUTPUT_DIR/dashboard allowlisted for HF recovery, smoke-only 1024 cap) and bundle pin `17207bf` (notebook pinned to `bff0a82`, live-run rewrite with _run_benchmark_live/_load_smoke_evidence/_display_smoke_dashboard/_raise_actionable_smoke_error/ScientificSmokeExecutionError/_validate_continuous_precondition and kaggle_console.log persistence). Latest real attempt = 0/9, 81 model calls, 47,694 tokens, 0 regenerated files — not scientific evidence; valid real Qwen remains 0/9; Kaggle rerun blocked pending the independent R7B audit. Full suite = 1,735 passed / 32 skipped / 0 failed; Ruff 0 new vs b6a2031 (91 = 91); Mypy strict 0 issues; builder rerun deterministic; manifest audit 0/0/0. **R7C real-run root closure complete** (record: selective_updates/records/KAGGLE-SMOKE-V2-REAL-RUN-ROOT-CLOSURE.md; branch fix/kaggle-smoke-v2-real-run-root, 7a80e53 + f01b8f0 pushed, local = remote): the attempt exp-20260801-123125 exposed FP16 OOM + dependency drift; four root contracts closed - (1) environment memory = exact pins in requirements-smoke-kaggle.lock (Django==5.2.16, djangorestframework==3.17.1, pytest==8.4.2, pytest-django==4.12.0, accelerate==1.14.0, bitsandbytes==0.49.2; torch/transformers intentionally unpinned) installed + verified in the notebook install-lock-cell (EXPECTED_RUNTIME via RUNTIME_ATTR, runtime_environment.json schema kaggle_runtime_environment.v1); (2) memory = int8 default (qwen:1:int8), PYTORCH_ALLOC_CONF=expandable_segments:True, seeded 64-token run_probe, preflight >=2.0 GiB VRAM headroom, no 4-bit fallback; (3) prompt = frozen RegenerationScenarioContext in strategy prompts with preserve-only byte-identity enforcement when expected_actions non-empty; (4) repair = FailureKind.infrastructure_nonrepairable first-failure, one execution, zero LLM repair. Preflight gate --kaggle-preflight-only (schema kaggle_smoke_preflight.v1, 6 checks; exit 0/1; no experiment/RunRecord/checkpoint/workspace/HF state) runs as a notebook gate cell before secrets + exec; notebook order = setup, install-lock, preflight, secrets, run. Bundle rebuilt (147 files / 894,735 bytes; notebook 36,351 bytes). Full suite (contract-first) = 1,451 passed / 31 skipped / 0 failed; dry-run scientific-smoke-v2 = 9/9; local preflight-only run = exit 1, 6 checks, no checkpoint/workspace; pre-existing failures confirmed identical at base fc5c908 (unit-first ordering 1, test_su0011 8, test_su0010a 9). **R7C root correction imported (independent GPT-5.6 Thinking, HEAD 6d6aa36, pushed):** the prior R7C report incorrectly called a 1,451-test subset the full suite; the true first full suite was 23 failed / 1,759 passed / 32 skipped, root cause = blanket baseline_validation => infrastructure_nonrepairable; the exact 23 former failures now pass; DRF import mapping, exact version verification, fail-fast preflight, driver-level VRAM, CPU-offload rejection, Python 3.12 contract, and stale source identity were corrected (SOURCE_COMMIT=ffa179a / DEPLOYED_BUILD_ID=ffa179a, identity test passes); current full gate = 1,790 passed / 32 skipped / 0 failed; valid real Qwen remains 0/9. Independent full-gate audit required before any Kaggle relaunch (sentinel R7C_CORRECTION_FULL_GATE_AUDIT_REQUIRED); do not tag/merge/force-push/relaunch Kaggle before that audit. Pilot not authorized. Smoke evidence is non-publication. Do not claim publication results without research-profile runs under the frozen protocol. Do not download or run LLM locally. Do not modify frozen protocol documents. Do not modify anything under `inputs/`. Canonical project root is `project/` (where `.git` lives).

Environment activation:
```bash
conda activate selective-regen-benchmark
```

Run tests:
```bash
python -m pytest -q
```

R7B_NOTEBOOK_COMPILE_REAUDIT_REQUIRED

R7C_CORRECTION_FULL_GATE_AUDIT_REQUIRED

R7C_POST_AUDIT_FULL_GATE_REQUIRED

SELECTIVE_CANARY_RESULT_AUDIT_REQUIRED
