# Route B — Ranker-Identity Audit

**Date:** 2026-09-17  **Type:** T3 audit  **ZERO API calls**
**Repository:** djangoCMS + Saleor DEVELOPMENT (deterministic recomputation from
committed run records and case bundles; no frozen historical output modified).

## 1. What the committed code defines (exact)

From `scripts/route_b_v2_robustness.py` (frozen, imported verbatim by the Saleor transfer):

- `bm` = normalized BM25 score (`bm25_scores[p] / max_bm25`).
- `graph_neighbor` = binary indicator (1.0 if candidate is a graph neighbor of seeds/write-set, else 0.0).
- `hybrid` feature = `0.5 * bm + 0.5 * graph_neighbor`.
- CIA ordering = descending `bm25 + graph_neighbor` (key `-bm25 - graph_neighbor`, path tie-break).
- Hybrid ordering = descending `hybrid` = descending `0.5*(bm25 + graph_neighbor)` (path tie-break).

## 2. Mathematical rank-equivalence proof (CIA vs Hybrid)

Let $s(p) = bm(p) + nb(p)$ be the CIA key and $h(p) = 0.5\cdot bm(p) + 0.5\cdot nb(p)$ the Hybrid key.
Then $h(p) = 0.5\cdot s(p)$ for every candidate $p$. Since $0.5 > 0$ is a fixed positive scalar,
the total order induced by descending $s$ equals the total order induced by descending $h$;
the path tie-break is identical. Therefore the two rankers produce **identical rankings and
identical top-$B$ sets for every budget $B$** on every task.

## 3. Empirical top-B identity (deterministic, zero API)

- djangoCMS DEVELOPMENT: 174 tasks; B = {1,3,5,10}; differing task-budget cells: **0**; full-rank identical: **True**.
- Saleor DEVELOPMENT: 149 tasks; B = {1,3,5,10}; differing task-budget cells: **0**; full-rank identical: **True**.

| Repo | B | tasks where top-B differs |
|---|---:|---:|
| djangoCMS | 1 | 0 |
| djangoCMS | 3 | 0 |
| djangoCMS | 5 | 0 |
| djangoCMS | 10 | 0 |
| Saleor | 1 | 0 |
| Saleor | 3 | 0 |
| Saleor | 5 | 0 |
| Saleor | 10 | 0 |

## 4. Classification

**CIA and Hybrid are rank-equivalent on every djangoCMS and Saleor DEVELOPMENT task at
every checked budget (0 differing cells). Hybrid is a REDUNDANT ALIAS/CONTROL, NOT an
independent baseline.** The V2 results files already show identical macro/micro ORR and
recovered-FN counts for CIA and Hybrid at every B on both repositories.

Historical results are NOT changed; this is a correction/clarification appended at 2026-09-17.

## 5. Name audit: does `Classical-CIA` overstate the implementation?

- The frozen Route-B V2 `CIA` arm is **exactly** `normalized BM25 + binary graph-neighbor
  indicator`. It does NOT implement classical dependency propagation, association/importance
  weighting, or a path-fused score in this script.
- A separate, genuinely classical CIA implementation exists at
  `scripts/classical_cia_baseline_v1.py` (CIA-1H / CIA-2H hop-bounded dependency closures,
  `reports/CLASSICAL_CIA_BASELINE_V1_REPORT.md`), but that is a DIFFERENT baseline and is NOT
  what the Route-B V2 frozen ranker calls `CIA`.
- **Conclusion:** the label `Classical-CIA` OVERSTATES the frozen Route-B V2 arm. Precise name:
  **`BM25+Graph-Neighbor Composite (historical label: CIA)`**. Terminology is corrected in the
  confirmatory packet V2 and Proposal V1.4; the ranking formula is NOT silently changed before
  confirmatory testing.

## 6. Incremental-evidence ablation (summary pointer)

See `reports/ROUTE_B_INCREMENTAL_EVIDENCE_ABLATION.md` for composite-vs-BM25 paired deltas,
bootstrap CIs, top-B overlap, and additional-FN recovery on both repositories.

Full machine-readable audit: `research/transparency/route_b_ranker_identity_audit.json`.