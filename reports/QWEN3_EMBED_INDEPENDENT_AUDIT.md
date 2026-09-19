# Qwen3-Embedding Contamination Bridge — Independent Preflight Audit

**Overall: PASS** (10/10)

| # | Check | PASS | Detail |
|---:|---|:---:|---|
| A1 | availability verdict (corrected embeddings-catalog probe) == available | PASS | catalog n=33, pinned=DeepInfra |
| A2 | no full scientific run produced (no metrics.json) | PASS | determinism stop before the full run |
| A12 | determinism stop evidence (drift ~1e-4; file B=5 flip on 1/5 tasks) | PASS | max_drift=9.61e-05, b5_overlap=[1.0, 1.0, 1.0, 0.8, 1.0] |
| A3 | budget JSON internally consistent (live $0.01/M price; expected $0.2188; $0.50 ceiling) | PASS | expected_cost=0.2188 |
| A4 | budget JSON status reflects STOP (not executing) | PASS | FROZEN_WITH_LIVE_PRICING; TECHNICAL PROBES EXECUTED; FULL RUN STOPPED (DETERMINISM) |
| A5 | sealed sets identified from split metadata (59 RESERVE / 80 INTERNAL_TEST), no outcome read | PASS | {"djangocms": {"DEV_TRAIN": 120, "DEV_VALIDATION": 30, "INTERNAL_TEST": 80, "RESERVE": 59}, "saleor": {"RESERVE": 1086, "DEV_TRAIN": 120, "DEV_VALIDATION": 30, "INTERNAL_TEST": 80}} |
| A6 | client frozen model id == requested model | PASS | qwen/qwen3-embedding-8b |
| A7 | no-fallback + provider pin present in client source | PASS | no-fallback + pinned provider |
| A8 | frozen numeric gate (A–H) + determinism criterion present | PASS | numeric gate A–H |
| A9 | provenance V2 verdict C unchanged | PASS | verdict C |

This audit does NOT import the bridge analyzer/evaluation code; it verifies recorded artifacts and reads the client source text only.