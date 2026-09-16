# MSC Proposal V1 — Supervisor Brief

**Title:** *Cost-Aware Repository Change Localization with Sparse Impact
Planning and Bounded Verification*
**Author:** Ahmed Ehab
**Status:** V1 supervisor-ready draft (2026-09-16). Content transplantable into
an official FCAI template; no institutional form fields are fabricated.

---

## One-paragraph summary

Before an LLM edits a repository it must decide which files a change affects.
This thesis studies that decision as a **correctness–cost trade-off under
limited inference budgets**: represent the impact policy cheaply
(*preserve-by-omission* sparse plans), localize with cheap/classical/LLM
methods under one protocol, and add a **bounded** second-stage mechanism that
revisits the scope (Route A, task-level) or individual suspicious omitted
candidates (Route B, candidate-level) under a hard budget. Current evidence:
sparse representation cuts serialization/cost dramatically in controlled
studies; BM25 is a real zero-LLM signal; but task-level omission risk is not
reliably predictable yet, so the thesis does **not** depend on a risk scorer
succeeding.

## What is already done (audited)

- Controlled encoding studies (M1A/M1B): Sparse-v2 vs Full-v2, large
  serialization/cost reductions; no semantic superiority claim.
- Real-commit datasets + held-out P1 (60 cells) and LocAgent shared-protocol
  P5 (10 tasks): real-commit semantic selection is hard; LocAgent very
  expensive with a 50% empty rate.
- Cheap baselines (Protocol A): BM25 meaningful zero-LLM localization.
- Sparse omission-risk development inference (90 cells TRAIN/VALIDATION, then
  431/450 V2 cells under authorized ceilings): **task-level RiskScorer is not
  justified** on current evidence; the apparent V2 pooled signal is a
  candidate-universe-size artifact.
- Classical/static CIA baseline on 150 V2 development cases (zero LLM).
- V2 dataset design, sample-size analysis, split proposal (metadata-only,
  untouched internal test + reserve), Saleor/NestJS suitability protocols.

## What the thesis will do

1. Build Stage 1 djangoCMS V2-LARGE with an untouched internal test;
2. evaluate sparse/cheap/classical/LLM localization under common file-level
   metrics with explicit budgets;
3. design + test bounded verification (Route B candidate-level default;
   Route A only if a larger development set justifies it);
4. cross-repository confirmation (Saleor if feasible, NestJS as
   cross-ecosystem check);
5. report per-repository correctness–cost Pareto evidence with a
   repository-identity confound check.

## Pre-registered decisions

- **No zero-LLM/cheap signal yet justifies a task-level risk scorer**
  (class-balance gate failed; signal does not replicate within V2).
- **Contingency:** if task-level risk remains unseparable, answer RQ3 with
  candidate-level bounded verification (Route B), not a weak risk scorer.
- **Exposure discipline:** the v1 40 are LEGACY_EXPOSED_V1; a fresh untouched
  internal test is reserved and never tuned on.

## Timeline to 1 October 2026

- 2026-09-16/17: Proposal V1 supervisor-ready draft (**this package**).
- by 2026-09-22: supervisor-feedback integration.
- by 2026-09-25: scientific content freeze.
- by 2026-09-27: print-layout freeze.
- by 2026-09-29: physical print ready; 2026-09-30 safety buffer;
  before 2026-10-01: submission-ready printed proposal.

## What I need from you

1. Feedback on the working title and RQs (RQ1–RQ4).
2. Confirmation that the Route A/B contingency framing is acceptable.
3. Any institutional template/pages requirements (FCAI cover page, committee
   signatures) — these are intentionally not fabricated here.