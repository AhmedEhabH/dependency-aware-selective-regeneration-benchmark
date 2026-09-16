# DECISIONS.md — Append-Only Decision Record

**Role:** Append-only record of implementation/research decisions made during
execution. Entries are never edited after append; corrections are new entries.

---

## Decision P1 — Governance hierarchy (2026-09-15)

- **Status:** ADOPTED (permanent)
- **Context:** Post-ICCI experimental block start; ambiguity between
  `00_CURRENT_RESEARCH_STATE.md`, `SYSTEM_STATE.md`, `TODO.md` as sources of truth.
- **Decision:** Permanent hierarchy:
  1. `00_CURRENT_RESEARCH_STATE.md` = scientific source of truth (frozen
     evidence, datasets/splits, exposed test sets, tags/SHAs, supported claims,
     research direction);
  2. `PROGRESS.md` = execution source of truth (current execution, last task,
     next step, blockers);
  3. `DECISIONS.md` = append-only decision record.
  No new competing current-state handoff will be created.
- **Rationale:** One scientific truth + one execution truth + append-only
  decisions; avoids handoff drift.
- **Impact:** All future state updates target exactly these three files.

## Decision P2 — Protocol CURRENT PHASE (2026-09-15)

- **Status:** ADOPTED
- **Context:** Execution & Validation Protocol v2 must name the current phase.
- **Decision:** CURRENT PHASE = **Repository change localization / impact
  selection**. Evaluation dimensions for this phase:
  - PRIMARY: 1. Impact Correctness (Precision, Recall, F1, FNR); 2. Efficiency
    (runtime, computational cost, retrieval/query cost; LLM calls/tokens/cost
    only when an LLM is actually used).
  - CONDITIONAL: 3. Architecture / protocol compliance.
  - DEFERRED (until downstream code regeneration): 4. Functional Correctness;
    5. Preservation / regression correctness.
- **Rationale:** Localization-only experiments must not be forced to claim
  downstream-regeneration dimensions.
- **Impact:** Baselines and future localization work report only applicable
  dimensions.

## Decision P3 — Protocol A scope (2026-09-15)

- **Status:** ADOPTED (this task)
- **Context:** Executing the only scientific experiment of this block.
- **Decision:** Implement B0 Random@K (seeded), B1 BM25@K, B2 path/identifier
  token@K, B3 Graph@K (frozen per-case parent-only dependency graph, seed =
  intent-term hits against candidate metadata; if no defensible seed exists,
  stop and document), B4 Hybrid@K (frozen pre-validation combination rule).
  Evaluate K in {1,3,5,10}. TRAIN 24 + VALIDATION 6 only; HELD_OUT_TEST 10 is
  PERMANENTLY EXCLUDED from all tuning/selection.
- **Rationale:** Zero-LLM-cost baseline family; matched K; matched-cardinality
  view kept separate if scientifically useful.
- **Impact:** Smallest defensible baseline family; zero API cost.

## Decision P4 — STRICT DATA RULE (2026-09-15)

- **Status:** ADOPTED (permanent)
- **Context:** The 10 HELD_OUT_TEST tasks are permanently exposed (P1 M4A-3 +
  P5 ran them).
- **Decision:** Use ONLY TRAIN (24) + VALIDATION (6). Never use HELD_OUT_TEST
  for tuning, threshold selection, method choice, K selection, feature design,
  or error-driven revisions. Report any aggregate on TRAIN/VALIDATION as
  development evidence only (not confirmatory/generalizable).
- **Rationale:** Exposed test set must not inform any new-method decision.
- **Impact:** Violations are audited fail-closed.

## Decision P5 — Frozen P1/P5 evidence immutability (2026-09-15)

- **Status:** ADOPTED (permanent)
- **Context:** Post-ICCI experimental block.
- **Decision:** Do NOT rerun or modify frozen ICCI/P1/P5 scientific evidence.
  All baseline analysis is run-fresh on TRAIN/VALIDATION; no frozen run_records
  are altered.
- **Rationale:** Immutable submitted science.
- **Impact:** Baseline output dirs are new; existing evidence untouched.

## Decision P6 — Frozen-corpus path-mention caveat classification (2026-09-16)

- **Status:** ADOPTED (documented, not a pipeline defect)
- **Context:** Gate2 flagged 6 frozen cases whose full-message public intent
  literally contains a changed path while the recorded
  `intent_mentions_changed_path` flag is False (M4A-2 leak detector ran on the
  short subject; persisted intent is the full message).
- **Decision:** Classify as a **frozen-corpus property** shared identically by
  the P1 LLM planner and the baselines (same public query). Do NOT modify the
  frozen corpus; record the 3 TRAIN cases
  (`djangocms-rc-2efae8e43bd6`, `ada585d3f358`, `5ff38b521274`) as a caveat in
  gates/audit/report, and treat it as a data-construction lesson for the
  future Saleor minining (test the SAME string that is persisted).
- **Rationale:** The baselines receive no new exposure beyond the public input
  the planner also sees; altering frozen data would corrupt frozen evidence.
- **Impact:** Gate2/audit now pass with the caveat recorded; no result change.

## Decision P7 — Protocol A frozen configuration (2026-09-16)

- **Status:** ADOPTED (frozen before validation)
- **Decision:** K ∈ {1,3,5,10}; seed rule = intent-token ∩ candidate-token;
  Hybrid = 0.5·Nm(BM25) + 0.5·Ng(graph) with seedless→pure-BM25; tie-break by
  (-score, path); BM25 k1=1.5, b=0.75; frozen stopword set; per-case random
  seed `20260915:case_id`. No threshold/method/K change allowed from validation
  results.
- **Rationale:** smallest defensible baseline family, preregistered.
- **Impact:** freeze point for the cheap-baseline arm of the MSc proposal
  (pending Ahmed's review).

## Decision P8 — Matched-cardinality view NOT reported (2026-09-16)

- **Status:** ADOPTED
- **Context:** The prompt allows a separate matched-cardinality view "if
  scientifically useful".
- **Decision:** Do not report a matched-cardinality view: Full/Sparse predicted
  write-set sizes exist only on the exposed HELD_OUT_TEST ten, and matching K to
  the observed proxy cardinality would leak the reference into the method.
  Fixed-K tables are the honest default.
- **Rationale:** preserving the strict data rule and the exposed split.
- **Impact:** documented in `reports/CHEAP_BASELINES_V1_REPORT.md` §7.

## Decision P9 — No milestone tag on development evidence (2026-09-16)

- **Status:** ADOPTED
- **Context:** Prompt L.9 allows a milestone/evidence tag "if and only if the
  result is fully audited and worth freezing".
- **Decision:** Do NOT create a tag yet. Protocol A is TRAIN/VALIDATION
  development evidence (not confirmatory); the frozen-candidate-method decision
  belongs to Ahmed after review. Evidence tags for dev evidence would invite
  over-claiming. Revisit only after review and/or the fresh confirmatory step.
- **Rationale:** statistical discipline (H) + truthful status.
- **Impact:** commit `3b83dd6` on branch
  `research/cheap-nonllm-baselines-v1`; tag deferred.

## Decision P10 — Protocol A finalization: interpretative corrections + DEV tag (2026-09-16, SUPERSEDES P9)

- **Status:** ADOPTED — SUPERSEDES P9
- **Context:** P9 deferred a tag pending review. Supervisor review of the
  Protocol-A block concluded the block is a meaningful, fully audited
  DEVELOPMENT milestone and requested a detailed closure: (1) an
  over-strong comparison statement in the report must be corrected; (2) K
  must not be presented as a final configuration; (3) a path-mention
  sensitivity diagnostic must be added; (4) graph/hybrid/efficiency
  interpretations must be bounded; and (5) the block may carry a descriptive
  **DEV** tag after merge to main.
- **Decision:**
  1. **Replace** the claim "BM25 is far below / does not materially challenge
     the LLM planner" with the safe wording: **"BM25 provides a meaningful
     zero-LLM localization signal on development data. Whether it matches or
     underperforms the LLM planners remains untested under a shared fresh
     confirmatory protocol."** P1 Full/Sparse F1 numbers may appear only as
     clearly labeled directional context (different exposed HELD_OUT split),
     never as a head-to-head ranking.
  2. **Do not claim K=3 or K=5 is the final BM25 configuration.** Present
     TRAIN and VALIDATION separately; the VALIDATION table is the primary
     development-decision table. BM25@3 = low-cardinality / precision-oriented
     operating point; BM25@10 = recall/FNR-oriented operating point with the
     highest validation F1 (0.3059) in the current 6-task set. K is an
     operating-point curve, not a confirmatory conclusion; no pooled
     TRAIN+VALIDATION K-selection without explicit justification.
  3. **Sensitivity diagnostic (ZERO API):** the 3 TRAIN path-mention cases
     (`djangocms-rc-2efae8e43bd6`, `ada585d3f358`, `5ff38b521274`) are
     excluded in a deterministic recomputation over persisted per-task metrics
     (`scripts/sensitivity_cheap_baselines_path_mentions.py`,
     `research/cheap-baselines-v1/path_mention_sensitivity_v1.json`).
     Path-clean BM25@3 F1 0.283 → 0.262 (TRAIN) and 0.282 → 0.267 (pooled);
     the **material qualitative ordering is unchanged**. Diagnostic only; the
     frozen dataset is NOT modified.
  4. **Graph interpretation:** Graph@K uses lexical/path-token-derived seeds;
     Graph≈Path shows the cheap lexical-seeded expansion adds little over the
     seed signal, NOT that graph reasoning is generally unhelpful. No general
     negative graph result.
  5. **Hybrid interpretation:** the frozen 0.5/0.5 hybrid does not materially
     improve over BM25; no alpha tuning now; motivates bounded/selective graph
     verification rather than score fusion.
  6. **Efficiency interpretation:** the ~403 s BM25 wall time is dominated by
     parent git-archive materialization (snapshot/index-build cost), while
     query/ranking latency is ~1.3 s total. BM25 is not "403-second
     inference"; caching/pre-indexing is an engineering optimization, not a
     new scientific result.
- **Tag decision (supersedes P9):** create exactly one descriptive
  development-evidence tag **`cheap-baselines-v1-dev-2026-09-16`** after the
  block is merged to main and re-audited. The tag means **audited DEVELOPMENT
  evidence, NOT confirmatory evidence**. It does NOT move any stable tag and
  does NOT claim confirmatory/generalizable status.
- **Rationale:** development evidence is allowed an immutable tag when the tag
  explicitly says DEV; the interpretation corrections keep the record truthful
  and prevent over-claiming while allowing the audited block to be frozen.
- **Impact:** report rewritten (`reports/CHEAP_BASELINES_V1_REPORT.md`),
  protocol milestone-format section added
  (`docs/EXECUTION_AND_VALIDATION_PROTOCOL_V2.md` §9.2), sensitivity
  diagnostic + tests added, docs synchronized, branch merged into `main`,
  tag `cheap-baselines-v1-dev-2026-09-16` created and pushed, light export
  recreated after merge/tag.
- **Tag → exact commit:** `cheap-baselines-v1-dev-2026-09-16` (tag object
  `4b96049…`) peels to commit `541c8ba…` == `main` == `origin/main` (created
  2026-09-16 after merge; audited DEVELOPMENT evidence only).
## Decision P11 — Pluggable research harness V1 (2026-09-16)

- **Status:** ADOPTED (this task; T3 reusable experiment architecture)
- **Context:** Post-ICCI + cheap-baselines block closed; the research harness
  was hard-coded in places to one repository (djangoCMS), one model route, one
  selection method, one K grid.
- **Decision:** Generalize the harness minimally through explicit seams
  (DatasetAdapter, SnapshotProvider/RepositoryView, Ranker, Planner,
  ModelBackend, RiskScorer [interface only], Verifier [interface only],
  BudgetPolicy, common Evaluator, versioned ExperimentSpec) in the new package
  src/benchmark/harness/. Do NOT build a universal plugin framework; use
  Python ABC + config. django-specific rules live in the django adapter; future
  Saleor rules in a Saleor adapter (fail-closed seam). Model/provider names are
  configuration, never algorithm branches. Budget is explicit and persisted in
  the ExperimentSpec. Frozen historical generators/artifacts are NOT rewritten
  — the harness adapts them (compatibility layer reproduces Protocol-A outputs
  byte-for-byte).
- **Rationale:** minimal generalization, preservation of frozen evidence,
  preparation for the Omission-Risk Feature Study v1 without touching frozen
  machinery.
- **Impact:** src/benchmark/harness/, gate/equivalence scripts, 44 new
  tests, equivalence evidence, reports.

## Decision P12 — Living systematic review V1 (2026-09-16)

- **Status:** ADOPTED
- **Context:** The proposal/literature base must be a living artifact, not a
  one-shot table.
- **Decision:** Maintain docs/LIVING_SYSTEMATIC_REVIEW.md +
  esearch/literature/{review_matrix.csv,search_log.csv,idea_ledger.md}. Seed
  the matrix with 12 systems (RIPPLE, Repository Memory, Adaptive-k, LocAgent,
  GraphLocator, RepoGraph, Agentless, CodePlan, RepoCoder, AutoCodeRover,
  RPG/ZeroRepo, AB-RAG), classified PEER-REVIEWED / PREPRINT /
  CROSS-DOMAIN-INSPIRATION. Only LocAgent is VERIFIED with direct evidence;
  every other row is SEEDED - verify primary source until verified against
  the primary source. Dispositions (TEST/WATCH/BOUNDARY) live in the idea
  ledger.
- **Rationale:** truthful competitor tracking for the thesis; no unsupported
  novelty claims.
- **Impact:** new literature artifacts; the review is updated on every new
  screening.

## Decision P13 — Omission-Risk Feature Study v1 is the ONLY next scientific step (2026-09-16)

- **Status:** ADOPTED (this task; STATED, NOT STARTED)
- **Context:** The harness + review foundation is complete; the next scientific
  step must be chosen and NOT executed in this milestone.
- **Decision:** The single next scientific step is
  **OMISSION_RISK_FEATURE_STUDY_V1 (TRAIN/VALIDATION only)** — feature families
  and routing metrics as recommended in eports/RESEARCH_HARNESS_V1_REPORT.md
  §9 and esearch/literature/idea_ledger.md I1/I2/I5/I6. Do NOT start:
  omission-risk training/analysis, Saleor scientific execution, LocAgent
  scientific calls, selective escalation, or new model runs.
- **Rationale:** architecture first, science second; every future experiment
  runs through the harness with an explicit budget.
- **Impact:** the harness + review milestone STOPS here; the feature study
  requires its own freeze + authorization.

## Decision P14 — Phase-B mandatory preflight amendment adopted (2026-09-16)

- **Status:** ADOPTED (this task; permanent preflight requirement for
  omission-risk feature work)
- **Context:** The user provided an amendment requiring preflight gates before
  any omission-risk feature analysis: (A) Phase-B data availability gate;
  (B) repository evidence-capability audit; (C) cross-repository confound rule;
  (D) feature availability flags; (E) graph interpretation branches;
  (F) history/co-change interpretation; (G) manual equivalence sanity check;
  (H) pause before interpreting/freezing feature results until A–G complete.
- **Decision:** Adopt A–G as mandatory preflight for this study and all future
  omission-risk feature work. Gate A: if TRAIN/VALIDATION Sparse-v2 labels are
  unavailable, STOP scientific feature-result analysis, do NOT substitute the
  exposed HELD_OUT_TEST, produce a frozen DEVELOPMENT-INFERENCE protocol with
  expected calls/tokens/cost + gates, and request Ahmed's approval before any
  new scientific LLM/API call.
- **Rationale:** preserves the strict data rule; prevents the deterministic
  stand-in from being mistaken for the registered Sparse-v2 analysis.
- **Impact:** Phase-B preflight executed (reports/OMISSION_RISK_REPOSITORY_EVIDENCE_AUDIT.md
  + JSON/CSV; data_availability.json; equivalence_sanity_sample.json).

## Decision P15 — Registered Sparse-v2-label omission-risk study DEFERRED (2026-09-16)

- **Status:** ADOPTED (this task)
- **Context:** Gate A confirmed TRAIN/VALIDATION have NO Sparse-v2 predictions
  (P1 ran only on HELD_OUT_TEST, which is permanently exposed and cannot be
  substituted).
- **Decision:** The registered primary label `has_fn(t)` (Sparse-v2 prediction
  misses ≥1 proxy-positive file) is NOT computable on TRAIN/VALIDATION from
  existing evidence. The registered omission-risk feature analysis is
  **DEFERRED** pending a new scientific LLM run. The deterministic-first-pass
  development analysis (metadata-corpus BM25@K) IS delivered as development
  evidence for that variant only, explicitly NOT as the registered result.
- **Rationale:** amendment P14 (no substitution of the exposed split; no new
  LLM calls without approval).
- **Impact:** `docs/OMISSION_RISK_DEVELOPMENT_INFERENCE_PROTOCOL.md` (frozen:
  90-cell Sparse-v2 on TRAIN/VALIDATION, ~497.6k tokens, ~$0.19, ceiling
  $0.30); no LLM call without approval.

## Decision P16 — Deterministic-first-pass development analysis delivered (2026-09-16)

- **Status:** ADOPTED (this task)
- **Context:** Zero-LLM feature study executed on the deterministic first-pass
  label (metadata-corpus BM25@K, K∈{3,5,10}; 83 features; n=30; six gates +
  audit PASS).
- **Decision:** Report it as **development evidence for the deterministic
  first-pass variant** with: task-level statistical unit; raw-AUROC random band
  (n=30, radius ~0.24–0.26); expected-chance above-band count (~12) vs observed
  (1–2); no VALIDATION-only operating point frozen; cost analysis as decision
  analysis (C_FN/C_VERIFY grid), not a deployment policy.
- **Rationale:** honest, reproducible, bounded; nothing over-claimed.
- **Impact:** research/omission-risk-feature-study-v1/*; reports
  OMISSION_RISK_FEATURE_STUDY_V1_REPORT.md / _AUDIT.md; 19 unit tests.

## Decision P17 — No new scientific LLM/API call without approval (2026-09-16)

- **Status:** ADOPTED (permanent for this line)
- **Context:** The registered Sparse-v2-label analysis requires new inference;
  the amendment and §7 cost discipline forbid unapproved calls.
- **Decision:** No new scientific LLM/API call (including the deferred Sparse-v2
  development inference) may be made without Ahmed's explicit approval of
  `docs/OMISSION_RISK_DEVELOPMENT_INFERENCE_PROTOCOL.md`.
- **Rationale:** zero-cost discipline + strict data rule + truthful status.
- **Impact:** the milestone STOPS at the protocol + approval request.

## Decision P18 — Sparse-v2-label development-inference EXECUTED (2026-09-16)

- **Status:** ADOPTED (this task; supersedes the P15/P17 deferral for this run)
- **Context:** Ahmed APPROVED the frozen DEVELOPMENT-INFERENCE protocol with the
  RECOMMENDED configuration (90 cells, TRAIN/VALIDATION only, sparse_v2 only,
  3 reps, Qwen3-Coder @ deepinfra/turbo, temp 0, cap 16384, 600,000-token AND
  $0.30 hard stop).
- **Decision:** Execute the 90-cell run after the six frozen gates + leakage
  audit PASS; persist every raw response/usage/sha256/failure/retry/provenance;
  compute task-level Sparse-v2 `has_fn` (any-FN-over-reps, N=30); report
  prevalence BEFORE fitting; if either class < 10 independent tasks do NOT fit a
  multivariable RiskScorer (descriptive/single-feature only); rerun the frozen
  omission-risk feature analysis on the real Sparse-v2 labels; compare with the
  deterministic first-pass findings; independent audit; then commit → push →
  merge main → verify → push → DEV tag → fresh export.
- **Result:** 90/90 valid, 490,747 tokens / $0.184 (both ceilings respected);
  Sparse-v2 `has_fn` prevalence **86.7% (26/30, 4 negatives)**; class-balance
  gate FAILED → no multivariable RiskScorer; 3/97 features above the random band
  (4.85 expected by chance) — a retrieval-peakiness cluster now
  direction-consistent; Sparse–BM25 disagreement anti-predictive; adaptive-K no
  help; always-escalate dominates; RiskScorer v1 NOT statistically justified.
- **Impact:** `reports/OMISSION_RISK_SPARSE_V2_INFERENCE_REPORT.md` (answers the
  mandated questions); `reports/OMISSION_RISK_INFERENCE_AUDIT.md` (31/31 PASS);
  run evidence `research/omission-risk-feature-study-v1/sparse_v2_trainval_*`;
  analysis `research/omission-risk-feature-study-v1/sparse_v2_label_analysis/`;
  `data_availability.json` updated (TRAIN/VALIDATION sparse_v2 available).
