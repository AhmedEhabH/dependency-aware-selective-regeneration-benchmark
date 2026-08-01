# Technical Debt and Refactor Schedule

## Checkpoints

| Checkpoint | Trigger | Debt classes | Maximum scope | Exit evidence |
|---|---|---|---|---|
| R3C closure | before R3C freeze | TD-0/TD-1 plus directly related TD-2 | R3C tests/docs | focused Linux + Windows full suite |
| RF-2 | after R3D self-gates | TD-0/TD-1 in orchestration, selected TD-2 duplication | Runner/Pipeline/persistence only | integration sequence and round trip |
| RF-3 | after R4 self-gates | token/metric TD-0/1/2 | metrics and config only | arithmetic property tests |
| RF-4 | after R5 nine records | all TD-0/1; selected TD-2 | local production proof path | nine records rerun |
| R6 closure | after bundle | deployment TD-0/1 | docs/bundle/parity | source/build hash parity |
| Post-Smoke | after real records | evidence defects only | records/reports | preserved original results |

## Debt Register

### TD-R3C-001 — misleading TOCTOU tests
- **Severity:** TD-2
- **Closure:** rewrite tests to mutate after validation ✓
- **Checkpoint:** R3C closure

### TD-R3C-002 — missing lifecycle regression tests
- **Severity:** TD-1 (hidden evaluator output is a production contract)
- **Closure:** six fake-Django tests ✓
- **Checkpoint:** R3C closure

### TD-R3C-003 — incomplete permission-layer proof
- **Severity:** TD-0 scientific contract
- **Closure:** invoke configured permissions ✓
- **Checkpoint:** R3C closure

### TD-R3C-004 — source-isolation Boolean error
- **Severity:** TD-1
- **Closure:** single absence helper ✓
- **Checkpoint:** R3C closure

### TD-R3C-005 — tests mutate hash metadata
- **Severity:** TD-2
- **Closure:** metadata required and read-only ✓
- **Checkpoint:** R3C closure

### TD-PROCESS-001 — code/docs commit mixing
- **Severity:** TD-2
- **Closure:** explicit staging and report proof ✓
- **Checkpoint:** R3C closure

### TD-PROCESS-002 — empty documentation commit
- **Severity:** TD-2
- **Closure:** cached diff required before commit ✓
- **Checkpoint:** R3C closure

### TD-PROCESS-003 — actual model mismatch
- **Severity:** TD-1 process-control
- **Closure:** model preflight and footer truth ✓
- **Checkpoint:** R3C closure

### TD-R3D-001 — production entry omits evaluator configuration
- **Severity:** TD-0 scientific contract
- **Closure:** `_validate_scientific_configuration` checks validation_command existence and runs syntactic shell command ✓
- **Checkpoint:** R3D root correction

### TD-R3D-002 — final wrapper drops scientific and Agent fields
- **Severity:** TD-0 scientific contract
- **Closure:** selection_tool_transcript added to both success and failure return paths ✓
- **Checkpoint:** R3D root correction

### TD-R3D-003 — migration/evaluator failures are not repairable
- **Severity:** TD-1
- **Closure:** removed `functional_validation_passed` gate from repair eligibility; evaluator, generation_guard, migration are repairable ✓
- **Checkpoint:** R3D root correction

### TD-R3D-004 — Agent receives baseline output for evaluator failure
- **Severity:** TD-1
- **Closure:** `last_feedback_channels` passed into `revise_plan` when executor fails but sci passes ✓
- **Checkpoint:** R3D root correction

### TD-R3D-005 — failure stages collapsed
- **Severity:** TD-1
- **Closure:** each failure stage returns distinctive verdicts (generation_guard vs evaluator vs migration vs harness vs timeout vs infrastructure) ✓
- **Checkpoint:** R3D root correction

### TD-R3D-006 — selection-tool fields dropped from persistence/reporting
- **Severity:** TD-1
- **Closure:** `selection_tool_transcript` serialized in reporting.py `_RunRecordData` ✓
- **Checkpoint:** R3D root correction

### TD-R3D-007 — nominal R3D tests
- **Severity:** TD-0 scientific contract
- **Closure:** complete replacement with 54 public-path tests in `test_r3d_wiring.py` ✓
- **Checkpoint:** R3D root correction

### TD-PROCESS-004 — R3D code/docs not separated
- **Severity:** TD-2
- **Closure:** code commit (9e28790) separated from docs commit ✓
- **Checkpoint:** R3D root correction

### TD-PROCESS-005 — R3D report absent
- **Severity:** TD-2
- **Closure:** full R3D correction report persisted to reports/latest_phase_report.md and reports/r3d_correction_report.md ✓
- **Checkpoint:** R3D root correction

### TD-R3D-008 — evaluator stderr omitted from Agent/repair feedback
- **Severity:** TD-0 scientific contract
- **Closure:** `_scientific_feedback_channels()` constructs stderr from evaluator.stderr, evaluator.error, and checks ✓
- **Checkpoint:** R3D final evidence closure

### TD-R3D-009 — public-path regression tests incomplete
- **Severity:** TD-1
- **Closure:** replaced 5 nominal tests with 7 public-path tests in test_r3d_wiring.py ✓
- **Checkpoint:** R3D final evidence closure

### TD-PROCESS-006 — R3D report contained inaccurate evidence
- **Severity:** TD-2
- **Closure:** replaced with truthful Git-derived report at reports/latest_phase_report.md ✓
- **Checkpoint:** R3D final evidence closure

### TD-PROCESS-007 — visible OpenCode response omitted required report
- **Severity:** TD-2
- **Closure:** report printed in the visible OpenCode response ✓
- **Checkpoint:** R3D final evidence closure

### TD-R4-001 — truthful metrics implementation pending
- **Severity:** TD-0 scientific contract
- **Closure:** R4 single-pass completed — `budgets.resolve_completion_allowance` single resolver; frozen conflict rule at every constructor; stage-split `_WorkflowMetricAccumulator`; executor/Agent explicit limits; `model_metadata` forwards resolved total + max_attempts; R4 unit 66, R4 integration 31, full suite 1576/32/0 ✓
- **Checkpoint:** RF-3

### TD-R4-002 — per-call and workflow-total limits conflated
- **Severity:** TD-0
- **Closure:** separate `max_completion_tokens_per_call` (default 4096) and `max_total_workflow_tokens` (0 = unlimited) across executor, Agent, Runner, Pipeline, CLI record_dict ✓
- **Checkpoint:** RF-3

### TD-R4-003 — frozen conflict rule not enforced at construction
- **Severity:** TD-0
- **Closure:** `PipelineConfig.__post_init__`, `RunnerConfig`, `ExecutionConfig` raise at construction on differing positive totals; legacy-only and equal-positive resolve ✓
- **Checkpoint:** RF-3

### TD-R4-004 — repair regeneration counted as initial regeneration
- **Severity:** TD-0
- **Closure:** `is_repair = iteration > 0`; `repair_attempts += 1` once per repair executor call (runner.py:117, 1348-1349) ✓
- **Checkpoint:** RF-3

### TD-R4-005 — scientific stage durations not cumulative across attempts
- **Severity:** TD-1
- **Closure:** `_WorkflowMetricAccumulator.add_scientific` sums migration/baseline/evaluator across repair attempts; exact asserts (`0.5×2 = 1.5`, `0.7×3 = 2.1`) ✓
- **Checkpoint:** RF-3

### TD-R4-006 — nominal `assert True` executor/Agent/boundary tests
- **Severity:** TD-0
- **Closure:** replaced with 66 unit + 31 integration executable production-path tests; zero `assert True` ✓
- **Checkpoint:** RF-3

### TD-PROCESS-008 — R4 ARG001 introduced mid-session
- **Severity:** TD-2
- **Closure:** `_to_run_record_data` forwards `max_attempts` into `model_metadata`; new-error count restored to zero ✓
- **Checkpoint:** RF-3

### TD-R4-007 — exact workflow-budget exhaustion reopened an exhausted budget as unlimited
- **Severity:** TD-0 scientific contract
- **Closure:** `0` was overloaded as both "no total limit" and "exhausted". `budgets.runtime_remaining_total_tokens` now returns `None` when `has_total_token_limit` is False, `0` for exhausted, positive for remaining; `resolve_completion_allowance` takes `int | None` and returns the per-call limit for `None`, `0` for exhausted `0`, `max(0, min(per_call, remaining - prompt))` for positive. Executor/Agent defaults changed to `None` with `has_limit` accounting guards; all five Runner call sites forward `runtime_remaining_total_tokens`. Five-group regression (executor/analyze-impact/revise-plan/unlimited/resolver) + integration production-path tests ✓
- **Checkpoint:** R4 audit correction

### TD-R4-008 — evaluator integrity platform-dependent
- **Severity:** TD-0 scientific contract
- **Closure:** committed `.sha256` fingerprints are canonical LF but Windows checkout produced CRLF, so worktree raw SHA-256 mismatched. `.gitattributes` pins `tests/evaluator_assets/todo_smoke_*_checks.py` to `text eol=lf`; the three working-tree files rewritten to canonical LF with zero character changes. Proven: worktree SHA-256 matches committed `.sha256`, index/worktree blobs byte-identical, zero CR bytes ✓
- **Checkpoint:** R4 audit correction

### TD-R5-001 — generated file line endings differ from baseline bytes on Windows
- **Severity:** TD-0 (workspace diff integrity on Windows)
- **Closure:** regeneration executor now preserves exact generated bytes with a CRLF-robust write; workspace diff no longer sees LF-vs-CRLF phantom changes. Rewritten commit `875e4d1` (originally `6650b00`) ✓
- **Checkpoint:** R5 nine-record matrix

### TD-R6-BUNDLE-MANIFEST-001 — committed bundle manifests can mismatch committed blobs
- **Severity:** TD-0 (deployment integrity / traceability)
- **Closure:** CLOSED IN R6 (2026-08-01) — deterministic builder
  (`scripts/build_upload_bundle.py`) normalizes code/data/notebook bytes before
  SHA-256 manifest generation and verification; manifests use POSIX relative
  paths and LF line endings; builder performs no Git calls; bundle rebuilt and
  audited at worktree/index/committed-tree = 0 / 0 / 0 mismatches (Commit C
  `54a0462`).
- **Checkpoint:** R6 closure (blocked until R5 re-audit acceptance) — REACHED
- **Evidence:** Git-tree code-manifest mismatches = 0; Git-tree data-manifest
  mismatches = 0; Git-tree notebook-manifest mismatches = 0; staged
  (git-index) manifest mismatches = 0; committed-tree (HEAD) manifest
  mismatches = 0; controlled Todo tests deployed = exact five files / 47
  methods; evaluator assets deployed = 3 + 3 fingerprints; tests/support = 0;
  scripted/harness = 0; final builder run byte-identical, tree clean.

### TD-R6-ENTRYPOINT-001 — bundled CLI entrypoint regression missing
- **Severity:** TD-0 (deployed-entrypoint integrity)
- **Opened:** R6 Independent Audit (2026-08-01), section 7 — deployment
  preflight tests proved baseline/evaluator/scenario/migration behavior but
  never executed the generated CLI entrypoint itself.
- **Closure:** CLOSED IN R6 FINAL CORRECTION (2026-08-01) — regression
  `test_bundled_cli_dry_run_executes_exact_nine_cell_plan` appended to
  `tests/integration/test_kaggle_bundle_smoke_v2_preflight.py` (test commit
  `40c7a47`); runs the real generated CLI
  (`kaggle_upload/code/seven_arm_benchmark.py`) with the bundled data via
  subprocess and asserts exact persisted matrix and identity: rc=0, 9 succeeded
  records, exact scenario × strategy Cartesian product, checkpoint
  `total_planned=9` / `total_completed=9` / `completion_status=completed`,
  exact source/build identity, `source_identity.json` truth, per-strategy
  summary counts, unchanged working tree before/after.
- **Checkpoint:** R6 closure — REACHED — ACCEPTED AND FROZEN (final independent re-audit 2026-08-01 at `949e9c2`)
- **Evidence:** preflight file 9/9 passed; grouped gate
  (build_upload_bundle + config_models + cli + preflight) 79 passed; manual
  probe matched observed audit output (9 cells, 3×3 matrix, exit 0); final
  accepted full suite = 1,648 passed / 32 skipped / 0 failed.


## RF-4 status (after R5 scope correction, 2026-07-31)

Scoped RF-4 checks ran after the R5 nine-record matrix:

- **Test-only production leakage:** none — 8 leakage controls green (backend omits ground truth; no evaluator/strategy imports; production `src/benchmark` free of `tests.support`; llm registry and `seven_arm_benchmark.py` exclude scripted; Kaggle choices exclude scripted; `RepositoryTools` rejects `evaluator_assets`; no evaluator assets in workspace; AST-based name/module checks).
- **Dead local experiment setup touched by R5:** none.
- **Duplicated record construction introduced by R5:** none — single construction point `build_scripted_smoke_v2_cell` reused by the matrix runner.
- **Open TD-0/TD-1:** none opened by R5 (TD-R6-BUNDLE-MANIFEST-001 is recorded as R6 debt, not an R5 failure).
- **Selected TD-2 removable in a small bounded diff:** none found.

RF-4 produced no R5 code change, so the nine-record matrix was not rerun.
Full RF-4 technical-debt cleanup (all TD-0/1 plus selected TD-2) remains
scheduled in the R6 window per the checkpoint table above.

## Post-R6 Kaggle runtime fix (2026-08-01)

Two real Kaggle attempts failed pre-model (`exp-20260801-024041`,
`exp-20260801-024624`). No new technical debt was opened by the runtime fix;
the pre-existing debt register is unchanged. The runtime blockers closed on
branch `fix/kaggle-smoke-v2-runtime-blockers` (commits `de3163f`, `fb60972`)
are recorded in
`selective_updates/records/KAGGLE-SMOKE-V2-RUNTIME-FIX.md` and are not debt
items — they are the primary execution-path fixes needed for the first real
records. The only new TD-2-style note: pre-existing Mypy strict base of 5
errors in `seven_arm_benchmark.py` remains open (unchanged from R6).

## Post-R6 R7A pre-rerun hardening (2026-08-01)

The R7A hardening (`d50e89e`, `4c73db6`) closed the four findings reproduced
by the independent runtime-fix audit and opened no new technical debt. It is
recorded in `selective_updates/records/KAGGLE-SMOKE-V2-RUNTIME-HARDENING.md`.
The pre-existing Mypy strict base in `seven_arm_benchmark.py` is outside the
R7A authorized scope and remains unchanged.
