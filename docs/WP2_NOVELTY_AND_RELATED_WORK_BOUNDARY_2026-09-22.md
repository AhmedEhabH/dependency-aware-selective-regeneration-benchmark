# WP-2 Novelty and Related-Work Boundary (2026-09-22)

This document records what is NOT novel, what is proposed as a candidate
contribution to test, and the verified prior-art boundaries. Terminology:
**candidate differentiators / novelty hypotheses** are hypotheses to test, not
established facts.

## NOT novel by itself

- graph-based impact analysis;
- intent-aware change-impact prediction;
- repository memory / history;
- localize-then-repair;
- restrictive file gate as a concept;
- use of gold / oracle files;
- F2P / P2P testing.

## Verified prior art (boundaries)

- **Cost-Effective Repository Exploration for Agentic Issue Localization**
  (arXiv:2608.29675) already names restrictive file gates as a concept.
- **Loc2Repair** (arXiv:2606.30963) already links localization to downstream
  repair under a matched runtime.
- **Agentless** (arXiv:2407.01489) already uses localization → repair →
  validation.
- **RIPPLE** (ICSE 2026, DOI 10.1145/3744916.3773265) already studies
  intent-aware impact sets.
- **FEA-Bench** (ACL 2025, DOI 10.18653/v1/2025.acl-long.839) already evaluates
  incremental feature implementation and compares Oracle/BM25 context.
- **FastContext** (arXiv:2606.14066): current arXiv v4 is **withdrawn**; do not
  use as positive evidence without an explicit withdrawal note.

## Candidate differentiators / novelty hypotheses (to test, not asserted)

1. hard selective-regeneration contract vs soft localization hint under the
   SAME selector and downstream generator;
2. interventional functional-sufficiency analysis with a size-matched placebo;
3. causal Critical Omission Risk via Gold-minus-one subset;
4. real requirement/change-driven evolution tasks rather than only issue repair;
5. full pipeline cost: selection + generation + validation + repair;
6. preservation and architecture compliance under bounded editing scope.

These are framed as hypotheses until focused related-work review and E2E
evidence support them. The oracle-confirmation substrate built in this mission
(220-task F2P census, 8 confirmed behavioral oracles, per-file evaluator,
per-state test DB) is the measurement infrastructure that will let those
hypotheses be tested.