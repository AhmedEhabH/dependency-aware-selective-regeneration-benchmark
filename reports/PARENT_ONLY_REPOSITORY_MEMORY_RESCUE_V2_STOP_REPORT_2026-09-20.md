# Final Stop Report — PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2 (2026-09-20)

## 0. Execution identity

- Provider/model: openrouter/deepseek/deepseek-v4-flash-0731
- Branch: `main` (feature branch `research/parent-only-repository-memory-rescue-v2-2026-09-20` merged)
- HEAD: `ac0691198e443b7db58b5ddb4a645bbb78a1f48f` == `origin/main` (verified after push)
- Scientific tag: `parent-only-repository-memory-rescue-v2-2026-09-20` peels to merge `14f125a08d80b4ef113b4bc37d23a0fc960996b3` (post-tag docs commit `ac06911` is NOT the tag target — provenance invariant respected)
- Tree state: clean (`git status --porcelain` empty)
- Reason for stopping: COMPLETE (scientific decision is a frozen negative)

## 1. Why Full-Universe V2 was cancelled

`FULL_UNIVERSE_V2_CANCELLED_AS_NON_BINDING_ABLATION`. Verified from exposed
V1 artifacts (no new model fit): V1 selected non-Sparse additions ONLY at
dense ranks 1-4 (rank1 172, rank2 93, rank3 20, rank4 3, ranks 5-20 = 0;
n=4,981 pool rows, 0 selected). Max outer-OOF probability among non-Sparse
ranks 5-20 = 0.1880 (p95 0.0886); ranks 15-20 = **0.0650** (p95 0.0428). All
five V1 inner-CV thresholds (0.17-0.21) were strictly above every non-Sparse
rank-5+ probability → the top-20 boundary was NEVER active at the decision
boundary. Removing it while preserving the same rank-monotone signal would be
a near-null rerun with forking-path risk. Descriptive, NOT a new experiment.

## 2. Verified V1 rank-selection diagnostic

rank1: 172, rank2: 93, rank3: 20, rank4: 3, ranks 5-20: 0 (recomputed from
`research/calibrated-set-selection-v1/candidate_universe_A.parquet` +
`oof_probabilities_A.parquet`). Empirical proxy-positive rate by non-Sparse
band: r1 0.2562, r2 0.1660, r3 0.1254, r4 0.0519, r5-10 0.0616, r11-15
0.0447, r16-20 0.0261, r>20 0.0193. Expected max probability among non-Sparse
rank 15-20 ≈ 0.062 → verified 0.0650.

## 3. Verified deep-FN dense-rank distribution

DEEP_DENSE_MISS = V1 false-negative proxy positive outside Sparse ∪ dense-top-20.
djangoCMS 199 (median dense rank 62, mean 75.6); Saleor 177 (median 70, mean
130.1). Expected medians ≈ 62 / 70 → verified exactly.

## 4. Dependency-cluster diagnostic

Descriptive oracle-style (evaluation labels for retrospective headroom ONLY;
never inference seeds; NO graph features in V2):
- djangoCMS: A direct relation to another proxy positive 109/199 (0.548);
  B adjacent to V1 TP 25 (0.126); C within 2 hops 56 (0.281). Expected
  ≈109 / 25 / 55.
- Saleor: A 130/177 (0.735); B 49 (0.277); C 76 (0.429). Expected ≈130 / 49 / 74.

## 5. Exact parent-only history rule

For each task parent P: history = `git rev-list <P>` ancestors only (P
included); fail-closed if any ancestor is missing from the local index;
production-changing = touches ≥1 file in the task's legal production universe;
commits touching only excluded files never enter. Target commit, descendants,
future commits/issues/PRs forbidden by construction. Automated leakage tests +
independent audit re-assert counts. Repos: djangoCMS
`dist/real-commit-cache/djangocms`, Saleor `dist/pilot-repo-cache/saleor`
(all 323 parents verified ancestors of each repo's HEAD).

## 6. History size per repository

djangocms_commits.json 7.4 MB; saleor_commits.json 10.2 MB; memory_bundles.json
15.8 MB → 33.5 MB total on D: (outside Git/export). Production-changing commit
counts: all 323 tasks have ≥1; djangocms 169/174 tasks have structural
candidates, 172/174 episodic; saleor 147/149 structural, 149/149 episodic.

## 7. Structural-memory definition

C(f) / C(s) / C(f,s) over parent-visible production-changing commits;
`Jaccard(f,s) = C(f,s)/(C(f)+C(s)-C(f,s))`; pair score 0 if `C(f,s) < 2`
(support threshold frozen at 2, NOT swept). Seeds = all Sparse files + Qwen
dense rank-1 file (no target labels). `cochange_sparse(f)` = max Jaccard over
Sparse (0 if Sparse empty); `cochange_top1(f)` = Jaccard(f, rank1);
`cochange_memory_score(f)` = max of the two.

## 8. Episodic-memory definition

Each parent-visible production-changing commit becomes a document
(subject + body; NO web/API enrichment). Deterministic BM25 (reusing the
project's Okapi BM25) over this historical change-text corpus retrieves the
top-10 episodes for the frozen task intent (`EPISODIC_TOP_CHANGES = 10`, no K
sweep). `episode_similarity(f)` = max normalized BM25 among retrieved episodes
touching f (0 if none); `episode_hit_count(f)` descriptive only, NOT a feature.
`log_history_change_count(f)` = log1p(C(f)), no recency weighting.

## 9. Deep-FN count before V2

199 (djangoCMS) / 177 (Saleor); median dense rank 62 / 70. Remaining V2
"not-generated" FN: 156 / 129.

## 10. Structural DeepFNRecovery

djangoCMS 14 / 199 (0.070); Saleor 20 / 177 (0.113).

## 11. Episodic DeepFNRecovery

djangoCMS 23 / 199 (0.116); Saleor 24 / 177 (0.136). (both channels: 6 / 4.)

## 12. Union DeepFNRecovery

djangoCMS 43 / 199 (**0.216**); Saleor 48 / 177 (**0.271**).

## 13. Popularity/random comparison

Same budget (top-10 non-sparse): historical-popularity 41 (0.206) / 18
(0.102); seeded deterministic random (seed 20260920, 1,000 resamples) mean
11.1 (0.056, CI95 5-18) / 2.45 (0.014, CI95 0-6). Memory union (43/48) >
popularity on Saleor and >> random on both. NOT used to tune memory.

## 14. Sparse-empty recovery

djangoCMS 22/105 (0.210); Saleor 16/69 (0.232). V2 final policy empty-set
count falls 53→37 (djangoCMS) and 41→10 (Saleor).

## 15. Intent-length stratified Sparse/V1/V2 results (descriptive)

| Repo | bucket | n | Sparse F1 | V2 F1 | V2 R | V2 FNR |
|---|---:|---:|---:|---:|---:|---:|
| djangoCMS | <=6 | 70 | 0.2344 | 0.2094 | 0.1487 | 0.8513 |
| djangoCMS | 7-15 | 46 | 0.3162 | 0.3764 | 0.3592 | 0.6408 |
| djangoCMS | >15 | 58 | 0.4000 | 0.4324 | 0.4235 | 0.5765 |
| Saleor | <=6 | 37 | 0.1750 | 0.2755 | 0.2308 | 0.7692 |
| Saleor | 7-15 | 37 | 0.1842 | 0.2857 | 0.2970 | 0.7030 |
| Saleor | >15 | 75 | 0.3170 | 0.4016 | 0.4040 | 0.5960 |

Intent length is NOT a feature/gate; hypothesis-generating only.

## 16. djangoCMS Sparse/V1/V2 P/R/F1/FNR + CI (realization A)

| | Sparse | V1 | V2 | V2 Δ vs Sparse (95% CI) |
|---|---:|---:|---:|---:|
| TP/FP/FN | 125/155/382 | 140/191/367 | 152/222/355 | — |
| P | 0.4464 | 0.4230 | 0.4064 | −0.0400 [−0.0843, +0.0036] |
| R | 0.2465 | 0.2761 | 0.2998 | +0.0533 [+0.0148, +0.0884] |
| F1 | 0.3177 | 0.3341 | 0.3451 | +0.0274 [−0.0102, +0.0636] |
| FNR | 0.7535 | 0.7239 | 0.7002 | −0.0533 [−0.0886, −0.0156] |

Gate: A True, B **False** (CI crosses zero), C True, D True, E 3/5 → FAIL.

## 17. Saleor Sparse/V1/V2 P/R/F1/FNR + CI (realization A)

| | Sparse | V1 | V2 | V2 Δ vs Sparse (95% CI) |
|---|---:|---:|---:|---:|
| TP/FP/FN | 99/193/369 | 147/261/321 | 158/283/310 | — |
| P | 0.3390 | 0.3603 | 0.3583 | +0.0192 [−0.0348, +0.0657] |
| R | 0.2115 | 0.3141 | 0.3376 | +0.1261 [+0.0896, +0.1648] |
| F1 | 0.2605 | 0.3356 | 0.3476 | +0.0871 [+0.0515, +0.1229] |
| FNR | 0.7885 | 0.6859 | 0.6624 | −0.1261 [−0.1639, −0.0902] |

Gate: A-E True (5/5 folds) → PASS.

## 18. ADD/KEEP/DROP decomposition (realization A)

| Repo | TP retained | TP dropped | FP dropped | FP retained | added (dense/struct/epis/multi) | new FP |
|---|---:|---:|---:|---:|---:|---:|
| djangoCMS | 110 | 15 | 49 | 106 | 42 (0/8/6/28) | 116 |
| Saleor | 94 | 5 | 65 | 128 | 64 (4/20/12/28) | 155 |

Remaining FN: not-generated 156/129; rejected 184/176; Sparse-TP-dropped 15/5.

## 19. Dense-vs-history rescue attribution

On djangoCMS, ALL 42 added omitted positives came from history-involved
candidates (structural/episodic/multiple-memory); dense-only contributed 0.
On Saleor, 60/64 added positives came from history-involved candidates.
Memory candidates recovered 43/48 deep dense misses that the dense top-20
could not reach (dense-only additions to the added-positive pool were 0/4).

## 20. Realization-A/B robustness

Exact same selected set 99.07%; mean task Jaccard 0.9964 (median 1.0, min
0.5); djangoCMS F1 identical (0.3451); Saleor F1 0.3476 → 0.3495; verdict
agreement SAME (both `PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL`). No
`ROBUSTNESS_INCONCLUSIVE`.

## 21. Remaining Oracle gap

Candidate coverage error fell from 199/177 (V1) to 156/129 (V2) via the
memory candidate set; ADD decision error rose to 184/176; DROP decision error
15/5. The decision/acceptance layer over recovered candidates is now the
binding constraint (rejected 184/176). Updated in
`reports/CURRENT_ORACLE_GAP_EXPLAINED_2026-09-20.md`.

## 22. API calls / cost

**0 API calls / $0.00.** No embedding reruns, no model downloads, no web/API
enrichment, no sealed data opened, no Stage-5 execution.

## 23. CPU/RAM/disk efficiency

- History build: index load 2.6/1.7 s (first) / 0.06/0.16 s (cached); task
  build 52 s (174) / 73 s (149); total ≈ 183 s one-time.
- History index: 33.5 MB on D: (outside Git); repo artifacts
  `research/memory-rescue-v2/` ≈ 7 MB.
- Classifier: full nested CV ≈ 25-40 s/realization; determinism rerun
  identical (SHA 4e2c880…).
- Peak RAM: not instrumented (normal pandas/scikit workload).
- TRUE LIGHT export 39.8 MB; full STOP audit zip 101.4 MB (with .git).

## 24. PASS / FAIL

**`PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL`** (frozen negative; both
realizations A and B fail the SAME criterion — djangoCMS Delta-F1 CI crosses
zero). Saleor PASSES the gate. No `ROBUSTNESS_INCONCLUSIVE`.

## 25. Is the final-policy problem solved on DEV?

**NO.** Repository-history memory is an orthogonal, real, zero-API signal that
recovers deep dense misses at the CANDIDATE level (union 21.6%/27.1%; better
than popularity on Saleor, >> random), and V2 point F1 improves over Sparse
and V1 on both repos — but the unchanged final-set gate still fails on
djangoCMS. The final-set decision problem is NOT solved on DEV.

## 26. Is Stage 5 scientifically justified?

**NO.** `FINAL_POLICY_NOT_FROZEN`. The dense-mechanism replication removed the
non-replication blocker, but a frozen successful final-set policy does not
exist. Stage 5 stays PAUSED and SEALED (djangoCMS RESERVE 59, Saleor
INTERNAL_TEST 80, Saleor RESERVE 1086; spent djangoCMS INTERNAL_TEST
untouched). No Stage-5 preregistration packet is produced (verdict FAIL).

## 27. Provenance-by-construction note path/status

`reports/PROVENANCE_BY_CONSTRUCTION_DIRECTION_NOTE_2026-09-20.md` —
supervisor-facing strategic note ONLY; NOT implemented, NOT a scope change;
`SUPERVISOR_DISCUSSION_REQUIRED_BEFORE_EXECUTION`; scoped literature check
(traceability families) recorded in the literature ledger.

## 28. Expensive/irreversible actions avoided

Sealed datasets NOT opened; Stage 5 NOT executed; zero paid APIs; no embedding
model downloaded; LocAgent NOT run; no cross-language repositories cloned;
thesis scope NOT switched to provenance-by-construction.

## 29. One next action

A **V3 calibrated acceptance/decision layer specialized for recovered memory
candidates** (or `INTENT_ADAPTIVE_SELECTIVE_LOCALIZATION`) requires a NEW
mission + NEW frozen hypothesis + explicit authorization (no automatic V3).
Recommended immediate next step (mission-authorized): **STOP**. The final-set
decision layer, not candidate generation, is the now-identified binding
constraint on djangoCMS.

## 30. Git / tag / LIGHT export / SHA256

- Commits: `6c4a334` (feature) → merge `14f125a` → `ac06911` (export docs).
- Branch pushed: `research/parent-only-repository-memory-rescue-v2-2026-09-20`.
- Tag: `parent-only-repository-memory-rescue-v2-2026-09-20` (annotated) →
  peel `14f125a…` (scientific merge; post-tag docs commit is NOT the target).
- Verified: `HEAD == origin/main == ac06911…`; clean tree.
- TRUE LIGHT export: `project-LIGHT-2026-09-20-0521.zip` —
  39,829,885 bytes (39.8 MB ≤ 50 MB), SHA-256
  `7437137762d202271dbb952d97d08c19907865092be14713805d28a49c9d76e0`
  (git archive; exclusions per `reports/LIGHT_EXPORT_CONTRIBUTOR_REPORT_2026-09-19.md` §7).
- STOP audit ZIP (AGENTS.md rule, WITH .git): `project-2026-09-20-0516.zip` —
  101,444,752 bytes, SHA-256
  `af77824211f29fb1411adf1fd5b80b8442e97396c93399d81ffbc0e1cc3dc4d0`.
- Validation: independent audit 23/23 PASS (no analyzer import); new unit
  tests 36/36 PASS; V1 calibrated suite 18/18 PASS; ruff clean; py_compile
  clean; `git diff --check` clean.
- Sealed data NOT opened. DO NOT OPEN SEALED DATA.