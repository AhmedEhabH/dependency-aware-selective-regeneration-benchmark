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
| 15 | References verified / preprints marked | `references.bib` + living review | PARTIAL — 4 entries marked "AUTHOR LIST TO BE CONFIRMED" |

## Rule
- No claim may be strengthened beyond its source.
- Any number changed by a later run requires updating this matrix and the
  proposal changelog.