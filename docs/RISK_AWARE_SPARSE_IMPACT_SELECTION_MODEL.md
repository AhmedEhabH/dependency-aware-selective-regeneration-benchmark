# Risk-Aware Sparse Impact Selection Model

**STATUS:** DESIGN / THEORY FOR POSSIBLE FUTURE v3
**Date (UTC):** 2026-09-08
**Branch:** `research/djangocms-external-validity-prep-01`
**Relation:** companion to `reports/DJANGOCMS_IMPACTPLAN_V2_RESULTS.md`
**Constraint:** DESIGN ONLY. ZERO scientific calls. Does NOT modify v2 code or
results. Must NOT be executed or tuned on the six hidden-gold djangoCMS test
scenarios.

---

## 1. Purpose

The frozen ImpactPlan-v2 study evaluates a sparse, auditable, repository-level
impact policy representation. This note sketches a possible future v3 that makes
the selection decision risk-aware and prices serialization cost explicitly.
It is exploratory theory, not a committed design.

## 2. Notation

For candidate `i`:

- `q_i` — estimated probability that the file requires regeneration.
- `C_FN(i)` — cost of missing a required write (false negative).
- `C_FP(i)` — cost of an unnecessary selection (false positive).
- `t_i` — marginal emitted-token cost of explicitly deciding candidate `i`.
- `lambda_T` — token-cost weight (how much serialization cost matters relative
  to selection errors).

## 3. Binary expected losses (REGENERATE vs PRESERVE)

Choosing REGENERATE (`R`) for candidate `i`:

```
L_R(i) = (1 - q_i) * C_FP(i) + lambda_T * t_i
```

Choosing PRESERVE (`P`) for candidate `i`:

```
L_P(i) = q_i * C_FN(i)
```

Choose `R` when `L_R(i) < L_P(i)`, i.e.:

```
q_i  >  (C_FP(i) + lambda_T * t_i) / (C_FN(i) + C_FP(i))
```

### Interpretation

When `C_FN >> C_FP` (a missed write is much worse than an over-selection), the
threshold decreases, deliberately favoring Recall while still pricing
over-selection and serialization cost. The `lambda_T * t_i` term makes the
model favor fewer, more informative explicit decisions when serialization
tokens are priced.

## 4. Four-action generalization

Generalizing to `{R, P, V, H}` (REGENERATE, PRESERVE, VALIDATE, HUMAN_REVIEW):

```
a_i* = argmin_{a in {R,P,V,H}} [ ExpectedRisk(a | x_i) + lambda_T * TokenCost(a) ]
```

`TokenCost(a)` is 0 for PRESERVE (omitted under sparse encoding) and positive
for explicit actions.

## 5. Important caveats

- Raw LLM confidence is NOT automatically a calibrated probability. Do NOT
  label `q_i` as a probability unless calibration is demonstrated; otherwise
  `q_i` is only a ranking score.
- Thresholds/weights must NOT be fitted on the same six hidden-gold djangoCMS
  test scenarios and then evaluated on those scenarios.
- Calibration requires a separate development protocol with a separate
  development/calibration set and an untouched held-out evaluation set.

## 6. Possible future soft graph evidence

If soft dependency-graph evidence `g_i` (deterministic, normalized) were
available:

```
logit(q_i') = logit(q_i) + beta * g_i
```

- Do NOT execute this model now.
- Do NOT tune `beta` from hidden test gold.
- Do NOT hard-prune candidates in the current study (hard exclusion of a true
  gold candidate before LLM selection imposes an upper bound on achievable
  Recall).

## 7. Status

All of the above is **Future v3 / Future Work**. It is retained as a framework
only. The current v2 study makes NO use of risk-aware thresholds, calibration,
or graph evidence.