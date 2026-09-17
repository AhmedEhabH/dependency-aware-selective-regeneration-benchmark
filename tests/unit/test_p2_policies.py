"""Unit tests for P2 policies: formulas, no-gold proof, tie/failure rules."""
# ruff: noqa: N803, N806
# B / N are the frozen protocol symbols (budget / omitted-count); the tests
# mirror the scripts' protocol-symbol naming.

from __future__ import annotations

import pytest

from benchmark.p2.cost_model import VerifierCostModel, measured_verifier_cost_model
from benchmark.p2.policies import (
    P2P1ScoreGap,
    P2P2MarginalScore,
    P2P3CostRatio,
    P2P4LearningK,
    PolicyView,
    make_policy,
)


def _view(scores, N=None, universe=200):
    N = N if N is not None else len(scores)
    return PolicyView(composite_scores=tuple(float(x) for x in scores), omitted_size=N, universe_size=universe)


class TestScoreGap:
    def test_stops_when_gap_below_tau(self):
        # gaps: 1.0->0.8 gap 0.2 ; 0.8->0.70 gap 0.10 ; 0.70->0.30 gap 0.40...
        # tau=0.10 -> first B with gap < 0.10: s_B - s_{B+1} < 0.10
        v = _view([1.0, 0.80, 0.79, 0.70, 0.30, 0.05])  # gaps: .20,.01,.09,.40,.25
        B = P2P1ScoreGap(tau_gap=0.10).choose_budget(v)
        # B=1 gap .20 >= .10; B=3 gap .09 < .10 -> stop at 3
        assert B == 3

    def test_defaults_to_10_when_no_gap_small(self):
        v = _view([1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0])
        B = P2P1ScoreGap(tau_gap=0.10).choose_budget(v)
        assert B == 10

    def test_budget_capped_at_omitted_size(self):
        v = _view([1.0, 0.9], N=2)
        assert P2P1ScoreGap().choose_budget(v) == 2

    def test_zero_candidates_returns_zero(self):
        assert P2P1ScoreGap().choose_budget(_view([], N=0)) == 0

    def test_all_flat_scores_stops_at_one(self):
        v = _view([0.0, 0.0, 0.0, 0.0], N=4)
        assert P2P1ScoreGap().choose_budget(v) == 1


class TestMarginalScore:
    def test_stops_when_bth_below_tau(self):
        v = _view([2.0, 1.5, 0.9, 0.5, 0.2])  # tau=1.0 -> B=1 s=2 >=1, B=3 s=0.9<1 -> 3
        assert P2P2MarginalScore(tau_marg=1.0).choose_budget(v) == 3

    def test_defaults_to_10(self):
        v = _view([2.0, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, 1.3, 1.2, 1.1, 1.0])
        assert P2P2MarginalScore(tau_marg=1.0).choose_budget(v) == 10

    def test_requires_tau(self):
        with pytest.raises(ValueError):
            make_policy("P2-P2-marginal-score")


class TestCostRatio:
    def test_stops_when_cost_ratio_reached(self):
        model = VerifierCostModel()
        v = _view([1.0] * 10, N=200)  # tokens(1)/200 = 211.9/200 = 1.06 >= 0.5
        assert P2P3CostRatio(tau_cost=0.5, cost_model=model).choose_budget(v) == 1

    def test_defaults_to_10_when_never_reached(self):
        model = VerifierCostModel()
        v = _view([1.0] * 10, N=200000)  # tokens(10)/200000 tiny
        assert P2P3CostRatio(tau_cost=0.5, cost_model=model).choose_budget(v) == 10


class TestLearningK:
    def test_energy_rule(self):
        # scores 1,1,1,1,1,... energy 0.9 -> need 9 of 10 equal-mass? 9*0.1=0.9 -> B=9? grid caps at 10
        v = _view([1.0] * 10, N=10)
        B = P2P4LearningK(tau_energy=0.90).choose_budget(v)
        assert B == 10  # 9/10 mass -> smallest grid B with cum>=0.9 -> 10

    def test_high_energy_first(self):
        v = _view([10.0, 0.1, 0.05], N=3)
        # total 10.15; first 10/10.15 = 0.985 >= 0.9 -> B=1
        assert P2P4LearningK(tau_energy=0.90).choose_budget(v) == 1


class TestNoGoldProof:
    def test_policies_do_not_receive_labels_or_proxy(self):
        """PolicyView structurally has no proxy / label fields; a policy that
        tries to read them raises AttributeError (fail-closed)."""
        v = _view([1.0, 0.5, 0.2], N=3)
        for p in (P2P1ScoreGap(), P2P2MarginalScore(0.5), P2P3CostRatio(0.5, VerifierCostModel()), P2P4LearningK()):
            assert not hasattr(v, "proxy")
            assert not hasattr(v, "is_missed_positive")
            assert p.choose_budget(v) in {0, 1, 2, 3, 5, 10}


class TestCostModel:
    def test_measured_model_matches_confirmatory_means(self):
        m = measured_verifier_cost_model()
        assert abs(m.prompt_tokens(1) - 211.9) < 1.0
        assert abs(m.prompt_tokens(5) - 241.6) < 1.0
        assert abs(m.prompt_tokens(10) - 278.5) < 1.0

    def test_zero_budget_no_cost(self):
        m = VerifierCostModel()
        assert m.prompt_tokens(0) == 0.0
        assert m.api_cost_usd(0) == 0.0
