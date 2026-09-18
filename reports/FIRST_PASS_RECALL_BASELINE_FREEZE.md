# First-Pass Recall Baseline Freeze

**Date:** 2026-09-18  **Tier:** T3 (ZERO API, ZERO model calls)
**Data:** djangoCMS DEVELOPMENT (174) + Saleor DEVELOPMENT (149), frozen artifacts only.

## 1. Sparse baseline per repo (first-succeeded-rep write set)

| Repo | n | TP | FP | FN | P | R | F1 | FNR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| djangocms DEV | 174 | 125 | 155 | 382 | 0.4464 | 0.2465 | 0.3177 | 0.7535 |
| saleor DEV | 149 | 99 | 193 | 369 | 0.3390 | 0.2115 | 0.2605 | 0.7885 |

Known-diagnostic verification (FN):
- djangocms: recomputed FN **382** vs known **382** -> MATCH.
- saleor: recomputed FN **369** vs known **369** -> MATCH.

## 2. Route-B fixed-B composite (macro ORR)

| Repo | B=1 | B=3 | B=5 | B=10 |
|---|---:|---:|---:|---:|
| djangocms | 0.0464 | 0.1177 | 0.1633 | 0.2512 |
| saleor | 0.0775 | 0.1576 | 0.2369 | 0.3173 |

## 3. Per-task FN universe

Per-task FN file sets, candidate universes, and proxy sets are persisted in `reports/first_pass_recall_baseline_freeze.json` and `research/first-pass-recall-bottleneck/fn_universe.json`.

## 4. Notes

- First-succeeded-rep write set is the frozen Sparse first pass.
- The hidden proxy identifies FN files ONLY after the fact (evaluation-only).
- No INTERNAL_TEST / RESERVE set is loaded.