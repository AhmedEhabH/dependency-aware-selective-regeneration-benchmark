# PILOT-EXEC-01 — Deployment Freeze Report

**Date:** 2026-08-13 (supersedes the 2026-08-10 freeze on `v0.9.1-pilot-exec-ready`)
**Task:** `PILOT-EXEC-01` (Pilot deployment + pre-execution gates 9/10 closure)
**Status:** FROZEN (Pilot deployment locked; Pilot execution NOT STARTED)

---

## 1. Deployment source identity

| Field | Value |
|---|---|
| Branch | `main` (after `merge(pilot): PILOT-EXEC-01 real-launch closure …`) |
| Merge commit | `e030be5f4736e22ce40cfa798633b186858b0221` |
| Stable source tag | `v0.9.2-pilot-exec-ready` → peeled commit `e030be5f4736e22ce40cfa798633b186858b0221` |
| Prior tag (NOT moved) | `v0.9.0-pilot-ready` → `90a4282ac96328e26143b4f98d4bcf520c3c1e9b` (unchanged, immutable) |
| Superseded interim tag | `v0.9.1-pilot-exec-ready` → `7efdbe60bb195b1f3ca5854fd98057e29559a510` (pre-execution gates only; NOT the real-launch source) |
| Feature branch (pre-merge) | `fix/pilot-real-launch-closure` (commits `17bd4ca`, `4279f1c`, merged at `e030be5`) |
| Builder | `scripts/build_pilot_upload_bundle.py` |
| Real repo cache | git checkouts at pinned SHAs: django CMS `0f633fc9fa213357f4202482aab2b0edad680f95`, Saleor `e11a5557eff29fbb2eed36e6ff3cd0af08ab9e10` (todo embedded) |
| Deployment contract tests | `tests/integration/test_pilot_deployment_bundle.py` (in the 67-test Gate 10 set) |

## 2. Bundle (built from the tagged source)

| Field | Value |
|---|---|
| Output root | `dist/pilot-kaggle-upload/` (gitignored) |
| Archive | `dist/pilot-kaggle-upload.zip` |
| Archive SHA-256 | `ecb7ea7c85d8bdc527a0384f141b47a1e84ee0b3c3f12b6b8305d880098015f1` |
| Sidecar | `dist/pilot-kaggle-upload.zip.sha256` (matches archive hash) |
| Code files | 91 (manifest SHA-256 `99688e4e03291606399126061ae8305bb768a68d10fee0dc43964846272fbe96`) |
| Data files | 57 (manifest SHA-256 `8b859ecc72164fe95c0aa122f8179310ccc6375613543c6702c2ca5867c97b5a`) |
| Notebook files | 1 (manifest SHA-256 `9cbcc7589116eba4588b3566c1e1466f329c975e413c29682d109d0e202b7129`) |
| Repository snapshot manifest | SHA-256 `49d91d39435f7e6f2dbf7d15f1a59188aa059ebb16fb31094c7a1827fb62702c` |
| `pilot_deployment_identity.json` | task `PILOT-EXEC-01`; protocol 1.0; source_commit `e030be5f47…`; source_tag `v0.9.2-pilot-exec-ready`; model `Qwen/Qwen2.5-Coder-14B-Instruct`; quantization `bnb-nf4`; timeout 600; max_attempts 3; max_completion_tokens_per_call 4096; max_total_workflow_tokens 0; scenario_count 12; strategy_count 2; repetitions 2; expected_cells 48; created_utc `2026-08-13T00:00:00+00:00` |

The historical Scientific Smoke bundle (`kaggle_upload/`) is NOT the Pilot
deployment bundle. It remains frozen and byte-identical.

## 3. Verification performed on the frozen bundle

1. **Determinism:** bundle rebuilt deterministically from the tagged source
   (`--source-commit e030be5f… --source-tag v0.9.2-pilot-exec-ready
   --created-utc 2026-08-13T00:00:00+00:00`) with the real repo cache; the
   rebuild is byte-identical for identical inputs.
2. **Archive integrity:** `dist/pilot-kaggle-upload.zip` SHA-256 == sidecar ==
   `ecb7ea7c85…`; archive contains the notebook + three repos (todo embedded,
   django CMS, Saleor) with no `.git` directories.
3. **Identity contract:** `pilot_deployment_identity.json` holds the frozen
   values (section 2) and code/data/notebook/repository-snapshot manifest
   hashes match the emitted bundle bytes.
4. **Bundled exact 48-cell dry-run** (fresh output dir, mock backend, bundled
   CLI at `dist/pilot-kaggle-upload/code/seven_arm_benchmark.py`):
   **48/48 unique / 0 missing / 0 duplicate**; 12 unique scenario IDs;
   per-repo todo 16 / djangocms 16 / saleor 16; per-strategy
   iterative_repository_agent 24 / selective 24; per-rep 24 / 24.
5. **Targeted Gate 10 tests (67/67 passed, 90.88s)** on the tagged bundle:
   deployment bundle, notebook contract, repo snapshot, validation-command
   mapping, real-launch preflight. Post-merge static gates clean: `git diff
   --check`, ruff, mypy strict, py_compile.

## 4. Launch flags frozen for every real Pilot invocation

`--backend kaggle-qwen --profile pilot --qwen-quantization bnb-nf4
--max-attempts 3 --max-completion-tokens-per-call 4096
--max-total-workflow-tokens 0 --timeout 600 --source-commit
e030be5f4736e22ce40cfa798633b186858b0221 --source-tag v0.9.2-pilot-exec-ready
--hf-sync` plus the exact model path and HF results repo ID recorded at launch
time. One continuous 48-cell session; no `--max-runs` subsetting.

## 5. Post-freeze gate plan (Gate 9/10 evidence)

- [x] Gate 9 engineering preflight ledger written
      (`reports/PILOT_EXEC_01_GATE9_ENGINEERING_PREFLIGHT_LEDGER.md`); saleor
      `TZ=UTC` frozen; order/pricing cluster + `test_filters_date` classified
      as upstream/Windows artifacts.
- [x] Closure committed (`4279f1c`) and pushed on
      `fix/pilot-real-launch-closure`.
- [x] Non-fast-forward merge to `main` at `e030be5`; pushed; local ==
      origin/main.
- [x] Tag `v0.9.2-pilot-exec-ready` created + pushed (peeled `e030be5`);
      `v0.9.0-pilot-ready` NOT moved; `v0.9.1-pilot-exec-ready` superseded.
- [x] Bundle rebuilt from the tagged source and re-verified (this report).
- [ ] Exact Kaggle launch commands + evidence prepared (runtime identity
      preflight, bundled 48-cell dry-run, model-load preflight, real launch).
- [ ] Final report per `08_DETAILED_OPENCODE_REPORT_TEMPLATE.md`.

**Pilot = NOT STARTED.** Real launch is deferred until the user confirms the
actual Kaggle mounted model path (e.g. `/kaggle/input/<model-slug>`) and the
exact HF results repository ID.

---

## Historical record (superseded 2026-08-13)

The 2026-08-10 freeze on `v0.9.1-pilot-exec-ready`
(`7efdbe60bb195b1f3ca5854fd98057e29559a510`) covered the pre-execution gates
(deployment bundle + pre-registration). It was superseded by the real-launch
closure (Gates 9/10) which added the saleor `TZ=UTC` validation freeze and the
hermetic repo-snapshot/preflight gates; the deployment source tag moved from
`v0.9.1-pilot-exec-ready` to `v0.9.2-pilot-exec-ready`.
