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
**Last update:** 2026-09-18 (T2/T3 docs + ranking-bridge mission + precision-safe acceptance feasibility)

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
2026-09-18 | First-Pass Recall Bottleneck | FN taxonomy → source-specific ceilings → ≤3 ADD queues → matched-budget DEV eval + oracle reviewer → progression gate (ZERO API) | S006-like indirect-utility misses are GENERAL (consumer flag 58.9%/82.1% of FNs; 1-hop FNs 98.6%/100% lexically silent); reverse-1hop consumer pool carries 55.8%/72.4% of FNs @K=5, UNION_ALL 72.5%/87.0%; **NO simple ADD queue beats Route-B at matched budget**; oracle-reviewer F1 0.44/0.43 @B=5 vs Oracle-Add 0.72/0.64 | **RECALL_SIGNAL_HEADROOM_ONLY** — availability is NOT the bottleneck; RANKING is | Rules out simple binary-flag queues; directs the next instrument to verifier-ranked expansion under its own frozen budget | Only with a verifier-ranked (not binary-flag) pool expansion mission | [Final report](../reports/FIRST_PASS_RECALL_BOTTLENECK_FINAL_REPORT.md) · [taxonomy](../reports/FN_TAXONOMY_DEVELOPMENT.md) · [gate](../reports/FN_PROGRESSION_GATE.md)
2026-09-18 | Quantitative-structural ranking bridge | Exactly three transparent deterministic rankers (R1/R2/R3: BM25 + normalized reverse/bidirectional seed-support counts) over the high-coverage reverse-1hop pool, matched budget (ZERO API) | Section-1 reconfirmed the frozen gap EXACTLY; **best R1 at B=5 djangoCMS +0.034 but Saleor −0.020; NO formula material on BOTH repos**; folds not majority positive; artifact-free | **CHEAP_RANKING_CLOSED_FOR_NOW** — cheap count formulas cannot realize the ranking headroom | Rules out the last cheap-deterministic bridge; the bounded semantic middle layer is next | Only with a fundamentally stronger signal (e.g. typed edges, which the frozen graph does NOT expose) or the authorized semantic pilot | [Bridge report](../reports/QUANT_STRUCTURAL_RANKING_BRIDGE_REPORT.md) · [baseline freeze](../reports/fn_quant_ranking_bridge_baseline_freeze.json) · [audit](../reports/FN_QUANT_RANKING_BRIDGE_AUDIT.md)
2026-09-18 | Bounded semantic rerank/verify FREEZE (prepared, not executed) | Frozen protocol + API budget for a bounded semantic decision layer over Route-B top-10 ∪ reverse-1hop consumers (pool cap 40; ≤300 calls / ≤300k tokens / ≤$0.30 / ≤60 min) | NOT EXECUTED — ZERO calls; protocol + budget + exact authorization sentence delivered | Middle layer READY but gated on user authorization | Defines Stage 4 of the gap-reduction ladder; no call made | Execute ONLY under the explicit authorization sentence in the budget draft | [Protocol](../docs/BOUNDED_SEMANTIC_RERANK_VERIFY_PROTOCOL_FROZEN.md) · [budget draft](../reports/BOUNDED_SEMANTIC_EXPANSION_BUDGET_FREEZE_DRAFT.md)
2026-09-18 | Bounded semantic expansion pilot (AUTHORIZED) | Real Stage-4 run (300 calls: Arm A frozen Route-B verifier 240 + Arm B expanded-pool bounded rerank 60) on DEVELOPMENT under the frozen protocol/budget | Arm B raises ORR on djangoCMS (+0.139 @B=5) but NOT materially on Saleor (+0.023); naive final F1 falls materially on djangoCMS (−0.069); 106,325 tokens / $0.0444 / 553.6 s, ceilings respected | **BOUNDED_SEMANTIC_NEGATIVE_FROZEN** — preregistered gate FAIL (c1 saleor, c3 djangocms) | Closes Stage 4 NEGATIVE; the "ORR up but F1 down" case is not a success; no prompt/schema tuning | Only with a precision-safe acceptance rule (pre-registered) + explicit authorization | [Closure report](../reports/BOUNDED_SEMANTIC_EXPANSION_CLOSURE_REPORT.md) · [pilot report](../reports/BOUNDED_SEMANTIC_EXPANSION_PILOT_REPORT.md) · [audit](../reports/BOUNDED_SEMANTIC_EXPANSION_AUDIT.md) · [raw runs](../research/bounded-semantic-expansion/)
2026-09-18 | Precision-safe acceptance feasibility + protocol freeze (ZERO API) | Zero-API failure anatomy of the frozen 300-call record (rank-position precision, source split, cap loss, schema taxonomy, B=10 consistency) + ONE POST-HOC feasibility rule (RANK → VERIFY → VARIABLE ACCEPT) + exactly one frozen next protocol | FP tail is an acceptance-layer failure split across BOTH pool sources (dc 68/51, saleor 71/48); semantic rank is the first real FN-recovery instrument (dc ORR 0.111→0.250 @B5; 5/5 folds @B10 both repos); cap C=40 loses 10+29 FNs; 6/6 invalid = non-pool-path + partial credit; frozen verifier too weak (8.6–14% approval precision) and never assessed on consumer-only candidates | **FAMILY justified, specific frozen verifier not**; one frozen protocol (cap 80, K=10, strict boolean-vector verifier, variable 0..K, fresh disjoint sample seed 20260919, gate c1–c7 both repos) + budget draft (≤400 calls / 300k tok / $0.15 / 60 min), NOT EXECUTED | Diagnoses WHY Stage-4 failed (acceptance, not ranking) and freezes the exact precision-safe next instrument; no API spend | Execute ONLY under the exact authorization sentence in the budget draft §7; on gate FAIL freeze the negative | [Feasibility report](../reports/PRECISION_SAFE_ACCEPTANCE_FEASIBILITY_2026-09-18.md) · [metrics](../reports/precision_safe_feasibility_metrics.json) · [protocol](../docs/PRECISION_SAFE_ACCEPTANCE_PROTOCOL_FROZEN.md) · [budget draft](../reports/PRECISION_SAFE_ACCEPTANCE_BUDGET_FREEZE_DRAFT.md) · [audit](../reports/PRECISION_SAFE_ACCEPTANCE_AUDIT.md)

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
- **Simple binary-flag ADD queues for first-pass recall** — ruled out by the
  matched-budget comparison: none beats Route-B at matched K, so repeating them
  (or adding more binary flags) is unlikely to help; the loss is ranking-driven
  and the instrument is a verifier-ranked expansion under its own frozen budget.
- **Cheap quantitative-structural rankers for the reverse-1hop pool** — ruled
  out by the ranking bridge: three transparent count/normalized formulas
  (R1/R2/R3) give no material matched-budget ORR gain on BOTH repos
  (CHEAP_RANKING_CLOSED_FOR_NOW); the frozen graph's untyped edges block the
  typed-edge variant, and a semantic decision layer is the next instrument.
- **Bounded semantic rerank/verify over the expanded pool (this protocol)** —
  ruled out by the authorized Stage-4 pilot: Arm B raises ORR but not
  materially on Saleor (+0.023) and materially lowers naive final F1 on
  djangoCMS (−0.069) → BOUNDED_SEMANTIC_NEGATIVE_FROZEN. Repeating this exact
  protocol at higher budget is unlikely to help; any future semantic
  instrument needs a precision-safe acceptance rule.
- **The Stage-4 frozen verifier as a precision-safe acceptance layer** — ruled
  out POST-HOC by the feasibility anatomy: its approvals are 8.6–14% precise
  (it approves ~everything it sees) and it never saw reverse-1hop-only
  candidates, so an "AND verifier-approved" gate cannot rescue the FP tail
  without also removing FN recovery. This is a diagnosis of the SPECIFIC
  frozen instrument, NOT of the RANK → VERIFY → VARIABLE-ACCEPT family, which
  remains the single frozen next instrument under a new strict verifier.

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