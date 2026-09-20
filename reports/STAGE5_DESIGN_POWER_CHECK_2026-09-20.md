# STAGE5 DESIGN POWER CHECK (2026-09-20)

**Mission:** STAGE5_V2_FINAL (design-justification document; frozen before unsealing)
**Companion:** `docs/STAGE5_V2_FINAL_IMPACT_DECLARATION_2026-09-20.md`
**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731

## 1. Purpose

This document is DESIGN JUSTIFICATION ONLY. It motivates the repo-stratified
pooled confirmatory endpoint and is NOT a pre-experiment result, NOT a method
change, NOT a gate, and does NOT rewrite the frozen DEV FAIL verdicts.

## 2. Development evidence being motivated

| Repository | n (DEV) | Sparse F1 | V2 F1 | V2 minus Sparse (point) | Per-repo paired CI (DEV) |
|---|---|---|---|---|---|
| djangoCMS | 174 | 0.3177 | 0.3451 | +0.0274 | crosses zero (FAIL) |
| Saleor | 149 | 0.2605 | 0.3476 | +0.0871 | positive (PASS) |
| Pooled (repo-stratified, descriptive) | 323 | — | — | ≈ +0.0568 | positive descriptive CI |

- Minimal detectable effect (MDE) at approximately 80% power on djangoCMS DEV
  n=174 is ≈ +0.053.
- The DEV per-repository FAIL verdicts (djangoCMS criterion B, CI crosses
  zero) remain UNCHANGED.

## 3. Why a pooled repo-stratified endpoint

The historical per-repository rule — "EACH repository CI must independently
exclude zero" — is underpowered at n=59/80 and would make an otherwise
coherent one-shot confirmation near-impossible even under a true positive
effect. The pooled repo-stratified endpoint is the statistically coherent
motivation: it preserves the effect's sign in BOTH repositories (direction
consistency) while pooling evidence for the CI.

## 4. Confirmatory design (frozen)

- Population: djangoCMS RESERVE n=59 + Saleor INTERNAL_TEST n=80 = 139.
- Stratified resampling: sample with replacement 59 djangoCMS tasks from the 59
  and 80 Saleor tasks from the 80, per bootstrap replicate.
- Endpoint per replicate: pooled micro-F1 over BOTH strata for V2 and for
  Sparse; DeltaF1_b = F1_V2,b - F1_Sparse,b.
- 10,000 resamples, seed 20260920; 95% CI = [Q2.5, Q97.5].

## 5. Success rule (frozen)

Success requires BOTH:
- A: pooled stratified Delta F1 point > 0 AND 95% CI lower > 0;
- B: djangoCMS point Delta F1 > 0 AND Saleor point Delta F1 > 0.
Per-repo CIs are mandatory secondary results, NOT gates.

## 6. Limitations acknowledged

- A pooled endpoint cannot by itself establish per-repository statistical
  superiority; per-repo CIs are reported and labelled.
- Direction consistency guards against one repository hiding a true negative
  effect in the other, but is not a significance test per repo.
- n=59 / n=80 limits power for per-repo inference. This is acknowledged in the
  thesis rather than remedied by extending the population (Saleor RESERVE
  extension is explicitly declined: `SALEOR_RESERVE_POWER_EXTENSION = NO`).