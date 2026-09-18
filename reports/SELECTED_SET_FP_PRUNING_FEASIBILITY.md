# Selected-Set FP-Pruning Feasibility (ZERO-LLM, DEVELOPMENT)

**Date:** 2026-09-18
**Tier:** T3 (ZERO API, ZERO model calls)
**Mission:** OPENCODE_ORACLE_GAP_BIDIRECTIONAL_REPAIR_MISSION_2026-09-18
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731
**Data:** djangoCMS DEV (174) + Saleor DEV (149). Machine-readable:
`reports/selected_set_fp_pruning_feasibility.json`.

**Purpose:** test whether cheap observable evidence identifies likely false
positives among files the Sparse first pass SELECTED, enabling a bounded DROP
queue. Features are parent-visible only (intent↔file BM25, path-token overlap,
graph-neighbor support, composite = BM25 + graph). **No hidden proxy in any
feature; no neural/RL; no API.**

---

## 1. Selected-set composition

| Repo | selected files | true FPs | FP rate |
|---|---:|---:|---:|
| djangoCMS DEV | 280 | 155 | 0.5536 |
| Saleor DEV | 292 | 193 | 0.6610 |

The Sparse selected set is majority-FP on both repos.

## 2. Observable-rank flagging precision (D = 3, lowest score dropped first)

| Repo | ranker | flagged | flagged-FP | flagged precision | TP-loss risk | final F1 (heuristic) |
|---|---:|---:|---:|---:|---:|---:|
| djangoCMS | bm25 | 233 | 131 | 0.5622 | 0.4378 | 0.1106 |
| djangoCMS | composite | 233 | 133 | 0.5708 | 0.4292 | 0.1202 |
| djangoCMS | pt_overlap | 233 | 131 | 0.5622 | 0.4378 | 0.1067 |
| djangoCMS | graph_neighbor | 233 | 130 | 0.5579 | 0.4421 | 0.1000 |
| djangoCMS | random (control) | 233 | 130 | 0.5579 | 0.4421 | 0.1058 |
| Saleor | bm25 | 217 | 139 | 0.6406 | 0.3594 | 0.1027 |
| Saleor | composite | 217 | 138 | 0.6359 | 0.3641 | 0.0978 |
| Saleor | random (control) | 217 | 133 | 0.6129 | 0.3871 | 0.0733 |

**Finding:** observable rankers flag FP at precision barely above the random
control (0.562–0.571 vs 0.558 on djangoCMS; 0.636–0.641 vs 0.613 on Saleor).
TP-loss risk is high (36–44% of flagged are TPs). **The observable signal is
too weak to drive a safe DROP queue** — a reviewer dropping the flagged set
would destroy more recall than it recovers precision (final F1 collapses to
~0.10–0.12 vs 0.32/0.26 Sparse).

## 3. Oracle-Drop upper bound (informative only)

| D | djangoCMS F1 | Saleor F1 |
|---|---:|---:|
| 1 | 0.3561 | 0.2907 |
| 2 | 0.3782 | 0.3108 |
| 3 | 0.3876 | 0.3220 |
| 5 | 0.3943 | 0.3350 |

If the reviewer dropped ONLY true FPs (never a TP), F1 rises only to ~0.39
(djangoCMS) / ~0.34 (Saleor) because recall is pinned at the Sparse first-pass
value. **Even a perfect DROP oracle does not fix the dominant recall bottleneck.**

## 4. Conclusion (Section 4)

- **Simple transparent FP-pruning has limited signal on DEVELOPMENT:** flagged
  precision ≈ random control; TP-loss risk is high.
- **DROP-side correction alone is insufficient** (oracle ceiling ~0.35–0.40).
- The FP tail matters only as a *cap* on the add-only ceiling (Section 5 of the
  ceiling report): F1 0.85 on Saleor requires *some* FP removal, but the cheap
  observable rankers here cannot deliver it safely.
- No deployment claim is made; heuristic no-review behavior is reported as a
  diagnostic only.

Machine-readable: `reports/selected_set_fp_pruning_feasibility.json`.