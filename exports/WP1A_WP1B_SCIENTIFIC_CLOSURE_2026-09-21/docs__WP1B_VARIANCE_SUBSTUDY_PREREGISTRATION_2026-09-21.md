# WP-1b Variance Substudy — Preregistration (G5)

**Date:** 2026-09-21
**Status:** PREREGISTERED BEFORE OUTCOMES. Salt and selection frozen before any
WP-1b calibration/main inference. No WP-1b outcome has been observed.

## Purpose

Estimate execution variability of the repository-agent (Agent) arm. The main
experiment must not silently rely on one provider execution as though it were
perfectly deterministic.

## Design

- Subset size: **15** of the frozen main-50 tasks.
- Runs per selected task: **3** total Agent executions (temperature 0.0,
  identical to the main protocol).
- All scientific knobs identical to the main Agent arm
  (`docs/WP1B_KNOB_REGISTRY_2026-09-21.md`).
- **The first main execution does NOT count as replicate 1.** This rule is NOT
  pre-registered as "replicate 1 = main run"; all 3 repeats are fresh
  executions.

## Selection procedure (deterministic, outcome-free)

1. Canonical task IDs from the frozen main-50 manifest
   (`research/wp1a/wp1_main_50_manifest.json`).
2. `digest = sha256("<salt>" + task_id)`.
3. Sort ascending by digest.
4. Select the first 15.

| Field | Value |
|-------|-------|
| salt | `wp1b-variance-substudy-v1-2026-09-21` |
| algorithm | `sha256(salt + task_id)`, sort ascending by digest, first 15 |
| selection-manifest SHA256 | `2c4ac5b192dfc2f1432d09b95a22410102d8ae00913fe1b4bd96da45f7ee95f9` |

Machine-readable: `artifacts/wp1b_variance_substudy_preregistration_2026-09-21.json`
(with the full ordered digest list).

Selected 15 task IDs:

```
saleor-rc-1a8b592913a0
saleor-rc-1f6fbe2ebf9b
saleor-rc-032b98afff20
saleor-rc-0ad61b3f0096
saleor-rc-070f4bd7c042
saleor-rc-11756ee6b65a
saleor-rc-22a30bf2e4cc
saleor-rc-0f16ed78b02b
saleor-rc-19bb9b070965
saleor-rc-14f2176b5d8c
saleor-rc-0713acb0f004
saleor-rc-07c8859c0ac3
saleor-rc-1f9b5c53a63a
saleor-rc-1b4da5a88d08
saleor-rc-0df62b3144b0
```

## Pre-registered metrics (at minimum)

- per-task F1 across repeats
- aggregate F1 across repeats
- selected-path exact-match rate
- selected-path Jaccard similarity
- prediction-size variance
- input token variance
- output token variance
- cost variance
- latency variance
- cap-hit frequency
- final-answer truncation frequency
- EMPTY frequency
- provider-route frequency (if routing varies)

## Interpretation boundary

> This substudy estimates execution variability. It does NOT convert a 15-task
> subset into evidence equivalent to three complete main-50 replications.

## Falsifiers

- This preregistration is wrong if the salt or algorithm was changed after
  WP-1b outcomes were observed (it was frozen before any outcome).
- The subset is invalid if it was selected using F1, difficulty, method output,
  or any post-result criterion (it was not).