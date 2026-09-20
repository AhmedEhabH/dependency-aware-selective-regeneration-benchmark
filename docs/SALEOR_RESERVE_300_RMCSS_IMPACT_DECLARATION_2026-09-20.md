# SALEOR_RESERVE_300_RMCSS - T3 Impact Declaration + Frozen Configuration (2026-09-20)

**Status:** RECORDED APPEND-ONLY BEFORE any implementation / any Saleor RESERVE
target-outcome access. This is the final planned IMPACT-LOCALIZATION evaluation
for the current MSc method-development program.

**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731
**Tier:** T3
**Mission:** SALEOR RESERVE 300 — FINAL CLEAN RM-CSS REPLICATION +
PRE-REGISTERED CROSS-REPOSITORY TRANSFER TEST
**Approved by:** Ahmed (mission prompt authorization) — ONE clean untouched
evaluation on a preregistered sample of exactly 300 Saleor RESERVE tasks.

---

## 0. Primary purpose

The localization METHOD SEARCH is CLOSED. The questions are now:

- PRIMARY: Does the frozen current method **RM-CSS** improve exact
  affected-file-set F1 over **SIP** on a new untouched Saleor sample?
- SECONDARY: Can the EXACT SAME RM-CSS learning recipe trained ONLY on
  djangoCMS DEV transfer, without Saleor training labels, to the same untouched
  Saleor sample?

Regardless of outcome: `IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED` remains
permanent for this thesis.

## 1. Terminology freeze (thesis-facing, report-facing only)

- **SIP — Sparse Impact Plan** replaces OLD "V2"/"Sparse-v2"/"sparse impact
  plan". This is the Sparse baseline (the frozen Sparse write set).
- **RM-CSS — Repository-Memory Calibrated Set Selection** replaces CURRENT
  "V2" (the frozen calibrated ADD/KEEP/DROP set-selection policy built on
  SIP + Qwen dense ranking + parent-only Repository Memory).

RM-CSS = SIP + Qwen dense ranking + parent-only Repository Memory + calibrated
ADD/KEEP/DROP set selection.

Do NOT rename historical code identifiers, commits, tags, or artifact paths.
Only thesis-facing/report/glossary terminology changes. Add this mapping to the
project glossary and current research state. Avoid ambiguous bare wording such
as "V2 beats V2".

## 2. Preserved historical results (NOT rewritten)

All preserved exactly: all SIP/Sparse historical experiments; SweRank findings;
Qwen independent dense replication; calibrated-set-selection V1 FAIL;
Repository-Memory development results; Issue-Grounded result; invalid first
Stage-5 execution; P86 execution-invalid correction; corrected Stage-5
re-execution; all prior tags and reports.

The invalid Stage-5 FAIL remains historical only. The scientifically relevant
corrected result remains labelled `STAGE5_CORRECTED_REEXECUTION_POSITIVE` with
the explicit limitation that the 139-task population was already exposed by the
invalid run. It is NOT untouched confirmation.

## 3. Current corrected evidence (to be verified from artifacts, §3)

- djangoCMS: SIP F1 ≈ 0.3028; RM-CSS F1 ≈ 0.3256; Delta F1 ≈ +0.0228.
- Saleor: SIP F1 ≈ 0.2744; RM-CSS F1 ≈ 0.3524; Delta F1 ≈ +0.0780.
- Pooled: SIP F1 ≈ 0.2857; RM-CSS F1 ≈ 0.3419; Delta F1 ≈ +0.0562; CI95 ≈
  [+0.0185, +0.0945].

These numbers motivate replication. They are NOT the untouched evidence for
this mission.

## 4. Frozen primary model (IMMUTABLE; §6)

The PRIMARY model is the already-frozen corrected RM-CSS deployment artifact
(`research/stage5-v2-final/deployment_artifact.json`). Do NOT refit it.
Freeze/verify exactly:

- 11 features; feature order; scaler; Logistic Regression; C=1.0; solver
  liblinear; max_iter 1000; seed 0; threshold 0.20; Qwen realization A;
  parent-only Repository Memory; structural top-10; episodic top-10; dense
  top-20; candidate construction; no-unit/NaN behavior; corrected
  embedding-coverage behavior.

Expected config_sha256 `8925d29a8e065bc864cd16e755ac0e896c7675b4a12f68fb66c35e5bd644ea95`.

## 5. Secondary cross-repository model (§7)

BEFORE any Saleor RESERVE target outcome is opened, fit ONE secondary model
using djangoCMS DEVELOPMENT tasks ONLY, with the EXACT RM-CSS recipe (L2-LR
C=1.0 liblinear max_iter=1000 random_state=0; same 11 features; same
StandardScaler semantics; threshold = 5-fold task-grouped OOF on djangoCMS DEV
ONLY, grid 0.01..0.99 step 0.01, argmax micro-F1, tie-break higher; expected
threshold 0.20 — do NOT force it if recomputation differs). Persist:
coefficients, intercept, scaler, threshold, feature schema, training-task IDs,
folds, configuration, SHA256 hashes. Name:
`DJANGO_ONLY_RMCSS_TRANSFER_MODEL`. It is a SECONDARY preregistered test; it
does NOT gate the primary result.

## 6. Population and sampling (§8-10)

- Saleor RESERVE universe: 1,086 tasks (frozen split manifest
  `split_freeze_saleor.json`).
- Sample exactly 300 task IDs without replacement, seed 20260920,
  `numpy.random.default_rng(20260920)`, lexicographically sorted universe and
  output; persist selected IDs + SHA256 of newline-delimited IDs.
- Do NOT open target labels while sampling.
- Label-free eligibility: a sampled task may be excluded ONLY if the evaluation
  bundle cannot be constructed because of a label-free infrastructure condition
  (parent/intent/universe/repo state unavailable). No replacement sampling.
  Primary n = all successfully preflighted tasks among the original 300.
- Temporal descriptor: record target-commit dates (metadata only, no label
  disclosure); freeze wording as A (later-period) or B (same/overlapping-period
  disjoint-commit) Saleor replication.

## 7. SIP execution rule (§13)

Baseline = SIP (Sparse Impact Plan), exact frozen SIP prompt/protocol.
TRANSPORT errors may be retried with BYTE-IDENTICAL request, max 3 retries.
Only transport failures may be retried. Schema-invalid / truncated / completed
empty / unrecoverable parse-invalid responses are fail-closed EMPTY SIP sets
(sparse_empty=1). Report exact category counts. No manual repairs.

## 8. Cost guard (§14)

Verify live prices before paid execution. Estimate 300 SIP calls + missing Qwen
corpus embeddings + Qwen query embeddings. Hard total incremental ceiling
**$1.50**. If projected > $1.50: STOP before paid calls. No alternate provider,
no fallback model, no model substitution.

## 9. Embedding-coverage fix is MANDATORY (§15)

For every sampled Saleor parent-state blob: CASE A cached -> reuse; CASE B not
cached but embeddable units -> embed missing units with
`qwen/qwen3-embedding-8b` @ DeepInfra realization A (frozen unit splitter,
MAX-cosine aggregation); CASE C no embeddable units -> dense score NaN under
frozen corrected semantics. NEVER use finite missing sentinels (-1e9/-1e6/any).
Hard guard: if any finite |dense_file_score| > 10 reaches the feature builder:
RAISE and STOP.

## 10. Label-free parity gate (§16-17)

Complete all candidate generation and features BEFORE loading hidden target
labels. Create `reports/saleor_reserve_300_parity_gate.json`. Required checks:
(1) unresolved cache misses = 0; (2) finite missing-sentinel count = 0;
(3) no-unit/NaN rate within ±3pp of frozen Saleor DEV rate (~8.35%);
(4) finite dense scores within [-1.5, +1.5]; (5) each continuous feature mean
within 3 Saleor DEV SD; (6) candidate rows/task within ±25% of Saleor DEV;
(7) exact 11-feature names/order; (8) primary model/scaler/threshold hashes
exact; (9) secondary django-only model/scaler/threshold hashes exact;
(10) sample manifest hash exact. If ANY item fails: STOP. An independent parity
auditor (NOT importing the primary evaluator) must recompute all quantities and
agree; otherwise STOP.

## 11. Irreversible checkpoint (§18)

After preregistration + parity PASS and BEFORE label access print
`SALEOR_RESERVE_300_IRREVERSIBLE_CHECKPOINT` with timestamp, preregistration
tag, sample hash, primary model hash, secondary transfer-model hash,
threshold(s), actual pre-label task count, API spend so far.

## 12. Outcome evaluation (§20-29)

Open target outcomes ONCE. No configuration may change after this point.

- PRIMARY: frozen all-DEV RM-CSS vs SIP. Aggregate TP/FP/FN -> P/R/F1/FNR;
  DeltaF1 = F1_RMCSS - F1_SIP; task-paired bootstrap 10,000 resamples seed
  20260920; CI95 [Q2.5, Q97.5].
- PRIMARY success rule (§21): `SALEOR_RESERVE_300_RMCSS_PASS` iff DeltaF1 point
  > 0 AND CI lower > 0; INCONCLUSIVE if DeltaF1 > 0 but CI crosses/includes 0;
  FAIL if DeltaF1 <= 0. Do NOT change this rule.
- SECONDARY (§22-23): apply `DJANGO_ONLY_RMCSS_TRANSFER_MODEL` to the SAME
  Saleor sample; DeltaF1_transfer = F1_django_only - F1_SIP; same bootstrap.
  Labels: PASS / INCONCLUSIVE / FAIL. SECONDARY; does NOT gate PRIMARY.
- Required secondary metrics (§24): P/R/F1/FNR + deltas vs SIP; paired CIs for
  Delta P/R/FNR/F1 (primary); set sizes (mean/median/empty), additions/drops.
- Ranking compatibility (§25): Acc@K/Hit@K/Recall@K (K=1,3,5), |G|=1 slice
  separately if sample permits; descriptive only.
- Temporal/task characterization (§26) and error decomposition (§27)
  descriptive only.
- Efficiency (§28): SIP calls/tokens/cost/latency; Qwen missing units/query
  tokens/embedding calls/cost; memory index/retrieval; RM-CSS classifier time;
  total incremental cost; wall time; peak RAM; cache growth; one-time vs
  per-change split.
- Independent result audit (§29): MUST NOT import the primary result analyzer;
  recompute sample IDs, exclusions, SIP failure categories, SIP/Primary/transfer
  confusion, P/R/F1/FNR, DeltaF1, bootstrap CI, verdicts, Acc@K, hashes,
  thresholds, sample hash. If disagrees: STOP.

## 13. Claim boundaries (§30)

Allowed if PRIMARY PASS: "Frozen RM-CSS replicated a positive affected-file-set
F1 improvement over SIP on a preregistered untouched Saleor RESERVE sample." If
transfer also PASS: "The same RM-CSS learning recipe, trained using djangoCMS
DEVELOPMENT labels only, also improved F1 over SIP on the untouched Saleor
sample." Do NOT claim untouched djangoCMS confirmation, all-repository
generalization, universal superiority, SOTA, or direct superiority over
LocAgent/RepoMem.

## 14. Method-selection closure (§31)

Regardless of result: `IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED`. Do NOT
record `IMPACT_LOCALIZATION_EVIDENCE_COLLECTION_CLOSED`. A future
evaluation-only test of the SAME frozen RM-CSS on a THIRD repository remains
scientifically allowable ONLY with Ahmed's explicit authorization, with no
method changes.

## 15. Future work freeze (§32)

Keep as Future Work / follow-up publication (NOT executed): Energy-Based
Change-Set Completion; adaptive-k; negative association rules; JEPA /
repository world models; temporal hypergraphs; provenance-by-construction;
improved issue archival reconstruction; LocBench matched evaluation;
additional dense models.

## 16. Next thesis phase (§33)

Regardless of PASS/FAIL/INCONCLUSIVE, prepare a handoff for
`END_TO_END_SELECTIVE_REGENERATION` (Functional Correctness, Preservation,
Architecture Compliance, Efficiency) using the now-frozen impact-localization
evidence. Do NOT execute the new phase in this mission.

## 17. NOT authorized (RED)

New localization method; V3; feature search; threshold tuning; Energy-Based
models; adaptive-k; negative association rule redesign; JEPA/world models;
provenance-by-construction; issue re-mining; new embedding models; LocAgent/
Agentless runs; opening more than the preregistered 300 Saleor RESERVE tasks;
opening Saleor RESERVE labels before the parity gate; modifying RM-CSS after
unsealing.

## 18. Evidence trail

- docs/GLOSSARY.md (terminology mapping)
- docs/SALEOR_RESERVE_300_RMCSS_IMPACT_DECLARATION_2026-09-20.md (this file)
- reports/SALEOR_RESERVE_300_RMCSS_PREREGISTRATION_2026-09-20.md + .json
- reports/saleor_reserve_300_parity_gate.json
- reports/SALEOR_RESERVE_300_RMCSS_FINAL_REPLICATION_2026-09-20.md
- research/saleor-reserve-300-rmcss/ (artifacts)
- decision P88 (governance) and P89 (outcome)