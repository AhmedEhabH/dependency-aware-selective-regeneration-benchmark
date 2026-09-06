# v0.9.22 D9.6 — Kaggle/GitHub Boundary Correction (Closure Report)

**Date:** 2026-08-29
**Branch:** `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure`
**Status:** COMPLETE (local closure; REAL T4 PROOF PENDING — no stable tag yet)
**D9.6_SOURCE_COMMIT:** `6ff1c93ed355b6dc73fa3ebd18ba6079ace39ab6`
**Artifact:** `dist/pilot-kaggle-upload.zip` SHA-256 `03d8d0ae37b995a362ee90c53a1851588ad024f13ead033814399210ce54dfc4` (sidecar matches)
**Full acceptance:** 2538 passed / 33 skipped / 0 failed
**Supersedes:** D9 artifact `913e8065...` / source `9ea02b3...` and all earlier v0.9.22 candidates

## 1. Why D9.6 exists (truthful status)

D9 wired a no-shell bounded remote annotated-tag-peel launch gate
(`verify_remote_annotated_tag_peel`) into the Kaggle `pilot-launch-cell` AND
`pilot-resume-cell`. That design is suboptimal for the actual working model of
this project:

- The benchmark repository's **visibility is owner-controlled and out of scope**
  for the benchmark runtime. It is not a "public canonical remote" requirement.
- A Kaggle launch/resume step that contacts GitHub (even read-only `git ls-remote`)
  adds a fragile network dependency, needs no credential in a healthy setup, and is
  unnecessary: the launch-authorization gate needs only **local evidence**.
- The stable tag is an **owner-side release act**, deliberately created and locally
  verified against the owner-controlled, locally verified source commit **after** a
  real preflight passes. It should never be a runtime pre-command gate in Kaggle.

D9.6 therefore removes the entire remote tag-peel machinery and makes the local
`validate_pilot_launch_authorization` the ONLY pre-command gate, in BOTH cells.
Kaggle launch and resume NEVER contact GitHub (no `git ls-remote`, no token, no
`GIT_*`).

## 2. What was removed (`src/benchmark/execution/preflight.py`)

- The constants `KAGGLE_PUBLIC_CANONICAL_REMOTE`, `REMOTE_TAG_PROOF_TIMEOUT_SECONDS`,
  and `PILOT_STABLE_TAG`.
- The whole `verify_remote_annotated_tag_peel` function.
- No dead imports: `subprocess`/`time`/`os`/`shutil`/`contextlib` remain used
  elsewhere in `preflight.py`.

`PILOT_STABLE_TAG` was used ONLY by the tag-peel function, so removing it does not
affect any other production path.

## 3. What changed in the notebook (`notebooks/pilot_exec_01.ipynb`)

- `pilot-launch-cell`: imports and calls `validate_pilot_launch_authorization(...)`
  before `exec_cmd = [` construction; prints `PILOT LAUNCH AUTHORIZATION: PASSED`.
- `pilot-resume-cell`: **gained** the same `validate_pilot_launch_authorization(...)`
  call before `resume_cmd = [` construction (it previously had only the tag-peel
  gate); prints `PILOT RESUME AUTHORIZATION: PASSED`.
- The `secrets-cell` carries `HF_TOKEN` only — never `GITHUB_TOKEN`.
- No scientific inputs changed: model Qwen2.5-Coder-14B-Instruct, BNB-NF4, sdpa,
  kernel policy `flash_or_efficient_no_math`, GQA compat `repeat_kv_sm75`, 12
  scenarios, 3 pins, 2 strategies, 2 reps = 48 cells, prompts, Ground Truth,
  metrics, `--timeout 600`, `--validation-timeout 1800`, max attempts 3, completion
  cap 4096, the 12000/64 long-context gate.

## 4. Genuine RED (against the D9.5 baseline)

Stashing only the production + notebook changes (restoring the D9 baseline) and
running the new boundary tests produced exactly the misplaced-gate failures:

```
10 failed, 6 passed
```

covering the tag-peel machinery still in `preflight.py`, the notebook launch/resume
cells that could not compile/authorize via the standard join, and the missing
resume-cell authorization gate.

## 5. GREEN (after the fix)

- Focused boundary suites: `test_preflight.py::TestD96KaggleGitHubBoundary`,
  `test_pilot_notebook_contract.py::TestD96KaggleGitHubBoundary`,
  `test_pilot_deployment_bundle.py::TestD96NoGitHubLaunchRuntimeDependency`,
  `test_d96_kaggle_github_boundary.py` — all green.
- Previously-impacted focused suites (preflight, notebook contract, deployment
  bundle, release provenance) — green.
- **Full acceptance:** 2538 passed / 33 skipped / 0 failed.

New regression tests added:

- `tests/unit/execution/test_preflight.py::TestD96KaggleGitHubBoundary`
  (module-source scan + absence of tag-peel machinery; valid-complete evidence
  passes without git/network via a monkeypatched-raised `subprocess.run`).
- `tests/integration/test_pilot_notebook_contract.py::TestD96KaggleGitHubBoundary`
  (launch + resume both authorize before command construction; compile via standard
  join; forbidden fragments absent; `HF_TOKEN` not `GITHUB_TOKEN`; bundled vs
  canonical contract match).
- `tests/integration/test_pilot_deployment_bundle.py::TestD96NoGitHubLaunchRuntimeDependency`
  (bundled preflight + CLI + launch/resume cells carry no GitHub/git machinery and
  still call `validate_pilot_launch_authorization`).
- `tests/integration/test_d96_kaggle_github_boundary.py` (repo-wide runtime/notebook
  audit + current-truth documentation regression — required markers present, no
  forbidden fragments).

## 6. Freeze (two-pass finalizer, `--verify-source-provenance`)

- Commit 1 (code + notebook + tests): `13dc527bbb2e01432aa727683f7498088da00a65`
  (`fix(pilot): remove Kaggle GitHub runtime tag-peel gate (D9.6 boundary correction)`).
- Finalizer pass 1 at `13dc527...` wrote the anchors.
- Commit 2 (anchor refresh): `6ff1c93ed355b6dc73fa3ebd18ba6079ace39ab6` =
  **D9.6_SOURCE_COMMIT** (`chore(freeze): refresh pilot notebook frozen manifest
  anchors for D9.6 boundary correction`).
- Finalizer pass 2 at `6ff1c93...` with `--verify-source-provenance`: **FROZEN,
  0 mismatches**, idempotent (same-input rerun: archive SHA unchanged, stable
  manifest hashes unchanged).
- Exact artifact: `dist/pilot-kaggle-upload.zip` SHA-256
  `03d8d0ae37b995a362ee90c53a1851588ad024f13ead033814399210ce54dfc4`; sidecar matches;
  freeze evidence `reports/pilot_notebook_trust_freeze.json`.

## 7. Exact fresh-extraction bundled dry-run

Fresh extraction of the frozen artifact + transport restore, then the bundled CLI
dry-run with explicit `--source-commit 6ff1c93...`:

```
Terminal: 48/48
Succeeded: 48
Failed: 0
Pending: 0
```

Canonical `validate_pilot_dryrun_evidence` PASS: 48 records, 48 unique run IDs,
repos 16/16/16, strategies 24/24, reps 24/24, 0 model calls, 0 prompt/completion /
total workflow tokens; every record + `source_identity.json` == `6ff1c93...` and its
build id `6ff1c93`.

## 8. Current-truth documentation + decision log

- README.md, AGENTS.md, SYSTEM_STATE.md, TODO.md, docs/PILOT_KAGGLE_RUNBOOK.md,
  docs/START_HERE.md — current-truth block rewritten to D9.6; ALL forbidden
  fragments (`GITHUB_TOKEN`, `must be public`, `make the repository public`,
  `public mirror`, `public canonical remote`, `REMOTE TAG-PEEL PRE-LAUNCH GATE`,
  `verify_remote_annotated_tag_peel`, `REMOTE TAG PEEL PROOF`,
  `RESUME REMOTE TAG PEEL PROOF`) removed; required markers (`never contact GitHub`,
  `owner-controlled`, `locally verified against`, `after real preflight`,
  `v0.9.22-pilot-exec-ready`) present.
- docs/MASTER_IMPLEMENTATION_PLAN.md, docs/PROJECT_HANDOFF.md,
  docs/AI_ACCOUNT_TRANSFER_HANDOFF.md, reports/latest_phase_report.md — updated to
  D9.6 current truth with D9 demoted to PRIOR TRUTH.
- DECISION_LOG.md — Decision D031 added.

## 9. Required truthful status

- D8's exact 2x T4 preflight passed but D8 is **REJECTED** for Pilot launch (the
  real Pilot exposed the in-flight timeout/heartbeat defect D9 closes).
- `exp-20260828-151335` holds 0 accepted RunRecords and must never be resumed.
- D9 (`913e8065...`) and D8 (`02d16ca2...`) artifacts are SUPERSEDED by D9.6; do not
  upload either.
- No stable `v0.9.22-pilot-exec-ready` tag yet: next external step is ONE
  exact-D9.6-artifact real 2x T4 GQA microprobe + generation-deadline canary +
  short + 12k model-preflight-only session. On PASS, locally annotate the tag at
  `6ff1c93...` and verify it; on FAIL return to the SAME v0.9.22 task (never v0.9.23).
