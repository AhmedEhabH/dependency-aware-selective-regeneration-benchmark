# V0922_D9_6_REAL_T4_PASS_STABLE_TAG_CLOSURE_REPORT

**Task:** PILOT-EXEC-01 — v0.9.22 D9.6 Real 2×T4 Preflight PASS + Stable-Tag Closure (independent audit + create/push `v0.9.22-pilot-exec-ready`)

**Date:** 2026-08-30

**Branch:** `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure`

**Status:** COMPLETE — real exact-artifact 2×T4 preflight PASSED; annotated stable tag `v0.9.22-pilot-exec-ready` CREATED and PUSHED; real Pilot NOT started.

## 1. Objective

Independently audit the real 2×T4 Kaggle evidence for the exact D9.6 artifact
`edae1b7e5be7ebab642d1e3c068dda3842a8061b8b04ab84c027d43a38dc8c4a`, and on full
PASS create + push the annotated stable tag `v0.9.22-pilot-exec-ready` at the exact
artifact source commit `478261ff595d3d64ed9d5bab32d1cc90d7dabd77`, update
docs/reports, prove local↔remote parity, and produce a verified project export —
**without** modifying any code/test/notebook/artifact/freeze/dataset/prompt/metric
and **without** launching the real 48-cell Pilot.

## 2. Evidence audited (Gate B)

Three files, SHA-256 recorded pre-extraction:
- `runs-2026-08-30-112728.zip` = `df8de87c8aab96c0a28792b0edfb67a271e23ef421b9b750b32901647e2b3de1`
- `pilot_bundle-2026-08-30-112733.zip` = `2b2de1123f94fc79253833257dbb1244e8ad2a3b67e4fe3ba28bb0e20131dcd8`
- `pilot-exec (12).ipynb` = `587323e663010d0c34e263cd8618c3e360fb346692e21c451d4bd83afa6ba957`

Extracted into a fresh temp audit area outside the repo
(`C:\Users\Ahmed\AppData\Local\Temp\opencode\pilot-exec-01-v0922\`); the canonical
`validate_pilot_dryrun_evidence` was executed against the extracted evidence.

## 3. Gate A (git safety) — FULL PASS

- Working tree clean; branch `fix/pilot-...`; HEAD == origin/HEAD == `6cde3758…`.
- `478261ff…` exists and is an ancestor of HEAD; tag absent locally+remotely pre-creation.
- Artifact + sidecar both == `edae1b7e5be7ebab642d1e3c068dda3842a8061b8b04ab84c027d43a38dc8c4a`.

## 4. Gate B (independent evidence audit) — FULL PASS

- **Artifact/identity:** expanded-mode sidecar proof matches the artifact SHA. Deployment identity
  (`pilot_deployment_identity.json`): source_commit `478261ff...`, source_tag
  `v0.9.22-pilot-exec-ready`, 48 cells, `Qwen/Qwen2.5-Coder-14B-Instruct`, `bnb-nf4`, 12 / 2 / 2.
  All five manifest hashes independently recomputed and matched: code `37e79950…`, data `8b859ecc…`,
  repository snapshot `49d91d39…`, transport path map `07036a36…`, notebook manifest `9d3edac4…`.
- **Repo preflight** (`repo_preflight.json`): `overall == PASS`; djangocms/todo/saleor primary all PASS;
  Saleor fast capability gate PASS; Saleor PostgreSQL (127.0.0.1:5433) and Valkey/Redis (127.0.0.1:6379)
  reachable.
- **T4 SDPA GQA microprobe** (notebook cell 12 full stdout): `all_passed=True device_count=2
  gqa_compatibility_mode=repeat_kv_sm75`; device 0 (`cuda:0`) passed=True Tesla T4 cc=7.5 heads
  40/8/8→40/40/40, Q/K/V + output on `cuda:0`, out_shape (1,40,68,128); device 1 (`cuda:1`) identical on
  `cuda:1`; "T4 SDPA GQA MICROPROBE: PASSED".
- **Model preflight** (`model_preflight.json`): `passed == true`; exactly 2 Tesla T4; `model_identity ==
  qwen:14b-instruct-v1:bnb-nf4:cfg-cc9474140d25`; requested/effective attention `sdpa`, kernel policy
  `flash_or_efficient_no_math`, GQA `repeat_kv_sm75`; short generation PASS (17 completion tokens);
  **generation-deadline canary PASS** (`deadline_fired==true`, `finish_reason==timeout`, 4 completion
  tokens); long-context probe PASS (12,044 prompt / 64 completion tokens, target ≥ 12000).
- **Exact-artifact dry-run** (`runs/dryrun_pilot_48`): canonical `validate_pilot_dryrun_evidence` PASS —
  48 records / 48 unique IDs / statuses all succeeded / repo 16-16-16 / strategies 24-24 / reps 24-24 /
  all model-call + token counters integer zero / source `478261ff...` + `v0.9.22-pilot-exec-ready` +
  build `478261f` + `dry-run:mock`. Experiment id `exp-20260830-112618`.
- **Launch boundary** (audited `pilot-exec (12).ipynb`, 35 cells): errors in cells 0–7 = none; the
  pilot-launch/resume/verify/export cells all `exec_count == None` (unexecuted); the only
  `run_records.jsonl` is the 48-record dry-run file; rejected `exp-20260828-151335` NOT present; the HF
  token value never appears (cell 20 only prints "retrieved and set in environment").
- **Launch authorization** `validate_pilot_launch_authorization`: all evidence-based checks PASS; local run
  failed only at "HF_TOKEN is missing or blank in the environment" (expected — local lacks the Kaggle
  secret; non-blocking since cell 20 confirms retrieval).

## 5. Gate C (stable tag create + push) — FULL PASS

- Annotated tag `v0.9.22-pilot-exec-ready` created at exactly `478261ff595d3d64ed9d5bab32d1cc90d7dabd77`
  (NOT at HEAD `6cde375…`).
- `git cat-file -t refs/tags/v0.9.22-pilot-exec-ready` = `tag`; local peeled target `^{commit}` ==
  `478261ff...`; tag object `fdcb409670e040a287811840ddbcab475816a7e5` == remote
  `refs/tags/v0.9.22-pilot-exec-ready` `fdcb4096...` (remote peels identically).
- Pushed to origin; verified with the configured authenticated origin credentials. **No anonymous/public
  readability probe** — GitHub stays private (owner-controlled source/release storage only; GitHub privacy
  is irrelevant to Kaggle execution).

## 6. What did NOT change

- **No code, tests, notebook, artifact, freeze, dataset, prompt, or metric changed.** No finalizer/rebuild
  run. The artifact REMAINS `edae1b7e5be7ebab642d1e3c068dda3842a8061b8b04ab84c027d43a38dc8c4a`.
- Runtime code unchanged → full suite remains the previously accepted **2538 passed / 33 skipped / 0 failed**
  (carried). Scientific contract unchanged; this remains v0.9.22 (never v0.9.23).
- The real 48-cell Pilot has **NOT** started.

## 7. Docs / decision log updated (Gate D)

- AGENTS.md, SYSTEM_STATE.md, TODO.md, README.md, docs/START_HERE.md, docs/PILOT_KAGGLE_RUNBOOK.md,
  docs/MASTER_IMPLEMENTATION_PLAN.md, docs/PROJECT_HANDOFF.md, docs/AI_ACCOUNT_TRANSFER_HANDOFF.md,
  reports/latest_phase_report.md, reports/PROJECT_HEALTH_REPORT.md — current-truth rewritten to the REAL
  2×T4 PASS + stable-tag closure; the D9.6 notebook-markdown cell-labels truth demoted to PRIOR TRUTH;
  required boundary markers preserved (Kaggle launch/resume never contact GitHub; stable tag owner-side +
  locally verified; GitHub privacy irrelevant to Kaggle; never resume `exp-20260828-151335`).
- DECISION_LOG.md — Decision D033 added.

## 8. Required truthful status

- The annotated stable tag **`v0.9.22-pilot-exec-ready` EXISTS and peels to
  `478261ff595d3d64ed9d5bab32d1cc90d7dabd77`** (tag object `fdcb4096…`, local == remote, pushed + verified
  with configured authenticated origin credentials).
- The artifact REMAINS `edae1b7e…8c4a`; no rebuild / no finalizer run for this closure.
- The real 48-cell Pilot has **NOT** started. The ONLY remaining operational step is, in the same still-live
  Kaggle session, to run **Step 8 "Pilot Launch — STOP Until Stable Tag Is Confirmed" / `pilot-launch-cell`**.
- Never resume `exp-20260828-151335` (zero accepted RunRecords). Prior artifacts `03d8d0ae…`/`6ff1c93…`,
  `02d16ca2…` (D8), `913e8065…` (D9), `e0a64937…` (D7), `ce40b330…`/`f72ecda…` remain SUPERSEDED (do not upload).
