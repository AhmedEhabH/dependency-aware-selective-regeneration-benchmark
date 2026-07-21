# Master Implementation Plan

## Dependency-Aware Selective Regeneration for LLM-Assisted Software Evolution

### Overview

This plan defines the sequence of implementation phases for a research-grade benchmark evaluating dependency-aware selective regeneration strategies. The work spans 11 phases, each building on the previous.

### Phase Map

| Phase | Name                            | Status      |
|-------|---------------------------------|-------------|
| 0     | Bootstrap and Environment       | IN PROGRESS |
| 1     | Input Audit                     | PENDING     |
| 2     | Research Protocol               | PENDING     |
| 3     | Repository and Scenario Preparation | PENDING  |
| 4     | Benchmark Core                  | PENDING     |
| 5     | Strategies                      | PENDING     |
| 6     | Validation and Leakage          | PENDING     |
| 7     | Metrics and Statistics          | PENDING     |
| 8     | Kaggle Notebook                 | PENDING     |
| 9     | Packaging and Documentation     | PENDING     |
| 10    | Static and Local Engineering Audit | PENDING  |

### Dependencies

- Phase 0 must complete before Phase 1.
- Phase 1 must complete before Phase 2.
- Phases 2–3 can be partially parallelized.
- Phase 4 requires Phase 3 scenario definitions.
- Phase 5 requires Phase 4 benchmark core.
- Phase 6 requires Phase 5 strategies.
- Phase 7 requires Phase 6 leakage checks.
- Phase 8 requires Phases 4–7.
- Phase 9 requires Phase 8.
- Phase 10 runs at the end.

### Approved Repositories

| Size   | Repository            | Status |
|--------|-----------------------|--------|
| Small  | Controlled Django Todo| PENDING|
| Medium | django CMS            | PENDING|
| Large  | Saleor Core           | PENDING|
| Stress | ERPNext (optional)    | PENDING|

### Approved Strategies

- repository_agent (baseline)
- static_only
- semantic_only
- hybrid_selective
- traceability_only (additional impact strategy)
- full_context (only when feasible)

### Key Constraints

- No local model download or inference.
- All real LLM runs on Kaggle only.
- Correctness > efficiency.
- Python 3.11, Conda environment.
