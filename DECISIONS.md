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
  and routing metrics as recommended in
eports/RESEARCH_HARNESS_V1_REPORT.md
  §9 and
esearch/literature/idea_ledger.md I1/I2/I5/I6. Do NOT start:
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

## Decision P53 - V1.4 print/bibliography/timeline addendum applied in place (2026-09-17)

- **Status:** ADOPTED (no V1.5; V1.4 still the active unmerged draft)
- **Chosen:** apply the V1.4 layout/references/timeline addendum to V1.4 in
  place. (1) Experimental Design at a Glance rebuilt with 8 compact tabularx
  columns (raggedright, short labels, no internal codes, no resizebox) —
  overlap fixed, zero overfull hboxes. (2) Bibliography rendered in the PDF:
  Section 11 now compiles the actual verified references.bib via BibTeX
  (unsrt); every in-text cite{} resolves; 21 reference entries appear (pages
  9-10); preprints marked; the stale bibliography (V1.3) sentence replaced
  with V1.4 wording. (3) Timeline replaced with the detailed 2026-11 to
  2027-10 schedule (12 windows); intended substantive research/thesis
  completion = 2027-07/08; September-October 2027 = publication/revision/admin
  buffer; no fabricated months. (4) Compiles clean (pdflatex x2 + bibtex): 10
  pages (was 7); PDF SHA-256 50957a2525f7430de47fd9306895d2b4c80b30c358d3cafe6798a0a27b0525b1.
- **Why:** the printed proposal must be readable at A4/grayscale (table
  overlap), carry the actual verified references, and show an honest, detailed
  schedule matching Ahmed's 2026-11 to 2027-10 plan.
- **Impact:** msc_proposal/MSC_PROPOSAL_V1_4.tex/.pdf, PROPOSAL_V1_4_AUDIT.md,
  PROPOSAL_CHANGELOG.md, PROPOSAL_CLAIMS_MATRIX.md, PROPOSAL_PRINT_CHECKLIST.md;
  no scientific input changed; INTERNAL_TEST/RESERVE sealed.
- **Evidence:** msc_proposal/MSC_PROPOSAL_V1_4.pdf (10 pages, SHA-256
  50957a25...), reports/V14_FINAL_DOCUMENT_CONSISTENCY_AUDIT.md.
- **Revisit:** V1.5 only if a further material change occurs.

## Decision P54 - Pre-confirmatory execution package + P2 + semantic audit readiness (2026-09-17)

- **Status:** ADOPTED (ZERO API, ZERO test peek)
- **Chosen:** (C) prepare a ready-to-run confirmatory execution package
  (scripts/djangocms_confirmatory_config.py,
  scripts/djangocms_confirmatory_execution.py,
  scripts/djangocms_confirmatory_metrics.py, 6 focused tests) with the frozen
  560-call / 2,100,000-token / USD 1.00 ceilings, per-call fail-closed
  reservation ledger, raw+sha persistence, failure taxonomy, and stop rule;
  dry-run (synthetic, NOT_REAL) PASS; status READY_FOR_AHMED_APPROVAL - real
  execution requires Ahmed's explicit approval. (D) P2 adaptive budget stays
  CONDITIONAL - AFTER FIXED ROUTE-B CONFIRMATION; exact observable features,
  train/dev-only evaluation plan, stop/fail criteria, and the
  CONDITIONAL-to-ACTIVE vs negative-close evidence are now specified. (E)
  semantic human audit made turnkey (blinded manifest, Rater A/B + adjudicator
  forms, one-page instructions, kappa/sensitivity scripts, checklist, exact
  save locations, one synthetic dry-run clearly NOT_REAL); status
  READY_FOR_HUMAN_EXECUTION.
- **Why:** everything machine-preparable must be finished so the semantic human
  audit and (on approval) the confirmatory run are turnkey; no confirmatory
  model call is made in this mission.
- **Impact:** reports/DJANGOCMS_CONFIRMATORY_EXECUTION_READINESS.md,
  reports/SEMANTIC_AUDIT_HUMAN_EXECUTION_READINESS.md,
  docs/ADAPTIVE_BUDGET_P2_PRE_REGISTRATION_NOTE.md,
  scripts/djangocms_confirmatory_*.py, tests/unit/test_djangocms_confirmatory_execution.py,
  research/transparency/djangocms_internal_test_case_ids.json (split metadata
  only).
- **Evidence:** dry-run summary + 6/6 tests PASS; semantic_audit_finalize.py
  PACKET_INTEGRITY PASS + SYNTHETIC_DRYRUN PASS.
- **Revisit:** on Ahmed's approval of the confirmatory run / after the human
  audit.


## Decision P55 - djangoCMS INTERNAL_TEST confirmatory run: EXECUTED, CONFIRMS (2026-09-17)

- **Status:** EXECUTED (Ahmed-authorized opening; ZERO method change)
- **Authorization:** Ahmed explicitly authorized opening ONLY djangoCMS V2
  INTERNAL_TEST (80 tasks) under the frozen V2 confirmatory packet + API budget.
- **Chosen:** run exactly the frozen V2 protocol: Sparse-v2 first pass (3
  reps/task, qwen/qwen3-coder @ deepinfra/turbo, temp 0, cap 16384); first
  SUCCEEDED rep write set; frozen `BM25+Graph-Neighbor Composite` ranker; B in
  {0,1,3,5,10}; verifier 1 call/(task,B) for B in {1,3,5,10}, cap 512;
  analytic Random control; ORR/FNRR primary; hard ceilings 560 calls /
  2,100,000 tokens / $1.00; no reruns.
- **Result:** 560 calls / 1,470,174 tokens / $0.505917 (within ceilings); 0
  failures; 0 excluded; raw+sha 560/560 verified. Composite ORR vs analytic
  Random: B=1 0.0591 vs 0.0055; B=3 0.1098 vs 0.0166; B=5 0.165 vs 0.0277;
  B=10 0.2669 vs 0.0554; CIs exclude zero at every B; 5/5 folds positive; 4/4
  B-points; no size artifact. **Classification: CONFIRMS.**
- **Rejected:** method/ranker/verifier change after outcomes; reruns; opening
  RESERVE or Saleor INTERNAL_TEST/RESERVE.
- **Evidence:** reports/DJANGOCMS_ROUTE_B_CONFIRMATORY_RESULT.md,
  reports/DJANGOCMS_CONFIRMATORY_AUDIT.md,
  research/djangocms-confirmatory-route-b/ (metrics JSON, raw manifest,
  run_records.jsonl, runs/raw/*.txt + .sha256).
- **Revisit:** the opened INTERNAL_TEST is permanently used; never reused as a
  fresh test for P2 algorithm selection.

## Decision P56 - P2 five-month adaptive-budget algorithm program (2026-09-17)

- **Status:** ADOPTED (DEVELOPMENT-only; Nov 2026 - Mar 2027 window)
- **Chosen:** launch a five-month P2 program on DEVELOPMENT data only
  (djangoCMS DEV + Saleor DEV): (1) reproduce Shichao-Zhang-inspired
  adaptive-budget ideas (Learning-k, cost-sensitive KNN, one-step computation,
  demand-driven kNN, adaptive-neighborhood); (2) systematically discover and
  classify competing/alternative algorithms from adjacent literature
  (adaptive/conditional computation, selective prediction/abstention/
  learning-to-defer, cascaded inference, optimal stopping, budgeted retrieval,
  active search, contextual bandits where mechanistically relevant); (3)
  implement the strongest interpretable candidates; (4) compare against fixed
  B={1,3,5,10}, Analytic Random, BM25-only, frozen composite, Oracle, InspectAll
  under a common zero-LLM/low-cost harness; (5) freeze negative methods, select
  at most 1-2 justified P2 candidates using DEVELOPMENT only, pre-register
  final evaluation, use still-sealed Saleor INTERNAL_TEST for P2 confirmation
  only if justified; (6) otherwise close P2 negative and keep the fixed-B
  thesis. Fixed Route B is now CONFIRMED and is NOT retuned.
- **Rejected:** using the now-opened djangoCMS INTERNAL_TEST for P2 algorithm
  selection/tuning; learned (neural/large) models unless evidence justifies;
  fabricated work to fill months.
- **Evidence:** reports/P2_ALGORITHM_LANDSCAPE_2026-09.md,
  research/literature/p2_algorithm_landscape.csv,
  docs/P2_IMPLEMENTATION_ROADMAP_2026_2027.md,
  docs/ADAPTIVE_BUDGET_P2_PRE_REGISTRATION_NOTE.md.
- **Revisit:** monthly during Nov 2026 - Mar 2027; P2 may be closed negative
  early with the fixed-B thesis intact.

## Decision P57 - Proposal V1.5 created (doctor-guide polish; ZERO API) (2026-09-17)

- **Status:** ADOPTED (V1.4 immutable; docs-only milestone)
- **Context:** the NEXT MISSION mandates a doctor-guide-compliant abstract
  rewrite, a related-work comparison matrix (fixing the Section 4
  forward-reference), a terminology/claim-safety pass, a slide-handoff
  package, and P2 status alignment. No new scientific evidence exists beyond
  V1.4 (the confirmatory result was already in V1.4).
- **Chosen:** create V1.5 as a POLISH of V1.4 with: (1) abstract rewritten to
  the doctor-guide order (problem/context -> limitation -> precise gap ->
  approach -> setting -> strongest result only -> confirmatory status -> one
  scope limitation), removing "for the first time" and unscoped "robust";
  (2) related-work comparison matrix ADDED in Section 5 (two compact tables,
  rows Classical/history CIA, Agentless, CodePlan, RepoCoder, LocAgent,
  GraphLocator, RepoGraph, This proposal; columns Input | Output unit | First
  pass? | Second stage? | History? | Graph? | Budget-aware? | False-negative
  recovery? | Real commits? | Cross-repo? | Main difference);
  (3) terminology pass ("Classical-CIA" -> "BM25+Graph-Neighbor Composite
  (historical label: Classical-CIA)" / BM25+GraphNeighbor; "fair comparison" ->
  "shared-protocol, budget-matched comparison"; "missed impacted files" ->
  "missed files in the observed historical change-set proxy"; ranking !=
  verification != final localization explicit); (4) P2 stated as NOT complete
  (development research program, not a proven contribution); (5) NestJS/NextJS
  = future external-validity work only (April 2027, suitability gate +
  TypeScript extractor).
- **New verified reference:** RepoGraph (ICLR 2025, arXiv:2410.14684)
  verified from the arXiv API 2026-09-17 (added to references.bib).
- **Compile:** 12 pages; zero overfull/zero underfull/zero undefined citations;
  22/22 references cited; PDF SHA-256
  67dff046347847e1f80e01bdf313acf3cf2a577bfa2783f02686c4e3cf041ef7.
- **Rejected:** deleting the Section 4 forward-reference instead of adding the
  matrix; creating V1.6 (not needed); touching sealed sets; any method change.
- **Evidence:** msc_proposal/MSC_PROPOSAL_V1_5.tex/.pdf,
  PROPOSAL_V1_5_AUDIT.md, PROPOSAL_V1_5_CHANGELOG.md,
  PROPOSAL_V1_5_CLAIMS_MATRIX.md, ABSTRACT_REWRITE_NOTE.md,
  slides/HANDOFF_INTERACTIVE_MSC_SEMINAR_SLIDES.md.
- **Revisit:** V1.6 only if a further material scientific change occurs.

## Decision P58 - P2 Phase-1 NEGATIVE closure + fixed Route-B reviewer closure (2026-09-18)

- **Status:** ADOPTED (mission OPENCODE_P2_PHASE1_MAJOR_SCIENCE_MISSION_2026-09-18; ZERO API)
- **Chosen:** close the fixed Route-B reviewer-facing issues WITHOUT changing the frozen result: (1) curve-level POST-HOC characterization (AURC composite 0.1553 / verifier 0.0971 / random 0.0277; simultaneous task-bootstrap band; per-task distributions; zero-FN 10/80 explicit) in
eports/ROUTE_B_CURVE_LEVEL_POSTHOC_CHARACTERIZATION.md; (2) sparse-vs-full causal parity audit = **PARITY_VERIFIED** (
eports/SPARSE_FULL_CAUSAL_PARITY_AUDIT.md); (3) dataset operational-definition audit (
eports/DATASET_OPERATIONAL_DEFINITIONS.md).
- **P2 Phase-1:** build the common adaptive-budget DEVELOPMENT harness (src/benchmark/p2/, scripts/p2_phase1_run.py, scripts/p2_phase1_gates.py); implement the four preregistered interpretable policies (P2-P1 score-gap, P2-P2 marginal-score, P2-P3 cost-ratio, P2-P4 learning-k analogue) with constants derived on djangoCMS DEV_TRAIN only (tau_gap 0.10 declared; tau_marg 1.0 = 25th pct of DEV_TRAIN top-1 scores; tau_energy 0.90 declared; cost-ratio grid {0.5,1.0,2.0} declared sensitivity); evaluate on djangoCMS DEV (174) + Saleor DEV (149) with the measured verifier cost model.
- **Result:** all four policies **NEGATIVE** (P2-P3 additionally REJECTED_BY_DESIGN as a size/repo artifact); strong-method gate = FALSE; the two stronger methods (cost-sensitive expected-loss stopping; one-step/joint ranking+budget) are NOT implemented; **P2 Phase-1 = NEGATIVE, frozen** (valid scientific result per mission section 4). Phase-2 candidates: NONE.
- **Literature:** +15 verified entries (P2-025..P2-039) in
esearch/literature/p2_algorithm_landscape.csv +
eports/P2_ALGORITHM_LANDSCAPE_2026-09.md section 7 +
eports/LITERATURE_DECISION_LEDGER.md.
- **Semantic audit:** package re-verified; blocker = **AWAITING_HUMAN_RATINGS** (
eports/SEMANTIC_AUDIT_ACTION_REQUIRED_FROM_HUMANS.md); no coding time spent rebuilding ready forms.
- **NestJS:** zero-API readiness documented (
eports/NESTJS_READINESS_ZERO_API_2026-09-18.md); blockers listed (no local cache; TS extractor not implemented).
- **V1.5:** no V1.6, no PPTX;
eports/V15_SUPERVISOR_PATCH_LIST.md created.
- **Rejected:** using the opened djangoCMS INTERNAL_TEST for any P2 tuning/selection; opening djangoCMS RESERVE or Saleor INTERNAL_TEST/RESERVE; inventing human labels; neural/learned policies; any new model/API call.
- **Evidence:**
eports/P2_PHASE1_CLOSURE_REPORT.md, P2_PHASE1_DECISION_GATE.md, P2_POLICY_SPECIFICATIONS.md, P2_PHASE1_HARNESS_RESULTS.md, P2_PHASE1_INDEPENDENT_AUDIT.md,
eports/p2_phase1_gates*.json,
esearch/p2-phase1/*, 31 new tests.
- **Revisit:** Phase-2 candidates may be drawn from the expanded landscape after further development evidence; Saleor INTERNAL_TEST stays sealed for a possible future P2 confirmation ONLY after a policy is frozen (not the case here).

## Decision P59 - Independent AI-assisted semantic-plausibility audit packages prepared (2026-09-18)

- **Status:** ADOPTED (mission OPENCODE_PREPARE_BLINDED_AI_SEMANTIC_AUDIT_2026-09-18; ZERO API; ZERO model calls)
- **Context:** the human semantic-proxy audit remains **AWAITING_HUMAN_RATINGS**; an independent, fully blinded AI-assisted semantic-plausibility audit was requested as a parallel descriptive reliability check of two assistants (ChatGPT + Claude) without touching the human packets.
- **Decision:** build a derived AI-blinded package under `research/semantic_audit/ai_blinded_v1/`: 25 cases → neutral case IDs (AI-CASE-001..025); 361 file-level rows (AI-ROW-0001..0361: 111 `historical_changed_file` + 250 `omitted_candidate_file`) with neutral candidate IDs; hide method/arm name, Route B, BM25/Graph/Composite/Random/Oracle labels, rank position, top-ranked vs matched-random wording, thesis outcomes, and any aggregate metric; preserve original arms ONLY in a sealed private mapping (`sealed_mapping.json`, never sent to raters); 5 fresh-chat batches per rater with different fixed seeds (chatgpt 20260919, claude 20260920; neutral seeds 20260918); strict JSON output schema (`AI_AUDIT_OUTPUT_SCHEMA.json`); agreement script (`scripts/semantic_ai_audit_agreement.py`) computing exact row agreement, Cohen's kappa (nominal/unweighted), confusion matrix, agreement by label, abstention rate, role-split agreement (historical-changed vs omitted-candidate), case-level agreement for proxy_quality / omitted_candidate_semantic_impact / mixed_tangled_commit, disagreement list, and a deterministic 10-row agreement sample; unit tests (15 PASS); human minimal-spot-check generator + placeholder (`human_spotcheck_form.csv`).
- **Explicit status recorded:** this is an **independent AI-assisted semantic plausibility audit**; it does NOT replace human semantic gold; ChatGPT and Claude MUST be run in separate fresh chats per batch; neither rater may see the other's labels before freeze; the private arm mapping is never sent to either model.
- **Rules:** do NOT alter labels to increase agreement; do NOT collapse categories before reporting; do NOT call inter-model agreement human agreement; do NOT use thesis performance results.
- **Rejected:** modifying the original 25 human packets/forms/manifests; any model/API call; opening INTERNAL_TEST/RESERVE; using thesis results.
- **Evidence:** research/semantic_audit/ai_blinded_v1/* (preparation_manifest.json, sealed_mapping.json, 10 batch dirs), scripts/semantic_ai_audit_{prepare,agreement,human_spotcheck}.py, tests/unit/test_semantic_ai_audit.py (15/15), reports/AI_SEMANTIC_AUDIT_ANALYSIS_PROTOCOL.md.
- **Revisit:** after the 10 fresh-chat runs are returned → ingest + agreement → human spot-check.

## Decision P60 - AI-assisted semantic audit agreement + post-hoc sensitivity closure (2026-09-18)

- **Status:** ADOPTED (mission OPENCODE_AI_SEMANTIC_AUDIT_ANALYSIS_2026-09-18; ZERO API; ZERO model calls)
- **Context:** the 10 frozen rater outputs (5 ChatGPT + 5 Claude fresh-chat batches) were returned; the prepared ai_blinded_v1 package needed validation, agreement analysis, a post-hoc sensitivity check, and a human minimal spot-check artifact.
- **Decision:** treat all 10 outputs as frozen; validate byte-exactly as received (2 files — chatgpt_batch_02/04 — had unescaped inner double-quotes inside evidence strings; created syntax-only normalized copies, originals untouched, full content preservation verified by tolerant-parse equality); ingest via scripts/semantic_ai_audit_agreement.py against the sealed mapping (exact agreement 0.6981, Cohen's kappa 0.5579, confusion matrix, agreement-by-label, abstention 0/0, role split historical 0.8468 vs omitted 0.6320, case-level proxy 0.56 / omitted-impact 0.48 / tangled 0.68, 109 disagreements, deterministic 10-row sample seed 20260918); run a clearly labeled POST-HOC sensitivity analysis (scripts/semantic_ai_audit_posthoc.py) separating sparse_omitted_and_historical_changed (n=15, kappa 0.17) from sparse_omitted_and_outside_historical_diff (n=235, kappa 0.26) because some rationales interpret "omitted" as "absent from the historical diff"; report descriptively, per rater and NEVER pooled as gold, top-ranked vs matched-random relevance outside the historical diff (ChatGPT 0.193 vs 0.099; Claude 0.053 vs 0.008); generate the 119-row human minimal spot-check form (109 disagreements + 10 deterministic agreement rows) without fabricating human judgments; update PROGRESS/DECISIONS/00_CURRENT_RESEARCH_STATE + ledgers.
- **Explicit status recorded:** this is an **independent AI-assisted semantic plausibility audit / model-based semantic sensitivity analysis**, NOT human semantic gold and NOT expert adjudication; inter-model agreement is NOT human agreement; frozen labels NOT altered.
- **Rules:** do NOT rerun/relabel/reconcile the raters; do NOT expose either rater to the other's labels; do NOT collapse categories; do NOT use thesis results.
- **Rejected:** modifying any frozen label/confidence/rationale/evidence/case judgment; claiming human agreement; any model/API call; opening INTERNAL_TEST/RESERVE.
- **Evidence:** reports/ai_semantic_audit_{json_validation,agreement_result,posthoc_result}.json, reports/AI_SEMANTIC_AUDIT_AGREEMENT_REPORT.md, research/semantic_audit/ai_blinded_v1/rater_outputs/ (10 files), research/semantic_audit/ai_blinded_v1/human_spotcheck_form.csv (119 rows), scripts/semantic_ai_audit_posthoc.py, tests/unit/test_semantic_ai_audit.py (19/19).
- **Revisit:** after the human minimal spot-check is reviewed; the human two-rater + adjudicator audit remains AWAITING_HUMAN_RATINGS.

## Decision P61 - Oracle-gap decomposition + bidirectional bounded set repair — BIDIRECTIONAL_HEADROOM_ONLY (2026-09-18)

- **Status:** ADOPTED (mission OPENCODE_ORACLE_GAP_BIDIRECTIONAL_REPAIR_MISSION_2026-09-18; ZERO API; ZERO model calls; exploratory DEVELOPMENT after the frozen P2 Phase-1 negative closure)
- **Context:** P2 Phase-1 NEGATIVE is frozen/immutable. The remaining question is the file-level Oracle/F1 gap: Sparse recalls only ~21-25% of proxy positives on DEVELOPMENT and Route-B add-only lowers file-level F1.
- **Decision:** verify the confirmatory error budget from frozen records (matches the working diagnostic: Sparse TP=51/FP=104/FN=199 F1=0.252; verifier B=5 F1=0.239, acceptance precision 0.105); compute DEVELOPMENT oracle ceilings (Oracle-Add ALL 0.8674/0.8291; Oracle-Drop ALL 0.3956/0.3492; bidirectional to F1 1.0; **F1=0.85 NOT add-only-reachable on Saleor**); decompose the gap (first-pass recall loss dominant, review false-acceptance second, ranking third, budget loss ~0); test observable FP-pruning (signal ~ random control); simulate a simple ZERO-LLM bidirectional candidate (BBSR) and apply the progression gate.
- **Result:** progression gate FAIL on both repos (heuristic BBSR does not beat Sparse or add-only Route-B; recall degrades; DROP only helps at K>=5 and only under perfect oracle review). **Decision = BIDIRECTIONAL_HEADROOM_ONLY**: oracle headroom exists but cheap observable signals cannot realize the DROP side. No new verifier calls authorized.
- **Explicit status:** DEVELOPMENT-only; spent djangoCMS INTERNAL_TEST used ONLY as labelled POST-HOC sanity; djangoCMS RESERVE + Saleor INTERNAL_TEST/RESERVE sealed; F1>=0.85 treated as an aspirational target, not a tuning stop rule; no novelty claim (BBSR is an internal working label; literature check found no verified DIRECT_COMPETITOR for bounded ADD+DROP set repair in the 41-entry ledger).
- **Rejected:** reopening P2 Phase-1; tuning on the spent INTERNAL_TEST; any model/API call; neural/RL; new LocAgent spend; forcing F1 0.85.
- **Evidence:** reports/ORACLE_GAP_{ERROR_DECOMPOSITION,F1_CEILING_AND_BUDGET_SURFACE,BIDIRECTIONAL_REPAIR_FINAL_REPORT,INDEPENDENT_AUDIT}.md + JSONs, reports/SELECTED_SET_FP_PRUNING_FEASIBILITY.md, reports/BBSR_DEVELOPMENT_SIMULATION.md, reports/LOCAGENT_FAIR_COMPARISON_PLAN_V2.md, reports/BIDIRECTIONAL_SET_REPAIR_LITERATURE_CHECK.md, scripts/oracle_gap_*.py (10), tests/unit/test_oracle_gap.py (16/16), reports/oracle_gap_gates_validation.json.
- **Revisit:** after a first-pass-recall improvement candidate is defined on DEVELOPMENT (the measured dominant bottleneck); human semantic-audit ratings remain an open blocker.

## Decision P62 - README reorganization + research journey (documentation architecture) (2026-09-18)

- **Status:** ADOPTED (mission OPENCODE_README_RESEARCH_JOURNEY_REORG_2026-09-18; T2 docs-only; ZERO API)
- **Context:** the README had grown into a large chronological dump with stale claims (Saleor "future", LocAgent "adapter pending", Route-B "development only", P2 "conditional", semantic audit "preparation", old 2026-09-16/17 header), making the current state hard to find in ~5 minutes.
- **Decision:** adopt a documentation architecture with fixed roles: **README.md** = concise navigation / current headline overview (11 mandated sections); **00_CURRENT_RESEARCH_STATE.md** = detailed scientific truth; **PROGRESS.md** = current execution truth; **DECISIONS.md** = append-only decisions; **docs/RESEARCH_JOURNEY.md** (new) = chronological tried/learned/ruled-out history with revisit triggers; **reports/** = authoritative experiment evidence. README reorganized so stale chronology cannot dominate the top again; stale claims replaced with current status; docs/RESEARCH_JOURNEY.md created with 17 milestones, negatives framed as search-space reductions.
- **Rules:** do not change scientific numbers; do not delete historical evidence; do not create a parallel README; link to reports instead of duplicating tables.
- **Rejected:** deleting historical reports; moving scientific tags; rewriting 00_CURRENT_RESEARCH_STATE.md scientific claims; any model/API call.
- **Evidence:** README.md, docs/RESEARCH_JOURNEY.md (17 rows), DECISIONS.md P62, PROGRESS.md (docs task block).
- **Revisit:** when the First-Pass Recall Bottleneck study produces new milestones; add rows to docs/RESEARCH_JOURNEY.md as experiments complete.
## Decision P63 - First-pass recall bottleneck: RECALL_SIGNAL_HEADROOM_ONLY (2026-09-18)

- **Status:** ADOPTED (mission OPENCODE_FIRST_PASS_RECALL_BOTTLENECK_2026-09-18; T3 DEVELOPMENT; ZERO API; ZERO model/API calls)
- **Context:** the Oracle-gap closure (§61) identified first-pass recall as the dominant file-level bottleneck (75-79% of proxy positives missed; Oracle-Add headroom +0.55-0.57 F1). This mission explains WHY Sparse misses those files and tests whether a simple complementary ADD signal recovers them.
- **Frozen baseline (verified):** djangoCMS DEV 174 (Sparse TP125/FP155/FN382, F1 0.3177), Saleor DEV 149 (TP99/FP193/FN369, F1 0.2605); Route-B composite macro ORR djangocms 0.0464/0.1177/0.1633/0.2512 == frozen route_b_v2_results.json.
- **FN taxonomy (deterministic, parent-visible):** djangoCMS DIRECT_LEXICAL 95 (24.9%), HISTORY_COCHANGE 86 (22.5%), NO_OBSERVABLE_SIGNAL 87 (22.8%), DOWNSTREAM_CONSUMER 64 (16.8%), INDIRECT_2HOP 43 (11.3%); Saleor DIRECT_LEXICAL 264 (71.5%), DOWNSTREAM_CONSUMER 68 (18.4%).
- **S006-like pattern = GENERAL_PATTERN:** downstream-consumer flag on 58.9% (djangocms) / 82.1% (saleor) of FNs; consumer-or-provider 64.7%/91.1%; direct-1-hop FNs are 98.6%/100% lexically silent. The S006 `plugins.py`-style indirect-utility miss is a recurring, cross-repo structural miss.
- **Source ceilings @K=5:** GRAPH_REVERSE_1HOP ORR 0.558/0.724; UNION_CONSUMER_PROVIDER 0.605/0.802; UNION_2HOP+COCHANGE+SIBLING 0.670/0.778; UNION_ALL 0.725/0.870; BM25 ceiling is just the budget headroom (0.929/0.881). Candidate availability is NOT the binding constraint.
- **3 simple ADD queues (frozen):** Q1 BM25+ReverseDependency (bm25+consumer), Q2 BM25+ProviderConsumerSupport (bm25+consumer+provider), Q3 BM25+ComplementaryUnion (bm25+2hop+cocchange+sibling). NO queue beats Route-B at matched budget (B=5 Δ −0.011/+0.001, −0.025/−0.001, −0.086/−0.209). Q3 is much worse because the sibling flag dilutes ranking.
- **Oracle-reviewer simulation:** perfect reviewer accepts FNs in top-B → final F1 ≈ 0.44/0.43 @B=5 vs Oracle-Add 0.72/0.64. Dominant remaining loss = RANKING; reviewer acceptance second; availability NOT the gap.
- **Progression gate = FAIL on all queues** (C1 no material ORR gain on both repos; Q3 additionally fails fold direction). **Decision: RECALL_SIGNAL_HEADROOM_ONLY** — headroom exists (oracle + availability ceilings) but simple binary-flag queues cannot realize it; NO verifier calls authorized by this mission.
- **Rejected:** neural/learned/risk models; tuning until F1 0.85; using the spent djangoCMS INTERNAL_TEST for selection; opening djangoCMS RESERVE or Saleor INTERNAL_TEST/RESERVE; claiming a queue improves F1 while ORR rises without the View A/B separation; any model/API call.
- **Evidence:** reports/FIRST_PASS_RECALL_{BASELINE_FREEZE,FINAL_REPORT}.md, reports/FN_{TAXONOMY_DEVELOPMENT,SOURCE_SPECIFIC_RECALL_CEILINGS,ADD_QUEUE_EVALUATION,PROGRESSION_GATE,INDEPENDENT_AUDIT}.md + JSONs, src/benchmark/recall/, scripts/fn_*.py (6), tests/unit/test_recall_bottleneck.py (19/19), reports/fn_independent_audit.json (19/19).
- **Revisit:** a bounded verifier-ranked expansion (Route-B top-B + reverse-1hop consumer pool) on DEVELOPMENT, using the existing frozen verifier protocol/budget, is the natural next instrument and requires a separate authorized mission.

## Decision P64 - Ranking bridge + bounded semantic freeze: CHEAP_RANKING_CLOSED_FOR_NOW (2026-09-18)

- **Status:** ADOPTED (mission OPENCODE_RANKING_BRIDGE_AND_BOUNDED_SEMANTIC_FREEZE_2026-09-18; T3 DEVELOPMENT; ZERO API; ZERO model/API calls)
- **Context:** the First-Pass Recall closure (P63) established RECALL_SIGNAL_HEADROOM_ONLY: availability is high (reverse-1hop 0.558/0.724 @K=5, UNION_ALL 0.725/0.870) but simple binary-flag ADD queues cannot order the pool; the dominant remaining loss is RANKING. This mission asked ONE last bounded question: can quantitative structural support (counts, not binary flags) order the high-coverage reverse-1hop pool better, without learned models or LLMs?
- **Section-1 reconfirmation freeze (exact):** reproduced frozen Route-B macro ORR (0.0464/0.1177/0.1633/0.2512 and 0.0775/0.1576/0.2369/0.3173), BM25-only, reverse-1hop/consumer+provider/union-all availability, Oracle-Add F1 (0.841/0.782), oracle-reviewer Route-B F1 (0.441/0.424) — every verification flag PASS (
eports/fn_quant_ranking_bridge_baseline_freeze.json).
- **Section-2 (exactly three transparent formulas, frozen before outcome inspection):** R1 BM25+RevSupport, R2 BM25+BidirSupport, R3 BM25+BidirNorm. All use only parent-visible features (normalized BM25 + directed seed-support counts). Typed-edge support is NOT available (frozen graph exposes only untyped [src,dest] edges), documented in provenance. Results at B=5: best R1 djangoCMS +0.034 (0.197) but Saleor −0.020 (0.217); R2/R3 smaller; NO formula materially beats Route-B on BOTH repos (gate c1/c2 fail on all three); folds not majority positive; artifact-free; naive-F1 not clearly worse.
- **Decision: CHEAP_RANKING_CLOSED_FOR_NOW** (negative frozen; no fourth formula invented in this mission). The bounded semantic middle layer is the next instrument.
- **Frozen protocol + budget PREPARED, NOT EXECUTED:** docs/BOUNDED_SEMANTIC_RERANK_VERIFY_PROTOCOL_FROZEN.md (Route-B top-10 ∪ reverse-1hop consumers, dedupe, deterministic pre-order, hard pool cap C=40; qwen3-coder/OpenRouter temp 0 cap 512; strict JSON; fail-closed; no result-based retries; ≤30 tasks/repo pilot; matched-budget Arm A/B/C; primary + safety metrics; pre-registered stop rule) +
eports/BOUNDED_SEMANTIC_EXPANSION_BUDGET_FREEZE_DRAFT.md (≤300 calls / ≤300,000 tokens / ≤.30 / ≤60 min hard stop; per-call reservation ledger). NO call made.
- **P2/adaptive-k:** P2 Phase-1 COMPLETE, NEGATIVE, frozen; adaptive budget NOT the current bottleneck and NOT active work; Shichao-Zhang / adaptive-k / demand-driven-k = FUTURE WORK, GATED (revisit only after a stable ranking/recovery signal) — line gated, not deleted.
- **Future-work terminology correction:** "multi-language" has two meanings — (A) cross-language/cross-repository (different repos, different ecosystems) vs (B) polyglot SINGLE-repository (one repo, multiple production languages, real cross-language coupling). Ambiguous roadmap wording renamed cross-language + polyglot-repository generalization. grafana/grafana added as FUTURE feasibility candidate ONLY (Go backend + TS frontend; NOT scientifically accepted; requires feasibility audit, per-language universe, cross-language coupling representation, >=60 eligible commits, mixed-language strata, no leakage).
- **Gap-reduction roadmap ladder documented** (
eports/GAP_REDUCTION_ROADMAP.md): Stage 1 DONE (Sparse + Route-B), Stage 2 DONE (FN anatomy, ranking bottleneck), Stage 3 THIS MISSION (cheap quant bridge = negative), Stage 4 NEXT IF AUTHORIZED (bounded semantic rerank/verify), Stage 5 freeze+confirmatory if Stage 4 succeeds, Stage 6 adaptive-k later (gated), Stage 7 generalization (cross-language + polyglot), Stage 8 repository-agent only if needed.
- **Rejected:** neural/learned/RL rankers; a fourth formula in this mission; any model/API call; opening sealed sets; using the spent djangoCMS INTERNAL_TEST; tuning until a target F1; claiming ORR-only success without the F1 guard.
- **Evidence:** reports/QUANT_STRUCTURAL_RANKING_BRIDGE_REPORT.md + fn_quant_ranking_bridge.json + fn_quant_ranking_bridge_gates.json + fn_quant_ranking_bridge_baseline_freeze.json + FN_QUANT_RANKING_BRIDGE_AUDIT.md/audit.json (25/25), docs/BOUNDED_SEMANTIC_RERANK_VERIFY_PROTOCOL_FROZEN.md, reports/BOUNDED_SEMANTIC_EXPANSION_BUDGET_FREEZE_DRAFT.md, reports/GAP_REDUCTION_ROADMAP.md, src/benchmark/recall/quant_rankers.py (+rev_support/fwd_support in data.py), scripts/fn_quant_ranking_bridge*.py (2), tests/unit/test_quant_ranking_bridge.py (12/12), affected suites 35/35.
- **Revisit:** execute the frozen Stage-4 bounded semantic pilot ONLY under explicit user authorization (exact sentence in the budget draft §7); retest R2/R3 if a typed-edge graph extractor ever lands; revisit adaptive-k after a stable ranking signal.

## Decision P65 - Bounded semantic expansion pilot (AUTHORIZED): BOUNDED_SEMANTIC_NEGATIVE_FROZEN (2026-09-18)

- **Status:** ADOPTED (authorized Stage-4 execution of the frozen protocol; DEVELOPMENT; real pilot)
- **Context:** the user explicitly authorized the frozen bounded-semantic rerank/verify pilot (<=300 calls / <=300,000 tokens / <=.30 / <=60 min, qwen3-coder, DEV only, sealed sets sealed) with cost minimization as a first-class constraint (ceilings = safety limits, expected spend near the frozen projection ~.035; no result-dependent retries; no prompt tuning after outcomes; no fallback provider; STOP at the preregistered gate).
- **Frozen before call 1:**
esearch/bounded-semantic-expansion/pilot_registration_freeze.json — 60 DEVELOPMENT tasks (30 djangoCMS + 30 Saleor; seeded 20260918; >=1 Sparse FN and omitted >=5); Arm B pool = Route-B composite top-10 UNION reverse-1hop consumers, dedupe, pre-order desc bm25 then asc path, hard cap 40 (verified <=40 on all); Arm A = frozen Route-B verifier (4 calls/task, B in {1,3,5,10}); strict JSON schemas; per-call reservation ledger.
- **Real run (AUTHORIZED):** 300 calls (Arm A 240 + Arm B 60), 106,325 tokens, .0444, 553.6 s; budget respected; sidecars 300/300 (0 hash mismatches); 6 Arm B schema-invalid calls recorded fail-closed (no retries). One harness crash mid-run (progress-print bug only) was fixed and the pilot resumed from disk WITHOUT re-dispatching any completed call (241 records resumed; no double spend).
- **Result (pooled file-level, B=5):** djangoCMS Arm A ORR 0.111 / Arm B 0.250; naive-F1 0.396 / 0.327; Saleor Arm A 0.334 / Arm B 0.357; naive-F1 0.304 / 0.270.
- **Preregistered gate = FAIL → decision BOUNDED_SEMANTIC_NEGATIVE_FROZEN:** c1 ORR materially > Arm A on BOTH repos FAILS (Saleor +0.023 < 0.05; djangoCMS +0.139 passes); c3 naive final F1 not materially worse FAILS on djangoCMS (-0.069). Arm B raises ORR but NOT materially on Saleor, and on djangoCMS it materially lowers naive final F1 — the protocol explicitly forbids claiming this as success. No prompt/schema tuning after outcomes.
- **Rejected:** any prompt/schema tuning; result-based reruns; fallback provider; re-opening the frozen protocol mid-run; any confirmatory/INTERNAL_TEST/RESERVE use; a success claim on ORR-only.
- **Evidence:** reports/BOUNDED_SEMANTIC_EXPANSION_{PILOT_REPORT,CLOSURE_REPORT,AUDIT}.md + bounded_semantic_expansion_{metrics,gate,audit}.json, research/bounded-semantic-expansion/* (registration freeze, results, ledger, runs/ raw + sha256), scripts/bounded_semantic_expansion_{pilot,analyze,audit}.py, affected suites 31/31, audit 8/8.
- **Revisit:** Stage 4 of the gap-reduction ladder is closed NEGATIVE. Any future bounded semantic instrument must be pre-registered with a precision-safe acceptance rule (e.g., verifier-approved AND ranked-gated) and requires its own explicit authorization + budget before any API spend.

## Decision P66 - Precision-safe acceptance feasibility + protocol freeze (2026-09-18)

- **Status:** ADOPTED (mission PRECISION_SAFE_ACCEPTANCE_FEASIBILITY_PROTOCOL_FREEZE_2026-09-18; T3 DEVELOPMENT; ZERO API; ZERO model/API calls)
- **Context:** Stage 4 (P65) closed NEGATIVE: Arm B (bounded semantic rerank over the expanded pool) raises ORR but carries an FP tail that materially lowers naive F1 on djangoCMS. P65's revisit condition — a precision-safe acceptance rule pre-registered before any further semantic API spend — is executed here as a ZERO-API failure anatomy + feasibility + protocol freeze.
- **Failure anatomy (from the frozen 300-call record):** (1) Arm-B cumulative candidate precision by semantic rank is flat-low on djangoCMS (0.125 rank1 → 0.093 rank5) and monotonically decaying on Saleor (0.346 → 0.177 → 0.153); (2) at B=5 Arm B adds 14/26 FNs but 119/119 FPs (candidate precision 0.105/0.179 vs Arm A 0.143/0.256); (3) the FP tail is split across BOTH pool sources (dc 68/51, saleor 71/48 top-10 vs consumer-only) — no single source is the FP problem, the acceptance layer is; (4) pool cap C=40 loses 10 (dc) + 29 (saleor) FNs (cap-40 covers 52%/54%, cap-80 66%/60%, cap-120 69%/69%); (5) 6/6 schema-invalid Arm-B calls are non-pool-path hallucinations and the frozen analyzer granted them partial credit; (6) B=10 recovery is consistent (5/5 positive folds BOTH repos; Saleor mean per-task delta +0.146) — inspection-depth signal, DEVELOPMENT motivation only.
- **Feasibility (POST-HOC, exactly ONE principled family RANK → VERIFY → VARIABLE ACCEPT):** the AND-rule (semantic top-K AND frozen Arm-A B=10 verifier approval) improves candidate precision (dc 0.105→0.146, saleor 0.179→0.222) and recovers Arm-B's F1 loss on dc (0.324→0.407) — but does NOT beat the frozen Route-B verifier on F1 on either repo (dc 0.407 vs 0.414; saleor 0.263 vs 0.287) because the frozen verifier is uncalibrated for acceptance (8.6–14% approval precision). **Explicit insufficiency stated:** the frozen verifier never saw reverse-1hop-only candidates; no existing record can assess a verifier on them. Verdict: the FAMILY is justified; the SPECIFIC frozen verifier is not.
- **One frozen next protocol (docs/PRECISION_SAFE_ACCEPTANCE_PROTOCOL_FROZEN.md):** Sparse → deterministic expanded pool (Route-B top-10 ∪ reverse-1hop consumers, cap C=80, DEV-derived) → bounded semantic ranking (1 call/task) → top-K inspection set (K=10, DEV-derived) → strict fixed-length boolean-vector verifier over K (1 call/task; candidate-ID enum schema; NO partial credit) → variable accepted additions (0..K) → final file set; baseline = frozen Route-B verifier at B∈{1,3,5,10}; fresh disjoint DEVELOPMENT sample (seed 20260919, 30/repo, 60 Stage-4 case_ids excluded; 123 dc + 97 saleor fresh eligible remain); gate c1–c7 on BOTH repos (ORR > ArmA+0.05; ≥3/5 folds; naive F1 ≥ ArmA−0.05; candidate precision ≥ ArmA; leak-free; ≥90% schema-valid; within budget). Budget draft (reports/PRECISION_SAFE_ACCEPTANCE_BUDGET_FREEZE_DRAFT.md): expected ~360 calls / ~140k tokens / ~$0.055; hard ceilings 400 calls / 300,000 tokens / $0.15 / 60 min; exact authorization sentence in §7.
- **Rejected:** rerunning/tuning Stage 4; threshold sweeping; more than one acceptance formula; claiming B=10 as a retroactive endpoint; calling B=10 a Stage-4 success; opening sealed sets; any model/API call; "RANK → TAKE FIRST B" acceptance; designing multiple alternative protocols.
- **Evidence:** reports/PRECISION_SAFE_ACCEPTANCE_FEASIBILITY_2026-09-18.md, reports/precision_safe_feasibility_metrics.json, reports/PRECISION_SAFE_ACCEPTANCE_AUDIT.md + precision_safe_feasibility_audit.json (11/11), docs/PRECISION_SAFE_ACCEPTANCE_PROTOCOL_FROZEN.md, reports/PRECISION_SAFE_ACCEPTANCE_BUDGET_FREEZE_DRAFT.md, scripts/precision_safe_feasibility_{anatomy,audit}.py, tests/unit/test_precision_safe_feasibility.py (13/13).
- **Revisit:** execute the frozen precision-safe pilot ONLY under the exact authorization sentence (budget draft §7); if the gate fails, freeze the negative. Stage 5 (confirmatory) remains gated on a successful DEVELOPMENT pilot.

## Decision P67 - Precision-safe acceptance pilot (AUTHORIZED): PRECISION_SAFE_ACCEPTANCE_FAIL (2026-09-18)

- **Status:** ADOPTED (authorized execution of the frozen precision-safe acceptance protocol; DEVELOPMENT; real pilot)
- **Context:** the user authorized the frozen RANK -> VERIFY -> VARIABLE ACCEPT pilot (docs/PRECISION_SAFE_ACCEPTANCE_PROTOCOL_FROZEN.md) under the budget in reports/PRECISION_SAFE_ACCEPTANCE_BUDGET_FREEZE_DRAFT.md (<=400 calls / <=300,000 tokens / <=.15 / <=60 min, qwen3-coder @ OpenRouter deepinfra/turbo, DEVELOPMENT only, sealed sets sealed, no result-based retries, no prompt tuning, no fallback provider, STOP at the preregistered gate).
- **Frozen before call 1:** research/precision-safe-acceptance-pilot/pilot_registration_freeze.json — 60 DEVELOPMENT tasks (30 djangoCMS + 30 Saleor; seed 20260919; Stage-4's 60 case_ids EXCLUDED); Arm B pool = Route-B top-10 UNION reverse-1hop consumers, dedupe, pre-order desc bm25 asc path, cap 80; K=10; Arm A = exact frozen Stage-4 Route-B verifier (4 calls/task); candidate-ID enum + uniqueness rank schema; fixed-length boolean-vector verify schema; per-call reservation ledger.
- **Real run (AUTHORIZED):** 357 dispatched calls (240 Arm A + 60 rank + 57 verify; 3 rank abstentions with no inspection set -> fail-closed zero additions), 176,060 tokens, .0648, 718.8 s total wall (655.7 s execution + reload) — all ceilings respected; sidecars 357/357 (0 hash mismatches); resume-from-disk 357 with no double spend; **0/357 schema-invalid dispatched calls** (vs Stage-4 6/60) — the candidate-ID enum + uniqueness schema eliminated hallucinated paths.
- **Result @B=5:** djangoCMS Arm A ORR 0.2225 / Arm B 0.1523 (delta -0.0702); cand-prec 0.1406 -> 0.2500; naive F1 0.2176 -> 0.2604. Saleor Arm A 0.1278 / Arm B 0.2029 (delta +0.0751); cand-prec 0.0882 -> 0.1163; naive F1 0.1744 -> 0.1972.
- **Preregistered gate = FAIL -> decision PRECISION_SAFE_ACCEPTANCE_FAIL (negative frozen):** djangoCMS c1 (ORR -0.0702 < +0.05) and c2 (2/5 folds) FAIL; Saleor c1 PASS (+0.0751) and c2 PASS (5/5); c3/c4/c5/c6/c7 PASS on BOTH repos. The precision-safe layer eliminated the Stage-4 "ORR up, F1 down" failure (F1 and precision improve on BOTH repos; variable acceptance removed the FP tail) and achieved material Saleor recovery, BUT on djangoCMS the conservative verifier over-rejects — it misses the easy M=1 recoveries (3 tasks where Arm A recovered 1/1 and Arm B approved a different non-FN candidate). No prompt/schema/threshold tuning after outcomes.
- **Rejected:** any prompt/schema/threshold tuning to chase ORR; result-based reruns; fallback provider; opening sealed sets; reusing the Stage-4 sample; claiming the family is dead (this is a FAIL of THIS frozen instantiation under the conjunctive gate); any confirmatory/INTERNAL_TEST/RESERVE use.
- **Evidence:** reports/PRECISION_SAFE_ACCEPTANCE_{CLOSURE_REPORT,PILOT_REPORT,AUDIT}.md + precision_safe_acceptance_{metrics,gate,audit}.json, research/precision-safe-acceptance-pilot/* (registration freeze, results, ledger, runs/ raw + sha256), scripts/precision_safe_acceptance_{pilot,analyze,audit}.py, tests/unit/test_precision_safe_acceptance.py (9/9), affected suites 53/53, audit 11/11.
- **Revisit:** Stage 5 (freeze method + fresh confirmatory) NOT reached. Any future instrument that keeps the verifier's precision/F1 gains while restoring djangoCMS ORR is a NEW protocol (e.g., calibrated acceptance criterion) requiring its own freeze, sample discipline, budget, and explicit authorization, and must still be gated on BOTH repositories.

## Decision P68 - Bounded cheap-semantic family closure: BOUNDED_CHEAP_SEMANTIC_CLOSED_FOR_NOW (2026-09-19)

- **Status:** ADOPTED (mission STRONG_LOCALIZATION_SIGNAL_BRIDGE_2026-09-19; T3 DEVELOPMENT; ZERO API)
- **Context:** the accumulated evidence closes the currently tested bounded generic-Qwen semantic family: (1) the cheap structural ranking bridge is negative (CHEAP_RANKING_CLOSED_FOR_NOW, P64); (2) the bounded semantic Stage 4 pilot is negative (BOUNDED_SEMANTIC_NEGATIVE_FROZEN, P65); (3) the precision-safe bounded semantic Stage 4b pilot is negative under its preregistered gate (PRECISION_SAFE_ACCEPTANCE_FAIL, P67). No reproducibility/audit defect was found in this mission (Stage-4b point estimates reproduce exactly; independent audit 11/11). The descriptive statistical closure (POST-HOC, task-paired bootstrap, 10,000 resamples, fixed seed 20260919) added uncertainty quantification but did NOT change the frozen verdict.
- **Decision:** record **BOUNDED_CHEAP_SEMANTIC_CLOSED_FOR_NOW**, scoped narrowly: *no further incremental generic-Qwen prompt / verifier / threshold / acceptance-rule / K tuning is scientifically justified on the same DEVELOPMENT evidence under the tested bounded semantic family.* This does NOT mean semantic localization is impossible, specialized localization models are ineffective, repository agents are ineffective, or future fundamentally different signals are forbidden. Stage 4 and Stage 4b are NOT re-tuned; no verifier-v3; no threshold sweeps.
- **Rejected:** tuning Stage 4/4b; creating verifier-v3; sweeping thresholds; reopening P65/P66/P67.
- **Evidence:** reports/STAGE4B_STATISTICAL_CLOSURE_2026-09-19.md, reports/stage4b_bootstrap_ci.json, research/strong-localization-signal/stage4b/task_level.json; affected suites + audit in the mission.
- **Revisit:** a fundamentally different signal family (specialized embedding, repository memory, reranker, agentic) — the specialized embedding line is recorded separately in P69/P70.

## Decision P69 - SweRank training-provenance verdict: TRAINING_PROVENANCE_INSUFFICIENT_TO_RULE_OUT_OVERLAP (2026-09-19)

- **Status:** ADOPTED (mission STRONG_LOCALIZATION_SIGNAL_BRIDGE_2026-09-19; T3; ZERO API)
- **Context:** before treating SweRank results as scientific evidence, the SweLoc training corpus (top ~11k PyPI Python repos, SWE-Bench/LocBench excluded, 3,387 curated repos; paper arXiv 2505.07849 §3.1) was audited against djangoCMS/Saleor. The 3,387-repo manifest and the training data are NOT publicly released; no SweLoc HF dataset exists; the paper's full text contains no "django"/"saleor" mention but does not enumerate repos; djangoCMS/Saleor are NOT in the SWE-Bench/LocBench exclusion sets; a PyPI download-rank check was attempted but the PyPI API was unreachable locally.
- **Decision:** **TRAINING_PROVENANCE_INSUFFICIENT_TO_RULE_OUT_OVERLAP** (verdict C). SweRankEmbed-Small is evaluated ONLY as an **EXTERNAL PRETRAINED DIAGNOSTIC BASELINE**; its results are NOT clean unseen generalization and must carry the contamination/pretraining label everywhere.
- **Rejected:** assuming clean pretraining; claiming unseen generalization; treating absence of paper mention as absence from the corpus.
- **Evidence:** reports/SWERANK_TRAINING_PROVENANCE_AUDIT.md.
- **Revisit:** if the SweLoc repo manifest or training file is released → re-run the membership check → upgrade to verdict A or B.

## Decision P70 - SweRankEmbed-Small DEV evaluation: SWERANK_EMBED_PASS (2026-09-19)

- **Status:** ADOPTED (mission STRONG_LOCALIZATION_SIGNAL_BRIDGE_2026-09-19; T3 DEVELOPMENT; ZERO API; EXTERNAL PRETRAINED DIAGNOSTIC BASELINE)
- **Context:** a NEW specialized issue-localization embedding signal was evaluated under a frozen protocol (docs/SWERANK_EMBED_BASELINE_PROTOCOL_FROZEN.md, frozen BEFORE any target-aware metric inspection) on the FULL legal DEVELOPMENT populations (djangoCMS 174 + Saleor 149), pinned model revision `745d2a06103a66d3cfa600aa52fc0d3523010daa`, frozen MAX-file adapter, parent-only queries, Route-B matched pool + tie-break. Comparator/K frozen BEFORE results (Route-B primary, BM25 secondary, K=5 primary operating point; clarification recorded before any metric inspection).
- **Result @B=5 (vs frozen Route-B composite):** djangoCMS F1 0.226→0.280 (+0.054), P +0.039, R +0.089, FNR −0.089, macro ORR 0.163→0.291, candP 0.071→0.123; Saleor F1 0.237→0.288 (+0.052), P +0.038, R +0.083, FNR −0.083, macro ORR 0.237→0.327, candP 0.106→0.158. **Every metric improves at every B on BOTH repos; all six paired-bootstrap 95% CIs @B=5 exclude zero on BOTH repos.** Efficiency: 0 API calls, $0, local CPU; one-time corpus encode (49,705 units) dominates wall (~6.6 h); marginal per-task cost after indexing ~0.1 s. Independent audit 11/11 (recomputes formulas, ORR, gate, folds, CIs, leakage, pin, efficiency from raw JSONs without importing the analyzer).
- **Decision:** **SWERANK_EMBED_PASS** on the frozen gate (A–E on both repos). The method is FROZEN as the candidate-ranking signal (Sparse write set + ranked additions). Next step (frozen selection): **A — use SweRankEmbed-Small as the replacement candidate-ranking signal inside the bounded architecture** (zero-API, direct continuation); option B (official SweRankLLM listwise reranker, 7B LLM) is documented with a cost/compute plan but NOT executed (needs a new frozen budget + authorization). Stage 5 confirmatory remains gated.
- **Explicit label:** EXTERNAL PRETRAINED DIAGNOSTIC BASELINE — training provenance is verdict C (P69); PASS is a diagnostic result on DEVELOPMENT, not clean unseen generalization, not a confirmatory claim, not a head-to-head with external paper numbers.
- **Rejected:** tuning aggregation/K/query/normalization/thresholds; selecting K/comparator after outcomes; claiming clean generalization; calling the reranker; opening sealed sets; reinterpreting P65/P66/P67.
- **Evidence:** reports/SWERANK_EMBED_DEVELOPMENT_REPORT.md, research/strong-localization-signal/swerank/{metrics,gate,efficiency,task_rankings,model_pin}.json, reports/swerank_independent_audit.json + SWERANK_INDEPENDENT_AUDIT.md, reports/STRONG_LOCALIZATION_COMPETITOR_REVIEW_2026-09-19.md.
- **Revisit:** a confirmatory protocol under a fresh authorization after the method is frozen; a budgeted reranker (option B) as a separate authorized mission; multilingual transfer (SweRank+ / cross-language readiness) at Stage 7.

## Decision P71 - Scope change: Stage 5 confirmatory PAUSED; Qwen3-embedding contamination-robustness bridge = QWEN3_EMBED_BRIDGE_TECHNICALLY_INCONCLUSIVE (2026-09-19)

- **Status:** ADOPTED (mission QWEN3_EMBED_CONTAMINATION_BRIDGE_2026-09-19; T3 DEVELOPMENT; scope change authorized by the user; ZERO paid API)
- **Context:** before consuming any sealed confirmatory evidence, the user asked whether the SweRank DEV gain is due to dense semantic retrieval as a general mechanism or to SweRank/SweLoc specialization/possible overlap. Stage 5 confirmatory execution was therefore PAUSED and a DEVELOPMENT-only contamination-robustness bridge with qwen/qwen3-embedding-8b (OpenRouter embeddings interface) was authorized with a hard .50 scientific cost ceiling.
- **Preflight result (STOP BEFORE CALL 1):** (1) the exact model is NOT available on OpenRouter - full catalog (447 models) contains zero embedding-capable models; HTTP 404 on qwen/qwen3-embedding-8b, -4b, -0.6b. (2) Even if available, the REQUIRED full DEVELOPMENT population (49,705 units / 21,870,401 unit tokens + 12,128 query tokens, Qwen3-Embedding-8B tokenizer) projects >.50 at every realistic rate (.09-.47), and subsampling is forbidden without a documented limitation + new authorization. No scientific call was made (0 calls, .00); no substitute model was executed.
- **Decision:** **QWEN3_EMBED_BRIDGE_TECHNICALLY_INCONCLUSIVE** - the bridge is frozen as technically inconclusive (a technical freeze, NOT a scientific verdict on dense retrieval, Qwen3-Embedding, or SweRank). Provenance audit V2 keeps verdict C (TRAINING_PROVENANCE_INSUFFICIENT_TO_RULE_OUT_OVERLAP): django-cms rank 11,118 in the 2026-09 top-PyPI dump (just outside the top-11k SweLoc cutoff; 2025 rank unverifiable), saleor absent from top-15k, no released SweLoc manifest found anywhere (full SweRank repo history has no corpus artifacts). Stage-5 decision: STAGE5_REMAINS_BLOCKED_BY_PROVENANCE_OR_NONREPLICATION - confirmatory stays PAUSED and SEALED (djangoCMS RESERVE 59, Saleor INTERNAL_TEST 80, Saleor RESERVE 1086; spent djangoCMS INTERNAL_TEST untouched).
- **Preserved (unchanged):** CHEAP_RANKING_CLOSED_FOR_NOW, BOUNDED_SEMANTIC_NEGATIVE_FROZEN, PRECISION_SAFE_ACCEPTANCE_FAIL, BOUNDED_CHEAP_SEMANTIC_CLOSED_FOR_NOW, SWERANK_EMBED_PASS; SweRank revision 745d2a06103a66d3cfa600aa52fc0d3523010daa; comparator Frozen Route-B @ B=5; DEV populations 174/149.
- **Rejected:** silently substituting an embedding model; executing any paid call against an unverified endpoint; opening sealed populations; changing the frozen SweRank method or any prior gate; claiming a positive bridge label.
- **Evidence:** reports/QWEN3_EMBED_DEVELOPMENT_REPORT_2026-09-19.md, reports/CONTAMINATION_ROBUSTNESS_BRIDGE_CLOSURE_2026-09-19.md, reports/QWEN3_EMBED_CONTAMINATION_BRIDGE_BUDGET_FREEZE.md + .json, reports/SWERANK_TRAINING_PROVENANCE_AUDIT_V2_2026-09-19.md, reports/QWEN3_EMBED_INDEPENDENT_AUDIT.md + .json (9/9), docs/QWEN3_EMBED_CONTAMINATION_ROBUSTNESS_PROTOCOL_FROZEN.md, research/contamination-bridge/*.json, tests/unit/test_or_embeddings.py (13/13), src/benchmark/signal/or_embeddings.py.
- **Revisit:** with explicit authorization, run the bridge with an available independent dense-embedding control (recommended local BAAI/bge-m3) under a new freeze, then decide Stage-5 justification; OR if qwen3-embedding becomes available on OpenRouter, re-verify availability and the .50 ceiling.

## Decision P72 - Qwen3 availability probe defect confirmed + bridge resumed: QWEN3_EMBED_AVAILABILITY_PROBE_DEFECT_CONFIRMED (2026-09-19)

- **Status:** ADOPTED (mission QWEN3_EMBEDDING_BRIDGE_PROBE_DEFECT_CORRECTION_2026-09-19; T3 DEVELOPMENT; explicit user correction; authorized paid scientific run <= .50)
- **Context:** P71 (QWEN3_EMBED_BRIDGE_TECHNICALLY_INCONCLUSIVE) remains a TRUE historical record of what the old probe concluded (the old probe queried the GENERATION model catalog, which contains zero embedding models). No scientific Qwen result was produced under P71. The user authorized a re-probe of the DEDICATED embeddings-model discovery endpoint and, if the model exists, resumption of the previously frozen bridge under the .50 ceiling.
- **Re-probe result (2026-09-19):** GET https://openrouter.ai/api/v1/embeddings/models returns **33 embedding-capable models**, including **qwen/qwen3-embedding-8b** (context 32,768; HF Qwen/Qwen3-Embedding-8B) served by Nebius (.01/M, ctx 32,000), DeepInfra (.01/M, ctx 32,768) and SiliconFlow (.04/M, fp8). qwen/qwen3-embedding-4b also present (.02/M; information only); qwen/qwen3-embedding-0.6b NOT in the catalog (information only). Root cause of P71 = incorrect embedding-model discovery (generation catalog), NOT model absence.
- **Decision:** record **QWEN3_EMBED_AVAILABILITY_PROBE_DEFECT_CONFIRMED**; the DEVELOPMENT contamination-robustness bridge RESUMES under the previously frozen scientific protocol with: pinned provider **DeepInfra** (documented .01/M, full 32,768 context, 100% 5m uptime, consistent with the project's prior frozen DeepInfra route), provider routing pinned + fallbacks disabled, expected full-run cost ~.219 (21,882,529 estimated tokens x .01/M), hard ceiling .50. This is a TECHNICAL CORRECTION, NOT result-dependent method tuning. A regression test now forces future availability checks to use the embeddings-model catalog.
- **Frozen scope:** DEVELOPMENT only (djangocms 174 + saleor 149); sealed sets untouched (djangoCMS RESERVE 59, Saleor INTERNAL_TEST 80, Saleor RESERVE 1086, spent djangoCMS INTERNAL_TEST 80); only qwen/qwen3-embedding-8b is scientifically authorized (no 4B/0.6B, no Jina, no DeepSeek); no Stage-5 confirmatory execution; no cross-language mining.
- **Rejected:** substituting another model; switching provider based on scientific output; opening sealed data; running Stage 5; deleting/rewriting P71.
- **Evidence:** research/contamination-bridge/model_availability_v2.json, reports/QWEN3_EMBED_CONTAMINATION_BRIDGE_BUDGET_FREEZE.md (+.json, live pricing), docs/QWEN3_EMBED_CONTAMINATION_ROBUSTNESS_PROTOCOL_FROZEN.md (numeric gate + API-semantics addendum), tests/unit/test_or_embeddings.py (embeddings-catalog regression test), reports/QWEN3_EMBED_DEVELOPMENT_REPORT_EXECUTED_2026-09-19.md.
- **Revisit:** at bridge closure, decide whether Stage 5 is NOW_JUSTIFIED or REMAINS_BLOCKED (still sealed).

## Decision P73 - Qwen3 bridge STOPPED on material embedding nondeterminism (2026-09-19)

- **Status:** ADOPTED (mission QWEN3_EMBEDDING_BRIDGE_PROBE_DEFECT_CORRECTION_2026-09-19; T3 DEVELOPMENT; authorized paid technical probes <= .50)
- **Context:** after P72 confirmed the availability-probe defect and the bridge resumed, the frozen determinism probe (protocol 12.8) was executed on already-exposed DEVELOPMENT material: (a) 201-unit probe embedded twice - max cosine drift ~1.0e-4 (float-level), unit top-10 overlap 1.0; (b) FILE-level stability check on 5 complete djangoCMS DEVELOPMENT tasks embedded twice (two independent realizations) - B=5 file sets identical for 4/5 tasks, but djangocms-rc-0526cdde8118 had 0.8 overlap (ONE of its 5 selected files flipped across realizations).
- **Finding:** the endpoint's ~1.0e-4 cosine nondeterminism (normal hosted-service float noise) CAN change the file-level B=5 selection for a task with a near-tie (1/5 in the sample). Per the frozen pre-committed criterion (protocol 12.8: if drift could plausibly change ranking ties, STOP and report), this is MATERIAL enough to destabilize the operating-point ranking.
- **Decision:** STOP BEFORE THE FULL SCIENTIFIC RUN. The bridge remains **QWEN3_EMBED_BRIDGE_TECHNICALLY_INCONCLUSIVE** (root cause NOW = material embedding nondeterminism at the file-level B=5 margin, NOT unavailability and NOT model absence). NO full scientific Qwen result was produced; total technical-probe spend ~.023 (probe + stability + batch tests), well inside the .50 ceiling. This is a technical freeze, NOT a scientific verdict on Qwen3-Embedding or dense retrieval; interpretation CASE E.
- **Preserved (unchanged):** P71 (historical availability-probe record), P72 (availability defect confirmed + corrected), all earlier frozen decisions; SweRank DEV result untouched; Stage-5 confirmatory remains PAUSED and SEALED; no sealed data opened.
- **Rejected:** proceeding with the full run despite the 1/5 file-flip evidence (post-hoc relaxation of the frozen probe criterion); result-based retesting; switching providers to chase determinism; substituting another embedding model; opening sealed data.
- **Evidence:** research/contamination-bridge/qwen_embed/{probe,stability}.json, reports/QWEN3_EMBED_DEVELOPMENT_REPORT_2026-09-19.md (updated technical-stop), reports/CONTAMINATION_ROBUSTNESS_BRIDGE_CLOSURE_2026-09-19.md (updated).
- **Revisit:** with explicit authorization, a determinism-controllable control (e.g., LOCAL open-weight inference where numerical determinism can be pinned) under a new freeze; OR a documented provider/endpoint change if OpenRouter adds a deterministic-embedding guarantee.

## Decision P74 - Protocol amendment: two independent realizations replace bitwise determinism for the Qwen bridge (2026-09-19)

- **Status:** ADOPTED (mission QWEN3_TWO_REALIZATION_REPLICATION_2026-09-19; T3 DEVELOPMENT; recorded APPEND-ONLY and BEFORE any target-aware Qwen P/R/F1 inspection)
- **Context:** P73 (QWEN3_EMBED_BRIDGE_TECHNICALLY_INCONCLUSIVE; determinism root cause) remains a TRUE historical record: the hosted endpoint is nondeterministic at ~1e-4 cosine and that noise CAN flip a B=5 file set on a near-tie task (1/5 sampled djangoCMS DEV tasks). The prior strict bitwise/deterministic STOP was historically valid. However NO full Qwen localization metrics were ever inspected. This mission therefore evaluates CONCLUSION REPRODUCIBILITY using TWO complete independent realizations of the hosted Qwen embeddings, rather than requiring hosted floating-point outputs to be bit-identical.
- **Amendment (frozen BEFORE call 1 and BEFORE any target-aware Qwen P/R/F1 inspection):** (1) run TWO independent full realizations (A and B) of the complete DEVELOPMENT population (djangoCMS 174 + Saleor 149; 49,705 code units + 323 queries) under the SAME frozen model/provider/settings; (2) analyze each realization SEPARATELY — no averaging of A/B embeddings, no cherry-picking, no combined scientific metrics; (3) the frozen matched localization protocol is UNCHANGED (parent-only state; same production-file universe; same code-unit extraction; same query text; same text preparation/truncation; same MAX-code-unit -> file aggregation; same deterministic path tie-break; B=5 primary; Route-B historical primary comparator; same metrics; same paired task bootstrap >=10,000 resamples, fixed seed, CI95=[Q2.5,Q97.5]); (4) declare INDEPENDENT_DENSE_RETRIEVAL_REPLICATED ONLY IF realizations A AND B BOTH pass the frozen gate (A-F) on djangoCMS AND Saleor at B=5; otherwise INDEPENDENT_DENSE_RETRIEVAL_REPRODUCIBILITY_INCONCLUSIVE; no cherry-picking.
- **Preserved (unchanged):** P71/P72/P73 immutable; QWEN3_EMBED_BRIDGE_TECHNICALLY_INCONCLUSIVE historical verdict stands for the strict-determinism question; SweRank DEV result untouched; sealed sets untouched; Stage-5 confirmatory remains PAUSED and SEALED.
- **Rejected:** relaxing the gate; averaging realizations; choosing the better realization; running only one realization; opening sealed data; executing Stage 5; switching provider based on results.
- **Evidence:** docs/QWEN3_TWO_REALIZATION_REPLICATION_IMPACT_DECLARATION_2026-09-19.md; this decision.
- **Revisit:** at bridge closure, decide Stage-5 justification from the A/B verdict; the historical determinism finding remains a documented limitation of the hosted interface.

## Decision P75 - Qwen bridge cumulative budget freeze v2 (two realizations) (2026-09-19)

- **Status:** ADOPTED (mission QWEN3_TWO_REALIZATION_REPLICATION_2026-09-19; frozen BEFORE call 1)
- **Decision:** live provider price re-verified immediately before call 1 (DeepInfra serves qwen/qwen3-embedding-8b at **$0.01 / 1M prompt tokens**; context 32,768; fallback disabled). Expected cost per complete realization = 21,882,529 tokens / 1e6 × $0.01 = **$0.2188**; TWO realizations ≈ **$0.4377**. Prior technical probes ~$0.023 already spent. **Cumulative Qwen bridge hard ceiling = $0.50.** Fail-closed projection guard: after every batch, projected final cumulative cost (spent + remaining estimated tokens × price) must stay below $0.50; if both complete realizations cannot remain within the ceiling, STOP before exceeding it and report the exact projection. Wall ceiling: frozen 180 min per realization is retained unless a longer ceiling is documented before call 1.
- **Rejected:** silently exceeding $0.50; subsampling; result-based retry; provider/model substitution.
- **Evidence:** reports/qwen3_two_realization_budget_freeze.json; DECISIONS.md P75.
- **Revisit:** at bridge closure.

## Decision P76 - Qwen bridge wall-ceiling extension (measured rate, 2026-09-19)

- **Status:** ADOPTED (mission QWEN3_TWO_REALIZATION_REPLICATION_2026-09-19; append-only; recorded DURING realization A after the first measured batches)
- **Context:** the frozen 180-min per-realization wall ceiling (P75) was estimated from ~783 batched requests x assumed provider latency. The first measured batches of realization A show ~192 code units/min (batch=64, DeepInfra embeddings latency p50~1s / p90~16s per the provider's own telemetry), projecting ~4.3 h per complete realization -- above 180 min but FAR below the cost ceiling.
- **Decision:** extend the documented wall ceiling to **300 min per realization** (engineering-only clarification; does not change any scientific input, batch size, model, provider, or the cost ceiling). The **$0.50 cumulative cost ceiling remains the HARD stop**; the fail-closed projection guard (spent + projected remaining + prior probes < $0.50) is unchanged and is checked before every request. Recorded transparently as an append-only amendment BEFORE the realization continues beyond 180 min.
- **Rejected:** changing batch size; switching provider; subsampling; ignoring the cost ceiling.
- **Evidence:** reports/qwen3_two_realization_budget_freeze.json (wall_minutes_per_realization 180 -> 300), this decision.
- **Revisit:** at bridge closure.

## Decision P77 - Qwen3 two-realization replication: INDEPENDENT_DENSE_RETRIEVAL_REPLICATED (2026-09-19)

- **Status:** ADOPTED (mission QWEN3_TWO_REALIZATION_REPLICATION_2026-09-19; T3; authorized paid run; cumulative spend ~$0.439 <= $0.50 ceiling)
- **Context:** the contamination bridge line needed ONE remaining answer: does an independent dense embedding family reproduce the frozen SweRank ranking/recovery signal on BOTH DEVELOPMENT repositories? The hosted endpoint is nondeterministic at ~1e-4 cosine (P73), so under the P74 amendment the mission evaluated CONCLUSION REPRODUCIBILITY with TWO complete independent realizations (A and B) of the full DEV population (qwen/qwen3-embedding-8b @ DeepInfra, live $0.01/M re-verified, fallback disabled).
- **Execution:** 49,703 embeddable units + 323 queries embedded TWICE (whitespace-only units excluded per frozen 12.9; resume-safe chunked caches on E:; budget guard checked before every request). Actual cost A $0.1971 / B $0.2188; cumulative incl. prior probes ~$0.439 < $0.50 ceiling; 0 permanent failures (2 transient 429s retried per policy).
- **Result @B=5 (vs frozen Route-B):** djangoCMS F1 0.226 -> 0.262 (P +0.026, R +0.059, FNR -0.059, macro ORR 0.163 -> 0.242, candP 0.071 -> 0.106); Saleor F1 0.237 -> 0.270 (P +0.024, R +0.053, FNR -0.053, macro ORR 0.237 -> 0.296, candP 0.106 -> 0.140). Every file-level paired-bootstrap 95% CI excludes zero on BOTH repos in BOTH realizations (djangoCMS final F1 delta +0.0362 CI [0.0134, 0.0592]; Saleor +0.0333 CI [0.0042, 0.0616]). Saleor macro ORR CI crosses zero (diagnostic only). Gate A-E PASS on both repos both realizations (A: delta F1 > 0 AND CI lower > 0; B: delta Recall >= -0.02; C: delta FNR <= +0.02; D: delta Precision >= -0.02; E: >= 3/5 folds delta F1 >= 0). Fold deltas: djangoCMS 5/5 positive, Saleor 4/5.
- **Reproducibility A vs B (B=5, 323 tasks):** exact same selected-set 97.21%; mean Jaccard 0.9907 (median 1.0, min 0.6667); 9 one-file boundary flips -- ALL swapped one FP for another FP (verified), so pooled metrics are IDENTICAL A vs B (all deltas 0.0000). Scientific robustness to hosted numerical noise: high.
- **Decision:** **INDEPENDENT_DENSE_RETRIEVAL_REPLICATED** (requires A and B BOTH pass on djangoCMS AND Saleor @B=5 - satisfied; no cherry-picking). The dense ranking/recovery signal now has independent support as a general mechanism. This strengthens the dense-retrieval hypothesis and weakens (does NOT eliminate) the specialization/memorization hypothesis.
- **NO OVERCLAIM (recorded):** Qwen improves dense ranking/recovery over Route-B but does NOT beat Sparse final-set F1 (0.318/0.261) and does NOT replace SweRankEmbed-Small (0.280/0.288); not 'the Sparse problem is solved'; SweRank diagnostic B=1 (0.348/0.304) remains diagnostic, not the primary point; rank hit-rates are frequencies, not calibrated probabilities; provenance verdict C unchanged (does NOT prove unseen generalization).
- **Engineering artifact (for the FUTURE calibrated ADD+DROP study):** label-free full-file-score Parquet tables persisted per realization (143,852 rows each; case_id/repository/parent_commit/file_path/dense_file_score/dense_rank/in_sparse/query_sha256/model_id/provider/realization_id; NO target labels, NO raw vectors in Git; caches on E:). CALIBRATED_SET_SELECTION_V1 DRAFTED, NOT executed. Lipton 2014 F1-threshold theory documented as motivation only. Competitors (LocAgent/Agentless/Loc-Bench) documented, NOT run.
- **Stage-5 decision:** STAGE5_REMAINS_BLOCKED_BY_PROVENANCE_OR_NONREPLICATION - confirmatory stays PAUSED and SEALED (djangoCMS RESERVE 59, Saleor INTERNAL_TEST 80, Saleor RESERVE 1086; spent djangoCMS INTERNAL_TEST untouched). The dense replication does NOT by itself unlock Stage 5.
- **Rejected:** averaging A/B embeddings; choosing the better realization; combining metrics; relaxing the gate; claiming final-set superiority; opening sealed data; executing Stage 5; executing calibrated set selection; switching provider.
- **Evidence:** reports/QWEN3_TWO_REALIZATION_REPLICATION_REPORT_2026-09-19.md, research/contamination-bridge/qwen_embed/{realization_A,realization_B,two_realization_metrics}.json, reports/qwen3_two_realization_{gate,reproducibility,audit}.json, docs/CALIBRATED_SET_SELECTION_V1_DRAFT.md, reports/qwen3_two_realization_budget_freeze.json, tests/unit/test_qwen3_two_realization.py (6/6), audit 13/13.
- **Revisit:** CALIBRATED_SET_SELECTION_V1 (DEV only) as the next mission after explicit authorization + freeze; then a Stage-5 confirmatory decision.

## Decision P78 - CALIBRATED_SET_SELECTION_V1 governance amendment + frozen configuration (2026-09-20)

- **Status:** ADOPTED (mission CALIBRATED_SET_SELECTION_V1; T3 DEVELOPMENT; ZERO API; recorded APPEND-ONLY and BEFORE any outer-OOF outcome inspection)
- **Governance amendment (mission section 3):** (1) **\INDEPENDENT_DENSE_RETRIEVAL_REPLICATED\** (P77) means lack of independent replication is **NO LONGER a Stage-5 blocker**. (2) **Stage 5 remains paused** because the final file-set decision policy is NOT frozen: **\FINAL_POLICY_NOT_FROZEN\**. (3) **Pretrained-model provenance claim boundary preserved:** independent replication (Qwen3-Embedding-8B A+B both PASS djangoCMS and Saleor @B=5) **weakens** the hypothesis that SweRankEmbed-Small's gain is solely due to SweLoc-specific supervision or memorization, but it does **NOT** prove that either pretrained model never saw public target-repository code (verdict C unchanged).
- **Frozen config (documented in full in docs/CALIBRATED_SET_SELECTION_V1_IMPACT_DECLARATION_2026-09-20.md and reports/calibrated_set_selection_v1_freeze.json):** primary score realization = Qwen realization A (generated first; choice made independent of downstream performance); candidate universe = Sparse files (KEEP/DROP) UNION top-20 NON-SPARSE files by frozen Qwen dense rank (TOP_ADD_UNIVERSE = 20; NO fixed B, NO max-additions cap, NO minimum-one-file constraint); features EXACTLY [dense_file_score (NaN imputed deterministically to min_finite_score - 1.0), log_rank = log1p(ABSOLUTE dense_rank) (NOT normalized by N), gap_to_top1, in_sparse, log_sparse_set_size = log1p(|Sparse|), sparse_empty, sparse_rank_interaction = in_sparse * log_rank]; repository identity / N / normalized rank / BM25 / graph / co-change / history / path tokens / extension / labels FORBIDDEN; model = L2 LogisticRegression (C=1.0, solver=liblinear, max_iter=1000, random_state=0) with StandardScaler on the 5 continuous features fit on training rows ONLY; nested 5-fold OUTER task-grouped CV (repo-stratified) + 5-fold INNER task-grouped OOF threshold selection on the grid 0.01..0.99 step 0.01, argmax pooled micro-F1, tie-break higher threshold; final set = {candidate : P >= threshold}; primary baseline = Sparse; paired task bootstrap >= 10,000 resamples fixed seed 20260920; primary gate A-G on BOTH repos; calibration diagnostics with 10 equal-width bins; realization-B robustness rerun of the EXACT same pipeline; decision rule PASS / FAIL / ROBUSTNESS_INCONCLUSIVE.
- **Reason for absolute log-rank (documented BEFORE execution):** the post-hoc DEVELOPMENT rank-hit pattern is broadly similar across repositories despite large universe-size separation (djangoCMS 139..234, Saleor 403..1142 with no overlap); normalized-by-N rank would act as a hidden repository-identity proxy, contradicting the pooled repository-independent policy. Rank-hit rates are frequencies, NOT calibrated probabilities.
- **Preserved (unchanged):** all prior decisions P1-P77; frozen Sparse/Route-B/Qwen/SweRank DEV numbers; SWERANK_EMBED_PASS; INDEPENDENT_DENSE_RETRIEVAL_REPLICATED; verdict C; Stage 5 PAUSED/SEALED; sealed sets untouched.
- **Rejected:** opening sealed data; executing Stage 5; feature shopping; model-family comparison; averaging A/B; choosing the better realization; any post-outcome change to the frozen config; paid API calls.
- **Evidence:** docs/CALIBRATED_SET_SELECTION_V1_IMPACT_DECLARATION_2026-09-20.md, reports/calibrated_set_selection_v1_freeze.json, this decision.
- **Revisit:** at V1 closure, record PASS / FAIL / ROBUSTNESS_INCONCLUSIVE; Stage-5 decision is then governed by the frozen final policy.

## Decision P79 - CALIBRATED_SET_SELECTION_V1 execution: CALIBRATED_SET_SELECTION_V1_FAIL (2026-09-20)

- **Status:** ADOPTED (mission CALIBRATED_SET_SELECTION_V1; T3 DEVELOPMENT; ZERO API; frozen negative)
- **Context:** P78 froze the governance amendment (INDEPENDENT_DENSE_RETRIEVAL_REPLICATED removes the non-replication Stage-5 blocker; Stage 5 stays paused because FINAL_POLICY_NOT_FROZEN) and the exact V1 configuration BEFORE any outer-OOF inspection. This decision records the execution outcome.
- **Execution (ZERO API; primary = Qwen realization A; B = robustness):** candidate universe = Sparse files (KEEP/DROP) UNION top-20 NON-SPARSE files by frozen Qwen dense rank; 7 frozen features (dense_file_score with deterministic NaN floor, absolute log_rank = log1p(rank), gap_to_top1, in_sparse, log_sparse_set_size, sparse_empty, sparse_rank_interaction); L2-LR C=1.0 solver=liblinear max_iter=1000 seed 0; StandardScaler on the 5 continuous features fit on training rows only; nested 5x5 task-grouped repo-stratified CV (seed 20260920); inner-OOF threshold = argmax pooled micro-F1 over 0.01..0.99 (tie-break HIGHER); final set = {candidate : P >= threshold}; primary baseline Sparse; paired task bootstrap 10,000 resamples seed 20260920; calibration diagnostics (10 equal-width bins); error decomposition; set-size analysis; realization-B robustness.
- **Result (realization A):** djangoCMS Sparse 125/155/382 (F1 0.318) -> policy 140/191/367 (F1 0.334; Delta F1 +0.0165, 95% CI [-0.0190, +0.0525]); Saleor Sparse 99/193/369 (F1 0.261) -> policy 147/261/321 (F1 0.336; Delta F1 +0.0751, CI [+0.0416, +0.1083]). **Primary gate FAIL** on djangoCMS (criterion B: CI lower crosses zero); Saleor PASSES (A-E). Fold criterion E: djangoCMS 3/5, Saleor 4/5. PARETO_SUCCESS = FALSE (Saleor Pareto-only). Realization B: same verdict (83.28% exact same selected set; mean Jaccard 0.9284; F1 djangoCMS 0.341, Saleor 0.332). Calibration: Brier 0.064, ECE 0.0057 (well calibrated). Determinism (gate G): identical rerun. Independent audit 20/20 PASS. Error decomposition (A): djangoCMS retained 111 / dropped 14 / FP dropped 44 / FP retained 111 / added 29 / new FP 80; Saleor 93/6/57/136/54/125.
- **Decision:** **CALIBRATED_SET_SELECTION_V1_FAIL** (frozen negative; no automatic V2). The calibrated family is directionally positive (point F1 improves on both repos; Saleor statistically significant) but the frozen primary gate fails on djangoCMS, robustly across realizations. Oracle gap re-decomposed into ranking/coverage error (199/177), ADD decision error (154/138), DROP decision error (14/6), and proxy ambiguity. First-pass recall/coverage remains the dominant loss.
- **Stage-5 decision:** **FINAL_POLICY_NOT_FROZEN** — confirmatory stays PAUSED and SEALED (djangoCMS RESERVE 59, Saleor INTERNAL_TEST 80, Saleor RESERVE 1086; spent djangoCMS INTERNAL_TEST untouched). The dense-mechanism replication is accepted (no longer a blocker) but a frozen successful final policy does not exist.
- **Post-hoc verification correction (no scientific change):** the historical two-realization report's SweRank rank-4/5 hit rates (0.023/0.034 dc; 0.074/0.034 saleor) do not match a fresh recomputation from the SAME artifact (0.080/0.052 dc; 0.134/0.094 saleor). Ranks 1-3 (used by every frozen conclusion) are identical; noted as a transcription error in the V1 report.
- **Rejected:** opening sealed data; executing Stage 5; any post-outcome change to the frozen config (candidate universe, features, model, folds, grid, tie-break, gate); feature shopping; comparing model families; paid API calls; claiming success.
- **Evidence:** reports/CALIBRATED_SET_SELECTION_V1_REPORT_2026-09-20.md, reports/calibrated_set_selection_v1_{freeze,audit,oracle_gap}.json, reports/CALIBRATED_SET_SELECTION_V1_AUDIT_2026-09-20.md, reports/CURRENT_ORACLE_GAP_EXPLAINED_2026-09-20.md, reports/LOCAGENT_MATCHED_COMPARISON_PROTOCOL_DRAFT_2026-09-20.md, research/calibrated-set-selection-v1/*, scripts/calibrated_set_selection_v1_{run,audit,report}.py, src/benchmark/calibrated/, tests/unit/test_calibrated_set_selection.py (18/18).
- **Revisit:** a V2 calibrated set-selection policy requires a NEW mission and NEW frozen hypothesis (mission section 32 forbids automatic V2); Stage 5 requires a frozen successful final policy.

## Decision P80 - PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2 governance amendment + Full-Universe V2 cancellation + frozen configuration (2026-09-20)

- **Status:** ADOPTED (mission PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2; T3 DEVELOPMENT; ZERO API; recorded APPEND-ONLY and BEFORE any implementation / outer-OOF inspection)
- **Preserved (unchanged):** `INDEPENDENT_DENSE_RETRIEVAL_REPLICATED`; `CALIBRATED_SET_SELECTION_V1_FAIL` (frozen negative, NOT rewritten as a success); all prior decisions P1-P79; Stage 5 PAUSED/SEALED (`FINAL_POLICY_NOT_FROZEN`); sealed sets untouched; pretrained-model provenance verdict C unchanged.
- **Full-Universe V2 CANCELLED before execution = `FULL_UNIVERSE_V2_CANCELLED_AS_NON_BINDING_ABLATION`:** verified from already-exposed V1 artifacts WITHOUT fitting a new model — V1 selected non-Sparse additions ONLY at dense ranks 1-4 (rank1 172, rank2 93, rank3 20, rank4 3, ranks 5-20 = 0; n=4981 rank-5-20 pool rows, 0 selected); max outer-OOF probability among non-Sparse ranks 5-20 = 0.1880 (p95 0.0886) and ranks 15-20 = 0.0650 (p95 0.0428); all five V1 inner-CV thresholds were 0.17-0.21, strictly ABOVE every non-Sparse rank-5+ probability, so the top-20 boundary was NEVER ACTIVE at the decision boundary. Removing it while preserving the same rank-monotone signal would be expected to produce a near-null rerun and creates unnecessary forking-path risk. Descriptive decision from exposed DEV/V1 artifacts, NOT a new scientific experiment.
- **Deep dense miss (verified):** `DEEP_DENSE_MISS` = historical-proxy positive file that remains a V1 false negative AND was outside the V1 frozen candidate universe (Sparse UNION dense-top20). Verified counts: djangoCMS 199, Saleor 177; median dense rank of deep misses 62 (djangoCMS) / 70 (Saleor). The bottleneck is DEEP FALSE-NEGATIVE RECOVERY, not basic dense ranking discovery (already independently replicated by SweRankEmbed-Small + Qwen3-Embedding-8B).
- **Frozen V2 config (full detail in docs/PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_IMPACT_DECLARATION_2026-09-20.md):** parent-ONLY history (ancestors of P, fail-closed; ALL parent-visible production-changing history, no window tuning; production-changing = touches >=1 file in the task's legal production universe); Channel A structural co-change (Jaccard = C(f,s)/(C(f)+C(s)-C(f,s)); pair score 0 if C(f,s)<2, frozen support=2, NO sweep; seeds = Sparse files + Qwen dense rank-1 file; cochange_memory_score = max(cochange_sparse, cochange_top1)); Channel B episodic memory (commit subject+body docs only, no web/API enrichment; deterministic BM25 over historical change text; query = frozen parent-visible task intent; EPISODIC_TOP_CHANGES=10 frozen); features per file: episode_similarity (max normalized BM25 among retrieved top-10 episodes touching f; 0 if none), episode_hit_count DESCRIPTIVE ONLY (NOT a feature), history_change_count with log1p feature, NO recency weighting; memory candidate generation = top-10 NON-SPARSE by cochange_memory_score>0 UNION top-10 NON-SPARSE by episode_similarity>0 (COCHANGE_TOP_FILES=10, EPISODIC_TOP_FILES=10; tie-break higher score / higher historical support / path ascending); V2 candidate universe = Sparse UNION dense top-20 NON-SPARSE UNION memory candidate set (NOT the full repository universe); features EXACTLY 11 = the 7 V1 features + cochange_sparse + cochange_top1 + log_history_change_count + episode_similarity (FORBIDDEN: repository ID, graph features, code BM25, path features, extension, labels, LLM features, recency, issue categories, episode_hit_count); model/CV/threshold EXACTLY V1 (L2-LR C=1.0 liblinear max_iter=1000 seed 0; StandardScaler on continuous fit on training rows only; EXACT V1 outer fold assignments; EXACT V1 inner 5-fold task-grouped OOF; threshold argmax pooled micro-F1 on 0.01..0.99 tie-break higher); primary score realization = Qwen realization A (B = frozen robustness rerun, no averaging); primary baseline = Sparse (V1, Qwen B=5/B=1, SweRank B=5/B=1 descriptive); metrics + task-paired bootstrap (10,000 resamples, seed 20260920); success gate A-G on BOTH repos UNCHANGED from V1; descriptive-only: dependency-cluster diagnostic (oracle-style, never inference seeds, no graph features in V2), deep-FN coverage report before fitting, popularity/random mechanism baselines, channel ablations, intent-length stratification (buckets <=6 / 7-15 / >15 words; NOT a feature, NOT a gate); realization-B robustness (verdict change -> ROBUSTNESS_INCONCLUSIVE).
- **Decision rule (frozen):** V2 PASS requires the unchanged gate on BOTH repos AND realization B preserves the verdict -> `PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_PASS`; otherwise `PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL` and STOP. No automatic V3. No Stage-5 execution. No novelty claims (repository-memory is prior art: Improving Code Localization with Repository Memory, arXiv 2510.01003).
- **Expensive/irreversible guard:** do NOT open sealed datasets; do NOT execute Stage 5; do NOT run paid APIs; do NOT download another embedding model; do NOT run LocAgent; do NOT clone cross-language repositories; do NOT switch thesis scope to provenance-by-construction (only a supervisor-facing strategic direction note is created). Stop and ask Ahmed first if any becomes necessary.
- **Rejected:** opening sealed data; executing Stage 5; paid API calls; embedding reruns; feature shopping; graph features; post-outcome changes to the frozen config; claiming novelty.
- **Evidence:** docs/PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_IMPACT_DECLARATION_2026-09-20.md, reports/memory_rescue_v2_freeze.json, this decision.
- **Revisit:** at V2 closure, record PASS / FAIL / ROBUSTNESS_INCONCLUSIVE; Stage-5 decision is then governed by the frozen final policy.

## Decision P81 - PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2 execution: PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL (2026-09-20)

- **Status:** ADOPTED (mission PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2; T3 DEVELOPMENT; ZERO API; frozen negative)
- **Context:** P80 froze the V2 configuration (parent-only history memory channels A structural co-change + B episodic BM25; memory candidate set = top-10 structural ∪ top-10 episodic NON-SPARSE; V2 universe = Sparse ∪ dense-top20 ∪ memory; EXACTLY 11 features = 7 V1 + cochange_sparse + cochange_top1 + log_history_change_count + episode_similarity; model/CV/threshold EXACTLY V1; gate A-G unchanged; cancellation `FULL_UNIVERSE_V2_CANCELLED_AS_NON_BINDING_ABLATION`) BEFORE any implementation / outer-OOF inspection.
- **Execution (ZERO API / $0.00; primary = Qwen realization A; B = robustness):** parent-only history built from local git caches (djangocms `dist/real-commit-cache/djangocms`, saleor `dist/pilot-repo-cache/saleor`; all 323 parents verified ancestors of HEAD; fail-closed ancestry; production-file filter = touches >=1 legal production universe file; ALL parent-visible history, no window tuning; Jaccard with support threshold 2 frozen; episodic BM25 top-10 frozen; caches on D: outside Git, 33.5 MB). Verified deep dense misses 199/177 (median dense rank 62/70). Deep-FN coverage by memory candidate set (union) 43/199 (0.216) djangoCMS / 48/177 (0.271) Saleor; popularity baseline 41/199 / 18/177; random baseline (seed 20260920, 1000 resamples) 11.1 / 2.45. Dependency-cluster diagnostic (oracle-style, NOT features): A 109/130, B 25/49, C 56/76. V2 result (A): djangoCMS Sparse 125/155/382 -> policy 152/222/355 (P 0.4064 / R 0.2998 / F1 0.3451 / FNR 0.7002; Delta F1 +0.0274, CI [-0.0102, +0.0636] CROSSES ZERO); Saleor Sparse 99/193/369 -> policy 158/283/310 (P 0.3583 / R 0.3376 / F1 0.3476 / FNR 0.6624; Delta F1 +0.0871, CI [+0.0515, +0.1229] PASS). Realization B: same verdict (exact same set 99.07%, mean Jaccard 0.9964; djangoCMS F1 0.3451 identical; Saleor 0.3495). Gate: djangoCMS criterion B FAIL in both realizations; Saleor A-E PASS. Error decomposition (A): djangoCMS retained 110 / dropped 15 / FP dropped 49 / FP retained 106; added positives 42 (0 dense-only / 8 structural / 6 episodic / 28 multiple-memory), new FP 116; remaining FN not-generated 156 / rejected 184 / Sparse-TP-dropped 15. Saleor retained 94 / dropped 5 / FP dropped 65 / FP retained 128; added 64 (4/20/12/28), new FP 155; remaining FN 129/176/5. Set sizes: policy mean 2.15/2.96; empty-policy 37/10 (Sparse-empty 53/41). Channel ablations (descriptive): structural-removed F1 0.3459/0.3333; episodic-removed 0.3462/0.3326 (verdict unchanged). Determinism (gate G): 2 reruns identical (SHA 4e2c880...). Independent audit **23/23 PASS** (`reports/memory_rescue_v2_audit.json`), recomputes every claim WITHOUT importing the analyzer. New unit tests **36/36 PASS** + V1 calibrated suite 18/18 still PASS.
- **Decision:** **PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL** (frozen negative; both realizations fail the same criterion). Parent-visible repository history IS an orthogonal, real, zero-API signal that recovers deep dense misses at the candidate level (21.6%/27.1% coverage, better than popularity on Saleor and far better than random), and V2 point F1 improves over both Sparse and V1 on both repos — but the unchanged final-set gate still fails on djangoCMS (Delta-F1 CI crosses zero). The final-set policy problem is NOT solved on DEV.
- **Stage-5 decision:** **FINAL_POLICY_NOT_FROZEN** — confirmatory stays PAUSED and SEALED (djangoCMS RESERVE 59, Saleor INTERNAL_TEST 80, Saleor RESERVE 1086; spent djangoCMS INTERNAL_TEST untouched). No Stage-5 preregistration packet is produced (verdict is FAIL).
- **Rejected:** opening sealed data; executing Stage 5; paid API calls; embedding reruns; feature shopping; graph features; using the dependency-cluster diagnostic as inference seeds; post-outcome changes to the frozen config; claiming repository-memory novelty (prior art arXiv 2510.01003); automatic V3.
- **Evidence:** reports/PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_REPORT_2026-09-20.md, reports/PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_DIAGNOSTICS_2026-09-20.md, reports/memory_rescue_v2_audit.json, reports/MEMORY_RESCUE_V2_INDEPENDENT_AUDIT_2026-09-20.md, reports/PROVENANCE_BY_CONSTRUCTION_DIRECTION_NOTE_2026-09-20.md, reports/memory_rescue_v2_freeze.json, research/memory-rescue-v2/*, scripts/memory_rescue_v2_{history,run,diagnostics,ablation,audit}.py, src/benchmark/memory_rescue/, tests/unit/test_memory_rescue_{history,cochange,v2}.py (36/36).
- **Revisit:** any V3 would require a NEW mission and NEW frozen hypothesis (no automatic V3); Stage 5 requires a frozen successful final policy.

## Decision P82 - ISSUE_GROUNDED_INTENT_HEADROOM governance amendment + frozen protocol (2026-09-20)

- **Status:** ADOPTED (mission ISSUE_GROUNDED_INTENT_HEADROOM; T3 DEVELOPMENT; recorded APPEND-ONLY and BEFORE any issue-ranking outcome inspection)
- **Preserved (unchanged):** `INDEPENDENT_DENSE_RETRIEVAL_REPLICATED`; `CALIBRATED_SET_SELECTION_V1_FAIL` (frozen negative, NOT rewritten as a success); `PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL` (frozen negative, NOT rewritten); all prior decisions P1-P81; Stage 5 PAUSED/SEALED (`FINAL_POLICY_NOT_FROZEN`); sealed sets untouched; pretrained-model provenance verdict C unchanged; current final DEVELOPMENT point estimates unchanged (djangoCMS Sparse F1~0.318 / V1~0.334 / V2~0.345 gate FAIL; Saleor Sparse~0.261 / V1~0.336 / V2~0.348 PASS).
- **Mission:** information-headroom test - does a temporally valid pre-change GitHub issue description (title + body) materially improve localization signal vs the short commit-message proxy on the SAME already-exposed DEVELOPMENT tasks? NOT a new final policy; NOT Stage 5; NOT a V1/V2 tune; NO code-unit re-embedding.
- **Frozen protocol** (`docs/ISSUE_GROUNDED_INTENT_HEADROOM_IMPACT_DECLARATION_2026-09-20.md` + `reports/issue_grounded_intent_freeze.json`): primary alternative intent = ISSUE TITLE + ISSUE BODY (PR body/diff/review comments/later comments/commit diff/target paths/solution summaries FORBIDDEN); deterministic `#NNNN` reference parsing + repository-local resolution; ISSUE vs PR distinction (PR itself NOT textual intent; linked closing issue = dataset-construction linkage only); provenance categories DIRECT_ISSUE / PR_ONE_LINKED / PR_MULTI_LINKED / PR_NO_LINKED / UNRESOLVED; multiple linked issues concatenated in ascending issue-number order (counted separately); STRICT temporal rule (clean iff `created_at < target_commit_time` AND `updated_at <= target_commit_time`; else TEMPORALLY_UNCERTAIN, excluded from PRIMARY clean population, descriptive only); frozen issue corpus + per-record SHA256 + corpus manifest before ranking evaluation; PRIMARY paired population = clean issue-grounded DEV tasks, same case_ids in both arms; dense arms reuse the frozen Qwen corpus (ARM M = existing frozen message rankings; ARM I = NEW issue-query embedding only) with UNCHANGED file-MAX aggregation / cosine / tie-break / full-universe dense rank, evaluated against BOTH realizations A and B; metrics = target-file Recall@1/3/5/10/20 + coverage@K + median rank + MRR + rank distribution + top-K precision + exact rank movement + task-paired bootstrap 10,000 (seed 20260920); DeepFNRescue@20 using the frozen deep-dense-miss definition; historical-episode retrieval arm (frozen BM25/top-10, message vs issue query); path-mention sensitivity (descriptive, pre-registered, no task deletion); intent-length analysis (frozen buckets, descriptive only).
- **Primary gate (frozen BEFORE outcomes):** `ISSUE_GROUNDED_INTENT_SIGNAL_SUPPORTED` iff on BOTH repos (A) Recall@20(issue) > Recall@20(message) AND (B) task-paired 95% CI lower bound of Delta Recall@20 > 0 AND (C) median target-file rank improves or stays equal AND (D) no leakage / temporal-validity violation. One repo -> MIXED; neither -> NOT_SUPPORTED. No post-hoc K choice; no gate redefinition.
- **Expensive/irreversible guard:** do NOT open sealed datasets; do NOT execute Stage 5; do NOT fit a new final-policy classifier; do NOT modify V1/V2 features; do NOT rerun code-unit embeddings; do NOT run SweRank / LocAgent / Agentless / JEPA / energy models; do NOT clone new large repos. Allowed: GitHub metadata retrieval (free), local BM25, Qwen QUERY embeddings ONLY against already-persisted code-unit embeddings, hard incremental API ceiling $0.05 (verify live price before any Qwen call; STOP before paid calls if projected cost > $0.05).
- **Rejected:** opening sealed data; executing Stage 5; fitting a new final policy; V1/V2 tuning; corpus re-embedding; ranking-method changes; claiming F1 beats the literature; claiming `F1 >= 0.8` impossible; reinterpreting any frozen negative.
- **Evidence:** docs/ISSUE_GROUNDED_INTENT_HEADROOM_IMPACT_DECLARATION_2026-09-20.md, reports/issue_grounded_intent_freeze.json, this decision.
- **Revisit:** at closure record SUPPORTED / MIXED / NOT_SUPPORTED; Stage-5 decision remains governed by the frozen final policy.

## Decision P83 - ISSUE_GROUNDED_INTENT_HEADROOM execution: ISSUE_GROUNDED_INTENT_SIGNAL_NOT_SUPPORTED (2026-09-20)

- **Status:** ADOPTED (mission ISSUE_GROUNDED_INTENT_HEADROOM; T3 DEVELOPMENT; minimal-cost; frozen negative)
- **Context:** P82 froze the protocol (primary alternative intent = issue title+body; reference parsing + repo-local resolution; provenance categories; STRICT temporal rule clean iff created < target AND updated <= target; frozen corpus + SHA before ranking; ARM M = frozen Qwen message rankings, ARM I = NEW issue-query embeddings only against persisted code-unit cache; unchanged aggregation/tie-break; pairwise bootstrap 10,000 seed 20260920; gate A-D on BOTH repos) BEFORE any outcome inspection.
- **Execution (minimal-cost; GitHub free reads + Qwen query embeddings only):** references verified (djangocms 99/174, saleor 112/149; 262 refs, 211 tasks, 257 distinct objects resolved). Provenance: DIRECT_ISSUE 28, PR_ONE_LINKED 30, PR_MULTI_LINKED 8, PR_NO_LINKED 145, NO_REFERENCE 112. Strict temporal rule -> PRIMARY clean paired population = djangocms 12 / saleor 0. ARM I embedded 12 issue queries (5,662 prompt tokens, $0.000057; live $0.01/M verified). djangocms n=12 (identical A and B): Recall@20 message 0.6875 -> issue 0.7188; paired bootstrap Delta +0.0201 CI [-0.0875, +0.1375] (crosses zero); pooled median target rank 6.0 -> 7.5 (worsens); MRR 0.351 -> 0.375. Gate djangocms REPO_FAIL (A pass, B FAIL, C FAIL, D pass); saleor no clean population -> cannot demonstrate support. Overall ISSUE_GROUNDED_INTENT_SIGNAL_NOT_SUPPORTED (realization A == B; 90.6% A/B proxy-rank agreement). DeepFNRescue@20 = 0.143 (1/7 djangocms, saleor 0). History BM25 arm: ARM I candidate precision 0.0431 vs ARM M 0.0885 (worse). Path-mention descriptive: R20 gain lives in the no-mention subgroup (0.75->0.80). Intent lengths: issues median 174 words vs messages 11.
- **Decision:** **ISSUE_GROUNDED_INTENT_SIGNAL_NOT_SUPPORTED** (frozen negative; no automatic follow-on). The commit-message proxy was NOT demonstrated to suppress useful localization information; the strict temporal rule leaves a near-empty clean population (esp. saleor 0/149), and on the small clean djangocms population issue text does not materially improve the dense signal (CI crosses zero; median rank worsens). Do NOT rerun V1/V2 with issue text on this evidence.
- **Stage-5 decision:** **FINAL_POLICY_NOT_FROZEN** - confirmatory stays PAUSED and SEALED (djangoCMS RESERVE 59, Saleor INTERNAL_TEST 80, Saleor RESERVE 1086; spent djangoCMS INTERNAL_TEST untouched).
- **Future roadmap (documented, NOT executed):** ENERGY_BASED_CHANGE_SET_COMPLETION (structured prediction over file sets; LeCun-EBL reference; dedicated literature review required) and JEPA/world-model as a supervisor-discussion direction only.
- **Rejected:** opening sealed data; executing Stage 5; fitting a new final policy; V1/V2/Sparse changes; corpus re-embedding; ranking-method changes; using PR diff/body/comments as intent; claiming F1 beats the literature; claiming `F1 >= 0.8` impossible; reinterpreting any frozen negative.
- **Evidence:** reports/ISSUE_GROUNDED_INTENT_HEADROOM_2026-09-20.md, reports/LOCALIZATION_COMPARABILITY_MAP_2026-09-20.md, reports/issue_grounded_intent_freeze.json, reports/issue_grounded_audit.json, research/issue-grounded-intent-headroom/*, scripts/issue_grounded_{resolve,dense_arm,headroom,extended,descriptive,audit}.py, src/benchmark/issue_grounded/, tests/unit/test_issue_grounded.py (27/27).
- **Revisit:** a future issue-grounded mission requires a NEW mission and NEW frozen hypothesis (deliberately chosen temporal rule + pre-registered larger clean corpus); Stage 5 requires a frozen successful final policy.

## Decision P84 - STAGE5_V2_FINAL governance: one-shot untouched confirmatory evaluation APPROVED BY AHMED (2026-09-20)

- **Status:** ADOPTED (mission STAGE5_V2_FINAL; T3 one-shot confirmatory; recorded APPEND-ONLY and BEFORE any Stage-5 outcome inspection / unsealing)
- **Approved by:** Ahmed (mission prompt authorization) — ONE and ONLY ONE opening of the defined Stage-5 confirmatory populations AFTER the complete protocol/configuration/artifact hashes are frozen, committed, pushed, and tagged.
- **Decision wording (frozen):** "Stage 5 is a one-shot untouched evaluation of the best frozen DEVELOPMENT-selected candidate, V2. The primary endpoint is ONE pre-registered pooled, repository-stratified Delta-F1 vs Sparse. Per-repository point estimates and confidence intervals are mandatory secondary analyses. The historical DEV per-repository FAIL verdicts remain unchanged."
- **Also recorded:** `NO_FURTHER_METHOD_SHOPPING_BEFORE_FINAL_THESIS_DECISION`.
- **Preserved (unchanged, NOT rewritten):** `INDEPENDENT_DENSE_RETRIEVAL_REPLICATED`; `CALIBRATED_SET_SELECTION_V1_FAIL`; `PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL` (may cite pooled DEV delta +0.0568 as post-hoc DESCRIPTIVE motivation, NOT a verdict rewrite); `ISSUE_GROUNDED_INTENT_SIGNAL_NOT_SUPPORTED` (may be clarified as "not supported under the frozen strict temporal rule; clean population small/underpowered"; NOT upgraded, NOT rerun); all prior decisions P1-P83; Stage 5 previously PAUSED/SEALED.
- **Frozen protocol:** `docs/STAGE5_V2_FINAL_IMPACT_DECLARATION_2026-09-20.md`. Candidate = `PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2` with `BEST_FROZEN_DEV_CANDIDATE_NOT_CONFIRMED_SUPERIOR_ON_BOTH_REPOS`. Population EXACTLY djangoCMS RESERVE 59 + Saleor INTERNAL_TEST 80 = 139 (`SALEOR_RESERVE_POWER_EXTENSION = NO`). `QWEN_REALIZATION = A`. V2 policy EXACTLY the frozen 11-feature policy; final deployment model refit on ALL 323 DEV (L2-LR C=1.0 liblinear max_iter=1000 random_state=0; StandardScaler on continuous trained rows; 5-fold task-grouped OOF threshold = argmax pooled micro-F1 over 0.01..0.99 tie-break HIGHER). Preregistration artifacts + `stage5-v2-final-preregistered-2026-09-20` tag BEFORE unsealing. Primary endpoint = repo-stratified pooled micro-F1 diff V2-Sparse, 10,000 resamples seed 20260920, CI95 [Q2.5,Q97.5]. Success = (A) pooled delta>0 AND CI lower>0 AND (B) dc point delta>0 AND saleor point delta>0. Per-repo CIs secondary, non-gating. Acc@K/Hit@K/Recall@K descriptive only.
- **Budget:** hard incremental ceiling $1.00 paid (frozen Qwen model/provider only; live price verified pre-call; STOP before paid calls if projected > $1.00). No fallback provider, no model substitution, no extra realization, no Saleor RESERVE extension.
- **Rejected:** method redesign; threshold redesign; endpoint redesign; V3; Energy-Based methods; adaptive-k; JEPA/world models; provenance-by-construction; issue re-mining; LocAgent/Agentless runs; cross-language experiments; opening Saleor RESERVE; changing the success rule after unsealing; second chance.
- **Evidence:** docs/STAGE5_V2_FINAL_IMPACT_DECLARATION_2026-09-20.md, this decision. Full artifacts are frozen with the preregistration step before unsealing.
- **Revisit:** at outcome record PASS / FAIL / MIXED; method selection closes regardless (`IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED`).

## Decision P85 - STAGE5_V2_FINAL execution: STAGE5_V2_FINAL_CONFIRMATION_FAIL (2026-09-20)

- **Status:** ADOPTED (mission STAGE5_V2_FINAL; T3 one-shot untouched confirmatory evaluation; ONE look only; frozen negative)
- **Context:** P84 froze the governance + protocol (best DEV candidate = PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2; population exactly dc RESERVE 59 + saleor INTERNAL_TEST 80 = 139; QWEN_REALIZATION=A; final V2 model refit on all 323 DEV threshold 0.20; primary endpoint repo-stratified pooled Delta-F1; success rule A+B; budget ceiling $1.00) BEFORE unsealing.
- **Execution (one-shot; $0.544067 << $1.00):** preregistration committed `4badcea1…`/tagged `stage5-v2-final-preregistered-2026-09-20` and pushed before any outcome; irreversible checkpoint printed; 139 Stage-5 case bundles materialized (zero-API); Sparse write sets generated with the frozen Sparse-v2 strategy (139/139 succeeded, schema-valid, 1,702,783 tokens, $0.544009); Qwen query embeddings (5,827 tokens, $0.000058; all Stage-5 code units already in the persisted realization-A E: cache); parent-only memory for all 139; frozen V2 model + threshold 0.20 applied.
- **Primary result (audited 10/10):** pooled V2 F1 0.2269 vs Sparse 0.2857; **Delta F1 −0.0588, 95% CI [−0.1119, −0.0084]** (excludes zero, negative); criterion A FAIL; direction consistency FAIL (djangoCMS −0.0618, Saleor −0.0570, both negative). Per-repo: dc Sparse 0.3028 vs V2 0.2410; Saleor Sparse 0.2744 vs V2 0.2174.
- **Decision:** **STAGE5_V2_FINAL_CONFIRMATION_FAIL** + **IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED**. The frozen DEV-selected V2 improvement did NOT survive the preregistered untouched confirmation; on the confirmatory population the learned V2 policy is statistically worse than Sparse, with both repositories negative. Method-search phase CLOSED (`NO_FURTHER_LOCALIZATION_METHOD_SHOPPING_FOR_CURRENT_THESIS`). Thesis reports Sparse, dense recovery, V1, V2, untouched confirmation outcome, limitations -> THESIS_AND_PAPER_EVIDENCE_CLOSURE.
- **Preserved (unchanged):** `INDEPENDENT_DENSE_RETRIEVAL_REPLICATED`; `CALIBRATED_SET_SELECTION_V1_FAIL`; `PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL` (DEV per-repo FAIL stays); `ISSUE_GROUNDED_INTENT_SIGNAL_NOT_SUPPORTED`; all P1-P84.
- **Rejected:** post-unseal tuning; threshold/feature/model changes; A->B switch; adding Saleor RESERVE; bootstrap/endpoint changes; V3; retesting Stage-5; any method redesign; directly comparing Stage-5 Acc@K to external LocAgent/SWE-bench headlines.
- **Evidence:** reports/STAGE5_V2_FINAL_CONFIRMATORY_REPORT_2026-09-20.md, reports/STAGE5_FINAL_PREREGISTRATION_2026-09-20.md, reports/stage5_final_preregistration.json, reports/stage5_primary_result.json, reports/stage5_secondary_result.json, reports/stage5_independent_audit.json, reports/LOCAGENT_NATIVE_METRIC_COMPATIBILITY_2026-09-20.md, research/stage5-v2-final/*, scripts/stage5_v2_{build_bundles,sparse_run,dense_scores,evaluate,secondary,independent_audit,dev_refit_audit,native_compat_audit,preregistration}.py, tests/unit/test_stage5_v2_final.py (10/10).
- **Revisit:** next phase = EXTERNAL_VALIDITY_AND_END_TO_END_REGENERATION (separate authorized mission); no further localization method for the current thesis.

## Decision P86 - STAGE5_V2_EXECUTION_INVALID_EMBEDDING_COVERAGE_DEFECT (2026-09-20)

- **Status:** ADOPTED (mission STAGE5_V2_FINAL; T3 execution-defect correction; recorded APPEND-ONLY and BEFORE any Stage-5 execution-code change; governance-first)
- **Context:** the first Stage-5 evaluation (P85, `STAGE5_V2_FINAL_CONFIRMATION_FAIL`) did NOT execute the preregistered V2 dense-score pipeline correctly. The Stage-5 dense scorer (`scripts/stage5_v2_dense_scores.py`) reused the DEV blob-text/unit cache; for a Stage-5 blob unseen in that DEV cache it failed to construct/embed the new code units and instead assigned a FINITE SENTINEL `dense_file_score = -1e9`. The frozen feature builder (`src/benchmark/memory_rescue/candidates.py`) only invokes the missing/no-unit imputation (`no_units_score` -> NaN -> `min_finite - 1`) on NON-finite values; because `-1e9` is finite, the NaN path never fired, StandardScaler received extreme values, dense-score/gap features became extreme, and LR probabilities collapsed to zero. This violates the frozen Stage-5 preregistration rule (execution step 3: new corpus embeddings REQUIRED when the persisted cache does not already cover the tasks) and the frozen DEV missing-unit rule (NaN, never a finite sentinel).
- **Decision wording (frozen):** The first Stage-5 evaluation is **execution-invalid**; its artifacts remain historical; its scientific FAIL label `STAGE5_V2_FINAL_CONFIRMATION_FAIL` is **superseded** by `STAGE5_V2_EXECUTION_INVALID_EMBEDDING_COVERAGE_DEFECT`; the 139 tasks (djangoCMS RESERVE 59 + Saleor INTERNAL_TEST 80) are considered **exposed**; a corrected rerun on those same 139 tasks is **diagnostic/corrective**, NOT a new untouched confirmation. The old negative Stage-5 numbers must NOT be cited as evidence about V2 generalization; the narrative "the DEV ladder failed to generalize" is NOT to be used unless a technically valid evaluation later supports it.
- **Preserved (unchanged, NOT rewritten):** `IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED`; `INDEPENDENT_DENSE_RETRIEVAL_REPLICATED`; `CALIBRATED_SET_SELECTION_V1_FAIL`; `PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL`; `ISSUE_GROUNDED_INTENT_SIGNAL_NOT_SUPPORTED`; all prior decisions P1-P85; preregistration tag `stage5-v2-final-preregistered-2026-09-20`; invalid-evaluation tag `stage5-v2-final-evaluation-2026-09-20`; invalid artifacts (NOT moved/deleted).
- **Corrective scope (mission-authorized):** FIX ONLY embedding coverage. CASE A cache hit -> reuse the realization-A embedding exactly. CASE B cache miss but file has embeddable units -> materialize/split the Stage-5 blob using the SAME frozen unit splitter and embed the missing units with `qwen/qwen3-embedding-8b` @ DeepInfra (fallback disabled; same realization-A MAX-cosine aggregation). CASE C file truly has no embeddable unit -> dense score MUST be NaN/missing per the frozen DEV semantics. NEVER use a finite sentinel (-1e9/-1e6/-999999) for no-unit or missing-embedding state. HARD PIPELINE GUARDS: fail if `abs(dense_file_score) > 10` for any finite candidate dense score; fail if a blob has embeddable units but no embedding result; fail if a required cache lookup silently resolves to a finite sentinel; fail if dense score generation produces out-of-range values without an explicit documented reason; NO silent fallback.
- **Budget:** hard incremental ceiling **$0.25** for new embedding calls (live price verified before call 1; STOP before paid calls if projected > $0.25). No provider fallback, no model substitution, no extra realization.
- **Frozen scientific inputs (UNCHANGED):** Qwen model; provider; realization A; unit splitter; file aggregation; feature definitions; feature order; scaler; LR coefficients; LR intercept; threshold 0.20; candidate constants; Sparse predictions (persisted write sets REUSED, no Sparse LLM re-call); parent-only history rules; endpoint; bootstrap; seed 20260920.
- **Required before the corrected evaluator loads any Stage-5 label:** label-free parity gate (`reports/stage5_parity_gate.json`) with embedding coverage 100%, zero finite sentinels, NaN/no-unit rate within ±3pp of DEV per repo, finite dense-score range within [-1.5,+1.5], feature-distribution parity within 3 DEV SD, candidate-row-count parity within ±25%, exact 11-feature schema, frozen model/scaler/threshold hashes. An INDEPENDENT parity audit must recompute every check without importing the primary analyzer. If any parity check fails: STOP; do NOT inspect corrected Stage-5 labels/results; do NOT loosen the rule.
- **Rejected:** reopening method selection; V3; feature/model/threshold/candidate-budget/Qwen-realization/endpoint changes; new tuning; new DEV fitting; regenerating Sparse outputs; opening Saleor RESERVE; sampling Saleor RESERVE labels; LocBench; JEPA/energy-based models; adaptive-k; deleting or moving historical tags/artifacts; reusing `stage5-v2-final-evaluation-2026-09-20` as the corrected tag.
- **Evidence:** docs/STAGE5_EXECUTION_DEFECT_CORRECTION_IMPACT_DECLARATION_2026-09-20.md, reports/STAGE5_EXECUTION_DEFECT_REPORT_2026-09-20.md, reports/stage5_execution_defect_reproduction.json, reports/stage5_parity_gate.json, reports/STAGE5_CORRECTED_REEXECUTION_2026-09-20.md, this decision.
- **Revisit:** at corrected-run closure record `STAGE5_CORRECTED_REEXECUTION_POSITIVE` / `_NEGATIVE` / `_MIXED`; `IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED` holds regardless; clean untouched replication (Saleor RESERVE) remains a SEPARATE future mission awaiting Ahmed authorization.

## Decision P87 - STAGE5_V2 execution-defect corrected re-execution: STAGE5_CORRECTED_REEXECUTION_POSITIVE (2026-09-20)

- **Status:** ADOPTED (mission STAGE5_V2_EXECUTION_INVALID_EMBEDDING_COVERAGE_DEFECT; T3 corrective re-execution on the SAME 139 exposed tasks; P86 superseded the original FAIL)
- **Context:** P86 declared the first Stage-5 evaluation EXECUTION-INVALID (finite -1e9 sentinel embedding-coverage defect in `scripts/stage5_v2_dense_scores.py`) and superseded `STAGE5_V2_FINAL_CONFIRMATION_FAIL`. This decision records the corrected re-execution outcome.
- **Execution (corrective, NOT untouched; paid $0.019985 << $0.25):** embedding coverage repaired (CASE A cache hit reuse realization-A; CASE B 1,241 missing Stage-5 blobs materialized from the pinned git caches at the task parent commit with SHA-256 verified, 1,489 missing code units embedded with qwen/qwen3-embedding-8b @ DeepInfra $0.019927/1,992,694 tokens + 139 queries $0.000058/5,827 tokens; CASE C no-unit files -> NaN). Full dense-score/memory/candidate-rows re-computation with the frozen pipeline. Sparse write sets REUSED exactly (no Sparse LLM re-call; candidate in_sparse == persisted write sets 139/139). Label-free parity gate `reports/stage5_parity_gate.json` **8/8 PASS** + independent parity audit `reports/stage5_parity_gate_audit.json` **8/8 PASS** (0 embedding misses; 0 finite sentinels; NaN rate dc 5.19%/saleor 8.07% within ±3pp of DEV 5.27%/8.35%; finite dense range [0.092,0.820]; feature-distribution parity within 3 DEV SD; candidate-rows/task within ±25%; exact 11-feature schema; frozen model hash 8925d29a + threshold 0.20).
- **Corrected primary result (independently audited 13/13 PASS):** pooled V2 F1 **0.3419** vs Sparse 0.2857; **Delta F1 = +0.0562, 95% CI [+0.0185, +0.0945]** (excludes zero, positive); criterion A PASS; criterion B PASS (djangoCMS +0.0228, Saleor +0.0780, both positive). Per-repo: dc Sparse 0.3028 vs V2 0.3256; Saleor Sparse 0.2744 vs V2 0.3524. **Verdict `STAGE5_CORRECTED_REEXECUTION_POSITIVE`** (NOT `STAGE5_V2_FINAL_CONFIRMATION_PASS`, because the population is no longer untouched).
- **Defect impact (invalid vs corrected):** 60,485 file scores changed; 4,438 candidate probabilities changed; 81 selected flags changed; 60 forced-zero Sparse files -> 39 restored by corrected V2; 34 affected Sparse proxy TPs -> 27 retained by corrected V2; pooled TP 70->113, FP 178->179, FN 299->256, F1 0.2269->0.3419 (Δ +0.1150). The embedding-coverage defect MATERIALLY changed the Stage-5 conclusion.
- **Scientific status:** the corrected run is a DIAGNOSTIC/CORRECTIVE re-execution on already-exposed tasks. It answers ONLY: "What would the original frozen Stage-5 V2 pipeline have produced if the documented execution bug had not corrupted dense features?" It is NOT untouched confirmation, NOT independent confirmation, NOT a second clean Stage-5 test. The old negative Stage-5 numbers are NOT cited as evidence about V2 generalization.
- **Clean untouched replication:** NOT executed. `CLEAN_SALEOR_RESERVE_REPLICATION_AWAITS_AHMED_AUTHORIZATION`; draft preregistration prepared (`docs/CLEAN_SALEOR_RESERVE_REPLICATION_DRAFT_PREREGISTRATION_2026-09-20.md`: Saleor-only, 150 RESERVE sampled seed 20260920, corrected frozen V2 pipeline, same parity gate, Sparse comparator, Delta F1 endpoint, projected ~$0.61-0.62). No untouched djangoCMS confirmation population remains in the current split.
- **Preserved (unchanged, NOT rewritten):** P86; `STAGE5_V2_FINAL_CONFIRMATION_FAIL` historical label (superseded, NOT deleted); `IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED`; `INDEPENDENT_DENSE_RETRIEVAL_REPLICATED`; `CALIBRATED_SET_SELECTION_V1_FAIL`; `PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL`; `ISSUE_GROUNDED_INTENT_SIGNAL_NOT_SUPPORTED`; preregistration + invalid-evaluation tags and artifacts; all P1-P86; Saleor RESERVE SEALED.
- **Rejected:** opening Saleor RESERVE; new djangoCMS mining; new localization method; V3; threshold/feature/model/candidate-budget/endpoint changes; new tuning; new DEV fitting; regenerating Sparse outputs; LocBench; JEPA/energy-based models; adaptive-k; deleting historical tags; reusing `stage5-v2-final-evaluation-2026-09-20` as the corrected tag.
- **Evidence:** reports/STAGE5_CORRECTED_REEXECUTION_2026-09-20.md, reports/stage5_corrected_reexecution_result.json, reports/stage5_corrected_secondary_result.json, reports/stage5_corrected_impact_analysis.json, reports/stage5_corrected_result_audit.json, reports/stage5_parity_gate.json, reports/stage5_parity_gate_audit.json, reports/stage5_execution_defect_reproduction.json, research/stage5-v2-final/*_corrected.*, scripts/stage5_corrected_*, docs/STAGE5_EXECUTION_DEFECT_CORRECTION_IMPACT_DECLARATION_2026-09-20.md, tests/unit/test_stage5_corrected_reexecution.py (24/24), new tag `stage5-corrected-reexecution-2026-09-20`.
- **Revisit:** any future clean untouched confirmation (Saleor RESERVE) is a SEPARATE mission awaiting Ahmed authorization; thesis direction remains THESIS_AND_PAPER_EVIDENCE_CLOSURE with external-validity + end-to-end regeneration as the next phase.

## Decision P88 - SALEOR_RESERVE_300_RMCSS preregistration: ONE clean untouched evaluation APPROVED BY AHMED (2026-09-20)

- **Status:** ADOPTED (mission SALEOR_RESERVE_300_RMCSS; T3 final planned IMPACT-LOCALIZATION evaluation; recorded APPEND-ONLY and BEFORE any Saleor RESERVE target outcome access / unsealing)
- **Approved by:** Ahmed (mission prompt authorization) — ONE clean untouched evaluation on a preregistered sample of exactly 300 Saleor RESERVE tasks.
- **Terminology freeze:** **SIP — Sparse Impact Plan** (baseline; old names Sparse-v2 / sparse impact plan). **RM-CSS — Repository-Memory Calibrated Set Selection** = SIP + Qwen dense ranking + parent-only Repository Memory + calibrated ADD/KEEP/DROP set selection (old name V2). Thesis-facing/report terminology only; historical code identifiers/commits/tags/artifact paths NOT renamed (`docs/GLOSSARY.md`).
- **Preserved (unchanged, NOT rewritten):** all historical results; invalid Stage-5 FAIL (historical only); `STAGE5_CORRECTED_REEXECUTION_POSITIVE` (with exposed-population limitation); all P1-P87.
- **Verified evidence (motivation only):** djangoCMS SIP 0.3028 / RM-CSS 0.3256 / Δ +0.0228; Saleor SIP 0.2744 / RM-CSS 0.3524 / Δ +0.0780; pooled SIP 0.2857 / RM-CSS 0.3419 / Δ +0.0562 CI [+0.0185, +0.0945].
- **Cross-repo diagnostic verified on exposed data** (`reports/v2_cross_repo_transfer.json`): djangoCMS DEV → Saleor DEV Δ +0.0745 CI [+0.0441, +0.1061]; djangoCMS DEV → corrected exposed Saleor Stage-5 Δ +0.0776 CI [+0.0237, +0.1312]; django-only threshold 0.20; reverse (Saleor DEV → djangoCMS DEV) Δ +0.0213 CI [−0.0145, +0.0559] (weak, crosses zero). EXPOSED-DATA MOTIVATION ONLY.
- **Preregistration frozen BEFORE unsealing:** population Saleor RESERVE 1,086 → sample EXACTLY 300 (seed 20260920, `numpy.random.default_rng`); sample manifest SHA-256 `445b5e9d…` (selected_ids txt); label-free preflight 300/300 OK, 0 exclusions; temporal descriptor wording **B** (`same/overlapping-period disjoint-commit Saleor replication`, NOT temporal generalization); PRIMARY model = frozen corrected RM-CSS deployment artifact (config_sha256 `8925d29a…`, threshold 0.20, realization A, 11 features, file SHA-256 `7e9f82bc…`); SECONDARY `DJANGO_ONLY_RMCSS_TRANSFER_MODEL` (djangoCMS DEV only 174 tasks, threshold 0.20, artifact SHA-256 `efb38c07…`, file SHA-256 `7e5a46a9…`); SIP failure semantics (transport retry max 3 byte-identical; schema-invalid/truncated/completed-empty/parse-invalid → fail-closed EMPTY set with sparse_empty=1); Qwen embedding-coverage rule (CASE A reuse / CASE B embed missing units / CASE C NaN; no finite sentinels; |score|>10 → RAISE/STOP); label-free parity gate 10 checks + independent parity audit; PRIMARY endpoint DeltaF1 = F1_RMCSS − F1_SIP, task-paired bootstrap 10,000 seed 20260920, CI95 [Q2.5,Q97.5]; PRIMARY success rule PASS/INCONCLUSIVE/FAIL; SECONDARY transfer endpoint + labels (secondary, non-gating); cost ceiling **$1.50**; prohibited actions frozen. Preregistration SHA-256 `097b8625…`.
- **Irreversible checkpoint:** `SALEOR_RESERVE_300_IRREVERSIBLE_CHECKPOINT` printed after preregistration + parity PASS and BEFORE label access. ONE evaluation under this exact frozen protocol.
- **Rejected:** new localization method; V3; feature search; threshold tuning; Energy-Based models; adaptive-k; negative association rule redesign; JEPA/world models; provenance-by-construction; issue re-mining; new embedding models; LocAgent/Agentless runs; opening more than the preregistered 300 Saleor RESERVE tasks; modifying RM-CSS after unsealing; replacement sampling; label-count-based exclusion.
- **Evidence:** docs/SALEOR_RESERVE_300_RMCSS_IMPACT_DECLARATION_2026-09-20.md, docs/GLOSSARY.md, reports/SALEOR_RESERVE_300_RMCSS_PREREGISTRATION_2026-09-20.md, reports/saleor_reserve_300_rmcss_preregistration.json, reports/v2_cross_repo_transfer.json, research/saleor-reserve-300-rmcss/*, scripts/saleor_reserve_300_{sample,preflight,temporal,transfer_model}.py, scripts/v2_cross_repo_transfer_diagnostic.py, this decision.
- **Revisit:** at closure record PASS/FAIL/INCONCLUSIVE + transfer PASS/INCONCLUSIVE/FAIL; `IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED` holds regardless; next phase END_TO_END_SELECTIVE_REGENERATION.

## Decision P89 - PRE-UNSEALING COST-CEILING AMENDMENT: $1.50 -> $1.75 (2026-09-20)

- **Status:** ADOPTED (mission SALEOR_RESERVE_300_RMCSS; pre-unsealing; Ahmed-authorized; recorded BEFORE any paid call and BEFORE any Saleor RESERVE outcome access)
- **Context:** the frozen preregistration (P88) set a hard incremental cost ceiling of $1.50. The exact label-free cost projection (rendered all 300 SIP prompts; chars->tokens ratio 0.31367 calibrated on the 80 stage-5 Saleor IT tasks; live prices prompt $0.30/M completion $1.00/M; embeddings $0.01/M) projected **total $1.650909 > $1.50**, triggering the frozen mandatory stop. ZERO paid calls were made; ZERO outcomes were opened.
- **Decision:** raise ONLY the hard incremental cost ceiling from **$1.50** to **$1.75**. Reason: preserve the preregistered n=300 sample (statistical power) rather than alter it; $1.75 provides a small execution cushion over the $1.650909 projection (breakdown: SIP $1.612393 + missing embeddings $0.038390 + queries $0.000126).
- **Explicitly UNCHANGED:** sample size 300; sample IDs; sample seed 20260920; SIP baseline; primary RM-CSS; django-only transfer model; feature set; thresholds (0.20/0.20); Qwen realization A; candidate constants; primary endpoint; secondary endpoint; bootstrap (10,000 seed 20260920); success criteria; exclusion rules; parity gate; all other scientific design fields.
- **Timing:** zero paid calls before this amendment; zero outcomes opened before this amendment (verified: no hidden proxies materialized, no change_statuses, no SIP/embedding calls).
- **Evidence:** DECISIONS.md P88 (original ceiling $1.50), research/saleor-reserve-300-rmcss/saleor_reserve_300_cost_projection.json (projected $1.650909), reports/SALEOR_RESERVE_300_RMCSS_PREREGISTRATION_2026-09-20.md + .json (amendment section + new SHA), tag `saleor-reserve-300-rmcss-preregistration-cost-amendment-2026-09-20`.
- **Revisit:** at final closure report actual total API cost vs $1.75.

## Decision P90 - SALEOR_RESERVE_300_RMCSS outcome: PRIMARY PASS + SECONDARY CROSS-REPO TRANSFER PASS (2026-09-20)

- **Status:** ADOPTED (mission SALEOR_RESERVE_300_RMCSS; final clean untouched replication on 300 Saleor RESERVE tasks; Ahmed-authorized ONE evaluation; outcomes opened once after parity)
- **Context:** P88 froze the preregistration (n=300, seed 20260920, sample manifest SHA `445b5e9d…`, primary frozen RM-CSS artifact config_sha256 `8925d29a…` thr 0.20, secondary `DJANGO_ONLY_RMCSS_TRANSFER_MODEL` thr 0.20 artifact SHA `efb38c07…`, SIP protocol, P86 embedding-coverage rule, 10-check parity gate, endpoints, bootstrap 10,000 seed 20260920, ceiling $1.50). P89 amended ONLY the ceiling to $1.75 (projected $1.650909; zero paid calls / zero outcomes before amendment).
- **Execution (per frozen protocol; actual cost $1.619525 < $1.75):** label-free public bundles (300/300) built; SIP executed 300/300 calls (228 succeeded / 70 completed-empty / 2 transport-failed HTTP 429 after 3 byte-identical retries -> fail-closed EMPTY; 5,094,731 tokens; $1.59349); 2,076 missing Qwen units + 299 unique queries embedded (P86-corrected, $0.026035; 0 sentinels; 0 unresolved misses); RM-CSS candidate/features built label-free (proxy EMPTY until outcome-open); label-free parity gate **10/10 PASS** + independent parity audit **11/11 PASS**; irreversible checkpoint printed; 300 outcomes opened ONCE (921 proxy files); evaluation + audits.
- **PRIMARY RESULT:** RM-CSS TP/FP/FN 283/382/638 (P 0.4256 / R 0.3073 / F1 0.3569 / FNR 0.6927) vs SIP 193/344/728 (P 0.3594 / R 0.2096 / F1 0.2647 / FNR 0.7904); **Delta F1 +0.0921, 95% CI [+0.0691, +0.1156]** (excludes zero); Delta P [+0.0259,+0.1034], Delta R [+0.0752,+0.1207], Delta FNR [−0.1208,−0.0753]. **Verdict `SALEOR_RESERVE_300_RMCSS_PASS`.**
- **SECONDARY CROSS-REPO TRANSFER RESULT:** django-only RM-CSS TP/FP/FN 262/363/659 (P 0.4192 / R 0.2845 / F1 0.3389 / FNR 0.7155) vs SIP 0.2647; **Delta F1 +0.0742, 95% CI [+0.0535, +0.0957]** (excludes zero). **Verdict `SECONDARY_CROSS_REPO_TRANSFER_PASS`** (a policy trained ONLY on djangoCMS DEVELOPMENT labels produced a positive file-set F1 improvement over SIP on the untouched Saleor sample). SECONDARY, non-gating.
- **Ranking (descriptive):** Acc@1/3/5 0.4833/0.2867/0.3067; Hit@5 0.7700; Recall@1/3/5 0.2333/0.4238/0.5162; |G|=1 (89 tasks) Hit@1 0.3933.
- **Decision:** **`SALEOR_RESERVE_300_RMCSS_PASS`** + **`SECONDARY_CROSS_REPO_TRANSFER_PASS`**. Allowed claims (frozen): "Frozen RM-CSS replicated a positive affected-file-set F1 improvement over SIP on a preregistered untouched Saleor RESERVE sample." + "The same RM-CSS learning recipe, trained using djangoCMS DEVELOPMENT labels only, also improved F1 over SIP on the untouched Saleor sample." Forbidden: untouched djangoCMS confirmation; all-repository/language generalization; universal superiority; SOTA; direct superiority over LocAgent/RepoMem.
- **Preserved (unchanged):** `IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED` (permanent); `IMPACT_LOCALIZATION_EVIDENCE_COLLECTION_CLOSED` NOT recorded; all prior decisions P1-P89; all historical reports/tags; invalid Stage-5 FAIL historical; `STAGE5_CORRECTED_REEXECUTION_POSITIVE` (exposed-population limitation). Remaining untouched Saleor RESERVE: **786 tasks**. No post-unseal tuning; no V3.
- **Rejected:** new localization method; V3; feature/threshold/candidate-budget changes; Energy-Based/adaptive-k/negative-association-rule/JEPA redesigns; provenance-by-construction; issue re-mining; new embedding models; LocAgent/Agentless runs; opening more than the 300; modifying RM-CSS after unsealing.
- **Evidence:** reports/SALEOR_RESERVE_300_RMCSS_FINAL_REPLICATION_2026-09-20.md, reports/saleor_reserve_300_rmcss_result.json, reports/saleor_reserve_300_rmcss_secondary_metrics.json, reports/saleor_reserve_300_rmcss_result_audit.json, reports/saleor_reserve_300_parity_gate.json, reports/saleor_reserve_300_parity_gate_audit.json, reports/saleor_reserve_300_efficiency.json, research/saleor-reserve-300-rmcss/*, scripts/saleor_reserve_300_*, reports/v2_cross_repo_transfer.json, this decision.
- **Revisit:** next phase = `END_TO_END_SELECTIVE_REGENERATION` (prepared handoff, NOT executed); final tag `saleor-reserve-300-rmcss-final-replication-2026-09-20`.

---

## Decision WP0 — G7 Ground-Truth Leakage Fix (ArtifactUniverse de-repo) (2026-09-20)

- **Status:** ADOPTED (this WP-0; measurement-infrastructure repair, NOT a scientific claim)
- **Context:** The execution Runner could derive `ArtifactUniverse` from
  `scenario.expected_affected_artifacts` on the legacy impact-only path,
  exposing ground truth (G7). A valid E2E execution must derive the eligible
  artifact universe from the parent-commit repository state.
- **Decision:**
  1. `BenchmarkRunner._build_artifact_universe` now derives the universe from
     the parent repository state (active snapshot via `resolve_allowed_artifacts`)
     for every non-fixture execution.
  2. Legacy fixture behavior (universe from `expected_affected_artifacts`) is
     preserved ONLY behind an explicit `allow_ground_truth_universe` flag
     (default `False`), auditable on the produced `RunRecord`.
  3. Fail-closed config: `allow_ground_truth_universe=True` is incompatible
     with `enable_regeneration=True` and with `selection_only=True`; non-bool
     flag rejected.
  4. Added pass-through in `PipelineConfig` -> `RunnerConfig`.
- **Rationale:** removes the documented G7 ground-truth leakage blocker before
  any scientific E2E execution. Scientific scope unchanged; frozen evidence
  unchanged; localization science (SIP/RM-CSS) untouched.
- **Scope amendment:** `WP0_SCOPE_AMENDMENT_RUNRECORD_AUDITABILITY`
  (ACCEPTED) authorized the minimal additions to
  `src/benchmark/core/models.py` (RunRecord auditable field) and
  `src/benchmark/execution/pipeline.py` (flag pass-through). Scientific scope
  changed: NO. Frozen evidence changed: NO.
- **Impact:** production/selection-only/regeneration executions are now
  ground-truth-independent; legacy fixture tests moved to explicit opt-in.
  RED->GREEN regression proven; AC-0.1..AC-0.5 PASS; independent audit 6/6
  PASS. Scientific API spend $0.00.
- **Evidence:** `tests/unit/test_artifact_universe_no_ground_truth.py`,
  `scripts/ac01_hidden_truth_independence.py`,
  `scripts/ac03_universe_sanity.py`, `scripts/wp0_independent_audit.py`,
  `selective_updates/records/SU-0012-artifact-universe-derepo.md`.
- **Revisit:** WP-1 Repository-Agent Selection-Only baseline
  (DEFERRED, AWAITING AHMED AUTHORIZATION after WP-0); WP-2 E2E Phase-0
  instrument (DEFERRED). G6 F2P/P2P oracle still unresolved; no E2E
  scientific claims allowed yet.

---

## WP-0 Event / Decision / Deferral Ledger (2026-09-20) — append-only

| # | id | title | status | reason | evidence | sci-scope | frozen-evidence | reopen |
|---|---|---|---|---|---|---|---|---|
| A | LED-A | IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED | ACCEPTED | permanent for current thesis | P88/P89/P90 | NO | NO | new mission + frozen hypothesis |
| B | LED-B | 786 Saleor RESERVE outcomes remain unread | ACCEPTED | hard boundary; outcomes untouched | WP-0 hard boundary B2 | NO | NO | n/a |
| C | LED-C | WP-1 Repository-Agent Selection-Only same-protocol baseline | DEFERRED | requires Ahmed authorization after WP-0 | PROGRESS.md | NO | NO | Ahmed explicit authorization after WP-0 |
| D | LED-D | WP-2 E2E Phase-0 instrument on Todo | DEFERRED | requires WP-0 PASS + Ahmed authorization | PROGRESS.md | NO | NO | WP-0 PASS + Ahmed authorization |
| E | LED-E | G6 F2P/P2P real-task oracle | DEFERRED | oracle not yet established | docs/ | NO | NO | WP-1/2 progress |
| F | LED-F | NestJS external validity | FUTURE_WORK | cross-language | docs/CROSS_LANGUAGE_READINESS | NO | NO | future |
| G | LED-G | JabRef Java external validity | FUTURE_WORK | cross-language | docs/CROSS_LANGUAGE_READINESS | NO | NO | future |
| H | LED-H | Prometheus Go external validity | FUTURE_WORK | cross-language | docs/CROSS_LANGUAGE_READINESS | NO | NO | future |
| I | LED-I | Grafana Go+TypeScript true polyglot | FUTURE_WORK | cross-language | docs/POLYGLOT_REPOSITORY_FEASIBILITY | NO | NO | future |
| J | LED-J | Energy-Based Change-Set Completion | FUTURE_WORK | roadmap | reports/ | NO | NO | future |
| K | LED-K | Adaptive-k / negative association rules | FUTURE_WORK | roadmap | reports/ | NO | NO | future |
| L | LED-L | JEPA / Repository World Model | FUTURE_WORK | roadmap | reports/ | NO | NO | future |
| M | LED-M | Provenance-by-construction | FUTURE_WORK | roadmap | reports/PROVENANCE_BY_CONSTRUCTION_DIRECTION_NOTE | NO | NO | supervisor discussion |
| N | LED-N | Conformal Risk Control / risk-controlled scope | FUTURE_WORK | do not implement | roadmap | NO | NO | future |
| O | LED-O | Cost-optimal scope threshold / expected-cost objective | FUTURE_WORK | pending E2E regeneration/repair cost measurement | END_TO_END_MEASUREMENT_BOUNDARY | NO | NO | E2E cost measurement |
| P | LED-P | Validation-driven scope escalation | FUTURE_WORK | roadmap | roadmap | NO | NO | future |
| Q | LED-Q | Ripple competitive-position correction | ACCEPTED retraction + BLOCKED head-to-head | original +10.7/+43% mixed granularity; confounded by benchmark/language/macro vs micro/seed assumption; exact file-level seed treatment unresolved | WP-0 §1/§2 | NO | NO | Ripple exact file-level seed convention established from authors/replication |
| R | LED-R | Read-only macro/seed sensitivity diagnostics | ACCEPTED AS DIAGNOSTIC ONLY | 0.581/0.200 sensitivity bounds, not competitor/headline results | WP-0 §2 | NO | NO | n/a |
| S | WP0-AMEND | WP0_SCOPE_AMENDMENT_RUNRECORD_AUDITABILITY | ACCEPTED | hard requirement/AC-0.4 #5 needs RunRecord field + pipeline pass-through | this decision | NO | NO | n/a |

---

## Decision WP1-INT — WP-0 Integration / Governance Closure (2026-09-20)

- **Status:** IN_PROGRESS until main integration + both exports pass.
- **Context:** Integration/governance closure of the completed WP-0 (G7)
  ground-truth leakage fix. Tier T2. Scientific API spend $0.00.
- **Decisions appended (append-only):**

### OPENCODE_ENGLISH_ONLY_POLICY — ACCEPTED
- All OpenCode-generated content must be English only (chat, STOP reports,
  code comments, docs, Markdown, governance, commit messages, tests,
  generated prompts/handoffs). No Arabic in repository files or status
  reports. Historical content needs no retrospective translation. Arabic
  communication with Ahmed is outside OpenCode.
- Scope change: NO scientific scope change.

### MANDATORY_DUAL_EXPORT_POLICY — ACCEPTED
- Every T2/T3 closure or STOP requires BOTH FULL (`project-*.zip`) and
  TRUE LIGHT (`project-LIGHT-*.zip`) exports.
- Reason: OpenCode omitted the exports at two consecutive STOP/closure events
  and only generated them after Ahmed explicitly reminded it. This removes
  reliance on operator memory.
- Scientific scope changed: NO. Frozen evidence changed: NO.

### WP0_INTEGRATION_CLOSURE — IN_PROGRESS
- Status IN_PROGRESS until main integration and both exports pass.

### WP1_REPOSITORY_AGENT_SELECTION_BASELINE — DEFERRED / AWAITING_AHMED_AUTHORIZATION
- Do NOT execute. Draft specification only at
  `docs/WP1_REPOSITORY_AGENT_SELECTION_ONLY_BASELINE_DRAFT.md`.

---

## Decision WP1A - Repository-Agent Selection Baseline Preparation (2026-09-21)

- **Status:** ADOPTED (this WP-1a; zero-API preparation; Tier T3; $0.00
  scientific API spend; freezes future WP-1b invariants)
- **Context:** WP-1 (Repository-Agent Selection-Only Baseline) must be prepared
  before any paid run. The WP-1 draft claimed the SIP scientific model as
  DeepSeek; the frozen Saleor-300 SIP run records mechanically show
  `qwen/qwen3-coder @ deepinfra/turbo` (300/300 consistent). `candidate_rows
  _saleor300.parquet` contains a `label` column needing a prediction-side
  boundary. The future WP-1b must compare repository_agent vs SIP vs RM-CSS on
  a frozen main-50 sample with a separate calibration-3 set.
- **Decision:**
  1. **Model parity (AC-1A.1):** SIP scientific model mechanically recovered as
     `qwen/qwen3-coder @ deepinfra/turbo` (exact route
     `openrouter:qwen/qwen3-coder@deepinfra/turbo`, temp 0.0, cap 16384,
     300/300). The WP-1 draft DeepSeek claim is CORRECTED. The future WP-1b
     repository-agent generative arm MUST use the same Qwen3-Coder identity.
     The OpenCode coding model is NOT the scientific arm model. Artifact:
     `research/wp1a/sip_scientific_model_provenance.json`.
  2. **Label isolation (AC-1A.2):** prediction-side loaders drop/deny
     label/outcome columns at the boundary (`src/benchmark/wp1a/schema.py`);
     repository-agent universe comes from parent-state/public sources only.
  3. **Exact 300 re-derivation (AC-1A.3):** deterministic zero-API per-task
     SIP/RM-CSS re-derivation reproduces the authoritative headline values
     EXACTLY (SIP F1 0.2647462277, RM-CSS F1 0.3568726356, DeltaF1
     +0.09212640785196952). Persisted with SHA-256 manifest; historical
     Saleor-300 artifact NOT replaced.
  4. **Sample freeze (AC-1A.4):** main n=50 = first 50 of the frozen
     Saleor-300 ordering (SHA `9b26ad59…`); calibration n=3 = deterministic
     complement draw, seed 20260921 (SHA `23f520d8…`); intersection empty;
     both from the already-opened 300; 786 RESERVE untouched.
  5. **Intent parity (AC-1A.5):** 53/53 canonical hash match to the stored SIP
     intent (`research/wp1a/wp1a_intent_parity.json`); future agent input MUST
     be byte/canonical-hash-identical.
  6. **Frozen agent protocol (AC-1A.6):** `wp1a_frozen_agent_protocol.json`
     freezes the authoritative iterative repository-agent protocol
     (MAX_AGENT_CALLS=8, control cap 512, tools, schemas, parent-only boundary,
     allow_ground_truth_universe=False, fail-closed semantics);
     mock-executable with a stub backend.
  7. **Failure semantics (section 8):** ALL-TASKS / FAIL-CLOSED primary
     analysis; EMPTY prediction on no-paths/transport/deadline/malformed;
     sensitivity excludes ONLY pre-defined infrastructure failures, reported
     alongside primary.
  8. **Shared scorer (AC-1A.7):** one scorer for repository_agent/SIP/RM-CSS
     (TP/FP/FN/P/R/FNR/F1, mean set size, empty rate; paired task bootstrap
     10,000 seed 20260920; CI crossing zero = NO_DIFFERENCE_DETECTED_AT_THIS_N).
  9. **Accounting (AC-1A.8):** per-arm tokens/calls/wall/USD; RM-CSS TWO views
     (marginal/per-change vs one-time setup) with amortized N=50/N=300; no
     double counting; latency descriptive.
  10. **Budget (AC-1A.9):** label-free model; recommended future ceiling ~$1.10
      for Ahmed review (NOT auto-accepted); cumulative USD guard before each
      paid request; main-run ceiling frozen before main task 1; hitting the
      ceiling mid-main-run = `BUDGET_ABORT_INVALID_FOR_PRIMARY_COMPARISON`
      (no ordered partial n<50 primary table).
  11. **Outcome categories (section 12):** RM_CSS_COST_QUALITY_DOMINANCE /
      COST_QUALITY_TRADEOFF / NO_RM_CSS_EFFICIENCY_ADVANTAGE /
      RM_CSS_EFFICIENCY_HYPOTHESIS_FALSIFIED; latency not a hard gate;
      no universal/SOTA claim.
  12. **Independent audit (AC-1A.10):** 19/19 PASS without importing audited
      helpers (`research/wp1a/wp1a_independent_audit.json`).
- **Rationale:** freezes scientific harness semantics, leakage boundaries,
  accounting and future experiment invariants BEFORE any paid WP-1b call.
- **Impact:** WP-1a acceptance criteria AC-1A.1..AC-1A.12 ALL PASS
  (`research/wp1a/wp1a_acceptance_report.json`); new selective-update record
  `SU-0013-repository-agent-selection-baseline-preparation.md`. No production
  runtime change required (existing iterative agent already parent-only).
- **Evidence:** `docs/WP1A_IMPACT_DECLARATION_2026-09-21.md`,
  `research/wp1a/*`, `scripts/wp1a_*.py`, `src/benchmark/wp1a/*`,
  `tests/unit/test_wp1a_*.py`, this decision.
- **Revisit:** WP-1b Calibration + Main n=50 Selection Run — AWAITING AHMED
  AUTHORIZATION. NOT executed here.

### WP1A_MODEL_PARITY - ACCEPTED
- SIP scientific model mechanically recovered = `qwen/qwen3-coder @
  deepinfra/turbo` (not DeepSeek). Future agent arm MUST use the same model.
- Scope change: NO scientific scope change.

### WP1A_LABEL_ISOLATION - ACCEPTED
- Prediction-side loaders deny label/outcome columns at the boundary;
  repository-agent universe is parent-state/public only.
- Scope change: NO.

### WP1A_SAMPLE_FREEZE - ACCEPTED
- main n=50 + calibration n=3 frozen, disjoint, deterministic, label-free,
  from the already-opened 300 only.
- Scope change: NO.

### WP1A_FAILURE_SEMANTICS - ACCEPTED
- ALL-TASKS / FAIL-CLOSED primary; EMPTY prediction on no-paths/transport/
  deadline/malformed; no silent exclusions.
- Scope change: NO.

### WP1A_COST_ACCOUNTING - ACCEPTED
- Two RM-CSS cost views (marginal + setup) + amortized N=50/N=300; no double
  counting; latency descriptive.
- Scope change: NO.

### WP1A_BUDGET_ABORT - ACCEPTED
- Cumulative USD guard before each paid request; main-run ceiling frozen before
  main task 1; ceiling hit mid-main-run =
  `BUDGET_ABORT_INVALID_FOR_PRIMARY_COMPARISON`.
- Scope change: NO.

### WP1B_CALIBRATION_AND_MAIN - AWAITING_AHMED_AUTHORIZATION
- WP-1b Calibration + Main n=50 Selection Run NOT started; requires Ahmed
  authorization after reviewing the WP-1a STOP report.

---

## Decision WP1B_G1_NI_MARGIN — DECISION REQUIRED (2026-09-21)

- **Status:** BLOCKER G1 — DECISION REQUIRED. No authoritative pre-result
  artifact freezes an F1 non-inferiority margin for the WP-1b selection-only
  comparison.
- **Provenance:** DA-08 Δ=0.05 governs regression pass rate (H2), not F1;
  docs/EXPERIMENTAL_DESIGN_V2.md H1 defines F1 NI Δ=0.05 for
  hybrid_selective vs epository_agent (candidate, authority not
  established for this experiment); WP-1a scorer schema explicitly says "no
  non-inferiority margin is silently chosen"; WP-1a cost-quality categories
  use a point-estimate rule.
- **Decision:** Do NOT invent a margin. Prepared
  docs/WP1B_NI_MARGIN_DECISION_REQUIRED_2026-09-21.md +
  rtifacts/wp1b_ci_decision_rule_preregistration_2026-09-21.json. NO PAID
  WP-1b EXECUTION IS AUTHORIZED UNTIL THIS VALUE IS FROZEN.
- **Scope change:** NO (no margin invented).

## Decision WP1B_G2_COMPLETION_CAP — DECISION REQUIRED (2026-09-21)

- **Status:** BLOCKER G2 — DECISION REQUIRED. 512 (pilot-derived) vs 1024
  (v1.1 scientific-run value) cannot be resolved from valid prospective
  evidence alone.
- **Decision:** Do NOT silently change 512 to 1024. Prepared
  docs/WP1B_AGENT_COMPLETION_CAP_PROVENANCE_2026-09-21.md +
  docs/WP1B_AGENT_COMPLETION_CAP_AMENDMENT_2026-09-21.md (PROPOSED,
  NOT EFFECTIVE). Paid WP-1b blocked until the cap decision is made.
- **Scope change:** NO.

## Decision WP1B_G3_LOOP_SEMANTICS — INSTRUMENTED (2026-09-21)

- **Status:** Resolved. Forced-final/round-cap precedence derived from code
  (iterative_agent.py) and frozen protocol; no code/protocol contradiction.
- **Decision:** Add behavior-preserving truncation/EMPTY telemetry to
  IterativeRepositoryAgentStrategy + src/benchmark/wp1b/telemetry.py;
  document state machine in
  docs/WP1B_AGENT_LOOP_TERMINATION_SEMANTICS_2026-09-21.md. Transport-retry
  count gap recorded (frozen rule says max 3; backend default 1) — WP-1b must
  configure/confirm before paid execution.
- **Scope change:** NO behavior change to selection.

## Decision WP1A_AUDIT_TERMINOLOGY_CORRECTION — ADOPTED (2026-09-21)

- **Status:** Terminology corrected. The WP-1a "independent audit 19/19" was a
  SAME-SESSION alternate-implementation cross-check (same execution context
  authored both implementation and checker). It is not an independent/external
  audit.
- **Decision:** Relabel WP-1a artifacts/scripts/docs accordingly
  (wp1a_independent_audit.json, wp1a_acceptance_report.json AC-1A.10,
  wp1a_frozen_agent_protocol.json runrecord_audit_field, WP-1 draft, WP-1a
  impact declaration, PROGRESS.md, test docstrings). Prepared a blind
  independent-audit packet at
  xports/wp1a_independent_audit_packet_2026-09-21/.
- **Scope change:** NO.

---

## Decision WP1A_INTEGRATION_CLOSURE — ADOPTED (2026-09-21)

- **Status:** WP-1a integration closed. All AC-1A.1..12 PASS; G1/G2 are
  explicitly FAIL-CLOSED blockers for paid WP-1b; G3/G4/G5/G6 closed; merged
  to main via --no-ff (merge commit 18652d6,
  "chore(wp1a): close integration and preregister WP1b blockers").
- **Merge rationale:** the contract authorizes merging when all integration
  criteria pass and G1/G2 ambiguities cannot contaminate WP-1b interpretation
  (WP-1b is fail-closed until both decisions are frozen; the merge-message
  example "close integration and preregister WP1b blockers" matches this
  mission). No squash; scientific amendment history preserved.
- **Post-merge re-audit:** 146 targeted passed / 1 skipped from main;
  recompute + cross-check PASS; full suite 3700/35/5 where the 5 failures are
  PRE-EXISTING baseline failures (also fail at 25950f); no material
  post-merge difference vs the branch.
- **Scope change:** NO scientific scope change.

## Decision PROGRESS_FORMAT — AUTHORITY RESOLUTION (2026-09-21)

- A5 of the task contract lists Arabic standing-section headers for
  PROGRESS.md; A12 and protocol v2 section 11 mandate English-only content.
- Resolution: PROGRESS.md stays in the existing English narrative format
  (English-only rule governs; the Arabic-header requirement conflicts with the
  standing English-only protocol). Recorded here as an explicit authority
  resolution; no silent convenience choice.

## Decision WP1B_CLOSURE_DECISION — BLOCKED (2026-09-21)

- **WP-1b is NOT ready for authorization.** G1 (NI margin) and G2 (completion
  cap) require Ahmed/supervisor prospective decisions. Paid WP-1b inference is
  not authorized and was not run. API spend for this mission: .00.
- Next permitted actions: resolve G1 (margin), then G2 (cap), then obtain
  spend authorization (contract section 25/35-16).

## Decision WP1B_PREFLIGHT_A1_ARTIFACT_ABSOLUTE_PATH_LEAK — COSMETIC DEFECT (2026-09-21)

- **Status:** RECORDED as a known cosmetic defect (not fixed in place).
- **Context:** three frozen tracked artifacts contain machine-absolute Windows
  paths (`C:\Users\...`): `artifacts/wp1b_variance_substudy_preregistration_2026-09-21.json`
  (`source_manifest`), `artifacts/wp1b_completion_cap_truncation_evidence.json`
  (`run_records_path`), `artifacts/wp1a_wp1b_closure_recomputation.json`
  (`v11_truncation_evidence.run_records_path`); `research/wp1a/wp1a_acceptance_report.json`
  rewrites `generated_utc` on every generator run.
- **Decision:** do NOT rewrite the already-frozen artifacts to "clean" their
  absolute paths (that would change their frozen SHA-256 values). All NEW
  artifacts created in this mission store repository-relative POSIX paths. The
  four generator scripts (`wp1a_independent_audit.py`, `wp1a_acceptance_report.py`,
  `wp1b_closure_recompute.py`, `wp1b_variance_substudy_selection.py`) now accept
  `--out <dir>` so tests redirect outputs into a pytest `tmp_path`; default
  human-run behaviour is byte-identical to before.
- **Scope change:** NO scientific scope change.

## Decision WP1B_G2_COMPLETION_CAP_2026_09_21 — EFFECTIVE (2026-09-21)

- **Status:** **EFFECTIVE** — authority D3. The proposed prospective amendment
  `docs/WP1B_AGENT_COMPLETION_CAP_AMENDMENT_2026-09-21.md`
  (`agent_control_max_completion_tokens` 512 → 1024) is APPROVED and in force
  for WP-1b.
- **Four recorded reasons:**
  1. The loop breaks on `finish_reason == "length"` at **any** of the 8 calls,
     not only the final one (`iterative_agent.py` line ~507 in `analyze_impact`).
     One verbose exploration reply at 512 ends the task as EMPTY.
  2. A cap only matters when it is hit. `max_tokens` stops generation; it does
     not change the tokens generated before that point. A reply that fits in 512
     tokens is unaffected by raising the cap. Raising it can only turn a
     would-be truncation into a complete reply.
  3. EMPTY counts as F1 = 0 for the agent. A 512 cap would therefore bias the
     comparison **toward RM-CSS**. 1024 is the conservative choice relative to
     our own hypothesis.
  4. The runaway-loop risk that motivated 512 is already bounded by
     `MAX_AGENT_CALLS = 8` and the per-request USD guard.
- **Artifacts:** `research/wp1b/wp1b_frozen_agent_protocol_v2.json` (v1
  `research/wp1a/wp1a_frozen_agent_protocol.json` untouched); WP-1b runner
  configuration passes 1024 explicitly (covered by a unit test asserting the
  WP-1b configuration resolves to 1024 and that the SIP / RM-CSS artifacts'
  SHA-256 values are unchanged).
- **Scope change:** this is the ONLY frozen scientific knob amended in this
  mission (G2, approved by D3). All other frozen knobs unchanged.
- **Revisit:** the value is immutable for a WP-1b run once it starts; any
  further change requires a new prospective amendment.

## Decision WP1B_PREFLIGHT_PHASE_B — ADOPTED (2026-09-21)

- **Status:** ADOPTED. Phase B pre-result freeze complete (B1–B7), zero API
  spend.
- **B1 Budget model v2 (G8):** `research/wp1b/wp1b_budget_model_v2.json`. The
  real ArtifactUniverse per task (production path,
  `allow_ground_truth_universe=False`, from each case's public
  `candidate_universe.json`) and the exact initial prompt (`_build_initial_prompt`)
  are rendered label-free. Worst case (8 calls, cap 1024) per task and totals
  for Calibration-3 / Main-50 / Main-150 / Main-297 / variance (15×3) with the
  1.5× safety factor. **No ceiling below worst case ×1.5** (cal $0.202 ≤ $0.25;
  main-297 $18.640 ≤ $21.50; variance $3.025 ≤ $3.50). Underestimate factor vs
  the v1 model ≈ 3.40×. Abort rule v2 preregistered (BUDGET_ABORT + nested
  MAIN_50 `UNDERPOWERED_FALLBACK` exception).
- **B2 Sample-size amendment (G9):** `research/wp1b/wp1b_main_297_manifest.json`
  (n=297, first 50 == WP-1a MAIN_50 exactly, calibration IDs absent, hashes
  recorded), `wp1b_main_150_manifest.json` (n=149; one calibration task
  `saleor-rc-349d46d906ad` removed), `wp1b_main_50_manifest.json` (unchanged
  reference). Execution order = manifest order. Power doc
  `docs/WP1B_POWER_AND_SAMPLE_SIZE_2026-09-21.md` re-derives R-C (AGREE).
- **B3 G1 freeze:** `research/wp1b/wp1b_ni_margin_frozen.json` +
  `docs/WP1B_NI_MARGIN_FROZEN_2026-09-21.md`: Δ=0.05 (sensitivity 0.03/0.10),
  pooled micro-F1, Q5 one-sided rule, inheritance record (margin only),
  coherence anchor + relative size. AC-P8 satisfied.
- **B4 Decision rules v2:** `research/wp1b/wp1b_decision_rules_v2.json` — P/S
  dual analysis, seven ordered quality verdicts, cost verdict + CHEAPER rule,
  five final categories; "dominance" retired for WP-1b. AC-P9 satisfied.
- **B5 G2 freeze (D3):** `WP1B_G2_COMPLETION_CAP_2026_09_21` EFFECTIVE (recorded
  above); `research/wp1b/wp1b_frozen_agent_protocol_v2.json` (cap 1024, v1
  untouched); runner-config test asserts 1024 + frozen SIP/RM-CSS artifacts
  unchanged. AC-P10 satisfied.
- **B6 Agent telemetry (G10):** additive per-call sidecar JSONL + per-task
  observation metrics in `iterative_agent.py` + `telemetry.py`; behavior
  preservation proven by the stub-backend golden test
  (`tests/unit/test_wp1b_agent_telemetry_golden.py`); disclosure
  `docs/WP1B_AGENT_BASELINE_DISCLOSURE_2026-09-21.md`. AC-P11 satisfied.
- **B7 Exploratory preregistration:** `research/wp1b/wp1b_exploratory_prereg.json`
  X1–X5, status `EXPLORATORY_PREREGISTERED`, computed only after the primary
  result is frozen and tagged, never part of the primary verdict. AC-P12.
- **Scope change:** the ONLY frozen scientific knob amended is G2 (D3). All
  other frozen knobs unchanged.

## Decision WP1B_CALIBRATION_3 — EXECUTED (2026-09-21)

- **Status:** EXECUTED. Calibration-3 run authorized (D6 = YES), protocol v2
  (cap 1024), frozen provider/route/pricing, cumulative USD guard ≤ $0.25.
- **Run:** exactly the 3 tasks in `research/wp1a/wp1_calibration_3_manifest.json`
  (`saleor-rc-349d46d906ad`, `saleor-rc-b05633dae118`, `saleor-rc-d52a55471bfc`)
  via `scripts/wp1b_calibration_run.py`; output under
  `research/wp1b/calibration-3-2026-09-21/`.
- **Cost:** cumulative **$0.081142 ≤ $0.25** (per task $0.033858 / $0.031420 /
  $0.015865). Per-task cost / B1 worst case ratios 0.636 / 0.617 / 0.523 — all
  within 1.2× (BUDGET_MODEL_V2_OK; no BUDGET_MODEL_V2_WRONG stop).
- **Gate:** CG-1..CG-9 all **PASS**
  (`research/wp1b/calibration-3-2026-09-21/wp1b_calibration_gate_result.json`).
- **Instrument findings:** 0 cap hits (finish_reason=length), 0 observation
  truncations (0%), 0 EMPTY predictions (all 3 valid finals), finish-reason
  distribution 24× `stop`; 24 per-call sidecar records.
- **Calibration is NOT scored against labels** (instrument check only).
- **STOP after Phase C:** the main run (MAIN_297) and the variance substudy are
  NOT authorized (D7 = NO). MAIN_297 requires a new explicit Ahmed
  authorization after he reviews this Calibration-3 STOP report.
- **Scope change:** NO scientific scope change.

## Decision WP1B_PREFLIGHT_APPENDIX_R_REDERIVATION — ALL_AGREE (2026-09-21)

- **Status:** ADOPTED. Every Appendix R number was independently re-derived with
  OpenCode's own code (`scripts/wp1b_appendix_r_rederivation.py`), NOT copied
  from the external reference evidence script (which was never committed).
  Comparison: `scripts/wp1b_appendix_r_agreement.py`.
- **Result:** **125 comparisons, 0 disagreements, status ALL_AGREE**:
  - R-A pooled micro-F1 (RESERVE-300 SIP 0.26474622770919065 / RM-CSS
    0.35687263556116017 / delta +0.09212640785196952; MAIN_50 0.30204 / 0.39231
    / +0.09027) — AGREE.
  - R-B RM-CSS reproduction: 0/300 mismatches with `continuous_features +
    boolean_features` order; 174/300 if `feature_names` order — AGREE.
  - R-C bootstrap SE (0.0377 / 0.0277) + power table n=50/150/297 — AGREE.
  - R-D budget (universe mean 810 [438,1140], editable-path tokens ~11190/call,
    underestimation factor 3.398) — AGREE.
  - R-E exploratory headroom (gold 921, in-pool 689/74.8%, TP 283/FP 382,
    FN in-pool 406/out-pool 232, oracle 0.856, bands) — AGREE.
- Artifact: `research/wp1b/wp1b_appendix_r_agreement.json` (125-entry
  machine-readable record).
- **Scope change:** NO scientific scope change.

## Decision WP1B_PREFLIGHT_A2_KNOWN_TEST_FAILURES — ACCEPTED (2026-09-21)

- **Status:** ADOPTED. Full suite on clean checkout: **5 failed / 3700 passed /
  35 skipped** at baseline `1ae7058`.
- **Decision:** the full-suite acceptance rule is now **set of failing node IDs
  == `artifacts/known_test_failures_2026-09-21.json`**. Recorded node IDs and
  classes in `docs/KNOWN_TEST_FAILURES_2026-09-21.md`:
  - REAL_DEFECT: `test_d96_..._no_github_machinery` (github.py docstring
    contains `GITHUB_TOKEN`),
    `test_model_identity_policy_..._current_facing_docs` (README model-name
    policy), `test_readme_markdown_tables_..._svg_fallbacks` (README SVG
    embed policy).
  - ENV_OR_DATA_MISSING: `test_stagec_..._all_six_gates_pass`,
    `test_stagec_..._pinned_source_available` (pinned djangocms repo absent).
- These are pre-existing (fail at the pre-WP-1a baseline `f25950f`) and are NOT
  fixed in this mission (contract forbids fixing a REAL_DEFECT outside WP-1
  code); each REAL_DEFECT got a `TODO.md` entry.
- **Scope change:** NO.

## Decision WP1B_PREFLIGHT_A4_EXPORT_MEMBER — RESOLVED (2026-09-21)

- **Status:** RESOLVED by restoring the archived member.
- **Context:** `KNOWN_ARCHIVED_EXPORT_MEMBER_MISSING` for
  `dist/pilot-kaggle-upload.zip` (+ `.sha256`) — the pilot artifacts were
  archived externally and absent locally, so the FULL export could not include
  them as required members.
- **Decision:** RESTORE the member: copied the provenance-verified D13R2
  candidate `pilot-kaggle-upload.zip` (SHA-256
  `65269528049b1f22f277c508f0b0db5b09d536e99fd31d306cfbbfb42e47ef9f`, sidecar
  matches) from `_historical_archive/` back into `dist/`. The expected-member
  list stays unchanged. No scientific effect.

## Decision WP1B_PREFLIGHT_A3_AUDIT_PACKET_V2 — ADOPTED (2026-09-21)

- **Status:** ADOPTED. Created `exports/wp1a_independent_audit_packet_2026-09-21_v2/`
  (v1 untouched as history).
- **Decision:** corrected `README_AUDITOR.md` adds two reproduction traps found
  by the external review: (1) **coefficient order** — in
  `research/stage5-v2-final/deployment_artifact.json` `lr_coef` is ordered
  `continuous_features + boolean_features`, NOT the `feature_names` order; using
  `feature_names` order fails on 174/300 tasks, the documented order gives
  0/300 mismatches; (2) **FULL-only inputs** — `benchmark_data/
  real_commit_impact_saleor/scientific/<case_id>/public/candidate_universe.json`
  and `dependency_graph.json` (530 cases each) plus
  `saleor_development_manifest.json` are excluded from the LIGHT export and are
  required for the RM-CSS reproduction and the WP-1a A7 universe check.
  `artifact_manifest.json`, `recompute_instructions.md` and `sha256sums.txt`
  updated to match (deployment artifact + full_file_scores + FULL-only list).
- **Scope change:** NO scientific scope change.

## Decision WP1B_TOOLFIX_LIVESTATUS_2026_09_21 — AHMED DECISION BLOCK (2026-09-21)

- **Status:** ADOPTED — authorization record for mission
  `WP1B_TOOLFIX_LIVESTATUS_2026-09-21` (T3). Copied verbatim from the mission
  contract §0, with every field resolved.
- **D1 — Calibration-3 classification:** **GATE_V1_PASS / INSTRUMENT_INVALID**.
  MAIN_297 blocked until a clean Calibration-3b.
- **D2 — Tool-budget semantics (amendment `WP1B_G11_TOOL_BUDGET_2026_09_21`):**
  **APPROVED**: `search_text` no longer consumes the distinct-file budget;
  `read_file` keeps `MAX_DISTINCT_FILES = 30`. No other agent knob changes.
- **D3 — Calibration gate v2 (CG-10, CG-11 + report-only metrics, §4 A5):**
  **APPROVED**.
- **D4 — Phase C — Calibration-3b (same 3 tasks, not scored, ceiling $0.25):**
  **YES**.
- **D5 — MAIN_297 + variance substudy:** **NO** (separate message after the
  Calibration-3b report). MAIN_297 is NOT authorized under any circumstance in
  this mission.
- **D6 — Single source of truth `docs/LIVE_STATUS.json` + rendered README /
  START_HERE / PROGRESS blocks:** **YES**.
- **Decided by:** Ahmed Ehab, 2026-09-21. Supervisor informed: **no**.
- **Additional authoritative clarifications (Ahmed, 2026-09-21):**
  - `docs/LIVE_STATUS.json` is the single current-state source of truth; its
    rendered LIVE block must be generated and byte-for-byte tested in FOUR
    current-facing files: `README.md`, `START_HERE_CURRENT_2026-09-21b.md`,
    `PROGRESS.md`, `00_CURRENT_RESEARCH_STATE.md`. `test_live_status_blocks.py`
    must validate all four rendered targets.
  - D2 tool-budget amendment: `search_text` backend scanning does NOT consume
    `MAX_DISTINCT_FILES`; `MAX_DISTINCT_FILES = 30` continues to bound
    successful explicit `read_file` exposure; no other scientific Agent knob
    may change.
  - Add behavior-preserving, report-only search telemetry before
    Calibration-3b (`search_files_scanned`, `search_results_returned`,
    `search_result_cap_hit`, `unique_paths_surfaced`, `tool_duration_seconds`).
    `MAX_SEARCH_RESULTS=50`, search ordering, and the 2,000-char observation
    window stay unchanged.
  - Tool errors use three conceptual classes without weakening CG-10:
    `INSTRUMENT_ERROR` (gating), `AGENT_MISUSE` (report-only), and
    `FROZEN_POLICY_LIMIT` (report-only). Fail-closed semantics preserved.
  - Calibration-3b is a paired instrument revalidation of D2, NOT a fresh
    independent performance sample. No labels loaded or scored; no prompt or
    Agent-behavior tuning; no F1/performance claim from Calibration-3 or
    Calibration-3b.
  - The old Calibration-3 call audit is re-derived mechanically from
    `research/wp1b/calibration-3-2026-09-21/wp1b_call_sidecar.jsonl`.
  - Calibration-3 is preserved historically and reclassified prospectively as
    `GATE_V1_PASS / INSTRUMENT_INVALID`.
  - Gate v2 must FAIL on the old Calibration-3 evidence before it is trusted on
    Calibration-3b (RED → GREEN evidence preserved).
  - Calibration-3b may run only when every Phase A/B acceptance criterion
    passes, all zero-API work is committed/integrated, the tool-fix tag is
    pushed and verified, the working tree is clean, the scientific
    model/provider/route and 1024-token cap match the frozen protocol, and
    spend before Phase C is exactly $0.00.
  - Calibration-3b STOP conditions: CG-10/CG-11 fail; any new instrument-class
    tool error; any task exceeds 1.2× budget-v2 worst-case; scientific
    configuration drifts; completing the task would require another
    behavior-changing fix. No repair-and-continue in the same paid run.
  - The 786 unread Saleor RESERVE outcomes remain sealed.
  - MAIN_297 and the 15×3 variance substudy remain forbidden even if
    Calibration-3b passes perfectly.
  - Current-facing documentation updated from repository evidence, not previous
    reports; namespace prefixes `WP1B-G*` and `E2E-G*`; no invented Phase 0–4
    numbering; no AI-assistant names in public/thesis-facing docs.
- **Scope change:** NO scientific scope change.

## Decision WP1B_CALIBRATION_3_RECLASSIFIED — GATE_V1_PASS / INSTRUMENT_INVALID (2026-09-21)

- **Status:** CORRECTION — prospective reclassification of the Calibration-3
  instrument finding (D1). The Calibration-3 STOP report and frozen artifacts
  are NOT edited; this entry supersedes their interpretation going forward.
- **Classification:** **`GATE_V1_PASS / INSTRUMENT_INVALID`**. The frozen gate
  (CG-1..CG-9) passed, but the agent's tools were defective: 0 of 3 tasks
  successfully read a file, and most searches returned the frozen
  `Max distinct files limit (30) reached` error.
- **Mechanical audit:** `scripts/wp1b_sidecar_tool_audit.py` re-derives the
  24-call Calibration-3 sidecar:
  `research/wp1b/calibration-3-2026-09-21/wp1b_tool_audit.json` — **3 forced
  final answers / 5 tool calls returning data (3 list_files + 2 search_text) /
  9 tool errors from the 30-file limit (7 search_text + 2 read_file) /
  7 rejected repeated requests / 0 successful `read_file`** (AC-T1).
- **v1.1 check re-derived (AC-T2):** `reports/scientific_microstudy_v11/run_records.jsonl`
  0 occurrences of `Max distinct files limit`; `selection_inspected_file_count`
  distribution {0:15, 2:3, 3:7, 4:5}, max 4, over 30 runs. On Todo the
  30-file budget never bound, so D2 restores on Saleor the behaviour the v1.1
  agent actually had.
- **Defect doc:** `docs/WP1B_AGENT_TOOL_BUDGET_DEFECT_2026-09-21.md`.
- **Fix (D2):** amendment `WP1B_G11_TOOL_BUDGET_2026_09_21` — `search_text`
  no longer consumes the distinct-file budget; `read_file` keeps
  `MAX_DISTINCT_FILES = 30`.
- **Gate v2 (D3):** `artifacts/wp1b_calibration_gate_v2.json` adds CG-10
  (0 instrument-class tool errors) and CG-11 (>= 1 successful `read_file` in
  >= 1 task). Gate v2 run on the old Calibration-3 records is expected
  **CG-10 FAIL** (RED), then PASS on Calibration-3b (GREEN).
- **Scope change:** NO scientific scope change.

## Decision WP1B_KNOWN_TEST_FAILURES_V2 — README NODE IDS REMOVED (2026-09-21)

- **Status:** ADOPTED. `artifacts/known_test_failures_2026-09-21_v2.json`
  supersedes the v1 acceptance set (v1 preserved as history).
- **Decision:** the two README REAL_DEFECT node IDs are FIXED by the B2
  current-state rewrite and REMOVED from the failing set:
  - `test_full_model_name_present_in_current_facing_docs` (README now carries
    the full model name `Qwen3-Coder-480B-A35B-Instruct`);
  - `test_svg_fallbacks_exist_and_are_embedded` (README now embeds
    `docs/assets/experiment_map.svg` and the other SVG fallbacks).
- **Remaining failing set (3 node IDs):** the D96 GitHub-token REAL_DEFECT and
  the two djangocms ENV_OR_DATA_MISSING nodes (unchanged from v1).
- **Scope change:** NO scientific scope change.

## Decision WP1B_CALIBRATION_3B — EXECUTED, GATE V2 PASS (2026-09-21)

- **Status:** EXECUTED. Calibration-3b run authorized (D4 = YES), protocol v2
  (cap 1024), frozen provider/route/pricing, cumulative USD guard ≤ $0.25.
- **Run:** the SAME 3 tasks as Calibration-3 (paired instrument revalidation of
  the D2 tool-budget fix, NOT a fresh performance sample) via
  `scripts/wp1b_calibration_run.py`; output under
  `research/wp1b/calibration-3b-2026-09-21/`.
- **Cost:** cumulative **$0.070028 ≤ $0.25** (per task $0.021543 / $0.031885 /
  $0.016599). Per-task cost / budget-v2 worst-case ratios
  **0.405 / 0.626 / 0.547** — all within 1.2× (BUDGET_MODEL_V2_OK).
- **Gate:** **CG-1..CG-11 all PASS**
  (`wp1b_calibration_gate_v2_result.json`). **CG-10 PASS (0 instrument-class
  errors) · CG-11 PASS (3 successful reads).**
- **Instrument VALID (raw per-call outcomes):** 21 calls; tool_ok 7; rejected
  repeats 11 (1/6/4); 0 instrument errors, 0 agent-misuse, 0
  frozen-policy-limit; 0 search-result-cap hits (max 11 results, 1,106 files
  scanned per task). 0 EMPTY. 0 cap hits.
- **Calibration-3b is NOT scored against labels** (paired instrument
  revalidation only; no F1/performance claim).
- **STOPPED after Phase C** (contract §6 step 7), regardless of the PASS.
  MAIN_297 + variance substudy NOT authorized (D5/D7 NO): requires a separate
  explicit Ahmed decision after he reviews the Calibration-3b evidence. The
  786 sealed Saleor RESERVE outcomes remain untouched.
- **Scope change:** NO scientific scope change.

## Decision WP1B_G12_TO_MAIN297 - §0 DECISION BLOCK (2026-09-22)

- **Status:** ADOPTED (this mission, verbatim per the contract §0).
- **Contract:** `_workspace/active/OPENCODE_CONTRACT_WP1B_G12_TO_MAIN297_2026-09-22.md`.
  The block below is copied verbatim into this append-only record; the
  `[CHOOSE]` placeholders are superseded by Ahmed's explicit decisions stated
  in the mission message (2026-09-22).
- **Decision block (verbatim):**

> | ID | Decision | Value |
> |----|----------|-------|
> | D1 | Amendment `WP1B_G12_AGENT_CONTEXT_HYGIENE_2026_09_22` (§2 A3, exactly 4 changes) | **APPROVED** |
> | D2 | Calibration-3c (same 3 tasks, protocol v3, gate v3, not scored, ceiling $0.25) | **YES** |
> | D3 | MAIN_297 + variance 15×3 + scoring | **MANUAL = stop after 3c** |
> | D4 | Ceilings (unchanged from preflight) | 3c **$0.25** · MAIN_297 **$21.50** · variance **$3.50** |
> | D5 | One-amendment rule | **APPROVED** (No scaffold or agent change after D1, whatever 3c or MAIN_297 shows) |
> | — | Decided by | Ahmed Ehab, 2026-09-22. Supervisor informed: **no** |

- **Authoritative clarifications (Ahmed, 2026-09-22):**
  1. **STOP after Calibration-3c.** MAIN_297, the variance substudy, label
     loading and scoring are NOT authorized. Even a fully clean Calibration-3c
     does not continue to Phase C.
  2. **G12 is prospective and label-blind**, NOT behavior-preserving. Its
     purpose is to remove deterministic context-loop artifacts before the
     baseline is evaluated.
  3. **G12 elements:** echo the actual previous tool action + arguments before
     its result; show the current call number and calls remaining; name the
     exact repeated request in the rejection warning; explicitly mark truncated
     tool output.
  4. **No new strategic guidance.** Early `action=final` IS already explicitly
     visible to the model (TOOL_SCHEMA item 4 lists `final` with its JSON, the
     `AGENT_ACTION_SCHEMA` enum includes `final`, and `INITIAL_SYSTEM_PROMPT`
     states call 8 is forced to final). Therefore the counter message uses ONLY
     `[control] Call {k} of 8. Calls left before the forced final: {8-k}.` and
     does NOT repeat or emphasize early-final availability.
  5. **Review Card semantics:** BLOCKING = any instrument-class error; >= 3
     consecutive identical rejected requests; zero successful reads across ALL
     THREE tasks; cost-ratio violation; other contract-defined hard failures.
     INFORMATIONAL = an individual task with zero `read_file` calls;
     search/list-only task behavior; ordinary frozen-policy-limit events.
     Do NOT force every individual task to read a file.
  6. **Anomaly wording:** "identical normalized tool output/error repeated >= 3
     times" replaces "same tool-output length repeated >= 3 times" (equal string
     length alone cannot create a false anomaly).
  7. **Calibration-3c clean criteria:** CG-1..CG-12 PASS; >= 2 of 3 tasks with
     >= 1 successful `read_file`; rejected-repeat share <= 25% of all calls; no
     run of >= 3 consecutive identical rejected requests; cost ratio <= 1.0 on
     every task; zero BLOCKING Review Card anomalies. INFORMATIONAL flags do not
     independently fail the calibration.
  8. **Gate v3 is run against Calibration-3b BEFORE 3c** and must catch the
     repeat loop prospectively (RED evidence preserved).
  9. **Same 3 calibration tasks**; unscored paired harness regression check; do
     not load labels and do not calculate F1.
  10. **No knob change** (model/provider/route, temperature, MAX_AGENT_CALLS=8,
      completion cap=1024, tools or arguments, read budget=30,
      MAX_SEARCH_RESULTS=50, search ordering, 2000-char observation window,
      MAX_READ_CHARS, editable paths, schemas, SIP/RM-CSS predictions, NI rules,
      sample manifests, budget-v2 ceilings, or any other scientific knob).
  11. **If Calibration-3c reveals any new issue: STOP.** No second scaffold fix
      in this mission. D5 is binding.
  12. The final STOP report includes call-by-call review evidence (calls/task,
      useful calls, successful reads/task, rejected repeats/task, longest
      consecutive rejected-request run, rejected-call share, prompt growth,
      truncation events, instrument errors, review-card blocking + informational
      flags, token counts, USD spend, budget ratios).
  13. Standing Execution & Validation Protocol v2 applies (Impact Declaration
      first, targeted tests before full suite, append-only DECISIONS.md,
      smallest defensible diff, push/tag stable T3 work, update LIVE_STATUS,
      FULL + TRUE LIGHT exports).
- **Authorization boundary:** Phase A zero-API G12 work AUTHORIZED.
  Calibration-3c AUTHORIZED up to $0.25. MAIN_297 and all scoring FORBIDDEN.
  STOP after Calibration-3c regardless of outcome.
- **Scope change:** NO scientific scope change.

## Decision WP1B_CALIBRATION_3C - EXECUTED, GATE V3 PASS, CLEAN (2026-09-22)

- **Status:** EXECUTED. Calibration-3c run authorized (D2 = YES, ceiling $0.25),
  protocol v3 (G12 applied), gate v3 (CG-1..CG-12), frozen provider/route/
  pricing, cumulative USD guard <= $0.25. **NOT scored**; no labels loaded; no
  F1 (paired unscored harness regression).
- **Run:** the SAME 3 tasks as Calibration-3/3b via
  `scripts/wp1b_calibration_run.py`; output under
  `research/wp1b/calibration-3c-2026-09-22/`; branch
  `wp1b/calibration-3c-2026-09-22`.
- **Cost:** cumulative **$0.063205 <= $0.25** (per task $0.017620 / $0.032844 /
  $0.012740). Per-task cost / budget-v2 worst-case ratios
  **0.331 / 0.645 / 0.420** - all <= 1.0.
- **Gate:** **CG-1..CG-12 all PASS** (`wp1b_calibration_gate_v3_result.json`).
  CG-12 PASS: longest rejection run = 1, rejected share 5.6% (was runs 6/4,
  share 52.4% in 3b).
- **Clean criteria (clarification 7):** all six PASS. Instrument VALID (raw
  per-call outcomes): 18 calls; tool_ok 14; rejected repeats 1 (5.6%); 4
  successful reads (tasks 1 and 3 have 2 each; task 2 is search-only, 0 reads);
  0 instrument errors, 0 agent-misuse, 2 frozen-policy events (search-result
  cap hits) - informational only; 0 cap hits; 0 EMPTY; 0 malformed.
- **Review Card:** `REVIEW_CARD.md` - **0 BLOCKING**, 4 INFORMATIONAL
  (I1/I2 task b05633dae118 search/list-only, I3 x2 search-result-cap hits).
  INFORMATIONAL flags do not fail the calibration.
- **STOPPED per D3 = MANUAL** (contract section 3), regardless of the clean
  result. MAIN_297 + variance substudy + label loading + scoring NOT
  authorized; no second scaffold fix (D5 binding). Report:
  `docs/WP1B_CALIBRATION_3C_STOP_REPORT_2026-09-22.md`.
- **Scope change:** NO scientific scope change.

## Decision WP1B_MAIN297 - §0 DECISION BLOCK (2026-09-22)

- **Status:** ADOPTED (this mission, verbatim per the overnight contract §0).
- **Contract:** `_workspace/active/OPENCODE_OVERNIGHT_WP1B_MAIN297_FULL_2026-09-22.md`.
- **Decision block (verbatim):**

> | ID | Decision | Value |
> |----|----------|-------|
> | D1 | Harness + analysis bundle `WP1B_MAIN297_HARNESS_2026_09_22` (new files + documentation; no frozen scientific file modified) | **APPROVED** |
> | D2 | Preregistration addendum v2 (X6–X11) + agent budget-sensitivity DESIGN (execution NOT authorized) — committed and tagged BEFORE the first paid call | **APPROVED** |
> | D3 | MAIN_297 + variance 15×3 + scoring + exploratory X1–X11 | **YES** |
> | D4 | Ceilings (unchanged) | MAIN_297 **$21.50** · variance **$3.50** |
> | D5 | One-amendment rule | **CLOSED** — no agent / scaffold / prompt / tool / knob change, whatever MAIN_297 shows |
> | D6 | Agent budget-sensitivity arm (AG16 on MAIN_50) | **NOT IN THIS MISSION** (design frozen only; separate decision) |
> | D7 | Documentation housekeeping (README lessons 1a–1d + FAQ §12, AGENTS.md archive, MISSION_TEMPLATE §4/§4b, Calibration-3c record correction, LIVE_STATUS `authorization` key) | **APPROVED** |
> | — | Decided by | Ahmed Ehab, 2026-09-22. Supervisor informed: **no** |

- **Scope change:** NO scientific scope change (harness/analysis/docs only).

## Decision WP1B_MAIN297_HARNESS - ADOPTED (2026-09-22)

- **Status:** ADOPTED. Harness + analysis bundle `WP1B_MAIN297_HARNESS_2026_09_22`
  (D1 APPROVED). Pointer: `docs/WP1B_MAIN297_EXECUTION_ADDENDUM_2026-09-22.md`.
- **Five harness gaps of the calibration runner and their fixes (addendum §1):**
  - G-A: predictions not persisted (only run records) → per-item prediction
    persistence + freeze script.
  - G-B: calibration runner writes only at the end and `rmtree`s the out dir on
    re-entry → per-item fsync commit + `--resume` + never-delete rule.
  - G-C: 1 immediate transport retry vs the frozen 3-retry rule → frozen
    3-retry rule (10/60/180 s) in `resilient_backend`.
  - G-D: unhandled transport error could surface as an unexpected crash → item
    restart ×2 + session halt (exit 4) without recording the item.
  - G-E: calibration card blocks on agent behaviour → MAIN-mode card blocks on
    instrument-level anomalies only (M1–M5); per-task agent behaviour is data.
- **NO scientific knob changed** (model/route/temp/cap/calls/prompts/tools/
  schemas/budgets/manifests unchanged).
- **Scope change:** NO scientific scope change.

## Decision WP1B_CALIBRATION_3C_RECORD_CORRECTION - ADOPTED (2026-09-22)

- **Status:** ADOPTED. Pointer:
  `docs/WP1B_CALIBRATION_3C_RECORD_CORRECTION_2026-09-22.md`.
- **Correction:** "7 distinct searches" → 6 distinct + 1 non-adjacent repeat; task
  2 reached the forced final at call 8. Verdict **CLEAN unchanged**.
- **Scope change:** NO scientific scope change (record precision only).

## Decision WP1B_EXPLORATORY_PREREG_V2_AND_AG16_DESIGN - FROZEN (2026-09-22)

- **Status:** FROZEN before any MAIN_297 output (D2 APPROVED).
- **Pointers:** `research/wp1b/wp1b_exploratory_prereg_addendum_v2.json`
  (X6–X11) and `research/wp1b/wp1b_agent_budget_sensitivity_prereg.json`
  (design only).
- **AG16 execution is NOT authorized** (needs D6); only the design is frozen.
- **Scope change:** NO scientific scope change.
