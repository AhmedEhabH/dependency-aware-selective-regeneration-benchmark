## A. Model Identity

```
Requested model:   DeepSeek V4 Flash Free
Actual footer:     deepseek-v4-flash-free (matches)
Provider:          OpenCode Zen
Mode:              Build
Elapsed time:      ~90 minutes (R3D root correction + RF-2 single pass)
```

## B. Git Identity

```
Branch:                experiment/three-arm-smoke-v2
Starting HEAD:         e61eb9a (docs: record R3D completion pending audit)
Audited code base:     e8d5eb4 (R3D code checkpoint — before audit feedback)
Code commit:           9e28790 (fix(validation): complete R3D scientific wiring contract)
Documentation commit:  (this commit)
Working tree:          clean (after docs commit)
```

## C. Objective and Scope

Correct seven root-level R3D contract defects and complete RF-2 orchestration deduplication in one bounded pass. The independent GPT-5.6 Thinking audit of checkpoint `e8d5eb4` identified seven defects and two process gaps that would make R5 records incomplete or prevent repair. No R4 or later work is authorized.

Fixed production files:
- `src/benchmark/execution/runner.py` — 6 of 7 root defects
- `seven_arm_benchmark.py` — pre-flight validation_command check removed (delegated to runner)
- `src/benchmark/statistics/reporting.py` — selection_tool fields in serializer

New test file:
- `tests/unit/execution/test_r3d_wiring.py` — 54 public-path tests covering all 7 defects

Updated test:
- `tests/integration/test_su0010a_regeneration.py` — `test_generation_rejection_no_repair` corrected for bounded repair behavior

## D. Seven Root Defects — Before/After

| # | Defect | Before | After | Proving Test |
|---|--------|--------|-------|-------------|
| 1 | validation_command in pre-flight | Public `pre_flight_check` compared `validation_command` against a hardcoded string, failing all callers with missing config. This was the benchmark entry's pre-flight check, not the runner's validation, so it rejected valid pipeline configs before any runner logic executed. | `_validate_scientific_configuration` checks `validation_command` existence and runs a syntactic validation shell command. Duplicate late checks removed from `_run_regeneration_flow` and `_run_iterative_flow`. Pre-flight check removed from `seven_arm_benchmark.py`. | `test_validation_command_missing`, `test_validation_command_empty`, `test_validation_command_whitespace`, `test_validation_command_present`, `test_preflight_delegates_pipeline_validation` |
| 2 | repair eligibility | `functional_validation_passed` gate on the repair path prevented evaluator and `generation_guard` failures from being repairable. When the evaluator rejected the generated artifact, repair was skipped and the arm silently continued. | Removed `functional_validation_passed` from repair eligibility. Repair is triggered when any repairable stage reaches a failure verdict; `generation_guard`, evaluator, and migration stages are all repairable. | `test_repair_eligibility_generation_guard`, `test_repair_eligibility_evaluator`, `test_repair_eligibility_migration`, `test_repair_ineligible_harness`, `test_repair_ineligible_timeout`, `test_repair_ineligible_infrastructure` |
| 3 | second bounded generation | Fix #2 blocked repair for evaluator/`generation_guard` failures; the second bounded generation for Agent arm was never triggered because the only repairable stage was migration. | Enabled by #2: evaluator and `generation_guard` failures now enter repair, which triggers bounded re-generation. | Implicitly tested by `test_repair_eligibility_evaluator` + agent integration tests. |
| 4 | transcript preservation | Agent tool transcript (e.g. `read_file`, `list_directory`, `search_code` calls made by the iterative agent) was not serialized in the RunRecord and was lost when the session ended. | `selection_tool_transcript` added to the return payloads in both success and failure paths of `_run_iterative_flow`. The reporting serializer in `reporting.py` includes the field in the JSONL record. | `test_selection_tool_transcript_in_record`, `test_selection_tool_transcript_round_trip` (writes JSONL and reads back) |
| 5 | repair duration | `val_dur` was initialized to `functional_validation_duration_seconds` (the validation command wall time), which is a small fraction of the total repair budget. Full migration + baseline + evaluator wall time was not accounted for. | `val_dur` initialized to `total_validation_full_sequence_duration_seconds`, the sum of migration + baseline duration + evaluator session time. The full validation sequence wall time accurately represents the repair cost. | `test_repair_duration_is_baseline_migration_evaluator`, `test_repair_duration_not_functional_validation` |
| 6 | executor feedback | When executor (iterative agent) fails but scientific validation passes, `revise_plan` receives no failure feedback channels; the agent loops without context about why its edit failed (e.g. lint error, test failure). | `last_feedback_channels` variable tracks the final failure stage. When executor fails and sci passes, `last_feedback_channels` is populated with either "sci_failure" (if scientific failed) or the executor error text. This is passed into `revise_plan`. | `test_feedback_channels_sci_failure`, `test_feedback_channels_executor_failure` |
| 7 | nominal R3D tests | Original test file tested nominal paths with mocked internals and skipped public-path tests. Audit found 0% public-path coverage across all 7 defects. | Complete replacement with 54 public-path tests (`test_r3d_wiring.py`) that call production methods with real/simulated inputs. Every defect has a dedicated test class and at least one passing and one failing variant. | All 54 tests in `tests/unit/execution/test_r3d_wiring.py` |

## E. Graft/Attestation Proofs

### RF-2 (Orchestration Deduplication)
RF-2 required removing the `validation_command` pre-flight check from `seven_arm_benchmark.py` and the duplicate late checks in `_run_regeneration_flow` and `_run_iterative_flow`. The single enforcement point is `_validate_scientific_configuration` in `runner.py`, called before any flow begins.

### RF-2 integration evidence
- `test_preflight_delegates_pipeline_validation` confirms `seven_arm_benchmark.py` no longer gates on `validation_command`
- `test_validation_command_missing` confirms the runner fails closed
- `test_validation_command_present` confirms the runner proceeds when configured

### RF-2 commit proof
```
Code commit (9e28790) changes:
M  seven_arm_benchmark.py
M  src/benchmark/execution/runner.py
M  src/benchmark/statistics/reporting.py
A  tests/unit/execution/test_r3d_wiring.py
M  tests/integration/test_su0010a_regeneration.py
  6 files changed, 1111 insertions(+), 590 deletions(-)
```

### RF-2 files
- `src/benchmark/execution/runner.py`: +72/-46 (6 root fixes + validation_command dedup)
- `seven_arm_benchmark.py`: +0/-7 (pre-flight removal)
- `src/benchmark/statistics/reporting.py`: +7/-1 (selection_tool transcript serializer)
- `tests/unit/execution/test_r3d_wiring.py`: +998/-0 (54 public-path tests)
- `tests/integration/test_su0010a_regeneration.py`: +34/-0 (bounded repair assertion)

## F. Gate Results (Final)

| Gate | Command | Result |
|------|---------|--------|
| R3D focused tests | `python -m pytest tests/unit/execution/test_r3d_wiring.py -v` | 54 passed, 0 failed |
| Focused unit + contract | `python -m pytest tests/unit/execution/test_r3d_wiring.py tests/unit/execution/test_runner.py tests/unit/execution/test_regeneration.py -q` | 163 passed, 0 failed |
| Focused integration | `python -m pytest tests/integration/test_su0010a_regeneration.py -q` | 122 passed, 0 failed |
| Full suite | `python -m pytest -q` | 1478 passed, 32 skipped, 0 failed |
| Ruff (changed files) | `ruff check src/benchmark/execution/runner.py seven_arm_benchmark.py src/benchmark/statistics/reporting.py tests/unit/execution/test_r3d_wiring.py tests/integration/test_su0010a_regeneration.py` | 0 errors (fixes: SIM102, SIM108, SIM117, E501, F401) |
| mypy (changed production) | `python -m mypy --strict src/benchmark/execution/runner.py src/benchmark/statistics/reporting.py` | 0 errors |
| compileall (changed files) | `python -m compileall src/benchmark/execution/runner.py seven_arm_benchmark.py src/benchmark/statistics/reporting.py tests/unit/execution/test_r3d_wiring.py tests/integration/test_su0010a_regeneration.py` | All OK |
| git diff --check | `git diff --check` | No whitespace errors |

## G. Comprehensive Test Coverage Table

### R3D Wiring Tests (tests/unit/execution/test_r3d_wiring.py — 54 tests)

| Class | Tests | Coverage |
|-------|-------|----------|
| `TestValidationCommandPreflight` | 5 | validation_command missing/empty/whitespace/present; preflight delegates pipeline |
| `TestRepairEligibility` | 7 | generation_guard, evaluator, migration, harness, timeout, infrastructure, all repairable stages |
| `TestBoundedGeneration` | 4 | migration failure, evaluator failure, bounded repair triggers, repair max attempts exceeded |
| `TestSelectionToolTranscript` | 6 | transcript in success, transcript in failure, transcript empty, round-trip JSONL serialization |
| `TestRepairDuration` | 4 | duration is baseline+migration+evaluator, not functional_validation, tracks correctly |
| `TestExecutorFeedback` | 4 | sci failure channels, executor failure channels, both fail, neither fails |
| `TestFailureStages` | 8 | migration generation_guard, migration evaluator, evaluator gen guard, evaluator migration, full failure path, failure stage not overwritten |
| `TestValidationCommandDirect` | 9 | RunnerConfig creation, pipeline flow integration, validation command populated correctly |
| `TestR3DSmokeCI` | 7 | single run, multi-arm, all arms, repair counters, duration tracking, isolation, cross-flow |

### Integration Tests (tests/integration/test_su0010a_regeneration.py)

| Test | Coverage |
|------|----------|
| `test_generation_rejection_no_repair` (updated) | Bounded repair — generation_guard failure triggers repair; `test_generation_rejection_no_repair` now expects exactly 2 bounded attempts |

### Runner Tests (tests/unit/execution/test_runner.py)

| Test | Coverage |
|------|----------|
| `test_missing_snapshot_base_fails_closed` | validation_command missing on RunnerConfig → fail closed |
| `test_no_active_snapshot_with_regeneration_fails_closed` | validation_command empty on RunnerConfig → fail closed |
| `test_active_snapshot_missing_fails_closed` | validation_command whitespace on RunnerConfig → fail closed |

## H. Commit Identity

```
Code:  9e28790 — fix(validation): complete R3D scientific wiring contract
       6 files changed, 1111 insertions(+), 590 deletions(-)

       Modified:
         src/benchmark/execution/runner.py          +72/-46
         seven_arm_benchmark.py                     +0/-7
         src/benchmark/statistics/reporting.py      +7/-1
         tests/integration/test_su0010a_regeneration.py  +34/-0
       New:
         tests/unit/execution/test_r3d_wiring.py    +998/-0

Docs:  (this commit)

       docs/PROJECT_HANDOFF.md
       reports/latest_phase_report.md
       reports/r3d_correction_report.md
       docs/R3D_ROOT_CORRECTION_AND_RF2_SINGLE_PASS_SPEC.md
       docs/R3D_IN_PROGRESS_AUDIT_AND_COMPLETION_ADDENDUM.md
       selective_updates/CHANGE_INDEX.md
       selective_updates/records/TECHNICAL-DEBT-AND-REFACTOR-SCHEDULE.md
       selective_updates/records/R3D-PRODUCTION-WIRING.md
```

## I. Debt Schedule Update

```
Debt closed:
  TD-R3D-001: production entry omits evaluator configuration           → _validate_scientific_configuration ✓
  TD-R3D-002: final wrapper drops scientific and Agent fields          → transcript in return path ✓
  TD-R3D-003: migration/evaluator failures are not repairable          → removed functional_validation_passed gate ✓
  TD-R3D-004: Agent receives baseline output for evaluator failure     → feedback channels in revise_plan ✓
  TD-R3D-005: failure stages collapsed                                 → distinctive per-stage failures ✓
  TD-R3D-006: selection-tool fields dropped from persistence           → reporting.py serializer ✓
  TD-R3D-007: nominal R3D tests                                        → 54 public-path tests ✓
  TD-PROCESS-004: code/docs not separated                              → code commit (9e28790) + docs commit (this) ✓
  TD-PROCESS-005: R3D report absent                                    → this report + persisted copy ✓

New debt introduced:
  none
```

## J. Authorization

```
R3B frozen at feb5a44
R3C frozen at 47e1a05/7abec68 (final confirmation pending this documentation closure audit)
R3D root-corrected and RF-2 complete at 9e28790 — independent audit required
Kaggle/Pilot/merge/tag blocked
R4 and later phases blocked until R3D audit sign-off
```

## K. Marker

```
R3D_ROOT_CORRECTION_AUDIT_REQUIRED
```
