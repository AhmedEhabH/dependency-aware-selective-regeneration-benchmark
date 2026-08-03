# Master Implementation Plan

## Dependency-Aware Selective Regeneration for LLM-Assisted Software Evolution

## Authoritative Current Execution Track

```text
R4 = accepted and frozen (f5ae826)
R5 = accepted and frozen (7761c48)
R6 = ACCEPTED AND FROZEN (949e9c2) — freeze record and milestone-branch publication authorized
Push = next (publish with upstream, verify local/remote equality)
Real Smoke = 0/9 (local scripted 9/9; bundled CLI dry-run 9/9)
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

R6_ACCEPTED_FREEZE_AND_PUBLISH_AUTHORIZED
