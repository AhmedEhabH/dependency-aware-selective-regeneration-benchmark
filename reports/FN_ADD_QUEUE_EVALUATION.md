# FN ADD-Queue Evaluation (matched budget, DEVELOPMENT)

**Date:** 2026-09-18  **Tier:** T3 (ZERO API)  **Data:** djangoCMS DEV 174 + Saleor DEV 149

Queue formulas (frozen, deterministic, no hidden-proxy features; tie-break = desc score then asc path):

| ID | Formula | Rationale |
|---|---|---|
| Q1 BM25+ReverseDependency | score = bm25 + consumer | S006-like downstream consumers (taxonomy D, 16.8%/18.4% primary) |
| Q2 BM25+ProviderConsumerSupport | score = bm25 + consumer + provider | directed dependency support (taxonomy D+E) |
| Q3 BM25+ComplementaryUnion | score = bm25 + 2hop + co-change + sibling | INDIRECT_2HOP + HISTORY + STRUCTURAL_SIBLING union |

**IMPORTANT — View A vs View B:** a queue may raise ORR while naive union F1 falls (FP additions).
Both views are reported; superiority is claimed only on View A with View B not clearly worse.

## djangoCMS DEV — sparse baseline + route-B

Sparse: TP 125 FP 155 FN 382 F1 0.3177

| B | Route-B ORR | Random ORR | BM25 ORR | Oracle-Add F1 |
|---|---:|---:|---:|---:|
| 1 | 0.046 | 0.006 | 0.046 | 0.592 |
| 3 | 0.118 | 0.019 | 0.113 | 0.796 |
| 5 | 0.163 | 0.032 | 0.161 | 0.841 |
| 10 | 0.251 | 0.065 | 0.226 | 0.867 |

### djangoCMS DEV — queue View A (macro ORR) + View B (naive union F1) + View C (oracle reviewer F1)

| B | Ranker | ORR | unique FN vs Route-B | naive union F1 | oracle reviewer F1 |
|---|---:|---:|---:|---:|---:|
| 1 | Route-B | 0.046 | - | 0.295 | 0.353 |
| 1 | BM25 | 0.046 | - | 0.293 | 0.351 |
| 1 | BM25+ReverseDependency | 0.047 | 4 | 0.298 | 0.355 |
| 1 | BM25+ProviderConsumerSupport | 0.039 | 4 | 0.295 | 0.353 |
| 1 | BM25+ComplementaryUnion | 0.020 | 6 | 0.275 | 0.333 |
| 3 | Route-B | 0.118 | - | 0.257 | 0.405 |
| 3 | BM25 | 0.113 | - | 0.249 | 0.395 |
| 3 | BM25+ReverseDependency | 0.114 | 8 | 0.258 | 0.407 |
| 3 | BM25+ProviderConsumerSupport | 0.112 | 9 | 0.257 | 0.405 |
| 3 | BM25+ComplementaryUnion | 0.056 | 14 | 0.226 | 0.365 |
| 5 | Route-B | 0.163 | - | 0.226 | 0.441 |
| 5 | BM25 | 0.161 | - | 0.220 | 0.431 |
| 5 | BM25+ReverseDependency | 0.152 | 10 | 0.227 | 0.442 |
| 5 | BM25+ProviderConsumerSupport | 0.139 | 10 | 0.220 | 0.431 |
| 5 | BM25+ComplementaryUnion | 0.077 | 15 | 0.188 | 0.381 |
| 10 | Route-B | 0.251 | - | 0.179 | 0.509 |
| 10 | BM25 | 0.226 | - | 0.170 | 0.490 |
| 10 | BM25+ReverseDependency | 0.233 | 8 | 0.176 | 0.502 |
| 10 | BM25+ProviderConsumerSupport | 0.239 | 20 | 0.174 | 0.499 |
| 10 | BM25+ComplementaryUnion | 0.155 | 22 | 0.146 | 0.437 |
## Saleor DEV — sparse baseline + route-B

Sparse: TP 99 FP 193 FN 369 F1 0.2605

| B | Route-B ORR | Random ORR | BM25 ORR | Oracle-Add F1 |
|---|---:|---:|---:|---:|
| 1 | 0.077 | 0.002 | 0.072 | 0.510 |
| 3 | 0.158 | 0.004 | 0.158 | 0.710 |
| 5 | 0.237 | 0.007 | 0.234 | 0.782 |
| 10 | 0.317 | 0.015 | 0.315 | 0.827 |

### Saleor DEV — queue View A (macro ORR) + View B (naive union F1) + View C (oracle reviewer F1)

| B | Ranker | ORR | unique FN vs Route-B | naive union F1 | oracle reviewer F1 |
|---|---:|---:|---:|---:|---:|
| 1 | Route-B | 0.077 | - | 0.273 | 0.316 |
| 1 | BM25 | 0.072 | - | 0.268 | 0.312 |
| 1 | BM25+ReverseDependency | 0.072 | 3 | 0.273 | 0.316 |
| 1 | BM25+ProviderConsumerSupport | 0.085 | 9 | 0.282 | 0.325 |
| 1 | BM25+ComplementaryUnion | 0.008 | 0 | 0.222 | 0.265 |
| 3 | Route-B | 0.158 | - | 0.257 | 0.380 |
| 3 | BM25 | 0.158 | - | 0.257 | 0.380 |
| 3 | BM25+ReverseDependency | 0.160 | 6 | 0.260 | 0.384 |
| 3 | BM25+ProviderConsumerSupport | 0.171 | 11 | 0.262 | 0.386 |
| 3 | BM25+ComplementaryUnion | 0.024 | 0 | 0.172 | 0.272 |
| 5 | Route-B | 0.237 | - | 0.236 | 0.424 |
| 5 | BM25 | 0.234 | - | 0.234 | 0.420 |
| 5 | BM25+ReverseDependency | 0.238 | 10 | 0.239 | 0.428 |
| 5 | BM25+ProviderConsumerSupport | 0.235 | 15 | 0.239 | 0.428 |
| 5 | BM25+ComplementaryUnion | 0.027 | 0 | 0.141 | 0.276 |
| 10 | Route-B | 0.317 | - | 0.187 | 0.482 |
| 10 | BM25 | 0.315 | - | 0.187 | 0.482 |
| 10 | BM25+ReverseDependency | 0.288 | 7 | 0.180 | 0.470 |
| 10 | BM25+ProviderConsumerSupport | 0.287 | 17 | 0.182 | 0.473 |
| 10 | BM25+ComplementaryUnion | 0.036 | 0 | 0.100 | 0.290 |

## Oracle-Add reference (perfect add, zero FP)

| Repo | B | F1 |
|---|---:|---:|
| djangoCMS | 1 | 0.592 |
| djangoCMS | 3 | 0.796 |
| djangoCMS | 5 | 0.841 |
| djangoCMS | 10 | 0.867 |
| Saleor | 1 | 0.510 |
| Saleor | 3 | 0.710 |
| Saleor | 5 | 0.782 |
| Saleor | 10 | 0.827 |

Machine-readable: reports/fn_add_queue_evaluation.json