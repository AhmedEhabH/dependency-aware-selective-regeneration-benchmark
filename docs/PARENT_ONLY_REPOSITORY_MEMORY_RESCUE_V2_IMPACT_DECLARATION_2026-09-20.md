# PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2 — T3 Impact Declaration + Frozen Configuration (2026-09-20)

**Status:** FROZEN BEFORE IMPLEMENTATION. This document records the exact
history-memory channels, candidate-universe rule, feature set, model
configuration, cross-validation procedure, threshold procedure, success gate,
and expected file list for the PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2 mission
BEFORE any outer-OOF outcome is inspected.

**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731
**Mission:** PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2
(HISTORY-AUGMENTED DEEP FALSE-NEGATIVE RECOVERY)
**Tier:** T3 (new evaluation strategy / signal family)
**API budget:** ZERO paid API calls. No embedding runs. No model downloads.
No web/API enrichment during V2.
**Sealed data:** NOT opened. Development populations only (djangoCMS DEV 174,
Saleor DEV 149). Stage 5 stays PAUSED and SEALED.

---

## 0. Preserved frozen scientific history (NOT rewritten)

- `INDEPENDENT_DENSE_RETRIEVAL_REPLICATED` — preserved exactly.
- `CALIBRATED_SET_SELECTION_V1_FAIL` — preserved exactly as a frozen negative.
  V1 is NOT rewritten as a success.
- Current V1 result (unchanged): djangoCMS Sparse P 0.4464 / R 0.2465 /
  F1 0.3177 / FNR 0.7535 → V1 P 0.4230 / R 0.2761 / F1 0.3341 / FNR 0.7239;
  Delta F1 +0.0165, 95% CI [-0.0190, +0.0525], FAIL (CI crosses zero).
  Saleor Sparse P 0.3390 / R 0.2115 / F1 0.2605 / FNR 0.7885 → V1 P 0.3603 /
  R 0.3141 / F1 0.3356 / FNR 0.6859; Delta F1 +0.0751, CI [+0.0416, +0.1083],
  PASS. Realization B reproduced the SAME scientific verdict.
- Stage 5 remains PAUSED and SEALED (`FINAL_POLICY_NOT_FROZEN`).

---

## 1. Full-Universe V2 CANCELLED before execution (mission §2)

The mission explicitly cancels `CALIBRATED_SET_SELECTION_V2_FULL_UNIVERSE`.
Instead of fitting a new model over the full repository universe, the V1
non-Sparse selection was verified from already-exposed V1 artifacts (no new
model fit):

- V1 selected non-Sparse additions ONLY at dense ranks 1-4, exactly:
  rank1 172, rank2 93, rank3 20, rank4 3, ranks 5-20 = 0.
- Non-Sparse candidate pool ranks 5-20: n = 4981 rows, 0 selected.
- Max outer-OOF predicted probability among non-Sparse candidates:
  ranks 5-20 max 0.1880 (p95 0.0886); ranks 15-20 max 0.0650 (p95 0.0428).
- All five V1 inner-CV learned thresholds were 0.17-0.21 (fold dependent) —
  strictly ABOVE every non-Sparse rank-5+ probability. The top-20 boundary was
  therefore NEVER ACTIVE at the decision boundary.
- Empirical proxy-positive rate by non-Sparse dense-rank band: r1 0.2562,
  r2 0.1660, r3 0.1254, r4 0.0519, r5-10 0.0616, r11-15 0.0447,
  r16-20 0.0261, r>20 0.0193.

**Governance decision recorded:**

`FULL_UNIVERSE_V2_CANCELLED_AS_NON_BINDING_ABLATION`

The top-20 boundary was not empirically active at the decision boundary
(the learned thresholds 0.17-0.21 exceed every non-Sparse rank-5+ probability,
max 0.188; the tail bands 15-20 cap at 0.065). Removing it while preserving
the same rank-monotone signal would be expected to produce a near-null rerun
and creates unnecessary forking-path risk. This is a descriptive decision
based on already-exposed DEV/V1 artifacts, NOT a new scientific experiment.

---

## 2. Deep dense miss definition (mission §3)

`DEEP_DENSE_MISS` = a historical-proxy positive file that:

1. remains a FALSE NEGATIVE after V1 (not in the V1 final selected set); AND
2. was OUTSIDE the V1 frozen candidate universe (`Sparse UNION dense-top20`).

Verified counts from artifacts (realization A): djangoCMS **199**, Saleor **177**.
Verified dense-rank distribution of V1 deep misses: djangoCMS median rank 62
(mean 75.6, p25 37, p75 100.5); Saleor median rank 70 (mean 130.1, p25 42,
p75 163). The current bottleneck is DEEP FALSE-NEGATIVE RECOVERY: affected
files remain far below the useful dense-score decision region.

---

## 3. Dependency-cluster diagnostic (mission §4) — descriptive only

Before implementing memory, a DESCRIPTIVE oracle-style dependency-cluster
diagnostic is reproduced over DEEP_DENSE_MISS files using ONLY parent-visible
public dependency graphs (the frozen `dependency_graph.json` per case):

- A. how many have a direct dependency/import relation to ANOTHER proxy-positive
  file from the same historical target change;
- B. how many are directly adjacent (1 hop) to a V1-selected TRUE POSITIVE;
- C. how many are within 2 dependency hops of a V1-selected TRUE POSITIVE.

**This uses evaluation labels ONLY for retrospective headroom analysis.**
"Another proxy positive" and "V1 true positive" are NEVER inference-time seeds.
These are oracle-style diagnostics, NOT deployable features. NO graph features
are added to V2 (V2 isolates repository-history memory as the new orthogonal
signal).

---

## 4. History visibility — strict parent only (mission §7)

For each task with parent revision P:

- ALLOWED: commits that are provably ancestors of P (`git rev-list <P>`).
- FORBIDDEN: target commit; target diff; child revision; future commit;
  future issue/PR metadata; later branch state.
- The history construction FAILS CLOSED if temporal visibility cannot be
  proven (any required commit whose ancestry is unprovable aborts the task).

Leakage tests (automated) assert: every memory entry's commit is an ancestor
of P; the target commit and all descendants are never present; no target
patch paths / proxy labels enter the memory or any feature.

### 4.1 Repositories (deterministic local git caches, ZERO network)

| Repo | Path | Type | Anchor note |
|---|---|---|---|
| djangoCMS | `dist/real-commit-cache/djangocms` | full (not shallow) | HEAD `ba0007f15…`; all 174 DEV parents are ancestors of HEAD (verified) |
| Saleor | `dist/pilot-repo-cache/saleor` | full (not shallow) | HEAD `2c48391b…` == dataset anchor; all 149 DEV parents are ancestors of HEAD (verified) |

### 4.2 Production-file history filtering (mission §8)

A commit is a **production-changing commit** iff it modifies at least one file
in the task's legal production universe (the frozen `candidate_universe.json`
paths for that task). Commits that modify ONLY files excluded by the
benchmark's production-file policy are excluded. This is applied per task
against that task's frozen production universe.

---

## 5. History window (mission §8) — ALL, no tuning

Use ALL available parent-visible production-changing history before P.
NO last-N tuning, NO time windows, NO recency weighting, NO 1yr-vs-2yr choice,
NO 500-vs-2000-commit choice. V2 freezes cumulative repository memory.

---

## 6. Memory Channel A — structural co-change (mission §9)

Deterministic historical co-change statistics over parent-visible
production-changing commits. For production files f and s:

- `C(f)` = number of parent-visible production-changing commits touching f.
- `C(s)` = number touching s.
- `C(f,s)` = number touching both.
- `Jaccard(f,s) = C(f,s) / (C(f) + C(s) - C(f,s))`.
- If `C(f,s) < 2` then pair score = 0.

Freeze support threshold = 2. Do NOT sweep it.

---

## 7. Inference-time structural memory seeds (mission §10)

Use ONLY inference-available seeds:

- A. ALL Sparse-selected files (`in_sparse == True`).
- B. the Qwen dense rank-1 file (minimum `dense_rank` in the task universe).

Do NOT seed from target labels. For candidate f:

- `cochange_sparse(f) = max Jaccard(f, s) over s in Sparse`; 0 if Sparse empty.
- `cochange_top1(f) = Jaccard(f, dense-rank1-file)`.
- `cochange_memory_score(f) = max(cochange_sparse(f), cochange_top1(f))`.

---

## 8. Memory Channel B — episodic change memory (mission §11)

Deterministic non-parametric memory of prior repository changes. For each
parent-visible production-changing commit create a document from:

- REQUIRED: commit subject; commit body.
- OPTIONAL: linked issue/PR title/body ONLY IF already available locally,
  parent-visible timestamp provable, no external retrieval, and no
  target/future information can enter. **No web/API enrichment during V2.**
  (No local linked-issue corpus is available; the V2 documents are therefore
  commit subject + body only.)

---

## 9. Historical episode retrieval (mission §12)

Deterministic BM25 over HISTORICAL CHANGE TEXT (NOT source-code BM25).
Corpus = historical commit/change descriptions. Query = the exact frozen
parent-visible task intent already used by the benchmark
(`intent.json` → `RecallTask.intent_text`).

Retrieve top 10 historical episodes. Freeze `EPISODIC_TOP_CHANGES = 10`.
No K sweep.

---

## 10. Episodic file signal (mission §13)

For file f:

- `episode_similarity(f)` = maximum normalized BM25 score among the retrieved
  top-10 historical episodes that modified f; 0 if no retrieved episode
  touched f. Normalization = raw BM25 score divided by the maximum raw BM25
  score within the retrieved top-10 list (deterministic).
- `episode_hit_count(f)` = number of retrieved top-10 historical episodes
  touching f — computed for DESCRIPTIVE purposes ONLY; NOT a V2 model feature.

---

## 11. File history frequency (mission §14)

- `history_change_count(f)` = number of parent-visible production-changing
  historical commits touching f.
- Feature: `log_history_change_count(f) = log1p(history_change_count(f))`.
- No recency weighting.

---

## 12. Memory candidate generation (mission §15)

- Structural candidates: top 10 NON-SPARSE files by
  `cochange_memory_score > 0`.
- Episodic candidates: top 10 NON-SPARSE files by `episode_similarity > 0`.
- Freeze `COCHANGE_TOP_FILES = 10`, `EPISODIC_TOP_FILES = 10`.
- Tie-break deterministically: (1) higher score; (2) higher historical support
  where relevant; (3) normalized path ascending.
- Memory candidate set = union(structural candidates, episodic candidates).
- No K tuning.

---

## 13. Final V2 candidate universe (mission §16)

Candidate universe per task:

1. ALL Sparse files; UNION
2. Qwen dense top-20 NON-SPARSE files; UNION
3. the frozen memory candidate set.

Do NOT use the full repository universe for classification. Purpose: test
whether an ORTHOGONAL history generator makes deep dense misses reachable.

---

## 14. V2 feature set (mission §19) — exactly 11

Reuse all V1 features exactly:

1. `dense_file_score`
2. `log_rank` = log1p(absolute dense_rank)
3. `gap_to_top1`
4. `in_sparse`
5. `log_sparse_set_size`
6. `sparse_empty`
7. `sparse_rank_interaction` = in_sparse * log_rank

Add EXACTLY:

8. `cochange_sparse`
9. `cochange_top1`
10. `log_history_change_count`
11. `episode_similarity`

FORBIDDEN: repository ID, graph features, code BM25, path features, file
extension, target labels, LLM-generated features, recency features, issue
categories, `episode_hit_count`.

---

## 15. Model / CV / threshold — EXACTLY V1 (mission §20)

- L2 Logistic Regression: `penalty="l2"`, `C=1.0`, `solver="liblinear"`,
  `max_iter=1000`, `random_state=0`.
- StandardScaler on the continuous features fit on TRAINING rows only;
  boolean features unscaled.
- Reuse EXACT V1 outer fold assignments (the frozen
  `fold_assignments_A.json`; deterministic recomputation from case IDs with
  seed 20260920 — identical by construction).
- Reuse EXACT V1 inner fold procedure (5-fold task-grouped repo-stratified
  inner OOF within outer-train; seed 20260920).
- Inner threshold: `argmax pooled micro-F1` over grid 0.01..0.99 step 0.01;
  tie-break HIGHER threshold.
- No class-weight search, no model search, no threshold-rule change.

---

## 16. Primary score realization (mission §21)

Qwen realization A = primary dense scores. After V2 is completely frozen and
evaluated on A, repeat the exact V2 pipeline with Qwen realization B.
Do NOT average A+B. Do NOT redesign V2 based on B.

---

## 17. Primary baseline (mission §22)

Primary baseline: **Sparse**. Also reported descriptively (NOT retuned):
V1; Qwen fixed B=5; Qwen diagnostic B=1; SweRank B=5; SweRank diagnostic B=1.

---

## 18. Metrics — always report formulas (mission §23)

```
TP, FP, FN
P = TP / (TP + FP)
R = TP / (TP + FN)
FNR = FN / (TP + FN) = 1 - R
F1 = 2TP / (2TP + FP + FN)
Delta_metric = Metric_V2 - Metric_Sparse
```
Task-paired bootstrap: >= 10,000 resamples, fixed seed 20260920 (same seed as
V1 for paired comparability), task unit; CI95 = [Q2.5, Q97.5].

---

## 19. Primary success gate — UNCHANGED from V1 (mission §24)

Required on BOTH repositories:
- A. Final micro-F1 > Sparse.
- B. paired-bootstrap 95% CI lower bound for Delta F1 > 0.
- C. Recall >= Sparse.
- D. FNR <= Sparse.
- E. >= 3/5 outer folds with Delta F1 >= 0.
- F. zero target leakage.
- G. deterministic local rerun identical.

Precision always reported with: point estimate, Delta Precision, 95% CI.
NO post-hoc Precision margin. `PARETO_SUCCESS` reported descriptively.

---

## 20. Error decomposition (mission §25)

Per repository report: Sparse TP retained / Sparse TP dropped / Sparse FP
dropped / Sparse FP retained. Omitted positives added from: dense-only
candidate, structural-memory candidate, episodic-memory candidate, candidate
generated by multiple channels. New FP added from the same channel categories.
Remaining FN classified: A. not generated by dense or memory candidates;
B. candidate generated but policy rejected; C. Sparse TP dropped.

---

## 21. Intent-information stratification — descriptive only (mission §26)

Pre-registered BEFORE V2 result inspection (intent-length buckets):
- <= 6 whitespace-separated words
- 7 to 15 words
- > 15 words.

For Sparse, V1, V2 report per repository and bucket: n tasks, P, R, F1, FNR.
Also report memory DeepFNRecovery per bucket. Intent length is NOT a V2
feature, NOT a gate, NOT used to choose thresholds/memory settings/candidate
generation. Descriptive hypothesis-generating analysis only. No causal /
information-theoretic-impossibility claims.

---

## 22. Channel ablations — descriptive only (mission §31)

PRIMARY V2 = dense + structural history + episodic history. After primary V2
is frozen and evaluated, report DESCRIPTIVELY: remove structural channel;
remove episodic channel. Do NOT use ablations to redefine V2 or to select the
better channel post hoc. Mechanism understanding only.

---

## 23. Realization-B robustness (mission §32)

After the complete V2 design is frozen: rerun the exact pipeline with Qwen
realization B dense scores. Report: P/R/F1/FNR A-vs-B; selected-set exact
agreement; task-level Jaccard; PASS/FAIL agreement. If the verdict changes:
`PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_ROBUSTNESS_INCONCLUSIVE`.

---

## 24. Scientific decision (mission §33)

- V2 passes the unchanged gate on BOTH repositories AND realization B
  preserves the verdict → `PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_PASS`.
  Interpretation: parent-visible repository history adds orthogonal
  localization signal and supports a stronger final affected-file policy.
- Otherwise → `PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL` and STOP.
- No automatic V3. Do NOT open Stage 5. Do NOT claim repository-memory
  novelty, perfect localization, clean unseen generalization, or
  intent-information impossibility.

---

## 25. Expensive / irreversible guard (mission §34)

Do NOT: open sealed datasets; execute Stage 5; run paid APIs; download
another embedding model; run LocAgent; clone cross-language repositories;
switch thesis scope to provenance-by-construction. If any becomes necessary:
STOP and ask Ahmed first.

---

## 26. Storage / efficiency discipline (mission §30, §35)

- Report separately: history extraction/build wall time, history index size,
  co-change index size, BM25 memory size, per-task memory retrieval latency,
  classifier latency, peak RAM if practical, disk usage, API calls, API cost.
- Keep large caches outside Git/export. History/co-change/BM25 caches go to
  `D:\opencode_cache\memory_rescue_v2\` (outside the repo; excluded from the
  TRUE LIGHT export).
- TRUE LIGHT export <= 50 MB.

---

## 27. Frozen sealed-data guard (mission §36, §37)

- The primary analyzer reads ONLY: (1) the label-free Qwen full-file-score
  Parquet artifacts; (2) `load_dev_tasks()` (DEV 174 + 149 only); (3) local
  git history caches. A runtime guard asserts the case set is exactly the 323
  DEV case IDs and that no sealed split (INTERNAL_TEST / RESERVE) case is
  present.
- Independent audit does NOT import the primary analyzer.

---

## 28. Files expected from this mission

### A. Implementation

| File | Purpose |
|---|---|
| `src/benchmark/memory_rescue/__init__.py` | package marker |
| `src/benchmark/memory_rescue/history.py` | parent-only git history extraction: global per-repo commit index (sha, subject, body, changed paths), per-task ancestor filtering, production-file filtering, C(f)/C(f,s)/history_change_count; FAIL-CLOSED ancestry checks |
| `src/benchmark/memory_rescue/cochange.py` | Channel A: Jaccard, support>=2 freeze, structural seeds, cochange_sparse / cochange_top1 / cochange_memory_score, structural top-K |
| `src/benchmark/memory_rescue/episodic.py` | Channel B: historical change-text corpus, deterministic BM25, top-K episode retrieval, episode_similarity / episode_hit_count |
| `src/benchmark/memory_rescue/candidates.py` | memory candidate generation (structural ∪ episodic), V2 candidate universe, V2 feature builder (11 features) |
| `src/benchmark/memory_rescue/analysis.py` | nested 5x5 task-grouped CV driver for V2 (reuses `benchmark.calibrated.policy`), metrics, bootstrap, gate, error decomposition, channel attribution, intent stratification |
| `scripts/memory_rescue_v2_history.py` | one-time history/co-change/episodic index build + per-task memory computation (cached on D:) |
| `scripts/memory_rescue_v2_run.py` | primary V2 analyzer (realization A primary; `--realization B` robustness) |
| `scripts/memory_rescue_v2_diagnostics.py` | deep-FN counts, dependency-cluster diagnostic, deep-FN coverage report, popularity/random baselines, channel ablations, intent stratification |
| `scripts/memory_rescue_v2_audit.py` | INDEPENDENT audit (does NOT import the primary analyzer) |
| `tests/unit/test_memory_rescue_history.py` | parent-only visibility, no-future/target leakage, temporal ancestry, production-file filtering |
| `tests/unit/test_memory_rescue_cochange.py` | co-change counts, Jaccard formula, support>=2 |
| `tests/unit/test_memory_rescue_episodic.py` | historical commit-text indexing, BM25 determinism, top-K retrieval |
| `tests/unit/test_memory_rescue_v2.py` | structural top10, episodic top10, candidate-union construction, V1 fold reuse, V1 LR reuse, V1 threshold reuse, metrics, task-paired bootstrap, intent bucket assignment (NOT a feature), realization-B robustness, sealed-data guard |

### B. Evidence / reports

| File | Purpose |
|---|---|
| `reports/PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_REPORT_2026-09-20.md` | human-readable report (all required sections) |
| `reports/PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_DIAGNOSTICS_2026-09-20.md` | verified V1 rank-selection diagnostic, deep-FN distribution, dependency-cluster diagnostic, deep-FN coverage, baselines |
| `reports/PROVENANCE_BY_CONSTRUCTION_DIRECTION_NOTE_2026-09-20.md` | supervisor-facing strategic note (mission §28) |
| `reports/memory_rescue_v2_freeze.json` | machine-readable frozen config (frozen BEFORE OOF) |
| `research/memory-rescue-v2/` | machine-readable outputs |
| `research/literature/*` | literature ledger update: repository-memory prior art + selective-prediction note |

### C. Governance / documentation updates

| File | Purpose |
|---|---|
| `DECISIONS.md` | append P80 (governance amendment + this frozen config + cancellation) and P81 (execution outcome) |
| `00_CURRENT_RESEARCH_STATE.md` | scientific truth update |
| `PROGRESS.md` | execution truth update |
| `docs/RESEARCH_JOURNEY.md` | chronological row |
| `reports/CURRENT_ORACLE_GAP_EXPLAINED_2026-09-20.md` | add the V2 update (preserve prior content) |
| `reports/CURRENT_NUMBERS_CHEATSHEET_2026-09-19.md` | add V2 numbers (preserve prior content) or dated successor |
| `reports/GAP_REDUCTION_ROADMAP.md` | add the V2 stage/addendum |
| `reports/EXPERIMENT_AND_IDEA_LEDGER.md` | E-014 V2 row |
| `reports/LITERATURE_DECISION_LEDGER.md` | repository-memory prior-art + selective-prediction entries |

---

## 29. Verification plan (mission §37)

- Independent audit does NOT import the primary analyzer.
- Unit tests cover: strict parent-only history visibility; no future/target
  commit leakage; temporal ancestry; production-file history filtering;
  co-change counts; Jaccard formula; support >= 2; Sparse-empty behavior;
  dense-rank1 seed behavior; historical commit-text indexing; BM25
  determinism; structural top10; episodic top10; candidate-union construction;
  V1 fold reuse; V1 LR reuse; V1 threshold procedure reuse; metrics;
  task-paired bootstrap; intent bucket assignment; intent bucket NOT used as
  feature; realization-B robustness; sealed-data guard.
- Run: targeted pytest; ruff; py_compile; `git diff --check`; affected suites.