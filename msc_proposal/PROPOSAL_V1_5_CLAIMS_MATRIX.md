# MSC Proposal V1.5 — Claims Matrix

**Purpose:** every factual claim in `msc_proposal/MSC_PROPOSAL_V1_5.tex` maps
to an audited evidence source. Any claim without a source is marked
`TO VERIFY`. V1.5 is a polish of V1.4; claims 1–31 are carried from the
V1.4 claims matrix (unchanged sources), and claims 32+ are new for V1.5.
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731

| # | Claim in proposal (V1.5) | Source (artifact) | Status |
|---|---|---|---|
| 1 | Full policy serializes ~144 records at 16K cap; Sparse 4.9; ~96.6% reduction | `reports/CONTROLLED_ENCODING_16K_RESULT.md` | VERIFIED (controlled, descriptive) |
| 2 | P1 real-commit: selection difficult, high FNR, no Full/Sparse superiority | `reports/REAL_COMMIT_M4A3_P1_RESULT.md` | VERIFIED (paired CIs cross zero) |
| 3 | LocAgent ~402 calls / 32.8M tokens / ~$9.93 est.; 5/10 non-usable taxonomy | `reports/LOCAGENT_P5C_HELDOUT_RUN.md` | VERIFIED (system-level context, not reproduction) |
| 4 | BM25 meaningful zero-LLM signal; K = operating-point curve | Protocol A (cheap baselines), `reports/CHEAP_BASELINES_V1_REPORT.md` | VERIFIED |
| 5 | Task-level RiskScorer not justified; v1 signal does not replicate in V2 cohort; pooled signal = universe-size artifact | `reports/OMISSION_RISK_SPARSE_V2_INFERENCE_REPORT.md`, `reports/REAL_COMMIT_V2_OMISSION_RISK_DEVELOPMENT_ANALYSIS.md` | VERIFIED |
| 6 | Genuinely classical dependency-propagation CIA baseline on 150 V2 dev cases, zero LLM (separate script from the composite) | `reports/CLASSICAL_CIA_BASELINE_V1_REPORT.md` | VERIFIED (development evidence) |
| 7 | Saleor DEV Sparse run: 150×3 = 450 cells; 446 valid / 4 failed; 7,316,986 tokens / $2.31; 0 truncations; no Saleor tuning | `research/saleor-sparse-inference/saleor_dev_run_records.jsonl` + `reports/SALEOR_ROUTE_B_TRANSFER_REPORT.md` | VERIFIED (V1.4) |
| 8 | Saleor Route-B transfer REPLICATES (DEVELOPMENT): 149 tasks; B=5 composite 0.237 vs Random 0.006; Δ+0.231 CI [+0.180,+0.287]; 5/5 folds; no size artifact; per-repository primary, no pooling headline | `reports/SALEOR_ROUTE_B_TRANSFER_REPORT.md` + `research/transparency/saleor_route_b_transfer_results.json` | VERIFIED (DEVELOPMENT transfer replication, NOT confirmatory) |
| 9 | Ranker identity: frozen "Classical-CIA" = normalized BM25 + binary graph-neighbor; Hybrid rank-equivalent; short form BM25+GraphNeighbor | `reports/ROUTE_B_RANKER_IDENTITY_AUDIT.md` + `research/transparency/route_b_ranker_identity_audit.json` | VERIFIED |
| 10 | Incremental-evidence ablation: cross-repo signal predominantly lexical (BM25); composite−BM25 deltas small, CIs include zero at most B; no graph-novelty claim | `reports/ROUTE_B_INCREMENTAL_EVIDENCE_ABLATION.md` + `research/transparency/route_b_incremental_ablation.json` | VERIFIED (characterization only) |
| 11 | djangoCMS INTERNAL_TEST confirmatory run (CONFIRMS): 80 tasks; 560 calls / 1,470,174 tokens / $0.505917; 0 failures; 0 excluded; composite ORR vs analytic Random B=1 0.059 vs 0.006, B=3 0.110 vs 0.017, B=5 0.165 vs 0.028 (Δ+0.137, CI [+0.075,+0.205]), B=10 0.267 vs 0.055; CIs exclude zero at every B; no size artifact | `reports/DJANGOCMS_ROUTE_B_CONFIRMATORY_RESULT.md` + `research/djangocms-confirmatory-route-b/confirmatory_metrics.json` + raw manifest | VERIFIED (2026-09-17; authorized INTERNAL_TEST; CONFIRMATORY) |
| 12 | Confirmatory test permanently used; never reused for P2 selection; P2 DEVELOPMENT-only; Saleor INTERNAL_TEST sealed | mission contract + `docs/P2_COMMON_EVALUATION_CONTRACT.md` | VERIFIED (governance) |
| 13 | P2 (adaptive budget) is NOT complete — development research program (Nov 2026–Mar 2027) after fixed Route-B confirmation; not a proven contribution; may close negative | `docs/ADAPTIVE_BUDGET_P2_PRE_REGISTRATION_NOTE.md`, `docs/P2_IMPLEMENTATION_ROADMAP_2026_2027.md` | VERIFIED (status statement) |
| 14 | P2 program covers Shichao-inspired algorithms + competitors/analogues from selective prediction, cascades, optimal stopping, budgeted retrieval, value-of-information, interpretable adaptive stopping | `research/literature/p2_algorithm_landscape.csv` + `docs/P2_IMPLEMENTATION_ROADMAP_2026_2027.md` | VERIFIED (24-entry landscape; Track B) |
| 15 | NestJS/NextJS/cross-language extension = future external-validity work only, April 2027, conditional on suitability gate AND TypeScript-extractor readiness | `docs/P2_IMPLEMENTATION_ROADMAP_2026_2027.md` (2027-04 row) + `reports/NESTJS…` suitability design | VERIFIED (design/status) |
| 16 | Ranking ≠ verification ≠ final localization (stage boundaries) | design definition in `sec:design`; no empirical claim | VERIFIED (definitional) |
| 17 | Related-work matrix rows: Classical/history CIA, Agentless, CodePlan, RepoCoder, LocAgent, GraphLocator, RepoGraph, This proposal — columns as in Section 5 | `references.bib` + living review `research/literature/review_matrix.csv` | VERIFIED (rows verified from primary sources) |
| 18 | RepoGraph = ICLR 2025, arXiv:2410.14684, repository-level code-graph plug-in; SWE-bench + CrossCodeEval | arXiv API lookup 2026-09-17 (primary source) + `research/literature/review_matrix.csv` (VERIFIED row) | VERIFIED (new for V1.5) |
| 19 | Abstract structure follows doctor-guide order and carries no "for the first time"/unscoped "robust"; strongest result only + one scope limitation | `ABSTRACT_REWRITE_NOTE.md` + V1.5 PDF | VERIFIED (text audit) |
| 20 | V1.5 compiles clean: 12 pages; zero overfull/underfull/undefined; 22/22 citations resolve; no uncited dump | `MSC_PROPOSAL_V1_5.log` + `references.bib` + `PROPOSAL_V1_5_AUDIT.md` | VERIFIED (compile audit) |

## Rule
- No claim may be strengthened beyond its source.
- Any number changed by a later run requires updating this matrix, the V1.5
  changelog, and the audit.
- V1.5 introduces no new scientific claim; it restructures and re-scopes the
  V1.4 claims. The strongest-claim level (fixed Route-B CONFIRMED on djangoCMS
  INTERNAL_TEST; Saleor = DEVELOPMENT transfer) is unchanged from V1.4.