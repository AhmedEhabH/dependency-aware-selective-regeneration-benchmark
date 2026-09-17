# P2 Phase-1 — Common Adaptive-Budget Harness: DEVELOPMENT Results

**Date:** 2026-09-18  **Tier:** T3 scientific DEVELOPMENT (ZERO API)
**Data:** djangoCMS DEV (174 tasks) + Saleor DEV (149 tasks). djangoCMS
INTERNAL_TEST is spent and NEVER used for P2 selection/tuning; RESERVE and
Saleor INTERNAL_TEST/RESERVE are sealed.

## Frozen constants (derived on djangoCMS DEV_TRAIN ONLY)

- `tau_gap` = 0.1 (declared in the pre-registration note)
- `tau_marg` = 1.0 (25th percentile of DEV_TRAIN composite scores)
- `tau_energy` = 0.9 (declared)
- cost-ratio grid (declared sensitivity): [0.5, 1.0, 2.0]

## Verifier cost model (measured, frozen)

- prompt_tokens(B) = 204.51 + 7.40*B; api_cost(B) = 0.000065 + 0.000005*B
  (least-squares fit over the 320 frozen confirmatory verifier calls).
- Cost semantics: 1 batch verifier call at realized B_t (candidates = B_t);
  `marginal_calls = B_t` is a labelled sensitivity.

## djangoCMS DEV (n=174)

| method | macro ORR | micro ORR | mean B/task | mean tokens | mean cost $ | oracle-gap | over-alloc | under-alloc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| fixed-B1 (composite) | 0.0464 | 0.0445 | 1 | 211.91 | 7e-05 | 0.0856 | 0.0 | 0.2047 |
| fixed-B3 (composite) | 0.1177 | 0.1126 | 3 | 226.71 | 8e-05 | 0.1163 | 1.2759 | 0.1334 |
| fixed-B5 (composite) | 0.1633 | 0.1623 | 5 | 241.51 | 9e-05 | 0.1434 | 2.7586 | 0.0879 |
| fixed-B10 (composite) | 0.2512 | 0.2644 | 10 | 278.51 | 0.000115 | 0.2084 | 6.7816 | 0.0 |
| P2-P1-score-gap | 0.0775 | 0.0681 | 1.6092 | 216.418 | 7.3e-05 | 0.1092 | 0.3678 | 0.1737 |
| P2-P2-marginal-score | 0.2389 | 0.2513 | 8.4713 | 267.1974 | 0.000107 | 0.2034 | 5.4828 | 0.0123 |
| P2-P4-learning-k-analogue | 0.2389 | 0.2513 | 8.4483 | 267.0272 | 0.000107 | 0.2035 | 5.4598 | 0.0123 |
| P2-P3-cost-ratio-tau=0.5 | 0.0464 | 0.0445 | 1.0 | 211.91 | 7e-05 | 0.0856 | 0.0 | 0.2047 |
| P2-P3-cost-ratio-tau=1.0 | 0.061 | 0.0628 | 1.5517 | 215.9928 | 7.3e-05 | 0.0964 | 0.3908 | 0.1902 |
| P2-P3-cost-ratio-tau=2.0 | 0.2512 | 0.2644 | 10.0 | 278.51 | 0.000115 | 0.2084 | 6.7816 | 0.0 |

Pareto frontier (recovery-vs-cost): fixed-B1, fixed-B3, fixed-B5, fixed-B10, P2-P1-score-gap, P2-P2-marginal-score, P2-P4-learning-k-analogue, P2-P3-cost-ratio, P2-P3-cost-ratio, inspect-all

Matched fixed-B comparison: {
 "P2-P1-score-gap": {
  "policy": "P2-P1-score-gap",
  "policy_cost_usd": 7.3e-05,
  "policy_orr": 0.0775,
  "dominates_or_matches_fixed": true,
  "matched_fixed_point": {
   "n_tasks": 174,
   "macro_orr": 0.1177,
   "micro_orr": 0.1126,
   "fnrr": 0.8823,
   "total_recovered": 43,
   "total_missed": 382,
   "expected_budget": 3.0,
   "mean_candidates": 3.0,
   "mean_tokens": 226.71,
   "mean_cost_usd": 8e-05,
   "mean_oracle_gap_closed": 0.1163,
   "over_allocation_rate": 1.2759,
   "under_allocation_rate": 0.1334,
   "name": "fixed-B3",
   "budget": 3
  }
 },
 "P2-P2-marginal-score": {
  "policy": "P2-P2-marginal-score",
  "policy_cost_usd": 0.000107,
  "policy_orr": 0.2389,
  "dominates_or_matches_fixed": true,
  "matched_fixed_point": {
   "n_tasks": 174,
   "macro_orr": 0.2512,
   "micro_orr": 0.2644,
   "fnrr": 0.7488,
   "total_recovered": 101,
   "total_missed": 382,
   "expected_budget": 10.0,
   "mean_candidates": 10.0,
   "mean_tokens": 278.51,
   "mean_cost_usd": 0.000115,
   "mean_oracle_gap_closed": 0.2084,
   "over_allocation_rate": 6.7816,
   "under_allocation_rate": 0.0,
   "name": "fixed-B10",
   "budget": 10
  }
 },
 "P2-P4-learning-k-analogue": {
  "policy": "P2-P4-learning-k-analogue",
  "policy_cost_usd": 0.000107,
  "policy_orr": 0.2389,
  "dominates_or_matches_fixed": true,
  "matched_fixed_point": {
   "n_tasks": 174,
   "macro_orr": 0.2512,
   "micro_orr": 0.2644,
   "fnrr": 0.7488,
   "total_recovered": 101,
   "total_missed": 382,
   "expected_budget": 10.0,
   "mean_candidates": 10.0,
   "mean_tokens": 278.51,
   "mean_cost_usd": 0.000115,
   "mean_oracle_gap_closed": 0.2084,
   "over_allocation_rate": 6.7816,
   "under_allocation_rate": 0.0,
   "name": "fixed-B10",
   "budget": 10
  }
 },
 "P2-P3-cost-ratio-tau=0.5": {
  "policy": "P2-P3-cost-ratio",
  "policy_cost_usd": 7e-05,
  "policy_orr": 0.0464,
  "dominates_or_matches_fixed": true,
  "matched_fixed_point": {
   "n_tasks": 174,
   "macro_orr": 0.0464,
   "micro_orr": 0.0445,
   "fnrr": 0.9536,
   "total_recovered": 17,
   "total_missed": 382,
   "expected_budget": 1.0,
   "mean_candidates": 1.0,
   "mean_tokens": 211.91,
   "mean_cost_usd": 7e-05,
   "mean_oracle_gap_closed": 0.0856,
   "over_allocation_rate": 0.0,
   "under_allocation_rate": 0.2047,
   "name": "fixed-B1",
   "budget": 1
  }
 },
 "P2-P3-cost-ratio-tau=1.0": {
  "policy": "P2-P3-cost-ratio",
  "policy_cost_usd": 7.3e-05,
  "policy_orr": 0.061,
  "dominates_or_matches_fixed": true,
  "matched_fixed_point": {
   "n_tasks": 174,
   "macro_orr": 0.1177,
   "micro_orr": 0.1126,
   "fnrr": 0.8823,
   "total_recovered": 43,
   "total_missed": 382,
   "expected_budget": 3.0,
   "mean_candidates": 3.0,
   "mean_tokens": 226.71,
   "mean_cost_usd": 8e-05,
   "mean_oracle_gap_closed": 0.1163,
   "over_allocation_rate": 1.2759,
   "under_allocation_rate": 0.1334,
   "name": "fixed-B3",
   "budget": 3
  }
 },
 "P2-P3-cost-ratio-tau=2.0": {
  "policy": "P2-P3-cost-ratio",
  "policy_cost_usd": 0.000115,
  "policy_orr": 0.2512,
  "dominates_or_matches_fixed": true,
  "matched_fixed_point": {
   "n_tasks": 174,
   "macro_orr": 0.2512,
   "micro_orr": 0.2644,
   "fnrr": 0.7488,
   "total_recovered": 101,
   "total_missed": 382,
   "expected_budget": 10.0,
   "mean_candidates": 10.0,
   "mean_tokens": 278.51,
   "mean_cost_usd": 0.000115,
   "mean_oracle_gap_closed": 0.2084,
   "over_allocation_rate": 6.7816,
   "under_allocation_rate": 0.0,
   "name": "fixed-B10",
   "budget": 10
  }
 }
}

## Saleor DEV (n=149)

| method | macro ORR | micro ORR | mean B/task | mean tokens | mean cost $ | oracle-gap | over-alloc | under-alloc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| fixed-B1 (composite) | 0.0775 | 0.0678 | 1 | 211.91 | 7e-05 | 0.1649 | 0.0 | 0.2398 |
| fixed-B3 (composite) | 0.1576 | 0.1518 | 3 | 226.71 | 8e-05 | 0.1809 | 1.1812 | 0.1597 |
| fixed-B5 (composite) | 0.2369 | 0.2141 | 5 | 241.51 | 9e-05 | 0.239 | 2.5906 | 0.0804 |
| fixed-B10 (composite) | 0.3173 | 0.3008 | 10 | 278.51 | 0.000115 | 0.3098 | 6.6174 | 0.0 |
| P2-P1-score-gap | 0.1151 | 0.0976 | 1.5235 | 215.7838 | 7.3e-05 | 0.1906 | 0.3221 | 0.2022 |
| P2-P2-marginal-score | 0.3173 | 0.3008 | 9.953 | 278.1623 | 0.000115 | 0.3098 | 6.5705 | 0.0 |
| P2-P4-learning-k-analogue | 0.3139 | 0.2981 | 9.9396 | 278.063 | 0.000115 | 0.3065 | 6.5705 | 0.0034 |
| P2-P3-cost-ratio-tau=0.5 | 0.2918 | 0.2683 | 9.0336 | 271.3583 | 0.00011 | 0.2874 | 6.0 | 0.0255 |
| P2-P3-cost-ratio-tau=1.0 | 0.3173 | 0.3008 | 10.0 | 278.51 | 0.000115 | 0.3098 | 6.6174 | 0.0 |
| P2-P3-cost-ratio-tau=2.0 | 0.3173 | 0.3008 | 10.0 | 278.51 | 0.000115 | 0.3098 | 6.6174 | 0.0 |

Pareto frontier (recovery-vs-cost): fixed-B1, fixed-B3, fixed-B5, fixed-B10, P2-P1-score-gap, P2-P2-marginal-score, P2-P3-cost-ratio, P2-P3-cost-ratio, P2-P3-cost-ratio, inspect-all

Matched fixed-B comparison: {
 "P2-P1-score-gap": {
  "policy": "P2-P1-score-gap",
  "policy_cost_usd": 7.3e-05,
  "policy_orr": 0.1151,
  "dominates_or_matches_fixed": true,
  "matched_fixed_point": {
   "n_tasks": 149,
   "macro_orr": 0.1576,
   "micro_orr": 0.1518,
   "fnrr": 0.8424,
   "total_recovered": 56,
   "total_missed": 369,
   "expected_budget": 3.0,
   "mean_candidates": 3.0,
   "mean_tokens": 226.71,
   "mean_cost_usd": 8e-05,
   "mean_oracle_gap_closed": 0.1809,
   "over_allocation_rate": 1.1812,
   "under_allocation_rate": 0.1597,
   "name": "fixed-B3",
   "budget": 3
  }
 },
 "P2-P2-marginal-score": {
  "policy": "P2-P2-marginal-score",
  "policy_cost_usd": 0.000115,
  "policy_orr": 0.3173,
  "dominates_or_matches_fixed": true,
  "matched_fixed_point": {
   "n_tasks": 149,
   "macro_orr": 0.3173,
   "micro_orr": 0.3008,
   "fnrr": 0.6827,
   "total_recovered": 111,
   "total_missed": 369,
   "expected_budget": 10.0,
   "mean_candidates": 10.0,
   "mean_tokens": 278.51,
   "mean_cost_usd": 0.000115,
   "mean_oracle_gap_closed": 0.3098,
   "over_allocation_rate": 6.6174,
   "under_allocation_rate": 0.0,
   "name": "fixed-B10",
   "budget": 10
  }
 },
 "P2-P4-learning-k-analogue": {
  "policy": "P2-P4-learning-k-analogue",
  "policy_cost_usd": 0.000115,
  "policy_orr": 0.3139,
  "dominates_or_matches_fixed": true,
  "matched_fixed_point": {
   "n_tasks": 149,
   "macro_orr": 0.3173,
   "micro_orr": 0.3008,
   "fnrr": 0.6827,
   "total_recovered": 111,
   "total_missed": 369,
   "expected_budget": 10.0,
   "mean_candidates": 10.0,
   "mean_tokens": 278.51,
   "mean_cost_usd": 0.000115,
   "mean_oracle_gap_closed": 0.3098,
   "over_allocation_rate": 6.6174,
   "under_allocation_rate": 0.0,
   "name": "fixed-B10",
   "budget": 10
  }
 },
 "P2-P3-cost-ratio-tau=0.5": {
  "policy": "P2-P3-cost-ratio",
  "policy_cost_usd": 0.00011,
  "policy_orr": 0.2918,
  "dominates_or_matches_fixed": true,
  "matched_fixed_point": {
   "n_tasks": 149,
   "macro_orr": 0.3173,
   "micro_orr": 0.3008,
   "fnrr": 0.6827,
   "total_recovered": 111,
   "total_missed": 369,
   "expected_budget": 10.0,
   "mean_candidates": 10.0,
   "mean_tokens": 278.51,
   "mean_cost_usd": 0.000115,
   "mean_oracle_gap_closed": 0.3098,
   "over_allocation_rate": 6.6174,
   "under_allocation_rate": 0.0,
   "name": "fixed-B10",
   "budget": 10
  }
 },
 "P2-P3-cost-ratio-tau=1.0": {
  "policy": "P2-P3-cost-ratio",
  "policy_cost_usd": 0.000115,
  "policy_orr": 0.3173,
  "dominates_or_matches_fixed": true,
  "matched_fixed_point": {
   "n_tasks": 149,
   "macro_orr": 0.3173,
   "micro_orr": 0.3008,
   "fnrr": 0.6827,
   "total_recovered": 111,
   "total_missed": 369,
   "expected_budget": 10.0,
   "mean_candidates": 10.0,
   "mean_tokens": 278.51,
   "mean_cost_usd": 0.000115,
   "mean_oracle_gap_closed": 0.3098,
   "over_allocation_rate": 6.6174,
   "under_allocation_rate": 0.0,
   "name": "fixed-B10",
   "budget": 10
  }
 },
 "P2-P3-cost-ratio-tau=2.0": {
  "policy": "P2-P3-cost-ratio",
  "policy_cost_usd": 0.000115,
  "policy_orr": 0.3173,
  "dominates_or_matches_fixed": true,
  "matched_fixed_point": {
   "n_tasks": 149,
   "macro_orr": 0.3173,
   "micro_orr": 0.3008,
   "fnrr": 0.6827,
   "total_recovered": 111,
   "total_missed": 369,
   "expected_budget": 10.0,
   "mean_candidates": 10.0,
   "mean_tokens": 278.51,
   "mean_cost_usd": 0.000115,
   "mean_oracle_gap_closed": 0.3098,
   "over_allocation_rate": 6.6174,
   "under_allocation_rate": 0.0,
   "name": "fixed-B10",
   "budget": 10
  }
 }
}

## Pooled DEV (n=323)

| method | macro ORR | micro ORR | mean B/task | mean tokens | mean cost $ | oracle-gap | over-alloc | under-alloc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| fixed-B1 (composite) | 0.0607 | 0.0559 | 1 | 211.91 | 7e-05 | 0.1222 | 0.0 | 0.2209 |
| fixed-B3 (composite) | 0.1361 | 0.1318 | 3 | 226.71 | 8e-05 | 0.1461 | 1.2322 | 0.1455 |
| fixed-B5 (composite) | 0.1972 | 0.1877 | 5 | 241.51 | 9e-05 | 0.1875 | 2.6811 | 0.0844 |
| fixed-B10 (composite) | 0.2817 | 0.2823 | 10 | 278.51 | 0.000115 | 0.2552 | 6.7059 | 0.0 |
| P2-P1-score-gap | 0.0948 | 0.0826 | 1.5697 | 216.1255 | 7.3e-05 | 0.1467 | 0.3467 | 0.1868 |
| P2-P2-marginal-score | 0.275 | 0.2756 | 9.1548 | 272.2555 | 0.000111 | 0.2525 | 5.9845 | 0.0066 |
| P2-P4-learning-k-analogue | 0.2735 | 0.2743 | 9.1362 | 272.118 | 0.000111 | 0.251 | 5.9721 | 0.0082 |
| P2-P3-cost-ratio-tau=0.5 | 0.1596 | 0.1545 | 4.7059 | 239.3335 | 8.9e-05 | 0.1787 | 2.7678 | 0.1221 |
| P2-P3-cost-ratio-tau=1.0 | 0.1792 | 0.1798 | 5.4489 | 244.832 | 9.2e-05 | 0.1948 | 3.2632 | 0.1024 |
| P2-P3-cost-ratio-tau=2.0 | 0.2817 | 0.2823 | 10.0 | 278.51 | 0.000115 | 0.2552 | 6.7059 | 0.0 |

Pareto frontier (recovery-vs-cost): fixed-B1, fixed-B3, fixed-B5, fixed-B10, P2-P1-score-gap, P2-P2-marginal-score, P2-P3-cost-ratio, P2-P3-cost-ratio, inspect-all

Matched fixed-B comparison: {
 "P2-P1-score-gap": {
  "policy": "P2-P1-score-gap",
  "policy_cost_usd": 7.3e-05,
  "policy_orr": 0.0948,
  "dominates_or_matches_fixed": true,
  "matched_fixed_point": {
   "n_tasks": 323,
   "macro_orr": 0.1361,
   "micro_orr": 0.1318,
   "fnrr": 0.8639,
   "total_recovered": 99,
   "total_missed": 751,
   "expected_budget": 3.0,
   "mean_candidates": 3.0,
   "mean_tokens": 226.71,
   "mean_cost_usd": 8e-05,
   "mean_oracle_gap_closed": 0.1461,
   "over_allocation_rate": 1.2322,
   "under_allocation_rate": 0.1455,
   "name": "fixed-B3",
   "budget": 3
  }
 },
 "P2-P2-marginal-score": {
  "policy": "P2-P2-marginal-score",
  "policy_cost_usd": 0.000111,
  "policy_orr": 0.275,
  "dominates_or_matches_fixed": true,
  "matched_fixed_point": {
   "n_tasks": 323,
   "macro_orr": 0.2817,
   "micro_orr": 0.2823,
   "fnrr": 0.7183,
   "total_recovered": 212,
   "total_missed": 751,
   "expected_budget": 10.0,
   "mean_candidates": 10.0,
   "mean_tokens": 278.51,
   "mean_cost_usd": 0.000115,
   "mean_oracle_gap_closed": 0.2552,
   "over_allocation_rate": 6.7059,
   "under_allocation_rate": 0.0,
   "name": "fixed-B10",
   "budget": 10
  }
 },
 "P2-P4-learning-k-analogue": {
  "policy": "P2-P4-learning-k-analogue",
  "policy_cost_usd": 0.000111,
  "policy_orr": 0.2735,
  "dominates_or_matches_fixed": true,
  "matched_fixed_point": {
   "n_tasks": 323,
   "macro_orr": 0.2817,
   "micro_orr": 0.2823,
   "fnrr": 0.7183,
   "total_recovered": 212,
   "total_missed": 751,
   "expected_budget": 10.0,
   "mean_candidates": 10.0,
   "mean_tokens": 278.51,
   "mean_cost_usd": 0.000115,
   "mean_oracle_gap_closed": 0.2552,
   "over_allocation_rate": 6.7059,
   "under_allocation_rate": 0.0,
   "name": "fixed-B10",
   "budget": 10
  }
 },
 "P2-P3-cost-ratio-tau=0.5": {
  "policy": "P2-P3-cost-ratio",
  "policy_cost_usd": 8.9e-05,
  "policy_orr": 0.1596,
  "dominates_or_matches_fixed": true,
  "matched_fixed_point": {
   "n_tasks": 323,
   "macro_orr": 0.1972,
   "micro_orr": 0.1877,
   "fnrr": 0.8028,
   "total_recovered": 141,
   "total_missed": 751,
   "expected_budget": 5.0,
   "mean_candidates": 5.0,
   "mean_tokens": 241.51,
   "mean_cost_usd": 9e-05,
   "mean_oracle_gap_closed": 0.1875,
   "over_allocation_rate": 2.6811,
   "under_allocation_rate": 0.0844,
   "name": "fixed-B5",
   "budget": 5
  }
 },
 "P2-P3-cost-ratio-tau=1.0": {
  "policy": "P2-P3-cost-ratio",
  "policy_cost_usd": 9.2e-05,
  "policy_orr": 0.1792,
  "dominates_or_matches_fixed": true,
  "matched_fixed_point": {
   "n_tasks": 323,
   "macro_orr": 0.2817,
   "micro_orr": 0.2823,
   "fnrr": 0.7183,
   "total_recovered": 212,
   "total_missed": 751,
   "expected_budget": 10.0,
   "mean_candidates": 10.0,
   "mean_tokens": 278.51,
   "mean_cost_usd": 0.000115,
   "mean_oracle_gap_closed": 0.2552,
   "over_allocation_rate": 6.7059,
   "under_allocation_rate": 0.0,
   "name": "fixed-B10",
   "budget": 10
  }
 },
 "P2-P3-cost-ratio-tau=2.0": {
  "policy": "P2-P3-cost-ratio",
  "policy_cost_usd": 0.000115,
  "policy_orr": 0.2817,
  "dominates_or_matches_fixed": true,
  "matched_fixed_point": {
   "n_tasks": 323,
   "macro_orr": 0.2817,
   "micro_orr": 0.2823,
   "fnrr": 0.7183,
   "total_recovered": 212,
   "total_missed": 751,
   "expected_budget": 10.0,
   "mean_candidates": 10.0,
   "mean_tokens": 278.51,
   "mean_cost_usd": 0.000115,
   "mean_oracle_gap_closed": 0.2552,
   "over_allocation_rate": 6.7059,
   "under_allocation_rate": 0.0,
   "name": "fixed-B10",
   "budget": 10
  }
 }
}

## Strata (omitted-size terciles, per repo)

```json
{
 "djangocms": {
  "P2-P1-score-gap": {
   "small": {
    "n_tasks": 73,
    "macro_orr": 0.0961,
    "expected_budget": 1.6575
   },
   "medium": {
    "n_tasks": 50,
    "macro_orr": 0.0842,
    "expected_budget": 1.84
   },
   "large": {
    "n_tasks": 51,
    "macro_orr": 0.0441,
    "expected_budget": 1.3137
   }
  },
  "P2-P2-marginal-score": {
   "small": {
    "n_tasks": 73,
    "macro_orr": 0.2981,
    "expected_budget": 9.5068
   },
   "medium": {
    "n_tasks": 50,
    "macro_orr": 0.2386,
    "expected_budget": 9.28
   },
   "large": {
    "n_tasks": 51,
    "macro_orr": 0.1543,
    "expected_budget": 6.1961
   }
  },
  "P2-P4-learning-k-analogue": {
   "small": {
    "n_tasks": 73,
    "macro_orr": 0.2981,
    "expected_budget": 9.5068
   },
   "medium": {
    "n_tasks": 50,
    "macro_orr": 0.2386,
    "expected_budget": 9.28
   },
   "large": {
    "n_tasks": 51,
    "macro_orr": 0.1543,
    "expected_budget": 6.1176
   }
  }
 },
 "saleor": {
  "P2-P1-score-gap": {
   "small": {
    "n_tasks": 50,
    "macro_orr": 0.1437,
    "expected_budget": 1.6
   },
   "medium": {
    "n_tasks": 54,
    "macro_orr": 0.065,
    "expected_budget": 1.3704
   },
   "large": {
    "n_tasks": 45,
    "macro_orr": 0.1435,
    "expected_budget": 1.6222
   }
  },
  "P2-P2-marginal-score": {
   "small": {
    "n_tasks": 50,
    "macro_orr": 0.3793,
    "expected_budget": 10.0
   },
   "medium": {
    "n_tasks": 54,
    "macro_orr": 0.3,
    "expected_budget": 10.0
   },
   "large": {
    "n_tasks": 45,
    "macro_orr": 0.269,
    "expected_budget": 9.8444
   }
  },
  "P2-P4-learning-k-analogue": {
   "small": {
    "n_tasks": 50,
    "macro_orr": 0.3793,
    "expected_budget": 10.0
   },
   "medium": {
    "n_tasks": 54,
    "macro_orr": 0.3,
    "expected_budget": 10.0
   },
   "large": {
    "n_tasks": 45,
    "macro_orr": 0.2579,
    "expected_budget": 9.8
   }
  }
 }
}
```

## Strong-method gate (pre-registered)

gate pass = False

```json
{
 "rule": "proceed to stronger methods iff any P2-P1..P4 shows lower mean cost than fixed-B=5 AND macro ORR within 5% of fixed-B=5 on BOTH djangoCMS DEV and Saleor DEV (pre-registered, not tuned)",
 "djangocms_dev": {
  "P2-P1-score-gap": {
   "policy_orr": 0.0775,
   "policy_cost_usd": 7.3e-05,
   "fixedB5_orr": 0.1633,
   "fixedB5_cost_usd": 9e-05,
   "lower_cost_than_B5": true,
   "orr_within_5pct_of_B5": false,
   "trade_off_present": false
  },
  "P2-P2-marginal-score": {
   "policy_orr": 0.2389,
   "policy_cost_usd": 0.000107,
   "fixedB5_orr": 0.1633,
   "fixedB5_cost_usd": 9e-05,
   "lower_cost_than_B5": false,
   "orr_within_5pct_of_B5": true,
   "trade_off_present": false
  },
  "P2-P4-learning-k-analogue": {
   "policy_orr": 0.2389,
   "policy_cost_usd": 0.000107,
   "fixedB5_orr": 0.1633,
   "fixedB5_cost_usd": 9e-05,
   "lower_cost_than_B5": false,
   "orr_within_5pct_of_B5": true,
   "trade_off_present": false
  },
  "P2-P3-cost-ratio-tau=0.5": {
   "policy_orr": 0.0464,
   "policy_cost_usd": 7e-05,
   "fixedB5_orr": 0.1633,
   "fixedB5_cost_usd": 9e-05,
   "lower_cost_than_B5": true,
   "orr_within_5pct_of_B5": false,
   "trade_off_present": false
  },
  "P2-P3-cost-ratio-tau=1.0": {
   "policy_orr": 0.061,
   "policy_cost_usd": 7.3e-05,
   "fixedB5_orr": 0.1633,
   "fixedB5_cost_usd": 9e-05,
   "lower_cost_than_B5": true,
   "orr_within_5pct_of_B5": false,
   "trade_off_present": false
  },
  "P2-P3-cost-ratio-tau=2.0": {
   "policy_orr": 0.2512,
   "policy_cost_usd": 0.000115,
   "fixedB5_orr": 0.1633,
   "fixedB5_cost_usd": 9e-05,
   "lower_cost_than_B5": false,
   "orr_within_5pct_of_B5": true,
   "trade_off_present": false
  }
 },
 "saleor_dev": {
  "P2-P1-score-gap": {
   "policy_orr": 0.1151,
   "policy_cost_usd": 7.3e-05,
   "fixedB5_orr": 0.2369,
   "fixedB5_cost_usd": 9e-05,
   "lower_cost_than_B5": true,
   "orr_within_5pct_of_B5": false,
   "trade_off_present": false
  },
  "P2-P2-marginal-score": {
   "policy_orr": 0.3173,
   "policy_cost_usd": 0.000115,
   "fixedB5_orr": 0.2369,
   "fixedB5_cost_usd": 9e-05,
   "lower_cost_than_B5": false,
   "orr_within_5pct_of_B5": true,
   "trade_off_present": false
  },
  "P2-P4-learning-k-analogue": {
   "policy_orr": 0.3139,
   "policy_cost_usd": 0.000115,
   "fixedB5_orr": 0.2369,
   "fixedB5_cost_usd": 9e-05,
   "lower_cost_than_B5": false,
   "orr_within_5pct_of_B5": true,
   "trade_off_present": false
  },
  "P2-P3-cost-ratio-tau=0.5": {
   "policy_orr": 0.2918,
   "policy_cost_usd": 0.00011,
   "fixedB5_orr": 0.2369,
   "fixedB5_cost_usd": 9e-05,
   "lower_cost_than_B5": false,
   "orr_within_5pct_of_B5": true,
   "trade_off_present": false
  },
  "P2-P3-cost-ratio-tau=1.0": {
   "policy_orr": 0.3173,
   "policy_cost_usd": 0.000115,
   "fixedB5_orr": 0.2369,
   "fixedB5_cost_usd": 9e-05,
   "lower_cost_than_B5": false,
   "orr_within_5pct_of_B5": true,
   "trade_off_present": false
  },
  "P2-P3-cost-ratio-tau=2.0": {
   "policy_orr": 0.3173,
   "policy_cost_usd": 0.000115,
   "fixedB5_orr": 0.2369,
   "fixedB5_cost_usd": 9e-05,
   "lower_cost_than_B5": false,
   "orr_within_5pct_of_B5": true,
   "trade_off_present": false
  }
 },
 "strong_method_gate_pass": false
}
```

Machine-readable: research/p2-phase1/{frozen_constants,results_summary,per_task_rows}.json