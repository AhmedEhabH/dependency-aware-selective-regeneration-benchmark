# STAGE5 V2 FINAL CONFIRMATORY REPORT (2026-09-20)

**Mission:** FINAL THESIS IMPACT-LOCALIZATION FREEZE + ONE-SHOT STAGE-5 CONFIRMATORY EVALUATION
**Verdict:** `STAGE5_V2_FINAL_CONFIRMATION_FAIL`
`IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED`
**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731
**Companion documents:** `docs/STAGE5_V2_FINAL_IMPACT_DECLARATION_2026-09-20.md`,
`reports/STAGE5_FINAL_PREREGISTRATION_2026-09-20.md`,
`reports/stage5_final_preregistration.json`,
`reports/LOCAGENT_NATIVE_METRIC_COMPATIBILITY_2026-09-20.md`,
`reports/STAGE5_DESIGN_POWER_CHECK_2026-09-20.md`
**Audit:** `reports/stage5_independent_audit.json` (10/10 PASS)

---

## 1. Why method shopping stopped

The prior five-day method-search cycle is CLOSED. The thesis takes the single
best frozen DEVELOPMENT-selected candidate (`PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2`)
and evaluates it ONCE on untouched evidence. `NO_FURTHER_LOCALIZATION_METHOD_SHOPPING_FOR_CURRENT_THESIS`
holds after this mission regardless of outcome.

## 2. Why V2 was selected

V2 (Repository Memory Rescue) is the only DEV candidate whose point F1
improved over Sparse on BOTH repositories (djangoCMS 0.3451 vs 0.3177; Saleor
0.3476 vs 0.2605), with a positive pooled DEV descriptive delta (+0.0568). The
DEV per-repo gate official verdict remained FAIL (djangoCMS per-repo CI crossed
zero), which is why this mission exists.

## 3. Why DEV V2 was still officially FAIL

DEV djangoCMS: Delta F1 +0.0274, paired CI crosses zero -> criterion B FAIL.
DEV Saleor: Delta F1 +0.0871, CI positive -> PASS. `PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL`
and `BEST_FROZEN_DEV_CANDIDATE_NOT_CONFIRMED_SUPERIOR_ON_BOTH_REPOS` remain
unchanged. The DEV result is selection evidence, not confirmatory proof.

## 4. Why the Stage-5 endpoint differs from the old per-repository DEV gate

The historical rule — "each repository CI must independently exclude zero" —
is underpowered at n=59/80 and would be near-impossible to satisfy even under a
true positive effect. The frozen Stage-5 endpoint is ONE pre-registered pooled,
repository-stratified Delta-F1 vs Sparse (10,000 resamples, seed 20260920),
with per-repo point estimates and CIs as mandatory secondary results, plus a
direction-consistency condition to stop one repository from masking a true
negative in the other.

## 5. Why the endpoint was frozen BEFORE unsealing

`reports/STAGE5_FINAL_PREREGISTRATION_2026-09-20.md` + `.json` were written, the
final V2 deployment model (threshold 0.20) was frozen with config SHA
`8925d29a…`, the preregistration was committed
(`4badcea1…`) and pushed, and the immutable tag
`stage5-v2-final-preregistered-2026-09-20` was created and pushed BEFORE any
Stage-5 outcome was read. `STAGE5_IRREVERSIBLE_CHECKPOINT_REACHED` was printed.

## 6. Exact Stage-5 sample

djangoCMS RESERVE n = 59, Saleor INTERNAL_TEST n = 80, TOTAL n = 139.
`SALEOR_RESERVE_POWER_EXTENSION = NO` (Saleor RESERVE untouched).

## 7. Exact primary endpoint

`repo-stratified pooled micro-F1 difference (V2 minus Sparse)`.
Per replicate: resample 59 dc tasks and 80 saleor tasks with replacement;
pool TP/FP/FN across BOTH strata for V2 and for Sparse; compute each F1;
DeltaF1_b = F1_V2,b - F1_Sparse,b. 10,000 resamples, seed 20260920. 95% CI =
[Q2.5, Q97.5].

## 8. Exact success rule (frozen; not changed after unsealing)

- A: pooled stratified Delta F1 point > 0 AND 95% CI lower > 0.
- B: djangoCMS point Delta F1 > 0 AND Saleor point Delta F1 > 0.
Per-repo CIs are secondary, not gates.

## 9. Primary result

| Metric | Value |
|---|---|
| Pooled V2 F1 | 0.2269 |
| Pooled Sparse F1 | 0.2857 |
| **Delta F1 (point)** | **−0.0588** |
| 95% CI | **[−0.1119, −0.0084]** (excludes zero, negative) |
| Criterion A | FAIL (point < 0, CI lower < 0) |
| djangoCMS point Delta F1 | −0.0618 |
| Saleor point Delta F1 | −0.0570 |
| Criterion B | FAIL (both repos negative) |

**Verdict: `STAGE5_V2_FINAL_CONFIRMATION_FAIL`.**

Interpretation (frozen): the development improvement did NOT survive the
preregistered untouched confirmation. On the untried confirmatory population,
the frozen V2 policy was WORSE than the simple Sparse baseline in pooled
file-set F1; both repositories point in the same negative direction.

## 10. Per-repo results

| repo | n | Sparse TP/FP/FN | V2 TP/FP/FN | Sparse F1 | V2 F1 | Delta |
|---|---|---|---|---|---|---|
| djangoCMS | 59 | 38 / 69 / 106 | 30 / 75 / 114 | 0.3028 | 0.2410 | −0.0618 |
| Saleor | 80 | 52 / 102 / 173 | 40 / 103 / 185 | 0.2744 | 0.2174 | −0.0570 |

Precision/Recall/FNR (per repo; V2 vs Sparse):
- djangoCMS V2 P 0.2857 / R 0.2083 / FNR 0.7917; Sparse P 0.3551 / R 0.2639 / FNR 0.7361.
- Saleor V2 P 0.2797 / R 0.1778 / FNR 0.8222; Sparse P 0.3377 / R 0.2311 / FNR 0.7689.

On the Stage-5 (untouched) population, Sparse is BOTH more precise and more
sensitive than V2 on both repositories.

## 11. Acc@K compatibility (descriptive; NOT gate criteria)

| Population | Acc@1 | Acc@3 | Acc@5 | Hit@1 | Hit@3 | Hit@5 | Recall@1/3/5 |
|---|---|---|---|---|---|---|---|
| ALL 139 | 0.2374 | 0.1223 | 0.1223 | 0.2374 | 0.4173 | 0.4748 | 0.1004/0.2220/0.2683 |
| djangoCMS 59 | 0.1864 | 0.1356 | 0.1356 | 0.1864 | 0.4576 | 0.5085 | 0.0852/0.2606/0.3054 |
| Saleor 80 | 0.2750 | 0.1125 | 0.1125 | 0.2750 | 0.3875 | 0.4500 | 0.1116/0.1936/0.2410 |

These percentages are V2 Stage-5 descriptive compatibility numbers. They are
NOT compared directly to external SWE-bench/LocAgent headlines as a
winner/loser claim.

## 12. Set-size / error decomposition

| repo | Sparse size (mean/med/empty) | V2 size (mean/med/empty) | additions mean | drops mean |
|---|---|---|---|---|
| djangoCMS | 1.81 / 1 / 24 | 1.78 / 1 / 18 | 0.56 | 0.59 |
| Saleor | 1.93 / 1 / 19 | 1.79 / 1 / 13 | 0.84 | 0.98 |

V2 drops roughly as many true Sparse positives as it adds (on both repos),
and the added candidates are mostly false positives on the untouched data.

## 13. Efficiency

| phase | tokens | cost |
|---|---|---|
| Sparse write-set generation (139 tasks, qwen3-coder) | 1,702,783 | $0.544009 |
| Qwen query embeddings (139, realization-A method) | 5,827 | $0.000058 |
| Code-unit corpus embedding | 0 (all units already in the persisted E: cache) | $0.00 |
| **Total paid** | 1,708,610 | **$0.544067** |

Hard incremental ceiling $1.00 respected. No fallback provider, no model
substitution, no extra realization. Case-bundle materialization and repository
memory were zero-API local git operations. Full wall clock dominated by the 139
Sparse calls (~minutes each) + local dense/memory computation (~1 hour).

## 14. PASS / FAIL / MIXED

**`STAGE5_V2_FINAL_CONFIRMATION_FAIL`** (pooled CI excludes zero on the negative
side; both repository points negative).

## 15. What this PROVES

- The frozen DEV-selected V2 improvement did NOT transfer to untouched
  confirmatory evidence; on the confirmatory population the learned V2 policy
  is statistically worse than Sparse (pooled Delta F1 −0.0588, 95% CI
  [−0.1119, −0.0084]).
- The negative effect is direction-consistent (both repositories), so this is
  not a single-repository artifact.
- The pre-registered one-shot design, frozen endpoint and success rule were
  applied exactly, and an independent audit recomputed the result from raw
  artifacts without importing the analyzer (10/10 PASS).

## 16. What this does NOT prove

- It does NOT prove repository-memory signals are useless generally (DEV
  candidate-level deep-FN recovery remains descriptive evidence).
- It does NOT prove Sparse is a "final policy" or that no other method could
  beat Sparse on unseen data.
- It does NOT compare our numbers with LocAgent/Agentless as winner/loser.
- It does NOT open Saleor RESERVE, execute Stage-5 a second time, or change
  V1/V2/Sparse.

## 17. Why no further localization tuning is allowed

The one-shot confirmation is complete; `NO_FURTHER_LOCALIZATION_METHOD_SHOPPING_FOR_CURRENT_THESIS`
applies. Any further localization method is future work / follow-up
publication, not this thesis.

## 18. Governance

- Preserved exactly: `INDEPENDENT_DENSE_RETRIEVAL_REPLICATED`,
  `CALIBRATED_SET_SELECTION_V1_FAIL`, `PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL`,
  `ISSUE_GROUNDED_INTENT_SIGNAL_NOT_SUPPORTED`.
- Stage-5 result label: `STAGE5_V2_FINAL_CONFIRMATION_FAIL`;
  `IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED`.
- Stage-5 decision updated: thesis reports Sparse, dense recovery, V1, V2,
  untouched confirmation outcome, limitations -> `THESIS_AND_PAPER_EVIDENCE_CLOSURE`.
- Next scientific phase (separate authorized mission): external-validity and
  end-to-end regeneration. NOT executed here.