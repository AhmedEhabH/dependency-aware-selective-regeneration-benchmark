# BibTeX Literature Triage (2026-09-16)

**Source:** 13 uploaded BibTeX exports (`papers (4)..(16).bib`) treated as
**candidate discovery sources**, not authoritative publication metadata.
High-priority items verified from primary sources (arXiv API / Crossref).

## Summary

- raw entries parsed: **987**
- unique normalized titles: **806**
- duplicates (same title in >1 export): **166**
- USE_NOW: **9**
- VERIFY_FIRST: **260**
- BACKGROUND_ONLY: **56**
- REJECT_IRRELEVANT: **315**

Full machine-readable classification:
`research/literature/bibtex_triage_classified_2026-09-16.csv`.

## High-priority verified items (Section B of the addendum)

| Title | Classification | Verification |
|---|---|---|
| LLM-Driven Cost-Effective Requirements Change Impact Analysis | USE_NOW | arXiv 2511.00262; same cost-aware CIA question; requirements-to-requirements (not file localization); strong novelty/design reference |
| Change-Patterns Mapping: A Boosting Way for Change Impact Analysis | USE_NOW | TSE 2022 10.1109/TSE.2021.3059481; history/change-pattern augmentation of CIA; direct Route-B history-evidence overlap |
| Learning dependency-based change impact predictors using independent change histories | USE_NOW | IST 2015 10.1016/j.infsof.2015.07.007; cross-project/history-based impact prediction; history/co-change + cross-repo relevance |
| A Software Impact Analysis Tool based on Change History Learning and its Evaluation | USE_NOW | ICSE-SEIP 2022 10.1145/3510457.3519017; history-learned candidate recommendation; classical/history baseline + novelty threat |
| Enhancing Code Understanding for Impact Analysis by Combining Transformers and Program Dependence Graphs | USE_NOW | arXiv 2607.23355 (Yan et al 2026); modern transform+PDG impact analysis; graph use overlap, file/entity unit |
| Repoformer: Selective Retrieval for Repository-Level Code Completion | USE_NOW | arXiv 2403.10059 (Wu et al 2024); selective-compute prior; guards against generic 'selective escalation is novel' claims |
| FastCoder: Accelerating Repository-level Code Generation via Efficient Retrieval and Verification | USE_NOW | arXiv 2502.17139 (Zhao et al 2025); efficiency+verification at repo level; exact verification mechanism/cost threat |
| Issue Localization via LLM-Driven Iterative Code Graph Searching | USE_NOW | arXiv 2503.22424 (Jiang et al 2025); graph-guided issue localization competitor vs LocAgent/GraphLocator/Route B |
| Supporting Change Impact Analysis Using a Recommendation System: An Industrial Case Study in a Safety-Critical Context | USE_NOW | TSE 2017 10.1109/TSE.2016.2620458; recommendation-system CIA; classical/history lineage + industrial grounding |
| A Prediction Model for Software Requirements Change Impact | BACKGROUND_ONLY | ASE 2021 10.1109/ASE51524.2021.9678582; requirements-level prediction; background, not direct file baseline |

## Noise / rejection discipline

Query-collision noise (robotics/SLAM, NLP parsing, medical/selective-
prediction, generic graph acceleration, vulnerability) is recorded as
`REJECT_IRRELEVANT` and is NOT cited merely because keywords overlap.
Representative false-positive examples are retained in the CSV with short
reasons.

## Use in the proposal

The 10 verified high-priority items are integrated into the living review
and the comparison matrix. The proposal retains only high-signal
references; it does NOT copy hundreds of entries.