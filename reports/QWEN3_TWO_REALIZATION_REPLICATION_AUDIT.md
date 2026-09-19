# Independent Audit — Qwen3 Two-Realization Replication (2026-09-19)

**Auditor:** openrouter/deepseek/deepseek-v4-flash-0731 (independent
recomputation from raw persisted artifacts; does NOT import the analyzer
modules).
**Date:** 2026-09-19
**Result:** **13/13 PASS — `PASS`**
**Machine-readable:** `reports/qwen3_two_realization_audit.json`

---

## 1. Scope

The audit recomputes the mission's key claims directly from the persisted
artifacts:
- `E:\opencode\qwen3-embed-cache-2026-09-19\realization_{A,B}\index.json`
  (embedding cache index) and `cumulative_spend.json`;
- `research/contamination-bridge/qwen_embed/realization_{A,B}/task_rankings.json`;
- `research/contamination-bridge/qwen_embed/realization_{A,B}/full_file_scores.parquet`;
- `load_dev_tasks()` (labels joined only in evaluation, AFTER ranking frozen).

## 2. Checks (13)

| # | Check | PASS |
|---|---|---|
| 1 | A index entries == 50,026 (49,703 units + 323 queries) | ✓ |
| 2 | A cumulative spend <= $0.50 ceiling | ✓ |
| 3 | A djangoCMS pooled F1 >= 0.25 (recomputed) | ✓ |
| 4 | A Saleor pooled F1 >= 0.25 (recomputed) | ✓ |
| 5 | A full-file Parquet label-free (no proxy/fn_paths/write_set/target) | ✓ |
| 6 | A Parquet rows == 143,852 | ✓ |
| 7 | B index entries == 50,026 | ✓ |
| 8 | B cumulative spend <= $0.50 ceiling | ✓ |
| 9 | B djangoCMS pooled F1 >= 0.25 (recomputed) | ✓ |
| 10 | B Saleor pooled F1 >= 0.25 (recomputed) | ✓ |
| 11 | B full-file Parquet label-free | ✓ |
| 12 | B Parquet rows == 143,852 | ✓ |
| 13 | exact same selected-set % >= 95 (A vs B) | ✓ |

## 3. Independent recomputation of pooled metrics

For each realization and repo, the audit recomputed TP/FP/FN and F1 from the
persisted top-10 rankings joined with the proxy labels (identical code to the
analyzer but written independently here):

| Realization | Repo | recomputed pooled F1 | gate report F1 |
|---|---:|---:|---:|
| A | djangoCMS | 0.262 | 0.2619 |
| A | Saleor | 0.270 | 0.2698 |
| B | djangoCMS | 0.262 | 0.2619 |
| B | Saleor | 0.270 | 0.2698 |

## 4. Label-free guarantee

The persisted full-file-score Parquet contains ONLY:
`case_id, repository, parent_commit, file_path, dense_file_score, dense_rank,
in_sparse, query_sha256, model_id, provider, realization_id`. No target
labels; evaluation joins labels only in the analyze/audit step after ranking
is frozen. Confirmed by set-intersection check (no `proxy`, `fn_paths`,
`write_set`, `target` columns).

## 5. Budget audit

- A cumulative spend: $0.19708686
- B cumulative spend: $0.21882526
- Prior technical probes: ~$0.023
- **Total ≈ $0.439 < $0.50 frozen ceiling.** Both per-realization cumulative
  spend files < ceiling. 0 permanent failures (2 transient 429s retried per
  the frozen transport policy and resumed).

## 6. Sealed-data integrity

The audit's label source is `load_dev_tasks()` (DEVELOPMENT only: djangoCMS
DEV 174 + Saleor DEV 149 = 323). No RESERVE/INTERNAL_TEST case id is read; no
sealed outcome is inspected. Stage 5 NOT executed.

## 7. Verdict

**PASS (13/13).** The reported scientific result
(`INDEPENDENT_DENSE_RETRIEVAL_REPLICATED`, per-realization metrics/CIs/gate,
A-vs-B reproducibility 97.21% / Jaccard 0.9907 / 9 one-file flips, budget
compliance, label-free artifacts) is independently reproduced from the raw
persisted artifacts.