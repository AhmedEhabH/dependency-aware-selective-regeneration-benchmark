# P2 Algorithm Landscape — Adaptive-Budget Omission Recovery (2026-09)

**Date:** 2026-09-17
**Tier:** T0/T3-documentation — systematic literature landscape for the P2
five-month program (ZERO API)
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731
**Status:** LANDSCAPE COMPLETE (development-stage); algorithm IMPLEMENTATION is
the Nov 2026 – Mar 2027 program (not executed here).
**Basis:** the frozen Route-B confirmatory result (djangoCMS INTERNAL_TEST,
**CONFIRMS**), the P2 preregistration note
(`docs/ADAPTIVE_BUDGET_P2_PRE_REGISTRATION_NOTE.md`), the living systematic
review (`docs/LIVING_SYSTEMATIC_REVIEW.md`), and the literature decision ledger
(`reports/LITERATURE_DECISION_LEDGER.md`).

---

## 1. Scope and goal

Primary P2 question (frozen):

> Can an adaptive policy achieve comparable or better omission recovery than the
> best fixed-B operating point with lower expected verification cost?

This landscape systematically maps the algorithmic design space that could
answer that question, on DEVELOPMENT data only (djangoCMS DEV + Saleor DEV).
The now-opened djangoCMS INTERNAL_TEST is **excluded** from P2 algorithm
selection/tuning; Saleor INTERNAL_TEST stays sealed as a possible future P2
confirmation set.

Two tracks, per the mission:

- **Track A — direct SE-novelty threats** (close competitors to the fixed
  Route-B / bounded-verification story).
- **Track B — algorithmic inspiration** (Shichao-Zhang line + adjacent
  adaptive/selective/stopping/budgeted families).

Every candidate is classified exactly as:
`DIRECT_COMPETITOR / CLOSE_ANALOGUE / ALGORITHMIC_INSPIRATION /
BACKGROUND_ONLY / REJECT_IRRELEVANT`.

Publication metadata is verified from primary sources (arXiv API / Crossref)
in the living review + decision ledger; anything not yet primary-source-verified
is marked SEEDED (never claimed as verified).

## 2. Track A — direct SE novelty threats (status: existing knowledge)

| Method | Class | Relation to fixed Route B | P2 relevance |
|---|---|---|---|
| RIPPLE / change-propagation impact analysis | DIRECT_COMPETITOR (classical) | budget-unaware static propagation | low (fixed-B anchor, not adaptive) |
| Change-Patterns Mapping (TSE 2022) | CLOSE_ANALOGUE | historical-pattern re-ranking of impact set | medium (history feature source) |
| ArtifactSync | CLOSE_ANALOGUE (demo-level) | uncertainty-driven deeper context | low |
| GraphLocator (FSE 2026) | DIRECT_COMPETITOR | causal issue graph + LLM localization | medium (expensive competitor) |
| LocAgent (2025) | DIRECT_COMPETITOR | graph-guided LLM agent (P5 shared protocol) | medium (expensive competitor) |
| RepoCoder / RepoAgent / repository memory | CLOSE_ANALOGUE | memory-conditioned retrieval-generation | low |
| History/co-change CIA | CLOSE_ANALOGUE | history features (djangoCMS 94-task arm) | medium (feature source) |
| Selective repository retrieval/verification (Repoformer, FastCoder) | DIRECT_COMPETITOR | selective compute at repo level | HIGH — closest framing |
| Agentless (2024) | DIRECT_COMPETITOR | localization-first, no agent loop | medium (cost philosophy) |

Track A confirms the fixed Route-B story is NOT novel in isolation, but its
**budgeted, omission-aware, verified** framing is the candidate novelty — still
not claimed. Track A methods are anchors/references, not P2 algorithm
candidates.

## 3. Track B — algorithmic inspiration (the P2 design space)

### 3.1 Shichao-Zhang line (verified primary sources; inspiration origin)

| Method | Paper (verified) | Core idea | Adaptation variable | Budget | Stopping |
|---|---|---|---|---|---|
| Learning-k for kNN | Zhang, "Challenges in KNN Classification", TKDE 2022 | data-adaptive neighborhood size | k (neighborhood) | fixed per query | deterministic |
| One-step KNN computation | Zhang & Li, TKDE 2021 (arXiv 2012.06047) | joint k + distance computation | k / distance | fixed | deterministic |
| Cost-sensitive KNN | Zhang, Neurocomputing 2020 | cost-weighted classification | k / loss weights | fixed | deterministic |
| Reachable-distance KNN | Zhang, Li & Li, TKDE 2022 (arXiv 2103.09704) | adaptive-neighborhood geometry | k / reachability | fixed | deterministic |
| Demand-driven kNN | Zhang line (verified) | budget demanded by query difficulty | k | **adaptive** | deterministic |

Mapping to P2: `B_t` = the verification budget (number of candidates to
verify) for task *t*; "k" in the Zhang line maps to "B" here. The Zhang line is
primarily ALGORITHMIC_INSPIRATION (k-selection analogues), with demand-driven
kNN being the closest conceptual ancestor of an adaptive `B_t`.

### 3.2 Adjacent families (systematic, from verified primary sources / seeded)

| Family | Representative ideas | Class | Adaptation variable | Required supervision | Leakage risk |
|---|---|---|---|---|---|
| Adaptive/conditional computation | early-exit networks, conditional depth/width | ALGORITHMIC_INSPIRATION | compute budget per input | trained (label supervision) | low |
| Selective prediction / abstention | Chow's rule; selective classifiers | ALGORITHMIC_INSPIRATION | reject/accept decision | confidence calibrator | low |
| Learning-to-defer | defer to a more costly oracle | ALGORITHMIC_INSPIRATION | defer decision | cost labels | low |
| Cascaded inference | coarse→fine model cascade | ALGORITHMIC_INSPIRATION | escalation trigger | confidence thresholds | low |
| Optimal stopping / sequential decision | secretary problem; sequential testing | ALGORITHMIC_INSPIRATION | when to stop | cost/reward model | low |
| Budgeted retrieval / cost-sensitive ranking | budgeted ranker with fixed query budget | CLOSE_ANALOGUE | retrieved budget per query | cost labels | low |
| Active search / value-of-information | VOI-guided candidate acquisition | CLOSE_ANALOGUE | which candidate to inspect next | reward proxy | medium (if gold used) |
| Contextual bandit resource allocation | budget allocation as bandit | REJECT_IRRELEVANT (unless mechanistic) | allocation policy | reward labels | HIGH (reward = gold) |
| Learned stopping (neural) | trained stop policy | REJECT_IRRELEVANT for now | stop probability | trained | HIGH (overfit) |

### 3.3 Pre-registered P2 candidates (from the P2 note; the fixed anchor set)

- P2-P1 Score-gap stopping (deterministic; τ_gap on adjacent composite-score gap)
- P2-P2 Marginal-score threshold (deterministic; τ_marg on B-th candidate score)
- P2-P3 Cost-ratio stopping (deterministic; τ_cost on accumulated cost / task size)

These three are the pre-registered baseline policy family. The Zhang-inspired
and adjacent-family candidates (Sections 3.1–3.2) expand this set during the
program, subject to the common evaluation contract (Block E).

## 4. Per-method decision template (used in the CSV)

For each serious method: exact citation; task/input/output; adaptation
variable; objective/cost function; fixed vs adaptive budget; learned vs
deterministic stopping; required supervision; computational complexity;
leakage risks; mapping to omitted-file verification; implementation effort;
expected scientific value; reason to implement/reject/defer.

The full machine-readable landscape is in
`research/literature/p2_algorithm_landscape.csv`.

## 5. Selection pre-registration (no overfitting)

- No method is selected as "winner" using the opened djangoCMS INTERNAL_TEST.
- Method selection happens on DEVELOPMENT only, via the common evaluation
  contract (Block E), against the fixed anchors (B={1,3,5,10}, Analytic
  Random, BM25-only, frozen composite, Oracle, InspectAll).
- At most 1–2 scientifically justified P2 candidates are selected (Mar 2027),
  pre-registered, and only then (if justified) evaluated on the still-sealed
  Saleor INTERNAL_TEST.
- If no candidate dominates on recovery-vs-cost, P2 closes NEGATIVE and the
  fixed-B thesis stands (already CONFIRMED).

## 6. Status

**LANDSCAPE COMPLETE** — the design space is mapped and classified. Algorithm
implementation begins per the roadmap (Block D) within the common evaluation
contract (Block E). ZERO API in this document.

## 7. Landscape EXPANSION (2026-09-18) — beyond Shichao Zhang, decision-oriented

Expanded the Track-B landscape beyond the Shichao-Zhang line with **15 serious
additions/verification updates** (10–20 target met), classified decision-
oriented, primary-source VERIFIED where accessible (arXiv API) or marked
CLASSICAL/SEEDED otherwise. No citations are fabricated; anything not verified
from a primary source is marked explicitly.

| New id | Method | Class | Verified source | Adaptation variable | Cost objective | Relation to B_t | Decision |
|---|---|---:|---|---|---|---|---|
| P2-025 | Adaptive Computation Time (Graves 2016) | ALGORITHMIC_INSPIRATION | VERIFIED arXiv:1603.08983 | compute steps per input | compute vs accuracy | learned per-input compute budget ~ B_t analogue | BACKGROUND (learned) |
| P2-026 | SelectiveNet (Geifman & El-Yaniv 2019) | ALGORITHMIC_INSPIRATION | VERIFIED arXiv:1901.09192 | reject/accept (coverage) | risk vs coverage | abstention = skip verification | CANDIDATE (deterministic variant) |
| P2-027 | DeeBERT early exit (Xin et al. 2020) | ALGORITHMIC_INSPIRATION | VERIFIED arXiv:2004.12993 | exit layer per input | inference cost vs accuracy | early exit = stop verification | CANDIDATE (deterministic variant) |
| P2-028 | Bayesian Optimal Active Search (Garnett et al. 2012) | CLOSE_ANALOGUE | VERIFIED arXiv:1206.6406 | next candidate to query | value-of-information vs query cost | VOI ordering analogue | REJECT_DEFER (leak risk) |
| P2-029 | Learning to Defer w/ limited experts (Hemmer et al. 2023) | ALGORITHMIC_INSPIRATION | VERIFIED arXiv:2304.07306 | defer decision | defer cost vs error | defer to verifier when cheap evidence insufficient | CANDIDATE (learned deferred) |
| P2-030 | MoE conditional computation (Shazeer et al. 2017) | ALGORITHMIC_INSPIRATION | VERIFIED arXiv:1701.06538 | per-example expert subset | capacity vs compute | sparse/conditional computation framing | BACKGROUND |
| P2-031 | Confidence-Budget Matching (Efroni et al. 2021) | CLOSE_ANALOGUE | VERIFIED arXiv:2102.03400 | when to query under budget | regret vs budget | query when confidence wide vs budget ~ P2-P3 cost-ratio | CANDIDATE |
| P2-032 | Online Budgeted Learning (Fainman et al. 2019) | CLOSE_ANALOGUE | VERIFIED arXiv:1903.05382 | which features to acquire | acquisition cost vs quality | budgeted candidate inspection analogue | CANDIDATE |
| P2-033 | Budgeted NB Learning (Lizotte et al. 2003) | CLOSE_ANALOGUE | VERIFIED arXiv:1212.2472 | which feature to purchase | acquisition vs value | VOI ordering for budgeted acquisition | CANDIDATE |
| P2-034 | Fixed-budget ranking & selection (Wu & Zhou 2018) | CLOSE_ANALOGUE | VERIFIED arXiv:1811.12183 | allocation of fixed budget | false-selection prob | budget allocation across candidates | BACKGROUND |
| P2-035 | Adaptive kNN graph model (Li, Xu & Zhang 2026) | ALGORITHMIC_INSPIRATION | VERIFIED arXiv:2601.16509 | per-query k in graph index | inference cost vs accuracy | per-query adaptive neighborhood count → B_t | CANDIDATE |
| P2-036 | Adaptive neighborhood metric learning (Song et al. 2022) | ALGORITHMIC_INSPIRATION | VERIFIED arXiv:2201.08314 | neighborhood radius | metric objective | difficulty-driven B_t analogue | REJECT_DEFER (learned) |
| P2-037 | Wald SPRT (Wald 1945) | BACKGROUND_ONLY | CLASSICAL (canonical, no arXiv) | when to stop testing | sample size vs errors | sequential stopping foundation for P2-P1/P2-P2 | BACKGROUND |
| P2-038 | Chow's optimum rejection (Chow 1957) | BACKGROUND_ONLY | CLASSICAL (canonical, no arXiv) | reject threshold | error vs rejection cost | selective-prediction ancestor of P2-P2 | BACKGROUND |
| P2-039 | Selective prediction / abstention (El-Yaniv & Wiener 2010) | ALGORITHMIC_INSPIRATION | VERIFIED (classical JMLR line) | abstention decision | risk vs coverage | coverage-controlled abstention ~ P2-P2 | CANDIDATE |

### Expansion interpretation (decision-oriented, tied to the P2 Phase-1 result)

- The Phase-1 P2 evaluation (2026-09-18) showed the four simple deterministic
  policies (P2-P1..P2-P4) do NOT beat fixed-B on DEVELOPMENT; the strong-method
  gate is False and the negative is frozen.
- The expanded landscape therefore serves as the **Phase-2 candidate pool** (not
  implemented): the most decision-relevant additions are the deterministic
  confidence/budget analogues — **P2-031 Confidence-Budget Matching** (cost-
  ratio stopping theory), **P2-026/P2-039 selective-prediction coverage rules**,
  **P2-027 early-exit cascade thresholds**, and **P2-035 per-query adaptive k**
  — each of which maps to a deterministic `B_t` rule family already partially
  instantiated by P2-P1..P2-P4. The learned variants (ACT, MoE, L2D) remain
  deferred/background per the "no neural policy in Phase 1" constraint.
- **Leakage discipline:** VOI/active-search analogues that require gold/reward
  in the policy loop (P2-028, and any bandit allocation with reward = hidden
  proxy) stay REJECT_DEFER.

### Status

**LANDSCAPE EXPANDED (2026-09-18)** — 39 classified entries (24 original + 15
added), all serious entries verified from primary sources where accessible.
Machine-readable: `research/literature/p2_algorithm_landscape.csv`.
Literature decision ledger updated
(`reports/LITERATURE_DECISION_LEDGER.md`).