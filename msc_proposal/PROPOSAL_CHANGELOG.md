# MSC Proposal V1 — Changelog

## V1 (2026-09-16)

- **Initial supervisor-ready draft.**
- Title: *Cost-Aware Repository Change Localization with Sparse Impact Planning
  and Bounded Verification* (does not assume graph/RiskScorer success).
- 16 sections: background, problem, gap, objectives, RQs, current evidence,
  architecture, dataset methodology, baselines, evaluation, statistical plan,
  generalization plan, threats, contributions, work plan/timeline, references.
- Evidence included truthfully:
  - M1A/M1B controlled representation effect;
  - real-commit P1 (60 cells), LocAgent P5 (10 tasks);
  - cheap baselines (Protocol A);
  - 90-cell Sparse-v2 TRAIN/VALIDATION development inference (90/90 valid,
    490,747 tokens / $0.184);
  - V2 development inference (431/450 cells, 144 tasks;
    signal does not replicate → no RiskScorer);
  - classical/static CIA baseline (150 V2 dev cases, zero LLM).
- Contingencies pre-registered: Route A (task-level routing) vs Route B
  (candidate-level bounded verification); **no positive algorithmic result
  promised**.
- References: `references.bib` (verified + preprint-marked; 4 entries flagged
  "author list to be confirmed from primary source" — NO fabricated citations).
- Compiled with pdflatex: 6 pages, clean (2 passes).
- Known open items for supervisor:
  1. institutional (FCAI) template/cover/signature pages — intentionally not
     fabricated;
  2. confirm RQ wording and Route A/B framing;
  3. decide whether to expand the 6-page draft with evidence tables.

<!-- Append new versions below. -->
## V1.2 (2026-09-16 evening)

- **Central story** made explicit (can a cheap/sparse first pass + bounded
  omission recovery beat cheap-only and always-on expensive reasoning?).
- **Internal codes removed** from main prose; descriptive names used; IDs only
  in the Experimental Design table and traceability.
- **11-section structure** (A3), Experimental Design at a Glance table, and
  architecture flow added.
- **Factual corrections** (A4): Sparse 4.9 / Full 144.0 / ~96.6% reduction;
  LocAgent 5/10 non-usable taxonomy; V2 431 calls / 2,501,964 tokens /
  1,964-token (0.08%) overshoot; removed stale 5.9, "50% empty", "within
  ceiling".
- **Budget definition frozen** (A7): B = omitted candidate files, primary
  B=5, secondary {1,3,10}, FN recovery endpoint, Random Verify control; LLM
  verifier primary compute = additional tokens per task.
- **Multiple-comparison discipline** (A8) added.
- **Representation-isolation paragraph** (A5) added.
- **Dataset/proxy construct validity** (A6) expanded; semantic-proxy audit
  protocol referenced.
- **Related-work wording** softened (no absolute "none combines"); verified
  related lines + comparison matrix added (A9).
- **Bibliography** verified from primary sources (arXiv/Crossref); LocAgent
  arXiv corrected to 2503.09089; RepoGraph placeholder removed.
- Compile: 7 pages, clean. PDF SHA-256: 61023f425e317b490a1b25eef19df1890579517974f328b13b149750d7433630.
- Audit: PROPOSAL_V1_2_AUDIT.md.

## V1.3 (2026-09-17)

- Central identity sentence added.
- CI-crossing-zero parity wording removed.
- B-curve (B in {0,1,3,5,10}) is primary; B=5 is a reference point.
- RIPPLE / Change-Patterns Mapping / ArtifactSync contrasts added.
- Graph/history/selective explicitly not novel alone.
- Title preserved.
- Scope contract (CORE vs CONDITIONAL/FUTURE) added.
- Future Work adaptive/cost-sensitive verification paragraph added (rho =
  sensitivity, not monetary truth; not yet a contribution).
- Route B V2 budget curve + verifier pilot incorporated into preliminary
  evidence.
- Compile: 7 pages, clean. PDF SHA-256:
  db2e46f3e028b380bad68fce09356a93f4c7952ba7619fdff369481b18585ec.
- Audit: PROPOSAL_V1_3_AUDIT.md.

## V1.4 (2026-09-17)

- **Material scientific change:** Saleor Route-B transfer REPLICATES on
  DEVELOPMENT → V1.4 created (V1.3 predates the completed Saleor transfer).
- Saleor DEVELOPMENT Sparse run: 150×3 = 450 cells; 446 valid / 4 failed;
  7,316,986 tokens / $2.31; 0 truncations; no Saleor-specific tuning.
- Saleor frozen Route-B transfer: 149 evaluable tasks; B=5 composite 0.237 vs
  analytic Random 0.006; delta +0.231, CI [+0.180,+0.287]; 5/5 folds positive;
  no size artifact. Explicitly DEVELOPMENT transfer replication, NOT
  confirmatory.
- **Ranker identity corrected:** "Classical-CIA" → `BM25+Graph-Neighbor
  Composite (historical label: Classical-CIA)` (normalized BM25 + binary
  graph-neighbor), per the ranker-identity audit; Hybrid labelled a
  rank-equivalent redundant control.
- **Incremental-evidence ablation:** cross-repo signal stated as predominantly
  lexical (BM25); graph increment small, largely non-significant; no graph
  novelty claim.
- Per-repository primary retained; no djangoCMS+Saleor pooling as headline.
- Adaptive B_t remains future/conditional; INTERNAL_TEST/RESERVE sealed
  (djangoCMS + Saleor).
- Compile: 7 pages, clean. PDF SHA-256: dd7125fa52025917b32bed77bd141a954657f888c83513f42ba0829e7ee59cd8.
- Audit: PROPOSAL_V1_4_AUDIT.md.

## V1.4 print/bibliography/timeline addendum (2026-09-17, V1.4 in place — no V1.5)

- **Experimental Design at a Glance table overlap fixed:** rebuilt with 8
  compact `tabularx` columns (Study | Purpose | Repo / Split | Method | Unit |
  Budget / Reps | Primary metrics | Status), `\raggedright` wrapping, short
  labels, no internal codes, no `\resizebox`. Zero overfull hboxes.
- **Bibliography rendered in the PDF:** Section 11 now compiles the actual
  verified `references.bib` via BibTeX (`unsrt`); every in-text `\cite{}`
  resolves; 21 reference entries appear in the PDF (pages 9–10); preprints
  marked; the stale "authoritative bibliography (V1.3)" sentence replaced with
  V1.4 wording.
- **Timeline replaced:** detailed **2026-11 → 2027-10** schedule (12 windows);
  intended substantive research/thesis completion **2027-07/08**;
  September–October 2027 = publication/revision/admin buffer.
- Compile: pdflatex (2×) + bibtex clean; **10 pages** (was 7). PDF SHA-256:
  `11647e0c6378684203dde339b5aa306f038b27afbf0af82107f8559f35805ad1`.
- Audit: PROPOSAL_V1_4_AUDIT.md (§0 addendum).

## V1.4 confirmatory + P2 timeline + cover update (2026-09-17, V1.4 in place)

- **Confirmatory result incorporated (2026-09-17):** the frozen confirmatory
  protocol ran on the authorized djangoCMS V2 INTERNAL_TEST (80 tasks;
  560 calls / 1,470,174 tokens / ~$0.51; 0 failures; 0 excluded). Composite
  ORR vs analytic Random: B=1 0.059 vs 0.006, B=3 0.110 vs 0.017, B=5 0.165
  vs 0.028 (Δ+0.137, CI [+0.075,+0.205]), B=10 0.267 vs 0.055; CIs exclude
  zero at every B; no size artifact. **Fixed Route-B CONFIRMED on djangoCMS
  INTERNAL_TEST.** The confirmatory test is permanently used; not reused for
  P2 selection.
- **Timeline first five months aligned to the real P2 program:** 2026-11
  fixed Route-B confirmation + P2 formulation freeze; 2026-12 simple
  Shichao-inspired adaptive policies; 2027-01 cost-sensitive/one-step/
  demand-driven analogues; 2027-02 competitor/alternative reproduction;
  2027-03 P2 comparison/freeze/pre-registration or negative closure (Saleor
  INTERNAL_TEST only if pre-registered).
- **Cover/title page:** conservative academic title page
  (`MSC_PROPOSAL_V1_4_TITLEPAGE.tex/.pdf`): Prepared by Ahmed Ehab; Faculty of
  Computing and AI, Cairo University + University of London Branch (EUE),
  Egypt; email ahmed.ehab@fci-cu.edu.eg; Supervised by Mohammad El-Ramly
  (m.elramly@fci-cu.edu.eg); ORCID 0000-0002-5076-3829; no invented academic
  ranks; no IEEE author blocks. Combined print artifact
  `MSC_PROPOSAL_V1_4_PRINT.pdf` (11 pages: title + body) via `pdfunite`.
- Compile: pdflatex (2×) + bibtex clean; **10 pages** (body). PDF SHA-256:
  `07cb0588bbc3c0f92e99c3634a1c325d5b8a03a6f6af706c393dad8c7c35497c`.
- Audit: PROPOSAL_V1_4_AUDIT.md (§0 addendum + §13 cover).
