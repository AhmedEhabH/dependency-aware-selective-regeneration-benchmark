# Route B — Candidate-Level Bounded Omission Recovery V1 (zero-LLM)

**Date:** 2026-09-16  **Tier:** T3  **Zero LLM cost**
**Data:** v1 TRAIN/VALIDATION + V2 DEV_TRAIN/DEV_VALIDATION (development only).
V2 INTERNAL_TEST/RESERVE untouched.

## Design

- Candidate unit: file omitted by the Sparse first pass.
- Label (evaluation-only): is_missed_positive = proxy-positive AND omitted by Sparse.
- Primary budget B=5; secondary B in {1,3,10}.
- Arms: R0 Random, R1 BM25, R2 Path-token, R3 Graph neighbor, R4 Classical CIA,
  R5 fixed hybrid, Oracle (evaluation-only).
- Primary metric: task-clustered missed-file recall (macro over tasks).

## Primary comparison at B=5 (predeclared best vs Random)

| Split | Best arm | Best macro recall | Random macro recall | Delta | Delta 95% CI |
|---|---|---:|---:|---:|---:|
| DEV_TRAIN | R4_CIA | 0.148 | 0.022 | +0.126 | [+0.069, +0.179] |
| DEV_VALIDATION | R4_CIA | 0.180 | 0.037 | +0.143 | [-0.003, +0.285] |
| POOLED | R4_CIA | 0.163 | 0.029 | +0.135 | [+0.085, +0.184] |

## Artifact / confound checks

- **Universe-size artifact:** corr(candidate-count, per-task CIA-vs-Random delta)
  = **+0.105** on DEV_VALIDATION -> the advantage is NOT a candidate-count artifact.
- **Leakage:** candidate features use only public parent-visible inputs (BM25 /
  path-token / graph-neighbor / intent overlap); `is_missed_positive` is
  evaluation-only. No hidden gold or future state enters a feature.
- **Direction stability:** R4_CIA beats Random at B=5 on both DEV_TRAIN and
  DEV_VALIDATION (same direction). DEV_VALIDATION point estimate +0.143 but its
  95% CI includes 0 (n=27 tasks); DEV_TRAIN CI excludes 0.

## Pooled macro recall by arm and budget

| Budget | Random | BM25 | PathToken | GraphNb | CIA | Hybrid | Oracle |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.009 | 0.046 | 0.002 | 0.005 | 0.046 | 0.046 | 0.509 |
| 3 | 0.023 | 0.113 | 0.003 | 0.052 | 0.118 | 0.118 | 0.815 |
| 5 | 0.029 | 0.161 | 0.003 | 0.089 | 0.163 | 0.163 | 0.858 |
| 10 | 0.045 | 0.226 | 0.006 | 0.148 | 0.251 | 0.251 | 0.879 |

## Notes

- Development-only; DEV_TRAIN and DEV_VALIDATION reported separately first.
- Task is the independent unit; candidate rows are NOT independent tasks.
- The observed diff remains an OBSERVED CHANGE-SET PROXY, never semantic gold.
- Full machine-readable results: research/transparency/route_b_v1_results.json