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
