"""Unit tests for the P2 evaluator (synthetic TP/FP/FN) and harness integrity."""
# ruff: noqa: N803
# N is the frozen protocol's omitted-count symbol.

from __future__ import annotations

import pytest

from benchmark.p2.cost_model import VerifierCostModel
from benchmark.p2.evaluate import (
    analytic_random_recovery,
    evaluate_fixed_b,
    evaluate_policy,
    matched_fixed_b_summary,
    pareto_frontier,
    recovery_at,
    strata_summary,
)
from benchmark.p2.policies import P2P1ScoreGap, P2P4LearningK
from benchmark.p2.tasks import ObservableCandidate, ObservableTask


def _task(cids, composites, missed, *, N=None):
    cands = [
        ObservableCandidate(
            path=f"p{i}", bm25=float(c), bm25_rank_pct=0.5, graph_neighbor=0.0,
            composite=float(c), intent_overlap=0, is_missed_positive=int(m),
        )
        for i, (c, m) in enumerate(zip(composites, missed, strict=True))
    ]
    cands.sort(key=lambda c: (-c.composite, c.path))
    proxy = frozenset(f"p{i}" for i, m in enumerate(missed) if m)
    return ObservableTask(
        case_id=cids, repository="djangocms", role="DEV_TRAIN",
        candidates=tuple(cands), omitted_size=N or len(cands),
        universe_size=len(cands) + 20, proxy=proxy, n_missed=int(sum(missed)),
    )


class TestRecovery:
    def test_composite_recovers_top_b_misses(self):
        t = _task("t1", [1.0, 0.8, 0.6, 0.4, 0.2], [1, 0, 1, 0, 1])
        assert recovery_at(t, 1) == 1   # top candidate is a miss
        assert recovery_at(t, 3) == 2   # p0 + p2
        assert recovery_at(t, 5) == 3
        assert recovery_at(t, 0) == 0

    def test_bm25_ranking(self):
        t = _task("t1", [0.1, 0.9, 0.5], [1, 0, 1])
        # bm25 ranking is descending by bm25 (= composite here)
        assert recovery_at(t, 1, ranker="bm25") == 0  # top bm25 = p1 (0.9) not missed
        assert recovery_at(t, 2, ranker="bm25") == 1

    def test_analytic_random_expectation(self):
        t = _task("t1", [1.0] * 10, [1] * 4 + [0] * 6)
        assert analytic_random_recovery(t, 5) == pytest.approx(5 * 4 / 10)
        assert analytic_random_recovery(t, 0) == 0.0
        t0 = _task("t0", [1.0], [0])
        assert analytic_random_recovery(t0, 3) == 0.0


class TestEvaluateFixedB:
    def test_macro_micro_and_budget(self):
        tasks = [
            _task("a", [1.0, 0.5, 0.2], [1, 0, 1]),   # B=1 recovers 1/2
            _task("b", [1.0, 0.8, 0.6], [0, 1, 1]),   # B=1 recovers 0/2
        ]
        agg = evaluate_fixed_b(tasks, 1)
        assert agg["n_tasks"] == 2
        assert agg["macro_orr"] == pytest.approx((0.5 + 0.0) / 2)
        assert agg["micro_orr"] == pytest.approx(1 / 4)
        assert agg["expected_budget"] == 1
        assert agg["mean_tokens"] > 0

    def test_zero_fn_handling(self):
        tasks = [_task("a", [1.0, 0.5], [1, 0]), _task("b", [1.0], [0])]
        agg = evaluate_fixed_b(tasks, 1)
        assert agg["macro_orr"] == pytest.approx(0.5)  # zero-FN task contributes 0


class TestEvaluatePolicy:
    def test_policy_realized_budget_used(self):
        tasks = [_task("a", [1.0, 0.8, 0.6, 0.4, 0.2], [0, 1, 0, 1, 0])]
        # P2-P4 with energy 0.9: cumulative 1.0/3.0=0.33 (B=1) < 0.9; B=3:
        # (1.0+0.8+0.6)/3.0=0.8 < 0.9; B=5 -> 1.0 >= 0.9 -> realized budget 5
        p = P2P4LearningK(tau_energy=0.9)
        agg = evaluate_policy(tasks, p)
        assert agg["expected_budget"] == 5
        assert agg["macro_orr"] == 1.0  # top-5 recovers both misses (2/2)


class TestMatchedAndPareto:
    def test_pareto_frontier_keeps_undominated(self):
        pts = [
            {"name": "A", "mean_cost_usd": 0.05, "macro_orr": 0.2},
            {"name": "B", "mean_cost_usd": 0.10, "macro_orr": 0.5},
            {"name": "C", "mean_cost_usd": 0.08, "macro_orr": 0.4},
        ]
        front = pareto_frontier(pts)
        assert "A" in front and "B" in front and "C" in front  # all undominated

    def test_dominated_point_excluded(self):
        pts = [
            {"name": "A", "mean_cost_usd": 0.05, "macro_orr": 0.2},
            {"name": "B", "mean_cost_usd": 0.04, "macro_orr": 0.3},  # dominates A
        ]
        assert "A" not in pareto_frontier(pts)

    def test_matched_fixed_b(self):
        fixed = [
            {"name": "fixed-B1", "budget": 1, "mean_cost_usd": 0.000070, "macro_orr": 0.05},
            {"name": "fixed-B5", "budget": 5, "mean_cost_usd": 0.000090, "macro_orr": 0.16},
        ]
        pol = {"name": "pol", "mean_cost_usd": 0.00008, "macro_orr": 0.10}
        m = matched_fixed_b_summary(pol, fixed)
        assert m["dominates_or_matches_fixed"] is True


class TestStrata:
    def test_strata_terciles(self):
        tasks = [
            _task("a", [1.0, 0.5], [1, 0], N=2),
            _task("b", [1.0, 0.5, 0.4, 0.3], [1, 0, 0, 0], N=4),
            _task("c", [1.0, 0.5, 0.4, 0.3, 0.2, 0.1], [1, 0, 0, 0, 0, 0], N=6),
        ]
        s = strata_summary(tasks, P2P1ScoreGap(), cost_model=VerifierCostModel())
        assert set(s) == {"small", "medium", "large"}
        assert sum(v["n_tasks"] for v in s.values()) == 3
