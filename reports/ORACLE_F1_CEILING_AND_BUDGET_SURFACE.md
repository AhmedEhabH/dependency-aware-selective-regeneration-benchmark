# Oracle F1 Ceiling and Budget Surface

**Date:** 2026-09-18
**Tier:** T3 (ZERO API, ZERO model calls)
**Mission:** OPENCODE_ORACLE_GAP_BIDIRECTIONAL_REPAIR_MISSION_2026-09-18
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731
**Data:** djangoCMS DEVELOPMENT (174) + Saleor DEVELOPMENT (149) = PRIMARY design
evidence. The spent djangoCMS INTERNAL_TEST is reported separately as POST-HOC
sanity in `reports/ORACLE_GAP_ERROR_DECOMPOSITION.md` §1–§2.
**Machine-readable:** `reports/oracle_f1_ceiling_and_budget_surface.json`.

These are **deterministic oracle upper bounds** (perfect add / perfect drop).
They define what is *mathematically* possible; they are NOT method budgets and
NOT permission to tune until a number is reached.

---

## 1. Sparse baseline (reference)

| Repo | n | TP | FP | FN | P | R | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| djangoCMS DEV | 174 | 125 | 155 | 382 | 0.4464 | 0.2465 | 0.3177 |
| Saleor DEV | 149 | 99 | 193 | 369 | 0.3390 | 0.2115 | 0.2605 |

## 2. A. ORACLE-ADD (perfect add, zero FP)

| A | djangoCMS P/R/F1 | Saleor P/R/F1 |
|---|---:|---:|
| 0 (Sparse) | 0.4464 / 0.2465 / 0.3177 | 0.3390 / 0.2115 / 0.2605 |
| 1 | 0.5590 / 0.4004 / **0.5915** | 0.4363 / 0.3526 / **0.5096** |
| 2 | 0.6284 / 0.5227 / **0.7294** | 0.5125 / 0.4529 / **0.6371** |
| 3 | 0.6732 / 0.6124 / **0.7964** | 0.5665 / 0.5321 / **0.7102** |
| 5 | 0.7213 / 0.7258 / **0.8406** | 0.6248 / 0.6553 / **0.7816** |
| 10 | 0.7614 / 0.9083 / **0.8674** | 0.6744 / 0.8707 / **0.8270** |
| ALL | 0.7659 / 1.0 / **0.8674** | 0.7080 / 1.0 / **0.8291** |

## 3. B. ORACLE-DROP (perfect drop, zero TP removed)

| D | djangoCMS P/R/F1 | Saleor P/R/F1 |
|---|---:|---:|
| 1 | 0.5650 / 0.2465 / 0.3561 | 0.4406 / 0.2115 / 0.2907 |
| 2 | 0.6674 / 0.2465 / 0.3782 | 0.5264 / 0.2115 / 0.3108 |
| 3 | 0.7610 / 0.2465 / 0.3876 | 0.6059 / 0.2115 / 0.3220 |
| 5 | 0.8964 / 0.2465 / 0.3943 | 0.7427 / 0.2115 / 0.3350 |
| 10 | 0.9661 / 0.2465 / 0.3956 | 0.8631 / 0.2115 / 0.3443 |
| ALL | 1.0 / 0.2465 / 0.3956 | 1.0 / 0.2115 / 0.3492 |

## 4. C. ORACLE-BIDIRECTIONAL (A × D grid, F1)

**djangoCMS DEV**

| A \ D | 0 | 1 | 3 | 5 | ALL |
|---|---:|---:|---:|---:|---:|
| 0 | 0.3177 | 0.3561 | 0.3876 | 0.3943 | 0.3956 |
| 1 | 0.5915 | 0.6503 | 0.6967 | 0.7065 | 0.7083 |
| 2 | 0.7294 | 0.7941 | 0.8444 | 0.8549 | 0.8568 |
| 3 | 0.7964 | 0.8631 | 0.9144 | 0.9250 | 0.9270 |
| 5 | 0.8406 | 0.9082 | 0.9600 | 0.9707 | 0.9726 |
| 10 | 0.8674 | 0.9354 | 0.9873 | 0.9980 | 1.0 |
| ALL | 0.8674 | 0.9354 | 0.9873 | 0.9980 | 1.0 |

**Saleor DEV**

| A \ D | 0 | 1 | 3 | 5 | ALL |
|---|---:|---:|---:|---:|---:|
| 0 | 0.2605 | 0.2907 | 0.3220 | 0.3350 | 0.3492 |
| 1 | 0.5096 | 0.5594 | 0.6092 | 0.6295 | 0.6513 |
| 2 | 0.6371 | 0.6936 | 0.7491 | 0.7715 | 0.7954 |
| 3 | 0.7102 | 0.7696 | 0.8273 | 0.8505 | 0.8750 |
| 5 | 0.7816 | 0.8429 | 0.9021 | 0.9258 | 0.9507 |
| 10 | 0.8270 | 0.8893 | 0.9491 | 0.9729 | 0.9979 |
| ALL | 0.8291 | 0.8914 | 0.9512 | 0.9750 | 1.0 |

Mean inspections/task for the minimal region (from the reachability grid):
djangoCMS F1=0.85: A=10,D=0 → 2.20/task; Saleor F1=0.85: A=3,D=5 → 2.91/task.

## 5. D. F1-target reachability (is 0.85 mathematically reachable?)

| Target | djangoCMS add-only | djangoCMS drop-only | djangoCMS bidirectional (min) | Saleor add-only | Saleor drop-only | Saleor bidirectional (min) |
|---|---:|---:|---:|---:|---:|---:|
| 0.50 | A=1 | — | A=1,D=0 (0.88/task) | A=1 | — | A=1,D=0 (0.85/task) |
| 0.60 | A=2 | — | A=1,D=1 (1.37/task) | A=2 | — | A=2,D=0 (1.41/task) |
| 0.70 | A=2 | — | A=2,D=0 (1.47/task) | A=3 | — | A=3,D=0 (1.78/task) |
| 0.80 | A=5 | — | A=5,D=0 (2.04/task) | A=10 | — | A=10,D=0 (2.46/task) |
| **0.85** | **A=10** | — | A=10,D=0 (2.20/task) | **UNREACHABLE add-only** (ceiling 0.8291) | — | **A=3,D=5 (2.91/task)** |
| 0.90 | — | — | A=5,D=1 (2.53/task) | — | — | A=5,D=3 (3.15/task) |

**Answer to the mission question:**
- **djangoCMS:** F1 = 0.85 IS mathematically reachable by **add-only** (A=10
  oracle, 2.20 inspections/task). It is also reachable bidirectionally at less
  cost (A=3,D=5 → F1 0.9250).
- **Saleor:** F1 = 0.85 is **NOT reachable by add-only** — even perfect adds at
  A=ALL cap at **0.8291** because the 193-file Sparse FP tail pins precision at
  0.708. Bidirectional repair is **required** (e.g. A=3,D=5 → 0.8505).
- **F1 = 0.90 requires bidirectional repair on both repos.**
- **What prevents 0.85 on Saleor add-only:** the Sparse first-pass FP tail.
  First-pass precision loss (FP/P = 0.661 on Saleor) is the binding constraint
  once recall is perfect. Add-only can fix recall but cannot remove Sparse FPs.

Machine-readable: `reports/oracle_f1_ceiling_and_budget_surface.json`.