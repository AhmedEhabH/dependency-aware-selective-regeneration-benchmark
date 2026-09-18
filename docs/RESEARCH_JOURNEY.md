# Research Journey — What We Tried, What Worked, What Failed, and Why It Matters

**Purpose:** preserve, for future researchers/engineers, what was tried, why,
what happened, what was ruled out, what came next, and what should NOT be
repeated without new justification. This is the **chronological** companion to
the README (current-state overview) and
[`00_CURRENT_RESEARCH_STATE.md`](../00_CURRENT_RESEARCH_STATE.md) (scientific
truth). Negatives are **search-space reductions / empirical boundaries**, not
thesis failures: each saves future time, API cost, and effort by ruling out an
approach already tested under this protocol.

**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731
**Last update:** 2026-09-18 (T2 docs-only)

---

## Chronological table

Date/Phase | Question | Method | Result | Decision | Why it matters | Revisit trigger | Evidence
---|:---|:---|:---|:---|:---|:---|:---
2026-08–09 | Preserve-by-Omission controlled studies (M1A/M1B, controlled representation) | Full explicit file-policy vs sparse preserve-by-omission on controlled djangoCMS tasks | M1B (16K): Sparse-v2 F1 0.794 vs Full-v2 0.571; ~90% lower completion output, ~96% fewer serialized records | Representation/cost advantage is real; semantic effect heterogeneous across task units | Sparse is a **cost** win, not a correctness claim | Only under a new controlled study with a different representation question | [M1B metrics](../research/controlled-encoding-ablation-16k-01/final_metrics.json) · [P1 correction](../reports/REAL_COMMIT_M4A3_P1_SERIALIZATION_METRIC_CORRECTION.md)
2026-09 | Graph ablation (M3) | Broadcast graph hints / graph-gated disclosure on the mechanism set | Hints: precision ↑ (0.72→0.81) but recall ↓ (0.88→0.80); gated disclosure not promising | Exploratory; no general "graphs improve selection" claim | Graph evidence is not a reliable universal lever | Only with a different graph-feeding mechanism + new protocol | [M3 report](../reports/) · [graph C0-C1-C2](../research/graph-c0-c1-c2-01/)
2026-09 | Real-commit dataset + leakage controls (M4A-1/M4A-2) | Deterministic miner, frozen filters/dedup, parent-only public/hidden boundary | 40 clean djangoCMS cases; 24/6/10 split; leakage-safe machinery | Dataset frozen; proxy = observed change-set, not gold | Provides the external-validity evidence base | — | [M4A-2 adjudication](../reports/REAL_COMMIT_M4A2_ADJUDICATION.md) · [definitions](../reports/DATASET_OPERATIONAL_DEFINITIONS.md)
2026-09-14 | Real-commit Full-vs-Sparse (M4A-3 / P1, 10 held-out) | 10 tasks × 2 arms × 3 reps = 60 cells | ΔF1 (Sparse−Full) −0.009 CI [−0.130,+0.119]; Δcost/task −$0.0235 (CI excludes 0) | Cost/output effect transfers; semantic superiority does NOT | Kills "sparse is semantically better" claim; keeps representation-cost claim | Only with a new representation hypothesis | [P1 correction](../reports/REAL_COMMIT_M4A3_P1_SERIALIZATION_METRIC_CORRECTION.md)
2026-09-15 | LocAgent shared protocol + P5R closure | Pinned upstream LocAgent under our shared protocol (WSL2 Ubuntu, same model route, common evaluator) | F1 0.333 (5/10 non-empty) vs Full 0.353 / Sparse 0.312; 50% empty/non-usable; 402 calls, ~$9.93 normalized | Shared-protocol comparison only; NOT a faithful published-config reproduction; no dominance claim | LocAgent at published cost is not favorable under our protocol; denominators must never mix | Only with a faithful published-config reproduction (new budget) | [P5C shared comparison](../reports/LOCAGENT_P5C_SHARED_COMPARISON.md) · [fair plan V2](../reports/LOCAGENT_FAIR_COMPARISON_PLAN_V2.md)
2026-09-16 | Cheap baselines / BM25 (Protocol A) | BM25@K, Graph@K, path_token@K, Hybrid@K on TRAIN 24 + VALIDATION 6 | BM25@K is the strongest cheap baseline (VALIDATION BM25@10 F1 0.306); K is an operating-point curve | BM25 gives a meaningful zero-LLM localization signal; graph ≈ path_token | Establishes the lexical floor; graph is not a free win | — | [Cheap baselines](../reports/CHEAP_BASELINES_V1_REPORT.md)
2026-09-16 | Task-level RiskScorer negative replication (omission-risk study) | 30-task TRAIN/VALIDATION feature study + 90-cell Sparse-v2 label inference | has_fn prevalence 86.7%; class-balance gate FAILED; only 3/97 features above the random band | **RiskScorer v1 NOT statistically justified**; no multivariable scorer | Rules out a meta-risk layer under this protocol; always-escalate dominates | Only with a much larger labeled pool (>30 tasks) | [Risk report](../reports/OMISSION_RISK_SPARSE_V2_INFERENCE_REPORT.md) · [audit](../reports/OMISSION_RISK_INFERENCE_AUDIT.md)
2026-09-16 | Route-B candidate-level recovery | Cheap candidate-level rankers (BM25/CIA/Hybrid) over omitted candidates on djangoCMS DEV | CIA/Hybrid beat analytic Random at every B; Oracle headroom large | Positive candidate-level signal on DEVELOPMENT | Establishes the Route-B line that later confirms | — | [Route-B V2](../reports/ROUTE_B_V2_ROBUSTNESS_REPORT.md)
2026-09-17 | Saleor DEVELOPMENT transfer | Frozen Route-B V2 protocol on Saleor DEV (149) | CIA B=5 macro ORR 0.237 vs random 0.006; **REPLICATES**; 5/5 folds positive | Cross-repository transfer on DEVELOPMENT | Generalization signal to a second repo | — | [Saleor transfer](../reports/SALEOR_ROUTE_B_TRANSFER_REPORT.md)
2026-09-17 | Graph incremental ablation / BM25 dominance | Incremental feature ablation on the Route-B ranking | Graph increment is small; most ranking signal is lexical/BM25 | Confirms BM25 dominance in ranking | Avoids over-investing in graph ranking | — | [Route-B ablation](../reports/ROUTE_B_INCREMENTAL_EVIDENCE_ABLATION.md)
2026-09-17 | djangoCMS fixed Route-B confirmatory | Frozen protocol on the spent djangoCMS INTERNAL_TEST (80) | Composite ORR B=5 0.165 vs random 0.028; gate PASS (5/5 folds, 4/4 B-points); final set F1 0.239 | **Fixed Route-B omission recovery CONFIRMED** | The anchor result of the thesis line | — | [Confirmatory](../reports/DJANGOCMS_ROUTE_B_CONFIRMATORY_RESULT.md)
2026-09-18 | P2 adaptive-budget Phase 1 (NEGATIVE) | Four adaptive-budget policies on a common DEV harness | Strong-method gate FALSE on both repos; fixed-B5 already near the practical point | **NEGATIVE, frozen** — choosing B is not the main bottleneck | Rules out adaptive budget as the primary fix | Only with a fundamentally different cost/reward model | [P2 final](../reports/P2_PHASE1_FINAL_REPORT.md)
2026-09-18 | AI-assisted semantic plausibility audit | Two blinded assistants (ChatGPT/Claude) judge file-level semantic plausibility | Exact agreement 0.698 / κ 0.558; historical-changed 0.847 vs omitted 0.632; top-ranked>random direction for both | **DESCRIPTIVE only — NOT human semantic gold** | Human gold remains AWAITING_HUMAN_RATINGS; do not cite as gold | Human ratings must be supplied first | [AI audit](../reports/AI_SEMANTIC_AUDIT_AGREEMENT_REPORT.md)
2026-09-18 | Oracle-gap decomposition | Deterministic oracle add/drop ceilings + F1 reachability on DEVELOPMENT | First-pass recall loss 75–79%; Oracle-Add ALL F1 0.867/0.829; **F1 0.85 NOT add-only-reachable on Saleor** | First-pass recall is the dominant bottleneck | Redirects effort to the ADD side | — | [Oracle-gap](../reports/ORACLE_GAP_BIDIRECTIONAL_REPAIR_FINAL_REPORT.md)
2026-09-18 | FP-pruning negative | Cheap observable features to flag selected-set false positives | Flagged precision ≈ random control; TP-loss risk 36–44% | **NEGATIVE** — cheap DROP signal too weak | Avoids a DROP queue based on cheap signals | Only with stronger (e.g. verified) signals | [FP pruning](../reports/SELECTED_SET_FP_PRUNING_FEASIBILITY.md)
2026-09-18 | BBSR → `BIDIRECTIONAL_HEADROOM_ONLY` | Zero-LLM bidirectional bounded set repair simulation | Heuristic BBSR fails the progression gate on both repos; oracle headroom exists but cheap signals cannot realize the DROP side | **BIDIRECTIONAL_HEADROOM_ONLY** — no new verifier calls authorized | Rules out the DROP side; keeps ADD side | Only when a much stronger FP-discriminator exists | [BBSR](../reports/BBSR_DEVELOPMENT_SIMULATION.md) · [final report](../reports/ORACLE_GAP_BIDIRECTIONAL_REPAIR_FINAL_REPORT.md)
FUTURE | **First-Pass Recall Bottleneck** (fixed next task, NOT started) | FN taxonomy → source-specific recovery ceilings → complementary ADD queues → matched-budget DEV comparison → gate; ZERO-API first | — | — | Addresses the dominant measured bottleneck | — | [Oracle-gap §17](../reports/ORACLE_GAP_BIDIRECTIONAL_REPAIR_FINAL_REPORT.md)

---

## Why negative findings are preserved

Every negative row above is preserved because it is a **tested empirical
boundary** that saves future researchers/engineers **time, API cost, and
effort** by ruling out an approach under this protocol:

- **Sparse semantic superiority** — ruled out by P1 (ΔF1 CI crosses zero).
- **Graph as a general lever** — ruled out by M3 + the Route-B ablation.
- **Adaptive budget as the main fix** — ruled out by P2 Phase-1 (NEGATIVE).
- **Task-level RiskScorer v1** — ruled out by the 30-task study (class balance).
- **Cheap DROP / FP-pruning** — ruled out by the FP-pruning study + BBSR.
- **LocAgent as a cheap competitor under our protocol** — ruled out by P5
  (fragility/cost), pending a faithful published-config reproduction.
- **Bidirectional set repair** — bounded to `BIDIRECTIONAL_HEADROOM_ONLY`.

Each has an explicit **revisit trigger** (new hypothesis, new protocol, more
data, or a genuinely stronger signal) — never "re-run because we want a
different number".

## Documentation architecture

README = concise navigation/current headline overview ·
[`00_CURRENT_RESEARCH_STATE.md`](../00_CURRENT_RESEARCH_STATE.md) = detailed
scientific truth · [`PROGRESS.md`](../PROGRESS.md) = current execution truth ·
[`DECISIONS.md`](../DECISIONS.md) = append-only decisions · this file =
chronological tried/learned/ruled-out history · [`reports/`](../reports/) =
authoritative experiment evidence.