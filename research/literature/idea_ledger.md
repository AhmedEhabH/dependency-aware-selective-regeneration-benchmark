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
- **I10 (NEW, Route B SUBSTRATE)**: candidate-level bounded omission
  verification. Given the negative task-level RiskScorer result (both v1 and
  V2), identify which omitted candidates deserve a second look using
  independent structural/history/retrieval evidence, and verify only those
  under a hard budget. Compare with always-verify and random matched-budget
  verification. Disposition: DESIGN/PROTOCOL (Route B); do not run a model
  until the V2 internal test is protected and gates pass.
- **I11 (IMPLEMENTED)**: classical/static CIA baseline V1 - BM25/path_token
  seeds -> 1-hop / 2-hop reverse-dependency closure over the parent-only
  graph; executed on 150 V2 development cases (zero LLM); GRAPH@K and BM25
  strongest, closure arms weaker; development evidence only
  (reports/CLASSICAL_CIA_BASELINE_V1_REPORT.md).
- **V2 development-inference result (2026-09-16)**: 431/450 cells (fail-closed
  token-ceiling stop), 144 V2 tasks, merged 174 tasks / 155 pos / 19 neg;
  v1 peakiness signal does NOT replicate in V2 (universe-size artifact); NO
  multivariable RiskScorer; Route B pivot.

- **djangoCMS INTERNAL_TEST confirmatory run (2026-09-17, CONFIRMS)**: 80
  tasks; 560 calls / 1,470,174 tokens / \.505917; 0 failures; composite ORR
  vs analytic Random B=5 0.165 vs 0.028 (delta +0.137, CI [+0.075,+0.205]);
  fixed Route-B CONFIRMED. Confirmatory test permanently used; never reused
  for P2 selection (reports/DJANGOCMS_ROUTE_B_CONFIRMATORY_RESULT.md).
- **P2 adaptive-budget program (2026-09-17, ADOPTED; DEVELOPMENT only)**:
  five-month (Nov 2026 - Mar 2027) program on djangoCMS DEV + Saleor DEV;
  Shichao-Zhang-inspired policies (Learning-k, cost-sensitive KNN, one-step,
  demand-driven kNN, adaptive-neighborhood) + systematic landscape of
  competing families (selective/abstention/learning-to-defer/cascade/optimal
  stopping/budgeted retrieval). 24-entry landscape CSV; common evaluation
  contract; at most 1-2 justified candidates on DEV only; Saleor INTERNAL_TEST
  sealed as possible future P2 confirmation (reports/P2_ALGORITHM_LANDSCAPE_2026-09.md,
  research/literature/p2_algorithm_landscape.csv,
  docs/P2_COMMON_EVALUATION_CONTRACT.md).
- **STRONG LOCALIZATION SIGNAL BRIDGE (2026-09-19, T3, ZERO API)**:
  Stage-4b statistical closure (task-paired bootstrap, 10k resamples, fixed
  seed 20260919; frozen verdict PRECISION_SAFE_ACCEPTANCE_FAIL unchanged;
  djangoCMS ORR-vs-F1 phenomenon explained by macro-vs-pooled weighting and
  M=1 verifier over-rejection) + `BOUNDED_CHEAP_SEMANTIC_CLOSED_FOR_NOW`
  (generic-Qwen prompt/verifier/threshold family closed) +
  `Salesforce/SweRankEmbed-Small` DEV evaluation on the FULL legal populations
  (djangocms 174 + saleor 149; pinned revision 745d2a06…; frozen MAX-file
  adapter; parent-only queries). Result: **SWERANK_EMBED_PASS** — every metric
  improves at every B on both repos; all paired-bootstrap 95% CIs exclude zero
  @B=5 (F1 +0.054 dc / +0.052 saleor vs frozen Route-B); 0 API calls / $0.
  Method frozen as the candidate-ranking signal; next step A (embed as
  replacement signal) chosen over B (SweRankLLM reranker — needs a budget).
  Labeled EXTERNAL PRETRAINED DIAGNOSTIC BASELINE
  (TRAINING_PROVENANCE_INSUFFICIENT_TO_RULE_OUT_OVERLAP). Repository-memory,
  cross-language (TS/Java/Go) and polyglot (grafana) readiness audited.
  Evidence: reports/STAGE4B_STATISTICAL_CLOSURE_2026-09-19.md,
  reports/SWERANK_EMBED_DEVELOPMENT_REPORT.md,
  research/strong-localization-signal/swerank/*.json,
  reports/STRONG_LOCALIZATION_COMPETITOR_REVIEW_2026-09-19.md,
  docs/SWERANK_EMBED_BASELINE_PROTOCOL_FROZEN.md.
