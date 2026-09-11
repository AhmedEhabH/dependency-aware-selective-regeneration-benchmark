# Qwen3-Coder-30B-A3B-Instruct Paper Integration Note

**Date:** 2026-09-11
**Study:** `scientific-stagec-djangocms-qwen3-coder-30b-a3b-crossmodel-01`
**Classification:** POST-HOC CROSS-MODEL / CROSS-PROVIDER ROBUSTNESS REPLICATION

## 1. What was run

- Same repositories, cases, treatments and gateway as the frozen
  Qwen3-Coder-480B-A35B-Instruct djangoCMS studies; **the model AND the
  provider changed**:
  - model: `qwen/qwen3-coder` (Qwen3-Coder-480B-A35B-Instruct) →
    `qwen/qwen3-coder-30b-a3b-instruct` (Qwen3-Coder-30B-A3B-Instruct);
  - provider: DeepInfra (`deepinfra/turbo`) → SiliconFlow (`siliconflow/fp8`;
    Novita failed the capability contract — rejects `response_format=json_schema`).
- Reasoning: the new model is **model-native non-thinking**; NO reasoning
  control parameter is sent (avoids the Qwen3-32B reasoning-control confound).
- 60 cells: 6 scenarios × 2 arms (`impact_plan` v1, `impact_plan_v2`) × 5 reps.

## 2. Headline results (descriptive)

- v1: 17/30 valid, 13 failed, **11 truncations**; v2: **28/30 valid, 2 failed,
  0 truncations**.
- v2 pooled P 0.5556 / R 0.6881 / F1 0.6148 / FNR 0.3119; full-recall 10/28.
- 60 requests issued, 59 responses, 59 usage-known / 1 usage-unknown
  (one transport failure). Recorded 301,146 total tokens and $0.041518 live
  cost are **lower bounds**.
- **DIRECTIONALLY REPLICATED** (descriptive): v2 validity 0.933 > v1 0.567 and
  v2 truncation 0.000 < v1 0.367.

## 3. Allowed claims

- "The sparse v2 representation remained the most operational for a second
  coder model (28/30 valid, 0 truncations at the frozen 4096 cap)."
- "Directionally replicated (descriptive): v2 validity rate (93%) exceeded v1
  (57%) and v2 truncation rate (0%) was below v1 (37%)."
- "Cross-model Sparse-v2 agreement (descriptive): 135 cross-product Jaccard
  pairs vs historical Qwen3-Coder-480B-A35B-Instruct; mean 0.491, median
  0.429; per-file frequencies in
  `reports/QWEN3_CODER_30B_A3B_CROSSMODEL_AGREEMENT.{md,csv}`."
- "S006 remains the weak case for the new coder model (over-selection +
  persistent gold misses) — qualitatively consistent with the historical
  model; descriptive only."

## 4. Forbidden claims

- **No** model-superiority / inferiority claim between Qwen3-Coder-30B-A3B-Instruct
  and Qwen3-Coder-480B-A35B-Instruct.
- **No** "independent confirmation" or "confirmatory replication" framing —
  this is post-hoc on the same six cases with a different provider.
- **No** significance / equivalence / statistical test.
- **No** pooling with the Qwen3-32B study or the historical study.

## 5. Provider confound (state explicitly)

The historical model was served via DeepInfra; the new coder model was served
via SiliconFlow. **Model and provider are confounded** — any comparison is a
cross-model / cross-provider descriptive observation, not a clean model-only
contrast.

## 6. Accounting (state explicitly)

- Lower-bound semantics apply: the single transport-failure cell
  (`stgc30b-djangocms-external-validity-007-impact_plan_v2-r3`) issued a
  request with unknown billed usage; its usage/cost are NOT silently zeroed.
- A recorded-field wiring artifact (`request_dispatched` snapshot) is
  documented in `ACCOUNTING_CORRECTION_NOTE.md`; the authoritative accounting
  is derived from immutable raw evidence and asserted by the zero-API
  verifier.

## 7. Remaining limitations

- Same six author-curated djangoCMS cases; no real-commit or cross-project
  evidence (see `reports/REAL_COMMIT_BENCHMARK_PLAN.md`).
- Provider confound (above).
- Selection-only; downstream regeneration correctness unevaluated.
- S006 remains the weak case for all three studies.