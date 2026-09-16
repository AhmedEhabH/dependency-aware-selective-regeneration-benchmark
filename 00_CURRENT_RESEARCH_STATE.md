# 00_CURRENT_RESEARCH_STATE.md

**Single authoritative current-state document — POST-ICCI closure (2026-09-15).**
**This document SUPERSEDES the historical handoffs (it does NOT delete them).**
For historical closure records see `docs/PROJECT_HANDOFF.md`, `SYSTEM_STATE.md`,
`TODO.md`, `docs/PAPER_WRITING_HANDOFF.md`, `docs/MSC_RESEARCH_ROADMAP_2026_2027.md`
(all preserved verbatim below their HISTORICAL boundaries).

**Governance (2026-09-16):** permanent hierarchy — scientific truth =
this file; execution truth = `PROGRESS.md`; decisions (append-only) =
`DECISIONS.md`. Protocol: `docs/EXECUTION_AND_VALIDATION_PROTOCOL_V2.md`
(CURRENT PHASE = **Repository change localization / impact selection**).

**Phase:** paper submitted (ICCI shorthand; repo artifact = IEEE-format V20
submission) → **FIRST POST-ICCI EXPERIMENTAL BLOCK COMPLETE AND CLOSED (Protocol A:
cheap-non-LLM baselines v1, 2026-09-16; ZERO new scientific model/API calls;
development milestone merged to main + DEV tag `cheap-baselines-v1-dev-2026-09-16`).**
→ **PLUGGABLE RESEARCH HARNESS V1 + LIVING SYSTEMATIC REVIEW V1 COMPLETE AND
AUDITED (2026-09-16; T3 reusable experiment architecture; ZERO new scientific
model/API calls; six T3 gates + independent audit PASS; Protocol-A outputs
reproduced byte-for-byte through the compatibility layer; merged to main + DEV
tag `research-harness-v1-dev-2026-09-16`).**
Post-submission window. Scientific runs remaining in this block: ZERO.

---

## 1. Submitted science — FROZEN (do not touch, do not rerun)

- Manuscript: `paper/v20-final/` (blind + supervisor TEX/PDF, `v20_body.tex`,
  `references.bib`, change log, claims matrix 43/43, reviewer-risk audit).
- Submission ZIP: `paper/v20-final/V20_FINAL_SUBMISSION.zip`
  SHA-256 `9CB5BDCCFCE8542E5A936136B60E01471FB917EF18B5B537220966421425E138`
  (10 entries, sidecar verified).
- Science candidate commit `42755df0cb53a60be1c8a2a3c3322d34ef3d8155`;
  submission archive commit `0a5928ce615340262ca3697615eee55fb8847ed6`;
  corrected main base `884ba7982f283b2e78c48d768d34f2f5a726a862`.
- Conference paper/submission ID and submission timestamp: **NOT recorded in
  the repo** (truthful: nothing to report; never fabricated).
- Full per-file hashes: `paper/v20-final/ICCI_SUBMISSION_RECORD_2026-09-15.json`.

## 2. Completed evidence (all audited / frozen)

| Study | Status | Where |
|---|---|---|
| Selection-stage benchmark (Todo + djangoCMS, 60-cell Stage-C) | CLOSED / AUDITED | `reports/`, tag `v0.11.0-benchmark-complete` |
| ImpactPlan-v2 post-hoc/exploratory (30 cells) | COMPLETE / AUDITED | `reports/scientific-stagec-djangocms-impactplan-v2-01/` |
| M1A controlled 4096-cap feasibility boundary | COMPLETE / AUDITED | `reports/CONTROLLED_ENCODING_4096_FEASIBILITY_RESULT.md` |
| M1B controlled 16K cap-relaxed ablation | COMPLETE / AUDITED | `reports/CONTROLLED_ENCODING_16K_RESULT.md` |
| M1 defensive closure (threat matrix, n=6 scenario stats) | COMPLETE | `reports/M1_*` |
| M3 graph ablation C0/C1/C2 (90 cells, development-set) | COMPLETE / AUDITED | `reports/M3_GRAPH_*`; hints MIXED, gated disclosure NOT PROMISING |
| M4A-1 RealCommitImpactDataset-v1 miner + 6 MINER_DEV | COMPLETE / AUDITED | `reports/REAL_COMMIT_M4A1_*`; ZERO API |
| M4A-2 scientific corpus (40 cases) + split freeze | COMPLETE / AUDITED | `reports/REAL_COMMIT_M4A2_*`; ZERO API |
| M4A-3/P1 real held-out evaluation (60/60 cells) | EXECUTED (2026-09-14) | `research/real-commit-p1-01/`, `reports/REAL_COMMIT_M4A3_P1_*` |
| P5 LocAgent shared-protocol comparison (P5-A/B/C) | COMPLETE (2026-09-15) + C1–C7 reporting corrections | `reports/LOCAGENT_P5C_*`, `research/locagent-p5b/` |

## 3. Exact tags / SHAs (authoritative)

- `v0.11.0-benchmark-complete` — benchmark closed + audited (NOT end-to-end
  executor success).
- `v0.11.1-p1-serialization-docs-model-refactor`, `v0.11.2-p5-locagent-shared-comparison`,
  `v0.11.3-p5-reporting-corrections` @ `884ba79…`.
- `cheap-baselines-v1-dev-2026-09-16` — Protocol A cheap non-LLM baselines v1
  DEV evidence tag @ commit `541c8ba…` (tag object `4b96049…`; audited
  DEVELOPMENT evidence, NOT confirmatory; NOT a stable-tag move).
- `research-harness-v1-dev-2026-09-16` — pluggable research harness V1 + living
  systematic review V1 DEV evidence tag (audited DEVELOPMENT/architecture
  evidence; NOT a stable-tag move).
- Study tags: `real-commit-p1-full-v2-vs-sparse-v2-01-audited`,
  `real-commit-impact-dataset-v1-corpus-audited`,
  `real-commit-impact-dataset-v1-m4a1-closure-audited`,
  `graph-c0-c1-c2-01-study-01-audited`,
  `controlled-encoding-ablation-16k-study-01-audited`, etc.
- P1 frozen protocol `real-commit-p1-v1.0.0`; P1 model `qwen/qwen3-coder`
  (Qwen3-Coder-480B-A35B-Instruct) @ `deepinfra/turbo`; temp 0; cap 16384; Graph OFF.
- LocAgent pinned upstream commit `4935b557326c154bad8e8dcf3747cc8d32d1f387`.

## 4. Datasets / splits (frozen, ZERO-API)

- `benchmark_data/real_commit_impact_v1/`: **40 scientific djangoCMS cases** +
  6 MINER_DEV cases.
- Split freeze (seed `20260913`, metadata-only, pre-model): **TRAIN 24 /
  VALIDATION 6 / HELD_OUT_TEST 10** (`split_freeze.json`,
  `scientific_manifest.json`).
- Gold = **OBSERVED CHANGE-SET PROXY** (evaluation-only), never semantic
  ground truth.

## 5. Exposed test sets — PERMANENT (do not tune)

- **The 10 HELD_OUT_TEST tasks are PERMANENTLY EXPOSED** (P1 M4A-3/P1 ran
  Full-v2 and Sparse-v2 with 3 nested reps; P5-C ran LocAgent 10/10). They are
  used for reporting/audit only.
- **DO NOT TUNE any new method on these 10 tasks.** Any tuned-threshold /
  selected-feature / escalation-policy decision must be made on
  TRAIN/VALIDATION (or MINER_DEV) and confirmed on a FRESH held-out split
  that has never been used for any selection decision.
- **DO NOT CALL-CONFIRMATORY on the exposed 10** to "check" a new method:
  repeated confirmatory inference on the same exposed split is confirmatory
  bias. Fresh confirmatory protocol = new repository OR new non-exposed split.

## 6. Current threats (active, from `reports/M1_THREATS_TO_VALIDITY_MATRIX.md`)

1. HELD_OUT_TEST exposure (now permanent — mitigation: fresh split required).
2. Survivor-conditioned LocAgent metrics must never be reported as headline.
3. Change-set proxy is an observed diff, not semantic ground truth.
4. Single-repository, single-model selection evidence (djangoCMS;
   Qwen3-Coder-480B-A35B-Instruct).
5. LocAgent provider route is OpenRouter-routed (backend not pinned per call);
   cost $9.9288 is a NORMALIZED estimate, not provider-billed.
6. No arm-superiority claim from P1: paired ΔF1 CIs cross zero.
7. Selective escalation is NOT validated — proposal only.

## 7. Current numbers (frozen, recomputed 2026-09-15, ZERO API)

### P1 (10 tasks × 2 arms × 3 reps = 60 cells; 60/60 valid; 566,755 tokens; $0.36)
- Full-v2 micro: P 0.3388 / R 0.3694 / F1 0.3534 / FNR 0.6306.
- Sparse-v2 micro: P 0.3867 / R 0.2613 / F1 0.3118 / FNR 0.7387.
- Paired bootstrap over 10 tasks: ΔF1 −0.0088 [−0.1297, +0.1189] (crosses zero);
  Δcost −$0.0235 [−0.0244, −0.0228] (cost effect supported, descriptive).

### Cheapest-baseline block (Protocol A, 2026-09-16, ZERO API, DEVELOPMENT evidence — CLOSED + DEV tag)
- B0 Random@K ≈ floor (pooled F1 0.012–0.021 across K).
- B1 BM25@K strongest cheap lexical: **VALIDATION is the primary
  development-decision table** — BM25@3 P 0.333/R 0.240/F1 **0.279** (precision
  operating point); BM25@10 P 0.217/R 0.520/F1 **0.306**/FNR 0.480 (recall
  operating point, highest VALIDATION F1). **K is an operating-point curve, NOT
  a final configuration.**
- B2 path_token@K / B3 Graph@K ≈ 0.18–0.19 pooled F1 @K=3 (graph ≈ path_token;
  Graph@K seeds are lexical/path-token-derived → this shows the cheap
  lexical-seeded expansion adds little over the seed signal, NOT that graph
  reasoning is generally unhelpful).
- B4 Hybrid@K ≈ BM25@K (pooled F1 0.258 @K=3; frozen 0.5/0.5 fusion does not
  materially improve over BM25 → motivates bounded/selective graph verification,
  not score fusion).
- **Fair-comparison caveat (safe wording):** BM25 provides a meaningful
  zero-LLM localization signal on development data; whether it matches or
  underperforms the LLM planners remains untested under a shared fresh
  confirmatory protocol. Full-v2 F1 0.353 / Sparse-v2 F1 0.312 (exposed
  HELD_OUT) are directional context only, never a head-to-head ranking.
- Efficiency: BM25 wall ≈ 403 s dominated by parent git-archive
  materialization (snapshot/index-build cost), queries ~1.3 s total (not
  "403-second inference"); path_token/graph < 2 s; **0 LLM calls, 0 tokens**.
- **Path-mention sensitivity (ZERO API, diagnostic):** excluding the 3 TRAIN
  cases whose full intent mentions a changed path, path-clean BM25@3 F1
  0.283 → 0.262 (TRAIN) and 0.282 → 0.267 (pooled); material qualitative
  ordering unchanged. `research/cheap-baselines-v1/path_mention_sensitivity_v1.json`.
- Artifacts: `research/cheap-baselines-v1/`; six gates + audit PASS
  (`reports/CHEAP_BASELINES_V1_REPORT.md`, `_AUDIT.md`); merged to `main`;
  tag `cheap-baselines-v1-dev-2026-09-16` = audited DEVELOPMENT evidence,
  NOT confirmatory.

### P5 LocAgent (10 tasks × 1 exec; 402 calls; 32.8M tokens; $9.9288 est.)
- **Headline (A, fail-closed all-10):** TP 10 / FP 13 / FN 27 → P 0.4348 /
  R 0.2703 / F1 0.3333 / FNR 0.7297.
- **Diagnostic (B, usable-5, survivor-conditioned — NOT headline):** micro
  P 0.4348 / R 0.4000 / F1 0.4167 / FNR 0.6000; macro P 0.6909 / R 0.6033 /
  F1 0.6370 / FNR 0.3967.
- Failure taxonomy: **2 timeout / 1 context-length BadRequest / 2
  completed-but-empty** (NOT "5 timeouts").
- Official native Acc@K: Acc@1 4/10, Acc@3 4/10, Acc@5 2/10 (the old 8/10,
  9/10 were item-hit sums — corrected).
- Source: `research/locagent-p5b/locagent_two_way.json` +
  `reports/LOCAGENT_P5C_SHARED_COMPARISON.md`.

### Four-action FN breakdown (existing P1 raw outputs; secondary diagnostic)
- Full-v2 FN 70: PRESERVE 70 / VALIDATE 0 / HUMAN_REVIEW 0.
- Sparse-v2 FN 82: PRESERVE 74 / VALIDATE 8 / HUMAN_REVIEW 0.
- Both arms: PRESERVE 144 / VALIDATE 8 / HUMAN_REVIEW 0 (REGENERATE excluded
  by construction). See
  `research/post-icci-zero-api-closure/four_action_fn_breakdown.{json,csv}`.

### Harness V1 + living systematic review V1 (2026-09-16; T3 architecture; ZERO API — CLOSED + DEV tag)
- Reusable experiment harness `src/benchmark/harness/` with seams:
  DatasetAdapter, SnapshotProvider/RepositoryView, Ranker, Planner,
  ModelBackend, RiskScorer (interface only), Verifier (interface only),
  BudgetPolicy, common Evaluator, versioned ExperimentSpec. Config-driven name
  registry; django rules in a django adapter; future Saleor rules in a
  fail-closed Saleor adapter; model/provider names are config; budget explicit
  and persisted.
- **Protocol-A compatibility layer reproduces the frozen cheap-baseline outputs
  byte-for-byte**: full equivalence run 30 cases × 5 methods × 4 K = 600 rows
  scientific projection + per_task + aggregates identical to
  `research/cheap-baselines-v1/*.json`
  (evidence `research/harness-protocol-a-equivalence/raw_predictions_via_harness_v1.json`).
- Living review: `docs/LIVING_SYSTEMATIC_REVIEW.md`,
  `research/literature/review_matrix.csv` (12 seeded systems; only LocAgent
  VERIFIED with direct evidence; all others SEEDED — verify primary source),
  `research/literature/search_log.csv`, `research/literature/idea_ledger.md`
  (ideas I1–I7 with TEST/WATCH/BOUNDARY dispositions).
- Validation: six T3 gates + independent audit PASS
  (`reports/RESEARCH_HARNESS_V1_REPORT.md`, `_AUDIT.md`,
  `reports/research_harness_v1_gates.json`); 44 new tests; full suite 3270
  passed / 33 skipped / 2 pre-existing environmental failures (missing pinned
  djangocms repo checkout; identical on clean base).
- **ONE next scientific step: OMISSION_RISK_FEATURE_STUDY_V1 (TRAIN/VALIDATION
  only). NOT STARTED here.**

## 8. Next experiment — ONLY ONE (not started, not authorized without review)

**Protocol A (cheap non-LLM baselines v1) is COMPLETE AND CLOSED (2026-09-16;
TRAIN 24 + VALIDATION 6; ZERO API; six gates + audit PASS; merged to main; DEV
tag `cheap-baselines-v1-dev-2026-09-16`).**

**PLUGGABLE RESEARCH HARNESS V1 + LIVING SYSTEMATIC REVIEW V1 are COMPLETE AND
AUDITED (2026-09-16; T3 reusable experiment architecture; ZERO API; six T3
gates + audit PASS; Protocol-A outputs reproduced byte-for-byte through the
compatibility layer — 30 cases × 5 methods × 4 K = 600 rows + aggregates;
merged to main; DEV tag `research-harness-v1-dev-2026-09-16`).** The next
scientific step is chosen after Ahmed reviews the closure — **STATED**:
- primary next line (drafted, NOT executed): **Selective escalation for
  cost-aware repository change localization** (the proposal topic),
  pre-ceded by the **omission-risk detection** core mechanism
  (`docs/OMISSION_RISK_DETECTION_PROTOCOL_DRAFT.md`) — evaluated on TRAIN/
  VALIDATION, then a FRESH confirmatory split. The ONE next scientific step is
  **OMISSION_RISK_FEATURE_STUDY_V1 (TRAIN/VALIDATION only)** — feature families
  and routing metrics per `reports/RESEARCH_HARNESS_V1_REPORT.md` §9.
- Saleor remains the second-repository confirmatory line, DOCUMENT-ONLY for now
  (`docs/SALEOR_CONFIRMATORY_PROTOCOL_DRAFT.md`).

Sequence per the MSc roadmap:
`Sparse first pass → omission-risk detection → selective graph-guided escalation
→ bounded false-negative verification`.

Do NOT automatically begin: Saleor scientific execution, risk-detector
training, selective escalation, faithful LocAgent inference, new LLM calls, or
new model-family runs.

## 9. DO-NOT warnings (operational)

- **DO-NOT-TUNE** on the exposed HELD_OUT_TEST ten.
- **DO-NOT-CALL-CONFIRMATORY** on the exposed ten.
- **DO-NOT** claim selective escalation has been validated.
- **DO-NOT** run Saleor / LocBench / new LocAgent inference / new model
  matrices without a fresh preregistration + frozen budget.
- **DO-NOT** alter frozen P1/P5 outputs; all post-ICCI analyses are
  read-only recomputations from existing evidence.