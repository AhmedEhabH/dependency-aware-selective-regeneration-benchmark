# FN Source-Specific Recall Ceilings + Complementarity

**Date:** 2026-09-18  **Tier:** T3 (ZERO API)  **Data:** djangoCMS DEV 174 + Saleor DEV 149

Oracle-Recall ceiling = max FNs a source can surface at budget K if its ranking
were perfect among the candidates its deterministic pool can emit. The hidden proxy
is never used in a pool or ranking.

## Section 4 — Oracle ceilings per source

### djangoCMS DEV (total FN = 382)

| Source | K | ORR ceil | FN rec | queue/task | Route-B rec | overlap | unique | Random ORR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25 | 1 | 0.401 | 153 | 1.00 | 17 | 17 | 136 | 0.006 |
| BM25 | 3 | 0.819 | 313 | 3.00 | 43 | 43 | 270 | 0.019 |
| BM25 | 5 | 0.929 | 355 | 5.00 | 62 | 62 | 293 | 0.032 |
| BM25 | 10 | 1.000 | 382 | 10.00 | 101 | 101 | 281 | 0.065 |
| BM25 | ALL | 1.000 | 382 | 159.87 | 382 | 382 | 0 | 1.000 |
| PATH_TOKEN | 1 | 0.401 | 153 | 1.00 | 17 | 17 | 136 | 0.006 |
| PATH_TOKEN | 3 | 0.819 | 313 | 3.00 | 43 | 43 | 270 | 0.019 |
| PATH_TOKEN | 5 | 0.929 | 355 | 5.00 | 62 | 62 | 293 | 0.032 |
| PATH_TOKEN | 10 | 1.000 | 382 | 10.00 | 101 | 101 | 281 | 0.065 |
| PATH_TOKEN | ALL | 1.000 | 382 | 159.87 | 382 | 382 | 0 | 1.000 |
| GRAPH_1HOP | 1 | 0.126 | 48 | 0.82 | 17 | 1 | 47 | 0.005 |
| GRAPH_1HOP | 3 | 0.183 | 70 | 2.43 | 43 | 4 | 66 | 0.015 |
| GRAPH_1HOP | 5 | 0.186 | 71 | 3.80 | 62 | 5 | 66 | 0.024 |
| GRAPH_1HOP | 10 | 0.186 | 71 | 6.88 | 101 | 16 | 55 | 0.042 |
| GRAPH_1HOP | ALL | 0.186 | 71 | 31.84 | 382 | 71 | 0 | 0.191 |
| GRAPH_REVERSE_1HOP | 1 | 0.264 | 101 | 0.83 | 17 | 14 | 87 | 0.005 |
| GRAPH_REVERSE_1HOP | 3 | 0.495 | 189 | 2.44 | 43 | 36 | 153 | 0.015 |
| GRAPH_REVERSE_1HOP | 5 | 0.558 | 213 | 4.04 | 62 | 52 | 161 | 0.025 |
| GRAPH_REVERSE_1HOP | 10 | 0.589 | 225 | 7.94 | 101 | 84 | 141 | 0.050 |
| GRAPH_REVERSE_1HOP | ALL | 0.589 | 225 | 53.61 | 382 | 225 | 0 | 0.351 |
| GRAPH_FORWARD_1HOP | 1 | 0.223 | 85 | 0.82 | 17 | 15 | 70 | 0.005 |
| GRAPH_FORWARD_1HOP | 3 | 0.387 | 148 | 2.43 | 43 | 36 | 112 | 0.015 |
| GRAPH_FORWARD_1HOP | 5 | 0.424 | 162 | 4.01 | 62 | 49 | 113 | 0.025 |
| GRAPH_FORWARD_1HOP | 10 | 0.437 | 167 | 7.85 | 101 | 66 | 101 | 0.049 |
| GRAPH_FORWARD_1HOP | ALL | 0.437 | 167 | 47.47 | 382 | 167 | 0 | 0.318 |
| GRAPH_2HOP | 1 | 0.065 | 25 | 0.77 | 17 | 0 | 25 | 0.005 |
| GRAPH_2HOP | 3 | 0.105 | 40 | 2.19 | 43 | 0 | 40 | 0.013 |
| GRAPH_2HOP | 5 | 0.113 | 43 | 3.43 | 62 | 0 | 43 | 0.021 |
| GRAPH_2HOP | 10 | 0.113 | 43 | 6.51 | 101 | 0 | 43 | 0.039 |
| GRAPH_2HOP | ALL | 0.113 | 43 | 29.97 | 382 | 43 | 0 | 0.174 |
| GRAPH_REVERSE_2HOP | 1 | 0.000 | 0 | 0.00 | 17 | 0 | 0 | 0.000 |
| GRAPH_REVERSE_2HOP | 3 | 0.000 | 0 | 0.00 | 43 | 0 | 0 | 0.000 |
| GRAPH_REVERSE_2HOP | 5 | 0.000 | 0 | 0.00 | 62 | 0 | 0 | 0.000 |
| GRAPH_REVERSE_2HOP | 10 | 0.000 | 0 | 0.00 | 101 | 0 | 0 | 0.000 |
| GRAPH_REVERSE_2HOP | ALL | 0.000 | 0 | 0.00 | 382 | 0 | 0 | 0.000 |
| HISTORY_COCHANGE | 1 | 0.141 | 54 | 0.64 | 17 | 4 | 50 | 0.004 |
| HISTORY_COCHANGE | 3 | 0.262 | 100 | 1.84 | 43 | 14 | 86 | 0.011 |
| HISTORY_COCHANGE | 5 | 0.293 | 112 | 2.94 | 62 | 23 | 89 | 0.018 |
| HISTORY_COCHANGE | 10 | 0.301 | 115 | 5.46 | 101 | 37 | 78 | 0.035 |
| HISTORY_COCHANGE | ALL | 0.301 | 115 | 27.87 | 382 | 115 | 0 | 0.189 |
| STRUCTURAL_SIBLING | 1 | 0.280 | 107 | 0.84 | 17 | 16 | 91 | 0.005 |
| STRUCTURAL_SIBLING | 3 | 0.518 | 198 | 2.52 | 43 | 39 | 159 | 0.016 |
| STRUCTURAL_SIBLING | 5 | 0.579 | 221 | 4.19 | 62 | 56 | 165 | 0.026 |
| STRUCTURAL_SIBLING | 10 | 0.615 | 235 | 8.33 | 101 | 83 | 152 | 0.052 |
| STRUCTURAL_SIBLING | ALL | 0.615 | 235 | 82.88 | 382 | 235 | 0 | 0.525 |
| UNION_1HOP_2HOP | 1 | 0.165 | 63 | 0.82 | 17 | 1 | 62 | 0.005 |
| UNION_1HOP_2HOP | 3 | 0.275 | 105 | 2.45 | 43 | 4 | 101 | 0.016 |
| UNION_1HOP_2HOP | 5 | 0.296 | 113 | 4.02 | 62 | 5 | 108 | 0.025 |
| UNION_1HOP_2HOP | 10 | 0.298 | 114 | 7.25 | 101 | 16 | 98 | 0.045 |
| UNION_1HOP_2HOP | ALL | 0.298 | 114 | 61.81 | 382 | 114 | 0 | 0.365 |
| UNION_CONSUMER_PROVIDER | 1 | 0.285 | 109 | 0.83 | 17 | 17 | 92 | 0.005 |
| UNION_CONSUMER_PROVIDER | 3 | 0.534 | 204 | 2.48 | 43 | 43 | 161 | 0.016 |
| UNION_CONSUMER_PROVIDER | 5 | 0.605 | 231 | 4.14 | 62 | 61 | 170 | 0.026 |
| UNION_CONSUMER_PROVIDER | 10 | 0.647 | 247 | 8.24 | 101 | 96 | 151 | 0.052 |
| UNION_CONSUMER_PROVIDER | ALL | 0.647 | 247 | 69.25 | 382 | 247 | 0 | 0.453 |
| UNION_2HOP_COCHANGE_SIBLING | 1 | 0.309 | 118 | 0.84 | 17 | 16 | 102 | 0.005 |
| UNION_2HOP_COCHANGE_SIBLING | 3 | 0.600 | 229 | 2.52 | 43 | 39 | 190 | 0.016 |
| UNION_2HOP_COCHANGE_SIBLING | 5 | 0.670 | 256 | 4.19 | 62 | 57 | 199 | 0.026 |
| UNION_2HOP_COCHANGE_SIBLING | 10 | 0.709 | 271 | 8.36 | 101 | 85 | 186 | 0.052 |
| UNION_2HOP_COCHANGE_SIBLING | ALL | 0.709 | 271 | 104.76 | 382 | 271 | 0 | 0.650 |
| UNION_ALL | 1 | 0.317 | 121 | 0.84 | 17 | 17 | 104 | 0.005 |
| UNION_ALL | 3 | 0.633 | 242 | 2.52 | 43 | 43 | 199 | 0.016 |
| UNION_ALL | 5 | 0.725 | 277 | 4.19 | 62 | 61 | 216 | 0.026 |
| UNION_ALL | 10 | 0.772 | 295 | 8.36 | 101 | 96 | 199 | 0.052 |
| UNION_ALL | ALL | 0.772 | 295 | 113.57 | 382 | 295 | 0 | 0.702 |

### Saleor DEV (total FN = 369)

| Source | K | ORR ceil | FN rec | queue/task | Route-B rec | overlap | unique | Random ORR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BM25 | 1 | 0.344 | 127 | 1.00 | 25 | 25 | 102 | 0.002 |
| BM25 | 3 | 0.718 | 265 | 3.00 | 56 | 56 | 209 | 0.004 |
| BM25 | 5 | 0.881 | 325 | 5.00 | 79 | 79 | 246 | 0.007 |
| BM25 | 10 | 0.995 | 367 | 10.00 | 111 | 111 | 256 | 0.015 |
| BM25 | ALL | 1.000 | 369 | 774.92 | 369 | 369 | 0 | 1.000 |
| PATH_TOKEN | 1 | 0.344 | 127 | 1.00 | 25 | 25 | 102 | 0.002 |
| PATH_TOKEN | 3 | 0.718 | 265 | 3.00 | 56 | 56 | 209 | 0.004 |
| PATH_TOKEN | 5 | 0.881 | 325 | 5.00 | 79 | 79 | 246 | 0.007 |
| PATH_TOKEN | 10 | 0.995 | 367 | 10.00 | 111 | 111 | 256 | 0.015 |
| PATH_TOKEN | ALL | 1.000 | 369 | 774.92 | 369 | 369 | 0 | 1.000 |
| GRAPH_1HOP | 1 | 0.111 | 41 | 0.94 | 25 | 0 | 41 | 0.001 |
| GRAPH_1HOP | 3 | 0.184 | 68 | 2.82 | 56 | 0 | 68 | 0.004 |
| GRAPH_1HOP | 5 | 0.203 | 75 | 4.70 | 79 | 0 | 75 | 0.007 |
| GRAPH_1HOP | 10 | 0.209 | 77 | 9.40 | 111 | 0 | 77 | 0.014 |
| GRAPH_1HOP | ALL | 0.209 | 77 | 332.78 | 369 | 77 | 0 | 0.407 |
| GRAPH_REVERSE_1HOP | 1 | 0.306 | 113 | 0.99 | 25 | 22 | 91 | 0.002 |
| GRAPH_REVERSE_1HOP | 3 | 0.602 | 222 | 2.98 | 56 | 51 | 171 | 0.004 |
| GRAPH_REVERSE_1HOP | 5 | 0.724 | 267 | 4.96 | 79 | 70 | 197 | 0.007 |
| GRAPH_REVERSE_1HOP | 10 | 0.818 | 302 | 9.89 | 111 | 96 | 206 | 0.015 |
| GRAPH_REVERSE_1HOP | ALL | 0.821 | 303 | 363.72 | 369 | 303 | 0 | 0.474 |
| GRAPH_FORWARD_1HOP | 1 | 0.279 | 103 | 0.99 | 25 | 22 | 81 | 0.002 |
| GRAPH_FORWARD_1HOP | 3 | 0.542 | 200 | 2.98 | 56 | 49 | 151 | 0.004 |
| GRAPH_FORWARD_1HOP | 5 | 0.642 | 237 | 4.97 | 79 | 71 | 166 | 0.007 |
| GRAPH_FORWARD_1HOP | 10 | 0.713 | 263 | 9.87 | 111 | 100 | 163 | 0.015 |
| GRAPH_FORWARD_1HOP | ALL | 0.715 | 264 | 281.30 | 369 | 264 | 0 | 0.390 |
| GRAPH_2HOP | 1 | 0.027 | 10 | 0.94 | 25 | 0 | 10 | 0.001 |
| GRAPH_2HOP | 3 | 0.043 | 16 | 2.82 | 56 | 0 | 16 | 0.004 |
| GRAPH_2HOP | 5 | 0.051 | 19 | 4.70 | 79 | 0 | 19 | 0.007 |
| GRAPH_2HOP | 10 | 0.057 | 21 | 9.38 | 111 | 0 | 21 | 0.014 |
| GRAPH_2HOP | ALL | 0.057 | 21 | 192.75 | 369 | 21 | 0 | 0.227 |
| GRAPH_REVERSE_2HOP | 1 | 0.000 | 0 | 0.00 | 25 | 0 | 0 | 0.000 |
| GRAPH_REVERSE_2HOP | 3 | 0.000 | 0 | 0.00 | 56 | 0 | 0 | 0.000 |
| GRAPH_REVERSE_2HOP | 5 | 0.000 | 0 | 0.00 | 79 | 0 | 0 | 0.000 |
| GRAPH_REVERSE_2HOP | 10 | 0.000 | 0 | 0.00 | 111 | 0 | 0 | 0.000 |
| GRAPH_REVERSE_2HOP | ALL | 0.000 | 0 | 0.00 | 369 | 0 | 0 | 0.000 |
| HISTORY_COCHANGE | 1 | 0.000 | 0 | 0.00 | 25 | 0 | 0 | 0.000 |
| HISTORY_COCHANGE | 3 | 0.000 | 0 | 0.00 | 56 | 0 | 0 | 0.000 |
| HISTORY_COCHANGE | 5 | 0.000 | 0 | 0.00 | 79 | 0 | 0 | 0.000 |
| HISTORY_COCHANGE | 10 | 0.000 | 0 | 0.00 | 111 | 0 | 0 | 0.000 |
| HISTORY_COCHANGE | ALL | 0.000 | 0 | 0.00 | 369 | 0 | 0 | 0.000 |
| STRUCTURAL_SIBLING | 1 | 0.314 | 116 | 1.00 | 25 | 25 | 91 | 0.002 |
| STRUCTURAL_SIBLING | 3 | 0.610 | 225 | 3.00 | 56 | 56 | 169 | 0.004 |
| STRUCTURAL_SIBLING | 5 | 0.732 | 270 | 5.00 | 79 | 79 | 191 | 0.007 |
| STRUCTURAL_SIBLING | 10 | 0.818 | 302 | 9.97 | 111 | 111 | 191 | 0.015 |
| STRUCTURAL_SIBLING | ALL | 0.824 | 304 | 394.97 | 369 | 304 | 0 | 0.541 |
| UNION_1HOP_2HOP | 1 | 0.133 | 49 | 0.94 | 25 | 0 | 49 | 0.001 |
| UNION_1HOP_2HOP | 3 | 0.225 | 83 | 2.82 | 56 | 0 | 83 | 0.004 |
| UNION_1HOP_2HOP | 5 | 0.255 | 94 | 4.70 | 79 | 0 | 94 | 0.007 |
| UNION_1HOP_2HOP | 10 | 0.266 | 98 | 9.40 | 111 | 0 | 98 | 0.014 |
| UNION_1HOP_2HOP | ALL | 0.266 | 98 | 525.52 | 369 | 98 | 0 | 0.633 |
| UNION_CONSUMER_PROVIDER | 1 | 0.325 | 120 | 0.99 | 25 | 25 | 95 | 0.002 |
| UNION_CONSUMER_PROVIDER | 3 | 0.658 | 243 | 2.98 | 56 | 55 | 188 | 0.004 |
| UNION_CONSUMER_PROVIDER | 5 | 0.802 | 296 | 4.97 | 79 | 78 | 218 | 0.007 |
| UNION_CONSUMER_PROVIDER | 10 | 0.905 | 334 | 9.93 | 111 | 110 | 224 | 0.015 |
| UNION_CONSUMER_PROVIDER | ALL | 0.911 | 336 | 484.46 | 369 | 336 | 0 | 0.633 |
| UNION_2HOP_COCHANGE_SIBLING | 1 | 0.325 | 120 | 1.00 | 25 | 25 | 95 | 0.002 |
| UNION_2HOP_COCHANGE_SIBLING | 3 | 0.648 | 239 | 3.00 | 56 | 56 | 183 | 0.004 |
| UNION_2HOP_COCHANGE_SIBLING | 5 | 0.778 | 287 | 5.00 | 79 | 79 | 208 | 0.007 |
| UNION_2HOP_COCHANGE_SIBLING | 10 | 0.870 | 321 | 9.97 | 111 | 111 | 210 | 0.015 |
| UNION_2HOP_COCHANGE_SIBLING | ALL | 0.875 | 323 | 538.56 | 369 | 323 | 0 | 0.710 |
| UNION_ALL | 1 | 0.344 | 127 | 1.00 | 25 | 25 | 102 | 0.002 |
| UNION_ALL | 3 | 0.710 | 262 | 3.00 | 56 | 56 | 206 | 0.004 |
| UNION_ALL | 5 | 0.870 | 321 | 5.00 | 79 | 79 | 242 | 0.007 |
| UNION_ALL | 10 | 0.978 | 361 | 9.97 | 111 | 111 | 250 | 0.015 |
| UNION_ALL | ALL | 0.984 | 363 | 702.81 | 369 | 363 | 0 | 0.898 |

## Section 5 — Complementarity

### Jaccard overlap of top-K candidate queues (mean over tasks)

#### djangoCMS DEV @K=5

| | BM25 | PATH_TOKEN | ROUTE_B |
|---|---:|---:|---:|
| BM25 | 1.000 | 0.571 | 0.765 |
| PATH_TOKEN | 0.571 | 1.000 | 0.445 |
| ROUTE_B_COMPOSITE | 0.765 | 0.445 | 1.000 |

#### djangoCMS DEV @K=10

| | BM25 | PATH_TOKEN | ROUTE_B |
|---|---:|---:|---:|
| BM25 | 1.000 | 0.687 | 0.751 |
| PATH_TOKEN | 0.687 | 1.000 | 0.530 |
| ROUTE_B_COMPOSITE | 0.751 | 0.530 | 1.000 |

#### Saleor DEV @K=5

| | BM25 | PATH_TOKEN | ROUTE_B |
|---|---:|---:|---:|
| BM25 | 1.000 | 0.305 | 0.854 |
| PATH_TOKEN | 0.305 | 1.000 | 0.267 |
| ROUTE_B_COMPOSITE | 0.854 | 0.267 | 1.000 |

#### Saleor DEV @K=10

| | BM25 | PATH_TOKEN | ROUTE_B |
|---|---:|---:|---:|
| BM25 | 1.000 | 0.338 | 0.831 |
| PATH_TOKEN | 0.338 | 1.000 | 0.287 |
| ROUTE_B_COMPOSITE | 0.831 | 0.287 | 1.000 |

### FN recovery per top-K ranker

| Repo | K | BM25 ORR | PATH_TOKEN ORR | ROUTE_B ORR |
|---|---:|---:|---:|---:|
| djangoCMS | 5 | 0.149 | 0.131 | 0.162 |
| djangoCMS | 10 | 0.236 | 0.236 | 0.264 |
| Saleor | 5 | 0.209 | 0.157 | 0.214 |
| Saleor | 10 | 0.301 | 0.230 | 0.301 |

### Union-gain combos @K=5 (oracle pool ceiling; marginal FN over previous combo)

| Repo | Combo | ORR ceil | marginal FN |
|---|---:|---:|---:|
| djangoCMS | BASE_ROUTE_B_1HOP | 0.186 | 71 |
| djangoCMS | +REVERSE_1HOP | 0.573 | 148 |
| djangoCMS | +FORWARD_1HOP | 0.605 | 12 |
| djangoCMS | +2HOP | 0.712 | 41 |
| djangoCMS | +HISTORY | 0.712 | 0 |
| djangoCMS | +SIBLING | 0.725 | 5 |
| Saleor | BASE_ROUTE_B_1HOP | 0.203 | 75 |
| Saleor | +REVERSE_1HOP | 0.748 | 201 |
| Saleor | +FORWARD_1HOP | 0.802 | 20 |
| Saleor | +2HOP | 0.854 | 19 |
| Saleor | +HISTORY | 0.854 | 0 |
| Saleor | +SIBLING | 0.870 | 6 |

Machine-readable: reports/fn_source_specific_recall_ceilings.json, reports/fn_source_complementarity.json