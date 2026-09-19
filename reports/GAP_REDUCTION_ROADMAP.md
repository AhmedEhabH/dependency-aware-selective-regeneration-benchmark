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
| **Stage 4b EXECUTION — precision-safe acceptance pilot (AUTHORIZED, 2026-09-18)** | **DONE (AUTHORIZED PILOT; NEGATIVE)** | `reports/PRECISION_SAFE_ACCEPTANCE_CLOSURE_REPORT.md` + `PRECISION_SAFE_ACCEPTANCE_PILOT_REPORT.md` + `research/precision-safe-acceptance-pilot/` | **PRECISION_SAFE_ACCEPTANCE_FAIL**: 357 dispatched calls (240 Arm A + 60 rank + 57 verify), 176,060 tokens, $0.0648, 655.7 s; 0/357 schema-invalid; @B=5 djangoCMS ORR 0.223→0.152 (−0.070, c1 FAIL, 2/5 folds c2 FAIL) and Saleor ORR 0.128→0.203 (+0.075, PASS); F1 + candidate precision improve on BOTH repos (Stage-4 "ORR up, F1 down" eliminated); gate FAIL → negative frozen, no tuning |
| **Stage 5 — freeze method + fresh confirmatory test on untouched split/repository** | **IF A FUTURE 4b PILOT SUCCEEDS** | — | frozen method, pre-registered protocol, sealed set |
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
- Stage 4b precision-safe acceptance: **EXECUTED and FAILED its preregistered
  gate (authorized pilot, 2026-09-18) → `PRECISION_SAFE_ACCEPTANCE_FAIL`,
  negative frozen** (see the Stage 4b EXECUTION row above: 357 dispatched
  calls, 176,060 tokens, $0.0648; djangoCMS c1 ORR −0.0702 and c2 folds 2/5
  FAIL; Saleor c1/c2 PASS; F1 + candidate precision improve on BOTH repos).
  The pre-execution feasibility stage (ZERO API) found the FP tail is an
  acceptance-layer failure (both sources) and the frozen verifier is
  uncalibrated for acceptance; the RANK → VERIFY → VARIABLE-ACCEPT family is
  directionally supported by the F1/precision gains. The frozen protocol
  (`docs/PRECISION_SAFE_ACCEPTANCE_PROTOCOL_FROZEN.md`) was executed under the
  exact authorization sentence in
  `reports/PRECISION_SAFE_ACCEPTANCE_BUDGET_FREEZE_DRAFT.md` §7; the gate FAILED
  on djangoCMS and the negative is frozen — no tuning. A descriptive statistical
  closure (POST-HOC, task-paired bootstrap) is recorded separately in
  `reports/STAGE4B_STATISTICAL_CLOSURE_2026-09-19.md` and does NOT alter the
  preregistered verdict. Any future instrument that keeps the precision/F1
  gains while restoring djangoCMS ORR is a NEW protocol requiring its own
  freeze + authorization.
- **2026-09-19 addendum — statistical closure + new signal family:**
  - Stage-4b descriptive closure (task-paired bootstrap, 10,000 resamples,
    fixed seed) reproduces the frozen point estimates exactly and explains the
    djangoCMS ORR-down/F1-up phenomenon (macro-vs-pooled weighting + verifier
    over-rejecting three M=1 recoveries). The preregistered verdict is
    UNCHANGED.
  - `BOUNDED_CHEAP_SEMANTIC_CLOSED_FOR_NOW` (P68): the bounded generic-Qwen
    prompt/verifier/threshold family is closed FOR NOW on the tested DEV
    evidence (narrowly scoped).
  - **NEW external diagnostic baseline (NOT part of the ladder):**
    `Salesforce/SweRankEmbed-Small` evaluated on the FULL DEV populations
    (djangocms 174 + saleor 149) under a frozen protocol →
    **`SWERANK_EMBED_PASS`** (every metric improves at every B on both repos;
    all paired-bootstrap CIs @B=5 exclude zero; 0 API calls / $0). Labeled
    EXTERNAL PRETRAINED DIAGNOSTIC BASELINE (SweLoc provenance verdict C).
    Method frozen as the candidate-ranking signal; confirmatory (Stage 5) or a
    budgeted SweRankLLM reranker each require a NEW protocol + authorization.
- **2026-09-19 addendum — contamination-robustness bridge (scope change):**
  Stage-5 confirmatory execution is **PAUSED** pending a DEVELOPMENT-only
  contamination-robustness bridge that tests whether the SweRank DEV gain is a
  general dense-retrieval mechanism. The bridge was **STOPPED BEFORE CALL 1**
  (`qwen/qwen3-embedding-8b` unavailable on OpenRouter — 0 embedding models;
  full-population cost projection exceeds the frozen $0.50 ceiling) →
  **`QWEN3_EMBED_BRIDGE_TECHNICALLY_INCONCLUSIVE`**; 0 calls / $0. Provenance
  audit V2 keeps verdict C (django-cms rank 11,118 in the 2026-09 top-PyPI
  dump, outside the top-11k SweLoc cutoff; saleor absent from top-15k; no
  released SweLoc manifest). **Stage-5 decision:
  `STAGE5_REMAINS_BLOCKED_BY_PROVENANCE_OR_NONREPLICATION`** — confirmatory
  stays sealed. Recommended alternative control (NOT executed): local
  `BAAI/bge-m3` under a new freeze + authorization.
- Stage 6 adaptive-k: gated on a stable ranking signal (P2 Phase-1 negative is
  frozen; choosing k cannot rescue a poorly ordered list).