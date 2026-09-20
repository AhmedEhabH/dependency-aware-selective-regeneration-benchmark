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
- **2026-09-19 addendum — probe-defect CORRECTION + determinism stop:**
  the availability probe was defective (generation catalog). Corrected probe
  (dedicated embeddings catalog) confirmed `qwen/qwen3-embedding-8b` IS
  available (DeepInfra pinned, $0.01/M; expected full-run $0.2188 < $0.50
  ceiling). The frozen determinism probe then found cosine drift ~1.0e-4 that
  **flips a file-level B=5 selection on 1/5 sampled DEVELOPMENT tasks** →
  **STOPPED BEFORE THE FULL SCIENTIFIC RUN** (P73): the bridge remains
  `QWEN3_EMBED_BRIDGE_TECHNICALLY_INCONCLUSIVE` (determinism root cause). Stage
  5 stays PAUSED/SEALED. A determinism-controllable LOCAL control
  (e.g. `BAAI/bge-m3` local inference) is the recommended next step under a
  new authorization. Human-readable consolidation + TRUE LIGHT export
  delivered (contributor report: 50 MB target unreachable without deleting
  authoritative dataset/raw evidence).
- **2026-09-20 addendum — CALIBRATED_SET_SELECTION_V1 + PARENT-ONLY REPOSITORY
  MEMORY RESCUE V2:**
  - **Stage 1-4/4b negatives all preserved.** V1 (2026-09-20) = frozen
    negative `CALIBRATED_SET_SELECTION_V1_FAIL`: one minimal calibrated
    ADD/KEEP/DROP policy (7 dense/sparse features, L2-LR, nested CV, inner-OOF
    F1 threshold, no fixed B) improves point F1 on both repos but fails the
    frozen gate on djangoCMS (Delta-F1 CI crosses zero), robustly A/B.
  - **Full-Universe V2 cancelled** = `FULL_UNIVERSE_V2_CANCELLED_AS_NON_BINDING_
    ABLATION`: V1 never selected any non-Sparse candidate beyond rank 4
    (172/93/20/3, ranks 5-20 = 0); max non-Sparse probability 0.188 @5-20 /
    0.065 @15-20 is strictly below every learned threshold (0.17-0.21) — the
    top-20 boundary was never active at the decision boundary; expanding it
    while keeping the rank-monotone signal would be a near-null rerun.
  - **V2 (2026-09-20) = frozen negative `PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL`:**
    a deterministic parent-only repository-memory generator (structural
    co-change Jaccard support≥2 + episodic BM25 over commit text) recovers
    deep dense misses at the CANDIDATE level (21.6%/27.1% of the 199/177 deep
    misses; median dense rank 62/70; better than popularity on Saleor and far
    better than random), and V2 point F1 improves over Sparse and V1 on both
    repos — but the unchanged final-set gate still fails on djangoCMS
    (Delta-F1 CI crosses zero in A and B). **Conclusion: candidate generation
    is no longer the binding constraint; the acceptance/decision layer over
    recovered candidates is.** Deep-FN coverage and dependency-cluster
    headroom are documented; graph features were NOT added to V2 (isolation of
    the history signal).
  - **Future hypotheses (documented, NOT executed):**
    `INTENT_ADAPTIVE_SELECTIVE_LOCALIZATION` (abstain/broaden when confidence
    low; risk-coverage evaluation, selective-prediction literature note);
    `PROVENANCE_BY_CONSTRUCTION` (trace links requirement→files→symbols→tests;
    supervisor-facing strategic note; `SUPERVISOR_DISCUSSION_REQUIRED_BEFORE_EXECUTION`).
  - Stage 5 stays PAUSED/SEALED (`FINAL_POLICY_NOT_FROZEN`); any V3 needs a
    NEW mission + NEW frozen hypothesis (no automatic V3).
- Stage 6 adaptive-k: gated on a stable ranking signal (P2 Phase-1 negative is
  frozen; choosing k cannot rescue a poorly ordered list).

## STAGE 5 COMPLETE — SALEOR RESERVE 300 clean untouched replication (2026-09-20)

The final planned impact-localization evaluation is COMPLETE. On a preregistered
sample of exactly 300 Saleor RESERVE tasks (seed 20260920), the frozen method
**RM-CSS** (Repository-Memory Calibrated Set Selection = SIP + Qwen dense +
parent-only Repository Memory + calibrated set selection) improved file-set F1
over **SIP** (Sparse Impact Plan): Delta F1 **+0.0921** (95% CI [+0.0691,
+0.1156]) -> SALEOR_RESERVE_300_RMCSS_PASS. A djangoCMS-DEV-only-trained
RM-CSS policy also transferred (Delta F1 +0.0742, CI [+0.0535,+0.0957]) ->
SECONDARY_CROSS_REPO_TRANSFER_PASS. Label-free parity gate 10/10 + audit
11/11; result audit 15/15; cost .619525 < .75. 786 Saleor RESERVE tasks
remain untouched. IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED permanent; no
V3. Next phase (separate authorized mission): END_TO_END_SELECTIVE_REGENERATION
(Functional Correctness, Preservation, Architecture Compliance, Efficiency).
