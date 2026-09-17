# Proposal V1.5 — Audit

**Date:** 2026-09-17
**Audit type:** factual + structural + claims + layout audit for
`msc_proposal/MSC_PROPOSAL_V1_5.tex` / `.pdf`.
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731
**Boundary:** V1.5 is a DOCTOR-GUIDE-COMPLIANT POLISH of V1.4. **ZERO API; no
scientific/method/ranker/verifier change; no new experiment; no sealed set
opened.** V1.4 remains immutable (PDF SHA-256
`07cb0588bbc3c0f92e99c3634a1c325d5b8a03a6f6af706c393dad8c7c35497c` — verified
unchanged after V1.5 work).

---

## 1. Reason V1.5 exists — PASS (documentation polish milestone)

- The mission mandates a doctor-guide-compliant abstract rewrite, a
  related-work comparison matrix (fixing the Section 4 forward-reference), a
  terminology/claim-safety pass, slide-handoff, and P2 status alignment.
- **No material scientific change** vs V1.4: the last material change was the
  confirmed djangoCMS INTERNAL_TEST result, already incorporated in V1.4.

## 2. Abstract rewrite — PASS (doctor-guide order)

- Order verified: problem/context → limitation of current approaches → precise
  gap → proposed approach → experimental setting → strongest result only →
  confirmatory status → one scope limitation.
- "for the first time" removed; unscoped "robust" removed.
- No miniature methods section; no excessive internal experiment codes in the
  Abstract (no P1/V2/ORR/M1B codes; `B` and `P2` are explained in text).
- DEVELOPMENT vs CONFIRMATORY vs FUTURE boundaries explicit.
- Rationale ledger: `ABSTRACT_REWRITE_NOTE.md`.

## 3. Related-work comparison matrix — PASS (forward-reference fixed)

- Section 4 forward-reference to Section 5 now resolves: two compact
  `tabularx` tables added under `sec:design` ("Related-work comparison
  matrix", split 1/2 design & structure, 2/2 evidence & position).
- Rows: Classical/history CIA, Agentless, CodePlan, RepoCoder / repo
  retrieval-for-generation, LocAgent, GraphLocator, RepoGraph (ICLR 2025,
  verified from primary source), This proposal.
- Columns: Input | Output unit | First pass? | Second stage? | History? |
  Graph? | Budget-aware? (table 1); False-negative recovery? | Real commits? |
  Cross-repo? | Main difference (table 2). No overlap between the two tables.
- RepoGraph added to `references.bib` as `repograph2025` (verified from the
  arXiv API: arXiv:2410.14684, ICLR 2025; authors verified). 22/22 entries
  cited; no uncited dump; no missing citations.

## 4. Terminology and claim-safety pass — PASS

- "Classical-CIA" appears only with the historical-label qualifier
  ("BM25+Graph-Neighbor Composite (historical label: Classical-CIA)") or as
  the short form `BM25+GraphNeighbor`; the genuinely classical
  dependency-propagation CIA baseline is explicitly distinguished.
- "fair comparison" → "shared-protocol, budget-matched comparison".
- "missed impacted files" → "missed files in the observed historical
  change-set proxy" (RQ3, preliminary evidence, cross-repo section).
- Ranking ≠ verification ≠ final localization: new "Stage boundaries"
  paragraph under `sec:design`.
- P2 stated as **NOT complete** — a development research program (Nov 2026 –
  Mar 2027), not a proven contribution; competitor/analogue families named
  (selective prediction, cascades, optimal stopping, budgeted retrieval,
  value-of-information, interpretable adaptive stopping).
- NestJS/NextJS/cross-language stated as **future external-validity work only**
  (April 2027, conditional on suitability gate AND TypeScript-extractor
  readiness).

## 5. Factual integrity — PASS

- All numbers re-quoted in V1.5 map to audited artifacts:
  - Saleor DEV Sparse run: 150×3 = 450 cells; 446 valid / 4 failed;
    7,316,986 tokens / $2.31; 0 truncations
    (`reports/SALEOR_ROUTE_B_TRANSFER_REPORT.md`).
  - Saleor transfer: 149 tasks; B=5 composite 0.237 vs Random 0.006; delta
    +0.231, CI [+0.180,+0.287]
    (`reports/SALEOR_ROUTE_B_TRANSFER_REPORT.md`).
  - djangoCMS confirmatory: 80 tasks; 560 calls / 1,470,174 tokens / ~$0.51;
    B=5 0.165 vs 0.028, delta +0.137, CI [+0.075,+0.205]
    (`reports/DJANGOCMS_ROUTE_B_CONFIRMATORY_RESULT.md`).
- The "Candidate recovery" row status in the Experimental-Design table was
  corrected from "confirmatory pending" (stale after the 2026-09-17 run) to
  "DEV replicated; CONFIRMED (2026-09-17)".
- Markdown `**...**` bold artifacts left in V1.4's LaTeX source were corrected
  to `\textbf{...}` in V1.5 (typography only; V1.4 PDF unchanged).

## 6. Compile / layout — PASS

- `pdflatex -halt-on-error` (3×) + `bibtex`: clean; **12 pages** (V1.4 was
  10; +2 from the two comparison-matrix tables).
- **Zero overfull hboxes; zero underfull; zero undefined references; zero
  multiply-defined citations; zero BibTeX warnings.**
- All tables render within the text block at A4; matrix split into two
  readable tables (no `\resizebox`, no landscape needed).
- PDF SHA-256: `67dff046347847e1f80e01bdf313acf3cf2a577bfa2783f02686c4e3cf041ef7`.

## 7. Bibliography — PASS

- `references.bib` V1.5: 22 entries, all verified (the only addition for V1.5
  is `repograph2025`, verified from the arXiv API 2026-09-17).
- Every in-text citation resolves; no uncited dump (22 cited / 22 present).

## 8. Boundary / governance — PASS

- No sealed data opened: djangoCMS RESERVE, Saleor INTERNAL_TEST/RESERVE stay
  sealed; the opened djangoCMS INTERNAL_TEST is recorded as permanently spent,
  never reused as a fresh test for P2 selection.
- No stable tag moved; historical V1/V1.2/V1.3/V1.4 PDFs byte-identical.

## Overall

**SUPERVISOR-READY / PRINT-CANDIDATE (V1.5).** V1.5 supersedes V1.4 as the
print candidate for the submission-seminar; V1.4 remains immutable.