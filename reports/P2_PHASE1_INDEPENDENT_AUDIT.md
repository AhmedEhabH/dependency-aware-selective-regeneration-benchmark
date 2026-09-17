# P2 Phase-1 Major Science Mission — Independent Audit

**Date:** 2026-09-18
**Auditor:** independent verification pass over the P2 Phase-1 + fixed-Route-B
closure mission
**Mission:** OPENCODE_P2_PHASE1_MAJOR_SCIENCE_MISSION_2026-09-18
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731

---

## 1. Scope

- A. Fixed Route-B closure: curve-level post-hoc characterization; sparse-vs-
  full causal parity audit; dataset operational-definition audit.
- B. P2 common adaptive-budget harness + P2-P1..P4 + evaluation + decision gate.
- C. Conditional stronger methods (gate-gated).
- D. Literature landscape expansion.
- E. Semantic-audit human action report.
- F. NestJS zero-API readiness.
- G. V1.5 supervisor patch list.
- H. Validation, traceability, git, tag, LIGHT export.

## 2. Boundary (verified)

- **ZERO new model/API calls:** all P2 and closure work is deterministic
  recomputation from frozen DEV artifacts + measured cost model. The only
  network access was the arXiv API (bibliographic verification for the
  literature expansion) and `git ls-remote` of the NestJS repo (readiness
  probe) — neither is a scientific call.
- **Sealed sets untouched (verified):** djangoCMS RESERVE (59), Saleor
  INTERNAL_TEST (80), Saleor RESERVE (1086) never loaded (integration-tested).
  The opened djangoCMS INTERNAL_TEST (80) is used ONLY for the frozen
  fixed-Route-B reporting (curve-level characterization is a read-only
  recomputation of the frozen confirmatory records) — never for P2 tuning or
  selection.
- **Frozen fixed Route-B result unchanged:** the confirmatory decision
  (CONFIRMS) and all frozen numbers are untouched; the post-hoc
  characterization is explicitly labelled POST-HOC.
- **P2 negative frozen without stronger methods:** the pre-registered
  strong-method gate is False; Candidate A/B are NOT implemented (mission §4
  explicitly authorizes freezing the negative).

## 3. Deliverable audit

### A. Fixed Route-B closure — PASS
- `reports/ROUTE_B_CURVE_LEVEL_POSTHOC_CHARACTERIZATION.md` + JSON: AURC
  (composite 0.1553 / verifier 0.0971 / analytic random 0.0277, normalized),
  simultaneous task-bootstrap band (4000 resamples, frozen task unit), per-task
  recovery distributions, zero-FN count (10/80, 12.5%) with explicit
  denominator handling, macro+micro. Frozen macro (all 80 tasks) reproduces the
  frozen confirmatory numbers exactly (B=5 composite 0.165); a positive-only
  sensitivity is labelled. POST-HOC label is prominent.
- `reports/SPARSE_FULL_CAUSAL_PARITY_AUDIT.md`: **PARITY_VERIFIED** — all
  audited dimensions match (model/version, provider/route, parent snapshot/
  candidate universe, context, temperature/decoding, reasoning mode,
  completion cap, tools, repetitions); the ONLY intended treatment difference
  is the serialization-policy block, proven by the frozen
  `PROMPT_CONTROLLED_DIFF` PASS (10/10). No invented evidence.
- `reports/DATASET_OPERATIONAL_DEFINITIONS.md`: exact operational rules for
  meaningful intent, production-source eligibility, exclusions (canonical code
  set), dedup R1/R2/R3, failure/evaluable-task rules, 3-rep aggregation,
  zero-FN handling. Documentation-only; no new dataset.

### B. P2 harness + policies — PASS
- `src/benchmark/p2/` (tasks/cost_model/policies/evaluate + `__init__`);
  `scripts/p2_phase1_run.py`, `scripts/p2_phase1_gates.py`.
- Frozen constants: tau_gap 0.10 (declared), tau_marg 1.0 (25th pct of
  DEV_TRAIN top-1 scores, derived on DEV_TRAIN only), tau_energy 0.90
  (declared), cost-ratio grid {0.5,1.0,2.0} (declared sensitivity).
- Cost model: measured from 320 frozen confirmatory verifier calls
  (prompt_tokens ≈ 204.5+7.4·B; cost ≈ 0.000065+0.000005·B); used for relative
  accounting only.
- Anchor reproduction: harness fixed-B composite macro ORR matches frozen
  route_b_v2 (djangoCMS) and saleor transfer JSONs within 0.02 at every B.
- Tests: 31 new tests (15 policy unit + 10 evaluator unit + 6 integration),
  all PASS. Validation gates JSON: all PASS.

### C. P2 evaluation + decision gate — PASS (negative)
- Results per repo (djangoCMS DEV 174 / Saleor DEV 149) in
  `research/p2-phase1/results_summary.json`; per-task rows + frozen constants.
- Decision: P2-P1/P2-P2/P2-P3/P2-P4 all **NEGATIVE** (P2-P3 additionally
  REJECTED_BY_DESIGN as size/repo artifact). Strong-method gate = False.
  Phase-2 candidates: **NONE**. Saleor INTERNAL_TEST remains sealed.
- `reports/P2_PHASE1_DECISION_GATE.md`, `reports/P2_POLICY_SPECIFICATIONS.md`,
  `reports/P2_PHASE1_HARNESS_RESULTS.md`, `reports/p2_phase1_gates.json`.

### D. Literature expansion — PASS
- 15 new verified entries (P2-025..P2-039) appended to
  `research/literature/p2_algorithm_landscape.csv` (24 → 39), each classified
  with adaptation variable, cost objective, relation to B_t, and decision;
  primary sources verified via the arXiv API where accessible; classical
  works marked CLASSICAL (no arXiv). Landscape report §7 + literature decision
  ledger updated. No fabrication; verification status explicit.

### E. Semantic-audit human action — PASS (blocker recorded)
- `reports/SEMANTIC_AUDIT_ACTION_REQUIRED_FROM_HUMANS.md`; finalize script
  re-verified (PACKET_INTEGRITY PASS + SYNTHETIC_DRYRUN PASS); blocker =
  **AWAITING_HUMAN_RATINGS**. No coding time spent rebuilding ready forms.

### F. NestJS zero-API readiness — PASS (blockers listed)
- `reports/NESTJS_READINESS_ZERO_API_2026-09-18.md`: repo reachable, stable
  tags pinnable, >=60 rule frozen, TS extractor NOT implemented, no local
  cache. No inference.

### G. V1.5 supervisor patch list — PASS
- `reports/V15_SUPERVISOR_PATCH_LIST.md`; no V1.6, no PPTX.

## 4. Factual-number spot-check (independent re-derivation) — PASS
- Confirmatory frozen macro reproduced exactly in the post-hoc report
  (B=1/3/5/10 composite 0.0591/0.1098/0.165/0.2669).
- P2 harness fixed-B composite macro ORR (djangoCMS B=5 0.1633, Saleor B=5
  0.2369) matches the frozen route_b_v2 / transfer JSONs.
- P2 decision numbers: P2-P1 djangoCMS B_t 1.61 ORR 0.0775; P2-P2 B_t 8.47
  ORR 0.2389; P2-P3 tau=0.5 djangoCMS B_t 1.0 ORR 0.0464 vs Saleor B_t 9.03
  ORR 0.2918 (the size/repo artifact that justifies REJECTED_BY_DESIGN).
- Cost model: prompt_tokens(B=1)=211.9 ≈ 204.5+7.4 → matches measured mean
  211.9; B=5 → 241.5 ≈ 241.6.

## 5. Tests / static checks
- `git diff --check` PASS.
- Ruff on changed Python files: (see validation step output).
- Unit + integration tests: 31 new PASS (P2); pre-existing suite re-verified
  at the final gate.
- Mypy on changed production files (P2 package): strict.

## 6. Verdict

**PASS.** The P2 Phase-1 + fixed-Route-B closure mission executed with zero new
model calls, preserved all frozen evidence and sealed sets, delivered the
harness, evaluated the four pre-registered policies, froze an honest NEGATIVE
P2 Phase-1 result (stronger methods NOT triggered per the pre-registered
gate), expanded the literature landscape with verified sources, recorded the
human-rating blocker, and produced the required governance/export artifacts.