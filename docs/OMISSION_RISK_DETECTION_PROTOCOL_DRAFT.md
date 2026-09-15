# OMISSION-RISK DETECTION PROTOCOL — DRAFT (THESIS CORE; DOCUMENT-ONLY)

**Status:** DRAFT / PLANNING ONLY. **No risk detector is trained, tuned, or
executed in this block.** This is the central planned MSc mechanism; it is
funded by the roadmap as Pillar 8.

**Owner:** Ahmed (MSc) · **Constraint:** develop using TRAIN/VALIDATION only;
NEVER tune on the exposed ten-task HELD_OUT_TEST; not implemented before
full-baseline establishment.

---

## 1. Research question

> Can signals available **after the cheap Sparse first pass** predict elevated
> false-negative risk well enough to **selectively invoke a more expensive
> verifier** (bounded graph/agent verification), so that verification budget
> is spent mostly on the tasks/cases where omissions are likely?

## 2. Motivation (frozen P1 diagnostics)

- Full-v2 FN 70: **PRESERVE 70** / VALIDATE 0 / HUMAN_REVIEW 0.
- Sparse-v2 FN 82: **PRESERVE 74** / VALIDATE 8 / HUMAN_REVIEW 0.

Most missed affected files are **silent PRESERVE decisions** — action labels
alone cannot identify most omissions, so an **independent omission-risk signal**
is required. Risk estimates would gate escalation:

```
Sparse first-pass impact plan
    ↓
Omission-risk estimation
    ↓
low risk → accept
high risk → bounded graph/agent verification
    ↓
revised impact scope
```

## 3. Candidate feature families (to investigate LATER)

Available **after the cheap Sparse first pass**, without hidden gold:

1. Predicted write-set size / density (posterior size, candidate density).
2. VALIDATE count (explicitly flagged validation boundary).
3. HUMAN_REVIEW count / escalation triggers in the first pass.
4. Action-distribution entropy across the plan.
5. First-pass self-consistency / disagreement (multi-trial or retry variance).
6. Requirement length / ambiguity proxies (intent token count, specificity).
7. Lexical-retrieval disagreement (first-pass vs BM25@K ranking distance).
8. Graph neighborhood characteristics (seed/frontier size, reachable zone,
   cross-component counts).
9. Subsystem novelty / history (path touched in recent history proxies).
10. Candidate density in the affected neighborhood.
11. Model confidence proxies IF available without hidden gold (confidence
    scores, finish-reason, truncation).

**Forbidden features:** hidden gold, future commit, changed-file proxy,
serious-test-derived information, any exposed-HELD_OUT-derived statistic.

## 4. Planned routing metrics

- AUROC / AUPRC of the risk score vs the observed omission label (development).
- Calibration (ECE/reliability) of the risk probability.
- **Risk–coverage curve:** retained risk vs fraction of cases escalated.
- **Escalation rate** at operating points.
- **FN recovery rate** (un-missed files among escalated cases).
- **Cost per recovered FN** (verifier cost / additional true positives found).

## 5. Planned future escalation arms (design only)

1. **Sparse only** (no escalation).
2. **Always escalate** (full verification upper cost).
3. **Random escalation** at matched budget (control).
4. **Selective escalation** (risk-ranked; the method).
5. **Oracle escalation** (upper bound; uses hidden gold at evalaution time only
   — reported separately, never used for tuning).

## 6. Data discipline

- Risk-detector features, threshold selection, and operating-point choice use
  **TRAIN + VALIDATION only**.
- The exposed ten HELD_OUT_TEST tasks are permanently excluded from any risk
  decision; a fresh confirmatory split/repository is required for any
  confirmatory claim.
- Labels/omission indicators derive from the observed change-set proxy at
  **evaluation time only**.

## 7. Status

Planning only. Nothing here is implemented, trained, or run in the
cheap-nonllm-baselines block or before review and authorization.