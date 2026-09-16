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