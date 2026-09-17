"""P2 — common evaluator (DEVELOPMENT only; deterministic; ZERO API).

Computes, per task and then pooled:

- ORR / FNRR at the REALIZED budget ``B_t`` (macro and micro),
- expected B / task (mean realized budget),
- verifier candidates inspected (= B_t) and tokens / cost via the measured
  model,
- fraction of the Oracle gap closed,
- over-allocation and under-allocation rates,
- strata by omitted-size / universe-size / proxy-size buckets,
- matched fixed-B comparison (recovery-vs-cost vs the fixed-B curve),
- Pareto frontier (cost/task vs ORR).

Cost semantics (documented, frozen): the frozen confirmatory verifier used ONE
call per (task, B) presenting B candidates. The P2 policies decide ``B_t``
from observable features BEFORE any verifier call, so the faithful model is a
single batch inspection of the top-``B_t`` candidates (``calls/task = 1``),
with ``candidates = B_t`` and tokens/cost = measured model at ``B_t``. A
labelled per-candidate ``marginal_calls = B_t`` column is included as a
sensitivity, not the primary model.
"""
# ruff: noqa: N803, N806
# B / N / M are the frozen protocol's budget / omitted-count / missed-count
# symbols (docs/ROUTE_B_V2_DEVELOPMENT_PROTOCOL.md); B_t is the realized budget.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .cost_model import VerifierCostModel
from .policies import BudgetPolicy, PolicyView
from .tasks import FIXED_BUDGETS, ObservableTask

# ---------------------------------------------------------------------------
# Recovery primitives (evaluation-only)
# ---------------------------------------------------------------------------


def recovery_at(task: ObservableTask, B: int, *, ranker: str = "composite") -> int:
    """Number of recovered Sparse-observed FNs within the top-B of a ranking."""
    N = task.omitted_size
    if B <= 0 or N == 0:
        return 0
    B_eff = min(B, N)
    if ranker == "composite":
        ranked = task.ranked_paths
    elif ranker == "bm25":
        ranked = tuple(
            p for p, _ in sorted(
                ((c.path, c.bm25) for c in task.candidates),
                key=lambda kv: (-kv[1], kv[0]),
            )
        )
    elif ranker == "oracle":
        ranked = tuple(
            p for p, _ in sorted(
                ((c.path, c.is_missed_positive) for c in task.candidates),
                key=lambda kv: (-kv[1], kv[0]),
            )
        )
    else:
        raise KeyError(ranker)
    top = set(ranked[:B_eff])
    return sum(1 for c in task.candidates if c.path in top and c.is_missed_positive)


def analytic_random_recovery(task: ObservableTask, B: int) -> float:
    """Hypergeometric expectation E[X] = B*M/N (B clipped to N)."""
    N = task.omitted_size
    M = task.n_missed
    if N == 0 or M == 0 or B <= 0:
        return 0.0
    return min(B, N) * M / N


# ---------------------------------------------------------------------------
# Evaluation result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TaskResult:
    name: str
    case_id: str
    repository: str
    role: str
    realized_budget: int
    orr: float
    fnrr: float
    recovered: int
    total_missed: int
    candidates: int
    tokens: float
    cost_usd: float
    calls_batch: int
    marginal_calls: int
    oracle_gap_closed: float
    over_allocation: int
    under_allocation: float
    omitted_size: int
    universe_size: int


def _aggregate(rows: list[TaskResult]) -> dict[str, Any]:
    if not rows:
        return {"n_tasks": 0, "macro_orr": 0.0, "micro_orr": 0.0, "fnrr": 1.0,
                "total_recovered": 0, "total_missed": 0, "expected_budget": 0.0,
                "mean_candidates": 0.0, "mean_tokens": 0.0, "mean_cost_usd": 0.0,
                "mean_oracle_gap_closed": 0.0, "over_allocation_rate": 0.0,
                "under_allocation_rate": 0.0}
    macro_orr = float(np.mean([r.orr for r in rows]))
    tot_rec = sum(r.recovered for r in rows)
    tot_missed = sum(r.total_missed for r in rows)
    micro_orr = tot_rec / tot_missed if tot_missed else 0.0
    return {
        "n_tasks": len(rows),
        "macro_orr": round(macro_orr, 4),
        "micro_orr": round(micro_orr, 4),
        "fnrr": round(1.0 - macro_orr, 4),
        "total_recovered": tot_rec,
        "total_missed": tot_missed,
        "expected_budget": round(float(np.mean([r.realized_budget for r in rows])), 4),
        "mean_candidates": round(float(np.mean([r.candidates for r in rows])), 4),
        "mean_tokens": round(float(np.mean([r.tokens for r in rows])), 4),
        "mean_cost_usd": round(float(np.mean([r.cost_usd for r in rows])), 6),
        "mean_oracle_gap_closed": round(float(np.mean([r.oracle_gap_closed for r in rows])), 4),
        "over_allocation_rate": round(float(np.mean([r.over_allocation for r in rows])), 4),
        "under_allocation_rate": round(float(np.mean([r.under_allocation for r in rows])), 4),
    }


def evaluate_fixed_b(
    tasks: list[ObservableTask],
    B: int,
    *,
    ranker: str = "composite",
    cost_model: VerifierCostModel | None = None,
) -> dict[str, Any]:
    """Fixed-B anchor evaluation (composite or bm25 ranking)."""
    cost_model = cost_model or VerifierCostModel()
    rows: list[TaskResult] = []
    for t in tasks:
        rec = recovery_at(t, B, ranker=ranker)
        N = t.omitted_size
        M = t.n_missed
        orr = rec / M if M else 0.0
        rand = analytic_random_recovery(t, B)
        oracle = min(B, N, M) if M else 0
        gap = (rec - rand) / (oracle - rand) if (oracle - rand) > 0 else (1.0 if rec >= oracle > 0 else 0.0)
        # over/under allocation relative to the composite max-recovery grid point
        best_B, best_rec = B, rec
        for b in FIXED_BUDGETS:
            r = recovery_at(t, b, ranker=ranker)
            if r > best_rec or (r == best_rec and b < best_B):
                best_B, best_rec = b, r
        rows.append(
            TaskResult(
                name=f"fixed-B{B}", case_id=t.case_id, repository=t.repository, role=t.role,
                realized_budget=B, orr=orr, fnrr=1.0 - orr if M else 0.0, recovered=rec,
                total_missed=M, candidates=min(B, N) if N else 0,
                tokens=cost_model.prompt_tokens(B), cost_usd=cost_model.api_cost_usd(B),
                calls_batch=1, marginal_calls=min(B, N) if N else 0,
                oracle_gap_closed=gap,
                over_allocation=max(0, B - best_B),
                under_allocation=(best_rec - rec) / M if M else 0.0,
                omitted_size=N, universe_size=t.universe_size,
            )
        )
    agg = _aggregate(rows)
    agg["name"] = f"fixed-B{B}"
    agg["budget"] = B
    return agg


def evaluate_inspect_all(tasks: list[ObservableTask], *, cost_model: VerifierCostModel | None = None) -> dict[str, Any]:
    """InspectAll reference: verify ALL omitted candidates (exhaustive
    reconsideration). ORR = 1.0 by definition; cost = measured verifier model
    at B = omitted size (NOT zero — an honest exhaustive-cost reference)."""
    cost_model = cost_model or VerifierCostModel()
    rows: list[TaskResult] = []
    for t in tasks:
        rec = t.n_missed
        M = t.n_missed
        orr = 1.0 if M else 0.0
        N = t.omitted_size
        rows.append(
            TaskResult(
                name="inspect-all", case_id=t.case_id, repository=t.repository, role=t.role,
                realized_budget=N, orr=orr, fnrr=0.0 if M else 0.0, recovered=rec,
                total_missed=M, candidates=N,
                tokens=cost_model.prompt_tokens(N), cost_usd=cost_model.api_cost_usd(N),
                calls_batch=1 if N > 0 else 0, marginal_calls=N,
                oracle_gap_closed=1.0, over_allocation=0, under_allocation=0.0,
                omitted_size=N, universe_size=t.universe_size,
            )
        )
    agg = _aggregate(rows)
    agg["name"] = "inspect-all"
    return agg


def evaluate_policy(
    tasks: list[ObservableTask],
    policy: BudgetPolicy,
    *,
    cost_model: VerifierCostModel | None = None,
) -> dict[str, Any]:
    """Evaluate an adaptive policy at its REALIZED per-task budget."""
    cost_model = cost_model or VerifierCostModel()
    rows: list[TaskResult] = []
    for t in tasks:
        B_t = int(policy.choose_budget(PolicyView.from_task(t)))
        rec = recovery_at(t, B_t, ranker="composite")
        N = t.omitted_size
        M = t.n_missed
        orr = rec / M if M else 0.0
        rand = analytic_random_recovery(t, B_t)
        oracle = min(B_t, N, M) if M else 0
        gap = (rec - rand) / (oracle - rand) if (oracle - rand) > 0 else (1.0 if rec >= oracle > 0 else 0.0)
        best_B, best_rec = B_t, rec
        for b in FIXED_BUDGETS:
            r = recovery_at(t, b, ranker="composite")
            if r > best_rec or (r == best_rec and b < best_B):
                best_B, best_rec = b, r
        rows.append(
            TaskResult(
                name=policy.name, case_id=t.case_id, repository=t.repository, role=t.role,
                realized_budget=B_t, orr=orr, fnrr=1.0 - orr if M else 0.0, recovered=rec,
                total_missed=M, candidates=B_t,
                tokens=cost_model.prompt_tokens(B_t), cost_usd=cost_model.api_cost_usd(B_t),
                calls_batch=1 if B_t > 0 else 0, marginal_calls=B_t,
                oracle_gap_closed=gap,
                over_allocation=max(0, B_t - best_B),
                under_allocation=(best_rec - rec) / M if M else 0.0,
                omitted_size=N, universe_size=t.universe_size,
            )
        )
    agg = _aggregate(rows)
    agg["name"] = policy.name
    return agg


def matched_fixed_b_summary(policy_agg: dict[str, Any], fixed_curve: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare a policy at its realized cost against the fixed-B curve."""
    p_cost = policy_agg["mean_cost_usd"]
    p_orr = policy_agg["macro_orr"]
    best = None
    for f in fixed_curve:
        if f["mean_cost_usd"] >= p_cost and f["macro_orr"] >= p_orr and (
            best is None or f["mean_cost_usd"] < best["mean_cost_usd"]
        ):
            best = f
    return {
        "policy": policy_agg["name"],
        "policy_cost_usd": p_cost,
        "policy_orr": p_orr,
        "dominates_or_matches_fixed": best is not None,
        "matched_fixed_point": best,
    }


def pareto_frontier(points: list[dict[str, Any]]) -> list[str]:
    """Names of points not strictly dominated (lower cost AND >= ORR, or equal
    cost with higher ORR) by any other point."""
    front = []
    for p in points:
        dominated = False
        for q in points:
            if q is p:
                continue
            q_cost_lt = q["mean_cost_usd"] < p["mean_cost_usd"]
            q_orr_ge = q["macro_orr"] >= p["macro_orr"]
            q_cost_le = q["mean_cost_usd"] <= p["mean_cost_usd"]
            q_orr_gt = q["macro_orr"] > p["macro_orr"]
            if (q_cost_lt and q_orr_ge) or (q_cost_le and q_orr_gt):
                dominated = True
                break
        if not dominated:
            front.append(p["name"])
    return front


def strata_summary(
    tasks: list[ObservableTask],
    policy: BudgetPolicy,
    *,
    cost_model: VerifierCostModel | None = None,
) -> dict[str, Any]:
    """Task-size strata (omitted-size / universe-size terciles)."""
    cost_model = cost_model or VerifierCostModel()
    out: dict[str, Any] = {}
    Ns = sorted(t.omitted_size for t in tasks)
    q33 = Ns[len(Ns) // 3] if Ns else 0
    q66 = Ns[2 * len(Ns) // 3] if Ns else 0
    buckets: dict[str, list[ObservableTask]] = {"small": [], "medium": [], "large": []}
    for t in tasks:
        if t.omitted_size <= q33:
            buckets["small"].append(t)
        elif t.omitted_size <= q66:
            buckets["medium"].append(t)
        else:
            buckets["large"].append(t)
    for k, ts in buckets.items():
        agg = evaluate_policy(ts, policy, cost_model=cost_model)
        out[k] = {"n_tasks": agg["n_tasks"], "macro_orr": agg["macro_orr"], "expected_budget": agg["expected_budget"]}
    return out
