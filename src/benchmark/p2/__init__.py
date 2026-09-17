"""P2 Phase-1 — common adaptive-budget DEVELOPMENT harness.

The P2 scientific question (frozen):

> Can an observable adaptive budget policy choose B_t per task so that expected
> omission recovery is comparable to or better than fixed-B while using fewer
> verifier candidates/calls/tokens/cost?

This package implements the common DEVELOPMENT-only harness, the frozen
anchors, the measured verifier cost model, the four pre-registered
interpretable policies (P2-P1..P2-P4), and the common evaluator. ZERO new
model/API calls: all evaluation is a deterministic recomputation from frozen
djangoCMS DEV (174 tasks) and Saleor DEV (149 tasks) artifacts plus the
verifier cost model measured from the 320 confirmatory verifier calls.

Boundaries (hard, enforced by tests):
- Policies receive ONLY parent-visible observable features (never the hidden
  proxy / gold / ``is_missed_positive``).
- ``DEV_TRAIN`` (djangoCMS) is the ONLY split used to derive frozen constants;
  ``DEV_VALIDATION`` (djangoCMS) and Saleor DEV are validated UNCHANGED.
- The opened djangoCMS INTERNAL_TEST and all RESERVE / Saleor
  INTERNAL_TEST/RESERVE sets are never loaded.
"""

from __future__ import annotations

from .cost_model import VerifierCostModel, measured_verifier_cost_model
from .evaluate import (
    evaluate_fixed_b,
    evaluate_inspect_all,
    evaluate_policy,
    matched_fixed_b_summary,
    pareto_frontier,
    strata_summary,
)
from .policies import (
    BudgetPolicy,
    P2P1ScoreGap,
    P2P2MarginalScore,
    P2P3CostRatio,
    P2P4LearningK,
    make_policy,
)
from .tasks import (
    ObservableCandidate,
    ObservableTask,
    load_dev_tasks,
)

__all__ = [
    "VerifierCostModel",
    "measured_verifier_cost_model",
    "BudgetPolicy",
    "P2P1ScoreGap",
    "P2P2MarginalScore",
    "P2P3CostRatio",
    "P2P4LearningK",
    "make_policy",
    "ObservableCandidate",
    "ObservableTask",
    "load_dev_tasks",
    "evaluate_fixed_b",
    "evaluate_inspect_all",
    "evaluate_policy",
    "matched_fixed_b_summary",
    "pareto_frontier",
    "strata_summary",
]
