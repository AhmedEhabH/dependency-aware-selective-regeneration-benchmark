# Gap-Reduction Roadmap (frozen ladder, 2026-09-18)

**Tier:** T0/T3 documentation (ZERO API; DEVELOPMENT evidence referenced).
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731

Current ladder (each stage gates the next; negatives are preserved):

| Stage | Status | Evidence | Entry condition / exit |
|---|---:|---|---|
| **Stage 1 — Sparse first pass + cheap Route-B candidate recovery** | **DONE** | Route-B V2 robustness + djangoCMS confirmatory (CONFIRMS, 2026-09-17) | cheap candidate-level recovery above analytic Random |
| **Stage 2 — FN anatomy / source availability** | **DONE** | First-pass recall bottleneck: FN taxonomy + source ceilings (reverse-1hop 0.558/0.724, UNION_ALL 0.725/0.870 @K=5) | **Finding: high structural availability, ranking bottleneck** |
| **Stage 3 — one bounded quantitative-structural ranking bridge** | **THIS MISSION (DONE)** | `reports/QUANT_STRUCTURAL_RANKING_BRIDGE_REPORT.md` | **CHEAP_RANKING_CLOSED_FOR_NOW**: no transparent count formula materially beats Route-B on both repos |
| **Stage 4 — bounded semantic rerank/verify over expanded high-coverage pool** | **DONE (AUTHORIZED PILOT; NEGATIVE)** | `reports/BOUNDED_SEMANTIC_EXPANSION_CLOSURE_REPORT.md` + `BOUNDED_SEMANTIC_EXPANSION_PILOT_REPORT.md` | **BOUNDED_SEMANTIC_NEGATIVE_FROZEN**: Arm B raises ORR but not materially on Saleor (+0.023) and materially lowers naive F1 on djangoCMS (−0.069); 300 calls, $0.0444; gate FAIL → no confirmatory |
| **Stage 4b — precision-safe acceptance feasibility + protocol freeze (THIS MISSION, 2026-09-18; ZERO API)** | **DONE (FEASIBILITY + FROZEN PROTOCOL; NOT EXECUTED)** | `reports/PRECISION_SAFE_ACCEPTANCE_FEASIBILITY_2026-09-18.md` + `reports/precision_safe_feasibility_metrics.json` + `docs/PRECISION_SAFE_ACCEPTANCE_PROTOCOL_FROZEN.md` + `reports/PRECISION_SAFE_ACCEPTANCE_BUDGET_FREEZE_DRAFT.md` | **Failure anatomy**: FP tail is an acceptance-layer failure split across BOTH pool sources; semantic ranking is the FIRST real FN-recovery instrument (dc ORR 0.111→0.250 @B5; 5/5 folds @B10 both repos); cap C=40 loses 10+29 FNs; 6/6 schema-invalid calls are non-pool-path with partial credit. **Feasibility (POST-HOC)**: the frozen verifier is too weak to serve as the acceptance layer (8.6–14% approval precision; never saw reverse-1hop-only candidates — explicit insufficiency); the RANK → VERIFY → VARIABLE-ACCEPT family is directionally supported. **One frozen next protocol**: Sparse → expanded pool (cap 80) → semantic rank (1 call) → top-K=10 inspection → strict fixed-length boolean-vector verifier (1 call) → variable accept 0..K; baseline frozen Route-B verifier; fresh disjoint sample (seed 20260919); gate c1–c7 both repos; budget draft ≤400 calls / 300k tok / $0.15 / 60 min. NOT EXECUTED — requires the exact authorization sentence |
| **Stage 5 — freeze method + fresh confirmatory test on untouched split/repository** | **IF STAGE 4b PILOT SUCCEEDS** | — | frozen method, pre-registered protocol, sealed set |
| **Stage 6 — adaptive-k / budget optimization** | **LATER** | P2 Phase-1 NEGATIVE (frozen) | revisit ONLY after ranking quality is stable (gated, not deleted) |
| **Stage 7 — generalization** | **FUTURE** | NestJS readiness (zero-API); Grafana = FUTURE polyglot candidate | Next.js/NestJS, Java/Go, one polyglot single repo (Grafana candidate, feasibility-audit first) |
| **Stage 8 — full repository-agent / expensive semantic reasoning** | **ONLY IF NEEDED** | LocAgent P5/P5C shared-protocol evidence | compare fairly with LocAgent under matched protocol |

**Revisit triggers (preserved):**
- Stage 3 rankers: revisit only with a fundamentally stronger cheap signal
  (typed edges are NOT exposed in the frozen graph; if a typed-graph
  extraction ever lands, typed-edge support becomes valid and R2/R3 should be
  retested).
- Stage 4 verifier: **closed NEGATIVE (2026-09-18, authorized pilot)**. The
  measured availability headroom (0.73/0.87) is NOT realized by this bounded
  semantic protocol; the "ORR up but F1 down" case is preserved. Revisit only
  with a precision-safe acceptance rule (e.g., verifier-approved AND
  ranked-gated) under a NEW pre-registered protocol + explicit authorization.
- Stage 4b precision-safe acceptance: **frozen protocol NOT executed
  (2026-09-18, ZERO API)**. The failure anatomy found the FP tail is an
  acceptance-layer failure (both sources) and the frozen verifier is
  uncalibrated for acceptance; the RANK → VERIFY → VARIABLE-ACCEPT family is
  directionally supported and frozen as the ONE next DEVELOPMENT pilot
  (`docs/PRECISION_SAFE_ACCEPTANCE_PROTOCOL_FROZEN.md`). Execute ONLY under the
  exact authorization sentence in
  `reports/PRECISION_SAFE_ACCEPTANCE_BUDGET_FREEZE_DRAFT.md` §7; on gate FAIL,
  freeze the negative (do NOT tune).
- Stage 6 adaptive-k: gated on a stable ranking signal (P2 Phase-1 negative is
  frozen; choosing k cannot rescue a poorly ordered list).