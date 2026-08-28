# Project Handoff — Dependency-Aware Selective Regeneration Benchmark

> **CURRENT STATE (2026-08-28, v0.9.22 D8 DRY-RUN TOKEN-SCHEMA + LAUNCH-AUTH
> EVIDENCE CLOSURE; REAL T4 PROOF PENDING):** D8 closes the proven `RunRecordData`
> token-schema drift — a real 48-record dry-run writes nested `token_usage`
> (`prompt/completion/total`), `total_workflow_model_calls` / `total_workflow_tokens`,
> and phase `selection|regeneration|repair` `_model_calls` / `_total_tokens`, NEVER a
> top-level `total_tokens`. D8.1 adds canonical `validate_pilot_dryrun_evidence` +
> `_collect_dryrun_evidence_errors` with strict `_expect_zero_int`, and refactors
> `validate_pilot_launch_authorization` onto the same collector; D8.2 the bundled
> `dryrun-cell` calls the canonical validator (`dry-run:mock`) and prints only
> summary-backed totals; D8.3 the GQA per-device display reads real evidence fields
> instead of the fabric `.get('available')`. Genuine RED: 39 unit tests + 1
> false-green proof failed pre-D8.1; GREEN: focused 40/40 plus 136/136
> (contract+bundle); full acceptance is **2492 passed / 33 skipped / 0 failed**.
> Exact-artifact dry-run is **48/48** (48 unique IDs, repos 16/16/16, strategies
> 24/24, reps 24/24, zero calls/tokens), every record source commit ==
> `8f0b11953a4fe2990b7e6c680288be282b8a6b67`. Exact artifact SHA-256 is
> `02d16ca2c3a35969b32ac438e577f41198e376ba0ce9ee88757a07bd46f268ee`;
> sidecar matches; trust/provenance 0 mismatches, FROZEN. `e0a64937…` (D7),
> `ce40b330…` / `f72ecda…` are SUPERSEDED. Scientific inputs unchanged. No stable
> tag exists; next is the exact new-artifact 2x T4 model preflight only, and tag
> `8f0b119…` only after GQA microprobe + short + 12k PASS. No 48-cell launch while
> untagged. Report:
> `reports/V0922_D8_DRYRUN_TOKEN_SCHEMA_LAUNCH_AUTH_CLOSURE_REPORT.md`.
> **Authoritative snapshot: `docs/AI_ACCOUNT_TRANSFER_HANDOFF.md`.**
>
> **PRIOR STATE (2026-08-27, SUPERSEDED by D8 — LAUNCH/RESUME VALIDATION-ARGV
> EXECUTABILITY CLOSURE):** D6 was RESOLVED at `1b857fc…` before D7. D7 made all three
> per-repository validation-interpreter mappings and `--validation-timeout 1800` live AST
> elements in both Pilot launch routes, with exact AST and canonical/fresh-bundle newline
> regression tests. Affected GREEN 102/102; full acceptance **2442 passed / 33 skipped /
> 0 failed**; exact-artifact dry-run 48/48 at source
> `3ebc75dad2f47c8985ce045bcdc8907ce2d52f3c`; artifact
> `e0a649375104b44d1de7bc5f39145f81bc21365a4380755e73cb1efb719390a8` FROZEN (superseded by
> D8; do not upload). Report was
> `reports/V0922_D7_LAUNCH_RESUME_ARGV_EXECUTABILITY_CLOSURE_REPORT.md`.
>
> **PRIOR STATE (2026-08-27, SUPERSEDED by D7 — GQA MICROPROBE + NOTEBOOK + EXPORT
> INTEGRITY CLOSURE; REAL T4 PROOF PENDING):** branch
> `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure` (built on `ba083925…` + the
> T4 GQA SDPA/preflight-observability closure) carries the D1–D6 bounded correction:
> D1 `_gqa_microprobe_expand_kv` uses local `repeat_interleave` on the head axis (no fabricated
> `torch.nn.functional.repeat_kv`); D2 the microprobe allocates Q/K/V explicitly on each
> `cuda:<index>`, synchronizes the device after SDPA, records/verifies per-device evidence
> (exact geometry 40/8/8 → 40/40/40, FP16, {FLASH,EFFICIENT} only, MATH excluded), and
> `all_passed` only when every visible device passes finite+shape+device; D3
> `pilot-repo-preflight-cell` restored to a 210-element newline-preserving source (was a
> 172-element all-comment no-op) that `compile("".join(source), …)` succeeds on and whose AST
> carries executable microprobe + fail-closed `raise` + `_run_tee` nodes; D4 `_run_tee`
> enforces its deadline WHILE the child runs (terminate→kill→reap, bounded tail); D5 em-dash
> mojibake restored (0 mojibake in canonical + bundled); D6 export rebuilt only after final
> commit/push + fresh-extraction verified (empty git status, extracted HEAD == report HEAD, origin
> ref == HEAD, artifact + sidecar match, trust freeze tracked & byte-identical) — **truthful status:
> local export verified, but push/origin parity (`origin ref == HEAD`) and the definitive post-push
> export remain PENDING until this branch is pushed.** Frozen scientific
> contract UNCHANGED (model Qwen2.5-Coder-14B-Instruct, BNB-NF4, sdpa, kernel policy
> `flash_or_efficient_no_math`, GQA compat `repeat_kv_sm75`, 12 scenarios / 3 pins / 2 strategies /
> 2 reps = 48 cells, prompts, Ground Truth, metrics, --timeout 600, --validation-timeout 1800,
> max attempts 3, completion cap 4096, 12000/64 gate). Full suite **2441 passed / 33 skipped /
> 0 failed**; exact final-artifact dry-run **48/48** (48 unique IDs, repos 16/16/16, strategies
> 24/24, reps 24/24, 0 model calls/tokens, every record source commit == `f72ecda…`). Exact
> artifact `dist/pilot-kaggle-upload.zip` SHA-256
> `ce40b33019feba58d8cabeef2244a765e157cdba4288a9d9ea2eb186de46a24d` (+ sidecar verified) built from
> source commit `f72ecda0e7dac10e81dae34daa6bb1610c94b9ee` (trust/provenance 0 mismatches, FROZEN;
> supersedes `de0c5bd…`/`bfbc935f…`). NO stable tag yet: real 2x T4 Kaggle model preflight (repo
> preflight + heartbeat, Qwen 14B BNB-NF4 load, GQA microprobe, short + 12k probe) MUST PASS →
> then `v0.9.22-pilot-exec-ready`; if it fails, return to the SAME v0.9.22 task. Report:
> `reports/V0922_GQA_MICROPROBE_NOTEBOOK_EXPORT_INTEGRITY_CLOSURE_REPORT.md`.
> **Authoritative snapshot: `docs/AI_ACCOUNT_TRANSFER_HANDOFF.md`.**
>
> **PRIOR STATE (2026-08-24, HISTORICAL): v0.9.22 long-context attention memory closure — branch
> `fix/pilot-v0922-long-context-attention-memory-closure` on clean main
> `58d1be533c98ca9bafc9a344f2a73f8a140b9540` (v0.9.21 reconciled), superseded by the candidate above:**
> the real Kaggle v0.9.21 model preflight PASSED repository preflight / dependencies / Qwen 14B
> BNB-NF4 load (`qwen_model_load[bnb-nf4]: PASS`) / GPU-only device map / 2x Tesla T4 / per-GPU
> headroom (min free 7.764 GiB) / short probe, then FAILED at the long-context probe with CUDA OOM:
> 12,044 prompt tokens / 64-token output budget / **failed allocation 21.62 GiB == exactly
> `12044*12044*40*4 bytes = 21.6153 GiB`, the full float32 40-head quadratic attention score matrix**
> — the effective runtime attention path materialized the math/eager fallback during prompt prefill.
> v0.9.21 Real Pilot REJECTED BEFORE LAUNCH (no Experiment ID / no RunRecord; no stable tag moved).
> That candidate closed it WITHOUT touching any scientific input: Task A explicit
> `attn_implementation="sdpa"`; Task B fail-closed CUDA generation inside
> `sdpa_kernel([FLASH_ATTENTION, EFFICIENT_ATTENTION])`; Task C canonical attention evidence
> + fail-closed `attention_policy` check + launch authorization enforcement; Task D corrected
> OOM diagnosis; Tasks E/F regression guards. RED/GREEN proven (12 backend + 18 preflight
> contract tests failed against v0.9.21); full suite 2407 passed / 33 skipped / 0 failed;
> dry-run pilot 48/48.
> Report: `reports/V0922_LONG_CONTEXT_ATTENTION_MEMORY_CLOSURE_REPORT.md`.
>
> **PRIOR STATE (2026-08-24, HISTORICAL): accepted release = `v0.9.21-pilot-exec-ready`** @ annotated tag
> peel == artifact source commit == merge `e308047c9c05f38316d80ce565bac1b51d105bfa`; archive
> `dist/pilot-kaggle-upload.zip` SHA-256 `62e377467e225d336cbcaa70a2c610b5080e329e1a4e6578fbcbdc1af7dbee40`;
> trust/provenance 0 mismatches; dry-run 48/48; target-shaped Gates 1-3 + complete no-model preflight GREEN on the
> released source state (CI runs 32692489617 / 32694137255). v0.9.20 was NOT accepted for Real Pilot launch: the
> independent audit found B1 (per-cell validation routed every repository through sys.executable), B2 (frozen
> validation env discarded by FunctionalValidator) and B3 (hardcoded 180s validation timeout below the measured
> 941.42s Saleor runtime); v0.9.21 closes all three with --validation-python mappings, frozen-env propagation and
> explicit --validation-timeout 1800 on launch+resume — these repository/per-cell fixes remain VALID and are
> carried forward into v0.9.22.
> Report: `reports/V0921_PER_CELL_VALIDATION_RUNTIME_CLOSURE_REPORT.md`.
> **Authoritative snapshot: `docs/AI_ACCOUNT_TRANSFER_HANDOFF.md`.**
>
> **PRIOR STATE (2026-08-24 earlier in the day, HISTORICAL):** the
> real Kaggle v0.9.19 run FAILED at the Saleor fast capability gate (Pytest
> exit 5 = no tests collected; all earlier stages PASS) —
> **`v0.9.19-pilot-exec-ready` REJECTED FOR PILOT LAUNCH**. Root cause = gate
> argv concatenated a second `-m pytest` onto the resolved primary command;
> local tests false-green via substring mock. Fix + exact-argv regression tests
> + evidence-backed Saleor baseline-flake policy + target-shaped CI preflight
> gate complete and RELEASED as **`v0.9.20-pilot-exec-ready`** @ annotated tag
> peel == artifact source commit == merge `febda7938db1284da4090d35e980db472149c3ad`;
> archive `dist/pilot-kaggle-upload.zip` SHA-256
> `56b1c2a9019a03892ce627321b9a415795ac95836ac415694bbc0995263c8024`; trust/
> provenance 0 mismatches; dry-run 48/48; target-shaped no-model preflight GREEN
> on the released source state (CI run 32676588800). HISTORICAL next action at
> that time (SUPERSEDED — first by v0.9.21, now by the v0.9.22 attention closure
> candidate): fresh Kaggle v0.9.20 target preflight with that artifact.
> Report: `reports/V0920_ROOT_CAUSE_CLOSURE_REPORT.md`.
> **Authoritative snapshot: `docs/AI_ACCOUNT_TRANSFER_HANDOFF.md`.**
>
> **PRIOR STATE (2026-08-22, HISTORICAL for launch purposes):** accepted release = **`v0.9.19-pilot-exec-ready`**
> @ tag peel == artifact source commit `2305991442a4f965d44bb066bb00c0a459fc395a`;
> `main` is a post-tag docs/evidence child of that merge; v0.9.19 artifact
> trust/provenance GREEN (archive `f7a16858…`); OpenCode full suite at that
> state = 2330 passed / 34 skipped / 0 failed.
> The dated "Handoff type" entries and older sections below are a
> chronological HISTORICAL trail (each superseded by the next); they are kept
> for traceability only.

**Handoff Date:** 2026-08-17
**Prepared by:** OpenCode (engineering assistant)
**Handoff to:** Human researcher (subsequent sessions)
**Handoff type:** **PILOT-EXEC-01 AUDIT DELTA + v0.9.13 ANCHOR ALIGNMENT (2026-08-17): branch `fix/pilot-target-preflight-closure` from clean `origin/main` `b174be1`; audit-delta fix `e71782c`, freeze `1fd3a54`.** Independent audit found `_collect_saleor_failure_diagnostics()` called `_run_lastfailed_serial()` unconditionally — if `.pytest_cache/v/cache/lastfailed` is missing/empty/malformed, `pytest --lf -n 0` has no selection constraint and risks becoming a full serial Saleor suite. FIX (minimal): load `lastfailed` first; only execute `pytest --lf -n 0 -x -vv --tb=long` when `lastfailed is not None AND len(nodeids) > 0`; missing/empty/malformed caches record `SKIPPED_NO_LASTFAILED` with `failed_count=0` and `lastfailed_serial_command=None`. Primary FAIL verdict never flipped. Companion fix: `_run_command` TimeoutExpired handler now preserves both `output` and `stderr` when both are present (evidence-quality hardening). Permanent Stop/Blocker Reporting Contract added to root `AGENTS.md`. Anchor alignment: `FROZEN_SOURCE_TAG` updated from `v0.9.12-pilot-exec-ready` to `v0.9.13-pilot-exec-ready` in notebook + all four test constants. No scientific inputs changed. Targeted gates: unit 22/22, integration 14/14, deployment bundle 60/60 (1 skipped), notebook contract 45/45, repo-env provisioning 28/28, Gate 5 anchor alignment 1/1, release provenance 17/17. Full suite **2,276 passed / 34 skipped / 4 pre-existing failed** (all 4 in `test_scientific_smoke_v1_fixes.py` source-inspection tests, verified pre-existing on clean main). diff-check/ruff/mypy/compile clean. **Pilot = NOT STARTED.**
**Handoff type:** **PILOT-EXEC-01 RELEASE-PROVENANCE CLOSURE (2026-08-16): `v0.9.11-pilot-exec-ready` REJECTED FOR LAUNCH; `v0.9.12-pilot-exec-ready` SHIPPED WITH A FAIL-CLOSED `source_commit` GIT-TREE PROVENANCE GATE (branch `fix/pilot-release-provenance-closure` from clean `origin/main` `5cee179`; code/test commit `6cd2767`, freeze commit `7923b37`).** The v0.9.11 immutable tag peeled to merge commit `8801304`, whose notebook is the v0.9.10 notebook `d15d8683…`, while the deployed artifact carried the re-frozen notebook `85edbd33…` that landed only in the POST-tag re-freeze commit `b87aa49` — the embedded notebook trust could be made internally self-consistent, yet the tag does not contain the deployed notebook. v0.9.11 is therefore documented as `internally-valid artifact, but rejected for launch because the immutable tag does not contain the deployed re-frozen notebook and therefore cannot reproduce the claimed source snapshot.` FIX (minimal): a fail-closed `validate_source_commit_provenance(*, source_commit, bundled_root, …, git_reader=None)` gate in `scripts/build_pilot_upload_bundle.py` proves the bundled Pilot notebook AND every `code_manifest.json` entry equal the normalized (CRLF→LF for text suffixes) tracked Git blob at `identity.source_commit`; it is a standalone release acceptance step run BEFORE the immutable tag is created, never falls back to the working tree, and has no skip flag. It is deliberately NOT wired into `build_pilot_bundle`/`freeze()` because the finalizer's validation rebuild runs before the re-frozen notebook + constants are committed. Companion byte-faithfulness fix: bundled `*.lock` files are LF-normalized in the code bundle (`_normalize_lock_files`) — on a `core.autocrlf=true` Windows checkout the two `requirements-*-kaggle.lock` files were bundled CRLF (manifest `95ad3b2b…` vs LF blob `1f4b1875…`). New suite `tests/integration/test_pilot_release_provenance.py` (Gates 1–5): exact v0.9.11 forensic RED regression from real git blobs (`8801304` vs `b87aa49`; internally-consistent identity PASSES embedded trust while the provenance gate FAILS), notebook CRLF/LF parity PASS, code-manifest modified/missing FAIL naming exact paths, invalid SHA / unknown commit fail closed, `.lock` LF-faithful entry PASS vs CRLF entry FAIL, and the v0.9.12 release-tag sequencing contract (notebook `FROZEN_SOURCE_TAG` == `PILOT_SOURCE_TAG` == `EXPECTED_FROZEN_SOURCE_TAG` == `SOURCE_TAG` == `v0.9.12-pilot-exec-ready`). Finalizer re-freeze `--source-tag v0.9.12-pilot-exec-ready`: code manifest `0fd86fc9…` (94/94 entries source-faithful incl. both locks), data `8b859ecc…`, repository snapshot `49d91d39…`, transport path map `07036a36…`; archive SHA-256 `5a7d7e0af7bd…` (merge re-freeze; sidecar matches). Full suite **2,255 passed / 33 skipped / 0 failed** (2026-08-16). **Pilot = NOT STARTED.**
**Handoff type (REJECTED FOR LAUNCH — superseded by the 2026-08-16 v0.9.12 release-provenance closure; internally-valid artifact but the immutable tag does not contain the deployed re-frozen notebook):** **PILOT-EXEC-01 SALEOR SOURCE-VISIBILITY HEALTH-PROBE FIX (2026-08-16): CLOSED AND FROZEN AT `v0.9.11-pilot-exec-ready` — MERGED TO MAIN `8801304` + ANNOTATED TAG ON THE MERGE COMMIT + FINALIZER RE-FREEZE `b87aa49` + FINAL ARTIFACT TRUST GATE PASS + 48-CELL DRY-RUN 48/48 (feature branch `fix/pilot-saleor-source-visibility-probe`: code/test `ee3d88b`, docs `228b2e8`).** Real Kaggle v0.9.10 PASSED every preflight stage (release trust, transport restore, runtime lock, repository snapshots, PostgreSQL TCP proof, Redis fallback, uv tool, django CMS no-pip env + health probe, Saleor copy, Saleor 3.12 `.venv`, `uv sync --locked`) and then failed ONLY at the new health probe: `import saleor` exit 1, `ModuleNotFoundError: No module named 'saleor'`. Root cause: the pinned Saleor `pyproject.toml` sets `[tool.uv] package = false` (upstream, immutable), so uv installs the locked dependencies but never the root project into site-packages; the v0.9.10 probe ran `<saleor .venv>/bin/python -c "import saleor"` without `cwd=the Saleor working copy`, while the frozen downstream preflight already runs Saleor commands with `cwd = pristine staged repository root`. Fix (minimal): `_import_probe` gained optional `cwd`; `_saleor_probe` always probes from `work_dir`; BOTH call sites fixed (marker/reuse + post-sync). NO `package=true`, NO pip/uv editable install, NO global `PYTHONPATH`; `uv sync --locked` / Python 3.12 / `UV_PYTHON_DOWNLOADS=never` preserved. Strong tests: real-subprocess source-visibility regression (RED vs old helper), `_FakeRunner` cwd assertion (the exact local-pass gap), pinned `package=false` contract, fresh/reuse provisioning cwd topology, missing-source fail-closed, downstream preflight parity, no semantic drift. Targeted integration 188 passed; full suite **2,239 passed / 33 skipped / 0 failed** (2026-08-16). v0.9.10 remains immutable (real Kaggle preflight reached the Saleor post-sync health probe then failed because the probe did not run from the repository root). **ALL SUBSEQUENT STEPS COMPLETE:** independent audit PASS → non-ff merge to main `8801304d855fe29c694f2a3c0500f661685b0d72` (merge SHA == main HEAD == tag peel) → release-trust-gate finalizer re-freeze (`--source-commit` = merge SHA, `--source-tag v0.9.11-pilot-exec-ready`, `--created-utc "2026-08-16T12:00:00+00:00"`; code manifest `7e86eb5dd651…`, data `8b859ecc7216…`, repository snapshot `49d91d39435f…`, transport map `07036a36cd97…` — last three byte-identical to v0.9.10) → FINAL ARTIFACT TRUST GATE **Notebook == Identity == Actual 4/4** (deployed notebook `85edbd33e81b…`, archive SHA-256 `039818bde60edcc9693ca88f779c7987bde818ddbfbca705426747b08c6d5453`) → immutable annotated tag `v0.9.11-pilot-exec-ready` created on the merge commit and pushed (peels to `8801304d855fe29c694f2a3c0500f661685b0d72`) → bundled 48-cell mock dry-run **48/48** (todo 16 / djangocms 16 / saleor 16; iterative_repository_agent 24 / selective 24; rep1 24 / rep2 24; 48 unique / 0 missing / 0 duplicate / 0 model calls) → **STOP. Pilot = NOT STARTED.**
**Handoff type (HISTORICAL — superseded by the 2026-08-16 Saleor source-visibility fix):** **PILOT-EXEC-01 RELEASE TRUST GATE CLOSED AND FROZEN AT `v0.9.10-pilot-exec-ready` (2026-08-15): MERGED TO MAIN + TAGGED + TAGGED REBUILD + FINAL ARTIFACT TRUST GATE PASS + 48-CELL DRY-RUN 48/48** — the deployment source is re-frozen at `v0.9.10-pilot-exec-ready` via a REAL two-pass deterministic release-trust-gate finalizer run against the LOCAL repo cache (`dist/pilot-repo-cache`, NO `--allow-acquire`, no network acquisition): `python scripts/finalize_pilot_notebook_trust.py --source-commit 80d4d6e581cef60463efde31b414643ba182f35a --source-tag v0.9.10-pilot-exec-ready --repo-cache dist/pilot-repo-cache --created-utc "2026-08-15T14:00:00+00:00"`. Both pinned repo cat-file checks PASS (django CMS `0f633fc9…`, Saleor `e11a5557…`) and `git archive` works in both cache dirs. **Notebook == Identity == Actual proven 4/4** for the four frozen manifest/map hashes: code `bb976f67fefe…` (the v0.9.9 recorded `99688e4e` was stale — it predated the bundled helper-script additions and was never validated against the build; the new gate freezes the true value), data `8b859ecc7216…`, repository snapshot `49d91d39435f…`, transport path map `07036a36cd97…` (the last three byte-identical to v0.9.9); deployed notebook SHA-256 `d15d86831bf8…` == bundled archive bytes, normalized bundled notebook == source `873e97735cd2…`. **No scientific inputs changed** (scenarios, prompts, metrics, model, quantization, timeout 600, repair budget, repository pins, validation scope). Freeze evidence `reports/pilot_notebook_trust_freeze.json` tracked; validation-rebuild archive SHA-256 `dd5ee529e3a0…`. Gates: targeted trust-gate closures 142/142 (deployment bundle 52/52, notebook contract 46/46, repo-env provisioning 24/24, real-launch preflight 13/13), full suite **2,234 passed / 33 skipped / 0 failed**, diff-check/ruff/mypy/compile clean. **ALL SUBSEQUENT STEPS COMPLETE:** independent audit PASS → non-ff merge to main `44e9a1f…` → tagged rebuild (`--source-commit` = merge SHA `44e9a1f…`, SAME `--created-utc "2026-08-15T14:00:00+00:00"`) → **FINAL ARTIFACT TRUST GATE PASS** (Notebook == Identity == Actual 4/4) → annotated tag `v0.9.10-pilot-exec-ready` created on the merge commit and pushed (peels to `44e9a1f…`; main HEAD) → exact 48-cell bundled dry-run on the tagged rebuild **48/48 terminal / 48 succeeded / 0 failed / 0 pending / 48 unique run IDs** (per-repo 16/16/16; per-strategy 24/24; per-rep 24/24; 0 model calls). Tagged-rebuild archive SHA-256 `9df1396d50a9…` (sidecar matches). **Pilot = NOT STARTED** — real launch deferred until the user confirms the Kaggle mounted model path and HF results repository ID.
**Handoff type (HISTORICAL — superseded by the 2026-08-15 v0.9.10 release trust gate closure):** **PILOT-EXEC-01 KAGGLE REPO-ENV PROVISIONING CLOSURE (2026-08-15) ON BRANCH `fix/pilot-kaggle-env-provisioning-closure` (COMMIT `28f0405`), FULL SUITE GREEN — MERGE + TAG `v0.9.9-pilot-exec-ready` PENDING** — the real Kaggle `pilot-repo-preflight-cell` blocker closed: `python -m venv /kaggle/working/pilot_envs/djangocms` -> `/kaggle/working/pilot_envs/djangocms/bin/python3 -m ensurepip --upgrade --default-pip` returned non-zero exit status 1 in ~0.24 s (NOT a hang). The runtime lock installs pip into the base interpreter on Kaggle, so `venv`+`ensurepip` cannot build a working pip inside a fresh env. The bundled helper `scripts/pilot_kaggle_repo_envs.py` (new, stdlib-only) provisions every repository validation env WITHOUT the ensurepip path: stdlib venv uses `--without-pip` everywhere; HOST pip (`<benchmark-python> -m pip --python <target>`) bootstraps the no-pip tool/target envs (documented pip 22.3+ feature for pip-less envs); dedicated no-pip `pilot_envs/tools` env gets `uv` via host pip `--python`; django CMS deps installed with `uv pip install -r test_requirements/django-5.0.txt` from the frozen snapshot root (SHA-256 recorded); Saleor = copy of pinned snapshot into `pilot_envs/saleor`, then `uv venv .venv --python <existing 3.12>` with `UV_PYTHON_DOWNLOADS=never` (no silent download/switch) then `uv sync --locked`. Completion markers (`.pilot_env_ready.json`, schema `pilot_repo_environment.v1`) + health probes (django `5.0.*` + `import cms`, `import saleor`, `uv --version`) drive reuse; ONLY the specific invalid private env dir is rebuilt (`_remove_private_env`), never arbitrary `/kaggle/working`. Upstream OS prerequisites `gettext` + `gcc` + `libpq-dev` (ALL mandatory) install in ONE `apt-get install` transaction (fail closed listing ALL missing when apt unavailable or still missing after install; the Redis `valkey-server`/`redis-server` alternatives bug is never reintroduced). Visible START/END/elapsed output + 30 s heartbeat threads; provisioning log `preflight/environment_provisioning.log` redacts `HF_TOKEN=`/`SECRET_KEY=`/`PGPASSWORD=` secrets. The notebook `pilot-repo-preflight-cell` is now a thin adapter: `_assert_service_port` on 5433/6379, `importlib.util` load of the bundled helper, `provision_repository_envs(...)`, then the shared `scripts/pilot_repo_snapshot.py preflight` with todo=`sys.executable` + the provisioned djangocms/saleor interpreters. `scripts/build_pilot_upload_bundle.py` ships the helper at `code/scripts/pilot_kaggle_repo_envs.py` (byte-equal normalized + hashed in `code_manifest.json`). **No scientific inputs changed** (scenarios, prompts, metrics, model, quantization, timeout 600, repair budget, repository pins, validation scope). New regression matrix `tests/integration/test_pilot_repo_env_provisioning.py` (24 tests, Gates B/C/D/E/G/J/K + end-to-end) all green; notebook contract (+ thin-adapter static test) and deployment bundle contract (+ helper-shipped test) updated. Gates: provisioning 24/24, notebook contract 46/46, service bootstrap 41/41, real-launch preflight 13/13, deployment bundle 52/52, full suite **2,225 passed / 33 skipped / 0 failed**, diff-check/ruff/mypy/compile clean. `dist/pilot-kaggle-upload.zip` + `.sha256` rebuilt from the exact tag `v0.9.9-pilot-exec-ready` after merge. **Pilot = NOT STARTED**; real launch still deferred until the user confirms the actual Kaggle mounted model path and HF results repository ID.
**Handoff type (HISTORICAL — superseded by the 2026-08-15 repo-env provisioning closure):** **PILOT-EXEC-01 KAGGLE-REDIS-PACKAGE-FALLBACK MERGED TO MAIN + TAGGED `v0.9.8-pilot-exec-ready` (2026-08-15) via non-fast-forward merge of branch `fix/pilot-kaggle-redis-package-fallback`** — the final real Kaggle preflight blocker closed: the v0.9.7 cell ran `apt-get install -y valkey-server redis-server`, which aborts the WHOLE apt transaction with `E: Unable to locate package valkey-server` because the real Kaggle Ubuntu (Jammy-shaped) runtime exposes `redis-server` in its configured apt repositories but NOT `valkey-server`. The `service-bootstrap-cell` now provisions the Redis-compatible server binary-first, refreshes apt metadata at most once per invocation (`_apt_update_once`), probes each alternative candidate individually via `apt-cache policy <name>` (`_apt_package_available`, argument-list only, no shell), installs EXACTLY ONE package per `apt-get install` (`_apt_install_one`), records UNAVAILABLE and failed candidates, and FAILS CLOSED with distro/runtime diagnostics when no candidate can be installed — there is NO pip client-package and NO in-process fake-server fallback. A selected-implementation label and a proven server `--version` are printed after start; the endpoint stays `127.0.0.1:6379` / `redis://127.0.0.1:6379/0`. **No scientific inputs changed** (scenarios, prompts, metrics, model, quantization, timeout 600, repair budget, repository pins, validation scope). New hermetic Gate-R contract in `tests/integration/test_pilot_service_bootstrap.py` (14 new tests: already-installed, MANDATORY Jammy-shaped valkey-unavailable→redis-only, reverse future-distro valkey-only, install-failure fallback, neither-available fail-closed, apt-get/apt-cache missing fail-closed, apt update-once, start/version service semantics, full-cell end-to-end PG+Redis green; full-cell executor `_exec_cell` runs the EXACT provisioning + prove section with per-port open flags + apt fakes); static notebook contract gains `test_redis_package_fallback_contract` (combined `"valkey-server redis-server"` string forbidden); notebook + `build_pilot_upload_bundle.py`/`finalize_pilot_notebook_trust.py` + deployment-bundle contract move to `FROZEN_SOURCE_TAG = "v0.9.8-pilot-exec-ready"`. Gates: service bootstrap 41/41, notebook contract 43/43, deployment bundle 51/51, full suite **2,199 passed / 33 skipped / 0 failed**, diff-check/ruff/mypy/compile clean. Tagged rebuild recreated `dist/pilot-kaggle-upload.zip` + `.sha256` (authoritative frozen upload artifacts — never manually re-zip). **Pilot = NOT STARTED**; real launch still deferred until the user confirms the actual Kaggle mounted model path and HF results repository ID.
**Handoff type (HISTORICAL — superseded by the 2026-08-15 Redis package-fallback correction):** **PILOT-EXEC-01 KAGGLE POSTGRES ROOT-FIX MERGED TO MAIN + TAGGED `v0.9.7-pilot-exec-ready` (2026-08-13) via non-fast-forward merge of branch `fix/pilot-kaggle-postgres-unprivileged-bootstrap` → tag `v0.9.7-pilot-exec-ready` → tagged rebuild** — the real Kaggle blocker closed: the Kaggle notebook process runs as root while PostgreSQL `initdb`/`pg_ctl` refuse root (`initdb: error: cannot be run as root`), which blocked the v0.9.6 service bootstrap. The `service-bootstrap-cell` now resolves the package-native unprivileged `postgres` OS account when the notebook effective uid is 0 and runs the PostgreSQL server lifecycle (initdb, pg_ctl and the postgres server it launches) under that account via `subprocess.run(..., user=...)` (POSIX-only, checked, fail-closed; no `runuser`, no `shell=True`); FAILS CLOSED before initdb when the account is missing and NEVER falls back to root; non-root notebook processes keep the direct path. Ownership/log preparation is limited to the private service paths (data dir `0o700`, log `0o600`, chown to the postgres uid/gid; incomplete previous clusters safely recreated, ONLY `PG_DATA_DIR`). The frozen TCP client probe (psql) still runs from the notebook process against `127.0.0.1:5433 saleor/saleor/saleor`; Valkey/Redis `127.0.0.1:6379` unchanged. **No scientific inputs changed** (scenarios, prompts, metrics, model, quantization, timeout 600, repair budget, repository pins, validation scope; the four frozen manifest hashes stay byte-identical). New hermetic Gate-H contract `tests/integration/test_pilot_service_bootstrap.py` (28 tests) execs the EXACT cell definitions with os/pwd/subprocess/socket fakes (Gates B/C/D/E/F/H); notebook contract gains 2 root-safe static tests and moves to `FROZEN_SOURCE_TAG = "v0.9.7-pilot-exec-ready"`; deployment bundle contract + `build_pilot_upload_bundle.py`/`finalize_pilot_notebook_trust.py` defaults updated to v0.9.7. Gates: service bootstrap 28/28, notebook contract 42/42, deployment bundle 51/51, real-launch preflight 13/13, full suite **2,185 passed / 33 skipped / 0 failed**, diff-check/ruff/mypy/compile clean. Tagged rebuild recreated `dist/pilot-kaggle-upload.zip` + `.sha256` (authoritative frozen upload artifacts — never manually re-zip). **Pilot = NOT STARTED.**
**Handoff type (HISTORICAL — superseded by the 2026-08-13 root-fix correction):** **PILOT-EXEC-01 KAGGLE RESERVED-NAME TRANSPORT CORRECTION MERGED TO MAIN + TAGGED `v0.9.5-pilot-exec-ready` (2026-08-13) via non-fast-forward merge of branch `fix/pilot-kaggle-reserved-transport-name` (commits `189cc60`, `99348d1`) → merge `eb07b7b` → tag `v0.9.5-pilot-exec-ready` (annotated object `b99fe9b9`) → tagged rebuild** — Kaggle rejected the v0.9.4 upload because the transport root `__kaggle_transport__` matches Kaggle's reserved `__name__` naming pattern (`^__.*__$`). The transport root is now `kaggle_transport` everywhere (`scripts/build_pilot_upload_bundle.py`, the notebook `transport-restore-cell`, the `kaggle_transport_path_map.json` exact-path map contract, tests, and runbook/contract docs). A MANDATORY pre-upload archive validator (`validate_archive_members_kaggle_ready`) now scans EVERY ZIP member and fails closed on any path component with characters outside `[A-Za-z0-9._-]` or matching `^__.*__$`; `is_kaggle_safe_name` also flags reserved-name components so reserved-name canonical files are transported like unsafe-special-char files. Canonical upstream filenames are NEVER renamed or deleted; the encoding is ZIP-only and fully reversible; round-trip restores EXACT original paths and bytes. **No scientific inputs changed** (scenarios, prompts, metrics, model, quantization, timeout 600, repair budget, repository pins, validation scope). Gates: targeted notebook + deployment transport contracts 61/61 (33 + 28, incl. 8 new reserved-name/validator cases), full suite **2,125 passed / 33 skipped / 0 failed**, diff-check/ruff/mypy/compile clean. Tagged rebuild (`--source-commit eb07b7b --source-tag v0.9.5-pilot-exec-ready --created-utc 2026-08-13T12:00:00+00:00`, real repo cache) verified byte-deterministic (two builds → archive SHA-256 **`7be899d1398b7e7061dd98d7d8d710482bfe3f1f66f1663be26dce7de7e0997a`**, sidecar `dist/pilot-kaggle-upload.zip.sha256` matches; 6396 members / 0 unsafe / 0 reserved-name / 50 transport blobs; roundtrip restore 50/50 exact paths/bytes; all five identity manifest hashes PASS; repo content hashes PASS; 48-cell bundled dry-run 48/48 unique / 0 failed; map SHA-256 `07036a36…` bound into identity). Authoritative upload artifact rebuilt from the exact tag: **`dist/pilot-kaggle-upload.zip` + `dist/pilot-kaggle-upload.zip.sha256`** (never manually re-zip; closure record carries the exact SHA). `v0.9.4-pilot-exec-ready` NOT moved. **Pilot = NOT STARTED.** Real launch deferred until the user confirms the actual Kaggle mounted model path and HF results repository ID.
**Handoff type (HISTORICAL — superseded by the 2026-08-13 reserved-name transport correction):** **PILOT-EXEC-01 KAGGLE FILENAME TRANSPORT CORRECTION MERGED TO MAIN + TAGGED `v0.9.4-pilot-exec-ready` (2026-08-13) on branch `fix/pilot-kaggle-filename-transport`** — the frozen Pilot archive `dist/pilot-kaggle-upload.zip` (v0.9.3) was rejected by Kaggle: 50 ZIP member names from the pinned upstream repos (45 Saleor, 5 django CMS) contain `[ ] & @ =`. A reversible transport encoding now makes the archive Kaggle-safe. `scripts/build_pilot_upload_bundle.py` restricts ZIP member names to `^[A-Za-z0-9._/-]+$`, stores every unsafe canonical repository file as `__kaggle_transport__/files/<content-hash-blob>`, and writes the exact-path map `__kaggle_transport__/kaggle_transport_path_map.json` (SHA-256 `a5c1e2cbae309b89c3268fa177a7cd68bcef285f5a483e4354ba54ef982b875e` bound into `pilot_deployment_identity.json` as `kaggle_transport_path_map_sha256`). The frozen Pilot notebook `notebooks/pilot_exec_01.ipynb` gained ONE fail-closed `transport-restore-cell` (now 18 cells; between archive verification and identity verification): it verifies the map hash against the identity, rejects traversal/drive/`..` destinations, destination collisions, missing blobs, and leftover blobs, restores the EXACT original paths and bytes, removes `__kaggle_transport__/`, and prints `PILOT KAGGLE TRANSPORT RESTORE: PASSED` BEFORE any manifest or repository verification. Canonical upstream filenames are NEVER renamed or deleted — the encoding is ZIP-only and fully reversible. **No scientific inputs changed** (scenarios, prompts, metrics, model, quantization, timeout 600, repair budget, repository pins, validation scope). Gates: notebook contract 28/28 (incl. 8 new transport-restore tests), deployment bundle contract 27/27 (incl. 13 new `TestPilotKaggleTransport` tests), full suite **2,119 passed / 33 skipped / 0 failed**, diff-check/ruff/mypy/compile clean. STEP 5 real bundle verified: 6396 members / **0 unsafe** / 50 transport blobs / roundtrip restore 50/50 / restored repo content hashes PASS / exact 48-cell bundled dry-run 48/48. Deployment archive rebuilt from the exact tag: **`dist/pilot-kaggle-upload.zip` + `dist/pilot-kaggle-upload.zip.sha256`** (authoritative frozen upload artifacts — never manually re-zip). **Pilot = NOT STARTED.** Next = exact Kaggle launch prep (upload zip + sidecar as ONE Dataset, attach Pilot notebook + Qwen 14B, Internet ON, HF_TOKEN) -> target preflight (transport restore + service bootstrap) -> real Pilot (only after all preflights pass). Real launch deferred until the user confirms the actual Kaggle mounted model path and HF results repository ID.
**Handoff type (HISTORICAL — superseded by the 2026-08-13 transport correction):** **PILOT-EXEC-01 KAGGLE SERVICE BOOTSTRAP LAST-MILE CORRECTION MERGED TO MAIN + TAGGED `v0.9.3-pilot-exec-ready` (2026-08-13) on branch `fix/pilot-kaggle-service-bootstrap`** — the frozen Pilot notebook `notebooks/pilot_exec_01.ipynb` gained ONE fail-closed, idempotent `service-bootstrap-cell` (between repository snapshot verification and the repo-specific preflight, BEFORE any repository validation and model load) that provisions the Saleor validation OS services on a fresh Kaggle session: PostgreSQL `127.0.0.1:5433` (role/db `saleor/saleor@saleor`, private data dir `/kaggle/working/pilot_services/postgres`, `pg_config --bindir` preferred) and Valkey/Redis `127.0.0.1:6379` (persistence disabled). Topology mirrors `benchmark_data/manifests/pilot_validation_commands.yaml`; OS installs non-interactive (apt-get; Kaggle Internet ON required — installs fail loudly offline); no benchmark/model Python environment modification; no secrets printed beyond the frozen non-secret test credentials. **No scientific inputs changed** (scenarios, prompts, metrics, model, quantization, timeout 600, repair budget, repository pins, validation scope). Gates: notebook contract 20/20 (incl. 5 new service-bootstrap tests), deployment bundle contract 14/14, targeted pilot gates 77/77, full suite **2,098 passed / 33 skipped / 0 failed**, diff-check/ruff/mypy/compile clean. Deployment archive rebuilt from the exact tag: **`dist/pilot-kaggle-upload.zip` + `dist/pilot-kaggle-upload.zip.sha256`** (authoritative frozen upload artifacts — never manually re-zip). Superseded because Kaggle rejected the v0.9.3 upload (50 unsafe ZIP member names) — see the transport correction above. **Pilot = NOT STARTED.**
**Handoff type (HISTORICAL — superseded by the 2026-08-13 service-bootstrap correction):** **PILOT-EXEC-01 REAL-LAUNCH CLOSURE GATES 9/10 COMPLETE (2026-08-13) on branch `fix/pilot-real-launch-closure` (from `main` @ `98863d0`)** — Gate 9 engineering preflight evidence ledger written (`reports/PILOT_EXEC_01_GATE9_ENGINEERING_PREFLIGHT_LEDGER.md`): saleor `TZ=UTC` frozen into `benchmark_data/manifests/pilot_validation_commands.yaml` (verified 2026-08-11; two `test_transaction_schema_time_valid` cases were drifting by the box UTC offset); remaining ~31-36 order/pricing saleor failures classified as an upstream nondeterministic fixture artifact (33 vs 38 observed), not a regression. Gate 10: `dist/pilot-kaggle-upload/` + `dist/pilot-kaggle-upload.zip` **rebuilt from the closure state** with the real repo cache (djangocms `0f633fc9…`, saleor `e11a5557…` git checkouts at pinned SHAs; todo embedded); notebook byte-matches `notebooks/pilot_exec_01.ipynb`; `notebook_manifest.json` non-empty + hash-verifies; all three repos materialized with pinned SHAs verified; `pilot_deployment_identity.json` frozen contract (`v0.9.2-pilot-exec-ready`); code/data/notebook/repository-snapshot manifest hashes match emitted bytes; archive contains notebook + three repos, no `.git`; deterministic rebuild byte-identical (archive SHA-256 `ecb7ea7c85d8bdc527a0384f141b47a1e84ee0b3c3f12b6b8305d880098015f1`); fresh 48-cell bundled dry-run 48/48 unique / 0 missing / 0 duplicate (todo 16 / djangocms 16 / saleor 16; iterative_repository_agent 24 / selective 24; rep1 24 / rep2 24); targeted gates 67/67 passed; diff-check/ruff/mypy/compile clean. **Pilot = NOT STARTED.** Real launch still deferred until the user confirms the actual Kaggle mounted model path and HF results repository ID.
**Handoff type (HISTORICAL — superseded by the 2026-08-13 closure):** **PILOT-EXEC-01 PRE-EXECUTION GATES IN PROGRESS (2026-08-10) on branch `experiment/pilot-exec-01` (from `main` @ `72d041d`)** — Pilot-specific deployment bundle + pre-registration prepared. New `scripts/build_pilot_upload_bundle.py` (reuses the historical builder, redirects output to `dist/pilot-kaggle-upload/`, omits the Smoke notebook, deterministic zip, writes `pilot_deployment_identity.json`; refuses output root == `kaggle_upload`) + new 12-test contract `tests/integration/test_pilot_deployment_bundle.py` (12/12 passed; historical Smoke bundle byte-identical). Gate A5: exact fresh 48-cell bundled dry-run 48/48 (todo 16 / djangocms 16 / saleor 16; iterative_repository_agent 24 / selective 24; rep1 24 / rep2 24). Gate A6: full suite **2,038 passed / 33 skipped / 0 failed** (750.99s); diff-check/ruff/mypy/compile clean. Gate B: execution contract **pre-registered** before any real Pilot model result (`docs/PILOT_EXEC_01_EXECUTION_CONTRACT.md`; DECISION_LOG D025) — frozen 48-cell matrix, Qwen2.5-Coder-14B-Instruct / bnb-nf4 / temp 0 / 600s / max 3 attempts / 4096 completion tokens/call / cap 0; runbook `docs/PILOT_KAGGLE_RUNBOOK.md` created; `docs/KAGGLE_EXECUTION_GUIDE.md` Pilot instructions corrected (explicit `--qwen-quantization bnb-nf4`, no `--max-runs 2`, Pilot bundle slug guidance). **Pilot = NOT STARTED.** Remaining: commit (deployment + docs) -> push -> independent pre-execution audit -> merge to main -> push -> tag `v0.9.1-pilot-exec-ready` (do NOT move `v0.9.0-pilot-ready`) -> rebuild bundle from tagged source -> verify -> `reports/PILOT_EXEC_01_DEPLOYMENT_FREEZE.md` -> exact Kaggle launch prep -> final report. Real launch deferred until the user confirms the actual Kaggle mounted model path and HF results repository ID.
**Handoff type:** **HANDOFF-CONSISTENCY-01 DOCS RECONCILIATION CLOSED (2026-08-09), merged to main `403977b`** — the 8 authoritative docs (README, SYSTEM_STATE, TODO, MASTER_IMPLEMENTATION_PLAN, PROJECT_HANDOFF, START_HERE, PROJECT_HEALTH_REPORT, latest_phase_report) were reconciled to a single current-state truth (Smoke V2 accepted, MAIN-GREEN-01 closed, full suite 1,958/33/0/0 carried forward, preferred recovery tag now `v0.8.2-smoke-v2-complete` at main `403977b`) and the docs-only closure was committed (`75f90cb` on `docs/handoff-consistency`), non-fast-forward merged to main, and pushed (local `main` == `origin/main` == `403977b`). **Docs-only closure: no code, tests, or scientific inputs changed; no full-suite rerun required (carried forward).** **Next = `PILOT-READY-01`; Pilot NOT started; no further Smoke Full-9 authorized.**
**Handoff type:** **MAIN-GREEN-01 POST-MERGE TEST-ISOLATION AND REPRODUCIBILITY HOTFIX COMPLETE (2026-08-09) on branch `fix/main-green-test-isolation` (commit A `34b9fc7` `fix(test): make Smoke-v2 integration state-independent`, pushed, local = remote)** — the post-merge full-suite regression (12 failed / 4 errors on the Windows `core.autocrlf=true` working tree) is **FIXED AND CLOSED**: full suite **1,958 passed / 33 skipped / 0 failed / 0 errors**. NOT a scientific or merge regression (merge-tree proof: `193d889^{tree}` == `65f9fb8^{tree}` == `fdd72f6…`; `git diff 65f9fb8..193d889` empty). Root causes: (A) bundle evaluator assets `kaggle_upload/code/tests/evaluator_assets/todo_smoke_*_checks.py` checked out CRLF → fingerprint mismatch; (B) `benchmark_data/repositories/todo/**` checked out CRLF → preserve-files rejected as `out_of_scope_change` (backend reads LF, executor writes LF) → cells failed before migration generation → sequential isolation "expected exactly one new migration, got ()"; (C) `__pycache__/*.pyc` residue inside baseline comparisons. Fix: `.gitattributes` `text eol=lf` pins for the three path groups + LF renormalization (zero CRLF remain; zero blob changes) + ephemeral-baseline predicate in `tests/support/evaluator_fixture_workspaces.py` (`_EPHEMERAL_BASELINE_MARKERS`), `_baseline_hashes()` ephemeral skip, and new T1/T2/T3 unit tests. **Zero scientific drift** — no production `src/` code, prompts, datasets, strategies, metrics, model identity, or timeout changes. Repeatability: T4 representative cell twice PASS; T5 sequential isolation twice PASS; T6 fingerprint PASS; T7 affected subset twice PASS (production-path 45, todo assets 53+1 skipped, kaggle bundle 51); T8 related regression 380 passed / 22 skipped; T9 full suite green once; static gates clean; dry-run pipeline 8/8 clean. **Next = `PILOT-READY-01`; Pilot NOT started.** After this docs commit: independent-style audit, non-ff merge `merge(fix): close Smoke-v2 test-isolation reproducibility defect`, new annotated tag `v0.8.1-smoke-v2-complete` (peeled == new main HEAD); `v0.8.0-smoke-v2-complete` unchanged (immutable provenance at `193d889`). Sentinel: `MAIN_GREEN_01_CLOSURE_AUDIT_REQUIRED`.
**Handoff type:** **SCIENTIFIC SMOKE V2 COMPLETE AND ACCEPTED (SMOKE-V2-CLOSE-01, 2026-08-09) on branch fix/kaggle-smoke-v2-model-output-closure** — the 600-second confirmatory timeout-sensitivity Full-9 (**T600**, contract FULL9-T600-01) was **EXECUTED AND ACCEPTED**: run `exp-20260808-222843`, uniform `--timeout 600` on the frozen runtime source/build `7f2a450`, fail-closed output namespace `/kaggle/working/runs/qwen14b_bnb_nf4_full9_scientific_smoke_wsfix_7f2a450_t600`, evidence prefix `corrected-full9-t600-wsfix-7f2a450-`; result **9/9 terminal / 2 successes / 7 scientific failures / 0 engineering blockers / 0 budget-exhausted / 63 model calls / 77,929 tokens / max run ≈373 s / Full-9 verification PASS / HF synchronization PASS** — the **same 2/9 result** as the accepted clean 300-second baseline (runtime `7f2a450`, `--timeout 300`, valid and preserved, NOT invalidated or replaced). **Timeout sensitivity confirmed: the 600-second ceiling did NOT change the accepted result; the 300-second baseline signal was not distorted by timeout censoring. This is NOT an improvement claim.** The uniform per-run workflow timeout is now frozen at **600s** for monolithic / selective / iterative_repository_agent (one shared Full-9 command; no strategy receives extra time); do NOT raise the timeout above 600 (analyze duration/repair distribution and pre-register the Pilot budget if Pilot runs again accumulate near 600 s). Executable validation recorded: final executable full suite **1947 passed / 33 skipped / 0 failed**; Pipeline Smoke PASS (T600 command + fail-closed `_t600` namespace contract); Dry Run PASS (exact 3x3 no-model/bundled dry-run contract with scientific timeout 600); Dataset/Prompt/Metric PASS carried-forward (zero drift); audit = implementation PASS / over-engineering PASS / scientific identity PASS (runtime source/build remains frozen `7f2a450`); non-destructive RED proof recorded (committed HEAD notebook with `--timeout 300` FAILS the new 600-second contract). **HISTORICAL (all completed — SMOKE-V2-CLOSE-01 is CLOSED):** at that time the task was to close Scientific Smoke V2 permanently (update all authoritative docs to the accepted state, audit the closure, commit/push proving local = remote, non-fast-forward merge to main, create/push stable tag `v0.8.0-smoke-v2-complete`, leave repo ready for `PILOT-READY-01` without starting Pilot); the next authorized action was an independent delta audit of that closure, then main merge + stable tag, then `PILOT-READY-01` — **all now executed: closure audited and merged (`193d889`), stable tag `v0.8.0-smoke-v2-complete` created, MAIN-GREEN-01 merged (`d875c72`), preferred recovery tag `v0.8.1-smoke-v2-complete`, next task `PILOT-READY-01` (Pilot NOT STARTED)**. No further Kaggle Full-9 is authorized; the accepted T600 run is the final Smoke evidence. Sentinel: `SMOKE_V2_CLOSURE_AUDIT_REQUIRED`.
**Handoff type (HISTORICAL — superseded by SMOKE-V2-CLOSE-01 and MAIN-GREEN-01):** **FULL9-EXEC-01 CANONICAL CORRECTED FULL-9 NOTEBOOK EXECUTION CLOSURE COMPLETE (2026-08-08) on branch fix/kaggle-smoke-v2-model-output-closure (Commit A `c4aee03` `feat(kaggle): make corrected Full-9 notebook executable`, pushed, local = remote, tree clean; status COMPLETE — pending independent delta audit before Kaggle Full-9)** - the canonical Kaggle notebook is now the single, tested, fail-closed execution artifact for exactly one fresh corrected Full-9. Fixed the setup-cell bootstrap regression (undefined `MODEL_DIR` NameError; now `MODEL_CANDIDATES` initialized from `KNOWN_MODEL`, `MODEL_PATH` derived from it, `src_dir` guard + `sys.path.insert`, `SCRIPT_PATH.is_file()` guard); removed all stale execution routes (setup order = setup-cell -> install-lock-cell -> preflight-cell -> secrets-cell -> full9-execution-cell -> full9-verification-cell -> export-evidence-cell; no generic/canary/continuous cells). Latest Kaggle attempt truth: source/build `7f2a450`; runtime install/preflight PASS; a redundant corrected-source selective canary ran and succeeded - **that attempt is NOT a Full-9**; corrected Full-9 evidence remained **0/9** at that time (later executed and accepted as `exp-20260808-222843`); the evidence ZIP downloaded from that session must NOT be labeled accepted Full-9 evidence. Validation: full suite **1,947 passed / 33 skipped / 0 failed**; targeted notebook/CLI/bundle 137 passed; related production-path/isolation regression 45 + 33 passed / 1 skipped; notebook JSON parse OK; all canonical code cells compile; bundle rebuilt and verified; canonical/bundled notebook parity proven; zero data/prompt/metric/runtime drift. **HISTORICAL next action (superseded — the T600 corrected Full-9 was executed and accepted as `exp-20260808-222843`): independent delta audit of FULL9-EXEC-01; after acceptance, exactly one fresh corrected Full-9.** Main merge / stable tag / Pilot / fine-tune remain unauthorized (all since completed except Pilot). No Kaggle run was performed in this task. Sentinel: `FULL9_EXEC01_NOTEBOOK_EXECUTION_CLOSURE_AUDIT_REQUIRED`. **Bootstrap Runtime Contract (Bootstrap-Contract-1, added by FULL9-EXEC-01):** the notebook setup-cell must be self-contained and fail-closed in this exact order - (1) resolve and validate the repo root, (2) insert `src/` on `sys.path` only after the repo root is known, (3) derive every deployment path from `KAGGLE_DEPLOYMENT_PATHS` (single source of truth), (4) initialize model candidates from `KNOWN_MODEL` and derive `MODEL_PATH` from them (never a previously-deleted sibling name like `MODEL_DIR`), (5) guard `SCRIPT_PATH.is_file()`, and (6) never reference a variable before it is defined in the cell. Violations are caught by `test_full9_exec_01_setup_bootstrap_symbols_defined_before_use` and `test_full9_exec_01_setup_bootstrap_contract_preserved`. **Automatic gate-progression lessons (added by FULL9-EXEC-01):** the Auto-Gate-Progression Policy still applies - PASS is not a STOP; no Kaggle/Pilot/main-merge/tag/new-deps without the authorized next step; a redundant corrected-source canary is engineering evidence only, never a Full-9; the bundled notebook must be byte-reproduced by the bundle builder, never hand-edited, or the canonical/bundled parity gate fails. **FULL9-WS-02A LAUNCH-SAFETY DOCS/RUNBOOK CLOSURE COMPLETE (2026-08-08) on branch fix/kaggle-smoke-v2-model-output-closure (docs/runbook only; no runtime/test/data/prompt/metric/notebook/bundle change)** — the independent GPT-5.6 Sol audit ACCEPTED the runtime workspace-isolation fix (`7f2a450`, deployment re-pinned by `e29c017`) but blocked a new Full-9 because the canonical runbook still launched source/build `f7b1ebb` and its output directory did not fail closed on pre-existing records. The canonical runbook `docs/KAGGLE_QWEN14B_FULL9_SCIENTIFIC_SMOKE_RUNBOOK.md` now launches with SOURCE_COMMIT=`7f2a4509482dc7e62c2b243374592e9a88e2ff48` / DEPLOYED_BUILD_ID=`7f2a450`; setup order = setup-cell -> install-lock-cell -> preflight-cell -> secrets-cell -> Full-9; fresh output = `/kaggle/working/runs/qwen14b_bnb_nf4_full9_scientific_smoke_wsfix_7f2a450` with a fail-closed non-empty guard; initial command = no `--strategy` / `--max-runs` / `--auto-resume-hf`. Truth at that time (HISTORICAL): accepted selective canary `exp-20260807-131819`; first Full-9 `exp-20260807-205422` = RUN BUT REJECTED (workspace contamination); corrected fresh Full-9 = NOT YET RUN (later executed and accepted as `exp-20260808-222843`). **HISTORICAL next action (superseded): independent delta audit of this docs/runbook closure; only if accepted, run exactly one fresh corrected Full-9.** Main merge / stable tag / Pilot / fine-tune remain unauthorized (all since completed except Pilot). **FULL-9 WORKSPACE ISOLATION DEFECT CLOSED (2026-08-08) on branch fix/kaggle-smoke-v2-model-output-closure (HEAD `e29c017`, pushed, local = remote, tree clean)** — the real Kaggle Full-9 `exp-20260807-205422` (physically completed 9/9 under runtime source `f7b1ebb`) was REJECTED as a stable scientific matrix: raw result 2 succeeded / 7 failed, raw total 62 calls / 76,858 tokens; root cause = overlay source restaging leaked generated files across scenarios (`0004_task_priority` survived into 002 and produced `0005_remove_task_priority_task_deleted_at`; affected selective/agent 002 and 003); full-9 scientific acceptance = rejected, preserved as evidence only; fixed by an exact reset from the immutable snapshot before every matrix run (Commit A `7f2a450` `fix(smoke): reset workspace source before every matrix run` + Commit B `e29c017` `chore(deploy): repin isolated Full-9 Smoke bundle`, `SOURCE_COMMIT=7f2a4509482dc7e62c2b243374592e9a88e2ff48` / `DEPLOYED_BUILD_ID=7f2a450`); official pre-benchmark gate (pytest 8.4.2) green = 1,928 passed / 33 skipped / 0 failed; Dataset 161/1, Prompt 200/12, Pipeline Smoke 45 (incl. sequential regression), Dry Run 9/9/9/0 exit 0, Metric 187, ruff 0 new, mypy 0 new; isolated selective canary remains accepted; `v0.8.0-canary.1` unchanged; main merge NOT authorized at that time (NOW COMPLETE at `193d889`/`d875c72`); `v0.8.0-smoke-v2-complete` NOT created then (CREATED at `193d889`); Pilot NOT authorized at that time (now NOT STARTED); Kaggle NOT rerun; next (historical) = independent code audit, then ONE fresh Full-9 with corrected source/build `7f2a450`; record `selective_updates/records/FULL9-WORKSPACE-ISOLATION-DEFECT-2026-08-08.md`; sentinel `FULL9_WORKSPACE_ISOLATION_CLOSURE_AUDIT_REQUIRED`. **QWEN 14B SELECTIVE CANARY SUCCESS ACCEPTED AND RECORDED + MILESTONE TAG `v0.8.0-canary.1` CREATED AND PUSHED (2026-08-07) on branch fix/kaggle-smoke-v2-model-output-closure (documentation HEAD `5561f918`; milestone tag `v0.8.0-canary.1` annotated, NON-STABLE, points to `31a619857ce07eb09ab5e206fbc9dc792782c99c`)** — independent GPT-5.6 Thinking audit ACCEPTED SUCCESSFUL REAL CANARY; real 14B canary records = 1 succeeded / 0 failed; milestone tag `v0.8.0-canary.1` = created and pushed, annotated, NON-STABLE (first accepted real Qwen 14B NF4 selective-canary milestone); full 9-record Scientific Smoke V2 = NOT RUN at that time (HISTORICAL — subsequently executed and accepted as `exp-20260808-222843`); main merge = NOT YET (pending Full-9 audit) at that time (NOW COMPLETE at `193d889`/`d875c72`); stable Smoke tag `v0.8.0-smoke-v2-complete` = not yet created then (CREATED at `193d889`; preferred recovery `v0.8.1-smoke-v2-complete` at `d875c72`); Pilot = NOT AUTHORIZED (now NOT STARTED); next (historical) = one fresh Full-9 via `docs/KAGGLE_QWEN14B_FULL9_SCIENTIFIC_SMOKE_RUNBOOK.md`; record `selective_updates/records/QWEN14B-SELECTIVE-CANARY-SUCCESS-2026-08-07.md`; sentinel `QWEN14B_CANARY_SUCCESS_DOCUMENTED_FULL9_READY`. **Historical (2026-08-05) preparation header — QWEN 14B BNB-NF4 CANARY PREPARATION COMPLETE (2026-08-05) on branch fix/kaggle-smoke-v2-model-output-closure (Commit A `0ece665` `fix(model): add model-aware Qwen BNB quantization profiles` + Commit B `0a596b8` `chore(deploy): pin Qwen 14B NF4 selective-canary bundle`, pushed, local = remote, tree clean)** — model-aware identity `qwen:<checkpoint-basename>:<quantization>:cfg-<12hex>` replaces the frozen `qwen:1:int8` (blocks auto-resume cross-model contamination; the generic auto-resume cell had downloaded `exp-20260804-133016` because both 7B and attempted 14B were `qwen:1:int8`); explicit `bnb-nf4` profile (`load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True`, T4) with canonical modes `bnb-int8`/`bnb-nf4`/`fp16` via `--qwen-quantization`; prequantized non-bnb checkpoint fails fast (`PREQUANTIZED_CHECKPOINT_INCOMPATIBLE`) before model load, no fallback; GPTQ deferred — failed 14B GPTQ attempt `exp-20260804-195126` (0 records / 0 calls / 0 tokens, GPTQConfig + BitsAndBytesConfig conflict) preserved as engineering evidence; notebook pinned to unquantized `14b-instruct/1`, `QWEN_QUANTIZATION = "bnb-nf4"`, `RUN_GENERIC_ONE_RUN = False`, isolated `qwen14b_bnb_nf4_selective_canary` output, fail-closed canary preflight gate, no `--auto-resume-hf`, `SOURCE_COMMIT = 0ece665ef25e1b0ca3aa14f5f25977cadbd06d0c` / `DEPLOYED_BUILD_ID = 0ece665`; full suite **1,877 passed / 32 skipped / 0 failed**; Dataset PASS (27 scenarios, zero closure dataset changes); Prompt 380; Pipeline Smoke 189; Scripted dry run 9/9 exit 0; Metric Verification 169; Ruff 0 new (21 pre-existing); mypy 0 new (5 pre-existing); notebooks compile 8/8 + 8/8; bundle content-identical (147 files / 962,188 bytes), manifests verified, no cache files; **next action = Kaggle engineering preflight ONLY for the 14B bnb-nf4 profile**; record `selective_updates/records/QWEN14B-BNB-NF4-CANARY-READINESS.md`; sentinel `QWEN14B_NF4_CANARY_READINESS_AUDIT_REQUIRED` - R4 ACCEPTED AND FROZEN (explicit freeze commit f5ae826) — R5 ACCEPTED AND FROZEN (independent re-audit 2026-08-01 at 7761c48) — R6 ACCEPTED AND FROZEN (final independent re-audit 2026-08-01 at 949e9c2) — **DETERMINISTIC INTERPRETER CLOSURE (2026-08-02) on branch fix/kaggle-smoke-v2-model-output-closure (runtime commit aac9914, bundle pin 311e084, pushed, local = remote, tree clean)** — **PRE-BENCHMARK FINAL SOURCE REPIN (2026-08-03) on branch fix/kaggle-smoke-v2-model-output-closure (deployment-only correction f8d00d7 re-pins deployment to source snapshot e5d9430, pushed, local = remote, tree clean; complete clean suite green 1,834 passed / 32 skipped / 0 failed)** — branch experiment/three-arm-smoke-v2 PUBLISHED to origin (freeze commit 4b2dd27 = first publication HEAD; upstream origin/experiment/three-arm-smoke-v2; local/remote equality verified before publication-status commit); post-R6 KAGGLE RUNTIME FIX on branch fix/kaggle-smoke-v2-runtime-blockers — two real Kaggle attempts failed pre-model (exp-20260801-024041, exp-20260801-024624; both 0 model calls; preserved, not deleted), all real runtime blockers closed (fix commit de3163f) and pinned (bundle commit fb60972) with the core fix accepted by the independent runtime-fix audit, and the R7A pre-rerun hardening closed all four audit findings (hardened source d50e89e, hardened bundle 4c73db6); a further real attempt reached 81 model calls / 47,694 tokens with 0 succeeded / 0 regenerated files (0/9, not scientific evidence); R7B SMOKE FINISH on branch fix/kaggle-smoke-v2-finish (runtime commit bff0a82, bundle pin 17207bf) makes the Qwen Smoke run observable and executable, with the notebook compile correction at 4c7a0af; **R7C REAL-RUN ROOT CLOSURE on branch fix/kaggle-smoke-v2-real-run-root (runtime commit 7a80e53, bundle pin f01b8f0, pushed, local = remote)** closed the four root contracts the FP16/deps-drift attempt exp-20260801-123125 exposed: environment memory (exact pins in requirements-smoke-kaggle.lock installed + verified in the notebook), int8 memory contract (qwen:1:int8 default, PYTORCH_ALLOC_CONF, seeded probe, VRAM headroom), frozen RegenerationScenarioContext prompt contract, and FailureKind.infrastructure_nonrepairable first-failure repair contract — plus a --kaggle-preflight-only gate (kaggle_smoke_preflight.v1, 6 checks, no run side effects); the prior R7C report incorrectly called a 1,451-test subset the full suite (true first full suite = 23 failed / 1,759 passed / 32 skipped; root cause = blanket baseline_validation => infrastructure_nonrepairable); the independent GPT-5.6 Thinking correction was imported via bundle fast-forward (**ffa179a + 6d6aa36, HEAD 6d6aa36, pushed**) and the exact 23 former failures now pass, with DRF import mapping, exact version verification, fail-fast preflight, driver-level VRAM, CPU-offload rejection, Python 3.12 contract, and stale source identity (SOURCE_COMMIT=ffa179a) corrected; current full gate = 1,790 passed / 32 skipped / 0 failed; local scripted = 9/9; bundled CLI dry-run = 9/9; real Qwen = 0/9; tag not created; Pilot = NOT AUTHORIZED; independent full-gate audit required before any Kaggle relaunch; do not tag/merge/force-push/relaunch Kaggle before that audit. All reading is repository-contained; external prompt packages are historical provenance only. An independent post-gate audit on `5e47a1e` then found (a) the project-local `ImportError` was incorrectly bypassing repair (blanket marker match), (b) the bundled preflight could not import `benchmark` without ambient `PYTHONPATH`, and (c) preflight output was buffered; its exact correction was imported via bundle fast-forward (**6f88823 + 5797fc0, HEAD 5797fc0, pushed**) and now the project-local `ModuleNotFoundError` / `cannot import name` are repairable via the canonical classifier (missing declared Django + CUDA OOM stay `infrastructure_nonrepairable`), the bundled script bootstraps its own `src/`, and preflight output is streamed and persisted; notebook source identity = `SOURCE_COMMIT 6f88823` / `DEPLOYED_BUILD_ID 6f88823`; current full gate = 1,796 passed / 32 skipped / 0 failed; valid real Qwen remains 0/9; no scientific evidence exists; final independent full-gate audit required before any Kaggle relaunch, after which only the engineering preflight cell is authorized (not the scientific One-Run cell); do not tag/merge/force-push/relaunch Kaggle before that final audit. **POST-SMOKE CALIBRATION CLOSURE (2026-08-03) on branch fix/kaggle-smoke-v2-model-output-closure (HEAD 231b0a5, pushed, local = remote, tree clean)** closed four proven calibration control defects: Closure A per-attempt atomic regeneration (zero writes on any guard failure), Closure B repair no-progress detection (`repair_no_progress` early-stop on identical repair hash), Closure C fail-closed calibration continuation gate (`AUTHORIZE_CONTINUOUS_AFTER_CALIBRATION_REVIEW = False`), Closure D cooperative deadline semantics (`scientific_budget_exhausted` scientific terminal vs engineering blockers). Commits: `27c1693` (runtime + tests), `56772fe` (deployment pin, `SOURCE_COMMIT = 27c1693e22b1a68be0b299fb146d9ff1e500908b`, `DEPLOYED_BUILD_ID = 27c1693`), `231b0a5` (test-fixture reconciliation — the nine first-gate failures were stale constant-output fixtures activating the new no-progress contract, not validly proven pre-existing; all metric/count/duration/token expectations preserved; side-by-side boundary test added). Final gate: full suite = **1,849 passed / 32 skipped / 0 failed**; mypy strict Success (77 files); ruff 93 = 93 baseline (0 new); bundle content-identical (147 files / 934,495 bytes); all notebook cells compile. Calibration evidence `exp-20260803-002741` = 9 terminal records / 0 succeeded / 8 failed / 1 timed_out / 81 model calls / 118,211 tokens — **preserved, not accepted scientific evidence**; latest real calibration = 0/9; no Kaggle rerun performed; no tag; Pilot NOT authorized; next action after the independent audit is **one selective calibration canary only** (not a full relaunch, not a fine-tune, not a tag/merge). Sentinel: `POST_SMOKE_CALIBRATION_CLOSURE_AUDIT_REQUIRED`. **FINAL SELECTIVE CANARY READINESS CLOSURE (2026-08-04) on branch fix/kaggle-smoke-v2-model-output-closure (HEAD 356722b, pushed, local = remote, tree clean)** — the independent GPT-5.6 Thinking audit at `f727b3e` REJECTED canary readiness even though the full suite was green, based on three independently reproduced blockers: (1) the cooperative deadline was checked only before the whole regeneration attempt, not before every selection/generation/repair model call — direct repro: 3 model calls and false success with a 1s deadline; now every in-flight call returning beyond the deadline consumes/records its tokens, makes no next call, writes none of the staged attempt, returns the failed scientific terminal `scientific_budget_exhausted` (same guard on every internal Iterative Agent call); (2) atomic-abort `regenerated_artifact_count` was false (1 with 0 writes when an artifact was rejected) — now all staged `generated` statuses become `aborted`/`rejected`, count = 0, hashes/evidence preserved, all-valid attempts still write each file exactly once; (3) the generic one-run cell selects `monolithic` (scenario-first plan order), not `selective` — a dedicated, separately named Selective Calibration Canary cell was added (`--strategy selective --max-runs 1 --new-experiment`, isolated output `runs/selective_calibration_canary`, NO `--auto-resume-hf`, `AUTHORIZE_CONTINUOUS_AFTER_CALIBRATION_REVIEW = False`) whose `_verify_selective_canary()` asserts exactly one current-source record `todo-smoke-001 / selective`, model identity `qwen:1:int8`, model calls > 0, terminal scientific success/failure, HF `recovery_uploaded`, checkpoint 3 planned / 1 completed / 2 pending. Commits: `50ec2c1` (Commit A: per-call deadline + atomic metric truth), `28ecc5a` (Commit B: pin `SOURCE_COMMIT = 50ec2c1ca43c230aed4538be32ca7dab2ccc22e5` / `DEPLOYED_BUILD_ID = 50ec2c1`, bundle rebuilt 147 files / 948,250 bytes, canary cell added), `356722b` (test alignment: `model_call_budget_exhausted=False` on MagicMock exec_ret, r4 staged-status assertions corrected to `aborted`/`rejected`, asyncio loop fix). Full gate: **1,856 passed / 32 skipped / 0 failed**; grouped per-category 629 passed / 1 skipped; scripted dry run 9/9 exit 0 (fresh dir; default dir held a stale checkpoint); mypy strict Success (77 files); ruff 0 new; compileall clean; notebooks compile (8/8 bundle code cells); bundle content-identical. Calibration evidence `exp-20260803-002741` remains preserved, 0/9 success, not accepted scientific evidence; no Kaggle rerun; no tag; no merge; Pilot NOT authorized; **no stable release claimed**; next action = run the dedicated selective calibration canary cell ONLY after the independent re-audit (not the generic one-run cell, not the continuous cell, not a full relaunch, not a fine-tune, not a tag/merge). Sentinel: `FINAL_SELECTIVE_CANARY_READINESS_AUDIT_REQUIRED`. — **SELECTIVE CALIBRATION CANARY RESULT (2026-08-04) on branch fix/kaggle-smoke-v2-model-output-closure: dedicated canary `exp-20260804-133523` (`todo-smoke-001 / selective`, source/build `50ec2c1`) FAILED `model_output` — 4 calls / 5,804 tokens / 257.596 s / 3 selected / 2 preserved / 0 written; Qwen defects in models/serializers/views; `repair_no_progress` after a byte-identical first repair; harness safety controls verified while Qwen code quality unchanged (identical initial tokens + output hashes); incidental monolithic run `exp-20260804-133016` diagnostic only; continuous cell fail-closed (`CALIBRATION_REVIEW_REQUIRED`); accepted dedicated canary records = 1, successful = 0; full 9-record experiment NOT run; no merge/tag/Pilot/Kaggle authorized; no stable release claimed. Sentinel: `SELECTIVE_CANARY_RESULT_AUDIT_REQUIRED`.**

---

## CURRENT PROJECT STATE

**CURRENT (2026-08-22):** the accepted deployment source is
**`v0.9.19-pilot-exec-ready`** @ tag peel == artifact source commit
`2305991442a4f965d44bb066bb00c0a459fc395a` (2026-08-19, the PostgreSQL
admin/application bootstrap + partial recovery closure on branch
`fix/pilot-v0919-postgres-admin-bootstrap-recovery` from clean `origin/main`,
non-ff merged to main; annotated tag ON the merge commit). Artifact
trust/provenance is GREEN: `pilot_deployment_identity.json.source_commit ==
2305991…` == tag peel; source-provenance gate PASS; FINAL ARTIFACT TRUST GATE
PASS; exact archive `dist/pilot-kaggle-upload.zip` SHA-256 `f7a16858…`
(+ `.sha256` sidecar). v0.9.18 release-only provenance/docs correction is PRIOR.
Carried full-suite evidence at this state: **2330 passed / 34 skipped /
0 failed** (OpenCode full suite). Release chain summary:

- v0.9.14 REJECTED: artifact notebook provenance did not match immutable tag notebook
- v0.9.15 REJECTED FOR ACCEPTED PILOT LAUNCH: dist artifact still v0.9.14; code-manifest SHA stale; single-parent commit
- v0.9.16: release-only closure (notebook anchors corrected); PGDG bootstrap bug discovered during real Kaggle run
- v0.9.17 REJECTED FOR ACCEPTED PILOT LAUNCH: tag/source-commit release-provenance mismatch (PGDG fix GOOD)
- v0.9.18: release-only provenance/docs correction (no scientific or production code changes) — historical
- **v0.9.19: ACCEPTED — PostgreSQL admin/application bootstrap + partial recovery closure (real Kaggle defect fix); trust/provenance GREEN**

Real Pilot = NOT STARTED. Next = fresh Kaggle v0.9.19 target preflight →
accepted 48-cell Pilot in the same session if all target gates pass.

HISTORICAL release records (superseded — traceability only):
`b8d3cf5e…` + all 94 `code_manifest.json` entries equal the normalized tracked
Git blobs at `identity.source_commit`; both bundled `*.lock` files are
LF-faithful). **Non-ff merged to main `bfeff97…`; annotated tag
`v0.9.12-pilot-exec-ready` created on the merge commit and pushed; identity
source_commit `bfeff97…` == tag peel == main HEAD; tag-tree notebook blob ==
deployed == freeze anchor; bundled 48-cell mock dry-run 48/48.** Full
suite **2,255 passed / 33 skipped / 0 failed** (2026-08-16). Freeze evidence
`reports/pilot_notebook_trust_freeze.json` (tracked).

v0.9.11 record (REJECTED for launch — see the handoff-type header above): the
v0.9.11 artifact passed its internal release gates (merged to main `8801304`,
annotated tag on the merge commit, finalizer re-freeze `b87aa49`, FINAL
ARTIFACT TRUST GATE Notebook == Identity == Actual 4/4, 48-cell dry-run 48/48)
but the immutable tag `8801304` does NOT contain the deployed re-frozen
notebook `85edbd33…` (it carries the v0.9.10 notebook `d15d8683…`; the re-freeze
landed only in the post-tag commit `b87aa49`), so the tag cannot reproduce the
claimed source snapshot. Tag NOT moved; superseded by v0.9.12.

v0.9.10 record (release trust gate closure, immutable):
**MERGED TO MAIN + TAGGED**. Feature branch `fix/pilot-release-trust-gate-closure`
(fix `097768e`, docs `4ac7f0d`) was non-fast-forward merged to `main` as
`44e9a1f4314c2ce8ec0b7abb16c88cbc3f83bfb6` (`merge(pilot): release trust gate
closure (notebook==identity==actual, v0.9.10-pilot-exec-ready)`; main HEAD ==
merge SHA), and the annotated tag `v0.9.10-pilot-exec-ready` was created on
that merge commit and pushed to origin (peels to `44e9a1f…`). The release
trust gate re-freezes the deployment source: the frozen notebook anchors are
proven equal to the deployment identity AND the actually-built bundle bytes
for ALL four manifest/map hashes (Notebook == Identity == Actual 4/4). Code
manifest hash `bb976f67fefe184796469efcd3f6916fbd592ec9f226b7b0365a237a0ef654d5`
(91 entries) — the v0.9.9 recorded value `99688e4e…` was stale (it predated the
bundled helper-script additions and was never validated against the build).
Data `8b859ecc72164fe95c0aa122f8179310ccc6375613543c6702c2ca5867c97b5a`,
repository snapshot `49d91d39435f7e6f2dbf7d15f1a59188aa059ebb16fb31094c7a1827fb62702c`,
transport path map `07036a36cd97daef48a39f6490bc055f58e87b336d849a4c1343e82a167cdbce`
remain byte-identical to v0.9.9. Deployed notebook SHA-256
`d15d86831bf805e7bcc9e811eb87158b2e4f56732082d1e6326ee9d94ccb81ec` == bundled
archive bytes == freeze report; normalized bundled notebook == source
`873e97735cd22b9f7686b56b3d058d1cd01f75513e6a6c8603f1e9dcf70ed71b`. Freeze
evidence `reports/pilot_notebook_trust_freeze.json` (tracked). Tagged-rebuild
archive SHA-256 `9df1396d50a99da7b3dd101fefe79013c3c253da8fd65251dbd9eb4650e71436`
(sidecar matches; `pilot_deployment_identity.json` source_commit `44e9a1f…`
== tag peel; created_utc `2026-08-15T14:00:00+00:00`).
**FINAL ARTIFACT TRUST GATE PASS** (Notebook == Identity == Actual 4/4 on the
tagged rebuild; deployed notebook == freeze; trust-gate regression + real
artifact expanded simulation 19/19). **No scientific inputs changed.** No-pip
repository env provisioning (v0.9.9), Redis-compatible per-candidate OS
package fallback (v0.9.8), root-safe unprivileged PostgreSQL bootstrap
(v0.9.7), transport encoding and `service-bootstrap-cell` are all unchanged.
Targeted trust-gate closures 142/142; full suite **2,234 passed / 33 skipped /
0 failed**; diff-check/ruff/mypy/compile clean. Authoritative upload artifacts
= `dist/pilot-kaggle-upload.zip` + `dist/pilot-kaggle-upload.zip.sha256`
(tagged rebuild; never manually re-zip). Execution contract pre-registered
(`docs/PILOT_EXEC_01_EXECUTION_CONTRACT.md`, DECISION_LOG D025); exact fresh
48-cell bundled dry-run on the tagged rebuild **48/48 terminal / 48 succeeded /
0 failed / 0 pending / 48 unique run IDs** (per-repo 16/16/16; per-strategy
24/24; per-rep 24/24; 0 model calls). **Pilot = NOT STARTED**; real launch
deferred until the user confirms the actual Kaggle mounted model path and HF
results repository ID. Previous milestone state (PILOT-READY-01 = CLOSED at
`34ecf78`; Scientific Smoke V2 complete/accepted; preferred Smoke recovery tag
`v0.8.2-smoke-v2-complete`; no-pip repo-env provisioning closure
`v0.9.9-pilot-exec-ready`) is unchanged historical truth.

## LAST ACCEPTED MILESTONE

Scientific Smoke V2 (SMOKE-V2-CLOSE-01): accepted clean 300-second Full-9
baseline + accepted 600-second confirmatory Full-9 `exp-20260808-222843`
(2/9 successes, 0 engineering blockers, timeout censoring ruled out). Plus the
MAIN-GREEN-01 reproducibility hotfix (this closure), which preserves that
scientific evidence with zero drift.

## PREFERRED RECOVERY TAG

Smoke era: `v0.8.2-smoke-v2-complete` (immutable, do not move). Pilot
readiness: `v0.9.0-pilot-ready` @ `90a4282` (immutable, do NOT move).
**CURRENT deployment source tag (accepted release, 2026-08-19):
`v0.9.19-pilot-exec-ready` @ tag peel == artifact source commit
`2305991442a4f965d44bb066bb00c0a459fc395a`** (annotated tag ON the merge
commit, pushed; trust/provenance GREEN; exact archive `f7a16858…`).
Pilot deployment source tags (HISTORICAL — superseded by v0.9.19):
`v0.9.12-pilot-exec-ready` @ main `bfeff97…`
(release-provenance closure, 2026-08-16;
annotated tag ON the merge commit, pushed; the immutable tag
contains the deployed re-frozen notebook and the source-provenance gate passed
on the artifact built from the tagged commit — bundled notebook + all
`code_manifest.json` entries equal the normalized tracked Git blobs at
`identity.source_commit`; full suite 2,255 passed / 33 skipped / 0 failed).
`v0.9.11-pilot-exec-ready` @ main `8801304` = internally-valid artifact, REJECTED
for launch (the immutable tag does not contain the deployed re-frozen notebook
`85edbd33…` — it carries `d15d8683…`; NOT moved). Historical execution-ready
points:
`v0.9.10-pilot-exec-ready` (2026-08-15 release trust gate closure; MERGED TO
MAIN `44e9a1f…` + TAGGED; peels to the merge commit; carries the validated
release-trust-gate freeze — Notebook == Identity == Actual 4/4 for the four
frozen manifest/map hashes against a real build from the LOCAL repo cache,
code manifest `bb976f67…` validated; tagged-rebuild archive `9df1396d…`;
48-cell dry-run 48/48; immutable, NOT moved),
`v0.9.9-pilot-exec-ready` (2026-08-15 no-pip repository environment
provisioning closure — stdlib venv always `--without-pip`, HOST pip `--python`
bootstrap of the no-pip tool/target envs, `uv` tool env, django CMS deps via
`uv pip install -r` from the frozen snapshot, Saleor pinned-snapshot copy +
`uv venv .venv --python <existing 3.12>` (`UV_PYTHON_DOWNLOADS=never`) + `uv
sync --locked`, completion markers + health probes, rebuild ONLY the invalid
private env dir, ONE `apt-get install` transaction for `gettext`+`gcc`+
`libpq-dev` (fail closed), secret-redacting provisioning log, thin-adapter
`pilot-repo-preflight-cell`, bundle-shipped helper + `code_manifest.json`
hash; immutable, NOT moved),
`v0.9.8-pilot-exec-ready` (2026-08-15 Redis-compatible per-candidate OS package
fallback + root-safe unprivileged PostgreSQL bootstrap + `kaggle_transport`
encoding + pre-upload validator + `transport-restore-cell`; immutable, NOT
moved),
`v0.9.7-pilot-exec-ready` (2026-08-13 root-safe PostgreSQL bootstrap; immutable,
NOT moved),
`v0.9.6-pilot-exec-ready` (Kaggle auto-expanded mount correction; immutable,
NOT moved),
`v0.9.5-pilot-exec-ready` @ `eb07b7b` (reserved-name transport correction;
immutable, NOT moved),
`v0.9.4-pilot-exec-ready` @ `96b6481` (Kaggle filename transport correction;
`__kaggle_transport__` root superseded by v0.9.5; immutable, NOT moved),
`v0.9.3-pilot-exec-ready` @ `4fa6e1d` (service-bootstrap correction; immutable,
NOT moved), `v0.9.2-pilot-exec-ready` @ `e030be5` (merged main commit carrying
the Pilot bundle builder + deployment contract + pre-registration + Gate 9/10
closure; immutable, NOT moved; the interim tag `v0.9.1-pilot-exec-ready` @
`7efdbe6` is superseded).

## FROZEN SCIENTIFIC IDENTITIES

Pilot contract (frozen): model `Qwen/Qwen2.5-Coder-14B-Instruct`, quantization
`bnb-nf4`, temperature 0, scientific per-run workflow timeout **600s** (do NOT
raise above 600), max 3 attempts (initial + 2 repairs), max completion 4096
tokens/call, workflow-token ceiling 0 (unlimited for Pilot), 12 scenarios × 2
strategies (`iterative_repository_agent`, `selective`) × 2 repetitions = 48
cells; repos Todo / django CMS / Saleor. Prompts/datasets/strategies/metrics/
evaluator frozen. Every Pilot launch MUST pass `--qwen-quantization bnb-nf4`
explicitly (generic CLI default is `bnb-int8`).

## ACCEPTED EXPERIMENTS

- Accepted clean 300-second Full-9 baseline (runtime `7f2a450`, `--timeout 300`, 2/9).
- Accepted 600-second confirmatory Full-9 `exp-20260808-222843` (2/9, T600).
- Accepted isolated selective canary `exp-20260807-131819` (todo-smoke-001 / selective, succeeded).
- Accepted nine non-dry scripted production records (R5, 9/9, frozen).

## REJECTED EXPERIMENTS — NEVER PROMOTE

- First Full-9 `exp-20260807-205422` (runtime `f7b1ebb`) — workspace contamination, evidence only.
- Dedicated canary `exp-20260804-133523` — failed `model_output`, diagnostic only.
- Real attempts `exp-20260801-024041` / `exp-20260801-024624` — failed pre-model, preserved.
- Any dry-run/mock record — never accepted scientific evidence.

## KNOWN FIXED DEFECTS

- Post-merge test-isolation/reproducibility defect (MAIN-GREEN-01): CRLF
  working-tree checkouts of byte-frozen LF fixtures + `__pycache__/*.pyc`
  residue in baseline comparisons → 12 failed / 4 errors. Fixed via
  `.gitattributes` `text eol=lf` pins + LF renormalization + ephemeral-baseline
  predicate; proven repeatable twice (T4/T5/T7) and full-suite green (T9).
- Pre-existing (documented, out of scope for MAIN-GREEN-01): re-running
  `seven_arm_benchmark.py --dry-run` in the SAME output dir hits
  `ReportRebuildError: Unexpected Run IDs` from stale records in
  `rebuild_experiment_reports` (src/benchmark/checkpoint/reports.py:164); use a
  fresh `--output-dir` for repeat dry-runs.

## CURRENT GIT STATE

`main` = `44e9a1f` (merge `merge(pilot): release trust gate closure
(notebook==identity==actual, v0.9.10-pilot-exec-ready)`; tag
`v0.9.10-pilot-exec-ready` peels here; non-ff merged from
`fix/pilot-release-trust-gate-closure` — fix `097768e` + docs `4ac7f0d`; all
pushed). Prior deployment source `v0.9.9-pilot-exec-ready` @ `f211e4d` (non-ff
merge `44d0102`) NOT moved; `v0.9.8-pilot-exec-ready` @ `7e0a908` NOT moved.
Earlier milestones: MAIN-GREEN-01 closed at `d875c72`; SMOKE-V2-CLOSE-01 merged
at `193d889`. Tags: preferred recovery `v0.8.2-smoke-v2-complete` at `403977b`;
historical `v0.8.1-smoke-v2-complete` at `d875c72`; `v0.8.0-smoke-v2-complete`
at `193d889` — all immutable, never force push.

## EXACT NEXT TASK

`PILOT-EXEC-01` — Pilot freeze and execution. The release trust gate closure
is MERGED AND TAGGED: `v0.9.10-pilot-exec-ready` @ `44e9a1f` (non-ff merge),
FINAL ARTIFACT TRUST GATE PASS (Notebook == Identity == Actual 4/4), exact
`dist/pilot-kaggle-upload.zip` SHA-256 `9df1396d…` + sidecar rebuilt from the
tagged source, bundled 48-cell mock dry-run 48/48, full suite 2,234 passed /
33 skipped / 0 failed. The real Pilot remains **NOT STARTED and
NOT yet authorized**: upload the exact archive as ONE Kaggle Dataset, attach the
Pilot notebook + Qwen 14B model, enable Internet, configure `HF_TOKEN`, run the
preflight cells in order, and execute the real 48-cell Pilot ONLY after all
preflight gates pass — still deferred until the user confirms the actual Kaggle
mounted model path and HF results repository ID. Do NOT raise the timeout above
600s; pre-register the Pilot budget. Frozen Pilot matrix: model
Qwen2.5-Coder-14B-Instruct, quantization bnb-nf4, timeout 600s, 12 scenarios, 2
strategies (iterative_repository_agent, selective), 2 repetitions = 48 cells;
repositories Todo / django CMS / Saleor.

## DO NOT DO

Do not change frozen scientific inputs (model, prompts, datasets, strategies,
metrics, evaluator, timeout=600). Do not modify the accepted evidence
workspaces. Do not move/delete `v0.8.0-smoke-v2-complete` (or any tag). Do not
force push, amend, or rewrite history. Do not patch the pre-existing
stale-records dry-run behavior without a dedicated task.

## PILOT-READY-01 BLOCKERS

None — **PILOT-READY-01 = CLOSED (2026-08-10)**. The Pilot profile and matrix
are frozen (Qwen2.5-Coder-14B-Instruct / bnb-nf4 / 600s / 12 scenarios / 2
strategies / 2 repetitions / 48 cells; Todo / django CMS / Saleor). The Pilot
budget must be pre-registered by `PILOT-EXEC-01` before any Pilot run.

## TECHNICAL DEBT

- Pre-existing: dry-run in a reused output dir hits stale-record validation.
- Pre-existing ruff/mypy baseline findings in untouched files (unchanged by
  MAIN-GREEN-01; no production files modified).

## RECOVERY ON A NEW MACHINE

1. `git clone <repo>` and `git checkout v0.8.2-smoke-v2-complete`.
2. `conda activate selective-regen-benchmark` (or recreate from declarations).
3. `python -m pytest -q` → expect **2,026 passed / 33 skipped / 0 failed**.
4. `python seven_arm_benchmark.py --dry-run --output-dir <fresh>` → 8/8 clean.
5. `git status --short` → clean; `git log --oneline -5` shows the HANDOFF-CONSISTENCY-01
   merge + `v0.8.2-smoke-v2-complete` tag.

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

## 3. Historical State Snapshot (R6 era — SUPERSEDED 2026-08-22; current state = CURRENT PROJECT STATE above and docs/AI_ACCOUNT_TRANSFER_HANDOFF.md)

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
- **QWEN 14B FINAL PREFLIGHT CLOSURE (2026-08-05):** the independent audit rejected real preflight on the `5ef6438` state (full suite was green) after reproducing three blockers — all three are now closed on branch `fix/kaggle-smoke-v2-model-output-closure`. Commit A `0aa705d` (`fix(model): close Qwen 14B Kaggle preflight blockers`, 6 files / +280 / −10) + Commit B `cc7846b` (`chore(deploy): repin final Qwen 14B preflight bundle`), both pushed, local = remote, tree clean. **Fix A (notebook):** `SELECTIVE_CANARY_OUTPUT_DIR` was used before assignment (defined in the canary cell, referenced earlier) — moved to the `setup-cell` after `OUTPUT_DIR`, duplicate removed. **Fix B (preflight):** `EXPECTED_VISIBLE_GPU_COUNTS = (1, 2)` — real 2×Tesla T4 environments pass; else `FAIL (N; expected 1 or 2)`. **Fix C (identity):** `_checkpoint_identity_slug` maps numeric version dirs to `<parent>-v<version>` (e.g. `/kaggle/input/models/qwen-lm/qwen2.5-coder/transformers/14b-instruct/1` → `14b-instruct-v1` → `qwen:14b-instruct-v1:bnb-nf4:cfg-<12hex>`), so real Kaggle paths never yield a `qwen:1:*` readable identity. Official gate = declared clean env (Python 3.11.9 / pytest 8.4.2, `_workspace\cache\prebenchmark-py311`): full suite **1,890 passed / 32 skipped / 0 failed**; Dataset 285/5; Prompt 174; Pipeline Smoke 223/12; Dry Run 9/9 (exit 0, dashboard + evidence files present); Metric Verification 169; Ruff 0 new (91 pre-existing baseline in untouched files); mypy strict Success (77 files); compileall clean; notebook 8/8 + 8/8 compile; builder content-identical (147 files / 963,067 bytes), no cache files. Explicit regression proofs: **2-GPU otherwise-valid preflight = PASS** and **canary setup reaches subprocess construction without NameError**. Ambient pytest 9.1.1 is diagnostic only, never the gate. No Kaggle run, no canary, no continuous, no model/quantization/prompt/data change, no GPTQ/AWQ/GGUF/vLLM, no merge/tag/Pilot; **no real 14B result and no stable release claimed**; current accepted real records remain 0/9. **Next action after independent audit = Kaggle engineering preflight cell ONLY.** Sentinel: `QWEN14B_FINAL_PREFLIGHT_CLOSURE_AUDIT_REQUIRED`. Record: `selective_updates/records/QWEN14B-FINAL-PREFLIGHT-CLOSURE.md`.
- **QWEN 14B NF4 TRANSFORMERS V4 LOADER CLOSURE (2026-08-05):** the independent OOM audit reproduced the real preflight OOM at `9fd4eee` (full suite was green): transformers was unpinned, Kaggle image drift installed **5.0.0**, and its loader materialized the **14B BF16 weights on GPU before BNB-NF4 quantization** — OOM after 232.412 s at ~75% of 579 checkpoint params (tried 136 MiB; GPU 1 free 46.81 MiB; allocated 14.38 GiB). Commit A `41e9ad7` (`fix(model): pin transformers==4.57.6 BNB loader and preserve static preflight metadata`, 8 files / +210 / −6) + Commit B `920ab9b` (`chore(deploy): repin Qwen 14B NF4 v4 loader closure bundle`), pushed, local = remote, tree clean. **Fix A (lock):** `requirements-smoke-kaggle.lock` + `requirements-kaggle.txt` pin `transformers==4.57.6`; torch stays unpinned (Kaggle torch preserved). **Fix B (preflight):** `_REQUIRED_IMPORTS` requires the exact `"4.57.6"` — any other version FAILs before staging/model load. **Fix C (notebook):** `install-lock-cell` `EXPECTED_RUNTIME` gains transformers 4.57.6 (fail-closed mismatch check). **Fix D (loader):** `_load_model` passes `low_cpu_mem_usage=True` for `bnb-int8`/`bnb-nf4` so the 4.57.x loader streams/quantizes in place instead of materializing the full-precision temporary copy. **Fix E (truth):** `_static_model_metadata` preserves `model_identity`/`checkpoint_basename`/`quantization_method`/`gpu_count`/`gpu_name` (config.json + CUDA discovery, no weight load) when the load OOMs/fails. Gate = ambient Python 3.11.5 / pytest 9.1.1 (declared clean env `_workspace\cache\prebenchmark-py311` NOT present locally — audit should recreate it): full suite **1,898 passed / 32 skipped / 0 failed**; Ruff 0 new (86 pre-existing baseline); mypy strict Success (77 files); notebook + bundle pin identity PASS (`SOURCE_COMMIT=41e9ad7`); bundle integration 32 passed; builder content-identical (147 files / 964,859 bytes). Regression proofs: preflight FAILs on transformers≠4.57.6 before load; BNB loads pass `low_cpu_mem_usage=True` (fp16 does not); static metadata preserved on failed probe. No Kaggle run, no canary, no continuous, no model/quantization/prompt/data change, no GPTQ/AWQ/GGUF/vLLM, no merge/tag/Pilot; **no real 14B result and no stable release claimed**; current accepted real records remain 0/9. **Next action after independent audit = Kaggle engineering preflight cell ONLY.** Sentinel: `QWEN14B_V4_LOADER_CLOSURE_AUDIT_REQUIRED`. Record: `selective_updates/records/QWEN14B-NF4-TRANSFORMERS-V4-LOADER-CLOSURE.md`.
- **QWEN 14B NF4 V4 LOADER OFFICIAL GATE (2026-08-05):** the missing official clean-environment gate for the Qwen 14B NF4 transformers v4 loader closure is complete, and one stale Notebook markdown statement was corrected (docs/deploy only — no runtime code, tests, requirements, data, prompts, scenarios, strategies, evaluator logic, metrics, model settings, or runtime limits changed). The markdown cell immediately before `preflight-cell` in `notebooks/seven_arm_benchmark.ipynb` described the load as `int8` (`load_in_8bit=True` + `device_map="auto"` with `expandable_segments`) — stale; it now truthfully reads **Qwen 14B BNB-NF4 load** — `Qwen2.5-Coder-14B-Instruct` base checkpoint via BitsAndBytes NF4 (`load_in_4bit=True`, `bnb_4bit_quant_type="nf4"`, `bnb_4bit_compute_dtype=float16`, `bnb_4bit_use_double_quant=True`, `device_map="auto"`, Transformers 4.57.6). No executable code cell, `SOURCE_COMMIT`/`DEPLOYED_BUILD_ID` (`41e9ad7`), command, quantization setting, model path, timeout, token limit, or auth flag changed. Official gate = fresh disposable env created from project declarations only (`_workspace\cache\prebenchmark-py311-v4-loader`, Python 3.11.5 / **pytest 8.4.2 exactly**; Django 5.2.16, DRF 3.17.1, pytest-django 4.12.0, pytest-asyncio 1.2.0, ruff 0.15.22, mypy 1.20.2): full suite **1,898 passed / 32 skipped / 0 failed** (517.97 s); Dataset 281/4; Prompt 126/4; Pipeline Smoke 177; Dry Run 9 planned / 9 terminal / 9 succeeded / 0 failed / exit 0; Metric Verification 169; Ruff 0 new (91 pre-existing baseline); mypy strict Success (77 files); compileall clean; notebook code cells compile canonical + bundled; bundle rebuilt twice via `scripts/build_upload_bundle.py` — second run content-identical (147 files / 965,015 bytes; tree hash 26EA934F16A25C14788484CE1A75EFF4FB453E6C346F5FDCEE72D3004EC5B7D1), manifests verified, no cache files; `git diff --check` clean; working tree clean. Commit `docs(deploy): finalize Qwen 14B NF4 loader gate truth` pushed, local = remote. No Kaggle run, no preflight, no canary, no continuous, no merge/tag/Pilot; **no real 14B result and no stable release claimed**; accepted real records remain 0/9. Next action after independent audit = **Kaggle engineering preflight cell only**. Sentinel: `QWEN14B_V4_LOADER_OFFICIAL_GATE_AUDIT_REQUIRED`. Record: `selective_updates/records/QWEN14B-NF4-TRANSFORMERS-V4-LOADER-CLOSURE.md`.
- **QWEN 14B MULTI-GPU VRAM PREFLIGHT CLOSURE (2026-08-06):** the independent audit (`QWEN14B_MULTI_GPU_VRAM_PREFLIGHT_INDEPENDENT_AUDIT_2026-08-06.md`) found the preflight on the `897e323` state (full suite was green) read VRAM from **GPU 0 only** — `_qwen_probe_metrics` used `torch.cuda.memory_allocated(0)`/`memory_reserved(0)`/`mem_get_info(0)`/`synchronize(0)` and `vram_headroom` checked only that single free value, so a 2x Tesla T4 `device_map="auto"` 14B bnb-nf4 load could pass while GPU 1 had <2.0 GiB free. Commit A `f7b1ebb` (`fix(model): enforce multi-GPU VRAM headroom per visible GPU`, 2 files / +524 / −11) + Commit B `c8f5685` (`chore(deploy): repin multi-GPU VRAM preflight bundle`), pushed, local = remote, tree clean. **Fix:** immutable `GpuVramSnapshot`; `_collect_gpu_vram_snapshots()` (synchronize + read allocated/reserved/free/total on **every** visible GPU, three-decimal rounding, never swallows a per-GPU failure, `()` when CUDA unavailable); `free_vram_after_probe_gib = min(snapshot.free_gib)` + summed allocated/reserved scalars; minimum-free gate on every visible GPU (`vram_headroom: PASS (minimum free across 2 GPU(s)=X.XX GiB)` / `FAIL (GPU 1 free=0.12 GiB < 2.0 GiB)`, failing devices listed by index); ordered per-GPU evidence in `kaggle_smoke_preflight.v1` JSON (`gpu_vram_by_device`) and one human line per GPU; per-GPU snapshots preserved on failed loads via `_static_model_metadata`. Official clean-env gate (`_workspace\cache\prebenchmark-py311-v4-loader`, Python 3.11.5 / **pytest 8.4.2 exactly**): full suite **1,915 passed / 32 skipped / 0 failed** (500.22 s; +17 net new tests); Metric Verification 169; Ruff 0 new (86 pre-existing baseline); mypy strict Success (77 files); compileall clean; notebook + bundle pin identity PASS (`SOURCE_COMMIT=f7b1ebb`); bundle integration 32 passed; builder content-identical (147 files / 968,722 bytes). Mandatory adversarial reproduction: **GPU0 free 3.0 GiB / GPU1 free 0.125 GiB → FAIL**. No Kaggle run, no preflight on Kaggle, no canary, no continuous, no model/quantization/prompt/data change, no GPTQ/AWQ/GGUF/vLLM, no merge/tag/Pilot; **no real 14B result and no stable release claimed**; accepted real records remain 0/9. **Next action after independent audit = Kaggle engineering preflight cell ONLY.** Sentinel: `QWEN14B_MULTI_GPU_VRAM_CLOSURE_AUDIT_REQUIRED`. Record: `selective_updates/records/QWEN14B-MULTI-GPU-VRAM-PREFLIGHT-CLOSURE.md`.
- **QWEN 14B SELECTIVE CANARY SUCCESS (2026-08-07):** independent GPT-5.6 Thinking audit ACCEPTED the successful real canary — docs-only closure, no code/tests/data/prompts/configs/notebook/kaggle_upload changes. Real engineering preflight PASS (2×Tesla T4, bnb-nf4, identity `qwen:14b-instruct-v1:bnb-nf4:cfg-cc9474140d25`, footprint 9,721,981,184 bytes, preflight 174.016 s, probe 68+17 tokens, minimum free VRAM 8.417 GiB, GPU-only). Canary `exp-20260807-131819` (`todo-smoke-001 / selective`, runtime source `f7b1ebba73b52868a95c47ef3806d3b09da16d93` / build `f7b1ebb`) succeeded: 3 selected / 2 preserved / 3 regenerated; migration `todo/migrations/0004_task_priority.py`; 3 model calls / 2,527 prompt + 720 completion = 3,247 tokens / 295.944 s / 0 repairs; functional validation PASS; evaluator PASS 10/10; HF `recovery_uploaded`. Accepted real 14B canary records = 1 succeeded / 0 failed. At the time this canary was accepted, Full 9-record Scientific Smoke V2 had not yet been run; subsequently the first Full-9 `exp-20260807-205422` was run under `f7b1ebb` and REJECTED for workspace contamination (fresh corrected Full-9 under `7f2a450` was NOT YET RUN at that time, pending the FULL9-WS-02A delta audit — HISTORICAL, later executed and accepted as `exp-20260808-222843`). Vs 7B: 25.0% fewer calls / 44.1% fewer tokens / repairs eliminated / 14.9% slower — functional viability, not strategy superiority. Unused `Q` import in generated `views.py` = non-blocking, evidence workspace NOT to be repaired. Continuous cell failed closed with zero model calls (generic experiment empty) — not a failure, do NOT patch before Full-9. No merge/tag/Pilot; next (HISTORICAL — superseded by the executed and accepted T600 Full-9) = independent delta audit of the FULL9-WS-02A runbook/docs closure, then one fresh corrected Full-9 only if accepted. Record: `selective_updates/records/QWEN14B-SELECTIVE-CANARY-SUCCESS-2026-08-07.md`.
- **SCIENTIFIC SMOKE V2 COMPLETE AND ACCEPTED (2026-08-09, SMOKE-V2-CLOSE-01):** the 600-second confirmatory Full-9 (T600, FULL9-T600-01) was **EXECUTED AND ACCEPTED** — run `exp-20260808-222843`, uniform `--timeout 600` on frozen runtime source/build `7f2a450`, fail-closed `_t600` output namespace, evidence prefix `corrected-full9-t600-wsfix-7f2a450-`: **9/9 terminal / 2 successes / 7 scientific failures / 0 engineering blockers / 0 budget-exhausted / 63 model calls / 77,929 tokens / max run ≈373 s / Full-9 verification PASS / HF synchronization PASS** — **same 2/9 result** as the accepted clean 300-second baseline (runtime `7f2a450`, `--timeout 300`, 9/9 terminal / 2 successes / 7 scientific failures / 0 engineering blockers, three runs at ~307–337 s ceiling). **Timeout sensitivity confirmed; the 300-second baseline signal was not distorted by timeout censoring; NOT an improvement claim.** 300-second baseline remains valid and preserved, NOT invalidated or replaced. Uniform per-run workflow timeout now frozen at **600s** for monolithic / selective / iterative_repository_agent (one shared Full-9 command; no strategy receives extra time); do NOT raise above 600. **HISTORICAL (all completed — SMOKE-V2-CLOSE-01 is CLOSED):** at the time, the task was to close Scientific Smoke V2 permanently (update all authoritative docs to the accepted state, audit the closure, commit/push proving local = remote, non-fast-forward merge to main, create/push stable tag `v0.8.0-smoke-v2-complete`, leave repo ready for `PILOT-READY-01` without starting Pilot); the next authorized action was an independent delta audit of the closure, then main merge + stable tag, then `PILOT-READY-01` — **all executed: closure audited and merged (`193d889`), stable tag `v0.8.0-smoke-v2-complete` created, MAIN-GREEN-01 merged (`d875c72`), preferred recovery `v0.8.1-smoke-v2-complete`, next `PILOT-READY-01` (Pilot NOT STARTED)**. No further Kaggle Full-9 is authorized; the accepted T600 run is the final Smoke evidence.
- **MAIN-GREEN-01 POST-MERGE TEST-ISOLATION AND REPRODUCIBILITY HOTFIX (2026-08-09):** the post-merge full-suite regression (12 failed / 4 errors on the Windows `core.autocrlf=true` working tree) is **FIXED AND CLOSED** — full suite **1,958 passed / 33 skipped / 0 failed / 0 errors**. Merge drift RULED OUT (tree proof `193d889`==`65f9fb8`==`fdd72f6…`; zero diff `65f9fb8..193d889`). Root causes: (A) bundle evaluator assets checked out CRLF → fingerprint mismatch; (B) `benchmark_data/repositories/todo/**` checked out CRLF → preserve-files rejected (`out_of_scope_change`) → cells failed before migration generation → sequential isolation "expected exactly one new migration, got ()"; (C) `__pycache__/*.pyc` residue in `_baseline_hashes()` → baseline compatibility false-negatives. Fix (zero scientific drift): `.gitattributes` `text eol=lf` pins for bundle evaluator assets + `benchmark_data/repositories/todo/**` + `kaggle_upload/data/repositories/todo/**` + LF renormalization (zero CRLF remain; zero blob changes); ephemeral-baseline predicate `_EPHEMERAL_BASELINE_MARKERS` in `tests/support/evaluator_fixture_workspaces.py` (copytree ignore in `_copy_baseline`) + `_baseline_hashes()` ephemeral skip; new T1/T2/T3 unit tests. Repeatability: T4 representative cell twice PASS; T5 sequential isolation twice PASS; T6 fingerprint PASS; T7 affected subset twice PASS (production-path 45, todo assets 53+1 skipped, kaggle bundle 51); T8 related regression 380 passed / 22 skipped; T9 full suite green once; static gates clean; dry-run pipeline 8/8 clean (fresh output dir; reusing an output dir hits a pre-existing stale-record validation — documented, out of scope). **Next = `PILOT-READY-01`; Pilot NOT started.** After docs commit B: independent-style audit, non-ff merge, tag `v0.8.1-smoke-v2-complete` (peeled == new main HEAD); `v0.8.0-smoke-v2-complete` unchanged.
- **Real Qwen records:** accepted canary succeeded 1 (isolated selective-only plan) / 0 failed; accepted Full-9 evidence = clean 300-second baseline (runtime `7f2a450`, `--timeout 300`, 2 successes / 7 scientific failures / 0 engineering blockers, valid and preserved) + accepted 600-second confirmatory Full-9 `exp-20260808-222843` (uniform `--timeout 600`, 2 successes / 7 scientific failures / 0 engineering blockers / 0 budget-exhausted / 63 calls / 77,929 tokens / max run ≈373 s / Full-9 verification PASS / HF synchronization PASS); first Full-9 `exp-20260807-205422` (source `f7b1ebb`) **RUN BUT REJECTED** (workspace contamination, evidence only); milestone tag `v0.8.0-canary.1` created/pushed (annotated, non-stable, points to `31a6198`); stable tag `v0.8.0-smoke-v2-complete` created after docs commit + main merge (`193d889`); main merge and MAIN-GREEN-01 merge complete (main `d875c72`); Pilot NOT AUTHORIZED (now NOT STARTED); next (HISTORICAL — superseded, all completed) = independent delta audit of the closure (SMOKE-V2-CLOSE-01), then main merge + stable tag, then `PILOT-READY-01` — current truth: preferred recovery `v0.8.1-smoke-v2-complete`, next task `PILOT-READY-01`.
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
| **Execute Scientific Smoke V2 on Kaggle** | **COMPLETE** | 300-second baseline accepted (runtime `7f2a450`, `--timeout 300`, 2 successes / 7 scientific failures / 0 engineering blockers) + 600-second confirmatory Full-9 `exp-20260808-222843` accepted (uniform `--timeout 600`, same 2/9 result, 0 budget-exhausted, max run ≈373 s, Full-9 verification PASS, HF synchronization PASS); milestone CLOSED (SMOKE-V2-CLOSE-01); timeout frozen at 600s uniformly; no further Kaggle Full-9 authorized |
| Audit Smoke V2 results | HIGH | Independent delta audit of the closure (SMOKE-V2-CLOSE-01) before main merge + stable tag + Pilot authorization |
| Integrate Pilot repositories | MEDIUM | ≥5K LOC, permissive license, pinned commit, passing tests |
| Run Pilot profile | MEDIUM | 7+ changes, 3+ repos, agent+selective — only via `PILOT-READY-01` after this closure |
| Merge to main | HIGH | In this closure task: after docs closure commit, non-fast-forward merge to main |
| Create stable tag `v0.8.0-smoke-v2-complete` | HIGH | In this closure task: after main merge (replaces stale `v2.0.0-scientific-smoke` naming); milestone `v0.8.0-canary.1` already created/pushed, non-stable |

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
tag not created (HISTORICAL: R6-era state; stable tag now `v0.8.0-smoke-v2-complete` @ `193d889`, preferred recovery `v0.8.1-smoke-v2-complete` @ `d875c72`)
Pilot not authorized (HISTORICAL: R6-era state; now NOT STARTED — PILOT-READY-01 = CLOSED, next task `PILOT-EXEC-01`)
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
  bitsandbytes==0.49.2, transformers==4.57.6. torch intentionally unpinned
  (Kaggle image provides its GPU torch build). The notebook `install-lock-cell`
  installs the lock first, verifies `EXPECTED_RUNTIME` via `RUNTIME_ATTR`, and
  writes `runtime_environment.json` (schema `kaggle_runtime_environment.v1`)
  under `OUTPUT_DIR.parent/"environment"`.
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
