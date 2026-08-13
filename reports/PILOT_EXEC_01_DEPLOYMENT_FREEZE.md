# PILOT-EXEC-01 — Deployment Freeze Report

**Date:** 2026-08-13 (service-bootstrap correction freeze; supersedes the
2026-08-13 freeze on `v0.9.2-pilot-exec-ready`, which in turn superseded the
2026-08-10 freeze on `v0.9.1-pilot-exec-ready`)
**Task:** `PILOT-EXEC-01` (Pilot deployment + KAGGLE SERVICE BOOTSTRAP
last-mile correction)
**Status:** FROZEN (Pilot deployment locked; Pilot execution NOT STARTED)

---

## 1. Deployment source identity

| Field | Value |
|---|---|
| Branch | `main` (after `merge(pilot): Kaggle service bootstrap last-mile correction …`) |
| Merge commit | `4fa6e1dfb1a45782d9e5176ef6325405d848b70b` |
| Stable source tag | `v0.9.3-pilot-exec-ready` → peeled commit `4fa6e1dfb1a45782d9e5176ef6325405d848b70b` |
| Historical execution-ready point (NOT moved) | `v0.9.2-pilot-exec-ready` → `e030be5f4736e22ce40cfa798633b186858b0221` |
| Prior tag (NOT moved) | `v0.9.0-pilot-ready` → `90a4282ac96328e26143b4f98d4bcf520c3c1e9b` (unchanged, immutable) |
| Superseded interim tag | `v0.9.1-pilot-exec-ready` → `7efdbe60bb195b1f3ca5854fd98057e29559a510` (pre-execution gates only; NOT the real-launch source) |
| Feature branch (pre-merge) | `fix/pilot-kaggle-service-bootstrap` (commits `d40feb2`, `37486f8`, merged at `4fa6e1d`) |
| Builder | `scripts/build_pilot_upload_bundle.py` |
| Real repo cache | git checkouts at pinned SHAs: django CMS `0f633fc9fa213357f4202482aab2b0edad680f95`, Saleor `e11a5557eff29fbb2eed36e6ff3cd0af08ab9e10` (todo embedded) |
| Deployment contract tests | `tests/integration/test_pilot_notebook_contract.py` (20, incl. 5 new service-bootstrap tests) + `tests/integration/test_pilot_deployment_bundle.py` (14) |

The last-mile correction added ONE fail-closed, idempotent
`service-bootstrap-cell` to the frozen Pilot notebook
(`notebooks/pilot_exec_01.ipynb`, now 17 cells) between repository snapshot
verification and the repo-specific preflight — BEFORE any repository
validation and model load. It provisions the Saleor validation OS services on
a fresh Kaggle session: PostgreSQL `127.0.0.1:5433` (role/db
`saleor/saleor@saleor`, private data dir `/kaggle/working/pilot_services/postgres`,
`pg_config --bindir` preferred) and Valkey/Redis `127.0.0.1:6379`
(persistence disabled); OS installs non-interactive via apt-get (Kaggle
Internet ON required, fail loudly offline); never modifies the benchmark/model
Python environment; prints no secrets beyond the frozen non-secret test
credentials. No scientific inputs changed.

## 2. Bundle (built from the tagged source)

| Field | Value |
|---|---|
| Output root | `dist/pilot-kaggle-upload/` (gitignored) |
| Archive | `dist/pilot-kaggle-upload.zip` |
| Archive SHA-256 | `27e9cd612b33ebc433dafb7a42b7ebe2149f560bc6b73f16b969d3031a6baae1` |
| Sidecar | `dist/pilot-kaggle-upload.zip.sha256` (matches archive hash) |
| Code files | 91 (manifest SHA-256 `99688e4e03291606399126061ae8305bb768a68d10fee0dc43964846272fbe96` — byte-identical to v0.9.2, zero scientific drift) |
| Data files | 57 (manifest SHA-256 `8b859ecc72164fe95c0aa122f8179310ccc6375613543c6702c2ca5867c97b5a` — byte-identical to v0.9.2) |
| Notebook files | 1 (manifest SHA-256 `64cb33b9c800b8ac2fc38b71fff4290474a192137f982a5a5d0892e0728a7a0c`) |
| Repository snapshot manifest | SHA-256 `49d91d39435f7e6f2dbf7d15f1a59188aa059ebb16fb31094c7a1827fb62702c` |
| `pilot_deployment_identity.json` | task `PILOT-EXEC-01`; protocol 1.0; source_commit `4fa6e1dfb1a45782d9e5176ef6325405d848b70b`; source_tag `v0.9.3-pilot-exec-ready`; model `Qwen/Qwen2.5-Coder-14B-Instruct`; quantization `bnb-nf4`; timeout 600; max_attempts 3; max_completion_tokens_per_call 4096; max_total_workflow_tokens 0; scenario_count 12; strategy_count 2; repetitions 2; expected_cells 48; created_utc `2026-08-13T07:15:24+00:00` |

The bundled notebook byte-matches the LF-normalized git blob at the tag
(SHA-256 `8378edf542bb0ed12b29bc5498fd8f5d0e550319154c59f7c097c2b032349089`)
and contains the `service-bootstrap-cell`. The historical Scientific Smoke
bundle (`kaggle_upload/`) is NOT the Pilot deployment bundle. It remains
frozen and byte-identical.

## 3. Verification performed on the frozen bundle

1. **Determinism:** bundle rebuilt deterministically from the tagged source
   (`--source-commit 4fa6e1dfb1a45782d9e5176ef6325405d848b70b
   --source-tag v0.9.3-pilot-exec-ready
   --created-utc 2026-08-13T07:15:24+00:00`) with the real repo cache; the
   rebuild is byte-identical for identical inputs.
2. **Archive integrity:** `dist/pilot-kaggle-upload.zip` SHA-256 == sidecar ==
   `27e9cd612b33ebc433dafb7a42b7ebe2149f560bc6b73f16b969d3031a6baae1`;
   archive contains the notebook + three repos (todo embedded, django CMS,
   Saleor) with no `.git` directories.
3. **Identity contract:** `pilot_deployment_identity.json` holds the frozen
   values (section 2) and code/data/notebook/repository-snapshot manifest
   hashes match the emitted bundle bytes.
4. **Bundled exact 48-cell dry-run** (fresh output dir, mock backend, bundled
   CLI at `dist/pilot-kaggle-upload/code/seven_arm_benchmark.py`):
   **48/48 terminal / 48 succeeded / 0 failed / 0 pending / 48 unique run
   IDs**; profile `pilot`; source_commit `4fa6e1d`; per-repo todo 16 /
   djangocms 16 / saleor 16; per-strategy iterative_repository_agent 24 /
   selective 24; per-rep 24 / 24.
5. **Gates on the correction:** notebook contract 20/20; deployment bundle
   contract 14/14; targeted pilot gates 77/77; full suite **2,098 passed /
   33 skipped / 0 failed**; `git diff --check`, ruff, mypy strict, py_compile
   clean.

## 4. Launch flags frozen for every real Pilot invocation

`--backend kaggle-qwen --profile pilot --qwen-quantization bnb-nf4
--max-attempts 3 --max-completion-tokens-per-call 4096
--max-total-workflow-tokens 0 --timeout 600 --source-commit
4fa6e1dfb1a45782d9e5176ef6325405d848b70b --source-tag v0.9.3-pilot-exec-ready
--hf-sync` plus the exact model path and HF results repo ID recorded at launch
time. One continuous 48-cell session; no `--max-runs` subsetting.

## 5. Post-freeze gate plan (service-bootstrap correction evidence)

- [x] `service-bootstrap-cell` added to the frozen Pilot notebook (fail-closed,
      idempotent; Postgres 5433 + Valkey/Redis 6379; before repository
      validation and model load).
- [x] Notebook contract (+5 service-bootstrap tests), deployment bundle
      contract, targeted pilot gates, full suite 2,098/33/0 all green.
- [x] Correction committed (`d40feb2`) and docs committed (`37486f8`) on
      `fix/pilot-kaggle-service-bootstrap`; branch pushed; local == remote.
- [x] Non-fast-forward merge to `main` at `4fa6e1d`; pushed; local ==
      origin/main.
- [x] Tag `v0.9.3-pilot-exec-ready` created + pushed (annotated `47a65efd`,
      peels to `4fa6e1d`); `v0.9.0`/`v0.9.1`/`v0.9.2` NOT moved.
- [x] Bundle rebuilt from the tagged source and re-verified (this report);
      exact 48-cell bundled dry-run 48/48.
- [ ] Exact Kaggle launch commands + evidence prepared (runtime identity
      preflight, bundled 48-cell dry-run, service bootstrap, model-load
      preflight, real launch).
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

The 2026-08-13 freeze on `v0.9.2-pilot-exec-ready`
(`e030be5f4736e22ce40cfa798633b186858b0221`) covered the real-launch closure
(Gates 9/10: saleor `TZ=UTC` freeze + Gate 9 preflight ledger + hermetic
repo-snapshot/preflight gates; archive SHA-256
`ecb7ea7c85d8bdc527a0384f141b47a1e84ee0b3c3f12b6b8305d880098015f1`). It was
superseded by the service-bootstrap correction (this freeze) because a fresh
Kaggle session has no PostgreSQL/Valkey OS services; the deployment source tag
moved from `v0.9.2-pilot-exec-ready` to `v0.9.3-pilot-exec-ready`. The
2026-08-10 freeze on `v0.9.1-pilot-exec-ready`
(`7efdbe60bb195b1f3ca5854fd98057e29559a510`) covered the pre-execution gates
(deployment bundle + pre-registration).
