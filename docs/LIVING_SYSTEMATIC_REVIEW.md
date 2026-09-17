# Living Systematic Review — Repository Change Localization / Impact Selection

**Status:** SEEDED 2026-09-16 (V1). Living document: updated on every new
literature screening. Machine-readable artifacts:
`research/literature/review_matrix.csv`, `research/literature/search_log.csv`,
`research/literature/idea_ledger.md`.

**Status update 2026-09-16 (V1.1 verification pass):** primary-source
verification of the priority rows is COMPLETE for Agentless, CodePlan,
RepoCoder, AutoCodeRover, RepoGraph, GraphLocator, RPG/ZeroRepo and the
Shichao Zhang adaptive-computation line (see §4 and the matrix `status`
column). Corrections: RepoGraph ICLR 2025; RepoCoder EMNLP 2023; AutoCodeRover
ISSTA 2024; GraphLocator FSE 2026 (LLM causal-issue-graph localization);
RPG/ZeroRepo = repository generation; RIPPLE = classical ripple-effect line
(no canonical system).**

**Purpose.** Track the competitor space for the thesis line **Repository Change
Localization Under Limited Inference Budgets**: which systems solve (parts of)
the same problem, with what evidence, at what cost, and which ideas we should
test in the **Omission-Risk Feature Study v1 (TRAIN/VALIDATION only)**.

---

## 1. Scope

- **In scope:** file-level localization / impact selection over repositories;
  budget-aware and cost-aware retrieval/verification; graph-assisted
  localization; repository-level understanding for coding agents; cheap
  non-LLM baselines.
- **Out of scope (monitored, not screened in depth):** general code
  generation, fine-tuning, end-to-end patch repair, non-localization agent
  benchmarks — unless they change the localization claim.

## 2. Classification legend

- **PEER-REVIEWED** — accepted at a peer-reviewed venue (venue cited).
- **PREPRINT** — arXiv/technical report; not yet peer-reviewed.
- **CROSS-DOMAIN-INSPIRATION** — not repository localization per se, but a
  transferable mechanism (adaptive retrieval, change-impact analysis, RAG
  routing).

## 3. Initial matrix (12 entries)

| System | Category | Mechanism (one line) | Cost posture | Relation to us |
|---|---|---|---|---|
| RIPPLE | PEER-REVIEWED (verify) | change-propagation impact analysis | static/dynamic, cheap | our B3 graph expansion |
| Repository Memory | PEER-REVIEWED (verify) | memory-conditioned iterative generation | high (LLM calls) | planner/agent line |
| Adaptive-k | CROSS-DOMAIN | query-dependent retrieval depth | varies | K = operating-point curve |
| LocAgent | PEER-REVIEWED (shared-protocol, direct evidence) | graph-guided agent, search+fix | high ($9.93 est / 402 calls) | primary external comparator |
| GraphLocator | CROSS-DOMAIN (verify) | graph-based suspiciousness propagation | cheap (static) | B3 Graph@K |
| RepoGraph | PEER-REVIEWED (verify) | repository graph construction for LLM retrieval | graph build + LLM | dependency-graph construction |
| Agentless | PREPRINT | localize-then-repair, no agent loop | low-moderate (~1/3 agents) | sparse-first-pass philosophy |
| CodePlan | PEER-REVIEWED (verify) | repository-level edit planning | planner + per-file regen | Full/Sparse impact planning |
| RepoCoder | PREPRINT | clones-like retrieval memory, iterative | high | memory-conditioned iteration |
| AutoCodeRover | PREPRINT | AST-level search + repair loop | substantial | repair-focused (boundary) |
| RPG / ZeroRepo | PREPRINT | repo-map manifest + zero-shot retrieval | low-moderate | candidate-universe-as-manifest |
| AB-RAG | CROSS-DOMAIN (verify) | adaptive/agentic retrieval routing | retrieval + LLM | selective-escalation gate |

Full rows (mechanism, evidence, datasets, metrics, cost, relation, novelty
threat, idea, status): `research/literature/review_matrix.csv`.

## 4. Verification status

Only **LocAgent** is VERIFIED with direct evidence in this project (P5-B/P5-C
shared protocol; upstream pinned at `4935b557…`). All other rows are **SEEDED —
verify primary source**; no thesis claim may rely on an unverified row. The
matrix `status` column carries this explicitly.

**Verification pass 2026-09-16 (V1.1).** Primary sources were checked
(arXiv API, Crossref, ACM, web search) for the priority rows. VERIFIED rows now
include: Agentless, CodePlan, RepoCoder, AutoCodeRover, RepoGraph,
GraphLocator, RPG/ZeroRepo, and the Shichao Zhang KNN/adaptive-computation
line (Challenges in KNN TKDE 2022; One-step TKDE 2021; Reachable Distance TKDE
2022; Cost-sensitive KNN Neurocomputing 2020; Adaptive kNN graph 2026). RIPPLE
is SEEDED at the classical ripple-effect/change-propagation concept level (no
canonical single system). Repository Memory is mapped to the verified RepoCoder
line (+ RepoAgent SEEDED). Adaptive-k remains a cross-domain pattern (no single
primary source pinned); the adaptive-neighborhood idea is corroborated by the
verified Shichao Zhang adaptive kNN graph work.

## 5. Most important competitor ideas (V1 read)

1. **Localization-first without an agent loop (Agentless, CodePlan).** Strong
   evidence that a decoupled localize-then-edit pipeline is competitive at a
   fraction of agent cost — the same philosophy as our sparse first pass +
   selective verification.
2. **Manifest/repo-map retrieval (ZeroRepO).** A repository map as the
   retrieval index mirrors our candidate-universe design and suggests manifest
   statistics as useful risk features.
3. **Adaptive routing (adaptive-k, AB-RAG).** Query-dependent decisions about
   how much to retrieve/escalate is the direct template for the omission-risk
   gate.
4. **Graph-guided agents (LocAgent, GraphLocator).** The expensive, graph-aware
   alternative — the natural 'verifier' arm, bounded by cost and a 50% empty
   rate in our shared protocol.

## 6. Novelty threats (V1 read)

- **MEDIUM/HIGH:** 'localize first, no agent loop' (Agentless) is the closest
  conceptual competitor to our pipeline; our differentiators are (a) the cheap
  non-LLM first pass, (b) the sparse representation, and (c) an explicit
  cost-aware escalation gate.
- **MEDIUM:** graph-based localization (GraphLocator/RepoGraph) — our B3/Hybrid
  result already bounds graph-expansion value on the seed signal.
- **LOW–MEDIUM:** adaptive-K and adaptive RAG routing are known patterns; our
  contribution is applying them to repository change localization with an
  explicit budget discipline.

## 7. Ideas we should test (Omission-Risk Feature Study v1, TRAIN/VALIDATION only)

See `research/literature/idea_ledger.md` (I1–I7). Headline:
- risk features from manifest density, graph frontier, first-pass agreement
  (I1/I2/I5);
- a risk-coverage operating-point evaluation (AUROC/AUPRC, escalation rate, FN
  recovery, cost per recovered FN) (I6);
- zero-LLM graph/change-propagation alternatives measured against BM25@K (I3).

**Do NOT start:** omission-risk RiskScorer training, Saleor scientific execution,
LocAgent scientific calls, selective escalation, or further omission-risk model
runs — until the harness + review foundation milestone is audited and reviewed.

**Registered Sparse-v2-label study: EXECUTED 2026-09-16 (approved
development-inference, 90 cells, TRAIN/VALIDATION only).** Outcome: 90/90
valid; Sparse-v2 `has_fn` prevalence 86.7% (26/30; 4 negatives); class-balance
gate FAILED → descriptive/single-feature only, no multivariable RiskScorer; no
signal survives the random band; report
`reports/OMISSION_RISK_SPARSE_V2_INFERENCE_REPORT.md`.

## 8. How to update

1. Append the search to `research/literature/search_log.csv`.
2. Add/update the row in `research/literature/review_matrix.csv` (keep the
   `status` column truthful).
3. Update `research/literature/idea_ledger.md` disposition.
4. Update this doc's summary tables.
5. Record any decision in `DECISIONS.md` (append-only).

## 9. Shichao Zhang / adaptive-computation track (VERIFIED 2026-09-16)

Primary-source-verified line (see `research/literature/idea_ledger.md` for the
full citations):

- **Challenges in KNN Classification** — S. Zhang, IEEE TKDE 2022
  (DOI 10.1109/TKDE.2021.3049250). Survey of KNN challenges incl. K selection,
  distance metrics, lazy-learning efficiency (complete nearest-neighbor
  search).
- **KNN Classification with One-step Computation** — S. Zhang & J. Li, IEEE
  TKDE 2021 (arXiv 2012.06047). Replaces the lazy K-neighbor search with a
  one-step matrix computation + group lasso (K setting and neighbor search are
  jointly integrated).
- **Reachable Distance Function for KNN Classification** — S. Zhang, J. Li,
  Y. Li, IEEE TKDE 2022 (arXiv 2103.09704). Class-aware 'Z' distance.
- **Cost-sensitive KNN classification** — S. Zhang, Neurocomputing 2020
  (DOI 10.1016/j.neucom.2018.11.101). Cost-sensitive decision making.
- **Adaptive kNN graph model** — J. Li, H. Xu, S. Zhang, arXiv 2601.16509
  (2026). HNSW graph + pre-computed voting; neighbor selection/weighting moved
  to the training phase (offline work).

**Reusable principles extracted for our thesis:**
1. query-specific neighborhood/budget (K is query-dependent, not global);
2. confidence of approximate answers must be quantified;
3. move reusable work offline (pre-indexing / precomputation analogue);
4. cost-sensitive decision making (escalation rule weight C_FN vs C_VERIFY);
5. joint candidate-count/candidate-selection = **TEST-LATER** (group lasso /
   one-step sparse reconstruction NOT implemented in this block; revisit only
   if the simple risk signals fail).

**Experimental implication:** the adaptive-K rules in the omission-risk study
operationalize principle 1; the cost-sensitive analysis operationalizes
principle 4; the pre-indexed candidate universe operationalizes principle 3.

## 10. Novelty audit (2026-09-16, Milestone H)

**Do NOT claim as novel by themselves:**
- graph localization (LocAgent/GraphLocator/RepoGraph line);
- repository memory (RepoCoder/RepoAgent line);
- intent-aware impact expansion (classical CIA/ripple-effect line);
- adaptive K (Shichao Zhang line, verified);
- generic uncertainty-triggered escalation.

**Strongest defensible FUTURE novelty candidate:**
> omission-aware, cost-sensitive bounded verification of an explicit sparse
> file-level impact policy under matched inference budgets —

with a candidate-level fallback if task-level routing remains unsupported
(Route B). Marked **`CANDIDATE NOVELTY — NOT YET CLAIMED`** until literature
and experiment support it.

**Classical / modern CIA and omission-recovery additions to the matrix** (see
`research/literature/review_matrix.csv`; status SEEDED):
- Classical change-impact analysis / ripple effect (RIPPLE line): relevant for
  the Route B candidate-level verifier and the classical CIA baseline.
- Candidate-level omission recovery / false-negative recovery literature:
  relevance — identifying which non-selected candidates deserve a second look
  is the pre-registered Route B question; no single canonical system pinned.

**Where the evidence leaves the thesis (after M1A-M3 + P1/P5 + cheap baselines +
Sparse omission-risk v1 + V2):** the defensible proven contributions are
(1) sparse explicit impact-plan representation with controlled evidence,
(2) a reproducible real-commit impact-localization dataset/protocol,
(3) fair cheap/classical/LLM/agent comparison under common file-level metrics,
(4) an honest negative for task-level cheap risk modeling on current evidence,
and (5) the pre-registered Route A/B bounded-verification mechanism. No
positive algorithmic result is promised.
## 11. BibTeX triage + verified literature additions (2026-09-16 evening)

Ingested 13 uploaded BibTeX exports as CANDIDATE DISCOVERY sources
(987 raw / 806 unique titles). Full classification:
eports/BIBTEX_LITERATURE_TRIAGE_2026-09-16.md +
esearch/literature/bibtex_triage_classified_2026-09-16.csv.

High-signal USE_NOW verified from primary sources (arXiv API / Crossref):

- LLM-Driven Cost-Effective Requirements CIA (arXiv 2511.00262, Etezadi et al. 2025) - requirements unit.
- Change-Patterns Mapping (TSE 2022, 10.1109/TSE.2021.3059481) - history-pattern boosting of CIA (Route B history overlap).
- Learning dependency-based change impact predictors (IST 2015, 10.1016/j.infsof.2015.07.007) - history/co-change + cross-repo.
- A Software Impact Analysis Tool based on Change History Learning (ICSE-SEIP 2022, 10.1145/3510457.3519017).
- Transformers + Program Dependence Graphs for Impact Analysis (arXiv 2607.23355, Yan et al. 2026).
- Repoformer (ICML 2024, arXiv 2403.10059) - selective retrieval prior.
- FastCoder (ASE 2025, arXiv 2502.17139) - efficient retrieval + verification.
- Issue Localization via LLM-Driven Iterative Code Graph (ASE 2025, arXiv 2503.22424).
- Recommendation-System CIA industrial case (TSE 2017, 10.1109/TSE.2016.2620458).

Noise (robotics/SLAM, NLP parsing, medical/selective-prediction, generic graph
acceleration, vulnerability) is REJECT_IRRELEVANT and not cited.

Comparison matrix columns added to the proposal: explicit file policy, sparse
omission representation, cheap first pass, omission recovery, hard/matched
budget, real-commit evaluation, cross-repository evidence. Novelty wording
revised: 'Existing work covers several individual components; this thesis
evaluates their combination...' - no absolute 'none combines' claim.

## 12. Route B development result + novelty update (2026-09-16 evening)

**Route B candidate-level omission recovery V1 (zero-LLM):** R4 Classical CIA
(BM25-seed 1-hop closure + graph neighbor) beats Random at B=5 on DEV_TRAIN
(0.148 vs 0.022, CI [+0.069,+0.179]) and DEV_VALIDATION (0.180 vs 0.037,
CI [-0.003,+0.285]); pooled 0.163 vs 0.029 (CI [+0.085,+0.184]). No
universe-size artifact (corr 0.105). This is the FIRST positive development
signal for candidate-level omission recovery, in contrast to the negative
task-level risk-scorer result. Oracle upper bound 0.858 at B=5 shows headroom.
See reports/ROUTE_B_OMISSION_RECOVERY_V1_REPORT.md.

**Novelty matrix implication (from the BibTeX triage):** existing work covers
individual components (explicit file policy, sparse representation, cheap first
pass, omission recovery, matched budget, real-commit evaluation, cross-repo).
This thesis evaluates their COMBINATION; candidate novelty remains
CANDIDATE NOVELTY - NOT YET CLAIMED. The strongest defensible future
contribution is 'omission-aware, cost-sensitive bounded verification of an
explicit sparse file-level impact policy under matched inference budgets',
now with a positive candidate-level zero-LLM development signal (Route B).

**PROVEN (unchanged):** Preserve-by-Omission representation + controlled evidence.
**DEVELOPMENT RESULT:** task-level cheap omission-risk routing did NOT replicate
at V2 scale; candidate-level CIA omission recovery IS directionally positive on
development data.
**CANDIDATE FUTURE CONTRIBUTION:** bounded candidate-level omission recovery
under matched budgets (Route B).

## 13. Overnight update (2026-09-17)

- **Route B V2 robustness closure:** the candidate-level Classical-CIA ranker
  recovers Sparse-omitted missed files above the analytic (hypergeometric)
  Random control across the whole budget curve B in {0,1,3,5,10} with
  task-level bootstrap intervals excluding zero at every point; 5/5 development
  folds positive; no omitted/universe-size artifact. Progression gate PASS.
  This is the first statistically stable candidate-level signal, in contrast to
  the negative task-level RiskScorer result.
- **Verifier pilot:** 30 dev tasks, 30 calls, .0023. Oracle-in-top-B = 1.000
  (the frozen CIA ranker places recoverable missed files in top-B); verifier
  ORR 0.86-1.00. Dominant loss = first-pass omission.
- **History/co-change arm:** beats analytic Random where parent-visible history
  is available (94 tasks); CIA remains the frozen primary.
- **Adaptive budget horizon:** exploratory per-task Oracle curves show 83% of
  tasks reach >=90% of Oracle@10 with B<5; marginal gain sharply diminishing
  after B=3. WORTH-PURSUING AFTER FIXED ROUTE-B (not a contribution).
- **Novelty position unchanged:** CANDIDATE NOVELTY - NOT YET CLAIMED;
  combination of sparse policy + bounded omission recovery under matched
  budgets.

## 14. Continuation update (2026-09-17)

- **Saleor portability fix:** whole-tree git archive → production-only parent
  materializer (git ls-tree + git cat-file --batch); 98/98 equivalence PASS;
  150/150 DEVELOPMENT bundles; canonical hashes identical to pre-portability.
  INTERNAL_TEST/RESERVE sealed. ZERO model calls.
- **Saleor sparse inference budget-blocked:** measured ~14.5k tokens/.0047 per
  cell → 450-cell run ~2.4-2.7x the authorized ceiling; FAIL-CLOSED; Saleor
  Route-B replication therefore blocked. This is a ceiling issue, NOT a method
  failure; the Saleor protocol §5.1 pre-warned about larger universes.
- **djangoCMS Route-B confirmatory-freeze packet:** ready-to-approve; choice B
  (ranking + actual verifier); INTERNAL_TEST sealed.
- **P2 adaptive budget:** formalized + pre-registered 3 policies; CONDITIONAL.
- **Semantic audit:** machine-prep complete (integrity PASS, kappa tests,
  synthetic dry-run NOT REAL); human judgments pending.
- **Novelty position unchanged:** candidate-level bounded omission recovery
  under matched budgets (Route B V2) is the strongest dev signal; Saleor
  replication and confirmatory test are the next gates.
