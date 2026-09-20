# STAGE5_EXECUTION_DEFECT_REPORT (2026-09-20)

**Mission:** STAGE-5 EXECUTION DEFECT - RECORD -> REPRODUCE -> FIX ->
LABEL-FREE PARITY GATE -> CORRECTED RE-EXECUTION
**Verdict (diagnosis):** `STAGE5_V2_EXECUTION_INVALID_EMBEDDING_COVERAGE_DEFECT`
**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731
**Tier:** T3
**Companion:** `reports/stage5_execution_defect_reproduction.json`,
`docs/STAGE5_EXECUTION_DEFECT_CORRECTION_IMPACT_DECLARATION_2026-09-20.md`,
`DECISIONS.md` P86
**Note:** This report is a DIAGNOSIS. It was written after the independent
reproduction below confirmed every count from the persisted invalid artifacts.
Nothing here is treated as an unquestioned assertion.

---

## 1. What the first Stage-5 run did wrong (root cause)

The frozen Stage-5 dense-score generator
`scripts/stage5_v2_dense_scores.py` was required (by the frozen preregistration
execution step 3 and the frozen DEV missing-unit semantics) to produce a dense
file score for every legal production file in the 139 Stage-5 candidate
universes, embedding any Stage-5 code unit NOT already present in the persisted
realization-A cache, and representing a file with NO embeddable unit as
`NaN` (the frozen DEV convention).

Instead, the Stage-5 scorer reused the DEV blob-text/unit cache and, for a
Stage-5 blob unseen in that DEV cache, silently assigned a FINITE sentinel:

```
scripts/stage5_v2_dense_scores.py:206   keys = plan.get(sha, []) if sha else []
scripts/stage5_v2_dense_scores.py:207   rows_ = [cache_idx[k] for k in keys if k in cache_idx]
scripts/stage5_v2_dense_scores.py:208   if not rows_:
scripts/stage5_v2_dense_scores.py:209       scores[path] = -1e9        # <-- FINITE SENTINEL (defect)
scripts/stage5_v2_dense_scores.py:210       continue
```

`plan` is derived from the DEV blob-text cache
(`BLOB_CACHE = ...\swerank-cache\blob_text.json`, line 44) via
`build_plan` (lines 138-145). For any Stage-5 blob whose text is not in that
DEV cache, `plan.get(sha, [])` returns `[]`, `rows_` is empty, and the code
assigns `-1e9` instead of (a) embedding the new units, or (b) `NaN` if the blob
truly has no embeddable unit.

The frozen feature builder only imputes NON-finite values:

```
src/benchmark/memory_rescue/candidates.py:146   scores = np.where(np.isfinite(g["dense_file_score"]...),
src/benchmark/memory_rescue/candidates.py:147                             g["dense_file_score"]..., floor)
src/benchmark/calibrated/features.py:78-90      no_units_score -> min_finite - 1 (NaN imputation floor)
src/benchmark/calibrated/features.py:93-96      _impute_scores: np.where(np.isfinite(arr), arr, floor)
```

Because `-1e9` is finite, the NaN path never fired; the extreme value flowed
into the frozen StandardScaler (DEV-fit mean/scale ~0.49/0.128 for
`dense_file_score`) and `gap_to_top1 = score_max - score`, producing extreme
standardized features, logits, and `prob = 0` for affected rows. This
contradicts the frozen DEV missing-unit rule (NaN, never a finite sentinel) and
the frozen Stage-5 preregistration rule that new corpus embeddings MUST be
created when the persisted cache does not cover the tasks.

## 2. Why the first Stage-5 result is INVALID

- The Stage-5 `full_file_scores_stage5.parquet` was contaminated with finite
  `-1e9` sentinel scores (7,074/74,918 rows).
- Candidate features built on those rows are extreme and un-scientific; 245
  candidate probabilities collapsed to exactly 0 (60 of them Sparse rows, of
  which 34 were proxy true positives).
- The memory-bundle `cochange_top1` seeds were computed from a corrupted dense
  rank-1, so the structural-memory channel was also affected.
- The downstream V2 final sets / pooled Delta F1 (0.2269 vs 0.2857) are
  therefore NOT a valid execution of the preregistered frozen V2 pipeline.
- `STAGE5_V2_FINAL_CONFIRMATION_FAIL` is SCIENTIFICALLY SUPERSEDED by
  `STAGE5_V2_EXECUTION_INVALID_EMBEDDING_COVERAGE_DEFECT`. The old negative
  numbers must NOT be cited as evidence about V2 generalization.

## 3. Independent reproduction (from persisted artifacts only)

All counts below are recomputed by
`scripts/stage5_execution_defect_reproduce.py` from the persisted invalid
artifacts (no analyzer import). Full JSON:
`reports/stage5_execution_defect_reproduction.json`.

| # | claim | recomputed | exact? |
|---|---|---|---|
| A | full-file-score rows == -1e9 | **7,074** | yes |
| B | sentinel rows whose path had valid DEV embeddings | **2,062** (dc 268, saleor 1,794) | yes |
| C | candidate rows forced to prob exactly 0 | **245 / 4,815** | yes |
| D | Sparse candidate rows forced to prob 0 | **60 / 261** | yes |
| E | of those 60, proxy true positives | **34** | yes |
| F | total Sparse TPs dropped by invalid V2; directly hit | **39** total; **34 / 39** (own score == -1e9, prob 0) | yes |
| G | gold non-Sparse candidate rows forced to zero | **63 / 162** | yes |
| H | candidate dense-score distribution vs DEV | mean ≈ **-50,882,657.9** vs DEV **0.3793** (tens of millions negative) | yes |

Supporting facts:
- FFS NaN count = 0 (the invalid run never emitted the frozen NaN marker).
- DEV reference NaN rates: djangoCMS **5.27%**, Saleor **8.35%** (matches the
  frozen ±3pp parity references ≈5.3% / ≈8.4%).
- Sentinel composition: **1,320 rows** (1,114 unique blobs) are blobs whose
  TEXT IS MISSING from the DEV blob cache (these SHOULD have been embedded);
  **5,754 rows** are the GIT EMPTY BLOB (`e3b0c44…`, sha256 of empty string) —
  files truly empty at the parent commit, which under frozen DEV semantics
  MUST be `NaN`, not a finite sentinel.
- 1,241 unique non-empty Stage-5 blobs are missing from the DEV blob-text cache
  (1,114 appear in sentinel rows; the rest are referenced in candidate
  universes). All 1,241 are materializable from the pinned git caches via
  `git show <parent>:<path>` with SHA-256 exactly matching the
  candidate-universe record.

## 4. Cost projection for the corrective embedding (pre-call estimate)

- missing non-empty blobs to materialize: **1,241** (0 git misses);
- missing code units to embed: **1,489**;
- estimated unit tokens (≈3.5 chars/token over 10,332,283 chars):
  ≈ **2,952,081**;
- projected cost at the frozen $0.01/M (DeepInfra): ≈ **$0.0295**;
- plus Stage-5 query re-embed (139 intents, ≈5,827 tokens): ≈ **$0.00006**;
- total ≈ **$0.0296 << $0.25 hard ceiling**. Live price will be re-verified
  before call 1.

## 5. Exact fix (scope-limited, no scientific change)

1. Materialize the missing Stage-5 blob texts from the pinned git caches at the
   task parent commit; verify each content SHA-256 == candidate-universe record.
2. CASE A (cache hit): reuse the realization-A embedding exactly.
3. CASE B (cache miss, file has embeddable units): split with the SAME frozen
   `extract_code_units`, embed missing units with `qwen/qwen3-embedding-8b` @
   DeepInfra (fallback disabled), same MAX-cosine aggregation + full-universe
   rank.
4. CASE C (no embeddable unit, incl. empty blob): dense score = `NaN` (frozen
   DEV semantics; the feature builder imputes `min_finite - 1`).
5. NEVER emit a finite sentinel (-1e9 / -1e6 / -999999) for no-unit or
   missing-embedding state.
6. HARD PIPELINE GUARDS: fail if `abs(dense_file_score) > 10` for any finite
   candidate dense score; fail if a blob has embeddable units but no embedding
   result; fail if a required cache lookup silently resolves to a finite
   sentinel; fail if dense scores are out of the scientific range without an
   explicit documented reason; NO silent fallback.

## 6. Corrected re-execution status

- Population: the SAME exposed 139 tasks (dc RESERVE 59 + Saleor IT 80).
- Sparse write sets REUSED exactly from
  `research/stage5-v2-final/sparse_stage5_run_records.jsonl` (no Sparse LLM
  re-call).
- Frozen V2 model / scaler / threshold 0.20 / realization A / endpoint /
  bootstrap seed 20260920 reused exactly. NO refit, NO retuning.
- Result label: `STAGE5_CORRECTED_REEXECUTION_POSITIVE` / `_NEGATIVE` /
  `_MIXED` (NOT `STAGE5_V2_FINAL_CONFIRMATION_PASS`), because the population is
  no longer untouched.
- Saleor RESERVE stays SEALED. No new djangoCMS mining. No V3.

## 7. Boundaries held

- `IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED` preserved.
- Historical preregistration tag `stage5-v2-final-preregistered-2026-09-20` and
  invalid-evaluation tag `stage5-v2-final-evaluation-2026-09-20` preserved.
- Invalid artifacts preserved (never deleted).
- New tag (after corrected run): `stage5-corrected-reexecution-2026-09-20`.