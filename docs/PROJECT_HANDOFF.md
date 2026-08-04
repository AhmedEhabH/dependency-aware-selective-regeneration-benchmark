# Project Handoff — Dependency-Aware Selective Regeneration Benchmark

**Handoff Date:** 2026-08-01
**Prepared by:** OpenCode (engineering assistant)
**Handoff to:** Human researcher (subsequent sessions)
**Handoff type:** **QWEN 14B BNB-NF4 CANARY PREPARATION COMPLETE (2026-08-05) on branch fix/kaggle-smoke-v2-model-output-closure (Commit A `0ece665` `fix(model): add model-aware Qwen BNB quantization profiles` + Commit B `0a596b8` `chore(deploy): pin Qwen 14B NF4 selective-canary bundle`, pushed, local = remote, tree clean)** — model-aware identity `qwen:<checkpoint-basename>:<quantization>:cfg-<12hex>` replaces the frozen `qwen:1:int8` (blocks auto-resume cross-model contamination; the generic auto-resume cell had downloaded `exp-20260804-133016` because both 7B and attempted 14B were `qwen:1:int8`); explicit `bnb-nf4` profile (`load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True`, T4) with canonical modes `bnb-int8`/`bnb-nf4`/`fp16` via `--qwen-quantization`; prequantized non-bnb checkpoint fails fast (`PREQUANTIZED_CHECKPOINT_INCOMPATIBLE`) before model load, no fallback; GPTQ deferred — failed 14B GPTQ attempt `exp-20260804-195126` (0 records / 0 calls / 0 tokens, GPTQConfig + BitsAndBytesConfig conflict) preserved as engineering evidence; notebook pinned to unquantized `14b-instruct/1`, `QWEN_QUANTIZATION = "bnb-nf4"`, `RUN_GENERIC_ONE_RUN = False`, isolated `qwen14b_bnb_nf4_selective_canary` output, fail-closed canary preflight gate, no `--auto-resume-hf`, `SOURCE_COMMIT = 0ece665ef25e1b0ca3aa14f5f25977cadbd06d0c` / `DEPLOYED_BUILD_ID = 0ece665`; full suite **1,877 passed / 32 skipped / 0 failed**; Dataset PASS (27 scenarios, zero closure dataset changes); Prompt 380; Pipeline Smoke 189; Scripted dry run 9/9 exit 0; Metric Verification 169; Ruff 0 new (21 pre-existing); mypy 0 new (5 pre-existing); notebooks compile 8/8 + 8/8; bundle content-identical (147 files / 962,188 bytes), manifests verified, no cache files; **next action = Kaggle engineering preflight ONLY for the 14B bnb-nf4 profile**; record `selective_updates/records/QWEN14B-BNB-NF4-CANARY-READINESS.md`; sentinel `QWEN14B_NF4_CANARY_READINESS_AUDIT_REQUIRED` - R4 ACCEPTED AND FROZEN (explicit freeze commit f5ae826) — R5 ACCEPTED AND FROZEN (independent re-audit 2026-08-01 at 7761c48) — R6 ACCEPTED AND FROZEN (final independent re-audit 2026-08-01 at 949e9c2) — **DETERMINISTIC INTERPRETER CLOSURE (2026-08-02) on branch fix/kaggle-smoke-v2-model-output-closure (runtime commit aac9914, bundle pin 311e084, pushed, local = remote, tree clean)** — **PRE-BENCHMARK FINAL SOURCE REPIN (2026-08-03) on branch fix/kaggle-smoke-v2-model-output-closure (deployment-only correction f8d00d7 re-pins deployment to source snapshot e5d9430, pushed, local = remote, tree clean; complete clean suite green 1,834 passed / 32 skipped / 0 failed)** — branch experiment/three-arm-smoke-v2 PUBLISHED to origin (freeze commit 4b2dd27 = first publication HEAD; upstream origin/experiment/three-arm-smoke-v2; local/remote equality verified before publication-status commit); post-R6 KAGGLE RUNTIME FIX on branch fix/kaggle-smoke-v2-runtime-blockers — two real Kaggle attempts failed pre-model (exp-20260801-024041, exp-20260801-024624; both 0 model calls; preserved, not deleted), all real runtime blockers closed (fix commit de3163f) and pinned (bundle commit fb60972) with the core fix accepted by the independent runtime-fix audit, and the R7A pre-rerun hardening closed all four audit findings (hardened source d50e89e, hardened bundle 4c73db6); a further real attempt reached 81 model calls / 47,694 tokens with 0 succeeded / 0 regenerated files (0/9, not scientific evidence); R7B SMOKE FINISH on branch fix/kaggle-smoke-v2-finish (runtime commit bff0a82, bundle pin 17207bf) makes the Qwen Smoke run observable and executable, with the notebook compile correction at 4c7a0af; **R7C REAL-RUN ROOT CLOSURE on branch fix/kaggle-smoke-v2-real-run-root (runtime commit 7a80e53, bundle pin f01b8f0, pushed, local = remote)** closed the four root contracts the FP16/deps-drift attempt exp-20260801-123125 exposed: environment memory (exact pins in requirements-smoke-kaggle.lock installed + verified in the notebook), int8 memory contract (qwen:1:int8 default, PYTORCH_ALLOC_CONF, seeded probe, VRAM headroom), frozen RegenerationScenarioContext prompt contract, and FailureKind.infrastructure_nonrepairable first-failure repair contract — plus a --kaggle-preflight-only gate (kaggle_smoke_preflight.v1, 6 checks, no run side effects); the prior R7C report incorrectly called a 1,451-test subset the full suite (true first full suite = 23 failed / 1,759 passed / 32 skipped; root cause = blanket baseline_validation => infrastructure_nonrepairable); the independent GPT-5.6 Thinking correction was imported via bundle fast-forward (**ffa179a + 6d6aa36, HEAD 6d6aa36, pushed**) and the exact 23 former failures now pass, with DRF import mapping, exact version verification, fail-fast preflight, driver-level VRAM, CPU-offload rejection, Python 3.12 contract, and stale source identity (SOURCE_COMMIT=ffa179a) corrected; current full gate = 1,790 passed / 32 skipped / 0 failed; local scripted = 9/9; bundled CLI dry-run = 9/9; real Qwen = 0/9; tag not created; Pilot = NOT AUTHORIZED; independent full-gate audit required before any Kaggle relaunch; do not tag/merge/force-push/relaunch Kaggle before that audit. All reading is repository-contained; external prompt packages are historical provenance only. An independent post-gate audit on `5e47a1e` then found (a) the project-local `ImportError` was incorrectly bypassing repair (blanket marker match), (b) the bundled preflight could not import `benchmark` without ambient `PYTHONPATH`, and (c) preflight output was buffered; its exact correction was imported via bundle fast-forward (**6f88823 + 5797fc0, HEAD 5797fc0, pushed**) and now the project-local `ModuleNotFoundError` / `cannot import name` are repairable via the canonical classifier (missing declared Django + CUDA OOM stay `infrastructure_nonrepairable`), the bundled script bootstraps its own `src/`, and preflight output is streamed and persisted; notebook source identity = `SOURCE_COMMIT 6f88823` / `DEPLOYED_BUILD_ID 6f88823`; current full gate = 1,796 passed / 32 skipped / 0 failed; valid real Qwen remains 0/9; no scientific evidence exists; final independent full-gate audit required before any Kaggle relaunch, after which only the engineering preflight cell is authorized (not the scientific One-Run cell); do not tag/merge/force-push/relaunch Kaggle before that final audit. **POST-SMOKE CALIBRATION CLOSURE (2026-08-03) on branch fix/kaggle-smoke-v2-model-output-closure (HEAD 231b0a5, pushed, local = remote, tree clean)** closed four proven calibration control defects: Closure A per-attempt atomic regeneration (zero writes on any guard failure), Closure B repair no-progress detection (`repair_no_progress` early-stop on identical repair hash), Closure C fail-closed calibration continuation gate (`AUTHORIZE_CONTINUOUS_AFTER_CALIBRATION_REVIEW = False`), Closure D cooperative deadline semantics (`scientific_budget_exhausted` scientific terminal vs engineering blockers). Commits: `27c1693` (runtime + tests), `56772fe` (deployment pin, `SOURCE_COMMIT = 27c1693e22b1a68be0b299fb146d9ff1e500908b`, `DEPLOYED_BUILD_ID = 27c1693`), `231b0a5` (test-fixture reconciliation — the nine first-gate failures were stale constant-output fixtures activating the new no-progress contract, not validly proven pre-existing; all metric/count/duration/token expectations preserved; side-by-side boundary test added). Final gate: full suite = **1,849 passed / 32 skipped / 0 failed**; mypy strict Success (77 files); ruff 93 = 93 baseline (0 new); bundle content-identical (147 files / 934,495 bytes); all notebook cells compile. Calibration evidence `exp-20260803-002741` = 9 terminal records / 0 succeeded / 8 failed / 1 timed_out / 81 model calls / 118,211 tokens — **preserved, not accepted scientific evidence**; latest real calibration = 0/9; no Kaggle rerun performed; no tag; Pilot NOT authorized; next action after the independent audit is **one selective calibration canary only** (not a full relaunch, not a fine-tune, not a tag/merge). Sentinel: `POST_SMOKE_CALIBRATION_CLOSURE_AUDIT_REQUIRED`. **FINAL SELECTIVE CANARY READINESS CLOSURE (2026-08-04) on branch fix/kaggle-smoke-v2-model-output-closure (HEAD 356722b, pushed, local = remote, tree clean)** — the independent GPT-5.6 Thinking audit at `f727b3e` REJECTED canary readiness even though the full suite was green, based on three independently reproduced blockers: (1) the cooperative deadline was checked only before the whole regeneration attempt, not before every selection/generation/repair model call — direct repro: 3 model calls and false success with a 1s deadline; now every in-flight call returning beyond the deadline consumes/records its tokens, makes no next call, writes none of the staged attempt, returns the failed scientific terminal `scientific_budget_exhausted` (same guard on every internal Iterative Agent call); (2) atomic-abort `regenerated_artifact_count` was false (1 with 0 writes when an artifact was rejected) — now all staged `generated` statuses become `aborted`/`rejected`, count = 0, hashes/evidence preserved, all-valid attempts still write each file exactly once; (3) the generic one-run cell selects `monolithic` (scenario-first plan order), not `selective` — a dedicated, separately named Selective Calibration Canary cell was added (`--strategy selective --max-runs 1 --new-experiment`, isolated output `runs/selective_calibration_canary`, NO `--auto-resume-hf`, `AUTHORIZE_CONTINUOUS_AFTER_CALIBRATION_REVIEW = False`) whose `_verify_selective_canary()` asserts exactly one current-source record `todo-smoke-001 / selective`, model identity `qwen:1:int8`, model calls > 0, terminal scientific success/failure, HF `recovery_uploaded`, checkpoint 3 planned / 1 completed / 2 pending. Commits: `50ec2c1` (Commit A: per-call deadline + atomic metric truth), `28ecc5a` (Commit B: pin `SOURCE_COMMIT = 50ec2c1ca43c230aed4538be32ca7dab2ccc22e5` / `DEPLOYED_BUILD_ID = 50ec2c1`, bundle rebuilt 147 files / 948,250 bytes, canary cell added), `356722b` (test alignment: `model_call_budget_exhausted=False` on MagicMock exec_ret, r4 staged-status assertions corrected to `aborted`/`rejected`, asyncio loop fix). Full gate: **1,856 passed / 32 skipped / 0 failed**; grouped per-category 629 passed / 1 skipped; scripted dry run 9/9 exit 0 (fresh dir; default dir held a stale checkpoint); mypy strict Success (77 files); ruff 0 new; compileall clean; notebooks compile (8/8 bundle code cells); bundle content-identical. Calibration evidence `exp-20260803-002741` remains preserved, 0/9 success, not accepted scientific evidence; no Kaggle rerun; no tag; no merge; Pilot NOT authorized; **no stable release claimed**; next action = run the dedicated selective calibration canary cell ONLY after the independent re-audit (not the generic one-run cell, not the continuous cell, not a full relaunch, not a fine-tune, not a tag/merge). Sentinel: `FINAL_SELECTIVE_CANARY_READINESS_AUDIT_REQUIRED`. — **SELECTIVE CALIBRATION CANARY RESULT (2026-08-04) on branch fix/kaggle-smoke-v2-model-output-closure: dedicated canary `exp-20260804-133523` (`todo-smoke-001 / selective`, source/build `50ec2c1`) FAILED `model_output` — 4 calls / 5,804 tokens / 257.596 s / 3 selected / 2 preserved / 0 written; Qwen defects in models/serializers/views; `repair_no_progress` after a byte-identical first repair; harness safety controls verified while Qwen code quality unchanged (identical initial tokens + output hashes); incidental monolithic run `exp-20260804-133016` diagnostic only; continuous cell fail-closed (`CALIBRATION_REVIEW_REQUIRED`); accepted dedicated canary records = 1, successful = 0; full 9-record experiment NOT run; no merge/tag/Pilot/Kaggle authorized; no stable release claimed. Sentinel: `SELECTIVE_CANARY_RESULT_AUDIT_REQUIRED`.**

---

## 1. Executive Summary

The project was recovered from a broken methodology-conformance work-in-progress that overfitted selection signals to Ground Truth, broke the full test suite (36 failures), and introduced untested design complexity. All WIP changes were stashed as `broken methodology-conformance WIP 2026-07-27`. The last green baseline at commit `0a1c603` (1063 passed, 5 skipped, 0 failed) was confirmed and a new branch `experiment/three-arm-smoke-v2` was created from it.

The three-arm core experiment is now frozen:
- `full_scope_reference` (monolithic) — regenerate all eligible artifacts
- `dependency_aware_selective` (selective) — repository graph + anchor/keyword mapping
- `repository_agent` (iterative_repository_agent) — bounded LLM loop with list/read/search tools

All arms share the same LLM backend, temperature (0.0), per-call max_tokens (4096), SharedRegenerationExecutor, and isolated workspace.

## 2. Canonical Structure

```
project/
├── src/benchmark/               canonical production code
├── benchmark_data/              repositories, profiles, scenarios
│   ├── manifests/
│   ├── repository_profiles/
│   ├── repositories/todo/       pinned to b8a33e2
│   └── scenarios/               24 protocol scenarios + 3 smoke scenarios
├── tests/
│   ├── contract/                protocol and architecture contract tests
│   ├── evaluator_assets/        NOT collected by pytest; run via subprocess
│   ├── hidden_tests/            (removed — was WIP-only; does not exist on clean baseline)
│   ├── integration/
│   └── unit/
├── configs/
│   └── smoke.yaml               (valid exact V2 smoke contract, loads via load_config)
├── docs/
│   ├── FINAL_RESEARCH_PROTOCOL.md  v1.0 FROZEN
│   ├── MASTER_IMPLEMENTATION_PLAN.md
│   ├── PROJECT_HANDOFF.md
│   └── ...
├── selective_updates/
│   ├── CHANGE_INDEX.md
│   ├── metrics/change_metrics.jsonl
│   └── records/
│       ├── SCIENTIFIC-SMOKE-V1.md
│       ├── THREE-ARM-CORE-EXPERIMENT.md
│       └── ...
├── scripts/
│   └── build_upload_bundle.py
├── kaggle_upload/               mirror regenerated only via build_upload_bundle.py
├── seven_arm_benchmark.py       CLI entry point
└── pyproject.toml
```

## 3. Current State

- **Branch:** experiment/three-arm-smoke-v2
- **R1 checkpoint:** b129d42 (feat(agent): complete bounded workspace exploration)
- **R2 checkpoint:** 5057e7d (fix(selection): correct R2 selective scope)
- **R3A checkpoint:** 3eaab60 (feat(scenarios): add V2 execution metadata)
- **R3B code-checkpoint:** c11f25e (feat(validation): add deterministic migration runner)
- **R3B correction-checkpoint:** c873d9f (fix(validation): close migration runner safety gaps)
- **R3B final-correction-checkpoint:** c635e42 (fix(validation): reject unsafe migration entries and malformed execution input)
- **R3B acceptance-closure-checkpoint:** f8faa08 (fix(validation): fail on untrusted migration after-state)
- **R3B root-refactor-checkpoint:** f8f95d2 (refactor(validation): model migration execution as trusted states)
- **R3B cross-platform-freeze-checkpoint:** feb5a44 (fix(validation): close cross-platform migration snapshot contract)
- **R3B docs-checkpoint:** 8c588e6 (docs(state): record R3B completion)
- **R3B correction-docs-checkpoint:** 8c588e6
- **R3B final-correction-docs-checkpoint:** 8c588e6
- **R3B root-refactor-docs-checkpoint:** 8c588e6
- **R3B cross-platform-freeze-docs-checkpoint:** 8c588e6
- **R3C functional-checkpoint:** 47e1a05 (test(validation): close R3C freeze evidence gaps) — independently accepted by GPT-5.6 Thinking
- **R3C lint-closure-checkpoint:** 7abec68 (test(validation): close residual R3C lint debt)
- **R3D code-checkpoint:** 9e28790 (fix(validation): complete R3D scientific wiring contract)
- **R3D final-evidence-checkpoint:** 11f88f5 (fix(validation): close final R3D evidence gaps)
- **R3D docs-checkpoint:** e61eb9a (docs(state): record R3D completion pending audit)
- **R4 code-checkpoint:** e87d4ad (fix(metrics): separate per-call limits and workflow totals)
- **R4 audit-correction commits:** c928bd9 (fix(validation): pin evaluator assets to canonical LF), cc32b17 (fix(metrics): preserve exhausted workflow token budgets), a46213c (docs(audit): record R4 audit corrections)
- **R4 freeze:** f5ae826 — ACCEPTED AND FROZEN by independent re-audit (GPT-5.6 Thinking, 2026-07-31); commit `a46213c` recorded the R4 audit corrections, `f5ae826` is the explicit acceptance/freeze commit
- **R5 benchmark correction:** 8fafb50 (fix(validation): reconcile Smoke V2 baseline contracts) — pre-results amendment R5-BASELINE-CONTRACT-001, no Smoke V2 record existed
- **R5 amendment docs:** a24a9cd (docs(protocol): record pre-results Smoke V2 baseline amendment)
- **R5 execution fix:** 875e4d1 (fix(execution): preserve generated file bytes on Windows) — exactly 2 files
- **R5 test proof:** ee148fa (test(smoke): prove nine scripted production records) — exactly 3 files
- **R5 audit docs commit:** this commit (docs(audit): accept and freeze R5 production path proof) — documentation only
- **R5 acceptance/freeze:** ACCEPTED AND FROZEN by independent re-audit (GPT-5.6 Thinking, 2026-08-01) at 7761c48; recorded in docs/R5_FINAL_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md
- **R6 audited implementation HEAD:** da6ccf3 — technical implementation and bundle PASSED the independent audit (GPT-5.6 Thinking, 2026-08-01)
- **R6 test correction commit:** 40c7a47 (test(deploy): prove bundled V2 CLI execution plan) — TD-R6-ENTRYPOINT-001 closed
- **R6 documentation correction:** 949e9c2 (docs(audit): close R6 handoff truth gaps) — defects D1–D6 closed
- **R6 final independent re-audit:** ACCEPTED AND FROZEN (GPT-5.6 Thinking, 2026-08-01, HEAD 949e9c2); freeze and milestone-branch publication authorized
- **R6 freeze commit:** 4b2dd27 (docs(audit): accept and freeze R6 deployment closure) — exact first publication HEAD
- **Publication:** branch PUBLISHED to origin with upstream origin/experiment/three-arm-smoke-v2; local/remote equality verified before publication-status commit
- **HEAD:** this publication-status commit (R6 accepted and frozen; branch published)
- **Working tree:** clean
- **Canonical V2 profile source:** PROFILES["scientific-smoke-v2"] in seven_arm_benchmark.py
- **Test suite:** 1,648 passed / 32 skipped / 0 failed (final accepted R6 full suite); bundled CLI dry-run regression 9/9 at 40c7a47
- **Lint:** ruff 0 new findings vs starting HEAD 7761c48 (identical set, 94 baseline findings unchanged)
- **Types:** mypy strict 0 new errors vs starting HEAD 7761c48
- **Dependencies:** pip check clean
- **Benchmark data:** 3 repositories (todo, djangocms, saleor), 24 protocol scenarios + 3 smoke scenarios
- **Kaggle status:** NOT LAUNCHED — next after branch publication and environment preflight
- **Pilot status:** NOT AUTHORIZED
- **R4 status:** ACCEPTED AND FROZEN at f5ae826
- **R5 status:** ACCEPTED AND FROZEN at 7761c48 (nine non-dry scripted production records = 9/9)
- **R6 status:** ACCEPTED AND FROZEN at 949e9c2 (final independent re-audit 2026-08-01) — deployment closure; runtime source commit cb25e9f; deployed bundle commit 54a0462; manifest committed-tree counts 0/0/0; Todo baseline tests deployed = 47; evaluator assets deployed = 3 + 3 fingerprints; `.gitattributes` manifest-LF rule = audit-approved scope extension (disclosed in the R6 final correction ledger)
- **Bundled CLI dry-run 9/9:** proven by regression test test_bundled_cli_dry_run_executes_exact_nine_cell_plan (test commit 40c7a47) — generated CLI + bundled data execute all nine cells together (3 scenarios × 3 strategies, all succeeded, exact persisted matrix and identity)
- **Selective scopes verified:** 001=models,serializers,views | 002=models,views | 003=models,permissions,serializers,views
- **DETERMINISTIC INTERPRETER CLOSURE (2026-08-02):** runtime commit `aac9914` (fix(exec): bind Python scenario commands to active runtime) + deployment commit `311e084` (chore(deploy): pin deterministic-interpreter Smoke V2 bundle), both pushed, local=remote, working tree clean. Normalizes bare interpreter tokens (python/python.exe/python3/python3.exe, case-insensitive, no directory) to `sys.executable` at the post-generation execution boundary; scenario YAML unchanged; original command preserved in diagnostics, resolved executable recorded. Notebook SOURCE_COMMIT=`aac9914c6dcda054736539a0d0ed649cf9865128`, DEPLOYED_BUILD_ID=`aac9914`; bundle 147 files / 928,175 bytes; identity tests pass.
- **PRE-BENCHMARK FINAL REPRODUCIBILITY AUDIT CLOSURE (2026-08-03):** branch `fix/kaggle-smoke-v2-model-output-closure`. Declared the complete pre-benchmark test environment — `pyproject.toml [dev]` + `requirements-dev.txt` gain Django==5.2.16, djangorestframework==3.17.1, pytest-django==4.12.0, pytest-asyncio==1.2.0, tabulate==0.10.0, httpx==0.28.1, Jinja2==3.1.6, huggingface_hub==0.24.0, types-pyyaml, pytest (runtime `[project.dependencies]` and `requirements-smoke-kaggle.lock` untouched; commits `769d84e` + `e5d9430`); recreated the clean env from declarations only (Python 3.11.9, `_workspace\cache\prebenchmark-py311`). The previous `76a6b16` gate had **1 failure, not a green full suite** (1,833 passed / 32 skipped / 1 failed; sole failure = notebook-pin identity test, structural, reported truthfully, not forced green; root cause = dependency declarations changing `pyproject.toml` after the `aac9914`/`311e084` deployment pin; **no runtime, prompt, metric, scenario, evaluator, or data change was needed**). The exact deployment-only correction `f8d00d7` (bundle fast-forward, exactly one commit; HEAD `f8d00d7`, pushed, local=remote, tree clean) re-pins the deployment: bundled `pyproject.toml` byte-identical to canonical; notebooks re-pin SOURCE_COMMIT=e5d943065c6f4158c30a1cbbba39436ab2a7a898 / DEPLOYED_BUILD_ID=e5d9430 (deployment source snapshot = `e5d9430`; deployment correction = `f8d00d7`). Complete clean suite now **green: 1,834 passed / 32 skipped / 0 failed**; Dataset 285/5 (data unchanged); Prompt 158; Pipeline Smoke 220/12; Dry Run 9/9; Integration PASS; Metric Verification 169; mypy strict Success (77 files); ruff 93 = 93 baseline (0 new); compileall clean; all notebook cells compile; bundle build content-identical then `kaggle_upload` restored. Historical `exp-20260801-210443` produced one failed model-output terminal record under `6f88823` — preserved, excluded from the current `e5d9430` aggregation; current accepted real records = 0/9.
- **CLEAN-ENV VALIDATION (Python 3.11.9, pytest 8.4.2):** full suite **1,834 passed / 32 skipped / 0 failed**; Dataset 285/5; Prompt 158; Pipeline Smoke 220/12; Metric Verification 169; mypy strict Success (77 files); ruff clean on changed files; compileall clean; bundle idempotent; notebook valid; manifests SHA-256 verified. Bundled CLI dry-run `--profile scientific-smoke-v2` 9/9/9 (9 planned/terminal/succeeded, exit 0); source_identity 311e084/311e084.
- **First clean-env full-suite attempt** failed 5 tests due to missing optional deps (tabulate, httpx, jinja2) in the recreated environment — installed into the clean env only (tabulate>=0.9.0 required by pandas 2.3.3), no repo change; all 5 then pass. The declarations-only recreated environment now includes those deps plus the full declared set (see PRE-BENCHMARK FINAL REPRODUCIBILITY AUDIT CLOSURE above).
- **Real Qwen records:** 0/9 — no scientific evidence; tag not created; Pilot NOT AUTHORIZED; independent audit required before any Kaggle relaunch.
- **SELECTIVE CALIBRATION CANARY (2026-08-04):** dedicated canary `exp-20260804-133523` (`todo-smoke-001 / selective`, source/build `50ec2c1`) **failed `model_output`** — 4 calls / 5,804 tokens / 257.596 s / 3 selected / 2 preserved / 0 written; Qwen defects in `models.py` (`max_length=5`), `serializers.py` + `views.py` (duplicated `Priority(models.TextChoices)`); first repair byte-identical → `repair_no_progress`; atomic write wrote zero files. Harness safety controls verified; Qwen code quality unchanged (identical initial generation tokens 3,372 and output hashes vs previous selective run). Incidental monolithic `exp-20260804-133016` (6 calls / 7,927 tokens / 300.165 s / `scientific_budget_exhausted`) is diagnostic only, NOT an accepted comparison. Continuous cell correctly blocked fail-closed (`CALIBRATION_REVIEW_REQUIRED`). Accepted dedicated canary records = 1, successful = 0; full 9-record experiment NOT run; merge/tag/Pilot/Kaggle NOT authorized; no stable release claimed. Record: `selective_updates/records/SELECTIVE-CANARY-RESULTS-2026-08-04.md`. Next: independent result audit (`SELECTIVE_CANARY_RESULT_AUDIT_REQUIRED`), then a deliberate decision between repeating the canary and the full 9-record run.

## 4. Core Scientific Question

> For a given natural-language requirement change, which strategy produces a correct implementation with the fewest unnecessary modifications, lowest token consumption, and fewest model calls?

### Three Confirmatory Arms

| Role | Legacy ID | Scope Determination | Model Calls |
|------|-----------|-------------------|-------------|
| full_scope_reference | monolithic | All eligible source artifacts | 1 per artifact |
| dependency_aware_selective | selective | Repository graph + anchors + BFS | 1 per selected artifact |
| repository_agent | iterative_repository_agent | Bounded LLM loop (list/read/search) | ≤8 total |

### Shared Across All Arms

- Same LLM backend (Qwen2.5-Coder on Kaggle)
- Same temperature (0.0)
- Same per-call max_tokens (4096)
- Same SharedRegenerationExecutor for writing code
- Same validation pipeline
- Same isolated workspace

## 5. Scientific Smoke V2 Policy

| Dimension | Value |
|-----------|-------|
| Repositories | 1 (controlled Django Todo) |
| Independent changes | 3 |
| Arms | 3 |
| Repetitions | 1 |
| Total real runs | 9 |
| Execution platform | Kaggle (Qwen2.5-Coder) |
| Evidence tier | scientific_smoke_v2 (non-publication) |

### Changes

1. **todo-smoke-001** (localized) — Add Task priority with low/medium/high and default medium
2. **todo-smoke-002** (cross-layer) — Add Task soft deletion with deleted_at, restore endpoint
3. **todo-smoke-003** (cross-cutting) — Only Project owner may modify tasks in that Project

Each starts from the same clean pinned baseline (b8a33e2). They are not cumulative.

## 6. Pilot Policy

Authorized only after real Smoke V2 completes and passes independent audit.

| Criterion | Requirement |
|-----------|-------------|
| Minimum changes | 7 |
| Minimum repositories | 3 |
| Minimum LOC per repository | 5,000 |
| License | Permissive (MIT, BSD, Apache 2.0) |
| Commit | Pinned exact commit |
| Baseline | Passing reproducible test suite |

## 7. What Is Complete (may include historical items)

- Baseline recovery from 0a1c603 (1063 pass, 5 skip) — historical
- Three-arm core experiment amendment (THREE-ARM-CORE-EXPERIMENT.md) — historical
- Three smoke scenarios drafted (todo-smoke-001, 002, 003) — being corrected against baseline
- Evaluator-only test assets in tests/evaluator_assets/ (pytest-norecursed)
- Contract tests for all 13 required contracts
- All 7 historical strategy arms preserved — historical
- kaggle_upload regenerable via build_upload_bundle.py
- Caches and build artifacts excluded

## 8. What Remains

| Task | Priority | Notes |
|------|----------|-------|
| R3A — scenario execution metadata | COMPLETE | evaluator_asset, post_generation_command, require_new_migration |
| R3B — deterministic post-generation migration runner | ACCEPTED AND FROZEN at feb5a44 | Two final corrections applied: (1) lexical directory symlink rejected before resolve instead of after, (2) valid ordinary created numbered paths preserved as partial evidence when after-state untrusted; 109 focused tests + 12 symlink skipped (121 total), 1424 full suite |
| R3C — isolated scenario evaluator runner and three evaluator scripts | COMPLETE | Functional behavior independently accepted at 47e1a05 by GPT-5.6 Thinking; lint closure at 7abec68 (5 ruff violations fixed); final freeze confirmation pending this documentation audit |
| R3D — production Runner validation wiring | ACCEPTED | 1478 full suite; R4 depends on it |
| R4 — token limits and truthful workflow metrics | ACCEPTED AND FROZEN at a46213c | Independent re-audit accepted on 2026-07-31; two defects closed (exact exhaustion, evaluator LF pinning) |
| RF-3 — token/metric refactor | COMPLETE | Delivered inside R4 |
| RF-4 — full technical debt cleanup | SCHEDULED | R5 scoped RF-4 checks passed (no R5 code change required); full cleanup remains for R6 window |
| **R5 — nine non-dry scripted production records** | **CORRECTION COMPLETE — PENDING INDEPENDENT RE-AUDIT** | Nine records all succeeded; scripted engineering proof only; scope correction rebuilt the local tail without the accidental 6650b00 Kaggle bundle content; R5_SCOPE_CLEANUP_REAUDIT_REQUIRED |
| **Execute Scientific Smoke V2 on Kaggle** | HIGH | Unauthorized — blocked until R6 complete |
| Audit Smoke V2 results | HIGH | Independent verification before Pilot authorization |
| Integrate Pilot repositories | MEDIUM | ≥5K LOC, permissive license, pinned commit, passing tests |
| Run Pilot profile | MEDIUM | 7+ changes, 3+ repos, agent+selective |
| Merge to main | LOW | After successful Smoke V2 |
| Create stable tag | LOW | Only after real Smoke V2 passes and is audited |

## 9. Git State

```
Current branch:  experiment/three-arm-smoke-v2
R1 checkpoint:   b129d42 (feat(agent): complete bounded workspace exploration)
R2 checkpoint:   5057e7d (fix(selection): correct R2 selective scope)
R3A checkpoint:  3eaab60 (feat(scenarios): add V2 execution metadata)
R3B checkpoint:              c11f25e (feat(validation): add deterministic migration runner)
R3B correction:              c873d9f (fix(validation): close migration runner safety gaps)
R3B final correction:        c635e42 (fix(validation): reject unsafe migration entries and malformed execution input)
R3B acceptance closure:      f8faa08 (fix(validation): fail on untrusted migration after-state)
R3B root refactor:           f8f95d2 (refactor(validation): model migration execution as trusted states)
R3B cross-platform freeze:   feb5a44 (fix(validation): close cross-platform migration snapshot contract)
R3B docs:                    8c588e6 (docs(state): record R3B completion)
R3B acceptance docs:         8c588e6
R3B cross-platform freeze docs: 8c588e6
R3C functional:              47e1a05 (test(validation): close R3C freeze evidence gaps)
R3C lint-closure:            7abec68 (test(validation): close residual R3C lint debt)
R3D code:                    9e28790 (fix(validation): complete R3D scientific wiring contract)
R3D docs:                    e61eb9a (docs(state): record R3D completion pending audit)
R3D final evidence:          11f88f5 (fix(validation): close final R3D evidence gaps)
R4 code:                     e87d4ad (fix(metrics): separate per-call limits and workflow totals)
R4 audit corrections:        c928bd9 (.gitattributes), cc32b17 (production + tests), a46213c (docs)
R4 freeze:                   f5ae826 (ACCEPTED AND FROZEN — independent re-audit 2026-07-31)
R5 benchmark correction:     8fafb50 (fix(validation): reconcile Smoke V2 baseline contracts)
R5 amendment docs:           a24a9cd (docs(protocol): record pre-results Smoke V2 baseline amendment)
R5 execution fix:            875e4d1 (fix(execution): preserve generated file bytes on Windows) — 2 files
R5 test proof:               ee148fa (test(smoke): prove nine scripted production records) — 3 files
R5 audit docs commit:        docs(audit): accept and freeze R5 production path proof (docs only)
R6 audited HEAD:             da6ccf3 (docs(state): prepare Three-Arm Smoke V2 pre-Kaggle audit)
R6 test correction:          40c7a47 (test(deploy): prove bundled V2 CLI execution plan)
R6 documentation:            949e9c2 (docs(audit): close R6 handoff truth gaps)
R6 final re-audit:           ACCEPTED AND FROZEN at 949e9c2 (independent re-audit 2026-08-01)
R6 freeze commit:            4b2dd27 (docs(audit): accept and freeze R6 deployment closure) — first publication HEAD
Publication:          PUBLISHED — upstream origin/experiment/three-arm-smoke-v2; local/remote equality verified
HEAD:                        this publication-status commit (docs(state): record R6 milestone branch publication)
Local/remote:         equal (verified before and after publication-status commit)
Working tree:         clean
Tags:            v0.7.0-smoke-passed at 0c58250 (unchanged — historical orchestration smoke, not V2 evidence)
Stash:           broken methodology-conformance WIP 2026-07-27
Kaggle:          not launched (R6); 2 real attempts FAILED pre-model (exp-20260801-024041, exp-20260801-024624; preserved)
Runtime fix:     committed de3163f (fix(kaggle): close real Smoke runtime blockers); core accepted by independent audit
Deployment pin:  fb60972 (chore(deploy): pin corrected Scientific Smoke V2 bundle)
R7A hardening:   complete — d50e89e (fix(hf): make recovery sync state remotely truthful) + 4c73db6 (chore(deploy): pin hardened Scientific Smoke V2 rerun bundle)
Pilot:           blocked
R6:              accepted and frozen at 949e9c2 (freeze commit 4b2dd27)
README:          updated
```

> Note: the original R5 tail (6650b00, 88b6f84, c3ecad2) was rebuilt because
> `6650b00` accidentally committed 31 premature `kaggle_upload/` derivative
> files and introduced a committed notebook-manifest mismatch. The final R5
> branch contains no `kaggle_upload` diff from `f5ae826`. The pre-rebuild state
> is preserved on `backup/r5-pre-audit-c3ecad2`. See
> `selective_updates/records/R5-INDEPENDENT-AUDIT-SCOPE-CORRECTION.md` and
> `..\R5_INDEPENDENT_AUDIT_SCOPE_AND_EVIDENCE_2026-07-31.md`.

## 10. Stash Recovery

The broken WIP is stashed as `broken methodology-conformance WIP 2026-07-27` on the original branch `experiment/scientific-smoke-v1`. A patch file `broken-methodology-wip.patch` and status file `broken-methodology-wip-status.txt` were saved to the parent directory for reference. The stash contains:

- Overfitted methodology conformance tests (test_methodology_conformance.py)
- Hidden tests under tests/hidden_tests/
- Signal tuning (stop words, AST extraction, thresholds, traceability)
- Selective signal modules (builder.py, semantic.py, traceability.py)
- Class alias for IterativeRepositoryAgentStrategy

None of these should be applied without explicit authorization.

## 11. V2-01 → V2-01B — Data-Truth Corrections (2026-07-28)

### V2-01 (completed earlier)

| Item | Status |
|------|--------|
| Scenario contracts corrected against actual controlled baseline | Done |
| Profile llm_editable policy frozen | Done |
| Duplicate V2 config removed | Done |

### V2-01B (this task)

| Item | Status |
|------|--------|
| todo-smoke-003 IsProjectMember baseline behavior corrected | Done |
| TagViewSet constraint corrected | Done |
| todo.yaml artifact_catalog paths corrected (no todo_project/) | Done |
| Source descriptions corrected to actual baseline | Done |
| artifact_universe.included replaced with exact verified list | Done |
| artifact_universe.excluded replaced with policy exclusions | Done |
| Data-truth tests strengthened | Done |
| PROJECT_HANDOFF corrected to reflect dirty state | Done |

**Remaining for V2 complete:**
- Production strategies still not corrected
- Production-path scripted proof not run
- Evaluator and production-path work incomplete
- Kaggle unauthorized
- Pilot unauthorized
- No stable tag authorized
- Next task after independent approval: V2-02 Safe ArtifactUniverse

**Scope:** Data-contract-only task. No strategies, Runner, Pipeline, LLM backends,
checkpointing, notebooks, or Kaggle execution were modified. Do not claim Smoke
readiness after this task.

## 12. Getting Started

```bash
# Activate environment
conda activate selective-regen-benchmark

# Verify baseline
python -m pytest -q

# Check current state
git log --oneline -3
git status

# Run focused Selective tests
python -m pytest tests/unit/selection/test_dependency_scope.py -v

# Verify three verified scopes
python -c "
from tests.unit.selection.test_dependency_scope import *
for n, s in [('001',SCENARIO_001),('002',SCENARIO_002),('003',SCENARIO_003)]:
    print(f'Scenario {n}: {select_dependency_scope(s, FIVE_UNIVERSE, DESCRIPTORS, TODO_GRAPH)}')
"

# Dry-run with canonical profile
python seven_arm_benchmark.py --dry-run

# Rebuild Kaggle bundle (not yet authorized)
# python scripts/build_upload_bundle.py
```

---

## 14. R3C Status — Isolated Scenario Evaluator System

**[HISTORICAL — superseded. Sections 14–19 record completed R3C/R3D/R4/R5 phases. The authoritative current state is sections 1–3, 20, and 21. Statements such as "R5 in progress" or "R6 blocked" in these historical sections do NOT describe current execution.]**

**Status:** R3C FREEZE CLOSURE — DOCUMENTATION CLOSURE AUDIT REQUIRED
**Code checkpoints:** `47e1a05` (functional acceptance), `7abec68` (lint closure)
**Date:** 2026-07-30

### What was built

- `src/benchmark/execution/scenario_evaluator.py` — four-state evaluator (validation, trust, subprocess, payload parsing) with typed result objects
- `tests/support/evaluator_fixture_workspaces.py` — three fixture workspace builders; calls `run_post_generation_command`; one-fault variants derived from correct sources (626 lines)
- `tests/evaluator_assets/todo_smoke_001_checks.py` (10 checks), `_002` (9 checks), `_003` (10 checks) — all use identical fail-closed JSON structure
- `tests/integration/test_todo_smoke_evaluator_assets.py` (20 tests: 12 real subprocess runs + 8 integrity including baseline hashes, migration integrity, source isolation)
- `tests/unit/execution/test_scenario_evaluator.py` (57 tests: public-path truth table, symlink/workspace-leak rejection, subprocess exception coverage, isolation cleanup)

### Closure specifics (2026-07-30)

- TOCTOU tests now validate first, mutate second, then trust-load — proving the validate→mutate→trust transition
- Inode-based regular-file replacement test removed; replaced by content-frozen-at-trust-time proof
- Smoke 003 permission proof now invokes every configured permission class via `SimpleNamespace` and `TaskViewSet()`, not just checks class membership
- Source-isolation Boolean logic corrected: buggy `not exists() or not is_symlink()` replaced with `_assert_workspace_has_no_evaluator_assets` helper using AND logic
- 6 fake-Django lifecycle tests (3 assets × 2 failure modes) persist the setup/teardown JSON contract
- Evaluator hash tests are now read-only: metadata required to exist, never written
- Code/docs commit separation enforced: `test(validation)` commit contains code/tests only

### Quality gates

- Full suite: 1424 passed, 32 skipped, 0 failed
- Ruff: 0 errors (5 pre-existing violations in test_scenario_evaluator.py closed in lint-closure commit)
- R3B frozen files untouched
- R3C functional behavior independently accepted by GPT-5.6 Thinking at code checkpoint 47e1a05
- R3C lint debt closed (5 violations: 1 F841, 3 SIM117, 1 E501)
- Git tree: clean (after docs commit)

### Blocked

- R3D: FINAL FREEZE CANDIDATE — code committed (11f88f5); independent audit pending
- RF-2: part of R3D correction; complete
- RF-3: scheduled after R4
- RF-4: scheduled after R5
- Kaggle/Pilot/merge/tag: BLOCKED

---

## 15. R3D Status — Production Runner Validation Wiring

**Status:** R3D FINAL FREEZE CANDIDATE — INDEPENDENT AUDIT REQUIRED
**Code checkpoints:** `9e28790` (root correction), `11f88f5` (final evidence closure)
**Date:** 2026-07-31

### What was built

- **`_validate_scientific_configuration`** — preflight check for canonical_project_root, python_executable, evaluator_asset, validation_command before any model call
- **`_execute_scientific_validation`** — orchestrates post-generation migration, baseline validation, and scenario evaluator; returns `_ScientificValidationResult` with per-stage bounded outputs
- **`_scientific_record_fields`** — maps validation result to RunRecord dict; gracefully handles None
- **`_failure_from_scientific_result`** — converts failed result into FailureRecord with correct stage/kind
- **`_scientific_feedback_channels`** — produces (exit_code, stdout, stderr) bounded at 1000 chars per channel; evaluator branch includes stderr + error + public check names
- **`_is_repairable_failure`** — gating: migration, evaluator, and generation_guard are repairable; pre-flight/config failures are not
- **RF-2 deduplication** — single enforcement point in `_validate_scientific_configuration`; pre-flight and late duplicate checks removed from seven_arm_benchmark.py and runner.py
- **`selection_tool_transcript`** — preserved in both success/failure return paths and reporting serializer

### RF-2 (Orchestration Deduplication)

Single enforcement point: `_validate_scientific_configuration` in runner.py. Pre-flight `validation_command` check removed from `seven_arm_benchmark.py`. Duplicate late checks removed from `_run_regeneration_flow` and `_run_iterative_flow`.

### Final evidence closure (11f88f5)

- Evaluator stderr channel: constructed from `evaluator.stderr`, `evaluator.error`, and `checks`; bounded at 1000 chars; no evaluator source, Ground Truth, or hidden descriptions
- 7 public-path tests replace 5 prior nominal tests: entry config, monolithic migration repair, selective evaluator repair, agent evaluator revision + transcript, feedback channel content, duration aggregation, record round-trip
- Truthful Git-derived report at `reports/latest_phase_report.md` (2269 words)

### Quality gates

- Full suite: 1478 passed, 32 skipped, 0 failed
- 54 focused R3D wiring tests (7 public-path, 18 private-helper, 7 persistence, 1 reporting)
- Ruff: 0 errors on changed files
- Mypy strict: 0 errors on changed production files
- Compileall: all OK
- Git tree: clean
- Commit separation: code (9e28790) → docs (e61eb9a) → final evidence (11f88f5)

### Blocked

- R3D freeze: blocks R4 (truthful metrics), R5 (nine local records), R6 (bundle and push), Kaggle execution, Pilot

---

## 16. R4 Status — Token Limits and Truthful Workflow Metrics

**Status:** R4 ACCEPTED AND FROZEN — independent re-audit by GPT-5.6 Thinking on 2026-07-31 accepted the audit corrections and froze R4 for progression to R5
**Starting HEAD:** `b8724cc`
**Code commit:** `e87d4ad` — `fix(metrics): separate per-call limits and workflow totals`
**Audit-correction commits:** `c928bd9` — `fix(validation): pin evaluator assets to canonical LF`; `cc32b17` — `fix(metrics): preserve exhausted workflow token budgets`
**Freeze HEAD:** `f5ae826` (explicit acceptance/freeze commit; `a46213c` recorded the audit corrections)
**Date:** 2026-07-31

### What was built

- **Single allowance resolver** — `budgets.resolve_completion_allowance(*, max_completion_tokens_per_call, remaining_total_workflow_tokens, prompt_tokens)`; zero total → per-call limit; otherwise `max(0, min(per_call, remaining − prompt))`.
- **Frozen conflict rule at every constructor** — `PipelineConfig`, `RunnerConfig`, `ExecutionConfig`: both zero → unlimited; one positive → it; both positive equal → it; both positive different → constructor-time `ValueError`.
- **Stage-split truthful metrics** — `_WorkflowMetricAccumulator` tracks selection / initial regeneration / repair / migration / baseline / evaluator separately; `total_workflow_*` equals the exact stage sum; `repair_attempts` increments once per repair executor call.
- **Executor/Agent limit separation** — executor `SharedRegenerationExecutor.execute(..., max_completion_tokens_per_call, remaining_total_workflow_tokens)`; agent `analyze_impact`/`revise_plan` use explicit per-call + remaining-total; `MAX_AGENT_CALLS = 8`.
- **Resolved total forwarded everywhere** — `seven_arm_benchmark.py` `record_dict` carries `max_completion_tokens_per_call`/`max_total_workflow_tokens`; `_to_run_record_data` forwards them plus `max_attempts` into `model_metadata`; survives JSONL reload and report.
- **Real test evidence** — `test_r4_token_and_metrics.py` (66 tests), `test_r4_metric_contract.py` (31 tests); zero `assert True`.

### Audit corrections (2026-07-31)

- **Defect A** — exact workflow-budget exhaustion reopened an exhausted budget as unlimited because `0` was overloaded as both "no limit" and "exhausted". Fixed by `budgets.runtime_remaining_total_tokens` (`None` = unlimited, `0` = exhausted, positive = remaining) and `int | None` semantics in `resolve_completion_allowance`, executor, and agent, with `has_limit` accounting guards; all five Runner call sites forward the runtime allowance. Five-group exact-exhaustion regression + integration production-path tests added.
- **Defect B** — evaluator integrity was platform-dependent: committed `.sha256` are canonical LF but Windows checkout produced CRLF. `.gitattributes` pins `tests/evaluator_assets/todo_smoke_*_checks.py` to `text eol=lf`; worktree rewritten to canonical LF, SHA-256 still matches the committed `.sha256`, index/worktree byte-identical.

### Quality gates

- 9.1 R4 unit: 66 passed; 9.2 R4 integration: 31 passed; 9.3 R3D-adjacent: 177 passed; 9.4 evaluator integrity: 50 passed, 1 pre-existing skip
- Full suite: 1576 passed, 32 skipped, 0 failed
- Ruff: 0 new errors (pre-existing tracked-file findings verified vs HEAD worktree)
- Mypy --strict: 0 new errors (10 pre-existing in seven_arm_benchmark.py, verified vs HEAD worktree)
- Compileall: exit 0; `git diff --check`: clean
- Direct scripts A/B/C1/C2/D all met §7 acceptance; Script D showed 2048/9000 at all five boundaries
- Code commit `e87d4ad`: 21 files, 3052 insertions, 307 deletions (14 production + 7 tests)

### Audit-correction gates (2026-07-31)

- R4 unit: 72 passed; R4 integration: 33 passed; R3D-adjacent (r3d_wiring + repair): 62 passed; evaluator integrity: 50 passed, 1 pre-existing skip; full suite: 1584 passed, 32 skipped, 0 failed
- Ruff: 88 findings = baseline `ccdb49c` (0 new); Mypy --strict on the 4 changed production files: 0 errors; compileall: exit 0; `git diff --check`: clean
- Defect B proven: worktree SHA-256 matches committed `.sha256` for all three evaluator files; index/worktree blobs byte-identical; zero CR bytes; `git ls-files --eol` shows `i/lf w/lf`

### Freeze (2026-07-31)

The independent re-audit accepted R4 at the explicit acceptance/freeze commit `f5ae826`. See `docs/R4_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md`.

### Blocked

- R5 freeze: blocks R6 (bundle and push), Kaggle execution, Pilot. R6 remains blocked pending R5 completion and independent audit.
- R5 is in progress; R6 is blocked. **[HISTORICAL/SUPERSEDED — R5 was accepted and frozen at 7761c48 on 2026-08-01; R6 was accepted and frozen by the final independent re-audit at 949e9c2 on 2026-08-01. See sections 20 and 21.]**

---

**R4_ACCEPTED_R5_SCOPE_CORRECTION_REAUDIT_REQUIRED**

---

## 17. R5 Baseline-Contract Amendment — R5-BASELINE-CONTRACT-001

**Status:** AMENDED AND COMMITTED — R5 RESUMED
**Correction commit:** `8fafb50` — `fix(validation): reconcile Smoke V2 baseline contracts`
**Date:** 2026-07-31

### Trigger

An independent blocker audit (`..\R5_BLOCKER_INDEPENDENT_AUDIT_2026-07-31.md`)
confirmed a data contract contradiction between the frozen baseline regression
assertions and the three frozen Smoke V2 scenarios. R5 was blocked at Step 2
(the first Monolithic cell) at `baseline_validation`. No Smoke V2 record
existed, so the correction is pre-results. Full scope, gate order, and final
marker are defined in `..\OPENCODE_R5_CONTRACT_CORRECTION_AND_RESUME_DIRECTIVE.md`.

### What changed (7 files, production = NONE, scenario YAML = NONE)

- `test_serializers.py`: ProjectSerializer/TaskSerializer field assertions are
  now baseline-field preservation; TagSerializer stays exact.
- `test_views.py`: common project created through the authenticated Project API;
  unowned-task forbidden test creates its project via another user's API client;
  exact HTTP 403 preserved.
- `evaluator_fixture_workspaces.py`: smoke-002 correct-source keys exactly
  `todo/models.py` + `todo/views.py`.
- `todo_smoke_002_checks.py` + `.sha256`: removed only the unstated
  `deleted_at`-response-field loop; canonical LF SHA-256 recomputed.
- `test_todo_smoke_evaluator_assets.py`: three-scenario correct-fixture
  compatibility gate (`test_correct_fixture_passes_baseline_and_evaluator_*`).
- `repository_versions.yaml`: Todo notes record the amendment; pinned SHA unchanged.

### Evidence

- Baseline repository suite: 47 passed.
- Compatibility gate: 3 scenarios passed (baseline + evaluator + one migration +
  unchanged old migrations + exact changed-source paths + unchanged baseline tests
  + no evaluator assets in workspace).
- Complete evaluator suite: 53 passed, 1 pre-existing skip.
- Full suite: 1598 passed, 32 skipped, 0 failed.
- R5 status = RESUMED; R6/Kaggle/push/tag = BLOCKED.

Record: `selective_updates/records/R5-BASELINE-CONTRACT-AMENDMENT.md`.

---

## 18. R5 Scope Correction and Evidence Tightening (2026-07-31)

**Status:** CORRECTION COMPLETE — PENDING INDEPENDENT RE-AUDIT
**Audit source:** `..\R5_INDEPENDENT_AUDIT_SCOPE_AND_EVIDENCE_2026-07-31.md`
**Directive source:** `..\OPENCODE_R5_SCOPE_CLEANUP_DIRECTIVE.md`
**Backup branch:** `backup/r5-pre-audit-c3ecad2` (preserved until re-audit)

An independent audit found the original R5 tail acceptable in production
behavior but mis-scoped in git history: commit `6650b00` claimed one execution
fix while also committing 31 premature `kaggle_upload/` files, introducing a
committed notebook-manifest mismatch. Because the branch had no upstream, the
local R5 tail was rebuilt cleanly:

- `8fafb50` and `a24a9cd` preserved untouched.
- `875e4d1` — rewritten execution fix (exactly 2 files).
- `ee148fa` — rewritten R5 test proof (exactly 3 files).
- This commit — R5 audit documentation only.
- No `kaggle_upload/` change from `f5ae826`; no bundle rebuild; no README
  change; no push; no tag.

Three evidence boundaries were tightened: exact selected/generated path and
count assertions for all nine cells (`generation_paths_requested`,
`selected_artifact_count`, `regeneration_model_calls`,
`regenerated_artifact_count`, `preserved_artifact_count`); the snapshot
mutation control now proves an accepted-hash → mutated-hash transition
(`snapshot_hash_before != snapshot_hash_after`, `record.status == failed`);
and persisted timestamps are captured immediately before/after the real
pipeline run (`started_at <= ended_at`, timezone-aware, all nine records).
Negative-control documentation was corrected: dry-run and no-regeneration are
valid guarded no-op modes; no-new-migration is a failed validation control;
the remaining failure controls fail at their exact intended stage.

The Git-tree bundle-manifest issue is recorded as R6 debt
`TD-R6-BUNDLE-MANIFEST-001` and was not fixed inside R5
(`scripts/build_upload_bundle.py` was not modified). The Git-tree manifest
mismatch counts are reported in
`selective_updates/records/R5-INDEPENDENT-AUDIT-SCOPE-CORRECTION.md`.

Next action: R6 deployment closure under the corrected directive
(`..\R6_OpenCode_Package_CORRECTED\02_OPENCODE_R6_CORRECTED_EXECUTION_DIRECTIVE.md`),
then an independent R6 audit before push. Kaggle, push, tag, merge, and Pilot
remain BLOCKED.

## 19. R5 Acceptance and R6 Authorization (2026-08-01)

**Status:** R5 ACCEPTED AND FROZEN — R6 AUTHORIZED AND IN PROGRESS
**Audit source:** `..\R5_FINAL_INDEPENDENT_REAUDIT_ACCEPTANCE_2026-08-01.md`
**Directive source:** `..\R6_OpenCode_Package_CORRECTED\02_OPENCODE_R6_CORRECTED_EXECUTION_DIRECTIVE.md` (supersedes every earlier R6 directive)
**Backup branch:** `backup/r6-pre-execution-7761c48` (created 2026-08-01; no tag)

The independent re-audit accepted and froze R5 at `7761c48` on 2026-08-01.
Local scripted Smoke V2 evidence = 9/9 records succeeded, 0 failed. Real Qwen
records = 0/9. The R6 corrected plan closes the deployment gaps found by the
audit (TD-R6-BUNDLE-MANIFEST-001, missing controlled Todo tests, missing
evaluator assets, V1 notebook/smoke config, and future-hash identity rules)
with a deterministic builder, an exact evaluator allowlist, controlled Todo
test deployment, a valid V2 smoke config, a pinned notebook, a bundle
preflight integration, and committed-byte manifest parity audits. R6 does not
modify production Runner, strategies, metrics, regeneration, evaluator
behavior, frozen scenarios, evaluator assets, or controlled Todo source/tests.

## 20. R6 Deployment Closure (2026-08-01)

**Status:** R6 ACCEPTED AND FROZEN — FINAL INDEPENDENT RE-AUDIT 2026-08-01 AT 949e9c2
**Record:** `selective_updates/records/R6-BUNDLE-PARITY-AND-PRE-KAGGLE-HANDOFF.md`
**Audit record:** `docs/R6_INDEPENDENT_AUDIT_AND_CORRECTION_REPORT.md`
**Freeze record:** `docs/R6_FINAL_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md`

R6 executed the corrected deployment directive in one bounded pass:
Commit A `5784a4f` recorded R5 acceptance; Commit B `cb25e9f` is the runtime
source commit; Commit C `54a0462` pinned and built the Scientific Smoke V2
bundle. Worktree/index/committed-tree manifest audits are all 0/0/0
mismatches. Todo baseline tests deployed = exact five files / 47 methods;
evaluator assets deployed = 3 + 3 fingerprints; tests/support = 0;
scripted/harness = 0. Bundle totals = 144 files / 805,634 bytes.

```text
R4 accepted/frozen
R5 accepted/frozen
R6 ACCEPTED AND FROZEN at 949e9c2 (freeze commit 4b2dd27)
local scripted = 9/9
bundled CLI dry-run = 9/9
real Qwen = 0/9
Kaggle not launched
push PUBLISHED (upstream set, local/remote equal)
tag not created
Pilot not authorized
```

Pilot wording: exact final run denominator not frozen; minimum 7–12 changes
across at least 3 real repositories; current descriptive 48-run config is not
authorization. Final accepted full suite at R6 closure: 1,648 passed, 32
skipped, 0 failed. Ruff set identical to starting HEAD (94 findings, zero new);
mypy strict 0 errors; compileall clean; final builder run left the tree clean.

Next action: Kaggle environment preflight, then nine real Qwen Smoke records.
Do not tag, merge, force-push, or launch Kaggle now.

## 21. R6 Final Audit Correction (2026-08-01)

**Status:** ACCEPTED AND FROZEN — FINAL INDEPENDENT RE-AUDIT 2026-08-01 AT 949e9c2
**Audit source:** `..\R6_Final_Audit_Correction_Package\01_R6_INDEPENDENT_AUDIT.md`
**Directive source:** `..\R6_Final_Audit_Correction_Package\02_OPENCODE_R6_FINAL_CORRECTION_DIRECTIVE.md`
**Backup branch:** `backup/r6-pre-final-audit-da6ccf3` (created 2026-08-01; no tag)

The independent audit (GPT-5.6 Thinking, 2026-08-01, audited HEAD `da6ccf3`)
passed the R6 code and bundle technically (manifest mismatches 0/0/0, canonical
parity 0, builder rerun 0, exact evaluator assets, exact Todo tests, sensitive
scan 0; 70 focused tests passed; full suite 1,647 passed). R6 freeze was
withheld only for one missing deployed-entrypoint regression (TD-R6-ENTRYPOINT-001)
and documentation-truth defects D1–D6. The bounded correction pass closed both:

- Test commit `40c7a47` — `test(deploy): prove bundled V2 CLI execution plan`
  adds `test_bundled_cli_dry_run_executes_exact_nine_cell_plan` to
  `tests/integration/test_kaggle_bundle_smoke_v2_preflight.py`. It runs the
  real generated CLI (`kaggle_upload/code/seven_arm_benchmark.py`) with the
  bundled data and asserts return code 0, the three exact output lines, an
  unchanged working tree, and the exact persisted matrix: 9 succeeded records,
  exact scenario × strategy Cartesian product, checkpoint identity
  (total_planned=9, total_completed=9, completion_status=completed, exact
  source/build identity), source_identity truth, and per-strategy summary
  counts. TD-R6-ENTRYPOINT-001 = closed.
- Documentation commit `949e9c2` — `docs(audit): close R6 handoff
  truth gaps` closes D1–D6 across README.md, SYSTEM_STATE.md,
  docs/START_HERE.md, docs/MASTER_IMPLEMENTATION_PLAN.md, docs/PROJECT_HANDOFF.md,
  reports/latest_phase_report.md, docs/R6_INDEPENDENT_AUDIT_AND_CORRECTION_REPORT.md,
  selective_updates/records/R6-BUNDLE-PARITY-AND-PRE-KAGGLE-HANDOFF.md,
  selective_updates/records/TECHNICAL-DEBT-AND-REFACTOR-SCHEDULE.md,
  selective_updates/CHANGE_INDEX.md, selective_updates/metrics/change_metrics.jsonl.

Scope discipline: no production, builder, bundle, notebook, config, scenario,
evaluator, or R5 change. `.gitattributes` manifest-LF rule is an audit-approved
scope extension and is disclosed in the final ledger. The final independent
re-audit (GPT-5.6 Thinking, 2026-08-01, HEAD `949e9c2`) **accepted R6** and
authorized freeze and milestone-branch publication (recorded in
`docs/R6_FINAL_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md`). The R6 freeze commit
`4b2dd27` (docs(audit): accept and freeze R6 deployment closure) is the exact
first publication HEAD; the branch was published to origin with upstream
`origin/experiment/three-arm-smoke-v2` and local/remote equality was verified.
Continuation does not require any external prompt package; the earlier audit
and correction packages are historical provenance only. Next action is
unambiguous: **record the publication status, push again, verify final
equality, then Kaggle environment preflight.** Do not tag, merge, force-push,
or run Kaggle now.

## 22. Post-R6 Kaggle Runtime Fix (2026-08-01)

**Status:** FIXES APPLIED AND COMMITTED — INDEPENDENT RUNTIME-FIX AUDIT REQUIRED
**Branch:** `fix/kaggle-smoke-v2-runtime-blockers` (from R6-published `experiment/three-arm-smoke-v2` @ `9ff3c4e`)
**Directive:** `..\Kaggle_Runtime_Blockers_Fix_Package\02_OPENCODE_KAGGLE_RUNTIME_FIX_DIRECTIVE.md`
**Evidence audit:** `..\Kaggle_Runtime_Blockers_Fix_Package\01_KAGGLE_TWO_RUNS_INDEPENDENT_AUDIT.md`
**Record:** `selective_updates/records/KAGGLE-SMOKE-V2-RUNTIME-FIX.md`

Two real Kaggle Scientific Smoke V2 runs launched from the published R6
deployment failed completely before any model call:
`exp-20260801-024041` and `exp-20260801-024624` (both 9 planned / 0 succeeded /
9 failed / 0 model calls / 0 tokens; first failure = workspace isolation).
These outputs remain visible on the results dataset and must NOT be deleted.

The real runtime blockers were closed under the Kaggle Runtime Blockers Fix
directive and pinned into a corrected bundle:

- **Runtime fix commit `de3163f`** (`fix(kaggle): close real Smoke runtime blockers`, 8 files):
  shared-snapshot isolation root (`make_isolation(..., snapshot_storage_root)` →
  `IsolationContext(snapshot_base=...)`), Kaggle Qwen fail-closed `--model-path`
  validation + `qwen:` identity, `_decide_session_exit_code` (failed last run →
  exit 1), batched HF upload (`_upload_batch_with_retry`/`CommitOperationAdd`/
  `create_commit`) with truthful booleans, `mark_completed(completed_with_failures=...)`.
- **Deployment pin commit `fb60972`** (`chore(deploy): pin corrected Scientific Smoke V2 bundle`, 8 files):
  notebook pinned to `de3163f12d51c31d3f488897ed2047821da3b190`, fail-closed
  `discover_model()`, `_verify_scientific_run()` in both run cells,
  `NabilDo/selective-regeneration-experiment-results`, `Terminal: n/9`
  vocabulary, continuous-cell markdown guard; bundle rebuilt via
  `scripts/build_upload_bundle.py` (144 files / 815,004 bytes; notebook 18,137 bytes).
- **R7A hardened source `d50e89e`** (`fix(hf): make recovery sync state remotely truthful`):
  `upload_recovery()` writes `remote_sync.json` as `last_sync = recovery_uploaded`
  before `create_commit` and commits that exact file in the same recovery commit
  (one `create_commit`); on success local = committed; on failure local
  overwritten to `failed_local_safe` with the real remote path + error, failure
  record retained, `False` returned. Remote never holds `pending`. Added
  `TestHfRecoveryStateTruth` (5 tests); HF exception fixtures version-compatible
  (`httpx.Request` + `httpx.Response(404, request=request)` /
  `RuntimeError`).
- **R7A hardened bundle `4c73db6`** (`chore(deploy): pin hardened Scientific Smoke V2 rerun bundle`):
  notebook status cell reads `last_sync`/`timestamp`/`remote_path`/`details`
  schema; bundle rebuilt via `scripts/build_upload_bundle.py`
  (144 files / 815,779 bytes; notebook 18,262 bytes); added
  `test_notebook_sync_display_uses_current_schema`.

Test evidence: preflight = 15 passed (incl. `TestKaggleBundleRuntimeGuardrails`,
6); last full suite = 1,688 passed / 32 skipped / 0 failed. Ruff 0 new versus
`d9068fd` (baseline 91, current 91); Mypy strict 0 issues; compileall clean;
`git diff --check` clean; builder rerun leaves tree unchanged; worktree/index/HEAD
manifests: code 87 / data 56 / notebook 1 — 0 mismatches.

Next action: independent re-audit of the R7A pre-rerun hardening
(R7A_HARDENING_REAUDIT_REQUIRED). Do not relaunch Kaggle, tag, merge, or
force-push before that re-audit passes.

## 23. R7B Smoke Finish — Observable and Executable Qwen Smoke (2026-08-01)

**Status:** IMPLEMENTATION COMPLETE — INDEPENDENT R7B AUDIT REQUIRED
**Branch:** `fix/kaggle-smoke-v2-finish` (from the post-R6 runtime-blockers tail)
**Directive:** `..\R7B_SMOKE_FINISH_PACKAGE\07_R7B_RESUME_TO_COMPLETION_DIRECTIVE.md`
**Record:** `selective_updates/records/KAGGLE-SMOKE-V2-FINISH.md`

### Truth

```text
latest real attempt    = 0/9, 81 model calls, 47,694 tokens, 0 regenerated files
scientific evidence    = NONE (not scientific evidence)
R7B implementation     = complete, pending independent audit
valid real Qwen        = 0/9
Kaggle rerun           = BLOCKED until the independent audit passes
```

### What changed

- **Strict output normalization** — new `src/benchmark/llm/output_normalization.py`:
  single-fenced JSON object extraction with regex fallback when `ast.parse`
  fails; empty/partial responses fail closed.
- **Kaggle Qwen backend** — Qwen chat-template token counting, deterministic
  single-`json.loads` parsing, `inference_mode()` + best-effort CUDA cache
  cleanup after every generation (success, OOM, other-exception), one shared
  backend instance per process (single model initialization).
- **Progress + cross-session ETA** — `_render_progress_line` per run;
  `_estimate_run_eta` from the persisted ledger; `RUN`/`STAGE`/`REGEN`/`HF`
  structured log events in `seven_arm_benchmark.py`.
- **Deterministic dashboard** — `write_dashboard_artifacts` in
  `checkpoint/reports.py` writes `dashboard_summary.json`, `run_matrix.csv`,
  `strategy_summary.csv`, `failure_summary.csv` under `OUTPUT_DIR/dashboard`;
  HF recovery allowlist + recovery-dir mkdir in `checkpoint/hf_sync.py`.
- **Smoke-only cap** — `configs/smoke.yaml` now
  `max_completion_tokens_per_call: 1024` (Pilot/Research untouched).
- **Notebook rewrite** — live subprocess streaming (`_run_benchmark_live`),
  evidence loading (`_load_smoke_evidence`), dashboard display
  (`_display_smoke_dashboard`), actionable failure error
  (`_raise_actionable_smoke_error` + `ScientificSmokeExecutionError`),
  continuous precondition (`_validate_continuous_precondition`),
  `kaggle_console.log` persistence, executable `max-runs 1` exec cell + guarded
  continuous cell.

### Commits

```text
A = bff0a82  fix(kaggle): make Qwen Smoke observable and executable
             (runtime/config + directly related tests; 16 files, +1483/−46)
B = 17207bf  chore(deploy): pin final observable Smoke V2 bundle
             (notebook pinned to bff0a82, bundle rebuilt, test_cli notebook
             assertions; 14 files, +2199/−685)
```

Both pushed to `origin/fix/kaggle-smoke-v2-finish`; local/remote equality
verified after each push.

### Gates

```text
Focused set (directive §7)      all passed (unit + integration 100, cli/builder/preflight 91)
Full suite (final gate, §10)    1,790 passed / 32 skipped / 0 failed
Ruff                            0 new vs a4e9186 except ARG004 (identity-locked; inherent to reviewed commit)
Mypy --strict src/benchmark     0 issues
Compileall                      clean
Builder rerun                   no content diff (deterministic; only CRLF warnings)
git diff --check                clean
git status --short              clean
Identity test                   SOURCE_COMMIT=ffa179a, DEPLOYED_BUILD_ID=ffa179a passes
```

Next action: independent full-gate audit of the corrected R7C branch (HEAD
`6d6aa36`, R7C_CORRECTION_FULL_GATE_AUDIT_REQUIRED). Kaggle rerun remains
blocked until that audit passes. No tag, no merge, no force-push, no Kaggle
relaunch.

## 24. R7C Real-Run Root Closure — Environment Memory + Prompt Contracts (2026-08-01)

**Status:** IMPLEMENTATION COMPLETE + TWO CORRECTIONS IMPORTED — FINAL FULL-GATE AUDIT REQUIRED
**Branch:** `fix/kaggle-smoke-v2-real-run-root` (from the `fix/kaggle-smoke-v2-finish` tail at `fc5c908`)
**HEAD:** `5797fc0` (correction `ffa179a` + `6d6aa36` fast-forwarded onto `a4e9186`; post-gate correction `6f88823` + `5797fc0` fast-forwarded onto `5e47a1e`; pushed)
**Directive:** `..\R7C_REAL_RUN_ROOT_CLOSURE_PACKAGE\02_OPENCODE_R7C_ROOT_CLOSURE_DIRECTIVE.md`
**Record:** `selective_updates/records/KAGGLE-SMOKE-V2-REAL-RUN-ROOT-CLOSURE.md`

### Truth

```text
latest real attempt    = exp-20260801-123125 (FP16 → OOM; deps drifted from lock)
scientific evidence    = NONE (not scientific evidence)
R7C implementation     = complete, committed, pushed; exact correction imported
                         (ffa179a + 6d6aa36); post-gate correction imported (6f88823 + 5797fc0)
root contracts         = environment memory + prompt contracts closed
preflight gate         = kaggle_smoke_preflight.v1 (6 checks; exit 0/1; no run side effects)
local scripted         = 9/9 (dry-run scientific-smoke-v2)
true first full suite  = 23 failed / 1,759 passed / 32 skipped (corrected full gate)
full suite after fix   = 1,790 passed / 32 skipped / 0 failed (Windows / Python 3.11.5)
full suite after post-gate fix = 1,796 passed / 32 skipped / 0 failed (Windows / Python 3.11.5)
Kaggle relaunch        = BLOCKED until the final independent full-gate audit passes
```

### Correction of prior R7C full-gate truth

The prior R7C report incorrectly called a **1,451-test subset the full suite**.
The true first full suite was **23 failed / 1,759 passed / 32 skipped**. The
root cause of the 23 failures was the blanket
`baseline_validation => infrastructure_nonrepairable` classification in
`src/benchmark/execution/runner.py`, which classified every normal baseline
test failure as infrastructure so the repair loop never ran. An independent
GPT-5.6 Thinking audit implemented and tested the exact correction as two
commits (`ffa179a` + `6d6aa36`) imported via bundle fast-forward. The exact 23
former failures now pass. Also corrected: DRF import mapping
(`djangorestframework` distribution → `rest_framework` module), exact version
verification, fail-fast preflight, driver-level VRAM (`torch.cuda.mem_get_info()`),
CPU/disk-offload rejection, Python 3.12 runtime contract, and stale source
identity (`SOURCE_COMMIT = ffa179a`, `DEPLOYED_BUILD_ID = ffa179a`). Valid real
Qwen remains **0/9**; Kaggle remains **blocked** pending the final full-gate
audit.

### Post-gate independent audit (on `5e47a1e`)

An independent post-gate audit on `5e47a1e` found three remaining issues and
its exact correction was imported via bundle fast-forward as `6f88823`
(fix(kaggle): align repair eligibility and script bootstrap) + `5797fc0`
(chore(deploy): pin audited preflight and live gate):

- **Project-local `ImportError` incorrectly bypassed repair.** The prior
  blanket marker match in `_is_repairable_failure` returned False for any
  `modulenotfounderror`/`cannot import name`/`importerror` message, so a
  project-local missing module was classified infrastructure instead of being
  repaired. The blanket match is replaced by the canonical
  `classify_validation_repairability` classifier: project-local
  `ModuleNotFoundError` and `cannot import name` are **repairable**, while a
  missing declared Django dependency and CUDA OOM remain
  `infrastructure_nonrepairable`.
- **Bundled preflight could not import `benchmark` without ambient
  `PYTHONPATH`.** The bundled `seven_arm_benchmark.py` now bootstraps its own
  `src/` onto `sys.path` at startup, so the deployed CLI reaches its preflight
  gate in a clean subprocess (proven by the new
  `test_bundled_cli_bootstraps_src_without_ambient_pythonpath` regression).
- **Preflight output was buffered.** The preflight gate now streams and
  persists its output (`preflight_streams_with_deployed_pythonpath`), rather
  than buffering it invisibly.

Notebook source identity is now `SOURCE_COMMIT = 6f88823` /
`DEPLOYED_BUILD_ID = 6f88823`.

### What changed

- **Environment memory — exact runtime pins** — new
  `requirements-smoke-kaggle.lock`: Django==5.2.16, djangorestframework==3.17.1,
  pytest==8.4.2, pytest-django==4.12.0, accelerate==1.14.0,
  bitsandbytes==0.49.2. torch/transformers intentionally unpinned (Kaggle image
  provides them). The notebook `install-lock-cell` installs the lock first,
  verifies `EXPECTED_RUNTIME` via `RUNTIME_ATTR`, and writes
  `runtime_environment.json` (schema `kaggle_runtime_environment.v1`) under
  `OUTPUT_DIR.parent/"environment"`.
- **Memory contract — int8 default** — `qwen:1:int8` model identity;
  `PYTORCH_ALLOC_CONF=expandable_segments:True`; `run_probe` seeded
  `torch.manual_seed(0)` for 64 tokens; preflight enforces ≥2.0 GiB VRAM
  headroom after a real int8 load. No 4-bit fallback.
- **Prompt contract — frozen scenario context** — `RegenerationScenarioContext`
  (repo identity, change, expected actions, blast radius, integrity rules)
  frozen into strategy prompts; preserve-only byte-identity enforcement when
  `expected_actions` is non-empty.
- **Repair contract — infrastructure-aware classification** —
  `FailureKind.infrastructure_nonrepairable` on first failure: one execution,
  zero LLM repair attempts; the post-gate correction routes eligibility through
  the canonical `classify_validation_repairability` classifier.
- **Preflight gate** — new `src/benchmark/execution/preflight.py` +
  `--kaggle-preflight-only`: exit 0/1, no experiment/RunRecord/checkpoint/
  workspace/HF state; 6 checks (dependency table, baseline staging, `manage.py
  check`, `makemigrations --check`, real int8 load, VRAM headroom). Notebook
  gate cell before the exec cell; `secrets-cell` moved after preflight; output
  streamed and persisted.
- **Notebook order** — setup → install-lock → preflight → secrets → run
  (7 code cells, all `ast.parse` clean).

### Commits

```text
A = 7a80e53  fix(kaggle): close environment memory and prompt contracts
             (lock, deps, CLI, preflight, int8 backend, runner classification,
             scenario context, tests)
B = f01b8f0  chore(deploy): pin preflighted int8 Smoke V2 bundle
             (notebook install-lock + preflight gate + secrets reorder,
              bundle rebuilt; 147 files / 894,735 bytes; notebook 36,351 bytes)
C = a4e9186  (previous R7C HEAD — published but broken)
D = ffa179a  fix(kaggle): correct repair and preflight contracts (independent audit)
E = 6d6aa36  chore(deploy): pin corrected R7C preflight bundle (ffa179a/ffa179a)
F = 5e47a1e  docs(audit): correct R7C full-gate and deployment truth (audit baseline)
G = 6f88823  fix(kaggle): align repair eligibility and script bootstrap (post-gate audit)
H = 5797fc0  chore(deploy): pin audited preflight and live gate (6f88823/6f88823)
```

All pushed to `origin/fix/kaggle-smoke-v2-real-run-root`; local/remote
equality verified after each push. Current HEAD = `5797fc0`.

### Gates

```text
Changed-file diagnostics        git diff --check clean (CRLF warnings only)
Ruff on changed files            clean except ARG004 (identity-locked; see record)
                                 and 5 pre-existing seven_arm_benchmark.py findings
                                 (ARG001 x2, E501, SIM102, SIM113) — all reproduced at
                                 5e47a1e with the same rule/file (lines shifted +6 by
                                 the added SRC_ROOT bootstrap block)
Mypy --strict src/benchmark      0 issues
Compileall                       clean
Notebook cells                   canonical + generated 7/7 code cells compile
Regression gates                 4 (runner eligibility) + 1 (bootstrap) + 2 (cli) = 7 passed
Focused gates                    runner 45; cli+builder 84; r4 33; su0010a 61;
                                 su0011 25; bundle preflight 25; production-path 41
Full suite (final gate)          contract-first 1,451 was a SUBSET; true first full suite
                                 23 failed / 1,759 passed / 32 skipped;
                                 after correction 1,790 passed / 32 skipped / 0 failed;
                                 after post-gate correction 1,796 passed / 32 skipped / 0 failed
Dry-run                          scientific-smoke-v2 9/9 succeeded
Preflight-only (local, fake model) exit 1, 6 checks, no checkpoint/workspace
Builder rerun                    content-identical (byte-hash equal; CRLF warnings only)
Bundle manifests                 verified OK (code / data / notebook)
```

Pre-existing failures confirmed identical at base `fc5c908` (worktree checks):
unit-first ordering → 1 asyncio event-loop failure; `test_su0011` → 8;
`test_su0010a` → 9. Canonical order `tests/contract tests/unit` passes.

Next action: final independent full-gate audit of the corrected R7C branch
(HEAD `5797fc0`) — repair eligibility, bundled clean-subprocess preflight
bootstrap, preflight live streaming, boundary regressions, and the complete
full suite
(R7C_POST_AUDIT_FULL_GATE_REQUIRED). After that audit passes, the only
authorized Kaggle action is the engineering preflight cell — not the
scientific One-Run cell. Kaggle relaunch remains blocked until that final
audit passes. No tag, no merge, no force-push, no Kaggle relaunch.

## 25. Pre-Benchmark Final Reproducibility Audit Closure (2026-08-03)

**Status:** DEPLOYMENT CORRECTION APPLIED AND PUSHED — COMPLETE CLEAN SUITE GREEN
**Branch:** `fix/kaggle-smoke-v2-model-output-closure`
**HEAD:** `f8d00d7` (pushed; local = remote; working tree clean)
**Deployment correction:** `f8d00d7` (chore(deploy): repin reproducible pre-benchmark source snapshot)
**Deployment source snapshot:** `e5d9430` (SOURCE_COMMIT=e5d943065c6f4158c30a1cbbba39436ab2a7a898, DEPLOYED_BUILD_ID=e5d9430)
**Runtime commit:** `aac9914` (fix(exec): bind Python scenario commands to active runtime)
**Deployment pin:** `311e084` (chore(deploy): pin deterministic-interpreter Smoke V2 bundle)
**Declaration commits:** `769d84e` + `e5d9430` (dependency declarations only)
**Record:** `selective_updates/records/KAGGLE-SMOKE-V2-MODEL-OUTPUT-CLOSURE.md`

### Truth

```text
branch                    = fix/kaggle-smoke-v2-model-output-closure
HEAD                      = f8d00d7 (pushed; local = remote; tree clean)
deployment correction     = f8d00d7  chore(deploy): repin reproducible pre-benchmark source snapshot
deployment source         = e5d9430 (SOURCE_COMMIT = e5d943065c6f4158c30a1cbbba39436ab2a7a898;
                                     DEPLOYED_BUILD_ID = e5d9430)
runtime commit            = aac9914   deployment pin = 311e084
declaration commits       = 769d84e + e5d9430
previous 76a6b16 gate     = 1,833 passed / 32 skipped / 1 failed (NOT a green full suite;
                            structural notebook-pin identity test, truthful, not forced green;
                            root cause = dependency declarations changing pyproject.toml after
                            the aac9914/311e084 deployment pin; no runtime/prompt/metric/
                            scenario/evaluator/data change needed)
historical experiment     = exp-20260801-210443 produced ONE failed model-output
                            terminal record under source 6f88823 — preserved,
                            excluded from the current e5d9430 aggregation
current real records      = 0/9 (no accepted real records; no scientific evidence)
tag                       = not created   Pilot = not authorized   Kaggle = not launched
```

### What changed

1. **Step 1 — exact versions recovered** from the previously passing
   environment: tabulate 0.10.0, httpx 0.28.1, Jinja2 3.1.6, pytest 8.4.2,
   ruff 0.15.22, mypy 1.20.2.
2. **Step 2 — complete dependency declarations.** `pyproject.toml [dev]` +
   `requirements-dev.txt` now declare the full pre-benchmark test environment
   (Django==5.2.16, djangorestframework==3.17.1, pytest-django==4.12.0,
   pytest-asyncio==1.2.0, tabulate==0.10.0, httpx==0.28.1, Jinja2==3.1.6,
   huggingface_hub==0.24.0, types-pyyaml, pytest>=8.0,<9). Runtime
   `[project.dependencies]` and `requirements-smoke-kaggle.lock` untouched.
3. **Step 3 — environment recreated from declarations only** (Python 3.11.9,
   `_workspace\cache\prebenchmark-py311`).
4. **Step 4 — complete clean gate repeated** on the recreated environment.
   The previous 76a6b16 gate recorded the truthful **1,833 passed / 32 skipped /
   1 failed** (structural notebook-pin identity test, not forced green).
5. **Step 5 — deployment-only correction applied.** The exact independently
   reviewed correction f8d00d7 (bundle fast-forward, exactly one commit) re-pins
   the deployment: bundled pyproject.toml byte-identical to canonical, notebooks
   re-pin SOURCE_COMMIT=e5d943065c6f4158c30a1cbbba39436ab2a7a898 /
   DEPLOYED_BUILD_ID=e5d9430; the complete clean suite is now **green: 1,834 passed
   / 32 skipped / 0 failed**. No runtime, prompt, metric, scenario, evaluator, or
   data change was needed.
6. **Step 6 — operational documentation corrected** (this handoff + the record
   + state docs + ledger).

### Gates (on the declarations-only recreated environment)

```text
Previous 76a6b16 gate = 1,833 passed / 32 skipped / 1 failed (NOT green)
                        (sole failure = test_notebook_source_commit_matches_deployed_runtime_tree,
                         structural: the mandated pyproject.toml declaration change breaks
                         byte-identity with the pinned aac9914 SOURCE_COMMIT; frozen artifacts
                         not modified to force green — reported truthfully;
                         root cause = dependency declarations changing pyproject.toml after the
                         aac9914/311e084 deployment pin; no runtime/prompt/metric/scenario/
                         evaluator/data change needed)
Complete clean suite  = 1,834 passed / 32 skipped / 0 failed (GREEN, after f8d00d7)
Dataset Validation    = 285 passed / 5 skipped (PASS); benchmark data unchanged
Prompt Validation     = 158 passed (PASS)
Pipeline Smoke        = 220 passed / 12 skipped (PASS)
Dry Run               = scientific-smoke-v2 9/9 succeeded, exit 0 (PASS)
Integration           = PASS
Metric Verification   = 169 passed (PASS)
Mypy --strict src/benchmark = Success: no issues found in 77 source files
Ruff                  = 93 findings = 76a6b16 baseline (re-exported and re-run; 93 = 93), 0 new
Compileall            = clean
Notebook cells        = all compile (canonical 7/7 + generated 7/7)
Bundle build          = success: 147 files / 928,329 bytes; content-identical; manifests verified; no cache files
git diff --check      = clean
git status            = clean
```

The deployment-only correction `f8d00d7` (imported via bundle fast-forward, exactly
one commit) re-pins the deployment to the current source snapshot `e5d9430`; the
previously failing identity test now passes. Next action after this independent
audit: update the Kaggle code dataset + notebook to the corrected `e5d9430`
deployment, then run the Kaggle **engineering preflight** cell only (not the
scientific One-Run cell). Do not relaunch Kaggle, tag, merge, or force-push
beyond that documented preflight step.
