# Current Numbers Cheatsheet (2026-09-19)

Exact values only. Definitions (used everywhere):

```
Precision  P   = TP / (TP + FP)          Recall  R  = TP / (TP + FN)
FNR           = FN / (TP + FN) = 1 - R
F1            = 2TP / (2TP + FP + FN)
Candidate Precision = correct recovered omitted positives / all accepted additions
ORR_i         = recovered initial FN_i / initial FN_i ;  Macro ORR = mean_i(ORR_i)
Paired bootstrap CI (task unit, >=10,000 resamples, fixed seed):
  Delta_b = Metric_new_b - Metric_base_b ;  CI95 = [Q2.5, Q97.5]
```

## Fixed baselines (DEV populations: djangoCMS n=174, Saleor n=149)

| Method @B=5 | Repo | ORR | P | R | F1 | FNR | candP | TP/FP/FN |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Sparse (no additions) | djangoCMS | — | 0.446 | 0.247 | 0.318 | 0.753 | — | 125/155/382 |
| Sparse | Saleor | — | 0.339 | 0.212 | 0.261 | 0.788 | — | 99/193/369 |
| Route-B composite | djangoCMS | 0.1633 | 0.1626 | 0.3688 | 0.2257 | 0.6312 | 0.0713 | 187/963/320 |
| Route-B | Saleor | 0.2369 | 0.1716 | 0.3803 | 0.2365 | 0.6197 | 0.1060 | 178/859/290 |
| BM25 | djangoCMS | 0.1606 | 0.1583 | 0.3590 | 0.2197 | 0.6410 | 0.0655 | 182/968/325 |
| BM25 | Saleor | 0.2335 | 0.1697 | 0.3761 | 0.2339 | 0.6239 | 0.1034 | 176/861/292 |

## SweRankEmbed-Small (DEV; EXTERNAL PRETRAINED DIAGNOSTIC BASELINE; SWERANK_EMBED_PASS)

Pinned revision `745d2a06103a66d3cfa600aa52fc0d3523010daa`; 0 API calls / $0;
49,705 units embedded once on CPU.

| @B=5 | Repo | ORR | P | R | F1 | FNR | candP | TP/FP/FN |
|---|---:|---:|---:|---:|---:|---:|---:|
| SweRankEmbed | djangoCMS | 0.2908 | 0.2017 | 0.4576 | 0.2800 | 0.5424 | 0.1230 | 232/918/275 |
| SweRankEmbed | Saleor | 0.3266 | 0.2093 | 0.4637 | 0.2884 | 0.5363 | 0.1584 | 217/820/251 |

Paired bootstrap CIs @B=5 (SweRank − Route-B; all exclude 0):

| Repo | Metric | Δ | CI95 |
|---|---:|---:|---:|
| djangoCMS | macro ORR | +0.1274 | [0.0684, 0.1880] |
| djangoCMS | final P | +0.0391 | [0.0202, 0.0586] |
| djangoCMS | final R | +0.0888 | [0.0463, 0.1329] |
| djangoCMS | final F1 | +0.0543 | [0.0283, 0.0811] |
| djangoCMS | final FNR | −0.0888 | [−0.1329, −0.0463] |
| djangoCMS | candP | +0.0517 | [0.0264, 0.0770] |
| Saleor | macro ORR | +0.0897 | [0.0242, 0.1578] |
| Saleor | final P | +0.0376 | [0.0174, 0.0588] |
| Saleor | final R | +0.0833 | [0.0398, 0.1263] |
| Saleor | final F1 | +0.0518 | [0.0243, 0.0800] |
| Saleor | final FNR | −0.0833 | [−0.1263, −0.0398] |
| Saleor | candP | +0.0523 | [0.0242, 0.0819] |

Efficiency: model load 17.6 s; materialize 901 s (one-time); corpus encode
23,908 s (one-time, 49,705 units); per-task scoring 32.4 s / 323 tasks
(~0.1 s/task after indexing). **Correction:** the earlier
`per_query_seconds_est` (74.1 s) mixed one-time index cost with query latency;
the marginal cached query+ranking latency is ~0.1 s/task (reported separately;
see `research/strong-localization-signal/swerank/efficiency.json`).

## Stage-4b precision-safe pilot @B=5 (frozen verdict: PRECISION_SAFE_ACCEPTANCE_FAIL)

| Repo | Arm A ORR / F1 / candP | Arm B ORR / F1 / candP | closure Δ (95% CI) |
|---|---:|---:|---:|
| djangoCMS (n=30) | 0.2225 / 0.2176 / 0.1406 | 0.1523 / 0.2604 / 0.2500 | ORR −0.0702 [−0.196, +0.034]; F1 +0.0427 [−0.013, +0.096]; P +0.0716 [0.009, 0.151] |
| Saleor (n=30) | 0.1278 / 0.1744 / 0.0882 | 0.2029 / 0.1972 / 0.1163 | ORR +0.0751 [0.004, 0.175]; F1 +0.0228 [−0.012, +0.060]; R +0.0392 [0.009, 0.076] |

Calls/cost: 357 calls / 176,060 tokens / $0.0648 / 718.8 s (Stage-4b pilot).

## Stage-4 bounded semantic pilot @B=5 (frozen verdict: BOUNDED_SEMANTIC_NEGATIVE_FROZEN)

300 calls / 106,325 tokens / $0.0444 / 553.6 s. djangoCMS ORR 0.111→0.250 but
F1 0.396→0.327; Saleor ORR 0.334→0.357 but F1 0.304→0.270.

## Qwen3 contamination bridge (technical stop; NO full run)

- Availability: `qwen/qwen3-embedding-8b` present in the embeddings catalog
  (33 models); pinned DeepInfra $0.01/M; expected full-run $0.2188 (ceiling
  $0.50).
- Determinism probe: max cosine drift ~1.0e-4; unit top-10 overlap 1.0; file
  B=5 set flipped 1/5 tasks → **STOP** (P73). Spend ~$0.023 (technical only).

## Historical confirmatory anchor (for context; sealed now)

djangoCMS Route-B confirmatory (2026-09-17): 80 tasks, 560 calls / 1,470,174
tokens / $0.5059; composite ORR B=5 0.165 vs analytic Random 0.028 (Δ +0.137,
CI [+0.075, +0.205]) → CONFIRMS. That split is permanently spent.

## Source JSONs

- `research/strong-localization-signal/swerank/{metrics,gate,efficiency}.json`
- `reports/stage4b_bootstrap_ci.json`
- `reports/precision_safe_acceptance_metrics.json`
- `research/bounded-semantic-expansion/*`
- `research/contamination-bridge/qwen_embed/{probe,stability}.json`