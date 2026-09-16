# MSc Seminar Presentation — Outline (Foundation, not final deck)

**Status:** outline only (2026-09-16). The full visual deck improves AFTER the
proposal print freeze (before 2026-10-01). 10–12 slides.

---

## Storyline (12 slides)

1. **Problem.** Before an LLM edits a repository it must choose which files a
   change affects. That choice is costly and error-prone.
2. **Why scope matters.** A repository-scale explicit plan serializes hundreds
   of records; second-stage reasoning can cost orders of magnitude more than
   the first pass.
3. **Preserve-by-Omission.** Emit only non-preserve decisions; reconstruct
   omitted candidates deterministically as preserve.
4. **Controlled evidence.** M1A/M1B at 16K: Sparse-v2 vs Full-v2 — ~90%
   fewer completion tokens, ~95% fewer serialized records, ~82% lower cost,
   both arms valid.
5. **Real commits.** A reproducible corpus of 40 real djangoCMS changes
   (24/6/10 split), parent-only inputs, observed-change-set proxy.
6. **Cheap / agent comparison.** BM25 is a meaningful zero-LLM signal;
   LocAgent under a shared protocol is very expensive with a 50% empty rate;
   no arm-superiority claim from P1.
7. **Omission-risk finding.** Sparse-v2 development inference (90 cells) shows
   omissions are common (26/30) but a task-level RiskScorer is NOT justified
   on current evidence; V2 (144 more tasks) does not change that — apparent
   signal is a universe-size artifact.
8. **Why a larger V2 is needed.** More negatives, protected untouched test,
   enough power to test the risk question honestly.
9. **Proposed bounded verification.** Route A (task-level routing, only if
   justified) and Route B (candidate-level bounded verification of suspicious
   omitted candidates; compare with always/random matched-budget).
10. **Generalization.** Stage 1 djangoCMS V2-LARGE → Stage 2 Saleor →
    Stage 3 NestJS (cross-ecosystem).
11. **Thesis contributions.** Representation + dataset/protocol + fair
    comparison + bounded-verification protocol + correctness–cost Pareto;
    no positive result promised.
12. **Timeline.** To 1 October (proposal), then V2-LARGE, verification,
    Saleor/NestJS, thesis.

## Figures / data needed

- M1B reduction table (already in repo reports).
- P1 / P5 shared-protocol table.
- Sparse-v2 label prevalence + random-band figure.
- V2 sampling-frame funnel (6000→916→334→329→40→24/6/10).
- Pareto sketch (correctness vs cost; arms annotated).

## Likely supervisor questions (prepare answers)

- "Why is the observed diff a proxy and not ground truth?"
- "Why doesn't the risk signal replicate in V2?" — universe-size confound;
  within-cohort AUROC table.
- "Isn't BM25 enough?" — it is the strongest cheap signal; the thesis adds
  sparse representation + bounded verification + real-commit evidence.
- "Why not just always verify?" — always-verify is an arm; the question is
  whether bounded verification beats it and random matched budget on the
  Pareto frontier.
- "What is the actual contribution?" — the combination + honest evidence,
  and the bounded-verification protocol if supported.

## Claims that must stay carefully scoped

- No "graph-guided" in the primary title without explaining graph is only one
  optional verifier.
- No superiority claim from P1; no RiskScorer claim before gates pass;
  LocAgent numbers are SYSTEM-LEVEL context, not a faithful reproduction.
- Every live-inference number is LIVE API, never a dry run.