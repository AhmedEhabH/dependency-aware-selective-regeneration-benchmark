# Master Implementation Plan

## Dependency-Aware Selective Regeneration for LLM-Assisted Software Evolution

### Overview

This plan defines the sequence of implementation phases for a research-grade benchmark evaluating dependency-aware selective regeneration strategies. The work spans 11 phases, each building on the previous.

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

## Next

- Merge SU-0011
- Scientific Smoke (only after merge, only after stable tag)
- Pilot (remains unauthorized until Scientific Smoke passes)

## Known Boundary

- neutral empty graph when no profile graph exists
- real repository dependency inference remains deferred
- Scientific Smoke and Pilot remain unauthorized

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
