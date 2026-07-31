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

Position: R4 frozen at `a46213c`; R5 authorized and in progress. Next authorized action: complete R5 (nine local records), then RF-4 cleanup and rerun, then R6 (bundle and push).

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
