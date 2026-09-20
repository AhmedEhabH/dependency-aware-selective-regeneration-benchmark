# SALEOR RESERVE 300 - RM-CSS FINAL REPLICATION (2026-09-20)

**Mission:** FINAL CLEAN RM-CSS REPLICATION + PRE-REGISTERED
CROSS-REPOSITORY TRANSFER TEST
**Verdicts:** PRIMARY `SALEOR_RESERVE_300_RMCSS_PASS`; SECONDARY
`SECONDARY_CROSS_REPO_TRANSFER_PASS`
`IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED`
**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731 (remainder;
pre-unsealing partly GLM-5.3-Flash — see `docs/EXECUTION_AGENT_PROVENANCE_2026-09-20.md`)
**Tier:** T3
**Companion documents:** `docs/SALEOR_RESERVE_300_RMCSS_IMPACT_DECLARATION_2026-09-20.md`,
`reports/SALEOR_RESERVE_300_RMCSS_PREREGISTRATION_2026-09-20.md`,
`reports/saleor_reserve_300_rmcss_preregistration.json`,
`reports/saleor_reserve_300_parity_gate.json`,
`reports/saleor_reserve_300_parity_gate_audit.json`,
`reports/saleor_reserve_300_rmcss_result.json`,
`reports/saleor_reserve_300_rmcss_secondary_metrics.json`,
`reports/saleor_reserve_300_rmcss_result_audit.json`, `DECISIONS.md` P88/P89/P90

---

## WHY SIP AND RM-CSS ARE DIFFERENT

- **SIP — Sparse Impact Plan** is the Sparse baseline: the frozen Sparse write
  set produced by the frozen Sparse (qwen3-coder) strategy.
- **RM-CSS — Repository-Memory Calibrated Set Selection** = SIP + Qwen dense
  ranking (qwen/qwen3-embedding-8b, realization A) + parent-only Repository
  Memory (structural top-10 + episodic top-10) + a calibrated ADD/KEEP/DROP
  set-selection (11-feature L2-LR, threshold 0.20). It decides, per candidate,
  whether to keep/drop SIP files and which non-SIP candidates to add.

## WHY THE OLD "V2" NAME WAS AMBIGUOUS

"V2" was used for different things across reports (e.g., a verification
instrument, then the calibrated policy, then the corrected re-execution). The
thesis-facing terminology is now fixed in `docs/GLOSSARY.md`: SIP and RM-CSS.
Historical code identifiers/commits/tags/artifact paths are NOT renamed.

## WHY 300 TASKS WERE CHOSEN

Ahmed authorized exactly 300 Saleor RESERVE tasks — the only remaining
untouched population in the current split (1,086 RESERVE total). 300 preserves
statistical power for the preregistered 10,000-resample task-paired bootstrap
while leaving 786 RESERVE tasks untouched after this mission. A pre-unsealing
cost-ceiling amendment (P89, $1.50 -> $1.75) preserved n=300 rather than
altering it.

## WHAT WAS FROZEN BEFORE UNSEALING

- Sample: 300/1,086 RESERVE, seed 20260920, manifest SHA-256 `445b5e9d…`;
  label-free preflight 300/300, 0 exclusions; temporal wording B
  (same/overlapping-period disjoint-commit; 2020-05-20 -> 2026-08-05).
- PRIMARY model: frozen corrected RM-CSS deployment artifact
  (config_sha256 `8925d29a…`, threshold 0.20, realization A, 11 features).
- SECONDARY model: `DJANGO_ONLY_RMCSS_TRANSFER_MODEL` (djangoCMS DEV only, 174
  tasks, threshold 0.20, artifact SHA-256 `efb38c07…`).
- SIP protocol (exact frozen prompt; transport retry max 3 byte-identical;
  schema-invalid/truncated/completed-empty/parse-invalid -> fail-closed EMPTY).
- Qwen embedding-coverage rule (CASE A/B/C, no finite sentinels, |score|>10 ->
  RAISE). Cost ceiling $1.75 (amended). Parity gate 10 checks + independent
  audit. PRIMARY/SECONDARY endpoints + bootstrap (10,000, seed 20260920).
- Preregistration SHA-256 `3bedb7d6…` (after P89 amendment), committed
  `04abef5` + amendment `8d9a6a2`, tagged
  `saleor-reserve-300-rmcss-preregistered-2026-09-20` +
  `saleor-reserve-300-rmcss-preregistration-cost-amendment-2026-09-20`.

## LABEL-FREE PARITY

`reports/saleor_reserve_300_parity_gate.json` **10/10 PASS** + independent
audit **11/11 PASS** (agree): 0 unresolved embedding misses (226,895
blobs-with-units); 0 finite sentinels; NaN rate 7.93% vs Saleor DEV 8.35%
(within ±3pp); finite dense range [0.072, 0.805] within [-1.5, +1.5]; all 9
continuous feature means within 3 Saleor DEV SD; candidate rows/task 34.84 vs
DEV 34.83 (within ±25%); exact 11-feature schema; primary + transfer hashes
exact; sample manifest hash exact.

## PRIMARY RM-CSS RESULT

| | SIP | RM-CSS | Delta |
|---|---|---|---|
| TP / FP / FN | 193 / 344 / 728 | 283 / 382 / 638 | +90 / +38 / −90 |
| Precision | 0.3594 | 0.4256 | +0.0662 |
| Recall | 0.2096 | 0.3073 | +0.0977 |
| FNR | 0.7904 | 0.6927 | −0.0977 |
| F1 | 0.2647 | 0.3569 | **+0.0921** |

**Delta F1 = +0.0921, 95% CI [+0.0691, +0.1156]** (excludes zero, positive).
Paired CIs: Delta P [+0.0259, +0.1034]; Delta R [+0.0752, +0.1207]; Delta FNR
[−0.1208, −0.0753]. **Verdict: `SALEOR_RESERVE_300_RMCSS_PASS`.**

## CROSS-REPOSITORY TRANSFER RESULT

| | SIP | django-only RM-CSS | Delta |
|---|---|---|---|
| TP / FP / FN | 193 / 344 / 728 | 262 / 363 / 659 | +69 / +19 / −69 |
| Precision | 0.3594 | 0.4192 | +0.0598 |
| Recall | 0.2096 | 0.2845 | +0.0749 |
| FNR | 0.7904 | 0.7155 | −0.0749 |
| F1 | 0.2647 | 0.3389 | **+0.0742** |

**Delta F1_transfer = +0.0742, 95% CI [+0.0535, +0.0957]** (excludes zero).
**Verdict: `SECONDARY_CROSS_REPO_TRANSFER_PASS`** (a policy trained ONLY on
djangoCMS DEVELOPMENT labels produced a positive file-set F1 improvement over
SIP on the untouched Saleor sample). SECONDARY and non-gating.

## PRECISION / RECALL / F1 / FNR

See the two tables above (pooled over 300 tasks; task-paired bootstrap CI95).

## RANKING METRICS

| Population (300) | Acc@1 | Acc@3 | Acc@5 | Hit@1 | Hit@3 | Hit@5 | Recall@1/3/5 |
|---|---|---|---|---|---|---|---|
| RM-CSS ranking | 0.4833 | 0.2867 | 0.3067 | 0.4833 | 0.7067 | 0.7700 | 0.2333/0.4238/0.5162 |
| |G|=1 slice (89 tasks) | 0.3933 (Hit@1) | 0.5843 (Hit@3) | 0.6629 (Hit@5) | | | | |

Descriptive only; NOT a primary endpoint; NOT compared to external
SWE-bench/LocAgent headlines.

## ERROR DECOMPOSITION (PRIMARY RM-CSS)

SIP TP retained 175; SIP TP dropped 18; SIP FP dropped 150; SIP FP retained
194; omitted positives added 108; new FP added 188. Remaining FN:
not-generated (outside candidate universe) and generated-but-rejected are the
dominant residual loss. Descriptive only.

## TEMPORAL CHARACTERIZATION

Sample target commits 2020-05-20 -> 2026-08-05 (median 2023-07-20),
overlapping Saleor DEV (2020-06-30 -> 2026-08-10) -> wording **B**,
same/overlapping-period disjoint-commit replication (NOT temporal
generalization). Target-file count per task: mean 3.07 / median 2 (range
1-12). Commit-message words: mean 23.1 / median 12. SIP empty 72/300; RM-CSS
empty 29/300. Candidate set mean 34.84; RM-CSS selected set mean 2.22; SIP
selected set mean 1.79.

## EFFICIENCY / COST

- SIP: 300 calls, 5,094,731 tokens (5.00M prompt + 0.09M completion),
  **$1.59349**, ~49 min wall; categories 228 succeeded / 70 completed-empty / 2
  transport-failed (HTTP 429 after 3 byte-identical retries -> fail-closed
  EMPTY); 7 transport retries total.
- Qwen embeddings: 2,076 missing units (est 2.59M tokens, $0.025909) + 299
  unique queries (12,558 tokens, $0.000126); **$0.026035**; P86-corrected
  coverage (0 sentinels).
- Repository Memory: cached index on D:; ~0.57 s/task (172 s for 300).
- RM-CSS classifier: ~5 s (in-memory L2-LR over 10,452 candidate rows).
- **Total incremental cost: $1.619525 < $1.75 amended ceiling.**
- Peak RAM ~2 GB (dev embedding matrix). Cache growth on E: (reserve-300
  embedding cache + blob/unit texts) — reproducible, archivable at closure.

## WHAT THE RESULT PROVES

- **Frozen RM-CSS replicated a positive affected-file-set F1 improvement over
  SIP on a preregistered untouched Saleor RESERVE sample** (Delta F1 +0.0921,
  CI [+0.0691, +0.1156]).
- **The same RM-CSS learning recipe, trained using djangoCMS DEVELOPMENT labels
  only, also improved F1 over SIP on the untouched Saleor sample** (Delta F1
  +0.0742, CI [+0.0535, +0.0957]).

## WHAT IT DOES NOT PROVE

- It does NOT claim untouched djangoCMS confirmation (none remains in the
  current split; the 139 Stage-5 tasks are exposed).
- It does NOT claim all-repository / language-independent generalization,
  universal superiority, state-of-the-art, or direct superiority over
  LocAgent/RepoMem.
- It does NOT prove temporal generalization (the sample overlaps the DEV
  period).

## WHY METHOD SEARCH IS NOW CLOSED

`IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED` is permanent for this thesis. No
new localization method will be designed/tuned. This mission evaluated the
frozen method; it did not search for a new one. `IMPACT_LOCALIZATION_EVIDENCE_
COLLECTION_CLOSED` is NOT recorded.

## NEXT THESIS PHASE

`END_TO_END_SELECTIVE_REGENERATION` (Functional Correctness, Preservation,
Architecture Compliance, Efficiency) using the now-frozen impact-localization
evidence. Prepared as a handoff, NOT executed in this mission. Remaining
untouched Saleor RESERVE: **786 tasks**.

---

**Storage-cleanup note:** reproducible caches that may later be
archived/moved: `E:\opencode\qwen3-embed-cache-*` (regenerable from corpus +
model), `E:\opencode\stage5-corrected-2026-09-20` and
`E:\opencode\saleor-reserve-300-2026-09-20` (blob/unit texts, regenerable from
git), `D:\opencode_cache\memory_rescue_v2` (commit index, regenerable from git).
The cache families are kept separate and were NOT moved/merged/deleted during
the active experiment.

**Git:** preregistration tag
`saleor-reserve-300-rmcss-preregistered-2026-09-20` (peel `04abef5`), amendment
tag `saleor-reserve-300-rmcss-preregistration-cost-amendment-2026-09-20` (peel
`8d9a6a2`), final result tag
`saleor-reserve-300-rmcss-final-replication-2026-09-20`.