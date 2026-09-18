# Experiment and Idea Ledger

**Purpose:** every meaningful idea/experiment — proposed / executed / rejected /
deferred / superseded — with why, result, artifact, and whether it may be
revisited. Complements `research/literature/idea_ledger.md` (literature ideas).

Legend: PROPOSED / EXECUTED / REJECTED / DEFERRED / SUPERSEDED.

---

## E-001 — Preserve-by-Omission representation (controlled, 16K)
- **Status:** EXECUTED (M1B).
- **Result:** Sparse 4.9 vs Full 144.0 mean serialized records; ~96.6% reduction;
  large completion-token/cost reduction. No semantic-superiority claim.
- **Artifact:** `reports/CONTROLLED_ENCODING_16K_RESULT.md`.
- **Revisit:** no (frozen controlled evidence).

## E-002 — Real-commit held-out Full vs Sparse (P1)
- **Status:** EXECUTED.
- **Result:** 60/60 valid; selection hard, FNR high; no Full-vs-Sparse
  superiority (paired CIs cross zero); Sparse cheaper.
- **Artifact:** `reports/REAL_COMMIT_M4A3_P1_RESULT.md`.
- **Revisit:** no.

## E-003 — Graph-gated disclosure (C2)
- **Status:** EXECUTED / NOT PROMISING as implemented.
- **Result:** gated disclosure did not improve; hints MIXED.
- **Artifact:** M3 report.
- **Revisit:** not in this thesis line.

## E-004 — Task-level omission-risk (v1 deterministic + Sparse-v2)
- **Status:** EXECUTED (v1 + V2) → REJECTED for RiskScorer.
- **Result:** v1: 26/30 has_fn, class-balance gate failed; V2: 144 tasks, merged
  174 / 155 pos / 19 neg; signal does not replicate (universe artifact).
- **Artifact:** omission-risk reports.
- **Revisit:** only if a larger balanced development set passes the gate.

## E-005 — Adaptive-K vs fixed K=10
- **Status:** EXECUTED → REJECTED.
- **Result:** adaptive rules did not beat fixed K=10.
- **Artifact:** omission-risk adaptive-K results.
- **Revisit:** no.

## E-006 — Fixed 0.5/0.5 Hybrid
- **Status:** EXECUTED (Protocol A / classical CIA).
- **Result:** hybrid ~ BM25; no improvement over BM25.
- **Artifact:** cheap-baselines / CIA report.
- **Revisit:** no.

## E-007 — Classical/static CIA baseline (dependency propagation)
- **Status:** EXECUTED (150 V2 dev cases, zero LLM).
- **Result:** BM25/GRAPH@K strongest; reverse-dependency closure arms weaker.
- **Artifact:** `reports/CLASSICAL_CIA_BASELINE_V1_REPORT.md`.
- **Revisit:** extend to cross-repo.

## E-008 — Route B candidate-level bounded omission recovery
- **Status:** PROPOSED (primary next mechanism); zero-LLM study to run in this
  mission.
- **Result:** pending.
- **Revisit:** n/a.

## E-009 — LocAgent P5 (shared-protocol)
- **Status:** EXECUTED (immutable).
- **Result:** 5/10 usable; 2 timeout + 1 context + 2 empty; 402 calls /
  32.8M tokens / ~$9.93 estimated.
- **Artifact:** `reports/LOCAGENT_P5C_HELDOUT_RUN.md`.
- **Revisit:** P5R-1 (new robustness study; not a P5 rewrite).

## E-010 — Saleor Stage 2
- **Status:** DEFERRED (SUITABLE-WITH-DEVIATIONS; no inference tonight).
- **Revisit:** after full-history cache + frame + split freeze.

## E-011 — NestJS Stage 3
- **Status:** DEFERRED (SUITABLE-WITH-DEVIATIONS; TS extractor required).
- **Revisit:** after TS import extractor + eligible-pool yield check.

## E-012 — Semantic-proxy human adjudication packets
- **Status:** PROPOSED (development-only sample; human audit required; AI notes
  not semantic gold).
- **Revisit:** n/a.

## E-013 — V2-LARGE vs V2-CENSUS
- **Status:** DECIDED → V2-LARGE default (census descriptive-only).
- **Revisit:** no for the confirmatory line.

## E-014 — Verifier pilot (LLM)
- **Status:** PROPOSED only if the Route-B progression gate strongly passes
  (<=30 tasks/calls, <=300k tokens, <=$0.30, dev-only).
- **Revisit:** after Route B zero-LLM study.

## E-015 — BibTeX triage
- **Status:** EXECUTED (2026-09-16 evening).
- **Result:** 987 raw / 806 unique; 9 USE_NOW / 260 VERIFY_FIRST / 56 BACKGROUND
  / 315 REJECT / 166 DUPLICATE.
- **Artifact:** `reports/BIBTEX_LITERATURE_TRIAGE_2026-09-16.md` + classified CSV.
- **Revisit:** as new literature appears.
## E-016 — LocAgent P5R-1 rescue pilot (live)
- **Status:** EXECUTED (2026-09-16 evening) -> 0/5 usable.
- **Result:** 241 calls / 20.54M tokens / .18; all 5 non-usable tasks remained
  non-usable (2 context-length, 1 upstream 15-min deadline, 1 worker crash,
  1 completed-but-empty). Full 10-task rerun NOT triggered.
- **Artifact:** reports/LOCAGENT_P5R1_PILOT_REPORT.md;
  research/locagent-p5r1/ (evidence + sha256 manifest).
- **Revisit:** P5R-2 (provider-deviation) only if same weights with larger
  context can be established; otherwise LocAgent is treated as system-level
  context only.

## E-017 — Route B candidate-level omission recovery V1 (zero-LLM)
- **Status:** EXECUTED (2026-09-16 evening).
- **Result:** R4_Classical CIA beats Random at B=5 on DEV_TRAIN (0.148 vs 0.022,
  CI [+0.069,+0.179]) and DEV_VALIDATION (0.180 vs 0.037, CI [-0.003,+0.285]).
  No universe-size artifact (corr 0.105). Direction stable. R5_Hybrid == R4_CIA
  (identical formula: 0.5 BM25 + 0.5 graph neighbor).
- **Artifact:** reports/ROUTE_B_OMISSION_RECOVERY_V1_REPORT.md;
  research/transparency/route_b_v1_results.json; scripts/route_b_omission_recovery_v1.py.
- **Revisit:** progression gate PARTIAL PASS (direction stable, no artifact, but
  DEV_VALIDATION CI includes 0) -> a verifier pilot is NOT strongly justified
  yet; recommend a larger DEV_VALIDATION or predeclared hybrid refinement.

## E-018 — Route B V2 robustness closure
- **Status:** EXECUTED (2026-09-17).
- **Result:** CIA best predeclared arm; mean curve delta +0.118 vs analytic
  Random; 5/5 folds positive; CIs exclude zero at every B; progression gate
  PASS. Verifier pilot authorized (Block 4).
- **Artifact:** reports/ROUTE_B_V2_ROBUSTNESS_REPORT.md; route_b_v2_gates.json.
- **Revisit:** n/a (frozen ranker family; confirm on INTERNAL_TEST after full freeze).

## E-019 — Route B V2 robustness closure (overnight 2026-09-17)
- **Status:** EXECUTED; progression gate PASS.
- **Result:** CIA best arm; curve above analytic Random at every B; CIs exclude
  zero; 5/5 folds positive; no size artifact. Verifier pilot authorized + run.
- **Artifact:** reports/ROUTE_B_V2_ROBUSTNESS_REPORT.md, route_b_v2_gates.json.
- **Revisit:** confirm on INTERNAL_TEST after full freeze.

## E-020 — Verifier pilot (overnight 2026-09-17)
- **Status:** EXECUTED (30 calls, .0023; 30/30 valid).
- **Result:** Oracle-in-top-B = 1.0; verifier ORR 0.86-1.0; dominant loss =
  first-pass omission. Diagnostic only.
- **Artifact:** reports/ROUTE_B_VERIFIER_PILOT_REPORT.md.

## E-021 — History/co-change arm (overnight 2026-09-17)
- **Status:** EXECUTED (94 tasks with parent-visible history).
- **Result:** beats analytic Random; CIA remains frozen primary.
- **Artifact:** reports/ROUTE_B_HISTORY_ARM_REPORT.md.

## E-022 — Adaptive-budget exploratory (overnight 2026-09-17)
- **Status:** EXPLORATORY (not a contribution).
- **Result:** 83% of tasks reach >=90% Oracle@10 with B<5; diminishing marginal
  gain after B=3. Decision: WORTH-PURSUING AFTER FIXED ROUTE-B.
- **Artifact:** docs/ADAPTIVE_VERIFICATION_BUDGET_RESEARCH_NOTE.md.

## E-023 — Saleor case-bundle rebuild 150/150 via production-only materializer (2026-09-17)
- **Status:** EXECUTED; equivalence gate 98/98 PASS; canonical hashes identical
  to pre-portability snapshot (0 mismatch).
- **Artifact:** reports/SALEOR_PORTABILITY_FIX_AND_150_BUILD_REPORT.md.

## E-024 — Saleor sparse inference (Block C) — BLOCKED on budget
- **Status:** 1/450 smoke cell executed (succeeded, .0047, raw+sha persisted);
  full run fail-closed on budget. No Saleor predictions available -> Block D
  (Route-B replication) blocked.
- **Artifact:** reports/SALEOR_SPARSE_INFERENCE_BUDGET_BLOCKED_CLOSURE.md.

## E-025 — djangoCMS Route-B confirmatory-freeze packet (Block E)
- **Status:** COMPLETE (ready-to-approve; INTERNAL_TEST sealed). Choice B:
  ranking + actual verifier.
- **Artifact:** reports/DJANGOCMS_ROUTE_B_CONFIRMATORY_FREEZE_PACKET.md.

## E-026 — Saleor identity migration + 150/150 equivalence (2026-09-17)
- **Status:** EXECUTED (ZERO model calls). 150 bundles djangocms-rc-* ->
  saleor-rc-*; identity corrected; 150/150 scientific-payload equivalence PASS.
- **Artifact:** reports/SALEOR_IDENTITY_MIGRATION_REPORT.md.

## E-027 — Saleor clean 150x3 DEVELOPMENT sparse run (2026-09-17)
- **Status:** EXECUTED (450 cells; 446 valid / 4 failed; 7.32M tokens / .31;
  150 tasks; 0 truncations; DeepInfra). Pre-fix smoke archived as operational.
- **Artifact:** research/saleor-sparse-inference/, saleor_dev_closure.json.

## E-028 — Saleor Route-B transfer replication (2026-09-17)
- **Status:** REPLICATES (149 tasks; CIA best arm; B=5 delta +0.231 CI
  [+0.180,+0.287]; 5/5 folds; 4/4 B-points; artifact-free).
- **Artifact:** reports/SALEOR_ROUTE_B_TRANSFER_REPORT.md.

## E-029 - Ranker-identity audit: CIA ≡ Hybrid (2026-09-17)
- **Status:** COMPLETE (ZERO API; deterministic recomputation).
- **Finding:** frozen Route-B V2 arm historically labelled Classical-CIA =
  normalized BM25 + binary graph-neighbor; Hybrid (0.5 BM25 + 0.5
  graph-neighbor) is mathematically rank-equivalent (0 differing cells at
  B={1,3,5,10} on 174 djangoCMS + 149 Saleor DEV tasks; full-rank identical).
- **Artifact:** reports/ROUTE_B_RANKER_IDENTITY_AUDIT.md +
  research/transparency/route_b_ranker_identity_audit.json.

## E-030 - Incremental-evidence ablation (2026-09-17)
- **Status:** COMPLETE (ZERO API; characterization, no method change).
- **Finding:** composite−BM25 paired deltas small with CIs including zero at
  most B on both repos (djangoCMS B=5 +0.003 [−0.015,+0.019]; Saleor B=5
  +0.003 [−0.017,+0.024]); signal predominantly lexical; Saleor graph arm ≈
  binary-neighbor floor; history (djangoCMS 94 tasks) beats Random but not the
  frozen primary.
- **Artifact:** reports/ROUTE_B_INCREMENTAL_EVIDENCE_ABLATION.md +
  research/transparency/route_b_incremental_ablation.json.

## E-031 - Confirmatory freeze packet V2 + API budget freeze (2026-09-17)
- **Status:** FROZEN (ready-to-approve; INTERNAL_TEST sealed; ZERO test peek).
- **Scope:** truthful ranker name; CIA/Hybrid redundancy; Saleor=REPLICATES;
  exact repetition/failure/verifier semantics; 560 calls / ≤2.1M tokens /
  ≤.00 with per-call reservation rule.
- **Artifact:** reports/DJANGOCMS_ROUTE_B_CONFIRMATORY_FREEZE_PACKET_V2.md +
  reports/DJANGOCMS_CONFIRMATORY_API_BUDGET_FREEZE.md.

## E-032 - Proposal V1.4 (2026-09-17)
- **Status:** COMPLETE (V1.3 immutable; 7-page PDF compiled clean).
- **Change:** Saleor DEV transfer replication is a material scientific change;
  Classical-CIA terminology corrected; lexical-dominance stated.
- **Artifact:** msc_proposal/MSC_PROPOSAL_V1_4.tex/.pdf + PROPOSAL_V1_4_AUDIT.md.

## E-0XX - P2 Phase-1 adaptive-budget harness + four policies (2026-09-18)
- **Status:** EXECUTED (DEVELOPMENT; ZERO API; negative closure).
- **Result:** common harness (src/benchmark/p2/); P2-P1/P2-P2/P2-P3/P2-P4
  evaluated on djangoCMS DEV (174) + Saleor DEV (149). All four NEGATIVE
  (P2-P3 REJECTED_BY_DESIGN — size/repo artifact). Strong-method gate FALSE;
  stronger methods NOT run. Phase-2 candidates: NONE.
- **Artifact:** reports/P2_PHASE1_DECISION_GATE.md + research/p2-phase1/*.
- **Revisit:** Phase-2 candidate pool = expanded landscape (P2-025..P2-039).

## E-0XY - Fixed Route-B curve-level POST-HOC characterization (2026-09-18)
- **Status:** EXECUTED (POST-HOC; ZERO API; frozen result unchanged).
- **Result:** AURC composite 0.1553 / verifier 0.0971 / analytic random 0.0277
  (normalized); simultaneous task-bootstrap band (4000 resamples); per-task
  recovery distributions; zero-FN 10/80 (12.5%) explicit denominator handling;
  macro+micro. Frozen macro reproduced exactly (B=5 composite 0.165).
- **Artifact:** reports/ROUTE_B_CURVE_LEVEL_POSTHOC_CHARACTERIZATION.md +
  research/djangocms-confirmatory-route-b/curve_level_posthoc.json.
- **Revisit:** no (frozen confirmatory; post-hoc labelled).

## E-0XZ - Sparse-vs-Full causal parity audit (2026-09-18)
- **Status:** EXECUTED (verification of frozen configs; ZERO API).
- **Result:** PARITY_VERIFIED — all audited dimensions match; the only intended
  difference is the serialization-policy block (PROMPT_CONTROLLED_DIFF PASS
  10/10).
- **Artifact:** reports/SPARSE_FULL_CAUSAL_PARITY_AUDIT.md.
- **Revisit:** no (recorded configuration identity).

## E-040 - Independent AI-assisted semantic-plausibility audit (2026-09-18)
- **Status:** PREPARED (ZERO API; packages ready; AWAITING_RATER_OUTPUTS).
- **Idea:** an independent, fully blinded two-assistant (ChatGPT + Claude)
  semantic-plausibility audit of the 25 DEVELOPMENT packets, run in fresh
  chats, with a sealed private arm mapping, strict JSON schema, agreement
  analysis, and a human minimal-spot-check.
- **Result (preparation):** 25 cases → AI-CASE-001..025; 361 file-level rows
  (AI-ROW-0001..0361; 111 historical_changed_file + 250 omitted_candidate_file);
  5 fresh-chat batches per rater (different fixed seeds 20260919/20260920);
  leak scan clean; 15 unit tests PASS.
- **Artifact:** research/semantic_audit/ai_blinded_v1/* +
  scripts/semantic_ai_audit_{prepare,agreement,human_spotcheck}.py +
  reports/AI_SEMANTIC_AUDIT_ANALYSIS_PROTOCOL.md.
- **Revisit:** after the 10 fresh-chat runs are returned → agreement analysis
  → human spot-check. Inter-model agreement is NOT human agreement; the human
  audit remains gold.

## E-041 - AI-assisted semantic audit — agreement + post-hoc sensitivity (2026-09-18)
- **Status:** EXECUTED (ZERO API; descriptive; NOT human semantic gold).
- **Result:** 10 frozen rater outputs validated as received (chatgpt_batch_02/
  chatgpt_batch_04 syntax-only repaired — unescaped quotes in evidence strings,
  normalized copies, originals untouched, content preserved). Agreement vs
  sealed mapping: exact 0.6981 (252/361), Cohen's kappa 0.5579; abstentions
  0/0; historical-changed 0.8468 vs omitted-candidate 0.6320; case-level proxy
  0.56 / omitted-impact 0.48 / tangled 0.68. POST-HOC omitted-role partition:
  sparse_omitted_and_historical_changed (n=15, kappa 0.17) vs
  sparse_omitted_and_outside_historical_diff (n=235, kappa 0.26) — raters
  appear to interpret "omitted" as "absent from the historical diff" on the
  ambiguous 15. Descriptive top-ranked-vs-random relevance outside the
  historical diff, per rater (ChatGPT 0.193 vs 0.099; Claude 0.053 vs 0.008):
  both raters, same direction (top-ranked > random); absolute rates low;
  NOT pooled as gold. 119-row human minimal spot-check form (109 disagreements
  + 10 deterministic agreement rows seed 20260918).
- **Artifact:** reports/ai_semantic_audit_{json_validation,agreement_result,
  posthoc_result}.json, reports/AI_SEMANTIC_AUDIT_AGREEMENT_REPORT.md,
  research/semantic_audit/ai_blinded_v1/rater_outputs/,
  research/semantic_audit/ai_blinded_v1/human_spotcheck_form.csv,
  scripts/semantic_ai_audit_posthoc.py, tests/unit/test_semantic_ai_audit.py
  (19/19).
- **Revisit:** after human review of the 119-row spot-check; the human
  two-rater + adjudicator audit remains AWAITING_HUMAN_RATINGS.

## E-042 - Oracle-gap decomposition + bidirectional bounded set repair (2026-09-18)
- **Status:** EXECUTED (DEVELOPMENT; ZERO API; decision BIDIRECTIONAL_HEADROOM_ONLY).
- **Result:** confirmatory budget verified (Sparse F1 0.252; verifier B=5 F1
  0.239). DEVELOPMENT Sparse baseline djangoCMS 0.3177 / Saleor 0.2605.
  Oracle-Add ALL 0.8674 / 0.8291; Oracle-Drop ALL 0.3956 / 0.3492;
  bidirectional reaches F1 1.0; **F1=0.85 NOT add-only-reachable on Saleor**.
  Dominant bottleneck = first-pass recall (75-79% missed); Route-B add-only
  lowers file-level F1. Observable FP-pruning ~ random; heuristic BBSR fails
  the progression gate -> no verifier calls. Next = first-pass recall.
- **Artifact:** reports/ORACLE_GAP_*.md + JSONs, scripts/oracle_gap_*.py (10),
  tests/unit/test_oracle_gap.py (16/16), reports/oracle_gap_gates_validation.json.
- **Revisit:** when a first-pass-recall improvement candidate is defined on DEV.
-Append-Marker
## E-043 - First-Pass Recall Bottleneck: FN taxonomy + source ceilings + ADD queues (2026-09-18)
- **Status:** EXECUTED (DEVELOPMENT only; ZERO API; decision RECALL_SIGNAL_HEADROOM_ONLY).
- **Result:** baseline freeze reproduced frozen Route-B exactly (djangocms macro ORR
  0.0464/0.1177/0.1633/0.2512). FN taxonomy (primary): djangoCMS DIRECT_LEXICAL 95
  (24.9%), HISTORY_COCHANGE 86 (22.5%), NO_OBSERVABLE_SIGNAL 87 (22.8%),
  DOWNSTREAM_CONSUMER 64 (16.8%), INDIRECT_2HOP 43 (11.3%); Saleor DIRECT_LEXICAL
  264 (71.5%), DOWNSTREAM_CONSUMER 68 (18.4%). S006-like indirect-utility/downstream
  misses = GENERAL_PATTERN (raw consumer flag 58.9%/82.1%; direct-1hop FNs 98.6%/100%
  lexically silent). Source ceilings @K=5: GRAPH_REVERSE_1HOP ORR 0.558/0.724;
  UNION_ALL 0.725/0.870; BM25 = budget headroom 0.929/0.881. Three simple queues
  (BM25+ReverseDependency / +ProviderConsumerSupport / +ComplementaryUnion) do NOT
  beat Route-B at matched budget (B=5 deltas -0.011/+0.001, -0.025/-0.001,
  -0.086/-0.209). Oracle-reviewer F1 0.44/0.43 @B=5 vs Oracle-Add 0.72/0.64 ->
  dominant remaining loss = RANKING, not availability or reviewer acceptance.
- **Artifact:** reports/FIRST_PASS_RECALL_{BASELINE_FREEZE,FINAL_REPORT}.md,
  reports/FN_{TAXONOMY_DEVELOPMENT,SOURCE_SPECIFIC_RECALL_CEILINGS,ADD_QUEUE_EVALUATION,PROGRESSION_GATE,INDEPENDENT_AUDIT}.md
  + JSONs, src/benchmark/recall/, scripts/fn_*.py, tests/unit/test_recall_bottleneck.py (19/19),
  research/first-pass-recall-bottleneck/fn_universe.json + cochange_cache.json.
- **Revisit:** a bounded verifier-ranked expansion (Route-B top-B + reverse-1hop
  pool) on DEVELOPMENT is the natural next instrument (frozen verifier protocol);
  NOT authorized by this mission.

- **E-012 — Quantitative-structural ranking bridge (2026-09-18; T3 DEV; ZERO API):** can
  quantitative structural support order the high-coverage reverse-1hop pool better than
  the binary graph flag, without learned models/LLMs? EXACTLY three transparent formulas
  (R1 BM25+RevSupport, R2 BM25+BidirSupport, R3 BM25+BidirNorm; parent-visible features
  only; typed-edge support NOT available in the frozen graph). Result: best R1 at B=5
  djangoCMS +0.034 (0.197) but Saleor -0.020 (0.217); no formula material on BOTH repos;
  folds not majority positive; artifact-free; naive-F1 not clearly worse ->
  CHEAP_RANKING_CLOSED_FOR_NOW. Idea B (typed edges) is blocked on graph schema (untyped
  edges) and is a revisit trigger if a typed extractor lands.
- **Artifact:** reports/QUANT_STRUCTURAL_RANKING_BRIDGE_REPORT.md +
  fn_quant_ranking_bridge{,_gates,_baseline_freeze,_audit}.json,
  src/benchmark/recall/quant_rankers.py, scripts/fn_quant_ranking_bridge*.py,
  tests/unit/test_quant_ranking_bridge.py (12/12), audit 25/25.
- **Revisit:** execute the frozen Stage-4 bounded semantic pilot ONLY under explicit
  user authorization (protocol + budget draft); retest R2/R3 if typed edges become
  available.

- **E-013 — Bounded semantic expansion pilot (2026-09-18; T3 DEV; AUTHORIZED real run; 300 calls):** can a bounded semantic decision layer over the deterministic high-coverage pool (Route-B top-10 UNION reverse-1hop consumers, cap 40) convert availability headroom into realized FN recovery WITHOUT full agentic search? Arm A = frozen Route-B verifier (4 calls/task), Arm B = expanded-pool bounded rerank/verify (1 call/task). Result @B=5: djangoCMS Arm A ORR 0.111 / Arm B 0.250 (naive-F1 0.396/0.327); Saleor Arm A 0.334 / Arm B 0.357 (0.304/0.270). Preregistered gate FAIL -> BOUNDED_SEMANTIC_NEGATIVE_FROZEN (c1 saleor, c3 djangocms). Cost: 106,325 tokens / .0444 / 553.6 s. No prompt/schema tuning; 6 fail-closed schema-invalid Arm B calls.
- **Artifact:** research/bounded-semantic-expansion/ (registration freeze, results, ledger, 300 raw runs + sha256), reports/BOUNDED_SEMANTIC_EXPANSION_{PILOT_REPORT,CLOSURE_REPORT,AUDIT}.md + json, scripts/bounded_semantic_expansion_{pilot,analyze,audit}.py.
- **Revisit:** a precision-safe acceptance rule (e.g., verifier-approved AND ranked-gated) under a NEW pre-registered protocol + explicit authorization; otherwise Stage 4 stays NEGATIVE.
