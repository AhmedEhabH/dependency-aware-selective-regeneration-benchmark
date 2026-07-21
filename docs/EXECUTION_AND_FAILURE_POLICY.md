# Execution and Failure Policy — v1.0 (FROZEN)

**Part of:** Research Protocol v1.0
**Approval Date:** 2026-07-22

---

## 1. Execution Stages (per DA-09)

### Smoke
One controlled scenario; mock backend locally; one real Qwen Kaggle orchestration run. Non-publication evidence.

### Pilot
Three repositories, four scenarios each, two strategies (`repository_agent`, `hybrid_selective`), two repetitions. Descriptive only.

### Main
All 24 scenarios. Impact-only strategies run without generation where possible. Full evolution uses `repository_agent`, `hybrid_selective`, `static_only`, `semantic_only`. Three repetitions per stochastic scenario-strategy cell.

Freeze per-run budgets (input tokens, output tokens, model calls, repair calls, timeouts) after the pilot. If the balanced confirmatory design is infeasible, stop and approve a balanced reduced design before main execution.

## 2. Sequential Execution (per AC-06)

Each strategy starts from the same clean snapshot. Scenarios applied sequentially in predefined evolution order. Only an accepted state becomes the next scenario's base state. If a scenario fails after the repair budget, stop that sequential chain for that strategy.

Also run remaining scenarios independently from predefined base snapshots for per-scenario analysis. Report sequential-chain and independent-scenario results separately.

Randomize or counterbalance strategy order and, where feasible, repository order across repetitions. Record order seeds. Fresh run directories must isolate caches and prior outputs.

## 3. Failure Classification

| Failure Class | Definition | Handling |
|--------------|-----------|----------|
| Infrastructure | System crash, OOM, network timeout | Retry (up to 3x); if persistent, report and exclude as infrastructure failure |
| Model output | Model returns empty/truncated/nonsensical output | Retry (up to 2x) with same prompt; if persistent, record as model failure |
| Build | Generated code does not compile/build | Record as failed run; attempt repair |
| Changed requirement | Changed-requirement tests fail | Record as failed run; attempt repair |
| Regression | Regression tests fail after change | Record as failed run; attempt repair |
| Architecture | Architecture constraints violated | Record as failed run; attempt repair |
| Timeout | Run exceeds time budget (frozen after pilot) | Terminate; record as timeout failure |
| Harness defect | Bug in benchmark harness | Correct and rerun under pilot rules or protocol amendment; not a strategy failure |

## 4. Repair Policy (per AC-05)

Comparable generative strategies receive the same repair budget and feedback.

Default main-study policy:
- One initial generation
- Maximum **two** LLM repair attempts
- Deterministic syntax/format normalization only when strategy-independent and logged

Freeze the final repair budget after the pilot.

## 5. Failed Strategies (per AC-04)

**Failed strategies remain in results.** Do not remove a strategy from repository aggregates merely because all runs fail. Include failures in:
- Attempted-run success rate
- Failure taxonomy
- Robustness analysis

Conditional metrics among successful runs must be labelled conditional.

## 6. Partial Completion

If a strategy fails on some scenarios but not others, all results are reported. No imputation of missing values for failed runs. Per-scenario sample sizes reported alongside aggregate statistics.

## 7. Run Cancellation

A run may be manually cancelled if it exceeds 2× the expected runtime. Cancellation reason documented in run log.

## 8. Kaggle Cost Reporting (per AC-08)

Report tokens, GPU time, wall-clock time, and Kaggle resource use. Do not invent API monetary cost for the attached Kaggle model. Any estimated compute cost must state its assumptions and must not be presented as an observed charge.
