# Baseline Selection Ledger

**Purpose:** every baseline — included/excluded, fairness/input-contract,
implementation status, reason, comparison role. Appendix to the comparison plan.

---

## B-001 — Random/cheap control
- **Status:** INCLUDED (implemented).
- **Input contract:** matched candidate budget; no hidden gold.
- **Role:** floor control; matched-budget random verification control.
- **Reason:** establishes chance floor.

## B-002 — BM25
- **Status:** INCLUDED (implemented, Protocol A + CIA).
- **Input contract:** parent-visible corpus; zero-LLM.
- **Role:** strongest cheap lexical baseline.
- **Reason:** meaningful zero-LLM signal.

## B-003 — Adaptive cheap retrieval
- **Status:** INCLUDED if justified; adaptive-K REJECTED (did not beat K=10).
- **Reason:** no benefit observed on development data.
- **Role:** K = operating-point curve, not a fixed config.

## B-004 — Classical/static change-impact analysis (dependency propagation)
- **Status:** INCLUDED (implemented, Milestone D).
- **Input contract:** parent-only graph; zero-LLM.
- **Role:** fair classical baseline; not CodeQL (input contract incompatible).
- **Reason:** thesis must compare LLM/agent vs classical baselines.

## B-005 — Sparse planner
- **Status:** INCLUDED (executed).
- **Role:** first-pass representation of interest.
- **Reason:** core contribution.

## B-006 — Full planner
- **Status:** INCLUDED (executed).
- **Role:** explicit-policy comparator.
- **Reason:** isolates representation effect.

## B-007 — Graph-guided reference agent (LocAgent)
- **Status:** INCLUDED at shared-protocol level (P5); NOT a faithful reproduction.
- **Role:** expensive system-level context.
- **Reason:** cost/efficiency comparison.
- **Fairness note:** OpenRouter-routed, upstream temp 1, 10 tasks, 5/10 usable.

## B-008 — Sparse + Always Verify
- **Status:** INCLUDED (design).
- **Role:** upper-cost reference for the verification question.
- **Reason:** always-on expensive reasoning comparator.

## B-009 — Sparse + Random Verify (matched budget)
- **Status:** INCLUDED (design; key control for Route B).
- **Role:** matched-budget random control.
- **Reason:** primary comparison is R_best vs Random at B=5.

## B-010 — Sparse + Selective/Bounded Verify (Route B candidate-level)
- **Status:** INCLUDED (design; primary mechanism).
- **Role:** the method.
- **Reason:** candidate-level bounded verification under a hard budget.

## B-011 — Oracle-routing upper bound
- **Status:** INCLUDED (evaluation-only).
- **Role:** upper bound; never used for tuning.
- **Reason:** quantifies headroom.

## B-012 — Repoformer / FastCoder (selective-retrieval / verification priors)
- **Status:** VERIFIED via triage; used as related-work, not as a new baseline in
  this thesis (different task: code completion, not change localization).
- **Reason:** guards generic "selective escalation is novel" claims; noted as
  cross-domain inspiration.

## B-013 — Historical change-history CIA baselines (Change-Patterns Mapping,
    Software Impact Analysis Tool, recommendation-system CIA, learning
    dependency-based predictors)
- **Status:** VERIFIED via triage; candidate classical/history baselines for
  Route B history evidence and cross-repo generalization.
- **Reason:** direct overlap with candidate-level omission recovery using
  history/co-change features.