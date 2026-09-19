# SweRank DEV Study + Stage-4b Closure — Independent Audit

**Overall: PASS** (11/11)

| # | Check | PASS | Detail |
|---:|---|:---:|---|
| S1 | metric formulas (P/R/F1/FNR) recompute from TP/FP/FN | PASS | recomputed from metrics.json B=5 |
| S2 | macro ORR recomputed from raw rankings @B=5 | PASS | swe/routeb/bm25 x both repos |
| S3 | pooled final P/R/F1/FNR recomputed from raw rankings @B=5 | PASS | swe/routeb/bm25 x both repos |
| S4 | frozen gate A-E recomputed from raw rankings | PASS | both repos + folds |
| S5 | paired bootstrap CI deterministic under fixed seed | PASS | djangocms final_f1 mini-bootstrap [0.0285,0.0810] |
| S6 | leakage surface: query hashes + real paths + fn subset of proxy | PASS | 60-task sample |
| S7 | deterministic ranking inputs (stable unit manifest) | PASS | unit_manifest keys |
| S8 | pinned model revision + license | PASS | 745d2a06103a66d3cfa600aa52fc0d3523010daa |
| S9 | zero API calls / zero API cost | PASS | {"api_calls": 0, "api_cost_usd": 0.0, "model_load_seconds": 17.59, "materialize_seconds": 901.39, "encode_seconds": 23907.77, "per_task_scoring_seconds": 32.42, "total_seconds": 24877.09, "distinct_blobs": 14807, "distinct_units": 49705, "missing_blobs": 0, "cached_unit_embeddings": 49705, "embedding_cache_bytes": 152693888, "per_query_seconds_est": 74.1182} |
| S10 | Stage-4b closure reproduces frozen pilot point estimates | PASS | both repos @B=5 |
| S11 | Stage-4b preregistered verdict unchanged | PASS | PRECISION_SAFE_ACCEPTANCE_FAIL |

This audit does NOT import any analyzer module; every headline number is recomputed from the raw JSON artifacts with std-lib + numpy.