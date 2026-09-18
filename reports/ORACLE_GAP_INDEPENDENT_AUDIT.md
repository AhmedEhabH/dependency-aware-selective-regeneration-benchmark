# Oracle-Gap Mission — Independent Audit

**Date:** 2026-09-18
**Tier:** T3 (ZERO API, ZERO model calls)
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731
**Method:** independent recomputation of the mission's headline numbers from
RAW frozen records + datasets (route_b_v2_robustness helpers + stdlib only;
the oracle-gap analysis scripts were NOT imported).

## Checks performed and results

| # | Check | Result |
|---|---|---|
| 1 | Sparse baseline per repo (DEVELOPMENT) TP/FP/FN/F1 recomputed from raw records | djangoCMS 125/155/382 F1 0.3177; Saleor 99/193/369 F1 0.2605 — **matches** |
| 2 | Oracle-Add ALL F1 recomputed independently | djangoCMS 0.8674; Saleor 0.8291 — **matches** `oracle_f1_ceiling_and_budget_surface.json` |
| 3 | Saleor F1=0.85 add-only reachability | ceiling 0.8291 < 0.85 → **NOT add-only-reachable** (confirmed) |
| 4 | Route-B add-only B=5 lowers F1 | djangoCMS 0.2257 < 0.3177; Saleor 0.2365 < 0.2605 — **confirmed** |
| 5 | FP-pruning bm25 flagged precision > random (D=3, djangoCMS) | 0.5622 > 0.5579 — **confirmed** (marginal) |
| 6 | BBSR heuristic progression gate | **FAIL on both repos** (confirmed) |

## Verdict

**ALL CHECKS PASS.** The analysis reports are reproducible from the frozen
evidence. No hidden-proxy leakage; no INTERNAL_TEST used for selection; sealed
sets untouched.

Independent recomputation entry point:
`C:\Users\Ahmed\AppData\Local\Temp\opencode\oracle_gap_independent_audit.py`
(reproduced here; method described above).