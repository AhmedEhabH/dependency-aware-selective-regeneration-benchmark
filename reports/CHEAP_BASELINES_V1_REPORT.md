# CHEAP NON-LLM BASELINES v1 — FINAL REPORT (Protocol A)

**Protocol:** `cheap-nonllm-baselines-v1` (T3 — new evaluation strategy / baseline family)
**Date:** 2026-09-16 (first POST-ICCI experimental block; corrected final report)
**Model/AI:** openrouter/deepseek/deepseek-v4-flash-0731 (implementation only; **zero LLM calls in the experiment**)
**Branch:** `research/cheap-nonllm-baselines-v1` → merged into `main`
**Tag:** `cheap-baselines-v1-dev-2026-09-16` (audited DEVELOPMENT evidence, NOT confirmatory)
**Dataset:** `benchmark_data/real_commit_impact_v1` — **TRAIN 24 + VALIDATION 6 only**; HELD_OUT_TEST 10 permanently excluded from all decisions.
**Reference:** observed changed-production-Python proxy within U_t (evaluation-only).
**Evaluator:** frozen P1 binary evaluator (`p1_selection_metrics`, same as P1/P5).

---

## A. Executive verdict

- Zero-LLM baselines provide a **genuine but bounded** localization signal on
  development data (TRAIN+VALIDATION, n=30; VALIDATION n=6).
- **BM25@K is the strongest cheap baseline** in this development set, but it is
  **not** a final operating point and **not** a head-to-head LLM competitor.
- Random@K is a ≈0.01–0.07 F1 floor; Graph@K ≈ path_token@K; Hybrid@K ≈ BM25@K
  with no material improvement.
- **BM25 provides a meaningful zero-LLM localization signal on development
  data. Whether it matches or underperforms the LLM planners remains untested
  under a shared fresh confirmatory protocol.**
- The reported P1 Full/Sparse numbers appear **only** as clearly labeled
  directional context (they come from a different, permanently exposed
  HELD_OUT split and are NOT a head-to-head ranking against these baselines).
- Cheap baselines do **not** solve omission (pooled FNR ≈0.41–0.56 at K=10) —
  the exact hole the omission-risk pillar (thesis core) targets.
- All rules frozen before results; HELD_OUT_TEST never touched; ZERO API cost;
  sensitivity diagnostic on the 3 path-mention TRAIN cases preserves the
  material baseline ordering.

## B. Scientific question

Does an inexpensive, zero-LLM repository-localization baseline provide useful
file-selection value relative to (and as a reference point for) the LLM impact
planner line? This block establishes the cheapest defensible baseline family on
**development data only** and freezes its configuration. It is **development
evidence**, not confirmatory, and it does NOT claim any LLM-vs-BM25 ranking.

## C. Data used / data forbidden

**Used (development only):**
- TRAIN 24 cases + VALIDATION 6 cases (djangoCMS, real commits).
- Public per-case bundle: visible commit intent, candidate universe,
  dependency graph (parent-commit-derived).
- Parent-only file corpus materialized via `git archive <parent>`.

**Forbidden (never used):**
- HELD_OUT_TEST 10 (permanently exposed by P1/P5; tuning/selection FORBIDDEN).
- Hidden observed change-set proxy as a ranking input (evaluation-only).
- Target/future commit state.
- Semantic-gold labels / status tokens.

Frozen-corpus caveat (NOT a pipeline leak): 3 TRAIN cases carry a full-message
public intent that literally contains a changed path
(`djangocms-rc-2efae8e43bd6`, `djangocms-rc-ada585d3f358`,
`djangocms-rc-5ff38b521274`). The P1 LLM planner saw the identical full-message
intent, so baselines and planner share the same public input. This is a dataset
property, reported and sensitivity-checked (Section I), never hidden.

## D. Baselines

Five deterministic, zero-API baselines at K ∈ {1, 3, 5, 10}:

| ID | Baseline | Description | Inputs |
|---|---|---|---|
| B0 | Random@K | seeded deterministic shuffle (per-case seed = `20260915:case_id`) | candidate paths only |
| B1 | BM25@K | Okapi BM25 (in-repo impl) over parent-commit file content vs visible intent | parent-only file corpus + intent |
| B2 | Path/token@K | token-overlap between path/module/class/function token sets and intent tokens | candidate metadata + intent |
| B3 | Graph@K | frozen parent-only dependency graph; seed = intent-token ∩ candidate-token hits; rank by BFS distance then lexical overlap | graph edges + metadata + intent |
| B4 | Hybrid@K | frozen rule: 0.5·Nm(BM25) + 0.5·Ng(graph); seedless → pure BM25 | BM25 scores + graph distances |

**Frozen before validation:** seed rule (intent-token ∩ candidate-token, no
gold); hybrid alpha = 0.5; K grid; tie-break = (-score, path); BM25
k1=1.5/b=0.75; stopword set. No threshold/method/K selection used validation
results — all rules were fixed pre-run. If the seed rule yields an empty set,
Graph@K emits an empty ranking and documents the case (no invented signal).

## E. Six validation gates

| Gate | Name | Result |
|---|---|---|
| G1 | Dataset Validation (TRAIN 24 / VALIDATION 6 / HELD_OUT_TEST 10; universe hashes; proxy ⊆ universe) | PASS |
| G2 | Input/Query Validation (query = public intent; no hidden proxy; frozen path-mention caveat recorded) | PASS |
| G3 | Pipeline Smoke (B0–B4 × K bounded deterministic ranks on synthetic case) | PASS |
| G4 | Dry Run (2 real cases; 20 cells/case; zero API) | PASS |
| G5 | Integration (30 cases × 5 baselines × 4 K = 600 cells; manifest hash stable) | PASS |
| G6 | Metric Verification (synthetic TP=2/FP=1/FN=1 → P=R=2/3, F1=2/3, FNR=1/3) | PASS |
| — | Independent audit (persisted evidence only; no held-out case; zero LLM cost; sensitivity diagnostic) | PASS |

Gate JSON: `reports/cheap_baselines_v1_gates.json` (all_gates_passed=true,
audit_passed=true).

## F. VALIDATION results — primary development-decision table (6 tasks, micro)

This is the **primary development-decision table**: the 6-task VALIDATION
split is what a confirmatory protocol would select on. BM25 is shown in full;
all baselines are in `research/cheap-baselines-v1/aggregate_v1.json`.

**BM25 (VALIDATION, 6 tasks, micro):**

| K | P | R | F1 | FNR | TP | FP | FN |
|---|---|---|---|---|---|---|---|
| 1 | 0.1667 | 0.040 | 0.0645 | 0.960 | 1 | 5 | 24 |
| 3 | 0.3333 | 0.240 | 0.2791 | 0.760 | 6 | 12 | 19 |
| 5 | 0.2333 | 0.280 | 0.2545 | 0.720 | 7 | 23 | 18 |
| 10 | 0.2167 | 0.520 | 0.3059 | 0.480 | 13 | 47 | 12 |

Other baselines on VALIDATION (micro): random F1 0.000–0.073; path_token F1
0.065–0.259; graph F1 0.065–0.259 (≈ path_token at every K); hybrid F1
0.065–0.282.

**Operating-point interpretation (K is NOT a final config):**
- **BM25@3** is the **low-cardinality / precision-oriented operating point**
  (P 0.3333, R 0.240, F1 0.2791 on VALIDATION).
- **BM25@10** is the **recall/FNR-oriented operating point** and has the
  **highest validation F1 (0.3059) in the current 6-task validation set**
  (R 0.520, FNR 0.480).
- **K is NOT yet a confirmatory conclusion.** K=3 vs K=10 trade precision
  against recall; the choice is a policy decision, not a measured fact.
- **Treat K as an operating-point curve** unless/until the next frozen protocol
  defines a primary selection objective (e.g., minimize FNR at bounded FP, or
  maximize F1 at a fixed card).
- **Do not choose K from pooled TRAIN+VALIDATION** without explicitly
  justifying that choice (see H).

## G. TRAIN results (24 tasks, micro)

| Baseline | K | P | R | F1 | FNR |
|---|---|---|---|---|---|
| random | 3 | 0.000 | 0.000 | 0.000 | 1.000 |
| random | 10 | 0.004 | 0.021 | 0.007 | 0.979 |
| bm25 | 1 | 0.417 | 0.208 | 0.278 | 0.792 |
| bm25 | 3 | 0.236 | 0.354 | 0.283 | 0.646 |
| bm25 | 5 | 0.183 | 0.458 | 0.262 | 0.542 |
| bm25 | 10 | 0.125 | 0.625 | 0.208 | 0.375 |
| path_token | 3 | 0.153 | 0.229 | 0.183 | 0.771 |
| path_token | 10 | 0.092 | 0.458 | 0.153 | 0.542 |
| graph | 3 | 0.159 | 0.229 | 0.188 | 0.771 |
| graph | 10 | 0.091 | 0.438 | 0.151 | 0.563 |
| hybrid | 3 | 0.208 | 0.313 | 0.250 | 0.688 |
| hybrid | 10 | 0.121 | 0.604 | 0.201 | 0.396 |

TRAIN and VALIDATION are presented **separately** throughout; they are not
pooled to select K (see H).

## H. Pooled development results (30 tasks, micro)

| Baseline | K | P | R | F1 | FNR |
|---|---|---|---|---|---|
| random | 3 | 0.011 | 0.014 | 0.012 | 0.986 |
| random | 10 | 0.013 | 0.055 | 0.021 | 0.945 |
| bm25 | 1 | 0.367 | 0.151 | 0.214 | 0.849 |
| bm25 | 3 | 0.256 | 0.315 | 0.282 | 0.685 |
| bm25 | 5 | 0.193 | 0.397 | 0.260 | 0.603 |
| bm25 | 10 | 0.143 | 0.589 | 0.231 | 0.411 |
| path_token | 3 | 0.167 | 0.206 | 0.184 | 0.795 |
| graph | 3 | 0.172 | 0.206 | 0.188 | 0.795 |
| hybrid | 3 | 0.233 | 0.288 | 0.258 | 0.712 |
| hybrid | 10 | 0.137 | 0.562 | 0.220 | 0.438 |

Macro (pooled, K=3): bm25 P 0.256/R 0.398/F1 0.285/FNR 0.602; graph
P 0.167/R 0.201/F1 0.166/FNR 0.799; hybrid P 0.233/R 0.353/F1 0.257/FNR 0.647.

**Pooled tables are development context, not a K-selection device.** The pooled
best-F1 (bm25 @K=3) is dominated by the 24 TRAIN cases; the primary
development-decision table is VALIDATION (F). No K is declared final from the
pool.

## I. Sensitivity analysis excluding visible-path cases (ZERO API, diagnostic)

**Why:** 3 TRAIN cases carry a full-message public intent that literally
mentions a changed path. This is NOT hidden-gold pipeline leakage (the P1
planner sees the same public query), but it is a **task-level localization
shortcut** for those cases. A deterministic, zero-API recomputation over the
persisted per-task metrics excludes them.

**Excluded (all TRAIN):** `djangocms-rc-2efae8e43bd6`,
`djangocms-rc-ada585d3f358`, `djangocms-rc-5ff38b521274`.

Diagnostic output (persisted):
`research/cheap-baselines-v1/path_mention_sensitivity_v1.json`
(regenerate: `python scripts/sensitivity_cheap_baselines_path_mentions.py`).

### Original vs path-clean TRAIN (micro; BM25)

| Table | K | P | R | F1 | FNR |
|---|---|---|---|---|---|
| ORIGINAL TRAIN (n=24) | 3 | 0.236 | 0.354 | 0.283 | 0.646 |
| ORIGINAL TRAIN (n=24) | 10 | 0.125 | 0.625 | 0.208 | 0.375 |
| PATH-CLEAN TRAIN (n=21) | 3 | 0.222 | 0.318 | 0.262 | 0.682 |
| PATH-CLEAN TRAIN (n=21) | 10 | 0.129 | 0.614 | 0.213 | 0.386 |

### Original vs path-clean pooled (micro; BM25)

| Table | K | P | R | F1 | FNR |
|---|---|---|---|---|---|
| ORIGINAL POOLED (n=30) | 3 | 0.256 | 0.315 | 0.282 | 0.685 |
| ORIGINAL POOLED (n=30) | 10 | 0.143 | 0.589 | 0.231 | 0.411 |
| PATH-CLEAN POOLED (n=27) | 3 | 0.247 | 0.290 | 0.267 | 0.710 |
| PATH-CLEAN POOLED (n=27) | 10 | 0.148 | 0.580 | 0.236 | 0.420 |

### Result

- Path-clean TRAIN BM25@3 F1 drops from 0.283 → **0.262**; path-clean pooled
  BM25@3 F1 drops from 0.282 → **0.267**. The 3 path-mention cases carried
  roughly half of BM25@3's TRAIN TP gain (TRAIN TP 17 → 14; pooled TP 23 → 20).
- **The material qualitative baseline ordering is unchanged**
  (BM25 > Hybrid > max(Graph, path_token) > Random; Graph ≈ path_token at every
  K, |ΔF1| < 0.01). The only change is a tie-level graph↔path_token micro
  sub-order flip at K=10 (ΔF1 < 0.001), which does not alter any claim.
- Conclusion: the frozen-corpus path-mention property inflates BM25 somewhat on
  TRAIN/pooled but does **not** change which baseline is strongest, and the
  VALIDATION split (F) contains none of the 3 cases and is unaffected.
- **This is a sensitivity diagnostic only.** The frozen dataset is NOT modified;
  the original tables remain the primary development evidence.

## J. Efficiency decomposition

**Two distinct costs are separated (persisted: `efficiency_v1.json`):**

| Baseline | Index-build total (s) | Corpus-build (git archive) total (s) | Query total (s) | LLM calls/tokens |
|---|---|---|---|---|
| B0 random | 0.000 | 0.000 | 0.010 | 0 / 0 |
| B1 bm25 | 15.78 | 377.85 | 1.08 | 0 / 0 |
| B2 path_token | 0.000 | 0.000 | 0.530 | 0 / 0 |
| B3 graph | 0.000 | 0.000 | 1.08 | 0 / 0 |
| B4 hybrid | 15.78 | 377.85 | 1.11 | 0 / 0 |

- Wall-clock ≈ **403 s for BM25/hybrid, dominated by parent-state `git archive`
  materialization (~13 s/case)** — a one-time repository snapshot / index-build
  cost, not inference.
- **Query/ranking latency is ~1.3 s total** across all 120 BM25 cells
  (≈10 ms/case). BM25 itself is NOT a 403-second inference method.
- Pure metadata/graph baselines cost < 2 s total. Memory trivial (per-case
  corpora).
- **Caching / pre-indexing the parent snapshot at repository-pin time is an
  engineering optimization, NOT a new scientific result.** It is recorded here
  so the cheap arm's operational cost is not misread as an algorithmic one.

## K. What we learned about BM25

- BM25@K is the **strongest cheap lexical baseline** on development data: on
  VALIDATION it reaches F1 0.2791 @K=3 (P 0.333, precision-oriented) and
  F1 0.3059 @K=10 (R 0.520, recall/FNR-oriented).
- It trains on nothing: it uses only parent file text + the visible commit
  intent, so its signal is genuinely zero-LLM and zero-trained.
- K is an **operating-point curve, not a conclusion** (F). K must be set by a
  future frozen protocol's primary objective, not by pooling.
- BM25 leaves a large omission hole (VALIDATION FNR 0.480 @K=10): even the best
  recall operating point misses half the changed files. That is precisely the
  target of the omission-risk pillar.
- On the path-clean sensitivity set, BM25 remains strongest but slightly lower
  (I), so its headline development numbers are partly helped by 3 intent
  path-mention TRAIN cases — documented, not hidden.

## L. What we learned about Graph

- **Graph@K in Protocol A uses lexical/path-token-derived seeds** (the frozen
  seed rule is intent-token ∩ candidate-token). The BFS/lexical ranking then
  reorders that seed neighborhood.
- Therefore **Graph≈Path does NOT show graph reasoning is generally
  unhelpful.** It shows that **this cheap lexical-seeded graph expansion adds
  little over the seed signal under this development protocol** (it neither
  recovers recall the seed misses nor adds a material precision edge).
- **No general negative graph result is claimed.** The M3 development-set
  finding (graph as a precision/ordering signal, not a recall amplifier) is
  consistent with, and bounded to, this lexical-seed protocol.

## M. What we learned about Hybrid

- The frozen **0.5 BM25 + 0.5 Graph hybrid does not materially improve over
  BM25** in this development study (pooled F1 0.258 vs 0.282 @K=3; VALIDATION
  identical at K=3, slightly lower at K=10).
- **No alpha tuning was performed and none will be now; no new hybrid
  experiment is created.**
- This motivates testing **graph reasoning later as bounded/selective
  verification** (e.g., targeted graph-guided expansion only where the lexical
  signal is weak or where omission risk is elevated) rather than simple score
  fusion.

## N. What this DOES NOT establish

- **No fair LLM-vs-BM25 superiority result.** BM25 was evaluated on
  TRAIN/VALIDATION; the reported Full/Sparse numbers come from a different
  permanently exposed HELD_OUT split. The only safe wording: **BM25 provides a
  meaningful zero-LLM localization signal on development data. Whether it
  matches or underperforms the LLM planners remains untested under a shared
  fresh confirmatory protocol.** P1 Full/Sparse F1 (0.353 / 0.312) appear only
  as directional context, never as a head-to-head ranking.
- **No confirmatory generalization.** TRAIN/VALIDATION (n=30) is development
  evidence; VALIDATION n=6 is small.
- **No graph-general conclusion** (L).
- **No hybrid-optimization result** (M).
- **No Saleor result** and **no risk-detector result** (O/P).
- K=3 or K=5 is **not** declared the final BM25 configuration (F/H).

## O. Connection to Omission-Risk / Selective Escalation

- Cheap baselines' persistent **FNR is the opening** for the thesis's
  omission-risk pillar: a cheap Sparse/BM25 first pass leaves
  unidentified changes (VALIDATION FNR 0.48–0.96; pooled FNR 0.41–0.56 @K=10),
  and the research question is whether **post-first-pass signals** (e.g.,
  lexical-retrieval disagreement, weak-seed cases, graph reachability) can
  predict which cases carry elevated omission risk — enabling **selective
  graph-guided escalation** instead of full regeneration.
- The hybrid result (M) says: prefer **targeted verification/escalation** over
  indiscriminate score fusion.
- Draft protocol: `docs/OMISSION_RISK_DETECTION_PROTOCOL_DRAFT.md` (not run).

## P. Connection to Saleor

- Saleor is the **second-repository confirmatory line** (fresh repository, not
  the exposed HELD_OUT ten).
- The cheap-baselines lesson is a **mining/annotation lesson**: persist and
  test the SAME string that is consumed (the path-mention caveat arose because
  the eligibility leak detector used the short subject while the persisted
  intent is the full message).
- Draft protocol: `docs/SALEOR_CONFIRMATORY_PROTOCOL_DRAFT.md`. NO Saleor
  scientific execution has run.

## Q. Connection to LocAgent future work

- The faithful LocAgent track (shared-protocol adapter, P5) would be the LLM
  side of a **shared fresh confirmatory protocol** that could finally compare
  BM25 vs LLM planners fairly (same split, same evaluator, same budget rules).
- The cheap-baseline arm is a legitimate **zero-cost reference/control** for
  any future LocAgent comparison; the common P1 evaluator already used for
  both sides makes that comparison mechanically sound once the split discipline
  is satisfied.
- LocAgent is NOT re-run here (zero API; frozen P5 evidence unchanged).

## R. Threats / caveats

- Development evidence only (TRAIN 24 + VALIDATION 6; VALIDATION n=6).
- Single repository (djangoCMS); parent-content corpus locally git-materialized.
- 3 TRAIN cases carry full-message path mentions (shared with the P1 planner;
  sensitivity-checked, not hidden) — BM25 development numbers are slightly
  inflated by them.
- The exposed HELD_OUT ten are permanently unusable for tuning; a fresh
  confirmatory split/repository is required for any LLM-vs-BM25 ranking.
- No statistical significance testing (paired bootstrap across the tiny
  VALIDATION set is not meaningful).
- Wall-clock dominated by git archive (J) — engineering, not algorithmic.

## S. Exact next scientific decision

**ONE next scientific step (recommended, NOT started):**
**Design and freeze the omission-risk detection protocol** on TRAIN/VALIDATION
with a primary selection objective that fixes the BM25 operating point (F/H),
then develop the risk detector on the post-cheap-first-pass signals
(`docs/OMISSION_RISK_DETECTION_PROTOCOL_DRAFT.md`), and only afterwards run a
**fresh confirmatory** LLM-vs-BM25 comparison (Saleor or a new non-exposed
split) under a shared frozen protocol.

This block is complete; nothing further is executed in this task.

## T. Engineering closure

- Deterministic zero-API pipeline + config/manifest/efficiency/prediction
  artifacts: `research/cheap-baselines-v1/`.
- Six gates + independent audit: `reports/cheap_baselines_v1_gates.json`.
- Sensitivity diagnostic + tests:
  `src/benchmark/cheap_baselines/sensitivity.py`,
  `scripts/sensitivity_cheap_baselines_path_mentions.py`,
  `tests/unit/test_cheap_baselines_sensitivity.py`,
  `research/cheap-baselines-v1/path_mention_sensitivity_v1.json`.
- Report/audit: `reports/CHEAP_BASELINES_V1_REPORT.md` (this file),
  `reports/CHEAP_BASELINES_V1_AUDIT.md`.
- Docs synchronized (00_CURRENT_RESEARCH_STATE, PROGRESS, DECISIONS P10,
  SYSTEM_STATE, TODO, MSc roadmap).
- Merged into `main`; tagged `cheap-baselines-v1-dev-2026-09-16` (DEV evidence
  only); light export created after merge/tag.

---

## Artifacts

- Raw predictions: `research/cheap-baselines-v1/raw_predictions_v1.json`
- Per-task metrics: `research/cheap-baselines-v1/per_task_metrics_v1.json` / `.csv`
- Aggregates: `research/cheap-baselines-v1/aggregate_v1.json` / `.csv`
- Config/manifest: `research/cheap-baselines-v1/config_v1.json`, `manifest_v1.json`
- Efficiency: `research/cheap-baselines-v1/efficiency_v1.json`
- Sensitivity diagnostic: `research/cheap-baselines-v1/path_mention_sensitivity_v1.json`
- Gates: `reports/cheap_baselines_v1_gates.json`
- Code: `src/benchmark/cheap_baselines/`, `scripts/run_cheap_baselines.py`,
  `scripts/verify_cheap_baselines_v1.py`, `scripts/export_cheap_baselines_csv.py`,
  `scripts/sensitivity_cheap_baselines_path_mentions.py`