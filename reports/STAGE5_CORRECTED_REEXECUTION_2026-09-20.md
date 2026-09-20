# STAGE5 CORRECTED RE-EXECUTION REPORT (2026-09-20)

**Mission:** STAGE-5 EXECUTION DEFECT - RECORD -> REPRODUCE -> FIX ->
LABEL-FREE PARITY GATE -> CORRECTED RE-EXECUTION
**Verdict:** `STAGE5_CORRECTED_REEXECUTION_POSITIVE`
`IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED`
**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731
**Tier:** T3
**Companion documents:** `docs/STAGE5_EXECUTION_DEFECT_CORRECTION_IMPACT_DECLARATION_2026-09-20.md`,
`reports/STAGE5_EXECUTION_DEFECT_REPORT_2026-09-20.md`,
`reports/stage5_execution_defect_reproduction.json`,
`reports/stage5_parity_gate.json`, `reports/stage5_parity_gate_audit.json`,
`reports/stage5_corrected_reexecution_result.json`,
`reports/stage5_corrected_secondary_result.json`,
`reports/stage5_corrected_impact_analysis.json`,
`reports/stage5_corrected_result_audit.json`, `DECISIONS.md` P86/P87

---

## WHAT FAILED IN THE FIRST EXECUTION?

The first Stage-5 dense-score run (`scripts/stage5_v2_dense_scores.py`) reused
the DEV blob-text/unit cache and, for a Stage-5 blob not present in that DEV
cache, silently assigned `dense_file_score = -1e9` (a finite sentinel) instead
of embedding the new code units or representing them as NaN. 7,074 / 74,918
full-file-score rows were set to -1e9.

## WHY THE FIRST STAGE-5 RESULT IS INVALID

`-1e9` is finite, so the frozen feature builder's NaN imputation
(`no_units_score` -> `min_finite - 1`) never fired. StandardScaler received
extreme values, dense-score/gap features became extreme, and LR probabilities
collapsed to exactly zero for 245 candidate rows (60 Sparse rows, of which 34
were proxy true positives). The downstream V2 sets, pooled Delta F1 (−0.0588)
and `STAGE5_V2_FINAL_CONFIRMATION_FAIL` are NOT a valid execution of the
preregistered frozen V2 pipeline. The original run is therefore
EXECUTION-INVALID and its FAIL label is superseded (P86).

## HOW THE BUG WAS REPRODUCED

Independently recomputed from the persisted invalid artifacts
(`reports/stage5_execution_defect_reproduction.json`):

| # | quantity | recomputed | exact? |
|---|---|---|---|
| A | full-file-score rows == -1e9 | 7,074 | yes |
| B | sentinel rows whose path had valid DEV embeddings | 2,062 (dc 268 / saleor 1,794) | yes |
| C | candidate rows forced to prob exactly 0 | 245 / 4,815 | yes |
| D | Sparse candidate rows forced to prob 0 | 60 / 261 | yes |
| E | of those 60, proxy true positives | 34 | yes |
| F | Sparse TPs dropped by invalid V2; directly hit | 39 total; 34 / 39 | yes |
| G | gold non-Sparse candidate rows forced to zero | 63 / 162 | yes |
| H | candidate dense-score mean | −50,882,658 vs DEV 0.379 | yes |

Root cause confirmed in code: `scripts/stage5_v2_dense_scores.py:206-209`
(`plan.get(sha, [])` empty -> `scores[path] = -1e9`); the frozen feature
builder `src/benchmark/memory_rescue/candidates.py:146-147` only imputes
non-finite values; `src/benchmark/calibrated/features.py:78-96` defines the NaN
floor `min_finite - 1`. This violates the frozen Stage-5 preregistration rule
(new corpus embeddings REQUIRED when the cache does not cover the tasks).

## EXACT FIX

Pipeline correctness only; no scientific change. CASE A (cache hit): reuse the
realization-A embedding exactly. CASE B (cache miss but file has embeddable
units): materialize the Stage-5 blob from the pinned git cache at the task
parent commit (SHA-256 verified), split with the SAME frozen unit splitter, and
embed the missing units with `qwen/qwen3-embedding-8b` @ DeepInfra (fallback
disabled), same MAX-cosine aggregation. CASE C (no embeddable unit): NaN per
the frozen DEV semantics. No finite sentinel. 1,241 missing blobs materialized;
1,489 units embedded ($0.019927, 1,992,694 tokens); 139 queries embedded
($0.000058, 5,827 tokens); total $0.019985 << $0.25 ceiling.

HARD PIPELINE GUARDS added: fail if `abs(dense_file_score) > 10` for any finite
candidate dense score (`src/benchmark/memory_rescue/candidates.py`
`assert_finite_dense_score_bounds`); fail if a blob has embeddable units but no
embedding result; fail if a required cache lookup silently resolves to a finite
sentinel; fail if dense scores are out of range without an explicit documented
reason. No silent fallback.

## LABEL-FREE PARITY GATE

Ran BEFORE the corrected evaluator loaded any Stage-5 label.
`reports/stage5_parity_gate.json` **8/8 PASS** + independent parity audit
`reports/stage5_parity_gate_audit.json` **8/8 PASS** (agrees):
- A. Embedding coverage: 69,164 blobs-with-units, **0** unresolved misses.
- B. No finite sentinels: `==-1e9:0`, other sentinels: 0, |score|>10: 0.
- C. NaN/no-unit rate: djangoCMS 5.19% (DEV 5.27%), Saleor 8.07% (DEV 8.35%) —
  within ±3pp.
- D. Finite score range: [0.092, 0.820] within [-1.5, +1.5].
- E. Feature-distribution parity: all 9 continuous features within 3 DEV SD.
- F. Candidate rows/task: dc 32.6 vs DEV 31.9; saleor 34.9 vs DEV 34.8 (within
  ±25%).
- G. Feature schema: exact same 11 features, names, order, dtypes.
- H. Model hash: config_sha256 `8925d29a…`, threshold 0.20 (frozen).

## WHY THE CORRECTED RUN IS NOT UNTOUCHED ANYMORE

The 139 tasks (dc RESERVE 59 + Saleor INTERNAL_TEST 80) were exposed by the
original Stage-5 run and are treated as exposed. The corrected run is a
diagnostic/corrective re-execution answering only: "What would the original
frozen Stage-5 V2 pipeline have produced if the documented execution bug had
not corrupted dense features?" It is NOT untouched confirmation, NOT
independent confirmation, NOT a second clean Stage-5 test.

## CORRECTED DJANGOCMS RESULT

| | Sparse | V2 (corrected) | Delta |
|---|---|---|---|
| TP/FP/FN | 38 / 69 / 106 | 42 / 72 / 102 | +4 / +3 / −4 |
| Precision | 0.3551 | 0.3684 | +0.0133 |
| Recall | 0.2639 | 0.2917 | +0.0278 |
| FNR | 0.7361 | 0.7083 | −0.0278 |
| F1 | 0.3028 | 0.3256 | **+0.0228** |

## CORRECTED SALEOR RESULT

| | Sparse | V2 (corrected) | Delta |
|---|---|---|---|
| TP/FP/FN | 52 / 102 / 173 | 71 / 107 / 154 | +19 / +5 / −19 |
| Precision | 0.3377 | 0.3989 | +0.0612 |
| Recall | 0.2311 | 0.3156 | +0.0844 |
| FNR | 0.7689 | 0.6844 | −0.0844 |
| F1 | 0.2744 | 0.3524 | **+0.0780** |

## POOLED RESULT

| Metric | Value |
|---|---|
| Pooled V2 F1 (corrected) | 0.3419 |
| Pooled Sparse F1 | 0.2857 |
| **Delta F1 (point)** | **+0.0562** |
| 95% CI | **[+0.0185, +0.0945]** (excludes zero, positive) |
| Criterion A | PASS (point > 0, CI lower > 0) |
| djangoCMS point Delta F1 | +0.0228 |
| Saleor point Delta F1 | +0.0780 |
| Criterion B | PASS (both repos positive) |

**Verdict: `STAGE5_CORRECTED_REEXECUTION_POSITIVE`** (10,000 resamples, seed
20260920, task-paired bootstrap; independent result audit 13/13 PASS).

## INVALID VS CORRECTED DELTA

- 60,485 file scores changed; 4,438 candidate probabilities changed; 81
  selected flags changed.
- 60 previously forced-zero Sparse files -> 39 restored by corrected V2.
- Of the 34 previously affected Sparse proxy TPs: 27 retained by corrected V2
  (all 34 present in the corrected candidate universe).
- Pooled: TP 70 -> 113 (+43), FP 178 -> 179 (+1), FN 299 -> 256 (−43),
  F1 0.2269 -> 0.3419 (**Δ +0.1150**).
- Per repo F1 delta (invalid -> corrected): djangoCMS 0.2410 -> 0.3256
  (+0.0846); Saleor 0.2174 -> 0.3524 (+0.1350).

The embedding-coverage defect MATERIALLY changed the Stage-5 conclusion.

## RANKING / ACC@K CHANGES

Corrected dense rank-1 changed on 50/139 tasks; corrected dense top-20 changed
on 118/139 tasks (structural-memory seeds and candidate universes recomputed).

| Population (139) | Acc@1 | Acc@3 | Acc@5 | Hit@1 | Hit@3 | Hit@5 | Recall@1/3/5 |
|---|---|---|---|---|---|---|---|
| Invalid V2 | 0.2374 | 0.1223 | 0.1223 | 0.2374 | 0.4173 | 0.4748 | 0.1004/0.2220/0.2683 |
| **Corrected V2** | **0.3741** | **0.1871** | **0.2302** | **0.3741** | **0.6115** | **0.6906** | **0.1603/0.3341/0.4456** |
| djangoCMS corrected | 0.2712 | 0.1695 | 0.1864 | 0.2712 | 0.5593 | 0.6271 | 0.1281/0.3143/0.3951 |
| Saleor corrected | 0.4500 | 0.2000 | 0.2625 | 0.4500 | 0.6500 | 0.7375 | 0.1840/0.3488/0.4828 |

Acc@K / Hit@K / Recall@K are descriptive compatibility numbers, NOT gate
criteria.

## WHAT THE CORRECTED RESULT MEANS

On the exposed 139 tasks, with the embedding-coverage defect repaired, the
frozen V2 policy IMPROVES over Sparse (pooled Delta F1 +0.0562, CI
[+0.0185, +0.0945], both repos positive). The corrected V2 is more precise and
more sensitive than Sparse on both repositories. This is the number the frozen
pipeline would have produced without the execution bug.

## WHAT IT DOES NOT PROVE

- It is NOT untouched confirmatory evidence (the 139 tasks were exposed).
- It does NOT restore untouched status to any task.
- It does NOT prove V2 generalizes to unseen data.
- It does NOT open or use Saleor RESERVE.
- It does NOT show there is any remaining untouched djangoCMS population.
- It does NOT change the frozen method-selection closure.

## WHAT UNTOUCHED DATA REMAINS

Saleor RESERVE (1,086 tasks) is the only untouched population in the current
split. djangoCMS RESERVE (59) and Saleor INTERNAL_TEST (80) are exposed. There
is NO remaining untouched djangoCMS confirmation population in the current
benchmark split.

## NEXT DECISION

A clean untouched replication (Saleor RESERVE only, 150 sampled seed 20260920,
corrected frozen V2 pipeline, same parity gate, Sparse comparator, Delta F1
endpoint; projected ~$0.61-0.62) is drafted for Ahmed's review
(`docs/CLEAN_SALEOR_RESERVE_REPLICATION_DRAFT_PREREGISTRATION_2026-09-20.md`)
and awaits authorization. Until then:
`CLEAN_SALEOR_RESERVE_REPLICATION_AWAITS_AHMED_AUTHORIZATION`.
`IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED` holds regardless.

---

**Efficiency:** paid $0.019985 (missing units $0.019927 + queries $0.000058);
1,998,521 new tokens; hard $0.25 ceiling respected; no fallback provider; no
model substitution; no Sparse re-call; Saleor RESERVE untouched.

**Git:** corrected-reexecution tag `stage5-corrected-reexecution-2026-09-20`;
historical preregistration + invalid-evaluation tags preserved.