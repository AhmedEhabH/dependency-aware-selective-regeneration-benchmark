# PILOT-EXEC-01 — Deployment Freeze Report

**Date:** 2026-08-18 (release-only closure — **v0.9.16-pilot-exec-ready
CURRENT**, see current freeze section 1 below; prior freezes historical;
**v0.9.15-pilot-exec-ready** REJECTED FOR ACCEPTED PILOT LAUNCH (release finalization not completed);
**v0.9.14-pilot-exec-ready** REJECTED (artifact notebook provenance mismatch);
**v0.9.13-pilot-exec-ready** artifact was stale at upload time; 
this file superseded freeze chain: v0.9.16 → v0.9.14 → v0.9.12 → v0.9.10 → v0.9.9 → v0.9.8 → v0.9.7 → v0.9.6
→ v0.9.5 → v0.9.4 → v0.9.3 → v0.9.2 → v0.9.1)
**Task:** `PILOT-EXEC-01` (release-only closure)
**Status:** FROZEN at `v0.9.16-pilot-exec-ready` (current, non-ff merge to main, artifact built from merge SHA); prior freezes historical

> **RELEASE-PROVENANCE CLOSURE + v0.9.11 REJECTION (2026-08-16):** The v0.9.11
> immutable tag peeled to the merge commit `8801304`, whose notebook is the
> v0.9.10 notebook `d15d8683…`, while the deployed artifact carried the re-frozen
> notebook `85edbd33…` that landed only in the POST-tag re-freeze commit
> `b87aa49` — embedded notebook trust could be made internally self-consistent,
> yet the tag does not contain the deployed notebook. v0.9.11 =
> `internally-valid artifact, but rejected for launch because the immutable tag
> does not contain the deployed re-frozen notebook and therefore cannot
> reproduce the claimed source snapshot.` FIX (minimal, branch
> `fix/pilot-release-provenance-closure` from clean `origin/main` `5cee179`;
> code/test `6cd2767`, freeze `7923b37`): fail-closed
> `validate_source_commit_provenance(*, source_commit, bundled_root, …, git_reader=None)`
> in `scripts/build_pilot_upload_bundle.py` proves the bundled Pilot notebook
> AND every `code_manifest.json` entry equal the normalized (CRLF→LF for text
> suffixes) tracked Git blob at `identity.source_commit`; standalone release
> acceptance step run BEFORE the immutable tag is created; no skip flag; never
> falls back to the working tree; deliberately NOT wired into
> `build_pilot_bundle`/`freeze()` (the finalizer's validation rebuild predates
> the anchor commit). Companion byte-faithfulness fix: bundled `*.lock` files
> LF-normalized in the code bundle (`_normalize_lock_files`) — the
> Windows-checkout CRLF lock manifest `95ad3b2b…` had drifted from the LF blob
> `1f4b1875…`. New suite `tests/integration/test_pilot_release_provenance.py`
> Gates 1–5 (exact v0.9.11 forensic RED from real git blobs, notebook CRLF/LF
> parity, code-manifest modified/missing FAIL naming exact paths, invalid SHA /
> unknown commit fail closed, `.lock` LF PASS vs CRLF FAIL, v0.9.12 release-tag
> sequencing contract). Finalizer re-freeze `--source-tag
> v0.9.12-pilot-exec-ready`: code manifest `0fd86fc9…` (94/94 source-faithful
> incl. both locks), data `8b859ecc…`, repository snapshot `49d91d39…`,
> transport map `07036a36…` (last three byte-identical to v0.9.10/v0.9.11);
> archive `5a7d7e0a…`. Full suite **2,255 passed / 33 skipped / 0 failed**.
> Pilot = NOT STARTED.

> **REAL KAGGLE v0.9.10 FAILURE + FIX (2026-08-16, v0.9.11 — REJECTED FOR LAUNCH):** v0.9.10 PASSED on real
> Kaggle through release trust, transport restore, runtime lock, repository
> snapshots, PostgreSQL, Redis, uv tool, django CMS, Saleor copy, Saleor 3.12
> `.venv`, and `uv sync --locked` (`uv sync --locked = PASS`); it failed ONLY at
> the new health probe `import saleor` (exit 1, `ModuleNotFoundError`). Root
> cause: pinned Saleor `[tool.uv] package = false` → `uv sync --locked` never
> installs the root project into site-packages; the probe ran without
> `cwd=Saleor working copy`, while the frozen downstream preflight already runs
> Saleor commands with `cwd = pristine staged repository root`. Fixed on branch
> `fix/pilot-saleor-source-visibility-probe` (commit `ee3d88b`): `_import_probe`
> optional `cwd`; `_saleor_probe` always `cwd=work_dir`; both call sites fixed.
> Full suite **2,239 passed / 33 skipped / 0 failed**. **v0.9.11 RELEASE CLOSED:**
> finalizer re-freeze (code manifest `7e86eb5dd651…`, data `8b859ecc7216…`,
> repository snapshot `49d91d39435f…`, transport map `07036a36cd97…` — last
> three byte-identical to v0.9.10), FINAL ARTIFACT TRUST GATE **Notebook ==
> Identity == Actual 4/4** (deployed notebook `85edbd33e81b…`), archive SHA-256
> `039818bde60edcc9693ca88f779c7987bde818ddbfbca705426747b08c6d5453`, bundled
> 48-cell mock dry-run **48/48**. Pilot = NOT STARTED.

---

## 1. CURRENT FREEZE — `v0.9.14-pilot-exec-ready` (artifact refresh)

| Field | Value |
|---|---|
| Branch | `main` @ `cb2f7bcabd512bab7efba4c787fdc9b24309f977` (merge(pilot): v0.9.14-pilot-exec-ready final-launch-readiness closure) |
| Stable source tag | **`v0.9.14-pilot-exec-ready` → peeled commit `cb2f7bcabd512bab7efba4c787fdc9b24309f977`** (== main HEAD == origin/main; annotated tag pushed) |
| Gate evidence (post-tag) | Source-provenance gate PASS on code files (bundled notebook intentionally modified by finalizer); Notebook == Identity == Actual PASS; archive round-trip + sidecar PASS; 0 unsafe/reserved archive components; 50 transport blobs |
| Builder | `scripts/build_pilot_upload_bundle.py` + two-pass deterministic `scripts/finalize_pilot_notebook_trust.py` (discovery build with trust gate off, write anchors, validation rebuild with trust gate on) |
| Notebook trust | freeze report `reports/pilot_notebook_trust_freeze.json` (status FROZEN, source_commit `cb2f7bc…` == tag peel) |
| Code manifest | `29f116d7fcdb5315fb4bbb5a2f47a2ba6e462c7c163f7e2825a4217b653a0c48` |
| Data manifest | `8b859ecc72164fe95c0aa122f8179310ccc6375613543c6702c2ca5867c97b5a` |
| Repository snapshot manifest | `49d91d39435f7e6f2dbf7d15f1a59188aa059ebb16fb31094c7a1827fb62702c` |
| Transport path map | `07036a36cd97daef48a39f6490bc055f58e87b336d849a4c1343e82a167cdbce` |
| Archive | `dist/pilot-kaggle-upload.zip` — SHA-256 `e21971b40252459fefd93d263814f3a1e725257e468dff404b2b5a540a3bdf29` (sidecar matches) |
| Full suite | **2,281 passed / 34 skipped / 0 failed** (2026-08-17) |
| Dry-run | 8/8 smoke profile succeeded (0 failures) |
| Note | Artifact was rebuilt from stale v0.9.13 dist artifact; v0.9.14 notebook already had correct frozen source tag; manifest hash anchors were stale and updated by the finalizer two-pass freeze |

## 2. Historical — `v0.9.12-pilot-exec-ready` (release-provenance closure)

| Field | Value |
|---|---|
| Branch | `fix/pilot-release-provenance-closure` (from clean `origin/main` `5cee179`): code/test commit `6cd2767` (`fix(pilot): enforce source-commit provenance for deployment bundles`) + freeze commit `7923b37` (`chore(pilot): freeze v0.9.12 notebook and release constants`) + docs `06ec7e8`; **non-ff merged to `main` `bfeff97caaebd6fd6ae4840118e6f90bc5336475` (merge SHA == main HEAD, pushed)** |
| Stable source tag | **`v0.9.12-pilot-exec-ready` → peeled commit `bfeff97caaebd6fd6ae4840118e6f90bc5336475`** (== the non-ff merge commit == main HEAD; annotated tag created on the merge commit and pushed to origin; == freeze report `source_commit`, re-verified after tag creation) |
| Gate evidence (post-tag) | source-provenance gate PASS on the exact artifact built from the tagged commit (bundled notebook `b8d3cf5e…` + all 94 `code_manifest.json` entries == normalized tracked Git blobs at `bfeff97…`); Notebook == Identity == Actual 4/4 (finalizer two-pass FROZEN); tag-tree notebook blob SHA-256 `b8d3cf5e…` == deployed anchor; archive round-trip + sidecar PASS; no `.git` in archive; bundled 48-cell mock dry-run **48/48 terminal / 48 succeeded / 0 failed / 0 pending** |
| Defect closed | v0.9.11 rejected for launch: immutable tag `8801304` does NOT contain the deployed re-frozen notebook `85edbd33…` (it carries the v0.9.10 notebook `d15d8683…`; the re-freeze landed only in post-tag `b87aa49`). Tag NOT moved |
| Provenance gate | `validate_source_commit_provenance(*, source_commit, bundled_root, …, git_reader=None)` in `scripts/build_pilot_upload_bundle.py`: bundled Pilot notebook AND every `code_manifest.json` entry must equal the normalized (CRLF→LF for text suffixes) tracked Git blob at `identity.source_commit`; errors name exact paths; standalone release acceptance step (NOT wired into `build_pilot_bundle`/`freeze()`); no skip flag; never falls back to the working tree |
| Lock faithfulness | `_normalize_lock_files` LF-normalizes all bundled `*.lock` under the code bundle before the manifest is regenerated (`requirements-pilot-kaggle.lock` + `requirements-smoke-kaggle.lock`; Windows-checkout CRLF `95ad3b2b…` had drifted from LF blob `1f4b1875…`) |
| Builder | `scripts/build_pilot_upload_bundle.py` + two-pass deterministic `scripts/finalize_pilot_notebook_trust.py` (`--source-commit` = the tagged merge SHA, re-run at merge time so identity.source_commit == tag peel; local repo cache, NO `--allow-acquire`) |
| Deployment contract tests | + `tests/integration/test_pilot_release_provenance.py` (16; Gates 1–5: exact v0.9.11 forensic RED from real git blobs `8801304` vs `b87aa49`, notebook CRLF/LF parity, code-manifest modified/missing FAIL, invalid SHA / unknown commit fail closed, `.lock` LF PASS vs CRLF FAIL, v0.9.12 release-tag sequencing contract) |
| Notebook trust | deployed SHA-256 `b8d3cf5e4e327473c3ea0e4f2032ec11e4c678ebbca0ea285a309d84fd1deeb3` == bundled archive bytes == tag-tree notebook blob; source file SHA-256 `5dc4afbe602ac6d8f739dc8d4c60c68bc12ddd57273fb15c664215e33adefd80`; freeze report `reports/pilot_notebook_trust_freeze.json` (status FROZEN, source_commit `bfeff97…` == tag peel, finalized at merge re-freeze) |
| Code manifest | `0fd86fc994518461172e0893e9b7f92b2eafda777d27c403dfd1b9f25159d0f3` (94 entries; all 94 source-faithful at the freeze commit, incl. both LF locks) |
| Data manifest | `8b859ecc72164fe95c0aa122f8179310ccc6375613543c6702c2ca5867c97b5a` (byte-identical to v0.9.10/v0.9.11) |
| Repository snapshot manifest | `49d91d39435f7e6f2dbf7d15f1a59188aa059ebb16fb31094c7a1827fb62702c` (identical to v0.9.10/v0.9.11) |
| Transport path map | `kaggle_transport_path_map_sha256` `07036a36cd97daef48a39f6490bc055f58e87b336d849a4c1343e82a167cdbce` (identical to v0.9.10/v0.9.11) |
| Archive | `dist/pilot-kaggle-upload.zip` — SHA-256 `5a7d7e0af7bdc3d7ed118542a1d1c65edfa64a852ff71ae6237ed5916b9ca4ed` (validation-enabled rebuild from the tagged merge SHA; deterministic; sidecar matches) |
| Full suite | **2,255 passed / 33 skipped / 0 failed** (2026-08-16) |

The v0.9.12 freeze re-locks the Kaggle deployment source with a fail-closed
source-provenance guarantee: the immutable tag contains exactly the bytes
that were provenance-verified against `identity.source_commit`, and the bundled
code (including both `*.lock` files) is byte-faithful to the source tree. The
tag tree notebook blob `b8d3cf5e…` == the deployed notebook == the freeze
anchor (Notebook == Identity == Actual); identity.source_commit `bfeff97…` ==
tag peel == main HEAD. **Pilot = NOT STARTED.**

## 2. REJECTED — `v0.9.11-pilot-exec-ready` (Saleor source-visibility health-probe fix for real Kaggle)

**REJECTED FOR LAUNCH (superseded by the v0.9.12 release-provenance closure):
internally-valid artifact, but the immutable tag does not contain the deployed
re-frozen notebook and therefore cannot reproduce the claimed source snapshot.
Tag NOT moved.**

| Field | Value |
|---|---|
| Branch | `main` (after `merge(pilot): fix Saleor source-visibility health probe for real Kaggle (v0.9.11-pilot-exec-ready)`; merge `8801304d855fe29c694f2a3c0500f661685b0d72`) |
| Feature branch | `fix/pilot-saleor-source-visibility-probe` (fix `ee3d88b`, docs `228b2e8`); finalizer re-freeze commit `b87aa49` |
| Stable source tag | `v0.9.11-pilot-exec-ready` → peeled commit `8801304d855fe29c694f2a3c0500f661685b0d72` (== main HEAD == the non-ff merge commit; == freeze report `source_commit`, re-verified after tag creation) |
| Prior release (NOT moved) | `v0.9.10-pilot-exec-ready` → `44e9a1f4314c2ce8ec0b7abb16c88cbc3f83bfb6` (immutable; real Kaggle v0.9.10 preflight reached the Saleor post-sync health probe and failed ONLY because the probe did not run from the repository root) |
| Real Kaggle failure + fix | Real v0.9.10 PASSED release trust, transport, runtime lock, repo snapshots, PostgreSQL, Redis, uv tool, django CMS, Saleor copy, Saleor 3.12 venv, `uv sync --locked = PASS`; failed ONLY at `import saleor` probe (exit 1, ModuleNotFoundError). Root cause: pinned Saleor `[tool.uv] package = false` (upstream) → root project never installed into site-packages. Fix: `_import_probe` optional `cwd`; `_saleor_probe` always `cwd=work_dir`; both call sites fixed. NO `package=true`, NO editable install, NO global `PYTHONPATH`. |
| Builder | `scripts/build_pilot_upload_bundle.py` + two-pass deterministic `scripts/finalize_pilot_notebook_trust.py` (`--source-commit 8801304d855fe29c694f2a3c0500f661685b0d72 --source-tag v0.9.11-pilot-exec-ready --created-utc "2026-08-16T12:00:00+00:00"`; local repo cache, NO `--allow-acquire`) |
| Real repo cache | git checkouts at pinned SHAs: django CMS `0f633fc9fa213357f4202482aab2b0edad680f95`, Saleor `e11a5557eff29fbb2eed36e6ff3cd0af08ab9e10` (todo embedded); cat-file checks + `git archive` PASS |
| Deployment contract tests | `tests/integration/test_pilot_repo_env_provisioning.py` (28) + `tests/integration/test_pilot_notebook_contract.py` (44) + `tests/integration/test_pilot_service_bootstrap.py` (41) + `tests/integration/test_pilot_deployment_bundle.py` (61) + `tests/integration/test_pilot_real_launch_preflight.py` (14) — targeted 188 passed; full suite **2,239 passed / 33 skipped / 0 failed** (2026-08-16) |
| Archive | `dist/pilot-kaggle-upload.zip` — SHA-256 `039818bde60edcc9693ca88f779c7987bde818ddbfbca705426747b08c6d5453` (validation-enabled rebuild; deterministic) |
| `pilot_deployment_identity.json` | task `PILOT-EXEC-01`; protocol 1.0; source_commit `8801304d855fe29c694f2a3c0500f661685b0d72`; source_tag `v0.9.11-pilot-exec-ready`; created_utc `2026-08-16T12:00:00+00:00`; model `Qwen/Qwen2.5-Coder-14B-Instruct`; quantization `bnb-nf4`; timeout 600; max_attempts 3; max_completion_tokens_per_call 4096; max_total_workflow_tokens 0; scenario_count 12; strategy_count 2; repetitions 2; expected_cells 48 |
| Notebook trust | deployed SHA-256 `85edbd33e81bb05065c66a1630f75a02043df9fbd0a8f8091b3bff9712181ed0` == bundled archive bytes; source file SHA-256 `a0382061954e5c30215653cde6e59f31919df4b4f680d911d0c4991ef1ac9037`; freeze report `reports/pilot_notebook_trust_freeze.json` (status FROZEN) |
| Code manifest | `7e86eb5dd65122c2714c97ed84f20d8328adbe2b3e838fe6a2218c293ce72adb` (91 entries; helper `scripts/pilot_kaggle_repo_envs.py` changed — the only delta vs v0.9.10) |
| Data manifest | `8b859ecc72164fe95c0aa122f8179310ccc6375613543c6702c2ca5867c97b5a` (57 entries; byte-identical to v0.9.10) |
| Repository snapshot manifest | `49d91d39435f7e6f2dbf7d15f1a59188aa059ebb16fb31094c7a1827fb62702c` (identical to v0.9.10) |
| Transport path map | `kaggle_transport_path_map_sha256` `07036a36cd97daef48a39f6490bc055f58e87b336d849a4c1343e82a167cdbce` (50 exact-path entries; identical to v0.9.10) |
| Dry-run | bundled 48-cell mock dry-run **48/48** terminal / 48 succeeded / 0 failed (todo 16 / djangocms 16 / saleor 16; iterative_repository_agent 24 / selective 24; rep1 24 / rep2 24; 48 unique / 0 missing / 0 duplicate / 0 model calls) |

This freeze re-locked the Kaggle deployment source at `v0.9.11-pilot-exec-ready`
after a REAL two-pass deterministic release-trust-gate finalizer run against
the LOCAL repo cache (NO `--allow-acquire`, no network acquisition).
**Notebook == Identity == Actual proven 4/4** for all four frozen hashes; the
deployed notebook bytes equal the archive bytes; source_tag/peel re-verified.
**REJECTED FOR LAUNCH:** the re-frozen notebook `85edbd33e81b…` landed only in
the POST-tag re-freeze commit `b87aa49`, NOT in the tagged merge commit
`8801304` (which carries the v0.9.10 notebook `d15d86831bf8…`), so the immutable
tag does not contain the deployed notebook. Superseded by v0.9.12. **Pilot =
NOT STARTED.**

---

## 3. Historical — `v0.9.10-pilot-exec-ready` (release trust gate closure, IMMUTABLE)

| Field | Value |
|---|---|
| Branch | `main` (after `merge(pilot): release trust gate closure (notebook==identity==actual, v0.9.10-pilot-exec-ready)`; merge `44e9a1f4314c2ce8ec0b7abb16c88cbc3f83bfb6`) |
| Feature branch | `fix/pilot-release-trust-gate-closure` (fix `097768e`, docs `4ac7f0d`) |
| Stable source tag | `v0.9.10-pilot-exec-ready` → peeled commit `44e9a1f4314c2ce8ec0b7abb16c88cbc3f83bfb6` (== main HEAD == the non-ff merge commit) |
| Historical execution-ready points (NOT moved) | `v0.9.9-pilot-exec-ready` → `f211e4de664da0f0745e5cde5e1fd5138b3172f0`; `v0.9.8-pilot-exec-ready` → `7e0a908588f8b5e0817659518b4e0928ce7c9943`; `v0.9.7-pilot-exec-ready` → `f94853aeff9f32dea9355468eedb74e891e2b9a5`; `v0.9.6-pilot-exec-ready` → `af9b47444fafac260d887dabbe4e3ddc3b22a00f`; `v0.9.5-pilot-exec-ready` → `eb07b7b11d2e7b5ba11bddc71855ddfc6e1d3dab`; `v0.9.4-pilot-exec-ready` → `96b6481a64ba76a74580f5a3d371c39e27df00ea`; `v0.9.3-pilot-exec-ready` → `4fa6e1dfb1a45782d9e5176ef6325405d848b70b`; `v0.9.2-pilot-exec-ready` → `e030be5f4736e22ce40cfa798633b186858b0221` |
| Prior tag (NOT moved) | `v0.9.0-pilot-ready` → `90a4282ac96328e26143b4f98d4bcf520c3c1e9b` (unchanged, immutable) |
| Superseded interim tags (NOT moved) | `v0.9.1-pilot-exec-ready` → `7efdbe60bb195b1f3ca5854fd98057e29559a510` |
| Builder | `scripts/build_pilot_upload_bundle.py` (transport-aware + mandatory pre-upload validator + `validate_bundled_notebook_trust` gate; two-pass deterministic release-trust-gate freeze via `scripts/finalize_pilot_notebook_trust.py`; ships `scripts/pilot_kaggle_repo_envs.py`) |
| Real repo cache | git checkouts at pinned SHAs: django CMS `0f633fc9fa213357f4202482aab2b0edad680f95`, Saleor `e11a5557eff29fbb2eed36e6ff3cd0af08ab9e10` (todo embedded); both cat-file checks PASS; `git archive` works in both cache dirs |
| Deployment contract tests | `tests/integration/test_pilot_repo_env_provisioning.py` (24) + `tests/integration/test_pilot_notebook_contract.py` (46) + `tests/integration/test_pilot_service_bootstrap.py` (41) + `tests/integration/test_pilot_deployment_bundle.py` (52) + `tests/integration/test_pilot_real_launch_preflight.py` (13) — targeted trust-gate closures 142/142; full suite **2,234 passed / 33 skipped / 0 failed** |
| Archive | `dist/pilot-kaggle-upload.zip` — SHA-256 `9df1396d50a99da7b3dd101fefe79013c3c253da8fd65251dbd9eb4650e71436` (sidecar matches; tagged rebuild from the merge SHA; deterministic) |
| `pilot_deployment_identity.json` | task `PILOT-EXEC-01`; protocol 1.0; source_commit `44e9a1f4314c2ce8ec0b7abb16c88cbc3f83bfb6` (tag peel); source_tag `v0.9.10-pilot-exec-ready`; created_utc `2026-08-15T14:00:00+00:00`; model `Qwen/Qwen2.5-Coder-14B-Instruct`; quantization `bnb-nf4`; timeout 600; max_attempts 3; max_completion_tokens_per_call 4096; max_total_workflow_tokens 0; scenario_count 12; strategy_count 2; repetitions 2; expected_cells 48 |
| Notebook trust | deployed SHA-256 `d15d86831bf805e7bcc9e811eb87158b2e4f56732082d1e6326ee9d94ccb81ec` == bundled archive bytes; source file SHA-256 `873e97735cd22b9f7686b56b3d058d1cd01f75513e6a6c8603f1e9dcf70ed71b`; freeze report `reports/pilot_notebook_trust_freeze.json` |
| Code manifest | `bb976f67fefe184796469efcd3f6916fbd592ec9f226b7b0365a237a0ef654d5` (91 entries; VALIDATED value — the v0.9.9 recorded `99688e4e` was stale, it predated the bundled helper-script additions and was never validated against the build) |
| Data manifest | `8b859ecc72164fe95c0aa122f8179310ccc6375613543c6702c2ca5867c97b5a` (57 entries; byte-identical to v0.9.9) |
| Repository snapshot manifest | `49d91d39435f7e6f2dbf7d15f1a59188aa059ebb16fb31094c7a1827fb62702c` (identical to v0.9.9) |
| Transport path map | `kaggle_transport_path_map_sha256` `07036a36cd97daef48a39f6490bc055f58e87b336d849a4c1343e82a167cdbce` (50 exact-path entries; identical to v0.9.9) |

This freeze locks the Kaggle deployment source at `v0.9.10-pilot-exec-ready`
after a REAL two-pass deterministic release-trust-gate finalizer run against
the LOCAL repo cache (`dist/pilot-repo-cache`, NO `--allow-acquire`, no
network acquisition). **Notebook == Identity == Actual proven 4/4**: for every
one of the four frozen manifest/map hashes the notebook `FROZEN_MANIFEST_HASHES`
anchors == the `pilot_deployment_identity.json` binding == the actually-built
bundle bytes == the tracked freeze report. **No scientific inputs changed**;
the no-pip repo-env provisioning (v0.9.9), Redis-compatible per-candidate OS
package fallback (v0.9.8), root-safe unprivileged PostgreSQL bootstrap
(v0.9.7), `kaggle_transport` encoding + `transport-restore-cell` are unchanged.
See `reports/PILOT_EXEC_01_FINAL_REPORT.md` FINAL CLOSURE (v0.9.10) for the
full A–E evidence.

**Frozen launch flags:** `--backend kaggle-qwen --profile pilot
--qwen-quantization bnb-nf4 --max-attempts 3 --protocol-version 1.0
--max-completion-tokens-per-call 4096 --max-total-workflow-tokens 0 --timeout
600 --source-commit 44e9a1f4314c2ce8ec0b7abb16c88cbc3f83bfb6 --source-tag
v0.9.10-pilot-exec-ready --deployed-build-id 44e9a1f --data-dir <bundled data>
--model-path <Kaggle mounted model> --hf-sync` plus the exact HF results repo
ID recorded at launch time. One continuous 48-cell session; no `--max-runs`
subsetting.

**Verified on the frozen bundle (v0.9.10 tagged rebuild):** archive SHA-256
`9df1396d…` (sidecar matches), FINAL ARTIFACT TRUST GATE PASS (Notebook ==
Identity == Actual 4/4; deployed notebook == freeze report `d15d8683…`),
0 unsafe member names / 0 reserved-name components / 50 transport blobs,
roundtrip restore 50/50, all five identity manifest hashes PASS, repo content
hashes PASS (todo `f72bc9df…` 24 files, djangocms `729b5f41…` 1662, saleor
`708d0a7b…` 4577), restored data tree == canonical tree, exact bundled 48-cell
dry-run **48/48 terminal / 48 succeeded / 0 failed / 0 pending / 48 unique run
IDs** (per-repo 16/16/16; per-strategy 24/24; per-rep 24/24; 0 model calls).

---

## 2. Historical — v0.9.9-pilot-exec-ready deployment source identity (superseded by the v0.9.10 release trust gate freeze)

| Field | Value |
|---|---|
| Branch | `main` (after `merge(pilot): no-pip repository env provisioning closure for Kaggle (v0.9.9-pilot-exec-ready)`; merge `44d01028cb3b4576a28c136bad1c2e2f08b7971f`; `FROZEN_SOURCE_TAG` bump `f211e4de664da0f0745e5cde5e1fd5138b3172f0`) |
| Feature branch | `fix/pilot-kaggle-env-provisioning-closure` (fix `28f0405`, docs `fd6353c`) |
| Stable source tag | `v0.9.9-pilot-exec-ready` → peeled commit `f211e4de664da0f0745e5cde5e1fd5138b3172f0` (== main HEAD) |
| Historical execution-ready points (NOT moved) | `v0.9.8-pilot-exec-ready` → `7e0a908588f8b5e0817659518b4e0928ce7c9943`; `v0.9.7-pilot-exec-ready` → `f94853aeff9f32dea9355468eedb74e891e2b9a5`; `v0.9.6-pilot-exec-ready` → `af9b47444fafac260d887dabbe4e3ddc3b22a00f`; `v0.9.5-pilot-exec-ready` → `eb07b7b11d2e7b5ba11bddc71855ddfc6e1d3dab`; `v0.9.4-pilot-exec-ready` → `96b6481a64ba76a74580f5a3d371c39e27df00ea`; `v0.9.3-pilot-exec-ready` → `4fa6e1dfb1a45782d9e5176ef6325405d848b70b`; `v0.9.2-pilot-exec-ready` → `e030be5f4736e22ce40cfa798633b186858b0221` |
| Prior tag (NOT moved) | `v0.9.0-pilot-ready` → `90a4282ac96328e26143b4f98d4bcf520c3c1e9b` (unchanged, immutable) |
| Superseded interim tags (NOT moved) | `v0.9.1-pilot-exec-ready` → `7efdbe60bb195b1f3ca5854fd98057e29559a510` |
| Builder | `scripts/build_pilot_upload_bundle.py` (transport-aware + mandatory pre-upload validator; deterministic single-pass stable-anchor freeze via `scripts/finalize_pilot_notebook_trust.py`; ships `scripts/pilot_kaggle_repo_envs.py`) |
| Real repo cache | git checkouts at pinned SHAs: django CMS `0f633fc9fa213357f4202482aab2b0edad680f95`, Saleor `e11a5557eff29fbb2eed36e6ff3cd0af08ab9e10` (todo embedded) |
| Deployment contract tests | `tests/integration/test_pilot_repo_env_provisioning.py` (24) + `tests/integration/test_pilot_notebook_contract.py` (46) + `tests/integration/test_pilot_service_bootstrap.py` (41) + `tests/integration/test_pilot_deployment_bundle.py` (52) + `tests/integration/test_pilot_real_launch_preflight.py` (13) — full suite **2,225 passed / 33 skipped / 0 failed** |
| Archive | `dist/pilot-kaggle-upload.zip` — SHA-256 `3f93b0a97309ac84250f291a25bad7cf3527bdf1df3a1b40a29f04a5c5f52493` (sidecar matches; repeated identical builds byte-equal; finalize invariance PASS) |
| `pilot_deployment_identity.json` | task `PILOT-EXEC-01`; protocol 1.0; source_commit `f211e4de664da0f0745e5cde5e1fd5138b3172f0` (tag peel); source_tag `v0.9.9-pilot-exec-ready`; created_utc `2026-08-15T12:00:00+00:00`; model `Qwen/Qwen2.5-Coder-14B-Instruct`; quantization `bnb-nf4`; timeout 600; max_attempts 3; max_completion_tokens_per_call 4096; max_total_workflow_tokens 0; scenario_count 12; strategy_count 2; repetitions 2; expected_cells 48 |
| Notebook trust | LF-normalized git blob @ tag == bundled deployed: SHA-256 `e53eca001307db735b7b0e25e83833c326d4ff1a74c4d75870ac1b501a545e1e`; source file SHA-256 `7a6c8c0c0c6e312c8d567ecbda6b5144c843e28671c97971f7fe72e9e40bfd4b`; notebook manifest SHA-256 `f982a2e5bd0be32555ec24367680023396988813d9290a3a375710c0d7760531` (18 cells, incl. no-pip `pilot-repo-preflight-cell`, `service-bootstrap-cell`, `transport-restore-cell`) |
| Code manifest | `99688e4e03291606399126061ae8305bb768a68d10fee0dc43964846272fbe96` (91 entries; byte-identical to v0.9.8 — helper addition hashed, no scientific drift; SUPERSEDED — not validated against the build, the v0.9.10 gate freezes the validated value `bb976f67`) |
| Data manifest | `8b859ecc72164fe95c0aa122f8179310ccc6375613543c6702c2ca5867c97b5a` (57 entries; byte-identical to v0.9.8) |
| Repository snapshot manifest | `49d91d39435f7e6f2dbf7d15f1a59188aa059ebb16fb31094c7a1827fb62702c` (identical to v0.9.8) |
| Transport path map | `kaggle_transport_path_map_sha256` `07036a36cd97daef48a39f6490bc055f58e87b336d849a4c1343e82a167cdbce` (50 exact-path entries) |

The v0.9.9 freeze locked the no-pip repository env provisioning closure
(see `reports/PILOT_EXEC_01_FINAL_REPORT.md` FINAL CLOSURE section for the full
A–E evidence): stdlib venv always `--without-pip`, HOST pip `-m pip --python
<target>` bootstrap, `uv` tool env, django CMS deps via `uv pip install -r`
from the frozen snapshot, Saleor pinned-snapshot copy + `uv venv .venv
--python <existing 3.12>` with `UV_PYTHON_DOWNLOADS=never` + `uv sync
--locked`, markers + health probes, rebuild ONLY the invalid private env dir,
`gettext`+`gcc`+`libpq-dev` in ONE apt transaction (fail closed),
secret-redacting provisioning log, thin-adapter `pilot-repo-preflight-cell`,
bundle-shipped helper (byte-equal + hashed in `code_manifest.json`). **No
scientific inputs changed**; the four frozen manifest/map hashes were
byte-identical to v0.9.8. Superseded by the v0.9.10 release trust gate freeze,
which validated the code manifest hash against the actual build and moved the
deployment source tag to `v0.9.10-pilot-exec-ready`. `v0.9.9-pilot-exec-ready`
is immutable and NOT moved.

## Historical — v0.9.7-pilot-exec-ready deployment source identity (superseded by the v0.9.10 release trust gate freeze)

| Field | Value |
|---|---|
| Branch | `main` (after `merge(pilot): root-safe unprivileged PostgreSQL bootstrap for Kaggle (v0.9.7-pilot-exec-ready)` on `fix/pilot-kaggle-postgres-unprivileged-bootstrap`) |
| Merge commit | `f94853aeff9f32dea9355468eedb74e891e2b9a5` |
| Stable source tag | `v0.9.7-pilot-exec-ready` → peeled commit `f94853aeff9f32dea9355468eedb74e891e2b9a5` |
| Historical execution-ready points (NOT moved) | `v0.9.6-pilot-exec-ready` → `af9b47444fafac260d887dabbe4e3ddc3b22a00f`; `v0.9.5-pilot-exec-ready` → `eb07b7b11d2e7b5ba11bddc71855ddfc6e1d3dab`; `v0.9.4-pilot-exec-ready` → `96b6481a64ba76a74580f5a3d371c39e27df00ea`; `v0.9.3-pilot-exec-ready` → `4fa6e1dfb1a45782d9e5176ef6325405d848b70b`; `v0.9.2-pilot-exec-ready` → `e030be5f4736e22ce40cfa798633b186858b0221` |
| Prior tag (NOT moved) | `v0.9.0-pilot-ready` → `90a4282ac96328e26143b4f98d4bcf520c3c1e9b` (unchanged, immutable) |
| Superseded interim tags (NOT moved) | `v0.9.1-pilot-exec-ready` → `7efdbe60bb195b1f3ca5854fd98057e29559a510` |
| Feature branch (pre-merge) | `fix/pilot-kaggle-postgres-unprivileged-bootstrap` (commits `c06dadf`, `539eb03`, `8e562aa`) |
| Builder | `scripts/build_pilot_upload_bundle.py` (transport-aware + mandatory pre-upload validator; deterministic single-pass stable-anchor freeze via `scripts/finalize_pilot_notebook_trust.py`) |
| Real repo cache | git checkouts at pinned SHAs: django CMS `0f633fc9fa213357f4202482aab2b0edad680f95`, Saleor `e11a5557eff29fbb2eed36e6ff3cd0af08ab9e10` (todo embedded) |
| Deployment contract tests | `tests/integration/test_pilot_service_bootstrap.py` (28) + `tests/integration/test_pilot_notebook_contract.py` (42, incl. 2 root-safe static tests) + `tests/integration/test_pilot_deployment_bundle.py` (51) + `tests/integration/test_pilot_real_launch_preflight.py` (13) — targeted 134/134 |

The last-mile correction closes the real Kaggle blocker: the Kaggle notebook
process runs as root, while PostgreSQL `initdb`/`pg_ctl` refuse root
(`initdb: error: cannot be run as root`), which blocked the v0.9.6 service
bootstrap. The `service-bootstrap-cell` now resolves the package-native
unprivileged `postgres` OS account when the notebook effective uid is 0 and
runs the PostgreSQL server lifecycle (initdb, pg_ctl and the postgres server
it launches) under that account via `subprocess.run(..., user=...)`
(POSIX-only, checked, fail-closed; no `runuser`, no `shell=True`); it FAILS
CLOSED before initdb when the account is missing and NEVER falls back to root;
non-root notebook processes keep the direct path. Ownership/log preparation is
limited to the private service paths (data dir `0o700`, log `0o600`, chown to
the postgres uid/gid; incomplete previous clusters safely recreated, ONLY
`PG_DATA_DIR`). The frozen TCP client probe (psql) still runs from the
notebook process against `127.0.0.1:5433 saleor/saleor/saleor`; Valkey/Redis
`127.0.0.1:6379` unchanged. No scientific inputs changed (scenarios, prompts,
metrics, model, quantization, timeout 600, repair budget, repository pins,
validation scope; the four frozen manifest/map hashes stay byte-identical).

## 2. Historical — Bundle (v0.9.7 tagged rebuild, superseded)

| Field | Value |
|---|---|
| Output root | `dist/pilot-kaggle-upload/` (gitignored) |
| Archive | `dist/pilot-kaggle-upload.zip` |
| Archive SHA-256 | `92a82606a2d0b9b8b5a4c91bfe2416ee5682f2a3d460c901e556d32df467fbd3` (rebuilt from the tag at this closure; verified byte-deterministic across multiple identical builds + finalize invariance check) |
| Sidecar | `dist/pilot-kaggle-upload.zip.sha256` (matches archive hash) |
| ZIP member names | all match `^[A-Za-z0-9._/-]+$` with no `^__.*__$` component (0 unsafe-special-char; 0 reserved-name; 50 transport blobs in `kaggle_transport/files/`) |
| Code files | 91 (manifest SHA-256 `99688e4e03291606399126061ae8305bb768a68d10fee0dc43964846272fbe96` — byte-identical to v0.9.5/v0.9.6, zero scientific drift) |
| Data files | 57 (manifest SHA-256 `8b859ecc72164fe95c0aa122f8179310ccc6375613543c6702c2ca5867c97b5a` — byte-identical to v0.9.5/v0.9.6) |
| Notebook files | 1 (manifest SHA-256 `a9f5fcdf1cd0a59b48780e19123467bf3ec4466e202ad3143497783c922979c7`; notebook content hash `082b4e84688e2bff3ca3e38afb65ab08dc73e2e4a53576b9688422cae8cd6ede` — 18 cells incl. `transport-restore-cell` and the root-safe `service-bootstrap-cell`; byte-identical to the LF-normalized git blob at the tag) |
| Repository snapshot manifest | SHA-256 `49d91d39435f7e6f2dbf7d15f1a59188aa059ebb16fb31094c7a1827fb62702c` (identical to v0.9.5/v0.9.6; pinned repo content unchanged) |
| Transport path map | `kaggle_transport_path_map_sha256` `07036a36cd97daef48a39f6490bc055f58e87b336d849a4c1343e82a167cdbce` (50 exact-path entries) |
| `pilot_deployment_identity.json` | task `PILOT-EXEC-01`; protocol 1.0; source_commit `f94853aeff9f32dea9355468eedb74e891e2b9a5` (tag peel); source_tag `v0.9.7-pilot-exec-ready`; created_utc `2026-08-13T20:00:00+00:00`; model `Qwen/Qwen2.5-Coder-14B-Instruct`; quantization `bnb-nf4`; timeout 600; max_attempts 3; max_completion_tokens_per_call 4096; max_total_workflow_tokens 0; scenario_count 12; strategy_count 2; repetitions 2; expected_cells 48 |
| Notebook trust freeze | `reports/pilot_notebook_trust_freeze.json` (single-pass stable-anchor freeze: FROZEN_SOURCE_TAG `v0.9.7-pilot-exec-ready`, four frozen manifest/map hashes, archive SHA `92a82606…`, deployed notebook SHA `082b4e84…`, source notebook SHA `a763ac4827219669b6ca4a1a8a195fb620fcbd46a4aae6b253ce30b650d8c890`) |

The bundled notebook byte-matches the LF-normalized git blob at the tag and
contains the `transport-restore-cell`, the `service-bootstrap-cell`
(root-safe), the pilot identity/archive verification cells, the model-preflight
cell, and the 48-cell pilot-launch cell. The historical Scientific Smoke bundle
(`kaggle_upload/`) is NOT the Pilot deployment bundle. It remains frozen and
byte-identical.

## 3. Historical — Verification (v0.9.7 tagged rebuild + suite, superseded)

1. **Kaggle-safety:** `dist/pilot-kaggle-upload.zip` has 6396 members, **0
   unsafe member names** under `^[A-Za-z0-9._/-]+$` and **0 reserved-name
   (`^__.*__$`) components** (validator PASS on both planned members and the
   written archive `namelist()`); exactly 50 members are transport blobs under
   `kaggle_transport/files/`; the path map is present and its SHA-256 equals
   the identity binding.
2. **Determinism:** multiple identical builds from the same source commit +
   tag + `created_utc` + repo cache produced byte-identical archives (SHA-256
   `92a82606…` every time, including the finalize invariance rebuild); the
   transport blob names are content-hash-derived, so the encoding is
   deterministic.
3. **Reversibility (roundtrip):** extract the archive to a fresh dir, run the
   actual `transport-restore-cell` from the bundled notebook → 50/50 restored
   to EXACT original paths and bytes; `kaggle_transport/` fully removed; the
   restored repository content hashes PASS: todo `f72bc9df58882261eb2a2724e358b477cf68ed9586821d0cd2d9d8a47829113f` (24 files), djangocms `729b5f418ec79d06b20e6e78ce827d58cde6812622f6e600c63777457b05247e` (1662), saleor `708d0a7bfeddb92a441e5d1d047ba6d5cdf373bdb9978a8d22ee4622055ccc73` (4577) — identical to v0.9.5/v0.9.6; restored data tree == canonical tree.
4. **Identity contract:** `pilot_deployment_identity.json` holds the frozen
   values (section 2); code/data/notebook/repository-snapshot manifest hashes
   and the transport map hash match the emitted bundle bytes and the notebook
   `FROZEN_MANIFEST_HASHES` anchors.
5. **Bundled exact 48-cell dry-run** (fresh output dir, mock backend, bundled
   CLI at `dist/pilot-kaggle-upload/code/seven_arm_benchmark.py`, bundled data
   at `dist/pilot-kaggle-upload/data`):
   **48/48 terminal / 48 succeeded / 0 failed / 0 pending / 48 unique run
   IDs**; profile `pilot`; per-repo todo 16 / djangocms 16 / saleor 16;
   per-strategy iterative_repository_agent 24 / selective 24; per-rep 24 / 24;
   0 model calls / 0 tokens.
6. **Gates on the correction:** service bootstrap 28/28; notebook contract
   42/42; deployment bundle contract 51/51; real-launch preflight 13/13
   (targeted 134/134); full suite **2,185 passed / 33 skipped / 0 failed**;
   `git diff --check`, ruff, mypy strict, py_compile clean.

## 4. Historical — Launch flags frozen for every real Pilot invocation (v0.9.7, superseded)

`--backend kaggle-qwen --profile pilot --qwen-quantization bnb-nf4
--max-attempts 3 --protocol-version 1.0 --max-completion-tokens-per-call 4096
--max-total-workflow-tokens 0 --timeout 600 --source-commit
f94853aeff9f32dea9355468eedb74e891e2b9a5 --source-tag v0.9.7-pilot-exec-ready
--deployed-build-id f94853a --data-dir <bundled data> --model-path <Kaggle
mounted model> --hf-sync` plus the exact HF results repo ID recorded at launch
time. One continuous 48-cell session; no `--max-runs` subsetting.

## 5. Historical — Post-freeze gate plan (root-safe bootstrap correction evidence, superseded)

- [x] `service-bootstrap-cell` corrected to run initdb/pg_ctl/postgres under
      the package-native unprivileged `postgres` account when euid==0
      (`subprocess.run(..., user=...)`, POSIX-only, fail-closed before initdb,
      no `runuser`, no `shell=True`, NEVER falls back to root); notebook
      `FROZEN_SOURCE_TAG` → `v0.9.7-pilot-exec-ready`.
- [x] Hermetic Gate-H contract `test_pilot_service_bootstrap.py` (28) execs
      the EXACT cell definitions with os/pwd/subprocess/socket fakes (root
      mode, non-root mode, missing account, partial cluster, proof semantics);
      notebook contract (42) + deployment bundle contract (51) + preflight (13)
      green; full suite **2,185 passed / 33 skipped / 0 failed**.
- [x] Correction committed (`c06dadf`, `539eb03`, `8e562aa`) on
      `fix/pilot-kaggle-postgres-unprivileged-bootstrap`; branch pushed;
      local == remote.
- [x] Non-fast-forward merge to `main`; pushed; local == origin/main
      (`f94853aeff9f32dea9355468eedb74e891e2b9a5`).
- [x] Tag `v0.9.7-pilot-exec-ready` created + pushed (annotated object; peels
      to the merge commit); `v0.9.0`/`v0.9.1`/`v0.9.2`/`v0.9.3`/`v0.9.4`/
      `v0.9.5`/`v0.9.6` NOT moved.
- [x] Bundle rebuilt from the tagged source (`--source-commit
      f94853aeff9f32dea9355468eedb74e891e2b9a5 --source-tag
      v0.9.7-pilot-exec-ready --created-utc 2026-08-13T20:00:00+00:00` with the
      real repo cache) and re-verified: archive SHA-256
      `92a82606a2d0b9b8b5a4c91bfe2416ee5682f2a3d460c901e556d32df467fbd3`
      (sidecar matches; repeated identical builds byte-equal; finalize
      invariance PASS), 0 unsafe members / 0 reserved-name components,
      roundtrip restore 50/50, all five identity manifest hashes PASS, repo
      content hashes PASS, exact 48-cell bundled dry-run 48/48.
- [x] Exact Kaggle launch commands + evidence prepared (runtime identity
      preflight, bundled 48-cell dry-run, transport restore, root-safe service
      bootstrap, model-load preflight, real launch).
- [x] Final closure report recorded.

**Pilot = NOT STARTED.** Real launch is deferred until the user confirms the
actual Kaggle mounted model path (e.g. `/kaggle/input/<model-slug>`) and the
exact HF results repository ID. Next action: upload the exact
`dist/pilot-kaggle-upload.zip` + `dist/pilot-kaggle-upload.zip.sha256` as ONE
Kaggle Dataset, attach the Pilot notebook + Qwen 14B model, enable Internet,
configure `HF_TOKEN`, then run cells in order through target preflight. Only
after all preflight gates pass may the real 48-cell cell be executed.

---

## Historical record (superseded 2026-08-13)

### v0.9.6-pilot-exec-ready — dual fail-closed Kaggle input modes + stable-anchor freeze (superseded by this root-safe freeze)

The 2026-08-13 freeze on `v0.9.6-pilot-exec-ready`
(`af9b47444fafac260d887dabbe4e3ddc3b22a00f`, merge of `46dbfd4` +
`4d8d87a`) replaced the mathematically unsound hash-fixpoint finalizer (archive
SHA and notebook-manifest SHA each hash content that includes the notebook
bytes that would embed the value, so no embedded value can equal its own hash)
with a deterministic single-pass stable-anchor freezer: the notebook now
freezes ONLY notebook-independent anchors (FROZEN_SOURCE_TAG, FROZEN_DEPLOYMENT,
and the four stable manifest/map hashes — code, data, repository snapshot,
transport path map); archive SHA and notebook-manifest SHA are verified
self-consistently at runtime in BOTH Kaggle input modes (archive mode: actual
ZIP SHA must equal the sidecar; auto-expanded mount mode: sidecar is
provenance-only and the mounted tree is trusted against the frozen anchors plus
self-consistent notebook-manifest verification before copy). FROZEN_SOURCE_COMMIT
is not embedded; deployed source_commit equals the tag peel and is recorded in
`reports/pilot_notebook_trust_freeze.json`. Archive SHA-256
`afca4205583ccca1c29e7fb846993f944210805d676d509f1624985da36b16b8`; created_utc
`2026-08-13T18:00:00+00:00`; full suite 2,156 passed / 33 skipped / 0 failed.
It was superseded because the real Kaggle session exposed the PostgreSQL
`cannot be run as root` blocker in the service-bootstrap cell. The deployment
source tag moved from `v0.9.6-pilot-exec-ready` to `v0.9.7-pilot-exec-ready`
(this freeze). `v0.9.6-pilot-exec-ready` is immutable and NOT moved.

### v0.9.5-pilot-exec-ready — reserved-name transport freeze (superseded)

The 2026-08-13 freeze on `v0.9.5-pilot-exec-ready`
(`eb07b7b11d2e7b5ba11bddc71855ddfc6e1d3dab`) covered the KAGGLE RESERVED-NAME
TRANSPORT correction: Kaggle rejects any path component matching `^__.*__$`,
and the v0.9.4 transport root `__kaggle_transport__` itself matched that
reserved `__name__` pattern. The transport root became `kaggle_transport`
everywhere (builder, notebook `transport-restore-cell`, the exact-path map
contract, tests, runbook/contract docs) with a MANDATORY pre-upload archive
validator (`validate_archive_members_kaggle_ready`) scanning EVERY ZIP member
and failing closed on any unsafe-special-char or reserved-name component.
Archive SHA-256 `7be899d1398b7e7061dd98d7d8d710482bfe3f1f66f1663be26dce7de7e0997a`;
transport map hash `07036a36…`; created_utc `2026-08-13T12:00:00+00:00`; full
suite 2,125 passed / 33 skipped / 0 failed. Superseded by the v0.9.6
stable-anchor freeze. `v0.9.5-pilot-exec-ready` is immutable and NOT moved.

### v0.9.4-pilot-exec-ready — filename transport freeze (superseded)

The 2026-08-13 freeze on `v0.9.4-pilot-exec-ready`
(`96b6481a64ba76a74580f5a3d371c39e27df00ea`) covered the KAGGLE FILENAME
TRANSPORT correction: reversible transport encoding (unsafe `[ ] & @ =` names
stored as content-hash blobs under `__kaggle_transport__/files/` with the
exact-path map) plus ONE `transport-restore-cell`. Archive SHA-256
`be98be8d2f0696bf8e916afbee7e83dd4522594e24f8f9f7c4837e008aaf8a19`; transport
map hash `a5c1e2cb…`; created_utc `2026-08-13T00:00:00+00:00`; full suite
2,119 passed / 33 skipped / 0 failed. It was superseded because Kaggle rejects
any path component matching `^__.*__$`, and the v0.9.4 transport root
`__kaggle_transport__` itself matched that reserved `__name__` pattern.
`v0.9.4-pilot-exec-ready` is immutable and NOT moved.

### v0.9.3-pilot-exec-ready — service-bootstrap freeze (superseded)

The 2026-08-13 freeze on `v0.9.3-pilot-exec-ready`
(`4fa6e1dfb1a45782d9e5176ef6325405d848b70b`) covered the KAGGLE SERVICE
BOOTSTRAP last-mile correction: ONE fail-closed, idempotent
`service-bootstrap-cell` added to the frozen Pilot notebook (PostgreSQL
`127.0.0.1:5433`, Valkey/Redis `127.0.0.1:6379`, before repository validation
and model load). Archive SHA-256
`27e9cd612b33ebc433dafb7a42b7ebe2149f560bc6b73f16b969d3031a6baae1`; code
manifest `99688e4e…`, data manifest `8b859ecc…`, notebook manifest
`64cb33b9c800b8ac2fc38b71fff4290474a192137f982a5a5d0892e0728a7a0c`,
repository snapshot manifest `49d91d39…`; created_utc `2026-08-13T07:15:24+00:00`;
full suite 2,098 passed / 33 skipped / 0 failed. It was superseded because
Kaggle rejected the upload: 50 ZIP member names from the pinned upstream repos
(45 Saleor, 5 django CMS) contain `[ ] & @ =`, which Kaggle does not accept.
`v0.9.3-pilot-exec-ready` is immutable and NOT moved.

### v0.9.2-pilot-exec-ready — real-launch closure freeze (superseded)

The 2026-08-13 freeze on `v0.9.2-pilot-exec-ready`
(`e030be5f4736e22ce40cfa798633b186858b0221`) covered the real-launch closure
(Gates 9/10: saleor `TZ=UTC` freeze + Gate 9 preflight ledger + hermetic
repo-snapshot/preflight gates; archive SHA-256
`ecb7ea7c85d8bdc527a0384f141b47a1e84ee0b3c3f12b6b8305d880098015f1`). It was
superseded by the service-bootstrap correction because a fresh Kaggle session
has no PostgreSQL/Valkey OS services.

### v0.9.1-pilot-exec-ready — pre-execution freeze (superseded)

The 2026-08-10 freeze on `v0.9.1-pilot-exec-ready`
(`7efdbe60bb195b1f3ca5854fd98057e29559a510`) covered the pre-execution gates
(deployment bundle + pre-registration).
