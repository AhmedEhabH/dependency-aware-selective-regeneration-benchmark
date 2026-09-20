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

## Qwen3 two-realization replication (2026-09-19; verdict: INDEPENDENT_DENSE_RETRIEVAL_REPLICATED)

P74 amendment: two complete independent realizations (A and B) replace the
bitwise-determinism requirement. Model `qwen/qwen3-embedding-8b` @ DeepInfra
$0.01/M (live-verified), fallback disabled. Full DEV population embedded twice
(49,703 units + 323 queries/realization). Actual: A $0.1971 / B $0.2188;
cumulative incl. ~$0.023 probes ≈ **$0.439 < $0.50**.

| @B=5 | Repo | Method | P | R | F1 | FNR | ORR | candP | TP/FP/FN |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen A (= B pooled) | djangoCMS | 0.1887 | 0.4280 | **0.2619** | 0.5720 | 0.2419 | 0.1057 | 217/933/290 |
| Qwen A (= B pooled) | Saleor | 0.1958 | 0.4338 | **0.2698** | 0.5662 | 0.2958 | 0.1396 | 203/834/265 |
| Route-B | djangoCMS | 0.1626 | 0.3688 | 0.2257 | 0.6312 | 0.1633 | 0.0713 | 187/963/320 |
| Route-B | Saleor | 0.1716 | 0.3803 | 0.2365 | 0.6197 | 0.2369 | 0.1060 | 178/859/290 |

A-vs-B (B=5): exact same set 97.21%; mean Jaccard 0.9907 (median 1.0,
min 0.6667); 9 one-file flips all FP-for-FP (pooled metrics identical).
CIs (Qwen − RouteB) exclude zero for file-level P/R/F1/FNR on both repos both
realizations (djangoCMS F1 +0.0362 [0.0134, 0.0592]; Saleor +0.0333
[0.0042, 0.0616]). Saleor macro ORR CI crosses zero (diagnostic).
**NO OVERCLAIM:** Qwen beats Route-B (dense-ranking/recovery) but does NOT beat
Sparse final-set F1 (0.318/0.261) and does NOT replace SweRankEmbed-Small
(0.280/0.288). Source:
`research/contamination-bridge/qwen_embed/two_realization_metrics.json`,
`reports/QWEN3_TWO_REALIZATION_REPLICATION_REPORT_2026-09-19.md`.

## Set-selection diagnosis (POST-HOC DEV; verified from artifacts)

SweRank exact-rank omitted-positive hit rates (FN hits at rank k / n_tasks):
djangoCMS 0.241/0.132/0.109; Saleor 0.262/0.174/0.128 (ranks 1/2/3). Mean
|Sparse| 1.61/1.96; mean |proxy changed set| 2.91/3.14; Sparse empty 53/174
and 41/149. Frequencies, NOT calibrated probabilities.

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

## PARENT-ONLY REPOSITORY MEMORY RESCUE V2 (2026-09-20; frozen negative PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL; ZERO API)

Candidate universe = Sparse ∪ Qwen dense top-20 ∪ memory candidates
(top-10 structural co-change Jaccard support≥2 ∪ top-10 episodic BM25).
Features = 11 (7 V1 + cochange_sparse + cochange_top1 +
log_history_change_count + episode_similarity). Model/CV/threshold EXACTLY V1.

### Final P/R/F1/FNR (realization A; primary baseline Sparse)

| Repo | Sparse TP/FP/FN (F1) | V1 (F1) | V2 TP/FP/FN (F1) | Delta F1 (95% CI) | gate B |
|---|---:|---:|---:|---:|---:|
| djangoCMS | 125/155/382 (0.3177) | 140/191/367 (0.3341) | 152/222/355 (0.3451) | +0.0274 [−0.0102, +0.0636] | FAIL (crosses 0) |
| Saleor | 99/193/369 (0.2605) | 147/261/321 (0.3356) | 158/283/310 (0.3476) | +0.0871 [+0.0515, +0.1229] | PASS |

V2 Delta P: djangoCMS −0.0400 [−0.0843, +0.0036]; Saleor +0.0192 [−0.0348, +0.0657].
V2 Delta R: djangoCMS +0.0533 [+0.0148, +0.0884]; Saleor +0.1261 [+0.0896, +0.1648].
V2 Delta FNR: djangoCMS −0.0533 [−0.0886, −0.0156]; Saleor −0.1261 [−0.1639, −0.0902].

Realization B (same frozen pipeline): 99.07% exact same selected set, mean
Jaccard 0.9964; djangoCMS F1 0.3451 (identical), Saleor 0.3495; verdict SAME
(FAIL).

### Deep dense misses + coverage (descriptive, pre-model)

- DEEP_DENSE_MISS (V1 FN outside Sparse∪dense-top-20): djangoCMS 199 / Saleor 177;
  median dense rank 62 / 70.
- Memory candidate set recovery: union 43/199 (0.216) / 48/177 (0.271);
  structural-only 14/20; episodic-only 23/24; both 6/4; unrecovered 156/129.
- Sparse-empty recovery: 22/105 (0.210) / 16/69 (0.232).
- Baselines (same budget): popularity 41 (0.206) / 18 (0.102); random
  (seed 20260920, 1000 resamples) 11.1 (0.056) / 2.45 (0.014).
- Dependency-cluster diagnostic (oracle-style, NOT features):
  A 109/130; B 25/49; C 56/76.

### Error decomposition (A) — ADD/KEEP/DROP

| Repo | TP retained | TP dropped | FP dropped | FP retained | added (dense/struct/epis/multi) | new FP |
|---|---:|---:|---:|---:|---:|---:|
| djangoCMS | 110 | 15 | 49 | 106 | 42 (0/8/6/28) | 116 |
| Saleor | 94 | 5 | 65 | 128 | 64 (4/20/12/28) | 155 |

Remaining FN: djangoCMS not-generated 156 / rejected 184 / Sparse-TP-dropped 15;
Saleor 129/176/5.

### Set sizes + sparse-empty + intent (A)

- Policy mean |set| 2.15 / 2.96 (Sparse 1.61 / 1.96); empty-policy 37 / 10
  (empty-Sparse 53 / 41).
- Sparse-empty tasks: djangoCMS (n=53) P 0.208/R 0.036/F1 0.062/FNR 0.964;
  Saleor (n=41) P 0.333/R 0.194/F1 0.245/FNR 0.806.
- Intent buckets (descriptive): djangoCMS <=6 F1 0.209 / 7-15 0.376 / >15 0.432;
  Saleor <=6 0.276 / 7-15 0.286 / >15 0.402.

### Efficiency

0 API calls / $0.00; history build ≈ 183 s one-time (index 7.4 MB + 10.2 MB +
bundles 15.8 MB on D:, outside Git); classifier ≈ 25–40 s/realization;
deterministic rerun identical (SHA 4e2c880…); audit 23/23; unit tests 36/36.

### Cancelled

`CALIBRATED_SET_SELECTION_V2_FULL_UNIVERSE` = `FULL_UNIVERSE_V2_CANCELLED_AS_
NON_BINDING_ABLATION` (V1 selected non-Sparse only at ranks 1-4 = 172/93/20/3;
max non-Sparse prob 0.188 @5-20 / 0.065 @15-20 < all thresholds 0.17-0.21).
## STAGE5_V2_FINAL (2026-09-20; untouched confirmatory; one-shot; frozen negative)

Population: dc RESERVE 59 + Saleor INTERNAL_TEST 80 = 139. Paid $0.544067.
Verdict: `STAGE5_V2_FINAL_CONFIRMATION_FAIL`; `IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED`.

| repo | n | Sparse F1 | V2 F1 | Delta F1 |
|---|---:|---:|---:|---:|
| djangoCMS | 59 | 0.3028 | 0.2410 | −0.0618 |
| Saleor | 80 | 0.2744 | 0.2174 | −0.0570 |
| POOLED stratified | 139 | 0.2857 | 0.2269 | **−0.0588 CI [−0.1119,−0.0084]** |

Criteria: A FAIL (CI excludes zero, negative); B FAIL (both repos negative).
Sparse is more precise AND more sensitive than V2 on untouched data.
V2 Acc@1/3/5 (139): 0.2374/0.1223/0.1223; Hit@5 0.4748 (descriptive).
