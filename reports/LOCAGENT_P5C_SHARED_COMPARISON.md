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

Execution/validity denominators are EXPLICIT and not mixed:
- **Independent tasks** = the 10 historical changes (equal for all systems).
- **Runs/cells** = P1 arms ran 10 tasks × 3 nested repetitions = 30 cells;
  LocAgent ran 10 tasks × 1 execution = 10 outcomes.
- **Non-empty/parseable** = outcomes with a usable emitted file set.
- **Fail-closed/empty** = outcomes persisted fail-closed as empty.

| System | Tasks | Runs/cells | Non-empty/parseable | Fail-closed/empty | P | R | F1 | FNR | comp_tok | calls | cost | lat |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Full-v2 | 10 | 30 | 30 | 0 | 0.339 | 0.369 | 0.353 | 0.631 | 8,445.8 | 30 | $0.2976 | 1,715.7s |
| Sparse-v2 | 10 | 30 | 30 | 0 | 0.387 | 0.261 | 0.312 | 0.739 | 599.0 | 30 | $0.0623 | 200.4s |
| LocAgent | 10 | 10 | 5 | 5 | 0.435 | 0.270 | 0.333 | 0.730 | 11,325.6 | 402 | $9.9288 | 4,025.9s |

- `30/30` and `5/10` were previously placed side-by-side under one ambiguous
  `Valid` column; this is NOT a valid comparison because the denominators
  differ (30 nested cells vs 10 executions). The table above separates them.
- LocAgent `calls` is the authoritative per-call usage ledger count (402);
  prompt 32,718,518 / completion 113,256 / total 32,831,774 tokens; est. cost
  $9.928811 (frozen $0.30/$1.00 per 1M pricing snapshot — a NORMALIZED
  estimate, not authoritative provider-billed cost).
- LocAgent `non-empty/parseable` = 5/10. The 5 empty outcomes are NOT all
  timeouts: failure taxonomy from the raw logs is 2 timeout, 1
  context-length `BadRequestError`, 2 completed-but-empty (upstream logged
  "succeed" with no parseable file set). See the taxonomy note below.
- Pooled micro metrics are primary; macro means below are secondary.

## Failure taxonomy of the 5 empty LocAgent outcomes (from raw logs)

| Case | Raw-log evidence | Outcome |
|---|---|---|
| `4307e1b8c2e2` | `execution flow reconstruction exceeded timeout. Terminating.` → `failed, save empty outputs` | timeout (900 s) → fail-closed empty |
| `66c70394c9e1` | `OpenrouterException - Upstream error from Venice: ... maximum context length ... 198248 input tokens` → `failed, save empty outputs` | context-length `BadRequestError` → fail-closed empty |
| `9e33db4f4660` | `localizing ... succeed, process multiple loc outputs` with empty `found_files` | completed-but-empty |
| `b39799f9fc1c` | `localizing ... succeed, process multiple loc outputs` with empty `found_files` | completed-but-empty |
| `fdda30c271f0` | `execution flow reconstruction exceeded timeout. Terminating.` → `failed, save empty outputs` | timeout (900 s) → fail-closed empty |

Summary: **2/10 timeout**, **1/10 context-length failure**, **2/10
completed-but-empty**, i.e. a 50% empty/non-usable localization rate. The
previous "50% timeout rate" wording is NOT supported by the raw logs.

## Provider-route provenance (corrected)

The intended statement "OpenRouter → pinned DeepInfra, fallback OFF" is NOT
proved per call by the delivered evidence:

- The per-call usage ledger records `provider="openrouter"` (the OpenRouter
  gateway), not the resolved backend provider.
- Raw logs show BOTH `Upstream error from DeepInfra` (P5-B run and the
  aborted case-3 attempt) AND `Upstream error from Venice` (resumed P5-C run,
  case `66c70394c9e1`), i.e. the backend provider was OpenRouter-RUTED and
  was not deterministically pinned per call.

Therefore the correct P5 wording is **OpenRouter-routed Qwen3-Coder**, with
the backend-provider provenance disclosed as a limitation. P1's own endpoint
freeze (DeepInfra `deepinfra/turbo`) is separate evidence and unchanged. The
`$9.9288` figure is a **normalized estimate under the frozen pricing
snapshot**, not an authoritative provider-billed cost.

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

- **Official LocAgent Acc@K** (task hit iff #correct among top-K ==
  min(len(proxy), K), mirroring the pinned upstream
  `evaluation/eval_metric.py` `acc_at_k`):
  - Acc@1: 4/10 (0.400)
  - Acc@3: 4/10 (0.400)
  - Acc@5: 2/10 (0.200)
- **Simple task-level Hit@K** (>=1 proxy file among top-K):
  - Hit@1: 4/10; Hit@3: 4/10; Hit@5: 4/10
- **Item-hit counts (audit-only, NOT task accuracy):** 4 / 8 / 9. The
  historical 4/10, 8/10, 9/10 "Acc@K" claims were these cross-task sums of
  matching FILE ITEMS mislabeled as task accuracy; they are NOT reproduced by
  the official metric and MUST NOT be reported as Acc@K / Hit@K.

These are NOT directly comparable with the common F1 columns.

## Interpretation

- **Accuracy:** LocAgent micro F1 (0.333) sits between Sparse-v2 (0.312) and
  Full-v2 (0.353); paired ΔF1 CIs cross zero for both comparisons.
- **FNR risk:** LocAgent FNR 0.730 is close to Sparse-v2 (0.739); both higher
  than Full-v2 (0.631).
- **Efficiency:** LocAgent is far more token/call/cost intensive (402 calls,
  ~$9.93, 32.8M tokens) than both our arms (Full 30 calls/$0.30, Sparse 30
  calls/$0.06) on the same tasks.
- **Trade-off:** the accuracy–cost frontier on these real held-out tasks does
  not favor LocAgent: comparable-to-slightly-lower F1 at far higher resource
  cost, with a 50% empty/non-usable localization rate (not a pure timeout
  rate).
- **Limitation:** when LocAgent does localize, its native ranking is strong at
  rank 1 (Acc@1 4/10), but the common set-based evaluator penalizes the large
  emitted file sets (low precision). Acc@K and F1 measure different things and
  must not be compared directly.

## Claim-safe summary

- We report a system-level shared-task comparison, not an algorithm ablation.
- We do NOT claim LocAgent is universally worse or better; the paired CIs cross
  zero. We DO report its substantially higher resource cost and 50%
  empty/non-usable localization rate (2 timeout / 1 context-length /
  2 completed-but-empty) on these tasks.
- We do NOT claim token savings compensate for accuracy differences anywhere.
- We do NOT claim an unqualified DeepInfra pin for every P5-C call (see
  provider-route provenance above).

Machine-readable output: `research/locagent-p5b/shared_comparison.json`.