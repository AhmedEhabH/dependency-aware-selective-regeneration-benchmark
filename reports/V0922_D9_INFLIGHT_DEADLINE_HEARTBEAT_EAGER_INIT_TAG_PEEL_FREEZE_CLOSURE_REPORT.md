# v0.9.22 D9 — In-Flight Deadline Heartbeat, Eager Model Init, Remote Tag-Peel Gate, Freeze Recovery (Closure Report)

**Date:** 2026-08-29
**Branch:** `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure`
**Status:** COMPLETE (local closure; REAL T4 PROOF PENDING)
**D9_SOURCE_COMMIT:** `9ea02b35d58a3e4ef2d0d5d980e44fa53d8c079d`
**Artifact:** `dist/pilot-kaggle-upload.zip` SHA-256 `913e8065a384effa2cf6b6a69f11e5840506644873fa54764c3cbe8ee5406d48` (sidecar matches)
**Full acceptance:** 2532 passed / 33 skipped / 0 failed (D8+prior closures already green; not re-run)

## 1. Why D9 exists (truthful status)

D8's exact 2x T4 preflight passed, but the real Pilot exposed an in-flight
timeout/heartbeat defect: a long synchronous Qwen decode could cross the 600 s
workflow deadline because the deadline was only enforced BETWEEN model calls,
never DURING a single `model.generate`. D8 is therefore **REJECTED for Pilot
launch** and superseded by D9 (still v0.9.22; never v0.9.23). The interrupted
D8 freeze session (`exp-20260828-151335`) holds 0 accepted RunRecords, is not an
accepted experiment, and must never be resumed.

## 2. D9 production closures (commit `a91ee87db540ae9da0ffd87b73ebdfb1cf973d86`)

- **D9.1 in-flight deadline heartbeat** (`src/benchmark/llm/kaggle_qwen_backend.py`,
  `_WorkflowDeadlineHeartbeatStoppingCriteria`): a transformers-compatible
  `StoppingCriteria` is polled at every decode step. The instant the injected run
  guard (`lambda: not budget.timed_out`) first returns false, generation stops on
  the next completed step with `finish_reason="timeout"` and the measured partial
  token usage is returned so the canonical workflow-budget-exhausted RunRecord is
  written (partial text never committed). Bounded 30 s liveness heartbeats
  (`GENERATION_RUNNING …` / `GENERATION_STOPPED reason=workflow_deadline …`) prove a
  long synchronous decode alive. Cooperative stop at the step boundary — never an
  unsafe Python thread kill.
- **D9.2 real-Qwen generation-deadline canary**
  (`run_generation_deadline_probe` + `GENERATION_DEADLINE_PROBE_MAX_CHECK_BOUND=8`):
  a deterministic counter guard becomes false after `max_checks_before_deadline=3`
  criterion checks, so the deadline (NOT EOS/length) is proven target-side with
  `completion_tokens` in the tiny bound `[1, 8]`. The preflight and
  `validate_pilot_launch_authorization` both fail closed through
  `_generation_deadline_probe_errors` (missing/wrong-type/false/EOS-or-length/
  underflow/overflow all rejected). Mock backends omit it (legacy assertions
  unaffected); a real launch ALWAYS requires it.
- **D9.3 eager shared-model init** (`KaggleQwenBackend.initialize()` +
  `seven_arm_benchmark.py`): the one-time Qwen weights load happens via
  `initialize()` BEFORE `t_start`/any `RUN_START`, so model load is never charged
  to one strategy/repetition's scientific timing or token budget. Failure is an
  engineering blocker: checkpoint left resumable/incomplete, 0 RunRecords, exit 1.
- **D9.4 per-run cooperative guard install** (`src/benchmark/execution/runner.py`
  `_apply_model_call_guards`): every run installs a fresh guard on the strategy
  AND the shared backend; the lambda closes over THIS run's `BudgetManager`, so the
  shared backend never retains a prior run's deadline guard. Mock/OpenRouter
  backends are untouched (optional setter).
- **D9.5 pre-launch remote annotated-tag peel gate + live reaper**
  (`verify_remote_annotated_tag_peel` in `preflight.py`; notebook `pilot-launch-cell`
  and `pilot-resume-cell`): bounded 30 s, no-shell
  `git ls-remote --tags <public canonical remote> refs/tags/v0.9.22-pilot-exec-ready
  refs/tags/v0.9.22-pilot-exec-ready^{}` requires BOTH the annotated ref and its
  peel == the notebook's exact `SOURCE_COMMIT`; any miss (lightweight tag, missing,
  wrong peel, malformed/duplicate output, nonzero exit, timeout, network/DNS/TLS,
  missing git) raises fail-closed. Engineering-only, never inside scientific
  timing/metrics. `_run_live` gains process-group terminate→kill→reap with bounded
  grace.
- Tests: `test_preflight.py` +318, `test_llm_kaggle_qwen_backend.py` +235,
  `test_runner.py` +70, `test_pilot_notebook_contract.py` +173.

### RED/GREEN
- Genuine RED: D8 baseline **17 failures** before the D9 fix.
- DEGREE GREEN: focused D9 **38/38** plus the already-green D8 closures.
- Full acceptance **2532 passed / 33 skipped / 0 failed** (recorded by the
  interrupted session; NOT re-run for this freeze-only recovery per authorization).

## 3. Freeze recovery (authorized deletion + anchor refresh)

The freeze stopped because three uncommitted D8-baseline scratch copies entered
the bundle and failed source provenance. Deletion was explicitly authorized only
after the four read-only checks:

| Orphan (deleted) | SHA-256 | D8 blob @ `8f0b119…` | D8 file | Checks |
|---|---|---|---|---|
| `_base_check_seven.py` | `044913C89898CDAFB924E2448C95E6BE3F379AAE66E83E1F46DF27F1C2F4E7E5` | `99de1643…` | `seven_arm_benchmark.py` | untracked, 0 references, exact blob |
| `src/benchmark/execution/_base_check_preflight.py` | `7B583872A042C608C40C57CFDDD013817F86E72F9B491F859D760B3F8EC116B0` | `c7899452…` | `src/benchmark/execution/preflight.py` | untracked, 0 references, exact blob |
| `src/benchmark/llm/_base_check_backend.py` | `82CAA09237FEBE9705F82E4E6E788EF40D982BDBE578F95158960574C21FC293` | `6e2ff716…` | `src/benchmark/llm/kaggle_qwen_backend.py` | untracked, 0 references, exact blob |

All four required checks passed (untracked per `git ls-files --error-unmatch`;
zero references repo-wide per `rg`; exact D8 blobs recoverable from
`8f0b11953a4fe2990b7e6c680288be282b8a6b67`; SHA-256 recorded above). Only those
three exact paths were deleted — no directory, no wildcard/glob/recursive removal.

### Finalizer sequence
1. Discovery pass at `a91ee87db540ae9da0ffd87b73ebdfb1cf973d86` WITHOUT
   `--verify-source-provenance` (authorized bridge): rewrote the stale
   `code_manifest_sha256` anchor (which had been discovered while the orphans were
   present) to the correct anchor computed with the orphans absent. Only intended
   tracked source change = the canonical notebook's stable anchors.
2. Canonical + bundled notebook code cells compile **16/16**.
3. Focused notebook/finalizer/provenance tests **165/165** passed
   (`test_pilot_notebook_contract.py`, `test_pilot_release_provenance.py`,
   `test_pilot_deployment_bundle.py`).
4. Committed ONLY the canonical anchor-written notebook →
   **`9ea02b35d58a3e4ef2d0d5d980e44fa53d8c079d`**
   (`chore(freeze): refresh pilot notebook frozen manifest anchors for D9`) =
   D9_SOURCE_COMMIT / artifact source / future tag target.
5. Provenance-enabled finalizer at `9ea02b3…` WITH `--verify-source-provenance`:
   FROZEN, **0 provenance mismatches**.
6. Idempotence proof: identical second run → canonical notebook unchanged,
   archive SHA unchanged (`913e8065…`), stable manifest hashes unchanged,
   freeze report semantically byte-identical, still 0 mismatches.

## 4. Frozen identity and artifact acceptance

- `reports/pilot_notebook_trust_freeze.json` **FROZEN**: source_commit
  `9ea02b35d58a3e4ef2d0d5d980e44fa53d8c079d`, source_tag
  `v0.9.22-pilot-exec-ready` (planned), created_utc `2026-08-29T08:35:38Z`,
  archive_sha256 `913e8065…`.
- Stable manifest hashes (unchanged from D8 except code):
  code `e9347063b9459ec5f019e53b4354c1aaaca0ff759e74358654faadff6eee8f19`,
  data `8b859ecc7216…`, repository_snapshot `49d91d3943…`,
  kaggle_transport_path_map `07036a36cd…`. Data/repo/transport unchanged -> code
  manifest reflects D9 production code with the orphans absent.
- Artifact `dist/pilot-kaggle-upload.zip` SHA-256
  `913e8065a384effa2cf6b6a69f11e5840506644873fa54764c3cbe8ee5406d48`; sidecar
  (`dist/pilot-kaggle-upload.zip.sha256`) matches; `git diff --check` clean;
  canonical notebook clean at HEAD `9ea02b3…`.
- Bundled identity `dist/pilot-kaggle-upload/pilot_deployment_identity.json`
  resolves source_commit `9ea02b3…`; deployed build id at runtime defaults to
  source_commit.
- D8 artifact `02d16ca2…` is SUPERSEDED; do not upload.

## 5. Exact final-artifact dry run (48/48) + canonical validator

Fresh extraction of `dist/pilot-kaggle-upload.zip`, bundled CLI, explicit
`--source-commit 9ea02b35d58a3e4ef2d0d5d980e44fa53d8c079d --source-tag
v0.9.22-pilot-exec-ready --profile pilot --dry-run`:

- **48/48 succeeded**, 48 unique run IDs;
- repositories 16/16/16 (todo/djangocms/saleor);
- strategies 24/24 (iterative_repository_agent/selective);
- repetitions 24/24 (rep1/rep2);
- 0 model calls, 0 prompt/completion/total tokens,
  0 total_workflow_model_calls/tokens, all phase fields 0;
- every record + `source_identity.json` == D9_SOURCE_COMMIT with build id
  `9ea02b3…`, model_identity `dry-run:mock`, protocol 1.0, profile `pilot`;
- canonical `validate_pilot_dryrun_evidence` **PASS** (summary printed in the
  session log; evidence dir kept outside the repo under
  `%TEMP%\opencode\d9_dryrun`).

## 6. Verification performed (this closure)

- `git diff --check` PASS; canonical notebook clean at HEAD.
- Canonical + bundled notebook compile: 16/16 code cells each.
- Focused notebook/finalizer/provenance: **165/165** PASS.
- Two-pass finalizer: discovery PASS; provenance-enabled FROZEN PASS (0
  mismatches); idempotent rerun PASS.
- Freeze report / artifact / sidecar consistency PASS.
- Exact-artifact dry-run + validator PASS (48/48).
- Full 2532-test suite NOT re-run (authorization: only notebook anchors changed
  after `a91ee87`; production/test files untouched since the recorded 2532/33/0).

## 7. Authoritative docs updated

- `AGENTS.md` — D9 CURRENT TRUTH block + v0.9.22 candidate bullet (D8 demoted
  to PRIOR TRUTH / superseded).
- `reports/latest_phase_report.md` — D9 CURRENT TRUTH block (D8 preserved as
  PRIOR TRUTH).
- `reports/PROJECT_HEALTH_REPORT.md` — Current Health table, Next action,
  D8 superseded.
- `reports/pilot_notebook_trust_freeze.json` — FROZEN (commit in this closure).

## 8. Scientific and release truth

- Frozen scientific contract **UNCHANGED** (model Qwen2.5-Coder-14B-Instruct,
  BNB-NF4, sdpa, kernel policy `flash_or_efficient_no_math`, GQA compat
  `repeat_kv_sm75`, 12 scenarios, 3 pins, 2 strategies, 2 reps = 48 cells,
  prompts, Ground Truth, metrics, `--timeout 600`, `--validation-timeout 1800`,
  max attempts 3, completion cap 4096, the 12000/64 long-context gate).
- No stable tag created during this local closure. **NO 48-cell launch.**
- Next external step (single): upload ONLY this exact D9 artifact and run the
  fresh real 2x T4 Kaggle model preflight (repo preflight + heartbeat, Qwen 14B
  BNB-NF4 load, GQA microprobe, short probe, 12k/64 probe with attention-policy
  evidence, and the now-mandatory generation-deadline canary); only on PASS
  annotate `v0.9.22-pilot-exec-ready` at `9ea02b35d58a3e4ef2d0d5d980e44fa53d8c079d`;
  on FAIL return to the SAME v0.9.22 task (never v0.9.23).
- Commits in this closure: production+tests `a91ee87…` (D9), frozen notebook
  `9ea02b3…` (C1, artifact source / future tag target), then the freeze report
  and docs commits.
- Superseded artifacts (do not upload): D8 `02d16ca2…` from `8f0b119…`; D7
  `e0a64937…` from `3ebc75d…`; D1–D6 `ce40b330…` from `f72ecda…`; earlier
  candidates.

## 9. Post-closure consistency note (docs/evidence-labeling correction, PILOT-EXEC-01 — 2026-08-29)

Added after the D9 acceptance evidence above was frozen, to keep the repository
current without touching the artifact/freeze:

- A docs/evidence-labeling correction pass aligned the stale D8/older
  "CURRENT" sections in 8 documents to the D9 truth above: `SYSTEM_STATE.md`,
  `TODO.md`, `README.md`, `docs/AI_ACCOUNT_TRANSFER_HANDOFF.md`,
  `docs/MASTER_IMPLEMENTATION_PLAN.md`, `docs/PROJECT_HANDOFF.md`,
  `docs/PILOT_KAGGLE_RUNBOOK.md`, `reports/PROJECT_HEALTH_REPORT.md`. Old D8
  blocks were relabeled PRIOR/SUPERSEDED; only current/next-action summaries
  were rewritten; historical chronology was preserved.
- `runs_dryrun/README.md` added (tracked, docs-only) making explicit that
  `runs_dryrun/` is a frozen HISTORICAL 7-record Smoke fixture that MUST NOT be
  used as current candidate proof; the D9 48/48 evidence comes from a fresh
  exact-artifact dry-run into a fresh output directory. The 11 original fixture
  files were left byte-identical.
- `AGENTS.md` Project Export Rule wording updated to describe `runs_dryrun/` as
  a historical fixture rather than current candidate evidence.
- **No production, tests, notebook, artifact, or freeze changed.**
  `D9_SOURCE_COMMIT` remains `9ea02b35d58a3e4ef2d0d5d980e44fa53d8c079d` and the
  artifact remains `913e8065…`; no release, tag, or artifact was moved or
  rebuilt. The position of "NO stable tag, REAL T4 PROOF PENDING, single exact
  D9-artifact real 2x T4 preflight next" is unchanged.