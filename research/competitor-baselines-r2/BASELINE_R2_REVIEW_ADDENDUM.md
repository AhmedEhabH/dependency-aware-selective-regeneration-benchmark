# M17 Competitor Baselines R2 — Evidence Freeze Review Addendum

**Mission:** `M17_COMP_BASELINES_R2_EVIDENCE_FREEZE_AND_DISCLOSURE`
**Branch:** `parallel/competitor-baselines-2026-10-12`
**Base (pre-freeze HEAD):** `1661ec215ede6ae96e82735148db4febffb21580`
**Status:** ADDITIVE DISCLOSURE ONLY. This addendum does NOT modify any existing
scientific output, prediction, metric, protocol freeze, or receipt. It records
the precise terminology and claim boundaries that must be used when reporting or
quoting the frozen R2 evidence.

---

## Cost terminology

The correct phrase for this evidence package is:

> **ZERO NEW BENCHMARK-ARM API CALLS**

with:

- `benchmark_arm_new_llm_calls = 0`
- `benchmark_arm_new_embedding_calls = 0`
- `benchmark_arm_incremental_api_cost_usd = 0.00`

This statement is scoped to the benchmark arms. It does **NOT** claim that the
coding/orchestration environment itself used no external model/API. No claim
about orchestration-environment model usage is made or implied.

## Primary result boundary

Frozen MAIN_297 (micro F1, file-level evaluator):

- **RM-CSS F1 ≈ 0.3568**
- **AGENT F1 ≈ 0.3631**
- **SIP F1 ≈ 0.2652**

Therefore:

- **DO NOT write:** "RM-CSS beats the Agent."
- **DO NOT write:** "RM-CSS has the highest F1."

Correct claim boundary:

> RM-CSS is non-inferior to the preregistered budget-bounded repository Agent
> under the separately frozen non-inferiority protocol, while using
> substantially lower interaction resources.

The new B2 retrieval arms (BM25 / DENSE / CIA) strengthen RQ2 (cheap retrieval
baselines); they do **not** change or support any Agent-superiority claim.

## Fixed-k arms

`BM25@1` / `BM25@3` / `BM25@5` / `BM25@10` and
`DENSE@1` / `DENSE@3` / `DENSE@5` / `DENSE@10`
are **pre-specified variants** of a fixed-k parameter grid. Do **not** select
the post-outcome best observed k and present it as if it were the sole
preregistered comparator.

## Size-matched arms

`BM25_SIZE_MATCHED` and `DENSE_SIZE_MATCHED` are labeled
**`SIZE_MATCHED_CONTROL`** because `k_t = |RM-CSS output|` (the number of files
in the frozen RM-CSS prediction for task t). They never read gold, but they are
**conditioned on RM-CSS output size**; they are not independent unconstrained
comparators.

## Dense

The DENSE arms reuse the frozen `qwen/qwen3-embedding-8b` realization-A scores
(already-frozen internal signal, `research/saleor-reserve-300-rmcss/full_file_scores_saleor300.parquet`).
This is **frozen internal signal reuse**. Label: **`DENSE_ONLY_ABLATION`**.
Do **not** describe the DENSE arms as a fully independent modern external
system.

## BM25→CIA

The realistic-seed CIA arms are labeled:

- `BM25_TO_CIA_1HOP`
- `BM25_TO_CIA_2HOP`

This is a **seeded propagation baseline/adaptation** (seed = BM25 top-1 for the
same task). Do **not** imply exact equivalence to a particular published CIA
implementation unless separately proven.

## Gold seeded

`C_ORACLE_1HOP` and `C_ORACLE_2HOP` must be described as:

- **`GOLD_SEEDED_DIAGNOSTIC`**
- **`SEED_INFORMATION_UPPER_BOUND_ONLY`**

"Upper bound" refers **ONLY** to oracle seed-information availability. It is
**NOT** an upper bound on:

- F1;
- precision;
- recall;
- downstream success;
- overall method performance.

## Agentless

`AGENTLESS_STYLE_EXECUTION_ESTIMATE.md` is **planning evidence only**.
Agentless-style has **NOT** yet been executed on MAIN_297.

Current:

- prompt-size measurements are deterministic/offline;
- token count is approximate;
- exact qwen3-coder tokenizer count is **UNVERIFIED**;
- USD estimate is **not** an empirical benchmark result;
- wall-time estimate is **not** an empirical benchmark result.

Do **not** insert these estimate numbers into the empirical results table.

## RIPPLE

RIPPLE was **not** run. Gold-seeded RIPPLE would be oracle-seeded diagnostic
evidence, **not** a direct same-protocol comparator.

---

*End of additive review addendum. No existing artifact was modified.*