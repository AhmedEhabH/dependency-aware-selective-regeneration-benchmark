# System State

## Current Truth
- **PILOT-EXEC-01 SALEOR SOURCE-VISIBILITY FIX (2026-08-16): REAL KAGGLE v0.9.10 FAILURE + EXACT ROOT CAUSE + NARROW FIX ON `fix/pilot-saleor-source-visibility-probe` (code/test commit `ee3d88b`, pushed).** Real Kaggle v0.9.10 PASSED: release trust, transport restore, runtime lock install, repository snapshot verification, PostgreSQL provisioning + TCP proof, Redis fallback + reachability, uv tool env, django CMS no-pip env + deps + health probe, Saleor source copy, Saleor Python 3.12 `.venv` creation, and `uv sync --locked` (`uv sync --locked = PASS`). Then it failed ONLY at the new repository-env health probe: `START import saleor probe / END import saleor probe FAILED elapsed=0s exit=1 / ModuleNotFoundError: No module named 'saleor'`. ROOT CAUSE: the pinned Saleor `pyproject.toml` sets `[tool.uv] package = false` (upstream), so uv correctly installs the locked dependencies but deliberately does NOT install the root Saleor project into site-packages; the v0.9.10 probe ran `<saleor .venv>/bin/python -c "import saleor"` WITHOUT `cwd=the Saleor working copy`, while the frozen downstream preflight already runs Saleor commands with `cwd = pristine staged repository root`. Kaggle is NOT the root cause. FIX (minimal, source-faithful): `_import_probe` gained optional `cwd`; `_saleor_probe` always probes from `work_dir`; BOTH call sites fixed (marker/reuse `_needs_rebuild` probe and post-`uv sync --locked` probe). Explicit non-solutions honored: NO `package=true`, NO pip/uv editable install, NO global `PYTHONPATH`, `uv sync --locked` / Python 3.12 / `UV_PYTHON_DOWNLOADS=never` all preserved. Strong tests: real-subprocess source-visibility regression (import saleor FAILS from unrelated cwd, PASSES with `cwd=work`; `_saleor_probe(..., work_dir=work)` matches) — RED proven against old helper; `_FakeRunner` no longer blindly succeeds on `import saleor` (requires cwd exposing the package — the exact local-pass gap); pinned `[tool.uv] package=false` contract asserted on the bundled pyproject (no mutation); fresh provisioning (copy → uv venv → 3.12 → uv sync --locked cwd=work_dir → probe cwd=work_dir → marker only after probe PASS); reuse path (marker + probe PASS, no uv venv/sync); missing-source fail-closed negative; downstream preflight parity (cwd=staged repo root, provided Saleor `.venv/bin/python`); no semantic drift. Targeted integration green (provisioning 28, notebook contract 46, deployment bundle 61, real-launch preflight 14, service bootstrap 39); full suite **2,239 passed / 33 skipped / 0 failed** (2026-08-16). v0.9.10 remains immutable (real Kaggle preflight reached the Saleor post-sync health probe then failed because the probe did not run from the repository root). **v0.9.11-pilot-exec-ready release in progress** (code_manifest changes → release finalizer → FINAL ARTIFACT TRUST GATE → tag → exact 48-cell mock dry-run). Pilot = NOT STARTED.
- **PILOT-EXEC-01 v0.9.10 RELEASE TRUST GATE CLOSURE: **CLOSED AND FROZEN AT `v0.9.10-pilot-exec-ready`** (2026-08-15) — MERGED TO MAIN (`44e9a1f`) + TAGGED + TAGGED REBUILD + FINAL ARTIFACT TRUST GATE PASS + 48-CELL DRY-RUN 48/48.** The deployment source is re-frozen at `v0.9.10-pilot-exec-ready` via a REAL two-pass deterministic release-trust-gate finalizer run against the LOCAL repo cache (`dist/pilot-repo-cache`, NO `--allow-acquire`): `python scripts/finalize_pilot_notebook_trust.py --source-commit 80d4d6e581cef60463efde31b414643ba182f35a --source-tag v0.9.10-pilot-exec-ready --repo-cache dist/pilot-repo-cache --created-utc "2026-08-15T14:00:00+00:00"`. Both pinned repo cat-file checks PASS (django CMS `0f633fc9…`, Saleor `e11a5557…`) and `git archive` works in both cache dirs. **Notebook == Identity == Actual proven 4/4** for the four frozen manifest/map hashes: code `bb976f67fefe…` (validated; the v0.9.9 recorded `99688e4e` was stale — it predated the bundled helper-script additions and was never validated against the build), data `8b859ecc7216…`, repository snapshot `49d91d39435f…`, transport path map `07036a36cd97…` (last three byte-identical to v0.9.9); deployed notebook SHA-256 `d15d86831bf8…` == bundled archive bytes, normalized bundled notebook == source `873e97735cd2…`. **No scientific inputs changed** (scenarios, prompts, metrics, model, quantization, timeout 600, repair budget, repository pins, validation scope). Freeze evidence `reports/pilot_notebook_trust_freeze.json` (tracked). No-pip repo-env provisioning (v0.9.9), Redis-compatible per-candidate OS package fallback (v0.9.8), root-safe unprivileged PostgreSQL bootstrap (v0.9.7), `kaggle_transport` encoding + `transport-restore-cell` unchanged. Gates: targeted trust-gate closures 142/142 (deployment bundle 52/52, notebook contract 46/46, repo-env provisioning 24/24, real-launch preflight 13/13); full suite **2,234 passed / 33 skipped / 0 failed**; diff-check/ruff/mypy/compile clean. **Post-freeze execution (all COMPLETE):** independent audit PASS → non-ff merge to main `44e9a1f4314c2ce8ec0b7abb16c88cbc3f83bfb6` (merge SHA == main HEAD) → tagged rebuild (`--source-commit` = merge SHA, SAME `--created-utc "2026-08-15T14:00:00+00:00"`) → **FINAL ARTIFACT TRUST GATE PASS** (Notebook == Identity == Actual 4/4 on the tagged rebuild; deployed notebook == freeze; trust-gate regression + real artifact expanded simulation 19/19) → annotated tag `v0.9.10-pilot-exec-ready` created on the merge commit and pushed (peels to `44e9a1f…`) → exact 48-cell bundled dry-run on the tagged rebuild **48/48 terminal / 48 succeeded / 0 failed / 0 pending / 48 unique run IDs** (per-repo 16/16/16; per-strategy 24/24; per-rep 24/24; 0 model calls). Tagged-rebuild archive SHA-256 `9df1396d50a99da7b3dd101fefe79013c3c253da8fd65251dbd9eb4650e71436` (sidecar matches; identity source_commit == tag peel). **Pilot = NOT STARTED.**
- **PILOT-EXEC-01 KAGGLE REPO-ENV PROVISIONING CLOSURE: MERGED TO MAIN + TAGGED `v0.9.9-pilot-exec-ready` (2026-08-15).** Real Kaggle blocker closed: the v0.9.8 `pilot-repo-preflight-cell` ran `python -m venv` and the runtime lock installs pip into the benchmark interpreter, so on Kaggle `python -m venv /kaggle/working/pilot_envs/djangocms` -> `/kaggle/working/pilot_envs/djangocms/bin/python3 -m ensurepip --upgrade --default-pip` returned non-zero exit status 1 (cell failed in ~0.24 s, NOT a hang; real Kaggle Python installs the runtime lock into the base interpreter, which is why venv+ensurepip cannot create a working pip inside the env). New bundled helper `scripts/pilot_kaggle_repo_envs.py` provisions every repository validation env WITHOUT the failing ensurepip path: stdlib venv uses `--without-pip` everywhere; HOST pip (`<benchmark-python> -m pip --python <target>`) bootstraps the no-pip tool/target envs (documented pip 22.3+ feature for pip-less envs); dedicated no-pip `pilot_envs/tools` env gets `uv` via host pip `--python`; django CMS deps installed with `uv pip install -r test_requirements/django-5.0.txt` from the frozen snapshot root; Saleor = copy of pinned `DATA_DIR/repositories/saleor` into `pilot_envs/saleor`, then `uv venv .venv --python <existing 3.12>` with `UV_PYTHON_DOWNLOADS=never` (no silent download/switch) then `uv sync --locked`. Completion markers (`.pilot_env_ready.json`, schema `pilot_repo_environment.v1`) + health probes decide reuse; ONLY the specific invalid private env dir is rebuilt (never arbitrary `/kaggle/working`). Upstream OS prerequisites `gettext` + `gcc` + `libpq-dev` (ALL mandatory, NOT alternatives) install in ONE `apt-get install` transaction, failing closed listing ALL missing when apt is unavailable or they remain missing; the Redis `valkey-server`/`redis-server` alternatives bug is never reintroduced. Visible START/END/elapsed output with 30 s heartbeat threads on long installs; provisioning log (`preflight/environment_provisioning.log`) redacts `HF_TOKEN=`/`SECRET_KEY=`/`PGPASSWORD=` secrets. The notebook `pilot-repo-preflight-cell` is now a thin adapter: assert service ports 5433/6379 via `_assert_service_port`, load the bundled helper via `importlib.util`, call `provision_repository_envs(...)`, then pass the exact interpreter paths to the shared `scripts/pilot_repo_snapshot.py preflight` (todo = `sys.executable`). The helper rides in the Pilot code bundle (`code/scripts/pilot_kaggle_repo_envs.py`, byte-equal + hashed in `code_manifest.json`). No scientific inputs changed (scenarios, prompts, metrics, model, quantization, timeout, repair budget, repository pins, validation scope unchanged). New regression matrix `tests/integration/test_pilot_repo_env_provisioning.py` (24 tests: Gates B/C/D/E/G/J/K + end-to-end) all green; notebook + deployment bundle contracts updated. Full suite **2,225 passed / 33 skipped / 0 failed** (2026-08-15). `dist/pilot-kaggle-upload.zip` + `.sha256` will be rebuilt from the exact tagged source `v0.9.9-pilot-exec-ready` after merge. **Pilot = NOT STARTED.**
- **PILOT-EXEC-01 KAGGLE-REDIS-PACKAGE-FALLBACK: MERGED TO MAIN + TAGGED `v0.9.8-pilot-exec-ready`.** Final real Kaggle preflight blocker closed: the v0.9.7 cell ran the combined `apt-get install -y valkey-server redis-server`, which aborts the WHOLE apt transaction with `E: Unable to locate package valkey-server` because the real Kaggle Ubuntu (Jammy-shaped) runtime exposes `redis-server` in its configured apt repositories but NOT `valkey-server`. Branch `fix/pilot-kaggle-redis-package-fallback` (from clean origin/main) replaced the Redis provisioning in `service-bootstrap-cell`: resolve an already-installed Redis-compatible binary first; refresh apt metadata at most once per invocation (`_apt_update_once`); probe each alternative candidate individually via `apt-cache policy <name>` (`_apt_package_available`, argument-list only, no shell); install EXACTLY ONE package per `apt-get install` (`_apt_install_one`); record UNAVAILABLE and failed candidates; FAIL CLOSED with distro/runtime diagnostics when no candidate can be installed (no pip client-package, no in-process fake-server fallback). Selected-implementation label + proven server `--version` after start; endpoint stays `127.0.0.1:6379` / `redis://127.0.0.1:6379/0`. Root-safe unprivileged PostgreSQL bootstrap (v0.9.7) unchanged. No scientific inputs changed (scenarios, prompts, metrics, model, quantization, timeout, repair budget, repository pins, validation scope all unchanged; the four frozen manifest hashes remain byte-identical). Hermetic contract `tests/integration/test_pilot_service_bootstrap.py` grows a full-cell executor (`_exec_cell`) + 14 Redis package-fallback tests (41/41 total); notebook contract (+`test_redis_package_fallback_contract`) and deployment bundle contract updated to v0.9.8. Full suite **2,199 passed / 33 skipped / 0 failed** (2026-08-15). `dist/pilot-kaggle-upload.zip` + `.sha256` rebuilt from the exact tagged source `v0.9.8-pilot-exec-ready` (this closure). **Pilot = NOT STARTED.**
- **PILOT-EXEC-01 KAGGLE POSTGRES ROOT-FIX (HISTORICAL — superseded by the v0.9.8 Redis package-fallback correction): MERGED TO MAIN + TAGGED `v0.9.7-pilot-exec-ready`.** Real Kaggle blocker closed: the Kaggle notebook process runs as root while PostgreSQL `initdb`/`pg_ctl` refuse root (`initdb: error: cannot be run as root`), which blocked the v0.9.6 service bootstrap. Branch `fix/pilot-kaggle-postgres-unprivileged-bootstrap` (from clean origin/main) replaced the `service-bootstrap-cell` lifecycle: when the notebook effective uid is 0, the PostgreSQL server lifecycle (initdb, pg_ctl and the postgres server it launches) runs under the package-native unprivileged `postgres` OS account; the cell FAILS CLOSED before initdb if that account is missing and never falls back to root; non-root notebook processes keep the direct path. The frozen TCP client probe (psql) still runs from the notebook process against `127.0.0.1:5433 saleor/saleor/saleor`; Redis/Valkey `127.0.0.1:6379` unchanged; ownership/log preparation limited to the private service paths; no `shell=True`; no secrets printed. No scientific inputs changed (scenarios, prompts, metrics, model, quantization, timeout, repair budget, repository pins, validation scope all unchanged; the four frozen manifest hashes remain byte-identical). New hermetic contract `tests/integration/test_pilot_service_bootstrap.py` (28 tests, Gates B/C/D/E/F/H) execs the EXACT cell definitions with os/pwd/subprocess/socket fakes; notebook contract (+2 root-safe static tests) and deployment bundle contract updated to v0.9.7. Full suite **2,185 passed / 33 skipped / 0 failed** (2026-08-13). `dist/pilot-kaggle-upload.zip` + `.sha256` rebuilt from the exact tagged source `v0.9.7-pilot-exec-ready`. **Pilot = NOT STARTED.**
- **PILOT-EXEC-01 KAGGLE SERVICE BOOTSTRAP LAST-MILE CORRECTION: MERGED TO MAIN + TAGGED `v0.9.3-pilot-exec-ready`.** The frozen Pilot notebook now provisions the Saleor validation OS services on a fresh Kaggle session via a new fail-closed, idempotent `service-bootstrap-cell` (PostgreSQL `127.0.0.1:5433` role/db `saleor/saleor@saleor`; Valkey/Redis `127.0.0.1:6379` persistence-disabled) placed between repository snapshot verification and the repo-specific preflight — BEFORE any repository validation or model load. Service topology mirrors `benchmark_data/manifests/pilot_validation_commands.yaml`. No scientific inputs changed (scenarios, prompts, metrics, model, quantization, timeout, repair budget, repository pins, validation scope all unchanged). Notebook contract (+5 tests), deployment bundle contract, and targeted pilot gates green; full suite **2,098 passed / 33 skipped / 0 failed**. `dist/pilot-kaggle-upload.zip` + `.sha256` sidecar rebuilt from the exact tagged source `v0.9.3-pilot-exec-ready` (this closure) — the uploaded/manual re-zip is never the frozen archive. **Pilot = NOT STARTED.**
- **PILOT-EXEC-01 real-launch closure (HISTORICAL execution-ready point): `v0.9.2-pilot-exec-ready` @ `e030be5`.** Branch `fix/pilot-real-launch-closure` non-fast-forward merged to `main` at `e030be5`, pushed; annotated tag `v0.9.2-pilot-exec-ready` created at `e030be5` and pushed and NOT moved by this correction. Pre-correction bundle identity `source_commit=e030be5…`, `source_tag=v0.9.2-pilot-exec-ready`, archive SHA-256 `ecb7ea7c85d8bdc527a0384f141b47a1e84ee0b3c3f12b6b8305d880098015f1`; superseded as the launch source by the service-bootstrap correction (the tag itself stays immutable as the historical execution-ready point).
- Scientific Smoke V2: COMPLETE / ACCEPTED (unchanged)
- PILOT-READY-01: **CLOSED** (2026-08-10) after all gates green — multi-repo selective input contracts fixed, stale real-smoke expectation corrected, focused multi-repo production-path contract added, exact fresh 48-cell Pilot dry-run 48/48 deterministic, isolation/evidence/export gates 142 passed, full suite green
- Full suite: 2,234 passed / 33 skipped / 0 failed (2026-08-15, after the v0.9.10 release trust gate closure; 0 failed / 0 errors)
- Pilot: **NOT STARTED** (execution not authorized)
- Next exact task: `PILOT-EXEC-01` (Pilot freeze + execution)
- Frozen Pilot matrix: model Qwen2.5-Coder-14B-Instruct, quantization bnb-nf4, timeout 600s uniform, 12 scenarios, 2 strategies (iterative_repository_agent, selective), 2 repetitions = 48 cells; repositories Todo / django CMS / Saleor
- Stable tags: `v0.9.0-pilot-ready` @ `90a4282` (NOT moved); `v0.9.1-pilot-exec-ready` @ `7efdbe6` (superseded); `v0.9.2-pilot-exec-ready` @ `e030be5` (historical execution-ready point, NOT moved); `v0.9.3-pilot-exec-ready` (service-bootstrap correction, historical execution-ready point, NOT moved); `v0.9.6-pilot-exec-ready` (Kaggle auto-expanded mount correction, historical execution-ready point, NOT moved); `v0.9.7-pilot-exec-ready` (root-safe unprivileged PostgreSQL bootstrap, historical execution-ready point, NOT moved); `v0.9.8-pilot-exec-ready` (Redis-compatible OS package fallback, historical execution-ready point, NOT moved); `v0.9.9-pilot-exec-ready` (no-pip repository env provisioning closure, historical execution-ready point, @ `f211e4d`, NOT moved); `v0.9.10-pilot-exec-ready` = historical immutable release source @ main `44e9a1f` (release trust gate closure — Notebook == Identity == Actual validated 4/4; annotated tag ON the merge commit, pushed); `v0.9.11-pilot-exec-ready` = PENDING (Saleor source-visibility health-probe fix, 2026-08-16 — finalizer/trust-gate/tag/dry-run in progress)
- No further Smoke Full-9 authorized
- PILOT-EXEC-01 Gate 9 (2026-08-13): engineering preflight evidence ledger written — saleor `TZ=UTC` frozen (`pilot_validation_commands.yaml`); nondeterministic order/pricing cluster classified as upstream fixture artifact (33 vs 38 observed), not a regression; djangocms `test_filters_date` Windows-only artifact (passes on Linux/Kaggle)
- PILOT-EXEC-01 Gate 10 (2026-08-13): `dist/pilot-kaggle-upload/` + `dist/pilot-kaggle-upload.zip` rebuilt from the closure state with the real repo cache (djangocms/saleor at pinned SHAs, todo embedded); all proofs pass (notebook parity, non-empty verifiable `notebook_manifest.json`, 3 repos + SHA verification, frozen identity, manifest hash match, archive contents, deterministic rebuild byte-identical, fresh 48-cell bundled dry-run 48/48); archive SHA-256 `ecb7ea7c85d8bdc527a0384f141b47a1e84ee0b3c3f12b6b8305d880098015f1`
- PILOT-EXEC-01 Gate C: service-bootstrap corrections merged + tagged
  `v0.9.8-pilot-exec-ready` (Redis-compatible OS package fallback — the fix
  for the real Kaggle combined `apt-get install -y valkey-server redis-server`
  transaction abort, plus the prior root-safe unprivileged PostgreSQL
  bootstrap; `v0.9.6`/`v0.9.7`-pilot-exec-ready are historical execution-ready
  points); launch flow is the
  ONE-bundle Kaggle flow — one
  Dataset with `pilot-kaggle-upload.zip` + `.sha256`, extracted to
  `/kaggle/working/pilot_bundle`. The notebook now provisions PostgreSQL
  127.0.0.1:5433 and Valkey/Redis 127.0.0.1:6379 on a fresh Kaggle session
  before repository validation, running the PostgreSQL server lifecycle under
  the unprivileged `postgres` OS account when the notebook effective uid is 0
  (fail-closed, never root). Real Pilot is still awaiting the external
  Kaggle runtime preflight (SHA-256 verify, identity/manifest verify, service
  bootstrap, bundled 48-cell dry-run, model-load preflight) and the
  researcher-confirmed model path / HF results repo ID. Kaggle Internet must
  be ON (required for HF sync and any OS package install).

## Current Phase
**PILOT-READY-01 — PILOT READINESS CLOSURE (2026-08-10), STATUS `CLOSED` (BRANCH `feat/pilot-ready-01`, CODE/TEST COMMIT `34ecf78` `fix(pilot): close multi-repo selective input contracts` PUSHED, LOCAL = REMOTE).** Closed the selective arm's repository-level input-contract defects and proved Pilot readiness without starting Pilot. Root causes fixed: (A) `build_dependency_graph` silently reused one graph built from the first repository's snapshot for every run on mixed-repository plans — now fails closed on mixed repositories and `build_repository_dependency_graphs` builds one graph per repository (`_dep_graphs[repository_id]`), with the Pilot run loop selecting each repository's own graph; (B) editable-path expansion was applied once globally instead of per repository profile — `expand_editable_paths` is now applied per repository (excluded dirs, empty fail-close, duplicate/traversal/absolute/backslash rejection preserved); (C) artifact catalog normalization produced category-key descriptors for django CMS/Saleor instead of concrete file paths — `_normalize_artifact_catalog`/`descriptors_from_profile` now yield file-granular descriptors that are a strict subset of the editable universe; (D) stale real-smoke integration expectation — `STRATEGIES_WITH_MISSING_PREREQS` corrected to `{"agent"}` (selective is now fully provisioned; previously the test expected selective to be skipped with `success_count == 1`). New focused contract `tests/integration/test_pilot_multi_repo_production_path.py` (12 tests) proves per-repository graph identity (todo profile graph 5 nodes/6 edges; django CMS neutral_edgeless_fallback; Saleor architecture_fallback with `repo_id` metadata), concrete non-empty editable universes, non-empty descriptors ⊆ universe, deterministic `HybridSelectiveStrategy` impact analysis for all 12 frozen Pilot scenario deltas with zero cross-repository reuse, and zero exceptions. Validation: Gate 1 unit contract 14 passed; Gate 2 real-smoke 9 passed; Gate 3 production-path 12 passed (twice, 21 combined, no state leak); Gate 4 `git diff --check`/compile/ruff/mypy clean (feature-caused findings only fixed; 5 pre-existing mypy + 3 pre-existing ruff in untouched lines recorded as debt); Gate 5 exact fresh 48-cell Pilot dry-run (`runs/pilot_dryrun_48cell_20260810_012744`) = 48 planned / 48 terminal / 48 succeeded / 0 failed / 0 pending, 48 unique deterministic run IDs (config_hash `7ef6ffc7a2c0d369`, protocol 1.0, source_commit `34ecf78`), per-repo todo/djangocms/saleor 16/16/16, per-strategy 24/24, per-rep 24/24, checkpoint `completion_status: completed`, no residue; Gate 6 isolation/evidence/export gates = 142 passed; Gate 7 final full suite = **2,026 passed / 33 skipped / 0 failed**. Pilot matrix frozen (Qwen2.5-Coder-14B-Instruct / bnb-nf4 / 600s / 12 scenarios / 2 strategies / 2 repetitions / 48 cells). **Pilot = NOT STARTED; next = `PILOT-EXEC-01`; stable tag `v0.9.0-pilot-ready` after main merge.**
**MAIN-GREEN-01 — POST-MERGE TEST-ISOLATION AND REPRODUCIBILITY HOTFIX (2026-08-09), STATUS `FIXED AND CLOSED — FULL SUITE 1,958 PASSED / 33 SKIPPED / 0 FAILED / 0 ERRORS` (BRANCH `fix/main-green-test-isolation`, COMMIT A `34b9fc7` `fix(test): make Smoke-v2 integration state-independent` PUSHED).** After the SMOKE-V2-CLOSE-01 merge to main (`193d889`), the full suite regressed to 12 failed / 4 errors on the Windows working tree (`core.autocrlf=true`) — **NOT a scientific or merge regression** (merge-tree proof: `193d889^{tree}` == `65f9fb8^{tree}` == `fdd72f6…`; `git diff 65f9fb8..193d889` empty → merge drift ruled out). Root causes: **(A)** `kaggle_upload/code/tests/evaluator_assets/todo_smoke_*_checks.py` checked out CRLF → bundle SHA-256 fingerprints mismatched the recorded LF blob hashes (only the root `tests/evaluator_assets/` path was LF-pinned in `.gitattributes`); **(B)** `benchmark_data/repositories/todo/**` checked out CRLF → the scripted backend reads LF (universal newlines) while the executor writes verbatim LF (`regeneration.py` line 801 `write_text(..., newline="")`) → preserve-files (`todo/permissions.py`, `todo/urls.py`) rejected as `out_of_scope_change` → cells failed before migration generation → sequential isolation "expected exactly one new migration, got ()"; **(C)** `_baseline_hashes()` included `__pycache__/*.pyc` residue, regenerated bytecode differed → baseline compatibility false-negatives. Fix — **zero scientific drift** (only `.gitattributes` + test-support/test files changed; NO production `src/` code, prompts, datasets, strategies, metrics, model identity, or timeout changes): (1) `.gitattributes` pins `text eol=lf` for the bundle evaluator assets + `benchmark_data/repositories/todo/**` + `kaggle_upload/data/repositories/todo/**`, then LF renormalization (`git rm --cached -r` + `git checkout HEAD --`; verified zero CRLF remain; git status shows only `.gitattributes` modified → zero blob changes); (2) ephemeral baseline predicate (`__pycache__`, `.pytest_cache`, `.coverage`, `db.sqlite3`, `.git`, `.pyc`/`.pyo`) applied in `_copy_baseline` (copytree ignore) and `_baseline_hashes()`; (3) new unit tests T1/T2/T3. Repeatability gates: T4 representative monolithic cell twice PASS; T5 sequential isolation twice PASS (2×~160 s); T6 fingerprint contract PASS; T7 affected subset run twice each PASS (production-path 45, todo evaluator assets 53+1 skipped, kaggle bundle 51); T8 related regression 380 passed / 22 skipped; T9 full suite **1,958 passed / 33 skipped / 0 failed**. Static gates: compileall clean, ruff clean on changed files, `git diff --check` clean; mypy unchanged (no production files changed). Pre-benchmark validation: Dataset/Prompt/Metric PASS carried-forward (zero drift); Pipeline Smoke + Dry Run PASS (8/8, 0 failed, on a clean output dir; note: re-running the dry-run in the SAME output dir hits pre-existing stale-record validation in `rebuild_experiment_reports` — pre-existing, out of scope, documented); Integration Test PASS (production-path module 45 passed twice). **Next = `PILOT-READY-01`. Pilot NOT started. Stable tag `v0.8.1-smoke-v2-complete` created after main merge; old tag `v0.8.0-smoke-v2-complete` untouched (immutable provenance at `193d889`).**
**FULL9-T600-01 — 600S CONFIRMATORY TIMEOUT-SENSITIVITY FULL-9 CONTRACT PUBLISHED (2026-08-08), STATUS `CLOSED (2026-08-09) — EXECUTED AND ACCEPTED (SMOKE-V2-CLOSE-01)` (EXECUTABLE COMMIT `e6dbd3e` `chore(smoke): raise confirmatory Full-9 timeout to 600s`, PUSHED, LOCAL = REMOTE; BRANCH `fix/kaggle-smoke-v2-model-output-closure`).** The accepted clean 300-second Full-9 baseline (runtime source/build `7f2a450`, `--timeout 300`) showed **three runs at or beyond the scientific per-run workflow ceiling (~307–337 s)**; to reduce timeout censoring while preserving equal computational opportunity across strategies, the scientific workflow timeout was increased **uniformly to 600 seconds** for **one confirmatory Full-9** (T600). **The 300-second baseline remains valid and preserved** (9/9 terminal / 2 successes / 7 scientific failures / 0 engineering blockers) and is **NOT invalidated or replaced**; **T600 was EXECUTED and ACCEPTED** (`exp-20260808-222843`: uniform `--timeout 600` = 9/9 terminal / 2 successes / 7 scientific failures / 0 engineering blockers / 0 budget-exhausted / 63 model calls / 77,929 tokens / max run ≈373 s / Full-9 verification PASS / HF synchronization PASS — same result as the accepted 300-second baseline; **timeout sensitivity confirmed NOT to censor the accepted signal; NOT an improvement claim**) and changed ONLY the uniform scientific per-run workflow timeout 300 → 600 — all other frozen scientific inputs (model, prompts, strategies, scenarios, evaluator, metrics, max attempts, token budgets, deployment identity `7f2a450`) remain unchanged. 600 seconds applies uniformly to monolithic, selective, and iterative_repository_agent via ONE shared Full-9 command — **no strategy receives extra time**. **Do NOT raise the timeout above 600**; if Pilot runs accumulate near 600 s, analyze the duration/repair distribution and pre-register the Pilot budget instead. New fail-closed output namespace: `/kaggle/working/runs/qwen14b_bnb_nf4_full9_scientific_smoke_wsfix_7f2a450_t600`; new evidence archive prefix: `corrected-full9-t600-wsfix-7f2a450-`. Pre-benchmark validation recorded at contract time: Dataset PASS/carried-forward (zero drift); Prompt PASS/carried-forward (zero drift); Pipeline Smoke PASS (T600 command + fail-closed `_t600` namespace contract); Dry Run PASS (exact 3x3 no-model/bundled dry-run contract with scientific timeout 600); Integration Test PASS (final executable full suite **1947 passed / 33 skipped / 0 failed**); Metric Verification PASS/carried-forward (zero metric/evaluator drift). Audit status: executable implementation PASS; over-engineering PASS (one protocol value, one isolated namespace, contract tests only; no framework/refactor/dependency expansion); scientific identity PASS (runtime source/build remains the frozen `7f2a450` deployment identity — runtime source did not change). Non-destructive RED proof recorded: committed HEAD notebook (`--timeout 300`) FAILS the new 600-second contract; working notebook satisfies it. **SCIENTIFIC SMOKE V2 = COMPLETE AND ACCEPTED; MILESTONE CLOSED. NEXT AUTHORIZED ACTION = INDEPENDENT DELTA AUDIT OF THIS CLOSURE (SMOKE-V2-CLOSE-01); AFTER ACCEPTANCE, MAIN MERGE + STABLE TAG `v0.8.0-smoke-v2-complete`, THEN `PILOT-READY-01`.** Pilot / fine-tune remain unauthorized. No further Kaggle Full-9 is authorized; the accepted T600 run is final Smoke evidence.
**FULL9-EXEC-01 — CANONICAL CORRECTED FULL-9 NOTEBOOK EXECUTION CLOSURE (2026-08-08), STATUS `HISTORICAL — SUPERSEDED BY THE EXECUTED AND ACCEPTED T600 CONFIRMATORY FULL-9 (SMOKE-V2-CLOSE-01)` (COMMIT A `c4aee03` `feat(kaggle): make corrected Full-9 notebook executable`, PUSHED, LOCAL = REMOTE, TREE CLEAN) - THE CANONICAL KAGGLE NOTEBOOK IS NOW THE SINGLE, TESTED, FAIL-CLOSED EXECUTION ARTIFACT FOR EXACTLY ONE FRESH CORRECTED FULL-9** (branch `fix/kaggle-smoke-v2-model-output-closure`, notebook HEAD `c4aee03b14a707bcbe203aa4549b7efb6c5afeee`; milestone tag `v0.8.0-canary.1` @ `31a619857ce07eb09ab5e206fbc9dc792782c99c` — UNCHANGED). Latest Kaggle attempt truth: source/build `7f2a450`; runtime install/preflight PASS; a redundant corrected-source selective canary ran and succeeded — **that attempt is NOT a Full-9**; corrected Full-9 evidence remained **0/9** at that time (later executed and accepted as `exp-20260808-222843` — see FULL9-T600-01 above); the evidence ZIP downloaded from that session must NOT be labeled accepted Full-9 evidence. The canonical notebook removed all stale execution routes (setup order = setup-cell → install-lock-cell → preflight-cell → secrets-cell → full9-execution-cell → full9-verification-cell → export-evidence-cell) and the setup-cell bootstrap is restored fail-closed: `src/` validated and inserted on `sys.path`, `MODEL_CANDIDATES` initialized from `KNOWN_MODEL` with `MODEL_PATH` derived from them (the deleted `MODEL_DIR` NameError regression is fixed), `SCRIPT_PATH` existence guard, `KAGGLE_DEPLOYMENT_PATHS` as source of truth, no canary/continuous state. Validation: full suite **1,947 passed / 33 skipped / 0 failed**; targeted notebook/CLI/bundle 137 passed; related production-path/isolation regression 45 + 33 passed / 1 skipped; notebook JSON parse OK; all canonical code cells compile; bootstrap symbol-closure clean; bundle rebuilt and verified (code/data/notebook parity, no forbidden artifacts); canonical/bundled notebook parity proven; zero data/prompt/metric/runtime drift. **THIS CLOSURE'S PLANNED NEXT ACTION (ONE FRESH CORRECTED FULL-9) WAS SUPERSEDED BY THE T600 CONFIRMATORY FULL-9, WHICH WAS EXECUTED AND ACCEPTED (SEE FULL9-T600-01 ABOVE; SMOKE-V2-CLOSE-01).** MAIN MERGE / STABLE TAG / PILOT / FINE-TUNE REMAIN UNAUTHORIZED; NO FURTHER KAGGLE FULL-9 AUTHORIZED. (sentinel `FULL9_EXEC01_NOTEBOOK_EXECUTION_CLOSURE_AUDIT_REQUIRED`)
**FULL9-WS-02A LAUNCH-SAFETY DOCS/RUNBOOK CLOSURE (2026-08-08) — THE RUNTIME WORKSPACE-ISOLATION FIX IS ACCEPTED (COMMIT A `7f2a450` + COMMIT B `e29c017`, PUSHED, LOCAL = REMOTE, TREE CLEAN); THE FIRST FULL-9 `exp-20260807-205422` (PHYSICALLY COMPLETED 9/9 UNDER RUNTIME SOURCE/BUILD `f7b1ebb`; RAW RESULT 2 SUCCEEDED / 7 FAILED; RAW TOTAL 62 CALLS / 76,858 TOKENS) WAS RUN BUT SCIENTIFICALLY **REJECTED** BECAUSE GENERATED FILES LEAKED ACROSS REUSED STRATEGY WORKSPACES — PRESERVED AS EVIDENCE ONLY (NOT THE ACCEPTED AGGREGATE); THE CANONICAL FULL-9 RUNBOOK IS NOW FAIL-CLOSED FOR THE CORRECTED FRESH RUN: SOURCE_COMMIT=`7f2a4509482dc7e62c2b243374592e9a88e2ff48` / DEPLOYED_BUILD_ID=`7f2a450`, SETUP ORDER = SETUP-CELL → INSTALL-LOCK-CELL → PREFLIGHT-CELL → SECRETS-CELL → FULL-9, OUTPUT DIRECTORY = `/kaggle/working/runs/qwen14b_bnb_nf4_full9_scientific_smoke_wsfix_7f2a450` WITH A NON-EMPTY-DIRECTORY FAIL-CLOSED GUARD, AND THE INITIAL COMMAND HAS NO `--strategy` / `--max-runs` / `--auto-resume-hf`; **THE CORRECTED FRESH FULL-9 HAS NOT YET BEEN RUN**; THE ISOLATED SELECTIVE CANARY `exp-20260807-131819` REMAINS ACCEPTED AND `v0.8.0-canary.1` REMAINS UNCHANGED; OFFICIAL PRE-BENCHMARK GATE (PYTEST 8.4.2) GREEN: 1,928 PASSED / 33 SKIPPED / 0 FAILED; MAIN MERGE = NOT AUTHORIZED; STABLE SMOKE TAG `v0.8.0-smoke-v2-complete` = NOT CREATED; PILOT = NOT AUTHORIZED; NEXT ACTION = INDEPENDENT DELTA AUDIT OF THE FULL9-WS-02A DOCS/RUNBOOK CLOSURE, THEN ONE FRESH CORRECTED FULL-9 ONLY IF ACCEPTED; NO STABLE RELEASE CLAIMED** (branch `fix/kaggle-smoke-v2-model-output-closure`, runtime HEAD `e29c017124473e8e6ad6d54e8cee3ad2315d336e`, corrected deployment source `7f2a4509482dc7e62c2b243374592e9a88e2ff48` / build `7f2a450`; milestone tag `v0.8.0-canary.1` @ `31a619857ce07eb09ab5e206fbc9dc792782c99c`; sentinel `FULL9_WORKSPACE_ISOLATION_CLOSURE_AUDIT_REQUIRED`)

The Qwen 14B selective canary success (2026-08-07) is the first accepted real
Qwen result in the current real-model calibration path: for the first time, a
real Qwen implementation reached and passed every functional validation stage.
The independent GPT-5.6 Thinking audit **ACCEPTED SUCCESSFUL REAL CANARY**.
Real engineering preflight = **PASS** on 2×Tesla T4 (Python 3.12.13 / Django
5.2.16 / DRF 3.17.1 / pytest 8.4.2 / accelerate 1.14.0 / bitsandbytes 0.49.2 /
torch 2.10.0+cu128 / transformers 4.57.6; model identity
`qwen:14b-instruct-v1:bnb-nf4:cfg-cc9474140d25`, footprint 9,721,981,184 bytes;
preflight 174.016 s; probe 68+17 tokens; minimum free VRAM 8.417 GiB, GPU-only
device map). Canary `exp-20260807-131819` (`todo-smoke-001 / selective`) =
**succeeded**: 3 selected / 2 preserved / 3 regenerated, one migration
`todo/migrations/0004_task_priority.py`, 3 model calls / 2,527 prompt + 720
completion = 3,247 tokens / 295.944 s / 0 repair attempts; functional
validation PASS; scenario evaluator PASS 10/10; HF local evidence
`recovery_uploaded`. Accepted real 14B canary records = **1 succeeded / 0
failed** (checkpoint 1 / 0 / 2 pending within the selective-only three-scenario
canary plan). **Milestone tag `v0.8.0-canary.1` = created and pushed,
annotated, non-stable** — first accepted real Qwen 14B NF4 selective-canary
milestone, pointing to `31a619857ce07eb09ab5e206fbc9dc792782c99c`. **Stable
release = NO.** At the time this canary was accepted, Full-9 had not yet been
run; subsequently the first Full-9 `exp-20260807-205422` was run under
`f7b1ebb` and scientifically REJECTED for workspace contamination, and a fresh
corrected Full-9 under `7f2a450` remains pending — the canary is an
isolated selective-only plan; do NOT call it `1/9`. Interpretation: 14B crossed
the model-quality floor seen with 7B on the same task (25.0% fewer calls, 44.1%
fewer tokens, repair eliminated, 14.9% slower) — functional viability, not
strategy superiority. The generated `views.py` includes an unused `Q` import
(non-blocking evidence quality note; the accepted evidence workspace must NOT
be modified or regenerated). The continuous cell failed closed with zero model
calls because the generic experiment was empty — not a failure; do NOT patch
the continuous workflow before the Full-9 run. Next action = **independent
delta audit of the FULL9-WS-02A docs/runbook closure**, then one fresh
corrected Full-9 Scientific Smoke V2 (3 scenarios × 3 arms = 9 records) only
if accepted, using the corrected runbook
`docs/KAGGLE_QWEN14B_FULL9_SCIENTIFIC_SMOKE_RUNBOOK.md` — corrected identity
SOURCE_COMMIT=`7f2a4509482dc7e62c2b243374592e9a88e2ff48` /
DEPLOYED_BUILD_ID=`7f2a450`, fail-closed output
`/kaggle/working/runs/qwen14b_bnb_nf4_full9_scientific_smoke_wsfix_7f2a450`;
one engineering preflight + one benchmark process in a fresh isolated
experiment; never merge the canary or the rejected Full-9; then independent
results audit. Record:
`selective_updates/records/QWEN14B-SELECTIVE-CANARY-SUCCESS-2026-08-07.md`.

The Qwen 14B NF4 v4 loader official gate (2026-08-05) completed the missing
official clean-environment gate and corrected one stale Notebook markdown
statement (docs/deploy only — no runtime code, tests, requirements, data,
prompts, scenarios, strategies, evaluator logic, metrics, model settings, or
runtime limits changed). The markdown cell immediately before `preflight-cell`
in `notebooks/seven_arm_benchmark.ipynb` described the load as **int8**
(`load_in_8bit=True` + `device_map="auto"` with `expandable_segments`) — stale;
it now truthfully reads **Qwen 14B BNB-NF4 load** (`Qwen2.5-Coder-14B-Instruct`
base checkpoint via BitsAndBytes NF4: `load_in_4bit=True`,
`bnb_4bit_quant_type="nf4"`, `bnb_4bit_compute_dtype=float16`,
`bnb_4bit_use_double_quant=True`, `device_map="auto"`, Transformers 4.57.6). No
executable code cell, `SOURCE_COMMIT`/`DEPLOYED_BUILD_ID` (`41e9ad7`), command,
quantization setting, model path, timeout, token limit, or authorization flag
was altered. The official gate ran in a fresh disposable env created from
project declarations only (`_workspace\cache\prebenchmark-py311-v4-loader`,
Python 3.11.5 / **pytest 8.4.2 exactly**; Django 5.2.16, DRF 3.17.1,
pytest-django 4.12.0, pytest-asyncio 1.2.0, ruff 0.15.22, mypy 1.20.2): full
suite **1,898 passed / 32 skipped / 0 failed** (517.97 s); Dataset 281/4;
Prompt 126/4; Pipeline Smoke 177; Scripted dry run `--profile
scientific-smoke-v2` 9 planned / 9 terminal / 9 succeeded / 0 failed / exit 0;
Metric Verification 169; Ruff 0 new (91 pre-existing baseline in untouched
files); mypy strict Success (77 files); compileall clean; notebook code cells
compile canonical + bundled; bundle rebuilt twice via
`scripts/build_upload_bundle.py` — second run content-identical (147 files /
965,015 bytes; tree hash 26EA934F16A25C14788484CE1A75EFF4FB453E6C346F5FDCEE72D3004EC5B7D1),
manifests verified, no cache files; `git diff --check` clean. Commit
`docs(deploy): finalize Qwen 14B NF4 loader gate truth` pushed, local = remote,
tree clean. No Kaggle run, no preflight, no canary, no continuous, no
merge/tag/Pilot; **no real 14B result and no stable release claimed**; accepted
real records = 0/9. Next action after independent audit = **Kaggle engineering
preflight cell only**.

The Qwen 14B NF4 transformers v4 loader closure (2026-08-05) fixed the loader
defect the independent OOM audit reproduced at `9fd4eee`: transformers was
unpinned, Kaggle image drift installed **5.0.0**, and its loader materialized
the **14B BF16 weights on GPU before BNB-NF4 quantization** — OOM after
232.412 s at ~75% of 579 checkpoint params (tried 136 MiB; GPU 1 free
46.81 MiB / allocated 14.38 GiB; runtime Python 3.12.13 / transformers 5.0.0 /
bitsandbytes 0.49.2 / accelerate 1.14.0 / torch 2.10.0+cu128). Commit A
`41e9ad7` (`fix(model): pin transformers==4.57.6 BNB loader and preserve static
preflight metadata`) + Commit B `920ab9b` (`chore(deploy): repin Qwen 14B NF4
v4 loader closure bundle`), pushed, local = remote, tree clean. Fixes: (A)
`requirements-smoke-kaggle.lock` + `requirements-kaggle.txt` pin
`transformers==4.57.6` (torch stays unpinned — Kaggle torch preserved); (B)
preflight `_REQUIRED_IMPORTS` requires the exact `"4.57.6"` — any other version
FAILs before staging/model load; (C) notebook `install-lock-cell`
`EXPECTED_RUNTIME` gains transformers 4.57.6 with the fail-closed mismatch
check; (D) `kaggle_qwen_backend._load_model` passes `low_cpu_mem_usage=True`
for `bnb-int8`/`bnb-nf4` so the 4.57.x loader streams/quantizes in place; (E)
preflight `_static_model_metadata` preserves `model_identity` /
`checkpoint_basename` / `checkpoint_quantization_method` / `gpu_count` /
`gpu_name` (from `config.json` + CUDA discovery, no weight load) when the load
OOMs/fails. Regression proofs: preflight FAILs on transformers 5.0.0/absent
before load; BNB loads pass `low_cpu_mem_usage=True` (fp16 does not); static
metadata preserved on failed probe. Record:
`selective_updates/records/QWEN14B-NF4-TRANSFORMERS-V4-LOADER-CLOSURE.md`.

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
FULL9-T600-01 600s CONFIRMATORY TIMEOUT-SENSITIVITY FULL-9 CONTRACT = PUBLISHED (2026-08-08) and CLOSED (2026-08-09, SMOKE-V2-CLOSE-01) — executable commit e6dbd3e (chore(smoke): raise confirmatory Full-9 timeout to 600s), pushed, local = remote; the accepted clean 300-second Full-9 baseline (runtime source/build 7f2a450, --timeout 300) showed three runs at or beyond the scientific per-run workflow ceiling (~307–337 s); uniform scientific per-run workflow timeout raised 300 → 600 for ONE confirmatory Full-9 (T600) to reduce timeout censoring while preserving equal computational opportunity; 300-second baseline REMAINS VALID AND PRESERVED (9/9 terminal / 2 successes / 7 scientific failures / 0 engineering blockers) and is NOT invalidated or replaced; T600 WAS EXECUTED AND ACCEPTED (exp-20260808-222843): uniform --timeout 600 = 9/9 terminal / 2 successes / 7 scientific failures / 0 engineering blockers / 0 budget-exhausted / 63 model calls / 77,929 tokens / max run ≈373 s / Full-9 verification PASS / HF synchronization PASS — same result as the accepted 300-second baseline (timeout sensitivity confirmed NOT to censor the accepted signal; NOT an improvement claim); changed ONLY the timeout — all other frozen scientific inputs unchanged; 600s applies uniformly to monolithic / selective / iterative_repository_agent via ONE shared Full-9 command, no strategy receives extra time; DO NOT raise the timeout above 600 — if Pilot runs accumulate near 600 s, analyze duration/repair distribution and pre-register the Pilot budget instead; new fail-closed output namespace = /kaggle/working/runs/qwen14b_bnb_nf4_full9_scientific_smoke_wsfix_7f2a450_t600; new evidence archive prefix = corrected-full9-t600-wsfix-7f2a450-; pre-benchmark validation recorded at contract time: Dataset PASS/carried-forward (zero drift), Prompt PASS/carried-forward (zero drift), Pipeline Smoke PASS (T600 command + fail-closed _t600 namespace contract), Dry Run PASS (exact 3x3 no-model/bundled dry-run contract with scientific timeout 600), Integration Test PASS (final executable full suite 1947 passed / 33 skipped / 0 failed), Metric Verification PASS/carried-forward (zero metric/evaluator drift); audit status = executable implementation PASS / over-engineering PASS (one protocol value, one isolated namespace, contract tests only) / scientific identity PASS (runtime source/build remains the frozen 7f2a450 deployment identity — runtime source did not change); non-destructive RED proof recorded (committed HEAD notebook with --timeout 300 FAILS the 600-second contract; working notebook satisfies it); SCIENTIFIC SMOKE V2 = COMPLETE AND ACCEPTED, MILESTONE CLOSED; next action (HISTORICAL — completed) = independent delta audit of this closure (SMOKE-V2-CLOSE-01), then main merge + stable tag v0.8.0-smoke-v2-complete, then PILOT-READY-01 — all executed (closure merged `193d889`; MAIN-GREEN-01 merged `d875c72`; preferred recovery `v0.8.1-smoke-v2-complete`; next task `PILOT-READY-01`); Pilot execution NOT STARTED (fine-tune unauthorized); no further Kaggle Full-9 authorized
FULL9-WS-02A LAUNCH-SAFETY DOCS/RUNBOOK CLOSURE = COMPLETE (2026-08-08) — docs/runbook-only closure; no runtime/test/data/prompt/metric/notebook/bundle change; canonical Full-9 runbook now uses the corrected runtime identity SOURCE_COMMIT=7f2a4509482dc7e62c2b243374592e9a88e2ff48 / DEPLOYED_BUILD_ID=7f2a450 (NOT f7b1ebb); setup order = setup-cell → install-lock-cell → preflight-cell → secrets-cell → Full-9; corrected output directory = /kaggle/working/runs/qwen14b_bnb_nf4_full9_scientific_smoke_wsfix_7f2a450 with a fail-closed non-empty-directory guard raising before mkdir; initial Full-9 command has no --strategy / --max-runs / --auto-resume-hf; resume/merge/copy-forward of rejected exp-20260807-205422 and accepted canary exp-20260807-131819 explicitly prohibited; current-state docs then said first Full-9 = RUN BUT REJECTED and corrected fresh Full-9 = NOT YET RUN (this was later resolved: the corrected Full-9 was executed and accepted as the T600 confirmatory run exp-20260808-222843 — see FULL9-T600-01 above, SMOKE-V2-CLOSE-01); next action = independent delta audit of this closure, then one fresh corrected Full-9 only if accepted; prior corrected-runtime pre-benchmark gate carried forward (zero benchmark-relevant drift); Kaggle Full-9 NOT run in this task; main merge / stable tag / Pilot / fine-tune remain unauthorized
FULL-9 WORKSPACE ISOLATION CLOSURE = COMPLETE (2026-08-08) — rejected Full-9 exp-20260807-205422 (9/9 completed, 2 succeeded / 7 failed, 62 calls / 76,858 tokens, runtime source f7b1ebb) = overlay source restaging leaked generated files across scenarios (0004_task_priority survived into 002 and produced 0005_remove_task_priority_task_deleted_at; affected selective/agent 002 and 003); scientific acceptance REJECTED, preserved as evidence only; fixed by exact reset from immutable snapshot before every matrix run — Commit A 7f2a450 (fix(smoke): reset workspace source before every matrix run; _WORKSPACE_INFRASTRUCTURE_DIRS={runs,tmp,snapshots}, _reset_workspace_source_from_snapshot deletes source tree then restages, make_isolation calls it per arm workspace per run) + Commit B e29c017 (chore(deploy): repin isolated Full-9 Smoke bundle; SOURCE_COMMIT=7f2a4509482dc7e62c2b243374592e9a88e2ff48 / DEPLOYED_BUILD_ID=7f2a450), pushed, local = remote, tree clean; unit edge cases 33 passed / 1 skipped (symlink skipped on Windows); sequential 001→002→003 migration proof green (002 clean, no 0004_task_priority, depends on canonical 0003) + nine-run zero-residue matrix proof; OFFICIAL PRE-BENCHMARK GATE (Python 3.11.9 / pytest 8.4.2 exactly, _workspace\cache\prebenchmark-py311) GREEN = 1,928 passed / 33 skipped / 0 failed (859.46 s); Dataset 161/1 (27 scenarios unchanged, scopes intact), Prompt 200/12, Pipeline Smoke 45 (incl. sequential regression), Dry Run 9 planned / 9 terminal / 9 succeeded / 0 failed / exit 0, Metric Verification 187; ruff 0 new (5 pre-existing baseline); mypy 0 new (4 pre-existing baseline); compileall clean; notebook cells compile; bundle content-identical (147 files / 969,713 bytes), manifests verified, no cache files; Kaggle NOT rerun; isolated canary remains accepted; v0.8.0-canary.1 unchanged; audit marker FULL9_WORKSPACE_ISOLATION_CLOSURE_AUDIT_REQUIRED
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
QWEN 14B NF4 TRANSFORMERS V4 LOADER CLOSURE + OFFICIAL GATE = COMPLETE (2026-08-05) — Commit A 41e9ad7 (fix(model): pin transformers==4.57.6 BNB loader and preserve static preflight metadata) + Commit B 920ab9b (chore(deploy): repin Qwen 14B NF4 v4 loader closure bundle) + official gate docs/deploy commit (docs(deploy): finalize Qwen 14B NF4 loader gate truth); transformers==4.57.6 pinned in lock + requirements-kaggle.txt (torch unpinned), preflight _REQUIRED_IMPORTS exact version fail-closed, notebook EXPECTED_RUNTIME entry, low_cpu_mem_usage=True for bnb-int8/bnb-nf4, _static_model_metadata preserved on failed probe; stale int8 markdown cell corrected to truthful BNB-NF4 wording (docs-only); official clean-env gate (fresh disposable env from declarations, Python 3.11.5 / pytest 8.4.2 exactly) FULL SUITE = 1,898 passed / 32 skipped / 0 failed (517.97 s); Dataset 281/4, Prompt 126/4, Pipeline Smoke 177, Dry Run 9/9/9/0 exit 0, Metric 169; ruff 0 new (91 baseline); mypy strict Success (77 files); compileall clean; notebook compile canonical + bundled; bundle content-identical double rebuild (147 files / 965,015 bytes); git diff --check clean; audit marker QWEN14B_V4_LOADER_OFFICIAL_GATE_AUDIT_REQUIRED
QWEN 14B SELECTIVE CANARY SUCCESS = COMPLETE (2026-08-07) — independent GPT-5.6 Thinking audit ACCEPTED SUCCESSFUL REAL CANARY; real engineering preflight PASS (2×Tesla T4, bnb-nf4, identity qwen:14b-instruct-v1:bnb-nf4:cfg-cc9474140d25, footprint 9,721,981,184 bytes, 174.016 s, probe 68+17, min free VRAM 8.417 GiB, GPU-only); canary exp-20260807-131819 (todo-smoke-001 / selective) SUCCEEDED — 3 selected / 2 preserved / 3 regenerated, migration todo/migrations/0004_task_priority.py, 3 model calls / 2,527+720=3,247 tokens / 295.944 s / 0 repair attempts; functional validation PASS; scenario evaluator PASS 10/10; HF local evidence recovery_uploaded; accepted real 14B canary records = 1 succeeded / 0 failed (isolated selective-only plan, NOT 1/9); at the time this canary was accepted Full-9 was NOT RUN — subsequently the first Full-9 exp-20260807-205422 was run under f7b1ebb and REJECTED for workspace contamination, and a fresh corrected Full-9 under 7f2a450 remains pending; vs 7B: 25.0% fewer calls / 44.1% fewer tokens / repair eliminated / 14.9% slower → functional viability, not strategy superiority; unused `Q` import in generated views.py = non-blocking, evidence NOT to be repaired; continuous cell failed closed with zero model calls (generic experiment empty); record selective_updates/records/QWEN14B-SELECTIVE-CANARY-SUCCESS-2026-08-07.md
Current real records = accepted clean 300-second Full-9 baseline (runtime 7f2a450, --timeout 300): 9/9 terminal / 2 successes / 7 scientific failures / 0 engineering blockers — valid and preserved; accepted 600-second confirmatory Full-9 exp-20260808-222843 (uniform --timeout 600): 9/9 terminal / 2 successes / 7 scientific failures / 0 engineering blockers / 0 budget-exhausted / 63 model calls / 77,929 tokens / max run ≈373 s — valid and accepted; the first Full-9 exp-20260807-205422 (source f7b1ebb) remains REJECTED contamination evidence only
Real Qwen records = 1 accepted selective canary + accepted clean 300-second Full-9 baseline (9 terminal records) + accepted T600 confirmatory Full-9 (9 terminal records, exp-20260808-222843)
Real 14B engineering preflight = PASS
Accepted real 14B selective canary = 1 succeeded / 0 failed
Milestone tag = v0.8.0-canary.1 (created/pushed, annotated, non-stable, points to 31a6198) — unchanged
Stable release = NO
Full 9-record Scientific Smoke V2 = COMPLETE AND ACCEPTED (SMOKE-V2-CLOSE-01) — accepted clean 300-second baseline (source/build 7f2a450, --timeout 300) VALID AND PRESERVED (2 successes / 7 scientific failures / 0 engineering blockers, three runs at ~307–337 s ceiling) + accepted 600-second confirmatory Full-9 exp-20260808-222843 (uniform --timeout 600, _t600 namespace; 2 successes / 7 scientific failures / 0 engineering blockers / 0 budget-exhausted / 63 model calls / 77,929 tokens / max run ≈373 s; Full-9 verification PASS; HF synchronization PASS); first Full-9 exp-20260807-205422 (source f7b1ebb) REJECTED (evidence only); the 600-second run did NOT change the 2/9 result — timeout sensitivity confirmed, NOT an improvement claim
Main merge = COMPLETE — SMOKE-V2-CLOSE-01 docs closure merged to main (193d889); post-merge hotfix MAIN-GREEN-01 merged (main now d875c72)
Stable Smoke tag = v0.8.0-smoke-v2-complete — CREATED at 193d889 (immutable provenance); preferred recovery tag = v0.8.1-smoke-v2-complete at main d875c72
Pilot = NOT STARTED — Pilot execution not authorized; PILOT-READY-01 = CLOSED (2026-08-10); next task = PILOT-EXEC-01 (Pilot freeze + execution)
README = updated
push = PUBLISHED — main d875c72 at origin/main, local = remote
milestone tag = v0.8.0-canary.1 (created/pushed, annotated, non-stable, points to 31a6198); stable Smoke tag v0.8.0-smoke-v2-complete CREATED at 193d889 (see above)
next action = HISTORICAL (SUPERSEDED — PILOT-READY-01 is now CLOSED, see line 226 and Current Task): at the time, PILOT-READY-01 (prepare the repository for Pilot readiness; Pilot execution NOT STARTED). HISTORICAL PLANNED NEXT ACTION AT THAT TIME — SUPERSEDED: INDEPENDENT DELTA AUDIT OF THE SCIENTIFIC SMOKE V2 CLOSURE (SMOKE-V2-CLOSE-01) — the 600-second confirmatory Full-9 was EXECUTED AND ACCEPTED (exp-20260808-222843, uniform --timeout 600, _t600 output namespace, evidence prefix corrected-full9-t600-wsfix-7f2a450-, 9/9 terminal / 2 successes / 7 scientific failures / 0 engineering blockers / 0 budget-exhausted / 63 model calls / 77,929 tokens / max run ≈373 s, Full-9 verification PASS, HF synchronization PASS, same 2/9 result as the accepted clean 300-second baseline, timeout sensitivity confirmed, NOT an improvement claim); after acceptance of the closure, main merge + stable tag v0.8.0-smoke-v2-complete, then PILOT-READY-01 — all completed; Pilot / fine-tune not authorized; no further Kaggle Full-9 authorized
```

## Previous Phase
**R5 — Nine Non-Dry Scripted Production Records — ACCEPTED AND FROZEN**

R5 proved exactly nine non-dry scripted production records (3 frozen scenarios × 3 arms × 1 repetition) through the real production orchestration path. R5 was accepted by the independent re-audit on 2026-08-01 at `7761c48`. The cleaned R5 tail is `8fafb50`, `a24a9cd`, `875e4d1`, `ee148fa`, `7761c48`. The old contaminated tail is preserved on `backup/r5-pre-audit-c3ecad2`.

## Current Task
PILOT-READY-01 is **CLOSED** (2026-08-10) — the Pilot readiness closure is
complete on branch `feat/pilot-ready-01` (code/test commit `34ecf78` pushed,
local = remote). The selective arm's repository-level input contracts were fixed
(per-repository dependency graphs, per-repository editable universes,
file-granular descriptors for django CMS/Saleor), the stale real-smoke
expectation was corrected (`STRATEGIES_WITH_MISSING_PREREQS = {"agent"}`), and a
focused 12-test multi-repo production-path contract was added. Full suite green:
**2,026 passed / 33 skipped / 0 failed**. Exact fresh 48-cell Pilot dry-run:
48/48 succeeded, 0 failed, deterministic unique run IDs, zero residue. Gate 6
isolation/evidence/export gates: 142 passed. **Pilot = NOT STARTED** (execution
not authorized); **next task = `PILOT-EXEC-01`**; stable tag `v0.9.0-pilot-ready`
after main merge. No accepted Smoke evidence or frozen source history changed.

## Previous Task
MAIN-GREEN-01 is **COMPLETE** — the post-merge test-isolation and
reproducibility defect is FIXED and CLOSED. The full suite is green again
**1,958 passed / 33 skipped / 0 failed** (was 12 failed / 4 errors after the
SMOKE-V2-CLOSE-01 merge). Root causes were working-tree state, not scientific:
`core.autocrlf=true` CRLF checkouts of byte-frozen LF fixtures (bundle
evaluator assets + `benchmark_data/repositories/todo/**`) and
`__pycache__/*.pyc` residue inside baseline comparisons. Fix = `.gitattributes`
`text eol=lf` pins + LF renormalization + ephemeral-baseline predicate in the
test fixtures — **zero scientific drift** (no production code, prompts,
datasets, strategies, metrics, model identity, or timeout changes). Repeatability
proven twice (T4/T5/T7); full suite green (T9); static gates clean; dry-run
pipeline 8/8 clean. **Next task (then) = `PILOT-READY-01`** — leave the repo ready for
a weaker AI to continue directly; do NOT start Pilot. Closure executed: docs commit
B (`c2be100 docs(audit): record post-merge reproducibility hotfix`),
independent-style audit, non-ff merge `d875c72 merge(fix): close Smoke-v2 test-isolation
reproducibility defect`, annotated tag `v0.8.1-smoke-v2-complete` (peeled == main
HEAD `d875c72`); `v0.8.0-smoke-v2-complete` remains immutable provenance at
`193d889`. Pilot / fine-tune remain unauthorized; no Kaggle Full-9 rerun for this
hotfix.


 The real attempt `exp-20260801-123125` failed at runtime root (FP16 model exceeded GPU memory; dependency versions had drifted from the previously assumed runtime). R7C (`fix/kaggle-smoke-v2-real-run-root`, commits `7a80e53` + `f01b8f0`) closes the four root contracts: **(1) environment memory** — exact runtime pins in `requirements-smoke-kaggle.lock` (Django==5.2.16, djangorestframework==3.17.1, pytest==8.4.2, pytest-django==4.12.0, accelerate==1.14.0, bitsandbytes==0.49.2, transformers==4.57.6 — Qwen14B NF4 transformers v4 loader closure (2026-08-05); torch intentionally unpinned, Kaggle image provides its GPU torch build) installed and verified in the notebook `install-lock-cell` (`EXPECTED_RUNTIME` via `RUNTIME_ATTR`, `runtime_environment.json` schema `kaggle_runtime_environment.v1`); **(2) memory contract** — int8 default (`qwen:1:int8`), `PYTORCH_ALLOC_CONF=expandable_segments:True`, seeded 64-token `run_probe`, preflight ≥2.0 GiB VRAM headroom; **(3) prompt contract** — frozen `RegenerationScenarioContext` in strategy prompts, preserve-only byte-identity enforcement when `expected_actions` is non-empty; **(4) repair contract** — `FailureKind.infrastructure_nonrepairable` first-failure, one execution, zero LLM repair. `src/benchmark/execution/preflight.py` adds `--kaggle-preflight-only` (exit 0/1, no experiment/RunRecord/checkpoint/workspace/HF state; schema `kaggle_smoke_preflight.v1`, 6 checks), run as a notebook gate cell before the exec cell; `secrets-cell` moved after preflight. Notebook now: setup → install lock → preflight → secrets → run. Bundle rebuilt via `scripts/build_upload_bundle.py` (147 files / 894,735 bytes; notebook 36,351 bytes). Full suite (contract-first) = 1,451 passed / 31 skipped / 0 failed was a SUBSET mislabeled as full suite — the true first full suite was 23 failed / 1,759 passed / 32 skipped (root cause: blanket `baseline_validation => infrastructure_nonrepairable` in `src/benchmark/execution/runner.py`); the independent GPT-5.6 Thinking correction was imported via bundle fast-forward (`ffa179a` + `6d6aa36`, HEAD `6d6aa36`, pushed): the exact 23 former failures now pass, and DRF import mapping, exact version verification, fail-fast preflight, driver-level VRAM, CPU-offload rejection, Python 3.12 runtime contract, and stale source identity (SOURCE_COMMIT=ffa179a / DEPLOYED_BUILD_ID=ffa179a) were corrected. Current full gate (Windows / Python 3.11.5) = 1,790 passed / 32 skipped / 0 failed; mypy strict 0; compileall clean; builder rerun clean. Valid real Qwen remains 0/9; Kaggle remains blocked pending the independent full-gate audit. Current task: **independent full-gate audit of the corrected R7C branch** (`R7C_CORRECTION_FULL_GATE_AUDIT_REQUIRED`), then update the Kaggle code dataset + notebook, then one real cell, then continue to 9/9 — blocked on the audit. **R7C post-gate correction imported (independent post-gate audit on e47a1e\, exact correction f88823\ + /97fc0\, HEAD /97fc0\, pushed):** the audit found (a) the project-local \ImportError\ was incorrectly bypassing repair (the blanket marker match is replaced by the canonical \classify_validation_repairability\ classifier, so project-local \ModuleNotFoundError\ and \cannot import name\ are repairable while missing declared Django and CUDA OOM stay \infrastructure_nonrepairable\), (b) the bundled preflight could not import \enchmark\ without an ambient \PYTHONPATH\ (the bundled script now bootstraps its own \src/\ and reaches its preflight in a clean subprocess), and (c) preflight output was buffered (now streamed and persisted). Notebook source identity is now \SOURCE_COMMIT = 6f88823\, \DEPLOYED_BUILD_ID = 6f88823\. Current full gate (Windows / Python 3.11.5) = 1,796 passed / 32 skipped / 0 failed; mypy strict 0; compileall clean; builder rerun content-identical; bundle manifests verified. Valid real Qwen remains 0/9; no scientific evidence exists yet; Kaggle remains blocked pending the final independent full-gate audit, after which the only authorized Kaggle action is the engineering preflight cell - not the scientific One-Run cell. **QWEN 14B MULTI-GPU VRAM PREFLIGHT CLOSURE (2026-08-06):** the independent audit (`QWEN14B_MULTI_GPU_VRAM_PREFLIGHT_INDEPENDENT_AUDIT_2026-08-06.md`) found the preflight on the `897e323` state (full suite was green) read VRAM from **GPU 0 only** — `_qwen_probe_metrics` used `torch.cuda.memory_allocated(0)` / `memory_reserved(0)` / `mem_get_info(0)` / `synchronize(0)` and `vram_headroom` checked only that single free value, so a 2x Tesla T4 `device_map="auto"` 14B bnb-nf4 load could pass while GPU 1 had <2.0 GiB free. Commit A `f7b1ebb` (`fix(model): enforce multi-GPU VRAM headroom per visible GPU`) + Commit B `c8f5685` (`chore(deploy): repin multi-GPU VRAM preflight bundle`), pushed, local = remote, tree clean. **Fix:** immutable `GpuVramSnapshot` (`device_index/gpu_name/allocated_gib/reserved_gib/free_gib/total_gib`); `_collect_gpu_vram_snapshots()` synchronizes and reads allocated/reserved/free/total on **every** visible GPU (three-decimal rounding, never swallows a per-GPU failure, `()` when CUDA unavailable); `free_vram_after_probe_gib = min(snapshot.free_gib)` with summed allocated/reserved scalars; minimum-free gate requiring **every visible GPU >= 2.0 GiB** (`vram_headroom: PASS (minimum free across 2 GPU(s)=X.XX GiB)` / `FAIL (GPU 1 free=0.12 GiB < 2.0 GiB)`, all failing devices listed by index); ordered per-GPU evidence in the `kaggle_smoke_preflight.v1` JSON (`gpu_vram_by_device`) and one line per GPU in the human preflight table; per-GPU snapshots preserved on failed model loads via `_static_model_metadata`. Official clean-env gate (`_workspace\cache\prebenchmark-py311-v4-loader`, Python 3.11.5 / **pytest 8.4.2 exactly**): full suite **1,915 passed / 32 skipped / 0 failed** (500.22 s; +17 net new tests); Metric Verification 169; Ruff 0 new (86 pre-existing baseline); mypy strict Success (77 files); compileall clean; notebook + bundle pin identity PASS (`SOURCE_COMMIT=f7b1ebb`); bundle integration 32 passed; builder content-identical (147 files / 968,722 bytes). Mandatory adversarial reproduction: **GPU0 free 3.0 GiB / GPU1 free 0.125 GiB → FAIL**. No Kaggle run, no preflight on Kaggle, no canary, no continuous, no model/quantization/prompt/data change, no GPTQ/AWQ/GGUF/vLLM, no merge/tag/Pilot; **no real 14B result and no stable release claimed**; accepted real records remain 0/9. **Next action after independent audit = Kaggle engineering preflight cell ONLY.** Sentinel: `QWEN14B_MULTI_GPU_VRAM_CLOSURE_AUDIT_REQUIRED`. Record: `selective_updates/records/QWEN14B-MULTI-GPU-VRAM-PREFLIGHT-CLOSURE.md`.

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
`main` @ `f211e4d` = **PILOT-EXEC-01 KAGGLE NO-PIP REPO-ENV PROVISIONING CLOSURE** (non-ff merge `44d0102` of `fix/pilot-kaggle-env-provisioning-closure` — commits `28f0405` fix + `fd6353c` docs; `FROZEN_SOURCE_TAG` bump `f211e4d`; tagged `v0.9.9-pilot-exec-ready`, pushed; archive `dist/pilot-kaggle-upload.zip` SHA-256 `3f93b0a9…` + sidecar rebuilt from the tag, deterministic; bundled 48-cell dry-run 48/48). Historical execution-ready tags `v0.9.0`/`v0.9.1`/`v0.9.2`/`v0.9.3`/`v0.9.4`/`v0.9.5`/`v0.9.6`/`v0.9.7`/`v0.9.8`-pilot-exec-ready NOT moved.

## Latest Commit (main HEAD)
`f211e4de664da0f0745e5cde5e1fd5138b3172f0` `chore(pilot): move FROZEN_SOURCE_TAG to v0.9.9-pilot-exec-ready`; tag `v0.9.9-pilot-exec-ready` peels to this commit (merge `44d01028cb3b4576a28c136bad1c2e2f08b7971f` directly beneath).

## Known Risks
1. **LR-3 - No test data boundary:** Test fixtures need a defined home outside `inputs/` and `src/`.
2. **LR-5 - Paper vs. implementation drift:** Must document any conflict rather than silently resolving.
3. **LR-7 - django CMS and Saleor not yet cloned locally:** Test suite runnability not verified locally beyond manifest documentation.
4. **LR-8 - Scenario content quality:** YAML files generated by automated agents; manual review recommended before Phase 4.

## Exact Next Task
1. `PILOT-EXEC-01` - **KAGGLE NO-PIP REPO-ENV PROVISIONING CLOSURE — MERGED + TAGGED `v0.9.9-pilot-exec-ready` (2026-08-15)** - the final real Kaggle preflight blocker is closed: `python -m venv`'s internal `ensurepip` cannot produce a working pip on Kaggle (runtime lock installs pip into the base interpreter; real cell died `[.../djangocms/bin/python3', '-m', 'ensurepip', '--upgrade', '--default-pip'] returned non-zero exit status 1`, ~0.24 s). New stdlib-only helper `scripts/pilot_kaggle_repo_envs.py` provisions `tools`/`djangocms`/`saleor` envs with NO ensurepip (stdlib venv `--without-pip`; HOST pip `-m pip --python <target>` bootstrap; `uv` via host pip; django CMS deps `uv pip install -r` from frozen snapshot; Saleor pinned-snapshot copy + `uv venv .venv --python <existing 3.12>` with `UV_PYTHON_DOWNLOADS=never` + `uv sync --locked`; markers `.pilot_env_ready.json` + health probes; rebuild ONLY the invalid private env dir; ONE apt transaction for `gettext`+`gcc`+`libpq-dev`; secret-redacting provisioning log). Thin-adapter `pilot-repo-preflight-cell`; bundle ships the helper (byte-equal + hashed). No scientific inputs changed. Gates: provisioning 24/24, notebook contract 46/46, service bootstrap 41/41, real-launch preflight 13/13, deployment bundle 52/52, full suite **2,225 passed / 33 skipped / 0 failed**. Merged non-ff (`44d0102`) + tag bump (`f211e4d`) + tag `v0.9.9-pilot-exec-ready` pushed; exact `dist/pilot-kaggle-upload.zip` SHA-256 `3f93b0a9…` + sidecar rebuilt from the tagged source; bundled 48-cell dry-run 48/48. **NEXT:** upload the exact archive as ONE Kaggle Dataset → target preflight → real 48-cell Pilot (ONLY after all preflights pass). **Pilot = NOT STARTED.** Real launch still deferred until the user confirms the actual Kaggle mounted model path and HF results repository ID.
2. `PILOT-READY-01` - **CLOSED (2026-08-10)** - Pilot readiness closure completed on `feat/pilot-ready-01` (`34ecf78` pushed): multi-repo selective input contracts fixed, stale real-smoke expectation corrected, 12-test multi-repo production-path contract added, full suite 2,026 passed / 33 skipped / 0 failed, exact 48-cell Pilot dry-run 48/48 deterministic, isolation/evidence/export gates 142 passed. Pilot execution NOT STARTED.
3. Per-run workflow timeout stays frozen at 600 s uniformly; no further Kaggle Full-9 is authorized.

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

MAIN_GREEN_01_CLOSURE_AUDIT_REQUIRED
