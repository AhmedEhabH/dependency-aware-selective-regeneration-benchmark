# Proposal V1.3 — Audit

**Date:** 2026-09-17
**Audit type:** factual + structural + bibliography audit for
`msc_proposal/MSC_PROPOSAL_V1_3.tex` / `.pdf` (V1.2 immutable).

---

## 1. Central identity (mission §8.10) — PASS

- Added the exact central identity sentence: "This thesis studies whether a
  cheap sparse file-impact policy can reduce repository-wide localization
  effort while a bounded second look recovers important files the first pass
  chose not to change."

## 2. CI-crossing-zero ≠ parity (mission §8.1) — PASS

- No claim says CI crossing zero implies parity/equivalence. Where intervals
  include zero (e.g., earlier task-level DEV_VALIDATION), the text states the
  point estimate and the interval without a parity claim.

## 3. B-curve, not B=5 (mission §8.2) — PASS

- Primary object is the budget curve B∈{0,1,3,5,10}; B=5 is a reference point.
- Route B V2 curve reported (CIA above analytic Random at every B, intervals
  exclude zero).

## 4. Exact contrasts (mission §8.3–8.5) — PASS

- RIPPLE (known seed → recall expansion → precision refinement) vs this thesis
  (explicit repo-wide sparse policy → rejected residual set → bounded
  reconsideration of rejected candidates).
- Change-Patterns Mapping (reranks initial set) vs this work (allocates NEW
  inspection to the excluded residual set).
- ArtifactSync as a demo-level mechanistic analogue (different post-commit
  task).

## 5. Graph/history/selective not novel alone (mission §8.6) — PASS

- Explicitly stated: "Graph, history, and selective computation are not novelty
  claims by themselves."

## 6. Title preserved (mission §8.7) — PASS

- `Cost-Aware Repository Change Localization with Sparse Impact Planning and
  Bounded Verification` unchanged.

## 7. Scope contract (mission §8.8) — PASS

- CORE vs CONDITIONAL/FUTURE separated.

## 8. Future Work adaptive paragraph (mission §8.9) — PASS

- Added the adaptive/cost-sensitive verification paragraph with the formal
  B_t* expression and rho-as-sensitivity caveat; labeled as not yet a
  contribution.

## 9. Factual integrity (V1.2 corrections carried) — PASS

- Sparse 4.9 / Full 144.0 / ~96.6% reduction; LocAgent 5/10 taxonomy; V2
  431 calls / 2,501,964 tokens / 1,964-token (0.08%) overshoot; no stale 5.9,
  no "50% empty", no "within ceiling".

## 10. Bibliography (mission §13) — PASS

- Verified from primary sources (arXiv/Crossref); no placeholder authors;
  preprints marked.

## 11. Compile / print (mission §8 goal) — PASS

- `pdflatex -halt-on-error` compiles clean: **7 pages**.
- Tables fit via \resizebox (no rendered overflow).
- PDF SHA-256 recorded in `PROPOSAL_CHANGELOG.md`.

## Overall
**SUPERVISOR-READY / PRINT-CANDIDATE**, pending institutional cover / template
or supervisor-requested edits.