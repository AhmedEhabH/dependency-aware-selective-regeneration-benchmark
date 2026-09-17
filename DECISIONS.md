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

## Decision P19 — Autonomous MSc acceleration session authorized (2026-09-16)

- **Status:** ADOPTED (this session)
- **Context:** Ahmed is away; the `_workspace/active/OPENCODE_AUTONOMOUS_MSC_ACCELERATION_TO_PROPOSAL_2026-09-16.md`
  authorizes autonomous execution in priority order with explicit stop
  conditions (no hidden-test peeking, no destructive git, no scope change, no
  hard budget violation, no fabrication).
- **Decision:** Execute the ordered milestones (README transparency closure;
  RealCommitImpactDataset-v2 design + sample-size analysis; Saleor/NestJS
  suitability; classical/static CIA; conditional V2 development inference only
  if within the authorized ceilings — ≤450 new cells, ≤2.5M tokens, ≤$1.00;
  living-review novelty audit; print-ready MSc Proposal V1; seminar outline;
  light export). Record choices in DECISIONS.md; document blockers and continue.
- **Budget ceilings (authorized in the mission file):** new V2 development
  cells ≤ 450; new tokens ≤ 2,500,000; new API/frozen-pricing cost ≤ USD 1.00;
  no V2 TEST/RESERVE calls; no result-dependent reruns; no provider/model
  family change. STOP the model only if these are exceeded.
- **Rationale:** proposal deadline before 2026-10-01; supervisor-ready draft
  needed now.

## Decision P20 — Roadmap position + contingency routes updated (2026-09-16)

- **Status:** ADOPTED
- **Context:** The Sparse-v2 omission-risk development inference is complete;
  task-level RiskScorer is not justified on n=30 (class-balance gate failed).
- **Decision:** The roadmap now states the overall research position without
  forcing the thesis to depend on RiskScorer success. Two pre-registered
  contingency routes: Route A (task-level selective routing, used only if a
  larger development set establishes a reliable signal) and Route B
  (candidate-level bounded verification of suspicious omitted candidates under
  a hard budget, compared with always-verify and random matched-budget).
- **Impact:** docs/MSC_RESEARCH_ROADMAP_2026_2027.md (overall position +
  Route A/B + frozen comparison plan + proposal deadline schedule).

## Decision P21 — README / dataset transparency closure (Milestone A, T2)

- **Status:** ADOPTED
- **Context:** README diagrams used Mermaid only (browser-dependent rendering);
  the RealCommitImpactDataset-v1 funnel and the 30 development tasks were not
  documented in the README; RiskScorer vs planner/verifier terminology was
  ambiguous.
- **Decision:** Keep editable Mermaid sources under `docs/diagrams/*.mmd`
  (source of truth); generate deterministic static SVG fallbacks under
  `docs/assets/` with `scripts/generate_readme_svgs.py` (no browser
  dependency); embed SVGs in README; document the verified v1 funnel and the
  30-task development table (generated from frozen artifacts by
  `scripts/generate_transparency_tables.py`, never hand-transcribed); add a
  planner/RiskScorer/verifier terminology section; state that RiskScorer v1 is
  NOT justified on the 30-task development evidence.
- **Impact:** README.md; docs/diagrams/*.mmd; docs/assets/*.svg;
  research/transparency/*; scripts/generate_readme_svgs.py,
  scripts/generate_transparency_tables.py.

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

## Decision P22 - V2 development inference EXECUTED; RiskScorer gate FAILS (2026-09-16)

- **Status:** ADOPTED (this session)
- **Context:** Authorized by mission C3 (<=450 NEW cells, <=2.5M tokens, <=.00).
  V2 split frozen (150 DEV cases; INTERNAL_TEST/RESERVE untouched); six V2
  gates PASS; LIVE API run.
- **Result:** 431/450 cells executed (144 independent V2 tasks; 129 pos /
  15 neg, prevalence 89.6%); fail-closed budget STOP at 2.5M tokens
  (2,501,964 tokens, .873 cost; 19 cells not run); 430 valid / 1 failure
  (JSON-parse cell, no replacement). Merged v1+v2: 174 tasks, 155 pos /
  19 neg (89.1%).
- **Decision (C4/C5):** C4 signal gates FAIL. The v1 peakiness signal
  (bm25_zero_count AUROC 0.837) does NOT replicate in V2 (0.592, inside the v2
  band); the pooled "33 above-band" is a cohort/universe-size artifact
  (V2 universes up to 234 vs v1 140-152; graph features correlate ~0.99 with
  universe size). NO multivariable RiskScorer fitted. The negative is frozen as
  development evidence; the mechanism pivots to Route B - candidate-level
  bounded omission verification (pre-registered).
- **Impact:** reports/REAL_COMMIT_V2_OMISSION_RISK_DEVELOPMENT_ANALYSIS.md;
  research/transparency/v2_omission_risk_analysis.json; v2_trainval run evidence.

## Decision P23 - Proposal V1 + seminar outline drafted (2026-09-16)

- **Status:** ADOPTED (deadline-critical deliverable)
- **Context:** printed registration-seminar proposal required before 2026-10-01.
- **Decision:** create a supervisor-ready, print-ready proposal package in
  msc_proposal/ with a conservative academic LaTeX format (no fabricated
  institutional form fields), truthful current evidence, pre-registered Route
  A/B contingencies, and the preferred title.
- **Impact:** msc_proposal/MSC_PROPOSAL_V1.tex+.pdf (6 pages, compiles clean),
  references.bib, PROPOSAL_CLAIMS_MATRIX.md, PROPOSAL_SUPERVISOR_BRIEF.md,
  PROPOSAL_PRINT_CHECKLIST.md, PROPOSAL_CHANGELOG.md,
  msc_proposal/SEMINAR_PRESENTATION_OUTLINE.md.

## Decision P24 - Living-review novelty audit (2026-09-16)

- **Status:** ADOPTED
- **Decision:** do NOT claim graph localization, repository memory, intent-
  aware expansion, adaptive K, or generic uncertainty-triggered escalation as
  novel by themselves. The strongest defensible FUTURE novelty candidate is
  'omission-aware, cost-sensitive bounded verification of an explicit sparse
  file-level impact policy under matched inference budgets', marked
  CANDIDATE-NOT-YET-CLAIMED, with a Route B candidate-level fallback.
- **Impact:** docs/LIVING_SYSTEMATIC_REVIEW.md (novelty audit section);
  research/literature/review_matrix.csv + idea_ledger.md additions.

## Decision P25 - Experimental comparison plan frozen (2026-09-16)

- **Status:** ADOPTED (frozen in roadmap)
- **Decision:** the fair comparison includes Random/cheap control, BM25,
  adaptive cheap retrieval (if justified), classical/static CIA, Sparse
  planner, Full planner, faithful LocAgent/reference agent (when
  reproducible), Sparse+Always Verify, Sparse+Random Verify (matched budget),
  Sparse+Selective/Bounded Verify (Route B candidate-level if task-level
  routing unsupported), Oracle routing upper bound. Metrics include correctness,
  cost, latency, failure counts, and the Pareto frontier; per-repository
  primary, macro-average across repos, pooled secondary, repo-ID confound check.
- **Impact:** docs/MSC_RESEARCH_ROADMAP_2026_2027.md.

## Decision P26 - BibTeX triage: 13 exports as candidate discovery (2026-09-16)

- **Status:** ADOPTED (this session)
- **Options:** treat the 13 uploaded .bib exports as authoritative metadata OR as
  candidate discovery sources.
- **Chosen:** candidate discovery sources; every important reference verified
  from primary sources (arXiv API / Crossref) before citation.
- **Why:** exports are search-harvest exports with query-collision noise.
- **Rejected:** copying hundreds of references into the proposal.
- **Evidence:** reports/BIBTEX_LITERATURE_TRIAGE_2026-09-16.md + classified CSV.
- **Revisit:** as new literature appears.

## Decision P27 - Proposal factual corrections (V1.2)

- **Status:** ADOPTED
- **Options:** correct stale numbers OR keep.
- **Chosen:** correct all: Sparse 4.9 / Full 144.0 / ~96.6% reduction; LocAgent
  5/10 non-usable (2 timeout + 1 context + 2 empty); V2 431 calls / 2,501,964
  tokens / 1,964-token (0.08%) overshoot.
- **Why:** every number must map to one frozen artifact; no placeholder authors.
- **Rejected:** stale 5.9 / "50% empty" / "within ceiling".
- **Evidence:** M1B, P5C, V2 closure.
- **Revisit:** n/a.

## Decision P28 - Route B progression gate defined (2026-09-16)

- **Status:** ADOPTED (frozen in Proposal V1.2)
- **Options:** LLM verifier allowed always / only after a gate.
- **Chosen:** actual LLM verifier only if a predeclared rule beats Random at
  B=5 on DEV_VALIDATION, same direction on DEV_TRAIN, not a universe/repo-ID
  artifact, no leakage, practically meaningful recovery.
- **Why:** prevents inventing a complex verifier on weak evidence.
- **Rejected:** unconditional verifier pilot.
- **Evidence:** Proposal V1.2 Section 7.
- **Revisit:** after the zero-LLM Route B study.

## Decision P29 - P5R-1 operational-limits-only rerun (2026-09-16)

- **Status:** ADOPTED (design; execution pending)
- **Options:** mix old P5 successes with new rescued runs OR clean new study.
- **Chosen:** clean P5R-1 (all 10 tasks under ONE frozen P5R-1 config) if the
  rescue pilot triggers; P5 stays immutable.
- **Why:** do not "repair" the headline by mixing.
- **Rejected:** blending P5 with P5R.
- **Evidence:** reports/LOCAGENT_P5C_HELDOUT_RUN.md + P5R forensics.
- **Revisit:** after pilot outcome.

## Decision P30 - Traceability ledgers created (2026-09-16)

- **Status:** ADOPTED
- **Options:** document only successes OR document negatives/deferred too.
- **Chosen:** complete ledgers (decision/problem/experiment/baseline/literature)
  including rejected and deferred options and reasons.
- **Why:** nothing important silently forgotten.
- **Evidence:** reports/RESEARCH_DECISION_LEDGER.md, PROBLEMS_AND_FAILURES_LEDGER.md,
  EXPERIMENT_AND_IDEA_LEDGER.md, BASELINE_SELECTION_LEDGER.md,
  LITERATURE_DECISION_LEDGER.md.
- **Revisit:** append as the mission progresses.

## Decision P31 - Saleor Stage-2 READY-TO-RUN (2026-09-16 evening)

- **Status:** ADOPTED
- **Context:** full Saleor history cached (22,615 commits); frozen miner
  generalized to Saleor via PRODUCTION_ROOTS=('saleor',) adapter (no rule change).
- **Decision:** reconstruct the Saleor sampling frame (6000 -> 2409 -> 1352 ->
  1316 independent eligible); freeze a metadata-only split proposal (seed
  20260916; DEV_TRAIN 120 / DEV_VALIDATION 30 / INTERNAL_TEST 80 / RESERVE 1086);
  produce the pre-inference gate report. Do NOT run Saleor inference tonight.
- **Why:** Saleor pool (1316) is ~4x djangoCMS (329); a quantitative Stage-2 is
  fully supported; INTERNAL_TEST/RESERVE protected.
- **Rejected:** running Saleor inference without an audited case-bundle build;
  inspecting any Saleor TEST outcome.
- **Evidence:** reports/SALEOR_SAMPLING_FRAME_AUDIT.md,
  reports/SALEOR_SAMPLE_SIZE_ANALYSIS.md, reports/SALEOR_PRE_INFERENCE_GATE_REPORT.md,
  research/transparency/saleor_*.
- **Revisit:** after the Saleor case-bundle build + split manifest audit.

## Decision P32 - P5R full rerun NOT triggered (2026-09-16 evening)

- **Status:** ADOPTED
- **Options:** full clean 10-task P5R-1 rerun / pilot-only.
- **Chosen:** pilot-only (0/5 usable; the pilot consumed 20.54M tokens / \.18
  with a fail-closed stop; a full rerun cannot rescue the empty/worker-crash
  cases and would consume the remaining evening budget with no expected change).
- **Why:** the wrapper timeout is ineffective (upstream 900 s hard-coded
  deadline); context is a hard route limit (262,144).
- **Rejected:** blending P5 with P5R; editing upstream.
- **Evidence:** reports/LOCAGENT_P5R1_PILOT_REPORT.md.
- **Revisit:** P5R-2 (provider-deviation) only if same weights + larger context.

## Decision P33 - Route B is the primary mechanism; verifier pilot deferred

- **Status:** ADOPTED (progression gate PARTIAL)
- **Options:** run LLM verifier pilot now / defer.
- **Chosen:** defer; the zero-LLM Route B signal is positive (CIA beats Random
  at B=5) but DEV_VALIDATION CI includes 0; an LLM verifier pilot is not
  strongly justified until a larger validation set or a hybrid refinement
  strengthens the signal.
- **Why:** do not invent a complex verifier on weak evidence.
- **Rejected:** unconditional verifier pilot.
- **Evidence:** reports/ROUTE_B_OMISSION_RECOVERY_V1_REPORT.md.
- **Revisit:** if a larger DEV_VALIDATION confirms the CIA advantage.

## Decision P34 - Saleor Stage-2 ready-to-run; no inference tonight

- **Status:** ADOPTED
- **Context:** full Saleor history cached (22,615 commits); frame reconstructed
  (1316 eligible); split proposed (seed 20260916).
- **Decision:** Saleor READY-TO-RUN (reports/SALEOR_PRE_INFERENCE_GATE_REPORT.md);
  no Saleor model inference tonight; case-bundle build + split manifest is the
  next audited data step.
- **Why:** the 1316 pool supports a quantitative Stage-2 with a protected test.
- **Rejected:** running Saleor inference without the audited build; inspecting
  Saleor TEST.
- **Evidence:** reports/SALEOR_SAMPLING_FRAME_AUDIT.md, SALEOR_SAMPLE_SIZE_ANALYSIS.md.
- **Revisit:** after the Saleor case-bundle build.

## Decision P35 - Route B V2 progression gate PASS; CIA frozen (2026-09-17)

- **Status:** ADOPTED (overnight)
- **Options:** freeze CIA / keep exploring.
- **Chosen:** freeze CIA (0.5 BM25 + 0.5 graph neighbor) as the predeclared
  ranker family for the conditional verifier.
- **Why:** 5/5 folds positive direction; 4/4 B-curve points above analytic
  Random; bootstrap CIs exclude zero at every B; no omitted/universe-size
  artifact (corr -0.119/-0.117).
- **Rejected:** path-token (worst); single-draw Random (analytic hypergeometric
  expectation used instead); per-fold tuning.
- **Evidence:** reports/ROUTE_B_V2_ROBUSTNESS_REPORT.md.
- **Revisit:** if a fresh confirmatory set (INTERNAL_TEST, after full freeze)
  contradicts the direction.

## Decision P36 - B-curve is the primary object; B=5 is a reference point

- **Status:** ADOPTED
- **Chosen:** budget curve B in {0,1,3,5,10}; B=5 is a convenient reference only.
- **Why:** a single point is fragile; the scientific object is recovery as a
  function of added inspection budget.
- **Evidence:** docs/ROUTE_B_V2_DEVELOPMENT_PROTOCOL.md.
- **Revisit:** n/a (frozen).

## Decision P37 - Analytic Random replaces single-draw Random

- **Status:** ADOPTED
- **Chosen:** E[X] = B*M/N (B clipped to N) hypergeometric expectation.
- **Why:** avoids dependence on one lucky draw; per-task analytic comparison
  with task-level bootstrap CI.
- **Rejected:** single-draw Random; random repetitions as independent tasks.
- **Evidence:** docs/ROUTE_B_V2_DEVELOPMENT_PROTOCOL.md.
- **Revisit:** n/a.

## Decision P38 - Verifier pilot run (small, one-shot)

- **Status:** EXECUTED (30 calls, 6,748 tokens, .0023)
- **Chosen:** run the verifier pilot because the Route B V2 gate PASSED.
- **Result:** Oracle-in-top-B = 1.000 at every B; verifier ORR 0.86-1.00;
  dominant loss = first-pass omission. Diagnostic, not headline.
- **Evidence:** reports/ROUTE_B_VERIFIER_PILOT_REPORT.md.
- **Revisit:** a confirmatory verifier run requires INTERNAL_TEST after full freeze.

## Decision P39 - INTERNAL_TEST stays sealed overnight

- **Status:** ADOPTED
- **Chosen:** do NOT open INTERNAL_TEST=80 or RESERVE=59.
- **Why:** open only after ALL are frozen: Route-B ranker family, budget curve,
  tie-breaking, analytic Random control, metrics, verifier protocol, statistical
  analysis, leakage/confound checks, and proposal review acknowledging the freeze.
- **Evidence:** mission Section 10; ledgers.
- **Revisit:** after the full freeze (next milestone).

## Decision P40 - Saleor portability fix (production-only materializer) (2026-09-17)

- **Status:** ADOPTED (continuation mission Block B)
- **Problem:** whole-tree git archive fails on Windows for Saleor parents with
  a test cassette containing ?/[/] filename chars.
- **Chosen:** platform-independent production-only parent materializer
  (git ls-tree + frozen production predicate + git cat-file --batch); only
  production .py blobs under saleor/ are materialized.
- **Why:** does NOT change frozen eligibility/production-file rules; no
  scientific file deleted or skipped; extraction-mechanism only.
- **Rejected:** cassette-exclusion rule change; POSIX-only re-run.
- **Evidence:** equivalence gate 98/98 PASS; rebuilt 150/150; canonical
  universe+graph hashes identical to pre-portability snapshot (0 mismatch).
- **Revisit:** n/a (fix proven equivalent).

## Decision P41 - Saleor sparse inference FAIL-CLOSED on budget (2026-09-17)

- **Status:** BLOCKED (documented; no silent protocol change)
- **Problem:** measured Saleor per-cell cost ~14.5k tokens / .0047 (live smoke
  cell) -> 450-cell run projects ~6.5-7.4M tokens / .13-2.23, 2.4-2.7x over
  the authorized hard ceiling (2.7M tok / .00).
- **Chosen:** stop after 1 smoke cell; do NOT run the remaining 449.
- **Rejected:** silent subset/reduced-reps (protocol change); raising ceiling
  without authorization.
- **Evidence:** reports/SALEOR_SPARSE_INFERENCE_BUDGET_BLOCKED_CLOSURE.md.
- **Revisit:** requires explicit re-budget (measured basis ~7.5M tok / .25)
  or a documented pre-registered subset.

## Decision P42 - Confirmatory freeze packet: choice B (ranking + actual verifier) (2026-09-17)

- **Status:** PROPOSED in packet (ready-to-approve; INTERNAL_TEST sealed).
- **Chosen:** B - end-to-end conditional-verifier budget curve (ranker + frozen
  verifier inspecting top-B) as the confirmatory claim.
- **Why:** DEV result includes Oracle-in-top-B=1.0 verifier-pilot finding;
  ranking-only would under-claim the proposal.
- **Revisit:** supervisor approval required before confirmatory execution.

## Decision P43 - P2 adaptive budget stays CONDITIONAL (2026-09-17)

- **Status:** CONDITIONAL - AFTER FIXED ROUTE-B CONFIRMATION.
- **Chosen:** formalize features + pre-register 3 policies; NO learned policy;
  NO winner on confirmatory data.
- **Evidence:** docs/ADAPTIVE_BUDGET_P2_PRE_REGISTRATION_NOTE.md.

## Decision P44 - Proposal V1.4 NOT created (2026-09-17)

- **Status:** ADOPTED (no material claim change).
- **Chosen:** keep V1.3 as the print candidate; update state/roadmap/ledgers only.
- **Why:** Saleor replication did NOT run (budget-blocked) -> no new
  cross-repo result; confirmatory-freeze packet is ready-to-approve, not an
  executed confirmatory outcome; P2 unchanged (conditional).
- **Revisit:** create V1.4 when Saleor replication or confirmatory results exist.

## Decision P45 - Saleor identity/provenance correction (2026-09-17)

- **Status:** ADOPTED
- **Problem:** Saleor bundles carried djangoCMS identity (djangocms-rc-* IDs,
  django-cms URL, #djangocms license, graph repo_id=djangocms); the case ID was
  visible in the inference prompt -> provenance leak.
- **Chosen:** deterministic migration djangocms-rc-<sha> -> saleor-rc-<sha>
  (prefix swap; sha = target short sha); corrected repository URL/anchor/
  license/repo identity; old->new mapping persisted; 150/150 scientific-payload
  equivalence PASS (commits/split/universes/proxies/edges preserved).
- **Rejected:** running Saleor inference with the djangocms-rc-* leak.
- **Evidence:** reports/SALEOR_IDENTITY_MIGRATION_REPORT.md.

## Decision P46 - Saleor clean DEVELOPMENT sparse run + budget (2026-09-17)

- **Status:** EXECUTED
- **Chosen:** clean 150x3 DEVELOPMENT sparse run after identity fix.
- **Ceilings:** 450 cells / 9,000,000 tokens / .00 (re-authorized).
- **Result:** 450/450 cells; 446 succeeded / 4 failed (3x HTTP 429 transport +
  1x schema duplicate-id); 7,316,986 tokens / .31 (within ceilings);
  150 independent tasks; 0 truncations; provider DeepInfra.
- **Rejected:** rerunning failed cells (no result-dependent reruns); opening
  INTERNAL_TEST/RESERVE; Saleor-specific tuning.
- **Evidence:** research/saleor-sparse-inference/, saleor_dev_closure.json.

## Decision P47 - Saleor Route-B transfer classification: REPLICATES (2026-09-17)

- **Status:** ADOPTED (transfer test result)
- **Chosen:** classify as REPLICATES — frozen Classical-CIA arm above analytic
  Random over the Saleor DEV B-curve (149 tasks; B=5 delta +0.231 CI
  [+0.180,+0.287]; 5/5 folds positive; 4/4 B-points; no size artifact).
- **Rejected:** pooling djangoCMS+Saleor as the primary headline; tuning the
  method on Saleor outcomes.
- **Evidence:** reports/SALEOR_ROUTE_B_TRANSFER_REPORT.md.

## Decision P48 - Ranker identity: CIA ≡ Hybrid; name corrected (2026-09-17)

- **Status:** ADOPTED (zero-API audit, PRE-CONFIRMATORY HARDENING V14)
- **Chosen:** confirm the frozen Route-B V2 "CIA" arm is exactly
  normalized BM25 + binary graph-neighbor; the Hybrid arm (0.5 BM25 + 0.5
  graph-neighbor) is MATHEMATICALLY RANK-EQUIVALENT (Hybrid = 0.5 × CIA key).
  Verified at top-B identity on 174 djangoCMS + 149 Saleor DEV tasks: 0
  differing cells, full-rank identical. Hybrid is a redundant alias/control,
  NOT an independent baseline. "Classical-CIA" terminology corrected to
  `BM25+Graph-Neighbor Composite (historical label: CIA)`.
- **Why:** documentation must match the exact code; the confirmatory formula is
  NOT changed before confirmatory testing.
- **Evidence:** reports/ROUTE_B_RANKER_IDENTITY_AUDIT.md +
  research/transparency/route_b_ranker_identity_audit.json.
- **Revisit:** n/a (correction appended; historical results unchanged).

## Decision P49 - Incremental-evidence ablation: predominantly lexical (2026-09-17)

- **Status:** ADOPTED (characterization only; zero API)
- **Chosen:** composite−BM25 paired task-level deltas are small with bootstrap
  CIs including zero at most B on both repositories (djangoCMS B=5 +0.003
  [−0.015,+0.019]; Saleor B=5 +0.003 [−0.017,+0.024]). The cross-repo signal
  is predominantly LEXICAL (BM25); the graph-neighbor increment is small and
  largely non-significant. No new ranker chosen; frozen confirmatory method
  unchanged.
- **Evidence:** reports/ROUTE_B_INCREMENTAL_EVIDENCE_ABLATION.md +
  research/transparency/route_b_incremental_ablation.json.
- **Revisit:** n/a (characterization).

## Decision P50 - Confirmatory freeze packet V2 supersedes V1 (2026-09-17)

- **Status:** ADOPTED (V1 immutable; V2 supersedes)
- **Chosen:** correct ranker name/formula; record CIA/Hybrid redundancy; state
  Saleor transfer is AVAILABLE and REPLICATES on DEVELOPMENT; exact first-pass
  repetition rule (first SUCCEEDED rep write-set), failed-rep/task treatment,
  verifier semantics (1 call per (task,B), independent across B, B=0 no call),
  B∈{0,1,3,5,10}, primary ORR + secondary P/R/F1/FNR, analytic Random,
  bootstrap, failure semantics, no result-dependent reruns. Frozen claim:
  end-to-end Sparse → frozen ranker → bounded verifier on djangoCMS
  INTERNAL_TEST.
- **Evidence:** reports/DJANGOCMS_ROUTE_B_CONFIRMATORY_FREEZE_PACKET_V2.md.
- **Revisit:** on supervisor approval before confirmatory execution.

## Decision P51 - Confirmatory API budget frozen (2026-09-17)

- **Status:** FROZEN (zero test peek; DEVELOPMENT distributions only)
- **Chosen:** 80 djangoCMS INTERNAL_TEST tasks; Sparse-v2 3-rep first pass
  (240 cells); verifier at B={1,3,5,10} (320 calls; B=0 none). Expected 560
  calls / ~1,443,395 tokens / ~$0.50; hard ceilings 2,100,000 tokens / $1.00;
  per-call reservation rule (sparse p99 7,877 tok / $0.00302; verifier 400 tok
  / $0.00015) so cumulative budget cannot overshoot materially.
- **Why:** conservative ceiling from DEVELOPMENT maxima with a fail-closed
  reservation ledger.
- **Evidence:** reports/DJANGOCMS_CONFIRMATORY_API_BUDGET_FREEZE.md.
- **Revisit:** requires Ahmed's explicit approval with the V2 packet before any
  confirmatory call.

## Decision P52 - Proposal V1.4 created (material scientific change) (2026-09-17)

- **Status:** ADOPTED (V1.3 immutable)
- **Chosen:** create V1.4 because the completed Saleor DEVELOPMENT transfer
  replication is a material scientific-state change vs V1.3 (which predated
  it). Conservative updates: Saleor 450-cell DEV run, transfer REPLICATES,
  DEVELOPMENT-transfer boundary explicit, Classical-CIA terminology corrected,
  predominantly-lexical signal stated, no graph novelty, adaptive B_t
  conditional, INTERNAL_TEST/RESERVE sealed.
- **Evidence:** msc_proposal/MSC_PROPOSAL_V1_4.tex/.pdf (7 pages, SHA-256
  dd7125fa…), PROPOSAL_V1_4_AUDIT.md, PROPOSAL_CHANGELOG.md,
  PROPOSAL_CLAIMS_MATRIX.md.
- **Revisit:** V1.5 only if a further material change occurs (e.g., confirmatory
  outcome).
