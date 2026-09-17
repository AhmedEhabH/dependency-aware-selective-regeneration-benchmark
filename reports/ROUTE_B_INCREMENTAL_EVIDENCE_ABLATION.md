# Route B — Incremental-Evidence Ablation (zero API)

**Date:** 2026-09-17  **Type:** CHARACTERIZATION/ABLATION (no method tuning, no method change)
**Basis:** frozen Route-B V2 protocol applied to djangoCMS and Saleor DEVELOPMENT run records.
Primary endpoint = Omission Recovery Rate @ B (macro).

## Interpretation guide

- `Composite` = frozen `BM25+Graph-Neighbor Composite (historical label: CIA)`.
- The key question is whether graph-neighbor evidence adds materially to BM25 alone or whether
  the replicated transfer signal is predominantly lexical.
- No new ranker is chosen from this analysis; the frozen confirmatory method is unchanged.


### djangoCMS — incremental evidence (N=174)

| B | Random | BM25 | Graph | Composite | CIA−BM25 Δ (boot 95% CI) | Graph−Random | Jaccard overlap comp vs BM25 | extra FN comp−BM25 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.006 | 0.046 | 0.005 | 0.046 | +0.001 [-0.007, +0.008] | -0.001 | 0.810 | +1 |
| 3 | 0.017 | 0.113 | 0.052 | 0.118 | +0.004 [-0.017, +0.024] | +0.035 | 0.786 | +5 |
| 5 | 0.028 | 0.161 | 0.089 | 0.163 | +0.003 [-0.015, +0.019] | +0.061 | 0.765 | +5 |
| 10 | 0.057 | 0.226 | 0.148 | 0.251 | +0.025 [-0.002, +0.055] | +0.091 | 0.751 | +11 |

### Saleor — incremental evidence (N=149)

| B | Random | BM25 | Graph | Composite | CIA−BM25 Δ (boot 95% CI) | Graph−Random | Jaccard overlap comp vs BM25 | extra FN comp−BM25 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.001 | 0.072 | 0.005 | 0.077 | +0.005 [+0.000, +0.013] | +0.004 | 0.913 | +2 |
| 3 | 0.004 | 0.158 | 0.005 | 0.158 | +0.000 [+0.000, +0.000] | +0.001 | 0.876 | +0 |
| 5 | 0.006 | 0.234 | 0.005 | 0.237 | +0.003 [-0.017, +0.024] | -0.001 | 0.854 | +2 |
| 10 | 0.012 | 0.315 | 0.009 | 0.317 | +0.003 [-0.021, +0.028] | -0.003 | 0.831 | +0 |

### History / co-change arm (parent-visible, where available)

- **djangoCMS:** parent-visible history is available on 94/174 DEVELOPMENT tasks (frozen
  `research/transparency/route_b_history_arm_results.json`). History beats analytic Random on
  that subset (B=5: History macro ORR 0.241 vs analytic Random 0.034, Δ +0.207) and is broadly
  comparable to the composite (CIA macro ORR 0.246 on the same 94-task subset). History is an
  ADDITIONAL predeclared arm, NOT the frozen primary.
- **Saleor:** parent-visible history cache is NOT available (`dist/real-commit-cache/saleor`
  absent). History is recorded as UNAVAILABLE for Saleor; no co-change arm is computed there.

## Notes

- Paired task-level delta (composite − BM25) with a task-level bootstrap CI (seed 20260917,
  2000 resamples); task is the independent unit.
- Jaccard overlap of top-B sets composite vs BM25 (1.0 = identical top-B sets on that task;
  the table reports the mean across tasks).
- extra FN = (composite recovered FNs) − (BM25 recovered FNs) summed over tasks; positive =
  the composite recovers additional omitted files beyond BM25 at the same budget.
- Saleor `Graph` arm ≈ binary neighbor only; the Saleor dependency graph is sparser, which the
  graph-vs-random row reflects.
- Full machine-readable results: `research/transparency/route_b_incremental_ablation.json`.