# WP-1b MAIN-mode Review Card - VARIANCE_15x3

- items: 45/45 · status: COMPLETE · ledger USD: 1.194112
- verdict: **NO_BLOCKING_INSTRUMENT_ANOMALIES**
- AC-14 ledger reconciliation: {"abandoned_attempts": 1, "abandoned_attempts_usd": 0.025037, "kept_records_usd": 1.169076, "ledger_total_usd": 1.194112, "ok": true, "per_record_mismatches": [], "total_matches": true}

## BLOCKING (instrument-level only)

- none

## INFORMATIONAL (agent behaviour = data, never blocking)

- resolved_halts_before_completion: []
- empty_by_reason: {}
- empty_rate: 0.0
- forced_final_items: 26
- calls_histogram: {"3": 1, "4": 2, "5": 3, "7": 13, "8": 26}
- items_with_zero_reads: 21
- mean_successful_reads: 1.0222222222222221
- rejected_repeat_share_of_calls: 0.16307692307692306
- items_with_rejected_repeats: 23
- instrument_error_items: 0
- infra_failure_items: 0
- transport_retries: 6
- http_attempts: 331
- logical_calls: 325
- cost_ratio_to_worst_case: {"items_above_1": 0, "max": 0.6981107016592155, "mean": 0.5658991322514836}
- usd_per_item: {"mean": 0.025979460000000003, "median": 0.028544599999999996}
- tool_quality_X11: {"multi_word_search_share": 0.29878048780487804, "multi_word_zero_result_share": 0.5918367346938775, "non_consecutive_duplicate_requests": 23, "non_consecutive_duplicate_share": 0.1013215859030837, "note": "search_text is a case-insensitive SUBSTRING match of the whole query; the frozen rejection rule only rejects CONSECUTIVE identical requests.", "search_calls": 164, "tool_calls_executed": 227, "zero_result_search_share": 0.3780487804878049}
