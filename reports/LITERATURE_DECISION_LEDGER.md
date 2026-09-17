# Literature Decision Ledger

**Purpose:** every high-priority related work — use now / background / reject /
verify — with exact reason and novelty/design implication. Built from the
BibTeX triage (2026-09-16) and the living systematic review.

Format: `title [classification] — reason; novelty/design implication`.

---

## USE_NOW (verified from primary sources)

1. **LLM-Driven Cost-Effective Requirements Change Impact Analysis**
   (arXiv 2511.00262, Etezadi et al. 2025)
   — USE_NOW. Same cost-aware CIA question but requirements-to-requirements,
   NOT repository file localization. Implication: cost-aware CIA is an active
   line; our differentiator is file-level sparse impact planning + bounded
   omission recovery on real commits.

2. **Change-Patterns Mapping: A Boosting Way for Change Impact Analysis**
   (TSE 2022, 10.1109/TSE.2021.3059481, Huang et al.)
   — USE_NOW. History/change-pattern augmentation of CIA — a "boost initial
   impact set using historical patterns" mechanism close to our Route B
   candidate second-look design. Implication: Route B history evidence must be
   compared against / positioned after this established mechanism.

3. **Learning dependency-based change impact predictors using independent
   change histories** (IST 2015, 10.1016/j.infsof.2015.07.007, Abdeen et al.)
   — USE_NOW. Cross-project/history-based impact prediction. Implication:
   supports history/co-change features and cross-repository generalization;
   classical lineage.

4. **A Software Impact Analysis Tool based on Change History Learning and its
   Evaluation** (ICSE-SEIP 2022, 10.1145/3510457.3519017, Iwasaki et al.)
   — USE_NOW. History-learned candidate recommendation. Implication: classical/
   history baseline + novelty threat for candidate-level omission recovery.

5. **Enhancing Code Understanding for Impact Analysis by Combining Transformers
   and Program Dependence Graphs** (arXiv 2607.23355, Yan et al. 2026)
   — USE_NOW. Modern transform+PDG impact analysis. Implication: graph+LLM for
   impact analysis is active; our graph is only one optional verifier.

6. **Repoformer: Selective Retrieval for Repository-Level Code Completion**
   (arXiv 2403.10059, Wu et al. 2024)
   — USE_NOW. Selective-compute/retrieval prior (different task: code
   completion). Implication: guards generic "selective escalation is novel";
   we apply selective/bounded compute to change localization under matched
   budgets.

7. **FastCoder: Accelerating Repository-level Code Generation via Efficient
   Retrieval and Verification** (arXiv 2502.17139, Zhao et al. 2025)
   — USE_NOW. Efficiency+verification at repo level (code generation).
   Implication: verification mechanism/cost accounting must be compared; design
   threat to our bounded-verification framing.

8. **Issue Localization via LLM-Driven Iterative Code Graph Searching**
   (arXiv 2503.22424, Jiang et al. 2025)
   — USE_NOW. Graph-guided issue localization competitor. Implication: compare
   with LocAgent/GraphLocator/Route B.

9. **Supporting Change Impact Analysis Using a Recommendation System: An
   Industrial Case Study in a Safety-Critical Context**
   (TSE 2017, 10.1109/TSE.2016.2620458, Borg et al.)
   — USE_NOW. Recommendation-system CIA with industrial grounding. Implication:
   classical/history lineage; industrial validity reference.

## BACKGROUND_ONLY

10. **A Prediction Model for Software Requirements Change Impact**
    (ASE 2021, 10.1109/ASE51524.2021.9678582, Zamani)
    — BACKGROUND_ONLY. Requirements-level prediction; not a direct file baseline.
    Implication: background for the requirements-CIA line (item 1).

## VERIFY_FIRST (representative; full list in triage CSV)

- Remaining software-CIA / localization / retrieval / verification /
  selective-compute items (260 titles) are VERIFY_FIRST pending primary-source
  checks. Only a small high-signal subset will be cited; the rest are candidates.

## REJECT_IRRELEVANT (noise; representative)

- Robotics/SLAM "graph localization", NLP dependency parsing, medical/
  selective-prediction, generic graph acceleration, vulnerability propagation
  without a transferable mechanism — recorded as REJECT_IRRELEVANT in the CSV.
  NOT cited.

## Novelty implication

Existing work covers several individual components; this thesis evaluates their
**combination** (sparse explicit impact policy + bounded omission recovery under
matched correctness-cost budgets) — we avoid an absolute "none combines..."
claim unless the verified matrix supports it. Candidate novelty remains
`CANDIDATE NOVELTY — NOT YET CLAIMED`.
## 2026-09-17 terminology note (ranked identity audit)

- The label Classical-CIA in the Route-B V2/transfer results refers to the
  BM25+Graph-Neighbor Composite (normalized BM25 + binary graph-neighbor),
  NOT to classical dependency-propagation CIA. The genuine classical CIA
  baseline (classical_cia_baseline_v1.py, CIA-1H/CIA-2H) is a separate
  implementation. Reports/proposal V1.4 use the corrected name.
- No literature claim changes; this is naming discipline only.

## 2026-09-17 P2 algorithm landscape (after CONFIRMATION)

The fixed Route-B story is now **CONFIRMED** on djangoCMS INTERNAL_TEST
(2026-09-17). P2 (adaptive-budget `B_t`) is a separate DEVELOPMENT-only program
(Nov 2026 – Mar 2027). The full landscape is:
`reports/P2_ALGORITHM_LANDSCAPE_2026-09.md` +
`research/literature/p2_algorithm_landscape.csv`.

Classification summary (24 entries):

- **Track A (SE novelty threats, existing knowledge, anchors only):**
  RIPPLE/change-propagation, Change-Patterns Mapping, ArtifactSync,
  GraphLocator, LocAgent, RepoCoder/RepoAgent/repository memory, history/
  co-change CIA, Repoformer/FastCoder (selective repo retrieval/verification),
  Agentless — reference/anchor only, NOT P2 algorithm candidates.
- **Track B (algorithmic inspiration, verified):** Shichao-Zhang line
  (Learning-k, one-step KNN, cost-sensitive KNN, reachable-distance KNN,
  demand-driven kNN) → ALGORITHMIC_INSPIRATION; plus adaptive/conditional
  computation, selective prediction/abstention, learning-to-defer, cascaded
  inference, optimal stopping, budgeted retrieval, active search/VOI,
  contextual bandits (reject), learned stopping (reject).
- **Pre-registered P2 policy family (this project):** P2-P1 score-gap
  stopping, P2-P2 marginal-score threshold, P2-P3 cost-ratio stopping.

Decision rules for P2:
- Implement (DEV only): P2-P1/P2-P2/P2-P3; score-gap/marginal/cost-ratio
  analogues; deterministic selective/cascade/optimal-stopping variants.
- Reject/defer: learned (neural) stopping, contextual bandit allocation,
  active-search VOI (leak risk) — unless a gold-free mechanistic variant is
  justified.
- No P2 method is selected using the opened djangoCMS INTERNAL_TEST; Saleor
  INTERNAL_TEST stays sealed as a possible future P2 confirmation set.
