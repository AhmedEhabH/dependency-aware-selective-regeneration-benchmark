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
