# V20 Claims-vs-Evidence Matrix

**Branch:** `paper/v20-final`
**Audit type:** zero-API, all values recomputed from frozen raw evidence.
**Date:** 2026-09-15

Every numeric claim in `paper/v20-final/v20_body.tex` is listed below with its
frozen evidence source and a PASS/FAIL recomputation result. No scientific
model call was made to produce this matrix.

| # | Claim in V20 | Value in paper | Frozen evidence | Recompute | Status |
|---|---|---|---|---|---|
| 1 | Candidate universe size | 144 paths | `benchmark_data/external_validity/djangocms_5_0_0_candidate_universe.json` | 144 records | PASS |
| 2 | Full explicit policy record count | 140--152 | `reports/REAL_COMMIT_M4A3_P1_SERIALIZATION_METRIC_CORRECTION.md` §1 | candidate counts 140--152, mean 144 | PASS |
| 3 | M1 completion tokens | Full 8,383 / Sparse 809 | `reports/CONTROLLED_ENCODING_16K_RESULT.md` | 8,383 / 809 | PASS |
| 4 | M1 serialized records | Full 144.0 / Sparse 5.9 | README M1B footnote (corrected 5.9) | 144.0 / 5.9 | PASS |
| 5 | M1 precision | 0.452 / 0.721 | `reports/CONTROLLED_ENCODING_16K_RESULT.md` | 0.451456 / 0.721088 | PASS |
| 6 | M1 recall | 0.775 / 0.883 | same | 0.775000 / 0.883333 | PASS |
| 7 | M1 F1 | 0.571 / 0.794 | same | 0.570552 / 0.794007 | PASS |
| 8 | M1 cost | $0.275 / $0.048 | same | 0.275124 / 0.048032 | PASS |
| 9 | M1 validity | 60/60, 0 truncations | same | 30/30 per arm, 0 | PASS |
| 10 | M1 completion reduction | ~90% | 1 - 809/8383 | 90.35% | PASS |
| 11 | M1 record reduction | ~96% | 1 - 5.9/144 | 95.9% | PASS |
| 12 | Scenario 006 Sparse recall | 0.333 vs Full 0.800 | `docs/PAPER_WRITING_HANDOFF.md` §2 / M1 defensive closure | 0.333 / 0.800 | PASS |
| 13 | P1 precision | Full 0.339 / Sparse 0.387 | `research/real-commit-p1-01/final_metrics.json` | 0.338843 / 0.386667 | PASS |
| 14 | P1 recall | 0.369 / 0.261 | same | 0.369369 / 0.261261 | PASS |
| 15 | P1 F1 | 0.353 / 0.312 | same | 0.353448 / 0.311828 | PASS |
| 16 | P1 FNR | 0.631 / 0.739 | same | 0.630631 / 0.738739 | PASS |
| 17 | P1 completion tokens | 8,445.8 / 599.0 | same | 8445.833 / 599.0 | PASS |
| 18 | P1 serialized records | 144.0 / 4.07 | correction report §4 | 144.000 / 4.067 | PASS |
| 19 | P1 cost | $0.2976 / $0.0623 | `final_metrics.json` | 0.297623 / 0.062341 | PASS |
| 20 | P1 Δcompletion | −7,848 CI[−8,136,−7,597] | `reports/REAL_COMMIT_M4A3_P1_RESULT.md` §6 | −7,847.9 [−8,136.0,−7,596.8] | PASS |
| 21 | P1 Δrecords | −139.9 CI[−143.3,−137.0] | correction report §4 | −139.910 [−143.300,−137.000] | PASS |
| 22 | P1 Δcost | −$0.0235 CI excl. zero | P1 result §6 | −0.023531 [−0.024396,−0.022778] | PASS |
| 23 | P1 ΔF1 | −0.009 CI[−0.130,+0.119] | P1 result §6 | −0.008822 [−0.129720,+0.118938] | PASS |
| 24 | Per-task P1 F1 table | 10 values | P1 result §5 | matches row-by-row | PASS |
| 25 | P5 valid executions | 5/10 non-empty | `research/locagent-p5b/out_c/merged_loc_outputs_mrr.jsonl` | 5 rows with found_files | PASS |
| 26 | P5 precision | 0.435 | independent recompute (TP10/FP13) | 0.434783 | PASS |
| 27 | P5 F1 | 0.333 | independent recompute | 0.333333 | PASS |
| 28 | P5 failure taxonomy | 2 timeout / 1 context / 2 empty | `out_c/localize.log` (raw) | verified from log markers | PASS |
| 29 | P5 50% empty, not 50% timeout | 5 empty, only 2 timeout | same | 2/10 timeout | PASS |
| 30 | P5 ΔF1 Loc−Full | −0.068 [−0.250,+0.170] | `shared_comparison.json` + scorer | −0.0684 [−0.2496,+0.1702] | PASS |
| 31 | P5 ΔF1 Loc−Sparse | −0.061 [−0.306,+0.241] | same | −0.0607 [−0.3057,+0.2409] | PASS |
| 32 | P5 official Acc@K | 4/10, 4/10, 2/10 | independent recompute (official `acc_at_k`) | 4/10, 4/10, 2/10 | PASS |
| 33 | P5 calls | 402 | `usage_ledger_final.jsonl` | 402 rows | PASS |
| 34 | P5 total tokens | 32.8M | ledger sum | 32,831,774 | PASS |
| 35 | P5 cost | ~$9.93 normalized | ledger × frozen pricing | $9.928811 | PASS |
| 36 | Mean tokens/task | Full 13,362 / Sparse 5,530 / Loc 3,283,177 | P1 metrics + ledger / 10 | 13,362.3 / 5,529.5 / 3,283,177.4 | PASS |
| 37 | Mean cost/task | 0.00992 / 0.00208 / 0.99288 | same | 0.009921 / 0.002078 / 0.992881 | PASS |
| 38 | Token ratios | 246× / 594× | 3,283,177/13,362 / 3,283,177/5,530 | 245.7× / 593.8× | PASS |
| 39 | Cost ratios | 100× / 478× | 0.99288/0.00992 / 0.99288/0.00208 | 100.1× / 477.8× | PASS |
| 40 | Pinned upstream LocAgent | 4935b557326c154bad8e8dcf3747cc8d32d1f387 | `reports/LOCAGENT_P5A_READINESS.md` + args.json | exact match | PASS |
| 41 | Provider wording | OpenRouter-routed, not proven per call | ledger provider=openrouter; Venice+DeepInfra in logs | supported | PASS |
| 42 | Corpus | 40 cases, TRAIN 24 / VAL 6 / HELD_OUT 10 | `benchmark_data/real_commit_impact_v1/split_freeze.json` | 24/6/10 | PASS |
| 43 | Leakage barrier / 92 excluded | 92 leaked ineligible | M4A-2 closure report | 92 excluded | PASS |

## Independent recomputation basis

All pooled P/R/F1/FNR and native Acc@K values were recomputed from
`merged_loc_outputs_mrr.jsonl` + candidate universes + observed change-set
proxies in a standalone script (`C:\Users\Ahmed\AppData\Local\Temp\opencode\p5_independent_recompute.py`),
independent of the tracked scorer, with identical results.

## Adversarial checks

- Item-hit sums 4/8/9 are NOT reported as Acc@K (official metric = 4/10,
  4/10, 2/10). PASS.
- No claim that all five empty LocAgent tasks timed out. PASS.
- No unqualified per-call DeepInfra pin. PASS.
- No comparison of published LocAgent Acc@5 0.90 with our F1. PASS.
- Efficiency ratios use one denominator (mean per execution/task). PASS.
- No mixed 30-cell / 10-execution validity column. PASS.
- CI crossing zero is phrased as "no clear detected difference", not
  equivalence. PASS.
- High FNR is framed as a weakness, not a success. PASS.
- M1/P1/P5 tables use observed change-set proxy wording. PASS.