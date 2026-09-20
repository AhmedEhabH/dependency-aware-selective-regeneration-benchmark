# STAGE5_V2_EXECUTION_INVALID_EMBEDDING_COVERAGE_DEFECT - T3 Impact Declaration (2026-09-20)

**Status:** RECORDED APPEND-ONLY BEFORE any implementation/code change, per the
mission governance-first requirement (mission §2). This document declares the
T3 impact of a diagnosed EXECUTION defect in the already-frozen Stage-5 V2
pipeline and the corrective scope. It does NOT reopen method selection.

**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731
**Mission:** STAGE-5 EXECUTION DEFECT - RECORD -> REPRODUCE -> FIX ->
LABEL-FREE PARITY GATE -> CORRECTED RE-EXECUTION
**Tier:** T3
**Related decision:** `P86 - STAGE5_V2_EXECUTION_INVALID_EMBEDDING_COVERAGE_DEFECT`

---

## 0. Hard scientific boundary (UNCHANGED)

- `IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED` — PRESERVED. Method shopping
  does NOT reopen.
- The previously recorded label `STAGE5_V2_FINAL_CONFIRMATION_FAIL` remains in
  history but is SCIENTIFICALLY SUPERSEDED by
  `STAGE5_V2_EXECUTION_INVALID_EMBEDDING_COVERAGE_DEFECT` for the Stage-5
  result, because the first Stage-5 evaluation did NOT execute the preregistered
  V2 dense-score pipeline correctly.
- The old negative Stage-5 numbers are NOT to be cited as evidence about V2
  generalization. The narrative "the DEV ladder failed to generalize" is NOT to
  be used unless a technically valid evaluation later supports it.
- Every historical artifact, tag, report and decision is PRESERVED verbatim.
  Nothing is deleted.

## 1. Defect diagnosis (to be independently verified from persisted artifacts)

The Stage-5 dense scorer (`scripts/stage5_v2_dense_scores.py`) reused the DEV
blob-text/unit cache. For a Stage-5 blob not present in that DEV cache it failed
to construct/embed the new code units and instead assigned:

```
dense_file_score = -1e9
```

(a finite sentinel). The frozen feature builder
(`src/benchmark/memory_rescue/candidates.py`) only invokes the missing/no-unit
imputation (`no_units_score` -> NaN -> min_finite - 1) on NON-finite values.
Because `-1e9` is finite:

- the NaN path never fired;
- StandardScaler received extreme values (~-1e9) and produced extreme
  standardized features;
- dense-file-score / gap features became extreme;
- LR probabilities collapsed to zero for the affected candidate rows.

This violates the frozen Stage-5 preregistration rule (execution plan step 3:
"new corpus/query embeddings ONLY if the persisted cache does not already cover
these tasks" — meaning when the cache does NOT cover them, new corpus
embeddings MUST be created) and the frozen DEV missing-unit rule (NaN, not a
finite sentinel).

## 2. Status of the first Stage-5 run

- The first Stage-5 run is **execution-invalid**.
- Its artifacts remain historical (preserved, not deleted).
- Its scientific FAIL label is **superseded** (not deleted).
- The 139 tasks (djangoCMS RESERVE 59 + Saleor INTERNAL_TEST 80) are
  considered **exposed** and therefore cannot be treated as untouched
  confirmatory evidence again.

## 3. Corrective scope (mission-authorized)

- FIX ONLY embedding coverage:
  - CASE A (cache hit): reuse the realization-A embedding exactly.
  - CASE B (cache miss but file has embeddable units): materialize/split the
    Stage-5 blob using the SAME frozen unit splitter
    (`benchmark.signal.code_units.extract_code_units`) and embed those missing
    units with `qwen/qwen3-embedding-8b` @ DeepInfra (fallback disabled), same
    realization-A aggregation procedure (`aggregate_file_score` MAX cosine).
  - CASE C (file truly has no embeddable unit): dense score MUST be NaN /
    missing according to the same frozen DEV semantics.
  - NEVER use a finite sentinel such as -1e9 / -1e6 / -999999 for no-unit or
    missing-embedding state.
- HARD PIPELINE GUARDS:
  - fail if `abs(dense_file_score) > 10` for any finite candidate dense score;
  - fail if a blob has embeddable units but no embedding result;
  - fail if a required cache lookup silently resolves to a finite sentinel;
  - fail if dense score generation produces values outside the scientifically
    expected range without an explicit documented reason.
  - NO silent fallback.
- COST GUARD: hard incremental ceiling **$0.25** for new embedding calls.
  Live price verified before the first paid call. If projected cost exceeds
  $0.25, STOP before paid calls. No provider fallback, no alternate model, no
  model substitution.

## 4. Explicitly NOT authorized (RED)

- a new localization method;
- a new V3;
- feature changes;
- model changes;
- threshold changes (threshold stays 0.20);
- candidate-budget changes;
- Qwen realization changes;
- endpoint changes;
- new tuning;
- new DEV fitting;
- Saleor RESERVE access;
- opening/reading Saleor RESERVE labels;
- re-generating Sparse outputs (the persisted Sparse write sets are reused
  exactly);
- LocBench execution;
- JEPA / energy-based model / adaptive-k.

The method-selection phase remains CLOSED.

## 5. Corrected re-execution population

- djangoCMS RESERVE: 59
- Saleor INTERNAL_TEST: 80
- TOTAL: 139 (the SAME previously exposed tasks)
- This rerun is **diagnostic/corrective**, NOT a new untouched confirmation.

## 6. Result label

The corrected result will NOT be labelled `STAGE5_V2_FINAL_CONFIRMATION_PASS`
even if the corrected numbers pass the old endpoint. It will use one of:
`STAGE5_CORRECTED_REEXECUTION_POSITIVE` / `_NEGATIVE` / `_MIXED`, because the
population is no longer untouched.

## 7. Frozen scientific inputs preserved EXACTLY (unchanged)

- Qwen model `qwen/qwen3-embedding-8b`; provider DeepInfra; realization A;
- unit splitter; file aggregation (MAX cosine); feature definitions; feature
  order; scaler; LR coefficients; LR intercept; threshold = 0.20;
- candidate constants (TOP_ADD_UNIVERSE 20, COCHANGE_TOP_FILES 10,
  EPISODIC_TOP_FILES 10);
- Sparse predictions (persisted write sets reused);
- parent-only history rules;
- endpoint (repo-stratified pooled Delta F1, 10,000 resamples, seed 20260920);
- bootstrap; seed.

## 8. Evidence trail

- `reports/STAGE5_EXECUTION_DEFECT_REPORT_2026-09-20.md` (defect diagnosis)
- `reports/stage5_execution_defect_reproduction.json` (independent
  reproduction)
- `reports/stage5_parity_gate.json` (label-free parity gate)
- `reports/STAGE5_CORRECTED_REEXECUTION_2026-09-20.md` (human-readable result)
- this declaration and decision P86.