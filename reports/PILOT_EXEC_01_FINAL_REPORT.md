# PILOT-EXEC-01 — Detailed OpenCode Report (pre-execution gates A1–A8)

> **NOTE (2026-08-13):** the pre-execution gate report below is SUPERSEDED by
> the KAGGLE SERVICE BOOTSTRAP LAST-MILE CORRECTION (branch
> `fix/pilot-kaggle-service-bootstrap`, merged to main, tagged
> `v0.9.3-pilot-exec-ready`). The frozen Pilot notebook gained ONE fail-closed,
> idempotent `service-bootstrap-cell` (PostgreSQL `127.0.0.1:5433` role/db
> `saleor/saleor@saleor`; Valkey/Redis `127.0.0.1:6379` persistence-disabled;
> apt-get non-interactive, Kaggle Internet ON required) placed between
> repository snapshot verification and the repo-specific preflight — BEFORE any
> repository validation and model load. No scientific inputs changed. Gates:
> notebook contract 20/20 (incl. 5 new tests), deployment bundle contract
> 14/14, targeted pilot gates 77/77, full suite **2,098 passed / 33 skipped /
> 0 failed**, diff-check/ruff/mypy/compile clean. Deployment archive rebuilt
> from the exact tag: `dist/pilot-kaggle-upload.zip` + `.sha256`. The final
> post-merge audit report (exact artifact report) is appended below when the
> closure audit completes.

Per `08_DETAILED_OPENCODE_REPORT_TEMPLATE.md`.

## 1. Executor identity

- Provider: local toolchain
- Model: opencode/big-pickle (code execution agent)
- Build/session: `experiment/pilot-exec-01` work session, 2026-08-10
- Elapsed: gates A1–A8 executed in this session (full suite 750.99 s is the
  dominant single gate)

## 2. Git and release identity

- Branch: started `main`; created `experiment/pilot-exec-01` from main
  @ `72d041d92ee7854fcc1b1eea535e5aa150a7ed85`; merged back non-ff to `main`
- Starting HEAD: `72d041d92ee7854fcc1b1eea535e5aa150a7ed85` (clean tree)
- origin/main: matched local at start; now local == origin/main ==
  `544f7e4` (freeze report commit)
- Stable starting tag: `v0.9.0-pilot-ready` @
  `90a4282ac96328e26143b4f98d4bcf520c3c1e9b` (unchanged, NOT moved)
- Current working tree: clean, on `main`

## 3. Where we are

- Task: PILOT-EXEC-01 — Pilot deployment + pre-execution gates (A1–A8)
- Current gate: pre-execution gates COMPLETE (A1–A8); real execution
  (Gate C) prepared but NOT started
- Pilot started YES/NO: NO (no real Pilot model result exists)
- Near goal: exact real Pilot launch once the researcher supplies the Kaggle
  Dataset slug, mounted model path, and HF results repository ID
- Long goal: Pilot results audit → Main-study per-run budget freeze →
  research experiment → statistical analysis → paper evidence package

## 4. Exact artifact changes

- `scripts/build_pilot_upload_bundle.py` (new): reuses
  `scripts/build_upload_bundle.py` via importlib
  (`build_upload_bundle_pilot_reused`); redirects
  `KAGGLE_UPLOAD/KAGGLE_CODE/KAGGLE_DATA/KAGGLE_NOTEBOOKS` to the output root;
  sets `CANONICAL_NOTEBOOK_SOURCES=[]` (omits the Smoke notebook); refuses
  output root == `kaggle_upload`; deterministic zip (fixed `date_time` from
  `created_utc`); writes `pilot_deployment_identity.json`. Old behavior: n/a.
  Dependency impact: read-only reuse of the historical builder. Tests:
  `tests/integration/test_pilot_deployment_bundle.py`. Scientific semantics
  changed: NO.
- `tests/integration/test_pilot_deployment_bundle.py` (new, 12 tests): output
  isolation, historical bundle untouched, notebook omission, parity (critical
  files, 3 profiles, 12 scenarios), identity frozen contract, manifest hash
  match, no forbidden files, deterministic rebuild, bundled CLI import, exact
  bundled 48-cell dry-run with repo/strategy/rep counts. Scientific semantics
  changed: NO.
- `docs/PILOT_EXEC_01_EXECUTION_CONTRACT.md` (new): pre-registered 48-cell
  matrix, model/quantization/temp, per-run budget (600s / max 3 attempts / 4096
  completion tokens/call / cap 0), stage budget, resource reporting, post-Pilot
  decision, execution identity, frozen launch flags.
- `docs/PILOT_KAGGLE_RUNBOOK.md` (new): exact Kaggle launch/resume/preflight
  commands with explicit `--qwen-quantization bnb-nf4`.
- `docs/KAGGLE_EXECUTION_GUIDE.md` (updated): Pilot cells 7/8 corrected (no
  `--max-runs 2`; explicit quantization; Pilot bundle slugs), profile table
  strategy names, session-limits Pilot estimate removed (no pre-Pilot wall-time
  estimate), Pilot bundle upload section (2.4) added.
- `DECISION_LOG.md` (updated): D025 pre-registration entry.
- `SYSTEM_STATE.md`, `TODO.md`, `docs/START_HERE.md`, `docs/PROJECT_HANDOFF.md`,
  `docs/MASTER_IMPLEMENTATION_PLAN.md`, `reports/latest_phase_report.md`,
  `reports/PROJECT_HEALTH_REPORT.md` (updated): current-state truth
  (PILOT-EXEC-01 in progress, Pilot NOT started).
- `reports/PILOT_EXEC_01_DEPLOYMENT_FREEZE.md` (new): A8 freeze evidence.
- `.gitignore` (updated): `!reports/PILOT_EXEC_01_DEPLOYMENT_FREEZE.md`.

## 5. Deployment identity

- Canonical source SHA: `7efdbe60bb195b1f3ca5854fd98057e29559a510`
- Source tag: `v0.9.1-pilot-exec-ready` (peeled commit == canonical source SHA)
- Pilot bundle path: `dist/pilot-kaggle-upload/` (archive
  `dist/pilot-kaggle-upload.zip`)
- Pilot archive SHA-256: `dd9b4e291f0db16ebe20bf6e13075e78ad8021a5d8fd6aa8a60fc0ae722c7c50`
- Code manifest SHA-256: `196561bdc8754d97890724a33ff7bbd921016a95009bf68111d47bc5d4a31a3e`
- Data manifest SHA-256: `2abc877aa4649f1ff0aa1e6eeb6719b04724869140dc6184213e380965e9f295`
- Historical Smoke bundle changed YES/NO: NO (byte-identical)

## 6. Model identity

- Exact model: `Qwen/Qwen2.5-Coder-14B-Instruct`
- Exact model path: PENDING — researcher must confirm the Kaggle mounted
  model path (e.g. `/kaggle/input/<model-slug>`); not recorded until confirmed
- Quantization: `bnb-nf4`
- Transformers/BitsAndBytes/Torch/GPU: recorded by the Gate C runtime identity
  preflight on Kaggle (not run locally — KaggleQwenBackend unavailable locally)
- Model identity/fingerprint: `qwen:14b-instruct-v1:bnb-nf4:cfg-<12hex>` per
  the frozen model-aware identity scheme (recorded at preflight)

## 7. Pilot execution contract

- Scenarios: 12 (todo-loc-001, todo-loc-002, todo-mod-004, todo-cross-007,
  djangocms-mod-005, djangocms-loc-002, djangocms-mod-004, djangocms-cross-007,
  saleor-loc-001, saleor-loc-002, saleor-mod-004, saleor-cross-007)
- Strategies: `iterative_repository_agent`, `selective`
- Repetitions: 2
- Cells: 48
- Timeout: 600 s uniform
- Attempts: max 3 (initial + 2 repairs)
- Per-call completion tokens: 4096
- Workflow token cap: 0 (unlimited for Pilot, DA-09)
- HF persistence: `--hf-sync` with the exact HF results repo ID (recorded at
  launch)
- Experiment ID: `pilot-qwen14b-nf4-<source7>-<UTC timestamp>` (suggested;
  created fresh at real launch)

## 8. Gate evidence

Gate A1 — PASS: clean starting tree; branch `experiment/pilot-exec-01` created
from `origin/main`; `v0.9.0-pilot-ready` unchanged (`90a4282`).

Gate A2 — PASS (RED, non-destructive): historical bundled
`kaggle_upload/code/configs/pilot.yaml` has `model_name: qwen2.5-coder`,
strategies `agent`+`selective`, repo ref `main`; canonical
`configs/pilot.yaml` has `Qwen/Qwen2.5-Coder-14B-Instruct` + `bnb-nf4`,
`iterative_repository_agent`+`selective`, pinned SHAs. Historical bundled
`seven_arm_benchmark.py` lacks `build_repository_dependency_graphs`; canonical
defines it (`src/benchmark/...`). No historical file modified.

Gate A3 — PASS: `scripts/build_pilot_upload_bundle.py` implemented; targeted
builder tests green.

Gate A4 — PASS: `python -m pytest -q tests/integration/test_pilot_deployment_bundle.py`
→ 12 passed (21.22 s). Affected existing contracts:
`test_cli.py test_pilot_readiness.py test_pilot_multi_repo_input_contract.py
test_pilot_multi_repo_production_path.py` → 126 passed (incl. historical Smoke
identity `test_historical_smoke_bundle_matches_frozen_source_commit`).

Gate A5 — PASS: built `dist/pilot-kaggle-upload/`; bundled CLI
(`dist/pilot-kaggle-upload/code/seven_arm_benchmark.py`) with bundled data,
fresh namespace `%TEMP%\pilot_bundle_dryrun_a5` then re-verified at freeze
(`%TEMP%\pilot_bundle_dryrun_freeze`): 48 planned / 48 terminal / 48 unique IDs
/ 0 missing / 0 duplicate; todo 16, djangocms 16, saleor 16;
iterative_repository_agent 24, selective 24; rep1 24, rep2 24.

Gate A6 — PASS: feature-caused files ruff-clean, mypy-strict-clean (new
script), py_compile clean, `git diff --check` clean; full suite ONCE after
final executable/test state → **2,038 passed / 33 skipped / 0 failed**
(750.99 s; 0 failed / 0 errors).

Gate A7 — PASS: commit `988830a` (code/tests) pushed immediately; commit
`0c2b5cc` (pre-registration/runbook/docs) pushed immediately; local branch ==
remote branch (`0c2b5cc`). Independent-style audit re-ran deployment contract
12/12 + ruff + mypy + compile clean. Non-ff merge to main `7efdbe6`; pushed;
local main == origin/main. Tag `v0.9.1-pilot-exec-ready` created + pushed;
dereferences to `7efdbe60bb…` == bundle source commit. `v0.9.0-pilot-ready`
NOT moved.

Gate A8 — PASS: bundle rebuilt from the clean tagged/main tree
(`--created-utc 2026-08-10T00:00:00+00:00`); code/data manifests identical
(`196561bd…`/`2abc877a…`); archive SHA-256 `dd9b4e29…` written to
`reports/PILOT_EXEC_01_DEPLOYMENT_FREEZE.md`; rebuilt bundle dry-run 48/48.
The real Kaggle run must use this exact bundle.

## 9. Pre-Benchmark Validation

- Dataset Validation: CARRIED FORWARD (frozen 27-scenario dataset unchanged;
  Pilot data bundle manifest verified `2abc877a…`)
- Prompt Validation: CARRIED FORWARD (frozen prompts; no prompt change)
- Pipeline Smoke Test: CARRIED FORWARD (Scientific Smoke V2 accepted; not
  re-run — no runtime change)
- Dry Run: PASS — bundled exact 48-cell dry-run 48/48 (Gate A5 + A8)
- Integration Test: PASS — full suite 2,038/33/0 (Gate A6); deployment
  contract 12/12 (Gate A4)
- Metric Verification: CARRIED FORWARD (frozen metric/evaluator; no change)

## 10. Code audit

- Correctness: PASS — reuse of the tested historical builder with narrowly
  redirected constants; determinism proven by rebuild + identity tests
- Edge cases: PASS — output-root collision refusal, empty notebook source,
  fixed zip timestamps, fresh-namespace dry-run
- Deployment parity: PASS — historical `kaggle_upload/` byte-identical
- No Ground Truth leakage: PASS — unchanged data pipeline; Ground Truth
  evaluation-only (no change)
- No cross-repo contamination: PASS — unchanged graph/selection logic
  (PILOT-READY-01 fixed multi-repo contracts; not modified)
- Model identity: PASS — identity frozen in `pilot_deployment_identity.json`
- Smoke provenance: PASS — Smoke bundle not promoted to Pilot
- Over-engineering: PASS — smallest Pilot-specific builder; no duplicate logic
- Technical debt: pre-existing 5 mypy + 3 ruff items recorded as debt
  (unchanged, out of scope)

## 11. Real Pilot progress/results

- Expected scientific cells: 48
- Terminal: 0 (no real cell started)
- Succeeded: 0
- Scientific failures: 0
- Engineering blockers: 0
- Timeouts: 0
- Missing: 0
- Duplicates: 0
- Per repo / strategy / rep counts: n/a (no real records)
- Tokens/Calls/Repairs/Duration: n/a

No interpretation is made; no raw evidence exists yet. Mock dry-run records are
NOT scientific evidence.

## 12. Docs and GitHub durability

- Updated docs: DECISION_LOG.md (D025), SYSTEM_STATE.md, TODO.md,
  docs/START_HERE.md, docs/PROJECT_HANDOFF.md, docs/MASTER_IMPLEMENTATION_PLAN.md,
  docs/KAGGLE_EXECUTION_GUIDE.md, docs/PILOT_EXEC_01_EXECUTION_CONTRACT.md,
  docs/PILOT_KAGGLE_RUNBOOK.md, reports/latest_phase_report.md,
  reports/PROJECT_HEALTH_REPORT.md, reports/PILOT_EXEC_01_DEPLOYMENT_FREEZE.md
- Commits: `988830a` (code/tests), `0c2b5cc` (docs), `7efdbe6` (merge),
  `544f7e4` (freeze report) — all pushed
- Remote equality: local == origin/main == `544f7e4`
- Merge: non-ff to main `7efdbe6`
- Tags: `v0.9.1-pilot-exec-ready` created + pushed (peeled `7efdbe6`);
  `v0.9.0-pilot-ready` untouched
- Evidence hashes/hosts: archive `dd9b4e29…`, code manifest `196561bd…`,
  data manifest `2abc877a…` in `reports/PILOT_EXEC_01_DEPLOYMENT_FREEZE.md`;
  bundle in `dist/` (gitignored, hash-verified)

## 13. Final status

`PILOT-EXEC-01 BLOCKED`

- Pilot real execution started: NO
- Pilot real execution completed: NO
- Remaining blockers: real Pilot launch requires (1) the Kaggle Dataset slug
  chosen by the researcher for the frozen Pilot bundle (ONE dataset containing
  `pilot-kaggle-upload.zip` + `.sha256`, per §14), (2) the exact Kaggle mounted
  model path for Qwen2.5-Coder-14B-Instruct, (3) the exact HF results
  repository ID. All pre-execution gates (A1–A8) are complete, the launch
  instructions were reconciled to the one-bundle flow (§14), and the exact
  launch commands are frozen in `docs/PILOT_KAGGLE_RUNBOOK.md`.
- Next exact task: on researcher confirmation, upload the ONE-bundle dataset
  (frozen archive + sidecar), then run Gate C runtime identity preflight →
  SHA-256 verify → extract to `/kaggle/working/pilot_bundle` → identity/manifest
  verify → bundled 48-cell dry-run → model-load preflight
  (`--qwen-quantization bnb-nf4`) → one continuous 48-cell real Pilot launch.
- Near goal: exact real Pilot launch
- Long goal: Pilot results audit → Main-study budget freeze → research
  experiment → statistical analysis → paper evidence package

## 14. Gate C launch-instructions reconciliation (docs-only)

**Purpose:** remove the launch-documentation ambiguity that mixed two
deployment shapes before the real Kaggle Pilot. No scientific or protocol
input changed; this is launch-documentation reconciliation only.

**Old ambiguous flow (superseded):** the runbook told the operator to upload
`code/` and `data/` as two separate Kaggle datasets, but then expected
`pilot_deployment_identity.json` at the code-dataset root — while that file
belongs to the frozen bundle root, not `code/` — and the final report referred
to one Dataset slug while the runbook used two slugs.

**New one-bundle flow (canonical, frozen in `docs/PILOT_KAGGLE_RUNBOOK.md`):**

- ONE Kaggle Dataset for the frozen Pilot archive, containing at minimum
  `pilot-kaggle-upload.zip` and `pilot-kaggle-upload.zip.sha256`.
- No hand-reconstruction of code/data datasets.
- Inside the notebook: resolve the dataset mount → verify the ZIP SHA-256
  equals the frozen `dd9b4e29…` → extract to
  `/kaggle/working/pilot_bundle` → verify
  `pilot_deployment_identity.json` (task `PILOT-EXEC-01`,
  `v0.9.1-pilot-exec-ready`) → verify code/data manifests → define
  `PILOT_CODE=/kaggle/working/pilot_bundle/code`,
  `PILOT_DATA=/kaggle/working/pilot_bundle/data` → install from
  `$PILOT_CODE/requirements-kaggle.txt` → bundled 48-cell dry-run
  (`$PILOT_CODE/seven_arm_benchmark.py --dry-run --profile pilot
  --data-dir $PILOT_DATA --qwen-quantization bnb-nf4`) → model-load preflight
  (`--qwen-quantization bnb-nf4`) → real 48-cell Pilot launch.
- The model mount path and the HF results repo ID are still verified at
  runtime, never assumed.

**Files changed (docs only):** `docs/PILOT_KAGGLE_RUNBOOK.md`,
`docs/KAGGLE_EXECUTION_GUIDE.md`, `reports/PILOT_EXEC_01_FINAL_REPORT.md`,
`SYSTEM_STATE.md` (single clarifying bullet).

**Confirmations:**

- NO production code change.
- NO prompt/metric/scenario/model/quantization/timeout change.
- NO protocol/execution-contract change (frozen contract untouched).
- Tag unchanged: `v0.9.1-pilot-exec-ready` remains the immutable executable
  source tag (peeled `7efdbe60bb…`); no new tag.
- Bundle NOT rebuilt; `dist/pilot-kaggle-upload.zip` and its SHA-256
  `dd9b4e29…` unchanged.
- Full test suite NOT rerun; frozen bundle NOT moved.
- Real Pilot NOT started during this docs correction.

**Git:** shipped as commit
`docs(pilot): reconcile Gate C Kaggle bundle launch paths`, pushed immediately
to `main`; verified local main == origin/main at the end of this step.
