# Classical / Static CIA Baseline V1

**Date:** 2026-09-16  **Tier:** T3  **Zero LLM cost**
**Data:** V2 development cases (N=150: 120 DEV_TRAIN + 30 DEV_VALIDATION)

## Method

- Input seed = intent-token ∩ candidate-token (frozen non-leaking rule; never the proxy).
- CIA-1H: seed ∪ 1-hop reverse-dependency closure (dependents of seeds).
- CIA-2H: 2-hop budgeted propagation.
- GRAPH@K: bounded BFS from seeds (frozen ranker).
- BM25 / PATH_TOKEN: lexical controls.
- Graph build cost (parent AST import graph, built once per case) is SEPARATED from
  query cost (seeding + propagation).

## Micro-averaged results (pooled over cases)

| Arm | K | P | R | F1 | FNR |
|---|---|---:|---:|---:|---:|
| BM25 | 1 | 0.160 | 0.054 | 0.081 | 0.946 |
| BM25 | 3 | 0.149 | 0.150 | 0.150 | 0.850 |
| BM25 | 5 | 0.116 | 0.195 | 0.145 | 0.805 |
| BM25 | 10 | 0.092 | 0.309 | 0.142 | 0.691 |
| PATH_TOKEN | 1 | 0.180 | 0.061 | 0.091 | 0.939 |
| PATH_TOKEN | 3 | 0.147 | 0.148 | 0.147 | 0.852 |
| PATH_TOKEN | 5 | 0.117 | 0.197 | 0.147 | 0.803 |
| PATH_TOKEN | 10 | 0.086 | 0.289 | 0.133 | 0.711 |
| GRAPH@K | 1 | 0.220 | 0.061 | 0.095 | 0.939 |
| GRAPH@K | 3 | 0.182 | 0.150 | 0.164 | 0.850 |
| GRAPH@K | 5 | 0.146 | 0.202 | 0.170 | 0.798 |
| GRAPH@K | 10 | 0.105 | 0.289 | 0.154 | 0.711 |
| CIA_1H | 1 | 0.081 | 0.022 | 0.035 | 0.978 |
| CIA_1H | 3 | 0.112 | 0.092 | 0.101 | 0.908 |
| CIA_1H | 5 | 0.107 | 0.146 | 0.123 | 0.854 |
| CIA_1H | 10 | 0.081 | 0.220 | 0.118 | 0.780 |
| CIA_2H | 1 | 0.081 | 0.022 | 0.035 | 0.978 |
| CIA_2H | 3 | 0.112 | 0.092 | 0.101 | 0.908 |
| CIA_2H | 5 | 0.107 | 0.146 | 0.123 | 0.854 |
| CIA_2H | 10 | 0.081 | 0.220 | 0.118 | 0.780 |

## Notes

- Development-only evidence; compared against BM25 on the same cases, NOT against P1 held-out numbers.
- CIA arms emit a variable-size selected set (closure), so K slices the ranked closure;
  fixed-K comparison keeps the lexical arms at matched output budgets.
- The historical diff remains an OBSERVED CHANGE-SET PROXY, never semantic gold.