# Qwen3 Two-Realization Replication Report (2026-09-19)

**Date:** 2026-09-19
**Mission:** QWEN3_TWO_REALIZATION_REPLICATION_2026-09-19 (T3 scientific
continuation of the contamination-robustness bridge line).
**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731
**Model/provider (frozen):** `qwen/qwen3-embedding-8b` @ **DeepInfra**,
$0.01 / 1M prompt tokens (live price re-verified before call 1), context
32,768, fallback disabled.
**Verdict:** **`INDEPENDENT_DENSE_RETRIEVAL_REPLICATED`** — realizations A and B
BOTH pass the frozen replication gate on djangoCMS AND Saleor at B=5.
**Sealed sets:** untouched. **Stage 5:** NOT executed. **Calibrated set
selection:** NOT executed (draft only).

---

## 1. Verdict summary

| Realization | djangoCMS gate @B=5 | Saleor gate @B=5 |
|---|---|---|
| A | PASS | PASS |
| B | PASS | PASS |

**`INDEPENDENT_DENSE_RETRIEVAL_REPLICATED`** (requires A AND B both pass on
both repos — satisfied; no cherry-picking).

## 2. Actual usage / budget

| Realization | Requests* | Prompt tokens* | Cost (realization) | Cumulative incl. prior probes | Ceiling |
|---|---:|---:|---:|---:|---:|
| A | 193 (last process) | 5,138,756 (last process) | **$0.1971** | $0.2201 | $0.50 |
| B | 71 (last process) | 1,700,683 (last process) | **$0.2188** | $0.2418 | $0.50 |
| **Total A+B** | — | — | **$0.4159** | **$0.4390** | **$0.50** |

*Ledger rows report the final process's client ledger; the authoritative
per-realization cost is the resume-safe cumulative spend
(`E:\opencode\qwen3-embed-cache-2026-09-19\realization_{A,B}\cumulative_spend.json`):
A = $0.19708686, B = $0.21882526. Realization B's billed tokens
(~21,882,526) match the frozen estimate (21,882,529) almost exactly, which
independently validates the estimate. Total cumulative Qwen bridge spend
(prior probes ~$0.023 + A + B) ≈ **$0.439 < $0.50 ceiling**. No permanent
failure on either realization (final process failures = 0/0).

Wall time: A ≈ 3,061 s final process (cumulative across 4 resumed processes
much larger due to the provider's ~4s-16s per-request latency); B final
process 1,134 s. Wall ceiling extended to 300 min per realization by
append-only P76 (cost ceiling remained the hard stop).

## 3. Metrics @B=5 (pooled file-level; per realization)

| Realization | Repo | Method | P | R | F1 | FNR | macro ORR | candP | TP/FP/FN |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| A | djangoCMS | Qwen A | 0.1887 | 0.4280 | **0.2619** | 0.5720 | 0.2419 | 0.1057 | 217/933/290 |
| A | djangoCMS | Route-B | 0.1626 | 0.3688 | 0.2257 | 0.6312 | 0.1633 | 0.0713 | 187/963/320 |
| A | djangoCMS | BM25 | 0.1583 | 0.3590 | 0.2197 | 0.6410 | 0.1606 | 0.0655 | 182/968/325 |
| A | Saleor | Qwen A | 0.1958 | 0.4338 | **0.2698** | 0.5662 | 0.2958 | 0.1396 | 203/834/265 |
| A | Saleor | Route-B | 0.1716 | 0.3803 | 0.2365 | 0.6197 | 0.2369 | 0.1060 | 178/859/290 |
| A | Saleor | BM25 | 0.1697 | 0.3761 | 0.2339 | 0.6239 | 0.2335 | 0.1034 | 176/861/292 |
| B | djangoCMS | Qwen B | 0.1887 | 0.4280 | **0.2619** | 0.5720 | 0.2419 | 0.1057 | 217/933/290 |
| B | djangoCMS | Route-B | 0.1626 | 0.3688 | 0.2257 | 0.6312 | 0.1633 | 0.0713 | 187/963/320 |
| B | Saleor | Qwen B | 0.1958 | 0.4338 | **0.2698** | 0.5662 | 0.2958 | 0.1396 | 203/834/265 |
| B | Saleor | Route-B | 0.1716 | 0.3803 | 0.2365 | 0.6197 | 0.2369 | 0.1060 | 178/859/290 |

**A-vs-B pooled metrics are IDENTICAL at B=5** (all deltas 0.0): the 9
one-file boundary flips each swapped one false positive for another false
positive, so pooled TP/FP/FN (and therefore every pooled metric) is unchanged.
This is strong evidence the scientific signal is robust to hosted numerical
noise (the ~1e-4 cosine drift that previously stopped the strict-determinism
bridge at P73).

## 4. Paired-bootstrap CIs @B=5 (Qwen − RouteB; task unit, 10,000 resamples, seed 20260919)

| Realization | Repo | Metric | Δ | 95% CI | excludes 0 |
|---|---:|---|---:|---:|---:|
| A | djangoCMS | macro ORR | +0.0786 | [+0.0253, +0.1320] | YES |
| A | djangoCMS | final P | +0.0261 | [+0.0096, +0.0429] | YES |
| A | djangoCMS | final R | +0.0592 | [+0.0219, +0.0972] | YES |
| A | djangoCMS | final F1 | +0.0362 | [+0.0134, +0.0592] | YES |
| A | djangoCMS | final FNR | −0.0592 | [−0.0972, −0.0219] | YES |
| A | djangoCMS | candP | +0.0345 | [+0.0126, +0.0563] | YES |
| A | Saleor | macro ORR | +0.0589 | [−0.0081, +0.1259] | no (crosses 0) |
| A | Saleor | final P | +0.0241 | [+0.0031, +0.0451] | YES |
| A | Saleor | final R | +0.0534 | [+0.0073, +0.0988] | YES |
| A | Saleor | final F1 | +0.0332 | [+0.0042, +0.0616] | YES |
| A | Saleor | final FNR | −0.0534 | [−0.0988, −0.0073] | YES |
| A | Saleor | candP | +0.0336 | [+0.0040, +0.0617] | YES |
| B | djangoCMS | macro ORR | +0.0786 | [+0.0253, +0.1320] | YES |
| B | djangoCMS | final F1 | +0.0362 | [+0.0134, +0.0592] | YES |
| B | Saleor | final F1 | +0.0332 | [+0.0042, +0.0616] | YES |
| B | Saleor | macro ORR | +0.0589 | [−0.0081, +0.1259] | no (crosses 0) |

The only CI that does not exclude zero is Saleor macro ORR (both
realizations), a mechanism diagnostic; the primary file-level F1/P/R/FNR CIs
exclude zero on BOTH repos in BOTH realizations. Note the gate's F1 condition
(A) uses the F1 CI lower bound, which excludes zero everywhere.

## 5. Frozen replication gate @B=5 (per realization, per repo)

| Realization | Repo | A: ΔF1>0 & CI↓>0 | B: ΔR≥−0.02 | C: ΔFNR≤+0.02 | D: ΔP≥−0.02 | E: ≥3/5 folds ΔF1≥0 | PASS |
|---|---:|---:|---:|---:|---:|---:|---:|
| A | djangoCMS | ✓ (0.0362; CI↓ 0.0134) | ✓ (+0.059) | ✓ (−0.059) | ✓ (+0.026) | ✓ 5/5 | **PASS** |
| A | Saleor | ✓ (0.0333; CI↓ 0.0042) | ✓ (+0.054) | ✓ (−0.054) | ✓ (+0.024) | ✓ 4/5 | **PASS** |
| B | djangoCMS | ✓ (0.0362; CI↓ 0.0134) | ✓ (+0.059) | ✓ (−0.059) | ✓ (+0.026) | ✓ 5/5 | **PASS** |
| B | Saleor | ✓ (0.0333; CI↓ 0.0042) | ✓ (+0.054) | ✓ (−0.054) | ✓ (+0.024) | ✓ 4/5 | **PASS** |

Fold deltas (F1, A): djangoCMS [0.141, 0.070, 0.082, 0.013, 0.087];
Saleor [0.232, 0.024, −0.112, 0.091, 0.060].
F: zero target leakage (labels joined only in the analyze step; the persisted
score artifact is label-free — audited). G: valid frozen provider/model
execution (pinned model, DeepInfra, no fallback; ≥95% valid requests after
permitted transport retries; 2 transient 429s were retried per policy and
resumed, 0 permanent failures). H: total cost ≈ $0.439 ≤ $0.50 ceiling.

## 6. Reproducibility analysis A vs B (independent of target correctness)

At B=5 across all 323 tasks:

| Statistic | Value |
|---|---|
| exact same selected-set task % | **97.21%** (314/323) |
| Jaccard overlap — mean | 0.9907 |
| Jaccard overlap — median | 1.0000 |
| Jaccard overlap — min | 0.6667 |
| Jaccard overlap — max | 1.0000 |
| one-file boundary flip tasks | **9** (4 djangoCMS + 5 Saleor) |
| metric delta A vs B (@B=5) | **0.0000 on every metric, both repos** |
| gate verdict change A vs B | **NO** (both PASS everywhere) |

Boundary-flip case ids:
`djangocms-rc-{47b63015feb1,95173e3367aa,95782b39ff54,d0f7b38f98b9}`,
`saleor-rc-{07df0e0ff24f,2da6d8c2d18f,c8a9f86f47e1,ce7d1e8d4d2b,ded69f9c7097}`.
Every flip swapped one false positive for another false positive (verified
against the proxy) — no TP/FN changed — which is why pooled metrics are
identical. **Scientific robustness to hosted numerical noise: high.**

## 7. Compare: Sparse vs Route-B vs SweRank vs Qwen A vs Qwen B (B=5 unless noted)

| Method @B=5 | djangoCMS F1 | Saleor F1 | label |
|---|---:|---:|---|
| Sparse (no additions) | 0.318 | 0.261 | frozen baseline (P≈0.446/0.339, R≈0.247/0.212) |
| Route-B composite | 0.226 | 0.237 | frozen historical primary comparator |
| SweRankEmbed-Small (137M, local) | 0.280 | 0.288 | frozen diagnostic PASS (provenance verdict C) |
| **Qwen A** | **0.262** | **0.270** | this mission |
| **Qwen B** | **0.262** | **0.270** | this mission |
| SweRank diagnostic B=1 | 0.348 | 0.304 | diagnostic only; NOT the primary point |

**Two questions, kept separate (no overclaiming):**
1. **Does Qwen improve dense ranking/recovery over Route-B?** YES — every
   metric improves at every B on both repos in both realizations, and all
   primary file-level CIs exclude zero (same direction as SweRank).
2. **Does the resulting final set beat Sparse itself?** **NO — the frozen
   SweRank evidence remains explicit and is NOT superseded.** Qwen F1
   (0.262/0.270) is above Route-B (0.226/0.237) but BELOW Sparse
   (0.318/0.261 on djangoCMS; Saleor 0.270 vs 0.261 is a wash and both are far
   below SweRank's 0.288). Qwen is a **dense-ranking / omission-recovery
   improvement over Route-B**, NOT final-set superiority, and NOT "the Sparse
   problem is solved". SweRankEmbed-Small remains the strongest frozen signal.

**Interpretation (per the frozen protocol's CASE A):** an independent
multilingual dense-embedding family (Qwen3-Embedding-8B, 8B, DeepInfra hosted)
reproduces the broad direction and magnitude of SweRankEmbed-Small's DEV
ranking/recovery gains under the identical parent-only protocol. This
strengthens the "dense retrieval as a mechanism" hypothesis and weakens (but
does NOT eliminate) the specialization/memorization hypothesis. It does NOT
prove either model has/hasn't seen djangoCMS or Saleor (provenance verdict C
unchanged), and it does NOT unlock Stage 5 by itself.

## 8. New set-selection diagnosis (POST-HOC DEVELOPMENT, verified from artifacts)

**SweRank exact-rank omitted-positive hit rates** (FN hits at exact rank k /
n_tasks; verified from `research/strong-localization-signal/swerank/task_rankings.json`):

| rank | djangoCMS | Saleor |
|---|---:|---:|
| 1 | 0.241 (42/174) | 0.262 (39/149) |
| 2 | 0.132 (23/174) | 0.174 (26/149) |
| 3 | 0.109 (19/174) | 0.128 (19/149) |
| 4 | 0.023 | 0.074 |
| 5 | 0.034 | 0.034 |

Distribution statistics (verified from `load_dev_tasks`):

| stat | djangoCMS | Saleor |
|---|---:|---:|
| mean \|Sparse\| | **1.61** | **1.96** |
| mean \|proxy changed set\| | **2.91** | **3.14** |
| Sparse empty | **53/174** | **41/149** |

**Interpretation:** the dense ranking signal is useful (rank-1 omitted
positives at 24–26% of tasks), but a fixed addition budget B=5 with an
increasing FP tail (candidate precision decays with rank) means a fixed-budget
policy adds mostly false positives after the first few ranks. These are rank
hit **frequencies**, NOT calibrated probabilities — they must not be treated
as such (see the Lipton note in §9).

## 9. Lipton et al. 2014 — F1-threshold theory (LITERATURE NOTE ONLY)

Zachary C. Lipton, Charles Elkan, Balakrishnan Narayanaswamy,
"Thresholding Classifiers to Maximize F1 Score," *Joint European Conference on
Machine Learning and Knowledge Discovery in Databases* (ECML-PKDD), 2014.

**Relevant result:** for WELL-CALIBRATED conditional probabilities, the
F1-optimal decision threshold is **t = F1* / 2**, where F1* is the maximum
achievable F1 of the classifier. This gives an actionable threshold without
cross-validated grid search, and the paper provides a batch-sensitive
(instance-count-aware) analogue for batch prediction.

**Use in this project (theory motivation ONLY):** this is the theoretical
basis for a FUTURE calibrated set-selection policy
(`CALIBRATED_SET_SELECTION_V1`, drafted, NOT executed). It is NOT applied here
because none of our quantities are calibrated conditional probabilities:
raw dense cosine scores are similarity scores (not probabilities); rank
numbers are ordinal; aggregate rank hit-rates are empirical frequencies over
tasks, not per-file probabilities. Applying `F1*/2` directly to any of these
would be invalid. The paper's batch-dependence caveat (the optimal threshold
also depends on how many files will be selected as a group) is acknowledged
and is exactly the ADD/DROP set-selection setting we must handle
calibrated-per-task, not with a single global threshold.

**Conclusion of this note:** the F1-threshold theorem motivates but does not
determine the future policy; calibration (grouped task-level out-of-fold
probabilities on DEV) must come first.

## 10. CALIBRATED_SET_SELECTION_V1 — DRAFT PREPARED, NOT EXECUTED

Prepared as a draft for the next DEVELOPMENT-only mission
(`docs/CALIBRATED_SET_SELECTION_V1_DRAFT.md`). Scope (frozen in the draft):
minimal interpretable feature set first — dense file score, dense rank, gap to
top-ranked score, in_sparse, |Sparse|; ONE model family (L2 logistic
regression); no feature shopping. Score Sparse + omitted files together;
grouped task-level out-of-fold probabilities on DEV; evaluate calibration;
derive the F1 threshold only inside training folds; apply to held-out folds;
permit ADD and DROP; freeze ONE final policy before Stage 5. Explicitly: NO
"minimum one file per task" constraint (not implied by the F1-threshold
theorem). Not executed in this mission.

## 11. Competitors — documented, NOT run

- **LocAgent:** published Acc@k is not directly comparable with our set-based
  P/R/F1 (different metric, protocol, and population). Documented; NOT run.
- **Agentless:** documented; NOT run.
- **Loc-Bench:** a future external-validity/comparability benchmark AFTER the
  final policy is frozen. NOT run.
- No large API budget is spent on a full competitor run before the method
  itself is frozen.

## 12. Storage discipline

- Embedding caches: `E:\opencode\qwen3-embed-cache-2026-09-19\realization_{A,B}\`
  (chunked float32 npy parts + index.json + cumulative_spend.json). NO raw
  embedding vectors committed to Git.
- Full-file-score artifacts (label-free, zstd Parquet):
  - `research/contamination-bridge/qwen_embed/realization_A/full_file_scores.parquet` (1.13 MB, 143,852 rows)
  - `research/contamination-bridge/qwen_embed/realization_B/full_file_scores.parquet` (1.13 MB, 143,852 rows)
  Columns: case_id, repository, parent_commit, file_path, dense_file_score,
  dense_rank, in_sparse, query_sha256, model_id, provider, realization_id.
  NO target labels. NO raw vectors.
- Per-realization task_rankings.json (top-10 ranked lists per method,
  0.51 MB each) + ledger.json; combined new tracked artifact total ≈ 3.3 MB.

## 13. What this does NOT mean

- NOT a claim that "the Sparse problem is solved" (Sparse F1 0.318/0.261
  still beats Qwen's final set; SweRank 0.280/0.288 remains the strongest).
- NOT a claim that Qwen/SweRank have or have not seen djangoCMS/Saleor
  (provenance verdict C unchanged).
- NOT a Stage-5 confirmatory claim; Stage 5 remains PAUSED and SEALED.
- NOT a claim that the rank hit-rates are calibrated probabilities.
- The prior strict-determinism finding (P73) remains a valid historical
  record; this mission's P74 amendment deliberately moved to a
  conclusion-reproducibility evaluation via two independent realizations.

## 14. Evidence paths

- `research/contamination-bridge/qwen_embed/realization_{A,B}/{task_rankings,ledger,full_file_scores}.json/parquet`
- `research/contamination-bridge/qwen_embed/two_realization_metrics.json`
- `reports/qwen3_two_realization_{gate,reproducibility,audit}.json`
- `reports/QWEN3_TWO_REALIZATION_REPLICATION_REPORT_2026-09-19.md` (this file)
- `docs/QWEN3_TWO_REALIZATION_REPLICATION_IMPACT_DECLARATION_2026-09-19.md`
- `DECISIONS.md` P74/P75/P76