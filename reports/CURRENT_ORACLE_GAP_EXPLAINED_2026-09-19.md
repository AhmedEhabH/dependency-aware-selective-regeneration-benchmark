# The Oracle Gap, Explained (2026-09-19)

## 1. What the "gap" is

We evaluate a localization method by the final file set it selects (Sparse
first pass ∪ ranked additions at budget B) against the observed change-set
proxy. Two ceilings define the gap:

- **Oracle-Add (perfect recall):** an oracle that adds the correct missing
  files gives file-level F1 ≈ **0.867** (djangoCMS) / **0.829** (Saleor) —
  the Sparse FP tail keeps F1 < 1.
- **Oracle-Drop (perfect precision):** an oracle that removes false positives
  gives ≈ **0.396** / **0.349**.
- **Bidirectional (both oracles):** F1 = 1.0.
- **F1 = 0.85 is NOT add-only-reachable on Saleor** (ceiling 0.829); it
  requires bidirectional repair.

The measured Sparse baseline is F1 ≈ 0.318 (djangoCMS) / 0.261 (Saleor), so
there is large headroom — but it is gated by specific bottlenecks.

## 2. Decomposition (who owns the loss)

Measured on DEVELOPMENT (frozen; see `reports/ORACLE_GAP_ERROR_DECOMPOSITION.md`):

1. **First-pass recall loss (dominant):** Sparse misses 75–79% of proxy
   positives. Oracle-Add ALL recovers +0.55–0.57 F1.
2. **Review false-acceptance (second):** Route-B add-only LOWERS file-level F1
   at every B (adding candidates without a precision-safe acceptance rule adds
   mostly FPs).
3. **Ranking (third):** even with a perfect reviewer, Route-B top-B ordering
   caps F1 ≈ 0.44 / 0.43 @B=5 (vs Oracle-Add 0.72 / 0.64).
4. **Budget:** ≈ 0 (not adaptive budget).

Conclusion: availability is NOT the binding constraint; **ranking** of the
omitted pool is.

## 3. Why the "ORR up but F1 down" failures happen

- Macro ORR is a per-task ratio mean; pooled F1 is a global ratio over pooled
  positives. A conservative verifier that over-rejects easy single-FN
  recoveries (M=1 tasks) can lower macro ORR while the pooled FP tail shrinks
  and pooled F1 rises (the Stage-4b djangoCMS pattern, verified from raw task
  data: Arm A recovered the single FN on 3 M=1 tasks, Arm B did not).
- Any future instrument must therefore report BOTH (impact correctness
  P/R/F1/FNR AND the ORR mechanism diagnostic), and gates must not make ORR the
  sole criterion.

## 4. Where the new embedding signal fits

SweRankEmbed-Small (DEV) is the first signal to raise ORR **and** F1 **and**
precision together on both repos — i.e., it starts to close the RANKING and
RECALL losses simultaneously without growing the FP tail (candidate precision
roughly doubles). This is why it PASSED the frozen gate. The remaining gap to
the Oracle ceilings is still large (F1 0.28 vs 0.87 ceiling) — the ceiling
itself is not the target; the signal is a ranking/recovery improvement, not
final-set superiority.

## 5. What this does NOT mean

- F1 = 0.85 is an aspirational analysis point, NOT a tuning target.
- The embedding result does NOT close the whole gap; it is a diagnostic PASS
  on DEVELOPMENT with a contamination caveat.
- No Stage-5/confirmatory claim is made.