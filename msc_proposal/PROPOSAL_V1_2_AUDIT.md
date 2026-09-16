# Proposal V1.2 — Audit

**Date:** 2026-09-16
**Audit type:** factual + structural + bibliography audit for
`msc_proposal/MSC_PROPOSAL_V1_2.tex` / `.pdf`.

---

## 1. Mandatory factual corrections — PASS

| Item | Required | In V1.2 | Source |
|---|---|---|---|
| Sparse mean serialized records | 4.9 | 4.9 | `reports/CONTROLLED_ENCODING_16K_RESULT.md` |
| Full mean serialized records | 144.0 | 144.0 | same |
| Reduction | ~96.6% | ~96.6% | computed (144−4.9)/144 |
| Stale 5.9 | removed | removed | n/a |
| LocAgent non-usable | 5/10 | 5/10 | P5C run report |
| LocAgent taxonomy | 2 timeout + 1 context + 2 empty | yes | P5C report |
| "50% empty localization rate" | removed | removed | n/a |
| V2 calls | 431 | 431 | V2 run_records |
| V2 cumulative tokens | 2,501,964 | 2,501,964 | V2 run_records |
| V2 post-call overshoot | 1,964 / 0.08% | yes | V2 run_records |
| "within ceiling" wording | removed | removed (overshoot stated) | n/a |

## 2. Structural changes (A1–A3) — PASS

- Central story made explicit (Section 2).
- Internal experiment codes (M1B/P1/P5/V2/Protocol-A/Route-A/Route-B) removed
  from main prose; descriptive names used; IDs only in the Experimental Design
  table and traceability.
- 11-section structure per the addendum.
- `Experimental Design at a Glance` table added.
- Architecture figure (flow) added.

## 3. Budget definition frozen (A7) — PASS

- Primary verification budget B = number of omitted candidate files admitted
  to second-stage inspection; primary operating point B=5; secondary
  B in {1,3,10}; primary endpoint task-clustered FN recovery at B=5; key
  control Sparse + Random Verify @ B=5. For a future LLM verifier: primary
  compute measure = additional total model tokens per task; tokens/cost/latency
  never collapsed.

## 4. Multiple-comparison discipline (A8) — PASS

- One primary endpoint at B=5; one primary Selective-vs-Random comparison;
  secondary labeled; task-level paired bootstrap; no post-hoc feature-family
  winner.

## 5. Representation-isolation paragraph (A5) — PASS

- States what was held constant in the Full-vs-Sparse controlled study and that
  fixed-policy decode equivalence is mathematical while different output
  instructions may alter LLM behavior.

## 6. Dataset/proxy construct validity (A6) — PASS

- Eligibility, exclusions, deduplication, production-file definition,
  parent-only input, hidden target, and the observed-change-set proxy scoping
  are stated. `docs/SEMANTIC_PROXY_AUDIT_PROTOCOL.md` is referenced (to be
  created in the semantic-proxy block).

## 7. Related-work / novelty wording (A9) — PASS

- Removed absolute "none combines..." wording.
- Added verified related lines + comparison matrix (file policy / sparse rep /
  cheap 1st / omission recovery / matched budget / real commit / x-repo).
- Candidate novelty marked NOT YET CLAIMED.

## 8. Bibliography (A4/A10) — PASS

- All high-priority references verified from primary sources (arXiv API /
  Crossref) on 2026-09-16.
- No placeholder or fabricated authors.
- LocAgent arXiv ID corrected (2503.09089; the earlier 2505.19084 was
  incorrect — that arXiv ID is a vision paper).
- RepoGraph placeholder entry removed (could not be verified from a primary
  source).

## 9. Compile / print (A10) — PASS

- `pdflatex -halt-on-error` compiles clean: **7 pages**.
- Tables use `\resizebox` to fit textwidth (no rendered overflow); remaining
  log overfull warnings are pre-scale inner-box warnings, not visual overflow.
- Figures are text/table based (grayscale-legible).
- PDF SHA-256 recorded in `PROPOSAL_CHANGELOG.md`.

## 10. Claims-matrix consistency — PASS

`PROPOSAL_CLAIMS_MATRIX.md` updated to rows 16–21 for the V1.2 corrections and
pre-registered gates.

## Overall
**SUPERVISOR-READY / PRINT-CANDIDATE**, pending only institutional cover/
template or supervisor-requested edits.