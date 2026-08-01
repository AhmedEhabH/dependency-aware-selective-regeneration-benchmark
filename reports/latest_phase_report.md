# R4 Token and Metric Contract — Single-Pass Completion Report

## 1. Executive Decision

This report records the single-pass completion of R4 (token limits and truthful workflow metrics) on branch `experiment/three-arm-smoke-v2`. The R4 working tree that existed at starting HEAD `b8724cc` was preserved, all remaining root defects from the binding closure contract were corrected, nominal tests were replaced with executable production-path tests, four direct scripts were run outside Pytest, RF-3 was reviewed, gates 9.1 through 9.6 were run in the fixed order, and one code commit plus one documentation commit were created. R4 was subsequently re-audited, the two audit-correction commits were accepted, and R4 was frozen — see Section 24. R5 is authorized and in progress. Roadmap R5 → R6 → Kaggle is preserved. No README change, no tag, and no scientific-result claim is made.

## 2. Requested and Actual Model

```
Requested model:  deepseek-v4-flash-free (OpenCode Zen)
Actual footer:    opencode/deepseek-v4-flash-free (matches the requested model id)
Mode:             Build
Provider:         OpenCode Zen
```

The model identity is taken from the session/UI footer available to OpenCode, not inferred from the request.

## 3. Starting Git Identity

```
Branch:        experiment/three-arm-smoke-v2
Starting HEAD: b8724cc  docs(audit): record R3D final freeze candidate
Code commit:   e87d4ad  fix(metrics): separate per-call limits and workflow totals
```

At session start the working tree held only authorized R4 production/test files and four untracked documentation files. `kaggle_upload/` was clean at HEAD and was never edited; only `project\seven_arm_benchmark.py` was in scope among root files. Evaluator asset `M` entries in `git status` are CRLF renormalization only (`core.autocrlf=true`); `git diff --ignore-all-space` over those paths is empty, so they were never staged.

## 4. Near Goal and Far Goal

Near goal: complete R4 end-to-end in one bounded pass — production corrections, real test rewrites, four verification scripts, RF-3 review, gates 9.1–9.6, code commit, a 2,200–3,000-word report, and a documentation commit. Far goal: after independent audit and freeze, run R5 (nine local records), RF-4 cleanup and rerun, R6 (bundle and push), nine real Qwen Kaggle runs, an independent results audit, the `v2.0.0-scientific-smoke` tag, and the Pilot. No far-goal step was performed in this session.

## 5. Scope Ledger and Restored Files

No files were restored or reverted in this session. The working tree was already scoped to the authorized R4 change set at session start. The pre-commit scope audit (§10 of the directive) produced exactly:

```
CODE_COMMIT_PRODUCTION_FILES (14):
  seven_arm_benchmark.py
  src/benchmark/checkpoint/persistence.py
  src/benchmark/config/models.py
  src/benchmark/core/models.py
  src/benchmark/execution/budgets.py
  src/benchmark/execution/pipeline.py
  src/benchmark/execution/regeneration.py
  src/benchmark/execution/runner.py
  src/benchmark/llm/dry_run_backend.py
  src/benchmark/llm/kaggle_qwen_backend.py
  src/benchmark/llm/mock_backend.py
  src/benchmark/llm/openrouter_backend.py
  src/benchmark/statistics/reporting.py
  src/benchmark/strategies/iterative_agent.py

CODE_COMMIT_TEST_FILES (7):
  tests/unit/execution/test_r4_token_and_metrics.py      (new)
  tests/integration/test_r4_metric_contract.py           (new)
  tests/integration/test_scientific_smoke_v1_fixes.py
  tests/integration/test_su0010a_regeneration.py
  tests/integration/test_su0011_iterative_agent.py
  tests/unit/execution/test_r3d_wiring.py
  tests/unit/statistics/test_reporting.py
```

Asserted: no docs, no notebook, no evaluator asset or `.sha256` hash, no README, no generated bundle, and no unrelated checkpoint or script file in code staging. The three `tests/evaluator_assets/todo_smoke_*_checks.py` working-tree `M` entries are CRLF-only and were excluded.

## 6. Root Defects Found

The audit identified ten root defects, each confirmed and corrected:

- **D1 — Per-call and aggregate limits conflated.** One `max_tokens` value was used for both per-call completion limits and workflow totals; the executor and Agent then could not distinguish them.
- **D2 — Frozen conflict rule not enforced at construction.** `both zero → unlimited / one positive → it / both positive equal → it / both positive different → ValueError` was not implemented in `PipelineConfig`, `RunnerConfig`, or `ExecutionConfig`.
- **D3 — Legacy aggregate fields misleading.** `total_workflow_*` did not equal the sum of selection + regeneration + repair stages.
- **D4 — Repair counted as initial regeneration.** Repair executor calls were merged into the regeneration bucket, hiding true repair cost.
- **D5 — Agent budget decremented ambiguously.** The Agent used a single `max_tokens` argument instead of explicit `max_completion_tokens_per_call` and `remaining_total_workflow_tokens`.
- **D6 — Scientific stage durations not cumulative.** Migration/baseline/evaluator durations across repair attempts were overwritten instead of summed.
- **D7 — `TokenUsage` did not enforce its own identity** (integers only, non-negative, non-bool).
- **D8 — Resolved total not forwarded to every metadata boundary**, so `model_metadata` could show a different limit than the Runner used.
- **D9 — Persistence/reporting lacked full R4 fields** (repair stage, per-stage tool/selection metrics, artifact counts).
- **D10 — Nominal `assert True` tests.** Executor/Agent/boundary tests exercised arithmetic helpers only, not the real production path.

## 7. Production Corrections by File

| file | defect/contract | exact change | direct evidence | tests |
|---|---|---|---|---|
| `src/benchmark/execution/budgets.py` | D1/D5 | Single resolver `resolve_completion_allowance(*, max_completion_tokens_per_call, remaining_total_workflow_tokens, prompt_tokens)`: zero total → per-call; otherwise `max(0, min(per_call, remaining - prompt))`; ValueError on bool/negative (budgets.py:145-172) | Script A/B; unit resolve tests | test_r4_token_and_metrics.py:183-267, 519 |
| `src/benchmark/execution/pipeline.py` | D2 | `PipelineConfig.__post_init__` (pipeline.py:33-49) + `resolved_max_total_workflow_tokens` property enforcing frozen conflict rule (pipeline.py:51-64) | Script D `2048 / 9000`; pytest.raises(ValueError) on differing positives | test_r4_metric_contract.py (CLI/config section) |
| `src/benchmark/execution/runner.py` | D2/D3/D4/D6 | `RunnerConfig` validation (runner.py:224-252); `_WorkflowMetricAccumulator` (runner.py:40-194) with `add_selection`/`add_code_generation(is_repair=...)`/`add_scientific` cumulative durations; `is_repair = iteration > 0` (runner.py:1348-1349); executor/Agent calls pass explicit limits (runner.py:866, 1004, 1201-1202, 1269-1270, 1339-1340) | §6.5 duration sums; §6.4 agent tests; full suite | test_r4_token_and_metrics.py E section; test_r4_metric_contract.py J/M sections |
| `src/benchmark/config/models.py` | D2 | `ExecutionConfig` validation + resolved-total property (config/models.py:57-67) | unit validation tests | test_r4_token_and_metrics.py |
| `src/benchmark/execution/regeneration.py` | D1/D4 | Executor signature gains explicit `max_completion_tokens_per_call`/`remaining_total_workflow_tokens` (regeneration.py:101-110); `local_remaining = max(0, local_remaining - usage.total_tokens)` (regeneration.py:147, 277) | Script A/B | test_r4_token_and_metrics.py §6.1 |
| `src/benchmark/strategies/iterative_agent.py` | D5 | `analyze_impact`/`revise_plan` accept `max_completion_tokens_per_call` + `remaining_total_workflow_tokens`; `local_remaining` decrement (iterative_agent.py:264-283, 316, 435-462, 478); `MAX_AGENT_CALLS = 8` | Script C1/C2 | test_r4_token_and_metrics.py §6.2 |
| `src/benchmark/core/models.py` | D7 | `TokenUsage` integer/bool/non-negative validation; R4 `RunRecord` fields (selection/regeneration/repair + totals, artifact counts, token_accounting_mode) | unit TokenUsage tests | test_r4_token_and_metrics.py A section |
| `src/benchmark/checkpoint/persistence.py` | D9 | `RunRecordData` R4 fields; `RunRecordStore.append/load_all` JSONL round-trip (persistence.py:187-233) | §6.6 test; Script D JSONL reload | test_r4_metric_contract.py M section |
| `src/benchmark/statistics/reporting.py` | D9 | `NotebookExporter._serialize_record` emits all R4 fields (reporting.py:97-156) | §6.6 test; Script D report | test_r4_metric_contract.py M section |
| `seven_arm_benchmark.py` | D8/D9 | `resolved_total` computed once (line 1191); `record_dict` carries `max_completion_tokens_per_call`/`max_total_workflow_tokens` (lines 1276-1277); `_to_run_record_data` forwards limits + `max_attempts` into `model_metadata` (lines 171-177) | Script D all five boundaries `2048 / 9000` | test_r4_metric_contract.py I section |
| `src/benchmark/llm/*` (dry_run/kaggle_qwen/mock/openrouter) | D1 | `count_prompt_tokens`/limit forwarding alignment; backend error propagation preserved | named-host tests | test_scientific_smoke_v1_fixes.py etc. |

## 8. Executor Production-Path Evidence

The five §6.1 executor tests instantiate and execute `SharedRegenerationExecutor` with real temp files. Sentinel results verified: unlimited → limits `[4096,4096,4096]`, 3 calls, success, 24 tokens total; positive-total overrun → limits `[20,2]`, 2 calls, 36 tokens retained, third file untouched (`"original content"`); zero-allowance → 0 backend calls with failure `Token budget exhausted`; backend overrun → `Backend overrun` with usage preserved; positive total 30 / per-call 20 → `[20,2]`. All five instantiate the real executor.

## 9. Agent Production-Path Evidence

The eight §6.2 agent tests instantiate `IterativeRepositoryAgentStrategy`, call `begin_run`, and exercise both `analyze_impact` and `revise_plan`. Sentinel evidence: initial call receives the per-call limit (captured `[450,390,330]` under total 500 with 3 calls); prediction usage is incremental, not cumulative; zero allowance → 0 backend calls with `no paths selected`; eight-call cap → exactly 8 backend calls at `[4096]*8` with `no remaining agent calls`. No `assert True` remains.

## 10. Entry/Persistence/Reporting Evidence

`test_public_runner_to_jsonl_to_reporting_preserves_metric_identity` runs the full boundary trace `RunRecord → record_dict → RunRecordData → JSONL reload → NotebookExporter` with sentinel responses `[18,18,23]` and `validation_command exit(1)`. Asserted exact identities:

```
selection_total = prompt + completion = 0 + 0 = 0
regeneration_total = 11 + 7 = 18
repair_total = 30 + 11 = 41
workflow_tokens = selection + regeneration + repair = 0 + 18 + 41 = 59
workflow_calls = 0 + 1 + 2 = 3
workflow_duration = stage sum (isclose 1e-9)
token_usage.total = 59 = workflow_tokens
model_metadata = max_completion_tokens_per_call "2048", max_total_workflow_tokens "9000"
```

## 11. Test Architecture and Exact Test Changes

- `tests/unit/execution/test_r4_token_and_metrics.py` — now 66 tests. Added `_ExecutorCaptureBackend`, `_AgentCaptureBackend`, `_make_executor_context`, `_make_agent_context`, `_final_action`, `_tool_action`; replaced helper-only bodies of `test_zero_allowance_skips_backend_call`, `test_backend_token_overrun_fails_closed_and_preserves_usage`, `test_three_files_each_receive_4096_when_total_unlimited`, `test_positive_total_ceiling_reduces_later_call`, and all eight §6.2 agent tests. The repair-loop test asserts one repair executor call at `max_attempts=3` because `record_attempt()` runs at loop top before `can_attempt` re-check.
- `tests/integration/test_r4_metric_contract.py` — now 31 tests. Added `_capture_cli_config` (monkeypatches `benchmark.execution.pipeline.PipelineConfig`/`BenchmarkPipeline`); rewrote `test_cli_explicit_limits_reach_pipeline_config` to assert real config `2048/9000` and result dict; added legacy-only, equal-positive, and differing-positive `pytest.raises(ValueError)` cases; `_make_runner` gained `canonical_project_root`/`python_executable`; `_make_scenario` gained `evaluator_asset`.
- §6.4: `test_public_agent_selection_tokens_are_not_double_counted` (60 selection + 15 regen = 75), `test_public_agent_tool_duration_is_submetric_only` (tool duration is a submetric of selection; stage-sum identity via `math.isclose` 1e-9; the tool is wrapped with a deterministic 50 ms sleep so wall-clock tool duration is measurably > 0), `test_public_agent_failed_run_preserves_selection_and_repair_metrics` (180 selection / 15 regen / 15 repair, 1 repair attempt, total 210).
- §6.5: migration duration exact `0.0`; `test_public_repair_accumulates_baseline_duration_across_attempts` (2 × 0.5 = 1.5 exact; evaluator variant 3 × 0.7 = 2.1 exact); `test_public_total_duration_equals_stage_sum`.
- §6.6: boundary trace (above) with `token_accounting_mode == "fixture_or_approximate"`.

## 12. Four Direct Script Results

```
SCRIPT_A_LIMITS= [4096, 4096, 4096]     SCRIPT_A_CALLS= 3
SCRIPT_A_STATUS= success                 SCRIPT_A_USAGE= 24   SCRIPT_A_FILES= 3

SCRIPT_B_LIMITS= [20, 2]                 SCRIPT_B_CALLS= 2
SCRIPT_B_STATUS= failed closed           SCRIPT_B_USAGE= 36
SCRIPT_B_FAILURE= Backend overrun for src/b.py: completion_tokens 8 > allowance 2
SCRIPT_B_THIRD_FILE_CHANGED= False

SCRIPT_C1_BACKEND_CALLS= 0               SCRIPT_C1_REGEN_CALLS= 0
SCRIPT_C1_SELECTION_USAGE= 0             SCRIPT_C1_STATUS= blocked_no_allowance
SCRIPT_C1_FAILURE= iterative_agent: no paths selected after exploration

SCRIPT_C2_BACKEND_CALLS= 8               SCRIPT_C2_LIMITS= [4096]*8
SCRIPT_C2_STATUS= bounded                SCRIPT_C2_FAILURE= iterative_agent: no remaining agent calls

SCRIPT_D_PIPELINECONFIG= 2048 / 9000     SCRIPT_D_RUN_STATUS= succeeded
SCRIPT_D_RECORD_DICT= 2048 / 9000
SCRIPT_D_RECORDDATA_METADATA= 2048 / 9000
SCRIPT_D_JSONL_RELOAD= 2048 / 9000
SCRIPT_D_REPORT= 2048 / 9000
SCRIPT_D_REPORT_TOTAL_WORKFLOW_TOKENS= 15
```

All §7 acceptance values were met. The scripts were temporary, outside tracked paths, and not committed.

## 13. RF-3 Review

```
[PASS] one allowance resolver/one frozen rule    budgets.py:145-172; pipeline.py:33-64; runner.py:224-252; config/models.py:57-67
[PASS] executor decrements local total           regeneration.py:147, 277
[PASS] Agent decrements local total              iterative_agent.py:271, 316, 444, 478
[PASS] no ambiguous max_tokens in R4 calls       runner.py:866, 1004, 1201-1202, 1269-1270, 1339-1340 (explicit kwargs)
[PASS] one metric accumulator                    runner.py:40 _WorkflowMetricAccumulator; as_record_fields runner.py:135
[PASS] no repair inside initial regeneration     runner.py:1348-1349 is_repair = iteration > 0
[PASS] no double-counted Agent deltas            integration: test_public_agent_selection_tokens_are_not_double_counted
[PASS] no double-counted tool duration           integration: test_public_agent_tool_duration_is_submetric_only
[PASS] resolved total reaches every metadata boundary   seven_arm_benchmark.py:1191,1206,1276-1277,171-177; Script D
[PASS] complete persistence/reporting forwarding persistence.py:187-233; reporting.py:97-156; §6.6 test
[PASS] no duplicate repair_attempts              runner.py:117 (single += 1 per repair call)
[PASS] no unrelated modified code/test files     §5 scope ledger; git status post-commit clean except CRLF-only evaluator assets
```

Passing items were not refactored for aesthetics.

## 14. Focused and Integration Gate Results

```
Gate 9.1  test_r4_token_and_metrics.py          66 passed, 0 failed, 0 skipped   (run before and after code commit)
Gate 9.2  test_r4_metric_contract.py            31 passed, 0 failed, 0 skipped   (run before and after code commit)
Gate 9.3  r3d_wiring + scientific_smoke_v1_fixes + su0010a + su0011   177 passed, 0 failed
Gate 9.4  test_todo_smoke_evaluator_assets.py   50 passed, 1 skipped, 0 failed
```

Named hosts run separately (`+ test_reporting.py`): 194 passed.

## 15. Full Suite Result

```
command: python -m pytest -q
exit:    0
result:  1576 passed, 32 skipped, 0 failed
run:     after code commit (post final model_metadata edit)
```

The 32 skips are pre-existing environment-dependent skips (HF token, CUDA, etc.). No R4 test skips. The count is the exact final command output, not a reused earlier count.

## 16. Ruff, Mypy, Compileall, and Diff Evidence

Ruff (all 21 authorized changed Python files): 50 findings — 8 pre-existing identical tracked-file findings at shifted line numbers, plus E501s in the two new R4 test files that existed before this session's edits (my new lines are clean) and one pre-existing B008 in `_FixedTokenBackend`. One new ARG001 was found and fixed during this session: `_to_run_record_data`'s `max_attempts` became unused when `repair_attempts` moved to the accumulator; it is now forwarded into `model_metadata`.

Mypy `--strict` (14 production files): 10 errors, all in `seven_arm_benchmark.py`, mapping 1:1 to HEAD baseline errors (verified in a temporary worktree at `b8724cc`); 13 `src/benchmark` files clean. Zero new errors.

Compileall on `src\benchmark seven_arm_benchmark.py` and both R4 test files: exit 0. `git diff --check`: exit 0.

## 17. Code Commit Scope and Hash

```
e87d4ad fix(metrics): separate per-call limits and workflow totals
21 files changed, 3052 insertions(+), 307 deletions(-)
```

Scope matches §5 exactly. `git show --stat` output printed during the session.

## 18. Documentation Updates and Commit Scope

The documentation commit `docs(state): record R4 completion pending audit` stages only the §12 documentation/state files: `docs/ONE_PASS_PHASE_EXECUTION_PROTOCOL.md`, `docs/R3D_INDEPENDENT_AUDIT_AND_FREEZE_REPORT.md`, `docs/R4_PRECOMMIT_ROOT_AUDIT_AND_SINGLE_PASS_COMPLETION.md`, `docs/phase_specs/R4_SINGLE_PASS_SPEC.md`, `docs/phase_specs/R4_FINAL_PRECOMMIT_CLOSURE.md`, `docs/PROJECT_HANDOFF.md`, `docs/V2_R3B_TO_KAGGLE_NO_DISCRETION_EXECUTION_SPEC.md`, `reports/latest_phase_report.md`, `selective_updates/CHANGE_INDEX.md`, `selective_updates/records/TECHNICAL-DEBT-AND-REFACTOR-SCHEDULE.md`, and the new `selective_updates/records/R4-TOKEN-AND-METRIC-CONTRACT.md`. No production or test file is staged.

## 19. Closed and Remaining Technical Debt

```
remaining R4 TD-0 = 0
remaining R4 TD-1 = 0
```

All ten root defects (D1–D10) are closed. Remaining open debt is outside R4 scope: `TD-R4-001` closed; `TD-R5-001` (nine local records) pending; `TD-KAGGLE-001` (bundle push and Kaggle execution) pending.

## 20. Known Limitations

- Wall-clock tool duration in the agent is quantized to `0.0` at `time.monotonic()` resolution for fast tool calls; the §6.4 test uses a deterministic 50 ms tool wrapper and asserts `> 0` and the stage-sum identity, not an exact value.
- `selection_*` metrics are exactly `0` for monolithic strategies whose `analyze_impact` returns a zero-usage prediction; this is asserted as `== 0` where deterministic and justified.
- With `max_attempts=3`, the iterative repair loop executes only one repair executor call (loop-top `record_attempt()` before `can_attempt` re-check); asserted totals use 15, not 30.
- The two R4 test files carry pre-existing E501 lines and one B008 (default `TokenUsage` in `_FixedTokenBackend`) that predate this session's edits; no new lint findings were introduced.
- Ruff and Mypy on `seven_arm_benchmark.py` still report pre-existing HEAD baseline findings at shifted line numbers (documented with the HEAD worktree output above).

## 21. Project Position and Next Authorized Action

Position: R4 frozen at the explicit acceptance/freeze commit `f5ae826`; R5 correction complete pending independent re-audit. Nine non-dry scripted production records produced. Rewritten R5 commits: `875e4d1` execution fix (2 files), `ee148fa` test proof (3 files), audit docs commit. Next authorized action: independent R5 re-audit, then bounded RF-4/R6 bundle-builder correction, then R6 (bundle and push).

## 22. Independent Audit Handoff

Independent audit must verify: the frozen conflict rule at every constructor; executor/Agent local-total decrement; stage separation and `repair_attempts` semantics; cumulative scientific durations; the boundary trace identity; the four script outputs; the full-suite count; the commit scopes and hashes; and the absence of `assert True`. All evidence commands and outputs are recorded above and in the commit itself.

## 23. R4 Audit Corrections Addendum

A re-audit of the R4 evidence was performed at starting HEAD `ccdb49c` (branch `experiment/three-arm-smoke-v2`, clean tree, `core.autocrlf=true`, repo root at `project/`). Two defects were found and corrected.

### Defect A — exact workflow-budget exhaustion reopened an exhausted budget as unlimited

**Root cause:** `0` was overloaded as both "no total workflow limit" and "configured limit exhausted". On exact exhaustion the runtime remaining value hit `0`, and `resolve_completion_allowance` returned the full per-call allowance for `0`, so the exhausted budget reopened as unlimited (a second generation ran after the budget was consumed).

**Fix (internal representation):** `None` = unlimited runtime allowance; `0` = exhausted configured allowance; positive integer = remaining configured allowance. The public config meaning of zero as unlimited is preserved.

- `budgets.py`: new `runtime_remaining_total_tokens` property — `None` when `has_total_token_limit` is False, else `max(0, _max_tokens - _state.total_tokens)`; `resolve_completion_allowance(remaining_total_workflow_tokens: int | None)` returns the per-call limit for `None`, `0` for exhausted `0`, and `max(0, min(per_call, remaining - prompt))` for positive.
- `regeneration.py`: `SharedRegenerationExecutor.execute` default changed to `None`; budget accounting guarded by `has_limit`.
- `iterative_agent.py`: `analyze_impact`/`revise_plan` defaults changed to `None`; accounting guarded by `has_limit`.
- `runner.py`: all five call sites (867, 1005, 1202, 1270, 1340) forward `self._budget.runtime_remaining_total_tokens`.

**Regression tests (5 groups):** executor exact exhaustion (limit 20, consume exactly 20, one call, second file not generated, explicit `Token budget exhausted before src/b.py`); analyze-impact exact exhaustion; revise-plan exact exhaustion; unlimited-budget preservation distinguishing all three runtime states; and integration-level coverage reaching real production code via `BenchmarkRunner` (`_ExactExhaustToolBackend`).

### Defect B — evaluator integrity was platform-dependent

**Root cause:** the committed `.sha256` fingerprints and the committed evaluator `.py` blobs are canonical LF, but on Windows `git restore` produced CRLF working-tree bytes, so the raw SHA-256 of the working tree mismatched the committed values for all three evaluator files.

**Fix:** `.gitattributes` pins `tests/evaluator_assets/todo_smoke_*_checks.py` to `text eol=lf`; the three working-tree files were rewritten to canonical LF with zero character changes.

**Proven for all three files:** (a) worktree SHA-256 matches the committed `.sha256` (`eeb95c87…`, `74b6b141…`, `c0cd3891…`); (b) index/worktree byte identity — `git hash-object` of the worktree equals the index blob hash and staging produced an empty diff; (c) zero CR bytes in the working tree; `git ls-files --eol` now shows `i/lf w/lf attr/text eol=lf`.

### Gate results for the corrections

```
R4 unit gate (test_r4_token_and_metrics.py)     72 passed, 0 failed, 0 skipped
R4 integration gate (test_r4_metric_contract.py) 33 passed, 0 failed, 0 skipped
R3D-adjacent regression (r3d_wiring + repair)    62 passed, 0 failed
Evaluator portability gate                       50 passed, 1 skipped (pre-existing), 0 failed
Full suite                                       1584 passed, 32 skipped, 0 failed
Ruff                                             88 findings = baseline ccdb49c (0 new)
Mypy --strict (4 changed production files)       0 errors (baseline also clean)
Compileall                                       exit 0
git diff --check                                 exit 0
```

### Commit boundaries (audit corrections)

```
c928bd9  fix(validation): pin evaluator assets to canonical LF   (.gitattributes only)
cc32b17  fix(metrics): preserve exhausted workflow token budgets (4 production files + 2 test files)
docs commit  docs(audit): record R4 audit corrections             (documentation only)
```

No push, no tag. R5/R6/Kaggle remain unauthorized pending independent re-audit.

R4_AUDIT_CORRECTIONS_REAUDIT_REQUIRED

---

## 24. R4 Independent Re-Audit Acceptance Addendum

A second independent re-audit of the R4 evidence was performed on 2026-07-31 by GPT-5.6 Thinking. The audit reviewed the correction commits `c928bd9`, `cc32b17`, and `a46213c` on branch `experiment/three-arm-smoke-v2` at HEAD `a46213c` (clean tree) and accepted R4:

```text
R4 status: ACCEPTED AND FROZEN
R5 status: AUTHORIZED / IN PROGRESS
R6 status: BLOCKED
Kaggle status: BLOCKED
Push status: governed by R6 plan unless separately authorized
Tag status: BLOCKED
```

The audit confirmed both defects closed (exact exhaustion semantics; evaluator LF pinning with matching SHA-256), verified the correction commits are narrowly scoped, and recorded no remaining R4 TD-0/TD-1. The user-environment full suite at freeze was 1584 passed, 32 skipped, 0 failed; the independent environment ran the R4 focused files with 105 passed, 0 failed on Linux/Python 3.13.

The repository freeze record is `docs/R4_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md`. README remains intentionally deferred to R6.

**R4_ACCEPTED_R5_AUTHORIZED**

---

## 25. R5 Baseline-Contract Amendment Addendum (R5-BASELINE-CONTRACT-001)

On 2026-07-31, after R4 freeze, R5 Step 2 (the first Monolithic cell) was
blocked at `baseline_validation`: the frozen baseline regression assertions
contradicted the three frozen Smoke V2 scenarios. An independent blocker audit
confirmed the contradiction. No Smoke V2 record had been produced, so a single
narrow pre-results benchmark-data amendment was authorized
(`..\R5_BLOCKER_INDEPENDENT_AUDIT_2026-07-31.md`,
`..\OPENCODE_R5_CONTRACT_CORRECTION_AND_RESUME_DIRECTIVE.md`).

### Amendment contents

- Serializer field assertions became baseline-field preservation checks
  (`TagSerializer` exact); the exact-set Project/Task assertions were
  unsatisfiable because smoke-001 correctly adds `priority` and smoke-003
  correctly adds `owner`.
- The `TaskViewSetTest` common project is created through the authenticated
  `POST /api/projects/` API; the unowned-task forbidden test creates its
  project through another user's API client and still asserts HTTP 403.
- The smoke-002 correct-source fixture keys are exactly `todo/models.py` and
  `todo/views.py`; Monolithic/Selective return the baseline serializer content.
- The smoke-002 evaluator dropped only the unstated `deleted_at`-response-field
  loop inside `_deleted_action_lists_deleted`; `_soft_delete_sets_timestamp`
  remains authoritative; all other checks and check names are unchanged.
  Canonical LF SHA-256 recomputed.
- A three-scenario compatibility gate
  (`test_correct_fixture_passes_baseline_and_evaluator_*`) proves baseline +
  evaluator + one migration + unchanged old migrations + exact frozen
  changed-source paths + unchanged baseline tests + no evaluator assets in the
  workspace.

### Gate results

```
Baseline repository suite (todo)      47 passed, 0 failed
Correct-fixture compatibility gate    3 scenarios passed
Complete evaluator suite              53 passed, 1 skipped (pre-existing), 0 failed
R5 Step-1 + Monolithic smoke-001 cell 11 passed (test_scientific_smoke_v2_production_path.py)
Full suite                            1598 passed, 32 skipped, 0 failed
Ruff                                  0 new findings (correction + R5 WIP files clean)
Mypy                                  0 errors on changed production files
Compileall                            exit 0
git diff --check                      clean
```

### Commit boundaries

```
8fafb50  fix(validation): reconcile Smoke V2 baseline contracts  (7 files, no production, no scenario YAML)
docs(protocol): record pre-results Smoke V2 baseline amendment     (documentation only)
```

No scientific result existed under the old rules. This is a pre-results
correction, not post-hoc tuning: every preserved check still fails its negative
variant, and the exact changed-source-path contract is unchanged. R5 is resumed;
R6, Kaggle, push, and tag remain blocked.

---

## 26. R5 Nine-Record Matrix Completion Addendum (2026-07-31)

R5 produced exactly nine non-dry scripted production records on the real
production path (three scenarios × three strategy arms). This is a local
engineering proof of the complete harness and orchestration; it is not
model-quality evidence. After the independent audit, the local R5 tail was
rebuilt without the accidental Kaggle bundle content (see Section 27).

### Production defect discovered and fixed (rewritten Commit `875e4d1`)

The regeneration executor wrote generated migration files with platform default
line endings, so on Windows the workspace diff compared LF generated bytes
against CRLF baseline bytes and counted the difference as a new change. The fix
preserves the exact generated bytes with a CRLF-robust write
(`target_path.write_text(output_text, encoding="utf-8", newline="")`). No other
production defect was found. The rewritten commit contains exactly two files.

### Nine-record matrix

```
scenario            strategy                   selected generated migration_path                total_tokens
todo-smoke-001      monolithic                 5        5         todo/migrations/0004_task_priority.py   3432
todo-smoke-001      selective                  3        3         todo/migrations/0004_task_priority.py   2383
todo-smoke-001      iterative_repository_agent 3        3         todo/migrations/0004_task_priority.py   6190
todo-smoke-002      monolithic                 5        5         todo/migrations/0004_alter_task_managers_task_deleted_at.py  3918
todo-smoke-002      selective                  2        2         todo/migrations/0004_alter_task_managers_task_deleted_at.py  2092
todo-smoke-002      iterative_repository_agent 2        2         todo/migrations/0004_alter_task_managers_task_deleted_at.py  6218
todo-smoke-003      monolithic                 5        5         todo/migrations/0004_project_owner.py   4524
todo-smoke-003      selective                  4        4         todo/migrations/0004_project_owner.py   3935
todo-smoke-003      iterative_repository_agent 4        4         todo/migrations/0004_project_owner.py   9667
```

All nine records: `status=succeeded`, `baseline=True`, `evaluator=True`,
`functional=True`, `snapshot_unchanged=True`. Agent cells report
`selection_calls=4`, `tool_calls=3`, `inspected=1`, total calls 6–8.
Token magnitudes are scripted-backend engineering metrics, not real model cost.

### Negative and leakage controls

Ten controls green. Corrected wording: `dry_run=True` and
`enable_regeneration=False` are **valid guarded no-op modes** (no generation,
no failure); `pre_apply_migration=True` with no new migration is a **failed
validation control** (status `failed`, stage `migration_generation`,
`migration_generation_passed=False`); the remaining failure controls
(zero_calls, empty_source, no selected artifacts, missing python, vacuous
validation command, mutated snapshot, zeroed persisted metrics) fail at their
exact intended stage. The mutated-snapshot control now proves an
accepted-hash → mutated-hash transition (`snapshot_hash_before !=
snapshot_hash_after`, status `failed`, stage `runner`, message identifies
`views.py`). 8 leakage controls green (backend omits ground truth; no
evaluator/strategy imports; production `src/benchmark` free of `tests.support`;
llm registry and `seven_arm_benchmark.py` exclude scripted; Kaggle choices
exclude scripted; `RepositoryTools` rejects `evaluator_assets`; no evaluator
assets in workspace; AST-based name/module checks).

### Gates

```
Gate 1 backend/source/leakage         15 passed,  0 failed,  0 skipped   20.09s
Gate 2 representative cells            3 passed,  0 failed,  0 skipped   58.01s
Gate 3 nine-record matrix              1 passed,  0 failed,  0 skipped  176.66s
Gate 4 persistence/negative/fail-closed 16 passed, 0 failed, 0 skipped 221.99s
Gate 5 full R5 file                   36 passed,  0 failed,  0 skipped  272.76s
Gate 6 adjacent regression           123 passed,  0 failed,  1 skipped  144.48s
Gate 7 checkpoint + matrix            10 passed,  0 failed,  0 skipped  180.55s
Gate 8 full suite                 1624 passed,  0 failed, 32 skipped   463.37s
Gate 9 ruff 125→122 (0 new)  mypy 10→10 (0 new)  compileall 0  diff-check clean
```

### RF-4 scoped checks

Test-only leakage none; dead local experiment touched none; duplicated record
construction none (single construction point `build_scripted_smoke_v2_cell`);
open TD-0/TD-1 none; selected TD-2 none in a bounded diff. No R5 code change was
required by RF-4, so no matrix rerun was needed.

### Status

```
R5 status: CORRECTION COMPLETE — PENDING INDEPENDENT RE-AUDIT
RF-4 status: PASSED (scoped checks; full cleanup remains scheduled)
R6 status: BLOCKED
Kaggle status: NOT RUN / BLOCKED
Push status: NOT PERFORMED
Tag status: BLOCKED
```

R5_SCOPE_CLEANUP_REAUDIT_REQUIRED

---

## 27. R5 Scope-Cleanup Addendum — Independent Audit Correction (2026-07-31)

An independent audit (`..\R5_INDEPENDENT_AUDIT_SCOPE_AND_EVIDENCE_2026-07-31.md`)
found canonical production not broadly damaged but the original R5 git tail
mis-scoped: commit `6650b00` claimed one execution fix while also committing 31
premature `kaggle_upload/` derivative files and introducing a committed
notebook-manifest mismatch. Because the branch had no upstream, the local R5
tail was rebuilt cleanly per `..\OPENCODE_R5_SCOPE_CLEANUP_DIRECTIVE.md`.

### Rebuilt history

```
8fafb50  preserved  fix(validation): reconcile Smoke V2 baseline contracts
a24a9cd  preserved  docs(protocol): record pre-results Smoke V2 baseline amendment
875e4d1  rewritten  fix(execution): preserve generated file bytes on Windows  (2 files)
ee148fa  rewritten  test(smoke): prove nine scripted production records      (3 files)
docs(audit)        docs(audit): record R5 completion pending re-audit        (docs only, this commit)
```

The accidental `6650b00` bundle content is recorded for traceability; local
history was rebuilt before any push. The pre-rebuild state is preserved on
`backup/r5-pre-audit-c3ecad2` (not deleted until independent re-audit).

### Evidence tightened

- Exact generation contract for all nine cells:
  `backend.generation_paths_requested` equals the sorted expected paths
  (monolithic = 5, selective/agent = 3/2/4 per scenario), with exact
  `selected_artifact_count`, `regeneration_model_calls`,
  `regenerated_artifact_count`, and `preserved_artifact_count`.
- Snapshot mutation transition: `snapshot_hash_before != snapshot_hash_after`,
  `record.status == failed`, failure message identifies the invalid active
  snapshot path.
- Truthful timestamps: `started_at`/`ended_at` captured immediately
  before/after the real `pipeline.run_scenario_by_id`; one exact test proves
  `started_at <= ended_at` and timezone-aware ISO parsing for all nine records.
- Negative-control wording corrected (see Section 26).
- Actual R5 file line counts: 268 / 699 / 717 (replacing stale 216 / 597 / 577).

### Bundle-scope and manifest status

```
kaggle_upload diff from a24a9cd = empty
kaggle_upload diff from f5ae826 = empty
Git-tree code manifest mismatches     = 0
Git-tree data manifest mismatches     = 10 (pre-existing, R6 blocker)
Git-tree notebook manifest mismatch   = 0 on the rebuilt branch (the old
                                       6650b00 introduced 1, now removed)
scripts/build_upload_bundle.py        = NOT modified in R5
```

The Git-tree bundle-manifest root cause (code text normalized before manifest
generation; data files and notebooks not normalized; manifests hash worktree
bytes) is recorded as R6 debt `TD-R6-BUNDLE-MANIFEST-001` and must be fixed in
the bounded RF-4/R6 bundle-builder correction.

### Final gates (this cleanup pass)

```
pytest tests/unit/execution/test_regeneration.py                  15 passed
pytest tests/integration/test_todo_smoke_evaluator_assets.py      53 passed, 1 skipped
pytest tests/integration/test_scientific_smoke_v2_production_path.py 37 passed
pytest r4_metric_contract + smoke_v1_fixes + su0010a + su0011     156 passed
pytest -q (full suite)                                           1625 passed, 32 skipped
ruff check .                                                      123 == baseline a24a9cd (0 new)
mypy --strict src seven_arm_benchmark.py                          10 == 10 (0 new)
compileall                                                        clean
git diff --check                                                  clean
working tree                                                      clean
```

Ruff and mypy compared against `backup/r5-pre-audit-c3ecad2`: zero new
findings.

---

## 28. R5 Acceptance and R6 Authorization (2026-08-01)

The independent re-audit (`..\R5_FINAL_INDEPENDENT_REAUDIT_ACCEPTANCE_2026-08-01.md`)
**accepted and froze R5** at HEAD `7761c48` on 2026-08-01. R5 produced nine
non-dry scripted production records (3 frozen scenarios × 3 arms × 1
repetition): 9 succeeded, 0 failed. The full suite at R5 acceptance was 1,625
passed, 32 skipped, 0 failed. The old contaminated R5 tail remains preserved
on `backup/r5-pre-audit-c3ecad2`.

R6 deployment closure was **AUTHORIZED** under the corrected directive in
`..\R6_OpenCode_Package_CORRECTED\` (supersedes every earlier R6 directive) and
was executed in one continuous bounded pass covering:

```text
R6-F01  R5 acceptance record
R6-F02  deterministic cross-platform builder
R6-F03  controlled Todo regression tests in data bundle
R6-F04  exact six evaluator assets + fingerprints in code bundle
R6-F05  valid exact V2 smoke config
R6-F06  current CLI help
R6-F07  notebook pinned to a real existing runtime-source commit
R6-F08  generated bundle built only through the builder
R6-F09  bundle deployment preflight integration
R6-F10  worktree/index/committed-tree manifest equality
R6-F11  README, reports, handoff, and future-AI state
R6-F12  stop before push for independent audit
```

R6 must not modify production Runner, strategies, metrics, regeneration,
evaluator behavior, frozen scenarios, evaluator assets, or controlled Todo
source/tests. No push, tag, merge, or Kaggle launch during R6.

### R6 Closure (2026-08-01)

R6 deployment closure is **COMPLETE PENDING INDEPENDENT AUDIT**, recorded in
`selective_updates/records/R6-BUNDLE-PARITY-AND-PRE-KAGGLE-HANDOFF.md`.
Commits: A `5784a4f` (R5 acceptance), B `cb25e9f` (runtime source), C `54a0462`
(pinned/generated bundle), D (documentation). Manifest audits at
worktree/index/committed-tree: 0 / 0 / 0. Todo baseline tests deployed = 47
methods; evaluator assets deployed = 3 + 3 fingerprints. Bundle totals = 144
files / 805,634 bytes. Deployment preflight: all three smoke scenarios passed
(one new migration, old hashes unchanged, `Ran 47 tests`, evaluator pass,
no `tests/evaluator_assets` in generated workspace). Full suite at R6 closure:
1,647 passed, 32 skipped, 0 failed. Ruff set identical to starting HEAD
`7761c48` (94 findings, zero new); mypy strict 0 errors; compileall clean;
final builder run left the tree clean.

### Status

```
R4 status: ACCEPTED AND FROZEN at f5ae826
R5 status: ACCEPTED AND FROZEN at 7761c48 (independent re-audit 2026-08-01)
R6 status: COMPLETE PENDING INDEPENDENT AUDIT
Kaggle status: NOT LAUNCHED
Push status: NOT PERFORMED (BLOCKED PENDING AUDIT)
Tag status: BLOCKED
Pilot status: NOT AUTHORIZED
Real Smoke progress: 0/9 (local scripted 9/9)
Next action: independent R6 audit (GPT-5.6 Thinking) before push; then push, Kaggle preflight, and nine real Qwen records
```

R6_DEPLOYMENT_CLOSURE_AUDIT_REQUIRED
