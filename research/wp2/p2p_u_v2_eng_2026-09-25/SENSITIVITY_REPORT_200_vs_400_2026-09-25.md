# P2P-U V2 ENG — 200-vs-400 Sensitivity Report (2026-09-25)

**Status:** cap200 = PRIMARY (preregistered); cap400 = descriptive sensitivity. No post-hoc threshold selects 200 vs 400 (Mission-09 §13/§21).

## 1. SELECTION (per executed ENG task)

| task | raw | cap200 | cap400 | c200 P/D | c400 P/D | prox dist |
|---|---|---|---|---|---|---|
| saleor-rc-2d45b76a52f2 | 176 | 176 | 176 | 0/176 | 0/176 | [1] |
| saleor-rc-39b4138e8550 | 10582 | 200 | 400 | 150/50 | 300/100 | [1, 2] |
| saleor-rc-74538ea00ce9 | 8062 | 200 | 400 | 150/50 | 300/100 | [1, 2] |
| saleor-rc-82c56bde0e34 | 8147 | 200 | 400 | 150/50 | 300/100 | [1, 2, 3] |
| saleor-rc-8f76ddc6267f | 6130 | 200 | 400 | 116/84 | 116/284 | [1, 2] |
| saleor-rc-d220843b5418 | 10726 | 200 | 400 | 150/50 | 204/196 | [1, 2] |
| saleor-rc-dfe77ac1c5dc | 434 | 200 | 400 | 0/200 | 0/400 | [1] |
| saleor-rc-e03ee76d2b89 | 6338 | 200 | 400 | 150/50 | 165/235 | [1, 2] |

## 2. OUTCOMES (class distributions)

### saleor-rc-2d45b76a52f2

| cap | n | STABLE_P2P | TARGET_BROKEN | PARENT_BROKEN | BOTH_FAIL | FLAKY | COLLECTION_ERROR | stable_rate |
|---|---|---|---|---|---|---|---|---|
| 200 | 176 | 176 | 0 | 0 | 0 | 0 | 0 | 1.0 |
| 400 | 176 | 176 | 0 | 0 | 0 | 0 | 0 | 1.0 |

### saleor-rc-39b4138e8550

| cap | n | STABLE_P2P | TARGET_BROKEN | PARENT_BROKEN | BOTH_FAIL | FLAKY | COLLECTION_ERROR | stable_rate |
|---|---|---|---|---|---|---|---|---|
| 200 | 200 | 195 | 0 | 0 | 0 | 0 | 5 | 0.975 |
| 400 | 400 | 393 | 0 | 0 | 0 | 2 | 5 | 0.9825 |

### saleor-rc-74538ea00ce9

| cap | n | STABLE_P2P | TARGET_BROKEN | PARENT_BROKEN | BOTH_FAIL | FLAKY | COLLECTION_ERROR | stable_rate |
|---|---|---|---|---|---|---|---|---|
| 200 | 200 | 181 | 0 | 0 | 0 | 1 | 18 | 0.905 |
| 400 | 400 | 369 | 0 | 0 | 0 | 1 | 30 | 0.9225 |

### saleor-rc-82c56bde0e34

| cap | n | STABLE_P2P | TARGET_BROKEN | PARENT_BROKEN | BOTH_FAIL | FLAKY | COLLECTION_ERROR | stable_rate |
|---|---|---|---|---|---|---|---|---|
| 200 | 200 | 195 | 0 | 0 | 1 | 0 | 4 | 0.975 |
| 400 | 400 | 384 | 0 | 0 | 7 | 0 | 9 | 0.96 |

### saleor-rc-8f76ddc6267f

| cap | n | STABLE_P2P | TARGET_BROKEN | PARENT_BROKEN | BOTH_FAIL | FLAKY | COLLECTION_ERROR | stable_rate |
|---|---|---|---|---|---|---|---|---|
| 200 | 200 | 194 | 0 | 0 | 0 | 0 | 6 | 0.97 |
| 400 | 400 | 378 | 0 | 0 | 0 | 0 | 22 | 0.945 |

### saleor-rc-d220843b5418

| cap | n | STABLE_P2P | TARGET_BROKEN | PARENT_BROKEN | BOTH_FAIL | FLAKY | COLLECTION_ERROR | stable_rate |
|---|---|---|---|---|---|---|---|---|
| 200 | 200 | 193 | 0 | 0 | 4 | 0 | 3 | 0.965 |
| 400 | 400 | 388 | 0 | 0 | 4 | 0 | 8 | 0.97 |

### saleor-rc-dfe77ac1c5dc

| cap | n | STABLE_P2P | TARGET_BROKEN | PARENT_BROKEN | BOTH_FAIL | FLAKY | COLLECTION_ERROR | stable_rate |
|---|---|---|---|---|---|---|---|---|
| 200 | 200 | 197 | 0 | 0 | 0 | 0 | 3 | 0.985 |
| 400 | 400 | 397 | 0 | 0 | 0 | 0 | 3 | 0.9925 |

### saleor-rc-e03ee76d2b89

| cap | n | STABLE_P2P | TARGET_BROKEN | PARENT_BROKEN | BOTH_FAIL | FLAKY | COLLECTION_ERROR | stable_rate |
|---|---|---|---|---|---|---|---|---|
| 200 | 200 | 196 | 0 | 0 | 2 | 0 | 2 | 0.98 |
| 400 | 400 | 382 | 0 | 0 | 5 | 0 | 13 | 0.955 |

## 3. OVERLAP REPEATABILITY (first-200 identities, independent executions)

| task | overlap n | class agree | stable agree | changed | Jaccard STABLE_P2P |
|---|---|---|---|---|---|
| saleor-rc-2d45b76a52f2 | 176 | 1.0 | 1.0 | 0 | 1.0 |
| saleor-rc-39b4138e8550 | 200 | 1.0 | 1.0 | 0 | 1.0 |
| saleor-rc-74538ea00ce9 | 200 | 1.0 | 1.0 | 0 | 1.0 |
| saleor-rc-82c56bde0e34 | 200 | 1.0 | 1.0 | 0 | 1.0 |
| saleor-rc-8f76ddc6267f | 200 | 1.0 | 1.0 | 0 | 1.0 |
| saleor-rc-d220843b5418 | 200 | 1.0 | 1.0 | 0 | 1.0 |
| saleor-rc-dfe77ac1c5dc | 200 | 1.0 | 1.0 | 0 | 1.0 |
| saleor-rc-e03ee76d2b89 | 200 | 1.0 | 1.0 | 0 | 1.0 |

## 4. Aggregate stable rates

| metric | cap200 | cap400 |
|---|---|---|
| min | 0.905 | 0.9225 |
| max | 1.0 | 1.0 |
| avg | 0.9694 | 0.9659 |
| median | 0.975 | 0.97 |
| overall (nodes) | 0.9689 | 0.9634 |

## 5. Cost / resource comparison

| dimension | cap200 | cap400 | multiplier |
|---|---|---|---|
| total wall (s) | 4346.9 | 5955.8 | 1.37 |
| selected nodes | 1576 | 2976 | 1.89 |
| stable nodes | 1527 | 2867 | 1.88 |
| WSL peak used (GiB) | 1.59 | 1.616 | - |
| host peak used (GiB) | 24.394 | 24.859 | - |
| evidence (MiB) | ~31.5* | ~59.5* | - |

*Evidence bytes/node estimate from the 59.3 MiB total across all 16 runs (59.3 MiB / 4552 node-state totals ≈ 13 KB/node-state).

## 6. Conclusion (preregistered)

- **Deterministic nesting:** PASS — first_200 ⊂ first_400 for every task (frozen at selection time).
- **Independent-execution overlap class agreement:** perfect (1.0) for all 8 executed ENG tasks.
- **Stable-rate difference per task:** cap400 vs cap200 are 0.9689 vs 0.9634 overall (within ~0.5pp; no material instability).
- **Runtime multiplier (400/200):** 1.37x total wall.
- **cap200 remains PRIMARY.** cap400 sensitivity does not retune K.
- No serious instability detected that would require `P2P_V2_ENG_ISSUES` on repeatability grounds.
