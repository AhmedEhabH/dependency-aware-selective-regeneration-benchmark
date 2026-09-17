# MSC Proposal V1 — Print Checklist

Run on the FINAL compiled PDF before physical print.

## Content / correctness

- [ ] Title and terminology consistent between `.tex`, `references.bib`,
      `PROPOSAL_SUPERVISOR_BRIEF.md`, and the claims matrix.
- [ ] No fabricated institutional form fields (no FCAI cover/signatures unless
      real template provided).
- [ ] Claims matrix rows all VERIFIED or marked `TO VERIFY`; none strengthened.
- [ ] Preprints explicitly marked; no fake citations (4 bib entries marked
      "author list to be confirmed").
- [ ] Data-vs-model distinction correct: live inference (90-cell, V2 431/450)
      is NOT a dry run anywhere in the text.

## LaTeX / PDF quality

- [ ] `pdflatex -halt-on-error` compiles clean (currently 6 pages).
- [ ] No undefined references, no overfull hboxes that clip text.
- [ ] Page count reasonable (target 8–12 single-spaced; current 6 is concise —
      can be expanded with more evidence tables if the supervisor wants).
- [ ] Margins sensible (geometry 2.5 cm set).
- [ ] Figures legible in grayscale (proposal has no color-critical figures).
- [ ] Font/line spacing readable in print (lmodern, 11pt).

## Layout / print

- [ ] A4 or Letter as required by the target institution.
- [ ] No hyperlink-only content that disappears in print (URLs printed).
- [ ] Headings/numbering consistent.
- [ ] PDF metadata title set to the proposal title.

## Post-print

- [ ] Physical print matches the frozen PDF byte-for-byte (no post-print edits).
- [ ] Changelog entry records the frozen PDF hash.

## Current status

- Compiled: **10 pages, PASS (2026-09-17, V1.4 print addendum + confirmatory/
  P2/cover update)**; bibliography rendered (21 verified entries, Section 11);
  Experimental Design table rebuilt (`tabularx`, zero overfull hboxes);
  timeline 2026-11→2027-10 (first five months = real P2 program); fixed
  Route-B CONFIRMED on djangoCMS INTERNAL_TEST incorporated.
- PDF SHA-256 (V1.4 confirmatory/P2/cover update):
  `07cb0588bbc3c0f92e99c3634a1c325d5b8a03a6f6af706c393dad8c7c35497c`.
- Title page: `MSC_PROPOSAL_V1_4_TITLEPAGE.pdf`; combined print:
  `MSC_PROPOSAL_V1_4_PRINT.pdf` (11 pages).
- Pending: institutional FCAI/Cairo University cover template/information from
  the supervisor (not fabricated).