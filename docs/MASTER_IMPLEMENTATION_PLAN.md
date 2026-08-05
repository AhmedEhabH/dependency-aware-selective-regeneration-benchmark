# Master Implementation Plan

## Dependency-Aware Selective Regeneration for LLM-Assisted Software Evolution

## Authoritative Current Execution Track

```text
R4 = accepted and frozen (f5ae826)
R5 = accepted and frozen (7761c48)
R6 = ACCEPTED AND FROZEN (949e9c2) - freeze record and milestone-branch publication authorized
Push = published (upstream set, local/remote equality verified)
Selective calibration canary = EXECUTED (exp-20260804-133523, source/build 50ec2c1) - failed model_output, 0 files written; harness controls verified, Qwen quality unchanged
Qwen 14B BNB-NF4 canary preparation = COMPLETE (2026-08-05) - Commit A 0ece665 + Commit B 0a596b8, pushed, local = remote, tree clean; model-aware identity qwen:<basename>:<mode>:cfg-<12hex> replaces qwen:1:int8 (blocks auto-resume cross-model contamination); bnb-nf4 profile added; notebook pinned to unquantized 14b-instruct/1 with fail-closed canary preflight gate; full suite 1,877 passed / 32 skipped / 0 failed; next action = Kaggle engineering preflight ONLY
Real Smoke = 0/9 (local scripted 9/9; bundled CLI dry-run 9/9; 1 dedicated canary record accepted, 0 successful)
Tag = v2.0.0-scientific-smoke after real-result audit
Pilot = denominator not frozen; not authorized
```

Exact path from R6 freeze to Pilot freeze:

```text
record R6 freeze
→ push branch and set upstream, verify local/remote equality
→ record publication status and push again
→ Kaggle environment preflight
→ nine real Qwen Scientific Smoke V2 records (3 scenarios × 3 arms × 1 rep)
→ independent real-result audit
→ stable v2.0.0-scientific-smoke tag
→ freeze Pilot matrix and authorize Pilot
```

## Historical implementation plan — non-authoritative for current execution

The pre-R3 phase map, the legacy approved-repository and approved-strategy
lists below describe earlier implementation history. They are retained for
traceability only and are NOT authoritative for current execution. The current
authoritative track is the section above.

### Phase Map

| Phase | Name                            | Status      |
|-------|---------------------------------|-------------|
| 0     | Bootstrap and Environment       | COMPLETE    |
| 1     | Input Audit                     | COMPLETE    |
| 2     | Research Protocol               | COMPLETE    |
| 3     | Repository and Scenario Preparation | COMPLETE |
| 4     | Benchmark Core                  | COMPLETE    |
| 4A    | Domain Models and Contracts     | COMPLETE    |
| 4B    | Loaders and Validation          | COMPLETE    |
| 4C    | Model Backends                  | COMPLETE    |
| 4D    | Execution Core                  | COMPLETE    |
| 4E    | Impact Strategies               | COMPLETE    |
| 4F    | Evaluation Engine               | COMPLETE    |
| 5     | Strategies                      | SUPERSEDED  |
| 6     | Validation and Leakage          | PENDING     |
| 7     | Metrics and Statistics          | SUPERSEDED  |
| 8     | Kaggle Notebook                 | COMPLETE    |
| 9     | Packaging and Documentation     | COMPLETE    |
| 10    | Static and Local Engineering Audit | COMPLETE |

## Completed

- SU-0010A shared regeneration
- SU-0010B1 repository-derived ArtifactUniverse
- SU-0010B1A active snapshot staging
- SU-0010B1B Ground-Truth-free graph construction
- SU-0010B2 metrics persistence/reporting
- SU-0010B3 functional validation and bounded repair (correction: token budget enforcement, failure history preservation, timeout test fix)
- SU-0011 iterative repository agent (audit corrections applied: cumulative token accounting, budget check between reasoning/regeneration, fair token-budget semantics, requires_iteration control state, backend exception propagation, type-ignore removal)
- SU-0011 on feature/su-0011-iterative-repository-agent awaiting merge
- Efficient Agent Verification Setup (AGENTS.md, skill, commands, check_fast.py on chore/efficient-opencode-verification)
- OPENROUTER-BACKEND on feature/openrouter-api-backend — minimal OpenRouter API backend
- **SCIENTIFIC-SMOKE-V1 EXECUTED + FAILED** — 6 root-cause failures identified and fixed; retry required on experiment/scientific-smoke-v1
- **SCIENTIFIC-SMOKE-V1 RETRY1 DEPLOYMENT PINNED** — commit 76ef349, deployed build ID 76ef349, output `/kaggle/working/runs/scientific_smoke_v1_retry1`
- **SCIENTIFIC-SMOKE-V1 RETRY2 FIXES APPLIED** — active_snapshot_root propagation, filtered HF resume identity (commit 8a1948f+)
- **THREE-ARM-CORE-EXPERIMENT** — Recovered from broken methodology-conformance WIP; frozen three-arm design; create branch experiment/three-arm-smoke-v2 from 0a1c603

## Next

- ~~Scientific Smoke V1~~ — Superseded by THREE-ARM-CORE-EXPERIMENT
- **Execute Scientific Smoke V2 on Kaggle** — 3 arms × 3 changes × 1 rep = 9 real runs
- Pilot (remains unauthorized until Scientific Smoke V2 passes audit)
- **Complete:** 0a1c603 baseline verified (1063 pass, 5 skip), three-arm core experiment documented, 3 smoke scenarios created, evaluator tests isolated, contract tests added

## Known Boundary

- neutral empty graph when no profile graph exists
- real repository dependency inference remains deferred
- OpenRouter API backend is provider-integration only; no retries, streaming, or fallback routing
- Scientific Smoke V2 and Pilot remain unauthorized until Kaggle execution

### Dependencies

- Phase 0 must complete before Phase 1.
- Phase 1 must complete before Phase 2.
- Phases 2–3 can be partially parallelized.
- Phase 4 (subphases A–D) requires Phase 3 scenario definitions.
- Phase 4E requires Phase 4D execution core.
- Phase 4F requires Phase 4E strategies.
- Phase 6 requires Phase 4F evaluation engine.
- Phase 8 requires Phases 4–7.
- Phase 9 requires Phase 8.
- Phase 10 runs at the end.

### Approved Repositories (historical — pre-R6 plan)

| Size   | Repository            | Status |
|--------|-----------------------|--------|
| Small  | Controlled Django Todo| PENDING|
| Medium | django CMS            | PENDING|
| Large  | Saleor Core           | PENDING|
| Stress | ERPNext (optional)    | PENDING|

### Approved Strategies (historical — pre-R6 plan)

- repository_agent (baseline)
- static_only
- semantic_only
- hybrid_selective
- traceability_only (additional impact strategy)
- full_context (only when feasible)

### Key Constraints

- No local model download or inference.
- Real LLM runs on Kaggle (Qwen) or OpenRouter API (free/paid models).
- OpenRouter backend uses Python standard library only (no external SDK).
- Correctness > efficiency.
- Python 3.11, Conda environment.

## R6 Status (2026-08-01)

R6 deployment closure is **ACCEPTED AND FROZEN** by the final independent re-audit (GPT-5.6 Thinking, 2026-08-01, audited HEAD `949e9c2`), recorded in `docs/R6_FINAL_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md`. The bounded final correction closed TD-R6-ENTRYPOINT-001 (test commit `40c7a47`, bundled CLI dry-run 9/9) and documentation-truth defects D1–D6 (`949e9c2`). Runtime source commit `cb25e9f`; deployed bundle commit `54a0462`; manifest committed-tree counts 0/0/0; Todo baseline tests deployed = 47; evaluator assets deployed = 3 + 3 fingerprints. Local scripted records = 9/9; bundled CLI dry-run = 9/9; real Qwen records = 0/9; Kaggle not launched; push authorized and pending at this commit; tag not created; Pilot not authorized. Final accepted full suite = 1,648 passed / 32 skipped / 0 failed. Next: publish the branch with upstream, verify local/remote equality, then Kaggle environment preflight and nine real Qwen records.

## Deterministic Interpreter Closure (2026-08-02)

The clean-environment reproducibility defect at the project execution boundary was closed on branch `fix/kaggle-smoke-v2-model-output-closure`. Runtime commit `aac9914` (fix(exec): bind Python scenario commands to active runtime) normalizes bare interpreter tokens (`python`, `python.exe`, `python3`, `python3.exe`, case-insensitive, directory-less) to `sys.executable` before executing `post_generation_command`, preserving the original command in diagnostics (`PostGenerationResult.original_command`) and recording the resolved executable (`resolved_executable`). Deployment commit `311e084` pins the bundle (notebook SOURCE_COMMIT=`aac9914c6dcda054736539a0d0ed649cf9865128`, DEPLOYED_BUILD_ID=`aac9914`); bundle = 147 files / 928,175 bytes; identity tests pass (build ID length 7, == SOURCE_COMMIT[:7], canonical==generated notebook, HEAD==SOURCE_COMMIT at pin time).

Recreated clean Python 3.11.9 validation environment (`_workspace\cache\prebenchmark-py311`, pytest 8.4.2, Django 5.2.16, DRF 3.17.1) full gate: **1,834 passed / 32 skipped / 0 failed** (first clean-env attempt exposed missing optional test deps — tabulate, httpx, jinja2 — installed in the clean env only; no repo change). Dataset Validation 285 passed / 5 skipped; Prompt Validation 158 passed; Pipeline Smoke 220 passed / 12 skipped; Metric Verification 169 passed; mypy strict src/benchmark Success (77 files); ruff clean on changed files; compileall clean; bundle rebuild idempotent; notebook valid; all manifest SHA-256 verified (code 87 + 3 .sha256 = 90, data 56, notebook 1). Bundled CLI dry-run `--profile scientific-smoke-v2`: 9 planned / 9 terminal / 9 succeeded / exit 0; source_identity = source_commit 311e084, deployed_build_id 311e084. Real Qwen records remain 0/9; no scientific evidence exists; tag not created; Pilot not authorized; independent audit required before any Kaggle relaunch.

## Pre-Benchmark Final Reproducibility Audit Closure (2026-08-03)

The pre-benchmark reproducibility-and-truth closure on branch `fix/kaggle-smoke-v2-model-output-closure` declares the complete pre-benchmark test environment so it can be recreated purely from project declarations, and records the observed truth. Runtime commit `aac9914` (fix(exec): bind Python scenario commands to active runtime) and deployment commit `311e084` (bundle pin; notebook SOURCE_COMMIT=`aac9914c6dcda054736539a0d0ed649cf9865128`, DEPLOYED_BUILD_ID=`aac9914`) are unchanged. Declaration commits `769d84e` + `e5d9430` extend `pyproject.toml [dev]` + `requirements-dev.txt` with the complete pre-benchmark set: Django==5.2.16, djangorestframework==3.17.1, pytest-django==4.12.0, pytest-asyncio==1.2.0 (required by `--asyncio-mode=auto`), tabulate==0.10.0, httpx==0.28.1, Jinja2==3.1.6, huggingface_hub==0.24.0 (the 1.x line broke positional `hf_hub_download`/`local_dir_use_symlinks` and strict mypy), types-pyyaml>=6.0,<7 (mypy strict yaml stubs), pytest>=8.0,<9. Runtime `[project.dependencies]` and `requirements-smoke-kaggle.lock` untouched.

The environment was deleted and recreated from declarations only (Python 3.11.9, pytest 8.4.2, Django 5.2.16, DRF 3.17.1, pytest-django 4.12.0, tabulate 0.10.0, httpx 0.28.1, Jinja2 3.1.6, ruff 0.15.22, mypy 1.20.2). Complete clean gate on the recreated environment: full suite = **1,833 passed / 32 skipped / 1 failed** (sole failure = `test_notebook_source_commit_matches_deployed_runtime_tree`, structural because the mandated `pyproject.toml` declaration change breaks byte-identity with the pinned `aac9914` SOURCE_COMMIT; frozen artifacts were not modified to force green — reported truthfully); Dataset Validation 285 passed / 5 skipped; Prompt Validation 158 passed; Pipeline Smoke 220 passed / 12 skipped; Dry Run 9/9 succeeded (exit 0); Integration PASS; Metric Verification 169 passed; mypy strict src/benchmark Success (77 files); ruff 93 findings = 468a23a baseline (0 new); compileall clean; bundle build verified (147 files / 928,329 bytes) then `kaggle_upload` restored unchanged; git diff --check clean; tree clean. Historical experiment `exp-20260801-210443` produced **one failed model-output terminal record** under source `6f88823` — preserved, excluded from the current `aac9914` aggregation; current accepted `aac9914` records = **0/9**; no scientific evidence; no tag; no Pilot; no Kaggle launch. Next action after this independent audit: Kaggle engineering preflight only (update the Kaggle code dataset + notebook to the corrected `e5d9430` deployment, then the preflight cell, not the scientific One-Run cell). Superseded by the deployment-only correction `f8d00d7` below: complete clean suite is green (1,834 passed / 32 skipped / 0 failed); aggregation is now `e5d9430`.


## Pre-Benchmark Final Source Repin (2026-08-03) — Deployment-Only Correction

The previous `76a6b16` gate had **1 failure, not a green full suite**: full suite =
**1,833 passed / 32 skipped / 1 failed**. The sole failure was
`test_notebook_source_commit_matches_deployed_runtime_tree`, structural because the
mandated `pyproject.toml` declaration change broke byte-identity with the pinned
`aac9914` SOURCE_COMMIT. **Root cause:** dependency declarations changed
`pyproject.toml` after the `aac9914`/`311e084` deployment pin. **No runtime, prompt,
metric, scenario, evaluator, or data change was needed.**

The exact independently reviewed **deployment-only correction** `f8d00d7`
(`chore(deploy): repin reproducible pre-benchmark source snapshot`, imported via
bundle fast-forward `PRE_BENCHMARK_FINAL_REPIN_EXACT.bundle`, exactly one commit)
re-pins the deployment to the current source snapshot:

1. `kaggle_upload/code/pyproject.toml` gains the six declaration lines
   (`tabulate==0.10.0`, `httpx==0.28.1`, `Jinja2==3.1.6`, `pytest-asyncio==1.2.0`,
   `huggingface_hub==0.24.0`, `types-pyyaml>=6.0,<7`) and is now **byte-identical**
   to the canonical `pyproject.toml` (verified: identical, 1,948 bytes).
2. Both canonical and generated notebooks re-pin
   `SOURCE_COMMIT = e5d943065c6f4158c30a1cbbba39436ab2a7a898` /
   `DEPLOYED_BUILD_ID = e5d9430`. Deployment source snapshot = `e5d9430`;
   deployment correction = `f8d00d7`.
3. Manifests re-verified.

The complete clean gate on the declarations-only environment is now **green**:
full suite = **1,834 passed / 32 skipped / 0 failed** (identity test passes);
Dataset Validation 285 passed / 5 skipped (data unchanged); Prompt Validation 158
passed; Pipeline Smoke 220 passed / 12 skipped; Dry Run 9/9; Integration PASS;
Metric Verification 169 passed; mypy strict Success (77 files); ruff 93 = 93
baseline (0 new); compileall clean; all notebook code cells compile (7/7 + 7/7);
bundle build content-identical (147 files / 928,329 bytes); manifests verified;
no cache files in `kaggle_upload`; tree clean. Historical `exp-20260801-210443`
failed model-output record under `6f88823` remains excluded from the current
 `e5d9430` aggregation; current accepted real records = **0/9**; no scientific
evidence; no tag; no Pilot; no Kaggle launch. Next action after this independent
audit: **Kaggle engineering preflight only** (update the Kaggle code dataset +
notebook to the corrected `e5d9430` deployment, then the preflight cell, not the
scientific One-Run cell).

## Post-Smoke Calibration Closure (2026-08-03)

The post-smoke calibration closure on branch `fix/kaggle-smoke-v2-model-output-closure`
(HEAD `231b0a5`, pushed, local = remote, tree clean) closed the four proven
control defects the real calibration run `exp-20260803-002741` exposed, then
pinned and reconciled the gate:

- **Commit `27c1693`** (runtime + tests): per-attempt atomic regeneration
  (normalize + validate every selected artifact, stage accepted bytes, write
  zero files of the attempt on any guard failure); repair no-progress detection
  (`repair_no_progress` early-stop on an identical repair response hash after
  validation feedback, no new round, consumed calls/tokens retained);
  fail-closed calibration continuation gate
  (`AUTHORIZE_CONTINUOUS_AFTER_CALIBRATION_REVIEW = False`;
  `scientific_failure` prints `CALIBRATION_REVIEW_REQUIRED`, only a deliberate
  human change to `True` authorizes the continuous cell); cooperative deadline
  semantics (deadline checked before every selection/generation/repair call;
  workflow budget exhaustion = scientific terminal
  `scientific_budget_exhausted` with `configured_budget` /
  `actual_elapsed_seconds`; preflight/env/harness/HF timeouts stay engineering
  blockers).
- **Commit `56772fe`** (deployment): notebook re-pin
  `SOURCE_COMMIT = 27c1693e22b1a68be0b299fb146d9ff1e500908b` /
  `DEPLOYED_BUILD_ID = 27c1693`; bundle rebuilt (147 files / 934,495 bytes;
  code 90 / data 56 / notebook 1); manifests verified; both notebooks compile
  7/7 code cells.
- **Commit `231b0a5`** (test-fixture reconciliation): the nine failures of the
  first full gate were **stale constant-output integration fixtures**
  (`test_r4_metric_contract.py`, `test_su0010a_regeneration.py`) that
  accidentally activated the new no-progress early-stop. They were **not
  validly proven pre-existing**: `ec9ba0b` lacked the early-stop, and a detached
  worktree using the main editable installation can import the current branch
  instead of the worktree source. The fixtures now return distinct valid Python
  per call (`_FixedTokenBackend(vary_output=True)` for the three duration tests,
  unique per-index `_SentinelBackend` output, `value = <call_number>` for the
  five bounded-repair fixtures); every expectation was preserved (max_attempts
  3, calls 3/6, `repair_attempts`, `repair_model_calls` 2/4, durations 1.5/2.1,
  tokens 41/59/90, JSONL/reporting identity); dedicated identical-output
  no-progress tests unchanged; new boundary test
  `test_no_progress_and_max_attempts_are_separate_contracts` proves constant
  output → 2 calls + `repair_no_progress` vs distinct outputs → 3 calls /
  2 repairs. Runtime semantics, prompts, scenarios, datasets, evaluators,
  strategies, and metrics were never changed.

Final gate: full suite = **1,849 passed / 32 skipped / 0 failed**; mypy strict
`src/benchmark` Success (77 files); ruff 93 = 93 baseline (identical line-set,
0 new); compileall clean; bundle content-identical; `git diff --check` clean;
tree clean. Calibration evidence `exp-20260803-002741` (9 terminal records /
0 succeeded / 8 failed / 1 timed_out / 81 model calls / 118,211 tokens) is
**preserved and not an accepted scientific comparison**; latest real
calibration = **0/9**. No Kaggle rerun; no tag; no merge; Pilot not authorized.
Next action after this independent audit: **one selective calibration canary
only** (not a full relaunch, not a fine-tune, not a tag/merge).
Sentinel: `POST_SMOKE_CALIBRATION_CLOSURE_AUDIT_REQUIRED`.

## Final Selective Canary Readiness Closure (2026-08-04)

The independent GPT-5.6 Thinking audit at `f727b3e` **rejected canary readiness**
even though the full suite was green, based on three independently reproduced
blockers. All three are closed on branch `fix/kaggle-smoke-v2-model-output-closure`
(HEAD `356722b`, pushed, local = remote, tree clean):

- **Blocker 1 — per-call cooperative deadline.** Direct reproduction: 1s
  timeout, 3 selected artifacts, budget advanced after call 1 → **3 model calls
  and false success**. Commit `50ec2c1` checks the workflow deadline before every
  selection/generation/repair model call; an in-flight call returning beyond the
  deadline consumes/records its tokens, makes no next call, writes none of the
  staged attempt, and returns the failed scientific terminal
  `scientific_budget_exhausted` with truthful elapsed time and budget. The same
  guard applies to every internal Iterative Agent call, not only before
  `analyze_impact()`. Direct adversarial proofs: generation (1 call, count 0,
  15 tokens), repair (2 calls, `repair_model_calls == 1`, repair tokens
  retained), iterative agent (1 call, `model_call_budget_exhausted`, 50 tokens
  preserved).
- **Blocker 2 — atomic metric truth.** Direct reproduction: **0 writes but
  `regenerated_artifact_count = 1`** when an artifact was rejected. On atomic
  attempt abort, all staged `generated` statuses become `aborted` or `rejected`,
  `regenerated_artifact_count = 0`, preserved response hashes/evidence remain
  available; an all-valid attempt still commits every artifact exactly once.
  Metric/evidence truth, not a scientific formula change. Commit `356722b`
  aligns the affected tests with the truthful staged statuses.
- **Blocker 3 — dedicated selective canary cell.** The generic one-run cell
  selects `todo-smoke-001 / monolithic` (execution-plan order is scenario first,
  then strategies), NOT selective. Commit `28ecc5a` adds a dedicated, separately
  named Selective Calibration Canary cell (`selective-calibration-canary-cell`):
  `--strategy selective --max-runs 1 --new-experiment --backend kaggle-qwen
  --profile scientific-smoke-v2 --max-attempts 3 --max-completion-tokens-per-call
  1024 --max-total-workflow-tokens 0 --timeout 300 --hf-sync`, isolated output
  `runs/selective_calibration_canary`, NO `--auto-resume-hf`,
  `AUTHORIZE_CONTINUOUS_AFTER_CALIBRATION_REVIEW = False`.
  `_verify_selective_canary()` asserts exactly one current-source RunRecord
  `todo-smoke-001 / selective`, model identity `qwen:1:int8`, model calls > 0,
  terminal scientific success/failure outcome, HF `recovery_uploaded`, checkpoint
  `total_planned = 3 / completed = 1 / pending = 2`.

Deployment pinned: `SOURCE_COMMIT = 50ec2c1ca43c230aed4538be32ca7dab2ccc22e5`,
`DEPLOYED_BUILD_ID = 50ec2c1`; bundle rebuilt (147 files / 948,250 bytes; code
90 / data 56 / notebook 1); content-identical rerun (tree hash
`3b8d5b0ebf5e3ab8`); all 8 bundle notebook code cells compile.

Final gate: full suite = **1,856 passed / 32 skipped / 0 failed**; grouped
per-category 629 passed / 1 skipped; scripted dry run `--profile
scientific-smoke-v2` into a fresh dir = 9/9 exit 0 (the default `runs` dir held
a stale checkpoint causing `ReportRebuildError`, not a code defect); mypy strict
`src` Success (77 files); ruff 0 new findings (175 pre-existing repo-wide, 19
pre-existing E501 in `test_r4_token_and_metrics.py`); compileall clean; `git
diff --check` clean; tree clean. Calibration evidence `exp-20260803-002741`
remains **preserved, 0/9 success, not accepted scientific evidence**. No Kaggle
rerun; no tag; no merge; Pilot not authorized; **no stable release claimed**.
Next action after this independent re-audit: **run the dedicated selective
calibration canary cell only** (not the generic one-run cell, not the continuous
cell, not a full relaunch, not a fine-tune, not a tag/merge).
Sentinel: `FINAL_SELECTIVE_CANARY_READINESS_AUDIT_REQUIRED`.

## Selective Calibration Canary Result (2026-08-04)

The dedicated selective calibration canary was executed on Kaggle under the
pinned bundle (source/build `50ec2c1`) and its result is recorded in
`selective_updates/records/SELECTIVE-CANARY-RESULTS-2026-08-04.md`.

- **Canary result `exp-20260804-133523`** (`todo-smoke-001 / selective`):
  **failed / `model_output`**, 4 model calls / 5,804 tokens / 257.596 s,
  3 selected / 2 preserved / **0 written**; initial 3 calls / 3,372 tokens;
  repair 1 call / 2,432 tokens; HF `recovery_uploaded`; checkpoint 1 completed /
  2 pending.
- **Qwen output defects:** `todo/models.py` `max_length=5` (the `MEDIUM` value
  has length 6); duplicated `Priority(models.TextChoices)` in
  `todo/serializers.py` and `todo/views.py`. The first repair was byte-identical
  to the initial response, so `repair_no_progress` stopped the round and the
  atomic application wrote zero files.
- **Harness vs model:** versus the previous selective run the canary used 41.6%
  fewer tokens, 33.3% fewer calls, and was 22.4% faster — but the initial
  generation tokens (3,372) and the three output SHA-256 hashes were identical.
  The harness safety controls (per-call deadline, no-progress detection, atomic
  writes, fail-closed continuation gate) worked exactly as designed, while
  **Qwen code quality did not improve**.
- **Incidental monolithic run `exp-20260804-133016`** (6 calls / 7,927 tokens /
  300.165 s / `scientific_budget_exhausted`, 0 written) is diagnostic evidence
  only — NOT the authorized canary and NOT an accepted comparison.
- **Continuous cell:** correctly blocked fail-closed with
  `CALIBRATION_REVIEW_REQUIRED`; it made no additional scientific calls.
- **Current scientific truth:** accepted current dedicated canary records = 1,
  successful = 0; the full current 9-record experiment is **not run**;
  merge/tag/Pilot/Kaggle **not authorized**; **no stable release claimed**.

Decision from the independent audit: harness safety controls worked; Qwen code
quality did not improve. Next action: independent result audit
(`SELECTIVE_CANARY_RESULT_AUDIT_REQUIRED`), then a deliberate decision between
repeating the dedicated selective canary and proceeding to the full 9-record run.

R6_ACCEPTED_FREEZE_AND_PUBLISH_AUTHORIZED

## Final Qwen 14B NF4 Preflight Closure (2026-08-05)

The independent audit reproduced three preflight blockers on the `5ef6438`
state (full suite was green there, but the audit rejected real preflight). All
three are closed on branch `fix/kaggle-smoke-v2-model-output-closure`:

1. **Canary used `SELECTIVE_CANARY_OUTPUT_DIR` before assignment.** The
   definition lived inside the `selective-calibration-canary` cell while
   `CANARY_PREFLIGHT_DIR = SELECTIVE_CANARY_OUTPUT_DIR / "preflight"` referenced
   it earlier — a `NameError` at canary run time. Fix A moved the definition to
   the `setup-cell` (right after `OUTPUT_DIR`) and removed the duplicate
   assignment.
2. **Preflight required exactly one visible GPU.** `EXPECTED_VISIBLE_GPU_COUNTS
   = (1, 2)` now accepts real 2×Tesla T4 environments and reports
   `FAIL (N; expected 1 or 2)` otherwise (Fix B).
3. **Numeric version dirs produced a `qwen:1:*` readable identity.**
   `_checkpoint_identity_slug` maps e.g. `.../14b-instruct/1` → `14b-instruct-v1`
   → `qwen:14b-instruct-v1:bnb-nf4:cfg-<12hex>` in `compute_model_identity` and
   `checkpoint_basename` (Fix C).

Commit A `0aa705d` (runtime + tests + notebook) and Commit B `cc7846b`
(deployment repin) are pushed, local = remote, tree clean. Official gate =
declared clean environment (Python 3.11.9 / pytest 8.4.2): full suite
**1,890 passed / 32 skipped / 0 failed**; Dataset 285/5; Prompt 174; Pipeline
Smoke 223/12; Dry Run 9/9 (exit 0); Metric Verification 169; Ruff 0 new (91
pre-existing baseline); mypy strict Success (77 files); compileall clean;
notebook 8/8 + 8/8 compile; builder content-identical (147 files /
963,067 bytes). Regression proofs: **2-GPU preflight = PASS** and **canary
reaches subprocess construction without NameError**. No Kaggle run, no canary,
no continuous, no model/quantization/prompt/data/scenario/evaluator/metric
change, no GPTQ/AWQ/GGUF/vLLM, no merge/tag/Pilot. **No real 14B result and no
stable release claimed**; accepted real records remain 0/9. Next action after
independent audit = **Kaggle engineering preflight cell only**.
Sentinel: `QWEN14B_FINAL_PREFLIGHT_CLOSURE_AUDIT_REQUIRED`.

## Qwen 14B NF4 Transformers v4 Loader Closure (2026-08-05)

The independent OOM audit reproduced the real preflight OOM on the `9fd4eee`
state (full suite was green there, but the real load OOM'd on Kaggle). Root
cause: transformers was unpinned in the Kaggle runtime, image drift installed
**5.0.0**, and the 5.0.x loader materialized the **14B BF16 weights on GPU
before BNB-NF4 quantization** — OOM after 232.412 s at ~75% of 579 checkpoint
params (tried 136 MiB; GPU 1 free 46.81 MiB / allocated 14.38 GiB; runtime
Python 3.12.13 / transformers 5.0.0 / bitsandbytes 0.49.2 / accelerate 1.14.0 /
torch 2.10.0+cu128). All fixes are closed on branch
`fix/kaggle-smoke-v2-model-output-closure`:

1. **Transformers pinned to `==4.57.6`** in `requirements-smoke-kaggle.lock` and
   `requirements-kaggle.txt`; torch stays unpinned (Kaggle image provides its
   GPU torch build — no torch pin in the lock).
2. **Fail-closed preflight version check**: `_REQUIRED_IMPORTS` now requires the
   exact `"4.57.6"`, so `dependency_import_verification` FAILs with
   `transformers=5.0.0 (expected 4.57.6)` before staging/model load; absent
   transformers also FAILs.
3. **Notebook install-lock-cell**: `EXPECTED_RUNTIME` gains
   `"transformers": ("transformers", "transformers", "4.57.6")` with the
   fail-closed mismatch check; setup-cell repinned to `SOURCE_COMMIT =
   41e9ad70c86ac696ce6ceaacd6b6892889bcc48a` / `DEPLOYED_BUILD_ID = 41e9ad7`.
4. **BNB loads pass `low_cpu_mem_usage=True`** in
   `kaggle_qwen_backend._load_model` for `bnb-int8` and `bnb-nf4` (fp16
   unchanged), so the 4.57.x loader streams/quantizes in place instead of
   materializing the full-precision temporary copy.
5. **Static preflight metadata on load failure**: `_static_model_metadata`
   reads `config.json` + CUDA discovery (no weight load) and fills
   `model_identity` / `checkpoint_basename` / `checkpoint_quantization_method` /
   `gpu_count` / `gpu_name` even when the probe OOMs or fails.

Commit A `41e9ad7` (runtime + tests + notebook) and Commit B `920ab9b`
(deployment repin) are pushed, local = remote, tree clean. Gate = ambient
Python 3.11.5 / pytest 9.1.1 (declared clean env `_workspace\cache\
prebenchmark-py311` is NOT present locally — independent audit must recreate it
for the official gate): full suite **1,898 passed / 32 skipped / 0 failed**;
Ruff 0 new (86 pre-existing baseline); mypy strict Success (77 files);
compileall clean; notebook cells compile canonical + bundled; bundle pin
identity PASS; bundle integration 32 passed; builder content-identical (147
files / 964,859 bytes). Regression proofs: **preflight FAILs on transformers
5.0.0 / NOT_INSTALLED before load**, **BNB int8 + NF4 loads pass
`low_cpu_mem_usage=True` (fp16 does not)**, **static model/GPU metadata
preserved on failed probe**. No Kaggle run / canary / continuous / merge / tag /
Pilot; no model, quantization, prompt, data, scenario, evaluator, or metric
change; no GPTQ/AWQ/GGUF/vLLM (no new backend); **no real 14B result and no
stable release claimed**; accepted real records remain 0/9. Next action after
independent audit = **Kaggle engineering preflight cell only**.
Sentinel: `QWEN14B_V4_LOADER_CLOSURE_AUDIT_REQUIRED`.
