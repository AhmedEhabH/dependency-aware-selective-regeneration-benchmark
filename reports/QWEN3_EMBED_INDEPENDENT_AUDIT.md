# Qwen3-Embedding Contamination Bridge — Independent Preflight Audit

**Overall: PASS** (9/9)

| # | Check | PASS | Detail |
|---:|---|:---:|---|
| A1 | model availability verdict == STOP before call 1 | PASS | catalog n=447, embedding models=0 |
| A2 | no paid scientific call made | PASS | recorded 0 calls / $0.00 |
| A3 | budget JSON internally consistent (tokens, batching, $0.50 ceiling) | PASS | {"unit_requests_at_batch64": 777, "query_requests_at_batch64": 6, "total_requests": 783} |
| A4 | budget JSON marked NOT EXECUTED | PASS | FROZEN_BUT_NOT_EXECUTED |
| A5 | sealed sets identified from split metadata (59 RESERVE / 80 INTERNAL_TEST), no outcome read | PASS | {"djangocms": {"DEV_TRAIN": 120, "DEV_VALIDATION": 30, "INTERNAL_TEST": 80, "RESERVE": 59}, "saleor": {"RESERVE": 1086, "DEV_TRAIN": 120, "DEV_VALIDATION": 30, "INTERNAL_TEST": 80}} |
| A6 | client frozen model id == requested model | PASS | qwen/qwen3-embedding-8b |
| A7 | no-fallback enforcement present in client source | PASS | no-fallback guard in constructor |
| A8 | frozen gate (A–J) + inconclusive label present in protocol | PASS | gate A–J + CASE E label |
| A9 | provenance V2 verdict C unchanged | PASS | verdict C |

This audit does NOT import the bridge analyzer/evaluation code; it verifies recorded artifacts and reads the client source text only.