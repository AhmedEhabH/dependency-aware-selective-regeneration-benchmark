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