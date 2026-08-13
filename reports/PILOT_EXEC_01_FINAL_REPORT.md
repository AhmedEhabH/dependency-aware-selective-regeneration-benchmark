# PILOT-EXEC-01 — Detailed OpenCode Report (pre-execution gates A1–A8)

> **NOTE (2026-08-13, LATEST):** superseded by the KAGGLE RESERVED-NAME
> TRANSPORT CORRECTION (branch `fix/pilot-kaggle-reserved-transport-name`,
> non-fast-forward merged to main, tagged `v0.9.5-pilot-exec-ready`). Kaggle
> rejected the v0.9.4 archive because its transport root `__kaggle_transport__`
> matches Kaggle's reserved `__name__` pattern (`^__.*__$`). Transport root is
> now `kaggle_transport` everywhere, and a mandatory pre-upload validator
> (`validate_archive_members_kaggle_ready`) scans EVERY ZIP member and fails
> closed on any unsafe-special-char or reserved-name component. No scientific
> inputs changed. Gates: notebook contract 28/28, deployment bundle contract
> 33/33 (targeted 61/61), full suite **2,125 passed / 33 skipped / 0 failed**,
> diff-check/ruff/mypy/compile clean. Deployment archive rebuilt from the
> exact tag: `dist/pilot-kaggle-upload.zip` + `.sha256` (archive SHA-256
> `7be899d1…`, deterministic). Final closure section appended below.

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

---

## FINAL CLOSURE — KAGGLE SERVICE BOOTSTRAP LAST-MILE CORRECTION (2026-08-13)

**Executor:** opencode (provider `opencode/big-pickle`, model `big-pickle`).

### Pre-Benchmark Validation

| Gate | Result |
|---|---|
| Dataset Validation | PASS (carried forward — zero data drift; 57 data files, manifest `8b859ecc…`, byte-identical to the v0.9.2 bundle) |
| Prompt Validation | PASS (carried forward — zero prompt drift; no scenario/prompt changes in the correction) |
| Pipeline Smoke Test | PASS (bundled exact 48-cell dry-run executes the full pipeline end-to-end on the tagged bundle) |
| Dry Run | PASS (48/48 terminal / 48 succeeded / 0 failed / 0 pending / 48 unique run IDs; profile `pilot`) |
| Integration Test | PASS (full suite **2,098 passed / 33 skipped / 0 failed / 0 errors**) |
| Metric Verification | PASS (carried forward — zero metric/evaluator drift; no evaluator/metric changes in the correction) |

### Independent audit

| Item | Verdict |
|---|---|
| Notebook ordering | PASS — `service-bootstrap-cell` is cell index 6, after `pilot-snapshot-verify-cell` (5) and before `pilot-repo-preflight-cell` (7) / `model-preflight-cell` (9) / `dryrun-cell` (10) / `pilot-launch-cell` (12); REQUIRED_CELL_ORDER contract enforced by tests |
| Service bootstrap correctness | PASS — fail-closed (RuntimeError stops before repository validation/model load on any failure), idempotent (port-open + proven frozen connection short-circuit; role/db created idempotently), topology matches `benchmark_data/manifests/pilot_validation_commands.yaml` (PostgreSQL 127.0.0.1:5433 user/pass/db `saleor`, Valkey/Redis 127.0.0.1:6379), `pg_config --bindir` preferred, private data dir `/kaggle/working/pilot_services/postgres`, apt-get non-interactive with loud offline failure |
| Repository validation isolation | PASS — OS service provisioning never touches the benchmark/model Python environment; django CMS/Saleor isolated envs untouched; no `pip install` of Saleor/django CMS deps into the model runtime |
| No scientific RunRecord before all preflights | PASS — `pilot-launch-cell` runs last; no real run executed; dry-run records are mock-only with `hardware_identity "dry-run:mock"` |
| Model identity 14B | PASS — `EXPECTED_MODEL_IDENTITY = "qwen:14b-instruct-v1:bnb-nf4:cfg-cc9474140d25"`, `KNOWN_MODEL = …/qwen2.5-coder/transformers/14b-instruct/1`, identity JSON model `Qwen/Qwen2.5-Coder-14B-Instruct` |
| bnb-nf4 | PASS — `QWEN_QUANTIZATION = "bnb-nf4"`; every launch/preflight passes `--qwen-quantization bnb-nf4`; FORBIDDEN_CODE_FRAGMENTS rejects `bnb-int8` |
| 600s timeout | PASS — launch cell `--timeout 600`; identity JSON `timeout_seconds 600` |
| 48-cell matrix unchanged | PASS — 12 scenarios × 2 strategies × 2 reps = 48; dry-run per-repo 16/16/16, per-strategy 24/24, per-rep 24/24; no `--max-runs` |
| Metrics/prompts unchanged | PASS — no `src/benchmark`, prompt, scenario, or metric files changed in the correction (diff limited to notebook + 2 test files + builder tag + docs) |
| No Ground Truth leakage | PASS — no evaluator/ground-truth data changed; evaluator is evaluation-only, frozen |
| Historical Smoke untouched | PASS — `kaggle_upload/` not in the change set; byte-identical |
| GitHub durability | PASS — branch pushed (`origin/fix/pilot-kaggle-service-bootstrap`), main pushed (`c0bcaa5..4fa6e1d`), tag pushed (`v0.9.3-pilot-exec-ready` on origin); local == remote |
| Docs consistency | PASS — all 10 authoritative docs reconciled to v0.9.3 current truth + v0.9.2 historical |
| Over-engineering | PASS — single self-contained fail-closed cell; no new abstractions/dependencies |
| Technical debt | PASS — no new debt; cell documented, contract-tested, deterministic |

### Exact artifact report

- Final main SHA: `4fa6e1dfb1a45782d9e5176ef6325405d848b70b`
- Feature commits: `d40feb2` (`feat(pilot): add fail-closed Kaggle service bootstrap cell…`) and `37486f8` (`docs(pilot): reconcile authoritative docs…`)
- Merge SHA: `4fa6e1dfb1a45782d9e5176ef6325405d848b70b` (non-ff `merge(pilot): Kaggle service bootstrap last-mile correction…`)
- `v0.9.3-pilot-exec-ready` dereference: annotated tag object `47a65efda99ec55b0abe4ec7abf79f0efe0ad8a9` → peeled commit `4fa6e1dfb1a45782d9e5176ef6325405d848b70b`
- Exact archive path: `dist/pilot-kaggle-upload.zip`
- Exact archive SHA-256: `27e9cd612b33ebc433dafb7a42b7ebe2149f560bc6b73f16b969d3031a6baae1`
- Sidecar: `dist/pilot-kaggle-upload.zip.sha256` → `27e9cd612b33ebc433dafb7a42b7ebe2149f560bc6b73f16b969d3031a6baae1` (matches)
- Notebook SHA-256 (git blob @ tag == bundled): `8378edf542bb0ed12b29bc5498fd8f5d0e550319154c59f7c097c2b032349089` (17 cells, incl. `service-bootstrap-cell`)
- Repository snapshot SHAs/hashes (from `repository_snapshot_manifest.json`, manifest SHA-256 `49d91d39435f7e6f2dbf7d15f1a59188aa059ebb16fb31094c7a1827fb62702c`):
  - todo (embedded): requested `b8a33e20bdaf5b329114273063fbe8d5aa66e9cf`, content_hash `f72bc9df58882261eb2a2724e358b477cf68ed9586821d0cd2d9d8a47829113f`, 24 files
  - djangocms: requested `0f633fc9fa213357f4202482aab2b0edad680f95`, content_hash `729b5f418ec79d06b20e6e78ce827d58cde6812622f6e600c63777457b05247e`, 1662 files
  - saleor: requested `e11a5557eff29fbb2eed36e6ff3cd0af08ab9e10`, content_hash `708d0a7bfeddb92a441e5d1d047ba6d5cdf373bdb9978a8d22ee4622055ccc73`, 4577 files
- Final full-suite counts: **2,098 passed / 33 skipped / 0 failed / 0 errors** (2026-08-13)
- Final bundled dry-run counts: **48/48 terminal, 48 succeeded, 0 failed, 0 pending, 48 unique run IDs** (profile `pilot`, source_commit `4fa6e1d`)

### Final state

PILOT-EXEC-01 GATE C READY
Real Pilot NOT STARTED

Next action: upload exact `dist/pilot-kaggle-upload.zip` + `dist/pilot-kaggle-upload.zip.sha256` as ONE Kaggle Dataset, attach the Pilot notebook + Qwen 14B model, enable Internet, configure `HF_TOKEN`, then run cells in order through target preflight. Only after all preflight gates pass may the real 48-cell cell be executed.

---

## FINAL CLOSURE — KAGGLE RESERVED-NAME TRANSPORT CORRECTION (2026-08-13, `v0.9.5-pilot-exec-ready`)

**Executor:** opencode (provider `opencode/big-pickle`, model `big-pickle`).
**Reason for this correction:** the v0.9.4 Pilot archive was rejected by Kaggle
because its transport root `__kaggle_transport__` matches Kaggle's reserved
`__name__` naming pattern (`^__.*__$`). The transport root is now
`kaggle_transport` everywhere (builder, notebook `transport-restore-cell`,
`kaggle_transport_path_map.json` contract, tests, docs).

**What changed (transport layer only, fully reversible):**

- `scripts/build_pilot_upload_bundle.py`: `TRANSPORT_BLOB_PREFIX =
  "kaggle_transport"`; `is_kaggle_safe_name` now ALSO flags reserved-name
  components (`^__.*__$`), so reserved-name canonical files (e.g.
  `data/__pilot__/magic.txt` in the hermetic fixture) are transported like
  unsafe-special-char files; `kaggle_unsafe_members` reports unsafe AND
  reserved members; a mandatory pre-upload validator
  (`validate_archive_members_kaggle_ready`) scans EVERY planned member and the
  written archive `namelist()` and fails closed with
  `KAGGLE PRE-UPLOAD VALIDATION FAILED - archive is NOT Kaggle-ready`;
  `FROZEN_SOURCE_TAG` → `v0.9.5-pilot-exec-ready`.
- `notebooks/pilot_exec_01.ipynb` (18 cells): `transport-restore-cell` restore
  paths updated to `kaggle_transport/` (3 lines). The cell still verifies the
  map hash against the identity, rejects traversal/collisions/missing/leftover
  blobs, restores EXACT original paths and bytes, removes `kaggle_transport/`,
  and prints `PILOT KAGGLE TRANSPORT RESTORE: PASSED` BEFORE any manifest or
  repository verification.
- Canonical upstream filenames are NEVER renamed or deleted. No scientific
  input changed (scenarios, prompts, metrics, model, quantization, timeout
  600, repair budget, repository pins, validation scope).

### Pre-Benchmark Validation

| Gate | Result |
|---|---|
| Dataset Validation | PASS (carried forward — zero data drift; 57 data files, manifest `8b859ecc…`, byte-identical to v0.9.4) |
| Prompt Validation | PASS (carried forward — zero prompt drift; no scenario/prompt changes in the correction) |
| Pipeline Smoke Test | PASS (bundled exact 48-cell dry-run executes the full pipeline end-to-end on the v0.9.5 tagged-rebuild bundle) |
| Dry Run | PASS (48/48 terminal / 48 succeeded / 0 failed / 0 pending / 48 unique run IDs; profile `pilot`) |
| Integration Test | PASS (full suite **2,125 passed / 33 skipped / 0 failed / 0 errors**) |
| Metric Verification | PASS (carried forward — zero metric/evaluator drift; no evaluator/metric changes in the correction) |

### Independent audit

| Item | Verdict |
|---|---|
| Kaggle-safety | PASS — `dist/pilot-kaggle-upload.zip` has 6396 members, **0 unsafe** under `^[A-Za-z0-9._/-]+$` and **0 reserved-name (`^__.*__$`) components**; exactly 50 transport blobs under `kaggle_transport/files/`; validator PASS on planned members AND written archive |
| Reversibility | PASS — extract + execute the real `transport-restore-cell`: 50/50 restored to EXACT original paths/bytes; `kaggle_transport/` fully removed; all five identity manifest hashes PASS; restored repo content hashes PASS (todo `f72bc9df…`, djangocms `729b5f41…`, saleor `708d0a7b…` — identical to v0.9.4); restored tree == canonical tree |
| Notebook ordering | PASS — `transport-restore-cell` after `pilot-archive-verify-cell` and BEFORE `pilot-identity-verify-cell`; REQUIRED_CELL_ORDER enforced by tests |
| Fail-closed guards | PASS — traversal/drive/`..` destinations, destination collisions, duplicate/missing blobs, leftover blobs, and reserved-name/unsafe ZIP members all rejected by the cell and by `TestPilotKaggleTransport` |
| Determinism | PASS — two identical tagged builds → byte-identical archives (SHA-256 `7be899d1…` both times); blob names content-hash-derived |
| Identity binding | PASS — `kaggle_transport_path_map_sha256` in identity == emitted map hash (`07036a36…`) |
| No scientific RunRecord before all preflights | PASS — `pilot-launch-cell` runs last; no real run executed; dry-run records are mock-only |
| 48-cell matrix unchanged | PASS — 12 scenarios × 2 strategies × 2 reps = 48; dry-run per-repo 16/16/16, per-strategy 24/24; no `--max-runs` |
| Metrics/prompts/model/quantization/timeout unchanged | PASS — no `src/benchmark`, prompt, scenario, metric, config, or model-identity change in the correction |
| No Ground Truth leakage | PASS — no evaluator/ground-truth data changed |
| Historical Smoke untouched | PASS — `kaggle_upload/` not in the change set; byte-identical |
| No upstream file rename/delete | PASS — transport is ZIP-only; canonical repo files kept exact names/bytes |
| Over-engineering | PASS — single deterministic encoding layer + one self-contained fail-closed restore cell + one mandatory validator |
| Technical debt | PASS — no new debt; transport contract-tested, deterministic, documented |

### Exact artifact report

- Feature commits: `189cc60` (`fix(pilot): replace reserved __kaggle_transport__
  root with kaggle_transport + mandatory pre-upload validator`, 8 files) and
  `99348d1` (`docs(pilot): reconcile authoritative docs to
  v0.9.5-pilot-exec-ready reserved-name transport correction`) on
  `fix/pilot-kaggle-reserved-transport-name`; local == remote at `99348d1`.
- Merge SHA `eb07b7b11d2e7b5ba11bddc71855ddfc6e1d3dab` (non-fast-forward);
  tag `v0.9.5-pilot-exec-ready` (annotated object
  `b99fe9b9f426fc3fe7b269c448d9737e3f20cd4c`) peels to the merge commit;
  archive SHA-256 `7be899d1398b7e7061dd98d7d8d710482bfe3f1f66f1663be26dce7de7e0997a`;
  sidecar `dist/pilot-kaggle-upload.zip.sha256` matches; final `created_utc`
  `2026-08-13T12:00:00+00:00`.
- Code manifest SHA-256 `99688e4e…` (byte-identical to v0.9.4); data manifest
  SHA-256 `8b859ecc…` (byte-identical to v0.9.4); notebook manifest SHA-256
  `052efe08…` (notebook content hash `8b0ef489…`, byte-identical to the git
  blob at the tag; 18 cells, incl. `transport-restore-cell` and
  `service-bootstrap-cell`); repository snapshot manifest SHA-256 `49d91d39…`
  (identical to v0.9.4).
- Transport path map SHA-256 `07036a36cd97daef48a39f6490bc055f58e87b336d849a4c1343e82a167cdbce` (50 exact-path entries).
- Final full-suite counts: **2,125 passed / 33 skipped / 0 failed / 0 errors** (2026-08-13)
- Final bundled dry-run counts (v0.9.5 tagged rebuild): **48/48 terminal, 48 succeeded, 0 failed, 0 pending, 48 unique run IDs** (profile `pilot`; per-repo todo 16 / djangocms 16 / saleor 16; per-strategy iterative_repository_agent 24 / selective 24)
- Tagged-rebuild acceptance: archive SHA `7be899d1…` (byte-deterministic across two identical builds), 6396 members / 0 unsafe / 0 reserved / 50 transport blobs, roundtrip restore 50/50, all five identity manifest hashes PASS, repo content hashes PASS (todo `f72bc9df…`, djangocms `729b5f41…`, saleor `708d0a7b…`), restored data tree == canonical data tree.

### Final state

PILOT-EXEC-01 GATE C READY (reserved-name-safe transport archive)
Real Pilot NOT STARTED

Next action: upload exact `dist/pilot-kaggle-upload.zip` +
`dist/pilot-kaggle-upload.zip.sha256` (rebuilt from `v0.9.5-pilot-exec-ready`)
as ONE Kaggle Dataset, attach the Pilot notebook + Qwen 14B model, enable
Internet, configure `HF_TOKEN`, then run cells in order through target
preflight. Only after all preflight gates pass may the real 48-cell cell be
executed.

---

## FINAL CLOSURE — KAGGLE FILENAME TRANSPORT CORRECTION (2026-08-13, `v0.9.4-pilot-exec-ready`)

> **SUPERSEDED** by the reserved-name transport correction on
> `v0.9.5-pilot-exec-ready` above (2026-08-13). `v0.9.4-pilot-exec-ready` is
> immutable and NOT moved; its archive is retained for reference only. Kaggle
> rejected the v0.9.4 upload because the transport root `__kaggle_transport__`
> matches the reserved `__name__` pattern `^__.*__$`.

**Executor:** opencode (provider `opencode/big-pickle`, model `big-pickle`).
**Reason for this correction:** the v0.9.3 Pilot archive was rejected by Kaggle —
50 ZIP member names from the pinned upstream repos (45 Saleor, 5 django CMS)
contain `[ ] & @ =`, which the Kaggle Dataset upload does not accept.

**What changed (transport layer only, fully reversible):**

- `scripts/build_pilot_upload_bundle.py`: ZIP member names restricted to
  `^[A-Za-z0-9._/-]+$` with NO path component matching the reserved Kaggle
  pattern `^__.*__$` (transport root `kaggle_transport`, replacing the
  rejected `__kaggle_transport__`); unsafe canonical repository files stored
  as `kaggle_transport/files/<content-hash-blob>`; exact-path map
  `kaggle_transport/kaggle_transport_path_map.json` (SHA-256 bound into
  `pilot_deployment_identity.json` as `kaggle_transport_path_map_sha256`);
  mandatory pre-upload archive validator scans EVERY ZIP member and fails
  closed on any unsafe-special-char or reserved-name component;
  `FROZEN_SOURCE_TAG` → `v0.9.5-pilot-exec-ready`.
- `notebooks/pilot_exec_01.ipynb` (now 18 cells): `transport-restore-cell`
  between `pilot-archive-verify-cell` and `pilot-identity-verify-cell` —
  verifies the map hash against the identity; rejects path traversal / drive /
  `..` destinations, destination collisions, missing blobs, and leftover
  blobs; restores the EXACT original paths and bytes; removes
  `kaggle_transport/`; prints `PILOT KAGGLE TRANSPORT RESTORE: PASSED`
  BEFORE any manifest or repository verification.
- Canonical upstream filenames are NEVER renamed or deleted. No scientific
  input changed.

### Pre-Benchmark Validation

| Gate | Result |
|---|---|
| Dataset Validation | PASS (carried forward — zero data drift; 57 data files, manifest `8b859ecc…`, byte-identical to v0.9.3) |
| Prompt Validation | PASS (carried forward — zero prompt drift; no scenario/prompt changes in the correction) |
| Pipeline Smoke Test | PASS (bundled exact 48-cell dry-run executes the full pipeline end-to-end on the STEP 5 transport bundle) |
| Dry Run | PASS (48/48 terminal / 48 succeeded / 0 failed / 0 pending / 48 unique run IDs; profile `pilot`) |
| Integration Test | PASS (full suite **2,119 passed / 33 skipped / 0 failed / 0 errors**) |
| Metric Verification | PASS (carried forward — zero metric/evaluator drift; no evaluator/metric changes in the correction) |

### Independent audit

| Item | Verdict |
|---|---|
| Kaggle-safety | PASS — `dist/pilot-kaggle-upload.zip` (STEP 5) has 6396 members, **0 unsafe** under `^[A-Za-z0-9._/-]+$`; exactly 50 transport blobs |
| Reversibility | PASS — extract + execute the real `transport-restore-cell`: 50/50 restored; `data_manifest` PASS (6296 entries, 0 errors); restored repo content hashes PASS (todo `f72bc9df…`, djangocms `729b5f41…`, saleor `708d0a7b…` — identical to v0.9.3); restored tree == canonical tree |
| Notebook ordering | PASS — `transport-restore-cell` after `pilot-archive-verify-cell` and BEFORE `pilot-identity-verify-cell`; REQUIRED_CELL_ORDER enforced by tests |
| Fail-closed guards | PASS — traversal/drive/`..` destinations, destination collisions, duplicate/missing blobs, leftover blobs all rejected by the cell and by `TestPilotKaggleTransport` |
| Determinism | PASS — blob names are content-hash-derived; identical inputs → byte-identical archive |
| Identity binding | PASS — `kaggle_transport_path_map_sha256` in identity == emitted map hash (`a5c1e2cb…`) |
| No scientific RunRecord before all preflights | PASS — `pilot-launch-cell` runs last; no real run executed; dry-run records are mock-only |
| 48-cell matrix unchanged | PASS — 12 scenarios × 2 strategies × 2 reps = 48; dry-run per-repo 16/16/16, per-strategy 24/24, per-rep 24/24; no `--max-runs` |
| Metrics/prompts/model/quantization/timeout unchanged | PASS — no `src/benchmark`, prompt, scenario, metric, config, or model-identity change in the correction |
| No Ground Truth leakage | PASS — no evaluator/ground-truth data changed |
| Historical Smoke untouched | PASS — `kaggle_upload/` not in the change set; byte-identical |
| No upstream file rename/delete | PASS — transport is ZIP-only; canonical repo files kept exact names/bytes |
| Over-engineering | PASS — single deterministic encoding layer + one self-contained fail-closed restore cell |
| Technical debt | PASS — no new debt; transport contract-tested, deterministic, documented |

### Exact artifact report

- Feature commits: `7d63d9f` (`fix(pilot): encode Kaggle-unsafe repository
  filenames in transport`) and `ed142f8` (`fix(pilot): keep notebook title cell
  byte-identical (ascii-safe dump)`) on `fix/pilot-kaggle-filename-transport`;
  local == remote at `ed142f8`.
- Merge SHA `96b6481a64ba76a74580f5a3d371c39e27df00ea`; tag
  `v0.9.4-pilot-exec-ready` (annotated object `b48537928d3313624fbdbba1a1a69709356a561f`)
  peels to the merge commit; archive SHA-256
  `be98be8d2f0696bf8e916afbee7e83dd4522594e24f8f9f7c4837e008aaf8a19`; sidecar
  `dist/pilot-kaggle-upload.zip.sha256` matches; final `created_utc`
  `2026-08-13T00:00:00+00:00`.
- Code manifest SHA-256 `99688e4e…` (byte-identical to v0.9.3); data manifest
  SHA-256 `8b859ecc…` (byte-identical to v0.9.3); notebook manifest SHA-256
  `8c13c671…` (notebook content hash `9f139c23…`, byte-identical to the git
  blob at the tag; 18 cells, incl. `transport-restore-cell` and
  `service-bootstrap-cell`); repository snapshot manifest SHA-256 `49d91d39…`
  (identical to v0.9.3).
- Transport path map SHA-256 `a5c1e2cbae309b89c3268fa177a7cd68bcef285f5a483e4354ba54ef982b875e` (50 exact-path entries).
- Final full-suite counts: **2,119 passed / 33 skipped / 0 failed / 0 errors** (2026-08-13)
- Final bundled dry-run counts (STEP 11 tagged rebuild): **48/48 terminal, 48 succeeded, 0 failed, 0 pending, 48 unique run IDs** (profile `pilot`; per-repo todo 16 / djangocms 16 / saleor 16; per-strategy iterative_repository_agent 24 / selective 24; per-rep 24 / 24)
- Tagged-rebuild acceptance (STEP 11): archive SHA `be98be8d…`, 6396 members / 0 unsafe / 50 transport blobs, roundtrip restore 50/50, `data_manifest` 6296 entries / 0 errors, repo content hashes PASS (todo `f72bc9df…`, djangocms `729b5f41…`, saleor `708d0a7b…`), restored data tree == canonical data tree.

### Final state

PILOT-EXEC-01 GATE C READY (transport-safe archive)
Real Pilot NOT STARTED

Next action: upload exact `dist/pilot-kaggle-upload.zip` +
`dist/pilot-kaggle-upload.zip.sha256` (rebuilt from `v0.9.4-pilot-exec-ready`)
as ONE Kaggle Dataset, attach the Pilot notebook + Qwen 14B model, enable
Internet, configure `HF_TOKEN`, then run cells in order through target
preflight (transport restore + service bootstrap included). Only after all
preflight gates pass may the real 48-cell cell be executed.
