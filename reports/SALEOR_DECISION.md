# Saleor Decision

**Date:** 2026-09-11

## 1. The comparison

Two ways to strengthen external validity:

- **A.** More independent real djangoCMS changes (see
  `reports/REAL_COMMIT_BENCHMARK_PLAN.md`), or
- **B.** Add Saleor now.

## 2. Analysis

Saleor would improve **cross-project** external validity (a second,
materially different repository). But adding another repository does **NOT**
fix weak scenario construction if the scenarios remain manually authored —
the same author-created requirement/gold bias would carry over to Saleor.

Marginal value comparison:

- **20–30 real djangoCMS commits** attack the root limitation (author-created
  requirement/gold bias) directly, within a codebase whose selection behavior
  the current studies already characterize.
- **A smaller manually constructed Saleor set** adds a second repository but
  keeps the manual-construction bias; its marginal validity gain is limited
  unless the Saleor scenarios are also real-commit-derived.

## 3. Recommendation

Do **not** automatically recommend Saleor merely to increase the project
count.

- If the supervisor wants **cross-project generalization**, Saleor may be
  worthwhile (ideally with real-commit-derived scenarios).
- If the supervisor wants a **focused mechanism paper**, real djangoCMS
  commits have higher immediate value.

No Saleor execution was performed in this task.