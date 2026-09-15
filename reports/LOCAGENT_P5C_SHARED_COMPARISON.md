# P5 — Full-v2 / Sparse-v2 / LocAgent Shared-Protocol Comparison

**Date:** 2026-09-15
**Classification:** SYSTEM-LEVEL SHARED-PROTOCOL COMPARISON — P1 used its own
frozen settings (temperature 0); LocAgent retains its upstream protocol
(temperature 1). NOT a pure algorithm ablation.

## Evidence

- Full-v2 / Sparse-v2: recomputed from frozen P1 raw evidence only
  (`research/real-commit-p1-01/final_metrics.json`). No P1 model call was
  rerun.
- LocAgent: NEW P5-C held-out run
  (`research/locagent-p5b/out_c/`), scored with the frozen common evaluator
  against the SAME observed change-set proxy on the SAME 10 tasks.

## Shared-task table (same 10 real held-out djangoCMS changes)

| System | Valid | P | R | F1 | FNR | comp_tok | calls | cost | lat |
|---|---|---|---|---|---|---|---|---|---|
| Full-v2 | 30/30 | 0.339 | 0.369 | 0.353 | 0.631 | 8,445.8 | 30 | $0.2976 | 1,715.7s |
| Sparse-v2 | 30/30 | 0.387 | 0.261 | 0.312 | 0.739 | 599.0 | 30 | $0.0623 | 200.4s |
| LocAgent | 5/10 | 0.435 | 0.270 | 0.333 | 0.730 | 11,325.6 | 402 | $9.9288 | 4,025.9s |

- LocAgent `calls` is the authoritative per-call usage ledger count (402);
  prompt 32,718,518 / completion 113,256 / total 32,831,774 tokens; est. cost
  $9.928811 (frozen $0.30/$1.00 per 1M pricing).
- LocAgent `valid` = 5/10 because 5 tasks hit the frozen 900 s per-attempt
  timeout and were persisted fail-closed as empty (timeout rate 50%).
- Pooled micro metrics are primary; macro means below are secondary.

## Macro means (task-level)

| System | P | R | F1 | FNR |
|---|---|---|---|---|
| Full-v2 | 0.392 | 0.528 | 0.387 | 0.472 |
| Sparse-v2 | 0.427 | 0.465 | 0.379 | 0.535 |
| LocAgent | 0.345 | 0.302 | 0.318 | 0.698 |

## Paired task-level F1 deltas (bootstrap over 10 independent tasks, CI95)

| Pair | mean ΔF1 | CI95 |
|---|---|---|
| LocAgent − Full | −0.0684 | [−0.2496, 0.1702] |
| LocAgent − Sparse | −0.0607 | [−0.3057, 0.2409] |
| Sparse-v2 − Full-v2 | −0.0088 | [−0.1297, 0.1189] (frozen P1) |

All CI95 intervals cross zero → no significant F1 difference at task level.

## LocAgent-native metrics (separate from common F1)

From the ORIGINAL ranked order in `merged_loc_outputs_mrr.jsonl` (never
reconstructed from a set):

- Acc@1: 4/10 (0.400)
- Acc@3: 8/10 (0.800)
- Acc@5: 9/10 (0.900)

These are NOT directly comparable with the common F1 columns.

## Interpretation

- **Accuracy:** LocAgent micro F1 (0.333) sits between Sparse-v2 (0.312) and
  Full-v2 (0.353); paired ΔF1 CIs cross zero for both comparisons.
- **FNR risk:** LocAgent FNR 0.730 is close to Sparse-v2 (0.739); both higher
  than Full-v2 (0.631).
- **Efficiency:** LocAgent is far more token/call/cost intensive (402 calls,
  ~$9.93, 32.8M tokens) than both our arms (Full 30 calls/$0.30, Sparse 30
  calls/$0.06) on the same tasks, and its 50% timeout rate shows the upstream
  agent budget (900 s) is frequently exhausted on these real changes.
- **Trade-off:** the accuracy–cost frontier on these real held-out tasks does
  not favor LocAgent: comparable-to-slightly-lower F1 at roughly 33× the token
  budget and 160× the cost of Full-v2, with high timeout attrition.
- **Limitation:** LocAgent native ranking is strong (Acc@3 0.80, Acc@5 0.90),
  but the common set-based evaluator penalizes the large emitted file sets
  (low precision). Acc@K and F1 measure different things and must not be
  compared directly.

## Claim-safe summary

- We report a system-level shared-task comparison, not an algorithm ablation.
- We do NOT claim LocAgent is universally worse or better; the paired CIs cross
  zero. We DO report its substantially higher resource cost and 50% timeout
  rate on these tasks.
- We do NOT claim token savings compensate for accuracy differences anywhere.

Machine-readable output: `research/locagent-p5b/shared_comparison.json`.