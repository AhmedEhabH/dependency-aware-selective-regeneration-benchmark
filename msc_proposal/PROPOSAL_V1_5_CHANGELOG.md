# MSC Proposal V1.5 — Changelog

**Version:** V1.5 (2026-09-17) · **Model (authoring agent):**
openrouter/deepseek/deepseek-v4-flash-0731
**Type:** DOCTOR-GUIDE-COMPLIANT POLISH. **ZERO API; no scientific input, no
method/ranker/verifier change; no new experiment; no sealed set opened.**

V1, V1.2, V1.3 and V1.4 are preserved immutably. V1.5 supersedes V1.4 as the
print candidate.

---

## V1.5 (2026-09-17)

### 1. Abstract rewritten (doctor-guide order)
- Order: problem/context → limitation of current approaches → precise gap →
  proposed approach → experimental setting → strongest result only →
  confirmatory status → one scope limitation.
- Removed unsafe phrasings: "for the first time at candidate level", unscoped
  "robust recovery signal".
- Demoted secondary results (representation effect 4.9/144, verifier pilot,
  identity audit/ablation detail, task-level RiskScorer rejection) to
  Section 9 (Preliminary evidence).
- Kept only the strongest result (djangoCMS confirmatory B=5 0.165 vs 0.028,
  Δ+0.137, CI excludes zero) plus a one-line Saleor DEV replication (0.237 vs
  0.006, development evidence only).
- Added the mandated one scope limitation (observed historical diff as proxy,
  not semantic ground truth).
- Full old-vs-new rationale: `ABSTRACT_REWRITE_NOTE.md`.

### 2. Related-work comparison matrix ADDED (fixes the Section 4 forward-reference)
- Section 4's promise ("The comparison matrix (Section~\ref{sec:design})")
  now resolves to two compact `tabularx` tables under `sec:design`
  ("Related-work comparison matrix", 1/2 design & structure, 2/2 evidence &
  position). The matrix was NOT deleted; it was added.
- Rows: Classical/history CIA · Agentless · CodePlan · RepoCoder/repo retrieval
  · LocAgent · GraphLocator · RepoGraph (ICLR 2025) · This proposal.
- Columns (split, no overlap): Input | Output unit | First pass? | Second
  stage? | History? | Graph? | Budget-aware? (table 1); False-negative
  recovery? | Real commits? | Cross-repo? | Main difference (table 2).
- New bibliography entry `repograph2025` (arXiv:2410.14684, ICLR 2025)
  verified from the arXiv API on 2026-09-17. `references.bib` now has 22
  entries; 22/22 cited; no uncited dump.

### 3. Terminology / claim-safety pass
- "Classical-CIA" standardized to "BM25+Graph-Neighbor Composite (historical
  label: Classical-CIA)" / short form `BM25+GraphNeighbor`; the genuinely
  classical dependency-propagation CIA baseline is explicitly distinguished
  from the frozen composite.
- "fair comparison" → "shared-protocol, budget-matched comparison".
- "missed impacted files" → "missed files in the observed historical
  change-set proxy".
- Ranking ≠ verification ≠ final localization made explicit (new "Stage
  boundaries" paragraph in `sec:design`).
- P2 (adaptive budget) stated as **NOT complete**: a development research
  program (Nov 2026 – Mar 2027) after fixed Route-B confirmation, not a
  proven contribution; competitor/analogue families named (selective
  prediction, cascades, optimal stopping, budgeted retrieval,
  value-of-information, interpretable adaptive stopping).
- NestJS/NextJS/cross-language extension stated as **future external-validity
  work only**, planned April 2027, conditional on the suitability gate AND
  TypeScript-extractor readiness (scope contract + timeline + closing note).

### 4. Factual / typographic corrections
- Experimental-Design table: "Candidate recovery" status corrected from
  "confirmatory pending" to "DEV replicated; CONFIRMED (2026-09-17)" (the
  confirmatory run completed and CONFIRMED on 2026-09-17).
- Markdown `**...**` bold artifacts left in V1.4's LaTeX source replaced with
  `\textbf{...}` (typography only; V1.4 PDF byte-identical).

### 5. Compile / layout
- `pdflatex -halt-on-error` (3×) + `bibtex`: clean; **12 pages** (V1.4 was 10;
  +2 from the two comparison-matrix tables).
- **Zero overfull hboxes; zero underfull; zero undefined references; zero
  BibTeX warnings.**
- PDF SHA-256: `67dff046347847e1f80e01bdf313acf3cf2a577bfa2783f02686c4e3cf041ef7`.
- Audit: `PROPOSAL_V1_5_AUDIT.md`; claims: `PROPOSAL_V1_5_CLAIMS_MATRIX.md`.

### 6. Boundary
- No sealed set opened; djangoCMS RESERVE, Saleor INTERNAL_TEST/RESERVE sealed;
  djangoCMS INTERNAL_TEST recorded as permanently spent (never reused as a
  fresh P2 test).
- No stable tag moved; V1/V1.2/V1.3/V1.4 immutable.