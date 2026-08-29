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

> **CURRENT TRUTH (2026-08-29, v0.9.22 D9.6 IN-FLIGHT WORKFLOW-DEADLINE HEARTBEAT +
> EAGER MODEL INIT + KAGGLE/GITHUB BOUNDARY CORRECTION; REAL T4 PROOF PENDING):**
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
- **v0.9.22 candidate (CURRENT, D9.6):** branch `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure`; D1–D9.6 closures complete; full suite 2538 passed / 33 skipped / 0 failed; exact final-artifact dry-run 48/48 (48 unique IDs, repos 16/16/16, strategies 24/24, reps 24/24, 0 calls/tokens, every record source commit/get build id == `6ff1c93ed355b6dc73fa3ebd18ba6079ace39ab6`); exact artifact SHA `03d8d0ae37b995a362ee90c53a1851588ad024f13ead033814399210ce54dfc4` (+ sidecar verified) from future tag target/source commit `6ff1c93…` (**D9.6_SOURCE_COMMIT**; supersedes D9 `913e8065…`/`9ea02b3…` and all earlier candidates); trust/provenance 0 mismatches, FROZEN, idempotent; the Kaggle launch/resume cells never contact GitHub and the stable tag is locally verified against the owner-controlled, locally verified source commit after real preflight passes; NO stable tag until real 2x T4 GQA microprobe + short + 12k probe PASSES
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
