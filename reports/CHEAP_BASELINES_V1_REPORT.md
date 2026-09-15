# CHEAP NON-LLM BASELINES v1 — REPORT

**Protocol:** `cheap-nonllm-baselines-v1` (T3 — new evaluation strategy / baseline family)
**Date:** 2026-09-16 (first POST-ICCI experimental block)
**Model/AI:** openrouter/deepseek/deepseek-v4-flash-0731 (implementation only; **zero LLM calls in the experiment**)
**Branch:** `research/cheap-nonllm-baselines-v1`
**Dataset:** `benchmark_data/real_commit_impact_v1` — **TRAIN 24 + VALIDATION 6 only**; HELD_OUT_TEST 10 permanently excluded from all decisions.
**Reference:** observed changed-production-Python proxy within U_t (evaluation-only).
**Evaluator:** frozen P1 binary evaluator (`p1_selection_metrics`, same as P1/P5).

---

## 0. Executive summary

- Zero-LLM baselines provide genuine but limited signal on TRAIN+VALIDATION:
  **BM25@K is the strongest** (pooled F1 0.282 @K=3; recall 0.589 @K=10),
  Random@K is a ≈0.01–0.07 F1 floor, Graph@K ≈ path_token@K, Hybrid@K ≈ BM25@K.
- Far from the LLM planners on the exposed held-out proxies (Full-v2 F1 0.353,
  Sparse-v2 F1 0.312); directional context only (exposed split not comparable).
- Cheap baselines do **not** solve omission (pooled FNR 0.41–0.56 at K=10) —
  the exact hole the omission-risk pillar (thesis core) targets.
- All rules frozen before results; HELD_OUT_TEST never touched; ZERO API cost.

## 1. Question

Does an inexpensive, zero-LLM repository-localization baseline provide useful
file-selection value relative to (and as a reference point for) the LLM impact
planner line? This block establishes the cheapest defensible baseline family
and freezes its configuration; it is **development evidence**, not
confirmatory.

## 2. Method

Five deterministic, zero-API baselines at K ∈ {1, 3, 5, 10}:

| ID | Baseline | Description | Inputs |
|---|---|---|---|
| B0 | Random@K | seeded deterministic shuffle (per-case seed = `20260915:case_id`) | candidate paths only |
| B1 | BM25@K | Okapi BM25 (in-repo impl) over parent-commit file content vs visible intent | parent-only file corpus + intent |
| B2 | Path/token@K | token-overlap between path/module/class/function token sets and intent tokens | candidate metadata + intent |
| B3 | Graph@K | frozen parent-only dependency graph; seed = intent-token ∩ candidate-token hits; rank by BFS distance then lexical overlap | graph edges + metadata + intent |
| B4 | Hybrid@K | frozen rule: 0.5·Nm(BM25) + 0.5·Ng(graph); seedless → pure BM25 | BM25 scores + graph distances |

**Frozen before validation:** seed rule (intent-token ∩ candidate-token, no gold);
hybrid alpha = 0.5; K grid; tie-break = (-score, path); BM25 k1=1.5/b=0.75;
stopword set. No threshold/method/K selection used validation results — all
rules were fixed pre-run. If the seed rule yields an empty set, Graph@K emits
an empty ranking and documents the case (no invented signal).

**Leakage controls:** ranking inputs are strictly (public intent, candidate
metadata, parent-only corpus via `git archive <parent>`, parent-only graph).
The hidden proxy and target/future state are never pipeline inputs.
**Frozen-corpus caveat (documented):** 3 TRAIN cases (e.g.
`djangocms-rc-2efae8e43bd6`) carry full-message intents that **literally
contain a changed path** (the M4A-2 eligibility leak detector used the short
subject; the persisted intent is the full message). The P1 LLM planner saw the
same full-message intent, so this is a dataset property shared by both,
**not** a pipeline leak introduced by baselines.

## 3. Efficiency (30 cases, 30×5×4 = 600 cells)

| Baseline | Index-build total (s) | Corpus-build total (s) | Query total (s) | LLM calls | LLM tokens |
|---|---|---|---|---|---|
| B0 random | 0.000 | 0.000 | 0.010 | 0 | 0 |
| B1 bm25 | 15.782 | ~387 (git archive) | 1.146 | 0 | 0 |
| B2 path_token | 0.000 | 0.000 | 0.571 | 0 | 0 |
| B3 graph | 0.000 | 0.000 | 1.133 | 0 | 0 |
| B4 hybrid | 15.782 | ~387 (git archive) | 1.303 | 0 | 0 |

Wall-clock ≈ 403 s for BM25/hybrid, dominated by parent-state git archive
(~13 s/case). Pure metadata/graph baselines cost < 2 s total. Memory trivial
(per-case corpora).

## 4. Aggregate results (micro; DEVELOPMENT EVIDENCE)

### VALIDATION (6 tasks) — micro

| Baseline | K | P | R | F1 | FNR | TP | FP | FN |
|---|---|---|---|---|---|---|---|---|
| random | 1 | 0.000 | 0.000 | 0.000 | 1.000 | 0 | 6 | 25 |
| random | 3 | 0.056 | 0.040 | 0.047 | 0.960 | 1 | 17 | 24 |
| random | 5 | 0.067 | 0.080 | 0.073 | 0.920 | 2 | 28 | 23 |
| random | 10 | 0.050 | 0.120 | 0.071 | 0.880 | 3 | 57 | 22 |
| bm25 | 1 | 0.167 | 0.040 | 0.065 | 0.960 | 1 | 5 | 24 |
| bm25 | 3 | 0.333 | 0.240 | **0.279** | 0.760 | 6 | 12 | 19 |
| bm25 | 5 | 0.233 | 0.280 | 0.255 | 0.720 | 7 | 23 | 18 |
| bm25 | 10 | 0.217 | 0.520 | 0.306 | 0.480 | 13 | 47 | 12 |
| path_token | 1 | 0.167 | 0.040 | 0.065 | 0.960 | 1 | 5 | 24 |
| path_token | 3 | 0.222 | 0.160 | 0.186 | 0.840 | 4 | 14 | 21 |
| path_token | 5 | 0.200 | 0.240 | 0.218 | 0.760 | 6 | 24 | 19 |
| path_token | 10 | 0.183 | 0.440 | 0.259 | 0.560 | 11 | 49 | 14 |
| graph | 1 | 0.167 | 0.040 | 0.065 | 0.960 | 1 | 5 | 24 |
| graph | 3 | 0.222 | 0.160 | 0.186 | 0.840 | 4 | 14 | 21 |
| graph | 5 | 0.200 | 0.240 | 0.218 | 0.760 | 6 | 24 | 19 |
| graph | 10 | 0.183 | 0.440 | 0.259 | 0.560 | 11 | 49 | 14 |
| hybrid | 1 | 0.167 | 0.040 | 0.065 | 0.960 | 1 | 5 | 24 |
| hybrid | 3 | 0.333 | 0.240 | **0.279** | 0.760 | 6 | 12 | 19 |
| hybrid | 5 | 0.200 | 0.240 | 0.218 | 0.760 | 6 | 24 | 19 |
| hybrid | 10 | 0.200 | 0.480 | 0.282 | 0.520 | 12 | 48 | 13 |

### TRAIN (24 tasks) — micro

| Baseline | K | P | R | F1 | FNR | TP | FP | FN |
|---|---|---|---|---|---|---|---|---|
| random | 1 | 0.000 | 0.000 | 0.000 | 1.000 | 0 | 24 | 48 |
| random | 3 | 0.000 | 0.000 | 0.000 | 1.000 | 0 | 72 | 48 |
| random | 5 | 0.000 | 0.000 | 0.000 | 1.000 | 0 | 120 | 48 |
| random | 10 | 0.004 | 0.021 | 0.007 | 0.979 | 1 | 239 | 47 |
| bm25 | 1 | 0.417 | 0.208 | 0.278 | 0.792 | 10 | 14 | 38 |
| bm25 | 3 | 0.236 | 0.354 | **0.283** | 0.646 | 17 | 55 | 31 |
| bm25 | 5 | 0.183 | 0.458 | 0.262 | 0.542 | 22 | 98 | 26 |
| bm25 | 10 | 0.125 | 0.625 | 0.208 | 0.375 | 30 | 210 | 18 |
| path_token | 1 | 0.167 | 0.083 | 0.111 | 0.917 | 4 | 20 | 44 |
| path_token | 3 | 0.153 | 0.229 | 0.183 | 0.771 | 11 | 61 | 37 |
| path_token | 5 | 0.117 | 0.292 | 0.167 | 0.708 | 14 | 106 | 34 |
| path_token | 10 | 0.092 | 0.458 | 0.153 | 0.542 | 22 | 218 | 26 |
| graph | 1 | 0.174 | 0.083 | 0.113 | 0.917 | 4 | 19 | 44 |
| graph | 3 | 0.159 | 0.229 | 0.188 | 0.771 | 11 | 58 | 37 |
| graph | 5 | 0.122 | 0.292 | 0.172 | 0.708 | 14 | 101 | 34 |
| graph | 10 | 0.091 | 0.438 | 0.151 | 0.563 | 21 | 209 | 27 |
| hybrid | 1 | 0.375 | 0.188 | 0.250 | 0.813 | 9 | 15 | 39 |
| hybrid | 3 | 0.208 | 0.313 | 0.250 | 0.688 | 15 | 57 | 33 |
| hybrid | 5 | 0.192 | 0.479 | 0.274 | 0.521 | 23 | 97 | 25 |
| hybrid | 10 | 0.121 | 0.604 | 0.201 | 0.396 | 29 | 211 | 19 |

### Pooled TRAIN+VALIDATION (30 tasks) — micro

| Baseline | K | P | R | F1 | FNR | TP | FP | FN |
|---|---|---|---|---|---|---|---|---|
| random | 3 | 0.011 | 0.014 | 0.012 | 0.986 | 1 | 89 | 72 |
| random | 10 | 0.013 | 0.055 | 0.021 | 0.945 | 4 | 296 | 69 |
| bm25 | 1 | 0.367 | 0.151 | 0.214 | 0.849 | 11 | 19 | 62 |
| bm25 | 3 | 0.256 | 0.315 | **0.282** | 0.685 | 23 | 67 | 50 |
| bm25 | 5 | 0.193 | 0.397 | 0.260 | 0.603 | 29 | 121 | 44 |
| bm25 | 10 | 0.143 | 0.589 | 0.231 | 0.411 | 43 | 257 | 30 |
| path_token | 3 | 0.167 | 0.206 | 0.184 | 0.795 | 15 | 75 | 58 |
| graph | 3 | 0.172 | 0.206 | 0.188 | 0.795 | 15 | 72 | 58 |
| hybrid | 3 | 0.233 | 0.288 | 0.258 | 0.712 | 21 | 69 | 52 |

Macro (pooled, K=3): bm25 P 0.256/R 0.398/F1 0.285/FNR 0.602; graph
P 0.167/R 0.201/F1 0.166/FNR 0.799; hybrid P 0.233/R 0.353/F1 0.257/FNR 0.647.
(Macro tables in `research/cheap-baselines-v1/aggregate_v1.json`.)

## 5. Interpretation

- **Random@K is a floor ≈ 0.01–0.07 F1** — the task is far above chance, so
  any positive signal is real.
- **BM25@K is the strongest cheap lexical baseline** (pooled best F1 0.282 @K=3;
  @K=10 recall 0.589, FNR 0.411). Trained on nothing, it uses only parent file
  text + the visible commit intent.
- **Graph@K ≈ path_token@K** with a slight precision edge on TRAIN. Reason:
  the frozen seed rule *is* the token-overlap basis, so the graph mainly reorders
  the same seed neighborhood; it does not recover recall the lexical signal
  misses. Consistent with the M3 development-set finding (graph as a
  precision/ordering signal, not a recall amplifier).
- **Hybrid@K ≈ BM25@K** (cleanly overlaps at most K); the graph term neither
  helps nor hurts materially at these small proxy sizes.
- **Signal is far from the LLM planners on the (larger) exposed held-out
  proxies:** Full-v2 F1 0.353, Sparse-v2 F1 0.312 on the 10 exposed tasks
  (which have proxy sizes ≈3–36), versus pooled baseline best F1 0.282 @K=3 on
  TRAIN+VALIDATION (proxy sizes ≈1–9). Exact cross-split comparability is
  prohibited (exposed split), so these are directional context only.
- **FNR remains high for all baselines even at K=10** (0.41–0.56 pooled), which
  is exactly the hole the omission-risk pillar (thesis core) targets: cheap
  first passes leave substantial unidentified changes, motivating bounded
  verification.

## 6. Frozen baseline selection (development evidence)

Candidate method to carry forward in the proposal's cheap-baseline arm
(tentative, pending Ahmed's review): **BM25@K with K=3 or K=5** (best F1 at
K=3, best FNR at K=5) and **Random@K as the control**, plus the frozen
Hybrid@K rule for the escalation-pipeline reference. All implementation, K
grid, metric code, seed rule, and candidate-universe rules are frozen in
`research/cheap-baselines-v1/config_v1.json`. No threshold was tuned on
validation; no exposed held-out case informed any decision.

## 7. Matched-cardinality note

A matched-cardinality view (predicting exactly the observed proxy cardinality)
is **not reported**: Full/Sparse predicted write-set sizes exist only on the
exposed HELD_OUT_TEST ten; using them for TRAIN/VALIDATION would be a leakage
of the exposed split. The fixed-K tables are the honest default.

## 8. Limitations

- Development evidence only (TRAIN+VALIDATION n=30; VALIDATION n=6).
- Single repository (djangoCMS), parent-content corpus currently local-git
  materialized.
- BM25 wall-clock dominated by git archive; an index pre-built at repository
  snapshot time would cut that.
- 6 frozen cases carry full-message path mentions (shared with the P1 planner;
  documented, not hidden).
- No statistical significance testing against the exposed HELD_OUT_TEST.

## 9. Artifacts

- Raw predictions: `research/cheap-baselines-v1/raw_predictions_v1.json`
- Per-task metrics: `research/cheap-baselines-v1/per_task_metrics_v1.json` / `.csv`
- Aggregates: `research/cheap-baselines-v1/aggregate_v1.json` / `.csv`
- Config/manifest: `research/cheap-baselines-v1/config_v1.json`, `manifest_v1.json`
- Efficiency: `research/cheap-baselines-v1/efficiency_v1.json`
- Gates: `reports/cheap_baselines_v1_gates.json`
- Code: `src/benchmark/cheap_baselines/`, `scripts/run_cheap_baselines.py`,
  `scripts/verify_cheap_baselines_v1.py`, `scripts/export_cheap_baselines_csv.py`