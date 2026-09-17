# MSC Proposal V1 — Claims Matrix

**Purpose:** every factual claim in `MSC_PROPOSAL_V1.tex` must map to an
audited evidence source. Any claim without a source is marked `TO VERIFY`.

| # | Claim in proposal | Source (artifact) | Status |
|---|---|---|---|
| 1 | Full policy serializes ~144 records at 16K cap | M1B (60 cells) `reports/…M1B` | VERIFIED (corrected metric 5.9 serialized for Sparse; Full 144) |
| 2 | Sparse reduces completion tokens ~90%, cost ~82%, latency ~63% | M1B | VERIFIED (controlled, descriptive) |
| 3 | P1 semantic selection difficult; high FNR; no Full/Sparse superiority | `reports/REAL_COMMIT_M4A3_P1_RESULT.md` | VERIFIED (paired CIs cross zero) |
| 4 | LocAgent ~402 calls / 32.8M tokens / ~$9.93 / 50% empty on 10 tasks | P5-C shared protocol | VERIFIED (system-level context, not reproduction) |
| 5 | BM25 meaningful zero-LLM signal; K = operating-point curve | Protocol A (cheap baselines) | VERIFIED |
| 6 | Sparse-v2 dev inference 90/90 valid; 490,747 tokens / $0.184; has_fn 26/30 | `reports/OMISSION_RISK_SPARSE_V2_INFERENCE_REPORT.md` | VERIFIED |
| 7 | Task-level RiskScorer not justified on 30 tasks (4 negatives) | Sparse-v2 analysis | VERIFIED |
| 8 | V2 dev inference 431/450 cells; 144 tasks; signal does not replicate; universe-size artifact | `reports/REAL_COMMIT_V2_OMISSION_RISK_DEVELOPMENT_ANALYSIS.md` | VERIFIED |
| 9 | Classical/static CIA baseline on 150 V2 dev cases, zero LLM | `reports/CLASSICAL_CIA_BASELINE_V1_REPORT.md` | VERIFIED (development evidence) |
| 10 | djangoCMS eligible pool 329; 289 untouched beyond exposed v1 40 | `reports/REAL_COMMIT_V2_SAMPLING_FRAME_AUDIT.md` | VERIFIED |
| 11 | V2 split metadata-only, seed 20260916, hashes frozen before model results | `research/transparency/v2_split_proposal.json` | VERIFIED |
| 12 | Saleor SUITABLE-WITH-DEVIATIONS; NestJS SUITABLE-WITH-DEVIATIONS | `reports/SALEOR…`, `reports/NESTJS…` | VERIFIED (design) |
| 13 | Route A / Route B pre-registered contingencies | `docs/MSC_RESEARCH_ROADMAP…`, V2 protocol | VERIFIED |
| 14 | "No positive algorithmic result is promised" | consistent with all evidence | VERIFIED |
| 15 | References verified / preprints marked | `references.bib` V1.2 + living review | VERIFIED (2026-09-16 primary-source checks; no placeholder authors) |
| 16 | Sparse mean serialized records = 4.9; Full = 144.0; reduction ~96.6% | `reports/CONTROLLED_ENCODING_16K_RESULT.md` | VERIFIED (V1.2 corrected; stale 5.9 removed) |
| 17 | LocAgent 5/10 non-usable; taxonomy = 2 timeout + 1 context-length + 2 completed-but-empty (NOT "50% empty") | `reports/LOCAGENT_P5C_HELDOUT_RUN.md` | VERIFIED (V1.2 corrected) |
| 18 | V2 inference: 431 calls; 2,501,964 tokens; 1,964-token (0.08%) post-call overshoot of nominal 2.5M ceiling; fail-closed stop (NOT "within ceiling") | V2 run_records + `reports/REAL_COMMIT_V2_OMISSION_RISK_DEVELOPMENT_ANALYSIS.md` | VERIFIED (V1.2 corrected) |
| 19 | Related-work claims verified against primary sources (arXiv/Crossref) | `references.bib` V1.2 | VERIFIED (no placeholder authors) |
| 20 | Route B progression gate: LLM verifier only if predeclared rule beats Random at B=5 on DEV_VALIDATION + same direction DEV_TRAIN + not universe artifact + no leakage | Proposal V1.2 Section 7 | VERIFIED (pre-registered) |
| 21 | Comparison matrix columns (file policy / sparse rep / cheap 1st / omission recovery / matched budget / real commit / x-repo) | Proposal V1.2 Section 7 | VERIFIED |
| 22 | Route B V2 budget curve: composite above analytic Random at every B, bootstrap CIs exclude zero | `reports/ROUTE_B_V2_ROBUSTNESS_REPORT.md` | VERIFIED (V1.3) |
| 23 | Verifier pilot: 30 calls, $0.0023, Oracle-in-top-B = 1.000, verifier ORR 0.86–1.00 | `reports/ROUTE_B_VERIFIER_PILOT_REPORT.md` | VERIFIED (V1.3) |
| 24 | Saleor clean DEV sparse run: 150×3=450 cells; 446 valid / 4 failed; 7,316,986 tokens / $2.31; 0 truncations | `research/saleor-sparse-inference/saleor_dev_run_records.jsonl` + `reports/SALEOR_ROUTE_B_TRANSFER_REPORT.md` | VERIFIED (V1.4) |
| 25 | Saleor Route-B transfer REPLICATES: 149 tasks; B=5 composite 0.237 vs Random 0.006; delta +0.231 CI [+0.180,+0.287]; 5/5 folds; no size artifact | `reports/SALEOR_ROUTE_B_TRANSFER_REPORT.md` + `research/transparency/saleor_route_b_transfer_results.json` | VERIFIED (V1.4; DEVELOPMENT transfer replication, NOT confirmatory) |
| 26 | Ranker identity: frozen "Classical-CIA" = normalized BM25 + binary graph-neighbor; Hybrid rank-equivalent (0 differing task-budget cells on 174 djangoCMS + 149 Saleor DEV tasks) | `reports/ROUTE_B_RANKER_IDENTITY_AUDIT.md` + `research/transparency/route_b_ranker_identity_audit.json` | VERIFIED (V1.4) |
| 27 | Incremental-evidence ablation: cross-repo signal predominantly lexical; composite−BM25 deltas small, CIs include zero at most B | `reports/ROUTE_B_INCREMENTAL_EVIDENCE_ABLATION.md` + `research/transparency/route_b_incremental_ablation.json` | VERIFIED (V1.4; characterization only) |
| 28 | V1.4 timeline: 2026-11→2027-10; substantive thesis/research completion 2027-07/08; 2027-09/10 = publication/revision/admin buffer | `msc_proposal/MSC_PROPOSAL_V1_4.tex` §10 (addendum; approved schedule, not a scientific claim) | VERIFIED (V1.4 print addendum) |
| 29 | V1.4 bibliography rendered in PDF: 21 verified entries, every in-text citation resolves, preprints marked | `msc_proposal/MSC_PROPOSAL_V1_4.pdf` Section 11 (BibTeX `unsrt`, `references.bib`) | VERIFIED (V1.4 print addendum) |
| 30 | djangoCMS INTERNAL_TEST confirmatory run: 80 tasks; 560 calls / 1,470,174 tokens / $0.505917; 0 failures; 0 excluded; composite ORR vs analytic Random B=1 0.059 vs 0.006, B=3 0.110 vs 0.017, B=5 0.165 vs 0.028 (Δ+0.137, CI [+0.075,+0.205]), B=10 0.267 vs 0.055; CIs exclude zero at every B; no size artifact; **CONFIRMS** | `reports/DJANGOCMS_ROUTE_B_CONFIRMATORY_RESULT.md` + `research/djangocms-confirmatory-route-b/confirmatory_metrics.json` + raw manifest | VERIFIED (2026-09-17; authorized INTERNAL_TEST; CONFIRMATORY) |
| 31 | Confirmatory test permanently used; not reused for P2 selection; P2 = DEVELOPMENT-only (djangoCMS DEV + Saleor DEV); Saleor INTERNAL_TEST sealed | mission contract + `docs/P2_COMMON_EVALUATION_CONTRACT.md` | VERIFIED (governance) |

## Rule
- No claim may be strengthened beyond its source.
- Any number changed by a later run requires updating this matrix and the
  proposal changelog.