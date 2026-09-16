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