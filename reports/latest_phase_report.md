# PILOT-EXEC-01 Pre-Execution Gates — Latest Phase Report

> **CURRENT TRUTH (2026-08-24, v0.9.20 ROOT-CAUSE CLOSURE):** the real Kaggle
> v0.9.19 session FAILED at the Saleor fast capability gate (Pytest exit 5 =
> no tests collected) after every earlier stage passed —
> **`v0.9.19-pilot-exec-ready` is REJECTED FOR PILOT LAUNCH**. Root cause: the
> gate argv concatenated a second `-m pytest` vector onto the already-resolved
> frozen primary command; the local suite was false-green via a substring-based
> fake runner. Closure complete on branch
> `fix/pilot-v0920-saleor-preflight-root-closure`: exact standalone gate argv +
> fail-fast invariant + exact-argv regression tests (RED/GREEN recorded;
> target-proven on Linux CI run 32650273641) + exact-command mock validation +
> evidence-backed Saleor baseline-flake policy
> (`pilot_saleor_baseline_flaky_profile.v1`, armed-if-evidenced) + target-shaped no-model Linux CI
> preflight workflow. All release gates then passed: non-ff merge to main,
> idempotent re-freeze at the merge commit with --verify-source-provenance,
> exact-artifact dry-run 48/48, and the annotated stable tag
> `v0.9.20-pilot-exec-ready` created AT the merge commit `febda7938db1284da4090d35e980db472149c3ad`
> (archive `56b1c2a9019a03892ce627321b9a415795ac95836ac415694bbc0995263c8024`).
> Full detail:
> `reports/V0920_ROOT_CAUSE_CLOSURE_REPORT.md`.
>
> **HISTORICAL TRUTH (2026-08-22):** v0.9.19 was merged to main and tagged as `v0.9.19-pilot-exec-ready`,
> tag peel == artifact source commit `2305991442a4f965d44bb066bb00c0a459fc395a`;
> `main` is a post-tag docs/evidence child of that merge; artifact
> trust/provenance GREEN; OpenCode full suite = 2330 passed / 34 skipped / 0
> failed at that state; Real Pilot = NOT STARTED. Authoritative snapshot:
> `docs/AI_ACCOUNT_TRANSFER_HANDOFF.md`.

> **CURRENT TRUTH (2026-08-19):** **PILOT-EXEC-01 v0.9.19 POSTGRESQL ADMIN/APPLICATION BOOTSTRAP + PARTIAL RECOVERY CLOSURE — `v0.9.19-pilot-exec-ready` (real Kaggle defect fix).** v0.9.18 release-only provenance/docs correction is PRIOR. v0.9.19 = PostgreSQL admin/application bootstrap + partial recovery closure: `_psql` no longer has implicit Saleor DB default, server proofs use `db="postgres"`, `SHOW data_directory` protects partial recovery, Saleor DB is created before any application DB connection. All authoritative docs updated. *(Historical at the time: non-ff merge/tag were pending — since completed, see the 2026-08-22 UPDATE above.)*

> **CURRENT TRUTH (2026-08-16):** **PILOT-EXEC-01 RELEASE-PROVENANCE CLOSURE — `v0.9.11-pilot-exec-ready` REJECTED FOR LAUNCH; `v0.9.12-pilot-exec-ready` SHIPPED WITH A FAIL-CLOSED `source_commit` GIT-TREE PROVENANCE GATE (branch `fix/pilot-release-provenance-closure` from clean `origin/main` `5cee179`; code/test commit `6cd2767`, freeze commit `7923b37`).** The v0.9.11 immutable tag peeled to the merge commit `8801304`, whose notebook is the v0.9.10 notebook `d15d8683…`, while the deployed artifact carried the re-frozen notebook `85edbd33…` that landed only in the POST-tag re-freeze commit `b87aa49` — embedded notebook trust could be made internally self-consistent, yet the tag does not contain the deployed notebook. v0.9.11 = `internally-valid artifact, but rejected for launch because the immutable tag does not contain the deployed re-frozen notebook and therefore cannot reproduce the claimed source snapshot.` FIX (minimal): fail-closed `validate_source_commit_provenance(*, source_commit, bundled_root, …, git_reader=None)` in `scripts/build_pilot_upload_bundle.py` proves the bundled Pilot notebook AND every `code_manifest.json` entry equal the normalized (CRLF→LF for text suffixes) tracked Git blob at `identity.source_commit`; standalone release acceptance step run BEFORE the immutable tag is created; no skip flag; never falls back to the working tree; deliberately NOT wired into `build_pilot_bundle`/`freeze()` (the finalizer's validation rebuild predates the anchor commit). Companion byte-faithfulness fix: bundled `*.lock` files LF-normalized in the code bundle (`_normalize_lock_files`) — the Windows-checkout CRLF lock manifest `95ad3b2b…` had drifted from the LF blob `1f4b1875…`. New suite `tests/integration/test_pilot_release_provenance.py` Gates 1–5: exact v0.9.11 forensic RED (real git blobs `8801304` vs `b87aa49`; internally-consistent identity PASSES embedded trust while the provenance gate FAILS), notebook CRLF/LF parity, code-manifest modified/missing FAIL naming exact paths, invalid SHA / unknown commit fail closed, `.lock` LF PASS vs CRLF FAIL, v0.9.12 release-tag sequencing contract. Finalizer re-freeze `--source-tag v0.9.12-pilot-exec-ready`: code `0fd86fc9…` (94/94 source-faithful incl. both locks), data `8b859ecc…`, repo snapshot `49d91d39…`, transport `07036a36…`; archive `5a7d7e0a…`. Full suite **2,255 passed / 33 skipped / 0 failed** (2026-08-16). **Pilot = NOT STARTED.**
>
> **HISTORICAL TRUTH (2026-08-16, REJECTED FOR LAUNCH — superseded by the v0.9.12 release-provenance closure):** **PILOT-EXEC-01 SALEOR SOURCE-VISIBILITY HEALTH-PROBE FIX — REAL KAGGLE v0.9.10 FAILURE CLOSED ON `fix/pilot-saleor-source-visibility-probe` (code/test commit `ee3d88b`, pushed; release `v0.9.11-pilot-exec-ready` internally-valid but REJECTED for launch because the immutable tag does not contain the deployed re-frozen notebook — see the Current section below).** Real Kaggle v0.9.10 PASSED every preflight stage — release trust, transport restore, runtime lock install, repository snapshot verification, PostgreSQL provisioning + TCP proof, Redis fallback + reachability, uv tool env, django CMS no-pip env + deps + health probe, Saleor source copy, Saleor Python 3.12 `.venv` creation, `uv sync --locked` (`uv sync --locked = PASS`) — then failed ONLY at the new health probe: `START import saleor probe / END import saleor probe FAILED elapsed=0s exit=1 / ModuleNotFoundError: No module named 'saleor'`. ROOT CAUSE: the pinned Saleor `pyproject.toml` sets `[tool.uv] package = false` (upstream), so uv correctly installs the locked dependencies but deliberately does NOT install the root Saleor project into site-packages; the v0.9.10 probe ran `<saleor .venv>/bin/python -c "import saleor"` WITHOUT `cwd=the Saleor working copy`, while the frozen downstream preflight already runs Saleor commands with `cwd = pristine staged repository root`. Kaggle is NOT the root cause. FIX (minimal, source-faithful): `_import_probe` gained optional `cwd`; `_saleor_probe` always probes from `work_dir`; BOTH call sites fixed (marker/reuse + post-sync). Explicit non-solutions honored (NO `package=true`, NO pip/uv editable install, NO global `PYTHONPATH`; `uv sync --locked` / Python 3.12 / `UV_PYTHON_DOWNLOADS=never` preserved). Strong tests: real-subprocess source-visibility regression (RED proven vs old helper), `_FakeRunner` cwd assertion (the exact local-pass gap), pinned `package=false` contract on the bundled pyproject (no mutation), fresh/reuse cwd topology, missing-source fail-closed, downstream preflight parity, no semantic drift. Targeted integration green (provisioning 28, notebook contract 44, deployment bundle 61, real-launch preflight 14, service bootstrap 41 = 188); full suite **2,239 passed / 33 skipped / 0 failed** (2026-08-16); diff-check/ruff/mypy/compile clean. v0.9.10 remains immutable (real Kaggle preflight reached the Saleor post-sync health probe then failed because the probe did not run from the repository root). **ALL SUBSEQUENT STEPS COMPLETE:** independent audit PASS → non-ff merge to main `8801304` (merge SHA == main HEAD == tag peel) → finalizer re-freeze (code manifest `7e86eb5dd651…`, data/repo/transport byte-identical) → FINAL ARTIFACT TRUST GATE **Notebook == Identity == Actual 4/4** (deployed notebook `85edbd33e81b…`, archive `039818bde60edcc9…`) → immutable annotated tag `v0.9.11-pilot-exec-ready` ON the merge commit, pushed → bundled 48-cell mock dry-run **48/48** (todo 16 / djangocms 16 / saleor 16; IRA 24 / selective 24; rep1 24 / rep2 24; 48 unique / 0 missing / 0 duplicate / 0 model calls) → **STOP. Pilot = NOT STARTED.**
>
> **HISTORICAL TRUTH (2026-08-15, superseded by the 2026-08-16 Saleor source-visibility fix):** **PILOT-EXEC-01 v0.9.10 RELEASE TRUST GATE CLOSURE CLOSED AND FROZEN AT `v0.9.10-pilot-exec-ready` — MERGED TO MAIN (`44e9a1f`) + TAGGED + TAGGED REBUILD + FINAL ARTIFACT TRUST GATE PASS + 48-CELL DRY-RUN 48/48.** The deployment source is re-frozen at `v0.9.10-pilot-exec-ready` via a REAL two-pass deterministic release-trust-gate finalizer run against the LOCAL repo cache (`dist/pilot-repo-cache`, NO `--allow-acquire`, no network): `python scripts/finalize_pilot_notebook_trust.py --source-commit 80d4d6e581cef60463efde31b414643ba182f35a --source-tag v0.9.10-pilot-exec-ready --repo-cache dist/pilot-repo-cache --created-utc "2026-08-15T14:00:00+00:00"`. Both pinned repo cat-file checks PASS (django CMS `0f633fc9…`, Saleor `e11a5557…`) and `git archive` works in both cache dirs. **Notebook == Identity == Actual proven 4/4** for the four frozen manifest/map hashes: code `bb976f67fefe…` (validated; the v0.9.9 recorded `99688e4e` was stale — it predated the bundled helper-script additions and was never validated against the build), data `8b859ecc7216…`, repository snapshot `49d91d39435f…`, transport path map `07036a36cd97…` (last three byte-identical to v0.9.9); deployed notebook SHA-256 `d15d86831bf8…` == bundled archive bytes, normalized bundled notebook == source `873e97735cd2…`. **No scientific inputs changed** (scenarios, prompts, metrics, model, quantization, timeout 600, repair budget, repository pins, validation scope). Freeze evidence `reports/pilot_notebook_trust_freeze.json` (tracked). Targeted trust-gate closures 142/142 (deployment bundle 52/52, notebook contract 46/46, repo-env provisioning 24/24, real-launch preflight 13/13); full suite **2,234 passed / 33 skipped / 0 failed**; diff-check/ruff/mypy/compile clean. **Post-freeze execution COMPLETE:** independent audit PASS → non-ff merge to main `44e9a1f…` (merge SHA == main HEAD) → tagged rebuild (`--source-commit` = merge SHA, SAME `--created-utc "2026-08-15T14:00:00+00:00"`) → **FINAL ARTIFACT TRUST GATE PASS** (Notebook == Identity == Actual 4/4 on the tagged rebuild; deployed notebook == freeze report; 19/19 trust-gate regression + real artifact expanded simulation) → annotated tag `v0.9.10-pilot-exec-ready` created on the merge commit and pushed (peels to `44e9a1f…`) → exact 48-cell bundled dry-run **48/48 terminal / 48 succeeded / 0 failed / 0 pending / 48 unique run IDs** (per-repo 16/16/16; per-strategy 24/24; per-rep 24/24; 0 model calls). Tagged-rebuild archive SHA-256 `9df1396d50a99da7b3dd101fefe79013c3c253da8fd65251dbd9eb4650e71436` (sidecar matches; identity source_commit == tag peel). **Pilot = NOT STARTED.**
>
> **HISTORICAL TRUTH (2026-08-15, superseded by the v0.9.10 release trust gate closure):** **PILOT-EXEC-01 KAGGLE REPO-ENV PROVISIONING CLOSURE COMPLETE ON BRANCH `fix/pilot-kaggle-env-provisioning-closure` @ `28f0405` — MERGE + TAG `v0.9.9-pilot-exec-ready` PENDING.** The final real Kaggle preflight blocker is closed: on real Kaggle the runtime lock installs pip into the base interpreter, so `python -m venv` (which runs `ensurepip` inside the base interpreter) cannot build a working pip inside a fresh env — the v0.9.8 cell died with `['/kaggle/working/pilot_envs/djangocms/bin/python3', '-m', 'ensurepip', '--upgrade', '--default-pip'] returned non-zero exit status 1` in ~0.24 s (NOT a hang). The bundled stdlib-only helper `scripts/pilot_kaggle_repo_envs.py` (new) provisions every repository validation env WITHOUT the ensurepip path: stdlib venv always `--without-pip`; HOST pip (`<benchmark-python> -m pip --python <target>`) bootstraps the no-pip tool/target envs (documented pip 22.3+ feature for pip-less envs); no-pip `pilot_envs/tools` gets `uv` via host pip `--python`; django CMS deps via `uv pip install -r test_requirements/django-5.0.txt` from the frozen snapshot root (SHA-256 recorded); Saleor = pinned-snapshot copy into `pilot_envs/saleor` + `uv venv .venv --python <existing 3.12>` with `UV_PYTHON_DOWNLOADS=never` (no silent download/switch) then `uv sync --locked`. Completion markers (`.pilot_env_ready.json`, schema `pilot_repo_environment.v1`) + health probes (django `5.0.*` + `import cms`; `import saleor`; `uv --version`) drive reuse; ONLY the specific invalid private env dir is rebuilt (`_remove_private_env`), never arbitrary `/kaggle/working`. OS prerequisites `gettext`+`gcc`+`libpq-dev` (ALL mandatory) install in ONE `apt-get install` transaction and FAIL CLOSED listing ALL missing when apt is unavailable or still missing; the Redis `valkey-server`/`redis-server` alternatives bug is never reintroduced. Visible START/END/elapsed + 30 s heartbeats; provisioning log `preflight/environment_provisioning.log` redacts `HF_TOKEN=`/`SECRET_KEY=`/`PGPASSWORD=` secrets. The `pilot-repo-preflight-cell` is a thin adapter (port asserts on 5433/6379, `importlib.util` helper load, `provision_repository_envs(...)`, then shared `pilot_repo_snapshot.py preflight` with todo=`sys.executable` + provisioned djangocms/saleor interpreters). `scripts/build_pilot_upload_bundle.py` ships the helper at `code/scripts/pilot_kaggle_repo_envs.py` (byte-equal normalized + hashed in `code_manifest.json`). **No scientific inputs changed** (scenarios, prompts, metrics, model, quantization, timeout 600, repair budget, repository pins, validation scope). Gates: new provisioning matrix 24/24 (`tests/integration/test_pilot_repo_env_provisioning.py`, incl. real subprocess log/secret tests + real no-pip venv Gate-K), notebook contract 46/46 (+`test_preflight_is_a_thin_provisioning_helper_adapter`), service bootstrap 41/41, real-launch preflight 13/13, deployment bundle 52/52 (+`test_repo_env_provisioning_helper_bundled_byte_equal_and_hashed`), full suite **2,225 passed / 33 skipped / 0 failed**, diff-check/ruff/mypy/compile clean. Feature commit `28f0405` pushed to `origin/fix/pilot-kaggle-env-provisioning-closure` (docs commit, non-ff merge to main, tag `v0.9.9-pilot-exec-ready`, and exact tagged-archive rebuild are the pending final steps). **Pilot = NOT STARTED**; real launch still deferred until the user confirms the actual Kaggle mounted model path and HF results repository ID.
>
> **HISTORICAL TRUTH (2026-08-15, superseded by the v0.9.9 repo-env provisioning closure):** **PILOT-EXEC-01 KAGGLE-REDIS-PACKAGE-FALLBACK COMPLETE AND MERGED — tagged `v0.9.8-pilot-exec-ready`.** The final real Kaggle preflight blocker is closed: the v0.9.7 cell ran `apt-get install -y valkey-server redis-server`, which aborts the WHOLE apt transaction with `E: Unable to locate package valkey-server` because the real Kaggle Ubuntu (Jammy-shaped) runtime exposes `redis-server` in its configured apt repositories but NOT `valkey-server`. The `service-bootstrap-cell` now provisions the Redis-compatible server binary-first, refreshes apt metadata at most once per invocation (`_apt_update_once`), probes each alternative candidate individually via `apt-cache policy <name>` (`_apt_package_available`, argument-list only, no shell), installs EXACTLY ONE package per `apt-get install` (`_apt_install_one`), records UNAVAILABLE and failed candidates, and FAILS CLOSED with distro/runtime diagnostics when no candidate can be installed — no pip client-package and no in-process fake-server fallback. A selected-implementation label and a proven server `--version` are printed after start; the endpoint stays `127.0.0.1:6379` / `redis://127.0.0.1:6379/0`. The root-safe unprivileged PostgreSQL bootstrap (v0.9.7) is unchanged. **No scientific inputs changed** (scenarios, prompts, metrics, model, quantization, timeout 600, repair budget, repository pins, validation scope). Gates: hermetic service bootstrap contract 41/41 (+14 Redis package-fallback tests incl. MANDATORY Jammy-shaped valkey-unavailable→redis-only, reverse future-distro, install-failure fallback, neither-available/apt-missing fail-closed, apt update-once, start/version service semantics, full-cell end-to-end green; full-cell executor `_exec_cell`), notebook contract 43/43 (+`test_redis_package_fallback_contract`), deployment bundle contract 51/51, full suite **2,199 passed / 33 skipped / 0 failed**, diff-check/ruff/mypy/compile clean. Notebook + `build_pilot_upload_bundle.py`/`finalize_pilot_notebook_trust.py` + deployment-bundle contract moved to `FROZEN_SOURCE_TAG = "v0.9.8-pilot-exec-ready"`. Deployment archive rebuilt from the exact tagged source: **`dist/pilot-kaggle-upload.zip` + `dist/pilot-kaggle-upload.zip.sha256`** (authoritative frozen upload artifacts; never manually re-zip). **Pilot = NOT STARTED**; real launch still deferred until the user confirms the actual Kaggle mounted model path and HF results repository ID.
>
> **HISTORICAL TRUTH (2026-08-13, superseded by the v0.9.8 Redis package-fallback correction):** **PILOT-EXEC-01 KAGGLE POSTGRES ROOT-FIX COMPLETE AND MERGED — tagged `v0.9.7-pilot-exec-ready`.** The real Kaggle blocker is closed: the Kaggle notebook process runs as root while PostgreSQL `initdb`/`pg_ctl` refuse root (`initdb: error: cannot be run as root`), which blocked the v0.9.6 service bootstrap. The `service-bootstrap-cell` now runs the PostgreSQL server lifecycle (initdb, pg_ctl and the postgres server it launches) under the package-native unprivileged `postgres` OS account when the notebook effective uid is 0 — FAILS CLOSED before initdb when that account is missing, NEVER falls back to root, keeps the direct path for non-root notebook processes, uses `subprocess.run(..., user=...)` (POSIX-only, checked; no `runuser`, no `shell=True`), and limits ownership/log preparation to the private service paths (data dir `0o700`, log `0o600`, chown to the postgres uid/gid; incomplete previous clusters recreated — ONLY `PG_DATA_DIR`). The frozen TCP client probe (psql) still runs from the notebook process against `127.0.0.1:5433 saleor/saleor/saleor`; Valkey/Redis `127.0.0.1:6379` unchanged. **No scientific inputs changed** (scenarios, prompts, metrics, model, quantization, timeout 600, repair budget, repository pins, validation scope; the four frozen manifest hashes stay byte-identical). Gates: hermetic service bootstrap contract 28/28 (new `tests/integration/test_pilot_service_bootstrap.py`, exact-cell Gate-H seam), notebook contract 42/42 (+2 root-safe static tests, `FROZEN_SOURCE_TAG = "v0.9.7-pilot-exec-ready"`), deployment bundle contract 51/51, real-launch preflight 13/13, full suite **2,185 passed / 33 skipped / 0 failed**, diff-check/ruff/mypy/compile clean. Deployment archive rebuilt from the exact tagged source: **`dist/pilot-kaggle-upload.zip` + `dist/pilot-kaggle-upload.zip.sha256`** (authoritative frozen upload artifacts; never manually re-zip). **Pilot = NOT STARTED**; real launch still deferred until the user confirms the actual Kaggle mounted model path and HF results repository ID. (Historical points `v0.9.6`, `v0.9.5`, `v0.9.3`, `v0.9.2`, `v0.9.0` immutable, NOT moved.)
>
> **HISTORICAL TRUTH (2026-08-13, superseded by the v0.9.7 root-fix):** **PILOT-EXEC-01 KAGGLE SERVICE BOOTSTRAP LAST-MILE CORRECTION COMPLETE AND MERGED — tagged `v0.9.3-pilot-exec-ready`** (historical execution-ready point `v0.9.2-pilot-exec-ready` @ `e030be5` immutable, NOT moved; `v0.9.0-pilot-ready` @ `90a4282` NOT moved). The frozen Pilot notebook (`notebooks/pilot_exec_01.ipynb`) gained ONE fail-closed, idempotent `service-bootstrap-cell` between repository snapshot verification and the repo-specific preflight — BEFORE any repository validation and model load — that provisions the Saleor validation OS services on a fresh Kaggle session: PostgreSQL `127.0.0.1:5433` (role/db `saleor/saleor@saleor`, private data dir `/kaggle/working/pilot_services/postgres`, `pg_config --bindir` preferred) and Valkey/Redis `127.0.0.1:6379` (persistence disabled), topology mirroring `benchmark_data/manifests/pilot_validation_commands.yaml`; OS installs non-interactive (apt-get; Kaggle Internet ON required, fail loudly offline); no benchmark/model Python environment modification; no secrets printed beyond the frozen non-secret test credentials. **No scientific inputs changed** (scenarios, prompts, metrics, model, quantization, timeout 600, repair budget, repository pins, validation scope). Gates: notebook contract 20/20 (incl. 5 new service-bootstrap tests), deployment bundle contract 14/14, targeted pilot gates 77/77, full suite **2,098 passed / 33 skipped / 0 failed**, diff-check/ruff/mypy/compile clean. Deployment archive rebuilt from the exact tagged source: **`dist/pilot-kaggle-upload.zip` + `dist/pilot-kaggle-upload.zip.sha256`** (authoritative frozen upload artifacts; never manually re-zip). **Pilot = NOT STARTED**; next = exact Kaggle launch prep (upload zip + sidecar as ONE Dataset, attach Pilot notebook + Qwen 14B, Internet ON, HF_TOKEN) -> target preflight -> real Pilot (only after all preflights pass); real launch deferred until the user confirms the actual Kaggle mounted model path and HF results repository ID.
>
> **HISTORICAL TRUTH (2026-08-13, superseded by the service-bootstrap correction):** **PILOT-EXEC-01 real-launch closure Gates 9/10 COMPLETE AND MERGED — main @ `e030be5`; annotated tag `v0.9.2-pilot-exec-ready` created at `e030be5` and pushed** (stable tag `v0.9.0-pilot-ready` @ `90a4282` NOT moved). Gate 9 (engineering preflight): evidence ledger written (`reports/PILOT_EXEC_01_GATE9_ENGINEERING_PREFLIGHT_LEDGER.md`) — saleor `TZ=UTC` frozen in `benchmark_data/manifests/pilot_validation_commands.yaml` (verified 2026-08-11; two `test_transaction_schema_time_valid` cases were drifting by the box UTC offset); the remaining ~31-36 order/pricing saleor failures are an upstream nondeterministic fixture artifact (33 vs 38 observed), not a regression; djangocms `test_filters_date` is a Windows-only strftime artifact (passes on Linux/Kaggle). Gate 10 (final bundle rebuild + proofs): `dist/pilot-kaggle-upload/` + `dist/pilot-kaggle-upload.zip` rebuilt from the TAGGED SOURCE `v0.9.2-pilot-exec-ready` (= merge `e030be5`) with the real repo cache (djangocms `0f633fc9…`, saleor `e11a5557…` at pinned SHAs; todo embedded); notebook byte-matches canonical; `notebook_manifest.json` non-empty + hash-verifies; three repos materialized with pinned SHAs verified; identity frozen contract `v0.9.2-pilot-exec-ready` / `source_commit=e030be5…` / `created_utc=2026-08-13T00:00:00+00:00`; code/data/notebook/repository-snapshot manifest hashes match; archive contains notebook + three repos with no `.git`; deterministic rebuild byte-identical; fresh 48-cell bundled dry-run 48/48 unique / 0 missing / 0 duplicate (todo 16 / djangocms 16 / saleor 16; iterative_repository_agent 24 / selective 24; rep1 24 / rep2 24); targeted gates 67/67 passed (90.88s) on the tagged bundle; sidecar SHA matches (archive SHA-256 `ecb7ea7c85d8bdc527a0384f141b47a1e84ee0b3c3f12b6b8305d880098015f1`); diff-check/ruff/mypy/compile clean. **Pilot = NOT STARTED**; real launch deferred until the user confirms the actual Kaggle mounted model path and HF results repository ID. Remaining: deployment freeze report (`reports/PILOT_EXEC_01_DEPLOYMENT_FREEZE.md`), exact Kaggle launch prep, final report. Prior closure paragraphs below are HISTORICAL.

## Current — PILOT-EXEC-01 v0.9.19 PostgreSQL admin/application bootstrap + partial recovery closure

**Status: `v0.9.19-pilot-exec-ready` — ACCEPTED RELEASE (PostgreSQL
admin/application bootstrap + partial recovery closure, real Kaggle defect
fix). Non-ff merged to main `2305991442a4f965d44bb066bb00c0a459fc395a`;
annotated tag ON that merge commit; artifact trust/provenance GREEN; exact
archive `dist/pilot-kaggle-upload.zip` SHA-256 `f7a16858…`. v0.9.18
release-only provenance/docs correction is PRIOR. All authoritative docs
updated. Real Pilot = NOT STARTED — next = fresh Kaggle v0.9.19 target
preflight, then the accepted 48-cell Pilot in the same session if all target
gates pass (see `docs/AI_ACCOUNT_TRANSFER_HANDOFF.md`).**

## Historical — PILOT-EXEC-01 Saleor source-visibility health-probe fix (v0.9.11, REJECTED FOR LAUNCH — superseded by the v0.9.12 release-provenance closure)

**Status: `REJECTED FOR LAUNCH` — internally-valid artifact, but the immutable
tag does not contain the deployed re-frozen notebook and therefore cannot
reproduce the claimed source snapshot** (v0.9.11, 2026-08-16; feature branch
`fix/pilot-saleor-source-visibility-probe` code/test
`ee3d88b` + docs `228b2e8`; **non-ff merged to main `8801304`; annotated tag
`v0.9.11-pilot-exec-ready` created on the merge commit and pushed**; finalizer
re-freeze `b87aa49` — the re-frozen notebook `85edbd33…` landed ONLY in the
post-tag commit `b87aa49`, NOT in the tagged `8801304`, so the tag does not
contain the deployed notebook). Real Kaggle v0.9.10 failed
ONLY at the new `import saleor` health probe after `uv sync --locked` PASSED
(pinned Saleor `[tool.uv] package = false` → root project never installed into
site-packages; probe ran without `cwd=Saleor working copy`). Fix: optional `cwd`
on `_import_probe`; `_saleor_probe` always probes from `work_dir`; BOTH call
sites fixed (marker/reuse + post-sync). Full suite **2,239 passed / 33 skipped
/ 0 failed**. Finalizer re-freeze: code manifest `7e86eb5dd651…`, data
`8b859ecc7216…`, repository snapshot `49d91d39435f…`, transport map
`07036a36cd97…` (last three byte-identical to v0.9.10); FINAL ARTIFACT TRUST
GATE **Notebook == Identity == Actual 4/4**; archive SHA-256
`039818bde60edcc9693ca88f779c7987bde818ddbfbca705426747b08c6d5453`; bundled
48-cell mock dry-run **48/48** (todo 16 / djangocms 16 / saleor 16;
iterative_repository_agent 24 / selective 24; rep1 24 / rep2 24; 48 unique / 0
missing / 0 duplicate / 0 model calls). **STOP. Pilot = NOT STARTED.**

## Historical — PILOT-EXEC-01 v0.9.10 release trust gate closure (superseded by the v0.9.12 release-provenance closure; v0.9.11 rejected for launch)

**Status: `CLOSED AND FROZEN AT v0.9.10-pilot-exec-ready`** (2026-08-15,
feature branch `fix/pilot-release-trust-gate-closure` `097768e` + docs
`4ac7f0d`; **non-ff merged to main `44e9a1f…`; annotated tag
`v0.9.10-pilot-exec-ready` created on the merge commit and pushed**;
tagged rebuild + FINAL ARTIFACT TRUST GATE + exact 48-cell dry-run all
COMPLETE).

- **Real two-pass deterministic freeze against the LOCAL repo cache** (NO
  `--allow-acquire`, no network): `scripts/finalize_pilot_notebook_trust.py`
  with `--source-commit 80d4d6e… --source-tag v0.9.10-pilot-exec-ready
  --repo-cache dist/pilot-repo-cache --created-utc "2026-08-15T14:00:00+00:00"`;
  discovery build + validation-enabled rebuild
  (`dd5ee529e3a0…`); both pinned repo cat-file checks PASS; `git archive`
  works in both cache dirs.
- **Notebook == Identity == Actual proven 4/4** for the four frozen
  manifest/map hashes against the actually-built bundle; deployed notebook
  `d15d86831bf8…` == bundled bytes; bundled-normalized == source
  `873e97735cd2…`.
- **Code manifest hash corrected to its validated value** `bb976f67fefe…`
  (v0.9.9 recorded `99688e4e` was never validated against the build); data /
  repository snapshot / transport map byte-identical to v0.9.9.
- **No scientific inputs changed**; freeze evidence
  `reports/pilot_notebook_trust_freeze.json` tracked.
- Gates: targeted trust-gate closures 142/142; full suite **2,234 passed / 33
  skipped / 0 failed**; diff-check/ruff/mypy/compile clean.
- **Post-freeze execution COMPLETE:** independent audit PASS → non-ff merge to
  main `44e9a1f4314c2ce8ec0b7abb16c88cbc3f83bfb6` (merge SHA == main HEAD) →
  tagged rebuild (`--source-commit` = merge SHA, SAME `created_utc`) →
  **FINAL ARTIFACT TRUST GATE PASS** (Notebook == Identity == Actual 4/4 on
  the tagged rebuild; deployed notebook == freeze report; trust-gate
  regression + real artifact expanded simulation 19/19) → tag
  `v0.9.10-pilot-exec-ready` (peels to `44e9a1f…`) → exact 48-cell bundled
  dry-run **48/48 terminal / 48 succeeded / 0 failed / 0 pending / 48 unique
  run IDs** (per-repo 16/16/16; per-strategy 24/24; per-rep 24/24; 0 model
  calls). Tagged-rebuild archive SHA-256 `9df1396d50a99da7b3dd101fefe79013c3c253da8fd65251dbd9eb4650e71436`
  (sidecar matches; identity source_commit == tag peel). **Pilot = NOT
  STARTED** — real launch deferred until the user confirms the Kaggle mounted
  model path and HF results repository ID.

## Historical — PILOT-EXEC-01 Kaggle no-pip repository env provisioning closure (superseded by the v0.9.10 release trust gate closure)

**Status: `FEATURE COMPLETE ON BRANCH`** (2026-08-15, branch
`fix/pilot-kaggle-env-provisioning-closure` @ `28f0405`; merge + tag
`v0.9.9-pilot-exec-ready` + exact artifact rebuild pending).

- **Final real Kaggle preflight blocker closed:** the v0.9.8 cell created the
  django CMS env with `python -m venv /kaggle/working/pilot_envs/djangocms`,
  whose internal `ensurepip` step runs against the base interpreter and cannot
  succeed because the Kaggle runtime lock installs pip into that base
  interpreter — the real cell died with
  `['/kaggle/working/pilot_envs/djangocms/bin/python3', '-m', 'ensurepip',
  '--upgrade', '--default-pip'] returned non-zero exit status 1` in ~0.24 s
  (NOT a hang). The SAME latent failure existed in the `tools` env
  (`pilot_envs/tools`). The bundled helper `scripts/pilot_kaggle_repo_envs.py`
  (new, stdlib-only, no-pip design) now provisions every repository validation
  env WITHOUT the failing ensurepip path:
  - stdlib `venv` is ALWAYS created with `--without-pip` (no `ensurepip`
    invocation anywhere);
  - HOST pip `<benchmark-python> -m pip --python <target>` bootstraps the
    no-pip tool/target envs (documented pip 22.3+ feature for pip-less envs;
    pip target compatibility is verified once and cached);
  - the dedicated no-pip `pilot_envs/tools` env gets `uv` via host pip
    `--python`;
  - django CMS deps: `uv pip install -r test_requirements/django-5.0.txt` from
    the frozen snapshot root (dependency file SHA-256 recorded in the marker);
  - Saleor: pinned-snapshot copy into `pilot_envs/saleor`, then
    `uv venv .venv --python <existing 3.12>` with `UV_PYTHON_DOWNLOADS=never`
    (refuses to download a different interpreter) then `uv sync --locked`;
  - completion markers (`.pilot_env_ready.json`, schema
    `pilot_repo_environment.v1`) + health probes (django `5.0.*` +
    `import cms`; `import saleor`; `uv --version`) decide reuse; ONLY the
    specific invalid private env dir is rebuilt (`_remove_private_env`), never
    arbitrary `/kaggle/working`;
  - OS prerequisites `gettext` + `gcc` + `libpq-dev` (ALL mandatory) install in
    ONE `apt-get install` transaction and FAIL CLOSED listing ALL missing when
    apt is unavailable or still missing (probed via `msgfmt`/`gcc`/`pg_config`);
  - visible START/END/elapsed output + 30 s heartbeat threads; provisioning
    log redacts `HF_TOKEN=`/`SECRET_KEY=`/`PGPASSWORD=` secrets.
- **Thin-adapter notebook cell:** `pilot-repo-preflight-cell` asserts
  PostgreSQL 5433 + Valkey/Redis 6379 ports (`_assert_service_port`, global
  `_port_open`), loads the bundled helper via `importlib.util`, calls
  `provision_repository_envs(host_python=sys.executable, ...,
  source_tag=SOURCE_TAG, log_path=PREFLIGHT_DIR/"environment_provisioning.log")`,
  sets TODO_PYTHON=sys.executable + DJANGO_PYTHON/SALEOR_PYTHON from the
  returned evidence, then runs the shared `pilot_repo_snapshot.py preflight`
  with the provisioned interpreters. No `'"-m", "venv"'` code and no
  "ensurepip" token remain in the cell.
- **Bundle shipping:** `scripts/build_pilot_upload_bundle.py` copies the helper
  to `code/scripts/pilot_kaggle_repo_envs.py` (byte-equal normalized + hashed
  in `code_manifest.json`), so the Kaggle cell and the local code always match.
- **Zero scientific drift:** scenarios, prompts, metrics, model, quantization,
  timeout 600, repair budget, repository pins, validation scope all unchanged;
  only the preflight cell, the helper, the bundle builder, the tag
  (`FROZEN_SOURCE_TAG = "v0.9.9-pilot-exec-ready"` pending at merge), and
  related tests/script defaults changed.
- **Gates:** new provisioning matrix 24/24; notebook contract 46/46; service
  bootstrap 41/41; real-launch preflight 13/13; deployment bundle 52/52; full
  suite **2,225 passed / 33 skipped / 0 failed**; `git diff --check` / ruff /
  mypy / compile clean.
- **Pending (this closure):** docs evidence commit + push, independent audit,
  non-fast-forward merge to `main`, push `origin/main`, bump `FROZEN_SOURCE_TAG`
  to `v0.9.9-pilot-exec-ready` (builder + notebook + contract tests), create
  tag, rebuild exact `dist/pilot-kaggle-upload.zip` + `.sha256` from the
  tagged source (authoritative frozen upload archive + sidecar; never manually
  re-zip), bundled 48-cell mock dry-run 48/48, then STOP — real Pilot still
  NOT STARTED.

## Historical — PILOT-EXEC-01 Kaggle Redis package fallback (one apt candidate at a time)

**Status: `COMPLETE`** (2026-08-15, branch `fix/pilot-kaggle-redis-package-fallback`, merged to main, tagged `v0.9.8-pilot-exec-ready`).

- **Final real Kaggle preflight blocker closed:** the v0.9.7 cell ran the
  combined `apt-get install -y valkey-server redis-server`, which aborts the
  WHOLE apt transaction with `E: Unable to locate package valkey-server`
  whenever one candidate is unavailable — and the real Kaggle Ubuntu
  (Jammy-shaped) runtime exposes `redis-server` but NOT `valkey-server`.
  The two candidates are ALTERNATIVES, so a combined install can never be the
  resolution. The `service-bootstrap-cell` now:
  - resolves an already-installed Redis-compatible binary first
    (`_which("valkey-server", "redis-server")`);
  - refreshes apt metadata at most ONCE per cell invocation
    (`_apt_update_once`, shared module-level flag);
  - probes each candidate individually via `apt-cache policy <name>`
    (`_apt_package_available`; argument-list only, never `shell=True`);
  - installs EXACTLY ONE package per `apt-get install` (`_apt_install_one`);
  - records UNAVAILABLE and failed candidates (the exact first install failure
    is retained in the diagnostic evidence) and continues to the next;
  - FAILS CLOSED with distro/runtime facts, candidates checked, unavailable
    list and failed installs when no candidate can be installed — there is NO
    pip client-package and NO in-process fake-server fallback;
  - prints the selected implementation label and proves the server `--version`
    after start (version-command failure is an explicit diagnostic).
- **Endpoint unchanged:** `127.0.0.1:6379` / `redis://127.0.0.1:6379/0`,
  persistence disabled.
- **Hermetic Gate-R verification:** `tests/integration/test_pilot_service_bootstrap.py`
  grows a full-cell executor `_exec_cell` (runs the EXACT provisioning + prove
  section with per-port open flags and apt/`shutil.which` fakes) and 14 new
  tests: already-installed (no apt at all), MANDATORY Jammy-shaped
  (valkey unavailable + redis available → install ONLY redis-server → PASS),
  reverse future-distro (both available → install ONLY valkey-server and stop),
  install-failure fallback, neither-available fail-closed, apt-get/apt-cache
  missing fail-closed, apt update at most once, start-command failure
  propagation, version-command diagnostic, and a full-cell end-to-end
  PG-lifecycle + Redis-fallback green run.
- **Static contract:** `test_redis_package_fallback_contract` forbids the
  combined `"valkey-server redis-server"` install string and requires the
  per-candidate helpers.
- **Zero scientific drift:** scenarios, prompts, metrics, model, quantization,
  timeout 600, repair budget, repository pins, validation scope, and the four
  frozen manifest hashes all unchanged; only the notebook service cell, the
  tag (`FROZEN_SOURCE_TAG = "v0.9.8-pilot-exec-ready"`), and related
  tests/script defaults changed.
- **Gates:** service bootstrap 41/41; notebook contract 43/43; deployment
  bundle contract 51/51; full suite **2,199 passed / 33 skipped / 0 failed**;
  `git diff --check` / ruff / mypy / compile clean.
- **Artifacts:** `dist/pilot-kaggle-upload.zip` + `dist/pilot-kaggle-upload.zip.sha256`
  rebuilt from the exact tag `v0.9.8-pilot-exec-ready` (authoritative frozen
  upload archive + sidecar; never manually re-zip).

## Historical — PILOT-EXEC-01 Kaggle PostgreSQL root fix (unprivileged bootstrap)

**Status: `COMPLETE`** (2026-08-13, branch `fix/pilot-kaggle-postgres-unprivileged-bootstrap`, merged to main, tagged `v0.9.7-pilot-exec-ready`; superseded by the v0.9.8 Redis package-fallback correction).

- **Real Kaggle blocker closed:** the real v0.9.6 Kaggle preflight failed at
  `initdb: error: cannot be run as root` — the Kaggle notebook process runs as
  root while PostgreSQL `initdb`/`pg_ctl` refuse root. The
  `service-bootstrap-cell` now resolves the package-native unprivileged
  `postgres` OS account (`pwd.getpwnam`) whenever the notebook effective uid is
  0 and runs the PostgreSQL server lifecycle under that account:
  - `initdb`, `pg_ctl start` and the postgres server process it launches run
    with `user="postgres"` via `subprocess.run(..., user=...)` (POSIX-only,
    uid-checked, fail-closed; never `runuser`, never `shell=True`).
  - FAILS CLOSED before initdb when the `postgres` account is missing (no
    silent fallback to root — falling back would reproduce the exact Kaggle
    blocker).
  - Non-root notebook processes keep the existing direct path (`user=None`).
  - The frozen TCP client probe (`psql "SELECT 1"`) still runs from the
    notebook process against `127.0.0.1:5433 saleor/saleor/saleor`.
  - Ownership/log preparation is limited to the private service paths
    (`SERVICES_ROOT`, `PG_DATA_DIR`, `PG_LOG`): data dir `0o700`, log `0o600`,
    chown to the postgres uid/gid; incomplete previous clusters (no
    `PG_VERSION`) are safely recreated — ONLY `PG_DATA_DIR`, never the Pilot
    bundle or repository snapshots.
- **Valkey/Redis at v0.9.7 (HISTORICAL):** `127.0.0.1:6379`, persistence
  disabled, `valkey-server` preferred else `redis-server` — superseded by the
  v0.9.8 per-candidate package fallback above.
- **Hermetic Gate-H verification:** `tests/integration/test_pilot_service_bootstrap.py`
  (28 tests) execs the EXACT cell definitions (truncated at the
  `# ---- Provision and prove` marker) with `os`/`pwd`/`subprocess`/`socket`
  fakes — no root, no real services, no network. Gates B (root contract),
  C (non-root), D (missing service user fails closed), E (partial cluster
  state), F (service proof semantics), H (exact command construction).
- **Zero scientific drift:** scenarios, prompts, metrics, model, quantization,
  timeout 600, repair budget, repository pins, validation scope, and the four
  frozen manifest hashes all unchanged; only the notebook service cell, the
  tag (`FROZEN_SOURCE_TAG = "v0.9.7-pilot-exec-ready"`), and related tests/script
  defaults changed.
- **Gates:** notebook contract 42/42; deployment bundle contract 51/51;
  real-launch preflight 13/13; full suite **2,185 passed / 33 skipped / 0
  failed**; `git diff --check` / ruff / mypy / compile clean.
- **Artifacts:** `dist/pilot-kaggle-upload.zip` + `dist/pilot-kaggle-upload.zip.sha256`
  rebuilt from the exact tag `v0.9.7-pilot-exec-ready` (authoritative frozen
  upload archive + sidecar; never manually re-zip).

## Historical — PILOT-EXEC-01 Kaggle service bootstrap last-mile correction

**Status: `COMPLETE`** (2026-08-13, branch `fix/pilot-kaggle-service-bootstrap`, merged to main, tagged `v0.9.3-pilot-exec-ready`; superseded by the v0.9.7 root-fix).

- **Launch blocker closed:** the frozen Pilot notebook only probed the Saleor
  PostgreSQL/Valkey services in the shared preflight and assumed they were
  already running. A fresh Kaggle session has no such OS services, so the
  notebook now provisions them in ONE new fail-closed, idempotent
  `service-bootstrap-cell` (placed after repository snapshot verification,
  before the repo-specific preflight — i.e. before any repository validation
  and any model load):
  - PostgreSQL `127.0.0.1:5433` — role/db `saleor/saleor@saleor`, private
    data dir `/kaggle/working/pilot_services/postgres`, binaries located
    deterministically (prefer `pg_config --bindir`), non-interactive OS
    install fallback via apt-get (Kaggle Internet ON required — fail loud,
    never silent).
  - Valkey/Redis `127.0.0.1:6379` — `valkey-server` preferred, else
    `redis-server` (Redis protocol contract), persistence disabled.
  - Proves both ports reachable, proves a real PostgreSQL connection with the
    frozen credentials, prints service versions/host/ports, prints no secrets
    beyond the frozen non-secret test credentials, and STOPs before
    repository validation / model load on any install/startup/health failure.
- **Isolation preserved:** OS provisioning never modifies the benchmark/model
  Python environment; the isolated django CMS and Saleor environments remain
  untouched; no `pip install` of Saleor/django CMS deps into the model runtime.
- **Zero scientific drift:** scenarios, prompts, metrics, model, quantization,
  timeout 600, repair budget, repository pins, validation scope all unchanged.
- **Gates:** notebook contract 20/20 (incl. 5 new service-bootstrap tests);
  deployment bundle contract 14/14; targeted pilot gates 77/77; full suite
  **2,098 passed / 33 skipped / 0 failed**; `git diff --check` / ruff / mypy /
  compile clean.
- **Artifacts:** `dist/pilot-kaggle-upload.zip` + `dist/pilot-kaggle-upload.zip.sha256`
  rebuilt from the exact tag `v0.9.3-pilot-exec-ready` (authoritative frozen
  upload archive + sidecar; never manually re-zip).

## Historical — PILOT-EXEC-01 real-launch closure (Gates 9/10 complete)

**Status: `COMPLETE`** (2026-08-13, branch `fix/pilot-real-launch-closure`; superseded by the service-bootstrap correction above).

- Gate 9 (engineering preflight evidence): recorded preflight runs
  (`preflight_todo_djangocms.json`, `preflight_saleor.json`,
  `preflight_saleor_tzfix.json`, `saleor_primary_rerun.txt`,
  `saleor_failures_tb.txt`) summarized in
  `reports/PILOT_EXEC_01_GATE9_ENGINEERING_PREFLIGHT_LEDGER.md`. todo PASS
  (47/47); djangocms 382 tests with one Windows-only `test_filters_date`
  strftime error (passes on Linux/Kaggle; documented in
  `repository_versions.yaml`); saleor 6~7k tests with a nondeterministic
  ~31-36 order/pricing cluster (33 vs 38 observed) classified as an upstream
  fixture/hardware artifact; the two `test_transaction_schema_time_valid`
  cases were TZ drift — fixed and frozen with `TZ=UTC`.
- Gate 10 (final bundle rebuild + proofs): `dist/pilot-kaggle-upload/` +
  `dist/pilot-kaggle-upload.zip` rebuilt from the closure state via
  `scripts/build_pilot_upload_bundle.py --repo-cache <real cache>
  --source-commit e030be5f… --source-tag v0.9.2-pilot-exec-ready
  --created-utc 2026-08-13T00:00:00+00:00`. All 20 proof checks pass
  (notebook byte-match; non-empty verifiable `notebook_manifest.json`; three
  repos + pinned SHAs verified; identity frozen contract; code/data/notebook/
  repository-snapshot manifest hashes match emitted bytes; archive contains
  notebook + three repos, no `.git`; sidecar SHA matches). Deterministic
  rebuild byte-identical. Fresh 48-cell bundled dry-run 48/48 unique / 0
  missing / 0 duplicate. Targeted gates: deployment bundle + notebook
  contract + repo snapshot + validation mapping + real-launch preflight
  = 67 passed. `git diff --check` clean; ruff clean; mypy clean; compile
  clean. Archive SHA-256 `ecb7ea7c85d8bdc527a0384f141b47a1e84ee0b3c3f12b6b8305d880098015f1`.

**Status: `IN PROGRESS`** (2026-08-10, branch `experiment/pilot-exec-01`).

- Gate A3 (deployment build): `scripts/build_pilot_upload_bundle.py` created —
  reuses `scripts/build_upload_bundle.py` via importlib, redirects output to
  `dist/pilot-kaggle-upload/`, omits the Smoke notebook, deterministic zip,
  writes `pilot_deployment_identity.json`, refuses output root ==
  `kaggle_upload`. Built bundle = 90 code + 56 data files; archive SHA-256
  `8c52d26b69e9fc0a072d68ba89b9a300e2e8351ba0902e32c71f96ecc45b2de7`;
  identity `created_utc 2026-08-10T00:00:00+00:00`, `source_commit 72d041d9...`,
  `source_tag v0.9.1-pilot-exec-ready`, code/data manifest SHA-256s.
- Gate A4 (deployment contract): new 12-test `test_pilot_deployment_bundle.py`
  12/12 passed; affected contracts 126/126 passed (incl. historical Smoke
  identity).
- Gate A5 (bundled dry-run): fresh 48-cell exact Pilot dry-run 48/48 terminal /
  48 unique IDs / 0 missing / 0 duplicate; per-repo 16/16/16; per-strategy
  iterative_repository_agent 24 / selective 24; per-rep 24/24.
- Gate A6 (full gate): full suite **2,038 passed / 33 skipped / 0 failed**
  (750.99s); `git diff --check` clean; ruff clean; mypy strict clean on new
  script; compile clean.
- Gate B (pre-registration): `docs/PILOT_EXEC_01_EXECUTION_CONTRACT.md` +
  DECISION_LOG D025 pre-registered; `docs/PILOT_KAGGLE_RUNBOOK.md` created;
  `docs/KAGGLE_EXECUTION_GUIDE.md` Pilot cells/table/session-limits corrected
  (explicit `--qwen-quantization bnb-nf4`, no `--max-runs 2`, Pilot bundle
  slug guidance, no pre-Pilot wall-time estimate).
- Next: commit (deployment code/test + docs) -> push -> independent
  pre-execution audit -> merge to main -> push -> tag `v0.9.1-pilot-exec-ready`
  -> rebuild bundle from tagged source -> verify -> deployment freeze report ->
  exact Kaggle launch prep -> final report. **Pilot = NOT STARTED.**

## Latest closure — PILOT-READY-01 (Pilot readiness closure)

**Status: `CLOSED`** (2026-08-10, branch `feat/pilot-ready-01`). See
`reports/PILOT_READY_01_FINAL_REPORT.md` for the full detailed report.

- Root causes fixed: (A) `build_dependency_graph` reused one graph built from
  the first repository's snapshot on mixed-repository plans → now fails closed
  on mixed repositories, `build_repository_dependency_graphs` builds one graph
  per repository, Pilot run loop uses `_dep_graphs[repository_id]`; (B)
  editable-path expansion applied globally instead of per repository profile →
  now per-repository `expand_editable_paths`; (C) artifact catalog
  normalization produced category-key descriptors for django CMS/Saleor →
  `_normalize_artifact_catalog`/`descriptors_from_profile` yield file-granular
  descriptors ⊆ editable universe; (D) stale real-smoke expectation →
  `STRATEGIES_WITH_MISSING_PREREQS = {"agent"}`.
- Gates: Gate 1 unit contract 14 passed; Gate 2 real-smoke 9 passed; Gate 3
  production-path 12 passed (twice, no state leak); Gate 4 static/compile clean
  (feature-caused mypy fixed; 5 pre-existing mypy + 3 pre-existing ruff
  recorded as debt); Gate 5 exact fresh 48-cell Pilot dry-run 48/48 succeeded /
  0 failed / 0 pending, deterministic unique run IDs (config_hash
  `7ef6ffc7a2c0d369`, protocol 1.0, source_commit `34ecf78`), per-repo
  todo/djangocms/saleor 16/16/16, per-strategy 24/24, per-rep 24/24, checkpoint
  completed, no residue; Gate 6 isolation/evidence/export 142 passed; Gate 7
  final full suite **2,026 passed / 33 skipped / 0 failed**.
- Commit `34ecf78` pushed; local feature HEAD == remote feature HEAD. **Pilot =
  NOT STARTED; next = `PILOT-EXEC-01`; stable tag `v0.9.0-pilot-ready` after
  main merge.**

## Previous closure — MAIN-GREEN-01 (post-merge test-isolation and reproducibility hotfix)

**Status: `FIXED AND CLOSED`** (2026-08-09, branch `fix/main-green-test-isolation`,
commit A `34b9fc7` pushed). After the SMOKE-V2-CLOSE-01 merge to main
(`193d889`), the full suite regressed to **12 failed / 4 errors** on the Windows
working tree. This was a **working-tree state defect, NOT a scientific or merge
regression**.

### Symptoms (RED, all deterministically reproduced)
- Bundle fingerprint: `tests/evaluator_assets/todo_smoke_*_checks.py` SHA-256
  mismatch (recorded LF blob hash vs CRLF working-tree hash).
- Scripted/integration cells: wrong-stage failures; sequential isolation
  `expected exactly one new migration, got ()` — cell diagnostics showed
  `todo/permissions.py` / `todo/urls.py` rejected as `out_of_scope_change`.
- Baseline compatibility: comparing `__pycache__/test_models.cpython-311.pyc`
  bytecode residue.

### Root cause
`core.autocrlf=true` on Windows checked out byte-frozen LF fixtures as CRLF:
(A) bundle evaluator assets (only the root `tests/evaluator_assets/` path was
LF-pinned in `.gitattributes`, not the `kaggle_upload/code/...` bundle path);
(B) `benchmark_data/repositories/todo/**` — backend reads LF (universal
newlines), executor writes verbatim LF (`regeneration.py:801
write_text(..., newline="")`), so preserve-files differed byte-wise and were
rejected; (C) `_baseline_hashes()` included regenerated `.pyc` residue.

### Merge drift
Ruled out: `193d889^{tree}` == `65f9fb8^{tree}` == `fdd72f6…`;
`git diff --name-status 65f9fb8..193d889` empty.

### Changed files (zero scientific drift)
- `.gitattributes` — `text eol=lf` pins for the bundle evaluator assets,
  `benchmark_data/repositories/todo/**`, `kaggle_upload/data/repositories/todo/**`;
  LF renormalization verified (zero CRLF remain; only `.gitattributes` shows
  modified → zero blob changes).
- `tests/support/evaluator_fixture_workspaces.py` — `_EPHEMERAL_BASELINE_MARKERS`
  + `_is_ephemeral_baseline_path`; `_copy_baseline` copytree ignore.
- `tests/integration/test_todo_smoke_evaluator_assets.py` — `_baseline_hashes()`
  skips ephemeral paths.
- NEW `tests/unit/test_baseline_ephemeral_policy.py` (T1/T2);
  `tests/unit/execution/test_isolation.py` (T3).
No production `src/` code, prompts, datasets, strategies, metrics, model
identity, or timeout changed.

### Repeatability evidence
- T4 representative monolithic cell `test_r5_representative_monolithic_cell_todo_smoke_001`: 2/2 PASS (18.20s, 18.52s).
- T5 sequential isolation `test_r5_sequential_workspace_isolation_001_002_003`: 2/2 PASS (160.27s, 158.62s).
- T6 fingerprint contract: PASS.
- T7 affected subset twice each: production-path 45 (447.21s, 464.50s); todo
  evaluator assets 53 passed + 1 skipped (129.61s, 129.74s); kaggle bundle 51
  (58.18s, 57.05s).
- T8 related regression: 380 passed / 22 skipped (14.68s).

### Full-suite evidence
T9 full suite once: **1,958 passed / 33 skipped / 0 failed / 0 errors**
(724.84s). Static gates: compileall clean; ruff clean on changed files;
`git diff --check` clean; mypy unchanged (no production files changed — only
pre-existing findings in unchanged test code).

### Scientific non-impact
Zero. Merge-tree equality + zero blob changes prove no scientific input
changed. Pre-benchmark validation: Dataset/Prompt/Metric carried-forward
(zero drift); Pipeline Smoke + Dry Run PASS (8/8, 0 failed, fresh output dir);
Integration Test PASS (production-path module twice). Note: re-running the
dry-run in the SAME output dir hits pre-existing stale-record validation
(`ReportRebuildError: Unexpected Run IDs`, `reports.py:164`) — pre-existing,
out of scope, documented in PROJECT_HANDOFF.

### GitHub/tag state
- Branch `fix/main-green-test-isolation` pushed (upstream
  `origin/fix/main-green-test-isolation`).
- Commit A `34b9fc7` pushed; commit B (this docs commit) pending.
- Old tag `v0.8.0-smoke-v2-complete` unchanged (immutable provenance at
  `193d889`).
- After audit + non-ff merge: new annotated tag `v0.8.1-smoke-v2-complete`
  (peeled == new main HEAD).

### Next phase
`PILOT-READY-01` — repository ready for the Pilot phase; Pilot NOT started.
Sentinel: `MAIN_GREEN_01_CLOSURE_AUDIT_REQUIRED`.

## Previous closure — SCIENTIFIC SMOKE V2 COMPLETE AND ACCEPTED (SMOKE-V2-CLOSE-01)

**Status: `CLOSED — EXECUTED AND ACCEPTED`** (2026-08-09, branch
`fix/kaggle-smoke-v2-model-output-closure`). The 600-second confirmatory
timeout-sensitivity Full-9 (**T600**, contract FULL9-T600-01) was **EXECUTED
AND ACCEPTED**: run `exp-20260808-222843`, uniform `--timeout 600` on the
frozen runtime source/build `7f2a450`, fail-closed output namespace
`/kaggle/working/runs/qwen14b_bnb_nf4_full9_scientific_smoke_wsfix_7f2a450_t600`,
evidence prefix `corrected-full9-t600-wsfix-7f2a450-`.

**Accepted result: 9/9 terminal / 2 successes / 7 scientific failures / 0
engineering blockers / 0 budget-exhausted / 63 model calls / 77,929 tokens /
max run ≈373 s / Full-9 verification PASS / HF synchronization PASS** — the
**same 2/9 result** as the accepted clean 300-second baseline (runtime
`7f2a450`, `--timeout 300`, valid and preserved: 9/9 terminal / 2 successes /
7 scientific failures / 0 engineering blockers, with three runs at or beyond
the ~300-second scientific per-run workflow ceiling (~307–337 s)).
**Timeout sensitivity confirmed: the 600-second ceiling did NOT change the
accepted result; the 300-second baseline signal was not distorted by timeout
censoring. This is NOT an improvement claim.** The 300-second baseline remains
valid and preserved and is NOT invalidated or replaced. The uniform per-run
workflow timeout is now frozen at **600s** for monolithic / selective /
iterative_repository_agent (one shared Full-9 command; no strategy receives
extra time). **Do NOT raise the timeout above 600** — if Pilot runs accumulate
near 600 s, analyze the duration/repair distribution and pre-register the
Pilot budget instead.

Pre-benchmark validation recorded at contract time (2026-08-08, carried forward):
- Dataset PASS / carried-forward (zero drift); Prompt PASS / carried-forward
  (zero drift); Metric PASS / carried-forward (zero metric/evaluator drift).
- Pipeline Smoke PASS (T600 command + fail-closed `_t600` namespace contract).
- Dry Run PASS (exact 3×3 no-model/bundled dry-run contract with scientific
  timeout 600).
- Integration Test PASS: final executable full suite
  **1,947 passed / 33 skipped / 0 failed**.

Audit:
- Executable implementation PASS; over-engineering PASS (one protocol value,
  one isolated namespace, contract tests only); scientific identity PASS
  (runtime source/build remains the frozen `7f2a450` deployment identity —
  runtime source did not change).
- Non-destructive RED proof recorded: the committed HEAD notebook
  (`--timeout 300`) FAILS the new 600-second contract; the working notebook
  satisfies it.

**HISTORICAL (all completed) — next authorized action was: independent delta
audit of the Scientific Smoke V2 closure (SMOKE-V2-CLOSE-01); after acceptance,
main merge + stable tag `v0.8.0-smoke-v2-complete`, then `PILOT-READY-01`.**
All executed: closure audited and merged (`193d889`), stable tag
`v0.8.0-smoke-v2-complete` created, MAIN-GREEN-01 merged (main `d875c72`),
preferred recovery tag `v0.8.1-smoke-v2-complete`; **next = `PILOT-READY-01`
(Pilot NOT STARTED)**. Pilot / fine-tune remain unauthorized. No further Kaggle
Full-9 is authorized; the accepted T600 run is the final Smoke evidence.
Sentinel: `SMOKE_V2_CLOSURE_AUDIT_REQUIRED`.

## Previous closure — FULL9-EXEC-01 canonical corrected Full-9 notebook execution closure

**Status (HISTORICAL — superseded by SMOKE-V2-CLOSE-01): `COMPLETE — was pending independent delta audit before Kaggle Full-9`**
(2026-08-08, Commit A `c4aee03` `feat(kaggle): make corrected Full-9 notebook
executable`, pushed, local = remote, tree clean, branch
`fix/kaggle-smoke-v2-model-output-closure`).

The canonical Kaggle notebook is now the single, tested, fail-closed execution
artifact for exactly one fresh corrected Full-9. The setup-cell bootstrap
regression was fixed (undefined `MODEL_DIR` NameError → `MODEL_CANDIDATES`
initialized from `KNOWN_MODEL` and `MODEL_PATH` derived from it; `src_dir` guard
+ `sys.path.insert`; `SCRIPT_PATH.is_file()` guard) and all stale execution
routes were removed: setup order = setup-cell → install-lock-cell →
preflight-cell → secrets-cell → full9-execution-cell → full9-verification-cell →
export-evidence-cell, with no generic/canary/continuous cells.

**Latest Kaggle attempt truth:** source/build `7f2a450`; runtime
install/preflight PASS; a redundant corrected-source selective canary ran and
succeeded — **that attempt is NOT a Full-9**; corrected Full-9 evidence remained
**0/9** at that time (later executed and accepted as `exp-20260808-222843`);
the evidence ZIP downloaded from that session must NOT be labeled
accepted Full-9 evidence.

**Validation:** full suite **1,947 passed / 33 skipped / 0 failed**; targeted
notebook/CLI/bundle 137 passed; related production-path/isolation regression
45 + 33 passed / 1 skipped; notebook JSON parse OK; all canonical code cells
compile; bootstrap symbol-closure clean; bundle rebuilt and verified
(code/data/notebook parity, no forbidden artifacts); canonical/bundled notebook
parity proven; zero data/prompt/metric/runtime drift.

**HISTORICAL next action (superseded — the T600 corrected Full-9 was executed
and accepted as `exp-20260808-222843`): independent delta audit of
FULL9-EXEC-01; after acceptance, exactly one fresh corrected Full-9.** Main
merge / stable tag / Pilot / fine-tune remain unauthorized (all since completed
except Pilot). No Kaggle run was performed in this task.

## Executive decision

The real Kaggle Full-9 `exp-20260807-205422` (physically completed 9/9 under
runtime source `f7b1ebb`) is **REJECTED as a stable scientific matrix** by the
independent audit — raw result **2 succeeded / 7 failed**, raw total **62 model
calls / 76,858 tokens**. Root cause = **overlay source restaging leaked
generated files across scenarios**: each strategy workspace was reused across
scenarios and `_populate_workspace_source` overlaid the immutable snapshot
without deleting stale generated files, so `todo/migrations/0004_task_priority.py`
from scenario 001 survived into scenario 002 and produced
`0005_remove_task_priority_task_deleted_at`, contaminating the selective/agent
002 and 003 records. **The defect is closed** on branch
`fix/kaggle-smoke-v2-model-output-closure` (Commit A `7f2a450` + Commit B
`e29c017`, pushed, local = remote, tree clean). Official pre-benchmark gate
(`_workspace\cache\prebenchmark-py311`, Python 3.11.9 / pytest 8.4.2 exactly):
**1,928 passed / 33 skipped / 0 failed**. The isolated selective canary remains
accepted; `v0.8.0-canary.1` unchanged.

**Follow-up docs closure FULL9-WS-02A (2026-08-08, docs/runbook only):** the
independent GPT-5.6 Sol audit **ACCEPTED the runtime workspace-isolation fix
(`7f2a450`, deployment re-pinned by `e29c017`)** but **blocked a new Full-9**
because the canonical runbook still launched source/build `f7b1ebb` and its
output directory did not fail closed on pre-existing records. This closure
corrected `docs/KAGGLE_QWEN14B_FULL9_SCIENTIFIC_SMOKE_RUNBOOK.md` to launch with
**SOURCE_COMMIT=`7f2a4509482dc7e62c2b243374592e9a88e2ff48` /
DEPLOYED_BUILD_ID=`7f2a450`**, setup order **setup-cell -> install-lock-cell ->
preflight-cell -> secrets-cell -> Full-9**, a fresh fail-closed output directory
**`/kaggle/working/runs/qwen14b_bnb_nf4_full9_scientific_smoke_wsfix_7f2a450`**
(raises if already non-empty), and an initial command with **no
`--strategy` / `--max-runs` / `--auto-resume-hf`**. Truth at that time
(HISTORICAL): accepted selective canary `exp-20260807-131819`; first Full-9
`exp-20260807-205422` = **RUN BUT REJECTED** (workspace contamination);
**corrected fresh Full-9 = NOT YET RUN** (later executed and accepted as
`exp-20260808-222843`). **HISTORICAL next action (superseded): independent
delta audit of the FULL9-WS-02A docs/runbook closure; only if accepted, exactly
one fresh corrected Full-9 with source/build `7f2a450`** — not a merge, tag, or
Pilot.

## Why this closure existed

The first real Full-9 attempt under the previously pinned source/build
(`f7b1ebb`) completed all 9 planned records, but the audit proved the source
restaging was an **overlay**, not a reset: workspaces accumulated stale
generated files across scenarios, so scenario 002/003 records for the
selective and iterative-repository-agent arms were computed against
contaminated source trees. The rejected Full-9 is **preserved as evidence
only** and must never be used as the accepted aggregate.

## The exact reset contract (Commit A `7f2a450`)

- `_WORKSPACE_INFRASTRUCTURE_DIRS = frozenset({"runs", "tmp", "snapshots"})`.
- `_reset_workspace_source_from_snapshot(workspace_dir, snapshot_root)`
  replaces `_populate_workspace_source`: the source tree is deleted first
  (every symlink/file unlinked, every directory removed), then restaged from
  the snapshot — stale generated files cannot survive.
- `_skip_subdirs = frozenset({"_metadata", "manifests"})` for generated-command
  scans.
- `make_isolation` calls the reset for every arm workspace on every run, so
  every matrix cell starts byte-identical to the immutable snapshot and leaves
  zero residue.

## Tests added

- **Unit** (`tests/unit/execution/test_isolation.py`,
  `TestResetWorkspaceSourceFromSnapshot`): deletes stale generated files,
  restores canonical files, preserves infrastructure dirs, symlink/empty-dir
  handling, missing-infra tolerance, root `.gitignore` preservation,
  3-strategy parameterization — **33 passed / 1 skipped** (symlink skipped on
  Windows, runs on Linux/Kaggle).
- **Sequential integration** (`tests/integration/test_scientific_smoke_v2_production_path.py`
  "Step 5b"): 001→002→003 per strategy — 001 produces exactly
  `0004_task_priority.py`; restaging returns to canonical-only byte-identical
  files; 002's migration is clean (depends only on canonical `0003`, no
  `0004_task_priority`, no `priority`); 003's migration contains `"owner"`;
  nine-run zero-residue matrix — **4 passed** (production-path file 45 passed).

## Gate totals (official clean env `_workspace\cache\prebenchmark-py311`, Python 3.11.9 / pytest 8.4.2 exactly)

```text
Dataset Validation      PASS  161 passed / 1 skipped — 27 scenarios unchanged; scopes intact
Prompt Validation       PASS  200 passed / 12 skipped
Pipeline Smoke Test     PASS  45 passed — incl. sequential stale-migration regression
Scripted 9-record Dry Run PASS 9 planned / 9 terminal / 9 succeeded / 0 failed, exit 0
Complete Integration    PASS  1,928 passed / 33 skipped / 0 failed (859.46 s)
Metric Verification     PASS  187 passed
Ruff                    0 new (5 pre-existing baseline)
strict mypy             0 new (4 pre-existing baseline)
compileall              clean
Notebook compilation    PASS  canonical + bundled compile
builder/manifests       PASS  content-identical rebuild (147 files / 969,713 bytes)
```

## Commit hashes and remote equality

```text
86acb29  docs(state): record canary milestone tag and freeze Full-9 launch (starting HEAD)
7f2a450  fix(smoke): reset workspace source before every matrix run          (Commit A, pushed)
e29c017  chore(deploy): repin isolated Full-9 Smoke bundle                   (Commit B, pushed)
```

All pushed to `origin/fix/kaggle-smoke-v2-model-output-closure`; local = remote
verified after each push. Working tree clean.

## Next action

**HISTORICAL (superseded — the corrected Full-9 was executed and accepted as
`exp-20260808-222843`):** after the independent delta audit of the FULL9-WS-02A
docs/runbook closure: **exactly one fresh corrected Full-9 Scientific Smoke V2**
with the corrected
deployment source/build `7f2a450` (SOURCE_COMMIT=`7f2a4509482dc7e62c2b243374592e9a88e2ff48` /
DEPLOYED_BUILD_ID=`7f2a450`, fail-closed fresh output dir) — one engineering preflight +
one benchmark process in a fresh isolated experiment; never resume/merge the
rejected `exp-20260807-205422` records or workspaces; never merge the accepted
canary; then independent results audit. Record:
`selective_updates/records/FULL9-WORKSPACE-ISOLATION-DEFECT-2026-08-08.md`.
Sentinel: `FULL9_WORKSPACE_ISOLATION_CLOSURE_AUDIT_REQUIRED`.

---

## Prior phase (2026-08-07) — Qwen 14B Selective Canary Success

# Qwen 14B Selective Canary Success — Latest Phase Report

## Executive decision

The independent GPT-5.6 Thinking audit **ACCEPTED SUCCESSFUL REAL CANARY** on branch `fix/kaggle-smoke-v2-model-output-closure` (documentation HEAD `5561f918`). Docs-only closure — no code, tests, data, prompts, configs, notebook executable cells, or `kaggle_upload` changes. Real engineering preflight **PASS** on 2×Tesla T4 and the dedicated selective canary `exp-20260807-131819` **succeeded**. Accepted real 14B canary records = **1 succeeded / 0 failed** (isolated selective-only plan — NOT `1/9`). **Milestone tag `v0.8.0-canary.1` = created and pushed, annotated, NON-STABLE** (first accepted real Qwen 14B NF4 selective-canary milestone, points to `31a619857ce07eb09ab5e206fbc9dc792782c99c`). At the time this canary was accepted, **Full 9-record Scientific Smoke V2 = NOT RUN** (subsequently the first Full-9 `exp-20260807-205422` ran under `f7b1ebb` and was REJECTED for workspace contamination; a fresh corrected Full-9 under `7f2a450` was NOT YET RUN at that time, pending the FULL9-WS-02A delta audit — HISTORICAL, later executed and accepted as `exp-20260808-222843`). **HISTORICAL (at that time):** Main merge = pending corrected Full-9 audit (NOT YET) — NOW COMPLETE (SMOKE-V2-CLOSE-01 merged `193d889`, MAIN-GREEN-01 `d875c72`); Stable Smoke tag `v0.8.0-smoke-v2-complete` = not yet created then, CREATED at `193d889` (preferred recovery `v0.8.1-smoke-v2-complete`); Pilot = NOT AUTHORIZED (now NOT STARTED). **HISTORICAL next action (superseded): independent delta audit of the FULL9-WS-02A runbook/docs closure, then exactly one fresh corrected Full-9 Scientific Smoke V2** using the corrected runbook `docs/KAGGLE_QWEN14B_FULL9_SCIENTIFIC_SMOKE_RUNBOOK.md`. No stable release claimed at that time (HISTORICAL — stable release `v0.8.0-smoke-v2-complete` now created; preferred recovery `v0.8.1-smoke-v2-complete`).

## Why this phase existed

After the Multi-GPU VRAM preflight closure (2026-08-06) closed the last engineering blocker, the independent audit authorized and the real 14B selective canary was executed on Kaggle to prove the Qwen 14B bnb-nf4 stack end-to-end (preflight → model load → selective plan → generation → validation → evaluation → HF recovery upload) before committing to the full 9-record Scientific Smoke V2.

## What happened (real Kaggle evidence, 2026-08-07)

- **Real engineering preflight PASS** on 2×Tesla T4 (Python 3.12.13 / transformers 4.57.6 / bnb-nf4): identity `qwen:14b-instruct-v1:bnb-nf4:cfg-cc9474140d25`; footprint 9,721,981,184 bytes; preflight 174.016 s; probe 68+17 tokens; minimum free VRAM **8.417 GiB** — GPU-only device map, no offload.
- **Canary `exp-20260807-131819`** (`todo-smoke-001 / selective`, runtime source `f7b1ebba73b52868a95c47ef3806d3b09da16d93` / build `f7b1ebb`) = **succeeded**: 3 selected / 2 preserved / 3 regenerated; one migration `todo/migrations/0004_task_priority.py`; 3 model calls / 2,527 prompt + 720 completion = 3,247 tokens / 295.944 s / 0 repair attempts; functional validation PASS; scenario evaluator **PASS 10/10**; HF `recovery_uploaded`.

## Interpretation and caveats

14B crossed the 7B model-quality floor on the same task: **25.0% fewer calls / 44.1% fewer tokens / repair eliminated / 14.9% slower** — functional viability, not strategy superiority. Generated `views.py` has an unused `Q` import (non-blocking; evidence workspace must NOT be repaired). The continuous cell failed closed with zero model calls because the generic experiment was empty — not a failure; do NOT patch the continuous workflow before Full-9.

## Next action

**HISTORICAL — SUPERSEDED (the corrected Full-9 was executed and accepted as `exp-20260808-222843`; current next task = `PILOT-READY-01`).** Was: independent delta audit of the FULL9-WS-02A docs/runbook closure; only if accepted, exactly one fresh corrected Full-9 Scientific Smoke V2 (3 scenarios × 3 arms = 9 records; SOURCE_COMMIT=7f2a4509482dc7e62c2b243374592e9a88e2ff48 / DEPLOYED_BUILD_ID=7f2a450, fail-closed fresh output dir) via the corrected `docs/KAGGLE_QWEN14B_FULL9_SCIENTIFIC_SMOKE_RUNBOOK.md` — one engineering preflight + one benchmark process, fresh isolated experiment, never resume/merge the canary or the rejected `exp-20260807-205422`, then independent results audit. Record: `selective_updates/records/QWEN14B-SELECTIVE-CANARY-SUCCESS-2026-08-07.md`. Sentinel: `QWEN14B_CANARY_SUCCESS_DOCUMENTED_FULL9_READY`.

---

## Prior phase (2026-08-06) — Multi-GPU VRAM Preflight Closure

# Qwen 14B Multi-GPU VRAM Preflight Closure — Latest Phase Report

## Executive decision

The independent audit (`QWEN14B_MULTI_GPU_VRAM_PREFLIGHT_INDEPENDENT_AUDIT_2026-08-06.md`) accepted that the `897e323` state was full-suite green but rejected one preflight invariant: **VRAM headroom was measured and enforced on GPU 0 only**. The defect is **closed** on branch `fix/kaggle-smoke-v2-model-output-closure` (Commit A `f7b1ebb` + Commit B `c8f5685`, pushed, local = remote, tree clean). Official clean-env gate (`_workspace\cache\prebenchmark-py311-v4-loader`, Python 3.11.5 / pytest 8.4.2 exactly): full suite **1,915 passed / 32 skipped / 0 failed**, zero new static findings, and all five regression proofs pass. **Next authorized action after independent audit = Kaggle engineering preflight cell only.** No real 14B result and no stable release claimed.

## Why this closure existed

The old `_qwen_probe_metrics` in `src/benchmark/execution/preflight.py` read VRAM from GPU 0 only:

```text
torch.cuda.synchronize(0)
torch.cuda.memory_allocated(0)
torch.cuda.memory_reserved(0)
torch.cuda.mem_get_info(0)
```

`free_vram_after_probe_gib` was that single device-0 value and `vram_headroom`
compared only it against `MIN_FREE_VRAM_GIB = 2.0`. On a 2x Tesla T4 Kaggle
runtime with `device_map="auto"`, the 14B bnb-nf4 model is distributed across
both GPUs, so GPU 1 with under 2.0 GiB free was invisible to the gate.

Exact reproduction (mandatory adversarial case from the audit):

```text
GPU0 free = 3.0 GiB   (>= 2.0)   -> old gate PASSED (read GPU 0 only)
GPU1 free = 0.125 GiB (< 2.0)    -> corrected gate FAILS (GPU 1 free=0.12 GiB < 2.0 GiB)
```

## What changed

- **Per-GPU snapshot type:** `GpuVramSnapshot` (frozen) — `device_index`,
  `gpu_name`, `allocated_gib`, `reserved_gib`, `free_gib`, `total_gib`.
- **`_collect_gpu_vram_snapshots()`:** iterates `range(torch.cuda.device_count())`,
  synchronizes every device, reads `memory_allocated(i)` / `memory_reserved(i)` /
  `mem_get_info(i)` per GPU; three-decimal GiB rounding; returns `()` when CUDA
  unavailable; a failure on any one GPU is raised, never swallowed; no tensors
  allocated.
- **Probe metrics semantics:** called once after the probe; `gpu_vram_by_device`
  persisted; `free_vram_after_probe_gib = min(snapshot.free_gib)`;
  `allocated_vram_gib`/`reserved_vram_gib` = sums (three decimals);
  `gpu_name` = device 0 name; `gpu_count` = visible GPU count; FAIL when
  `gpu_count > 0` but no snapshots exist.
- **Minimum-free gate:** every visible GPU must have `free_gib >= 2.0`;
  `vram_headroom: PASS (minimum free across 2 GPU(s)=X.XX GiB)`; failures list
  every failing device deterministically by index; free memory never
  averaged/summed for the gate.
- **Failure-path evidence:** `_static_model_metadata` includes
  `gpu_vram_by_device`, so a failed load/probe still preserves the real per-GPU
  count, names, and memory; probe tokens/footprint may stay zero; the preflight
  still fails. No forced CUDA imports when dependency verification fails first.
- **Result + JSON schema:** `KaggleSmokePreflightResult.gpu_vram_by_device:
  tuple[GpuVramSnapshot, ...] = ()`; ordered per-GPU objects persisted in
  `kaggle_smoke_preflight.v1` JSON; one concise human line per GPU; no existing
  JSON field removed or renamed.

## Gate totals (official clean env `_workspace\cache\prebenchmark-py311-v4-loader`, Python 3.11.5 / pytest 8.4.2)

```text
Complete Integration    PASS   1,915 passed / 32 skipped / 0 failed (500.22 s; +17 net new tests)
Metric Verification     PASS   169 passed / 0 failed (test_r4_token_and_metrics + test_r4_metric_contract + test_statistics + test_reporting)
Ruff                    PASS   0 new findings (86 pre-existing baseline in untouched files; changed files clean)
strict mypy             PASS   Success in 77 source files (0 issues)
compileall              PASS   clean (src, tests, scripts, seven_arm_benchmark.py)
Notebook compilation    PASS   canonical + bundled code cells compile; source-commit identity test PASS (SOURCE_COMMIT=f7b1ebb)
Bundle integration      PASS   32 passed (test_kaggle_bundle_smoke_v2_preflight.py against the repinned bundle)
builder/manifests       PASS   147 files / 968,722 bytes; two consecutive builder runs content-identical; manifests verified; no cache files
Regression proof 1      PASS   1 GPU with >= 2 GiB free -> vram_headroom PASS
Regression proof 2      PASS   2 GPUs both >= 2 GiB free -> PASS (minimum free across 2 GPU(s))
Regression proof 3      PASS   asymmetric GPU0 3.0 GiB / GPU1 0.125 GiB -> FAIL (the audit case)
Regression proof 4      PASS   both GPUs low -> FAIL listing every failing device by index (0 then 1)
Regression proof 5      PASS   failed model load preserves per-GPU snapshots via _static_model_metadata
```

## Commit hashes and remote equality

```text
commit A = f7b1ebba73b52868a95c47ef3806d3b09da16d93  fix(model): enforce multi-GPU VRAM headroom per visible GPU
commit B = c8f56853437eb14211f6afcde6c621ade8cd0abd  chore(deploy): repin multi-GPU VRAM preflight bundle
local HEAD = remote HEAD = c8f5685 (pushed; working tree clean)
```

The directive requested exact commit messages `fix(preflight): enforce per-GPU VRAM headroom` and `chore(deploy): repin multi-GPU Qwen preflight bundle`; the execution used the established `fix(model)` / `chore(deploy)` convention instead. Because the directive prohibits amend/rebase/force-push, history was not rewritten; the deviation is recorded truthfully in the closure record and does not alter shipped code, bundle, pins, or gate results.

Record: `selective_updates/records/QWEN14B-MULTI-GPU-VRAM-PREFLIGHT-CLOSURE.md`.
Sentinel: `QWEN14B_MULTI_GPU_VRAM_CLOSURE_AUDIT_REQUIRED`.

---

# Qwen 14B NF4 v4 Loader Official Gate — Latest Phase Report

## Executive decision

The missing official clean-environment gate for the Qwen 14B NF4 transformers
v4 loader closure is **complete** on branch `fix/kaggle-smoke-v2-model-output-closure`,
and one stale Notebook markdown statement was corrected (docs/deploy only — no
runtime code, tests, requirements, data, prompts, scenarios, strategies,
evaluator logic, metrics, model settings, or runtime limits changed). The
official gate ran in a fresh disposable env created from project declarations
only (Python 3.11.5 / pytest 8.4.2 exactly): full suite **1,898 passed / 32
skipped / 0 failed**, all Pre-Benchmark categories pass, zero new static
findings, and the bundle rebuilt content-identical. **Next authorized action
after independent audit = Kaggle engineering preflight cell only.** No real 14B
result and no stable release claimed.

## The authorized change — Notebook markdown truth

The markdown cell immediately before `preflight-cell` in
`notebooks/seven_arm_benchmark.ipynb` described the load as **int8**
(`load_in_8bit=True` + `device_map="auto"` with `expandable_segments`). This was
stale — the deployed loader is the Qwen 14B BNB-NF4 profile. The cell now reads:

```text
3. **Qwen 14B BNB-NF4 load** — `Qwen2.5-Coder-14B-Instruct` base checkpoint via
   BitsAndBytes NF4: `load_in_4bit=True`, `bnb_4bit_quant_type="nf4"`,
   `bnb_4bit_compute_dtype=float16`, `bnb_4bit_use_double_quant=True`,
   `device_map="auto"`, Transformers 4.57.6
```

No executable code cell, `SOURCE_COMMIT`/`DEPLOYED_BUILD_ID` (`41e9ad7`),
command, quantization setting, model path, timeout, token limit, or
authorization flag was altered. The bundle was regenerated twice with
`scripts/build_upload_bundle.py`; the second run was byte-identical to the
first (content-identical), and the bundled notebook now carries the corrected
markdown with its `notebook_manifest.json` SHA-256 updated.

## Official gate totals (fresh disposable env `_workspace\cache\prebenchmark-py311-v4-loader`, Python 3.11.5 / pytest 8.4.2 exactly)

```text
Environment              PASS   pip install -e ".[dev]" pytest==8.4.2 ruff==0.15.22 mypy==1.20.2
                                Python 3.11.5 / pytest 8.4.2 / Django 5.2.16 / DRF 3.17.1 /
                                pytest-django 4.12.0 / pytest-asyncio 1.2.0
Dataset Validation      PASS   281 passed / 4 skipped (scenarios + repositories + models + config +
                                registry + enums + integration test set)
Prompt Validation       PASS   126 passed / 4 skipped (strategies + output_normalization + llm_factory +
                                llm_mock + llm_dry_run + llm_openrouter)
Pipeline Smoke Test     PASS   177 passed / 0 failed (preflight + kaggle_bundle_smoke_v2_preflight +
                                real_smoke + scientific_smoke_v1/v2 + subprocess_pythonpath +
                                llm_kaggle_qwen_backend in the established safe order)
Scripted 9-record Dry   PASS   9 planned / 9 terminal / 9 succeeded / 0 failed / exit 0
                                (--profile scientific-smoke-v2, fresh disposable output dir)
Complete Integration    PASS   1,898 passed / 32 skipped / 0 failed (517.97 s; exit 0) — the official full suite
Metric Verification     PASS   169 passed / 0 failed (test_r4_token_and_metrics + test_r4_metric_contract +
                                test_statistics + test_reporting)
Ruff                    PASS   0 new findings (91 pre-existing baseline in untouched files; changed files clean)
strict mypy             PASS   Success in 77 source files (0 issues)
compileall              PASS   clean (exit 0)
Notebook compilation    PASS   canonical + bundled code cells compile
                                (test_all_deployed_notebook_code_cells_compile, 2 passed)
Builder/manifests       PASS   147 files / 965,015 bytes; two consecutive builder runs content-identical
                                (tree hash 26EA934F16A25C14788484CE1A75EFF4FB453E6C346F5FDCEE72D3004EC5B7D1);
                                manifests verified; no cache files
git diff --check        PASS   clean; working tree clean
```

## Commit hashes and remote equality

```text
loader commit A = 41e9ad70c86ac696ce6ceaacd6b6892889bcc48a  fix(model): pin transformers==4.57.6 BNB loader and preserve static preflight metadata
loader commit B = 920ab9b75ff86ae41722fc8ec0e6f381282f54b5  chore(deploy): repin Qwen 14B NF4 v4 loader closure bundle
this commit     = docs(deploy): finalize Qwen 14B NF4 loader gate truth (pushed)
local HEAD = remote HEAD (pushed; working tree clean)
```

Record: `selective_updates/records/QWEN14B-NF4-TRANSFORMERS-V4-LOADER-CLOSURE.md`.
Sentinel: `QWEN14B_V4_LOADER_OFFICIAL_GATE_AUDIT_REQUIRED`.

---

# Qwen 14B NF4 Transformers v4 Loader Closure — Latest Phase Report

## Executive decision

The independent OOM audit reproduced the real preflight OOM on the `9fd4eee`
state (full suite was green, but the real Qwen 14B load OOM'd on Kaggle). The
root cause is **closed** on branch `fix/kaggle-smoke-v2-model-output-closure`
(Commit A `41e9ad7` + Commit B `920ab9b`, pushed, local = remote, tree clean).
Gate = ambient Python 3.11.5 / pytest 9.1.1: full suite **1,898 passed / 32
skipped / 0 failed**, zero new static findings, and all three explicit
regression proofs pass. **Next authorized action after independent audit =
Kaggle engineering preflight cell only.** No real 14B result and no stable
release claimed.

## Why this closure existed

The independent audit accepted that `9fd4eee` was full-suite green but rejected
it for real preflight after reproducing the OOM at runtime. Root cause:
transformers was **unpinned** in the Kaggle runtime lock, the Kaggle image
drifted to **transformers 5.0.0**, and the 5.0.x loader **materialized the 14B
BF16 weights on GPU before BNB-NF4 quantization**.

```text
Runtime evidence (Kaggle):  Python 3.12.13 / transformers 5.0.0 /
                            bitsandbytes 0.49.2 / accelerate 1.14.0 / torch 2.10.0+cu128
OOM signature:              OOM after 232.412 s at ~75% of 579 checkpoint params
                            (tried 136 MiB; GPU 1 free 46.81 MiB / allocated 14.38 GiB)
```

With transformers 4.57.x, `from_pretrained(...) + BitsAndBytesConfig` streams
and quantizes in place; with 5.0.x the full-precision temporary copy caused the
OOM. The closure makes the 4.57.x loader mandatory and fail-closed.

## What changed

- **Lock pin:** `requirements-smoke-kaggle.lock` now requires
  `transformers==4.57.6` (with a transformers-add/version-pin header comment;
  transformers removed from the "intentionally omitted" list). **torch stays
  unpinned** — Kaggle provides its GPU torch build and no torch pin was added.
  `requirements-kaggle.txt` updates `transformers>=4.30` → `transformers==4.57.6`.
- **Fail-closed preflight:** `_REQUIRED_IMPORTS` requires the exact `"4.57.6"`;
  `dependency_import_verification` FAILs with `transformers=5.0.0 (expected
  4.57.6)` and with `NOT_INSTALLED` before staging/model load.
- **Notebook install-lock-cell:** `EXPECTED_RUNTIME` gains
  `"transformers": ("transformers", "transformers", "4.57.6")` (fail-closed
  mismatch check). Setup-cell repinned to `SOURCE_COMMIT =
  41e9ad70c86ac696ce6ceaacd6b6892889bcc48a` / `DEPLOYED_BUILD_ID = 41e9ad7`.
- **BNB loader:** `kaggle_qwen_backend._load_model` passes
  `low_cpu_mem_usage=True` for the `bnb-int8` and `bnb-nf4` branches (fp16
  unchanged), so 4.57.x streams/quantizes in place.
- **Static preflight metadata:** `_static_model_metadata(model_path,
  quantization_mode)` reads `config.json` + CUDA discovery (no weight load) and
  fills `model_identity` / `checkpoint_basename` /
  `checkpoint_quantization_method` / `gpu_count` / `gpu_name`; the probe-failure
  path preserves this metadata even when the load OOMs/fails.

## Gate totals (ambient Python 3.11.5 / pytest 9.1.1 — full suite; declared clean env `_workspace\cache\prebenchmark-py311` must be recreated by the independent audit for the official gate)

```text
Complete Integration    PASS   1,898 passed / 32 skipped / 0 failed (539.32 s; 8 new tests in this closure)
Ruff                    PASS   0 new findings (86 pre-existing baseline in untouched files; changed files clean)
strict mypy             PASS   Success in 77 source files (0 issues)
compileall              PASS   clean (changed Python files)
Notebook compilation    PASS   canonical + bundled code cells compile; pin identity SOURCE_COMMIT=41e9ad7
Bundle integration      PASS   32 passed (lock now requires transformers==4.57.6; no torch pin)
builder/manifests       PASS   147 files / 964,859 bytes; rerun content-identical; manifests verified
Regression proof 1      PASS   preflight FAILs on transformers 5.0.0 / NOT_INSTALLED before load
Regression proof 2      PASS   BNB int8 + NF4 loads pass low_cpu_mem_usage=True (fp16 does not)
Regression proof 3      PASS   static model/GPU metadata preserved when the probe fails
```

The ambient pytest 9.1.1 result is diagnostic only for the full-suite gate; the
declared clean environment must be recreated for the official independent gate.

## Commit hashes and remote equality

```text
commit A = 41e9ad70c86ac696ce6ceaacd6b6892889bcc48a  fix(model): pin transformers==4.57.6 BNB loader and preserve static preflight metadata
commit B = 920ab9b75ff86ae41722fc8ec0e6f381282f54b5  chore(deploy): repin Qwen 14B NF4 v4 loader closure bundle
local HEAD = remote HEAD = 920ab9b (pushed; working tree clean)
```

Record: `selective_updates/records/QWEN14B-NF4-TRANSFORMERS-V4-LOADER-CLOSURE.md`.
Sentinel: `QWEN14B_V4_LOADER_CLOSURE_AUDIT_REQUIRED`.

---

# Qwen 14B Final Preflight Closure — Latest Phase Report

## Executive decision

The three Qwen 14B preflight blockers independently reproduced on the
`5ef6438` state are **closed** on branch `fix/kaggle-smoke-v2-model-output-closure`
(Commit A `0aa705d` + Commit B `cc7846b`, pushed, local = remote, tree clean).
The official gate ran in the declared clean environment (Python 3.11.9 /
pytest 8.4.2): full suite **1,890 passed / 32 skipped / 0 failed**, zero new
static findings, and both explicit regression proofs pass. **Next authorized
action after independent audit = Kaggle engineering preflight cell only.** No
real 14B result and no stable release claimed.

## Why this closure existed

The independent audit accepted that `5ef6438` was full-suite green but rejected
it for real preflight after reproducing three defects:

1. **Canary used `SELECTIVE_CANARY_OUTPUT_DIR` before assignment** — the
   definition sat inside the `selective-calibration-canary` cell while
   `CANARY_PREFLIGHT_DIR = SELECTIVE_CANARY_OUTPUT_DIR / "preflight"` was
   computed earlier, so the canary cell raised `NameError` at run time.
2. **Preflight incorrectly required exactly one visible GPU** — real 2×Tesla T4
   Kaggle environments were rejected.
3. **Numeric version dir produced a `qwen:1:*` readable identity** — e.g.
   `/kaggle/input/models/qwen-lm/qwen2.5-coder/transformers/14b-instruct/1`
   produced `qwen:1:...` because `path.name` was `"1"`.

## What changed

- **Fix A (notebook):** `SELECTIVE_CANARY_OUTPUT_DIR` definition moved to the
  `setup-cell` (immediately after `OUTPUT_DIR`); duplicate assignment removed
  from the canary cell. Order: setup defines → ... → canary cell uses.
- **Fix B (preflight):** `EXPECTED_VISIBLE_GPU_COUNTS = (1, 2)`; `1` or `2`
  visible GPUs pass, else `FAIL (N; expected 1 or 2)`.
- **Fix C (identity):** `_checkpoint_identity_slug` maps a numeric final dir to
  `<parent>-v<version>` (e.g. `14b-instruct/1` → `14b-instruct-v1`,
  `7b-instruct/1` → `7b-instruct-v1`), lowercased/sanitized to `[a-z0-9._-]`,
  used by `compute_model_identity` and `checkpoint_basename`. Real identities
  read `qwen:14b-instruct-v1:bnb-nf4:cfg-<12hex>` — never `qwen:1:*`.

## Gate totals (declared clean environment — Python 3.11.9 / pytest 8.4.2)

```text
Dataset Validation      PASS   285 passed / 5 skipped
Prompt Validation       PASS   174 passed / 0 failed
Pipeline Smoke Test     PASS   223 passed / 12 skipped / 0 failed
Scripted 9-record Dry   PASS   9 planned / 9 terminal / 9 succeeded / 0 failed / exit 0; dashboard + evidence files present
Complete Integration    PASS   1,890 passed / 32 skipped / 0 failed (the only official full-suite gate; 584.37 s)
Metric Verification     PASS   169 passed / 0 failed
Ruff                    PASS   0 new findings (91 pre-existing baseline in untouched files; changed files clean)
strict mypy             PASS   Success in 77 source files (0 issues)
compileall              PASS   clean
Notebook compilation    PASS   canonical 8/8 + bundled 8/8 code cells compile
builder/manifests       PASS   147 files / 963,067 bytes; rerun content-identical; manifests verified; no cache files
Regression proof 1      PASS   2-GPU otherwise-valid preflight = PASS
Regression proof 2      PASS   canary setup reaches subprocess construction without NameError
```

The ambient pytest 9.1.1 result is diagnostic only and never the official gate.

## Commit hashes and remote equality

```text
commit A = 0aa705d1c071827421461922c24f59f45fced029  fix(model): close Qwen 14B Kaggle preflight blockers
commit B = cc7846b152a83ae8ea6cfb6b6d56ae1c0f8733a6  chore(deploy): repin final Qwen 14B preflight bundle
local HEAD = remote HEAD = cc7846b (pushed; working tree clean)
```

Record: `selective_updates/records/QWEN14B-FINAL-PREFLIGHT-CLOSURE.md`.
Sentinel: `QWEN14B_FINAL_PREFLIGHT_CLOSURE_AUDIT_REQUIRED`.

---

# Qwen 14B BNB-NF4 Canary Preparation — Latest Phase Report

## Executive decision

The Qwen 14B BNB-NF4 canary preparation closure is **complete** on branch
`fix/kaggle-smoke-v2-model-output-closure` (Commit A `0ece665` + Commit B
`0a596b8`, pushed, local = remote, tree clean). The frozen model-blind
`qwen:1:int8` identity has been replaced with a deterministic model-aware
identity, an explicit `bnb-nf4` profile exists, prequantized-checkpoint
conflicts fail fast before model load, and the notebook is pinned to the
official unquantized 14B base checkpoint with a fail-closed canary preflight
gate. **Next authorized action = Kaggle engineering preflight only.**

## Why this closure existed

- The generic auto-resume cell downloaded `exp-20260804-133016` because both
  the 7B and an attempted 14B run were labeled `qwen:1:int8` — identity
  contamination, not a 14B result.
- An attempted 14B GPTQ checkpoint run (`exp-20260804-195126`) produced
  0 records / 0 calls / 0 tokens: the preflight failed before the model probe
  because a `GPTQConfig` checkpoint cannot be loaded by the `BitsAndBytesConfig`
  loader. Preserved as engineering evidence; GPTQ support is deferred.

## What changed

- **Identity:** `qwen:<checkpoint-basename>:<quantization>:cfg-<12hex>`, computed
  before auto-resume from `config.json` fields (model_type, hidden_size,
  num_hidden_layers, num_attention_heads) + requested mode + checkpoint
  quantization method. 7B bnb-int8 / 14B bnb-int8 / 14B bnb-nf4 always differ;
  historical `qwen:1:int8` records preserved.
- **Profiles:** canonical modes `bnb-int8` / `bnb-nf4` / `fp16` via
  `--qwen-quantization` (default `bnb-int8`, unknown values exit 2). NF4 =
  `load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=
  torch.float16, bnb_4bit_use_double_quant=True` (Tesla T4).
- **Fail-fast:** a prequantized non-bitsandbytes checkpoint raises
  `PREQUANTIZED_CHECKPOINT_INCOMPATIBLE` before tokenizer/model load; no
  automatic fallback.
- **Notebook:** pinned to the unquantized `14b-instruct/1` base checkpoint
  (never `14b-instruct-gptq-int4`), `QWEN_QUANTIZATION = "bnb-nf4"`,
  `RUN_GENERIC_ONE_RUN = False`, isolated
  `/kaggle/working/runs/qwen14b_bnb_nf4_selective_canary`, a fail-closed
  canary preflight assertion, `--strategy selective --max-runs 1
  --new-experiment`, no `--auto-resume-hf`. Notebook identity
  `SOURCE_COMMIT = 0ece665ef25e1b0ca3aa14f5f25977cadbd06d0c` /
  `DEPLOYED_BUILD_ID = 0ece665`.

## Gate totals

```text
Dataset Validation      PASS   27 scenario files / 27 unique IDs / 0 duplicates / 3 smoke IDs; zero dataset changes in closure
Prompt Validation       PASS   380 passed / 10 skipped / 0 failed
Pipeline Smoke Test     PASS   189 passed / 12 skipped / 0 failed
Scripted 9-record Dry   PASS   9/9 succeeded / 0 failed / exit 0 (scientific-smoke-v2, fresh dir)
Complete Integration    PASS   1,877 passed / 32 skipped / 0 failed (full tests suite, 631.20 s)
Metric Verification     PASS   169 passed / 0 failed
Ruff                    PASS   0 new findings (21 pre-existing)
strict mypy             PASS   0 new findings (5 pre-existing, identical rule set to self-contained HEAD baseline)
compileall              PASS   8 changed Python files compile
Notebook compilation    PASS   canonical 8/8 + bundled 8/8 code cells compile
builder/manifests       PASS   147 files / 962,188 bytes; rerun content-identical; manifests verified; no cache files
```

## Commit hashes and remote equality

```text
commit A = 0ece665ef25e1b0ca3aa14f5f25977cadbd06d0c  fix(model): add model-aware Qwen BNB quantization profiles
commit B = 0a596b83bd971aacad52806461c237a72784eaef  chore(deploy): pin Qwen 14B NF4 selective-canary bundle
local HEAD = remote HEAD = 0a596b8 (pushed; working tree clean)
```

Record: `selective_updates/records/QWEN14B-BNB-NF4-CANARY-READINESS.md`.
Sentinel: `QWEN14B_NF4_CANARY_READINESS_AUDIT_REQUIRED`.

---

# Selective Calibration Canary Result — Latest Phase Report

## Executive decision

The dedicated selective calibration canary was executed on Kaggle under the
pinned bundle and its result has been ingested documentation- and ledger-only
on branch `fix/kaggle-smoke-v2-model-output-closure` (pushed, local = remote,
tree clean). **Result: the harness safety controls worked; Qwen code quality
did not improve; no successful implementation exists.**

- **Canary `exp-20260804-133523`** (`todo-smoke-001 / selective`, source/build
  `50ec2c1`): **failed / `model_output`**, 4 model calls / 5,804 tokens /
  257.596 seconds, 3 selected / 2 preserved / **0 written**. Initial generation
  = 3 calls / 3,372 tokens; repair = 1 call / 2,432 tokens. HF state =
  `recovery_uploaded`; checkpoint = 1 completed / 2 pending.
- **Qwen output defects:** `todo/models.py` used `max_length=5` for a `MEDIUM`
  value of length 6; `todo/serializers.py` and `todo/views.py` each duplicated
  `Priority(models.TextChoices)`. The first repair of `models.py` was
  byte-identical to the initial response → `repair_no_progress` stopped the
  round; the atomic application wrote zero files (workspace stayed at baseline).
- **Harness vs model:** versus the previous selective run on the same scenario,
  the canary used 41.6% fewer tokens, 33.3% fewer calls, and was 22.4% faster,
  but the initial generation tokens (3,372) and the three output SHA-256 hashes
  were **identical**. The improvement came entirely from the harness controls
  (per-call deadline, no-progress detection, atomic writes, fail-closed
  continuation gate); the model produced the same bad code.
- **Incidental monolithic run `exp-20260804-133016`** (todo-smoke-001 /
  monolithic, 6 calls / 7,927 tokens / 300.165 s / `scientific_budget_exhausted`
  / 0 written): the generic one-run cell ran before the canary and is retained as
  diagnostic calibration evidence only — NOT the authorized canary and NOT an
  accepted comparison.
- **Continuous cell:** executed after the canary and correctly stopped
  fail-closed with `CALIBRATION_REVIEW_REQUIRED`; no additional scientific model
  calls, no remaining runs launched.
- **Current scientific truth:** accepted current dedicated canary records = 1,
  successful = 0; the full current 9-record experiment is **not run**; no
  merge/tag/Pilot/Kaggle authorized; **no stable release claimed**.

Record: `selective_updates/records/SELECTIVE-CANARY-RESULTS-2026-08-04.md`.
Next action: independent result audit (`SELECTIVE_CANARY_RESULT_AUDIT_REQUIRED`),
then a deliberate decision between repeating the dedicated selective canary and
proceeding to the full 9-record run.

SELECTIVE_CANARY_RESULTS_DOCUMENTED

---

# Final Selective Canary Readiness Closure — Latest Phase Report

## Executive decision

The final selective canary readiness closure is **complete** on branch
`fix/kaggle-smoke-v2-model-output-closure` (HEAD `356722b`, pushed, local =
remote, tree clean). The independent GPT-5.6 Thinking audit at `f727b3e`
**REJECTED canary readiness** even though the full suite was green, based on
three independently reproduced blockers. All three are now closed, pinned, and
gated:

1. **Per-call cooperative deadline (Blocker 1).** The workflow deadline was
   checked only before the whole regeneration attempt; `SharedRegenerationExecutor`
   looped through every selected artifact without consulting the deadline.
   Direct reproduction: 1s timeout, 3 selected artifacts, budget advanced after
   call 1 → **3 model calls and false success**. Now every in-flight call
   returning beyond the deadline consumes/records its tokens, makes no next
   call, writes none of the staged attempt, and returns the failed scientific
   terminal `scientific_budget_exhausted` with truthful elapsed time and budget.
   The same guard applies to every internal Iterative Agent call, not only once
   before `analyze_impact()`. Direct adversarial proofs:
   `TestRunner.test_generation_deadline_stops_after_first_model_call` (1 call,
   failed terminal, count 0, 15 tokens),
   `TestRepairDeadline.test_repair_deadline_stops_after_first_repair_call`
   (2 calls, failed terminal, count 0, `repair_model_calls == 1`, repair tokens
   retained), `TestIterativeAgentDeadline.test_agent_selection_deadline_stops_after_first_call`
   (1 call, `model_call_budget_exhausted`, 50 tokens preserved).
2. **Atomic metric truth (Blocker 2).** Atomic validation prevented writes when
   any artifact was rejected, but `regenerated_artifact_count` still counted a
   staged artifact: direct reproduction = **0 writes but count 1**. Now every
   staged `generated` status becomes `aborted` or `rejected`,
   `regenerated_artifact_count = 0`, preserved response hashes/evidence remain
   available, and an all-valid attempt still commits every artifact exactly
   once. Metric/evidence truth, not a scientific formula change.
   `test_r4_token_and_metrics.py` assertions updated to the truthful staged
   statuses (`["aborted", "aborted", "rejected"]` / `["aborted", "rejected"]`);
   `MagicMock` exec_ret gains `model_call_budget_exhausted=False` in
   `test_r3d_wiring.py`.
3. **Dedicated selective canary cell (Blocker 3).** The generic one-run cell
   selects `todo-smoke-001 / monolithic` (execution-plan order is scenario
   first, then strategies), not `selective`. A dedicated, separately named
   Selective Calibration Canary cell (`selective-calibration-canary-cell`) was
   added: `--strategy selective --max-runs 1 --new-experiment --backend
   kaggle-qwen --profile scientific-smoke-v2 --max-attempts 3
   --max-completion-tokens-per-call 1024 --max-total-workflow-tokens 0 --timeout
   300 --hf-sync`, isolated output `runs/selective_calibration_canary`, **NO**
   `--auto-resume-hf`, `AUTHORIZE_CONTINUOUS_AFTER_CALIBRATION_REVIEW = False`.
   `_verify_selective_canary()` asserts exactly one current-source RunRecord
   `todo-smoke-001 / selective`, model identity `qwen:1:int8`, model calls > 0,
   terminal scientific success/failure outcome, HF `recovery_uploaded`,
   checkpoint `total_planned = 3 / completed = 1 / pending = 2`.

Commits: `50ec2c1` (Commit A: `fix(smoke): enforce per-call deadline and atomic
metric truth`), `28ecc5a` (Commit B: `chore(deploy): pin selective-canary-ready
Smoke V2 bundle`, `SOURCE_COMMIT = 50ec2c1ca43c230aed4538be32ca7dab2ccc22e5`,
`DEPLOYED_BUILD_ID = 50ec2c1`, bundle rebuilt 147 files / 948,250 bytes),
`356722b` (test alignment: `test(smoke): align affected unit tests with atomic
metric truth`).

Final gate: full suite = **1,856 passed / 32 skipped / 0 failed** (571.57s);
grouped per-category = 629 passed / 1 skipped (530.96s); scripted dry run
`--profile scientific-smoke-v2` into a fresh dir = **9/9 exit 0** (the default
`runs` dir held a stale checkpoint causing `ReportRebuildError: Unexpected Run
IDs`, not a code defect); mypy `--strict src` Success (77 files); ruff 0 new
findings (175 pre-existing repo-wide; 19 pre-existing E501 in
`test_r4_token_and_metrics.py`); compileall clean; notebook code cells compile
(8/8 bundle, incl. the canary cell); bundle content-identical (tree hash
`3b8d5b0ebf5e3ab8`); manifests verified (code 90 / data 56 / notebook 1); `git
diff --check` clean; working tree clean.

Calibration truth: `exp-20260803-002741` remains **preserved, 0/9 success, not
accepted scientific evidence** (9 terminal records / 0 succeeded / 8 failed / 1
timed_out / 81 model calls / 118,211 tokens). No Kaggle rerun has occurred. No
tag; no merge; Pilot not authorized; **no stable release claimed**. Next action:
after the independent re-audit, run the **dedicated selective calibration canary
cell only** (not the generic one-run cell, not the continuous cell, not a full
relaunch, not a fine-tune, not a tag/merge).

FINAL_SELECTIVE_CANARY_READINESS_AUDIT_REQUIRED

---

# Post-Smoke Calibration Closure — Latest Phase Report

## Executive decision

The post-smoke calibration closure is **complete and green** on branch
`fix/kaggle-smoke-v2-model-output-closure` (HEAD `231b0a5`, pushed, local =
remote, tree clean). The real calibration run `exp-20260803-002741` (9 terminal
records: 0 succeeded / 8 failed / 1 timed_out; 81 model calls; 118,211 total
tokens) exposed four proven control defects that were closed in three commits:
`27c1693` (runtime + tests: per-attempt atomic regeneration, repair no-progress
detection, fail-closed calibration continuation gate, cooperative deadline
semantics), `56772fe` (deployment pin: `SOURCE_COMMIT =
27c1693e22b1a68be0b299fb146d9ff1e500908b` / `DEPLOYED_BUILD_ID = 27c1693`,
bundle rebuilt, 147 files / 934,495 bytes), and `231b0a5` (test-fixture
reconciliation).

The first full gate after `56772fe` exposed **nine stale constant-output
integration fixtures** that accidentally activated the new no-progress
early-stop and lowered observed counts below the max-attempt expectations.
These failures were **not validly proven to be pre-existing**: the starting HEAD
`ec9ba0b` did not contain the `repair_no_progress` early-stop, and a detached
worktree using the main editable installation can import the current branch
instead of the detached worktree source — a cross-worktree comparison is valid
only with an isolated environment or an explicit worktree-local `PYTHONPATH`.
The reconciliation (`231b0a5`) changed tests only: `_FixedTokenBackend` gained
an opt-in `vary_output=True` (three duration tests), `_SentinelBackend` returns
a unique valid Python string per indexed response while preserving the exact
`TokenUsage`, and the five bounded-repair fixtures return distinct valid Python
per call. Every expectation was preserved unchanged (max_attempts, call counts
3/6, `repair_attempts`, `repair_model_calls` 2/4, durations 1.5/2.1, tokens
41/59/90, JSONL/reporting identity); the dedicated identical-output no-progress
tests remain unchanged; a new side-by-side boundary test proves constant output
→ 2 calls + `repair_no_progress` vs distinct outputs → 3 calls / 2 repair
attempts. These failures are documented as caused by the stale fixtures, never
as "pre-existing" production defects, and no runtime, prompt, metric, scenario,
evaluator, or dataset was changed.

Final gate: full suite = **1,849 passed / 32 skipped / 0 failed**; mypy
`--strict src/benchmark` Success (77 source files); ruff 93 findings =
identical 93-finding baseline set (0 new, verified by line-set export); compileall
clean; bundle build content-identical (147 files / 934,495 bytes; builder rerun
leaves the tree unchanged); all notebook code cells compile (canonical 7/7 +
generated 7/7); manifests verified (code 90 / data 56 / notebook 1); `git diff
--check` clean; working tree clean.

Calibration truth: `exp-20260803-002741` is **calibration evidence, not an
accepted scientific comparison** — latest real calibration = **0/9** (selective
9 artifacts vs monolithic 15 / agent 8; agent was the only arm to reach the
scenario evaluator, on `todo-smoke-002`). No Kaggle rerun has occurred. No tag;
Pilot not authorized. Next action after this independent audit: **one selective
calibration canary only** (not a full relaunch, not a fine-tune, not a
tag/merge). Fine-tuning is deferred to a separate future project on held-out
benchmark scenarios.

POST_SMOKE_CALIBRATION_CLOSURE_AUDIT_REQUIRED

---

# Pre-Benchmark Final Source Repin — Latest Phase Report

## Executive decision

The pre-benchmark reproducibility-and-truth closure is **complete and green** on
branch `fix/kaggle-smoke-v2-model-output-closure` (HEAD `f8d00d7`, pushed, local
= remote, tree clean). The pre-benchmark test environment is fully declared in
`pyproject.toml [dev]` + `requirements-dev.txt` (commits `769d84e` + `e5d9430`;
runtime `[project.dependencies]` and `requirements-smoke-kaggle.lock` untouched),
the clean environment was deleted and recreated from declarations only (Python
3.11.9, `_workspace\cache\prebenchmark-py311`), and the complete clean gate was
repeated.

The previous `76a6b16` gate had **1 failure, not a green full suite**:
**1,833 passed / 32 skipped / 1 failed**. The sole failure was
`test_notebook_source_commit_matches_deployed_runtime_tree`, structural because
the mandated `pyproject.toml` declaration change broke byte-identity with the
pinned `aac9914` SOURCE_COMMIT (frozen artifacts were not modified to force
green and the truthful total was recorded). **Root cause:** dependency
declarations changing `pyproject.toml` after the `aac9914`/`311e084` deployment
pin. **No runtime, prompt, metric, scenario, evaluator, or data change was
needed.**

The exact independently reviewed **deployment-only correction** `f8d00d7`
(imported via bundle fast-forward, exactly one commit) re-pins the deployment to
the current source snapshot `e5d9430`: bundled `kaggle_upload/code/pyproject.toml`
is now byte-identical to canonical, and both notebooks re-pin
`SOURCE_COMMIT = e5d943065c6f4158c30a1cbbba39436ab2a7a898` /
`DEPLOYED_BUILD_ID = e5d9430` (deployment source snapshot = `e5d9430`;
deployment correction = `f8d00d7`). The complete clean suite is now **green:
1,834 passed / 32 skipped / 0 failed** (the identity test passes). Dataset
Validation 285 passed / 5 skipped (data unchanged); Prompt Validation 158
passed; Pipeline Smoke 220 passed / 12 skipped; Dry Run 9/9 succeeded (exit 0);
Integration PASS; Metric Verification 169 passed; mypy strict Success (77
files); ruff 93 = 93 baseline (0 new); compileall clean; all notebook code cells
compile; bundle build content-identical (147 files / 928,329 bytes); manifests
verified; no cache files in `kaggle_upload`; git diff --check clean; tree clean.
Historical `exp-20260801-210443` produced one failed model-output terminal
record under source `6f88823` — preserved, excluded from the current `e5d9430`
aggregation; current accepted real records = **0/9**; no scientific evidence
exists; no tag; no Pilot; no Kaggle launch. Next: the only action after this
independent audit is the **Kaggle engineering preflight** cell (not the
scientific One-Run cell), after updating the Kaggle code dataset + notebook to
the corrected `e5d9430` deployment.

This report is the current, latest-first post-R6 report. The R6 acceptance,
freeze, and publication detail belongs to
`docs/R6_FINAL_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md` and
`selective_updates/records/R6-BUNDLE-PARITY-AND-PRE-KAGGLE-HANDOFF.md` and is
not repeated here. The prior R7C root-closure report is preserved as history
in `selective_updates/records/KAGGLE-SMOKE-V2-REAL-RUN-ROOT-CLOSURE.md`.

## Models used

```text
Requested model:  DeepSeek V4 Flash Free through OpenCode Zen
Actual model:     opencode/deepseek-v4-flash-free
Mode:             Build
Provider:         OpenCode Zen
```

## Branch and commits

```text
Branch             = fix/kaggle-smoke-v2-model-output-closure (from the deterministic-interpreter tail)
R6 accepted HEAD   = 949e9c2; R6 freeze commit 4b2dd27 (published milestone branch)
Runtime commit     = aac9914  fix(exec): bind Python scenario commands to active runtime
Deployment pin     = 311e084  chore(deploy): pin deterministic-interpreter Smoke V2 bundle
Declaration 1      = 769d84e  chore(test): declare complete pre-benchmark dependencies
Declaration 2      = e5d9430  chore(test): declare remaining pre-benchmark dependencies
Deployment correction = f8d00d7  chore(deploy): repin reproducible pre-benchmark source snapshot (HEAD)
Deployment source = e5d9430 (SOURCE_COMMIT=e5d943065c6f4158c30a1cbbba39436ab2a7a898, DEPLOYED_BUILD_ID=e5d9430)
Failed attempts    = exp-20260801-024041, exp-20260801-024624 (preserved; not deleted)
Latest real attempt = exp-20260801-123125 (FP16 → OOM; deps drifted; not scientific evidence)
Historical experiment = exp-20260801-210443 (ONE failed model-output terminal record under 6f88823;
                          preserved; excluded from current e5d9430 aggregation)
Record             = selective_updates/records/KAGGLE-SMOKE-V2-MODEL-OUTPUT-CLOSURE.md
```

## The failed attempts (truth)

```text
exp-20260801-024041  planned 9 / succeeded 0 / failed 9 / model calls 0 / tokens 0
exp-20260801-024624  planned 9 / succeeded 0 / failed 9 / model calls 0 / tokens 0
exp-20260801-123125  failed at runtime root (FP16 OOM; deps drifted from lock)
```

The first two attempts failed at the first arm/scenario triplet during
workspace **isolation** before any LLM call; the later attempt reached the
model (81 calls, 47,694 tokens) but every record failed selection/validation;
the root-closure attempt failed before any model call at runtime root. None of
these outputs are scientific evidence. They remain visible on the results
dataset and must not be deleted.

## Fix evidence

```text
Pre-benchmark categories (declarations-only recreated environment)  all passed
  Dataset Validation           285 passed / 5 skipped (data unchanged)
  Prompt Validation            158 passed
  Pipeline Smoke               220 passed / 12 skipped
  Dry Run                      scientific-smoke-v2 9/9 succeeded, exit 0
  Integration                  PASS
  Metric Verification          169 passed
Full suite (previous 76a6b16 gate)  1,833 passed / 32 skipped / 1 failed (NOT green)
  sole failure = test_notebook_source_commit_matches_deployed_runtime_tree
                 (structural: mandated pyproject.toml declaration change breaks
                  byte-identity with pinned aac9914 SOURCE_COMMIT; root cause =
                  dependency declarations changing pyproject.toml after the
                  aac9914/311e084 deployment pin; no runtime/prompt/metric/scenario/
                  evaluator/data change needed; frozen artifacts not modified to force
                  green — reported truthfully)
Full suite (after deployment-only correction f8d00d7)  1,834 passed / 32 skipped / 0 failed (GREEN)
  identity test now passes (working-tree pyproject.toml byte-matches pinned
  e5d9430 SOURCE_COMMIT)
Mypy strict src/benchmark      Success: no issues found in 77 source files
Ruff                          93 findings = 76a6b16 baseline (re-exported and re-run;
                              93 = 93) — 0 new findings
Compileall                    clean (exit 0)
Notebook cells                all compile (canonical 7/7 + generated 7/7)
git diff --check              clean
Benchmark data                unchanged
```

## Bundle inventory

```text
code = 90 files; data = 56 files; notebooks = 1; total = 147 files / 928,329 bytes
Builder = scripts/build_upload_bundle.py only; build verified and content-identical
         (manifests code 90 / data 56 / notebook 1; no cache files in kaggle_upload)
```

## Exact gates

```text
git diff --check    clean
Ruff                93 = 93 vs 76a6b16 baseline (0 new)
Mypy strict         Success: no issues found in 77 source files
Compileall          clean
notebook cells      all compile (7/7 canonical + 7/7 generated)
full suite          1,834 passed / 32 skipped / 0 failed (green)
identity test       test_notebook_source_commit_matches_deployed_runtime_tree PASSES
                    (deployment re-pinned to SOURCE_COMMIT=e5d9430 by f8d00d7)
bundle build        content-identical (147 files / 928,329 bytes); manifests verified
```

## Historical status snapshot (R7C era — SUPERSEDED; current truth = the CURRENT TRUTH blockquotes at the top of this file)

```text
R4 = accepted and frozen (f5ae826)
R5 = accepted and frozen (7761c48)
R6 = ACCEPTED AND FROZEN (949e9c2; freeze commit 4b2dd27; branch published)
Kaggle attempts = 2 (exp-20260801-024041, exp-20260801-024624) — failed pre-model, preserved
Latest real attempt = exp-20260801-123125 (FP16 → OOM; deps drifted) — not scientific evidence
Runtime fixes  = committed (de3163f) and pinned (fb60972) — core accepted by independent audit
R7A hardening  = complete (d50e89e + 4c73db6) — four audit findings closed
R7B Smoke Finish = complete (bff0a82 + 17207bf)
R7C root closure = complete (7a80e53 + f01b8f0) + correction imported (ffa179a + 6d6aa36)
                    + post-gate correction imported (6f88823 + 5797fc0, HEAD 5797fc0, pushed)
Full-gate truth = prior "1,451 full suite" was a SUBSET; true first full suite
                  23 failed / 1,759 passed / 32 skipped; after correction 1,790 passed / 32 skipped / 0 failed;
                  after post-gate correction 1,796 passed / 32 skipped / 0 failed
Deterministic interpreter closure = complete (aac9914 + 311e084) — bare interpreter tokens bound to active runtime
Pre-benchmark reproducibility closure = COMPLETE AND GREEN (769d84e + e5d9430 declarations;
                  deployment-only correction f8d00d7, HEAD f8d00d7, pushed) — previous 76a6b16 gate
                  1,833 passed / 32 skipped / 1 failed (structural notebook-pin identity test, truthful,
                  not forced green); f8d00d7 re-pins deployment to e5d9430; complete clean suite now
                  1,834 passed / 32 skipped / 0 failed; Dataset 285/5 (data unchanged), Prompt 158,
                  Pipeline Smoke 220/12, Dry Run 9/9, Integration PASS, Metric Verification 169;
                  mypy strict Success (77 files); ruff 93 = 93 baseline (0 new)
Historical experiment = exp-20260801-210443 produced ONE failed model-output terminal record under 6f88823 —
                  preserved, excluded from current e5d9430 aggregation
Current real records = 0/9
Local scripted Smoke = 9/9
Bundled CLI dry-run  = 9/9
Real Qwen Smoke      = 0/9
Scientific evidence  = NONE (no real-model success yet)
Tag                  = not created
Pilot                = not authorized
```

## Near goal

Independent audit complete and its exact deployment-only correction applied
(`f8d00d7`, pushed) → the only authorized Kaggle action is the engineering
preflight cell (not the scientific One-Run cell) → update the Kaggle code
dataset + notebook to the corrected `e5d9430` deployment → run the engineering
preflight → one real cell (require 1/9 succeeded) → remaining eight real Qwen
Scientific Smoke V2 records → independent result audit.

## Far goal

Independent real-result audit → main merge → stable `v0.8.0-smoke-v2-complete` tag (replaces the stale `v2.0.0-scientific-smoke` future-tag wording; milestone `v0.8.0-canary.1` already created/pushed, non-stable) → **EXECUTED (SMOKE-V2-CLOSE-01 closure merged `193d889`, stable tag created; MAIN-GREEN-01 merged `d875c72`, preferred recovery `v0.8.1-smoke-v2-complete`)** → freeze
Pilot matrix → Pilot execution → research experiment → statistical analysis →
paper evidence package.

## Next action

**Only Kaggle engineering preflight** after this independent audit (HEAD
`f8d00d7`): update the Kaggle code dataset + notebook to the corrected
`e5d9430` deployment, then run the preflight cell only. Do not relaunch Kaggle,
tag, merge, or force-push beyond that documented preflight step.

PRE_BENCHMARK_FINAL_SOURCE_REPIN_AUDIT_REQUIRED
