# Parent-Only Repository Memory Rescue V2 — Report (2026-09-20)

**Mission:** PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2
(HISTORY-AUGMENTED DEEP FALSE-NEGATIVE RECOVERY)
**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731
**Tier:** T3 · **API budget:** ZERO paid calls ($0.00) · **Sealed data:** untouched
**Primary score realization:** Qwen realization A; realization B = frozen robustness rerun
**Verdict:** `PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL`

> The primary gate fails on djangoCMS (criterion B: paired-bootstrap 95% CI for
> Delta F1 crosses zero) in BOTH realizations A and B; Saleor passes. Verdict
> agreement A/B is SAME (robust FAIL). The frozen negative is recorded:
> `PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL`.

---

## WHAT DID V1 TEACH US?

CALIBRATED_SET_SELECTION_V1 (`CALIBRATED_SET_SELECTION_V1_FAIL`, frozen
negative) taught us that a single minimal interpretable repository-independent
decision policy (L2-LR over 7 dense/sparse features, nested 5×5 CV, inner-OOF
F1 threshold, ADD/KEEP/DROP, no fixed B) improves the point F1 over Sparse on
BOTH repositories (djangoCMS 0.318 → 0.334; Saleor 0.261 → 0.336) but is NOT
statistically distinguishable from Sparse on djangoCMS (Delta-F1 CI
[−0.019, +0.053] crosses zero). The dominant remaining error source is
**candidate coverage**: 199 (djangoCMS) / 177 (Saleor) proxy positives are
NOT even in the V1 candidate universe (Sparse ∪ dense-top-20). Dense ranking
itself was already independently replicated (`INDEPENDENT_DENSE_RETRIEVAL_REPLICATED`,
SweRankEmbed-Small + Qwen3-Embedding-8B A/B), so the binding bottleneck is
DEEP FALSE-NEGATIVE RECOVERY — files that remain far below the useful
dense-score decision region.

## WHY FULL-UNIVERSE V2 WAS CANCELLED

`CALIBRATED_SET_SELECTION_V2_FULL_UNIVERSE` was cancelled BEFORE execution.
Verification from already-exposed V1 artifacts (no new model fit):

| V1 non-Sparse selection by dense rank | count |
|---|---:|
| rank 1 | 172 |
| rank 2 | 93 |
| rank 3 | 20 |
| rank 4 | 3 |
| ranks 5–20 | **0** |

Non-Sparse candidate pool rows at ranks 5–20: n = 4,981, selected = 0. The max
outer-OOF probability among non-Sparse candidates was 0.1880 at ranks 5–20
(p95 0.0886) and **0.0650** at ranks 15–20 (p95 0.0428) — while every one of
the five V1 inner-CV thresholds was **0.17–0.21**. The top-20 boundary was
therefore NEVER ACTIVE at the decision boundary.

Governance decision recorded:
`FULL_UNIVERSE_V2_CANCELLED_AS_NON_BINDING_ABLATION` — removing the top-20
boundary while preserving the same rank-monotone signal would be expected to
produce a near-null rerun and creates unnecessary forking-path risk. This is a
descriptive decision from exposed DEV/V1 artifacts, not a new experiment.

## WHAT IS A DEEP DENSE MISS?

`DEEP_DENSE_MISS` = a historical-proxy positive file that (a) remains a FALSE
NEGATIVE after V1 AND (b) was outside the V1 frozen candidate universe
(Sparse ∪ dense-top-20). Verified counts: **djangoCMS 199**, **Saleor 177**.
Their dense-rank distribution (median): djangoCMS 62 (mean 75.6, p25 37,
p75 100.5); Saleor 70 (mean 130.1, p25 42, p75 163). These files are
structurally "unreachable" to the frozen V1 policy — the dense rank did not
bring them into the ADD pool at all.

## WHAT DOES THE DEPENDENCY-CLUSTER DIAGNOSTIC SHOW?

Descriptive oracle-style diagnostic over DEEP_DENSE_MISS files using ONLY
parent-visible public dependency graphs (evaluation labels used ONLY for
retrospective headroom):

| Repo | A. direct relation to another proxy positive | B. adjacent to a V1 TP | C. within 2 hops of a V1 TP |
|---|---:|---:|---:|
| djangoCMS | 109 / 199 (0.548) | 25 (0.126) | 56 (0.281) |
| Saleor | 130 / 177 (0.735) | 49 (0.277) | 76 (0.429) |

Both repositories show a majority of deep misses have a DIRECT dependency
relation to another proxy positive from the same historical change; a smaller
fraction are adjacent to a V1 true positive. This confirms dependency
structure "contains" some deep misses — but these diagnostics are NOT used as
inference features.

## WHY DEPENDENCY LABEL DIAGNOSTICS ARE NOT INFERENCE FEATURES

"Another proxy positive" and "V1 true positive" are **oracle-style** concepts:
at inference time the proxy label is unknown, so a "direct relation to another
proxy positive" cannot be computed without the target. The diagnostics exist
to measure retrospective headroom, exactly as Oracle-Add ceilings. Per the
frozen mission, **NO graph features were added to V2** — V2 isolates
repository-history memory as the new orthogonal signal.

## WHY REPOSITORY HISTORY IS ORTHOGONAL

Dense retrieval scores the CURRENT code at the parent revision against the
intent; repository history scores the EVOLUTION of files (which files have
changed together and how past changes were described). A file with strong
historical coupling to the Sparse seed set, or whose past change descriptions
resemble the task intent, can be a strong localization candidate even when its
current-code cosine similarity is deep in the tail (median dense rank 62/70 for
deep misses). This is the repository-memory mechanism of
"Improving Code Localization with Repository Memory" (arXiv 2510.01003) —
**prior art, not claimed as novel** — reproduced here with a deterministic,
parent-only, zero-API generator.

## HOW CO-CHANGE MEMORY WORKS

For parent-visible production-changing commits (ancestors of P that touch at
least one legal production file):

- `C(f)` = commits touching f; `C(s)` = commits touching s; `C(f,s)` = both.
- `Jaccard(f,s) = C(f,s)/(C(f)+C(s)-C(f,s))`; **0 if `C(f,s) < 2`** (frozen
  support threshold 2, NOT swept).
- Inference-time seeds: (A) all Sparse-selected files; (B) the Qwen dense
  rank-1 file. NO target-label seeding.
- `cochange_sparse(f) = max Jaccard(f,s)` over Sparse (0 if Sparse empty);
  `cochange_top1(f) = Jaccard(f, rank1)`;
  `cochange_memory_score(f) = max(cochange_sparse, cochange_top1)`.

## HOW EPISODIC CHANGE MEMORY WORKS

Every parent-visible production-changing commit becomes a document
(subject + body; no web/API enrichment). Deterministic BM25 (the SAME Okapi
BM25 as the project's cheap baselines) over this historical change-text corpus
retrieves the top-10 episodes for the frozen task intent
(`EPISODIC_TOP_CHANGES = 10`, not swept). For a file f,
`episode_similarity(f)` = max normalized BM25 score among the retrieved
episodes that modified f (0 if none); `episode_hit_count(f)` is computed
descriptively but is NOT a model feature.

## HOW TEMPORAL LEAKAGE WAS PREVENTED

- History = `git rev-list <parent>` only: every memory commit is a provable
  ancestor of P. The target commit, all descendants, future commits, and
  future issue/PR metadata are structurally excluded.
- Construction **fails closed**: any ancestor commit missing from the local
  index aborts the task (visibility unprovable).
- Production-file filter is per-task against that task's frozen legal
  production universe; commits touching only excluded files never enter.
- Automated tests assert no future/target leakage and deterministic ancestry;
  the independent audit re-asserts the counts.

## DEEP-FN COVERAGE BEFORE MODELING

Coverage of the 199 / 177 DEEP_DENSE_MISS files by the FROZEN memory candidate
set (realization A; computed before/independent of the V2 classifier):

| Channel | djangoCMS | Saleor |
|---|---:|---:|
| structural only | 14 | 20 |
| episodic only | 23 | 24 |
| both | 6 | 4 |
| **union recovered** | **43 (0.216)** | **48 (0.271)** |
| unrecovered | 156 | 129 |

DeepFNRecovery on tasks where Sparse is empty: djangoCMS 22/105 (0.210);
Saleor 16/69 (0.232).

Mechanism baselines at the same candidate budget (top-10 non-sparse):
historical-popularity covers 41 (0.206) / 18 (0.102); seeded deterministic
random (seed 20260920, 1,000 resamples) covers 11.1 (0.056) / 2.45 (0.014).
The memory generator recovers more deep misses than popularity on Saleor and
far more than random on both. NO 15% pass/fail threshold exists; the
preregistered V2 continued regardless.

## RESULTS ON SPARSE-EMPTY TASKS

V2 policy metrics restricted to tasks where Sparse is empty (realization A):
djangoCMS (n=53): P 0.208 / R 0.036 / F1 0.062 / FNR 0.964;
Saleor (n=41): P 0.333 / R 0.194 / F1 0.245 / FNR 0.806. The empty-Sparse
final-policy emptiness falls from 53→37 (djangoCMS) and 41→10 (Saleor).

## INTENT-LENGTH STRATIFIED RESULTS

Pre-registered descriptive buckets (NOT a feature, NOT a gate):

| Repo | bucket | n | Sparse F1 | V2 F1 | Sparse R | V2 R |
|---|---:|---:|---:|---:|---:|---:|
| djangoCMS | <=6 | 70 | 0.2344 | 0.2094 | 0.1641 | 0.1487 |
| djangoCMS | 7-15 | 46 | 0.3162 | 0.3764 | 0.2606 | 0.3592 |
| djangoCMS | >15 | 58 | 0.4000 | 0.4324 | 0.3294 | 0.4235 |
| Saleor | <=6 | 37 | 0.1750 | 0.2755 | 0.1197 | 0.2308 |
| Saleor | 7-15 | 37 | 0.1842 | 0.2857 | 0.1386 | 0.2970 |
| Saleor | >15 | 75 | 0.3170 | 0.4016 | 0.2840 | 0.4040 |

Development evidence suggests localization quality is associated with intent
informativeness/length, particularly for short commit-message queries; this
requires untouched confirmation. This is hypothesis-generating analysis on
DEVELOPMENT only — NOT causal, NOT an information-theoretic impossibility.

## FINAL PRECISION / RECALL / F1 / FNR

Formulas: `P = TP/(TP+FP)`, `R = TP/(TP+FN)`, `FNR = FN/(TP+FN)`,
`F1 = 2TP/(2TP+FP+FN)`; `Delta = Metric_V2 - Metric_Sparse`; task-paired
bootstrap, 10,000 resamples, seed 20260920.

### djangoCMS (realization A)

| | Sparse | V1 | **V2** |
|---|---:|---:|---:|
| TP / FP / FN | 125/155/382 | 140/191/367 | **152/222/355** |
| Precision | 0.4464 | 0.4230 | **0.4064** (Δ −0.0400, CI [−0.0843, +0.0036]) |
| Recall | 0.2465 | 0.2761 | **0.2998** (Δ +0.0533, CI [+0.0148, +0.0884]) |
| F1 | 0.3177 | 0.3341 | **0.3451** (Δ +0.0274, CI [−0.0102, +0.0636]) |
| FNR | 0.7535 | 0.7239 | **0.7002** (Δ −0.0533, CI [−0.0886, −0.0156]) |

### Saleor (realization A)

| | Sparse | V1 | **V2** |
|---|---:|---:|---:|
| TP / FP / FN | 99/193/369 | 147/261/321 | **158/283/310** |
| Precision | 0.3390 | 0.3603 | **0.3583** (Δ +0.0192, CI [−0.0348, +0.0657]) |
| Recall | 0.2115 | 0.3141 | **0.3376** (Δ +0.1261, CI [+0.0896, +0.1648]) |
| F1 | 0.2605 | 0.3356 | **0.3476** (Δ +0.0871, CI [+0.0515, +0.1229]) |
| FNR | 0.7885 | 0.6859 | **0.6624** (Δ −0.1261, CI [−0.1639, −0.0902]) |

Realization B (same frozen pipeline): djangoCMS F1 0.3451 (identical);
Saleor F1 0.3495. Exact selected-set agreement A/B 99.07%; mean task Jaccard
0.9964 (median 1.0); verdict agreement SAME (both FAIL).

### Gate (both realizations)

| Criterion | djangoCMS | Saleor |
|---|---:|---:|
| A: F1_V2 > F1_Sparse | True | True |
| B: CI lower(Delta F1) > 0 | **False** | True |
| C: R_V2 >= R_Sparse | True | True |
| D: FNR_V2 <= FNR_Sparse | True | True |
| E: >= 3/5 folds Delta F1 >= 0 | True (3/5) | True (5/5) |
| F: zero target leakage | PASS (tests + audit) | PASS |
| G: deterministic rerun | True | True |

`PARETO_SUCCESS` = FALSE (Saleor Pareto-only). **Primary gate FAIL on
djangoCMS (criterion B) in both realizations → `PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL`.**

## ADD / KEEP / DROP DECOMPOSITION

| Repo | Sparse TP retained | Sparse TP dropped | Sparse FP dropped | Sparse FP retained |
|---|---:|---:|---:|---:|
| djangoCMS | 110 | 15 | 49 | 106 |
| Saleor | 94 | 5 | 65 | 128 |

Omitted positives ADDED by channel / new FP ADDED by channel:

| Repo | dense-only | structural | episodic | multiple-memory |
|---|---:|---:|---:|---:|
| djangoCMS added | 0 | 8 | 6 | 28 |
| djangoCMS new FP | 0 | 31 | 37 | 48 |
| Saleor added | 4 | 20 | 12 | 28 |
| Saleor new FP | 22 | 50 | 45 | 38 |

Remaining FN classification: djangoCMS not-generated 156 / rejected 184 /
Sparse-TP-dropped 15; Saleor not-generated 129 / rejected 176 /
Sparse-TP-dropped 5.

## WHAT HISTORY RESCUED THAT DENSE RANKING MISSED

- On djangoCMS, **all 42 added omitted positives** came from history-involved
  candidates (structural / episodic / multiple-memory); dense-only candidates
  contributed 0.
- On Saleor, 60/64 added positives came from history-involved candidates.
- The memory generator recovered 21.6% (djangoCMS) / 27.1% (Saleor) of the
  DEEP_DENSE_MISS files — files that the dense top-20 could not reach — versus
  20.6%/10.2% for historical popularity and 5.6%/1.4% for random.
- Structural candidates alone added 8/20 positives; episodic alone 6/12; the
  overlap (multiple-memory) 28/28 — both channels carry complementary signal.

## WHAT REMAINS UNREACHABLE

156 (djangoCMS) / 129 (Saleor) deep misses remain outside the V2 candidate
universe ("not-generated"), and 184/176 are generated but rejected by the
learned threshold. The dependency-cluster diagnostic shows most deep misses
have a direct relation to another proxy positive (109/199; 130/177), so
dependency-aware generation could theoretically reach them — but that would
require oracle-style seeding and is outside this mission. The final-set policy
problem remains unsolved on DEV: history improves coverage and recall but does
not (yet) make the djangoCMS final-set F1 statistically distinguishable from
Sparse under the frozen gate.

## COST / LATENCY / STORAGE

- API calls: **0**; API cost: **$0.00** (no model/embedding/API used).
- History extraction/build (one-time, first run): djangoCMS 2.6 s index +
  52 s tasks; Saleor 1.7 s index + 73 s tasks; total ≈ 183 s wall.
- History index size (D:, outside Git): djangoCMS 7.4 MB + Saleor 10.2 MB
  (commit index); memory bundles 15.8 MB (co-change + episodic features).
- Per-task memory retrieval: cached; sub-second at run time.
- Classifier: full nested 5×5 CV over 323 tasks ≈ 25–40 s per realization
  (incl. feature building); deterministic rerun identical.
- Peak RAM: not instrumented beyond the normal pandas/scikit workload.
- Disk (repo): research/memory-rescue-v2 artifacts ≈ small (JSON/parquet);
  D: cache 33.5 MB, excluded from Git/export.

## VERDICT

`PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL` (frozen negative; both
realizations A and B fail the SAME criterion). Repository-history memory IS a
real, parent-visible, zero-API signal that recovers deep dense misses at the
candidate level, but the unchanged final-set gate still fails on djangoCMS:
the Delta-F1 paired-bootstrap CI crosses zero in both realizations.

## WHAT THIS RESULT MEANS

- Parent-visible repository history is ORTHOGONAL to current-code dense
  similarity: it brings deep dense misses (median dense rank 62/70) into the
  candidate pool that dense ranking alone cannot reach.
- The memory generator is a valid descriptive mechanism (better than
  popularity on Saleor, much better than random on both) and attacks the
  deep-FN bottleneck at the candidate level (21.6% / 27.1% coverage).
- V2 point F1 improves over both Sparse and V1 on both repositories
  (djangoCMS 0.318→0.334→0.345; Saleor 0.261→0.336→0.348).
- The result is reproducible and leakage-free (23/23 independent audit).

## WHAT IT DOES NOT MEAN

- It does NOT mean the final-set policy problem is solved on DEV (the frozen
  gate fails on djangoCMS).
- It does NOT claim repository-memory novelty (repository-memory /
  co-change / history retrieval is prior art, e.g. arXiv 2510.01003).
- It does NOT unlock Stage 5, and does NOT claim clean unseen
  pretrained-model generalization.
- It does NOT mean intent-information limits are causal/impossible (short
  intent buckets show the worst localization, descriptively, on DEV).
- It does NOT justify a V3: no automatic V3; a V3 would require a NEW mission
  and NEW frozen hypothesis.

## STAGE-5 CONSEQUENCE

Stage 5 remains **PAUSED and SEALED** (`FINAL_POLICY_NOT_FROZEN`). The
dense-mechanism replication (`INDEPENDENT_DENSE_RETRIEVAL_REPLICATED`) removed
the non-replication blocker, but a frozen successful final-set policy does not
exist. Sealed sets (djangoCMS RESERVE 59, Saleor INTERNAL_TEST 80, Saleor
RESERVE 1086; spent djangoCMS INTERNAL_TEST) are untouched. No Stage-5
preregistration packet is produced (the scientific decision is FAIL).

## Evidence

Machine-readable outputs under `research/memory-rescue-v2/`; frozen config in
`reports/memory_rescue_v2_freeze.json`; governance in `DECISIONS.md` P80/P81;
independent audit 23/23 PASS (`reports/memory_rescue_v2_audit.json`);
diagnostics `reports/PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_DIAGNOSTICS_2026-09-20.md`.