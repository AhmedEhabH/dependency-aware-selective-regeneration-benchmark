# Proposal V1.4 — Audit

**Date:** 2026-09-17
**Audit type:** factual + structural + claims + layout audit for
`msc_proposal/MSC_PROPOSAL_V1_4.tex` / `.pdf` (V1, V1.2, V1.3 immutable).

---

## 1. Reason V1.4 now exists (material scientific change) — PASS

- Saleor Route-B transfer REPLICATES on DEVELOPMENT (2026-09-17): a DEVELOPMENT
  transfer result is a material scientific-state change vs V1.3 (which predates
  the completed Saleor transfer). Proposal V1.4 is therefore justified.
- **Boundary:** the Saleor evidence is DEVELOPMENT transfer replication only,
  NOT confirmatory. Explicitly labelled as such in the abstract, preliminary
  evidence, and cross-repo section.

## 2. Saleor DEVELOPMENT Sparse run facts (mission §E.1) — PASS

- 150 × 3 = 450 cells; 446 valid / 4 failed; 7,316,986 tokens / $2.31;
  0 truncations; no Saleor-specific tuning. All stated in §9.

## 3. Saleor frozen Route-B transfer facts (mission §E.2) — PASS

- 149 evaluable tasks (012472eb8482 excluded — no succeeded rep).
- Replicated positive omission-recovery signal vs Analytic Random.
- B=5 composite ~0.237 vs Random ~0.006; delta +0.231, CI [+0.180, +0.287];
  5/5 folds positive; no size artifact.

## 4. Ranker-identity correction (mission §E.5, §E.6) — PASS

- "Classical-CIA" terminology corrected to the actual implementation:
  **`BM25+Graph-Neighbor Composite (historical label: Classical-CIA)`** =
  normalized BM25 + binary graph-neighbor indicator (per the ranker-identity
  audit). No association/importance weighting claimed.
- Hybrid arm explicitly labelled a rank-equivalent redundant control, not an
  independent baseline.

## 5. Incremental-evidence ablation (mission §E.5) — PASS

- The proposal states the cross-repo signal is **predominantly lexical (BM25)**:
  composite-minus-BM25 paired deltas are small with bootstrap CIs including
  zero at most B (djangoCMS B=5 +0.003 [−0.015,+0.019]; Saleor B=5 +0.003
  [−0.017,+0.024]). It does NOT imply dependency reasoning contributes strongly.
- No graph novelty claim (graph/history/selective not novel alone retained).

## 6. No new ranker / no method change (mission constraints) — PASS

- The frozen confirmatory method is unchanged; the audit/ablation are
  characterization only. No confirmatory test result is claimed.

## 7. Cross-repo discipline (mission §E.4) — PASS

- Per-repository primary; no djangoCMS+Saleor pooling as the headline.

## 8. Adaptive B_t (mission §E.8) — PASS

- Adaptive / cost-sensitive B_t remains future/conditional (unchanged).

## 9. INTERNAL_TEST / RESERVE sealed (mission §E.9) — PASS

- djangoCMS INTERNAL_TEST/RESERVE and Saleor INTERNAL_TEST/RESERVE stated as
  sealed; never opened.

## 10. Factual integrity (V1.3 corrections carried) — PASS

- Sparse 4.9 / Full 144.0 / ~96.6% reduction; LocAgent 5/10 taxonomy; no stale
  numbers. Route B V2 curve + verifier pilot retained.

## 11. Compile / layout (mission §E: compile + claims/citation/layout audit) — PASS

- `pdflatex -halt-on-error` compiles clean: **7 pages**.
- Tables fit (Experimental Design at a Glance uses \resizebox).
- PDF SHA-256 recorded in `PROPOSAL_CHANGELOG.md`.

## 12. Bibliography — PASS (unchanged from V1.3)

- `references.bib` V1.3 verified from primary sources (arXiv/Crossref);
  preprints marked; no fabricated/placeholder citations remain.

## Overall
**SUPERVISOR-READY / PRINT-CANDIDATE**, pending institutional cover / template
or supervisor-requested edits. V1.4 supersedes V1.3 as the print candidate;
V1.3 remains immutable.