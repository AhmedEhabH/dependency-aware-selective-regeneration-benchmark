# AI Account-Transfer Handoff — CURRENT v0.9.22 D9.6 NOTEBOOK-MARKDOWN CELL-LABELS CANDIDATE State (2026-08-29)

**Read this file FIRST.** It is the single authoritative snapshot of the
current project state for any AI agent or human resuming on a new account.
Older files contain valuable history, but their "Current" sections may be
superseded — this file wins every contradiction.

---

## 1. Current truth (memorize these facts)

| Fact | Value |
|---|---|
| Real Kaggle v0.9.21 model preflight result | **FAILED at the long-context probe — CUDA OOM: 12,044 prompt tokens / 64-token output budget / failed allocation 21.62 GiB == exactly `12044*12044*40*4 bytes = 21.6153 GiB`, the full float32 40-head quadratic attention score matrix** after repository preflight / dependencies / Qwen 14B BNB-NF4 load (`qwen_model_load[bnb-nf4]: PASS` — the old 2026-08-05 model-load OOM fix still works) / GPU-only device map / 2x Tesla T4 / per-GPU headroom (min free 7.764 GiB) / short generation probe all PASSED; **v0.9.21 Real Pilot REJECTED BEFORE LAUNCH — no Experiment ID / no RunRecord created; no stable tag moved** |
| Root cause | The effective runtime attention path materialized the math/eager fallback during prompt prefill (offloaded KV cache does not cover prefill attention; `device_map=auto` is not tensor parallelism) |
| Closure branch | `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure`; the D9.6 notebook-markdown cell-labels closure is CURRENT (D1–D9 + D9.6 boundary correction complete, superseded by it) |
| D9.6 notebook-markdown cell-labels closure (current) | **Notebook-navigation refinement on top of the D9.6 Kaggle/GitHub boundary correction.** NOTHING scientific, NOTHING in production/runtime code, and NOT the Kaggle/GitHub boundary changed: 11 exact Markdown navigation cells (`pilot-step-00..10-*md`, e.g. Step 04 model-preflight, Step 08 STOP boundary, Step 09 launch, Step 10 resume) were inserted between the (byte-identical, unchanged) 16 executable code cells in `notebooks/pilot_exec_01.ipynb` so Kaggle's Table of Contents names every operational stage and a visible pre-launch STOP boundary guards `pilot-launch`. New regression tests in `tests/integration/test_pilot_notebook_contract.py` (TestMarkdownNavigation, TestCodeCellsUnchangedFromBaseline, TestBundledNotebookParity) and `tests/integration/test_pilot_deployment_bundle.py` (TestPilotBundleKeepsMarkdownNavigation); notebook diff 126 insertions / 0 deletions; code cells compile 16/16; RED-to-GREEN established. The boundary correction carries forward unchanged: Kaggle launch and resume NEVER contact GitHub (no `git ls-remote`, no token, no `GIT_*`); `validate_pilot_launch_authorization` (pure local evidence: preflight JSON, sdpa kernel policy, mandatory generation-deadline canary) is the ONLY pre-command gate and is wired into BOTH `pilot-launch-cell` AND `pilot-resume-cell`; the stable `v0.9.22-pilot-exec-ready` tag is locally verified against the owner-controlled, locally verified source commit after real preflight passes. Full suite **2538 passed / 33 skipped / 0 failed**. FROZEN via the two-pass finalizer (`--verify-source-provenance`), 0 mismatches, idempotent (stable code/data/repository-snapshot/transport manifest hashes unchanged from D9.6; notebook_manifest_sha256 NEW `9d3edac4c20c00ab73a1ecda10d52322a5c57756820ed03f3a6162615e19adb6`; deployed bundle notebook SHA `6720293b922e06a80ecdc44a6d16e5eb12cc777d23c24a7076d005872d7aba68`) → **SOURCE COMMIT `478261ff595d3d64ed9d5bab32d1cc90d7dabd77`** (build id `478261f`); exact artifact `edae1b7e5be7ebab642d1e3c068dda3842a8061b8b04ab84c027d43a38dc8c4a` (+ sidecar); exact fresh-extraction bundled dry-run **48/48** (every record + `source_identity.json` == `478261f…`). **Prior D9.6 artifact `03d8d0ae…` (source `6ff1c93…`), D9 (`913e8065…`) and D8 (`02d16ca2…`) are SUPERSEDED; do not upload either. Never resume `exp-20260828-151335` (0 accepted RunRecords).** |
| D9.6 boundary correction (PRIOR, superseded by the notebook-markdown cell-labels closure) | **Prior D9.6 Kaggle/GitHub boundary correction on top of D9.** The D9.5 remote tag-peel launch gate is REMOVED; Kaggle launch and resume NEVER contact GitHub (no `git ls-remote`, no token, no `GIT_*`); `validate_pilot_launch_authorization` (pure local evidence: preflight JSON, sdpa kernel policy, mandatory generation-deadline canary) is the ONLY pre-command gate and is wired into BOTH `pilot-launch-cell` AND `pilot-resume-cell`; the stable `v0.9.22-pilot-exec-ready` tag is locally verified against the owner-controlled, locally verified source commit after real preflight passes. Genuine RED: the D9.5 baseline left 10 boundary-test failures; D9.6 closes all 10. GREEN: focused boundary + notebook/finalizer/provenance suites green; full suite **2538 passed / 33 skipped / 0 failed**. FROZEN via the two-pass finalizer (`--verify-source-provenance`), 0 mismatches, idempotent `→` **D9.6_SOURCE_COMMIT `6ff1c93ed355b6dc73fa3ebd18ba6079ace39ab6`**; exact artifact `03d8d0ae37b995a362ee90c53a1851588ad024f13ead033814399210ce54dfc4` (+ sidecar); exact fresh-extraction bundled dry-run **48/48** (every record + `source_identity.json` == `6ff1c93…`). SUPERSEDED by the notebook-markdown cell-labels closure — do not upload the old artifact. |
| D9 closure (PRIOR, superseded by D9.6) | **In-flight workflow-deadline heartbeat + eager model init + a remote tag-peel gate + freeze recovery closure (gate removed by D9.6).** D9.1 `_WorkflowDeadlineHeartbeatStoppingCriteria` (transformers-compatible stopping criterion, `kaggle_qwen_backend.py`) is polled at EVERY decode step and stops generation with `finish_reason="timeout"` the moment the injected run guard (`lambda: not budget.timed_out`) first returns false — an in-flight generation can never cross the 600 s deadline; bounded 30 s liveness heartbeats (`GENERATION_RUNNING` / `GENERATION_STOPPED reason=workflow_deadline`) prove a long synchronous decode alive (cooperative step-boundary stop, never a thread kill). D9.2 mandatory real-Qwen generation-deadline canary (`run_generation_deadline_probe`): deterministic counter guard fails closed after 3 criterion checks, proving the deadline (NOT EOS/length) target-side with `completion_tokens` in `[1, 8]`; preflight + `validate_pilot_launch_authorization` both fail closed through `_generation_deadline_probe_errors` (mock backends omit it; a real launch ALWAYS requires it). D9.3 eager shared-model init (`initialize()` before `t_start`/any `RUN_START`): one-time Qwen load outside the first run's scientific timing/token budget; failure = engineering blocker, 0 RunRecords, exit 1. D9.4 per-run cooperative guard install on strategy AND shared backend (`_apply_model_call_guards`). D9.5 no-shell bounded remote annotated-tag-peel launch gate (`verify_remote_annotated_tag_peel`, wired into `pilot-launch-cell` AND `pilot-resume-cell`) + interrupt-safe process-group terminate→kill→reap. Genuine RED: D8 baseline 17 failures; GREEN: focused 38/38 + green D8 closures; full suite **2532 passed / 33 skipped / 0 failed**. Freeze recovery (3 orphan D8 scratch copies deleted after authorized checks; anchors refreshed) → **D9_SOURCE_COMMIT `9ea02b35d58a3e4ef2d0d5d980e44fa53d8c079d`**; finalizer FROZEN 0 mismatches, idempotent. Exact artifact `913e8065a384effa2cf6b6a69f11e5840506644873fa54764c3cbe8ee5406d48` (+ sidecar); exact final-artifact dry-run **48/48** (every record + `source_identity.json` == `9ea02b3…`), canonical validator PASS; focused notebook/finalizer/provenance **165/165**. **D8 is REJECTED for Pilot launch (the real Pilot exposed the in-flight timeout/heartbeat defect D9 closes); never resume `exp-20260828-151335` (0 accepted RunRecords).** |
| D8 closure (prior, SUPERSEDED by D9) | **Dry-run token-schema + launch-auth evidence closure.** Prove + close the `RunRecordData` token-schema drift: a real 48-record CLI dry-run writes nested `token_usage` (`prompt/completion/total`), `total_workflow_model_calls` / `total_workflow_tokens`, phase `selection|regeneration|repair` `_model_calls` / `_total_tokens`, and status `succeeded` — NEVER a top-level `total_tokens` (the pre-D8 bundled dryrun-cell read a fabricated top-level field, so its old 48-cell gate was a **false green**, proven to PASS real records via the fail-open `or 0` check). D8.1 canonical `validate_pilot_dryrun_evidence` + `_collect_dryrun_evidence_errors` with strict `_expect_zero_int`; `validate_pilot_launch_authorization` refactored onto the same collector. D8.2 bundled `dryrun-cell` calls the canonical validator (`expected_model_identity="dry-run:mock"`) and prints only summary-backed totals. D8.3 GQA per-device display reads real fields (device/passed/gpu/cc/heads/qkv/out), not the fabric `.get('available')`. Genuine RED: 39 unit tests + 1 false-green proof failed pre-D8.1. GREEN: focused 40/40; contract+bundle 136/136; full suite **2492 passed / 33 skipped / 0 failed**. Do NOT upload the D8 artifact `02d16ca2…`. |
| Fix set (Tasks A–F) | Task A explicit `attn_implementation="sdpa"` at from_pretrained; Task B fail-closed CUDA generation inside `sdpa_kernel([FLASH_ATTENTION, EFFICIENT_ATTENTION])` (no math/eager fallback; missing torch.nn.attention API on CUDA fails closed); Task C canonical attention evidence (`requested/effective_attn_implementation`, `sdpa_kernel_policy=flash_or_efficient_no_math`) persisted in preflight JSON + rendered in the human table + enforced by the fail-closed `attention_policy` check and pilot launch authorization; Task D corrected OOM diagnosis (long-prompt OOM reports prompt-prefill evidence + free GiB, never advises completion-cap reduction); Tasks E/F regression-guard prior memory fixes and the unchanged 12000/64 gate. RED/GREEN proven: 12 backend + 18 preflight contract tests failed against v0.9.21 code before the fix; full suite **2407 passed / 33 skipped / 0 failed**; dry-run pilot 48/48 (unique IDs, 0 model calls, 0 tokens) |
| Accepted release | `v0.9.21-pilot-exec-ready` @ annotated tag peel == artifact source commit == merge `e308047c9c05f38316d80ce565bac1b51d105bfa`; archive SHA-256 `62e377467e225d336cbcaa70a2c610b5080e329e1a4e6578fbcbdc1af7dbee40`; trust/provenance 0 mismatches; target-shaped Gates 1-3 + full preflight GREEN (runs 32692489617 / 32694137255) — **superseded as launch candidate by the v0.9.22 attention closure; its repository/per-cell fixes remain VALID and are carried forward** |
| v0.9.22 stable tag | **DOES NOT EXIST YET.** Per the one-shot flow: build the exact candidate artifact from the merge commit → run the fresh Kaggle model preflight ONLY (same 12k target, same 64-token probe) → only on PASS create `v0.9.22-pilot-exec-ready`. If the Kaggle proof FAILS, return to the SAME v0.9.22 task (never spawn v0.9.23) |
| Real Pilot status | **NOT STARTED** (no 48-cell launch while untagged) |
| Exact next action | **D1–D9.6 COMPLETE.** Upload only exact D9.6 notebook-markdown cell-labels artifact `edae1b7e5be7ebab642d1e3c068dda3842a8061b8b04ab84c027d43a38dc8c4a` from source/future tag target `478261ff595d3d64ed9d5bab32d1cc90d7dabd77` (trust/provenance 0 mismatches, FROZEN; full suite 2538/33/0; exact-artifact dry-run 48/48). Run the model-preflight-only proof (repository preflight + heartbeat, Qwen 14B BNB-NF4 load, GQA microprobe, **generation-deadline canary**, short probe, 12k/64 probe); tag `v0.9.22-pilot-exec-ready` at `478261f…` only after ALL PASS; do not launch 48 cells while untagged. Prior D9.6 `03d8d0ae…`/`6ff1c93…` SUPERSEDED (do not upload), as are `02d16ca2…` (D8), `913e8065…` (D9), `e0a64937…` (D7), `ce40b330…` / `f72ecda…`. Never resume rejected `exp-20260828-151335`. |
| Per-cell validation runtime seam | **CLOSED and executable after D7.** Generated-workspace validation uses live AST `--validation-python` mappings for Todo/django CMS/Saleor, carries the frozen env into `FunctionalValidator`, and passes live `--validation-timeout 1800` on launch and resume (separate from `--timeout 600`). Exact canonical/fresh-bundle AST and newline tests prevent text/comment false greens. Target proof remains Saleor full primary exit 0 in 941.42s < 1800s (CI run 32692489617). |

Frozen Pilot matrix (unchanged, pre-registered in
`docs/PILOT_EXEC_01_EXECUTION_CONTRACT.md`, DECISION_LOG D025):

- Model: `Qwen/Qwen2.5-Coder-14B-Instruct`, quantization `bnb-nf4`, temperature 0
- Timeout: 600 s uniform per run (do NOT raise), max 3 attempts (initial + 2 repairs),
  max completion 4096 tokens/call, workflow token cap 0 (unlimited)
- 12 scenarios × 2 strategies (`iterative_repository_agent`, `selective`)
  × 2 repetitions = **48 cells**
- Repositories: Todo / django CMS / Saleor at pinned SHAs

## 2. Research goal + frozen protocol

Working paper: *"Don't Regenerate What Hasn't Changed: Selective Regeneration
for Token-Efficient LLM-Driven Software Evolution."* The benchmark measures
whether dependency-aware selective regeneration matches full-scope and agentic
regeneration on correctness while reducing regenerated artifacts, tokens,
calls, and time.

Research Protocol **v1.0 is FROZEN** (`docs/FINAL_RESEARCH_PROTOCOL.md`,
`PROTOCOL_VERSION.md`). No post-hoc scenario/metric changes. Ground Truth is
evaluation-only and post-hoc. Failed runs stay visible. Smoke evidence
(complete/accepted: `exp-20260808-222843` T600 Full-9, 2 successes /
7 scientific failures / 0 engineering blockers) is non-publication evidence.
Pilot findings are descriptive; confirmatory claims require the main study.

## 3. Exact frozen Pilot scenario IDs (12)

| Repository | Scenario IDs |
|---|---|
| todo | `todo-loc-001`, `todo-loc-002`, `todo-mod-004`, `todo-cross-007` |
| djangocms | **`djangocms-mod-005`**, `djangocms-loc-002`, `djangocms-mod-004`, `djangocms-cross-007` |
| saleor | `saleor-loc-001`, `saleor-loc-002`, `saleor-mod-004`, `saleor-cross-007` |

Note: `djangocms-mod-005` replaced `djangocms-loc-001` before any Pilot result
(DA-07 amendment: `djangocms-loc-001` was objectively infeasible at pinned
revision `0f633fc` because `PageContent` already has `meta_description`). The
scenario list lives in `configs/pilot.yaml` and must match
`PROFILES["pilot"]` exactly (parity contract test).

## 4. Release history (chronological, newest last)

| Release | Status | Reason |
|---|---|---|
| v0.9.1–v0.9.10 | historical execution-ready points | superseded as newer Kaggle blockers were closed (service bootstrap, transport encoding, root-safe PostgreSQL, Redis fallback, no-pip envs, release trust gate) |
| v0.9.11 | REJECTED FOR LAUNCH | internally-valid artifact, but the immutable tag did not contain the deployed re-frozen notebook (tag peel `8801304` lacked notebook landed only in post-tag `b87aa49`) |
| v0.9.12 | historical (GOOD) | fail-closed `source_commit` git-tree provenance gate introduced (`validate_source_commit_provenance`) |
| v0.9.13 | stale at upload time | superseded |
| v0.9.14 | REJECTED | artifact notebook provenance did not match immutable tag notebook |
| v0.9.15 | REJECTED FOR ACCEPTED PILOT LAUNCH | release finalization/artifact not completed (dist still v0.9.14; code-manifest SHA stale; single-parent commit) |
| v0.9.16 | RELEASE-ONLY CLOSURE | no production behavior changes; notebook anchors corrected |
| v0.9.17 | REJECTED FOR ACCEPTED PILOT LAUNCH | tag/source-commit provenance mismatch (tag peel `28a18e6…` != artifact source_commit `adf72d4…`); the PGDG bootstrap fix itself was GOOD |
| v0.9.18 | historical (release-only) | provenance/docs correction only; no scientific or production code changes |
| v0.9.19 | REJECTED FOR PILOT LAUNCH | PostgreSQL admin/application bootstrap + partial recovery closure; artifact internally GREEN (trust/provenance 0 mismatches) but the real Kaggle session failed at the Saleor fast capability gate (Pytest exit 5, no tests collected) |
| v0.9.20 | superseded for Real Pilot launch | Saleor preflight root-cause closure (exact fast-gate argv, false-green removal); internally trustworthy and target-shaped no-model preflight GREEN (run 32676588800), but an independent audit found the per-cell validation runtime parity blockers B1/B2/B3 — closed in v0.9.21 |
| v0.9.21 | accepted release — superseded as launch candidate | per-cell validation runtime closure: explicit `--validation-python` interpreter routing (B1), frozen env into `FunctionalValidator` (B2), explicit `--validation-timeout 1800` on launch+resume (B3); target-shaped Gates 1–3 + full no-model preflight GREEN (runs `32692489617` / `32694137255`); trust/provenance 0 mismatches; dry-run 48/48. Real Pilot rejected BEFORE LAUNCH at the real 12k attention-prefill OOM; repository/per-cell fixes remain VALID and are carried forward |
| **v0.9.22 candidate (D9.6, CURRENT)** | **CURRENT — REAL 2x T4 PROOF PENDING, NO TAG YET** | v0.9.22 long-context attention memory closure (Task A–F) plus D1–D6 GQA microprobe/notebook/export closure, D7 validation-argv executability, D8 dry-run token-schema + launch-auth, **D9 in-flight deadline heartbeat + eager model init + freeze recovery**, **D9.6 Kaggle/GitHub boundary correction**, and **D9.6 notebook-markdown cell-labels closure** (11 exact Markdown navigation cells `pilot-step-00..10-*md` + visible pre-launch STOP boundary between the byte-identical 16 executable code cells; new TestMarkdownNavigation/TestCodeCellsUnchangedFromBaseline/TestBundledNotebookParity/TestPilotBundleKeepsMarkdownNavigation regression tests; nothing scientific/runtime/boundary changed): SOURCE COMMIT `478261ff595d3d64ed9d5bab32d1cc90d7dabd77` (build id `478261f`; supersedes `6ff1c93…`), artifact SHA-256 `edae1b7e5be7ebab642d1e3c068dda3842a8061b8b04ab84c027d43a38dc8c4a` (+ sidecar), finalizer FROZEN 0 mismatches/idempotent, full suite **2538/33/0**, exact-artifact dry-run 48/48 (all records == `478261f…`); the launch/resume cells never contact GitHub. Scientific contract unchanged. **Prior D9.6 (`03d8d0ae…`/`6ff1c93…`), D8 (`02d16ca2…`) and D9 (`913e8065…`) are SUPERSEDED (D8 rejected for launch; never resume `exp-20260828-151335`).** Stable tag `v0.9.22-pilot-exec-ready` ONLY after the real 2x T4 GQA microprobe + generation-deadline canary + short + 12k PASS at `478261f…`. |

## 5. Recurring errors → permanent guards

Every guard below exists because a real failure happened. Never remove or
weaken one without an explicit new audit.

1. **Tag/source-commit mismatch** (v0.9.11, v0.9.17 rejected) → create the
   annotated tag ON the accepted artifact source commit; run
   `validate_source_commit_provenance` BEFORE tagging; post-tag docs/evidence
   commits are never tag targets.
2. **Stale "current" docs contradicting reality** → this file is authoritative;
   reconcile all state docs whenever truth moves (see Source-of-truth below).
3. **Workspace contamination across scenarios** (Full-9 `exp-20260807-205422`
   rejected) → exact reset from the immutable snapshot before EVERY matrix run
   (`_reset_workspace_source_from_snapshot`, fixed by `7f2a450`).
4. **Kaggle `venv`+`ensurepip` failure** → repository envs are provisioned
   WITHOUT pip (`--without-pip` + host pip bootstrap; v0.9.9 helper
   `scripts/pilot_kaggle_repo_envs.py`).
5. **Combined apt install abort** (`valkey-server` missing) → probe candidates
   individually via `apt-cache policy`; install EXACTLY ONE package per
   `apt-get install`; fail closed if none works (v0.9.8).
6. **PostgreSQL refuses root** → run the server lifecycle under the unprivileged
   `postgres` OS account when the notebook uid is 0; fail closed if absent;
   never fall back to root (v0.9.7). v0.9.19 additionally removed the implicit
   Saleor DB default from `_psql`, proofs use `db="postgres"`,
   `SHOW data_directory` protects partial recovery, and the Saleor DB is
   created BEFORE any application DB connection.
7. **Dependency drift OOM** (transformers 5.0.0 materialized BF16 before NF4) →
   pin `transformers==4.57.6`; fail-closed version check before load;
   `low_cpu_mem_usage=True`.
8. **GPU0-only VRAM check** → read VRAM on EVERY visible GPU; minimum-free gate
   ≥ 2.0 GiB per GPU (`GpuVramSnapshot`).
9. **CRLF/LF byte drift on Windows checkouts** → `.gitattributes` LF pins +
   LF normalization inside bundle manifests and the provenance gate. Keep it.
10. **Kaggle reserved/unsafe archive names** → `kaggle_transport` reversible
    ZIP encoding + mandatory pre-upload validator (`v0.9.4`/`v0.9.5`).
11. **Saleor `[tool.uv] package=false` import-probe failure** → health probes
    MUST run with `cwd = pristine staged repository root` (v0.9.11 fix; GOOD).

## 6. Git / release invariants

- Immutable tags are NEVER moved, deleted, or recreated.
- Artifact source commit MUST equal the immutable release tag peel.
- Non-fast-forward merges into `main` (no direct pushes of feature work);
  force-push to `main` is prohibited.
- No commit/push/merge/tag/reset/stash unless explicitly requested by the task.
- Stable tags only after successful independent audits.
- Ground Truth stays evaluation-only; no success claims without real execution.
- `dist/pilot-kaggle-upload.zip` (+ `.sha256`) is THE upload artifact — rebuilt
  only by the builder/finalizer from tagged source, never hand-edited.

## 7. OpenCode working rules (summary)

- Validation order: `git diff --check` → Ruff (changed files) → mypy (changed
  production files) → compile check (changed files) → targeted pytest → full
  pytest only at final gates/shared interfaces → bundle rebuilds only when
  production code changed.
- Resources: no pytest-xdist by default; no watch mode/GPU/model downloads/
  clean rebuild; trim logs to first root cause (~120 lines).
- Context discipline: search before reading; do not read whole repo, generated
  code, datasets, or unrelated docs.
- Stop/Blocker Reporting Contract and Project Export Rule in root `AGENTS.md`
  apply to every mandatory stop.

## 8. Exact next action

1. ~~Phase 2 release mechanics (local)~~ **DONE:** non-ff merge → `main` @
   `4827045fce96eb4caa3645e3cf3c8434dca2a1a8` (pushed); notebook/deployment anchors frozen for
   planned `v0.9.22-pilot-exec-ready` via the idempotent two-pass finalizer with
   `--verify-source-provenance` (0 mismatches; freeze evidence `reports/pilot_notebook_trust_freeze.json`);
   exact candidate artifact built from the merge commit: `dist/pilot-kaggle-upload.zip`
   SHA-256 `9182ea2bb091f785ff325a1355caa5bb0f57283764215059092970bbd8014974` (+ sidecar verified);
   exact-artifact dry-run 48/48 succeeded / 48 unique IDs / 0 model calls / 0 tokens.
   **The stable tag still DOES NOT exist — do not create it before step 3 PASSES.**
   **SUPERSEDED by the candidate consistency closure (same day):** branch
   `fix/pilot-v0922-candidate-consistency-closure` non-ff merged → `main` @
   `ba08392552545baa15c10ae5db2e95ce7496a720` (pushed; NO scientific/runtime code delta — four
   stale release-test constants aligned, order-independent missing-SDPA-API test isolation,
   generated dry-run dirs removed, full suite 2407/33/0 with the expanded-artifact simulation
   re-enabled); anchors re-frozen at the new merge via the same finalizer (0 mismatches); exact
   candidate artifact REBUILT: `dist/pilot-kaggle-upload.zip`
   SHA-256 `3fd986262936972a6f12adbae21e844adef488dfd76ef0e4b2e6e434b2aa65b3` (+ sidecar verified);
   exact-artifact dry-run 48/48 succeeded / 48 unique IDs / repos 16/16/16 / strategies 24/24 /
   reps 24/24 / 0 model calls / 0 tokens / new source commit in every record.
   **SUPERSEDED first by D1–D6, then by the D7 executable validation-argv closure (2026-08-27):**
   D1 local repeat-KV (no fabricated `torch.nn.functional.repeat_kv`); D2 microprobe allocates
   Q/K/V per `cuda:<index>` + device sync + per-device finite/shape/device evidence (FLASH+EFFICIENT
   only); D3 `pilot-repo-preflight-cell` restored to a 210-element newline-preserving executable
   source (was an all-comment no-op) carrying microprobe + fail-closed `raise` + `_run_tee`;
   D4 `_run_tee` deadline enforced while child runs (terminate→kill→reap, bounded tail); D5 em-dash
   mojibake restored (0 mojibake); D6 export rebuilt only after final commit/push + fresh-extraction
   verified — **truthful status: local export verified, but push/origin parity (`origin ref == HEAD`)
   and the definitive post-push export remain PENDING until this branch is pushed.** Frozen
   scientific contract unchanged. Full suite **2441 passed / 33 skipped / 0 failed**;
   exact final-artifact dry-run **48/48**; exact artifact REBUILT: `dist/pilot-kaggle-upload.zip`
   SHA-256 `ce40b33019feba58d8cabeef2244a765e157cdba4288a9d9ea2eb186de46a24d` (+ sidecar verified) from
   source commit `f72ecda0e7dac10e81dae34daa6bb1610c94b9ee` (trust/provenance 0 mismatches, FROZEN).
D7 exact artifact: SHA-256 `e0a649375104b44d1de7bc5f39145f81bc21365a4380755e73cb1efb719390a8`
    from source/future tag target `3ebc75dad2f47c8985ce045bcdc8907ce2d52f3c`; full suite
    2442/33/0; exact dry-run 48/48; trust/provenance 0 mismatches, FROZEN. The D1–D6
    `ce40b330…` / `f72ecda…` artifact is SUPERSEDED and must not be uploaded.
    **SUPERSEDED once more by the D8 dry-run token-schema + launch-auth evidence closure
    (2026-08-28):** canonical `validate_pilot_dryrun_evidence` (strict nested token_usage +
    workflow/phase totals; strict `_expect_zero_int`; launch-auth single-source collector);
    bundled `dryrun-cell` calls the validator (`dry-run:mock`); GQA per-device display reads
    real fields. Genuine RED 39 unit + false-green proof; focused 40/40 + 136/136; full suite
    **2492/33/0**; exact final-artifact dry-run **48/48**. D8 exact artifact: SHA-256
    `02d16ca2c3a35969b32ac438e577f41198e376ba0ce9ee88757a07bd46f268ee` from source/future tag
    target `8f0b11953a4fe2990b7e6c680288be282b8a6b67`; sidecar verified; trust/provenance
    0 mismatches, FROZEN. The D7 `e0a64937…` / `3ebc75d…` artifact is SUPERSEDED and must
    not be uploaded.
    **SUPERSEDED twice more: by the D9 in-flight workflow-deadline heartbeat + eager model
    init closure (2026-08-29) and then by the D9.6 Kaggle/GitHub boundary correction (2026-08-29):** D9.1
    `_WorkflowDeadlineHeartbeatStoppingCriteria` stops a long synchronous Qwen decode at a
    step boundary with `finish_reason="timeout"` the instant the 600 s run budget elapses
    (30 s liveness heartbeats prove a decode alive — never a thread kill); D9.2 mandatory
    real-Qwen generation-deadline canary (`run_generation_deadline_probe`, `completion_tokens`
    in `[1, 8]`) required by preflight + launch authorization; D9.3 eager one-time model init
    outside the first run's timing/token budget; D9.4 per-run cooperative guard reinstall;
    D9.5 (REMOVED by D9.6) wired a no-shell bounded annotated-tag-peel launch gate into
    `pilot-launch-cell` and `pilot-resume-cell`; D9.6 removed that gate — launch and resume
    NEVER contact GitHub; `validate_pilot_launch_authorization` (pure local evidence) is the
    ONLY pre-command gate in BOTH cells; + interrupt-safe process-group cleanup. Genuine RED 17 (D8 baseline);
    full suite **2538/33/0**; focused
    notebook/finalizer/provenance **165/165**. Freeze recovery → **D9.6 notebook-markdown
    cell-labels exact artifact: SHA-256
    `edae1b7e5be7ebab642d1e3c068dda3842a8061b8b04ab84c027d43a38dc8c4a`** (+ sidecar verified)
    from source/future tag target `478261ff595d3d64ed9d5bab32d1cc90d7dabd77` (build id
    `478261f`; supersedes `6ff1c93…`/`03d8d0ae…`); finalizer FROZEN
    0 mismatches, idempotent; exact-artifact dry-run **48/48** (every record == `478261f…`).
    **D8 is REJECTED for Pilot launch** (the real Pilot exposed the in-flight
    timeout/heartbeat defect D9 closes); do not upload `02d16ca2…`. Never resume rejected
    `exp-20260828-151335` (0 accepted RunRecords).
2. Upload the EXACT D9.6 v0.9.22 candidate artifact (`edae1b7e5be7...`)) as ONE fresh Kaggle Dataset; attach
   the frozen Pilot notebook (`notebooks/pilot_exec_01.ipynb`) and Qwen 14B input; Internet ON;
   `HF_TOKEN` secret set; confirm mounted model path + HF results repo ID.
3. Run the **fresh Kaggle v0.9.22 candidate model preflight ONLY** (SHA-256 verify,
   identity/manifest verify, repository preflight + heartbeat, Qwen 14B BNB-NF4 load PASS,
   GQA microprobe PASS, **generation-deadline canary PASS**, short generation probe PASS,
   **12k long-context probe PASS with attention policy evidence**
   `requested=sdpa effective=sdpa kernel_policy=flash_or_efficient_no_math`). No 48-cell
   launch while untagged.
4. If the 12k probe PASSES → annotate `v0.9.22-pilot-exec-ready` at the tested source
    commit `478261ff595d3d64ed9d5bab32d1cc90d7dabd77` (locally verified against the owner-controlled source commit), push the tag, update docs, then launch the
   accepted 48-cell Pilot in a fresh session. If it FAILS → return to the SAME v0.9.22 task
   (never spawn v0.9.23).

## 9. Source-of-truth hierarchy

When documents disagree, trust in this order:

1. **This file** (`docs/AI_ACCOUNT_TRANSFER_HANDOFF.md`) — current snapshot.
2. `SYSTEM_STATE.md` → `## Current Truth` (top block only).
3. `AGENTS.md` → `## Release facts`.
4. Machine evidence: `reports/pilot_notebook_trust_freeze.json`,
   `dist/pilot-kaggle-upload/pilot_deployment_identity.json`,
   `configs/pilot.yaml`, `docs/PILOT_EXEC_01_EXECUTION_CONTRACT.md`.
5. Reports (`reports/*.md`) — detailed but partially HISTORICAL.
6. Everything else (README history blockquotes, TODO historical ledger,
   PROJECT_HANDOFF trail, DECISION_LOG entries) — HISTORICAL context.

Anything labeled HISTORICAL / SUPERSEDED anywhere else in the repository must
never be used to override items 1–4.
