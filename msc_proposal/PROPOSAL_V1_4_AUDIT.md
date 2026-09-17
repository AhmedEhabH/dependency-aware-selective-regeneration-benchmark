# Proposal V1.4 — Audit

**Date:** 2026-09-17 (updated for the V1.4 print/bibliography/timeline
addendum, same day)
**Audit type:** factual + structural + claims + layout audit for
`msc_proposal/MSC_PROPOSAL_V1_4.tex` / `.pdf` (V1, V1.2, V1.3 immutable).

---

## 0. V1.4 print addendum (2026-09-17, supersedes section 11 of the prior audit)

- **Table overlap fixed:** `Experimental Design at a Glance` rebuilt with 8
  compact columns (`Study | Purpose | Repo / Split | Method | Unit | Budget /
  Reps | Primary metrics | Status`), `tabularx` + `p{}`/`X` columns,
  `\raggedright`, short labels (`Controlled`, `Historical`, `Agent`, `Cheap
  baselines`, `Task risk`, `Candidate recovery`, `Cross-repo transfer`), no
  internal experiment codes, and status wording accurate as of 2026-09-17
  (Task risk = Negative / closed; Candidate recovery = DEV replicated;
  confirmatory pending; Cross-repo transfer = Saleor DEV replication complete).
  `\resizebox` removed. **Zero overfull hboxes** after tuning.
- **Bibliography rendered:** Section 11 now renders the actual verified
  `references.bib` (V1.4) via BibTeX (`unsrt`); every in-text `\cite{}`
  resolves; **21 reference entries** appear in the PDF (pages 9–10); preprints
  explicitly marked; no uncited dump (all 21 entries are cited in text);
  the stale "authoritative bibliography (V1.3)" sentence is replaced with V1.4
  wording.
- **Timeline replaced:** the short 2026-09→2027-05 table is replaced by the
  detailed **2026-11 → 2027-10** schedule (12 windows, compact wrapped table).
  Intended substantive research/thesis completion = **2027-07/08**;
  September–October 2027 is an explicit publication/revision/administrative
  buffer, not fabricated work.
- **Compile:** `pdflatex -halt-on-error` (2× + bibtex) clean; **10 pages**
  (7 → 10; acceptable for an MSc proposal; readability preserved); zero
  overfull/underfull/undefined-citation warnings.
- **PDF SHA-256:** `50957a2525f7430de47fd9306895d2b4c80b30c358d3cafe6798a0a27b0525b1`
  (recorded in `PROPOSAL_CHANGELOG.md`).

## 0b. V1.4 confirmatory + P2 timeline + cover update (2026-09-17)

- **Confirmatory result incorporated (CONFIRMS):** the frozen confirmatory
  protocol ran on the authorized djangoCMS V2 INTERNAL_TEST (80 tasks;
  560 calls / 1,470,174 tokens / ~$0.51; 0 failures; 0 excluded). Composite
  ORR vs analytic Random: B=1 0.059 vs 0.006, B=3 0.110 vs 0.017, B=5 0.165
  vs 0.028 (Δ+0.137, CI [+0.075,+0.205]), B=10 0.267 vs 0.055; CIs exclude
  zero at every B; no size artifact. **Fixed Route-B CONFIRMED on djangoCMS
  INTERNAL_TEST.** The confirmatory test is permanently used; not reused for
  P2 selection.
- **Timeline first five months aligned to the real P2 program** (Nov 2026 –
  Mar 2027): fixed Route-B confirmation + P2 formulation freeze → simple
  Shichao-inspired adaptive policies → cost-sensitive/one-step/demand-driven
  analogues → competitor/alternative reproduction → P2 comparison/freeze/
  pre-registration or negative closure (Saleor INTERNAL_TEST only if
  pre-registered).
- **Cover/title page:** conservative academic title page
  (`MSC_PROPOSAL_V1_4_TITLEPAGE.tex/.pdf`): Prepared by Ahmed Ehab; Faculty of
  Computing and AI, Cairo University + University of London Branch (EUE),
  Egypt; email ahmed.ehab@fci-cu.edu.eg; Supervised by Mohammad El-Ramly
  (m.elramly@fci-cu.edu.eg); ORCID 0000-0002-5076-3829; no invented academic
  ranks; no IEEE author blocks. Combined print artifact
  `MSC_PROPOSAL_V1_4_PRINT.pdf` (11 pages: title + body) via `pdfunite`.
- **Compile:** pdflatex (2×) + bibtex clean; **10 pages** (body). PDF SHA-256:
  `07cb0588bbc3c0f92e99c3634a1c325d5b8a03a6f6af706c393dad8c7c35497c`.

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

- `pdflatex -halt-on-error` + `bibtex` compiles clean: **10 pages** (V1.4
  print addendum; was 7).
- Experimental Design at a Glance: 8 compact `tabularx` columns, readable at
  A4, zero overfull hboxes, `\resizebox` removed.
- Timeline: 2026-11→2027-10 schedule renders cleanly (12 rows, wrapped text).
- PDF SHA-256 recorded in `PROPOSAL_CHANGELOG.md`.

## 12. Bibliography — PASS (rendered in PDF, V1.4)

- `references.bib` V1.4 verified from primary sources (arXiv/Crossref);
  preprints marked; no fabricated/placeholder citations remain.
- **Section 11 renders the actual bibliography** (BibTeX `unsrt`); every
  in-text citation resolves; 21 reference entries appear; no uncited dump.

## Overall
**SUPERVISOR-READY / PRINT-CANDIDATE**, pending institutional cover / template
or supervisor-requested edits. V1.4 supersedes V1.3 as the print candidate;
V1.3 remains immutable.

## 13. Author / cover format (2026-09-17; mission Block F) — PASS

- The proposal is NOT an IEEE conference paper; **no `\IEEEauthorblockN` /
  `\IEEEauthorblockA`** are used.
- A conservative academic title page was created:
  `msc_proposal/MSC_PROPOSAL_V1_4_TITLEPAGE.tex` / `.pdf` with: title, "MSc
  Research Proposal", Prepared by Ahmed Ehab, Faculty of Computing and AI,
  Cairo University, affiliation exactly as supplied (Faculty of Computing and
  AI, Cairo University **and** University of London Branch (EUE), Egypt),
  email `ahmed.ehab@fci-cu.edu.eg`, Supervised by Mohammad El-Ramly, email
  `m.elramly@fci-cu.edu.eg`, ORCID `0000-0002-5076-3829`, date 2026-09-17,
  academic year 2026/2027.
- **No academic ranks (Prof./Dr.) are invented** (none verified from an
  official source). Ahmed = candidate; El-Ramly = supervisor (not co-authors).
- Combined print artifact: `MSC_PROPOSAL_V1_4_PRINT.pdf` (11 pages: title
  page + 10-page V1.4 body) merged with `pdfunite` (MiKTeX pdfpages had an
  "artifact undefined" bug on the hyperref-rich V1.4 PDF).
- No official FCAI/Cairo University cover template exists locally; institutional
  cover/form fields are documented as PENDING (not fabricated).
- V1.4 science is preserved; no new scientific version was created for cover
  formatting.