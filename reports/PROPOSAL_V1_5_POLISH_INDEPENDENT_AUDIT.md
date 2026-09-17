# Proposal V1.5 Polish + Matrix + Abstract + Slide Handoff — Independent Audit

**Date:** 2026-09-17
**Auditor:** independent verification pass over the V1.5 docs-only milestone
**Mission:** OPENCODE NEXT MISSION — PROPOSAL V1.5 POLISH + RELATED-WORK
MATRIX + ABSTRACT REWRITE + SLIDE HANDOFF PACKAGE (2026-09-17)
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731

---

## 1. Scope

- A. Abstract rewrite (doctor-guide order).
- B. Related-work comparison matrix (Section 4 forward-reference fix).
- C. Terminology / claim-safety pass.
- D. V1.5 versioning (tex/pdf/audit/changelog/claims matrix), V1.4 immutable.
- E. Slide handoff package.
- F. P2 + five-month-program status alignment.
- G. Audit / test / git / export.

## 2. Boundary (verified)

- **ZERO API / zero model calls**: nothing in this mission calls a model;
  the only network access was the arXiv API bibliographic lookup for
  RepoGraph (arXiv:2410.14684) — literature verification, not a scientific
  call.
- **No scientific/method/ranker/verifier change**; no new experiment; no
  production `src/` change.
- **Sealed sets untouched (verified):** djangoCMS RESERVE, Saleor
  INTERNAL_TEST/RESERVE remain sealed; the opened djangoCMS INTERNAL_TEST is
  only referenced as permanently spent (never reopened, never reused as a
  fresh P2 test).
- **V1.4 immutable (verified):** `MSC_PROPOSAL_V1_4.tex` byte-identical
  (git diff empty); `MSC_PROPOSAL_V1_4.pdf` SHA-256
  `07cb0588…497c` unchanged. V1/V1.2/V1.3 untouched.

## 3. Deliverable audit

### A. Abstract rewrite — PASS
- Doctor-guide order verified in the compiled PDF: problem/context →
  limitation → precise gap → proposed approach → experimental setting →
  strongest result only → confirmatory status → one scope limitation.
- "for the first time" and unscoped "robust" removed (only appear in the
  header comment documenting the change).
- No miniature methods section; no internal experiment codes in the Abstract.
- Rationale ledger present: `msc_proposal/ABSTRACT_REWRITE_NOTE.md`.

### B. Related-work comparison matrix — PASS
- Section 4 forward-reference now resolves (two `tabularx` tables under
  `sec:design`); the promise was fulfilled by ADDING the matrix, not deleting
  the reference.
- Rows/columns match the mission spec; two readable tables, no overlap.
- RepoGraph row verified from the primary source (arXiv API, 2026-09-17:
  ICLR 2025, arXiv:2410.14684, authors/title verified); new `repograph2025`
  bib entry; 22/22 entries cited, no uncited dump, no missing citations.

### C. Terminology / claim-safety — PASS
- "Classical-CIA" only appears with the historical-label qualifier; the
  genuinely classical dependency-propagation CIA baseline is distinguished.
- "fair comparison" → "shared-protocol, budget-matched comparison".
- "missed impacted files" → "missed files in the observed historical
  change-set proxy".
- Ranking ≠ verification ≠ final localization explicit ("Stage boundaries").
- P2 = NOT complete (development research program); NestJS/NextJS = future
  external-validity work only (April 2027, suitability gate + TS extractor).

### D. V1.5 versioning — PASS
- `MSC_PROPOSAL_V1_5.tex/.pdf` (12 pages; compile clean), `PROPOSAL_V1_5_AUDIT.md`,
  `PROPOSAL_V1_5_CHANGELOG.md`, `PROPOSAL_V1_5_CLAIMS_MATRIX.md`,
  `ABSTRACT_REWRITE_NOTE.md` created; `PROPOSAL_CHANGELOG.md` + claims-matrix
  pointer updated.
- Compile: `pdflatex -halt-on-error` (3×) + `bibtex` clean; **12 pages**;
  **zero overfull / zero underfull / zero undefined references / zero
  multiply-defined / zero BibTeX warnings**.
- PDF SHA-256: `67dff046347847e1f80e01bdf313acf3cf2a577bfa2783f02686c4e3cf041ef7`.

### E. Slide handoff — PASS
- `slides/HANDOFF_INTERACTIVE_MSC_SEMINAR_SLIDES.md`: one-minute story,
  20-slide interactive outline (18–24 range), toy 10-file example, exact
  definitions, frozen key numbers with provenance filenames, claim
  boundaries, Q&A, builder notes. Self-contained for a fresh LLM.

### F. P2 status — PASS
- `docs/P2_IMPLEMENTATION_ROADMAP_2026_2027.md`,
  `docs/P2_COMMON_EVALUATION_CONTRACT.md`,
  `docs/ADAPTIVE_BUDGET_P2_PRE_REGISTRATION_NOTE.md` updated: P2 NOT complete;
  fixed Route B CONFIRMED; P2 = development research program; April 2027
  NestJS/NextJS external-validity conditional on suitability gate + TS
  extractor; pre-registration gate 1 satisfied, gate 2 pending.

## 4. Factual-number spot-check (independent re-derivation) — PASS

- djangoCMS confirmatory JSON: B=5 composite ORR 0.165 / analytic Random
  0.0277 / Δ+0.1367 CI [0.0746,0.2046]; verifier B=5 ORR 0.1007; final set
  @B=5 P 0.2058 / R 0.284 / F1 0.2387 / FNR 0.716 — matches every quoted
  number in the abstract, matrix captions, and slide file.
- Saleor transfer JSON: B=5 CIA macro ORR 0.2369 vs AnalyticRandom 0.0061;
  Δ+0.2307 CI [0.1799,0.2871] — matches 0.237 / 0.006 / Δ+0.231 CI
  [+0.180,+0.287].
- Saleor closure JSON: 450 cells, 446 valid / 4 failed, 7,316,986 tokens,
  $2.306918, 150 tasks, ceilings respected — matches.
- Confirmatory ledger: 560 calls / 1,470,174 tokens / $0.505917; 0 failures;
  0 excluded; ceilings respected — matches.

## 5. Tests / static checks

- `git diff --check`: PASS (0 whitespace errors).
- No Python files changed → Ruff/Mypy/py_compile not applicable (docs-only).
- No production code/config/Kaggle/entry-point change → bundle rebuild NOT
  applicable per the verification skill.
- Full pytest suite NOT run (docs-only; the last audited baseline was
  3303 passed / 33 skipped / 2 pre-existing environmental failures on the
  clean base, unchanged by docs).

## 6. Verdict

**PASS.** The V1.5 milestone is a clean docs-only polish: the abstract
follows the doctor-guide order, the comparison matrix resolves the
forward-reference, terminology is safe, all quoted numbers match frozen
artifacts, V1.4 stays immutable, sealed sets stay sealed, and the slide
handoff is self-contained. No scientific claim level changed from V1.4.