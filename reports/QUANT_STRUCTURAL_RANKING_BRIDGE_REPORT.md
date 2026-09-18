# Quantitative-Structural Ranking Bridge (DEVELOPMENT, ZERO API)

**Date:** 2026-09-18  **Tier:** T3  **Data:** djangoCMS DEV 174 + Saleor DEV 149

## Section 1 — ranking-gap reconfirmation freeze

| Repo | n | Sparse F1 | Route-B ORR@1/3/5/10 | BM25 ORR@5 | rev-1hop avail@5 | cons+prov avail@5 | UNION_ALL avail@5 | Oracle-Add F1@5 | oracle-reviewer F1@5 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| djangoCMS | 174 | 0.318 | 0.046 / 0.118 / 0.163 / 0.251 | 0.161 | 0.558 | 0.605 | 0.725 | 0.841 | 0.441 |
| Saleor | 149 | 0.261 | 0.077 / 0.158 / 0.237 / 0.317 | 0.234 | 0.724 | 0.802 | 0.870 | 0.782 | 0.424 |

Verification vs frozen numbers: 
- djangoCMS: route-B exact B=1 OK, B=3 OK, B=5 OK, B=10 OK; reverse-1hop OK; UNION_ALL OK; Oracle-Add OK; oracle-reviewer OK
- Saleor: route-B exact B=1 OK, B=3 OK, B=5 OK, B=10 OK; reverse-1hop OK; UNION_ALL OK; Oracle-Add OK; oracle-reviewer OK

## Section 2 — three transparent quantitative-structural rankers

Formulas (frozen before outcome inspection; feature provenance in `src/benchmark/recall/quant_rankers.py`):

| ID | Formula |
|---|---|
| R1 BM25+RevSupport | score = bm25 + rev_norm (normalized reverse-seed-support count) |
| R2 BM25+BidirSupport | score = bm25 + rev_norm + fwd_norm (both directions) |
| R3 BM25+BidirNorm | score = bm25 + bidir_norm (single combined bidirectional term) |

Typed-edge support is NOT used (frozen graph exposes only untyped [src,dest] edges).

### djangoCMS DEV @B=5

| Ranker | ORR | dORR vs Route-B | cand. precision | unique FN > Route-B | naive union F1 | oracle-reviewer F1 | folds+ | artifact-free |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| R1_BM25+RevSupport | 0.197 | +0.034 | 0.092 | 38 | 0.247 | 0.473 | 2/5 | True |
| R2_BM25+BidirSupport | 0.193 | +0.030 | 0.083 | 29 | 0.238 | 0.459 | 1/5 | True |
| R3_BM25+BidirNorm | 0.185 | +0.022 | 0.081 | 22 | 0.235 | 0.455 | 0/5 | True |

### Saleor DEV @B=5

| Ranker | ORR | dORR vs Route-B | cand. precision | unique FN > Route-B | naive union F1 | oracle-reviewer F1 | folds+ | artifact-free |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| R1_BM25+RevSupport | 0.217 | -0.020 | 0.109 | 30 | 0.239 | 0.428 | 0/5 | True |
| R2_BM25+BidirSupport | 0.217 | -0.020 | 0.103 | 31 | 0.234 | 0.420 | 0/5 | True |
| R3_BM25+BidirNorm | 0.209 | -0.028 | 0.094 | 20 | 0.225 | 0.407 | 0/5 | True |

## Gate decision

**CHEAP_RANKING_CLOSED_FOR_NOW**

| Ranker | c1 ORR>+0.05 both | c2 folds both | c3 naive-F1 ok | c4 artifact-free | c5 no-leak | c6 simpler | PASS |
|---|---:|---:|---:|---:|---:|---:|---:|
| R1_BM25+RevSupport | False | False | True | True | True | True | False |
| R2_BM25+BidirSupport | False | False | True | True | True | True | False |
| R3_BM25+BidirNorm | False | False | True | True | True | True | False |

Machine-readable: reports/fn_quant_ranking_bridge.json, reports/fn_quant_ranking_bridge_gates.json, reports/fn_quant_ranking_bridge_baseline_freeze.json