"""Integration tests for the P2 harness: frozen-anchor reproduction, end-to-end
DEV run, and sealed-set / no-gold guarantees."""
# ruff: noqa: N806
# B is the frozen protocol's budget symbol (docs/ROUTE_B_V2_DEVELOPMENT_PROTOCOL.md).

from __future__ import annotations

import json

import pytest

from benchmark.p2.cost_model import measured_verifier_cost_model
from benchmark.p2.evaluate import evaluate_fixed_b, evaluate_policy
from benchmark.p2.policies import P2P1ScoreGap, P2P4LearningK, PolicyView
from benchmark.p2.tasks import FIXED_BUDGETS, load_dev_tasks

FROZEN_V2 = "research/transparency/route_b_v2_results.json"
FROZEN_SALEOR = "research/transparency/saleor_route_b_transfer_results.json"


@pytest.fixture(scope="module")
def dev_tasks():
    return list(load_dev_tasks())


class TestAnchorReproduction:
    def test_djangocms_fixed_b_matches_frozen_route_b_v2(self, dev_tasks):
        """Composite fixed-B anchors must reproduce the frozen route_b_v2
        pooled macro ORR on djangoCMS DEV (174 tasks)."""
        with open(FROZEN_V2, encoding="utf-8") as fh:
            frozen = json.load(fh)["pooled_curve"]
        dc = [t for t in dev_tasks if t.repository == "djangocms"]
        assert len(dc) == 174
        for B in FIXED_BUDGETS:
            agg = evaluate_fixed_b(dc, B, ranker="composite", cost_model=measured_verifier_cost_model())
            assert abs(agg["macro_orr"] - frozen[str(B)]["CIA"]["macro_orr"]) < 0.02, (
                f"djangoCMS B={B}: harness {agg['macro_orr']} vs frozen {frozen[str(B)]['CIA']['macro_orr']}"
            )

    def test_saleor_fixed_b_matches_frozen_transfer(self, dev_tasks):
        with open(FROZEN_SALEOR, encoding="utf-8") as fh:
            frozen = json.load(fh)["pooled_curve"]
        sa = [t for t in dev_tasks if t.repository == "saleor"]
        assert len(sa) == 149
        for B in FIXED_BUDGETS:
            agg = evaluate_fixed_b(sa, B, ranker="composite", cost_model=measured_verifier_cost_model())
            assert abs(agg["macro_orr"] - frozen[str(B)]["CIA"]["macro_orr"]) < 0.02, (
                f"Saleor B={B}: harness {agg['macro_orr']} vs frozen {frozen[str(B)]['CIA']['macro_orr']}"
            )


class TestEndToEnd:
    def test_policy_run_deterministic(self, dev_tasks):
        cost = measured_verifier_cost_model()
        subset = [t for t in dev_tasks if t.role in ("DEV_VALIDATION", "SALEOR_DEV")][:40]
        p1 = P2P1ScoreGap()
        a1 = evaluate_policy(subset, p1, cost_model=cost)
        a2 = evaluate_policy(subset, p1, cost_model=cost)
        assert a1 == a2
        assert a1["n_tasks"] == 40
        assert 0 <= a1["macro_orr"] <= 1.0
        assert a1["expected_budget"] >= 1.0

    def test_policy_only_sees_observables(self, dev_tasks):
        """PolicyView has no proxy/label; policies are pure functions of scores/sizes."""
        t = next(t for t in dev_tasks if t.omitted_size >= 10)
        view = PolicyView.from_task(t)
        assert not hasattr(view, "proxy")
        assert not hasattr(view, "is_missed_positive")
        for p in (P2P1ScoreGap(), P2P4LearningK()):
            B = p.choose_budget(view)
            assert B in {0, 1, 2, 3, 5, 10}

    def test_no_internal_test_reserve_loaded(self, dev_tasks):
        """P2 loads ONLY DEV roles (djangoCMS DEV_TRAIN/DEV_VALIDATION/V1_DEV,
        Saleor SALEOR_DEV). INTERNAL_TEST/RESERVE case ids must never appear."""
        forbidden = []
        with open("research/transparency/v2_split_proposal.json", encoding="utf-8") as fh:
            v2_split = json.load(fh)["assignment"]
        for cid, role in v2_split.items():
            if role in ("INTERNAL_TEST", "RESERVE") and cid.startswith("djangocms-"):
                forbidden.append(cid)
        with open("benchmark_data/real_commit_impact_saleor/split_freeze_saleor.json", encoding="utf-8") as fh:
            saleor_split = json.load(fh)
        for role_name in ("INTERNAL_TEST", "RESERVE"):
            for cid in saleor_split.get("per_role", {}).get(role_name, {}).get("case_ids", []):
                forbidden.append(cid)
        loaded = {t.case_id for t in dev_tasks}
        assert not (set(forbidden) & loaded), "INTERNAL_TEST/RESERVE leaked into P2 tasks"

    def test_frozen_constants_derived_on_dev_train_only(self):
        with open("research/p2-phase1/frozen_constants.json", encoding="utf-8") as fh:
            constants = json.load(fh)
        assert constants["frozen"] is True
        assert constants["derivation_split"].startswith("djangoCMS DEV_TRAIN")
        assert "DEV_VALIDATION" not in constants["derivation_split"]
        assert "Saleor" not in constants["derivation_split"]
