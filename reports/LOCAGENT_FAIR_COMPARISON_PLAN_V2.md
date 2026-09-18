# LocAgent Fair Comparison Plan V2

**Date:** 2026-09-18
**Tier:** T3 (ZERO API; ZERO LocAgent spend in this mission)
**Mission:** OPENCODE_ORACLE_GAP_BIDIRECTIONAL_REPAIR_MISSION_2026-09-18
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731

**Purpose:** define, WITHOUT any new LocAgent spend, what evidence would be
required to fairly compare our methods against LocAgent. Do NOT optimize
against LocAgent's published headline numbers; the previous shared-protocol run
is NOT a faithful reproduction of the published fine-tuned setup.

---

## 1. Three distinct configurations (must never be conflated)

| Config | What it is | Status |
|---|---|---|
| Published LocAgent | Liu et al. tool-learning agent, fine-tuned on SWE-bench-style data; temperature-1 decoding; agentic tool loop | EXTERNAL reference only |
| Our prior shared-protocol run (`research/locagent-p5b/shared_comparison.json`) | LocAgent run under OUR shared protocol (P1 task prompts, our eval), 10 tasks / 10 runs, 5 non-empty parseable | NOT a faithful reproduction; 5/10 fail-closed-empty |
| Our Sparse / Route-B / (future) BBSR methods | Our pipeline on the same shared protocol | FROZEN / DEVELOPMENT |

The prior run's own record says: "Not a pure algorithm ablation"; temperature
P1=0 vs LocAgent=1; provider routes not fully pinned; cost is a normalized
estimate. It must never be presented as "LocAgent under its published config".

## 2. What evidence is required to say "method X Pareto-dominates the LocAgent run"

Under the SAME shared protocol (same task packets, same eval unit, same proxy),
method X Pareto-dominates the recorded LocAgent run only if ALL of:

| Dimension | Required evidence |
|---|---|
| F1 (file-level) | X F1 ≥ LocAgent-run F1 with a documented aggregation (same n tasks, same denominator rule) |
| Cost | X mean cost/task ≤ LocAgent-run cost/task with a pinned pricing snapshot |
| Tokens | X mean total tokens/task ≤ LocAgent-run tokens/task |
| Latency | X mean latency/task ≤ LocAgent-run latency/task (same hardware/backend class) |
| Failure rate | X failed/non-parseable cell rate ≤ LocAgent-run rate, with the fail-closed-empty rule applied identically |

A claim of "Pareto-dominates" requires strict ≤ on ALL and < on at least one,
computed on IDENTICAL task sets. The prior shared-protocol run's 5/10
fail-closed-empty cells make it an unreliable dominance target; any dominance
claim against it must state this limitation.

## 3. Current Sparse / Route-B status vs LocAgent-run (from frozen records)

From `research/locagent-p5b/shared_comparison.json` (10 tasks):
- LocAgent run: TP 10, FP 13, FN 27 → P 0.4348, R 0.2703, F1 0.3333;
  5/10 cells fail-closed-empty; mean total tokens ~millions/task (e.g. 5.36M,
  4.46M on two tasks); cost ~$1.3–1.6 on two tasks; latency ~500–844 s/task.
- Full-v2 run: F1 0.3534; Sparse-v2 run: F1 0.3118 (same 10 tasks, 30 cells,
  30 non-empty parseable).

Our Sparse on full DEV (174/149 tasks) is F1 0.318/0.261; Route-B add-only
lowers it. **No dominance claim is made in this mission.** The shared-protocol
numbers exist only as a frozen record.

## 4. What we will NOT do

- No new LocAgent API spend.
- No claim that our method beats the published fine-tuned LocAgent config.
- No "universal superiority" wording.
- No reuse of the prior run as if it were a faithful LocAgent benchmark.

## 5. Plan if a future comparison is authorized

1. Freeze one shared protocol (task packets, eval unit, proxy, denominator
   rules, pricing snapshot, latency ceiling).
2. Run LocAgent under its published config AND our method under the same
   protocol on the same DEVELOPMENT tasks (new budget authorized separately).
3. Report the full Pareto table (F1 / cost / tokens / latency / failure rate)
   with the fail-closed-empty rule applied identically to both.
4. Only then may a Pareto-dominance statement be written, and it must be
   scoped to "under the same shared protocol".

This mission performs the plan only (Section 2/3/5); it spends zero LocAgent
budget.