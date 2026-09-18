# Focused Literature Check — Bidirectional / Set-Repair Novelty

**Date:** 2026-09-18
**Tier:** T3 (ZERO API except arXiv abstract lookups where already present in
the ledger)
**Mission:** OPENCODE_ORACLE_GAP_BIDIRECTIONAL_REPAIR_MISSION_2026-09-18
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731

**Scope:** focused review, not a broad sweep, on the specific idea of **bounded
ADD + DROP correction around an LLM/sparse first-pass set for repository file
localization**, and its nearest relatives.

---

## 1. Question

Has prior work explicitly treated repository file localization as a bounded
ADD+DROP correction around an LLM/sparse first-pass set, i.e. a "set-repair"
step that both adds high-suspicion omitted files AND drops low-support selected
files under one review budget?

## 2. Classification of related work

| Work | Theme | Class |
|---|---|---|
| LocAgent (2025) | Agentic repo traversal; no explicit ADD/DROP set repair | DIRECT_COMPETITOR (already in ledger P2-020) |
| GraphLocator (FSE 2026) | Graph-based localization; no bounded set-repair step | DIRECT_COMPETITOR (ledger P2-019) |
| Change-Patterns Mapping (TSE 2022) | CIA change patterns; no ADD/DROP repair | DIRECT_COMPETITOR (ledger P2-018) |
| Repoformer / FastCoder (2024-25) | Selective retrieval + verifier on top-k; ADD-only reconsideration of a rejected residual | CLOSE_ANALOGUE (ledger P2-021) |
| Agentless (2024) | Repo-level localization then patch; no DROP queue | DIRECT_COMPETITOR (ledger P2-022) |
| SelectiveNet / selective prediction (2019/2010) | Reject/abstain on individual predictions; one-sided | ALGORITHMIC_INSPIRATION (ledger P2-010/P2-039) |
| Budgeted retrieval / cost-sensitive ranking | Top-k selection under budget; ADD-only | CLOSE_ANALOGUE (ledger P2-014) |
| Active search / value-of-information | Sequential query decisions; not set repair | CLOSE_ANALOGUE (ledger P2-015/P2-028) |
| Precision-recall repair / set prediction under bounded review | N/A — no directly verified primary source found in the current ledger | (not claimed) |

## 3. Assessment

- **Explicit "bounded ADD+DROP set repair" around a first-pass localization
  set:** **No verified primary source in the current ledger was found.** The
  closest families are (a) selective verification/reranking of a rejected
  residual (ADD-only; e.g. Repoformer/FastCoder-style verifier on top-k) and
  (b) selective prediction with abstention (one-sided rejection). A DROP queue
  that prunes the *selected* set with the same review budget as the ADD queue is
  not represented in the current literature ledger.
- **Claim discipline:** this mission makes **NO novelty claim**. Absence from
  the current 39-entry ledger is not proof of absence in the wider literature.
  A proper novelty search (databases: ACL, EMNLP, ICLR, ICML, TSE, TOSEM, IEEE
  Software) would be required before any novelty statement. The internal label
  `BBSR` is explicitly a working name only.
- **Why this matters here:** the DEVELOPMENT result is **negative** for the
  simple heuristic BBSR (Section 5 report). Even if the idea were novel, the
  current cheap observable implementation does not pass the progression gate,
  so no novelty claim would currently be actionable.

## 4. Ledger additions

The following serious, verified-adjacent entries are appended to
`research/literature/p2_algorithm_landscape.csv` (P2-040, P2-041) as
CLOSE_ANALOGUE / ALGORITHMIC_INSPIRATION, based on entries already present in
the ledger (no new primary-source sweep was performed):

- **P2-040** — Selective prediction with abstention (El-Yaniv & Wiener 2010;
  Chow 1957) as one-sided rejection inspiration for a DROP queue
  (ALGORITHMIC_INSPIRATION).
- **P2-041** — Budgeted verification of a predicted set (Repoformer/FastCoder
  verifier-on-top-k line) as ADD-only reconsideration (CLOSE_ANALOGUE).

Both are classified honestly; no DIRECT_COMPETITOR for "bidirectional bounded
set repair" is added because no verified primary source is held in the ledger.