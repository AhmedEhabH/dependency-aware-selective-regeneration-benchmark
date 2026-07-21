# Statistical Analysis Plan — v1.0 (FROZEN)

**Part of:** Research Protocol v1.0
**Approval Date:** 2026-07-22

---

## 1. Comparison Structure

- Paired comparisons: each method processes the same repository state and change
- Per-repository reporting
- Per-change-type stratification
- Per-model reporting (when multiple models)
- Failed runs retained and analysed (not discarded)

## 2. Hypothesis Tests

| Hypothesis | Test | Details |
|-----------|------|---------|
| H1 (recall) | Paired bootstrap CI | Compare recall distributions across strategies; report median difference with 95% CI |
| H1 (FNR) | Paired bootstrap CI | As above for false-negative rate |
| H2 (preservation) | Non-inferiority test | One-sided test with NI margin Δ = 0.05; lower bound of one-sided 95% CI for selective − baseline > −0.05. Also report two-sided 95% CI and sensitivity at Δ = 0.03 and 0.10 |
| H3 (architecture) | Descriptive + McNemar | Compare violation detection rates; McNemar's test for paired binary outcomes |
| H4 (efficiency) | Paired bootstrap / Wilcoxon | Effect size (Cliff's delta or Cohen's d) with 95% CI; conditional on equivalent correctness |
| H5 (sensitivity) | Mixed-effects model | efficiency ~ blast_radius * strategy + (1|repository) + (1|scenario) |

## 3. Non-Inferiority Margin (per DA-08)

Δ = 0.05 for regression pass rate. Selective regeneration is non-inferior when the lower bound of the one-sided 95% confidence interval for selective minus baseline is greater than -0.05. Also report the observed difference, a two-sided 95% CI, and supplementary sensitivity analyses at 0.03 and 0.10.

## 4. Multiple-Comparison Correction (per DA-14)

- **No blanket correction** across the five distinct pre-specified primary hypotheses (H1–H5).
- **Benjamini-Hochberg** within secondary/exploratory comparison families.
- **Holm** for small confirmatory pairwise families where strong family-wise control is appropriate.
- Report raw and adjusted p-values, method, and family membership. Exploratory formal tests are not automatically exempt from correction.

## 5. Effect Size Reporting

- Report effect sizes with confidence intervals for all primary comparisons
- Cohen's d for normally distributed outcomes
- Cliff's delta for non-parametric comparisons
- Interpretation thresholds documented

## 6. Power Analysis

Minimum detectable effect size given 8 scenarios × 3+ strategies × 2+ repositories = 48+ paired observations. Post-hoc power estimation may be reported but not used as exclusion criterion.

## 7. Outlier and Exclusion Policy

All runs reported in raw form; exclusions documented with rationale. Exclusion criteria: infrastructure failure (not model error), human error in scenario definition. Sensitivity analysis with and without excluded points.

## 8. Reporting Format

- Per-change results in table (each row = one scenario × one strategy)
- Per-repository summary statistics
- Aggregate results with forest plots or similar
- Failed runs reported separately with reasons

## 9. Regression Pass Rate Formula (per AC-02)

- **Regression pass rate** = passed regression tests / total regression tests
- **Regression failure rate** = newly failing regression tests / total regression tests

Report counts and rates. The draft's "regressed_tests / total, inverted" wording is corrected.
