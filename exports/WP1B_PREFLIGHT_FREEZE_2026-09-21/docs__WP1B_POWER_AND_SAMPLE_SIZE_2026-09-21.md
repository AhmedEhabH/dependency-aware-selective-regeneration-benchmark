# WP-1b Power and Sample Size — 2026-09-21

**Status:** PREREGISTERED. Sample-size amendment G9: MAIN_50 → MAIN_297
(authority D4). This document contains OpenCode's own bootstrap re-derivation
of the power numbers in Appendix R-C (external reference; not trusted as
authority). It is a prospective, label-free analysis: no WP-1b agent prediction,
no scoring, no outcome has been produced.

## 1. Exposure argument (unchanged exposure class)

MAIN_50 is already a subset of the opened RESERVE-300. Every one of the 300
has the same exposure status: labels read on 2026-09-20 for the RM-CSS
evaluation; no agent output ever produced; agent protocol frozen in WP-1a
before any agent call. Using all 297 (300 minus the 3 Calibration-3 tasks)
adds no new exposure class. The 786 sealed tasks are untouched.

## 2. Why n = 297

At n = 50 the one-sided 95 % lower bound has a half-width of about
0.045–0.088. If RM-CSS and the agent are truly equal (true D = 0), the chance
of showing non-inferiority at Δ = 0.05 is only about 24–56 % at n = 50 but
about 74–100 % at n = 297. A result that is "INCONCLUSIVE" by design wastes the
run.

## 3. Method (own re-derivation)

The SE of D = F1(RM-CSS) − F1(Agent) is unknown before WP-1b. It is bracketed
between:

- **lower bound (highly-correlated methods, RM-CSS vs its own SIP input):**
  the paired-task bootstrap SE of F1(RM-CSS) − F1(SIP) on MAIN_50;
- **upper bound (independent methods):** √2 × SE(F1(RM-CSS)) on MAIN_50.

Both SEs are computed by a paired task bootstrap with 10,000 resamples,
seed 20260920, unit = task (resample task IDs with replacement and recompute
both pooled micro-F1 values each draw). The bracket is then scaled by √(50/n)
for n ∈ {50, 150, 297}.

## 4. Own numbers (re-derived, AGREE with Appendix R-C)

| Quantity | OpenCode value | R-C value | Status |
|----------|----------------|-----------|--------|
| SE(RM-CSS pooled F1) @ n=50 | 0.0376813 | 0.0377 | AGREE |
| SE(RM-CSS − SIP) @ n=50 (paired) | 0.0276508 | 0.0277 | AGREE |
| SE(D) bracket @ n=50 | 0.028 (correlated) · 0.040 (mid) · 0.053 (independent) | same | AGREE |
| mid SE @ n=150 | 0.0234 | 0.0234 | AGREE |
| mid SE @ n=297 | 0.0166 | 0.0166 | AGREE |

## 5. Power of the one-sided NI test (Δ = 0.05, α = 0.05)

One-sided lower bound > −0.05; power = 1 − Φ(1.645 − (D + 0.05)/SE). For true
D = 0:

| n | correlated (SE 0.028→) | mid | independent (SE 0.053→) |
|---|------------------------|-----|--------------------------|
| 50  | 0.56 | 0.34 | 0.24 |
| 150 | 0.93 | 0.69 | 0.49 |
| 297 | 1.00 | 0.91 | 0.74 |

At n = 50 (mid SE), RM-CSS needs a point estimate of about **+0.017** to reach
Q5 > −0.05; at n = 297 it needs about **−0.023** (it may be slightly worse than
the agent and still demonstrate non-inferiority).

## 6. Interpretation

- The NI decision at n = 297 has 74 % power even in the worst-case independent
  bracket and ≥ 91 % under the mid bracket when the two methods are truly equal.
- MAIN_297 is NOT a new untouched or held-out confirmatory sample: it is a
  prospective sample-size amendment over the already-opened Saleor-300
  population (same exposure class as MAIN_50).
- The primary fail-closed analysis and the instrument-failure-excluded
  sensitivity analysis remain distinct and preregistered (see
  `research/wp1b/wp1b_decision_rules_v2.json`); power is computed for the
  primary analysis.

## 7. Manifest (B2)

- `research/wp1b/wp1b_main_297_manifest.json` — n=297; first 50 == WP-1a
  MAIN_50 exactly; calibration-3 IDs absent; hashes recorded.
- `research/wp1b/wp1b_main_150_manifest.json` — n=149 (one calibration task,
  `saleor-rc-349d46d906ad`, removed from the first 150).
- `research/wp1b/wp1b_main_50_manifest.json` — reference copy of the unchanged
  WP-1a MAIN_50.

Execution order for Phase D = manifest order (MAIN_50 first).

## 8. Falsifiers

- This power analysis is wrong if the frozen WP-1a sample ordering changed
  (it did not; `selected_ids_sha256` unchanged).
- It is wrong if the WP-1b agent arm's F1 variance is materially outside the
  bracketing assumptions (e.g., systematic empty-prediction clustering not
  captured by the RM-CSS-vs-SIP paired SE or the independent bound); the
  bracket is intentionally wide to cover this.