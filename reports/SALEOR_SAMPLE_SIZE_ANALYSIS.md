# Saleor Stage-2 — Sample-Size Analysis

**Date:** 2026-09-16  **Eligible pool:** 1316 (reconstructed).
Uses djangoCMS development negative-prevalence sensitivity; NEVER tunes a test.

## Key rows (observed prevalence 13.3%)

| N | exp neg | P(>=10) | P(>=20) | 3-rep tokens | 3-rep cost $ | <=450 cells |
|---|---:|---:|---:|---:|---:|---:|
| 120 | 16 | 0.97 | 0.17 | 2,084,880 | 0.73 | True |
| 150 | 20 | 1.00 | 0.53 | 2,606,100 | 0.91 | True |
| 200 | 27 | 1.00 | 0.94 | 3,474,800 | 1.21 | False |
| 300 | 40 | 1.00 | 1.00 | 5,212,200 | 1.82 | False |

## Recommendation

Saleor eligible pool (1316) >> djangoCMS (329); N=120-150 Saleor development tasks is comfortably within the pool and the 450-cell/2.5M-token/$1.00 ceiling pattern.

Saleor's eligible pool (1316) is 4x djangoCMS's (329), so a quantitative
Stage-2 development set (e.g. N=120-150) plus an untouched internal test
is fully supported without consuming the pool.