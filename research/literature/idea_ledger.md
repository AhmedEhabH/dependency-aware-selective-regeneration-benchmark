# Idea Ledger — Living Systematic Review (V1)

**Status:** SEEDED 2026-09-16. Every entry records an idea and its disposition
(what we should TEST vs what is a monitor-only threat vs what is disambiguated
for the thesis). Dispositions are updated only by explicit decisions.

Legend for `disposition`:
- **TEST** — candidate idea to test in Omission-Risk Feature Study v1
  (TRAIN/VALIDATION only).
- **WATCH** — monitor; do not test now.
- **BOUNDARY** — outside localization-only scope; requires a future
  regeneration/verification milestone.

---

## I1 — K as an operating-point decision (TEST)
**Source:** adaptive-k (cross-domain) + Protocol-A finding (BM25@3 precision
point vs BM25@10 recall point; K = operating-point curve).
**Idea:** model the omission-risk gate as a K/routing decision: keep cheap
first-pass K small for low-risk, escalate (more K or verification) for
high-risk. Feature candidates: predicted write-set size, VALIDATE count,
action-distribution entropy, lexical-retrieval disagreement, graph frontier
size.
**Disposition:** TEST in Omission-Risk Feature Study v1.

## I2 — Manifest-as-repo-map features (TEST)
**Source:** ZeroRepO (repo map / manifest-first).
**Idea:** candidate-universe manifest statistics (module structure, density,
namespace breadth) as omission-risk features; also cheap BM25-over-universe as
a disagreement signal with the first pass.
**Disposition:** TEST (features only; no new model calls).

## I3 — Change-propagation as a cheap graph alternative (TEST)
**Source:** RIPPLE / change-impact analysis.
**Idea:** replace/extend B3 graph expansion with a change-propagation-style
closure over the parent-only dependency graph; measure whether closure
outperforms 1-hop expansion on TRAIN/VALIDATION.
**Disposition:** TEST (zero-LLM; reuse frozen graph).

## I4 — Localization-first vs agentic escalation boundary (WATCH)
**Source:** Agentless, CodePlan, AutoCodeRover.
**Idea:** 'no agent loop' localization-first is competitive; our sparse
first-pass + selective verification is the same philosophy with an explicit
budget. Monitor these as the 'strong baseline' family for a future fresh
confirmatory protocol.
**Disposition:** WATCH (no new runs now; fair-comparison boundary must hold).

## I5 — Graph neighborhood features for risk (TEST)
**Source:** GraphLocator, RepoGraph.
**Idea:** seed/frontier size, reachable zone, cross-component counts as
omission-risk features (post-first-pass, hidden-gold-free).
**Disposition:** TEST in Omission-Risk Feature Study v1.

## I6 — Risk-gated escalation operating point (TEST)
**Source:** AB-RAG / adaptive RAG (cross-domain).
**Idea:** AUROC/AUPRC, risk-coverage curve, escalation rate, FN recovery rate,
cost-per-recovered-FN as routing metrics.
**Disposition:** TEST (metrics registered in the omission-risk protocol draft;
no detector trained now).

## I7 — LocAgent as the expensive verifier (WATCH)
**Source:** LocAgent (direct shared-protocol evidence).
**Idea:** LocAgent is the natural expensive verifier for selective escalation;
its 50% empty rate + high cost argue for bounded invocation.
**Disposition:** WATCH. No LocAgent scientific calls in this milestone.

---

## Matrix integrity rule
Rows in `research/literature/review_matrix.csv` marked `SEEDED - verify
primary source` must be verified against the primary source before any thesis
claim relies on them. LocAgent is the only VERIFIED row (direct evidence).

---

## 2026-09-16 (post-feature-study) verification update

Priority-row primary-source verification completed (arXiv API / Crossref / ACM):
**VERIFIED**: Agentless (arXiv 2407.01489), CodePlan (FSE 2024,
DOI 10.1145/3643757), RepoCoder (EMNLP 2023, arXiv 2303.12570), RepoGraph
(ICLR 2025, arXiv 2410.14684), AutoCodeRover (ISSTA 2024,
DOI 10.1145/3650212.3680384), GraphLocator (FSE 2026, arXiv 2512.22469,
DOI 10.1145/3797079), RPG/ZeroRepo (ICLR 2026, arXiv 2509.16198), and the
**Shichao Zhang KNN line** (Challenges in KNN, TKDE 2022; One-step Computation,
TKDE 2021; Reachable Distance, TKDE 2022; Cost-sensitive KNN, Neurocomputing
2020; Adaptive kNN graph, arXiv 2601.16509).
**SEEDED (corrected)**: RIPPLE = classical ripple-effect/change-propagation line
(no canonical single system); Repository Memory = RepoCoder/RepoAgent mapping;
Adaptive-k = cross-domain pattern.

### Shichao Zhang / adaptive-computation principles (extracted, primary-verified)
1. **Query-specific neighborhood/budget** — K as a query-dependent decision
   (Challenges in KNN; Adaptive kNN graph).
2. **Confidence of approximate answers** — reliability of cheap/approximate
   answers must be quantified before trusting them.
3. **Move reusable work offline** — one-step computation / precomputed voting
   (HNSW + training-phase neighbor/weight assignment) converts lazy per-query
   search into offline work; the analogue is pre-indexing the candidate
   universe for the cheap first pass.
4. **Cost-sensitive decision making** — Cost-sensitive KNN (Neurocomputing
   2020): the decision rule must weight misclassification cost; the analogue
   is our C_FN/C_VERIFY escalation rule.
5. **Joint candidate-count/candidate-selection** — One-step KNN jointly sets K
   and selects neighbors via group lasso; the analogue (joint first-pass depth
   and candidate selection) is **TEST-LATER**, NOT implemented in this block.

### Corrections to previously seeded rows (2026-09-16)
- GraphLocator is **LLM-based causal-issue-graph reasoning** (FSE 2026), not
  static suspiciousness propagation.
- RepoGraph is **ICLR 2025**, not ICSE 2024.
- RepoCoder is **EMNLP 2023** (arXiv 2303.12570), not arXiv 2403.12595.
- AutoCodeRover is **ISSTA 2024**, not a preprint.
- RPG/ZeroRepo is **repository generation** (ICLR 2026, RepoCraft), not
  zero-shot repo-QA retrieval; the I2 'manifest-as-repo-map' idea is retained
  as a design pattern but its attribution to this paper is removed.

### New dispositions from Omission-Risk Feature Study V1 (development evidence)
- **I8 (NEW, WATCH — UPDATED 2026-09-16 after the Sparse-v2-label run)**: Retrieval
  peakiness/confidence as an (inverse) omission-risk signal. On the deterministic
  first-pass label the direction was OPPOSITE to the pre-registered 'more
  confident = safer' assumption. On the REAL Sparse-v2 labels the
  retrieval-peakiness cluster (bm25_zero_count AUROC 0.837 direction-consistent,
  with bm25_nonzero_frac / bm25_relthresh_count) becomes the only 3/97 features
  above the random band — now CONSISTENT with the pre-registered direction
  (peaked/confident retrieval → more omissions) — but the count is still within
  the chance expectation (4.85). Hypothesis-generating only; NOT yet eligible
  for RiskScorer v1.
- **I9 (NEW, EXECUTED 2026-09-16)**: The registered Sparse-v2-label
  omission-risk study was executed via the approved DEVELOPMENT-INFERENCE
  protocol (90-cell Sparse-v2 run on TRAIN/VALIDATION; 90/90 valid; 490,747
  tokens / $0.184). Outcome: prevalence 86.7% (26/30, 4 negatives);
  class-balance gate FAILED → no multivariable RiskScorer; no reliable signal
  survives the random band; see
  reports/OMISSION_RISK_SPARSE_V2_INFERENCE_REPORT.md.
- **I6 disposition update**: risk-gated operating-point evaluation was
  executed on the deterministic first-pass label; single features were
  statistically indistinguishable from random (n=30), so no operating point was
  frozen.