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
