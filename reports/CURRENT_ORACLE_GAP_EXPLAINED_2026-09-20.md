# The Oracle Gap, Explained — V1 UPDATE (2026-09-20)

**Status:** dated successor of `reports/CURRENT_ORACLE_GAP_EXPLAINED_2026-09-19.md`
(the 2026-09-19 file remains immutable). This file keeps the 2026-09-19
content in force and ADDS the CALIBRATED_SET_SELECTION_V1 update.

---

## 0. Recap of the frozen 2026-09-19 position (unchanged)

- Oracle-Add ALL caps file-level F1 at ≈ 0.867 (djangoCMS) / 0.829 (Saleor);
  Oracle-Drop ALL ≈ 0.396 / 0.349; bidirectional reaches F1 1.0.
- Measured Sparse baseline: F1 ≈ 0.318 / 0.261.
- Decomposition: first-pass recall loss dominant (75–79% of proxy positives
  missed), review false-acceptance second, ranking third, budget ≈ 0.
- The dense-ranking signal (SweRank, then Qwen A/B)
  (`INDEPENDENT_DENSE_RETRIEVAL_REPLICATED`) is a ranking/recovery
  improvement, not final-set superiority.

---

## 1. CALIBRATED_SET_SELECTION_V1 update (2026-09-20)

The V1 calibrated policy (L2-LR, 7 frozen features, nested 5×5 task-grouped
CV, inner-OOF F1 threshold, ADD+KEEP+DROP, no fixed B) was evaluated on
DEVELOPMENT. Primary verdict: **`CALIBRATED_SET_SELECTION_V1_FAIL`** (both
realizations A and B fail the same criterion). Point estimates improve over
Sparse on BOTH repositories (djangoCMS F1 0.318 → 0.334; Saleor 0.261 →
0.336), but the djangoCMS paired-bootstrap 95% CI for Delta F1 crosses zero
([−0.019, +0.053]), so that improvement is not statistically distinguished.

### 1.1 The remaining Oracle gap after V1 (decomposed, realization A)

V1 reaches file-level F1 0.334 (djangoCMS) / 0.336 (Saleor) vs the
Oracle-Add ALL ceiling 0.867 / 0.829. The remaining error (policy
false negatives) separates into exactly the four sources of the frozen
ladder (Section 28 of the mission), measured from the artifacts
(`reports/calibrated_set_selection_v1_oracle_gap.json`):

| Error source (djangoCMS / Saleor) | Count | Meaning |
|---|---:|---|
| 1. Ranking / candidate-coverage error | 199 / 177 | proxy positives that are NOT in the frozen candidate universe (Sparse ∪ top-20) — the dense rank did not bring them into the ADD pool |
| 2. ADD decision error | 154 / 138 | proxy positives that ARE in the top-20 ADD pool but fell below the learned probability threshold |
| 3. DROP decision error | 14 / 6 | Sparse true positives that the policy accidentally dropped |
| 4. Historical changed-file proxy ambiguity | not countable | the proxy is the observed change set, not perfect semantic gold (see §1.2) |
| **Total policy FN** | **367 / 321** | = 1 + 2 + 3 (matches the pooled FN of the V1 final set) |

Interpretation:

1. **Candidate-coverage (199/177) is now the LARGEST remaining error source.**
   The top-20 ADD universe recovers 183/192 of the omitted positives into the
   pool but leaves 199/177 outside. This is exactly the ranking/coverage
   boundary of the frozen V1 design (TOP_ADD_UNIVERSE = 20).
2. **ADD decision error (154/138)** is the second source: the LR threshold
   is conservative (it also limits the FP tail); it refuses many positives
   that ARE in the pool.
3. **DROP decision error (14/6)** is small but real: the policy trades a few
   Sparse true positives for a large reduction in Sparse false positives
   (44/57 dropped).
4. **Proxy ambiguity** remains an unquantified component of every number in
   this project (the observed change set can be tangled, incidental, or
   incomplete).

### 1.2 Oracle is NOT a realistic method

As in the 2026-09-19 version: the Oracle ceilings are analysis points that
define headroom, NOT tuning targets, and the Oracle was NOT used to tune V1.
V1's frozen design (features/model/folds/threshold procedure/gate) was frozen
BEFORE any outer-OOF inspection.

### 1.3 What this means for the research ladder

- First-pass recall (ranking/coverage) remains the dominant loss — the same
  conclusion as 2026-09-19, now re-quantified AFTER the calibrated policy.
- The calibrated ADD+DROP policy is a directionally positive but statistically
  weak instrument on djangoCMS under the frozen gate; it is a frozen negative
  verdict (`CALIBRATED_SET_SELECTION_V1_FAIL`).
- Stage 5 stays PAUSED/SEALED: `FINAL_POLICY_NOT_FROZEN` (the dense-mechanism
  replication means lack of replication is no longer a blocker, but the
  final-set policy is not frozen as a success).

### 1.4 What this does NOT mean

- It does NOT prove the calibrated family is useless (point estimates improve
  on both repos; Saleor CI excludes zero).
- It does NOT justify a V2 by adding features now (any V2 requires a new
  mission and a new frozen hypothesis).
- It does NOT unlock Stage 5 and does NOT change any frozen verdict
  (SweRank/Qwen diagnostics, provenance verdict C, Stage-4/4b negatives).