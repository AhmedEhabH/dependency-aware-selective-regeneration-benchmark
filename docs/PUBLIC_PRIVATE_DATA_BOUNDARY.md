# Public and Private Data Boundary — v1.0

**Phase:** 3.5 — Static Architecture Audit and Project Map  
**Date:** 2026-07-22  
**Status:** FROZEN

---

## 1. Principle

Data is classified as **public** (visible to strategies) or **private** (inaccessible to strategies). Private data is loaded only during final scoring and analysis, never during strategy execution. This boundary prevents data leakage per AC-03 and AC-01.

## 2. Public Data (Visible to Strategies)

| Category | Path | Contents |
|----------|------|----------|
| Repository manifests | `benchmark_data/manifests/` | Repository URLs, pinned versions, architectural style |
| Repository profiles | `benchmark_data/repository_profiles/` | Architecture descriptions, module boundaries, artifact catalogs |
| Scenario descriptions | `benchmark_data/scenarios/` | Requirement before/after, acceptance criteria, architecture constraints |
| Public tests | `benchmark_data/public_tests/` (Phase 4+) | Tests visible to strategies during execution |
| Configuration profiles | `configs/` (Phase 4+) | Smoke, pilot, research execution profiles |

### What strategies see

- The frozen repository snapshot (commit SHA)
- The requirement change (before/after text and acceptance criteria)
- Architecture constraints from the scenario definition
- Public test results (pass/fail) during repair cycles
- The candidate artifact universe (paths and types)

## 3. Private Data (Inaccessible to Strategies)

| Category | Path | Contents |
|----------|------|----------|
| Hidden tests | `private_evaluation/hidden_tests/` | Tests not visible to strategies; used only for final scoring |
| Ground truth | `private_evaluation/ground_truth/` | Expected action labels (regenerate/preserve/validate_only/human_review) |
| Scoring oracle | `private_evaluation/scoring/` | Evaluation logic that compares strategy outputs to ground truth |
| Adjudication records | `private_evaluation/adjudication/` | Annotator disagreements and resolution |
| Held-out scenarios | `private_evaluation/held_out/` | Scenarios reserved for final validation |

## 4. Import Isolation

No module under `src/benchmark/strategies/` may import from `private_evaluation/`.

No module under `src/benchmark/execution/` may import ground-truth annotations.

The `src/benchmark/evaluation/` package loads private data, but:

- `evaluation/` is not imported by `strategies/` or `execution/`
- `evaluation/` reads ground truth only during the scoring stage, not during strategy execution
- The execution pipeline produces immutable run records; evaluation consumes these records post-hoc

## 5. File System Isolation

| Rule | Enforcement |
|------|-------------|
| Private files must not be placed inside `src/benchmark/` | Directory layout policy |
| Private files must not be included in strategy-facing Kaggle Code Dataset | Upload script audit |
| Private paths must not appear in strategy prompts | Prompt template audit |
| Hidden test files must have distinct naming from public test files | Naming convention audit |

## 6. Data Flow

```
Phase 4 (execution):
  strategy → sees public data only
  → produces run records (immutable)
  → pipeline stores run records in runs/

Phase 6 (scoring):
  evaluation → loads run records
  → loads private ground truth
  → computes scores
  → produces score records

Phase 7 (analysis):
  statistics → loads score records
  → produces analysis results
  → never loads raw strategy outputs or ground truth directly
```

## 7. Audit Checklist

Before main execution, verify:

- [ ] `grep -r "private_evaluation" src/benchmark/strategies/` returns nothing
- [ ] `grep -r "ground_truth" src/benchmark/execution/` returns nothing
- [ ] No hidden test file path is referenced in any strategy prompt template
- [ ] The Kaggle upload script excludes `private_evaluation/`
- [ ] The scoring script loads ground truth after execution, not during
