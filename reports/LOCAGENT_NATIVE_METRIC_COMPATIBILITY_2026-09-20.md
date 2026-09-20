# LOCAGENT_NATIVE_METRIC_COMPATIBILITY (2026-09-20)

**Mission:** STAGE5_V2_FINAL (integrated and audited BEFORE unsealing)
**Companion:** `docs/STAGE5_V2_FINAL_IMPACT_DECLARATION_2026-09-20.md`
**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731

Purpose: integrate the post-hoc LocAgent-native metric-compatibility facts from
PERSISTED DEV artifacts and independently audit them, before Stage-5 unsealing.
These metrics are DESCRIPTIVE / COMPATIBILITY-ONLY. They do NOT change method
selection, the Stage-5 endpoint, or the frozen V2 policy.

---

## 1. Metric definitions (frozen)

For task i, with ranking R_i (frozen V2 ranking) and target file set G_i:

- Acc@K_i = 1[ |TopK(R_i) ∩ G_i| == min(|G_i|, K) ]
  Acc@K = mean over tasks.
- Hit@K = mean_i 1[ |TopK(R_i) ∩ G_i| >= 1 ].
- Recall@K = mean_i |TopK(R_i) ∩ G_i| / |G_i|.

These are DISTINCT from set-F1 (the primary endpoint). They are NEVER
compared directly to published LocAgent/SWE-bench headline percentages as a
winner/loser claim.

**V2 ranking definition used:** the frozen V2 OOF-probability ranking over the
frozen V2 candidate universe (Sparse ∪ Qwen dense-top20-non-Sparse ∪ memory),
sorting candidates by descending final-model probability, tie-break ascending
path. This is the ranking of the deployed V2 policy — the most direct
"V2 top-K list" analogue.

## 2. Verified DEV facts (all 323 DEV tasks; Qwen realization A)

| Metric | Value |
|---|---|
| V2 Acc@1 | 0.4737 (stated ~47.4%) |
| V2 Acc@3 | 0.2508 (stated ~25.1%) |
| V2 Acc@5 | 0.2663 (stated ~26.6%) |
| V2 Hit@1 | 0.4737 |
| V2 Hit@3 | 0.6625 |
| V2 Hit@5 | 0.7492 (stated ~74.9%) |
| V2 Recall@1 | 0.2179 |
| V2 Recall@3 | 0.3911 |
| V2 Recall@5 | 0.4837 |
| Single-target slice (|G_i|=1, n=80): V2 Acc@5 | 48/80 = 0.600 (stated 60.0%) |

The mission-stated DEV numbers (`Acc@1 47.4%, Acc@3 25.1%, Acc@5 26.6%,
Hit@5 74.9%; single-target |G|=1 n=80 Acc@5 = 60.0%`) are REPRODUCED from the
persisted artifacts.

## 3. Historical P5-C LocAgent exposed 10-task run (reference only)

From `research/locagent-p5b/shared_comparison.json` `locagent_native`:

| Acc@K | 1 | 3 | 5 |
|---|---|---|---|
| Official Acc@K | 4/10 | 4/10 | 2/10 |
| Hit@K | 4/10 | 4/10 | 4/10 |

Definition in that artifact: "Acc@K (official) = task hit iff #correct among
top-K == min(len(proxy), K); Hit@K = task hit iff >=1 proxy file among top-K."

These are a DIFFERENT exposed 10-task population (P1 HELD_OUT_TEST), not our
323-task DEV population, and NOT the Stage-5 confirmatory population. No direct
cross-population comparison is made.

## 4. Integrity statements

1. All numbers in section 2 were recomputed from persisted label-free score /
   memory / OOF artifacts (research/contamination-bridge/qwen_embed/realization_A,
   research/memory-rescue-v2/oof_probabilities_A.parquet, DEV tasks).
2. The mission is entitled to report V2 Acc@K/Hit@K/Recall@K at Stage-5 with
   the SAME definitions; they are descriptive, non-gating, and never compared
   as winner/loser to external SWE-bench headlines.
3. The compatibility expression does not modify any frozen scientific input.

## 5. Audit

`scripts/stage5_native_compat_audit.py` recomputes every number here WITHOUT
importing the Stage-5 analyzer. See AUDIT SUMMARY at end of that script and
`reports/stage5_native_compat_audit.json`.