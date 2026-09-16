# RESEARCH HARNESS V1 + LIVING SYSTEMATIC REVIEW V1 — CLOSURE REPORT

**Date:** 2026-09-16
**Classification:** T3 (reusable experiment architecture; NOT a new scientific
experiment; ZERO new scientific API/model calls).
**Model:** openrouter/deepseek/deepseek-v4-flash-0731
**Branch basis:** `main` @ `0ba7a1a` (clean tree).

---

## 1. Executive verdict

**PASS.** The pluggable research harness (V1) and the living systematic review
(V1) are complete, audited, and reproduce the frozen Protocol-A cheap-baseline
outputs byte-for-byte through the compatibility layer. All six T3 validation
gates + interface/leakage/determinism/budget/config-reproducibility/
isolation tests PASS. Frozen scientific evidence is unchanged (full 30-case × 5
method × 4 K = 600-row scientific-equivalence run). No new scientific
experiment was started.

## 2. What this milestone IS

Reusable experiment architecture + a living competitor review. It generalizes
the research harness through explicit seams (DatasetAdapter, SnapshotProvider,
Ranker, Planner, ModelBackend, RiskScorer [interface only], Verifier [interface
only], BudgetPolicy, common Evaluator, versioned ExperimentSpec) without
building a universal plugin framework and without rewriting any frozen
generator or artifact.

## 3. What became configurable (goal A)

| Seam | What is now config | Where |
|---|---|---|
| DatasetAdapter | dataset name → concrete adapter (djangoCMS now; Saleor seam fail-closed) | `registry.resolve_dataset` |
| SnapshotProvider/RepositoryView | snapshot mode (`metadata` / `parent_commit`) and cache location | `DjangoCMSParentSnapshot(cache_dir)` |
| Ranker | method name → frozen B0–B4 ranker adapter | `registry.resolve_ranker` |
| Planner | seam (no concrete V1 registration; frozen LLM planners remain in their own modules) | `registry.resolve_planner` |
| ModelBackend | model/provider names are CONFIG strings; `none`/`mock` backends only in V1 | `registry.resolve_backend` |
| RiskScorer / Verifier | interface only; no concrete registration in V1 | `registry.known_names()` |
| BudgetPolicy | explicit max calls/tokens/cost/wallclock + `zero_llm` flag, persisted in the spec | `spec.budget` |
| common Evaluator | one scoring function (`harness-common-evaluator-v1`) wrapping frozen `p1_selection_metrics` | `evaluator.evaluate_prediction` |
| ExperimentSpec | versioned (`harness-experiment-spec-v1`), frozen, deterministic SHA-256 | `spec.ExperimentSpec` |

## 4. What deliberately remains repo-specific (goal A boundary)

- **djangoCMS adapter** (`djangocms.py`): repo identity, split policy for
  RealCommitImpactDataset-v1, candidate-universe semantics. Django-specific
  rules live ONLY there.
- **Saleor adapter** (`saleor.py`): fail-closed future seam; Saleor scientific
  execution is NOT authorized.
- Frozen cheap-baseline rankers/corpora (`benchmark/cheap_baselines/*`) are
  NOT rewritten — the harness adapts them.
- No universal plugin framework: seams are Python ABCs + a name registry +
  config.

## 5. Proof frozen results did not change (goal B/D)

- **Full equivalence run** `scripts/run_harness_protocol_a_equivalence.py`
  (git parent-commit corpus, all 30 TRAIN+VALIDATION cases):
  **600/600 rows** (30 cases × 5 methods × 4 K) scientific projection
  **byte-identical** to frozen `research/cheap-baselines-v1/raw_predictions_v1.json`;
  `per_task` view identical to `per_task_metrics_v1.json`; TRAIN/VALIDATION/
  TRAIN_VALIDATION aggregates identical to `aggregate_v1.json`.
  Evidence: `research/harness-protocol-a-equivalence/raw_predictions_via_harness_v1.json`.
- Wall-clock timing fields are excluded by design (non-deterministic by
  nature); scientific fields (ranked/selected paths, seed reason, corpus
  source, TP/FP/FN/P/R/F1/FNR) are exact.
- Frozen dataset, frozen cheap-baseline outputs, frozen P1/P5 evidence,
  paper artifact: untouched (git status shows no modification to those paths).

## 6. Systematic-review additions (goal C)

- `docs/LIVING_SYSTEMATIC_REVIEW.md` — living review doc (scope, legend,
  initial matrix, verification status, threats, update protocol).
- `research/literature/review_matrix.csv` — 12 seeded systems: RIPPLE,
  Repository Memory, Adaptive-k, LocAgent, GraphLocator, RepoGraph, Agentless,
  CodePlan, RepoCoder, AutoCodeRover, RPG/ZeroRepo, AB-RAG. Each row records
  mechanism, evidence, datasets, metrics, cost, relation to us, novelty
  threat, idea to test, and a truthful `status` (only LocAgent is VERIFIED
  with direct evidence; all others are `SEEDED - verify primary source`).
- `research/literature/search_log.csv` — 10 search entries (S001–S010).
- `research/literature/idea_ledger.md` — ideas I1–I7 with TEST / WATCH /
  BOUNDARY dispositions.

## 7. Most important competitor ideas

1. Localization-first without an agent loop (Agentless; CodePlan).
2. Repo-map / manifest-first retrieval (RPG/ZeroRepo).
3. Adaptive routing / adaptive-K (AB-RAG, adaptive-k).
4. Graph-guided agents (LocAgent; GraphLocator).

## 8. Novelty threats

- Agentless-style 'localize first' is the closest conceptual competitor
  (MEDIUM/HIGH); our differentiators: cheap non-LLM first pass + sparse
  representation + explicit cost-aware escalation gate.
- Graph-based localization (GraphLocator/RepoGraph) — MEDIUM; B3/Hybrid result
  already bounds graph-expansion value on the lexical seed signal.
- Adaptive-K / adaptive RAG routing — LOW–MEDIUM (known pattern; our
  contribution is the localization + budget discipline).

## 9. Recommended feature families for the Omission-Risk Feature Study v1

TRAIN/VALIDATION only, hidden-gold-free (from `idea_ledger.md` I1/I2/I5/I6):
1. First-pass statistics: predicted write-set size, VALIDATE count,
   action-distribution entropy, HUMAN_REVIEW triggers.
2. Manifest/repo-map features: candidate density, module/namespace breadth.
3. Graph neighborhood features: seed/frontier size, reachable zone,
   cross-component counts.
4. Lexical-retrieval disagreement (first-pass vs BM25@K ranking distance).
5. Routing metrics: AUROC/AUPRC, risk–coverage curve, escalation rate, FN
   recovery rate, cost per recovered FN.

## 10. Validation

Six T3 gates + independent audit PASS; `reports/research_harness_v1_gates.json`.
New tests: 40 unit + 4 integration harness tests; all existing cheap-baseline
tests (32) still pass; full suite runs at final gate.

## 11. Deliverables map

| Artifact | Path |
|---|---|
| Harness package | `src/benchmark/harness/` |
| Gates module | `src/benchmark/harness/gates.py` |
| Gate runner | `scripts/verify_research_harness_v1.py` |
| Equivalence runner | `scripts/run_harness_protocol_a_equivalence.py` |
| Gates JSON | `reports/research_harness_v1_gates.json` |
| Equivalence evidence | `research/harness-protocol-a-equivalence/raw_predictions_via_harness_v1.json` |
| Living review | `docs/LIVING_SYSTEMATIC_REVIEW.md` |
| Literature | `research/literature/{review_matrix,search_log}.csv`, `idea_ledger.md` |
| Audit | `reports/RESEARCH_HARNESS_V1_AUDIT.md` |

## 12. STOP CONDITION

After this harness + review foundation is audited, STOP. NOT started:
omission-risk training/analysis, Saleor scientific execution, LocAgent
scientific calls, selective escalation, new model runs.