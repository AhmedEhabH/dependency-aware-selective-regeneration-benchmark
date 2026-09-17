"""P2 — pre-registered interpretable adaptive-budget policies.

Every policy is a deterministic stopping rule that consumes ONLY observable,
parent-visible features (composite rank scores, task-size proxies) and emits a
per-task verification budget ``B_t``. No policy reads the hidden proxy or the
``is_missed_positive`` label (enforced by tests).

Pre-registered constants:
- P2-P1 Score-gap: ``tau_gap = 0.10`` (relative to the top composite score),
  declared in ``docs/ADAPTIVE_BUDGET_P2_PRE_REGISTRATION_NOTE.md``.
- P2-P2 Marginal-score: ``tau_marg`` = 25th percentile of the DEV_TRAIN
  composite-score distribution (DERIVED on DEV_TRAIN only, before any
  validation/Saleor outcome).
- P2-P3 Cost-ratio: declared cost ratio grid (sensitivity), never monetary
  truth.
- P2-P4 Learning-k analogue: ``tau_energy = 0.90`` (declared); the budget is
  the number of top candidates that explain >=90% of observable score mass
  ("select k per query from the score structure" — the transferred Zhang
  concept), NOT kNN labels/features/distance geometry.

Tie/failure rule (frozen): candidates are ranked by composite score descending
with path-lexicographic tie-break (deterministic); ``B_t`` is clipped to
``[1, omitted_size]``; a task with no candidates (``N == 0``) emits ``B_t = 0``
(no verification); a degenerate task with ``s_1 == 0`` (all flat scores) emits
``B_t = 1`` for gap-based rules (stop immediately, no signal).
"""
# ruff: noqa: N803, N806
# B / N are the frozen protocol's budget / omitted-count symbols.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from .tasks import MAX_BUDGET, ObservableTask


class PolicyInput(Protocol):
    """The observable slice of a task a policy may read.

    Policies receive a plain view with ONLY: composite-sorted scores,
    task-size proxies, and the frozen budget cap. The proxy / labels are
    structurally absent.
    """

    @property
    def composite_scores(self) -> tuple[float, ...]:
        ...

    @property
    def omitted_size(self) -> int:
        ...

    @property
    def universe_size(self) -> int:
        ...


@dataclass(frozen=True)
class PolicyView:
    """Observable-only view of a task handed to a policy (no gold, no proxy)."""

    composite_scores: tuple[float, ...]
    omitted_size: int
    universe_size: int
    max_budget: int = MAX_BUDGET

    @classmethod
    def from_task(cls, task: ObservableTask) -> PolicyView:
        return cls(
            composite_scores=tuple(c.composite for c in task.candidates),
            omitted_size=task.omitted_size,
            universe_size=task.universe_size,
            max_budget=MAX_BUDGET,
        )


class BudgetPolicy(Protocol):
    """A P2 adaptive-budget policy: observable view -> realized budget B_t."""

    name: str

    def choose_budget(self, view: PolicyView) -> int:
        ...


def _clip(B: int, N: int, *, lo: int = 1) -> int:
    if N <= 0:
        return 0
    return max(lo, min(B, N, MAX_BUDGET))


# ---------------------------------------------------------------------------
# P2-P1 — Score-gap stopping
# ---------------------------------------------------------------------------


class P2P1ScoreGap:
    """Stop at the smallest B in {1,3,5,10} whose adjacent relative score gap
    (s_B - s_{B+1})/s_1 drops below ``tau_gap``.

    Deterministic formula (frozen BEFORE any policy outcome):
    ``gap(B) = (s_B - s_{B+1}) / s_1`` with ``s_{B+1} = 0`` when ``B == N``.
    ``B_t = min{B in {1,3,5,10} : gap(B) < tau_gap or B >= N}``, default 10.
    """

    name = "P2-P1-score-gap"

    def __init__(self, tau_gap: float = 0.10) -> None:
        self.tau_gap = float(tau_gap)

    def choose_budget(self, view: PolicyView) -> int:
        s = view.composite_scores
        N = view.omitted_size
        if N <= 0 or not s:
            return 0
        s1 = s[0]
        for B in (1, 3, 5, 10):
            if B >= N:
                return _clip(B, N)
            if s1 == 0:
                return _clip(1, N)
            gap = round((s[B - 1] - (s[B] if len(s) > B else 0.0)) / s1, 6)
            if gap < self.tau_gap:
                return _clip(B, N)
        return _clip(10, N)


# ---------------------------------------------------------------------------
# P2-P2 — Marginal-score stopping
# ---------------------------------------------------------------------------


class P2P2MarginalScore:
    """Stop at the smallest B whose candidate's absolute composite score falls
    below ``tau_marg`` (derived on DEV_TRAIN only as the 25th percentile of the
    DEV_TRAIN composite-score distribution; validated UNCHANGED elsewhere).
    """

    name = "P2-P2-marginal-score"

    def __init__(self, tau_marg: float) -> None:
        self.tau_marg = float(tau_marg)

    def choose_budget(self, view: PolicyView) -> int:
        s = view.composite_scores
        N = view.omitted_size
        if N <= 0 or not s:
            return 0
        for B in (1, 3, 5, 10):
            if B >= N:
                return _clip(B, N)
            if s[B - 1] < self.tau_marg:
                return _clip(B, N)
        return _clip(10, N)


# ---------------------------------------------------------------------------
# P2-P3 — Cost-ratio stopping
# ---------------------------------------------------------------------------


class P2P3CostRatio:
    """Stop when the accumulated verifier cost (measured prompt tokens) up to B
    divided by a task-size proxy (omitted-size N) reaches a DECLARED cost ratio
    ``tau_cost``. ``tau_cost`` is a declared sensitivity parameter (run as a
    curve), NOT a monetary truth.

    Rule: ``B_t = min{B in {1,3,5,10} : cost_tokens(B)/N >= tau_cost}``.
    """

    name = "P2-P3-cost-ratio"

    def __init__(self, tau_cost: float, cost_model: Any) -> None:
        self.tau_cost = float(tau_cost)
        self._cost_model = cost_model

    def choose_budget(self, view: PolicyView) -> int:
        N = view.omitted_size
        if N <= 0:
            return 0
        for B in (1, 3, 5, 10):
            if B >= N:
                return _clip(B, N)
            tokens = self._cost_model.prompt_tokens(B)
            if tokens / N >= self.tau_cost:
                return _clip(B, N)
        return _clip(10, N)


# ---------------------------------------------------------------------------
# P2-P4 — Learning-k analogue (per-task budget from observable score structure)
# ---------------------------------------------------------------------------


class P2P4LearningK:
    """Adapt the Shichao-Zhang 'select k per query' idea to choose B_t.

    TRANSFERRED concept: the neighbor/budget count is selected PER QUERY (per
    task) from the observable structure of the ranked scores — here, the number
    of top candidates whose cumulative score mass explains ``tau_energy`` of
    the total observable score, capped to [1, 10].

    NOT transferred: kNN labels, distance geometry, majority voting, or any
    fitted/learned classifier.

    ``B_t = min{B : sum_{i<=B} s_i / sum_i s_i >= tau_energy}`` (default 10).
    """

    name = "P2-P4-learning-k-analogue"

    def __init__(self, tau_energy: float = 0.90) -> None:
        self.tau_energy = float(tau_energy)

    def choose_budget(self, view: PolicyView) -> int:
        s = view.composite_scores
        N = view.omitted_size
        if N <= 0 or not s:
            return 0
        total = sum(s)
        if total <= 0:
            return _clip(1, N)
        acc = 0.0
        for B in (1, 3, 5, 10):
            if B >= N:
                return _clip(B, N)
            acc += s[B - 1]
            if acc / total >= self.tau_energy:
                return _clip(B, N)
        return _clip(10, N)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def make_policy(name: str, *, tau_marg: float | None = None,
                tau_cost: float | None = None, cost_model: object | None = None) -> BudgetPolicy:
    """Construct a policy by name with frozen/declared constants."""
    if name == "P2-P1-score-gap":
        return P2P1ScoreGap()
    if name == "P2-P2-marginal-score":
        if tau_marg is None:
            raise ValueError("P2-P2 requires tau_marg (derived on DEV_TRAIN)")
        return P2P2MarginalScore(tau_marg)
    if name == "P2-P3-cost-ratio":
        if tau_cost is None or cost_model is None:
            raise ValueError("P2-P3 requires tau_cost and cost_model")
        return P2P3CostRatio(tau_cost, cost_model)
    if name == "P2-P4-learning-k-analogue":
        return P2P4LearningK()
    raise KeyError(name)
