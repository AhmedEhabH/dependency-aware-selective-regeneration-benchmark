# AGENTS.md — Dependency-Aware Selective Regeneration Benchmark

## Project facts

- **Language:** Python 3.11
- **Source:** `src/benchmark/`
- **Entry:** `seven_arm_benchmark.py`
- **Tests:** Pytest (test suite under `tests/`)
- **Lint:** Ruff (pyproject.toml config)
- **Types:** Mypy strict (`pyproject.toml`)
- **Kaggle:** generated code under `kaggle_upload/code/`
- **Bundle:** `scripts/build_upload_bundle.py`
- **Docs:** `docs/`
- **Updates:** ledgers under `selective_updates/`

## Working rule

inspect minimally → edit narrowly → changed-file diagnostics → affected tests → full validation only at final gate

## Context rules

Start with:
```
git status --short
git diff --stat
git diff --name-only
```

Use exact searches before reading whole files. Read only:
- changed files
- related symbols
- directly affected tests
- necessary configuration (pyproject.toml)

Do not read entire repository, generated code (unless verifying derivatives), datasets, large logs, or unrelated documentation.

## Release facts

> **CURRENT TRUTH (2026-09-03, v0.9.22 D13r1 CANARY LAUNCH-READINESS FINALIZER
> CLOSURE (PILOT-EXEC-01) — F1 SEMANTIC EXECUTABILITY WIRED INTO THE REAL
> PILOT/PILOT-CANARY PRE-MODEL LAUNCH PATH + F2 MIGRATION METADATA ON THE 3
> CANARY SCENARIOS + F3 MIGRATION EXECUTION DECOUPLED FROM EVALUATOR_ASSET +
> F4 EXACT-PATCH REPAIR-PROMPT CONTRADICTION REMOVED + F5 EXACT_PATCH +
> AGENT-CONTROL-CAP IN FROZEN CONFIG/PROVENANCE IDENTITY; D13r1 CANDIDATE
> `v0.9.22-d13r1-candidate` BUILT + PROVENANCE-VERIFIED FROZEN;
> NOT A RELEASE; NO STABLE TAG MOVE):** branch
> `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure`. D13r1 FINALIZES
> canary launch-readiness on top of D13 WITHOUT touching any scientific input
> (model Qwen2.5-Coder-14B-Instruct, BNB-NF4, sdpa `flash_or_efficient_no_math`,
> GQA `repeat_kv_sm75`, 12 scenarios, 3 repo pins, 2 strategies, 2 reps = 48
> cells, prompts, Ground Truth, metrics, timeout 1200). F1 the fail-closed
> semantic-executability gate is now WIRED into the real pilot/pilot-canary
> PRE-MODEL launch path: `validate_pilot_launch_authorization` runs it when a
> `scenario_dir` is supplied, new
> `validate_pilot_semantic_executability` (scenario_dir + repository_roots),
> the canary cell gates the 3 canary scenarios BEFORE any model call, and the
> CLI `--require-launch-authorization` passes `scenario_dir`/`scenario_ids` —
> the FULL 48-cell Pilot is **NOT a launch basis** while any of its scenarios is
> semantically unexecutable (saleor-loc-002 `is_featured` known-absent; 7
> unregistered scenarios fail closed). F2 per-repo `migration_directory`
> metadata added ONLY to the 3 canary scenarios (todo-loc-001
> `todo/migrations`, saleor-loc-001 `saleor/product/migrations`,
> djangocms-cross-007 `cms/migrations`). F3 migration execution decoupled from
> `evaluator_asset`: a migration-only scenario (post_generation_command /
> require_new_migration without evaluator_asset) is a VALID configuration.
> F4 the exact-patch repair-prompt contradiction removed (repair context no
> longer instructs complete-file regeneration in patch mode). F5 `exact_patch`
> + `agent_control_max_completion_tokens` in the frozen config/provenance
> identity (source_identity.json, bundle identity, notebook `FROZEN_DEPLOYMENT`
> `{exact_patch: True, agent_control_max_completion_tokens: 512}`, configs/
> pilot.yaml) and ENFORCED by the dry-run + canary evidence validators.
> Production-shape tests: 60k/85k short-patch, repair-prompt exact-patch
> contract (F4), semantic pre-model gate + launch-auth wiring (F1), 3-repo
> migrations (F2/F3). Full suite **2650 passed / 34 skipped / 0 failed**;
> six gates GREEN: G1 dataset 333/4, G2 prompt 132/4, G3 pipeline smoke 930/23,
> G4 source pilot 48/48 + source canary 6/6 (canonical validator PASS), G6
> metrics 194, G5 full suite 2650/34/0, plus exact-artifact dry-runs Pilot
> **48/48** + pilot-canary **6/6** (repos 2/2/2, strategies 3/3, rep 1:6, 0
> calls/tokens, protocol 1.2, exact_patch True, agent_control 512) and the
> bundled exact CANARY SEMANTIC PRE-MODEL GATE **PASS** on the 3 canary
> scenarios. **D13r1 candidate artifact `v0.9.22-d13r1-candidate` built +
> provenance-verified FROZEN** (`--verify-source-provenance`, **0 mismatches**,
> idempotent same-input rerun archive SHA unchanged): source commit
> `6bc946a…`; archive SHA-256
> **`9f120412cfef5dfb7f66a57c03380fc5149b45b20d53c60d623d1e81bc203461`**
> (+ sidecar verified); freeze report
> `reports/pilot_notebook_trust_freeze_d13r1.json`; FROZEN_PROTOCOL_VERSION
> `1.2`; notebook `FROZEN_DEPLOYMENT.protocol_version: "1.2"`,
> `exact_patch: True`, `agent_control_max_completion_tokens: 512`;
> FROZEN_MANIFEST_HASHES freshly computed (code `dce4b81b…`, data `6e085b2b…`,
> repo-snapshot `5b53af9c…`, transport `07036a36…`). The next REAL Pilot launch
> requires a real pilot-canary pass on this or a fresh exact candidate with its
> own tag decision. The retired `v0.9.22-pilot-exec-ready` tag (peel
> `478261ff…`) and the `edae1b7e…8c4a` artifact are NOT reused; the D13
> candidate (`v0.9.22-d13-candidate`, archive `6edd487a…`) is SUPERSEDED by
> this D13r1 candidate. Never resume `exp-20260828-151335` (zero accepted
> RunRecords); `exp-20260830-134232` remains REJECTED (48/48 terminal
> failures). Report:
> `reports/V0922_D13R1_CANARY_LAUNCH_READINESS_CLOSURE_REPORT.md`.
>
> **PRIOR TRUTH (2026-09-03, SUPERSEDED by the D13r1 canary-launch-readiness
> closure — v0.9.22 D13 CANARY PRODUCTION-SCALE EXECUTION
> FIX CLOSURE (PILOT-EXEC-01) — B1 EXACT-PATCH + B2 AGENT-CONTROL CAP +
> B3 REPO-AWARE MIGRATIONS + B4 SEMANTIC EXECUTABILITY GATE + PROTOCOL 1.2;
> D13 CANDIDATE `v0.9.22-d13-candidate` BUILT + PROVENANCE-VERIFIED FROZEN;
> NOT A RELEASE; NO STABLE TAG MOVE; D12 CANDIDATE SUPERSEDED):** branch
> `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure`. D13 closes
> root-cause blockers exposed by the 2026-09-02 real pilot-canary (6/6 failed):
> B1 exact-patch source editing (`exact_patch.py`, 19 tests), B2 configurable
> agent-control cap (`AGENT_CONTROL_MAX_COMPLETION_TOKENS=512`, 6 tests), B3
> repository-aware migrations (`ScenarioModel.migration_directory`,
> `_normalize_interpreter_command`, 12 tests), B4 semantic executability gate
> (`semantic_executability.py`, 6 tests, standalone not wired into validator),
> protocol Pilot-only 1.1→1.2, event-loop robustness fix, metric-contract test
> fix. NOTHING scientific changed (model Qwen2.5-Coder-14B-Instruct, BNB-NF4,
> sdpa `flash_or_efficient_no_math`, GQA `repeat_kv_sm75`, 12 scenarios, 3 repo
> pins, 2 strategies, 2 reps = 48 cells, prompts, Ground Truth, metrics, timeout
> 1200). **D13 candidate artifact `v0.9.22-d13-candidate` was built +
> provenance-verified FROZEN** (`--verify-source-provenance`, 0 mismatches):
> source commit `88605f4…`; archive SHA-256
> **`6edd487a853c7bd1cf7eabb788f3fa3b4492dfe96bf0272d04ac6bb3eb34bfdd`**
> (+ sidecar verified); FROZEN_PROTOCOL_VERSION `1.2`; notebook
> `FROZEN_DEPLOYMENT.protocol_version: "1.2"`, `FROZEN_MANIFEST_HASHES`
> freshly computed (code `371d75…`, data `f95656…`, repo-snapshot `5b53af…`,
> transport `07036a…`); full suite **2630 passed / 33 skipped / 0 failed**
> (D12 was 2589/33/0; +41 = B1 19 + B2 4 + B3 12 + B4 6). Six validation
> gates PASS: G1 dataset 267 passed / 4 skipped, G2 prompt 101/4, G3 pipeline
> smoke 722/14, G4 dry-runs (source pilot 48/48 + source canary 6/6 +
> exact-artifact pilot 48/48 + exact-artifact canary 6/6, protocol 1.2, 0 model
> calls, 0 tokens, canonical `validate_pilot_dryrun_evidence` PASS), G5
> integration 258 passed, G6 metrics 329 passed / 10 skipped.
> Exact-artifact dry-runs (bundled code/data, protocol 1.2, every record +
> `source_identity.json` == `88605f4…` + `v0.9.22-d13-candidate` + build
> `88605f4`): Pilot **48/48** (repos 16/16/16, strategies 24/24, reps
> {1:24,2:24}, 0 calls/tokens, agent_control_max_completion_tokens 512) and
> pilot-canary **6/6** (repos 2/2/2, strategies 3/3, rep 1:6, 0 calls/tokens).
> This candidate is **NOT** a launch basis: the next REAL Pilot launch requires
> a real pilot-canary pass on this or a fresh exact candidate with its own tag
> decision. The retired `v0.9.22-pilot-exec-ready` tag (peel `478261ff…`) and
> the `edae1b7e…8c4a` artifact are NOT reused; the D12 candidate
> (`v0.9.22-d12-candidate`, archive `812d3755…`) is SUPERSEDED by this D13
> candidate. Never resume `exp-20260828-151335` (zero accepted RunRecords);
> `exp-20260830-134232` remains REJECTED (48/48 terminal failures). Report:
> `reports/V0922_D13_CANARY_PRODUCTION_SCALE_EXECUTION_CLOSURE_REPORT.md`.
>
> **PRIOR TRUTH (2026-09-01, SUPERSEDED by the D12 notebook-orchestration fix
> closure — v0.9.22 D11 PRE-PILOT VIABILITY GATE CLOSURE
> (PILOT-EXEC-01) — PILOT CANARY TOPOLOGY MADE SALEOR-INCLUSIVE 6-CELL
> (todo/djangocms/saleor), PROTOCOL-PROFILE RESOLUTION SEPARATED PLOT-CANARY
> 1.1 FROM OTHER PROFILES 1.0, VALIDATION MANIFEST PROTOCOL PARITY RESTORED,
> EXECUTABLE CANARY INTEGRATION COVERAGE ADDED, D11 CANDIDATE
> `v0.9.22-d11-candidate` BUILT + PROVENANCE-VERIFIED FROZEN; NOT A RELEASE;
> NO STABLE TAG MOVE):** branch
> `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure`. D11 (B1–B4)
> corrects the pilot-canary operational topology WITHOUT touching any
> scientific input (model Qwen2.5-Coder-14B-Instruct, BNB-NF4, sdpa
> `flash_or_efficient_no_math`, GQA `repeat_kv_sm75`, 12 scenarios, 3 repo pins
> Todo/django CMS/Saleor, 2 strategies, 2 reps = 48 cells): B1 the
> `pilot-canary` profile now represents ALL THREE Pilot repos as a 6-cell matrix
> (3 canary scenarios `todo-loc-001`/`djangocms-cross-007`/`saleor-loc-001`, 2
> strategies, 1 rep) and the fix for the contradictory `blast_radii` filter that
> dropped `djangocms-cross-007` (cross_cutting) and made the canary uncallable;
> `validate_pilot_canary_evidence` defaults are 3-repo / 6-cell with 2/2/2 repo
> counts (was internally 1-repo / 1-cell in D10's default path); B2 the
> `--protocol-version` CLI default is now profile-derived via
> `resolve_profile_protocol` (pilot/pilot-canary → 1.1; smoke/research/
> scientific-smoke-v1/v2 → 1.0; explicit `--protocol-version` always overrides
> — fixes the pre-D11 bug where the CLI default 1.1 leaked into dry-run and
> other profiles); B3 `benchmark_data/manifests/pilot_validation_commands.yaml`
> `protocol_version` 1.0 → 1.1 to mirror `configs/pilot.yaml` (parity enforced
> by new tests); B4 a new executable integration test invokes the actual CLI in
> dry-run mode against canonical scenario data and proves the six-cell
> saleor-inclusive canary topology. The D11 candidate artifact
> `v0.9.22-d11-candidate` was built + **provenance-verified FROZEN**
> (`--verify-source-provenance`, 0 mismatches): builds `b07da1a` (code) →
> `c1c892b` (notebook anchor refresh + freeze report) → `224c5a9`
> (provenance-verified freeze report); archive SHA-256
> **`4554dced6a438893ed01cbdbce9756613c0b0951459a43eb9a4a467edee4cb8a`**
> (+ sidecar verified) from source commit `c1c892b…`; full suite **2585 passed
> / 33 skipped / 0 failed**; exact-artifact dry-runs with the bundled code/data/
> notebook: Pilot **48/48** (repos 16/16/16, strategies 24/24, reps {1:24,2:24},
> 0 model calls, 0 tokens, protocol 1.1, canonical `validate_pilot_dryrun_evidence`
> PASS) and pilot-canary **6/6** (repos 2/2/2, strategies 3/3, rep 1:6, 0 model
> calls, 0 tokens, protocol 1.1). This candidate is **NOT** a launch basis: the
> next REAL Pilot launch requires a real pilot-canary pass on this or a fresh
> exact candidate with its own tag decision. The retired
> `v0.9.22-pilot-exec-ready` tag (peel `478261ff…`) and the `edae1b7e…8c4a`
> artifact are NOT reused; the D10 candidate (`v0.9.22-d10-candidate`, archive
> `d468ee63…`) is SUPERSEDED by D11. Never resume `exp-20260828-151335` (zero
> accepted RunRecords); `exp-20260830-134232` remains REJECTED (48/48 terminal
> failures). Report: `reports/V0922_D11_PILOT_CANARY_SALEOR_INCLUSIVE_CLOSURE_REPORT.md`;
> freeze `reports/pilot_notebook_trust_freeze.json`.

> **PRIOR TRUTH (2026-08-31, SUPERSEDED by the D11 saleor-inclusive canary
> closure — v0.9.22 D10 ALL-FAILED PILOT VIABILITY CLOSURE
> (PILOT-EXEC-01) — REAL 48-CELL PILOT `exp-20260830-134232` FINISHED 48/48
> TERMINAL FAILURES (0 SUCCEEDED, 0 EVALUATOR-PASSED) AND IS REJECTED; STABLE
> ANNOTATED TAG `v0.9.22-pilot-exec-ready` UNCHANGED BUT RETIRED AS A LAUNCH
> CANDIDATE; INTERNAL RUNTIME CONTRACT CORRECTED (PROTOCOL 1.1, TIMEOUT 1200,
> PILOT-CANARY GATE, STANDALONE FAIL-CLOSED RESUME, TERMINALITY/VIABILITY
> SPLIT); NO REAL PILOT LAUNCH AND NO TAG MOVE IN THIS CLOSURE):**
> branch `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure`. The one
> permitted real 48-cell Pilot launched from the exact D9.6 artifact
> `edae1b7e5be7ebab642d1e3c068dda3842a8061b8b04ab84c027d43a38dc8c4a` (source
> commit `478261ff595d3d64ed9d5bab32d1cc90d7dabd77`, tag
> `v0.9.22-pilot-exec-ready`) on 2026-08-30 completed with **48/48 terminal
> failures / 0 succeeded / 0 evaluator-passed** (`exp-20260830-134232`;
> protocol 1.0; config hash `4b5bbcb2abcf62af`; ~23,610 s; 293 model calls;
> 731,678 prompt + 88,953 completion = 820,631 total tokens; classifications
> `scientific_budget_exhausted`=33, `model_output`=8, `build`=7; 33 runs killed
> at the 600 s workflow deadline; iterative agent ran out to "no paths
> selected" on several Saleor/djangoCMS/Todo scenarios). It is REJECTED and
> preserved verbatim, never resumed or counted. The stable annotated tag
> `v0.9.22-pilot-exec-ready` **still exists and still peels to `478261ff...`**
> — it is NOT deleted/moved/re-forced, but it is **retired as a launch
> candidate** (the only permitted launch from that artifact was 100%-failed).
> Scientific version remains v0.9.22 (never v0.9.23); scientific inputs
> unchanged (model Qwen2.5-Coder-14B-Instruct, BNB-NF4, sdpa
> `flash_or_efficient_no_math`, GQA `repeat_kv_sm75`, 12 scenarios, 3 repo pins
> Todo/django CMS/Saleor, 2 strategies, 2 reps = 48 cells, prompts, Ground
> Truth, metrics, max attempts 3, completion cap 4096, 12000/64 gate). D10
> (D10.1–D10.7) corrects the internal runtime/operability contract WITHOUT
> touching scientific inputs: D10.1 truth-only report+docs+commit+push (this
> closure); D10.2 internal contract correction `protocol_version 1.0 → 1.1`
> and Pilot profile `timeout_seconds 600 → 1200` uniformly for BOTH strategies
> (the 600 s ceiling censored 33/48 runs; selective mean was 540 s with zero
> headroom); D10.3 a real end-to-end pilot-canary mode + canonical fail-closed
> `validate_pilot_canary_evidence` gate (a genuinely small real run that still
> exercises select→regenerate→repair→validate, not a no-op) wired as a notebook
> stage before the full 48; D10.4 the resume cell made standalone
> (`PILOT_OUTPUT_DIR` recomputed independently — the D9.6 resume cell raised
> `NameError: name 'PILOT_OUTPUT_DIR' is not defined` when run standalone) and
> fail-closed against rejected experiment IDs; D10.5 validator separates
> terminality (did the pipeline finish) from scientific viability (is the
> result accepted) so deadline-censored / no-path-selection runs are not
> masked as generic terminal failures; D10.6 all fixes driven tests-first
> (RED then GREEN); D10.7 freeze, docs, push, verified
> `project-2026-08-31-*.zip` export, Stop Report. The next REAL Pilot launch
> requires a NEW freshly-finalized artifact (protocol 1.1, 1200 s, corrected
> resume + terminality/viability) with its own real pilot-canary pass and its
> own tag decision — the retired `v0.9.22-pilot-exec-ready` tag and the
> `edae1b7e…8c4a` artifact are NOT reused as a launch basis. Report:
> `reports/V0922_D10_ALL_FAILED_PILOT_VIABILITY_CLOSURE_REPORT.md`.

> **PRIOR TRUTH (2026-08-30, SUPERSEDED by the D10 all-failed relaunch closure
> — v0.9.22 D9.6 REAL 2×T4 PASS + STABLE-TAG
> CLOSURE (PILOT-EXEC-01) — REAL EXACT-ARTIFACT 2×T4 PREFLIGHT PASSED ON
> 2026-08-30; STABLE ANNOTATED TAG EXISTS AND PEELS TO `478261ff...`; REAL
> PILOT NOT STARTED):** branch
> `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure`. Independent
> audit of the exact D9.6 artifact `edae1b7e5be7ebab642d1e3c068dda3842a8061b8b04ab84c027d43a38dc8c4a`
> (source commit `478261ff595d3d64ed9d5bab32d1cc90d7dabd77`, source tag
> `v0.9.22-pilot-exec-ready`) real 2×T4 Kaggle evidence PASSED every Gate B
> requirement: the expanded-mode sidecar proof matches the artifact SHA; the
> deployment identity uses `478261ff...` / `v0.9.22-pilot-exec-ready` /
> 48 cells / Qwen 14B / BNB-NF4 and all five code/data/repository/notebook/
> transport manifest hashes recompute and match; repository preflight
> `overall == PASS` with Todo, django CMS, Saleor all PASS and Saleor
> PostgreSQL + Valkey/Redis reachable; the T4 SDPA GQA microprobe passes on
> both `cuda:0` and `cuda:1` (Tesla T4 compute capability 7.5, Q/K/V + output
> on the intended device, `repeat_kv_sm75`); `model_preflight.json.passed ==
> true` with exactly 2 Tesla T4, `model_identity ==
> qwen:14b-instruct-v1:bnb-nf4:cfg-cc9474140d25`, requested/effective attention
> `sdpa`, kernel policy `flash_or_efficient_no_math`, GQA `repeat_kv_sm75`,
> short generation PASS (17 completion tokens), generation-deadline canary
> PASS (`deadline_fired==true`, `finish_reason==timeout`, 4 completion tokens),
> long-context probe PASS (12,044 prompt tokens / 64 completion tokens); the
> bundled canonical `validate_pilot_dryrun_evidence` PASSED (48 records / 48
> unique IDs / statuses all succeeded / repo 16-16-16 / strategies 24-24 /
> reps 24-24 / all model-call + token counters integer zero / source identity
> `478261ff...` + `v0.9.22-pilot-exec-ready` + build `478261f` +
> `dry-run:mock`); notebook cells 0–7 have no error outputs, the
> pilot-launch/resume/verify/export cells remain UNEXECUTED, the only
> `run_records.jsonl` is the 48-record dry-run file, and the HF token value
> never appears (only "retrieved and set in environment" is printed). On PASS,
> the annotated stable tag **`v0.9.22-pilot-exec-ready` now EXISTS** and peels
> to `478261ff595d3d64ed9d5bab32d1cc90d7dabd77` (tag object
> `fdcb409670e040a287811840ddbcab475816a7e5`; `git cat-file -t` = `tag`;
> local + remote peeled target == `478261ff...`; pushed to origin and verified
> with the configured authenticated origin credentials — no anonymous/public
> readability probe). The artifact REMAINS `edae1b7e…8c4a`; **no rebuild and
> no finalizer run**. The real 48-cell Pilot has **NOT** started; the ONLY
> remaining operational step is, in the same still-live Kaggle session, to run
> **Step 8 "Pilot Launch — STOP Until Stable Tag Is Confirmed" /
> `pilot-launch-cell`**. Never resume `exp-20260828-151335` — it has zero
> accepted RunRecords. GitHub privacy is irrelevant to Kaggle execution;
> GitHub is owner-controlled source/release storage only. Full suite remains
> the previously accepted **2538 passed / 33 skipped / 0 failed** (carried;
> runtime code unchanged). Report:
> `reports/V0922_D9_6_REAL_T4_PASS_STABLE_TAG_CLOSURE_REPORT.md`.
>
> **PRIOR TRUTH (2026-08-29, SUPERSEDED by the real 2×T4 PASS + stable-tag
> closure — v0.9.22 D9.6 NOTEBOOK-MARKDOWN CELL-LABELS CLOSURE (PILOT-EXEC-01)
> — NOTEBOOK-NAVIGATION REFINEMENT ON TOP OF THE D9.6 KAGGLE/GITHUB BOUNDARY
> CORRECTION; REAL T4 PROOF PENDING; NO STABLE TAG YET):** branch
> `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure`.
> NOTHING scientific, NOTHING in production/runtime code, and NOT the
> Kaggle/GitHub boundary changed: 11 exact Markdown navigation cells
> (`pilot-step-00..10-*md`, e.g. Step 04 model-preflight, Step 08 STOP
> boundary, Step 09 launch, Step 10 resume) were inserted between the
> (byte-identical, unchanged) 16 executable code cells in
> `notebooks/pilot_exec_01.ipynb` so Kaggle's Table of Contents names every
> operational stage and a visible pre-launch STOP boundary guards
> `pilot-launch`. New regression tests:
> `tests/integration/test_pilot_notebook_contract.py`
> (TestMarkdownNavigation, TestCodeCellsUnchangedFromBaseline,
> TestBundledNotebookParity) and `tests/integration/test_pilot_deployment_bundle.py`
> (TestPilotBundleKeepsMarkdownNavigation). No code-cell source changed;
> witnesses: notebook diff 126 insertions / 0 deletions; code cells compile
> 16/16; established RED-to-GREEN for the new tests. The D9.6 boundary
> correction is carried forward unchanged — Kaggle launch and resume NEVER
> contact GitHub (no `git ls-remote`, no token, no `GIT_*`);
> `validate_pilot_launch_authorization` (pure local evidence: preflight JSON,
> sdpa kernel policy, mandatory generation-deadline canary) is the ONLY
> pre-command gate and is wired into BOTH `pilot-launch-cell` AND
> `pilot-resume-cell` before command construction; the stable tag is
> owner-side only: the annotated `v0.9.22-pilot-exec-ready` tag is created and
> locally verified against the owner-controlled, locally verified source
> commit after real preflight passes — no runtime gate ever contacts GitHub.
> D9.1–D9.4 mechanics (decode-step workflow-deadline stopping criterion with
> 30 s liveness heartbeats, mandatory real-Qwen generation-deadline canary,
> eager shared-model init, per-run cooperative guard install) and the
> interrupt-safe process-group terminate→kill→reap are unchanged. DEGREE
> GREEN: the new notebook-nav tests + focused boundary + notebook/finalizer/
> provenance suites green; full acceptance **2538 passed / 33 skipped / 0
> failed**. FROZEN via the two-pass finalizer (`--source-commit 478261f…`,
> `--verify-source-provenance`): **0 mismatches**, idempotent same-input rerun
> (archive SHA unchanged); the stable code/data/repository-snapshot/transport
> manifest hashes are UNCHANGED from D9.6 — `37e79950…`/`8b859ecc…`/
> `49d91d39…`/`07036a36…` — because only the notebook markdown changed;
> notebook_manifest_sha256 is NEW
> `9d3edac4c20c00ab73a1ecda10d52322a5c57756820ed03f3a6162615e19adb6`,
> deployed bundle notebook SHA
> `6720293b922e06a80ecdc44a6d16e5eb12cc777d23c24a7076d005872d7aba68` ==
> canonical source blob at `478261f…` → **SOURCE COMMIT
> `478261ff595d3d64ed9d5bab32d1cc90d7dabd77`** (build id `478261f`; supersedes
> the D9.6 boundary-correction source
> `6ff1c93ed355b6dc73fa3ebd18ba6079ace39ab6`). Exact artifact
> `dist/pilot-kaggle-upload.zip` SHA-256
> **`edae1b7e5be7ebab642d1e3c068dda3842a8061b8b04ab84c027d43a38dc8c4a`**;
> sidecar matches. Freeze report source == `478261f…`, FROZEN. Canonical+
> bundled notebooks compile 16/16. Exact fresh-extraction bundled dry-run
> (bundled CLI, explicit `--source-commit
> 478261ff595d3d64ed9d5bab32d1cc90d7dabd77`) **48/48**: 48 unique IDs, repos
> 16/16/16, strategies 24/24, reps 24/24, 0 calls/tokens; canonical
> `validate_pilot_dryrun_evidence` PASS — every record + `source_identity.json`
> == `478261f…` and its build id `478261f`. Scientific contract unchanged.
> REQUIRED TRUTHFUL STATUS: the prior D9.6 artifact
> `03d8d0ae37b995a362ee90c53a1851588ad024f13ead033814399210ce54dfc4` (source
> `6ff1c93…`) is SUPERSEDED by this notebook-nav artifact — do not upload the
> old artifact; D8 (`02d16ca2…`) is REJECTED for Pilot launch (its exact 2×T4
> preflight passed but the real Pilot exposed the in-flight timeout/heartbeat
> defect D9 closes) and remains superseded;
> `exp-20260828-151335` has 0 accepted RunRecords and must never be resumed;
> this remains v0.9.22 (never v0.9.23). NO stable tag during this local
> closure: next external step is ONE exact-new-artifact real 2x T4 GQA
> microprobe + generation-deadline canary + short + 12k preflight ONLY;
> annotate `v0.9.22-pilot-exec-ready` at `478261f…` ONLY after PASS; on FAIL
> return to the SAME v0.9.22 task (never v0.9.23). Report:
> `reports/V0922_D9_6_NOTEBOOK_MARKDOWN_NAVIGATION_CLOSURE_REPORT.md`.
>
> **PRIOR TRUTH (2026-08-29, SUPERSEDED by the D9.6 notebook-markdown
> cell-labels closure — v0.9.22 D9.6 KAGGLE/GITHUB BOUNDARY CORRECTION +
> IN-FLIGHT WORKFLOW-DEADLINE HEARTBEAT + EAGER MODEL INIT):**
> branch `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure`. D9.1 the
> `_WorkflowDeadlineHeartbeatStoppingCriteria` (transformers-compatible stopping
> criterion, `kaggle_qwen_backend.py`) is polled at every decode step and stops
> generation with `finish_reason="timeout"` the moment the injected run guard
> (`lambda: not budget.timed_out`) first returns false — an in-flight generation
> can never cross the 600 s deadline; bounded 30 s liveness heartbeats
> (`GENERATION_RUNNING` / `GENERATION_STOPPED reason=workflow_deadline`) prove a
> long synchronous decode alive (cooperative stop at the step boundary, never a
> thread kill). D9.2 real-Qwen generation-deadline canary
> (`run_generation_deadline_probe`): a deterministic counter guard makes the
> workflow-deadline path fail-closed after 3 criterion checks, so the deadline
> (NOT EOS/length) is proven target-side with `completion_tokens` in the tiny
> bound `[1, GENERATION_DEADLINE_PROBE_MAX_CHECK_BOUND=8]`;
> `_generation_deadline_probe_errors` makes the canary MANDATORY in preflight and
> launch authorization (mock backends omit it; a real launch always requires it).
> D9.3 eager shared-model init (`initialize()` + CLI before `t_start`/any
> `RUN_START`): the one-time Qwen weights load happens outside the first run's
> scientific timing/token budget; failure is an engineering blocker with 0
> RunRecords (checkpoint left resumable/incomplete, nonzero exit). D9.4 the Runner
> installs the cooperative deadline guard per-run on strategy AND shared backend
> (`_apply_model_call_guards`, fresh lambda over THIS run's budget) so the backend
> never retains a prior run's guard. D9.6 Kaggle/GitHub boundary correction: the
> D9.5 runtime remote tag-peel gate is REMOVED — Kaggle launch
> and resume NEVER contact GitHub (no `git ls-remote`, no token, no `GIT_*`);
> `validate_pilot_launch_authorization` (pure local evidence: preflight JSON, sdpa
> kernel policy, mandatory generation-deadline canary) is the ONLY pre-command
> gate and is wired into BOTH `pilot-launch-cell` AND `pilot-resume-cell` before
> command construction. The stable tag is owner-side only: the annotated
> `v0.9.22-pilot-exec-ready` tag is created and locally verified against the
> owner-controlled, locally verified source commit after real preflight passes —
> no runtime gate ever contacts GitHub. `_run_live` keeps process-group
> terminate→kill→reap with bounded grace. Genuine RED: the D9.5 baseline left 10
> boundary-test failures (tag-peel machinery in preflight.py + notebook; the
> resume cell lacked the local authorization gate); D9.6 closes all 10. DEGREE
> GREEN: focused boundary + notebook/finalizer/provenance suites green; full
> acceptance **2538 passed / 33 skipped / 0 failed**. FROZEN via the two-pass
> finalizer (`--source-commit 6ff1c93…`, `--verify-source-provenance`): **0
> mismatches**, idempotent same-input rerun (archive SHA unchanged, stable
> manifest hashes unchanged) → **D9.6_SOURCE_COMMIT
> `6ff1c93ed355b6dc73fa3ebd18ba6079ace39ab6`** (supersedes D9
> `9ea02b35d58a3e4ef2d0d5d980e44fa53d8c079d`; code+tests commit `13dc527…`,
> anchor-refresh commit `6ff1c93…`). Exact artifact `dist/pilot-kaggle-upload.zip`
> SHA-256 **`03d8d0ae37b995a362ee90c53a1851588ad024f13ead033814399210ce54dfc4`**;
> sidecar matches. Freeze report source == `6ff1c93…`, FROZEN. Canonical+bundled
> notebooks compile 16/16. Exact fresh-extraction bundled dry-run (bundled CLI,
> explicit `--source-commit 6ff1c93…`) **48/48**: 48 unique IDs, repos 16/16/16,
> strategies 24/24, reps 24/24, 0 calls/tokens; canonical
> `validate_pilot_dryrun_evidence` PASS — every record + `source_identity.json`
> == `6ff1c93…` and its build id. Scientific contract unchanged. REQUIRED
> TRUTHFUL STATUS: D8 exact 2×T4 preflight passed but D8 is REJECTED for Pilot
> launch (the real Pilot exposed the in-flight timeout/heartbeat defect D9 now
> closes); `exp-20260828-151335` has 0 accepted RunRecords and must never be
> resumed; D9 remains v0.9.22 and supersedes D8 (`02d16ca2…` artifact superseded;
> the D9 artifact `913e8065…` is also superseded by D9.6; do not upload either).
> NO stable tag during this local closure: next external step is ONE
> exact-D9.6-artifact real 2x T4 GQA microprobe + generation-deadline canary +
> short + 12k preflight only; annotate `v0.9.22-pilot-exec-ready` at `6ff1c93…`
> ONLY after PASS; on FAIL return to the SAME v0.9.22 task (never v0.9.23). Report:
> `reports/V0922_D9_6_KAGGLE_GITHUB_BOUNDARY_CLOSURE_REPORT.md`.
>
> **PRIOR TRUTH (2026-08-29, SUPERSEDED by D9.6 — v0.9.22 D9 IN-FLIGHT
> WORKFLOW-DEADLINE HEARTBEAT + EAGER MODEL INIT + FREEZE RECOVERY CLOSURE):**
> branch `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure`. D9.1 the
> `_WorkflowDeadlineHeartbeatStoppingCriteria` (as above) polls every decode step
> and stops generation with `finish_reason="timeout"`; bounded 30 s liveness
> heartbeats prove a long synchronous decode alive. D9.2 real-Qwen
> generation-deadline canary makes the deadline (NOT EOS/length) proven target-side
> with `completion_tokens` in `[1, 8]`, MANDATORY in preflight and launch
> authorization. D9.3 eager shared-model init outside the first run's scientific
> timing/token budget (failure = engineering blocker, 0 RunRecords, exit 1). D9.4
> per-run cooperative guard install on strategy AND shared backend
> (`_apply_model_call_guards`, fresh lambda over THIS run's budget). D9.5 (REMOVED
> by D9.6) wired a no-shell bounded remote annotated-tag-peel launch gate
> into `pilot-launch-cell` AND
> `pilot-resume-cell`; `_run_live` gained process-group terminate→kill→reap.
> Genuine RED: D8 baseline 17 failures before D9. DEGREE GREEN: focused D9 38/38 +
> the already-green D8 closures; full acceptance **2532 passed / 33 skipped /
> 0 failed**. FREEZE RECOVERY (authorized): three orphan untracked D8-baseline
> scratch copies deleted after the four read-only checks (untracked, zero repo
> references, exact D8 blobs at `8f0b119…`: `_base_check_seven.py` =
> `seven_arm_benchmark.py` blob `99de1643…` SHA-256 `044913c8…`,
> `src/benchmark/execution/_base_check_preflight.py` = `preflight.py` blob
> `c7899452…` SHA-256 `7b583872…`, `src/benchmark/llm/_base_check_backend.py` =
> `kaggle_qwen_backend.py` blob `6e2ff716…` SHA-256 `82caa092…`); finalizer
> discovery at `a91ee87db540ae9da0ffd87b73ebdfb1cf973d86` (no
> `--verify-source-provenance`) rewrote the stale code-manifest anchor after the
> orphans were absent (only tracked source change = the canonical notebook
> anchors) → **D9_SOURCE_COMMIT
> `9ea02b35d58a3e4ef2d0d5d980e44fa53d8c079d`**. Provenance-enabled finalizer
> (`--verify-source-provenance`) at `9ea02b3…` FROZEN, **0 mismatches**;
> idempotent same-input rerun: notebook unchanged, archive SHA unchanged, stable
> manifest hashes unchanged. Exact artifact `dist/pilot-kaggle-upload.zip`
> SHA-256 **`913e8065a384effa2cf6b6a69f11e5840506644873fa54764c3cbe8ee5406d48`**;
> sidecar matches. Freeze report source == `9ea02b3…`, FROZEN. Canonical+bundled
> notebooks compile 16/16; focused notebook/finalizer/provenance **165/165**.
> Exact fresh-extraction bundled dry-run (bundled CLI, explicit
> `--source-commit 9ea02b3…`) **48/48**: 48 unique IDs, repos 16/16/16,
> strategies 24/24, reps 24/24, 0 calls/tokens; canonical
> `validate_pilot_dryrun_evidence` PASS — every record + `source_identity.json`
> == `9ea02b3…` and its build id. Scientific contract unchanged. REQUIRED
> TRUTHFUL STATUS: D8 exact 2×T4 preflight passed but D8 is REJECTED for Pilot
> launch (the real Pilot exposed the in-flight timeout/heartbeat defect D9 now
> closes); `exp-20260828-151335` has 0 accepted RunRecords and must never be
> resumed; D9 remains v0.9.22 and supersedes D8 (`02d16ca2…` artifact superseded;
> do not upload the old artifact). NO stable tag during this local closure: next
> external step is ONE exact-D9-artifact real 2x T4 GQA microprobe + short + 12k
> preflight only; annotate `v0.9.22-pilot-exec-ready` at `9ea02b3…` ONLY after
> PASS; on FAIL return to the SAME v0.9.22 task (never v0.9.23). Report:
> `reports/V0922_D9_INFLIGHT_DEADLINE_HEARTBEAT_EAGER_INIT_TAG_PEEL_FREEZE_CLOSURE_REPORT.md`.
>
> **PRIOR TRUTH (2026-08-28, SUPERSEDED by D9 — v0.9.22 D8 DRY-RUN TOKEN-SCHEMA +
> LAUNCH-AUTH EVIDENCE CLOSURE):** branch
> `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure`. D8 closes the proven
> `RunRecordData` token-schema drift: a real 48-record CLI dry-run writes nested
> `token_usage` (`prompt/completion/total`) plus `total_workflow_model_calls`,
> `total_workflow_tokens`, phase `selection|regeneration|repair` `_model_calls` /
> `_total_tokens`, and status `succeeded` — NEVER a top-level `total_tokens`. The
> pre-D8 bundled dryrun-cell read the fabricated top-level `total_tokens`, so the
> old 48-cell gate was a false green (proven: old code PASSes real records via the
> fail-open `or 0` check). D8.1 adds the canonical
> `validate_pilot_dryrun_evidence` + private `_collect_dryrun_evidence_errors` with
> strict `_expect_zero_int` (None/bool/str/float/non-zero all fail closed), returns a
> truthful summary, and refactors `validate_pilot_launch_authorization` to reuse the
> same collector (single source of truth); D8.2 the bundled `dryrun-cell` now calls
> `validate_pilot_dryrun_evidence(..., expected_model_identity="dry-run:mock")` and
> prints only summary-backed totals; D8.3 the GQA per-device display reads all real
> evidence fields (device/passed/gpu/cc/heads/qkv/out) instead of the fabric
> `.get('available')`; D8.4 notebook-contract AST tests (6), GQA display tests (3),
> and D8.5 real CLI dry-run + bundled integration tests (2) green; D8.6 release-path
> tests include the notebook executing the same canonical fixture. Genuine RED: 39
> new unit tests + 1 false-green proof failed before D8.1. GREEN: focused 40/40 (unit)
> plus 136/136 (contract+bundle); full acceptance **2492 passed / 33 skipped /
> 0 failed**. Exact final-artifact dry-run **48/48** (48 unique IDs, repos 16/16/16,
> strategies 24/24, reps 24/24, zero calls/tokens, every record source commit ==
> `8f0b11953a4fe2990b7e6c680288be282b8a6b67`). Exact artifact
> `dist/pilot-kaggle-upload.zip` SHA-256
> `02d16ca2c3a35969b32ac438e577f41198e376ba0ce9ee88757a07bd46f268ee`;
> sidecar matches; trust/provenance 0 mismatches, FROZEN. `e0a64937…` (D7),
> `ce40b330…` / `f72ecda…` are SUPERSEDED. Scientific contract unchanged. NO stable
> tag: run the exact new-artifact real 2x T4 preflight only; tag
> `v0.9.22-pilot-exec-ready` at `8f0b119…` only after GQA microprobe + short + 12k
> PASS; no 48-cell launch while untagged. Report:
> `reports/V0922_D8_DRYRUN_TOKEN_SCHEMA_LAUNCH_AUTH_CLOSURE_REPORT.md`.
>
> **PRIOR TRUTH (2026-08-27, SUPERSEDED by D8 — LAUNCH/RESUME VALIDATION-ARGV
> EXECUTABILITY CLOSURE):** D6 was RESOLVED before D7 began: local/remote branch
> parity and a verified post-push project export were proven at
> `1b857fc9fce77e6b637ef292c393d28620e92fdc`. D7 restored the three live
> `--validation-python` mappings (Todo, django CMS, Saleor) and live
> `--validation-timeout 1800` in both `pilot-launch-cell` and `pilot-resume-cell` by
> adding only the missing source-element newlines. Exact assigned-list AST tests prove
> the mappings/order, timeout-before-`--hf-repo-id`, and unchanged scientific
> `--timeout 600`. GREEN: affected suites 102/102; full acceptance **2442 passed /
> 33 skipped / 0 failed**. Exact artifact SHA-256
> `e0a649375104b44d1de7bc5f39145f81bc21365a4380755e73cb1efb719390a8` from source
> `3ebc75dad2f47c8985ce045bcdc8907ce2d52f3c`; sidecar matches; trust/provenance
> 0 mismatches, FROZEN (superseded by D8; do not upload the old artifact).
>
> **PRIOR TRUTH (2026-08-27, SUPERSEDED by D7 — GQA MICROPROBE + NOTEBOOK + EXPORT INTEGRITY CLOSURE):** branch
> `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure` (built on the v0.9.22
> candidate-consistency merge `ba08392552545baa15c10ae5db2e95ce7496a720` + the v0.9.22
> GQA SDPA + preflight observability closure) now carries the D1–D6 bounded correction
> task: D1 `_gqa_microprobe_expand_kv` uses local tensor repeat-KV
> (`repeat_interleave` on the head axis) — NO fabricated `torch.nn.functional.repeat_kv`;
> D2 the microprobe allocates Q/K/V explicitly on each target `cuda:<index>`, synchronizes
> the device after SDPA, records/verifies per-device evidence (exact geometry 40/8/8→40/40/40,
> FP16, seq 68; FLASH+EFFICIENT only, MATH excluded), and `all_passed` only when every
> visible device passes finite+shape+device; D3 `pilot-repo-preflight-cell` restored to a
> 210-element newline-preserving source (was a 172-element all-comment no-op) that
> `compile("".join(source), …)` succeeds on and whose AST carries executable microprobe +
> fail-closed `raise` + `_run_tee` nodes; D4 `_run_tee` enforces its deadline WHILE the child
> runs (terminate→kill→reap, bounded tail) instead of only after EOF; D5 em-dash mojibake
> (`â€"`) restored to proper em dashes across cells (0 mojibake in canonical + bundled); D6
> export rebuilt only after final commit/push and verified by fresh extraction (empty
> `git status`, extracted HEAD == report HEAD, origin ref == HEAD, artifact + sidecar match,
> trust freeze tracked & byte-identical) — **truthful status: local export verified, but
> push/origin parity (`origin ref == HEAD`) and the definitive post-push export remain
> PENDING until this branch is pushed.** Frozen scientific contract UNCHANGED (model
> Qwen2.5-Coder-14B-Instruct, BNB-NF4, sdpa, kernel policy `flash_or_efficient_no_math`
> (MATH disabled), GQA compat `KAGGLE_SDPA_GQA_COMPATIBILITY = "repeat_kv_sm75"`, 12
> scenarios, 3 pins, 2 strategies, 2 reps = 48 cells, prompts, Ground Truth, metrics,
> --timeout 600, --validation-timeout 1800, max attempts 3, completion cap 4096, the
> 12000/64 long-context gate). Full suite **2441 passed / 33 skipped / 0 failed**; exact
> final-artifact dry-run **48/48** (48 unique IDs, repos 16/16/16, strategies 24/24, reps
> 24/24, 0 model calls, 0 tokens, every record source commit == `f72ecda…`). Exact candidate
> artifact `dist/pilot-kaggle-upload.zip` SHA-256
> `ce40b33019feba58d8cabeef2244a765e157cdba4288a9d9ea2eb186de46a24d` (+ sidecar verified)
> built from source commit `f72ecda0e7dac10e81dae34daa6bb1610c94b9ee` via the idempotent
> two-pass finalizer with `--verify-source-provenance` (0 mismatches;
> `reports/pilot_notebook_trust_freeze.json` FROZEN). NO stable `v0.9.22` tag yet: the real 2x
> T4 Kaggle model preflight (repo preflight + heartbeat, Qwen 14B BNB-NF4 load, GQA microprobe,
> short probe + 12k target, same 64-token probe) is MANDATORY before creating
> `v0.9.22-pilot-exec-ready`; if the Kaggle proof fails, return to the SAME v0.9.22 task (never
> spawn v0.9.23). Report:
> `reports/V0922_GQA_MICROPROBE_NOTEBOOK_EXPORT_INTEGRITY_CLOSURE_REPORT.md`.
> **SUPERSEDED:** prior v0.9.22 candidate source `de0c5bd8bcc7d499246292f515207ce1d10baba7` /
> artifact `bfbc935f762b484482eee411c5ea7996412b1e47f759f6dca81fa58b0ab9a850` — do not run
> the old artifact (`reports/V0922_T4_GQA_SDPA_PREFLIGHT_OBSERVABILITY_CLOSURE_REPORT.md`).
>
> **PRIOR TRUTH (2026-08-24, HISTORICAL): v0.9.22 long-context attention memory closure —
> branch `fix/pilot-v0922-long-context-attention-memory-closure` implements the long-context
> attention memory closure on top of clean main `58d1be533c98ca9bafc9a344f2a73f8a140b9540`
> (v0.9.21 reconciled).** The real Kaggle v0.9.21 model preflight PASSED repository
> preflight / dependencies / Qwen 14B BNB-NF4 load (`qwen_model_load[bnb-nf4]: PASS` —
> the old 2026-08-05 model-load OOM fix still works) / GPU-only device map / 2x Tesla T4 /
> per-GPU headroom (min free 7.764 GiB) / short generation probe, then FAILED at the
> long-context probe with CUDA OOM: 12,044 prompt tokens / 64-token output budget /
> **failed allocation 21.62 GiB == exactly `12044*12044*40*4 bytes = 21.6153 GiB`, the
> full float32 40-head quadratic attention score matrix** — proving the effective runtime
> attention path had materialized the math/eager fallback during prompt prefill
> (offloaded KV cache does not cover prefill attention; device_map=auto is not tensor
> parallelism). v0.9.21 Real Pilot REJECTED BEFORE LAUNCH for this reason; no Experiment
> ID / no RunRecord created; no stable tag moved. The v0.9.22 candidate closes it WITHOUT
> touching any scientific input (model Qwen2.5-Coder-14B-Instruct, BNB-NF4, 12 scenarios,
> 3 repo pins, 2 strategies, 2 reps = 48 cells, prompts, Ground Truth, metrics,
> --timeout 600, --validation-timeout 1800, max attempts 3, completion cap 4096, the
> 12000-token long-context gate, the 64-token probe): Task A explicit
> `attn_implementation="sdpa"` at from_pretrained; Task B fail-closed CUDA generation
> inside `sdpa_kernel([FLASH_ATTENTION, EFFICIENT_ATTENTION])` (no math/eager fallback;
> missing torch.nn.attention API on CUDA fails closed); Task C canonical attention
> evidence (`requested/effective_attn_implementation`,
> `sdpa_kernel_policy=flash_or_efficient_no_math`) persisted in preflight JSON, rendered
> in the human table, enforced by the new fail-closed `attention_policy` check and by
> pilot launch authorization; Task D corrected OOM diagnosis (long-prompt OOM reports
> prompt-prefill attention evidence + free GiB and never advises completion-cap
> reduction); Tasks E/F regression-guard every prior memory fix and the unchanged
> 12000/64 gate. RED/GREEN proven: 12 backend + 18 preflight contract tests failed
> against v0.9.21 code before the fix. Full suite **2407 passed / 33 skipped / 0
> failed**; dry-run pilot profile 48/48 (unique IDs, 0 model calls, 0 tokens). Phase 2 release
> mechanics COMPLETE, superseded once by the candidate consistency closure (PILOT-EXEC-01,
> branch `fix/pilot-v0922-candidate-consistency-closure`, non-ff merge → main
> `ba08392552545baa15c10ae5db2e95ce7496a720` pushed; NO scientific/runtime code delta):
> four stale v0.9.21 release-test constants aligned to the planned tag, order-independent
> missing-SDPA-API test isolation (pre-populated `torch.nn.attention` regression condition,
> RED/GREEN proven), untracked generated dry-run dirs removed after evidence verification;
> post-correction full suite **2407 passed / 33 skipped / 0 failed** (2440 collected) with the
> real expanded-artifact simulation re-enabled and passing; anchors frozen for planned
> `v0.9.22-pilot-exec-ready` at the new merge via the idempotent two-pass finalizer with
> `--verify-source-provenance` (0 mismatches; `reports/pilot_notebook_trust_freeze.json`);
> exact candidate artifact `dist/pilot-kaggle-upload.zip` SHA-256
> `3fd986262936972a6f12adbae21e844adef488dfd76ef0e4b2e6e434b2aa65b3` (+ sidecar verified) with
> exact-artifact dry-run 48/48 (repos 16/16/16, strategies 24/24, reps 24/24, new source commit
> in every record). Historical first-freeze identity: merge `4827045fce96eb4caa3645e3cf3c8434dca2a1a8`,
> artifact `9182ea2bb091f785ff325a1355caa5bb0f57283764215059092970bbd8014974`. NO stable
> tag exists yet: per the one-shot flow the exact candidate artifact is built from the
> merge commit and the real 2x T4 Kaggle model preflight (same 12k target, same 64-token
> probe) is MANDATORY before creating `v0.9.22-pilot-exec-ready`; if the Kaggle proof
> fails, return to the SAME v0.9.22 task (never spawn v0.9.23). Report:
> `reports/V0922_LONG_CONTEXT_ATTENTION_MEMORY_CLOSURE_REPORT.md` (Section 7 = consistency audit).
>
> **PRIOR TRUTH (2026-08-24, HISTORICAL): accepted release =
> `v0.9.21-pilot-exec-ready` @ annotated tag peel == artifact source commit ==
> merge `e308047c9c05f38316d80ce565bac1b51d105bfa`; archive
> `dist/pilot-kaggle-upload.zip` SHA-256
> `62e377467e225d336cbcaa70a2c610b5080e329e1a4e6578fbcbdc1af7dbee40` (+ sidecar);
> trust/provenance 0 mismatches; exact-artifact dry-run 48/48; full suite 2370 passed /
> 33 skipped / 0 failed; target-shaped no-model preflight GREEN on the released source
> state (CI run 32694137255; Gates 1-3 green in run 32692489617: production
> FunctionalValidator real targets exit 0 with provisioned interpreters + frozen env;
> Saleor full primary exit 0 in 941.42s < the new explicit 1800s per-cell validation
> budget). v0.9.20 closed the Saleor preflight root cause but was NOT accepted for Real
> Pilot launch: an independent audit found that generated-workspace validation used
> sys.executable for every repository (B1), discarded the frozen validation env (B2), and
> hardcoded a 180s validation timeout below the measured 775.71s/941.42s Saleor runtime
> (B3). v0.9.21 closes all three with --validation-python mappings,
--validation-timeout 1800 on launch+resume, and frozen-env propagation through
PipelineConfig/RunnerConfig into FunctionalValidator. The v0.9.21 repository/per-cell
fixes remain VALID and are carried forward; the Real Pilot was rejected before launch
only because the fresh real 12k model probe exposed the attention-prefill OOM now closed
by the v0.9.22 candidate. Report:
> `reports/V0921_PER_CELL_VALIDATION_RUNTIME_CLOSURE_REPORT.md`.
>
> **PRIOR TRUTH (2026-08-24 earlier in the day, HISTORICAL): accepted release =
> `v0.9.20-pilot-exec-ready` @ annotated tag peel == artifact source commit ==
> merge `febda7938db1284da4090d35e980db472149c3ad`; archive
> `dist/pilot-kaggle-upload.zip` SHA-256
> `56b1c2a9019a03892ce627321b9a415795ac95836ac415694bbc0995263c8024` (+ sidecar);
> trust/provenance 0 mismatches; dry-run 48/48; full suite 2346 passed /
> 33 skipped / 0 failed. The real Kaggle v0.9.19 run FAILED at the Saleor fast
> capability gate (Pytest exit 5 = no tests collected; services/env/Todo/
> django CMS all PASS) — v0.9.19 REJECTED FOR PILOT LAUNCH. Root cause: the gate
> argv concatenated a second `-m pytest` vector onto the already-resolved full
> primary command (Pytest read `-m pytest` as a marker expression). Local tests
> were false-green via a substring-based fake runner. Closed in v0.9.20: exact
> standalone gate argv + fail-fast invariant + exact-argv regression tests
> (RED/GREEN proven; target-proven on Linux CI runs 32650273641 / 32672656326 /
> 32676588800 — the last is the fully green no-model preflight on the released
> source state, pristine Saleor primary exit 0 in 775.71 s) + substring mock
> replaced by exact-command validation + evidence-backed baseline-flake policy
> (`pilot_saleor_baseline_flaky_profile.v1`, armed-if-evidenced) +
> `.github/workflows/pilot-preflight-target-shape.yml`. Stable-tag policy:
> `*-pilot-exec-ready` means all no-model preflight gates passed in
> target-shaped Linux CI. Report:
> `reports/V0920_ROOT_CAUSE_CLOSURE_REPORT.md`.
>
> **PRIOR TRUTH (HISTORICAL):** accepted source tag `v0.9.19-pilot-exec-ready`;
> tag peel/artifact source commit `2305991442a4f965d44bb066bb00c0a459fc395a`
> (REJECTED FOR PILOT LAUNCH 2026-08-24 by the defect above).

- **Accepted release/tag:** `v0.9.21-pilot-exec-ready` @ tag peel == artifact source commit == merge `e308047c9c05f38316d80ce565bac1b51d105bfa`; archive `62e377467e225d336cbcaa70a2c610b5080e329e1a4e6578fbcbdc1af7dbee40`; trust/provenance 0 mismatches; target-shaped CI green with Gates 1-3 (runs 32692489617 / 32694137255) — **superseded as launch candidate by the v0.9.22 attention closure (Real Pilot rejected before launch at the real 12k attention-prefill OOM); no v0.9.22 stable tag until the real 2x T4 12k probe PASSES**
- **v0.9.22 candidate (CURRENT, D9.6 — REAL 2×T4 PREFLIGHT PASS + STABLE TAG CREATED):** branch `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure`; D1–D9.6 closures complete; full suite 2538 passed / 33 skipped / 0 failed; exact final-artifact dry-run 48/48 (48 unique IDs, repos 16/16/16, strategies 24/24, reps 24/24, 0 calls/tokens, every record source commit/get build id == `478261ff595d3d64ed9d5bab32d1cc90d7dabd77`); exact artifact SHA `edae1b7e5be7ebab642d1e3c068dda3842a8061b8b04ab84c027d43a38dc8c4a` (+ sidecar verified) from tag target/source commit `478261f…` (D9.6 notebook-markdown cell-labels closure on top of the D9.6 Kaggle/GitHub boundary correction — 11 exact Markdown navigation cells + pre-launch STOP boundary, nothing scientific/runtime changed, boundary correction unchanged; supersedes `6ff1c93…`/`03d8d0ae…` and all earlier candidates); trust/provenance 0 mismatches, FROZEN, idempotent, stable manifest hashes unchanged from D9.6; the Kaggle launch/resume cells never contact GitHub; the **real exact-artifact 2×T4 preflight PASSED on 2026-08-30** (GQA microprobe on both `cuda:0`/`cuda:1`, sdpa `flash_or_efficient_no_math` `repeat_kv_sm75`, short probe 17 tokens, generation-deadline canary timeout/4 tokens, 12k long-context 12044/64, repo preflight overall PASS) and the annotated stable tag **`v0.9.22-pilot-exec-ready` now EXISTS and peels to `478261ff...`** (tag object `fdcb409670e040a287811840ddbcab475816a7e5`, pushed to origin, verified with configured authenticated credentials); artifact remains `edae1b7e…8c4a`, no rebuild/finalizer was run; the real 48-cell Pilot has **NOT** started (only Step 8 `pilot-launch-cell` remains, in the still-live Kaggle session); never resume `exp-20260828-151335`
- **v0.9.22 D13r1 candidate (CURRENT — D13r1 CANARY LAUNCH-READINESS FINALIZER; NOT a release; NO stable tag move):** branch `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure`; D13r1 finalizes canary launch-readiness on top of D13 WITHOUT touching scientific inputs. F1 fail-closed semantic-executability gate WIRED into the real pilot/pilot-canary PRE-MODEL launch path (`validate_pilot_launch_authorization` + new `validate_pilot_semantic_executability`, canary/launch/resume cells, CLI `--require-launch-authorization`): the FULL 48-cell Pilot is **NOT a launch basis** while any scenario is semantically unexecutable (saleor-loc-002 `is_featured` known-absent; 7 unregistered fail closed). F2 per-repo `migration_directory` added ONLY to the 3 canary scenarios (todo `todo/migrations`, saleor `saleor/product/migrations`, djangocms `cms/migrations`). F3 migration execution decoupled from `evaluator_asset` (migration-only scenario is valid). F4 exact-patch repair-prompt contradiction removed. F5 `exact_patch` + `agent_control_max_completion_tokens` in frozen config/provenance identity (source_identity.json, bundle identity, notebook `FROZEN_DEPLOYMENT` `{exact_patch: True, agent_control_max_completion_tokens: 512}`, `configs/pilot.yaml`) and ENFORCED by the dry-run + canary evidence validators. **D13r1 candidate artifact `v0.9.22-d13r1-candidate` built + provenance-verified FROZEN** (`--verify-source-provenance`, **0 mismatches**, idempotent same-input rerun archive SHA unchanged): source commit `6bc946a…`; archive SHA-256 **`9f120412cfef5dfb7f66a57c03380fc5149b45b20d53c60d623d1e81bc203461`** (+ sidecar verified); freeze `reports/pilot_notebook_trust_freeze_d13r1.json`; full suite **2650 passed / 34 skipped / 0 failed**; exact-artifact dry-runs (bundled exact): Pilot **48/48** + pilot-canary **6/6**, protocol 1.2 both, canonical `validate_pilot_dryrun_evidence` PASS (source_commit `6bc946a`, exact_patch True, agent_control 512) + bundled-exact canary semantic pre-model gate PASS. This candidate is **NOT** a full-Pilot launch basis either: the next REAL Pilot launch requires a real pilot-canary pass on this or a fresh exact candidate with its own tag decision. The retired `v0.9.22-pilot-exec-ready` tag (peel `478261ff…`) and the `edae1b7e…8c4a` artifact are NOT reused; the D13 candidate (`v0.9.22-d13-candidate`, archive `6edd487a…`) is SUPERSEDED. Report: `reports/V0922_D13R1_CANARY_LAUNCH_READINESS_CLOSURE_REPORT.md`.
- **v0.9.22 D13 candidate (PRIOR — SUPERSEDED by the D13r1 canary launch-readiness closure; NOT a release; NO stable tag move):** branch `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure`; D13 closes root-cause blockers exposed by the 2026-09-02 real pilot-canary (6/6 failed): B1 exact-patch source editing (`exact_patch.py`, 19 tests), B2 configurable agent-control cap (`AGENT_CONTROL_MAX_COMPLETION_TOKENS`, 6 tests), B3 repository-aware migrations (`ScenarioModel.migration_directory`, `_normalize_interpreter_command`, 12 tests), B4 semantic executability gate (`semantic_executability.py`, 6 tests, standalone not wired into validator), protocol Pilot-only 1.1→1.2, event-loop robustness fix, metric-contract test fix. **D13 candidate artifact `v0.9.22-d13-candidate` built + provenance-verified FROZEN** (`--verify-source-provenance`, 0 mismatches): source commit `88605f4…`; archive SHA-256 **`6edd487a853c7bd1cf7eabb788f3fa3b4492dfe96bf0272d04ac6bb3eb34bfdd`** (+ sidecar verified); FROZEN_PROTOCOL_VERSION `1.2`; notebook `FROZEN_DEPLOYMENT.protocol_version: "1.2"`, `FROZEN_MANIFEST_HASHES` freshly computed (code `371d75…`, data `f95656…`, repo-snapshot `5b53af…`, transport `07036a…`); full suite **2630 passed / 33 skipped / 0 failed** (D12 was 2589; +41 = B1 19 + B2 4 + B3 12 + B4 6); exact-artifact dry-runs (bundled exact): Pilot **48/48** + pilot-canary **6/6**, protocol 1.2 both, canonical `validate_pilot_dryrun_evidence` PASS (source_commit `88605f4`, agent_control_max_completion_tokens 512). This candidate is **NOT** a launch basis: next REAL Pilot launch requires a real pilot-canary pass on this or a fresh exact candidate with its own tag decision. The retired `v0.9.22-pilot-exec-ready` tag (peel `478261ff…`) and the `edae1b7e…8c4a` artifact are NOT reused; the D12 candidate (`v0.9.22-d12-candidate`, archive `812d3755…`) is SUPERSEDED. Report: `reports/V0922_D13_CANARY_PRODUCTION_SCALE_EXECUTION_CLOSURE_REPORT.md`.
- **v0.9.22 D12 candidate (PRIOR — SUPERSEDED by the D13 canary production-scale execution fix closure; NOT a release; NO stable tag move):** D12 fixes the verified in-flight blocker: `pilot-canary-cell` (cell 20) read SCRIPT_PATH that only `dryrun-cell` (cell 22) defined, so the canary could not run as an independent stage (NameError). The single canonical `SCRIPT_PATH = CODE_DIR / "seven_arm_benchmark.py"` + FileNotFoundError guard now sits in `pilot-archive-verify-cell` (cell 4) after CODE_DIR checks and before ANY use; the duplicate def/guard was deleted from the dry-run cell; new `TestD12ScriptPathOrchestration` (4 tests) RED→GREEN. NOTHING scientific changed. **D12 candidate artifact `v0.9.22-d12-candidate` built + provenance-verified FROZEN** (`--verify-source-provenance`, 0 mismatches): builds `83d15dd` (code+RED test) → `84acb8b` (notebook anchor refresh + freeze report) → `f960abe` (provenance-verified freeze report) → `fb84073` (release-tag constants); archive SHA-256 **`812d37555a42f8fbdfbbb2e5441c814fb733cfd424ca75c810ead96a0bc4346a`** (+ sidecar verified) from source commit `84acb8b…`; deployed build id `84acb8b`; created-utc 2026-09-01T18:40:35+00:00; full suite **2589 passed / 33 skipped / 0 failed**; six validation gates PASS (G1 267/4, G2 101/4, G3 722/14, G4 source pilot 48/48 + canary 6/6 + exact-artifact pilot 48/48 + canary 6/6, protocol 1.1, canonical `validate_pilot_dryrun_evidence` PASS; G5 integration 258; G6 metrics 329/10). This candidate is **NOT** a launch basis: next REAL Pilot launch requires a real pilot-canary pass on this or a fresh exact candidate with its own tag decision. The retired `v0.9.22-pilot-exec-ready` tag (peel `478261ff…`) and the `edae1b7e…8c4a` artifact are NOT reused; the D11 candidate (`v0.9.22-d11-candidate`, archive `4554dced…`) is SUPERSEDED. Report: `reports/V0922_D12_NOTEBOOK_ORCHESTRATION_FIX_CLOSURE_REPORT.md`; freeze `reports/pilot_notebook_trust_freeze.json`.
- **v0.9.22 D11 candidate (PRIOR — SUPERSEDED by the D12 notebook-orchestration fix closure; D11 B1–B4 complete; NOT a release; NO stable tag move):** the D11 pre-pilot viability gate corrects the pilot-canary operational topology WITHOUT touching scientific inputs. B1 `pilot-canary` profile now represents ALL THREE Pilot repos as a 6-cell matrix (todo-loc-001/djangocms-cross-007/saleor-loc-001 × 2 strategies × 1 rep; fixes the contradictory blast_radii filter that dropped `djangocms-cross-007`); `validate_pilot_canary_evidence` defaults 3-repo / 6-cell (2/2/2 repos, 3/3 strategies, rep1=6); B2 `--protocol-version` CLI default profile-derived via `resolve_profile_protocol` (pilot/pilot-canary → 1.1; all other profiles → 1.0; explicit override always wins); B3 validation-manifest `protocol_version` 1.0 → 1.1 parity with `configs/pilot.yaml`; B4 new executable canary integration test. **D11 candidate artifact `v0.9.22-d11-candidate` built + provenance-verified FROZEN** (`--verify-source-provenance`, 0 mismatches): builds `b07da1a` (code) → `c1c892b` (notebook anchor refresh + freeze report) → `224c5a9` (provenance-verified freeze report); archive SHA-256 **`4554dced6a438893ed01cbdbce9756613c0b0951459a43eb9a4a467edee4cb8a`** (+ sidecar verified) from source commit `c1c892b…`; full suite **2585 passed / 33 skipped / 0 failed**; exact-artifact dry-runs (bundled exact): Pilot **48/48** + pilot-canary **6/6**, protocol 1.1 both, canonical `validate_pilot_dryrun_evidence` PASS. This candidate is **NOT** a launch basis: next REAL Pilot launch requires a real pilot-canary pass on this or a fresh exact candidate with its own tag decision. The retired `v0.9.22-pilot-exec-ready` tag (peel `478261ff…`) and the `edae1b7e…8c4a` artifact are NOT reused; the D10 candidate (`v0.9.22-d10-candidate`, archive `d468ee63…`) is SUPERSEDED. Report: `reports/V0922_D11_PILOT_CANARY_SALEOR_INCLUSIVE_CLOSURE_REPORT.md`; freeze `reports/pilot_notebook_trust_freeze.json`.
- **v0.9.22 D10 candidate (PRIOR — SUPERSEDED by D11; D10.2–D10.7 complete; NOT a release; NO stable tag move):** D10 corrects the internal runtime/operability contract WITHOUT touching scientific inputs. The D10.2–D10.7 implementation (protocol_version 1.0→1.1, Pilot timeout 600→1200 uniformly both strategies, real end-to-end pilot-canary mode + canonical fail-closed `validate_pilot_canary_evidence` gate, standalone fail-closed resume against rejected experiment IDs, terminality-vs-viability split, tests-first RED/GREEN) is complete and pushed. A NEW D10 candidate artifact `v0.9.22-d10-candidate` was built + **provenance-verified FROZEN** (`--verify-source-provenance`, 0 mismatches): archive SHA-256 **`d468ee6341f9a8c652554a814d32e2ff599d0b44359f21f7e7c657eb83c1669c`** (+ sidecar verified) from source commit `0b0e2a8…` (build: 0cb8cc9 code + notebook anchor refresh + freeze report 6b0a88c + release-tag alignment a5c2f02); full suite **2572 passed / 33 skipped / 0 failed**; exact-artifact dry-run 48/48 (bundled exact + expanded-mode; bundled canary gate, protocol 1.1/1200, canonical `validate_pilot_dryrun_evidence` PASS). This candidate is **NOT** a launch basis either: the next REAL Pilot launch requires a real pilot-canary pass on this or a fresh exact candidate with its own tag decision. The retired `v0.9.22-pilot-exec-ready` tag (peel `478261ff…`) and the `edae1b7e…8c4a` artifact are NOT reused. Report: `reports/V0922_D10_ALL_FAILED_PILOT_VIABILITY_CLOSURE_REPORT.md`; freeze `reports/pilot_notebook_trust_freeze.json`.
- **v0.9.20 status:** internally trustworthy; no-model target preflight GREEN; superseded for Real Pilot launch by v0.9.21 after the independent audit found the per-cell validation runtime parity blockers (B1 interpreter routing / B2 frozen env discarded / B3 180s timeout below measured runtime)
- **v0.9.19 status:** REJECTED FOR PILOT LAUNCH 2026-08-24 — real Kaggle Saleor fast-gate Pytest exit 5 (artifact itself was internally GREEN; superseded by v0.9.20)
- **v0.9.18 status:** RELEASE-ONLY CLOSURE (release-only provenance/docs correction; no scientific or production code changes) — historical
- **v0.9.17 status:** REJECTED FOR ACCEPTED PILOT LAUNCH — tag/source-commit release-provenance mismatch (immutable tag peel `28a18e6...` != artifact source_commit `adf72d4...`; the artifact itself is internally trustworthy and the PGDG fix is GOOD)
- **v0.9.16 status:** RELEASE-ONLY CLOSURE (no production behavior changes; notebook anchors corrected) — historical
- **v0.9.15 status:** REJECTED FOR ACCEPTED PILOT LAUNCH — release finalization/artifact not completed (dist artifact still v0.9.14; code-manifest SHA stale; single-parent commit)
- **v0.9.14 status:** REJECTED — artifact notebook provenance did not match immutable tag notebook (historical; see CURRENT TRUTH above)

## Validation order

1. `git diff --check`
2. Ruff on changed Python files
3. Mypy on changed production Python files only
4. Python compile check on changed Python files
5. Targeted Pytest
6. Full Pytest only before commit/merge or when shared interfaces changed
7. Bundle only when production code changed

## Resource rules

- No pytest-xdist by default
- No watch mode, GPU, dataset/model downloads, clean rebuild
- No full test suite after every small patch
- No parallel heavy commands
- Trim logs to first root cause and relevant tail (~120 lines max)

## Git rules

Do not commit, push, merge, tag, reset, stash, force, or delete files unless explicitly requested in the current task.

## Scientific rules

- Ground Truth is evaluation-only.
- Do not claim Scientific Smoke or Pilot success without real execution.
- Keep PROJECT_HANDOFF and MASTER_IMPLEMENTATION_PLAN truthful.
- Update README only when user-facing behavior changes.
- Stable tag only after a successful Scientific Smoke audit.

## Release provenance invariant

- Artifact source commit MUST equal immutable release tag peel.
- Create the tag explicitly on the accepted artifact source commit (not HEAD).
- Post-tag docs evidence commits are never tag targets.

## Stop / Blocker Reporting Contract

Before stopping for ANY reason (needs auth, missing input, blocker, task
complete, uncertain decision, permission rule, resource boundary), print a
structured report containing:

1. **Execution Identity** — provider, model, branch, HEAD, origin/main, tree state
2. **Why I Am Stopping** — exact reason; COMPLETE / BLOCKED / NEEDS AUTHORIZATION / NEEDS INPUT
3. **What I Completed** — per-file table: File | Symbol | Old | New | Why | Dependencies
4. **Verification Performed** — compile, lint, mypy, tests (PASS/FAIL/NOT RUN/BLOCKED with exact counts)
5. **Pre-Benchmark Validation** — dataset, prompt, pipeline, dry-run, integration, metrics
6. **Independent Self-Audit** — objective unchanged, plan adherence, over-engineering, debt, durability, freshness, tag state
7. **Exact Current State** — where project stops in the pipeline
8. **What Remains** — ordered remaining tasks
9. **What I Need From User** — minimum input or `Nothing — I can continue automatically.`
10. **Recommended Next Action** — exact next command; if existing instructions authorize it, continue without stopping

Never end with only "Proceed?" or a bare question.

## Project Export Rule (every mandatory stop)

At every STOP / Mandatory Stop Report, create a filtered audit ZIP in the
parent directory of `project/` named exactly `project-YYYY-MM-DD-HHmm.zip`
(local creation timestamp). This is workflow/documentation only — do NOT
create a release, move, or tag for this rule.

**Include:** ALL files tracked by `git ls-files` (source, tests, notebooks,
docs, configs, scripts, `benchmark_data/`, `reports/`, `.opencode/` workflow
files, etc.), `.git/`,
`dist/pilot-kaggle-upload.zip`, `dist/pilot-kaggle-upload.zip.sha256`.
`runs_dryrun/` is a **frozen HISTORICAL tracked fixture** (7 records,
`profile=smoke`, source `0c831e3`, added at commit `b203b21`) and is included
only for historical reproducibility — it is NOT current candidate proof and
MUST NOT be used for Pilot launch authorization; current D9 evidence is a fresh
exact-artifact 48/48 run generated into a fresh temporary/output directory.

**Exclude:** `.mypy_cache/`, `.ruff_cache/`, `.pytest_cache/`,
`__pycache__/`, `*.pyc`, `.opencode/node_modules/`, `dist/_provcheck*`,
extracted `dist/pilot-kaggle-upload/`, `dist/pilot-repo-cache/`.

**Do not delete** anything from the real project. Only the share ZIP is
filtered.

After creation verify required members inside the ZIP (`.git/HEAD`,
`dist/pilot-kaggle-upload.zip`, `.sha256`), compute size + SHA-256, and
print:

```
PROJECT_EXPORT_READY
PROJECT_EXPORT_NAME=project-YYYY-MM-DD-HHmm.zip
PROJECT_EXPORT_PATH=<absolute path>
PROJECT_EXPORT_SIZE_BYTES=<bytes>
PROJECT_EXPORT_SHA256=<sha256>
UPLOAD_THIS_FILE=project-YYYY-MM-DD-HHmm.zip
```

The Stop Report must include this filename so the user knows which file to
upload.
