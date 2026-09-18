# FN Taxonomy — DEVELOPMENT (deterministic)

**Date:** 2026-09-18  **Tier:** T3 (ZERO API)  **Data:** djangoCMS DEV 174 + Saleor DEV 149

Classifier input: parent-visible features only (intent text, universe metadata,
dependency graph, djangocms ancestors-of-parent co-change). The hidden proxy is used
ONLY to identify FN files after the fact. Multi-label allowed; one primary per file.

| Category | Code | Meaning |
|---|---|---|
| DIRECT_LEXICAL | A | path/module/symbol overlaps change intent |
| DIRECT_DEPENDENCY | B | 1-hop undirected edge to/from a seed |
| INDIRECT_DEPENDENCY_2HOP | C | reachable in 2 hops, not 1 |
| DOWNSTREAM_CONSUMER | D | imports a seed, lexically distant |
| UPSTREAM_PROVIDER | E | imported by a seed, lexically distant |
| CROSS_LAYER | F | shared concern across layers, no 1/2-hop edge |
| HISTORY_COCHANGE | G | co-changed with write set in parent ancestors |
| STRUCTURAL_NEIGHBOR | H | same parent dir/module as a seed, no stronger evidence |
| NO_OBSERVABLE_SIGNAL | I | no cheap evidence exposes the file |

## djangocms DEV — primary reason counts

| Primary | Count | % of FN |
|---|---:|---:|
| DOWNSTREAM_CONSUMER | 64 | 16.8 |
| UPSTREAM_PROVIDER | 6 | 1.6 |
| DIRECT_DEPENDENCY | 1 | 0.3 |
| INDIRECT_DEPENDENCY_2HOP | 43 | 11.3 |
| HISTORY_COCHANGE | 86 | 22.5 |
| DIRECT_LEXICAL | 95 | 24.9 |
| CROSS_LAYER | 0 | 0.0 |
| STRUCTURAL_NEIGHBOR | 0 | 0.0 |
| NO_OBSERVABLE_SIGNAL | 87 | 22.8 |

Total FN: **382** over 174 tasks (153 with >=1 FN).

### Graph-distance distribution (djangocms)

| dist | count |
|---:|---:|
| -1 | 79 |
| 0 | 181 |
| 1 | 71 |
| 2 | 43 |
| 3 | 5 |
| 4 | 3 |

### Lexical (normalized BM25) distribution (djangocms)

| BM25 bin | count |
|---|---:|
| [0.000,0.001) | 201 |
| [0.100,0.250) | 26 |
| [0.250,0.500) | 58 |
| [0.750,1.000) | 30 |
| [0.500,0.750) | 33 |
| [0.001,0.100) | 34 |

### Per-task FN count distribution (djangocms)

| FNs/task | tasks |
|---:|---:|
| 0 | 21 |
| 1 | 51 |
| 2 | 44 |
| 3 | 32 |
| 4 | 10 |
| 5 | 3 |
| 6 | 3 |
| 7 | 6 |
| 8 | 4 |
## saleor DEV — primary reason counts

| Primary | Count | % of FN |
|---|---:|---:|
| DOWNSTREAM_CONSUMER | 68 | 18.4 |
| UPSTREAM_PROVIDER | 9 | 2.4 |
| DIRECT_DEPENDENCY | 0 | 0.0 |
| INDIRECT_DEPENDENCY_2HOP | 21 | 5.7 |
| HISTORY_COCHANGE | 0 | 0.0 |
| DIRECT_LEXICAL | 264 | 71.5 |
| CROSS_LAYER | 0 | 0.0 |
| STRUCTURAL_NEIGHBOR | 1 | 0.3 |
| NO_OBSERVABLE_SIGNAL | 6 | 1.6 |

Total FN: **369** over 149 tasks (127 with >=1 FN).

### Graph-distance distribution (saleor)

| dist | count |
|---:|---:|
| -1 | 2 |
| 0 | 264 |
| 1 | 77 |
| 2 | 21 |
| 3 | 5 |

### Lexical (normalized BM25) distribution (saleor)

| BM25 bin | count |
|---|---:|
| [0.750,1.000) | 58 |
| [0.500,0.750) | 71 |
| [0.250,0.500) | 79 |
| [0.000,0.001) | 118 |
| [0.100,0.250) | 39 |
| [0.001,0.100) | 4 |

### Per-task FN count distribution (saleor)

| FNs/task | tasks |
|---:|---:|
| 0 | 22 |
| 1 | 44 |
| 2 | 28 |
| 3 | 20 |
| 4 | 10 |
| 5 | 10 |
| 6 | 3 |
| 7 | 5 |
| 8 | 2 |
| 9 | 2 |
| 10 | 1 |
| 11 | 2 |

## S006-like indirect-utility / downstream-miss pattern test

| Metric | djangoCMS | Saleor |
|---|---:|---:|
| % FN with downstream-consumer flag | 58.9 | 82.1 |
| % FN with upstream-provider flag | 43.7 | 71.5 |
| % FN consumer OR provider (raw) | 64.7 | 91.1 |
| % FN primary DOWNSTREAM_CONSUMER | 16.8 | 18.4 |
| % FN primary UPSTREAM_PROVIDER | 1.6 | 2.4 |
| direct-1-hop FN count | 71 | 77 |
| direct-1-hop lexically silent % | 98.6 | 100.0 |
| downstream-consumer lexical-disconnect % | 100.0 | 100.0 |

**Decision: GENERAL_PATTERN**

Evidence: {"djangocms_consumer_or_provider_pct": 64.66, "saleor_consumer_or_provider_pct": 91.06, "djangocms_direct_1hop_lexically_silent_pct": 98.59, "saleor_direct_1hop_lexically_silent_pct": 100.0}

Machine-readable: reports/fn_taxonomy_development.json