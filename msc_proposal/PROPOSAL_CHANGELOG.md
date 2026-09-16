# MSC Proposal V1 — Changelog

## V1 (2026-09-16)

- **Initial supervisor-ready draft.**
- Title: *Cost-Aware Repository Change Localization with Sparse Impact Planning
  and Bounded Verification* (does not assume graph/RiskScorer success).
- 16 sections: background, problem, gap, objectives, RQs, current evidence,
  architecture, dataset methodology, baselines, evaluation, statistical plan,
  generalization plan, threats, contributions, work plan/timeline, references.
- Evidence included truthfully:
  - M1A/M1B controlled representation effect;
  - real-commit P1 (60 cells), LocAgent P5 (10 tasks);
  - cheap baselines (Protocol A);
  - 90-cell Sparse-v2 TRAIN/VALIDATION development inference (90/90 valid,
    490,747 tokens / $0.184);
  - V2 development inference (431/450 cells, 144 tasks;
    signal does not replicate → no RiskScorer);
  - classical/static CIA baseline (150 V2 dev cases, zero LLM).
- Contingencies pre-registered: Route A (task-level routing) vs Route B
  (candidate-level bounded verification); **no positive algorithmic result
  promised**.
- References: `references.bib` (verified + preprint-marked; 4 entries flagged
  "author list to be confirmed from primary source" — NO fabricated citations).
- Compiled with pdflatex: 6 pages, clean (2 passes).
- Known open items for supervisor:
  1. institutional (FCAI) template/cover/signature pages — intentionally not
     fabricated;
  2. confirm RQ wording and Route A/B framing;
  3. decide whether to expand the 6-page draft with evidence tables.

<!-- Append new versions below. -->