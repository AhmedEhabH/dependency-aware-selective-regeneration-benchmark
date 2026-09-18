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
| **Stage 5 — freeze method + fresh confirmatory test on untouched split/repository** | **IF STAGE 4 SUCCEEDS** | — | frozen method, pre-registered protocol, sealed set |
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
- Stage 6 adaptive-k: gated on a stable ranking signal (P2 Phase-1 negative is
  frozen; choosing k cannot rescue a poorly ordered list).