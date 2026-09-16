"""Omission-Risk Feature Study V1 — cost-sensitive decision analysis.

DEVELOPMENT-ONLY analysis of the decision form:

    escalate  when  expected_omission_loss > expected_verification_cost

We do NOT pretend to know the true cost of a false negative. Instead we run a
transparent sensitivity analysis over the ratio

    r = C_FN / C_VERIFY

(pre-registered grid: {2, 5, 10, 20, 50, 100}; each cell uses C_VERIFY = 1).

Decision model (per task, simplified):
- Never escalate  -> cost = C_FN * E[|FN|]  (risk score used as P(has_fn) proxy;
  expected non-verified omission cost uses calibrated risk x E[fn | has_fn]).
- Escalate        -> cost = C_VERIFY (verifier invoked once; verified omissions
  are assumed recovered at the verification cost).

Per-task decision uses the calibrated omission probability p_hat(t):
    escalate iff  p_hat(t) * r * lambda > 1
where lambda = E[|FN| | has_fn] estimated on TRAIN (development) only.

Reports, for each ratio r:
- escalation rate (fraction of tasks escalated)
- risky-task recall among escalated
- total cost vs never-escalate / always-escalate policies
This is decision analysis, NOT a final deployment policy.
"""

from __future__ import annotations

from typing import Any


def analyze_cost_sensitivity(
    *,
    risk_score: dict[str, float],
    prob_score: dict[str, float],
    has_fn: dict[str, int],
    fn_pos_mean: float,
    ratio_grid: tuple[float, ...] = (2, 5, 10, 20, 50, 100),
) -> dict[str, Any]:
    """Run the sensitivity table over C_FN/C_VERIFY ratios.

    ``risk_score`` ranks tasks (for recall-at-routing comparisons),
    ``prob_score`` is the calibrated omission probability used for the decision
    rule, ``has_fn`` is the label, ``fn_pos_mean`` is the TRAIN-estimated
    mean |FN| among has_fn=1 tasks (development-only statistic).
    """
    tasks = sorted(risk_score)
    n = len(tasks)
    out: dict[str, Any] = {
        "n_tasks": n,
        "fn_pos_mean": fn_pos_mean,
        "decision_rule": (
            "escalate iff p_hat(t) * ratio * E[|FN||has_fn] > 1 "
            "(expected omission loss > expected verification cost = 1)"
        ),
        "ratios": {},
    }
    for r in ratio_grid:
        escalated: list[str] = []
        escalated_set: set[str] = set()
        cost_never_r = 0.0
        for t in tasks:
            expected_loss = prob_score[t] * r * fn_pos_mean
            cost_never_r += expected_loss
            if expected_loss > 1.0:
                escalated.append(t)
        escalated_set = set(escalated)
        n_pos = sum(has_fn[t] for t in tasks)
        captured = sum(1 for t in escalated if has_fn[t])
        # Cost model: escalate -> C_VERIFY = 1; skip -> expected omission loss.
        cost_total = 0.0
        for t in tasks:
            expected_loss = prob_score[t] * r * fn_pos_mean
            cost_total += 1.0 if t in escalated_set else expected_loss
        out["ratios"][str(r)] = {
            "ratio": r,
            "escalation_rate": len(escalated) / n if n else 0.0,
            "n_escalated": len(escalated),
            "risky_recall_among_escalated": (
                captured / n_pos if n_pos else 0.0
            ),
            "cost_total": cost_total,
            "cost_never_escalate": cost_never_r,
            "cost_always_escalate": float(n),
            "cost_saving_vs_always": (
                (n - cost_total) / n if n > 0 else 0.0
            ),
            "cost_vs_never_ratio": (
                cost_total / cost_never_r if cost_never_r > 0 else 0.0
            ),
        }
    return out
