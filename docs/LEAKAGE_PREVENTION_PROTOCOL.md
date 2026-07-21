# Leakage Prevention Protocol — v1.0 (FROZEN)

**Part of:** Research Protocol v1.0
**Approval Date:** 2026-07-22

---

## 1. Ground-Truth Isolation

- Ground-truth annotations stored separately from evaluation pipeline code
- Evaluation code does not have access to ground-truth labels during execution
- Ground-truth files loaded only during the comparison/analysis stage

## 2. Hidden Test Separation (per AC-03)

**Hidden tests are mandatory for every scenario.** Hidden changed-requirement and regression tests must remain inaccessible to strategies and be used only for final scoring.

**Held-out scenarios (optional):** Where feasible, reserve two scenarios per repository for final held-out validation. Scenario holding out may be omitted if all eight are needed, but hidden tests remain mandatory. **Cross-validation is not a substitute** for hidden tests.

## 3. Static Snapshot Isolation

- Each repository snapshot is pinned by commit SHA before any analysis
- No dynamic repository alteration during impact analysis
- All strategies see the same repository state
- The candidate artifact universe is frozen per repository and scenario before any strategy execution (per AC-01)

## 4. Annotation Non-Contamination

- Annotators do not have access to strategy outputs during annotation
- Strategy outputs are generated after ground truth is finalized
- Annotators are blinded to which strategy produced which result (where feasible)

## 5. Cache Exclusion

- No caching of ground-truth answers in the execution pipeline
- Random seeds recorded to detect accidental determinism that could reveal patterns
- Fresh run directories isolate caches and prior outputs (per AC-06)

## 6. Data Flow Verification

Before analysis, audit the data pipeline to confirm:
- No ground-truth file is imported or loaded by any strategy module
- No strategy module reads annotation files
- Evaluation scripts load annotations only for scoring, not for execution control

This audit is documented.

## 7. Pre-Registration of Analyses

Primary analyses (hypothesis tests, metrics) specified before seeing results. Exploratory analyses clearly labelled as post-hoc. Analysis plan registered before experiment execution.

## 8. Post-Hoc Analysis Policy

Any analysis not pre-registered is labelled as "exploratory." Exploratory findings are reported with asterisks and clear disclaimers.

## 9. Determinism and Reproducibility (per AC-07)

Temperature zero and fixed seeds do not guarantee identical GPU LLM outputs. Deterministic components must reproduce exactly; model execution is best-effort reproducible. Record hardware, CUDA, kernels, quantization, packages, parameters, and all supported seeds. Retain repeated runs.
