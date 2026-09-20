# SALEOR RESERVE 300 RM-CSS PREREGISTRATION (2026-09-20)

**Mission:** FINAL CLEAN RM-CSS REPLICATION + PRE-REGISTERED
CROSS-REPOSITORY TRANSFER TEST
**Frozen BEFORE any Saleor RESERVE target outcome is opened.**
**Companion JSON:** `reports/saleor_reserve_300_rmcss_preregistration.json`
**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731
**Tier:** T3

---

## 1. Primary purpose

Does the frozen current method **RM-CSS** improve exact affected-file-set F1
over **SIP** on a new untouched Saleor sample? The method-search phase is
CLOSED; `IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED` is permanent.

## 2. Terminology

- **SIP — Sparse Impact Plan** (the Sparse baseline; old thesis-facing names:
  Sparse-v2 / sparse impact plan).
- **RM-CSS — Repository-Memory Calibrated Set Selection** = SIP + Qwen dense
  ranking + parent-only Repository Memory + calibrated ADD/KEEP/DROP set
  selection (old thesis-facing name: V2).
- Thesis-facing/report terminology only; historical code identifiers, commits,
  tags and artifact paths are NOT renamed. See `docs/GLOSSARY.md`.

## 3. Population (EXACT; no replacement)

- Saleor RESERVE universe: **1,086 tasks**.
- Sample: **exactly 300 task IDs**, without replacement, seed **20260920**,
  `numpy.random.default_rng(20260920)`, lexicographically sorted universe and
  output.
- Sample manifest SHA-256 (`saleor_reserve_300_sample.txt`, newline-delimited):
  **`445b5e9d0aeeab9551e8feeb3e59e6b5bcfee793f029810a6efe0cbc8f126447`**.
- Preflight: 300/300 label-free infrastructure OK; **0 exclusions**.
- Do NOT open target labels while sampling; do NOT replacement-sample later.

## 4. Temporal descriptor

Target-commit date ranges (commit metadata only; no label disclosure):

| population | earliest | latest | median |
|---|---|---:|---:|
| sample 300 | 2020-05-20 | 2026-08-05 | 2023-07-20 |
| Saleor DEV | 2020-06-30 | 2026-08-10 | 2022-12-13 |
| corrected Saleor INTERNAL_TEST | 2020-07-27 | 2026-07-29 | 2023-04-28 |

**Freeze wording B: `same/overlapping-period disjoint-commit Saleor
replication`.** NOT temporal generalization (periods overlap).

## 5. Primary RM-CSS model (IMMUTABLE)

Frozen corrected deployment artifact
`research/stage5-v2-final/deployment_artifact.json`:
- file SHA-256 `7e9f82bc…`; config_sha256 `8925d29a…`; threshold **0.20**;
  realization **A**; 11 features; L2-LR C=1.0 liblinear max_iter=1000 seed 0;
  StandardScaler on 9 continuous features; parent-only Repository Memory;
  structural top-10; episodic top-10; dense top-20; no-unit/NaN behavior;
  corrected embedding-coverage behavior. NOT refit.

## 6. Secondary cross-repository model (§7)

`DJANGO_ONLY_RMCSS_TRANSFER_MODEL`
(`research/saleor-reserve-300-rmcss/django_only_rmcss_transfer_model.json`):
- file SHA-256 `7e5a46a9…`; artifact SHA-256 `efb38c07…`; **threshold 0.20**
  (5-fold task-grouped OOF on djangoCMS DEV, grid 0.01..0.99, argmax micro-F1,
  tie-break higher); trained on djangoCMS DEVELOPMENT tasks ONLY (174 tasks;
  NO Saleor labels); EXACT RM-CSS recipe.
- SECONDARY preregistered test; does NOT gate the primary result.

## 7. SIP execution rule (§13)

Baseline = SIP (exact frozen SIP prompt/protocol).
- TRANSPORT errors: retry with BYTE-IDENTICAL request, max 3 retries. Only
  transport failures may be retried.
- Fail-closed EMPTY SIP sets: schema-invalid; truncated; completed empty;
  unrecoverable parse-invalid. For such tasks SIP = empty set and RM-CSS
  executes with `sparse_empty = 1`.
- Report exact counts: success / transport retry / schema-invalid / truncated /
  parse-invalid / completed-empty. No manual repairs.

## 8. Cost guard (§14)

Live prices verified before paid execution. Hard total incremental ceiling
**$1.50**. If projected > $1.50: STOP before paid calls. No alternate provider,
no fallback model, no model substitution.

## 9. Embedding-coverage rule (MANDATORY, §15)

For every sampled Saleor parent-state blob: CASE A cached -> reuse; CASE B not
cached but embeddable units -> embed with `qwen/qwen3-embedding-8b` @ DeepInfra
realization A (frozen splitter + MAX-cosine aggregation); CASE C no embeddable
units -> dense score NaN. NEVER use finite missing sentinels (-1e9/-1e6/any).
Hard guard: any finite |dense_file_score| > 10 reaching the feature builder ->
RAISE and STOP.

## 10. Label-free parity gate (§16-17)

All candidate generation and features completed BEFORE loading hidden target
labels. `reports/saleor_reserve_300_parity_gate.json` must PASS all 10 checks:
(1) unresolved cache misses = 0; (2) finite missing-sentinel count = 0;
(3) NaN/no-unit rate within ±3pp of Saleor DEV (~8.35%); (4) finite dense
scores within [-1.5, +1.5]; (5) continuous feature means within 3 Saleor DEV
SD; (6) candidate rows/task within ±25% of Saleor DEV; (7) exact 11-feature
names/order; (8) primary hashes exact; (9) secondary hashes exact;
(10) sample manifest hash exact. Independent parity audit must agree; on
disagreement or any FAIL: STOP (no label reads, no rule loosening).

## 11. Irreversible checkpoint (§18)

Print `SALEOR_RESERVE_300_IRREVERSIBLE_CHECKPOINT` (timestamp, preregistration
tag, sample hash, primary model hash, secondary model hash, thresholds, actual
pre-label task count, API spend so far) before label access.

## 12. Outcome evaluation (§20-29)

Open target outcomes ONCE; no configuration change after this point.
- PRIMARY endpoint: frozen all-DEV RM-CSS vs SIP; TP/FP/FN -> P/R/F1/FNR;
  DeltaF1 = F1_RMCSS − F1_SIP; task-paired bootstrap 10,000 resamples seed
  20260920; CI95 [Q2.5, Q97.5].
- PRIMARY success rule: `SALEOR_RESERVE_300_RMCSS_PASS` iff point > 0 AND CI
  lower > 0; `_INCONCLUSIVE` iff point > 0 but CI crosses/includes 0; `_FAIL`
  iff point <= 0. Do NOT change this rule.
- SECONDARY: `DJANGO_ONLY_RMCSS_TRANSFER_MODEL` vs SIP on the same sample;
  DeltaF1_transfer; same bootstrap; labels `SECONDARY_CROSS_REPO_TRANSFER_PASS
  / _INCONCLUSIVE / _FAIL`. SECONDARY; does NOT gate PRIMARY.
- Required secondary metrics (§24), ranking compatibility Acc@K/Hit@K/Recall@K
  (§25, descriptive), temporal/task characterization (§26, descriptive), error
  decomposition (§27, descriptive), efficiency (§28).
- Independent result audit (§29): MUST NOT import the primary result analyzer;
  recompute all quantities; on disagreement STOP.

## 13. Claim boundaries (§30)

Allowed if PRIMARY PASS: "Frozen RM-CSS replicated a positive
affected-file-set F1 improvement over SIP on a preregistered untouched Saleor
RESERVE sample." If transfer also PASS: "The same RM-CSS learning recipe,
trained using djangoCMS DEVELOPMENT labels only, also improved F1 over SIP on
the untouched Saleor sample." Forbidden: untouched djangoCMS confirmation;
all-repository generalization; universal superiority; SOTA; direct superiority
over LocAgent/RepoMem.

## 14. Governance / closure (§31-33)

`IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED` regardless of outcome. Future
work freeze list in §32. Next thesis phase handoff:
`END_TO_END_SELECTIVE_REGENERATION` (prepared, NOT executed).

## 15. Validation (§36)

Targeted pytest (sampling determinism, exclusion tests, cache coverage, NaN
behavior, sentinel guard, feature schema, primary/transfer model hashes,
bootstrap, metrics, independent audit) + ruff + py_compile + git diff --check.

## 16. Cost / irreversible guard summary

- Hard incremental ceiling: **$1.50**.
- Prohibited: opening more than the preregistered 300 Saleor RESERVE tasks;
  modifying RM-CSS after unsealing; new localization method; V3; feature/threshold
  changes; Energy-Based/adaptive-k/negative-association-rule/JEPA redesigns;
  provenance-by-construction; issue re-mining; new embedding models;
  LocAgent/Agentless runs.

---

# AMENDMENT — P89 PRE-UNSEALING COST-CEILING AMENDMENT (2026-09-20)

- **Authorized by:** Ahmed.
- **Old ceiling:** $1.50. **New ceiling:** **$1.75** (ONLY the hard incremental
  cost ceiling changed).
- **Exact label-free projection:** SIP $1.612393 + missing embeddings $0.038390
  + queries $0.000126 = **$1.650909** (evidence:
  `research/saleor-reserve-300-rmcss/saleor_reserve_300_cost_projection.json`).
- **Reason:** preserve the preregistered n=300 sample (statistical power) rather
  than alter it; $1.75 provides a small execution cushion.
- **Zero paid calls before this amendment; zero outcomes opened before this
  amendment.**
- **Explicitly UNCHANGED:** sample size 300; sample IDs; sample seed 20260920;
  SIP baseline; primary RM-CSS; django-only transfer model; feature set;
  thresholds; Qwen realization A; candidate constants; primary endpoint;
  secondary endpoint; bootstrap; success criteria; exclusion rules; parity gate.
- **Preregistration SHA256 updated to:** `3bedb7d6ccd4cb738d539e6808eb4776fb313743ab4291140ceba9f3b9c8c982`.
- **Amendment tag:** `saleor-reserve-300-rmcss-preregistration-cost-amendment-2026-09-20`
  (original preregistration tag `saleor-reserve-300-rmcss-preregistered-2026-09-20` NOT moved).