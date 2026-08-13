# PILOT-EXEC-01 — Deployment Freeze Report

**Date:** 2026-08-13 (Kaggle reserved-name transport correction freeze;
supersedes the 2026-08-13 filename-transport freeze on
`v0.9.4-pilot-exec-ready`, which superseded the 2026-08-13 service-bootstrap
freeze on `v0.9.3-pilot-exec-ready`, which superseded the 2026-08-13 freeze on
`v0.9.2-pilot-exec-ready`, which superseded the 2026-08-10 freeze on
`v0.9.1-pilot-exec-ready`)
**Task:** `PILOT-EXEC-01` (Pilot deployment + KAGGLE RESERVED-NAME TRANSPORT
last-mile correction)
**Status:** FROZEN (Pilot deployment locked; Pilot execution NOT STARTED)

---

## 1. Deployment source identity

| Field | Value |
|---|---|
| Branch | `main` (after `merge(pilot): Kaggle reserved-name transport correction …` on `fix/pilot-kaggle-reserved-transport-name`) |
| Merge commit | `eb07b7b11d2e7b5ba11bddc71855ddfc6e1d3dab` |
| Stable source tag | `v0.9.5-pilot-exec-ready` → peeled commit `eb07b7b11d2e7b5ba11bddc71855ddfc6e1d3dab` |
| Historical execution-ready points (NOT moved) | `v0.9.4-pilot-exec-ready` → `96b6481a64ba76a74580f5a3d371c39e27df00ea`; `v0.9.3-pilot-exec-ready` → `4fa6e1dfb1a45782d9e5176ef6325405d848b70b`; `v0.9.2-pilot-exec-ready` → `e030be5f4736e22ce40cfa798633b186858b0221` |
| Prior tag (NOT moved) | `v0.9.0-pilot-ready` → `90a4282ac96328e26143b4f98d4bcf520c3c1e9b` (unchanged, immutable) |
| Superseded interim tags (NOT moved) | `v0.9.1-pilot-exec-ready` → `7efdbe60bb195b1f3ca5854fd98057e29559a510` |
| Feature branch (pre-merge) | `fix/pilot-kaggle-reserved-transport-name` (commits `189cc60`, `99348d1`) |
| Builder | `scripts/build_pilot_upload_bundle.py` (transport-aware + mandatory pre-upload validator) |
| Real repo cache | git checkouts at pinned SHAs: django CMS `0f633fc9fa213357f4202482aab2b0edad680f95`, Saleor `e11a5557eff29fbb2eed36e6ff3cd0af08ab9e10` (todo embedded) |
| Deployment contract tests | `tests/integration/test_pilot_notebook_contract.py` (28, incl. reserved-name transport-root assertion) + `tests/integration/test_pilot_deployment_bundle.py` (33, incl. 19 `TestPilotKaggleTransport` tests) — targeted 61/61 |

The last-mile corrections made the frozen Pilot archive Kaggle-upload-safe.
Kaggle rejects Dataset/ZIP member names containing `[ ] & @ =` and reserves
any path component matching `^__.*__$`; the pinned upstream repos contain 50
such filename-unsafe files (45 Saleor, 5 django CMS) and the v0.9.4 transport
root `__kaggle_transport__` itself matched Kaggle's reserved `__name__`
pattern and was rejected. The corrections add a reversible TRANSPORT ENCODING
to `scripts/build_pilot_upload_bundle.py` (member names restricted to
`^[A-Za-z0-9._/-]+$` with NO reserved `__name__` component; transport root
`kaggle_transport`; unsafe files stored under
`kaggle_transport/files/<deterministic-blob>` with the exact-path map
`kaggle_transport/kaggle_transport_path_map.json`, whose SHA-256 is bound
into `pilot_deployment_identity.json` as `kaggle_transport_path_map_sha256`;
a mandatory pre-upload validator (`validate_archive_members_kaggle_ready`)
scans EVERY ZIP member and fails closed on any unsafe-special-char or
reserved-name component) and ONE `transport-restore-cell` to the frozen Pilot
notebook (`notebooks/pilot_exec_01.ipynb`, now 18 cells) between archive
verification and identity verification. The cell verifies the map hash
against the identity, rejects traversal/drive/`..` destinations, destination
collisions, missing blobs, and leftover blobs, restores the EXACT original
paths and bytes, removes `kaggle_transport/`, and prints
`PILOT KAGGLE TRANSPORT RESTORE: PASSED` BEFORE any manifest or repository
verification. Canonical upstream filenames are NEVER renamed or deleted; the
encoding exists only inside the ZIP and inside the notebook restore step.
No scientific inputs changed (scenarios, prompts, metrics, model,
quantization, timeout 600, repair budget, repository pins, validation scope).

## 2. Bundle (built from the tagged source)

| Field | Value |
|---|---|
| Output root | `dist/pilot-kaggle-upload/` (gitignored) |
| Archive | `dist/pilot-kaggle-upload.zip` |
| Archive SHA-256 | `7be899d1398b7e7061dd98d7d8d710482bfe3f1f66f1663be26dce7de7e0997a` (rebuilt from the tag at this closure; verified byte-deterministic across two identical builds) |
| Sidecar | `dist/pilot-kaggle-upload.zip.sha256` (matches archive hash) |
| ZIP member names | all match `^[A-Za-z0-9._/-]+$` with no `^__.*__$` component (0 unsafe-special-char; 0 reserved-name; 50 transport blobs in `kaggle_transport/files/`) |
| Code files | 91 (manifest SHA-256 `99688e4e03291606399126061ae8305bb768a68d10fee0dc43964846272fbe96` — byte-identical to v0.9.4, zero scientific drift) |
| Data files | 57 (manifest SHA-256 `8b859ecc72164fe95c0aa122f8179310ccc6375613543c6702c2ca5867c97b5a` — byte-identical to v0.9.4) |
| Notebook files | 1 (manifest SHA-256 `052efe08e0f942abac367f90a0f7073a9ba724e97cb3ebb9ccbae16816890cad`; notebook content hash `8b0ef4892345cbd8760085d578e055045a11d881985d1fe5c845c3f35807e9ba` — 18 cells incl. `transport-restore-cell`; byte-identical to the git blob at the tag) |
| Repository snapshot manifest | SHA-256 `49d91d39435f7e6f2dbf7d15f1a59188aa059ebb16fb31094c7a1827fb62702c` (identical to v0.9.4; pinned repo content unchanged) |
| Transport path map | `kaggle_transport_path_map_sha256` `07036a36cd97daef48a39f6490bc055f58e87b336d849a4c1343e82a167cdbce` (50 exact-path entries) |
| `pilot_deployment_identity.json` | task `PILOT-EXEC-01`; protocol 1.0; source_commit `eb07b7b11d2e7b5ba11bddc71855ddfc6e1d3dab` (tag peel); source_tag `v0.9.5-pilot-exec-ready`; created_utc `2026-08-13T12:00:00+00:00`; model `Qwen/Qwen2.5-Coder-14B-Instruct`; quantization `bnb-nf4`; timeout 600; max_attempts 3; max_completion_tokens_per_call 4096; max_total_workflow_tokens 0; scenario_count 12; strategy_count 2; repetitions 2; expected_cells 48 |

The bundled notebook byte-matches the git blob at the tag and contains the
`transport-restore-cell` and the `service-bootstrap-cell`. The historical
Scientific Smoke bundle (`kaggle_upload/`) is NOT the Pilot deployment bundle.
It remains frozen and byte-identical.

## 3. Verification performed on the frozen bundle (v0.9.5 tagged rebuild + suite)

1. **Kaggle-safety:** `dist/pilot-kaggle-upload.zip` has 6396 members, **0
   unsafe member names** under `^[A-Za-z0-9._/-]+$` and **0 reserved-name
   (`^__.*__$`) components** (validator PASS on both planned members and the
   written archive `namelist()`); exactly 50 members are transport blobs under
   `kaggle_transport/files/`; the path map is present and its SHA-256 equals
   the identity binding.
2. **Determinism:** two identical builds from the same source commit + tag +
   `created_utc` + repo cache produced byte-identical archives (SHA-256
   `7be899d1…` both times); the transport blob names are content-hash-derived,
   so the encoding is deterministic.
3. **Reversibility (roundtrip):** extract the archive to a fresh dir, run the
   actual `transport-restore-cell` from the bundled notebook → 50/50 restored
   to EXACT original paths and bytes; `kaggle_transport/` fully removed; the
   restored repository content hashes PASS: todo `f72bc9df58882261eb2a2724e358b477cf68ed9586821d0cd2d9d8a47829113f` (24 files), djangocms `729b5f418ec79d06b20e6e78ce827d58cde6812622f6e600c63777457b05247e` (1662), saleor `708d0a7bfeddb92a441e5d1d047ba6d5cdf373bdb9978a8d22ee4622055ccc73` (4577) — identical to v0.9.4; restored data tree == canonical tree.
4. **Identity contract:** `pilot_deployment_identity.json` holds the frozen
   values (section 2); code/data/notebook/repository-snapshot manifest hashes
   and the transport map hash match the emitted bundle bytes.
5. **Bundled exact 48-cell dry-run** (fresh output dir, mock backend, bundled
   CLI at `dist/pilot-kaggle-upload/code/seven_arm_benchmark.py`):
   **48/48 terminal / 48 succeeded / 0 failed / 0 pending / 48 unique run
   IDs**; profile `pilot`; per-repo todo 16 / djangocms 16 / saleor 16;
   per-strategy iterative_repository_agent 24 / selective 24.
6. **Gates on the correction:** notebook contract 28/28; deployment bundle
   contract 33/33 (targeted 61/61); full suite **2,125 passed /
   33 skipped / 0 failed**; `git diff --check`, ruff, mypy strict, py_compile
   clean.

## 4. Launch flags frozen for every real Pilot invocation

`--backend kaggle-qwen --profile pilot --qwen-quantization bnb-nf4
--max-attempts 3 --max-completion-tokens-per-call 4096
--max-total-workflow-tokens 0 --timeout 600 --source-commit
eb07b7b11d2e7b5ba11bddc71855ddfc6e1d3dab --source-tag v0.9.5-pilot-exec-ready
--hf-sync` plus the exact model path and HF results repo ID recorded at launch
time. One
continuous 48-cell session; no `--max-runs` subsetting.

## 5. Post-freeze gate plan (reserved-name correction evidence)

- [x] `transport-restore-cell` added to the frozen Pilot notebook (fail-closed:
      identity-bound map hash, traversal/drive/`..` rejection, destination
      collision rejection, missing-blob rejection, no leftover blob; restores
      exact paths/bytes before manifest/repo verification; removes transport
      dir).
- [x] Notebook contract (28) + deployment bundle contract (33, incl. 8 new
      reserved-name/validator cases in `TestPilotKaggleTransport`), full suite
      2,125/33/0 all green.
- [x] Correction committed (`189cc60`, `99348d1`) on
      `fix/pilot-kaggle-reserved-transport-name`; branch pushed; local == remote.
- [x] Non-fast-forward merge to `main`; pushed; local == origin/main
      (`eb07b7b11d2e7b5ba11bddc71855ddfc6e1d3dab`).
- [x] Tag `v0.9.5-pilot-exec-ready` created + pushed (annotated object
      `b99fe9b9f426fc3fe7b269c448d9737e3f20cd4c`; peels to the merge commit);
      `v0.9.0`/`v0.9.1`/`v0.9.2`/`v0.9.3`/`v0.9.4` NOT moved.
- [x] Bundle rebuilt from the tagged source (`--source-commit
      eb07b7b11d2e7b5ba11bddc71855ddfc6e1d3dab --source-tag
      v0.9.5-pilot-exec-ready --created-utc 2026-08-13T12:00:00+00:00` with the
      real repo cache) and re-verified: archive SHA-256
      `7be899d1398b7e7061dd98d7d8d710482bfe3f1f66f1663be26dce7de7e0997a`
      (sidecar matches; second identical build byte-equal), 0 unsafe members /
      0 reserved-name components, roundtrip restore 50/50, all five identity
      manifest hashes PASS, repo content hashes PASS, exact 48-cell bundled
      dry-run 48/48.
- [x] Exact Kaggle launch commands + evidence prepared (runtime identity
      preflight, bundled 48-cell dry-run, transport restore, service bootstrap,
      model-load preflight, real launch).
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

### v0.9.4-pilot-exec-ready — filename transport freeze (superseded by this reserved-name freeze)

The 2026-08-13 freeze on `v0.9.4-pilot-exec-ready`
(`96b6481a64ba76a74580f5a3d371c39e27df00ea`, annotated tag object
`b48537928d3313624fbdbba1a1a69709356a561f`) covered the KAGGLE FILENAME
TRANSPORT correction: reversible transport encoding (unsafe `[ ] & @ =` names
stored as content-hash blobs under `__kaggle_transport__/files/` with the
exact-path map) plus ONE `transport-restore-cell`. Archive SHA-256
`be98be8d2f0696bf8e916afbee7e83dd4522594e24f8f9f7c4837e008aaf8a19`; transport
map hash `a5c1e2cb…`; created_utc `2026-08-13T00:00:00+00:00`; full suite
2,119 passed / 33 skipped / 0 failed. It was superseded because Kaggle rejects
any path component matching `^__.*__$`, and the v0.9.4 transport root
`__kaggle_transport__` itself matched that reserved `__name__` pattern. The
deployment source tag moved to `v0.9.5-pilot-exec-ready` (this freeze).
`v0.9.4-pilot-exec-ready` is immutable and NOT moved.

### v0.9.3-pilot-exec-ready — service-bootstrap freeze (superseded by this transport freeze)

The 2026-08-13 freeze on `v0.9.3-pilot-exec-ready`
(`4fa6e1dfb1a45782d9e5176ef6325405d848b70b`, annotated tag object `47a65ef`)
covered the KAGGLE SERVICE BOOTSTRAP last-mile correction: ONE fail-closed,
idempotent `service-bootstrap-cell` added to the frozen Pilot notebook
(PostgreSQL `127.0.0.1:5433`, Valkey/Redis `127.0.0.1:6379`, before repository
validation and model load). Archive SHA-256
`27e9cd612b33ebc433dafb7a42b7ebe2149f560bc6b73f16b969d3031a6baae1`; code
manifest `99688e4e…`, data manifest `8b859ecc…`, notebook manifest
`64cb33b9c800b8ac2fc38b71fff4290474a192137f982a5a5d0892e0728a7a0c`,
repository snapshot manifest `49d91d39…`; created_utc `2026-08-13T07:15:24+00:00`;
full suite 2,098 passed / 33 skipped / 0 failed. It was superseded because
Kaggle rejected the upload: 50 ZIP member names from the pinned upstream repos
(45 Saleor, 5 django CMS) contain `[ ] & @ =`, which Kaggle does not accept.
The deployment source tag moved from `v0.9.3-pilot-exec-ready` to
`v0.9.4-pilot-exec-ready` (this freeze). `v0.9.3-pilot-exec-ready` is
immutable and NOT moved.

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
