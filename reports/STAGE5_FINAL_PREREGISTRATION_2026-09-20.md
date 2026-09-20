# STAGE 5 V2 FINAL PREREGISTRATION (2026-09-20)

**Mission:** FINAL THESIS IMPACT-LOCALIZATION FREEZE + ONE-SHOT STAGE-5
CONFIRMATORY EVALUATION
**Frozen BEFORE Stage-5 outcome access.**
**Companion JSON:** `reports/stage5_final_preregistration.json`
(`preregistration_sha256 = a4f484a9c075b015df87dee2eaa7c885b18b120e3ab0511dc450c68dd6edf670`)
**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731

---

## 1. Population (EXACT; NO extension)

- djangoCMS RESERVE: **n = 59**
- Saleor INTERNAL_TEST: **n = 80**
- TOTAL: **n = 139**
- `SALEOR_RESERVE_POWER_EXTENSION = NO`. No other confirmatory task.

## 2. Final V2 policy (frozen exactly)

Candidate universe: Sparse ∪ Qwen dense top-20 NON-SPARSE ∪ parent-only
structural memory top-10 ∪ parent-only episodic memory top-10.
Features EXACTLY 11: dense_file_score, log_rank, gap_to_top1, in_sparse,
log_sparse_set_size, sparse_empty, sparse_rank_interaction, cochange_sparse,
cochange_top1, log_history_change_count, episode_similarity.
No new/deleted features; no graph feature; no class weighting; no issue text;
no adaptive K.

## 3. Final deployment model (DEV-only refit, frozen)

- L2 LogisticRegression, C=1.0, solver liblinear, max_iter 1000, random_state 0.
- StandardScaler on 9 continuous features (fit on all 323 DEV rows).
- Threshold selection: 5-fold task-grouped repository-stratified OOF over all
  323 DEV, argmax pooled micro-F1 on 0.01..0.99, tie-break HIGHER.
- **Threshold = 0.20**
- Coefficients (11): [0.449415, -0.398721, -0.291699, 0.062069, 0.079529,
  0.504251, 0.159188, 0.284543, 0.400004, -0.152204, 0.483655]; intercept
  -3.47414.
- config_sha256 = `8925d29a8e065bc864cd16e755ac0e896c7675b4a12f68fb66c35e5bd644ea95`.

## 4. Primary endpoint (EXACTLY ONE)

Repo-stratified pooled micro-F1 difference (V2 minus Sparse):
per bootstrap replicate sample 59 dc RESERVE and 80 saleor IT with replacement;
aggregate TP/FP/FN across both sampled strata for V2 and for Sparse; compute
F1_V2,b and F1_Sparse,b; DeltaF1_b = F1_V2,b - F1_Sparse,b.
10,000 resamples; seed 20260920; 95% CI = [Q2.5%, Q97.5%].

## 5. Success rule (frozen; not to be changed post-unseal)

- A: pooled stratified Delta F1 point > 0 AND 95% CI lower > 0.
- B: djangoCMS Stage-5 point Delta F1 > 0 AND Saleor Stage-5 point Delta F1 > 0.
Per-repo CIs are mandatory secondary, NOT gating.

## 6. Budget

- Hard incremental paid ceiling: **$1.00**.
- Only the frozen Qwen model required by V2 (`qwen/qwen3-embedding-8b` @
  DeepInfra; Sparse strategy `qwen/qwen3-coder` frozen route). Live price is
  verified before the first paid call.
- If projected Stage-5 cost > $1.00, STOP before paid calls and report.
- No fallback provider; no model substitution; no extra realization.

## 7. Stage-5 input / history semantics

EXACT parent-only Repository Memory semantics from V2. No target diff, no
changed-path labels, no future commit relative to the task parent, no
issue-grounded text, no target-aware feature. If the frozen V2 implementation
cannot be applied exactly: STOP.

## 8. Sealed-data guard

Stage 5 is opened ONLY after this preregistration is committed, pushed, and the
immutable tag `stage5-v2-final-preregistered-2026-09-20` exists remotely.
ONE shot only; no second chance; no post-outcome tuning.

## 9. Execution plan (frozen)

1. Build the 139 Stage-5 case bundles from the frozen git caches (deterministic,
   zero-API; public intent/universe/graph built exactly as DEV).
2. Generate the frozen Sparse write sets for the 139 Stage-5 tasks (Sparse
   strategy; the same pipeline that produced DEV `predicted_write_set`).
3. Compute Qwen dense scores for the Stage-5 candidate universes (realization-A
   method; new corpus/query embeddings ONLY if the persisted cache does not
   already cover these tasks).
4. Build parent-only Repository Memory for the 139 Stage-5 tasks.
5. Apply the frozen final V2 model + threshold (0.20) to obtain V2 final sets.
6. Evaluate the primary endpoint + secondaries + Acc@K/Hit@K/Recall@K.
7. Independent audit; final PASS/FAIL/MIXED label; evidence tag.

## 10. Result labels

- PASS: `STAGE5_V2_FINAL_CONFIRMATION_PASS`; `IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED`.
- FAIL: `STAGE5_V2_FINAL_CONFIRMATION_FAIL`; `IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED`.
- MIXED: `STAGE5_V2_FINAL_CONFIRMATION_MIXED`; `IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED`.

## 11. Validation accomplished before this freeze

- Metric-compatibility audit 7/7 PASS (Acc@1 0.4737, Acc@3 0.2508, Acc@5
  0.2663, Hit@5 0.7492; single-target n=80 Acc@5 0.600; P5-C reference).
- Final DEV refit independent audit 9/9 PASS.
- Pre-unsealing tests 10/10 PASS.
- ruff clean; py_compile clean; git diff --check clean.