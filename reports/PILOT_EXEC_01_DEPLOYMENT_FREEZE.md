# PILOT-EXEC-01 — Deployment Freeze Report

**Date:** 2026-08-10
**Task:** `PILOT-EXEC-01` (Pilot deployment + pre-execution gates)
**Status:** FROZEN (Pilot deployment locked; Pilot execution NOT STARTED)

---

## 1. Deployment source identity

| Field | Value |
|---|---|
| Branch | `main` (after `merge(pilot): PILOT-EXEC-01 pre-execution gates`) |
| Merge commit | `7efdbe60bb195b1f3ca5854fd98057e29559a510` |
| Stable source tag | `v0.9.1-pilot-exec-ready` → peeled commit `7efdbe60bb195b1f3ca5854fd98057e29559a510` |
| Prior tag (NOT moved) | `v0.9.0-pilot-ready` → `90a4282ac96328e26143b4f98d4bcf520c3c1e9b` (unchanged, immutable) |
| Feature branch (pre-merge) | `experiment/pilot-exec-01` (2 commits, pushed, local == remote at merge) |
| Builder | `scripts/build_pilot_upload_bundle.py` (committed at `988830a`) |
| Deployment contract tests | `tests/integration/test_pilot_deployment_bundle.py` (committed at `988830a`, 12/12 passed) |

## 2. Bundle (built from the tagged source)

| Field | Value |
|---|---|
| Output root | `dist/pilot-kaggle-upload/` (gitignored) |
| Archive | `dist/pilot-kaggle-upload.zip` |
| Archive SHA-256 | `dd9b4e291f0db16ebe20bf6e13075e78ad8021a5d8fd6aa8a60fc0ae722c7c50` |
| Sidecar | `dist/pilot-kaggle-upload.zip.sha256` (matches archive hash) |
| Code files | 90 (manifest SHA-256 `196561bdc8754d97890724a33ff7bbd921016a95009bf68111d47bc5d4a31a3e`) |
| Data files | 56 (manifest SHA-256 `2abc877aa4649f1ff0aa1e6eeb6719b04724869140dc6184213e380965e9f295`) |
| Notebooks | 0 (Pilot bundle omits the Smoke notebook by design) |
| `pilot_deployment_identity.json` | task `PILOT-EXEC-01`; protocol 1.0; source_commit `7efdbe60bb...`; source_tag `v0.9.1-pilot-exec-ready`; model `Qwen/Qwen2.5-Coder-14B-Instruct`; quantization `bnb-nf4`; timeout 600; max_attempts 3; max_completion_tokens_per_call 4096; max_total_workflow_tokens 0; scenario_count 12; strategy_count 2; repetitions 2; expected_cells 48; created_utc `2026-08-10T00:00:00+00:00` |

The historical Scientific Smoke bundle (`kaggle_upload/`) is NOT the Pilot
deployment bundle. It remains frozen and byte-identical.

## 3. Verification performed on the frozen bundle

1. **Determinism:** bundle rebuilt from the tagged source with
   `--created-utc 2026-08-10T00:00:00+00:00`; code/data manifest SHA-256s match
   the pre-tag Gate A build (`196561bd…` / `2abc877a…`) — content-identical
   code and data; only `source_commit` in the identity changed to the tag's
   peeled commit.
2. **Archive integrity:** `dist/pilot-kaggle-upload.zip` SHA-256 == sidecar ==
   `dd9b4e29…`.
3. **Bundled exact 48-cell dry-run** (fresh output dir
   `%TEMP%\pilot_bundle_dryrun_freeze`, mock backend, bundled CLI at
   `dist/pilot-kaggle-upload/code/seven_arm_benchmark.py`,
   `--profile pilot --qwen-quantization bnb-nf4 --max-attempts 3 --timeout 600
   --source-commit 7efdbe60… --source-tag v0.9.1-pilot-exec-ready`):
   **48/48 terminal / 48 succeeded / 0 failed / 0 pending**; 48 unique run IDs;
   12 unique scenario IDs; per-repo todo 16 / djangocms 16 / saleor 16;
   per-strategy iterative_repository_agent 24 / selective 24; per-rep 24 / 24.
4. **Deployment contract tests:** `test_pilot_deployment_bundle.py` 12/12
   passed at commit `0c2b5cc` (post-merge state re-verified: ruff clean, mypy
   strict clean, py_compile clean, `git diff --check` clean).

## 4. Launch flags frozen for every real Pilot invocation

`--backend kaggle-qwen --profile pilot --qwen-quantization bnb-nf4
--max-attempts 3 --max-completion-tokens-per-call 4096
--max-total-workflow-tokens 0 --timeout 600 --source-commit
7efdbe60bb195b1f3ca5854fd98057e29559a510 --source-tag v0.9.1-pilot-exec-ready
--hf-sync` plus the exact model path and HF results repo ID recorded at launch
time. One continuous 48-cell session; no `--max-runs` subsetting.

## 5. Post-freeze gate plan (A7/A8 evidence)

- [x] Commits pushed: deployment code/test `988830a`, docs/pre-registration
      `0c2b5cc` (branch `experiment/pilot-exec-01`, local == remote).
- [x] Independent-style pre-execution audit: deployment contract 12/12,
      ruff, mypy strict, compile, diff-check clean.
- [x] Non-fast-forward merge to `main` at `7efdbe6`; pushed; local ==
      origin/main.
- [x] Tag `v0.9.1-pilot-exec-ready` created + pushed (peeled `7efdbe6`);
      `v0.9.0-pilot-ready` NOT moved.
- [x] Bundle rebuilt from the tagged source and re-verified (this report).
- [ ] Exact Kaggle launch commands + evidence prepared (runtime identity
      preflight, bundled 48-cell dry-run, model-load preflight, real launch).
- [ ] Final report per `08_DETAILED_OPENCODE_REPORT_TEMPLATE.md`.

**Pilot = NOT STARTED.** Real launch is deferred until the user confirms the
actual Kaggle mounted model path (e.g. `/kaggle/input/<model-slug>`) and the
exact HF results repository ID.
