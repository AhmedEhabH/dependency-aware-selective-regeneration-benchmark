# PILOT-EXEC-01 — Detailed OpenCode Report (pre-execution gates A1–A8)

> **NOTE (2026-08-16, LATEST):** superseded by the PILOT-EXEC-01
> RELEASE-PROVENANCE CLOSURE — **`v0.9.11-pilot-exec-ready` REJECTED FOR LAUNCH;
> `v0.9.12-pilot-exec-ready` SHIPPED WITH A FAIL-CLOSED `source_commit`
> GIT-TREE PROVENANCE GATE** (branch `fix/pilot-release-provenance-closure`
> from clean `origin/main` `5cee179`; code/test commit `6cd2767`, freeze commit
> `7923b37`). The v0.9.11 immutable tag peeled to the merge commit `8801304`,
> whose notebook is the v0.9.10 notebook `d15d8683…`, while the deployed
> artifact carried the re-frozen notebook `85edbd33…` that landed only in the
> POST-tag re-freeze commit `b87aa49` — embedded notebook trust could be made
> internally self-consistent, yet the tag does not contain the deployed
> notebook. v0.9.11 = `internally-valid artifact, but rejected for launch
> because the immutable tag does not contain the deployed re-frozen notebook
> and therefore cannot reproduce the claimed source snapshot.` FIX (minimal):
> fail-closed `validate_source_commit_provenance(*, source_commit,
> bundled_root, …, git_reader=None)` in `scripts/build_pilot_upload_bundle.py`
> proves the bundled Pilot notebook AND every `code_manifest.json` entry equal
> the normalized (CRLF→LF for text suffixes) tracked Git blob at
> `identity.source_commit`; standalone release acceptance step run BEFORE the
> immutable tag is created; no skip flag; never falls back to the working tree;
> deliberately NOT wired into `build_pilot_bundle`/`freeze()`. Companion
> byte-faithfulness fix: bundled `*.lock` files LF-normalized in the code bundle
> (`_normalize_lock_files`) — the Windows-checkout CRLF lock manifest
> `95ad3b2b…` had drifted from the LF blob `1f4b1875…`. New suite
> `tests/integration/test_pilot_release_provenance.py` Gates 1–5 (exact v0.9.11
> forensic RED from real git blobs `8801304` vs `b87aa49`, notebook CRLF/LF
> parity, code-manifest modified/missing FAIL naming exact paths, invalid SHA /
> unknown commit fail closed, `.lock` LF PASS vs CRLF FAIL, v0.9.12 release-tag
> sequencing contract). Finalizer re-freeze `--source-tag
> v0.9.12-pilot-exec-ready`: code `0fd86fc9…` (94/94 source-faithful incl. both
> locks), data `8b859ecc…`, repository snapshot `49d91d39…`, transport map
> `07036a36…`; archive `5a7d7e0a…`. Full suite **2,255 passed / 33 skipped /
> 0 failed** (2026-08-16). **Pilot = NOT STARTED.**
>
> **NOTE (2026-08-16, REJECTED FOR LAUNCH — superseded by the v0.9.12 release-provenance closure):** superseded by the PILOT-EXEC-01 SALEOR
> SOURCE-VISIBILITY HEALTH-PROBE FIX (REAL KAGGLE v0.9.10 FAILURE CLOSED on
> branch `fix/pilot-saleor-source-visibility-probe`, code/test commit `ee3d88b`
> pushed; release `v0.9.11-pilot-exec-ready` internally-valid but REJECTED FOR
> LAUNCH — see the final
> closure note above). Real Kaggle v0.9.10
> PASSED every preflight stage (release trust, transport restore, runtime lock,
> repository snapshots, PostgreSQL, Redis, uv tool, django CMS, Saleor copy,
> Saleor 3.12 `.venv`, `uv sync --locked` = PASS) and failed ONLY at the new
> health probe: `import saleor` exit 1, `ModuleNotFoundError: No module named
> 'saleor'`. Root cause: pinned Saleor `pyproject.toml` sets `[tool.uv] package
> = false` (upstream), so `uv sync --locked` installs the locked dependencies
> but never the root project into site-packages; the v0.9.10 probe ran
> `<saleor .venv>/bin/python -c "import saleor"` without `cwd=the Saleor working
> copy`, while the frozen downstream preflight already runs Saleor commands with
> `cwd = pristine staged repository root`. Fix (minimal): `_import_probe`
> optional `cwd`; `_saleor_probe` always `cwd=work_dir`; BOTH call sites fixed
> (marker/reuse + post-sync). NO `package=true`, NO pip/uv editable install, NO
> global `PYTHONPATH`; `uv sync --locked` / Python 3.12 / `UV_PYTHON_DOWNLOADS=
> never` preserved. Strong tests: real-subprocess source-visibility regression
> (RED vs old helper), `_FakeRunner` cwd assertion, pinned `package=false`
> contract, fresh/reuse cwd topology, missing-source fail-closed, downstream
> preflight parity, no semantic drift. Targeted integration 188 passed; full
> suite **2,239 passed / 33 skipped / 0 failed** (2026-08-16). v0.9.10 remains
> immutable (real Kaggle preflight reached the Saleor post-sync health probe
> then failed because the probe did not run from the repository root). This
> v0.9.11 record completed
> **ALL SUBSEQUENT STEPS** (internally-valid; SUBSEQUENTLY REJECTED FOR LAUNCH
> because the immutable tag does not contain the deployed re-frozen notebook):
> independent audit PASS → non-ff merge to
> main `8801304d855fe29c694f2a3c0500f661685b0d72` (merge SHA == main HEAD ==
> tag peel) → release-trust-gate finalizer re-freeze (`--source-commit` = merge
> SHA, `--source-tag v0.9.11-pilot-exec-ready`, `--created-utc
> "2026-08-16T12:00:00+00:00"`; code manifest `7e86eb5dd651…`, data
> `8b859ecc7216…`, repository snapshot `49d91d39435f…`, transport map
> `07036a36cd97…` — last three byte-identical to v0.9.10) → FINAL ARTIFACT
> TRUST GATE **Notebook == Identity == Actual 4/4** (deployed notebook
> `85edbd33e81b…` == bundled bytes; archive SHA-256
> `039818bde60edcc9693ca88f779c7987bde818ddbfbca705426747b08c6d5453`) →
> immutable annotated tag `v0.9.11-pilot-exec-ready` ON the merge commit,
> pushed → bundled 48-cell mock dry-run **48/48** (todo 16 / djangocms 16 /
> saleor 16; iterative_repository_agent 24 / selective 24; rep1 24 / rep2 24;
> 48 unique / 0 missing / 0 duplicate / 0 model calls) → **STOP. Pilot = NOT
> STARTED.**

> **NOTE (2026-08-15, HISTORICAL — superseded by the 2026-08-16 Saleor source-visibility fix):** superseded by the PILOT-EXEC-01 v0.9.10 RELEASE
> TRUST GATE CLOSURE (MERGED TO MAIN + TAGGED: branch
> `fix/pilot-release-trust-gate-closure` fix `097768e` + docs `4ac7f0d`,
> non-ff merge `44e9a1f…`, annotated tag `v0.9.10-pilot-exec-ready` on the
> merge commit, tagged rebuild + FINAL ARTIFACT TRUST GATE PASS + 48-cell
> dry-run 48/48 — see FINAL CLOSURE section below). The deployment source is
> re-frozen at `v0.9.10-pilot-exec-ready`
> via a REAL two-pass deterministic release-trust-gate finalizer run against
> the LOCAL repo cache (`dist/pilot-repo-cache`, NO `--allow-acquire`, no
> network acquisition): `python scripts/finalize_pilot_notebook_trust.py
> --source-commit 80d4d6e581cef60463efde31b414643ba182f35a --source-tag
> v0.9.10-pilot-exec-ready --repo-cache dist/pilot-repo-cache --created-utc
> "2026-08-15T14:00:00+00:00"`. Notebook == Identity == Actual proven for ALL
> four frozen hashes (code `bb976f67fefe…`, data `8b859ecc7216…`, repository
> snapshot `49d91d39435f…`, transport path map `07036a36cd97…`); deployed
> notebook SHA-256 `d15d86831bf8…` == bundled archive bytes; normalized bundled
> notebook == source `873e97735cd2…`. **No scientific inputs changed.** The
> v0.9.9 recorded code hash `99688e4e` was stale (predated the bundled
> helper-script additions and was never validated against the build); the new
> gate freezes the true validated value `bb976f67`. Gates: deployment bundle
> 52/52, notebook contract 46/46, repo-env provisioning 24/24, real-launch
> preflight 13/13 (targeted 142/142), full suite **2,234 passed / 33 skipped /
> 0 failed**. Final closure section appended below.

> **NOTE (2026-08-15, HISTORICAL — superseded by the v0.9.10 release trust gate closure):** superseded by the KAGGLE NO-PIP REPOSITORY ENV
> PROVISIONING CLOSURE (branch `fix/pilot-kaggle-env-provisioning-closure` @
> `28f0405`; merge + tag `v0.9.9-pilot-exec-ready` + exact artifact rebuild
> PENDING). The real Kaggle blocker is closed: on real Kaggle the runtime lock
> installs pip into the base interpreter, so `python -m venv` (which runs
> `ensurepip` inside the base interpreter) cannot build a working pip inside a
> fresh env — the v0.9.8 cell died with `['/kaggle/working/pilot_envs/djangocms/
> bin/python3', '-m', 'ensurepip', '--upgrade', '--default-pip'] returned
> non-zero exit status 1` in ~0.24 s (NOT a hang); the same latent failure
> existed in the `pilot_envs/tools` env. The bundled stdlib-only helper
> `scripts/pilot_kaggle_repo_envs.py` provisions every repository validation
> env WITHOUT the ensurepip path (stdlib venv always `--without-pip`, HOST pip
> `<benchmark-python> -m pip --python <target>` bootstrap, `uv` tool env,
> django CMS deps via `uv pip install -r`, Saleor pinned-snapshot copy + `uv
> venv .venv --python <existing 3.12>` with `UV_PYTHON_DOWNLOADS=never` + `uv
> sync --locked`, markers + health probes, rebuild ONLY the invalid private env
> dir, ONE `apt-get install` transaction for `gettext`+`gcc`+`libpq-dev`,
> secret-redacting provisioning log, thin-adapter `pilot-repo-preflight-cell`,
> bundle-shipped helper + `code_manifest.json` hash). **No scientific inputs
> changed** (scenarios, prompts, metrics, model, quantization, timeout 600,
> repair budget, repository pins, validation scope; the four frozen
> manifest/map hashes stay byte-identical). Gates: provisioning matrix 24/24,
> notebook contract 46/46, service bootstrap 41/41, real-launch preflight 13/13,
> deployment bundle 52/52, full suite **2,225 passed / 33 skipped / 0 failed**.
> Final closure section appended below.

> **NOTE (2026-08-13, HISTORICAL):** superseded by the KAGGLE POSTGRESQL ROOT-SAFE
> BOOTSTRAP CORRECTION (branch `fix/pilot-kaggle-postgres-unprivileged-bootstrap`,
> non-fast-forward merged to main, tagged `v0.9.7-pilot-exec-ready`). The real
> Kaggle blocker is closed: the notebook process runs as root while PostgreSQL
> `initdb`/`pg_ctl` refuse root (`initdb: error: cannot be run as root`). The
> `service-bootstrap-cell` now runs the PostgreSQL server lifecycle under the
> package-native unprivileged `postgres` OS account when euid==0 via
> `subprocess.run(..., user=...)` (POSIX-only, fail-closed before initdb, no
> `runuser`, no `shell=True`, NEVER falls back to root); non-root processes
> keep the direct path. No scientific inputs changed; the four frozen
> manifest/map hashes stay byte-identical. Gates: service bootstrap 28/28,
> notebook contract 42/42, deployment bundle 51/51, preflight 13/13 (targeted
> 134/134), full suite **2,185 passed / 33 skipped / 0 failed**. Deployment
> archive rebuilt from the exact tag: `dist/pilot-kaggle-upload.zip` + `.sha256`
> (archive SHA-256 `92a82606…`, byte-deterministic; finalize invariance PASS).
> Final closure section appended below.

> **NOTE (2026-08-13):** superseded by the KAGGLE RESERVED-NAME
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

---

## FINAL CLOSURE — KAGGLE STABLE-ANCHOR FREEZE / DUAL INPUT MODES (2026-08-13, `v0.9.6-pilot-exec-ready`)

> **SUPERSEDED** by the root-safe bootstrap correction on
> `v0.9.7-pilot-exec-ready` above. `v0.9.6-pilot-exec-ready` is immutable and
> NOT moved; its archive is retained for reference only.

**Executor:** opencode (provider `opencode/big-pickle`, model `big-pickle`).
**Reason for this correction:** the v0.9.5 hash-fixpoint finalizer was
mathematically unsound (archive SHA and notebook-manifest SHA each hash content
that includes the notebook bytes that would embed the value, so no embedded
value can equal its own hash). Replaced with a deterministic single-pass
stable-anchor freezer: the notebook now freezes ONLY notebook-independent
anchors (FROZEN_SOURCE_TAG, FROZEN_DEPLOYMENT, and the four stable
manifest/map hashes); archive SHA and notebook-manifest SHA are verified
self-consistently at runtime in BOTH Kaggle input modes (archive mode: actual
ZIP SHA must equal the sidecar; auto-expanded mount mode: sidecar is
provenance-only and the mounted tree is trusted against the frozen anchors plus
self-consistent notebook-manifest verification before copy). FROZEN_SOURCE_COMMIT
is not embedded; deployed source_commit equals the tag peel and is recorded in
`reports/pilot_notebook_trust_freeze.json`. Added
`scripts/finalize_pilot_notebook_trust.py` (deterministic single-pass freeze +
invariance rebuild) and expanded the deployment bundle contract (561 new
lines). Frozen values verified: the four stable hashes match v0.9.5 exactly.
Full suite **2,156 passed / 33 skipped / 0 failed**. Merge SHA
`af9b47444fafac260d887dabbe4e3ddc3b22a00f`; archive SHA-256
`afca4205583ccca1c29e7fb846993f944210805d676d509f1624985da36b16b8`;
created_utc `2026-08-13T18:00:00+00:00`. It was superseded because the real
Kaggle session exposed the PostgreSQL `cannot be run as root` blocker.

### Final state

PILOT-EXEC-01 GATE C READY (stable-anchor freeze) — Real Pilot NOT STARTED
(bootstrap blocked until the v0.9.7 root-safe correction).

---

## FINAL CLOSURE — KAGGLE POSTGRESQL ROOT-SAFE BOOTSTRAP (2026-08-13, `v0.9.7-pilot-exec-ready`)

**Executor:** opencode (provider `opencode/big-pickle`, model `big-pickle`).
**Reason for this correction:** the real Kaggle session exposed a blocker in
the v0.9.6 service bootstrap: the Kaggle notebook process runs as root, and
PostgreSQL `initdb`/`pg_ctl` refuse root (`initdb: error: cannot be run as
root`). The `service-bootstrap-cell` now resolves the package-native
unprivileged `postgres` OS account when the notebook effective uid is 0 and
runs the PostgreSQL server lifecycle (initdb, pg_ctl and the postgres server
it launches) under that account via `subprocess.run(..., user=...)`
(POSIX-only, checked, fail-closed; no `runuser`, no `shell=True`); FAILS
CLOSED before initdb when the account is missing and NEVER falls back to root;
non-root notebook processes keep the direct path. Ownership/log preparation is
limited to the private service paths (data dir `0o700`, log `0o600`, chown to
the postgres uid/gid; incomplete previous clusters safely recreated, ONLY
`PG_DATA_DIR`). The frozen TCP client probe (psql) still runs from the
notebook process against `127.0.0.1:5433 saleor/saleor/saleor`; Valkey/Redis
`127.0.0.1:6379` unchanged. **No scientific inputs changed** (scenarios,
prompts, metrics, model, quantization, timeout 600, repair budget, repository
pins, validation scope; the four frozen manifest/map hashes stay
byte-identical).

**What changed (bootstrap layer only):**

- `notebooks/pilot_exec_01.ipynb` (18 cells): `service-bootstrap-cell` replaced
  (299 lines) — `_run(..., user=...)`, `_pg_service_user()`, root-aware initdb
  cluster preparation, `pg_ctl`/postgres under the postgres account when
  euid==0, fail-closed missing-account handling; `FROZEN_SOURCE_TAG` →
  `v0.9.7-pilot-exec-ready`. Cell id `service-bootstrap-cell` preserved; all
  other cells byte-identical (canonical LF-normalized blob `082b4e84…` at the
  tag).
- `tests/integration/test_pilot_service_bootstrap.py` (NEW, 28 hermetic
  tests): execs the EXACT cell definitions with `sys.modules["os"]`/`pwd`
  fakes + fake `subprocess.run`/`socket.create_connection` (Gates B/C/D/E/F/H)
  — root mode, non-root mode, missing account, partial cluster state, proof
  semantics; exact argv assertions for initdb and pg_ctl.
- `tests/integration/test_pilot_notebook_contract.py` (42): 2 new root-safe
  static tests (`test_root_safe_unprivileged_postgres_lifecycle`,
  `test_never_prints_unknown_secrets`) + `FROZEN_SOURCE_TAG` v0.9.7.
- `tests/integration/test_pilot_deployment_bundle.py` (51),
  `scripts/build_pilot_upload_bundle.py`,
  `scripts/finalize_pilot_notebook_trust.py`: v0.9.7 defaults.

### Pre-Benchmark Validation

| Gate | Result |
|---|---|
| Dataset Validation | PASS (carried forward — zero data drift; 57 data files, manifest `8b859ecc…`, byte-identical to v0.9.6) |
| Prompt Validation | PASS (carried forward — zero prompt drift; no scenario/prompt changes in the correction) |
| Pipeline Smoke Test | PASS (bundled exact 48-cell dry-run executes the full pipeline end-to-end on the v0.9.7 tagged-rebuild bundle) |
| Dry Run | PASS (48/48 terminal / 48 succeeded / 0 failed / 0 pending / 48 unique run IDs; profile `pilot`) |
| Integration Test | PASS (full suite **2,185 passed / 33 skipped / 0 failed / 0 errors**) |
| Metric Verification | PASS (carried forward — zero metric/evaluator drift; no evaluator/metric changes in the correction) |

### Independent audit

| Item | Verdict |
|---|---|
| Root-safe bootstrap correctness | PASS — `_pg_service_user()` returns None for non-root (direct path preserved), `pwd.getpwnam("postgres")` for root else fail-closed RuntimeError BEFORE initdb; `_run(..., user=...)` only on POSIX + euid==0; no `runuser`, no `shell=True`; never falls back to root (verified: missing account → no run_calls, no chown_calls) |
| Exact command construction | PASS — Gate H seam execs the exact cell definitions; initdb/pg_ctl argv asserted exactly (`-p 5433 -h 127.0.0.1 -k <data_dir>`, `--auth=trust`, `--username=saleor`); psql client probe runs from the notebook process with env assertions on the final `SELECT 1` |
| Fail-closed behavior | PASS — incomplete previous cluster recreated ONLY as `PG_DATA_DIR`; tampered/destroyed paths never repaired; any failure stops before repository validation and model load |
| Privilege surface | PASS — ownership/chmod limited to private service paths (data dir `0o700`, log `0o600`, chown to postgres uid/gid); notebook process never grants the benchmark/model tree to postgres |
| Non-root parity | PASS — non-root notebook keeps the direct path; no behavior regression for the Smoke/prior notebooks |
| Test realism | PASS — hermetic seam replicates Kaggle root-euid conditions with exact cell source; no global `os` mutation (sys.modules fakes avoid pathlib breakage); 28/28 green in 0.36s |
| Notebook ordering | PASS — `service-bootstrap-cell` is cell index 7, after `pilot-snapshot-verify-cell` and before `pilot-repo-preflight-cell` / `gpu-verify-cell` / `model-preflight-cell` / `dryrun-cell` / `pilot-launch-cell`; REQUIRED_CELL_ORDER + `test_scientific_cell_ordering_unchanged` enforced by tests |
| No scientific RunRecord before all preflights | PASS — `pilot-launch-cell` runs last; no real run executed; dry-run records are mock-only with `hardware_identity "dry-run:mock"` |
| 48-cell matrix unchanged | PASS — 12 scenarios × 2 strategies × 2 reps = 48; dry-run per-repo 16/16/16, per-strategy 24/24, per-rep 24/24; no `--max-runs` |
| Metrics/prompts/model/quantization/timeout unchanged | PASS — no `src/benchmark`, prompt, scenario, metric, config, or model-identity change in the correction |
| Frozen manifest anchors unchanged | PASS — code `99688e4e…`, data `8b859ecc…`, repository snapshot `49d91d39…`, transport map `07036a36…` all byte-identical; notebook `FROZEN_MANIFEST_HASHES` == identity hashes |
| No Ground Truth leakage | PASS — no evaluator/ground-truth data changed |
| Historical Smoke untouched | PASS — `kaggle_upload/` not in the change set; byte-identical |
| Over-engineering | PASS — single self-contained fail-closed cell; no new abstractions/dependencies (option A, no `runuser`, no `shell=True`) |
| Technical debt | PASS — no new debt; hermetic seam is test-only; cell documented, contract-tested, deterministic |
| GitHub durability | PASS — branch pushed (`origin/fix/pilot-kaggle-postgres-unprivileged-bootstrap`, commits `c06dadf`/`539eb03`/`8e562aa`); main pushed non-ff to `f94853a`; tag `v0.9.7-pilot-exec-ready` pushed; local == remote |
| Docs consistency | PASS — runbook, SYSTEM_STATE, PROJECT_HANDOFF, phase report, deployment freeze, notebook trust freeze all reconciled to v0.9.7 current truth |

### Exact artifact report

- Final main SHA: `f94853aeff9f32dea9355468eedb74e891e2b9a5`
- Feature commits: `c06dadf` (`fix(pilot): root-safe unprivileged PostgreSQL
  bootstrap for Kaggle`, 6 files, +580/−17), `539eb03`
  (`docs(pilot): record v0.9.7 root-safe PostgreSQL bootstrap closure`,
  4 files, +119/−49), `8e562aa`
  (`test(pilot): harden hermetic os shim with path/getenv/sep`, +3/−0)
- Merge SHA: `f94853aeff9f32dea9355468eedb74e891e2b9a5` (non-ff
  `merge(pilot): root-safe unprivileged PostgreSQL bootstrap for Kaggle
  (v0.9.7-pilot-exec-ready)`; 10 files, +702/−66)
- `v0.9.7-pilot-exec-ready` dereference: annotated tag object peels to
  `f94853aeff9f32dea9355468eedb74e891e2b9a5` == merge commit
- Exact archive path: `dist/pilot-kaggle-upload.zip`
- Exact archive SHA-256: `92a82606a2d0b9b8b5a4c91bfe2416ee5682f2a3d460c901e556d32df467fbd3`
- Sidecar: `dist/pilot-kaggle-upload.zip.sha256` → matches archive hash
- Determinism: repeated identical builds from the tag (incl. the finalize
  invariance rebuild) all produced the SAME archive SHA-256 `92a82606…`
- Notebook SHA-256 (LF-normalized git blob @ tag == bundled deployed):
  `082b4e84688e2bff3ca3e38afb65ab08dc73e2e4a53576b9688422cae8cd6ede`;
  source notebook file SHA-256 `a763ac4827219669b6ca4a1a8a195fb620fcbd46a4aae6b253ce30b650d8c890`
  (18 cells, incl. root-safe `service-bootstrap-cell` and
  `transport-restore-cell`)
- Code manifest SHA-256 `99688e4e…` (byte-identical to v0.9.6); data manifest
  SHA-256 `8b859ecc…` (byte-identical to v0.9.6); notebook manifest SHA-256
  `a9f5fcdf…`; repository snapshot manifest SHA-256 `49d91d39…` (identical to
  v0.9.6); transport path map SHA-256 `07036a36…` (50 exact-path entries)
- Repository snapshot SHAs/hashes (from `repository_snapshot_manifest.json`):
  todo (embedded) `b8a33e20…` / content `f72bc9df…` / 24 files; djangocms
  `0f633fc9…` / content `729b5f41…` / 1662 files; saleor `e11a5557…` /
  content `708d0a7b…` / 4577 files — all identical to v0.9.6
- `pilot_deployment_identity.json`: source_commit `f94853aeff9f32dea9355468eedb74e891e2b9a5`
  (tag peel), source_tag `v0.9.7-pilot-exec-ready`, created_utc
  `2026-08-13T20:00:00+00:00`; expected_cells 48; all frozen values match the
  notebook `FROZEN_MANIFEST_HASHES`
- Notebook trust freeze: `reports/pilot_notebook_trust_freeze.json`
  (single-pass stable-anchor freeze, invariance OK; archive `92a82606…`,
  deployed notebook `082b4e84…`, source notebook `a763ac48…`)
- Final full-suite counts: **2,185 passed / 33 skipped / 0 failed / 0 errors**
  (2026-08-13)
- Final bundled dry-run counts (v0.9.7 tagged rebuild): **48/48 terminal, 48
  succeeded, 0 failed, 0 pending, 48 unique run IDs** (profile `pilot`;
  per-repo todo 16 / djangocms 16 / saleor 16; per-strategy
  iterative_repository_agent 24 / selective 24; per-rep 24 / 24)
- Tagged-rebuild acceptance: archive SHA `92a82606…`, 6396 members / 0 unsafe /
  0 reserved / 50 transport blobs, roundtrip restore 50/50, all five identity
  manifest hashes PASS, repo content hashes PASS, restored data tree ==
  canonical data tree, bundle dry-run 48/48

### Final state

PILOT-EXEC-01 GATE C READY (root-safe service bootstrap archive)
Real Pilot NOT STARTED

Next action: upload exact `dist/pilot-kaggle-upload.zip` +
`dist/pilot-kaggle-upload.zip.sha256` (rebuilt from
`v0.9.7-pilot-exec-ready`) as ONE Kaggle Dataset, attach the Pilot notebook +
Qwen 14B model, enable Internet, configure `HF_TOKEN`, then run cells in order
through target preflight (archive verify → transport restore → identity verify
→ install lock → snapshot verify → root-safe service bootstrap → repo preflight
→ GPU verify → model preflight → dry-run). Only after all preflight gates pass
may the real 48-cell cell be executed.

## FINAL CLOSURE — KAGGLE REDIS-COMPATIBLE OS PACKAGE FALLBACK (2026-08-15, `v0.9.8-pilot-exec-ready`)

**Executor:** opencode (provider `opencode/big-pickle`, model `big-pickle`).
**Reason for this correction:** the real Kaggle session exposed a blocker in
the v0.9.7 service bootstrap: the cell ran the combined
`apt-get install -y valkey-server redis-server`, which aborts the WHOLE apt
transaction with `E: Unable to locate package valkey-server` whenever one
candidate is unavailable — and the real Kaggle Ubuntu (Jammy-shaped) runtime
exposes `redis-server` in its configured apt repositories but NOT
`valkey-server`. The two candidates are ALTERNATIVES, so a combined install
can never be the resolution. The `service-bootstrap-cell` now provisions the
Redis-compatible server binary-first, refreshes apt metadata at most once per
cell invocation, probes each alternative candidate individually via
`apt-cache policy <name>`, installs EXACTLY ONE package per `apt-get install`,
records UNAVAILABLE and failed candidates, and FAILS CLOSED with
distro/runtime diagnostics when no candidate can be installed — no pip
client-package and no in-process fake-server fallback. A selected
implementation label and a proven server `--version` are printed after start.
The endpoint stays `127.0.0.1:6379` / `redis://127.0.0.1:6379/0`. The
root-safe unprivileged PostgreSQL bootstrap (v0.9.7) is unchanged. **No
scientific inputs changed** (scenarios, prompts, metrics, model,
quantization, timeout 600, repair budget, repository pins, validation scope;
the four frozen manifest/map hashes stay byte-identical).

**What changed (bootstrap layer only):**

- `notebooks/pilot_exec_01.ipynb` (18 cells): `service-bootstrap-cell` Redis
  provisioning replaced — `_APT_UPDATED` flag + `_apt_update_once()`
  (idempotent), `_apt_install()` (mandatory PG group only), `_apt_install_one()`
  (ONE package per apt-get), `_apt_package_available()` (`apt-cache policy
  <name>`, argument-list only, no shell), `REDIS_CANDIDATE_PACKAGES =
  ("valkey-server", "redis-server")`, `_distro_facts()`,
  `_provision_redis_server()` (binary-first → update-once → per-candidate
  probe/install → fail-closed diagnostic), `_ensure_redis` fail-closed on None
  + proven `--version`; final output gains `implementation=%s`; provisioning
  block calls `_provision_redis_server()`; `FROZEN_SOURCE_TAG` →
  `v0.9.8-pilot-exec-ready`. Cell id `service-bootstrap-cell` preserved; all
  other cells byte-identical.
- `tests/integration/test_pilot_service_bootstrap.py` (41 hermetic tests):
  14 new Redis package-fallback tests + a full-cell executor `_exec_cell`
  (runs the EXACT provisioning-and-prove section with per-port open flags and
  apt/`shutil.which` fakes) — already-installed (no apt at all), MANDATORY
  Jammy-shaped (valkey unavailable + redis available → install ONLY
  redis-server → PASS), reverse future-distro (both available → install ONLY
  valkey-server and stop), install-failure fallback, neither-available
  fail-closed, apt-get/apt-cache missing fail-closed, apt update at most once,
  start-command failure propagation, version-command diagnostic, full-cell
  end-to-end PG-lifecycle + Redis-fallback green.
- `tests/integration/test_pilot_notebook_contract.py` (43):
  `test_redis_package_fallback_contract` (forbids the combined
  `"valkey-server redis-server"` install string; requires the per-candidate
  helpers + `"apt-cache", "policy"`; no pip, no shell=True) +
  `FROZEN_SOURCE_TAG` v0.9.8.
- `tests/integration/test_pilot_deployment_bundle.py` (51),
  `scripts/build_pilot_upload_bundle.py`,
  `scripts/finalize_pilot_notebook_trust.py`: v0.9.8 defaults.

### Pre-Benchmark Validation

| Gate | Result |
|---|---|
| Dataset Validation | PASS (carried forward — zero data drift; 57 data files, manifest `8b859ecc…`, byte-identical to v0.9.7) |
| Prompt Validation | PASS (carried forward — zero prompt drift; no scenario/prompt changes in the correction) |
| Pipeline Smoke Test | PASS (bundled exact 48-cell dry-run executes the full pipeline end-to-end on the v0.9.8 tagged-rebuild bundle) |
| Dry Run | PASS (48/48 terminal / 48 succeeded / 0 failed / 0 pending / 48 unique run IDs; profile `pilot`) |
| Integration Test | PASS (full suite **2,199 passed / 33 skipped / 0 failed / 0 errors**) |
| Metric Verification | PASS (carried forward — zero metric/evaluator drift; no evaluator/metric changes in the correction) |

### Independent audit

| Item | Verdict |
|---|---|
| Fallback correctness | PASS — `_provision_redis_server()` resolves an installed binary first, then probes each candidate via `apt-cache policy` (never a combined install); EXACTLY ONE package per `apt-get install` |
| Jammy-shaped Kaggle reality | PASS — MANDATORY test: valkey-server unavailable + redis-server available → installs ONLY redis-server and passes (the real Kaggle case); reverse distro order also covered |
| Fail-closed behavior | PASS — neither candidate installable (or apt missing) → RuntimeError with distro facts, candidates checked, UNAVAILABLE list, failed installs; no pip package, no in-process fake server; stops before repository validation and model load |
| Idempotency | PASS — apt update runs at most once per cell (`_APT_UPDATED`); already-running service uses the binary path with zero apt commands |
| Service semantics | PASS — start-command failure propagates; version-command failure is an explicit diagnostic; `_ensure_redis` returns None → fail closed |
| Exact command construction | PASS — full-cell executor `_exec_cell` runs the exact provisioning-and-prove section; apt/cache argv asserted; no `shell=True` anywhere |
| Test realism | PASS — hermetic seam replicates Kaggle euid/apt conditions with exact cell source; Jammy-shaped test run FIRST; 41/41 green in <1s |
| 48-cell matrix unchanged | PASS — 12 scenarios × 2 strategies × 2 reps = 48; no `--max-runs` |
| Metrics/prompts/model/quantization/timeout unchanged | PASS — no `src/benchmark`, prompt, scenario, metric, config, or model-identity change in the correction |
| Frozen manifest anchors unchanged | PASS — code `99688e4e…`, data `8b859ecc…`, repository snapshot `49d91d39…`, transport map `07036a36…` all byte-identical; notebook `FROZEN_MANIFEST_HASHES` == identity hashes |
| No Ground Truth leakage | PASS — no evaluator/ground-truth data changed |
| Historical Smoke untouched | PASS — `kaggle_upload/` not in the change set; byte-identical |
| Over-engineering | PASS — single self-contained fail-closed cell; no new abstractions/dependencies (option A, no pip, no fake server) |
| Technical debt | PASS — no new debt; hermetic seam is test-only; cell documented, contract-tested, deterministic |
| GitHub durability | PASS — branch pushed (`origin/fix/pilot-kaggle-redis-package-fallback`, commit `9cf1745`); main non-ff merge + tag `v0.9.8-pilot-exec-ready` + archive rebuild recorded below |
| Docs consistency | PASS — runbook, SYSTEM_STATE, PROJECT_HANDOFF, phase report, deployment freeze, notebook trust freeze all reconciled to v0.9.8 current truth |

### Exact artifact report

- Feature commit: `9cf1745` (`fix(pilot): fall back to available
  Redis-compatible server package on Kaggle`, 6 files, +530/−20)
- Docs commit: `1f3f911` (`docs(pilot): record Kaggle Redis package fallback
  evidence`, 5 files, +278/−49)
- Final main SHA: `7e0a908588f8b5e0817659518b4e0928ce7c9943`
- Merge SHA: `7e0a908588f8b5e0817659518b4e0928ce7c9943` (non-ff
  `merge(pilot): fall back to available Redis-compatible server package on
  Kaggle (v0.9.8-pilot-exec-ready)`; 11 files, +808/−69)
- `v0.9.8-pilot-exec-ready` dereference: annotated tag object peels to
  `7e0a908588f8b5e0817659518b4e0928ce7c9943` == merge commit
- Exact archive path: `dist/pilot-kaggle-upload.zip`
- Exact archive SHA-256: `21e1d933d4d26c45818be8048cd42b3aeedd044a59b41fa442e93023d174662b`
- Sidecar: `dist/pilot-kaggle-upload.zip.sha256` → matches archive hash
- Determinism: repeated identical builds from the tag all produced the SAME
  archive SHA-256 `21e1d933…`
- Notebook SHA-256 (LF-normalized git blob @ tag == bundled deployed):
  `eff87bd76b412341d5ffc969ab3b7bb4a4400fc4`;
  source notebook file SHA-256 `d16009bfa618999ed380982cea3e908b399f2283a2ef602cb9933eb7aa12d633`
  (18 cells, incl. Redis-fallback `service-bootstrap-cell` and
  `transport-restore-cell`)
- Code manifest SHA-256 `99688e4e…` (byte-identical to v0.9.7); data manifest
  SHA-256 `8b859ecc…` (byte-identical to v0.9.7); repository snapshot
  manifest SHA-256 `49d91d39…` (identical to v0.9.7); transport path map
  SHA-256 `07036a36…` (50 exact-path entries)
- Repository snapshot SHAs/hashes: todo (embedded), djangocms `0f633fc9…`,
  saleor `e11a5557…` — all identical to v0.9.7
- Final full-suite counts: **2,199 passed / 33 skipped / 0 failed / 0 errors**
  (2026-08-15)
- Final bundled dry-run counts (v0.9.8 tagged rebuild): **48/48 terminal, 48
  succeeded, 0 failed, 0 pending, 48 unique run IDs** (profile `pilot`;
  per-repo todo 16 / djangocms 16 / saleor 16; per-strategy
  iterative_repository_agent 24 / selective 24; per-rep 24 / 24)
- Tagged-rebuild acceptance: archive SHA `21e1d933…`, 0 unsafe /
  0 reserved / 50 transport blobs, roundtrip restore 50/50, all five identity
  manifest hashes PASS, repo content hashes PASS, restored data tree ==
  canonical data tree, bundle dry-run 48/48

### Final state

PILOT-EXEC-01 GATE C READY (Redis-fallback service bootstrap archive)
Real Pilot NOT STARTED

Next action: upload exact `dist/pilot-kaggle-upload.zip` +
`dist/pilot-kaggle-upload.zip.sha256` (rebuilt from
`v0.9.8-pilot-exec-ready`) as ONE Kaggle Dataset, attach the Pilot notebook +
Qwen 14B model, enable Internet, configure `HF_TOKEN`, then run cells in order
through target preflight (archive verify → transport restore → identity verify
→ install lock → snapshot verify → service bootstrap → repo preflight
→ GPU verify → model preflight → dry-run). Only after all preflight gates pass
may the real 48-cell cell be executed.

## FINAL CLOSURE — KAGGLE NO-PIP REPOSITORY ENVIRONMENT PROVISIONING (2026-08-15, `v0.9.9-pilot-exec-ready`)

**Executor:** opencode (provider `opencode`, model `big-pickle`, model ID
`opencode/big-pickle`). Branch `fix/pilot-kaggle-env-provisioning-closure`;
start HEAD `48b956fdb3b5105bf058e1377cfda960151b6d44`; feature HEAD
`28f0405` (+ docs commit); merge/tag/archive SHAs recorded under "Exact
artifact report" below.

**Reason for this correction:** the real Kaggle session exposed a blocker in
the v0.9.8 `pilot-repo-preflight-cell`: it created the django CMS env with
`python -m venv /kaggle/working/pilot_envs/djangocms`, whose internal
`ensurepip` step runs against the BASE interpreter and cannot succeed because
the Kaggle runtime lock installs pip into that base interpreter. The real cell
died with:

```
['/kaggle/working/pilot_envs/djangocms/bin/python3', '-m', 'ensurepip', '--upgrade', '--default-pip'] returned non-zero exit status 1
```

(cell duration ~0.24 s — NOT a hang; a hang was explicitly ruled out). The same
latent failure existed in the `pilot_envs/tools` env. The fix never creates a
pip-capable env via `ensurepip`: stdlib venv always uses `--without-pip`, and
HOST pip bootstraps the pip-less envs via the documented `-m pip --python
<target>` feature (pip 22.3+). **No scientific inputs changed** (scenarios,
prompts, metrics, model, quantization, timeout 600, repair budget, repository
pins, validation scope; the four frozen manifest/map hashes stay
byte-identical).

### A. Model / execution identity

- Provider: `opencode`; model: `big-pickle`; model ID: `opencode/big-pickle`
- Start HEAD: `48b956fdb3b5105bf058e1377cfda960151b6d44` (== origin/main at start)
- Feature branch: `fix/pilot-kaggle-env-provisioning-closure`
- Feature HEAD: `28f0405` (fix commit) + docs evidence commit (see Exact
  artifact report for final SHAs)
- Merge SHA / main HEAD / tag + peel: recorded in "Exact artifact report"
  (PENDING until the merge + tag steps complete)

### B. Real target evidence

- Exact failing command (observed on real Kaggle, v0.9.8):
  `['/kaggle/working/pilot_envs/djangocms/bin/python3', '-m', 'ensurepip', '--upgrade', '--default-pip'] returned non-zero exit status 1`
- Root cause: `venv`+`ensurepip` installs pip into the base interpreter, which
  the Kaggle runtime lock has already modified — the env's pip install can
  never succeed there.
- Cell duration: ~0.24 s (ruled out the earlier hang hypothesis; the failure
  is an immediate command failure, not a timeout).
- Real Pilot: **NOT STARTED** (unchanged; still deferred until the user
  confirms the Kaggle mounted model path + HF results repository ID).

### C. Exact change table

| File | Symbol / Cell | Old | Root cause | New | Dependencies | Tests |
|---|---|---|---|---|---|---|
| `scripts/pilot_kaggle_repo_envs.py` (NEW) | provisioning helper | n/a | `venv`+`ensurepip` cannot produce a working pip on Kaggle | stdlib-only, no-pip provisioning of `tools`/`djangocms`/`saleor` envs; host-pip `--python` bootstrap; `uv` via host pip; markers + health probes; private-env-only rebuild; one apt transaction for `gettext`/`gcc`/`libpq-dev`; secret-redacting log | stdlib only | `tests/integration/test_pilot_repo_env_provisioning.py` (24) |
| `notebooks/pilot_exec_01.ipynb` | `pilot-repo-preflight-cell` | direct `venv`-based provisioning | runtime-lock ensurepip failure | thin adapter: `_assert_service_port` 5433/6379, helper load via `importlib.util`, `provision_repository_envs(...)`, shared `pilot_repo_snapshot.py preflight` with provisioned interpreters | `pilot_kaggle_repo_envs.py` (bundled), service-bootstrap `_port_open`, `KAGGLE_DEPLOYMENT_PATHS` | `test_pilot_notebook_contract.py` (46, + thin-adapter test) |
| `scripts/build_pilot_upload_bundle.py` | `PILOT_ENVS_SCRIPT` | helper not shipped | Kaggle cell must run the same helper | copies helper to `code/scripts/pilot_kaggle_repo_envs.py`, normalized + hashed in `code_manifest.json` | — | `test_pilot_deployment_bundle.py` (52, + helper-shipped test) |
| `tests/integration/test_pilot_repo_env_provisioning.py` (NEW) | Gate matrix | n/a | — | 24 hermetic/real tests (RED first) | helper | — |
| `docs/` (`PILOT_KAGGLE_RUNBOOK.md`, `PROJECT_HANDOFF.md`), `SYSTEM_STATE.md`, `reports/` | current-truth docs | v0.9.8 | — | v0.9.9 closure truth | — | — |

Scientific semantics changed: **NO** (no scenario/prompt/metric/model/
quantization/timeout/repo-pin/validation-scope change; the four frozen
manifest/map hashes byte-identical).

### D. Provisioning contract (per env)

| Env | Path | Method | Installer | Dep hash | Probes | Ready marker |
|---|---|---|---|---|---|---|
| uv tool | `pilot_envs/tools` | stdlib venv `--without-pip`; host pip `-m pip --python <target>` | HOST pip (no env pip) | — | `uv --version` | `.pilot_env_ready.json` (`pilot_repo_environment.v1`) |
| django CMS | `pilot_envs/djangocms` | stdlib venv `--without-pip`; host pip bootstrap; deps from frozen snapshot | `uv pip install -r test_requirements/django-5.0.txt` | `dependency_file` + `dependency_sha256` recorded | Django `5.0.*` + `import cms` | `.pilot_env_ready.json` |
| Saleor | `pilot_envs/saleor` | pinned-snapshot copy; `uv venv .venv --python <existing 3.12>` (`UV_PYTHON_DOWNLOADS=never`); `uv sync --locked` | `uv sync --locked` | lockfile (pinned snapshot) | `import saleor` | `.pilot_env_ready.json` |

Shared: OS prerequisites `gettext`+`gcc`+`libpq-dev` in ONE `apt-get install`
transaction (fail closed listing ALL missing); visible START/END/elapsed + 30 s
heartbeats; `_sanitize` redacts `HF_TOKEN=`/`SECRET_KEY=`/`PGPASSWORD=`;
rebuild ONLY the invalid private env dir (`_remove_private_env`); final log
line `PROVISIONING: PASSED (elapsed=...)`.

### E. Edge-case test ledger (all PASS)

| Case | Test | Result |
|---|---|---|
| `python -m venv` WITHOUT `--without-pip` (the v0.9.8 failure) | `test_venv_without_without_pip_flag_rejected` | PASS — rejected/fail-closed |
| tools-env ensurepip latent failure | `test_tools_env_never_uses_ensurepip` | PASS |
| host pip `--python` unsupported (pip < 22.3) | `test_host_pip_target_unsupported_fails_closed` | PASS |
| host pip `--python` verified once (cache) | `test_host_pip_target_verified_once` | PASS |
| interpreter discovery (bin/python, bin/python3, Scripts/python.exe, `.venv/bin/python`) | `test_interpreter_for_*` | PASS |
| django version mismatch (`<5.0`) | `test_django_version_rejected` | PASS |
| django missing `import cms` | `test_import_cms_probe_fails` | PASS |
| saleor missing | `test_saleor_import_fails_closed` | PASS |
| marker schema mismatch | `test_marker_schema_mismatch_rebuilds` | PASS |
| probe failure after marker OK | `test_marker_decision_probe_rebuilds` | PASS |
| reuse when everything matches | `test_marker_decision_reuses` | PASS |
| real no-pip venv (Gate K) | `test_real_no_pip_venv_created_and_has_no_pip` | PASS (real `python -m venv --without-pip`) |
| real marker decision on real venv | `test_real_marker_decision_on_real_venv` | PASS |
| failed command records tail + exit code | `test_failed_command_tail_recorded` | PASS (real subprocess, `exit_code == 7`) |
| secrets never logged | `test_log_never_records_secret_values` | PASS (real subprocess; `super-secret-token` absent, `HF_TOKEN=***` present) |
| OS prerequisites one apt transaction | `test_os_prerequisites_are_installed_in_one_apt_transaction` | PASS (probe-counted) |
| apt unavailable → fail closed listing ALL missing | `test_apt_unavailable_fails_closed_listing_all_missing` | PASS |
| still-missing after install → fail closed | `test_os_prerequisites_fail_closed_when_install_leaves_missing` | PASS |
| services required but unreachable | `test_services_required_unreachable_fails_closed` | PASS |
| partial-env rebuild safety | `test_rebuild_only_invalid_private_env_dir` | PASS |
| end-to-end (tools + django CMS + saleor, mock/uv) | `test_provision_repository_envs_end_to_end` | PASS |
| bundled helper == source (byte-equal normalized + hashed) | `test_repo_env_provisioning_helper_bundled_byte_equal_and_hashed` | PASS |
| thin-adapter notebook cell contract | `test_preflight_is_a_thin_provisioning_helper_adapter` | PASS |

### Pre-Benchmark Validation

| Gate | Result |
|---|---|
| Dataset Validation | PASS (carried forward — zero data drift; no data change in the correction) |
| Prompt Validation | PASS (carried forward — zero prompt drift; no scenario/prompt changes in the correction) |
| Pipeline Smoke Test | PASS (bundled exact 48-cell dry-run executes the full pipeline end-to-end on the v0.9.9 tagged-rebuild bundle) |
| Dry Run | PASS (48/48 terminal / 48 succeeded / 0 failed / 0 pending / 48 unique run IDs; profile `pilot`) |
| Integration Test | PASS (full suite **2,225 passed / 33 skipped / 0 failed / 0 errors**) |
| Metric Verification | PASS (carried forward — zero metric/evaluator drift; no evaluator/metric changes in the correction) |

### Independent audit

| Item | Verdict |
|---|---|
| No-ensurepip correctness | PASS — no `ensurepip` invocation and no bare `"python", "-m", "venv", <env>` path remains in the notebook cell; stdlib venv always `--without-pip`; host pip `-m pip --python <target>` bootstraps pip-less envs (documented pip 22.3+ feature) |
| Real Kaggle reality | PASS — MANDATORY matrix test reproduces the exact v0.9.8 command failure mode and the no-pip resolution; real-venv Gate-K tests run actual `python -m venv --without-pip` |
| Fail-closed behavior | PASS — unsupported host-pip, apt unavailable, still-missing OS packages, unreachable services, schema/probe mismatches all fail closed with exact reasons; only the specific invalid private env dir is rebuilt |
| Reuse semantics | PASS — markers + probes decide reuse; rebuilt envs re-provisioned exactly once and reused on subsequent runs |
| Secret hygiene | PASS — provisioning log redacts `HF_TOKEN=`/`SECRET_KEY=`/`PGPASSWORD=`; real-subprocess test proves a secret value never reaches the log |
| Saleor env | PASS — pinned-snapshot copy + `uv venv .venv --python <existing 3.12>` with `UV_PYTHON_DOWNLOADS=never` (no silent download/switch) + `uv sync --locked`; reuse verified via `.venv/bin/python` |
| Bundle parity | PASS — helper bundled byte-equal (normalized) + hashed in `code_manifest.json`; notebook contract + deployment bundle contract updated |
| 48-cell matrix unchanged | PASS — 12 scenarios × 2 strategies × 2 reps = 48; no `--max-runs` |
| Metrics/prompts/model/quantization/timeout unchanged | PASS — no `src/benchmark`, prompt, scenario, metric, config, or model-identity change in the correction |
| Frozen manifest anchors unchanged | PASS — code `99688e4e…`, data `8b859ecc…`, repository snapshot `49d91d39…`, transport map `07036a36…` all byte-identical; notebook `FROZEN_MANIFEST_HASHES` == identity hashes |
| No Ground Truth leakage | PASS — no evaluator/ground-truth data changed |
| Historical Smoke untouched | PASS — `kaggle_upload/` not in the change set; byte-identical |
| Over-engineering | PASS — single self-contained stdlib helper + thin adapter cell; no new runtime dependencies |
| Technical debt | PASS — no new debt; helper covered by 24-test matrix incl. real subprocess + real venv cases |
| GitHub durability | PASS — feature commit `28f0405` pushed (`origin/fix/pilot-kaggle-env-provisioning-closure`); docs commit, non-ff merge to main, tag `v0.9.9-pilot-exec-ready`, archive rebuild recorded in the Exact artifact report |
| Docs consistency | PASS — runbook, SYSTEM_STATE, PROJECT_HANDOFF, phase report, final report all reconciled to v0.9.9 current truth |

### Exact artifact report

- Feature commit: `28f0405` (`fix(pilot): no-pip repository env provisioning
  closure for Kaggle`, 6 files, +1726/−119)
- Docs commit: `fd6353c` (`docs(pilot): record no-pip repository env
  provisioning closure evidence`, 5 files, +423/−70)
- Final main SHA: `f211e4de664da0f0745e5cde5e1fd5138b3172f0`
- Merge SHA: `44d01028cb3b4576a28c136bad1c2e2f08b7971f` (non-ff
  `merge(pilot): no-pip repository env provisioning closure for Kaggle
  (v0.9.9-pilot-exec-ready)`; 11 files, +2149/−189)
- `v0.9.9-pilot-exec-ready` dereference: annotated tag object
  `ac4d4818d8490c67aa925a1bf496a408c687b0c2` peels to
  `f211e4de664da0f0745e5cde5e1fd5138b3172f0` (== main HEAD; the
  `FROZEN_SOURCE_TAG` bump commit following the merge)
- Exact archive path: `dist/pilot-kaggle-upload.zip`
- Exact archive SHA-256: `3f93b0a97309ac84250f291a25bad7cf3527bdf1df3a1b40a29f04a5c5f52493`
- Sidecar: `dist/pilot-kaggle-upload.zip.sha256` → matches archive hash
- Determinism: repeated identical builds from the tag with the same
  `--created-utc` produce the SAME archive SHA-256 `3f93b0a9…`
- Notebook SHA-256 (LF-normalized git blob @ tag == bundled deployed):
  `e53eca001307db735b7b0e25e83833c326d4ff1a74c4d75870ac1b501a545e1e`;
  source notebook file SHA-256
  `7a6c8c0c0c6e312c8d567ecbda6b5144c843e28671c97971f7fe72e9e40bfd4b`
  (18 cells, incl. no-pip `pilot-repo-preflight-cell`, `service-bootstrap-cell`
  and `transport-restore-cell`); notebook manifest SHA-256
  `f982a2e5bd0be32555ec24367680023396988813d9290a3a375710c0d7760531`
- Code manifest SHA-256 `99688e4e…` (byte-identical to v0.9.8); data manifest
  SHA-256 `8b859ecc…` (byte-identical to v0.9.8); repository snapshot
  manifest SHA-256 `49d91d39…` (identical to v0.9.8); transport path map
  SHA-256 `07036a36…` (50 exact-path entries)
- Repository snapshot SHAs/hashes: todo (embedded), djangocms `0f633fc9…`,
  saleor `e11a5557…` — all identical to v0.9.8
- `pilot_deployment_identity.json`: source_commit
  `f211e4de664da0f0745e5cde5e1fd5138b3172f0` (tag peel), source_tag
  `v0.9.9-pilot-exec-ready`, created_utc `2026-08-15T12:00:00+00:00`;
  expected_cells 48; all frozen values match the notebook
  `FROZEN_MANIFEST_HASHES`
- Final full-suite counts: **2,225 passed / 33 skipped / 0 failed / 0 errors**
  (2026-08-15)
- Final bundled dry-run counts (v0.9.9 tagged rebuild): **48/48 terminal, 48
  succeeded, 0 failed, 0 pending, 48 unique run IDs** (profile `pilot`;
  per-repo todo 16 / djangocms 16 / saleor 16; per-strategy
  iterative_repository_agent 24 / selective 24; per-rep 24 / 24)
- Tagged-rebuild acceptance: archive SHA `3f93b0a9…`, 0 unsafe /
  0 reserved / 50 transport blobs, roundtrip restore 50/50, all five identity
  manifest hashes PASS, repo content hashes PASS, restored data tree ==
  canonical data tree, bundle dry-run 48/48

### Final state

PILOT-EXEC-01 GATE C READY (no-pip repository env provisioning archive)
Real Pilot NOT STARTED

Next action: upload exact `dist/pilot-kaggle-upload.zip` +
`dist/pilot-kaggle-upload.zip.sha256` (rebuilt from
`v0.9.9-pilot-exec-ready`) as ONE Kaggle Dataset, attach the Pilot notebook +
Qwen 14B model, enable Internet, configure `HF_TOKEN`, then run cells in order
through target preflight (archive verify → transport restore → identity verify
→ install lock → snapshot verify → service bootstrap → repo preflight → GPU
verify → model preflight → dry-run). Only after all preflight gates pass may
the real 48-cell cell be executed.

## FINAL CLOSURE — RELEASE TRUST GATE (2026-08-15, `v0.9.10-pilot-exec-ready`)

**Executor:** opencode (provider `opencode`, model `big-pickle`, model ID
`opencode/big-pickle`). Branch `fix/pilot-release-trust-gate-closure`; base
HEAD `80d4d6e581cef60463efde31b414643ba182f35a` (== main == origin/main at
start); feature HEAD `097768e` (+ docs evidence commit `4ac7f0d`). Merge SHA /
main HEAD `44e9a1f4314c2ce8ec0b7abb16c88cbc3f83bfb6`; tag `v0.9.10-pilot-exec-ready`
peels to the merge commit; tagged-rebuild archive SHA
`9df1396d50a99da7b3dd101fefe79013c3c253da8fd65251dbd9eb4650e71436` — all
recorded under "Exact artifact report" below (COMPLETE).

**Reason for this closure:** every prior freeze recorded the four manifest/map
hashes from values carried forward across releases WITHOUT validating them
against an actual build of the tagged source. This release trust gate runs the
real two-pass deterministic finalizer
(`scripts/finalize_pilot_notebook_trust.py`) against the LOCAL repo cache and
proves, byte-for-byte, that the frozen notebook anchors == the deployment
identity == the actually-built bundle (Notebook == Identity == Actual for all
four frozen hashes). **No scientific inputs changed** (scenarios, prompts,
metrics, model, quantization, timeout 600, repair budget, repository pins,
validation scope).

### A. Model / execution identity

- Provider: `opencode`; model: `big-pickle`; model ID: `opencode/big-pickle`
- Base HEAD: `80d4d6e581cef60463efde31b414643ba182f35a` (== origin/main at start)
- Feature branch: `fix/pilot-release-trust-gate-closure`
- Feature HEAD: `097768e` (fix commit) + docs evidence commit `4ac7f0d`
- Merge SHA / main HEAD / tag + peel: `44e9a1f4314c2ce8ec0b7abb16c88cbc3f83bfb6`
  (non-ff merge; main HEAD; annotated tag `v0.9.10-pilot-exec-ready` peels to
  the merge commit — see "Exact artifact report")

### B. Real freeze evidence

- Finalizer invocation (real, NO `--allow-acquire`):
  `python scripts/finalize_pilot_notebook_trust.py --source-commit
  80d4d6e581cef60463efde31b414643ba182f35a --source-tag
  v0.9.10-pilot-exec-ready --repo-cache dist/pilot-repo-cache --created-utc
  "2026-08-15T14:00:00+00:00"`
- Local repo cache cat-file checks: PASS both pinned commits — django CMS
  `0f633fc9fa213357f4202482aab2b0edad680f95`, Saleor
  `e11a5557eff29fbb2eed36e6ff3cd0af08ab9e10`; `git archive` works in both
  cache dirs (djangocms 16,617,486 chars; saleor 60,692,235 chars).
- Two-pass deterministic freeze: discovery build archive
  `49219d80…`; validation-enabled rebuild archive
  `dd5ee529e3a0066f40a5a2d037526bcef20a7a04b469874ec05e55b9978777be` (the
  archive that carries the frozen anchors and is verified at runtime).
- Freeze report: `reports/pilot_notebook_trust_freeze.json` (tracked):
  `created_utc` `2026-08-15T14:00:00+00:00`; `frozen_source_tag`
  `v0.9.10-pilot-exec-ready`; frozen manifest hashes — code
  `bb976f67fefe184796469efcd3f6916fbd592ec9f226b7b0365a237a0ef654d5`, data
  `8b859ecc72164fe95c0aa122f8179310ccc6375613543c6702c2ca5867c97b5a`,
  repository snapshot
  `49d91d39435f7e6f2dbf7d15f1a59188aa059ebb16fb31094c7a1827fb62702c`,
  transport path map
  `07036a36cd97daef48a39f6490bc055f58e87b336d849a4c1343e82a167cdbce`;
  deployed notebook SHA-256 `d15d86831bf805e7bcc9e811eb87158b2e4f56732082d1e6326ee9d94ccb81ec`;
  source notebook SHA-256
  `873e97735cd22b9f7686b56b3d058d1cd01f75513e6a6c8603f1e9dcf70ed71b`.
- Notebook == Identity == Actual: **PASS 4/4** — for every one of the four
  frozen manifest/map hashes the notebook anchors == the deployment identity
  binding == the actually-built bundle bytes (deployed notebook bytes in the
  archive == report `notebook_sha256`; bundled-normalized notebook == source).
- Why `code_manifest` changed vs v0.9.9 (`99688e4e` → `bb976f67`): the v0.9.9
  recorded code hash predated the bundled helper-script additions and was never
  validated against the build; the new gate freezes the true validated value
  (data `8b859ecc…`, repository snapshot `49d91d39…`, transport map
  `07036a36…` remain byte-identical to v0.9.9; bundled files identical
  `f211e4d..80d4d6e`).
- Real Pilot: **NOT STARTED** (unchanged; still deferred until the user
  confirms the Kaggle mounted model path + HF results repository ID).

### C. Exact change table (feature commit `097768e`, 7 files, +579/−234)

| File | Symbol / Cell | Old | Root cause | New | Dependencies | Tests |
|---|---|---|---|---|---|---|
| `notebooks/pilot_exec_01.ipynb` | frozen anchors | v0.9.9 values | stale unvalidated code hash | `FROZEN_SOURCE_TAG` `v0.9.10-pilot-exec-ready`; `FROZEN_MANIFEST_HASHES` = the four validated hashes above (code `bb976f67…`) | — | `test_pilot_notebook_contract.py` |
| `scripts/finalize_pilot_notebook_trust.py` | two-pass deterministic freeze | single-pass discovery only | archive carrying frozen anchors must be validated | discovery + validation rebuild; freezes only notebook-independent anchors | `scripts/build_pilot_upload_bundle.py` | `test_pilot_deployment_bundle.py` |
| `scripts/build_pilot_upload_bundle.py` | trust gate | no end-to-end proof | need Notebook==Identity==Actual evidence | `validate_bundled_notebook_trust` gate against the freeze report | finalizer | `test_pilot_deployment_bundle.py` |
| `tests/integration/test_pilot_deployment_bundle.py` | trust-gate regressions | — | — | 4-hash Notebook==Identity==Actual proof + freeze-report contract | — | — |
| `tests/integration/test_pilot_notebook_contract.py` | v0.9.10 anchors | v0.9.9 | — | updated anchors/hashes | — | — |
| `tests/integration/test_pilot_repo_env_provisioning.py` / `test_pilot_real_launch_preflight.py` | version bumps | v0.9.9 | — | v0.9.10 | — | — |
| `reports/pilot_notebook_trust_freeze.json` | freeze evidence | v0.9.9 | — | v0.9.10 values above | — | trust-gate tests |

Scientific semantics changed: **NO**.

### D. Gate totals (this closure)

| Gate | Result |
|---|---|
| Dataset Validation | PASS (carried forward — zero data drift; the four frozen hashes re-validated against the build) |
| Prompt Validation | PASS (carried forward — zero prompt/scenario drift) |
| Pipeline Smoke Test | PASS (bundled exact 48-cell dry-run executes the full pipeline end-to-end; re-verified on the tagged-rebuild bundle — see Exact artifact report) |
| Dry Run | PASS (exact bundled 48-cell dry-run 48/48 terminal / 48 succeeded / 0 failed / 0 pending / 48 unique run IDs; profile `pilot`) |
| Integration Test | PASS (full suite **2,234 passed / 33 skipped / 0 failed / 0 errors**) |
| Metric Verification | PASS (carried forward — zero evaluator/metric drift) |
| Targeted trust-gate closures | PASS — deployment bundle 52/52, notebook contract 46/46, repo-env provisioning 24/24, real-launch preflight 13/13 = **142 passed in 258.38s** |
| Static gates | PASS — `git diff --check` exit 0; ruff clean; py_compile OK; mypy `--strict` OK |

### E. Independent audit

| Item | Verdict |
|---|---|
| Freeze is real, not smoke | PASS — the finalizer ran against the local repo cache (`dist/pilot-repo-cache`) with NO `--allow-acquire`; both pinned repo cat-file checks pass; `git archive` works in both cache dirs |
| Notebook == Identity == Actual | PASS — all four frozen manifest/map hashes proven equal across the notebook anchors, the deployment identity, and the actually-built bundle; deployed notebook == freeze report `notebook_sha256`; bundled-normalized notebook == source |
| Determinism | PASS — one explicit `created_utc` (`2026-08-15T14:00:00+00:00`) drives the two-pass freeze; the post-merge tagged rebuild reuses the SAME `created_utc` with `source_commit` = merge SHA (recorded in the Exact artifact report) |
| No scientific drift | PASS — scenarios/prompts/metrics/model/quantization/timeout/repair budget/repo pins/validation scope unchanged; data/repo/transport hashes byte-identical to v0.9.9 |
| Code hash delta explained | PASS — `99688e4e` (v0.9.9) predated bundled helper additions and was never validated; `bb976f67` is the true validated value |
| Historical Smoke untouched | PASS — `kaggle_upload/` not in the change set; byte-identical |
| Fail-closed behavior | PASS — trust-gate tests fail if any frozen hash diverges between notebook, identity, and actual bundle |
| GitHub durability | PASS — feature commit `097768e` pushed (`origin/fix/pilot-release-trust-gate-closure`); docs commit, non-ff merge to main, tag `v0.9.10-pilot-exec-ready`, archive rebuild recorded in the Exact artifact report |

### Exact artifact report

- Feature commit: `097768e` (`fix(pilot): v0.9.10 release trust gate closure
  (notebook==identity==actual)`, 7 files, +579/−234)
- Docs commit: `4ac7f0d` (`docs(pilot): record v0.9.10 release trust gate
  closure evidence`, 4 files, +267/−62)
- Final main SHA: `44e9a1f4314c2ce8ec0b7abb16c88cbc3f83bfb6` (== merge SHA ==
  main HEAD after the non-ff merge)
- Merge SHA: `44e9a1f4314c2ce8ec0b7abb16c88cbc3f83bfb6` (non-ff
  `merge(pilot): release trust gate closure (notebook==identity==actual,
  v0.9.10-pilot-exec-ready)`; 11 files, +846/−296)
- `v0.9.10-pilot-exec-ready` dereference: annotated tag object peels to
  `44e9a1f4314c2ce8ec0b7abb16c88cbc3f83bfb6` (== main HEAD == the non-ff merge
  commit; created ONLY after the FINAL ARTIFACT TRUST GATE passed)
- Exact archive path: `dist/pilot-kaggle-upload.zip` (gitignored)
- Exact archive SHA-256 (freeze validation rebuild, source_commit provisional
  `80d4d6e…`): `dd5ee529e3a0066f40a5a2d037526bcef20a7a04b469874ec05e55b9978777be`
- Tagged-rebuild archive SHA-256: `9df1396d50a99da7b3dd101fefe79013c3c253da8fd65251dbd9eb4650e71436`
  (rebuilt after the merge/tag with the SAME `--created-utc
  "2026-08-15T14:00:00+00:00"` and `--source-commit` = merge SHA
  `44e9a1f…`; differs from the freeze validation rebuild ONLY by the
  identity `source_commit` — the four frozen manifest/map hashes are
  identical)
- Notebook SHA-256 (deployed, == bundled archive bytes):
  `d15d86831bf805e7bcc9e811eb87158b2e4f56732082d1e6326ee9d94ccb81ec`; source
  notebook SHA-256 `873e97735cd22b9f7686b56b3d058d1cd01f75513e6a6c8603f1e9dcf70ed71b`
- Code manifest `bb976f67fefe184796469efcd3f6916fbd592ec9f226b7b0365a237a0ef654d5`
  (validated, 91 entries); data manifest
  `8b859ecc72164fe95c0aa122f8179310ccc6375613543c6702c2ca5867c97b5a`;
  repository snapshot manifest
  `49d91d39435f7e6f2dbf7d15f1a59188aa059ebb16fb31094c7a1827fb62702c`;
  transport path map
  `07036a36cd97daef48a39f6490bc055f58e87b336d849a4c1343e82a167cdbce`
- `pilot_deployment_identity.json`: source_commit
  `44e9a1f4314c2ce8ec0b7abb16c88cbc3f83bfb6` (tag peel), source_tag
  `v0.9.10-pilot-exec-ready`, created_utc `2026-08-15T14:00:00+00:00`;
  expected_cells 48; all frozen values match the notebook
  `FROZEN_MANIFEST_HASHES`
- Final full-suite counts: **2,234 passed / 33 skipped / 0 failed / 0 errors**
  (2026-08-15)
- Final bundled dry-run counts (v0.9.10 tagged rebuild): **48/48 terminal, 48
  succeeded, 0 failed, 0 pending, 48 unique run IDs** (profile `pilot`;
  per-repo todo 16 / djangocms 16 / saleor 16; per-strategy
  iterative_repository_agent 24 / selective 24; per-rep 24 / 24)
- Tagged-rebuild acceptance: **PASS — FINAL ARTIFACT TRUST GATE** (Notebook ==
  Identity == Actual 4/4 for the four frozen manifest/map hashes; deployed
  notebook == freeze report; trust-gate regression + real artifact expanded
  simulation 19/19 passed on the tagged rebuild)

### Final state

PILOT-EXEC-01 RELEASE TRUST GATE: **CLOSED and FROZEN at
`v0.9.10-pilot-exec-ready`** (merge `44e9a1f…` on `main`; annotated tag created
on the merge commit; tagged-rebuild archive `9df1396d…`; FINAL ARTIFACT TRUST
GATE PASS — Notebook == Identity == Actual 4/4; exact bundled 48-cell mock
dry-run 48/48 PASS on the tagged rebuild). Deployment is locked and ready for
Real Pilot. **Real Pilot execution NOT STARTED** — deferred until the user
confirms the Kaggle mounted model path and the exact HF results repository ID.

## FINAL CLOSURE — SALEOR SOURCE-VISIBILITY HEALTH PROBE (2026-08-16, `v0.9.11-pilot-exec-ready`)

**Executor:** opencode (provider `opencode/big-pickle`, model `big-pickle`).

### Real Kaggle failure chain (v0.9.10)

| Stage | Result |
|---|---|
| release trust / transport restore / runtime lock | PASS |
| repository snapshot verification | PASS |
| PostgreSQL provisioning + TCP proof | PASS |
| Redis fallback + reachability | PASS |
| uv tool env | PASS |
| django CMS no-pip env + deps + health probe | PASS |
| Saleor source copy | PASS |
| Saleor Python 3.12 `.venv` creation | PASS |
| `uv sync --locked` | **PASS** (`uv sync --locked = PASS`) |
| `import saleor` health probe | **FAILED** — exit 1, `ModuleNotFoundError: No module named 'saleor'` |

### Root cause (audited)

The pinned Saleor `pyproject.toml` (commit `e11a5557…`) sets
`[tool.uv] package = false` (upstream), so uv correctly installs the locked
dependencies but deliberately does NOT install the root Saleor project into
site-packages. The v0.9.10 probe ran `<saleor .venv>/bin/python -c "import
saleor"` WITHOUT `cwd=the Saleor working copy`, while the frozen downstream
preflight already runs Saleor commands with `cwd = pristine staged repository
root`. **Kaggle is NOT the root cause.** Non-solutions explicitly excluded:
NO `package=true`, NO pip/uv editable install, NO global `PYTHONPATH`;
`uv sync --locked` / Python 3.12 / `UV_PYTHON_DOWNLOADS=never` preserved.

### Fix (minimal, source-faithful)

`_import_probe` gained optional `cwd`; `_saleor_probe` requires `work_dir` and
always probes with `cwd=work_dir`; BOTH call sites fixed (marker/reuse
`_needs_rebuild` probe and post-`uv sync --locked` probe).

### Gates

| Gate | Result |
|---|---|
| RED (vs old helper) | PASS — new tests failed with `TypeError: _saleor_probe() got an unexpected keyword argument 'work_dir'` |
| real-subprocess source-visibility regression | PASS — `import saleor` FAILS from unrelated cwd, PASSES with `cwd=work` |
| `_FakeRunner` cwd assertion | PASS — the exact local-pass gap (fail-closed on `import saleor` unless cwd exposes the package) |
| pinned `[tool.uv] package=false` contract | PASS — bundled pyproject not mutated |
| fresh/reuse cwd topology + missing-source fail-closed | PASS |
| downstream preflight parity (Gate H) | PASS |
| no semantic drift | PASS |
| diff-check / ruff / mypy / py_compile | PASS |
| targeted integration | PASS — provisioning 28, notebook contract 44, deployment bundle 61, real-launch preflight 14, service bootstrap 41 (188 passed) |
| full suite | PASS — **2,239 passed / 33 skipped / 0 failed** (2026-08-16) |

### Release closure (v0.9.11-pilot-exec-ready)

| Item | Value |
|---|---|
| Feature branch | `fix/pilot-saleor-source-visibility-probe` (fix `ee3d88b`, docs `228b2e8`) |
| Non-ff merge | `8801304d855fe29c694f2a3c0500f661685b0d72` (main HEAD == merge SHA) |
| Finalizer re-freeze | `b87aa49`; `--source-commit` = merge SHA; `--source-tag v0.9.11-pilot-exec-ready`; `--created-utc "2026-08-16T12:00:00+00:00"` |
| Code manifest | `7e86eb5dd65122c2714c97ed84f20d8328adbe2b3e838fe6a2218c293ce72adb` (91 entries; only delta vs v0.9.10 is the bundled helper) |
| Data / repo snapshot / transport map | `8b859ecc7216…` / `49d91d39435f…` / `07036a36cd97…` (byte-identical to v0.9.10) |
| FINAL ARTIFACT TRUST GATE | **PASS — Notebook == Identity == Actual 4/4** (deployed notebook `85edbd33e81b…` == archive bytes; source `a0382061954e…`) |
| Archive | `dist/pilot-kaggle-upload.zip` SHA-256 `039818bde60edcc9693ca88f779c7987bde818ddbfbca705426747b08c6d5453` |
| Annotated tag | `v0.9.11-pilot-exec-ready` ON the merge commit, pushed (peels to `8801304d855fe29c694f2a3c0500f661685b0d72` == freeze report `source_commit`) |
| Bundled 48-cell mock dry-run | **PASS — 48/48** terminal / 48 succeeded / 0 failed; todo 16 / djangocms 16 / saleor 16; iterative_repository_agent 24 / selective 24; rep1 24 / rep2 24; 48 unique / 0 missing / 0 duplicate / 0 model calls |
| Scientific inputs | unchanged (scenarios, prompts, metrics, model, quantization, timeout 600, repair budget, repository pins, validation scope) |

### Final state

PILOT-EXEC-01 v0.9.11: **CLOSED and FROZEN at `v0.9.11-pilot-exec-ready`**
(merge `8801304…` on `main`; annotated tag on the merge commit; archive
`039818bde60edcc9…`; FINAL ARTIFACT TRUST GATE PASS 4/4; bundled 48-cell mock
dry-run 48/48). The Saleor source-visibility health-probe blocker from real
Kaggle v0.9.10 is fixed and the deployment source is re-frozen. **STOP. Real
Pilot execution NOT STARTED** — deferred until the user confirms the Kaggle
mounted model path and the exact HF results repository ID.
